import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from camera import Camera
from opengl_basic import *
from BSP import *

def main():

	useCustomShader = True

	testverts = np.concatenate(np.array([[0,0,0], [0,100,0], [100,100,0]], dtype=np.float32))
	testedges = np.array([0,1,1,2,2,0], dtype=np.int16)

	returnedLumps = GetBSPData("dd2.bsp")

	#debug 
	#returnedLumps[3]=testverts
	#returnedLumps[12]=testedges

	#after parsing
	print("Pygame init")
	pygame.init()
	display = (800,600)
	pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

	print("OpenGL init")
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

	# cleanup @TODO: Move this to quit event :|
	print("exit")
	CleanupOpenGL()

if __name__=="__main__":
	main()