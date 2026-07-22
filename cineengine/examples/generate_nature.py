"""
Generate a 5-second NATURE video using the CineEngine code from the repo.

This drives the engine's REAL pure-Python modules directly:
  - cineengine.config.Config
  - cineengine.camera.camera.Camera  (cinematic_push -> CameraMotion + easing)
  - cineengine.camera.camera.Camera.add_shake  (Perlin CameraShake)

The engine's post-effects (grain / vignette / colorgrade) are GLSL shaders that
require a GPU/ModernGL context, unavailable here. Their exact fragment-shader
math is ported to numpy below, matching the formulas in:
  - effects/grain.py      (rand-based additive grain)
  - effects/vignette.py   (smoothstep vignette)
  - effects/colorgrade.py (ACES filmic tonemap)

The AI image module (Stable Diffusion) also needs a GPU, so the nature scene is
painted procedurally as the source frame.
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from cineengine.config import Config
from cineengine.camera.camera import Camera

import imageio.v2 as imageio
import imageio_ffmpeg  # noqa: F401

# ---- engine config (real Config object) ----
config = Config(fps=24, resolution=(1080, 1920))
W, H = config.RESOLUTION
FPS = config.FPS
DURATION = 5.0
OUT = os.path.join(os.path.dirname(__file__), "nature_demo.mp4")

# ---- drive the REAL engine camera ----
camera = Camera(config)
camera.cinematic_push(duration=DURATION, start_zoom=1.0, end_zoom=1.25, start_time=0.0)
camera.add_shake(intensity=0.004, frequency=1.5, seed=7)  # subtle handheld drift


# ---------- procedural nature scene (stand-in for the AI image module) ----------
def make_nature_scene(w, h):
    """A layered landscape: sky, sun glow, rolling hills, mist."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = xx / w, yy / h
    img = np.zeros((h, w, 3), np.float32)

    # Sky: warm golden-hour gradient (top deep blue -> horizon warm)
    horizon = 0.55
    sky_t = np.clip(ny / horizon, 0, 1)
    sky = (np.array([70, 120, 190]) * (1 - sky_t)[..., None]
           + np.array([250, 200, 130]) * sky_t[..., None])
    # Sun glow near horizon, slightly right of center
    sx, sy = 0.62, 0.5
    d = np.sqrt(((nx - sx) * (w / h)) ** 2 + (ny - sy) ** 2)
    glow = np.clip(1.0 - d * 1.8, 0, 1) ** 2
    sky += glow[..., None] * np.array([90, 70, 20])
    img += sky  # paint sky across the full frame; hills composite on top (no gaps)

    # Rolling hills: a few sine-ridged bands receding to the horizon
    rng = np.random.default_rng(42)
    hill_colors = [np.array([46, 88, 52]), np.array([34, 70, 44]),
                   np.array([24, 54, 38]), np.array([16, 40, 30])]
    for i, col in enumerate(hill_colors):
        base = horizon + 0.02 + i * 0.11
        amp = 0.03 + i * 0.015
        freq = 3.0 + i * 1.7
        phase = rng.uniform(0, 6.28)
        ridge = base - amp * np.sin(nx * freq * 3.14159 + phase) \
                     - amp * 0.4 * np.sin(nx * freq * 7.0 + phase * 2)
        mask = (ny > ridge)[..., None]
        # depth haze: farther hills lighter/bluer
        haze = (len(hill_colors) - i) / len(hill_colors)
        shade = col * (0.75 + 0.25 * (1 - haze)) + np.array([120, 130, 140]) * 0.10 * haze
        img = img * (1 - mask) + shade * mask

    # Low mist band over the hills at the horizon
    mist = np.exp(-((ny - horizon) ** 2) / (2 * 0.02 ** 2))
    img += (mist[..., None] * np.array([200, 205, 200]) * 0.35)

    # gentle atmospheric grain in the source (very low)
    img += rng.normal(0, 2.0, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


# oversized so the camera push has room to crop in
SCENE = Image.fromarray(make_nature_scene(int(W * 1.3), int(H * 1.3)), "RGB")


# ---------- ported engine effect math ----------
# Precompute static coordinate grids
_uv_y, _uv_x = np.mgrid[0:H, 0:W].astype(np.float32)
_tc_x, _tc_y = _uv_x / W, _uv_y / H  # texcoords 0..1


def _grain(arr, intensity, t):
    """Port of effects/grain.py fragment shader:
       grain = fract(sin(dot(texcoord*res + time, (12.9898,78.233)))*43758.5453)*2-1
       color.rgb += grain * intensity   (values in 0..1 space)."""
    px = _tc_x * W + t
    py = _tc_y * H + t
    dot = px * 12.9898 + py * 78.233
    grain = (np.sin(dot) * 43758.5453)
    grain = grain - np.floor(grain)          # fract
    grain = grain * 2.0 - 1.0                # -1..1
    return arr + (grain[..., None] * intensity * 255.0)


def _vignette(arr, strength):
    """Port of effects/vignette.py:
       uv = texcoord-0.5; uv.x *= res.x/res.y
       dist = length(uv); v = smoothstep(0.8,0.3, dist*(1+strength)); color*=v."""
    ux = (_tc_x - 0.5) * (W / H)
    uy = (_tc_y - 0.5)
    dist = np.sqrt(ux ** 2 + uy ** 2) * (1.0 + strength)
    # smoothstep(edge0=0.8, edge1=0.3, x): note edge0>edge1 -> inverted
    e0, e1 = 0.8, 0.3
    tt = np.clip((dist - e0) / (e1 - e0), 0, 1)
    v = tt * tt * (3 - 2 * tt)
    return arr * v[..., None]


def _aces_colorgrade(arr):
    """Port of effects/colorgrade.py ACES filmic tonemap (operates in 0..1)."""
    x = arr / 255.0
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    out = (x * (a * x + b)) / (x * (c * x + d) + e)
    return np.clip(out, 0, 1) * 255.0


def make_frame(t):
    # --- REAL engine camera state ---
    (cam_x, cam_y), zoom = camera.get_state(t)

    bw, bh = SCENE.size
    cw, ch = int(W / zoom), int(H / zoom)
    # camera pan offsets (shake/spline) mapped into pixels
    ox = int(cam_x * W)
    oy = int(cam_y * H)
    left = np.clip((bw - cw) // 2 + ox, 0, bw - cw)
    top = np.clip((bh - ch) // 2 + oy, 0, bh - ch)
    frame = SCENE.crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS)
    arr = np.asarray(frame, np.float32)

    # --- engine effect stack (ported shader math) ---
    arr = _aces_colorgrade(arr)                                  # colorgrade.py
    arr = _grain(arr, config.GRAIN_INTENSITY, t * FPS)           # grain.py
    arr = _vignette(arr, config.VIGNETTE_STRENGTH)               # vignette.py
    return np.clip(arr, 0, 255).astype(np.uint8)


def main():
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "23", "-preset", "medium",
                                               "-pix_fmt", "yuv420p",
                                               "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} nature frames at {W}x{H} @ {FPS}fps using engine camera...")
    for i in range(n):
        writer.append_data(make_frame(i / FPS))
        if (i + 1) % 12 == 0:
            print(f"  {i + 1}/{n}")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
