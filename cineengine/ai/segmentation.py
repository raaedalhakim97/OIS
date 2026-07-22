import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageSegmentation:
    """
    Performs image segmentation using a pre-trained deep learning model.
    """
    def __init__(self, model_name: str = "deeplabv3_resnet101", device: str = "cuda"):
        """
        Initializes the image segmentation model.

        Args:
            model_name (str): The name of the segmentation model to use (e.g., "deeplabv3_resnet101").
            device (str): The device to run the model on ("cuda" or "cpu").
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_name)
        self.model.to(self.device)
        self.model.eval()
        self.transform = T.Compose([
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        logger.info(f"Image Segmentation initialized with model: {model_name} on device: {self.device}")

    def _load_model(self, model_name: str):
        """
        Loads a pre-trained segmentation model from torchvision.
        """
        try:
            if model_name == "deeplabv3_resnet101":
                model = torch.hub.load("pytorch/vision:v0.10.0", "deeplabv3_resnet101", pretrained=True)
            elif model_name == "fcn_resnet101":
                model = torch.hub.load("pytorch/vision:v0.10.0", "fcn_resnet101", pretrained=True)
            else:
                raise ValueError(f"Unsupported segmentation model: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load segmentation model {model_name}: {e}")
            raise

    def segment_image(self, image_path: str) -> np.ndarray:
        """
        Segments the main object in an image and returns a binary mask.

        Args:
            image_path (str): Path to the input image file.

        Returns:
            np.ndarray: A binary mask (0s and 1s) representing the segmented object.
        """
        try:
            img = Image.open(image_path).convert("RGB")
            input_tensor = self.transform(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.model(input_tensor)["out"]
            
            # Get the predicted mask for the most prominent object (usually index 0 or 1 for background/foreground)
            # For DeepLabV3, the output is typically logits for each class.
            # We'll take the argmax to get the class with the highest score for each pixel.
            normalized_output = torch.nn.functional.softmax(output, dim=1)
            # Assuming the foreground object is typically class 1 (after background class 0)
            # This might need adjustment based on the specific model and desired object.
            mask = normalized_output.argmax(1).squeeze(0).cpu().numpy()

            # Create a binary mask for the main object (e.g., person, car, etc.)
            # This is a simplification; a more robust solution would involve class mapping.
            # For now, let's assume any non-background class is part of the foreground.
            # We'll create a mask where 1 represents foreground and 0 represents background.
            # The background class is typically 0 in most segmentation models.
            binary_mask = (mask != 0).astype(np.uint8)

            logger.info(f"Image segmented for {image_path}.")
            return binary_mask
        except Exception as e:
            logger.error(f"Error segmenting image {image_path}: {e}")
            raise

if __name__ == "__main__":
    # Example usage (requires a dummy image file)
    print("ImageSegmentation requires an image file to run. This is a placeholder example.")
    print("To test, create a dummy image.png and run:")
    print("    segmentor = ImageSegmentation(model_name=\"deeplabv3_resnet101\")")
    print("    mask = segmentor.segment_image(\"dummy_image.png\")")
    print("    print(f\"Mask shape: {mask.shape}\")")
    print("    # You can save the mask for visualization:")
    print("    # Image.fromarray((mask * 255).astype(np.uint8)).save(\"segmentation_mask.png\")")
