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
The FanConnect addon connects multiple selected verts to one single other vert.


Documentation

First go to User Preferences->Addons and enable the FanConnect addon in the Mesh category.
Go to EditMode, select all verts (the vert to connect to last) and invoke
the addon (button in the Mesh Tool panel).  The first selected vertices will be connected to the last.

If you wish to hotkey FanConnect:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.fanconnect'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "FanConnect",
	"author": "Gert De Roost",
	"version": (0, 2, 1),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Connects multiple selected verts to one single other vert.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bmesh



class FanConnect(bpy.types.Operator):
	bl_idname = "mesh.fanconnect"
	bl_label = "Fan Connect"
	bl_description = "Connects multiple selected verts to one single other vert"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH' and list(context.tool_settings.mesh_select_mode)[0] == True)

	def invoke(self, context, event):

		ret = self.do_fanconnect(context)
		if ret == False:
			return {'CANCELLED'}
		self.bm.free()
		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()

		return {'FINISHED'}




	def do_fanconnect(self, context):

		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()
		# initialization
		selobj = context.active_object
		mesh = selobj.data
		self.bm = bmesh.from_edit_mesh(mesh)
		actvert = self.bm.select_history.active
		if not(isinstance(actvert, bmesh.types.BMVert)):
			return False

		vertlist = []
		for v in self.bm.verts:
			if v.select:
				if not(v == actvert):
					vertlist.append(v)

		# do connection
		for v in vertlist:
			for f in actvert.link_faces:
				if v in f.verts:
					# when already face: split it
					bmesh.ops.connect_verts(self.bm, verts=[v, actvert])
		for v in vertlist:
			v2 = None
			for e in v.link_edges:
				v2 = e.other_vert(v)
				if v2 in vertlist:
					already = False
					for f in actvert.link_faces:
						if v in f.verts and v2 in f.verts:
							already = True
							break
					# if no face already between to first and selected vert: make it
					if not(already):
						self.bm.faces.new([v, actvert, v2])




def panel_func(self, context):
	self.layout.label(text="FanConnect:")
	self.layout.operator("mesh.fanconnect", text="Connect mult")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()






