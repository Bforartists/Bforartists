# Blender.Text3 module and the Text3d PyType object

"""
The Blender.Text3d submodule.

Text3d Objects
============

This module provides access to B{Font} objects in Blender.

Example::
  import Blender
  from Blender import Curve, Object, Scene, Text3d
  #
  txt = Text3d.New("MyText")          # create a new Text3d object
  cur = Scene.getCurrent()    # get current scene
  ob = Object.New('Text')    # make curve object
  ob.link(c)                  # link curve data with this object
  cur.link(ob)                # link object into scene
  ob.makeDisplayList()
  Window.RedrawAll()
"""

def New (name = None):
  """
  Create a new Text3d object.
  @type name: string
  @param name: The Text3d name.
  @rtype: Blender Text3d
  @return: The created Text3d Data object.
  """

def Get (name = None):
  """
  Get the Text3d object(s) from Blender.
  @type name: string
  @param name: The name of the Text3d object.
  @rtype: Blender Text3d or a list of Blender Text3ds
  @return: It depends on the 'name' parameter:
      - (name): The Text3d object with the given name;
      - ():     A list with all Text3d objects in the current scene.
  """
class Text3d:
  """
  The Text3d object
  ===============
    This object gives access to Text3ds in Blender.
  @cvar name: The Text3d name.
  @cvar filename: The filename of the file loaded into this Text.
  @cvar mode: The follow_mode flag: if 1 it is 'on'; if 0, 'off'.
  @cvar nlines: The number of lines in this Text.
  """

  def getName():
    """
    Get the name of this Text3d object.
    @rtype: string
    """

  def setName(name):
    """
    Set the name of this Text3d object.
    @type name: string
    @param name: The new name.
    """

  def getText(data):
    """
    Get string text of Text3d object
    @type data: string
    @param data:  The string name of Text3d.
    """

  def setText(name):
    """
    Set string text to be redering in Text3d object
    @type name: string
    @param name:  The string name of Text3d.
    """

