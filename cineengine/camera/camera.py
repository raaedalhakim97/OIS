
import logging
from typing import Tuple, List

from cineengine.config import Config
from cineengine.camera.motion import CameraMotion

logger = logging.getLogger(__name__)

class Camera:
    """
    Manages the virtual camera within CineEngine, providing methods for cinematic movements.
    """
    def __init__(self, config: Config):
        """
        Initializes the Camera module.

        Args:
            config (Config): The CineEngine configuration object.
        """
        self.config = config
        self.motion = CameraMotion(config=self.config)
        logger.info("Camera module initialized.")

    def get_state(self, current_time: float) -> Tuple[Tuple[float, float], float]:
        """
        Retrieves the current position and zoom of the camera at a given time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            Tuple[Tuple[float, float], float]: A tuple containing (position_x, position_y) and zoom level.
        """
        return self.motion.update(current_time)

    def cinematic_push(self, duration: float = 5.0, start_zoom: float = 1.0, end_zoom: float = 1.2, start_time: float = 0.0) -> None:
        """
        Applies a cinematic push-in effect to the camera.

        Args:
            duration (float): Duration of the push effect in seconds.
            start_zoom (float): Initial zoom level.
            end_zoom (float): Final zoom level.
            start_time (float): The time at which this effect starts.
        """
        logger.info(f"Applying cinematic push: duration={duration}s, start_zoom={start_zoom}, end_zoom={end_zoom}")
        self.motion.set_target(
            zoom=end_zoom,
            duration=duration,
            start_time=start_time,
            easing='ease_in_out_cubic'
        )

    def cinematic_pull(self, duration: float = 5.0, start_zoom: float = 1.2, end_zoom: float = 1.0, start_time: float = 0.0) -> None:
        """
        Applies a cinematic pull-out effect to the camera.

        Args:
            duration (float): Duration of the pull effect in seconds.
            start_zoom (float): Initial zoom level.
            end_zoom (float): Final zoom level.
            start_time (float): The time at which this effect starts.
        """
        logger.info(f"Applying cinematic pull: duration={duration}s, start_zoom={start_zoom}, end_zoom={end_zoom}")
        self.motion.set_target(
            zoom=end_zoom,
            duration=duration,
            start_time=start_time,
            easing='ease_in_out_cubic'
        )

    def add_shake(self, intensity: float = None, frequency: float = None, seed: int = None) -> None:
        """
        Adds or updates camera shake.

        Args:
            intensity (float, optional): Intensity of the shake. Defaults to config value.
            frequency (float, optional): Frequency of the shake. Defaults to 1.0.
            seed (int, optional): Seed for the Perlin noise generator.
        """
        self.motion.reset_shake(intensity=intensity, frequency=frequency, seed=seed)
        logger.info(f"Camera shake added/updated with intensity={intensity}, frequency={frequency}")

    def add_bezier_path(self, control_points: List[Tuple[float, float]]) -> None:
        """
        Adds a Bezier curve to the camera's movement path.

        Args:
            control_points (List[Tuple[float, float]]): A list of (x, y) tuples representing the control points.
        """
        self.motion.add_spline_curve(control_points)
        logger.info(f"Bezier path added with {len(control_points)} control points.")

    # Example of a more complex cinematic movement
    def cinematic_dolly_zoom(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float], start_zoom: float, end_zoom: float, duration: float, start_time: float = 0.0) -> None:
        """
        Applies a dolly zoom (vertigo) effect.

        Args:
            start_pos (Tuple[float, float]): Starting camera position.
            end_pos (Tuple[float, float]): Ending camera position.
            start_zoom (float): Starting zoom level.
            end_zoom (float): Ending zoom level.
            duration (float): Duration of the effect in seconds.
            start_time (float): The time at which this effect starts.
        """
        logger.info(f"Applying cinematic dolly zoom: duration={duration}s, start_zoom={start_zoom}, end_zoom={end_zoom}")
        self.motion.set_target(
            position=end_pos,
            zoom=end_zoom,
            duration=duration,
            start_time=start_time,
            easing='linear' # Dolly zoom often uses linear movement for position and zoom
        )

