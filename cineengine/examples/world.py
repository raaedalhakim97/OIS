"""
Richer environment drawings for THE OBSERVER WORLD — layered, atmospheric worlds
that change with time of day and season. Parallax terrain, horizon glow, a sun or
moon, depth haze, distant + foreground trees, and animated atmosphere (fog,
fireflies, or falling snow). Kept moody/dark-friendly so silhouettes + light read.

  base = build(scene)              # static numpy base (cache once per scene)
  atmosphere(a, t, scene)          # add animated elements each frame
scenes: night · dawn · morning · golden · dusk · winter (+ home_fields, fading_edge)
"""
import math
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920


def _P(**k):
    d = dict(sky_top=(8, 10, 26), sky_bot=(22, 24, 48), horizon=(70, 64, 96), horizon_y=0.66,
             hills=[(30, 32, 60), (23, 25, 50), (17, 19, 42), (11, 12, 30)], ground=None,
             orb=("moon", 0.74, 0.20, (228, 224, 210)), particle=("firefly", (255, 200, 130)),
             fog=(40, 44, 78), trees=True, snow_ground=False, bare=False)
    d.update(k); return d

PAL = {
    "night":   _P(),
    "home_fields": _P(),
    "dawn":    _P(sky_top=(18, 22, 50), sky_bot=(58, 46, 70), horizon=(224, 140, 104), horizon_y=0.64,
                  hills=[(40, 40, 66), (30, 30, 56), (22, 22, 46), (13, 13, 32)],
                  orb=("sun", 0.30, 0.30, (255, 180, 120)), particle=("firefly", (255, 200, 140)),
                  fog=(70, 56, 74)),
    "morning": _P(sky_top=(28, 48, 88), sky_bot=(74, 98, 132), horizon=(210, 190, 160), horizon_y=0.66,
                  hills=[(48, 62, 84), (36, 50, 72), (26, 40, 60), (16, 26, 42)],
                  orb=("sun", 0.52, 0.20, (255, 236, 190)), particle=("firefly", (255, 235, 190)),
                  fog=(64, 82, 110)),
    "golden":  _P(sky_top=(34, 30, 60), sky_bot=(128, 92, 70), horizon=(235, 165, 110), horizon_y=0.65,
                  hills=[(58, 46, 56), (44, 36, 48), (30, 26, 40), (18, 16, 30)],
                  orb=("sun", 0.70, 0.28, (255, 195, 120)), particle=("firefly", (255, 210, 150)),
                  fog=(96, 72, 68)),
    "dusk":    _P(sky_top=(26, 22, 54), sky_bot=(78, 52, 84), horizon=(206, 112, 118), horizon_y=0.64,
                  hills=[(44, 34, 62), (33, 26, 52), (23, 19, 42), (13, 11, 30)],
                  orb=("sun", 0.30, 0.34, (240, 120, 110)), particle=("firefly", (255, 190, 150)),
                  fog=(76, 54, 82)),
    "winter":  _P(sky_top=(34, 46, 74), sky_bot=(78, 96, 128), horizon=(170, 190, 216), horizon_y=0.64,
                  hills=[(120, 134, 160), (96, 110, 140), (74, 88, 118), (52, 64, 92)],
                  orb=("sun", 0.62, 0.22, (220, 228, 240)), particle=("snow", (236, 242, 252)),
                  fog=(120, 134, 162), snow_ground=True, bare=True),
    "fading_edge": _P(sky_top=(6, 8, 20), sky_bot=(18, 20, 40), horizon=(70, 74, 96),
                  hills=[(22, 26, 46), (17, 20, 40), (13, 15, 32), (9, 10, 24)],
                  orb=("moon", 0.74, 0.20, (210, 214, 226)), particle=("firefly", (170, 190, 235)),
                  fog=(34, 40, 66)),
}


def _grad(top, bot):
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t)[:, None, :].repeat(W, 1)
    return a


def _ridge(d, base_y, amp, ph, color):
    pts = [(0, H)]
    for x in range(0, W + 1, 16):
        y = base_y + amp * (0.55 * math.sin(x * 0.0055 + ph) + 0.30 * math.sin(x * 0.014 + ph * 1.7)
                            + 0.15 * math.sin(x * 0.031 + ph * 0.6))
        pts.append((x, y))
    pts.append((W, H)); d.polygon(pts, fill=color)


def _tree(d, x, y, s, color, bare=False):
    d.rectangle([x - 3 * s, y - 30 * s, x + 3 * s, y], fill=color)
    if bare:
        for dx, dy in [(-10, -30), (10, -34), (0, -44), (-6, -40), (7, -42)]:
            d.line([(x, y - 20 * s), (x + dx * s, y + dy * s)], fill=color, width=max(1, int(2 * s)))
    else:
        for dx, dy, r in [(0, -34, 20), (-13, -28, 14), (13, -30, 15), (0, -46, 14), (-7, -40, 11), (8, -42, 11)]:
            d.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=color)


def build(scene="night"):
    p = PAL.get(scene, PAL["night"])
    a = _grad(p["sky_top"], p["sky_bot"])
    hz = int(p["horizon_y"] * H)
    yy = np.arange(H)[:, None]
    band = np.exp(-((yy - hz) ** 2) / (2 * (0.12 * H) ** 2)).astype(np.float32)
    a += band[..., None] * np.array(p["horizon"], np.float32) * 0.40
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    # stars — only for the darker scenes
    if scene in ("night", "home_fields", "fading_edge", "dawn", "dusk"):
        for _ in range(170):
            sx, sy = rng.integers(0, W), rng.integers(0, int(0.55 * H))
            r = rng.choice([1, 1, 1, 2]); b = rng.integers(110, 200)
            d.ellipse([sx, sy, sx + r, sy + r], fill=(b, b, min(255, b + 20)))
    # sun / moon
    kind, ox, oy, ocol = p["orb"]
    mx, my = int(ox * W), int(oy * H); mr = 46 if kind == "moon" else 54
    for r, al in ((mr + 40, 26), (mr + 16, 46), (mr, 210)):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([mx - r, my - r, mx + r, my + r], fill=(*ocol, al))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    # parallax terrain
    bases = [0.60, 0.68, 0.75, 0.83]; amps = [26, 34, 46, 60]
    for i, col in enumerate(p["hills"]):
        _ridge(d, bases[i] * H, amps[i], 1.3 + i * 2.1, col)
    # trees
    if p["trees"]:
        for tx, ty, s, ci in [(0.16, 0.70, 0.7, 1), (0.30, 0.69, 0.55, 1), (0.83, 0.72, 0.85, 2)]:
            _tree(d, tx * W, ty * H, s, p["hills"][ci], bare=p["bare"])
        _tree(d, 0.12 * W, 0.86 * H, 1.5, tuple(max(0, c - 6) for c in p["hills"][3]), bare=p["bare"])
    # snow blanket on the ground for winter
    if p["snow_ground"]:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([-0.2 * W, 0.80 * H, 1.2 * W, 1.3 * H], fill=(210, 222, 240, 90))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(im)
    # foreground grass (skip on snow)
    if not p["snow_ground"]:
        for _ in range(150):
            gx = rng.integers(0, W); gh = rng.integers(20, 60); sway = rng.uniform(-10, 10)
            d.line([(gx, H), (gx + sway, H - gh)], fill=(6, 7, 16), width=2)
    return np.asarray(im, np.float32)


# animated atmosphere -------------------------------------------------------
_r = np.random.default_rng(31)
_FFX = _r.uniform(0, 1, 40); _FFY = _r.uniform(0.45, 0.9, 40)
_FFSP = _r.uniform(0.008, 0.03, 40); _FFPH = _r.uniform(0, 6.28, 40); _FFR = _r.uniform(2.5, 6, 40)
_SNX = _r.uniform(0, 1, 90); _SNY = _r.uniform(0, 1, 90); _SNSP = _r.uniform(0.03, 0.08, 90)
_SNPH = _r.uniform(0, 6.28, 90); _SNR = _r.uniform(2, 4.5, 90)
_STX = _r.integers(0, W, 110); _STY = _r.integers(0, int(0.55 * H), 110); _STPH = _r.uniform(0, 6.28, 110)


def _glow(a, cx, cy, rad, color, alpha):
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)


def atmosphere(a, t, scene="night"):
    p = PAL.get(scene, PAL["night"])
    if scene in ("night", "home_fields", "fading_edge", "dawn", "dusk"):
        tw = 0.5 + 0.5 * np.sin(t * 1.6 + _STPH)
        a[_STY, _STX] += (tw * 0.4)[:, None] * np.array([200, 206, 230], np.float32)
    # drifting depth-fog
    for k, (yc, spd, al) in enumerate([(0.60, 0.010, 0.05), (0.72, -0.007, 0.045)]):
        off = (t * spd) % 1.0
        prof = (0.5 + 0.5 * np.sin(np.linspace(0, 6.28, W) + off * 6.28 + k))
        yy = int(yc * H)
        a[yy - 40:yy + 40, :] += (prof * al)[None, :, None] * np.array(p["fog"], np.float32)
    kind, col = p["particle"]
    if kind == "snow":
        for i in range(len(_SNX)):
            sx = (_SNX[i] + 0.04 * math.sin(t * 0.6 + _SNPH[i])) % 1.0
            sy = (_SNY[i] + t * _SNSP[i]) % 1.0
            _glow(a, sx * W, sy * H, _SNR[i], col, 0.5)
    else:
        for i in range(len(_FFX)):
            fx = (_FFX[i] + 0.02 * math.sin(t * 0.5 + _FFPH[i])) % 1.0
            fy = (_FFY[i] - t * _FFSP[i]) % 0.5 + 0.42
            fl = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 2.4 + _FFPH[i]))
            _glow(a, fx * W, fy * H, _FFR[i], col, 0.5 * fl)
    return a
