
# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####


'''
DESCRIPTION

Measures distance using start and end points. Emulates the functionality of the standard 'distance' command in CAD applications. User is now able to change snap target while operating.


INSTALATION

Unzip and place .py file to scripts / addons_contrib folder. In User Preferences / Addons tab, search with Testing filter - NP Point Distance and check the box.
Now you have the operator in your system. If you press Save User Preferences, you will have it at your disposal every time you run Blender.


SHORTCUTS

After successful installation of the addon, the NP Point Distance operator should be registered in your system. Enter User Preferences / Input, and under that, 3DView / Global mode. At the bottom of the list click the 'Add new' button. In the operator field type object.np_point_distance_xxx (xxx being the number of the version) and assign a key of yor prefference. At the moment i am using 'T' for 'tape measure'. I have my 'T' and 'N' keys free because of new 'Z' and 'X' keys assigned to toolshelf and properties (under the left hand, no need to look down).


USAGE

Run operator (spacebar search - NP Point Distance, or keystroke if you assigned it)
Select a point anywhere in the scene (holding CTRL enables snapping). This will be your start point.
Move your mouse anywhere in the scene, in relation to the start point (again CTRL - snap). The addon will show the distance between your start and end points.
Middle mouse button (MMB) enables axis constraint, numpad keys enable numerical input of distance, ENTER key changes snap target and RMB and ESC key interrupt the operation.


ADDON SETTINGS:

Below the addon name in the user preferences / addon tab, you can find a couple of settings that control the behavior of the addon:

Unit scale: Distance multiplier for various unit scenarios
Suffix: Unit abbreviation after the numerical distance
Custom colors: Default or custom colors for graphical elements
Mouse badge: Option to display a small cursor label


IMPORTANT PERFORMANCE NOTES

Now can start in all 3D modes, the operator temporarily exits the mode and enters the object mode, does the task and returns to original mode.


WISH LIST

X/Y/Z distance components
Custom colors, fonts and unit formats
Navigation enabled during use
Smarter code and faster performance


TO DO

PEP8
Custom colors, fonts and unit formats, custom colors for badge, aistance num on top
Navigation enabled during use
Smarter code and faster performance


WARNINGS

None so far
'''


bl_info = {
    'name': 'NP 020 Point Distance',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Measures distance between two snapped points',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bgl
import blf
import mathutils
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix
from blf import ROTATION
from math import radians

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *

# Defining the main class - the macro:

class NP020PointDistance(bpy.types.Macro):
    bl_idname = 'object.np_020_point_distance'
    bl_label = 'NP 020 Point Distance'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable-bank for
# exchange among the classes. Later, this bank will receive more variables
# with their values for safe keeping, as the program goes on:

class NP020PD:

    startloc3d = (0.0, 0.0, 0.0)
    endloc3d = (0.0, 0.0, 0.0)
    phase = 0
    start = None
    end = None
    dist = None
    flag = 'TRANSLATE'
    snap = 'VERTEX'


# Defining the first of the classes from the macro, that will gather the
# current system settings set by the user. Some of the system settings
# will be changed during the process, and will be restored when macro has
# completed. It also aquires the list of selected objects and storing them
# for later re-call (the addon doesn't need them for operation):

class NP020PDGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_pd_get_selection'
    bl_label = 'NP PD Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        # First, storing all of the system preferences set by the user, that
        # will be changed during the process, in order to restore them when the
        # operation is completed:

        np_print('01_get_selection_START')
        NP020PD.use_snap = bpy.context.tool_settings.use_snap
        NP020PD.snap_element = bpy.context.tool_settings.snap_element
        NP020PD.snap_target = bpy.context.tool_settings.snap_target
        NP020PD.pivot_point = bpy.context.space_data.pivot_point
        NP020PD.trans_orient = bpy.context.space_data.transform_orientation
        NP020PD.show_manipulator = bpy.context.space_data.show_manipulator
        NP020PD.acob = bpy.context.active_object
        np_print('NP020PD.acob =', NP020PD.acob)
        np_print(bpy.context.mode)
        if bpy.context.mode == 'OBJECT':
            NP020PD.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020PD.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020PD.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020PD.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020PD.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020PD.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020PD.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020PD.edit_mode = 'PARTICLE_EDIT'
        NP020PD.phase = 0
        # Reading and storing the selection:
        selob = bpy.context.selected_objects
        NP020PD.selob = selob
        # De-selecting objects in prepare for other processes in the script:
        for ob in selob:
            ob.select_set(False)
        np_print('01_get_selection_END')
        return {'FINISHED'}

# Defining the operator that will read the mouse position in 3D when the
# command is activated and store it as a location for placing the start
# and end points under the mouse:


class NP020PDReadMouseLoc(bpy.types.Operator):
    bl_idname = 'object.np_pd_read_mouse_loc'
    bl_label = 'NP PD Read Mouse Loc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        np_print('02_read_mouse_loc_START')
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        pointloc = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, co2d) + view_vector / 5
        np_print(pointloc)
        NP020PD.pointloc = pointloc
        np_print('02_read_mouse_loc_END')
        return{'FINISHED'}

    def invoke(self, context, event):
        np_print('02_read_mouse_loc_INVOKE_a')
        args = (self, context)
        context.window_manager.modal_handler_add(self)
        np_print('02_read_mouse_loc_INVOKE_b')
        return {'RUNNING_MODAL'}


# Defining the operator that will generate start and end points at the
# spot marked by mouse and select them, preparing for translation:


class NP020PDAddPoints(bpy.types.Operator):
    bl_idname = 'object.np_pd_add_points'
    bl_label = 'NP PD Add Points'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_add_points_START')
        pointloc = NP020PD.pointloc
        if bpy.context.mode not in ('OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.space_data.show_manipulator = False
        bpy.ops.object.add(type='MESH', location=pointloc)
        start = bpy.context.object
        start.name = 'NP_PD_start'
        NP020PD.start = start
        bpy.ops.object.add(type='MESH', location=pointloc)
        end = bpy.context.object
        end.name = 'NP_PD_end'
        NP020PD.end = end
        start.select_set(True)
        end.select_set(True)
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = NP020PD.snap
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        np_print('03_add_points_END')
        return{'FINISHED'}


# Defining the operator that will draw the OpenGL line across the screen
# together with the numerical distance and the on-screen instructions in
# normal, translation mode:

def draw_callback_px_TRANS(self, context):

    np_print('04_callback_TRANS_START')

    addon_prefs = context.preferences.addons[__package__].preferences

    scale = addon_prefs.nppd_scale
    badge = addon_prefs.nppd_badge
    step = addon_prefs.nppd_step
    info = addon_prefs.nppd_info
    clip = addon_prefs.nppd_clip
    xyz_lines = addon_prefs.nppd_xyz_lines
    xyz_distances = addon_prefs.nppd_xyz_distances
    xyz_backdrop = addon_prefs.nppd_xyz_backdrop
    stereo_cage = addon_prefs.nppd_stereo_cage
    gold = addon_prefs.nppd_gold

    if addon_prefs.nppd_col_line_main_DEF == False:
        col_line_main = addon_prefs.nppd_col_line_main
    else:
        col_line_main = (1.0, 1.0, 1.0, 1.0)

    if addon_prefs.nppd_col_line_shadow_DEF == False:
        col_line_shadow = addon_prefs.nppd_col_line_shadow
    else:
        col_line_shadow = (0.1, 0.1, 0.1, 0.25)

    if addon_prefs.nppd_col_num_main_DEF == False:
        col_num_main = addon_prefs.nppd_col_num_main
    else:
        col_num_main = (0.95, 0.95, 0.95, 1.0)

    if addon_prefs.nppd_col_num_shadow_DEF == False:
        col_num_shadow = addon_prefs.nppd_col_num_shadow
    else:
        col_num_shadow = (0.0, 0.0, 0.0, 0.75)

    if addon_prefs.nppd_suffix == 'None':
        suffix = None

    elif addon_prefs.nppd_suffix == 'km':
        suffix = ' km'

    elif addon_prefs.nppd_suffix == 'm':
        suffix = ' m'

    elif addon_prefs.nppd_suffix == 'cm':
        suffix = ' cm'

    elif addon_prefs.nppd_suffix == 'mm':
        suffix = ' mm'

    elif addon_prefs.nppd_suffix == 'nm':
        suffix = ' nm'

    elif addon_prefs.nppd_suffix == "'":
        suffix = "'"

    elif addon_prefs.nppd_suffix == '"':
        suffix = '"'

    elif addon_prefs.nppd_suffix == 'thou':
        suffix = ' thou'
    # np_print('0')
    # sel=bpy.context.selected_objects
    phase = NP020PD.phase
    start = NP020PD.start
    end = NP020PD.end
    startloc3d = start.location
    endloc3d = end.location
    endloc3dx = copy.deepcopy(startloc3d)
    endloc3dx[0] = endloc3d[0]
    endloc3dy = copy.deepcopy(startloc3d)
    endloc3dy[1] = endloc3d[1]
    endloc3dz = copy.deepcopy(startloc3d)
    endloc3dz[2] = endloc3d[2]
    region = context.region
    rv3d = context.region_data
    startloc2d = view3d_utils.location_3d_to_region_2d(
        region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)
    endloc2dx = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3dx)
    endloc2dy = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3dy)
    endloc2dz = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3dz)
    if startloc2d is None:
        startloc2d = (0.0, 0.0)
        endloc2d = (0.0, 0.0)
    np_print(startloc2d, endloc2d)
    # np_print('1')
    dist = (mathutils.Vector(endloc3d) - mathutils.Vector(startloc3d))
    distgold = dist / 1.6180339887
    goldloc3d = mathutils.Vector(startloc3d) + distgold
    goldloc2d = view3d_utils.location_3d_to_region_2d(
        region, rv3d, goldloc3d)
    distn = dist.length * scale
    distn = str(abs(round(distn, 2)))

    dist = dist.length * scale

    if suffix is not None:
        dist = str(abs(round(dist, 2))) + suffix
    else:
        dist = str(abs(round(dist, 2)))
    NP020PD.dist = dist
    # np_print('2')
    # This is for correcting the position of the numerical on the screen if
    # the endpoints are far out of screen:
    numloc = []
    run = 'IN'
    startx = startloc2d[0]
    starty = startloc2d[1]
    endx = endloc2d[0]
    endy = endloc2d[1]
    if startx > region.width:
        startx = region.width
        run = 'OUT'
    if startx < 0:
        startx = 0
        run = 'OUT'
    if starty > region.height:
        starty = region.height
        run = 'OUT'
    if starty < 0:
        starty = 0
        run = 'OUT'
    if endx > region.width:
        endx = region.width
        run = 'OUT'
    if endx < 0:
        endx = 0
        run = 'OUT'
    if endy > region.height:
        endy = region.height
        run = 'OUT'
    if endy < 0:
        endy = 0
        run = 'OUT'
    numloc.append((startx + endx) / 2)
    numloc.append((starty + endy) / 2)
    # np_print('3')
    if phase == 0:
        instruct = 'select start point'

    if phase == 1:
        instruct = 'select end point'

    if NP020PD.flag == 'HOLD':
        instruct = 'inspect result'

    # Drawing:

    bgl.glEnable(bgl.GL_BLEND)


    # ON-SCREEN INSTRUCTIONS:


    if NP020PD.flag == 'HOLD':
        keys_aff = 'LMB, ENT, SPACE - continue'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'

    else:
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap, MMB - lock axis'
        keys_nav = 'SPACE - change to navigate'
        keys_neg = 'ESC, RMB - quit'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)



    # LINES:
    # cage lines:
    if phase == 1 and stereo_cage:

        startloc3dx = copy.deepcopy(endloc3d)
        startloc3dx[0] = startloc3d[0]
        startloc3dy = copy.deepcopy(endloc3d)
        startloc3dy[1] = startloc3d[1]
        startloc3dz = copy.deepcopy(endloc3d)
        startloc3dz[2] = startloc3d[2]
        startloc2dx = view3d_utils.location_3d_to_region_2d(
            region, rv3d, startloc3dx)
        startloc2dy = view3d_utils.location_3d_to_region_2d(
            region, rv3d, startloc3dy)
        startloc2dz = view3d_utils.location_3d_to_region_2d(
            region, rv3d, startloc3dz)

        bgl.glColor4f(0.5, 0.5, 0.5, 0.5)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*endloc2d)
        bgl.glVertex2f(*startloc2dx)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*endloc2d)
        bgl.glVertex2f(*startloc2dy)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*endloc2d)
        bgl.glVertex2f(*startloc2dz)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*endloc2dy)
        bgl.glVertex2f(*startloc2dx)
        bgl.glVertex2f(*endloc2dz)
        bgl.glVertex2f(*startloc2dy)
        bgl.glVertex2f(*endloc2dx)
        bgl.glVertex2f(*startloc2dz)
        bgl.glVertex2f(*endloc2dy)
        bgl.glEnd()

    if phase == 1 and xyz_lines == False and stereo_cage == True:

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*startloc2d)
        bgl.glVertex2f(*endloc2dx)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*startloc2d)
        bgl.glVertex2f(*endloc2dy)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*startloc2d)
        bgl.glVertex2f(*endloc2dz)
        bgl.glEnd()

    # main line:

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

    # xyz lines:

    if phase == 1 and xyz_lines:

        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
        bgl.glLineWidth(1.2)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*startloc2d)
        bgl.glVertex2f(*endloc2dx)
        bgl.glEnd()

        bgl.glColor4f(0.0, 0.75, 0.0, 1.0)
        bgl.glLineWidth(1.2)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*startloc2d)
        bgl.glVertex2f(*endloc2dy)
        bgl.glEnd()

        bgl.glColor4f(0.0, 0.0, 1.0, 1.0)
        bgl.glLineWidth(1.2)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*startloc2d)
        bgl.glVertex2f(*endloc2dz)
        bgl.glEnd()

        # bgl.glEnable(bgl.GL_BLEND)

        bgl.glPointSize(2)
        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*endloc2dx)
        bgl.glEnd()

        bgl.glPointSize(2)
        bgl.glColor4f(0.0, 0.75, 0.0, 1.0)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*endloc2dy)
        bgl.glEnd()

        bgl.glPointSize(2)
        bgl.glColor4f(0.0, 0.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*endloc2dz)
        bgl.glEnd()
    # np_print('4')



    # Drawing the small badge near the cursor with the basic instructions:
    size = 2
    font_id = 0
    end = NP020PD.end
    endloc = end.location
    mouseloc = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc)
    if badge and NP020PD.flag != 'HOLD':
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        snapsquare = [[17, 30], [67, 30], [67, 20], [17, 20]]
        arrow = [[20, 33], [18, 35], [20, 37], [18, 35],
            [26, 35], [24, 33], [26, 35], [24, 37]]
        dots1 = [[19, 31], [20, 31]]
        dots2 = [[22, 31], [23, 31]]
        dots3 = [[25, 31], [26, 31]]
        ipx = 29
        ipy = 33
        for co in square:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        for co in rectangle:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        for co in snapsquare:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        for co in arrow:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        for co in dots1:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        for co in dots2:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        for co in dots3:
            co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
            co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
        ipx = round((ipx * size), 0) - 20 + mouseloc[0]
        ipy = round((ipy * size), 0) - 50 + mouseloc[1]
        ipsize = 6 * size
        bgl.glColor4f(0.0, 0.0, 0.0, 0.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in rectangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(0.4, 0.15, 0.75, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in snapsquare:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x, y in arrow:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ipx - (10 * size), ipy - (10 * size), 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, NP020PD.snap)
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ipx, ipy, 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, 'CTRL+SNAP')
        if step == 'continuous':
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots1:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots2:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots3:
                bgl.glVertex2f(x, y)
            bgl.glEnd()

    if gold and phase != 0:
        '''
        goldtriangle = [[0, 0], [-1, 1], [1, 1]]
        for co in goldtriangle:
            co[0] = round((co[0] * 10), 0) + goldloc2d[0]
            co[1] = round((co[1] * 10), 0) + goldloc2d[1]
        bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in goldtriangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        '''
        goldvec1 = mathutils.Vector((1.0 , 0.0))
        goldvec2 = endloc2d - startloc2d
        ang = goldvec1.angle_signed(goldvec2, None)
        if ang is not None:
            coy = round(cos(ang), 8)
            cox = round(sin(ang), 8)
            goldtick = [[-cox, -coy], [0, 0], [cox, coy]]
            for co in goldtick:
                co[0] = round((co[0] * 10), 0) + goldloc2d[0]
                co[1] = round((co[1] * 10), 0) + goldloc2d[1]
            bgl.glColor4f(0.95, 0.55, 0.0, 1.0)
            bgl.glLineWidth(2)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in goldtick:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glLineWidth(1)
            if xyz_distances:
                distgold_first = (goldloc3d - startloc3d).length * scale
                distgold_first = str(abs(round(distgold_first, 2)))
                distgold_sec = (endloc3d - goldloc3d).length * scale
                distgold_sec = str(abs(round(distgold_sec, 2)))
                goldloc_first = [((startloc2d[0] + goldloc2d[0]) / 2), ((startloc2d[1] + goldloc2d[1]) / 2)]
                goldloc_sec = [((goldloc2d[0] + endloc2d[0]) / 2), ((goldloc2d[1] + endloc2d[1]) / 2)]
                if xyz_backdrop:
                    bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
                    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                    bgl.glVertex2f(goldloc_first[0]-2, goldloc_first[1]-2)
                    bgl.glVertex2f(goldloc_first[0]-2, goldloc_first[1]+10)
                    bgl.glVertex2f(goldloc_first[0]+50, goldloc_first[1]+10)
                    bgl.glVertex2f(goldloc_first[0]+50, goldloc_first[1]-2)
                    bgl.glEnd()
                bgl.glColor4f(0.95, 0.55, 0.0, 1.0)
                if xyz_backdrop:
                    bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
                blf.position(font_id, goldloc_first[0], goldloc_first[1], 0)
                blf.draw(font_id, distgold_first)
                if xyz_backdrop:
                    bgl.glColor4f(1.0, 0.5, 0.0, 1.0)
                    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                    bgl.glVertex2f(goldloc_sec[0]-2, goldloc_sec[1]-2)
                    bgl.glVertex2f(goldloc_sec[0]-2, goldloc_sec[1]+10)
                    bgl.glVertex2f(goldloc_sec[0]+50, goldloc_sec[1]+10)
                    bgl.glVertex2f(goldloc_sec[0]+50, goldloc_sec[1]-2)
                    bgl.glEnd()
                bgl.glColor4f(0.95, 0.55, 0.0, 1.0)
                if xyz_backdrop:
                    bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
                blf.position(font_id, goldloc_sec[0], goldloc_sec[1], 0)
                blf.draw(font_id, distgold_sec)


    # NUMERICAL DISTANCE:

    square = [[17, 30], [17, 40], [27, 40], [27, 30]]
    for co in square:
        co[0] = round((co[0] * size), 0) - 20 + mouseloc[0]
        co[1] = round((co[1] * size), 0) - 50 + mouseloc[1]
    badgeloc = [(square[0][0] + 6), (square[0][1] - 8)]
    numlocdistx = abs(badgeloc[0] - numloc[0])
    numlocdisty = abs(badgeloc[1] - numloc[1])
    if numlocdistx < 96 and numlocdisty < 30:
        numloc[0] = square[0][0]
        numloc[1] = square[0][1] - 40

    if startloc3d[0] == endloc3d[0] and startloc3d[1] == endloc3d[1]:
        col_num_main = (0.0, 0.0, 0.80, 0.75)
    elif startloc3d[1] == endloc3d[1] and startloc3d[2] == endloc3d[2]:
        col_num_main = (0.85, 0.0, 0.0, 0.75)
    elif startloc3d[0] == endloc3d[0] and startloc3d[2] == endloc3d[2]:
        col_num_main = (0.0, 0.60, 0.0, 0.75)

    bgl.glColor4f(*col_num_shadow)
    if phase == 1:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, (numloc[0] - 1), (numloc[1] - 1), 0)
        blf.draw(font_id, dist)

    bgl.glColor4f(*col_num_main)
    if phase == 1:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, numloc[0], numloc[1], 0)
        blf.draw(font_id, dist)

    # xyz numericals:

    if phase == 1 and xyz_distances:

        badgeloc[0] = badgeloc[0] + 27
        badgeloc[1] = badgeloc[1] - 15
        font_id = 0
        blf.size(font_id, 12, 72)
        slide = 0
        numloccen = [0, 0]
        numloccen[0] = numloc[0] + 15
        numloccen[1] = numloc[1] + 2

        distx = (endloc3dx[0] - startloc3d[0]) * scale
        distx = str(abs(round(distx, 2)))
        if distx not in (dist, distn):
            numlocx = [(
                       (startloc2d[0] + endloc2dx[0]) / 2),
     ((startloc2d[1] + endloc2dx[1]) / 2)]
            numlocbadge = (
                mathutils.Vector(
                    numlocx) - mathutils.Vector(
                        badgeloc)).length
            numlocdistx = abs(numlocx[0] - numloccen[0])
            numlocdisty = abs(numlocx[1] - numloccen[1])
            if numlocdistx < 60 and numlocdisty < 16:
                numlocx[0] = numloc[0]
                numlocx[1] = numloc[1] - 15
                slide = slide + 1
            elif run == 'OUT' or numlocbadge < 65:
                numlocx[0] = numloc[0]
                numlocx[1] = numloc[1] - 15
                slide = slide + 1
            # bgl.glColor4f(*col_num_shadow)
            # blf.position(font_id, numlocx[0]-1, numlocx[1]-1, 0)
            # blf.draw(font_id, distx)
            if xyz_backdrop:
                bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                bgl.glVertex2f(numlocx[0]-2, numlocx[1]-2)
                bgl.glVertex2f(numlocx[0]-2, numlocx[1]+10)
                bgl.glVertex2f(numlocx[0]+50, numlocx[1]+10)
                bgl.glVertex2f(numlocx[0]+50, numlocx[1]-2)
                bgl.glEnd()
            bgl.glColor4f(0.85, 0.0, 0.0, 1.0)
            if xyz_backdrop:
                bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
            blf.position(font_id, numlocx[0], numlocx[1], 0)
            blf.draw(font_id, distx)

        disty = (endloc3dy[1] - startloc3d[1]) * scale
        disty = str(abs(round(disty, 2)))
        if disty not in (dist, distn):
            numlocy = [(
                       (startloc2d[0] + endloc2dy[0]) / 2),
     ((startloc2d[1] + endloc2dy[1]) / 2)]
            numlocbadge = (
                mathutils.Vector(
                    numlocy) - mathutils.Vector(
                        badgeloc)).length
            numlocdistx = abs(numlocy[0] - numloccen[0])
            numlocdisty = abs(numlocy[1] - numloccen[1])
            if numlocdistx < 60 and numlocdisty < 16:
                numlocy[0] = numloc[0]
                numlocy[1] = numloc[1] - ((slide * 12) + 15)
                slide = slide + 1
            elif run == 'OUT' or numlocbadge < 65:
                numlocy[0] = numloc[0]
                numlocy[1] = numloc[1] - ((slide * 12) + 15)
                slide = slide + 1
            if xyz_backdrop:
                bgl.glColor4f(0.0 ,0.65 ,0.0 ,1.0)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                bgl.glVertex2f(numlocy[0]-2, numlocy[1]-2)
                bgl.glVertex2f(numlocy[0]-2, numlocy[1]+10)
                bgl.glVertex2f(numlocy[0]+50, numlocy[1]+10)
                bgl.glVertex2f(numlocy[0]+50, numlocy[1]-2)
                bgl.glEnd()
            bgl.glColor4f(0.0 ,0.75 ,0.0 ,1.0)
            if xyz_backdrop:
                bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
            blf.position(font_id, numlocy[0], numlocy[1], 0)
            blf.draw(font_id, disty)

        distz = (endloc3dz[2] - startloc3d[2]) * scale
        distz = str(abs(round(distz, 2)))
        if distz not in (dist, distn):
            numlocz = [(
                       (startloc2d[0] + endloc2dz[0]) / 2),
     ((startloc2d[1] + endloc2dz[1]) / 2)]
            numlocbadge = (
                mathutils.Vector(
                    numlocz) - mathutils.Vector(
                        badgeloc)).length
            numlocdistx = abs(numlocz[0] - numloccen[0])
            numlocdisty = abs(numlocz[1] - numloccen[1])
            if numlocdistx < 60 and numlocdisty < 16:
                numlocz[0] = numloc[0]
                numlocz[1] = numloc[1] - ((slide * 12) + 15)
            elif run == 'OUT' or numlocbadge < 65:
                numlocz[0] = numloc[0]
                numlocz[1] = numloc[1] - ((slide * 12) + 15)
            if xyz_backdrop:
                bgl.glColor4f(0.0, 0.0, 0.85, 1.0)
                bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                bgl.glVertex2f(numlocz[0]-2, numlocz[1]-2)
                bgl.glVertex2f(numlocz[0]-2, numlocz[1]+10)
                bgl.glVertex2f(numlocz[0]+50, numlocz[1]+10)
                bgl.glVertex2f(numlocz[0]+50, numlocz[1]-2)
                bgl.glEnd()
            bgl.glColor4f(0.0, 0.0, 1.0, 1.0)
            if xyz_backdrop:
                bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
            blf.position(font_id, numlocz[0], numlocz[1], 0)
            blf.draw(font_id, distz)

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    # np_print('5')

    # ENDING

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    # np_print('7')
    np_print('04_callback_TRANS_END')


def scene_update(context):
    # np_print('00_scene_update_START')
    # np_print('up1')
    if bpy.data.objects.is_updated:
        phase = NP020PD.phase
        np_print('up')
        start = NP020PD.start
        end = NP020PD.end
        if phase == 1:
            # np_print('up2')
            startloc3d = start.location
            endloc3d = end.location
            NP020PD.startloc3d = startloc3d
            NP020PD.endloc3d = endloc3d
    # np_print('up3')
    # np_print('00_scene_update_END')


# Defining the operator that will let the user translate start and end to
# the desired point. It also uses some listening operators that clean up
# the leftovers should the user interrupt the command. Many thanks to
# CoDEmanX and lukas_t:


class NP020PDRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_pd_run_translate'
    bl_label = 'NP PD Run Translate'
    bl_options = {'INTERNAL'}

    np_print('04_run_TRANS_START')
    count = 0

    def modal(self, context, event):
        context.area.tag_redraw()
        self.count += 1
        selob = NP020PD.selob
        start = NP020PD.start
        end = NP020PD.end
        phase = NP020PD.phase

        if self.count == 1:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            np_print('04_run_TRANS_count_1_INVOKE_DEFAULT')

        elif event.type in ('LEFTMOUSE', 'NUMPAD_ENTER') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PD.flag = 'PASS'
            np_print('04_run_TRANS_left_release_FINISHED')
            return{'FINISHED'}

        elif event.type == 'RET' and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if bpy.context.tool_settings.snap_element == 'VERTEX':
                bpy.context.tool_settings.snap_element = 'EDGE'
                NP020PD.snap = 'EDGE'
            elif bpy.context.tool_settings.snap_element == 'EDGE':
                bpy.context.tool_settings.snap_element = 'FACE'
                NP020PD.snap = 'FACE'
            elif bpy.context.tool_settings.snap_element == 'FACE':
                bpy.context.tool_settings.snap_element = 'VERTEX'
                NP020PD.snap = 'VERTEX'
            NP020PD.flag = 'TRANSLATE'
            np_print('04_run_TRANS_enter_PASS')
            return{'FINISHED'}

        elif event.type == 'SPACE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            start.hide = True
            end.hide = True
            NP020PD.flag = 'NAVIGATE'
            np_print('04_run_TRANS_space_FINISHED_flag_NAVIGATE')
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
        # this actually begins when user RELEASES esc or rightmouse, PRESS is
        # taken by transform.translate operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.select_all(action='DESELECT')
            start.select_set(True)
            end.select_set(True)
            bpy.ops.object.delete('EXEC_DEFAULT')
            for ob in selob:
                ob.select_set(True)
            NP020PD.startloc3d = (0.0, 0.0, 0.0)
            NP020PD.endloc3d = (0.0, 0.0, 0.0)
            NP020PD.phase = 0
            NP020PD.start = None
            NP020PD.end = None
            NP020PD.dist = None
            NP020PD.flag = 'TRANSLATE'
            NP020PD.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020PD.use_snap
            bpy.context.tool_settings.snap_element = NP020PD.snap_element
            bpy.context.tool_settings.snap_target = NP020PD.snap_target
            bpy.context.space_data.pivot_point = NP020PD.pivot_point
            bpy.context.space_data.transform_orientation = NP020PD.trans_orient
            bpy.context.space_data.show_manipulator = NP020PD.show_manipulator
            if NP020PD.acob is not None:
                bpy.context.view_layer.objects.active = NP020PD.acob
                bpy.ops.object.mode_set(mode=NP020PD.edit_mode)
            np_print('04_run_TRANS_esc_right_CANCELLED')
            return{'CANCELLED'}

        np_print('04_run_TRANS_PASS_THROUGH')
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        flag = NP020PD.flag
        np_print('04_run_TRANS_INVOKE_a')
        np_print('flag=', flag)
        if flag == 'TRANSLATE':
            if context.area.type == 'VIEW_3D':
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(
                    draw_callback_px_TRANS, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                np_print('04_run_TRANS_INVOKE_a_RUNNING_MODAL')
                return {'RUNNING_MODAL'}
            else:
                self.report(
                    {'WARNING'},
                    "View3D not found, cannot run operator")
                np_print('04_run_TRANS_INVOKE_a_CANCELLED')
                return {'CANCELLED'}
        else:
            np_print('04_run_TRANS_INVOKE_a_FINISHED')
            return {'FINISHED'}


# Defining the operator that will draw the graphicall reprezentation of
# distance in navigation mode if user calls it:


def draw_callback_px_NAV(self, context):

    np_print('05_callback_NAV_START')

    addon_prefs = context.preferences.addons[__package__].preferences

    scale = addon_prefs.nppd_scale
    badge = addon_prefs.nppd_badge
    step = addon_prefs.nppd_step
    info = addon_prefs.nppd_info
    clip = addon_prefs.nppd_clip

    if addon_prefs.nppd_col_line_main_DEF == False:
        col_line_main = addon_prefs.nppd_col_line_main
    else:
        col_line_main = (1.0, 1.0, 1.0, 1.0)

    if addon_prefs.nppd_col_line_shadow_DEF == False:
        col_line_shadow = addon_prefs.nppd_col_line_shadow
    else:
        col_line_shadow = (0.1, 0.1, 0.1, 0.25)

    if addon_prefs.nppd_col_num_main_DEF == False:
        col_num_main = addon_prefs.nppd_col_num_main
    else:
        col_num_main = (0.95, 0.95, 0.95, 1.0)

    if addon_prefs.nppd_col_num_shadow_DEF == False:
        col_num_shadow = addon_prefs.nppd_col_num_shadow
    else:
        col_num_shadow = (0.0, 0.0, 0.0, 0.75)

    if addon_prefs.nppd_suffix == 'None':
        suffix = None

    elif addon_prefs.nppd_suffix == 'km':
        suffix = ' km'

    elif addon_prefs.nppd_suffix == 'm':
        suffix = ' m'

    elif addon_prefs.nppd_suffix == 'cm':
        suffix = ' cm'

    elif addon_prefs.nppd_suffix == 'mm':
        suffix = ' mm'

    elif addon_prefs.nppd_suffix == 'nm':
        suffix = ' nm'

    elif addon_prefs.nppd_suffix == "'":
        suffix = "'"

    elif addon_prefs.nppd_suffix == '"':
        suffix = '"'

    elif addon_prefs.nppd_suffix == 'thou':
        suffix = ' thou'

    # Calculating the 3d points for the graphical line while in NAVIGATE flag:
    phase = NP020PD.phase
    region = context.region
    rv3d = context.region_data
    co2d = self.co2d
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
    pointloc = view3d_utils.region_2d_to_origin_3d(
        region, rv3d, co2d) + view_vector / 5

    np_print('phase=', phase)
    if phase == 0:
        startloc3d = (0.0, 0.0, 0.0)
        endloc3d = (0.0, 0.0, 0.0)

    if phase == 1:
        startloc3d = NP020PD.startloc3d
        endloc3d = pointloc

    # Calculating the 2D points for the graphical line while in NAVIGATE flag
    # from 3D points:

    startloc2d = view3d_utils.location_3d_to_region_2d(
        region, rv3d, startloc3d)
    endloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, endloc3d)

    if startloc2d is None:
        startloc2d = (0.0, 0.0)
        endloc2d = (0.0, 0.0)
    np_print(startloc2d, endloc2d)

    dist = (mathutils.Vector(endloc3d) - mathutils.Vector(startloc3d))
    dist = dist.length * scale
    if suffix is not None:
        dist = str(abs(round(dist, 2))) + suffix
    else:
        dist = str(abs(round(dist, 2)))

    NP020PD.dist = dist

    # This is for correcting the position of the numerical on the screen if
    # the endpoints are far out of screen:
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

    if phase == 0:
        instruct = 'navigate for better placement of start point'

    if phase == 1:
        instruct = 'navigate for better placement of end point'

    # Drawing:

    bgl.glEnable(bgl.GL_BLEND)

    # ON-SCREEN INSTRUCTIONS:

    keys_aff = 'MMB, SCROLL - navigate'
    keys_nav = 'LMB, SPACE - leave navigate'
    keys_neg = 'ESC, RMB - quit'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    # LINE:

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



    # Drawing the small badge near the cursor with the basic instructions:

    if badge:
        font_id = 0
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        arrow = [[20, 33], [18, 35], [20, 37], [18, 35],
            [26, 35], [24, 33], [26, 35], [24, 37]]
        dots1 = [[19, 31], [20, 31]]
        dots2 = [[22, 31], [23, 31]]
        dots3 = [[25, 31], [26, 31]]
        ipx = 29
        ipy = 33
        size = 2
        for co in square:
            co[0] = round((co[0] * size), 0) - 20 + co2d[0]
            co[1] = round((co[1] * size), 0) - 50 + co2d[1]
        for co in rectangle:
            co[0] = round((co[0] * size), 0) - 20 + co2d[0]
            co[1] = round((co[1] * size), 0) - 50 + co2d[1]
        for co in arrow:
            co[0] = round((co[0] * size), 0) - 20 + co2d[0]
            co[1] = round((co[1] * size), 0) - 50 + co2d[1]
        for co in dots1:
            co[0] = round((co[0] * size), 0) - 20 + co2d[0]
            co[1] = round((co[1] * size), 0) - 50 + co2d[1]
        for co in dots2:
            co[0] = round((co[0] * size), 0) - 20 + co2d[0]
            co[1] = round((co[1] * size), 0) - 50 + co2d[1]
        for co in dots3:
            co[0] = round((co[0] * size), 0) - 20 + co2d[0]
            co[1] = round((co[1] * size), 0) - 50 + co2d[1]
        ipx = round((ipx * size), 0) - 20 + co2d[0]
        ipy = round((ipy * size), 0) - 50 + co2d[1]
        ipsize = 6 * size
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
        for x, y in arrow:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ipx, ipy, 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, 'NAVIGATE')
        if step == 'continuous':
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots1:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots2:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots3:
                bgl.glVertex2f(x, y)
            bgl.glEnd()

    # NUMERICAL DISTANCE:

    bgl.glColor4f(*col_num_shadow)
    if phase == 1:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, (numloc[0] - 1), (numloc[1] - 1), 0)
        blf.draw(font_id, dist)

    bgl.glColor4f(*col_num_main)
    if phase == 1:
        font_id = 0
        blf.size(font_id, 20, 72)
        blf.position(font_id, numloc[0], numloc[1], 0)
        blf.draw(font_id, dist)

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    # ENDING
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('05_callback_NAV_END')


# Defining the operator that will enable navigation if user calls it:

class NP020PDRunNavigate(bpy.types.Operator):
    bl_idname = "object.np_pd_run_navigate"
    bl_label = "NP PD Run Navigate"
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        np_print('05_run_NAV_START')
        context.area.tag_redraw()
        selob = NP020PD.selob
        start = NP020PD.start
        end = NP020PD.end
        phase = NP020PD.phase

        if event.type == 'MOUSEMOVE':
            np_print('05_run_NAV_mousemove_a')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            np_print('05_run_NAV_mousemove_b')

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            np_print('05_run_NAV_left_space_press_START')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            phase = NP020PD.phase
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(
                region, rv3d, co2d)
            pointloc = view3d_utils.region_2d_to_origin_3d(
                region, rv3d, co2d) + view_vector / 5
            start = NP020PD.start
            end = NP020PD.end
            start.hide = False
            end.hide = False
            np_print('phase=', phase)
            if phase == 0:
                startloc3d = (0.0, 0.0, 0.0)
                endloc3d = (0.0, 0.0, 0.0)
                start.location = pointloc
                end.location = pointloc
            if phase == 1:
                startloc3d = NP020PD.startloc3d
                endloc3d = pointloc
                end.location = pointloc
            NP020PD.start = start
            NP020PD.end = end
            NP020PD.startloc3d = startloc3d
            NP020PD.endloc3d = endloc3d
            NP020PD.flag = 'TRANSLATE'
            np_print('05_run_NAV_left_space_press_FINISHED_flag_TRANSLATE')
            return {'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
            np_print('05_run_NAV_esc_right_any_START')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.select_all(action='DESELECT')
            start.hide = False
            end.hide = False
            start.select_set(True)
            end.select_set(True)
            bpy.ops.object.delete('EXEC_DEFAULT')
            for ob in selob:
                ob.select_set(True)
            NP020PD.startloc3d = (0.0, 0.0, 0.0)
            NP020PD.endloc3d = (0.0, 0.0, 0.0)
            NP020PD.phase = 0
            NP020PD.start = None
            NP020PD.end = None
            NP020PD.dist = None
            NP020PD.flag = 'TRANSLATE'
            NP020PD.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020PD.use_snap
            bpy.context.tool_settings.snap_element = NP020PD.snap_element
            bpy.context.tool_settings.snap_target = NP020PD.snap_target
            bpy.context.space_data.pivot_point = NP020PD.pivot_point
            bpy.context.space_data.transform_orientation = NP020PD.trans_orient
            bpy.context.space_data.show_manipulator = NP020PD.show_manipulator
            if NP020PD.acob is not None:
                bpy.context.view_layer.objects.active = NP020PD.acob
                bpy.ops.object.mode_set(mode=NP020PD.edit_mode)
            np_print('05_run_NAV_esc_right_any_CANCELLED')
            return{'CANCELLED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('05_run_NAV_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}
        np_print('05_run_NAV_RUNNING_MODAL')
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('05_run_NAV_INVOKE_a')
        flag = NP020PD.flag
        np_print('flag=', flag)
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag == 'NAVIGATE':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_px_NAV, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('05_run_NAV_INVOKE_a_RUNNING_MODAL')
            return {'RUNNING_MODAL'}
        else:
            np_print('05_run_NAV_INVOKE_a_FINISHED')
            return {'FINISHED'}


# Changing the mode of operating and leaving start point at the first
# snap, continuing with just the end point:

class NP020PDChangePhase(bpy.types.Operator):
    bl_idname = "object.np_pd_change_phase"
    bl_label = "NP PD Change Phase"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('06_change_phase_START')
        NP020PD.phase = 1
        np_print('NP020PD.phase=', NP020PD.phase)
        start = NP020PD.start
        end = NP020PD.end
        startloc3d = start.location
        endloc3d = end.location
        NP020PD.startloc3d = startloc3d
        NP020PD.endloc3d = endloc3d
        bpy.ops.object.select_all(action='DESELECT')
        end.select_set(True)
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = NP020PD.snap
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        NP020PD.flag = 'TRANSLATE'
        np_print('06_change_phase_END_flag_TRANSLATE')
        return {'FINISHED'}


# Defining the operator that will hold the end result in the viewport and let the user navigate around it for documentation

class NP020PDHoldResult(bpy.types.Operator):
    bl_idname = 'object.np_pd_hold_result'
    bl_label = 'NP PD Hold Result'
    bl_options = {'INTERNAL'}

    np_print('07_HOLD_START')

    def modal(self, context, event):
        context.area.tag_redraw()
        selob = NP020PD.selob
        start = NP020PD.start
        end = NP020PD.end

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        elif event.type in ('LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE') and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PD.flag = 'PASS'
            np_print('07_HOLD_left_release_FINISHED')
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
        # this actually begins when user RELEASES esc or rightmouse, PRESS is
        # taken by transform.translate operator
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.object.select_all(action='DESELECT')
            start.select_set(True)
            end.select_set(True)
            bpy.ops.object.delete('EXEC_DEFAULT')
            for ob in selob:
                ob.select_set(True)
            NP020PD.startloc3d = (0.0, 0.0, 0.0)
            NP020PD.endloc3d = (0.0, 0.0, 0.0)
            NP020PD.phase = 0
            NP020PD.start = None
            NP020PD.end = None
            NP020PD.dist = None
            NP020PD.flag = 'TRANSLATE'
            NP020PD.snap = 'VERTEX'
            bpy.context.tool_settings.use_snap = NP020PD.use_snap
            bpy.context.tool_settings.snap_element = NP020PD.snap_element
            bpy.context.tool_settings.snap_target = NP020PD.snap_target
            bpy.context.space_data.pivot_point = NP020PD.pivot_point
            bpy.context.space_data.transform_orientation = NP020PD.trans_orient
            bpy.context.space_data.show_manipulator = NP020PD.show_manipulator
            if NP020PD.acob is not None:
                bpy.context.view_layer.objects.active = NP020PD.acob
                bpy.ops.object.mode_set(mode=NP020PD.edit_mode)
            np_print('07_HOLD_esc_right_CANCELLED')
            return{'CANCELLED'}

        np_print('07_HOLD_PASS_THROUGH')
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        flag = NP020PD.flag
        np_print('flag=', flag)
        np_print('07_HOLD_INVOKE_a')
        addon_prefs = context.preferences.addons[__package__].preferences
        hold = addon_prefs.nppd_hold
        if hold:
            if context.area.type == 'VIEW_3D':
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(
                    draw_callback_px_TRANS, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                NP020PD.flag = 'HOLD'
                np_print('07_HOLD_INVOKE_a_RUNNING_MODAL')
                return {'RUNNING_MODAL'}
            else:
                self.report(
                    {'WARNING'},
                    "View3D not found, cannot run operator")
                np_print('07_HOLD_INVOKE_a_CANCELLED')
                return {'CANCELLED'}
        else:
            np_print('07_HOLD_INVOKE_a_FINISHED')
            return {'FINISHED'}


# Deleting the anchors after succesfull translation and reselecting
# previously selected objects:

class NP020PDDeletePoints(bpy.types.Operator):
    bl_idname = "object.np_pd_delete_points"
    bl_label = "NP PD Delete Points"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences
        dist = NP020PD.dist
        step = addon_prefs.nppd_step
        info = addon_prefs.nppd_info
        clip = addon_prefs.nppd_clip
        np_print('07_delete_points_START')
        if info:
            np_print('GO info')
            self.report({'INFO'}, dist)
        if clip:
            startloc3d = NP020PD.startloc3d
            endloc3d = NP020PD.endloc3d
            le = (
                mathutils.Vector(
                    endloc3d) - mathutils.Vector(
                        startloc3d)).length
            le = str(abs(round(le, 4)))
            bpy.context.window_manager.clipboard = le
        selob = NP020PD.selob
        start = NP020PD.start
        end = NP020PD.end
        bpy.ops.object.select_all(action='DESELECT')
        start.select_set(True)
        end.select_set(True)
        bpy.ops.object.delete('EXEC_DEFAULT')
        for ob in selob:
            ob.select_set(True)
        NP020PD.startloc3d = (0.0, 0.0, 0.0)
        NP020PD.endloc3d = (0.0, 0.0, 0.0)
        NP020PD.phase = 0
        if step == 'simple':
            NP020PD.snap = 'VERTEX'
        NP020PD.flag = 'TRANSLATE'
        NP020PD.start = None
        NP020PD.end = None
        NP020PD.dist = None
        bpy.context.tool_settings.use_snap = NP020PD.use_snap
        bpy.context.tool_settings.snap_element = NP020PD.snap_element
        bpy.context.tool_settings.snap_target = NP020PD.snap_target
        bpy.context.space_data.pivot_point = NP020PD.pivot_point
        bpy.context.space_data.transform_orientation = NP020PD.trans_orient
        bpy.context.space_data.show_manipulator = NP020PD.show_manipulator
        if NP020PD.acob is not None:
            bpy.context.view_layer.objects.active = NP020PD.acob
            bpy.ops.object.mode_set(mode=NP020PD.edit_mode)

        if step == 'simple':
            np_print('07_delete_points_END_cancelled')
            return {'CANCELLED'}
        if step == 'continuous':
            np_print('07_delete_points_END_FINISHED')
            return {'FINISHED'}



# This is the actual addon process, the algorithm that defines the order
# of operator activation inside the main macro:

def register():

    #bpy.app.handlers.scene_update_post.append(scene_update)

    for i in range(1, 15):
        NP020PointDistance.define('OBJECT_OT_np_pd_get_selection')
        NP020PointDistance.define('OBJECT_OT_np_pd_read_mouse_loc')
        NP020PointDistance.define('OBJECT_OT_np_pd_add_points')
        for i in range(1, 15):
            NP020PointDistance.define('OBJECT_OT_np_pd_run_translate')
            NP020PointDistance.define('OBJECT_OT_np_pd_run_navigate')
        NP020PointDistance.define('OBJECT_OT_np_pd_change_phase')
        for i in range(1, 15):
            NP020PointDistance.define('OBJECT_OT_np_pd_run_translate')
            NP020PointDistance.define('OBJECT_OT_np_pd_run_navigate')
        NP020PointDistance.define('OBJECT_OT_np_pd_hold_result')
        NP020PointDistance.define('OBJECT_OT_np_pd_delete_points')


def unregister():

    # bpy.app.handlers.scene_update_post.remove(scene_update)

    pass
