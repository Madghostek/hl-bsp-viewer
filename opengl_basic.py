from OpenGL.GL import *
from OpenGL.GLU import *
# Config
########
useCustomShader = True

########

# globals
gProjectionMatrixHandle = -1
gDrawCount = -1

gBuffers = []

vertex_shader_perspective = """#version 410
layout(location = 0) in vec3 pos;
uniform mat4 projection_matrix;

out vec4 position;
void main () {
    gl_Position = projection_matrix*vec4(pos, 1.0f);
    position = vec4(pos, 1.0f);;
}""" # lub pos

fragment_shader = """#version 410

in vec4 position;
out vec4 FragColor;

uniform float ymin;
uniform float ymax;

void main(){

	FragColor = vec4(1,2*(position.y-ymin)/(ymax-ymin),2-2*(position.y-ymin)/(ymax-ymin), 1.0);
}"""

def UpdateViewToCamera(c):
	glRotatef(-c.angle[0],1,0,0);
	glRotatef(-c.angle[1],0,1,0)
	glRotatef(-c.angle[2],0,0,1)
	glTranslatef(*c.pos)

def pe():
	print("error",glGetError())

def ProgramWithShader(vertexShader, fragmentShader = None):
	#shader
	prog = glCreateProgram()
	shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(shader, vertexShader)
	pe()
	glCompileShader(shader);
	res = glGetShaderiv(shader,GL_COMPILE_STATUS)
	print("vertex shader compilation status:","OK" if res==GL_TRUE else "ERROR")
	assert (res == GL_TRUE)
	glAttachShader(prog, shader);
	print("LOG:",glGetProgramInfoLog(prog))

	if fragmentShader:
		shader = glCreateShader(GL_FRAGMENT_SHADER)
		glShaderSource(shader, fragmentShader)
		pe()
		glCompileShader(shader);
		print("LOG:",glGetProgramInfoLog(prog))
		glAttachShader(prog, shader)
		res = glGetShaderiv(shader,GL_COMPILE_STATUS)
		print("Fragment shader compilation status:","OK" if res==GL_TRUE else "ERROR")
		assert (res == GL_TRUE)

		

	pe()
	glLinkProgram(prog);
	pe()
	glUseProgram(prog);
	pe()
	print("Program done")
	return prog

def SetupOpenGL(returnedLumps):
	global gDrawCount
	global gProjectionMatrixHandle
	global gBuffers

	#OpenGL version
	renderer = glGetString(GL_RENDERER)
	version = glGetString(GL_VERSION)
	print('Renderer:', renderer)  # Renderer: b'Intel Iris Pro OpenGL Engine'
	print('OpenGL version supported: ', version)  # OpenGL version supported:  b'4.1 INTEL-10.12.13'

	#glEnableClientState(GL_VERTEX_ARRAY) #this is not needed?

	if useCustomShader == True:

		# get world bounds:
		print(returnedLumps[3])
		for vert in returnedLumps[3]:
			minx = returnedLumps[3][:,0].min()
			miny = returnedLumps[3][:,1].min()
			minz = returnedLumps[3][:,2].min()
			maxx = returnedLumps[3][:,0].max()
			maxy = returnedLumps[3][:,1].max()
			maxz = returnedLumps[3][:,2].max()
		print(minx,miny,minz,maxx,maxy,maxz)

		program = ProgramWithShader(vertex_shader_perspective, fragment_shader)
		gProjectionMatrixHandle = glGetUniformLocation(program, "projection_matrix")
		yminHandle = glGetUniformLocation(program, "ymin")
		ymaxHandle = glGetUniformLocation(program, "ymax")
		glUniform1f(yminHandle, miny)
		glUniform1f(ymaxHandle, maxy)
		assert (gProjectionMatrixHandle!=-1)

	# #init buffers
	vinfo = GLuint()
	glGenVertexArrays(1, vinfo)
	glBindVertexArray(vinfo)
	b1 = GLuint()
	glGenBuffers(1, b1)

	indexBuffer = GLuint()
	glGenBuffers(1, indexBuffer);

	gBuffers = [vinfo,b1,indexBuffer]


	# # tell OpenGL to use the b1 buffer for rendering, and give it data
	glBindBuffer(GL_ARRAY_BUFFER, b1)
	glBufferData(GL_ARRAY_BUFFER, returnedLumps[3], GL_STATIC_DRAW)

	# # describe what the data is (3x float)
	glEnableVertexAttribArray(0);
	# pe()

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0)); #or None
	# pe()

	# describe the edges (element buffer)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBuffer);
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, returnedLumps[12], GL_STATIC_DRAW);

	gDrawCount = len(returnedLumps[12])*2
	print(returnedLumps[12])
	print("DRAWCOUNT",gDrawCount)

def DrawOpenGL(cam,display):
	global gDrawCount
	global gProjectionMatrixHandle
	# send the final matrix to shader

	# everything is done on model matrix because its simpler
	glLoadIdentity() # clear the model matrix
	gluPerspective(45, (display[0]/display[1]), 0.1, 4000) # generate the perspective
	UpdateViewToCamera(cam)

	if useCustomShader == True:
		proj_mat = glGetFloatv(GL_MODELVIEW_MATRIX);	# now take it
		glUniformMatrix4fv(gProjectionMatrixHandle, 1, GL_FALSE, proj_mat);

		

	glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

	glDrawElements(GL_LINES, gDrawCount, GL_UNSIGNED_SHORT,None)	

def CleanUpOpenGL():
	global gBuffers
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, gBuffers[2]);

	glBindBuffer(GL_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, gBuffers[1]);

	glBindVertexArray(0)
	glDeleteVertexArrays(gBuffers[0])