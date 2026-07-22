"""
"Letting Go" — a short animated meditation on loss and acceptance.

A figure sits beside a small warm light (someone they love). The light must
rise; they open their hands and let it climb into a sky that fills with stars.
It doesn't leave — it becomes the sky they walk beneath, and a glow they carry.

Improved silhouette figure with a proper FOOT BASELINE so it stands/sits
exactly on the ground. Fast local-glow pipeline. CPU only.
"""
import os, sys, argparse, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX

W, H = 1080, 1920
FPS = 24
DURATION = 22.0
GROUND = 0.84 * H
OUT = "letting_go.mp4"
fx = FX(W, H)
INK = (16, 18, 26)


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


# ---------------- fast local glow ----------------
def glow(a, cx, cy, rad, color, alpha):
    """Additive radial glow computed only on a local window (fast)."""
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    g = np.exp(-d2 / (2 * rad ** 2)) * alpha
    a[y0:y1, x0:x1] += g[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.35), 0, 1) ** 0.7 * alpha
    a[y0:y1, x0:x1] += disc[..., None] * np.array(color, np.float32)


# ---------------- background ----------------
def base_sky(night):
    top = np.array([12, 14, 30]) * (0.6 + 0.4 * night) + np.array([30, 28, 60]) * (1 - night)
    bot = np.array([20, 26, 52]) * (0.5 + 0.5 * night) + np.array([120, 80, 96]) * (1 - night)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a = (top.astype(np.float32) * (1 - t) + bot.astype(np.float32) * t)[:, None, :].repeat(W, 1).copy()
    a[int(GROUND):] = np.array([12, 12, 20], np.float32)
    return a


# precomputed star layer (added, scaled by night)
_r = np.random.default_rng(4)
STAR = np.zeros((H, W, 3), np.float32)
for _ in range(220):
    sx = _r.integers(0, W); sy = _r.integers(0, int(GROUND * 0.98))
    b = _r.uniform(0.3, 1.0) * 220
    STAR[sy, sx] += [b, b, b * 1.05]
STAR_PH = _r.uniform(0, 6.28, (H, W)).astype(np.float32)


# ---------------- figure (proper foot baseline) ----------------
def figure(hpx, pose, ph=0.0, face=1):
    """Return (RGBA sprite, foot_y) with feet at the sprite's baseline."""
    S = 2
    margin = int(hpx * 0.12)
    Cw = int(hpx * 0.95) * S
    Ch = int(hpx + 2 * margin) * S
    im = Image.new("RGBA", (Cw, Ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = Cw // 2
    h = hpx * S
    top = margin * S
    col = INK + (255,)
    # key joints (from top)
    headc = top + 0.10 * h; headr = 0.085 * h
    shoulder = top + 0.26 * h
    hip = top + 0.56 * h
    foot = top + h
    lw = int(0.075 * h)

    def limb(x0, y0, x1, y1, w=lw):
        d.line([(x0, y0), (x1, y1)], fill=col, width=w)
        d.ellipse([x1 - w / 2, y1 - w / 2, x1 + w / 2, y1 + w / 2], fill=col)

    sw = 0.13 * h        # shoulder half-width
    hw = 0.09 * h        # hip half-width

    if pose == "sit":
        # curled up, hugging knees (seated silhouette, head bowed)
        seat = foot
        # knees + shins along the ground, tucked in front
        limb(cx, seat - 0.30 * h, cx + 0.30 * h, seat, w=int(0.12 * h))    # thigh->knee down to feet
        limb(cx + 0.24 * h, seat, cx + 0.34 * h, seat, w=int(0.08 * h))    # foot
        # curled back/torso as a rounded mass
        d.ellipse([cx - 0.24 * h, seat - 0.44 * h, cx + 0.22 * h, seat - 0.02 * h], fill=col)
        # arm wrapping the knees
        limb(cx - 0.02 * h, seat - 0.30 * h, cx + 0.24 * h, seat - 0.06 * h, w=int(0.08 * h))
        # bowed head resting toward the knees
        hx = cx + 0.06 * h; hy = seat - 0.46 * h
        d.ellipse([hx - headr, hy - headr, hx + headr, hy + headr], fill=col)
        foot_y = seat
    else:
        # legs
        if pose == "walk":
            a = math.sin(ph) * 0.15 * h
            limb(cx - hw, hip, cx - a, foot); limb(cx + hw, hip, cx + a, foot)
        else:
            limb(cx - hw, hip, cx - 0.05 * h, foot); limb(cx + hw, hip, cx + 0.05 * h, foot)
        # torso (tapered)
        d.polygon([(cx - sw, shoulder), (cx + sw, shoulder),
                   (cx + hw, hip), (cx - hw, hip)], fill=col)
        # arms
        if pose == "reach":
            limb(cx - sw, shoulder, cx - 0.14 * h, shoulder - 0.30 * h)
            limb(cx + sw, shoulder, cx + 0.14 * h, shoulder - 0.30 * h)
        elif pose == "handout":
            limb(cx - sw, shoulder, cx - 0.10 * h, shoulder + 0.16 * h)
            limb(cx + sw, shoulder, cx + face * 0.26 * h, shoulder - 0.06 * h)   # one arm up/out
        elif pose == "walk":
            a = math.sin(ph) * 0.12 * h
            limb(cx - sw, shoulder, cx + a, shoulder + 0.24 * h)
            limb(cx + sw, shoulder, cx - a, shoulder + 0.24 * h)
        else:
            limb(cx - sw, shoulder, cx - 0.10 * h, shoulder + 0.26 * h)
            limb(cx + sw, shoulder, cx + 0.10 * h, shoulder + 0.26 * h)
        # neck + head
        d.line([(cx, shoulder), (cx, headc + headr)], fill=col, width=int(0.06 * h))
        d.ellipse([cx - headr, headc - headr, cx + headr, headc + headr], fill=col)
        foot_y = foot

    im = im.resize((Cw // S, Ch // S), Image.LANCZOS)
    return im, foot_y / S


def place(im, spr_fy, cx, ground_y):
    spr, fy = spr_fy
    sw, sh = spr.size
    im.paste(spr, (int(cx - sw / 2), int(ground_y - fy)), spr)


NARR = {
    "A": "Some people become\na light we carry.",
    "B": "And one day,\nthe light must rise.",
    "C": "So we open our hands —\nand let it climb.",
    "D": "It doesn't leave us.\nIt becomes the sky.",
    "E": "And we walk on,\ncarrying them in every step.",
}


def text(im, key, fade, y=0.13):
    if fade <= 0.01:
        return
    d = ImageDraw.Draw(im, "RGBA")
    a = int(235 * fade); yy = int(H * y)
    for ln in NARR[key].split("\n"):
        bb = d.textbbox((0, 0), ln, font=FN)
        d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FN, fill=(232, 230, 224, a))
        yy += int((bb[3] - bb[1]) * 1.6)


def render(t):
    night = smooth(3, 16, t)
    a = base_sky(night)
    if night > 0.02:
        tw = (0.5 + 0.5 * np.sin(t * 2 + STAR_PH))
        a += STAR * (night * tw)[..., None]

    # lantern light position over time
    if t < 5:      key, fy = "A", None
    lx = 0.5 * W
    if t < 5.5:
        ly = GROUND - 30
    else:
        rise = smooth(5.5, 14, t)
        ly = lerp(GROUND - 30, 0.22 * H, rise)
        lx = 0.5 * W + math.sin(rise * 3) * 26
    lantern_a = 1.0 - smooth(13, 16, t) * 0.35
    glow(a, lx, ly, lerp(30, 16, smooth(5.5, 15, t)), [255, 196, 120], lantern_a)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))

    # figure + narration by scene
    if t < 5:                       # sit beside the light
        place(im, figure(150, "sit"), 0.40 * W, GROUND)
        text(im, "A", smooth(0.6, 1.6, t) * (1 - smooth(4.0, 4.8, t)))
    elif t < 10:                    # stand, reach up as it lifts
        pose = "reach" if t > 6.5 else "stand"
        place(im, figure(160, pose), 0.42 * W, GROUND)
        text(im, "B", smooth(5.6, 6.6, t) * (1 - smooth(9.0, 9.8, t)))
    elif t < 15:                    # hand out, watching it climb
        place(im, figure(160, "handout"), 0.42 * W, GROUND)
        text(im, "C", smooth(10.4, 11.4, t) * (1 - smooth(14.0, 14.8, t)))
    elif t < 18.5:                  # alone under the stars
        place(im, figure(160, "stand"), 0.5 * W, GROUND)
        text(im, "D", smooth(15.4, 16.4, t) * (1 - smooth(17.4, 18.2, t)))
    else:                           # walks on, a glow in the chest
        cx = lerp(0.5, 0.66, smooth(18.5, 22, t)) * W
        im2 = np.asarray(im, np.float32)
        glow(im2, cx, GROUND - 90, 22, [255, 190, 120], 0.6)     # chest glow
        im = Image.fromarray(im2.clip(0, 255).astype(np.uint8))
        place(im, figure(160, "walk", t * 6), cx, GROUND)
        text(im, "E", smooth(19.2, 20.2, t))

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=7, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.017)
    return frame.clip(0, 255).astype(np.uint8)


def main():
    import imageio.v2 as imageio
    import imageio_ffmpeg
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("lg_prev.png"); print("preview saved"); return
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
