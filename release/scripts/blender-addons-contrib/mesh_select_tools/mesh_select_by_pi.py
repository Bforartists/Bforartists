# mesh_select_by_pi.py Copyright (C) 2011, Dolf Veenvliet
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
    "name": "Select by pi",
    "author": "Dolf Veenvliet",
    "version": 1,
    "blender": (2, 56, 0),
    "location": "View3D > Select",
    "description": "Select fake random based on pi",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

"""
Usage:

Launch from from "Select -> By pi"

Additional links:
	Author Site: http://www.macouno.com
	e-mail: dolf {at} macouno {dot} com
"""
'''
import bpy
from bpy.props import BoolProperty


class Select_by_pi():

	# Initialise the class
	def __init__(self, context, e, invert, extend):

		self.ob = context.active_object
		bpy.ops.object.mode_set(mode='OBJECT')

		self.invert = invert

		# Make pi as a list of integers
		if e:
			self.pi = list('27182818284590452353602874713526624977572470936999')
		else:
			self.pi = list('31415926535897932384626433832795028841971693993751')

		self.piLen = len(self.pi)
		self.piPos = 0

		vertSelect = bpy.context.tool_settings.mesh_select_mode[0]
		edgeSelect = bpy.context.tool_settings.mesh_select_mode[1]
		faceSelect = bpy.context.tool_settings.mesh_select_mode[2]

		# Vert select
		if vertSelect:

			hasSelected = self.hasSelected(self.ob.data.vertices)

			for v in self.ob.data.vertices:

				s = self.selectCheck(v.select, hasSelected, extend)
				d = self.deselectCheck(v.select, hasSelected, extend)

				# Check if the verts match any of the directions
				if s and self.choose():
					v.select = True

				if d and not self.choose():
					v.select = False

		# Edge select
		if edgeSelect:

			hasSelected = self.hasSelected(self.ob.data.edges)

			for e in self.ob.data.edges:

				s = self.selectCheck(e.select, hasSelected, extend)
				d = self.deselectCheck(e.select, hasSelected, extend)

				if s and self.choose():
					e.select = True

				if d and not self.choose():
					e.select = False

		# Face select
		if faceSelect:

			hasSelected = self.hasSelected(self.ob.data.polygons)

			# Loop through all the given faces
			for f in self.ob.data.polygons:

				s = self.selectCheck(f.select, hasSelected, extend)
				d = self.deselectCheck(f.select, hasSelected, extend)

				# Check if the faces match any of the directions
				if s and self.choose():
					f.select = True

				if d and not self.choose():
					f.select = False

		bpy.ops.object.mode_set(mode='EDIT')



	# Choose by pi
	def choose(self):
		choice = True

		# We just choose the odd numbers
		if int(self.pi[self.piPos]) % 2:
			choice = False

		if self.invert:
			if choice:
				choice = False
			else:
				choice = True

		self.incrementPiPos()
		return choice



	# Increment the pi position
	def incrementPiPos(self):
		self.piPos += 1
		if self.piPos == self.piLen:
			self.piPos = 0



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
	bl_idname = 'mesh.select_by_pi'
	bl_label = 'Select by pi'
	bl_options = {'REGISTER', 'UNDO'}

	e = BoolProperty(name='Use e', description='use e in stead of pi', default=False)

	invert = BoolProperty(name='Invert', description='Invert the selection result', default=False)

	extend = BoolProperty(name='Extend', description='Extend the current selection', default=False)

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def execute(self, context):
		SELECT_DIRECTION = Select_by_pi(context, self.e, self.invert, self.extend)
		return {'FINISHED'}
