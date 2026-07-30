"""
observian — the spoken language of THE OBSERVER WORLD, as an engine.
Words are melodic patterns of the seven sounds; grammar is register, rhythm,
silence and harmony. Captions carry meaning; this module carries the speech.

  say(d, "hello", t0)                      # the lantern sings "Do Mi Sol"
  say(d, "Fa Mi Sol", t0, style="calm")    # raw notation works too
  say(d, "we are connected", t0)           # '+' chords sound together
  say(d, word_melody("HELLO"), t0)         # any human word, letter -> note

styles: calm | urgent | fear | confident | whisper
color:  major (hope) | minor (sadness: Mi and La lowered)
register: semitone shift (e.g. -12 a deep elder voice, +12 excitement)
Returns the phrase's total duration so callers can time captions and glyphs.
"""
from make_music import midi, piano

DEGREE = {"Do": 0, "Re": 2, "Mi": 4, "Fa": 5, "Sol": 7, "La": 9, "Ti": 11}
BASE = 60                                            # Do = middle C

# canon phrases (from the language spec) + working extensions
LEXICON = {
    "hello": "Do Mi Sol",                # I recognize your harmony.
    "how are you": "Fa Mi Sol",          # What is your harmony?
    "i am well": "Do Sol Do",            # My harmony is complete.
    "i": "Do",                           # the origin, alone
    "you and i": "Do Mi",                # origin, then the other
    "we are connected": "Do+Mi+Sol",     # chord = complete thought
    "friend": "Mi Sol",                  # the other, in harmony
    "home": "Sol Do",                    # harmony arriving at the origin
    "farewell": "Sol Re Ti",             # our harmony moves toward the future
    "come with me": "Re Re Do",          # motion, motion, toward me
    "i am searching": "Do Fa Re",        # self, doubt, and moving anyway
    "danger": "Fa Ti Fa",                # doubt around what is coming
    "thank you": "Mi La Sol",            # you, feeling, harmony
    "the song has begun": "Do Re Mi Sol",
    # --- Chapter II ---
    "listen": "Fa Mi",                   # question toward the other = attend
    "who are you": "Fa Do",              # question the origin
    "something is wrong": "Fa Sol Fa",   # the harmony is in question
    "the song is broken": "Do Re Mi Fa",  # "the song has begun" with harmony -> doubt
    "i hear you": "Mi Do Sol",           # you reach my harmony
    "wait": "Do Do",                     # remain at the origin
    "i am afraid": "La Fa La",           # feeling, doubt, feeling
    "what now": "Fa Re",                 # question the motion = where do we go
    "yes": "Sol",                        # agreement IS harmony
    "no": "Do+Fa",                       # a clash: self against doubt
    "again": "Re Do Re",                 # motion returning to the origin, and out again
    "how far": "Fa Re Re",               # question the motion, twice — distance
    "closer": "Re Do",                   # motion toward here
    "far": "Re Re Ti",                   # motion, motion, still ahead
    "do you hear it": "Fa Mi Do",        # question toward the other, about me
    "there": "Re Mi",                    # motion toward the other — pointing
    "let us go": "Re Sol",               # we move in harmony
    "what is it": "Fa Ti",               # question the unknown
    "i am here": "Do Sol",               # the origin, in harmony — I am, and I am well
    "help us": "Fa Sol",                 # question toward harmony = I ask you for harmony
    "i cannot": "Do Fa",                 # self meeting doubt
    "i remember you": "Mi La Do",        # other, memory, self
    "i was wrong": "Do Fa Sol",          # self, doubt, MOVING to harmony — an apology
    "rise": "Re Ti",                     # motion toward the future/above
    "the same": "Mi Mi",                 # the other, twice — an echo, not an answer
    "now": "Ti Do",                      # the future arriving at the origin = this instant
    "together": "Sol Mi",                # harmony with the other
    "i give you this": "Do Mi Sol Ti",   # self, other, harmony, future — a gift forward
    "it was mine": "Do La Do",           # self, memory, self
}

# The Silence does not speak in notes. It answers with a REST — the absence where a
# reply should be. Use silence(seconds) in a scene to give it a line.
def silence(seconds):
    return seconds

# letter -> note (anchors: A→Ti B→Fa C→Sol, HELLO → Fa Mi Sol Sol Ti)
LETTERS = {
    "A": "Ti", "B": "Fa", "C": "Sol", "D": "Do", "E": "Mi", "F": "Fa", "G": "Sol",
    "H": "Fa", "I": "Do", "J": "Re", "K": "Ti", "L": "Sol", "M": "Mi", "N": "Re",
    "O": "Ti", "P": "Fa", "Q": "Fa", "R": "Re", "S": "Sol", "T": "Ti", "U": "La",
    "V": "La", "W": "Re", "X": "Fa", "Y": "La", "Z": "Re",
}

STYLES = {                # (note_dur, gap, amp, broken)
    "calm":      (0.60, 0.30, 0.11, False),
    "urgent":    (0.26, 0.09, 0.12, False),
    "fear":      (0.30, None, 0.10, True),           # broken rhythm: uneven gaps
    "confident": (0.42, 0.16, 0.12, False),
    "whisper":   (0.55, 0.32, 0.055, False),
}
_FEAR_GAPS = [0.10, 0.46, 0.14, 0.38]


def word_melody(word):
    """Translate a human word into Observian notation (letters -> notes)."""
    return " ".join(LETTERS[c] for c in word.upper() if c in LETTERS)


def _degree_midi(name, color):
    dg = DEGREE[name]
    if color == "minor" and dg in (4, 9):            # sadness lowers Mi and La
        dg -= 1
    return BASE + dg


def events(phrase, style="calm", register=0, color="major"):
    """Compile a phrase into [(midi, t_offset, dur, amp)]. '+' joins a chord."""
    phrase = LEXICON.get(phrase.lower(), phrase)
    dur, gap, amp, broken = STYLES[style]
    out = []; t = 0.0
    for k, tok in enumerate(phrase.split()):
        names = tok.split("+")
        for nm in names:
            out.append((_degree_midi(nm, color) + register, t, dur,
                        amp / (1.0 if len(names) == 1 else 1.4)))
        g = _FEAR_GAPS[k % len(_FEAR_GAPS)] if broken else gap
        t += dur + g
    return out, t


def say(d, phrase, t0, style="calm", register=0, color="major", pan=0.5):
    """Sing a phrase into the mix via d(signal, at, pan). Returns its duration."""
    evs, total = events(phrase, style, register, color)
    for (m, dt, du, am) in evs:
        d(piano(midi(m), du + 0.9, am), t0 + dt, pan)
    return total
