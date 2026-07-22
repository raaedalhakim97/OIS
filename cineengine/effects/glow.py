import moderngl
import numpy as np
from typing import Tuple

class GlowEffect:
    """
    Applies a glow effect to an image using ModernGL.
    Similar to bloom, but often with a stronger emphasis on bright areas.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int], threshold: float = 0.9, blur_radius: int = 5):
        """
        Initializes the GlowEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
            threshold (float): Pixels brighter than this threshold will contribute to glow.
            blur_radius (int): The radius for the Gaussian blur applied to the glow.
        """
        self.ctx = ctx
        self.width, self.height = resolution
        self.threshold = threshold
        self.blur_radius = blur_radius

        # Framebuffers for intermediate steps
        self.fbo_bright = self.ctx.framebuffer(
            self.ctx.texture(resolution, 4)
        )
        self.fbo_blur_h = self.ctx.framebuffer(
            self.ctx.texture(resolution, 4)
        )
        self.fbo_blur_v = self.ctx.framebuffer(
            self.ctx.texture(resolution, 4)
        )

        # Shaders
        self.bright_pass_program = self.ctx.program(
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
                uniform float u_threshold;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    vec4 color = texture(u_texture, v_texcoord);
                    float brightness = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722)); // Luminance
                    f_color = vec4(color.rgb * step(u_threshold, brightness), 1.0);
                }
            """,
        )
        self.bright_pass_program["u_threshold"].value = self.threshold

        self.gaussian_blur_program = self.ctx.program(
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
                uniform vec2 u_direction;
                uniform vec2 u_resolution;
                uniform int u_radius;
                in vec2 v_texcoord;
                out vec4 f_color;

                void main() {
                    vec2 texel_size = 1.0 / u_resolution;
                    vec4 sum = texture(u_texture, v_texcoord);

                    for (int i = 1; i <= u_radius; ++i) {
                        sum += texture(u_texture, v_texcoord + float(i) * u_direction * texel_size);
                        sum += texture(u_texture, v_texcoord - float(i) * u_direction * texel_size);
                    }
                    f_color = sum / (1.0 + 2.0 * u_radius);
                }
            """,
        )
        self.gaussian_blur_program["u_resolution"].value = resolution
        self.gaussian_blur_program["u_radius"].value = self.blur_radius

        self.combine_program = self.ctx.program(
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
                uniform sampler2D u_original_texture;
                uniform sampler2D u_glow_texture;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    vec4 original_color = texture(u_original_texture, v_texcoord);
                    vec4 glow_color = texture(u_glow_texture, v_texcoord);
                    f_color = original_color + glow_color * 0.8; // Adjust glow intensity
                }
            """,
        )

        # A simple quad covering the entire screen
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.bright_pass_program,
            [(
                self.vbo,
                "2f 2f",
                "in_vert", "in_texcoord"
            )]
        )

    def apply(self, original_texture: moderngl.Texture) -> moderngl.Texture:
        """
        Applies the glow effect to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply glow to.

        Returns:
            moderngl.Texture: A new texture with the glow effect applied.
        """
        # 1. Bright Pass
        self.fbo_bright.use()
        self.bright_pass_program["u_texture"] = original_texture
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # 2. Horizontal Blur
        self.fbo_blur_h.use()
        self.gaussian_blur_program["u_texture"] = self.fbo_bright.color_attachments[0]
        self.gaussian_blur_program["u_direction"].value = (1.0, 0.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # 3. Vertical Blur
        self.fbo_blur_v.use()
        self.gaussian_blur_program["u_texture"] = self.fbo_blur_h.color_attachments[0]
        self.gaussian_blur_program["u_direction"].value = (0.0, 1.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # 4. Combine with Original
        final_fbo = self.ctx.framebuffer(
            self.ctx.texture((self.width, self.height), 4)
        )
        final_fbo.use()
        self.combine_program["u_original_texture"] = original_texture
        self.combine_program["u_glow_texture"] = self.fbo_blur_v.color_attachments[0]
        self.vao.render(moderngl.TRIANGLE_STRIP)

        return final_fbo.color_attachments[0]

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.fbo_bright.release()
        self.fbo_blur_h.release()
        self.fbo_blur_v.release()
        self.vbo.release()
        self.vao.release()
        self.bright_pass_program.release()
        self.gaussian_blur_program.release()
        self.combine_program.release()


# Example usage (requires a ModernGL context and a texture)
if __name__ == "__main__":
    print("GlowEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.glow = GlowEffect(self.ctx, self.wnd.size, threshold=0.8, blur_radius=7)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # glowed_texture = self.glow.apply(self.image_texture)")
    print("        # glowed_texture.use(0)")
    print("        # Render glowed_texture to screen")
    print("mglw.run_window_config(MyWindow)")
