
import moderngl
import numpy as np
from PIL import Image
from typing import Tuple

class BloomEffect:
    """
    Applies a bloom effect to an image using ModernGL.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int], threshold: float = 0.8):
        """
        Initializes the BloomEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
            threshold (float): Pixels brighter than this threshold will contribute to bloom.
        """
        self.ctx = ctx
        self.width, self.height = resolution
        self.threshold = threshold

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
                    f_color = vec4(max(color.rgb - u_threshold, 0.0), 1.0);
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
                uniform float u_resolution_x;
                uniform float u_resolution_y;
                in vec2 v_texcoord;
                out vec4 f_color;

                void main() {
                    vec2 texel_size = vec2(1.0 / u_resolution_x, 1.0 / u_resolution_y);
                    vec4 sum = vec4(0.0);
                    sum += texture(u_texture, v_texcoord - 4.0 * u_direction * texel_size) * 0.004429;
                    sum += texture(u_texture, v_texcoord - 3.0 * u_direction * texel_size) * 0.021592;
                    sum += texture(u_texture, v_texcoord - 2.0 * u_direction * texel_size) * 0.084200;
                    sum += texture(u_texture, v_texcoord - 1.0 * u_direction * texel_size) * 0.230300;
                    sum += texture(u_texture, v_texcoord) * 0.341100;
                    sum += texture(u_texture, v_texcoord + 1.0 * u_direction * texel_size) * 0.230300;
                    sum += texture(u_texture, v_texcoord + 2.0 * u_direction * texel_size) * 0.084200;
                    sum += texture(u_texture, v_texcoord + 3.0 * u_direction * texel_size) * 0.021592;
                    sum += texture(u_texture, v_texcoord + 4.0 * u_direction * texel_size) * 0.004429;
                    f_color = sum;
                }
            """,
        )
        self.gaussian_blur_program["u_resolution_x"].value = float(self.width)
        self.gaussian_blur_program["u_resolution_y"].value = float(self.height)

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
                uniform sampler2D u_bloom_texture;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    vec4 original_color = texture(u_original_texture, v_texcoord);
                    vec4 bloom_color = texture(u_bloom_texture, v_texcoord);
                    f_color = original_color + bloom_color * 0.5; // Adjust bloom intensity
                }
            """,
        )

        # A simple quad covering the entire screen
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype=\'f4\')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.bright_pass_program,
            [(
                self.vbo,
                \"2f 2f\",
                \"in_vert\", \"in_texcoord\"
            )]
        )

    def apply(self, original_texture: moderngl.Texture) -> moderngl.Texture:
        """
        Applies the bloom effect to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply bloom to.

        Returns:
            moderngl.Texture: A new texture with the bloom effect applied.
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
        # We need a new FBO to render the final combined image, or render directly to screen
        # For now, let's assume we render to the default framebuffer or a new one for chaining
        final_fbo = self.ctx.framebuffer(
            self.ctx.texture((self.width, self.height), 4)
        )
        final_fbo.use()
        self.combine_program["u_original_texture"] = original_texture
        self.combine_program["u_bloom_texture"] = self.fbo_blur_v.color_attachments[0]
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
    # This part would typically be run within a moderngl-window context
    # For demonstration, we'll simulate a context and texture
    print("BloomEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.bloom = BloomEffect(self.ctx, self.wnd.size, threshold=0.7)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # bloomed_texture = self.bloom.apply(self.image_texture)")
    print("        # bloomed_texture.use(0)")
    print("        # Render bloomed_texture to screen")
    print("mglw.run_window_config(MyWindow)")

