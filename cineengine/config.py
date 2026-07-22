
import logging

class Config:
    """Configuration settings for CineEngine."""

    # Video settings
    FPS: int = 30
    RESOLUTION: tuple[int, int] = (1080, 1920)  # Vertical video resolution (width, height)
    OUTPUT_DIR: str = "outputs"
    ASSETS_DIR: str = "assets"

    # Camera settings
    CAMERA_SPEED_MULTIPLIER: float = 1.0
    CAMERA_SHAKE_INTENSITY: float = 0.5

    # Effect settings
    BLOOM_THRESHOLD: float = 0.8
    GRAIN_INTENSITY: float = 0.05
    VIGNETTE_STRENGTH: float = 0.5
    CHROMATIC_ABERRATION_STRENGTH: float = 0.01
    DEPTH_OF_FIELD_STRENGTH: float = 0.1
    MOTION_BLUR_SAMPLES: int = 8

    # Audio settings
    AUDIO_VOLUME: float = 1.0
    BEAT_DETECTION_THRESHOLD: float = 0.8

    # AI settings
    MIDAS_MODEL_TYPE: str = "MiDaS_small"  # or "DPT_Hybrid", "DPT_Large"
    AI_IMAGE_GENERATION_MODEL: str = "stabilityai/stable-diffusion-xl-base-1.0"

    # Subtitle settings
    SUBTITLE_FONT: str = "Arial"
    SUBTITLE_FONT_SIZE: int = 48
    SUBTITLE_COLOR: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)  # RGBA white

    # Logging settings
    LOG_LEVEL = logging.INFO
    LOG_FILE: str = "cineengine.log"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key.upper()):
                setattr(self, key.upper(), value)
            else:
                logging.warning(f"Unknown configuration key: {key}")


# Initialize logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("CineEngine configuration loaded.")
