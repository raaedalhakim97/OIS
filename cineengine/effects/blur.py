
import moderngl
import numpy as np
from typing import Tuple

class BlurEffect:
    """
    Applies a Gaussian blur effect to an image using ModernGL.
    This can be extended for motion blur by incorporating velocity.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int], radius: int = 5):
        """
        Initializes the BlurEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
            radius (int): The radius of the Gaussian blur kernel.
        """
        self.ctx = ctx
        self.width, self.height = resolution
        self.radius = radius

        # Framebuffers for horizontal and vertical blur passes
        self.fbo_blur_h = self.ctx.framebuffer(
            self.ctx.texture(resolution, 4)
        )
        self.fbo_blur_v = self.ctx.framebuffer(
            self.ctx.texture(resolution, 4)
        )

        # Gaussian blur shader
        # This is a simplified Gaussian blur. For a true motion blur, we'd need velocity vectors.
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
        self.gaussian_blur_program["u_radius"].value = self.radius

        # A simple quad covering the entire screen
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype=\'f4\')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.gaussian_blur_program,
            [(
                self.vbo,
                \"2f 2f\",
                \"in_vert\", \"in_texcoord\"
            )]
        )

    def apply(self, original_texture: moderngl.Texture) -> moderngl.Texture:
        """
        Applies the Gaussian blur effect to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply blur to.

        Returns:
            moderngl.Texture: A new texture with the blur effect applied.
        """
        # Horizontal blur pass
        self.fbo_blur_h.use()
        self.gaussian_blur_program["u_texture"] = original_texture
        self.gaussian_blur_program["u_direction"].value = (1.0, 0.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # Vertical blur pass
        self.fbo_blur_v.use()
        self.gaussian_blur_program["u_texture"] = self.fbo_blur_h.color_attachments[0]
        self.gaussian_blur_program["u_direction"].value = (0.0, 1.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        return self.fbo_blur_v.color_attachments[0]

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.fbo_blur_h.release()
        self.fbo_blur_v.release()
        self.vbo.release()
        self.vao.release()
        self.gaussian_blur_program.release()


# Example usage (requires a ModernGL context and a texture)
if __name__ == "__main__":
    print("BlurEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.blur = BlurEffect(self.ctx, self.wnd.size, radius=10)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # blurred_texture = self.blur.apply(self.image_texture)")
    print("        # blurred_texture.use(0)")
    print("        # Render blurred_texture to screen")
    print("mglw.run_window_config(MyWindow)")
