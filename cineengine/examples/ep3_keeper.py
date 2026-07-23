"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 3 — "The Keeper"   (the adventure begins)
Introduces the main character and launches the journey. The Keeper — one note who
lost his chord to the Silence — sits alone holding the last light. Far off, scattered
notes still call in the dark. He understands he cannot mend his own chord (a note
cannot complete itself), but he can help the others find theirs, and piece by piece
bring the song back. He lifts his light, the world's horizon opens, and he takes the
first step. Hooks into Ep. 4 "The Fading". ~2:15 vertical.

Standards: title card, centered captions, note-glyphs, breathing pace, the Observer's
Question, the weighted swing.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from character import character
from make_music import SR, midi, piano, pad, bass, reverb, add, write_wav
from ep3_part1 import wind_gust, owl, crickets, step_note, walk_notes
import title_card as tc

W, H = 1080, 1920
FPS = 24
TITLE_DUR = 6.0
SDUR = 139.0
DUR = TITLE_DUR + SDUR
GROUND = 0.80 * H
fx = FX(W, H)
GOLD = [255, 200, 130]
COLD = [150, 172, 224]
CENTER_Y = 0.45
CH, EP, TITLE, LAND = "I", "3", "The Keeper", "the Home Fields"


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
def gfont(sz):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
FS = font(48); FSM = font(34); GF = gfont(54)


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


def darken(a, cx, cy, rad, strength):
    """The Silence: a void that eats light and world in a soft region."""
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    m = np.exp(-d2 / (2 * rad ** 2)) * strength
    a[y0:y1, x0:x1] *= (1 - m)[..., None]


def build_bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([6, 8, 22], np.float32) * (1 - t)
            + np.array([16, 17, 38], np.float32) * t)[:, None, :].repeat(W, 1)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([-0.3 * W, GROUND - 0.05 * H, 0.6 * W, GROUND + 0.3 * H], fill=(17, 19, 36))
    d.ellipse([0.5 * W, GROUND - 0.04 * H, 1.3 * W, GROUND + 0.3 * H], fill=(20, 22, 40))
    d.rectangle([0, int(GROUND), W, H], fill=(13, 14, 28))
    rr = np.random.default_rng(7)
    for _ in range(130):
        gx = rr.integers(0, W); gh = rr.integers(14, 46); sway = rr.uniform(-8, 8)
        d.line([(gx, H), (gx + sway, H - gh)], fill=(9, 12, 20), width=2)
    return np.asarray(im, np.float32)
BG = build_bg()
_r = np.random.default_rng(11)
STARX = _r.integers(0, W, 150); STARY = _r.integers(0, int(GROUND * 0.9), 150)
STARB = _r.uniform(0.3, 1.0, 150); STARPH = _r.uniform(0, 6.28, 150)

# the Great Chord memory — lights that cluster, then the Silence scatters them
_m = np.random.default_rng(4)
MEM_CL = [(0.5 + _m.uniform(-0.10, 0.10), 0.40 + _m.uniform(-0.06, 0.06)) for _ in range(7)]
MEM_SC = [(_m.uniform(0.05, 0.95), _m.uniform(0.15, 0.60)) for _ in range(7)]
MEM_M = [53, 57, 60, 64, 67, 55, 62]

# distant scattered notes that still call in the dark (x, y, blink-on time)
FARCALL = [(0.20, 0.60, 55.0), (0.82, 0.58, 59.0), (0.35, 0.55, 64.0),
           (0.68, 0.62, 69.0), (0.50, 0.52, 73.0)]

# the horizon of the world ahead (faint territory silhouettes revealed at departure)
TERR = [(0.16, 0.66, 0.16), (0.42, 0.63, 0.20), (0.72, 0.66, 0.18), (0.92, 0.64, 0.14)]

CAPS = [
    (2.0, 8.5, "before the world went quiet,\nit was a song."),
    (9.5, 16.5, "he was one note in it —\none voice in a great chord."),
    (19.0, 26.0, "then the silence came,\nand the song came apart."),
    (28.0, 37.5, "his chord was scattered.\nhe was left holding\nthe last light."),
    (41.0, 50.0, "for a long time,\nhe did not move."),
    (55.0, 63.0, "then — far away —\na note. then another."),
    (65.0, 77.0, "the song was not gone.\nonly scattered —\nwaiting to be answered."),
    (81.0, 90.0, "he could not mend his own chord —\na note cannot complete itself."),
    (92.0, 99.0, "but he could help the others\nfind theirs."),
    (100.0, 106.0, "and piece by piece,\nbring the song back."),
    (109.0, 116.0, "so he lifted his light —\nand took the first step."),
    (117.5, 124.0, "somewhere ahead,\na light was going out.\nhe walked toward it."),
    (132.0, 138.0, "the more you know,\nthe more you observe."),
]
GLYPHS = [(t + 0.4, x, y - 0.02, "♪") for (x, y, t) in FARCALL]


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.9, e - 0.9, e], [0, 1, 1, 0])
            small = txt.startswith("the more you know")
            f = FSM if small else FS
            lines = txt.split("\n")
            hs = [d.textbbox((0, 0), ln, font=f)[3] for ln in lines]
            total = sum(int(h * 1.55) for h in hs)
            yy = int(CENTER_Y * H - total / 2)
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f)
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f,
                       fill=(232, 228, 220, int(236 * fade)))
                yy += int((bb[3] - bb[1]) * 1.55)


def draw_glyphs(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (nt, xf, yf, g) in GLYPHS:
        age = ts - nt
        if 0 <= age <= 1.8:
            al = np.interp(age, [0, 0.3, 1.3, 1.8], [0, 1, 1, 0])
            d.text((xf * W, yf * H - age * 34), g, font=GF,
                   fill=(255, 208, 146, int(230 * al)), anchor="mm")


def story(ts):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(ts * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([210, 214, 234])

    # ---- Beat 2: the memory of the Great Chord, and the Silence scattering it ----
    mem = smooth(18.5, 20.5, ts) * (1 - smooth(37, 39.5, ts))
    if mem > 0.01:
        scat = smooth(27.5, 36.0, ts)
        for i in range(7):
            cx = lerp(MEM_CL[i][0], MEM_SC[i][0], scat)
            cy = lerp(MEM_CL[i][1], MEM_SC[i][1], scat)
            b = mem * (1 - 0.9 * scat) * (0.85 + 0.15 * math.sin(ts * 3 + i))
            glow(a, cx * W, cy * H, 16 - 6 * scat, GOLD, b)
        # the Silence sweeps across, eating the lights
        sil = smooth(27.0, 36.0, ts)
        if sil > 0.01:
            sx = lerp(1.25, 0.30, sil)
            darken(a, sx * W, 0.40 * H, 0.55 * W, 0.9 * sil)

    # ---- Beat 4: distant scattered notes still calling in the dark ----
    for (fx_, fy_, t0) in FARCALL:
        on = smooth(t0, t0 + 0.6, ts)
        tw2 = 0.6 + 0.4 * math.sin(ts * 2.5 + fx_ * 9)
        glow(a, fx_ * W, fy_ * H, 8, GOLD, (0.10 + 0.45 * on) * tw2 * (1 - 0.4 * smooth(116, 122, ts)))

    # ---- Beat 6: the horizon of the world opens (territories ahead) ----
    horizon = smooth(104, 116, ts)
    if horizon > 0.01:
        im0 = Image.fromarray(a.clip(0, 255).astype(np.uint8)); dd = ImageDraw.Draw(im0, "RGBA")
        for (tx, ty, tw3) in TERR:
            col = (28, 30, 52, int(150 * horizon))
            dd.ellipse([(tx - tw3) * W, ty * H, (tx + tw3) * W, (ty + 0.5) * H], fill=col)
        a = np.asarray(im0, np.float32)
        for (tx, ty, tw3) in TERR:
            glow(a, tx * W, ty * H, 7, GOLD, 0.25 * horizon * (0.8 + 0.2 * math.sin(ts + tx * 7)))

    # ---- the Keeper ----
    lift = smooth(100, 108, ts) * (1 - smooth(110, 115, ts))     # raises the light, then lowers to carry
    walk = smooth(113, 133, ts)
    kx = lerp(0.5, 0.80, walk)
    moving = ts > 113
    pose = "walk" if moving else "stand"
    lean = 0.05 * math.sin(ts * 0.6) + 0.06 * smooth(114, 126, ts)
    spr, fy, odx, ody = character(132, pose, ts, 1, lift=lift, lean=lean)
    kox = kx * W + odx; koy = GROUND + ody
    # the lantern, with the Great Chord shimmering faintly inside it
    lb = 0.9 * (0.92 + 0.08 * math.sin(ts * 3)) + 0.25 * smooth(80, 100, ts) + 0.3 * lift
    glow(a, kox, koy, 24 + 8 * lift, GOLD, lb)
    if ts < 108:                                    # tiny inner glimmers = the remembered chord
        for k in range(4):
            ang = ts * 0.8 + k * 1.57
            glow(a, kox + 9 * math.cos(ang), koy + 9 * math.sin(ang), 3, [255, 235, 200],
                 0.5 * (0.85 + 0.15 * math.sin(ts * 4 + k)))

    # ---- Beat 7: the fading light ahead + the Silence looming (hook to Ep.4) ----
    if ts > 115:
        hk = smooth(116, 120, ts)
        darken(a, 1.02 * W, 0.5 * H, 0.42 * W, 0.5 * hk)         # the Silence at the edge
        flick = 0.4 + 0.3 * (0.5 + 0.5 * math.sin(ts * 7))
        glow(a, 0.9 * W, 0.66 * H, 9, COLD, hk * flick)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im.paste(spr, (int(kx * W - spr.size[0] / 2), int(GROUND - fy)), spr)

    draw_glyphs(im, ts)
    draw_caption(im, ts)
    tc.quiz_overlay(im, ts, "what begins an adventure?", 125.0, 131.0,
                    options=["a map", "a reason to walk", "a cry in the dark"], y=0.30)

    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=8, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.42)
    frame = fx.grain(frame, ts * FPS, amt=0.014)
    return frame.clip(0, 255).astype(np.uint8)


def render(t):
    if t < TITLE_DUR:
        return tc.title_frame(t, CH, EP, TITLE, LAND, dur=TITLE_DUR)
    return story(t - TITLE_DUR)


def title_audio():
    n = int(TITLE_DUR * SR); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    p = pad([midi(41), midi(53), midi(57)], TITLE_DUR, amp=0.05)
    add(L, p, 0.2); add(R, np.roll(p, 400), 0.2)
    g = wind_gust(4.0, 0.03, 3); add(L, g, 0.6); add(R, g, 0.9)
    L = reverb(L); R = reverb(R)
    st = np.tanh(np.stack([L, R], 1) * 1.1); st /= (np.max(np.abs(st)) + 1e-6); st *= 0.6
    fi, fo = int(0.5 * SR), int(1.0 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]; st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st.astype(np.float32)


def story_audio():
    n = int(SDUR * SR); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    for at, am, sd, pan in [(1.0, 0.035, 2, 0.4), (44.0, 0.035, 5, 0.55), (108.0, 0.04, 8, 0.5)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.045, 53), 48.0, 0.7); st(owl(0.045, 60), 96.0, 0.35)
    cp = crickets(20.0, 0.005, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 60.0, 0.5)

    # Beat 1 — the Great Chord, heard faint inside the lantern (Fmaj9)
    gc = pad([midi(53), midi(57), midi(60), midi(64), midi(67)], 15.0, amp=0.05)
    add(L, gc, 2.0); add(R, np.roll(gc, 500), 2.0)
    # Beat 2 — the chord returns, then FRACTURES into dissonance, then silence
    gc2 = pad([midi(53), midi(57), midi(60), midi(64)], 8.0, amp=0.06)
    add(L, gc2, 19.0); add(R, np.roll(gc2, 500), 19.0)
    diss = pad([midi(53), midi(54), midi(59), midi(60)], 5.0, amp=0.06)   # clustered = coming apart
    add(L, diss, 28.0); add(R, np.roll(diss, 300), 28.5)
    # Beat 3 — one lonely note, alone in the quiet
    st(piano(midi(53), 8.0, amp=0.12), 42.0, 0.5)
    # Beat 4 — distant scattered notes calling (panned to their far positions)
    for (fx_, fy_, t0), m in zip(FARCALL, [60, 55, 64, 57, 62]):
        st(piano(midi(m), 5.0, amp=0.10), t0 + 0.3, fx_)
    stir = pad([midi(53), midi(57), midi(60)], 8.0, amp=0.04)             # the lantern stirs
    add(L, stir, 66.0); add(R, np.roll(stir, 400), 66.0)
    # Beat 5 — the mission: a warm resolve blooms
    res = pad([midi(53), midi(57), midi(60), midi(65)], 16.0, amp=0.06)
    add(L, res, 80.0); add(R, np.roll(res, 400), 80.0)
    # Beat 6 — the lantern rings a hopeful phrase; the first steps
    for i, m in enumerate([53, 57, 60, 65]):
        st(piano(midi(m), 5.0, amp=0.12), 106.0 + i * 1.1, 0.5)
    walk_notes(st, [114, 116, 118, 120, 122, 124], [53, 55, 57, 55, 53, 57], amp=0.10, base_pan=0.55)
    # Beat 7 — the far fading light: a lone wavering note (hook to Ep.4)
    st(piano(midi(62) * 0.996, 5.0, amp=0.09), 118.0, 0.82)
    st(piano(midi(53), 8.0, amp=0.11), 129.5, 0.5)                        # settle

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15); mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fo = int(4.0 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix.astype(np.float32)


def build_audio():
    return np.concatenate([title_audio(), story_audio()], axis=0)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep3k_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep3k_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "20", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep3k.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep3k_silent.mp4", "-i", "ep3k.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "ch1_ep3_the_keeper.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep3_the_keeper.mp4")


if __name__ == "__main__":
    main()
