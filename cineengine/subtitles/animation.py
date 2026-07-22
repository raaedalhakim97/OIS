
import numpy as np
from typing import Tuple, Callable

class SubtitleAnimation:
    """
    Provides various animation functions for subtitles.
    """

    @staticmethod
    def fade_in_out(t: float, duration: float) -> float:
        """
        Calculates alpha for a fade-in/fade-out animation.

        Args:
            t (float): Current time within the subtitle's active duration (0.0 to duration).
            duration (float): Total active duration of the subtitle.

        Returns:
            float: Alpha value (0.0 to 1.0).
        """
        fade_duration = min(duration / 4.0, 0.5) # Fade in/out over 25% of duration or max 0.5s

        if t < fade_duration:
            return t / fade_duration  # Fade in
        elif t > duration - fade_duration:
            return (duration - t) / fade_duration  # Fade out
        else:
            return 1.0  # Fully visible

    @staticmethod
    def slide_in_from_bottom(t: float, duration: float, initial_y_offset: float = 0.1) -> float:
        """
        Calculates vertical offset for a slide-in-from-bottom animation.

        Args:
            t (float): Current time within the subtitle's active duration (0.0 to duration).
            duration (float): Total active duration of the subtitle.
            initial_y_offset (float): How much below the final position the subtitle starts (normalized).

        Returns:
            float: Normalized vertical offset (0.0 for final position, positive for lower).
        """
        animation_time = min(t, 0.5) # Animation happens in the first 0.5 seconds
        progress = animation_time / 0.5
        eased_progress = 1.0 - (1.0 - progress)**3 # Ease out cubic
        return initial_y_offset * (1.0 - eased_progress)

    @staticmethod
    def get_animation_function(animation_type: str) -> Callable[[float, float], float]:
        """
        Retrieves an animation function by type.

        Args:
            animation_type (str): The type of animation (e.g., 'fade_in_out', 'slide_in_from_bottom').

        Returns:
            Callable[[float, float], float]: The corresponding animation function.

        Raises:
            ValueError: If the animation type is not recognized.
        """
        if animation_type == 'fade_in_out':
            return SubtitleAnimation.fade_in_out
        elif animation_type == 'slide_in_from_bottom':
            return SubtitleAnimation.slide_in_from_bottom
        else:
            raise ValueError(f"Unknown subtitle animation type: {animation_type}")

if __name__ == "__main__":
    print("SubtitleAnimation provides animation logic. Rendering would be handled externally.")
    print("Example fade_in_out animation values:")
    duration = 3.0
    for i in range(31):
        t = i / 10.0
        if t <= duration:
            alpha = SubtitleAnimation.fade_in_out(t, duration)
            print(f"Time: {t:.1f}s, Alpha: {alpha:.2f}")

    print("\nExample slide_in_from_bottom animation values:")
    duration = 2.0
    for i in range(21):
        t = i / 10.0
        if t <= duration:
            offset = SubtitleAnimation.slide_in_from_bottom(t, duration)
            print(f"Time: {t:.1f}s, Y-Offset: {offset:.2f}")
