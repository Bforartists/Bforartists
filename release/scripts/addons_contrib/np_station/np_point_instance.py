

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

DESCRIPTION:

Makes a copy (duplicate) of objects using snap points. Emulates the functionality of the standard 'copy' command in CAD applications, with vertex snapping. Optionally, using selected objects and last distance used, makes an array of selected objects.


INSTALLATION:

Unzip and place .py file to scripts / addons_contrib folder. In User Preferences / Addons tab, search with Testing filter - NP Point Copy and check the box.
Now you have the operator in your system. If you press Save User Preferences, you will have it at your disposal every time you run Blender.


SHORTCUTS:

After successful installation of the addon, the NP Point Copy operator should be registered in your system. Enter User Preferences / Input, and under that, 3DView / Object mode. At the bottom of the list click the 'Add new' button. In the operator field type object.np_point_copy_xxx (xxx being the number of the version) and assign a shortcut key of your preference. At the moment i am using 'C' for 'copy', as in standard CAD applications. I rarely use circle selection so letter 'C' is free.


USAGE:

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


IMPORTANT PERFORMANCE NOTES:

None so far.

'''

bl_info = {
    'name':'NP 020 Point Instance',
    'author':'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Duplicates selected objects as linked instances using "take" and "place" snap points',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bmesh
import bgl
import blf
import mathutils
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix
from blf import ROTATION
from math import radians
from bpy.props import *

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *


# Defining the main class - the macro:

class NP020PointInstance(bpy.types.Macro):
    bl_idname = 'object.np_020_point_instance'
    bl_label = 'NP 020 Point Instance'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020PI:

    take = None
    place = None
    takeloc3d = (0.0,0.0,0.0)
    placeloc3d = (0.0,0.0,0.0)
    dist = None
    mode = 'MOVE'
    flag = 'NONE'
    deltavec = Vector ((0, 0, 0))
    deltavec_safe = Vector ((0, 0, 0))


# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:

@persistent
def NPPI_scene_update(context):

    #np_print('00_SceneUpdate_START')
    if bpy.data.objects.is_updated:
        np_print('NPPI_update1')
        mode = NP020PI.mode
        flag = NP020PI.flag
        #np_print(mode, flag)
        take = NP020PI.take
        place = NP020PI.place
        if flag in ('RUNTRANSZERO', 'RUNTRANSFIRST','RUNTRANSNEXT', 'NAVTRANSZERO', 'NAVTRANSFIRST', 'NAVTRANSNEXT'):
            np_print('NPPI_update2')
            NP020PI.takeloc3d = take.location
            NP020PI.placeloc3d = place.location
    #np_print('up3')
    #np_print('00_SceneUpdate_FINISHED')


# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPPIGetContext(bpy.types.Operator):
    bl_idname = 'object.np_pi_get_context'
    bl_label = 'NP PI Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.selected_objects == []:
            self.report({'WARNING'}, "Please select objects first")
            return {'CANCELLED'}
        NP020PI.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020PI.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020PI.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020PI.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020PI.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020PI.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020PI.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020PI.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020PI.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020PI.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020PI.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020PI.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020PI.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020PI.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020PI.edit_mode = 'PARTICLE_EDIT'
        return {'FINISHED'}
        # Changing to OBJECT mode which will be the context for the procedure:
        if bpy.context.mode not in ('OBJECT'):
            bpy.ops.object.mode_set(mode = 'OBJECT')
        # De-selecting objects in prepare for other processes in the script:
        bpy.ops.object.select_all(action = 'DESELECT')
        np_print('01_ReadContext_FINISHED', ';', 'flag = ', NP020PI.flag)
        return {'FINISHED'}


# Defining the operator for aquiring the list of selected objects and storing them for later re-calls:

class NPPIGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_pi_get_selection'
    bl_label = 'NP PI Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # Reading and storing the selection:
        NP020PI.selob = bpy.context.selected_objects
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and store it as a location for placing the 'take' and 'place' points under the mouse:

class NPPIGetMouseloc(bpy.types.Operator):
    bl_idname = 'object.np_pi_get_mouseloc'
    bl_label = 'NP PI Get Mouseloc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector/5
        NP020PI.enterloc = copy.deepcopy(enterloc)
        #np_print('02_RadMouseloc_FINISHED', ';', 'flag = ', NP020PI.flag)
        return{'FINISHED'}

    def invoke(self,context,event):
        args = (self,context)
        context.window_manager.modal_handler_add(self)
        #np_print('02_ReadMouseloc_INVOKED_FINISHED', ';', 'flag = ', NP020PI.flag)
        return {'RUNNING_MODAL'}


# Defining the operator that will generate 'take' and 'place' points at the spot marked by mouse, preparing for translation:

class NPPIAddHelpers(bpy.types.Operator):
    bl_idname = 'object.np_pi_add_helpers'
    bl_label = 'NP PI Add Helpers'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_AddHelpers_START', ';', 'flag = ', NP020PI.flag)
        enterloc = NP020PI.enterloc
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        take = bpy.context.active_object
        take.name = 'NP_PI_take'
        NP020PI.take = take
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        place = bpy.context.active_object
        place.name = 'NP_PI_place'
        NP020PI.place = place
        return{'FINISHED'}


# Defining the operator that will change some of the system settings and prepare objects for the operation:

class NPPIPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_pi_prepare_context'
    bl_label = 'NP PI Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        take = NP020PI.take
        place = NP020PI.place
        take.select_set(True)
        place.select_set(True)
        bpy.context.view_layer.objects.active = place
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = 'VERTEX'
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        NP020PI.flag = 'RUNTRANSZERO'
        return{'FINISHED'}


# Defining the operator that will let the user translate take and place points to the desired 'take' location. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPPIRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_pi_run_translate'
    bl_label = 'NP PI Run Translate'
    bl_options = {'INTERNAL'}

    #np_print('04_RunTrans_START',';','NP020PI.flag = ', NP020PI.flag)
    count = 0

    def modal(self,context,event):
        context.area.tag_redraw()
        flag = NP020PI.flag
        take = NP020PI.take
        place = NP020PI.place
        selob = NP020PI.selob
        self.count += 1

        if self.count == 1:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            np_print('04_RunTrans_count_1_INVOKE_DEFAULT', ';', 'flag = ', NP020PI.flag)

        elif event.type in ('LEFTMOUSE','RET','NUMPAD_ENTER') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANSZERO':
                take.select_set(False)
                place.select_set(False)
                NP020PI.firsttake3d = copy.deepcopy(take.location)
                for ob in selob:
                   ob.select_set(True)
                bpy.ops.object.duplicate(linked = True)
                NP020PI.nextob = bpy.context.selected_objects
                NP020PI.prevob = selob
                place.select_set(True)
                NP020PI.flag = 'RUNTRANSFIRST_break'
            elif flag == 'RUNTRANSFIRST':
                NP020PI.deltavec_safe = copy.deepcopy(NP020PI.deltavec)
                np_print('deltavec_safe = ', NP020PI.deltavec_safe)
                NP020PI.ar13d = copy.deepcopy(take.location)
                NP020PI.ar23d = copy.deepcopy(place.location)
                place.select_set(False)
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in NP020PI.selob:
                    ob.select_set(True)
                bpy.ops.object.duplicate(linked = True)
                value = (place.location - NP020PI.firsttake3d).to_tuple(4)
                bpy.ops.transform.translate(value = value)
                bpy.ops.object.duplicate()
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                NP020PI.arob = prevob
                NP020PI.prevob = nextob
                NP020PI.nextob = bpy.context.selected_objects
                take.location = copy.deepcopy(place.location)
                place.select_set(True)
                bpy.context.view_layer.objects.active = place
                NP020PI.flag = 'RUNTRANSNEXT_break'
            elif flag == 'RUNTRANSNEXT':
                NP020PI.deltavec_safe = copy.deepcopy(NP020PI.deltavec)
                np_print('deltavec_safe = ', NP020PI.deltavec_safe)
                NP020PI.ar13d = copy.deepcopy(take.location)
                NP020PI.ar23d = copy.deepcopy(place.location)
                place.select_set(False)
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in NP020PI.selob:
                    ob.select_set(True)
                bpy.ops.object.duplicate(linked = True)
                value = (place.location - NP020PI.firsttake3d).to_tuple(4)
                bpy.ops.transform.translate(value = value)
                bpy.ops.object.duplicate()
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                NP020PI.arob = prevob
                NP020PI.prevob = nextob
                NP020PI.nextob = bpy.context.selected_objects
                take.location = copy.deepcopy(place.location)
                place.select_set(True)
                NP020PI.flag = 'RUNTRANSNEXT_break'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            np_print('04_RunTrans_alt_left_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type == 'SPACE' and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            take.hide = True
            place.hide = True
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            co2d = self.co2d
            region = context.region
            rv3d = context.region_data
            away = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) - place.location
            away = away.length
            placeloc3d = NP020PI.placeloc3d
            awayloc = copy.deepcopy(placeloc3d)
            NP020PI.awayloc = awayloc
            NP020PI.away = copy.deepcopy(away)
            if flag == 'RUNTRANSZERO':
                NP020PI.flag = 'NAVTRANSZERO'
            elif flag == 'RUNTRANSFIRST':
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = True
                NP020PI.flag = 'NAVTRANSFIRST'
            elif flag == 'RUNTRANSNEXT':
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = True
                NP020PI.flag = 'NAVTRANSNEXT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            np_print('04_RunTrans_space_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANSZERO':
                NP020PI.flag = 'EXIT'
            elif flag == 'RUNTRANSFIRST':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.selob = prevob
                NP020PI.flag = 'EXIT'
            elif flag == 'RUNTRANSNEXT':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.selob = prevob
                NP020PI.flag = 'EXIT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            np_print('04_RunTrans_rmb_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANSZERO':
                NP020PI.flag = 'EXIT'
            elif flag == 'RUNTRANSFIRST':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.flag = 'EXIT'
            elif flag == 'RUNTRANSNEXT':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                NP020PI.selob = prevob
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.flag = 'EXIT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            np_print('04_RunTrans_rmb_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        np_print('04_RunTrans_count_PASS_THROUGH',';','flag = ', NP020PI.flag)
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        #np_print('04_RunTrans_INVOKE_START')
        flag = NP020PI.flag
        selob = NP020PI.selob
        #np_print('flag = ', flag)
        if context.area.type == 'VIEW_3D':
            if flag in ('RUNTRANSZERO', 'RUNTRANSFIRST', 'RUNTRANSNEXT'):
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_RunTranslate, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                np_print('04_RunTrans_INVOKED_RUNNING_MODAL',';','flag = ', NP020PI.flag)
                return {'RUNNING_MODAL'}
            else:
                #np_print('04_RunTrans_INVOKE_DECLINED_FINISHED',';','flag = ', flag)
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            flag = 'WARNING3D'
            NP020PI.flag = flag
            np_print('04_RunTrans_INVOKE_DECLINED_FINISHED',';','flag = ', NP020PI.flag)
            return {'CANCELLED'}


# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of RunTranslate operator:

def DRAW_RunTranslate(self, context):

    np_print('04_DRAW_RunTrans_START',';','flag = ', NP020PI.flag)

    addon_prefs = context.preferences.addons[__package__].preferences


    flag = NP020PI.flag
    takeloc3d = NP020PI.takeloc3d
    placeloc3d = NP020PI.placeloc3d

    region = context.region
    rv3d = context.region_data

    if flag in ('RUNTRANSZERO', 'RUNTRANSFIRST', 'RUNTRANSNEXT'):
        takeloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, takeloc3d)
        placeloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, placeloc3d)
    if flag == 'NAVTRANSZERO':
        takeloc2d = self.co2d
        placeloc2d = self.co2d
    if flag in ('NAVTRANSFIRST', 'NAVTRANSNEXT'):
        takeloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, takeloc3d)
        placeloc2d = self.co2d

    '''
    if flag in ('RUNTRANSNEXT', 'NAVTRANSNEXT'):
        ardist_num = NP020PI.ar23d - NP020PI.ar13d
        ardist_num = ardist_num.length * dist_scale
        ar12d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PI.ar13d)
        ar22d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PI.ar23d)
        ardist_num = abs(round(ardist_num,2))
        if suffix is not None:
            ardist = str(ardist_num)+suffix
        else:
            ardist = str(ardist_num)
        NP020PI.ardist = ardist
        ardist_loc = (ar12d + ar22d) /2
    '''

    # DRAWING START:
    bgl.glEnable(bgl.GL_BLEND)

    if flag == 'RUNTRANSZERO':
        instruct = 'select the take point'
        keys_aff = 'LMB - confirm, CTRL - snap, MMB - lock axis, NUMPAD - value'
        keys_nav = 'SPACE - navigate'
        keys_neg = 'ESC / RMB - cancel copy'

        badge_mode = 'RUN'
        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'RUNTRANSFIRST':
        instruct = 'select the placement point'
        keys_aff = 'LMB - confirm, CTRL - snap, MMB - lock axis, NUMPAD - value'
        keys_nav = 'SPACE - navigate'
        keys_neg = 'ESC / RMB - cancel copy'

        badge_mode = 'RUN'
        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'RUNTRANSNEXT':
        instruct = 'select the placement point'
        keys_aff = 'LMB - confirm, CTRL - snap, MMB - lock axis, NUMPAD - value'
        keys_nav = 'SPACE - navigate'
        keys_neg = 'ESC / RMB - cancel current'

        badge_mode = 'RUN'
        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'NAVTRANSZERO':
        instruct = 'navigate for better placement of take point'
        keys_aff = 'MMB / SCROLL - navigate'
        keys_nav = 'LMB / SPACE - leave navigate'
        keys_neg = 'ESC / RMB - cancel copy'

        badge_mode = 'NAV'
        message_main = 'NAVIGATE'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'NAVTRANSFIRST':
        instruct = 'navigate for better selection of placement point'
        keys_aff = 'MMB / SCROLL - navigate'
        keys_nav = 'LMB / SPACE - leave navigate'
        keys_neg = 'ESC / RMB - cancel copy'

        badge_mode = 'NAV'
        message_main = 'NAVIGATE'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'NAVTRANSNEXT':
        instruct = 'navigate for better selection of placement point'
        keys_aff = 'MMB / SCROLL - navigate'
        keys_nav = 'LMB / SPACE - leave navigate'
        keys_neg = 'ESC / RMB - cancel current'

        badge_mode = 'NAV'
        message_main = 'NAVIGATE'
        message_aux = None
        aux_num = None
        aux_str = None

    # ON-SCREEN INSTRUCTIONS:

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)

    # MOUSE BADGE:

    co2d = placeloc2d

    symbol = [[23, 34], [23, 32], [19, 32], [19, 36], [21, 36], [21, 38], [25, 38], [25, 34], [23, 34], [23, 36], [21, 36]]

    display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str)

    # LINE:

    display_line_between_two_points(region, rv3d, takeloc3d, placeloc3d)

    # DISTANCE:

    display_distance_between_two_points(region, rv3d, takeloc3d, placeloc3d)
    NP020PI.deltavec = copy.deepcopy(display_distance_between_two_points(region, rv3d, takeloc3d, placeloc3d)[0])

    #DRAWING END:
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('04_DRAW_RunTrans_FINISHED',';','flag = ', NP020PI.flag)


# Defining the operator that will enable navigation if user calls it:

class NPPINavTranslate(bpy.types.Operator):
    bl_idname = "object.np_pi_nav_translate"
    bl_label = "NP PI Nav Translate"
    bl_options = {'INTERNAL'}

    np_print('04a_NavTrans_START',';','flag = ', NP020PI.flag)

    def modal(self,context,event):
        context.area.tag_redraw()
        flag = NP020PI.flag
        take = NP020PI.take
        place = NP020PI.place

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            pointloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector * NP020PI.away
            NP020PI.placeloc3d = copy.deepcopy(pointloc)
            np_print('04a_NavTrans_mousemove',';','flag = ', NP020PI.flag)

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector*NP020PI.away
            placeloc3d = NP020PI.placeloc3d
            navdelta = enterloc - NP020PI.awayloc
            take.hide = False
            place.hide = False
            np_print('flag = ', flag)
            if flag == 'NAVTRANSZERO':
                takeloc3d = enterloc
                placeloc3d = enterloc
                take.location = enterloc
                place.location = enterloc
                NP020PI.flag = 'RUNTRANSZERO'
            elif flag == 'NAVTRANSFIRST':
                takeloc3d = NP020PI.takeloc3d
                placeloc3d = enterloc
                place.location = enterloc
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = False
                place.select_set(False)
                bpy.ops.transform.translate(value = navdelta)
                place.select_set(True)
                NP020PI.flag = 'RUNTRANSFIRST'
            elif flag == 'NAVTRANSNEXT':
                takeloc3d = NP020PI.takeloc3d
                placeloc3d = enterloc
                place.location = enterloc
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = False
                place.select_set(False)
                bpy.ops.transform.translate(value = navdelta)
                place.select_set(True)
                NP020PI.flag = 'RUNTRANSNEXT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            NP020PI.take = take
            NP020PI.place = place
            NP020PI.takeloc3d = takeloc3d
            NP020PI.placeloc3d = placeloc3d
            np_print('04a_NavTrans_left_space_FINISHED',';','flag = ', NP020PI.flag)
            return {'FINISHED'}

        elif event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            take.hide = False
            place.hide = False
            if flag == 'NAVTRANSZERO':
                place.select_set(False)
                NP020PI.flag = 'EXIT'
            elif flag == 'NAVTRANSFIRST':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = False
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.flag = 'EXIT'
            elif flag == 'NAVTRANSNEXT':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = False
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                bpy.ops.object.delete('EXEC_DEFAULT')
                NP020PI.flag = 'ARRAYTRANS'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            np_print('04a_NavTrans_rmb_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            take.hide = False
            place.hide = False
            if flag == 'NAVTRANSZERO':
                place.select_set(False)
                NP020PI.flag = 'EXIT'
            elif flag == 'NAVTRANSFIRST':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                for ob in nextob:
                    ob.hide = False
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.flag = 'EXIT'
            elif flag == 'NAVTRANSNEXT':
                place.select_set(False)
                prevob = NP020PI.prevob
                nextob = NP020PI.nextob
                NP020PI.selob = prevob
                for ob in nextob:
                    ob.hide = False
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select_set(True)
                NP020PI.flag = 'EXIT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PI.flag = 'EXIT'
            np_print('04a_NavTrans_esc_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('04a_NavTrans_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}

        np_print('04a_NavTrans_INVOKED_RUNNING_MODAL',';','flag = ', NP020PI.flag)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        #np_print('04a_NavTrans_INVOKE_START')
        flag = NP020PI.flag
        #np_print('flag = ', flag)
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag in ('NAVTRANSZERO', 'NAVTRANSFIRST', 'NAVTRANSNEXT'):
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_RunTranslate, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('04a_run_NAV_INVOKE_a_RUNNING_MODAL',';','flag = ', NP020PI.flag)
            return {'RUNNING_MODAL'}
        else:
            #np_print('04a_run_NAV_INVOKE_a_FINISHED',';','flag = ', flag)
            return {'FINISHED'}


# Defining the operator that will enable the return to RunTrans cycle by reseting the 'break' flag:

class NPPIPrepareNext(bpy.types.Operator):
    bl_idname = 'object.np_pi_prepare_next'
    bl_label = 'NP PI Prepare Next'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('05_PrepareNext_START',';','flag = ', NP020PI.flag)
        if NP020PI.flag == 'RUNTRANSFIRST_break':
            NP020PI.flag = 'RUNTRANSFIRST'
        if NP020PI.flag == 'RUNTRANSNEXT_break':
            NP020PI.flag = 'RUNTRANSNEXT'
        np_print('05_PrepareNext_FINISHED',';','flag = ', NP020PI.flag)
        return{'FINISHED'}

'''
# Defining the operator that will collect the necessary data and the generate the array with an input dialogue for number of items:

class NPPIArrayTranslate(bpy.types.Operator):
    bl_idname = "object.np_pi_array_translate"
    bl_label = "NP PI Array Translate"
    bl_options = {'INTERNAL'}

    np_print('06_ArrayTrans_START',';','flag = ', NP020PI.flag)

    def modal(self,context,event):
        np_print('06_ArrayTrans_START',';','flag = ', NP020PI.flag)
        context.area.tag_redraw()
        flag = NP020PI.flag
        ardict = NP020PI.ardict
        arob = NP020PI.arob
        np_print('ardict = ', ardict)

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            np_print('04a_NavTrans_mousemove',';','flag = ', NP020PI.flag)

        elif event.type in ('LEFTMOUSE', 'RIGHTMOUSE') and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PI.flag = 'EXIT'
            np_print('06_ArrayTrans_rmb_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.ctrl and event.type == 'WHEELUPMOUSE' or event.type == 'UP_ARROW' and event.value == 'PRESS':
            for ob in arob:
                ar = ardict[ob][0]
                deltavec_start = Vector(ardict[ob][1])
                count = ardict[ob][2]
                if ar.fit_type == 'FIXED_COUNT':
                    ar.count = ar.count+1
                    count = count + 1
                elif ar.fit_type == 'FIT_LENGTH' and count == 3:
                    ar.fit_type = 'FIXED_COUNT'
                    ar.constant_offset_displace = deltavec_start
                    ar.count = 2
                    count = 2
                elif ar.fit_type == 'FIT_LENGTH' and count >3:
                    count = count - 1
                    ar.constant_offset_displace.length = ar.fit_length/(count-1)
                ardict[ob][2] = count
            NP020PI.fit_type = ar.fit_type
            NP020PI.count = count
            bpy.context.scene.update()

        elif event.ctrl and event.type == 'WHEELDOWNMOUSE' or event.type == 'DOWN_ARROW' and event.value == 'PRESS':
            for ob in arob:
                ar = ardict[ob][0]
                deltavec_start = Vector(ardict[ob][1])
                count = ardict[ob][2]
                if ar.fit_type == 'FIXED_COUNT' and count > 2:
                    ar.count = ar.count-1
                    count = count - 1
                elif ar.fit_type == 'FIXED_COUNT' and count == 2:
                    ar.fit_type = 'FIT_LENGTH'
                    ar.fit_length = deltavec_start.length
                    ar.constant_offset_displace.length = ar.fit_length/2
                    count = 3
                elif ar.fit_type == 'FIT_LENGTH':
                    count = count + 1
                    ar.constant_offset_displace.length = ar.fit_length/(count-1)
                ardict[ob][2] = count
            NP020PI.fit_type = ar.fit_type
            NP020PI.count = count
            bpy.context.scene.update()

        elif event.type in ('RET', 'NUMPAD_ENTER') and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            selob = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            for ob in arob:
                ob.select = True
                bpy.ops.object.modifier_apply(modifier = ardict[ob][0].name)
                ob.select = False
            for ob in selob:
                ob.select = True
            NP020PI.flag = 'EXIT'
            np_print('06_ArrayTrans_enter_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.ctrl and event.type == 'TAB' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if NP020PI.fit_type == 'FIXED_COUNT':
                value = NP020PI.ar23d - NP020PI.ar13d
            else:
                value = (NP020PI.ar23d - NP020PI.ar13d)/(NP020PI.count - 1)
            selob = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            for ob in arob:
                ob.select = True
                ob.modifiers.remove(ardict[ob][0])
                np_print('NP020PI.count', NP020PI.count)
                for i in range(1, NP020PI.count):
                    bpy.ops.object.duplicate(linked = True)
                    bpy.ops.transform.translate(value = value)
                bpy.ops.object.select_all(action='DESELECT')
            for ob in selob:
                ob.select = True
            NP020PI.flag = 'EXIT'
            np_print('06_ArrayTrans_ctrl_tab_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type == 'TAB' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if NP020PI.fit_type == 'FIXED_COUNT':
                value = NP020PI.ar23d - NP020PI.ar13d
            else:
                value = (NP020PI.ar23d - NP020PI.ar13d)/(NP020PI.count - 1)
            selob = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            for ob in arob:
                ob.select = True
                ob.modifiers.remove(ardict[ob][0])
                np_print('NP020PI.count', NP020PI.count)
                for i in range(1, NP020PI.count):
                    bpy.ops.object.duplicate()
                    bpy.ops.transform.translate(value = value)
                bpy.ops.object.select_all(action='DESELECT')
            for ob in selob:
                ob.select = True
            NP020PI.flag = 'EXIT'
            np_print('06_ArrayTrans_tab_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type == 'ESC' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            for ob in arob:
                ob.modifiers.remove(ardict[ob][0])
            NP020PI.flag = 'EXIT'
            np_print('06_ArrayTrans_esc_FINISHED',';','flag = ', NP020PI.flag)
            return{'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('06_ArrayTrans_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}

        np_print('06_ArrayTrans_INVOKED_RUNNING_MODAL',';','flag = ', NP020PI.flag)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('06_ArrayTrans_INVOKE_START')
        flag = NP020PI.flag
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag == 'ARRAYTRANS':
            arob = NP020PI.arob
            np_print('deltavec_safe = ', NP020PI.deltavec_safe)
            ardict = {}
            for ob in arob:
                deltavec = copy.deepiopy(NP020PI.deltavec_safe)
                np_print('deltavec = ', deltavec)
                loc, rot, sca = ob.matrix_world.decompose()
                rot = ob.rotation_euler
                rot = rot.to_quaternion()
                sca = ob.scale
                np_print(loc, rot, sca, ob.matrix_world)
                np_print('deltavec = ', deltavec)
                deltavec.rotate(rot.conjugated())
                np_print('sca.length', sca.length)
                deltavec[0] = deltavec[0] / sca[0]
                deltavec[1] = deltavec[1] / sca[1]
                deltavec[2] = deltavec[2] / sca[2]
                np_print('deltavec = ', deltavec)
                deltavec_trans = deltavec.to_tuple(4)
                arcur = ob.modifiers.new(name = '', type = 'ARRAY')
                arcur.fit_type = 'FIXED_COUNT'
                arcur.use_relative_offset = False
                arcur.use_constant_offset = True
                arcur.constant_offset_displace = deltavec_trans
                arcur.count = 5
                ardict[ob] = []
                ardict[ob].append(arcur)
                ardict[ob].append(deltavec_trans)
                ardict[ob].append(arcur.count)
            NP020PI.selob = arob
            NP020PI.ardict = ardict
            NP020PI.count = 5
            NP020PI.fit_type = 'FIXED_COUNT'
            selob = NP020PI.selob
            lenselob = len(selob)
            for i, ob in enumerate(selob):
                ob.select = True
                if i == lenselob-1:
                    bpy.context.scene.objects.active = ob
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_ArrayTrans, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('06_ArayTrans_INVOKE_a_RUNNING_MODAL',';','flag = ', NP020PI.flag)
            return {'RUNNING_MODAL'}
        else:
            np_print('06_ArrayTrans_INVOKE_DENIED',';','flag = ', NP020PI.flag)
            return {'FINISHED'}
'''

'''
# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of ArrayTrans operator:

def DRAW_ArrayTrans(self, context):

    np_print('06a_DRAW_ArrayTrans_START',';','flag = ', NP020PI.flag)

    addon_prefs = context.preferences.addons[__package__].preferences
    badge = addon_prefs.nppi_badge
    badge_size = addon_prefs.nppi_badge_size

    # DRAWING START:
    bgl.glEnable(bgl.GL_BLEND)

    # MOUSE BADGE:
    if badge == True:
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        icon = copy.deepcopy(NP020PI.icon)
        np_print('icon', icon)
        ipx = 29
        ipy = 33
        for co in square:
            co[0] = round((co[0] * badge_size),0) -(badge_size*10) + self.co2d[0]
            co[1] = round((co[1] * badge_size),0) -(badge_size*25) + self.co2d[1]
        for co in rectangle:
            co[0] = round((co[0] * badge_size),0) -(badge_size*10) + self.co2d[0]
            co[1] = round((co[1] * badge_size),0) -(badge_size*25) + self.co2d[1]
        for co in icon:
            co[0] = round((co[0] * badge_size),0) -(badge_size*10) + self.co2d[0]
            co[1] = round((co[1] * badge_size),0) -(badge_size*25) + self.co2d[1]
        ipx = round((ipx * badge_size),0) -(badge_size*10) + self.co2d[0]
        ipy = round((ipy * badge_size),0) -(badge_size*25) + self.co2d[1]
        ipsize = int(6* badge_size)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in square:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        bgl.glColor4f(0.5, 0.75, 0.0, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in rectangle:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        bgl.glColor4f(0.2, 0.15, 0.55, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in rectangle:
            bgl.glVertex2f(x,(y-(badge_size*35)))
        bgl.glEnd()
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        font_id = 0
        blf.position(font_id,ipx,ipy,0)
        blf.size(font_id,ipsize,72)
        blf.draw(font_id,'NAVIGATE')
        blf.position(font_id,ipx,(ipy-(badge_size*35)),0)
        blf.size(font_id,ipsize,72)
        blf.draw(font_id,'CTRL+SCRL')
        bgl.glColor4f(1,1,1,1)
        blf.position(font_id,ipx,(int(ipy-badge_size*25)),0)
        blf.size(font_id,(int(badge_size*24)),72)
        if NP020PI.fit_type == 'FIT_LENGTH':
            blf.draw(font_id,'/' + str(NP020PI.count))
        else:
            blf.draw(font_id,str(NP020PI.count))
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x,y in icon:
            bgl.glVertex2f(x,y)
        bgl.glEnd()

    # ON-SCREEN INSTRUCTIONS:
    font_id = 0
    bgl.glColor4f(1,1,1,0.35)
    blf.size(font_id,88,72)
    blf.position(font_id,5,74,0)
    blf.draw(font_id,'N')
    blf.size(font_id,28,72)
    blf.position(font_id,22,74,0)
    blf.draw(font_id,'P')
    blf.enable(font_id, ROTATION)
    bgl.glColor4f(1,1,1,0.40)
    ang = radians(90)
    blf.size(font_id,19,72)
    blf.rotation(font_id,ang)
    blf.position(font_id,78,73,0)
    blf.draw(font_id,'PI 002')
    blf.disable(font_id, ROTATION)

    main='SPECIFY NUMBER OF ITEMS IN ARRAY'
    bgl.glColor4f(0,0.5,0,1)
    blf.size(font_id,11,72)
    blf.position(font_id,93,105,0)
    blf.draw(font_id,'MMB, SCROLL - navigate')
    blf.position(font_id,93,90,0)
    blf.draw(font_id,'CTRL+SCROLL, UPARROW / DOWNARROW - number of items')
    blf.position(font_id,93,75,0)
    blf.draw(font_id,'LMB, RMB - confirm and keep array, ENTER - apply as one, TAB - apply as separate, CTRL+TAB - apply as instanced')
    bgl.glColor4f(1,0,0,1)
    blf.position(font_id,93,60,0)
    blf.draw(font_id,'ESC - cancel array')
    bgl.glColor4f(0.0, 0.0, 0.0, 0.5)
    blf.position(font_id,93,124,0)
    blf.size(font_id,16,72)
    blf.draw(font_id,main)
    bgl.glColor4f(1,1,1,1)
    blf.position(font_id,94,125,0)
    blf.size(font_id,16,72)
    blf.draw(font_id,main)


    region = context.region
    rv3d = context.region_data
    ar12d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PI.ar13d)
    ar22d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PI.ar23d)
    ardist = NP020PI.ardist
    ardist_loc = (ar12d + ar22d) /2

    # ARMARKERS:
    markersize = badge_size*2.5
    triangle = [[0, 0], [-1, 1], [1, 1]]
    triangle = [[0, 0], [-1, 1], [1, 1]]
    for co in triangle:
        co[0] = int(co[0] * markersize * 3) + ar12d[0]
        co[1] = int(co[1] * markersize * 3) + ar12d[1]
    bgl.glColor4f(0.4, 0.15, 0.75, 1.0)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    for x,y in triangle:
        bgl.glVertex2f(x,y)
    bgl.glEnd()
    triangle = [[0, 0], [-1, 1], [1, 1]]
    for co in triangle:
        co[0] = int(co[0] * markersize * 3) + ar22d[0]
        co[1] = int(co[1] * markersize * 3) + ar22d[1]
    bgl.glColor4f(0.4, 0.15, 0.75, 1.0)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    for x,y in triangle:
        bgl.glVertex2f(x,y)
    bgl.glEnd()

    # AR NUMERICAL DISTANCE:
    np_print('ardist = ', ardist, 'ardist_loc = ', ardist_loc)
    bgl.glColor4f(0.4, 0.15, 0.75, 1.0)
    font_id = 0
    blf.size(font_id, 20, 72)
    blf.position(font_id, ardist_loc[0], ardist_loc[1], 0)
    blf.draw(font_id, ardist)

    #DRAWING END:
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('06a_DRAW_ArrayTrans_FINISHED',';','flag = ', NP020PI.flag)
'''

# Restoring the object selection and system settings from before the operator activation. Deleting the helpers after successful translation, reseting all viewport options and reselecting previously selected objects:

class NPPIRestoreContext(bpy.types.Operator):
    bl_idname = "object.np_pi_restore_context"
    bl_label = "NP PI Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('07_CleanExit_START',';','flag = ', NP020PI.flag)
        flag = NP020PI.flag
        selob = NP020PI.selob
        take = NP020PI.take
        place = NP020PI.place
        bpy.ops.object.select_all(action='DESELECT')
        take.select_set(True)
        place.select_set(True)
        bpy.ops.object.delete('EXEC_DEFAULT')
        lenselob = len(selob)
        for i, ob in enumerate(selob):
            ob.select_set(True)
            if i == lenselob-1:
                bpy.context.view_layer.objects.active = ob
        NP020PI.take = None
        NP020PI.place = None
        NP020PI.takeloc3d = (0.0,0.0,0.0)
        NP020PI.placeloc3d = (0.0,0.0,0.0)
        NP020PI.dist = None
        NP020PI.mode = 'MOVE'
        NP020PI.flag = 'NONE'
        NP020PI.ardict = {}
        NP020PI.deltavec = Vector ((0, 0, 0))
        NP020PI.deltavec_safe = Vector ((0, 0, 0))
        bpy.context.tool_settings.use_snap = NP020PI.use_snap
        bpy.context.tool_settings.snap_element = NP020PI.snap_element
        bpy.context.tool_settings.snap_target = NP020PI.snap_target
        bpy.context.space_data.pivot_point = NP020PI.pivot_point
        bpy.context.space_data.transform_orientation = NP020PI.trans_orient
        #if NP020PI.acob is not None:
            #bpy.context.scene.objects.active = NP020PI.acob
            #bpy.ops.object.mode_set(mode = NP020PI.edit_mode)

        np_print('07_CleanExit_FINISHED',';','flag = ', NP020PI.flag)
        return {'FINISHED'}


'''
# Defining the settings of the addon in the User preferences / addons tab:

class NPPIPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    dist_scale = bpy.props.FloatProperty(
            name='Unit scale',
            description='Distance multiplier (for example, for cm use 100)',
            default=100,
            min=0,
            step=1,
            precision=3)

    suffix = bpy.props.EnumProperty(
        name='Unit suffix',
        items=(("'","'",''), ('"','"',''), ('thou','thou',''), ('km','km',''), ('m','m',''), ('cm','cm',''), ('mm','mm',''), ('nm','nm',''), ('None','None','')),
        default='cm',
        description='Add a unit extension after the numerical distance ')

    badge = bpy.props.BoolProperty(
            name='Mouse badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    badge_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the mouse badge, the default is 2.0',
            default=2,
            min=0.5,
            step=10,
            precision=1)

    col_line_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    col_line_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    col_num_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    col_num_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    col_line_main = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the measurement line, to disable it set alpha to 0.0')

    col_line_shadow = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.25), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the line shadow, to disable it set alpha to 0.0')

    col_num_main = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.75), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number, to disable it set alpha to 0.0')

    col_num_shadow = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number shadow, to disable it set alpha to 0.0')

    def draw(self, context):
        layout = self.layout
        split = layout.split()
        col = split.column()
        col.prop(self, "dist_scale")
        col = split.column()
        col.prop(self, "suffix")
        split = layout.split()
        col = split.column()
        col.label(text='Line Main COLOR')
        col.prop(self, "col_line_main_DEF")
        if self.col_line_main_DEF == False:
            col.prop(self, "col_line_main")
        col = split.column()
        col.label(text='Line Shadow COLOR')
        col.prop(self, "col_line_shadow_DEF")
        if self.col_line_shadow_DEF == False:
            col.prop(self, "col_line_shadow")
        col = split.column()
        col.label(text='Numerical Main COLOR')
        col.prop(self, "col_num_main_DEF")
        if self.col_num_main_DEF == False:
            col.prop(self, "col_num_main")
        col = split.column()
        col.label(text='Numerical Shadow COLOR')
        col.prop(self, "col_num_shadow_DEF")
        if self.col_num_shadow_DEF == False:
            col.prop(self, "col_num_shadow")
        split = layout.split()
        col = split.column()
        col.prop(self, "badge")
        col = split.column()
        if self.badge == True:
            col.prop(self, "badge_size")
        col = split.column()
        col = split.column()
'''

# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    #bpy.utils.register_class(NPPIPreferences)
    #bpy.utils.register_module(__name__)
    bpy.app.handlers.scene_update_post.append(NPPI_scene_update)

    NP020PointInstance.define('OBJECT_OT_np_pi_get_context')
    NP020PointInstance.define('OBJECT_OT_np_pi_get_selection')
    NP020PointInstance.define('OBJECT_OT_np_pi_get_mouseloc')
    NP020PointInstance.define('OBJECT_OT_np_pi_add_helpers')
    NP020PointInstance.define('OBJECT_OT_np_pi_prepare_context')
    for i in range(1, 50):
        for i in range(1, 10):
            NP020PointInstance.define('OBJECT_OT_np_pi_run_translate')
            NP020PointInstance.define('OBJECT_OT_np_pi_nav_translate')
        NP020PointInstance.define('OBJECT_OT_np_pi_prepare_next')
    #NP020PointInstance.define('OBJECT_OT_np_pi_array_translate')
    NP020PointInstance.define('OBJECT_OT_np_pi_restore_context')

def unregister():
    #pass
    #bpy.utils.unregister_class(NPPIPreferences)
    #bpy.utils.unregister_module(__name__)
    bpy.app.handlers.scene_update_post.remove(NPPI_scene_update)
