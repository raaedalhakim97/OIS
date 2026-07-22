
import logging
from typing import List, Tuple, Optional

from cineengine.config import Config

logger = logging.getLogger(__name__)

class Subtitle:
    """
    Represents a single subtitle entry with text, timing, and styling.
    """
    def __init__(
        self,
        text: str,
        start_time: float,
        end_time: float,
        font: Optional[str] = None,
        font_size: Optional[int] = None,
        color: Optional[Tuple[float, float, float, float]] = None,
        position: Optional[Tuple[float, float]] = None,
        animation_type: Optional[str] = None
    ):
        """
        Initializes a Subtitle object.

        Args:
            text (str): The text content of the subtitle.
            start_time (float): The start time of the subtitle in seconds.
            end_time (float): The end time of the subtitle in seconds.
            font (str, optional): Font family for the subtitle. Defaults to None.
            font_size (int, optional): Font size for the subtitle. Defaults to None.
            color (Tuple[float, float, float, float], optional): RGBA color for the subtitle. Defaults to None.
            position (Tuple[float, float], optional): Normalized (x, y) position of the subtitle. Defaults to None.
            animation_type (str, optional): Type of animation to apply. Defaults to None.
        """
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.font = font
        self.font_size = font_size
        self.color = color
        self.position = position
        self.animation_type = animation_type

    def is_active(self, current_time: float) -> bool:
        """
        Checks if the subtitle should be displayed at the given time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            bool: True if the subtitle is active, False otherwise.
        """
        return self.start_time <= current_time < self.end_time


class SubtitleManager:
    """
    Manages a collection of subtitles and their rendering properties.
    """
    def __init__(self, config: Config):
        """
        Initializes the SubtitleManager.

        Args:
            config (Config): The CineEngine configuration object.
        """
        self.config = config
        self.subtitles: List[Subtitle] = []
        logger.info("SubtitleManager initialized.")

    def add_subtitle(
        self,
        text: str,
        start_time: float,
        end_time: float,
        font: Optional[str] = None,
        font_size: Optional[int] = None,
        color: Optional[Tuple[float, float, float, float]] = None,
        position: Optional[Tuple[float, float]] = None,
        animation_type: Optional[str] = None
    ) -> None:
        """
        Adds a new subtitle to the manager.

        Args:
            text (str): The text content of the subtitle.
            start_time (float): The start time of the subtitle in seconds.
            end_time (float): The end time of the subtitle in seconds.
            font (str, optional): Font family for the subtitle. Defaults to config.
            font_size (int, optional): Font size for the subtitle. Defaults to config.
            color (Tuple[float, float, float, float], optional): RGBA color for the subtitle. Defaults to config.
            position (Tuple[float, float], optional): Normalized (x, y) position of the subtitle. Defaults to centered.
            animation_type (str, optional): Type of animation to apply. Defaults to None.
        """
        subtitle = Subtitle(
            text=text,
            start_time=start_time,
            end_time=end_time,
            font=font or self.config.SUBTITLE_FONT,
            font_size=font_size or self.config.SUBTITLE_FONT_SIZE,
            color=color or self.config.SUBTITLE_COLOR,
            position=position or (0.5, 0.1), # Default to bottom center
            animation_type=animation_type
        )
        self.subtitles.append(subtitle)
        logger.info(f"Added subtitle: \"{text}\" from {start_time:.2f}s to {end_time:.2f}s.")

    def get_active_subtitles(self, current_time: float) -> List[Subtitle]:
        """
        Returns a list of subtitles that are active at the given time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            List[Subtitle]: A list of active Subtitle objects.
        """
        return [s for s in self.subtitles if s.is_active(current_time)]

    def clear_subtitles(self) -> None:
        """
        Clears all subtitles from the manager.
        """
        self.subtitles.clear()
        logger.info("All subtitles cleared.")

if __name__ == "__main__":
    # Example Usage
    from cineengine.config import Config
    config = Config()
    manager = SubtitleManager(config)

    manager.add_subtitle("Hello, CineEngine!", 0.0, 2.0)
    manager.add_subtitle("This is a test.", 1.5, 3.5, font_size=36, color=(1.0, 0.0, 0.0, 1.0))
    manager.add_subtitle("Animated text here!", 3.0, 5.0, animation_type="fade_in_out")

    print("\n--- Time 0.5s ---")
    for sub in manager.get_active_subtitles(0.5):
        print(f"Active: {sub.text}")

    print("\n--- Time 2.0s ---")
    for sub in manager.get_active_subtitles(2.0):
        print(f"Active: {sub.text}")

    print("\n--- Time 4.0s ---")
    for sub in manager.get_active_subtitles(4.0):
        print(f"Active: {sub.text}")

    manager.clear_subtitles()
    print(f"\nSubtitles after clearing: {len(manager.subtitles)}")
