
import moviepy.editor as mpy
import numpy as np
import logging
from typing import List, Tuple, Callable, Optional

logger = logging.getLogger(__name__)

class VideoExporter:
    """
    Handles the final export of the video, combining frames and audio.
    """
    def __init__(self, fps: int, resolution: Tuple[int, int]):
        """
        Initializes the VideoExporter.

        Args:
            fps (int): Frames per second for the output video.
            resolution (Tuple[int, int]): Resolution of the output video (width, height).
        """
        self.fps = fps
        self.resolution = resolution
        logger.info(f"VideoExporter initialized with FPS: {self.fps}, Resolution: {self.resolution}")

    def export_video(
        self,
        frame_generator: Callable[[float], np.ndarray],
        duration: float,
        output_path: str,
        audio_path: Optional[str] = None
    ) -> None:
        """
        Exports the video by generating frames and optionally combining with an audio track.

        Args:
            frame_generator (Callable[[float], np.ndarray]): A function that takes current time (float) 
                                                              and returns a numpy array representing the frame.
            duration (float): The total duration of the video in seconds.
            output_path (str): The path where the final video will be saved.
            audio_path (Optional[str]): Path to the audio file to be included in the video. Defaults to None.
        """
        logger.info(f"Starting video export to {output_path} with duration {duration:.2f}s...")

        try:
            # Create a MoviePy VideoClip from the frame generator
            clip = mpy.VideoClip(make_frame=frame_generator, duration=duration)
            clip = clip.set_fps(self.fps)

            if audio_path:
                logger.info(f"Adding audio track from {audio_path}...")
                audio_clip = mpy.AudioFileClip(audio_path)
                # Ensure audio clip duration matches video clip duration
                if audio_clip.duration > duration:
                    audio_clip = audio_clip.subclip(0, duration)
                elif audio_clip.duration < duration:
                    # Optionally loop or pad audio if shorter than video
                    logger.warning("Audio clip is shorter than video duration. Audio will end early.")
                clip = clip.set_audio(audio_clip)

            # Write the video file
            clip.write_videofile(
                output_path,
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                preset="medium", # or "fast", "slow" for quality/speed trade-off
                threads=4, # Adjust based on CPU cores
                verbose=False, # Suppress MoviePy verbose output
                logger=None # Suppress MoviePy logger
            )
            logger.info(f"Video successfully exported to {output_path}")

        except Exception as e:
            logger.error(f"Error during video export: {e}")
            raise

if __name__ == "__main__":
    print("VideoExporter requires a frame generator and duration to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("    from cineengine.config import Config")
    print("    config = Config()")
    print("    exporter = VideoExporter(config.FPS, config.RESOLUTION)")
    print("    # Define a dummy frame generator (e.g., solid color frames)")
    print("    def dummy_frame_generator(t):
    print("        color = (int(255 * (t / 5.0)), 0, int(255 * (1 - t / 5.0)))")
    print("        return np.full((config.RESOLUTION[1], config.RESOLUTION[0], 3), color, dtype=np.uint8)")
    print("    # exporter.export_video(dummy_frame_generator, duration=5.0, output_path=\"dummy_output.mp4\")")
    print("    print(\"Dummy video export example finished.\")")
