import logging
from typing import Optional
from PIL import Image

# Conditional import for diffusers and transformers
try:
    from diffusers import DiffusionPipeline
    from transformers import pipeline, set_seed
    _DIFFUSERS_AVAILABLE = True
except ImportError:
    _DIFFUSERS_AVAILABLE = False
    logging.warning("diffusers or transformers not found. AI image generation will be disabled.")

logger = logging.getLogger(__name__)

class AIImageGenerator:
    """
    Generates images from text prompts using a pre-trained diffusion model.
    """
    def __init__(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0", device: str = "cuda"):
        """
        Initializes the AI image generator.

        Args:
            model_id (str): The Hugging Face model ID for the diffusion pipeline.
            device (str): The device to run the model on ("cuda" or "cpu").
        """
        if not _DIFFUSERS_AVAILABLE:
            raise RuntimeError("diffusers and transformers libraries are required for AI image generation.")

        self.model_id = model_id
        self.device = device
        self.pipeline = None
        logger.info(f"AIImageGenerator initialized with model: {model_id} on device: {device} (model loading deferred).")

    def _load_pipeline(self):
        """
        Loads the diffusion pipeline if not already loaded.
        """
        if self.pipeline is None:
            try:
                logger.info(f"Loading diffusion pipeline: {self.model_id}...")
                self.pipeline = DiffusionPipeline.from_pretrained(self.model_id, torch_dtype=torch.float16)
                self.pipeline.to(self.device)
                logger.info("Diffusion pipeline loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load diffusion pipeline {self.model_id}: {e}")
                self.pipeline = None # Ensure pipeline is None on failure
                raise

    def generate_image(self, prompt: str, negative_prompt: Optional[str] = None, seed: Optional[int] = None) -> Image.Image:
        """
        Generates an image from a text prompt.

        Args:
            prompt (str): The text prompt to generate the image from.
            negative_prompt (str, optional): A prompt to guide the model away from certain concepts.
            seed (int, optional): Random seed for reproducible generation.

        Returns:
            PIL.Image.Image: The generated image.
        """
        self._load_pipeline()
        if self.pipeline is None:
            raise RuntimeError("AI image generation pipeline is not loaded.")

        if seed is not None:
            set_seed(seed)
            logger.debug(f"Set random seed for generation: {seed}")

        logger.info(f"Generating image for prompt: \'{prompt}\'...")
        try:
            image = self.pipeline(prompt=prompt, negative_prompt=negative_prompt).images[0]
            logger.info("Image generated successfully.")
            return image
        except Exception as e:
            logger.error(f"Error generating image for prompt \'{prompt}\': {e}")
            raise

if __name__ == "__main__":
    if _DIFFUSERS_AVAILABLE:
        print("AIImageGenerator requires a GPU and significant VRAM to run effectively.")
        print("This example will attempt to load a model and generate an image.")
        try:
            # Create a dummy image file for testing
            dummy_image_path = "dummy_image_for_ai_test.png"
            Image.new("RGB", (100, 100), color = "red").save(dummy_image_path)

            generator = AIImageGenerator()
            # Example prompt
            test_prompt = "A futuristic city at sunset, highly detailed, cyberpunk, neon lights"
            generated_image = generator.generate_image(test_prompt, seed=42)
            output_path = "generated_image.png"
            generated_image.save(output_path)
            print(f"Generated image saved to {output_path}")
        except RuntimeError as e:
            print(f"Error during AI image generation: {e}")
            print("Please ensure diffusers and transformers are installed and a compatible GPU is available.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print("Skipping AIImageGenerator example: diffusers or transformers not installed.")
