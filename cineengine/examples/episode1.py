"""
THE LIGHTKEEPER - Episode 1: "The Answer"
A calm night-shore short. The Lightkeeper walks in, raises the light, and the
stars answer. Event-synced sound (footsteps, a rising tone on the lift,
twinkles as the stars brighten) over an ambient bed. ~24s vertical.

Same fast pipeline. Timeline constants are shared by picture + sound.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, reverb, write_wav, add, compose

W, H = 1080, 1920
FPS = 24
DUR = 24.0
HOR = 0.72
WL = int(HOR * H)
fx = FX(W, H)

# ---- shared timeline ----
T_WALKIN = (0.0, 6.0)      # walk in from left to center
T_IDLE = (6.0, 9.0)
T_LIFT = (9.0, 13.0)       # raise the light
T_HOLD = (13.0, 18.0)
T_WALKOUT = (18.0, 24.0)
CENTER_X = 0.5
STEP = 0.52                # footstep cadence


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FT = font(58); FS = font(38)


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


# ---- background (precomputed) ----
def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([10, 14, 34], np.float32) * (1 - t)
            + np.array([32, 30, 62], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    # soft hills
    d.ellipse([-0.3 * W, HOR * H - 0.10 * H, 0.55 * W, HOR * H + 0.3 * H], fill=(20, 22, 40))
    d.ellipse([0.5 * W, HOR * H - 0.07 * H, 1.35 * W, HOR * H + 0.3 * H], fill=(23, 25, 44))
    d.rectangle([0, WL, W, H], fill=(14, 16, 30))     # water base
    return np.asarray(im, np.float32)
BG = build_bg()

_r = np.random.default_rng(8)
STAR_X = _r.integers(0, W, 150); STAR_Y = _r.integers(0, int(HOR * H), 150)
STAR_B = _r.uniform(0.3, 1.0, 150); STAR_PH = _r.uniform(0, 6.28, 150)
FF = 30
FX_ = _r.uniform(0.1, 0.9, FF); FY_ = _r.uniform(HOR + 0.02, 0.96, FF)
FPH = _r.uniform(0, 6.28, FF); FSP = _r.uniform(0.1, 0.4, FF)


def char_state(t):
    if t < T_WALKIN[1]:
        return "walk", lerp(0.12, CENTER_X, smooth(*T_WALKIN, t)), 1
    if t < T_IDLE[1]:
        return "stand", CENTER_X, 1
    if t < T_LIFT[1]:
        return "lift", CENTER_X, 1
    if t < T_HOLD[1]:
        return "lift", CENTER_X, 1
    return "walk", lerp(CENTER_X, 0.9, smooth(*T_WALKOUT, t)), 1


def render(t):
    a = BG.copy()
    # star brightness answers the lift
    answer = smooth(9.6, 13.0, t)
    base_star = 0.5 + 0.5 * answer
    tw = (0.5 + 0.5 * np.sin(t * 2 + STAR_PH)) * base_star
    a[STAR_Y, STAR_X] += (STAR_B * tw)[:, None] * np.array([210, 214, 235]) * 1.1
    # a few stars 'pop' brighter right as the light rises
    if answer > 0.05:
        for k in range(int(24 * answer)):
            i = (k * 7) % len(STAR_X)
            glow(a, STAR_X[i], STAR_Y[i], 6, [255, 245, 220], 0.5 * answer)

    pose, cxf, face = char_state(t)
    cx = cxf * W
    spr, fy, odx, ody = character(150, pose, t, face)

    # orb position + light it casts (rises during lift)
    lift = smooth(9.0, 12.0, t) if t >= 9 else 0.0
    ox = cx + odx
    oy = HOR * H + ody - lift * 0.16 * H
    orb_pulse = 0.85 + 0.15 * math.sin(t * 3)
    glow(a, ox, oy, 34 + 16 * lift, [255, 198, 120], (0.7 + 0.4 * lift) * orb_pulse)
    # orb reflection on the water
    gy = np.arange(H - WL)
    streak = np.exp(-((np.arange(W)[None, :] - ox) ** 2) / (2 * 26 ** 2)) * (1 - gy[:, None] / (H - WL)) ** 1.4
    a[WL:] += streak[..., None] * np.array([255, 200, 130]) * 0.5 * orb_pulse

    # fireflies during hold
    ffw = smooth(12, 15, t) * (1 - smooth(19, 22, t))
    if ffw > 0.02:
        for i in range(FF):
            px = int((FX_[i] + 0.02 * np.sin(t * FSP[i] * 3 + FPH[i])) * W)
            py = int(FY_[i] * H)
            fl = 0.4 + 0.6 * np.sin(t * 5 + FPH[i])
            glow(a, px, py, 5, [255, 220, 150], 0.5 * ffw * max(0, fl))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(cx - spr.size[0] / 2), int(HOR * H - fy)), spr)

    # branding: gentle title in, calm caption out
    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.5, 1.5, t) * (1 - smooth(4.5, 5.5, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE ANSWER", FT, 0.10), ("part 1 · the sky", FS, 0.10 + 0.045)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(235, 232, 226, int(230 * tfade)))
    cfade = smooth(14.5, 15.5, t) * (1 - smooth(22, 23.2, t))
    if cfade > 0.01:
        txt = "ask the sky,\nand it answers in light."
        yy = int(H * 0.12)
        for ln in txt.split("\n"):
            bb = d.textbbox((0, 0), ln, font=FS)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(228, 226, 220, int(220 * cfade)))
            yy += int((bb[3] - bb[1]) * 1.7)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.016)
    return frame.clip(0, 255).astype(np.uint8)


# ---- synced audio ----
def rising_shimmer(dur, amp=0.24):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 220 * 2 ** (t / dur * 2.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    env = np.clip(t / (dur * 0.4), 0, 1) * np.clip((dur - t) / 1.2, 0, 1)
    return (y * env * amp).astype(np.float32)


def twinkle(freq, amp=0.16, dur=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.01 * t))
            * np.exp(-t * 7) * amp).astype(np.float32)


def footstep(amp=0.2, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    n = int(DUR * SR)
    music = compose(DUR) * 0.5
    L = music[:, 0].copy(); R = music[:, 1].copy()
    def st(sig, at, pan=0.5): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    # footsteps in (0->6) and out (18->24)
    for (s, e) in (T_WALKIN, T_WALKOUT):
        tt = s + 0.3
        while tt < e - 0.2:
            st(footstep(), tt); tt += STEP
    # rising shimmer on the lift
    st(rising_shimmer(T_LIFT[1] - T_LIFT[0]), T_LIFT[0])
    # twinkles as the stars answer (9.6 -> 15)
    rng = np.random.default_rng(5)
    tt = 9.8
    while tt < 15.5:
        st(twinkle(rng.uniform(1600, 3200)), tt, rng.uniform(0.3, 0.7)); tt += rng.uniform(0.35, 0.7)
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.3)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi, fo = int(SR), int(2 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep1_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep1.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep1_silent.mp4", "-i", "ep1.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "answer_part1.mp4"],
                   check=True, capture_output=True)
    print("Done -> answer_part1.mp4")


if __name__ == "__main__":
    main()
