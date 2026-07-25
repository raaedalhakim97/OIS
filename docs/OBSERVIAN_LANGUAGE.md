# OBSERVIAN — the Observer Language (Harmonic)

> The people of Observer World do not speak with letters. They speak with music.
> Every sentence is a melody. Every conversation is literally a piece of music.
> To an outsider it sounds like singing. To them it is language.

**Production rule:** in every story, CAPTIONS carry the meaning; the Observian
SOUND carries the speech. Characters never get spoken/written dialogue — the
lantern sings the phrase, the caption translates it. Recurring phrases repeat
until the audience understands them without being told.
*(the more you know, the more you observe.)*

---

## The Seven Sounds (musical alphabet)

| Sound | Meaning core | Concept |
|---|---|---|
| **Do** | Origin | self, beginning, existence |
| **Re** | Motion | change, travel, movement |
| **Mi** | Reflection | other people, communication |
| **Fa** | Question | doubt, searching, uncertainty |
| **Sol** | Harmony | unity, completion, balance |
| **La** | Emotion | feeling, desire, memory |
| **Ti** | Future | hope, expectation, destiny |

Words are **melodic patterns** built from these, never arbitrary.

## Grammar = music
- **Pitch register:** high = excitement/urgency/discovery · low = calm/sadness/wisdom.
- **Rhythm:** slow = calm · fast = urgency · broken = fear · continuous = confidence.
- **Silence:** pauses are punctuation. A rest changes meaning.
- **Harmony:** single note = simple idea · interval = relationship · **chord = complete
  thought/action** (e.g. Do+Mi+Sol sounded together = "we are connected").
- **Emotion by harmony:** major = hope · minor = sadness · dissonance = conflict ·
  resolution = understanding.

## Canon phrasebook (from the spec)
| Observian | Literal | Functions as |
|---|---|---|
| Do Mi Sol | "I recognize your harmony." | Hello. |
| Fa Mi Sol | "What is your harmony?" | How are you? |
| Do Sol Do | "My harmony is complete." | I am well. |
| Do | "I" | — |
| Do Mi | "You and I" | — |
| Do+Mi+Sol *(chord)* | "We are connected." | — |

## Proposed extensions (working phrasebook — approve/veto freely)
| Observian | Literal | Functions as |
|---|---|---|
| Mi Sol | "your harmony (recognized)" | friend |
| Sol Do | "harmony at the origin" | home |
| Sol Re Ti | "our harmony moves toward the future" | farewell |
| Re Re Do | "move, move, with me" | come with me |
| Do Fa Re | "I search, moving" | I am searching |
| Fa Ti Fa (fast, high) | "question the future, question" | danger! |
| Mi La Sol | "you, felt, in harmony" | thank you |
| Do Re Mi Sol | "from the origin, moving, together, whole" | the song has begun |

## Translating human words (letter → note)
Each letter maps to a note by phonetic weight (anchors from the spec:
A→Ti, B→Fa, C→Sol, and HELLO → Fa Mi Sol Sol Ti):

```
A→Ti B→Fa C→Sol D→Do E→Mi F→Fa G→Sol H→Fa I→Do J→Re K→Ti L→Sol M→Mi
N→Re O→Ti P→Fa Q→Fa R→Re S→Sol T→Ti U→La V→La W→Re X→Fa Y→La Z→Re
```

So any name or word can be sung: e.g. **HELLO → Fa Mi Sol Sol Ti**.

## Writing system
Written Observian is not alphabetical: every word is a small musical phrase —
reading Observian is reading sheet music. (On screen, the staff HUD already IS
this: the world's writing.)

## Engine
`observian.py` implements the language for every episode:
- `say(d, "hello", t, style=, register=, color=, pan=)` — sings a phrase from the
  phrasebook (or raw "Do Mi Sol" notation; chords with `+`).
- Styles: calm · urgent · fear (broken rhythm) · confident · whisper.
- `color="minor"` lowers Mi and La (sadness); registers shift ±12 (voices).
- `word_melody("HELLO")` — letter→note translation of any human word.
The Lightkeeper's lantern is the voice; other keepers answer in their own register.
