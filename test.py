import numpy as np
from OpenGL.GL import *

WINDOW_LIBRARY = 'GLFW'  # GLFW or GLUT
TRY_FRAMEBUFFER = True
GENERATE_TEXTURE_ID_PROBLEM = False  # Follow this global variable to see the error in texture ID generation

SIDE = 400  # window size


# Utility functions
def float_size(n=1):
    return sizeof(ctypes.c_float) * n


def pointer_offset(n=0):
    return ctypes.c_void_p(float_size(n))


def create_shader(vertex_shader, fragment_shader):
    vs_id = GLuint(glCreateShader(GL_VERTEX_SHADER))  # shader id for vertex shader
    glShaderSource(vs_id, vertex_shader)  # Send the code of the shader
    glCompileShader(vs_id)  # compile the shader code
    status = glGetShaderiv(vs_id, GL_COMPILE_STATUS)
    if status != 1:
        print('VERTEX SHADER ERROR')
        print(glGetShaderInfoLog(vs_id).decode())

    fs_id = GLuint(glCreateShader(GL_FRAGMENT_SHADER))
    glShaderSource(fs_id, fragment_shader)
    glCompileShader(fs_id)
    status = glGetShaderiv(fs_id, GL_COMPILE_STATUS)
    if status != 1:
        print('FRAGMENT SHADER ERROR')
        print(glGetShaderInfoLog(fs_id).decode())

    # Link the shaders into a single program
    program_id = GLuint(glCreateProgram())
    glAttachShader(program_id, vs_id)
    glAttachShader(program_id, fs_id)
    glLinkProgram(program_id)
    status = glGetProgramiv(program_id, GL_LINK_STATUS)
    if status != 1:
        print('status', status)
        print('SHADER PROGRAM', glGetShaderInfoLog(program_id))

    glDeleteShader(vs_id)
    glDeleteShader(fs_id)

    return program_id


# Initialize project
if WINDOW_LIBRARY == 'GLFW':
    def default_key_callback(win, key, scancode, action, mods):
        if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
            glfwSetWindowShouldClose(win, True)

    import glfw
    glfw.init()
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.RESIZABLE, GL_FALSE)
    glfw.window_hint(glfw.SAMPLES, 4)
    window = glfw.create_window(SIDE, SIDE, 'GLFW Framebuffer Test', None, None)
    glfw.make_context_current(window)
    glfw.set_key_callback(window, default_key_callback)

# OpenGL version info
renderer = glGetString(GL_RENDERER)
version = glGetString(GL_VERSION)
print('Renderer:', renderer)  # Renderer: b'Intel Iris Pro OpenGL Engine'
print('OpenGL version supported: ', version)  # OpenGL version supported:  b'4.1 INTEL-10.12.13'

# Generate simple colored triangle
triangle_data = np.array([
    # Positions   Colors
    -.5, -.5, 0,   1, 0, 0,
    .5, -.5, 0,    0, 1, 0,
    0, .5, 0,      0, 0, 1
], dtype=np.float32)
triangle_vao = GLuint()
glGenVertexArrays(1, triangle_vao)
glBindVertexArray(triangle_vao)
vbo = GLuint()
glGenBuffers(1, vbo)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, triangle_data, GL_STATIC_DRAW)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, float_size(6), pointer_offset(0))  # attribute 0 = coordinates
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, float_size(6), pointer_offset(3))  # attribute 1 = colors
glEnableVertexAttribArray(0)
glEnableVertexAttribArray(1)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# A quad to show the rendered content
screen_quad_data = np.array([
    # Positions  TexCoords
    -1.0, 1.0,   0.0, 1.0,
    -1.0, -1.0,  0.0, 0.0,
    1.0, -1.0,   1.0, 0.0,

    -1.0, 1.0,   0.0, 1.0,
    1.0, -1.0,   1.0, 0.0,
    1.0, 1.0,    1.0, 1.0
], dtype=np.float32)
screen_quad_vao = GLuint()
glGenVertexArrays(1, screen_quad_vao)
glBindVertexArray(screen_quad_vao)
quad_vbo = GLuint()
glGenBuffers(1, quad_vbo)
glBindBuffer(GL_ARRAY_BUFFER, quad_vbo)
glBufferData(GL_ARRAY_BUFFER, screen_quad_data, GL_STATIC_DRAW)
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, float_size(4), pointer_offset(0))
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, float_size(4), pointer_offset(2))
glEnableVertexAttribArray(0)
glEnableVertexAttribArray(1)

glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# Shaders
vertex_shader1 = """#version 410
layout(location = 0) in vec3 pos;
layout(location = 1) in vec3 col;
out vec3 fg_color;
void main () {
    fg_color = col;
    gl_Position = vec4(pos, 1.0f);
}"""

fragment_shader1 = """#version 410
in vec3 fg_color;
out vec4 color;
void main () {
    color = vec4(fg_color, 1.);
}"""

main_shader = create_shader(vertex_shader1, fragment_shader1)

vertex_shader2 = """# version 400
layout(location=0) in vec2 position;
layout(location=1) in vec2 texCoords;
out vec2 TexCoords;
void main()
{
    gl_Position = vec4(position.x, position.y, 0.0f, 1.0f);
    TexCoords = texCoords;
}
"""

fragment_shader2 = """# version 400
in vec2 TexCoords;
out vec4 color;
uniform sampler2D screenTexture;
void main()
{
    vec3 sampled = vec4(texture(screenTexture, TexCoords)).xyz; // original rendered pixel color value
    //color = vec4(TexCoords.x, TexCoords.y, 0., 1.); // to see whether I placed quad correctly
    //color = vec4(sampled, 1.0); // original
    color = vec4(1.0 - sampled, 1.0); // processed (inverted)
}
"""

screen_quad_shader = create_shader(vertex_shader2, fragment_shader2)

if WINDOW_LIBRARY == 'GLFW':
    w, h = glfw.get_framebuffer_size(window)
    glViewport(0, 0, w, h)
    SIDE = w  # I guess due to Anti-Aliasing viewport size is 1600x1600 now (?)

# Framebuffer to render offscreen
fbo = GLuint()
glGenFramebuffers(1, fbo)
glBindFramebuffer(GL_FRAMEBUFFER, fbo)

if GENERATE_TEXTURE_ID_PROBLEM:
    texture = GLuint()
    glGenTextures(1, texture)
else:
    texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, SIDE, SIDE, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

# Render buffer is not necessary for this example
rbo = GLuint()
glGenRenderbuffers(1, rbo)
glBindRenderbuffer(GL_RENDERBUFFER, rbo)
glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, SIDE, SIDE)
glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

if not glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
    print('framebuffer binding failed')
    exit()
glBindFramebuffer(GL_FRAMEBUFFER, 0)
glBindTexture(GL_TEXTURE_2D, 0)
glBindRenderbuffer(GL_RENDERBUFFER, 0)


def draw_scene_to_texture():
    if TRY_FRAMEBUFFER:
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glEnable(GL_DEPTH_TEST)  # https://www.khronos.org/opengles/sdk/docs/man/xhtml/glEnable.xml
    glClearColor(0., 0., 0., 1.0)
    glClearDepth(1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glBindVertexArray(triangle_vao)
    glUseProgram(main_shader)
    glDrawArrays(GL_TRIANGLES, 0, 3)

    glBindVertexArray(0)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)


def draw_texture_to_quad():
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glClearColor(1., 0., 0., 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)

    glBindVertexArray(screen_quad_vao)
    glUseProgram(screen_quad_shader)
    glBindTexture(GL_TEXTURE_2D, texture)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    glBindTexture(GL_TEXTURE_2D, 0)
    glBindVertexArray(0)


def draw():
    draw_scene_to_texture()  # First pass
    if TRY_FRAMEBUFFER:
        draw_texture_to_quad()  # Final pass


def draw_glfw():
    draw()
    glfw.poll_events()
    glfw.swap_buffers(window)


# Main loop
glDepthFunc(GL_LESS)
if WINDOW_LIBRARY == 'GLFW':
    while not glfw.window_should_close(window):
        draw_glfw()
