"""
Standard intro title-card + Observer's-Question (quiz) overlay for THE OBSERVER
WORLD. Every episode opens with this card:  CHAPTER · EPISODE № · TITLE · LAND.
A single lantern light in the dark, serif type, the world's calm palette.

  title_frame(t, chapter, ep, title, land)  -> uint8 frame  (a ~5s intro)
  quiz_overlay(im, t, question, ...)         -> draws the Observer's Question

Reuse across all episodes so every video shares one identity.
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 24
GOLD = (255, 200, 130)


def _font(sz, serif=True):
    fam = "DejaVuSerif" if serif else "DejaVuSans"
    for p in (f"/usr/share/fonts/truetype/dejavu/{fam}.ttf",
              f"/usr/share/fonts/truetype/dejavu/{fam}-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def _bg():
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array([5, 7, 20], np.float32) * (1 - t)
            + np.array([13, 15, 33], np.float32) * t)[:, None, :].repeat(W, 1)
    return a
BG = _bg()
_r = np.random.default_rng(5)
STARX = _r.integers(0, W, 110); STARY = _r.integers(0, H, 110)
STARB = _r.uniform(0.2, 0.9, 110); STARPH = _r.uniform(0, 6.28, 110)


def _glow(a, cx, cy, rad, color, alpha):
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)


def _spaced(s, gap=" "):     # letter-spacing for the chapter/episode line
    return gap.join(list(s))


def _text_center(d, y, s, font, fill, alpha):
    r, g, b = fill
    bb = d.textbbox((0, 0), s, font=font)
    d.text(((W - (bb[2] - bb[0])) // 2, y), s, font=font, fill=(r, g, b, int(alpha)))
    return int(bb[3] - bb[1])


def title_frame(t, chapter="I", ep="1", title="The Note Between",
                land="the Home Fields", dur=5.0):
    """One frame of the intro card at time t (seconds)."""
    a = BG.copy()
    tw = 0.5 + 0.5 * np.sin(t * 1.6 + STARPH)
    a[STARY, STARX] += (STARB * tw * 0.4)[:, None] * np.array([210, 214, 234])
    # a single lantern breathing in the dark
    pulse = 0.9 + 0.1 * math.sin(t * 2.2)
    _glow(a, W * 0.5, H * 0.36, 42, GOLD, 0.9 * pulse * min(1.0, t / 0.8))
    _glow(a, W * 0.5, H * 0.36, 16, (255, 235, 200), 1.0 * pulse * min(1.0, t / 0.8))

    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")

    # timed reveals: chapter/ep line, then title, then land
    f1 = np.interp(t, [0.4, 1.1, dur - 0.6, dur], [0, 1, 1, 0])
    f2 = np.interp(t, [1.1, 1.9, dur - 0.6, dur], [0, 1, 1, 0])
    f3 = np.interp(t, [2.0, 2.8, dur - 0.6, dur], [0, 1, 1, 0])

    FCE = _font(34); FTIT = _font(76); FLAND = _font(38)
    _text_center(d, int(H * 0.50), _spaced(f"CHAPTER {chapter}   ·   EPISODE {ep}"),
                 FCE, (210, 186, 150), 210 * f1)
    # title (wrap to 2 lines if long)
    words = title.split()
    line, lines = "", []
    for w in words:
        test = (line + " " + w).strip()
        if d.textbbox((0, 0), test, font=FTIT)[2] > W * 0.86:
            lines.append(line); line = w
        else:
            line = test
    lines.append(line)
    yy = int(H * 0.545)
    for ln in lines:
        h = _text_center(d, yy, ln, FTIT, (238, 231, 218), 240 * f2)
        yy += int(h * 1.9)
    # a thin divider + the land/territory
    if f3 > 0.02:
        cy = yy + 18
        d.line([(W * 0.36, cy), (W * 0.64, cy)], fill=(150, 130, 100, int(150 * f3)), width=2)
        _text_center(d, cy + 22, land, FLAND, (196, 176, 146), 200 * f3)

    frame = np.asarray(im, np.float32)
    # soft vignette
    yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xv - W / 2) / (W / 2)) ** 2 + ((yv - H / 2) / (H / 2)) ** 2)
    frame *= (1 - 0.42 * np.clip(r - 0.5, 0, 1))[..., None]
    return frame.clip(0, 255).astype(np.uint8)


def quiz_overlay(im, t, question, s, e, options=None, y=0.60):
    """Draw the Observer's Question — a prompt for the viewer to think about while
    watching. `options` (optional list) renders as choices to consider. Styled
    quiet, in-world. Call inside an episode's render() over an existing PIL image."""
    if not (s <= t <= e): return
    fade = np.interp(t, [s, s + 0.6, e - 0.6, e], [0, 1, 1, 0])
    d = ImageDraw.Draw(im, "RGBA")
    FQ = _font(30); FL = _font(42); FO = _font(38)
    _text_center(d, int(H * y), _spaced("THE OBSERVER'S QUESTION"), FQ, (200, 178, 146), 190 * fade)
    yy = int(H * y) + 46
    for ln in question.split("\n"):
        bb = d.textbbox((0, 0), ln, font=FL)
        d.text(((W - (bb[2] - bb[0])) // 2, yy), ln, font=FL, fill=(236, 231, 220, int(236 * fade)))
        yy += int((bb[3] - bb[1]) * 1.5)
    if options:
        yy += 14
        for i, opt in enumerate(options):
            s_ = f"{chr(97 + i)}.  {opt}"
            bb = d.textbbox((0, 0), s_, font=FO)
            d.text(((W - (bb[2] - bb[0])) // 2, yy), s_, font=FO, fill=(206, 198, 184, int(216 * fade)))
            yy += int((bb[3] - bb[1]) * 1.7)


if __name__ == "__main__":
    Image.fromarray(title_frame(3.2, "I", "2", "The First Light",
                                land="the Home Fields")).save("title_demo.png")
    # a quiz-card demo composited on a dark frame
    base = Image.fromarray(_bg().clip(0, 255).astype(np.uint8))
    quiz_overlay(base, 1.0, "which note was missing —\nand who carried it?",
                 0.0, 2.0, options=["the flat", "the fifth", "the stranger"], y=0.42)
    base.save("quiz_demo.png")
    print("saved title_demo.png, quiz_demo.png")
