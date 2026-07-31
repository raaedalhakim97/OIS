"""
THE OBSERVER WORLD · CHAPTER II · EPISODE 8 — "The Voice Inside the Note"
The Keeper is out of chords: the Silence learned all seven. So this episode gives him
nothing new — it tells him something about what he already had. He holds one low note
and listens *above* it, and the note turns out to contain other notes. Partials 3, 4
and 5 of a low C are G, C and E. He never built the chord in Ep6. He found it.

And this is where the Observer stops being a narrator. The Keeper hears him — a sound
with too much inside it to be a note, from no direction. The Silence never noticed,
because the Silence only ever listened for pitch, and a voice is a shape above a pitch.

Hidden lesson: the harmonic series, and timbre. Rendered at TRUE ratios, not equal
temperament, so the reveal is not a lie. ~2:46.

The narration is baked in here rather than added by tools/narrate.py, because the
Keeper reacts to a specific line at a specific moment. Do not run --story on this one.
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
SDUR = 166.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]; LAV = [206, 190, 244]
VIOLET = [176, 158, 232]; WHITE = [255, 244, 214]; COLD = [150, 176, 214]
STEEL = [96, 118, 156]
CENTER_Y = 0.50
CH, EP, TITLE, LAND = "II", "8", "The Voice Inside the Note", "the Long Dark"
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
FS = font(45); FSM = font(33); TAG = font(29); NAMEF = font(34); TINY = font(27)


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


def ring(a, cx, cy, rad, color, alpha, width=3.0):
    """A hollow circle — used for a partial that is *not* sounding: the shape of an
    absence. This is how the audience sees what the Silence's copy is missing."""
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - rad - 8)); x1 = min(W, int(cx + rad + 8))
    y0 = max(0, int(cy - rad - 8)); y1 = min(H, int(cy + rad + 8))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dd = np.sqrt((xg - cx) ** 2 + (yg - cy) ** 2)
    band = np.exp(-((dd - rad) ** 2) / (2 * width ** 2)) * alpha
    a[y0:y1, x0:x1] += band[..., None] * np.array(color, np.float32)


def darken(a, cx, cy, rad, amount):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 2.5 * rad)); x1 = min(W, int(cx + 2.5 * rad))
    y0 = max(0, int(cy - 2.5 * rad)); y1 = min(H, int(cy + 2.5 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    g = np.exp(-((xg - cx) ** 2 + (yg - cy) ** 2) / (2 * rad ** 2))
    a[y0:y1, x0:x1] *= (1 - g * amount)[..., None]


for s in ("night", "fading_edge"): pl.build_sky(s); pl.planet_base(s)
def theta_of(ts): return 0.035 * ts
def ground_y(x):
    aa = math.asin(clamp((x - CX) / R, -1, 1))
    return CY - R * math.cos(aa) + SINK


KX = 0.30 * W; KY = ground_y(KX)
STONE_X = 0.62 * W                      # the low stone he holds
STONE_Y = ground_y(STONE_X) - 0.03 * H
SUN_X = 1.06 * W                        # the Silence, still off-frame at the open

# ── the harmonic series, as geometry ──────────────────────────────────────────
# Pitch is logarithmic, so height must be too: partial k sits log2(k) octaves above the
# fundamental. That makes the picture obey the same maths as the sound.
OCT_PX = 0.108 * H
PARTIALS = [2, 3, 4, 5]
P_LABEL = {2: "×2   an octave", 3: "×3   a fifth above", 4: "×4   two octaves",
           5: "×5   a major third"}
P_T0 = 58.0                             # first partial rises
P_STEP = 5.4


def partial_xy(k):
    return (STONE_X + 0.055 * W * math.log2(k), STONE_Y - OCT_PX * math.log2(k))


def partial_amt(k, ts):
    """How present partial k is: rises in turn, then holds."""
    i = PARTIALS.index(k)
    t0 = P_T0 + i * P_STEP
    return smooth(t0, t0 + 1.5, ts)


# where the three that matter go when they collapse into the chord he knows
COLLAPSE = {4: 0, 5: 2, 3: 4}           # C -> Do, E -> Mi, G -> Sol
C_T0, C_T1 = 82.0, 88.0

# the Silence copies the fundamental only
COPY_T0 = 98.0
LOUD_T0 = 118.0
CLOSE_T0 = 136.0

SEVEN = [[0, 2, 4], [1, 3, 5], [2, 4, 6], [3, 5, 7], [4, 6, 1], [5, 7, 2], [6, 1, 3]]

STORY_CAPS = [
    (1.2, 5.4, "he had seven chords."),
    (6.2, 9.6, "the dark had learned\nall seven."),
    (21.0, 24.4, "so he stopped playing."),
    (35.0, 38.6, "and something spoke\nthat was not a note."),
    (50.0, 53.4, "he tried to copy it."),
    (54.0, 57.0, "he could not."),
    (64.0, 67.4, "so he held one sound —"),
    (72.0, 75.0, "and listened above it."),
    (89.0, 93.0, "the chord was already\ninside the note."),
    (106.0, 109.4, "the dark took the pitch."),
    (127.0, 131.0, "and missed everything\nstanding on it."),
    (145.0, 149.0, "it can copy what you play."),
    (150.0, 154.0, "not what you are made of."),
    (156.4, 159.4, "it cost him\nmost of his light."),
]

# Only the beats with no narration survive as written captions. Everything Alan says is
# now on screen word for word, timed against his own waveform — the screen and the voice
# must not tell the audience two different things.
# "he could not" and "something spoke that was not a note" were dropped: Alan says both
# beats himself now, and a caption repeating him in different words is the exact problem
# this replaces. Only the moment he never narrates stays written.
STORY_ONLY = {"it cost him\nmost of his light."}

_CAPS = None


def CAPS_():
    """Captions: Alan's exact words, plus the few silent beats."""
    global _CAPS
    if _CAPS is None:
        extra = [c for c in STORY_CAPS if c[2] in STORY_ONLY]
        _CAPS = subs.build(ALAN, alan_sigs(), SR, extra=extra)
    return _CAPS

# Alan. Baked in, because the Keeper answers the line at 34.
ALAN = [
    (1.0,   "Every note you have ever heard was hiding other notes inside it."),
    (20.5,  "He had seven chords. The dark had learned all seven."),
    (34.0,  "So I said his name. And for the first time, somebody in this world heard me."),
    (49.0,  "He tried to copy my voice, and he couldn't. A voice is not one note."),
    (63.0,  "So he held the lowest sound he had, and listened above it."),
    (71.0,  "Twice the speed, an octave. Three times, a fifth. Four, five."),
    # the picture lands this one. he only has to name it.
    (88.5,  "He never built that chord. He found it."),
    (105.0, "Then the dark copied the note."),
    (126.0, "And missed everything standing on top of it."),
    (144.0, "It can copy what you play. It cannot copy what you are made of."),
]

OBS = [(30.0, "the same", "urgent", 0), (46.0, "who are you", "calm", 0),
       (57.0, "what is it", "calm", 0), (84.0, "i hear you", "calm", 0),
       (101.0, "we are connected", "confident", 0), (122.0, "no", "fear", -12),
       (152.0, "i am here", "confident", 0)]

BLINKS = [(13.0, 0.24, 0.08, 0.38, 1.0),
          (27.0, 0.22, 0.07, 0.34, 0.9),
          (34.6, 0.40, 0.14, 0.55, 1.0),      # the moment he hears the voice
          (56.5, 0.20, 0.06, 0.30, 0.8),
          (81.0, 0.12, 0.04, 0.18, 0.45),
          (97.0, 0.24, 0.08, 0.38, 1.0),
          (117.0, 0.14, 0.05, 0.20, 0.5),
          (135.0, 0.26, 0.09, 0.40, 1.0),
          (155.0, 0.30, 0.10, 0.44, 1.0),
          (160.5, 0.85, 0.30, 1.10, 1.0)]


# ── the camera ───────────────────────────────────────────────────────────────
# Short-form retention wants a visual change every 1.5-2s. This world is ambient and
# fast cutting would wreck it, so the change comes from a moving camera instead: slow
# pushes that reset attention without breaking the calm, and focus zooms that go and
# look at whichever tone is sounding. Titles are drawn after the move, so text stays
# crisp and still while the world drifts behind it.
#
# (t, zoom, centre x as fraction of W, centre y as fraction of H)
CAM = [
    (0.0,   1.02, 0.34, 0.62), (12.0,  1.14, 0.30, 0.60),
    (14.5,  1.06, 0.46, 0.52),
    (17.0,  1.13, 0.52, 0.50),                              # drift out toward the dark
    (20.0,  1.10, 0.62, 0.55),                              # the echo comes back
    (24.0,  1.04, 0.44, 0.54),
    (33.0,  1.10, 0.30, 0.58), (36.5,  1.26, 0.29, 0.60),   # he hears the voice
    (43.0,  1.16, 0.32, 0.58),
    (48.0,  1.18, 0.52, 0.66), (55.0,  1.10, 0.58, 0.68),   # the thin note
    (57.5,  1.30, 0.60, 0.70),                              # down onto the stone
]
# each partial gets its own look: the camera climbs the ladder with the sound
for _i, _k in enumerate(PARTIALS):
    _t = P_T0 + _i * P_STEP
    _x, _y = partial_xy(_k)
    CAM += [(_t + 0.5, 1.34, _x / W, _y / H), (_t + 3.6, 1.24, _x / W, (_y / H) - 0.02)]
CAM += [
    (C_T0 - 0.6, 1.30, 0.62, 0.58),
    (C_T1 + 1.0, 1.00, 0.50, 0.42),                         # pull out to the whole staff
    (96.0, 1.06, 0.50, 0.44),
    (COPY_T0 + 1.5, 1.22, 0.50, 0.38),                      # in on the hollow rings
    (112.0, 1.14, 0.56, 0.44),
    (115.5, 1.06, 0.42, 0.40),                              # it does not understand
    (LOUD_T0 + 2.0, 1.24, 0.70, 0.60),                      # its copy, getting louder
    (132.0, 1.06, 0.44, 0.56),
    (CLOSE_T0 + 2.0, 1.20, 0.30, 0.60),                     # his answer
    (146.0, 1.12, 0.38, 0.54),                              # one last look at him
    (150.0, 1.02, 0.44, 0.50),
    (157.0, 1.16, 0.30, 0.60),                              # the cost, up close
    (SDUR, 1.02, 0.44, 0.52),
]
CAM.sort(key=lambda r: r[0])


def cam_at(ts):
    """Interpolated camera, plus a slow breath so the frame is never quite still."""
    z = CAM[0][1]; cx = CAM[0][2]; cy = CAM[0][3]
    for i in range(len(CAM) - 1):
        t0, z0, x0, y0 = CAM[i]; t1, z1, x1, y1 = CAM[i + 1]
        if t0 <= ts <= t1:
            u = smooth(t0, t1, ts)
            z = lerp(z0, z1, u); cx = lerp(x0, x1, u); cy = lerp(y0, y1, u)
            break
    else:
        if ts > CAM[-1][0]:
            z, cx, cy = CAM[-1][1], CAM[-1][2], CAM[-1][3]
    z *= 1.0 + 0.006 * math.sin(ts * 0.31)                  # breath
    cx += 0.004 * math.sin(ts * 0.23 + 1.1)
    cy += 0.003 * math.sin(ts * 0.19)
    return z, cx, cy


def cam_box(z, cx, cy):
    """The crop rectangle, kept inside the frame."""
    bw, bh = W / z, H / z
    x0 = min(max(cx * W - bw / 2, 0.0), W - bw)
    y0 = min(max(cy * H - bh / 2, 0.0), H - bh)
    return x0, y0, bw, bh


def to_screen(x, y, box):
    """Scene coordinates -> screen, so labels can be drawn after the move and stay sharp."""
    x0, y0, bw, bh = box
    return (x - x0) * (W / bw), (y - y0) * (H / bh)


# ── Alan, driving the picture ────────────────────────────────────────────────
# The narration is not a layer on top; it moves the world. His actual speech waveform
# is turned into an envelope, and the light answers it syllable by syllable. When he
# talks, the frame breathes with him — which is what makes the Keeper turning toward
# him at 34 read as a reaction to something really there.
_SIGS = None
_ENV = None
ENV_HZ = 100.0


def alan_sigs():
    """Alan's lines, synthesized once and shared by the picture and the mix."""
    global _SIGS
    if _SIGS is None:
        import narrate as N
        _SIGS = [(t, N.voiced(s, "alan")) for (t, s) in ALAN]
    return _SIGS


def alan_env(ts):
    """How loudly Alan is speaking at story time ts, 0..1."""
    global _ENV
    if _ENV is None:
        n = int(SDUR * ENV_HZ) + 4
        e = np.zeros(n, np.float32)
        step = int(SR / ENV_HZ)
        for (t, sig) in alan_sigs():
            mag = np.abs(sig)
            k = len(mag) // step
            if k < 1: continue
            block = mag[:k * step].reshape(k, step).max(1)
            i0 = int(t * ENV_HZ)
            j = min(n, i0 + k)
            e[i0:j] = np.maximum(e[i0:j], block[:j - i0])
        # a short release so the light does not flicker between syllables
        for i in range(1, n):
            e[i] = max(e[i], e[i - 1] * 0.90)
        _ENV = e / (e.max() + 1e-9)
    i = int(clamp(ts, 0, SDUR - 0.02) * ENV_HZ)
    return float(_ENV[min(i, len(_ENV) - 1)])


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


def caption_on(ts):
    """How strongly a caption is showing — labels must not fight it for the same band."""
    v = 0.0
    for (s, e, _t) in CAPS_():
        if s <= ts <= e:
            v = max(v, float(np.interp(ts, [s, s + 0.5, e - 0.5, e], [0, 1, 1, 0])))
    return v


def draw_partial_labels(im, ts, box, seen):
    """Name each partial as it arrives, beside its light — following the light through
    the camera move, so the label stays attached to the tone it names."""
    if not (P_T0 - 1 <= ts <= C_T0 + 2): return
    d = ImageDraw.Draw(im, "RGBA")
    for k in PARTIALS:
        i = PARTIALS.index(k)
        t0 = P_T0 + i * P_STEP
        f = smooth(t0, t0 + 0.9, ts) * (1 - smooth(C_T0, C_T0 + 1.6, ts))
        if f < 0.03 or k not in seen: continue
        x, y = to_screen(seen[k][0], seen[k][1], box)
        if not (-60 < x < W and -40 < y < H + 40): continue
        # the caption owns the middle of the frame. A label in that band does not
        # compete at reduced opacity — it gets out of the way completely.
        near = 1.0 - clamp(abs(y - CENTER_Y * H) / 165.0)
        con = caption_on(ts)
        if near > 0.45 and con > 0.25: continue
        f *= 1.0 - near * con
        if f < 0.03: continue
        tx = x + 34
        if tx > W - 300: tx = x - 34                   # flip inboard near the edge
        d.text((tx + 2, y - 2), P_LABEL[k], font=TINY, fill=(0, 0, 0, int(150 * f)),
               anchor="lm" if tx > x else "rm")
        d.text((tx, y - 4), P_LABEL[k], font=TINY, fill=(226, 220, 208, int(220 * f)),
               anchor="lm" if tx > x else "rm")


def draw_chord_name(im, ts):
    f = smooth(C_T1, C_T1 + 1.0, ts) * (1 - smooth(COPY_T0 - 2, COPY_T0, ts))
    if f < 0.03: return
    d = ImageDraw.Draw(im, "RGBA")
    for (s, yy, fnt) in [("Do  Mi  Sol", SY + 5.4 * LG, NAMEF),
                         ("it was already in there", SY + 6.7 * LG, TINY)]:
        bb = d.textbbox((0, 0), s, font=fnt); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx + 2, yy + 2), s, font=fnt, fill=(0, 0, 0, int(140 * f)))
        d.text((xx, yy), s, font=fnt, fill=(WARM[0], WARM[1], WARM[2], int(235 * f)))


def end_card(im, ts):
    if ts < 161.0: return
    d = ImageDraw.Draw(im, "RGBA")
    fade = np.interp(ts, [161.0, 161.9, 163.4, 164.8], [0, 1, 1, 0])
    for (ln, yy) in [("the more you know,", 0.455), ("the more you observe.", 0.492)]:
        bb = d.textbbox((0, 0), ln, font=FSM); xx = (W - (bb[2] - bb[0])) // 2
        d.text((xx, int(yy * H)), ln, font=FSM, fill=(238, 232, 220, int(235 * fade)))
    tg = "to be continued"
    bb = d.textbbox((0, 0), tg, font=TAG); xx = (W - (bb[2] - bb[0])) // 2
    d.text((xx, int(0.552 * H)), tg, font=TAG, fill=(202, 194, 182, int(190 * fade)))


def story(ts):
    scene = "night" if ts < 132 else "fading_edge"
    a = pl.build_sky(scene).copy()
    base, mask = pl.planet_base(scene)
    a[mask] = base[mask]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta_of(ts), scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)
    a *= (1 - 0.16 * (1 - smooth(CLOSE_T0, CLOSE_T0 + 8, ts)))

    # ── the voice: it has no position, so it cannot be drawn as a point ──────────
    # Every other light in this world comes from somewhere. This one lifts the whole
    # frame and closes in from the edges — the Observer, who is not standing anywhere.
    voice = alan_env(ts)                               # his real waveform, not a guess
    heard = smooth(34.0, 35.4, ts)                     # the one he actually notices
    if voice > 0.02:
        a *= (1.0 + 0.055 * voice)
        for i in range(5):
            # the rings breathe outward on every syllable he speaks
            r = (0.28 + i * 0.13) * W + 26 * voice
            ring(a, CX, 0.42 * H, r, WHITE, 0.022 * voice * (1 - i * 0.14), width=26)
        if heard > 0.05:                               # once he can hear it, it has weight
            glow(a, CX, 0.42 * H, 260, WHITE, 0.012 * voice * heard)

    # ── the Silence ─────────────────────────────────────────────────────────────
    arrive = smooth(COPY_T0 - 8, COPY_T0, ts)
    sx = lerp(SUN_X, 0.86 * W, arrive)
    sy = ground_y(sx)
    if arrive > 0.02:
        darken(a, sx, sy - 0.035 * H, 54 + 26 * smooth(LOUD_T0, LOUD_T0 + 10, ts),
               0.86 * arrive)
        glow(a, sx, sy - 0.035 * H, 13, STEEL, 0.30 * arrive)

    # ── the Keeper ──────────────────────────────────────────────────────────────
    hold = smooth(56.0, 58.0, ts) * (1 - smooth(C_T0, C_T0 + 2, ts))
    lift = max(0.5 * smooth(14.0, 15.2, ts) * (1 - smooth(20.0, 21.4, ts)),
               0.95 * hold,
               0.85 * smooth(CLOSE_T0, CLOSE_T0 + 1.6, ts))
    face = -1 if 34.6 <= ts < 56.0 else 1              # he turns toward the voice
    # the light he is holding does not turn with him instantly — it swings a beat late
    swing = 0.0
    for tt in (34.6, 56.0):
        swing += 26.0 * math.exp(-max(0.0, ts - tt) * 2.1) * math.sin((ts - tt) * 7.0) \
                 * (1.0 if ts >= tt else 0.0)
    kspr, kfoot, kdx, kdy = character(146, "stand", ts, face,
                                      lift=clamp(lift), lean=fl.idle_sway(ts))
    # he gives his own light to answer, and does not get it back. this is the price the
    # chapter has been avoiding, and what Ep10 finally collects.
    spend = smooth(153.0, 158.0, ts)
    klit = (0.85 + 0.15 * hold) * (1.0 - 0.74 * spend)
    LX, LY = KX + kdx + swing, KY + kdy - abs(swing) * 0.22
    glow(a, LX, LY, (22 + 8 * heard * (1 - smooth(56, 58, ts))) * (1 - 0.45 * spend),
         GOLD, klit)

    # ---- every source that can light something else ----
    lights = [(LX, LY, 430 * (1 - 0.4 * spend), GOLD, 0.90 * klit)]

    # ── the seven spent chords, at the open ─────────────────────────────────────
    spent = 1 - smooth(10.0, 13.0, ts)
    modes = ["full"] * 8
    glows = [0.14 + 0.10 * spent] * 8
    if spent > 0.02:
        k = int(clamp((ts - 1.6) / 1.15, 0, 6.99))
        for dg in SEVEN[k]:
            glows[dg] = max(glows[dg], 0.30 * spent)

    # ── he plays the chord; the dark returns it identical ───────────────────────
    play = smooth(14.6, 15.4, ts) * (1 - smooth(18.0, 19.2, ts))
    ech = smooth(18.6, 19.4, ts) * (1 - smooth(22.0, 23.4, ts))
    for dg in (0, 2, 4):
        glows[dg] = max(glows[dg], 0.72 * play, 0.55 * ech)
    if ech > 0.05:
        glow(a, 0.90 * W, ground_y(0.90 * W) - 0.05 * H, 20, COLD, 0.30 * ech)

    # ── one thin note, trying to be a voice ────────────────────────────────────
    thin = smooth(48.6, 49.4, ts) * (1 - smooth(53.0, 55.0, ts))
    if thin > 0.05:
        glows[0] = max(glows[0], 0.6 * thin)
        glow(a, STONE_X, STONE_Y, 11, GOLD, 0.5 * thin)

    # ── the reveal: the fundamental, and what stands on it ─────────────────────
    fund = smooth(56.5, 58.0, ts) * (1 - smooth(C_T0, C_T0 + 2.0, ts))
    fund = max(fund, smooth(CLOSE_T0, CLOSE_T0 + 1.4, ts))
    if arrive > 0.5 and ts < CLOSE_T0:
        fund = max(fund, 0.55 * arrive)                # the Silence holds the pitch too
    if fund > 0.02:
        glow(a, STONE_X, STONE_Y, 15 + 6 * fund, GOLD, 0.85 * fund)
        glow(a, STONE_X, STONE_Y, 44, GOLD, 0.14 * fund)
        lights.append((STONE_X, STONE_Y, 360, WARM, 0.75 * fund))

    coll = smooth(C_T0, C_T1, ts)
    seen = {}                                          # where each tone ended up, for its label
    # the chord dies as the Silence takes the pitch, and he brings it back at the close
    alive = 1 - smooth(COPY_T0 - 1.2, COPY_T0 + 0.8, ts)
    back = smooth(CLOSE_T0 + 0.5, CLOSE_T0 + 3.0, ts)
    for k in PARTIALS:
        amt = partial_amt(k, ts) * alive
        amt = max(amt, back)
        px, py = partial_xy(k)
        # a sounding tone is never still: higher partials ride faster, as they do in air
        px += fl.bob(ts, 7.0 + 1.4 * k, f1=0.13 * k, f2=0.31 * k, ph=k * 1.7)
        py += fl.bob(ts, 5.0 + 1.0 * k, f1=0.17 * k, f2=0.24 * k, ph=k * 0.9)
        if k in COLLAPSE and coll > 0.01:              # 3, 4 and 5 become Do Mi Sol
            tx, ty = SLOT[COLLAPSE[k]]
            # they do not travel in a straight line at the same speed: each leaves a
            # beat after the last, arcs, and overshoots a little before it settles.
            order = {4: 0, 5: 1, 3: 2}[k]
            u = clamp((ts - (C_T0 + order * 0.42)) / (C_T1 - C_T0 - 0.9))
            e = fl.back_out(u) if u > 0 else 0.0
            ax, ay = lerp(px, tx, e), lerp(py, ty, e)
            ay -= 96 * math.sin(math.pi * clamp(u)) * (1 - 0.4 * order)   # the arc
            px, py = ax, ay
            coll_k = e
            if coll_k > 0.55:
                glows[COLLAPSE[k]] = max(glows[COLLAPSE[k]],
                                         0.75 * coll_k * max(alive, back))
        seen[k] = (px, py)
        if amt > 0.03:
            glow(a, px, py, 9 + 4 * amt, WARM, 0.75 * amt)
            glow(a, px, py, 26, WARM, 0.13 * amt)
        if k in COLLAPSE and COPY_T0 - 0.5 <= ts < CLOSE_T0 + 0.5:
            # the Silence's copy: the partials become rings — present as shapes, absent
            # as sound. this is the whole episode, in one gesture, and it has to be seen.
            e = smooth(COPY_T0 + 0.4, COPY_T0 + 2.2, ts) * (1 - back)
            tx, ty = SLOT[COLLAPSE[k]]
            ring(a, tx, ty, 15, STEEL, 0.60 * e, width=3.0)
            ring(a, tx, ty, 15, COLD, 0.22 * e, width=7.0)

    if COPY_T0 <= ts < CLOSE_T0:                       # its copy: bright pitch, nothing on it
        louder = smooth(LOUD_T0, LOUD_T0 + 12, ts)
        glow(a, STONE_X, STONE_Y, 13 + 20 * louder, COLD, 0.40 + 0.42 * louder)
        lights.append((STONE_X, STONE_Y, 300 + 120 * louder, COLD, 0.55 + 0.35 * louder))

    # motes lifting off the ground — the world is never a still picture
    for i in range(9):
        ph = i * 0.7
        u = ((ts * 0.055 + i * 0.111) % 1.0)
        mx = (0.16 + 0.085 * i) * W + 40 * math.sin(ts * 0.21 + ph)
        my = ground_y(mx) - u * 0.30 * H
        al = 0.30 * math.sin(math.pi * u) * (0.5 + 0.5 * math.sin(ts * 0.7 + ph))
        if al > 0.01:
            glow(a, mx, my, 5, WARM, al)

    # the ground catches the light it is standing under, and the Keeper throws a shadow
    lg.spill(a, mask, lights, amount=0.55)
    lg.cast(a, KX, KY, lights, ground_y, length=2.0, amount=0.40)
    fg.motes(a, ts, cam_at(ts), glow, WARM, n=5)

    vis = smooth(1.0, 4.5, ts)
    staff.glows_into(a, vis, glows, modes)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    kspr = lg.rim(kspr, KX, KY, lights, width=5, gain=1.05)
    im.paste(kspr, (int(KX - kspr.size[0] / 2), int(KY - kfoot)), kspr)
    if arrive > 0.02:
        sspr, sfoot, _, _ = character(178, "stand", ts, -1, lean=0.02 * math.sin(ts * 0.5))
        sspr = lg.rim(sspr, sx, sy, lights, width=4, gain=0.55)   # it catches less
        al = sspr.getchannel("A").point(lambda v: int(v * clamp(arrive)))
        sspr = sspr.copy(); sspr.putalpha(al)
        im.paste(sspr, (int(sx - sspr.size[0] / 2), int(sy - sfoot)), sspr)
    staff.draw(im, vis, modes, glows)

    # ── move the camera, then lay the words on top ──────────────────────────────
    # Text is drawn after the crop so it stays sharp and stationary while the world
    # drifts behind it — the way titles sit above a moving shot in a real edit.
    z, ccx, ccy = cam_at(ts)
    box = cam_box(z, ccx, ccy)
    if z > 1.001:
        x0, y0, bw, bh = box
        im = im.resize((W, H), Image.LANCZOS,
                       box=(x0, y0, x0 + bw, y0 + bh))
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    fg.draw(im, ts, (z, ccx, ccy), strength=1.0)
    draw_partial_labels(im, ts, box, seen)
    draw_chord_name(im, ts)
    draw_caption(im, ts)
    end_card(im, ts)

    frame = np.asarray(im.convert("RGB"), np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    eye.apply_lids(frame, eye.blink_amount(ts, BLINKS))
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


# ── sound ────────────────────────────────────────────────────────────────────
F0 = midi(36)                                          # C2, 65.41 Hz


def sine(freq, dur, amp, decay=1.0):
    """A single partial: one frequency, no harmonics of its own. The Silence's copy is
    made of this, which is exactly why it sounds hollow."""
    t = np.linspace(0, dur, int(dur * SR), False, dtype=np.float32)
    env = np.minimum(1.0, t / 0.10) * np.exp(-t * decay)
    return (np.sin(2 * np.pi * freq * t) * env * amp).astype(np.float32)


def build_audio(bed_only=False):
    import narrate as N
    n = int(DUR * SR)
    dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
    wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
    A = TITLE_DUR
    def d(s, at, pan=0.5): add(dL, s * (1 - pan), A + at); add(dR, s * pan, A + at)
    def w(s, at, pan=0.5): add(wL, s * (1 - pan), A + at); add(wR, s * pan, A + at)
    K = dict(register=0, pan=0.38); SH = dict(register=0, pan=0.60)

    w(pad([midi(45), midi(52), midi(57), midi(60)], 34, 0.036), 1, 0.5)
    w(bass(midi(33), 18, 0.042), 1, 0.5)

    # the seven chords he already has, played spent and quick — a defeat, not a fanfare
    for i, degs in enumerate(SEVEN):
        t0 = 1.8 + i * 1.15
        for j, dg in enumerate(degs):
            d(piano(midi(PITCH[dg]), 1.6, 0.045), t0 + j * 0.06, 0.34 + 0.08 * j)

    # he plays Do Mi Sol; the dark hands it back identical
    for j, dg in enumerate((0, 2, 4)):
        d(piano(midi(PITCH[dg]), 3.4, 0.105), 14.8 + j * 0.20, 0.36 + 0.10 * j)
    for j, dg in enumerate((0, 2, 4)):
        d(piano(midi(PITCH[dg]), 3.0, 0.080), 18.8 + j * 0.20, 0.68)
    say(d, "the same", 30.0, style="urgent", **SH)

    # he cannot copy a voice, so he plays one bare note
    say(d, "who are you", 46.0, style="calm", **K)
    d(piano(midi(48), 3.0, 0.10), 49.0, 0.44)
    say(d, "what is it", 57.0, style="calm", **K)

    # ── the reveal. true ratios: 2x octave, 3x fifth, 4x octave, 5x major third ──
    d(sine(F0, 30.0, 0.115, 0.055), 56.8, 0.5)          # the fundamental, held
    w(pad([F0, F0 * 2], 16.0, 0.030), 56.8, 0.5)
    for i, k in enumerate(PARTIALS):
        t0 = P_T0 + i * P_STEP
        amp = [0.100, 0.078, 0.064, 0.054][i]
        # each partial must still be sounding when the next one arrives, and all four
        # when the last does — the picture holds every light, so the sound has to hold
        # every voice. A short decay here would show four and play one.
        d(sine(F0 * k, 34.0, amp, 0.050), t0 + 0.15, 0.42 + 0.045 * k)
    say(d, "i hear you", 84.0, style="calm", **K)

    # they collapse into the chord he knew: 4x, 5x, 3x = C, E, G
    for i, k in enumerate((4, 5, 3)):
        d(sine(F0 * k, 11.0, 0.082, 0.11), C_T0 + 0.6 + i * 0.10, 0.44 + 0.04 * i)
    d(sine(F0, 12.0, 0.100, 0.09), C_T0 + 0.6, 0.5)
    w(pad([F0 * 4, F0 * 5, F0 * 3], 10.0, 0.048), C_T0 + 0.6, 0.5)
    w(bass(midi(36), 10.0, 0.048), C_T0 + 0.6, 0.5)
    say(d, "we are connected", 101.0, style="confident", **K)

    # ── the Silence's copy: the fundamental alone. right pitch, nothing above it ──
    d(sine(F0, 18.0, 0.230, 0.045), COPY_T0, 0.58)
    d(sine(F0, 18.0, 0.045, 0.045), COPY_T0 + 0.02, 0.58)
    d(softkick(0.10), COPY_T0, 0.6)
    say(d, "no", 122.0, style="fear", register=-12, pan=0.6)
    # louder is not it: the same hollow tone, bigger
    d(sine(F0, 16.0, 0.300, 0.035), LOUD_T0, 0.56)
    d(sine(F0 * 2, 16.0, 0.030, 0.05), LOUD_T0 + 6.0, 0.56)   # it gropes for one partial
    for t in np.arange(LOUD_T0, LOUD_T0 + 14, 2 * BEAT):
        d(softkick(0.075), t, 0.6)

    # ── he answers with the whole note: fundamental and everything standing on it ──
    d(sine(F0, 20.0, 0.115, 0.040), CLOSE_T0, 0.46)
    for i, k in enumerate([2, 3, 4, 5, 6, 8]):
        d(sine(F0 * k, 17.0, 0.070 / (1 + 0.35 * i), 0.075), CLOSE_T0 + 0.10 * i, 0.44 + 0.02 * i)
    d(piano(midi(60), 8.0, 0.085), CLOSE_T0 + 1.2, 0.5)
    d(piano(midi(64), 8.0, 0.075), CLOSE_T0 + 1.5, 0.52)
    d(piano(midi(67), 8.0, 0.075), CLOSE_T0 + 1.8, 0.48)
    w(pad([midi(36), midi(48), midi(55), midi(60), midi(64)], 18, 0.052), CLOSE_T0, 0.5)
    w(bass(midi(36), 18, 0.055), CLOSE_T0, 0.5)
    say(d, "i am here", 152.0, style="confident", **K)
    # and then he gives it away. the light goes out of the mix as it goes out of him.
    say(d, "i give you this", 156.2, style="whisper", **K)
    w(pad([midi(48), midi(55), midi(60)], 9.0, 0.030), 156.0, 0.5)
    d(piano(midi(48), 7.0, 0.055), 158.6, 0.44)
    w(bass(midi(29), 8.0, 0.034), 158.0, 0.5)

    dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
    wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
    mix = master(dry * 0.92 + wet)
    fi, fo = int(0.6 * SR), int(4 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]

    # Alan, laid over the finished bed with ducking — the Observer, in the room.
    # Shared with the picture, so the light answers the exact waveform you hear.
    if bed_only:
        return mix                                     # for measuring the voice against
    items = [(A + t, sig) for (t, sig) in alan_sigs()]
    # The bed is dense — pads and held sines — so a gentle duck left Alan sitting at or
    # even below the music, and speech recognition found no speech to transcribe. It has
    # to come down hard under him and he has to come up. Measured, not guessed: the
    # target is roughly +12 dB of voice over bed.
    return N.lay(mix, items, level=1.22, target_db=13.0, keep=0.14)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, default=None)
    ap.add_argument("--audio-only", action="store_true")
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save(f"ep19_prev_{a.preview:.0f}.png")
        print("preview saved"); return
    if a.audio_only:
        write_wav("ep19.wav", build_audio()); print("audio only -> ep19.wav"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep19_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep19.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep19_silent.mp4", "-i", "ep19.wav",
                    "-c:v", "libx264", "-crf", "27", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "ch2_ep8_the_voice_inside_the_note.mp4"], check=True, capture_output=True)
    print("Done -> ch2_ep8_the_voice_inside_the_note.mp4")


if __name__ == "__main__":
    main()
