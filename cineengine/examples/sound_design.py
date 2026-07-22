"""
Event-synced sound design for 'Letting Go'.

Sounds are triggered at the exact timestamps of on-screen events:
  - light lifts off + climbs   -> a rising shimmer (pitch glissandos up)
  - stars appear               -> soft twinkles
  - the release (hands open)   -> a warm chime swell
  - the final walk             -> soft footsteps on the walk cadence
...over a gentle ambient music bed. Pure numpy synthesis, muxed with ffmpeg.
"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_music import SR, midi, piano, pad, bass, reverb, write_wav, add, compose

DUR = 22.0
N = int(DUR * SR)


def rising_shimmer(t0, t1, octaves=2.3, amp=0.26):
    dur = t1 - t0
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 200 * 2 ** (t / dur * octaves)                 # glissando up
    phase = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase)
    # airy top that grows as it rises
    air = np.random.randn(n).astype(np.float32)
    air = np.diff(air, prepend=0) * (t / dur)
    y = y * 0.7 + air * 0.4
    env = np.clip(t / (dur * 0.4), 0, 1) * np.clip((dur - t) / 1.5, 0, 1)  # swell in, fade end
    return (y * env * amp).astype(np.float32)


def twinkle(freq, amp=0.16, dur=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.01 * t)
    return (y * np.exp(-t * 7.0) * amp).astype(np.float32)


def chime(dur=3.2, amp=0.2):
    n = int(dur * SR); y = np.zeros(n, np.float32)
    for k, m in enumerate([72, 76, 79, 84]):            # C5 E5 G5 C6, staggered
        f = midi(m); t = np.arange(n) / SR
        tone = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t))
        onset = int(k * 0.18 * SR)
        e = np.zeros(n, np.float32); e[onset:] = np.exp(-np.arange(n - onset) / SR * 1.3)
        y += tone * e
    return (y / 4 * amp).astype(np.float32)


def footstep(amp=0.22, dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    low = np.sin(2 * np.pi * 68 * t) * np.exp(-t * 34)
    click = np.random.randn(n).astype(np.float32) * np.exp(-t * 70)
    return ((low + click * 0.5) * amp).astype(np.float32)


def build():
    # music bed (reduced so the sfx read)
    music = compose(DUR) * 0.55
    L = music[:, 0].copy(); R = music[:, 1].copy()

    def stereo(sig, at, pan=0.5):
        add(L, sig * (1 - pan), at); add(R, sig * pan, at)

    # --- events (timings taken from letting_go.py) ---
    # light rises 5.5 -> 14
    stereo(rising_shimmer(5.5, 14.0), 5.5, pan=0.5)
    # release / hands open ~13.2
    stereo(chime(), 13.2, pan=0.5)
    # stars appear ~10 -> 18: scattered twinkles
    rng = np.random.default_rng(3)
    for at in [10.4, 11.2, 12.1, 12.9, 14.3, 15.2, 16.1, 17.0, 17.8]:
        stereo(twinkle(rng.uniform(1600, 3200)), at, pan=rng.uniform(0.25, 0.75))
    # final walk 19.2 -> 21.8: footsteps on the cadence (~0.52s apart)
    tt = 19.2
    while tt < 21.9:
        stereo(footstep(), tt, pan=0.5)
        tt += 0.52

    L = reverb(L); R = reverb(R)
    mix = np.stack([L, R], axis=1)
    mix = np.tanh(mix * 1.3)
    mix /= (np.max(np.abs(mix)) + 1e-6); mix *= 0.9
    fi = int(1.0 * SR); fo = int(1.8 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return mix


if __name__ == "__main__":
    write_wav("lg_sfx.wav", build())
    print("wrote lg_sfx.wav")
