# $Id$
# Documentation for BL_ActionActuator
from SCA_IActuator import *

class BL_ActionActuator(SCA_IActuator):
	"""
	Action Actuators apply an action to an actor.
	"""
	def setAction(action, reset = True):
		"""
		Sets the current action.
		
		@param action: The name of the action to set as the current action.
		@type action: string
		@param reset: Optional parameter indicating whether to reset the
		              blend timer or not.  A value of 1 indicates that the
		              timer should be reset.  A value of 0 will leave it
		              unchanged.  If reset is not specified, the timer will
		              be reset.
		"""

	def setStart(start):
		"""
		Specifies the starting frame of the animation.
		
		@param start: the starting frame of the animation
		@type start: float
		"""

	def setEnd(end):
		"""
		Specifies the ending frame of the animation.
		
		@param end: the ending frame of the animation
		@type end: float
		"""
	def setBlendin(blendin):
		"""
		Specifies the number of frames of animation to generate
		when making transitions between actions.
		
		@param blendin: the number of frames in transition.
		@type blendin: float
		"""

	def setPriority(priority):
		"""
		Sets the priority of this actuator.
		
		@param priority: Specifies the new priority.  Actuators will lower
		                 priority numbers will override actuators with higher
		                 numbers.
		@type priority: integer
		"""
	def setFrame(frame):
		"""
		Sets the current frame for the animation.
		
		@param frame: Specifies the new current frame for the animation
		@type frame: float
		"""

	def setProperty(prop):
		"""
		Sets the property to be used in FromProp playback mode.
		
		@param prop: the name of the property to use.
		@type prop: string.
		"""

	def setBlendtime(blendtime):
		"""
		Sets the internal frame timer.
		 
		Allows the script to directly modify the internal timer
		used when generating transitions between actions.  
		
		@param blendtime: The new time. This parameter must be in the range from 0.0 to 1.0.
		@type blendtime: float
		"""

	def getAction():
		"""
		getAction() returns the name of the action associated with this actuator.
		
		@rtype: string
		"""
	
	def getStart():
		"""
		Returns the starting frame of the action.
		
		@rtype: float
		"""
	def getEnd():
		"""
		Returns the last frame of the action.
		
		@rtype: float
		"""
	def getBlendin():
		"""
		Returns the number of interpolation animation frames to be generated when this actuator is triggered.
		
		@rtype: float
		"""
	def getPriority():
		"""
		Returns the priority for this actuator.  Actuators with lower Priority numbers will
		override actuators with higher numbers.
		
		@rtype: integer
		"""
	def getFrame():
		"""
		Returns the current frame number.
		
		@rtype: float
		"""
	def getProperty():
		"""
		Returns the name of the property to be used in FromProp mode.
		
		@rtype: string
		"""
	def setChannel(channel, matrix, mode = False):
		"""
		@param channel: A string specifying the name of the bone channel.
		@type channel: string
		@param matrix: A 4x4 matrix specifying the overriding transformation
		               as an offset from the bone's rest position.
		@type matrix: list [[float]]
		@param mode: True for armature/world space, False for bone space
		@type mode: boolean
		"""


