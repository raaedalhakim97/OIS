"""
THE CYCLE · part 2 — "The Carry"  (~60s)
The keeper walks their road, light held high, while time passes around them:
dawn -> day -> dusk -> night. They do not set it down. Fuller, busier
call-and-response piano over a steady walking pulse. Black silhouettes.
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
KX = 0.42
fx = FX(W, H)
yy, xx = fx.yy, fx.xx


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


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


# day->night keyframes (time, sky_top, sky_bottom)
SKY = [
    (0.0,  [40, 44, 92],  [232, 150, 100]),   # dawn
    (15.0, [66, 116, 196], [198, 214, 240]),  # day
    (30.0, [72, 56, 120], [252, 150, 92]),    # dusk
    (45.0, [9, 12, 32],   [24, 24, 52]),      # night
    (60.0, [40, 44, 92],  [232, 150, 100]),   # back to dawn (loop)
]


def sky_colors(t):
    for i in range(len(SKY) - 1):
        t0, a0, b0 = SKY[i]; t1, a1, b1 = SKY[i + 1]
        if t0 <= t <= t1:
            u = smooth(t0, t1, t)
            top = [lerp(a0[k], a1[k], u) for k in range(3)]
            bot = [lerp(b0[k], b1[k], u) for k in range(3)]
            return np.array(top, np.float32), np.array(bot, np.float32)
    return np.array(SKY[-1][1], np.float32), np.array(SKY[-1][2], np.float32)


_r = np.random.default_rng(19)
STARX = _r.integers(0, W, 200); STARY = _r.integers(0, int(GROUND * 0.95), 200)
STARB = _r.uniform(0.3, 1.0, 200); STARPH = _r.uniform(0, 6.28, 200)
# far passing lights (other keepers on their roads)
PASS = [(0.2, 0.62, 0.010, 0.6), (0.7, 0.66, 0.016, 0.8), (0.45, 0.6, 0.008, 0.5)]

NARR = [
    (2.0, 7.0, "the road did not end\nwhere they left it."),
    (7.5, 13.0, "so you walked."),
    (13.5, 19.0, "through the morning\nof your life —"),
    (19.5, 25.0, "and the long afternoon."),
    (26.0, 31.0, "the light grew heavy."),
    (31.5, 37.0, "your arms grew tired."),
    (37.5, 43.0, "but you did not\nset it down."),
    (43.5, 49.0, "you carried it —"),
    (49.5, 55.0, "not because it was yours,"),
    (55.0, 60.0, "but because\nsomeone must."),
]


def render(t):
    top, bot = sky_colors(t)
    tg = (yy / H)[..., None]
    a = (top * (1 - tg) + bot * tg)

    nightf = math.exp(-((t - 45) / 13) ** 2) + 0.4 * math.exp(-((t - 60) / 6) ** 2)
    # stars
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * nightf)[:, None] * np.array([215, 218, 236])
    # sun (first half) / moon (second half) arcing across
    if t < 32:
        p = smooth(4, 30, t); sunx = lerp(0.15, 0.9, p) * W
        suny = (0.5 - 0.34 * math.sin(math.pi * p)) * H
        glow(a, sunx, suny, 90, [255, 236, 180], 0.9 * (1 - smooth(28, 32, t)))
    if t > 36:
        p = smooth(38, 60, t); mx = lerp(0.12, 0.88, p) * W
        my = (0.5 - 0.32 * math.sin(math.pi * p)) * H
        glow(a, mx, my, 70, [226, 232, 255], 0.8 * smooth(36, 42, t))

    # scrolling parallax hills
    scroll = t * 90
    xcol = np.arange(W, dtype=np.float32)
    for spd, base, amp, freq, col in [
        (0.4, 0.74, 0.05, 3.0, np.array([0.30, 0.32, 0.42])),
        (0.8, 0.78, 0.06, 4.5, np.array([0.22, 0.24, 0.34])),
        (1.4, 0.82, 0.05, 6.0, np.array([0.15, 0.16, 0.26])),
    ]:
        ridge = base * H - amp * H * np.sin((xcol / W * freq * 6.283) + scroll * spd * 0.01)
        m = (yy > ridge[None, :])[..., None]
        shade = (col * 255 * (0.5 + 0.5 * (1 - nightf)))
        a = a * (1 - m) + shade * m
    a[int(GROUND):] = np.array([18, 19, 34], np.float32)

    # passing far lights
    for (px0, py, spd, br) in PASS:
        px = ((px0 - t * spd) % 1.3 - 0.15) * W
        glow(a, px, py * H, 12, [255, 205, 140], 0.4 * br)

    # keeper walks in place, light held HIGH (with a gentle carrying bob)
    lift = 0.72 + 0.06 * math.sin(t * 3.0)
    kspr, kfy, kodx, kody = character(150, "walk", t, 1, lift=lift)
    kx = KX * W
    ox = kx + kodx; oy = GROUND + kody - lift * 0.15 * H
    glow(a, ox, oy, 30, [255, 198, 120], 0.9 * (0.9 + 0.1 * math.sin(t * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(GROUND - kfy)), kspr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.4, 1.4, t) * (1 - smooth(11.5, 12.5, t))
    if tfade > 0.01:
        for txt, f, yv in (("THE CYCLE", FT, 0.08), ("part 2 · the carry", FS, 0.125)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yv)), txt, font=f,
                   fill=(232, 230, 224, int(225 * tfade)))
    for (s, e, txt) in NARR:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            yv = int(H * 0.80)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=FS)
                d.text(((W - (bb[2] - bb[0])) // 2, yv), ln, font=FS, fill=(230, 228, 222, int(220 * fade)))
                yv += int((bb[3] - bb[1]) * 1.6)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.38)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: steady walking pulse + dense call-&-response + memory echoes ----
def footstep(amp=0.11, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 62 * t) * np.exp(-t * 32)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.4) * amp)


def build_audio():
    n = int(DUR * SR)
    Lc = np.zeros(n, np.float32); Rc = np.zeros(n, np.float32)
    def st(sig, at, pan): add(Lc, sig * (1 - pan), at); add(Rc, sig * pan, at)
    def note(m, at, pan, amp=0.2, dur=2.6, mem=True):
        st(piano(midi(m), dur, amp=amp), at, pan)
        if mem:                                       # memory: soft echoes returning
            st(piano(midi(m), dur * 0.8, amp=amp * 0.42), at + 0.5, 1 - pan)
            st(piano(midi(m), dur * 0.55, amp=amp * 0.22), at + 1.4, pan)

    prog = [([53, 57, 60], 41), ([48, 52, 55], 48), ([50, 53, 57], 50), ([46, 50, 53], 46)] * 3
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        p = pad([midi(m) for m in notes], step + 0.4, amp=0.075)
        add(Lc, p, k * step); add(Rc, np.roll(p, 350), k * step)
        add(Lc, bass(midi(br), step + 0.2, amp=0.12), k * step)
        add(Rc, bass(midi(br), step + 0.2, amp=0.12), k * step)

    # steady walking pulse (momentum) — every ~0.55s, low, alternating feet
    tt = 1.0
    i = 0
    while tt < 58:
        st(footstep(amp=0.10), tt, 0.5 + (0.06 if i % 2 else -0.06)); tt += 0.55; i += 1

    # dense continuous call-and-response (F-major pentatonic), busier than part 1
    PENTA = [60, 62, 65, 67, 69, 72, 74, 77, 79, 81]
    rng = np.random.default_rng(23)
    tt = 4.0
    while tt < 56:
        dens = 0.55 + 0.45 * math.sin((tt - 4) / 52 * math.pi)   # fullest mid-journey
        base = rng.integers(2, 6)
        call = [PENTA[base], PENTA[base + 1], PENTA[base + 2]]
        for j, m in enumerate(call):
            note(m, tt + j * 0.36, 0.28, amp=0.14 * dens, dur=2.4)
        resp = [PENTA[base + 2], PENTA[base + 1], PENTA[base], PENTA[max(0, base - 1)]]
        for j, m in enumerate(resp):
            note(m, tt + 1.0 + j * 0.36, 0.72, amp=0.12 * dens, dur=2.4, mem=False)
        tt += rng.uniform(2.0, 2.8)

    # a lift on 'but you did not set it down' — a rising resolve figure
    for i, m in enumerate([65, 69, 72, 77]):
        st(piano(midi(m), 2.8, amp=0.16), 38.0 + i * 0.5, 0.5)
    st(piano(midi(65), 4.0, amp=0.2), 57.5, 0.5)          # home

    Lc = reverb(Lc); Rc = reverb(Rc)
    mix = np.tanh(np.stack([Lc, Rc], 1) * 1.2)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi, fo = int(1.5 * SR), int(3 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e2b_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2b_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2b.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2b_silent.mp4", "-i", "e2b.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "cycle_part2.mp4"],
                   check=True, capture_output=True)
    print("Done -> cycle_part2.mp4")


if __name__ == "__main__":
    main()
