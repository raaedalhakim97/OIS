"""
THE OBSERVER WORLD · CHAPTER II · FINALE — "The Loudest Quiet"
He has copied everything: the note, the beat, the thread, every chord. So the Keeper
plays nothing — a rest — and the one who can only echo has nothing to echo. Then, in
the quiet, he does the only thing a keeper can do, and the only thing the Sunderer has
never done: he gives his note away. To him. And the hole closes.

Hidden lesson: the rest — silence is not the end of music, it is written into it. ~2:40.
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
SDUR = 154.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; LAV = [206, 190, 244]
VIOLET = [176, 158, 232]; WHITE = [255, 244, 214]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "8", "The Loudest Quiet", "the Long Dark"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
FEET = APEX_Y + SINK
SLOT = [staff.note_xy(i) for i in range(8)]
PITCH = [60, 62, 64, 65, 67, 69, 71, 72]

REST0, REST1 = 44.0, 74.0          # the silence
GIVE0 = 92.0                       # he offers his note
TAKEN = 104.0                      # it is accepted
FILLED = 112.0                     # the hole closes


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
FS = font(45); FSM = font(33); TAG = font(30); SHF = gfont(34); NAMEF = font(34)


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


for s in ("night", "fading_edge", "dawn", "morning"): pl.build_sky(s); pl.planet_base(s)
def theta_of(ts): return 0.04 * ts
def ground_y(x):
    aa = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(aa) + SINK

KX0 = 0.255 * W; SHX = 0.385 * W
SUN_X = 0.80 * W

# the chords that fail, because he has learned them all
FAILS = [(9.0, "Re  Fa  La", [1, 3, 5], VIOLET), (18.0, "Fa  La  Do", [3, 5, 7], WARM),
         (27.0, "Sol  Ti  Re", [4, 6, 1], WHITE)]
FDUR = 6.0
def fail_at(ts):
    for (t0, nm, degs, col) in FAILS:
        if t0 <= ts <= t0 + FDUR: return (t0, nm, degs, col, (ts - t0) / FDUR)
    return None

def keeper_x(ts):
    return lerp(KX0, 0.60 * W, smooth(GIVE0, TAKEN, ts))

CAPS = [
    (1.4, 5.4, "he came back.\nand he had learned them all."),
    (12.4, 16.4, "every way they knew\nhow to stand together —"),
    (21.4, 24.4, "he sang each one back."),
    (31.6, 34.4, "what now?"),
    (37.0, 40.4, "the Keeper looked at\nthe empty place beside him."),
    (41.4, 43.2, "listen."),
    (45.6, 48.6, "and he played nothing."),
    (55.0, 58.6, "he could copy any sound."),
    (59.4, 62.4, "so they gave him none."),
    (66.0, 69.4, "silence is not\nthe end of music."),
    (70.0, 73.4, "it is written into it."),
    (75.0, 77.4, "it is a rest."),
    (80.4, 84.0, "and in the quiet,\nthe Keeper understood."),
    (86.0, 88.0, "no."),
    (88.6, 90.4, "listen."),
    (93.0, 97.0, "a keeper is one\nwho gives his own away."),
    (99.0, 102.4, "he had taken everything."),
    (103.0, 106.4, "no one had ever\ngiven him anything."),
    (113.0, 116.4, "and the hole closed."),
    (121.0, 124.6, "the ones he had taken\ncame back."),
    (125.4, 127.6, "all but one."),
    (133.0, 135.4, "thank you."),
    (138.0, 141.0, "the world had its song back."),
    (141.8, 145.0, "and the Keeper\nhad empty hands."),
    (146.0, 150.0, "which is how you know\nhe was a keeper."),
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
    if ts < 150.6: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [150.6, 151.6, 153.0, 154.0], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.445), ("the more you observe.", 0.482)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "— end of Chapter II —"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.545 * H)), tg, font=TAG, fill=(214, 206, 192, int(210 * fade)))


BLINKS = [(35.6, 0.26, 0.09, 0.40, 1.0),
          (43.6, 0.34, 0.30, 0.90, 1.0),      # the long blink into silence
          (78.6, 0.28, 0.10, 0.44, 1.0),
          (110.4, 0.20, 0.30, 1.20, 0.85),    # the hole closes: a slow, soft blink
          (129.0, 0.26, 0.09, 0.42, 1.0),
          (152.4, 0.90, 0.35, 1.20, 1.0)]


def story(ts):
    if ts < 74: scene = "night"
    elif ts < 118: scene = "fading_edge"
    elif ts < 138: scene = "dawn"
    else: scene = "morning"
    a = pl.build_sky(scene).copy()
    base, mask = pl.planet_base(scene)
    a[mask] = base[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta_of(ts), scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    healed = smooth(FILLED, FILLED + 8, ts)
    dark = (1 - healed)
    sx = SUN_X + 150 * smooth(FILLED + 12, 150, ts)
    sy = ground_y(sx)
    a *= (1 - 0.16 * dark)
    darken(a, sx + 0.05 * W, sy - 0.02 * H, 170, 0.40 * dark)

    # ---- the rest: the world holds its breath ----
    inrest = smooth(REST0, REST0 + 1.4, ts) * (1 - smooth(REST1, REST1 + 2.0, ts))
    if inrest > 0.02:
        a *= (1 - 0.30 * inrest)                       # the light itself goes quiet

    kx = keeper_x(ts); ky = ground_y(kx)
    # ---- the trio (two) ----
    f = fail_at(ts)
    kl = 0.0
    if f is not None:
        kl = 0.9 * smooth(f[0] - 0.8, f[0], ts) * (1 - smooth(f[0] + 4.4, f[0] + 5.6, ts))
    kl = max(kl, 0.45 * smooth(41.0, 41.8, ts) * (1 - smooth(44, 45.4, ts)))
    kl = max(kl, 0.95 * smooth(GIVE0 - 1.0, GIVE0 + 1.0, ts) * (1 - smooth(TAKEN + 1.5, TAKEN + 3.5, ts)))
    kl = max(kl, 0.35 * smooth(132.4, 133.2, ts) * (1 - smooth(136, 137.4, ts)))
    kspr, kfoot, kdx, kdy = character(140, "walk" if GIVE0 < ts < TAKEN else "stand", ts, 1,
                                      lift=clamp(kl), lean=fl.idle_sway(ts))
    hand = (kx + kdx, ky + kdy)
    has_note = 1.0 - smooth(TAKEN, TAKEN + 2.0, ts)     # he gives it away
    glow(a, hand[0], hand[1], 22, GOLD, (0.30 + 0.60 * has_note) * (1 - 0.5 * inrest))

    shx = SHX + fl.bob(ts, 6, f1=0.5, f2=1.15, ph=0.7)
    shy = ground_y(SHX) - 0.08 * H + fl.bob(ts, 8, ph=1.9)
    glow(a, shx, shy, 12, LAV, 0.9 * (1 - 0.4 * inrest)); glow(a, shx, shy, 30, LAV, 0.16)

    # ---- the chords that fail ----
    if f is not None:
        t0, nm, degs, col, u = f
        mid = (0.58 * W, SY + 3.6 * LG)
        conv = smooth(0.18, 0.44, u); land = smooth(0.42, 0.60, u) * (1 - smooth(0.80, 0.95, u))
        for dg in degs:
            p0 = SLOT[dg]
            glow(a, p0[0], p0[1], 15, col, 0.30 + 0.40 * smooth(0.0, 0.25, u) * (1 - smooth(0.8, 1.0, u)))
            if conv > 0.02:
                for i in range(10):
                    uu = (i / 9.0) * conv
                    glow(a, lerp(p0[0], mid[0], uu), lerp(p0[1], mid[1], uu), 5, col, 0.26 * conv)
        if land > 0.02:
            for i in range(14):
                uu = (i / 13.0) * land
                glow(a, lerp(mid[0], sx, uu), lerp(mid[1], sy - 0.05 * H, uu) - 0.05 * H * math.sin(math.pi * uu),
                     6, col, 0.34 * land)
        if u > 0.66:                                    # he sings it back and it dies
            b = smooth(0.66, 0.80, u) * (1 - smooth(0.92, 1.0, u))
            for dg in degs:
                glow(a, sx + 0.04 * W, sy - 0.06 * H, 20, col, 0.22 * b)
            darken(a, sx + 0.05 * W, sy - 0.04 * H, 54, 0.45 * b)

    # ---- the gift ----
    if GIVE0 <= ts <= FILLED + 2:
        p = smooth(GIVE0 + 2, TAKEN, ts)
        gx = lerp(hand[0], sx + 0.05 * W, p)
        gy = lerp(hand[1], sy - 0.035 * H, p) - 0.05 * H * math.sin(math.pi * p)
        glow(a, gx, gy, 14, GOLD, 0.95)
        glow(a, gx, gy, 34, GOLD, 0.20)
    fill = smooth(TAKEN, FILLED, ts)
    hole_r = 50 * (1 - fill)
    if hole_r > 2 and healed < 0.9:
        darken(a, sx + 0.05 * W, sy - 0.035 * H, hole_r, 0.85 * (1 - fill))
        glow(a, sx + 0.05 * W, sy - 0.035 * H, 13, [70, 92, 152], 0.30 * (1 - fill))
    if fill > 0.05:                                     # the void becomes a lantern
        glow(a, sx + 0.05 * W, sy - 0.035 * H, 20, WARM, 0.85 * fill)
        glow(a, sx + 0.05 * W, sy - 0.035 * H, 46, WARM, 0.18 * fill)

    # ---- the taken lights come back ----
    ret = smooth(119, 132, ts)
    if ret > 0.02:
        for i in range(9):
            ph = i * 0.7 + ts * 0.5
            rx = lerp(sx, 0.14 * W + i * 0.095 * W, ret)
            ry = lerp(sy - 0.04 * H, ground_y(0.14 * W + i * 0.095 * W) - 0.10 * H - 26 * math.sin(ph), ret)
            glow(a, rx, ry, 7, WARM, ret * 0.55)

    # ---- the Sunderer ----
    sspr, sfoot, _, _ = character(176, "walk" if ts > FILLED + 12 else "stand", ts, -1,
                                  lean=0.02 * math.sin(ts * 0.5))
    if healed > 0.5:
        al = sspr.getchannel("A").point(lambda v: int(v * (1 - 0.35 * healed))); sspr = sspr.copy(); sspr.putalpha(al)

    # ---- the staff ----
    vis = smooth(1.0, 4.5, ts)
    modes = ["full"] * 8; glows = [0.26] * 8
    if f is not None:
        for dg in f[2]: glows[dg] = max(glows[dg], 0.6)
    if REST0 - 0.6 <= ts <= REST1 + 4.2:                # THE REST (held through the line)
        modes = ["rest"] * 8; glows = [0.0] * 8
    if ts > 134:                                        # the song comes back, whole
        for i in range(8):
            t0 = 134 + i * 0.5
            if t0 <= ts <= t0 + 1.2: glows[i] = max(glows[i], 1 - (ts - t0) / 1.2)
            if ts > t0: glows[i] = max(glows[i], 0.42)
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(ky - kfoot)), kspr)
    im.paste(sspr, (int(sx - sspr.size[0] / 2), int(sy - sfoot)), sspr)
    staff.draw(im, vis, modes, glows)
    ImageDraw.Draw(im, "RGBA").text((shx + 28, shy - 24), "♯", font=SHF,
                                    fill=(216, 204, 248, 220), anchor="mm")
    if f is not None:                                    # the chord's name
        t0, nm, degs, col, u = f
        fade = float(np.interp(u, [0, 0.08, 0.7, 0.85], [0, 1, 1, 0]))
        d2 = ImageDraw.Draw(im, "RGBA")
        bb = d2.textbbox((0, 0), nm, font=NAMEF); xx = (W - (bb[2] - bb[0])) // 2
        d2.text((xx, int(SY + 5.4 * LG)), nm, font=NAMEF, fill=(col[0], col[1], col[2], int(230 * fade)))
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.42 - 0.08 * healed)
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
    K = dict(register=0, pan=0.38); SH = dict(register=0, pan=0.56)

    # ACT I — everything fails
    w(pad([midi(44), midi(51), midi(56), midi(59)], 42, 0.04), 1, 0.5)
    w(bass(midi(30), 40, 0.05), 1, 0.5)
    for (t0, nm, degs, col) in FAILS:
        mids = [PITCH[g] for g in degs]
        for i, m in enumerate(mids): d(piano(midi(m), 3.4, 0.115), t0 + i * 0.22, 0.36 + 0.12 * i)
        for m in mids: d(piano(midi(m), 3.0, 0.10), t0 + 2.0, 0.42)
        for m in mids: d(piano(midi(m), 2.6, 0.09), t0 + 4.0, 0.66)     # he sings it back
        d(softkick(0.08), t0 + 4.6, 0.66); w(bass(midi(29), 3.0, 0.05), t0 + 4.6, 0.66)
    say(d, "what now", 31.6, style="calm", **SH)
    say(d, "listen", 41.4, style="calm", **K)

    # ACT II — THE REST. everything stops. (only a bare room tone underneath)
    w(bass(midi(24), REST1 - REST0 + 2, 0.018), REST0, 0.5)
    d(softkick(0.05), REST0 + 9.5, 0.66)                                 # he staggers
    d(softkick(0.045), REST0 + 15.0, 0.66)
    w(bass(midi(27), 6, 0.03), REST0 + 16.0, 0.62)

    # ACT III — the gift
    w(pad([midi(41), midi(48), midi(53), midi(57)], 22, 0.04), 79.0, 0.5)
    say(d, "no", 86.0, style="urgent", **SH)
    say(d, "listen", 88.6, style="calm", **K)
    d(piano(midi(60), 6.0, 0.15), GIVE0, 0.42)                           # his note, held out
    w(pad([midi(48), midi(60)], 8, 0.04), GIVE0, 0.5)
    for i, m in enumerate([60, 60, 60]):                                 # the walk toward him
        d(softkick(0.07), GIVE0 + 2 + i * 1.6, 0.5)
    d(piano(midi(60), 8.0, 0.17), TAKEN, 0.56)                           # it is accepted
    w(pad([midi(36), midi(48), midi(55), midi(60)], 14, 0.05), TAKEN, 0.5)
    for i, m in enumerate([48, 55, 60, 64, 67]):                         # the hole closes
        d(piano(midi(m), 5.0, 0.085), FILLED - 2 + i * 0.35, 0.5)
    w(bass(midi(36), 20, 0.055), FILLED - 2, 0.5)

    # ACT IV — the lights return; the world has its song
    for i in range(9):
        d(piano(midi(PITCH[i % 8]), 3.2, 0.07), 120.0 + i * 1.1, 0.30 + 0.05 * i)
    say(d, "thank you", 133.0, style="calm", **K)
    for i in range(8):                                                    # the scale, whole
        d(piano(midi(PITCH[i]), 2.4, 0.11), 134.0 + i * 0.5, 0.38 + 0.03 * i)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 20, 0.05), 134.0, 0.5)
    w(bass(midi(36), 20, 0.055), 134.0, 0.5)
    for i, m in enumerate([60, 64, 67, 72]):
        d(piano(midi(m), 7.0, 0.09), 146.0 + i * 0.25, 0.5)

    dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
    wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
    mix = master(dry * 0.92 + wet)
    # enforce the silence: fade the world out and back around the rest
    t = np.arange(len(mix)) / SR - TITLE_DUR
    env = np.ones(len(mix), np.float32)
    env *= 1 - 0.93 * np.clip((t - REST0) / 1.6, 0, 1) * np.clip(1 - (t - REST1) / 2.2, 0, 1)
    mix *= env[:, None]
    fi, fo = int(0.6 * SR), int(4 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep18_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep18_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep18.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep18_silent.mp4", "-i", "ep18.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep8_the_loudest_quiet.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep8_the_loudest_quiet.mp4")


if __name__ == "__main__":
    main()
