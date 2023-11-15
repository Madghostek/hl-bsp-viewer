from OpenGL.GL import *
from OpenGL.GLU import *
from BSP import LumpsEnum
from triangle_math import SeparateVertices,hsv_to_rgb
import numpy as np

from benchmark import TimerMs
# Config
########
useCustomShader = True
cameraNear = 50
cameraFar = 10000

########

# globals
gProjectionMatrixHandle = -1
gDrawCount = -1

gBuffers = []

vertex_shader_perspective = """#version 410
layout(location = 0) in vec3 pos;
layout(location = 1) in vec3 vertexColor;

out vec4 position;
out vec3 fragmentColor;

uniform mat4 projection_matrix;

void main () {
    gl_Position = projection_matrix*vec4(pos, 1.0f);
    position = vec4(pos, 1.0f);
    fragmentColor = vertexColor;
}"""  # lub pos

fragment_shader = """#version 410

in vec4 position;

in vec3 fragmentColor;
in float rand;

layout(location = 0) out vec4 FragColor;

uniform float ymin;
uniform float ymax;
uniform float forceColor;

void main(){
    //FragColor = vec4(0.8,(gl_PrimitiveID%5)/4.0,1, 1.0);
    if (forceColor==-1.0)
        FragColor = vec4(fragmentColor,1.0);
    else
        FragColor = vec4(0,0,0, 1.0);
    //FragColor = vec4(0.8,2*(position.y-ymin)/(ymax-ymin),2-2*(position.y-ymin)/(ymax-ymin), 1.0);
}"""

fragment_shader_depth = f"""#version 410

in vec4 position;
out vec4 FragColor;

uniform float ymin;
uniform float ymax;

float near = {cameraNear};
float far  = {cameraFar}

float LinearizeDepth(float depth)
{{
    float z = depth * 2.0 - 1.0; // back to NDC
    return (2.0 * near * far) / (far + near - z * (far - near));
}}

void main(){{
    ymin;
    ymax;
    FragColor = vec4(vec3(LinearizeDepth(gl_FragCoord.z)), 1.0);
}}"""


def UpdateViewToCamera(c):
    glRotatef(-c.angle[0], 1, 0, 0)
    glRotatef(-c.angle[1], 0, 1, 0)
    glRotatef(-c.angle[2], 0, 0, 1)
    glTranslatef(*c.pos)


def pe():
    print("error", glGetError())


def ProgramWithShader(vertexShader, fragmentShader=None):
    # shader
    prog = glCreateProgram()
    shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(shader, vertexShader)
    glCompileShader(shader)
    res = glGetShaderiv(shader, GL_COMPILE_STATUS)
    print("vertex shader compilation status:",
          "OK" if res == GL_TRUE else "ERROR")
    assert (res == GL_TRUE)
    glAttachShader(prog, shader)
    print("LOG:", glGetProgramInfoLog(prog))

    if fragmentShader:
        shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(shader, fragmentShader)
        glCompileShader(shader)
        print("LOG:", glGetProgramInfoLog(prog))
        glAttachShader(prog, shader)
        res = glGetShaderiv(shader, GL_COMPILE_STATUS)
        print("Fragment shader compilation status:",
              "OK" if res == GL_TRUE else "ERROR")
        assert (res == GL_TRUE)

    glLinkProgram(prog)
    glUseProgram(prog)
    print("Program done")
    return prog


def PrepareEdges(returnedLumps):
    global gBuffers, gDrawCount

    # #init buffers
    vinfo = GLuint()
    glGenVertexArrays(1, vinfo)
    glBindVertexArray(vinfo)
    b1 = GLuint()
    glGenBuffers(1, b1)

    indexBuffer = GLuint()
    glGenBuffers(1, indexBuffer)

    gBuffers = [vinfo, b1, indexBuffer]

    # # tell OpenGL to use the b1 buffer for rendering, and give it data
    glBindBuffer(GL_ARRAY_BUFFER, b1)
    glBufferData(GL_ARRAY_BUFFER,
                 returnedLumps[LumpsEnum.LUMP_VERTICES.value], GL_STATIC_DRAW)

    # # describe what the data is (3x float)
    glEnableVertexAttribArray(0)
    # pe()

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0,
                          ctypes.c_void_p(0))  # or None
    # pe()

    # describe the edges (element buffer)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBuffer)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                 returnedLumps[LumpsEnum.LUMP_EDGES.value], GL_STATIC_DRAW)

    return len(returnedLumps[LumpsEnum.LUMP_EDGES.value])*2

# retun color based on the plane its parallel to


def FaceToColor(lumps, face):
    plane = lumps[LumpsEnum.LUMP_PLANES.value][face.iPlane]
    col = hsv_to_rgb(abs(plane[1]),0.2,0.5+max(plane[0],0)/2,1)
    #print(plane[0:3])
    return np.array(col, dtype=np.float32)


def TriangulateFaces(returnedLumps):
    # split n-gons into triangles...
    # when faces lump wants more than 3 vertices at once, split them into 0 1 2, 0 3 4, 0 4 5
    # now these indices can be inserted into element array, then GL_TRIANGLES can be used
    triangles = []
    colors = []  # color for each vertex
    tricount = 0
    edges = returnedLumps[LumpsEnum.LUMP_EDGES.value]
    surfedges = returnedLumps[LumpsEnum.LUMP_SURFEDGES.value]
    print("prepare faces from surfedges,", len(surfedges))
    for face in returnedLumps[LumpsEnum.LUMP_FACES.value]:
        # for each face, figure out which surfedges (then real edges) it uses,
        # then get list of all vertex indices used by face, but in a way that every 3 make a triangle

        # this means - get first "base" index, take second index, take next edge and one of the indices (the new one),
        # take next edge and another new index, until all edges from face taken, save the triplets to triangles array
        # print(face)
        base = face.iFirstEdge
        # !!! since im building triangles on my own, the last edge is not needed
        count = face.nEdges-1
        tricount += count-1  # 4 edges = 2 tris, 5 edges = 3 tris etc
        # print("the edges that will make a face:",surfedges[base:base+count+1])
        # print("which have these indices...")
        # for i in range(count):
        # print(edges[abs(surfedges[base+i][0])])
        first = edges[abs(surfedges[base][0])]
        # print("first",first,surfedges[base][0])
        if surfedges[base][0] >= 0:
            astri = [first[0], first[1]]
        else:
            astri = [first[1], first[0]]
        # print("first two:",astri)
        first = astri[0]
        sedge = surfedges[base+1]
        # print(sedge)
        newedge = edges[abs(sedge[0])]
        # print(newedge)
        if sedge[0] <= 0:
            newidx = newedge[0]
        else:
            newidx = newedge[1]
        astri.append(newidx)

        cur = 2
        # print("first tri:",astri)
        while cur < count:
            sedge = surfedges[base+cur]
            # print(sedge)
            newedge = edges[abs(sedge[0])]
            # print(newedge)
            if sedge[0] <= 0:
                newidx = newedge[0]
            else:
                newidx = newedge[1]
            # print(newidx)
            # append base and last one
            astri.extend([first, astri[-1], newidx])
            # print("more",astri)
            cur += 1

        # all triangles of given face will have same color
        color = FaceToColor(returnedLumps, face)
        for i in range(0, len(astri), 3):
            triangles.append(astri[i:i+3])
            # triangle is single-colored
            colors.append([color]*3)

    # print("final tri list",triangles)
    return triangles, colors, tricount

def PrepareFaces(returnedLumps):
    t = TimerMs("[Prepare faces]")
    t.start("Triangulate")
    triangles, colors, tricount = TriangulateFaces(returnedLumps)
    t.end("Triangulate")

    t.start("Make unique vertices")
    # uint32 here!! this is reflected in drawing code
    triangles, vertices = SeparateVertices(
        np.array(triangles, dtype=np.uint32), returnedLumps[LumpsEnum.LUMP_VERTICES.value])
    t.end("Make unique vertices")

    t.start("Upload data to GPU")

    # turn that into ndarray, send as element buffer (vertex buffer is the same as last time, draw with GL_TRIANGLES...)

    vinfo = GLuint()
    glGenVertexArrays(1, vinfo)
    glBindVertexArray(vinfo)

    b1 = GLuint()
    glGenBuffers(1, b1)

    indexBuffer = GLuint()
    glGenBuffers(1, indexBuffer)

    colorBuffer = GLuint()
    glGenBuffers(1, colorBuffer)

    # gBuffers = [vinfo, b1, indexBuffer, colorBuffer]

    # # tell OpenGL to use the b1 buffer for rendering, and give it data
    glBindBuffer(GL_ARRAY_BUFFER, b1)
    glBufferData(GL_ARRAY_BUFFER, vertices, GL_STATIC_DRAW)

    # enable this attribute index in rendering process
    glEnableVertexAttribArray(0)

    # describe what the data is (3x float)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0,
                          ctypes.c_void_p(0))  # or None

    # now use color buffer
    glBindBuffer(GL_ARRAY_BUFFER, colorBuffer)
    glBufferData(GL_ARRAY_BUFFER, np.array([colors]), GL_STATIC_DRAW)

    # again tell opengl what to do with this data, this time use index 1 (which will be same in the shader)
    glEnableVertexAttribArray(1)  # this could be written later
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0,
                          ctypes.c_void_p(0))  # again 3 floats

    # describe the edges (element buffer), uint32 again here
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBuffer)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array(
        [triangles], dtype=np.uint32), GL_STATIC_DRAW)

    t.end("Upload data to GPU")

    return tricount*3


def SetupOpenGL(returnedLumps):
    global gDrawCount
    global gProjectionMatrixHandle

    t = TimerMs("SetupOpenGL")

    # OpenGL version
    renderer = glGetString(GL_RENDERER)
    version = glGetString(GL_VERSION)
    print('Renderer:', renderer)  # Renderer: b'Intel Iris Pro OpenGL Engine'
    # OpenGL version supported:  b'4.1 INTEL-10.12.13'
    print('OpenGL version supported: ', version)

    # glEnableClientState(GL_VERTEX_ARRAY) #this is not needed?

    if useCustomShader is True:
        t.start("Prepare shader")

        # get world bounds:
        # print(returnedLumps[LumpsEnum.LUMP_VERTICES.value])
        for vert in returnedLumps[LumpsEnum.LUMP_VERTICES.value]:
            # minx = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:, 0].min()
            miny = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:, 1].min()
            # minz = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:, 2].min()
            # maxx = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:, 0].max()
            maxy = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:, 1].max()
            # maxz = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:, 2].max()
        # print(minx,miny,minz,maxx,maxy,maxz)

        program = ProgramWithShader(vertex_shader_perspective, fragment_shader)
        gProjectionMatrixHandle = glGetUniformLocation(
            program, "projection_matrix")
        yminHandle = glGetUniformLocation(program, "ymin")
        ymaxHandle = glGetUniformLocation(program, "ymax")
        glUniform1f(yminHandle, miny)
        glUniform1f(ymaxHandle, maxy)
        assert (gProjectionMatrixHandle != -1)
        t.end("Prepare shader")

    t.start("PrepareFaces")
    # send data from lumps to gpu
    gDrawCount = PrepareFaces(returnedLumps)
    t.end("PrepareFaces")

    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    glEnable(GL_DEPTH_TEST)  # gl_FragCoord in fragment shader
    # glEnable(GL_MULTISAMPLE);
    glLineWidth(2)

    print("DRAWCOUNT", gDrawCount)

    return program

# override debug colors with this
# set to -1 to disable


def SetFragColor(program, color):
    forceColor = glGetUniformLocation(program, "forceColor")
    glUniform1f(forceColor, color)


def DrawOpenGL(cam, display, program):
    global gDrawCount
    global gProjectionMatrixHandle
    # send the final matrix to shader

    # everything is done on model matrix because its simpler
    glLoadIdentity()  # clear the model matrix
    # generate the perspective
    gluPerspective(45, (display[0]/display[1]), cameraNear, cameraFar)
    UpdateViewToCamera(cam)
    # print(cam.pos)

    if useCustomShader is True:
        proj_mat = glGetFloatv(GL_MODELVIEW_MATRIX)  # now take it
        glUniformMatrix4fv(gProjectionMatrixHandle, 1, GL_FALSE, proj_mat)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # here pass pretty much length of element array, no matter the mode
    SetFragColor(program, -1)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glDrawElements(GL_TRIANGLES, gDrawCount, GL_UNSIGNED_INT, None)

    # outline
    SetFragColor(program, 0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawElements(GL_TRIANGLES, gDrawCount, GL_UNSIGNED_INT, None)


def CleanUpOpenGL():
    global gBuffers
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    glDeleteBuffers(1, gBuffers[2])

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glDeleteBuffers(1, gBuffers[1])

    glBindVertexArray(0)
    glDeleteVertexArrays(gBuffers[0])
