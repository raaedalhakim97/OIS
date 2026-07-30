#!/usr/bin/env python3
"""
narrate — give every episode a spoken keyword line, in the Observer's voice.

TikTok transcribes video audio and indexes the transcript. Our episodes have no
speech, so they forfeit the platform's strongest text signal. This adds one short
spoken sentence at the top of each video: the searchable question, said out loud.

The world's rule is untouched. The characters still speak only Observian — the voice
here belongs to the **Observer**, the one who watches and names things. So it is
processed to sound like a watcher, not a person: low, unhurried, and set back in the
room with the same reverb the music uses.

The video stream is copied, never re-encoded. Only the audio is re-mixed, so this
costs no render time and no visual quality.

    python3 tools/narrate.py --sample                 # voice options -> one mp3, pick one
    python3 tools/narrate.py --episode ch1_ep8        # one episode
    python3 tools/narrate.py --all                    # every episode with a line
    python3 tools/narrate.py --all --voice deep --at 1.2
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from make_music import SR, reverb                                        # noqa: E402

import imageio_ffmpeg                                                    # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "cineengine", "examples")
PIPE = os.path.join(EX, "pipeline", "episodes.json")

# espeak-ng presets. Lower pitch and a slower rate both help TikTok's transcriber
# and make the voice sound like an observer rather than a narrator on a schedule.
VOICES = {
    "observer": dict(v="en-gb-x-rp", s=136, p=24, g=9, a=195),   # default: RP, low, spaced
    "deep":     dict(v="en-gb",      s=128, p=12, g=11, a=200),  # heavier, slower
    "clear":    dict(v="en-us",      s=150, p=35, g=6,  a=195),  # most intelligible
}

# One line per episode: the searchable question first, then the story's own words.
# Keep them short — under ~5 seconds — so they land before the title card clears.
LINES = {
    "tr1_world":   "Every soul is a musical note. This is the Observer World.",
    "tr2_lessons": "Learn music theory as a story. The scale, the octave, the chords.",
    "tr3_dark":    "Something here cannot make its own sound. So it takes yours.",

    "ch1_prologue": "A keeper of notes. This is where the Observer World begins.",
    "ch1_ep1":  "There is a note between two notes. It is called a semitone.",
    "ch1_ep2":  "When two notes sound together, that distance is called an interval.",
    "ch1_ep4":  "Why do some notes hurt to hear together? That is dissonance.",
    "ch1_ep5":  "Five notes that cannot sound wrong. This is the pentatonic scale.",
    "ch1_ep6":  "Tempo is the speed of music. This world beats at seventy two.",
    "ch1_ep7":  "Do, re, mi, fa, sol, la, ti. This is the solfege scale.",
    "ch1_ep8":  "What is an octave? The same note, in a higher place.",
    "ch1_ep9":  "A whole step, a half step, and the first sharp.",
    "ch1_ep10": "Seven notes on a staff. This is how you read sheet music.",

    "ch2_ep1":  "An echo came back. Something is copying the notes.",
    "ch2_ep2":  "You can follow a note the way you follow a footprint. Listen for the pitch.",
    "ch2_ep3":  "Two names for one sound. These are enharmonic notes.",
    "ch2_ep4":  "On the beat, it lands. Off the beat, nothing. This is the downbeat.",
    "ch2_ep5":  "An elder tells the truth, and every hidden thing is finally named.",
    "ch2_ep6":  "A root and a fifth is a power chord. Add a third and it becomes a triad.",
    "ch2_ep7":  "Seven notes make seven chords. One for every degree of the scale.",
    "ch2_ep8":  "Silence is not the end of music. It is written in. It is a rest.",
}


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def speak(text, voice="observer"):
    """espeak-ng -> float32 mono at SR."""
    p = VOICES[voice]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        raw = f.name
    try:
        run(["espeak-ng", "-v", p["v"], "-s", str(p["s"]), "-p", str(p["p"]),
             "-g", str(p["g"]), "-a", str(p["a"]), "-w", raw, text])
        out = run([FFMPEG, "-v", "error", "-i", raw, "-ac", "1", "-ar", str(SR),
                   "-f", "f32le", "-"]).stdout
    finally:
        os.unlink(raw)
    return np.frombuffer(out, np.float32).copy()


def shape(x, room=0.30):
    """Make it the Observer: trim the mud, soften the edge, set it back in the room."""
    if len(x) == 0:
        return x
    # a gentle 3-point smooth tames espeak's buzzy top without blurring consonants,
    # which the transcriber needs to stay crisp
    x = np.convolve(x, np.array([0.25, 0.5, 0.25], np.float32), "same")
    # high-pass by subtracting a slow moving average — removes rumble under ~90 Hz
    k = max(1, int(SR / 90))
    x = x - np.convolve(x, np.ones(k, np.float32) / k, "same")
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.92
    wet = reverb(x, mix=room)
    x = x + (wet - x) * 0.34                          # a watcher's distance, not a cathedral
    return (x / (np.max(np.abs(x)) + 1e-9) * 0.9).astype(np.float32)


def audio_of(path):
    """Decode a video's audio to (n,2) float32 at SR. Empty if the file is unreadable —
    a truncated mp4 (no moov atom) must not take the whole batch down with it."""
    try:
        out = run([FFMPEG, "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(SR),
                   "-f", "f32le", "-"]).stdout
    except subprocess.CalledProcessError as e:
        why = (e.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        print(f"  ! {os.path.basename(path)}: unreadable — {why[0] if why else 'ffmpeg failed'}")
        return np.zeros((0, 2), np.float32)
    a = np.frombuffer(out, np.float32).copy()
    return a.reshape(-1, 2) if len(a) else np.zeros((0, 2), np.float32)


def video_seconds(path):
    """Duration of the video stream alone. Some episodes carry an audio stream that is
    slightly shorter than the picture; muxing with -shortest would then cut the picture."""
    r = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True).stderr
    for ln in r.splitlines():
        if "Duration:" in ln:
            hh, mm, ss = ln.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(hh) * 3600 + int(mm) * 60 + float(ss)
    return None


def duck(bed, nar, at, amount=0.42, ramp=0.28):
    """Lay the narration over the bed, pulling the music down only while it speaks."""
    n = len(bed)
    i = int(at * SR)
    j = min(n, i + len(nar))
    if i >= n:
        return bed
    env = np.ones(n, np.float32)
    r = max(1, int(ramp * SR))
    lo = 1.0 - amount
    env[i:j] = lo
    fi, fo = max(0, i - r), min(n, j + r)
    env[fi:i] = np.linspace(1.0, lo, i - fi, dtype=np.float32)
    env[j:fo] = np.linspace(lo, 1.0, fo - j, dtype=np.float32)
    out = bed * env[:, None]
    seg = nar[:j - i]
    out[i:j, 0] += seg * 0.85                        # centred, a hair wide
    out[i:j, 1] += seg * 0.85
    peak = np.max(np.abs(out)) + 1e-9
    if peak > 0.995:
        out = out / peak * 0.995
    return out.astype(np.float32)


def process(path, line, voice, at, outdir):
    bed = audio_of(path)
    if len(bed) == 0:
        print(f"  → {os.path.basename(path)} skipped")
        return None
    # hold the bed to the picture's full length, so the mux can never trim the video
    vs = video_seconds(path)
    if vs:
        want = int(round(vs * SR))
        if want > len(bed):
            bed = np.vstack([bed, np.zeros((want - len(bed), 2), np.float32)])
        elif want < len(bed):
            bed = bed[:want]

    nar = shape(speak(line, voice))
    mixed = duck(bed, nar, at)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = f.name
    try:
        run([FFMPEG, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2",
             "-i", "-", wav], input=mixed.tobytes())
        base = os.path.basename(path).replace(".mp4", "_tts.mp4")
        dst = os.path.join(outdir, base)
        run([FFMPEG, "-v", "error", "-y", "-i", path, "-i", wav,
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", dst])
    finally:
        os.unlink(wav)
    print(f"  ✓ {base}   ({len(nar) / SR:.1f}s of speech at {at:.1f}s)")
    return dst


def sample(outdir):
    """One mp3 with the same sentence in every voice, announced, so a voice can be picked."""
    parts = []
    gap = np.zeros(int(0.55 * SR), np.float32)
    for name in VOICES:
        parts.append(shape(speak(f"Voice: {name}.", "clear")) * 0.55)
        parts.append(gap)
        parts.append(shape(speak(LINES["ch1_ep8"], name)))
        parts.append(gap)
    mono = np.concatenate(parts)
    st = np.stack([mono, mono], 1)
    dst = os.path.join(outdir, "tts_voice_sample.mp3")
    run([FFMPEG, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2",
         "-i", "-", "-b:a", "192k", dst], input=st.tobytes())
    print(f"  ✓ {dst}")
    return dst


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true", help="render a voice-comparison mp3")
    p.add_argument("--episode", help="one episode id from episodes.json")
    p.add_argument("--all", action="store_true")
    p.add_argument("--voice", default="observer", choices=list(VOICES))
    p.add_argument("--at", type=float, default=1.0, help="seconds into the video")
    p.add_argument("--outdir", default=os.path.join(EX, "tts"))
    a = p.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    if a.sample:
        sample(a.outdir)
        return

    eps = json.load(open(PIPE))["episodes"]
    todo = [e for e in eps if (a.all or e["id"] == a.episode) and e["id"] in LINES]
    if not todo:
        sys.exit("nothing to do — check --episode against episodes.json ids")

    done = 0
    for e in todo:
        src = os.path.join(ROOT, e["path"])
        if not os.path.exists(src):
            print(f"  ! missing {e['path']}")
            continue
        if process(src, LINES[e["id"]], a.voice, a.at, a.outdir):
            done += 1
    print(f"\n{done}/{len(todo)} narrated into {a.outdir}")


if __name__ == "__main__":
    main()
