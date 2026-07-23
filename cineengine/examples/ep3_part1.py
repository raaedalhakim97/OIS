"""
STAY · part 1 — "Stop"   (direct address to the viewer)
A pattern-interrupt for the scroller. Near-silent open, wind fades in, the
Lightkeeper turns to look at YOU, then guides one breath. The soundscape is
built like music FROM the environment: the air hums the tonic (F), gentle
crickets = night texture, a soft owl on chord tones, grass, and only whispers
of piano. Footsteps barely there. ~42s.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, reverb, add, write_wav

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
    # a few grass blades along the foreground
    rr = np.random.default_rng(7)
    for _ in range(120):
        gx = rr.integers(0, W); gh = rr.integers(14, 46)
        sway = rr.uniform(-8, 8)
        d.line([(gx, H), (gx + sway, H - gh)], fill=(9, 12, 20), width=2)
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(11)
STARX = _r.integers(0, W, 150); STARY = _r.integers(0, int(GROUND * 0.9), 150)
STARB = _r.uniform(0.3, 1.0, 150); STARPH = _r.uniform(0, 6.28, 150)

# (start, end, text, font, y)
TEXT = [
    (2.2, 5.8, "stop scrolling.", FBIG, 0.40),
    (6.4, 9.6, "yeah — you.", FBIG, 0.40),
    (10.2, 15.6, "you've been scrolling\na while now.", FS, 0.42),
    (16.2, 22.2, "it's okay.\nbreathe with me.", FS, 0.42),
    (23.0, 27.0, "in…", FBIG, 0.40),
    (27.6, 31.6, "…and out.", FBIG, 0.40),
    (32.4, 38.4, "the world is still here.\nquiet. waiting.", FS, 0.42),
    (38.8, 42.0, "stay for the next breath.", FSM, 0.44),
]


def breath(t):
    # one guided breath: in 23-27, out 27-31 (grows then settles)
    if t < 23 or t > 31.5:
        return 0.0
    return 0.5 - 0.5 * math.cos(2 * math.pi * (t - 23) / 8.0)


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * (0.4 + 0.4 * smooth(2, 10, t)))[:, None] * np.array([210, 214, 234])

    turned = t >= 6.2
    pose = "front" if turned else "stand"
    spr, fy, odx, ody = character(150, pose, t, 1)
    kx = CX * W
    ox = kx + odx; oy = GROUND + ody
    br = 0.45 + 0.25 * smooth(2, 8, t) + 0.5 * breath(t)      # light swells with the breath
    rad = 24 + 22 * breath(t)
    glow(a, ox, oy, rad, [255, 198, 122], min(1.4, br) * (0.92 + 0.08 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
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
    # small brand tag at the end
    bt = smooth(39.5, 40.5, t)
    if bt > 0.01:
        ln = "the observer"
        bb = d.textbbox((0, 0), ln, font=FSM)
        d.text(((W - (bb[2] - bb[0])) // 2, int(H * 0.9)), ln, font=FSM, fill=(150, 152, 165, int(160 * bt)))

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.014)
    return frame.clip(0, 255).astype(np.uint8)


# =================== the soundscape (environment as music) ===================
def air(dur, amp=0.05, seed=1):
    """Wind that hums the tonic — filtered noise + a soft low F drone."""
    n = int(dur * SR); t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    nse = np.convolve(r.standard_normal(n).astype(np.float32), np.ones(520) / 520, mode="same")
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.055 * t + 1) * np.sin(2 * np.pi * 0.018 * t)
    wind = nse * gust
    drone = (0.5 * np.sin(2 * np.pi * midi(41) * t) + 0.3 * np.sin(2 * np.pi * midi(29) * t))
    drone *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t + seed))
    return (wind * amp + drone * amp * 0.45).astype(np.float32)


def crickets(dur, amp=0.014, seed=3):
    """Subtle night insects — soft high trills (kept very low in the mix)."""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for f, rate, ph in [(4100, 13.5, 0.0), (3800, 12.5, 1.1), (4400, 14.5, 2.3)]:
        env = (0.5 + 0.5 * np.sin(2 * np.pi * rate * t + ph)) ** 8
        y += np.sin(2 * np.pi * f * t) * env
    y /= 3
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)
    return (y * amp * (0.5 + 0.5 * swell)).astype(np.float32)


def owl(amp=0.07, root=48):
    """Soft owl 'hoo…hoo-hoo', tuned to a chord tone (C)."""
    seg = np.zeros(int(1.6 * SR), np.float32)
    f0 = midi(root)
    for start in (0.0, 0.62, 0.92):
        n = int(0.42 * SR); t = np.arange(n) / SR
        f = f0 * (1 - 0.04 * t / 0.42)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.sin(ph) * 0.7 + 0.14 * np.sin(2 * ph)
        env = np.sin(np.clip(t / 0.42, 0, 1) * np.pi) ** 1.4
        s = int(start * SR); seg[s:s + n] += y * env
    return seg * amp


def grass_step(amp=0.028, dur=0.24):
    n = int(dur * SR); t = np.arange(n) / SR
    nse = np.convolve(np.random.randn(n).astype(np.float32), np.ones(22) / 22, mode="same")
    return (nse * np.exp(-t * 15) * np.clip(t / 0.008, 0, 1)) * amp


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # air fades in from near-silence (the wind arriving)
    aL = air(DUR, 0.055, 1); aR = air(DUR, 0.055, 2)
    fadein = np.clip(np.arange(n) / SR / 4.0, 0, 1)      # 4s fade-in
    L += aL * fadein; R += aR * fadein
    # night crickets, low, entering after the hook
    cin = np.clip((np.arange(n) / SR - 8) / 4.0, 0, 1)
    L += crickets(DUR, 0.013, 3) * cin; R += crickets(DUR, 0.012, 4) * cin
    # owl calls (chord tones), distant
    st(owl(0.07, 48), 11.5, 0.3)     # C
    st(owl(0.06, 53), 30.0, 0.7)     # F
    st(owl(0.05, 45), 37.5, 0.4)     # A
    # a couple of very soft grass shifts as it turns / settles
    st(grass_step(), 6.3, 0.5); st(grass_step(0.022), 6.9, 0.52); st(grass_step(0.02), 16.5, 0.48)

    # whispers of piano — sparse, warm, in F, blending with the drone
    st(piano(midi(53), 5.0, amp=0.15), 6.4, 0.5)     # F when it turns to you
    st(piano(midi(57), 4.0, amp=0.10), 11.0, 0.4)    # A
    st(piano(midi(60), 5.0, amp=0.12), 23.0, 0.5)    # C on the in-breath
    st(piano(midi(53), 5.5, amp=0.13), 27.6, 0.5)    # back to F on the out-breath
    st(piano(midi(57), 4.5, amp=0.10), 33.0, 0.6)    # A
    st(piano(midi(53), 6.0, amp=0.14), 39.0, 0.5)    # settle on F
    # soft pad only under the breath (a held F chord) so it 'blooms' with the breath
    p = pad([midi(53), midi(57), midi(60)], 10.0, amp=0.07)
    add(L, p, 22.5); add(R, np.roll(p, 400), 22.5)

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fo = int(2.5 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e3_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e3_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e3.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e3_silent.mp4", "-i", "e3.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "stay_part1.mp4"],
                   check=True, capture_output=True)
    print("Done -> stay_part1.mp4")


if __name__ == "__main__":
    main()
