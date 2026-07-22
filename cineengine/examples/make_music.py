"""
Tiny CPU music synthesizer — clean piano + warm pad + bass, smooth reverb.
Key: F major (consonant, calm). No samples, no AI: pure numpy synthesis.

    python make_music.py --duration 22 --out score.wav
"""
import os, sys, argparse, wave
import numpy as np

SR = 44100


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def piano(freq, dur, amp=0.26):
    """Clean, mellow piano-ish tone (in-phase harmonics, smooth decay)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * freq * t)
         + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
         + 0.22 * np.sin(2 * np.pi * 3 * freq * t)
         + 0.10 * np.sin(2 * np.pi * 4 * freq * t))
    decay = np.exp(-t * 3.0)
    atk = np.clip(t / 0.006, 0, 1)
    return (y * decay * atk * amp).astype(np.float32)


def pad(freqs, dur, amp=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.06, 0.06):                      # very slight detune = warmth
            y += np.sin(2 * np.pi * (f + det) * t)
        y += 0.4 * np.sin(2 * np.pi * 2 * f * t)        # gentle octave
    y /= (len(freqs) * 2.4)
    a, r = int(0.5 * SR), int(0.6 * SR)
    e = np.ones(n, np.float32) * 0.9
    e[:a] = np.linspace(0, 1, a)
    if r < n:
        e[-r:] = np.linspace(0.9, 0, r)
    trem = 1 + 0.04 * np.sin(2 * np.pi * 0.5 * t)
    return (y * e * trem * amp).astype(np.float32)


def bass(freq, dur, amp=0.20):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
    a, r = int(0.04 * SR), int(0.4 * SR)
    e = np.ones(n, np.float32) * 0.75
    e[:a] = np.linspace(0, 1, a)
    if r < n:
        e[-r:] = np.linspace(0.75, 0, r)
    return (y * e * amp).astype(np.float32)


def reverb(x):
    """Smooth, dense taps (no metallic comb)."""
    out = x.copy()
    g = 0.42
    for i in range(1, 10):
        d = int((0.021 * i + 0.003) * SR)
        if d < len(x):
            out[d:] += x[:-d] * (g * (0.72 ** i))
    return out


def add(buf, sig, at):
    i = int(at * SR); j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j - i]


def compose(duration, mood="warm"):
    np.random.seed(11)
    n = int(duration * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)

    # F major, I–V–vi–IV (F – C – Dm – Bb): warm, resolving, gentle
    # (chord midi notes, bass midi, consonant melody candidates)
    prog = [
        ("F",  [53, 57, 60], 41, [65, 69, 72]),   # F A C
        ("C",  [48, 52, 55], 48, [67, 72, 76]),   # C E G
        ("Dm", [50, 53, 57], 50, [65, 69, 74]),   # D F A
        ("Bb", [46, 50, 53], 46, [65, 70, 74]),   # Bb D F
    ]
    seq = prog * max(1, round(duration / (len(prog) * 2.8)))
    step = duration / len(seq)

    for k, (name, notes, broot, mel) in enumerate(seq):
        t0 = k * step
        freqs = [midi(m) for m in notes]
        p = pad(freqs, step + 0.4, amp=0.12 * (0.7 + 0.3 * min(1, k / 3)))
        add(L, p, t0); add(R, np.roll(p, 400), t0)
        b = bass(midi(broot), step + 0.2, amp=0.19)
        add(L, b, t0); add(R, b, t0)
        # sparse, always-consonant melody
        for mi in range(2):
            if np.random.rand() < 0.6:
                note = piano(midi(np.random.choice(mel)), 2.4, amp=0.24)
                at = t0 + mi * step * 0.5 + np.random.uniform(0, 0.12)
                pan = np.random.uniform(0.35, 0.65)
                add(L, note * (1 - pan), at); add(R, note * pan, at)

    L = reverb(L); R = reverb(R)
    mix = np.stack([L, R], 1)
    mix = np.tanh(mix * 1.25)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.85
    fi, fo = int(1.2 * SR), int(2.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


def write_wav(path, mix):
    data = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=22.0)
    ap.add_argument("--out", default="score.wav")
    ap.add_argument("--mood", default="warm")
    a = ap.parse_args()
    write_wav(a.out, compose(a.duration, a.mood))
    print(f"wrote {a.out} ({a.duration}s, F major)")


if __name__ == "__main__":
    main()
