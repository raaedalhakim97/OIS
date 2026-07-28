"""A demo of the new harmony engine: bare triads (old) vs voiced chords (new),
then the series THEME sung over its progression, then a richer colour palette."""
import numpy as np
from make_music import SR, midi, piano, pad, bass, softkick, reverb, master, add, write_wav
import songbook as sb

DUR = 76.0
n = int(DUR * SR)
dL = np.zeros(n, np.float32); dR = np.zeros(n, np.float32)
wL = np.zeros(n, np.float32); wR = np.zeros(n, np.float32)
def d(s, at, pan=0.5): add(dL, s*(1-pan), at); add(dR, s*pan, at)
def w(s, at, pan=0.5): add(wL, s*(1-pan), at); add(wR, s*pan, at)

# 1) OLD: bare stacked triads, the way every episode has done it so far
for i, ch in enumerate([[60,64,67],[57,60,64],[65,69,72],[67,71,74]]):
    for m in ch: d(piano(midi(m), 3.0, 0.115), 2.0 + i*3.4, 0.5)

# 2) NEW: the same four chords, properly voiced
for i, nm in enumerate(["C","Am","F","G"]):
    sb.chord(d, w, nm, 18.0 + i*3.6)

# 3) THE THEME, sung over its progression
sb.song(d, w, 34.0, bar=3.0)

# 4) colour: sevenths and ninths
for i, nm in enumerate(["Cmaj9","Am9","Fmaj7","G7","C6"]):
    sb.chord(d, w, nm, 60.0 + i*3.0, dur=3.0)

dry = np.stack([reverb(dL, mix=0.45), reverb(dR, mix=0.45)], 1)
wet = np.stack([reverb(wL, mix=1.0), reverb(wR, mix=1.0)], 1)
mix = master(dry*0.92 + wet)
fi, fo = int(0.4*SR), int(3*SR)
mix[:fi] *= np.linspace(0,1,fi)[:,None]; mix[-fo:] *= np.linspace(1,0,fo)[:,None]
write_wav("songbook_demo.wav", mix)
import imageio_ffmpeg, subprocess
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,"-y","-i","songbook_demo.wav","-codec:a","libmp3lame","-b:a","192k",
                "observer_songbook_demo.mp3"], check=True, capture_output=True)
print("Done -> observer_songbook_demo.mp3")
