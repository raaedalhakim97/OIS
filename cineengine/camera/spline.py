
import numpy as np
from typing import List, Tuple

class BezierCurve:
    """
    Represents a Bezier curve defined by control points.
    """
    def __init__(self, control_points: List[Tuple[float, float]]):
        """
        Initializes a Bezier curve with a list of 2D control points.

        Args:
            control_points (List[Tuple[float, float]]): A list of (x, y) tuples representing the control points.
        """
        if len(control_points) < 2:
            raise ValueError("Bezier curve requires at least 2 control points.")
        self.control_points = np.array(control_points, dtype=float)
        self.degree = len(control_points) - 1

    def _bernstein_polynomial(self, n: int, i: int, t: float) -> float:
        """
        Calculates the i-th Bernstein polynomial of degree n at time t.

        Args:
            n (int): Degree of the polynomial.
            i (int): Index of the polynomial.
            t (float): Time parameter (0.0 to 1.0).

        Returns:
            float: The value of the Bernstein polynomial.
        """
        return (math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)))

    def get_point(self, t: float) -> Tuple[float, float]:
        """
        Evaluates the Bezier curve at a given time t.

        Args:
            t (float): Time parameter (0.0 to 1.0).

        Returns:
            Tuple[float, float]: The (x, y) coordinates on the curve at time t.
        """
        if not (0.0 <= t <= 1.0):
            raise ValueError("Time parameter t must be between 0.0 and 1.0.")

        point = np.zeros(2)
        for i in range(self.degree + 1):
            point += self.control_points[i] * self._bernstein_polynomial(self.degree, i, t)
        return tuple(point)


class CameraSpline:
    """
    Manages multiple Bezier curves for camera paths.
    """
    def __init__(self):
        """
        Initializes the CameraSpline manager.
        """
        self.curves: List[BezierCurve] = []

    def add_curve(self, control_points: List[Tuple[float, float]]) -> None:
        """
        Adds a new Bezier curve to the camera path.

        Args:
            control_points (List[Tuple[float, float]]): Control points for the new curve.
        """
        self.curves.append(BezierCurve(control_points))

    def get_position_on_path(self, curve_index: int, t: float) -> Tuple[float, float]:
        """
        Gets a point on a specific Bezier curve within the path.

        Args:
            curve_index (int): The index of the curve to evaluate.
            t (float): Time parameter (0.0 to 1.0) for the specific curve.

        Returns:
            Tuple[float, float]: The (x, y) coordinates on the specified curve.

        Raises:
            IndexError: If the curve_index is out of bounds.
        """
        if not (0 <= curve_index < len(self.curves)):
            raise IndexError(f"Curve index {curve_index} out of bounds. Available curves: {len(self.curves)}")
        return self.curves[curve_index].get_point(t)

    def get_total_duration(self) -> float:
        """
        Returns the total conceptual duration of the entire spline path (number of curves).
        """
        return float(len(self.curves))

    def get_global_position(self, global_t: float) -> Tuple[float, float]:
        """
        Gets a point on the overall camera path given a global time parameter.

        Args:
            global_t (float): Global time parameter, where each integer unit represents one curve.
                              e.g., 0.0-1.0 for the first curve, 1.0-2.0 for the second, etc.

        Returns:
            Tuple[float, float]: The (x, y) coordinates on the overall path.

        Raises:
            ValueError: If global_t is out of the valid range [0, total_duration].
        """
        total_duration = self.get_total_duration()
        if not (0.0 <= global_t <= total_duration):
            raise ValueError(f"Global time parameter global_t must be between 0.0 and {total_duration}.")

        if total_duration == 0:
            raise ValueError("No curves added to the spline.")

        curve_index = min(int(global_t), len(self.curves) - 1)
        local_t = global_t - curve_index

        return self.get_position_on_path(curve_index, local_t)
