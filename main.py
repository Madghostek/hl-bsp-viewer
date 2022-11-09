import struct , matplotlib.pyplot as plt
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from camera import Camera
from opengl_basic import *

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
	returnedLumps[myindex]=np.array(vertices, dtype=np.float32)

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

def UpdateViewToCamera(c):
	glRotatef(-c.angle[0],1,0,0);
	glRotatef(-c.angle[1],0,1,0)
	glRotatef(-c.angle[2],0,0,1)
	glTranslatef(*c.pos)

def main(lumpNames, callbacks):

	useCustomShader = True

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
			#with open(lumpNames[idx]+".raw","wb") as f:
				#f.write(rawData)

			if idx in callbacks:
				#print("calling",idx,hex(length))
				callbacks[idx](rawData, length, returnedLumps, idx)

	#debug 
	#returnedLumps[3]=testverts
	#returnedLumps[12]=testedges

	#after parsing
	pygame.init()
	display = (800,600)
	pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

	SetupOpenGL(returnedLumps)

	#glViewport(0,0,400,400)
	cam = Camera(0,-50,-300,90,0,0)
	pygame.event.set_grab(True) # lock mouse
	while True:
		keys = pygame.key.get_pressed()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					pygame.event.set_grab(pygame.event.get_grab()^1) # lock mouse
				if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
					cam.reset()

		modifier = 0.2 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
		if keys[pygame.K_d]:
			cam.moveLocal(10*modifier,0)
		if keys[pygame.K_a]:
			cam.moveLocal(-10*modifier,0)
		if keys[pygame.K_UP]:
			cam.pos[2]-=10*modifier
		if keys[pygame.K_DOWN]:
			cam.pos[2]+=10*modifier
		if keys[pygame.K_q]:
			cam.angle[2]+=1*modifier
		if keys[pygame.K_e]:
			cam.angle[2]-=1*modifier
		if keys[pygame.K_w]:
			cam.moveLocal(0,-10*modifier)
		if keys[pygame.K_s]:
			cam.moveLocal(0,10*modifier)
		if keys[pygame.K_i]:
			cam.pos = np.array([0,0,0])
			cam.angle = np.array([0,0,0,0])


		x,y = pygame.mouse.get_rel()
		if pygame.mouse.get_pressed()[0]:
			cam.angle[2]+=x*0.1
			cam.angle[0]+=y*0.1

		# everything is done on model matrix because its simpler
		glLoadIdentity() # clear the model matrix
		gluPerspective(45, (display[0]/display[1]), 0.1, 4000) # generate the perspective
		UpdateViewToCamera(cam)

		DrawOpenGL()

		pygame.display.flip()
		pygame.time.wait(10)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
	glDeleteBuffers(1, indexBuffer);
if __name__=="__main__":
	main(gLumpNames,gCallbacks)