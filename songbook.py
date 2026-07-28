"""
songbook — proper harmony and songs for THE OBSERVER WORLD.

Until now chords were bare stacked triads. This gives them a pianist's hands:
a bass root, an open fifth in the tenor, the colour tones close and high, a gentle
roll so the notes arrive like fingers landing, and velocity shaping so the top voice
sings. It also holds the series' recurring THEME, so every chapter shares a melody.

  chord(d, w, "C",  t)                 # a voiced chord into the dry/wet buses
  chord(d, w, "Am7", t, dur=4, amp=.9)
  progression(d, w, [("C",0),("Am",4)], t0)
  sing(d, MELODY, t0)                  # the theme, over the top
"""
import math
import numpy as np
from make_music import midi, piano, pad, bass

QUAL = {
    "":     [0, 4, 7],          "m":    [0, 3, 7],       "dim":  [0, 3, 6],
    "sus4": [0, 5, 7],          "sus2": [0, 2, 7],       "6":    [0, 4, 7, 9],
    "maj7": [0, 4, 7, 11],      "m7":   [0, 3, 7, 10],   "7":    [0, 4, 7, 10],
    "add9": [0, 4, 7, 14],      "m9":   [0, 3, 7, 10, 14], "maj9": [0, 4, 7, 11, 14],
}
ROOT = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6,
        "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def parse(name):
    """'Am7' -> (9, 'm7')"""
    i = 1
    if len(name) > 1 and name[1] in "#b": i = 2
    return ROOT[name[:i]], name[i:]


def voicing(name, base=60):
    """A pianist's spacing: bass root, open fifth beneath, colour tones close on top."""
    r, q = parse(name)
    ivs = QUAL[q]
    root = base + r
    while root >= base + 12: root -= 12
    low = root - 24                      # the bass
    fifth = root - 12 + 7                # an open fifth in the tenor — the 'thread'
    upper = [root + iv for iv in ivs[1:]]
    upper = [u if u < base + 17 else u - 12 for u in upper]
    return low, [root - 12, fifth], sorted(set(upper))


def chord(d, w, name, t, dur=3.6, amp=1.0, pan=0.5, roll=0.035, base=60, padamp=0.045):
    """Lay a properly voiced chord. d/w are the dry and wet add-functions."""
    low, mid, upper = voicing(name, base)
    d(bass(midi(low), dur * 1.15, 0.055 * amp), t, pan)
    for i, m in enumerate(mid):                       # the hand underneath
        d(piano(midi(m), dur, 0.070 * amp), t + i * roll, pan - 0.05)
    for i, m in enumerate(upper):                     # the colour, and the top voice sings
        top = 1.0 + 0.35 * (i == len(upper) - 1)
        d(piano(midi(m), dur * 0.95, 0.058 * amp * top), t + (len(mid) + i) * roll, pan + 0.05)
    if padamp > 0:
        w(pad([midi(m) for m in ([low + 12] + mid + upper)], dur * 1.1, padamp * amp), t, pan)


def progression(d, w, prog, t0, bar=3.6, **kw):
    """prog = [(chord_name, bar_index), ...]"""
    for (nm, b) in prog:
        chord(d, w, nm, t0 + b * bar, dur=bar, **kw)


# ---------------------------------------------------------------- the theme
# Built from the material the series already owns: the First Song's rising head
# (Do Re Mi Sol) and the Do-Sol thread. Scale degrees, 0 = Do.
DEG = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16]              # major scale, two octaves

# (degree, beats) — 'None' is a rest, which this world takes seriously
THEME = [(0, 1), (2, 1), (4, 2), (7, 2), (4, 1), (2, 1),
         (5, 2), (4, 1), (2, 1), (0, 3), (None, 1),
         (4, 1), (5, 1), (7, 2), (9, 2), (7, 1), (5, 1),
         (4, 2), (2, 1), (0, 1), (0, 4)]
THEME_CHORDS = [("C", 0), ("Am", 1), ("F", 2), ("G", 3),
                ("C", 4), ("F", 5), ("G", 6), ("C", 7)]


def sing(d, mel, t0, beat=0.75, amp=0.11, pan=0.5, base=72, swell=True):
    """Play a melody on top — the voice that carries a song."""
    t = t0
    n = len(mel)
    for i, (deg, beats) in enumerate(mel):
        du = beats * beat
        if deg is not None:
            a = amp * (0.86 + 0.30 * math.sin(math.pi * i / max(1, n - 1)) if swell else 1.0)
            d(piano(midi(base + deg), du + 0.8, a), t, pan)
        t += du
    return t - t0


def song(d, w, t0, bar=3.0, mel=None, prog=None, amp=1.0, pan=0.5):
    """A chord progression with the theme sung over it."""
    progression(d, w, prog or THEME_CHORDS, t0, bar=bar, amp=amp, pan=pan)
    sing(d, mel or THEME, t0 + 0.05, beat=bar / 4.0, amp=0.105 * amp, pan=pan)
