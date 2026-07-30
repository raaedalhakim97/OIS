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
    python3 tools/narrate.py --all --voice ryan --at 1.2
"""
import argparse
import ast
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

# Neural voices (piper). These are real recorded-voice models, not formant synthesis —
# espeak sounds like a machine reading, which is wrong for a watcher. length_scale > 1
# slows delivery, which suits the Observer and helps TikTok's transcriber.
#
# The models live on GitHub releases rather than HuggingFace on purpose: HF is blocked by
# the render container's egress policy, and these mirrors are not.
REL = "https://github.com/rhasspy/piper/releases/download/v0.0.2"
PIPER = {
    "alan":  ("en-gb-alan-low.onnx",     f"{REL}/voice-en-gb-alan-low.tar.gz",     1.18),
    "ryan":  ("en-us-ryan-high.onnx",    f"{REL}/voice-en-us-ryan-high.tar.gz",    1.15),
    "amy":   ("en-us-amy-low.onnx",      f"{REL}/voice-en-us-amy-low.tar.gz",      1.15),
    "libri": ("en-us-libritts-high.onnx", f"{REL}/voice-en-us-libritts-high.tar.gz", 1.12),
}

# espeak-ng fallbacks, kept only for machines with no model cache and no network.
ESPEAK = {
    "espeak-gb": dict(v="en-gb-x-rp", s=136, p=24, g=9, a=195),
    "espeak-us": dict(v="en-us",      s=150, p=35, g=6, a=195),
}
VOICES = list(PIPER) + list(ESPEAK)
VOICE_DIR = os.environ.get("OBSERVER_VOICES",
                           os.path.join(os.path.expanduser("~"), ".cache", "observer-voices"))

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
    "ch2_ep8":  "What is the harmonic series? Every note has other notes inside it.",
    "ch2_ep10": "Silence is not the end of music. It is written in. It is a rest.",
}


# Which module rendered which episode. Matched on title text and confirmed against each
# video's duration; ch1_ep5 was settled by reading the caption off an actual frame, since
# two modules shared both a title and a duration.
#
# ch1_ep4's script is 143s while its rendered video is 122.4s — that video predates the
# current script, so its final captions have no picture to sit under and are dropped.
# ch1_ep1 and the trailers have no CAPS table, so they get the keyword line only.
MODULES = {
    "ch1_prologue": "ep3_keeper.py",
    "ch1_ep2":  "ep2_conversation.py",
    "ch1_ep4":  "ep4_thehollow.py",
    "ch1_ep5":  "ep5_planet.py",
    "ch1_ep6":  "ep6_heartbeat.py",
    "ch1_ep7":  "ep7_otherkeeper.py",
    "ch1_ep8":  "ep8_firstnote.py",
    "ch1_ep9":  "ep9_secondnote.py",
    "ch1_ep10": "ep10_firstsong.py",
    "ch2_ep1":  "ep11_echo.py",
    "ch2_ep2":  "ep12_coldtrail.py",
    "ch2_ep3":  "ep13_betweenstone.py",
    "ch2_ep4":  "ep14_drumbelow.py",
    "ch2_ep5":  "ep15_elderstruth.py",
    "ch2_ep6":  "ep16_chordofthree.py",
    "ch2_ep7":  "ep17_sevenways.py",
    "ch2_ep10": "ep18_loudestquiet.py",
}

# ch2_ep8 is deliberately absent above. It bakes its own narration in ep19_voiceinside.py,
# because the Keeper reacts to a specific line at a specific moment; adding a second pass
# here would double the voice.


# ── the trailers: Alan and the world, taking turns ───────────────────────────────
# Alan does not narrate over the top of this world; he talks with it. He says a line,
# and a note answers him in Observian — the language the characters actually speak. So
# the trailer teaches the audience the premise by demonstrating it: words, then music,
# answering each other. ("say", text) is Alan; ("obs", phrase, style) is the reply.
#
# Times are placed in the gaps between the on-screen captions of each trailer, so a
# reply lands while its caption is still up.
DIALOG = {
    "tr1_world": [
        (0.6,  "say", "Every soul is a note."),
        (2.6,  "obs", "hello", "calm", 0),        # answers inside the first caption
        (5.5,  "say", "Some are bright."),
        (7.3,  "obs", "i am here", "confident", 12),
        (9.0,  "say", "Some are fading."),
        (10.7, "obs", "i am afraid", "fear", -12),
        (13.1, "say", "No note completes itself."),
        (15.3, "obs", "help us", "calm", 0),
        (17.5, "say", "So one walks the world, helping them harmonise."),
        (21.1, "obs", "we are connected", "calm", 0),
    ],
    "tr2_lessons": [
        (0.5,  "say", "This is a music lesson."),
        (2.9,  "say", "You won't notice."),
        (5.0,  "say", "The scale."),
        (6.0,  "obs", "the song has begun", "confident", 0),
        (8.4,  "say", "The octave."),
        (9.8,  "obs", "the same", "calm", 12),
        (11.8, "say", "Half steps."),
        (13.2, "obs", "closer", "urgent", 0),
        (15.2, "say", "The beat."),
        (16.6, "obs", "now", "confident", 0),
        (18.6, "say", "Chords."),
        (20.0, "obs", "we are connected", "confident", 0),
        (22.0, "say", "And silence."),
        # nothing answers here. that is the lesson.
        (24.6, "say", "The more you know, the more you observe."),
    ],
    "tr3_dark": [
        (0.5,  "say", "Something in the dark heard the song."),
        (3.7,  "obs", "who are you", "fear", -12),
        (7.0,  "say", "It learned pitch."),
        (8.3,  "obs", "the same", "urgent", 0),
        (9.6,  "say", "It learned time."),
        (10.9, "obs", "again", "urgent", 0),
        (12.4, "say", "Everything you sing, it can sing back."),
        (18.4, "say", "It learned every chord."),
        (19.9, "obs", "we are connected", "urgent", -12),
        (21.4, "say", "And then there were two."),
        (23.0, "obs", "no", "fear", -12),
        (24.8, "say", "One thing was left it could not copy."),
        # and then nothing — the rest it cannot steal.
    ],
}


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def to_mono(path):
    """Read any wav as float32 mono, resampled to the world's rate."""
    out = run([FFMPEG, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
               "-f", "f32le", "-"]).stdout
    return np.frombuffer(out, np.float32).copy()


def ensure_model(voice):
    """Fetch and unpack a piper voice on first use. Returns the .onnx path."""
    fn, url, _ = PIPER[voice]
    dst = os.path.join(VOICE_DIR, fn)
    if os.path.exists(dst):
        return dst
    os.makedirs(VOICE_DIR, exist_ok=True)
    print(f"  … fetching the {voice} voice model (one time)")
    tgz = os.path.join(VOICE_DIR, f"{voice}.tar.gz")
    run(["curl", "-sL", "--max-time", "300", "-o", tgz, url])
    run(["tar", "xzf", tgz, "-C", VOICE_DIR])
    os.unlink(tgz)
    if not os.path.exists(dst):
        raise SystemExit(f"unpacked {voice} but {fn} is not there")
    return dst


_LOADED = {}


def speak(text, voice="alan", length_scale=None):
    """Synthesize one line -> float32 mono at SR."""
    if voice in ESPEAK:
        p = ESPEAK[voice]
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            raw = f.name
        try:
            run(["espeak-ng", "-v", p["v"], "-s", str(p["s"]), "-p", str(p["p"]),
                 "-g", str(p["g"]), "-a", str(p["a"]), "-w", raw, text])
            return to_mono(raw)
        finally:
            os.unlink(raw)

    from piper import PiperVoice, SynthesisConfig
    if voice not in _LOADED:
        _LOADED[voice] = PiperVoice.load(ensure_model(voice))
    cfg = SynthesisConfig(length_scale=length_scale or PIPER[voice][2], noise_scale=0.60,
                          noise_w_scale=0.75, normalize_audio=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        raw = f.name
    try:
        import wave
        with wave.open(raw, "wb") as w:
            _LOADED[voice].synthesize_wav(text, w, syn_config=cfg)
        return to_mono(raw)
    finally:
        os.unlink(raw)


def shape(x, room=0.26, soften=0.0):
    """Make it the Observer: trim the rumble, set it back in the room.

    A neural voice needs no smoothing — it is already a real voice, and blurring it only
    costs the consonants the transcriber reads. `soften` exists for the espeak fallback,
    whose formant buzz does want taming.
    """
    if len(x) == 0:
        return x
    if soften > 0:
        k3 = np.array([soften * 0.5, 1.0 - soften, soften * 0.5], np.float32)
        x = np.convolve(x, k3 / k3.sum(), "same")
    # high-pass by subtracting a slow moving average — removes rumble under ~90 Hz
    k = max(1, int(SR / 90))
    x = x - np.convolve(x, np.ones(k, np.float32) / k, "same")
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.92
    wet = reverb(x, mix=room)
    x = x + (wet - x) * 0.26                          # a watcher's distance, not a cathedral
    return (x / (np.max(np.abs(x)) + 1e-9) * 0.9).astype(np.float32)


def voiced(text, voice):
    """One shaped line, with the right amount of taming for the engine in use."""
    return shape(speak(text, voice), soften=0.5 if voice in ESPEAK else 0.0)


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


def lay(bed, items, amount=0.40, ramp=0.26, level=0.85):
    """Lay spoken lines over the bed, pulling the music down only while a voice speaks.

    items = [(seconds, mono_signal), ...]. One envelope is built across every line, so
    back-to-back narration ducks once and stays down rather than pumping between lines.
    """
    n = len(bed)
    env = np.ones(n, np.float32)
    lo = 1.0 - amount
    r = max(1, int(ramp * SR))
    spans = []
    for at, sig in items:
        i = int(at * SR)
        j = min(n, i + len(sig))
        if i < n and j > i:
            spans.append((i, j))
            env[i:j] = lo
    for i, j in spans:                                # ramp only where still open
        fi = max(0, i - r)
        env[fi:i] = np.minimum(env[fi:i], np.linspace(1.0, lo, i - fi, dtype=np.float32))
        fo = min(n, j + r)
        env[j:fo] = np.minimum(env[j:fo], np.linspace(lo, 1.0, fo - j, dtype=np.float32))
    out = bed * env[:, None]
    for at, sig in items:
        i = int(at * SR)
        j = min(n, i + len(sig))
        if i >= n or j <= i:
            continue
        seg = sig[:j - i]
        out[i:j, 0] += seg * level
        out[i:j, 1] += seg * level
    peak = np.max(np.abs(out)) + 1e-9
    if peak > 0.995:
        out = out / peak * 0.995
    return out.astype(np.float32)


def obs_signal(phrase, style="calm", register=0, color="major", level=0.55):
    """Render one Observian phrase to a mono signal — the world's half of the conversation.

    The lexicon is the same one the episodes speak, so a reply here is a real sentence in
    the language, not decoration: 'hello' really is Do Mi Sol.
    """
    from observian import events, LEXICON
    from make_music import piano, midi, add
    if phrase not in LEXICON:
        raise SystemExit(f"not in the Observian lexicon: {phrase!r}")
    evs, total = events(phrase, style, register, color)
    buf = np.zeros(int((total + 1.8) * SR), np.float32)
    for (m, dt, du, am) in evs:
        add(buf, piano(midi(m), du + 0.9, am), dt)
    peak = np.max(np.abs(buf)) + 1e-9
    return (buf / peak * level).astype(np.float32)


def dialogue_lines(beats, voice, limit):
    """Alan and the world, taking turns: spoken lines and Observian replies."""
    items, spoken, replies = [], 0, 0
    for beat in beats:
        at, kind = beat[0], beat[1]
        if at >= limit:
            continue
        if kind == "say":
            items.append((at, voiced(beat[2], voice)))
            spoken += 1
        else:
            phrase, style, register = beat[2], beat[3], beat[4]
            items.append((at, obs_signal(phrase, style, register)))
            replies += 1
    return items, spoken, replies


def caps_of(mod):
    """Read CAPS and TITLE_DUR out of an episode module without importing it — importing
    would build the whole scene. AST + literal_eval keeps it cheap and side-effect free."""
    tree = ast.parse(open(os.path.join(ROOT, mod)).read())
    caps = title = None
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        if name not in ("CAPS", "TITLE_DUR"):
            continue
        try:
            val = ast.literal_eval(node.value)
        except ValueError:
            continue
        if name == "CAPS":
            caps = val
        else:
            title = val
    if caps is None or title is None:
        raise SystemExit(f"{mod}: could not read CAPS/TITLE_DUR")
    return title, caps


def story_lines(mod, voice, limit):
    """Speak every on-screen caption at the moment it appears.

    A line is compressed only if it would run into the next caption — the story stays in
    sync with the picture, and nothing is spoken over the top of the following line.
    """
    title, caps = caps_of(mod)
    base = PIPER[voice][2] if voice in PIPER else 1.0
    items, clipped = [], 0
    for k, (s, e, txt) in enumerate(caps):
        at = title + s
        if at >= limit:                               # video is shorter than the script
            clipped += 1
            continue
        room = (caps[k + 1][0] - s) if k + 1 < len(caps) else (e - s + 2.0)
        room = min(room, limit - at)
        text = " ".join(txt.split())                  # captions wrap with newlines
        sig = speak(text, voice)
        if len(sig) / SR > room and voice in PIPER:    # too long: say it a little quicker
            want = max(0.80, base * room / (len(sig) / SR))
            sig = speak(text, voice, length_scale=want)
        if len(sig) / SR > room:                       # still long: let it breathe, gently
            fade = np.linspace(1.0, 0.0, min(len(sig), int(0.25 * SR)), dtype=np.float32)
            cut = int(room * SR)
            sig = sig[:cut].copy()
            if len(sig) > len(fade):
                sig[-len(fade):] *= fade
        items.append((at, shape(sig, soften=0.5 if voice in ESPEAK else 0.0)))
    return items, clipped, len(caps)


def process(path, line, voice, at, outdir, mod=None, dialog=None):
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

    limit = len(bed) / SR
    if dialog:
        items, spoken, replies = dialogue_lines(dialog, voice, limit)
        mixed = lay(bed, items)
        note = f"{spoken} spoken lines + {replies} Observian replies"
        return write(path, mixed, outdir, note)

    nar = voiced(line, voice)
    items = [(at, nar)]
    note = f"{len(nar) / SR:.1f}s keyword line"
    if mod:
        told, clipped, total = story_lines(mod, voice, limit)
        items += told
        note += f" + {len(told)}/{total} story lines"
        if clipped:
            note += f" ({clipped} past the end of this video, dropped)"
    mixed = lay(bed, items)
    return write(path, mixed, outdir, note)


def write(path, mixed, outdir, note):
    """Mux a new audio track under the untouched video stream."""
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
    print(f"  ✓ {base}   ({note})")
    return dst


def sample(outdir):
    """One mp3 with the same sentence in each neural voice, announced, so one can be picked."""
    parts = []
    gap = np.zeros(int(0.55 * SR), np.float32)
    for name in PIPER:
        parts.append(voiced(f"Voice. {name}.", name) * 0.5)
        parts.append(gap)
        parts.append(voiced(LINES["ch1_ep8"], name))
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
    p.add_argument("--voice", default="alan", choices=VOICES)
    p.add_argument("--at", type=float, default=1.0, help="seconds into the video")
    p.add_argument("--story", action="store_true",
                   help="also speak every on-screen caption, in sync")
    p.add_argument("--dialogue", action="store_true",
                   help="trailers: Alan and the world take turns (Observian replies)")
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
        dlg = DIALOG.get(e["id"]) if a.dialogue else None
        mod = MODULES.get(e["id"]) if (a.story and not dlg) else None
        if a.story and not mod and not dlg:
            print(f"  · {e['id']} has no caption table — keyword line only")
        if process(src, LINES[e["id"]], a.voice, a.at, a.outdir, mod, dlg):
            done += 1
    print(f"\n{done}/{len(todo)} narrated into {a.outdir}")


if __name__ == "__main__":
    main()
