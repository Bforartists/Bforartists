# mesh_Select_innermost.py Copyright (C) 2011, Dolf Veenvliet
#
# Relaxes selected vertices while retaining the shape as much as possible
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
    "name": "Select innermost",
    "author": "Dolf Veenvliet",
    "version": (0,3),
    "blender": (2, 57, 0),
    "location": "Select > Innermost",
    "description": "Select the innermost faces",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

"""
Usage:

Launch from "Select -> Innermost"


Additional links:
	Author Site: http://www.macouno.com
	e-mail: dolf {at} macouno {dot} com
"""
'''
import bpy
from bpy.props import BoolProperty
from . import mesh_extras

# Grow stuff!
class Select_innermost():

	# Initialise the class
	def __init__(self, context, invert):

		me = context.active_object.data
		bpy.ops.object.mode_set(mode='OBJECT')

		oList = [f.index for f in mesh_extras.get_selected_faces()]
		oLen = len(oList)

		# If no faces are selected, we just return
		if not oLen:
			bpy.ops.object.mode_set(mode='EDIT')
			return

		# If all faces are selected, select nothing and return
		if oLen == len(me.polygons):
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='DESELECT')
			return

		fList = False

		# If we invert, we just want to select less once, and then we're done
		if invert:

			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_less()
			bpy.ops.object.mode_set(mode='OBJECT')

			fList = [f.index for f in mesh_extras.get_selected_faces()]

			# Only if there's now less selected do we change anything
			if len(fList) < oLen:

				for f in me.polygons:
					fIn = f.index
					if fIn in oList and not fIn in fList:
						f.select = True
					else:
						f.select = False

			bpy.ops.object.mode_set(mode='EDIT')
			return


		# So now we can start and see what's up
		while mesh_extras.contains_selected_item(me.polygons):

			if fList is False:
				fList = oList
			else:
				fList = [f.index for f in mesh_extras.get_selected_faces()]

			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_less()
			bpy.ops.object.mode_set(mode='OBJECT')

		if len(fList) < oLen:
			for f in me.faces:
				if f.index in fList:
					f.select = True
				else:
					f.select = False

		bpy.ops.object.mode_set(mode='EDIT')



class Select_innermost_init(bpy.types.Operator):
	'''Select the innermost faces of the current selection'''
	bl_idname = 'mesh.select_innermost'
	bl_label = 'Select innermost'
	bl_options = {'REGISTER', 'UNDO'}

	invert = BoolProperty(name='Invert', description='Invert the selection result (select outermost)', default=False)

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def execute(self, context):
		innermost = Select_innermost(context, self.invert)
		return {'FINISHED'}

