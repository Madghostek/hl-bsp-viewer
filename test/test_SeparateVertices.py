from triangle_math import SeparateVertices

def test_SeparateVertices():
	vertices = [(0,1,2),(1,1,1),(1,2,1)]
	triangles = [(0,1,2)]
	result = SeparateVertices(vertices,triangles)
	print(result)
