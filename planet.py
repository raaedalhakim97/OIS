"""
A rotating "little planet" ground for THE OBSERVER WORLD. The Keeper walks in place
on top of a curved, spinning ball; the surface (grass + features) scrolls opposite
his walk, so he appears to travel and search across the world while the sky changes.

  sky = build_sky(scene)                     # sky only (gradient + moon/sun + stars)
  base, mask = planet_base(scene)            # cached shaded ball
  draw_surface(a, theta, scene)              # rotating grass/features on the ball
apex (where the Keeper stands) = (W/2, APEX_Y)
"""
import math
import numpy as np
from PIL import Image, ImageDraw
import world

W, H = 1080, 1920
APEX_Y = 0.70 * H                 # the top of the ball — where the Keeper stands
CX = W / 2
R = 0.60 * H                      # planet radius
CY = APEX_Y + R                   # planet centre (below screen)
PAL = world.PAL


def _grad(top, bot):
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a[:] = (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t)[:, None, :].repeat(W, 1)
    return a


_skycache = {}
def build_sky(scene):
    if scene in _skycache: return _skycache[scene]
    p = PAL.get(scene, PAL["night"])
    a = _grad(p["sky_top"], p["sky_bot"])
    hz = int(0.70 * H)
    yy = np.arange(H)[:, None]
    band = np.exp(-((yy - hz) ** 2) / (2 * (0.14 * H) ** 2)).astype(np.float32)
    a += band[..., None] * np.array(p["horizon"], np.float32) * 0.45
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    if scene in ("night", "home_fields", "fading_edge", "dawn", "dusk"):
        for _ in range(150):
            sx, sy = rng.integers(0, W), rng.integers(0, int(0.6 * H))
            r = rng.choice([1, 1, 1, 2]); b = rng.integers(110, 200)
            d.ellipse([sx, sy, sx + r, sy + r], fill=(b, b, min(255, b + 20)))
    kind, ox, oy, ocol = p["orb"]
    mx, my, mr = int(ox * W), int(oy * 0.62 * H), 50
    for r, al in ((mr + 40, 26), (mr + 16, 46), (mr, 210)):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([mx - r, my - r, mx + r, my + r], fill=(*ocol, al))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    a = np.asarray(im, np.float32)
    _skycache[scene] = a
    return a


_pcache = {}
def planet_base(scene):
    if scene in _pcache: return _pcache[scene]
    p = PAL.get(scene, PAL["night"])
    planet = np.zeros((H, W, 3), np.float32)
    mask = np.zeros((H, W), bool)
    y0 = max(0, int(CY - R) - 2)
    ys, xs = np.mgrid[y0:H, 0:W].astype(np.float32)
    d2 = (xs - CX) ** 2 + (ys - CY) ** 2
    inside = d2 <= R * R
    trim = np.clip((ys - (CY - R)) / (2 * R), 0, 1)
    top_col = np.array(p["horizon"], np.float32) * 0.5
    bot_col = np.array(p["hills"][-1], np.float32) * 0.8
    col = top_col[None, None, :] * (1 - trim[..., None] ** 0.6) + bot_col[None, None, :] * (trim[..., None] ** 0.6)
    nz = np.sqrt(np.clip(1 - d2 / (R * R), 0, 1))          # spherical shading (darker at rim)
    col *= (0.55 + 0.45 * nz)[..., None]
    sub = planet[y0:H]; sub[inside] = col[inside]; planet[y0:H] = sub
    msub = mask[y0:H]; msub[inside] = True; mask[y0:H] = msub
    _pcache[scene] = (planet, mask)
    return planet, mask


# ---- surface features: grass tufts + occasional trees/rocks around the whole ball ----
_r = np.random.default_rng(19)
GRASS_PHI = np.sort(_r.uniform(0, 2 * math.pi, 220))
GRASS_LEN = _r.uniform(16, 40, 220)
GRASS_SWAY = _r.uniform(-0.25, 0.25, 220)
FEAT = [(_r.uniform(0, 2 * math.pi), _r.choice(["tree", "rock", "tree"])) for _ in range(14)]


def _surf_pt(phi):
    px = CX + R * math.sin(phi)
    py = CY - R * math.cos(phi)
    return px, py, math.sin(phi), -math.cos(phi)      # point + outward normal


def draw_surface(im, theta, scene, front_clear=0.0):
    """Draw the rotating grass + features on the visible top arc (as they scroll by).
    front_clear>0 keeps the central front arc (|angle|<front_clear) free of trees/rocks,
    so something laid out on the ground there (e.g. a scale of notes) reads cleanly."""
    d = ImageDraw.Draw(im, "RGBA")
    p = PAL.get(scene, PAL["night"])
    gcol = tuple(int(c * 0.7) for c in p["hills"][1])
    for i in range(len(GRASS_PHI)):
        a = GRASS_PHI[i] - theta
        c = math.cos(a)
        if c < 0.32: continue                          # only the visible top arc
        px = CX + R * math.sin(a); py = CY - R * math.cos(a)
        nx, ny = math.sin(a), -math.cos(a)
        ln = GRASS_LEN[i] * (0.5 + 0.5 * c)            # foreshorten near the rim
        sway = GRASS_SWAY[i]
        tx = px + nx * ln + (-ny) * sway * ln * 0.4
        ty = py + ny * ln + (nx) * sway * ln * 0.4
        al = int(200 * min(1, (c - 0.32) / 0.3))
        d.line([(px, py), (tx, ty)], fill=(*gcol, al), width=2)
    for phi, kind in FEAT:
        a = phi - theta; c = math.cos(a)
        if c < 0.55: continue
        aa = math.atan2(math.sin(a), math.cos(a))          # wrapped angle from apex
        if front_clear > 0 and abs(aa) < front_clear: continue
        px = CX + R * math.sin(a); py = CY - R * math.cos(a)
        nx, ny = math.sin(a), -math.cos(a)
        s = (0.6 + 0.6 * c)
        col = tuple(int(v * 0.6) for v in p["hills"][2]) + (int(220 * min(1, (c - 0.55) / 0.3)),)
        if kind == "tree":
            bx, by = px + nx * 40 * s, py + ny * 40 * s
            d.line([(px, py), (bx, by)], fill=col, width=int(4 * s))
            for dx, dy, rr in [(0, -10, 16), (-8, -4, 11), (8, -6, 12)]:
                d.ellipse([bx + dx * s - rr * s, by + dy * s - rr * s,
                           bx + dx * s + rr * s, by + dy * s + rr * s], fill=col)
        else:
            rr = 12 * s
            d.ellipse([px + nx * 8 - rr, py + ny * 8 - rr, px + nx * 8 + rr, py + ny * 8 + rr], fill=col)
