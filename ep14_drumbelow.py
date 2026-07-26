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

BLINKS = [(32.5, 0.28, 0.09, 0.42, 1.0),
          (64.5, 0.26, 0.08, 0.40, 1.0),
          (100.4, 0.13, 0.04, 0.20, 0.5),    # the unison hit
          (105.5, 0.28, 0.09, 0.42, 1.0),
          (131.0, 0.85, 0.30, 1.15, 1.0)]

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

COUNT_IN = beat_at(66.0, 8)                            # the Elder counts
K_HIT = beat_at(70.5, 1)[0]                            # lands (on the beat)
K_MISS = 48.6                                          # his first strike — off the beat
S_MISS = 78.4                                          # the sharp's instinct: between
S_HIT = beat_at(91.5, 1)[0]
UNISON = beat_at(98.6, 1)[0]

# ---------------- staging ----------------
def ground_y(x):
    a = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(a) + SINK
KX = 0.365 * W; KY = ground_y(KX)
EX = 0.485 * W; EY = ground_y(EX)
SHX = 0.585 * W; SHY = ground_y(SHX) - 0.075 * H       # the sharp floats
DRUM_X = 0.80 * W; DRUM_Y = ground_y(DRUM_X) + 26      # the heart, in the ground
HOL_X = 0.80 * W; HOL_Y = ground_y(HOL_X) - 18         # standing on it

CAPS = [
    (1.4, 5.0, "the world had a heartbeat."),
    (5.8, 9.0, "and it began to stumble."),
    (9.6, 12.0, "do you hear it?"),
    (12.4, 14.2, "listen."),
    (14.8, 18.6, "something was beating\nbetween the beats."),
    (19.2, 22.8, "and the heart\nwas trying to follow."),
    (23.4, 25.6, "come with me."),
    (26.4, 30.0, "down to the drum below."),
    (37.4, 41.4, "it stood on the heart\nof the world."),
    (42.2, 46.0, "striking it out of time."),
    (47.6, 49.6, "danger!"),
    (51.4, 54.6, "he struck.\nand missed."),
    (55.6, 57.4, "no."),
    (58.2, 62.0, "not there.\nthere."),
    (62.6, 65.4, "count.\none — two — three — four."),
    (69.8, 71.6, "now."),
    (73.4, 77.0, "on the beat,\nthe light lands."),
    (80.4, 84.0, "the between-stone lived\nbetween the steps —"),
    (84.6, 88.0, "but the beat\nhas no between."),
    (88.6, 90.6, "i cannot."),
    (91.0, 94.4, "so it learned to count."),
    (95.4, 97.4, "together."),
    (98.0, 101.6, "and on the one,\nthey struck together."),
    (103.2, 106.4, "the heart came back\nto time."),
    (108.4, 110.4, "thank you."),
    (116.6, 120.4, "as it went,\nit walked away in time."),
    (121.2, 124.0, "it had not come\nto break the drum."),
    (124.6, 128.2, "it had come\nto learn the tempo."),
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

    # ---- the drum: the heart of the world ----
    dseen = smooth(30, 36, ts)
    if dseen > 0.02:
        rad = 52 + 26 * hp
        glow(a, DRUM_X, DRUM_Y, rad, HEART, dseen * (0.30 + 0.55 * hp))
        glow(a, DRUM_X, DRUM_Y, rad * 2.4, HEART, dseen * (0.06 + 0.14 * hp))
        if op > 0.05:
            darken(a, DRUM_X, DRUM_Y, 70, 0.40 * op * dseen)

    # ---- the trio ----
    kwalk = walking(ts)
    klift = (0.55 * smooth(9.0, 9.8, ts) * (1 - smooth(12.2, 13.4, ts))
             + 0.9 * smooth(K_MISS - 1.0, K_MISS, ts) * (1 - smooth(K_MISS + 2.4, K_MISS + 3.6, ts))
             + 0.95 * smooth(K_HIT - 1.2, K_HIT, ts) * (1 - smooth(K_HIT + 2.6, K_HIT + 4.0, ts))
             + 0.95 * smooth(UNISON - 1.4, UNISON, ts) * (1 - smooth(UNISON + 2.4, UNISON + 4.0, ts))
             + 0.5 * smooth(107.8, 108.6, ts) * (1 - smooth(111, 112.4, ts)))
    kspr, kfoot, kdx, kdy = character(140, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(klift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts))
    khx, khy = KX + kdx, KY + kdy
    glow(a, khx, khy, 22, GOLD, 0.88 * (0.86 + 0.14 * hp))

    elift = (0.5 * smooth(11.8, 12.6, ts) * (1 - smooth(14.6, 15.8, ts))
             + 0.55 * smooth(22.8, 23.6, ts) * (1 - smooth(26, 27.4, ts))
             + 0.85 * smooth(57.6, 58.6, ts) * (1 - smooth(66, 67.6, ts))     # counting
             + 0.6 * smooth(87.8, 88.6, ts) * (1 - smooth(92, 93.4, ts))      # counting for the sharp
             + 0.95 * smooth(UNISON - 1.4, UNISON, ts) * (1 - smooth(UNISON + 2.4, UNISON + 4.0, ts)))
    espr, efoot, edx, edy = character(136, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(elift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts * 0.9 + 1))
    ehx, ehy = EX + edx, EY + edy
    glow(a, ehx, ehy, 21, WARM, 0.84 * (0.86 + 0.14 * hp))

    shx = SHX + fl.bob(ts, 6, f1=0.5, f2=1.15, ph=0.7)
    shy = SHY + fl.bob(ts, 8, ph=1.9)
    glow(a, shx, shy, 12, LAV, 0.9 * (0.88 + 0.12 * hp))
    glow(a, shx, shy, 30, LAV, 0.16)

    # ---- the strikes ----
    for (t0, x0, y0, hit, col) in [(K_MISS, khx, khy, False, GOLD),
                                   (K_HIT, khx, khy, True, GOLD),
                                   (S_MISS, shx, shy, False, LAV),
                                   (S_HIT, shx, shy, True, LAV)]:
        q = ts - t0
        if 0 <= q <= 0.85:
            bolt(a, x0, y0, DRUM_X, DRUM_Y - 30, fl.ease_out(q / 0.85), hit, col)
    q = ts - UNISON                                     # the unison: all three at once
    if 0 <= q <= 1.0:
        p = fl.ease_out(q / 1.0)
        for (x0, y0, col) in [(khx, khy, GOLD), (ehx, ehy, WARM), (shx, shy, LAV)]:
            bolt(a, x0, y0, DRUM_X, DRUM_Y - 30, p, True, col)
        glow(a, DRUM_X, DRUM_Y - 20, 40 + 60 * p, GOLD, 0.5 * (1 - p))

    # ---- the Hollow, standing on the heart ----
    gone = smooth(100.4, 112, ts)
    hseen = smooth(33, 37, ts) * (1 - 0.9 * smooth(112, 128, ts))
    hspr = None
    if hseen > 0.03:
        recoil = 26 * (smooth(K_HIT, K_HIT + 0.3, ts) * (1 - smooth(K_HIT + 1.6, K_HIT + 2.6, ts))
                       + smooth(S_HIT, S_HIT + 0.3, ts) * (1 - smooth(S_HIT + 1.6, S_HIT + 2.6, ts)))
        hx = HOL_X + recoil + 150 * gone
        hy = ground_y(hx) - 18 * (1 - gone) + fl.bob(ts, 2.0, f1=0.3, f2=0.7)
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

    say(d, "do you hear it", 9.6, style="calm", **K)
    say(d, "listen", 12.4, style="calm", **E)
    say(d, "come with me", 23.4, style="calm", **E)
    for t in np.arange(25.5, 32, 1.45): d(softkick(0.06), t, 0.42)             # the descent
    w(bass(midi(31), 12, 0.05), 26, 0.5)

    # the drum revealed
    d(piano(midi(48), 5.0, 0.08), 34.0, 0.5); w(bass(midi(36), 14, 0.05), 34.0, 0.5)

    # his first strike — off the beat, and it misses
    say(d, "danger", 47.6, style="fear", register=12, pan=0.36)
    d(piano(midi(72), 1.0, 0.10), K_MISS, 0.40)
    w(piano(midi(60), 1.6, 0.03), K_MISS + 0.2, 0.5)                           # it fizzles
    say(d, "no", 55.6, style="calm", **E)
    say(d, "wait", 57.6, style="calm", **E)
    # the count: four even Do's, exactly on the pulse
    for i, t in enumerate(COUNT_IN):
        d(piano(midi(60 if i % 4 == 0 else 55), 1.2, 0.10 if i % 4 == 0 else 0.06), t, 0.5)

    # on the beat, the light lands
    say(d, "now", 69.8, style="urgent", **K)
    d(piano(midi(72), 2.6, 0.15), K_HIT, 0.40)
    d(softkick(0.13), K_HIT, 0.5); w(pad([midi(48), midi(60)], 3, 0.04), K_HIT, 0.5)

    # the sharp's instinct is between — it misses
    d(piano(midi(68), 1.0, 0.10), S_MISS, 0.64)
    w(piano(midi(56), 1.6, 0.03), S_MISS + 0.2, 0.64)
    say(d, "i cannot", 88.6, style="calm", **SH)
    say(d, "listen", 90.0, style="calm", **E)
    for i, t in enumerate(beat_at(90.8, 4)):                                   # it counts
        d(piano(midi(60), 1.0, 0.075), t, 0.5)
    d(piano(midi(68), 2.6, 0.14), S_HIT, 0.64)                                 # and lands
    d(softkick(0.12), S_HIT, 0.5)

    # together, on the one
    say(d, "together", 95.4, style="confident", **K)
    for m, pan in [(60, 0.36), (67, 0.5), (68, 0.64)]:
        d(piano(midi(m), 4.6, 0.15), UNISON, pan)
    d(softkick(0.16), UNISON, 0.5)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(67)], 10, 0.05), UNISON, 0.5)
    say(d, "thank you", 108.4, style="calm", **K)

    # the cost: it walks away exactly in time
    for t in [b for b in BEAT_T if 113.0 <= b <= 127.0][::2]:
        d(softkick(0.075), float(t), 0.66)
    w(bass(midi(29), 12, 0.05), 113.0, 0.66)
    w(piano(midi(84), 3.0, 0.028), 124.5, 0.68)
    for i, m in enumerate([60, 64, 67]):
        d(piano(midi(m), 5.0, 0.07), 129.0 + i * 0.2, 0.5)

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
