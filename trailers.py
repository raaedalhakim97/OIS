"""
THE OBSERVER WORLD — three pinned trailers.

  python trailers.py --which world     # 1. what this is           (~0:22)
  python trailers.py --which lessons   # 2. the hidden curriculum  (~0:26)
  python trailers.py --which dark      # 3. Chapter II, the danger (~0:28)

Built to be pinned: a hook inside the first second, big legible text, fast blink
cuts, and the handle on the last card.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
import world, planet as pl, staff
import flow as fl, eye
import songbook as sb

W, H = 1080, 1920
FPS = 24
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COLD = [150, 176, 214]
LAV = [206, 190, 244]; VIOLET = [176, 158, 232]
LG = staff.LG; SY = staff.SY
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34; FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]
BEAT = 60.0 / 72.0
HANDLE = "@3theobserver3"


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def sfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
def gfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
BIG = sfont(62); MID = sfont(50); SML = sfont(36); TINY = gfont(30); LBL = gfont(40)


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


def ground_y(x):
    aa = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(aa) + SINK


def text(im, s, y, font=MID, fade=1.0, col=(238, 234, 226)):
    d = ImageDraw.Draw(im, "RGBA")
    for i, ln in enumerate(s.split("\n")):
        bb = d.textbbox((0, 0), ln, font=font)
        xx = (W - (bb[2] - bb[0])) // 2
        yy = int(y * H) + i * int(font.size * 1.45)
        d.text((xx + 2, yy + 2), ln, font=font, fill=(0, 0, 0, int(150 * fade)))
        d.text((xx, yy), ln, font=font, fill=col + (int(242 * fade),))


def cap(im, ts, caps, y=0.46, font=MID):
    for (s, e, txt) in caps:
        if s <= ts <= e:
            f = float(np.interp(ts, [s, s + 0.35, e - 0.35, e], [0, 1, 1, 0]))
            text(im, txt, y, font, f)


def finish(im, ts, blinks, grade=0.0):
    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.70)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    eye.apply_lids(frame, eye.blink_amount(ts, blinks))
    return frame.clip(0, 255).astype(np.uint8)


def base_scene(ts, scene, theta=0.0):
    a = pl.build_sky(scene).copy()
    b, mask = pl.planet_base(scene)
    a[mask] = b[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta, scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)
    return a


# ═══════════════════════════════════════════════ 1 · THE WORLD ═══════════════
W1 = 23.0
W1_CAPS = [(0.5, 4.0, "every soul\nis a note."),
           (5.4, 8.6, "some are bright."),
           (8.9, 12.0, "some are fading."),
           (13.0, 16.6, "no note\ncompletes itself."),
           (17.4, 20.0, "so one walks the world,\nhelping them find\nwho they harmonise with.")]
W1_BLINKS = [(4.7, 0.22, 0.07, 0.34, 1.0), (12.5, 0.22, 0.07, 0.34, 1.0),
             (20.6, 0.30, 0.16, 0.50, 1.0)]


def t_world(ts):
    a = base_scene(ts, "night", 0.06 * ts)
    a *= (1 - 0.55 * (1 - smooth(0.0, 3.2, ts)))               # open out of near-black
    kx = CX; ky = FEET
    lift = 0.85 * smooth(13.2, 15.0, ts) * (1 - smooth(18.5, 20.0, ts))
    walk = 5.0 < ts < 12.5
    spr, foot, dx, dy = character(150, "walk" if walk else "stand", ts, 1,
                                  lift=clamp(lift), lean=(0.03 if walk else 0) + fl.idle_sway(ts))
    seen = smooth(2.4, 4.2, ts)
    glow(a, kx + dx, ky + dy, 24, GOLD, 0.95 * seen)
    # the notes of the world
    for i in range(7):
        nx = 0.16 * W + i * 0.115 * W
        ny = ground_y(nx) - 0.085 * H - 22 * math.sin(ts * 0.7 + i)
        v = smooth(5.0 + i * 0.25, 6.4 + i * 0.25, ts)
        dim = (i in (2, 5))
        amp = v * (0.22 if dim else 0.85)
        if dim and ts > 15.4: amp = v * lerp(0.22, 0.85, smooth(15.4, 17.4, ts))
        glow(a, nx, ny, 11, WARM, amp)
        glow(a, nx, ny, 28, WARM, amp * 0.16)
    vis = smooth(16.4, 19.0, ts)
    if vis > 0.02:
        modes = ["full"] * 8
        glows = [0.30 + 0.45 * clamp(1 - abs(ts - (17.0 + i * 0.30)) / 0.6) for i in range(8)]
        staff.glows_into(a, vis, glows, modes)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - foot)), spr)
    if vis > 0.02:
        staff.draw(im, vis, ["full"] * 8, [0.35] * 8)
    cap(im, ts, W1_CAPS)
    if ts > 20.7:
        f = float(np.interp(ts, [20.7, 21.3, 22.4, 23.0], [0, 1, 1, 0]))
        text(im, "THE OBSERVER WORLD", 0.415, BIG, f)
        text(im, "the more you know, the more you observe.", 0.478, SML, f, (212, 204, 190))
        text(im, HANDLE, 0.532, TINY, f, (196, 188, 176))
    return finish(im, ts, W1_BLINKS)


def a_world(d, w):
    w(pad([midi(48), midi(55), midi(60)], 21, 0.042), 1.0, 0.5)
    d(piano(midi(60), 5.0, 0.15), 0.6, 0.5)
    for i, m in enumerate([67, 64, 72]):
        d(piano(midi(m), 3.4, 0.075), 5.6 + i * 1.8, 0.4 + 0.1 * i)
    for t in np.arange(5.4, 12.2, 1.45): d(softkick(0.07), t, 0.5)
    d(piano(midi(65), 3.0, 0.09), 13.2, 0.42)
    d(piano(midi(69), 4.0, 0.12), 15.6, 0.56)
    sb.chord(d, w, "F", 17.0, dur=3.2, amp=0.95, pan=0.5)
    sb.chord(d, w, "C", 20.4, dur=4.0, amp=1.1, pan=0.5)
    for i, m in enumerate(PITCH):
        d(piano(midi(m), 2.0, 0.085), 17.0 + i * 0.30, 0.38 + 0.03 * i)


# ═══════════════════════════════════════════ 2 · THE LESSONS ═════════════════
W2 = 27.0
L_ITEMS = [(5.0, "the scale", "scale"), (8.4, "the octave", "octave"),
           (11.8, "half steps", "flip"), (15.2, "the beat", "beat"),
           (18.6, "chords", "chord"), (22.0, "silence", "rest")]
W2_CAPS = [(0.4, 2.6, "this is a\nmusic lesson."), (3.0, 4.6, "you won't notice.")]
W2_BLINKS = [(2.8, 0.20, 0.06, 0.30, 1.0), (4.8, 0.16, 0.05, 0.26, 1.0),
             (8.2, 0.09, 0.02, 0.14, 0.4), (11.6, 0.09, 0.02, 0.14, 0.4),
             (15.0, 0.09, 0.02, 0.14, 0.4), (18.4, 0.09, 0.02, 0.14, 0.4),
             (21.8, 0.09, 0.02, 0.14, 0.4), (24.4, 0.26, 0.12, 0.42, 1.0)]


def t_lessons(ts):
    a = base_scene(ts, "night", 0.03 * ts)
    a *= 0.86
    item = None
    for (t0, label, kind) in L_ITEMS:
        if t0 <= ts <= t0 + 3.3: item = (t0, label, kind, ts - t0)
    modes = ["full"] * 8; glows = [0.22] * 8
    vis = smooth(0.6, 2.2, ts)
    if item:
        t0, label, kind, u = item
        if kind == "scale":
            for i in range(8):
                k = t0 + 0.25 + i * 0.26
                if k <= ts <= k + 0.9: glows[i] = max(glows[i], 1 - (ts - k) / 0.9)
        elif kind == "octave":
            glows[0] = glows[7] = 0.45 + 0.45 * abs(math.sin(u * 3.2))
        elif kind == "flip":
            modes[5] = "raised" if int(u * 2.2) % 2 else "fallen"
            glows[5] = 0.5
        elif kind == "beat":
            i = int((ts - t0) / BEAT)
            glows[(i * 2) % 8] = 0.95
        elif kind == "chord":
            for g in (0, 2, 4): glows[g] = 0.5 + 0.4 * abs(math.sin(u * 3))
        elif kind == "rest":
            modes = ["rest"] * 8; glows = [0.0] * 8
        staff.glows_into(a, vis, glows, modes)
    kx = CX * 0.62; ky = ground_y(kx)
    spr, foot, dx, dy = character(120, "stand", ts, 1, lift=0.5, lean=fl.idle_sway(ts))
    glow(a, kx + dx, ky + dy, 19, GOLD, 0.85)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - foot)), spr)
    if item:
        staff.draw(im, vis, modes, glows)
        t0, label, kind, u = item
        f = float(np.interp(u, [0, 0.3, 2.9, 3.3], [0, 1, 1, 0]))
        text(im, label, 0.415, LBL, f, (255, 226, 178))
        if kind == "octave":
            d2 = ImageDraw.Draw(im, "RGBA")
            d2.text(((SLOT[0][0] + SLOT[7][0]) / 2, SY - 3.6 * LG), "8", font=gfont(30),
                    fill=(240, 226, 202, int(220 * f)), anchor="mm")
    cap(im, ts, W2_CAPS)
    if ts > 24.5:
        f = float(np.interp(ts, [24.5, 25.1, 26.3, 27.0], [0, 1, 1, 0]))
        text(im, "18 episodes.", 0.40, MID, f)
        text(im, "no theory. all story.", 0.448, MID, f)
        text(im, "THE OBSERVER WORLD", 0.515, SML, f, (222, 214, 200))
        text(im, HANDLE, 0.558, TINY, f, (196, 188, 176))
    return finish(im, ts, W2_BLINKS)


def a_lessons(d, w):
    w(pad([midi(48), midi(55), midi(60)], 25, 0.038), 0.6, 0.5)
    d(piano(midi(60), 3.0, 0.13), 0.5, 0.5)
    for i, m in enumerate(PITCH):                                    # the scale
        d(piano(midi(m), 1.6, 0.105), 5.25 + i * 0.26, 0.38 + 0.03 * i)
    d(piano(midi(60), 3.2, 0.13), 8.6, 0.4); d(piano(midi(72), 3.2, 0.12), 8.62, 0.6)  # octave
    d(piano(midi(68), 2.0, 0.11), 12.0, 0.5); d(piano(midi(69), 2.4, 0.11), 13.4, 0.5)  # half step
    for i in range(5): d(softkick(0.12), 15.4 + i * BEAT, 0.5)                          # the beat
    for i in range(5): d(piano(midi(60 if i % 4 == 0 else 55), 1.0, 0.075), 15.4 + i * BEAT, 0.5)
    sb.chord(d, w, "C", 18.8, dur=2.6, amp=1.0, pan=0.5)                                # chords
    sb.chord(d, w, "Am", 21.0, dur=1.0, amp=0.9, pan=0.5)
    w(bass(midi(24), 3.4, 0.02), 22.0, 0.5)                                             # silence
    sb.chord(d, w, "C", 24.6, dur=3.4, amp=1.15, pan=0.5)
    sb.sing(d, sb.THEME[:8], 24.8, beat=0.34, amp=0.09, pan=0.56)


# ═══════════════════════════════════════════ 3 · THE DARK ════════════════════
W3 = 29.0
D_HITS = [(12.2, "Fa · Do", [3, 7]), (13.9, "Sol · Re", [4, 1]), (15.6, "La · Mi", [5, 2]),
          (17.3, "Re · La", [1, 5])]
W3_CAPS = [(0.4, 3.4, "something in the dark\nheard the song."),
           (7.0, 9.0, "it learned pitch."),
           (9.6, 11.6, "it learned time."),
           (18.4, 20.6, "it learned every chord."),
           (21.4, 24.0, "and then\nthere were two."),
           (24.8, 26.6, "one thing was left\nit could not copy.")]
W3_BLINKS = [(3.6, 0.20, 0.06, 0.30, 1.0), (6.8, 0.12, 0.04, 0.18, 0.5),
             (11.9, 0.10, 0.03, 0.15, 0.4), (13.6, 0.07, 0.02, 0.11, 0.3),
             (15.3, 0.07, 0.02, 0.11, 0.3), (17.0, 0.07, 0.02, 0.11, 0.3),
             (20.8, 0.22, 0.08, 0.34, 1.0), (26.8, 0.34, 0.18, 0.55, 1.0)]


def t_dark(ts):
    a = base_scene(ts, "night", 0.03 * ts)
    a *= (1 - 0.30 * smooth(0, 4, ts))
    sx = lerp(1.02 * W, 0.80 * W, smooth(4.0, 8.0, ts)); sy = ground_y(sx)
    darken(a, sx + 0.05 * W, sy - 0.02 * H, 180, 0.42)
    # the birth on the beat
    ba = 0.0
    if 3.8 <= ts <= 7.2:
        k = int((ts - 3.8) / BEAT) + 1
        q = (ts - 3.8) - (k - 1) * BEAT
        ba = clamp(k / 4.0 + math.exp(-q * 5.5) * 0.28 * (k / 4.0))
        rr = 6 + 90 * ba
        darken(a, sx, sy - 0.03 * H, rr, 0.30 + 0.5 * ba)
        glow(a, sx, sy - 0.03 * H, rr * 0.4, [64, 84, 140], 0.10 + 0.14 * ba)
    kx = 0.30 * W; ky = ground_y(kx)
    kspr, kfoot, kdx, kdy = character(140, "stand", ts, 1,
                                      lift=0.9 * smooth(11.6, 12.4, ts) * (1 - smooth(19, 20.4, ts)),
                                      lean=fl.idle_sway(ts))
    glow(a, kx + kdx, ky + kdy, 22, GOLD, 0.9)
    ex = 0.44 * W; ey = ground_y(ex)
    eout = smooth(21.0, 23.0, ts)
    espr, efoot, edx, edy = character(136, "stand", ts, 1, lean=fl.idle_sway(ts * 0.9 + 1))
    glow(a, ex + edx, ey + edy, 18, WARM, 0.34 * (1 - eout))
    modes = ["full"] * 8; glows = [0.24] * 8
    vis = smooth(1.0, 3.0, ts)
    # the power chord volley
    for (t0, nm, dg) in D_HITS:
        if t0 <= ts <= t0 + 1.5:
            u = (ts - t0) / 1.5
            for g in dg: glows[g] = max(glows[g], 0.95 * (1 - u * 0.7))
            fly = smooth(0.18, 0.6, u)
            for g in dg:
                p0 = SLOT[g]
                for i in range(9):
                    uu = (i / 8.0) * fly
                    glow(a, lerp(p0[0], sx, uu), lerp(p0[1], sy - 0.05 * H, uu), 5, GOLD, 0.32 * fly)
            if u > 0.6: glow(a, sx, sy - 0.05 * H, 30, GOLD, 0.45 * (1 - (u - 0.6) / 0.4))
    if 7.2 <= ts <= 9.2:                                     # pitch: the fifth, snapped
        glows[0] = glows[4] = 0.75
    if 9.6 <= ts <= 11.6:                                    # time
        glows[int((ts - 9.6) / BEAT) * 2 % 8] = 0.9
    if ts >= 24.9:                                           # the rest
        modes = ["rest"] * 8; glows = [0.0] * 8
    staff.glows_into(a, vis, glows, modes)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(ky - kfoot)), kspr)
    if eout < 0.98:
        sp = espr
        if eout > 0.02:
            al = sp.getchannel("A").point(lambda v: int(v * (1 - eout))); sp = sp.copy(); sp.putalpha(al)
        im.paste(sp, (int(ex - sp.size[0] / 2), int(ey - efoot)), sp)
    if ba > 0.55 or ts > 7.2:
        sspr, sfoot, _, _ = character(176, "stand", ts, -1, lean=0.02 * math.sin(ts * 0.5))
        al = sspr.getchannel("A").point(lambda v: int(v * clamp(smooth(6.2, 7.4, ts))))
        sspr = sspr.copy(); sspr.putalpha(al)
        im.paste(sspr, (int(sx - sspr.size[0] / 2), int(sy - sfoot)), sspr)
    staff.draw(im, vis, modes, glows)
    d2 = ImageDraw.Draw(im, "RGBA")
    for (t0, nm, dg) in D_HITS:
        if t0 <= ts <= t0 + 1.4:
            f = float(np.interp(ts - t0, [0, 0.15, 1.1, 1.4], [0, 1, 1, 0]))
            bb = d2.textbbox((0, 0), nm, font=SML); xx = (W - (bb[2] - bb[0])) // 2
            d2.text((xx, int(SY + 5.2 * LG)), nm, font=SML, fill=(255, 214, 150, int(230 * f)))
    cap(im, ts, W3_CAPS)
    if ts > 26.9:
        f = float(np.interp(ts, [26.9, 27.4, 28.4, 29.0], [0, 1, 1, 0]))
        text(im, "CHAPTER II", 0.395, SML, f, (216, 208, 194))
        text(im, "THE LISTENING DARK", 0.435, BIG, f)
        text(im, HANDLE, 0.518, TINY, f, (196, 188, 176))
    return finish(im, ts, W3_BLINKS)


def a_dark(d, w):
    w(pad([midi(44), midi(51), midi(56), midi(59)], 27, 0.042), 0.4, 0.5)
    w(bass(midi(29), 12, 0.055), 0.4, 0.5)
    d(piano(midi(42), 5.0, 0.075), 0.6, 0.5)
    for i in range(5): d(softkick(0.10 + 0.02 * i), 3.9 + i * BEAT, 0.62)     # the birth
    d(piano(midi(60), 2.2, 0.12), 7.2, 0.38); d(piano(midi(67), 2.2, 0.11), 7.22, 0.5)
    d(piano(midi(60), 1.8, 0.09), 8.4, 0.66); d(piano(midi(67), 1.8, 0.09), 8.42, 0.7)
    d(piano(midi(61), 1.2, 0.08), 9.0, 0.4)
    for i in range(5): d(softkick(0.13), 9.7 + i * BEAT, 0.5)
    for (t0, nm, dg) in D_HITS:                                              # power chords
        lo = PITCH[dg[0]]
        d(piano(midi(lo), 1.8, 0.145), t0, 0.34)
        d(piano(midi(lo + 7), 1.8, 0.125), t0 + 0.012, 0.46)
        d(piano(midi(lo + 12), 1.4, 0.07), t0 + 0.024, 0.58)
        w(bass(midi(lo - 24), 2.0, 0.05), t0, 0.5)
        d(softkick(0.12), t0 + 0.7, 0.5)
    for b in np.arange(12.0, 19.0, BEAT): d(softkick(0.06), b, 0.5)
    sb.chord(d, w, "Ab", 21.0, dur=4.0, amp=1.15, pan=0.5, roll=0.012)        # the rupture
    d(softkick(0.18), 21.0, 0.5); w(bass(midi(26), 10, 0.06), 21.0, 0.55)
    for i, m in enumerate([67, 65, 63, 61]):
        d(piano(midi(m), 2.0, 0.075 - 0.008 * i), 21.8 + i * 0.6, 0.48)
    w(bass(midi(24), 4.5, 0.02), 24.9, 0.5)                                   # the silence
    sb.chord(d, w, "Am", 26.9, dur=3.2, amp=1.05, pan=0.5)
    d(piano(midi(57), 4.0, 0.09), 27.0, 0.5)


PROGS = {"world": (W1, t_world, a_world, "trailer1_the_world"),
         "lessons": (W2, t_lessons, a_lessons, "trailer2_the_lessons"),
         "dark": (W3, t_dark, a_dark, "trailer3_the_listening_dark")}


def build_audio(dur, afn):
    n = int(dur * SR)
    dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
    wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
    def d(s, at, pan=0.5): add(dL, s * (1 - pan), at); add(dR, s * pan, at)
    def w(s, at, pan=0.5): add(wL, s * (1 - pan), at); add(wR, s * pan, at)
    afn(d, w)
    dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
    wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
    mix = master(dry * 0.92 + wet)
    fi, fo = int(0.25 * SR), int(1.6 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="world")
    ap.add_argument("--preview", type=float, default=None)
    args = ap.parse_args()
    dur, rfn, afn, name = PROGS[args.which]
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if args.preview is not None:
        Image.fromarray(rfn(args.preview)).save(f"tr_{args.which}_prev.png")
        print("preview saved"); return
    n = int(dur * FPS)
    writer = imageio.get_writer(f"{name}_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {name}: {n} frames ...")
    for i in range(n):
        writer.append_data(rfn(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n}")
    writer.close()
    write_wav(f"{name}.wav", build_audio(dur, afn))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", f"{name}_silent.mp4", "-i", f"{name}.wav",
                    "-c:v", "libx264", "-crf", "24", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    f"{name}.mp4"], check=True, capture_output=True)
    print(f"Done -> {name}.mp4")


if __name__ == "__main__":
    main()
