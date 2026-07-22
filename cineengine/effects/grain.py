
import moderngl
import numpy as np
from typing import Tuple

class FilmGrainEffect:
    """
    Applies a film grain effect to an image using ModernGL.
    """
    def __init__(self, ctx: moderngl.Context, resolution: Tuple[int, int], intensity: float = 0.05):
        """
        Initializes the FilmGrainEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
            intensity (float): The intensity of the film grain effect.
        """
        self.ctx = ctx
        self.width, self.height = resolution
        self.intensity = intensity

        self.grain_program = self.ctx.program(
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
                uniform float u_intensity;
                uniform vec2 u_resolution;
                uniform float u_time;
                in vec2 v_texcoord;
                out vec4 f_color;

                // Pseudo-random number generator
                float rand(vec2 co) {
                    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
                }

                void main() {
                    vec4 color = texture(u_texture, v_texcoord);

                    // Generate grain based on screen position and time
                    float grain = rand(v_texcoord * u_resolution + u_time) * 2.0 - 1.0; // -1 to 1
                    grain *= u_intensity;

                    // Apply grain to color channels
                    f_color = vec4(color.rgb + grain, color.a);
                }
            """,
        )
        self.grain_program["u_intensity"].value = self.intensity
        self.grain_program["u_resolution"].value = resolution

        # A simple quad covering the entire screen
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype=\'f4\')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.grain_program,
            [(
                self.vbo,
                \"2f 2f\",
                \"in_vert\", \"in_texcoord\"
            )]
        )

    def apply(self, original_texture: moderngl.Texture, time: float) -> moderngl.Texture:
        """
        Applies the film grain effect to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply film grain to.
            time (float): Current time in seconds, used for animating the grain.

        Returns:
            moderngl.Texture: A new texture with the film grain effect applied.
        """
        output_fbo = self.ctx.framebuffer(
            self.ctx.texture((self.width, self.height), 4)
        )
        output_fbo.use()

        self.grain_program["u_texture"] = original_texture
        self.grain_program["u_time"].value = time
        self.vao.render(moderngl.TRIANGLE_STRIP)

        return output_fbo.color_attachments[0]

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.vbo.release()
        self.vao.release()
        self.grain_program.release()


# Example usage (requires a ModernGL context and a texture)
if __name__ == "__main__":
    print("FilmGrainEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.grain = FilmGrainEffect(self.ctx, self.wnd.size, intensity=0.1)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # grained_texture = self.grain.apply(self.image_texture, time)")
    print("        # grained_texture.use(0)")
    print("        # Render grained_texture to screen")
    print("mglw.run_window_config(MyWindow)")
