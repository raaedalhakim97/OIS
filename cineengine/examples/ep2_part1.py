"""
THE CYCLE · part 1 — "The Gift"
The old keeper walks away, leaving a light in the dark. The small one lifts it
awake. The melody is handed over: the old voice fades, the child's voice answers
and takes it. Sparse, slow, dreamy call-and-response (F major). ~22s.
Opening framed to match part 5's ending (the loop).
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
DUR = 22.0
GROUND = 0.80 * H
fx = FX(W, H)
CHILDX = 0.46
LIGHTX = 0.5


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
    a[:] = (np.array([8, 10, 26], np.float32) * (1 - t)
            + np.array([18, 18, 40], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(11, 12, 26))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(13, 14, 28))
    d.rectangle([0, int(GROUND), W, H], fill=(9, 10, 20))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(15)
SX = _r.integers(0, W, 180); SY = _r.integers(0, int(GROUND * 0.98), 180)
SB = _r.uniform(0.3, 1.0, 180); SPH = _r.uniform(0, 6.28, 180)


def render(t):
    a = BG.copy()
    awake = smooth(11.5, 15.5, t)
    tw = 0.5 + 0.5 * np.sin(t * 2 + SPH)
    a[SY, SX] += (SB * tw * (0.2 + 0.8 * awake))[:, None] * np.array([215, 218, 236])

    # the old keeper walks away into the dark, fading
    oldx = lerp(LIGHTX, 0.9, smooth(0.0, 7.0, t)) * W
    oldalpha = 1 - smooth(2.5, 7.5, t)
    if oldalpha > 0.02:
        ospr, ofy, _, _ = character(150, "walk", t, 1)
        o = ospr.copy(); o.putalpha(ospr.split()[3].point(lambda p: int(p * oldalpha)))
        a_im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        a_im.paste(o, (int(oldx - o.size[0] / 2), int(GROUND - ofy)), o)
        a = np.asarray(a_im, np.float32)

    # the child approaches and lifts the light
    childx = lerp(0.40, CHILDX, smooth(5.0, 8.5, t)) * W
    pick = smooth(9.0, 11.0, t)
    lift = smooth(11.5, 14.0, t) * (1 - smooth(18.0, 19.5, t))
    cspr, cfy, codx, cody = character(105, "stand", t, 1, lift=lift)
    chx = childx + codx
    chy = GROUND + cody - lift * 0.15 * H
    # orb: on the ground first, then rises into the child's hand, then lifts
    gx, gy = LIGHTX * W, GROUND - 16
    ox = lerp(gx, chx, pick); oy = lerp(gy, chy, pick)
    obr = (0.3 + 0.2 * pick) if t < 11 else (0.5 + 0.9 * awake)
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    glow(a, ox, oy, 26 + 22 * lift + 14 * awake, [255, 198, 120], obr * pulse)
    if awake > 0.02:
        glow(a, ox, oy, 120 * awake + 20, [255, 200, 140], 0.35 * awake)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(cspr, (int(childx - cspr.size[0] / 2), int(GROUND - cfy)), cspr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.6, 1.6, t) * (1 - smooth(4.4, 5.2, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE CYCLE", FT, 0.10), ("part 1 · the gift", FS, 0.145)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(232, 230, 224, int(230 * tfade)))
    cfade = smooth(15.5, 16.5, t) * (1 - smooth(20.4, 21.4, t))
    if cfade > 0.01:
        yy = int(H * 0.12)
        for ln in ["the light is never yours —", "only yours to carry."]:
            bb = d.textbbox((0, 0), ln, font=FS)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(228, 226, 220, int(220 * cfade)))
            yy += int((bb[3] - bb[1]) * 1.7)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=203, gain=0.72)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: sparse, slow, dreamy hand-over of the melody ----
def footstep(amp=0.15, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    n = int(DUR * SR)
    Lc = np.zeros(n, np.float32); Rc = np.zeros(n, np.float32)
    def st(sig, at, pan): add(Lc, sig * (1 - pan), at); add(Rc, sig * pan, at)
    # sparse pad bed (F -> C -> Dm -> Bb), quiet
    prog = [([53, 57, 60], 41), ([48, 52, 55], 48), ([50, 53, 57], 50), ([46, 50, 53], 46)] * 2
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        p = pad([midi(m) for m in notes], step + 0.4, amp=0.07)
        add(Lc, p, k * step); add(Rc, np.roll(p, 350), k * step)
        add(Lc, bass(midi(br), step + 0.2, amp=0.12), k * step)
        add(Rc, bass(midi(br), step + 0.2, amp=0.12), k * step)
    # old keeper's footsteps fading as he leaves
    for i in range(6):
        st(footstep(amp=0.14 * (1 - i / 7)), 0.6 + i * 0.55, 0.6 + i * 0.03)
    # THE HAND-OVER (sparse, slow): old voice descends & fades (right),
    # the child's voice answers ascending & takes it home (left/center).
    for m, at, amp in [(72, 11.0, 0.26), (69, 12.4, 0.20), (65, 13.8, 0.13)]:   # old, fading
        st(piano(midi(m), 3.0, amp=amp), at, 0.72)
    for m, at, amp in [(65, 12.2, 0.18), (69, 13.6, 0.24), (72, 15.0, 0.28), (77, 16.6, 0.26)]:  # child rising
        st(piano(midi(m), 3.2, amp=amp), at, 0.32)
    # soft echoes (opposite side) for the 'conversation' feel
    for m, at in [(72, 15.7), (77, 17.3)]:
        st(piano(midi(m), 2.6, amp=0.10), at, 0.68)
    st(piano(midi(65), 3.6, amp=0.20), 18.4, 0.5)      # settle home on F
    Lc = reverb(Lc); Rc = reverb(Rc)
    mix = np.tanh(np.stack([Lc, Rc], 1) * 1.2)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi, fo = int(SR), int(2.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e2p_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2p_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 24 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2p.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2p_silent.mp4", "-i", "e2p.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "cycle_part1.mp4"],
                   check=True, capture_output=True)
    print("Done -> cycle_part1.mp4")


if __name__ == "__main__":
    main()
