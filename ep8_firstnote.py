"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 8 — "The First Note"
The Keeper has only ever helped OTHER notes find their place; tonight he finds one of
his own. It rings high and bright — but where does it belong on the scale? He tests it:
not Mi, not Sol... then he sounds it against low Do and the two fuse into one. The
puzzle's answer is the OCTAVE: his note has a different voice but the same heart — high
or low, Do is Do. He sets it home, and both Do's light, joined by an octave brace. The
hidden lesson is octave equivalence: the same note, same key, a different sound. ~1:48.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
import title_card as tc
import world, planet as pl, staff

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 104.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COOL = [150, 172, 214]
CENTER_Y = 0.52
CH, EP, TITLE, LAND = "I", "8", "The First Note", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
IDX_LO, IDX_HI = 0, 7                              # the two Do's (C4 and C5)
PLACED = 69.0                                      # his note settles into high Do


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
FS = font(47); FSM = font(34); BR = gfont(26)


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


SCENES = ["night", "dawn", "morning", "golden"]
for s in SCENES: pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "night"), (14, "dawn"), (56, "morning"), (92, "golden")]

ROT = 0.13
def _rate(u):
    if u < 12: return 1.0
    if u < 18: return 1.0 - smooth(12, 18, u)
    if u < 90: return 0.0
    if u < 96: return smooth(90, 96, u)
    return 1.0
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))


# --- his note's journey across the staff as he tests where it belongs ---
def above(i):
    x, y = staff.note_xy(i); return x, y - 1.15 * LG
FEET = APEX_Y + SINK
REST = (0.615 * W, FEET - 0.03 * H)
HOVER = (0.5 * W, SY - 2.5 * LG)
SEG = [(14, 30, REST, HOVER), (30, 33, HOVER, above(2)), (33, 40, above(2), above(2)),
       (40, 42, above(2), above(4)), (42, 48, above(4), above(4)), (48, 51, above(4), above(0)),
       (51, 64, above(0), above(0)), (64, PLACED, above(0), above(7))]
def orb_pos(ts):
    if ts < 14: return REST
    for (t0, t1, p0, p1) in SEG:
        if t0 <= ts <= t1:
            u = smooth(t0, t1, ts)
            arc = 0.0 if p0 == p1 else 0.05 * H * math.sin(math.pi * u)
            return lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - arc
    return above(7)

# (time, slot, is_match): flashes as he sounds his note against a slot
TESTS = [(35.0, 2, False), (44.0, 4, False), (53.0, 0, True)]


CAPS = [
    (2.0, 8.0, "the Keeper had guided\nmany notes home."),
    (9.5, 14.5, "tonight he found\none of his own."),
    (16.5, 22.0, "it rang — high\nand bright."),
    (24.0, 30.0, "but where on the scale\ndid it belong?"),
    (33.5, 39.0, "not Mi ..."),
    (42.0, 47.5, "not Sol ..."),
    (50.0, 57.0, "then — low Do.\nthe very same note."),
    (59.0, 66.0, "a different voice —\nthe same heart."),
    (68.0, 75.0, "high or low,\nDo is Do."),
    (77.0, 85.0, "one note, two homes.\nthe song had begun."),
    (88.0, 96.0, "the more you know,\nthe more you observe."),
]


def scene_blend(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 1.8:
            return n0, n1, smooth(s1 - 1.8, s1, ts)
    return n0, n0, 0.0


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


def draw_octave_brace(im, ts):
    """A brace joining the two Do's, with an '8' — the octave."""
    v = smooth(58, 64, ts)
    if v < 0.02: return
    d = ImageDraw.Draw(im, "RGBA")
    x0, _ = staff.note_xy(IDX_LO); x1, _ = staff.note_xy(IDX_HI)
    ytop = SY - 3.1 * LG
    al = int(200 * v)
    pts = []
    for k in range(31):
        u = k / 30.0; x = lerp(x0, x1, u)
        y = ytop + 0.9 * LG * math.sin(math.pi * u)       # gentle downward brace
        pts.append((x, y))
    d.line(pts, fill=(236, 224, 200, al), width=2, joint="curve")
    d.line([(x0, ytop), (x0, ytop + 0.5 * LG)], fill=(236, 224, 200, al), width=2)
    d.line([(x1, ytop), (x1, ytop + 0.5 * LG)], fill=(236, 224, 200, al), width=2)
    cxm = (x0 + x1) / 2
    d.text((cxm, ytop - 0.2 * LG), "8", font=BR, fill=(240, 226, 202, al), anchor="mm")


def story(ts):
    n0, n1, f = scene_blend(ts)
    if f <= 0.001:
        a = pl.build_sky(n0).copy(); base, mask = pl.planet_base(n0)
    else:
        a = pl.build_sky(n0) * (1 - f) + pl.build_sky(n1) * f
        b0, mask = pl.planet_base(n0); b1, _ = pl.planet_base(n1); base = b0 * (1 - f) + b1 * f
    a[mask] = base[mask]
    scene = n1 if f > 0.5 else n0

    theta = theta_of(ts)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta, scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    # the Keeper — searches, then stands and works the puzzle with a raised hand
    walk = ts < 14 or ts > 96
    lift = smooth(18, 30, ts) * (1 - smooth(PLACED, PLACED + 5, ts))
    spr, foot, hdx, hdy = character(140, "walk" if walk else "stand", ts, 1,
                                    lift=lift, lean=0.03 * math.sin(ts * 1.1))
    kx = CX + hdx; ky = FEET + hdy
    glow(a, kx, ky - 0.11 * H, 24, GOLD, 0.92 * (0.9 + 0.1 * math.sin(ts * 3)))

    # his found note, moving across the staff as he tests it
    seen = smooth(15, 21, ts)
    placed = ts >= PLACED
    if seen > 0.02 and not placed:
        ox, oy = orb_pos(ts)
        pulse = 0.85 + 0.15 * math.sin(ts * 5)
        glow(a, ox, oy, 15, WARM, seen * pulse)
        glow(a, ox, oy, 38, WARM, seen * 0.16)

    # test flashes: cool for a mismatch, warm bloom for the octave match
    for (tt, idx, ok) in TESTS:
        dd = ts - tt
        if -0.4 <= dd <= 1.3:
            al = float(np.interp(dd, [-0.4, 0.15, 0.9, 1.3], [0, 1, 0.65, 0]))
            sx, sy = staff.note_xy(idx)
            glow(a, sx, sy, 22 if ok else 18, WARM if ok else COOL, al * (0.85 if ok else 0.5))
    # the octave fusion: a thread from low Do to high Do while he realises
    if 52 <= ts <= PLACED + 4:
        v = smooth(52, 56, ts) * (1 - smooth(PLACED + 2, PLACED + 4, ts))
        x0, y0 = staff.note_xy(IDX_LO); x1, y1 = staff.note_xy(IDX_HI)
        for k in range(16):
            u = k / 15.0
            glow(a, lerp(x0, x1, u), lerp(y0, y1, u), 4, WARM,
                 v * 0.4 * (0.6 + 0.4 * math.sin(ts * 3 + k)))

    # staff state: all ghost; low Do lights at the octave aha; high Do fills when placed
    vis = smooth(22, 30, ts)
    modes = ["ghost"] * 8; glows = [0.0] * 8
    if ts >= 52.5:
        modes[IDX_LO] = "full"
        glows[IDX_LO] = clamp(1.0 - (ts - 53) / 1.6) * 0.6 + 0.45
    if placed:
        modes[IDX_HI] = "full"
        glows[IDX_HI] = clamp(1.0 - (ts - PLACED) / 1.6) * 0.6 + 0.45
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - foot)), spr)
    staff.draw(im, vis, modes, glows)
    draw_octave_brace(im, ts)
    # a small "?" over the staff while he's deciding
    if 24 <= ts <= 50:
        qv = np.interp(ts, [24, 26, 48, 50], [0, 1, 1, 0])
        ImageDraw.Draw(im, "RGBA").text((0.5 * W, SY - 2.9 * LG), "?", font=font(int(2.2 * LG)),
                                        fill=(236, 224, 200, int(150 * qv)), anchor="mm")
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


def build_audio():
    n = int(DUR * SR)
    dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
    wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
    A = TITLE_DUR
    def d(s, at, pan=0.5): add(dL, s * (1 - pan), A + at); add(dR, s * pan, A + at)
    def w(s, at, pan=0.5): add(wL, s * (1 - pan), A + at); add(wR, s * pan, A + at)

    w(pad([midi(48), midi(55), midi(60)], SDUR - 6, 0.04), 4, 0.5)
    for t in np.arange(2, 14, 1.4): d(softkick(0.09), t, 0.5)              # searching
    d(piano(midi(72), 4.0, 0.16), 16, 0.5)                                 # his note — high, bright

    # tests: his note (72), then the slot — a mismatch each time
    d(piano(midi(72), 1.6, 0.12), 34.0, 0.5); d(piano(midi(64), 2.0, 0.13), 35.2, 0.5)   # vs Mi
    d(piano(midi(72), 1.6, 0.12), 43.0, 0.5); d(piano(midi(67), 2.0, 0.13), 44.2, 0.5)   # vs Sol
    # the octave: low Do (60) and his note (72) sounded together -> they fuse
    d(piano(midi(60), 3.6, 0.15), 52.6, 0.5); d(piano(midi(72), 3.6, 0.15), 52.6, 0.5)
    w(pad([midi(48), midi(60), midi(72)], 10, 0.05), 53, 0.5)              # octave bloom
    # placing it home + both Do's ring
    d(piano(midi(72), 5.0, 0.18), PLACED, 0.5); d(piano(midi(60), 5.0, 0.12), PLACED + 0.1, 0.5)
    w(pad([midi(48), midi(55), midi(60), midi(72)], 12, 0.055), PLACED, 0.5)
    w(bass(midi(36), 12, 0.06), PLACED, 0.5)
    for t in np.arange(91, 100, 1.4): d(softkick(0.09), t, 0.5)            # walking on
    d(piano(midi(60), 6.0, 0.14), 96, 0.5); d(piano(midi(72), 6.0, 0.10), 96, 0.5)

    dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
    wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
    mix = master(dry * 0.92 + wet)
    fi, fo = int(0.6 * SR), int(4 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep8_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep8_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep8.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep8_silent.mp4", "-i", "ep8.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep8_the_first_note.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep8_the_first_note.mp4")


if __name__ == "__main__":
    main()
