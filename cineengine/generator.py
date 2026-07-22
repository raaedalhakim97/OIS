"""
CineEngine Generator — a prompt/image driven video generator built on the repo.

Usage:
    python -m cineengine.generator --prompt "cosmic quantum nebula" -o out.mp4
    python -m cineengine.generator --image photo.png --prompt "energy pulse" -o out.mp4

Text prompts route to a procedural scene (keyword matched); an --image is
animated with a cinematic push + energy effects. Motion is driven by the repo's
real Camera; the look uses the engine's effect math (bloom, film grain,
vignette, chromatic aberration, ACES). CPU-only — no GPU/AI weights required.
"""
import os
import sys
import argparse
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cineengine.config import Config
from cineengine.camera.camera import Camera

try:
    import imageio.v2 as imageio
    import imageio_ffmpeg  # noqa
except ImportError:
    raise SystemExit("pip install imageio imageio-ffmpeg numpy Pillow")


# ----------------------------- shared effect ports -----------------------------
class FX:
    def __init__(self, w, h):
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.xx, self.yy = xx, yy
        self.tcx, self.tcy = xx / w, yy / h

    def aces(self, a):
        x = a / 255.0
        o = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
        return np.clip(o, 0, 1) * 255.0

    def bloom(self, img, sigma=7, thr=175, gain=1.4):
        b = np.asarray(Image.fromarray(img.clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(sigma)), np.float32)
        return img + np.clip(b - thr, 0, 255) * gain

    def vignette(self, a, strength=0.45):
        ux = (self.tcx - 0.5) * (self.w / self.h)
        uy = (self.tcy - 0.5)
        d = np.sqrt(ux ** 2 + uy ** 2) * (1 + strength)
        tt = np.clip((d - 0.85) / (0.32 - 0.85), 0, 1)
        return a * (tt * tt * (3 - 2 * tt))[..., None]

    def grain(self, a, t, amt=0.035):
        n = np.sin((self.tcx * self.w + t) * 12.9898 + (self.tcy * self.h + t) * 78.233) * 43758.5453
        n = (n - np.floor(n)) * 2 - 1
        return a + n[..., None] * amt * 255

    def chromatic(self, a, amount):
        dx = (self.tcx - 0.5) * amount
        dy = (self.tcy - 0.5) * amount
        xr = np.clip(self.xx + dx, 0, self.w - 1).astype(np.int32)
        yr = np.clip(self.yy + dy, 0, self.h - 1).astype(np.int32)
        xb = np.clip(self.xx - dx, 0, self.w - 1).astype(np.int32)
        yb = np.clip(self.yy - dy, 0, self.h - 1).astype(np.int32)
        o = a.copy()
        o[..., 0] = a[yr, xr, 0]
        o[..., 2] = a[yb, xb, 2]
        return o


def fbm(w, h, octaves=5, seed=0, aspect=1.0):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot, base = 1.0, 0.0, 4
    for o in range(octaves):
        gw = max(2, int(base * (2 ** o) * aspect))
        gh = max(2, int(base * (2 ** o)))
        grid = (r.random((gh, gw)) * 255).astype(np.uint8)
        layer = np.asarray(Image.fromarray(grid).resize((w, h), Image.BICUBIC), np.float32) / 255.0
        out += layer * amp
        tot += amp
        amp *= 0.5
    return out / tot


# ------------------------------- scene presets ---------------------------------
def _palette(prompt):
    p = prompt.lower()
    if any(k in p for k in ("cosmic", "space", "nebula", "galaxy", "star", "quantum", "cosmos", "universe")):
        return "cosmic"
    if any(k in p for k in ("ocean", "sea", "water", "wave")):
        return "ocean"
    if any(k in p for k in ("fire", "lava", "ember", "inferno")):
        return "fire"
    return "nature"


def build_cosmic(w, h, prompt, seed=0):
    """Colored nebula + starfield + glowing core (great for quantum/space prompts)."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = xx / w, yy / h
    # deep space base
    img = np.zeros((h, w, 3), np.float32) + np.array([6, 8, 20], np.float32)
    # nebula clouds: two fbm masses tinted violet + teal + magenta
    n1 = fbm(w, h, 6, seed + 1, aspect=1.0)
    n2 = fbm(w, h, 6, seed + 2, aspect=1.0)
    neb = np.clip((n1 * 0.7 + n2 * 0.5 - 0.45) * 2.2, 0, 1) ** 1.5
    tintA = np.array([120, 40, 180], np.float32)   # violet
    tintB = np.array([30, 120, 170], np.float32)   # teal
    mix = np.clip(n2, 0, 1)[..., None]
    img += (neb[..., None] * (tintA * (1 - mix) + tintB * mix)) * 1.2
    # magenta core glow
    cx, cy = 0.5, 0.46
    d = np.sqrt(((nx - cx) * (w / h)) ** 2 + (ny - cy) ** 2)
    img += (np.clip(1 - d * 1.6, 0, 1) ** 2)[..., None] * np.array([190, 90, 210], np.float32)
    img += (np.clip(1 - d * 8.0, 0, 1) ** 0.7)[..., None] * np.array([255, 240, 255], np.float32)
    # starfield (three sizes)
    for n, br, sz in ((900, 120, 0), (240, 200, 1), (60, 255, 1)):
        ys = r.integers(0, h, n)
        xs = r.integers(0, w, n)
        for k in range(n):
            img[ys[k], xs[k]] += br
            if sz:
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy2, xx2 = ys[k] + dy, xs[k] + dx
                    if 0 <= yy2 < h and 0 <= xx2 < w:
                        img[yy2, xx2] += br * 0.5
    return np.clip(img, 0, 255), (cx, cy)


def build_nature(w, h, prompt, seed=0):
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = xx / w, yy / h
    horizon = 0.6
    t = np.clip(ny / horizon, 0, 1)[..., None]
    img = np.array([70, 120, 190], np.float32) * (1 - t) + np.array([250, 200, 130], np.float32) * t
    sx, sy = 0.5, horizon - 0.1
    d = np.sqrt(((nx - sx) * (w / h)) ** 2 + (ny - sy) ** 2)
    img += (np.clip(1 - d * 2.0, 0, 1) ** 2)[..., None] * np.array([120, 80, 20], np.float32)
    for i, col in enumerate([[46, 88, 52], [30, 64, 44], [18, 44, 32]]):
        base = horizon + 0.02 + i * 0.12
        ridge = base - (0.04 + i * 0.02) * np.sin(nx * (3 + i) * 6.28 + r.uniform(0, 6))
        m = (ny > ridge)[..., None]
        img = img * (1 - m) + np.array(col, np.float32) * m
    return np.clip(img, 0, 255), (0.5, horizon - 0.1)


BUILDERS = {"cosmic": build_cosmic, "ocean": build_cosmic, "fire": build_cosmic, "nature": build_nature}


# ------------------------------- generation ------------------------------------
def generate(prompt="", image=None, out="output.mp4", duration=5.0, fps=30, seed=0):
    config = Config(fps=fps, resolution=(1080, 1920))
    W, H = config.RESOLUTION
    fx = FX(W, H)
    camera = Camera(config)
    camera.cinematic_push(duration=duration, start_zoom=1.0, end_zoom=1.16)
    camera.add_shake(intensity=0.002, frequency=1.1, seed=seed + 5)

    if image:
        base = np.asarray(Image.open(image).convert("RGB").resize((W, H), Image.LANCZOS), np.float32)
        lum = base @ np.array([0.299, 0.587, 0.114], np.float32)
        b = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(25)), np.float32)
        cy, cx = np.unravel_index(np.argmax(b), b.shape)
        core = (cx / W, cy / H)
        bright = np.clip((lum - 165) / 90, 0, 1) ** 1.4
        rng = np.random.default_rng(seed)
        phase = rng.uniform(0, 6.28, (H, W)).astype(np.float32)
        mode = "image"
    else:
        kind = _palette(prompt)
        base, core = BUILDERS[kind](W, H, prompt, seed)
        mode = "scene"

    CX, CY = core[0] * W, core[1] * H
    R = np.sqrt((fx.xx - CX) ** 2 + (fx.yy - CY) ** 2)
    MAXR = float(R.max())

    def frame(t):
        f = base.copy()
        # energy pulse from the core (works for both modes)
        breathe = 0.5 + 0.5 * np.sin(2 * np.pi * t / 1.6)
        f += (np.exp(-(R ** 2) / (2 * 90.0 ** 2)) * (0.4 + 0.6 * breathe))[..., None] * np.array([255, 235, 210])
        for off in (0.0, 0.5):
            ph = ((t / 2.1 + off) % 1.0)
            ring = np.exp(-((R - ph * MAXR) ** 2) / (2 * 26.0 ** 2)) * (1 - ph) ** 1.3
            f += ring[..., None] * np.array([180, 150, 255] if mode == "scene" else [255, 205, 120]) * 0.7
        if mode == "image":
            f *= (1 + 0.35 * bright[..., None] * np.sin(2 * np.pi * t * 1.4 + phase)[..., None])
        beat = max(0.0, np.sin(2 * np.pi * t / 2.1))
        f = fx.aces(f) if mode == "scene" else f
        f = fx.chromatic(f, 1.0 + 2.0 * beat)
        f = fx.bloom(f)
        # camera collapse-zoom toward core
        (camx, camy), zoom = camera.get_state(t)
        cw, ch = W / zoom, H / zoom
        left = float(np.clip(CX - cw / 2 + camx * W, 0, W - cw))
        top = float(np.clip(CY - ch / 2 + camy * H, 0, H - ch))
        f = np.asarray(Image.fromarray(f.clip(0, 255).astype(np.uint8))
                       .crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS), np.float32)
        f = fx.grain(f, t * fps)
        f = fx.vignette(f)
        return f.clip(0, 255).astype(np.uint8)

    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(duration * fps)
    writer = imageio.get_writer(out, fps=fps, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    label = f"image:{os.path.basename(image)}" if image else f"scene:{_palette(prompt)}"
    print(f"[CineEngine Generator] prompt={prompt!r} {label} -> {out}")
    for i in range(n):
        writer.append_data(frame(i / fps))
        if (i + 1) % 15 == 0:
            print(f"  {i+1}/{n}")
    writer.close()
    print(f"Done -> {out} ({os.path.getsize(out)/1024:.0f} KB)")
    return out


def main():
    ap = argparse.ArgumentParser(description="CineEngine prompt/image video generator")
    ap.add_argument("--prompt", "-p", default="", help="text prompt (routes to a scene)")
    ap.add_argument("--image", "-i", default=None, help="animate this image instead")
    ap.add_argument("--out", "-o", default="output.mp4")
    ap.add_argument("--duration", "-d", type=float, default=5.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if not a.prompt and not a.image:
        ap.error("give --prompt or --image")
    generate(a.prompt, a.image, a.out, a.duration, a.fps, a.seed)


if __name__ == "__main__":
    main()
