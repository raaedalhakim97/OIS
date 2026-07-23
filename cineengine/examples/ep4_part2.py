"""
THE KNOWLEDGE · part 2 — "The Leaves"   (after Robert Frost, "The Road Not Taken", public domain)
Both roads lie the same, buried in leaves no step has trodden. The Lightkeeper
walks the chosen road, glances back once at the road not taken (it glows, soft,
unreachable), then keeps on — knowing way leads on to way. ~44s.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, grass_step, step_note, walk_notes, poem_sway
from ep4_part1 import leaf_rustle, bez

W, H = 1080, 1920
FPS = 24
DUR = 44.0
GROUND = 0.80 * H
fx = FX(W, H)


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FS = font(46); FSM = font(34)


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
    a[:] = (np.array([26, 20, 24], np.float32) * (1 - t)
            + np.array([70, 52, 40], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rr = np.random.default_rng(3)
    for tx in (0.04, 0.14, 0.24, 0.78, 0.88, 0.97):
        x = tx * W; tw = rr.uniform(11, 24)
        d.rectangle([x - tw, 0.28 * H, x + tw, GROUND], fill=(20, 15, 16))
        d.ellipse([x - 0.14 * W, 0.12 * H, x + 0.14 * W, 0.40 * H], fill=(24, 18, 18))
    d.rectangle([0, int(GROUND), W, H], fill=(30, 22, 18))
    # a thick carpet of fallen leaves — 'no step had trodden black'
    for _ in range(220):
        gx = rr.integers(0, W); gy = rr.integers(int(GROUND) - 20, H)
        shade = rr.integers(0, 3)
        col = [(96, 70, 38), (120, 84, 40), (70, 52, 30)][shade]
        d.ellipse([gx, gy, gx + rr.integers(5, 9), gy + rr.integers(3, 6)], fill=col)
    return np.asarray(im, np.float32)
BG = build_bg()

# the fork sits behind/below now; the road not taken recedes to the right-rear
FORK = (0.52, 0.86)
NOT_TAKEN = [FORK, (0.72, 0.72), (0.83, 0.60)]     # the road he didn't choose
TAKEN = [(0.30, 0.66), (0.24, 0.52), (0.20, 0.40)]  # the one he's on, ahead

_r = np.random.default_rng(21)
LX = _r.uniform(0, 1, 30); LY0 = _r.uniform(-0.2, 1.0, 30)
LSP = _r.uniform(0.02, 0.06, 30); LPH = _r.uniform(0, 6.28, 30); LSZ = _r.uniform(4, 10, 30)

TEXT = [
    (2.0, 7.2, "And both that morning\nequally lay", FS, 0.12),
    (7.7, 13.0, "in leaves no step\nhad trodden black.", FS, 0.12),
    (13.8, 19.2, "Oh, I kept the first\nfor another day!", FS, 0.12),
    (20.0, 25.4, "Yet knowing how\nway leads on to way,", FS, 0.12),
    (26.2, 32.0, "I doubted if I should\never come back.", FS, 0.12),
    (33.0, 39.5, "some doors close\nsoftly behind you.", FS, 0.12),
    (40.2, 43.5, "the road not taken · ii", FSM, 0.90),
]
HITS = [2.0, 7.7, 13.8, 20.0, 26.2, 33.0]   # line onsets the keeper rocks to


def draw_road(a, pts, bright, t, glint=1.0):
    n = 20
    for i in range(n):
        u = i / (n - 1)
        px, py = bez(pts[0], pts[1], pts[2], u)
        fade = (1 - u) ** 0.6
        tw = 0.7 + 0.3 * math.sin(t * 3 + i * 0.6)
        glow(a, px * W, py * H, 6 + 3 * (u < 0.4), [255, 205, 130],
             bright * fade * tw * glint * 0.8)


def render(t):
    a = BG.copy()
    for i in range(len(LX)):
        ly = (LY0[i] + t * LSP[i]) % 1.2 - 0.1
        lx = (LX[i] + 0.03 * math.sin(t * 0.8 + LPH[i]))
        px, py = int(lx * W), int(ly * H)
        if 0 <= py < H:
            glow(a, px, py, LSZ[i], [150, 110, 60], 0.28)

    # the road ahead is always faintly lit; the road-not-taken glows on the glance
    ahead = 0.45 + 0.2 * math.sin(t * 0.6)
    glance = smooth(20, 23, t) * (1 - smooth(30, 33, t))   # looks back mid-poem
    draw_road(a, TAKEN, 0.5 + 0.2 * ahead, t)
    draw_road(a, NOT_TAKEN, 0.18 + 0.55 * glance, t, glint=0.9)

    # keeper walks the chosen road; pauses and turns to glance back, then on
    walk = smooth(2, 40, t)
    kx = lerp(0.34, 0.24, walk) * W
    ky = lerp(0.70, 0.50, walk) * H
    ksz = int(lerp(120, 92, walk))
    looking = 20 <= t <= 30
    face = 1 if looking else -1                            # turn back to the fork, then forward
    pose = "front" if looking else "walk"
    # rock with the verse; lean back toward the fork on the glance, forward as he walks on
    lean = poem_sway(t, HITS, bias=0.07 * glance - 0.04 * (1 - glance) * walk)
    spr, fy, odx, ody = character(ksz, pose, t, face, lean=lean)
    ox = kx + odx; oy = ky + ody
    glow(a, ox, oy, 24, [255, 200, 130], 0.9 * (0.92 + 0.08 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt, f, yv) in TEXT:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.7, e - 0.7, e], [0, 1, 1, 0])
            yy = int(H * yv)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=f)
                col = (232, 226, 214, int(235 * fade)) if f is FS else (170, 150, 120, int(180 * fade))
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f, fill=col)
                yy += int((bb[3] - bb[1]) * 1.5)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    for at, am, sd, pan in [(1.5, 0.045, 4, 0.45), (17.0, 0.04, 7, 0.6), (34.0, 0.045, 2, 0.4)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.05, 53), 11.0, 0.7); st(owl(0.05, 48), 28.0, 0.3)
    cp = crickets(12.0, 0.006, 5); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 6.0, 0.5)
    # INTERACTIVE MUSICAL STEPS — each footfall is a piano note. Walking on into
    # the wood: a gentle settling phrase, then two soft steps after the glance.
    walk_notes(st, [2.5, 5.0, 7.5], [60, 57, 55], amp=0.12, base_pan=0.42)
    walk_notes(st, [36.0, 38.0], [53, 57], amp=0.12, base_pan=0.42)
    # leaf rustles for the deep leaf carpet
    for at in (4.0, 10.0, 24.0, 33.0): st(leaf_rustle(0.035), at, np.random.uniform(0.3, 0.7))
    # PIANO — slow F major, quarter pace
    st(piano(midi(53), 6.0, amp=0.13), 2.0, 0.5)     # F — both lay the same
    st(piano(midi(57), 5.0, amp=0.10), 13.8, 0.5)    # A — kept the first
    # the glance back: the road-not-taken answers with one soft note, panned to it
    st(piano(midi(60), 5.5, amp=0.11), 20.5, 0.7)    # C — a look over the shoulder
    st(piano(midi(53), 6.5, amp=0.12), 26.2, 0.45)   # F — doubt, settle
    # walking-on descent, letting it go (falling line resolves to F)
    for i, m in enumerate([60, 57, 55, 53]):
        st(piano(midi(m), 4.5, amp=0.10), 33.0 + i * 1.2, 0.4)
    p = pad([midi(53), midi(57), midi(60)], 10.0, amp=0.05)
    add(L, p, 19.0); add(R, np.roll(p, 400), 19.0)
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(SR), int(3.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e4b_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e4b_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e4b.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e4b_silent.mp4", "-i", "e4b.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "knowledge_part2.mp4"],
                   check=True, capture_output=True)
    print("Done -> knowledge_part2.mp4")


if __name__ == "__main__":
    main()
