"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 5 — "The Elder's Truth"
After the drum, the Keeper finally asks: who are you? And the Elder tells him
everything. What a keeper actually is (one who gives his own note away). Why the
Keeper walked home empty-handed his whole life. Where the dark came from — the first
keeper, who gave his note and then took it back, and left the first Silence behind.
Why the dark wears a keeper's shadow: it was one. And the last truth — the light the
Keeper found in the grass was the Elder's own, left there for him to find.

No fight. The Elder speaks and the world remembers, in memory scenes cut apart by the
Observer's blinks. ~2:28.
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
SDUR = 142.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COLD = [150, 176, 214]
LAV = [206, 190, 244]; MEMC = [232, 214, 186]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "5", "The Elder's Truth", "the Long Memory"
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


for s in ("night", "fading_edge", "dawn"): pl.build_sky(s); pl.planet_base(s)

# no travel: this episode stands still and remembers
def theta_of(ts): return 0.06 * ts

BLINKS = [(13.2, 0.30, 0.12, 0.46, 1.0),      # into memory
          (38.4, 0.28, 0.10, 0.42, 1.0),
          (62.4, 0.28, 0.10, 0.42, 1.0),
          (92.4, 0.28, 0.10, 0.42, 1.0),
          (114.4, 0.28, 0.10, 0.42, 1.0),
          (138.6, 0.32, 0.14, 0.50, 1.0),     # back to the present
          (147.0, 0.85, 0.30, 1.10, 1.0)]

# ---- the memories: (start, end, key) ----
MEMS = [(14.0, 38.0, "three"), (39.0, 62.0, "price"), (63.0, 92.0, "first"),
        (93.0, 114.0, "hollows"), (115.0, 138.2, "gift")]
def memory_at(ts):
    for (s, e, k) in MEMS:
        if s <= ts <= e:
            return k, ts - s, smooth(s, s + 0.9, ts) * (1 - smooth(e - 0.9, e, ts))
    return None, 0.0, 0.0


def ground_y(x):
    a = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(a) + SINK

KX = 0.375 * W; EX = 0.545 * W; SHX = 0.665 * W

CAPS = [
    (1.4, 5.0, "after the drum, the Keeper asked\nthe question he had never asked."),
    (5.4, 7.6, "who are you?"),
    (8.2, 10.4, "the Elder was quiet\nfor a long time."),
    (10.8, 12.6, "listen."),
    # I — the three
    (15.4, 19.0, "at the beginning\nthere were three keepers."),
    (19.8, 23.6, "no seven notes.\nno song. only three who walked."),
    (24.4, 27.2, "and the world was quiet."),
    (28.2, 31.4, "a note cannot\ncomplete itself."),
    (32.4, 35.4, "so we gave them ours."),
    # II — the price
    (40.2, 43.0, "that is what a keeper is."),
    (43.8, 46.8, "not one who has a song —"),
    (47.4, 50.6, "one who gives his own away."),
    (52.0, 55.8, "every night you walked home\nwith empty hands —"),
    (56.6, 60.4, "because you had\nalready given them."),
    # III — the first keeper
    (64.4, 67.8, "the first of us\ngave his note too."),
    (68.6, 71.6, "and then he wanted it back."),
    (73.4, 76.8, "you cannot take back\nwhat you have given."),
    (77.6, 80.0, "so he took anyway."),
    (82.4, 86.0, "and the place where\nhis note had been —"),
    (86.6, 89.4, "became the first silence."),
    (89.9, 91.6, "we called him the Sunderer."),
    # IV — the hollows
    (94.4, 98.0, "the ones who followed him\ndid the same."),
    (98.8, 102.6, "they took their notes back,\nand kept nothing."),
    (104.6, 108.6, "that is why the dark\nwears a keeper's shadow."),
    (110.0, 112.4, "it was one."),
    # V — the gift
    (116.4, 119.8, "and the light you found\nin the grass —"),
    (123.0, 125.2, "i left it there."),
    (126.4, 128.4, "it was mine."),
    (129.2, 130.8, "no."),
    (131.6, 136.6, "i gave you mine,\nso that you would have\none to give."),
    # coda
    (139.6, 142.4, "then what do you have left?"),
    (144.6, 147.4, "listen."),
    (148.4, 152.0, "and far ahead, something\nwas already walking toward them."),
]


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
    if ts < 153.0: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [153.0, 154.0, 155.2, 156.4], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.455), ("the more you observe.", 0.492)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "to be continued"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.552 * H)), tg, font=TAG, fill=(202, 194, 182, int(190 * fade)))


def keeper_sprite(h, ts, face=1, lift=0.0, walk=False, ph=0.0):
    return character(h, "walk" if walk else "stand", ts + ph, face,
                     lift=clamp(lift), lean=(0.03 if walk else 0.0) + fl.idle_sway(ts + ph))


# ================= THE MEMORIES =================
def mem_three(a, im_notes, t):
    """three keepers on a young, quiet world — and one gives his light away."""
    xs = [0.30 * W, 0.47 * W, 0.64 * W]
    give = smooth(17.0, 21.0, t)                     # the giving happens late in the beat
    for i, x in enumerate(xs):
        y = ground_y(x)
        dim = 1.0 - (0.75 * give if i == 1 else 0.0)  # the middle one gives his away
        spr, foot, dx, dy = keeper_sprite(132, t, 1, lift=0.55 * give if i == 1 else 0.0, ph=i * 2.1)
        glow(a, x + dx, y + dy, 20, WARM, 0.85 * dim)
        im_notes.append((spr, x, y, foot))
    # the dim note that receives it
    nx, ny = 0.80 * W, ground_y(0.80 * W) - 0.055 * H
    glow(a, nx, ny, 11, WARM, 0.10 + 0.85 * give)
    if 0.02 < give < 0.99:                            # the light crossing between them
        px, py = fl.flight((xs[1], ground_y(xs[1]) - 0.10 * H), (nx, ny), give, rise=0.16)
        glow(a, px, py, 9, WARM, 0.8)


def mem_price(a, im_notes, t):
    """the young Keeper walking a line of notes — brightening them, dimming himself."""
    prog = clamp(t / 20.0)
    kx = lerp(0.16 * W, 0.78 * W, prog)
    ky = ground_y(kx)
    spr, foot, dx, dy = keeper_sprite(134, t, 1, walk=True)
    glow(a, kx + dx, ky + dy, 22, WARM, 0.92 - 0.55 * prog)      # his light shrinking
    im_notes.append((spr, kx, ky, foot))
    for i in range(6):                                            # the notes he has passed
        nx = 0.22 * W + i * 0.115 * W
        ny = ground_y(nx) - 0.055 * H - 8 * math.sin(t * 0.6 + i)
        lit = clamp((kx - nx) / (0.06 * W))
        glow(a, nx, ny, 10, WARM, 0.08 + 0.72 * lit)


def mem_first(a, im_notes, t):
    """the first keeper takes his note back — and leaves the first silence."""
    x = 0.44 * W; y = ground_y(x)
    nx, ny = 0.68 * W, ground_y(0.68 * W) - 0.06 * H
    take = smooth(9.0, 15.0, t)                       # he reaches in and pulls
    spr, foot, dx, dy = keeper_sprite(138, t, 1, lift=0.75 * smooth(7.0, 10.0, t))
    glow(a, x + dx, y + dy, 20, WARM, 0.55 + 0.45 * take)   # his own light swells as he takes
    im_notes.append((spr, x, y, foot))
    glow(a, nx, ny, 11, WARM, 0.85 * (1 - take))            # the note going out
    if 0.02 < take < 0.99:
        px, py = fl.flight((nx, ny), (x + dx, y + dy - 0.10 * H), take, rise=0.10)
        glow(a, px, py, 8, WARM, 0.75)
    void = smooth(15.0, 24.0, t)                      # and the hole it leaves
    if void > 0.02:
        darken(a, nx, ny, 40 + 150 * void, 0.55 * void)
        for k in range(7):
            ang = k * 0.9 + t * 0.3
            darken(a, nx + (60 + 120 * void) * math.cos(ang), ny + (34 + 70 * void) * math.sin(ang),
                   32, 0.30 * void)
        glow(a, nx, ny, 6, COLD, 0.22 * void)


def mem_hollows(a, im_notes, t):
    """keepers taking their notes back — their lanterns going out, one by one."""
    xs = [0.28 * W, 0.45 * W, 0.62 * W, 0.79 * W]
    for i, x in enumerate(xs):
        y = ground_y(x)
        out = smooth(3.0 + i * 3.2, 6.4 + i * 3.2, t)          # each goes dark in turn
        spr, foot, dx, dy = keeper_sprite(132 + 4 * i, t, -1 if i > 1 else 1, ph=i * 1.7)
        glow(a, x + dx, y + dy, 20, WARM, 0.85 * (1 - out))
        if out > 0.05:                                          # what is left carries a hole
            darken(a, x + dx, y + dy, 34, 0.75 * out)
            glow(a, x + dx, y + dy, 10, [70, 92, 152], 0.30 * out)
            darken(a, x, y - 0.03 * H, 70, 0.22 * out)
        im_notes.append((spr, x, y, foot))


def mem_gift(a, im_notes, t):
    """the Elder kneels and leaves his own note in the grass."""
    x = 0.50 * W; y = ground_y(x)
    place = smooth(4.0, 9.0, t)
    spr, foot, dx, dy = keeper_sprite(136, t, 1, lift=-0.55 * place)     # reaching down
    glow(a, x + dx, y + dy, 21, WARM, 0.88 * (1 - 0.72 * place))         # his light leaving him
    im_notes.append((spr, x, y, foot))
    gx, gy = 0.615 * W, ground_y(0.615 * W) - 16
    if place > 0.02:
        if place < 0.99:
            px, py = fl.flight((x + dx, y + dy), (gx, gy), place, rise=0.10, settle=0.25)
        else:
            px, py = gx, gy + fl.bob(t, 2.5, f1=0.35, f2=0.8)
        glow(a, px, py, 12, WARM, 0.95)
        glow(a, px, py, 30, WARM, 0.18)


MEMFN = {"three": mem_three, "price": mem_price, "first": mem_first,
         "hollows": mem_hollows, "gift": mem_gift}


def story(ts):
    key, mt, mfade = memory_at(ts)
    scene = "night" if key is None else "fading_edge"
    if key == "gift": scene = "dawn"

    a = pl.build_sky(scene).copy()
    base, mask = pl.planet_base(scene)
    a[mask] = base[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta_of(ts), scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    sprites = []
    if key is None:
        # ---- the present: the three of them, standing still ----
        kl = 0.55 * smooth(4.8, 5.6, ts) * (1 - smooth(7.6, 8.8, ts)) \
             + 0.5 * smooth(139.0, 139.8, ts) * (1 - smooth(143, 144.4, ts))
        el = 0.5 * smooth(10.2, 11.0, ts) * (1 - smooth(13, 14, ts)) \
             + 0.5 * smooth(144.0, 144.8, ts) * (1 - smooth(148, 149.4, ts))
        ky = ground_y(KX); ey = ground_y(EX)
        kspr, kfoot, kdx, kdy = keeper_sprite(140, ts, 1, lift=kl)
        espr, efoot, edx, edy = keeper_sprite(136, ts, -1, lift=el, ph=1.3)
        glow(a, KX + kdx, ky + kdy, 22, GOLD, 0.9)
        # the Elder's light is nearly gone once we know the truth
        efade = 1.0 - 0.62 * smooth(138.5, 143, ts)
        glow(a, EX + edx, ey + edy, 21, WARM, 0.86 * efade)
        sprites += [(kspr, KX, ky, kfoot), (espr, EX, ey, efoot)]
        sx = SHX + fl.bob(ts, 6, f1=0.5, f2=1.15, ph=0.7)
        sy = ground_y(SHX) - 0.075 * H + fl.bob(ts, 8, ph=1.9)
        glow(a, sx, sy, 11, LAV, 0.85); glow(a, sx, sy, 28, LAV, 0.15)
        # the thing walking toward them, at the very end
        far = smooth(148, 154, ts)
        if far > 0.02:
            fx_ = 0.94 * W; fy_ = ground_y(fx_)
            darken(a, fx_, fy_ - 0.02 * H, 60 + 60 * far, 0.55 * far)
            glow(a, fx_, fy_ - 0.02 * H, 6, COLD, 0.22 * far)
    else:
        MEMFN[key](a, sprites, mt)

    # ---- the staff, dimmed while remembering ----
    vis = smooth(1.0, 4.5, ts) * (1 - 0.55 * mfade)
    modes = ["full"] * 8; glows = [0.26] * 8
    if key == "three":                                  # in the beginning: no notes at all
        modes = ["ghost"] * 8; glows = [0.0] * 8
        for i in range(8):
            if mt > 18 + i * 0.4: modes[i] = "full"; glows[i] = 0.22
    if key == "first" and mt > 15:                      # one goes out and stays out
        modes[5] = "ghost"
    if key == "hollows":
        for i in range(8): glows[i] = 0.18
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    for (spr, x, y, foot) in sprites:
        im.paste(spr, (int(x - spr.size[0] / 2), int(y - foot)), spr)
    if key is None:
        ImageDraw.Draw(im, "RGBA").text((sx + 28, sy - 24), "♯", font=SHF,
                                        fill=(216, 204, 248, 220), anchor="mm")
    staff.draw(im, vis, modes, glows)
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im, np.float32)
    # ---- THE LONG MEMORY GRADE ----
    if mfade > 0.01:
        grey = frame.mean(axis=2, keepdims=True)
        sep = grey * np.array([1.06, 0.99, 0.86], np.float32)
        frame = frame * (1 - 0.80 * mfade) + sep * (0.80 * mfade)
        frame *= (1 - 0.10 * mfade)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.40 + 0.16 * mfade)
    frame = fx.grain(frame, ts * FPS, amt=0.013 + 0.020 * mfade)
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
    K = dict(register=0, pan=0.40); E = dict(register=-12, pan=0.58)

    # the present: quiet, unresolved
    w(pad([midi(45), midi(52), midi(57), midi(60)], 16, 0.038), 1, 0.5)
    say(d, "who are you", 5.4, style="calm", **K)
    say(d, "listen", 10.8, style="calm", **E)

    # I — the three (bare, open fifths: a world with no song yet)
    w(pad([midi(36), midi(43), midi(50)], 26, 0.04), 14.2, 0.5)
    for i, t in enumerate([16.0, 20.2, 24.4]):
        d(piano(midi(48 + i * 7), 4.0, 0.075), t, 0.36 + 0.14 * i)
    d(piano(midi(60), 3.4, 0.10), 32.6, 0.42)                        # the gift crossing over
    d(piano(midi(67), 4.6, 0.11), 34.4, 0.62)

    # II — the price (a descending line: he is being emptied)
    w(pad([midi(41), midi(48), midi(53), midi(57)], 24, 0.04), 39.2, 0.5)
    for i, m in enumerate([72, 71, 69, 67, 65, 64, 62, 60]):
        d(piano(midi(m), 3.0, 0.095 - 0.004 * i), 41.0 + i * 2.3, 0.38 + 0.03 * i)
    for t in np.arange(41.0, 60, 1.5): d(softkick(0.06), t, 0.5)     # his long walk

    # III — the first keeper (the taking: a note pulled DOWN and out)
    w(pad([midi(40), midi(47), midi(52)], 30, 0.04), 63.2, 0.5)
    d(piano(midi(69), 3.0, 0.12), 66.0, 0.62)
    for i, m in enumerate([69, 68, 67, 66, 65]):                     # dragged down a half step at a time
        d(piano(midi(m), 2.0, 0.10), 73.4 + i * 1.15, 0.62 - 0.02 * i)
    d(softkick(0.13), 78.0, 0.5)
    w(bass(midi(28), 14, 0.06), 82.0, 0.5)                           # the first silence
    d(piano(midi(42), 6.0, 0.075), 86.4, 0.5)
    say(d, "no", 89.9, style="calm", register=-12, pan=0.58)          # naming the Sunderer

    # IV — the hollows (four lights going out)
    w(pad([midi(38), midi(45), midi(50), midi(56)], 22, 0.038), 93.2, 0.5)
    for i in range(4):
        t0 = 96.0 + i * 3.2
        d(piano(midi(67 - i * 3), 2.4, 0.085), t0, 0.34 + 0.16 * i)
        d(softkick(0.07), t0 + 1.1, 0.5)
        w(bass(midi(29), 3.0, 0.045), t0 + 1.1, 0.5 + 0.06 * i)
    d(piano(midi(42), 5.0, 0.08), 110.0, 0.5)

    # V — the gift (warm, and heartbreaking: the Elder's own note)
    w(pad([midi(36), midi(48), midi(55), midi(60)], 24, 0.045), 115.2, 0.5)
    d(piano(midi(60), 5.0, 0.13), 118.0, 0.5)                        # it is Do. the Keeper's note.
    say(d, "it was mine", 126.4, style="calm", **E)
    say(d, "no", 129.2, style="urgent", **K)
    say(d, "i give you this", 131.8, style="calm", **E)
    d(piano(midi(60), 6.0, 0.11), 133.0, 0.5)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 14, 0.048), 133.0, 0.5)

    # coda: the question he cannot answer
    say(d, "what now", 139.6, style="calm", **K)
    w(bass(midi(31), 10, 0.05), 142.0, 0.5)                          # the rest where an answer should be
    say(d, "listen", 144.6, style="whisper", register=-12, pan=0.58)
    d(softkick(0.10), 149.0, 0.62); d(softkick(0.10), 150.7, 0.62)   # something walking
    w(bass(midi(29), 9, 0.05), 149.0, 0.64)
    for i, m in enumerate([60, 63, 67]):
        d(piano(midi(m), 5.0, 0.07), 153.5 + i * 0.2, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep15_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep15_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep15.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep15_silent.mp4", "-i", "ep15.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep5_the_elders_truth.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep5_the_elders_truth.mp4")


if __name__ == "__main__":
    main()
