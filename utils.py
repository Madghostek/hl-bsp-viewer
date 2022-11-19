# special parsing utilities
import json
import numpy as np
from BSP import *

def EntitiesToPythonDict(ents: str):
	afterReplace = ents.replace(" ",":").replace('"\n"','",\n"').replace('\\', '\\\\').replace("}\n{", "},\n{")
	jsonable = "["+afterReplace+"]"

	return json.loads(jsonable)


# returns a list of edges of model, for each entity with matching classname
def GetAllClassLines(ents,lumps, classname):
	EntityBoundLines = {}
	for e in ents:
		if e['classname']==classname:
			# find model index:
			try:
				e['model']
			except:
				raise ValueError("This classname doesn't have a model!")

			mIdx = int(e['model'][1:])


			# get that model from lumps
			model = lumps[LumpsEnum.LUMP_MODELS.value][mIdx]
			
			# get faces
			facesIdx, nFaces = model[14], model[15]

			if nFaces<=0:
				print("!!! WARNING !!!")
				print(f"{classname} *{mIdx} Invalid face count:",nFaces)
				continue

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

			description = classname+" "+e['model']

			EntityBoundLines[description]=realedges
	return EntityBoundLines

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