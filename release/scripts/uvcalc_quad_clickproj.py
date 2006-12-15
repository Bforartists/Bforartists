#!BPY

""" Registration info for Blender menus: <- these words are ignored
Name: 'Click project from face'
Blender: 242
Group: 'UVCalculation'
Tooltip: '3 Clicks to project uvs onto selected faces.'
"""

__author__ = ["Campbell Barton"]
__url__ = ("blender", "elysiun", "http://members.iinet.net.au/~cpbarton/ideasman/")
__version__ = "0.1"
__bpydoc__=\
'''
http://mediawiki.blender.org/index.php/Scripts/Manual/UV_Calculate/Click_project_from_face
"

'''

# -------------------------------------------------------------------------- 
# Click project v0.1 by Campbell Barton (AKA Ideasman)
# -------------------------------------------------------------------------- 
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
# You should have received a copy of the GNU General Public License 
# along with this program; if not, write to the Free Software Foundation, 
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. 
# 
# ***** END GPL LICENCE BLOCK ***** 
# -------------------------------------------------------------------------- 

import Blender
import BPyMesh
import BPyWindow

mouseViewRay= BPyWindow.mouseViewRay
from Blender import Mathutils, Window, Scene, Draw, sys
from Blender.Mathutils import CrossVecs, Vector, Matrix, LineIntersect, Intersect #, AngleBetweenVecs, Intersect
LMB= Window.MButs['L']
RMB= Window.MButs['R']

def mouseup():
	# Loop until click
	mouse_buttons = Window.GetMouseButtons()
	while not mouse_buttons & LMB:
		sys.sleep(10)
		mouse_buttons = Window.GetMouseButtons()
	while mouse_buttons & LMB:
		sys.sleep(10)
		mouse_buttons = Window.GetMouseButtons()

def mousedown_wait():
	# If the menu has just been pressed dont use its mousedown,
	mouse_buttons = Window.GetMouseButtons()
	while mouse_buttons & LMB:
		mouse_buttons = Window.GetMouseButtons()
		sys.sleep(10)

def main():
	
	scn = Scene.GetCurrent()
	ob = scn.objects.active
	if not ob or ob.type!='Mesh':
		return
	
	mousedown_wait() # so the menu items clicking dosnt trigger the mouseclick
	
	Window.DrawProgressBar (0.0, '')
	Window.DrawProgressBar (0.1, '(1 of 3) Click on a face corner')	
	
	# wait for a click
	mouse_buttons = Window.GetMouseButtons()
	while not mouse_buttons & LMB:
		sys.sleep(10)
		mouse_buttons = Window.GetMouseButtons()
		
		# Allow for RMB cancel
		if mouse_buttons & RMB:
			Window.DrawProgressBar (1.0, '')
			return
		
	while mouse_buttons & LMB:
		sys.sleep(10)
		mouse_buttons = Window.GetMouseButtons()
	
	
	
	Window.DrawProgressBar (0.2, '(2 of 3 ) Click confirms the U coords')
	
	
	mousedown_wait()
	
	obmat= ob.matrixWorld
	screen_x, screen_y = Window.GetMouseCoords()
	mouseInView, OriginA, DirectionA = mouseViewRay(screen_x, screen_y, obmat)
	
	if not mouseInView or not OriginA:
		Window.DrawProgressBar (1.0, '')
		return
		
	me = ob.getData(mesh=1)
	
	# Get the face under the mouse
	face_click, isect, side = BPyMesh.pickMeshRayFace(me, OriginA, DirectionA)
	
	proj_z_component = face_click.no
	if not face_click:
		Window.DrawProgressBar (1.0, '')
		return
	
	# Find the face vertex thats closest to the mouse,
	# this vert will be used as the corner to map from.
	best_v= None
	best_length = 10000000
	vi1 = None
	for i, v in enumerate(face_click.v):
		l = (v.co-isect).length
		if l < best_length:
			best_v = v
			best_length = l
			vi1 = i
	
	# now get the 2 edges in the face that connect to v
	# we can work it out fairly easerly
	if len(face_click)==4:
		if	 vi1==0: vi2, vi3= 3,1
		elif vi1==1: vi2, vi3= 0,2
		elif vi1==2: vi2, vi3= 1,3
		elif vi1==3: vi2, vi3= 2,0
	else:
		if   vi1==0: vi2, vi3= 2,1
		elif vi1==1: vi2, vi3= 0,2
		elif vi1==2: vi2, vi3= 1,0
	
	face_corner_main =face_click.v[vi1].co
	face_corner_a =face_click.v[vi2].co
	face_corner_b =face_click.v[vi3].co
	
	line_a_len = (face_corner_a-face_corner_main).length
	line_b_len = (face_corner_b-face_corner_main).length
	
	orig_cursor = Window.GetCursorPos()
	Window.SetCursorPos(face_corner_main.x, face_corner_main.y, face_corner_main.z)
	
	MODE = 0 # firstclick, 1, secondclick
	mouse_buttons = Window.GetMouseButtons()
	
	project_mat = Matrix([0,0,0], [0,0,0], [0,0,0])
	
	
	SELECT_FLAG = Blender.Mesh.FaceFlags['SELECT']
	me_faces_sel = [ ([v.co-face_corner_main for v in f], f.uv) for f in me.faces if f.flag & SELECT_FLAG ]
	del SELECT_FLAG
	
	me_faces_sel_uvs = [uv.copy() for f in me_faces_sel for uv in f[1]]
	
	while 1:
		if mouse_buttons & LMB:
			if MODE == 0:
				mousedown_wait()
				Window.DrawProgressBar (0.8, '(3 of 3 ) Click confirms the V coords')
				MODE = 1 # second click
			else:
				break
		elif mouse_buttons & RMB:
			
			# Restore old uvs
			i= 0
			for f in me_faces_sel:
				for uv in f[1]:
					uv[:] = me_faces_sel_uvs[i]
					i+=1
			break
			
		mouse_buttons = Window.GetMouseButtons()
		screen_x, screen_y = Window.GetMouseCoords()
		mouseInView, OriginA, DirectionA = mouseViewRay(screen_x, screen_y, obmat)
		
		if not mouseInView:
			continue
		
		
		# Do a ray tri intersection, not clipped by the tri
		new_isect = Intersect(face_corner_main, face_corner_a, face_corner_b, DirectionA, OriginA, False)
		new_isect_alt = new_isect + DirectionA*0.0001
		
		
		# The distance from the mouse cursor ray vector to the edge
		line_isect_a_pair = LineIntersect(new_isect, new_isect_alt, face_corner_main, face_corner_a)
		line_isect_b_pair = LineIntersect(new_isect, new_isect_alt, face_corner_main, face_corner_b)
		
		if MODE == 0:	
			line_dist_a = (line_isect_a_pair[0]-line_isect_a_pair[1]).length
			line_dist_b = (line_isect_b_pair[0]-line_isect_b_pair[1]).length
			
			if line_dist_a < line_dist_b:
				proj_x_component = face_corner_a - face_corner_main
				y_axis_length = line_b_len
				x_axis_length = (line_isect_a_pair[1]-face_corner_main).length
			else:
				proj_x_component = face_corner_b - face_corner_main
				y_axis_length = line_a_len
				x_axis_length = (line_isect_b_pair[1]-face_corner_main).length
			
			proj_y_component = CrossVecs(proj_x_component, proj_z_component)
			
			proj_y_component.length = 1/y_axis_length
			proj_x_component.length = 1/x_axis_length
		
		else:
			if line_dist_a < line_dist_b:
				proj_y_component.length = 1/(line_isect_a_pair[1]-new_isect).length
			else:
				proj_y_component.length = 1/(line_isect_b_pair[1]-new_isect).length
		
		# Use the existing matrix to make a new 3x3 projecton matrix
		project_mat[0][:] = proj_x_component
		project_mat[1][:] = proj_y_component
		project_mat[2][:] = proj_z_component
		
		# Apply the projection matrix
		for f_proj_co, f_uv in me_faces_sel:
			for i, uv in enumerate(f_uv):
				uv[:] = (project_mat * f_proj_co[i])[0:2]
		
		Window.Redraw(Window.Types.VIEW3D)
	
	Window.DrawProgressBar (1.0, '')
	Window.SetCursorPos(*orig_cursor)
	Window.RedrawAll()
	
if __name__=='__main__':
	main()