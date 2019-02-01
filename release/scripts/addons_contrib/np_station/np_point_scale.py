
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


'''
DESCRIPTION

Scales and snap-stretches one or more objects with one end fixed. It's main advantage is stretching with precision. I am used of working with similar commands a lot, during my architecture design processes. Good for construction beams, openings, table-tops, carpets and other cubic shapes. Besides that, it doesn't require object origin and 3D cursor manipulation.


INSTALLATION

Unzip and place .py file to scripts / addons_contrib folder. In User Preferences / Addons tab, search with Testing filter - NP Point Scale and check the box.
Now you have the operator in your system. If you press Save User Preferences, you will have it at your disposal every time you run Blender.


SHORTCUTS

After successful installation of the addon, the NP Point Scale operator should be registered in your system. Enter User Preferences / Input, and under that, 3DView / Object mode. At the bottom of the list click the 'Add new' button. In the operator field type object.np_point_scale_xxx (xxx being the number of the version) and assign a shortcut key of your preference. I suggest assigning S, replacing the standard scale command since it is incorporated in this operator. Assign it only for the Object Mode because the addon doesn't work in other modes. This way the basic S command should be available in all other editing environments and you can copy it back to Object mode if needed. Note, this operator is still a prototype.


USAGE

Select one or more objects.
Run operator (spacebar search - NP Cage Scale, or keystroke if you assigned it)
Pick-snap one of the points on the mode-cage.
Scale or stretch with CTRL-snap

You can run the operator with spacebar search - NP Point Copy, or shortcut key if you assigned it.
Select a point anywhere in the scene (holding CTRL enables snapping). This will be your 'take' point.
Move your mouse and click to a point anywhere in the scene with the left mouse button (LMB), in relation to the 'take' point and the operator will duplicate the selected objects at that position (again CTRL - snap enables snapping to objects around the scene). You can continue duplicating objects in the same way. When you want to finish the process, press ESC or RMB. If you want to make an array of the copied objects in relation to the last pair, press the 'ENTER' button (ENT). The command will automatically read the direction and the distance between the last pair of copied objects and present an interface to specify the number of arrayed copies. You specify the number with CTRL + mouse scroll, with the possibility to go below the amount of 2 which changes the mode of array to division.  You confirm the array with RMB / ENTER / TAB key or cancel it with ESC. Pressing RMB at the end will confirm the array and keep it as a modifier in the modifier stack, ENTER will apply the modifier as a single object and remove the modifier, while TAB would apply the modifier as an array of separate individual objects and remove the modifier from the modifier stack.
If at any point you lose sight of the next point you want to snap to, you can press SPACE to go to NAVIGATION mode in which you can change the point of view. When your next point is clearly in your field of view, you return to normal mode by pressing SPACE again or LMB.
Middle mouse button (MMB) enables axis constraint during snapping, while numpad keys enable numerical input for the copy distance.


ADDON SETTINGS:

Below the addon name in the user preferences / addon tab, you can find a couple of settings that control the behavior of the addon:

Unit scale: Distance multiplier for various unit scenarios
Suffix: Unit abbreviation after the numerical distance
Custom colors: Default or custom colors for graphical elements
Mouse badge: Option to display a small cursor label


IMPORTANT PERFORMANCE NOTES

All origins of objects participating are centered to their geometry after scaling
In flipping, script goes through edit mode of objects
Scale and rotate are applied to all objects participating


WISH LIST

Ability to include lattices and other non-mesh types in the transformation
Ability to adjust the rotation of the cage to better suite the geometry of scaled object
Bgl overlay for mode points and eventually the mode cage
Blf instructions on screen, preferably interactive
Cleaner code and faster performance


WARNINGS

The addon is still in beta and is probably not immune to heavy geometry and has not been tested in all scenarios, so avoid production use...
'''

bl_info = {
    'name': 'NP 020 Point Scale',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Scales selected objects using bounding box with handles',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
#import math
import mathutils
import bgl
import blf
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *

# Defining the main class - the macro:

class NP020PointScale(bpy.types.Macro):
    bl_idname = 'object.np_020_point_scale'
    bl_label = 'NP 020 Point Scale'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020PS:

    flag = 'DISPLAY'


# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:

@persistent
def NPPS_scene_update(context):

    if bpy.data.objects.is_updated:
        a = 1


# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPPSGetContext(bpy.types.Operator):
    bl_idname = 'object.np_ps_get_context'
    bl_label = 'NP PS Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.selected_objects == []:
            self.report({'WARNING'}, "Please select objects first")
            return {'CANCELLED'}
        NP020PS.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020PS.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020PS.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020PS.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020PS.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020PS.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020PS.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020PS.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020PS.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020PS.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020PS.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020PS.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020PS.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020PS.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020PS.edit_mode = 'PARTICLE_EDIT'
        #in case the proces is interrupted from outside warning on multiple users and storage is stuck with old flags
        NP020PS.flag = 'DISPLAY'
        NP020PS.flag_con = False
        NP020PS.flag_cenpivot = False
        NP020PS.flag_lev = False
        NP020PS.flag_force = False
        NP020PS.mode = None
        return {'FINISHED'}


# Defining the class that will gather the list of selected objects and acquire the exact dimensions and the location of the selection - it reads the selection and scans bounding-box dimensions of all the objects included, searching for the farthest geometry in all directions. In this way it acquires the dimensions of the selection. The location of the selected group is calculated as the middle point afterwards:

class NPPSGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_ps_get_selection'
    bl_label = 'NP PS Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.mode not in ('OBJECT'):
            bpy.ops.object.mode_set(mode = 'OBJECT')
        selob = bpy.context.selected_objects
        NP020PS.selob = selob

        minx, miny, minz = (999999.0,)*3
        maxx, maxy, maxz = (-999999.0,)*3
        for ob in selob:
            for v in ob.bound_box:
                v_world = ob.matrix_world * mathutils.Vector((v[0],v[1],v[2]))

                if v_world[0] < minx:
                    minx = v_world[0]
                if v_world[0] > maxx:
                    maxx = v_world[0]

                if v_world[1] < miny:
                    miny = v_world[1]
                if v_world[1] > maxy:
                    maxy = v_world[1]

                if v_world[2] < minz:
                    minz = v_world[2]
                if v_world[2] > maxz:
                    maxz = v_world[2]

        cage3d = {}
        cage3d[0] = (minx, miny, minz)
        cage3d[1] = (maxx, miny, minz)
        cage3d[2] = (maxx, maxy, minz)
        cage3d[3] = (minx, maxy, minz)
        cage3d[4] = (minx, miny, maxz)
        cage3d[5] = (maxx, miny, maxz)
        cage3d[6] = (maxx, maxy, maxz)
        cage3d[7] = (minx, maxy, maxz)
        cage3d[10] = ((minx+maxx)/2, miny, minz)
        cage3d[12] = (maxx, (miny+maxy)/2, minz)
        cage3d[23] = ((minx+maxx)/2, maxy, minz)
        cage3d[30] = (minx, (miny+maxy)/2, minz)
        cage3d[40] = (minx, miny, (minz+maxz)/2)
        cage3d[15] = (maxx, miny, (minz+maxz)/2)
        cage3d[26] = (maxx, maxy, (minz+maxz)/2)
        cage3d[37] = (minx, maxy, (minz+maxz)/2)
        cage3d[45] = ((minx+maxx)/2, miny, maxz)
        cage3d[56] = (maxx, (miny+maxy)/2, maxz)
        cage3d[67] = ((minx+maxx)/2, maxy, maxz)
        cage3d[47] = (minx, (miny+maxy)/2, maxz)
        cross3d = {}
        cross3d['xmin'] = (minx, (miny + maxy)/2, (minz + maxz)/2)
        cross3d['xmax'] = (maxx, (miny + maxy)/2, (minz + maxz)/2)
        cross3d['ymin'] = ((minx + maxx)/2, miny, (minz + maxz)/2)
        cross3d['ymax'] = ((minx + maxx)/2, maxy, (minz + maxz)/2)
        cross3d['zmin'] = ((minx + maxx)/2, (miny + maxy)/2, minz)
        cross3d['zmax'] = ((minx + maxx)/2, (miny + maxy)/2, maxz)
        c3d = ((minx + maxx)/2, (miny + maxy)/2, (minz + maxz)/2)
        NP020PS.cage3d = cage3d
        NP020PS.cross3d = cross3d
        NP020PS.c3d = c3d

        '''
        NP020PS.minx = minx
        NP020PS.maxx = maxx
        NP020PS.miny = miny
        NP020PS.maxy = maxy
        NP020PS.minz = minz
        NP020PS.maxz = maxz
        '''
        return {'FINISHED'}


# Defining the operator that will read the user input made during display cage phase and set the next operator accordingly:

class NPPSPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_ps_prepare_context'
    bl_label = 'NP PS Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        flag = NP020PS.flag
        NP020PS.trans_custom = False  #..........................................
        np_print('prepare, NP020PS.flag = ', flag)

        if flag == 'DISPLAY':
            bpy.ops.object.select_all(action = 'DESELECT')

        elif flag == 'RUNRESIZE' :
            selob = NP020PS.selob
            mode = NP020PS.mode
            flag_con = NP020PS.flag_con
            flag_cenpivot = NP020PS.flag_cenpivot
            flag_lev = NP020PS.flag_lev
            flag_force = NP020PS.flag_force
            cage3d = NP020PS.cage3d
            cross3d = NP020PS.cross3d
            c3d = NP020PS.c3d
            curloc = NP020PS.curloc
            bpy.context.tool_settings.use_snap = False
            bpy.context.tool_settings.snap_element = 'VERTEX'
            bpy.context.tool_settings.snap_target = 'ACTIVE'
            bpy.context.space_data.pivot_point = 'CURSOR'
            bpy.context.space_data.transform_orientation = 'GLOBAL'
            for ob in selob:
                ob.select_set(True)
                bpy.context.view_layer.objects.active = ob
            axis = (False, False, False)
            if mode == 0:
                curloc = cage3d[6]
            elif mode == 1:
                curloc = cage3d[7]
            elif mode == 2:
                curloc = cage3d[4]
            elif mode == 3:
                curloc = cage3d[5]
            elif mode == 4:
                curloc = cage3d[2]
            elif mode == 5:
                curloc = cage3d[3]
            elif mode == 6:
                curloc = cage3d[0]
            elif mode == 7:
                curloc = cage3d[1]
            elif mode == 'xmin':
                curloc = cross3d['xmax']
                axis = (True, False, False)
            elif mode == 'xmax':
                curloc = cross3d['xmin']
                axis = (True, False, False)
            elif mode == 'ymin':
                curloc = cross3d['ymax']
                axis = (False, True, False)
            elif mode == 'ymax':
                curloc = cross3d['ymin']
                axis = (False, True, False)
            elif mode == 'zmin':
                curloc = cross3d['zmax']
                axis = (False, False, True)
            elif mode == 'zmax':
                curloc = cross3d['zmin']
                axis = (False, False, True)
            if flag_con: axis = (False, False, False)
            if flag_cenpivot: curloc = c3d
            if flag_force: bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
            bpy.context.scene.cursor_location = curloc
            NP020PS.axis = axis

        return{'FINISHED'}

# Defining the class for adding a representation of the scale cage to the viewport. By interacting with graphical elements of the cage, the user picks the type of scaling he wants to be performed:

class NPPSDisplayCage(bpy.types.Operator):
    bl_idname = 'object.np_ps_display_cage'
    bl_label = 'NP PS Display Cage'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        flag = NP020PS.flag

        if not event.ctrl and not event.shift and not event.alt and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = False
            self.flag_cenpivot = False
            self.flag_lev = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = True
            self.flag_cenpivot = False
            self.flag_lev = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.shift and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = False
            self.flag_cenpivot = True
            self.flag_lev = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.alt and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = False
            self.flag_cenpivot = False
            self.flag_lev = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.shift and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = True
            self.flag_cenpivot = True
            self.flag_lev = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.alt and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = True
            self.flag_cenpivot = False
            self.flag_lev = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.shift and event.alt and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = False
            self.flag_cenpivot = True
            self.flag_lev = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.shift and event.alt and event.type == 'MOUSEMOVE':
            self.mode = None
            self.flag_con = True
            self.flag_cenpivot = True
            self.flag_lev = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))


        if event.type == 'LEFT_CTRL' and event.value == 'PRESS':
            self.flag_con = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.value == 'RELEASE':
            self.flag_con = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_SHIFT' and event.value == 'PRESS':
            self.flag_cenpivot = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_SHIFT' and event.value == 'RELEASE':
            self.flag_cenpivot = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_ALT' and event.value == 'PRESS':
            self.flag_lev = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_ALT' and event.value == 'RELEASE':
            self.flag_lev = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.type == 'LEFT_SHIFT' and event.value == 'PRESS':
            self.flag_con = True
            self.flag_cenpivot = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.type == 'LEFT_SHIFT' and event.value == 'RELEASE':
            self.flag_con = False
            self.flag_cenpivot = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_ALT' and event.type == 'LEFT_SHIFT' and event.value == 'PRESS':
            self.flag_lev = True
            self.flag_cenpivot = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_ALT' and event.type == 'LEFT_SHIFT' and event.value == 'RELEASE':
            self.flag_lev = False
            self.flag_cenpivot = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.type == 'LEFT_ALT' and event.value == 'PRESS':
            self.flag_con = True
            self.flag_lev = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.type == 'LEFT_ALT' and event.value == 'RELEASE':
            self.flag_con = False
            self.flag_lev = False
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'TAB' and event.value == 'PRESS':
            if self.flag_force == True:
                self.flag_force = False
            else:
                self.flag_force = True

        if event.type in ('LEFTMOUSE', 'RIGHTMOUSE', 'RET', 'NUMPAD_ENTER') and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PS.flag_con = self.flag_con
            NP020PS.flag_cenpivot = self.flag_cenpivot
            NP020PS.flag_lev = self.flag_lev
            NP020PS.flag_force = self.flag_force
            NP020PS.mode = self.mode
            NP020PS.flag = 'RUNRESIZE'
            return {'FINISHED'}

        if event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PS.flag = 'EXIT'
            return {'FINISHED'}

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_DisplayCage, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            self.flag_con = False
            self.flag_cenpivot = False
            self.flag_lev = False
            self.flag_force = False
            self.mode = None
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


# Defining the set of instructions that will draw the graphical OpenGL elements on the screen during the execution of DisplayCage operator:

def DRAW_DisplayCage(self, context):

    flag = NP020PS.flag
    flag = 'DISPLAY'
    cage3d = NP020PS.cage3d
    cross3d = NP020PS.cross3d
    c3d = NP020PS.c3d

    region = context.region
    rv3d = context.region_data
    cage2d = copy.deepcopy(cage3d)
    cross2d = copy.deepcopy(cross3d)

    for co in cage3d.items():
        #np_print(co[0])
        cage2d[co[0]] = view3d_utils.location_3d_to_region_2d(region, rv3d, co[1])
    for co in cross3d.items():
        cross2d[co[0]] = view3d_utils.location_3d_to_region_2d(region, rv3d, co[1])
    c2d = view3d_utils.location_3d_to_region_2d(region, rv3d, c3d)

    points = copy.deepcopy(cage2d)
    points.update(cross2d)



    # DRAWING START:
    bgl.glEnable(bgl.GL_BLEND)

    if flag == 'DISPLAY':
        instruct = 'select a handle'
        keys_aff = 'LMB - confirm, CTRL - force proportional, SHIFT - force central, TAB - apply scale / rotation'
        keys_nav = ''
        keys_neg = 'ESC - quit'

    if self.flag_con:
        mark_col = (1.0, 0.5, 0.0, 1.0)
    else:
        mark_col = (0.3, 0.6, 1.0, 1.0)


    # ON-SCREEN INSTRUCTIONS:

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    sensor = 60
    self.mode = None
    co2d = mathutils.Vector(self.co2d)
    distmin = mathutils.Vector(co2d - c2d).length

    # Hover markers - detection
    for co in points.items():
        dist = mathutils.Vector(co2d - co[1]).length
        if dist < distmin:
            distmin = dist
            if distmin < sensor:
                self.mode = co[0]
                self.hoverco = co[1]

    # Drawing the graphical representation of scale cage, calculated from selection's bound box:
    if self.mode == None:
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glLineWidth(1.4)
    else:
        bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
        bgl.glLineWidth(1.0)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cage2d[0])
    bgl.glVertex2f(*cage2d[1])
    bgl.glVertex2f(*cage2d[2])
    bgl.glVertex2f(*cage2d[3])
    bgl.glVertex2f(*cage2d[0])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cage2d[4])
    bgl.glVertex2f(*cage2d[5])
    bgl.glVertex2f(*cage2d[6])
    bgl.glVertex2f(*cage2d[7])
    bgl.glVertex2f(*cage2d[4])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cage2d[0])
    bgl.glVertex2f(*cage2d[4])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cage2d[1])
    bgl.glVertex2f(*cage2d[5])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cage2d[2])
    bgl.glVertex2f(*cage2d[6])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cage2d[3])
    bgl.glVertex2f(*cage2d[7])
    bgl.glEnd()
    bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    bgl.glLineWidth(1.0)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cross2d['xmin'])
    bgl.glVertex2f(*cross2d['xmax'])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cross2d['ymin'])
    bgl.glVertex2f(*cross2d['ymax'])
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*cross2d['zmin'])
    bgl.glVertex2f(*cross2d['zmax'])
    bgl.glEnd()
    #bgl.glDepthRange(0,0)
    bgl.glColor4f(0.35, 0.65, 1.0, 1.0)
    bgl.glPointSize(9)
    bgl.glBegin(bgl.GL_POINTS)
    for [a,b] in cross2d.values():
       bgl.glVertex2f(a,b)
    bgl.glEnd()
    bgl.glEnable(bgl.GL_POINT_SMOOTH)
    bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
    bgl.glPointSize(11)
    bgl.glBegin(bgl.GL_POINTS)
    for co in cage2d.items():
       if len(str(co[0])) == 1:
           bgl.glVertex2f(*co[1])
    bgl.glEnd()
    bgl.glDisable(bgl.GL_POINT_SMOOTH)

    markers = {}
    markers[0] = (points[0], points[10], points[40], points[0], points[30], points[40], points[0], points[10], points[30])
    markers[1] = (points[1], points[10], points[15], points[1], points[12], points[15], points[1], points[10], points[12])
    markers[2] = (points[2], points[12], points[26], points[2], points[23], points[26], points[2], points[12], points[23])
    markers[3] = (points[3], points[30], points[37], points[3], points[23], points[37], points[3], points[30], points[23])
    markers[4] = (points[4], points[45], points[47], points[4], points[40], points[47], points[4], points[40], points[45])
    markers[5] = (points[5], points[45], points[56], points[5], points[15], points[56], points[5], points[15], points[45])
    markers[6] = (points[6], points[26], points[67], points[6], points[56], points[67], points[6], points[26], points[56])
    markers[7] = (points[7], points[37], points[67], points[7], points[47], points[67], points[7], points[37], points[47])
    markers['xmin'] = (points[0], points[3], points[7], points[4], points[0])
    markers['xmax'] = (points[1], points[2], points[6], points[5], points[1])
    markers['ymin'] = (points[0], points[1], points[5], points[4], points[0])
    markers['ymax'] = (points[2], points[3], points[7], points[6], points[2])
    markers['zmin'] = (points[0], points[1], points[2], points[3], points[0])
    markers['zmax'] = (points[4], points[5], points[6], points[7], points[4])

    pivot = {}
    if self.flag_cenpivot:
        pivot[0] = c2d
        pivot[1] = c2d
        pivot[2] = c2d
        pivot[3] = c2d
        pivot[4] = c2d
        pivot[5] = c2d
        pivot[6] = c2d
        pivot[7] = c2d
        pivot['xmin'] = c2d
        pivot['xmax'] = c2d
        pivot['ymin'] = c2d
        pivot['ymax'] = c2d
        pivot['zmin'] = c2d
        pivot['zmax'] = c2d
    else:
        pivot[0] = points[6]
        pivot[1] = points[7]
        pivot[2] = points[4]
        pivot[3] = points[5]
        pivot[4] = points[2]
        pivot[5] = points[3]
        pivot[6] = points[0]
        pivot[7] = points[1]
        pivot['xmin'] = points['xmax']
        pivot['xmax'] = points['xmin']
        pivot['ymin'] = points['ymax']
        pivot['ymax'] = points['ymin']
        pivot['zmin'] = points['zmax']
        pivot['zmax'] = points['zmin']

    np_print('self.mode = ', self.mode)
    fields = False
    field_contours = False
    pivots = True
    pivot_lines = True
    if fields:
        # Hover markers - fields
        bgl.glColor4f(0.65, 0.85, 1.0, 0.35)
        for mark in markers.items():
            if mark[0] == self.mode:
                #if type(mark[0]) is not str:
                    #bgl.glColor4f(1.0, 1.0, 1.0, 0.3)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                for x, y in mark[1]:
                    bgl.glVertex2f(x, y)
                bgl.glEnd()

    if field_contours:
        # Hover markers - contours
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glLineWidth(1.2)
        for mark in markers.items():
            if mark[0] == self.mode:
                if type(mark[0]) is not str:
                    #bgl.glColor4f(0.3, 0.6, 1.0, 0.5)
                    bgl.glColor4f(1.0, 1.0, 1.0, 0.75)
                    bgl.glLineWidth(1.0)
                bgl.glBegin(bgl.GL_LINE_STRIP)
                for x, y in mark[1]:
                    bgl.glVertex2f(x, y)
                bgl.glEnd()


    # Hover markers - pivot

    bgl.glEnable(bgl.GL_POINT_SMOOTH)

    bgl.glColor4f(*mark_col)
    bgl.glPointSize(12)
    for p in pivot.items():
        if p[0] == self.mode:
            if pivots:
                bgl.glBegin(bgl.GL_POINTS)
                #np_print(p[1])
                bgl.glVertex2f(*p[1])
                bgl.glEnd()

            if pivot_lines:
                bgl.glLineWidth(1.0)
                #bgl.glEnable(bgl.GL_LINE_STIPPLE)
                bgl.glBegin(bgl.GL_LINE_STRIP)
                bgl.glVertex2f(*points[self.mode])
                bgl.glVertex2f(*p[1])
                bgl.glEnd()
                #bgl.glDisable(bgl.GL_LINE_STIPPLE)

    if self.flag_cenpivot:
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glPointSize(12)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*c2d)
        bgl.glEnd()

    bgl.glDisable(bgl.GL_POINT_SMOOTH)

    # Hover markers - points
    bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
    bgl.glPointSize(16)
    for mark in markers.items():
        if mark[0] == self.mode:
            if type(mark[0]) is not str:
                bgl.glColor4f(*mark_col)
                bgl.glEnable(bgl.GL_POINT_SMOOTH)
                bgl.glPointSize(18)
            bgl.glBegin(bgl.GL_POINTS)
            bgl.glVertex2f(*points[self.mode])
            bgl.glEnd()
            bgl.glColor4f(*mark_col)
            bgl.glPointSize(12)
            if type(mark[0]) is not str:
                bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
                bgl.glEnable(bgl.GL_POINT_SMOOTH)
                bgl.glPointSize(14)
            bgl.glBegin(bgl.GL_POINTS)
            bgl.glVertex2f(*points[self.mode])
            bgl.glEnd()
            bgl.glDisable(bgl.GL_POINT_SMOOTH)

    if self.flag_force:
        flash_size = 7
        flash = [[0, 0], [2, 2], [1, 2], [2, 4], [0, 2], [1, 2], [0, 0]]
        for co in flash:
            co[0] = round((co[0] * flash_size),0) + self.co2d[0] + flash_size * 2
            co[1] = round((co[1] * flash_size),0) + self.co2d[1] - flash_size * 2

        bgl.glColor4f(0.95, 0.95, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for i, co in enumerate(flash):
            if i in range(0,3): bgl.glVertex2f(*co)
        bgl.glEnd()
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for i, co in enumerate(flash):
            if i in range(3,6): bgl.glVertex2f(*co)
        bgl.glEnd()
        bgl.glColor4f(1.0, 0.7, 0.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for co in flash:
            bgl.glVertex2f(*co)
        bgl.glEnd()



    # Restore opengl defaults
    bgl.glDisable(bgl.GL_POINTS)
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# Defining the operator that will do the actual scaling. It is basically a standard resize operator equipped with couple of additions. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPPSRunResize(bpy.types.Operator):
    bl_idname = 'object.np_ps_run_resize'
    bl_label = 'NP PS Run Resize'
    bl_options = {'INTERNAL'}

    def modal(self,context,event):
        context.area.tag_redraw()
        #flag = NP020PS.flag
        #self.mode = NP020PS.mode
        #self.flag_con = NP020PS.flag_con
        #self.flag_cenpivot = NP020PS.flag_cenpivot
        #self.flag_lev = NP020PS.flag_lev
        #self.flag_force = NP020PS.flag_force
        #axis = NP020PS.axis

        if event.type in ('LEFTMOUSE', 'NUMPAD_ENTER') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
        # this actually begins when user RELEASES esc or rightmouse, PRESS is
        # taken by transform.resize operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return{'FINISHED'}

        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        flag = NP020PS.flag

        if context.area.type == 'VIEW_3D':
            if flag == 'EXIT':
                np_print('RunResize_INVOKE_DECLINED_FINISHED',';','flag = ', flag)
                return {'FINISHED'}
            elif flag == 'RUNRESIZE':
                axis = NP020PS.axis
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_RunResize, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis = axis, constraint_orientation = 'GLOBAL')

            np_print('RunResize_INVOKE_a_RUNNING_MODAL')
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            np_print('RunResize_INVOKE_DECLINED_FINISHED',';','flag = ', Storage.flag)
            return {'FINISHED'}


# Defining the set of instructions that will draw the graphical OpenGL elements on the screen during the execution of RunResize operator:

def DRAW_RunResize(self, context):

    # Restore opengl defaults
    bgl.glDisable(bgl.GL_POINTS)
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# Restoring the object selection and system settings from before the operator activation:

class NPPSRestoreContext(bpy.types.Operator):
    bl_idname = "object.np_ps_restore_context"
    bl_label = "NP PS Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selob = NP020PS.selob
        bpy.ops.object.select_all(action = 'DESELECT')
        for ob in selob:
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
        bpy.context.tool_settings.use_snap = NP020PS.use_snap
        bpy.context.tool_settings.snap_element = NP020PS.snap_element
        bpy.context.tool_settings.snap_target = NP020PS.snap_target
        bpy.context.space_data.pivot_point = NP020PS.pivot_point
        bpy.context.space_data.transform_orientation = NP020PS.trans_orient
        if NP020PS.trans_custom: bpy.ops.transform.delete_orientation()
        bpy.context.scene.cursor_location = NP020PS.curloc
        if NP020PS.acob is not None:
            bpy.context.view_layer.objects.active = NP020PS.acob
            bpy.ops.object.mode_set(mode = NP020PS.edit_mode)
        NP020PS.flag = 'DISPLAY'
        return {'FINISHED'}


# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    NP020PointScale.define("OBJECT_OT_np_ps_get_context")
    NP020PointScale.define("OBJECT_OT_np_ps_get_selection")
    NP020PointScale.define("OBJECT_OT_np_ps_prepare_context")
    NP020PointScale.define("OBJECT_OT_np_ps_display_cage")
    NP020PointScale.define("OBJECT_OT_np_ps_prepare_context")
    NP020PointScale.define("OBJECT_OT_np_ps_run_resize")
    NP020PointScale.define("OBJECT_OT_np_ps_restore_context")

def unregister():
    pass
