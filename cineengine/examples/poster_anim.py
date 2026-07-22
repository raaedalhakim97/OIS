"""
Poster animator — brings the graphic/energy side of a text poster to life
(flowing shimmer, twinkling data points, drifting motes, gentle push) while
keeping the text side calm and readable.

Uses the repo's real Camera for the push and the engine effect math
(bloom, film grain, vignette, chromatic aberration).

    python poster_anim.py --image poster.jpg --out out.mp4 [--flow lr|diag|up]
"""
import os, sys, argparse
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.config import Config
from cineengine.camera.camera import Camera
from cineengine.generator import FX
import imageio.v2 as imageio
import imageio_ffmpeg  # noqa

DURATION = 5.0
FPS = 30


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def animate(image, out, flow="diag", seed=0):
    img = Image.open(image).convert("RGB")
    w0, h0 = img.size
    W = 1080
    H = int(round(W * h0 / w0 / 2) * 2)          # even height, keep aspect
    base = np.asarray(img.resize((W, H), Image.LANCZOS), np.float32)
    fx = FX(W, H)
    config = Config(fps=FPS, resolution=(W, H))
    cam = Camera(config)
    cam.cinematic_push(duration=DURATION, start_zoom=1.0, end_zoom=1.05)   # subtle, keeps text
    cam.add_shake(intensity=0.0015, frequency=1.0, seed=seed + 2)

    lum = base @ np.array([0.299, 0.587, 0.114], np.float32)
    # bright detail = the particle/energy structures
    bright = np.clip((lum - 95) / 110, 0, 1) ** 1.2
    # horizontal weight: calm on the left (text), lively on the right (graphic)
    hweight = smoothstep(0.30, 0.72, fx.tcx)
    if flow == "up":       # image with central/rising graphic -> weight the middle-right
        hweight = np.maximum(hweight, smoothstep(0.65, 0.35, fx.tcx) * smoothstep(0.25, 0.6, fx.tcy))
    anim = bright * hweight
    rng = np.random.default_rng(seed)
    phase = rng.uniform(0, 2 * np.pi, (H, W)).astype(np.float32)

    # flow direction for the traveling shimmer
    if flow == "lr":
        dirx, diry = 1.0, 0.0
    elif flow == "up":
        dirx, diry = 0.2, -1.0
    else:
        dirx, diry = 0.7, -0.7
    proj = (fx.xx * dirx + fx.yy * diry)

    # drifting motes seeded on the lively structure
    ys, xs = np.where(anim > 0.45)
    NP = 70
    if len(xs) > 0:
        pick = rng.choice(len(xs), min(NP, len(xs)), replace=False)
        mx, my = xs[pick].astype(np.float32), ys[pick].astype(np.float32)
    else:
        mx, my = np.array([]), np.array([])
    msz = rng.uniform(1.4, 3.0, len(mx))
    mph = rng.uniform(0, 6.28, len(mx))
    mspd = rng.uniform(8, 26, len(mx))

    def frame(t):
        f = base.copy()
        # twinkle the data points
        f *= (1 + 0.45 * anim[..., None] * np.sin(2 * np.pi * 1.3 * t + phase)[..., None])
        # traveling energy shimmer along the flow direction
        wave = 0.5 + 0.5 * np.sin(proj * 0.05 - t * 6.0)
        f += (anim * wave)[..., None] * np.array([235, 240, 255], np.float32) * 0.5
        # drifting motes (data flowing)
        for i in range(len(mx)):
            px = mx[i] + dirx * mspd[i] * (t % 2.0)
            py = my[i] + diry * mspd[i] * (t % 2.0)
            if not (0 <= px < W and 0 <= py < H):
                continue
            s = msz[i]; r = int(s * 3.5)
            x0, x1 = max(0, int(px) - r), min(W, int(px) + r)
            y0, y1 = max(0, int(py) - r), min(H, int(py) + r)
            if x1 <= x0 or y1 <= y0:
                continue
            yg, xg = np.mgrid[y0:y1, x0:x1]
            d2 = (xg - px) ** 2 + (yg - py) ** 2
            fl = 0.5 + 0.5 * np.sin(t * 7 + mph[i])
            f[y0:y1, x0:x1] += (np.exp(-d2 / (2 * s ** 2)) * fl)[..., None] * np.array([230, 238, 255]) * 0.8
        # gentle cinematic finish
        f = fx.bloom(f, sigma=5, thr=205, gain=0.7)
        f = fx.chromatic(f, 0.6)
        (cx, cy), zoom = cam.get_state(t)
        cw, ch = W / zoom, H / zoom
        left = float(np.clip((W - cw) / 2 + cx * W, 0, W - cw))
        top = float(np.clip((H - ch) / 2 + cy * H, 0, H - ch))
        f = np.asarray(Image.fromarray(f.clip(0, 255).astype(np.uint8))
                       .crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS), np.float32)
        f = fx.grain(f, t * FPS, amt=0.022)
        f = fx.vignette(f, strength=0.35)
        return f.clip(0, 255).astype(np.uint8)

    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DURATION * FPS)
    writer = imageio.get_writer(out, fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"animate {image} ({W}x{H}) flow={flow} -> {out}")
    for i in range(n):
        writer.append_data(frame(i / FPS))
        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{n}")
    writer.close()
    print(f"Done -> {out} ({os.path.getsize(out)/1024:.0f} KB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--flow", default="diag", choices=["lr", "diag", "up"])
    ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    if a.preview is not None:
        import types
        # quick single-frame preview
        img = Image.open(a.image).convert("RGB"); w0, h0 = img.size
        os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    animate(a.image, a.out, a.flow)
