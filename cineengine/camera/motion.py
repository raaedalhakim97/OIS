
import numpy as np
from typing import Tuple, Callable

from cineengine.camera.easing import Easing
from cineengine.camera.shake import CameraShake
from cineengine.camera.spline import CameraSpline

class CameraMotion:
    """
    Manages the overall motion of the virtual camera, combining various movement types.
    """
    def __init__(
        self,
        start_position: Tuple[float, float] = (0.0, 0.0),
        start_zoom: float = 1.0,
        config=None
    ):
        """
        Initializes the CameraMotion manager.

        Args:
            start_position (Tuple[float, float]): Initial (x, y) position of the camera.
            start_zoom (float): Initial zoom level of the camera.
            config: Configuration object for CineEngine.
        """
        self._current_position = np.array(start_position, dtype=float)
        self._current_zoom = start_zoom
        self._target_position = np.array(start_position, dtype=float)
        self._target_zoom = start_zoom
        self._motion_duration = 0.0
        self._motion_start_time = 0.0
        self._easing_function: Callable[[float], float] = Easing.get_easing_function('linear')

        self.camera_shake: CameraShake = CameraShake(intensity=config.CAMERA_SHAKE_INTENSITY) if config else CameraShake()
        self.camera_spline: CameraSpline = CameraSpline()

    def set_target(
        self,
        position: Tuple[float, float] = None,
        zoom: float = None,
        duration: float = 1.0,
        start_time: float = 0.0,
        easing: str = 'linear'
    ) -> None:
        """
        Sets a new target for camera position and zoom with a specified duration and easing.

        Args:
            position (Tuple[float, float], optional): New target (x, y) position. If None, current position is maintained.
            zoom (float, optional): New target zoom level. If None, current zoom is maintained.
            duration (float): Duration of the movement in seconds.
            start_time (float): The time at which this motion starts.
            easing (str): Name of the easing function to use (e.g., 'ease_in_out_cubic', 'linear').
        """
        if position is not None:
            self._target_position = np.array(position, dtype=float)
        else:
            self._target_position = self._current_position.copy()

        if zoom is not None:
            self._target_zoom = zoom
        else:
            self._target_zoom = self._current_zoom

        self._motion_duration = duration
        self._motion_start_time = start_time
        self._easing_function = Easing.get_easing_function(easing)

    def update(self, current_time: float) -> Tuple[Tuple[float, float], float]:
        """
        Updates the camera's position and zoom based on the current time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            Tuple[Tuple[float, float], float]: The updated (position_x, position_y) and zoom level.
        """
        # Apply motion along spline if any
        spline_offset_x, spline_offset_y = (0.0, 0.0)
        if len(self.camera_spline.curves) > 0:
            try:
                spline_pos = self.camera_spline.get_global_position(current_time)
                spline_offset_x, spline_offset_y = spline_pos
            except ValueError:
                # global_t out of range, camera is off the spline or spline is too short
                pass

        # Apply programmed motion (position and zoom targets)
        if current_time < self._motion_start_time:
            # Before motion starts, stay at the initial state
            eased_t = 0.0
            interpolated_position = self._current_position
            interpolated_zoom = self._current_zoom
        elif current_time >= self._motion_start_time + self._motion_duration:
            # After motion ends, stay at the target state
            eased_t = 1.0
            interpolated_position = self._target_position
            interpolated_zoom = self._target_zoom
        else:
            # During motion, interpolate
            t = (current_time - self._motion_start_time) / self._motion_duration
            eased_t = self._easing_function(t)

            interpolated_position = self._current_position + (self._target_position - self._current_position) * eased_t
            interpolated_zoom = self._current_zoom + (self._target_zoom - self._current_zoom) * eased_t

        # Apply camera shake
        shake_offset_x, shake_offset_y = self.camera_shake.get_shake_offset(current_time)

        final_position_x = interpolated_position[0] + shake_offset_x + spline_offset_x
        final_position_y = interpolated_position[1] + shake_offset_y + spline_offset_y
        final_zoom = interpolated_zoom

        return (final_position_x, final_position_y), final_zoom

    def get_current_state(self) -> Tuple[Tuple[float, float], float]:
        """
        Returns the current position and zoom of the camera.
        """
        return tuple(self._current_position), self._current_zoom

    def reset_shake(self, intensity: float = None, frequency: float = None, seed: int = None) -> None:
        """
        Resets or updates the camera shake parameters.
        """
        if intensity is not None: self.camera_shake.intensity = intensity
        if frequency is not None: self.camera_shake.frequency = frequency
        # Re-initialize Perlin noise if seed is provided
        if seed is not None:
            self.camera_shake = CameraShake(self.camera_shake.intensity, self.camera_shake.frequency, seed)

    def add_spline_curve(self, control_points: List[Tuple[float, float]]) -> None:
        """
        Adds a Bezier curve to the camera spline.
        """
        self.camera_spline.add_curve(control_points)

