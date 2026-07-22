"""
THE ANSWER · part 3 — "The Voices"  (point of view: ask others)
The Lightkeeper signals into the dark with his light; a distant light answers
back. Call-and-response in F major, then a thread of light connects them. ~24s.
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
HOR = 0.70
WL = int(HOR * H)
fx = FX(W, H)

T_WALKIN = (0.0, 6.0)
T_WALKOUT = (18.0, 24.0)
MEX = 0.30                 # our lightkeeper x
FARX, FARY = 0.76, 0.60    # the distant light
CALLS = [9.8, 10.5, 11.2]
RESPS = [13.2, 13.9, 14.6]
STEP = 0.52


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def flares(t, times, w=0.16):
    return sum(math.exp(-((t - c) / w) ** 2) for c in times)


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
    a[:] = (np.array([10, 13, 32], np.float32) * (1 - t)
            + np.array([28, 28, 56], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, HOR * H - 0.05 * H, 0.5 * W, HOR * H + 0.3 * H], fill=(18, 20, 38))
    d.ellipse([0.55 * W, HOR * H - 0.09 * H, 1.3 * W, HOR * H + 0.3 * H], fill=(22, 24, 44))
    d.rectangle([0, WL, W, H], fill=(12, 14, 30))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(8)
SX = _r.integers(0, W, 150); SY = _r.integers(0, WL, 150)
SB = _r.uniform(0.3, 1.0, 150); SPH = _r.uniform(0, 6.28, 150)


def char_state(t):
    if t < T_WALKIN[1]:
        return "walk", lerp(0.12, MEX, smooth(*T_WALKIN, t))
    if t < T_WALKOUT[0]:
        return "stand", MEX
    return "walk", lerp(MEX, -0.1, smooth(*T_WALKOUT, t))


def lift_amount(t):
    return smooth(9.0, 12.0, t) * (1 - smooth(16.5, 18.0, t))


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + SPH)
    a[SY, SX] += (SB * tw)[:, None] * np.array([200, 206, 230])

    pose, cxf = char_state(t)
    cx = cxf * W
    lift = lift_amount(t)
    spr, fy, odx, ody = character(150, pose, t, 1, lift=lift)
    ox = cx + odx
    oy = HOR * H + ody - lift * 0.15 * H
    # his light pulses on each CALL
    call = min(1.0, flares(t, CALLS)) * smooth(9.0, 9.6, t)
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    glow(a, ox, oy, 30 + 20 * lift + 26 * call, [255, 198, 120], (0.6 + 0.4 * lift + 0.5 * call) * pulse)

    # the distant light: appears after his call, then ANSWERS with flares
    appear = smooth(11.8, 12.6, t)
    fxp, fyp = FARX * W, FARY * H
    resp = min(1.0, flares(t, RESPS))
    if appear > 0.01:
        glow(a, fxp, fyp, 20 + 30 * resp, [255, 210, 150], (0.35 * appear + 0.6 * resp))

    # a thread of light connects them once both have spoken
    conn = smooth(15.0, 16.6, t) * (1 - smooth(17.6, 18.4, t))
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if conn > 0.02:
        d = ImageDraw.Draw(im, "RGBA")
        ax, ay = ox, oy; bx, by = fxp, fyp
        ccx, ccy = (ax + bx) / 2, min(ay, by) - 0.10 * H
        pts = [((1 - u) ** 2 * ax + 2 * (1 - u) * u * ccx + u ** 2 * bx,
                (1 - u) ** 2 * ay + 2 * (1 - u) * u * ccy + u ** 2 * by) for u in np.linspace(0, 1, 40)]
        d.line(pts, fill=(255, 210, 150, int(200 * conn)), width=max(1, int(3 * conn)))

    im.paste(spr, (int(cx - spr.size[0] / 2), int(HOR * H - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.5, 1.5, t) * (1 - smooth(4.5, 5.5, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE ANSWER", FT, 0.10), ("part 3 · the voices", FS, 0.145)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(235, 232, 226, int(230 * tfade)))
    cfade = smooth(15.2, 16.2, t) * (1 - smooth(22, 23.2, t))
    if cfade > 0.01:
        yy = int(H * 0.12)
        for ln in ["call into the dark —", "someone calls back."]:
            bb = d.textbbox((0, 0), ln, font=FS)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(228, 226, 220, int(220 * cfade)))
            yy += int((bb[3] - bb[1]) * 1.7)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.016)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: call (left) then response (right), in F major ----
def bell(m, dur=1.2, amp=0.12):
    n = int(dur * SR); t = np.arange(n) / SR; f = midi(m)
    y = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.18 * np.sin(2 * np.pi * 3 * f * t)
    return (y * np.exp(-t * 2.1) * np.clip(t / 0.015, 0, 1) * amp).astype(np.float32)


def footstep(amp=0.2, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    music = compose(DUR) * 0.5
    L = music[:, 0].copy(); R = music[:, 1].copy()
    def st(sig, at, pan=0.5): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    for (s, e) in (T_WALKIN, T_WALKOUT):
        tt = s + 0.3
        while tt < e - 0.2: st(footstep(), tt); tt += STEP
    # his CALL — ascending F A C, panned left
    for m, at in zip([65, 69, 72], CALLS):
        st(bell(m, amp=0.12), at, pan=0.24)
    # the RESPONSE — warm A C F, panned right (a harmonic answer)
    for m, at in zip([69, 72, 77], RESPS):
        st(bell(m, amp=0.12), at, pan=0.76)
    # union: soft F-major chord centered as the thread connects
    for m in [65, 69, 72]:
        st(bell(m, amp=0.07), 15.4, pan=0.5)
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
        Image.fromarray(render(a.preview)).save("e3_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e3_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e3.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e3_silent.mp4", "-i", "e3.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "answer_part3.mp4"],
                   check=True, capture_output=True)
    print("Done -> answer_part3.mp4")


if __name__ == "__main__":
    main()
