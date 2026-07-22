"""
Tiny CPU music synthesizer — ambient pad + soft piano + bass, light reverb.
Writes a WAV you can mux under a video. No AI, no samples: pure numpy synthesis.

    python make_music.py --duration 22 --out score.wav --mood warm
"""
import os, sys, argparse, wave, struct
import numpy as np

SR = 44100


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def env_adsr(n, a, d, s, r, sus=0.7):
    e = np.ones(n, np.float32) * sus
    ai = int(a * SR); di = int(d * SR); ri = int(r * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if di: e[ai:ai + di] = np.linspace(1, sus, di)
    if ri: e[-ri:] = np.linspace(e[-ri] if n - ri > 0 else sus, 0, ri)
    return e


def piano(freq, dur, amp=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # inharmonic partials with fast attack + long exp decay
    parts = [(1, 1.0), (2, 0.5), (3, 0.28), (4, 0.14), (5, 0.07), (6, 0.04)]
    y = np.zeros(n, np.float32)
    for h, a in parts:
        y += a * np.sin(2 * np.pi * freq * h * t + np.random.uniform(0, 6.28))
    decay = np.exp(-t * 2.6)
    atk = np.clip(t / 0.008, 0, 1)
    return (y * decay * atk * amp).astype(np.float32)


def pad(freqs, dur, amp=0.14):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.15, 0.0, 0.15):        # slight detune = warmth
            y += np.sin(2 * np.pi * (f + det) * t)
        y += 0.5 * np.sin(2 * np.pi * f * 2 * t)   # octave shimmer
    y /= (len(freqs) * 3.5)
    # slow attack/release + gentle tremolo
    e = env_adsr(n, 0.5, 0.3, 0.85, 0.6, sus=0.85)
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.7 * t)
    return (y * e * trem * amp).astype(np.float32)


def bass(freq, dur, amp=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    e = env_adsr(n, 0.05, 0.2, 0.7, 0.4, sus=0.7)
    return (y * e * amp).astype(np.float32)


def reverb(x, taps=((0.045, 0.35), (0.09, 0.22), (0.17, 0.14), (0.27, 0.08))):
    out = x.copy()
    for dt, g in taps:
        d = int(dt * SR)
        if d < len(x):
            out[d:] += x[:-d] * g
    return out


def add(buf, sig, at):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j - i]


def compose(duration, mood="warm"):
    np.random.seed(7)
    n = int(duration * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)

    # A-minor family progression (vi IV I V) — bittersweet, resolving
    # chords as midi note sets (mid octave)
    prog = [
        ("Am", [57, 60, 64], 45),   # A C E, bass A2(45)
        ("F",  [53, 57, 60], 41),   # F A C, bass F2
        ("C",  [48, 52, 55], 48),   # C E G, bass C3
        ("G",  [55, 59, 62], 43),   # G B D, bass G2
    ]
    seq = prog + prog                     # 8 chords
    step = duration / len(seq)
    melody_pool = [72, 74, 76, 79, 81]    # soft high notes (C5..A5)

    for k, (name, notes, broot) in enumerate(seq):
        t0 = k * step
        freqs = [midi(m) for m in notes]
        p = pad(freqs, step + 0.4, amp=0.13 * (0.6 + 0.4 * min(1, k / 3)))
        add(L, p, t0); add(R, np.roll(p, 300), t0)          # tiny stereo spread
        b = bass(midi(broot), step + 0.2, amp=0.2)
        add(L, b, t0); add(R, b, t0)
        # sparse melody: 1–2 notes per chord, drawn from chord+scale
        for mi in range(2):
            if np.random.rand() < 0.75:
                nm = np.random.choice(melody_pool)
                note = piano(midi(nm), 2.2, amp=0.26)
                at = t0 + mi * step * 0.5 + np.random.uniform(0, 0.15)
                pan = np.random.uniform(0.3, 0.7)
                add(L, note * (1 - pan), at); add(R, note * pan, at)

    L = reverb(L); R = reverb(R)
    mix = np.stack([L, R], axis=1)
    # gentle master: soft-clip, normalize, fade in/out
    mix = np.tanh(mix * 1.4)
    mix /= (np.max(np.abs(mix)) + 1e-6)
    mix *= 0.85
    fi = int(1.2 * SR); fo = int(2.0 * SR)
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
    print(f"wrote {a.out} ({a.duration}s)")


if __name__ == "__main__":
    main()
