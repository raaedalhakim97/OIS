"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 6 — "The Heartbeat"  (little-planet, my score)
The five notes are home (from Ep5), but the world is still silent — a note with no
time is only a sound. The Keeper travels the turning world searching for its heartbeat,
finds it still beating in the winter, and brings it home. The notes begin to ring IN
TIME with the pulse — the silent world becomes a song. Teaches rhythm/pulse. Scored by
the engine (felt piano + soft kick = the heartbeat). ~2:04.
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
GOLD = [255, 200, 130]; COLD = [150, 172, 224]; HEART = [255, 150, 110]
CENTER_Y = 0.46
CH, EP, TITLE, LAND = "I", "6", "The Heartbeat", "the Home Fields"
APEX_Y = pl.APEX_Y; CX = pl.CX
BEAT = 0.8333                       # ~72 bpm
BEAT0 = 6.0 + 24.0                  # the pulse starts (abs) when he first hears it


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def lerp(a, b, x): return a + (b - a) * clamp(x)
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(48); FSM = font(34)


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
for s in SCENES: pl.build_sky(s); pl.planet_base(s)
SEGS = [(0, "night"), (10, "dawn"), (26, "morning"), (42, "golden"),
        (58, "dusk"), (72, "winter"), (100, "dawn")]

SLOTS = [(0.30, 0.40), (0.40, 0.365), (0.50, 0.35), (0.60, 0.365), (0.70, 0.40)]
# the five home notes (from Ep5), sitting in the arch; (pitch, slot)
ARCH = [(53, 2), (55, 0), (57, 1), (60, 3), (62, 4)]

CAPS = [
    (1.5, 6.5, "the notes were home.\nbut the world was still silent."),
    (8.0, 13.5, "a note with no time\nis only a sound."),
    (15.0, 20.0, "the song needed a heartbeat."),
    (24.0, 30.0, "so he went to find\nthe beat of the world."),
    (46.0, 52.0, "he followed it\nthrough the turning days."),
    (74.0, 80.0, "and deep in the winter,\nhe found it —"),
    (81.5, 86.0, "still beating."),
    (92.0, 98.0, "he brought it home."),
    (100.0, 106.0, "and the notes began to sing —\nin time."),
    (108.0, 113.0, "the silent world\nbecame a song."),
    (114.0, 118.0, "the more you know,\nthe more you observe."),
]


def beat_pulse(t, start=BEAT0):
    if t < start: return 0.0
    ph = ((t - start) % BEAT) / BEAT
    return math.exp(-((ph) / 0.14) ** 2) + 0.4 * math.exp(-((ph - 1) / 0.14) ** 2)


def scene_blend(ts):
    i = 0
    for k in range(len(SEGS)):
        if SEGS[k][0] <= ts: i = k
    s0, n0 = SEGS[i]
    if i + 1 < len(SEGS):
        s1, n1 = SEGS[i + 1]
        if ts > s1 - 2.5:
            return n0, n1, smooth(s1 - 2.5, s1, ts)
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


def story(ts):
    at = ts + TITLE_DUR                                   # absolute time (for the beat grid)
    n0, n1, f = scene_blend(ts)
    if f <= 0.001:
        a = pl.build_sky(n0).copy(); base, mask = pl.planet_base(n0)
    else:
        a = pl.build_sky(n0) * (1 - f) + pl.build_sky(n1) * f
        b0, mask = pl.planet_base(n0); b1, _ = pl.planet_base(n1); base = b0 * (1 - f) + b1 * f
    a[mask] = base[mask]
    scene = n1 if f > 0.5 else n0

    theta = 0.33 * ts
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    pl.draw_surface(im, theta, scene)
    a = np.asarray(im, np.float32).copy()
    world.atmosphere(a, ts, scene)

    bp = beat_pulse(at)
    # the distant heartbeat he's chasing: a warm pulse growing over the search,
    # arriving at the apex in the winter, then 'taken' into his lantern
    search = smooth(28, 82, ts)
    if 24 < ts < 90:
        hx = lerp(0.86, 0.5, search); hy = lerp(0.70, 0.60, search)
        hb = (0.2 + 0.7 * search) * (1 - smooth(86, 90, ts))
        glow(a, hx * W, hy * H, 16 + 26 * search + 10 * bp, HEART, hb * (0.5 + 0.7 * bp))

    # the five home notes in the arch — dim & silent, then ring IN TIME once the song starts
    song = smooth(98, 104, ts)
    for i, (m, sl) in enumerate(ARCH):
        sx, sy = SLOTS[sl]
        base_b = 0.25 + 0.15 * math.sin(ts * 1.5 + m)     # dim, waiting
        # during the song each note flashes on its beat (a little melody around the arch)
        ring = 0.0
        if at >= 100:
            beat_i = int((at - BEAT0) / BEAT)
            order = [2, 0, 3, 1, 4, 3, 1, 2]              # which slot rings this beat
            if order[beat_i % len(order)] == sl:
                ring = beat_pulse(at)
        b = base_b + song * (0.5 + 0.9 * ring)
        glow(a, sx * W, sy * H, 11 + 7 * ring, GOLD, b)

    # the Keeper on top; his lantern beats once he carries the heart home
    walking = not (78 <= ts <= 92)
    lean = 0.035 * math.sin(ts * 1.1)
    spr, fy, odx, ody = character(132, "walk" if walking else "stand", ts, 1, lean=lean)
    kox = CX + odx; koy = APEX_Y + ody
    lantern = 0.9 + 0.08 * math.sin(ts * 3) + 0.5 * bp * smooth(86, 92, ts)
    glow(a, kox, koy, 24 + 8 * bp * smooth(86, 92, ts), GOLD, lantern)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(CX - spr.size[0] / 2), int(APEX_Y - fy)), spr)
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
    # pad bed (warms through the piece)
    for t0, ch in [(6, [53, 57, 60]), (100, [53, 57, 60, 65])]:
        w(pad([midi(m) for m in ch], (DUR - t0), 0.045), t0, 0.5)
    # intro — the silent home notes hanging, no beat
    for at2, m in [(8, 53), (13, 57), (18, 60)]:
        d(piano(midi(m), 4, 0.12), at2, 0.5)
    # the heartbeat: soft kick from BEAT0, quiet & distant, growing as he nears it
    t = BEAT0
    while t < DUR - 4:
        prog = smooth(BEAT0, BEAT0 + 56, t)               # distant -> full
        amp = 0.10 + 0.16 * prog
        if 84 <= t <= 92: amp *= smooth(84, 92, t)        # swells as he 'takes' it
        d(softkick(amp), t, 0.5)
        t += BEAT
    w(bass(midi(41), 30, 0.07), 90, 0.5)                  # low root joins for the song
    # THE SONG — the five notes ring in time (a pentatonic melody locked to the grid)
    order = [53, 55, 60, 57, 62, 60, 55, 53]              # F G C A D C G F
    i = 0; t = 100.0
    while t < 116:
        m = order[i % len(order)]
        d(piano(midi(m), 2.4, 0.15), t, 0.4 + 0.2 * (i % 2))
        if t > 106: d(piano(midi(m + 12), 1.8, 0.08), t + BEAT / 2, 0.6)  # octave sparkle
        i += 1; t += BEAT
    d(piano(midi(53), 8, 0.16), 116, 0.5)                 # resolve home on F
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
        Image.fromarray(render(a.preview)).save("ep6_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep6_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep6.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep6_silent.mp4", "-i", "ep6.wav", "-c:v", "libx264", "-crf", "27",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "ch1_ep6_the_heartbeat.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep6_the_heartbeat.mp4")


if __name__ == "__main__":
    main()
