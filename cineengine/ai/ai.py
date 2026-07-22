
import logging
from typing import Optional, List, Tuple

from cineengine.config import Config
from cineengine.ai.depth import MiDaSDepthEstimator
from cineengine.ai.segmentation import ImageSegmentation
from cineengine.ai.opticalflow import OpticalFlowEstimator
from cineengine.ai.caption import CaptionGenerator
from cineengine.ai.story import StoryGenerator
from cineengine.ai.prompt import PromptGenerator
from cineengine.ai.image import AIImageGenerator

logger = logging.getLogger(__name__)

class AI:
    """
    Manages AI-powered functionalities within CineEngine, including depth estimation, segmentation,
    optical flow, captioning, story generation, prompt generation, and image generation.
    """
    def __init__(self, config: Config):
        """
        Initializes the AI module.

        Args:
            config (Config): The CineEngine configuration object.
        """
        self.config = config

        self.depth_estimator: Optional[MiDaSDepthEstimator] = None
        self.segmentor: Optional[ImageSegmentation] = None
        self.optical_flow_estimator: Optional[OpticalFlowEstimator] = None
        self.caption_generator: Optional[CaptionGenerator] = None
        self.story_generator: Optional[StoryGenerator] = None
        self.prompt_generator: Optional[PromptGenerator] = None
        self.image_generator: Optional[AIImageGenerator] = None

        logger.info("AI module initialized.")

    def get_depth_estimator(self) -> MiDaSDepthEstimator:
        """
        Lazily initializes and returns the MiDaS Depth Estimator.
        """
        if self.depth_estimator is None:
            self.depth_estimator = MiDaSDepthEstimator(model_type=self.config.MIDAS_MODEL_TYPE)
        return self.depth_estimator

    def get_segmentor(self, model_name: str = "deeplabv3_resnet101") -> ImageSegmentation:
        """
        Lazily initializes and returns the Image Segmentor.
        """
        if self.segmentor is None:
            self.segmentor = ImageSegmentation(model_name=model_name)
        return self.segmentor

    def get_optical_flow_estimator(self) -> OpticalFlowEstimator:
        """
        Lazily initializes and returns the Optical Flow Estimator.
        """
        if self.optical_flow_estimator is None:
            self.optical_flow_estimator = OpticalFlowEstimator()
        return self.optical_flow_estimator

    def get_caption_generator(self, model_name: str = "Salesforce/blip-image-captioning-base") -> CaptionGenerator:
        """
        Lazily initializes and returns the Caption Generator.
        """
        if self.caption_generator is None:
            self.caption_generator = CaptionGenerator(model_name=model_name)
        return self.caption_generator

    def get_story_generator(self, model_name: str = "gpt-3.5-turbo") -> StoryGenerator:
        """
        Lazily initializes and returns the Story Generator.
        """
        if self.story_generator is None:
            self.story_generator = StoryGenerator(model_name=model_name)
        return self.story_generator

    def get_prompt_generator(self, model_name: str = "gpt-3.5-turbo") -> PromptGenerator:
        """
        Lazily initializes and returns the Prompt Generator.
        """
        if self.prompt_generator is None:
            self.prompt_generator = PromptGenerator(model_name=model_name)
        return self.prompt_generator

    def get_image_generator(self, model_id: Optional[str] = None) -> AIImageGenerator:
        """
        Lazily initializes and returns the AI Image Generator.
        """
        if self.image_generator is None:
            self.image_generator = AIImageGenerator(model_id=model_id or self.config.AI_IMAGE_GENERATION_MODEL)
        return self.image_generator

    # Convenience methods for direct access
    def estimate_depth(self, image_path: str) -> np.ndarray:
        """
        Estimates the depth map for a given image.
        """
        return self.get_depth_estimator().estimate_depth(image_path)

    def segment_image(self, image_path: str) -> np.ndarray:
        """
        Segments the main object in an image.
        """
        return self.get_segmentor().segment_image(image_path)

    def generate_caption(self, image_path: str) -> str:
        """
        Generates a caption for a given image.
        """
        return self.get_caption_generator().generate_caption(image_path)

    def generate_image(self, prompt: str, negative_prompt: Optional[str] = None, seed: Optional[int] = None) -> Image.Image:
        """
        Generates an image from a text prompt.
        """
        return self.get_image_generator().generate_image(prompt, negative_prompt, seed)

    def generate_story_from_images(self, image_descriptions: List[str]) -> str:
        """
        Generates a story based on a sequence of image descriptions.
        """
        return self.get_story_generator().generate_story_from_images(image_descriptions)

    def generate_image_prompt(self, theme: str, style: str = "cinematic, highly detailed, 8k") -> str:
        """
        Generates a detailed image generation prompt based on a theme and style.
        """
        return self.get_prompt_generator().generate_image_prompt(theme, style)

    def estimate_optical_flow(self, prev_frame: np.ndarray, next_frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Estimates dense optical flow between two consecutive frames.
        """
        return self.get_optical_flow_estimator().estimate_flow(prev_frame, next_frame)

