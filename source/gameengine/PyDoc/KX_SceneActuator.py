# $Id$
# Documentation for KX_SceneActuator
from SCA_IActuator import *

class KX_SceneActuator(SCA_IActuator):
	"""
	Scene Actuator logic brick.
	
	@warning: Scene actuators that use a scene name will be ignored if at game start, the
	          named scene doesn't exist or is empty
		  
		  This will generate a warning in the console:
		  
		  C{ERROR: GameObject I{OBName} has a SceneActuator I{ActuatorName} (SetScene) without scene}

	Properties:
	
	@ivar scene: the name of the scene to change to/overlay/underlay/remove/suspend/resume
	@type scene: string.
	@ivar camera: the camera to change to.
	              When setting the attribute, you can use either a L{KX_Camera} or the name of the camera.
	@type camera: L{KX_Camera} on read, string or L{KX_Camera} on write
	"""
	def setUseRestart(flag):
		"""
		DEPRECATED
		Set flag to True to restart the scene.
		
		@type flag: boolean
		"""
	def setScene(scene):
		"""
		DEPRECATED: use the scene property instead
		Sets the name of the scene to change to/overlay/underlay/remove/suspend/resume.
		
		@type scene: string
		"""
	def setCamera(camera):
		"""
		DEPRECATED: use the camera property instead
		Sets the camera to change to.
		
		Camera can be either a L{KX_Camera} or the name of the camera.
		
		@type camera: L{KX_Camera} or string
		"""
	def getUseRestart():
		"""
		DEPRECATED
		Returns True if the scene will be restarted.
		
		@rtype: boolean
		"""
	def getScene():
		"""
		DEPRECATED: use the scene property instead
		Returns the name of the scene to change to/overlay/underlay/remove/suspend/resume.
		
		Returns an empty string ("") if no scene has been set.
		
		@rtype: string
		"""
	def getCamera():
		"""
		DEPRECATED: use the camera property instead
		Returns the name of the camera to change to.
		
		@rtype: string
		"""
