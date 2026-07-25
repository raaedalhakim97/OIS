"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 2 — "The Cold Trail"
The two keepers hunt the fallen note. The Elder teaches the method: call, then count
the silence — the longer the answer takes, the farther it lies. They cross out of the
Home Fields into the Fading Edge, calling as they go, and each answer comes back
sooner. Then the answer comes back BEFORE the call is finished — and they understand
it was never an echo. They find La lying a half step below itself, held down in the
dark. And the dark has a shape: a keeper's silhouette carrying a hole where its
lantern should be. It is learning to sing. ~2:20.

Hidden lesson: echo delay = distance (how sound travels), and flat = fallen.
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
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "2", "The Cold Trail", "the Fading Edge"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]
FELL = 5                                        # La, still lying a half step low


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(46); FSM = font(33); TAG = font(29)


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


for s in ("night", "fading_edge", "winter"): pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "night"), (30, "fading_edge"), (76, "winter")]

# they travel; the world holds still when they stop to listen, and at the arrival
TURNS = [(1, 10), (24, 31), (38, 44), (50, 57)]
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

BLINKS = [(22.5, 0.30, 0.10, 0.45, 1.0),
          (35.5, 0.26, 0.08, 0.40, 1.0),
          (58.5, 0.30, 0.10, 0.45, 1.0),
          (68.0, 0.14, 0.04, 0.22, 0.5),     # the flinch: it was never an echo
          (94.0, 0.16, 0.05, 0.26, 0.6),     # the flinch: the dark has a shape
          (125.5, 0.85, 0.30, 1.20, 1.0)]    # the slow blink out

# --- the hunt: (call time, answer time) — the delay shrinks each time ---
CALLS = [(11.0, 15.4), (32.0, 35.0), (44.5, 46.3), (65.5, 65.6)]
RIMX = 0.955 * W
_srim = math.asin(clamp((RIMX - CX) / R, -1, 1))
RIMY = CY - R * math.cos(_srim)

# where the keepers stand
AK, AE = -0.075, 0.14
def ball_feet(ang): return CX + R * math.sin(ang), CY - R * math.cos(ang) + SINK
KFX, KFY = ball_feet(AK)
EFX, EFY = ball_feet(AE)
LA_POS = (0.845 * W, FEET - 0.045 * H)          # the fallen note, ahead on the ground
HOL_POS = (0.905 * W, FEET - 0.055 * H)         # the shape beside it

# the Hollow sings the First Song — flattened, slow, wrong
HSONG = [(106.0, 0), (107.3, 1), (108.6, 2), (110.1, 3)]

CAPS = [
    (1.5, 6.5, "they followed a sound\nthat should not exist."),
    (7.5, 12.0, "the Elder taught him\nhow to hunt a note."),
    (13.5, 18.0, "call — then count the silence."),
    (18.8, 22.2, "the longer the answer takes,\nthe farther it lies."),
    (25.0, 30.0, "so they walked to where\nthe grass forgets to grow."),
    (33.0, 36.0, "closer."),
    (38.5, 43.0, "the ground began\nto forget its colour."),
    (46.5, 49.5, "closer."),
    (51.0, 56.5, "and then the answer came\nbefore he finished asking."),
    (60.5, 64.5, "no delay at all."),
    (66.5, 72.0, "it was not an echo.\nit never had been."),
    (74.5, 79.5, "there — lying a half step\nbelow itself."),
    (81.0, 85.0, "i hear you."),
    (86.5, 92.0, "something was\nholding it down."),
    (97.5, 103.0, "and the dark had a shape."),
    (105.0, 112.0, "it wore a keeper's shadow —\nand carried a hole\nwhere its light should be."),
    (113.5, 117.5, "danger."),
    (118.5, 121.5, "wait."),
    (122.0, 125.0, "it wants us to run."),
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
            fade = np.interp(ts, [s, s + 0.6, e - 0.6, e], [0, 1, 1, 0])
            lines = txt.split("\n")
            total = sum(int(d.textbbox((0, 0), ln, font=FS)[3] * 1.5) for ln in lines)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=FS); xx = (W - (bb[2] - bb[0])) // 2
                d.text((xx + 2, yy + 2), ln, font=FS, fill=(0, 0, 0, int(150 * fade)))
                d.text((xx, yy), ln, font=FS, fill=(238, 234, 226, int(240 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)


def end_card(im, ts):
    if ts < 126.5: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [126.5, 128.0, 131.5, 133.5], [0, 1, 1, 0])
    for (ln, f, yy) in [("the more you know,", FSM, 0.455), ("the more you observe.", FSM, 0.492)]:
        bb = d.textbbox((0, 0), ln, font=f); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=f, fill=(238, 232, 220, int(235 * fade)))
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

    # ---- the dark ahead, thickening as they close in ----
    dk = 0.30 + 0.70 * smooth(30, 96, ts)
    darken(a, RIMX, RIMY, 80 + 130 * dk, 0.5 * dk)
    a *= (1 - 0.12 * dk)

    # ---- the cold answers sweeping in from the horizon ----
    for (ct, at) in CALLS:
        if ct <= ts <= at + 1.4:
            u = clamp((ts - ct) / max(0.12, at - ct))          # the answer travelling in
            ax = lerp(RIMX, 0.62 * W, u); ay = lerp(RIMY, SY + 4.2 * LG, u)
            glow(a, ax, ay, 6 + 5 * u, COLD, 0.30 * (0.35 + 0.65 * u))
        if at <= ts <= at + 1.6:                               # its arrival
            al = 1 - (ts - at) / 1.6
            glow(a, 0.62 * W, SY + 4.2 * LG, 16, COLD, 0.40 * al)

    # ---- the two keepers, walking the trail together ----
    kwalk = walking(ts)
    klift = (0.9 * smooth(10.2, 11.0, ts) * (1 - smooth(15.8, 17.0, ts))
             + 0.9 * smooth(31.2, 32.0, ts) * (1 - smooth(35.4, 36.4, ts))
             + 0.9 * smooth(43.7, 44.5, ts) * (1 - smooth(46.8, 48.0, ts))
             + 0.9 * smooth(64.7, 65.5, ts) * (1 - smooth(67, 68.5, ts))
             + 0.55 * smooth(80, 81, ts) * (1 - smooth(85.5, 87, ts))          # i hear you
             + 0.8 * smooth(112.8, 113.5, ts) * (1 - smooth(118, 119.5, ts)))  # danger
    kx = lerp(CX, KFX, smooth(58, 62, ts)); ky = lerp(FEET, KFY, smooth(58, 62, ts))
    kspr, kfoot, kdx, kdy = character(140, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(klift), lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts))
    glow(a, kx + kdx, ky + kdy, 22, GOLD, 0.9 * (0.9 + 0.1 * math.sin(ts * 2.6)))

    ex = lerp(0.335 * W, EFX, smooth(58, 62, ts)); ey = lerp(FEET - 6, EFY, smooth(58, 62, ts))
    elift = (0.6 * smooth(7.6, 8.6, ts) * (1 - smooth(12, 13.5, ts))            # listen
             + 0.75 * smooth(117.8, 118.6, ts) * (1 - smooth(124, 125.5, ts)))  # wait
    ewalk = kwalk
    espr, efoot, edx, edy = character(136, "walk" if ewalk else "stand", ts, 1,
                                      lift=clamp(elift), lean=(0.03 if ewalk else 0.0) + fl.idle_sway(ts * 0.9 + 1))
    glow(a, ex + edx, ey + edy, 21, WARM, 0.86 * (0.9 + 0.1 * math.sin(ts * 2.4 + 1)))

    # ---- La: found, lying a half step below itself, held down ----
    lseen = smooth(72, 76, ts)
    if lseen > 0.02:
        lx, ly = LA_POS
        ly += fl.bob(ts, 3.0, f1=0.35, f2=0.8)
        weak = 0.36 + 0.26 * abs(math.sin(ts * 0.8))
        weak *= (1 - 0.45 * smooth(104, 124, ts))                 # it dims as the shape works
        darken(a, lx, ly, 58, 0.42 * lseen)
        glow(a, lx, ly, 12, COLD, lseen * weak)
        glow(a, lx, ly, 30, COLD, lseen * weak * 0.20)

    # ---- and the dark had a shape: a keeper's shadow with a hole for a lantern ----
    hseen = smooth(95.5, 100.5, ts)
    hspr = None
    if hseen > 0.02:
        hx, hy = HOL_POS
        hx -= 26 * smooth(122, 132, ts)                           # it steps toward them
        hy += fl.bob(ts, 2.2, f1=0.3, f2=0.7)
        darken(a, hx + 0.055 * W, hy - 0.02 * H, 46, 0.85 * hseen)   # the void it carries
        glow(a, hx + 0.055 * W, hy - 0.02 * H, 13, [70, 92, 152], 0.38 * hseen)
        darken(a, hx, hy - 0.03 * H, 92, 0.34 * hseen)
        hspr, hfoot, _, _ = character(150, "stand", 0.0, -1, lean=0.02 * math.sin(ts * 0.6))
        if hseen < 0.995:
            al = hspr.getchannel("A").point(lambda v: int(v * hseen)); hspr = hspr.copy(); hspr.putalpha(al)
        HOLD = (hx, hy, hfoot)

    # ---- the staff: La still fallen, dimming; the Hollow's song flickers it ----
    vis = smooth(1.0, 5.0, ts)
    modes = ["full"] * 8; glows = [0.32] * 8
    modes[FELL] = "fallen"
    glows[FELL] = 0.26 + 0.34 * abs(math.sin(ts * 0.85))
    for (ct, at) in CALLS:                                        # his call lights Do
        if ct <= ts <= ct + 1.3: glows[0] = max(glows[0], 1.0 - (ts - ct) / 1.3)
        if at <= ts <= at + 1.4: glows[FELL] = max(glows[FELL], 0.9 * (1 - (ts - at) / 1.4))
    for (t0, i) in HSONG:                                          # it sings, and gets it wrong
        if t0 <= ts <= t0 + 1.5:
            glows[i] = max(glows[i], 0.95 * (1 - (ts - t0) / 1.5))
    if ts > 104:
        for i in range(8):
            glows[i] *= 1 - 0.35 * smooth(104, 122, ts) * (0.5 + 0.5 * math.sin(ts * 4 + i))
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(espr, (int(ex - espr.size[0] / 2), int(ey - efoot)), espr)
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(ky - kfoot)), kspr)
    if hspr is not None:
        hx, hy, hfoot = HOLD
        im.paste(hspr, (int(hx - hspr.size[0] / 2), int(hy - hfoot)), hspr)
    staff.draw(im, vis, modes, glows)

    d = ImageDraw.Draw(im, "RGBA")
    for (ct, at) in CALLS:
        ring(d, SLOT[0][0], SLOT[0][1], ct, ts, (255, 214, 150), rmax=30)
        ring(d, 0.62 * W, SY + 4.2 * LG, at, ts, (170, 192, 226), rmax=70, dur=1.3)
    if lseen > 0.02: ring(d, LA_POS[0], LA_POS[1], 74.0, ts, (170, 192, 226), rmax=52)
    for (t0, i) in HSONG: ring(d, SLOT[i][0], SLOT[i][1], t0, ts, (120, 146, 190), rmax=30)
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
    K = dict(register=0, pan=0.42); E = dict(register=-12, pan=0.58)

    # a cold, thin bed that loses its warmth as they cross out of the Home Fields
    w(pad([midi(45), midi(52), midi(57), midi(60)], 30, 0.04), 1, 0.5)      # Am
    w(pad([midi(44), midi(51), midi(56), midi(59)], 34, 0.038), 30, 0.5)    # a semitone colder
    w(pad([midi(43), midi(50), midi(56)], 30, 0.036), 74, 0.5)              # thinner still
    for (s, e) in TURNS:
        for t in np.arange(s + 0.5, e - 0.2, 1.45):
            d(softkick(0.075), t, 0.44); d(softkick(0.055), t + 0.72, 0.58)  # two sets of steps

    say(d, "listen", 8.0, style="calm", **E)

    # the hunt: each call is Do; each answer is the fallen note, arriving sooner
    for k, (ct, at) in enumerate(CALLS):
        d(piano(midi(60), 2.6, 0.145), ct, 0.42)
        amp = 0.055 + 0.03 * k
        w(piano(midi(68), 3.0, amp), at, 0.66)                   # A-flat: the fallen answer
        d(piano(midi(68), 2.4, amp * 0.8), at + 0.02, 0.60)
        if k == 3:                                               # it answers over his call
            d(piano(midi(68), 3.2, 0.11), ct - 0.35, 0.58)
    w(bass(midi(33), 8, 0.05), 51.0, 0.5)
    say(d, "i am afraid", 53.0, style="fear", register=0, pan=0.42)
    say(d, "we are connected", 56.0, style="confident", register=-12, pan=0.5)

    # arrival: La answers weakly, from the ground
    w(bass(midi(32), 10, 0.055), 66.0, 0.5)
    say(d, "i hear you", 81.0, style="calm", **K)
    d(piano(midi(68), 4.0, 0.075), 83.2, 0.68)                   # its weak reply
    d(piano(midi(68), 3.0, 0.05), 88.0, 0.68)
    w(bass(midi(30), 10, 0.05), 87.0, 0.5)

    # the shape: it sings the First Song, every note flattened
    d(softkick(0.11), 96.0, 0.5); w(bass(midi(29), 12, 0.055), 96.0, 0.5)
    for (t0, i) in HSONG:
        d(piano(midi(PITCH[i] - 1), 2.6, 0.10), t0, 0.64)        # wrong by a half step, all of it
        w(piano(midi(PITCH[i] - 13), 3.0, 0.04), t0 + 0.05, 0.68)
    d(piano(midi(42), 5.0, 0.075), 110.5, 0.5)                   # the not-a-note underneath

    say(d, "danger", 113.5, style="fear", register=12, pan=0.40)
    say(d, "wait", 118.5, style="calm", **E)
    d(softkick(0.085), 122.5, 0.62); d(softkick(0.09), 124.2, 0.60)   # it steps closer
    w(bass(midi(29), 9, 0.05), 122.5, 0.5)
    d(piano(midi(68), 6.0, 0.10), 126.5, 0.56)                   # the fallen note, still ringing

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
        Image.fromarray(render(a.preview)).save("ep12_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep12_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep12.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep12_silent.mp4", "-i", "ep12.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep2_the_cold_trail.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep2_the_cold_trail.mp4")


if __name__ == "__main__":
    main()
