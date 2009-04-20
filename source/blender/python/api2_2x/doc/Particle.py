# Blender.Object module and the Object PyType object

"""
The Blender.Particle submodule


Particle
========

This module provides access to the B{Particle} in Blender.

@type TYPE: readonly dictionary
@var TYPE: Constant dict used for with L{Particle.TYPE}
		- HAIR: set particle system to hair mode.
		- REACTOR: set particle system to reactor mode.
		- EMITTER: set particle system to emitter mode.
@type DISTRIBUTION: readonly dictionary
@var DISTRIBUTION: Constant dict used for with L{Particle.DISTRIBUTION}
		- GRID: set grid distribution.
		- RANDOM: set random distribution.
		- JITTERED: set jittered distribution.
@type EMITFROM: readonly dictionary
@var EMITFROM: Constant dict used for with L{Particle.EMITFROM}
		- VERTS: set particles emit from vertices
		- FACES: set particles emit from faces
		- VOLUME: set particles emit from volume
		- PARTICLE: set particles emit from particles
@type REACTON: readonly dictionary
@var REACTON: Constant dict used for with L{Particle.REACTON}
		- NEAR: react on near
		- COLLISION: react on collision
		- DEATH: react on death
@type DRAWAS: readonly dictionary
@var DRAWAS: Constant dict used for with L{Particle.DRAWAS}
		- NONE: Don't draw
		- POINT: Draw as point
		- CIRCLE: Draw as circles
		- CROSS: Draw as crosses
		- AXIS: Draw as axis
		- LINE: Draw as lines
		- PATH: Draw pathes
		- OBJECT: Draw object
		- GROUP: Draw group
		- BILLBOARD: Draw as billboard 
@type CHILDTYPE: readonly dictionary
@var CHILDTYPE: Constant dict used for whith L{Particle.CHILDTYPE}
		- NONE: set no children
		- PARTICLES: set children born from particles
		- FACES: set children born from faces
@type CHILDKINK: readonly dictionary
@var CHILDKINK: Type of periodic offset on the path
		- NOTHING: set no offset on the path 
		- CURL: set curl offset on the path
		- RADIAL: set radial offset on the path
		- WAVE: set wave offset on the path
		- BRAID: set braid offset on the path
@type CHILDKINKAXIS: readonly dictionary
@var CHILDKINKAXIS: Which axis to use for offset
		- X: set X axis for offset
		- Y: set Y axis for offset
		- Z: set Z axis for offset
"""

class Particle:
	"""
	The Particle object
	===================
		This object gives access to paticles data.
		
	@ivar seed: Set an offset in the random table.
	@type seed: int
	@ivar type: Type of particle system ( Particle.TYPE[ 'HAIR' | 'REACTOR' | 'EMITTER' ] ).
	@type type: int
	@ivar resolutionGrid: The resolution of the particle grid.
	@type resolutionGrid: int
	@ivar startFrame: Frame number to start emitting particles.
	@type startFrame: float
	@ivar endFrame: Frame number to stop emitting particles.
	@type endFrame: float
	@ivar editable: Finalize hair to enable editing in particle mode.
	@type editable: int
	@ivar amount: The total number of particles.
	@type amount: int
	@ivar multireact: React multiple times ( Particle.REACTON[ 'NEAR' | 'COLLISION' | 'DEATH' ] ).
	@type multireact: int
	@ivar reactshape: Power of reaction strength, dependent on distance to target.
	@type reactshape: float
	@ivar hairSegments: Amount of hair segments.
	@type hairSegments: int
	@ivar lifetime: Specify the life span of the particles.
	@type lifetime: float
	@ivar randlife: Give the particle life a random variation.
	@type randlife: float
	@ivar randemission: Emit particles in random order.
	@type randemission: int
	@ivar particleDistribution: Where to emit particles from  ( Particle.EMITFROM[ 'PARTICLE' | 'VOLUME' | 'FACES' | 'VERTS' ] )
	@type particleDistribution: int
	@ivar evenDistribution: Use even distribution from faces based on face areas or edge lengths.
	@type evenDistribution: int
	@ivar distribution: How to distribute particles on selected element ( Particle.DISTRIBUTION[ 'GRID' | 'RANDOM' | 'JITTERED' ] ).
	@type distribution: int
	@ivar jitterAmount: Amount of jitter applied to the sampling.
	@type jitterAmount: float
	@ivar pf: Emission locations / face (0 = automatic).
	@type pf:int
	@ivar invert: Invert what is considered object and what is not.
	@type invert: int
	@ivar targetObject: The object that has the target particle system (empty if same object).
	@type targetObject: Blender object
	@ivar targetpsys: The target particle system number in the object.
	@type targetpsys: int
	@ivar 2d: Constrain boids to a surface.
	@type 2d: float
	@ivar maxvel: Maximum velocity.
	@type maxvel: float
	@ivar avvel: The usual speed % of max velocity.
	@type avvel: float
	@ivar latacc: Lateral acceleration % of max velocity
	@type latacc: float
	@ivar tanacc: Tangential acceleration % of max velocity
	@type tanacc: float
	@ivar groundz: Default Z value.
	@type groundz: float
	@ivar object: Constrain boids to object's surface.
	@type object: Blender Object
	@ivar renderEmitter: Render emitter object.
	@type renderEmitter: int
	@ivar displayPercentage: Particle display percentage.
	@type displayPercentage: int
	@ivar hairDisplayStep: How many steps paths are drawn with (power of 2) in visu mode.
	@type hairDisplayStep: int
	@ivar hairRenderStep: How many steps paths are rendered with (power of 2) in render mode."
	@type hairRenderStep: int
	@ivar duplicateObject: Get the duplicate object.
	@type duplicateObject: Blender Object
	@ivar drawAs: Get draw type Particle.DRAWAS([ 'NONE' | 'OBJECT' | 'POINT' | ... ]).
	@type drawAs: int
	@ivar childAmount: The total number of children
	@type childAmount: int
	@ivar childType: Type of childrens ( Particle.CHILDTYPE[ 'FACES' | 'PARTICLES' | 'NONE' ] )
	@type childType: int
	@ivar childRenderAmount: Amount of children/parent for rendering
	@type childRenderAmount: int
	@ivar childRadius: Radius of children around parent
	@type childRadius: float
	@ivar childRound: Roundness of children around parent
	@type childRound: float
	@ivar childClump: Amount of clumpimg
	@type childClump: float
	@ivar childShape: Shape of clumpimg
	@type childShape: float
	@ivar childSize: A multiplier for the child particle size
	@type childSize: float
	@ivar childRand: Random variation to the size of the child particles
	@type childRand: float
	@ivar childRough1: Amount of location dependant rough
	@type childRough1: float
	@ivar childRough1Size: Size of location dependant rough
	@type childRough1Size: float
	@ivar childRough2: Amount of random rough
	@type childRough2: float
	@ivar childRough2Size: Size of random rough
	@type childRough2Size: float
	@ivar childRough2Thresh: Amount of particles left untouched by random rough
	@type childRough2Thresh: float
	@ivar childRoughE: Amount of end point rough
	@type childRoughE: float
	@ivar childRoughEShape: Shape of end point rough
	@type childRoughEShape: float
	@ivar childKink: Type of periodic offset on the path (Particle.CHILDKINK[ 'BRAID' | 'WAVE' | 'RADIAL' | 'CURL' | 'NOTHING' ])
	@type childKink: int
	@ivar childKinkAxis: Which axis to use for offset (Particle.CHILDKINKAXIS[ 'Z' | 'Y' | 'X' ])
	@type childKinkAxis: int
	@ivar childKinkFreq: The frequency of the offset (1/total length)
	@type childKinkFreq: float
	@ivar childKinkShape: Adjust the offset to the beginning/end
	@type childKinkShape: float
	@ivar childKinkAmp: The amplitude of the offset
	@type childKinkAmp: float
	@ivar childBranch: Branch child paths from eachother
	@type childBranch: int
	@ivar childBranch: Animate branching
	@type childBranch: int
	@ivar childBranch: Start and end points are the same
	@type childBranch: int
	@ivar childBranch: Threshold of branching
	@type childBranch: float
	"""
	
	def freeEdit():
		"""
		Free edit mode.
		@return: None
		"""

	def getLoc(all=0,id=0):
		"""
		Get the particles locations.
		A list of tuple is returned in particle mode.
		A list of list of tuple is returned in hair mode.
		The tuple is a vector of 3 or 4 floats in world space (x,y,z, optionally the particle's id).
		@type all: int
		@param all: if not 0 export all particles (uninitialized (unborn or died)particles exported as None).
		@type id: int
		@param id: add the particle id in the end of the vector tuple
		@rtype: list of vectors (tuple of 3 floats and optionally the id) or list of list of vectors
		@return: list of vectors or list of list of vectors (hair mode) or None if system is disabled
		"""
	def getRot(all=0,id=0):
		"""
		Get the particles' rotations as quaternion.
		A list of tuple is returned in particle mode.
		The tuple is vector of 4 or 5 floats (x,y,z,w, optionally the id of the particle).
		
		@type all: int
		@param all: if not 0, export all particles (uninitialized (unborn or died) particles exported as None).
		@type id: int
		@param id: add the particle id in the return tuple
		@rtype: list of tuple of 4 or 5 elements (if id is not zero)
		@return: list of 4-tuples or None if system is disabled
		"""
		
	def getMat():
		"""
		Get the particles' material.
		@rtype: Blender Material
		@return: The material assigned to particles
		"""
		
	def getSize(all=0,id=0):
		"""
		Get the particles' size.
		A list of float or list of tuple (particle's size,particle's id).
		@type all: int
		@param all: if not 0, export all particles (uninitialized (unborn or died) particles exported as None).
		@type id: int
		@param id: add the particle id in the return tuple
		@rtype: list of floats
		@return: list of floats or list of tuples if id is not zero (size,id) or None if system is disabled.
		"""
		
	def getAge(all=0,id=0):
		"""
		Get the particles' age.
		A list of float or list of tuple (particle's age, particle's id).
		@type all: int
		@param all: if not 0, export all particles (uninitialized (unborn or died) particles exported as None).
		@type id: int
		@param id: add the particle id in the return tuple
		@rtype: list of floats
		@return: list of floats or list of tuples if id is not zero (size,id) or None if system is disabled.
		"""
