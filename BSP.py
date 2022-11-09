import struct, numpy as np
from enum import IntEnum

gLumpNames = ["LUMP_ENTITIES","LUMP_PLANES","LUMP_TEXTURES","LUMP_VERTICES","LUMP_VISIBILITY","LUMP_NODES","LUMP_TEXINFO","LUMP_FACES","LUMP_LIGHTING","LUMP_CLIPNODES","LUMP_LEAVES","LUMP_MARKSURFACES","LUMP_EDGES","LUMP_SURFEDGES","LUMP_MODELS","HEADER_LUMPS"]

class LumpsEnum(IntEnum):
	LUMP_ENTITIES = 0
	LUMP_PLANES = 1
	LUMP_TEXTURES = 2
	LUMP_VERTICES = 3
	LUMP_VISIBILITY = 4
	LUMP_NODES = 5
	LUMP_TEXINFO = 6
	LUMP_FACES = 7
	LUMP_LIGHTING = 8
	LUMP_CLIPNODES = 9
	LUMP_LEAVES = 10
	LUMP_MARKSURFACES = 11
	LUMP_EDGES = 12
	LUMP_SURFEDGES = 13
	LUMP_MODELS = 14
	HEADER_LUMPS = 15

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

# do something with vertices, here I dump them to array of points
def VerticesCallback(raw,length,returnedLumps):
	vertices = GetChunks(raw, length, "fff") # xyz
	returnedLumps[LumpsEnum.LUMP_VERTICES.value]=np.array(vertices, dtype=np.float32)

def FacesCallback(raw,length, returnedLumps):
	# planes index, orientation (bool), index of first surfedge, number of next surfedges, index into textureinfo, 4 lighting styles, lightmap offset
	
	# right now only surfedges are interesting for me
	faces = GetChunks(raw, length, "hhihh4bi")
	onlyEdges = [(face[2],face[3]) for face in faces]
	returnedLumps[LumpsEnum.LUMP_FACES.value]=np.array(onlyEdges)

def ClipnodesCallback(raw,length,returnedLumps):
	nodes = GetChunks(raw, length, "ihh") # int32 planes index, int16[2] children?
	for index,data1,data2 in nodes:
		print(index,hex(data1),hex(data2))

def EdgesCallback(raw, length,returnedLumps):
	edges = GetChunks(raw, length, "HH")
	returnedLumps[LumpsEnum.LUMP_EDGES.value]=np.array(edges, dtype=np.int16)

def SurfedgesCallback(raw,length,returnedLumps):
	returnedLumps[LumpsEnum.LUMP_SURFEDGES.value]=np.array(GetChunks(raw,length,"i"), dtype=np.int32) # signed ints, indexes into edges

gCallbacks = {
	LumpsEnum.LUMP_VERTICES.value: VerticesCallback, # used only for edges
	LumpsEnum.LUMP_FACES.value: FacesCallback,
	#9: ClipnodesCallback,
	LumpsEnum.LUMP_EDGES.value: EdgesCallback,
	LumpsEnum.LUMP_SURFEDGES.value: SurfedgesCallback
}

def GetBSPData(fname):
	returnedLumps = [[False] for _ in range(len(gLumpNames))]
	with open(fname,"rb") as bsp:
		version, lumps = GetGoldsrcHeader(bsp)
		print("version:",version)
		print("lumps table:")
		for idx,element in enumerate(lumps):
			offset,length = element
			rawData = GetRawLump(bsp,offset,length)
			print(idx,offset,length)
			#with open(lumpNames[idx]+".raw","wb") as f:
				#f.write(rawData)

			if idx in gCallbacks:
				gCallbacks[idx](rawData, length, returnedLumps)
				print(idx,"Result:",returnedLumps[idx])
	return returnedLumps