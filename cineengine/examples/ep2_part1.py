"""
THE CYCLE · part 1 — "The Gift"  (~60s, fuller narration, interactive piano)
The old keeper sets the light down and walks on; the small one, afraid, finally
lifts it — and it remembers how to shine. Event-synced call-and-response piano
runs throughout (set-down, footsteps, the reach, the awakening). F major.
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
DUR = 60.0
GROUND = 0.80 * H
fx = FX(W, H)
LIGHTX = 0.5


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
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(20, 22, 40))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(23, 25, 44))
    d.rectangle([0, int(GROUND), W, H], fill=(17, 18, 34))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(15)
SX = _r.integers(0, W, 190); SY = _r.integers(0, int(GROUND * 0.98), 190)
SB = _r.uniform(0.3, 1.0, 190); SPH = _r.uniform(0, 6.28, 190)

# ---- fuller narration ----
NARR = [
    (1.5, 7.0, "in the beginning,\nthere was only dark."),
    (7.5, 13.0, "someone, before you,\ncarried a light."),
    (14.0, 20.0, "when they grew tired,\nthey did not put it out."),
    (20.5, 26.0, "they set it down —\nand walked on."),
    (26.5, 32.0, "they left it.\nfor you."),
    (33.0, 39.0, "you were afraid\nto touch it."),
    (39.5, 45.0, "but the dark was colder\nthan the fear."),
    (45.5, 51.0, "so you reached —\nand lifted it."),
    (51.5, 56.0, "and it remembered\nhow to shine."),
    (56.0, 60.0, "the light is never yours.\nonly yours to carry."),
]


def render(t):
    a = BG.copy()
    awake = smooth(45.0, 51.0, t)
    tw = 0.5 + 0.5 * np.sin(t * 2 + SPH)
    a[SY, SX] += (SB * tw * (0.18 + 0.82 * awake))[:, None] * np.array([215, 218, 236])

    # OLD keeper: holds the light, sets it down (14-16), walks away & fades (16-24)
    setdown = smooth(14.0, 16.0, t)
    oldx = lerp(LIGHTX, 0.92, smooth(16.0, 24.0, t)) * W
    oldalpha = 1 - smooth(17.5, 24.0, t)
    old_lift = (1 - setdown) * 0.15          # was holding it a bit up, lowers on set-down
    ospr, ofy, oodx, oody = character(150, "walk" if t > 16 else "stand", t, 1, lift=old_lift)
    old_hand = (LIGHTX * W + oodx, GROUND + oody - old_lift * 0.15 * H) if t < 16 else None

    # CHILD: fades in, approaches, reaches, lifts
    appear = smooth(17.0, 21.0, t)
    childx = lerp(0.34, 0.45, smooth(30.0, 40.0, t)) * W
    lift = smooth(45.0, 50.0, t) * (1 - smooth(57.0, 60.0, t))
    cspr, cfy, codx, cody = character(105, "stand", t, 1, lift=lift)
    child_hand = (childx + codx, GROUND + cody - lift * 0.15 * H)

    # THE LIGHT: old hand -> ground -> child hand -> lifted
    ground_pos = (LIGHTX * W, GROUND - 16)
    if t < 14 and old_hand:
        ox, oy = old_hand
    elif t < 16 and old_hand:
        ox, oy = lerp(old_hand[0], ground_pos[0], setdown), lerp(old_hand[1], ground_pos[1], setdown)
    else:
        pick = smooth(40.0, 43.0, t)
        ox = lerp(ground_pos[0], child_hand[0], pick)
        oy = lerp(ground_pos[1], child_hand[1], pick)
    if t < 16:
        obr = 0.55
    elif t < 43:
        obr = 0.28                            # dim, waiting on the ground
    else:
        obr = 0.5 + 0.9 * awake
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    glow(a, ox, oy, 26 + 22 * lift + 14 * awake, [255, 198, 120], obr * pulse)
    if awake > 0.02:
        glow(a, ox, oy, 130 * awake + 20, [255, 200, 140], 0.35 * awake)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if oldalpha > 0.02:
        o = ospr.copy(); o.putalpha(ospr.split()[3].point(lambda p: int(p * oldalpha)))
        im.paste(o, (int(oldx - o.size[0] / 2), int(GROUND - ofy)), o)
    if appear > 0.02:
        c = cspr.copy(); c.putalpha(cspr.split()[3].point(lambda p: int(p * appear)))
        im.paste(c, (int(childx - c.size[0] / 2), int(GROUND - cfy)), c)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.4, 1.4, t) * (1 - smooth(11.5, 12.5, t))
    if tfade > 0.01:
        for txt, f, yy in (("THE CYCLE", FT, 0.08), ("part 1 · the gift", FS, 0.125)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yy)), txt, font=f,
                   fill=(232, 230, 224, int(225 * tfade)))
    for (s, e, txt) in NARR:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            yy = int(H * 0.80)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=FS)
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FS, fill=(228, 226, 220, int(220 * fade)))
                yy += int((bb[3] - bb[1]) * 1.6)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=203, gain=0.72)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- interactive call-&-response piano (runs throughout), sparse & dreamy ----
def footstep(amp=0.13, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 66 * t) * np.exp(-t * 34)
             + np.random.randn(n).astype(np.float32) * np.exp(-t * 70) * 0.5) * amp)


def build_audio():
    n = int(DUR * SR)
    Lc = np.zeros(n, np.float32); Rc = np.zeros(n, np.float32)
    def st(sig, at, pan): add(Lc, sig * (1 - pan), at); add(Rc, sig * pan, at)
    def note(m, at, pan, amp=0.24, dur=3.0, echo=True):
        st(piano(midi(m), dur, amp=amp), at, pan)
        if echo:                                   # whispered answer on the other side
            st(piano(midi(m), dur * 0.8, amp=amp * 0.42), at + 0.5, 1 - pan)
            st(piano(midi(m + 12 if m < 74 else m), dur * 0.6, amp=amp * 0.22), at + 1.0, pan)

    # soft pad + bass bed across the whole minute
    prog = [([53, 57, 60], 41), ([48, 52, 55], 48), ([50, 53, 57], 50), ([46, 50, 53], 46)]
    prog = prog * 3
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        p = pad([midi(m) for m in notes], step + 0.4, amp=0.07)
        add(Lc, p, k * step); add(Rc, np.roll(p, 350), k * step)
        add(Lc, bass(midi(br), step + 0.2, amp=0.11), k * step)
        add(Rc, bass(midi(br), step + 0.2, amp=0.11), k * step)

    # ---- a CONTINUOUS call-and-response conversation across the minute ----
    # F-major pentatonic (always consonant, even when busy). Density ramps up
    # toward the awakening, then eases as it resolves.
    PENTA = [60, 62, 65, 67, 69, 72, 74, 77]      # C D F G A C D F
    rng = np.random.default_rng(7)
    tt = 5.0
    while tt < 55.5:
        dens = 0.35 + 0.65 * smooth(26.0, 49.0, tt) * (1 - 0.5 * smooth(52.0, 56.0, tt))
        base = rng.integers(2, 5)                 # index into PENTA
        # CALL (left): a little rising figure
        call = [PENTA[base], PENTA[min(base + 1, 7)], PENTA[min(base + 2, 7)]]
        for j, m in enumerate(call[:2 + (dens > 0.6)]):
            note(m, tt + j * 0.42, 0.28, amp=0.15 * dens, dur=2.6)
        # RESPONSE (right): the call answered, gently inverted / a step above
        resp = [PENTA[min(base + 2, 7)], PENTA[min(base + 1, 7)], PENTA[base]]
        for j, m in enumerate(resp[:2 + (dens > 0.6)]):
            note(m, tt + 1.1 + j * 0.42, 0.72, amp=0.14 * dens, dur=2.6, echo=False)
        tt += rng.uniform(2.4, 3.4) * (1.25 - 0.45 * dens)   # closer when busier

    # ---- phase accents on top of the conversation ----
    note(60, 15.2, 0.5, 0.18, echo=False)                    # the set-down
    for i in range(6):
        st(footstep(amp=0.12 * (1 - i / 8)), 16.5 + i * 0.7, 0.62 + i * 0.03)
    # AWAKENING hand-over (the fullest exchange)
    for m, at, p, amp in [(72, 45.0, 0.72, 0.22), (69, 47.0, 0.72, 0.17), (65, 49.0, 0.72, 0.13)]:
        note(m, at, p, amp)                                  # old voice fading (right)
    for m, at, p, amp in [(65, 45.8, 0.28, 0.20), (69, 47.8, 0.28, 0.24), (72, 49.8, 0.28, 0.28)]:
        note(m, at, p, amp)                                  # child rising (left)
    for i, m in enumerate([77, 81, 84, 86, 89]):             # stars answer, cascade
        st(piano(midi(m), 2.0, amp=0.09), 50.2 + i * 0.35, 0.5 + (i - 2) * 0.09)
    # resolve home to F
    for m in [65, 69, 72]:
        st(piano(midi(m), 3.4, amp=0.14), 54.2, 0.5)
    st(piano(midi(65), 4.2, amp=0.22), 57.8, 0.5)

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
        Image.fromarray(render(a.preview)).save("e2p_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2p_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2p.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2p_silent.mp4", "-i", "e2p.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "cycle_part1.mp4"],
                   check=True, capture_output=True)
    print("Done -> cycle_part1.mp4")


if __name__ == "__main__":
    main()
