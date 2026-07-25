"""
eye — THE OBSERVER'S EYE.
The screen is the eye of the one watching the world; the corner/edge fade is its rim.
Scenes change by BLINKING: curved lids sweep in from top and bottom (meeting at the
centre, as a real lid does), a beat of dark, then they open slower than they closed.

  amt = blink_amount(ts, BLINKS)     # 0 = open, 1 = shut
  apply_lids(frame, amt)             # in place, after bloom/vignette

BLINKS entries: (t_center, close, hold, open, depth)
  depth < 1 gives a half-blink (a flinch, or a slow story-blink).
"""
import numpy as np

_cache = {}


def blink_amount(ts, blinks):
    a = 0.0
    for (tc, close, hold, opn, depth) in blinks:
        s = tc - close                      # start closing
        e = tc + hold + opn                 # fully open again
        if ts < s or ts > e: continue
        if ts < tc:
            u = (ts - s) / close
            v = u * u                       # snaps shut
        elif ts < tc + hold:
            v = 1.0
        else:
            u = (ts - tc - hold) / opn
            v = 1.0 - (u ** 0.7)            # opens slower, eases wide
        a = max(a, depth * max(0.0, min(1.0, v)))
    return a


def _fields(shape):
    key = shape
    if key in _cache: return _cache[key]
    H, W = shape
    y = np.arange(H, dtype=np.float32)[:, None]
    x = np.arange(W, dtype=np.float32)[None, :]
    bulge = 1.0 - ((x / W - 0.5) * 2.0) ** 2            # lids dip lowest at the centre
    curve = 0.74 + 0.26 * bulge
    _cache[key] = (y, curve.astype(np.float32))
    return _cache[key]


def apply_lids(frame, amt, reach=0.58, feather=52.0):
    """Darken behind curved upper/lower lids. frame: float32 (H,W,3), modified in place."""
    if amt <= 0.001: return frame
    H, W = frame.shape[:2]
    y, curve = _fields((H, W))
    travel = amt * reach * H
    top = travel * curve                                 # lower edge of the upper lid
    bot = H - travel * curve                             # upper edge of the lower lid
    lid = np.clip((top - y) / feather + 1.0, 0.0, 1.0)
    lid = np.maximum(lid, np.clip((y - bot) / feather + 1.0, 0.0, 1.0))
    frame *= (1.0 - lid)[..., None]
    return frame
