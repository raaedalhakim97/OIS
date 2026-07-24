"""
Tiny CPU music synthesizer — clean piano + warm pad + bass, smooth reverb.
Key: F major (consonant, calm). No samples, no AI: pure numpy synthesis.

    python make_music.py --duration 22 --out score.wav
"""
import os, sys, argparse, wave
import numpy as np
from scipy.signal import iirpeak, butter, lfilter

SR = 44100


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def piano(freq, dur, amp=0.26):
    """A warm FELT piano — string inharmonicity, per-partial decay (highs die first),
    a soft hammer transient, and a felt-muted top. Reads as a real, tender piano."""
    n = int(dur * SR); t = np.arange(n) / SR
    B = 0.00042                                          # string inharmonicity
    y = np.zeros(n, np.float32)
    for k, ka in ((1, 1.0), (2, 0.42), (3, 0.20), (4, 0.11), (5, 0.06), (6, 0.035)):
        fk = k * freq * np.sqrt(1.0 + B * k * k)
        y += ka * np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.9 + 0.55 * k))   # higher partials fade faster
    y += 0.35 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 0.8)                # long fundamental tail
    hammer = np.random.randn(n).astype(np.float32) * np.exp(-t * 150) * 0.05   # soft felt hammer
    atk = np.clip(t / 0.005, 0, 1) ** 0.8
    y = (y * 0.85 + hammer) * atk * amp
    return np.convolve(y, np.ones(3) / 3, "same").astype(np.float32)           # felt = softened highs


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


def _violin_body(x):
    """A real violin-body resonance: a bank of scipy resonant peaks (formants) that
    give the woody/nasal string colour synthesis can't fake with harmonics alone."""
    out = np.zeros_like(x)
    for fc, Q, g in [(280, 2.5, 1.0), (460, 3, 0.9), (820, 4, 0.7),
                     (1300, 5, 0.55), (2400, 7, 0.7), (3200, 9, 0.5)]:
        b, a = iirpeak(fc / (SR / 2), Q)
        out += g * lfilter(b, a, x)
    return out


def violin(freq, dur, amp=0.16, vib=1.0, tremolo=0.0):
    """Bowed string = a band-limited sawtooth (physically the string's bridge motion) +
    bow-hair noise, run through a real violin-body formant filter bank (scipy). Pitch
    jitter + fade-in vibrato keep it from sounding like an organ. High & trembling =
    the threat; on chord tones = the threat reconciled."""
    freq = max(20.0, float(freq))
    n = int(dur * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(int(freq * 7) % 99991)
    vd = 0.009 * vib * np.clip((t - 0.12) / 0.35, 0, 1)
    jit = 0.0013 * np.convolve(rng.standard_normal(n).astype(np.float32), np.ones(40) / 40, "same")
    ph = 2 * np.pi * freq * np.cumsum(1 + vd * np.sin(2 * np.pi * 5.6 * t) + jit) / SR
    saw = np.zeros(n, np.float32)
    for k in range(1, min(40, int((SR / 2) / freq))):
        saw += np.sin(k * ph + rng.uniform(0, 2 * np.pi)) / k
    saw /= 2.5
    nz = rng.standard_normal(n).astype(np.float32)
    nz = nz - np.convolve(nz, np.ones(20) / 20, "same")
    y = _violin_body(saw + 0.10 * nz) * 0.9 + saw * 0.25
    atk, rel = int(0.07 * SR), int(0.45 * SR)
    e = np.ones(n, np.float32) * 0.85
    e[:atk] = np.linspace(0, 1, atk) ** 0.6
    if rel < n: e[-rel:] = np.linspace(0.85, 0, rel)
    if tremolo > 0:
        e = e * (1 - tremolo * 0.4 * (0.5 + 0.5 * np.sin(2 * np.pi * 6.2 * t)))
    return (y * e * amp).astype(np.float32)


def softkick(amp=0.26, dur=0.5):
    """A deep, soft pulse — low sine with a quick pitch drop, butter-low-passed so there
    is no click and no snare. The breathing beat."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 80 * np.exp(-t * 10) + 42
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    b, a = butter(2, 120 / (SR / 2)); y = lfilter(b, a, y)
    return (y / (np.max(np.abs(y)) + 1e-9) * amp).astype(np.float32)


def heartbeat(amp=0.16):
    """A soft, warm 'lub-dub' — the breathing pulse that replaces any hard beat.
    Round, low, heavily softened; sparse by design. Never a clicky kick."""
    def thump(f0, a, dur=0.34):
        m = int(dur * SR); t = np.arange(m) / SR
        f = f0 * np.exp(-t * 15) + 36
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8) * a
        return np.convolve(y, np.ones(60) / 60, "same").astype(np.float32)   # lowpass = soft
    out = np.zeros(int(0.62 * SR), np.float32)
    lub = thump(96, 1.0); dub = thump(78, 0.7)
    out[:len(lub)] += lub
    o = int(0.26 * SR); out[o:o + len(dub)] += dub[:len(out) - o]
    out /= (np.max(np.abs(out)) + 1e-9)
    return (out * amp).astype(np.float32)


def brush(amp=0.06, dur=0.18):
    """A soft brushed shaker — airy, high-quality, barely there."""
    m = int(dur * SR); t = np.arange(m) / SR
    nz = np.convolve(np.random.randn(m).astype(np.float32), np.ones(8) / 8, "same")
    return (nz * (np.clip(t / 0.02, 0, 1) * np.exp(-t * 16)) * amp).astype(np.float32)


def reverb(x, mix=1.0):
    """A lush hall — diffuse early reflections + a long, HF-damped tail. Gives the
    sense of a real room that a dry synth lacks."""
    x = x.astype(np.float32)
    out = x.copy()
    for d, g in ((0.007, 0.6), (0.013, 0.5), (0.019, 0.42), (0.029, 0.34), (0.041, 0.27)):
        dd = int(d * SR)
        if dd < len(x): out[dd:] += x[:-dd] * (g * 0.5 * mix)          # early reflections
    tail = np.zeros_like(x)
    for i in range(1, 16):                                            # long damped tail
        d = int((0.033 * i + 0.006) * SR)
        if d >= len(x): break
        w = 3 + i                                                     # progressive HF damping
        damped = np.convolve(x[:-d], np.ones(w) / w, "same")
        tail[d:] += damped * (0.55 * (0.80 ** i) * mix)
    return out + tail


def master(stereo, level=0.9, width=1.22, warmth=1.1):
    """Finishing chain: gentle tape warmth, stereo width, soft limiting — the polish
    that separates a demo from a record. Apply once to the final stereo mix."""
    s = np.asarray(stereo, np.float32)
    s = np.tanh(s * warmth) / np.tanh(warmth)                         # soft saturation = warmth
    L, R = s[:, 0], s[:, 1]
    mid = (L + R) * 0.5; side = (L - R) * 0.5 * width                 # mid/side widen
    s = np.stack([mid + side, mid - side], 1)
    s /= (np.max(np.abs(s)) + 1e-9)
    s = np.tanh(s * 1.05) * level                                     # soft limit
    return s.astype(np.float32)


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
