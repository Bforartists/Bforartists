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

DESCRIPTION:

Draws a polyline using snap points. Emulates the functionality of the standard 'polyline'
command in CAD applications, with vertex snapping. Extrudes and bevels the shape afterwards.


INSTALLATION:

Two ways:

A. Paste the the .py file to text editor and run (ALT+P)
B. Unzip and place .py file to addons_contrib. In User Preferences / Addons tab search under
Testing / NP Float Poly and check the box.

Now you have the operator in your system. If you press Save User Preferences, you will have
it at your disposal every time you run Blender.


SHORTCUTS:

After successful installation of the addon, or it's activation from the text editor,
the NP Float Poly operator should be registered in your system. Enter User Preferences / Input,
and under that, 3DView / Object mode.
At the bottom of the list click the 'Add new' button. In the operator field type object.np_float_poly_xxx
(xxx being the number of the version) and assign a key of your preference. At the moment i am using 'P' for 'polyline'.


USAGE:

You can run the operator with spacebar search - NP Float Poly, or keystroke if you assigned it.
Select a point anywhere in the scene (holding CTRL enables snapping). This will be your start point.
Move your mouse and click to a point anywhere in the scene with the left mouse button (LMB), in relation
to the start point (again CTRL - snap). The addon will make a line from the first to the second point.
You can continue adding other points in the same way. When you want to finish the poly, press ESC or if you
want to close it, press right mouse button (RMB).
After the closure of the poly, the command will automatically start the extrusion of the poly into 3D.
You can confirm this with the LMB or avoid the extrusion with ESC. This will restrict the poly to 2D surface.
If at any point you lose sight of the next point you want to snap to, you can press SPACE to go to NAVIGATION
mode in which you can change the point of view. When your next point is clearly in your field of view, you
return to normal mode by pressing SPACE again or LMB.
Middle mouse button (MMB) enables axis constraint during snapping, while numpad keys enable numerical input
poly segment length.
After the extrusion, if you enabled the bevel function in the addon options, the script will start the bevel
operation which you control as usual - LMB for the amount and MMB scroll for the number of segments.


ADDON SETTINGS:

Below the addon name in the user preferences / addon tab, you can find a couple of settings that control
the behavior of the addon:

Unit scale: Distance multiplier for various unit scenarios
Suffix: Unit abbreviation after the numerical distance
Custom colors: Default or custom colors for graphical elements
Mouse badge: Option to display a small cursor label
Point markers: Option to display graphical markers for the start and segment points
Bevel: Option to automatically start a bevel operation after the extrusion
Base material: Option to add a basic material to the poly object
Smooth shading: Option to turn on smooth shading for the poly object
Wire contour: Option to turn on wireframe over the solid


IMPORTANT PERFORMANCE NOTES:

Unfortunately, this addon is effected by blender development and in linux 2.77 and 2.78 it shows a strange bug
as viewport fps falls dramatically after the command. However, pressing 2xTAB solves the issue. I am not sure what
causes the problem, i found no similar issues in version 2.76 and 2.75 in which the addon was made and used.

"""

bl_info = {
    'name': 'NP 020 Float Poly',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Draws lines and closed polygons using vertex snapping',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bmesh
import bgl
import blf
import mathutils
from bpy_extras import view3d_utils
# from bpy.app.handlers import persistent
from mathutils import Vector
from blf import ROTATION
from math import radians

from bpy.props import (
        BoolProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        )


from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *

# Defining the main class - the macro:

class NP020FloatPoly(bpy.types.Macro):
    bl_idname = 'object.np_020_float_poly'
    bl_label = 'NP 020 Float Poly'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable-bank for exchange among the classes. Later,
# this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020FP:

    startloc3d = (0.0, 0.0, 0.0)
    endloc3d = (0.0, 0.0, 0.0)
    phase = 0
    first = None
    start = None
    end = None
    dist = None
    polyob = None
    flag = 'TRANSLATE'
    snap = 'VERTEX'
    polysymbol = [[18, 37], [21, 37], [23, 33], [26, 33]]


# Defining the first of the operational classes for acquiring the list of selected objects and storing
# them for later re-call:

class NPFPGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_fp_get_selection'
    bl_label = 'NP FP Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        # First, storing all of the system preferences set by the user, that will be changed during the
        # process, in order to restore them when the operation is completed:

        np_print('01_get_selection_START')
        NP020FP.use_snap = bpy.context.tool_settings.use_snap
        NP020FP.snap_element = bpy.context.tool_settings.snap_element
        NP020FP.snap_target = bpy.context.tool_settings.snap_target
        NP020FP.pivot_point = bpy.context.space_data.pivot_point
        NP020FP.trans_orient = bpy.context.space_data.transform_orientation
        NP020FP.show_manipulator = bpy.context.space_data.show_manipulator
        NP020FP.acob = bpy.context.active_object
        np_print('NP020FP.acob = ', NP020FP.acob)
        np_print(bpy.context.mode)
        if bpy.context.mode == 'OBJECT':
            NP020FP.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE',
                                  'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020FP.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020FP.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020FP.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020FP.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020FP.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020FP.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020FP.edit_mode = 'PARTICLE_EDIT'
        NP020FP.phase = 0
        # Reading and storing the selection:
        selob = bpy.context.selected_objects
        NP020FP.selob = selob
        # De-selecting objects in prepare for other processes in the script:
        for ob in selob:
            ob.select = False
        np_print('01_get_selection_END')
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and
# store it as a location for placing the start and end points under the mouse:

class NPFPReadMouseLoc(bpy.types.Operator):
    bl_idname = 'object.np_fp_read_mouse_loc'
    bl_label = 'NP FP Read Mouse Loc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        np_print('02_read_mouse_loc_START')
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        pointloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector / 5
        np_print(pointloc)
        NP020FP.pointloc = pointloc
        np_print('02_read_mouse_loc_END')
        return{'FINISHED'}

    def invoke(self, context, event):
        np_print('02_read_mouse_loc_INVOKE_a')
        # np_print("START_____")
        args = (self, context)  # hm is this used ?
        context.window_manager.modal_handler_add(self)
        np_print('02_read_mouse_loc_INVOKE_b')
        return {'RUNNING_MODAL'}


# Defining the operator that will generate start and end points at the spot marked by mouse and
# select them, preparing for translation:

class NPFPAddPoints(bpy.types.Operator):
    bl_idname = 'object.np_fp_add_points'
    bl_label = 'NP FP Add Points'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_add_points_START')
        pointloc = NP020FP.pointloc
        if bpy.context.mode not in ('OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.add(type='MESH', location=pointloc)
        start = bpy.context.object
        start.name = 'NP_FP_start'
        NP020FP.start = start
        bpy.ops.object.add(type='MESH', location=pointloc)
        end = bpy.context.object
        end.name = 'NP_FP_end'
        NP020FP.end = end
        start.select = True
        end.select = True
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = NP020FP.snap
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        np_print('03_add_points_END')
        return{'FINISHED'}


# Defining the operator that will draw the OpenGL line across the screen together with the numerical
# distance and the on-screen instructions in normal, translation mode:

def draw_callback_px_TRANS(self, context):

    np_print('04_callback_TRANS_START')

    addon_prefs = context.user_preferences.addons[__package__].preferences
    point_markers = addon_prefs.npfp_point_markers
    point_size = addon_prefs.npfp_point_size


    polyob = NP020FP.polyob
    phase = NP020FP.phase
    start = NP020FP.start
    end = NP020FP.end
    startloc3d = start.location
    endloc3d = end.location
    endloc = end.location
    region = context.region
    rv3d = context.region_data
    startloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)
    co2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc)
    # np_print(end, endloc, co2d)


    '''
    if addon_prefs.npfp_col_line_main_DEF is False:
        col_line_main = addon_prefs.npfp_col_line_main
    else:
        col_line_main = (1.0, 1.0, 1.0, 1.0)

    if addon_prefs.npfp_col_line_shadow_DEF is False:
        col_line_shadow = addon_prefs.npfp_col_line_shadow
    else:
        col_line_shadow = (0.1, 0.1, 0.1, 0.25)

    if addon_prefs.npfp_col_num_main_DEF is False:
        col_num_main = addon_prefs.npfp_col_num_main
    else:
        col_num_main = (0.1, 0.1, 0.1, 0.75)

    if addon_prefs.npfp_col_num_shadow_DEF is False:
        col_num_shadow = addon_prefs.npfp_col_num_shadow
    else:
        col_num_shadow = (1.0, 1.0, 1.0, 1.0)
    '''

    if addon_prefs.npfp_point_color_DEF is False:
        col_pointromb = addon_prefs.npfp_point_color
    else:
        col_pointromb = (0.15, 0.15, 0.15, 1.0)


    # np_print('0')
    # sel = bpy.context.selected_objects

    if startloc2d is None:
        startloc2d = (0.0, 0.0)
        endloc2d = (0.0, 0.0)
    np_print(startloc2d, endloc2d)
    # np_print('1')

    '''
    # np_print('2')
    # This is for correcting the position of the numerical on the screen if the endpoints are far out of screen:
    numloc = []
    startx = startloc2d[0]
    starty = startloc2d[1]
    endx = endloc2d[0]
    endy = endloc2d[1]
    if startx > region.width:
        startx = region.width
    if startx < 0:
        startx = 0
    if starty > region.height:
        starty = region.height
    if starty < 0:
        starty = 0
    if endx > region.width:
        endx = region.width
    if endx < 0:
        endx = 0
    if endy > region.height:
        endy = region.height
    if endy < 0:
        endy = 0
    numloc.append((startx + endx) / 2)
    numloc.append((starty + endy) / 2)
    '''

    # np_print('3')
    if phase == 0:
        main = 'place start point'

    if phase > 0:
        main = 'place next point'

    # Drawing:

    bgl.glEnable(bgl.GL_BLEND)
    font_id = 0

    # ON-SCREEN INSTRUCTIONS:

    region = bpy.context.region
    rv3d = bpy.context.region_data
    instruct = main
    keys_aff = 'LMB - confirm, CTRL - snap, ENT - change snap, MMB - axis lock, NUMPAD - value, RMB - close poly and extrude'
    keys_nav = 'SPACE - navigate'
    keys_neg = 'ESC - stop poly at current state'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)



    # LINE:


    display_line_between_two_points(region, rv3d, startloc3d, endloc3d)

    '''

    bgl.glColor4f(*col_line_shadow)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f((startloc2d[0] - 1), (startloc2d[1] - 1))
    bgl.glVertex2f((endloc2d[0] - 1), (endloc2d[1] - 1))
    bgl.glEnd()

    bgl.glColor4f(*col_line_main)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*startloc2d)
    bgl.glVertex2f(*endloc2d)
    bgl.glEnd()
    # np_print('4')
    '''


    # POINT MARKERS:
    markersize = point_size
    triangle = [[0, 0], [-1, 1], [1, 1]]
    romb = [[-1, 0], [0, 1], [1, 0], [0, -1]]  # is this used ?

    if phase > 0 and polyob is None and point_markers:
        polylist2d = []
        for co in triangle:
            co[0] = round((co[0] * markersize * 3), 0) + startloc2d[0]
            co[1] = round((co[1] * markersize * 3), 0) + startloc2d[1]
        np_print('triangle', triangle)
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in triangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        pointromb = [[-1, 0], [0, 1], [1, 0], [0, -1]]
        for co in pointromb:
            co[0] = round((co[0] * markersize), 0) + endloc2d[0]
            co[1] = round((co[1] * markersize), 0) + endloc2d[1]
        if phase == 2:
            np_print('pointromb', pointromb)
            bgl.glColor4f(*col_pointromb)
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for x, y in pointromb:
                bgl.glVertex2f(x, y)
            bgl.glEnd()

    if polyob is not None and point_markers:
        np_print('polyob not None')
        polyloc = polyob.location
        polyme = polyob.data
        polylist3d = []

        for me in polyme.vertices:
            polylist3d.append(me.co + polyloc)
        np_print('polylist3d = ', polylist3d)
        polylist2d = []

        for p3d in polylist3d:
            p2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p3d)
            polylist2d.append(p2d)
        np_print('polylist2d = ', polylist2d)

        # triangle for the first point
        for co in triangle:
            co[0] = round((co[0] * markersize * 3), 0) + polylist2d[0][0]
            co[1] = round((co[1] * markersize * 3), 0) + polylist2d[0][1]
        np_print('triangle', triangle)
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in triangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        # rombs for the other points
        i = 0
        for p2d in polylist2d:
            if i > 0:
                pointromb = [[-1, 0], [0, 1], [1, 0], [0, -1]]
                for co in pointromb:
                    co[0] = round((co[0] * markersize), 0) + p2d[0]
                    co[1] = round((co[1] * markersize), 0) + p2d[1]
                np_print('pointromb', pointromb)
                bgl.glColor4f(*col_pointromb)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)

                for x, y in pointromb:
                    bgl.glVertex2f(x, y)
            i = i + 1
            bgl.glEnd()


    # Drawing the small badge near the cursor with the basic instructions:


    symbol = copy.deepcopy(NP020FP.polysymbol)
    badge_mode = 'RUN'
    message_main = 'CTRL+SNAP'
    message_aux = NP020FP.snap
    aux_num = None
    aux_str = None


    display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str)




    '''
    if badge:
        for co in square:
            co[0] = round((co[0] * size), 0) - (size * 10) + mouseloc[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + mouseloc[1]
        for co in rectangle:
            co[0] = round((co[0] * size), 0) - (size * 10) + mouseloc[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + mouseloc[1]
        for co in polysymbol:
            co[0] = round((co[0] * size), 0) - (size * 10) + mouseloc[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + mouseloc[1]

        ipx = round((ipx * size), 0) - (size * 10) + mouseloc[0]
        ipy = round((ipy * size), 0) - (size * 25) + mouseloc[1]
        ipsize = int(6 * size)

        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in rectangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x, y in polysymbol:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ipx, ipy, 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, 'CTRL+SNAP')
    '''

    # NUMERICAL DISTANCE:
    '''
    np_print('numloc = ', numloc, 'dist = ', dist)
    font_id = 0
    bgl.glColor4f(*col_num_shadow)
    if phase > 0:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, (numloc[0] - 1), (numloc[1] - 1), 0)
        blf.draw(font_id, dist)

    bgl.glColor4f(*col_num_main)
    if phase > 0:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, numloc[0], numloc[1], 0)
        blf.draw(font_id, dist)
        '''

    region = bpy.context.region
    rv3d = bpy.context.region_data
    dist_scale = 100
    suffix = ' cm'
    num_size = 20

    display_distance_between_two_points(region, rv3d, startloc3d, endloc3d)
    NP020FP.dist = display_distance_between_two_points(region, rv3d, startloc3d, endloc3d)[1]

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    # np_print('7')
    np_print('04_callback_TRANS_END')


def scene_update(context):
    # np_print('00_scene_update_START')
    # np_print('up1')
    if bpy.data.objects.is_updated:
        phase = NP020FP.phase
        flag = NP020FP.flag
        np_print(flag)
        start = NP020FP.start
        end = NP020FP.end
        if phase == 1:
            # np_print('up2')
            startloc3d = start.location
            endloc3d = end.location
            NP020FP.startloc3d = startloc3d
            NP020FP.endloc3d = endloc3d
        if flag == 'EXTRUDE':
            polyob = NP020FP.polyob
            polyme = polyob.data
            i = len(polyme.vertices)
            np_print('A')
            np_print('i', i)
            j = i / 2
            j = int(j)
            np_print(i, j)
            np_print(polyme.vertices[0].co)
            NP020FP.startloc3d = polyme.vertices[0].co
            NP020FP.endloc3d = polyme.vertices[j].co
            np_print('Ss3d, Se3d', NP020FP.startloc3d, NP020FP.endloc3d)
    # np_print('up3')
    # np_print('00_scene_update_END')


# Defining the operator that will let the user translate start and end to the desired point.
#  It also uses some listening operators that clean up the leftovers should the user interrupt the command.
# Many thanks to CoDEmanX and lukas_t:

class NPFPRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_fp_run_translate'
    bl_label = 'NP FP Run Translate'
    bl_options = {'INTERNAL'}

    np_print('04_run_TRANS_START')
    count = 0

    def modal(self, context, event):
        context.area.tag_redraw()
        self.count += 1
        selob = NP020FP.selob
        start = NP020FP.start
        end = NP020FP.end
        phase = NP020FP.phase
        polyob = NP020FP.polyob

        if self.count == 1:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            np_print('04_run_TRANS_count_1_INVOKE_DEFAULT')

        elif event.type in ('LEFTMOUSE', 'NUMPAD_ENTER') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020FP.flag = 'PASS'
            np_print('04_run_TRANS_left_release_FINISHED')
            return{'FINISHED'}

        elif event.type == 'RET' and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if bpy.context.tool_settings.snap_element == 'VERTEX':
                bpy.context.tool_settings.snap_element = 'EDGE'
                NP020FP.snap = 'EDGE'
            elif bpy.context.tool_settings.snap_element == 'EDGE':
                bpy.context.tool_settings.snap_element = 'FACE'
                NP020FP.snap = 'FACE'
            elif bpy.context.tool_settings.snap_element == 'FACE':
                bpy.context.tool_settings.snap_element = 'VERTEX'
                NP020FP.snap = 'VERTEX'
            NP020FP.flag = 'TRANSLATE'
            np_print('04_run_TRANS_enter_PASS')
            return{'FINISHED'}


        elif event.type == 'SPACE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            start.hide = True
            end.hide = True
            NP020FP.flag = 'NAVIGATE'
            np_print('04_run_TRANS_space_FINISHED_flag_NAVIGATE')
            return{'FINISHED'}

        elif event.type == 'RIGHTMOUSE' and phase > 1:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            end.location = start.location
            start.hide = True
            end.hide = True
            NP020FP.flag = 'CLOSE'
            np_print('04_run_TRANS_space_FINISHED_flag_NAVIGATE')
            return{'FINISHED'}

        elif event.type == 'RIGHTMOUSE' and phase < 2:
            # this actually begins when user RELEASES esc or rightmouse,
            # PRESS is taken by transform.translate operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.select_all(action='DESELECT')
            start.select = True
            end.select = True
            bpy.ops.object.delete('EXEC_DEFAULT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('04_run_TRANS_esc_right_CANCELLED')

        elif event.type == 'ESC':
            # this actually begins when user RELEASES esc or rightmouse,
            # PRESS is taken by transform.translate operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.select_all(action='DESELECT')
            start.select = True
            end.select = True
            bpy.ops.object.delete('EXEC_DEFAULT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('04_run_TRANS_esc_right_CANCELLED')
            return{'CANCELLED'}

        np_print('04_run_TRANS_PASS_THROUGH')
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        flag = NP020FP.flag
        np_print('04_run_TRANS_INVOKE_a')
        np_print('flag=', flag)
        if flag == 'TRANSLATE':
            if context.area.type == 'VIEW_3D':
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_TRANS, args,
                                                                      'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                np_print('04_run_TRANS_INVOKE_a_RUNNING_MODAL')
                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, "View3D not found, cannot run operator")
                np_print('04_run_TRANS_INVOKE_a_CANCELLED')
                return {'CANCELLED'}
        else:
            np_print('04_run_TRANS_INVOKE_a_FINISHED')
            return {'FINISHED'}


# Defining the operator that will draw the graphicall reprezentation of distance in navigation mode if user calls it:

def draw_callback_px_NAV(self, context):

    np_print('05_callback_NAV_START')

    addon_prefs = context.user_preferences.addons[__package__].preferences
    point_markers = addon_prefs.npfp_point_markers
    point_size = addon_prefs.npfp_point_size

    polyob = NP020FP.polyob
    phase = NP020FP.phase
    start = NP020FP.start
    end = NP020FP.end
    startloc3d = start.location
    endloc3d = end.location
    endloc = end.location
    region = context.region
    rv3d = context.region_data
    startloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)
    mouseloc = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc)  # is this used ?

    '''
    if addon_prefs.npfp_col_line_main_DEF is False:
        col_line_main = addon_prefs.npfp_col_line_main
    else:
        col_line_main = (1.0, 1.0, 1.0, 1.0)

    if addon_prefs.npfp_col_line_shadow_DEF is False:
        col_line_shadow = addon_prefs.npfp_col_line_shadow
    else:
        col_line_shadow = (0.1, 0.1, 0.1, 0.25)

    if addon_prefs.npfp_col_num_main_DEF is False:
        col_num_main = addon_prefs.npfp_col_num_main
    else:
        col_num_main = (0.1, 0.1, 0.1, 0.75)

    if addon_prefs.npfp_col_num_shadow_DEF is False:
        col_num_shadow = addon_prefs.npfp_col_num_shadow
    else:
        col_num_shadow = (1.0, 1.0, 1.0, 1.0)
    '''
    if addon_prefs.npfp_point_color_DEF is False:
        col_pointromb = addon_prefs.npfp_point_color
    else:
        col_pointromb = (0.15, 0.15, 0.15, 1.0)
    '''
    if addon_prefs.npfp_suffix == 'None':
        suffix = None

    elif addon_prefs.npfp_suffix in ('km', 'm', 'cm', 'mm', 'nm', 'thou'):
        suffix = ' '.join(addon_prefs.npfp_suffix)

    elif addon_prefs.npfp_suffix == "'":
        suffix = "'"

    elif addon_prefs.npfp_suffix == '"':
        suffix = '"'
    '''
    # Calculating the 3d points for the graphical line while in NAVIGATE flag:

    co2d = self.co2d
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
    pointloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector / 5

    np_print('phase=', phase)
    if phase == 0 or phase == 3:
        startloc3d = (0.0, 0.0, 0.0)
        endloc3d = (0.0, 0.0, 0.0)

    if phase == 1:
        startloc3d = NP020FP.startloc3d
        endloc3d = pointloc

    if phase == 2:
        startloc3d = NP020FP.startloc3d
        endloc3d = pointloc
    '''
    # Calculating the 2D points for the graphical line while in NAVIGATE flag from 3D points:

    startloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)

    if startloc2d is None:
        startloc2d = (0.0, 0.0)
        endloc2d = (0.0, 0.0)
    np_print(startloc2d, endloc2d)

    dist = (Vector(endloc3d) - Vector(startloc3d))
    dist = dist.length * scale
    np_print(dist)

    if suffix is not None:
        dist = str(abs(round(dist, 2))) + suffix
    else:
        dist = str(abs(round(dist, 2)))

    NP020FP.dist = dist
    np_print(dist)

    # This is for correcting the position of the numerical on the screen if the endpoints are far out of screen:
    numloc = []
    startx = startloc2d[0]
    starty = startloc2d[1]
    endx = endloc2d[0]
    endy = endloc2d[1]
    if startx > region.width:
        startx = region.width
    if startx < 0:
        startx = 0
    if starty > region.height:
        starty = region.height
    if starty < 0:
        starty = 0
    if endx > region.width:
        endx = region.width
    if endx < 0:
        endx = 0
    if endy > region.height:
        endy = region.height
    if endy < 0:
        endy = 0
    numloc.append((startx + endx) / 2)
    numloc.append((starty + endy) / 2)
    '''


    # Drawing:

    bgl.glEnable(bgl.GL_BLEND)
    font_id = 0
    # LINE:


    display_line_between_two_points(region, rv3d, startloc3d, endloc3d)

    '''
    bgl.glColor4f(*col_line_shadow)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f((startloc2d[0] - 1), (startloc2d[1] - 1))
    bgl.glVertex2f((endloc2d[0] - 1), (endloc2d[1] - 1))
    bgl.glEnd()

    bgl.glColor4f(*col_line_main)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*startloc2d)
    bgl.glVertex2f(*endloc2d)
    bgl.glEnd()
    '''


    # POINT MARKERS:
    markersize = point_size
    triangle = [[0, 0], [-1, 1], [1, 1]]
    romb = [[-1, 0], [0, 1], [1, 0], [0, -1]]  # is this used ?
    if phase > 0 and polyob is None and point_markers:
        polylist2d = []
        for co in triangle:
            co[0] = round((co[0] * markersize * 3), 0) + startloc2d[0]
            co[1] = round((co[1] * markersize * 3), 0) + startloc2d[1]
        np_print('triangle', triangle)
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in triangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        pointromb = [[-1, 0], [0, 1], [1, 0], [0, -1]]

        for co in pointromb:
            co[0] = round((co[0] * markersize), 0) + endloc2d[0]
            co[1] = round((co[1] * markersize), 0) + endloc2d[1]

        if phase == 2:
            np_print('pointromb', pointromb)
            bgl.glColor4f(*col_pointromb)
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for x, y in pointromb:
                bgl.glVertex2f(x, y)
            bgl.glEnd()

    if polyob is not None and point_markers:
        np_print('polyob not None')
        polyloc = polyob.location
        polyme = polyob.data
        polylist3d = []

        for me in polyme.vertices:
            polylist3d.append(me.co + polyloc)
        np_print('polylist3d = ', polylist3d)
        polylist2d = []

        for p3d in polylist3d:
            p2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p3d)
            polylist2d.append(p2d)

        np_print('polylist2d = ', polylist2d)

        # triangle for the first point
        for co in triangle:
            co[0] = round((co[0] * markersize * 3), 0) + polylist2d[0][0]
            co[1] = round((co[1] * markersize * 3), 0) + polylist2d[0][1]
        np_print('triangle', triangle)
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in triangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        # rombs for the other points
        i = 0
        for p2d in polylist2d:
            if i > 0:
                pointromb = [[-1, 0], [0, 1], [1, 0], [0, -1]]
                for co in pointromb:
                    co[0] = round((co[0] * markersize), 0) + p2d[0]
                    co[1] = round((co[1] * markersize), 0) + p2d[1]
                np_print('pointromb', pointromb)
                bgl.glColor4f(*col_pointromb)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                for x, y in pointromb:
                    bgl.glVertex2f(x, y)
            i = i + 1
            bgl.glEnd()


    # ON-SCREEN INSTRUCTIONS:

    if phase == 0:
        main = 'navigate for better placement of start point'

    if phase == 1:
        main = 'navigate for better placement of next point'

    if phase == 2:
        main = 'navigate for better placement of next point'

    if phase == 3:
        main = 'navigate for better placement of extrusion height'

    region = bpy.context.region
    rv3d = bpy.context.region_data
    instruct = main
    keys_aff = 'MMB, SCROLL - navigate'
    keys_nav = 'LMB, SPACE - leave navigate'
    keys_neg = 'ESC, RMB - quit'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)

    font_id = 0

    # Drawing the small badge near the cursor with the basic instructions:

    symbol = copy.deepcopy(NP020FP.polysymbol)
    badge_mode = 'NAV'
    message_main = 'NAVIGATE'
    message_aux = None
    aux_num = None
    aux_str = None


    display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str)

    '''
    if badge is True:
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        polysymbol = copy.deepcopy(NP020FP.polysymbol)
        ipx = 29
        ipy = 33
        size = badge_size
        for co in square:
            co[0] = round((co[0] * size), 0) - (size * 10) + co2d[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + co2d[1]
        for co in rectangle:
            co[0] = round((co[0] * size), 0) - (size * 10) + co2d[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + co2d[1]
        for co in polysymbol:
            co[0] = round((co[0] * size), 0) - (size * 10) + co2d[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + co2d[1]

        ipx = round((ipx * size), 0) - (size * 10) + co2d[0]
        ipy = round((ipy * size), 0) - (size * 25) + co2d[1]
        ipsize = int(6 * size)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(0.5, 0.75, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in rectangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)

        for x, y in polysymbol:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ipx, ipy, 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, 'NAVIGATE')
    '''
    # NUMERICAL DISTANCE:

    '''
    bgl.glColor4f(*col_num_shadow)
    if phase > 0:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, (numloc[0] - 1), (numloc[1] - 1), 0)
        blf.draw(font_id, dist)

    bgl.glColor4f(*col_num_main)
    if phase > 0:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, numloc[0], numloc[1], 0)
        blf.draw(font_id, dist)
    '''

    region = bpy.context.region
    rv3d = bpy.context.region_data
    dist_scale = 100
    suffix = ' cm'
    num_size = 20

    display_distance_between_two_points(region, rv3d, startloc3d, endloc3d)


    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('05_callback_NAV_END')


# Defining the operator that will enable navigation if user calls it:

class NPFPRunNavigate(bpy.types.Operator):
    bl_idname = "object.np_fp_run_navigate"
    bl_label = "NP FP Run Navigate"
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        np_print('05_run_NAV_START')
        context.area.tag_redraw()
        selob = NP020FP.selob
        start = NP020FP.start
        end = NP020FP.end
        phase = NP020FP.phase
        polyob = NP020FP.polyob

        if event.type == 'MOUSEMOVE':
            np_print('05_run_NAV_mousemove_a')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            np_print('05_run_NAV_mousemove_b')

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            np_print('05_run_NAV_left_space_press_START')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            phase = NP020FP.phase
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            pointloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector / 5
            start = NP020FP.start
            end = NP020FP.end
            start.hide = False
            end.hide = False
            np_print('phase=', phase)
            if phase == 0:
                startloc3d = (0.0, 0.0, 0.0)
                endloc3d = (0.0, 0.0, 0.0)
                start.location = pointloc
                end.location = pointloc
                NP020FP.flag = 'TRANSLATE'
            if phase == 1:
                startloc3d = NP020FP.startloc3d
                endloc3d = pointloc
                end.location = pointloc
                NP020FP.flag = 'TRANSLATE'
            if phase == 2:
                startloc3d = NP020FP.startloc3d
                endloc3d = pointloc
                end.location = pointloc
                NP020FP.flag = 'TRANSLATE'
            if phase == 3:
                startloc3d = (0.0, 0.0, 0.0)
                endloc3d = (0.0, 0.0, 0.0)
                start.location = pointloc
                end.location = pointloc
                NP020FP.flag = 'EXTRUDE'
                """
            if phase == 3.5:
                startloc3d=(0.0,0.0,0.0)
                endloc3d=(0.0,0.0,0.0)
                start.location = pointloc
                end.location = pointloc
                NP020FP.flag = 'EXTRUDE'
                """
            NP020FP.start = start
            NP020FP.end = end
            NP020FP.startloc3d = startloc3d
            NP020FP.endloc3d = endloc3d

            np_print('05_run_NAV_left_space_press_FINISHED_flag_TRANSLATE')
            return {'FINISHED'}

        elif event.type == 'ESC':
            np_print('05_run_NAV_esc_right_any_START')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.select_all(action='DESELECT')
            start.hide = False
            end.hide = False
            start.select = True
            end.select = True
            bpy.ops.object.delete('EXEC_DEFAULT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient

            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('05_run_NAV_esc_right_any_CANCELLED')
            return{'CANCELLED'}

        elif event.type == 'RIGHTMOUSE' and phase > 1:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            end.location = start.location
            start.hide = True
            end.hide = True
            NP020FP.flag = 'CLOSE'
            np_print('04_run_TRANS_space_FINISHED_flag_NAVIGATE')
            return{'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('05_run_NAV_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}
        np_print('05_run_NAV_RUNNING_MODAL')
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('05_run_NAV_INVOKE_a')
        flag = NP020FP.flag
        phase = NP020FP.phase  # is this used ?
        np_print('flag=', flag)
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag == 'NAVIGATE':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_NAV, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('05_run_NAV_INVOKE_a_RUNNING_MODAL')
            return {'RUNNING_MODAL'}
        else:
            np_print('05_run_NAV_INVOKE_a_FINISHED')
            return {'FINISHED'}


# Changing the mode of operating and leaving start point at the first snap, continuing with just the end point:

class NPFPChangePhase(bpy.types.Operator):
    bl_idname = "object.np_fp_change_phase"
    bl_label = "NP FP Change Phase"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('06_change_phase_START')
        NP020FP.phase = 1
        np_print('NP020FP.phase=', NP020FP.phase)
        start = NP020FP.start
        end = NP020FP.end
        startloc3d = start.location
        endloc3d = end.location
        NP020FP.startloc3d = startloc3d
        NP020FP.endloc3d = endloc3d
        bpy.ops.object.select_all(action='DESELECT')
        end.select = True
        NP020FP.snap = NP020FP.snap
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = NP020FP.snap
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        NP020FP.flag = 'TRANSLATE'
        np_print('06_change_phase_END_flag_TRANSLATE')
        return {'FINISHED'}


# Changing the mode of operating and leaving start point at the first snap, continuing with just the end point:

class NPFPMakeSegment(bpy.types.Operator):
    bl_idname = "object.np_fp_make_segment"
    bl_label = "NP FP Make Segment"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__package__].preferences
        wire = addon_prefs.npfp_wire
        smooth = addon_prefs.npfp_smooth  # is this used ?
        material = addon_prefs.npfp_material

        flag = NP020FP.flag
        if flag == 'SURFACE':
            return {'FINISHED'}
        np_print('08_make_segment_START')
        np_print('NP020FP.phase =', NP020FP.phase)
        polyob = NP020FP.polyob
        start = NP020FP.start
        end = NP020FP.end
        startloc3d = start.location
        endloc3d = end.location
        if NP020FP.phase < 2:
            polyverts = []
            polyverts.append(startloc3d)
            polyverts.append(endloc3d)
            polyedges = []
            polyedges.append((1, 0))
            polyfaces = []
            polyme = bpy.data.meshes.new('float_poly')
            polyme.from_pydata(polyverts, polyedges, polyfaces)
            polyob = bpy.data.objects.new('float_poly', polyme)
            polyob.location = mathutils.Vector((0, 0, 0))
            scn = bpy.context.scene
            scn.objects.link(polyob)
            scn.objects.active = polyob
            scn.update()
            bpy.ops.object.select_all(action='DESELECT')
            polyob.select = True
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            if wire:
                polyob.show_wire = True
            if material:
                mtl = bpy.data.materials.new('float_poly_material')
                mtl.diffuse_color = (1.0, 1.0, 1.0)
                polyme.materials.append(mtl)
            activelayer = bpy.context.scene.active_layer
            np_print('activelayer:', activelayer)
            layers = [False, False, False, False, False, False, False, False, False, False,
                      False, False, False, False, False, False, False, False, False, False]
            layers[activelayer] = True
            layers = tuple(layers)
            np_print(layers)
            bpy.ops.object.move_to_layer(layers=layers)
            bpy.ops.object.select_all(action='DESELECT')
            NP020FP.polyob = polyob
        else:
            polyme = polyob.data
            bm = bmesh.new()
            bm.from_mesh(polyme)
            vco = endloc3d - polyob.location
            bmesh.ops.create_vert(bm, co=vco)
            i = len(bm.verts)
            bm.verts.ensure_lookup_table()
            if flag == 'CLOSE':
                verts = [bm.verts[i - 1], bm.verts[0]]
                NP020FP.flag = 'SURFACE'
            else:
                verts = [bm.verts[i - 1], bm.verts[i - 2]]
            bmesh.ops.contextual_create(bm, geom=verts)
            bm.to_mesh(polyme)
            bm.free()
            bpy.ops.object.select_all(action='DESELECT')
            polyob.select = True
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            NP020FP.polyob = polyob
        bpy.context.scene.objects.active = polyob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.objects.active = end
        start.location = endloc3d
        end.location = endloc3d
        bpy.ops.object.select_all(action='DESELECT')
        end.select = True
        NP020FP.start = start
        NP020FP.end = end
        NP020FP.phase = 2
        NP020FP.selob = polyob
        NP020FP.acob = polyob
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = NP020FP.snap
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        if flag not in {'CLOSE', 'SURFACE'}:
            NP020FP.flag = 'TRANSLATE'
        np_print('08_make_segment_END_flag_TRANSLATE')
        return {'FINISHED'}


# Deleting the anchors after succesfull translation and reselecting previously selected objects:

class NPFPDeletePoints(bpy.types.Operator):
    bl_idname = "object.np_fp_delete_points"
    bl_label = "NP FP Delete Points"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__package__].preferences  # is this used ?
        dist = NP020FP.dist  # is this used ?
        polyob = NP020FP.polyob
        np_print('07_delete_points_START')

        selob = NP020FP.selob
        start = NP020FP.start
        end = NP020FP.end
        bpy.ops.object.select_all(action='DESELECT')
        start.hide = False
        end.hide = False
        start.select = True
        end.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')
        if selob is not polyob:
            for ob in selob:
                ob.select = True
        else:
            polyob.select = True
        NP020FP.startloc3d = (0.0, 0.0, 0.0)
        NP020FP.endloc3d = (0.0, 0.0, 0.0)
        NP020FP.phase = 0
        NP020FP.flag = 'SURFACE'
        NP020FP.start = None
        NP020FP.end = None
        NP020FP.dist = None
        NP020FP.polyverts = []
        NP020FP.polyedges = []
        NP020FP.snap = 'VERTEX'
        bpy.context.tool_settings.use_snap = NP020FP.use_snap
        bpy.context.tool_settings.snap_element = NP020FP.snap_element
        bpy.context.tool_settings.snap_target = NP020FP.snap_target
        bpy.context.space_data.pivot_point = NP020FP.pivot_point
        bpy.context.space_data.transform_orientation = NP020FP.trans_orient
        if NP020FP.acob is not None:
            bpy.context.scene.objects.active = NP020FP.acob
            bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
        return {'FINISHED'}


# Creating a surface on the closed polyline:

class NPFPMakeSurface(bpy.types.Operator):
    bl_idname = "object.np_fp_make_surface"
    bl_label = "NP FP Make Surface"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__package__].preferences
        smooth = addon_prefs.npfp_smooth
        dist = NP020FP.dist  # is this used ?
        polyob = NP020FP.polyob
        polyme = polyob.data
        bm = bmesh.new()
        bm.from_mesh(polyme)
        bmesh.ops.contextual_create(bm, geom=bm.edges)
        bm.to_mesh(polyme)
        bm.free()
        bpy.ops.object.select_all(action='DESELECT')
        polyob.select = True
        if smooth:
            bpy.ops.object.shade_smooth()
            np_print('smooth ON')
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        bpy.ops.object.select_all(action='DESELECT')
        NP020FP.flag = 'EXTRUDE'
        NP020FP.phase = 3
        return {'FINISHED'}


def draw_callback_px_NAVEX(self, context):

    np_print('08_callback_NAVEX_START')

    addon_prefs = context.user_preferences.addons[__package__].preferences

    #scale = addon_prefs.npfp_scale  # is this used ?
    #badge = addon_prefs.npfp_badge
    #point_size = addon_prefs.npfp_point_size  # is this used ?
    #badge_size = addon_prefs.npfp_badge_size

    #polyob = NP020FP.polyob  # is this used ?
    #phase = NP020FP.phase  # is this used ?
    #region = context.region  # is this used ?
    #rv3d = context.region_data  # is this used ?
    co2d = self.co2d

    if addon_prefs.npfp_col_line_main_DEF is False:
        col_line_main = addon_prefs.npfp_col_line_main  # is this used ?
    else:
        col_line_main = (1.0, 1.0, 1.0, 1.0)  # is this used ?

    if addon_prefs.npfp_col_line_shadow_DEF is False:
        col_line_shadow = addon_prefs.npfp_col_line_shadow  # is this used ?
    else:
        col_line_shadow = (0.1, 0.1, 0.1, 0.25)  # is this used ?

    if addon_prefs.npfp_col_num_main_DEF is False:
        col_num_main = addon_prefs.npfp_col_num_main  # is this used ?
    else:
        col_num_main = (0.1, 0.1, 0.1, 0.75)  # is this used ?

    if addon_prefs.npfp_col_num_shadow_DEF is False:
        col_num_shadow = addon_prefs.npfp_col_num_shadow  # is this used ?
    else:
        col_num_shadow = (1.0, 1.0, 1.0, 1.0)  # is this used ?

    if addon_prefs.npfp_point_color_DEF is False:
        col_pointromb = addon_prefs.npfp_point_color  # is this used ?
    else:
        col_pointromb = (0.3, 0.3, 0.3, 1.0)  # is this used ?

    '''
    if addon_prefs.npfp_suffix == 'None':
        suffix = None  # is this used ?

    elif addon_prefs.npfp_suffix in ('km', 'm', 'cm', 'mm', 'nm', 'thou'):
        suffix = ' '.join(addon_prefs.npfp_suffix)

    elif addon_prefs.npfp_suffix == "'":
        suffix = "'"  # is this used ?

    elif addon_prefs.npfp_suffix == '"':
        suffix = '"'   # is this used ?
    '''
    # Calculating the 3d points for the graphical line while in NAVIGATE flag:

    """

    np_print('phase=', phase)
    if phase == 0 or phase == 3:
        startloc3d=(0.0,0.0,0.0)
        endloc3d=(0.0,0.0,0.0)

    if phase == 1:
        startloc3d = NP020FP.startloc3d
        endloc3d = pointloc

    if phase == 2:
        startloc3d = NP020FP.startloc3d
        endloc3d = pointloc
    """
    # Calculating the 2D points for the graphical line while in NAVIGATE flag from 3D points:
    """
    startloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)

    if startloc2d == None:
        startloc2d=(0.0,0.0)
        endloc2d=(0.0,0.0)
    np_print(startloc2d, endloc2d)

    dist = (Vector(endloc3d) - Vector(startloc3d))
    dist = dist.length*scale
    np_print(dist)

    if suffix is not None:
        dist = str(abs(round(dist,2))) + suffix
    else:
        dist = str(abs(round(dist,2)))

    NP020FP.dist = dist
    np_print(dist)

    #This is for correcting the position of the numerical on the screen if the endpoints are far out of screen:
    numloc = []
    startx=startloc2d[0]
    starty=startloc2d[1]
    endx=endloc2d[0]
    endy=endloc2d[1]
    if startx > region.width:
        startx = region.width
    if startx < 0:
        startx = 0
    if starty > region.height:
        starty = region.height
    if starty < 0:
        starty = 0
    if endx > region.width:
        endx = region.width
    if endx < 0:
        endx = 0
    if endy > region.height:
        endy = region.height
    if endy < 0:
        endy = 0
    numloc.append((startx+endx)/2)
    numloc.append((starty+endy)/2)

    if phase==0:
        main='NAVIGATE FOR BETTER PLACEMENT OF START POINT'

    if phase==1:
        main='NAVIGATE FOR BETTER PLACEMENT OF NEXT POINT'

    if phase==2:
        main='NAVIGATE FOR BETTER PLACEMENT OF NEXT POINT'

    if phase==3:
        main='NAVIGATE FOR BETTER PLACEMENT OF EXTRUSION HEIGHT'


    #Drawing:

    bgl.glEnable(bgl.GL_BLEND)

    #LINE:

    bgl.glColor4f(*col_line_shadow)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f((startloc2d[0]-1),(startloc2d[1]-1))
    bgl.glVertex2f((endloc2d[0]-1),(endloc2d[1]-1))
    bgl.glEnd()

    bgl.glColor4f(*col_line_main)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*startloc2d)
    bgl.glVertex2f(*endloc2d)
    bgl.glEnd()

    #POINT MARKERS:
    markersize = point_size
    triangle = [[0, 0], [-1, 1], [1, 1]]
    romb = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    if phase > 0 and polyob is None:
        polylist2d = []
        for co in triangle:
            co[0] = round((co[0] * markersize * 3),0) + startloc2d[0]
            co[1] = round((co[1] * markersize * 3),0) + startloc2d[1]
        np_print('triangle', triangle)
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in triangle:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        pointromb = [[-1, 0], [0, 1], [1, 0], [0, -1]]
        for co in pointromb:
            co[0] = round((co[0] * markersize),0) + endloc2d[0]
            co[1] = round((co[1] * markersize),0) + endloc2d[1]
        if phase == 2:
            np_print('pointromb', pointromb)
            bgl.glColor4f(*col_pointromb)
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for x,y in pointromb:
                bgl.glVertex2f(x,y)
            bgl.glEnd()
    if polyob is not None:
        np_print('polyob not None')
        polyloc = polyob.location
        polyme = polyob.data
        polylist3d = []
        for me in polyme.vertices:
            polylist3d.append(me.co + polyloc)
        np_print('polylist3d = ', polylist3d)
        polylist2d = []
        for p3d in polylist3d:
            p2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p3d)
            polylist2d.append(p2d)
        np_print('polylist2d = ', polylist2d)
        #triangle for the first point
        for co in triangle:
            co[0] = round((co[0] * markersize * 3),0) + polylist2d[0][0]
            co[1] = round((co[1] * markersize * 3),0) + polylist2d[0][1]
        np_print('triangle', triangle)
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in triangle:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        #rombs for the other points
        i = 0
        for p2d in polylist2d:
            if i > 0:
                pointromb = [[-1, 0], [0, 1], [1, 0], [0, -1]]
                for co in pointromb:
                    co[0] = round((co[0] * markersize),0) + p2d[0]
                    co[1] = round((co[1] * markersize),0) + p2d[1]
                np_print('pointromb', pointromb)
                bgl.glColor4f(*col_pointromb)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                for x,y in pointromb:
                    bgl.glVertex2f(x,y)
            i = i + 1
            bgl.glEnd()

    #NUMERICAL DISTANCE:

    bgl.glColor4f(*col_num_shadow)
    if phase > 0:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, (numloc[0]-1), (numloc[1]-1), 0)
        blf.draw(font_id, dist)

    bgl.glColor4f(*col_num_main)
    if phase > 0:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, numloc[0], numloc[1], 0)
        blf.draw(font_id, dist)

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    """
    # ON-SCREEN INSTRUCTIONS:

    main = 'navigate for better placement of extrusion height'

    # ON-SCREEN INSTRUCTIONS:

    region = bpy.context.region
    rv3d = bpy.context.region_data
    instruct = main
    keys_aff = 'MMB, SCROLL - navigate'
    keys_nav = 'LMB, SPACE - leave navigate'
    keys_neg = 'ESC, RMB - quit'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    font_id = 0

    # Drawing the small badge near the cursor with the basic instructions:

    if badge is True:
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        polysymbol = copy.deepcopy(NP020FP.polysymbol)
        ipx = 29
        ipy = 33
        size = badge_size
        for co in square:
            co[0] = round((co[0] * size), 0) - (size * 10) + co2d[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + co2d[1]
        for co in rectangle:
            co[0] = round((co[0] * size), 0) - (size * 10) + co2d[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + co2d[1]
        for co in polysymbol:
            co[0] = round((co[0] * size), 0) - (size * 10) + co2d[0]
            co[1] = round((co[1] * size), 0) - (size * 25) + co2d[1]

        ipx = round((ipx * size), 0) - (size * 10) + co2d[0]
        ipy = round((ipy * size), 0) - (size * 25) + co2d[1]
        ipsize = int(6 * size)
        bgl.glColor4f(0.0, 0.0, 0.0, 0.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(0.5, 0.75, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)

        for x, y in rectangle:
            bgl.glVertex2f(x, y)

        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)

        for x, y in polysymbol:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ipx, ipy, 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, 'NAVIGATE')

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('05_callback_NAVEX_END')


# Defining the operator that will draw the OpenGL the numerical distance and
# the on-screen instructions while the user extrudes the surface:

class NPFPRunNavEx(bpy.types.Operator):
    bl_idname = "object.np_fp_run_navex"
    bl_label = "NP FP Run NavEx"
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        np_print('05_run_NAVEX_START')
        context.area.tag_redraw()
        selob = NP020FP.selob
        phase = NP020FP.phase

        if event.type == 'MOUSEMOVE':
            np_print('05_run_NAVEX_mousemove_a')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            np_print('05_run_NAVEX_mousemove_b')

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            np_print('05_run_NAVEX_left_space_press_START')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            pointloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector / 5  # is this used ?
            np_print('phase=', phase)
            NP020FP.flag = 'EXTRUDE'
            np_print('05_run_NAVEX_left_space_press_FINISHED_flag_TRANSLATE')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            np_print('05_run_NAVEX_esc_right_any_START')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            # XXX selob and polyob are undefined
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True

            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('05_run_NAVEX_esc_right_any_CANCELLED')
            return{'CANCELLED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('05_run_NAVEX_middle_any_PASS_THROUGH')
            return {'PASS_THROUGH'}

        np_print('05_run_NAVEX_RUNNING_MODAL')
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('05_run_NAVEX_a')
        flag = NP020FP.flag
        np_print('flag=', flag)
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag == 'NAVEX':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_NAVEX, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            np_print('05_run_NAVEX_INVOKE_a_FINISHED')
            return {'FINISHED'}


def draw_callback_px_EXTRUDE(self, context):

    np_print('10_callback_EXTRUDE_START')

    addon_prefs = context.user_preferences.addons[__package__].preferences
    #scale = addon_prefs.npfp_scale
    #badge = addon_prefs.npfp_badge  # is this used ?
    #point_size = addon_prefs.npfp_point_size  # is this used ?
    #badge_size = addon_prefs.npfp_badge_size  # is this used ?

    '''
    if addon_prefs.npfp_col_line_main_DEF is False:
        col_line_main = addon_prefs.npfp_col_line_main  # is this used ?
    else:
        col_line_main = (1.0, 1.0, 1.0, 1.0)  # is this used ?

    if addon_prefs.npfp_col_line_shadow_DEF is False:
        col_line_shadow = addon_prefs.npfp_col_line_shadow  # is this used ?
    else:
        col_line_shadow = (0.1, 0.1, 0.1, 0.25)  # is this used ?

    if addon_prefs.npfp_col_num_main_DEF is False:
        col_num_main = addon_prefs.npfp_col_num_main  # is this used ?
    else:
        col_num_main = (0.1, 0.1, 0.1, 0.75)  # is this used ?

    if addon_prefs.npfp_col_num_shadow_DEF is False:
        col_num_shadow = addon_prefs.npfp_col_num_shadow  # is this used ?
    else:
        col_num_shadow = (1.0, 1.0, 1.0, 1.0)  # is this used ?

    if addon_prefs.npfp_point_color_DEF is False:
        col_pointromb = addon_prefs.npfp_point_color  # is this used ?
    else:
        col_pointromb = (0.3, 0.3, 0.3, 1.0)  # is this used ?


    if addon_prefs.npfp_suffix == 'None':
        suffix = None

    elif addon_prefs.npfp_suffix in ('km', 'm', 'cm', 'mm', 'nm', 'thou'):
        suffix = ' '.join(addon_prefs.npfp_suffix)

    elif addon_prefs.npfp_suffix == "'":
        suffix = "'"

    elif addon_prefs.npfp_suffix == '"':
        suffix = '"'
    '''
    # np_print('0')
    # sel = bpy.context.selected_objects
    flag = NP020FP.flag
    polyob = NP020FP.polyob
    polyme = polyob.data
    i = len(polyme.vertices)
    np_print('extrude_callback')
    np_print('i', i)
    j = i / 2
    j = int(j)
    np_print(i, j)
    np_print(polyme.vertices[0].co)
    startloc3d = polyme.vertices[0].co
    endloc3d = polyme.vertices[j].co
    np_print('Ss3d, Se3d', startloc3d, endloc3d)
    region = context.region
    rv3d = context.region_data



    '''
    startloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)
    np_print(startloc2d, endloc2d)
    # np_print('1')

    dist = (mathutils.Vector(endloc3d) - mathutils.Vector(startloc3d))
    dist = dist.length * scale
    np_print('dist =', dist)
    if suffix is not None:
        dist = str(abs(round(dist, 2))) + suffix
    else:
        dist = str(abs(round(dist, 2)))
    np_print('dist =', dist)
    NP020FP.dist = dist
    # np_print('2')
    # This is for correcting the position of the numerical on the screen if the endpoints are far out of screen:
    numloc = []
    startx = startloc2d[0]
    starty = startloc2d[1]
    endx = endloc2d[0]
    endy = endloc2d[1]
    if startx > region.width:
        startx = region.width
    if startx < 0:
        startx = 0
    if starty > region.height:
        starty = region.height
    if starty < 0:
        starty = 0
    if endx > region.width:
        endx = region.width
    if endx < 0:
        endx = 0
    if endy > region.height:
        endy = region.height
    if endy < 0:
        endy = 0
    numloc.append((startx + endx) / 2)
    numloc.append((starty + endy) / 2)
    # np_print('3')
    '''

    # Drawing:
    """
    bgl.glEnable(bgl.GL_BLEND)

    #LINE:

    bgl.glColor4f(*col_line_shadow)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f((startloc2d[0]-1),(startloc2d[1]-1))
    bgl.glVertex2f((endloc2d[0]-1),(endloc2d[1]-1))
    bgl.glEnd()

    bgl.glColor4f(*col_line_main)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*startloc2d)
    bgl.glVertex2f(*endloc2d)
    bgl.glEnd()
    #np_print('4')
    #NUMERICAL DISTANCE:

    np_print('numloc = ' ,numloc, 'dist = ', dist)

    bgl.glColor4f(*col_num_shadow)
    font_id = 0
    blf.size(font_id, 20, 72)
    blf.position(font_id, (numloc[0]-1), (numloc[1]-1), 0)
    blf.draw(font_id, dist)

    bgl.glColor4f(*col_num_main)
    font_id = 0
    blf.size(font_id, 20, 72)
    blf.position(font_id, numloc[0], numloc[1], 0)
    blf.draw(font_id, dist)

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    """
    # np_print('5')

    # ON-SCREEN INSTRUCTIONS:


    if flag == 'BEVEL':
        main = 'specify bevel amount'
    else:
        main = 'specify extrusion height'

    region = bpy.context.region
    rv3d = bpy.context.region_data
    instruct = main

    if flag == 'BEVEL':
        keys_aff = 'LMB, ENTER - confirm, SCROLL - num of segments, M - mode, C - clamp overlap, NUMPAD - value'
        keys_nav = ''
        keys_neg = 'ESC, RMB - cancel bevel'

    else:
        keys_aff = 'CTRL - snap, LMB - confirm, ENTER - confirm without bevel, MMB - lock axis, NUMPAD - value'
        keys_nav = 'SPACE - change to navigate'
        keys_neg = 'ESC, RMB - cancel extrusion'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    # ON-SCREEN INSTRUCTIONS:

    font_id = 0


    # Drawing the small badge near the cursor with the basic instructions:
    mouseloc = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)  # is this used ?
    # np_print(end, endloc, mouseloc)
    '''
    if badge == True:
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        polysymbol = copy.deepcopy(NP020FP.polysymbol)
        size = 2
        ipx = 29
        ipy = 33
        size = badge_size
        for co in square:
            co[0] = round((co[0] * size),0) -(size*10) + mouseloc[0]
            co[1] = round((co[1] * size),0) -(size*25) + mouseloc[1]
        for co in rectangle:
            co[0] = round((co[0] * size),0) -(size*10) + mouseloc[0]
            co[1] = round((co[1] * size),0) -(size*25) + mouseloc[1]
        for co in polysymbol:
            co[0] = round((co[0] * size),0) -(size*10) + mouseloc[0]
            co[1] = round((co[1] * size),0) -(size*25) + mouseloc[1]
        ipx = round((ipx * size),0) -(size*10) + mouseloc[0]
        ipy = round((ipy * size),0) -(size*25) + mouseloc[1]
        ipsize = int(6*size)
        bgl.glColor4f(0.0, 0.0, 0.0, 0.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in square:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in rectangle:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x,y in polysymbol:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id,ipx,ipy,0)
        blf.size(font_id,ipsize,72)
        blf.draw(font_id,'CTRL+SNAP')

    '''
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    # np_print('7')
    np_print('10_callback_EXTRUDE_END')


class NPFPRunExtrude(bpy.types.Operator):
    bl_idname = 'object.np_fp_run_extrude'
    bl_label = 'NP FP Run Extrude'
    bl_options = {'INTERNAL'}

    np_print('10_run_EXTRUDE_START')
    count = 0

    def modal(self, context, event):
        context.area.tag_redraw()
        self.count += 1
        selob = NP020FP.selob
        flag = NP020FP.flag  # is this used ?
        polyob = NP020FP.polyob
        phase = NP020FP.phase

        if self.count == 1:

            if phase == 3:
                bpy.ops.view3d.edit_mesh_extrude_move_normal('INVOKE_DEFAULT')
            else:
                bpy.ops.transform.translate('INVOKE_DEFAULT',
                                            constraint_axis=(False, False, True),
                                            constraint_orientation='NORMAL')

            np_print('B')
            np_print('10_run_EXTRUDE_count_1_INVOKE_DEFAULT')

        elif event.type in ('LEFTMOUSE', 'NUMPAD_ENTER') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            polyob.select = True
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            polyob.select = False
            bpy.ops.object.mode_set(mode='EDIT')
            NP020FP.flag = 'BEVEL'
            np_print('10_run_EXTRUDE_left_release_FINISHED')
            return{'FINISHED'}

        elif event.type == 'SPACE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020FP.phase = 3.5
            NP020FP.flag = 'NAVEX'
            np_print('10_run_TRANS_space_FINISHED_flag_NAVIGATE')
            return{'FINISHED'}

        elif event.type == 'RET':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            polyob.select = True
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            bpy.ops.object.select_all(action='DESELECT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('10_run_EXTRUDE_space_FINISHED_flag_TRANSLATE')
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
            # this actually begins when user RELEASES esc or rightmouse,
            # PRESS is taken by transform.translate operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('10_run_EXTRUDE_space_CANCELLED_flag_TRANSLATE')
            return{'CANCELLED'}

        np_print('10_run_EXTRUDE_PASS_THROUGH')
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('10_run_EXTRUDE_INVOKE_a')

        selob = NP020FP.selob  # is this used ?
        flag = NP020FP.flag
        np_print('flag = ', flag)
        polyob = NP020FP.polyob

        if flag == 'EXTRUDE':
            if context.area.type == 'VIEW_3D':
                if bpy.context.mode == 'OBJECT':
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.scene.objects.active = polyob
                    polyob.select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    polyme = polyob.data
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles()
                    i = len(polyme.vertices)
                    i = int(i / 2)
                    NP020FP.startloc3d = polyme.vertices[0].co
                    NP020FP.startloc3d = polyme.vertices[i].co
                if bpy.context.mode == 'EDIT':
                    polyme = polyob.data
                    i = len(polyme.vertices)
                    i = int(i / 2)
                    NP020FP.startloc3d = polyme.vertices[0].co
                    NP020FP.startloc3d = polyme.vertices[i].co
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_EXTRUDE, args,
                                                                      'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)

                np_print('10_run_EXTRUDE_INVOKE_a_RUNNING_MODAL')
                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, "View3D not found, cannot run operator")
                np_print('10_run_EXTRUDE_INVOKE_a_CANCELLED')
                return {'CANCELLED'}
        else:
            np_print('10_run_EXTRUDE_INVOKE_a_FINISHED')
            return {'FINISHED'}


class NPFPRunBevel(bpy.types.Operator):
    bl_idname = 'object.np_fp_run_bevel'
    bl_label = 'NP FP Run Bevel'
    bl_options = {'INTERNAL'}

    np_print('11_run_BEVEL_START')
    count = 0

    def modal(self, context, event):
        context.area.tag_redraw()
        self.count += 1
        selob = NP020FP.selob
        flag = NP020FP.flag  # is this used ?
        polyob = NP020FP.polyob

        if self.count == 1:

            bpy.ops.mesh.bevel('INVOKE_DEFAULT')

            np_print('B')
            np_print('11_run_BEVEL_count_1_INVOKE_DEFAULT')

        elif event.type in ('LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            NP020FP.flag = 'TRANSLATE'
            bpy.ops.object.select_all(action='DESELECT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('10_run_EXTRUDE_left_release_FINISHED')
            return{'FINISHED'}

        elif event.type in ('RIGHTMOUSE', 'ESC'):
            # this actually begins when user RELEASES esc or rightmouse,
            # PRESS is taken by transform.translate operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('11_run_BEVEL_esc_CANCELLED')
            return{'CANCELLED'}

        np_print('11_run_BEVEL_PASS_THROUGH')
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('11_run_BEVEL_INVOKE_a')
        addon_prefs = context.user_preferences.addons[__package__].preferences
        bevel = addon_prefs.npfp_bevel
        selob = NP020FP.selob
        flag = NP020FP.flag
        np_print('flag = ', flag)
        polyob = NP020FP.polyob

        if flag == 'BEVEL' and bevel:
            if context.area.type == 'VIEW_3D':
                bpy.context.scene.objects.active = polyob
                bpy.ops.mesh.select_all(action='SELECT')
                args = (self, context)
                NP020FP.main_BEVEL = 'DESIGNATE BEVEL AMOUNT'
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_EXTRUDE,
                                                                      args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                np_print('11_run_BEVEL_INVOKE_a_RUNNING_MODAL')
                return {'RUNNING_MODAL'}

            else:
                self.report({'WARNING'}, "View3D not found, cannot run operator")
                np_print('11_run_BEVEL_INVOKE_a_CANCELLED')
                return {'CANCELLED'}
        else:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            if selob is not polyob:
                for ob in selob:
                    ob.select = True
            else:
                polyob.select = True
            NP020FP.startloc3d = (0.0, 0.0, 0.0)
            NP020FP.endloc3d = (0.0, 0.0, 0.0)
            NP020FP.phase = 0
            NP020FP.start = None
            NP020FP.end = None
            NP020FP.dist = None
            NP020FP.polyob = None
            NP020FP.flag = 'TRANSLATE'
            NP020FP.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020FP.use_snap
            bpy.context.tool_settings.snap_element = NP020FP.snap_element
            bpy.context.tool_settings.snap_target = NP020FP.snap_target
            bpy.context.space_data.pivot_point = NP020FP.pivot_point
            bpy.context.space_data.transform_orientation = NP020FP.trans_orient
            if NP020FP.acob is not None:
                bpy.context.scene.objects.active = NP020FP.acob
                bpy.ops.object.mode_set(mode=NP020FP.edit_mode)
            np_print('11_run_BEVEL_INVOKE_a_FINISHED')
            return {'FINISHED'}




# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    bpy.app.handlers.scene_update_post.append(scene_update)

    NP020FloatPoly.define('OBJECT_OT_np_fp_get_selection')
    NP020FloatPoly.define('OBJECT_OT_np_fp_read_mouse_loc')
    NP020FloatPoly.define('OBJECT_OT_np_fp_add_points')
    for i in range(1, 10):
        NP020FloatPoly.define('OBJECT_OT_np_fp_run_translate')
        NP020FloatPoly.define('OBJECT_OT_np_fp_run_navigate')
    NP020FloatPoly.define('OBJECT_OT_np_fp_change_phase')
    for i in range(1, 100):
        for i in range(1, 10):
            NP020FloatPoly.define('OBJECT_OT_np_fp_run_translate')
            NP020FloatPoly.define('OBJECT_OT_np_fp_run_navigate')
        NP020FloatPoly.define('OBJECT_OT_np_fp_make_segment')
    NP020FloatPoly.define('OBJECT_OT_np_fp_delete_points')
    NP020FloatPoly.define('OBJECT_OT_np_fp_make_surface')
    for i in range(1, 10):
        NP020FloatPoly.define('OBJECT_OT_np_fp_run_extrude')
        NP020FloatPoly.define('OBJECT_OT_np_fp_run_navex')
    NP020FloatPoly.define('OBJECT_OT_np_fp_run_bevel')


def unregister():

    # bpy.app.handlers.scene_update_post.remove(scene_update)
    pass
