"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 3 — "The Between-Stone"
La lies a half step below herself, in the crack BETWEEN the steps — and keepers walk
only on the seven stones. The one who can go in is the outsider the Keeper turned away
in Chapter I: the sharp. "You call it a flat. I call it a sharp. It is the same stone.
I have always lived here." The Keeper apologises, asks for help, and he and the Elder
hold the dark back with a perfect fifth while the between-stone walks into the gap and
lifts La home. Then the Hollow withdraws — singing their fifth back, perfectly.

Hidden lesson: enharmonics (♭ and ♯ are the same stone, two names) + the fifth as the
strongest thread. ~2:20.
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
LAV = [206, 190, 244]                                 # the between-stone's light
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "3", "The Between-Stone", "the Fading Edge"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]
FELL = 5                                              # La
RESCUE = 100.0


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
FS = font(46); FSM = font(33); TAG = font(29); SHF = gfont(38)


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


for s in ("winter", "fading_edge", "dawn"): pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "winter"), (96, "fading_edge"), (120, "dawn")]

TURNS = [(126, 134)]                                   # they only travel at the very end
ROT = 0.13
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

BLINKS = [(34.0, 0.28, 0.09, 0.42, 1.0),
          (71.5, 0.28, 0.09, 0.42, 1.0),
          (89.0, 0.14, 0.04, 0.22, 0.5),      # the fifth strikes
          (116.0, 0.28, 0.09, 0.42, 1.0),
          (131.0, 0.85, 0.30, 1.15, 1.0)]


def ground_y(x):
    a = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(a) + SINK

KX = 0.415 * W; KY = ground_y(KX)
EX = 0.545 * W; EY = ground_y(EX)
FIS_X = 0.755 * W; FIS_Y = ground_y(FIS_X)             # the crack between the steps
HOL_X = 0.895 * W; HOL_Y = ground_y(HOL_X)
SH_X0 = 0.215 * W                                       # the crack the sharp climbs out of

# the sharp's journey: out of its crack -> to them -> into the fissure -> home with La
SH_PATH = [(38, 42, (SH_X0, ground_y(SH_X0) + 14), (0.30 * W, ground_y(0.30 * W) - 0.075 * H), "fly"),
           (42, 90, (0.30 * W, ground_y(0.30 * W) - 0.075 * H), (0.30 * W, ground_y(0.30 * W) - 0.075 * H), "hold"),
           (90, 94, (0.30 * W, ground_y(0.30 * W) - 0.075 * H), (FIS_X, FIS_Y + 26), "fly"),
           (94, 108, (FIS_X, FIS_Y + 26), (FIS_X, FIS_Y + 26), "hold"),
           (108, 114, (FIS_X, FIS_Y + 26), (0.615 * W, ground_y(0.615 * W) - 0.09 * H), "fly")]
def sharp_pos(ts):
    x, y = fl.path(ts, SH_PATH, (0.615 * W, ground_y(0.615 * W) - 0.09 * H))
    if 42 < ts < 90 or ts > 114:
        x += fl.bob(ts, 5, f1=0.5, f2=1.15, ph=0.7); y += fl.bob(ts, 7, ph=1.9)
    return x, y

# La: down in the crack, then lifted home
def la_pos(ts):
    base = (FIS_X, FIS_Y + 34)
    if ts < RESCUE: return (base[0], base[1] + fl.bob(ts, 2.5, f1=0.3, f2=0.75))
    if ts < 108:
        return fl.flight(base, (FIS_X - 8, FIS_Y - 0.085 * H), (ts - RESCUE) / 8.0, rise=0.06, settle=0.25)
    return (FIS_X - 8, FIS_Y - 0.085 * H + fl.bob(ts, 4, ph=1.2))

CAPS = [
    (1.4, 6.0, "the note was there.\nand they could not reach it."),
    (7.0, 9.4, "i am here."),
    (11.0, 14.6, "he called La to its place —"),
    (15.4, 19.6, "but La was no longer\nstanding there."),
    (20.4, 22.6, "listen."),
    (23.2, 27.0, "it had fallen into the crack\nbetween the steps."),
    (28.0, 30.4, "i cannot."),
    (30.9, 33.6, "keepers walk only\non the seven stones."),
    (36.2, 39.6, "but someone could."),
    (41.6, 45.8, "the between-stone —\nthe one he had sent away."),
    (46.6, 49.4, "i remember you."),
    (50.6, 53.2, "i was wrong."),
    (57.8, 61.4, "you call it a flat.\ni call it a sharp."),
    (62.4, 67.6, "it is the same stone.\ni have always lived here."),
    (68.4, 70.6, "help us."),
    (71.0, 72.4, "yes."),
    (75.0, 77.2, "listen."),
    (77.8, 81.6, "the dark cannot stand\na perfect thread."),
    (85.0, 88.6, "Do and Sol.\nthe strongest thread."),
    (90.2, 93.4, "the shape drew back from it."),
    (94.6, 98.4, "and the one who lived between\nwalked in."),
    (99.4, 101.4, "rise."),
    (104.6, 107.6, "La came back to itself."),
    (109.6, 113.0, "and the scale was whole."),
    (113.8, 115.6, "thank you."),
    (121.4, 125.4, "as it went, it sang\ntheir thread back to them."),
    (125.9, 127.6, "perfectly."),
    (128.2, 130.6, "the shield would not\nwork twice."),
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
            fade = np.interp(ts, [s, s + 0.55, e - 0.55, e], [0, 1, 1, 0])
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


def ring(d, cx, cy, t0, ts, col, rmax=46, dur=0.9):
    q = ts - t0
    if 0 <= q <= dur:
        u = q / dur; r = 8 + rmax * fl.ease_out(u); al = int(200 * (1 - u) ** 1.3)
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

    hollow_gone = smooth(118, 130, ts)
    dk = (1 - 0.85 * hollow_gone)
    darken(a, HOL_X + 0.05 * W, HOL_Y, 150, 0.45 * dk)
    a *= (1 - 0.10 * dk)

    # ---- the crack between the steps ----
    for i in range(9):                                   # a dark fissure across the ground
        u = i / 8.0; fx_ = FIS_X + (u - 0.5) * 150
        darken(a, fx_, ground_y(fx_) + 20, 34, 0.55 * (1 - abs(u - 0.5) * 1.1))
    lit = smooth(56, 62, ts) * (1 - smooth(112, 118, ts))   # it lights when the sharp claims it
    if lit > 0.02:
        for i in range(9):
            u = i / 8.0; fx_ = FIS_X + (u - 0.5) * 150
            glow(a, fx_, ground_y(fx_) + 20, 5, LAV, lit * 0.14)

    # ---- the fifth: a thread between the keepers that becomes a wall ----
    fifth = smooth(80, 84, ts) * (1 - smooth(104, 110, ts))
    if fifth > 0.02:
        strain = 1.0 + 0.12 * math.sin(ts * 9)
        for i in range(18):
            u = i / 17.0
            glow(a, lerp(KX, EX, u), lerp(KY, EY, u) - 0.115 * H - 0.02 * H * math.sin(math.pi * u),
                 5, GOLD, fifth * 0.42 * strain)
        for i in range(10):                              # the wall it throws forward
            u = i / 9.0
            glow(a, lerp(EX + 30, FIS_X - 40, u), lerp(EY, FIS_Y, u) - 0.11 * H + 26 * math.sin(u * 4 + ts * 3),
                 7, GOLD, fifth * 0.20 * strain)

    # ---- the two keepers ----
    kwalk = walking(ts)
    klift = (0.6 * smooth(6.4, 7.2, ts) * (1 - smooth(9.8, 11.0, ts))          # i am here
             + 0.85 * smooth(10.4, 11.2, ts) * (1 - smooth(19, 20.4, ts))      # calling her place
             + 0.3 * smooth(27.4, 28.2, ts) * (1 - smooth(30.6, 31.8, ts))     # i cannot
             + 0.55 * smooth(49.9, 50.7, ts) * (1 - smooth(53.6, 54.8, ts))    # i was wrong
             + 0.6 * smooth(67.7, 68.5, ts) * (1 - smooth(70.8, 72.0, ts))     # help us
             + 0.95 * smooth(79.5, 81.0, ts) * (1 - smooth(106, 109, ts))      # holding the fifth
             + 0.5 * smooth(113.1, 113.9, ts) * (1 - smooth(116, 117.5, ts)))  # thank you
    kspr, kfoot, kdx, kdy = character(140, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(klift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts))
    kfl = 1.0 + (0.10 * math.sin(ts * 9) if fifth > 0.5 else 0.0)
    glow(a, KX + kdx, KY + kdy, 22, GOLD, 0.9 * kfl * (0.9 + 0.1 * math.sin(ts * 2.6)))

    elift = (0.5 * smooth(19.7, 20.5, ts) * (1 - smooth(22.8, 24.0, ts))       # listen
             + 0.5 * smooth(74.3, 75.1, ts) * (1 - smooth(77.4, 78.6, ts))     # listen (the plan)
             + 0.95 * smooth(79.5, 81.0, ts) * (1 - smooth(106, 109, ts)))     # holding the fifth
    espr, efoot, edx, edy = character(136, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(elift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts * 0.9 + 1))
    glow(a, EX + edx, EY + edy, 21, WARM, 0.86 * kfl * (0.9 + 0.1 * math.sin(ts * 2.4 + 1)))

    # ---- La ----
    lx, ly = la_pos(ts)
    warm = smooth(RESCUE, RESCUE + 3, ts)
    lcol = [lerp(COLD[i], WARM[i], warm) for i in range(3)]
    lamp = lerp(0.42 + 0.22 * abs(math.sin(ts * 0.8)), 0.95, warm)
    glow(a, lx, ly, 12 + 4 * warm, lcol, lamp)
    glow(a, lx, ly, 32, lcol, lamp * 0.20)

    # ---- the between-stone ----
    sseen = smooth(38, 41, ts)
    sx, sy = sharp_pos(ts)
    if sseen > 0.02:
        inside = smooth(93, 95, ts) * (1 - smooth(108, 110, ts))
        glow(a, sx, sy, 12, LAV, sseen * (0.9 + 0.1 * math.sin(ts * 3.4)) * (1 - 0.35 * inside))
        glow(a, sx, sy, 30, LAV, sseen * 0.17)

    # ---- the Hollow ----
    hseen = 1 - hollow_gone
    hspr = None
    if hseen > 0.03:
        hx = HOL_X + 60 * smooth(88, 96, ts) + 90 * hollow_gone      # recoils, then withdraws
        hy = ground_y(hx) + fl.bob(ts, 2.0, f1=0.3, f2=0.7)
        darken(a, hx + 0.05 * W, hy - 0.02 * H, 44, 0.8 * hseen)
        glow(a, hx + 0.05 * W, hy - 0.02 * H, 12, [70, 92, 152], 0.34 * hseen)
        darken(a, hx, hy - 0.03 * H, 88, 0.30 * hseen)
        hspr, hfoot, _, _ = character(150, "stand", 0.0, -1, lean=0.02 * math.sin(ts * 0.6))
        if hseen < 0.995:
            al = hspr.getchannel("A").point(lambda v: int(v * hseen)); hspr = hspr.copy(); hspr.putalpha(al)
        HOLD = (hx, hy, hfoot)

    # ---- the staff ----
    vis = smooth(1.0, 4.5, ts)
    modes = ["full"] * 8; glows = [0.34] * 8
    if ts < RESCUE:
        # the lesson: the same stone, two names — ♭ flickers to ♯ and back
        modes[FELL] = "raised" if (54 <= ts <= 67 and int((ts - 54) / 1.6) % 2 == 1) else "fallen"
        glows[FELL] = 0.26 + 0.30 * abs(math.sin(ts * 0.85))
    else:
        glows[FELL] = max(0.45, clamp(1 - (ts - RESCUE) / 2.0))
    if 9.0 <= ts <= 10.4: glows[FELL] = 0.1                      # he calls her place: nothing
    for (t0, i) in [(85.0, 0), (85.0, 4)]:                       # the fifth on the staff
        if fifth > 0.3:
            glows[i] = max(glows[i], 0.55 + 0.3 * abs(math.sin(ts * 3)))
    if 109.5 <= ts <= 114:                                       # the whole scale rings
        for i in range(8):
            t0 = 109.5 + i * 0.42
            if t0 <= ts <= t0 + 1.0: glows[i] = max(glows[i], 1 - (ts - t0))
    for i, t0 in [(0, 121.5), (4, 121.5)]:                       # it sings the thread back
        if t0 <= ts <= t0 + 2.2: glows[i] = max(glows[i], 0.85 * (1 - (ts - t0) / 2.2))
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(KX - kspr.size[0] / 2), int(KY - kfoot)), kspr)
    im.paste(espr, (int(EX - espr.size[0] / 2), int(EY - efoot)), espr)
    if hspr is not None:
        hx, hy, hfoot = HOLD
        im.paste(hspr, (int(hx - hspr.size[0] / 2), int(hy - hfoot)), hspr)

    staff.draw(im, vis, modes, glows)
    d = ImageDraw.Draw(im, "RGBA")
    if sseen > 0.02:                                             # its name-glyph
        d.text((sx + 30, sy - 26), "♯", font=SHF,
               fill=(216, 204, 248, int(230 * sseen)), anchor="mm")
    ring(d, SLOT[FELL][0], SLOT[FELL][1], 9.0, ts, (255, 214, 150), rmax=34)      # he calls
    ring(d, lx, ly, 11.6, ts, (170, 192, 226), rmax=30)                            # she answers below
    ring(d, SH_X0, ground_y(SH_X0) + 14, 38.0, ts, (206, 190, 244), rmax=40)
    for t0 in (54.6, 58.6, 62.6):
        ring(d, SLOT[FELL][0], SLOT[FELL][1], t0, ts, (206, 190, 244), rmax=26)
    ring(d, lx, ly, RESCUE, ts, (255, 214, 150), rmax=60, dur=1.3)
    for i in (0, 4):
        ring(d, SLOT[i][0], SLOT[i][1], 84.0, ts, (255, 214, 150), rmax=34)
        ring(d, SLOT[i][0], SLOT[i][1], 121.5, ts, (150, 176, 214), rmax=34)
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
    K = dict(register=0, pan=0.38); E = dict(register=-12, pan=0.56)
    SH = dict(register=0, pan=0.63)

    w(pad([midi(44), midi(51), midi(56), midi(59)], 34, 0.04), 1, 0.5)      # cold, unresolved
    w(bass(midi(32), 12, 0.05), 1, 0.5)

    # --- ACT I: the reach ---
    say(d, "i am here", 6.6, style="calm", **K)
    d(piano(midi(69), 3.0, 0.14), 9.0, 0.42)                                # he calls A natural
    d(piano(midi(68), 3.4, 0.10), 11.6, 0.62)                               # ...and A-flat answers
    w(piano(midi(68), 3.0, 0.05), 11.7, 0.66)
    say(d, "listen", 20.0, style="calm", **E)
    d(piano(midi(69), 1.6, 0.09), 23.4, 0.42); d(piano(midi(68), 2.4, 0.09), 24.2, 0.62)
    say(d, "i cannot", 27.6, style="calm", register=0, pan=0.40)
    for i, m in enumerate(PITCH):                                           # the seven stones pulse
        d(piano(midi(m), 1.1, 0.035), 30.9 + i * 0.22, 0.42 + 0.02 * i)
    say(d, "wait", 33.0, style="calm", **E)

    # --- ACT II: the between-stone ---
    w(pad([midi(44), midi(56), midi(63)], 30, 0.035), 37, 0.5)
    d(piano(midi(68), 3.0, 0.10), 38.2, 0.66)                               # it rises, singing itself
    d(piano(midi(80), 2.0, 0.045), 38.4, 0.68)
    say(d, "i remember you", 46.4, style="calm", **SH)
    say(d, "i was wrong", 50.2, style="calm", **K)
    # THE LESSON: the same stone, twice, two names
    d(piano(midi(68), 3.2, 0.13), 54.6, 0.60)                               # "a flat"
    d(piano(midi(68), 3.2, 0.13), 58.6, 0.66)                               # "a sharp" — same pitch
    d(piano(midi(68), 4.0, 0.11), 62.6, 0.63)
    w(pad([midi(56), midi(68)], 8, 0.035), 62.8, 0.64)
    say(d, "help us", 68.0, style="calm", **K)
    say(d, "yes", 71.0, style="confident", **SH)

    # --- ACT III: the thread and the rescue ---
    say(d, "listen", 74.6, style="calm", **E)
    for t in (80.0, 84.0, 88.0, 92.0, 96.0, 100.0, 104.0):                  # the fifth, held and held
        d(piano(midi(60), 4.6, 0.135), t, 0.36)
        d(piano(midi(67), 4.6, 0.125), t + 0.02, 0.60)
        w(pad([midi(48), midi(55)], 4.6, 0.045), t, 0.5)
    d(softkick(0.10), 84.0, 0.5); d(softkick(0.10), 88.0, 0.5)
    w(bass(midi(36), 26, 0.055), 80.0, 0.5)
    say(d, "rise", 99.4, style="confident", **SH)
    d(piano(midi(68), 1.2, 0.10), 100.0, 0.62)                              # A-flat...
    d(piano(midi(69), 5.0, 0.17), 100.9, 0.5)                               # ...becomes A. home.
    w(pad([midi(45), midi(57), midi(64), midi(69)], 10, 0.05), 101.0, 0.5)
    for i, m in enumerate(PITCH):                                           # the scale, whole
        d(piano(midi(m), 1.8, 0.115), 109.5 + i * 0.42, 0.40 + 0.025 * i)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 12, 0.05), 109.5, 0.5)
    say(d, "thank you", 113.3, style="calm", **K)

    # --- ACT IV: the cost ---
    d(softkick(0.09), 118.5, 0.62)
    d(piano(midi(60), 4.4, 0.115), 121.5, 0.64)                             # it sings their fifth
    d(piano(midi(67), 4.4, 0.105), 121.55, 0.70)                            # ...perfectly
    w(bass(midi(29), 10, 0.05), 121.5, 0.66)
    w(piano(midi(84), 3.0, 0.03), 126.0, 0.7)
    say(d, "come with me", 130.4, style="calm", **K)
    for t in np.arange(127.5, 134, 1.45): d(softkick(0.075), t, 0.5)
    w(pad([midi(45), midi(52), midi(57), midi(60)], 8, 0.04), 128.5, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep13_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep13_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep13.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep13_silent.mp4", "-i", "ep13.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep3_the_between_stone.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep3_the_between_stone.mp4")


if __name__ == "__main__":
    main()
