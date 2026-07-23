"""
THE KNOWLEDGE · part 3 — "The Difference"   (after Robert Frost, "The Road Not Taken", public domain)
Ages hence, the Lightkeeper looks back on the whole road he chose — the path he
walked glows behind him as one long river of light. The famous last lines. He
lifts the light to the dark ahead and walks on. The road less traveled. ~46s.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, grass_step, step_note, walk_notes, poem_sway
from ep4_part1 import leaf_rustle, bez

W, H = 1080, 1920
FPS = 24
DUR = 46.0
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
FS = font(46); FBIG = font(58); FSM = font(34)


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
    a[:] = (np.array([22, 17, 22], np.float32) * (1 - t)       # deeper dusk, later hour
            + np.array([58, 44, 36], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rr = np.random.default_rng(8)
    for tx in (0.05, 0.15, 0.85, 0.94):
        x = tx * W; tw = rr.uniform(11, 22)
        d.rectangle([x - tw, 0.26 * H, x + tw, GROUND], fill=(18, 13, 14))
        d.ellipse([x - 0.13 * W, 0.10 * H, x + 0.13 * W, 0.38 * H], fill=(22, 16, 16))
    d.rectangle([0, int(GROUND), W, H], fill=(28, 20, 17))
    for _ in range(120):
        gx = rr.integers(0, W); gy = rr.integers(int(GROUND), H)
        d.ellipse([gx, gy, gx + 6, gy + 4], fill=(88, 64, 34))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(31)
STARX = _r.integers(0, W, 120); STARY = _r.integers(0, int(0.25 * H), 120)
STARB = _r.uniform(0.3, 1.0, 120); STARPH = _r.uniform(0, 6.28, 120)

# the long road already walked — a winding river of light coming up from behind
ROAD = [(0.5, 0.98), (0.62, 0.80), (0.40, 0.64), (0.52, 0.50)]   # cubic-ish via two bez halves
# forward, into the dark
AHEAD = [(0.52, 0.50), (0.60, 0.40), (0.66, 0.30)]

_r2 = np.random.default_rng(17)
LX = _r2.uniform(0, 1, 26); LY0 = _r2.uniform(-0.2, 1.0, 26)
LSP = _r2.uniform(0.02, 0.05, 26); LPH = _r2.uniform(0, 6.28, 26); LSZ = _r2.uniform(4, 9, 26)

TEXT = [
    (2.0, 7.4, "I shall be telling this\nwith a sigh", FS, 0.12),
    (8.0, 13.4, "somewhere ages\nand ages hence:", FS, 0.12),
    (14.2, 19.6, "Two roads diverged\nin a wood, and I —", FS, 0.12),
    (20.4, 26.4, "I took the one\nless traveled by,", FBIG, 0.11),
    (27.4, 34.0, "and that has made\nall the difference.", FBIG, 0.11),
    (35.6, 40.0, "the more you know,\nthe more you observe.", FS, 0.12),
    (41.2, 45.6, "the road not taken · iii", FSM, 0.90),
]
HITS = [2.0, 8.0, 14.2, 20.4, 27.4, 35.6]   # line onsets the keeper rocks to


def road_pt(u):
    # two quadratic halves stitched at ROAD[1]/ROAD[2] midpoint region
    if u < 0.5:
        return bez(ROAD[0], ROAD[1], ROAD[2], u / 0.5)
    return bez(ROAD[1], ROAD[2], ROAD[3], (u - 0.5) / 0.5)


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([230, 214, 180])
    for i in range(len(LX)):
        ly = (LY0[i] + t * LSP[i]) % 1.2 - 0.1
        lx = (LX[i] + 0.03 * math.sin(t * 0.8 + LPH[i]))
        px, py = int(lx * W), int(ly * H)
        if 0 <= py < H:
            glow(a, px, py, LSZ[i], [150, 110, 60], 0.26)

    # the walked road lights up fully by mid-video (memory of the whole journey)
    lit = smooth(3, 20, t)
    n = 34
    for i in range(n):
        u = i / (n - 1)
        px, py = road_pt(u)
        seq = smooth(0, lit, u) if lit > 0 else 0
        fade = 0.5 + 0.5 * (1 - u)
        twk = 0.7 + 0.3 * math.sin(t * 2.5 + i * 0.5)
        glow(a, px * W, py * H, 6 + 3 * (u > 0.6), [255, 200, 125], 0.7 * seq * fade * twk)

    # the road ahead — faint, lifts brighter as he raises the light (payoff)
    lift = smooth(34, 42, t)
    for i in range(12):
        u = i / 11
        px, py = bez(AHEAD[0], AHEAD[1], AHEAD[2], u)
        glow(a, px * W, py * H, 6, [255, 205, 140], (0.12 + 0.5 * lift) * (1 - u) ** 0.5)

    # keeper stands near the crest of the walked road, then lifts the light forward
    kx, ky, ksz = 0.52 * W, 0.52 * H, 118
    pose = "front" if t < 33 else "lift"
    # rock with the verse; as he lifts the light the sway settles and leans into it
    lean = poem_sway(t, HITS, bias=0.05 * lift) * (1 - 0.5 * lift)
    spr, fy, odx, ody = character(ksz, pose, t, 1, lift=lift, lean=lean)
    ox = kx + odx; oy = ky + ody
    glow(a, ox, oy, 26 + 8 * lift, [255, 200, 130], 0.95 * (0.92 + 0.08 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx - spr.size[0] / 2), int(ky - fy)), spr)

    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt, f, yv) in TEXT:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            yy = int(H * yv)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=f)
                col = (170, 150, 120, int(180 * fade)) if f is FSM else (236, 228, 214, int(238 * fade))
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f, fill=col)
                yy += int((bb[3] - bb[1]) * 1.5)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=200, gain=0.72)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    for at, am, sd, pan in [(1.5, 0.045, 6, 0.45), (16.0, 0.04, 3, 0.6), (33.0, 0.045, 9, 0.4)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.05, 53), 12.0, 0.7); st(owl(0.05, 48), 30.0, 0.3)
    cp = crickets(14.0, 0.006, 7); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 6.0, 0.5)
    # INTERACTIVE MUSICAL STEPS — a step to arrive, then walking on into the dark
    # at the end: an ascending phrase, the light rising as it goes.
    walk_notes(st, [2.5], [53], amp=0.11, base_pan=0.5)
    walk_notes(st, [40.0, 42.0, 44.0], [57, 60, 65], amp=0.12, base_pan=0.55)
    for at in (10.0, 25.0): st(leaf_rustle(0.03), at, np.random.uniform(0.3, 0.7))
    # PIANO — the road lighting up: a warm ascending F-major phrase (the journey)
    for i, m in enumerate([53, 57, 60, 65]):
        st(piano(midi(m), 5.0, amp=0.12), 3.0 + i * 1.3, 0.5)
    st(piano(midi(53), 6.0, amp=0.13), 14.2, 0.45)   # F — two roads diverged (callback)
    # the payoff line "less traveled by" — a bright lifted C, then the difference on high F
    st(piano(midi(60), 6.0, amp=0.14), 20.4, 0.55)   # C
    st(piano(midi(65), 7.0, amp=0.15), 27.4, 0.5)    # high F — 'all the difference'
    st(bass(midi(41), 8.0, amp=0.10), 27.0, 0.5)     # low F root, warmth under it
    # channel signature: resolve gently back to F (loops to episode's first note)
    st(piano(midi(53), 8.0, amp=0.13), 35.6, 0.5)
    p = pad([midi(53), midi(57), midi(60), midi(65)], 14.0, amp=0.055)
    add(L, p, 20.0); add(R, np.roll(p, 400), 20.0)
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(SR), int(4.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e4c_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e4c_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e4c.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e4c_silent.mp4", "-i", "e4c.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "knowledge_part3.mp4"],
                   check=True, capture_output=True)
    print("Done -> knowledge_part3.mp4")


if __name__ == "__main__":
    main()
