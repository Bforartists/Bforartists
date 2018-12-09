
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

Translates objects using anchor and target points.

Emulates the functionality of the standard 'move' command in CAD applications, with start and end points. This way, it does pretty much what the basic 'grab' function does, only it locks the snap ability to one designated point in selected group, giving more control and precision to the user.

INSTALATION

Two ways:

A. Paste the the .py file to text editor and run (ALT+P)
B. Unzip and place .py file to addons_contrib. In User Preferences / Addons tab search under Testing / NP Anchor Translate and check the box.

Now you have the operator in your system. If you press Save User Preferences, you will have it at your disposal every time you run Bl.

SHORTCUTS

After succesful instalation of the addon, or it's activation from the text editor, the NP Point Move operator should be registered in your system. Enter User Preferences / Input, and under that, 3DView / Object Mode. Search for definition assigned to simple M key (provided that you don't use it for placing objects into layers, instead of now almost-standard 'Layer manager' addon) and instead object.move_to_layer, type object.np_xxx_point_move (xxx being the number of the version). I suggest asigning hotkey only for the Object Mode because the addon doesn't work in other modes. Also, this way the basic G command should still be available and at your disposal.

USAGE

Select one or more objects.
Run operator (spacebar search - NP Anchor Translate, or keystroke if you assigned it)
Select a point anywhere in the scene (holding CTRL enables snapping). This will be your anchor point.
Place objects anywhere in the scene, in relation to the anchor point (again CTRL - snap).
Middle mouse button (MMB) enables axis constraint, numpad keys enable numerical input of distance, and RMB and ESC key interrupt the operation.

IMPORTANT PERFORMANCE NOTES

Should be key-mapped only for Object Mode. Other modes are not supported and key definitions should not be replaced.

WISH LIST

Bgl overlay for snapping modes and eventualy the translate path
Blf instructions on screen, preferably interactive
Smarter code and faster performance

WARNINGS

None so far
'''

bl_info = {
    'name': 'NP 020 Point Move',
    'author': 'Okavango & the Blenderartists community. Special thanks to CoDEmanX, lukas_t, matali',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Moves selected objects using "take" and "place" snap points',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bgl
import blf
import mathutils
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *


# Defining the main class - the macro:

class NP020PointMove(bpy.types.Macro):
    bl_idname = 'object.np_020_point_move'
    bl_label = 'NP 020 Point Move'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020PM:

    flag = 'TAKE'


# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:

@persistent
def NPPM_scene_update(context):

    if bpy.data.objects.is_updated:
        a = 1


# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPPMGetContext(bpy.types.Operator):
    bl_idname = 'object.np_pm_get_context'
    bl_label = 'NP PM Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.selected_objects == []:
            self.report({'WARNING'}, "Please select objects first")
            return {'CANCELLED'}
        NP020PM.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020PM.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020PM.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020PM.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020PM.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020PM.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020PM.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020PM.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020PM.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020PM.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020PM.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020PM.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020PM.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020PM.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020PM.edit_mode = 'PARTICLE_EDIT'
        return {'FINISHED'}


# Defining the operator for aquiring the list of selected objects and storing them for later re-calls:

class NPPMGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_pm_get_selection'
    bl_label = 'NP PM Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # Reading and storing the selection:
        NP020PM.selob = bpy.context.selected_objects
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and store it as a location for placing the helper object under the mouse:

class NPPMGetMouseloc(bpy.types.Operator):
    bl_idname = 'object.np_pm_get_mouseloc'
    bl_label = 'NP PM Get Mouseloc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector/5
        NP020PM.enterloc = copy.deepcopy(enterloc)
        # np_print('02_RadMouseloc_FINISHED', ';', 'flag = ', Storage.flag)
        return{'FINISHED'}

    def invoke(self,context,event):
        args = (self, context)
        context.window_manager.modal_handler_add(self)
        # np_print('02_ReadMouseloc_INVOKED_FINISHED', ';', 'flag = ', NP020PM.flag)
        return {'RUNNING_MODAL'}


# Defining the operator that will generate the helper object at the spot marked by mouse, preparing for translation:

class NPPMAddHelper(bpy.types.Operator):
    bl_idname = 'object.np_pm_add_helper'
    bl_label = 'NP PM Add Helper'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # np_print('03_AddHelpers_START', ';', 'flag = ', NP020PM.flag)
        enterloc = NP020PM.enterloc
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        helper = bpy.context.active_object
        helper.name = 'NP_PM_helper'
        NP020PM.helper = helper
        # np_print('03_AddHelpers_FINISHED', ';', 'flag = ', NP020PM.flag)
        return{'FINISHED'}


# Defining the operator that will change some of the system settings and prepare objects for the operation:

class NPPMPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_pm_prepare_context'
    bl_label = 'NP PM Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selob = NP020PM.selob
        helper = NP020PM.helper
        for ob in selob:
            ob.select = False
        helper.select = True
        bpy.context.scene.objects.active = helper
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = 'VERTEX'
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'
        return{'FINISHED'}


# Defining the operator that will let the user translate the helper to the desired point. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPPMRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_pm_run_translate'
    bl_label = 'NP PM Run Translate'
    bl_options = {'INTERNAL'}

    count = 0

    def modal(self, context, event):
        context.area.tag_redraw()
        flag = NP020PM.flag
        selob = NP020PM.selob
        helper = NP020PM.helper


        if event.type in ('LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'TAKE':
                NP020PM.takeloc = copy.deepcopy(helper.location)
                NP020PM.flag = 'PLACE'
            elif flag == 'PLACE':
                NP020PM.flag = 'EXIT'
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PM.flag = 'EXIT'
            return{'FINISHED'}

        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        # np_print('04_RunTrans_INVOKE_START')
        helper = NP020PM.helper
        flag = NP020PM.flag
        selob = NP020PM.selob
        # np_print('flag =', flag)
        if context.area.type == 'VIEW_3D':
            if flag == 'EXIT':
                # np_print('04_RunTrans_INVOKE_DECLINED_FINISHED',';','flag = ', flag)
                return {'FINISHED'}
            elif flag == 'PLACE':
                for ob in selob:
                    ob.select = True
                bpy.context.scene.objects.active = helper
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_RunTranslate, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            # np_print('04_RunTrans_INVOKED_RUNNING_MODAL',';','flag = ', Storage.flag)
            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            # np_print('04_RunTrans_INVOKE_DECLINED_FINISHED',';','flag = ', Storage.flag)
            return {'FINISHED'}


# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of RunTranslate operator:

def DRAW_RunTranslate(self, context):

    # np_print('04_DRAW_RunTranslate_START',';','flag = ', Storage.flag)
    flag = NP020PM.flag
    sel = bpy.context.selected_objects
    lensel = len(sel)
    helper = NP020PM.helper





    if flag == 'TAKE':
        takeloc = helper.location
        placeloc = helper.location
        main = 'select "take" point'
        keys_aff = 'LMB - select, CTRL - snap'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'

        badge_mode = 'RUN'
        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'PLACE':
        takeloc = NP020PM.takeloc
        placeloc = helper.location
        main = 'select "place" point'
        keys_aff = 'LMB - select, CTRL - snap, MMB - lock axis, NUMPAD - value'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'

        badge_mode = 'RUN'
        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None


    # ON-SCREEN INSTRUCTIONS:

    region = bpy.context.region
    rv3d = bpy.context.region_data
    instruct = main

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)

    co2d = view3d_utils.location_3d_to_region_2d(region, rv3d, helper.location)

    symbol = [[19, 34], [18, 35], [19, 36], [18, 35],
        [26, 35], [25, 34], [26, 35], [25, 37],
        [26, 35], [22, 35], [22, 39], [21, 38],
        [22, 39], [23, 38], [22, 39], [22, 31],
        [21, 32], [22, 31], [23, 32]]

    display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str)

    display_line_between_two_points(region, rv3d, takeloc, placeloc)

    display_distance_between_two_points(region, rv3d, takeloc, placeloc)

# Restoring the object selection and system settings from before the operator activation:

class NPPMRestoreContext(bpy.types.Operator):
    bl_idname = "object.np_pm_restore_context"
    bl_label = "NP PM Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selob = NP020PM.selob
        helper = NP020PM.helper
        bpy.ops.object.select_all(action = 'DESELECT')
        helper.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')
        for ob in selob:
            ob.select = True
            bpy.context.scene.objects.active = ob
        bpy.context.tool_settings.use_snap = NP020PM.use_snap
        bpy.context.tool_settings.snap_element = NP020PM.snap_element
        bpy.context.tool_settings.snap_target = NP020PM.snap_target
        bpy.context.space_data.pivot_point = NP020PM.pivot_point
        bpy.context.space_data.transform_orientation = NP020PM.trans_orient
        if NP020PM.acob is not None:
            bpy.context.scene.objects.active = NP020PM.acob
            bpy.ops.object.mode_set(mode = NP020PM.edit_mode)
        NP020PM.flag = 'TAKE'
        return {'FINISHED'}


# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    NP020PointMove.define('OBJECT_OT_np_pm_get_context')
    NP020PointMove.define('OBJECT_OT_np_pm_get_selection')
    NP020PointMove.define('OBJECT_OT_np_pm_get_mouseloc')
    NP020PointMove.define('OBJECT_OT_np_pm_add_helper')
    NP020PointMove.define('OBJECT_OT_np_pm_prepare_context')
    for i in range(1, 3):
        NP020PointMove.define('OBJECT_OT_np_pm_run_translate')
    NP020PointMove.define('OBJECT_OT_np_pm_restore_context')

def unregister():
    pass
