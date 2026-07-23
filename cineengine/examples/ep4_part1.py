"""
THE KNOWLEDGE · part 1 — "The Fork"   (after Robert Frost, "The Road Not Taken", public domain)
Two glowing roads diverge in a yellow wood. The Lightkeeper stands, looks down
one, then takes the other. Warm autumn palette, drifting leaves, the calm
gusting soundscape. Frost's words on screen. ~45s.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, grass_step, step_note, walk_notes

W, H = 1080, 1920
FPS = 24
DUR = 46.0
GROUND = 0.80 * H
fx = FX(W, H)


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
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


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([26, 20, 24], np.float32) * (1 - t)       # warm autumn dusk
            + np.array([70, 52, 40], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    # tree trunks + canopies framing the sides (the wood)
    rr = np.random.default_rng(5)
    for tx in (0.06, 0.16, 0.86, 0.95, 0.75):
        x = tx * W; tw = rr.uniform(12, 26)
        d.rectangle([x - tw, 0.30 * H, x + tw, GROUND], fill=(20, 15, 16))
        d.ellipse([x - 0.14 * W, 0.14 * H, x + 0.14 * W, 0.42 * H], fill=(24, 18, 18))
    d.rectangle([0, int(GROUND), W, H], fill=(30, 22, 18))
    # a scatter of fallen leaves on the ground
    for _ in range(60):
        gx = rr.integers(0, W); gy = rr.integers(int(GROUND), H)
        d.ellipse([gx, gy, gx + 6, gy + 4], fill=(90, 66, 36))
    return np.asarray(im, np.float32)
BG = build_bg()

# two diverging roads (screen fractions): start at the fork, curve away
FORK = (0.5, 0.80)
LEFT = [FORK, (0.30, 0.64), (0.19, 0.44)]
RIGHT = [FORK, (0.71, 0.63), (0.82, 0.47)]

# drifting leaves
_r = np.random.default_rng(9)
LX = _r.uniform(0, 1, 26); LY0 = _r.uniform(-0.2, 1.0, 26)
LSP = _r.uniform(0.02, 0.05, 26); LPH = _r.uniform(0, 6.28, 26); LSZ = _r.uniform(4, 9, 26)

TEXT = [
    (2.0, 6.6, "Two roads diverged\nin a yellow wood,", FS, 0.13),
    (7.1, 12.0, "and sorry I could not\ntravel both", FS, 0.13),
    (12.5, 17.5, "and be one traveler,\nlong I stood", FS, 0.13),
    (18.0, 23.2, "and looked down one\nas far as I could", FS, 0.13),
    (23.7, 28.7, "to where it bent\nin the undergrowth;", FS, 0.13),
    (29.6, 34.6, "Then took the other,\nas just as fair,", FS, 0.13),
    (35.1, 40.2, "because it was grassy\nand wanted wear;", FS, 0.13),
    (41.0, 45.5, "the road not taken · i", FSM, 0.90),
]


def draw_road(a, pts, bright, t, lit_frac=0.0):
    n = 22
    for i in range(n):
        u = i / (n - 1)
        px, py = bez(pts[0], pts[1], pts[2], u)
        fade = (1 - u) ** 0.6                      # far dots dimmer (into undergrowth)
        seq = 1.0 if u <= lit_frac else 0.25       # dots light up in sequence when chosen
        tw = 0.7 + 0.3 * math.sin(t * 3 + i * 0.6)
        glow(a, px * W, py * H, 7 + 3 * (u < 0.4), [255, 205, 130],
             bright * fade * seq * tw * 0.8)


def render(t):
    a = BG.copy()
    # drifting leaves
    for i in range(len(LX)):
        ly = (LY0[i] + t * LSP[i]) % 1.2 - 0.1
        lx = (LX[i] + 0.03 * math.sin(t * 0.8 + LPH[i]))
        px, py = int(lx * W), int(ly * H)
        if 0 <= py < H:
            glow(a, px, py, LSZ[i], [150, 110, 60], 0.28)

    appear = smooth(6, 9, t)
    look_r = smooth(18, 22, t) * (1 - smooth(28.5, 30, t))   # looking down the right road
    chose_l = smooth(29.5, 32, t)
    walk = smooth(35, 45, t)                                  # walking the left road
    draw_road(a, RIGHT, appear * (0.4 + 0.7 * look_r) * (1 - 0.5 * chose_l), t)
    draw_road(a, LEFT, appear * (0.4 + 0.6 * chose_l), t, lit_frac=walk)

    # the keeper: at the fork, then steps onto the chosen (left) road
    kx = lerp(0.5, 0.30, walk) * W
    ky = lerp(GROUND, 0.66 * H, walk)
    ksz = int(lerp(150, 112, walk))
    pose = "walk" if (t < 6 or t > 35) else "front"
    face = -1 if t > 29 else 1
    spr, fy, odx, ody = character(ksz, pose, t, face)
    ox = kx + odx; oy = ky + ody
    glow(a, ox, oy, 26, [255, 200, 130], 0.9 * (0.92 + 0.08 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt, f, yv) in TEXT:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.7, e - 0.7, e], [0, 1, 1, 0])
            yy = int(H * yv)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=f)
                col = (232, 226, 214, int(235 * fade)) if f is FS else (170, 150, 120, int(180 * fade))
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f, fill=col)
                yy += int((bb[3] - bb[1]) * 1.5)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


def leaf_rustle(amp=0.03, dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    nse = np.convolve(np.random.randn(n).astype(np.float32), np.ones(30) / 30, mode="same")
    return (nse * np.exp(-t * 6) * amp)


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    for at, am, sd, pan in [(1.5, 0.045, 2, 0.4), (14.0, 0.04, 5, 0.6), (33.0, 0.045, 8, 0.5)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.055, 53), 10.0, 0.7); st(owl(0.05, 48), 31.0, 0.3)
    cp = crickets(12.0, 0.006, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 8.0, 0.5)
    # soft leaf rustles as it stands in the wood
    for at in (13.0, 22.0, 30.0): st(leaf_rustle(), at, np.random.uniform(0.3, 0.7))
    # PIANO anchor notes on the key lines (the light's voice), slow quarter pace
    st(piano(midi(53), 6.0, amp=0.14), 2.0, 0.5)     # F — two roads
    st(piano(midi(57), 5.0, amp=0.10), 18.0, 0.65)   # A — looked down the right (panned right)
    st(piano(midi(60), 5.5, amp=0.12), 29.6, 0.35)   # C — took the other (panned left)
    # INTERACTIVE MUSICAL STEPS — each footfall IS a piano note (the light sings
    # its motion). Arrival at the fork: a gentle settling phrase.
    walk_notes(st, [2.5, 4.0, 5.5], [60, 57, 53], amp=0.13, base_pan=0.5)
    # Departure up the chosen (left) road: each step lights the next segment and
    # rings the next note — an ascending warm F-major climb, panned to the road.
    walk_notes(st, [35.5, 36.6, 37.7, 38.8, 39.9], [53, 57, 60, 62, 65], amp=0.14, base_pan=0.36)
    p = pad([midi(53), midi(57), midi(60)], 10.0, amp=0.05)
    add(L, p, 34.0); add(R, np.roll(p, 400), 34.0)
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(SR), int(3.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e4_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e4_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e4.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e4_silent.mp4", "-i", "e4.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "knowledge_part1.mp4"],
                   check=True, capture_output=True)
    print("Done -> knowledge_part1.mp4")


if __name__ == "__main__":
    main()
