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
This addon implements a subdivision scheme called deathguppie.
It is ideal for creating more detail locally when sculpting.


Documentation

First go to User Preferences->Addons and enable the DeathGuppie addon in the Mesh category.
Go to EditMode, select some elements and invoke the addon (button in the Mesh Tool panel).
The selected area will be subdivided according to the deathguppie algorithm.
Subdivision is destructive so this is no modifier but a mesh operation.
Selected area after operation allows for further sudividing the area.
The smooth tickbox chooses between smooth and non-smooth subdivision.
The Select inner only tickbox sets what is left selected after operation, only inner faces or everything.

BEWARE - deathguppie will only subdivide grids of quads!

If you wish to hotkey DeathGuppie:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.deathguppie'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "DeathGuppie",
	"author": "Gert De Roost",
	"version": (0, 3, 0),
	"blender": (2, 63, 0),
	"location": "View3D > Tools",
	"description": "Deathguppie subdivision operation",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bmesh


bpy.types.Scene.Smooth = bpy.props.BoolProperty(
		name = "Smoothing",
		description = "Subdivide smooth",
		default = True)

bpy.types.Scene.Inner = bpy.props.BoolProperty(
		name = "Select inner only",
		description = "After operation only inner verts selected",
		default = True)


class DeathGuppie(bpy.types.Operator):
	bl_idname = "mesh.deathguppie"
	bl_label = "DeathGuppie"
	bl_description = "Deathguppie subdivision operation"
	bl_options = {'REGISTER', 'UNDO'}


	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		self.do_deathguppie(context)

		return {'FINISHED'}


	def do_deathguppie(self, context):

		scn = context.scene
		selobj = context.active_object

		bpy.ops.object.editmode_toggle()
		bpy.ops.object.duplicate()
		projobj = bpy.context.active_object
		bpy.ops.object.editmode_toggle()
		bpy.ops.mesh.subdivide(number_cuts=5, smoothness=1.0)
		bpy.ops.object.editmode_toggle()
		projobj.hide = 1
		context.scene.objects.active = selobj
		bpy.ops.object.editmode_toggle()

		mesh = selobj.data
		bm = bmesh.from_edit_mesh(mesh)
		bmkeep = bm.copy()

		facelist = []
		for f1 in bm.faces:
			if f1.select:
				linked = []
				for e in f1.edges:
					for f2 in e.link_faces:
						if f2 != f1:
							if f2.select:
								linked.append(f2.index)
								break
				facelist.insert(0, [])
				facelist[0].append(f1)
				facelist[0].append(linked)


		transfer = {}
		holdlist = []
		for [f, linked] in facelist:
			bpy.ops.mesh.select_all(action = 'DESELECT')
			f.select = 1
			transfer[f.calc_center_median()[:]] = [f.index, linked]
			bpy.ops.mesh.split()

		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()
		bm = bmesh.from_edit_mesh(mesh)
		facelist = []
		for f in bm.faces:
			num = 0
			for e in f.edges:
				if len(e.link_faces) == 1:
					num += 1
			if num == 4:
				if f.calc_center_median()[:] in transfer.keys():
					f.select = 1
					facelist.insert(0, [])
					facelist[0].append(f)
					facelist[0].append(transfer[f.calc_center_median()[:]])


		def createinnerlists(f):

			for l in f.loops:
				self.cornerlist.append(l.vert)
				self.vselset.add(l.vert)
				v1 = l.vert
				vnext = l.link_loop_next.vert
				vprev = l.link_loop_prev.vert
				vnextnext = l.link_loop_next.link_loop_next.vert
				vprevprev = l.link_loop_prev.link_loop_prev.vert
				tempco1 = v1.co + (vprev.co - v1.co) / 3
				tempco2 = vnext.co + (vnextnext.co - vnext.co) / 3
				vert = bm.verts.new(tempco1 + ((tempco2 - tempco1) / 3))
				self.innerlist.append(vert)
				self.smoothset.add(vert)

		self.vselset = set([])
		fselset = set([])
		self.smoothset = set([])
		for [f, [foldidx, linked]] in facelist:
			fold = bmkeep.faces[foldidx]
			linked2 = []
			for idx in linked:
				linked2.append(bmkeep.faces[idx])
			self.cornerlist = []
			self.innerlist = []
			if len(linked) == 4:
				createinnerlists(f)
				for e in f.edges:
					ne, vert1 = bmesh.utils.edge_split(e, e.verts[0], 0.66)
					ne, vert2 = bmesh.utils.edge_split(ne, vert1, 0.5)
					self.vselset.add(vert1)
					self.vselset.add(vert2)
					self.smoothset.add(vert1)
					self.smoothset.add(vert2)
				for idx in range(len(self.cornerlist)):
					cv = self.cornerlist[idx]
					for l in f.loops:
						if l.vert == cv:
							fs = bm.faces.new((cv, l.link_loop_next.vert, self.innerlist[idx], l.link_loop_prev.vert))
							fselset.add(fs)
							fs = bm.faces.new((l.link_loop_prev.vert, l.link_loop_prev.link_loop_prev.vert, self.innerlist[idx - 1], self.innerlist[idx]))
							fselset.add(fs)
				fs = bm.faces.new((self.innerlist[0], self.innerlist[1], self.innerlist[2], self.innerlist[3]))
				fselset.add(fs)
				bm.faces.remove(f)
			elif len(linked) == 3:
				fedges = fold.edges[:]
				for e1 in fedges:
					for f1 in e1.link_faces:
						if len(e1.link_faces) == 1 or (f1 != fold and not(f1 in linked2)):
							edge = f.edges[fedges.index(e1)]
				createinnerlists(f)
				for e in f.edges:
					if e != edge:
						ne, vert1 = bmesh.utils.edge_split(e, e.verts[0], 0.66)
						ne, vert2 = bmesh.utils.edge_split(ne, vert1, 0.5)
						self.vselset.add(vert1)
						self.vselset.add(vert2)
						self.smoothset.add(vert1)
						self.smoothset.add(vert2)
				for l in edge.link_loops:
					if l.face == f:
						if l.edge == edge:
							v1 = l.vert
							vnext = l.link_loop_next.vert
							vprev = l.link_loop_prev.vert
							vnextnext = l.link_loop_next.link_loop_next.vert
							vprevprev = l.link_loop_prev.link_loop_prev.vert
							for idx in range(4):
								if self.cornerlist[idx] == v1:
									co1 = self.innerlist[idx].co + ((self.innerlist[idx].co - self.innerlist[idx-1].co) / 2)
									co2 = self.innerlist[idx-3].co + ((self.innerlist[idx-3].co - self.innerlist[idx-2].co) / 2)
									sidev1 = bm.verts.new(co1)
									sidev2 = bm.verts.new(co2)
									fs = bm.faces.new((v1, vnext, sidev2, sidev1))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((v1, sidev1, self.innerlist[idx], vprev))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((sidev2, vnext, vnextnext, self.innerlist[idx-3]))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((sidev1, sidev2, self.innerlist[idx-3], self.innerlist[idx]))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((self.innerlist[idx], self.innerlist[idx-1], vprevprev, vprev))
									fselset.add(fs)
							self.cornerlist[self.cornerlist.index(v1)] = None
							self.cornerlist[self.cornerlist.index(vnext)] = None
							break
				for idx in range(len(self.cornerlist)):
					cv = self.cornerlist[idx]
					if cv != None:
						for l in f.loops:
							if l.vert == cv:
								fs = bm.faces.new((cv, l.link_loop_next.vert, self.innerlist[idx], l.link_loop_prev.vert))
								fselset.add(fs)
								fs = bm.faces.new((l.link_loop_prev.vert, l.link_loop_prev.link_loop_prev.vert, self.innerlist[idx - 1], self.innerlist[idx]))
								fselset.add(fs)
				fs = bm.faces.new((self.innerlist[0], self.innerlist[1], self.innerlist[2], self.innerlist[3]))
				fselset.add(fs)
				bm.faces.remove(f)
				self.smoothset.add(sidev1)
				self.smoothset.add(sidev2)
			elif len(linked) == 2:
				case = 'BRIDGE'
				for vert in linked2[0].verts:
					if vert in linked2[1].verts:
						case = 'CORNER'
						break
				if case == 'CORNER':
					fedges = fold.edges[:]
					edges = []
					for e1 in fedges:
						for f1 in e1.link_faces:
							if len(e1.link_faces) == 1 or (f1 != fold and not(f1 in linked2)):
								edges.append(f.edges[fedges.index(e1)])
					for l in edges[1].link_loops:
						if l.face == f:
							if l.edge == edges[1] and l.link_loop_next.edge == edges[0]:
								edges.reverse()
								break
					createinnerlists(f)
					for e in f.edges:
						if not(e in edges):
							ne, vert1 = bmesh.utils.edge_split(e, e.verts[0], 0.66)
							ne, vert2 = bmesh.utils.edge_split(ne, vert1, 0.5)
							self.vselset.add(vert1)
							self.vselset.add(vert2)
							self.smoothset.add(vert1)
							self.smoothset.add(vert2)
					for l in edges[0].link_loops:
						if l.face == f:
							if l.edge == edges[0]:
								if l.link_loop_next.edge == edges[1]:
									v1 = l.vert
									vnext = l.link_loop_next.vert
									vprev = l.link_loop_prev.vert
									vnextnext = l.link_loop_next.link_loop_next.vert
									vnnn = l.link_loop_next.link_loop_next.link_loop_next.vert
									vprevprev = l.link_loop_prev.link_loop_prev.vert
									vppp = l.link_loop_prev.link_loop_prev.link_loop_prev.vert
									vpppp = l.link_loop_prev.link_loop_prev.link_loop_prev.link_loop_prev.vert
									for idx in range(4):
										if self.cornerlist[idx] == v1:
											delta1 = (self.innerlist[idx].co - self.innerlist[idx-1].co) / 2
											co1 = self.innerlist[idx].co + delta1
											delta2 = (self.innerlist[idx-3].co - self.innerlist[idx].co) / 2
											delta3 = (self.innerlist[idx-3].co - self.innerlist[idx-2].co) / 2
											co2 = self.innerlist[idx-3].co + delta1 + delta2
											sidev1 = bm.verts.new(co1)
											sidev2 = bm.verts.new(co2)
											sidev3 = bm.verts.new(self.innerlist[idx-2].co + ((self.innerlist[idx-2].co - self.innerlist[idx-1].co) / 2))

											fs = bm.faces.new((v1, vnext, sidev2, sidev1))
											if not(scn.Inner):
												fselset.add(fs)
											fs = bm.faces.new((sidev3, sidev2, vnext, vnextnext))
											if not(scn.Inner):
												fselset.add(fs)
											fs = bm.faces.new((v1, sidev1, self.innerlist[idx], vprev))
											if not(scn.Inner):
												fselset.add(fs)
											fs = bm.faces.new((self.innerlist[idx-2], sidev3, vnextnext, vnnn))
											if not(scn.Inner):
												fselset.add(fs)
											fs = bm.faces.new((sidev1, sidev2, self.innerlist[idx-3], self.innerlist[idx]))
											if not(scn.Inner):
												fselset.add(fs)
											fs = bm.faces.new((sidev2, sidev3, self.innerlist[idx-2], self.innerlist[idx-3]))
											if not(scn.Inner):
												fselset.add(fs)
											fs = bm.faces.new((vprevprev, vprev, self.innerlist[idx], self.innerlist[idx-1]))
											fselset.add(fs)
											fs = bm.faces.new((vpppp, vppp, vprevprev, self.innerlist[idx-1]))
											fselset.add(fs)
											fs = bm.faces.new((vnnn, vpppp, self.innerlist[idx-1], self.innerlist[idx-2]))
											fselset.add(fs)
											break
									break
					fs = bm.faces.new((self.innerlist[0], self.innerlist[1], self.innerlist[2], self.innerlist[3]))
					fselset.add(fs)
					bm.faces.remove(f)
					self.smoothset.add(sidev1)
					self.smoothset.add(sidev2)
					self.smoothset.add(sidev3)
				else:
					fedges = fold.edges[:]
					edges = []
					for e1 in fedges:
						for f1 in e1.link_faces:
							if len(e1.link_faces) == 1 or (f1 != fold and not(f1 in linked2)):
								edges.append(f.edges[fedges.index(e1)])
					createinnerlists(f)
					for e in f.edges:
						if not(e in edges):
							ne, vert1 = bmesh.utils.edge_split(e, e.verts[0], 0.66)
							ne, vert2 = bmesh.utils.edge_split(ne, vert1, 0.5)
							self.vselset.add(vert1)
							self.vselset.add(vert2)
							self.smoothset.add(vert1)
							self.smoothset.add(vert2)
					for l in f.loops:
						if l.edge == edges[0]:
							v1 = l.vert
							vnext = l.link_loop_next.vert
							vprev = l.link_loop_prev.vert
							vnextnext = l.link_loop_next.link_loop_next.vert
							vnnn = l.link_loop_next.link_loop_next.link_loop_next.vert
							vnnnn = l.link_loop_next.link_loop_next.link_loop_next.link_loop_next.vert
							vprevprev = l.link_loop_prev.link_loop_prev.vert
							vppp = l.link_loop_prev.link_loop_prev.link_loop_prev.vert
							vpppp = l.link_loop_prev.link_loop_prev.link_loop_prev.link_loop_prev.vert
							for idx in range(4):
								if self.cornerlist[idx] == v1:
									delta1 = (self.innerlist[idx].co - self.innerlist[idx-1].co) / 2
									co1 = self.innerlist[idx].co + delta1
									sidev1 = bm.verts.new(co1)
									delta2 = (self.innerlist[idx-3].co - self.innerlist[idx-2].co) / 2
									co2 = self.innerlist[idx-3].co + delta2
									sidev2 = bm.verts.new(co2)
									delta3 = (self.innerlist[idx-2].co - self.innerlist[idx-3].co) / 2
									co3 = self.innerlist[idx-2].co + delta3
									sidev3 = bm.verts.new(co3)
									delta4 = (self.innerlist[idx-1].co - self.innerlist[idx].co) / 2
									co4 = self.innerlist[idx-1].co + delta4
									sidev4 = bm.verts.new(co4)
									fs = bm.faces.new((v1, vnext, sidev2, sidev1))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((v1, sidev1, self.innerlist[idx], vprev))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((vnext, vnextnext, self.innerlist[idx-3], sidev2))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((sidev1, sidev2, self.innerlist[idx-3], self.innerlist[idx]))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((vppp, sidev4, sidev3, vnnnn))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((vppp, vprevprev, self.innerlist[idx-1], sidev4))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((sidev3, self.innerlist[idx-2], vnnn, vnnnn))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((sidev3, sidev4, self.innerlist[idx-1], self.innerlist[idx-2]))
									if not(scn.Inner):
										fselset.add(fs)
									fs = bm.faces.new((vprevprev, vprev, self.innerlist[idx], self.innerlist[idx-1]))
									fselset.add(fs)
									fs = bm.faces.new((vnextnext, vnnn, self.innerlist[idx-2], self.innerlist[idx-3]))
									fselset.add(fs)

					fs = bm.faces.new((self.innerlist[0], self.innerlist[1], self.innerlist[2], self.innerlist[3]))
					fselset.add(fs)
					bm.faces.remove(f)
					self.smoothset.add(sidev1)
					self.smoothset.add(sidev2)
					self.smoothset.add(sidev3)
					self.smoothset.add(sidev4)


			elif len(linked) == 1:
				fedges = fold.edges[:]
				edges = []
				for e1 in fedges:
					for f1 in e1.link_faces:
						if len(e1.link_faces) == 1 or (f1 != fold and not(f1 in linked2)):
							edges.append(f.edges[fedges.index(e1)])
				for l in f.loops:
					if not(l.edge in edges):
						edges = [l.link_loop_next.edge, l.link_loop_next.link_loop_next.edge, l.link_loop_next.link_loop_next.link_loop_next.edge]
				createinnerlists(f)
				for e in f.edges:
					if not(e in edges):
						ne, vert1 = bmesh.utils.edge_split(e, e.verts[0], 0.66)
						ne, vert2 = bmesh.utils.edge_split(ne, vert1, 0.5)
						self.vselset.add(vert1)
						self.vselset.add(vert2)
						self.smoothset.add(vert1)
						self.smoothset.add(vert2)
				for l in f.loops:
					if l.edge == edges[0]:
						v1 = l.vert
						vnext = l.link_loop_next.vert
						vprev = l.link_loop_prev.vert
						vnextnext = l.link_loop_next.link_loop_next.vert
						vnnn = l.link_loop_next.link_loop_next.link_loop_next.vert
						vprevprev = l.link_loop_prev.link_loop_prev.vert
						vppp = l.link_loop_prev.link_loop_prev.link_loop_prev.vert
						vpppp = l.link_loop_prev.link_loop_prev.link_loop_prev.link_loop_prev.vert
						for idx in range(4):
							if self.cornerlist[idx] == v1:
								delta1 = (self.innerlist[idx].co - self.innerlist[idx-1].co) / 2
								co1 = self.innerlist[idx].co + delta1
								delta2 = (self.innerlist[idx-3].co - self.innerlist[idx].co) / 2
								delta3 = (self.innerlist[idx-3].co - self.innerlist[idx-2].co) / 2
								co2 = self.innerlist[idx-3].co + delta1 + delta2
								sidev1 = bm.verts.new(co1)
								sidev2 = bm.verts.new(co2)
								delta4 = (self.innerlist[idx-2].co - self.innerlist[idx-1].co) / 2
								delta5 = (self.innerlist[idx-2].co - self.innerlist[idx-3].co) / 2
								co3 = self.innerlist[idx-2].co + delta4 + delta5
								sidev3 = bm.verts.new(co3)
								delta6 = (self.innerlist[idx-1].co - self.innerlist[idx].co) / 2
								co4 = self.innerlist[idx-1].co + delta6
								sidev4 = bm.verts.new(co4)
								fs = bm.faces.new((v1, vnext, sidev2, sidev1))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((sidev3, sidev2, vnext, vnextnext))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((v1, sidev1, self.innerlist[idx], vprev))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((sidev1, sidev2, self.innerlist[idx-3], self.innerlist[idx]))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((sidev2, sidev3, self.innerlist[idx-2], self.innerlist[idx-3]))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((sidev4, sidev3, vnextnext, vppp))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((self.innerlist[idx-2], self.innerlist[idx-1], sidev4, sidev3))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((vprevprev, vppp, sidev4, self.innerlist[idx-1]))
								if not(scn.Inner):
									fselset.add(fs)
								fs = bm.faces.new((vprev, vprevprev, self.innerlist[idx-1], self.innerlist[idx]))
								fselset.add(fs)
				fs = bm.faces.new((self.innerlist[0], self.innerlist[1], self.innerlist[2], self.innerlist[3]))
				fselset.add(fs)
				bm.faces.remove(f)
				self.smoothset.add(sidev1)
				self.smoothset.add(sidev2)
				self.smoothset.add(sidev3)
				self.smoothset.add(sidev4)

			elif len(linked) == 0:
				createinnerlists(f)
				l = f.loops[0]
				v1 = l.vert
				vnext = l.link_loop_next.vert
				vprev = l.link_loop_prev.vert
				vnextnext = l.link_loop_next.link_loop_next.vert
				for idx in range(4):
					if self.cornerlist[idx] == v1:
						sidev1 = bm.verts.new((self.cornerlist[idx].co + self.innerlist[idx].co) / 2)
						sidev2 = bm.verts.new((self.cornerlist[idx-3].co + self.innerlist[idx-3].co) / 2)
						sidev3 = bm.verts.new((self.cornerlist[idx-2].co + self.innerlist[idx-2].co) / 2)
						sidev4 = bm.verts.new((self.cornerlist[idx-1].co + self.innerlist[idx-1].co) / 2)
						fs = bm.faces.new((v1, vnext, sidev2, sidev1))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev3, sidev2, vnext, vnextnext))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev4, sidev3, vnextnext, vprev))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev1, sidev4, vprev, v1))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev1, sidev2, self.innerlist[idx-3], self.innerlist[idx]))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev2, sidev3, self.innerlist[idx-2], self.innerlist[idx-3]))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev3, sidev4, self.innerlist[idx-1], self.innerlist[idx-2]))
						if not(scn.Inner):
							fselset.add(fs)
						fs = bm.faces.new((sidev4, sidev1, self.innerlist[idx], self.innerlist[idx-1]))
						if not(scn.Inner):
							fselset.add(fs)
				fs = bm.faces.new((self.innerlist[0], self.innerlist[1], self.innerlist[2], self.innerlist[3]))
				fselset.add(fs)
				bm.faces.remove(f)
				self.smoothset.add(sidev1)
				self.smoothset.add(sidev2)
				self.smoothset.add(sidev3)
				self.smoothset.add(sidev4)


		if scn.Smooth:
			for v in self.smoothset:
				v.co = projobj.closest_point_on_mesh(v.co)[0]

		bpy.ops.mesh.select_all(action ='SELECT')
		bm.normal_update()
		bpy.ops.mesh.normals_make_consistent()
		bpy.ops.mesh.select_all(action = 'DESELECT')
		for f in fselset:
			f.select = 1
			for e in f.edges:
				e.select = 1
			for v in f.verts:
				v.select = 1
		for e in bm.edges:
			if len(e.link_faces) == 1:
				e.verts[0].select = 1
				e.verts[1].select = 1
		bpy.ops.mesh.remove_doubles()
		for e in bm.edges:
			if len(e.link_faces) == 1:
				e.verts[0].select = 0
				e.verts[1].select = 0
				e.select = 0

		mesh.update()
		bm.free()
		bmkeep.free()
		bpy.ops.object.editmode_toggle()
		bpy.ops.object.select_all(action = 'DESELECT')
		context.scene.objects.active = projobj
		projobj.hide = 0
		bpy.ops.object.delete()
		selobj.select = 1
		context.scene.objects.active = selobj
		bpy.ops.object.editmode_toggle()





def panel_func(self, context):

	scn = bpy.context.scene
	self.layout.label(text="DeathGuppie:")
	self.layout.operator("mesh.deathguppie", text="Subdivide DG")
	self.layout.prop(scn, "Smooth")
	self.layout.prop(scn, "Inner")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()





