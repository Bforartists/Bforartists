# $Id$
# Documentation for KX_CameraActuator
from SCA_IActuator import *

class KX_CameraActuator(SCA_IActuator):
	"""
	Applies changes to a camera.
	
	@author: snail
	"""
	def getObject():
		"""
		Returns the name of the object this actuator tracks.
		
		rtype: string
		"""
	
	def setObject(target):
		"""
		Sets the object this actuator tracks.
		
		@param target: the object to track.
		@type target: string or L{KX_GameObject}
		"""
	
	def getMin():
		"""
		Returns the minimum distance to target maintained by the actuator.
		
		@rtype: float
		"""
	
	def setMin(distance):
		"""
		Sets the minimum distance to the target object maintained by the
		actuator.
		
		@param distance: The minimum distance to maintain.
		@type distance: float
		"""
		
	def getMax():
		"""
		Gets the maximum distance to stay from the target object.
		
		@rtype: float
		"""
	
	def setMax(distance):
		"""
		Sets the maximum distance to stay from the target object.
		
		@param distance: The maximum distance to maintain.
		@type distance: float
		"""

	def getHeight():
		"""
		Returns the height to stay above the target object.
		
		@rtype: float
		"""
	
	def setHeight(height):
		"""
		Sets the height to stay above the target object.
		
		@type height: float
		@param height: The height to stay above the target object.
		"""
	
	def setXY(xaxis):
		"""
		Sets the axis to get behind.
		
		@param xaxis: False to track Y axis, True to track X axis.
		@type xaxis: boolean
		"""

	def getXY():
		"""
		Returns the axis this actuator is tracking.
		
		@return: True if tracking X axis, False if tracking Y axis.
		@rtype: boolean
		"""
