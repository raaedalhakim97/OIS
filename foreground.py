"""
foreground — a near layer, so the camera move reads as depth instead of a crop.

Everything in this world has been sitting on one plane at one distance. When the camera
pushes in, the whole picture scales together and the eye reads it as a zoom on a
photograph. Put something close to the lens that moves *more* than the world behind it
and the same move becomes parallax — the shot acquires a third dimension for free.

Drawn after the camera crop, offset by the camera's own motion times a factor above 1.

  draw(im, ts, cam, scene="night")
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920

# (x fraction, height px, lean, thickness) — a few blades and a stone, no more.
# Sparse on purpose: this layer frames the shot, it does not decorate it.
BLADES = [(0.045, 210, -0.22, 9), (0.085, 158, -0.10, 7), (0.135, 250, 0.06, 10),
          (0.175, 132, 0.18, 6),  (0.815, 176, -0.14, 8), (0.870, 244, 0.05, 11),
          (0.925, 150, 0.16, 7),  (0.965, 205, -0.08, 9)]


def _sway(ts, i):
    return math.sin(ts * 0.42 + i * 1.7) * 6.0 + math.sin(ts * 0.19 + i) * 3.0


def draw(im, ts, cam, strength=1.0, tint=(9, 10, 18)):
    """cam is (zoom, centre_x_fraction, centre_y_fraction) from the episode's camera."""
    z, ccx, ccy = cam
    # the near layer answers the camera harder than the world does
    px = (ccx - 0.5) * W * 0.62 * strength
    py = (ccy - 0.5) * H * 0.20 * strength
    scale = 1.0 + (z - 1.0) * 2.1 * strength

    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    base = H + 26
    for i, (fx, hgt, lean, thick) in enumerate(BLADES):
        x = fx * W - px + _sway(ts, i)
        h = hgt * scale
        tipx = x + lean * h
        d.line([(x, base), (x + lean * h * 0.45, base - h * 0.55), (tipx, base - h)],
               fill=tint + (255,), width=max(2, int(thick * scale)), joint="curve")

    # a stone at the lower edge, just enough to anchor the corner
    sx = 0.30 * W - px * 1.15
    sy = base - 30 * scale + py * 0.3
    rw, rh = 190 * scale, 92 * scale
    d.ellipse([sx - rw, sy - rh, sx + rw, sy + rh], fill=tint + (255,))

    # out of focus, because it is close to the lens
    lay = lay.filter(ImageFilter.GaussianBlur(radius=max(1.2, 3.4 * scale)))
    im.alpha_composite(lay) if im.mode == "RGBA" else im.paste(lay, (0, 0), lay)
    return im


def motes(a, ts, cam, glow, colour, n=5, strength=1.0):
    """A few big, soft, out-of-focus lights drifting close to the lens."""
    z, ccx, ccy = cam
    px = (ccx - 0.5) * W * 0.62 * strength
    for i in range(n):
        u = ((ts * 0.031 + i * 0.23) % 1.0)
        x = ((0.12 + 0.19 * i) * W) - px + 70 * math.sin(ts * 0.15 + i * 2.1)
        y = H - u * 1.15 * H
        al = 0.11 * math.sin(math.pi * u) * (0.6 + 0.4 * math.sin(ts * 0.5 + i))
        if al > 0.004:
            glow(a, x, y, 34 + 12 * math.sin(ts * 0.3 + i), colour, al)
