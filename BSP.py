import struct, numpy as np
from enum import IntEnum
import lump_classes

gLumpNames = ["LUMP_ENTITIES","LUMP_PLANES","LUMP_TEXTURES","LUMP_VERTICES","LUMP_VISIBILITY","LUMP_NODES","LUMP_TEXINFO","LUMP_FACES","LUMP_LIGHTING","LUMP_CLIPNODES","LUMP_LEAVES","LUMP_MARKSURFACES","LUMP_EDGES","LUMP_SURFEDGES","LUMP_MODELS","HEADER_LUMPS"]

#arrays of used plane indices, compare these to find clipnodes that use planes that arent rendered?
gClips = []
gFaces = []

class LumpsEnum(IntEnum):
	LUMP_ENTITIES = 0 	 	# ascii data about entities
	LUMP_PLANES = 1  		# plane equations
	LUMP_TEXTURES = 2
	LUMP_VERTICES = 3  		# Vec3D points
	LUMP_VISIBILITY = 4
	LUMP_NODES = 5
	LUMP_TEXINFO = 6
	LUMP_FACES = 7 	 		# indices into edges that make up a face
	LUMP_LIGHTING = 8  	 	# lightmap data
	LUMP_CLIPNODES = 9   	# another BSP tree, but only for collision
	LUMP_LEAVES = 10  		# leaves of BSP tree, they tell what lies inside the region
	LUMP_MARKSURFACES = 11 	# this is dumb and redundant, a indirection into faces
	LUMP_EDGES = 12 	 	# array of tuples v1 v2
	LUMP_SURFEDGES = 13		# simmilar to marksurfaces, does nothing but redirects
	LUMP_MODELS = 14

# basic code that parses BSP header, returns two values, version and 15 tuples (lump infos)
def GetGoldsrcHeader(file):
	header = struct.Struct("i30i")
	data = header.unpack(file.read(header.size))
	return data[0],zip(data[1::2],data[2::2])

# reads lump from stream
def GetRawLump(file,offset,nbytes):
	file.seek(offset)
	return file.read(nbytes)

def GetChunks(raw,length, format):
	chunk = struct.Struct(format)

	size = chunk.size
	# or yield
	return [chunk.unpack(raw[part*size:(part+1)*size]) for part in range(length//size)]

# --- callbacks ---

def EntitiesCallback(raw, length, returnedLumps):
	utf8string = raw[:-1].decode("utf-8") # there is null at end
	returnedLumps[LumpsEnum.LUMP_ENTITIES.value]=utf8string


#normal * point = fDist
def PlanesCallback(raw,length,returnedLumps):
	# !!!! probably broken plane type because numpy messes with dtype
	planes = GetChunks(raw, length, "3ffi") #[Vec3D normal,fDist,plane type]
	returnedLumps[LumpsEnum.LUMP_PLANES.value] = np.array(planes)
	#print(len(planes))

# do something with vertices, here I dump them to array of points
def VerticesCallback(raw,length,returnedLumps):
	vertices = GetChunks(raw, length, "fff") # xyz
	returnedLumps[LumpsEnum.LUMP_VERTICES.value]=np.array(vertices, dtype=np.float32)

def NodesCallback(raw,length,returnedLumps):
	for x in GetChunks(raw, length, "I2h3h3hHH"):
		returnedLumps[LumpsEnum.LUMP_NODES.value].append(lump_classes.Node(x[0],x[1:3],x[3:6],x[6:9],x[9],x[10]))

def FacesCallback(raw,length, returnedLumps):
	global gFaces
	# planes index, orientation (bool), index of first surfedge, number of next surfedges, index into textureinfo, 4 lighting styles, lightmap offset
	
	# right now only surfedges are interesting for me
	faces = GetChunks(raw, length, "hhihh4bi")
	onlyEdges = [(face[2],face[3]) for face in faces]
	returnedLumps[LumpsEnum.LUMP_FACES.value]=np.array(onlyEdges)

	# find planes that don't have a face attached
	# seen = [False for _ in range(len(returnedLumps[LumpsEnum.LUMP_PLANES.value]))]
	# print(len(faces))
	# for face in faces:
	# 	planeIdx = face[0]
	# 	#print("plane:",planeIdx)
	# 	seen[planeIdx]=True
	# notSeen = [idx for idx,val in enumerate(seen) if val]
	# #print("faces planes",notSeen[:100])
	# gFaces = notSeen[:]
# this might not be needed actually
def ClipnodesCallback(raw,length,returnedLumps):
	global gClips
	nodes = GetChunks(raw, length, "ihh") # int32 planes index, int16[2] children?
	#for index,data1,data2 in nodes:
	#	#print("clip",index,hex(data1),hex(data2))
	returnedLumps[LumpsEnum.LUMP_CLIPNODES.value] = np.array(nodes)

	#seen = [False for _ in range(len(returnedLumps[LumpsEnum.LUMP_PLANES.value]))]
	#print(len(nodes))
	#for node in nodes:
	#	planeIdx = node[0]
	#	#print("plane:",planeIdx)
	#	seen[planeIdx]=True
	#print(f"clipnodes planes {len(nodes)}")
	#print("how many unique:",sum(seen))

def LeavesCallback(raw,length,returnedLumps):
	leaves = GetChunks(raw, length, "ii3h3hHH4B")
	# for l in leaves:
	# 	#print(l)
	# 	if l[0] not in (-1,-6):
	# 		print(l)
	# 	if l[0]==-2: #type
	# 		#solid
	# 		if l[9]==0 or l[8]<0: #amount of marksurfs
	# 			print("invisible solid",l)
	# 		else:
	# 			ind=l[8]
	# 			if returnedLumps[LumpsEnum.LUMP_MARKSURFACES.value][ind]==0:
	# 				print("nonsense faces",l)
	# 			else:
	# 				print("valid solid:",l)
	returnedLumps[LumpsEnum.LUMP_LEAVES.value]=np.array(leaves)

def MarksurfacesCallback(raw,length,returnedLumps):
	msurfs = GetChunks(raw, length, "H")
	#print(msurfs)
	returnedLumps[LumpsEnum.LUMP_MARKSURFACES.value]=np.array(msurfs, dtype=np.uint16)

def EdgesCallback(raw, length,returnedLumps):
	edges = GetChunks(raw, length, "HH")
	returnedLumps[LumpsEnum.LUMP_EDGES.value]=np.array(edges, dtype=np.uint16)
	#print(edges)

def SurfedgesCallback(raw,length,returnedLumps):
	returnedLumps[LumpsEnum.LUMP_SURFEDGES.value]=np.array(GetChunks(raw,length,"i"), dtype=np.int32) # signed ints, indexes into edges

def ModelsCallback(raw,length,returnedLumps):
	# bounding box, then origin coords, then hulls, then Vis leafs index, then finally first face index and face count

	for x in GetChunks(raw,length,"3f3f3f4ii2i"):
		returnedLumps[LumpsEnum.LUMP_MODELS.value].append(lump_classes.Model(x[0:3],x[3:6],x[6:9],x[9:13],x[13],x[14],x[15]))



gCallbacks = {
	LumpsEnum.LUMP_ENTITIES.value: EntitiesCallback,
	LumpsEnum.LUMP_PLANES.value: PlanesCallback,
	LumpsEnum.LUMP_VERTICES.value: VerticesCallback, # used only for edges
	LumpsEnum.LUMP_NODES.value: NodesCallback,
	LumpsEnum.LUMP_FACES.value: FacesCallback,
	LumpsEnum.LUMP_CLIPNODES.value: ClipnodesCallback,
	LumpsEnum.LUMP_LEAVES.value : LeavesCallback,
	LumpsEnum.LUMP_MARKSURFACES.value: MarksurfacesCallback,
	LumpsEnum.LUMP_EDGES.value: EdgesCallback,
	LumpsEnum.LUMP_SURFEDGES.value: SurfedgesCallback,
	LumpsEnum.LUMP_MODELS.value: ModelsCallback
}

def GetBSPData(fname, debug=False, lumpsMask = 0x8000-1) -> lump_classes.LumpCollection:
	returnedLumps = [[] for _ in range(len(gLumpNames))]
	with open(fname,"rb") as bsp:
		version, lumps = GetGoldsrcHeader(bsp)
		if debug:
			print("version:",version)
			print("lumps table:")
		for idx,element in enumerate(lumps):
			offset,length = element
			rawData = GetRawLump(bsp,offset,length)
			if debug:
				print(idx,offset,length)
			with open(gLumpNames[idx]+".raw","wb") as f:
				f.write(rawData)

			if idx in gCallbacks and lumpsMask&2**idx:
				gCallbacks[idx](rawData, length, returnedLumps)
				if debug:
					print(LumpsEnum(idx).name,"Result:",returnedLumps[idx])

	#compared = [x for x in gClips if x not in set(gFaces)]
	#print(compared)
	return returnedLumps