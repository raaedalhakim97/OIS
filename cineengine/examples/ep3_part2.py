"""
STAY · part 2 — "Breathe"   (the concentration engine)
Guided breathing paced by the light (grows on in, holds, shrinks on out) and
sensory anchoring: each ambient sound is NAMED the moment it plays ("that's the
wind" -> a real gust). Calm, spacious — gusting wind with silence between, slow
notes. ~42s.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, grass_step   # reuse the soundscape kit

W, H = 1080, 1920
FPS = 24
DUR = 42.0
GROUND = 0.82 * H
fx = FX(W, H)
CX = 0.5


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FBIG = font(72); FS = font(44); FSM = font(34)


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
    for _ in range(120):
        gx = rr.integers(0, W); gh = rr.integers(14, 46); sway = rr.uniform(-8, 8)
        d.line([(gx, H), (gx + sway, H - gh)], fill=(9, 12, 20), width=2)
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(11)
STARX = _r.integers(0, W, 150); STARY = _r.integers(0, int(GROUND * 0.9), 150)
STARB = _r.uniform(0.3, 1.0, 150); STARPH = _r.uniform(0, 6.28, 150)

# ---- breathing paced by the light: two cycles (in / hold / out) ----
def breath_scale(t):
    if 10.0 <= t < 14.0: return smooth(10, 14, t)          # in
    if 14.0 <= t < 16.0: return 1.0                         # hold
    if 16.0 <= t < 22.0: return 1 - smooth(16, 22, t)       # out
    if 35.6 <= t < 38.5: return smooth(35.6, 38.5, t)       # one more — in
    if 38.5 <= t < 41.2: return 1 - smooth(38.5, 41.2, t)   # out
    return 0.12 + 0.04 * math.sin(t * 0.5)                  # gentle rest

TEXT = [
    (1.0, 4.4, "still here? good.\nmost people already left.", FS, 0.40),
    (4.9, 7.0, "now — we listen.", FS, 0.40),
    (7.4, 9.8, "breathe with the light.", FS, 0.42),
    (10.2, 13.9, "in, slow…", FBIG, 0.40),
    (14.1, 15.9, "hold…", FBIG, 0.40),
    (16.2, 21.6, "out, slower.", FBIG, 0.40),
    (22.2, 24.6, "that's the wind.", FS, 0.42),
    (25.3, 27.9, "an owl, far off.", FS, 0.42),
    (28.5, 30.5, "the grass.", FS, 0.42),
    (31.0, 34.0, "notice — you stopped\nthinking for a second.", FS, 0.42),
    (34.3, 35.4, "that's the whole point.", FS, 0.42),
    (35.7, 38.4, "one more. in…", FBIG, 0.40),
    (38.6, 41.0, "…and out.", FBIG, 0.40),
    (41.0, 42.0, "→ stay", FSM, 0.44),
]


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([210, 214, 234])

    spr, fy, odx, ody = character(150, "front", t, 1)
    kx = CX * W; ox = kx + odx; oy = GROUND + ody
    bs = breath_scale(t)
    glow(a, ox, oy, 24 + 32 * bs, [255, 198, 122], (0.42 + 0.6 * bs) * (0.94 + 0.06 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(GROUND - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt, f, yv) in TEXT:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.6, e - 0.6, e], [0, 1, 1, 0])
            yy = int(H * yv)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=f)
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f, fill=(236, 233, 226, int(235 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.014)
    return frame.clip(0, 255).astype(np.uint8)


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # SENSORY ANCHORING — each sound plays the instant it's named
    st(wind_gust(6.5, 0.05, 2), 21.6, 0.5)     # "that's the wind."
    st(owl(0.07, 48), 25.0, 0.72)              # "an owl, far off." (C)
    for gt in (28.4, 28.9, 29.4):              # "the grass."
        st(grass_step(0.03), gt, 0.35)
    # ambient gusts elsewhere, sparse, with silence between (never continuous)
    st(wind_gust(6.0, 0.04, 5), 2.0, 0.4)
    st(wind_gust(6.5, 0.04, 9), 37.0, 0.55)
    # a faint cricket patch in the mid-section only
    cp = crickets(12.0, 0.007, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 24.0, 0.5)

    # breath: one slow calm note in, one out (light does the rest). quarter pace.
    st(piano(midi(60), 6.0, amp=0.12), 10.2, 0.5)     # C — in
    st(piano(midi(53), 6.5, amp=0.13), 16.2, 0.5)     # F — out
    st(piano(midi(60), 5.5, amp=0.11), 35.7, 0.5)     # in
    st(piano(midi(53), 7.0, amp=0.13), 38.6, 0.5)     # out, settle on F
    # a soft F pad swelling gently under each breath cycle
    for at in (9.5, 35.0):
        p = pad([midi(53), midi(57), midi(60)], 8.0, amp=0.055)
        add(L, p, at); add(R, np.roll(p, 400), at)

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(SR), int(2.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e3b_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e3b_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e3b.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e3b_silent.mp4", "-i", "e3b.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "stay_part2.mp4"],
                   check=True, capture_output=True)
    print("Done -> stay_part2.mp4")


if __name__ == "__main__":
    main()
