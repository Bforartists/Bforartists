# Blender.Constraint module and the Constraint PyType object

"""
The Blender.Constraint submodule

B{New}: 
  -  provides access to Blender's constraint stack

This module provides access to the Constraint Data in Blender.

Examples::
  from Blender import *

  ob = Object.Get('Cube')
  if len(ob.constraints) > 0:
    const = ob.constraints[0]
    if const.type == Constraint.Type.FLOOR:
      offs = const[Constrint.Settings.OFFSET]
  
Or to print all the constraints attached to each bone in a pose::
  from Blender import *
  
  ob = Object.Get('Armature')
  pose = ob.getPose()
  for bonename in pose.bones.keys():
    bone = pose.bones[bonename]
    for const in bone.constraints:
      print bone.name,'=>',const

@type Type: readonly dictionary
@var Type: Constant Constraint dict used by L{ConstraintSeq.append()} and 
  for comparison with L{Constraint.type}.  Values are
  TRACKTO, IKSOLVER, FOLLOWPATH, COPYROT, COPYLOC, COPYSIZE, ACTION,
  LOCKTRACK, STRETCHTO, FLOOR, NULL

@type Settings: readonly dictionary
@var Settings: Constant dict used for changing constraint settings.
  - Used for all constraints
    - TARGET (Object)
    - BONE (string): name of Bone subtarget (for armature targets) (Note: not
      used by Stretch To (STRETCHTO))
  - Used by IK Solver (IKSOLVER) constraint:
    - TOLERANCE (float): clamped to [0.0001:1.0]
    - ITERATIONS (int): clamped to [1,10000]
    - CHAINLEN (int): clamped to [0,255]
    - POSWEIGHT (float): clamped to [0.01,1.0]
    - ROTWEIGHT (float): clamped to [0.01,1.0]
    - ROTATE (bool)
    - USETIP (bool)
  - Used by Action (ACTION) constraint:
    - ACTION (Action Object)
    - LOCAL (bool)
    - START (int): clamped to [1,maxframe]
    - END (int): clamped to [1,maxframe]
    - MIN (float): clamped to [-180.0,180.0]
    - MAX (float): clamped to [-180.0,180.0]
    - KEYON (int): values are XROT, YROT, ZROT
  - Used by Track To (TRACKTO) constraint:
    - TRACK (int): values are TRACKX, TRACKY, TRACKZ, TRACKNEGX,
      TRACKNEGY, TRACKNEGZ
    - UP (int): values are UPX, UPY, UPZ
  - Used by Stretch To (STRETCHTO) constraint:
    - RESTLENGTH (float): clamped to [0.0:100.0]
    - VOLVARIATION (float): clamped to [0.0:100.0]
    - VOLUMEMODE (int): values are VOLUMEXZ, VOLUMEX, VOLUMEZ,
      VOLUMENONE
    - PLANE (int): values are PLANEX, PLANEZ
  - Used by Follow Path (FOLLOWPATH) constraint:
    - FOLLOW (bool)
    - OFFSET (float): clamped to [-maxframe:maxframe]
    - FORWARD (int): values are TRACKX, TRACKY, TRACKZ, TRACKNEGX,
      TRACKNEGY, TRACKNEGZ
    - UP (int): values are UPX, UPY, UPZ
  - Used by Lock Track (FOLLOWPATH) constraint:
    - TRACK (int): values are TRACKX, TRACKY, TRACKZ, TRACKNEGX,
      TRACKNEGY, TRACKNEGZ
    - LOCK (int): values are LOCKX, LOCKY, LOCKZ
  - Used by Floor (FLOOR) constraint:
    - MINMAX (int): values are MINX, MINY, MINZ, MAXX, MAXY, MAXZ
    - OFFSET (float): clamped to [-100.0,100.0]
    - STICKY (bool)
  - Used by Copy Location (COPYLOC) and Copy Rotation (COPYROT)
    - COPY (bitfield): any combination of COPYX, COPYY and COPYZ
    - LOCAL (bool): Only for constraints which Armature targets.
  - Used by Copy Size (COPYSIZE) constraint:
    - COPY (bitfield): any combination of COPYX, COPYY and COPYZ

"""

class ConstraintSeq:
  """
  The ConstraintSeq object
  ========================
  This object provides access to sequence of
  L{constraints<Constraint.Constraint>} for a particular object.
  They can be accessed from L{Object.constraints<Object.Object.constraints>}.
  or L{PoseBone.constraints<Pose.PoseBone.constraints>}.
  """

  def __getitem__(index):
    """
    This operator returns one of the constraints in the stack.
    @type index: int
    @return: an Constraint object
    @rtype: Constraint
    @raise KeyError: index was out of range
    """

  def __len__():
    """
    Returns the number of constraints in the constraint stack.
    @return: number of Constraints
    @rtype: int
    """

  def append(type):
    """
    Appends a new constraint to the end of the constraint stack.
    @type type: a constant specifying the type of constraint to create. as from L{Type}
    @rtype: Constraint
    @return: the new Constraint
    """

  def remove(constraint):
    """
    Remove a constraint from this objects constraint sequence.
    @type constraint: a constraint from this sequence to remove.
    @note: Accessing attributes of the constraint after it is removed will 
    throw an exception.
    """

class Constraint:
  """
  The Constraint object
  =====================
  This object provides access to a constraint for a particular object
  accessed from L{ConstraintSeq}.
  @ivar name: The name of this constraint. 29 chars max.
  @type name: string
  @ivar type: The type of this constraint. Read-only.  The returned value
  matches the types in L{Type}.
  @type type: int
  @ivar influence: The influence value of the constraint.  Valid values
  are in the range [0.0,1.0].
  @type influence: float
  """

  def __getitem__(key):
    """
    This operator returns one of the constraint's data attributes.
    @type key: value from constraint's L{Constraint.Settings} constant
    @return: the requested data
    @rtype: varies
    @raise KeyError: the key does not exist for the constraint
    """

  def __setitem__(key):
    """
    This operator changes one of the constraint's data attributes.
    @type key: value from constraint's L{Constraint.Settings} constant
    @raise KeyError: the key does not exist for the constraint
    """

  def up():
    """
    Moves the constraint up in the object's constraint stack.
    @rtype: PyNone
    """

  def down():
    """
    Moves the constraint down in the object's constraint stack.
    @rtype: PyNone
    """

  def insertKey(frame):
    """
    Adds an influence keyframe for the constraint Ipo.  
    @rtype: PyNone
    @type frame: float
    @param frame: the frame number at which to insert the key.
    """



class ConstraintSeq:
  """
  The ConstraintSeq object
  ========================
  This object provides access to sequence of
  L{constraints<Constraint.Constraint>} for a particular object.
  They can be accessed from L{Object.constraints<Object.Object.constraints>}.
  or L{PoseBone.constraints<Pose.PoseBone.constraints>}.
  """

  def __getitem__(index):
    """
    This operator returns one of the constraints in the stack.
    @type index: int
    @return: an Constraint object
    @rtype: Constraint
    @raise KeyError: index was out of range
    """

  def __len__():
    """
    Returns the number of constraints in the constraint stack.
    @return: number of Constraints
    @rtype: int
    """

  def append(type):
    """
    Appends a new constraint to the end of the constraint stack.
    @type type: a constant specifying the type of constraint to create. as from L{Type}
    @rtype: Constraint
    @return: the new Constraint
    """

  def remove(constraint):
    """
    Remove a constraint from this objects constraint sequence.
    @type constraint: a constraint from this sequence to remove.
    @note: Accessing attributes of the constraint after removing will 
    throw an exception.
    """

