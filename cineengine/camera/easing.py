
import math
from typing import Callable

def ease_in_out_cubic(t: float) -> float:
    """
    Cubic ease-in-out function.

    Args:
        t (float): Normalized time (0.0 to 1.0).

    Returns:
        float: Eased value.
    """
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def linear(t: float) -> float:
    """
    Linear easing function.

    Args:
        t (float): Normalized time (0.0 to 1.0).

    Returns:
        float: Eased value.
    """
    return t

# Add more easing functions as needed

class Easing:
    """
    A collection of static easing functions.
    """
    @staticmethod
    def get_easing_function(name: str) -> Callable[[float], float]:
        """
        Retrieves an easing function by name.

        Args:
            name (str): The name of the easing function (e.g., 'ease_in_out_cubic', 'linear').

        Returns:
            Callable[[float], float]: The corresponding easing function.

        Raises:
            ValueError: If the easing function name is not recognized.
        """
        if name == 'ease_in_out_cubic':
            return ease_in_out_cubic
        elif name == 'linear':
            return linear
        else:
            raise ValueError(f"Unknown easing function: {name}")
