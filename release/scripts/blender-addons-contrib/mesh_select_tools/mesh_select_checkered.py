# mesh_select_checkered.py Copyright (C) 2011, Dolf Veenvliet
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

bl_info = {
    "name": "Select checkered",
    "author": "Dolf Veenvliet",
    "version": (1,),
    "blender": (2, 56, 0),
    "location": "View3D > Select",
    "description": "Select checkered",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

"""
Usage:

Launch from from "Select -> checkered"

Additional links:
	Author Site: http://www.macouno.com
	e-mail: dolf {at} macouno {dot} com
"""

import bpy
from bpy.props import BoolProperty


class Select_checkered():

	# Initialise the class
	def __init__(self, context, invert, extend):

		self.ob = context.active_object
		bpy.ops.object.mode_set(mode='OBJECT')

		self.invert = invert

		self.selectedVerts = []
		self.selectedFaces = []
		self.deselectedFaces = []

		hasSelected = self.hasSelected(self.ob.data.polygons)


		working = True
		while working:

			working = False

			# Loop through all the given faces
			for f in self.ob.data.polygons:

				if not f.index in self.selectedFaces and not f.index in self.deselectedFaces:

					choice = self.Choose(f)

					if choice != 'skip':

						s = self.selectCheck(f.select, hasSelected, extend)
						d = self.deselectCheck(f.select, hasSelected, extend)

						# Check if the faces match any of the directions
						if s and choice:
							f.select = True
							working = True

						if d and not choice:
							f.select = False
							working = True

		bpy.ops.object.mode_set(mode='EDIT')



	# Choose whether or not to select
	def Choose(self, f):

		choice = 'skip'

		if not len(self.selectedFaces):
			choice = True
			self.selectedFaces.append(f.index)
			self.selectedVerts.extend(f.vertices)

		else:
			intersection = [v for v in f.vertices if v in self.selectedVerts]

			if len(intersection) == 1:
				choice = True
				self.selectedFaces.append(f.index)
				self.selectedVerts.extend(f.vertices)

			elif len(intersection) == 2:
				choice = False
				self.deselectedFaces.append(f.index)

		if self.invert:
			if choice:
				choice = False
			else:
				choice = True
		return choice


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
	'''Select faces based on pi'''
	bl_idname = 'mesh.select_checkered'
	bl_label = 'Select checkered'
	bl_options = {'REGISTER', 'UNDO'}

	invert = BoolProperty(name='Invert', description='Invert the selection result', default=False)

	extend = BoolProperty(name='Extend', description='Extend the current selection', default=False)

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def execute(self, context):
		SELECT_DIRECTION = Select_checkered(context, self.invert, self.extend)
		return {'FINISHED'}

