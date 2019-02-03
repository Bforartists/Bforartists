# Copyright 2015 Théo Friberg under GNU GPL 3

if "bpy" in locals():
	import importlib
	importlib.reload(JSONOps)
else:
	from . import JSONOps

import bpy
import os
import glob

class AutomatOperatorFromTexture(bpy.types.Operator):

	"""This operator generates automatic materials from textures in Cycles."""

	# Metadata of the operator

	bl_idname = "com.new_automat"
	bl_label = "Automatic Material from Image"
	bl_options = {"UNDO"}

	# Variables used for storing the filepath given by blender's file manager

	filepath: bpy.props.StringProperty(subtype="FILE_PATH")
	filename: bpy.props.StringProperty()
	directory: bpy.props.StringProperty(subtype="FILE_PATH")

	make_seamless: bpy.props.BoolProperty(name="Make Seamless", description="Make tileable (removes visible borders of the image).")

	def execute(self, context):

		"""This is the main runnable method of the operator.

This creates all the node setup."""

		# Create the material

		mat = bpy.data.materials.new(self.filename)

		mat.use_nodes = True
		nodes = mat.node_tree.nodes

		# Empty whatever nodes we allready had.

		for node in nodes.keys():
			nodes.remove(nodes[node])

		nodes_dict = {}

		# Create the main part of the material

		nodes_dict = JSONOps.inflateFile(mat, os.path.dirname(
									  os.path.realpath(__file__))+os.sep+
									  "automatic_material.json")



		# We load the images

		image_data = bpy.data.images.load(self.filepath)
		nodes_dict["Color Image"].image = image_data

		# We check if the texture must be made seamless

		if self.make_seamless:
			seamless_vector = JSONOps.inflateFile(mat, os.path.dirname(os.path.realpath(__file__))+os.sep+"seamless_vector.json", -3000, 0)
			links = mat.node_tree.links
			links.new(seamless_vector["Pick Vector"].outputs["Color"], nodes_dict["Color Image"].inputs["Vector"])

		# Below we check potential maps

		modified_fname = self.filename.split(".")

		# Check if we are dealing with maps generated with CrazyBump.
		# If so is the case, the color map is by default suffixed with _COLOR

		known_scheme = False

		if modified_fname[0][-6:] == "_COLOR":

			# We are dealing with CrazyBump and we remove the suffix

			modified_fname[0] = modified_fname[0][:-6]
			known_scheme = True

		other_files = []
		folder = os.path.split(self.filepath)[0]+os.path.sep+"*"
		pattern = folder + ".".join(modified_fname[:-1])+"*."+modified_fname[-1]
		other_files = glob.glob(pattern)

		# We check if we can find a Specularity Map

		specmap = ""

		for file in other_files:
			if "spec" in os.path.split(file)[-1].lower():
				specmap = file
				break

		if len(specmap) > 0:

			spec_map = nodes.new("ShaderNodeTexImage")
			spec_map.location = [nodes_dict["Adjust reflectivity"].location[0],
								 nodes_dict["Adjust reflectivity"].location[1]+50]
			spec_map.label = "Specularity Map"
			nodes.remove(nodes_dict["Adjust reflectivity"])
			spec_map.image = bpy.data.images.load(specmap)
			links = mat.node_tree.links

			links.new(spec_map.outputs["Color"],
					  nodes_dict["Mix Shaders"].inputs[0])
			if self.make_seamless:
				links.new(seamless_vector["Pick Vector"].outputs["Color"], spec_map.inputs["Vector"])

		# We check if we can find a Normal Map

		normalmap = ""

		for file in other_files:
			if "normal" in os.path.split(file)[-1].lower() or ".".join(os.path.split(file)[1].split(".") [:-1])[-4:] == "_NRM":
				normalmap = file
				break

		if len(normalmap) > 0 and ((not "normal" in self.filename.lower()) or known_scheme):

			normal_map = nodes.new("ShaderNodeTexImage")
			normal_map.location = [nodes_dict["Color Image"].location[0],
								   nodes_dict["Color Image"].location[1]-240]
			normal_map.label = "Normal Map"
			normal_map.image = bpy.data.images.load(normalmap)
			links = mat.node_tree.links

			normal = nodes.new("ShaderNodeNormalMap")
			normal.location = [nodes_dict["Convert to Bump Map"].location[0],
							   nodes_dict["Convert to Bump Map"].location[1]]
			nodes.remove(nodes_dict["Convert to Bump Map"])
			links.new(normal_map.outputs["Color"],
					  normal.inputs[1])
			links.new(normal.outputs["Normal"],
					  nodes_dict["Diffuse Component"].inputs[2])
			links.new(normal.outputs["Normal"],
					  nodes_dict["Glossy Component"].inputs[2])
			if self.make_seamless:
				links.new(seamless_vector["Pick Vector"].outputs["Color"], normal_map.inputs["Vector"])

		# We check if we can find a Bump Map

		bumpmap = ""

		for file in other_files:
			if "bump" in os.path.split(file.lower())[-1]:
				bumpmap = file
				break

		if len(bumpmap) > 0 and not "bump" in self.filename.lower() and not len(normalmap) > 0:

			bump_map = nodes.new("ShaderNodeTexImage")
			bump_map.location = [nodes_dict["Color Image"].location[0],
								 nodes_dict["Color Image"].location[1]-240]
			bump_map.label = "Bump Map"
			bump_map.image = bpy.data.images.load(bumpmap)
			links = mat.node_tree.links
			links.new(bump_map.outputs["Color"], nodes_dict["Convert to Bump Map"].inputs[2])
			if self.make_seamless:
				links.new(seamless_vector["Pick Vector"].outputs["Color"], bump_map.inputs["Vector"])

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
			self.report({'ERROR'}, "Can't generate Cycles material with Blender"
			"internal as active renderer.")
			return {"FINISHED"}
