"""
THE ANSWER · part 5 — "The Lost"  (the finale / resolution)
Lost in the dark, his light nearly out, no point of view gave him the answer.
A small lost soul appears. He gives his light away — and the whole sky ignites.
The answer was never to find it. It was to become it. Full F-major resolve.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, compose, add, write_wav, reverb

W, H = 1080, 1920
FPS = 24
DUR = 26.0
GROUND = 0.80 * H
fx = FX(W, H)

KX0 = 0.34
SMALLX = 0.64
STEP = 0.52


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FT = font(58); FS = font(40)


def glow(a, cx, cy, rad, color, alpha):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.32), 0, 1) ** 0.7 * alpha
    a[y0:y1, x0:x1] += disc[..., None] * np.array(color, np.float32)


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([6, 8, 20], np.float32) * (1 - t)
            + np.array([14, 16, 34], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(10, 12, 24))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(12, 14, 26))
    d.rectangle([0, int(GROUND), W, H], fill=(8, 9, 18))
    return np.asarray(im, np.float32)
BG = build_bg()

_r = np.random.default_rng(21)
NSTAR = 260
SX = _r.integers(0, W, NSTAR); SY = _r.integers(0, int(GROUND * 0.98), NSTAR)
SB = _r.uniform(0.3, 1.0, NSTAR); SPH = _r.uniform(0, 6.28, NSTAR)


def keeper_x(t):
    if t < 7: return KX0
    return lerp(KX0, 0.47, smooth(7, 11, t))


def hand_of(h, x, face, lift=0.0):
    _, fy, odx, ody = character(h, "stand", 0, face, lift=lift)
    return x * W + odx, GROUND + ody


def render(t):
    a = BG.copy()
    ign = smooth(15.0, 18.5, t)          # the sky ignites
    # stars: faint at first, bloom at ignition
    tw = 0.5 + 0.5 * np.sin(t * 2 + SPH)
    star_amt = 0.12 + 0.9 * ign
    a[SY, SX] += (SB * tw * star_amt)[:, None] * np.array([225, 226, 240])

    # our lightkeeper (his light is dim / flickering — lost)
    kx = keeper_x(t)
    kpose = "walk" if 7 < t < 11 else "stand"
    kspr, kfy, kodx, kody = character(150, kpose, t, 1, lift=0.0)
    kx_px = kx * W

    # the small lost soul appears ahead, lightless at first
    appear = smooth(5.0, 7.0, t)
    sspr, sfy, sodx, sody = character(100, "stand", t, -1, lift=0.0)

    # THE LIGHT — travels from his hand to the child's hand as he gives it
    give = smooth(11.5, 15.0, t)
    khx, khy = kx_px + kodx, GROUND + kody
    shx, shy = SMALLX * W + sodx, GROUND + sody
    ox = lerp(khx, shx, give); oy = lerp(khy, shy, give)
    if t < 11:                            # dying, unsteady flame
        flick = 0.5 + 0.5 * math.sin(t * 11) * math.sin(t * 6.3)
        a_orb, r_orb = 0.32 + 0.18 * flick, 24
    elif t < 15:
        a_orb = lerp(0.45, 0.95, give); r_orb = lerp(24, 34, give)
    else:
        a_orb = 0.95 + 0.7 * ign; r_orb = 34 + 40 * ign
    glow(a, ox, oy, r_orb, [255, 200, 128], a_orb)

    # ignition: a warm wash of light spreading from the shared flame
    if ign > 0.01:
        glow(a, ox, oy, 260 * ign + 40, [255, 200, 140], 0.5 * ign)
        glow(a, W * 0.5, GROUND - 0.2 * H, 700 * ign, [80, 70, 110], 0.18 * ign)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    # paste small soul (behind/beside), then keeper
    if appear > 0.02:
        s = sspr.copy(); s.putalpha(sspr.split()[3].point(lambda p: int(p * appear)))
        im.paste(s, (int(SMALLX * W - s.size[0] / 2), int(GROUND - sfy)), s)
    im.paste(kspr, (int(kx_px - kspr.size[0] / 2), int(GROUND - kfy)), kspr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.6, 1.6, t) * (1 - smooth(4.4, 5.2, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE ANSWER", FT, 0.10), ("part 5 · the lost", FS, 0.145)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(232, 230, 224, int(230 * tfade)))
    # mid caption (giving)
    g1 = smooth(12.0, 13.0, t) * (1 - smooth(15.0, 15.8, t))
    if g1 > 0.01:
        ln = "so he gave his light away."
        bb = d.textbbox((0, 0), ln, font=FS)
        d.text(((W - (bb[2] - bb[0])) // 2, int(H * 0.13)), ln, font=FS, fill=(228, 226, 220, int(220 * g1)))
    # final resolve caption
    g2 = smooth(18.5, 19.8, t) * (1 - smooth(24.4, 25.4, t))
    if g2 > 0.01:
        yy = int(H * 0.11)
        for ln in ["the answer was never to find it —", "it was to become it."]:
            bb = d.textbbox((0, 0), ln, font=FS)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(235, 232, 224, int(230 * g2)))
            yy += int((bb[3] - bb[1]) * 1.7)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=9, thr=200, gain=0.75)
    frame = fx.vignette(frame, 0.4 - 0.15 * ign)      # vignette opens as it ignites
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: hollow -> giving -> full F-major resolve ----
def bell(m, dur=2.2, amp=0.12):
    n = int(dur * SR); t = np.arange(n) / SR; f = midi(m)
    y = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.18 * np.sin(2 * np.pi * 3 * f * t)
    return (y * np.exp(-t * 1.3) * np.clip(t / 0.015, 0, 1) * amp).astype(np.float32)


def bass(m, dur=4.0, amp=0.2):
    n = int(dur * SR); t = np.arange(n) / SR; f = midi(m)
    y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return (y * np.exp(-t * 0.5) * np.clip(t / 0.03, 0, 1) * amp).astype(np.float32)


def shimmer(dur, amp=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 300 * 2 ** (t / dur * 1.4)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.4 * np.sin(2 * ph)
    return (y * np.clip(t / (dur * 0.4), 0, 1) * np.clip((dur - t) / 0.8, 0, 1) * amp).astype(np.float32)


def wind(dur, amp=0.08):
    n = int(dur * SR)
    nse = np.convolve(np.random.randn(n).astype(np.float32), np.ones(220) / 220, mode="same")
    return (nse * np.sin(np.linspace(0, np.pi, n)) ** 2 * amp)


def footstep(amp=0.16, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    n = int(DUR * SR)
    music = compose(DUR)
    tt = np.arange(n) / SR
    def vs(a, b, x):
        s = np.clip((x - a) / (b - a), 0, 1); return s * s * (3 - 2 * s)
    # bed: hollow/quiet while lost, swells to full at the ignition, gentle out
    env = 0.14 + 0.60 * vs(12.5, 16.5, tt)
    music = music * env[:, None]
    L = music[:, 0].copy(); R = music[:, 1].copy()
    def st(sig, at, pan=0.5): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    st(wind(7.0), 0.5)                                  # lost in the dark
    st(bell(41, dur=3.0, amp=0.10), 2.2)                # a lonely low F
    tt2 = 7.3
    while tt2 < 10.8: st(footstep(), tt2); tt2 += STEP  # walking to the child
    st(shimmer(3.4), 11.6)                              # the light passing over

    # IGNITION at ~15.2 — full warm F-major resolve
    st(bass(41, dur=8.0, amp=0.22), 15.2)               # F2 home bass
    for i, m in enumerate([53, 57, 60, 65, 69, 72]):    # F A C F A C bloom
        st(bell(m, amp=0.12), 15.2 + i * 0.08)
    for i, m in enumerate([65, 69, 72, 77]):            # ascending melody resolving to F
        st(bell(m, amp=0.11), 15.6 + i * 0.5)
    # stars blooming: soft ascending pentatonic sparkles, organized
    for i, m in enumerate([77, 81, 84, 86, 89]):
        st(bell(m, dur=1.6, amp=0.06), 16.0 + i * 0.35, pan=0.5 + (i - 2) * 0.06)
    st(bell(65, dur=3.5, amp=0.12), 21.5)               # final settle on F

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.2)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi, fo = int(SR), int(3 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e5_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e5_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e5.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e5_silent.mp4", "-i", "e5.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "answer_part5.mp4"],
                   check=True, capture_output=True)
    print("Done -> answer_part5.mp4")


if __name__ == "__main__":
    main()
