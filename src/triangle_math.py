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


scalar = float # a scale value (0.0 to 1.0)
def hsv_to_rgb( h:scalar, s:scalar, v:scalar, a:scalar ) -> tuple:
    if s:
        if h == 1.0: h = 0.0
        i = int(h*6.0); f = h*6.0 - i
        
        w = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        if i==0: return (v, t, w)
        if i==1: return (q, v, w)
        if i==2: return (w, v, t)
        if i==3: return (w, q, v)
        if i==4: return (t, w, v)
        if i==5: return (v, w, q)
    else: return (v, v, v)