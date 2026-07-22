
import logging
import moderngl
from typing import Tuple, Optional

from cineengine.config import Config
from cineengine.effects.bloom import BloomEffect
from cineengine.effects.grain import FilmGrainEffect
from cineengine.effects.vignette import VignetteEffect
from cineengine.effects.chromatic import ChromaticAberrationEffect
from cineengine.effects.blur import BlurEffect
from cineengine.effects.dof import DepthOfFieldEffect
from cineengine.effects.glow import GlowEffect
from cineengine.effects.particles import ParticleSystem
from cineengine.effects.colorgrade import ColorGradeEffect

logger = logging.getLogger(__name__)

class Effects:
    """
    Manages and applies various visual effects to frames within CineEngine.
    """
    def __init__(self, config: Config, ctx: Optional[moderngl.Context] = None):
        """
        Initializes the Effects module.

        Args:
            config (Config): The CineEngine configuration object.
            ctx (moderngl.Context, optional): The ModernGL context. Required for shader-based effects.
        """
        self.config = config
        self.ctx = ctx
        self.resolution = config.RESOLUTION

        self.bloom_effect: Optional[BloomEffect] = None
        self.film_grain_effect: Optional[FilmGrainEffect] = None
        self.vignette_effect: Optional[VignetteEffect] = None
        self.chromatic_aberration_effect: Optional[ChromaticAberrationEffect] = None
        self.blur_effect: Optional[BlurEffect] = None
        self.dof_effect: Optional[DepthOfFieldEffect] = None
        self.glow_effect: Optional[GlowEffect] = None
        self.color_grade_effect: Optional[ColorGradeEffect] = None

        self.particle_systems: list[ParticleSystem] = []

        if self.ctx is None:
            logger.warning("ModernGL context not provided to Effects module. Shader-based effects will not be initialized.")
        else:
            logger.info("Effects module initialized with ModernGL context.")

    def _ensure_ctx(self):
        """
        Helper to ensure ModernGL context is available before initializing shader effects.
        """
        if self.ctx is None:
            raise RuntimeError("ModernGL context is not initialized. Cannot apply shader-based effects.")

    def bloom(self, threshold: Optional[float] = None) -> None:
        """
        Enables and configures the bloom effect.

        Args:
            threshold (float, optional): Pixels brighter than this threshold will contribute to bloom.
        """
        self._ensure_ctx()
        if self.bloom_effect is None:
            self.bloom_effect = BloomEffect(self.ctx, self.resolution, threshold or self.config.BLOOM_THRESHOLD)
            logger.info(f"Bloom effect enabled with threshold: {self.bloom_effect.threshold}")
        else:
            self.bloom_effect.threshold = threshold or self.config.BLOOM_THRESHOLD
            logger.info(f"Bloom effect updated with threshold: {self.bloom_effect.threshold}")

    def film_grain(self, intensity: Optional[float] = None) -> None:
        """
        Enables and configures the film grain effect.

        Args:
            intensity (float, optional): The intensity of the film grain effect.
        """
        self._ensure_ctx()
        if self.film_grain_effect is None:
            self.film_grain_effect = FilmGrainEffect(self.ctx, self.resolution, intensity or self.config.GRAIN_INTENSITY)
            logger.info(f"Film grain effect enabled with intensity: {self.film_grain_effect.intensity}")
        else:
            self.film_grain_effect.intensity = intensity or self.config.GRAIN_INTENSITY
            logger.info(f"Film grain effect updated with intensity: {self.film_grain_effect.intensity}")

    def vignette(self, strength: Optional[float] = None) -> None:
        """
        Enables and configures the vignette effect.

        Args:
            strength (float, optional): The intensity of the vignette effect.
        """
        self._ensure_ctx()
        if self.vignette_effect is None:
            self.vignette_effect = VignetteEffect(self.ctx, self.resolution, strength or self.config.VIGNETTE_STRENGTH)
            logger.info(f"Vignette effect enabled with strength: {self.vignette_effect.strength}")
        else:
            self.vignette_effect.strength = strength or self.config.VIGNETTE_STRENGTH
            logger.info(f"Vignette effect updated with strength: {self.vignette_effect.strength}")

    def chromatic_aberration(self, strength: Optional[float] = None) -> None:
        """
        Enables and configures the chromatic aberration effect.

        Args:
            strength (float, optional): The intensity of the chromatic aberration effect.
        """
        self._ensure_ctx()
        if self.chromatic_aberration_effect is None:
            self.chromatic_aberration_effect = ChromaticAberrationEffect(self.ctx, self.resolution, strength or self.config.CHROMATIC_ABERRATION_STRENGTH)
            logger.info(f"Chromatic aberration effect enabled with strength: {self.chromatic_aberration_effect.strength}")
        else:
            self.chromatic_aberration_effect.strength = strength or self.config.CHROMATIC_ABERRATION_STRENGTH
            logger.info(f"Chromatic aberration effect updated with strength: {self.chromatic_aberration_effect.strength}")

    def blur(self, radius: int = 5) -> None:
        """
        Enables and configures a general blur effect.

        Args:
            radius (int): The radius of the Gaussian blur kernel.
        """
        self._ensure_ctx()
        if self.blur_effect is None:
            self.blur_effect = BlurEffect(self.ctx, self.resolution, radius)
            logger.info(f"Blur effect enabled with radius: {self.blur_effect.radius}")
        else:
            self.blur_effect.radius = radius
            logger.info(f"Blur effect updated with radius: {self.blur_effect.radius}")

    def depth_of_field(self, strength: Optional[float] = None, focal_distance: float = 0.5, focal_range: float = 0.2) -> None:
        """
        Enables and configures the Depth of Field effect.

        Args:
            strength (float, optional): The overall strength of the DoF blur.
            focal_distance (float): Normalized distance (0.0 to 1.0) to the focal plane.
            focal_range (float): Normalized range (0.0 to 1.0) around the focal distance that is in focus.
        """
        self._ensure_ctx()
        if self.dof_effect is None:
            self.dof_effect = DepthOfFieldEffect(self.ctx, self.resolution, strength or self.config.DEPTH_OF_FIELD_STRENGTH, focal_distance, focal_range)
            logger.info(f"Depth of Field effect enabled with strength: {self.dof_effect.strength}, focal_distance: {self.dof_effect.focal_distance}, focal_range: {self.dof_effect.focal_range}")
        else:
            self.dof_effect.strength = strength or self.config.DEPTH_OF_FIELD_STRENGTH
            self.dof_effect.focal_distance = focal_distance
            self.dof_effect.focal_range = focal_range
            logger.info(f"Depth of Field effect updated with strength: {self.dof_effect.strength}, focal_distance: {self.dof_effect.focal_distance}, focal_range: {self.dof_effect.focal_range}")

    def glow(self, threshold: Optional[float] = None, blur_radius: Optional[int] = None) -> None:
        """
        Enables and configures the glow effect.

        Args:
            threshold (float, optional): Pixels brighter than this threshold will contribute to glow.
            blur_radius (int, optional): The radius for the Gaussian blur applied to the glow.
        """
        self._ensure_ctx()
        if self.glow_effect is None:
            self.glow_effect = GlowEffect(self.ctx, self.resolution, threshold or self.config.BLOOM_THRESHOLD, blur_radius or 5) # Reusing bloom threshold for glow
            logger.info(f"Glow effect enabled with threshold: {self.glow_effect.threshold}, blur_radius: {self.glow_effect.blur_radius}")
        else:
            self.glow_effect.threshold = threshold or self.config.BLOOM_THRESHOLD
            self.glow_effect.blur_radius = blur_radius or 5
            logger.info(f"Glow effect updated with threshold: {self.glow_effect.threshold}, blur_radius: {self.glow_effect.blur_radius}")

    def add_particle_system(
        self,
        max_particles: int = 1000,
        emission_rate: float = 10.0,
        particle_lifetime: Tuple[float, float] = (1.0, 3.0),
        particle_size: Tuple[float, float] = (0.01, 0.05),
        particle_velocity: Tuple[float, float] = (0.5, 2.0),
        particle_color_start: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        particle_color_end: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.0),
        gravity: Tuple[float, float, float] = (0.0, -9.8, 0.0)
    ) -> ParticleSystem:
        """
        Adds and returns a new particle system.
        """
        system = ParticleSystem(
            max_particles=max_particles,
            emission_rate=emission_rate,
            particle_lifetime=particle_lifetime,
            particle_size=particle_size,
            particle_velocity=particle_velocity,
            particle_color_start=particle_color_start,
            particle_color_end=particle_color_end,
            gravity=gravity
        )
        self.particle_systems.append(system)
        logger.info(f"Added a new particle system. Total systems: {len(self.particle_systems)}")
        return system

    def color_grade(self) -> None:
        """
        Enables ACES Filmic tone mapping.
        """
        self._ensure_ctx()
        if self.color_grade_effect is None:
            self.color_grade_effect = ColorGradeEffect(self.ctx, self.resolution)
            logger.info("ACES Filmic tone mapping enabled.")

    def apply_effects(self, original_texture: moderngl.Texture, current_time: float) -> moderngl.Texture:
        """
        Applies all enabled effects to the given texture in a specific order.

        Args:
            original_texture (moderngl.Texture): The input texture to apply effects to.
            current_time (float): The current time in seconds, used for time-dependent effects.

        Returns:
            moderngl.Texture: The texture with all enabled effects applied.
        """
        processed_texture = original_texture

        # Order of effects can be important. A common order is:
        # 1. Depth of Field / Blur
        # 2. Bloom / Glow
        # 3. Chromatic Aberration
        # 4. Film Grain
        # 5. Vignette
        # 6. Color Grading (Tone Mapping)

        if self.dof_effect:
            processed_texture = self.dof_effect.apply(processed_texture)
        if self.blur_effect:
            processed_texture = self.blur_effect.apply(processed_texture)
        if self.bloom_effect:
            processed_texture = self.bloom_effect.apply(processed_texture)
        if self.glow_effect:
            processed_texture = self.glow_effect.apply(processed_texture)
        if self.chromatic_aberration_effect:
            processed_texture = self.chromatic_aberration_effect.apply(processed_texture)

        # Particle systems are rendered separately, not directly applied to a texture here.
        # Their output would be composited later in the renderer.
        for ps in self.particle_systems:
            ps.update(1.0 / self.config.FPS, emitter_position=(0.0, 0.0, 0.0)) # Placeholder emitter position

        if self.film_grain_effect:
            processed_texture = self.film_grain_effect.apply(processed_texture, current_time)
        if self.vignette_effect:
            processed_texture = self.vignette_effect.apply(processed_texture)
        if self.color_grade_effect:
            processed_texture = self.color_grade_effect.apply(processed_texture)

        return processed_texture

    def release(self):
        """
        Releases all ModernGL resources held by the effects.
        """
        if self.bloom_effect: self.bloom_effect.release()
        if self.film_grain_effect: self.film_grain_effect.release()
        if self.vignette_effect: self.vignette_effect.release()
        if self.chromatic_aberration_effect: self.chromatic_aberration_effect.release()
        if self.blur_effect: self.blur_effect.release()
        if self.dof_effect: self.dof_effect.release()
        if self.glow_effect: self.glow_effect.release()
        if self.color_grade_effect: self.color_grade_effect.release()
        logger.info("All effect resources released.")
