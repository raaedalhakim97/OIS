"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 4 — "The Home of Five"
Cut to Magnus's music (ep4_music.wav, ~2:02). The Keeper travels dawn→morning→
golden→dusk gathering four notes home to the scale (call-and-response), then WINTER:
the last note (F, the root) is frozen and afraid, and under the high-strings climax
the cold presses in; he reaches, it shrinks; at the quiet drop he stops — you cannot
carry a note home. Then he plays the others, and the last note comes on its own; the
scale runs whole; the world sings. Calm motion; the picture serves the music.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
import title_card as tc
import world

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ep4_music.wav")
SDUR = 116.6
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; COLD = [150, 172, 224]
CENTER_Y = 0.46
CH, EP, TITLE, LAND = "I", "4", "The Home of Five", "the Home Fields"


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
def gfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(48); FSM = font(34); GF = gfont(50)


def glow(a, cx, cy, rad, color, alpha):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.32), 0, 1) ** 0.7 * alpha
    a[y0:y1, x0:x1] += disc[..., None] * np.array(color, np.float32)


def darken(a, cx, cy, rad, strength):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    m = np.exp(-((xg - cx) ** 2 + (yg - cy) ** 2) / (2 * rad ** 2)) * strength
    a[y0:y1, x0:x1] *= (1 - m)[..., None]


SCENES = ["night", "dawn", "morning", "golden", "dusk", "winter"]
WORLDS = {s: world.build(s) for s in SCENES}
SEGS = [(0, "night"), (8, "dawn"), (24, "morning"), (40, "golden"),
        (56, "dusk"), (70, "winter"), (103, "night")]


def bg(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 2.5:
            f = smooth(s1 - 2.5, s1, ts)
            return WORLDS[n0] * (1 - f) + WORLDS[n1] * f, (n1 if f > 0.5 else n0)
    return WORLDS[n0], n0


STEPS = [(0.30 + i * 0.085, 0.72 - i * 0.045) for i in range(5)]
NOTES = [
    dict(nm="F", m=53, step=0, seat=106.0, found=(0.86, 0.60), col=COLD, refuse=True),
    dict(nm="G", m=55, step=1, seat=22.0, found=(0.80, 0.48), col=GOLD),
    dict(nm="A", m=57, step=2, seat=36.0, found=(0.82, 0.40), col=GOLD),
    dict(nm="C", m=60, step=3, seat=52.0, found=(0.80, 0.44), col=GOLD),
    dict(nm="D", m=62, step=4, seat=66.0, found=(0.82, 0.38), col=GOLD),
]
# call-and-response glyphs: (time, x, y, glyph) — Keeper calls, then the note answers
GLYPHS = []
for nt in NOTES[1:]:
    seat = nt["seat"]
    GLYPHS.append((seat - 6.0, "keeper"))       # Keeper sings (resolved below to keeper pos)
    GLYPHS.append((seat - 4.0, nt["found"]))    # the note answers

CAPS = [
    (1.5, 6.0, "the song broke into five.\nfive notes, lost in the world."),
    (6.6, 10.0, "he went to bring them home."),
    (12.0, 17.0, "the first was restless —\nalways somewhere else."),
    (27.5, 32.5, "the second was bright,\nand lonely inside it."),
    (43.0, 48.0, "the third would not come\nwithout the one it kept."),
    (57.0, 62.0, "the fourth was a dreamer —\nit only needed company."),
    (74.0, 80.0, "the last one was afraid."),
    (86.0, 93.0, "he reached for it —\nand it shrank away."),
    (97.5, 102.0, "you cannot\ncarry a note home."),
    (103.5, 108.0, "so he played the others —\nand made a home worth coming to."),
    (108.6, 112.8, "and the last note\ncame on its own."),
    (113.6, 116.6, "the more you know,\nthe more you observe."),
]


def note_pos(nt, ts):
    fx_, fy_ = nt["found"]; sx, sy = STEPS[nt["step"]]
    seat = nt["seat"]
    if nt.get("refuse"):
        if ts < 103:
            shrink = smooth(78, 96, ts) * (1 - smooth(102, 103, ts))     # shrinks as he reaches
            fl = 0.30 + 0.12 * math.sin(ts * 3.0)
            return fx_, fy_, (fl) * (1 - 0.6 * shrink)
        p = smooth(103.5, seat, ts)
        return lerp(fx_, sx, p), lerp(fy_, sy, p), 0.4 + 0.6 * p
    if ts < seat - 3:
        return fx_ + 0.02 * math.sin(ts * 2.2 + nt["m"]), fy_ + 0.01 * math.sin(ts * 1.7), 0.7
    if ts < seat:
        p = smooth(seat - 3, seat, ts)
        return lerp(fx_, sx, p), lerp(fy_, sy, p), 0.8
    return sx, sy, 1.0


def keeper_x(ts):
    if ts < 8 or ts >= 103: return 0.30
    for k in range(1, len(SEGS) - 1):
        s0 = SEGS[k][0]; s1 = SEGS[k + 1][0]
        if s0 <= ts < s1:
            amp = 0.30 if SEGS[k][1] == "winter" else 0.24
            return 0.30 + amp * max(0.0, math.sin(math.pi * (ts - s0) / (s1 - s0)))
    return 0.30


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            f = FSM if txt.startswith("the more you know") else FS
            lines = txt.split("\n")
            total = sum(int(d.textbbox((0, 0), ln, font=f)[3] * 1.5) for ln in lines)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f); xx = (W - (bb[2] - bb[0])) // 2
                d.text((xx + 2, yy + 2), ln, font=f, fill=(0, 0, 0, int(150 * fade)))
                d.text((xx, yy), ln, font=f, fill=(238, 234, 226, int(240 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)


def draw_glyphs(im, ts, keeper_xy):
    d = ImageDraw.Draw(im, "RGBA")
    for (nt, who) in GLYPHS:
        age = ts - nt
        if 0 <= age <= 1.7:
            al = np.interp(age, [0, 0.3, 1.2, 1.7], [0, 1, 1, 0])
            if who == "keeper":
                x, y = keeper_xy[0] / W, keeper_xy[1] / H - 0.10
            else:
                x, y = who[0], who[1] - 0.03
            d.text((x * W, y * H - age * 34), "♪", font=GF,
                   fill=(255, 208, 146, int(230 * al)), anchor="mm")


def story(ts):
    a, scene = bg(ts)
    a = a.copy()
    world.atmosphere(a, ts, scene)

    # WINTER danger: the cold / the Silence presses in under the high strings, then recedes
    cold = smooth(72, 94, ts) * (1 - smooth(101, 104, ts))
    if cold > 0.01:
        darken(a, 1.15 * W, 0.5 * H, 0.6 * W, 0.55 * cold)
        darken(a, 0.5 * W, -0.1 * H, 0.7 * W, 0.3 * cold)

    for i, (sx, sy) in enumerate(STEPS):
        glow(a, sx * W, sy * H, 5, [96, 102, 136], 0.18)

    for nt in NOTES:
        nx, ny, nb = note_pos(nt, ts)
        run = 0.0
        if ts >= 104:
            order = [1, 2, 3, 4, 0, 4, 3, 2, 1]
            phase = (ts - 107.0) * 3.0
            for oi, stp in enumerate(order):
                if stp == nt["step"]:
                    run = max(run, math.exp(-((phase - oi) ** 2) / 0.5))
        glow(a, nx * W, ny * H, 11 + 5 * run, nt["col"],
             nb * (0.85 + 0.15 * math.sin(ts * 3 + nt["m"])) + 0.6 * run)

    def kxf(u): return keeper_x(u)
    kx = kxf(ts)
    vx = (kxf(ts + 0.05) - kxf(ts - 0.05)) / 0.10
    walking = abs(vx) > 0.0035
    lean = clamp(vx * 2.6, -0.10, 0.10)
    trail = clamp(-vx * 1.2, -0.06, 0.06)
    face = 1 if vx >= -1e-4 else -1
    spr, fy, odx, ody = character(132, "walk" if walking else "stand", ts, face, lean=lean, trail=trail)
    ky = 0.80
    kox = kx * W + odx; koy = ky * H + ody
    glow(a, kox, koy, 24, GOLD, 0.95 * (0.92 + 0.08 * math.sin(ts * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx * W - spr.size[0] / 2), int(ky * H - fy)), spr)
    draw_glyphs(im, ts, (kox, koy))
    draw_caption(im, ts)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.40)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess, wave, contextlib
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep4h5_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep4h5_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep4h5_silent.mp4", "-i", MUSIC, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "ch1_ep4_the_home_of_five.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep4_the_home_of_five.mp4")


if __name__ == "__main__":
    main()
