"""
Demo: the upgraded environment (world.py) + weighted movement (motion.py).
The Keeper walks in from the left, decelerates and settles (spring overshoot),
stands and breathes — with body-dip on footfalls, lean-into-motion, a dragging
cloak, and a lantern that lags behind the hand. Richer atmospheric world beneath.
"""
import os, math
import numpy as np
from PIL import Image
import imageio.v2 as imageio, imageio_ffmpeg, subprocess

from cineengine.generator import FX
from character import character
import world
from motion import Walker

W, H = 1080, 1920
FPS = 24
DUR = 8.0
fx = FX(W, H)
TERR = "home_fields"
BG = world.build(TERR)
FEET = 0.82


def glow(a, cx, cy, rad, color, alpha):
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.32), 0, 1) ** 0.7 * alpha
    a[y0:y1, x0:x1] += disc[..., None] * np.array(color, np.float32)


walker = Walker(-0.15, FEET, k=42.0, zeta=0.62)   # low k + underdamped = weighty ease + settle


def target_x(t):
    if t < 5.0: return 0.5           # walk in and settle at center
    return 0.5


def render(i):
    t = i / FPS; dt = 1.0 / FPS
    st = walker.update(target_x(t), dt, W, H, hand_dx=0, hand_dy=0)
    a = BG.copy()
    world.atmosphere(a, t, TERR)

    face = 1 if st["vx"] >= -1e-4 else -1
    pose = "walk" if st["walking"] else "stand"
    spr, fy, odx, ody = character(150, pose, t, face, lean=st["lean"], trail=st["trail"])
    kx = st["x"] * W
    ky = FEET * H + st["dip"]
    # lantern lags behind the hand (secondary motion) — feed the hand target to the walker
    hx = kx + odx; hy = ky + ody
    lx, ly = walker.light.step(hx, hy, dt)
    glow(a, lx, ly, 26, [255, 200, 130], 0.95 * (0.92 + 0.08 * math.sin(t * 3)))
    # a few embers trailing the lantern
    for k in range(3):
        ph = t * 1.3 + k * 2.1
        glow(a, lx + 14 * math.sin(ph), ly - 18 - 10 * ((t * 0.6 + k) % 1),
             2.5, [255, 210, 150], 0.4 * (0.6 + 0.4 * math.sin(ph)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - fy)), spr)
    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, i, amt=0.014)
    return frame.clip(0, 255).astype(np.uint8)


def main():
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DUR * FPS)
    writer = imageio.get_writer("motion_demo.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    for i in range(n):
        writer.append_data(render(i))
    writer.close()
    print("Done -> motion_demo.mp4")


if __name__ == "__main__":
    main()
