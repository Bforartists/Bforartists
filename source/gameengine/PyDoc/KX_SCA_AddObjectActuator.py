# $Id$
# Documentation for KX_SCA_AddObjectActuator
from SCA_IActuator import *

class KX_SCA_AddObjectActuator(SCA_IActuator):
	"""
	Edit Object Actuator (in Add Object Mode)
	@ivar object: the object this actuator adds.
	@type object: KX_GameObject or None
	@ivar objectLastCreated: the last added object from this actuator (read only).
	@type objectLastCreated: KX_GameObject or None
	@ivar time: the lifetime of added objects, in frames.
	@type time: integer
	@ivar linearVelocity: the initial linear velocity of added objects.
	@type linearVelocity: list [vx, vy, vz]
	@ivar angularVelocity: the initial angular velocity of added objects.
	@type angularVelocity: list [vx, vy, vz]
	
	@warning: An Add Object actuator will be ignored if at game start, the linked object doesn't exist
		  (or is empty) or the linked object is in an active layer.
		  
		  This will genereate a warning in the console:
		  
		  C{ERROR: GameObject I{OBName} has a AddObjectActuator I{ActuatorName} without object (in 'nonactive' layer)}
	"""
	def setObject(object):
		"""
		DEPRECATED: use the object property
		Sets the game object to add.
		
		A copy of the object will be added to the scene when the actuator is activated.
		
		If the object does not exist, this function is ignored.
		
		object can either be a L{KX_GameObject} or the name of an object or None.
		
		@type object: L{KX_GameObject}, string or None
		"""
	def getObject(name_only = 0):
		"""
		DEPRECATED: use the object property
		Returns the name of the game object to be added.
		
		Returns None if no game object has been assigned to be added.
		@type name_only: bool
		@param name_only: optional argument, when 0 return a KX_GameObject
		@rtype: string, KX_GameObject or None if no object is set
		"""
	def setTime(time):
		"""
		DEPRECATED: use the time property
		Sets the lifetime of added objects, in frames.
		
		If time == 0, the object will last forever.
		
		@type time: integer
		@param time: The minimum value for time is 0.
		"""
	def getTime():
		"""
		DEPRECATED: use the time property
		Returns the lifetime of the added object, in frames.
		
		@rtype: integer
		"""
	def setLinearVelocity(vx, vy, vz):
		"""
		DEPRECATED: use the linearVelocity property
		Sets the initial linear velocity of added objects.
		
		@type vx: float
		@param vx: the x component of the initial linear velocity.
		@type vy: float
		@param vy: the y component of the initial linear velocity.
		@type vz: float
		@param vz: the z component of the initial linear velocity.
		"""
	def getLinearVelocity():
		"""
		DEPRECATED: use the linearVelocity property
		Returns the initial linear velocity of added objects.
		
		@rtype: list [vx, vy, vz]
		"""
	def setAngularVelocity(vx, vy, vz):
		"""
		DEPRECATED: use the angularVelocity property
		Sets the initial angular velocity of added objects.
		
		@type vx: float
		@param vx: the x component of the initial angular velocity.
		@type vy: float
		@param vy: the y component of the initial angular velocity.
		@type vz: float
		@param vz: the z component of the initial angular velocity.
		"""
	def getAngularVelocity():
		"""
		DEPRECATED: use the angularVelocity property
		Returns the initial angular velocity of added objects.
		
		@rtype: list [vx, vy, vz]
		"""
	def getLastCreatedObject():
		"""
		DEPRECATED: use the objectLastCreated property
		Returns the last object created by this actuator.
		
		@rtype: L{KX_GameObject}
		@return: A L{KX_GameObject} or None if no object has been created.
		"""
