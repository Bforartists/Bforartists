# Blender.NMesh module and the NMesh PyType object

"""
The Blender.NMesh submodule.

Mesh Data
=========

This module provides access to B{Mesh Data} objects in Blender.

Example::

  import Blender
  from Blender import NMesh, Material
  #
  me = NMesh.GetRaw("Plane")       # get the mesh data called "Plane"

  if not me.materials:             # if there are no materials ...
    newmat = Material.New()        # create one ...
    me.materials.append(newmat)    # and append it to the mesh's list of mats

  print me.materials               # print the list of materials
  mat = me.materials[0]            # grab the first material in the list
  mat.R = 1.0                      # redefine its red component
  for v in me.verts:               # loop the list of vertices
    v.co[0] *= 2.5                 # multiply the coordinates
    v.co[1] *= 5.0
    v.co[2] *= 2.5
  me.update()                      # update the real mesh in Blender

@type FaceFlags: readonly dictionary
@type FaceModes: readonly dictionary
@type FaceTranspModes: readonly dictionary
@var FaceFlags: The available face selection flags.
    - SELECT - selected.
    - HIDE - hidden.
    - ACTIVE - the active face.
@var FaceModes: The available face modes.
    - ALL - set all modes at once.
    - BILLBOARD - always orient after camera.
    - HALO - halo face, always point to camera.
    - DINAMYC - respond to collisions.
    - INVISIBLE - invisible face.
    - LIGHT - dinamyc lighting.
    - OBCOL - use object colour instead of vertex colours.
    - SHADOW - shadow type.
    - SHAREDVERT - apparently unused in Blender.
    - SHAREDCOL - shared vertex colours (per vertex).
    - TEX - has texture image.
    - TILES - uses tiled image.
    - TWOSIDE - two-sided face.
@var FaceTranspModes: The available face transparency modes. Note: these are
  ENUMS, they can't be combined (and'ed, or'ed, etc) like a bit vector.
    - SOLID - draw solid.
    - ADD - add to background (halo).
    - ALPHA - draw with transparency.
    - SUB - subtract from background.
"""

def Col(col = [255, 255, 255, 255]):
  """
  Get a new mesh rgba color.
  @type col: list
  @param col: A list [red, green, blue, alpha] of int values in [0, 255].
  @rtype: NMCol
  @return:  A new NMCol (mesh rgba color) object.
  """

def Vert(x = 0, y = 0, z = 0):
  """
  Get a new vertex object.
  @type x: float
  @type y: float
  @type z: float
  @param x: The x coordinate of the vertex.
  @param y: The y coordinate of the vertex.
  @param z: The z coordinate of the vertex.
  @rtype: NMVert
  @return: A new NMVert object.
  """

def Face(vertexList = None):
  """
  Get a new face object.
  @type vertexList: list
  @param vertexList: A list of B{up to 4} NMVerts (mesh vertex
      objects).
  @rtype: NMFace
  @return: A new NMFace object.
  """

def New():
  """
  Create a new mesh object.
  rtype: NMesh
  @return: A new (B{empty}) NMesh object.
  """

def GetRaw(name = None):
  """
  Get the mesh data object called I{name} from Blender.
  @type name: string
  @param name: The name of the mesh data object.
  @rtype: NMesh
  @return: It depends on the 'name' parameter:
      - (name) - The NMesh wrapper of the mesh called I{name},
        None if not found.
      - () - A new (empty) NMesh object.
  """

def GetRawFromObject(name):
  """
  Get the raw mesh data object from the Object in Blender called I{name}.
  @type name: string
  @param name: The name of an Object of type "Mesh".
  @rtype: NMesh
  @return: The NMesh wrapper of the mesh data from the Object called I{name}.
  @warn: This function gets I{deformed} mesh data, already modified for
      rendering (think "display list").  It also doesn't let you overwrite the
      original mesh in Blender, so if you try to update it, a new mesh will
      be created.
  """

def PutRaw(nmesh, name = None, recalculate_normals = 1):
  """
  Put an NMesh object back in Blender.
  @type nmesh: NMesh
  @type name: string
  @type recalculate_normals: int
  @param name: The name of the mesh data object in Blender which will receive
     this nmesh data.  It can be an existing mesh data object or a new one.
  @param recalculate_normals: If non-zero, the vertex normals for the mesh will
     be recalculated.
  @rtype: None or Object
  @return: It depends on the 'name' parameter:
      - I{name} refers to an existing mesh data obj already linked to an
           object: return None.
      - I{name} refers to a new mesh data obj or an unlinked (no users) one:
           return the created Blender Object wrapper.
  """

class NMCol:
  """
  The NMCol object
  ================
    This object is a list of ints: [r, g, b, a] representing an
    rgba colour.
  @cvar r: The Red component in [0, 255].
  @cvar g: The Green component in [0, 255].
  @cvar b: The Blue component in [0, 255].
  @cvar a: The Alpha (transparency) component in [0, 255].
  """

class NMVert:
  """
  The NMVert object
  =================
    This object holds mesh vertex data.
  @type co: list of three floats
  @cvar co: The vertex coordinates (x, y, z).
  @type no: list of three floats
  @cvar no: The vertex normal vector (x, y, z).
  @type uvco: list of two floats
  @cvar uvco: The vertex texture "sticky" coordinates.
  @type index: int
  @cvar index: The vertex index, if owned by a mesh.
  @warn:  There are two kinds of uv texture coordinates in Blender: per vertex
     ("sticky") and per face vertex (uv in L{NMFace}).  In the first, there's
     only one uv pair of coordinates for each vertex in the mesh.  In the
     second, for each face it belongs to, a vertex can have different uv
     coordinates.  This makes the per face option more flexible, since two
     adjacent faces won't have to be mapped to a continuous region in an image:
     each face can be independently mapped to any part of its texture.
  """

class NMFace:
  """
  The NMFace object
  =================
    This object holds mesh face data.
  @type v: list
  @cvar v: The list of face vertices (B{up to 4}).
  @cvar col: The list of vertex colours.
  @cvar mat: Same as I{materialIndex} below.
  @cvar materialIndex: The index of this face's material in its NMesh materials
      list.
  @cvar smooth: If non-zero, the vertex normals are averaged to make this
     face look smooth.
  @cvar image: The Image used as a texture for this face.
  @cvar mode: The display mode (see L{Mesh.FaceModes<FaceModes>})
  @cvar flag: Bit vector specifying selection flags
     (see L{NMesh.FaceFlags<FaceFlags>}).
  @cvar transp: Transparency mode bit vector
     (see L{NMesh.FaceTranspModes<FaceTranspModes>}).
  @cvar uv: List of per-face UV coordinates: [(u0, v0), (u1, v1), ...].
  @warn: Assigning uv textures to mesh faces in Blender works like this:
    1. Select your mesh.
    2. Enter face select mode (press f) and select at least some face(s).
    3. In the UV/Image Editor window, load / select an image.
    4. Play in both windows (better split the screen to see both at the same
       time) until the uv coordinates are where you want them.  Hint: in the
       3d window, the 'u' key opens a menu of default uv choices and the 'r'
       key lets you rotate the uv coords.
    5. Leave face select mode (press f).
  """

  def append(vertex):
    """
    Append a vertex to this face's vertex list.
    @type vertex: NMVert
    @param vertex: An NMVert object.
    """

class NMesh:
  """
  The NMesh Data object
  =====================
    This object gives access to mesh data in Blender.  We refer to mesh as the
    object in Blender and NMesh as its Python counterpart.
  @cvar name: The NMesh name.  It's common to use this field to store extra
     data about the mesh (to be exported to another program, for example).
  @cvar materials: The list of materials used by this NMesh.
  @cvar verts: The list of NMesh vertices (NMVerts).
  @cvar users: The number of Objects using (linked to) this mesh.
  @cvar faces: The list of NMesh faces (NMFaces).
  """

  def addMaterial(material):
    """
    Add a new material to this NMesh's list of materials.  This method is the
    slower but safer way to add materials, since it checks if the argument
    given is really a material, imposes a limit of 16 materials and only adds
    the material if it wasn't already in the list.
    @type material: Blender Material
    @param material: A Blender Material.
    """

  def hasVertexColours(flag = None):
    """
    Get (and optionally set) if this NMesh has vertex colours.
    @type flag: int
    @param flag: If given and non-zero, the "vertex colour" flag for this NMesh
        is turned I{on}.
    @rtype: bool
    @return: The current value of the "vertex colour" flag.
    @warn: If a mesh has both vertex colours and textured faces, this function
       will return False.  This is due to the way Blender deals internally with
       the vertex colours array (if there are textured faces, it is copied to
       the textured face structure and the original array is freed/deleted).
       If you want to know if a mesh has both textured faces and vertex
       colours, set *in Blender* the "VCol Paint" flag for each material that
       covers an area that was also vertex painted and then check in your
       Python script if that material flag is set.  Of course also tell others
       who use your script to do the same.  The "VCol Paint" material mode flag
       is the way to tell Blender itself to render with vertex colours, too, so
       it's a natural solution.
    """

  def hasFaceUV(flag = None):
    """
    Get (and optionally set) if this NMesh has UV-mapped textured faces.
    @type flag: int
    @param flag: If given and non-zero, the "textured faces" flag for this
        NMesh is turned I{on}.
    @rtype: bool
    @return: The current value of the "textured faces" flag.
    """

  def hasVertexUV(flag = None):
    """
    Get (and optionally set) the "sticky" flag that controls if a mesh has
    per vertex UV coordinates.
    @type flag: int
    @param flag: If given and non-zero, the "sticky" flag for this NMesh is
        turned I{on}.
    @rtype: bool
    @return: The current value of the "sticky" flag.
    """

  def getActiveFace():
    """
    Get the index of the active face.
    @rtype: int
    @return: The index of the active face.
    """

  def getSelectedFaces(flag = None):
    """
    Get list of selected faces.
    @type flag: int
    @param flag: If given and non-zero, the list will have indices instead of
        the NMFace objects themselves.
    @rtype: list
    @return:  It depends on the I{flag} parameter:
        - if None or zero: List of NMFace objects.
        - if non-zero: List of indices to NMFace objects.
    """

  def getVertexInfluences(index):
    """
    Get influences of bones in a specific vertex.
    @type index: int
    @param index: The index of a vertex.
    @rtype: list
    @return: List of pairs (name, weight), where name is the bone name (string)
        and its weight is a float value.
    """

  def insertKey(frame = None, type = 'relative'):
    """
    Insert a mesh key at the given frame.  Remember to L{update} the nmesh
    before doing this, or changes in the vertices won't be updated in the
    Blender mesh.
    @type frame: int
    @type type: string
    @param frame: The Scene frame where the mesh key should be inserted.  If
        None, the current frame is used.
    @param type: The mesh key type: 'relative' or 'absolute'.  This is only
        relevant on the first call to insertKey for each nmesh (and after all
        keys were removed with L{removeAllKeys}, of course).
    @warn: This and L{removeAllKeys} were included in this release only to
        make accessing vertex keys possible, but may not be a proper solution
        and may be substituted by something better later.  For example, it
        seems that 'frame' should be kept in the range [1, 100]
        (the curves can be manually tweaked in the Ipo Curve Editor window in
        Blender itself later).
    """

  def removeAllKeys():
    """
    Remove all mesh keys stored in this mesh.
    @rtype: bool
    @return: True if succesful or False if this NMesh wasn't linked to a real
       Blender Mesh yet (or was, but the Mesh had no keys).
    @warn: Currently the mesh keys from meshs that are grabbed with
       NMesh.GetRaw() or .GetRawFromObject() are preserved, so if you want to
       clear them or don't want them at all, remember to call this method.  Of
       course NMeshes created with NMesh.New() don't have mesh keys until you
       add them.
    """

  def update(recalc_normals = 0):
    """
    Update the mesh in Blender.  The changes made are put back to the mesh in
    Blender, if available, or put in a newly created mesh object if this NMesh
    wasn't linked to one, yet.
    @type recalc_normals: int
    @param recalc_normals: If given and equal to 1, the vertex normals are
        recalculated.
    """
