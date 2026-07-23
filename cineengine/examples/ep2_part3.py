"""
THE CYCLE · part 3 — "The Weight"  (~60s)
The light is too heavy to carry alone. The keeper shares a spark with each unlit
soul around them; each lights up and ANSWERS with a calm piano note, the notes
stacking into a warm F-major chord — and the weight lifts. Connect -> piano
response (the series signature). Black silhouettes.
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
KX = 0.5
fx = FX(W, H)
yy, xx = fx.yy, fx.xx

# each other: (x, feet_y, size, midi note, connect_time)  notes stack to F major
OTHERS = [
    (0.18, 0.80, 74, 65, 15.0),   # F
    (0.82, 0.785, 70, 69, 21.0),  # A
    (0.31, 0.72, 56, 72, 28.0),   # C
    (0.70, 0.71, 54, 77, 35.0),   # F
    (0.13, 0.68, 46, 81, 41.0),   # A
    (0.89, 0.695, 48, 84, 47.0),  # C
]


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


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([8, 10, 26], np.float32) * (1 - t)
            + np.array([20, 20, 44], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(21, 23, 42))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(24, 26, 46))
    d.rectangle([0, int(GROUND), W, H], fill=(18, 19, 36))
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(31)
STARX = _r.integers(0, W, 160); STARY = _r.integers(0, int(GROUND * 0.95), 160)
STARB = _r.uniform(0.3, 1.0, 160); STARPH = _r.uniform(0, 6.28, 160)

# cache the others' silhouettes once (static) so we don't re-render 6/frame
OSPR = [character(sz, "stand", 0.0, 1 if ox < 0.5 else -1, 0.0)
        for (ox, oy, sz, m, ct) in OTHERS]

NARR = [
    (2.0, 7.0, "the light grew heavy."),
    (7.5, 13.0, "too heavy\nfor one."),
    (13.5, 19.0, "but you were not\nthe only one in the dark."),
    (19.5, 25.0, "others waited,\nunlit."),
    (26.0, 31.0, "so you shared it."),
    (31.5, 37.0, "a spark costs nothing —"),
    (37.5, 43.0, "and gives everything."),
    (43.5, 49.0, "and the weight\ngrew lighter."),
    (49.5, 55.0, "a light shared\nis never smaller."),
    (55.0, 60.0, "you were never meant\nto carry it alone."),
]


def render(t):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 2 + STARPH)
    a[STARX * 0 + STARY, STARX] += (STARB * tw * 0.7)[:, None] * np.array([210, 214, 234])

    # keeper (center). light heavy/dim at first, steadies as others light up.
    nconn = sum(1 for (_, _, _, _, ct) in OTHERS if t >= ct)
    lift = 0.66 + 0.05 * math.sin(t * 2.4)
    kspr, kfy, kodx, kody = character(150, "stand", t, 1, lift=lift)
    kx = KX * W
    kox = kx + kodx; koy = GROUND + kody - lift * 0.15 * H
    kbr = 0.4 + 0.09 * nconn                       # brighter with every shared spark
    glow(a, kox, koy, 30 + 3 * nconn, [255, 198, 120], kbr * (0.9 + 0.1 * math.sin(t * 3)))

    # the others: dim silhouettes that LIGHT UP when the spark reaches them
    others_sprites = []
    for idx, (ox, oy, sz, m, ct) in enumerate(OTHERS):
        oxp, oyp = ox * W, oy * H
        lit = smooth(ct, ct + 0.6, t)
        obr = 0.12 + 0.85 * lit
        ospr, ofy, oodx, oody = OSPR[idx]
        ohx = oxp + oodx; ohy = oyp + oody
        glow(a, ohx, ohy, 14 + 12 * lit, [255, 200, 130], obr * (0.85 + 0.15 * math.sin(t * 4 + ox * 9)))
        if lit > 0.3:                              # a little ripple as it wakes
            rp = (t - ct)
            if 0 < rp < 1.0:
                glow(a, ohx, ohy, 40 + 90 * rp, [255, 205, 150], 0.4 * (1 - rp))
        others_sprites.append((ospr, oxp, oyp, ofy))
        # travelling spark from keeper's light to this one just before it lights
        if ct - 0.55 <= t < ct:
            u = (t - (ct - 0.55)) / 0.55
            sx, sy = lerp(kox, ohx, u), lerp(koy, ohy, u)
            glow(a, sx, sy, 12, [255, 225, 170], 0.9)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    for (ospr, oxp, oyp, ofy) in others_sprites:
        im.paste(ospr, (int(oxp - ospr.size[0] / 2), int(oyp - ofy)), ospr)
    im.paste(kspr, (int(kx - kspr.size[0] / 2), int(GROUND - kfy)), kspr)

    d = ImageDraw.Draw(im, "RGBA")
    tfade = smooth(0.4, 1.4, t) * (1 - smooth(11.5, 12.5, t))
    if tfade > 0.01:
        for txt, f, yv in (("THE CYCLE", FT, 0.08), ("part 3 · the weight", FS, 0.125)):
            bb = d.textbbox((0, 0), txt, font=f)
            d.text(((W - (bb[2] - bb[0])) // 2, int(H * yv)), txt, font=f,
                   fill=(232, 230, 224, int(225 * tfade)))
    for (s, e, txt) in NARR:
        if s <= t <= e:
            fade = np.interp(t, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            yv = int(H * 0.85)
            for ln in txt.split("\n"):
                bb = d.textbbox((0, 0), ln, font=FS)
                d.text(((W - (bb[2] - bb[0])) // 2, yv), ln, font=FS, fill=(230, 228, 222, int(220 * fade)))
                yv += int((bb[3] - bb[1]) * 1.6)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=204, gain=0.72)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


# ---- audio: each CONNECTION = keeper call + the other's ringing response ----
def build_audio():
    n = int(DUR * SR)
    Lc = np.zeros(n, np.float32); Rc = np.zeros(n, np.float32)
    def st(sig, at, pan): add(Lc, sig * (1 - pan), at); add(Rc, sig * pan, at)

    prog = [([53, 57, 60], 41), ([48, 52, 55], 48), ([50, 53, 57], 50), ([46, 50, 53], 46)] * 3
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        p = pad([midi(m) for m in notes], step + 0.4, amp=0.07)
        add(Lc, p, k * step); add(Rc, np.roll(p, 350), k * step)
        add(Lc, bass(midi(br), step + 0.2, amp=0.11), k * step)
        add(Rc, bass(midi(br), step + 0.2, amp=0.11), k * step)

    # a light continuous conversation underneath (kept sparse so connections shine)
    PENTA = [65, 67, 69, 72, 74]
    rng = np.random.default_rng(5)
    tt = 5.0
    while tt < 54:
        st(piano(midi(rng.choice(PENTA)), 2.4, amp=0.07), tt, 0.3)
        st(piano(midi(rng.choice(PENTA)), 2.4, amp=0.06), tt + 0.9, 0.7)
        tt += rng.uniform(3.0, 4.5)

    # THE CONNECTIONS — keeper 'call' then the other's ringing 'response' (long,
    # so they STACK into a growing F-major chord as more light up)
    for (ox, oy, sz, m, ct) in OTHERS:
        st(piano(midi(60 + (m - 65) // 2 if m > 65 else 60), 1.8, amp=0.14), ct - 0.5, 0.5)  # call
        st(piano(midi(m), 7.0, amp=0.22), ct, ox)                                            # response, panned to it
        st(piano(midi(m), 4.5, amp=0.09), ct + 0.6, 1 - ox)                                  # echo across
    # final: the whole chord rolls once and settles (all lights singing together)
    for i, m in enumerate([65, 69, 72, 77, 81, 84]):
        st(piano(midi(m), 5.0, amp=0.12), 52.5 + i * 0.22, 0.2 + i * 0.12)
    st(piano(midi(53), 5.0, amp=0.16), 56.5, 0.5)     # low F home

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
        Image.fromarray(render(a.preview)).save("e2c_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("e2c_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("e2c.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "e2c_silent.mp4", "-i", "e2c.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "cycle_part3.mp4"],
                   check=True, capture_output=True)
    print("Done -> cycle_part3.mp4")


if __name__ == "__main__":
    main()
