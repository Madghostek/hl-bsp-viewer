from OpenGL.GL import *
from OpenGL.GLU import *
from BSP import LumpsEnum
import numpy as np
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

def PrepareEdges(returnedLumps):
	global gBuffers, gDrawCount

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
	glBufferData(GL_ARRAY_BUFFER, returnedLumps[LumpsEnum.LUMP_VERTICES.value], GL_STATIC_DRAW)

	# # describe what the data is (3x float)
	glEnableVertexAttribArray(0);
	# pe()

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0)); #or None
	# pe()

	# describe the edges (element buffer)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBuffer);
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, returnedLumps[LumpsEnum.LUMP_EDGES.value], GL_STATIC_DRAW);

	return len(returnedLumps[LumpsEnum.LUMP_EDGES.value])*2

def PrepareFaces(returnedLumps):
	# split n-gons into triangles...
	# when faces lump wants more than 3 vertices at once, split them into 0 1 2, 0 3 4, 0 4 5
	# now these indices can be inserted into element array, then GL_TRIANGLES can be used!
	triangles = []
	tricount=0
	edges = returnedLumps[LumpsEnum.LUMP_EDGES.value]
	surfedges = returnedLumps[LumpsEnum.LUMP_SURFEDGES.value]
	print("prepare faces from surfedges,",len(surfedges))
	for face in returnedLumps[LumpsEnum.LUMP_FACES.value]:
		# for each face, figure out which surfedges (then real edges) it uses,
		# then get list of all vertex indices used by face, but in a way that every 3 make a triangle

		# this means - get first "base" index, take second index, take next edge and one of the indices (the new one),
		# take next edge and another new index, until all edges from face taken, save the triplets to triangles array
		print(face)
		base = face[0]
		count = face[1]-1 #!!! since im building triangles on my own, the last edge is not needed
		tricount+=count-1 # 4 edges = 2 tris, 5 edges = 3 tris etc
		print("the edges that will make a face:",surfedges[base:base+count+1])
		print("which have these indices...")
		for i in range(count):
			print(edges[abs(surfedges[base+i][0])])
		first = edges[surfedges[base][0]]
		print("first",first,surfedges[base][0])
		if surfedges[base][0]>=0:
			astri=[first[0],first[1]]
		else:
			astri=[first[1],first[0]]
		print("first two:",astri)
		first = astri[0]
		sedge = surfedges[base+1]
		print(sedge)
		newedge = edges[sedge[0]]
		print(newedge)
		if sedge[0]<=0:
			newidx=newedge[0]
		else:
			newidx = newedge[1]
		astri.append(newidx)

		cur = 2
		print("first tri:",astri)
		while cur<count:
			sedge = surfedges[base+cur]
			print(sedge)
			newedge = edges[abs(sedge[0])] 
			print(newedge)
			if sedge[0]<=0:
				newidx=newedge[0]
			else:
				newidx = newedge[1]
			print(newidx)
			astri.extend([first,astri[-1],newidx]) #append base and last one
			print("more",astri)
			cur+=1
		for i in range(0,len(astri),3):
			triangles.append(astri[i:i+3])
	print("final tri list",triangles)

	# turn that into ndarray, send as element buffer (vertex buffer is the same as last time, draw with GL_TRIANGLES...)

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
	glBufferData(GL_ARRAY_BUFFER, returnedLumps[LumpsEnum.LUMP_VERTICES.value], GL_STATIC_DRAW)


	# # describe what the data is (3x float)
	glEnableVertexAttribArray(0);

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0)); #or None

	# describe the edges (element buffer)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBuffer);
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([triangles],dtype=np.int16), GL_STATIC_DRAW);

	return tricount*3

def SetupOpenGL(returnedLumps):
	global gDrawCount
	global gProjectionMatrixHandle

	#OpenGL version
	renderer = glGetString(GL_RENDERER)
	version = glGetString(GL_VERSION)
	print('Renderer:', renderer)  # Renderer: b'Intel Iris Pro OpenGL Engine'
	print('OpenGL version supported: ', version)  # OpenGL version supported:  b'4.1 INTEL-10.12.13'

	#glEnableClientState(GL_VERTEX_ARRAY) #this is not needed?

	if useCustomShader == True:

		# get world bounds:
		print(returnedLumps[LumpsEnum.LUMP_VERTICES.value])
		for vert in returnedLumps[LumpsEnum.LUMP_VERTICES.value]:
			minx = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:,0].min()
			miny = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:,1].min()
			minz = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:,2].min()
			maxx = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:,0].max()
			maxy = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:,1].max()
			maxz = returnedLumps[LumpsEnum.LUMP_VERTICES.value][:,2].max()
		print(minx,miny,minz,maxx,maxy,maxz)

		program = ProgramWithShader(vertex_shader_perspective, fragment_shader)
		gProjectionMatrixHandle = glGetUniformLocation(program, "projection_matrix")
		yminHandle = glGetUniformLocation(program, "ymin")
		ymaxHandle = glGetUniformLocation(program, "ymax")
		glUniform1f(yminHandle, miny)
		glUniform1f(ymaxHandle, maxy)
		assert (gProjectionMatrixHandle!=-1)

	# send data from lumps to gpu
	gDrawCount = PrepareFaces(returnedLumps)

	#glPolygonMode( GL_FRONT_AND_BACK, GL_LINE );

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

	# here pass pretty much length of element array, no matter the mode
	glDrawElements(GL_TRIANGLES, gDrawCount, GL_UNSIGNED_SHORT,None)	

def CleanUpOpenGL():
	global gBuffers
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, gBuffers[2]);

	glBindBuffer(GL_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, gBuffers[1]);

	glBindVertexArray(0)
	glDeleteVertexArrays(gBuffers[0])