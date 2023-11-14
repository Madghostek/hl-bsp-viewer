import numpy as np

def SeparateVertices(triangles, vertices):
	"""
	Prepares for coloring
	triangles - numpy list of (v1,v2,v3) tuples - indices into vertices
	vertices - numpy list, actual (x,y,z) points that make up triangles

	returns tuple	- list of triangles, will always
					- list on new vertices (flattened), that has duplicates now
	"""
	separatedVertices = (vx for tri in triangles for v in tri for vx in vertices[v])

	rebuildedVectices = np.fromiter(separatedVertices, dtype=vertices.dtype)
	# dtype is 32 bit, because there is a chance to overflow after separating
	rebuildedTriangles = np.fromiter(range(len(rebuildedVectices)), dtype=np.uint32)

	return rebuildedTriangles, rebuildedVectices