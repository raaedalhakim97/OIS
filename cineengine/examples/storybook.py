"""
20s children's-storybook animation of the nature lake:
day -> golden sunset -> starry night, with a little sailboat, birds,
fireflies and gentle storybook captions.

Scene backgrounds (day/dusk/night) are precomputed and blended over time;
only light sprites + effects are per-frame, so 20s stays fast.
Effects use the engine (generator.FX). Camera does a slow storybook drift.
"""
import os, sys, argparse
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX, fbm
import imageio.v2 as imageio
import imageio_ffmpeg  # noqa

W, H = 1080, 1920
FPS = 24
DURATION = 20.0
HOR = 0.60
WL = int(HOR * H)
OUT = "storybook.mp4"
fx = FX(W, H)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1.0)
    return t * t * (3 - 2 * t)


def font(sz, serif=True):
    for p in (("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf" if serif
               else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


# ---------------- precomputed scene backgrounds ----------------
def vgrad(top, bot):
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    return (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t)[:, None, :]


MOUNT = None
def mountains(shade):
    global MOUNT
    if MOUNT is None:
        xs = np.linspace(0, 1, W, dtype=np.float32)
        rng = np.random.default_rng(3)
        layers = []
        for i, amp in enumerate((0.045, 0.065, 0.085)):
            base = HOR - 0.02 + i * 0.012
            ridge = base - amp * np.sin(xs * (2.2 + i) * 6.28 + rng.uniform(0, 6)) \
                         - amp * 0.4 * np.sin(xs * (5 + i) * 6.28 + rng.uniform(0, 6))
            yy = (np.arange(H)[:, None] / H)
            layers.append(((yy > ridge[None, :]).astype(np.float32), 0.55 - i * 0.16))
        MOUNT = layers
    return MOUNT


def build_bg(sky_top, sky_bot, mtn_col, water_tint, water_k):
    img = np.repeat(vgrad(sky_top, sky_bot), W, axis=1).copy()
    for mask, sh in mountains(0):
        m = mask[..., None]
        img = img * (1 - m) + np.array(mtn_col, np.float32) * sh * m
    # water = reflect the top half, tint + darken
    top = img[:WL]
    refl = top[::-1][:H - WL]
    if refl.shape[0] < H - WL:
        refl = np.pad(refl, ((0, H - WL - refl.shape[0]), (0, 0), (0, 0)), mode="edge")
    depth = (np.arange(refl.shape[0]) / refl.shape[0])[:, None, None]
    refl = refl * (water_k - 0.25 * depth) + np.array(water_tint, np.float32) * (0.3 + 0.3 * depth)
    img[WL:] = np.clip(refl, 0, 255)
    return np.clip(img, 0, 255)


BG_DAY = build_bg([120, 170, 232], [214, 224, 246], [90, 120, 96], [60, 100, 150], 0.75)
BG_DUSK = build_bg([70, 56, 120], [255, 150, 92], [70, 60, 78], [120, 70, 90], 0.62)
BG_NIGHT = build_bg([8, 12, 34], [26, 34, 70], [26, 34, 48], [20, 34, 66], 0.5)

# stars (night) and fireflies (evening)
rng = np.random.default_rng(11)
star_x = rng.integers(0, W, 130); star_y = rng.integers(0, WL, 130)
star_b = rng.uniform(0.4, 1.0, 130); star_ph = rng.uniform(0, 6.28, 130)
NF = 46
ff_x = rng.uniform(0.06, 0.94, NF); ff_y = rng.uniform(HOR + 0.02, 0.97, NF)
ff_ph = rng.uniform(0, 6.28, NF); ff_sp = rng.uniform(0.1, 0.4, NF)

F_TITLE = font(70); F_CAP = font(46)


def glow(arr, cx, cy, rad, color, alpha):
    d2 = (fx.xx - cx) ** 2 + (fx.yy - cy) ** 2
    g = np.exp(-d2 / (2 * rad ** 2)) * alpha
    arr += g[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.32), 0, 1) ** 0.6 * alpha
    arr += disc[..., None] * np.array(color, np.float32) * 1.3


def celestial_reflection(arr, cx, alpha, color):
    gy = np.arange(H - WL)
    streak = np.exp(-((np.arange(W)[None, :] - cx) ** 2) / (2 * (34.0) ** 2))
    streak = streak * (1 - gy[:, None] / (H - WL)) ** 1.4 * alpha
    arr[WL:] += streak[..., None] * np.array(color, np.float32) * 0.7


CAPTIONS = [
    (0.4, 4.8, "Once upon a time,\nby a still blue lake…"),
    (5.2, 9.6, "the sun went down\nin colors of gold."),
    (10.2, 14.6, "One little boat\nsailed home for the night."),
    (15.2, 19.6, "and the stars whispered,\ngoodnight."),
]


def draw_sprites(pim, t, day_w, night_w):
    d = ImageDraw.Draw(pim, "RGBA")
    # boat drifts across the lake, with a soft reflection
    bx = int((0.14 + 0.62 * (t / DURATION)) * W)
    by = WL + 26
    hull = [(bx - 34, by), (bx + 34, by), (bx + 22, by + 16), (bx - 22, by + 16)]
    sailc = (250, 244, 230, 255)
    d.polygon(hull, fill=(30, 26, 30, 255))
    d.polygon([(bx, by - 60), (bx, by - 2), (bx + 30, by - 2)], fill=sailc)       # main sail
    d.polygon([(bx - 2, by - 50), (bx - 2, by - 2), (bx - 26, by - 2)], fill=(230, 224, 210, 255))
    d.line([(bx, by - 62), (bx, by)], fill=(60, 50, 44, 255), width=2)
    # reflection
    d.polygon([(bx - 30, by + 20), (bx + 30, by + 20), (bx, by + 70)], fill=(250, 244, 230, 60))

    # birds (day/dusk), gentle flap, drift
    if day_w > 0.05:
        a = int(200 * day_w)
        for k, (bxx, byy, ph) in enumerate([(0.30, 0.22, 0), (0.38, 0.26, 1.5), (0.46, 0.20, 3.0)]):
            cxp = int(((bxx + 0.05 * np.sin(t * 0.3 + ph)) + 0.03 * t / DURATION) * W)
            cyp = int((byy + 0.02 * np.sin(t * 0.5 + ph)) * H)
            fl = 8 + int(6 * np.sin(t * 4 + ph))
            d.line([(cxp - 16, cyp), (cxp, cyp - fl), (cxp + 16, cyp)], fill=(40, 40, 50, a), width=3)


def draw_text(pim, t):
    d = ImageDraw.Draw(pim, "RGBA")
    # title only in the first beat
    for (s, e, txt) in CAPTIONS:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.6, e - 0.6, e], [0, 1, 1, 0])
            a = int(255 * fade)
            lines = txt.split("\n")
            fnt = F_CAP
            yy = int(H * 0.10)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=fnt)
                w = bb[2] - bb[0]
                x = (W - w) // 2
                d.text((x + 2, yy + 2), ln, font=fnt, fill=(0, 0, 0, int(a * 0.6)))
                d.text((x, yy), ln, font=fnt, fill=(245, 240, 230, a))
                yy += int((bb[3] - bb[1]) * 1.5)


def render(t):
    wd = 1 - smooth(4, 8, t)
    wn = smooth(11, 15, t)
    wk = np.clip(1 - wd - wn, 0, 1)
    scene = BG_DAY * wd + BG_DUSK * wk + BG_NIGHT * wn

    # sun descends and sets (0..~10s)
    sun_p = np.clip(t / 10.0, 0, 1)
    sun_x = (0.36 + 0.26 * sun_p) * W
    sun_y = (0.26 + 0.34 * sun_p) * H
    sun_a = float(np.clip(1 - smooth(9, 11, t), 0, 1)) * (wd + wk)
    if sun_a > 0.01:
        glow(scene, sun_x, sun_y, 120, [255, 226, 170], sun_a)
        if sun_y < WL:
            celestial_reflection(scene, sun_x, sun_a, [255, 210, 150])
    # moon rises (12..20s)
    moon_p = np.clip((t - 12) / 8.0, 0, 1)
    moon_x = (0.66 - 0.14 * moon_p) * W
    moon_y = (0.58 - 0.34 * moon_p) * H
    moon_a = float(smooth(12, 15, t))
    if moon_a > 0.01:
        glow(scene, moon_x, moon_y, 90, [225, 232, 255], moon_a)
        if moon_y < WL:
            celestial_reflection(scene, moon_x, moon_a, [200, 215, 255])

    # stars fade in at night
    if wn > 0.02:
        tw = (0.6 + 0.4 * np.sin(t * 3 + star_ph)) * star_b * wn * 200
        scene[star_y, star_x] += np.stack([tw, tw, tw * 1.05], axis=1)
    # fireflies in the evening/night (lower area)
    ff_w = float(np.clip(smooth(8, 12, t), 0, 1))
    if ff_w > 0.02:
        for i in range(NF):
            px = int((ff_x[i] + 0.02 * np.sin(t * ff_sp[i] * 3 + ff_ph[i])) * W)
            py = int((ff_y[i] - 0.01 * t / DURATION * 5) % 1.0 * 0 + ff_y[i] * H)
            r = 7
            x0, x1 = max(0, px - r), min(W, px + r)
            y0, y1 = max(0, py - r), min(H, py + r)
            if x1 <= x0 or y1 <= y0:
                continue
            yg, xg = np.mgrid[y0:y1, x0:x1]
            fl = 0.4 + 0.6 * np.sin(t * 5 + ff_ph[i])
            g = np.exp(-((xg - px) ** 2 + (yg - py) ** 2) / (2 * 3.0 ** 2)) * fl * ff_w
            scene[y0:y1, x0:x1] += g[..., None] * np.array([255, 218, 140])

    # sprites (boat, birds)
    pim = Image.fromarray(scene.clip(0, 255).astype(np.uint8))
    draw_sprites(pim, t, wd + 0.5 * wk, wn)
    scene = np.asarray(pim, np.float32)

    # soft dreamy finish
    scene = fx.bloom(scene, sigma=8, thr=200, gain=0.6)
    # gentle storybook drift/zoom
    zoom = 1.02 + 0.05 * (t / DURATION)
    cw, ch = W / zoom, H / zoom
    left = (W - cw) / 2 + np.sin(t * 0.25) * 12
    top = (H - ch) / 2 + np.sin(t * 0.2) * 10
    left = float(np.clip(left, 0, W - cw)); top = float(np.clip(top, 0, H - ch))
    pim = Image.fromarray(scene.clip(0, 255).astype(np.uint8)).crop(
        (left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS)
    draw_text(pim, t)                       # captions fixed on top
    scene = np.asarray(pim, np.float32)
    scene = fx.grain(scene, t * FPS, amt=0.02)
    scene = fx.vignette(scene, 0.4)
    return scene.clip(0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("sb_prev.png"); print("preview saved"); return
    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ({DURATION}s storybook) ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0:
            print(f"  {i+1}/{n}  ({(i+1)/FPS:.0f}s)")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
