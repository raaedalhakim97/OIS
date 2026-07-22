"""
Premium animation of the 'face -> numbers' poster.

Keeps the face crisp (enhanced) and adds:
  - a cinematic SCANNER beam sweeping across the face
  - the data grid flowing + pulsing (traveling shimmer + node twinkle)
  - distinct data-sparks streaking off the grid (with motion trails)
Real engine Camera push + engine effects (bloom, grain, vignette, chromatic).
"""
import os, sys, argparse
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.config import Config
from cineengine.camera.camera import Camera
from cineengine.generator import FX
import imageio.v2 as imageio
import imageio_ffmpeg  # noqa

DURATION = 6.0
FPS = 30
SRC = "poster_face.jpg"
OUT = "face_dissolve.mp4"


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    img = Image.open(SRC).convert("RGB")
    w0, h0 = img.size
    W = 1080
    H = int(round(W * h0 / w0 / 2) * 2)
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Sharpness(img).enhance(1.6)
    img = ImageEnhance.Brightness(img).enhance(1.03)
    base = np.asarray(img, np.float32)
    lum = base @ np.array([0.299, 0.587, 0.114], np.float32)

    fx = FX(W, H)
    tcx, tcy = fx.tcx, fx.tcy
    R = smooth(0.42, 0.60, tcx)                       # right-side (grid) weight
    bright = np.clip((lum - 95) / 110, 0, 1) ** 1.2
    anim = bright * R
    rng = np.random.default_rng(1)
    phase = rng.uniform(0, 2 * np.pi, (H, W)).astype(np.float32)
    proj = fx.xx * 0.7 - fx.yy * 0.7                  # diagonal shimmer direction

    # distinct data-sparks seeded on bright grid nodes
    ys, xs = np.where(anim > 0.5)
    NP = 340
    pick = rng.choice(len(xs), min(NP, len(xs)), replace=False)
    mx, my = xs[pick].astype(np.float32), ys[pick].astype(np.float32)
    msz = rng.uniform(1.8, 3.6, len(mx)).astype(np.float32)
    mph = rng.uniform(0, 6.28, len(mx)).astype(np.float32)
    mspd = rng.uniform(28, 70, len(mx)).astype(np.float32)
    mup = rng.uniform(-18, 6, len(mx)).astype(np.float32)
    WHITE = np.array([225, 238, 255], np.float32)

    config = Config(fps=FPS, resolution=(W, H))
    cam = Camera(config)
    cam.cinematic_push(duration=DURATION, start_zoom=1.0, end_zoom=1.06)
    cam.add_shake(intensity=0.0015, frequency=1.0, seed=4)

    def frame(t):
        f = base.copy()
        # grid node twinkle
        f *= (1 + 0.5 * anim[..., None] * np.sin(2 * np.pi * 1.4 * t + phase)[..., None])
        # traveling shimmer along the grid
        wave = 0.5 + 0.5 * np.sin(proj * 0.05 - t * 6.0)
        f += (anim * wave)[..., None] * WHITE * 0.45

        # scanner beam sweeping across face+grid, with a bright "scanned" wake
        bf = 0.44 + 0.56 * (0.5 - 0.5 * np.cos(2 * np.pi * t / DURATION))
        beam = np.exp(-((tcx - bf) ** 2) / (2 * 0.011 ** 2)) * smooth(0.34, 0.5, tcx)
        f += beam[..., None] * np.array([170, 205, 255], np.float32) * 1.3
        wake = smooth(bf, bf - 0.18, tcx) * anim          # just-scanned grid glows
        f += wake[..., None] * WHITE * 0.6

        # data-sparks streaking off the grid (with trails)
        buf = np.zeros((H, W, 3), np.float32)
        prog = (t % 2.4)
        cxp = mx + mspd * prog
        cyp = my + mup * prog
        fl = 0.5 + 0.5 * np.sin(t * 6 + mph)
        life = 1 - prog / 2.4
        colm = WHITE * (fl * life)[:, None] * (msz / 2.5)[:, None]
        for k, wgt in ((1.0, 1.0), (0.7, 0.6), (0.42, 0.35), (0.18, 0.2)):
            xi = np.round(mx + (cxp - mx) * k).astype(np.int32)
            yi = np.round(my + (cyp - my) * k).astype(np.int32)
            inb = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
            np.add.at(buf, (yi[inb], xi[inb]), colm[inb] * wgt)
        glow = np.asarray(Image.fromarray(buf.clip(0, 255).astype(np.uint8))
                          .filter(ImageFilter.GaussianBlur(2.2)), np.float32)
        f += buf * 0.5 + glow * 1.6

        # cinematic finish
        f = fx.bloom(f, sigma=6, thr=202, gain=0.8)
        f = fx.chromatic(f, 0.4)
        (cx, cy), zoom = cam.get_state(t)
        cw, ch = W / zoom, H / zoom
        left = float(np.clip((W - cw) / 2 + cx * W, 0, W - cw))
        top = float(np.clip((H - ch) / 2 + cy * H, 0, H - ch))
        f = np.asarray(Image.fromarray(f.clip(0, 255).astype(np.uint8))
                       .crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS), np.float32)
        f = fx.grain(f, t * FPS, amt=0.02)
        f = fx.vignette(f, 0.34)
        return f.clip(0, 255).astype(np.uint8)

    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(frame(a.preview)).save("fd_prev.png"); print("preview saved"); return
    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "17", "-preset", "slow",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames {W}x{H} ...")
    for i in range(n):
        writer.append_data(frame(i / FPS))
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{n}")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
