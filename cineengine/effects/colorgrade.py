
import moderngl
import numpy as np
from typing import Tuple

class ColorGradeEffect:
    """
    Applies color grading effects, including ACES Filmic tone mapping, using ModernGL.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int]):
        """
        Initializes the ColorGradeEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
        """
        self.ctx = ctx
        self.width, self.height = resolution

        self.color_grade_program = self.ctx.program(
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
                in vec2 v_texcoord;
                out vec4 f_color;

                // ACES Filmic Tone Mapping
                vec3 ACESFilm(vec3 x) {
                    float a = 2.51;
                    float b = 0.03;
                    float c = 2.43;
                    float d = 0.59;
                    float e = 0.14;
                    return ((x * (a * x + b)) / (x * (c * x + d) + e));
                }

                void main() {
                    vec4 color = texture(u_texture, v_texcoord);
                    f_color = vec4(ACESFilm(color.rgb), color.a);
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
            self.color_grade_program,
            [(
                self.vbo,
                "2f 2f",
                "in_vert", "in_texcoord"
            )]
        )

    def apply(self, original_texture: moderngl.Texture) -> moderngl.Texture:
        """
        Applies the ACES Filmic tone mapping to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply tone mapping to.

        Returns:
            moderngl.Texture: A new texture with the tone mapping applied.
        """
        output_fbo = self.ctx.framebuffer(
            self.ctx.texture((self.width, self.height), 4)
        )
        output_fbo.use()

        self.color_grade_program["u_texture"] = original_texture
        self.vao.render(moderngl.TRIANGLE_STRIP)

        return output_fbo.color_attachments[0]

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.vbo.release()
        self.vao.release()
        self.color_grade_program.release()


# Example usage (requires a ModernGL context and a texture)
if __name__ == "__main__":
    print("ColorGradeEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.color_grade = ColorGradeEffect(self.ctx, self.wnd.size)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # graded_texture = self.color_grade.apply(self.image_texture)")
    print("        # graded_texture.use(0)")
    print("        # Render graded_texture to screen")
    print("mglw.run_window_config(MyWindow)")
