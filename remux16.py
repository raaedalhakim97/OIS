import ep16_chordofthree as e
from make_music import write_wav
write_wav('ep16.wav', e.build_audio())
import imageio_ffmpeg, subprocess
ff = imageio_ffmpeg.get_ffmpeg_exe()
r = subprocess.run([ff,'-y','-i','ep16_silent.mp4','-i','ep16.wav','-c:v','libx264','-crf','27',
 '-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart','-c:a','aac','-b:a','160k',
 '-shortest','ch2_ep6_the_chord_of_three.mp4'], capture_output=True, text=True)
print('mux rc', r.returncode)
