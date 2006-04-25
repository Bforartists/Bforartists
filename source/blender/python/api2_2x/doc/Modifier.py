# Blender.Modifier module and the Modifier PyType object

"""
The Blender.Modifier submodule

B{New}: 
  -  provides access to Blender's modifier stack

This module provides access to the Modifier Data in Blender.

Example::
  from Blender import *

  ob = Object.Get('Cube')        # retrieve an object
  mods = ob.modifiers            # get the object's modifiers
  for mod in mods:
    print mod,mod.name           # print each modifier and its name
  mod = mods.append(Modifier.Type.SUBSURF) # add a new subsurf modifier
  mod[Modifier.Settings.LEVELS] = 3     # set subsurf subdivision levels to 3
  
@type Type: readonly dictionary
@var Type: Constant Modifier dict used for  L{ModSeq.append()} to a modifier sequence and comparing with L{Modifier.type}:
    - ARMATURE - type value for Armature modifiers
    - BOOLEAN - type value for Boolean modifiers
    - BUILD - type value for Build modifiers
    - CURVE - type value for Curve modifiers
    - DECIMATE - type value for Decimate modifiers
    - LATTICE - type value for Lattice modifiers
    - SUBSURF - type value for Subsurf modifiers
    - WAVE - type value for Wave modifiers

@type Settings: readonly dictionary
@var Settings: Constant Modifier dict used for changing modifier settings.
	- EXPP_MOD_RENDER - Used for all modifiers
	- EXPP_MOD_REALTIME - Used for all modifiers
	- EXPP_MOD_EDITMODE - Used for all modifiers
	- EXPP_MOD_ONCAGE - Used for all modifiers

	- EXPP_MOD_OBJECT - Used for Armature, Lattice, Curve, Boolean and Array
	- EXPP_MOD_VERTGROUP - Used for Armature, Lattice and Curve
	- EXPP_MOD_LIMIT - Array and Mirror
	- EXPP_MOD_FLAG - Mirror and Wave
	- EXPP_MOD_COUNT - Decimator and Array
	
	- EXPP_MOD_TYPES - Used for Subsurf only
	- EXPP_MOD_LEVELS - Used for Subsurf only 
	- EXPP_MOD_RENDLEVELS - Used for Subsurf only
	- EXPP_MOD_OPTIMAL - Used for Subsurf only
	- EXPP_MOD_UV - Used for Subsurf only


	- EXPP_MOD_ENVELOPES - Used for Armature only
	
	- EXPP_MOD_START - Used for Build only
	- EXPP_MOD_LENGTH - Used for Build only
	- EXPP_MOD_SEED - Used for Build only
	- EXPP_MOD_RANDOMIZE - Used for Build only

	- EXPP_MOD_AXIS - Used for Mirror only

	- EXPP_MOD_RATIO - Used for Decimate only
	
	- EXPP_MOD_STARTX - Used for Wave only
	- EXPP_MOD_STARTY - Used for Wave only
	- EXPP_MOD_HEIGHT - Used for Wave only
	- EXPP_MOD_WIDTH - Used for Wave only
	- EXPP_MOD_NARROW - Used for Wave only
	- EXPP_MOD_SPEED - Used for Wave only
	- EXPP_MOD_DAMP - Used for Wave only
	- EXPP_MOD_LIFETIME - Used for Wave only
	- EXPP_MOD_TIMEOFFS - Used for Wave only
	- EXPP_MOD_OPERATION - Used for Wave only
"""

class ModSeq:
  """
  The ModSeq object
  =================
  This object provides access to list of L{modifiers<Modifier.Modifier>} for a particular object.
  Only accessed from L{Object.Object.modifiers}.
  """

  def __getitem__(index):
    """
    This operator returns one of the object's modifiers.
    @type index: int
    @return: an Modifier object
    @rtype: Modifier
    @raise KeyError: index was out of range
    """

  def __len__():
    """
    Returns the number of modifiers in the object's modifier stack.
    @return: number of Modifiers
    @rtype: int
    """

  def append(type):
    """
    Appends a new modifier to the end of the object's modifier stack.
    @type type: a constant specifying the type of modifier to create. as from L{Type}
    @rtype: Modifier
    @return: the new Modifier
    """

  def remove(modifier):
    """
    Remove a modifier from this objects modifier sequence.
    @type modifier: a modifier from this sequence to remove.
    @note: Accessing attributes of the modifier after removing will raise an error.
    """

class Modifier:
  """
  The Modifier object
  ===================
  This object provides access to a modifier for a particular object accessed from L{ModSeq}.
  @ivar name: The name of this modifier. 31 chars max.
  @type name: string
  @ivar type: The type of this modifier. Read-only.  The returned value
  matches the types in L{Type}.
  @type type: int
  """  

  def __getitem__(key):
    """
    This operator returns one of the modifier's data attributes.
    @type key: value from modifier's L{Modifier.Settings} constant
    @return: the requested data
    @rtype: varies
    @raise KeyError: the key does not exist for the modifier
    """

  def __setitem__(key):
    """
    This operator modifiers one of the modifier's data attributes.
    @type key: value from modifier's L{Modifier.Settings} constant
    @raise KeyError: the key does not exist for the modifier
    """

  def up():
    """
    Moves the modifier up in the object's modifier stack.
    @rtype: PyNone
    @raise RuntimeError: request to move above another modifier requiring
    original data
    """

  def down():
    """
    Moves the modifier down in the object's modifier stack.
    @rtype: PyNone
    @raise RuntimeError: request to move modifier beyond a non-deforming
    modifier
    """


