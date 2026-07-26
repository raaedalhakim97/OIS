"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 4 — "The Drum Below"
The Hollow can copy any pitch now — so pitch is useless. But it cannot keep time. The
world's heartbeat begins to stumble: something is beating BETWEEN the beats. The trio
goes down to the Drum Below and finds the Hollow standing on the heart of the world,
striking it out of time. Their strikes only land ON the beat — and the between-stone,
who lives between the steps, has to learn that the beat has no between. They drive it
off on the downbeat, together. And it walks away exactly in time: it never came to
break the drum. It came to learn the tempo.

Hidden lesson: the beat — downbeat vs off-beat, and counting one-two-three-four. ~2:20.
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
import flow as fl, eye
from observian import say

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 134.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COLD = [150, 176, 214]
LAV = [206, 190, 244]; HEART = [255, 150, 110]        # the world's heart (Ch I Ep6)
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "4", "The Drum Below", "the Drum Below"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]
BEAT = 60.0 / 72.0                                    # 72 bpm, as established in Ch I Ep6


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
FS = font(46); FSM = font(33); TAG = font(29); SHF = gfont(36)


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


for s in ("fading_edge", "night", "dawn"): pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "fading_edge"), (28, "night"), (118, "dawn")]

TURNS = [(24, 32)]                                     # the descent
ROT = 0.15
def _rate(u):
    r = 0.0
    for (s, e) in TURNS:
        r = max(r, smooth(s - 1.0, s + 0.4, u) * (1 - smooth(e - 0.4, e + 1.0, u)))
    return r
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))
def walking(ts): return any(s - 0.4 < ts < e + 0.4 for (s, e) in TURNS)

BLINKS = [(30.5, 0.26, 0.08, 0.40, 1.0),
          (49.6, 0.12, 0.03, 0.18, 0.45),    # the miss
          (64.6, 0.11, 0.03, 0.16, 0.40),    # into the volley
          (85.2, 0.11, 0.03, 0.16, 0.40),    # into double time
          (95.0, 0.09, 0.02, 0.14, 0.35),
          (103.0, 0.09, 0.02, 0.14, 0.35),
          (107.2, 0.14, 0.05, 0.22, 0.6),    # the unison hit
          (119.0, 0.28, 0.09, 0.42, 1.0),
          (132.0, 0.80, 0.28, 1.05, 1.0)]

# ---------------- the world's pulse ----------------
# a real beat grid: steady, then stumbling (dropped and late beats), then steady again
def _build_beats():
    out = []; t = 0.0; k = 0
    while t < SDUR + 4:
        strong = (k % 4 == 0)
        if 5.5 <= t <= 22.0:                           # the stumble
            if k % 7 == 3: t += BEAT; k += 1; continue  # a dropped beat
            jitter = 0.16 * math.sin(k * 1.7)           # and late arrivals
        else:
            jitter = 0.0
        out.append((t + jitter, strong))
        t += BEAT; k += 1
    return out
BEATS = _build_beats()
BEAT_T = np.array([b[0] for b in BEATS])
BEAT_S = np.array([1.0 if b[1] else 0.62 for b in BEATS])

def heart_pulse(ts):
    """0..1 — the heart's throb, from the nearest beat that has already sounded."""
    i = int(np.searchsorted(BEAT_T, ts) - 1)
    if i < 0: return 0.0
    q = ts - BEAT_T[i]
    return float(BEAT_S[i]) * math.exp(-q * 5.2) * (1 - math.exp(-q * 60))

# the Hollow's poison: strikes BETWEEN the beats
OFFS = [t + 0.42 * BEAT for (t, s) in BEATS if 12.0 <= t <= 100.0 and int(t / BEAT) % 2 == 0]
def off_pulse(ts):
    q = min([abs(ts - t) for t in OFFS if abs(ts - t) < 0.6] or [9])
    return math.exp(-q * 9) if q < 0.6 else 0.0

def beat_at(n_from, count):
    """The times of `count` beats starting at the first beat at/after n_from."""
    i = int(np.searchsorted(BEAT_T, n_from))
    return [float(BEAT_T[j]) for j in range(i, min(i + count, len(BEAT_T)))]

COUNT_IN = beat_at(50.5, 8)                            # the Elder counts
K_MISS = 45.1                                          # his first strike — off the beat
K_HIT = beat_at(58.5, 1)[0]                            # lands (on the beat)
S_MISS = 78.9                                          # the sharp's instinct: between
S_HIT = beat_at(83.0, 1)[0]
UNISON = beat_at(106.0, 1)[0]

# ---------------- THE FIGHT ----------------
# (t, who, hit) — who: k/e/s strike the drum · h strikes back at them
def _build_strikes():
    S = [(K_MISS, "k", False), (K_HIT, "k", True), (S_MISS, "s", False), (S_HIT, "s", True)]
    order = ["k", "e", "s"]
    # PHASE B — the volley: they trade blows, one per beat, it answers between
    for i, t in enumerate(beat_at(62.0, 16)):
        if t > 78.0: break
        S.append((t, order[i % 3], True))
        S.append((t + 0.5 * BEAT, "h", True))
    # PHASE C — double time: strikes on every beat AND every half beat
    for i, t in enumerate(beat_at(86.0, 24)):
        if t > 105.0: break
        S.append((t, order[i % 3], True))
        S.append((t + 0.5 * BEAT, order[(i + 2) % 3], True))
        if i % 2 == 0: S.append((t + 0.25 * BEAT, "h", True))
    S.append((UNISON, "u", True))                       # the unison finish
    return sorted(S)
STRIKES = _build_strikes()

# ---------------- staging ----------------
def ground_y(x):
    a = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(a) + SINK
KX = 0.235 * W; KY = ground_y(KX)
EX = 0.345 * W; EY = ground_y(EX)
SHX = 0.445 * W; SHY = ground_y(SHX) - 0.085 * H       # the sharp floats
# THE HEART OF THE WORLD — enormous, half-buried, filling the right of the frame
DRUM_X = 0.755 * W; DRUM_R = 0.315 * W
DRUM_Y = ground_y(DRUM_X) + DRUM_R * 0.34            # mostly above ground: a huge dome
DRUM_TOP = DRUM_Y - DRUM_R
HOL_X = DRUM_X - 0.045 * W                             # it stands ON the heart
HOL_Y = DRUM_TOP + 26

CAPS = [
    (1.4, 5.0, "the world had a heartbeat."),
    (5.8, 8.8, "and it began to stumble."),
    (9.4, 11.6, "do you hear it?"),
    (12.0, 13.8, "listen."),
    (14.4, 18.0, "something was beating\nbetween the beats."),
    (18.6, 21.8, "and the heart\nwas trying to follow."),
    (22.4, 24.4, "come with me."),
    (25.2, 28.6, "down to the drum below."),
    (33.4, 37.2, "it stood on the heart\nof the world."),
    (38.0, 41.6, "striking it out of time."),
    (43.4, 45.0, "danger!"),
    (46.6, 49.4, "he struck.\nand missed."),
    (49.9, 51.2, "no."),
    (51.6, 54.4, "not there.\nthere."),
    (54.8, 57.6, "count.\none — two — three — four."),
    (58.4, 60.0, "now."),
    (60.6, 63.4, "on the beat,\nthe light lands."),
    (66.0, 67.6, "again."),
    (71.0, 72.6, "again!"),
    (75.4, 78.2, "it struck back\nbetween the beats."),
    (79.4, 82.4, "the beat\nhas no between."),
    (82.9, 84.2, "i cannot."),
    (84.6, 86.2, "listen."),
    (86.8, 89.4, "so it learned to count."),
    (91.0, 92.6, "faster."),
    (96.0, 97.6, "again!"),
    (100.6, 102.2, "faster!"),
    (104.4, 105.9, "together."),
    (106.6, 110.0, "and on the one,\nthey struck as one."),
    (112.0, 115.2, "the heart came back\nto time."),
    (117.0, 118.8, "thank you."),
    (121.6, 124.8, "as it went,\nit walked away in time."),
    (125.2, 127.6, "it had not come\nto break the drum."),
    (128.0, 131.0, "it had come\nto learn the tempo."),
]


def scene_blend(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 2.0:
            return n0, n1, smooth(s1 - 2.0, s1, ts)
    return n0, n0, 0.0


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.5, e - 0.5, e], [0, 1, 1, 0])
            lines = txt.split("\n")
            total = sum(int(d.textbbox((0, 0), ln, font=FS)[3] * 1.5) for ln in lines)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=FS); xx = (W - (bb[2] - bb[0])) // 2
                d.text((xx + 2, yy + 2), ln, font=FS, fill=(0, 0, 0, int(150 * fade)))
                d.text((xx, yy), ln, font=FS, fill=(238, 234, 226, int(240 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)


def end_card(im, ts):
    if ts < 131.6: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [131.6, 132.4, 133.2, 134.0], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.455), ("the more you observe.", 0.492)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "to be continued"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.552 * H)), tg, font=TAG, fill=(202, 194, 182, int(190 * fade)))


def draw_pips(im, ts):
    """Four beat-pips above the staff — the count made visible."""
    v = smooth(58.0, 61.0, ts) * (1 - smooth(104, 108, ts))
    if v < 0.02: return
    d = ImageDraw.Draw(im, "RGBA")
    i = int(np.searchsorted(BEAT_T, ts) - 1)
    cur = (i % 4) if i >= 0 else -1
    q = ts - (BEAT_T[i] if i >= 0 else 0)
    y = SY - 3.6 * LG
    for k in range(4):
        x = CX + (k - 1.5) * 2.3 * LG
        rr = (0.52 if k == 0 else 0.36) * LG
        on = (k == cur) * math.exp(-q * 6.0)
        col = (255, 226, 178, int((60 + 190 * on) * v))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
        if k == 0:
            d.ellipse([x - rr * 1.9, y - rr * 1.9, x + rr * 1.9, y + rr * 1.9],
                      outline=(255, 226, 178, int((70 + 120 * on) * v)), width=2)


def bolt(a, x0, y0, x1, y1, prog, hit, col):
    """A strike: travels from a lantern toward the drum. If it misses it greys and dies."""
    reach = prog if hit else min(prog, 0.55)
    n = 14
    for i in range(n):
        u = (i / (n - 1)) * reach
        fade = 1.0 if hit else (1.0 - u / 0.55) ** 1.4
        c = col if hit else [110, 118, 132]
        glow(a, lerp(x0, x1, u), lerp(y0, y1, u) - 0.05 * H * math.sin(math.pi * u),
             6 if hit else 5, c, (0.42 if hit else 0.20) * fade)


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

    hp = heart_pulse(ts)
    op = off_pulse(ts) * (1 - smooth(99, 103, ts))
    depth = smooth(26, 34, ts)                          # they go down: the world closes in
    a *= (1 - 0.20 * depth)
    a += (hp * (10 + 26 * depth)) * np.array([1.0, 0.55, 0.42], np.float32)   # the whole world throbs
    a -= (op * 9) * np.array([1.0, 1.0, 1.0], np.float32)                      # the wrong beat sucks light

    # ---- THE DRUM: the heart of the world — an enormous half-buried dome ----
    dseen = smooth(28, 34, ts)
    hurt = smooth(36, 60, ts) * (1 - smooth(100, 112, ts))     # it is being struck out of time
    if dseen > 0.02:
        rr = DRUM_R * (1.0 + 0.06 * hp)
        amt = dseen * (0.55 + 0.45 * hp) * (1 - 0.30 * hurt)
        x0 = max(0, int(DRUM_X - rr * 1.6)); x1 = min(W, int(DRUM_X + rr * 1.6))
        y0 = max(0, int(DRUM_Y - rr * 1.6)); y1 = min(H, int(DRUM_Y + rr * 1.6))
        yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dist = np.sqrt((xg - DRUM_X) ** 2 + (yg - DRUM_Y) ** 2) / rr
        body = np.clip(1.0 - dist, 0, 1) ** 0.75                 # the solid mass
        rim = np.exp(-((dist - 1.0) ** 2) / 0.010) * (0.45 + 0.55 * hp)   # a bright edge
        halo = np.exp(-((dist - 1.0) ** 2) / 0.28) * 0.32
        inten = (body * (0.55 + 0.75 * hp) + rim + halo) * amt
        a[y0:y1, x0:x1] += inten[..., None] * np.array(HEART, np.float32)
        for k in range(11):                                      # veins of light on the dome
            ang = -1.25 + k * 0.25
            glow(a, DRUM_X + rr * 0.78 * math.sin(ang), DRUM_Y - rr * 0.78 * math.cos(ang),
                 22, [255, 205, 170], dseen * (0.06 + 0.24 * hp))
        if op > 0.05:
            darken(a, DRUM_X, DRUM_TOP + 60, 190, 0.42 * op * dseen)

    # ---- the trio ----
    kwalk = walking(ts)
    klift = (0.55 * smooth(8.8, 9.6, ts) * (1 - smooth(11.8, 13.0, ts))
             + 0.9 * smooth(K_MISS - 1.0, K_MISS, ts) * (1 - smooth(K_MISS + 1.8, K_MISS + 2.8, ts))
             + 0.95 * smooth(57.5, 58.5, ts) * (1 - smooth(78.5, 80, ts))     # fighting
             + 0.95 * smooth(85.5, 86.5, ts) * (1 - smooth(UNISON + 2, UNISON + 4, ts))
             + 0.5 * smooth(116.4, 117.2, ts) * (1 - smooth(119.5, 121, ts)))
    kspr, kfoot, kdx, kdy = character(140, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(klift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts))
    khx, khy = KX + kdx, KY + kdy
    glow(a, khx, khy, 22, GOLD, 0.88 * (0.86 + 0.14 * hp))

    elift = (0.5 * smooth(11.4, 12.2, ts) * (1 - smooth(14.2, 15.4, ts))
             + 0.55 * smooth(21.8, 22.6, ts) * (1 - smooth(25, 26.4, ts))
             + 0.85 * smooth(50.0, 51.0, ts) * (1 - smooth(58, 59.5, ts))     # counting
             + 0.95 * smooth(61.5, 62.5, ts) * (1 - smooth(78.5, 80, ts))     # fighting
             + 0.6 * smooth(84.0, 84.8, ts) * (1 - smooth(87, 88.4, ts))      # counting for the sharp
             + 0.95 * smooth(85.5, 86.5, ts) * (1 - smooth(UNISON + 2, UNISON + 4, ts)))
    espr, efoot, edx, edy = character(136, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(elift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts * 0.9 + 1))
    ehx, ehy = EX + edx, EY + edy
    glow(a, ehx, ehy, 21, WARM, 0.84 * (0.86 + 0.14 * hp))

    shx = SHX + fl.bob(ts, 6, f1=0.5, f2=1.15, ph=0.7)
    shy = SHY + fl.bob(ts, 8, ph=1.9)
    glow(a, shx, shy, 12, LAV, 0.9 * (0.88 + 0.12 * hp))
    glow(a, shx, shy, 30, LAV, 0.16)

    # ---- THE FIGHT: bolts flying both ways ----
    SRC = {"k": (khx, khy, GOLD), "e": (ehx, ehy, WARM), "s": (shx, shy, LAV)}
    TGT = (HOL_X, HOL_Y - 0.035 * H)
    shake = 0.0
    for (t0, who, hit) in STRIKES:
        q = ts - t0
        if not (-0.05 <= q <= 0.75): continue
        p = fl.ease_out(clamp(q / 0.55))
        if who == "h":                                          # it strikes back, off the beat
            for (x1, y1, _c) in SRC.values():
                n = 9
                for i in range(n):
                    u = (i / (n - 1)) * p
                    darken(a, lerp(TGT[0], x1, u), lerp(TGT[1], y1, u) - 0.03 * H * math.sin(math.pi * u),
                           16, 0.42 * (1 - u * 0.4))
            if q > 0.5: shake = max(shake, 3.0 * (1 - (q - 0.5) / 0.25))
        elif who == "u":                                        # the unison
            for (x0, y0, col) in SRC.values():
                bolt(a, x0, y0, TGT[0], TGT[1], p, True, col)
            glow(a, TGT[0], TGT[1], 60 + 150 * p, GOLD, 0.55 * (1 - p))
            shake = max(shake, 13.0 * (1 - p))
        else:
            x0, y0, col = SRC[who]
            bolt(a, x0, y0, TGT[0], TGT[1], p, hit, col)
            if hit and q > 0.45:
                f2 = 1 - (q - 0.45) / 0.30
                glow(a, TGT[0], TGT[1], 26 + 40 * (1 - f2), col, 0.55 * max(0.0, f2))
                shake = max(shake, 5.0 * max(0.0, f2))

    # ---- the Hollow, standing on the heart ----
    gone = smooth(UNISON + 0.4, 118, ts)
    hseen = smooth(31, 35, ts) * (1 - 0.9 * smooth(118, 130, ts))
    hspr = None
    if hseen > 0.03:
        recoil = 0.0                                            # every landed hit knocks it back
        for (t0, who, hit) in STRIKES:
            if who in ("h",) or not hit: continue
            q = ts - t0
            if 0.45 <= q <= 2.2:
                recoil += (24 if who != "u" else 90) * math.exp(-(q - 0.45) * 2.4)
        hx = HOL_X + min(recoil, 120) + 190 * gone
        hy = (HOL_Y if gone < 0.02 else lerp(HOL_Y, ground_y(hx), gone)) + fl.bob(ts, 2.0, f1=0.3, f2=0.7)
        darken(a, hx + 0.05 * W, hy - 0.02 * H, 44, 0.8 * hseen)
        glow(a, hx + 0.05 * W, hy - 0.02 * H, 12, [70, 92, 152], 0.32 * hseen)
        darken(a, hx, hy - 0.03 * H, 86, 0.30 * hseen)
        hspr, hfoot, _, _ = character(150, "stand", 0.0, -1, lean=0.02 * math.sin(ts * 0.6))
        if hseen < 0.995:
            al = hspr.getchannel("A").point(lambda v: int(v * hseen)); hspr = hspr.copy(); hspr.putalpha(al)
        HOLD = (hx, hy, hfoot)

    # ---- the staff: whole and warm, breathing with the heart ----
    vis = smooth(1.0, 4.5, ts)
    modes = ["full"] * 8
    glows = [0.28 + 0.22 * hp for _ in range(8)]
    if op > 0.1:
        for i in range(8): glows[i] *= 1 - 0.45 * op
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(KX - kspr.size[0] / 2), int(KY - kfoot)), kspr)
    im.paste(espr, (int(EX - espr.size[0] / 2), int(EY - efoot)), espr)
    if hspr is not None:
        hx, hy, hfoot = HOLD
        im.paste(hspr, (int(hx - hspr.size[0] / 2), int(hy - hfoot)), hspr)

    staff.draw(im, vis, modes, glows)
    draw_pips(im, ts)
    d = ImageDraw.Draw(im, "RGBA")
    d.text((shx + 28, shy - 24), "♯", font=SHF, fill=(216, 204, 248, 225), anchor="mm")
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.40)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    if shake > 0.4:                                             # impact shake
        dx = int(shake * math.sin(ts * 71)); dy = int(shake * 0.7 * math.sin(ts * 53 + 1))
        frame = np.roll(np.roll(frame, dy, axis=0), dx, axis=1)
    eye.apply_lids(frame, eye.blink_amount(ts, BLINKS))
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
    K = dict(register=0, pan=0.36); E = dict(register=-12, pan=0.5); SH = dict(register=0, pan=0.64)

    w(pad([midi(45), midi(52), midi(57), midi(60)], 30, 0.038), 1, 0.5)
    w(pad([midi(43), midi(50), midi(55), midi(58)], 40, 0.036), 30, 0.5)
    w(pad([midi(36), midi(48), midi(55), midi(60)], 22, 0.045), 100, 0.5)     # the heart, restored

    # THE HEARTBEAT — every beat of the grid, stumble and all
    for (t, strong) in BEATS:
        if t > SDUR: break
        amp = 0.115 if strong else 0.075
        if 5.5 <= t <= 22.0: amp *= 0.85                                       # weak while stumbling
        if t > 100: amp *= 1.25                                                # strong again
        d(softkick(amp), t, 0.5)
    # the Hollow's poison: dull thuds BETWEEN the beats
    for t in OFFS:
        w(bass(midi(29), 0.5, 0.05), t, 0.62)
        d(softkick(0.055), t, 0.62)

    say(d, "do you hear it", 9.4, style="calm", **K)
    say(d, "listen", 12.0, style="calm", **E)
    say(d, "come with me", 22.4, style="calm", **E)
    for t in np.arange(24.5, 30.5, 1.45): d(softkick(0.06), t, 0.42)           # the descent
    w(bass(midi(31), 12, 0.05), 25, 0.5)

    # the drum revealed — huge
    d(piano(midi(36), 6.0, 0.09), 31.5, 0.5); w(bass(midi(36), 16, 0.06), 31.5, 0.5)

    say(d, "danger", 43.4, style="fear", register=12, pan=0.36)
    say(d, "no", 49.9, style="calm", **E)
    say(d, "wait", 51.6, style="calm", **E)
    for i, t in enumerate(COUNT_IN):                                           # the count
        d(piano(midi(60 if i % 4 == 0 else 55), 1.2, 0.10 if i % 4 == 0 else 0.06), t, 0.5)
    say(d, "now", 58.4, style="urgent", **K)

    # ---- THE FIGHT: a sound for every strike ----
    VOICE = {"k": (72, 0.36), "e": (67, 0.5), "s": (68, 0.64)}
    for (t0, who, hit) in STRIKES:
        if t0 > SDUR: continue
        if who == "h":                                                         # it strikes back
            d(softkick(0.085), t0, 0.66); w(bass(midi(29), 0.8, 0.045), t0, 0.68)
            d(piano(midi(42), 1.0, 0.045), t0, 0.66)
        elif who == "u":                                                       # the unison
            for m, pan in [(60, 0.36), (67, 0.5), (72, 0.64)]:
                d(piano(midi(m), 5.0, 0.155), t0, pan)
            d(softkick(0.18), t0, 0.5)
            w(pad([midi(36), midi(48), midi(55), midi(60), midi(67)], 12, 0.055), t0, 0.5)
        else:
            m, pan = VOICE[who]
            if hit:
                d(piano(midi(m), 1.9, 0.125), t0, pan)
                d(softkick(0.10), t0, 0.5)
            else:
                d(piano(midi(m), 0.9, 0.085), t0, pan)                         # a miss: short, dead
                w(piano(midi(m - 12), 1.4, 0.025), t0 + 0.2, pan)
    # the fight's driving pulse — the world beating harder as it goes
    for t in [b for b in BEAT_T if 62.0 <= b <= 106.0]:
        d(softkick(0.055 if t < 86 else 0.075), float(t), 0.5)
    w(bass(midi(36), 20, 0.05), 62.0, 0.5); w(bass(midi(36), 22, 0.055), 86.0, 0.5)
    w(pad([midi(45), midi(52), midi(57)], 22, 0.035), 62.0, 0.5)
    w(pad([midi(43), midi(50), midi(55), midi(59)], 20, 0.04), 86.0, 0.5)

    say(d, "i cannot", 82.9, style="calm", **SH)
    say(d, "listen", 84.6, style="calm", **E)
    say(d, "together", 104.4, style="confident", **K)
    say(d, "thank you", 116.9, style="calm", **K)

    # the cost: it walks away exactly in time
    for t in [b for b in BEAT_T if 121.0 <= b <= 131.0][::2]:
        d(softkick(0.075), float(t), 0.66)
    w(bass(midi(29), 12, 0.05), 121.0, 0.66)
    w(piano(midi(84), 3.0, 0.028), 128.5, 0.68)
    for i, m in enumerate([60, 64, 67]):
        d(piano(midi(m), 5.0, 0.07), 131.5 + i * 0.2, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep14_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep14_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep14.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep14_silent.mp4", "-i", "ep14.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep4_the_drum_below.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep4_the_drum_below.mp4")


if __name__ == "__main__":
    main()
