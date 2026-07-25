"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 8 — "The First Note"  (rich cut)
Every night the Keeper tucks the world's notes into their places — and walks home
with empty hands. Tonight, caught in the grass, he finds a small light of his own.
It rings HIGH — too high for the songs he knows. He tries it beside Ti (it burns —
a half step), above Re (restless — a seventh); he begins to believe it belongs to
no song at all. Then the deepest stone of the empty scale hums by itself, and his
note answers — call and response — until the two sound together and fuse: the OCTAVE.
He carries it to the top of the staff: high or low, Do is Do. One note, two homes.
Hidden lesson: octave equivalence. ~1:52.
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
SDUR = 106.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COOL = [150, 172, 214]
NOTEC = [255, 228, 185]                              # his note: a touch whiter than the lantern
CENTER_Y = 0.52
CH, EP, TITLE, LAND = "I", "8", "The First Note", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
PLACED = 72.5                                        # his note settles into high Do


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
SEGS = [(0, "night"), (20, "dawn"), (60, "morning"), (96, "golden")]

ROT = 0.13
def _rate(u):
    if u < 12: return 1.0
    if u < 17: return 1.0 - smooth(12, 17, u)
    if u < 92: return 0.0
    if u < 98: return smooth(92, 98, u)
    return 1.0
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))


GRASS = (0.615 * W, FEET - 14)
DO0 = staff.note_xy(0); DO7 = staff.note_xy(7)
TI6 = staff.note_xy(6); RE1 = staff.note_xy(1)
TOP = (0.50 * W, SY - 2.4 * LG)
TIH = (TI6[0], TI6[1] - 1.1 * LG)
REH = (RE1[0], RE1[1] - 1.2 * LG)
DOWN = (0.50 * W, SY + 6.8 * LG)
DO0H = (DO0[0], DO0[1] - 1.2 * LG)


def note_pos(ts, hand):
    """His found note: grass -> circles his lantern like a moth -> the trials ->
    the doubt -> the answer -> home at the top of the staff."""
    if ts < 16: return GRASS
    if ts < 18:
        return fl.flight(GRASS, hand, (ts - 16) / 2, rise=0.10, settle=0.25)
    if ts <= 29.5:                                     # orbiting the lantern
        return (hand[0] + 30 * math.cos(ts * 0.9), hand[1] - 6 + 20 * math.sin(ts * 0.9))
    segs = [(29.5, 31.2, hand, TOP, "fly"),
            (31.2, 37, TOP, TOP, "hold"),
            (37, 38.6, TOP, TIH, "land"),
            (38.6, 43.5, TIH, TIH, "hold"),
            (43.5, 45.2, TIH, REH, "fly"),
            (45.2, 50.3, REH, REH, "hold"),
            (50.3, 52.2, REH, DOWN, "fly"),
            (52.2, 64.5, DOWN, DOWN, "hold"),
            (64.5, 66.2, DOWN, DO0H, "fly"),
            (66.2, 70.5, DO0H, DO0H, "hold"),
            (70.5, PLACED, DO0H, DO7, "land")]
    x, y = fl.path(ts, segs, DO7)
    if 38.6 <= ts <= 43.5:                             # beside Ti it burns — it can't stay
        k = smooth(38.6, 39.6, ts) * (1 - smooth(42.5, 43.5, ts))
        y += 0.26 * LG * math.sin(ts * 12) * k
        x += 0.16 * LG * math.sin(ts * 7.1) * k
    elif 45.2 <= ts <= 50.3:                           # above Re it wanders, restless
        x += fl.bob(ts, 9, f1=0.6, f2=1.4, ph=1.0)
        y += fl.bob(ts, 7, ph=2.2)
    elif 52.2 <= ts <= 64.5:                           # the doubt — it sinks, barely breathing
        y += fl.bob(ts, 4, f1=0.5, f2=1.0, ph=0.4)
    elif 31.2 <= ts <= 37 or 66.2 <= ts <= 70.5:
        y += fl.bob(ts, 5, ph=1.5)
    return x, y


def note_bright(ts):
    b = 1.0
    b *= 1 - 0.55 * (smooth(51, 54, ts) * (1 - smooth(58, 64, ts)))   # dims in the doubt
    return b


def ring(d, cx, cy, t0, ts, col, rmax=52):
    q = ts - t0
    if 0 <= q <= 0.9:
        u = q / 0.9; r = 8 + rmax * fl.ease_out(u); al = int(200 * (1 - u) ** 1.3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (al,), width=3)


def draw_octave_brace(im, ts):
    v = smooth(73.5, 76.5, ts)
    if v < 0.02: return
    d = ImageDraw.Draw(im, "RGBA")
    x0 = DO0[0]; x1 = DO7[0]
    ytop = SY - 3.9 * LG
    al = int(200 * v)
    pts = []
    for k in range(31):
        u = k / 30.0
        pts.append((lerp(x0, x1, u * v), ytop + 0.9 * LG * math.sin(math.pi * u)))
    d.line(pts, fill=(236, 224, 200, al), width=2, joint="curve")
    d.line([(x0, ytop), (x0, ytop + 0.5 * LG)], fill=(236, 224, 200, al), width=2)
    if v > 0.9:
        d.line([(x1, ytop), (x1, ytop + 0.5 * LG)], fill=(236, 224, 200, al), width=2)
    d.text(((x0 + x1) / 2, ytop - 0.3 * LG), "8", font=BR, fill=(240, 226, 202, al), anchor="mm")


CAPS = [
    (2.0, 7.5, "every night, the Keeper tucked\nthe world's notes into their places."),
    (9.0, 14.0, "and every night he walked home\nwith empty hands."),
    (16.0, 22.0, "then — caught in the grass,\na small light. humming."),
    (23.5, 29.5, "it rang high and bright —\ntoo high for the songs he knew."),
    (31.0, 36.5, "but where did it belong?"),
    (38.0, 43.5, "beside Ti it burned —\ntoo sharp, too close."),
    (45.0, 50.0, "above Re it wandered,\nrestless."),
    (51.5, 57.5, "perhaps, he thought,\nit belonged to no song at all."),
    (58.5, 64.0, "then the deepest stone\nbegan to hum."),
    (65.0, 70.0, "the same heart —\nsinging one floor higher."),
    (71.5, 77.0, "high or low,\nDo is Do."),
    (79.0, 86.5, "one note — two homes.\nand the song had begun."),
    (96.0, 103.0, "the more you know,\nthe more you observe."),
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


def keeper_lift(ts):
    lift = smooth(16, 19, ts) * 0.55                                   # raises the lantern
    lift -= smooth(29.5, 31.5, ts) * 0.40                              # eases back to carry
    lift += 0.45 * smooth(36.5, 38, ts) * (1 - smooth(43, 45, ts))     # trial one gesture
    lift += 0.45 * smooth(45.5, 47, ts) * (1 - smooth(49.5, 51, ts))   # trial two gesture
    lift -= 0.35 * smooth(51.5, 54, ts) * (1 - smooth(58, 61, ts))     # the doubt: arm falls
    lift += 0.75 * smooth(64.5, 67, ts) * (1 - smooth(74, 77, ts))     # the answer: arm rises
    return clamp(lift, -0.6, 1.0)


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

    # the Keeper — PLANTED at the apex; hand offsets go to the lantern, never the body
    walk = ts < 13 or ts > 93.5
    lean = (0.03 if walk else 0.0) + fl.idle_sway(ts)
    spr, foot, odx, ody = character(140, "walk" if walk else "stand", ts, 1,
                                    lift=keeper_lift(ts), lean=lean)
    kx = CX                                            # body stays put
    hand = (kx + odx, FEET + ody)                      # his lantern
    glow(a, hand[0], hand[1], 22, GOLD, 0.9 * (0.9 + 0.1 * math.sin(ts * 2.6)))

    # fireflies converge on the little light in the grass
    cv = smooth(13.5, 15.5, ts) * (1 - smooth(18, 20, ts))
    if cv > 0.02:
        for i in range(8):
            u = smooth(13.5, 19.0, ts)
            rr = lerp(150, 12, u)
            ang = ts * 1.1 + i * 0.785
            glow(a, GRASS[0] + rr * math.cos(ang), GRASS[1] - abs(rr * math.sin(ang)) * 0.5,
                 3.5, WARM, cv * 0.28)

    # his found note
    seen = smooth(14, 16.5, ts)
    nx, ny = note_pos(ts, hand)
    nb = note_bright(ts)
    if seen > 0.02 and ts < PLACED:
        pulse = 0.85 + 0.15 * math.sin(ts * 3.1 + 0.7)
        glow(a, nx, ny, 13 * (0.7 + 0.3 * nb), NOTEC, seen * nb * pulse)
        glow(a, nx, ny, 34, NOTEC, seen * nb * 0.15)

    # trial flashes: cool on the wrong homes
    for (tt, px, py) in [(39.5, *TI6), (41.5, *TI6), (46.5, *RE1), (48.5, *RE1)]:
        dd = ts - tt
        if -0.3 <= dd <= 1.2:
            al = float(np.interp(dd, [-0.3, 0.1, 0.8, 1.2], [0, 1, 0.5, 0]))
            glow(a, px, py, 18, COOL, al * 0.5)

    # the deepest stone hums; then the fusion thread between it and his note
    if 58 <= ts <= 66.5:
        hum = (0.35 + 0.45 * abs(math.sin((ts - 58) * math.pi / 2.0)))
        glow(a, DO0[0], DO0[1], 16, GOLD, hum * 0.8)
    if 66.2 <= ts <= PLACED + 1.5:
        v = smooth(66.2, 67.2, ts) * (1 - smooth(PLACED, PLACED + 1.5, ts))
        for k in range(12):
            u = k / 11.0
            glow(a, lerp(DO0[0], nx, u), lerp(DO0[1], ny, u), 3.5, WARM,
                 v * 0.4 * (0.6 + 0.4 * math.sin(ts * 3 + k)))

    # coda sparks: little lights rise past the staff while the octave sings
    if 78 <= ts <= 87:
        cvv = smooth(78, 79.5, ts) * (1 - smooth(85.5, 87, ts))
        for i in range(8):
            yy = SY + 5 * LG - ((ts * 26 + i * 41) % (9 * LG))
            xx = 0.5 * W + fl.bob(ts * 0.7 + i * 2.3, 0.16 * W, f1=0.31, f2=0.77, ph=i)
            glow(a, xx, yy, 3, WARM, cvv * 0.16)

    # staff: all ghosts; the deepest stone wakes, then both Do's are home
    vis = smooth(24, 31, ts)
    modes = ["ghost"] * 8; glows = [0.0] * 8
    if 58 <= ts < 66.5:
        modes[0] = "empty"
        glows[0] = 0.35 + 0.45 * abs(math.sin((ts - 58) * math.pi / 2.0))
    if ts >= 66.5:
        modes[0] = "full"
        glows[0] = clamp(1.0 - (ts - 66.5) / 1.6) * 0.55 + 0.4
    if ts >= PLACED:
        modes[7] = "full"
        glows[7] = clamp(1.0 - (ts - PLACED) / 1.6) * 0.55 + 0.4
    if ts >= 78:                                       # the octave see-saw: low and high trade breaths
        ph = math.sin(2 * math.pi * (ts - 78) / 1.5)
        glows[0] = 0.4 + 0.3 * max(0.0, ph)
        glows[7] = 0.4 + 0.3 * max(0.0, -ph)
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(FEET - foot)), spr)
    staff.draw(im, vis, modes, glows)
    draw_octave_brace(im, ts)

    d = ImageDraw.Draw(im, "RGBA")
    ring(d, GRASS[0], GRASS[1], 16.2, ts, (255, 224, 175), rmax=30)
    ring(d, nx, ny, 23.6, ts, (255, 228, 185), rmax=44)
    ring(d, TI6[0], TI6[1], 39.5, ts, (170, 188, 220), rmax=30)
    ring(d, RE1[0], RE1[1], 46.5, ts, (170, 188, 220), rmax=30)
    for t0 in (58.6, 60.6, 62.6):
        ring(d, DO0[0], DO0[1], t0, ts, (255, 214, 150), rmax=26)
    ring(d, DO0[0], DO0[1], 66.4, ts, (255, 214, 150), rmax=46)
    ring(d, DO7[0], DO7[1], PLACED, ts, (255, 214, 150), rmax=56)
    if 31 <= ts <= 37:
        qv = np.interp(ts, [31, 32.5, 35.5, 37], [0, 1, 1, 0])
        d.text((0.5 * W, SY - 3.1 * LG), "?", font=font(int(2.2 * LG)),
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

    # --- an evolving harmonic bed (the story told in chords) ---
    w(pad([midi(48), midi(55), midi(60)], 17, 0.045), 3, 0.5)            # C — the nightly round
    w(pad([midi(45), midi(52), midi(60)], 18, 0.045), 19.5, 0.5)         # Am — wonder
    w(pad([midi(41), midi(48), midi(57)], 15, 0.045), 36.5, 0.5)         # F — searching
    w(pad([midi(43), midi(50), midi(55)], 8, 0.032), 51, 0.5)            # G, thin — the doubt
    w(pad([midi(36), midi(48), midi(55), midi(60)], 13, 0.05), 58, 0.5)  # C low — the answer
    w(pad([midi(36), midi(48), midi(55), midi(64), midi(72)], 18, 0.05), 70.5, 0.5)  # C full — home
    w(pad([midi(41), midi(53), midi(57)], 6.5, 0.045), 88.5, 0.5)        # F — the last look back
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 12, 0.05), 94.5, 0.5)  # C — rest

    # --- the nightly round: a gentle rocking motif while he walks ---
    for t in np.arange(2, 12, 1.4): d(softkick(0.09), t, 0.5)
    for (m, t, amp) in [(60, 3.5, 0.08), (67, 5.0, 0.07), (69, 6.6, 0.06), (67, 8.0, 0.06), (60, 9.6, 0.07)]:
        d(piano(midi(m), 2.2, amp), t, 0.5)

    # --- discovery: starlight falls; the little light hums ---
    for i, m in enumerate([91, 88, 84, 79, 76, 72]):
        d(piano(midi(m), 1.2, 0.05 - 0.004 * i), 16.2 + i * 0.16, 0.5 + 0.04 * (i % 2))
    d(piano(midi(72), 2.5, 0.10), 17.5, 0.55)
    # it rings high and bright
    d(piano(midi(72), 3.5, 0.16), 23.6, 0.5); d(piano(midi(84), 2.5, 0.05), 23.7, 0.55)
    w(piano(midi(72), 2.0, 0.05), 25.8, 0.5)                             # far echo

    # --- trial one: beside Ti it burns (a half step) ---
    d(piano(midi(72), 1.8, 0.12), 39.3, 0.55); d(piano(midi(71), 1.8, 0.12), 39.35, 0.45)
    d(piano(midi(72), 2.0, 0.12), 41.3, 0.55); d(piano(midi(71), 2.0, 0.12), 41.35, 0.45)
    d(piano(midi(71), 1.4, 0.07), 43.0, 0.45)
    # --- trial two: above Re it wanders (a seventh) ---
    d(piano(midi(72), 1.8, 0.11), 46.3, 0.55); d(piano(midi(62), 1.8, 0.11), 46.35, 0.45)
    for (m, t) in [(62, 48.0), (72, 48.5), (62, 49.0)]:
        d(piano(midi(m), 1.0, 0.07), t, 0.5)

    # --- the doubt: one thin voice, and air ---
    d(piano(midi(72), 3.5, 0.07), 52.5, 0.5)
    d(piano(midi(84), 2.0, 0.035), 55.5, 0.55)

    # --- the answer: the deepest stone hums, and his note replies — call and response ---
    w(bass(midi(36), 5.0, 0.07), 58.3, 0.5)
    for (lo, hi, t0, t1, a0, a1) in [(60, 72, 58.6, 59.6, 0.09, 0.06),
                                     (60, 72, 60.6, 61.5, 0.10, 0.08),
                                     (60, 72, 62.6, 63.4, 0.11, 0.10)]:
        d(piano(midi(lo), 2.2, a0), t0, 0.42)
        d(piano(midi(hi), 2.0, a1), t1, 0.60)
    # fusion: the two sound as one — the octave
    d(piano(midi(60), 3.5, 0.14), 66.3, 0.45); d(piano(midi(72), 3.5, 0.14), 66.3, 0.55)
    for (t, dt) in [(66.5, 0.35), (68.5, 0.35)]:                         # a heartbeat
        d(softkick(0.10), t, 0.5); d(softkick(0.07), t + dt, 0.5)
    for i, m in enumerate([48, 60, 64, 67, 72]):                          # a rolled bloom
        d(piano(midi(m), 2.6, 0.07), 68.3 + i * 0.12, 0.5)

    # --- home: the placement chime ---
    d(piano(midi(72), 5.0, 0.17), PLACED, 0.5)
    d(piano(midi(84), 2.5, 0.05), PLACED + 0.1, 0.55)
    d(piano(midi(60), 4.0, 0.10), PLACED + 0.15, 0.45)
    w(bass(midi(36), 10, 0.06), PLACED, 0.5)

    # --- coda: the octave see-saw — low and high trading breaths ---
    for t in np.arange(78, 86, 1.5):
        d(piano(midi(60), 1.3, 0.075), t, 0.42)
        d(piano(midi(72), 1.3, 0.075), t + 0.75, 0.58)

    # --- walking on, and rest ---
    for t in np.arange(92, 102, 1.4): d(softkick(0.09), t, 0.5)
    d(piano(midi(60), 6.0, 0.13), 96, 0.5); d(piano(midi(67), 6.0, 0.07), 96, 0.5)
    d(piano(midi(72), 5.0, 0.08), 97.5, 0.5)
    w(bass(midi(36), 8.0, 0.06), 96, 0.5)

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
