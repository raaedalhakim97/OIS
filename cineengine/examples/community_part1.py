"""
THE COMMUNITY · part 1 — "The Perfect Fit"
Every keeper is a musical note. A triad (F–A–C) find each other and bond — a
thread of light + a warm chord. An outsider, E-flat, rings out and CLASHES: it
makes a tritone with the A (real tension), so it sits alone and keeps looking.
Then the community turns to look at IT — the chord opens to F7, and that same
clashing tritone becomes the soul of the richer chord. The odd note completes
them. Night field, calm gusting soundscape. ~49s vertical.

Seeds the series metaphor: consonance = belonging; you're not wrong, you just
haven't found your chord yet.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets

W, H = 1080, 1920
FPS = 24
DUR = 49.0
GROUND = 0.82 * H
fx = FX(W, H)

GOLD = [255, 200, 130]
COOL = [168, 194, 255]        # the outsider's pale light, until it finds its place


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
FS = font(46); FSM = font(34)


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


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([7, 9, 24], np.float32) * (1 - t)
            + np.array([17, 18, 40], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(18, 20, 38))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(21, 23, 42))
    d.rectangle([0, int(GROUND), W, H], fill=(14, 15, 30))
    rr = np.random.default_rng(7)
    for _ in range(130):
        gx = rr.integers(0, W); gh = rr.integers(14, 46); sway = rr.uniform(-8, 8)
        d.line([(gx, H), (gx + sway, H - gh)], fill=(9, 12, 20), width=2)
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(11)
STARX = _r.integers(0, W, 150); STARY = _r.integers(0, int(GROUND * 0.9), 150)
STARB = _r.uniform(0.3, 1.0, 150); STARPH = _r.uniform(0, 6.28, 150)
# faint distant community — unlit dots that imply a bigger crowd
DFAR = [(0.10, 0.70), (0.18, 0.74), (0.83, 0.70), (0.92, 0.73), (0.40, 0.68), (0.60, 0.68)]

# the keepers: (x-frac, feet-y-frac, size, midi-note, enter-time)
F_, A_, C_, E_ = 0, 1, 2, 3
KEEP = [
    dict(x=0.30, y=0.74, sz=118, m=53, enter=1.0),    # F
    dict(x=0.50, y=0.82, sz=140, m=57, enter=3.0),    # A (center, nearest)
    dict(x=0.70, y=0.74, sz=118, m=60, enter=5.0),    # C
    dict(x=0.885, y=0.66, sz=104, m=63, enter=18.5),  # E-flat (the outsider, b7)
]

TEXT = [
    (2.4, 7.6, "everyone here\nis a different note.", FS, 0.13),
    (9.0, 15.6, "some of them just… fit.", FS, 0.13),
    (18.8, 25.0, "and some don't.\nnot yet.", FS, 0.13),
    (27.0, 32.4, "so the world turns\nto look at them.", FS, 0.13),
    (33.6, 41.6, "and the note that didn't fit\nbecomes the reason\nit's beautiful.", FS, 0.13),
    (43.0, 48.6, "the more you know, the more you observe.", FSM, 0.90),
]


def pose_of(i, t):
    """(pose, face, lean, bright, colormix) for keeper i at time t.
    lean drives the 'looking': they lean toward whoever they're bonding with."""
    k = KEEP[i]
    b = smooth(k["enter"], k["enter"] + 1.8, t)                 # fade-in brightness
    sway = 0.045 * math.sin(2 * math.pi * (t - k["enter"]) / 5.0)   # gentle idle sway
    if i == F_:
        lean = sway + 0.10 * smooth(8, 12, t) + 0.06 * smooth(30, 34, t)   # look right→A, then →Eb
        return "stand", 1, lean, b, 0.0
    if i == A_:
        lean = 0.05 * math.sin(2 * math.pi * (t - 3) / 6.0) + 0.08 * smooth(30, 34, t)  # look around, then →Eb
        return "stand", 1, lean, b, 0.0
    if i == C_:
        lean = sway - 0.10 * smooth(8, 12, t) + 0.12 * smooth(30, 34, t)   # look left→A, then →Eb
        return "stand", -1 if t < 30 else 1, lean, b, 0.0
    # E-flat: searching sweep while alone, then settles leaning toward the community
    search = 0.13 * math.sin(2 * math.pi * (t - 19) / 3.4) * (1 - smooth(30, 33, t))
    settle = -0.11 * smooth(31, 35, t)
    warm = smooth(33, 37, t)                                    # pale -> gold as it belongs
    pose = "front" if (20 <= t < 31) else "stand"
    return pose, -1, search + settle, b, warm


def orb_world(i, t):
    p, face, lean, b, warm = pose_of(i, t)
    k = KEEP[i]
    spr, fy, odx, ody = character(k["sz"], p, t, face, lean=lean)
    return (k["x"] * W + odx, k["y"] * H + ody), b, warm, (spr, fy)


def draw_thread(a, p0, p1, bright, t, col=GOLD):
    if bright <= 0.01: return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 0.05 * H   # gentle upward sag
    n = 20
    for i in range(n):
        u = i / (n - 1)
        px, py = bez(p0, (mx, my), p1, u)
        tw = 0.6 + 0.4 * math.sin(t * 4 + i * 0.7)
        glow(a, px, py, 5, col, bright * 0.5 * tw)


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([210, 214, 234])
    for (fx_, fy_) in DFAR:
        glow(a, fx_ * W, fy_ * H, 6, GOLD, 0.05 + 0.03 * math.sin(t + fx_ * 8))

    # gather each keeper's orb + sprite
    orbs = []; sprites = []
    for i in range(len(KEEP)):
        (ox, oy), b, warm, (spr, fy) = orb_world(i, t)
        col = mix3(COOL, GOLD, warm) if i == E_ else GOLD
        orbs.append((ox, oy, b, col))
        sprites.append((spr, fy))

    # bonds (threads) — consonant pairs of the triad, then the outsider joins (F7)
    b_FA = smooth(9, 12, t); b_AC = smooth(11, 14, t); b_FC = smooth(13, 16, t)
    b_out = smooth(33, 37, t)
    pulse = 0.85 + 0.15 * math.sin(t * 2.2)
    draw_thread(a, orbs[F_][:2], orbs[A_][:2], b_FA * pulse, t)
    draw_thread(a, orbs[A_][:2], orbs[C_][:2], b_AC * pulse, t)
    draw_thread(a, orbs[F_][:2], orbs[C_][:2], b_FC * pulse * 0.8, t)
    draw_thread(a, orbs[C_][:2], orbs[E_][:2], b_out * pulse, t, col=mix3(COOL, GOLD, smooth(33, 38, t)))
    draw_thread(a, orbs[A_][:2], orbs[E_][:2], b_out * pulse * 0.7, t, col=mix3(COOL, GOLD, smooth(34, 39, t)))

    # orbs (glow) — the outsider flickers a touch while it clashes (unresolved)
    for i, (ox, oy, b, col) in enumerate(orbs):
        flick = 1.0
        if i == E_ and 20 <= t < 31:
            flick = 0.72 + 0.28 * (0.5 + 0.5 * math.sin(t * 9))   # uneasy, unresolved flicker
        glow(a, ox, oy, 22 + 8 * (i == A_), col, b * 0.95 * flick * (0.92 + 0.08 * math.sin(t * 3 + i)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    order = sorted(range(len(KEEP)), key=lambda i: KEEP[i]["y"])   # far (higher) first
    for i in order:
        spr, fy = sprites[i]
        k = KEEP[i]
        im.paste(spr, (int(k["x"] * W - spr.size[0] / 2), int(k["y"] * H - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt, f, yv) in TEXT:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.7, e - 0.7, e], [0, 1, 1, 0])
            yy = int(H * yv)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=f)
                col = (170, 150, 120, int(180 * fade)) if f is FSM else (234, 231, 224, int(236 * fade))
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f, fill=col)
                yy += int((bb[3] - bb[1]) * 1.5)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.014)
    return frame.clip(0, 255).astype(np.uint8)


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # environment as calm music (gusts with space, owl on chord tones, crickets)
    for at, am, sd, pan in [(1.0, 0.045, 2, 0.4), (20.0, 0.04, 5, 0.6), (36.0, 0.045, 8, 0.5)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.05, 53), 13.0, 0.7); st(owl(0.05, 60), 40.0, 0.35)
    cp = crickets(16.0, 0.006, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 8.0, 0.5)

    # each keeper RINGS its note as it lights up (pan to its position)
    for k, pan in ((KEEP[F_], 0.30), (KEEP[A_], 0.50), (KEEP[C_], 0.70)):
        st(piano(midi(k["m"]), 6.0, amp=0.15), k["enter"] + 0.4, pan)
    # the triad bonds — a warm F-major chord blooms as the threads form
    trip = pad([midi(53), midi(57), midi(60)], 12.0, amp=0.06)
    add(L, trip, 12.0); add(R, np.roll(trip, 400), 12.0)
    # call-and-response: the three answer each other softly once bonded
    st(piano(midi(57), 4.0, amp=0.08), 15.0, 0.5)
    st(piano(midi(60), 4.0, amp=0.07), 16.0, 0.6)

    # the outsider E-flat rings out ALONE — a tritone against the A = real tension.
    # left unresolved (no chord under it), with a faint detuned twin = 'searching'.
    eb = midi(63)
    st(piano(eb, 6.0, amp=0.14), 19.5, 0.86)
    st(piano(eb * 1.004, 5.0, amp=0.06), 20.2, 0.80)          # slightly off = unsettled
    st(piano(midi(57), 5.0, amp=0.07), 21.5, 0.35)            # the A still sounding -> tritone clash
    st(piano(eb, 5.0, amp=0.11), 25.0, 0.86)                  # it calls again, still alone

    # RESOLUTION — the chord opens to F7 (F-A-C-Eb). The very tritone that clashed
    # is now the soul of the chord. Warm, rich, whole.
    f7 = pad([midi(53), midi(57), midi(60), midi(63)], 14.0, amp=0.075)
    add(L, f7, 33.5); add(R, np.roll(f7, 400), 33.5)
    st(piano(eb, 7.0, amp=0.13), 34.0, 0.6)                   # Eb, now warm and belonging
    st(piano(midi(53), 8.0, amp=0.12), 43.0, 0.5)            # settle home on F

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(SR), int(4.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("comm_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("comm_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("comm.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "comm_silent.mp4", "-i", "comm.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "community_part1.mp4"],
                   check=True, capture_output=True)
    print("Done -> community_part1.mp4")


if __name__ == "__main__":
    main()
