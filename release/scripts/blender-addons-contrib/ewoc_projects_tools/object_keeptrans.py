# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
The KeepTrans addon works when you want to remove a ChildOf constraint, but keep the
constrained objects transforms.


Documentation

First go to User Preferences->Addons and enable the KeepTrans addon in the Object category.
Select the child object of your choice and invoke the addon (button in the Object Tools panel).

If you wish to hotkey DeCouple:
In the Input section of User Preferences at the bottom of the 3D View > Object Mode section click 'Add New' button.
In the Operator Identifier box put 'object.keeptrans'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "KeepTrans",
	"author": "Gert De Roost",
	"version": (0, 5, 1),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Remove ChildOf constraint and keep transforms",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"}



import bpy
from mathutils import *






class DeCouple(bpy.types.Operator):
	bl_idname = "object.keeptrans"
	bl_label = "KeepTrans"
	bl_description = "Remove ChildOf constraint and keep transforms"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		have = False
		for c in obj.constraints:
			if c.type == "CHILD_OF":
				have =  True
		return (obj and context.mode == 'OBJECT' and have)

	def invoke(self, context, event):

		self.do_keeptrans(context)

		return {'FINISHED'}


	def do_keeptrans(self, context):

		ob = context.active_object
		childof = None
		for c in ob.constraints:
			if c.type == "CHILD_OF":
				childof = c
				break
		if childof == None:
			return
		loc = ob.matrix_world.to_translation()
		dim = ob.dimensions
		mat = ob.matrix_world
		ob.constraints.remove(childof)
		ob.location = loc
		ob.dimensions = dim
		ob.matrix_world = mat




def panel_func(self, context):
	self.layout.label(text="KeepTrans:")
	self.layout.operator("object.keeptrans", text="KeepTrans")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_objectmode.remove(panel_func)


if __name__ == "__main__":
	register()






