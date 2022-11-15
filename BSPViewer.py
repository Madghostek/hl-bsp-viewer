import numpy as np
import argparse

from BSP import *
import json

import os # for os.path.basename

def RunWindow(returnedLumps):
	import pygame
	import pygame.locals
	from camera import Camera
	import opengl_basic

	print("Pygame init")
	pygame.init()
	display = (800,600)
	pygame.display.set_mode(display, pygame.locals.DOUBLEBUF|pygame.locals.OPENGL)

	print("OpenGL init")
	program = opengl_basic.SetupOpenGL(returnedLumps)

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

		opengl_basic.DrawOpenGL(cam,display, program)

		pygame.display.flip()
		pygame.time.wait(10)

	# cleanup @TODO: Move this to quit event :|
	print("exit")
	opengl_basic.CleanupOpenGL()

def EntitiesToPythonDict(ents: str):
	afterReplace = ents.replace(" ",":").replace('"\n"','",\n"').replace('\\', '\\\\').replace("}\n{", "},\n{")
	jsonable = "["+afterReplace+"]"

	return json.loads(jsonable)


def GetAllBoostCoords(ents,lumps):
	boosts = []
	for e in ents:
		if e['classname']=='trigger_push':
			# find model index:
			mIdx = int(e['model'][1:])

			# get that model from lumps
			model = lumps[LumpsEnum.LUMP_MODELS.value][mIdx]

			# get faces
			facesIdx, nFaces = model[14], model[15]

			# get all edges
			edges = []

			for face in lumps[LumpsEnum.LUMP_FACES.value][facesIdx:facesIdx+nFaces]:
				surfedgesIdx, nSurfedges = face[0],face[1]
				edges.extend(lumps[LumpsEnum.LUMP_SURFEDGES.value][surfedgesIdx:surfedgesIdx+nSurfedges])

			edges=np.concatenate(edges)

			# make all indices positive
			edges = set(map(lambda x: abs(x),edges))

			# get all vertex values
			realedges = []
			for edge in edges:
				v1i, v2i = lumps[LumpsEnum.LUMP_EDGES.value][edge]
				v1, v2 = lumps[LumpsEnum.LUMP_VERTICES.value][v1i].tolist(),lumps[LumpsEnum.LUMP_VERTICES.value][v2i].tolist()
				realedges.append([tuple(map(lambda x: round(x,2),v1)),tuple(map(lambda x: round(x,2),v2))])
			boosts.append(realedges)
	return boosts

# def DebugBoost(coords):
# 	import matplotlib.pyplot as plt
# 	from mpl_toolkits.mplot3d import Axes3D

# 	fig = plt.figure()
# 	ax  = fig.add_subplot(111, projection = '3d')

# 	x,y,z=[],[],[]
# 	for edge in coords:
# 		print(edge)
# 		ax.plot([edge[0][0],edge[1][0]],[edge[0][1],edge[1][1]],[edge[0][2],edge[1][2]])
# 	plt.show()

def main():

	parser = argparse.ArgumentParser(
					formatter_class=argparse.RawTextHelpFormatter,
                    prog = 'BSPViewer.py',
                    description = 'View BSP maps',
                    epilog = 'examples: \tpython3 BSPViewer.py maps/de_dust2.bsp -d\n\
		python3 BSPViewer.py maps/de_dust2.bsp -b output.json\n\
		python3 BSPViewer.py maps/de_dust2.bsp -b -s csv')
	parser.add_argument('filename', type=str, help='BSP map path')
	parser.add_argument('--boosts', '-b', nargs='?',  help='find boosts present in map and save edge coordinates to a file. If `--serialiser` not specified, Deduces output format from extension (json or csv)', const="nopath")
	parser.add_argument('--serialiser','-s', help='`boosts` optput format, if no output filename given')
	parser.add_argument('--display','-d',action='store_true', help='show map in OpenGL window')
	args = parser.parse_args()

	if args.serialiser not in ('csv','json', None):
		print("Serialiser invalid, only csv and json available")
		exit(1)
	if args.boosts!="nopath" and args.boosts[-5:] != '.json' and args.boosts[-4:] != '.csv':
		print("Boosts file output invalid, only .csv and .json available")
		exit(1)
	
	serialiser = args.serialiser if args.serialiser else "json" if args.boosts[-5:]==".json" else "csv"

	# lumps are returned as np.array, sometimes signed.
	# entity lump is special, its just a string
	# lump mask can be used to filter out not needed lumps, this speeds up calculation
	# it's a bitmask, where each lump has nth bit, so use powers of 2
	# if args.display:
	# 	mask|=2**15-1 #everything
	returnedLumps = GetBSPData(args.filename)

	if args.boosts:
		ents = EntitiesToPythonDict(returnedLumps[LumpsEnum.LUMP_ENTITIES.value])

		# list of boosts in map
		#	- boost is a tuple of 12 edges (parallelpiped)
		#		- edge is a tuple of two vertices
		#			- vertex is a tuple of 3 floats
		boostCoords = GetAllBoostCoords(ents, returnedLumps)
		
		#DebugBoost(boostCoords[0])

		for idx,boost in enumerate(boostCoords):
			print(f"boost #{idx}:")
			for edge in boost:
				print("\t",edge)
		if serialiser == 'json':
			boostsString = json.dumps(boostCoords)
			fname = args.filename[:-5]+"_boosts.json" if args.boosts == "nopath" else args.boosts
			print("writing to ",fname)
			with open(fname, "w") as f:
				f.write(boostsString)
		else:
			import csv
			fname = args.filename[:-4]+"_boosts.csv" if args.boosts == "nopath" else args.boosts
			print("writing to",fname)
			with open(fname, 'w') as csvfile:
				#writer = csv.writer(csvfile,quoting=csv.QUOTE_NONE, delimiter='\t')
				writer = csv.writer(csvfile,quoting=csv.QUOTE_NONE, delimiter=",")
				base = os.path.basename(args.filename)[:-4]
				for idx,boost in enumerate(boostCoords):
					for eIdx,edge in enumerate(boost):
						values = [base, f"boost #{idx+1} {eIdx+1}/{len(boost)}", *edge[0],*edge[1], 3]
						writer.writerow(values)

	
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
	if args.display:
		RunWindow(returnedLumps)

if __name__=="__main__":
	main()