"""
subs — turn a spoken line into on-screen captions that actually match the voice.

The captions in this world used to be poetry standing beside the narration: Alan said
one thing and the screen said a shorter, different thing, so words went missing for
anyone reading rather than listening. That is bad for a viewer with the sound off and
bad for search, since TikTok reads on-screen text.

piper's phoneme alignments come back empty for these voice models, so timing is
recovered from the audio instead: find the pauses in the waveform, split the sentence
at its punctuation, and match the two up. Where a chunk boundary lands near a real
pause it snaps to it; otherwise it falls back to weighted duration, with punctuation
carrying extra weight because that is where a reader — and piper — takes a breath.

  chunks = split(text, signal, sr, t0)   -> [(start, end, "two lines of text"), ...]
"""
import re

import numpy as np

MAX_LINE = 30          # characters per line before wrapping
MAX_WORDS = 8          # a caption longer than this is hard to read at a glance


def _phrases(text):
    """Break a sentence where a reader would pause, then again if still too long."""
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]
    out = []
    for p in parts:
        if len(p.split()) <= MAX_WORDS:
            out.append(p); continue
        bits = [b for b in re.split(r"(?<=,)\s+", p) if b]
        for b in bits:
            w = b.split()
            if len(w) <= MAX_WORDS:
                out.append(b)
            else:                                   # still long: halve on a word boundary
                h = len(w) // 2
                out += [" ".join(w[:h]), " ".join(w[h:])]
    return out


def _weight(s):
    """Roughly how long this will take to say: letters, plus a beat for each pause."""
    return len(s) + 9.0 * s.count(",") + 16.0 * sum(s.count(c) for c in ".!?")


def _gaps(sig, sr, floor=0.055, min_gap=0.11):
    """Where the voice actually stops, in seconds from the start of the line."""
    if len(sig) == 0:
        return []
    win = max(1, int(0.01 * sr))
    n = len(sig) // win
    if n < 3:
        return []
    env = np.abs(sig[:n * win]).reshape(n, win).max(1)
    env = env / (env.max() + 1e-9)
    quiet = env < floor
    out, run = [], 0
    for i, q in enumerate(quiet):
        if q:
            run += 1
        else:
            if run * 0.01 >= min_gap and i > 2:
                out.append((i - run * 0.5) * 0.01)   # the middle of the pause
            run = 0
    return out


def wrap(s):
    """Two short lines read better on a phone than one long one."""
    w = s.split()
    if len(" ".join(w)) <= MAX_LINE:
        return " ".join(w)
    best, cut = None, len(w) // 2
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        score = abs(len(a) - len(b)) + (0 if max(len(a), len(b)) <= MAX_LINE else 40)
        if best is None or score < best:
            best, cut = score, i
    return " ".join(w[:cut]) + "\n" + " ".join(w[cut:])


def split(text, sig, sr, t0, lead=0.06, tail=0.30):
    """[(start, end, text)] for one spoken line, timed against its own audio."""
    dur = len(sig) / sr
    parts = _phrases(text)
    if not parts:
        return []
    if len(parts) == 1:
        return [(t0 + lead, t0 + dur + tail, wrap(parts[0]))]

    wts = np.array([_weight(p) for p in parts], np.float64)
    edges = np.concatenate([[0.0], np.cumsum(wts / wts.sum()) * dur])

    # snap interior boundaries onto real pauses when one is close by
    gaps = _gaps(sig, sr)
    for i in range(1, len(edges) - 1):
        near = [g for g in gaps if abs(g - edges[i]) < 0.34]
        if near:
            edges[i] = min(near, key=lambda g: abs(g - edges[i]))
    edges = np.maximum.accumulate(edges)

    out = []
    for i, p in enumerate(parts):
        s = t0 + edges[i] + (lead if i == 0 else 0.02)
        e = t0 + edges[i + 1] + (tail if i == len(parts) - 1 else 0.06)
        if e - s < 0.55:                              # never flash a caption
            e = s + 0.55
        out.append((s, e, wrap(p)))
    return out


def build(lines, sigs, sr, extra=()):
    """All spoken lines -> one caption table, with any non-spoken story captions merged.

    lines: [(t, text)]   sigs: [(t, signal)]   extra: [(s, e, text)] shown as-is
    """
    caps = []
    for (t, text), (_t2, sig) in zip(lines, sigs):
        caps += split(text, sig, sr, t)
    caps += [(s, e, txt) for (s, e, txt) in extra]
    caps.sort(key=lambda c: c[0])
    # a caption must never outlive the next one
    for i in range(len(caps) - 1):
        s, e, txt = caps[i]
        if e > caps[i + 1][0] - 0.04:
            caps[i] = (s, max(s + 0.5, caps[i + 1][0] - 0.04), txt)
    return caps
