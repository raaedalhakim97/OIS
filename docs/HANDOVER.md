# THE OBSERVER WORLD — Project Handover

## What we are making
An animated vertical series (1080×1920, ~2 min per episode) for TikTok channel
**The Observer (@3theobserver3)** — signature line: *"the more you know, the more you
observe."* It is a **music-learning series told as story, never as a lesson**: every
episode is a quiet fable, and the music theory hides inside the plot.

## The world (lore in one breath)
- Every soul is a **note**. No note completes itself.
- The **Lightkeeper** (small cloaked silhouette carrying a lantern) walks a little
  turning planet helping notes find who they harmonize with — he completes, then walks on.
- The **Observer** is the one watching the world: the screen itself is its eye
  (vignette = eye rim; scene cuts = blinks).
- Enemies (Chapter II): the **Silence** (collects music into quiet), its **Hollow**
  (cuts the threads between notes), and the **Sunderer** (the first keeper, fallen).
- The **sharp ♯** (introduced Ep9) is an outsider "between-stone" — a future bridge-hero.
- A five-line **staff with the sol key** floats above scenes as the world's HUD:
  found notes = filled heads, missing = hollow, unfound = ghosts.

## Chapter structure
- **Chapter I — how the world works** (COMPLETE, posted/queued): teaches the audience
  the mechanics through story.
- **Chapter II — "The Listening Dark"** (next): story, action, myth puzzles built ON
  those mechanics. Full 8-episode season spine is in
  `docs/OBSERVER_WORLD_BIBLE.md` PART VIII. Premiere suggestion:
  **"The Echo That Came Back"** (the First Song's echo returns with one note flattened).

## Chapter I episodes (final)
| Ep | Title | Hidden lesson |
|---|---|---|
| 0 (Prologue) | The Keeper | the premise |
| 1 | The Note Between | belonging/harmony |
| 2 | The Conversation | two notes talking |
| 3 | *(vacant slot — never filled; decide later: fill or renumber)* | — |
| 4 | The Hollow | threat established |
| 5 | The Home of Five | the scale as home (Magnus music) |
| 6 | The Heartbeat | rhythm/beat |
| 7 | The Missing Note | solfège scale; find a note by ear |
| 8 | The First Note | **octave** — same note, different voice ("high or low, Do is Do") |
| 9 | The Second Note | **whole vs half steps**; what a sharp is |
| 10 | The First Song (finale) | scale complete; first melody; Ch II hook ("something heard it") |

## Tech (all procedural Python, CPU only — no GPU)
Repo **raaedalhakim97/OIS**, branch `claude/extract-create-new-repo-evr0vz`.
Working set lives flat next to `cineengine/`:
- `character.py` — keeper rig (poses stand/walk/lift/sit/front, lean, breathing).
  ⚠️ Its returned offsets are the **lantern/hand position** — never add them to the
  body position (that caused the floating-keeper bug, fixed in Ep8/9).
- `planet.py` — the rotating little-planet ground (apex at CX, keeper SINK=34 into
  the visual surface). World turns opposite the walk; **stops during scenes**.
- `world.py` — sky palettes (night/dawn/morning/golden/dusk/winter) + atmosphere.
- `staff.py` — shared staff HUD: real treble-clef glyph (FreeSerif U+1D11E), staggered
  write-in, note modes ghost/empty/full, glows.
- `flow.py` — motion system: eased curved flights, overshoot-settle landings,
  two-frequency bob, velocity lean, idle sway. USE THIS for all movement.
- `title_card.py` — intro card: Chapter · Episode № · Title · Land (6s) + quiz overlay.
- `make_music.py` — score engine: felt piano, pad, bass, softkick, reverb (dry/wet
  buses), master. **No violin (cancelled). No snare.** SR=44100 — ⚠️ never shadow `SR`.
- `cineengine.generator.FX` — bloom/vignette/grain finishing.
- Episode files: `ep7_otherkeeper.py`, `ep8_firstnote.py`, `ep9_secondnote.py`,
  `ep10_firstsong.py` (best current templates — copy Ep10's structure).

**Episode pattern:** `render(t)` per frame → imageio H.264 (CRF20 silent) →
`build_audio()` numpy stereo → ffmpeg mux CRF27 + AAC. Always preview key frames
(`--preview <sec>`) before the ~15-min render. Keep deliverables **< 30 MiB**.

## Music rules
- Engine (piano/pad/bass/softkick) for calm episodes; **Magnus AI** mp3s for
  danger/strings hero tracks (I sync animation to the audio).
- Amps modest (piano ≤ ~0.17, pads ≤ ~0.055); evolving chord bed tells the story
  (e.g. Ep8: C→Am→F→thin G→low C→3-octave C→plagal close).
- Music-as-story codex: piano=Keeper · consonance=belonging · dissonance=tension
  waiting to resolve · accidentals=bridges/outsiders · rest/silence = Ch II's answer.

## Language — Observian (canon)
The inhabitants speak **music, not letters**: seven sounds (Do origin · Re motion ·
Mi reflection · Fa question · Sol harmony · La emotion · Ti future) form melodic
words; grammar is register/rhythm/silence/harmony. Spec + phrasebook:
`docs/OBSERVIAN_LANGUAGE.md`. Engine: `observian.py` — `say(d, "hello", t)` sings
Do Mi Sol; styles calm/urgent/fear/confident/whisper; `color="minor"` for sadness;
`word_melody("HELLO")` translates human words (→ Fa Mi Sol Sol Ti).
**Law: no spoken/written dialogue ever — captions carry meaning, the lantern sings
the phrase.** Reused phrases teach the audience the language by ear.
Demo: `observian_demo.py` → `observian_demo.m4a`.

## Visual/story standards
- Captions: centered ~0.50H, serif, 2–3 short lines, lowercase poetry voice.
- Every episode: title card → story → brand line *"the more you know, the more you
  observe."* Chapter finales add an end tag (e.g. "— end of Chapter I —").
- Chime **rings** on every note event; threads of light = bonds; ring+fill on placements.
- **Observer's Eye blink** (PART IX in bible): scene transitions = eyelid blink
  (close ~0.3s, dark beat, open ~0.45s). RECORDED BUT NOT YET IMPLEMENTED — build as
  shared `blink()` before Chapter II.

## Delivery pipeline
- Direct push to the user's n8n is blocked by egress policy → **pull model**:
  n8n reads `cineengine/examples/pipeline/latest.json` (newest episode + caption) and
  `episodes.json` (catalog) from the repo. Update both with every episode.
- Rendered episodes live at `cineengine/examples/ch1_epN_<title>.mp4`.

## Open items
1. Implement the Observer's-Eye `blink()` transition (standard is written, code isn't).
2. Chapter II premiere: "The Echo That Came Back" (script beats in bible PART VIII).
3. Ep3 slot still vacant (fill or renumber — owner's call).
4. Minor: episode "N more to go" counts are approximate across Ep8–10; harmless.

*Prepared 2026-07-25 · session: Claude Code on OIS repo · everything above is pushed.*
