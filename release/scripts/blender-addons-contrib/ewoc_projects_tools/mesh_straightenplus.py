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
This addon enables you to straighten out multiple connected-edge-snakes between their endpoints.


Documentation

First go to User Preferences->Addons and enable the StraightenPlus addon in the Mesh category.
Go to EditMode, select one or more connected-edges-snakes (you can straighten several at the same time).
The vertices will be straightened out between the endpoints.  Choose amount of straightening with slider
or tweak interactively with LEFTMOUSE.
Restrict axis toggle restricts straightening to the view plane.
ENTER  to end operation and keep values, RIGHTMOUSE or ESC to cancel.

If you wish to hotkey StraightenPlus:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.straightenplus'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "StraightenPlus",
	"author": "Gert De Roost",
	"version": (0, 3, 0),
	"blender": (2, 63, 0),
	"location": "View3D > Tools",
	"description": "Straighten connected edges",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bmesh
from mathutils import Vector
import math


started = False


class StraightenPlus(bpy.types.Operator):
	bl_idname = "mesh.straightenplus"
	bl_label = "StraightenPlus"
	bl_description = "Straighten edgeslices"
	bl_options = {'REGISTER', 'UNDO'}

	CancelAxis = bpy.props.BoolProperty(
		name = "Restrict axis",
		description = "Dont straighten along the view axis",
		default = False)

	Percentage = bpy.props.FloatProperty(
		name = "Amount",
		description = "Amount of straightening",
        default = 1,
        min = 0,
        max = 1)


	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		global started, mainop

		started = True

		mainop = self

		bpy.types.Scene.PreSelOff = bpy.props.BoolProperty(
				name = "PreSelOff",
				description = "Switch off PreSel during Straighten operation",
				default = True)

		area = context.area
		area.header_text_set(text="Straighten :  Leftmouse tweaks - Enter confirms - Rightmouse/ESC cancels")

		self.rv3d = context.space_data.region_3d
		self.oldperc = False
		self.tweaking = False
		self.prepare_lists(context)
		result = self.do_straighten()
		if result == False:
			context.area.header_text_set()
			self.bm.free()
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			started = False
			return {'FINISHED'}

		context.window_manager.modal_handler_add(self)

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		global started

		if event.type in {'RIGHTMOUSE', 'ESC'}:
			# cancel operation, reset mesh
			del bpy.types.Scene.PreSelOff
			context.area.header_text_set()
			for vlist in self.vertlist:
				for (v, co) in vlist:
					v.co = co
			self.bm.free()
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			started = False
			return {'CANCELLED'}

		elif event.type in {'MIDDLEMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
			return {'PASS_THROUGH'}

		elif event.type in {'MOUSEMOVE', 'LEFTMOUSE'}:
			mxa = event.mouse_x
			mya = event.mouse_y
			self.region = None
			for a in bpy.context.screen.areas:
				if not(a.type == 'VIEW_3D'):
					continue
				for r in a.regions:
					if not(r.type == 'WINDOW'):
						continue
					if mxa > r.x and mya > r.y and mxa < r.x + r.width and mya < r.y + r.height:
						self.region = r
						break
			if not(self.region) and not(self.tweaking):
				return {'PASS_THROUGH'}

		if event.type == 'LEFTMOUSE':
			if event.value == 'PRESS':
				self.tweaking = True
				self.oldmx = event.mouse_x
			else:
				self.tweaking = False
			return {'RUNNING_MODAL'}

		if self.tweaking and event.type == 'MOUSEMOVE':
			mx = event.mouse_x
			newperc = self.Percentage + (mx - self.oldmx) / 200
			if newperc > 1:
				newperc = 1
			elif newperc < 0:
				newperc = 0
			self.Percentage = newperc
			self.do_straighten()
			self.oldmx = mx
			return {'RUNNING_MODAL'}

		if event.type in {'RET', 'NUMPAD_ENTER'}:
			if not(self.region):
				return {'PASS_THROUGH'}
			context.area.header_text_set()
			# Consolidate changes if ENTER pressed.
			# Free the bmesh.
			del bpy.types.Scene.PreSelOff
			self.bm.free()
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			started = 0
			return {'FINISHED'}

		return {'RUNNING_MODAL'}


	def prepare_lists(self, context):

		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()
		selobj = context.active_object
		self.mesh = selobj.data
		self.bm = bmesh.from_edit_mesh(self.mesh)

		self.selset = set([])
		for edge in self.bm.edges:
			if edge.select:
				self.selset.add(edge)


		def addstart(vert, posn):

			# recursive: adds to initial edgelist at start
			for e in vert.link_edges:
				if e in self.selset:
					self.selset.discard(e)
					v = e.other_vert(vert)
					self.vertlist[posn].insert(0, (v, Vector(v.co[:])))
					addstart(v, posn)
					break

		def addend(vert, posn):

			# recursive: adds to initial edgelist at end
			for e in vert.link_edges:
				if e in self.selset:
					self.selset.discard(e)
					v = e.other_vert(vert)
					self.vertlist[posn].append((v, Vector(v.co[:])))
					addend(v, posn)
					break

		posn = 0
		self.vertlist = []
		while len(self.selset) > 0:
			# initialize next edgesnake
			self.vertlist.append([])
			elem = self.selset.pop()
			vert = elem.verts[0]
			self.selset.add(elem)
			self.vertlist[posn].append((vert, Vector(vert.co[:])))
			# add to start and end of arbitrary start vert
			addstart(vert, posn)
			addend(vert, posn)
			posn += 1



	def do_straighten(self):

		for vlist in self.vertlist:
			vstart = vlist[0][0]
			vend = vlist[len(vlist) - 1][0]
			for (vert, vco) in vlist:
				savco = vco[:]
				# P' = A + {(AB dot AP) / || AB ||^2} AB
				ab = vend.co - vstart.co
				if ab.length == 0:
					return False
				ap = vco - vstart.co
				perpco = vstart.co + ((ab.dot(ap) / (ab.length ** 2)) * ab)
				vert.co = vco + ((perpco - vco) * (self.Percentage))

				if self.CancelAxis:
					# cancel movement in direction perp view
					delta = (vert.co - vco)
					if delta.length != 0:
						eyevec = Vector(self.rv3d.view_matrix[2][:3])
						ang = delta.angle(eyevec)
						deltanor = math.cos(ang) * delta.length
						nor = eyevec
						nor.length = abs(deltanor)
						if deltanor >= 0:
							nor = -1*nor
						vert.co = vert.co + nor

		self.mesh.update()




def panel_func(self, context):

	self.layout.label(text="StraightenPlus:")
	self.layout.operator("mesh.straightenplus", text="Straighten")
	if started:
		self.layout.prop(mainop, "Percentage")
		if mainop.Percentage != mainop.oldperc:
			mainop.do_straighten()
			mainop.oldperc = mainop.Percentage
		self.layout.prop(mainop, "CancelAxis")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)

if __name__ == "__main__":
	register()






