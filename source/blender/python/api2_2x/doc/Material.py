# Blender.Material module and the Material PyObject

"""
The Blender.Material submodule.

B{New}: L{Material.clearScriptLinks} accepts a parameter now.

Material 
========

This module provides access to B{Material} objects in Blender.

Example::
  import Blender
  from Blender import Material
  mat = Material.New('newMat')          # create a new Material called 'newMat'
  print mat.rgbCol                      # print its rgb color triplet sequence
  mat.rgbCol = [0.8, 0.2, 0.2]          # change its color
  mat.setAlpha(0.2)                     # mat.alpha = 0.2 -- almost transparent
  mat.emit = 0.7                        # equivalent to mat.setEmit(0.8)
  mat.mode |= Material.Modes.ZTRANSP    # turn on Z-Buffer transparency
  mat.setName('RedBansheeSkin')         # change its name
  mat.setAdd(0.8)                       # make it glow
  mat.setMode('Halo')                   # turn 'Halo' "on" and all others "off"

@type Modes: readonly dictionary
@var Modes: The available Material Modes.
    - TRACEABLE    - Make Material visible for shadow lamps.
    - SHADOW       - Enable Material for shadows.
    - SHADELESS    - Make Material insensitive to light or shadow.
    - WIRE         - Render only the edges of faces.
    - VCOL_LIGHT   - Add vertex colors as extra light.
    - VCOL_PAINT   - Replace basic colors with vertex colors.
    - HALO         - Render as a halo.
    - ZTRANSP      - Z-buffer transparent faces.
    - ZINVERT      - Render with inverted Z-buffer.
    - - HALORINGS  - Render rings over the basic halo.
    - ENV          - Do not render Material.
    - - HALOLINES  - Render star shaped lines over the basic halo.
    - ONLYSHADOW   - Let alpha be determined on the degree of shadow.
    - - HALOXALPHA - Use extreme alpha.
    - TEXFACE      - UV-Editor assigned texture gives color and texture info
        for faces.
    - - HALOSTAR   - Render halo as a star.
    - NOMIST       - Set the Material insensitive to mist.
    - - HALOSHADED - Let halo receive light.
    - HALOTEX      - Give halo a texture.
    - HALOPUNO     - Use the vertex normal to specify the dimension of the halo.
    - HALOFLARE    - Render halo as a lens flare.
    - RAYMIRROR    - Enables raytracing for mirror reflection rendering.
    - RAYTRANSP    - Enables raytracing for transparency rendering.
@warn: Some Modes are only available when the 'Halo' mode is I{off} and
    others only when it is I{on}.  But these two subsets of modes share the same
    numerical values in their Blender C #defines. So, for example, if 'Halo' is
    on, then 'NoMist' is actually interpreted as 'HaloShaded'.  We marked all
    such possibilities in the Modes dict below: each halo-related mode that
    uses an already taken value is preceded by "-" and appear below the normal
    mode which also uses that value.
"""

def New (name = 'Mat'):
  """
  Create a new Material object.
  @type name: string
  @param name: The Material name.
  @rtype: Blender Material
  @return: The created Material object.
  """

def Get (name = None):
  """
  Get the Material object(s) from Blender.
  @type name: string
  @param name: The name of the Material.
  @rtype: Blender Material or a list of Blender Materials
  @return: It depends on the 'name' parameter:
    - (name): The Material object with the given name;
    - ():   A list with all Material objects in the current scene.
  """

class Material:
  """
  The Material object
  ===================
   This object gives access to Materials in Blender.
  @ivar name: Material's name.
  @type mode: int
  @ivar mode: Mode flags as an or'ed int value.  See the Modes dictionary keys
      and descriptions in L{Modes}.
  @ivar rgbCol: Material's RGB color triplet sequence.
  @ivar specCol: Specular color rgb triplet sequence.
  @ivar mirCol: Mirror color rgb triplet sequence.
  @ivar R: Red component of L{rgbCol} - [0.0, 1.0].
  @ivar G: Green component of L{rgbCol} - [0.0, 1.0].
  @ivar B: Blue component of L{rgbCol} - [0.0, 1.0].
  @ivar alpha: Alpha (translucency) component of the Material - [0.0, 1.0].
  @ivar amb: Ambient factor - [0.0, 1.0].
  @ivar emit: Emitting light intensity - [0.0, 1.0].
  @ivar ref:  Reflectivity - [0.0, 1.0].
  @ivar spec: Specularity - [0.0, 2.0].
  @ivar specTransp: Specular transparency - [0.0, 1.0].
  @ivar add: Glow factor - [0.0, 1.0].
  @ivar zOffset: Artificial Z offset for faces - [0.0, 10.0].
  @ivar haloSize: Dimension of the halo - [0.0, 100.0].
  @ivar flareSize: Factor the flare is larger than the halo - [0.1, 25.0].
  @ivar flareBoost: Flare's extra strength - [0.1, 10.0].
  @ivar haloSeed: To use random values for ring dimension and line location -
     [0, 255].
  @ivar flareSeed: Offset in the seed table - [0, 255].
  @ivar subSize:  Dimension of subflares, dots and circles - [0.1, 25.0].
  @ivar hard: Hardness of the specularity - [1, 255].
  @ivar nFlares: Number of halo subflares - [1, 32].
  @ivar nStars: Number of points on the halo stars - [3, 50].
  @ivar nLines: Number of star shaped lines on each halo - [0, 250].
  @ivar nRings: Number of halo rings - [0, 24].
  @type ipo: Blender Ipo
  @ivar ipo: This Material's ipo.
  @ivar rayMirr: Amount mirror reflection for raytrace.
  @ivar rayMirrDepth: Amount of inter-reflections calculated maximal.
  @ivar fresnelDepth: Power of Fresnel for mirror reflection. 
  @ivar fresnelDepthFac: Blending factor for Fresnel. 
  @ivar IOR: Sets the angular index of refraction for raytrace. 
  @ivar transDepth: Amount of refractions calculated maximal. 
  @ivar fresnelTrans: Power of Fresnel for transparency.
  @ivar fresnelTransFac: Blending factor for Fresnel.
  @ivar specTrans: Makes specular areas opaque on transparent materials.
  @warning: Most member variables assume values in some [Min, Max] interval.
   When trying to set them, the given parameter will be clamped to lie in
   that range: if val < Min, then val = Min, if val > Max, then val = Max.
  """

  def getName():
    """
    Get the name of this Material object.
    @rtype: string
    """

  def setName(name):
    """
    Set the name of this Material object.
    @type name: string
    @param name: The new name.
    """

  def getIpo():
    """
    Get the Ipo associated with this material, if any.
    @rtype: Ipo
    @return: the wrapped ipo or None.
    """

  def setIpo(ipo):
    """
    Link an ipo to this material.
    @type ipo: Blender Ipo
    @param ipo: a material type ipo.
    """

  def clearIpo():
    """
    Unlink the ipo from this material.
    @return: True if there was an ipo linked or False otherwise.
    """

  def insertIpoKey(keytype):
    """
    Inserts keytype values in material ipo at curframe. Uses module constants.
    @type keytype: Integer
    @param keytype:
           -RGB
           -ALPHA
           -HALOSIZE
           -MODE
           -ALLCOLOR
           -ALLMIRROR
           -OFS
           -SIZE
           -ALLMAPPING
    @return: py_none
    """

  def getMode():
    """
    Get this Material's mode flags.
    @rtype: int
    @return: B{OR'ed value}. Use the Modes dictionary to check which flags
        are 'on'.

        Example::
          import Blender
          from Blender import Material
          flags = mymat.getMode()
          if flags & Material.Modes['HALO']:
            print "This material is rendered as a halo"
          else:
            print "Not a halo"
    """

  def setMode(param, stringN=None):
    """
    Set this Material's mode flags. Up to 22 mode strings can be given
    and specify the modes which are turned 'on'.  Those not provided are 
    turned 'off', so mat.setMode() -- without arguments -- turns off all 
    mode flags for Material mat.  Valid mode strings are "Traceable", 
    "Shadow", "Shadeless", "Wire", "VColLight", "VColPaint", "Halo",
    "ZTransp", "ZInvert", "HaloRings", "HaloLines", "OnlyShadow",
    "HaloXAlpha", "HaloStar", "TexFace", "HaloTex", "HaloPuno", "NoMist",
    "HaloShaded", "HaloFlare", "Radio", "RayMirr", "ZTransp", "RayTransp",
    "OnlyShadow", "NoMist", "Env"

    An integer can also be given, which directly sets the mode flag.  The
    Modes dictionary keys can (and should) be added or ORed to specify
    which modes to turn 'on'.  The value returned from getMode() can
    also be modified and input to this method.

    @type param: string, None or int
    @param param: A mode value (int) or flag (string).  Can also be None.
    @type stringN: string
    @param stringN: A mode flag. Up to 22 flags can be set at the same time.
    """

  def getRGBCol():
    """
    Get the rgb color triplet sequence.
    @rtype: list of 3 floats
    @return: [r, g, b]
    """

  def setRGBCol(rgb = None):
    """
    Set the rgb color triplet sequence.  If B{rgb} is None, set the color to black.
    @type rgb: three floats or a list of three floats
    @param rgb: The rgb color values in [0.0, 1.0] as:
        - a list of three floats: setRGBCol ([r, g, b]) B{or}
        - three floats as separate parameters: setRGBCol (r,g,b).
    """
 
  def getSpecCol():
    """
    Get the specular color triplet sequence.
    @rtype: list of 3 floats
    @return: [specR, specG, specB]
    """

  def setSpecCol(rgb = None):
    """
    Set the specular color triplet sequence.  If B{rgb} is None, set the color to black.
    @type rgb: three floats or a list of three floats
    @param rgb: The rgb color values in [0.0, 1.0] as:
        - a list of three floats: setSpecCol ([r, g, b]) B{or}
        - three floats as separate parameters: setSpecCol (r,g,b).
    """

  def getMirCol():
    """
    Get the mirror color triplet sequence.
    @rtype: list of 3 floats
    @return: [mirR, mirG, mirb]
    """

  def setMirCol(rgb = None):
    """
    Set the mirror color triplet sequence.  If B{rgb} is None, set the color to black.
    @type rgb: three floats or a list of three floats
    @param rgb: The rgb color values in [0.0, 1.0] as:
        - a list of three floats: setMirCol ([r, g, b]) B{or}
        - three floats as separate parameters: setMirCol (r,g,b).
    """

  def getAlpha():
    """
    Get the alpha (transparency) value.
    @rtype: float
    """

  def setAlpha(alpha):
    """
    Set the alpha (transparency) value.
    @type alpha: float
    @param alpha: The new value in [0.0, 1.0].
    """

  def getAmb():
    """
    Get the ambient color blend factor.
    @rtype: float
    """

  def setAmb(amb):
    """
    Set the ambient color blend factor.
    @type amb: float
    @param amb:  The new value in [0.0, 1.0].
    """

  def getEmit():
    """
    Get the emitting light intensity.
    @rtype: float
    """

  def setEmit(emit):
    """
    Set the emitting light intensity.
    @type emit: float
    @param emit: The new value in [0.0, 1.0].
    """

  def getRef():
    """
    Get the reflectivity value.
    @rtype: float
    """

  def setRef(ref):
    """
    Set the reflectivity value.
    @type ref: float
    @param ref: The new value in [0.0, 1.0].
    """

  def getSpec():
    """
    Get the specularity value.
    @rtype: float
    """

  def setSpec(spec):
    """
    Set the specularity value.
    @type spec: float
    @param spec: The new value in [0.0, 2.0].
    """

  def getSpecTransp():
    """
    Get the specular transparency.
    @rtype: float
    """

  def setSpecTransp(spectransp):
    """
    Set the specular transparency.
    @type spectransp: float
    @param spectransp: The new value in [0.0, 1.0].
    """

  def getAdd():
    """
    Get the glow factor.
    @rtype: float
    """

  def setAdd(add):
    """
    Set the glow factor.
    @type add: float
    @param add: The new value in [0.0, 1.0].
    """

  def getZOffset():
    """
    Get the artificial offset for faces with this Material.
    @rtype: float
    """

  def setZOffset(zoffset):
    """
    Set the artificial offset for faces with this Material.
    @type zoffset: float
    @param zoffset: The new value in [0.0, 10.0].
    """

  def getHaloSize():
    """
    Get the halo size.
    @rtype: float
    """

  def setHaloSize(halosize):
    """
    Set the halo size.
    @type halosize: float
    @param halosize: The new value in [0.0, 100.0].
    """

  def getHaloSeed():
    """
    Get the seed for random ring dimension and line location in halos.
    @rtype: int
    """

  def setHaloSeed(haloseed):
    """
    Set the seed for random ring dimension and line location in halos.
    @type haloseed: int
    @param haloseed: The new value in [0, 255].
    """

  def getFlareSize():
    """
    Get the ratio: flareSize / haloSize.
    @rtype: float
    """

  def setFlareSize(flaresize):
    """
    Set the ratio: flareSize / haloSize.
    @type flaresize: float
    @param flaresize: The new value in [0.1, 25.0].
    """

  def getFlareSeed():
    """
    Get flare's offset in the seed table.
    @rtype: int
    """

  def setFlareSeed(flareseed):
    """
    Set flare's offset in the seed table.
    @type flareseed: int
    @param flareseed: The new value in [0, 255].
    """

  def getFlareBoost():
    """
    Get the flare's extra strength.
    @rtype: float
    """

  def setFlareBoost(flareboost):
    """
    Set the flare's extra strength.
    @type flareboost: float
    @param flareboost: The new value in [0.1, 10.0].
    """

  def getSubSize():
    """
    Get the dimension of subflare, dots and circles.
    @rtype: float
    """

  def setSubSize(subsize):
    """
    Set the dimension of subflare, dots and circles.
    @type subsize: float
    @param subsize: The new value in [0.1, 25.0].
    """

  def getHardness():
    """
    Get the hardness of the specularity.
    @rtype: int
    """

  def setHardness(hardness):
    """
    Set the hardness of the specularity.
    @type hardness: int
    @param hardness: The new value in [1, 511].
    """

  def getNFlares():
    """
    Get the number of halo subflares.
    @rtype: int
    """

  def setNFlares(nflares):
    """
    Set the number of halo subflares.
    @type nflares: int
    @param nflares: The new value in [1, 32].
    """

  def getNStars():
    """
    Get the number of points in the halo stars.
    @rtype: int
    """

  def setNStars(nstars):
    """
    Set the number of points in the halo stars.
    @type nstars: int
    @param nstars: The new value in [3, 50].
    """

  def getNLines():
    """
    Get the number of star shaped lines on each halo.
    @rtype: int
    """

  def setNLines(nlines):
    """
    Set the number of star shaped lines on each halo.
    @type nlines: int
    @param nlines: The new value in [0, 250].
    """

  def getNRings():
    """
    Get the number of rings on each halo.
    @rtype: int
    """

  def setNRings(nrings):
    """
    Set the number of rings on each halo.
    @type nrings: int
    @param nrings: The new value in [0, 24].
    """

  def getRayMirr():
    """
    Get amount mirror reflection for raytrace.
    @rtype: float
    """

  def setRayMirr(nrmirr):
    """
    Set amount mirror reflection for raytrace.
    @type nrmirr: float
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getRayMirrDepth():
    """
    Get amount of inter-reflections calculated maximal.
    @rtype: int
    """

  def setRayMirrDepth(nrmirr):
    """
    Set amount mirror reflection for raytrace.
    @type nrmirr: int
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getFresnelMirr():
    """
    Get power of Fresnel for mirror reflection.
    @rtype: float
    """

  def setFresnelMirr(nrmirr):
    """
    Set power of Fresnel for mirror reflection.
    @type nrmirr: float
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getFresnelMirrFac():
    """
    Get the number of Ray Mirror.
    @rtype: float
    """

  def setFresnelMirrFac(nrmirr):
    """
    Set the number of ray mirror
    @type nrmirr: float
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getIOR():
    """
    Get the angular index of refraction for raytrace.
    @rtype: float
    """

  def setIOR(nrmirr):
    """
    Set the angular index of refraction for raytrace.
    @type nrmirr: float
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getTransDepth():
    """
    Get amount of refractions calculated maximal.
    @rtype: int
    """

  def setTransDepth(nrmirr):
    """
    Set amount of refractions calculated maximal.
    @type nrmirr: int
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getFresnelTrans():
    """
    Get power of Fresnel for transparency.
    @rtype: float
    """

  def setFresnelTrans(nrmirr):
    """
    Set power of Fresnel for transparency.
    @type nrmirr: float
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def getFresnelTransFac():
    """
    Get blending factor for Fresnel.
    @rtype: float
    """

  def setFresnelTransFac(nrmirr):
    """
    Set blending factor for Fresnel.
    @type nrmirr: float
    @param nrmirr: The new value in [0.0, 1.0].
    """

  def setTexture(index, texture, texco, mapto):
    """
    Assign a Blender Texture object to slot number 'number'.
    @type index: int
    @param index: material's texture index in [0, 9].
    @type texture: Blender Texture
    @param texture: a Blender Texture object.
    @type texco: int
    @param texco: optional or'ed bitflag -- defaults to TexCo.ORCO.  See TexCo var in L{Texture}.
    @type mapto: int
    @param mapto: optional or'ed bitflag -- defaults to MapTo.COL.  See MapTo var in L{Texture}.
    """

  def clearTexture(index):
    """
    Clear the ith (given by 'index') texture channel of this material.
    @type index: int
    @param index: material's texture channel index in [0, 9].
    """

  def getTextures ():
    """
    Get this Material's Texture list.
    @rtype: list of MTex
    @return: a list of Blender MTex objects.  None is returned for each empty
        texture slot.
    """

  def getScriptLinks (event):
    """
    Get a list with this Material's script links of type 'event'.
    @type event: string
    @param event: "FrameChanged" or "Redraw".
    @rtype: list
    @return: a list with Blender L{Text} names (the script links of the given
        'event' type) or None if there are no script links at all.
    """

  def clearScriptLinks (links = None):
    """
    Delete script links from this Material.  If no list is specified, all
    script links are deleted.
    @type links: list of strings
    @param links: None (default) or a list of Blender L{Text} names.
    """

  def addScriptLink (text, event):
    """
    Add a new script link to this Material.
    @type text: string
    @param text: the name of an existing Blender L{Text}.
    @type event: string
    @param event: "FrameChanged" or "Redraw".
    """
