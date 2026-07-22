
import numpy as np
from typing import List, Tuple, Optional

class Particle:
    """
    Represents a single particle with its properties.
    """
    def __init__(
        self,
        position: Tuple[float, float, float],
        velocity: Tuple[float, float, float],
        color: Tuple[float, float, float, float],
        size: float,
        lifetime: float,
        mass: float = 1.0
    ):
        """
        Initializes a particle.

        Args:
            position (Tuple[float, float, float]): Initial (x, y, z) position.
            velocity (Tuple[float, float, float]): Initial (vx, vy, vz) velocity.
            color (Tuple[float, float, float, float]): Initial (r, g, b, a) color.
            size (float): Initial size of the particle.
            lifetime (float): How long the particle will live in seconds.
            mass (float): Mass of the particle, affecting physics.
        """
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.color = np.array(color, dtype=float)
        self.size = size
        self.lifetime = lifetime
        self.mass = mass
        self.age = 0.0
        self.is_alive = True

    def update(self, dt: float, gravity: Tuple[float, float, float] = (0.0, -9.8, 0.0)) -> None:
        """
        Updates the particle's state based on time elapsed.

        Args:
            dt (float): Time elapsed since the last update in seconds.
            gravity (Tuple[float, float, float]): Gravity vector to apply.
        """
        if not self.is_alive:
            return

        self.age += dt
        if self.age >= self.lifetime:
            self.is_alive = False
            return

        # Apply gravity (simple integration)
        self.velocity += np.array(gravity) * dt

        # Update position
        self.position += self.velocity * dt

        # Fade out color based on age
        self.color[3] = (1.0 - self.age / self.lifetime) # Alpha fades from 1 to 0

class ParticleSystem:
    """
    Manages a collection of particles, their emission, and updates.
    """
    def __init__(
        self,
        max_particles: int = 1000,
        emission_rate: float = 10.0, # particles per second
        particle_lifetime: Tuple[float, float] = (1.0, 3.0), # min, max lifetime
        particle_size: Tuple[float, float] = (0.01, 0.05), # min, max size
        particle_velocity: Tuple[float, float] = (0.5, 2.0), # min, max speed
        particle_color_start: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        particle_color_end: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.0),
        gravity: Tuple[float, float, float] = (0.0, -9.8, 0.0)
    ):
        """
        Initializes the particle system.

        Args:
            max_particles (int): Maximum number of particles in the system.
            emission_rate (float): Number of particles emitted per second.
            particle_lifetime (Tuple[float, float]): Min and max lifetime of particles.
            particle_size (Tuple[float, float]): Min and max size of particles.
            particle_velocity (Tuple[float, float]): Min and max initial speed of particles.
            particle_color_start (Tuple[float, float, float, float]): Starting RGBA color.
            particle_color_end (Tuple[float, float, float, float]): Ending RGBA color.
            gravity (Tuple[float, float, float]): Gravity vector.
        """
        self.max_particles = max_particles
        self.emission_rate = emission_rate
        self.particle_lifetime = particle_lifetime
        self.particle_size = particle_size
        self.particle_velocity = particle_velocity
        self.particle_color_start = np.array(particle_color_start)
        self.particle_color_end = np.array(particle_color_end)
        self.gravity = gravity

        self.particles: List[Particle] = []
        self._time_since_last_emission = 0.0

    def _emit_particle(self, position: Tuple[float, float, float]) -> Particle:
        """
        Creates and returns a new particle.
        """
        lifetime = np.random.uniform(*self.particle_lifetime)
        size = np.random.uniform(*self.particle_size)

        # Random velocity direction and speed
        speed = np.random.uniform(*self.particle_velocity)
        direction = np.random.normal(size=3)
        direction /= np.linalg.norm(direction) # Normalize to unit vector
        velocity = direction * speed

        return Particle(
            position=position,
            velocity=tuple(velocity),
            color=tuple(self.particle_color_start),
            size=size,
            lifetime=lifetime
        )

    def update(self, dt: float, emitter_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> None:
        """
        Updates all particles in the system and emits new ones.

        Args:
            dt (float): Time elapsed since the last update in seconds.
            emitter_position (Tuple[float, float, float]): The position from which new particles are emitted.
        """
        # Emit new particles
        self._time_since_last_emission += dt
        particles_to_emit = int(self._time_since_last_emission * self.emission_rate)
        self._time_since_last_emission -= particles_to_emit / self.emission_rate

        for _ in range(particles_to_emit):
            if len(self.particles) < self.max_particles:
                self.particles.append(self._emit_particle(emitter_position))
            else:
                # Try to replace a dead particle if max_particles is reached
                for i, p in enumerate(self.particles):
                    if not p.is_alive:
                        self.particles[i] = self._emit_particle(emitter_position)
                        break

        # Update existing particles
        for particle in self.particles:
            particle.update(dt, self.gravity)

        # Remove dead particles (optional, if not replacing them)
        self.particles = [p for p in self.particles if p.is_alive]

    def get_active_particles(self) -> List[Particle]:
        """
        Returns a list of currently active (alive) particles.
        """
        return [p for p in self.particles if p.is_alive]


# Example usage
if __name__ == "__main__":
    print("ParticleSystem provides the logic for particles. Rendering would be handled externally.")
    print("Example simulation:")

    system = ParticleSystem(
        max_particles=100,
        emission_rate=20.0,
        particle_lifetime=(1.0, 2.0),
        gravity=(0.0, -5.0, 0.0)
    )

    total_time = 3.0
    dt = 0.1
    current_time = 0.0

    while current_time < total_time:
        system.update(dt, emitter_position=(0.0, 0.0, 0.0))
        print(f"Time: {current_time:.1f}s, Active particles: {len(system.get_active_particles())}")
        # In a real application, you would render these particles here
        current_time += dt

    print("Particle system simulation finished.")
