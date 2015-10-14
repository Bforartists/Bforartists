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
This script is an implementation of the concept of sliding vertices around
   on edges.  It is used to finetune/redraw edges/edgeloops through the process of sliding
   vertices.  It can be used to slide anything anywhere.
   To my knowledge this is a new concept in 3D modeling. Try it and you will
   see how it can impact your modeling habits.
   You are able to tune vertices by sliding by freehand-redrawing them on the
   edges they are part of.



   Documentation


   First install the addon by going to User Preferences-> AddOns and choosing
   "Install from file". Locate the downloaded file and install it.
   Enable the script in User Preferences->AddOns->Mesh.


   The addon will work on any vertice/edge/face-selection.
   Make a selection, click the EdgeTune button on the Mesh Tools panel.
   (addon only accessible when in EditMode).

   The selection will be visualized in yellow.
   EdgeTune will abide by the limited visibility setting.
   Press and hold left-mouse button and draw freely across the "slide-edges",
   visualized in red.
   The respective selected vertices will change position on the slide-edge to
   the new position you choose by moving over it with the left mouse-button
   pressed.  Vertices can be made to move past the end of the edge by
   keeping leftmouse pressed, and moving along the supporting edge and
   further in that same direction.

   Undo one step a time with Ctrl-Z.
   Press ENTER/RETURN to finalize the operation.

   Just press the right-mouse-button to cancel the addon operation.

   Change orientation the standard Blender way.
   HINT: EdgeTune is also multi-vertex-slide."""


bl_info = {
	"name": "EdgeTune",
	"author": "Gert De Roost",
	"version": (3, 5, 1),
	"blender": (2, 65, 0),
	"location": "View3D > Tools",
	"description": "Tuning edgeloops by redrawing them manually, sliding verts.",
	"warning": "",
	"wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Mesh/EdgeTune",
	"tracker_url": "",
	"category": "Mesh"}




import bpy
from bpy_extras import *
from bgl import *
import math
from mathutils import *
import bmesh







class EdgeTune(bpy.types.Operator):
	bl_idname = "mesh.edgetune"
	bl_label = "Tune Edge"
	bl_description = "Tuning edgeloops by redrawing them manually, sliding verts"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

	def invoke(self, context, event):

		self.scn = context.scene
		self.screen = context.screen
		self.area = context.area
		self.region = context.region
		self.selobj = context.active_object
		self.init_edgetune()

		context.window_manager.modal_handler_add(self)
		self._handle = bpy.types.SpaceView3D.draw_handler_add(self.redraw, (), 'WINDOW', 'POST_PIXEL')

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		self.viewchange = False
		if event.type == 'LEFTMOUSE':
			if event.value == 'PRESS':
				self.mbns = True
			if event.value == 'RELEASE':
				self.mbns = False
				self.contedge = None
				self.movedoff = True
		if event.type == 'RIGHTMOUSE':
			# cancel operation, reset to bmumdo mesh
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
			bpy.ops.object.editmode_toggle()
			self.bmundo.to_mesh(self.mesh)
			bpy.ops.object.editmode_toggle()
			return {'CANCELLED'}
		elif event.type == 'MIDDLEMOUSE':
			# recalculate view parameters
			self.viewchange = True
			return {'PASS_THROUGH'}
		elif event.type in {'WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
			# recalculate view parameters
			self.viewchange = True
			return {'PASS_THROUGH'}
		elif event.type == 'Z':
			if event.value == 'PRESS':
				if event.ctrl:
					if self.undolist != []:
						# put one vert(last) back to undo coordinate, found in list
						self.undolist.pop(0)
						vert = self.bm.verts[self.undocolist[0][0].index]
						vert.co[0] = self.undocolist[0][1]
						vert.co[1] = self.undocolist[0][2]
						vert.co[2] = self.undocolist[0][3]
						self.undocolist.pop(0)
						self.mesh.update()
			return {'RUNNING_MODAL'}

		elif event.type == 'RET':
			# Consolidate changes.
			# Free the bmesh.
			self.bmundo.free()
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
			self.region.tag_redraw()
			return {'FINISHED'}

		elif event.type == 'MOUSEMOVE':
			mxa = event.mouse_x
			mya = event.mouse_y
			self.region = None
			for a in context.screen.areas:
				if not(a.type == 'VIEW_3D'):
					continue
				for r in a.regions:
					if not(r.type == 'WINDOW'):
						continue
					if mxa > r.x and mya > r.y and mxa < r.x + r.width and mya < r.y + r.height:
						self.region = r
						break

			if not(self.region):
				return {'RUNNING_MODAL'}
			mx = mxa - self.region.x
			my = mya - self.region.y

			hoveredge = None

			# First check mouse is in bounding box edge of which edges.
			testscrl = []
			for edge in self.slideedges[self.region]:
				x1, y1, dummy = self.getscreencoords(edge.verts[0].co, self.region)
				x2, y2, dummy = self.getscreencoords(edge.verts[1].co, self.region)
				if x1 < x2:
					lwpx = x1 - 5
					uppx = x2 + 5
				else:
					lwpx = x2 - 5
					uppx = x1 + 5
				if y1 < y2:
					lwpy = y1 - 5
					uppy = y2 + 5
				else:
					lwpy = y2 - 5
					uppy = y1 + 5
				if (((x1 < mx < x2) or (x2 < mx < x1)) and (lwpy < my < uppy)) or (((y1 < my < y2) or (y2 < my < y1)) and (lwpx < mx < uppx)):
					testscrl.append(edge)
				if self.contedge != None:
					testscrl.append(self.contedge)

			# Then check these edges to see if mouse is on one of them.
			allhoveredges = []
			hovering = False
			zmin = 1e10
			if testscrl != []:
				for edge in testscrl:
					x1, y1, z1 = self.getscreencoords(edge.verts[0].co, self.region)
					x2, y2, z2 = self.getscreencoords(edge.verts[1].co, self.region)

					if x1 == x2 and y1 == y2:
						dist = math.sqrt((mx - x1)**2 + (my - y1)**2)
					else:
						dist = ((mx - x1)*(y2 - y1) - (my - y1)*(x2 - x1)) / math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

					if -5 < dist < 5:
						if self.movedoff or (not(self.movedoff) and edge == self.contedge):
							allhoveredges.append(edge)
							if hoveredge != None and ((z1 + z2) / 2) > zmin:
								pass
							else:
								hovering = True
								hoveredge = edge
								zmin = (z1 + z2) / 2
								self.mouseover = True
								x1, y1, dummy = self.getscreencoords(hoveredge.verts[0].co, self.region)
								x2, y2, dummy = self.getscreencoords(hoveredge.verts[1].co, self.region)
								for r in self.regions:
									self.bx1[r], self.by1[r], dummy = self.getscreencoords(hoveredge.verts[0].co, r)
									self.bx2[r], self.by2[r], dummy = self.getscreencoords(hoveredge.verts[1].co, r)
								self.region.tag_redraw()
								break

			if hovering == False:
				self.movedoff = True
				if self.mouseover == True:
					self.highoff = True
					self.region.tag_redraw()
				self.mouseover = False
				self.bx1[self.region] = -1
				self.bx2[self.region] = -1
				self.by1[self.region] = -1
				self.by2[self.region] = -1, -1, -1, -1



			if hoveredge != None and self.mbns == True:
				self.contedge = edge
				self.movedoff = False
				# Find projection mouse perpend on edge.
				if x1 == x2:	x1 += 1e-6
				if y1 == y2:	y1 += 1e-6
				a = (x2 - x1) / (y2 - y1)
				x = ((x1 / a) + (mx * a) + my - y1) / ((1 / a) + a)
				y = ((mx - x) * a) + my
				# Calculate relative position on edge and adapt screencoords accoringly.
				div = (x - x1) / (x2 - x1)
				if hoveredge.verts[0] in self.sverts[self.region]:
					vert = hoveredge.verts[0]
					vert2 = hoveredge.verts[1]
				else:
					vert = hoveredge.verts[1]
					vert2 = hoveredge.verts[0]

				# Update local undo info.
				if self.undolist == []:
					self.undolist.insert(0, hoveredge)
					self.undocolist.insert(0, [vert, vert.co[0], vert.co[1], vert.co[2]])
				if self.undolist[0] != hoveredge:
					self.undolist.insert(0, hoveredge)
					self.undocolist.insert(0, [vert, vert.co[0], vert.co[1], vert.co[2]])

				hx1, hy1, dummy = self.getscreencoords(hoveredge.verts[0].co, self.region)
				hx2, hy2, dummy = self.getscreencoords(hoveredge.verts[1].co, self.region)
				coords = [((hx2 - hx1) * div ) + hx1, ((hy2 - hy1) * div ) + hy1]
				for verts in self.selverts[self.region]:
					if vert == verts[0]:
						self.selcoords[self.region][self.selverts[self.region].index(verts)][0] = coords
					elif vert == verts[1]:
						self.selcoords[self.region][self.selverts[self.region].index(verts)][1] = coords
				if vert in self.singles:
					self.boxes[self.region][self.singles.index(vert)] = coords
				# Calculate new vert 3D coordinates.
				vx1, vy1, vz1 = hoveredge.verts[0].co[:]
				vx2, vy2, vz2 = hoveredge.verts[1].co[:]
				self.vertd[vert] = [((vx2 - vx1) * div ) + vx1, ((vy2 - vy1) * div ) + vy1, ((vz2 - vz1) * div ) + vz1]
				vert = self.bm.verts[vert.index]
				vert.co[0] = ((vx2 - vx1) * div ) + vx1
				vert.co[1] = ((vy2 - vy1) * div ) + vy1
				vert.co[2] = ((vz2 - vz1) * div ) + vz1
				self.mesh.update()

		return {'RUNNING_MODAL'}



	def adapt(self):

		self.firstrun = False

		self.regions = []
		self.spaces = []
		self.halfheight = {}
		self.halfwidth = {}
		self.perspm = {}
		for a in self.screen.areas:
			if not(a.type == 'VIEW_3D'):
				continue
			for r in a.regions:
				if not(r.type == 'WINDOW'):
					continue
				self.regions.append(r)
				self.halfwidth[r] = r.width / 2
				self.halfheight[r] = r.height / 2
				for sp in a.spaces:
					if sp.type == 'VIEW_3D':
						self.spaces.append(sp)
						self.perspm[r] = sp.region_3d.perspective_matrix

		self.selcoords = {}
		self.slidecoords = {}
		self.boxes = {}
		self.sverts = {}
		self.selverts = {}
		self.seledges = {}
		self.slideverts = {}
		self.slideedges = {}
		for r in self.regions:
			self.selcoords[r] = []
			self.slidecoords[r] = []
			self.boxes[r] = []
			self.sverts[r] = []
			self.selverts[r] = []
			self.seledges[r] = []
			self.slideverts[r] = []
			self.slideedges[r] = []

		for r in self.regions:

			self.getlayout(r)

			# recalculate screencoords in lists
			for posn in range(len(self.selverts[r])):
				self.selcoords[r][posn] = [self.getscreencoords(Vector(self.vertd[self.selverts[r][posn][0]]), r)[:2], self.getscreencoords(Vector(self.vertd[self.selverts[r][posn][1]]), r)[:2]]
			for posn in range(len(self.slideverts[r])):
				self.slidecoords[r][posn] = [self.getscreencoords(self.slideverts[r][posn][0].co, r)[:2],  self.getscreencoords(self.slideverts[r][posn][1].co, r)[:2]]
			for posn in range(len(self.singles)):
				self.boxes[r][posn] = self.getscreencoords(Vector(self.vertd[self.singles[posn]]), r)[:2]



	def findworldco(self, vec):

		vec = vec.copy()
		vec.rotate(self.selobj.matrix_world)
		vec.rotate(self.selobj.matrix_world)
		vec = vec * self.selobj.matrix_world + self.selobj.matrix_world.to_translation()
		return vec

	def getscreencoords(self, vec, reg):

		# calculate screencoords of given Vector
		vec = self.findworldco(vec)
		prj = self.perspm[reg] * vec.to_4d()
		return (self.halfwidth[reg] + self.halfwidth[reg] * (prj.x / prj.w), self.halfheight[reg] + self.halfheight[reg] * (prj.y / prj.w), prj.z)




	def init_edgetune(self):

		self.mesh = self.selobj.data
		self.bm = bmesh.from_edit_mesh(self.mesh)
		self.bmundo = self.bm.copy()

		self.viewwidth = self.area.width
		self.viewheight = self.area.height

		#remember initial selection
		self.keepverts = []
		for vert in self.bm.verts:
			if vert.select:
				self.keepverts.append(vert)
		self.keepedges = []
		for edge in self.bm.edges:
			if edge.select:
				self.keepedges.append(edge)

		self.firstrun = True
		self.highoff = False
		self.mbns = False
		self.viewchange = False
		self.mouseover = False
		self.bx1, self.bx2, self.by1, self.by2 = {}, {}, {}, {}
		self.undolist = []
		self.undocolist = []
		self.contedge = None

		self.adapt()
		for r in self.regions:
			r.tag_redraw()



	def getlayout(self, reg):

		# seledges: selected edges list
		# selverts: selected verts list per edge
		# selcoords: selected verts coordinate list per edge
		self.sverts[reg] = []
		self.seledges[reg] = []
		self.selverts[reg] = []
		self.selcoords[reg] = []
		visible = {}
		if self.spaces[self.regions.index(reg)].use_occlude_geometry:
			rv3d = self.spaces[self.regions.index(reg)].region_3d
			eyevec = Vector(rv3d.view_matrix[2][:3])
			eyevec.length = 100000
			eyeloc = Vector(rv3d.view_matrix.inverted().col[3][:3])
			for vert in self.keepverts:
				vno = vert.normal
				vno.length = 0.0001
				vco = self.findworldco(vert.co + vno)
				if rv3d.is_perspective:
					hit = self.scn.ray_cast(vco, eyeloc)
					if hit[0]:
						vno = -vno
						vco = self.findworldco(vert.co + vno)
						hit = self.scn.ray_cast(vco, eyevec)
				else:
					hit = self.scn.ray_cast(vco, vco + eyevec)
					if hit[0]:
						vno = -vno
						vco = self.findworldco(vert.co + vno)
						hit = self.scn.ray_cast(vco, vco + eyevec)
				if not(hit[0]):
					visible[vert] = True
					self.sverts[reg].append(self.bmundo.verts[vert.index])
				else:
					visible[vert] = False
		else:
			for vert in self.keepverts:
				visible[vert] = True
				self.sverts[reg].append(self.bmundo.verts[vert.index])

		for edge in self.keepedges:
			if visible[edge.verts[0]] and visible[edge.verts[1]]:
				edge = self.bmundo.edges[edge.index]
				self.seledges[reg].append(edge)
				self.selverts[reg].append([edge.verts[0], edge.verts[1]])
				x1, y1, dummy = self.getscreencoords(edge.verts[0].co, reg)
				x2, y2, dummy = self.getscreencoords(edge.verts[1].co, reg)
				self.selcoords[reg].append([[x1, y1],[x2, y2]])

		# selverts: selected verts list
		# slideedges: slideedges list
		# slideverts: slideverts list per edge
		# slidecoords: slideverts coordinate list per edge
		self.vertd = {}
		self.slideverts[reg] = []
		self.slidecoords[reg] = []
		self.slideedges[reg] = []
		count = 0
		for vert in self.sverts[reg]:
			self.vertd[vert] = vert.co[:]
			for edge in vert.link_edges:
				count += 1
				if not(edge in self.seledges[reg]):
					self.slideedges[reg].append(edge)
					self.slideverts[reg].append([edge.verts[0], edge.verts[1]])
					x1, y1, dummy = self.getscreencoords(edge.verts[0].co, reg)
					x2, y2, dummy = self.getscreencoords(edge.verts[1].co, reg)
					self.slidecoords[reg].append([[x1, y1], [x2, y2]])
		# Box out single vertices.
		self.singles = []
		self.boxes[reg] = []
		for vert in self.sverts[reg]:
			single = True
			for edge in self.seledges[reg]:
				if vert == edge.verts[0] or vert == edge.verts[1]:
					single = False
					break
			if single:
				self.singles.append(vert)
				self.boxes[reg].append(self.getscreencoords(vert.co, reg)[:2])


	def redraw(self):

		drawregion = bpy.context.region

		if self.viewchange:
			self.adapt()

		if self.slideverts[drawregion] != []:
			# Draw single verts as boxes.
			glColor3f(1.0,1.0,0)
			for self.vertcoords in self.boxes[drawregion]:
				glBegin(GL_POLYGON)
				x, y = self.vertcoords
				glVertex2f(x-2, y-2)
				glVertex2f(x-2, y+2)
				glVertex2f(x+2, y+2)
				glVertex2f(x+2, y-2)
				glEnd()

			# Accentuate selected edges.
			glColor3f(1.0, 1.0, 0)
			for posn in range(len(self.selcoords[drawregion])):
				glBegin(GL_LINES)
				x, y = self.selcoords[drawregion][posn][0]
				glVertex2f(x, y)
				x, y = self.selcoords[drawregion][posn][1]
				glVertex2f(x, y)
				glEnd()

			# Draw slide-edges.
			glColor3f(1.0, 0, 0)
			for posn in range(len(self.slidecoords[drawregion])):
				glBegin(GL_LINES)
				x, y = self.slidecoords[drawregion][posn][0]
				glVertex2f(x, y)
				x, y = self.slidecoords[drawregion][posn][1]
				glVertex2f(x, y)
				glEnd()

		# Draw mouseover highlighting.
		if self.mouseover:
			glColor3f(0, 0, 1.0)
			glBegin(GL_LINES)
			x,y = self.bx1[drawregion], self.by1[drawregion]
			if not(x == -1):
				glVertex2f(x,y)
			x,y = self.bx2[drawregion], self.by2[drawregion]
			if not(x == -1):
				glVertex2f(x,y)
			glEnd()
		if self.highoff:
			self.highoff = 0
			glColor3f(1.0, 0, 0)
			glBegin(GL_LINES)
			x,y = self.bx1[drawregion], self.by1[drawregion]
			if not(x == -1):
				glVertex2f(x,y)
			x,y = self.bx2[drawregion], self.by2[drawregion]
			if not(x == -1):
				glVertex2f(x,y)
			glEnd()





def panel_func(self, context):
	self.layout.label(text="Deform:")
	self.layout.operator("mesh.edgetune", text="EdgeTune")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()








