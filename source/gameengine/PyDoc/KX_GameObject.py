# $Id$
# Documentation for game objects

class KX_GameObject:
	"""
	All game objects are derived from this class.
	
	Properties assigned to game objects are accessible as attributes
	in objects of this class.
	
	Attributes:
	mass: The object's mass (provided the object has a physics controller). float. read only
	parent: The object's parent object. KX_GameObject. read only
	visible: visibility flag. boolean.
	position: The object's position. list [x, y, z]
	orientation: The object's orientation. 3x3 Matrix.  You can also write a Quaternion or Euler vector.
	scaling: The object's scaling factor. list [sx, sy, sz]
	"""
	
	def setVisible(visible):
		"""
		Sets the game object's visible flag.
		
		@type visible: boolean
		"""
	def setPosition(pos):
		"""
		Sets the game object's position.
		
		@type pos: [x, y, z]
		@param pos: the new position, in world coordinates.
		"""
	def getPosition():
		"""
		Gets the game object's position.
		
		@rtype list [x, y, z]
		@return the object's position in world coordinates.
		"""
	def setOrientation(orn):
		"""
		Sets the game object's orientation.
		
		@type orn: 3x3 rotation matrix, or Quaternion.
		@param orn: a rotation matrix specifying the new rotation.
		"""
	def getOrientation():
		"""
		Gets the game object's orientation.
		
		@rtype 3x3 rotation matrix
		@return The game object's rotation matrix
		"""
	def getLinearVelocity():
		"""
		Gets the game object's linear velocity.
		
		This method returns the game object's velocity through it's centre of mass,
		ie no angular velocity component.
		
		cf getVelocity()
		
		@rtype list [vx, vy, vz]
		@return the object's linear velocity.
		"""
	def getVelocity(point):
		"""
		Gets the game object's velocity at the specified point.
		
		Gets the game object's velocity at the specified point, including angular
		components.
		
		@type point: list [x, y, z]
		@param point: the point to return the velocity for, in local coordinates. (optional: default = [0, 0, 0])
		@rtype list [vx, vy, vz]
		@return the velocity at the specified point.
		"""
	def getMass():
		"""
		Gets the game object's mass.
		
		@rtype float
		@return the object's mass.
		"""
	def getReactionForce():
		"""
		Gets the game object's reaction force.
		
		The reaction force is the force applied to this object over the last simulation timestep.
		This also includes impulses, eg from collisions.
		
		@rtype list [fx, fy, fz]
		@return the reaction force of this object.
		"""
	def applyImpulse(point, impulse):
		"""
		Applies an impulse to the game object.
		
		This will apply the specified impulse to the game object at the specified point.
		If point != getPosition(), applyImpulse will also change the object's angular momentum.
		Otherwise, only linear momentum will change.
		
		@type point: list [x, y, z]
		@param point: the point to apply the impulse to (in world coordinates)
		"""
	def suspendDynamics():
		"""
		Suspends physics for this object.
		"""
	def restoreDynamics():
		"""
		Resumes physics for this object.
		"""
	def enableRigidBody():
		"""
		Enables rigid body physics for this object.
		
		Rigid body physics allows the object to roll on collisions.
		"""
	def disableRigidBody():
		"""
		Disables rigid body physics for this object.
		"""
	def getParent():
		"""
		Gets this object's parent.
		
		@rtype: game object
		@return this object's parent object, or None if this object has no parent.
		"""
	def getMesh(mesh):
		"""
		Gets the mesh object for this object.
		
		@type mesh: integer
		@param mesh: the mesh object to return (optional: default mesh = 0)
		@rtype: mesh object
		@returns the first mesh object associated with this game object, or None if this object has no meshs.
		"""
	def getPhysicsId():
		"""
		Returns the user data object associated with this game object's physics controller.
		"""
