
import moderngl
import numpy as np
from typing import Tuple

class ChromaticAberrationEffect:
    """
    Applies a chromatic aberration effect to an image using ModernGL.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int], strength: float = 0.01):
        """
        Initializes the ChromaticAberrationEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
            strength (float): The intensity of the chromatic aberration effect.
        """
        self.ctx = ctx
        self.width, self.height = resolution
        self.strength = strength

        self.chromatic_program = self.ctx.program(
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
                uniform float u_strength;
                uniform vec2 u_resolution;
                in vec2 v_texcoord;
                out vec4 f_color;

                void main() {
                    vec2 offset = u_strength * (v_texcoord - 0.5);

                    vec4 color_r = texture(u_texture, v_texcoord - offset);
                    vec4 color_g = texture(u_texture, v_texcoord);
                    vec4 color_b = texture(u_texture, v_texcoord + offset);

                    f_color = vec4(color_r.r, color_g.g, color_b.b, color_g.a);
                }
            """,
        )
        self.chromatic_program["u_strength"].value = self.strength
        self.chromatic_program["u_resolution"].value = resolution

        # A simple quad covering the entire screen
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype=\'f4\')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.chromatic_program,
            [(
                self.vbo,
                \"2f 2f\",
                \"in_vert\", \"in_texcoord\"
            )]
        )

    def apply(self, original_texture: moderngl.Texture) -> moderngl.Texture:
        """
        Applies the chromatic aberration effect to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply chromatic aberration to.

        Returns:
            moderngl.Texture: A new texture with the chromatic aberration effect applied.
        """
        output_fbo = self.ctx.framebuffer(
            self.ctx.texture((self.width, self.height), 4)
        )
        output_fbo.use()

        self.chromatic_program["u_texture"] = original_texture
        self.vao.render(moderngl.TRIANGLE_STRIP)

        return output_fbo.color_attachments[0]

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.vbo.release()
        self.vao.release()
        self.chromatic_program.release()


# Example usage (requires a ModernGL context and a texture)
if __name__ == "__main__":
    print("ChromaticAberrationEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.chromatic = ChromaticAberrationEffect(self.ctx, self.wnd.size, strength=0.02)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # chromatic_texture = self.chromatic.apply(self.image_texture)")
    print("        # chromatic_texture.use(0)")
    print("        # Render chromatic_texture to screen")
    print("mglw.run_window_config(MyWindow)")
