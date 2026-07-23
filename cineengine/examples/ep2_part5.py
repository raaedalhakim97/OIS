"""
THE CYCLE · part 5 — "The Passing"  (finale, ~60s)
The fading keeper meets a small lost one and gives the light away. It awakens in
their hands; the keeper walks on into the dark. The light's voice sings as it
passes and reignites; the melody hands over (old fading, child rising). The last
shot + last note loop back to part 1. Warm, low, every movement heard.
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
CHILD_X = 0.58                       # child on the right; old keeper faces them
LOW_Y = GROUND - 0.13 * H
HIGH_Y = GROUND - 0.13 * H - 0.16 * H


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


# ---- shared movement trajectories (drive BOTH picture and the light's voice) ----
def x_old(t):
    if t < 16: return 0.25
    if t < 26: return lerp(0.25, 0.42, smooth(16, 26, t))   # walk toward the child
    if t < 50: return 0.42                                   # stop, face them, give
    return lerp(0.42, 0.08, smooth(50, 60, t))               # turn, walk away into the dark

def orb_x(t):
    ohx = x_old(t) * W + 40          # old faces right -> hand on the child's side
    chx = CHILD_X * W - 34           # child faces left -> hand on the old keeper's side
    if t < 28: return ohx
    if t < 38: return lerp(x_old(28) * W + 40, chx, smooth(28, 38, t))
    return chx

def orb_y(t):
    if t < 38: return LOW_Y
    if t < 46: return lerp(LOW_Y, HIGH_Y, smooth(38, 46, t))
    return HIGH_Y - 4 * math.sin((t - 46) * 0.5)

def orb_bright(t):
    if t < 28: return 0.22 + 0.05 * math.sin(t * 3)
    if t < 38: return 0.28
    return 0.30 + 1.15 * smooth(38, 47, t)

def orb_height_norm(t):
    return (LOW_Y - orb_y(t)) / (LOW_Y - HIGH_Y)


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
    a[:] = (np.array([6, 8, 22], np.float32) * (1 - t)
            + np.array([15, 15, 36], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(18, 20, 38))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(21, 23, 42))
    d.rectangle([0, int(GROUND), W, H], fill=(15, 16, 32))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(41)
STARX = _r.integers(0, W, 200); STARY = _r.integers(0, int(GROUND * 0.95), 200)
STARB = _r.uniform(0.3, 1.0, 200); STARPH = _r.uniform(0, 6.28, 200)

NARR = [
    (2.0, 7.0, "your light was almost out."),
    (8.0, 14.0, "then — someone.\nsmall. lost."),
    (15.0, 21.0, "with no light\nof their own."),
    (22.0, 27.5, "you had so little left."),
    (28.0, 34.0, "but someone, once,\ngave it to you."),
    (35.0, 40.5, "so you gave it —"),
    (41.0, 46.5, "all of it."),
    (47.0, 52.5, "and it remembered\nhow to shine."),
    (52.3, 56.2, "the light goes on."),
    (56.8, 60.0, "it always does."),
]


def render(t):
    a = BG.copy()
    star_amt = 0.18 + 0.8 * smooth(40, 50, t)
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * star_amt)[:, None] * np.array([215, 218, 236])

    # old keeper — walks to the child, FACES them to give, then turns away & fades
    oldx = x_old(t) * W
    old_pose = "walk" if (16 < t < 26 or t > 50) else "stand"
    old_face = 1 if t < 49.5 else -1           # face the child while giving; face away to leave
    ospr, ofy, oodx, oody = character(150, old_pose, t, old_face, lift=0.0)
    old_alpha = 1 - smooth(50.5, 60, t)

    # child — appears, receives, lifts it awake
    child_ap = smooth(8, 13, t)
    child_lift = smooth(38, 46, t) * 0.75
    cspr, cfy, codx, cody = character(105, "stand", t, -1, lift=child_lift)

    # THE LIGHT (its own trajectory), brightness reignites as the child lifts it
    ox, oy = orb_x(t), orb_y(t)
    br = orb_bright(t)
    glow(a, ox, oy, 22 + 26 * orb_height_norm(t), [255, 198, 122], min(1.6, br) * (0.9 + 0.1 * math.sin(t * 3)))
    aw = smooth(40, 50, t)
    if aw > 0.02:
        glow(a, ox, oy, 150 * aw + 30, [255, 202, 140], 0.4 * aw)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if child_ap > 0.02:
        c = cspr.copy(); c.putalpha(cspr.split()[3].point(lambda p: int(p * child_ap)))
        im.paste(c, (int(CHILD_X * W - c.size[0] / 2), int(GROUND - cfy)), c)
    if old_alpha > 0.02:
        o = ospr.copy(); o.putalpha(ospr.split()[3].point(lambda p: int(p * old_alpha)))
        im.paste(o, (int(oldx - o.size[0] / 2), int(GROUND - ofy)), o)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.4, 1.4, t) * (1 - smooth(11.5, 12.5, t))
    if tfade > 0.01:
        for txt, f, yv in (("THE CYCLE", FT, 0.08), ("part 5 · the passing", FS, 0.125)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yv)), txt, font=f,
                   fill=(232, 230, 224, int(225 * tfade)))
    for (s, e, txt) in NARR:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            yv = int(H * 0.83)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=FS)
                d.text(((W - (bb[2] - bb[0])) // 2, yv), ln, font=FS, fill=(230, 228, 222, int(218 * fade)))
                yv += int((bb[3] - bb[1]) * 1.6)
    # loop hint at the very end
    lp = smooth(58.5, 59.3, t)
    if lp > 0.01:
        ln = "↺  it begins again"
        bb = d.textbbox((0, 0), ln, font=FS)
        d.text(((W - (bb[2] - bb[0])) // 2, int(H * 0.14)), ln, font=FS, fill=(220, 218, 212, int(200 * lp)))

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=203, gain=0.72)
    frame = fx.vignette(frame, 0.4 - 0.14 * aw)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: light-voice + hand-over piano + soft grass steps + wind + owl ----
def grass_step(amp=0.07, dur=0.24):
    """A soft footstep on grass — filtered noise rustle, no hard thud."""
    n = int(dur * SR); t = np.arange(n) / SR
    nse = np.convolve(np.random.randn(n).astype(np.float32), np.ones(22) / 22, mode="same")
    rustle = np.random.randn(n).astype(np.float32) * np.exp(-t * 45) * 0.35
    env = np.exp(-t * 15) * np.clip(t / 0.008, 0, 1)
    return (nse * env + rustle * env) * amp


def wind_bed(dur, amp=0.05, seed=0):
    """Soft, gusting wind (heavily low-passed noise)."""
    n = int(dur * SR)
    r = np.random.default_rng(seed)
    nse = np.convolve(r.standard_normal(n).astype(np.float32), np.ones(500) / 500, mode="same")
    t = np.arange(n) / SR
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.06 * t + 1) * np.sin(2 * np.pi * 0.017 * t)
    return nse * gust * amp


def owl(amp=0.09):
    """A soft, nostalgic owl call: 'hoo ... hoo-hoo'."""
    seg = np.zeros(int(1.6 * SR), np.float32)
    for f0, start in [(300, 0.0), (285, 0.62), (300, 0.92)]:
        n = int(0.4 * SR); t = np.arange(n) / SR
        f = f0 * (1 - 0.05 * t / 0.4)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.sin(ph) * 0.7 + 0.15 * np.sin(2 * ph)
        env = np.sin(np.clip(t / 0.4, 0, 1) * np.pi) ** 1.4
        s = int(start * SR); seg[s:s + n] += y * env
    return seg * amp


def build_audio():
    n = int(DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # ambient: soft gusting wind (stereo) across the whole minute
    add(L, wind_bed(DUR, 0.05, seed=1), 0.0)
    add(R, wind_bed(DUR, 0.05, seed=2), 0.0)
    # a nostalgic owl, a few soft calls in the distance
    st(owl(0.09), 6.0, 0.30); st(owl(0.075), 23.5, 0.72); st(owl(0.08), 47.5, 0.4)

    # the LIGHT'S VOICE: pitch tracks its height, amp tracks its movement + how
    # awake it is; it swells and climbs in pitch as it reignites.
    ct = np.linspace(0, DUR, 6000)
    ox_c = np.array([orb_x(x) for x in ct], np.float32)
    oy_c = np.array([orb_y(x) for x in ct], np.float32)
    h_c = np.array([orb_height_norm(x) for x in ct], np.float32)
    b_c = np.array([orb_bright(x) for x in ct], np.float32)
    at = np.arange(n) / SR
    h_a = np.interp(at, ct, h_c); b_a = np.interp(at, ct, b_c)
    ox_a = np.interp(at, ct, ox_c); oy_a = np.interp(at, ct, oy_c)
    freq = 66.0 * 2 ** (h_a * 2.1)
    speed = np.sqrt(np.gradient(ox_a) ** 2 + np.gradient(oy_a) ** 2) * SR
    spd_n = np.clip(speed / 400.0, 0, 1)
    amp = (0.05 + 0.13 * spd_n) * (0.25 + 0.85 * np.clip(b_a, 0, 1.4) / 1.4)
    ph = np.cumsum(2 * np.pi * freq / SR)
    voice = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph)) * amp
    L += voice * 0.55; R += voice * 0.55

    prog = [([53, 57, 60], 41), ([50, 53, 57], 38), ([48, 52, 55], 43), ([46, 50, 53], 46)] * 3
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        env = 0.05 + 0.06 * smooth(36, 48, k * step)          # bed swells at the awakening
        p = pad([midi(m) for m in notes], step + 0.4, amp=env)
        add(L, p, k * step); add(R, np.roll(p, 350), k * step)
        add(L, bass(midi(br), step + 0.2, amp=0.10), k * step)
        add(R, bass(midi(br), step + 0.2, amp=0.10), k * step)

    # soft grass footsteps: walking toward the child, and away into the dark
    tt = 16.0
    while tt < 25.5: st(grass_step(), tt, 0.46); tt += 0.72
    tt = 51.0
    while tt < 59: st(grass_step(amp=0.06 * (1 - (tt - 51) / 9)), tt, 0.36); tt += 0.72

    # THE HAND-OVER (warm, low): old voice descends & fades (right), the child's
    # voice rises & resolves home (left) — mirror of part 1.
    for m, att, amp_ in [(60, 30.0, 0.20), (57, 32.5, 0.15), (53, 35.0, 0.11)]:
        st(piano(midi(m), 3.4, amp=amp_), att, 0.72)
    for m, att, amp_ in [(53, 33.0, 0.16), (57, 36.0, 0.20), (60, 39.0, 0.24), (65, 42.0, 0.24)]:
        st(piano(midi(m), 3.6, amp=amp_), att, 0.30)
    # awakening: warm low F-major bloom + gentle cascade
    for i, m in enumerate([41, 45, 48, 53, 57, 60]):
        st(piano(midi(m), 4.5, amp=0.13), 40.5 + i * 0.18, 0.2 + i * 0.1)
    for i, m in enumerate([65, 67, 69, 72]):
        st(piano(midi(m), 2.6, amp=0.08), 44.0 + i * 0.4, 0.5 + (i - 2) * 0.08)
    # settle on F — the SAME note part 1 opens on (the loop closes)
    st(piano(midi(53), 5.5, amp=0.18), 55.5, 0.5)
    st(piano(midi(41), 6.0, amp=0.14), 56.0, 0.5)

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.2)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi, fo = int(1.5 * SR), int(3.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("e2e_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2e_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2e.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2e_silent.mp4", "-i", "e2e.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "cycle_part5.mp4"],
                   check=True, capture_output=True)
    print("Done -> cycle_part5.mp4")


if __name__ == "__main__":
    main()
