"""
Call-&-response piano demo (F major). Two voices trade phrases, echo and answer
each other, weave into counterpoint, then resolve. Two lights flare with each
voice so you can SEE the conversation. Preview of Episode 2's signature sound.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cineengine.generator import FX
from make_music import SR, midi, piano, pad, bass, reverb, add, write_wav

W, H = 1080, 1920
FPS = 24
DUR = 20.0
fx = FX(W, H)
LX, RX, CY = 0.30, 0.70, 0.46

# ---- the score: (time, midi, pan)   pan: 0.2=left voice, 0.8=right voice ----
L, R, C = 0.22, 0.78, 0.5
EV = []
def phrase(notes, t0, dt, pan):
    for i, m in enumerate(notes):
        EV.append((t0 + i * dt, m, pan))

# phase 1 — clear call (left), then answer (right)
phrase([72, 69, 65], 0.6, 0.5, L)          # C A F  (call, descending)
phrase([65, 69, 72], 2.3, 0.5, R)          # F A C  (answer, ascending)
phrase([74, 72, 69], 4.0, 0.5, L)          # D C A
phrase([69, 72, 77], 5.6, 0.5, R)          # A C F  (answer up)
# phase 2 — quick trading, climbing
for i, (m, p) in enumerate([(65, L), (69, R), (72, L), (77, R), (72, L), (69, R)]):
    EV.append((7.4 + i * 0.42, m, p))
# phase 3 — counterpoint: both voices overlap and weave
phrase([65, 69, 72, 77], 10.2, 0.5, L)     # left rising
phrase([72, 69, 65, 60], 10.45, 0.5, R)    # right falling (answers, offset)
EV += [(12.6, 81, R), (13.1, 84, L)]       # high sparkles trading
# phase 4 — resolve together, settle on F (home)
for m in [65, 69, 72]:
    EV.append((15.0, m, C))                 # F A C chord roll
phrase([77, 72, 69, 65], 15.5, 0.7, C)     # melody resolving down to F
EV.append((18.4, 53, C))                    # low F, home

# add echoes (each note whispered back 0.42s later on the opposite side)
echoes = [(t + 0.42, m, 1 - p) for (t, m, p) in EV if p != C]
SCORE = sorted(EV + [(t, m, p, 0.45) for (t, m, p) in echoes], key=lambda e: e[0])
SCORE = [(e[0], e[1], e[2], (e[3] if len(e) > 3 else 1.0)) for e in SCORE]


def flare(t, side_x, w=0.28):
    v = 0.0
    for (te, m, p, a) in SCORE:
        sx = LX if p < 0.4 else (RX if p > 0.6 else 0.5)
        if abs(sx - side_x) < 0.02 and t >= te:
            v += a * math.exp(-((t - te) / w) ** 2)
    return min(2.0, v)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
FS = font(46)


def glow(a, cx, cy, rad, color, alpha):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)


BG = np.zeros((H, W, 3), np.float32)
_t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
BG[:] = (np.array([10, 12, 30]) * (1 - _t) + np.array([22, 22, 46]) * _t)[:, None, :].repeat(W, 1)
_r = np.random.default_rng(4)
for _ in range(90):
    BG[_r.integers(0, H), _r.integers(0, W)] += 120


def render(t):
    a = BG.copy()
    fl = flare(t, LX); fr = flare(t, RX)
    lx, rx, cy = LX * W, RX * W, CY * H
    # connecting thread brightens as they weave (phase 3-4)
    weave = max(0.0, min(1.0, (t - 9.5) / 2.0))
    if weave > 0.02:
        a_line = a
        im0 = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im0, "RGBA")
        d.line([(lx, cy), (rx, cy)], fill=(255, 210, 150, int(70 * weave)), width=2)
        a = np.asarray(im0, np.float32)
    glow(a, lx, cy, 34 + 30 * fl, [255, 200, 130], 0.5 + 0.7 * fl)
    glow(a, rx, cy, 34 + 30 * fr, [180, 200, 255], 0.5 + 0.7 * fr)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    tx = "call & response"
    bb = d.textbbox((0, 0), tx, font=FS)
    d.text(((W - (bb[2] - bb[0])) // 2, int(H * 0.14)), tx, font=FS, fill=(228, 226, 220, 210))
    frame = np.asarray(im, np.float32)
    frame = fx.bloom(frame, sigma=7, thr=205, gain=0.7)
    frame = fx.vignette(frame, 0.4)
    frame = fx.grain(frame, t * FPS, amt=0.015)
    return frame.clip(0, 255).astype(np.uint8)


def build_audio():
    n = int(DUR * SR)
    Lc = np.zeros(n, np.float32); Rc = np.zeros(n, np.float32)
    def st(sig, at, pan):
        add(Lc, sig * (1 - pan), at); add(Rc, sig * pan, at)
    # soft bed
    prog = [([53, 57, 60], 41), ([48, 52, 55], 48), ([50, 53, 57], 50), ([46, 50, 53], 46)] * 2
    step = DUR / len(prog)
    for k, (notes, br) in enumerate(prog):
        p = pad([midi(m) for m in notes], step + 0.3, amp=0.08)
        add(Lc, p, k * step); add(Rc, np.roll(p, 300), k * step)
        b = bass(midi(br), step + 0.2, amp=0.13)
        add(Lc, b, k * step); add(Rc, b, k * step)
    # the call & response piano
    for (te, m, p, amp) in SCORE:
        st(piano(midi(m), 2.4, amp=0.30 * amp), te, p)
    Lc = reverb(Lc); Rc = reverb(Rc)
    mix = np.tanh(np.stack([Lc, Rc], 1) * 1.2)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi, fo = int(SR), int(2 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def main():
    import imageio.v2 as imageio, imageio_ffmpeg, subprocess
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(DUR * FPS)
    writer = imageio.get_writer("md_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "18", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames ...")
    for i in range(n):
        writer.append_data(render(i / FPS))
        if (i + 1) % 48 == 0: print(f"  {i+1}/{n}")
    writer.close()
    write_wav("md.wav", build_audio())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "md_silent.mp4", "-i", "md.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "call_response_demo.mp4"],
                   check=True, capture_output=True)
    print("Done -> call_response_demo.mp4")


if __name__ == "__main__":
    main()
