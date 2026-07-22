"""
THE ANSWER · part 4 — "The Climb"  (point of view: reason / effort)
The Lightkeeper climbs for the answer. A rising bass line builds with each step.
At the summit he raises his light, hopeful... and nothing answers. Only horizon.
The turn of the story. ~24s.
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
DUR = 24.0
fx = FX(W, H)

SUMMIT = (0.55, 0.42)
START = (0.16, 0.86)
T_CLIMB = (0.0, 10.0)
T_RAISE = (11.0, 14.0)
T_SIT = (18.5, 24.0)
CLIMB_STEPS = [1.4, 3.0, 4.6, 6.2, 7.8, 9.2]


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
    a[:] = (np.array([12, 15, 34], np.float32) * (1 - t)
            + np.array([34, 32, 60], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rr = np.random.default_rng(4)
    for _ in range(90):
        d.point((rr.integers(0, W), rr.integers(0, int(0.5 * H))), fill=(180, 186, 210))
    # distant receding hills near the summit height (the 'only horizon')
    for i, (yy, sh) in enumerate([(0.46, (30, 34, 54)), (0.49, (26, 30, 48)), (0.52, (22, 26, 42))]):
        d.ellipse([-0.2 * W + i * 0.1 * W, yy * H, 1.3 * W, yy * H + 0.4 * H], fill=sh)
    # the foreground mountain he climbs (apex at the summit)
    sx, sy = SUMMIT[0] * W, SUMMIT[1] * H
    d.polygon([(0, H), (0, 0.9 * H), (sx, sy), (0.92 * W, 0.72 * H), (W, 0.8 * H), (W, H)],
              fill=(16, 18, 30))
    return np.asarray(im, np.float32)
BG = build_bg()


def climb_pos(t):
    p = smooth(*T_CLIMB, t)
    return lerp(START[0], SUMMIT[0], p) * W, lerp(START[1], SUMMIT[1], p) * H


def char_state(t):
    if t < T_CLIMB[1]:
        return "walk", climb_pos(t)
    return "stand", (SUMMIT[0] * W, SUMMIT[1] * H)


def lift_amount(t):
    return smooth(11.0, 13.0, t) * (1 - smooth(15.5, 17.0, t))


def render(t):
    a = BG.copy()
    pose, (cx, feety) = char_state(t)
    sitting = t >= T_SIT[0]
    if sitting:
        pose = "sit"
    lift = 0 if sitting else lift_amount(t)
    spr, fy, odx, ody = character(140, pose, t, 1, lift=lift)

    # rim light so the climber reads against the dark slope
    glow(a, cx, feety - 55, 78, [120, 130, 175], 0.34)

    ox = cx + odx
    oy = feety + ody - lift * 0.14 * H
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    # the light dims a little in the empty 'no answer' hold
    dim = 1 - 0.35 * smooth(14.5, 16.0, t) * (1 - smooth(17.5, 18.5, t))
    glow(a, ox, oy, 28 + 18 * lift, [255, 198, 120], (0.6 + 0.4 * lift) * pulse * dim)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(cx - spr.size[0] / 2), int(feety - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.5, 1.5, t) * (1 - smooth(4.5, 5.5, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE ANSWER", FT, 0.10), ("part 4 · the climb", FS, 0.145)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(235, 232, 226, int(230 * tfade)))
    cfade = smooth(18.8, 19.8, t) * (1 - smooth(22.4, 23.4, t))
    if cfade > 0.01:
        yy = int(H * 0.72)
        for ln in ["you climb and climb —", "the summit only gives you sky."]:
            bb = d.textbbox((0, 0), ln, font=FS)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(225, 223, 218, int(215 * cfade)))
            yy += int((bb[3] - bb[1]) * 1.7)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.016)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: rising bass climb; then the answer never comes (music ducks) ----
def bassnote(m, dur=1.6, amp=0.22):
    n = int(dur * SR); t = np.arange(n) / SR; f = midi(m)
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    e = np.exp(-t * 1.6) * np.clip(t / 0.02, 0, 1)
    return (y * e * amp).astype(np.float32)


def bell(m, dur=1.6, amp=0.11):
    n = int(dur * SR); t = np.arange(n) / SR; f = midi(m)
    y = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t)
    return (y * np.exp(-t * 1.6) * np.clip(t / 0.015, 0, 1) * amp).astype(np.float32)


def wind(at_dur, amp=0.09):
    n = int(at_dur * SR)
    nse = np.random.randn(n).astype(np.float32)
    nse = np.convolve(nse, np.ones(200) / 200, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (nse * env * amp)


def footstep(amp=0.18, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    n = int(DUR * SR)
    # music bed, but DUCK it during the empty summit (14.5 -> 17.5)
    music = compose(DUR) * 0.5
    tt = np.arange(n) / SR
    def vsmooth(a, b, x):
        s = np.clip((x - a) / (b - a), 0, 1); return s * s * (3 - 2 * s)
    duck = 1 - 0.8 * (vsmooth(14.5, 15.5, tt) * (1 - vsmooth(17.0, 18.0, tt)))
    music *= duck[:, None]
    L = music[:, 0].copy(); R = music[:, 1].copy()
    def st(sig, at, pan=0.5): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    # climbing: footsteps + an ASCENDING bass line (effort building)
    for m, at in zip([41, 43, 45, 48, 50, 53], CLIMB_STEPS):
        st(bassnote(m), at); st(footstep(), at + 0.05)
    # reach + raise the light (hopeful rising)
    st(bell(72, amp=0.10), 11.4); st(bell(77, amp=0.09), 12.4)
    # ...but no answer: one unresolved bell hanging over wind, then quiet
    st(bell(76, amp=0.08, dur=2.4), 13.8)          # E5 = leading tone, unresolved
    st(wind(4.0), 14.2)
    # when he sits, a soft low melancholy note
    st(bell(53, amp=0.10, dur=2.6), 19.2)          # F3
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.25)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.86
    fi, fo = int(SR), int(2 * SR)
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
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e4.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e4_silent.mp4", "-i", "e4.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "answer_part4.mp4"],
                   check=True, capture_output=True)
    print("Done -> answer_part4.mp4")


if __name__ == "__main__":
    main()
