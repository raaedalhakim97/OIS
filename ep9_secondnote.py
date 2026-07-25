"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 9 — "The Second Note"
Do is home on the staff. The Keeper calls for the second note — and TWO lights answer,
almost identical. Which one is Re? The first will not rest on Re's space: it slides and
trembles between the steps, and against Do it clashes (a half step, C#). It is not a
scale note at all — it is a between-stone, a SHARP, and the ♯ appears beside it like a
name. The second walks Do→Re→Do cleanly and settles into its space: a whole step home.
The sharp bows and slips away, waiting for another song. Two found, six to go. The
hidden lesson: whole steps vs half steps, and what accidentals are. ~1:54.
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
SDUR = 108.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; COOL = [150, 172, 214]
SHARPC = [205, 196, 232]                            # the sharp's cooler, lavender light
CENTER_Y = 0.52
CH, EP, TITLE, LAND = "I", "9", "The Second Note", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY
SINK = 34
LG = staff.LG; SY = staff.SY
PLACED = 64.0                                       # Re settles into its space

AM = -0.24                                          # keeper's angle on the ball
KFX = CX + R * math.sin(AM)
KFY = CY - R * math.cos(AM) + SINK
FEET = APEX_Y + SINK


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
FS = font(47); FSM = font(34); SHF = gfont(34)


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
SEGS = [(0, "night"), (16, "dawn"), (58, "morning"), (94, "golden")]

ROT = 0.13
def _rate(u):
    if u < 12: return 1.0
    if u < 16: return 1.0 - smooth(12, 16, u)
    if u < 94: return 0.0
    if u < 100: return smooth(94, 100, u)
    return 1.0
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))


DO_XY = staff.note_xy(0); RE_XY = staff.note_xy(1)
BETWEEN = ((DO_XY[0] + RE_XY[0]) / 2, (DO_XY[1] + RE_XY[1]) / 2 + 0.15 * LG)


# the sharp (impostor, C#): rises, tries Re's space, trembles, sinks BETWEEN, leaves
_S1A = (0.66 * W, SY + 5.5 * LG); _S1X = (0.92 * W, SY + 8.5 * LG)
S1 = [(14, 19, (1.04 * W, FEET - 0.02 * H), _S1A, "fly"),
      (19, 33, _S1A, _S1A, "hold"),
      (33, 35, _S1A, RE_XY, "land"),
      (35, 45, RE_XY, RE_XY, "hold"),
      (45, 49, RE_XY, BETWEEN, "land"),
      (49, 78, BETWEEN, BETWEEN, "hold"),
      (78, 88, BETWEEN, _S1X, "fly")]
def sharp_pos(ts):
    x, y = fl.path(ts, S1, _S1X)
    if 35 <= ts <= 45:                                    # it will not rest: slide + tremble
        k = smooth(35, 36.5, ts) * (1 - smooth(43.5, 45, ts))
        y += (0.28 * LG * math.sin(ts * 12) + 0.30 * LG * math.sin(ts * 2.2)) * k
        x += 0.18 * LG * math.sin(ts * 7.3) * k
    elif ts > 19:
        y += fl.bob(ts, 6, ph=1.0)
        x += fl.bob(ts, 2.4, f1=0.51, f2=1.13, ph=2.0)
    return x, y

# Re (the true second): rises, waits, then walks Do -> Re and settles
_S2A = (0.82 * W, SY + 4.8 * LG)
S2 = [(15, 20, (1.07 * W, FEET - 0.06 * H), _S2A, "fly"),
      (20, 58, _S2A, _S2A, "hold"),
      (58, 59.6, _S2A, (DO_XY[0], DO_XY[1] - 1.3 * LG), "fly"),
      (59.6, 61.6, (DO_XY[0], DO_XY[1] - 1.3 * LG), (RE_XY[0], RE_XY[1] - 1.3 * LG), "fly"),
      (61.6, PLACED, (RE_XY[0], RE_XY[1] - 1.3 * LG), RE_XY, "land")]
def re_pos(ts):
    x, y = fl.path(ts, S2, RE_XY)
    if 20 < ts < 58:
        y += fl.bob(ts, 6, ph=2.0)
        x += fl.bob(ts, 2.4, f1=0.47, f2=1.19, ph=0.6)
    return x, y


def keeper_x(ts): return lerp(CX, KFX, smooth(11, 15, ts))


def ring(d, cx, cy, t0, ts, col, rmax=52):
    """An expanding ring of light — the chime made visible."""
    q = ts - t0
    if 0 <= q <= 0.9:
        u = q / 0.9; r = 8 + rmax * fl.ease_out(u); al = int(200 * (1 - u) ** 1.3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (al,), width=3)


CAPS = [
    (2.0, 8.0, "the first note was home."),
    (9.5, 15.0, "the Keeper called\nfor the second."),
    (17.5, 23.5, "two lights answered —\nalmost the same."),
    (25.5, 31.0, "which one was Re?"),
    (34.0, 40.0, "the first would not rest.\nit slid between the steps."),
    (41.5, 47.5, "and against Do\nit clashed — too close."),
    (50.0, 57.0, "it was a between-stone:\na sharp.  ♯"),
    (58.5, 66.0, "the second stepped true:\nDo — Re."),
    (68.0, 75.5, "a whole step home.\na half step between."),
    (78.0, 86.0, "the sharp bowed, and slipped away —\nwaiting for another song."),
    (89.0, 96.0, "two notes found.\nsix more to go."),
    (99.0, 106.0, "the more you know,\nthe more you observe."),
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

    # the Keeper — walks in, then stands to the left and conducts the test
    walk = ts < 12 or ts > 100
    lift = (smooth(9, 12, ts) * (1 - smooth(13, 15, ts))          # the call
            + smooth(32, 35, ts) * (1 - smooth(45, 48, ts))       # test one
            + smooth(57, 60, ts) * (1 - smooth(PLACED, PLACED + 4, ts)))  # test two
    lean = fl.vlean(keeper_x, ts) + fl.idle_sway(ts)       # lean into motion + living sway
    spr, foot, hdx, hdy = character(140, "walk" if walk else "stand", ts, 1,
                                    lift=clamp(lift), lean=lean)
    kx = keeper_x(ts)                                      # body planted; offsets are the lantern's
    ky = lerp(FEET, KFY, smooth(11, 15, ts))
    glow(a, kx + hdx, ky + hdy, 22, GOLD, 0.92 * (0.9 + 0.1 * math.sin(ts * 2.6)))

    # the two answering lights — each breathing at its own tempo
    seen1 = smooth(14, 18, ts); seen2 = smooth(15, 19, ts)
    gone1 = smooth(80, 88, ts)
    sx, sy2 = sharp_pos(ts)
    rx, ry2 = re_pos(ts)
    if seen1 > 0.02:
        c = SHARPC if ts > 49 else WARM                    # its true colour shows once named
        amp = seen1 * (1 - 0.85 * gone1) * (0.85 + 0.15 * math.sin(ts * 3.3 + 1))
        glow(a, sx, sy2, 14, c, amp)
        glow(a, sx, sy2, 34, c, amp * 0.16)
    if seen2 > 0.02 and ts < PLACED:
        amp = seen2 * (0.85 + 0.15 * math.sin(ts * 2.9 + 2))
        glow(a, rx, ry2, 14, WARM, amp)
        glow(a, rx, ry2, 34, WARM, amp * 0.16)

    # test-one clash flashes against Do
    for tt in (41.8, 44.0):
        dd = ts - tt
        if -0.3 <= dd <= 1.2:
            al = float(np.interp(dd, [-0.3, 0.1, 0.8, 1.2], [0, 1, 0.5, 0]))
            glow(a, DO_XY[0], DO_XY[1], 18, COOL, al * 0.5)

    # staff: Do full from Ep8; Re fills when placed
    vis = smooth(5, 11, ts)
    modes = ["ghost"] * 8; glows = [0.0] * 8
    modes[0] = "full"
    glows[0] = 0.45 + (clamp(1 - abs(ts - 10.5)) + clamp(1 - abs(ts - 12.7))) * 0.5  # rings at the call
    if ts >= PLACED:
        modes[1] = "full"
        glows[1] = clamp(1.0 - (ts - PLACED) / 1.6) * 0.6 + 0.45
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - foot)), spr)
    staff.draw(im, vis, modes, glows)

    d = ImageDraw.Draw(im, "RGBA")
    # chimes made visible: rings on the call, the naming, and the placement
    ring(d, DO_XY[0], DO_XY[1], 10.3, ts, (255, 214, 150), rmax=34)
    ring(d, DO_XY[0], DO_XY[1], 12.5, ts, (255, 214, 150), rmax=34)
    ring(d, BETWEEN[0], BETWEEN[1], 50.6, ts, (205, 196, 232), rmax=40)
    ring(d, RE_XY[0], RE_XY[1], PLACED, ts, (255, 214, 150), rmax=56)
    # the sharp's name appears beside it: ♯
    shv = smooth(50, 53, ts) * (1 - gone1)
    if shv > 0.02:
        d.text((sx + 1.1 * LG, sy2 - 0.2 * LG), "♯", font=SHF,
               fill=(215, 206, 240, int(230 * shv)), anchor="mm")
    # the question mark while the puzzle is open
    if 25 <= ts <= 32:
        qv = np.interp(ts, [25, 27, 30, 32], [0, 1, 1, 0])
        d.text((0.5 * W, SY - 2.9 * LG), "?", font=font(int(2.2 * LG)),
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

    w(pad([midi(48), midi(55), midi(60)], SDUR - 6, 0.04), 4, 0.5)
    for t in np.arange(2, 12, 1.4): d(softkick(0.09), t, 0.5)                # walking in
    d(piano(midi(60), 2.4, 0.14), 10.3, 0.42)                                # the call: Do... Do
    d(piano(midi(60), 2.8, 0.14), 12.5, 0.42)
    d(piano(midi(61), 2.0, 0.07), 17.2, 0.62)                                # two answers, faint
    d(piano(midi(62), 2.0, 0.07), 18.8, 0.70)

    # test one: C# against Do — a half step, beating hard
    d(piano(midi(60), 2.4, 0.12), 35.0, 0.45); d(piano(midi(61), 2.4, 0.12), 35.05, 0.58)
    d(piano(midi(60), 2.6, 0.12), 38.6, 0.45); d(piano(midi(61), 2.6, 0.12), 38.65, 0.58)
    d(piano(midi(61), 1.4, 0.09), 42.0, 0.58); d(piano(midi(60), 1.8, 0.09), 42.5, 0.45)
    # naming the sharp — its note alone, suddenly gentle
    d(piano(midi(61), 3.2, 0.09), 50.6, 0.60)
    w(pad([midi(49), midi(61)], 6, 0.03), 51.0, 0.60)

    # test two: the whole-step walk Do -> Re -> settle
    d(piano(midi(60), 1.6, 0.12), 59.3, 0.5)
    d(piano(midi(62), 1.6, 0.12), 60.7, 0.55)
    d(piano(midi(60), 1.6, 0.10), 62.1, 0.5)
    d(piano(midi(62), 4.6, 0.17), PLACED, 0.5)                               # Re home
    w(pad([midi(48), midi(55), midi(60), midi(62)], 10, 0.05), PLACED, 0.5)
    w(bass(midi(36), 10, 0.06), PLACED, 0.5)

    # the sharp's farewell — its voice recedes upward
    d(piano(midi(61), 3.5, 0.06), 79.0, 0.68)
    d(piano(midi(73), 4.0, 0.04), 81.5, 0.72)

    # two found: the little Do-Re motif, then walking on
    d(piano(midi(60), 1.6, 0.10), 89.0, 0.5); d(piano(midi(62), 1.6, 0.10), 90.3, 0.5)
    d(piano(midi(60), 2.6, 0.10), 91.6, 0.5)
    for t in np.arange(96, 105, 1.4): d(softkick(0.09), t, 0.5)
    d(piano(midi(60), 6.0, 0.14), 99.0, 0.5); d(piano(midi(67), 6.0, 0.08), 99.0, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep9_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep9_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep9.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep9_silent.mp4", "-i", "ep9.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep9_the_second_note.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep9_the_second_note.mp4")


if __name__ == "__main__":
    main()
