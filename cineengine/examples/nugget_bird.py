"""
'Nugget bird' cartoon: a round little bird hops around happily, finds pure
joy (hearts + sparkles), gets over-excited and comically falls down, then lies
dizzy with stars circling its head.

Pure CPU cartoon animation (PIL vector drawing + squash-and-stretch), rendered
at 1.5x supersample for smooth edges. ~13s, 1080x1920, 24fps.
"""
import os, sys, argparse, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX

W, H = 1080, 1920
SS = 1.5
SW, SH = int(W * SS), int(H * SS)
FPS = 24
DURATION = 13.0
GY = 0.80                      # ground line (fraction)
OUT = "nugget_bird.mp4"
fx = FX(W, H)

YELLOW = (252, 208, 66); YEL_D = (238, 184, 44); BELLY = (255, 240, 186)
ORANGE = (247, 146, 40); BLACK = (38, 32, 30); WHITE = (255, 255, 255)
PINK = (255, 150, 160)


def lerp(a, b, x):
    return a + (b - a) * max(0.0, min(1.0, x))


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------- background (precomputed) ----------------
def build_bg():
    im = Image.new("RGB", (SW, SH))
    d = ImageDraw.Draw(im)
    for y in range(SH):
        f = y / SH
        if f < GY:
            g = f / GY
            c = (int(lerp(150, 205, g)), int(lerp(205, 232, g)), int(lerp(245, 250, g)))
        else:
            g = (f - GY) / (1 - GY)
            c = (int(lerp(150, 110, g)), int(lerp(205, 165, g)), int(lerp(120, 92, g)))
        d.line([(0, y), (SW, y)], fill=c)
    # sun
    sx, sy, sr = int(SW * 0.80), int(SH * 0.16), int(SW * 0.09)
    for r, a in ((sr * 2, 40), (int(sr * 1.4), 90), (sr, 255)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 238, 170))
    # rolling hills
    d.ellipse([-SW * 0.3, SH * GY - SH * 0.05, SW * 0.5, SH * GY + SH * 0.3], fill=(120, 180, 100))
    d.ellipse([SW * 0.55, SH * GY - SH * 0.04, SW * 1.3, SH * GY + SH * 0.3], fill=(128, 188, 106))
    # flowers on the ground
    rng = np.random.default_rng(5)
    for _ in range(22):
        fxp = rng.uniform(0.03, 0.97) * SW
        fyp = rng.uniform(GY + 0.03, 0.98) * SH
        col = tuple(int(c) for c in rng.choice([[255, 120, 140], [255, 220, 90], [200, 150, 255]]))
        s = rng.uniform(6, 12) * SS
        for ang in range(0, 360, 72):
            px = fxp + s * math.cos(math.radians(ang)); py = fyp + s * math.sin(math.radians(ang))
            d.ellipse([px - s, py - s, px + s, py + s], fill=col)
        d.ellipse([fxp - s * 0.6, fyp - s * 0.6, fxp + s * 0.6, fyp + s * 0.6], fill=(255, 240, 150))
    return im


BG = build_bg()


def draw_cloud(d, cx, cy, s):
    for dx, dy, r in ((-1.1, 0, 1.0), (0, -0.4, 1.3), (1.1, 0, 1.0), (0, 0.1, 1.5)):
        d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s],
                  fill=(255, 255, 255))


# ---------------- the bird sprite ----------------
def bird_sprite(sq, expr, wing, blush, dir_, leg):
    """Return an RGBA sprite of the bird (centered), squash sq, expression, etc."""
    C = int(360 * SS)
    im = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = C // 2
    rx = 92 * SS * (1 + sq); ry = 92 * SS * (1 - sq)

    # feet
    fw = int(28 * SS * leg + 3)
    for s_ in (-1, 1):
        fx0 = cx + s_ * 34 * SS
        d.line([(fx0, cy + ry * 0.7), (fx0, cy + ry * 0.7 + fw)], fill=ORANGE, width=int(9 * SS))
        d.line([(fx0 - 14 * SS, cy + ry * 0.7 + fw), (fx0 + 14 * SS, cy + ry * 0.7 + fw)],
               fill=ORANGE, width=int(9 * SS))

    # wings (behind body a touch) - flap
    wa = 26 * math.sin(wing) * SS
    for s_ in (-1, 1):
        wx = cx + s_ * rx * 0.82
        d.polygon([(wx, cy - 10 * SS), (wx + s_ * 46 * SS, cy - 30 * SS - wa),
                   (wx + s_ * 40 * SS, cy + 34 * SS - wa)], fill=YEL_D)

    # body + belly
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=YELLOW, outline=YEL_D, width=int(4 * SS))
    d.ellipse([cx - rx * 0.6, cy - ry * 0.1, cx + rx * 0.6, cy + ry * 0.92], fill=BELLY)

    # blush
    if blush > 0.01:
        bc = (PINK[0], PINK[1], PINK[2], int(180 * blush))
        for s_ in (-1, 1):
            d.ellipse([cx + s_ * 46 * SS - 20 * SS, cy + 6 * SS - 12 * SS,
                       cx + s_ * 46 * SS + 20 * SS, cy + 6 * SS + 12 * SS], fill=bc)

    # beak (points in travel dir)
    bx = cx + dir_ * 40 * SS; by = cy + 4 * SS
    d.polygon([(bx, by - 12 * SS), (bx + dir_ * 34 * SS, by), (bx, by + 12 * SS)], fill=ORANGE)

    # eyes
    ex = 30 * SS; ey = -22 * SS
    if expr in ("happy", "joy"):
        for s_ in (-1, 1):        # upward happy arcs ^ ^
            x0 = cx + s_ * ex
            d.arc([x0 - 22 * SS, cy + ey - 8 * SS, x0 + 22 * SS, cy + ey + 26 * SS],
                  200, 340, fill=BLACK, width=int(8 * SS))
    elif expr == "blink":
        for s_ in (-1, 1):
            x0 = cx + s_ * ex
            d.line([(x0 - 16 * SS, cy + ey + 6 * SS), (x0 + 16 * SS, cy + ey + 6 * SS)],
                   fill=BLACK, width=int(8 * SS))
    elif expr == "ouch":         # X X eyes
        for s_ in (-1, 1):
            x0 = cx + s_ * ex; r = 16 * SS
            d.line([(x0 - r, cy + ey - r), (x0 + r, cy + ey + r)], fill=BLACK, width=int(8 * SS))
            d.line([(x0 - r, cy + ey + r), (x0 + r, cy + ey - r)], fill=BLACK, width=int(8 * SS))
    elif expr == "dizzy":        # spiral-ish @ @
        for s_ in (-1, 1):
            x0 = cx + s_ * ex
            for rr in (18 * SS, 11 * SS, 5 * SS):
                d.arc([x0 - rr, cy + ey - rr, x0 + rr, cy + ey + rr], 0, 300, fill=BLACK, width=int(5 * SS))
    else:                        # normal round eyes
        for s_ in (-1, 1):
            x0 = cx + s_ * ex; r = 20 * SS
            d.ellipse([x0 - r, cy + ey - r, x0 + r, cy + ey + r], fill=WHITE, outline=BLACK, width=int(3 * SS))
            pr = 11 * SS; px = x0 + dir_ * 4 * SS
            d.ellipse([px - pr, cy + ey - pr, px + pr, cy + ey + pr], fill=BLACK)
            d.ellipse([px - pr, cy + ey - pr - 3 * SS, px - pr + 7 * SS, cy + ey - pr + 4 * SS], fill=WHITE)

    # little tuft on head
    d.line([(cx, cy - ry), (cx - 6 * SS, cy - ry - 26 * SS)], fill=YEL_D, width=int(7 * SS))
    d.line([(cx, cy - ry), (cx + 10 * SS, cy - ry - 22 * SS)], fill=YEL_D, width=int(7 * SS))
    return im


def draw_heart(d, cx, cy, s, a):
    col = (255, 110, 130, a)
    d.ellipse([cx - s, cy - s, cx, cy], fill=col)
    d.ellipse([cx, cy - s, cx + s, cy], fill=col)
    d.polygon([(cx - s, cy - s * 0.1), (cx + s, cy - s * 0.1), (cx, cy + s)], fill=col)


def draw_star(d, cx, cy, s, a):
    col = (255, 230, 120, a)
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        r = s if i % 2 == 0 else s * 0.45
        pts.append((cx + r * math.cos(ang), cy - r * math.sin(ang)))
    d.polygon(pts, fill=col)


# ---------------- per-frame ----------------
def render(t):
    im = BG.copy()
    d = ImageDraw.Draw(im, "RGBA")
    # drifting clouds
    draw_cloud(d, (0.2 * SW + t * 8 * SS) % (SW + 300) - 150, SH * 0.12, 34 * SS)
    draw_cloud(d, (0.6 * SW + t * 5 * SS) % (SW + 300) - 150, SH * 0.20, 26 * SS)

    ground = GY * SH
    dir_ = 1
    blush = 0.0; expr = "normal"; leg = 1.0; rot = 0.0; wing = t * 14
    hearts = []; stars = []
    shake = 0.0

    if t < 4.6:
        # PHASE 1: hop happily left -> center
        prog = t / 4.6
        cx = lerp(0.16, 0.5, prog) * SW
        hop = (t / 0.62) % 1.0
        height = math.sin(math.pi * hop) * 150 * SS
        sq = 0.30 * (1 - height / (150 * SS)) - 0.10
        leg = 0.25 + 0.75 * (1 - math.sin(math.pi * hop))
        cy = ground - height - 92 * SS
        expr = "blink" if (t % 2.2) > 2.05 else "normal"
    elif t < 8.6:
        # PHASE 2: found pleasure! wiggle with joy, hearts + blush
        cx = 0.5 * SW
        u = t - 4.6
        bob = abs(math.sin(u * 4)) * 46 * SS
        cy = ground - bob - 92 * SS
        sq = 0.16 * math.sin(u * 8)
        rot = math.sin(u * 5) * 10
        expr = "joy"; blush = 1.0; wing = t * 22
        leg = 0.5
        for k in range(5):
            hp = (u * 0.6 + k * 0.2) % 1.0
            a = int(220 * (1 - hp))
            hx = 0.5 * SW + math.sin(k * 2 + u) * 90 * SS
            hy = ground - 92 * SS - 120 * SS - hp * 260 * SS
            hearts.append((hx, hy, (18 + k * 3) * SS, a))
    elif t < 9.3:
        # PHASE 3a: huge joyful leap
        u = (t - 8.6) / 0.7
        cx = 0.5 * SW
        height = math.sin(math.pi * u) * 420 * SS
        cy = ground - height - 92 * SS
        sq = -0.18
        expr = "joy"; blush = 1.0; leg = 0.15; wing = t * 30
        rot = u * 12
    elif t < 10.2:
        # PHASE 3b: it all goes wrong -> tumble down
        u = (t - 9.3) / 0.9
        cx = lerp(0.5, 0.56, u) * SW
        top = ground - 420 * SS
        cy = lerp(top, ground - 40 * SS, u * u)     # accelerate down
        rot = lerp(12, 200, u)                      # tumble over
        sq = -0.05
        expr = "ouch"; leg = 0.1
    else:
        # PHASE 4: flopped on ground, dizzy stars circling
        u = t - 10.2
        cx = 0.56 * SW
        land = min(u / 0.18, 1.0)
        cy = ground - lerp(40, 18, land) * SS
        sq = 0.34 if u < 0.35 else lerp(0.34, 0.24, min((u - 0.35) / 0.5, 1))  # splat then settle
        rot = 200
        expr = "dizzy"; leg = 0.05
        if u < 0.4:
            shake = (0.4 - u) * 26 * SS * math.sin(u * 60)
        for k in range(3):
            ang = u * 3 + k * 2.094
            sx = cx + math.cos(ang) * 70 * SS
            sy = cy - 130 * SS + math.sin(ang) * 26 * SS
            stars.append((sx, sy, 18 * SS, 230))

    # draw hearts (behind bird)
    for (hx, hy, s, a) in hearts:
        draw_heart(d, hx, hy, s, a)

    # bird sprite (rotated for tumble/wiggle)
    spr = bird_sprite(sq, expr, wing, blush, dir_, leg)
    if abs(rot) > 0.5:
        spr = spr.rotate(rot, resample=Image.BICUBIC, expand=True)
    sw, sh = spr.size
    im.paste(spr, (int(cx - sw / 2 + shake), int(cy - sh / 2)), spr)

    # dizzy stars (above head)
    d2 = ImageDraw.Draw(im, "RGBA")
    for (sx, sy, s, a) in stars:
        draw_star(d2, sx, sy, s, a)

    # downscale + gentle finish
    frame = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32)
    frame = fx.vignette(frame, 0.28)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


def main():
    import imageio.v2 as imageio
    import imageio_ffmpeg
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("nb_prev.png"); print("preview saved"); return
    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames nugget bird ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0:
            print(f"  {i+1}/{n}")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
