
import moderngl
import numpy as np
from typing import Tuple

class DepthOfFieldEffect:
    """
    Applies a Depth of Field (DoF) effect to an image using ModernGL.
    This implementation uses a simple blur based on a focal plane and range.
    For a more advanced effect, it would integrate a depth map.
    """
    def __init__(
        self, 
        ctx: moderngl.Context, 
        resolution: Tuple[int, int], 
        strength: float = 0.1, 
        focal_distance: float = 0.5, 
        focal_range: float = 0.2
    ):
        """
        Initializes the DepthOfFieldEffect.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            resolution (Tuple[int, int]): The resolution of the input texture (width, height).
            strength (float): The overall strength of the DoF blur.
            focal_distance (float): Normalized distance (0.0 to 1.0) to the focal plane.
            focal_range (float): Normalized range (0.0 to 1.0) around the focal distance that is in focus.
        """
        self.ctx = ctx
        self.width, self.height = resolution
        self.strength = strength
        self.focal_distance = focal_distance
        self.focal_range = focal_range

        # Framebuffers for blurred versions
        self.fbo_blur = self.ctx.framebuffer(
            self.ctx.texture(resolution, 4)
        )

        # Shader for Depth of Field
        # This shader will simulate DoF without an actual depth map for now.
        # A more advanced version would take a depth texture as input.
        self.dof_program = self.ctx.program(
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
                uniform float u_focal_distance;
                uniform float u_focal_range;
                uniform vec2 u_resolution;
                in vec2 v_texcoord;
                out vec4 f_color;

                // Simple blur function (can be replaced with a more advanced one)
                vec4 blur(sampler2D tex, vec2 uv, vec2 resolution, float radius) {
                    vec4 sum = vec4(0.0);
                    float count = 0.0;
                    vec2 texel_size = 1.0 / resolution;

                    for (float x = -radius; x <= radius; x += 1.0) {
                        for (float y = -radius; y <= radius; y += 1.0) {
                            sum += texture(tex, uv + vec2(x, y) * texel_size);
                            count += 1.0;
                        }
                    }
                    return sum / count;
                }

                void main() {
                    vec4 color = texture(u_texture, v_texcoord);

                    // For demonstration, we'll simulate depth based on Y-coordinate
                    // In a real scenario, this would come from a depth map texture
                    float depth = v_texcoord.y; // Example: objects further down are closer

                    float blur_amount = 0.0;
                    if (depth < u_focal_distance - u_focal_range / 2.0) {
                        blur_amount = (u_focal_distance - u_focal_range / 2.0 - depth) / (u_focal_distance - u_focal_range / 2.0);
                    } else if (depth > u_focal_distance + u_focal_range / 2.0) {
                        blur_amount = (depth - (u_focal_distance + u_focal_range / 2.0)) / (1.0 - (u_focal_distance + u_focal_range / 2.0));
                    }
                    blur_amount = clamp(blur_amount, 0.0, 1.0) * u_strength * 10.0; // Scale strength

                    if (blur_amount > 0.001) {
                        f_color = blur(u_texture, v_texcoord, u_resolution, blur_amount);
                    } else {
                        f_color = color;
                    }
                }
            """,
        )
        self.dof_program["u_strength"].value = self.strength
        self.dof_program["u_focal_distance"].value = self.focal_distance
        self.dof_program["u_focal_range"].value = self.focal_range
        self.dof_program["u_resolution"].value = resolution

        # A simple quad covering the entire screen
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.dof_program,
            [(
                self.vbo,
                "2f 2f",
                "in_vert", "in_texcoord"
            )]
        )

    def apply(self, original_texture: moderngl.Texture) -> moderngl.Texture:
        """
        Applies the Depth of Field effect to the given texture.

        Args:
            original_texture (moderngl.Texture): The input texture to apply DoF to.

        Returns:
            moderngl.Texture: A new texture with the DoF effect applied.
        """
        output_fbo = self.ctx.framebuffer(
            self.ctx.texture((self.width, self.height), 4)
        )
        output_fbo.use()

        self.dof_program["u_texture"] = original_texture
        self.vao.render(moderngl.TRIANGLE_STRIP)

        return output_fbo.color_attachments[0]

    def release(self):
        """
        Releases ModernGL resources.
        """
        self.fbo_blur.release()
        self.vbo.release()
        self.vao.release()
        self.dof_program.release()


# Example usage (requires a ModernGL context and a texture)
if __name__ == "__main__":
    print("DepthOfFieldEffect requires a ModernGL context to run. This is a placeholder example.")
    print("To test, you would typically do something like:")
    print("import moderngl_window as mglw")
    print("class MyWindow(mglw.WindowConfig):")
    print("    def __init__(self, **kwargs):")
    print("        super().__init__(**kwargs)")
    print("        self.dof = DepthOfFieldEffect(self.ctx, self.wnd.size, strength=0.1, focal_distance=0.5, focal_range=0.2)")
    print("        # Load an image into a texture")
    print("        # self.image_texture = self.load_texture(\"path/to/image.png\")")
    print("    def render(self, time, frametime):")
    print("        # self.ctx.clear()")
    print("        # dof_texture = self.dof.apply(self.image_texture)")
    print("        # dof_texture.use(0)")
    print("        # Render dof_texture to screen")
    print("mglw.run_window_config(MyWindow)")
