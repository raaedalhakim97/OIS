
import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TextRenderer:
    """
    Renders text onto a texture using PIL and then uploads it to ModernGL.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int]):
        """
        Initializes the TextRenderer.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the target framebuffer (width, height).
        """
        self.ctx = ctx
        self.width, self.height = resolution
        logger.info(f"TextRenderer initialized for resolution: {resolution}")

    def render_text_to_texture(
        self,
        text: str,
        font_path: str,
        font_size: int,
        color: Tuple[float, float, float, float],
        background_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0), # Transparent background
        padding: int = 10
    ) -> moderngl.Texture:
        """
        Renders text to a PIL image and converts it to a ModernGL texture.

        Args:
            text (str): The text string to render.
            font_path (str): Path to the font file (e.g., .ttf).
            font_size (int): Size of the font.
            color (Tuple[float, float, float, float]): RGBA color of the text.
            background_color (Tuple[float, float, float, float]): RGBA color of the background.
            padding (int): Padding around the text.

        Returns:
            moderngl.Texture: A ModernGL texture containing the rendered text.
        """
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            logger.warning(f"Font not found at {font_path}. Using default font.")
            font = ImageFont.load_default()

        # Calculate text size
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Create an image with enough space for text and padding
        img_width = text_width + 2 * padding
        img_height = text_height + 2 * padding
        text_image = Image.new("RGBA", (img_width, img_height), background_color)
        draw = ImageDraw.Draw(text_image)

        # Convert normalized RGBA (0-1) to 8-bit (0-255) for PIL
        pil_color = tuple(int(c * 255) for c in color)

        # Draw text
        draw.text((padding, padding), text, font=font, fill=pil_color)

        # Convert PIL image to ModernGL texture
        texture = self.ctx.texture(
            text_image.size,
            4, # RGBA
            text_image.tobytes()
        )
        logger.debug(f"Rendered text '{text}' to texture.")
        return texture

    def release(self, texture: moderngl.Texture):
        """
        Releases a ModernGL texture.
        """
        texture.release()

if __name__ == "__main__":
    print("TextRenderer requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.text_renderer = TextRenderer(self.ctx, self.wnd.size)")
    print("        # Example font path (ensure you have one, e.g., Arial.ttf in assets/)")
    print("        # self.font_path = \"assets/Arial.ttf\"")
    print("        # self.text_texture = self.text_renderer.render_text_to_texture(")
    print("        #    \"Hello World!\", self.font_path, 60, (1.0, 1.0, 1.0, 1.0))")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # self.text_texture.use(0)")
    print("        # Render self.text_texture to screen (requires a shader and VAO)")
    print("mglw.run_window_config(MyWindow)")
