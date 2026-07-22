"""
THE ANSWER · part 2 — "The Water"  (point of view: looking within)
The Lightkeeper lowers the light to the still water; the reflection lights up
and answers back — the answer was inside. Descending in-key bell motif +
water ripples, synced. ~24s vertical.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, compose, add, write_wav

W, H = 1080, 1920
FPS = 24
DUR = 24.0
HOR = 0.66
WL = int(HOR * H)
fx = FX(W, H)

T_WALKIN = (0.0, 6.0)
T_LOWER = (9.0, 13.0)
T_WALKOUT = (18.0, 24.0)
CENTER_X = 0.5
STEP = 0.52


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


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([9, 12, 30], np.float32) * (1 - t)
            + np.array([26, 26, 54], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, HOR * H - 0.08 * H, 0.5 * W, HOR * H + 0.3 * H], fill=(18, 20, 38))
    d.ellipse([0.55 * W, HOR * H - 0.06 * H, 1.3 * W, HOR * H + 0.3 * H], fill=(21, 23, 42))
    d.rectangle([0, WL, W, H], fill=(11, 13, 28))            # still water
    return np.asarray(im, np.float32)
BG = build_bg()

_r = np.random.default_rng(8)
SX = _r.integers(0, W, 140); SY = _r.integers(0, WL, 140)
SB = _r.uniform(0.3, 1.0, 140); SPH = _r.uniform(0, 6.28, 140)


def char_state(t):
    if t < T_WALKIN[1]:
        return "walk", lerp(0.12, CENTER_X, smooth(*T_WALKIN, t))
    if t < T_WALKOUT[0]:
        return "stand", CENTER_X
    return "walk", lerp(CENTER_X, 0.9, smooth(*T_WALKOUT, t))


def lower_amount(t):
    # lower 9->12, hold, raise back 16.5->18  (negative = arm reaches down)
    return -(smooth(9.0, 12.0, t) * (1 - smooth(16.5, 18.0, t)))


def render(t):
    a = BG.copy()
    # gentle static starfield + reflection in water
    tw = 0.5 + 0.5 * np.sin(t * 2 + SPH)
    a[SY, SX] += (SB * tw)[:, None] * np.array([200, 206, 230])
    a[WL + (WL - SY).clip(0, H - WL - 1), SX] += (SB * tw * 0.35)[:, None] * np.array([120, 130, 170])

    pose, cxf = char_state(t)
    cx = cxf * W
    low = lower_amount(t)                       # 0 .. -1
    depth = -low                                # 0 .. 1
    spr, fy, odx, ody = character(150, pose, t, 1, lift=low)

    # orb dips toward the water surface as it lowers
    ox = cx + odx
    oy = HOR * H + ody + depth * 0.05 * H
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    glow(a, ox, oy, 30 + 8 * depth, [255, 198, 120], (0.6 + 0.3 * depth) * pulse)

    # THE REFLECTION ANSWERS: bright mirrored orb + expanding ripples of light
    answer = smooth(11.0, 14.0, t) * (1 - smooth(16.5, 18.0, t))
    ref_y = 2 * WL - oy                          # mirror across waterline
    glow(a, ox, ref_y, 30 + 22 * answer, [255, 205, 140], (0.4 + 0.7 * answer) * pulse)
    # a soft 'answer' glow rising from within the water
    glow(a, ox, WL + 40, 60 * answer + 10, [255, 190, 120], 0.5 * answer)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if answer > 0.02:                            # ripple rings on the surface
        dd = ImageDraw.Draw(im, "RGBA")
        for k in range(3):
            rp = ((t - 11.0) * 0.5 + k * 0.33) % 1.0
            rad = rp * 300
            al = int(150 * answer * (1 - rp))
            dd.ellipse([ox - rad, WL - rad * 0.28, ox + rad, WL + rad * 0.28],
                       outline=(255, 205, 150, al), width=2)

    im.paste(spr, (int(cx - spr.size[0] / 2), int(HOR * H - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.5, 1.5, t) * (1 - smooth(4.5, 5.5, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE ANSWER", FT, 0.10), ("part 2 · the water", FS, 0.145)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(235, 232, 226, int(230 * tfade)))
    cfade = smooth(14.5, 15.5, t) * (1 - smooth(22, 23.2, t))
    if cfade > 0.01:
        yy = int(H * 0.12)
        for ln in ["look within —", "the answer looks back."]:
            bb = d.textbbox((0, 0), ln, font=FS)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(228, 226, 220, int(220 * cfade)))
            yy += int((bb[3] - bb[1]) * 1.7)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.016)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio ----
def desc_shimmer(dur, amp=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 660 * 2 ** (-t / dur * 1.6)              # glide DOWN
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.5 * np.sin(2 * ph)
    env = np.clip(t / (dur * 0.35), 0, 1) * np.clip((dur - t) / 1.2, 0, 1)
    return (y * env * amp).astype(np.float32)


def bell(m, dur=1.2, amp=0.12):
    n = int(dur * SR); t = np.arange(n) / SR; f = midi(m)
    y = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.18 * np.sin(2 * np.pi * 3 * f * t)
    return (y * np.exp(-t * 2.1) * np.clip(t / 0.015, 0, 1) * amp).astype(np.float32)


def water(amp=0.16, dur=0.9):
    n = int(dur * SR); t = np.arange(n) / SR
    nse = np.random.randn(n).astype(np.float32)
    nse = np.convolve(nse, np.ones(60) / 60, mode="same")   # low-passed = soft water
    return (nse * np.exp(-t * 3) * amp)


def footstep(amp=0.2, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    n = int(DUR * SR)
    music = compose(DUR) * 0.5
    L = music[:, 0].copy(); R = music[:, 1].copy()
    def st(sig, at, pan=0.5): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    for (s, e) in (T_WALKIN, T_WALKOUT):
        tt = s + 0.3
        while tt < e - 0.2: st(footstep(), tt); tt += STEP
    st(desc_shimmer(4.0), T_LOWER[0])                       # lowering the light
    st(water(), 11.2)                                       # touches the water
    # reflection answers: descending F-major bells, then a low resolve
    for i, m in enumerate([86, 84, 81, 79, 77]):            # D6 C6 A5 G5 F5
        st(bell(m, amp=0.11), 11.4 + i * 0.42, pan=0.5 + (i - 2) * 0.05)
    st(bell(65, amp=0.10), 13.4)                            # F4 resolve
    for at, m in ((14.6, 69), (16.0, 65)):                  # settle A3/F3
        st(bell(m, amp=0.08), at)
    from make_music import reverb
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.25)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.88
    fi, fo = int(SR), int(2 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e2_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2_silent.mp4", "-i", "e2.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "answer_part2.mp4"],
                   check=True, capture_output=True)
    print("Done -> answer_part2.mp4")


if __name__ == "__main__":
    main()
