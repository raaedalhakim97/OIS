"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 5 — "The Home of Five"  (little-planet cut)
The grassy earth is a rotating ball: the Keeper walks in place on top while the world
turns beneath him (surface scrolls left as he walks right) and the day changes around
him — so he is always travelling and searching. Five lost notes rise over the turning
horizon and gather into an arch above him (F, the root, the keystone). Winter brings the
cold; the last note comes home; the arch completes. Cut to Magnus's music (ep4_music.wav).
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
import title_card as tc
import world, planet as pl

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 116.6
DUR = TITLE_DUR + SDUR
MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ep4_music.wav")
fx = FX(W, H)
GOLD = [255, 200, 130]; COLD = [150, 172, 224]
CENTER_Y = 0.46
CH, EP, TITLE, LAND = "I", "5", "The Home of Five", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX


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
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    m = np.exp(-((xg - cx) ** 2 + (yg - cy) ** 2) / (2 * rad ** 2)) * strength
    a[y0:y1, x0:x1] *= (1 - m)[..., None]


SCENES = ["night", "dawn", "morning", "golden", "dusk", "winter"]
for s in SCENES: pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "night"), (8, "dawn"), (24, "morning"), (40, "golden"),
        (56, "dusk"), (70, "winter"), (103, "night")]


def scene_blend(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 2.5:
            f = smooth(s1 - 2.5, s1, ts); return n0, n1, f
    return n0, n0, 0.0


# arch slots above the Keeper (F = centre keystone); notes: (seat, pitch, slot)
SLOTS = [(0.30, 0.40), (0.40, 0.365), (0.50, 0.35), (0.60, 0.365), (0.70, 0.40)]
NOTES = [dict(nm="F", m=53, seat=106.0, slot=2, refuse=True),
         dict(nm="G", m=55, seat=28.0, slot=0),
         dict(nm="A", m=57, seat=42.0, slot=1),
         dict(nm="C", m=60, seat=58.0, slot=3),
         dict(nm="D", m=62, seat=72.0, slot=4)]
GLYPHS = []
for nt in NOTES:
    if not nt.get("refuse"):
        GLYPHS.append((nt["seat"] - 5.0, "keeper")); GLYPHS.append((nt["seat"] - 3.0, nt["slot"]))

CAPS = [
    (1.5, 6.0, "the song broke into five.\nfive notes, lost in the world."),
    (6.6, 10.0, "so he walked —\nand the world turned with him."),
    (12.0, 17.0, "the first was restless."),
    (27.5, 32.5, "the second, bright and alone."),
    (43.0, 48.0, "the third, guarding another."),
    (57.0, 62.0, "the fourth, a dreamer."),
    (74.0, 80.0, "the last one was afraid."),
    (86.0, 93.0, "and you cannot\ncarry a note home."),
    (97.5, 102.0, "so he waited."),
    (103.5, 108.0, "and made a home\nworth coming to."),
    (108.6, 112.8, "and the last note\ncame on its own."),
    (113.6, 116.6, "the more you know,\nthe more you observe."),
]


def note_state(nt, ts):
    """returns (x,y in frac, bright) for a note."""
    sx, sy = SLOTS[nt["slot"]]; seat = nt["seat"]
    if nt.get("refuse"):
        if ts < 103:
            fl = 0.28 + 0.12 * math.sin(ts * 3)
            return 0.80, 0.66, fl * (1 - 0.5 * smooth(80, 96, ts) * (1 - smooth(101, 103, ts)))
        p = smooth(103.5, seat, ts)
        return lerp(0.80, sx, p), lerp(0.66, sy, p), 0.4 + 0.6 * p
    if ts < seat - 8: return None
    p = smooth(seat - 8, seat, ts)
    rx, ry = 0.86, 0.70                                  # rises over the turning right horizon
    return lerp(rx, sx, p), lerp(ry, sy, p), 0.25 + 0.75 * p


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


def draw_glyphs(im, ts, keeper_head):
    d = ImageDraw.Draw(im, "RGBA")
    for (nt, who) in GLYPHS:
        age = ts - nt
        if 0 <= age <= 1.6:
            al = np.interp(age, [0, 0.3, 1.1, 1.6], [0, 1, 1, 0])
            if who == "keeper": x, y = keeper_head[0], keeper_head[1] - 40
            else: x, y = SLOTS[who][0] * W, SLOTS[who][1] * H
            d.text((x, y - age * 30), "♪", font=GF, fill=(255, 208, 146, int(230 * al)), anchor="mm")


def story(ts):
    n0, n1, f = scene_blend(ts)
    if f <= 0.001:                                        # fast path: no cross-fade blend
        a = pl.build_sky(n0).copy(); base, mask = pl.planet_base(n0)
    else:
        a = (pl.build_sky(n0) * (1 - f) + pl.build_sky(n1) * f)
        b0, mask = pl.planet_base(n0); b1, _ = pl.planet_base(n1); base = b0 * (1 - f) + b1 * f
    a[mask] = base[mask]
    scene = n1 if f > 0.5 else n0

    theta = 0.33 * ts                                    # the world turns as he walks
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta, scene)
    a = np.asarray(im, np.float32).copy()

    # atmosphere: drifting particles of the current scene, up in the sky
    world.atmosphere(a, ts, scene)
    # winter: the cold presses in from the edges
    cold = smooth(72, 94, ts) * (1 - smooth(101, 104, ts))
    if cold > 0.01:
        darken(a, W * 0.5, -0.05 * H, 0.8 * W, 0.35 * cold)
        darken(a, 1.15 * W, 0.5 * H, 0.6 * W, 0.4 * cold)

    # the notes rising over the turning horizon, gathering into the arch
    for nt in NOTES:
        stt = note_state(nt, ts)
        if stt is None: continue
        nx, ny, nb = stt
        run = 0.0
        if ts >= 104:
            order = [0, 1, 3, 4, 2, 4, 3, 1, 0]
            phase = (ts - 107.0) * 3.0
            for oi, sl in enumerate(order):
                if sl == nt["slot"]: run = max(run, math.exp(-((phase - oi) ** 2) / 0.5))
        col = COLD if (nt.get("refuse") and ts < 104) else GOLD
        glow(a, nx * W, ny * H, 11 + 5 * run, col, nb * (0.85 + 0.15 * math.sin(ts * 3 + nt["m"])) + 0.6 * run)

    # the Keeper — walks in place on top of the turning world
    walking = not (96 <= ts <= 106)
    lean = 0.035 * math.sin(ts * 1.1) + 0.05 * smooth(80, 92, ts) * (1 - smooth(101, 104, ts))
    spr, fy, odx, ody = character(132, "walk" if walking else "stand", ts, 1, lean=lean)
    kox = CX + odx; koy = APEX_Y + ody
    glow(a, kox, koy, 24, GOLD, 0.95 * (0.92 + 0.08 * math.sin(ts * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(CX - spr.size[0] / 2), int(APEX_Y - fy)), spr)
    draw_glyphs(im, ts, (kox, APEX_Y - 0.16 * H))
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
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep5p_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep5p_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep5p_silent.mp4", "-i", MUSIC, "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep5_the_home_of_five.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep5_the_home_of_five.mp4")


if __name__ == "__main__":
    main()
