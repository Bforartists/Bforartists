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
This script uses the concept of support edges, or the inserting of new edges parallel to the selected edges.


Documentation

First go to User Preferences->Addons and enable the ParEdge addon in the Mesh category.
Go to EditMode, select a closed edge path without corners (an edgeloop or part of an edgeloop)and invoke
the addon (button in the Mesh Tool panel).  Enter a distance (positive or negative) with the slider in
the Mesh Tools panel or leftclick-drag from left to right to
interactively choose the parallel distance.  Select "Both Sides" on the panel to insert edges on both sides.
Select "Endpoint quads" if you want to have edgepath endpoints "self.capped".
Press the right mouse button to cancel operation or ENTER to accept changes.
The tool will remember the last set distance and the "Both Sides" setting for the next ParEdge operation.

If you wish to hotkey ParEdge:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'self.mesh.paredge'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "ParEdge",
	"author": "Gert De Roost",
	"version": (0, 5, 3),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Inserting of parallel edges",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bmesh
import math



started = 0



def parchangedef(self, context):

	mainop.adapt(None)



class ParEdge(bpy.types.Operator):
	bl_idname = "mesh.paredge"
	bl_label = "ParEdge"
	bl_description = "Inserting of parallel edges"
	bl_options = {"REGISTER", "UNDO"}


	Distance = bpy.props.FloatProperty(
		name = "Distance",
		description = "Enter distance",
		default = 0,
		min = -1,
		max = 1,
		update = parchangedef)

	Both = bpy.props.BoolProperty(
		name = "Both sides",
		description = "Insert on both sides",
		default = False,
		update = parchangedef)

	Cap = bpy.props.BoolProperty(
		name = "Endpoint quads",
		description = "Create endpoint quads",
		default = False,
		update = parchangedef)


	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		global mainop

		mainop = self

		bpy.types.Scene.PreSelOff = bpy.props.BoolProperty(
				name = "PreSelOff",
				description = "Switch off PreSel during FPS navigation mode",
				default = True)

		self.area = context.area
		self.area.header_text_set(text="ParEdge :  Leftmouse to shift - Enter to confirm - Rightmouse/ESC cancels")

		self.init_paredge(context)

		context.window_manager.modal_handler_add(self)

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		global started

		mxa = event.mouse_x
		mya = event.mouse_y
		self.region = None
		for a in bpy.context.screen.areas:
			if not(a.type == 'VIEW_3D'):
				continue
			for r in a.regions:
				if mxa > r.x and mya > r.y and mxa < r.x + r.width and mya < r.y + r.height:
					if not(r.type == 'WINDOW'):
						self.region = None
						break
					self.region = r

		if event.type in {'RIGHTMOUSE', 'ESC'} or self.wrongsel or self.stop:
			self.area.header_text_set()
			del bpy.types.Scene.PreSelOff
			# right mousebutton cancels
			started = False
			self.bm.free()
			bpy.ops.object.editmode_toggle()
			self.bmundo.to_mesh(self.mesh)
			bpy.ops.object.editmode_toggle()
			return {'CANCELLED'}

		elif event.type == 'LEFTMOUSE':
			if not(self.region):
				# this for splitting up mouse func between panel and 3d view
				return {'PASS_THROUGH'}
			if event.value == 'PRESS':
				self.basex = event.mouse_region_x
				self.basev = self.dist
				self.mbns = 1
			if event.value == 'RELEASE':
				self.mbns = 0
			return {'RUNNING_MODAL'}

		elif event.type in {'MIDDLEMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
			# user transforms view
			return {'PASS_THROUGH'}

		elif event.type in {'RET', 'NUMPAD_ENTER'}:
			self.area.header_text_set()
			del bpy.types.Scene.PreSelOff
			# Consolidate changes if Enter pressed.
			# Free the bmesh.
			if not(self.region):
				return {'PASS_THROUGH'}
			started = False
			bpy.ops.mesh.select_all(action = 'DESELECT')
			for posn in range(len(self.vertlist)):
				if self.capped:
					for e in self.capsellist:
						if e == None:
							continue
						e.select = True
						e.verts[0].select = True
						e.verts[1].select = True
				# select only the inserted verts/edges
				if self.negsubd[posn]:
					for vert in self.dissverts1[posn]:
						vert.select = True
					for edge in self.dissedges1[posn]:
						edge.select = True
				if self.possubd[posn]:
					for vert in self.dissverts2[posn]:
						vert.select = True
					for edge in self.dissedges2[posn]:
						edge.select = True
				# if user resetted to zero: remove inserted edges
				if self.dist == 0:
					if self.negsubd[posn]:
						bpy.ops.mesh.select_all(action = 'DESELECT')
						for vert in self.dissverts1[posn]:
							vert.select = True
						for edge in self.dissedges1[posn]:
							edge.select = True
						bpy.ops.mesh.dissolve_edges(use_verts=True)
						self.mesh.calc_tessface()
						self.negsubd[posn] = False
						self.possubd[posn] = False
					if self.possubd[posn]:
						bpy.ops.mesh.select_all(action = 'DESELECT')
						for vert in self.dissverts2[posn]:
							vert.select = True
						for edge in self.dissedges2[posn]:
							edge.select = True
						bpy.ops.mesh.dissolve_edges(use_verts=True)
						self.mesh.calc_tessface()
						self.negsubd[posn] = False
						self.possubd[posn] = False
					for vert in self.vertlist[posn]:
						vert.select = True
					for edge in self.edgelist[posn]:
						edge.select = True
					self.mesh.update()
			self.bm.free()
			bpy.ops.object.editmode_toggle()
			self.bmundo.free()
			bpy.ops.object.editmode_toggle()
			return {'FINISHED'}

		elif event.type == 'MOUSEMOVE':
			# do some edgecreating
			self.adapt(event)
			return {'PASS_THROUGH'}

		return {'RUNNING_MODAL'}


	def adapt(self, event):

		global started

		def removecaps():
			self.capped = False
			for posn in range(len(self.vertlist)):
				for [e1, e2, v1, v2, fj, fo1, fo2] in self.caplist[posn]:
					if e1 == None:
						continue
					bmesh.utils.face_split(fj, v1, v2)
					templ = []
					for f in e1.link_faces:
						templ.append(f)
					bmesh.utils.face_join(templ)
					templ = []
					for f in e2.link_faces:
						templ.append(f)
					bmesh.utils.face_join(templ)
			self.mesh.calc_tessface()


		if self.mbns == 0:
			if self.Cap != self.oldcap:
				if self.dist != 0:
					self.mbns = 2
				if self.Cap == True:
					self.capped = False
				else:
					removecaps()
				self.oldcap = self.Cap
			if self.Both != self.oldboth:
				if self.dist != 0:
					# enter edge-building through the backdoor to instantaneously show both inserts
					self.mbns = 2
				if self.Both == True:
					# if just set
					for posn in range(len(self.vertlist)):
						if self.negsubd[posn]:
							self.possubd[posn] = False
						if self.possubd[posn]:
							self.negsubd[posn] = False
				else:
					if self.capped:
						self.capped = False
						removecaps()
					# if just unset: remove one side of edges
					if self.dist < 0:
						for posn in range(len(self.vertlist)):
							bpy.ops.mesh.select_all(action = 'DESELECT')
							for vert in self.dissverts2[posn]:
								vert.select = True
							for edge in self.dissedges2[posn]:
								edge.select = True
							bpy.ops.mesh.dissolve_edges(use_verts=True)
							self.mesh.calc_tessface()
							for vert in self.dissverts1[posn]:
								vert.select = True
							for edge in self.dissedges1[posn]:
								edge.select = True
							self.possubd[posn] = False
							self.railedges2[posn] = []
							self.railverts2[posn] = []
							self.dissverts2[posn] = []
							self.dissedges2[posn] = []
					if self.dist >= 0:
						for posn in range(len(self.vertlist)):
							if self.railedges1[posn] != []:
								bpy.ops.mesh.select_all(action = 'DESELECT')
								for vert in self.dissverts1[posn]:
									vert.select = True
								for edge in self.dissedges1[posn]:
									edge.select = True
								bpy.ops.mesh.dissolve_edges(use_verts=True)
								self.mesh.calc_tessface()
								for vert in self.dissverts2[posn]:
									vert.select = True
								for edge in self.dissedges2[posn]:
									edge.select = True
								self.negsubd[posn] = False
								self.railedges1[posn] = []
								self.railverts1[posn] = []
								self.dissverts1[posn] = []
								self.dissedges1[posn] = []
					for vert in self.vertlist[posn]:
						vert.select = True
					for edge in self.edgelist[posn]:
						edge.select = True
			self.oldboth = self.Both
			self.dist = self.Distance
			if self.dist != self.olddist:
				self.mbns = 2
			self.olddist = self.dist
		else:
			if self.mbns != 2:
				if event != None:
					# do mouse handling left-right
					mx = event.mouse_region_x
					mean = max(-1*self.meanmin, self.meanmax)
					self.dist = self.basev + ((mx - self.basex) / 200) * mean
					self.Distance = self.dist
					self.distset = True
			else:
				self.mbns = 0
			# dont do anything if zero - removing edges will be handled once exiting with ENTER
			if self.Distance == 0:
				return
				
			#negative side handling
			if self.dist < 0 or self.Both == True:
				for posn in range(len(self.vertlist)):
					if not(self.negsubd[posn]):
						if self.Both == False:
							# if just switched sides: remove positive side
							if self.possubd[posn] == True:
								bpy.ops.mesh.select_all(action='DESELECT')
								for vert in self.dissverts2[posn]:
									vert.select = True
								for edge in self.dissedges2[posn]:
									edge.select = True
								self.mesh.update()
								bpy.ops.mesh.dissolve_edges(use_verts=True, use_face_split=False)
								self.railedges2[posn] = []
								self.railverts2[posn] = []
								self.dissverts2[posn] = []
								self.dissedges2[posn] = []
								bpy.ops.mesh.select_all(action = 'DESELECT')
							self.possubd[posn] = False
						self.railedges1[posn] = []
						self.railverts1[posn] = []
						self.dissverts1[posn] = []
						self.dissedges1[posn] = []

				for posn in range(len(self.vertlist)):
					if not(self.negsubd[posn]):
						self.negsubd[posn] = True
						# if just switched sides: look for slide constellations
						for i, vert in enumerate(self.vertlist[posn]):
							if i == len(self.vertlist[posn]) - 1:
								break
							for loop in vert.link_loops:
								if loop.link_loop_next.vert == self.vertlist[posn][i + 1]:
									self.railverts1[posn].append(loop.link_loop_prev.vert)
									e = loop.link_loop_prev.edge
									self.railedges1[posn].append(e)
									if self.vertlist[posn].index(vert) == len(self.vertlist[posn]) - 2:
										self.railverts1[posn].append(loop.link_loop_next.link_loop_next.vert)
										e = loop.link_loop_next.edge
										self.railedges1[posn].append(e)
						if self.railedges1[posn] != []:
							# insert parallel edges
							prev = None
							popout = False
							for idx in range(len(self.railedges1[posn])):
								if popout:
									break
								edge = self.railedges1[posn][idx]
								if idx == len(self.railedges1[posn]) - 1 and self.railverts1[posn][0] == self.railverts1[posn][len(self.railverts1[posn]) - 1]:
									# this handles closed edgeloops
									vert = startvert
									self.railedges1[posn].pop(len(self.railedges1[posn]) - 1)
									self.railverts1[posn].pop(len(self.railverts1[posn]) - 1)
									popout = True
								else:
									dummy, vert = bmesh.utils.edge_split(edge, self.vertlist[posn][self.railedges1[posn].index(edge)], 0.5)
								if idx == 0:
									startvert = vert
								self.dissverts1[posn].append(vert)
								if not(prev == None):
									e = bmesh.ops.connect_verts(self.bm, verts=[vert, prev])
									self.dissedges1[posn].append(e['edges'][0])
								prev = vert
							self.mesh.calc_tessface()

				# select inserted edges/verts
				for posn in range(len(self.vertlist)):
					for v in self.dissverts1[posn]:
						v.select = True
					for e in self.dissedges1[posn]:
						e.select = True

			# do distance shifting
			for posn in range(len(self.vertlist)):
				if self.railedges1[posn] != []:
					for v in self.vertlist[posn]:
						pv = self.dissverts1[posn][self.vertlist[posn].index(v)]
						rv = self.railverts1[posn][self.vertlist[posn].index(v)]
						sv = self.bmundo.verts[v.index]
						vec = rv.co - sv.co
						vec.length = abs(self.dist)
						pv.co = sv.co + vec


			#positive side handling
			if self.dist > 0 or self.Both == True:
				for posn in range(len(self.vertlist)):
					if not(self.possubd[posn]):
						if self.Both == False:
							# if just switched sides: remove positive side
							if self.negsubd[posn] == True:
								bpy.ops.mesh.select_all(action = 'DESELECT')
								for vert in self.dissverts1[posn]:
									vert.select = True
								for edge in self.dissedges1[posn]:
									edge.select = True
								bpy.ops.mesh.dissolve_edges(use_verts=True, use_face_split=False)
								self.railedges1[posn] = []
								self.railverts1[posn] = []
								self.dissverts1[posn] = []
								self.dissedges1[posn] = []
								bpy.ops.mesh.select_all(action = 'DESELECT')
							self.negsubd[posn] = False
						self.railedges2[posn] = []
						self.railverts2[posn] = []
						self.dissverts2[posn] = []
						self.dissedges2[posn] = []
				for posn in range(len(self.vertlist)):
					if not(self.possubd[posn]):
						# if just switched sides: look for slide constellations
						for i, vert in enumerate(self.vertlist[posn]):
							if (i == len(self.vertlist[posn]) - 1) or (i > 0 and vert == self.vertlist[posn][0]):
								break
							for loop in vert.link_loops:
								if loop.link_loop_prev.vert == self.vertlist[posn][i + 1]:
									self.railverts2[posn].append(loop.link_loop_next.vert)
									e = loop.edge
									self.railedges2[posn].append(e)
									if self.vertlist[posn].index(vert) == len(self.vertlist[posn]) - 2:
										self.railverts2[posn].append(loop.link_loop_prev.link_loop_prev.vert)
										e = loop.link_loop_prev.link_loop_prev.edge
										self.railedges2[posn].append(e)
				for posn in range(len(self.vertlist)):
					if not(self.possubd[posn]):
						self.possubd[posn] = True
						if self.railedges2[posn] != []:
							# insert parallel edges
							prev = None
							popout = False
							for idx in range(len(self.railedges2[posn])):
								if popout:
									break
								edge = self.railedges2[posn][idx]
								if idx == len(self.railedges2[posn]) - 1 and self.railverts2[posn][0] == self.railverts2[posn][len(self.railverts2[posn]) - 1]:
									# this handles closed edgeloops
									vert = startvert
									self.railedges2[posn].pop(len(self.railedges2[posn]) - 1)
									self.railverts2[posn].pop(len(self.railverts2[posn]) - 1)
									popout = True
								else:
									dummy, vert = bmesh.utils.edge_split(edge, self.vertlist[posn][self.railedges2[posn].index(edge)], 0.5)
								if idx == 0:
									startvert = vert
								self.dissverts2[posn].append(vert)
								if not(prev == None):
									e = bmesh.ops.connect_verts(self.bm, verts=[vert, prev])
									self.dissedges2[posn].append(e['edges'][0])
								prev = vert
								prevedge = edge
							self.mesh.calc_tessface()


				# select inserted edges/verts
				for posn in range(len(self.vertlist)):
					for v in self.dissverts2[posn]:
						v.select = True
					for e in self.dissedges2[posn]:
						e.select = True

			# do distance shifting
			for posn in range(len(self.vertlist)):
				if self.railedges2[posn] != []:
					for v in self.vertlist[posn]:
						pv = self.dissverts2[posn][self.vertlist[posn].index(v)]
						rv = self.railverts2[posn][self.vertlist[posn].index(v)]
						sv = self.bmundo.verts[v.index]
						vec = rv.co - sv.co
						vec.length = abs(self.dist)
						pv.co = sv.co + vec

			# create cap
			if not(self.capped):
				self.capsellist = []
				for posn in range(len(self.vertlist)):
					if self.Both and self.Cap:
						self.capped = True

						def capendpoint(i):
							self.capedges = []
							es1 = None
							es2 = None
							vert = self.vertlist[posn][i]
							for e in vert.link_edges:
								v = e.other_vert(vert)
								if not(v in self.vertlist[posn]) and not(v in self.dissverts1[posn]) and not(v in self.dissverts2[posn]):
									self.capedges.append(e)
							if len(self.capedges) == 1:
								e = self.capedges[0]
								for f in e.link_faces:
									v2 = e.other_vert(vert)
									v2.select = True
									if self.dissverts1[posn][i] in f.verts:
										f1, l1 = bmesh.utils.face_split(f, v2, self.dissverts1[posn][i])
										if e in f.edges:
											fj1 = f
											fo1 = f1
										else:
											fj1 = f1
											fo1 = f
										for es in v2.link_edges:
											if es.other_vert(v2) == self.dissverts1[posn][i]:
												es.select = True
												es1 = es
									elif self.dissverts2[posn][i] in f.verts:
										f2, l1 = bmesh.utils.face_split(f, v2, self.dissverts2[posn][i])
										if e in f.edges:
											fj2 = f
											fo2 = f2
										else:
											fj2 = f2
											fo2 = f
										for es in v2.link_edges:
											if es.other_vert(v2) == self.dissverts2[posn][i]:
												es.select = True
												es2 = es
								f3 = bmesh.utils.face_join((fj1, fj2))
							if es1 == None:
								self.caplist[posn].append((None, None, None, None, None, None, None))
							else:
								self.caplist[posn].append((es1, es2, vert, v2, f3, fo1, fo2))
							self.capsellist.append(es1)
							self.capsellist.append(es2)

						self.caplist[posn] = []
						capendpoint(0)
						capendpoint(-1)
				self.mesh.calc_tessface()

			# select original verts/edges
			for posn in range(len(self.vertlist)):
				for edge in self.edgelist[posn]:
					edge.select = True
				for vert in self.vertlist[posn]:
					vert.select = True

		bmesh.update_edit_mesh(self.mesh, destructive=True)
		self.mesh.update()




	def init_paredge(self, context):

		global started

		self.oldcap = False
		self.capped = False
		self.stop = False
		self.dist = 0
		self.olddist = 0
		self.oldboth = 0
		self.wrongsel = False
		self.mbns = 0
		self.negsubd = []
		self.possubd = []
		self.distset = False
		self.railedges1 = []
		self.railedges2 = []
		self.railverts1 = []
		self.railverts2 = []
		self.dissedges1 = []
		self.dissedges2 = []
		self.dissverts1 = []
		self.dissverts2 = []
		self.caplist = []
		self.singledir = []
		self.firstvert = []

		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()

		bpy.ops.mesh.sort_elements(elements={'VERT'})
		self.region = context.region
		selobj = bpy.context.active_object
		self.mesh = selobj.data
		self.bm = bmesh.from_edit_mesh(self.mesh)
		self.bmundo = self.bm.copy()
		started = True

		self.selset = set([])
		self.edgelist = []
		self.vertlist = []
		for edge in self.bm.edges:
			if edge.select:
				self.selset.add(edge)
		if len(self.selset) <= 1:
			self.wrongsel = True
			return


		# get edge-snakes

		def addstart(vert):

			# recursive: adds to initial edgelist at start
			for e in vert.link_edges:
				if e in self.selset:
					self.selset.discard(e)
					v = e.other_vert(vert)
					self.edgelist[posn].insert(0, e)
					self.vertlist[posn].insert(0, v)
					addstart(v)
					break

		def addend(vert):

			# recursive: adds to initial edgelist at end
			for e in vert.link_edges:
				if e in self.selset:
					self.selset.discard(e)
					v = e.other_vert(vert)
					self.edgelist[posn].append(e)
					self.vertlist[posn].append(v)
					addend(v)
					break

		posn = 0
		while len(self.selset) > 0:
			self.railedges1.append([])
			self.railedges2.append([])
			self.railverts1.append([])
			self.railverts2.append([])
			self.dissedges1.append([])
			self.dissedges2.append([])
			self.dissverts1.append([])
			self.dissverts2.append([])
			self.caplist.append([])
			self.vertlist.append([])
			self.edgelist.append([])
			self.possubd.append(False)
			self.negsubd.append(False)
			self.singledir.append(None)
			self.firstvert.append(None)
			
			elem = self.selset.pop()
			vert = elem.verts[0]
			self.selset.add(elem)
			# add to START and END of arbitrary START vert
			self.vertlist[posn].insert(0, vert)
			addstart(vert)
			addend(vert)
			# add first vert at end when closed loop
			for loop in self.vertlist[posn][0].link_loops:
				if loop.link_loop_prev.vert == self.vertlist[posn][-1]:
					self.vertlist[posn].append(self.vertlist[posn][0])
					self.edgelist[posn].append(self.edgelist[posn][0])
			posn += 1

			
			

		# orient edge and vertlists parallel - reverse if necessary

		self.singledir[0] = self.edgelist[0][0].verts[0]

		e1 = None
		for i in range(len(self.edgelist) - 1):
			bpy.ops.mesh.select_all(action = 'DESELECT')
			# get first vert and edge for two adjacent slices
			for v in self.edgelist[i][0].verts:
				if len(self.edgelist[i]) == 1:
					vt = self.singledir[i]
					vt.select = True
					self.bm.select_history.add(vt)
					v1 = vt
					e1 = self.edgelist[i][0]
					break
				elif not(v in self.edgelist[i][1].verts):
					v.select = True
					self.bm.select_history.add(v)
					v1 = v
					e1 = self.edgelist[i][0]
			for v in self.edgelist[i+1][0].verts:
				if len(self.edgelist[i+1]) == 1:
					v.select = True
					self.bm.select_history.add(v)
					v2 = v
					e2 = self.edgelist[i+1][0]
					break
				elif not(v in self.edgelist[i+1][1].verts):
					v.select = True
					self.bm.select_history.add(v)
					v2 = v
					e2 = self.edgelist[i+1][0]
			self.singledir[i+1] = v2
			self.bm.select_history.validate()
			# get path between startverts for checking orientation
			bpy.ops.mesh.shortest_path_select()

			for e in self.bm.edges:
				if e.verts[0].select and e.verts[1].select:
					e.select = True


			# correct selected path when not connected neatly to vert from left or right(cant know direction)
			def correctsel(e1, v1, lst):

				found = False
				# check situation where left/right connection is on some other slicevert than first
				while not(found):
					found = True
					for edge in e1.other_vert(v1).link_edges:
						if edge.select and edge != e1:
							if lst.index(e1) < len(lst) - 1:
								v1.select = False
								e1.select = False
								v1 = e1.other_vert(v1)
								e1 = lst[lst.index(e1) + 1]
								break
							else:
								templ = list(e1.other_vert(v1).link_faces)
								for f in e1.link_faces:
									templ.pop(templ.index(f))
								if len(templ) < 2:
									v1.select = False
									e1.select = False
									v1 = e1.other_vert(v1)
									return e1, v1, 'REVERSE'
								for edge in e1.other_vert(v1).link_edges:
									if edge in templ[0].edges and edge in templ[1].edges:
										v1.select = False
										e1.select = False
										v1 = e1.other_vert(v1)
										e1 = edge
								break
							found = False

				# check situation where left/right connection is on vert thats outside slice
				found = False
				while not(found):
					templ = list(v1.link_faces)
					for f in e1.link_faces:
						templ.pop(templ.index(f))
					found = True
					if len(templ) < 2:
						break
					for edge in v1.link_edges:
						if edge in templ[0].edges and edge in templ[1].edges:
							if edge.other_vert(v1).select:
								v1.select = False
								edge.select = False
								v1 = edge.other_vert(v1)
								e1 = edge
								found = False
				return e1, v1, 'NORMAL'

			e1, v1, state1 = correctsel(e1, v1, self.edgelist[i])
			if state1 == 'REVERSE':
				# special trick - mail me
				for j in range(i + 1):
					self.edgelist[j].reverse()
					self.vertlist[j].reverse()
			e2, v2, state2 = correctsel(e2, v2, self.edgelist[i+1])
			if state2 == 'REVERSE':
				# special trick - mail me
				self.edgelist[i+1].reverse()
				self.vertlist[i+1].reverse()

			# do all the checking to see if the checked lists must be reversed
			brk = False
			for face1 in e1.link_faces:
				for edge1 in face1.edges:
					if edge1.select:
						for loop1 in face1.loops:
							if loop1.vert == v1:
								if loop1.edge == e1:
									turn = loop1
								elif loop1.link_loop_next.edge == e1:
									turn = loop1.link_loop_next
								else:
									turn = loop1.link_loop_prev
								# check if turning in one direction
								if turn.link_loop_next.edge.select:
									for face2 in e2.link_faces:
										for edge2 in face2.edges:
											if edge2.select:
												for loop2 in face2.loops:
													if loop2.vert == v2:
														if loop2.edge == e2:
															turn = loop2
														elif loop2.link_loop_next.edge == e2:
															turn = loop2.link_loop_next
														else:
															turn = loop2.link_loop_prev
														if turn.link_loop_next.edge.select:
															self.singledir[i+1] = e2.other_vert(v2)
															self.edgelist[i+1].reverse()
															self.vertlist[i+1].reverse()
														break
												brk = True
												break
										if brk == True:
											break
								# and the other
								elif loop1.link_loop_prev.edge.select:
									for face2 in e2.link_faces:
										for edge2 in face2.edges:
											if edge2.select:
												for loop2 in face2.loops:
													if loop2.vert == v2:
														if loop2.edge == e2:
															turn = loop2
														elif loop2.link_loop_next.edge == e2:
															turn = loop2.link_loop_next
														else:
															turn = loop2.link_loop_prev
														if turn.link_loop_prev.edge.select:
															self.singledir[i+1] = e2.other_vert(v2)
															self.edgelist[i+1].reverse()
															self.vertlist[i+1].reverse()
														break
												brk = True
												break
										if brk == True:
											break
								break
						break

		bpy.ops.mesh.select_all(action = 'DESELECT')
		for posn in range(len(self.vertlist)):
			for v in self.vertlist[posn]:
				v.select = True
			for e in self.edgelist[posn]:
				e.select = True

		# recalculate normals for affected faces
		recalcfaces = set([])
		for posn in range(len(self.vertlist)):
			for vert in self.vertlist[posn]:
				for face in	vert.link_faces:
					recalcfaces.add(face)
		bmesh.ops.recalc_face_normals(self.bm, faces=list(recalcfaces))
		
		# try to guess min and max values for distance slider - can always use mouse to override
		co1 = self.vertlist[0][0].co
		co2 = self.vertlist[0][len(self.vertlist[0]) - 1].co
		self.meanmin = (co1 - co2).length * -2
		self.meanmax = -self.meanmin
		if self.meanmax == 0:
			self.meanmax = self.meanmin = 1

		# this is only local - must find way to change Operator prop
		Distance = bpy.props.FloatProperty(
				name = "Distance",
				description = "Enter distance2",
				default = 0,
				min = self.meanmin,
				max = self.meanmax)







def panel_func(self, context):

	self.layout.label(text="ParEdge:")
	self.layout.operator("mesh.paredge", text="Insert Edges")
	if started:
		self.layout.prop(mainop, "Distance")
		self.layout.prop(mainop, "Both")
		if mainop.Both:
			self.layout.prop(mainop, "Cap")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_class(ParEdge)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()





