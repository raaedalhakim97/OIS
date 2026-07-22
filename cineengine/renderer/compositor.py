import moderngl
import numpy as np
from typing import Tuple, List, Optional
import logging

from cineengine.config import Config
from cineengine.effects.effects import Effects
from cineengine.subtitles.subtitles import Subtitles

logger = logging.getLogger(__name__)

class Compositor:
    """
    Combines various rendered layers (background, main image, effects, particles, subtitles)
    into a single final frame using ModernGL.
    """
    def __init__(self, ctx: moderngl.Context, config: Config):
        """
        Initializes the Compositor.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            config (Config): The CineEngine configuration object.
        """
        self.ctx = ctx
        self.config = config
        self.width, self.height = config.RESOLUTION

        # A simple quad covering the entire screen for rendering textures
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.base_render_program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D u_texture;
                out vec4 f_color;
                void main() {
                    f_color = texture(u_texture, v_texcoord);
                }
            """,
        )
        self.vao = self.ctx.vertex_array(
            self.base_render_program,
            [(
                self.vbo,
                "2f 2f",
                "in_vert", "in_texcoord"
            )]
        )

        self.text_render_program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                uniform vec2 u_position_offset;
                uniform vec2 u_scale;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(u_position_offset + in_vert * u_scale, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D u_text_texture;
                uniform float u_alpha;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    vec4 text_color = texture(u_text_texture, v_texcoord);
                    f_color = vec4(text_color.rgb, text_color.a * u_alpha);
                }
            """,
        )
        self.text_vao = self.ctx.vertex_array(
            self.text_render_program,
            [(
                self.vbo,
                "2f 2f",
                "in_vert", "in_texcoord"
            )]
        )
        logger.info("Compositor initialized.")

    def composite_frame(
        self,
        base_texture: moderngl.Texture,
        effects_module: Effects,
        subtitles_module: Subtitles,
        current_time: float,
        # particle_textures: List[moderngl.Texture] = None, # Future: particle textures
    ) -> moderngl.Texture:
        """
        Composites all layers into a final frame.

        Args:
            base_texture (moderngl.Texture): The main image/video frame texture.
            effects_module (Effects): The Effects module instance.
            subtitles_module (Subtitles): The Subtitles module instance.
            current_time (float): The current time in seconds.

        Returns:
            moderngl.Texture: The final composited texture.
        """
        # Start with the base texture
        final_texture = base_texture

        # Apply effects
        final_texture = effects_module.apply_effects(final_texture, current_time)

        # Render subtitles
        active_subtitles = subtitles_module.get_rendered_subtitles(current_time)
        if active_subtitles:
            # Create a new FBO to draw subtitles onto the current final_texture
            subtitle_fbo = self.ctx.framebuffer(
                self.ctx.texture((self.width, self.height), 4)
            )
            subtitle_fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 0.0) # Clear with transparent background

            # Draw the current final_texture onto the subtitle_fbo first
            self.base_render_program["u_texture"] = final_texture
            self.vao.render(moderngl.TRIANGLE_STRIP)

            # Enable blending for subtitles
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

            for sub_texture, position, alpha in active_subtitles:
                # Calculate position and scale for the subtitle texture
                # position is normalized (0-1), convert to clip space (-1 to 1)
                # sub_texture.width and sub_texture.height are pixel dimensions
                # We need to scale the quad to match the texture size and position it correctly
                
                # Assuming position is the center of the subtitle
                # Convert normalized position to clip space
                # Calculate normalized width and height of the subtitle texture
                norm_width = sub_texture.width / self.width
                norm_height = sub_texture.height / self.height

                # Calculate half normalized width and height for scaling the -1 to 1 quad
                half_norm_width = norm_width / 2.0
                half_norm_height = norm_height / 2.0

                # Calculate the center position in clip space (-1 to 1)
                center_x_clip = position[0] * 2.0 - 1.0
                center_y_clip = position[1] * 2.0 - 1.0

                self.text_render_program["u_text_texture"] = sub_texture
                self.text_render_program["u_position_offset"].value = (center_x_clip, center_y_clip)
                self.text_render_program["u_scale"].value = (half_norm_width, half_norm_height)
                self.text_render_program["u_alpha"].value = alpha
                self.text_vao.render(moderngl.TRIANGLE_STRIP)
                sub_texture.release() # Release the subtitle texture after use
            
            self.ctx.disable(moderngl.BLEND)
            final_texture = subtitle_fbo.color_attachments[0]

        # Future: Composite particles
        # if particle_textures:
        #     for p_tex in particle_textures:
        #         final_texture = self._blend_textures(final_texture, p_tex)

        return final_texture

    def _blend_textures(self, tex1: moderngl.Texture, tex2: moderngl.Texture) -> moderngl.Texture:
        """
        Helper to blend two textures. (Placeholder for a proper blending shader).
        """
        # This would use a shader to blend tex1 and tex2
        # For now, just return tex1
        return tex1

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.vbo.release()
        self.vao.release()
        self.vao.program.release()
        logger.info("Compositor resources released.")

if __name__ == "__main__":
    print("Compositor requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("from PIL import Image")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        from cineengine.config import Config")
    print("        self.config = Config()")
    print("        self.compositor = Compositor(self.ctx, self.config)")
    print("        self.effects_module = Effects(self.config, self.ctx)")
    print("        self.subtitles_module = Subtitles(self.config, self.ctx)")
    print("        # Create a dummy base texture")
    print("        # img = Image.new(\"RGB\", self.wnd.size, color = \"green\")")
    print("        # self.base_texture = self.ctx.texture(img.size, 3, img.tobytes())")
    print("        self.effects_module.bloom()")
    print("        self.subtitles_module.add(\"Hello Compositor!\", 0.0, 5.0, animation_type=\"fade_in_out\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # final_frame_texture = self.compositor.composite_frame(self.base_texture, self.effects_module, self.subtitles_module, time)")
    print("        # final_frame_texture.use(0)")
    print("        # Render final_frame_texture to screen")
    print("mglw.run_window_config(MyWindow)")
