"""A first conversation in Observian — two keepers meet. ~48s audio demo.
Keeper A: mid voice, panned left. Elder Keeper B: deep voice (-12), panned right.
"""
import numpy as np
from make_music import SR, midi, piano, pad, bass, reverb, master, add, write_wav
from observian import say, word_melody

DUR = 48.0
n = int(DUR * SR)
dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
def d(s, at, pan=0.5): add(dL, s * (1 - pan), at); add(dR, s * pan, at)
def w(s, at, pan=0.5): add(wL, s * (1 - pan), at); add(wR, s * pan, at)

w(pad([midi(48), midi(55), midi(60)], DUR - 4, 0.035), 1, 0.5)

A = dict(register=0, pan=0.36)
B = dict(register=-12, pan=0.64)

say(d, "hello", 2.0, style="calm", **A)                    # Do Mi Sol — hello
say(d, "hello", 5.2, style="calm", **B)                    # the elder answers, deep
say(d, "how are you", 8.6, style="calm", **A)              # Fa Mi Sol
say(d, "i am well", 11.8, style="confident", **B)          # Do Sol Do
say(d, "we are connected", 15.4, style="calm", **A)        # Do+Mi+Sol as one chord
say(d, "come with me", 19.0, style="urgent", register=12, pan=0.36)   # urgency: high & fast
say(d, "danger", 22.0, style="fear", register=12, pan=0.64)           # fear: broken rhythm
say(d, "i am well", 26.0, style="calm", register=-12, color="minor", pan=0.5)  # the same words, sad
# dissonance (conflict) resolving into understanding
d(piano(midi(65), 2.2, 0.10), 30.6, 0.45); d(piano(midi(71), 2.2, 0.10), 30.62, 0.55)
d(piano(midi(60), 3.0, 0.11), 33.2, 0.45); d(piano(midi(67), 3.0, 0.11), 33.22, 0.55)
d(piano(midi(72), 3.0, 0.07), 33.24, 0.5)
say(d, word_melody("HELLO"), 37.0, style="confident", pan=0.5)        # a human word, translated
say(d, "farewell", 41.0, style="calm", **B)                # Sol Re Ti
say(d, "home", 44.0, style="calm", **A)                    # Sol Do
w(bass(midi(36), 8, 0.05), 41.0, 0.5)

dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
mix = master(dry * 0.92 + wet)
fi, fo = int(0.4 * SR), int(3 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
write_wav("observian_demo.wav", mix)
print("wav done")

import imageio_ffmpeg, subprocess
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-y", "-i", "observian_demo.wav", "-c:a", "aac", "-b:a", "160k",
                "observian_demo.m4a"], check=True, capture_output=True)
print("Done -> observian_demo.m4a")
