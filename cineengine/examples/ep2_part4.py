"""
THE CYCLE · part 4 — "The Fade"  (~60s)
The keeper grows old; the light dims not from the wind, but from within. Every
movement makes sound: the LIGHT SINGS as it moves (its motion -> a warm tone,
pitch tracking its height), footsteps, the slow settle. Warm, low, fading.
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
DUR = 60.0
GROUND = 0.80 * H
fx = FX(W, H)


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


# ---- shared movement: the light's raise amount over time (drives BOTH picture
# and the light's voice) ----
def lift_traj(t):
    if t < 10:
        return smooth(0, 10, t) * 0.60                       # lift it as they arrive
    if t < 25:
        return 0.60 + 0.12 * math.sin((t - 10) * 0.85)       # tired sway
    if t < 46:
        return max(0.05, lerp(0.60, 0.08, smooth(25, 46, t)) + 0.03 * math.sin((t - 25) * 0.6))
    return 0.05 + 0.025 * math.sin((t - 46) * 0.5)           # low, faint tremor


def light_dim(t):
    return 1 - 0.72 * smooth(18, 54, t)                      # dims from within


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FT = font(58); FS = font(42)


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
            + np.array([17, 17, 38], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(19, 21, 40))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(22, 24, 44))
    d.rectangle([0, int(GROUND), W, H], fill=(16, 17, 33))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(27)
STARX = _r.integers(0, W, 170); STARY = _r.integers(0, int(GROUND * 0.95), 170)
STARB = _r.uniform(0.3, 1.0, 170); STARPH = _r.uniform(0, 6.28, 170)

NARR = [
    (2.0, 7.0, "the years grew long."),
    (7.5, 13.0, "the road, longer."),
    (13.5, 18.5, "and the light —"),
    (19.0, 25.0, "it did not dim\nfrom the wind."),
    (26.0, 31.5, "it dimmed\nfrom you."),
    (32.0, 37.5, "your steps grew slow."),
    (38.0, 43.5, "your arm, tired."),
    (44.0, 49.5, "you had carried it\nso far."),
    (50.0, 55.0, "and the dark\nfelt close again."),
    (55.0, 60.0, "but not yet.\nnot yet."),
]


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.6)[:, None] * np.array([208, 212, 232])

    kx = lerp(0.26, 0.46, smooth(0, 10, t)) * W
    sitting = t >= 46
    pose = "sit" if sitting else ("walk" if t < 10 else "stand")
    lift = lift_traj(t)
    kspr, kfy, kodx, kody = character(150, pose, t, 1, lift=lift)
    ox = kx + kodx; oy = GROUND + kody - lift * 0.15 * H
    dim = light_dim(t)
    flick = 0.85 + 0.15 * math.sin(t * 3) - 0.15 * (1 - dim) * (np.random.rand() * 0.5)
    glow(a, ox, oy, 22 + 16 * lift * dim, [255, 196, 120], (0.35 + 0.55 * lift) * dim * flick)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(GROUND - kfy)), kspr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.4, 1.4, t) * (1 - smooth(11.5, 12.5, t))
    if tfade > 0.01:
        for txt, f, yv in (("THE CYCLE", FT, 0.08), ("part 4 · the fade", FS, 0.125)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yv)), txt, font=f,
                   fill=(232, 230, 224, int(225 * tfade)))
    for (s, e, txt) in NARR:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            yv = int(H * 0.82)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=FS)
                d.text(((W - (bb[2] - bb[0])) // 2, yv), ln, font=FS, fill=(228, 226, 220, int(215 * fade)))
                yv += int((bb[3] - bb[1]) * 1.6)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: the LIGHT SINGS its movement + footsteps + sparse fading notes ----
def footstep(amp=0.11, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 60 * t) * np.exp(-t * 32)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.4) * amp)


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # --- THE LIGHT'S VOICE: a warm tone whose pitch tracks the light's height,
    #     louder when it MOVES, quieter when still; fades as the light dims. ---
    ct = np.linspace(0, DUR, 6000)
    lift_c = np.array([lift_traj(x) for x in ct], np.float32)
    dim_c = np.array([light_dim(x) for x in ct], np.float32)
    at = np.arange(n) / SR
    lift_a = np.interp(at, ct, lift_c)
    dim_a = np.interp(at, ct, dim_c)
    freq = 78.0 * 2 ** (lift_a * 2.2)                    # ~78..185 Hz (warm/low)
    speed = np.abs(np.gradient(lift_a) * SR)
    spd_n = np.clip(speed / 1.8, 0, 1)
    amp = (0.05 + 0.15 * spd_n) * (0.4 + 0.6 * dim_a)    # sings on movement, fades out
    ph = np.cumsum(2 * np.pi * freq / SR)
    voice = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph)) * amp
    L += voice * 0.55; R += voice * 0.55

    # soft low pad + bass bed
    prog = [([53, 57, 60], 41), ([50, 53, 57], 38), ([48, 52, 55], 43), ([46, 50, 53], 34)] * 3
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        p = pad([midi(m) for m in notes], step + 0.4, amp=0.06)
        add(L, p, k * step); add(R, np.roll(p, 350), k * step)
        add(L, bass(midi(br), step + 0.2, amp=0.10), k * step)
        add(R, bass(midi(br), step + 0.2, amp=0.10), k * step)

    # slow footsteps as they walk in (0-10)
    tt = 0.8
    while tt < 9.5:
        st(footstep(), tt, 0.5); tt += 0.72

    # sparse fading piano — warm, spreading further apart as the light dies
    notes = [(12, 57), (18.5, 53), (26, 57), (33, 53), (40, 48), (47, 45), (54, 41)]
    for i, (att, m) in enumerate(notes):
        amp_i = 0.18 * (1 - i / (len(notes) + 1))
        st(piano(midi(m), 4.2, amp=amp_i), att, 0.42)
        st(piano(midi(m), 3.0, amp=amp_i * 0.4), att + 0.7, 0.6)   # a tired echo

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.2)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.88
    fi, fo = int(1.5 * SR), int(3.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e2d_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2d_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2d.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2d_silent.mp4", "-i", "e2d.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "cycle_part4.mp4"],
                   check=True, capture_output=True)
    print("Done -> cycle_part4.mp4")


if __name__ == "__main__":
    main()
