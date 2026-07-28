"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 7 — "Seven Ways to Stand Together"
Two cannot make a chord. So the Keeper stops fighting with the notes and starts calling
them — and discovers, mid-fight, that the same seven notes stand together in seven
different ways. Each chord is a different weapon with a different colour and feeling.
The last discovery is not a chord at all: it is two chords in a row — the pull home —
and that is the one thing the Sunderer cannot follow.

Hidden lesson: triads built on every degree of the scale, then the cadence. ~2:30.
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
SDUR = 144.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; LAV = [206, 190, 244]
VIOLET = [176, 158, 232]; SICK = [150, 190, 150]; WHITE = [255, 244, 214]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "7", "Seven Ways to Stand Together", "the Long Dark"
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
FS = font(45); FSM = font(33); TAG = font(29); SHF = gfont(34); NAMEF = font(34)


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
def ground_y(x):
    aa = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(aa) + SINK

KX = 0.255 * W; KY = ground_y(KX)
SHX = 0.395 * W; SHY = ground_y(SHX) - 0.08 * H
SUN_X = 0.83 * W

# ---------------- THE CHORDS ----------------
# (t, name, degrees, colour, power)  power: 0 = fails, 1 = lands, 2 = huge
CHORDS = [
    (18.5, "Do  Mi",          [0, 2],    GOLD,   0),   # two is not a chord
    (34.0, "Do  Mi  Sol",     [0, 2, 4], GOLD,   0),   # he already knows this one
    (46.0, "Re  Fa  La",      [1, 3, 5], VIOLET, 1),   # a chord he had never heard
    (57.0, "Fa  La  Do",      [3, 5, 7], WARM,   1),   # shelter
    (68.0, "La  Do  Mi",      [5, 7, 2], VIOLET, 2),   # the Elder's colour
    (80.0, "Ti  Re  Fa",      [6, 1, 3], SICK,   1),   # stands on nothing
    (100.0, "Sol  Ti  Re",    [4, 6, 1], WHITE,  2),   # it does not push. it pulls.
    (108.0, "Do  Mi  Sol",    [0, 2, 4], WHITE,  2),   # ...home. the cadence.
]
CHORD_DUR = 3.4


def chord_at(ts):
    for (t0, nm, degs, col, pw) in CHORDS:
        if t0 <= ts <= t0 + CHORD_DUR:
            return (t0, nm, degs, col, pw, (ts - t0) / CHORD_DUR)
    return None


CAPS = [
    (1.4, 5.0, "there were two of them now."),
    (6.0, 7.6, "together."),
    (10.4, 13.6, "two notes are not a chord."),
    (14.2, 17.2, "they are only a question."),
    (20.6, 23.0, "so he stopped\nfighting with the notes —"),
    (23.6, 26.6, "and started calling them."),
    (30.0, 32.4, "listen."),
    (37.6, 40.8, "he already knew that one."),
    (43.0, 45.4, "so they tried another."),
    (49.6, 53.0, "a chord he had never heard."),
    (60.6, 63.4, "shelter."),
    (71.6, 75.4, "this one was\nthe Elder's colour."),
    (83.6, 87.2, "a chord that stands\non nothing."),
    (90.4, 93.0, "seven notes."),
    (93.6, 97.0, "and seven ways\nto stand together."),
    (103.6, 105.8, "this one did not push."),
    (106.4, 108.0, "it pulled."),
    (111.6, 115.0, "every song\nwants to come home."),
    (116.0, 119.6, "and he had nowhere\nto come home to."),
    (126.0, 130.0, "they had found seven ways\nto stand together."),
    (130.6, 134.2, "and he had taken\nthe one that mattered."),
    (135.0, 137.0, "what now?"),
    (138.0, 141.6, "there was one chord left\nthey had never tried."),
    (142.2, 145.6, "it had no notes in it at all."),
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


def draw_chord_name(im, ts):
    c = chord_at(ts)
    if c is None: return
    t0, nm, degs, col, pw, u = c
    fade = float(np.interp(u, [0, 0.10, 0.80, 1.0], [0, 1, 1, 0]))
    d = ImageDraw.Draw(im, "RGBA")
    bb = d.textbbox((0, 0), nm, font=NAMEF); xx = (W - (bb[2] - bb[0])) // 2
    yy = int(SY + 5.4 * LG)
    d.text((xx + 2, yy + 2), nm, font=NAMEF, fill=(0, 0, 0, int(140 * fade)))
    d.text((xx, yy), nm, font=NAMEF, fill=(col[0], col[1], col[2], int(235 * fade)))


def end_card(im, ts):
    if ts < 146.5: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [146.5, 147.4, 148.6, 149.8], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.455), ("the more you observe.", 0.492)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "to be continued"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.552 * H)), tg, font=TAG, fill=(202, 194, 182, int(190 * fade)))


def story(ts):
    scene = "night" if ts < 92 else "fading_edge"
    a = pl.build_sky(scene).copy()
    base, mask = pl.planet_base(scene)
    a[mask] = base[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta_of(ts), scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    push = 0.0                                          # how far he has been driven back
    for (t0, nm, degs, col, pw) in CHORDS:
        if ts > t0 + 1.2 and pw > 0:
            push += (26 if pw == 1 else 46) * smooth(t0 + 1.2, t0 + 2.6, ts)
    flee = smooth(118, 130, ts)
    sx = SUN_X + min(push, 150) + 260 * flee
    sy = ground_y(sx)
    a *= (1 - 0.14 * (1 - flee))
    darken(a, sx + 0.05 * W, sy - 0.02 * H, 170, 0.38 * (1 - 0.7 * flee))

    # ---- the Keeper, conducting ----
    c = chord_at(ts)
    kl = 0.55 * smooth(5.4, 6.2, ts) * (1 - smooth(9, 10.4, ts))
    if c is not None:
        kl = max(kl, 0.95 * smooth(c[0] - 0.9, c[0], ts) * (1 - smooth(c[0] + CHORD_DUR, c[0] + CHORD_DUR + 1.2, ts)))
    kl = max(kl, 0.5 * smooth(29.6, 30.4, ts) * (1 - smooth(33, 34.2, ts)))
    kspr, kfoot, kdx, kdy = character(140, "stand", ts, 1, lift=clamp(kl), lean=fl.idle_sway(ts))
    glow(a, KX + kdx, KY + kdy, 22, GOLD, 0.9)
    shx = SHX + fl.bob(ts, 6, f1=0.5, f2=1.15, ph=0.7)
    shy = SHY + fl.bob(ts, 8, ph=1.9)
    glow(a, shx, shy, 12, LAV, 0.9); glow(a, shx, shy, 30, LAV, 0.16)

    # ---- the chord: lit notes, converging beams, the strike ----
    shake = 0.0
    if c is not None:
        t0, nm, degs, col, pw, u = c
        rise = smooth(0.0, 0.28, u)
        hold = rise * (1 - smooth(0.86, 1.0, u))
        conv = smooth(0.30, 0.62, u)
        land = smooth(0.55, 0.72, u) * (1 - smooth(0.86, 1.0, u))
        mid = (0.60 * W, SY + 3.6 * LG)
        for dg in degs:                                  # each note pours its light down
            p0 = SLOT[dg]
            glow(a, p0[0], p0[1], 16 + 10 * hold, col, 0.30 + 0.55 * hold)
            if conv > 0.02:
                n = 12
                for i in range(n):
                    uu = (i / (n - 1.0)) * conv
                    glow(a, lerp(p0[0], mid[0], uu), lerp(p0[1], mid[1], uu), 5, col, 0.30 * conv)
        if conv > 0.3:
            glow(a, mid[0], mid[1], 22 + 26 * conv, col, 0.30 * conv)
        if land > 0.02:                                  # the strike
            n = 16
            for i in range(n):
                uu = (i / (n - 1.0)) * land
                fade = 1.0 if pw > 0 else max(0.0, 1 - uu / 0.5)
                cc = col if pw > 0 else [120, 126, 140]
                glow(a, lerp(mid[0], sx, uu), lerp(mid[1], sy - 0.05 * H, uu) - 0.05 * H * math.sin(math.pi * uu),
                     7, cc, (0.42 if pw > 0 else 0.18) * fade)
            if pw > 0 and land > 0.7:
                glow(a, sx, sy - 0.05 * H, 30 + 60 * (land - 0.7), col, 0.5 * (1 - (land - 0.7) / 0.3))
                shake = max(shake, (5.0 if pw == 1 else 9.0) * (1 - (land - 0.7) / 0.3))
            if pw == 0 and land > 0.5:                   # he sings it back / it fizzles
                darken(a, sx + 0.05 * W, sy - 0.04 * H, 46, 0.5)

    # ---- the Sunderer ----
    darken(a, sx + 0.05 * W, sy - 0.035 * H, 50, 0.85 * (1 - 0.6 * flee))
    glow(a, sx + 0.05 * W, sy - 0.035 * H, 13, [70, 92, 152], 0.32 * (1 - flee))
    sspr, sfoot, _, _ = character(176, "stand", ts, -1, lean=0.02 * math.sin(ts * 0.5))
    if flee > 0.02:
        al = sspr.getchannel("A").point(lambda v: int(v * (1 - flee))); sspr = sspr.copy(); sspr.putalpha(al)

    # ---- the staff ----
    vis = smooth(1.0, 4.5, ts)
    modes = ["full"] * 8; glows = [0.24] * 8
    if c is not None:
        t0, nm, degs, col, pw, u = c
        for dg in degs:
            glows[dg] = max(glows[dg], 0.45 + 0.5 * smooth(0.0, 0.3, u) * (1 - smooth(0.86, 1.0, u)))
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(KX - kspr.size[0] / 2), int(KY - kfoot)), kspr)
    im.paste(sspr, (int(sx - sspr.size[0] / 2), int(sy - sfoot)), sspr)
    staff.draw(im, vis, modes, glows)
    ImageDraw.Draw(im, "RGBA").text((shx + 28, shy - 24), "♯", font=SHF,
                                    fill=(216, 204, 248, 220), anchor="mm")
    draw_chord_name(im, ts)
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


BLINKS = [(28.4, 0.24, 0.08, 0.38, 1.0),
          (42.0, 0.10, 0.03, 0.16, 0.38),
          (54.0, 0.10, 0.03, 0.16, 0.38),
          (65.0, 0.10, 0.03, 0.16, 0.38),
          (77.0, 0.10, 0.03, 0.16, 0.38),
          (98.0, 0.22, 0.07, 0.34, 0.9),
          (123.0, 0.24, 0.08, 0.38, 1.0),
          (145.0, 0.85, 0.30, 1.10, 1.0)]


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
    K = dict(register=0, pan=0.36); SH = dict(register=0, pan=0.54)

    w(pad([midi(45), midi(52), midi(57), midi(60)], 30, 0.038), 1, 0.5)
    w(bass(midi(33), 16, 0.045), 1, 0.5)
    say(d, "together", 6.0, style="calm", **K)
    say(d, "listen", 30.0, style="confident", **K)

    for (t0, nm, degs, col, pw) in CHORDS:
        mids = [PITCH[g] for g in degs]
        for i, m in enumerate(mids):                     # the notes arrive one at a time
            d(piano(midi(m), 3.6, 0.115), t0 + i * 0.22, 0.36 + 0.14 * i)
        if pw > 0:                                       # then sound together and land
            for m in mids:
                d(piano(midi(m), 3.0, 0.105), t0 + 1.9, 0.5)
            w(pad([midi(m - 12) for m in mids], 3.6, 0.05), t0 + 1.9, 0.5)
            d(softkick(0.11 if pw == 1 else 0.15), t0 + 2.4, 0.5)
            w(bass(midi(mids[0] - 24), 4.0, 0.05), t0 + 1.9, 0.5)
        else:                                            # he sings it back; it dies
            for m in mids:
                d(piano(midi(m), 2.0, 0.075), t0 + 2.0, 0.66)
            w(bass(midi(29), 3.0, 0.05), t0 + 2.4, 0.64)
            d(softkick(0.07), t0 + 2.4, 0.64)

    # the cadence lands hard: V -> I, the world leaning home
    w(pad([midi(43), midi(50), midi(55), midi(62)], 8, 0.05), 100.0, 0.5)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 16, 0.055), 108.0, 0.5)
    w(bass(midi(31), 8, 0.055), 100.0, 0.5); w(bass(midi(36), 16, 0.06), 108.0, 0.5)
    for i, m in enumerate([60, 64, 67, 72]):
        d(piano(midi(m), 5.0, 0.10), 112.0 + i * 0.18, 0.5)
    d(softkick(0.16), 108.0, 0.5)
    for t in np.arange(119, 129, 1.2): d(softkick(0.07), t, 0.66)      # he breaks away

    say(d, "what now", 135.0, style="calm", **K)
    w(bass(midi(31), 10, 0.05), 137.0, 0.5)
    w(pad([midi(45), midi(52), midi(57)], 10, 0.038), 138, 0.5)
    d(piano(midi(60), 6.0, 0.09), 142.5, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep17_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep17_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep17.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep17_silent.mp4", "-i", "ep17.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch2_ep7_seven_ways.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch2_ep7_seven_ways.mp4")


if __name__ == "__main__":
    main()
