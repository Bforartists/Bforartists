# mesh_select_by_edge_length.py Copyright (C) 2011, Dolf Veenvliet
#
# Extrude a selection from a mesh multiple times
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
'''
bl_info = {
    "name": "Select by edge length",
    "author": "Dolf Veenvliet",
    "version": (1,),
    "blender": (2, 56, 0),
    "location": "View3D > Select",
    "description": "Select all items whose scale/length/surface matches a certain edge length",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

"""
Usage:

Launch from from "Select -> By edge length"

Additional links:
	Author Site: http://www.macouno.com
	e-mail: dolf {at} macouno {dot} com
"""
'''
import bpy, mathutils, math
from bpy.props import FloatProperty, BoolProperty, EnumProperty


class Select_by_edge_length():

	# Initialise the class
	def __init__(self, context, edgeLength, bigger, smaller, extend, space):

		self.ob = context.active_object
		bpy.ops.object.mode_set(mode='OBJECT')

		self.space = space
		self.obMat = self.ob.matrix_world

		# We ignore vert selections completely
		#vertSelect = bpy.context.tool_settings.mesh_select_mode[0]
		edgeSelect = bpy.context.tool_settings.mesh_select_mode[1]
		faceSelect = bpy.context.tool_settings.mesh_select_mode[2]


		# Edge select
		if edgeSelect:

			hasSelected = self.hasSelected(self.ob.data.edges)

			for e in self.ob.data.edges:

				if  self.selectCheck(e.select, hasSelected, extend):

					len = self.getEdgeLength(e.vertices)

					if len == edgeLength or (bigger and len >= edgeLength) or (smaller and len <= edgeLength):
						e.select = True

				if self.deselectCheck(e.select, hasSelected, extend):
					len = self.getEdgeLength(e.vertices)

					if len != edgeLength and not (bigger and len >= edgeLength) and not (smaller and len <= edgeLength):
						e.select = False

		# Face select
		if faceSelect:

			hasSelected = self.hasSelected(self.ob.data.polygons)

			# Loop through all the given faces
			for f in self.ob.data.polygons:

				# Check if the faces match any of the directions
				if self.selectCheck(f.select, hasSelected, extend):

					min = 0.0
					max = 0.0

					for i, e in enumerate(f.edge_keys):
						len = self.getEdgeLength(e)
						if not i:
							min = len
							max = len
						elif len < min:
							min = len
						elif len > max:
							max = len

					if (min == edgeLength and max == edgeLength) or (bigger and min >= edgeLength) or (smaller and max <= edgeLength):
						f.select = True

				if self.deselectCheck(f.select, hasSelected, extend):

					min = 0.0
					max = 0.0

					for i, e in enumerate(f.edge_keys):
						len = self.getEdgeLength(e)
						if not i:
							min = len
							max = len
						elif len < min:
							min = len
						elif len > max:
							max = len

					if (min != edgeLength and max != edgeLength) and not (bigger and  min >= edgeLength) and not (smaller and max <= edgeLength):
						f.select = False


		bpy.ops.object.mode_set(mode='EDIT')



	# Get the lenght of an edge, by giving this function all verts (2) in the edge
	def getEdgeLength(self, verts):

		vec1 = self.ob.data.vertices[verts[0]].co
		vec2 = self.ob.data.vertices[verts[1]].co

		vec = vec1 - vec2

		if self.space == 'GLO':
			vec *= self.obMat

		return round(vec.length, 5)



	# See if the current item should be selected or not
	def selectCheck(self, isSelected, hasSelected, extend):

		# If the current item is not selected we may want to select
		if not isSelected:

			# If we are extending or nothing is selected we want to select
			if extend or not hasSelected:
				return True

		return False



	# See if the current item should be deselected or not
	def deselectCheck(self, isSelected, hasSelected, extend):

		# If the current item is selected we may want to deselect
		if isSelected:

			# If something is selected and we're not extending we want to deselect
			if hasSelected and not extend:
				return True

		return False



	# See if there is at least one selected item
	def hasSelected(self, items):

		for item in items:
			if item.select:
				return True

		return False



class Select_init(bpy.types.Operator):
	'''Select all items with normals facing a certain direction'''
	bl_idname = 'mesh.select_by_edge_length'
	bl_label = 'Select by edge length'
	bl_options = {'REGISTER', 'UNDO'}

	edgeLength = FloatProperty(name='Edge length', description='The scale in Blender units', default=1.0, min=0.0, max=1000.0, soft_min=0.0, soft_max=100.0, step=100, precision=2)

	bigger = BoolProperty(name='Bigger', description='Select items bigger than the size setting', default=False)

	smaller = BoolProperty(name='Smaller', description='Select items smaller than the size setting', default=False)

	extend = BoolProperty(name='Extend', description='Extend the current selection', default=False)

	# The spaces we use
	spaces=(('LOC', 'Local', ''),('GLO', 'Global', ''))

	space = EnumProperty(items=spaces, name='Space', description='The space to interpret the directions in', default='LOC')

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and not bpy.context.tool_settings.mesh_select_mode[0])

	def execute(self, context):
		SELECT_EDGES = Select_by_edge_length(context, self.edgeLength, self.bigger, self.smaller, self.extend, self.space)
		return {'FINISHED'}

