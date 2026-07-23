"""
Richer environment drawings for THE OBSERVER WORLD — layered, atmospheric worlds
instead of flat gradients. Parallax terrain (back→front), horizon glow, depth haze,
stars, distant features (trees), foreground grass, and animated atmosphere (drifting
fog, fireflies, twinkle).

  base = build(territory)          # static numpy base (cache once)
  atmosphere(a, t, territory)      # add animated elements each frame
"""
import math
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920

PAL = {
    "home_fields": dict(
        sky_top=(8, 10, 26), sky_bot=(24, 24, 50), horizon=(120, 88, 60),
        hills=[(30, 32, 60), (23, 25, 50), (17, 19, 42), (11, 12, 30)],
        ground=(10, 11, 26), firefly=(255, 200, 130), fog=(40, 44, 78)),
    "fading_edge": dict(
        sky_top=(6, 8, 20), sky_bot=(18, 20, 40), horizon=(70, 74, 96),
        hills=[(22, 26, 46), (17, 20, 40), (13, 15, 32), (9, 10, 24)],
        ground=(9, 10, 22), firefly=(170, 190, 235), fog=(34, 40, 66)),
}


def _grad(top, bot):
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t)[:, None, :].repeat(W, 1)
    return a


def _ridge(d, base_y, amp, ph, color, rng):
    pts = [(0, H)]
    for x in range(0, W + 1, 16):
        y = base_y + amp * (0.55 * math.sin(x * 0.0055 + ph)
                            + 0.30 * math.sin(x * 0.014 + ph * 1.7)
                            + 0.15 * math.sin(x * 0.031 + ph * 0.6))
        pts.append((x, y))
    pts.append((W, H))
    d.polygon(pts, fill=color)


def _tree(d, x, y, s, color):
    d.rectangle([x - 3 * s, y - 30 * s, x + 3 * s, y], fill=color)
    for dx, dy, r in [(0, -34, 20), (-13, -28, 14), (13, -30, 15), (0, -46, 14), (-7, -40, 11), (8, -42, 11)]:
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=color)


def build(territory="home_fields"):
    p = PAL.get(territory, PAL["home_fields"])
    a = _grad(p["sky_top"], p["sky_bot"])
    # horizon glow band (warm light pooling at the far edge of the world)
    hz = int(0.66 * H)
    yy = np.arange(H)[:, None]
    band = np.exp(-((yy - hz) ** 2) / (2 * (0.10 * H) ** 2)).astype(np.float32)   # (H,1)
    a += band[..., None] * np.array(p["horizon"], np.float32) * 0.35
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    # stars (varied sizes), a low moon
    for _ in range(190):
        sx, sy = rng.integers(0, W), rng.integers(0, int(0.6 * H))
        r = rng.choice([1, 1, 1, 2]); b = rng.integers(120, 210)
        d.ellipse([sx, sy, sx + r, sy + r], fill=(b, b, min(255, b + 20)))
    mx, my, mr = int(0.74 * W), int(0.20 * H), 46
    for r, al in ((mr + 26, 22), (mr + 10, 40), (mr, 200)):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([mx - r, my - r, mx + r, my + r], fill=(228, 224, 210, al))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    # PARALLAX terrain — four ridges back→front (hazier/lighter far, darker near)
    bases = [0.60, 0.68, 0.75, 0.83]
    amps = [26, 34, 46, 60]
    for i, col in enumerate(p["hills"]):
        _ridge(d, bases[i] * H, amps[i], 1.3 + i * 2.1, col, rng)
    # distant trees on the mid ridge; a lone near tree
    for tx, ty, s, ci in [(0.16, 0.70, 0.7, 1), (0.30, 0.69, 0.55, 1), (0.83, 0.72, 0.85, 2),
                          (0.92, 0.71, 0.6, 2)]:
        _tree(d, tx * W, ty * H, s, p["hills"][ci])
    _tree(d, 0.12 * W, 0.86 * H, 1.5, (7, 8, 18))          # foreground hero tree
    # foreground grass tufts (a soft near layer)
    a = np.asarray(im, np.float32)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(150):
        gx = rng.integers(0, W); gh = rng.integers(20, 60); sway = rng.uniform(-10, 10)
        d.line([(gx, H), (gx + sway, H - gh)], fill=(6, 7, 16), width=2)
    return np.asarray(im, np.float32)


# animated atmosphere -------------------------------------------------------
_r = np.random.default_rng(31)
_FFX = _r.uniform(0, 1, 40); _FFY = _r.uniform(0.45, 0.9, 40)
_FFSP = _r.uniform(0.008, 0.03, 40); _FFPH = _r.uniform(0, 6.28, 40); _FFR = _r.uniform(2.5, 6, 40)
_STX = _r.integers(0, W, 120); _STY = _r.integers(0, int(0.6 * H), 120)
_STPH = _r.uniform(0, 6.28, 120)


def _glow(a, cx, cy, rad, color, alpha):
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)


def atmosphere(a, t, territory="home_fields"):
    p = PAL.get(territory, PAL["home_fields"])
    # star twinkle
    tw = 0.5 + 0.5 * np.sin(t * 1.6 + _STPH)
    a[_STY, _STX] += (tw * 0.4)[:, None] * np.array([200, 206, 230], np.float32)
    # drifting depth-fog (two soft horizontal bands sliding opposite ways)
    for k, (yc, spd, al) in enumerate([(0.60, 0.010, 0.06), (0.72, -0.007, 0.05)]):
        off = (t * spd) % 1.0
        prof = (0.5 + 0.5 * np.sin(np.linspace(0, 6.28, W) + off * 6.28 + k))
        yy = int(yc * H)
        a[yy - 40:yy + 40, :] += (prof * al)[None, :, None] * np.array(p["fog"], np.float32)
    # fireflies drifting up, glinting
    for i in range(len(_FFX)):
        fx = (_FFX[i] + 0.02 * math.sin(t * 0.5 + _FFPH[i])) % 1.0
        fy = (_FFY[i] - t * _FFSP[i]) % 0.5 + 0.42
        fl = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 2.4 + _FFPH[i]))
        _glow(a, fx * W, fy * H, _FFR[i], p["firefly"], 0.5 * fl)
    return a
