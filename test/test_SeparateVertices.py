from triangle_math import SeparateVertices
import pytest
import numpy as np

def test_SeparateVertices_nothingtodo():
	vertices = np.array([(0,1,2),(1,1,1),(1,2,1)])
	triangles = np.array([(0,1,2)])
	new_triangles,new_vertices = SeparateVertices(triangles, vertices)
	assert all(new_vertices==vertices.flatten())

def test_SeparateVertices_separateone():
	vertices = np.array([(0,0,0),(1,1,1),(2,2,2),(3,3,3),(4,4,4)])
	triangles = np.array([(0,1,2),(0,3,4)])
	target = np.array([(0,0,0),(1,1,1),(2,2,2),(0,0,0),(3,3,3),(4,4,4)])
	new_triangles,new_vertices = SeparateVertices(triangles, vertices)
	assert all(new_vertices==target.flatten())
