#!/usr/bin/env python3
"""
voicetrack — export Alan on his own, and the episode without him.

For editing in CapCut or TikTok rather than baking the mix here. Two files per episode:

  <id>_alan.mp3        Alan alone, silent everywhere he is not speaking, and exactly as
                       long as the video. Drop it at 00:00 and it is already in sync —
                       no nudging, no guessing.
  <id>_music.mp4       the episode with the score only, so adding the voice track back
                       does not give you two Alans.

Both come from the same synthesized signals the episode itself uses, so what you lay in
the editor is identical to what was verified here.

    python3 tools/voicetrack.py --episode ch2_ep8
    python3 tools/voicetrack.py --episode ch2_ep8 --no-video
"""
import argparse
import importlib
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_music import SR, add                                            # noqa: E402
import narrate as N                                                       # noqa: E402

ROOT = N.ROOT
EX = N.EX
OUT = os.path.join(EX, "voice")

# Episodes that carry their own narration in the episode module rather than getting it
# from narrate.py. These expose ALAN and alan_sigs().
BAKED = {"ch2_ep8": "ep19_voiceinside"}


def episode(eid):
    for e in json.load(open(N.PIPE))["episodes"]:
        if e["id"] == eid:
            return e
    sys.exit(f"unknown episode id: {eid}")


def voice_items(eid, voice):
    """[(seconds_into_video, mono_signal)] — exactly what the episode speaks."""
    if eid in BAKED:
        mod = importlib.import_module(BAKED[eid])
        return [(mod.TITLE_DUR + t, sig) for (t, sig) in mod.alan_sigs()], mod.DUR
    # otherwise it is a narrate.py episode: the keyword line, plus captions if mapped
    items = [(1.0, N.voiced(N.LINES[eid], voice))]
    mod = N.MODULES.get(eid)
    src = os.path.join(ROOT, episode(eid)["path"])
    dur = N.video_seconds(src) or 0.0
    if mod:
        told, _clip, _tot = N.story_lines(mod, voice, dur)
        items += told
    return items, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--voice", default="alan", choices=N.VOICES)
    ap.add_argument("--no-video", action="store_true", help="skip the music-only mp4")
    ap.add_argument("--peak", type=float, default=0.92, help="normalise the voice to this")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    e = episode(a.episode)
    src = os.path.join(ROOT, e["path"])
    if not os.path.exists(src):
        sys.exit(f"missing {e['path']}")

    items, dur = voice_items(a.episode, a.voice)
    if not dur:
        dur = N.video_seconds(src)
    n = int(round(dur * SR))
    track = np.zeros(n, np.float32)
    for at, sig in items:
        add(track, sig, at)
    peak = float(np.max(np.abs(track)))
    if peak > 1e-6:
        track *= a.peak / peak
    st = np.stack([track, track], 1)

    base = os.path.basename(src).replace(".mp4", "")
    mp3 = os.path.join(OUT, base + "_alan.mp3")
    N.run([N.FFMPEG, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2",
           "-i", "-", "-b:a", "192k", mp3], input=st.tobytes())
    spoken = sum(len(s) for _t, s in items) / SR
    print(f"  ✓ {os.path.basename(mp3)}   {dur:.0f}s long, {len(items)} lines, "
          f"{spoken:.0f}s of speech")

    if a.no_video:
        return
    # the same episode with the score only, so the voice can be laid back on top once
    if a.episode in BAKED:
        mod = importlib.import_module(BAKED[a.episode])
        bed = np.asarray(mod.build_audio(bed_only=True), np.float32)
    else:
        bed = N.audio_of(src)                       # already has no narration
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = f.name
    try:
        N.run([N.FFMPEG, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2",
               "-i", "-", wav], input=bed.tobytes())
        mp4 = os.path.join(OUT, base + "_music.mp4")
        N.run([N.FFMPEG, "-v", "error", "-y", "-i", src, "-i", wav,
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", mp4])
    finally:
        os.unlink(wav)
    print(f"  ✓ {os.path.basename(mp4)}   score only, video stream copied")


if __name__ == "__main__":
    main()
