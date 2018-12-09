

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
    'name':'NP 020 Point Array',
    'author':'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Makes a directional array of selected objects using "take" and "place" snap points',
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

class NP020PointArray(bpy.types.Macro):
    bl_idname = 'object.np_020_point_array'
    bl_label = 'NP 020 Point Array'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020PA:

    take = None
    place = None
    takeloc3d = (0.0,0.0,0.0)
    placeloc3d = (0.0,0.0,0.0)
    dist = None
    mode = 'MOVE'
    flag = 'NONE'
    deltavec = Vector ((0, 0, 0))
    deltavec_safe = Vector ((0, 0, 0))
    prevob = None
    nextob = None

# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:

@persistent
def NPPA_scene_update(context):

    #np_print('00_SceneUpdate_START')
    if bpy.data.objects.is_updated:
        np_print('NPPA_update1')
        mode = NP020PA.mode
        flag = NP020PA.flag
        #np_print(mode, flag)
        take = NP020PA.take
        place = NP020PA.place
        if flag in ('RUNTRANSZERO', 'RUNTRANSFIRST','RUNTRANSNEXT', 'NAVTRANSZERO', 'NAVTRANSFIRST', 'NAVTRANSNEXT'):
            np_print('NPPA_update2')
            NP020PA.takeloc3d = take.location
            NP020PA.placeloc3d = place.location
    #np_print('up3')
    #np_print('00_SceneUpdate_FINISHED')


# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPPAGetContext(bpy.types.Operator):
    bl_idname = 'object.np_pa_get_context'
    bl_label = 'NP PA Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.selected_objects == []:
            self.report({'WARNING'}, "Please select objects first")
            return {'CANCELLED'}
        NP020PA.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020PA.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020PA.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020PA.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020PA.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020PA.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020PA.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020PA.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020PA.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020PA.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020PA.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020PA.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020PA.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020PA.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020PA.edit_mode = 'PARTICLE_EDIT'
        return {'FINISHED'}
        # Changing to OBJECT mode which will be the context for the procedure:
        if bpy.context.mode not in ('OBJECT'):
            bpy.ops.object.mode_set(mode = 'OBJECT')
        # De-selecting objects in prepare for other processes in the script:
        bpy.ops.object.select_all(action = 'DESELECT')
        np_print('01_ReadContext_FINISHED', ';', 'flag = ', NP020PA.flag)
        return {'FINISHED'}


# Defining the operator for aquiring the list of selected objects and storing them for later re-calls:

class NPPAGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_pa_get_selection'
    bl_label = 'NP PA Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # Reading and storing the selection:
        NP020PA.selob = bpy.context.selected_objects
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and store it as a location for placing the 'take' and 'place' points under the mouse:

class NPPAGetMouseloc(bpy.types.Operator):
    bl_idname = 'object.np_pa_get_mouseloc'
    bl_label = 'NP PA Get Mouseloc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector/5
        NP020PA.enterloc = copy.deepcopy(enterloc)
        np_print('02_RadMouseloc_FINISHED', ';', 'flag = ', NP020PA.flag)
        return{'FINISHED'}

    def invoke(self,context,event):
        args = (self,context)
        context.window_manager.modal_handler_add(self)
        np_print('02_ReadMouseloc_INVOKED_FINISHED', ';', 'flag = ', NP020PA.flag)
        return {'RUNNING_MODAL'}


# Defining the operator that will generate 'take' and 'place' points at the spot marked by mouse, preparing for translation:

class NPPAAddHelpers(bpy.types.Operator):
    bl_idname = 'object.np_pa_add_helpers'
    bl_label = 'NP PA Add Helpers'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_AddHelpers_START', ';', 'flag = ', NP020PA.flag)
        enterloc = NP020PA.enterloc
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        take = bpy.context.active_object
        take.name = 'NP_PA_take'
        NP020PA.take = take
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        place = bpy.context.active_object
        place.name = 'NP_PA_place'
        NP020PA.place = place
        return{'FINISHED'}


# Defining the operator that will change some of the system settings and prepare objects for the operation:

class NPPAPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_pa_prepare_context'
    bl_label = 'NP PA Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        take = NP020PA.take
        place = NP020PA.place
        take.select = True
        place.select = True
        bpy.context.scene.objects.active = place
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = 'VERTEX'
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        NP020PA.flag = 'RUNTRANSZERO'
        return{'FINISHED'}


# Defining the operator that will let the user translate take and place points to the desired 'take' location. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPPARunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_pa_run_translate'
    bl_label = 'NP PA Run Translate'
    bl_options = {'INTERNAL'}

    np_print('04_RunTrans_START',';','NP020PA.flag = ', NP020PA.flag)
    count = 0

    def modal(self,context,event):
        context.area.tag_redraw()
        flag = NP020PA.flag
        take = NP020PA.take
        place = NP020PA.place
        selob = NP020PA.selob
        self.count += 1

        if self.count == 1:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            np_print('04_RunTrans_count_1_INVOKE_DEFAULT', ';', 'flag = ', NP020PA.flag)

        elif event.type in ('LEFTMOUSE','RET','NUMPAD_ENTER') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANSZERO':
                take.select = False
                place.select = False
                NP020PA.ar13d = copy.deepcopy(take.location)
                NP020PA.ar23d = copy.deepcopy(place.location)
                NP020PA.firsttake3d = copy.deepcopy(take.location)
                for ob in selob:
                   ob.select = True
                bpy.ops.object.duplicate()
                NP020PA.nextob = bpy.context.selected_objects
                NP020PA.prevob = selob
                place.select = True
                NP020PA.flag = 'RUNTRANSFIRST_break'
            elif flag == 'RUNTRANSFIRST':
                NP020PA.deltavec_safe = copy.deepcopy(NP020PA.deltavec)
                np_print('deltavec_safe = ', NP020PA.deltavec_safe)
                NP020PA.ar13d = copy.deepcopy(take.location)
                NP020PA.ar23d = copy.deepcopy(place.location)
                place.select = False
                bpy.ops.object.duplicate()
                prevob = NP020PA.prevob
                nextob = NP020PA.nextob
                NP020PA.arob = prevob
                NP020PA.prevob = nextob
                NP020PA.nextob = bpy.context.selected_objects
                take.location = copy.deepcopy(place.location)
                place.select = True
                NP020PA.flag = 'ARRAYTRANS'

            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            np_print('04_RunTrans_left_FINISHED',';','flag = ', NP020PA.flag)
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
            placeloc3d = NP020PA.placeloc3d
            awayloc = copy.deepcopy(placeloc3d)
            NP020PA.awayloc = awayloc
            NP020PA.away = copy.deepcopy(away)
            if flag == 'RUNTRANSZERO':
                NP020PA.flag = 'NAVTRANSZERO'
            elif flag == 'RUNTRANSFIRST':
                nextob = NP020PA.nextob
                for ob in nextob:
                    ob.hide = True
                NP020PA.flag = 'NAVTRANSFIRST'
            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            np_print('04_RunTrans_space_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANSZERO':
                NP020PA.flag = 'EXIT'
            elif flag == 'RUNTRANSFIRST':
                NP020PA.deltavec_safe = copy.deepcopy(NP020PA.deltavec)
                np_print('deltavec_safe = ', NP020PA.deltavec_safe)
                NP020PA.ar13d = copy.deepcopy(take.location)
                NP020PA.ar23d = copy.deepcopy(place.location)
                place.select = False
                bpy.ops.object.duplicate()
                prevob = NP020PA.prevob
                nextob = NP020PA.nextob
                NP020PA.arob = prevob
                NP020PA.prevob = nextob
                NP020PA.nextob = bpy.context.selected_objects
                take.location = copy.deepcopy(place.location)
                place.select = True
                NP020PA.flag = 'ARRAYTRANS'
            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            np_print('04_RunTrans_rmb_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANSZERO':
                NP020PA.flag = 'EXIT'
            elif flag == 'RUNTRANSFIRST':
                place.select = False
                prevob = NP020PA.prevob
                nextob = NP020PA.nextob
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select = True
                NP020PA.flag = 'EXIT'
            elif flag == 'RUNTRANSNEXT':
                place.select = False
                prevob = NP020PA.prevob
                nextob = NP020PA.nextob
                NP020PA.selob = prevob
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select = True
                NP020PA.flag = 'EXIT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            np_print('04_RunTrans_rmb_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        np_print('04_RunTrans_count_PASS_THROUGH',';','flag = ', NP020PA.flag)
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('04_RunTrans_INVOKE_START')
        flag = NP020PA.flag
        selob = NP020PA.selob
        np_print('flag = ', flag)
        if context.area.type == 'VIEW_3D':
            if flag in ('RUNTRANSZERO', 'RUNTRANSFIRST'):
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_RunTranslate, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                np_print('04_RunTrans_INVOKED_RUNNING_MODAL',';','flag = ', NP020PA.flag)
                return {'RUNNING_MODAL'}
            else:
                np_print('04_RunTrans_INVOKE_DECLINED_FINISHED',';','flag = ', flag)
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            flag = 'WARNING3D'
            NP020PA.flag = flag
            np_print('04_RunTrans_INVOKE_DECLINED_FINISHED',';','flag = ', NP020PA.flag)
            return {'CANCELLED'}


# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of RunTranslate operator:

def DRAW_RunTranslate(self, context):

    np_print('04_DRAW_RunTrans_START',';','flag = ', NP020PA.flag)

    addon_prefs = context.user_preferences.addons[__package__].preferences

    flag = NP020PA.flag
    takeloc3d = NP020PA.takeloc3d
    placeloc3d = NP020PA.placeloc3d

    region = context.region
    rv3d = context.region_data

    if flag in ('RUNTRANSZERO', 'RUNTRANSFIRST'):
        takeloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, takeloc3d)
        placeloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, placeloc3d)
    if flag == 'NAVTRANSZERO':
        takeloc2d = self.co2d
        placeloc2d = self.co2d
    if flag == 'NAVTRANSFIRST':
        takeloc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, takeloc3d)
        placeloc2d = self.co2d


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
    dist_num = copy.deepcopy(display_distance_between_two_points(region, rv3d, takeloc3d, placeloc3d)[0])


    if flag in ('RUNTRANSFIRST', 'NAVTRANSFIRST'):
        #ardist_num = NP020PA.ar23d - NP020PA.ar13d
        #ardist_num = ardist_num.length * dist_scale
        ar12d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PA.ar13d)
        ar22d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PA.ar23d)
        NP020PA.deltavec = NP020PA.placeloc3d - NP020PA.takeloc3d
        np_print('DAKLE', NP020PA.ar23d, NP020PA.ar13d, NP020PA.deltavec)
        #ardist_num = abs(round(ardist_num,2))
        #if suffix is not None:
            #ardist = str(dist_num)+suffix
        #else:
            #ardist = str(dist_num)
        #NP020PA.ardist = ardist
        #ardist_loc = (ar12d + ar22d) /2
        #np_print('First Calc - ardist =', ardist, ardist_loc)


    #DRAWING END:
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('04_DRAW_RunTrans_FINISHED',';','flag = ', NP020PA.flag)


# Defining the operator that will enable navigation if user calls it:

class NPPANavTranslate(bpy.types.Operator):
    bl_idname = "object.np_pa_nav_translate"
    bl_label = "NP PA Nav Translate"
    bl_options = {'INTERNAL'}

    np_print('04a_NavTrans_START',';','flag = ', NP020PA.flag)

    def modal(self,context,event):
        context.area.tag_redraw()
        flag = NP020PA.flag
        take = NP020PA.take
        place = NP020PA.place

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            pointloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector * NP020PA.away
            NP020PA.placeloc3d = copy.deepcopy(pointloc)
            np_print('04a_NavTrans_mousemove',';','flag = ', NP020PA.flag)

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector*NP020PA.away
            placeloc3d = NP020PA.placeloc3d
            navdelta = enterloc - NP020PA.awayloc
            take.hide = False
            place.hide = False
            np_print('flag = ', flag)
            if flag == 'NAVTRANSZERO':
                takeloc3d = enterloc
                placeloc3d = enterloc
                take.location = enterloc
                place.location = enterloc
                NP020PA.flag = 'RUNTRANSZERO'
            elif flag == 'NAVTRANSFIRST':
                takeloc3d = NP020PA.takeloc3d
                placeloc3d = enterloc
                place.location = enterloc
                nextob = NP020PA.nextob
                for ob in nextob:
                    ob.hide = False
                place.select = False
                bpy.ops.transform.translate(value = navdelta)
                place.select = True
                NP020PA.flag = 'RUNTRANSFIRST'
            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            NP020PA.take = take
            NP020PA.place = place
            NP020PA.takeloc3d = takeloc3d
            NP020PA.placeloc3d = placeloc3d
            np_print('04a_NavTrans_left_space_FINISHED',';','flag = ', NP020PA.flag)
            return {'FINISHED'}

        elif event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            take.hide = False
            place.hide = False
            if flag == 'NAVTRANSZERO':
                place.select = False
                NP020PA.flag = 'EXIT'
            elif flag == 'NAVTRANSFIRST':
                place.select = False
                prevob = NP020PA.prevob
                nextob = NP020PA.nextob
                for ob in nextob:
                    ob.hide = False
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select = True
                NP020PA.flag = 'ARRAYTRANS'
            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            np_print('04a_NavTrans_rmb_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            take.hide = False
            place.hide = False
            if flag == 'NAVTRANSZERO':
                place.select = False
                NP020PA.flag = 'EXIT'
            elif flag == 'NAVTRANSFIRST':
                place.select = False
                prevob = NP020PA.prevob
                nextob = NP020PA.nextob
                for ob in nextob:
                    ob.hide = False
                bpy.ops.object.delete('EXEC_DEFAULT')
                for ob in prevob:
                    ob.select = True
                NP020PA.flag = 'EXIT'
            else:
                np_print('UNKNOWN FLAG')
                NP020PA.flag = 'EXIT'
            np_print('04a_NavTrans_esc_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('04a_NavTrans_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}

        np_print('04a_NavTrans_INVOKED_RUNNING_MODAL',';','flag = ', NP020PA.flag)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('04a_NavTrans_INVOKE_START')
        flag = NP020PA.flag
        np_print('flag = ', flag)
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag in ('NAVTRANSZERO', 'NAVTRANSFIRST'):
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_RunTranslate, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('04a_run_NAV_INVOKE_a_RUNNING_MODAL',';','flag = ', NP020PA.flag)
            return {'RUNNING_MODAL'}
        else:
            np_print('04a_run_NAV_INVOKE_a_FINISHED',';','flag = ', flag)
            return {'FINISHED'}


# Defining the operator that will enable the return to RunTrans cycle by reseting the 'break' flag:

class NPPAPrepareNext(bpy.types.Operator):
    bl_idname = 'object.np_pa_prepare_next'
    bl_label = 'NP PA Prepare Next'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('05_PrepareNext_START',';','flag = ', NP020PA.flag)
        if NP020PA.flag == 'RUNTRANSFIRST_break':
            NP020PA.flag = 'RUNTRANSFIRST'
        np_print('05_PrepareNext_FINISHED',';','flag = ', NP020PA.flag)
        return{'FINISHED'}


# Defining the operator that will collect the necessary data and the generate the array with an input dialogue for number of items:

class NPPAArrayTranslate(bpy.types.Operator):
    bl_idname = "object.np_pa_array_translate"
    bl_label = "NP PA Array Translate"
    bl_options = {'INTERNAL'}

    np_print('06_ArrayTrans_START',';','flag = ', NP020PA.flag)

    def modal(self,context,event):
        np_print('06_ArrayTrans_START',';','flag = ', NP020PA.flag)
        context.area.tag_redraw()
        flag = NP020PA.flag
        ardict = NP020PA.ardict
        arob = NP020PA.arob
        np_print('ardict = ', ardict)

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            np_print('04a_NavTrans_mousemove',';','flag = ', NP020PA.flag)

        elif event.type in ('LEFTMOUSE', 'RIGHTMOUSE') and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PA.flag = 'EXIT'
            np_print('06_ArrayTrans_rmb_FINISHED',';','flag = ', NP020PA.flag)
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
            NP020PA.fit_type = ar.fit_type
            NP020PA.count = count
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
            NP020PA.fit_type = ar.fit_type
            NP020PA.count = count
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
            NP020PA.flag = 'EXIT'
            np_print('06_ArrayTrans_enter_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.ctrl and event.type == 'TAB' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if NP020PA.fit_type == 'FIXED_COUNT':
                value = NP020PA.ar23d - NP020PA.ar13d
            else:
                value = (NP020PA.ar23d - NP020PA.ar13d)/(NP020PA.count - 1)
            selob = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            for ob in arob:
                ob.select = True
                ob.modifiers.remove(ardict[ob][0])
                np_print('NP020PA.count', NP020PA.count)
                for i in range(1, NP020PA.count):
                    bpy.ops.object.duplicate(linked = True)
                    bpy.ops.transform.translate(value = value)
                bpy.ops.object.select_all(action='DESELECT')
            for ob in selob:
                ob.select = True
            NP020PA.flag = 'EXIT'
            np_print('06_ArrayTrans_ctrl_tab_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type == 'TAB' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if NP020PA.fit_type == 'FIXED_COUNT':
                value = NP020PA.ar23d - NP020PA.ar13d
            else:
                value = (NP020PA.ar23d - NP020PA.ar13d)/(NP020PA.count - 1)
            selob = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')
            for ob in arob:
                ob.select = True
                ob.modifiers.remove(ardict[ob][0])
                np_print('NP020PA.count', NP020PA.count)
                for i in range(1, NP020PA.count):
                    bpy.ops.object.duplicate()
                    bpy.ops.transform.translate(value = value)
                bpy.ops.object.select_all(action='DESELECT')
            for ob in selob:
                ob.select = True
            NP020PA.flag = 'EXIT'
            np_print('06_ArrayTrans_tab_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type == 'ESC' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            for ob in arob:
                ob.modifiers.remove(ardict[ob][0])
            NP020PA.flag = 'EXIT'
            np_print('06_ArrayTrans_esc_FINISHED',';','flag = ', NP020PA.flag)
            return{'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('06_ArrayTrans_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}

        np_print('06_ArrayTrans_INVOKED_RUNNING_MODAL',';','flag = ', NP020PA.flag)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('06_ArrayTrans_INVOKE_START')
        flag = NP020PA.flag
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag == 'ARRAYTRANS':
            arob = NP020PA.arob
            np_print('deltavec_safe = ', NP020PA.deltavec_safe)
            ardict = {}
            for ob in arob:
                deltavec = copy.deepcopy(NP020PA.deltavec_safe)
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
            NP020PA.selob = arob
            NP020PA.ardict = ardict
            NP020PA.count = 5
            NP020PA.fit_type = 'FIXED_COUNT'
            selob = NP020PA.selob
            lenselob = len(selob)
            for i, ob in enumerate(selob):
                ob.select = True
                if i == lenselob-1:
                    bpy.context.scene.objects.active = ob
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_ArrayTranslate, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('06_ArayTrans_INVOKE_a_RUNNING_MODAL',';','flag = ', NP020PA.flag)
            return {'RUNNING_MODAL'}
        else:
            np_print('06_ArrayTrans_INVOKE_DENIED',';','flag = ', NP020PA.flag)
            return {'FINISHED'}


# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of ArrayTranslate operator:

def DRAW_ArrayTranslate(self, context):

    np_print('06a_DRAW_ArrayTrans_START',';','flag = ', NP020PA.flag)

    addon_prefs = context.user_preferences.addons[__package__].preferences



    # MOUSE BADGE:
    '''
    if badge == True:
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        icon = copy.deepcopy(NP020PA.icon)
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
        if NP020PA.fit_type == 'FIT_LENGTH':
            blf.draw(font_id,'/' + str(NP020PA.count))
        else:
            blf.draw(font_id,str(NP020PA.count))
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x,y in icon:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
    '''

    region = context.region
    rv3d = context.region_data
    instruct = 'specify number of items in array'
    keys_aff = 'CTRL+SCROLL, UPARROW / DOWNARROW - number of items, LMB / RMB - confirm and keep array, ENTER - apply as one, TAB - apply as separate, CTRL+TAB - apply as instanced'
    keys_nav = 'MMB, SCROLL - navigate'
    keys_neg = 'ESC - cancel array'

    badge_mode = 'NAV'
    message_main = 'NAVIGATE'
    message_aux = 'CTRL+SCRL'

    if NP020PA.fit_type == 'FIT_LENGTH':
        aux_num = '/' + str(NP020PA.count)
    else:
        aux_num = str(NP020PA.count)
    aux_str = None

    # ON-SCREEN INSTRUCTIONS:

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)



    co2d = self.co2d

    symbol = [[23, 34], [23, 32], [19, 32], [19, 36], [21, 36], [21, 38], [25, 38], [25, 34], [23, 34], [23, 36], [21, 36]]

    display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str)






    ar12d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PA.ar13d)
    ar22d = view3d_utils.location_3d_to_region_2d(region, rv3d, NP020PA.ar23d)

    bgl.glEnable(bgl.GL_BLEND)
    # ARMARKERS:
    font_id = 0
    markersize = 2 * 2.5
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
    display_distance_between_two_points(region, rv3d, NP020PA.ar13d, NP020PA.ar23d)

    #DRAWING END:
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    np_print('06a_DRAW_ArrayTrans_FINISHED',';','flag = ', NP020PA.flag)


# Restoring the object selection and system settings from before the operator activation. Deleting the helpers after successful translation, reseting all viewport options and reselecting previously selected objects:

class NPPARestoreContext(bpy.types.Operator):
    bl_idname = "object.np_pa_restore_context"
    bl_label = "NP PA Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('07_CleanExit_START',';','flag = ', NP020PA.flag)
        flag = NP020PA.flag
        selob = NP020PA.selob
        take = NP020PA.take
        place = NP020PA.place
        bpy.ops.object.select_all(action='DESELECT')
        take.select = True
        place.select = True
        if NP020PA.prevob != None:
            prevob = NP020PA.prevob
            nextob = NP020PA.nextob
            if prevob is not selob:
                for i, ob in enumerate(prevob):
                    ob.select = True
            for i, ob in enumerate(nextob):
                ob.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')
        lenselob = len(selob)
        for i, ob in enumerate(selob):
            ob.select = True
            if i == lenselob-1:
                bpy.context.scene.objects.active = ob
        NP020PA.take = None
        NP020PA.place = None
        NP020PA.takeloc3d = (0.0,0.0,0.0)
        NP020PA.placeloc3d = (0.0,0.0,0.0)
        NP020PA.prevob = None
        NP020PA.nextob = None
        NP020PA.dist = None
        NP020PA.mode = 'MOVE'
        NP020PA.flag = 'NONE'
        NP020PA.ardict = {}
        NP020PA.deltavec = Vector ((0, 0, 0))
        NP020PA.deltavec_safe = Vector ((0, 0, 0))
        bpy.context.tool_settings.use_snap = NP020PA.use_snap
        bpy.context.tool_settings.snap_element = NP020PA.snap_element
        bpy.context.tool_settings.snap_target = NP020PA.snap_target
        bpy.context.space_data.pivot_point = NP020PA.pivot_point
        bpy.context.space_data.transform_orientation = NP020PA.trans_orient
        if NP020PA.acob is not None:
            bpy.context.scene.objects.active = NP020PA.acob
            bpy.ops.object.mode_set(mode = NP020PA.edit_mode)

        np_print('07_CleanExit_FINISHED',';','flag = ', NP020PA.flag)
        return {'FINISHED'}


'''
# Defining the settings of the addon in the User preferences / addons tab:

class NPPAPreferences(bpy.types.AddonPreferences):
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

    #bpy.utils.register_class(NPPAPreferences)
    #bpy.utils.register_module(__name__)
    bpy.app.handlers.scene_update_post.append(NPPA_scene_update)

    NP020PointArray.define('OBJECT_OT_np_pa_get_context')
    NP020PointArray.define('OBJECT_OT_np_pa_get_selection')
    NP020PointArray.define('OBJECT_OT_np_pa_get_mouseloc')
    NP020PointArray.define('OBJECT_OT_np_pa_add_helpers')
    NP020PointArray.define('OBJECT_OT_np_pa_prepare_context')
    for i in range(1, 3):
        for i in range(1, 10):
            NP020PointArray.define('OBJECT_OT_np_pa_run_translate')
            NP020PointArray.define('OBJECT_OT_np_pa_nav_translate')
        NP020PointArray.define('OBJECT_OT_np_pa_prepare_next')
    NP020PointArray.define('OBJECT_OT_np_pa_array_translate')
    NP020PointArray.define('OBJECT_OT_np_pa_restore_context')

def unregister():
    #pass
    #bpy.utils.unregister_class(NPPAPreferences)
    #bpy.utils.unregister_module(__name__)
    bpy.app.handlers.scene_update_post.remove(NPPA_scene_update)
