"""
CHAPTER II · Episode 1 — "The Echo That Came Back"  (conversation demo, ~1:36)
A whole story scene spoken ONLY in Observian. Captions (printed below) carry the
meaning; nobody speaks a word. The Keeper sings the First Song to the horizon —
and the echo returns with one note flattened. He questions the dark, and the dark
answers the way it always will: with a rest.

Voices:  Keeper  = mid register, left      Echo   = high, whispered, far (wet bus)
         Elder   = -12, right              Silence = no notes at all
"""
import numpy as np
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
from observian import say

DUR = 96.0
n = int(DUR * SR)
dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
def d(s, at, pan=0.5): add(dL, s * (1 - pan), at); add(dR, s * pan, at)
def w(s, at, pan=0.5): add(wL, s * (1 - pan), at); add(wR, s * pan, at)

KEEPER = dict(register=0, pan=0.38)
ELDER = dict(register=-12, pan=0.64)

SCRIPT = []   # (t, who, observian, caption)
def line(t, who, phrase, caption, fn=None, **kw):
    (fn or d).__call__  # noqa
    say(fn or d, phrase, t, **kw)
    SCRIPT.append((t, who, phrase, caption))
def beat(t, who, caption):
    SCRIPT.append((t, who, "—  (rest)  —", caption))

# ---------------- the world at night, before anything is wrong ----------------
w(pad([midi(48), midi(55), midi(60)], 26, 0.036), 1.0, 0.5)
for t in np.arange(2.5, 9, 1.6): d(softkick(0.07), t, 0.5)

# 1. The Keeper sings the First Song out to the horizon — proud, confident.
line(9.0, "KEEPER", "the song has begun", "the song has begun.",
     style="confident", **KEEPER)

# 2. The echo returns — the same melody, but one note has fallen. (minor, whispered, far)
say(w, "the song has begun", 15.5, style="whisper", register=12, color="minor", pan=0.72)
SCRIPT.append((15.5, "ECHO", "Do Re Mi Sol  (fallen)", "…the song has begun."))
beat(19.5, "", "he had sung it. and it came back wrong.")

# 3. Something is wrong. (low, slow)
w(pad([midi(45), midi(52), midi(57), midi(60)], 20, 0.04), 21.0, 0.5)   # Am — unease
line(22.0, "KEEPER", "something is wrong", "something is wrong.",
     style="calm", register=-12, pan=0.42)

# 4. He questions the dark.
line(28.0, "KEEPER", "who are you", "who are you?", style="urgent", **KEEPER)

# 5. THE SILENCE ANSWERS — with a rest. Only a drone that swells where a voice
#    should be. This is the antagonist speaking.
w(bass(midi(31), 9, 0.055), 32.0, 0.5)
beat(32.0, "THE SILENCE", "(no answer. and the no-answer is the answer.)")

# 6. He asks again — higher, faster, afraid.
line(41.0, "KEEPER", "who are you", "who are you?!", style="urgent", register=12, pan=0.38)
# the dark's single voice: a note that belongs to no scale (a tritone, far below)
d(piano(midi(42), 5.0, 0.075), 45.0, 0.5); w(bass(midi(30), 7, 0.05), 45.0, 0.5)
beat(45.0, "THE SILENCE", "something answered. it was not a note.")

# 7. He calls for help — broken rhythm, high.
line(50.5, "KEEPER", "danger", "danger.", style="fear", register=12, pan=0.38)
line(54.0, "KEEPER", "i am afraid", "i am afraid.", style="fear", register=0, pan=0.40)

# 8. The Elder answers from far away — deep, steady, unhurried.
w(pad([midi(41), midi(48), midi(57)], 18, 0.042), 58.0, 0.5)            # F — shelter
line(59.0, "ELDER", "i hear you", "i hear you.", style="calm", **ELDER)

# 9. The Elder names it — the First Song's phrase with harmony turned to doubt.
line(65.0, "ELDER", "the song is broken", "the song is broken.",
     style="calm", **ELDER)
beat(70.0, "", "one sound had changed. and with it, everything.")

# 10. Come with me.
line(72.0, "KEEPER", "come with me", "come with me.", style="urgent", **KEEPER)

# 11. We are connected — a chord: one complete thought, both voices.
w(pad([midi(36), midi(48), midi(55), midi(60)], 12, 0.05), 76.5, 0.5)
line(77.0, "ELDER", "we are connected", "we are connected.",
     style="confident", register=-12, pan=0.5)

# 12. They move. (walking pulse under both voices)
for t in np.arange(80.5, 88, 1.5): d(softkick(0.08), t, 0.5)
line(81.0, "KEEPER", "listen", "listen —", style="calm", **KEEPER)

# 13. And the fallen note rings alone, unresolved. The hook.
d(piano(midi(68), 6.0, 0.12), 86.0, 0.5)          # the flattened note, out of the key
w(bass(midi(30), 8, 0.05), 86.0, 0.5)
beat(86.0, "", "somewhere, the fallen note was still ringing.")

dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
mix = master(dry * 0.92 + wet)
fi, fo = int(0.4 * SR), int(4 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
write_wav("ch2_scene.wav", mix)

import imageio_ffmpeg, subprocess
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-y", "-i", "ch2_scene.wav", "-codec:a", "libmp3lame", "-b:a", "192k",
                "ch2_the_echo_that_came_back.mp3"], check=True, capture_output=True)

print(f"{'TIME':>6}  {'WHO':<12} {'OBSERVIAN':<26} CAPTION")
for (t, who, ph, cap) in sorted(SCRIPT):
    print(f"{t:6.1f}  {who:<12} {ph:<26} {cap}")
print("\nDone -> ch2_the_echo_that_came_back.mp3")
