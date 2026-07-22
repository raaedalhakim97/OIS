"""
Epic animation of the 'Observer Collapse' quantum-mandala photo.

Theme = wavefunction collapse: a slow zoom into the glowing core, a breathing
core, twinkling nodes, and energy shockwaves that pulse outward from the center.

Motion is driven by the repo's real Camera (cineengine.camera.Camera); the look
uses the engine's own effect math (bloom, film grain, vignette, chromatic
aberration) ported from its GLSL shaders. No AI/GPU needed — pure CPU compositing
on the supplied still.
"""
import os, sys, argparse
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from cineengine.config import Config
from cineengine.camera.camera import Camera
import imageio.v2 as imageio
import imageio_ffmpeg  # noqa

HERE = os.path.dirname(__file__)
BASE_PNG = os.path.join(HERE, "base_clean.png")
OUT = os.path.join(HERE, "observer_collapse_anim.mp4")

config = Config(fps=30, resolution=(1080, 1920))
W, H = config.RESOLUTION
FPS = config.FPS
DURATION = 5.0
PERIOD = 2.1                      # seconds between collapse pulses

# ---- base image ----
base = np.asarray(Image.open(BASE_PNG).convert("RGB").resize((W, H), Image.LANCZOS), np.float32)
lum = base @ np.array([0.299, 0.587, 0.114], np.float32)

# core = brightest blob
blur = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(25)), np.float32)
cy, cx = np.unravel_index(np.argmax(blur), blur.shape)
CX, CY = float(cx), float(cy)
print(f"core at ({CX:.0f},{CY:.0f})")

# masks + fields
bright = np.clip((lum - 165) / 90, 0, 1) ** 1.4            # nodes/lines glow strength
struct = np.clip((lum - 45) / 120, 0, 1)                   # any structure
rng = np.random.default_rng(7)
phase_map = rng.uniform(0, 2 * np.pi, (H, W)).astype(np.float32)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
R = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2)
THETA = np.arctan2(yy - CY, xx - CX)
MAXR = float(np.sqrt(max(CX, W - CX) ** 2 + max(CY, H - CY) ** 2))
_tcx, _tcy = xx / W, yy / H

# gold sparkles drifting outward from core
NP = 40
sp_ang = rng.uniform(0, 2 * np.pi, NP)
sp_r0 = rng.uniform(0.05, 0.95, NP) * MAXR
sp_speed = rng.uniform(6, 22, NP)
sp_size = rng.uniform(1.6, 3.6, NP)
sp_bright = rng.uniform(0.4, 0.9, NP)
sp_ph = rng.uniform(0, 6.28, NP)

# ---- engine camera: slow collapse push toward the core ----
camera = Camera(config)
camera.cinematic_push(duration=DURATION, start_zoom=1.0, end_zoom=1.14)
camera.add_shake(intensity=0.0018, frequency=1.1, seed=3)

GOLD = np.array([255, 205, 120], np.float32)
GOLDW = np.array([255, 235, 200], np.float32)


# ---- engine effect ports ----
def bloom(img, sigma=7, thr=175, gain=1.4):
    b = Image.fromarray(img.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    ba = np.asarray(b, np.float32)
    return img + np.clip(ba - thr, 0, 255) * gain


def vignette(a, strength=0.45):
    ux = (_tcx - 0.5) * (W / H); uy = (_tcy - 0.5)
    d = np.sqrt(ux ** 2 + uy ** 2) * (1 + strength)
    tt = np.clip((d - 0.85) / (0.32 - 0.85), 0, 1)
    return a * (tt * tt * (3 - 2 * tt))[..., None]


def grain(a, t, amt=0.035):
    n = np.sin((_tcx * W + t) * 12.9898 + (_tcy * H + t) * 78.233) * 43758.5453
    n = (n - np.floor(n)) * 2 - 1
    return a + n[..., None] * amt * 255


def chromatic(a, amount):
    dx = (_tcx - 0.5) * amount; dy = (_tcy - 0.5) * amount
    xr = np.clip(xx + dx, 0, W - 1).astype(np.int32); yr = np.clip(yy + dy, 0, H - 1).astype(np.int32)
    xb = np.clip(xx - dx, 0, W - 1).astype(np.int32); yb = np.clip(yy - dy, 0, H - 1).astype(np.int32)
    o = a.copy(); o[..., 0] = a[yr, xr, 0]; o[..., 2] = a[yb, xb, 2]
    return o


def energy(t):
    """Additive energy layer: breathing core + expanding shockwave rings + rays."""
    add = np.zeros((H, W, 3), np.float32)

    # breathing core glow
    breathe = 0.55 + 0.45 * np.sin(2 * np.pi * t / 1.6)
    core = np.exp(-(R ** 2) / (2 * (95.0) ** 2)) * (0.6 + 0.7 * breathe)
    add += core[..., None] * GOLDW

    # two expanding shockwave rings (collapse pulses)
    for off in (0.0, 0.5):
        ph = ((t / PERIOD + off) % 1.0)
        rr = ph * MAXR
        ring = np.exp(-((R - rr) ** 2) / (2 * (26.0) ** 2)) * (1 - ph) ** 1.3
        add += ring[..., None] * GOLD * 0.9

    # slow rotating ray sweep, only on existing structure (subtle shimmer)
    sweep = t * 0.9
    ang = np.cos(THETA - sweep) * np.cos(2 * (THETA - sweep))
    ray = np.clip(ang, 0, 1) ** 3 * struct * 0.35
    add += ray[..., None] * GOLD

    return add


def add_sparkles(img, t):
    for i in range(NP):
        rr = (sp_r0[i] + sp_speed[i] * (t % (PERIOD)) ) % MAXR
        px = CX + rr * np.cos(sp_ang[i]); py = CY + rr * np.sin(sp_ang[i])
        s = sp_size[i]; r = int(s * 3.5)
        x0, x1 = max(0, int(px) - r), min(W, int(px) + r)
        y0, y1 = max(0, int(py) - r), min(H, int(py) + r)
        if x1 <= x0 or y1 <= y0:
            continue
        yg, xg = np.mgrid[y0:y1, x0:x1]
        d2 = (xg - px) ** 2 + (yg - py) ** 2
        flick = 0.5 + 0.5 * np.sin(t * 7 + sp_ph[i])
        fade = 1 - rr / MAXR
        img[y0:y1, x0:x1] += (np.exp(-d2 / (2 * s ** 2)) * sp_bright[i] * flick * fade)[..., None] * GOLDW
    return img


def render(t):
    frame = base + energy(t)
    frame *= (1 + 0.35 * bright[..., None] * np.sin(2 * np.pi * (t * 1.4) + phase_map)[..., None])
    frame = add_sparkles(frame, t)

    # pulse-synced global flash + chromatic on each collapse
    beat = max(0.0, np.sin(2 * np.pi * t / PERIOD))
    frame *= (1 + 0.05 * beat)
    frame = chromatic(frame, 1.0 + 2.2 * beat)
    frame = bloom(frame)

    # collapse zoom toward the core (engine camera)
    (camx, camy), zoom = camera.get_state(t)
    cw, ch = W / zoom, H / zoom
    left = np.clip(CX - cw / 2 + camx * W, 0, W - cw)
    top = np.clip(CY - ch / 2 + camy * H, 0, H - ch)
    crop = Image.fromarray(frame.clip(0, 255).astype(np.uint8)).crop(
        (left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS)
    frame = np.asarray(crop, np.float32)

    frame = grain(frame, t * FPS)
    frame = vignette(frame)
    return frame.clip(0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    args = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if args.preview is not None:
        Image.fromarray(render(args.preview)).save(os.path.join(HERE, "anim_preview.png"))
        print("preview saved"); return
    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "slow",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames @ {W}x{H} {FPS}fps ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 15 == 0:
            print(f"  {i+1}/{n}")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
