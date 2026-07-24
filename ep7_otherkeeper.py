"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 7 — "The Missing Note"
One note is missing from the song. The Keeper searches the turning world and STOPS
when he meets another keeper — and asks him for the missing note. The other keeper
will not simply give it: "it is not mine to give." Instead he lays out the SOLFÈGE
SCALE on the ground — Do Re Mi Fa Sol La Ti Do — and the two play it note by note.
Where Fa should ring, there is silence: that empty step is the missing note. They
give it back its place, the scale rings whole, and they walk on. A note puzzle told
as story — the hidden lesson is the major scale and finding a pitch by ear. ~2:00.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
import title_card as tc
import world, planet as pl

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 116.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; DIMC = [120, 110, 120]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "I", "7", "The Missing Note", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX; R = pl.R; CY = pl.CY


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
FS = font(47); FSM = font(34); GF = gfont(50); SOLF = gfont(27)


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
SEGS = [(0, "night"), (16, "dawn"), (58, "morning"), (104, "golden")]

# ------- the world turns only while the Keeper walks; it HOLDS STILL while they solve it -------
ROT = 0.13
def _rate(u):
    if u < 12: return 1.0                     # searching — world turns
    if u < 18: return 1.0 - smooth(12, 18, u) # he sees the keeper — world eases to a stop
    if u < 104: return 0.0                    # the puzzle — world holds still
    if u < 110: return smooth(104, 110, u)    # walk on — world turns again
    return 1.0
_tt = np.linspace(0, SDUR, int(SDUR * 24) + 1)
_rs = np.array([_rate(u) for u in _tt])
_theta = ROT * np.concatenate([[0.0], np.cumsum((_rs[1:] + _rs[:-1]) * 0.5 * np.diff(_tt))])
def theta_of(ts): return float(np.interp(ts, _tt, _theta))

# ------- both keepers on the floor, either side of the apex -------
AM, AO = -0.27, 0.27
SINK = 34                                       # plant feet into the visually-solid ground
def ball_feet(a):                              # feet position on the ball at screen-angle a
    return CX + R * math.sin(a), CY - R * math.cos(a) + SINK

# ------- the scale, written as real music on a staff floating above the keepers -------
SCALE = [60, 62, 64, 65, 67, 69, 71, 72]       # C major = Do Re Mi Fa Sol La Ti Do
NAMES = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Ti", "Do"]
MISS = 3                                        # Fa is the missing step
PLAY = [50, 52.5, 55, 57.5, 60, 62.5, 65, 67.5]  # played note by note, ascending
FILL = 88.0                                     # the missing note is given its place
RUN0 = 95.0                                     # the whole scale rings, quick

# staff geometry (treble clef). y measured in staff-line gaps from the middle line.
SCX = 0.50 * W; SW = 0.70 * W; SY = 0.315 * H; LG = 25.0
SLX = SCX - SW / 2; SRX = SCX + SW / 2          # staff left / right edge (NOT audio SR!)
NX0, NX1 = SLX + 0.235 * SW, SRX - 0.045 * SW   # where the note column starts / ends
# C major on a treble staff, top of head measured in LG from the middle line (B4=0):
YSTEP = [3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0, -0.5]   # C4(ledger) D4 E4 F4 G4 A4 B4 C5
STAFF_COL = (206, 196, 178); NOTE_COL = (236, 226, 205); INKGOLD = (255, 214, 150)

def note_xy(i):
    return NX0 + (NX1 - NX0) * i / 7.0, SY + YSTEP[i] * LG

# glow amount for note i at time ts (0..1); empty=True while it is the missing slot
def note_light(i, ts):
    if i == MISS and ts < FILL:                  # missing: hollow, faint searching flicker
        if 70 <= ts <= FILL:
            return 0.15 + 0.12 * (0.5 + 0.5 * math.sin(ts * 4)), True
        return 0.0, True
    base = 0.0
    pt = PLAY[i]
    if pt <= ts <= pt + 1.2:                      # rings as it is played
        base = max(base, 1.0 - (ts - pt) / 1.2)
    if i == MISS and abs(ts - FILL) < 1.0:        # the moment it returns
        base = max(base, 1.0 - abs(ts - FILL))
    for j in range(8):                            # the final whole-scale run
        rt = RUN0 + j * 0.5
        if j == i and rt <= ts <= rt + 0.8:
            base = max(base, 1.0 - (ts - rt) / 0.8)
    if ts > RUN0 + 5: base = max(base, 0.5)       # stays lit once whole
    return clamp(base), False


CAPS = [
    (2.0, 8.0, "one note was missing\nfrom the song."),
    (9.5, 14.5, "the Keeper went\nlooking for it."),
    (18.0, 23.0, "then — another keeper."),
    (25.0, 31.0, "“do you have it —\nthe missing note?”"),
    (33.0, 39.0, "“it is not mine to give,”\nit answered."),
    (41.0, 48.0, "“but we can find it.\nlay out the scale.”"),
    (50.0, 56.0, "do  re  mi ..."),
    (57.5, 63.0, "... and there —\nsilence."),
    (65.0, 72.0, "the fourth step\nwas empty."),
    (74.0, 81.0, "the missing note:\nFa."),
    (84.0, 92.0, "they gave it back\nits place."),
    (95.0, 103.0, "and the scale\nwas whole again."),
    (106.0, 112.0, "the more you know,\nthe more you observe."),
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


def _clef(d, cx, alpha):
    """A hand-drawn treble (G) clef, belly centred on the G line (SY + LG)."""
    gy = SY + LG                                      # G4 line
    col = STAFF_COL + (alpha,)
    def curve(pts, w):                                # smooth polyline through anchor pts
        n = len(pts); out = []
        for k in range(n - 1):
            p0 = pts[max(0, k - 1)]; p1 = pts[k]; p2 = pts[k + 1]; p3 = pts[min(n - 1, k + 2)]
            for s in range(9):
                t = s / 9.0; t2 = t * t; t3 = t2 * t
                x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                           (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                           (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
                y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                           (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                           (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
                out.append((x, y))
        d.line(out, fill=col, width=w, joint="curve")
    L = LG
    pts = [(cx - 0.15 * L, gy + 2.7 * L),             # bottom tail
           (cx - 0.55 * L, gy + 1.9 * L),
           (cx + 0.55 * L, gy + 1.0 * L),
           (cx + 0.95 * L, gy - 0.1 * L),             # belly right
           (cx + 0.30 * L, gy - 0.9 * L),
           (cx - 0.75 * L, gy - 0.4 * L),             # belly left
           (cx - 0.85 * L, gy + 0.7 * L),
           (cx + 0.10 * L, gy + 1.2 * L),             # spiral into centre
           (cx + 0.55 * L, gy + 0.4 * L),
           (cx + 0.15 * L, gy - 1.1 * L),
           (cx - 0.10 * L, gy - 2.7 * L),             # up the stem
           (cx + 0.20 * L, gy - 3.4 * L)]             # top hook
    curve(pts, max(2, int(0.16 * L)))
    d.ellipse([cx - 0.20 * L, gy + 2.6 * L, cx + 0.16 * L, gy + 3.0 * L], fill=col)  # tail dot


def staff_glows(a, ts):
    """Gold glows behind the lit note-heads (into the float buffer, for bloom)."""
    vis = smooth(41, 47, ts)
    if vis < 0.02: return
    for i in range(8):
        lv, empty = note_light(i, ts)
        if lv <= 0.02: continue
        x, y = note_xy(i)
        glow(a, x, y, 12 + 12 * lv, GOLD, (0.25 + 0.95 * lv) * vis)


def staff_draw(im, ts):
    """Draw the staff, clef, time signature, note-heads/stems and solfège lyrics."""
    vis = smooth(41, 47, ts)
    if vis < 0.02: return
    yshift = int((1 - vis) * 26)                      # the staff settles down as it appears
    im2 = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(im2)
    A = int(255 * vis)
    for k in (-2, -1, 0, 1, 2):                       # five staff lines
        yy = SY + k * LG
        d.line([(SLX, yy), (SRX, yy)], fill=STAFF_COL + (int(150 * vis),), width=2)
    _clef(d, SLX + 0.10 * SW, int(190 * vis))
    d.text((SLX + 0.155 * SW, SY - 1.55 * LG), "C", font=font(int(2.7 * LG)),
           fill=STAFF_COL + (int(190 * vis),))        # common time
    for i in range(8):
        x, y = note_xy(i)
        lv, empty = note_light(i, ts)
        if i == 0:                                    # ledger line under low Do (C4)
            d.line([(x - 1.05 * LG, y), (x + 1.05 * LG, y)], fill=STAFF_COL + (int(150 * vis),), width=2)
        rx, ry = 0.62 * LG, 0.46 * LG
        nc = tuple(int(NOTE_COL[j] + (INKGOLD[j] - NOTE_COL[j]) * lv) for j in range(3))
        stem_top = y - 3.0 * LG
        if empty:                                     # missing note: hollow head, faint
            fl = int((70 + 120 * lv) * vis)
            d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=(180, 172, 184, fl), width=3)
        else:
            d.line([(x + rx * 0.85, y - ry * 0.2), (x + rx * 0.85, stem_top)],
                   fill=nc + (int(200 * vis),), width=max(2, int(0.12 * LG)))
            d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=nc + (int((180 + 75 * lv) * vis),))
        bb = d.textbbox((0, 0), NAMES[i], font=SOLF)  # solfège "lyrics" beneath the staff
        lc = (238, 224, 200, int((150 + 100 * lv) * vis)) if not empty else (180, 172, 184, int(140 * vis))
        d.text((x - (bb[2] - bb[0]) / 2, SY + 3.7 * LG), NAMES[i], font=SOLF, fill=lc)
    if yshift:
        im2 = im2.transform(im2.size, Image.AFFINE, (1, 0, 0, 0, 1, -yshift))
    im.paste(im2, (0, 0), im2)


def draw_glyph(im, x, y, ts, t0):
    age = ts - t0
    if 0 <= age <= 1.4:
        al = np.interp(age, [0, 0.3, 1.0, 1.4], [0, 1, 1, 0])
        ImageDraw.Draw(im, "RGBA").text((x, y - 40 - age * 26), "♪", font=GF,
                                        fill=(255, 208, 146, int(220 * al)), anchor="mm")


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

    # the Keeper — searches (walking, world turns), then stops and faces the other
    m_walk = ts < 14
    mfx, mfy0 = ball_feet(AM)
    mlift = smooth(85, 88, ts) * (1 - smooth(91, 93, ts))     # lifts to give the note its place
    mspr, mfoot, mdx, mdy = character(132, "walk" if m_walk else "stand", ts, 1,
                                      lift=0.9 * mlift, lean=0.03 * math.sin(ts * 1.1))
    mx = mfx + mdx; my = mfy0 + mdy

    # the other keeper — waits on the floor, faces the Keeper
    seen = smooth(13, 18, ts)
    ofx, ofy0 = ball_feet(AO)
    ospr, ofoot, odx, ody = character(130, "stand", ts, -1, lean=0.03 * math.sin(ts * 0.9 + 1))
    ox = ofx + odx; oy = ofy0 + ody

    # glows: both keepers + the scale of note-orbs on the ground
    glow(a, mx, my - 0.11 * H, 22, GOLD, 0.9 * (0.9 + 0.1 * math.sin(ts * 3)))
    if seen > 0.02:
        glow(a, ox, oy - 0.11 * H, 21, WARM, seen * 0.85 * (0.9 + 0.1 * math.sin(ts * 3 + 1)))
    staff_glows(a, ts)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(mspr, (int(mx - mspr.size[0] / 2), int(my - mfoot)), mspr)
    if seen > 0.02:
        if seen < 0.995:
            al = ospr.getchannel("A").point(lambda v: int(v * seen)); ospr.putalpha(al)
        im.paste(ospr, (int(ox - ospr.size[0] / 2), int(oy - ofoot)), ospr)
    staff_draw(im, ts)

    # dialogue glyphs above the two keepers
    if 24 <= ts <= 28: draw_glyph(im, mx, my - 0.16 * H, ts, 25.0)     # the Keeper asks
    if 33 <= ts <= 37: draw_glyph(im, ox, oy - 0.16 * H, ts, 33.5)     # the other answers

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

    w(pad([midi(48), midi(55), midi(60)], SDUR - 6, 0.04), 4, 0.5)          # soft drone
    for t in np.arange(2, 14, 1.4): d(softkick(0.09), t, 0.5)                # walking pulse (search)

    # the Keeper asks (rising question, left) ; the other declines (low, right)
    d(piano(midi(64), 1.4, 0.13), 25.0, 0.36); d(piano(midi(69), 2.2, 0.14), 26.4, 0.36)
    d(piano(midi(50), 3.2, 0.12), 34.0, 0.63); d(bass(midi(38), 3.0, 0.06), 34.0, 0.5)
    # the other lays out the scale (a small upward flourish, right)
    for j, m in enumerate([60, 64, 67]): d(piano(midi(m), 1.2, 0.11), 43 + j * 0.5, 0.6)

    # play the scale note by note — Fa (index 3) is SILENT: that gap is the missing note
    for i, m in enumerate(SCALE):
        if i == MISS: continue
        d(piano(midi(m), 2.0, 0.14), PLAY[i], 0.5)
    d(piano(midi(65), 3.4, 0.17), FILL, 0.5)                                 # Fa returns, warm
    w(pad([midi(53), midi(57), midi(60), midi(65)], 8, 0.05), FILL, 0.5)
    for j, m in enumerate(SCALE): d(piano(midi(m), 1.6, 0.12), RUN0 + j * 0.5, 0.5)  # whole scale
    # resolve + walk on
    w(pad([midi(48), midi(55), midi(60), midi(64)], 14, 0.05), 100, 0.5)
    w(bass(midi(36), 14, 0.06), 100, 0.5)
    for t in np.arange(105, 114, 1.4): d(softkick(0.09), t, 0.5)

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
        Image.fromarray(render(a.preview)).save("ep7_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep7_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep7.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep7_silent.mp4", "-i", "ep7.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep7_the_missing_note.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep7_the_missing_note.mp4")


if __name__ == "__main__":
    main()
