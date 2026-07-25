"""
Shared musical staff for THE OBSERVER WORLD — a five-line treble ("sol key") staff
that floats above the keepers, on which the solfège scale is written. The clef is a
real glyph (FreeSerif U+1D11E), so the sol key reads correctly.

  states drive each of the 8 scale degrees per frame:
    mode  : 'full'  filled note-head (present)
            'empty' hollow note-head (the missing note)
            'ghost' faint placeholder (a slot not yet filled)
    glow  : 0..1 gold ring behind a lit head

  staff.glows_into(a, vis, glows, modes)   # add lit-head glows to the float buffer
  staff.draw(im, vis, modes, glows)        # draw lines, clef, C, heads, stems, lyrics
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SCX = 0.50 * W; SW = 0.70 * W; SY = 0.315 * H; LG = 25.0
SLX = SCX - SW / 2; SRX = SCX + SW / 2
NX0, NX1 = SLX + 0.255 * SW, SRX - 0.045 * SW      # note column start / end (after clef+C)
# C major on a treble staff, head y measured in LG from the middle line (B4 = 0):
YSTEP = [3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0, -0.5]  # C4(ledger) D4 E4 F4 G4 A4 B4 C5
SCALE = [60, 62, 64, 65, 67, 69, 71, 72]
NAMES = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Ti", "Do"]

STAFF_COL = (206, 196, 178); NOTE_COL = (236, 226, 205)
INKGOLD = (255, 214, 150); GHOST = (150, 145, 156)

_DEJA = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_SER = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
_FREESERIF = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
def _f(p, s): return ImageFont.truetype(p, s) if os.path.exists(p) else ImageFont.load_default()
SOLF = _f(_DEJA, 27); CFONT = _f(_SER, int(2.7 * LG))


def note_xy(i):
    return NX0 + (NX1 - NX0) * i / 7.0, SY + YSTEP[i] * LG


def _build_clef():
    """Render the treble-clef glyph and seat its belly on the G line (SY + LG)."""
    big = _f(_FREESERIF, 300)
    tmp = Image.new("RGBA", (600, 900), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((150, 120), "\U0001D11E", font=big, fill=STAFF_COL + (255,))
    g = tmp.crop(tmp.getbbox())
    target_h = int(7.4 * LG)
    w, h = g.size
    return g.resize((max(1, int(w * target_h / h)), target_h), Image.LANCZOS)
_CLEF = _build_clef()
_CLEF_BELLY = 0.66          # belly sits ~66% down the glyph -> align to the G line


def glows_into(a, vis, glows, modes):
    if vis < 0.02: return
    from math import isnan
    for i in range(8):
        if modes[i] == "ghost": continue
        lv = glows[i]
        if lv <= 0.02: continue
        x, y = note_xy(i)
        _glow(a, x, y, 12 + 12 * lv, INKGOLD, (0.25 + 0.95 * lv) * vis)


def _glow(a, cx, cy, rad, color, alpha):
    cx, cy = float(cx), float(cy)
    x0 = max(0, int(cx - 3 * rad)); x1 = min(W, int(cx + 3 * rad))
    y0 = max(0, int(cy - 3 * rad)); y1 = min(H, int(cy + 3 * rad))
    if x1 <= x0 or y1 <= y0: return
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (xg - cx) ** 2 + (yg - cy) ** 2
    a[y0:y1, x0:x1] += (np.exp(-d2 / (2 * rad ** 2)) * alpha)[..., None] * np.array(color, np.float32)
    disc = np.clip(1 - np.sqrt(d2) / (rad * 0.32), 0, 1) ** 0.7 * alpha
    a[y0:y1, x0:x1] += disc[..., None] * np.array(color, np.float32)


def draw(im, vis, modes, glows, yshift_max=26):
    if vis < 0.02: return
    yshift = int((1 - vis) * yshift_max)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for idx, k in enumerate((-2, -1, 0, 1, 2)):       # five staff lines, writing in L→R
        yy = SY + k * LG
        wp = min(1.0, max(0.0, vis * 1.7 - 0.09 * idx))
        wp = wp * wp * (3 - 2 * wp)
        if wp <= 0.01: continue
        d.line([(SLX, yy), (SLX + (SRX - SLX) * wp, yy)], fill=STAFF_COL + (int(150 * vis),), width=2)
    clef = _CLEF                                       # the sol key
    cw, ch = clef.size
    if vis < 0.995:
        al = clef.getchannel("A").point(lambda v: int(v * vis)); clef = clef.copy(); clef.putalpha(al)
    ov.alpha_composite(clef, (int(SLX + 0.085 * SW - cw / 2), int(SY + LG - _CLEF_BELLY * ch)))
    d.text((SLX + 0.175 * SW, SY - 1.55 * LG), "C", font=CFONT, fill=STAFF_COL + (int(185 * vis),))
    for i in range(8):
        x, y = note_xy(i); mode = modes[i]; lv = glows[i]
        nv = min(1.0, max(0.0, vis * 1.9 - 0.10 * i))   # notes appear staggered, L→R
        if nv <= 0.01: continue
        rx, ry = 0.62 * LG, 0.46 * LG
        if mode == "ghost":                            # faint slot, not yet filled
            d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=GHOST + (int(90 * nv),), width=2)
            lc = GHOST + (int(110 * nv),)
        elif mode == "empty":                          # missing note (hollow)
            d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=(180, 172, 184, int((70 + 120 * lv) * nv)), width=3)
            lc = (184, 176, 188, int(150 * nv))
        else:                                          # full note-head
            if i == 0:                                 # ledger line under low Do
                d.line([(x - 1.05 * LG, y), (x + 1.05 * LG, y)], fill=STAFF_COL + (int(150 * nv),), width=2)
            nc = tuple(int(NOTE_COL[j] + (INKGOLD[j] - NOTE_COL[j]) * lv) for j in range(3))
            d.line([(x + rx * 0.85, y - ry * 0.2), (x + rx * 0.85, y - 3.0 * LG)],
                   fill=nc + (int(200 * nv),), width=max(2, int(0.12 * LG)))
            d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=nc + (int((180 + 75 * lv) * nv),))
            lc = (238, 224, 200, int((150 + 100 * lv) * nv))
        bb = d.textbbox((0, 0), NAMES[i], font=SOLF)
        d.text((x - (bb[2] - bb[0]) / 2, SY + 3.7 * LG), NAMES[i], font=SOLF, fill=lc)
    if yshift:
        ov = ov.transform(ov.size, Image.AFFINE, (1, 0, 0, 0, 1, -yshift))
    im.alpha_composite(ov) if im.mode == "RGBA" else im.paste(ov, (0, 0), ov)
