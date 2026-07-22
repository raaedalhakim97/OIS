"""
"The Walking" — a short animated meditation on the search for meaning.

A lone silhouette crosses dawn plains toward a distant light, climbs through a
storm to a summit expecting an answer, finds only sky — then looks back and
sees the whole path behind glowing with every step. The meaning was the walking.

Minimalist silhouette style: gradient skies, a solid figure, symbolic light,
narration. CPU only (numpy + PIL), engine effects for the finish.
"""
import os, sys, argparse, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX

W, H = 1080, 1920
FPS = 24
DURATION = 30.0
OUT = "meaning.mp4"
fx = FX(W, H)
INK = (14, 16, 24)


def lerp(a, b, x):
    return a + (b - a) * max(0.0, min(1.0, x))


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


FN = font(52)


def sky(top, bot, hor=1.0):
    a = np.zeros((H, W, 3), np.float32)
    t = (np.linspace(0, 1, H, dtype=np.float32) / hor).clip(0, 1)[:, None]
    a[:] = (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t)[:, None, :]
    return a


def add_stars(a, n, seed, ymax=0.8, bright=200):
    r = np.random.default_rng(seed)
    ys = r.integers(0, int(H * ymax), n); xs = r.integers(0, W, n)
    b = r.uniform(0.3, 1.0, n)
    for i in range(n):
        a[ys[i], xs[i]] += bright * b[i]
    return a


# ---------------- backgrounds (static parts) ----------------
def bg_plain(dawn=True):
    if dawn:
        a = sky([40, 44, 92], [235, 150, 96])
    else:
        a = sky([54, 96, 150], [206, 220, 236])
    gy = int(0.82 * H)
    a[gy:] = np.array([20, 20, 30], np.float32)
    a[gy:gy + 4] *= 1.6
    return a


def bg_mountain():
    a = sky([64, 68, 92], [118, 120, 146])       # lighter storm sky (silhouettes read)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # big dark mountain rising, clearly darker than sky
    d.polygon([(0, H), (0, int(0.78 * H)), (int(0.62 * W), int(0.26 * H)),
               (int(0.78 * W), int(0.40 * H)), (W, int(0.62 * H)), (W, H)], fill=(32, 34, 48))
    return np.asarray(im, np.float32)


def add_rim(a, cx, cy, r=90, color=(120, 132, 170), alpha=0.4):
    """Soft cool halo so a dark silhouette separates from a dark background."""
    glow(a, cx, cy, r, color, alpha)


def bg_summit():
    a = sky([5, 6, 16], [18, 26, 48])
    a = add_stars(a, 150, 7, 0.75, 210)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.polygon([(0, H), (int(0.30 * W), int(0.60 * H)), (int(0.5 * W), int(0.50 * H)),
               (int(0.70 * W), int(0.60 * H)), (W, H)], fill=(12, 13, 22))
    return np.asarray(im, np.float32)


def bg_lookback():
    a = sky([6, 8, 20], [16, 22, 42])
    a = add_stars(a, 170, 9, 0.7, 220)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # a summit ledge at the bottom, valley opening below
    d.polygon([(0, H), (0, int(0.80 * H)), (int(0.35 * W), int(0.74 * H)),
               (int(0.65 * W), int(0.78 * H)), (W, int(0.72 * H)), (W, H)], fill=(11, 12, 20))
    return np.asarray(im, np.float32)


BG = {
    "A": bg_plain(True), "B": bg_plain(False),
    "C": bg_mountain(), "D": bg_summit(), "E": bg_lookback(),
}


# ---------------- silhouette figure ----------------
def figure_sprite(s, pose, ph, face=1):
    """RGBA silhouette. s = pixel height. poses: stand, walk, climb, sit, back."""
    S = 2  # supersample the sprite
    C = int(s * 1.6) * S
    im = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = C // 2
    top = int(C * 0.12)
    hs = s * S
    head_r = hs * 0.12
    # anchor: feet near bottom
    hipy = top + hs * 0.55
    sh = top + hs * 0.30
    lw = int(hs * 0.09)      # limb width
    col = INK + (255,)

    def limb(x0, y0, x1, y1):
        d.line([(x0, y0), (x1, y1)], fill=col, width=lw)
        d.ellipse([x1 - lw / 2, y1 - lw / 2, x1 + lw / 2, y1 + lw / 2], fill=col)

    if pose == "walk":
        a = math.sin(ph) * hs * 0.16
        limb(cx, hipy, cx - a, hipy + hs * 0.42)
        limb(cx, hipy, cx + a, hipy + hs * 0.42)
        limb(cx, sh, cx + a * 0.7, sh + hs * 0.28)
        limb(cx, sh, cx - a * 0.7, sh + hs * 0.28)
        bx, by = cx, sh
    elif pose == "climb":
        limb(cx, hipy, cx - hs * 0.12, hipy + hs * 0.40)
        limb(cx, hipy, cx + hs * 0.16, hipy + hs * 0.30)     # front leg up
        reach = math.sin(ph) * hs * 0.05
        limb(cx, sh, cx + hs * 0.22, sh - hs * 0.24 - reach)  # arms reaching up-slope
        limb(cx, sh, cx + hs * 0.10, sh - hs * 0.30 + reach)
        bx, by = cx, sh
    elif pose == "reach":
        limb(cx, hipy, cx - hs * 0.10, hipy + hs * 0.42)
        limb(cx, hipy, cx + hs * 0.10, hipy + hs * 0.42)
        limb(cx, sh, cx - hs * 0.16, sh - hs * 0.34)          # both arms up
        limb(cx, sh, cx + hs * 0.16, sh - hs * 0.34)
        bx, by = cx, sh
    elif pose == "sit":
        hipy2 = top + hs * 0.74
        limb(cx, hipy2, cx - hs * 0.30, hipy2 + hs * 0.06)
        limb(cx, hipy2, cx + hs * 0.30, hipy2 + hs * 0.06)
        limb(cx, hipy2 - hs * 0.12, cx - hs * 0.14, hipy2 + hs * 0.02)
        limb(cx, hipy2 - hs * 0.12, cx + hs * 0.14, hipy2 + hs * 0.02)
        sh = hipy2 - hs * 0.30
        bx, by = cx, sh
    else:  # stand / back
        limb(cx, hipy, cx - hs * 0.06, hipy + hs * 0.42)
        limb(cx, hipy, cx + hs * 0.06, hipy + hs * 0.42)
        limb(cx, sh, cx - hs * 0.10, sh + hs * 0.26)
        limb(cx, sh, cx + hs * 0.10, sh + hs * 0.26)
        bx, by = cx, sh

    # torso
    d.line([(bx, by), (cx, hipy if pose != "sit" else top + hs * 0.62)], fill=col, width=int(hs * 0.16))
    # head
    hy = (by if pose in ("sit",) else sh) - hs * 0.10
    d.ellipse([cx - head_r, hy - head_r * 2, cx + head_r, hy], fill=col)

    im = im.resize((C // S, C // S), Image.LANCZOS)
    return im


def place_figure(base_img, sprite, cx, cy):
    sw, sh = sprite.size
    base_img.paste(sprite, (int(cx - sw / 2), int(cy - sh)), sprite)


def glow(arr, cx, cy, rad, color, alpha):
    d2 = (fx.xx - cx) ** 2 + (fx.yy - cy) ** 2
    g = np.exp(-d2 / (2 * rad ** 2)) * alpha
    arr += g[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.3), 0, 1) ** 0.7 * alpha
    arr += disc[..., None] * np.array(color, np.float32)


NARR = {
    "A": "We are born searching —\nfor a light we cannot name.",
    "B": "So we walk.\nToward something always just ahead.",
    "C": "We climb. We fall.\nWe ask what any of it is for.",
    "D": "At the summit we find\nno answer waiting. Only sky.",
    "E": "Then we look back —\nand the light was every step.",
    "E2": "The meaning was the walking.",
}


def draw_text(im, key, fade, y=0.12):
    if fade <= 0.01:
        return
    d = ImageDraw.Draw(im, "RGBA")
    a = int(235 * fade)
    yy = int(H * y)
    for ln in NARR[key].split("\n"):
        bb = d.textbbox((0, 0), ln, font=FN)
        x = (W - (bb[2] - bb[0])) // 2
        d.text((x, yy), ln, font=FN, fill=(232, 230, 224, a))
        yy += int((bb[3] - bb[1]) * 1.6)


# ---------------- scene composers ----------------
GROUND = 0.82 * H


def scene(t):
    """Return (numpy frame pre-global-FX)."""
    # ---- pick scene + local time (with 1s crossfades handled by caller via blend) ----
    if t < 6.5:      # A: dawn plain, stands then starts walking, distant light
        a = BG["A"].copy()
        lp = 0.5 + 0.5 * math.sin(t * 1.5)
        glow(a, 0.72 * W, 0.76 * H, 26, [255, 210, 150], 0.5 + 0.3 * lp)
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        walk = smooth(3.0, 4.0, t)
        cx = lerp(0.22, 0.30, smooth(3, 6.5, t)) * W
        pose = "walk" if walk > 0.2 else "stand"
        place_figure(im, figure_sprite(150, pose, t * 7), cx, GROUND)
        draw_text(im, "A", smooth(0.6, 1.6, t) * (1 - smooth(5.2, 6.4, t)))
        return np.asarray(im, np.float32)

    if t < 13:       # B: walking the plain, light a bit closer/brighter
        a = BG["B"].copy()
        lp = 0.5 + 0.5 * math.sin(t * 1.5)
        glow(a, 0.74 * W, 0.74 * H, 34, [255, 226, 180], 0.6 + 0.3 * lp)
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        cx = lerp(0.30, 0.44, smooth(6.5, 13, t)) * W
        place_figure(im, figure_sprite(150, "walk", t * 7), cx, GROUND)
        draw_text(im, "B", smooth(7.0, 8.0, t) * (1 - smooth(11.6, 12.8, t)))
        return np.asarray(im, np.float32)

    if t < 20:       # C: climbing the storm mountain, rain, light near peak
        a = BG["C"].copy()
        glow(a, 0.60 * W, 0.30 * H, 30, [210, 220, 255], 0.5)
        u = smooth(13, 20, t)
        cx = lerp(0.16, 0.52, u) * W
        cy = lerp(0.80, 0.42, u) * H
        add_rim(a, cx, cy - 55, 80, (140, 150, 195), 0.42)      # halo behind climber
        # rain
        r = np.random.default_rng(int(t * 24))
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(im)
        for _ in range(120):
            rx = r.integers(0, W); ry = r.integers(0, H)
            dr.line([(rx, ry), (rx - 6, ry + 26)], fill=(170, 178, 205, 120), width=2)
        place_figure(im, figure_sprite(120, "climb", t * 6), cx, cy)
        draw_text(im, "C", smooth(13.6, 14.6, t) * (1 - smooth(18.6, 19.8, t)))
        return np.asarray(im, np.float32)

    if t < 26:       # D: summit; reaches the light; it dissolves into stars
        a = BG["D"].copy()
        u = smooth(20, 23, t)
        dissolve = smooth(22.5, 25.0, t)
        glow(a, 0.5 * W, 0.34 * H, lerp(34, 8, dissolve), [230, 235, 255], (1 - dissolve) * 0.9)
        if dissolve > 0.2:      # light scatters into extra stars
            rr = np.random.default_rng(3)
            for _ in range(int(120 * dissolve)):
                ang = rr.uniform(0, 6.28); rad = rr.uniform(0, 400) * dissolve
                sx = int(0.5 * W + math.cos(ang) * rad); sy = int(0.34 * H + math.sin(ang) * rad)
                if 0 <= sx < W and 0 <= sy < H:
                    a[sy, sx] += 200
        cx = lerp(0.34, 0.5, u) * W
        cy = lerp(0.60, 0.50, u) * H
        add_rim(a, cx, cy - 55, 85, (110, 120, 165), 0.5)      # backlight at summit
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        pose = "reach" if 21 < t < 23.5 else "stand"
        place_figure(im, figure_sprite(120, pose, t * 5), cx, cy)
        draw_text(im, "D", smooth(20.6, 21.6, t) * (1 - smooth(24.6, 25.8, t)))
        return np.asarray(im, np.float32)

    # E: look back — path of light behind, then sits
    a = BG["E"].copy()
    # a winding path of glowing points receding into the valley (every step)
    npts = 60
    for i in range(npts):
        p = i / npts
        px = (0.5 + 0.30 * math.sin(p * 3.4)) * W * (1 - p) + 0.5 * W * p
        py = (0.78 - 0.5 * p) * H
        rad = lerp(9, 2, p)
        glow(a, px, py, rad, [255, 214, 150], 0.8 * (1 - p * 0.5))
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    sit = smooth(28.4, 29.2, t)
    pose = "sit" if sit > 0.5 else "back"
    place_figure(im, figure_sprite(150, pose, 0), 0.5 * W, 0.80 * H)
    draw_text(im, "E", smooth(26.4, 27.4, t) * (1 - smooth(28.2, 28.8, t)))
    draw_text(im, "E2", smooth(28.8, 29.6, t), y=0.5)
    return np.asarray(im, np.float32)


BOUNDS = (6.5, 13, 20, 26)


def render(t):
    frame = scene(t)
    # short dip-to-dark crossfade at scene borders
    for b in BOUNDS:
        if abs(t - b) < 0.35:
            dip = 1 - abs(t - b) / 0.35        # 0..1..0
            frame = frame * (1 - 0.7 * dip)
    frame = fx.bloom(frame, sigma=9, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.45)
    frame = fx.grain(frame, t * FPS, amt=0.018)
    return frame.clip(0, 255).astype(np.uint8)


def main():
    import imageio.v2 as imageio
    import imageio_ffmpeg
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("mn_prev.png"); print("preview saved"); return
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
