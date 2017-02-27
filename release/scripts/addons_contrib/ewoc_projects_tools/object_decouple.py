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
The DeCouple addon is really simple but useful: the selected parent object will be decoupled
temporarily from its children so youll be able to reposition the parent without influencing
the children.  This is mainly a workflow shortcut, cause unparenting and reparenting
can take some time when there are many children.


Documentation

First go to User Preferences->Addons and enable the DeCouple addon in the Object category.
Select the parent object of your choice and click "Unparent" (button in the Object Tools panel)
to unparent all children while keeping transform.  Now ex-parent can be transformed.
Then click "Reparent" to reparent all children to the ex-parent object.

If you wish to hotkey DeCouple:
In the Input section of User Preferences at the bottom of the 3D View > Object Mode section click 'Add New' button.
In the Operator Identifier box put 'object.decouple'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "DeCouple",
	"author": "Gert De Roost",
	"version": (0, 2, 1),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Temporarily decouples parent and children",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"}



import bpy


unparented = False



class DeCouple(bpy.types.Operator):
	bl_idname = "object.decouple"
	bl_label = "DeCouple"
	bl_description = "Temporarily decouples parent and children"
	bl_options = {"REGISTER", "UNDO"}


	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and context.mode == 'OBJECT' and obj.children)

	def execute(self, context):

		global unparented

		self.do_decouple(context)
		unparented = True

		return {'FINISHED'}


	def do_decouple(self, context):

		global parent, children

		parent = context.active_object
		if len(parent.children) == 0:
			return
		parent.select = 0
		children = []
		for child in parent.children:
			children.append(child)
			child.select = 1
		bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
		for child in children:
			child.select = 0
		parent.select = 1
		context.scene.objects.active = parent


class ReCouple(bpy.types.Operator):
	bl_idname = "object.recouple"
	bl_label = "ReCouple"
	bl_description = "Recouples decoupled parent and children"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and context.mode == 'OBJECT')

	def execute(self, context):

		global unparented

		self.do_recouple(context)
		unparented = False

		return {'FINISHED'}

	def do_recouple(self, context):

		parent.select = 0
		for child in children:
			child.select = 1
		parent.select = 1
		context.scene.objects.active = parent
		bpy.ops.object.parent_set()
		for child in children:
			child.select = 0





def panel_func(self, context):

	self.layout.label(text="DeCouple:")
	if not(unparented):
		self.layout.operator("object.decouple", text = "Unparent")
	else:
		self.layout.operator("object.recouple", text = "Reparent")


def register():

	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_objectmode.remove(panel_func)


if __name__ == "__main__":
	register()






