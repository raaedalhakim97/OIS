"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 7 — "The Other Keeper"  (introduces the world)
On the slow-turning little planet, the Keeper meets another keeper already there. It
does not speak — it sings. Through a call-and-response the other keeper welcomes him and
introduces the world: every soul is a note; we don't fix them, we help them find who
they harmonize with. Then the two walk on together. Slow earth, two keepers, engine
score (piano conversation that literally harmonises). ~2:00.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
import title_card as tc
import world, planet as pl

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 118.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]; WARM = [255, 214, 165]
CENTER_Y = 0.44
CH, EP, TITLE, LAND = "I", "7", "The Other Keeper", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
def gfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(47); FSM = font(34); GF = gfont(50)


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


SCENES = ["night", "dawn", "morning", "golden"]
for s in SCENES: pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "night"), (18, "dawn"), (58, "morning"), (100, "golden")]

MAIN_X = 0.43; OTHER_X0, OTHER_X1 = 0.92, 0.57

# the conversation: (time, who, pitch) — the other keeper calls (high), the Keeper
# answers (low); the intervals are consonant, so the two literally harmonise.
CONVO = [(52, "o", 69), (55, "m", 65), (60, "o", 72), (63, "m", 69),
         (74, "o", 74), (77, "m", 65), (88, "o", 72), (90, "m", 60)]
GLYPHS = [(t, who) for (t, who, p) in CONVO]

CAPS = [
    (2.0, 7.0, "he had walked a long way\nalone."),
    (10.0, 15.0, "then — another light."),
    (26.0, 32.0, "another keeper,\nalready here."),
    (40.0, 46.0, "it did not speak.\nit sang."),
    (58.0, 64.0, "welcome, it seemed to say."),
    (66.0, 73.0, "this is the observer world.\nevery soul here is a note."),
    (78.0, 86.0, "some bright, some low,\nsome still lost in the dark."),
    (92.0, 100.0, "we do not fix them —\nwe help them find\nwho they harmonize with."),
    (103.0, 109.0, "and the two walked on\ntogether."),
    (111.0, 116.0, "the more you know,\nthe more you observe."),
]


def scene_blend(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 3.0:
            return n0, n1, smooth(s1 - 3.0, s1, ts)
    return n0, n0, 0.0


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            f = FSM if txt.startswith("the more you know") else FS
            lines = txt.split("\n")
            total = sum(int(d.textbbox((0, 0), ln, font=f)[3] * 1.5) for ln in lines)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f); xx = (W - (bb[2] - bb[0])) // 2
                d.text((xx + 2, yy + 2), ln, font=f, fill=(0, 0, 0, int(150 * fade)))
                d.text((xx, yy), ln, font=f, fill=(238, 234, 226, int(240 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)


def draw_glyphs(im, ts, mpos, opos):
    d = ImageDraw.Draw(im, "RGBA")
    for (t, who) in GLYPHS:
        age = ts - t
        if 0 <= age <= 1.6:
            al = np.interp(age, [0, 0.3, 1.1, 1.6], [0, 1, 1, 0])
            x, y = (opos if who == "o" else mpos)
            d.text((x, y - 42 - age * 30), "♪", font=GF, fill=(255, 208, 146, int(230 * al)), anchor="mm")


def story(ts):
    n0, n1, f = scene_blend(ts)
    if f <= 0.001:
        a = pl.build_sky(n0).copy(); base, mask = pl.planet_base(n0)
    else:
        a = pl.build_sky(n0) * (1 - f) + pl.build_sky(n1) * f
        b0, mask = pl.planet_base(n0); b1, _ = pl.planet_base(n1); base = b0 * (1 - f) + b1 * f
    a[mask] = base[mask]
    scene = n1 if f > 0.5 else n0

    theta = 0.13 * ts                                     # SLOW earth
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta, scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    # the other keeper rises over the turning horizon, then comes to stand near him
    seen = smooth(9, 13, ts)
    ox = lerp(OTHER_X0, OTHER_X1, smooth(20, 46, ts))
    o_walk = 20 < ts < 46 or ts > 102
    o_face = -1
    ospr, ofy, oodx, oody = character(128, "walk" if o_walk else "stand", ts, o_face,
                                      lean=0.03 * math.sin(ts * 1.0))
    oox = ox * W + oodx; ooy = APEX_Y + oody

    # the Keeper — travels, then turns to face the other, then walks on together
    m_walk = ts < 20 or ts > 102
    m_face = 1
    mx = lerp(0.5, MAIN_X, smooth(16, 26, ts))
    mspr, mfy, modx, mody = character(132, "walk" if m_walk else "stand", ts, m_face,
                                      lean=0.03 * math.sin(ts * 1.1))
    mox = mx * W + modx; moy = APEX_Y + mody

    if seen > 0.02:
        glow(a, oox, ooy, 22, WARM, seen * 0.9 * (0.9 + 0.1 * math.sin(ts * 3 + 1)))
    glow(a, mox, moy, 24, GOLD, 0.95 * (0.9 + 0.1 * math.sin(ts * 3)))
    # a thread of light between them once they harmonise
    bond = smooth(52, 92, ts)
    if bond > 0.02:
        for i in range(14):
            u = i / 13; px = lerp(mox, oox, u); py = lerp(moy, ooy, u) - 0.03 * H * math.sin(math.pi * u)
            glow(a, px, py, 4, GOLD, bond * 0.4 * (0.6 + 0.4 * math.sin(ts * 3 + i)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if seen > 0.02:
        im.paste(ospr, (int(ox * W - ospr.size[0] / 2), int(APEX_Y - ofy)), ospr)
    im.paste(mspr, (int(mx * W - mspr.size[0] / 2), int(APEX_Y - mfy)), mspr)
    draw_glyphs(im, ts, (mox, APEX_Y - 0.16 * H), (oox, APEX_Y - 0.16 * H))
    draw_caption(im, ts)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.40)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


def build_audio():
    n = int(DUR * SR)
    dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
    wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
    def d(s, at, pan=0.5): add(dL, s * (1 - pan), at); add(dR, s * pan, at)
    def w(s, at, pan=0.5): add(wL, s * (1 - pan), at); add(wR, s * pan, at)
    w(pad([midi(53), midi(57), midi(60)], DUR - 6, 0.045), 6, 0.5)
    d(piano(midi(53), 5, 0.13), 8, 0.45)                  # the Keeper, alone
    d(piano(midi(57), 4, 0.10), 14, 0.45)
    for (t, who, p) in CONVO:                             # the conversation (o=right/high, m=left/low)
        pan = 0.66 if who == "o" else 0.36
        d(piano(midi(p), 3.2, 0.15 if who == "o" else 0.14), t, pan)
    # they harmonise: a warm F-major chord blooms as they walk on together
    w(pad([midi(53), midi(57), midi(60), midi(65)], 16, 0.06), 100, 0.5)
    w(bass(midi(41), 16, 0.07), 100, 0.5)
    for i, m in enumerate([53, 57, 60, 65]): d(piano(midi(m), 5, 0.12), 103 + i * 0.6, 0.5)
    for t in np.arange(30, 116, 1.6): d(softkick(0.10), t, 0.5)   # a soft, slow walking pulse
    d(piano(midi(53), 8, 0.15), 116, 0.5)
    dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
    wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
    mix = master(dry * 0.92 + wet)
    fi, fo = int(0.6 * SR), int(4 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep7_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep7_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep7.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep7_silent.mp4", "-i", "ep7.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep7_the_other_keeper.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep7_the_other_keeper.mp4")


if __name__ == "__main__":
    main()
