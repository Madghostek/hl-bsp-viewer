import struct , matplotlib.pyplot as plt
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

gLumpNames = ["LUMP_ENTITIES","LUMP_PLANES","LUMP_TEXTURES","LUMP_VERTICES","LUMP_VISIBILITY","LUMP_NODES","LUMP_TEXINFO","LUMP_FACES","LUMP_LIGHTING","LUMP_CLIPNODES","LUMP_LEAVES","LUMP_MARKSURFACES","LUMP_EDGES","LUMP_SURFEDGES","LUMP_MODELS","HEADER_LUMPS"]


# basic code that parses BSP header:
def GetGoldsrcHeader(file):
	header = struct.Struct("i30i")
	data = header.unpack(file.read(header.size))
	return data[0],zip(data[1::2],data[2::2]) # version and lumps

# reads lump from stream
def GetRawLump(file,offset,nbytes):
	file.seek(offset)
	return file.read(nbytes)

def GetChunks(raw,length, format):
	chunk = struct.Struct(format)

	size = chunk.size
	# or yield
	return [chunk.unpack(raw[part*size:(part+1)*size]) for part in range(length//size)]

# do something with vertices, here I dump them to array of points
def VerticesCallback(raw,length,returnedLumps, myindex):
	vertices = GetChunks(raw, length, "fff") # xyz
	returnedLumps[myindex]=np.concatenate(np.array(vertices, dtype=np.float32))
	print(returnedLumps[myindex])
	#print(vertices)
	#plot them
	#fig = plt.figure()
	#ax = fig.add_subplot(111, projection='3d')

def ClipnodesCallback(raw,length,returnedLumps, myindex):
	nodes = GetChunks(raw, length, "ihh") # int32 planes index, int16[2] children?
	for index,data1,data2 in nodes:
		print(index,hex(data1),hex(data2))

def EdgesCallback(raw, length,returnedLumps, myindex):
	edges = GetChunks(raw, length, "HH")
	returnedLumps[myindex]=np.array(edges, dtype=np.int16)



gCallbacks = {
	3: VerticesCallback, # used only for edges
	#9: ClipnodesCallback,
	12: EdgesCallback,
}

vertex_shader1 = """#version 410
layout(location = 0) in vec3 pos;
void main () {
    gl_Position = vec4(pos.x,pos.y,pos.z, 1.0f);
}""" # lub pos


def pe():
	print("error",glGetError())


def ProgramWithShader(vertexShader):
	#shader
	prog = glCreateProgram()
	shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(shader, vertexShader)
	pe()
	glCompileShader(shader);
	glAttachShader(prog, shader);
	
	pe()
	glLinkProgram(prog);
	print("LOG:",glGetProgramInfoLog(prog))
	pe()
	glUseProgram(prog);
	pe()
	print("Program done")

class Camera():
	def __init__(self,display,x=0.0,y=0.0,z=0.0,pitch=0.0,yaw=0.0,roll=0.0,fov=45.0):
		self.pos = np.array([x,y,z],dtype=np.float32)
		self.angle = np.array([pitch,roll,yaw],dtype=np.float32)
		self.fov = fov
		self.display = display

	def updateView(self):
		glLoadIdentity()
		gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 10000)
		glRotatef(-self.angle[0],1,0,0);
		glRotatef(-self.angle[1],0,1,0)
		glRotatef(-self.angle[2],0,0,1)
		glTranslatef(*self.pos)

	# du - forward backward, dw - left right
	def moveLocal(self,du,dw):
		#angle=-90
		#pos[0] should decrease
		self.pos[0]-=dw*np.sin(np.radians(self.angle[2]))+du*np.cos(np.radians(self.angle[2]))
		self.pos[1]+=dw*np.cos(np.radians(self.angle[2]))-du*np.sin(np.radians(self.angle[2]))
		print(self.pos)
		print(self.angle[2])
		print(du,dw)


def main(lumpNames, callbacks):
	testverts = np.concatenate(np.array([[0,0,0], [0,100,0], [100,100,0]], dtype=np.float32))
	testedges = np.array([0,1,1,2,2,0], dtype=np.int16)

	returnedLumps = [[] for _ in range(len(lumpNames))]
	with open("dd2.bsp","rb") as bsp:
		version, lumps = GetGoldsrcHeader(bsp)
		print("version:",version)
		print("lumps table:")
		for idx,element in enumerate(lumps):
			offset,length = element
			rawData = GetRawLump(bsp,offset,length)
			print(idx,offset,length)
			with open(lumpNames[idx]+".raw","wb") as f:
				f.write(rawData)

			if idx in callbacks:
				#print("calling",idx,hex(length))
				callbacks[idx](rawData, length, returnedLumps, idx)

	#returnedLumps[3]=testverts
	#returnedLumps[12]=testedges
	#after parsing
	pygame.init()
	display = (800,600)
	pygame.display.set_mode(display, DOUBLEBUF|OPENGL)


	#OpenGL version

	renderer = glGetString(GL_RENDERER)
	version = glGetString(GL_VERSION)
	print('Renderer:', renderer)  # Renderer: b'Intel Iris Pro OpenGL Engine'
	print('OpenGL version supported: ', version)  # OpenGL version supported:  b'4.1 INTEL-10.12.13'

	#glEnableClientState(GL_VERTEX_ARRAY) #this is not needed?

	#ProgramWithShader(vertex_shader1)
	# #init buffers
	vinfo = GLuint()
	glGenVertexArrays(1, vinfo)
	glBindVertexArray(vinfo)
	b1 = GLuint()
	glGenBuffers(1, b1)

	indexBuffer = GLuint()
	glGenBuffers(1, indexBuffer);


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

	#glViewport(0,0,400,400)
	cam = Camera(display,0,-50,-300,90,0,0)
	pygame.event.set_grab(True) # lock mouse
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			#if event.type == pygame.KEYDOWN:
			#	transMatrix = [];
			#	glGetFloatv(GL_MODELVIEW_MATRIX, transMatrix);
			#	print(transMatrix)
		keys = pygame.key.get_pressed()
		if keys[pygame.K_d]:
			cam.moveLocal(10,0)
		if keys[pygame.K_a]:
			cam.moveLocal(-10,0)
		if keys[pygame.K_UP]:
			cam.pos[2]-=10
		if keys[pygame.K_DOWN]:
			cam.pos[2]+=10
		if keys[pygame.K_q]:
			cam.angle[2]+=1
		if keys[pygame.K_e]:
			cam.angle[2]-=1
		if keys[pygame.K_w]:
			cam.moveLocal(0,-10)
		if keys[pygame.K_s]:
			cam.moveLocal(0,10)
		if keys[pygame.K_i]:
			cam.pos = np.array([0,0,0])
			cam.angle = np.array([0,0,0,0])

		if keys[pygame.K_ESCAPE]:
			pygame.event.set_grab(pygame.event.get_grab()^1) # lock mouse


		x,y = pygame.mouse.get_rel()
		if pygame.mouse.get_pressed()[0]:
			cam.angle[2]+=x*0.1
			cam.angle[0]+=y*0.1


		cam.updateView();
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		#glLoadIdentity()
		#glTranslatef(0,-50,-300)
		#glRotatef(-90, 1,0,0)
		#gluPerspective(45, (display[0]/display[1]), 0.1, 10000)
		glDrawElements(GL_LINES, len(returnedLumps[3]), GL_UNSIGNED_SHORT,None)

		pygame.display.flip()
		pygame.time.wait(10)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, indexBuffer);
if __name__=="__main__":
	main(gLumpNames,gCallbacks)