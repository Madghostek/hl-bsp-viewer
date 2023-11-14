def SeparateVertices(triangles, vertices):
	"""
    Prepares for coloring
    triangles - list of (v1,v2,v3) tuples - indices into vertices
    vertices - actual (x,y,z) points that make up triangles

    output - new list of indices and vertices that dont share vertices
    no need to change anything in colors, it's just the indexes that change.
    """
	return (vx for tri in triangles for v in tri for vx in vertices[v])