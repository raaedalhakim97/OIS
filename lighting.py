"""
lighting — make the lights in this world actually light something.

Until now every glow was an additive blob painted over a static background: a lantern
could sit beside the Keeper without brightening the ground under it, and the Keeper
stayed pure black however close he stood to it. That reads as a hole in the picture
rather than a body in a place, which is a strange weakness for a series about who is
carrying the light.

Three things, all cheap:

  spill(a, mask, lights)          the ground brightens near a source
  rim(sprite, x, y, lights)       a silhouette catches a warm edge on the lit side
  cast(a, x, y, lights, ground)   and throws a shadow away from it

A light is (x, y, radius, colour, intensity). Radius is the reach in pixels, not the
size of the visible glow — a lantern is a small dot with a long reach.
"""
import math

import numpy as np
from PIL import Image


def _win(w, h, cx, cy, rad):
    """The rectangle a source can reach, clipped to the frame."""
    x0 = max(0, int(cx - rad)); x1 = min(w, int(cx + rad))
    y0 = max(0, int(cy - rad)); y1 = min(h, int(cy + rad))
    return x0, y0, x1, y1


def spill(a, mask, lights, amount=1.0, floor=0.0):
    """Brighten the world near each source, strongest on surfaces facing it.

    `mask` is the ground mask from planet_base — the spill is applied only where there
    is something to catch it, so the sky does not glow from a lantern on the hill.
    """
    H, W = a.shape[:2]
    for (lx, ly, rad, col, inten) in lights:
        if inten <= 0.01:
            continue
        x0, y0, x1, y1 = _win(W, H, lx, ly, rad)
        if x1 <= x0 or y1 <= y0:
            continue
        yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.sqrt((xg - lx) ** 2 + (yg - ly) ** 2) / rad
        fall = np.clip(1.0 - d, 0.0, 1.0) ** 2.0            # inverse-square-ish, clamped
        # light pools on the ground rather than in the air above it
        below = np.clip((yg - ly) / (rad * 0.55), -1.0, 1.0)
        fall *= 0.45 + 0.55 * np.clip(below + 0.35, 0.0, 1.0)
        m = mask[y0:y1, x0:x1]
        fall = fall * (floor + (1.0 - floor) * m)
        a[y0:y1, x0:x1] += (fall * inten * amount)[..., None] * np.array(col, np.float32)


def rim(sprite, sx, sy, lights, width=5, gain=1.0, max_alpha=210):
    """Return the sprite with a lit edge on the side facing the light.

    Works off the alpha channel: shifting it away from the light and subtracting leaves
    a band exactly on the lit rim. The body stays black, which is the point — only the
    edge catches, the way a silhouette really behaves against a lamp.
    """
    if not lights:
        return sprite
    A = np.asarray(sprite.getchannel("A"), np.float32)
    h, w = A.shape
    cx, cy = sx, sy - h * 0.5
    rgb = np.zeros((h, w, 3), np.float32)
    lit = False
    for (lx, ly, rad, col, inten) in lights:
        d = math.hypot(lx - cx, ly - cy)
        if inten <= 0.01 or d > rad * 1.35 or d < 1e-6:
            continue
        ux, uy = (lx - cx) / d, (ly - cy) / d
        k = max(1, int(width))
        shifted = np.roll(np.roll(A, int(round(-uy * k)), axis=0), int(round(-ux * k)), axis=1)
        edge = np.clip(A - shifted, 0.0, 255.0) / 255.0
        if edge.max() < 1e-3:
            continue
        strength = inten * gain * (1.0 - min(1.0, d / (rad * 1.35))) ** 1.4
        rgb += edge[..., None] * np.array(col, np.float32) * strength
        lit = True
    if not lit:
        return sprite
    out = np.asarray(sprite, np.float32).copy()
    out[..., :3] = np.clip(out[..., :3] + rgb, 0, 255)
    # the rim must not punch a hole where the sprite is transparent
    keep = np.maximum(A, np.clip(rgb.max(2), 0, max_alpha) * (A > 8))
    out[..., 3] = np.clip(keep, 0, 255)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def cast(a, fx, fy, lights, ground_y, length=2.2, amount=0.42, width=54):
    """Throw a shadow along the ground, away from the brightest nearby source.

    One shadow does more for 'this is a real place' than any amount of particles, and
    the series has never had one.
    """
    H, W = a.shape[:2]
    best = None
    for L in lights:
        d = math.hypot(L[0] - fx, L[1] - fy)
        score = L[4] * max(0.0, 1.0 - d / (L[2] * 1.2))
        if score > 0.02 and (best is None or score > best[0]):
            best = (score, L, d)
    if best is None:
        return
    score, (lx, ly, rad, col, inten), d = best
    dx = fx - lx
    if abs(dx) < 1e-6:
        dx = 1e-6
    reach = min(360.0, (rad - d) * length * (1.0 if abs(dx) > 8 else 0.4))
    if reach < 12:
        return
    sign = 1.0 if dx > 0 else -1.0
    n = 22
    for i in range(n):
        u = (i + 0.5) / n
        px = fx + sign * reach * u
        py = ground_y(px) + 4
        rr = width * (1.0 - 0.55 * u)
        al = amount * score * (1.0 - u) ** 1.5
        x0, y0, x1, y1 = _win(W, H, px, py, rr * 2.2)
        if x1 <= x0 or y1 <= y0:
            continue
        yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        g = np.exp(-(((xg - px) / rr) ** 2 + ((yg - py) / (rr * 0.32)) ** 2))
        a[y0:y1, x0:x1] *= (1.0 - np.clip(g * al, 0, 0.85))[..., None]
