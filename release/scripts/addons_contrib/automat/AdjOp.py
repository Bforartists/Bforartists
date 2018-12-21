# Copyright 2015 Théo Friberg under GNU GPL 3

if "bpy" in locals():
	import importlib
	importlib.reload(JSONOps)
else:
	from . import JSONOps

import bpy
import os

class AdjustableOperatorFromTexture(bpy.types.Operator):

    """This operator generates adjustable materials from textures in Cycles.

This is a subclass from bpy.types.Operator.
"""

    # Metadata of the operator

    bl_idname = "com.new_adj_automat"
    bl_label = "Adjustable Material from Image"
    bl_options = {"UNDO"}

    # Variables used for storing the filepath given by blender's file manager

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty()
    directory = bpy.props.StringProperty(subtype="FILE_PATH")




    def execute(self, context):

        """This is the main runnable method of the operator.

This creates all the node setup."""

        # Create the material

        mat = bpy.data.materials.new("Material")

        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        # Empty whatever nodes we allready had.

        for node in nodes.keys():
            nodes.remove(nodes[node])

        nodes_dict = {}

        # Create the main part of the material

        nodes_dict = JSONOps.inflateFile(mat, os.path.dirname(
                                      os.path.realpath(__file__))+os.sep+
                                      "adj_material.json")

        # We create all of our blurs

        blurs = [

            JSONOps.inflateFile(mat, os.path.dirname(os.path.realpath(__file__))+
                             os.sep+"blur.json", -2500, -300),
            JSONOps.inflateFile(mat, os.path.dirname(os.path.realpath(__file__))+
                             os.sep+"blur.json", -2300, 300)
        ]

        # We set one of our blurs to be stronger

        blurs[1]["Blur strength"].outputs[0].default_value = 1000

        # We link the blurs up to the rest of the material

        links = mat.node_tree.links

        links.new(blurs[1]["Correct strength vector math"].outputs[0],
                  nodes_dict["Greater Than"].inputs[0])
        links.new(blurs[0]["Correct strength vector math"].outputs[0],
                  nodes_dict["Bumpmap Mix RGB"].inputs[2])
        links.new(nodes_dict["Texture Co-ordinate"].outputs["UV"],
                  blurs[0]["Add noise"].inputs[0])

        # We load the images

        image_data = bpy.data.images.load(self.filepath)
        nodes_dict["Color Image"].image = image_data
        nodes_dict["Bump Image"].image = image_data

        # Try to add the material to the selected object

        try:
            bpy.context.object.data.materials.append(mat)
        except AttributeError:

            # If there is no object with materials selected,
            # don't add the material to anythinng.

            pass

        # Tell that all went well

        return {"FINISHED"}

    def invoke(self, context, event):

        """This method opens the file browser. After that, the
execute(...) method gets ran, creating the node setup.
It also checks that the render engine is Cycles.  """

        if bpy.context.scene.render.engine == 'CYCLES':
            self.filename = ""
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}
        else:
            self.report({'ERROR'}, "Can't generate Cycles material with Blender internal as active renderer.")
            return {"FINISHED"}
