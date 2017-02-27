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
This addon implements a smoothing algorithm for meshes based on Laplacian relaxation, but adapted
to have no shrinkage.


Documentation

First go to User Preferences->Addons and enable the Heal addon in the Mesh category.

If you wish to hotkey Heal:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.heal'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "Heal",
	"author": "Gert De Roost",
	"version": (1, 0, 0),
	"blender": (2, 70, 0),
	"location": "View3D > Tools",
	"description": "Smoothing mesh keeping volume",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bmesh
from mathutils import *
import math


class Heal(bpy.types.Operator):
	bl_idname = "mesh.heal"
	bl_label = "Heal"
	bl_description = "Smoothing mesh keeping volume"
	bl_options = {'REGISTER', 'UNDO'}

	Repeat = bpy.props.IntProperty(
		name = "Repeat",
		description = "Repeat Healing operation a certain number of times",
		default = 1,
		min = 1,
		max = 100)


	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		self.dragging = False
		self.region = context.region
		self.selobj = context.active_object
		self.mesh = self.selobj.data
		self.bm = bmesh.from_edit_mesh(self.mesh)
		# smooth #Repeat times
		if self.mode == 0:
			for i in range(self.Repeat):
				self.do_laprelax()
		else:
			self.parents = []
			obj = self.selobj
			while obj.parent:
				self.parents.append(self.getmatrix(obj.parent))
				obj = obj.parent
			self.getmatrix(self.selobj)
			self.halfwidth = self.region.width / 2
			self.halfheight = self.region.height / 2
			for sp in context.area.spaces:
				if sp.type == "VIEW_3D":
					self.perspm = sp.region_3d.perspective_matrix
			copymesh = self.selobj.data.copy()
			self.copyobj = bpy.data.objects.new(name="heal_copy", object_data=copymesh)
			context.scene.objects.link(self.copyobj)
			context.scene.update()
			self.copyobj.hide = 1
					
			context.window_manager.modal_handler_add(self)
			
			return {'RUNNING_MODAL'}

		return {'FINISHED'}

	def modal(self, context, event):
		self.mx = event.mouse_region_x
		self.my = event.mouse_region_y
		
		if event.type == 'LEFTMOUSE':
			if event.value == 'PRESS':
				self.dragging = True
			elif event.value == 'RELEASE':
				if self.copyobj in list(scn.objects):
					context.scene.objects.unlink(self.copyobj)
					context.scene.update()
					bpy.data.objects.remove(self.copyobj)
				return {'FINISHED'}
				
		if event.type == 'MOUSEMOVE' and self.dragging:
			self.calccircle(context)
			for v in self.bm.verts:
				if v in self.circlelist:
					v.select = True
				else:
					v.select = False
			self.mesh.update()
				
		if event.type in ["WHEELDOWNMOUSE"]:
			if circle:
				if not(event.ctrl) and not(event.shift) and event.alt:
					Heal.radius += Heal.radius / 20
					if region:
						region.tag_redraw()
					return {'RUNNING_MODAL'}
				
		if event.type in ["WHEELUPMOUSE"]:
			if circle:
				if not(event.ctrl) and not(event.shift) and event.alt:
					Heal.radius -= Heal.radius / 20
					if region:
						region.tag_redraw()
					return {'RUNNING_MODAL'}
				
		return {'RUNNING_MODAL'}



	def do_laprelax(self):

		bmprev = self.bm.copy()

		for v in bmprev.verts:
			if v.select and len(v.link_edges) != 0:
				tot = Vector((0, 0, 0))
				cnt = 0
				for e in v.link_edges:
					for f in e.link_faces:
						if not(f.select):
							cnt = 1
					if len(e.link_faces) == 1:
						cnt = 1
						break
				if cnt:
					# dont affect border edges: they cause shrinkage
					continue

				# find Laplacian mean
				for e in v.link_edges:
					tot += e.other_vert(v).co
				tot /= len(v.link_edges)

				# cancel movement in direction of vertex normal
				delta = (tot - v.co)
				if delta.length != 0:
					ang = delta.angle(v.normal)
					deltanor = math.cos(ang) * delta.length
					nor = v.normal
					nor.length = abs(deltanor)
					self.bm.verts[v.index].co = tot + nor


		self.mesh.update()
		self.bm.free()
		bmprev.free()
#		bpy.ops.object.editmode_toggle()
#		bpy.ops.object.editmode_toggle()



	def calccircle(self, context):
		self.selobj = context.active_object
		self.region = context.region
		rv3d = spaces[regions.index(self.region)].region_3d
		eyevec = Vector(rv3d.view_matrix[2][:3])
		eyevec.length = 100000 
		eyeloc = Vector(rv3d.view_matrix.inverted().col[3][:3])
		eyeloc = (eyeloc - self.selobj.location) * matrix.inverted()
		
		r2 = Heal.radius
		xl = self.mx - r2
		xr = self.mx + r2
		yt = self.my + r2
		yb = self.my - r2
		
		self.copyobj.hide = 0
	
		def docircle(dictio):
		
			self.incircle = []
			for k, value in dictio.items():
				if len(value) == 4:
					if self.getscreencoords(k.verts[0].co)[2] or self.getscreencoords(k.verts[1].co)[2]:
						continue
					x1, y1, x2, y2 = value
					if x1 < xl and x2 < xl:
						continue
					if x1 > xr and x2 > xr:
						continue
					if y1 < yb and y2 < yb:
						continue
					if y1 > yt and y2 > yt:
						continue
					if math.sqrt((x1 - self.mx)**2 + (y1 - self.my)**2) <= Heal.radius:
						self.incircle.append(k)
					elif math.sqrt((x2 - self.mx)**2 + (y2 - self.my)**2) <= Heal.radius:
						self.incircle.append(k)
					else:
						v1 = Vector((x1, y1))
						v2 = Vector((x2, y2))
						m = Vector((self.mx, self.my))
						d = v2 - v1
						f = v1 - m
						a = d.dot(d)
						if (a == 0):
							a = 0.00001
						b = 2*f.dot(d)
						c = f.dot(f) - Heal.radius*Heal.radius
						discriminant = b*b - 4*a*c
						if discriminant >= 0:
							discriminant = math.sqrt(discriminant)
							t1 = (-b - discriminant)/(2*a)
							t2 = (-b + discriminant)/(2*a)
							if t1 >= 0 and t1 <= 1:
								self.incircle.append(k)
							elif t2 >= 0 and t2 <= 1:
								self.incircle.append(k)
						
				else:
					x1, y1 = value
					if x1 < xl:
						continue
					if x1 > xr:
						continue
					if y1 < yb:
						continue
					if y1 > yt:
						continue
					if math.sqrt((x1 - self.mx)**2 + (y1 - self.my)**2) <= Heal.radius:
						self.incircle.append(k)
	
	
			def oneside(k):
			
				def raycast(elem, locco = None, vno = None):
					if not(vno):
						vno = elem.normal
					vno.length = 0.01
					if not(locco):
						locco = elem.co
					vco = locco + vno
					if rv3d.is_perspective:
						hitnr = 0
						hit = self.copyobj.ray_cast(vco, eyeloc)
						if not(hit[2] == -1):
							vno = -vno
							vco = locco + vno
							hit = self.copyobj.ray_cast(vco, eyeloc)
							if hit[2] == -1:
								hitnr = 2
						else:
							hitnr = 1
						return hit, hitnr, eyeloc - vco
					else:
						end = ((vco * matrix) + eyevec) * matrix.inverted()
						hitnr = 0
						hit = self.copyobj.ray_cast(vco, end)
						if not(hit[2] == -1):
							vno = -vno
							vco = locco + vno
							hit = self.copyobj.ray_cast(vco, end)
							if hit[2] == -1:
								hitnr = 2
						else:
							hitnr = 1
						return hit, hitnr, end
					
				if isinstance(k, bmesh.types.BMEdge):
					hit1, hitnr, direc = raycast(k.verts[0])
					hit2, hitnr, direc = raycast(k.verts[1])
					if not(hit1[2] == -1) or not(hit2[2] == -1):
						return
				elif isinstance(k, bmesh.types.BMFace):
					found = 0
					hit, hitnr, direc = raycast(k, k.calc_center_median(), k.normal)
					if hitnr == 0:
						return
					if hitnr == 1:
						if direc.length == 0 or k.normal.length == 0:
							return
						if math.degrees(k.normal.angle(direc)) > 90:
							return
					else:
						if direc.length == 0 or k.normal.length == 0:
							return
						if math.degrees((-1*k.normal).angle(direc)) > 90:
							return
				else:
					hit, hitnr, direc = raycast(k)
					if not(hit[2] == -1):
						return
				self.circlelist.append(k)
		
		
			self.circlelist = self.incircle[:]
					
		self.copyobj.hide = 1



	def getscreencoords(self, vector):
		# calculate screencoords of given Vector
		vector = vector * matrix
		for m in parents:
			vector = vector * m
		vector = vector + self.selobj.matrix_world.to_translation()
		prj = perspm * vector.to_4d()
		clip = 0
		if abs(prj.z) > prj.w:
			clip = 1
		
		return (Vector((halfwidth + halfwidth * (prj.x / prj.w), halfheight + halfheight * (prj.y / prj.w))), clip)
		
	def getmatrix(self, obj):
	
		# Calculate matrix.
		if obj.rotation_mode == "AXIS_ANGLE":
			# object rotationmode axisangle
			ang, x, y, z =	obj.rotation_axis_angle
			mat = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
		elif obj.rotation_mode == "QUATERNION":
			# object rotationmode quaternion
			w, x, y, z = obj.rotation_quaternion
			x = -x						
			y = -y
			z = -z
			quat = Quaternion([w, x, y, z])
			mat = quat.to_matrix()
			mat.resize_4x4()
		else:
			# object rotationmode euler
			ax, ay, az = obj.rotation_euler
			mat_rotX = Matrix.Rotation(-ax, 4, 'X')
			mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
			mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
		if obj.rotation_mode == "XYZ":
			mat = mat_rotX * mat_rotY * mat_rotZ
		elif obj.rotation_mode == "XZY":
			mat = mat_rotX * mat_rotZ * mat_rotY
		elif obj.rotation_mode == "YXZ":
			mat = mat_rotY * mat_rotX * mat_rotZ
		elif obj.rotation_mode == "YZX":
			mat = mat_rotY * mat_rotZ * mat_rotX
		elif obj.rotation_mode == "ZXY":
			mat = mat_rotZ * mat_rotX * mat_rotY
		elif obj.rotation_mode == "ZYX":
			mat = mat_rotZ * mat_rotY * mat_rotX
	
		# handle object scaling
		sx, sy, sz = obj.scale
		mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
		mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
		mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
		mat = mat_scX * mat_scY * mat_scZ * mat
		
		return mat




def panel_func(self, context):

	scn = bpy.context.scene
	self.layout.label(text="LapRelax:")
	self.layout.operator("mesh.laprelax", text="Laplace Relax")
	self.layout.prop(scn, "Repeat")


def register():
	bpy.utils.register_module(__name__)
	Heal.radius = 40
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()





