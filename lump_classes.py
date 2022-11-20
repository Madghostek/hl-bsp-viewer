from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import typing

Vec3D = npt.NDArray[np.float32]

@dataclass
class Node:
	iPlane : np.uint32
	iChildren : npt.NDArray[np.int16]
	nMins : npt.NDArray[np.int16]
	nMaxs : npt.NDArray[np.int16]
	iFirstFace : np.int16
	nFaces : np.uint16

@dataclass
class Model:
	nMins : npt.NDArray[np.float32]
	nMaxs : npt.NDArray[np.float32]
	origin : Vec3D
	iHeadNodes : npt.NDArray[np.int32] # 4 hulls
	nVisLeafs : np.int32
	iFirstFace : np.int32
	nFaces : np.int32


LumpCollection = typing.Tuple[Node,Node,Node,Node,Node,Node,Node,Node,Node,Node,Node,Node,Node,Node,Node]