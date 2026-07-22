
import logging
import moderngl
import numpy as np
from PIL import Image
from typing import Tuple, List, Callable, Optional

from cineengine.config import Config
from cineengine.camera.camera import Camera
from cineengine.effects.effects import Effects
from cineengine.audio.audio import Audio
from cineengine.subtitles.subtitles import Subtitles
from cineengine.renderer.timeline import Timeline, TimelineEvent
from cineengine.renderer.transition import Transition
from cineengine.renderer.compositor import Compositor
from cineengine.renderer.export import VideoExporter

logger = logging.getLogger(__name__)

class Renderer:
    """
    Orchestrates the rendering process, combining all elements into a final video.
    """
    def __init__(
        self,
        config: Config,
        camera: Camera,
        effects: Effects,
        audio: Audio,
        subtitles: Subtitles,
        ctx: moderngl.Context
    ):
        """
        Initializes the Renderer.

        Args:
            config (Config): The CineEngine configuration object.
            camera (Camera): The Camera module instance.
            effects (Effects): The Effects module instance.
            audio (Audio): The Audio module instance.
            subtitles (Subtitles): The Subtitles module instance.
        """
        self.config = config
        self.camera = camera
        self.effects = effects
        self.audio = audio
        self.subtitles = subtitles

        self.timeline = Timeline()
        self.video_exporter = VideoExporter(self.config.FPS, self.config.RESOLUTION)

        # Initialize ModernGL context and related components
        self.ctx = ctx
        logger.info(f"ModernGL context received: {self.ctx.version_code}")

        # Ensure effects and subtitles have the shared context
        self.effects.ctx = self.ctx
        self.subtitles.ctx = self.ctx
        if self.subtitles.text_renderer is None:
            self.subtitles.text_renderer = TextRenderer(self.ctx, self.config.RESOLUTION)

        self.transition = Transition(self.ctx, self.config.RESOLUTION)
        self.compositor = Compositor(self.ctx, self.config)

        # Cache for loaded textures to avoid re-loading same images
        self._texture_cache = {}

        logger.info("Renderer module initialized.")

    def _load_image_as_texture(self, image_path: str) -> moderngl.Texture:
        """
        Loads an image from path and converts it into a ModernGL texture.
        Caches textures to avoid redundant loading.
        """
        if image_path in self._texture_cache:
            return self._texture_cache[image_path]

        try:
            img = Image.open(image_path).convert("RGBA")
            texture = self.ctx.texture(img.size, 4, img.tobytes())
            self._texture_cache[image_path] = texture
            logger.debug(f"Loaded image {image_path} as texture.")
            return texture
        except Exception as e:
            logger.error(f"Failed to load image {image_path} as texture: {e}")
            # Return a dummy texture (e.g., black) on error
            dummy_img = Image.new("RGBA", self.config.RESOLUTION, color = (0, 0, 0, 255))
            dummy_texture = self.ctx.texture(dummy_img.size, 4, dummy_img.tobytes())
            return dummy_texture

    def _render_base_image_frame(self, image_path: str, current_time: float) -> moderngl.Texture:
        """
        Renders the base image for the current frame, applying camera transformations.
        """
        base_texture = self._load_image_as_texture(image_path)

        # Get camera state
        (cam_x, cam_y), cam_zoom = self.camera.get_state(current_time)

        # Create a framebuffer to render the transformed image
        fbo = self.ctx.framebuffer(
            self.ctx.texture(self.config.RESOLUTION, 4)
        )
        fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 0.0) # Clear with transparent background

        # Simple shader to draw texture with camera transform
        render_program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                uniform vec2 u_camera_pos;
                uniform float u_camera_zoom;
                out vec2 v_texcoord;
                void main() {
                    // Apply zoom and pan
                    vec2 transformed_vert = (in_vert - u_camera_pos) / u_camera_zoom;
                    gl_Position = vec4(transformed_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D u_texture;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    f_color = texture(u_texture, v_texcoord);
                }
            """,
        )
        render_program["u_camera_pos"].value = (cam_x, cam_y)
        render_program["u_camera_zoom"].value = cam_zoom
        render_program["u_texture"] = base_texture

        # Use a VAO for rendering the image
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')
        vbo = self.ctx.buffer(vertices.tobytes())
        vao = self.ctx.vertex_array(
            render_program,
            [(
                vbo,
                "2f 2f",
                "in_vert", "in_texcoord"
            )]
        )
        vao.render(moderngl.TRIANGLE_STRIP)

        vbo.release()
        vao.release()
        render_program.release()

        return fbo.color_attachments[0]

    def render_frame(self, current_time: float) -> np.ndarray:
        """
        Renders a single frame of the video at the given time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            np.ndarray: A NumPy array representing the RGBA frame (height, width, 4).
        """
        self.ctx.clear(0.0, 0.0, 0.0, 1.0) # Clear the default framebuffer

        # Find active image event
        active_image_event = None
        for event in self.timeline.get_active_events(current_time):
            if event.event_type == "image":
                active_image_event = event
                break

        if active_image_event is None:
            logger.warning(f"No active image found at {current_time:.2f}s. Rendering black frame.")
            return np.zeros((self.config.RESOLUTION[1], self.config.RESOLUTION[0], 4), dtype=np.uint8)

        image_path = active_image_event.properties["path"]
        base_frame_texture = self._render_base_image_frame(image_path, current_time)

        # Apply effects and composite subtitles
        final_frame_texture = self.compositor.composite_frame(
            base_frame_texture,
            self.effects,
            self.subtitles,
            current_time
        )

        # Read the final texture back to a NumPy array
        # Create a temporary FBO to read from
        read_fbo = self.ctx.framebuffer(
            color_attachments=[final_frame_texture]
        )
        read_fbo.use()
        frame_data = np.frombuffer(self.ctx.read_framebuffer(read_fbo, components=4, dtype='f1'), dtype=np.float32).reshape(
            self.config.RESOLUTION[1], self.config.RESOLUTION[0], 4
        )
        # Convert float32 (0-1) to uint8 (0-255)
        frame_data_uint8 = (frame_data * 255).astype(np.uint8)

        # Release temporary FBO
        read_fbo.release()

        return frame_data_uint8

    def export_video(self, images: List[str], output_path: str, audio_path: Optional[str] = None) -> None:
        """
        Exports the final video by rendering all frames and combining with audio.

        Args:
            images (List[str]): List of image paths to use for the video.
            output_path (str): Path to save the output video.
            audio_path (Optional[str]): Path to the audio file to be included.
        """
        # Populate timeline with image events (simple sequential for now)
        current_start_time = 0.0
        for img_path in images:
            # Assuming each image is displayed for a fixed duration, e.g., 5 seconds
            image_duration = 5.0 # This should be dynamic based on user input or AI analysis
            self.timeline.add_event(TimelineEvent("image", current_start_time, image_duration, {"path": img_path}))
            current_start_time += image_duration

        total_video_duration = self.timeline.total_duration

        # Mix audio if provided
        mixed_audio_path = None
        if audio_path:
            # Placeholder: In a real scenario, audio mixing would happen here
            # For now, we just pass the single audio_path directly to the exporter
            mixed_audio_path = audio_path

        self.video_exporter.export_video(
            frame_generator=self.render_frame,
            duration=total_video_duration,
            output_path=output_path,
            audio_path=mixed_audio_path
        )

    def release(self):
        """
        Releases all ModernGL resources.
        """
        self.effects.release()
        self.subtitles.release()
        self.transition.release()
        self.compositor.release()
        for texture in self._texture_cache.values():
            texture.release()
        self.ctx.release()
        logger.info("Renderer resources released.")

if __name__ == "__main__":
    print("Renderer module requires a full CineEngine setup to run. This is a placeholder example.")
    print("To test, you would typically instantiate CineEngine and call its export method.")
    print("    from cineengine import CineEngine")
    print("    engine = CineEngine(fps=24, resolution=(1080, 1920))")
    print("    # engine.add_image(\"path/to/image1.png\")")
    print("    # engine.camera.cinematic_push()")
    print("    # engine.effects.film_grain()")
    print("    # engine.subtitles.add(\"Hello!\", 0.0, 2.0)")
    print("    # engine.export(\"output.mp4\")")
