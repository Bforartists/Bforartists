# mesh_bump.py Copyright (C) 2011, Dolf Veenvliet
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
    "name": "Bump",
    "author": "Dolf Veenvliet",
    "version": 1,
    "blender": (2, 56, 0),
    "location": "View3D > Specials > Bump",
    "description": "Extrude and translate/rotate/scale multiple times",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

"""
Usage:

Launch from "W-menu"

Additional links:
	Author Site: http://www.macouno.com
	e-mail: dolf {at} macouno {dot} com
"""

import bpy
from bpy.props import EnumProperty, FloatVectorProperty, FloatProperty, BoolProperty
from . import mesh_extras

# Bump stuff!
class Bump():

	# Initialise the class
	def __init__(self, context, type, scale, steps):

		self.ob = context.active_object
		bpy.ops.object.mode_set(mode='OBJECT')

		translate = mesh_extras.get_average_outer_edge_length()
		#inset = mesh_extras.get_shortest_outer_edge_length() * 0.25

		translate *= scale

		bpy.ops.object.mode_set(mode='EDIT')

		stepped = 0

		# Simple... we just do a bunch of steps... set in stone... easy!
		if type == 'BUM':

			self.extrude()

			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.mode_set(mode='EDIT')

			self.shrink(-translate)
			self.shrink(translate*0.3)

			stepped += 1

		# Spike!
		elif type == 'SPI':

			for i in range(3):

				self.extrude()

				bpy.ops.object.mode_set(mode='OBJECT')
				bpy.ops.object.mode_set(mode='EDIT')

				if not i:
					f = 0.5
				elif i == 1:
					f = 0.3
				elif i == 2:
					f = 0.2

				t = translate * f

				self.shrink(-t)
				self.shrink(t * (2 * f))

				stepped += 1

		# Dimple!
		elif type == 'DIM' or type == 'PIM':

			self.extrude()
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.mode_set(mode='EDIT')

			self.shrink(-translate * 0.2)

			self.extrude()
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.mode_set(mode='EDIT')

			self.shrink(translate * 0.2)
			self.shrink(-translate * 0.2)

			if type == 'PIM':
				self.extrude()
				bpy.ops.object.mode_set(mode='OBJECT')
				bpy.ops.object.mode_set(mode='EDIT')

				self.shrink(-translate * 0.2)
				stepped = 3
			else:
				stepped = 2




		if steps:
			self.ob['growsteps'] = stepped



	# Extrude the selection (do not move it)
	def extrude(self):
		bpy.ops.mesh.extrude_faces_move()

	# SHrink!
	def shrink(self,v):
		bpy.ops.transform.shrink_fatten(value=v, mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)



class Bump_init(bpy.types.Operator):
	'''Bump by extruding and moving/rotating/scaling multiple times'''
	bl_idname = 'mesh.bump'
	bl_label = 'Inset Extrude Bump'
	bl_options = {'REGISTER', 'UNDO'}

	# The falloffs we use
	types=(
		('BUM', 'Bump',''),
		('SPI', 'Spike',''),
		('DIM', 'Dimple',''),
		('PIM', 'Pimple',''),
		)

	type = EnumProperty(items=types, name='Type', description='The type of bump', default='BUM')

	# Scale
	scale = FloatProperty(name='Scale factor', description='Translation in Blender units', default=1.0, min=0.01, max=1000.0, soft_min=0.01, soft_max=1000.0, step=10, precision=2)

	steps = BoolProperty(name='Retain steps', description='Keep the step count in a property', default=False)

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and bpy.context.tool_settings.mesh_select_mode[0] == False and bpy.context.tool_settings.mesh_select_mode[1] == False and bpy.context.tool_settings.mesh_select_mode[2] == True)

	def execute(self, context):
		BUMP = Bump(context, self.type, self.scale, self.steps)
		return {'FINISHED'}

class bump_help(bpy.types.Operator):
	bl_idname = 'help.bump'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Make a selection or selection of Faces ')
		layout.label('Choose from the bump types in the menu')
		layout.label('To Help:')
		layout.label('Keep extrusions small to prevent overlapping')
		layout.label('Do not select all faces')
		layout.label('if using with create armature, enter object mode first')

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 350)
'''
def menu_func(self, context):
	self.layout.operator(Bump_init.bl_idname, text="Bump")

def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
	register()
'''