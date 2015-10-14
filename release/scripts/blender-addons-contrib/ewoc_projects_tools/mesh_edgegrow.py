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
This addon enables you to snakelike "grow" an edgeloop selection with arrow keys.


Documentation

First go to User Preferences->Addons and enable the EdgeGrow addon in the Mesh category.
Invoke it (button in the Mesh Tools panel).
Go to EditMode, select one or more edges or connected edge-snakes (you can grow several at the same time, a bmesh mesh has a certain
spin direction to it, so in most general non-complex situations multiple edges will grow together
in the desired direction).  Use the left and right arrow keys to grow / ungrow the edgeloop in any direction.
The addon will show the edges you can grow next in light blue, with the active edge(will be selected
when using arrow keys) highlighted in red.  Use up and down arrow keys to activate the other light blue
edges, this way you can route your edge-snake in every possible direction; defsult is the middle one.
You can grow multiple slices at the same time.

If you wish to hotkey EdgeGrow:
In the Input section of User Preferences at the bottom of the 3D View > Mesh section click 'Add New' button.
In the Operator Identifier box put 'mesh.edgetune'.
Assign a hotkey.
Save as Default (Optional).
"""


bl_info = {
	"name": "EdgeGrow",
	"author": "Gert De Roost",
	"version": (0, 4, 1),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Growing edgeloops with arrowkeys",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"}



import bpy
import bpy_extras
import bmesh
from bgl import glColor3f, glBegin, GL_LINES, glVertex2f, glEnd
from mathutils import Vector, Matrix
import time




class EdgeGrow(bpy.types.Operator):
	bl_idname = "mesh.edgegrow"
	bl_label = "EdgeGrow"
	bl_description = "Growing edgeloops with arrowkeys"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		self.init_edgegrow(context)

		context.window_manager.modal_handler_add(self)

		self._handle = bpy.types.SpaceView3D.draw_handler_add(self.redraw, (), 'WINDOW', 'POST_PIXEL')

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		if event.type in {'MIDDLEMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
			# User transforms view
			return {'PASS_THROUGH'}

		elif event.type in {'RET', 'NUMPAD_ENTER'}:
			# Consolidate changes if ENTER pressed.
			# Free the bmesh.
			self.bm.free()
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.editmode_toggle()
			return {'FINISHED'}

		elif event.type == 'LEFT_ARROW':
			# REINIT: when user returns to begin position: display self.cursor edges on both sides
			# START: add to beginning of lists
			# END: add to END of lists
			# INIT: first INITialization state: self.cursor on both sides
			# set self.cursor to correct edge
			for posn in range(len(self.edgelist)):
				if event.value == 'PRESS':
					if self.state[posn] == 'REINIT':
						self.check[posn] = False
						if self.oldstate[posn] == 'START':
							if self.activedir[posn] == 'LEFT':
								self.state[posn] = 'START'
							else:
								self.state[posn] = 'END'
								if self.cursor[posn] == self.startcur[posn]:
									self.cursor[posn] = self.endcur[posn]
								else:
									self.cursor[posn] = self.startcur[posn]
						else:
							if self.activedir[posn] == 'LEFT':
								self.state[posn] = 'END'
							else:
								self.state[posn] = 'START'
								if self.cursor[posn] == self.startcur[posn]:
									self.cursor[posn] = self.endcur[posn]
								else:
									self.cursor[posn] = self.startcur[posn]
						self.activedir[posn] = 'LEFT'
					if self.state[posn] == 'INIT':
						self.activedir[posn] = 'LEFT'
						self.check[posn] = True
						self.state[posn] = 'START'
						self.cursor[posn] = self.startcur[posn]

					# activedir: left or right absolute -> movement in x direction (when in INIT state)
					if self.activedir[posn] == 'LEFT':
						self.addedge(posn)
					else:
						self.removeedge(posn)
			return {'RUNNING_MODAL'}

		elif event.type == 'RIGHT_ARROW':
			# check LEFT_ARROW
			if event.value == 'PRESS':
				for posn in range(len(self.edgelist)):
					if self.state[posn] == 'REINIT':
						self.check[posn] = False
						if self.oldstate[posn] == 'START':
							if self.activedir[posn] == 'RIGHT':
								self.state[posn] = 'START'
								if self.cursor[posn] == self.startcur[posn]:
									self.cursor[posn] = self.startcur[posn]
								else:
									self.cursor[posn] = self.endcur[posn]
							else:
								self.state[posn] = 'END'
								if self.cursor[posn] == self.startcur[posn]:
									self.cursor[posn] = self.endcur[posn]
								else:
									self.cursor[posn] = self.startcur[posn]
						else:
							if self.activedir[posn] == 'RIGHT':
								self.state[posn] = 'END'
								if self.cursor[posn] == self.startcur[posn]:
									self.cursor[posn] = self.startcur[posn]
								else:
									self.cursor[posn] = self.endcur[posn]
							else:
								self.state[posn] = 'START'
								if self.cursor[posn] == self.startcur[posn]:
									self.cursor[posn] = self.endcur[posn]
								else:
									self.cursor[posn] = self.startcur[posn]
						self.activedir[posn] = 'RIGHT'
					if self.state[posn] == 'INIT':
						self.activedir[posn] = 'RIGHT'
						self.check[posn] = True
						self.state[posn] = 'END'
						self.cursor[posn] = self.endcur[posn]
					if self.activedir[posn] == 'RIGHT':
						self.addedge(posn)
					else:
						self.removeedge(posn)
			return {'RUNNING_MODAL'}

		elif event.type == 'UP_ARROW':
			# next cursor possibility
			if event.value == 'PRESS':
				self.counter += 1
				self.mesh.update()
			return {'RUNNING_MODAL'}

		elif event.type == 'DOWN_ARROW':
			# previous cursor possibility
			if event.value == 'PRESS':
				self.counter -= 1
				self.mesh.update()
			return {'RUNNING_MODAL'}

		return {'RUNNING_MODAL'}

	def addedge(self, posn):

		# add edge to edgelist
		self.change = True
		if self.state[posn] == 'START':
			self.edgelist[posn].insert(0, self.cursor[posn])
		if self.state[posn] == 'END':
			self.edgelist[posn].append(self.cursor[posn])
		self.cursor[posn].verts[0].select = True
		self.cursor[posn].verts[1].select = True
		self.cursor[posn].select = True
		self.mesh.update()

	def removeedge(self, posn):

		# remove edge from edgelist
		self.change = True
		if self.state[posn] == 'START':
			for vert in self.edgelist[posn][0].verts:
				if vert in self.cursor[posn].verts:
					vert.select = False
			self.cursor[posn] = self.edgelist[posn][0]
			self.edgelist[posn].pop(0)
		if self.state[posn] == 'END':
			for vert in self.edgelist[posn][len(self.edgelist[posn]) - 1].verts:
				if vert in self.cursor[posn].verts:
					vert.select = False
			self.cursor[posn] = self.edgelist[posn][len(self.edgelist[posn]) - 1]
			self.edgelist[posn].pop(len(self.edgelist[posn]) - 1)
		self.cursor[posn].select = False
		self.mesh.update()


	def init_edgegrow(self, context):

		self.change = True

		self.area = context.area
		self.region = context.region
		self.rv3d = context.space_data.region_3d
		self.selobj = context.active_object
		self.mesh = self.selobj.data
		self.bm = bmesh.from_edit_mesh(self.mesh)
		self.actedge = self.bm.select_history.active
		# get transf matrix
		self.getmatrix()

		# vsellist, essellist: remember selection for reselecting later
		self.selset = set([])
		self.vsellist = []
		self.esellist = []
		for edge in self.bm.edges:
			if edge.select:
				self.selset.add(edge)
				self.esellist.append(edge)
		for vert in self.bm.verts:
			if vert.select:
				self.vsellist.append(vert)


		def addstart(vert):

			# recursive: adds to initial edgelist at start
			for e in vert.link_edges:
				if e in self.selset:
					self.selset.discard(e)
					v = e.other_vert(vert)
					self.edgelist[posn].insert(0, e)
					addstart(v)
					break

		def addend(vert):

			# recursive: adds to initial edgelist at end
			for e in vert.link_edges:
				if e in self.selset:
					self.selset.discard(e)
					v = e.other_vert(vert)
					self.edgelist[posn].append(e)
					addend(v)
					break

		self.state = []
		self.oldstate = []
		self.cursor = []
		self.startcur = []
		self.endcur = []
		self.check = []
		self.activedir = []
		self.singledir = {}
		self.singledir[0] = None
		self.startlen = []
		self.edgelist = []
		posn = 0
		while len(self.selset) > 0:
			# INITialize next edgesnake
			self.state.append('INIT')
			self.oldstate.append('INIT')
			self.cursor.append(None)
			self.startcur.append(None)
			self.endcur.append(None)
			self.check.append(0)
			self.activedir.append("")

			self.edgelist.append([])
			elem = self.selset.pop()
			vert = elem.verts[0]
			self.selset.add(elem)
			# add to START and END of arbitrary START vert
			addstart(vert)
			addend(vert)
			self.startlen.append(len(self.edgelist[posn]))
			posn += 1
		if len(self.edgelist) == 1:
			if len(self.edgelist[0]) == 1:
				# must store leftmost vert as startingvert when only one edge selected
				x1, y = self.getscreencoords(self.edgelist[0][0].verts[0].co)
				x2, y = self.getscreencoords(self.edgelist[0][0].verts[1].co)
				if x1 < x2:
					self.singledir[0] = self.edgelist[0][0].verts[0]
				else:
					self.singledir[0] = self.edgelist[0][0].verts[1]

		# orient first edgesnake from left(start) to right(end)
		x1, y = self.getscreencoords(self.edgelist[0][0].verts[0].co)
		x2, y = self.getscreencoords(self.edgelist[0][len(self.edgelist[0]) - 1].verts[0].co)
		if x1 > x2:
			self.edgelist[0].reverse()


		#
		# orient edge and vertlists parallel - reverse if necessary
		for i in range(len(self.edgelist) - 1):
			bpy.ops.mesh.select_all(action='DESELECT')
			# get first vert and edge for two adjacent snakes
			for v in self.edgelist[i][0].verts:
				if len(self.edgelist[i]) == 1:
					if i == 0:
						x1, y = self.getscreencoords(v.co)
						x2, y = self.getscreencoords(self.edgelist[i][0].other_vert(v).co)
						if x1 < x2:
							self.singledir[0] = v
						else:
							self.singledir[0] = self.edgelist[i][0].other_vert(v)
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
				while not(found):
					found = True
					for edge in e1.other_vert(v1).link_edges:
						if edge.select and edge != e1:
							if lst.index(e1) < len(lst) - 1:
								v1.select = False
								e1.select = False
								v1 = e1.other_vert(v1)
								e1 = lst[lst.index(e1) + 1]
							else:
								templ = list(e1.other_vert(v1).link_faces)
								for f in e1.link_faces:
									templ.pop(templ.index(f))
								for edge in e1.other_vert(v1).link_edges:
									if edge in templ[0].edges and edge in templ[1].edges:
										v1.select = False
										e1.select = False
										v1 = e1.other_vert(v1)
										e1 = edge
							found = False

				# check situation where left/right connection is on vert thats outside slice
				found = False
				while not(found):
					templ = list(v1.link_faces)
					for f in e1.link_faces:
						templ.pop(templ.index(f))
					found = True
					for edge in v1.link_edges:
						if edge in templ[0].edges and edge in templ[1].edges:
							if edge.other_vert(v1).select:
								v1.select = False
								edge.select = False
								v1 = edge.other_vert(v1)
								e1 = edge
								found = False
				return e1, v1

			e1, v1 = correctsel(e1, v1, self.edgelist[i])
			e2, v2 = correctsel(e2, v2, self.edgelist[i+1])

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
														break
												brk = True
												break
										if brk == True:
											break
								break
						break

		for posn in range(len(self.edgelist)):
			if self.edgelist[posn][0] == self.actedge:
				for posn in range(len(self.edgelist)):
					self.edgelist[posn].reverse()

		bpy.ops.mesh.select_all(action='DESELECT')
		for v in self.vsellist:
			v.select = True
		for e in self.esellist:
			e.select = True


		self.region.tag_redraw()



	def getmatrix(self):

		# Rotating / panning / zooming 3D view is handled here.
		# Get matrix.
		if self.selobj.rotation_mode == 'AXIS_ANGLE':
			# when roataion mode is axisangle
			angle, x, y, z =  self.selobj.rotation_axis_angle
			self.matrix = Matrix.Rotation(-angle, 4, Vector((x, y, z)))
		elif self.selobj.rotation_mode == 'QUATERNION':
			# when rotation on object is quaternion
			w, x, y, z = self.selobj.rotation_quaternion
			x = -x
			y = -y
			z = -z
			quat = Quaternion([w, x, y, z])
			self.matrix = quat.to_matrix()
			self.matrix.resize_4x4()
		else:
			# when rotation of object is euler
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


	def getscreencoords(self, vector):

		# calculate screen coords for given Vector
		vector = vector * self.matrix
		vector = vector + self.selobj.location
		return bpy_extras.view3d_utils.location_3d_to_region_2d(self.region, self.rv3d, vector)


	def drawedges(self, vert, edge):

		def getedge(vert, edge):

			# get the next edge in list of edges rotating from/around vert at seelection END (for cursor choice)
			for loop in vert.link_loops:
				if loop.edge == edge:
					edge = loop.link_loop_prev.edge
					if edge == self.startedge:
						break
					self.sortlist.append(edge)
					getedge(vert, edge)
					break

		# get sorted list of possible cursor choices
		self.sortlist = []
		self.startedge = edge
		getedge(vert, edge)
		if len(vert.link_edges) - len(self.sortlist) > 1:
			for e in vert.link_edges:
				if e != self.startedge:
					if not(e in self.sortlist):
						self.sortlist.append(e)
		# calculate new cursor position in sortlist if changed
		if self.change:
			if len(self.sortlist) == 2 and (len(self.sortlist[0].link_faces) == 1 or len(self.sortlist[1].link_faces) == 1):
				for f in self.startedge.link_faces:
					for e in self.sortlist:
						tel = 0
						if e.verts[0] in f.verts:
							tel += 1
							vfound = e.verts[1]
						if e.verts[1] in f.verts:
							tel += 1
							vfound = e.verts[0]
						if tel == 1:
							break
				for e in self.sortlist:
					if vfound in e.verts:
						cnt = self.sortlist.index(e)
			else:
				# standard middle edge is cursor
				cnt = int((len(self.sortlist) - 1) / 2)
			self.counter = cnt
		else:
			# do revert to START when past END and other way around
			if self.counter >= len(self.sortlist):
				cnt = self.counter - (int(self.counter / len(self.sortlist)) * len(self.sortlist))
			elif self.counter < 0:
				cnt = self.counter
				while cnt < 0:
					cnt += len(self.sortlist)
			else:
				cnt = self.counter
		# draw cursor possibilities in blue, current in red
		for edge in self.sortlist:
			if self.sortlist.index(edge) == cnt:
				self.tempcur = edge
				glColor3f(1.0, 0, 0)
			else:
				glColor3f(0.2, 0.2, 1.0)
			glBegin(GL_LINES)
			x, y = self.getscreencoords(edge.verts[0].co)
			glVertex2f(x, y)
			x, y = self.getscreencoords(edge.verts[1].co)
			glVertex2f(x, y)
			glEnd()


	def setcursors(self, v, posn):

		# what it says
		if self.oldstate[posn] == 'START':
			if v in self.cursor[posn].verts:
				self.startcur[posn] = self.tempcur
			else:
				self.endcur[posn] = self.tempcur
		elif self.oldstate[posn] == 'END':
			if v in self.cursor[posn].verts:
				self.endcur[posn] = self.tempcur
			else:
				self.startcur[posn] = self.tempcur


	def redraw(self):

		# Reinit if returning to initial state
		for lst in self.edgelist:
			posn = self.edgelist.index(lst)
			self.oldstate[posn] = self.state[posn]
			if len(lst) == self.startlen[posn]:
				if self.check[posn]:
					self.state[posn] = 'REINIT'
			else:
				self.check[posn] = True

		for lst in self.edgelist:
			posn = self.edgelist.index(lst)

			if self.state[posn] == 'INIT' or self.state[posn] == 'REINIT':
				if len(lst) == 1:
					# if snake is one edge, use singledir vert for orientation
					v = lst[0].verts[0]
					self.drawedges(v, lst[0])
					self.setcursors(v, posn)
					if self.oldstate[posn] == 'INIT':
						if self.singledir[posn] == v:
							self.startcur[posn] = self.tempcur
						else:
							self.endcur[posn] = self.tempcur
					v = lst[0].verts[1]
					self.drawedges(v, lst[0])
					self.setcursors(v, posn)
					if self.oldstate[posn] == 'INIT':
						if self.singledir[posn] == v:
							self.startcur[posn] = self.tempcur
						else:
							self.endcur[posn] = self.tempcur
				else:
					# draw and set START and END cursors
					edge = lst[0]
					edge.select = False
					for vert in edge.verts:
						if not(vert in lst[1].verts):
							self.drawedges(vert, edge)
							self.startcur[posn] = self.tempcur
					edge = lst[len(lst) - 1]
					edge.select = False
					for vert in edge.verts:
						if not(vert in lst[len(lst) - 2].verts):
							self.drawedges(vert, edge)
							self.endcur[posn] = self.tempcur
			elif self.state[posn] == 'START':
				# draw and set cursor at START
				edge = lst[0]
				for vert in edge.verts:
					if not(vert in lst[1].verts):
						self.drawedges(vert, edge)
						self.cursor[posn] = self.tempcur
			elif self.state[posn] == 'END':
				# draw and set cursor at END
				edge = lst[len(lst) - 1]
				for vert in edge.verts:
					if not(vert in lst[len(lst) - 2].verts):
						self.drawedges(vert, edge)
						self.cursor[posn] = self.tempcur
			for e in self.edgelist[posn]:
				e.verts[0].select = True
				e.verts[1].select = True
				e.select = True

		self.change = False




def panel_func(self, context):
	self.layout.label(text="EdgeGrow:")
	self.layout.operator("mesh.edgegrow", text="Grow Edges")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()







