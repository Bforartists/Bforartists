
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you have Internet access, you can find the license text at
# http://www.gnu.org/licenses/gpl.txt,
# if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

"""
Fills selected border verts/edges area with quads.
Select several neighbouring verts/edges with at least one "border corner" selected.
Invoke addon. (its on the Mesh Tools panel)

If you wish to hotkey Quadder:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.quadder'.
Assign a hotkey.
Save as Default (Optional).
"""

bl_info = {
	"name": "Quadder",
	"author": "Gert De Roost",
	"version": (0, 4, 0),
	"blender": (2, 63, 0),
	"location": "View3D > Tools",
	"description": "Fills selected border verts/edges area with quads",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}


import bpy
import bmesh


class Quadder(bpy.types.Operator):
	bl_idname = "mesh.quadder"
	bl_label = "Quadder"
	bl_description = "Fills selected border verts/edges area with quads"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		self.do_quadder()

		return {'FINISHED'}



	def do_quadder(self):

		selobj = bpy.context.active_object
		mesh = selobj.data
		self.bm = bmesh.from_edit_mesh(mesh)

		smoothlist = []
		for v in self.bm.verts:
			if v.select:
				smoothlist.append(v)
		self.ecnt = 0
		for e in self.bm.edges:
			if e.select:
				self.ecnt += 1

		vertlist = []
		templist = []
		verts = self.findcorner()
		while verts:
			if len(verts) == 5 or len(verts) == 3:
				off1 = verts[0].co - verts[1].co
				off2 = verts[2].co - verts[1].co
				newco = verts[1].co + off1 + off2
				v = self.bm.verts.new(newco)
			elif len(verts) == 4:
				v = verts[3]
			self.bm.faces.new((verts[0], verts[1], verts[2], v))
			v.select = True
			templist.append(v)
			verts[1].select = False
			vertlist.append(verts[1])
			mesh.update()
			verts = self.findcorner()
			if self.ecnt == 2:
				verts = None

		for v in vertlist:
			v.select = True
		for v in smoothlist:
			v.select = False
		for v in self.bm.verts:
			if len(v.link_faces) <= 2:
				v.select = False
		bpy.ops.mesh.vertices_smooth(repeat = 4)
		bpy.ops.mesh.select_all(action = 'SELECT')
		self.bm.normal_update()
		bpy.ops.mesh.normals_make_consistent()
		for v in smoothlist:
			v.select = True
		for v in templist:
			v.select = True
		for v in vertlist:
			v.select = True
		bpy.ops.mesh.select_all(action = 'DESELECT')

		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()
		self.bm.free()


	def findcorner(self):

		if self.ecnt == 2:
			for v in self.bm.verts:
				if v.select:
					vlist = []
					for e in v.link_edges:
						if e.other_vert(v).select:
							vlist.append(e.other_vert(v))
					if len(vlist) == 2:
						return [vlist[0], v, vlist[1]]
		for v1 in self.bm.verts:
			if v1.select:
				if len(v1.link_edges) == 2:
					e1 = v1.link_edges[0]
					e2 = v1.link_edges[1]
					if len(e1.link_faces) == 0 and len(e2.link_faces) == 0:
						v2 = e1.other_vert(v1)
						v3 = e2.other_vert(v1)
						if len(v2.link_edges) == 1 and len(v3.link_edges) == 1:
							return [v2, v1, v3]
					continue
				elif len(v1.link_edges) > 2:
					slist = []
					fou = False
					for e1 in v1.link_edges:
						if e1.other_vert(v1).select:
							if len(e1.link_faces) == 0:
								for e2 in v1.link_edges:
									if e2.other_vert(v1).select and e1 != e2:
										if len(v1.link_edges) > 3:
											fou = True
											break
								if fou:
									v2 = e1.other_vert(v1)
									v3 = e2.other_vert(v1)
									return [v2, v1, v3]

				linkedges = []
				linkverts = []
				for e1 in v1.link_edges:
					if len(v1.link_edges) > 3:
						if e1.other_vert(v1).select:
							linkverts.append(e1.other_vert(v1))
							linkedges.append(e1)
				if len(linkedges) == 2:
					found1 = True
					if len(linkedges[0].link_faces) != 2 and len(linkedges[1].link_faces) != 2:
						f1 = linkedges[0].link_faces[0]
						f2 = linkedges[1].link_faces[0]
						if f1 == f2:
							found1 = False
						for e2 in f1.edges:
							if e2 in f2.edges:
								found1 = False
								break
						if found1:
							for e3 in linkverts[0].link_edges:
								if len(e3.link_faces) == 1:
									for v3 in e3.verts:
										if v3 != linkverts[0] and v3 != v1:
											if v3.select:
												found2 = True
												f3 = e3.link_faces[0]
												f4 = linkedges[0].link_faces[0]
												if f3 == f4:
													found2 = False
												for e4 in f3.edges:
													if e4 in f4.edges:
														found2 = False
														break
												if found2:
													return [linkverts[0], v1, linkverts[1], v3]
							for e3 in linkverts[1].link_edges:
								if len(e3.link_faces) == 1:
									for v3 in e3.verts:
										if v3 != linkverts[1] and v3 != v1:
											if v3.select:
												found2 = True
												f3 = e3.link_faces[0]
												f4 = linkedges[1].link_faces[0]
												if f3 == f4:
													found2 = False
												for e4 in f3.edges:
													if e4 in f4.edges:
														found2 = False
														break
												if found2:
													return [linkverts[0], v1, linkverts[1], v3]
							return [linkverts[0], v1, linkverts[1], f1, f2]
		return False




def panel_func(self, context):
	self.layout.label(text="Quadder:")
	self.layout.operator("mesh.quadder", text="Fill quads")

def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()





