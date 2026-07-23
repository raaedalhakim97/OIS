"""
THE COMMUNITY · Chapter 1 — "The Destiny"   (how they meet)
In the beginning, one note, alone. It calls out into the dark — the note made
visible as a ripple of light spreading across the field. Far off, another note
hears it and answers. Though they have never met, they begin walking toward each
other. They meet in the middle; a warm third rings; a thread binds them. Then a
new call sounds in the distance — destiny keeps unfolding. Night field, calm
gusting soundscape, interactive musical steps. ~48s vertical.

Destiny = the note was already calling the one who could answer it.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, step_note, walk_notes, poem_sway

W, H = 1080, 1920
FPS = 24
DUR = 48.0
GROUND = 0.80 * H
fx = FX(W, H)
GOLD = [255, 200, 130]


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1])


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


def ripple(a, cx, cy, R, thk, bright, color=GOLD):
    # the note made visible: a ring of light expanding outward from the caller
    if bright <= 0.01: return
    x0 = max(0, int(cx - R - 3 * thk)); x1 = min(W, int(cx + R + 3 * thk))
    y0 = max(0, int(cy - R - 3 * thk)); y1 = min(H, int(cy + R + 3 * thk))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dist = np.sqrt((xg - cx) ** 2 + (yg - cy) ** 2)
    ring = np.exp(-((dist - R) ** 2) / (2 * thk ** 2)) * bright
    a[y0:y1, x0:x1] += ring[..., None] * np.array(color, np.float32)


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([6, 8, 22], np.float32) * (1 - t)
            + np.array([16, 17, 38], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(17, 19, 36))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(20, 22, 40))
    d.rectangle([0, int(GROUND), W, H], fill=(13, 14, 28))
    rr = np.random.default_rng(7)
    for _ in range(130):
        gx = rr.integers(0, W); gh = rr.integers(14, 46); sway = rr.uniform(-8, 8)
        d.line([(gx, H), (gx + sway, H - gh)], fill=(9, 12, 20), width=2)
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(11)
STARX = _r.integers(0, W, 150); STARY = _r.integers(0, int(GROUND * 0.9), 150)
STARB = _r.uniform(0.3, 1.0, 150); STARPH = _r.uniform(0, 6.28, 150)

# the two who are destined to meet: born apart, walk together
FX0, FX1 = 0.22, 0.42        # the first note (F): starts left, walks in
AX0, AX1 = 0.82, 0.60        # the answer (A): starts right, walks in
FEET = 0.80
SZ = 124
CALLS = [4.0, 6.0]           # F sends its call (ripples emitted)
ANSW = [12.5, 14.5]          # A answers

TEXT = [
    (2.2, 7.4, "in the beginning —\none note. alone.", FS, 0.13),
    (9.2, 14.2, "so it called out\ninto the dark.", FS, 0.13),
    (15.4, 21.2, "and somewhere,\nsomething answered.", FS, 0.13),
    (22.4, 29.4, "they had never met,\nbut they were already\nwalking toward each other.", FS, 0.13),
    (30.6, 36.6, "some meetings feel\nlike they already happened.", FS, 0.13),
    (38.0, 43.4, "one note, calling\nthe one who could answer.", FS, 0.13),
    (44.2, 47.8, "chapter one · the destiny", FSM, 0.90),
]


def keeper_state(who, t):
    if who == "F":
        walk = smooth(16, 30, t)
        x = lerp(FX0, FX1, walk)
        moving = 16 < t < 30
        lean = 0.05 * math.sin(2 * math.pi * (t - 1) / 5.0) + 0.09 * smooth(18, 30, t) + 0.06 * smooth(37, 41, t)
        face = 1
        born = smooth(0.5, 3.0, t)
    else:
        walk = smooth(16, 30, t)
        x = lerp(AX0, AX1, walk)
        moving = 16 < t < 30
        lean = 0.05 * math.sin(2 * math.pi * (t - 12) / 5.0) - 0.09 * smooth(18, 30, t) - 0.04 * smooth(37, 41, t)
        face = -1
        born = smooth(11.5, 14.0, t)
    pose = "walk" if moving else "stand"
    return x, pose, face, lean, born


def orb_of(who, t):
    x, pose, face, lean, born = keeper_state(who, t)
    spr, fy, odx, ody = character(SZ, pose, t, face, lean=lean)
    return (x * W + odx, FEET * H + ody), (spr, fy, x), born


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([210, 214, 234])

    (foab, fspr, fborn) = None, None, None
    (foF, fF, fbornF) = orb_of("F", t)
    (foA, fA, fbornA) = orb_of("A", t)

    # F's call: expanding ripples of light from its orb (the note made visible)
    for ct in CALLS:
        if t >= ct:
            age = t - ct
            R = age * 150.0
            br = 0.5 * math.exp(-age * 0.5) * (1 - smooth(0, 0.4, -age))
            if R < 1.4 * W:
                ripple(a, foF[0], foF[1], R, 16, br)
    # A's answer: ripples back toward F
    for ct in ANSW:
        if t >= ct:
            age = t - ct
            R = age * 150.0
            br = 0.45 * math.exp(-age * 0.5)
            if R < 1.4 * W:
                ripple(a, foA[0], foA[1], R, 16, br)

    # the thread that forms as they meet (destiny binding)
    meet = smooth(28, 33, t)
    if meet > 0.01:
        p0, p1 = foF, foA
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 0.04 * H
        pulse = 0.85 + 0.15 * math.sin(t * 2.2)
        nn = 18
        for i in range(nn):
            u = i / (nn - 1)
            px, py = bez(p0, (mx, my), p1, u)
            glow(a, px, py, 5, GOLD, meet * 0.5 * pulse * (0.6 + 0.4 * math.sin(t * 4 + i)))

    # a NEW call in the distance at the end — destiny keeps unfolding
    ncall = 38.0
    ndc = (0.5 * W, 0.34 * H)
    if t >= ncall:
        age = t - ncall
        glow(a, ndc[0], ndc[1], 10 + 6 * math.sin(t * 3), GOLD, 0.5 * smooth(ncall, ncall + 1.5, t))
        R = age * 120.0
        ripple(a, ndc[0], ndc[1], R, 14, 0.35 * math.exp(-age * 0.5))

    # orbs
    glow(a, foF[0], foF[1], 24, GOLD, fbornF * 0.95 * (0.92 + 0.08 * math.sin(t * 3)))
    glow(a, foA[0], foA[1], 24, GOLD, fbornA * 0.95 * (0.92 + 0.08 * math.sin(t * 3 + 1)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    # paste sprites (only once born, so A appears when it answers)
    for (spr, fy, x), born in ((fF, fbornF), (fA, fbornA)):
        if born > 0.02:
            im.paste(spr, (int(x * W - spr.size[0] / 2), int(FEET * H - fy)), spr)

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

    for at, am, sd, pan in [(1.0, 0.04, 2, 0.4), (20.0, 0.04, 5, 0.6), (36.0, 0.045, 8, 0.5)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.05, 53), 10.0, 0.7); st(owl(0.05, 57), 33.0, 0.4)
    cp = crickets(16.0, 0.006, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 8.0, 0.5)

    # F calls (panned left, where it stands); the call rings out, reverberant
    st(piano(midi(53), 7.0, amp=0.16), 4.0, 0.30)
    st(piano(midi(53), 5.0, amp=0.08), 6.0, 0.30)
    # A answers from the right — a warm third above (call-and-response, destiny)
    st(piano(midi(57), 7.0, amp=0.15), 12.5, 0.72)
    st(piano(midi(57), 5.0, amp=0.08), 14.5, 0.72)

    # interactive musical steps as they walk toward each other (F left, A right)
    walk_notes(st, [17.0, 19.0, 21.0, 23.0, 25.0, 27.0], [53, 55, 57, 55, 53, 57], amp=0.11, base_pan=0.34)
    walk_notes(st, [17.6, 19.6, 21.6, 23.6, 25.6, 27.6], [60, 58, 57, 58, 60, 57], amp=0.11, base_pan=0.66)

    # they meet — a warm F+A third blooms, then answers each other softly
    third = pad([midi(53), midi(57)], 12.0, amp=0.06)
    add(L, third, 29.5); add(R, np.roll(third, 400), 29.5)
    st(piano(midi(53), 4.0, amp=0.09), 31.0, 0.42)
    st(piano(midi(57), 4.0, amp=0.09), 32.0, 0.58)
    # the new distant call — a faint C, high and far (destiny continues)
    st(piano(midi(60), 8.0, amp=0.10), 38.0, 0.5)
    st(piano(midi(53), 8.0, amp=0.11), 44.0, 0.5)     # settle home on F

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
        Image.fromarray(render(a.preview)).save("ch1_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ch1_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ch1.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ch1_silent.mp4", "-i", "ch1.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "community_chapter1.mp4"],
                   check=True, capture_output=True)
    print("Done -> community_chapter1.mp4")


if __name__ == "__main__":
    main()
