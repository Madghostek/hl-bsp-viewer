import struct, numpy as np

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

def SurfedgesCallback(raw,length,returnedLumps,myindex):
	returnedLumps[myindex]=np.array(GetChunks(raw,length,"i"), dtype=np.int32) # signed ints, indexes into edges

gCallbacks = {
	3: VerticesCallback, # used only for edges
	#9: ClipnodesCallback,
	12: EdgesCallback,
	13: SurfedgesCallback
}

def GetBSPData(fname):
	returnedLumps = [[] for _ in range(len(gLumpNames))]
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
				gCallbacks[idx](rawData, length, returnedLumps, idx)
				print(idx,"Result:",returnedLumps[idx])
	return returnedLumps