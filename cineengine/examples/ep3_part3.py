"""
STAY · part 3 — "Stay"   (the presence payoff + a warm CTA)
Rewards the ones who stayed, names how rare presence is, then a soft CTA that
turns a viewer into a follower. Ends open — an invitation to linger. A few small
lights answer softly (connect->piano, warm low). Calm gusting soundscape. ~42s.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, grass_step

W, H = 1080, 1920
FPS = 24
DUR = 44.0
GROUND = 0.82 * H
fx = FX(W, H)
CX = 0.5

# a few distant companions that softly light up (connect->piano), warm low notes
FRIENDS = [(0.20, 0.74, 53, 22.0), (0.80, 0.72, 57, 26.0), (0.34, 0.68, 60, 30.0),
           (0.66, 0.67, 48, 33.5)]


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FBIG = font(70); FS = font(44); FSM = font(34)


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
STARX = _r.integers(0, W, 160); STARY = _r.integers(0, int(GROUND * 0.9), 160)
STARB = _r.uniform(0.3, 1.0, 160); STARPH = _r.uniform(0, 6.28, 160)
FSPR = [character(56, "stand", 0.0, 1 if fx_ < 0.5 else -1, 0.0)
        for (fx_, fy, m, ct) in FRIENDS]

TEXT = [
    (1.0, 4.6, "you're still here.", FBIG, 0.40),
    (5.2, 9.6, "do you feel\nhow rare this is?", FS, 0.40),
    (10.2, 15.0, "a full minute given\nto nothing.\nto just… being.", FS, 0.40),
    (15.6, 19.6, "no likes. no rush. no next.", FS, 0.42),
    (20.4, 25.6, "this — right now —\nis the only moment that's real.", FS, 0.40),
    (26.2, 30.0, "the rest is memory,\nor worry.", FS, 0.42),
    (30.6, 35.0, "you noticed it.\nmost people never do.", FS, 0.40),
    (35.6, 40.0, "come back tomorrow —\ni'll keep the light on.", FS, 0.42),
    (40.4, 44.0, "…stay a little longer.", FSM, 0.44),
]


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.55)[:, None] * np.array([210, 214, 234])

    spr, fy, odx, ody = character(150, "front", t, 1)
    kx = CX * W; ox = kx + odx; oy = GROUND + ody
    glow(a, ox, oy, 30, [255, 198, 122], 0.9 * (0.94 + 0.06 * math.sin(t * 3)))

    # distant companions softly light up (connect -> piano) — 'you're not alone'
    for i, (fxr, fyr, m, ct) in enumerate(FRIENDS):
        lit = smooth(ct, ct + 0.7, t)
        _, ffy, fodx, fody = FSPR[i]
        glow(a, fxr * W + fodx, fyr * H + fody, 12 + 10 * lit, [255, 200, 130],
             (0.10 + 0.7 * lit) * (0.85 + 0.15 * math.sin(t * 4 + fxr * 9)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    for i, (fxr, fyr, m, ct) in enumerate(FRIENDS):
        fspr = FSPR[i][0]
        im.paste(fspr, (int(fxr * W - fspr.size[0] / 2), int(fyr * H - FSPR[i][1])), fspr)
    im.paste(spr, (int(kx - spr.size[0] / 2), int(GROUND - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt, f, yv) in TEXT:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.7, e - 0.7, e], [0, 1, 1, 0])
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

    # gusting wind with silence between; occasional owl; faint mid crickets
    for at, am, sd, pan in [(2.0, 0.045, 2, 0.4), (16.0, 0.04, 5, 0.6), (34.0, 0.045, 8, 0.5)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.06, 53), 12.0, 0.7); st(owl(0.05, 48), 37.0, 0.3)
    cp = crickets(14.0, 0.007, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 6.0, 0.5)

    # companions answer as they light up — warm low notes, panned to them
    for (fxr, fyr, m, ct) in FRIENDS:
        st(piano(midi(m), 6.5, amp=0.16), ct, fxr)
        st(piano(midi(m), 4.0, amp=0.06), ct + 0.6, 1 - fxr)     # soft echo
    # calm anchoring notes on key lines, slow (quarter pace)
    st(piano(midi(53), 6.0, amp=0.14), 1.0, 0.5)     # F — you're still here
    st(piano(midi(57), 5.0, amp=0.10), 20.4, 0.45)   # A — this moment is real
    st(piano(midi(53), 7.0, amp=0.14), 35.6, 0.5)    # F — keep the light on
    # a soft F-major pad blooms as the companions gather, then a gentle open ending
    p = pad([midi(53), midi(57), midi(60)], 12.0, amp=0.06)
    add(L, p, 21.0); add(R, np.roll(p, 400), 21.0)
    st(piano(midi(53), 8.0, amp=0.13), 40.4, 0.5)    # unresolved-open settle on F

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(SR), int(4.0 * SR)                  # long, soft fade-out = 'stay'
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e3c_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e3c_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e3c.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e3c_silent.mp4", "-i", "e3c.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "stay_part3.mp4"],
                   check=True, capture_output=True)
    print("Done -> stay_part3.mp4")


if __name__ == "__main__":
    main()
