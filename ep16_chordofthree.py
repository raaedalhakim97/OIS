"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 6 — "The Chord of Three"
The Sunderer arrives — walking, in time, and he sings their First Song back perfectly.
One note is swallowed. The fifth snaps, because he learned it. So they sound three at
once: a chord. And it holds, because a chord is not a sound — it is what happens
between more than one, and he is alone. So he does not break the chord. He breaks the
three: he takes the Elder, who has no note left to defend himself.

Hidden lesson: the triad — one note is a pitch, two an interval, three a chord. ~2:24.
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
SDUR = 164.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COLD = [150, 176, 214]
LAV = [206, 190, 244]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "6", "The Chord of Three", "the Long Dark"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]
BEAT = 60.0 / 72.0


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
FS = font(46); FSM = font(33); TAG = font(29); SHF = gfont(34)


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


for s in ("night", "fading_edge"): pl.build_sky(s); pl.planet_base(s)
def theta_of(ts): return 0.04 * ts

BLINKS = [(38.6, 0.24, 0.08, 0.38, 1.0),
          (48.0, 0.11, 0.03, 0.17, 0.42),
          (61.2, 0.10, 0.03, 0.16, 0.40),     # into the volley
          (72.8, 0.08, 0.02, 0.13, 0.32),
          (86.6, 0.08, 0.02, 0.13, 0.32),
          (99.0, 0.22, 0.07, 0.34, 0.95),     # into the chord
          (131.0, 0.24, 0.08, 0.38, 1.0),
          (145.6, 0.16, 0.06, 0.30, 0.75),    # the Elder goes out
          (159.0, 0.85, 0.30, 1.10, 1.0)]

BEATS = [i * BEAT for i in range(int(SDUR / BEAT) + 2)]
def beat_at(t0, n=1):
    return [b for b in BEATS if b >= t0][:n]
def heart_pulse(ts):
    i = int(ts / BEAT)
    q = ts - i * BEAT
    return math.exp(-q * 5.0) * (1 - math.exp(-q * 60))


def ground_y(x):
    a = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(a) + SINK

# they begin exactly where Ep5 left them — and give ground as he comes on
def kx_at(ts): return lerp(0.375 * W, 0.255 * W, smooth(4, 18, ts))
def ex_at(ts): return lerp(0.545 * W, 0.395 * W, smooth(4, 18, ts))
def shx_at(ts): return lerp(0.665 * W, 0.525 * W, smooth(4, 18, ts))
SUN_X0, SUN_X1 = 0.98 * W, 0.79 * W                  # he was already at the rim in Ep5

# --- the fight ---
ONE = beat_at(40.0, 1)[0]                            # a single note: swallowed
FIFTH0, FIFTH1 = 50.0, 57.0                          # the fifth he already knows: snapped

# THE POWER CHORDS — root and fifth, no third between them. a spear, not a shield.
# Each pair works the first time and fails the second: he learns them one by one,
# so they have to keep changing weapons.
VOL_T0, VOL_STEP = 62.0, 2.35
_PAIRS = [("Fa · Do", [3, 7], 1), ("Sol · Re", [4, 1], 1), ("La · Mi", [5, 2], 1),
          ("Fa · Do", [3, 7], 0), ("Re · La", [1, 5], 1), ("Mi · Ti", [2, 6], 1),
          ("Sol · Re", [4, 1], 0), ("Ti · Fa", [6, 3], 1), ("La · Mi", [5, 2], 0),
          ("Re · La", [1, 5], 0), ("Mi · Ti", [2, 6], 0), ("Ti · Fa", [6, 3], 0)]
POWER = [(VOL_T0 + i * VOL_STEP, nm, dg, hit) for i, (nm, dg, hit) in enumerate(_PAIRS)]
VOL_END = POWER[-1][0] + 2.0

CHORD0 = 100.0                                        # three voices: the chord
CHORD_HITS = [b for b in BEATS if 108 <= b <= 128][::2]   # he strikes it, and it holds
TAKE = 138.0                                          # he takes the Elder
OUT = 145.0                                           # the Elder's light goes out
HIS_SONG = [(21.5 + i * 1.25, i) for i in range(6)]   # he sings the First Song, perfectly


def power_at(ts):
    for (t0, nm, dg, hit) in POWER:
        if t0 <= ts <= t0 + 1.9: return (t0, nm, dg, hit, (ts - t0) / 1.9)
    return None


def sunderer_x(ts):
    return lerp(SUN_X0, SUN_X1, smooth(1.0, 9.0, ts)) + 26 * smooth(132, 136, ts)


CAPS = [
    (1.2, 5.0, "the Elder had just told him\neverything."),
    (5.6, 8.8, "and then the walking stopped."),
    (9.6, 13.0, "it did not gather out of the dark\nlike the others."),
    (13.6, 15.8, "it had walked here."),
    (16.6, 20.2, "and the Elder's light\nwas almost out."),
    (28.4, 31.0, "it sang their song back —"),
    (31.6, 34.4, "in tune. and in time."),
    (35.0, 38.2, "the Sunderer."),
    (39.6, 41.2, "now."),
    (43.0, 46.2, "the light landed.\nand went out."),
    (47.4, 49.8, "one note was not enough."),
    (49.2, 50.8, "together."),
    (52.0, 54.0, "Do and Sol."),
    (57.6, 60.4, "he had already\nlearned that pair."),
    (61.0, 63.0, "so they changed it."),
    (66.0, 69.4, "two notes, no third between —"),
    (69.9, 71.6, "a spear."),
    (74.0, 77.0, "Fa and Do."),
    (78.6, 81.2, "Sol and Re."),
    (83.0, 86.4, "every pair\nhad its own edge."),
    (88.0, 91.0, "and he learned each one."),
    (92.2, 95.4, "so they threw another.\nand another."),
    (96.0, 99.0, "until he had learned\nevery pair."),
    (101.0, 102.6, "together."),
    (103.4, 105.8, "so they sounded three."),
    (106.6, 110.6, "three notes, as one voice:\na chord."),
    (114.0, 118.0, "he could copy a note.\nhe could copy the beat."),
    (119.6, 122.0, "but a chord is not a sound."),
    (122.8, 126.8, "it is what happens\nbetween more than one."),
    (128.0, 130.4, "and he was alone."),
    (132.4, 135.2, "and for the first time,\nit stepped back."),
    (137.0, 140.2, "so it did not break the chord."),
    (141.0, 143.6, "it broke the three."),
    (146.6, 148.4, "listen."),
    (152.0, 155.0, "and then there were two."),
    (155.6, 157.4, "no."),
]


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
    if ts < 158.0: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [158.0, 159.0, 160.6, 162.0], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.455), ("the more you observe.", 0.492)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "to be continued"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.552 * H)), tg, font=TAG, fill=(202, 194, 182, int(190 * fade)))


def thread(a, p0, p1, amt, col, n=16, w=5):
    for i in range(n):
        u = i / (n - 1.0)
        glow(a, lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - 0.02 * H * math.sin(math.pi * u),
             w, col, amt)


def story(ts):
    scene = "night" if ts < 62 else "fading_edge"
    a = pl.build_sky(scene).copy()
    base, mask = pl.planet_base(scene)
    a[mask] = base[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta_of(ts), scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    hp = heart_pulse(ts)
    sx = sunderer_x(ts); sy = ground_y(sx)
    a *= (1 - 0.16 * smooth(0, 10, ts))
    darken(a, sx + 0.06 * W, sy - 0.02 * H, 190, 0.40)

    # ---- the three ----
    KX = kx_at(ts); KY = ground_y(KX)                           # they give ground as he comes
    EX = ex_at(ts); EY = ground_y(EX)
    elder_out = smooth(OUT, OUT + 2.5, ts)
    taken = smooth(TAKE, TAKE + 3.0, ts)
    kl = (0.9 * smooth(39.0, 39.8, ts) * (1 - smooth(45, 46.5, ts))
          + 0.95 * smooth(FIFTH0 - 0.9, FIFTH0, ts) * (1 - smooth(FIFTH1, FIFTH1 + 1.5, ts))
          + 0.95 * smooth(CHORD0 - 1.0, CHORD0, ts) * (1 - smooth(116, 118, ts))
          + 0.6 * smooth(135.4, 136.2, ts) * (1 - smooth(139, 140.4, ts)))
    kspr, kfoot, kdx, kdy = character(140, "stand", ts, 1, lift=clamp(kl), lean=fl.idle_sway(ts))
    glow(a, KX + kdx, KY + kdy, 22, GOLD, 0.9 * (0.9 + 0.1 * hp))

    el = (0.9 * smooth(FIFTH0 - 0.9, FIFTH0, ts) * (1 - smooth(FIFTH1, FIFTH1 + 1.5, ts))
          + 0.95 * smooth(CHORD0 - 1.0, CHORD0, ts) * (1 - smooth(TAKE, TAKE + 1.5, ts))
          + 0.4 * smooth(123.2, 124.0, ts) * (1 - smooth(126, 127, ts)))
    espr, efoot, edx, edy = character(136, "stand", ts, 1, lift=clamp(el), lean=fl.idle_sway(ts * 0.9 + 1))
    ey_off = 0.055 * H * taken                                  # he is lifted / pulled away
    # CONTINUITY (Ep5): he gave his note away — his light has almost nothing left in it,
    # and it gutters harder the more he spends holding the fifth and the chord.
    spent = 1 - 0.30 * (smooth(FIFTH0, FIFTH0 + 2, ts) * (1 - smooth(FIFTH1, FIFTH1 + 2, ts))
                        + smooth(CHORD0, CHORD0 + 2, ts) * (1 - smooth(TAKE, TAKE + 1, ts)))
    faint = 0.34 * spent * (0.80 + 0.20 * math.sin(ts * 1.7) * math.sin(ts * 0.9))
    glow(a, EX + edx, EY + edy - ey_off, 18, WARM, faint * (1 - elder_out) * (0.9 + 0.1 * hp))

    SHX = shx_at(ts); SHY = ground_y(SHX) - 0.08 * H
    shx = SHX + fl.bob(ts, 6, f1=0.5, f2=1.15, ph=0.7)
    shy = SHY + fl.bob(ts, 8, ph=1.9)
    glow(a, shx, shy, 12, LAV, 0.9); glow(a, shx, shy, 30, LAV, 0.16)

    KP = (KX + kdx, KY + kdy - 0.10 * H)
    EP_ = (EX + edx, EY + edy - 0.10 * H - ey_off)
    SP = (shx, shy)

    # ---- one note: swallowed ----
    q = ts - ONE
    if 0 <= q <= 1.4:
        p = fl.ease_out(clamp(q / 0.6))
        n = 14
        for i in range(n):
            u = (i / (n - 1)) * p
            fade = 1.0 if q < 0.6 else max(0.0, 1 - (q - 0.6) / 0.8)
            glow(a, lerp(KP[0], sx, u), lerp(KP[1], sy - 0.05 * H, u) - 0.05 * H * math.sin(math.pi * u),
                 6, GOLD, 0.40 * fade)
        if q > 0.55:
            darken(a, sx + 0.055 * W, sy - 0.04 * H, 40, 0.5 * clamp((q - 0.55) / 0.4))

    # ---- two: the fifth, then it snaps ----
    fif = smooth(FIFTH0, FIFTH0 + 1.2, ts) * (1 - smooth(FIFTH1, FIFTH1 + 0.9, ts))
    if fif > 0.02:
        strain = 1.0 + 0.14 * math.sin(ts * 11) * smooth(FIFTH1 - 3, FIFTH1, ts)
        thread(a, KP, EP_, fif * 0.44 * strain, GOLD)
        thread(a, ((KP[0] + EP_[0]) / 2, (KP[1] + EP_[1]) / 2 - 0.03 * H),
               (sx - 0.05 * W, sy - 0.06 * H), fif * 0.22 * strain, GOLD, n=12, w=6)
    if FIFTH1 <= ts <= FIFTH1 + 1.2:                              # the snap
        b = 1 - (ts - FIFTH1) / 1.2
        for i in range(10):
            u = i / 9.0
            glow(a, lerp(KP[0], EP_[0], u) + 40 * math.sin(u * 9 + ts * 6),
                 lerp(KP[1], EP_[1], u) + 30 * math.cos(u * 7 + ts * 5), 5, GOLD, 0.35 * b)

    shake = 0.0
    # ---- THE POWER CHORDS: root and fifth, thrown as spears ----
    pw = power_at(ts)
    if pw is not None:
        t0, nm, dg, hit, u = pw
        col = GOLD if hit else [126, 132, 148]
        rise = smooth(0.0, 0.22, u); fly = smooth(0.24, 0.60, u)
        for k, g in enumerate(dg):                       # the two notes light
            p0 = SLOT[g]
            glow(a, p0[0], p0[1], 15 + 8 * rise, col, 0.32 + 0.5 * rise * (1 - smooth(0.8, 1.0, u)))
        if fly > 0.02:                                   # twin beams: a spear, not a shield
            src = [(KP[0], KP[1]), (EP_[0], EP_[1])]
            for k, g in enumerate(dg):
                p0 = SLOT[g]; s0 = src[k % 2]
                tip = (lerp(s0[0], sx, fly), lerp(s0[1] - 0.02 * H, sy - 0.05 * H, fly))
                for i in range(9):
                    uu = i / 8.0
                    glow(a, lerp(p0[0], tip[0], 0.35 + 0.65 * uu), lerp(p0[1], tip[1], 0.35 + 0.65 * uu),
                         5, col, (0.34 if hit else 0.16) * fly)
        if hit and u > 0.62:
            b = 1 - (u - 0.62) / 0.38
            glow(a, sx, sy - 0.05 * H, 26 + 44 * (1 - b), GOLD, 0.5 * b)
            shake = max(shake, 6.0 * b)
        if not hit and u > 0.55:                          # he sings the pair back
            b = smooth(0.55, 0.7, u) * (1 - smooth(0.9, 1.0, u))
            darken(a, sx + 0.05 * W, sy - 0.04 * H, 52, 0.5 * b)

    # ---- three: THE CHORD ----
    ch = smooth(CHORD0, CHORD0 + 1.4, ts) * (1 - smooth(TAKE, TAKE + 1.2, ts))
    if ch > 0.02:
        hit = 0.0
        for t0 in CHORD_HITS:
            if 0 <= ts - t0 <= 0.7: hit = max(hit, 1 - (ts - t0) / 0.7)
        amp = ch * (0.40 + 0.30 * hit)
        thread(a, KP, EP_, amp, GOLD, n=18)                        # the triangle
        thread(a, EP_, SP, amp, WARM, n=18)
        thread(a, SP, KP, amp, LAV, n=18)
        cxm = (KP[0] + EP_[0] + SP[0]) / 3; cym = (KP[1] + EP_[1] + SP[1]) / 3
        glow(a, cxm, cym, 40 + 40 * hit, GOLD, ch * (0.22 + 0.3 * hit))
        thread(a, (cxm, cym), (sx - 0.045 * W, sy - 0.06 * H), amp * 0.55, GOLD, n=14, w=7)

    for t0 in CHORD_HITS:                                          # he strikes; it holds
        q2 = ts - t0
        if -0.05 <= q2 <= 0.6:
            p = fl.ease_out(clamp(q2 / 0.4))
            for i in range(10):
                u = (i / 9.0) * p
                darken(a, lerp(sx, (KP[0] + EP_[0] + SP[0]) / 3 + 0.06 * W, u),
                       lerp(sy - 0.05 * H, (KP[1] + EP_[1] + SP[1]) / 3, u), 20, 0.40)
            if q2 > 0.35: shake = max(shake, 5.0 * (1 - (q2 - 0.35) / 0.25))

    # ---- he takes the Elder ----
    if TAKE <= ts <= OUT + 2:
        p = smooth(TAKE, TAKE + 2.0, ts)
        for i in range(12):
            u = i / 11.0
            darken(a, lerp(sx, EP_[0], u * p), lerp(sy - 0.05 * H, EP_[1], u * p), 26, 0.45 * p)
        if ts > OUT:
            darken(a, EP_[0], EP_[1], 60 + 60 * elder_out, 0.55 * elder_out)
    if OUT <= ts <= OUT + 1.2:
        shake = max(shake, 8.0 * (1 - (ts - OUT) / 1.2))
    # ...and then there were two: a line, not a triangle
    two = smooth(OUT + 1.5, OUT + 3.5, ts)
    if two > 0.02:
        thread(a, KP, SP, two * 0.30, GOLD, n=16)

    # ---- the Sunderer ----
    darken(a, sx + 0.055 * W, sy - 0.035 * H, 52, 0.85)            # the hole he carries
    glow(a, sx + 0.055 * W, sy - 0.035 * H, 13, [70, 92, 152], 0.34)
    darken(a, sx, sy - 0.04 * H, 100, 0.34)
    sspr, sfoot, _, _ = character(176, "walk" if ts < 12 else "stand", ts, -1,
                                  lean=0.02 * math.sin(ts * 0.5))

    # ---- the staff ----
    vis = smooth(1.0, 4.5, ts)
    modes = ["full"] * 8; glows = [0.26 + 0.14 * hp for _ in range(8)]
    for (t0, i) in HIS_SONG:                                       # he sings it perfectly
        if t0 <= ts <= t0 + 1.5: glows[i] = max(glows[i], 0.95 * (1 - (ts - t0) / 1.5))
    if ch > 0.3:
        for i in (0, 2, 4): glows[i] = max(glows[i], 0.55 + 0.25 * abs(math.sin(ts * 2.4)))
    if fif > 0.3:
        for i in (0, 4): glows[i] = max(glows[i], 0.55 + 0.25 * abs(math.sin(ts * 2.4)))
    if ts > OUT:
        for i in range(8): glows[i] *= 1 - 0.45 * elder_out
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(KX - kspr.size[0] / 2), int(KY - kfoot)), kspr)
    if elder_out < 0.98:
        sp = espr
        if elder_out > 0.02:
            al = sp.getchannel("A").point(lambda v: int(v * (1 - elder_out))); sp = sp.copy(); sp.putalpha(al)
        im.paste(sp, (int(EX - sp.size[0] / 2), int(EY - efoot - ey_off)), sp)
    im.paste(sspr, (int(sx - sspr.size[0] / 2), int(sy - sfoot)), sspr)
    staff.draw(im, vis, modes, glows)
    ImageDraw.Draw(im, "RGBA").text((shx + 28, shy - 24), "♯", font=SHF,
                                    fill=(216, 204, 248, 220), anchor="mm")
    pwn = power_at(ts)
    if pwn is not None:                                   # the pair's name
        t0, nm, dg, hit, u = pwn
        fade = float(np.interp(u, [0, 0.10, 0.72, 0.92], [0, 1, 1, 0]))
        col = (255, 214, 150) if hit else (150, 156, 170)
        d3 = ImageDraw.Draw(im, "RGBA")
        bb = d3.textbbox((0, 0), nm, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d3.text((xx, int(SY + 5.3 * LG)), nm, font=FSM, fill=col + (int(235 * fade),))
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    if shake > 0.4:
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
    K = dict(register=0, pan=0.34); E = dict(register=-12, pan=0.46); SH = dict(register=0, pan=0.58)

    w(pad([midi(44), midi(51), midi(56), midi(59)], 48, 0.04), 1, 0.5)
    w(bass(midi(30), 24, 0.05), 1, 0.5)
    for b in [x for x in BEATS if x <= 9]:                        # his footsteps: exactly on the beat
        d(softkick(0.10), b, 0.66)
    for (t0, i) in HIS_SONG:                                       # and he sings it perfectly
        d(piano(midi(PITCH[i]), 2.4, 0.115), t0, 0.64)
        w(piano(midi(PITCH[i] - 12), 3.0, 0.04), t0 + 0.04, 0.66)
    say(d, "who are you", 35.0, style="calm", **E)

    # one note — swallowed
    say(d, "now", 39.6, style="urgent", **K)
    d(piano(midi(72), 2.0, 0.135), ONE, 0.34)
    w(bass(midi(29), 4.0, 0.05), ONE + 0.6, 0.66)
    d(softkick(0.09), ONE + 0.6, 0.66)

    # two — the fifth he already knows, and the snap
    say(d, "together", 49.2, style="confident", **E)
    for t in np.arange(FIFTH0, FIFTH1 - 1, 3.4):
        d(piano(midi(60), 3.4, 0.13), t, 0.34); d(piano(midi(67), 3.4, 0.12), t + 0.02, 0.5)
        w(pad([midi(48), midi(55)], 3.4, 0.04), t, 0.5)
    d(piano(midi(60), 2.4, 0.11), FIFTH1 - 1.4, 0.64)              # he sings it back
    d(piano(midi(67), 2.4, 0.11), FIFTH1 - 1.38, 0.68)
    d(softkick(0.14), FIFTH1, 0.5); w(bass(midi(28), 6, 0.055), FIFTH1, 0.5)
    d(piano(midi(61), 1.4, 0.09), FIFTH1 + 0.1, 0.4)               # the snap: a sour note

    # THE POWER-CHORD VOLLEY — root and fifth, punched out, weapon after weapon
    for (t0, nm, dg, hit) in POWER:
        lo, hi5 = PITCH[dg[0]], PITCH[dg[1]]
        if hi5 < lo: hi5 += 12
        if hit:
            d(piano(midi(lo), 2.2, 0.145), t0, 0.34)               # root
            d(piano(midi(lo + 7), 2.2, 0.125), t0 + 0.012, 0.44)   # the bare fifth: no third
            d(piano(midi(lo + 12), 1.8, 0.075), t0 + 0.024, 0.56)  # octave on top: the spear
            w(bass(midi(lo - 24), 2.4, 0.055), t0, 0.5)
            d(softkick(0.115), t0 + 0.9, 0.5)
        else:                                                      # he sings the pair back
            d(piano(midi(lo), 1.4, 0.09), t0, 0.34)
            d(piano(midi(lo + 7), 1.4, 0.08), t0 + 0.012, 0.44)
            d(piano(midi(lo), 1.8, 0.075), t0 + 1.0, 0.66)
            d(piano(midi(lo + 7), 1.8, 0.07), t0 + 1.01, 0.68)
            w(bass(midi(29), 2.0, 0.045), t0 + 1.0, 0.66)
    for b in [x for x in BEATS if VOL_T0 - 1 <= x <= VOL_END]:      # the volley's drive
        d(softkick(0.06), b, 0.5)
    w(bass(midi(36), VOL_END - VOL_T0 + 4, 0.05), VOL_T0, 0.5)
    w(pad([midi(45), midi(52), midi(57)], VOL_END - VOL_T0 + 4, 0.035), VOL_T0, 0.5)

    # three — THE CHORD
    say(d, "together", 101.0, style="confident", **SH)
    for t in np.arange(CHORD0, TAKE, 4.2):
        for m, pan in [(60, 0.34), (64, 0.46), (67, 0.58)]:
            d(piano(midi(m), 4.4, 0.115), t, pan)
        w(pad([midi(48), midi(60), midi(64), midi(67)], 4.4, 0.05), t, 0.5)
    for t0 in CHORD_HITS:                                          # his blows, absorbed
        d(softkick(0.10), t0, 0.62); w(bass(midi(29), 1.0, 0.045), t0, 0.64)
    w(bass(midi(36), 40, 0.05), CHORD0, 0.5)

    # he takes the Elder
    d(softkick(0.16), TAKE, 0.5); w(bass(midi(28), 10, 0.06), TAKE, 0.6)
    for i, m in enumerate([67, 65, 63, 61, 59]):                   # the Elder's light sliding away
        d(piano(midi(m), 2.2, 0.08 - 0.01 * i), TAKE + 1.0 + i * 0.7, 0.48)
    say(d, "listen", 146.6, style="whisper", register=-12, pan=0.46)
    d(piano(midi(48), 6.0, 0.09), OUT, 0.46)
    d(softkick(0.15), OUT, 0.5); w(bass(midi(28), 12, 0.055), OUT, 0.5)
    # and then there were two
    for t in np.arange(152.0, 160, 3.4):
        d(piano(midi(60), 3.2, 0.10), t, 0.36); d(piano(midi(68), 3.2, 0.09), t + 0.02, 0.58)
    say(d, "no", 155.6, style="urgent", **K)
    w(pad([midi(44), midi(51), midi(56)], 12, 0.04), 152, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep16_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep16_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep16.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep16_silent.mp4", "-i", "ep16.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep6_the_chord_of_three.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep6_the_chord_of_three.mp4")


if __name__ == "__main__":
    main()
