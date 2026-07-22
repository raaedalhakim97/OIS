import cv2
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class OpticalFlowEstimator:
    """
    Estimates optical flow between two consecutive frames.
    """
    def __init__(self):
        """
        Initializes the OpticalFlowEstimator.
        """
        # Parameters for Lucas-Kanade optical flow
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        # Parameters for ShiTomasi corner detection
        self.feature_params = dict(
            maxCorners=100,
            qualityLevel=0.3,
            minDistance=7,
            blockSize=7
        )
        logger.info("OpticalFlowEstimator initialized.")

    def estimate_flow(self, prev_frame: np.ndarray, next_frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Estimates dense optical flow using Farneback method.

        Args:
            prev_frame (np.ndarray): The previous frame (grayscale).
            next_frame (np.ndarray): The next frame (grayscale).

        Returns:
            np.ndarray: A 2-channel array of flow vectors (dx, dy) or None if an error occurs.
        """
        try:
            # Ensure frames are grayscale
            if len(prev_frame.shape) == 3: # If RGB, convert to grayscale
                prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            else:
                prev_frame_gray = prev_frame

            if len(next_frame.shape) == 3: # If RGB, convert to grayscale
                next_frame_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
            else:
                next_frame_gray = next_frame

            # Calculate dense optical flow using Farneback method
            flow = cv2.calcOpticalFlowFarneback(
                prev_frame_gray,
                next_frame_gray,
                None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            logger.debug("Dense optical flow estimated.")
            return flow
        except Exception as e:
            logger.error(f"Error estimating dense optical flow: {e}")
            return None

    def visualize_flow(self, flow: np.ndarray, frame: np.ndarray) -> np.ndarray:
        """
        Visualizes the optical flow as an HSV image.

        Args:
            flow (np.ndarray): The 2-channel array of flow vectors (dx, dy).
            frame (np.ndarray): The original frame to overlay the flow visualization on.

        Returns:
            np.ndarray: An RGB image with flow vectors visualized.
        """
        h, w = flow.shape[:2]
        hsv = np.zeros((h, w, 3), dtype=np.uint8)
        hsv[..., 1] = 255

        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv[..., 0] = ang * 180 / np.pi / 2
        hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # Overlay flow visualization on the original frame
        # Ensure the original frame is in BGR format for blending
        if len(frame.shape) == 2: # Grayscale
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        else:
            frame_bgr = frame

        # Blend the flow visualization with the original frame
        blended_frame = cv2.addWeighted(frame_bgr, 0.7, rgb, 0.3, 0)
        return blended_frame

if __name__ == "__main__":
    print("OpticalFlowEstimator requires two image frames to run. This is a placeholder example.")
    print("To test, you would typically load two consecutive frames (e.g., from a video) and run:")
    print("    estimator = OpticalFlowEstimator()")
    print("    # prev_frame = cv2.imread(\"frame000.png\")")
    print("    # next_frame = cv2.imread(\"frame001.png\")")
    print("    # flow = estimator.estimate_flow(prev_frame, next_frame)")
    print("    # if flow is not None:")
    print("    #     flow_viz = estimator.visualize_flow(flow, next_frame)")
    print("    #     cv2.imwrite(\"flow_visualization.png\", flow_viz)")
