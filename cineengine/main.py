
import logging
from typing import Tuple, List, Union

from cineengine.config import Config
from cineengine.camera.camera import Camera
from cineengine.renderer.timeline import TimelineEvent

logger = logging.getLogger(__name__)

class CineEngine:
    """Main class for CineEngine, orchestrating video generation."""

    def __init__(self, fps: int = 30, resolution: Tuple[int, int] = (1080, 1920), **kwargs):
        """
        Initializes the CineEngine.

        Args:
            fps (int): Frames per second for the output video.
            resolution (Tuple[int, int]): Resolution of the output video (width, height).
            **kwargs: Additional configuration parameters to override defaults.
        """
        self.config = Config(fps=fps, resolution=resolution, **kwargs)
        logger.info(f"CineEngine initialized with FPS: {self.config.FPS}, Resolution: {self.config.RESOLUTION}")

        import moderngl

        self.images: List[str] = []
        self.camera = Camera(self.config)
        from cineengine.audio.audio import Audio
        self.audio = Audio(self.config)
        from cineengine.ai.ai import AI
        self.ai = AI(self.config)

        # Create ModernGL context early for shared use
        self.ctx = moderngl.create_context(standalone=True, require=330)
        logger.info(f"ModernGL context created in CineEngine: {self.ctx.version_code}")

        from cineengine.effects.effects import Effects
        self.effects = Effects(self.config, ctx=self.ctx)
        from cineengine.subtitles.subtitles import Subtitles
        self.subtitles = Subtitles(self.config, ctx=self.ctx)
        from cineengine.renderer.renderer import Renderer
        self.renderer = Renderer(self.config, self.camera, self.effects, self.audio, self.subtitles, self.ctx)

    def add_image(self, image_path: str) -> None:
        """
        Adds an image to the video timeline.

        Args:
            image_path (str): Path to the image file.
        """
        self.images.append(image_path)
        logger.info(f"Added image: {image_path}")

    def export(self, output_path: str = "output.mp4") -> None:
        """
        Exports the generated video.

        Args:
            output_path (str): Path to save the output video.
        """
        logger.info(f"Exporting video to {output_path}...")
        # Before exporting, ensure the timeline is populated with image events
        current_start_time = 0.0
        for img_path in self.images:
            # Assuming each image is displayed for a fixed duration, e.g., 5 seconds
            image_duration = 5.0 # This should be dynamic based on user input or AI analysis
            self.renderer.timeline.add_event(TimelineEvent("image", current_start_time, image_duration, {"path": img_path}))
            current_start_time += image_duration

        self.renderer.export_video(self.images, output_path, self.audio.get_audio_mix(duration=self.renderer.timeline.total_duration))
        logger.info("Video export initiated.")

if __name__ == "__main__":
    # Example Usage:
    engine = CineEngine(
        fps=24,
        resolution=(1080, 1920)
    )

    engine.add_image("path/to/image1.png")
    engine.add_image("path/to/image2.png")

    engine.camera.cinematic_push()
    engine.effects.film_grain()
    engine.effects.bloom()
    engine.effects.depth_of_field()
    engine.audio.add("path/to/audio.wav")
    engine.subtitles.add("This is a test subtitle", start_time=0.0, end_time=5.0, animation_type="fade_in_out")

    engine.export("my_cinematic_video.mp4")
