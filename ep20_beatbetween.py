"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 9 — "The Beat Between"
The Silence stops copying tones and takes a voice: the Elder's. It gets very close, and
close is the whole problem. Two notes almost the same do not sound like two notes — they
sound like one note wobbling, and the wobble happens exactly as many times a second as
they are far apart. So the Keeper, with almost no light and no way to fight, wins with
his ears: he holds the Elder's true note against the impostor and listens.

Then he gives away the last of his light to bring the Elder back, and it is not enough.

Hidden lesson: unison and beating — the sum of two sines beats at their difference
frequency, which is how every piano is tuned. ~2:44.

Narration is baked in, as in Ep8. Do not run --story on this one.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
import title_card as tc
import world, planet as pl, staff
import flow as fl, eye
import lighting as lg, foreground as fg
import subs
from observian import say

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 158.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; LAV = [206, 190, 244]
WHITE = [255, 244, 214]; COLD = [150, 176, 214]; STEEL = [96, 118, 156]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "9", "The Beat Between", "the Elder's hollow"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
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
FS = font(45); FSM = font(33); TAG = font(29); NAMEF = font(36); TINY = font(28)


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
def theta_of(ts): return 0.030 * ts
def ground_y(x):
    aa = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(aa) + SINK


KX = 0.30 * W
HOLLOW_X = 0.68 * W                      # where the Elder should be
FAKE_X = 0.78 * W                        # where the voice comes from instead

# ── the physics ──────────────────────────────────────────────────────────────
# Two sines summed beat at their difference frequency. That is the whole episode, and
# it has to be exactly true: the picture pulses at the same rate the ear hears.
F_TRUE = 220.0
STEPS = [(46.0, 6.0), (76.0, 3.0), (88.0, 1.0), (98.0, 0.4)]   # (t, wobbles per second)
UNISON_T = 108.0                         # where he finds the still one
FOUND_T = 118.0
GIVE_T = 132.0


def detune(ts):
    """How far off the impostor is, in Hz, at story time ts."""
    if ts >= UNISON_T:
        return 0.0
    if ts < STEPS[0][0]:
        return 0.0
    d = STEPS[0][1]
    for i, (t, hz) in enumerate(STEPS):
        if ts < t:
            break
        d = hz
        # hold this value, then slide over the four seconds before the next correction —
        # the impostor is not drifting, it is deliberately closing in
        if i + 1 < len(STEPS):
            nt, nhz = STEPS[i + 1]
            if ts > nt - 4.0:
                d = lerp(hz, nhz, smooth(nt - 4.0, nt, ts))
    if ts > UNISON_T - 4.0:
        d = lerp(d, 0.0, smooth(UNISON_T - 4.0, UNISON_T, ts))
    return d


def beat_phase(ts):
    """0..1 brightness of the two lights beating against each other."""
    d = detune(ts)
    if d <= 1e-6:
        return 1.0
    return 0.5 + 0.5 * math.cos(2 * math.pi * d * ts)


ALAN = [
    (1.0,   "He had almost no light left. He went anyway."),
    (20.5,  "The Elder's hollow was dark, and nothing in it was singing."),
    (33.0,  "Then something answered, in a voice he had known all his life."),
    (45.0,  "So he held the Elder's true note up against it, and listened."),
    (59.0,  "Two notes almost the same do not sound like two. "
            "They sound like one note, wobbling."),
    (75.0,  "And the speed of that wobble is exactly how far apart they are."),
    (93.0,  "It got closer. Three wobbles a second. Then one. But it could not land."),
    (107.0, "So he listened for the place where the wobble stopped."),
    (119.0, "Perfectly still. That is what the same sounds like."),
    (133.0, "He gave the last of his light. It was not enough."),
]

STORY_CAPS = [
    (28.4, 31.4, "nothing answered."),
    (146.0, 149.6, "he had nothing left."),
]
STORY_ONLY = {c[2] for c in STORY_CAPS}

BLINKS = [(19.0, 0.26, 0.09, 0.40, 1.0),
          (31.8, 0.34, 0.12, 0.48, 1.0),
          (44.0, 0.20, 0.06, 0.30, 0.8),
          (57.0, 0.12, 0.04, 0.18, 0.45),
          (74.0, 0.16, 0.05, 0.24, 0.6),
          (92.0, 0.14, 0.05, 0.20, 0.5),
          (106.0, 0.28, 0.10, 0.42, 1.0),
          (117.5, 0.22, 0.07, 0.34, 0.9),
          (131.0, 0.24, 0.08, 0.38, 1.0),
          (145.0, 0.40, 0.14, 0.56, 1.0),
          (155.0, 0.85, 0.30, 1.10, 1.0)]

CAM = [
    (0.0,   1.04, 0.32, 0.60), (18.0,  1.16, 0.30, 0.58),
    (21.0,  1.06, 0.52, 0.56), (30.0,  1.22, 0.66, 0.58),   # into the empty hollow
    (33.5,  1.14, 0.74, 0.58), (43.0,  1.24, 0.76, 0.56),   # the voice
    (46.5,  1.10, 0.56, 0.54),                              # both notes in frame
    (60.0,  1.28, 0.60, 0.50), (72.0,  1.16, 0.58, 0.52),   # the wobble, close
    (78.0,  1.24, 0.62, 0.52), (90.0,  1.14, 0.60, 0.54),
    (100.0, 1.26, 0.64, 0.52),
    (109.0, 1.06, 0.50, 0.52), (116.0, 1.20, 0.66, 0.58),   # the still one
    (120.0, 1.16, 0.68, 0.60), (130.0, 1.08, 0.48, 0.58),
    (134.0, 1.22, 0.34, 0.60), (144.0, 1.12, 0.32, 0.60),   # the giving
    (150.0, 1.02, 0.42, 0.54), (SDUR, 1.00, 0.46, 0.50),
]
CAM.sort(key=lambda r: r[0])


def cam_at(ts):
    z, cx, cy = CAM[0][1], CAM[0][2], CAM[0][3]
    for i in range(len(CAM) - 1):
        t0, z0, x0, y0 = CAM[i]; t1, z1, x1, y1 = CAM[i + 1]
        if t0 <= ts <= t1:
            u = smooth(t0, t1, ts)
            z = lerp(z0, z1, u); cx = lerp(x0, x1, u); cy = lerp(y0, y1, u)
            break
    else:
        if ts > CAM[-1][0]:
            z, cx, cy = CAM[-1][1], CAM[-1][2], CAM[-1][3]
    z *= 1.0 + 0.006 * math.sin(ts * 0.29)
    cx += 0.004 * math.sin(ts * 0.21 + 0.6)
    cy += 0.003 * math.sin(ts * 0.17)
    return z, cx, cy


def cam_box(z, cx, cy):
    bw, bh = W / z, H / z
    x0 = min(max(cx * W - bw / 2, 0.0), W - bw)
    y0 = min(max(cy * H - bh / 2, 0.0), H - bh)
    return x0, y0, bw, bh


def to_screen(x, y, box):
    x0, y0, bw, bh = box
    return (x - x0) * (W / bw), (y - y0) * (H / bh)


_SIGS = None
_ENV = None
ENV_HZ = 100.0


def alan_sigs():
    global _SIGS
    if _SIGS is None:
        import narrate as N
        _SIGS = [(t, N.voiced(s, "alan")) for (t, s) in ALAN]
    return _SIGS


def alan_env(ts):
    global _ENV
    if _ENV is None:
        n = int(SDUR * ENV_HZ) + 4
        e = np.zeros(n, np.float32)
        step = int(SR / ENV_HZ)
        for (t, sig) in alan_sigs():
            mag = np.abs(sig); k = len(mag) // step
            if k < 1: continue
            block = mag[:k * step].reshape(k, step).max(1)
            i0 = int(t * ENV_HZ); j = min(n, i0 + k)
            e[i0:j] = np.maximum(e[i0:j], block[:j - i0])
        for i in range(1, n):
            e[i] = max(e[i], e[i - 1] * 0.90)
        _ENV = e / (e.max() + 1e-9)
    i = int(clamp(ts, 0, SDUR - 0.02) * ENV_HZ)
    return float(_ENV[min(i, len(_ENV) - 1)])


_CAPS = None


def CAPS_():
    global _CAPS
    if _CAPS is None:
        _CAPS = subs.build(ALAN, alan_sigs(), SR, extra=STORY_CAPS)
    return _CAPS


def caption_on(ts):
    v = 0.0
    for (s, e, _t) in CAPS_():
        if s <= ts <= e:
            v = max(v, float(np.interp(ts, [s, s + 0.5, e - 0.5, e], [0, 1, 1, 0])))
    return v


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS_():
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


def draw_meter(im, ts):
    """How fast it is wobbling, in words. The lesson, counted."""
    if not (48.0 <= ts <= UNISON_T + 8.0):
        return
    d = detune(ts)
    f = smooth(48.0, 50.0, ts) * (1 - smooth(UNISON_T + 6.0, UNISON_T + 8.0, ts))
    if f < 0.03:
        return
    txt = "perfectly still" if d < 0.02 else (
        f"{d:.1f} wobbles a second" if d < 1.0 else f"{d:.0f} wobbles a second")
    col = WARM if d < 0.02 else COLD
    dd = ImageDraw.Draw(im, "RGBA")
    bb = dd.textbbox((0, 0), txt, font=NAMEF); xx = (W - (bb[2] - bb[0])) // 2
    yy = int(0.365 * H)                            # clear of the solfege labels above
    dd.text((xx + 2, yy + 2), txt, font=NAMEF, fill=(0, 0, 0, int(150 * f)))
    dd.text((xx, yy), txt, font=NAMEF, fill=(col[0], col[1], col[2], int(238 * f)))


def end_card(im, ts):
    if ts < 151.0: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [151.0, 151.9, 154.4, 156.4], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.455), ("the more you observe.", 0.492)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "to be continued"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.552 * H)), tg, font=TAG, fill=(202, 194, 182, int(190 * fade)))


def story(ts):
    scene = "night" if ts < 128 else "fading_edge"
    a = pl.build_sky(scene).copy()
    base, mask = pl.planet_base(scene)
    a[mask] = base[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta_of(ts), scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)
    a *= 0.88                                          # this is the darkest episode yet

    voice = alan_env(ts)
    if voice > 0.02:
        a *= (1.0 + 0.05 * voice)

    # ── the Keeper, nearly out ──────────────────────────────────────────────────
    walk = ts < 18.0
    spark = 0.30 * (1 - 0.92 * smooth(GIVE_T + 2.0, GIVE_T + 7.0, ts))
    lift = max(0.5 * smooth(45.0, 46.4, ts) * (1 - smooth(106, 108, ts)),
               0.9 * smooth(GIVE_T, GIVE_T + 1.6, ts) * (1 - smooth(GIVE_T + 8, GIVE_T + 10, ts)))
    kx = lerp(KX - 0.10 * W, KX, smooth(0, 18, ts))
    ky = ground_y(kx)
    kspr, kfoot, kdx, kdy = character(146, "walk" if walk else "stand", ts, 1,
                                      lift=clamp(lift), lean=(0.03 if walk else 0) + fl.idle_sway(ts))
    LX, LY = kx + kdx, ky + kdy
    glow(a, LX, LY, 13, GOLD, spark)
    lights = [(LX, LY, 250, GOLD, 0.85 * spark)]

    # ── the two notes: his true one, and the one pretending ─────────────────────
    both = smooth(45.0, 46.5, ts) * (1 - smooth(FOUND_T + 4, FOUND_T + 7, ts))
    ph = beat_phase(ts)
    if both > 0.02:
        # they beat against each other: in phase they swell, out of phase they cancel.
        tx, ty = 0.52 * W, ground_y(0.52 * W) - 0.16 * H
        fxp, fyp = FAKE_X, ground_y(FAKE_X) - 0.16 * H
        amp_t = both * (0.42 + 0.58 * ph)
        amp_f = both * (0.42 + 0.58 * ph)
        glow(a, tx, ty, 14 + 10 * ph, WARM, 0.85 * amp_t)
        glow(a, tx, ty, 46, WARM, 0.16 * amp_t)
        glow(a, fxp, fyp, 14 + 10 * ph, COLD, 0.85 * amp_f)
        glow(a, fxp, fyp, 46, COLD, 0.16 * amp_f)
        lights += [(tx, ty, 320, WARM, 0.7 * amp_t), (fxp, fyp, 300, COLD, 0.6 * amp_f)]
        # the sum, between them: this is what the ear actually hears
        mx = (tx + fxp) * 0.5
        glow(a, mx, ty - 0.05 * H, 20 + 26 * ph, WHITE, 0.30 * both * ph)

    # ── the impostor ────────────────────────────────────────────────────────────
    fake = smooth(32.0, 34.0, ts) * (1 - smooth(FOUND_T, FOUND_T + 3, ts))
    fx_x = FAKE_X; fy_y = ground_y(fx_x)
    if fake > 0.02:
        darken(a, fx_x, fy_y - 0.035 * H, 60, 0.80 * fake)
        glow(a, fx_x, fy_y - 0.035 * H, 12, STEEL, 0.34 * fake)

    # ── the real Elder, found ───────────────────────────────────────────────────
    found = smooth(FOUND_T, FOUND_T + 2.5, ts)
    ex, ey = HOLLOW_X, ground_y(HOLLOW_X)
    if found > 0.02:
        lit = found * (0.30 + 0.55 * smooth(GIVE_T, GIVE_T + 3, ts)
                       * (1 - smooth(GIVE_T + 6, GIVE_T + 9, ts)))
        glow(a, ex, ey - 0.03 * H, 14, LAV, 0.55 * lit)
        glow(a, ex, ey - 0.03 * H, 40, LAV, 0.13 * lit)
        if lit > 0.05:
            lights.append((ex, ey - 0.03 * H, 260, LAV, 0.55 * lit))

    # the gift crossing the ground, and failing to catch
    give = smooth(GIVE_T, GIVE_T + 3.4, ts) * (1 - smooth(GIVE_T + 7, GIVE_T + 9, ts))
    if give > 0.02:
        for i in range(14):
            u = (i / 13.0) * smooth(GIVE_T, GIVE_T + 3.4, ts)
            gx = lerp(LX, ex, u); gy = lerp(LY, ey - 0.03 * H, u) - 0.05 * H * math.sin(math.pi * u)
            glow(a, gx, gy, 6, GOLD, 0.34 * give * (1 - u * 0.5))

    lg.spill(a, mask, lights, amount=0.55)
    lg.cast(a, kx, ky, lights, ground_y, length=2.0, amount=0.38)
    fg.motes(a, ts, cam_at(ts), glow, WARM, n=4)

    vis = smooth(1.0, 4.5, ts)
    modes = ["full"] * 8
    glows = [0.13] * 8
    if both > 0.02:                                   # unison: one slot, two voices
        glows[5] = max(glows[5], 0.30 + 0.45 * ph * both)
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    kspr = lg.rim(kspr, kx, ky, lights, width=5, gain=1.05)
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(ky - kfoot)), kspr)
    if fake > 0.02:
        sspr, sfoot, _, _ = character(176, "stand", ts, -1, lean=0.02 * math.sin(ts * 0.5))
        sspr = lg.rim(sspr, fx_x, fy_y, lights, width=4, gain=0.5)
        al = sspr.getchannel("A").point(lambda v: int(v * clamp(fake)))
        sspr = sspr.copy(); sspr.putalpha(al)
        im.paste(sspr, (int(fx_x - sspr.size[0] / 2), int(fy_y - sfoot)), sspr)
    staff.draw(im, vis, modes, glows)

    z, ccx, ccy = cam_at(ts)
    box = cam_box(z, ccx, ccy)
    if z > 1.001:
        x0, y0, bw, bh = box
        im = im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + bw, y0 + bh))
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    fg.draw(im, ts, (z, ccx, ccy), strength=1.0)
    draw_meter(im, ts)
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im.convert("RGB"), np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.44)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    eye.apply_lids(frame, eye.blink_amount(ts, BLINKS))
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


def tone(freq, dur, amp, fade=0.15):
    """One steady voice at a fixed pitch."""
    t = np.linspace(0, dur, int(dur * SR), False, dtype=np.float32)
    env = np.minimum(1.0, t / fade) * np.minimum(1.0, (dur - t) / fade)
    ph = 2 * np.pi * freq * t
    return ((np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph))
            * env * amp).astype(np.float32)


def glide(f_of_t, t0, t1, amp, fade=0.4):
    """A voice whose pitch changes, built by integrating phase.

    Chunking this into fixed segments would put an attack envelope every chunk and add
    an amplitude wobble of its own — which in an episode *about* amplitude wobble would
    be a lie the audience could hear. Integrating the phase keeps it continuous.
    """
    n = int((t1 - t0) * SR)
    tt = np.linspace(t0, t1, n, False, dtype=np.float64)
    ctrl_t = np.arange(t0, t1 + 0.05, 0.02)                  # detune sampled at 50 Hz
    ctrl_f = np.array([f_of_t(x) for x in ctrl_t], np.float64)
    f = np.interp(tt, ctrl_t, ctrl_f)
    ph = 2 * np.pi * np.cumsum(f) / SR
    local = tt - t0
    env = np.minimum(1.0, local / fade) * np.minimum(1.0, (t1 - t0 - local) / fade)
    return ((np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph))
            * env * amp).astype(np.float32)


def build_audio(bed_only=False):
    import narrate as N
    n = int(DUR * SR)
    dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
    wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
    A = TITLE_DUR
    def d(s, at, pan=0.5): add(dL, s * (1 - pan), A + at); add(dR, s * pan, A + at)
    def w(s, at, pan=0.5): add(wL, s * (1 - pan), A + at); add(wR, s * pan, A + at)
    K = dict(register=0, pan=0.36); E = dict(register=-12, pan=0.62); SH = dict(register=-12, pan=0.70)

    w(pad([midi(45), midi(52), midi(57)], 30, 0.030), 1, 0.5)
    w(bass(midi(33), 20, 0.038), 1, 0.5)
    for t in np.arange(2.0, 17.0, BEAT * 1.5):        # his footsteps, tired, off the beat
        d(softkick(0.055), t + 0.11, 0.42)

    say(d, "who are you", 28.0, style="calm", **K)
    w(bass(midi(31), 8, 0.030), 24.0, 0.5)

    # the impostor, in the Elder's voice
    say(d, "i remember you", 40.0, style="calm", **SH)
    say(d, "no", 56.0, style="fear", **K)

    # ── the two tones. the beat rate is the difference, and it is real ──────────
    HOLD_T0, HOLD_T1 = 45.5, FOUND_T + 3.0
    d(glide(lambda x: F_TRUE, HOLD_T0, HOLD_T1, 0.085), HOLD_T0, 0.40)          # his true note
    d(glide(lambda x: F_TRUE + detune(x), HOLD_T0, HOLD_T1, 0.085), HOLD_T0, 0.60)
    w(pad([F_TRUE * 0.5], 20, 0.020), 60.0, 0.5)

    say(d, "the same", 90.0, style="urgent", **SH)
    say(d, "i cannot", 104.0, style="fear", **SH)
    say(d, "i am here", 122.0, style="whisper", **E)

    # the real Elder: the same note, and nothing moving in it
    d(tone(F_TRUE, 16.0, 0.075), FOUND_T, 0.56)
    w(pad([midi(45), midi(57), midi(64)], 12, 0.032), FOUND_T, 0.5)

    say(d, "i give you this", 140.0, style="whisper", **K)
    for i, m in enumerate([60, 64, 67]):
        d(piano(midi(m), 5.0, 0.070), GIVE_T + 0.4 + i * 0.22, 0.42)
    w(bass(midi(29), 10, 0.034), GIVE_T + 3.0, 0.5)
    say(d, "i cannot", 152.0, style="whisper", **E)
    d(piano(midi(48), 7.0, 0.055), 150.0, 0.46)

    dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
    wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
    mix = master(dry * 0.92 + wet)
    fi, fo = int(0.6 * SR), int(4 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    if bed_only:
        return mix
    items = [(A + t, sig) for (t, sig) in alan_sigs()]
    return N.lay(mix, items, level=1.22, target_db=13.0, keep=0.14)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, default=None)
    ap.add_argument("--audio-only", action="store_true")
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save(f"ep20_prev_{a.preview:.0f}.png")
        print("preview saved"); return
    if a.audio_only:
        write_wav("ep20.wav", build_audio()); print("audio -> ep20.wav"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep20_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep20.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep20_silent.mp4", "-i", "ep20.wav",
                    "-c:v", "libx264", "-crf", "27", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "ch2_ep9_the_beat_between.mp4"], check=True, capture_output=True)
    print("Done -> ch2_ep9_the_beat_between.mp4")


if __name__ == "__main__":
    main()
