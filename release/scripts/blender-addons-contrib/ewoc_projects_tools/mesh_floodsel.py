# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
This addon enables you to "flood-select" or deselect entire areas of selected/deselected elements.


Documentation

First go to User Preferences->Addons and enable the FloodSel addon in the Mesh category.
Go to EditMode, select one or more areas of elements.  Invoke addon (button in Mesh Tools panel)
Click area with leftmouse to select/deselect and rightmouse to cancel.	Choose "Multiple" tickbox
if you want to do several operations in succession, and ENTER to keep changes.	Click tickbox
"Preselection" to preview selection/deselection when hovering mouse over areas.
Check "Deselect" if you want to deselect instead of select.
View can be transformed during operation.
Works in all viewports.

If you wish to hotkey FloodSel:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.floodsel'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "FloodSel",
	"author": "Gert De Roost",
	"version": (1, 1, 2),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Flood-(de)select areas.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bpy_extras
import bmesh
from mathutils import *


started = False



def change_header(self, context):

	if mainop.SelectMode == 0 and not(mainop.Multiple):
		mainop.area.header_text_set(text="FloodSel :  Leftclick selects")
	elif mainop.SelectMode == 1 and not(mainop.Multiple):
		mainop.area.header_text_set(text="FloodSel :  Leftclick deselects")
	elif mainop.SelectMode == 0 and mainop.Multiple:
		mainop.area.header_text_set(text="FloodSel :  Leftclick selects - Rightmouse/Enter exits")
	elif mainop.SelectMode == 1 and mainop.Multiple:
		mainop.area.header_text_set(text="FloodSel :  Leftclick deselects - Rightmouse/Enter exits")



class FloodSel(bpy.types.Operator):
	bl_idname = "mesh.floodsel"
	bl_label = "FloodSel"
	bl_description = "Flood-(de)select areas"
	bl_options = {'REGISTER', 'UNDO'}


	SelectMode = bpy.props.BoolProperty(
		name = "Deselect",
		description = "Switch between selecting and deselecting",
		default = False,
		update = change_header)

	Multiple = bpy.props.BoolProperty(
		name = "Multiple",
		description = "Several operations after each other",
		default = False,
		update = change_header)

	Preselection = bpy.props.BoolProperty(
		name = "Preselection",
		description = "Preview when hovering over areas",
		default = True)

	Diagonal = bpy.props.BoolProperty(
		name = "Diagonal is border",
		description = "Diagonal selections are treated as borders",
		default = True)


	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		global mainop, started

		started = True

		mainop = self

		self.initialize(context)

		context.window_manager.modal_handler_add(self)

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		global started

		if event.type in ['MIDDLEMOUSE']:
			return {'PASS_THROUGH'}
		elif event.type in ['WHEELDOWNMOUSE', 'WHEELUPMOUSE']:
			return {'PASS_THROUGH'}
		elif event.type in ['LEFTMOUSE']:
			if not(self.region):
				return {'PASS_THROUGH'}

			if not(self.Preselection):
				for elem in self.doneset:
					elem.select = not(self.state)
			if not(self.Multiple):
				started = False
				self.bm.free()
				bpy.ops.object.editmode_toggle()
				bpy.ops.object.editmode_toggle()
				return {'FINISHED'}
			else:
				self.doneset = set([])
			return {'RUNNING_MODAL'}
		elif event.type in {'RET', 'RIGHTMOUSE'}:
			started = False
			del bpy.types.Scene.PreSelOff
			# Consolidate changes if ENTER pressed.
			# Free the bmesh.
			self.area.header_text_set()
			self.bm.free()
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			return {'FINISHED'}
		elif event.type in ['MOUSEMOVE']:

			mxa = event.mouse_x
			mya = event.mouse_y

			oldregion = self.region
			self.region = None
			for a in context.screen.areas:
				if not(a.type == 'VIEW_3D'):
					continue
				for r in a.regions:
					if mxa > r.x and mya > r.y and mxa < r.x + r.width and mya < r.y + r.height:
						if not(r.type == 'WINDOW'):
							self.region = None
							break
						self.region = r
						for sp in a.spaces:
							if sp.type == 'VIEW_3D':
								self.space = sp

			if not(self.region):
				if len(self.doneset):
					oldregion.tag_redraw()
					for elem in self.doneset:
						elem.select = self.state
					self.doneset = set([])
				return {'PASS_THROUGH'}

			for elem in self.doneset:
				elem.select = self.state

			mx = mxa - self.region.x
			my = mya - self.region.y

			rv3d = self.space.region_3d
			eye = Vector(rv3d.view_matrix.inverted().col[3][:3])
			mpoint = Vector((mx, my))
			mvec = bpy_extras.view3d_utils.region_2d_to_vector_3d(self.region, rv3d, mpoint)
			mvec.length = 10000
			m3d = bpy_extras.view3d_utils.region_2d_to_location_3d(self.region, rv3d, mpoint, eye)
			start = (m3d - self.selobj.location) * self.matrix.inverted()
			end = ((m3d + mvec) - self.selobj.location) * self.matrix.inverted()
			bpy.ops.object.editmode_toggle()
			hit = self.selobj.ray_cast(start, end)
			bpy.ops.object.editmode_toggle()
			self.bm = bmesh.from_edit_mesh(self.mesh)
			if hit[2] == -1:
				self.doneset = set([])
				return {'RUNNING_MODAL'}
			face = self.bm.faces[hit[2]]

			self.doneset = set([])
			self.state = self.SelectMode
			if 'VERT' in self.bm.select_mode:
				startlist = []
				for v in face.verts:
					if v.select == self.state:
						startlist.append(v)
				scanlist = list(startlist)
				self.doneset = set(startlist)
				while len(scanlist) > 0:
					vert = scanlist.pop()
					cands = []
					if self.Diagonal:
						for e in vert.link_edges:
							v = e.other_vert(vert)
							cands.append(v)
					else:
						for f in vert.link_faces:
							cands.extend(list(f.verts))
					for v in cands:
						if not(v in self.doneset) and v.select == self.state:
							self.doneset.add(v)
							scanlist.append(v)
			if 'EDGE' in self.bm.select_mode:
				startlist = []
				for e in face.edges:
					if e.select == self.state:
						startlist.append(e)
				scanlist = list(startlist)
				self.doneset = set(startlist)
				while len(scanlist) > 0:
					edge = scanlist.pop()
					for l in edge.link_loops:
						if l.edge == edge:
							if self.state == False:
								cands = [l.link_loop_prev.edge, l.link_loop_next.edge]
							else:
								cands = l.vert.link_edges
							for e in cands:
								if e!= edge and not(e in self.doneset) and e.select == self.state:
									self.doneset.add(e)
									scanlist.append(e)
			if 'FACE' in self.bm.select_mode:
				if not(face.select == self.state):
					scanlist = []
					self.doneset = set([])
				else:
					scanlist = [face]
					self.doneset = set([face])
				while len(scanlist) > 0:
					face = scanlist.pop()
					cands = []
					if self.Diagonal:
						for e in face.edges:
							for f in e.link_faces:
								cands.append(f)
					else:
						for v in face.verts:
							for f in v.link_faces:
								cands.append(f)
					for f in cands:
						if f != face and not(f in self.doneset) and f.select == self.state:
							self.doneset.add(f)
							scanlist.append(f)
			if self.Preselection:
				for elem in self.doneset:
					elem.select = not(self.state)

			return {'RUNNING_MODAL'}

		return {'RUNNING_MODAL'}


	def initialize(self, context):

		bpy.types.Scene.PreSelOff = bpy.props.BoolProperty(
				name = "PreSelOff",
				description = "Switch off PreSel during FloodSel",
				default = True)

		self.area = context.area
		self.selobj = context.active_object
		self.mesh = self.selobj.data
		self.bm = bmesh.from_edit_mesh(self.mesh)

		self.area.header_text_set(text="FloodSel :  Leftclick selects")

		self.region = None
		self.doneset = set([])

		self.getmatrix()


	def getmatrix(self):

		# Rotating / panning / zooming 3D view is handled here.
		# Calculate matrix.
		if self.selobj.rotation_mode == 'AXIS_ANGLE':
			# object rotationmode axisangle
			ang, x, y, z =	self.selobj.rotation_axis_angle
			self.matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
		elif self.selobj.rotation_mode == 'QUATERNION':
			# object rotationmode quaternion
			w, x, y, z = self.selobj.rotation_quaternion
			x = -x
			y = -y
			z = -z
			quat = Quaternion([w, x, y, z])
			self.matrix = quat.to_matrix()
			self.matrix.resize_4x4()
		else:
			# object rotationmode euler
			ax, ay, az = self.selobj.rotation_euler
			mat_rotX = Matrix.Rotation(-ax, 4, 'X')
			mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
			mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
		if self.selobj.rotation_mode == 'XYZ':
			self.matrix = mat_rotX * mat_rotY * mat_rotZ
		elif self.selobj.rotation_mode == 'XZY':
			self.matrix = mat_rotX * mat_rotZ * mat_rotY
		elif self.selobj.rotation_mode == 'YXZ':
			self.matrix = mat_rotY * mat_rotX * mat_rotZ
		elif self.selobj.rotation_mode == 'YZX':
			self.matrix = mat_rotY * mat_rotZ * mat_rotX
		elif self.selobj.rotation_mode == 'ZXY':
			self.matrix = mat_rotZ * mat_rotX * mat_rotY
		elif self.selobj.rotation_mode == 'ZYX':
			self.matrix = mat_rotZ * mat_rotY * mat_rotX

		# handle object scaling
		sx, sy, sz = self.selobj.scale
		mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
		mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
		mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
		self.matrix = mat_scX * mat_scY * mat_scZ * self.matrix



def panel_func(self, context):

	self.layout.label(text="FloodSel:")
	self.layout.operator("mesh.floodsel", text="Flood SelArea")
	if started:
		print ("op")
		self.layout.prop(mainop, "SelectMode")
		self.layout.prop(mainop, "Multiple")
		self.layout.prop(mainop, "Preselection")
		self.layout.prop(mainop, "Diagonal")

def register():
	print ("registered")
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)

if __name__ == "__main__":
	register()





