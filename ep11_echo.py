"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 1 — "The Echo That Came Back"
Chapter I ended with the whole scale home and the First Song ringing. Tonight the
Keeper sings it to the horizon as he always does — and the horizon sings it back
with one note fallen. He questions the dark; the dark answers the only way it can:
with a rest. An Elder keeper comes, names the wound — "the song is broken" — and the
two set out toward the horizon. Behind them the flattened note keeps ringing, and
something out there is listening back.

Spoken entirely in Observian (captions carry meaning). Scene changes are blinks of
the Observer's eye. ~2:16.
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
SDUR = 130.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COLD = [150, 176, 214]
VOID = [40, 44, 66]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "1", "The Echo That Came Back", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]
FELL = 5                                    # La is the note that falls (A -> A-flat)
FALL_T = 21.5


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(46); FSM = font(33); BIG = font(62); TAG = font(30)


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


SCENES = ["night", "dusk", "night"]
for s in ("night", "dusk"): pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "night"), (44, "dusk"), (96, "night")]

# the world turns while they walk; it holds still through the whole confrontation
TURNS = [(0, 7), (110, 130)]
ROT = 0.13
def _rate(u):
    r = 0.0
    for (s, e) in TURNS:
        r = max(r, smooth(s - 1.2, s + 0.3, u) * (1 - smooth(e - 0.3, e + 1.2, u)))
    return r
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))
def walking(ts): return any(s - 0.4 < ts < e + 0.4 for (s, e) in TURNS)

# the Observer blinks between scenes (and flinches when the dark answers)
BLINKS = [(17.0, 0.30, 0.10, 0.45, 1.0),      # into the echo
          (41.0, 0.30, 0.10, 0.45, 1.0),      # into the dark
          (52.0, 0.14, 0.04, 0.22, 0.55),     # the eye flinches
          (65.0, 0.30, 0.10, 0.45, 1.0),      # the Elder comes
          (105.0, 0.34, 0.12, 0.50, 1.0),     # they set out
          (120.5, 0.90, 0.35, 1.30, 1.0)]     # the slow blink into Chapter II

# the two keepers, both on the ground
AK, AE = -0.055, 0.235
def ball_feet(ang): return CX + R * math.sin(ang), CY - R * math.cos(ang) + SINK
KFX, KFY = ball_feet(AK)
EFX, EFY = ball_feet(AE)

SUNG = [(9.0 + i * 0.78, i) for i in range(4)]                 # Do Re Mi Sol, sung out
ECHO = [(19.0 + i * 0.86, i) for i in range(4)]                # returned... wrong
BROKEN = [(74.0 + i * 0.72, i) for i in [0, 1, 2, 3]]          # "the song is broken"

CAPS = [
    (1.5, 6.0, "the whole scale was home.\nthe world had a song."),
    (7.0, 12.0, "and every night the Keeper\nsang it to the horizon."),
    (12.6, 16.4, "the song has begun."),
    (18.6, 23.0, "…the song has begun."),
    (23.6, 28.0, "but one note\ncame back fallen."),
    (29.0, 33.5, "something is wrong."),
    (35.0, 39.5, "he had never asked\nthe horizon a question before."),
    (42.5, 46.5, "who are you?"),
    (48.0, 52.5, "nothing answered.\nand the nothing was the answer."),
    (54.0, 58.0, "who are you?!"),
    (59.0, 64.0, "something answered.\nit was not a note."),
    (67.0, 71.0, "i hear you."),
    (72.0, 76.5, "listen."),
    (77.5, 81.5, "the song is broken."),
    (82.5, 88.0, "one sound had changed —\nand with it, everything."),
    (89.5, 93.0, "what now?"),
    (94.5, 98.5, "come with me."),
    (99.5, 104.0, "we are connected."),
    (107.0, 111.5, "so they went\ntoward the horizon —"),
    (112.5, 117.0, "to find where\nthe fallen note had gone."),
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
    """CHAPTER II — THE LISTENING DARK, after the slow blink."""
    if ts < 121.0: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [121.0, 122.5, 127.5, 129.5], [0, 1, 1, 0])
    for (ln, f, yy) in [("CHAPTER II", TAG, 0.405), ("THE LISTENING DARK", BIG, 0.445)]:
        bb = d.textbbox((0, 0), ln, font=f); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=f, fill=(238, 232, 220, int(235 * fade)))
    tagline = "the more you know, the more you observe."
    bb = d.textbbox((0, 0), tagline, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.535 * H)), tagline, font=FSM, fill=(206, 198, 186, int(200 * fade)))


def ring(d, cx, cy, t0, ts, col, rmax=46):
    q = ts - t0
    if 0 <= q <= 0.9:
        u = q / 0.9; r = 8 + rmax * fl.ease_out(u); al = int(200 * (1 - u) ** 1.3)
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

    # ---- the dark gathering at the far rim, and reaching for the staff ----
    dk = smooth(19, 30, ts) * 0.35 + smooth(44, 62, ts) * 0.65
    dk *= (1 - 0.55 * smooth(96, 108, ts))
    if dk > 0.02:
        srim = math.asin(clamp((0.955 * W - CX) / R, -1, 1))
        rimx = 0.955 * W; rimy = CY - R * math.cos(srim)
        darken(a, rimx, rimy, 70 + 90 * dk, 0.55 * dk)
        a *= (1 - 0.13 * dk)
        for i in range(4):                                  # slow tendrils
            u = smooth(50, 62, ts)
            tx = lerp(rimx, 0.80 * W, u); tyy = lerp(rimy, SY + 5.0 * LG, u)
            ph = ts * 0.7 + i * 1.6
            darken(a, tx + 26 * math.sin(ph), tyy + 34 * math.cos(ph * 0.8), 44, 0.34 * u * dk)
        glow(a, rimx, rimy, 5, COLD, dk * 0.22 * (0.5 + 0.5 * math.sin(ts * 1.6)))

    # ---- the Keeper ----
    kwalk = walking(ts)
    klift = (0.85 * smooth(8.2, 9.2, ts) * (1 - smooth(13.5, 15.0, ts))       # singing out
             + 0.5 * smooth(28.5, 29.5, ts) * (1 - smooth(33, 34.5, ts))      # something is wrong
             + 0.9 * smooth(42, 43, ts) * (1 - smooth(47, 48.5, ts))          # who are you
             + 0.95 * smooth(53.5, 54.3, ts) * (1 - smooth(58, 59.5, ts))     # who are you!
             - 0.45 * smooth(60, 62, ts) * (1 - smooth(66, 68, ts))           # recoils
             + 0.6 * smooth(89, 90, ts) * (1 - smooth(97, 99, ts)))           # what now
    kx = lerp(CX, KFX, smooth(6, 9, ts))
    ky = lerp(FEET, KFY, smooth(6, 9, ts))
    kspr, kfoot, kdx, kdy = character(140, "walk" if kwalk else "stand", ts, 1,
                                      lift=clamp(klift, -0.5, 1.0),
                                      lean=(0.03 if kwalk else 0.0) + fl.idle_sway(ts))
    glow(a, kx + kdx, ky + kdy, 22, GOLD, 0.9 * (0.9 + 0.1 * math.sin(ts * 2.6)))

    # ---- the Elder keeper: rises over the horizon at the blink, then stands with him ----
    eseen = smooth(66, 69, ts)
    ex = lerp(1.02 * W, EFX, smooth(66, 73, ts))
    ey = lerp(FEET + 0.02 * H, EFY, smooth(66, 73, ts))
    ewalk = ts < 73 or ts > 110
    elift = (0.55 * smooth(72, 73.5, ts) * (1 - smooth(81, 83, ts))           # listen / naming
             + 0.7 * smooth(94, 95, ts) * (1 - smooth(104, 106, ts)))         # come with me
    espr, efoot, edx, edy = character(136, "walk" if ewalk else "stand", ts, -1,
                                      lift=clamp(elift), lean=fl.idle_sway(ts * 0.9 + 1))
    if eseen > 0.02:
        glow(a, ex + edx, ey + edy, 21, WARM, eseen * 0.86 * (0.9 + 0.1 * math.sin(ts * 2.4 + 1)))

    # ---- the bond: we are connected ----
    bond = smooth(99.5, 102, ts) * (1 - smooth(112, 116, ts))
    if bond > 0.02:
        for i in range(14):
            u = i / 13.0
            glow(a, lerp(kx + kdx, ex + edx, u), lerp(ky + kdy, ey + edy, u) - 0.02 * H * math.sin(math.pi * u),
                 4, GOLD, bond * 0.38 * (0.6 + 0.4 * math.sin(ts * 3 + i)))

    # ---- the staff: the world's song, and the note that fell ----
    vis = smooth(1.0, 5.0, ts)
    modes = ["full"] * 8; glows = [0.35] * 8
    if ts >= FALL_T:
        modes[FELL] = "fallen"
    for (t0, i) in SUNG:                                     # he sings it out
        if t0 <= ts <= t0 + 1.4: glows[i] = max(glows[i], 1.0 - (ts - t0) / 1.4)
    for (t0, i) in ECHO:                                     # it comes back, cold
        if t0 <= ts <= t0 + 1.5: glows[i] = max(glows[i], 0.85 * (1.0 - (ts - t0) / 1.5))
    for (t0, i) in BROKEN:                                   # the Elder plays the wound
        if t0 <= ts <= t0 + 1.3: glows[i] = max(glows[i], 1.0 - (ts - t0) / 1.3)
    if ts >= FALL_T:                                          # the fallen note keeps ringing
        glows[FELL] = max(glows[FELL], 0.30 + 0.42 * abs(math.sin((ts - FALL_T) * 0.9)))
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(ky - kfoot)), kspr)
    if eseen > 0.02:
        sp = espr
        if eseen < 0.995:
            al = sp.getchannel("A").point(lambda v: int(v * eseen)); sp = sp.copy(); sp.putalpha(al)
        im.paste(sp, (int(ex - sp.size[0] / 2), int(ey - efoot)), sp)
    staff.draw(im, vis, modes, glows)

    d = ImageDraw.Draw(im, "RGBA")
    for (t0, i) in SUNG: ring(d, SLOT[i][0], SLOT[i][1], t0, ts, (255, 214, 150), rmax=30)
    for (t0, i) in ECHO: ring(d, SLOT[i][0], SLOT[i][1], t0, ts, (170, 192, 226), rmax=34)
    ring(d, SLOT[FELL][0], SLOT[FELL][1], FALL_T, ts, (170, 192, 226), rmax=58)
    for (t0, i) in BROKEN: ring(d, SLOT[i][0], SLOT[i][1], t0, ts, (255, 214, 150), rmax=26)
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.40)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    eye.apply_lids(frame, eye.blink_amount(ts, BLINKS))     # the Observer blinks
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
    K = dict(register=0, pan=0.40); E = dict(register=-12, pan=0.62)

    # --- the world whole (C major), the nightly walk ---
    w(pad([midi(48), midi(55), midi(60), midi(64)], 20, 0.042), 1, 0.5)
    for t in np.arange(2, 7.5, 1.5): d(softkick(0.075), t, 0.5)

    # 1. he sings the First Song out (Do Re Mi Sol)
    for (t0, i) in SUNG: d(piano(midi(PITCH[i]), 2.2, 0.135), t0, 0.42 + 0.02 * i)
    w(piano(midi(72), 2.0, 0.05), 12.6, 0.5)

    # 2. the echo returns — same melody, the sixth fallen, far away and cold
    for (t0, i) in ECHO:
        p = PITCH[i] + 12
        w(piano(midi(p), 2.4, 0.055), t0, 0.66)
    w(piano(midi(80), 3.0, 0.05), 21.5, 0.70)                 # the fallen note (A-flat)
    d(piano(midi(68), 3.2, 0.075), 21.6, 0.55)

    # 3. unease settles (A minor), and he speaks
    w(pad([midi(45), midi(52), midi(57), midi(60)], 22, 0.04), 23.5, 0.5)
    say(d, "something is wrong", 29.0, style="calm", register=-12, pan=0.44)
    d(softkick(0.07), 34.5, 0.5); d(softkick(0.06), 37.0, 0.5)   # his steps as he turns

    # 4. the question, and the rest that answers it (kept SHORT, always moving)
    say(d, "who are you", 42.5, style="urgent", **K)
    w(bass(midi(31), 5.0, 0.055), 46.0, 0.5)                  # the dark leans in
    d(softkick(0.055), 47.6, 0.5); d(softkick(0.05), 49.4, 0.5)
    say(d, "who are you", 54.0, style="urgent", register=12, pan=0.40)
    d(piano(midi(42), 4.5, 0.075), 58.4, 0.5)                 # not a note: below the scale
    w(bass(midi(30), 6.0, 0.05), 58.4, 0.5)
    say(d, "i am afraid", 61.5, style="fear", register=0, pan=0.42)

    # 5. the Elder arrives (F major = shelter)
    w(pad([midi(41), midi(48), midi(57), midi(60)], 20, 0.044), 65.5, 0.5)
    for t in np.arange(66.5, 72, 1.4): d(softkick(0.07), t, 0.62)   # his approach
    say(d, "i hear you", 67.2, style="calm", **E)
    say(d, "listen", 72.2, style="calm", **E)
    # 6. he names the wound: the First Song's phrase with harmony turned to doubt
    for (t0, i) in BROKEN: d(piano(midi(PITCH[i]), 2.0, 0.125), t0, 0.60 - 0.02 * i)
    w(piano(midi(65), 3.0, 0.05), 76.4, 0.62)
    say(d, "what now", 89.5, style="calm", register=0, pan=0.40)
    say(d, "come with me", 94.5, style="confident", **E)

    # 7. we are connected — a chord, then they set out
    w(pad([midi(36), midi(48), midi(55), midi(60)], 14, 0.05), 99.2, 0.5)
    say(d, "we are connected", 99.8, style="confident", register=-12, pan=0.5)
    for t in np.arange(106.5, 118, 1.5): d(softkick(0.08), t, 0.5)
    for (m, t) in [(60, 107.5), (62, 108.7), (64, 109.9), (67, 111.1)]:
        d(piano(midi(m), 2.0, 0.085), t, 0.46)

    # 8. the hook: the fallen note, alone, and something listening back
    d(piano(midi(68), 6.0, 0.115), 113.5, 0.56)
    w(bass(midi(30), 8.0, 0.05), 114.0, 0.5)
    d(softkick(0.11), 118.6, 0.5)
    w(piano(midi(92), 3.0, 0.022), 120.0, 0.66)               # a far, cold listening
    w(pad([midi(45), midi(52), midi(56)], 8, 0.04), 121.0, 0.5)
    d(piano(midi(45), 5.0, 0.075), 122.5, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep11_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep11_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep11.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep11_silent.mp4", "-i", "ep11.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep1_the_echo_that_came_back.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep1_the_echo_that_came_back.mp4")


if __name__ == "__main__":
    main()
