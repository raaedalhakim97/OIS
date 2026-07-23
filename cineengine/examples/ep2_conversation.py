"""
THE OBSERVER WORLD · CHAPTER I · EPISODE 2 — "The Conversation"
Two notes meet in the Home Fields and speak to each other in their notes (call and
response). A yearning note (E) has been calling a long time; a steady note (C)
hears, and answers. They discover they harmonize — a bright major third — and when
they sing together, the world remembers it was once a song, and the Silence at the
edge loses one step of ground. That is the consequence: every harmony pushes the
dark back, one note at a time.

Standards: opens with the title card; captions CENTERED (eyes don't move); a small
music-note glyph rises above a speaker's head as it sounds its note, then fades;
breathing pace; the Observer's Question; the light sings; ~2 min.
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
SDUR = 116.0                     # story length
DUR = TITLE_DUR + SDUR           # ~122s (about two minutes)
GROUND = 0.80 * H
fx = FX(W, H)
GOLD = [255, 200, 130]
DIM = [140, 165, 220]
CENTER_Y = 0.45                  # captions live in the vertical middle

CH, EP, TITLE, LAND = "I", "2", "The Conversation", "the Home Fields"

# the two who meet
EX = 0.37; EFEET = 0.75; ENOTE = 64          # E — the Yearning (has been calling)
CX0, CX1 = 0.86, 0.57; CFEET = 0.78; CNOTE = 60   # C — the Caller (hears, answers)


def lerp(a, b, x): return a + (b - a) * max(0.0, min(1.0, x))
def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1])
def mix3(c0, c1, x):
    return [c0[i] + (c1[i] - c0[i]) * clamp(x) for i in range(3)]


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
def gfont(sz):     # sans renders the music glyphs cleanly
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FS = font(48); FSM = font(34); GF = gfont(56)


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
DFAR = [(0.08, 0.71), (0.16, 0.73), (0.90, 0.70), (0.96, 0.73), (0.50, 0.67), (0.72, 0.69)]

# CAPTIONS (story-local time). Centered. Breathing (long fades, space between).
CAPS = [
    (2.0, 8.5, "in the home fields,\na note had been calling\na long time."),
    (9.5, 15.5, "is anyone there?"),
    (18.0, 23.5, "…and someone heard."),
    (27.0, 33.0, "i heard you."),
    (41.0, 48.0, "i have been calling\nso long."),
    (50.0, 57.0, "i know.\ni was looking too."),
    (60.0, 68.0, "so they sang —\ntogether."),
    (72.0, 82.0, "and the world remembered\nit was once a song."),
    (85.0, 95.0, "every time two notes agree,\nthe silence loses\none step of ground."),
    (106.0, 112.0, "now there were two.\nand the dark\nwas a little smaller."),
    (112.5, 116.0, "the more you know,\nthe more you observe."),
]
# note-glyphs that rise above a speaker's head as it sounds its note (story-local)
GLYPHS = [
    (10.0, EX, EFEET - 0.17, "♪"),      # E : "is anyone there?"
    (28.0, 0.74, CFEET - 0.17, "♪"),    # C (approaching) : "i heard you."
    (42.0, EX, EFEET - 0.17, "♪"),      # E : "i've been calling"
    (51.0, CX1, CFEET - 0.17, "♪"),     # C : "i was looking too"
    (61.0, 0.47, 0.55, "♫"),            # both : they sing together
    (63.5, 0.47, 0.50, "♫"),
]
# speaking windows (orb pulses brighter so it's clear who is 'talking')
E_SPK = [(9.5, 15.5), (41.0, 48.0), (60.0, 68.0)]
C_SPK = [(27.0, 33.0), (50.0, 57.0), (60.0, 68.0)]


def _spk(win, ts):
    b = 0.0
    for (s, e) in win:
        if s - 0.3 <= ts <= e + 0.3:
            b = max(b, 0.5 + 0.5 * math.sin((ts - s) / (e - s) * math.pi))
    return b


def draw_caption(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (s, e, txt) in CAPS:
        if s <= ts <= e:
            fade = np.interp(ts, [s, s + 0.9, e - 0.9, e], [0, 1, 1, 0])   # breathing
            lines = txt.split("\n")
            hs = [d.textbbox((0, 0), ln, font=FS)[3] for ln in lines]
            total = sum(int(h * 1.55) for h in hs)
            yy = int(CENTER_Y * H - total / 2)
            small = (txt.startswith("the more you know"))
            f = FSM if small else FS
            for ln in lines:
                bb = d.textbbox((0, 0), ln, font=f)
                col = (232, 228, 220, int(236 * fade))
                d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=f, fill=col)
                yy += int((bb[3] - bb[1]) * 1.55)


def draw_glyphs(im, ts):
    d = ImageDraw.Draw(im, "RGBA")
    for (nt, xf, yf, g) in GLYPHS:
        age = ts - nt
        if 0 <= age <= 1.8:
            al = np.interp(age, [0, 0.3, 1.3, 1.8], [0, 1, 1, 0])
            rise = age * 40
            d.text((xf * W, yf * H - rise), g, font=GF,
                   fill=(255, 208, 146, int(235 * al)), anchor="mm")


def story(ts):
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(ts * 2 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.5)[:, None] * np.array([210, 214, 234])

    # the world re-lights as the harmony spreads (the consequence, made visible)
    world = smooth(60, 84, ts)
    for i, (fx_, fy_) in enumerate(DFAR):
        glow(a, fx_ * W, fy_ * H, 7, GOLD, (0.05 + 0.5 * world) * (0.85 + 0.15 * math.sin(ts + i)))
    if world > 0.01:                              # a far horizon warms — the Silence recedes
        yy = int(GROUND - 2)
        band = (np.linspace(0, 1, W) * 0 + 1)
        a[yy - 3:yy + 3, :] += (world * 26) * np.array(GOLD, np.float32)

    # E — the yearning note; dim & pulsing until the harmony, then it blooms
    e_pulse = 0.38 + 0.12 * math.sin(ts * 1.6) + 0.5 * _spk(E_SPK, ts)
    e_b = e_pulse * (1 - smooth(58, 66, ts)) + 1.0 * smooth(58, 66, ts)
    e_lean = 0.05 * math.sin(ts * 0.7) + 0.08 * smooth(40, 46, ts)
    espr, efy, eodx, eody = character(120, "stand", ts, 1, lean=e_lean)
    eox, eoy = EX * W + eodx, EFEET * H + eody
    ecol = mix3(DIM, GOLD, smooth(58, 66, ts))

    # C — the caller; appears far right, walks in, answers
    c_seen = smooth(15, 18.5, ts)
    cx = lerp(CX0, CX1, smooth(24, 40, ts))
    c_walk = 24 < ts < 40
    c_lean = 0.05 * math.sin(ts * 0.7) - 0.08 * smooth(40, 46, ts)
    cpose = "walk" if c_walk else "stand"
    cspr, cfy, codx, cody = character(122, cpose, ts, -1, lean=c_lean)
    cox, coy = cx * W + codx, CFEET * H + cody
    c_b = (0.9 + 0.4 * _spk(C_SPK, ts)) * c_seen

    # the thread that forms when they sing together (the bond)
    bond = smooth(60, 68, ts)
    if bond > 0.01:
        mx, my = (eox + cox) / 2, (eoy + coy) / 2 - 0.05 * H
        pulse = 0.85 + 0.15 * math.sin(ts * 2.2)
        for i in range(20):
            u = i / 19
            px, py = bez((eox, eoy), (mx, my), (cox, coy), u)
            glow(a, px, py, 5, GOLD, bond * 0.5 * pulse * (0.6 + 0.4 * math.sin(ts * 4 + i)))

    glow(a, eox, eoy, 22, ecol, e_b * 0.95)
    if c_seen > 0.02:
        glow(a, cox, coy, 22, GOLD, c_b * 0.95)

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    # paste (depth: C is farther when higher; keep E in front near camera)
    if c_seen > 0.02:
        im.paste(cspr, (int(cx * W - cspr.size[0] / 2), int(CFEET * H - cfy)), cspr)
    im.paste(espr, (int(EX * W - espr.size[0] / 2), int(EFEET * H - efy)), espr)

    draw_glyphs(im, ts)
    draw_caption(im, ts)
    tc.quiz_overlay(im, ts, "what happens when\ntwo notes finally agree?",
                    97.0, 105.0, options=["nothing changes", "a chord is born", "the silence retreats"],
                    y=0.30)

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
    n = int(TITLE_DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    p = pad([midi(41), midi(53), midi(57)], TITLE_DUR, amp=0.05)
    add(L, p, 0.2); add(R, np.roll(p, 400), 0.2)
    g = wind_gust(4.0, 0.03, 3); add(L, g, 0.6); add(R, g, 0.9)
    L = reverb(L); R = reverb(R)
    st = np.tanh(np.stack([L, R], 1) * 1.1)
    st /= (np.max(np.abs(st)) + 1e-6); st *= 0.6
    fi, fo = int(0.5 * SR), int(1.0 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]; st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st.astype(np.float32)


def story_audio():
    n = int(SDUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    def st(sig, at, pan): add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    for at, am, sd, pan in [(1.0, 0.04, 2, 0.4), (30.0, 0.04, 5, 0.6),
                            (70.0, 0.04, 8, 0.45), (100.0, 0.04, 1, 0.55)]:
        st(wind_gust(6.5, am, sd), at, pan)
    st(owl(0.05, 60), 20.0, 0.7); st(owl(0.05, 64), 90.0, 0.3)
    cp = crickets(30.0, 0.006, 3); ce = np.sin(np.linspace(0, np.pi, len(cp))) ** 1.2
    st(cp * ce, 12.0, 0.5)

    # THE CONVERSATION — each spoken line is a note (call and response), panned to
    # whoever is speaking; E on the left, C on the right.
    st(piano(midi(ENOTE), 6.0, amp=0.14), 9.8, 0.36)     # E: "is anyone there?"
    walk_notes(st, [26, 28, 30, 32, 34, 36, 38], [60, 62, 60, 59, 60, 62, 60],
               amp=0.10, base_pan=0.64)                  # C walks in (musical steps)
    st(piano(midi(CNOTE), 6.0, amp=0.14), 27.6, 0.64)    # C: "i heard you."
    st(piano(midi(ENOTE), 5.5, amp=0.13), 42.0, 0.36)    # E: "i've been calling"
    st(piano(midi(CNOTE), 5.5, amp=0.13), 51.0, 0.62)    # C: "i was looking too"

    # THEY SING TOGETHER — the major third (C+E) blooms as a warm chord; the world
    # re-lights (a low F root joins = grounding, belonging).
    st(piano(midi(CNOTE), 6.0, amp=0.13), 60.5, 0.44)
    st(piano(midi(ENOTE), 6.0, amp=0.13), 61.2, 0.56)
    chord = pad([midi(60), midi(64), midi(67)], 16.0, amp=0.07)   # C major (C-E-G) warmth
    add(L, chord, 60.5); add(R, np.roll(chord, 400), 60.5)
    st(bass(midi(48), 8.0, amp=0.09), 61.0, 0.5)          # low C root under the bloom
    # the consequence swelling under the 'world remembered' lines
    swell = pad([midi(53), midi(57), midi(60)], 18.0, amp=0.05)
    add(L, swell, 72.0); add(R, np.roll(swell, 400), 72.0)
    # settle, and they walk on together
    walk_notes(st, [106, 108, 110], [60, 64, 60], amp=0.09, base_pan=0.5)
    st(piano(midi(53), 8.0, amp=0.11), 112.5, 0.5)        # home on F

    L = reverb(L); R = reverb(R)
    mix = np.tanh(np.stack([L, R], 1) * 1.15)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fo = int(4.0 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix.astype(np.float32)


def build_audio():
    return np.concatenate([title_audio(), story_audio()], axis=0)


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", type=float, default=None)
    a = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    if a.preview is not None:
        Image.fromarray(render(a.preview)).save("ep2_prev.png"); print("preview saved"); return
    n = int(DUR * FPS)
    writer = imageio.get_writer("ep2_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n} ({(i+1)/FPS:.0f}s)")
    writer.close()
    write_wav("ep2.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep2_silent.mp4", "-i", "ep2.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "ch1_ep2_the_conversation.mp4"],
                   check=True, capture_output=True)
    print("Done -> ch1_ep2_the_conversation.mp4")


if __name__ == "__main__":
    main()
