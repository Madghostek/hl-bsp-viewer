import numpy as np

class Camera():

	def __init__(self,x=0.0,y=0.0,z=0.0,pitch=0.0,yaw=0.0,roll=0.0,fov=45.0):
		self.pos = np.array([x,y,z],dtype=np.float32)
		self.angle = np.array([pitch,roll,yaw],dtype=np.float32)
		self.fov = fov

		self.defaultpos = self.pos.copy()
		self.defaultangle = self.angle.copy()
		self.defaultfov = self.fov

	# du - left right, dw - forward, backward
	def moveLocal(self,du,dw):
		self.pos[0]-=dw*np.sin(np.radians(self.angle[2]))+du*np.cos(np.radians(self.angle[2]))
		self.pos[1]+=dw*np.cos(np.radians(self.angle[2]))-du*np.sin(np.radians(self.angle[2]))
		self.pos[2]-=dw*np.cos(np.radians(self.angle[0]))

	def reset(self):
		print("reset")
		self.angle = self.defaultangle.copy()
		self.fov = self.defaultfov
		self.pos = self.defaultpos.copy()