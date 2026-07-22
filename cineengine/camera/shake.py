
import numpy as np
from typing import Tuple

class PerlinNoise:
    """
    Generates 1D Perlin noise.
    """
    def __init__(self, seed: int = None):
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
        self.permutations = np.arange(256, dtype=int)
        np.random.shuffle(self.permutations)
        self.permutations = np.stack([self.permutations, self.permutations]).flatten()

    def _fade(self, t: float) -> float:
        """
        6t^5 - 15t^4 + 10t^3
        """
        return 6 * t**5 - 15 * t**4 + 10 * t**3

    def _gradient(self, hash_val: int, x: float) -> float:
        """
        Returns a random gradient vector based on hash_val.
        """
        h = hash_val & 0xF
        grad = 1 + (h & 7)  # Gradient value from 1 to 8
        if h & 8:  # Randomly negate half of them
            grad = -grad
        return grad * x

    def get_noise(self, x: float) -> float:
        """
        Generates Perlin noise for a given x coordinate.

        Args:
            x (float): The x coordinate for noise generation.

        Returns:
            float: The Perlin noise value.
        """
        xi = int(x) & 255
        xf = x - int(x)
        u = self._fade(xf)

        hash_val_0 = self.permutations[xi]
        hash_val_1 = self.permutations[xi + 1]

        grad_0 = self._gradient(hash_val_0, xf)
        grad_1 = self._gradient(hash_val_1, xf - 1)

        return grad_0 * (1 - u) + grad_1 * u


class CameraShake:
    """
    Applies Perlin noise-based camera shake.
    """
    def __init__(self, intensity: float = 0.5, frequency: float = 1.0, seed: int = None):
        """
        Initializes the CameraShake.

        Args:
            intensity (float): The maximum displacement of the shake.
            frequency (float): How fast the shake oscillates.
            seed (int, optional): Seed for the random number generator. Defaults to None.
        """
        self.intensity = intensity
        self.frequency = frequency
        self.noise_x = PerlinNoise(seed=seed)
        self.noise_y = PerlinNoise(seed=seed + 1 if seed is not None else None)

    def get_shake_offset(self, time: float) -> Tuple[float, float]:
        """
        Calculates the camera shake offset for a given time.

        Args:
            time (float): Current time in seconds.

        Returns:
            Tuple[float, float]: (offset_x, offset_y) for camera shake.
        """
        offset_x = self.noise_x.get_noise(time * self.frequency) * self.intensity
        offset_y = self.noise_y.get_noise(time * self.frequency + 1000) * self.intensity # Offset y noise to be different
        return offset_x, offset_y
