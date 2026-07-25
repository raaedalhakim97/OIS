"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 10 — "The First Song"  (Chapter I finale)
Do and Re are home. The Keeper journeys a full day and night around the little world
to find the five that remain — Mi asleep in the shade (the sweet third), shy Fa in the
golden mist (the found ones call it home), Sol blazing on the far hill (the strongest
thread — a fifth), La singing longing to the night wind (the minor seed), and restless
Ti at dawn, forever leaning toward Do (the leading tone). Then, for the first time
since the world began, the whole scale is home — and it plays the FIRST SONG, the
staff lighting note by note. And far away, in the quiet dark... something hears it.
End of Chapter I. ~2:20.
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
import flow as fl

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 134.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COOL = [150, 172, 214]
CENTER_Y = 0.52
CH, EP, TITLE, LAND = "I", "10", "The First Song", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]


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
FS = font(47); FSM = font(34); TAG = font(27)


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


def darken(a, cx, cy, rad, amount):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 2.5 * rad)); x1 = min(W, int(cx + 2.5 * rad))
    y0 = max(0, int(cy - 2.5 * rad)); y1 = min(H, int(cy + 2.5 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    g = np.exp(-((xg - cx) ** 2 + (yg - cy) ** 2) / (2 * rad ** 2))
    a[y0:y1, x0:x1] *= (1 - g * amount)[..., None]


SCENES = ["morning", "golden", "dusk", "night", "dawn"]
for s in SCENES: pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "morning"), (22, "golden"), (38, "dusk"), (56, "night"), (72, "dawn"), (86, "morning"), (101, "golden")]

# the world turns between finds, holds still for each one; after the song it rests
TURNS = [(0, 8), (21, 25), (39, 43), (55, 59), (71, 75), (128, 134)]
ROT = 0.13
def _rate(u):
    r = 0.0
    for (s, e) in TURNS:
        r = max(r, smooth(s - 1.2, s + 0.3, u) * (1 - smooth(e - 0.3, e + 1.2, u)))
    return r
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))
def walking(ts): return any(s - 0.4 < ts < e + 0.4 for (s, e) in TURNS)


# ---- the five notes still out in the world ----
# slot, appear window, source point, quirk, fly window, its own light
FINDS = [
    dict(slot=2, appear=(9.5, 11.5), src=(0.72 * W, FEET - 42), quirk="sleep",
         fly=(14.0, 15.5), col=(255, 222, 172), rad=13),
    dict(slot=3, appear=(33.0, 36.0), src=(0.28 * W, SY + 7.2 * LG), quirk="mist",
         fly=(37.0, 38.5), col=(238, 228, 210), rad=11),
    dict(slot=4, appear=(41.0, 42.5), src=(0.82 * W, FEET - 36), quirk="sun",
         fly=(47.0, 49.0), col=(255, 236, 190), rad=17),
    dict(slot=5, appear=(56.5, 58.5), src=(0.24 * W, FEET - 0.11 * H), quirk="wind",
         fly=(63.5, 65.0), col=(214, 202, 236), rad=13),
    dict(slot=6, appear=(72.5, 74.0), src=(0.70 * W, SY + 6.4 * LG), quirk="restless",
         fly=(79.0, 80.5), col=(255, 246, 226), rad=12),
]
FILLS = {2: 15.5, 3: 38.5, 4: 49.0, 5: 65.0, 6: 80.5}


def find_pos(fi, ts):
    src = fi["src"]; f0, f1 = fi["fly"]; q = fi["quirk"]
    if ts >= f1: return SLOT[fi["slot"]]
    x, y = src
    if q == "sleep":
        y += fl.bob(ts, 2.5, f1=0.4, f2=0.9)
    elif q == "mist":
        x += fl.bob(ts, 8, f1=0.35, f2=0.8, ph=1.0); y += fl.bob(ts, 5, ph=2.0)
    elif q == "sun":
        y += fl.bob(ts, 3, f1=0.5, f2=1.1, ph=0.5)
    elif q == "wind":
        x += fl.bob(ts, 16, f1=0.45, f2=1.05, ph=0.3); y += fl.bob(ts, 9, f1=0.6, f2=1.3, ph=1.6)
    elif q == "restless":
        x += fl.bob(ts, 7, ph=0.9) + 22 * max(0.0, math.sin(ts * 2.6)) ** 3   # darts toward home
        y += fl.bob(ts, 5, ph=2.4)
    if ts < f0: return (x, y)
    u = (ts - f0) / (f1 - f0)
    return fl.flight((x, y), SLOT[fi["slot"]], u, rise=0.12, settle=0.3)


def find_bright(fi, ts):
    a0, a1 = fi["appear"]
    b = smooth(a0, a1, ts)
    if fi["quirk"] == "sleep":
        b *= lerp(0.45, 1.0, smooth(12.8, 13.8, ts))     # wakes when it is found
    return b


# ---- the finale: runs and the first song ----
RUNUP = [(93.0 + 0.5 * i, i) for i in range(8)]
RUNDN = [(97.4 + 0.45 * i, 7 - i) for i in range(8)]
_seq = [(0, .72), (1, .72), (2, .72), (0, .72),
        (2, .72), (3, .72), (4, 1.44),
        (4, .72), (5, .72), (6, .72), (7, 1.44),
        (6, .72), (4, .72), (2, .72), (0, 2.4)]
SONG = []
_t = 101.5
for (sl, du) in _seq:
    SONG.append((_t, sl, du)); _t += du
SONG_END = _t


CAPS = [
    (2.0, 7.5, "two notes were home.\nfive were still out there."),
    (9.5, 15.0, "Mi was asleep in the shade,\nhumming in its sleep."),
    (16.5, 21.5, "with Do it made\nthe first sweetness: a third."),
    (25.0, 30.5, "Fa — the shy one —\nhid in the golden mist."),
    (31.5, 37.0, "so the found ones called together.\nand Fa answered."),
    (41.0, 46.5, "Sol stood on the far hill,\nshining like a small sun."),
    (49.5, 55.0, "with Do: the strongest thread.\na fifth."),
    (57.0, 62.5, "La was singing to the wind —\nthe color of longing."),
    (65.5, 70.5, "even longing\nhas a place in the song."),
    (73.0, 78.5, "Ti could not stand still —\nit leaned toward Do. always."),
    (80.8, 85.8, "one half step from home.\nthat pull is what makes music move."),
    (87.0, 92.0, "and then — for the first time\nsince the world began —"),
    (92.5, 97.5, "the whole scale was home."),
    (102.0, 106.0, "the first song."),
    (117.0, 123.0, "and far away,\nin the quiet dark —"),
    (123.5, 127.5, "something heard it."),
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
            lines = txt.split("\n")
            total = sum(int(d.textbbox((0, 0), ln, font=FS)[3] * 1.5) for ln in lines)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=FS); xx = (W - (bb[2] - bb[0])) // 2
                d.text((xx + 2, yy + 2), ln, font=FS, fill=(0, 0, 0, int(150 * fade)))
                d.text((xx, yy), ln, font=FS, fill=(238, 234, 226, int(240 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)
    if 128.5 <= ts <= 133.8:                            # the closing card
        fade = np.interp(ts, [128.5, 129.3, 133.0, 133.8], [0, 1, 1, 0])
        for i, (ln, f) in enumerate([("the more you know,", FSM), ("the more you observe.", FSM)]):
            bb = d.textbbox((0, 0), ln, font=f); xx = (W - (bb[2] - bb[0])) // 2
            yy = int(0.47 * H) + i * int(1.6 * f.size)
            d.text((xx + 2, yy + 2), ln, font=f, fill=(0, 0, 0, int(150 * fade)))
            d.text((xx, yy), ln, font=f, fill=(238, 234, 226, int(240 * fade)))
        tag = "— end of Chapter I —"
        bb = d.textbbox((0, 0), tag, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(0.545 * H)), tag, font=TAG, fill=(210, 200, 185, int(200 * fade)))


def ring(d, cx, cy, t0, ts, col, rmax=52):
    q = ts - t0
    if 0 <= q <= 0.9:
        u = q / 0.9; r = 8 + rmax * fl.ease_out(u); al = int(200 * (1 - u) ** 1.3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (al,), width=3)


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

    # the Keeper — planted at the apex, gesturing each note home
    walk = walking(ts)
    lift = 0.0
    for (i, ft) in FILLS.items():
        lift += 0.55 * smooth(ft - 2.5, ft - 0.8, ts) * (1 - smooth(ft + 1.0, ft + 2.5, ts))
    lift += 0.95 * smooth(92, 95, ts) * (1 - smooth(SONG_END + 1, SONG_END + 4, ts))   # the song
    lean = (0.03 if walk else 0.0) + fl.idle_sway(ts)
    spr, foot, odx, ody = character(140, "walk" if walk else "stand", ts, 1,
                                    lift=clamp(lift), lean=lean)
    kx = CX
    hand = (kx + odx, FEET + ody)
    glow(a, hand[0], hand[1], 22, GOLD, 0.9 * (0.9 + 0.1 * math.sin(ts * 2.6)))

    # the five notes still out there
    for fi in FINDS:
        b = find_bright(fi, ts)
        if b < 0.02 or ts >= fi["fly"][1]: continue
        x, y = find_pos(fi, ts)
        pulse = 0.82 + 0.18 * math.sin(ts * (2.5 + 0.3 * fi["slot"]) + fi["slot"])
        glow(a, x, y, fi["rad"], list(fi["col"]), b * pulse)
        glow(a, x, y, fi["rad"] * 2.6, list(fi["col"]), b * 0.15)

    # Sol's lesson: the strongest thread, Do to Sol on the staff
    thr = smooth(49.8, 51, ts) * (1 - smooth(54, 55.5, ts))
    if thr > 0.02:
        for k in range(12):
            u = k / 11.0
            glow(a, lerp(SLOT[0][0], SLOT[4][0], u), lerp(SLOT[0][1], SLOT[4][1], u), 3.5, WARM,
                 thr * 0.42 * (0.6 + 0.4 * math.sin(ts * 3 + k)))

    # the song: the world brightens while it plays
    songv = smooth(101, 105, ts) * (1 - smooth(SONG_END + 0.5, SONG_END + 3.5, ts))
    if songv > 0.02:
        a += songv * np.array([16, 12, 7], np.float32)
        for i in range(8):                              # lights rising with the song
            yy = SY + 5 * LG - ((ts * 27 + i * 43) % (10 * LG))
            xx = 0.5 * W + fl.bob(ts * 0.6 + i * 2.1, 0.18 * W, f1=0.33, f2=0.71, ph=i)
            glow(a, xx, yy, 3, WARM, songv * 0.16)

    # the hook: the far dark hears the song
    hk = smooth(116, 120, ts) * (1 - smooth(127, 130, ts))
    if hk > 0.02:
        a *= (1 - 0.16 * hk)
        rimx = 0.93 * W
        srim = math.asin((rimx - CX) / R)
        rimy = CY - R * math.cos(srim)
        darken(a, rimx, rimy, 90, hk * 0.55)
        glow(a, rimx, rimy, 5, COOL, hk * 0.25 * (0.5 + 0.5 * math.sin(ts * 1.7)))

    # the staff: Do, Re, high Do home; the rest fill as they are found; the song plays it
    vis = smooth(3, 9, ts)
    modes = ["ghost"] * 8; glows = [0.0] * 8
    for i in (0, 1, 7):
        modes[i] = "full"; glows[i] = 0.4
    for (i, ft) in FILLS.items():
        if ts >= ft:
            modes[i] = "full"
            glows[i] = max(0.4, clamp(1.0 - (ts - ft) / 1.6) * 0.6 + 0.4)
    for (t0, i) in RUNUP + RUNDN:
        if t0 <= ts <= t0 + 0.7:
            glows[i] = max(glows[i], 1.0 - (ts - t0) / 0.7)
    for (t0, i, du) in SONG:
        if t0 <= ts <= t0 + du + 0.25:
            glows[i] = max(glows[i], 1.0 - (ts - t0) / (du + 0.25))
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(FEET - foot)), spr)
    staff.draw(im, vis, modes, glows)

    d = ImageDraw.Draw(im, "RGBA")
    for fi in FINDS:                                     # a chime as each note comes home
        ft = FILLS[fi["slot"]]
        ring(d, SLOT[fi["slot"]][0], SLOT[fi["slot"]][1], ft, ts, tuple(fi["col"]), rmax=44)
    ring(d, FINDS[0]["src"][0], FINDS[0]["src"][1], 13.5, ts, (255, 222, 172), rmax=30)  # Mi wakes
    for t0 in (31.0, 31.8, 32.6):                        # the found ones call for Fa
        for i in (0, 1, 2):
            ring(d, SLOT[i][0], SLOT[i][1], t0 + i * 0.05, ts, (255, 214, 150), rmax=20)
    ring(d, FINDS[2]["src"][0], FINDS[2]["src"][1], 42.0, ts, (255, 236, 190), rmax=56)  # Sol shines
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

    # --- the day's harmonic journey ---
    w(pad([midi(48), midi(55), midi(60), midi(64)], 18, 0.045), 3, 0.5)     # C morning
    w(pad([midi(48), midi(55), midi(62), midi(67)], 15, 0.04), 22, 0.5)     # golden shimmer
    w(pad([midi(41), midi(48), midi(57), midi(60)], 16, 0.045), 38, 0.5)    # F dusk
    w(pad([midi(45), midi(52), midi(57), midi(60)], 15, 0.045), 56, 0.5)    # Am night — La's colour
    w(pad([midi(43), midi(50), midi(55), midi(62)], 13, 0.04), 72, 0.5)     # G dawn — Ti's pull
    w(pad([midi(48), midi(55), midi(60)], 6, 0.04), 86, 0.5)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 8, 0.05), 92.5, 0.5)

    for (s, e) in TURNS[:-1]:
        for t in np.arange(s + 0.6, e - 0.2, 1.4): d(softkick(0.08), t, 0.5)

    # --- Mi: asleep, waking, the first sweetness ---
    d(piano(midi(64), 2.5, 0.06), 10.5, 0.62)
    d(piano(midi(64), 2.0, 0.10), 13.5, 0.62)
    d(piano(midi(64), 3.0, 0.15), 15.5, 0.5)
    d(piano(midi(60), 2.6, 0.12), 16.6, 0.45); d(piano(midi(64), 2.6, 0.12), 16.65, 0.55)
    d(piano(midi(60), 3.0, 0.10), 19.0, 0.45); d(piano(midi(64), 3.0, 0.10), 19.05, 0.55)

    # --- Fa: the shy one; the found ones call and it answers ---
    for (m, t) in [(60, 31.0), (62, 31.8), (64, 32.6)]:
        d(piano(midi(m), 1.6, 0.09), t, 0.45)
    d(piano(midi(65), 2.2, 0.055), 33.8, 0.35)                              # a faint answer
    d(piano(midi(65), 2.2, 0.09), 35.6, 0.35)
    d(piano(midi(65), 3.0, 0.14), 38.5, 0.5)

    # --- Sol: the small sun; the strongest thread ---
    d(piano(midi(67), 3.0, 0.13), 42.0, 0.62); d(piano(midi(79), 2.0, 0.04), 42.1, 0.62)
    d(piano(midi(67), 3.0, 0.16), 49.0, 0.5)
    d(piano(midi(60), 3.0, 0.12), 50.1, 0.45); d(piano(midi(67), 3.0, 0.12), 50.15, 0.55)
    d(piano(midi(60), 3.2, 0.10), 52.6, 0.45); d(piano(midi(67), 3.2, 0.10), 52.65, 0.55)

    # --- La: longing on the night wind ---
    d(piano(midi(69), 3.2, 0.11), 57.6, 0.38)
    for (m, t) in [(69, 59.0), (67, 60.2), (69, 61.4)]:
        d(piano(midi(m), 1.8, 0.07), t, 0.40)
    d(piano(midi(69), 3.0, 0.14), 65.0, 0.5)
    for i, m in enumerate([57, 64, 69]):                                    # a soft minor bloom
        d(piano(midi(m), 2.8, 0.07), 66.2 + i * 0.12, 0.5)

    # --- Ti: the leading tone, leaning home ---
    d(piano(midi(71), 2.4, 0.11), 73.6, 0.60)
    for t in (75.3, 77.1):
        d(piano(midi(71), 1.0, 0.09), t, 0.60); d(piano(midi(72), 1.6, 0.07), t + 0.7, 0.62)
    d(piano(midi(71), 2.6, 0.14), 80.5, 0.5)
    d(piano(midi(72), 1.4, 0.05), 81.4, 0.55)

    # --- the whole scale: up, down ---
    for (t0, i) in RUNUP: d(piano(midi(PITCH[i]), 1.6, 0.10), t0, 0.42 + 0.02 * i)
    for (t0, i) in RUNDN: d(piano(midi(PITCH[i]), 1.5, 0.09), t0, 0.42 + 0.02 * i)

    # --- THE FIRST SONG ---
    bars = [(101.5, [48, 55, 60, 64]), (104.4, [41, 53, 57, 60]),
            (107.3, [45, 52, 57, 64]), (110.2, [43, 50, 55, 62]),
            (112.4, [36, 48, 55, 60, 64, 72])]
    for (t0, ch) in bars:
        w(pad([midi(m) for m in ch], 3.4 if t0 < 112 else 9.0, 0.05), t0, 0.5)
        d(softkick(0.08), t0, 0.5)
    for (t0, sl, du) in SONG:
        d(piano(midi(PITCH[sl]), du + 0.9, 0.13), t0, 0.40 + 0.025 * sl)
        if du > 1.0:
            d(piano(midi(PITCH[sl] - 12), du + 0.9, 0.05), t0, 0.5)
    w(bass(midi(36), 12, 0.06), 101.5, 0.5)

    # --- the hook: the quiet dark ---
    d(softkick(0.12), 117.5, 0.5); w(bass(midi(30), 6, 0.06), 117.5, 0.5)
    w(piano(midi(96), 3.0, 0.022), 121.0, 0.62)
    d(softkick(0.09), 124.0, 0.5); w(bass(midi(30), 5, 0.05), 124.0, 0.5)

    # --- rest ---
    w(pad([midi(48), midi(55), midi(60)], 6, 0.04), 127.5, 0.5)
    d(piano(midi(60), 4.5, 0.09), 128.8, 0.5); d(piano(midi(67), 4.5, 0.05), 128.8, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep10_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep10_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep10.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep10_silent.mp4", "-i", "ep10.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep10_the_first_song.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep10_the_first_song.mp4")


if __name__ == "__main__":
    main()
