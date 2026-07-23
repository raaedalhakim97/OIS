"""
THE OBSERVER WORLD · Chapter 1 — "The Note Between"   (the deeper story)
A Lightkeeper walks the world alone, carrying his note. He finds one whose light
is fading and wants to help — but his note and hers do not agree (a tense whole
step, G against F). He cannot help by being himself alone. So he goes to find the
note between: an accidental, a flat, the outsider the scale left out — B-flat.
He brings it back, and the two clashing notes become a chord: G minor 7, warm and
whole. The fading light blooms. The note that belonged nowhere is the one that
held them together. ~58s vertical, night field, calm gusting soundscape.

Music is literally the story: G + F alone = unresolved; add the flat Bb = Gm7.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, step_note, walk_notes

W, H = 1080, 1920
FPS = 24
DUR = 58.0
GROUND = 0.80 * H
fx = FX(W, H)
GOLD = [255, 200, 130]
COOL = [168, 194, 255]        # the accidental's pale light until it belongs
DIM = [120, 150, 210]         # the fading one's faint, cold light


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
FS = font(45); FSM = font(33)


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
DFAR = [(0.10, 0.71), (0.92, 0.72), (0.50, 0.68)]

FX_ = 0.40; FEET_F = 0.80              # the fading one (F), sits
BBX0, BBX1 = 0.86, 0.80; FEET_B = 0.70  # the accidental (Bb), apart, higher/farther
FEET_K = 0.80

TEXT = [
    (2.0, 7.2, "in the observer world,\nevery soul is a note.", FS, 0.13),
    (8.6, 14.2, "the keeper walked,\ncarrying his.", FS, 0.13),
    (16.4, 22.2, "then he found one\nwhose light was fading.", FS, 0.13),
    (23.8, 30.0, "he offered his note.\nbut they did not agree.", FS, 0.13),
    (31.4, 37.6, "he could not help them\nby being himself alone.", FS, 0.13),
    (38.6, 45.4, "so he went to find\nthe note between —\na flat. an outsider.", FS, 0.12),
    (47.0, 54.2, "and the note that belonged nowhere\nwas the one\nthat held them.", FS, 0.12),
    (55.0, 58.0, "the observer world · i", FSM, 0.90),
]


def keeper_x(t):
    if t < 15: return lerp(0.08, 0.30, smooth(2, 15, t))
    if t < 31: return 0.30
    return lerp(0.30, 0.60, smooth(31, 44, t))


def keeper_state(t):
    x = keeper_x(t)
    moving = (2 < t < 15) or (31 < t < 44)
    pose = "walk" if moving else "stand"
    face = -1 if t >= 45 else 1                     # ends facing back toward the one he helped
    lean = (0.045 * math.sin(2 * math.pi * t / 5.0)
            + 0.08 * smooth(9, 15, t) * (1 - smooth(31, 34, t))    # lean toward F on approach
            + 0.07 * smooth(33, 43, t) * (1 - smooth(44, 47, t))   # lean into the journey right
            - 0.09 * smooth(46, 50, t))                            # turn back toward F at the end
    return x, pose, face, lean


def orb_world(x, feet, pose, t, face, lean, lift=0.0):
    spr, fy, odx, ody = character(int(_SZ), pose, t, face, lift=lift, lean=lean)
    return (x * W + odx, feet * H + ody), (spr, fy)
_SZ = 122


def f_bright(t):
    fl = 0.5 + 0.5 * math.sin(t * 7 + 1)
    base = 0.22 + 0.05 * fl
    base -= 0.06 * smooth(24, 27, t) * (1 - smooth(30, 33, t))   # dips during the clash
    return base * (1 - smooth(46, 49, t)) + 1.0 * smooth(46, 49, t)


def draw_thread(a, p0, p1, bright, t, col=GOLD, broken=False):
    if bright <= 0.01: return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 0.045 * H
    nn = 20
    for i in range(nn):
        u = i / (nn - 1)
        px, py = bez(p0, (mx, my), p1, u)
        if broken:
            # a thread that tries to form and fails — jittery, gappy, unresolved
            j = math.sin(t * 13 + i * 2.1)
            if j < 0.1: continue
            px += 6 * math.sin(t * 20 + i); py += 6 * math.cos(t * 18 + i)
            glow(a, px, py, 4, col, bright * 0.4 * (0.4 + 0.6 * abs(j)))
        else:
            glow(a, px, py, 5, col, bright * 0.5 * (0.6 + 0.4 * math.sin(t * 4 + i)))


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([210, 214, 234])
    for (fx_, fy_) in DFAR:
        glow(a, fx_ * W, fy_ * H, 6, GOLD, 0.05 + 0.03 * math.sin(t + fx_ * 8))

    # keeper
    kx, kp, kf, kl = keeper_state(t)
    (kox, koy), (kspr, kfy) = orb_world(kx, FEET_K, kp, t, kf, kl)

    # the fading one (F) — sits, dim/cold, revealed as the keeper nears; blooms later
    f_seen = smooth(15.5, 18.0, t)
    fb = f_bright(t)
    f_pose = "stand" if t >= 47 else "sit"
    (fox, foy), (fspr, ffy) = orb_world(FX_, FEET_F, f_pose, t, -1, 0.03 * math.sin(t * 1.5))
    fcol = mix3(DIM, GOLD, smooth(45, 50, t))

    # the accidental (Bb) — apart, pale, found when the keeper journeys right
    bb_seen = smooth(33, 36, t)
    bbx = lerp(BBX0, BBX1, smooth(44, 49, t))
    bb_pose = "front" if t < 44 else "stand"
    (bbox, bboy), (bbspr, bbfy) = orb_world(bbx, FEET_B, bb_pose, t, -1, 0.05 * math.sin(t * 1.3))
    bbcol = mix3(COOL, GOLD, smooth(44, 49, t))

    # the offer: the keeper's note ripples toward the fading one (t~23)
    if 22.5 <= t < 30:
        age = t - 22.5; ripple(a, kox, koy, age * 120, 14, 0.3 * math.exp(-age * 0.6))

    # the clash: a thread that tries to bind keeper<->F but fails (dissonant)
    clash = smooth(24, 26, t) * (1 - smooth(29, 31, t))
    draw_thread(a, (kox, koy), (fox, foy), clash, t, col=[210, 150, 130], broken=True)

    # the resolution: the flat bridges all three into Gm7 (warm triangle of light)
    bond = smooth(47, 51, t)
    pulse = 0.85 + 0.15 * math.sin(t * 2.2)
    draw_thread(a, (kox, koy), (bbox, bboy), bond * pulse, t)
    draw_thread(a, (kox, koy), (fox, foy), bond * pulse, t)
    draw_thread(a, (fox, foy), (bbox, bboy), bond * pulse * 0.7, t)
    if 46.5 <= t < 52:
        age = t - 46.5; ripple(a, kox, koy, age * 150, 16, 0.3 * math.exp(-age * 0.5))

    # orbs
    glow(a, fox, foy, 20, fcol, fb * 0.95 * (0.9 + 0.1 * math.sin(t * 3)) * f_seen)
    if bb_seen > 0.02:
        fl = 1.0 if t >= 44 else (0.7 + 0.3 * (0.5 + 0.5 * math.sin(t * 8)))   # flickers while alone
        glow(a, bbox, bboy, 20, bbcol, bb_seen * 0.9 * fl)
    glow(a, kox, koy, 24, GOLD, 0.95 * (0.92 + 0.08 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    # paste in depth order (higher feet = farther = behind)
    people = [(FEET_B, bbx, bbspr, bbfy, bb_seen), (FEET_F, FX_, fspr, ffy, f_seen),
              (FEET_K, kx, kspr, kfy, 1.0)]
    for feet, x, spr, fyy, vis in sorted(people, key=lambda p: p[0]):
        if vis > 0.02:
            im.paste(spr, (int(x * W - spr.size[0] / 2), int(feet * H - fyy)), spr)

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

    for at, am, sd, pan in [(1.0, 0.04, 2, 0.4), (24.0, 0.04, 5, 0.6), (44.0, 0.045, 8, 0.5)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.05, 55), 12.0, 0.7); st(owl(0.05, 58), 40.0, 0.35)
    cp = crickets(18.0, 0.006, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 8.0, 0.5)

    # the keeper walks — musical steps, a wandering G-ish phrase
    walk_notes(st, [3.0, 5.0, 7.0, 9.0, 11.0, 13.0], [55, 57, 58, 57, 55, 53], amp=0.11, base_pan=0.34)
    # the fading one's faint, wavering note (dim, unwell)
    st(piano(midi(53), 5.0, amp=0.07), 16.5, 0.55)
    st(piano(midi(53) * 0.997, 4.0, amp=0.05), 18.0, 0.55)     # slightly flat = struggling

    # the offer + the clash: G against F = a tense whole step, left unresolved
    st(piano(midi(55), 6.0, amp=0.15), 23.0, 0.42)             # his note, offered
    st(piano(midi(53), 5.0, amp=0.12), 24.4, 0.55)             # her note — they beat, no chord
    st(piano(midi(55), 4.0, amp=0.08), 27.0, 0.42)             # he tries again, still no agreement
    st(piano(midi(53), 4.0, amp=0.08), 27.6, 0.55)

    # he journeys to find the note between — steps again, moving right
    walk_notes(st, [33.0, 35.0, 37.0, 39.0, 41.0], [55, 53, 52, 53, 55], amp=0.10, base_pan=0.6)
    # the accidental, found — a pale Bb (the flat, the outsider)
    st(piano(midi(58), 6.0, amp=0.12), 41.5, 0.78)

    # RESOLUTION — the flat bridges them: G-Bb-D-F = Gm7, warm and whole. The three
    # notes ring in turn and lock into the chord; the fading light blooms.
    st(piano(midi(53), 6.0, amp=0.12), 47.0, 0.40)            # F
    st(piano(midi(55), 6.0, amp=0.13), 47.9, 0.52)            # G
    st(piano(midi(58), 6.5, amp=0.13), 48.8, 0.66)            # Bb — the bridge
    gm7 = pad([midi(55), midi(58), midi(62), midi(53 + 12)], 12.0, amp=0.07)
    add(L, gm7, 48.0); add(R, np.roll(gm7, 400), 48.0)
    st(piano(midi(55), 8.0, amp=0.11), 55.0, 0.5)            # settle, warm, on G

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
        Image.fromarray(render(a.preview)).save("obs_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("obs_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("obs.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "obs_silent.mp4", "-i", "obs.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "observer_world_ch1.mp4"],
                   check=True, capture_output=True)
    print("Done -> observer_world_ch1.mp4")


if __name__ == "__main__":
    main()
