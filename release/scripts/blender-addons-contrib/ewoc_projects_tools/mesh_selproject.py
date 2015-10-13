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
The SelProject addon enables you to "project" an object onto another object, every vertex inside the
projection's shape will be selected.


Documentation

First go to User Preferences->Addons and enable the SelProject addon in the Mesh category.
It will appear in the Tools panel.  First set From and To object from the dropdown list.  From object
is the object you project, To object the one you project on.  If switching to editmode first,
the "Use Selection" option appears.  When choosing this you will use a copy of the selected area
instead of a From object.
Press Start SelProject to start the projection.  When in Use Selection mode, the object selected from
will be temporarily hidden for the duration of the operation.  You can use manipulator and
G, R and S (and XYZ) hotkeys as usual to transform both objects.  Also there is the direction Empty
which is used in combination with the origin of the From object (which will be temporarily set to
object geometry median) to set the projection direction.
Press ENTER to finalize the selection projection operation.
"""


bl_info = {
	"name": "SelProject",
	"author": "Gert De Roost",
	"version": (0, 3, 0),
	"blender": (2, 63, 0),
	"location": "View3D > Tools",
	"description": "Use object projection as selection tool.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bpy_extras
import bmesh
from bgl import glColor3f, glBegin, GL_QUADS, glVertex2f, glEnd
from mathutils import Vector, Matrix
import math
from bpy.app.handlers import persistent


started = False
oldobjs = []



bpy.types.Scene.UseSel = bpy.props.BoolProperty(
		name = "Use Selection",
		description = "Use selected area as From object",
		default = False)

bpy.types.Scene.FromObject = bpy.props.EnumProperty(
		items = [("Empty", "Empty", "Empty")],
		name = "From",
		description = "Object to project",
		default = "Empty")

bpy.types.Scene.ToObject = bpy.props.EnumProperty(
		items = [("Empty", "Empty", "Empty")],
		name = "To",
		description = "Object to project onto")





class SelProject(bpy.types.Operator):
	bl_idname = "mesh.selproject"
	bl_label = "SelProject"
	bl_description = "Use object projection as selection tool"
	bl_options = {'REGISTER', 'UNDO'}

	def invoke(self, context, event):

		global started

		started = True

		self.area = context.area
		self.area.header_text_set(text="SelProject :  Enter to confirm - ESC to exit")

		self.init_selproject(context)

		context.window_manager.modal_handler_add(self)

		self._handle = bpy.types.SpaceView3D.draw_handler_add(self.redraw, (), 'WINDOW', 'POST_PIXEL')

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		global started

		if event.type in {'RET', 'NUMPAD_ENTER'}:
			self.area.header_text_set()
			if self.obhide != None:
				bpy.ops.object.select_all(action = 'DESELECT')
				self.obF.select = True
				bpy.context.scene.objects.active = self.obF
				bpy.ops.object.delete()
				self.obhide.hide = False
			bpy.ops.object.select_all(action = 'DESELECT')
			self.empt.select = True
			bpy.context.scene.objects.active = self.empt
			bpy.ops.object.delete()
			self.obT.select = True
			bpy.context.scene.objects.active = self.obT
			started = False
			for v in self.vsellist:
				v.select = True
			for e in self.esellist:
				e.select = True
			for f in self.fsellist:
				f.select = True
			self.obF.location = self.originobF
			self.obT.location = self.originobT
			self.bmT.select_flush(1)
			self.bmT.to_mesh(self.meT)
			self.meT.update()
			self.bmF.free()
			self.bmT.free()
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
			bpy.ops.object.editmode_toggle()
			return {'FINISHED'}

		elif event.type == 'ESC':
			self.area.header_text_set()
			if self.obhide != None:
				bpy.ops.object.select_all(action = 'DESELECT')
				self.obF.select = True
				bpy.context.scene.objects.active = self.obF
				bpy.ops.object.delete()
				self.obhide.hide = False
			bpy.ops.object.select_all(action = 'DESELECT')
			self.empt.select = True
			bpy.context.scene.objects.active = self.empt
			bpy.ops.object.delete()
			started = False
			self.obF.location = self.originobF
			self.obT.location = self.originobT
			self.bmF.free()
			self.bmT.free()
			for obj in self.oldobjlist:
				obj.select = True
			self.scn.objects.active = self.oldobj
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
			if self.oldmode == 'EDIT':
				bpy.ops.object.editmode_toggle()
			return {'CANCELLED'}

		elif event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE', 'G', 'S', 'R', 'X', 'Y', 'Z', 'MOUSEMOVE'}:
			context.region.tag_redraw()
			return {'PASS_THROUGH'}

		return {'RUNNING_MODAL'}


	def getmatrix(self, selobj):

		# Rotating / panning / zooming 3D view is handled here.
		# Creates a matrix.
		if selobj.rotation_mode == 'AXIS_ANGLE':
			# object rotation_quaternionmode axisangle
			ang, x, y, z =  selobj.rotation_axis_angle
			matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
		elif selobj.rotation_mode == 'QUATERNION':
			# object rotation_quaternionmode euler
			w, x, y, z = selobj.rotation_quaternion
			x = -x
			y = -y
			z = -z
			self.quat = Quaternion([w, x, y, z])
			matrix = self.quat.to_matrix()
			matrix.resize_4x4()
		else:
			# object rotation_quaternionmode euler
			ax, ay, az = selobj.rotation_euler
			mat_rotX = Matrix.Rotation(-ax, 4, 'X')
			mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
			mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
		if selobj.rotation_mode == 'XYZ':
			matrix = mat_rotX * mat_rotY * mat_rotZ
		elif selobj.rotation_mode == 'XZY':
			matrix = mat_rotX * mat_rotZ * mat_rotY
		elif selobj.rotation_mode == 'YXZ':
			matrix = mat_rotY * mat_rotX * mat_rotZ
		elif selobj.rotation_mode == 'YZX':
			matrix = mat_rotY * mat_rotZ * mat_rotX
		elif selobj.rotation_mode == 'ZXY':
			matrix = mat_rotZ * mat_rotX * mat_rotY
		elif selobj.rotation_mode == 'ZYX':
			matrix = mat_rotZ * mat_rotY * mat_rotX

		# handle object scaling
		sx, sy, sz = selobj.scale
		mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
		mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
		mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
		matrix = mat_scX * mat_scY * mat_scZ * matrix

		return matrix


	def getscreencoords(self, vector):
		# calculate screencoords of given Vector
		vector = vector * self.matrixT
		vector = vector + self.obT.location

		svector = bpy_extras.view3d_utils.location_3d_to_region_2d(self.region, self.rv3d, vector)
		if svector == None:
			return [0, 0]
		else:
			return [svector[0], svector[1]]




	def checksel(self):

		self.selverts = []
		self.matrixT = self.getmatrix(self.obT)
		self.matrixF = self.getmatrix(self.obF).inverted()
		direc1 =  (self.obF.location - self.empt.location) * self.matrixF
		direc2 =  (self.obF.location - self.empt.location) * self.matrixT.inverted()
		direc2.length = 10000
		for v in self.bmT.verts:
			vno1 = v.normal
			vno1.length = 0.0001
			vco1 = v.co + vno1
			hit1 = self.obT.ray_cast(vco1, vco1 + direc2)
			vno2 = -v.normal
			vno2.length = 0.0001
			vco2 = v.co + vno2
			hit2 = self.obT.ray_cast(vco2, vco2 + direc2)
			if hit1[2] == -1 or hit2[2] == -1:
				vco = ((v.co * self.matrixT + self.obT.location) - self.obF.location) * self.matrixF
				hit = self.obF.ray_cast(vco, vco + direc1)
				if hit[2] != -1:
					v.select = True
					self.selverts.append(v)





	def init_selproject(self, context):

		self.obhide = None
		# main operation
		self.scn = context.scene
		self.region = context.region
		self.rv3d = context.space_data.region_3d
		self.oldobjlist = list(self.scn.objects)
		self.oldobj = context.active_object
		self.oldmode = self.oldobj.mode
		mesh = self.oldobj.data

		if self.scn.UseSel and context.mode == 'EDIT_MESH':
			self.obhide = context.active_object
			me = self.obhide.data
			bmundo = bmesh.new()
			bmundo.from_mesh(me)
			objlist = []
			for obj in self.scn.objects:
				objlist.append(obj)
			bpy.ops.mesh.separate(type = 'SELECTED')
			for obj in self.scn.objects:
				if not(obj in objlist):
					self.obF = obj
			bmundo.to_mesh(me)
			bmundo.free()
			self.obhide.hide = True
		else:
			self.obF = bpy.data.objects.get(self.scn.FromObject)
		if context.mode == 'EDIT_MESH':
			bpy.ops.object.editmode_toggle()
		self.obF.select = True
		self.scn.objects.active = self.obF
		self.originobF = self.obF.location
		bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
		self.meF = self.obF.to_mesh(self.scn, 1, 'PREVIEW')
		self.bmF = bmesh.new()
		self.bmF.from_mesh(self.meF)

		self.obT = bpy.data.objects.get(self.scn.ToObject)
		self.obT.select = True
		self.scn.objects.active = self.obT
		self.originobT = self.obT.location
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		self.meT = self.obT.data
		self.bmT = bmesh.new()
		self.bmT.from_mesh(self.meT)

		self.vsellist = []
		for v in self.bmT.verts:
			if v.select:
				self.vsellist.append(v)
		self.esellist = []
		for e in self.bmT.edges:
			if e.select:
				self.esellist.append(e)
		self.fsellist = []
		for f in self.bmT.faces:
			if f.select:
				self.fsellist.append(f)

		bpy.ops.object.add(type='EMPTY', location=(self.obF.location + self.obT.location) / 2)
		self.empt = context.active_object
		self.empt.name = "SelProject_dir_empty"

		self.selverts = []


	def redraw(self):

		if started:
			self.checksel()
			glColor3f(1.0, 1.0, 0)
			for v in self.selverts:
				glBegin(GL_QUADS)
				x, y = self.getscreencoords(v.co)
				glVertex2f(x-2, y-2)
				glVertex2f(x-2, y+2)
				glVertex2f(x+2, y+2)
				glVertex2f(x+2, y-2)
				glEnd()





def panel_func(self, context):

	self.scn = context.scene

	self.layout.label(text="SelProject:")
	if started:
		self.layout.operator("mesh.selproject", text="SelProject")
	else:
		self.layout.operator("mesh.selproject", text="SelProject")
		if context.mode == 'EDIT_MESH':
			self.layout.prop(self.scn, "UseSel")
			if not(self.scn.UseSel):
				self.layout.prop(self.scn, "FromObject")
			else:
				self.scn.FromObject = bpy.context.active_object.name
				context.region.tag_redraw()
		else:
			self.layout.prop(self.scn, "FromObject")
		self.layout.prop(self.scn, "ToObject")




def register():

	bpy.app.handlers.scene_update_post.append(sceneupdate_handler)

	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


def unregister():
	bpy.app.handlers.scene_update_post.remove(sceneupdate_handler)

	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)
	bpy.types.VIEW3D_PT_tools_objectmode.append(panel_func)


if __name__ == "__main__":
	register()






@persistent
def sceneupdate_handler(dummy):

	global oldobjs

	scn = bpy.context.scene

	if not(list(scn.objects) == oldobjs):
		itemlist = []
		objs = list(scn.objects)
		for ob in objs:
			if ob.type == 'MESH':
				itemlist.append((ob.name, ob.name, "Set From:"))
		bpy.types.Scene.FromObject = bpy.props.EnumProperty(
				items = itemlist,
				name = "From",
				description = "Object to project")
		bpy.types.Scene.ToObject = bpy.props.EnumProperty(
				items = itemlist,
				name = "To",
				description = "Object to project onto")
		oldobjs = list(scn.objects)

	return {'RUNNING_MODAL'}




