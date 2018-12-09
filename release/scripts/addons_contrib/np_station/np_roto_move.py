
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


bl_info = {
    'name': 'NP 020 Roto Move',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Rotates selected objects using snap points',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bgl
import blf
import mathutils
from mathutils import *
from math import *
#from math import sin, cos, tan, atan, degrees, radians, asin, acos
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *

# Defining the main class - the macro:

class NP020RotoMove(bpy.types.Macro):
    bl_idname = 'object.np_020_roto_move'
    bl_label = 'NP 020 Roto Move'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020RM:

    flag = 'RUNTRANSCENTER'
    angstep = 10
    radius = 1
    rdelta = 100

# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:
'''
@persistent
def NPRM_scene_update(context):

    if bpy.data.objects.is_updated:
        region = bpy.context.region
        rv3d = bpy.context.region_data
        helper = NP020RM.helper
        co = helper.location
'''
# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPRMGetContext(bpy.types.Operator):
    bl_idname = 'object.np_rm_get_context'
    bl_label = 'NP RM Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.selected_objects == []:
            self.report({'WARNING'}, "Please select objects first")
            return {'CANCELLED'}
        NP020RM.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020RM.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020RM.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020RM.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020RM.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020RM.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020RM.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020RM.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020RM.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020RM.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020RM.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020RM.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020RM.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020RM.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020RM.edit_mode = 'PARTICLE_EDIT'
        return {'FINISHED'}


# Defining the operator for aquiring the list of selected objects and storing them for later re-calls:

class NPRMGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_rm_get_selection'
    bl_label = 'NP RM Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # Reading and storing the selection:
        NP020RM.selob = bpy.context.selected_objects
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and store it as a location for placing the helper object under the mouse:

class NPRMGetMouseloc(bpy.types.Operator):
    bl_idname = 'object.np_rm_get_mouseloc'
    bl_label = 'NP RM Get Mouseloc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector*100
        NP020RM.enterloc = copy.deepcopy(enterloc)
        np_print('02_GetMouseloc_FINISHED', ';', 'NP020RM.flag = ', NP020RM.flag)
        return{'FINISHED'}

    def invoke(self,context,event):
        args = (self, context)
        context.window_manager.modal_handler_add(self)
        np_print('02_GetMouseloc_INVOKED_FINISHED', ';', 'NP020RM.flag = ', NP020RM.flag)
        return {'RUNNING_MODAL'}


# Defining the operator that will generate the helper object at the spot marked by mouse, preparing for translation:

class NPRMAddHelper(bpy.types.Operator):
    bl_idname = 'object.np_rm_add_helper'
    bl_label = 'NP RM Add Helper'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_AddHelper_START', ';', 'NP020RM.flag = ', NP020RM.flag)
        enterloc = NP020RM.enterloc
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        helper = bpy.context.active_object
        helper.name = 'NP_RM_helper'
        NP020RM.helper = helper
        np_print('03_AddHelper_FINISHED', ';', 'NP020RM.flag = ', NP020RM.flag)
        return{'FINISHED'}


# Defining the operator that will change some of the system settings and prepare objects for the operation:

class NPRMPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_rm_prepare_context'
    bl_label = 'NP RM Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selob = NP020RM.selob
        helper = NP020RM.helper
        flag = NP020RM.flag
        if flag == 'RUNROTEND':
            proj_start = NP020RM.proj_start
            ndef = NP020RM.ndef
            helper.location = copy.deepcopy(NP020RM.startloc)
            centerloc = NP020RM.centerloc
            v1 = helper.location
            v2 = helper.location + Vector ((0.0, 0.0, 1.0))
            v3 = helper.location + ndef
            rot_axis = geometry.normal(v1, v2, v3)
            rot_ang = Vector ((0.0, 0.0, 1.0)).angle(ndef)
            np_print('rot_axis, rot_ang =', rot_axis, degrees(rot_ang))
            bpy.ops.object.select_all(action = 'DESELECT')
            helper.select = True
            bpy.ops.transform.rotate(value = rot_ang ,axis = rot_axis)
            bpy.ops.transform.create_orientation(use = True)
            #bpy.ops.transform.rotate(value = -rot_ang ,axis = rot_axis)
            for ob in selob:
                ob.select = True
            bpy.context.scene.objects.active = helper
            bpy.context.tool_settings.use_snap = False
            bpy.context.tool_settings.snap_element = 'VERTEX'
            bpy.context.tool_settings.snap_target = 'ACTIVE'
            bpy.context.space_data.pivot_point = 'CURSOR'
            #bpy.context.space_data.transform_orientation = 'GLOBAL'
            bpy.context.scene.cursor_location = centerloc
        else:
            for ob in selob:
                ob.select = False
            helper.select = True
            bpy.context.scene.objects.active = helper
            bpy.context.tool_settings.use_snap = False
            bpy.context.tool_settings.snap_element = 'VERTEX'
            bpy.context.tool_settings.snap_target = 'ACTIVE'
            bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
            bpy.context.space_data.transform_orientation = 'GLOBAL'
            NP020RM.centerloc = None
            NP020RM.qdef = None
            NP020RM.ndef = Vector((0.0, 0.0, 1.0))
            NP020RM.alpha_0 = 90
            NP020RM.alpha_1 = 90
        return{'FINISHED'}


# Defining the operator that will let the user translate the helper to the desired point. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPRMRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_rm_run_translate'
    bl_label = 'NP RM Run Translate'
    bl_options = {'INTERNAL'}

    if NP020RM.flag == 'RUNTRANSCENTER': np_print('04_RunTrans_START',';','NP020RM.flag = ', NP020RM.flag)
    elif NP020RM.flag == 'RUNTRANSSTART': np_print('06_RunTrans_START',';','NP020RM.flag = ', NP020RM.flag)
    count = 0

    def modal(self, context, event):
        context.area.tag_redraw()
        selob = NP020RM.selob
        helper = NP020RM.helper
        flag = NP020RM.flag
        self.count += 1

        if self.count == 1:
            if flag == 'RUNTRANSCENTER': np_print('04_RunTrans_START',';','NP020RM.flag = ', NP020RM.flag)
            elif flag == 'RUNTRANSSTART': np_print('06_RunTrans_START',';','NP020RM.flag = ', NP020RM.flag)

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            if flag == 'RUNTRANSCENTER': np_print('04_RunTrans_mousemove',';','NP020RM.flag = ', NP020RM.flag)
            elif flag == 'RUNTRANSSTART': np_print('06_RunTrans_mousemove',';','NP020RM.flag = ', NP020RM.flag)

        elif event.type in ('LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            if flag == 'RUNTRANSCENTER':
                NP020RM.centerloc = copy.deepcopy(helper.location)
                helper.hide = True
                NP020RM.flag = 'BGLPLANE'
            elif flag == 'RUNTRANSSTART':
                NP020RM.startloc = copy.deepcopy(helper.location)
                NP020RM.alpha_0_def = copy.deepcopy(NP020RM.alpha_0)
                NP020RM.flag = 'RUNROTEND'
            np_print('04_RunTrans_left_enter_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020RM.flag = 'EXIT'
            np_print('04_RunTrans_esc_right_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return{'FINISHED'}

        np_print('04_RunTrans_count_PASS_THROUGH',';','NP020RM.flag = ', NP020RM.flag)
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('04_RunTrans_INVOKE_START')
        helper = NP020RM.helper
        flag = NP020RM.flag
        selob = NP020RM.selob

        if context.area.type == 'VIEW_3D':
            if flag in ('RUNTRANSCENTER', 'RUNTRANSSTART'):
                self.co2d = ((event.mouse_region_x, event.mouse_region_y))
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_Overlay, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                bpy.ops.transform.translate('INVOKE_DEFAULT')
                np_print('04_RunTrans_INVOKED_RUNNING_MODAL',';','NP020RM.flag = ', NP020RM.flag)
                return {'RUNNING_MODAL'}
            else:
                np_print('04_RunTrans_INVOKE_DECLINED_wrong_flag_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            NP020RM.flag = 'EXIT'
            np_print('04_RunTrans_INVOKE_DECLINED_no_VIEW_3D_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return {'FINISHED'}


# Defining the operator that will ineract with user and let him choose the plane of rotation:

class NPRMBglPlane(bpy.types.Operator):
    bl_idname = "object.np_rm_bgl_plane"
    bl_label = "NP RM Bgl Plane"
    bl_options = {'INTERNAL'}

    np_print('05_BglPlane_START',';','NP020RM.flag = ', NP020RM.flag)

    def modal(self,context,event):
        np_print('05_BglPlane_START',';','NP020RM.flag = ', NP020RM.flag)
        context.area.tag_redraw()
        flag = NP020RM.flag
        mode = NP020RM.mode
        plane = NP020RM.plane
        helper = NP020RM.helper
        centerloc = NP020RM.centerloc

        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            np_print('05_BglPlane_mousemove',';','NP020RM.flag = ', NP020RM.flag, 'NP020RM.mode = ', NP020RM.mode, 'NP020RM.plane = ', NP020RM.plane)

        elif event.type in ('LEFTMOUSE', 'RIGHTMOUSE', 'RET', 'NUMPAD_ENTER'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            region = context.region
            rv3d = context.region_data
            co2d = self.co2d
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
            viewloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d)
            away = (centerloc - viewloc).length
            pointloc = viewloc + view_vector * away # to place the helper on centerloc to be in the vicinity of projection plane
            helper.location = pointloc
            helper.hide = False
            NP020RM.qdef = copy.deepcopy(NP020RM.q)
            NP020RM.ndef = copy.deepcopy(NP020RM.n)
            NP020RM.plane = 'SET'
            NP020RM.flag = 'RUNTRANSSTART'
            np_print('05_BglPlane_lmb_FINISHED',';','NP020RM.flag = ', NP020RM.flag, 'NP020RM.mode = ', NP020RM.mode, 'NP020RM.plane = ', NP020RM.plane)
            return{'FINISHED'}

        elif event.ctrl and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if mode == 'FREE':
                NP020RM.mode = 'X'
            elif mode == 'X':
                NP020RM.mode = 'Y'
            elif mode == 'Y':
                NP020RM.mode = 'Z'
            else:
                NP020RM.mode = 'FREE'
            np_print('05_BglPlane_rmb_FINISHED',';','NP020RM.flag = ', NP020RM.flag, 'NP020RM.mode = ', NP020RM.mode, 'NP020RM.plane = ', NP020RM.plane)

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020RM.flag = 'EXIT'
            np_print('05_BglPlane_esc_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return{'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            np_print('05_BglPlane_middle_wheel_any_PASS_THROUGH')
            return {'PASS_THROUGH'}

        np_print('05_BglPlane_standard_RUNNING_MODAL',';','NP020RM.flag = ', NP020RM.flag)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        np_print('05_BglPlane_INVOKE_START')
        flag = NP020RM.flag
        NP020RM.plane = 'CHOOSE'
        NP020RM.mode = 'FREE'
        self.co2d = ((event.mouse_region_x, event.mouse_region_y))
        if flag == 'BGLPLANE':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_Overlay, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            np_print('05_BglPlane_INVOKED_RUNNING_MODAL',';','NP020RM.flag = ', NP020RM.flag)
            return {'RUNNING_MODAL'}
        else:
            np_print('05_BglPlane_INVOKE_DECLINED_wrong_flag_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return {'FINISHED'}


# Defining the operator that will let the user rotate the selection with the helper to the desired point. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPRMRunRotate(bpy.types.Operator):
    bl_idname = 'object.np_rm_run_rotate'
    bl_label = 'NP RM Run Rotate'
    bl_options = {'INTERNAL'}


    np_print('07_RunRotate_START',';','NP020RM.flag = ', NP020RM.flag)


    def modal(self, context, event):
        context.area.tag_redraw()
        selob = NP020RM.selob
        helper = NP020RM.helper
        flag = NP020RM.flag


        if event.type == 'MOUSEMOVE':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            if flag == 'RUNTRANSCENTER': np_print('04_RunTrans_mousemove',';','NP020RM.flag = ', NP020RM.flag)
            elif flag == 'RUNTRANSSTART': np_print('06_RunTrans_mousemove',';','NP020RM.flag = ', NP020RM.flag)

        elif event.type in ('LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            NP020RM.flag = 'EXIT'
            bpy.ops.transform.delete_orientation()
            np_print('04_RunTrans_left_enter_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return{'FINISHED'}

        elif event.type in ('ESC', 'RIGHTMOUSE'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.transform.delete_orientation()
            NP020RM.flag = 'EXIT'
            np_print('04_RunTrans_esc_right_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return{'FINISHED'}

        np_print('04_RunTrans_count_PASS_THROUGH',';','NP020RM.flag = ', NP020RM.flag)
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('07_RunRotate_INVOKE_START')
        helper = NP020RM.helper
        flag = NP020RM.flag
        selob = NP020RM.selob
        ndef = NP020RM.ndef


        if context.area.type == 'VIEW_3D':
            if flag == 'RUNROTEND':
                self.co2d = ((event.mouse_region_x, event.mouse_region_y))
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_Overlay, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                NP020RM.rot_helper_0 = copy.deepcopy(helper.rotation_euler)
                bpy.ops.transform.rotate('INVOKE_DEFAULT', constraint_axis=(False, False, True))

                np_print('04_RunTrans_INVOKED_RUNNING_MODAL',';','NP020RM.flag = ', NP020RM.flag)
                return {'RUNNING_MODAL'}
            else:
                np_print('04_RunTrans_INVOKE_DECLINED_wrong_flag_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            NP020RM.flag = 'EXIT'
            np_print('04_RunTrans_INVOKE_DECLINED_no_VIEW_3D_FINISHED',';','NP020RM.flag = ', NP020RM.flag)
            return {'FINISHED'}

# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of RunTranslate operator:

def DRAW_Overlay(self, context):

    np_print('DRAW_Overlay_START',';','NP020RM.flag = ', NP020RM.flag)

    flag = NP020RM.flag
    helper = NP020RM.helper
    angstep = NP020RM.angstep
    region = bpy.context.region
    rv3d = bpy.context.region_data
    rw = region.width
    rh = region.height
    if NP020RM.centerloc == None: centerloc = helper.location
    else: centerloc = NP020RM.centerloc
    qdef = NP020RM.qdef
    ndef = NP020RM.ndef
    alpha_0 = NP020RM.alpha_0
    alpha_1 = NP020RM.alpha_1
    np_print('rw, rh', rw, rh)
    rmin = int(min(rw, rh) / 10)
    if rmin == 0: rmin = 1
    co2d = self.co2d
    if flag in ('RUNTRANSCENTER', 'RUNTRANSSTART'): co2d = view3d_utils.location_3d_to_region_2d(region, rv3d, helper.location)
    if qdef == None:
        q = get_ro_normal_from_vertical(region, rv3d, co2d)[1]
        n = get_ro_normal_from_vertical(region, rv3d, co2d)[0]
    else:
        q = qdef
        n = ndef
    NP020RM.q = q
    NP020RM.n = n
    #co2d_exp = (event.mouse_region_x, event.mouse_region_y)
    #n_exp = get_ro_normal_from_vertical(region, rv3d, co2d_exp)[0]
    #np_print('co2d, n, q, n_exp', co2d, n, q)

    # writing the dots for circle at center of scene:
    radius = 1
    ang = 0.0
    circle = [(0.0 ,0.0 ,0.0)]
    while ang < 360.0:
        circle.append(((cos(radians(ang)) * radius), (sin(radians(ang)) * radius), (0.0)))
        ang += 10
    circle.append(((cos(radians(0.0)) * radius), (sin(radians(0.0)) * radius), (0.0)))

    # rotating and translating the circle to user picked angle and place:
    circle = rotate_graphic(circle, q)
    circle = translate_graphic(circle, centerloc)

    rmax = 1
    for i, co in enumerate(circle):
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        circle[i] = co
    for i in range(1, 18):
        r = (circle[0] - circle[i]).length
        r1 = (circle[0] - circle[i + 18]).length
        #if (r + r1) > rmax and abs(r - r1) < min(r, r1)/5: rmax = (r+r1)/2
        #if (r + r1) > rmax and abs(r - r1) < min(r, r1)/10: rmax = r + r1
        if (r + r1) > rmax and (r + r1) / 2 < rmin: rmax = (r + r1)
        elif (r + r1) > rmax and (r + r1) / 2 >= rmin: rmax = (r + r1) * rmin / (((r + r1) / 2)- ((r + r1) / 2) - rmin)
        rmax = abs(rmax)
        circle[i] = co
    np_print('rmin', rmin)
    np_print('rmax', rmax)
    if flag not in ('RUNTRANSSTART', 'RUNROTEND'):
        fac = (rmin * 2) / rmax
        NP020RM.fac = fac
    else: fac = NP020RM.fac

    radius = 1 * fac
    ang = 0.0
    circle = [(0.0 ,0.0 ,0.0)]
    while ang < 360.0:
        circle.append(((cos(radians(ang)) * radius), (sin(radians(ang)) * radius), (0.0)))
        ang += 10
    circle.append(((cos(radians(0.0)) * radius), (sin(radians(0.0)) * radius), (0.0)))


    if flag == 'RUNTRANSCENTER':
        instruct = 'place center point'
        keys_aff = 'LMB / ENT / NUMPAD ENT - confirm, CTRL - snap'
        keys_nav = ''
        keys_neg = 'ESC - quit'

        r1 = 1
        r2 = 1.5
        walpha = construct_roto_widget(alpha_0, alpha_1, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_L = construct_roto_widget(90, 0, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_D = construct_roto_widget(0, 90, fac, r1, r2, angstep)

    elif flag == 'BGLPLANE':
        instruct = 'choose rotation plane'
        keys_aff = 'LMB / ENT / NUMPAD ENT - confirm'
        keys_nav = 'MMB / SCROLL - navigate'
        keys_neg = 'ESC - quit'

        ro_hor, isohipse = get_ro_x_from_iso(region, rv3d, co2d, centerloc)
        NP020RM.ro_hor = copy.deepcopy(ro_hor)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
        bgl.glLineWidth(2)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for co in isohipse:
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
        bgl.glEnd()

        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glPointSize(4)
        bgl.glBegin(bgl.GL_POINTS)
        for co in isohipse:
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
        bgl.glEnd()

        r1 = 1
        r2 = 1.5
        walpha = construct_roto_widget(alpha_0, alpha_1, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_L = construct_roto_widget(90, 0, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_D = construct_roto_widget(0, 90, fac, r1, r2, angstep)

        circle = rotate_graphic(circle, ro_hor)
        walpha = rotate_graphic(walpha, ro_hor)
        wbeta_L = rotate_graphic(wbeta_L, ro_hor)
        wbeta_D = rotate_graphic(wbeta_D, ro_hor)

        circle = rotate_graphic(circle, q)
        walpha = rotate_graphic(walpha, q)
        wbeta_L = rotate_graphic(wbeta_L, q)
        wbeta_D = rotate_graphic(wbeta_D, q)


    elif flag == 'RUNTRANSSTART':
        instruct = 'place start point'
        keys_aff = 'LMB / ENT / NUMPAD ENT - confirm, CTRL - snap'
        keys_nav = ''
        keys_neg = 'ESC - quit'

        hloc = helper.location
        #np_print('hloc', hloc)
        hlocb = hloc + n
        #np_print('hlocb', hlocb)
        #np_print('centerloc, n', centerloc, n)
        proj_start = mathutils.geometry.intersect_line_plane(helper.location, (helper.location + n), centerloc, n)
        NP020RM.proj_start = proj_start
        if proj_start == centerloc: proj = centerloc + Vector((0.0, 0.0, 0.001))
        #np_print('proj_start' , proj_start)

        alpha_0, isohipse = get_angle_from_iso_planar(centerloc, n, proj_start)
        alpha_1 = alpha_0
        NP020RM.alpha_0 = alpha_0
        NP020RM.alpha_1 = alpha_1
        np_print('alpha_0', alpha_0)

        ro_hor = NP020RM.ro_hor

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
        bgl.glLineWidth(2)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for co in isohipse:
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
        bgl.glEnd()

        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glPointSize(4)
        bgl.glBegin(bgl.GL_POINTS)
        for co in isohipse:
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
        bgl.glEnd()

        r1 = 1
        r2 = 1.5
        walpha = construct_roto_widget(alpha_0, alpha_1, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_L = construct_roto_widget(alpha_1, 0, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_D = construct_roto_widget(0, alpha_0, fac, r1, r2, angstep)


        circle = rotate_graphic(circle, ro_hor)
        walpha = rotate_graphic(walpha, ro_hor)
        wbeta_L = rotate_graphic(wbeta_L, ro_hor)
        wbeta_D = rotate_graphic(wbeta_D, ro_hor)

        circle = rotate_graphic(circle, q)
        walpha = rotate_graphic(walpha, q)
        wbeta_L = rotate_graphic(wbeta_L, q)
        wbeta_D = rotate_graphic(wbeta_D, q)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(0.5, 0.5, 1.0, 1.0)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        points = (helper.location, proj_start, centerloc)
        for co in points:
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
        bgl.glEnd()

        co = view3d_utils.location_3d_to_region_2d(region, rv3d, proj_start)
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glPointSize(14)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*co)
        bgl.glEnd()


    elif flag == 'RUNROTEND':
        instruct = 'place end point'
        keys_aff = 'LMB / ENT / NUMPAD ENT - confirm, CTRL - snap'
        keys_nav = ''
        keys_neg = 'ESC - quit'
        for k, v in bpy.context.active_operator.properties.items():
            np_print(k, v)
        alpha_0 = NP020RM.alpha_0_def
        hloc = helper.location
        startloc = NP020RM.startloc
        endloc = helper.location
        proj_start = NP020RM.proj_start
        #np_print('hloc', hloc)
        hlocb = hloc + n
        #np_print('hlocb', hlocb)
        #np_print('centerloc, n', centerloc, n)
        proj_end = mathutils.geometry.intersect_line_plane(helper.location, (helper.location + n), centerloc, n)
        if proj_end == centerloc: proj_end = centerloc + Vector((0.0, 0.0, 0.001))
        #np_print('proj_end' , proj_end)

        alpha = get_angle_vector_from_vector(centerloc, proj_start, proj_end)
        alpha_1 = alpha_0 + alpha
        np_print('alpha_0', alpha_0)

        ro_hor = NP020RM.ro_hor

        rot_helper_0 = NP020RM.rot_helper_0
        np_print('rot_helper_0 =', rot_helper_0)
        rot_helper_1 = helper.rotation_euler
        np_print('rot_helper_1 =', rot_helper_1)
        alpha_real = get_eul_z_angle_diffffff_in_rotated_system(rot_helper_0, rot_helper_1, ndef)
        np_print('alpha_real =', alpha_real)


        delta = (abs(alpha_real) - (360 * int(abs(alpha_real) / 360 )))
        if alpha_real >= 0:
            if alpha_0 + delta < 360: alpha_1 = alpha_0 + delta
            else: alpha_1 = delta - (360 - alpha_0)
        else:
            if delta < alpha_0:
                alpha_1 = alpha_0
                alpha_0 = alpha_1 - delta
            else:
                alpha_1 = alpha_0
                alpha_0 = 360 - (delta - alpha_0)

        if alpha_1 == alpha_0: alpha_1 = alpha_0 + 0.001
        r1 = 1
        r2 = 1.5
        walpha = construct_roto_widget(alpha_0, alpha_1, fac, r1, r2, angstep)

        r1 = 1.5
        r2 = 2
        wbeta_L = construct_roto_widget(alpha_1, alpha_0, fac, r1, r2, angstep)
        '''
        r1 = 1.5
        r2 = 2
        wbeta_D = construct_roto_widget(0, alpha_0, fac, r1, r2, angstep)
        '''

        circle = rotate_graphic(circle, ro_hor)
        walpha = rotate_graphic(walpha, ro_hor)
        wbeta_L = rotate_graphic(wbeta_L, ro_hor)
        #wbeta_D = rotate_graphic(wbeta_D, ro_hor)

        circle = rotate_graphic(circle, q)
        walpha = rotate_graphic(walpha, q)
        wbeta_L = rotate_graphic(wbeta_L, q)
        #wbeta_D = rotate_graphic(wbeta_D, q)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(0.5, 0.5, 1.0, 1.0)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        points = (helper.location, proj_end, centerloc, proj_start)
        for co in points:
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
        bgl.glEnd()

        co = view3d_utils.location_3d_to_region_2d(region, rv3d, proj_end)
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glPointSize(14)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*co)
        bgl.glEnd()





        # NUMERICAL ANGLE:

        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        font_id = 0
        blf.size(font_id, 20, 72)
        ang_pos = view3d_utils.location_3d_to_region_2d(region, rv3d, centerloc)
        blf.position(font_id, ang_pos[0]+2, ang_pos[1]-2, 0)
        blf.draw(font_id, str(round(alpha_real,2)))
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, ang_pos[0], ang_pos[1], 0)
        blf.draw(font_id, str(round(alpha_real,2)))




    # DRAWING START:
    bgl.glEnable(bgl.GL_BLEND)


    # ON-SCREEN INSTRUCTIONS:

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    np_print('centerloc', centerloc)
    circle = translate_graphic(circle, centerloc)

    walpha = translate_graphic(walpha, centerloc)
    wbeta_L = translate_graphic(wbeta_L, centerloc)
    if flag is not 'RUNROTEND': wbeta_D = translate_graphic(wbeta_D, centerloc)


    np_print('rv3d', rv3d)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.6)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i, co in enumerate(circle):
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        bgl.glVertex2f(*co)
        circle[i] = co
    bgl.glEnd()
    np_print('centerloc', centerloc)


    # drawing of walpha contours:
    bgl.glColor4f(1.0, 1.0, 1.0, 0.6)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i, co in enumerate(walpha):
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        bgl.glVertex2f(*co)
        walpha[i] = co
    bgl.glEnd()
    #np_print('walpha', walpha)
    bgl.glColor4f(0.0, 0.0, 0.0, 0.5)

    # drawing of walpha fields:
    np_print('alpha_0, alpha_1 =', alpha_0, alpha_1)
    if alpha_1 >= alpha_0: alpha = alpha_1 - alpha_0
    else: alpha = alpha_1 + (360 - alpha_0)
    sides = int(alpha / NP020RM.angstep) + 1
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2f(*walpha[0])
    bgl.glVertex2f(*walpha[1])
    bgl.glVertex2f(*walpha[2])
    bgl.glVertex2f(*walpha[(sides * 2) + 1])
    bgl.glEnd()
    for i in range(1, sides):
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        bgl.glVertex2f(*walpha[((sides * 2) + 2) - i])
        bgl.glVertex2f(*walpha[i + 1])
        bgl.glVertex2f(*walpha[2 + i])
        bgl.glVertex2f(*walpha[((sides * 2) + 2) - (i + 1)])
        bgl.glEnd()

    # drawing of wbeta_L contours:
    bgl.glColor4f(1.0, 1.0, 1.0, 0.6)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i, co in enumerate(wbeta_L):
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        bgl.glVertex2f(*co)
        wbeta_L[i] = co
    bgl.glEnd()
    #np_print('wbeta_L', wbeta_L)
    bgl.glColor4f(0.65, 0.85, 1.0, 0.35)

    # drawing of wbeta_L fields:
    if flag == 'RUNROTEND':
        if alpha_0 >= alpha_1: alpha = alpha_0 - alpha_1
        else: alpha = alpha_0 + (360 - alpha_1)
    else: alpha = 360 - alpha_1
    sides = int(alpha / NP020RM.angstep) + 1
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2f(*wbeta_L[0])
    bgl.glVertex2f(*wbeta_L[1])
    bgl.glVertex2f(*wbeta_L[2])
    bgl.glVertex2f(*wbeta_L[(sides * 2) + 1])
    bgl.glEnd()
    for i in range(1, sides):
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        bgl.glVertex2f(*wbeta_L[((sides * 2) + 2) - i])
        bgl.glVertex2f(*wbeta_L[i + 1])
        bgl.glVertex2f(*wbeta_L[2 + i])
        bgl.glVertex2f(*wbeta_L[((sides * 2) + 2) - (i + 1)])
        bgl.glEnd()


    if flag is not 'RUNROTEND':
        # drawing of wbeta_D contours:
        bgl.glColor4f(1.0, 1.0, 1.0, 0.6)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for i, co in enumerate(wbeta_D):
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
            wbeta_D[i] = co
        bgl.glEnd()
        #np_print('wbeta_D', wbeta_D)
        bgl.glColor4f(0.35, 0.6, 0.75, 0.35)

        # drawing of wbeta_D fields:

        alpha = alpha_0
        sides = int(alpha / NP020RM.angstep) + 1
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        bgl.glVertex2f(*wbeta_D[0])
        bgl.glVertex2f(*wbeta_D[1])
        bgl.glVertex2f(*wbeta_D[2])
        bgl.glVertex2f(*wbeta_D[(sides * 2) + 1])
        bgl.glEnd()
        for i in range(1, sides):
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            bgl.glVertex2f(*wbeta_D[((sides * 2) + 2) - i])
            bgl.glVertex2f(*wbeta_D[i + 1])
            bgl.glVertex2f(*wbeta_D[2 + i])
            bgl.glVertex2f(*wbeta_D[((sides * 2) + 2) - (i + 1)])
            bgl.glEnd()

    #ENDING

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# Restoring the object selection and system settings from before the operator activation:

class NPRMRestoreContext(bpy.types.Operator):
    bl_idname = "object.np_rm_restore_context"
    bl_label = "NP RM Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selob = NP020RM.selob
        helper = NP020RM.helper
        helper.hide = False
        bpy.ops.object.select_all(action = 'DESELECT')
        helper.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')
        for ob in selob:
            ob.select = True

        bpy.context.tool_settings.use_snap = NP020RM.use_snap
        bpy.context.tool_settings.snap_element = NP020RM.snap_element
        bpy.context.tool_settings.snap_target = NP020RM.snap_target
        bpy.context.space_data.pivot_point = NP020RM.pivot_point
        bpy.context.space_data.transform_orientation = NP020RM.trans_orient
        bpy.context.scene.cursor_location = NP020RM.curloc
        if NP020RM.acob is not None:
            bpy.context.scene.objects.active = NP020RM.acob
            bpy.ops.object.mode_set(mode = NP020RM.edit_mode)
        NP020RM.flag = 'RUNTRANSCENTER'
        return {'FINISHED'}


# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    #bpy.app.handlers.scene_update_post.append(NPRM_scene_update)

    NP020RotoMove.define('OBJECT_OT_np_rm_get_context')
    NP020RotoMove.define('OBJECT_OT_np_rm_get_selection')
    NP020RotoMove.define('OBJECT_OT_np_rm_get_mouseloc')
    NP020RotoMove.define('OBJECT_OT_np_rm_add_helper')
    NP020RotoMove.define('OBJECT_OT_np_rm_prepare_context')
    NP020RotoMove.define('OBJECT_OT_np_rm_run_translate')
    NP020RotoMove.define('OBJECT_OT_np_rm_bgl_plane')
    NP020RotoMove.define('OBJECT_OT_np_rm_run_translate')
    NP020RotoMove.define('OBJECT_OT_np_rm_prepare_context')
    NP020RotoMove.define('OBJECT_OT_np_rm_run_rotate')
    NP020RotoMove.define('OBJECT_OT_np_rm_restore_context')

def unregister():
    #bpy.app.handlers.scene_update_post.remove(NPRM_scene_update)
    pass
