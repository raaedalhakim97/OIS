"""
Assemble the official CHAPTER I · EPISODE 1 — "The Note Between":
  [ intro title card ~5s ]  +  [ the episode body (community_observer) ]
with a soft ambient bed under the card, then the episode's own audio.
Output: ch1_ep1_the_note_between.mp4
"""
import os
import numpy as np
import imageio.v2 as imageio, imageio_ffmpeg, subprocess
import title_card as tc
import community_observer as ep
from make_music import SR, midi, pad, reverb, add, write_wav
from ep3_part1 import wind_gust

os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 24
TITLE_DUR = 5.0
CHAPTER, EPISODE, TITLE, LAND = "I", "1", "The Note Between", "the Home Fields"
OUT = "ch1_ep1_the_note_between.mp4"


def title_audio():
    n = int(TITLE_DUR * SR)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    p = pad([midi(41), midi(53), midi(57)], TITLE_DUR, amp=0.05)     # a soft low F chord = the lantern
    add(L, p, 0.2); add(R, np.roll(p, 400), 0.2)
    g = wind_gust(4.0, 0.03, 3); add(L, g, 0.6); add(R, g, 0.9)
    L = reverb(L); R = reverb(R)
    st = np.tanh(np.stack([L, R], 1) * 1.1)
    st /= (np.max(np.abs(st)) + 1e-6); st *= 0.6
    fi, fo = int(0.5 * SR), int(1.0 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]; st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st.astype(np.float32)


def main():
    writer = imageio.get_writer("ep_silent.mp4", fps=FPS, codec="libx264",
                                output_params=["-crf", "19", "-preset", "medium",
                                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    n_t = int(TITLE_DUR * FPS)
    print(f"Title card {n_t} frames ...")
    for i in range(n_t):
        writer.append_data(tc.title_frame(i / FPS, CHAPTER, EPISODE, TITLE, LAND, dur=TITLE_DUR))
    n_b = int(ep.DUR * FPS)
    print(f"Body {n_b} frames ...")
    for i in range(n_b):
        writer.append_data(ep.render(i / FPS))
        if (i + 1) % 96 == 0: print(f"  {i+1}/{n_b}")
    writer.close()

    full = np.concatenate([title_audio(), ep.build_audio()], axis=0)
    write_wav("ep.wav", full)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", "ep_silent.mp4", "-i", "ep.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", OUT],
                   check=True, capture_output=True)
    print("Done ->", OUT)


if __name__ == "__main__":
    main()
