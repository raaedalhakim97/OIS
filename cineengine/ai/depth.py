import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MiDaSDepthEstimator:
    """
    Estimates depth maps from images using the MiDaS model.
    """
    def __init__(self, model_type: str = "MiDaS_small", device: str = "cuda"):
        """
        Initializes the MiDaS depth estimator.

        Args:
            model_type (str): The MiDaS model variant to use (e.g., "MiDaS_small", "DPT_Hybrid", "DPT_Large").
            device (str): The device to run the model on ("cuda" or "cpu").
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model_type = model_type
        self.model, self.transform = self._load_midas_model(model_type)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"MiDaS Depth Estimator initialized with model: {model_type} on device: {self.device}")

    def _load_midas_model(self, model_type: str):
        """
        Loads the MiDaS model and its corresponding transform.
        """
        try:
            midas = torch.hub.load("intel-isl/MiDaS", model_type)

            # Load transforms to resize and normalize the image
            # according to the model requirements.
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            transform = midas_transforms.dpt_transform if model_type == "DPT_Large" or model_type == "DPT_Hybrid" else midas_transforms.small_transform

            return midas, transform
        except Exception as e:
            logger.error(f"Failed to load MiDaS model {model_type}: {e}")
            raise

    def estimate_depth(self, image_path: str) -> np.ndarray:
        """
        Estimates the depth map for a given image.

        Args:
            image_path (str): Path to the input image file.

        Returns:
            np.ndarray: A normalized depth map (values between 0 and 1).
        """
        try:
            img = Image.open(image_path).convert("RGB")
            input_batch = self.transform(img).to(self.device)

            with torch.no_grad():
                prediction = self.model(input_batch)

                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img.shape[0:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()

            depth_map = prediction.cpu().numpy()

            # Normalize depth map to 0-1 range
            min_depth = depth_map.min()
            max_depth = depth_map.max()
            normalized_depth_map = (depth_map - min_depth) / (max_depth - min_depth)

            logger.info(f"Depth map estimated for {image_path}.")
            return normalized_depth_map
        except Exception as e:
            logger.error(f"Error estimating depth for {image_path}: {e}")
            raise

if __name__ == "__main__":
    # Example usage (requires a dummy image file)
    print("MiDaSDepthEstimator requires an image file to run. This is a placeholder example.")
    print("To test, create a dummy image.png and run:")
    print("    estimator = MiDaSDepthEstimator(model_type=\"MiDaS_small\")")
    print("    depth_map = estimator.estimate_depth(\"dummy_image.png\")")
    print("    print(f\"Depth map shape: {depth_map.shape}\")")
    print("    # You can save the depth map for visualization:")
    print("    # Image.fromarray((depth_map * 255).astype(np.uint8)).save(\"depth_map.png\")")
