
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

Emulates the functionality of the standard 'box' command in CAD applications, with start and end points. This way, it does pretty much what the basic 'grab' function does, only it locks the snap ability to one designated point in selected group, giving more control and precision to the user.

INSTALATION

Two ways:

A. Paste the the .py file to text editor and run (ALT+P)
B. Unzip and place .py file to addons_contrib. In User Preferences / Addons tab search under Testing / NP Anchor Translate and check the box.

Now you have the operator in your system. If you press Save User Preferences, you will have it at your disposal every time you run Bl.

SHORTCUTS

After succesful instalation of the addon, or it's activation from the text editor, the NP Float Box operator should be registered in your system. Enter User Preferences / Input, and under that, 3DView / Object Mode. Search for definition assigned to simple M key (provided that you don't use it for placing objects into layers, instead of now almost-standard 'Layer manager' addon) and instead object.move_to_layer, type object.np_xxx_float_box (xxx being the number of the version). I suggest asigning hotkey only for the Object Mode because the addon doesn't work in other modes. Also, this way the basic G command should still be available and at your disposal.

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
    'name': 'NP 020 Float Box',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Draws a mesh box using snap points',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bgl
import blf
import bmesh
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

class NP020FloatBox(bpy.types.Macro):
    bl_idname = 'object.np_020_float_box'
    bl_label = 'NP 020 Float Box'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020FB:

    flag = 'RUNTRANS0'
    boxob = None

# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:
'''
@persistent
def NPFB_scene_update(context):

    if bpy.data.objects.is_updated:
        region = bpy.context.region
        rv3d = bpy.context.region_data
        helper = NP020FB.helper
        co = helper.location
'''

# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPFBGetContext(bpy.types.Operator):
    bl_idname = 'object.np_fb_get_context'
    bl_label = 'NP FB Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        NP020FB.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020FB.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020FB.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020FB.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020FB.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020FB.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020FB.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020FB.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020FB.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020FB.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020FB.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020FB.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020FB.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020FB.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020FB.edit_mode = 'PARTICLE_EDIT'
        return {'FINISHED'}


# Defining the operator for aquiring the list of selected objects and storing them for later re-calls:

class NPFBGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_fb_get_selection'
    bl_label = 'NP FB Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # Reading and storing the selection:
        NP020FB.selob = bpy.context.selected_objects
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and store it as a location for placing the helper object under the mouse:

class NPFBGetMouseloc(bpy.types.Operator):
    bl_idname = 'object.np_fb_get_mouseloc'
    bl_label = 'NP FB Get Mouseloc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector*100
        NP020FB.enterloc = copy.deepcopy(enterloc)
        np_print('02_GetMouseloc_FINISHED', ';', 'NP020FB.flag = ', NP020FB.flag)
        return{'FINISHED'}

    def invoke(self,context,event):
        args = (self, context)
        context.window_manager.modal_handler_add(self)
        np_print('02_GetMouseloc_INVOKED_FINISHED', ';', 'NP020FB.flag = ', NP020FB.flag)
        return {'RUNNING_MODAL'}


# Defining the operator that will generate the helper object at the spot marked by mouse, preparing for translation:

class NPFBAddHelper(bpy.types.Operator):
    bl_idname = 'object.np_fb_add_helper'
    bl_label = 'NP FB Add Helper'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_AddHelper_START', ';', 'NP020FB.flag = ', NP020FB.flag)
        enterloc = NP020FB.enterloc
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        helper = bpy.context.active_object
        helper.name = 'NP_FR_helper'
        NP020FB.helper = helper
        np_print('03_AddHelper_FINISHED', ';', 'NP020FB.flag = ', NP020FB.flag)
        return{'FINISHED'}


# Defining the operator that will change some of the system settings and prepare objects for the operation:

class NPFBPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_fb_prepare_context'
    bl_label = 'NP FB Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        flag = NP020FB.flag
        np_print('prepare, NP020FB.flag = ', flag)
        if flag == 'RUNTRANS0':
            helper = NP020FB.helper
            bpy.ops.object.select_all(action = 'DESELECT')
            helper.select = True
            bpy.context.scene.objects.active = helper
            bpy.context.tool_settings.use_snap = False
            bpy.context.tool_settings.snap_element = 'VERTEX'
            bpy.context.tool_settings.snap_target = 'ACTIVE'
            bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
            bpy.context.space_data.transform_orientation = 'GLOBAL'
            NP020FB.corner_brush = False
            NP020FB.constrain = False
            NP020FB.trans_custom = False
            NP020FB.qdef = None
            NP020FB.ndef = Vector((0.0, 0.0, 1.0))
            NP020FB.ro_hor_def = 0

        elif flag == 'RUNTRANS1_break':
            NP020FB.flag = 'RUNTRANS1'
            corner_brush = NP020FB.corner_brush
            helper = NP020FB.helper
            pointloc = NP020FB.pointloc
            loc = copy.deepcopy(helper.location)
            ndef = NP020FB.ndef
            '''
            matrix = NP020FB.matrix
            np_print('matrix =' , matrix)
            matrix_world = helper.matrix_world.to_3x3()
            np_print('matrix_world =' , matrix_world)
            matrix_world.rotate(matrix)
            matrix_world.resize_4x4()
            helper.matrix_world = matrix_world
            helper.location = pointloc
            bpy.ops.object.select_all(action = 'DESELECT')
            helper.select = True
            '''

            ro_hor_def = NP020FB.ro_hor_def
            ang_hor = ro_hor_def.to_euler()
            ang_hor = ang_hor[2]
            v1 = helper.location
            v2 = helper.location + Vector ((0.0, 0.0, 1.0))
            v3 = helper.location + ndef
            rot_axis = Vector((1.0, 0.0, 0.0))
            rot_axis.rotate(ro_hor_def)
            rot_ang = Vector((0.0, 0.0, 1.0)).angle(ndef)
            np_print('rot_axis, rot_ang =', rot_axis, rot_ang)

            bpy.ops.object.select_all(action = 'DESELECT')
            if corner_brush == False: helper.location = pointloc
            helper.select = True
            bpy.ops.transform.rotate(value = ang_hor ,axis = Vector((0.0, 0.0, 1.0)))
            bpy.ops.transform.rotate(value = rot_ang ,axis = rot_axis)
            NP020FB.trans_custom = True
            bpy.ops.transform.create_orientation(use = True)
            bpy.context.scene.objects.active = helper
            bpy.context.tool_settings.use_snap = False
            bpy.context.tool_settings.snap_element = 'VERTEX'
            bpy.context.tool_settings.snap_target = 'ACTIVE'
            bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'

        elif flag in ('RUNTRANS2', 'RUNTRANS3'):
            helper = NP020FB.helper
            bpy.context.scene.objects.active = helper
            bpy.context.tool_settings.use_snap = False
            bpy.context.tool_settings.snap_element = 'VERTEX'
            bpy.context.tool_settings.snap_target = 'ACTIVE'
            bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'

        return{'FINISHED'}


# Defining the operator that will let the user translate the helper to the desired point. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPFBRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_fb_run_translate'
    bl_label = 'NP FB Run Translate'
    bl_options = {'INTERNAL'}

    if NP020FB.flag == 'RUNTRANS0': np_print('04_RunTrans_START',';','NP020FB.flag = ', NP020FB.flag)
    elif NP020FB.flag == 'RUNTRANS1': np_print('05_RunTrans_START',';','NP020FB.flag = ', NP020FB.flag)
    elif NP020FB.flag == 'RUNTRANS2': np_print('06_RunTrans_START',';','NP020FB.flag = ', NP020FB.flag)
    elif NP020FB.flag == 'RUNTRANS3': np_print('07_RunTrans_START',';','NP020FB.flag = ', NP020FB.flag)

    def modal(self, context, event):
        context.area.tag_redraw()
        flag = NP020FB.flag
        helper = NP020FB.helper



        if event.ctrl and event.type in ('LEFTMOUSE', 'NUMPAD_ENTER', 'SPACE'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            if flag == 'RUNTRANS0':
                NP020FB.p0 = copy.deepcopy(helper.location)
                NP020FB.ndef = copy.deepcopy(NP020FB.n)
                NP020FB.qdef = copy.deepcopy(NP020FB.q)
                NP020FB.ro_hor_def = copy.deepcopy(NP020FB.ro_hor)
                NP020FB.corner_brush = True
                NP020FB.flag = 'RUNTRANS1_break'
            elif flag == 'RUNTRANS1':
                NP020FB.p1 = copy.deepcopy(helper.location)
                NP020FB.flag = 'RUNTRANS2'
            elif flag == 'RUNTRANS2':
                NP020FB.p2 = copy.deepcopy(helper.location)
                NP020FB.flag = 'RUNTRANS3'
            elif flag == 'RUNTRANS3':
                NP020FB.flag = 'GENERATE'
            np_print('04_RunTrans_left_enter_FINISHED',';','NP020FB.flag = ', NP020FB.flag)
            return{'FINISHED'}

        elif event.type in ('LEFTMOUSE', 'NUMPAD_ENTER', 'SPACE') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            if flag == 'RUNTRANS0':
                NP020FB.p0 = copy.deepcopy(NP020FB.pointloc)
                NP020FB.ndef = copy.deepcopy(NP020FB.n)
                NP020FB.qdef = copy.deepcopy(NP020FB.q)
                NP020FB.ro_hor_def = copy.deepcopy(NP020FB.ro_hor)
                NP020FB.flag = 'RUNTRANS1_break'
            elif flag == 'RUNTRANS1':
                NP020FB.p1 = copy.deepcopy(helper.location)
                NP020FB.flag = 'RUNTRANS2'
            elif flag == 'RUNTRANS2':
                NP020FB.p2 = copy.deepcopy(helper.location)
                NP020FB.flag = 'RUNTRANS3'
            elif flag == 'RUNTRANS3':
                NP020FB.flag = 'GENERATE'
            np_print('04_RunTrans_left_enter_FINISHED',';','NP020FB.flag = ', NP020FB.flag)
            return{'FINISHED'}

        elif event.type == 'RET':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if flag == 'RUNTRANS0':
                NP020FB.ndef = copy.deepcopy(NP020FB.n)
                NP020FB.qdef = copy.deepcopy(NP020FB.q)
                NP020FB.ro_hor_def = copy.deepcopy(NP020FB.ro_hor)
                NP020FB.constrain = True
            elif flag == 'RUNTRANS1':
                NP020FB.p1 = copy.deepcopy(helper.location)
                NP020FB.flag = 'RUNTRANS2'
            elif flag == 'RUNTRANS2':
                NP020FB.p2 = copy.deepcopy(helper.location)
                NP020FB.flag = 'GENERATE'
            np_print('04_RunTrans_right_FINISHED',';','NP020FB.flag = ', NP020FB.flag)
            return{'FINISHED'}




        elif event.type in ('ESC', 'RIGHTMOUSE'):
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020FB.flag = 'EXIT'
            np_print('04_RunTrans_esc_right_FINISHED',';','NP020FB.flag = ', NP020FB.flag)
            return{'FINISHED'}

        np_print('04_RunTrans_count_PASS_THROUGH',';','NP020FB.flag = ', NP020FB.flag)
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('04_RunTrans_INVOKE_START')
        helper = NP020FB.helper
        flag = NP020FB.flag
        selob = NP020FB.selob

        if context.area.type == 'VIEW_3D':
            if flag in ('RUNTRANS0', 'RUNTRANS1', 'RUNTRANS2', 'RUNTRANS3'):
                self.co2d = ((event.mouse_region_x, event.mouse_region_y))
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_Overlay, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                if flag == 'RUNTRANS0':
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
                    np_print('04_RunTrans0_INVOKED_RUNNING_MODAL',';','NP020FB.flag = ', NP020FB.flag)
                elif flag == 'RUNTRANS1':
                    bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False))
                    np_print('04_RunTrans1_INVOKED_RUNNING_MODAL',';','NP020FB.flag = ', NP020FB.flag)
                elif flag == 'RUNTRANS2':
                    bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(False, True, False))
                    np_print('04_RunTrans2_INVOKED_RUNNING_MODAL',';','NP020FB.flag = ', NP020FB.flag)
                elif flag == 'RUNTRANS3':
                    bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(False, False, True))
                    np_print('04_RunTrans3_INVOKED_RUNNING_MODAL',';','NP020FB.flag = ', NP020FB.flag)
                return {'RUNNING_MODAL'}
            else:
                np_print('04_RunTrans_INVOKE_DECLINED_wrong_flag_FINISHED',';','NP020FB.flag = ', NP020FB.flag)
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            NP020FB.flag = 'EXIT'
            np_print('04_RunTrans_INVOKE_DECLINED_no_VIEW_3D_FINISHED',';','NP020FB.flag = ', NP020FB.flag)
            return {'FINISHED'}


# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of RunTranslate operator:

def DRAW_Overlay(self, context):

    np_print('DRAW_Overlay_START',';','NP020FB.flag = ', NP020FB.flag)

    '''
    addon_prefs = context.user_preferences.addons[__package__].preferences
    badge = addon_prefs.npfb_badge
    badge_size = addon_prefs.npfb_badge_size
    dist_scale = addon_prefs.npfb_dist_scale
    '''
    flag = NP020FB.flag
    helper = NP020FB.helper
    matrix = helper.matrix_world.to_3x3()
    region = bpy.context.region
    rv3d = bpy.context.region_data
    rw = region.width
    rh = region.height
    qdef = NP020FB.qdef
    ndef = NP020FB.ndef
    ro_hor_def = NP020FB.ro_hor_def
    constrain = NP020FB.constrain
    np_print('rw, rh', rw, rh)
    rmin = int(min(rw, rh) / 50)
    if rmin == 0: rmin = 1
    co2d = view3d_utils.location_3d_to_region_2d(region, rv3d, helper.location)
    if qdef != None and constrain == False:
        q = qdef
        n = ndef
        pointloc = helper.location
        ro_hor = ro_hor_def

    elif qdef != None and constrain == True:
        q = qdef
        n = ndef
        pointloc = get_ro_normal_from_vertical(region, rv3d, co2d)[2]
        ro_hor = ro_hor_def

    else:
        q = get_ro_normal_from_vertical(region, rv3d, co2d)[1]
        n = get_ro_normal_from_vertical(region, rv3d, co2d)[0]
        pointloc = get_ro_normal_from_vertical(region, rv3d, co2d)[2]
        ro_hor, isohipse = get_ro_x_from_iso(region, rv3d, co2d, helper.location)

    if pointloc == Vector((0.0, 0.0, 0.0)): pointloc = helper.location
    np_print('n / q', n, q)
    NP020FB.q = q
    NP020FB.n = n
    NP020FB.pointloc = pointloc
    NP020FB.ro_hor = ro_hor
    np_print('co2d, n, q', co2d, n, q)

    # Acquiring factor for graphics scaling in order to be space - independent


    fac = get_fac_from_view_loc_plane(region, rv3d, rmin, helper.location, q)
    NP020FB.fac = fac


    symbol = [[18, 37], [21, 37], [23, 33], [26, 33]]
    badge_mode = 'RUN'


    if qdef != None:
        matrix.rotate(ro_hor)
        matrix.rotate(qdef)
    NP020FB.matrix = matrix

    if flag == 'RUNTRANS0':
        instruct = 'choose plane / place corner point'
        keys_aff = 'LMB - select, CTRL - snap, ENT - lock plane'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'
        box = [helper.location, helper.location, helper.location, helper.location, helper.location, helper.location, helper.location, helper.location]

        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'RUNTRANS1':
        instruct = 'define the width of the box'
        keys_aff = 'LMB - select, CTRL - snap, NUMPAD - value'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'
        p0 = NP020FB.p0
        box = [p0, helper.location, helper.location, p0, p0, helper.location, helper.location, p0 ]

        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'RUNTRANS2':
        instruct = 'define the length of the box'
        keys_aff = 'LMB - select, CTRL - snap, NUMPAD - value'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'
        p0 = NP020FB.p0
        p1 = NP020FB.p1
        box = [p0, p1, helper.location, p0 + (helper.location-p1), p0, p1, helper.location, p0 + (helper.location-p1)]

        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    elif flag == 'RUNTRANS3':
        instruct = 'define the height of the box'
        keys_aff = 'LMB - select, CTRL - snap, NUMPAD - value'
        keys_nav = ''
        keys_neg = 'ESC, RMB - quit'
        p0 = NP020FB.p0
        p1 = NP020FB.p1
        p2 = NP020FB.p2
        p3 = p0 + (p2 - p1)
        h = helper.location - p2
        box = [p0, p1, p2, p3, p0 + h, p1 + h, p2 + h, p3 + h]

        message_main = 'CTRL+SNAP'
        message_aux = None
        aux_num = None
        aux_str = None

    NP020FB.box = box


    # ON-SCREEN INSTRUCTIONS:

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    # drawing of box:

    box_2d = []
    for co in box:
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        box_2d.append(co)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i in range (0, 4):
        bgl.glVertex2f(*box_2d[i])
    bgl.glVertex2f(*box_2d[0])
    bgl.glVertex2f(*box_2d[4])
    bgl.glVertex2f(*box_2d[7])
    bgl.glVertex2f(*box_2d[3])
    bgl.glVertex2f(*box_2d[7])
    bgl.glVertex2f(*box_2d[6])
    bgl.glVertex2f(*box_2d[2])
    bgl.glVertex2f(*box_2d[6])
    bgl.glVertex2f(*box_2d[5])
    bgl.glVertex2f(*box_2d[1])
    bgl.glVertex2f(*box_2d[5])
    bgl.glVertex2f(*box_2d[4])
    bgl.glEnd()
    bgl.glColor4f(1.0, 1.0, 1.0, 0.25)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    boxfaces = ((0, 1, 2, 3), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7))
    for face in boxfaces:
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        bgl.glVertex2f(*box_2d[face[0]])
        bgl.glVertex2f(*box_2d[face[1]])
        bgl.glVertex2f(*box_2d[face[2]])
        bgl.glVertex2f(*box_2d[face[3]])
        bgl.glEnd()


    # Drawing the small badge near the cursor with the basic instructions:





    display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str)


    # writing the dots for boxwidget widget at center of scene:

    geowidget_base = [(0.0 ,0.0 ,0.0), (5.0 ,0.0 ,0.0), (5.0 ,-3.0 ,0.0), (0.0, -3.0 ,0.0)]
    geowidget_top = [(0.0 ,0.0 ,4.0), (5.0 ,0.0 ,4.0), (5.0 ,-3.0 ,4.0), (0.0, -3.0 ,4.0)]
    geowidget_rest = [(0.0 ,0.0 ,0.0), (0.0 ,0.0 ,4.0), (5.0 ,0.0 ,4.0), (5.0 ,0.0 ,0.0), (5.0 ,-3.0 ,0.0), (5.0 ,-3.0 ,4.0), (0.0, -3.0 ,4.0), (0.0, -3.0 ,0.0)]

    # ON-SCREEN DISPLAY OF GEOWIDGET:

    display_geowidget(region, rv3d, fac, ro_hor, q, helper.location, n, qdef, geowidget_base, geowidget_top, geowidget_rest)




    # ON-SCREEN DISTANCES AND OTHERS:
    '''

    if addon_prefs.npfb_suffix == 'None':
        suffix = None

    elif addon_prefs.npfb_suffix == 'km':
        suffix = ' km'

    elif addon_prefs.npfb_suffix == 'm':
        suffix = ' m'

    elif addon_prefs.npfb_suffix == 'cm':
        suffix = ' cm'

    elif addon_prefs.npfb_suffix == 'mm':
        suffix = ' mm'

    elif addon_prefs.npfb_suffix == 'nm':
        suffix = ' nm'

    elif addon_prefs.npfb_suffix == "'":
        suffix = "'"

    elif addon_prefs.npfb_suffix == '"':
        suffix = '"'

    elif addon_prefs.npfb_suffix == 'thou':
        suffix = ' thou'
    '''


    # ON-SCREEN DISTANCES:

    display_distance_between_two_points(region, rv3d, box[0], box[1])
    display_distance_between_two_points(region, rv3d, box[1], box[2])
    display_distance_between_two_points(region, rv3d, box[2], box[6])

    #ENDING:

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# Defining the operator that will generate the box mesh from the collected points:

class NPFBGenerateGeometry(bpy.types.Operator):
    bl_idname = 'object.np_fb_generate_geometry'
    bl_label = 'NP FB Generate Geometry'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        flag = NP020FB.flag
        wire = True
        material = True
        if flag == 'GENERATE':
            boxverts = (NP020FB.box[0], NP020FB.box[1])
            boxedges = [(0, 1)]
            boxfaces = ()
            boxme = bpy.data.meshes.new('float_box')
            #print (boxverts,boxedges,boxfaces)
            boxme.from_pydata(boxverts, boxedges, boxfaces)
            boxob = bpy.data.objects.new('float_box', boxme)
            boxob.location = mathutils.Vector((0, 0, 0))
            scn = bpy.context.scene
            scn.objects.link(boxob)
            scn.objects.active = boxob
            scn.update()
            bm = bmesh.new()   # create an empty BMesh
            bm.from_mesh(boxme)   # fill it in from a Mesh


            #bpy.ops.mesh.select_all(action = 'SELECT')
            bmesh.ops.extrude_edge_only(bm, edges = bm.edges[:])
            vec = NP020FB.box[2] - NP020FB.box[1]
            bm.verts.ensure_lookup_table()
            for vert in bm.verts: np_print('vert.index:', vert.index)
            bmesh.ops.translate(bm, vec = vec, verts = [bm.verts[2], bm.verts[3]])
            bmesh.ops.extrude_face_region(bm, geom = bm.faces[:])
            vec = NP020FB.box[6] - NP020FB.box[2]
            bm.verts.ensure_lookup_table()
            bmesh.ops.translate(bm, vec = vec, verts = [bm.verts[4], bm.verts[5], bm.verts[6], bm.verts[7]])
            bm.to_mesh(boxme)
            bm.free()
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action = 'SELECT')
            bpy.ops.mesh.normals_make_consistent()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.select_all(action = 'DESELECT')
            boxob.select = True
            bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
            if wire:
                boxob.show_wire = True
            if material:
                mtl = bpy.data.materials.new('float_box_material')
                mtl.diffuse_color = (1.0, 1.0, 1.0)
                boxme.materials.append(mtl)
            activelayer = bpy.context.scene.active_layer
            np_print('activelayer:', activelayer)
            layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
            layers[activelayer] = True
            layers = tuple(layers)
            np_print(layers)
            bpy.ops.object.move_to_layer(layers = layers)
            NP020FB.boxob = boxob

        return{'FINISHED'}

# Restoring the object selection and system settings from before the operator activation:

class NPFBRestoreContext(bpy.types.Operator):
    bl_idname = "object.np_fb_restore_context"
    bl_label = "NP FB Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        selob = NP020FB.selob
        helper = NP020FB.helper
        boxob = NP020FB.boxob
        helper.hide = False
        bpy.ops.object.select_all(action = 'DESELECT')
        helper.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')
        if boxob == None:
            for ob in selob:
                ob.select = True
            if NP020FB.acob is not None:
                bpy.context.scene.objects.active = NP020FB.acob
                bpy.ops.object.mode_set(mode = NP020FB.edit_mode)
        else:
            boxob.select = True
            bpy.context.scene.objects.active = boxob
            bpy.ops.object.mode_set(mode = NP020FB.edit_mode)
        if NP020FB.trans_custom: bpy.ops.transform.delete_orientation()
        bpy.context.tool_settings.use_snap = NP020FB.use_snap
        bpy.context.tool_settings.snap_element = NP020FB.snap_element
        bpy.context.tool_settings.snap_target = NP020FB.snap_target
        bpy.context.space_data.pivot_point = NP020FB.pivot_point
        bpy.context.space_data.transform_orientation = NP020FB.trans_orient

        NP020FB.flag = 'RUNTRANS0'
        NP020FB.boxob = None
        return {'FINISHED'}


# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    #bpy.app.handlers.scene_update_post.append(NPFB_scene_update)

    NP020FloatBox.define('OBJECT_OT_np_fb_get_context')
    NP020FloatBox.define('OBJECT_OT_np_fb_get_selection')
    NP020FloatBox.define('OBJECT_OT_np_fb_get_mouseloc')
    NP020FloatBox.define('OBJECT_OT_np_fb_add_helper')
    NP020FloatBox.define('OBJECT_OT_np_fb_prepare_context')
    for i in range(1, 15):
        NP020FloatBox.define('OBJECT_OT_np_fb_run_translate')
    NP020FloatBox.define('OBJECT_OT_np_fb_prepare_context')
    NP020FloatBox.define('OBJECT_OT_np_fb_run_translate')
    NP020FloatBox.define('OBJECT_OT_np_fb_prepare_context')
    NP020FloatBox.define('OBJECT_OT_np_fb_run_translate')
    NP020FloatBox.define('OBJECT_OT_np_fb_prepare_context')
    NP020FloatBox.define('OBJECT_OT_np_fb_run_translate')
    NP020FloatBox.define('OBJECT_OT_np_fb_generate_geometry')
    NP020FloatBox.define('OBJECT_OT_np_fb_restore_context')

def unregister():
    #bpy.app.handlers.scene_update_post.remove(NPFB_scene_update)
    pass
