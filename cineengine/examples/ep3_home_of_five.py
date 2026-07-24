"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 3 — "The Home of Five"
The song broke into five notes, lost across the worlds. The Keeper travels through
dawn, morning, golden day, dusk and winter, meets a note in each, and brings it home
to its step in the scale (F pentatonic: F G A C D). A staircase of light builds one
note at a time; a beat grows as they gather. The last note (F, the root) is frozen
and afraid and won't be dragged — so he plays the others and makes a home worth
coming to, and it comes on its own. The scale runs whole; the world sings again.

A music-learning series told as story. Motion is calm: a small breathe, a gentle
swing, clean walking — no bounce. ~2 min.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets
import title_card as tc
import world

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 118.0
DUR = TITLE_DUR + SDUR
fx = FX(W, H)
GOLD = [255, 200, 130]
COLD = [150, 172, 224]
CENTER_Y = 0.46
CH, EP, TITLE, LAND = "I", "3", "The Home of Five", "the Home Fields"


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
def gfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(48); FSM = font(34); GF = gfont(50)


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


SCENES = ["night", "dawn", "morning", "golden", "dusk", "winter"]
WORLDS = {s: world.build(s) for s in SCENES}
SEGS = [(0, "night"), (10, "dawn"), (28, "morning"), (46, "golden"),
        (64, "dusk"), (80, "winter"), (100, "night")]


def bg(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 2.0:
            f = smooth(s1 - 2.0, s1, ts)
            return WORLDS[n0] * (1 - f) + WORLDS[n1] * f, (n1 if f > 0.5 else n0)
    return WORLDS[n0].copy() if False else WORLDS[n0], n0


# the scale — five rising steps (F low → D high). F is step 0 (the root, comes last)
STEPS = [(0.30 + i * 0.085, 0.72 - i * 0.045) for i in range(5)]
# notes: name, midi, step index, the scene it's found in, when it seats, found pos
NOTES = [
    dict(nm="F", m=53, step=0, seat=105.0, found=(0.86, 0.60), col=COLD, refuse=True),
    dict(nm="G", m=55, step=1, seat=24.0, found=(0.80, 0.48), col=GOLD),
    dict(nm="A", m=57, step=2, seat=42.0, found=(0.82, 0.40), col=GOLD),
    dict(nm="C", m=60, step=3, seat=60.0, found=(0.80, 0.44), col=GOLD),
    dict(nm="D", m=62, step=4, seat=76.0, found=(0.82, 0.38), col=GOLD),
]

CAPS = [
    (1.5, 6.0, "the song broke into five.\nfive notes, lost in the world."),
    (6.6, 9.6, "he went to bring them home."),
    (12.0, 17.5, "the first was restless —\nalways somewhere else."),
    (30.0, 35.5, "the second was bright,\nand lonely inside it."),
    (48.0, 53.5, "the third would not come\nwithout the one it kept."),
    (66.0, 71.5, "the fourth was a dreamer —\nit only needed company."),
    (82.0, 87.0, "the last one was afraid."),
    (89.5, 95.0, "and you cannot\ncarry a note home."),
    (100.5, 106.0, "so he played the others —\nand made a home worth coming to."),
    (107.0, 111.5, "and the last note\ncame on its own."),
    (115.0, 118.0, "the more you know,\nthe more you observe."),
]


def note_pos(nt, ts):
    fx_, fy_ = nt["found"]; sx, sy = STEPS[nt["step"]]
    seat = nt["seat"]
    if nt.get("refuse"):
        if ts < 100:                                   # frozen far off, shrinks when approached
            return fx_, fy_, 0.35 + 0.1 * math.sin(ts * 1.5)
        p = smooth(100.5, seat, ts)                    # comes on its own at the payoff
        return lerp(fx_, sx, p), lerp(fy_, sy, p), 0.4 + 0.6 * p
    if ts < seat - 3:
        wig = 0.02 * math.sin(ts * 2.2 + nt["m"])
        return fx_ + wig, fy_ + 0.01 * math.sin(ts * 1.7), 0.7
    if ts < seat:
        p = smooth(seat - 3, seat, ts)
        return lerp(fx_, sx, p), lerp(fy_, sy, p), 0.8
    return sx, sy, 1.0


def keeper_x(ts):
    # small excursions from the home staircase toward each note, then back — gentle
    if ts < 10 or ts >= 100: return 0.30
    for k in range(1, len(SEGS) - 1):
        s0 = SEGS[k][0]; s1 = SEGS[k + 1][0]
        if s0 <= ts < s1:
            return 0.30 + 0.24 * max(0.0, math.sin(math.pi * (ts - s0) / (s1 - s0)))
    return 0.30


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.8, e - 0.8, e], [0, 1, 1, 0])
            small = txt.startswith("the more you know")
            f = FSM if small else FS
            lines = txt.split("\n")
            hs = [d.textbbox((0, 0), ln, font=f)[3] for ln in lines]
            total = sum(int(h * 1.5) for h in hs)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f); xx = (W - (bb[2] - bb[0])) // 2
                d.text((xx + 2, yy + 2), ln, font=f, fill=(0, 0, 0, int(150 * fade)))    # shadow
                d.text((xx, yy), ln, font=f, fill=(238, 234, 226, int(240 * fade)))
                yy += int((bb[3] - bb[1]) * 1.5)


def story(ts):
    a, scene = bg(ts)
    a = a.copy()
    world.atmosphere(a, ts, scene)

    # the staircase of light (the scale) — faint markers, lit as notes seat
    for i, (sx, sy) in enumerate(STEPS):
        glow(a, sx * W, sy * H, 5, [90, 96, 130], 0.18)

    # notes (found in their worlds, then seated on their steps; run pulse at payoff)
    for nt in NOTES:
        nx, ny, nb = note_pos(nt, ts)
        # payoff run: seated steps pulse a little phrase up-and-down
        run = 0.0
        if ts >= 101:
            order = [1, 2, 3, 4, 0, 4, 3, 2, 1]           # G A C D F D C A G
            phase = (ts - 106.5) * 3.2
            for oi, stp in enumerate(order):
                if stp == nt["step"]:
                    run = max(run, math.exp(-((phase - oi) ** 2) / 0.5))
        rad = 11 + 5 * run
        glow(a, nx * W, ny * H, rad, nt["col"], nb * (0.85 + 0.15 * math.sin(ts * 3 + nt["m"])) + 0.6 * run)

    # the Keeper — calm: small breathe (character bob), gentle swing, clean walk. No dip.
    def kxf(u): return keeper_x(u)
    kx = kxf(ts)
    vx = (kxf(ts + 0.05) - kxf(ts - 0.05)) / 0.10
    walking = abs(vx) > 0.0035
    lean = clamp(vx * 2.6, -0.10, 0.10)
    trail = clamp(-vx * 1.2, -0.06, 0.06)
    face = 1 if vx >= -1e-4 else -1
    lift = 0.15 + 0.25 * math.sin(ts * 0.5) * 0 + 0.0     # lantern carried, calm
    spr, fy, odx, ody = character(132, "walk" if walking else "stand", ts, face, lean=lean, trail=trail)
    ky = 0.80
    kox = kx * W + odx; koy = ky * H + ody
    glow(a, kox, koy, 24, GOLD, 0.95 * (0.92 + 0.08 * math.sin(ts * 3)))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx * W - spr.size[0] / 2), int(ky * H - fy)), spr)

    draw_caption(im, ts)
    tc.quiz_overlay(im, ts, "how do you bring someone home?", 111.8, 116.0,
                    options=["carry them", "call them", "wait"], y=0.29)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.68)
    frame = fx.vignette(frame, 0.40)
    frame = fx.grain(frame, ts * FPS, amt=0.013)
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


# ---------- audio: a beat that BUILDS as notes come home ----------
def kick(amp=0.4, dur=0.26):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 22) + 46
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8) * amp).astype(np.float32)
def shaker(amp=0.12, dur=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.random.randn(n).astype(np.float32) * np.exp(-t * 40) * amp)


def title_audio():
    n = int(TITLE_DUR * SR); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    p = pad([midi(41), midi(53), midi(57)], TITLE_DUR, amp=0.05)
    add(L, p, 0.2); add(R, np.roll(p, 400), 0.2)
    L = reverb(L); R = reverb(R)
    st = np.tanh(np.stack([L, R], 1) * 1.1); st /= (np.max(np.abs(st)) + 1e-6); st *= 0.6
    fi, fo = int(0.5 * SR), int(1.0 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]; st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st.astype(np.float32)


def story_audio():
    n = int(SDUR * SR); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)
    beat = 0.75                                                  # ~80 bpm pulse
    # heartbeat/pulse builds: layers switch on as each note seats
    layers = [(2.0, "kick"), (24.0, "kick2"), (42.0, "shake"), (60.0, "bass"), (76.0, "kick3")]
    t = 2.0; i = 0
    while t < 98.0:
        st(kick(0.30), t, 0.5)
        if t >= 24: st(kick(0.16), t + beat / 2, 0.42)
        if t >= 42: st(shaker(0.10), t + beat / 2, 0.6); st(shaker(0.08), t + beat, 0.4)
        if t >= 60 and int(t / beat) % 2 == 0: st(bass(midi(41), 0.5, amp=0.08), t, 0.5)
        t += beat
    # each note rings its pitch as it seats (ascending → the ear learns the scale)
    for nt, seat in [(NOTES[1], 24), (NOTES[2], 42), (NOTES[3], 60), (NOTES[4], 76)]:
        st(piano(midi(nt["m"]), 4.0, amp=0.14), seat, 0.5)
        st(pad([midi(nt["m"]), midi(nt["m"] + 7)], 3.0, amp=0.04), seat, 0.5)
    # winter low point — the pulse thins to a lonely heartbeat + cold wind
    st(wind_gust(8.0, 0.05, 4), 82.0, 0.4)
    for hb in np.arange(82, 100, 1.5): st(kick(0.12), hb, 0.5)
    # payoff — the four call, F lands, then the full pentatonic run up & down
    for i2, m in enumerate([55, 57, 60, 62]): st(piano(midi(m), 2.5, amp=0.10), 101.0 + i2 * 0.5, 0.5)
    st(piano(midi(53), 6.0, amp=0.16), 105.5, 0.5)              # F comes home (the root)
    run = [53, 55, 57, 60, 62, 60, 57, 55, 53]
    for i2, m in enumerate(run): st(piano(midi(m), 2.0, amp=0.12), 106.6 + i2 * 0.32, 0.5)
    st(pad([midi(53), midi(57), midi(60)], 10.0, amp=0.06), 106.0, 0.5)
    for hb in np.arange(106, 116, beat): st(kick(0.26), hb, 0.5)   # groove returns
    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.18); mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.88
    fo = int(3.5 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix.astype(np.float32)


def build_audio():
    return np.concatenate([title_audio(), story_audio()], axis=0)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep3f_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep3f_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep3f.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep3f_silent.mp4", "-i", "ep3f.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "ch1_ep3_the_home_of_five.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep3_the_home_of_five.mp4")


if __name__ == "__main__":
    main()
