"""
"The Light Across" — a short on loneliness and connection.

Two figures stand alone on separate rooftops in a vast city of lit windows,
each feeling unseen. One notices the other; a small light reaches across the
dark between them. We were never as alone as we feared.

Same silhouette style + grounded figure + fast local-glow pipeline.
"""
import os, sys, argparse, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from letting_go import figure, place, glow, FN  # reuse grounded figure + helpers

W, H = 1080, 1920
FPS = 24
DURATION = 22.0
OUT = "connection.mp4"
fx = FX(W, H)

# rooftop anchor points (feet stand here)
AX, AY = 0.24 * W, 0.56 * H       # our figure (left)
BX, BY = 0.77 * W, 0.47 * H       # the other (right)


def lerp(a, b, x):
    return a + (b - a) * max(0.0, min(1.0, x))


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------- city background (precomputed) ----------------
def build_city():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([10, 12, 28], np.float32) * (1 - t)
            + np.array([26, 30, 54], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # moon (upper-left, clear of the centered narration) + stars
    mx, my, mr = 0.14 * W, 0.30 * H, 52
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(226, 228, 238))
    rr = np.random.default_rng(6)
    for _ in range(120):
        sx = rr.integers(0, W); sy = rr.integers(0, int(0.40 * H))
        b = rr.integers(120, 220); d.point((sx, sy), fill=(b, b, b))

    def tower(cx, w, top, shade):
        d.rectangle([cx - w / 2, top, cx + w / 2, H], fill=shade)
        # window grid
        gx = int(w // 26); gy = int((H - top) // 30)
        for ix in range(gx):
            for iy in range(gy):
                wx = cx - w / 2 + 10 + ix * 26
                wy = top + 14 + iy * 30
                if rr.random() < 0.5:
                    lit = rr.random() < 0.55
                    col = (255, 198, 120) if lit else (40, 44, 66)
                    d.rectangle([wx, wy, wx + 12, wy + 16], fill=col)

    # background clutter of buildings (dark, deep)
    rr2 = np.random.default_rng(11)
    x = -20
    while x < W:
        bw = rr2.integers(70, 150); top = rr2.uniform(0.60, 0.78) * H
        tower(x + bw / 2, bw, top, (18, 20, 38))
        x += bw + rr2.integers(-10, 20)
    # the two rooftop towers (mid depth), rooftops at AY/BY
    tower(AX, 150, AY, (24, 26, 46))
    tower(BX, 140, BY, (22, 24, 44))
    return np.asarray(im, np.float32)


CITY = build_city()

NARR = {
    "A": "In a city of a million lights,\nwe can still feel unseen.",
    "B": "Everyone behind their own glass.\nSo near. So far.",
    "C": "Then — someone,\nlooking back.",
    "D": "One small signal\nacross the dark.",
    "E": "We were never\nas alone as we feared.",
}


def text(im, key, fade, y=0.12):
    if fade <= 0.01:
        return
    d = ImageDraw.Draw(im, "RGBA")
    a = int(235 * fade); yy = int(H * y)
    for ln in NARR[key].split("\n"):
        bb = d.textbbox((0, 0), ln, font=FN)
        d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FN, fill=(232, 230, 224, a))
        yy += int((bb[3] - bb[1]) * 1.6)


def draw_thread(im, strength, t):
    """glowing arc between the two figures, brightening with strength."""
    if strength <= 0.01:
        return
    d = ImageDraw.Draw(im, "RGBA")
    ax, ay = AX, AY - 150 * 0.62
    bx, by = BX, BY - 150 * 0.62
    ccx, ccy = (ax + bx) / 2, min(ay, by) - 0.12 * H
    pts = []
    n = 48
    for i in range(n + 1):
        u = i / n
        px = (1 - u) ** 2 * ax + 2 * (1 - u) * u * ccx + u ** 2 * bx
        py = (1 - u) ** 2 * ay + 2 * (1 - u) * u * ccy + u ** 2 * by
        pts.append((px, py))
    a = int(220 * strength)
    d.line(pts, fill=(255, 210, 150, a), width=max(1, int(3 * strength)))
    # a travelling pulse of light along the thread
    pu = (t * 0.5) % 1.0
    i = int(pu * n)
    return pts[i]


def render(t):
    a = CITY.copy()

    # our figure always present (left). face toward the other once noticed.
    facing = 1
    noticed = t > 10
    # other figure's light appears at ~10s
    other_glow = smooth(10, 12.5, t)
    if other_glow > 0.01:
        glow(a, BX, BY - 95, 44, [255, 200, 130], 0.5 * other_glow)

    # forming connection thread
    conn = smooth(14, 18, t)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))

    # thread (behind figures)
    pulse = None
    if conn > 0.01:
        pulse = draw_thread(im, conn, t)

    # our figure pose
    if t < 10:
        poseA = "stand"
    elif t < 14:
        poseA = "stand"           # turned, noticing (face right)
    else:
        poseA = "handout"         # raising a hand / signalling
    place(im, figure(150, poseA, t * 5, face=1), AX, AY)

    # the other figure (appears with the glow)
    if other_glow > 0.2:
        spr = figure(150, "handout" if t > 14 else "stand", t * 5, face=-1)
        # fade it in
        s, fy = spr
        s2 = s.copy(); s2.putalpha(s.split()[3].point(lambda p: int(p * other_glow)))
        place(im, (s2, fy), BX, BY)

    # pulse glow node on the thread
    if pulse is not None and conn > 0.3:
        a2 = np.asarray(im, np.float32)
        glow(a2, pulse[0], pulse[1], 16, [255, 225, 170], 0.7 * conn)
        im = Image.fromarray(a2.clip(0, 255).astype(np.uint8))

    # narration
    if t < 5:
        text(im, "A", smooth(0.6, 1.6, t) * (1 - smooth(4.2, 4.9, t)))
    elif t < 10:
        text(im, "B", smooth(5.4, 6.4, t) * (1 - smooth(9.2, 9.9, t)))
    elif t < 14:
        text(im, "C", smooth(10.4, 11.4, t) * (1 - smooth(13.2, 13.9, t)))
    elif t < 18:
        text(im, "D", smooth(14.4, 15.4, t) * (1 - smooth(17.2, 17.9, t)))
    else:
        text(im, "E", smooth(18.6, 19.6, t))

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=7, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.017)
    return frame.clip(0, 255).astype(np.uint8)


def main():
    import imageio.v2 as imageio
    import imageio_ffmpeg
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    aa = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if aa.preview is not None:
        Image.fromarray(render(aa.preview)).save("cn_prev.png"); print("preview saved"); return
    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0:
            print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
