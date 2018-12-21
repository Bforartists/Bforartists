
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
    'name': 'NP 020 Point Align',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Aligns selected objects using 1, 2 or 3 pairs of snap points',
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

class NP020PointAlign(bpy.types.Macro):
    bl_idname = 'object.np_020_point_align'
    bl_label = 'NP 020 Point Align'
    bl_options = {'UNDO'}


# Defining the storage class that will serve as a variable bank for exchange among the classes. Later, this bank will receive more variables with their values for safe keeping, as the program goes on:

class NP020PL:

    flag = 'RUNTRANSF0'

# Defining the scene update algorithm that will track the state of the objects during modal transforms, which is otherwise impossible:
'''
@persistent
def NPPL_scene_update(context):

    if bpy.data.objects.is_updated:
        region = bpy.context.region
        rv3d = bpy.context.region_data
        helper = NP020PL.helper
        co = helper.location
'''

# Defining the first of the classes from the macro, that will gather the current system settings set by the user. Some of the system settings will be changed during the process, and will be restored when macro has completed.

class NPPLGetContext(bpy.types.Operator):
    bl_idname = 'object.np_pl_get_context'
    bl_label = 'NP PL Get Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if bpy.context.selected_objects == []:
            self.report({'WARNING'}, "Please select objects first")
            return {'CANCELLED'}
        NP020PL.use_snap = copy.deepcopy(bpy.context.tool_settings.use_snap)
        NP020PL.snap_element = copy.deepcopy(bpy.context.tool_settings.snap_element)
        NP020PL.snap_target = copy.deepcopy(bpy.context.tool_settings.snap_target)
        NP020PL.pivot_point = copy.deepcopy(bpy.context.space_data.pivot_point)
        NP020PL.trans_orient = copy.deepcopy(bpy.context.space_data.transform_orientation)
        NP020PL.curloc = copy.deepcopy(bpy.context.scene.cursor_location)
        NP020PL.acob = bpy.context.active_object
        if bpy.context.mode == 'OBJECT':
            NP020PL.edit_mode = 'OBJECT'
        elif bpy.context.mode in ('EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE'):
            NP020PL.edit_mode = 'EDIT'
        elif bpy.context.mode == 'POSE':
            NP020PL.edit_mode = 'POSE'
        elif bpy.context.mode == 'SCULPT':
            NP020PL.edit_mode = 'SCULPT'
        elif bpy.context.mode == 'PAINT_WEIGHT':
            NP020PL.edit_mode = 'WEIGHT_PAINT'
        elif bpy.context.mode == 'PAINT_TEXTURE':
            NP020PL.edit_mode = 'TEXTURE_PAINT'
        elif bpy.context.mode == 'PAINT_VERTEX':
            NP020PL.edit_mode = 'VERTEX_PAINT'
        elif bpy.context.mode == 'PARTICLE':
            NP020PL.edit_mode = 'PARTICLE_EDIT'
        return {'FINISHED'}


# Defining the operator for aquiring the list of selected objects and storing them for later re-calls:

class NPPLGetSelection(bpy.types.Operator):
    bl_idname = 'object.np_pl_get_selection'
    bl_label = 'NP PL Get Selection'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # Reading and storing the selection:
        NP020PL.selob = bpy.context.selected_objects
        return {'FINISHED'}


# Defining the operator that will read the mouse position in 3D when the command is activated and store it as a location for placing the helper object under the mouse:

class NPPLGetMouseloc(bpy.types.Operator):
    bl_idname = 'object.np_pl_get_mouseloc'
    bl_label = 'NP PL Get Mouseloc'
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        region = context.region
        rv3d = context.region_data
        co2d = ((event.mouse_region_x, event.mouse_region_y))
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, co2d)
        enterloc = view3d_utils.region_2d_to_origin_3d(region, rv3d, co2d) + view_vector*100
        NP020PL.enterloc = copy.deepcopy(enterloc)
        np_print('02_GetMouseloc_FINISHED', ';', 'NP020PL.flag = ', NP020PL.flag)
        return{'FINISHED'}

    def invoke(self,context,event):
        args = (self, context)
        context.window_manager.modal_handler_add(self)
        np_print('02_GetMouseloc_INVOKED_FINISHED', ';', 'NP020PL.flag = ', NP020PL.flag)
        return {'RUNNING_MODAL'}


# Defining the operator that will generate the helper object at the spot marked by mouse, preparing for translation:

class NPPLAddHelper(bpy.types.Operator):
    bl_idname = 'object.np_pl_add_helper'
    bl_label = 'NP PL Add Helper'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        np_print('03_AddHelper_START', ';', 'NP020PL.flag = ', NP020PL.flag)
        enterloc = NP020PL.enterloc
        bpy.ops.object.add(type = 'MESH',location = enterloc)
        helper = bpy.context.active_object
        helper.name = 'NP_PA_helper'
        NP020PL.helper = helper
        np_print('03_AddHelper_FINISHED', ';', 'NP020PL.flag = ', NP020PL.flag)
        return{'FINISHED'}


# Defining the operator that will change some of the system settings and prepare objects for the operation:

class NPPLPrepareContext(bpy.types.Operator):
    bl_idname = 'object.np_pl_prepare_context'
    bl_label = 'NP PL Prepare Context'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        flag = NP020PL.flag
        helper = NP020PL.helper
        NP020PL.mode = '1P'
        NP020PL.snap = 'VERTEX'
        np_print('prepare, NP020PL.flag = ', flag)

        bpy.ops.object.select_all(action = 'DESELECT')
        helper.select = True
        bpy.context.scene.objects.active = helper
        bpy.context.tool_settings.use_snap = False
        bpy.context.tool_settings.snap_element = 'VERTEX'
        bpy.context.tool_settings.snap_target = 'ACTIVE'
        bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
        bpy.context.space_data.transform_orientation = 'GLOBAL'

        NP020PL.frompoints = [None, None, None]
        NP020PL.topoints = [None, None, None]

        return{'FINISHED'}


# Defining the operator that will let the user translate the helper to the desired point. It also uses some listening operators that clean up the leftovers should the user interrupt the command. Many thanks to CoDEmanX and lukas_t:

class NPPLRunTranslate(bpy.types.Operator):
    bl_idname = 'object.np_pl_run_translate'
    bl_label = 'NP PL Run Translate'
    bl_options = {'INTERNAL'}

    np_print('RunTrans_START',';','NP020PL.flag = ', NP020PL.flag)

    def modal(self, context, event):
        context.area.tag_redraw()
        flag = NP020PL.flag
        helper = NP020PL.helper

        if event.type in ('LEFTMOUSE', 'NUMPAD_ENTER', 'SPACE') and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            if flag == 'RUNTRANSF0':
                NP020PL.frompoints[0] = copy.deepcopy(NP020PL.helper.location)
                NP020PL.flag = 'RUNTRANST0'
            elif flag == 'RUNTRANST0':
                NP020PL.topoints[0] = copy.deepcopy(NP020PL.helper.location)
                NP020PL.flag = 'RUNTRANSF1'
            elif flag == 'RUNTRANSF1':
                NP020PL.frompoints[1] = copy.deepcopy(NP020PL.helper.location)
                NP020PL.flag = 'RUNTRANST1'
            elif flag == 'RUNTRANST1':
                NP020PL.topoints[1] = copy.deepcopy(NP020PL.helper.location)
                NP020PL.mode = '2P'
                NP020PL.flag = 'RUNTRANSF2'
            elif flag == 'RUNTRANSF2':
                NP020PL.frompoints[2] = copy.deepcopy(NP020PL.helper.location)
                NP020PL.flag = 'RUNTRANST2'
            elif flag == 'RUNTRANST2':
                NP020PL.topoints[2] = copy.deepcopy(NP020PL.helper.location)
                NP020PL.mode = '3P'
                NP020PL.flag = 'ALIGN'
            np_print('RunTrans_left_enter_FINISHED',';','NP020PL.flag = ', NP020PL.flag)
            return{'FINISHED'}

        elif event.type == 'RET' and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if bpy.context.tool_settings.snap_element == 'VERTEX':
                bpy.context.tool_settings.snap_element = 'EDGE'
                NP020PL.snap = 'EDGE'
            elif bpy.context.tool_settings.snap_element == 'EDGE':
                bpy.context.tool_settings.snap_element = 'FACE'
                NP020PL.snap = 'FACE'
            elif bpy.context.tool_settings.snap_element == 'FACE':
                bpy.context.tool_settings.snap_element = 'VERTEX'
                NP020PL.snap = 'VERTEX'
            np_print('RunTrans_enter_PASS')
            return{'FINISHED'}

        elif event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if NP020PL.topoints[0] != None:
                NP020PL.flag = 'ALIGN'
                np_print('04_RunTrans_right_ALIGN',';','NP020PL.flag = ', NP020PL.flag)
            else:
                NP020PL.flag = 'EXIT'
                np_print('04_RunTrans_right_EXIT',';','NP020PL.flag = ', NP020PL.flag)
            return{'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            NP020PL.flag = 'EXIT'
            np_print('04_RunTrans_esc_EXIT',';','NP020PL.flag = ', NP020PL.flag)
            return{'FINISHED'}

        np_print('04_RunTrans_count_PASS_THROUGH',';','NP020PL.flag = ', NP020PL.flag)
        return{'PASS_THROUGH'}

    def invoke(self, context, event):
        np_print('RunTrans_INVOKE_START')
        helper = NP020PL.helper
        flag = NP020PL.flag

        if context.area.type == 'VIEW_3D':
            if flag in ('RUNTRANSF0', 'RUNTRANST0', 'RUNTRANSF1', 'RUNTRANST1', 'RUNTRANSF2', 'RUNTRANST2'):
                self.co2d = ((event.mouse_region_x, event.mouse_region_y))
                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(DRAW_Overlay, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                bpy.ops.transform.translate('INVOKE_DEFAULT')
                np_print('RunTrans_INVOKED_RUNNING_MODAL',';','NP020PL.flag = ', NP020PL.flag)
                return {'RUNNING_MODAL'}
            else:
                np_print('RunTrans_INVOKE_DECLINED_wrong_flag_FINISHED',';','NP020PL.flag = ', NP020PL.flag)
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            NP020PL.flag = 'EXIT'
            np_print('RunTrans_INVOKE_DECLINED_no_VIEW_3D_FINISHED',';','NP020PL.flag = ', NP020PL.flag)
            return {'FINISHED'}


# Defining the set of instructions that will draw the OpenGL elements on the screen during the execution of RunTranslate operator:

def DRAW_Overlay(self, context):

    np_print('DRAW_Overlay_START',';','NP020PL.flag = ', NP020PL.flag)

    flag = NP020PL.flag
    helper = NP020PL.helper
    region = bpy.context.region
    rv3d = bpy.context.region_data
    rw = region.width
    rh = region.height
    co2d = view3d_utils.location_3d_to_region_2d(region, rv3d, helper.location)
    frompoints = NP020PL.frompoints
    topoints = NP020PL.topoints


    col_line_main = (1.0, 1.0, 1.0, 1.0)
    col_line_shadow = (0.1, 0.1, 0.1, 0.25)

    #greys:
    mark_col_A = (0.25, 0.25, 0.25, 1.0)
    mark_col_B = (0.5, 0.5, 0.5, 1.0)
    mark_col_C = (0.75, 0.75, 0.75, 1.0)

    #marins
    mark_col_A = (0.25, 0.35, 0.4, 1.0)
    mark_col_B = (0.5, 0.6, 0.65, 1.0)
    mark_col_C = (0.67, 0.77, 0.82, 1.0)

    # writing the dots for recwidget widget at center of scene:

    r = 12
    angstep = 20
    psize = 25
    pofsetx = 15
    pofsety = 15
    fsize = 20
    fofsetx = -8
    fofsety = -7



    widget_circle = construct_circle_2d(r, angstep)


    if flag == 'RUNTRANSF0':
        instruct = 'place start for point a'
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap'
        keys_neg = 'RMB, ESC - quit'
        frompoints[0] = helper.location

    elif flag == 'RUNTRANST0':
        instruct = 'place target for point a'
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap, MMB - lock axis, NUMPAD - value'
        keys_neg = 'RMB, ESC - quit'
        topoints[0] = helper.location

    elif flag == 'RUNTRANSF1':
        instruct = 'place start for point b'
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap, MMB - lock axis, NUMPAD - value, RMB - align A (translate)'
        keys_neg = 'ESC - quit'
        frompoints[1] = helper.location

    elif flag == 'RUNTRANST1':
        instruct = 'place target for point b'
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap, MMB - lock axis, NUMPAD - value, RMB - align A (translate)'
        keys_neg = 'ESC - quit'
        topoints[1] = helper.location

    elif flag == 'RUNTRANSF2':
        instruct = 'place start for point c'
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap, MMB - lock axis, NUMPAD - value, RMB - align AB (translate, rotate)'
        keys_neg = 'ESC - quit'
        frompoints[2] = helper.location

    elif flag == 'RUNTRANST2':
        instruct = 'place target for point c'
        keys_aff = 'LMB - select, CTRL - snap, ENT - change snap, MMB - lock axis, NUMPAD - value, RMB - align AB (translate, rotate)'
        keys_neg = 'ESC - quit'
        topoints[2] = helper.location


    # ON-SCREEN INSTRUCTIONS:


    keys_nav = ''

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    # LINE:

    for i, frompoint in enumerate(frompoints):
        topoint = topoints[i]
        if frompoint != None and topoint != None:
            bgl.glColor4f(*col_line_shadow)
            bgl.glLineWidth(1.4)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            frompoint = view3d_utils.location_3d_to_region_2d(region, rv3d, frompoint)
            topoint = view3d_utils.location_3d_to_region_2d(region, rv3d, topoint)
            bgl.glVertex2f((frompoint[0] - 1), (frompoint[1] - 1))
            bgl.glVertex2f((topoint[0] - 1), (topoint[1] - 1))
            bgl.glEnd()

            bgl.glColor4f(*col_line_main)
            bgl.glLineWidth(1.4)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            bgl.glVertex2f(*frompoint)
            bgl.glVertex2f(*topoint)
            bgl.glEnd()


    # drawing of markers:
    i = 0
    for point in frompoints:
        if point != None:
            point = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
            point[0] = point[0] + pofsetx
            point[1] = point[1] + pofsety
            widget = []
            for co in widget_circle:
                c = [0.0, 0.0]
                c[0] = co[0] + point[0] + pofsetx
                c[1] = co[1] + point[1] + pofsety
                widget.append(c)
            bgl.glEnable(bgl.GL_BLEND)
            if i == 0:
                bgl.glColor4f(*mark_col_A)
                mark = "A"
            elif i == 1:
                bgl.glColor4f(*mark_col_B)
                mark = "B"
            elif i == 2:
                bgl.glColor4f(*mark_col_C)
                mark = "C"

            '''
            bgl.glLineWidth(1)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for co in widget:
                bgl.glVertex2f(*co)
            bgl.glVertex2f(*widget[len(widget) - 1])
            bgl.glEnd()
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for co in widget:
                bgl.glVertex2f(*co)
            bgl.glEnd()
            '''
            font_id = 0
            bgl.glEnable(bgl.GL_POINT_SMOOTH)
            bgl.glPointSize(psize)
            bgl.glBegin(bgl.GL_POINTS)
            bgl.glVertex2f(*point)
            bgl.glEnd()
            bgl.glDisable(bgl.GL_POINT_SMOOTH)

            bgl.glColor4f(1.0, 1.0, 1.0, 0.75)
            blf.size(font_id, fsize, 72)
            blf.position(font_id, point[0] + fofsetx, point[1] + fofsety, 0)
            blf.draw(font_id, mark)
            i = i + 1

    i = 0
    for point in topoints:
        if point != None:
            point = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
            point[0] = point[0] + pofsetx
            point[1] = point[1] + pofsety
            widget = []
            for co in widget_circle:
                c = [0.0, 0.0]
                c[0] = co[0] + point[0] + pofsetx
                c[1] = co[1] + point[1] + pofsety
                widget.append(c)
            bgl.glEnable(bgl.GL_BLEND)
            if i == 0:
                bgl.glColor4f(*mark_col_A)
                mark = "A'"
            elif i == 1:
                bgl.glColor4f(*mark_col_B)
                mark = "B'"
            elif i == 2:
                bgl.glColor4f(*mark_col_C)
                mark = "C'"
            '''
            bgl.glLineWidth(1)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for co in widget:
                bgl.glVertex2f(*co)
            bgl.glVertex2f(*widget[len(widget) - 1])
            bgl.glEnd()
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for co in widget:
                bgl.glVertex2f(*co)
            bgl.glEnd()
            '''
            font_id = 0
            bgl.glEnable(bgl.GL_POINT_SMOOTH)
            bgl.glPointSize(psize)
            bgl.glBegin(bgl.GL_POINTS)
            bgl.glVertex2f(*point)
            bgl.glEnd()
            bgl.glDisable(bgl.GL_POINT_SMOOTH)

            bgl.glColor4f(1.0, 1.0, 1.0, 0.75)
            blf.size(font_id, fsize, 72)
            blf.position(font_id, point[0] + fofsetx, point[1] + fofsety, 0)
            blf.draw(font_id, mark)
            i = i + 1


    #ENDING:

    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# Defining the operator that will align the selected objects according to the collected points:

class NPPLAlignSelected(bpy.types.Operator):
    bl_idname = 'object.np_pl_align_selected'
    bl_label = 'NP PL Align Selected'
    bl_options = {'INTERNAL'}

    def execute(self, context):

        flag = NP020PL.flag
        mode = NP020PL.mode
        helper = NP020PL.helper
        selob = NP020PL.selob
        frompoints = NP020PL.frompoints
        topoints = NP020PL.topoints
        scale = False
        copy = False

        bpy.ops.object.select_all(action = 'DESELECT')
        helper.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')


        fromverts = []
        for point in frompoints:
            if point != None:
                vert = point.to_tuple()
                fromverts.append(vert)
        fromedges = []
        fromfaces = []

        toverts = []
        for point in topoints:
            if point != None:
                vert = point.to_tuple()
                toverts.append(vert)
        toedges = []
        tofaces = []

        fromme = bpy.data.meshes.new('NP020PL_from')
        fromme.from_pydata(fromverts, fromedges, fromfaces)
        fromob = bpy.data.objects.new('NP020PL_from',fromme)
        fromob.location = mathutils.Vector((0,0,0))


        tome = bpy.data.meshes.new('NP020PL_to')
        tome.from_pydata(toverts, toedges, tofaces)
        toob = bpy.data.objects.new('NP020PL_to',tome)
        toob.location = mathutils.Vector((0,0,0))

        scn = bpy.context.scene
        scn.objects.link(fromob)
        scn.objects.link(toob)
        scn.update()

        bpy.ops.object.select_all(action = 'DESELECT')
        fromob.select = True
        bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')


        for ob in selob:
            ob.select = True

        if flag == 'ALIGN':
            value = (tome.vertices[0].co) - (fromme.vertices[0].co + fromob.location)
            bpy.ops.transform.translate(value = value)
            scn.update()
            if mode in ('2P', '3P'):

                rot_axis = geometry.normal(tome.vertices[0].co, tome.vertices[1].co, (fromme.vertices[1].co + fromob.location))
                rot_ang = (((fromme.vertices[1].co + fromob.location) - tome.vertices[0].co)).angle((tome.vertices[1].co - tome.vertices[0].co))
                np_print('rot_axis, rot_ang =', rot_axis, rot_ang)
                bpy.context.scene.cursor_location = tome.vertices[0].co
                bpy.context.space_data.pivot_point = 'CURSOR'
                bpy.ops.transform.rotate(value = -rot_ang, axis = rot_axis)
                np_print('fromme.vertices = ', fromme.vertices)
                bpy.ops.object.select_all(action = 'DESELECT')
                fromob.select = True
                bpy.ops.object.transform_apply(rotation=True,scale=True)
                for ob in selob:
                    ob.select = True
                scn.update()
                #if scale:
                    #bpy.ops.transform_resize(value=(1.0, 1.0, 1.0))
                if mode == '3P':
                    proj_t = geometry.intersect_point_line(tome.vertices[2].co, tome.vertices[1].co, tome.vertices[0].co)[0]
                    proj_f = geometry.intersect_point_line((fromme.vertices[2].co + fromob.location), tome.vertices[1].co, tome.vertices[0].co)[0]
                    np_print('proj_t, proj_f, tome[1], tome[0]', proj_t, proj_f, tome.vertices[1].co, tome.vertices[0].co)
                    #rot_axis = geometry.normal(tome.vertices[2].co, proj, (fromme.vertices[2].co + fromob.location))
                    rot_axis = tome.vertices[1].co - tome.vertices[0].co
                    rot_ang = ((tome.vertices[2].co - proj_t)).angle(((fromme.vertices[2].co + fromob.location) - proj_f))
                    np_print('rot_axis, rot_ang =', rot_axis, rot_ang)
                    bpy.context.scene.cursor_location = tome.vertices[1].co
                    bpy.ops.transform.rotate(value = -rot_ang, axis = rot_axis)
                    bpy.ops.object.select_all(action = 'DESELECT')
                    fromob.select = True
                    bpy.ops.object.transform_apply(rotation=True,scale=True)
                    for ob in selob:
                        ob.select = True
                    if ((tome.vertices[2].co - proj_t)).angle(((fromme.vertices[2].co + fromob.location) - proj_f)) != 0: bpy.ops.transform.rotate(value = 2*rot_ang, axis = rot_axis)

        bpy.ops.object.select_all(action = 'DESELECT')
        fromob.select = True
        toob.select = True
        bpy.ops.object.delete('EXEC_DEFAULT')

        return{'FINISHED'}

# Restoring the object selection and system settings from before the operator activation:

class NPPLRestoreContext(bpy.types.Operator):
    bl_idname = "object.np_pl_restore_context"
    bl_label = "NP PL Restore Context"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        bpy.ops.object.select_all(action = 'DESELECT')
        selob = NP020PL.selob
        for ob in selob:
            ob.select = True
        if NP020PL.acob is not None:
            bpy.context.scene.objects.active = NP020PL.acob
            bpy.ops.object.mode_set(mode = NP020PL.edit_mode)
        bpy.context.tool_settings.use_snap = NP020PL.use_snap
        bpy.context.tool_settings.snap_element = NP020PL.snap_element
        bpy.context.tool_settings.snap_target = NP020PL.snap_target
        bpy.context.space_data.pivot_point = NP020PL.pivot_point
        bpy.context.space_data.transform_orientation = NP020PL.trans_orient
        bpy.context.scene.cursor_location = NP020PL.curloc

        NP020PL.flag = 'RUNTRANSF0'
        return {'FINISHED'}


# This is the actual addon process, the algorithm that defines the order of operator activation inside the main macro:

def register():

    #bpy.app.handlers.scene_update_post.append(NPPL_scene_update)

    NP020PointAlign.define('OBJECT_OT_np_pl_get_context')
    NP020PointAlign.define('OBJECT_OT_np_pl_get_selection')
    NP020PointAlign.define('OBJECT_OT_np_pl_get_mouseloc')
    NP020PointAlign.define('OBJECT_OT_np_pl_add_helper')
    NP020PointAlign.define('OBJECT_OT_np_pl_prepare_context')
    for i in range(1, 50):
        NP020PointAlign.define('OBJECT_OT_np_pl_run_translate')
    NP020PointAlign.define('OBJECT_OT_np_pl_align_selected')
    NP020PointAlign.define('OBJECT_OT_np_pl_restore_context')

def unregister():
    #bpy.app.handlers.scene_update_post.remove(NPPL_scene_update)
    pass
