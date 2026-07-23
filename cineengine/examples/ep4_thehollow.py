"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 4 — "The Hollow"   (the first battle)
The Fading Edge — a whole village of light — is attacked by the Hollow: fallen
keepers, void where their light should be, who glide onto the threads between notes
and CUT them apart. The Keeper cannot fight with light alone; the dark cannot enter
a chord. So he fights by MATCHING — binding frightened notes into chords that bloom
and drive the Hollow back. He saves the Edge, but not everyone: one light goes dark
and the dark makes a new Hollow of it. The Sunderer watches from the horizon.

Dense, beat-driven action. No empty frames — full of notes, threads, and blooms.
~2:25 vertical.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, walk_notes
import title_card as tc
import world

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 137.0
DUR = TITLE_DUR + SDUR
GROUND = 0.82 * H
fx = FX(W, H)
GOLD = [255, 200, 130]
COLD = [150, 172, 224]
VOID = [40, 46, 70]
CENTER_Y = 0.46
CH, EP, TITLE, LAND = "I", "4", "The Hollow", "the Fading Edge"


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1])
def mix3(c0, c1, x):
    return [c0[i] + (c1[i] - c0[i]) * clamp(x) for i in range(3)]


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
def gfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(48); FSM = font(34); GF = gfont(52)


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


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([6, 8, 22], np.float32) * (1 - t)
            + np.array([15, 16, 36], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.7 * W, GROUND + 0.3 * H], fill=(16, 18, 34))
    d.ellipse([0.4 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(19, 21, 38))
    d.rectangle([0, int(GROUND), W, H], fill=(12, 13, 26))
    return np.asarray(im, np.float32)
BG = world.build("fading_edge")             # richer, colder world for the battle

# ---- the village of light: many notes across the Fading Edge (never an empty frame) ----
_v = np.random.default_rng(23)
N = 26
VX = _v.uniform(0.06, 0.94, N)
VY = _v.uniform(0.52, 0.78, N)
VN = [ [53,55,57,60,62,64,65,57,60,53][i % 10] for i in range(N) ]
VPH = _v.uniform(0, 6.28, N)
# initial bonds (a living web); (i, j)
BONDS0 = [(0,3),(3,7),(1,4),(4,8),(2,5),(6,9),(7,10),(8,11),(10,14),(11,15),
          (12,16),(13,17),(9,13),(5,12),(14,18),(15,19),(16,20),(18,22),(20,23),(21,24)]

# scripted battle events (story-local seconds)
CUTS = [(16.0, 0), (45.0, 4), (52.0, 9), (60.0, 12), (100.0, 17)]        # (time, BONDS0 index) severed
BINDS = [(34.0, 1, 4), (42.0, 6, 9), (50.0, 10, 14), (58.0, 13, 17),
         (66.0, 16, 20), (86.0, 25, 21)]                                  # (time, i, j) matched -> chord bloom
BLOOMS = [(t, i, j) for (t, i, j) in BINDS] + [(94.0, -1, -1)]            # -1,-1 = the great chord (whole field)
# the Hollow: (enter_t, exit_t, x0, x1, y) glide in from the right
HOLLOWS = [(11.0, 40.0, 1.15, 0.62, 0.60), (43.0, 96.0, 1.15, 0.70, 0.66),
           (56.0, 96.0, 1.15, 0.40, 0.58), (98.0, 137.0, 0.80, 0.95, 0.64)]
FOCAL = 24        # the dying light the Hollow swarm at the climax
OUTSIDER = 25     # the accidental beside it (cold-blue) that completes the chord
LOST = 21         # the light that is lost -> becomes a Hollow (the cost)

CAPS = [
    (2.0, 9.0, "at the fading edge,\nthe last village of light\nstill sang."),
    (10.5, 16.0, "then the dark\ntook a shape."),
    (18.0, 24.0, "and began to cut\nthe song apart."),
    (26.0, 32.0, "the keeper could not fight it\nwith light alone."),
    (34.5, 40.0, "but the dark\ncannot enter a chord."),
    (43.0, 47.0, "so he matched them."),
    (50.0, 54.0, "note to note."),
    (58.0, 62.0, "beat to beat."),
    (64.0, 69.0, "hold them together —"),
    (74.0, 80.0, "one light was almost gone,\nand its note fit no one."),
    (84.0, 90.0, "so he woke the outsider\nbeside it."),
    (91.0, 96.0, "the wrong note —\nmade right."),
    (97.0, 102.0, "and the whole edge\nsang at once."),
    (104.0, 110.0, "he could not save them all."),
    (111.0, 117.0, "and the dark made\none more of its own."),
    (119.0, 125.0, "but the ones who held together,\nthe dark could not touch."),
    (127.0, 132.0, "far off,\nsomething was watching."),
    (133.5, 137.0, "the more you know,\nthe more you observe."),
]
GLYPHS = [(34.6,), ]  # placeholder (glyphs drawn from BIND times below)


def bond_state(idx, ts):
    """returns (alive_fraction, cut_progress) for BONDS0[idx]."""
    for (ct, ci) in CUTS:
        if ci == idx and ts >= ct:
            return (1 - smooth(ct, ct + 1.2, ts), smooth(ct, ct + 1.0, ts))
    return (1.0, 0.0)


def light_bright(i, ts):
    b = 0.6
    # fading ones on the right dim over the opening, until rescued
    if i in (FOCAL,):
        b = 0.5 * (1 - 0.7 * smooth(20, 78, ts)) + 1.1 * smooth(88, 94, ts)
    if i == OUTSIDER:
        b = 0.25 + 0.9 * smooth(86, 92, ts)
    if i == LOST:
        b = 0.6 * (1 - smooth(100, 108, ts))          # cut, goes dark
    # endpoints of a cut bond dim a bit
    for (ct, ci) in CUTS:
        a_, b_ = BONDS0[ci]
        if i in (a_, b_) and ci != 17 and ts >= ct:
            b *= (1 - 0.4 * smooth(ct, ct + 1.5, ts) * (1 - smooth(ct + 8, ct + 14, ts)))
    # the great chord: everyone blazes
    b += 0.7 * smooth(94, 98, ts) * (1 - smooth(112, 120, ts)) if i not in (LOST,) else 0
    b += 0.3 * smooth(118, 122, ts)                    # settle glow (survivors)
    return max(0.0, b)


def light_color(i, ts):
    if i == OUTSIDER:
        return mix3(COLD, GOLD, smooth(86, 92, ts))
    if i == FOCAL:
        return mix3(COLD, GOLD, smooth(88, 94, ts))
    return GOLD


def draw_thread(a, p0, p1, bright, ts, cut=0.0, col=GOLD):
    n = 16
    for k in range(n):
        u = k / (n - 1)
        if cut > 0.01 and abs(u - 0.5) < 0.5 * cut:      # a growing gap = the sever
            continue
        px, py = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
        py -= 0.03 * H * math.sin(math.pi * u)           # gentle sag
        glow(a, px, py, 4, col, bright * 0.45 * (0.6 + 0.4 * math.sin(ts * 4 + k)))
    if 0.02 < cut < 0.6:                                  # snap flash
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 0.03 * H
        glow(a, mx, my, 10, [255, 150, 150], (0.6 - cut) * 0.8)


def draw_bloom(a, cx, cy, age, big=False):
    if age < 0 or age > 1.6: return
    R = age * (300 if big else 150)
    br = (0.8 if big else 0.5) * math.exp(-age * (1.4 if big else 2.0))
    # expanding ring
    x0 = max(0, int(cx - R - 40)); x1 = min(W, int(cx + R + 40))
    y0 = max(0, int(cy - R - 40)); y1 = min(H, int(cy + R + 40))
    if x1 > x0 and y1 > y0:
        yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dist = np.sqrt((xg - cx) ** 2 + (yg - cy) ** 2)
        ring = np.exp(-((dist - R) ** 2) / (2 * (16 if big else 12) ** 2)) * br
        a[y0:y1, x0:x1] += ring[..., None] * np.array(GOLD, np.float32)
    glow(a, cx, cy, 26 if big else 16, [255, 230, 190], br * 1.2)


def hollow_pos(h, ts):
    (te, tx, x0, x1, y) = h
    if ts < te or ts > tx: return None
    p = smooth(te, tx - 4 if tx - 4 > te else tx, ts) if tx < 130 else smooth(te, te + 30, ts)
    return (lerp(x0, x1, p), y)


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.7, e - 0.7, e], [0, 1, 1, 0])
            small = txt.startswith("the more you know")
            f = FSM if small else FS
            lines = txt.split("\n")
            hs = [d.textbbox((0, 0), ln, font=f)[3] for ln in lines]
            total = sum(int(h * 1.5) for h in hs)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f)
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f,
                       fill=(234, 230, 222, int(236 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)


def draw_glyphs(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (bt, i, j) in BINDS:                      # a ♫ blooms at each match
        age = ts - bt
        if 0 <= age <= 1.6:
            al = np.interp(age, [0, 0.25, 1.1, 1.6], [0, 1, 1, 0])
            mx = (VX[i] + VX[j]) / 2 * W; my = ((VY[i] + VY[j]) / 2 - 0.05) * H
            d.text((mx, my - age * 30), "♫", font=GF, fill=(255, 214, 150, int(230 * al)), anchor="mm")


def story(ts):
    a = BG.copy()
    world.atmosphere(a, ts, "fading_edge")

    # the Silence advancing from the right, then driven back at the great chord
    adv = smooth(8, 78, ts) * (1 - 0.7 * smooth(92, 100, ts))
    darken(a, (1.28 - 0.5 * adv) * W, 0.55 * H, 0.5 * W, 0.85 * adv)

    # threads (the web) — cut ones snap
    for idx, (i, j) in enumerate(BONDS0):
        al, cut = bond_state(idx, ts)
        if al > 0.02:
            draw_thread(a, (VX[i] * W, VY[i] * H), (VX[j] * W, VY[j] * H),
                        al * (0.6 + 0.4 * light_bright(i, ts)), ts, cut=cut)
    # new bonds the Keeper makes
    for (bt, i, j) in BINDS:
        g = smooth(bt, bt + 1.0, ts)
        if g > 0.02:
            draw_thread(a, (VX[i] * W, VY[i] * H), (VX[j] * W, VY[j] * H), g * 0.8, ts)
    # the great chord binds the whole surviving field
    gc = smooth(94, 98, ts) * (1 - smooth(120, 126, ts))
    if gc > 0.02:
        for k in range(0, N - 2, 2):
            if k in (LOST,): continue
            draw_thread(a, (VX[k] * W, VY[k] * H), (VX[k + 1] * W, VY[k + 1] * H), gc * 0.6, ts)

    # the village lights
    for i in range(N):
        b = light_bright(i, ts)
        if b > 0.02:
            glow(a, VX[i] * W, VY[i] * H, 10 + 4 * (i == FOCAL), light_color(i, ts),
                 b * (0.85 + 0.15 * math.sin(ts * 3 + VPH[i])))

    # chord-blooms (shields / matches)
    for (bt, i, j) in BINDS:
        cx = (VX[i] + VX[j]) / 2 * W if i >= 0 else 0.5 * W
        cy = (VY[i] + VY[j]) / 2 * H if i >= 0 else 0.6 * H
        draw_bloom(a, cx, cy, ts - bt, big=(bt == 86.0))
    draw_bloom(a, 0.5 * W, 0.62 * H, ts - 94.0, big=True)     # the great chord bloom

    # the Hollow — void figures; darken + cold rim where their light should be
    hollow_sprites = []
    for h in HOLLOWS:
        p = hollow_pos(h, ts)
        if p is None: continue
        hx, hy = p[0] * W, p[1] * H
        # a Hollow recoils near a fresh bloom (consonance repels it)
        recoil = 0.0
        for (bt, i, j) in BINDS:
            if 0 <= ts - bt <= 1.4:
                bx = (VX[i] + VX[j]) / 2 * W if i >= 0 else 0.5 * W
                if abs(bx - hx) < 0.28 * W: recoil = max(recoil, 1 - (ts - bt) / 1.4)
        hx += recoil * 60
        darken(a, hx, hy - 0.02 * H, 40, 0.8)                # the void orb
        glow(a, hx, hy - 0.02 * H, 12, [70, 90, 150], 0.4)   # cold rim
        spr, fy, odx, ody = character(96, "stand", 0.0, -1)
        hollow_sprites.append((spr, hx, hy, fy, 0.9 - 0.4 * recoil))

    # the Keeper — races along the front line, lantern high. Weighted motion
    # (analytic): velocity drives lean, cloak drag, body-dip, and a lagging lantern.
    def kxf(u): return clamp(0.12 + 0.72 * smooth(24, 100, u), 0.08, 0.9)
    kx = kxf(ts)
    vx = (kxf(ts + 0.05) - kxf(ts - 0.05)) / 0.10
    walking = (24 < ts < 100) and abs(vx) > 0.0025
    dip = -abs(math.sin(ts * 6)) * 0.018 * H if walking else 0.0    # body dips on each footfall
    lift = 0.5 + 0.5 * smooth(26, 34, ts)
    lean = clamp(vx * 3.5, -0.14, 0.14) + 0.035 * math.sin(ts * 1.1)
    trail = clamp(-vx * 1.6, -0.09, 0.09)
    face = 1 if vx >= -1e-4 else -1
    kspr, kfy, kodx, kody = character(130, "walk" if walking else "stand", ts, face,
                                      lift=lift, lean=lean, trail=trail)
    kx_px = kx * W; ky_px = 0.80 * H + dip
    kox = kx_px + kodx; koy = ky_px + kody
    lkx = kxf(ts - 0.12) * W + kodx                                # lantern trails the hand
    glow(a, 0.6 * kox + 0.4 * lkx, koy, 26 + 6 * lift, GOLD, 1.0 * (0.9 + 0.1 * math.sin(ts * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    for (spr, hx, hy, fy, al) in hollow_sprites:
        if al > 0.05:
            layer = spr.copy()
            if al < 0.999:
                alpha = layer.split()[3].point(lambda v: int(v * al)); layer.putalpha(alpha)
            im.paste(layer, (int(hx - spr.size[0] / 2), int(hy - fy)), layer)
    im.paste(kspr, (int(kx_px - kspr.size[0] / 2), int(ky_px - kfy)), kspr)

    # the Sunderer watching (climax hook) — a vast cold gaze on the horizon
    if ts > 124:
        d2 = ImageDraw.Draw(im, "RGBA"); hk = smooth(125, 129, ts)
        for r, al in ((120, 40), (60, 70)):
            d2.ellipse([0.5 * W - r, 0.16 * H - r * 0.6, 0.5 * W + r, 0.16 * H + r * 0.6],
                       fill=(90, 110, 170, int(al * hk)))

    draw_glyphs(im, ts)
    draw_caption(im, ts)
    tc.quiz_overlay(im, ts, "how do you fight the silence?", 121.0, 127.0,
                    options=["with a brighter light", "alone", "by holding together"], y=0.30)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=200, gain=0.72)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, ts * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


# ---------- audio: the battle has BEATS ----------
def kick(amp=0.5, dur=0.28):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 120 * np.exp(-t * 22) + 45
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    return (y * amp).astype(np.float32)

def tritone(amp=0.2, dur=1.2):                      # the Hollow's cold clash
    n = int(dur * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * midi(59) * t) + np.sin(2 * np.pi * midi(65) * t))   # tritone-ish cluster
    return (y * np.exp(-t * 2.2) * amp * 0.5).astype(np.float32)


def title_audio():
    n = int(TITLE_DUR * SR); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    p = pad([midi(41), midi(53), midi(57)], TITLE_DUR, amp=0.05)
    add(L, p, 0.2); add(R, np.roll(p, 400), 0.2)
    add(L, wind_gust(4.0, 0.03, 3), 0.6); add(R, wind_gust(4.0, 0.03, 4), 0.9)
    L = reverb(L); R = reverb(R)
    st = np.tanh(np.stack([L, R], 1) * 1.1); st /= (np.max(np.abs(st)) + 1e-6); st *= 0.6
    fi, fo = int(0.5 * SR), int(1.0 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]; st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st.astype(np.float32)


def story_audio():
    n = int(SDUR * SR); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # the village singing (a warm bed of the F-major chord), thinning as it's cut
    village = pad([midi(53), midi(57), midi(60)], 16.0, amp=0.05)
    add(L, village, 1.0); add(R, np.roll(village, 400), 1.0)
    # the Hollow arrives — tritone stabs on each cut
    for (ct, ci) in [(16, 0), (45, 4), (52, 9), (60, 12), (100, 17)]:
        st(tritone(0.22), ct - 0.2, 0.7)
    # the battle BEATS — a driving pulse from ~34 to ~100, building
    t0 = 34.0
    while t0 < 100.0:
        density = 0.4 + 0.5 * smooth(34, 92, t0)
        st(kick(0.34 * density), t0, 0.5)
        if t0 > 58: st(kick(0.2 * density), t0 + 0.5, 0.4)     # off-beat as it intensifies
        t0 += 1.0
    # the Keeper matching notes into chords (each bind = a chord + rising root)
    for (bt, i, j) in BINDS:
        st(pad([midi(VN[i]), midi(VN[j]), midi(VN[i] + 7)], 3.0, amp=0.06), bt, 0.5)
        st(piano(midi(VN[i]), 3.0, amp=0.11), bt, 0.4)
        st(piano(midi(VN[j]), 3.0, amp=0.11), bt + 0.2, 0.6)
    # the climax — the outsider completes it, then the GREAT CHORD blazes
    st(piano(midi(63), 4.0, amp=0.13), 88.0, 0.7)             # the outsider (a flat)
    great = pad([midi(53), midi(57), midi(60), midi(64), midi(67)], 12.0, amp=0.08)
    add(L, great, 94.0); add(R, np.roll(great, 500), 94.0)
    st(bass(midi(41), 8.0, amp=0.11), 94.0, 0.5)
    st(kick(0.6), 94.0, 0.5); st(kick(0.4), 95.0, 0.5)
    # the cost — a light goes out (a note falls and hollows: pitch bends down, dies)
    st(tritone(0.18, 2.0), 104.0, 0.3)
    # settle — survivors hold; a warm calm chord, a slow heartbeat, then quiet
    hold = pad([midi(53), midi(57), midi(60)], 14.0, amp=0.05)
    add(L, hold, 118.0); add(R, np.roll(hold, 400), 118.0)
    for hb in np.arange(112, 126, 1.4): st(kick(0.14), hb, 0.5)   # fading heartbeat
    st(owl(0.045, 53), 122.0, 0.7)
    st(piano(midi(53), 8.0, amp=0.10), 133.0, 0.5)

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.2); mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fo = int(4.0 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix.astype(np.float32)


def build_audio():
    return np.concatenate([title_audio(), story_audio()], axis=0)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep4h_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep4h_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep4h.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep4h_silent.mp4", "-i", "ep4h.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "ch1_ep4_the_hollow.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep4_the_hollow.mp4")


if __name__ == "__main__":
    main()
