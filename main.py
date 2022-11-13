import numpy as np
import pygame
from pygame.locals import *

from camera import Camera
from opengl_basic import *
from BSP import *

def RunWindow(returnedLumps):
	print("Pygame init")
	pygame.init()
	display = (800,600)
	pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

	print("OpenGL init")
	program = SetupOpenGL(returnedLumps)

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

		if pygame.key.get_mods() & pygame.KMOD_CTRL and keys[pygame.K_g]:
			tmp=pygame.event.get_grab()
			pygame.event.set_grab(0)
			strXYZ=input("goto (x,y,z):")
			coords = list(map(float,strXYZ.split(",")))
			cam.pos[0] = coords[0]
			cam.pos[1] = coords[1]
			cam.pos[2] = coords[2]
			pygame.event.set_grab(tmp)


		x,y = pygame.mouse.get_rel()
		if pygame.mouse.get_pressed()[0]:
			cam.angle[2]+=x*0.1
			cam.angle[0]+=y*0.1

		DrawOpenGL(cam,display, program)

		pygame.display.flip()
		pygame.time.wait(10)

	# cleanup @TODO: Move this to quit event :|
	print("exit")
	CleanupOpenGL()

def EntitiesToPythonDict(ents: str):
	import json
	afterReplace = ents.replace(" ",":").replace('"\n"','",\n"').replace('\\', '\\\\').replace("}\n{", "},\n{")
	jsonable = "["+afterReplace+"]"

	return json.loads(jsonable)

def BoundsToLines(mins, maxs):
	# parallelpiped has 12 edges

	edges = []
	# coming from min vertex
	edges.append((mins,(maxs[0],mins[1],mins[2])))
	edges.append((mins,(mins[0],maxs[1],mins[2])))
	edges.append((mins,(mins[0],mins[1],maxs[2])))

	# coming from max vertex
	edges.append((maxs,(mins[0],maxs[1],maxs[2])))
	edges.append((maxs,(maxs[0],mins[1],maxs[2])))
	edges.append((maxs,(maxs[0],maxs[1],mins[2])))

	# near min
	edges.append(((mins[0],maxs[1],mins[2]),(mins[0],maxs[1],maxs[2])))
	edges.append(((mins[0],maxs[1],mins[2]),(maxs[0],maxs[1],mins[2])))

	# near max
	edges.append(((mins[0],maxs[1],mins[2]),(maxs[0],mins[1],mins[2])))
	edges.append(((maxs[0],mins[1],maxs[2]),(mins[0],mins[1],maxs[2])))

	return edges



def GetAllBoostCoords(ents,lumps):
	boosts = []
	for e in ents:
		if e['classname']=='trigger_push':
			# find model index:
			mIdx = int(e['model'][1:])

			# get that model from lumps
			model = lumps[LumpsEnum.LUMP_MODELS.value][mIdx]

			# get bounds:

			nMins, nMaxs = list(map(lambda x: -x,model[0:3])),list(map(lambda x: -x,model[3:6]))
			lines = BoundsToLines(nMins,nMaxs)
			boosts.append(lines)
	return boosts
def main():

	useCustomShader = True

	# lumps are returned as np.array, sometimes signed.
	# entity lump is special, its just a string
	returnedLumps = GetBSPData("maps/surf_desert_city.bsp")

	ents = EntitiesToPythonDict(returnedLumps[LumpsEnum.LUMP_ENTITIES.value])

	boostCoords = GetAllBoostCoords(ents, returnedLumps)
	print("boosts:",boostCoords)

	
	#debug 
	# testverts = np.array([[-100,500,300], [100,500,300], [100,500,500]], dtype=np.float32)
	# testedges = np.array([[0,1],[1,2],[2,0]], dtype=np.int16)
	# testsurfedges = np.array([[0],[1],[2]], dtype=np.int32)
	# testfaces = np.array([[0,3]], dtype=np.int32)
	
	#returnedLumps[3]=testverts
	#returnedLumps[12]=testedges
	#returnedLumps[13]=testsurfedges
	#returnedLumps[7]=testfaces

	#after parsing
	RunWindow(returnedLumps)

if __name__=="__main__":
	main()