
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
    'name': 'NP 020 Shader Brush',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Transfers materials between objects in 3D view',
    'wiki_url': '',
    'category': '3D View'}


import bpy
import mathutils, bmesh, math
from math import sin, cos, tan, atan, degrees, radians, asin, acos
import bgl
import blf
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *

# Defining the first graphical set that will be shown during first phase and updated along:
def draw_callback1_px(self, context):

    # Getting the first object and face that raycast hits:
    mode = self.mode
    np_print('mode:', mode)
    region = self.region
    np_print('region', region)
    rv3d = self.rv3d
    np_print('rv3d', rv3d)
    co2d = self.co2d
    np_print('self.co2d', co2d)
    co3d = 1
    center = Vector((0,0,0))
    normal = Vector((0.0, 0.0, 1.0))
    scenecast = scene_cast(region, rv3d, co2d)
    np_print('scenecast', scenecast)
    hitob = scenecast[4]
    np_print('hitob', hitob)


    if mode == 0:
        instruct = 'paint material on object / objects'

    elif mode == 1:
        instruct = 'pick material to paint with'

    elif mode == 2:
        instruct = 'pick material to paint with'

    elif mode == 3:
        instruct = 'paint material on single face'

    elif mode == 4:
        instruct = 'paint material on object / objects'
        if hitob is not None:
            acob = bpy.context.view_layer.objects.active
            bpy.context.view_layer.objects.active = hitob
            slots = hitob.material_slots
            for i, s in enumerate(slots):
                hitob.active_material_index = i
                bpy.ops.object.material_slot_remove()
            if self.shader is not None:
                hitob.data.materials.append(self.shader)
            np_print(hitob.select)
            if hitob.select_get() is True:
                np_print('true')
                for ob in self.selob:
                    bpy.context.view_layer.objects.active = ob
                    slots = ob.material_slots
                    for i, s in enumerate(slots):
                        ob.active_material_index = i
                        bpy.ops.object.material_slot_remove()
                    if self.shader is not None:
                        ob.data.materials.append(self.shader)
            bpy.context.view_layer.objects.active = acob
            #bpy.context.scene.update()
            np_print('040')

    elif mode == 5:
        instruct = 'pick material to paint with'
        if hitob is not None:
            mat = None
            findex = scenecast[3]
            np_print('findex', findex)
            me = hitob.data
            np_print('me', me)
            bme = bmesh.new()
            bme.from_mesh(me)
            bme.faces.ensure_lookup_table()
            np_print('faces', bme.faces)
            np_print('face', bme.faces[findex])
            bmeface = bme.faces[findex]
            matindex = bmeface.material_index
            np_print('material_index', matindex)
            slots = list(hitob.material_slots)
            np_print('slots', slots)
            np_print('len slots', len(slots))
            np_print('slots',slots)
            if len(slots) == 0:
                self.shader = None
                self.shadername = 'None'
            elif slots[matindex].material is not None:
                self.shader = slots[matindex].material
                self.shadername = slots[matindex].material.name
            else:
                self.shader = None
                self.shadername = 'None'
            bpy.context.view_layer.objects.active = hitob
            hitob.active_material_index = matindex
            np_print('self.shader', self.shader)
            np_print('050')
        else:
            self.shader = None
            self.shadername = 'None'

    elif mode == 6:
        instruct = 'pick material to paint with'

    elif mode == 7:
        instruct = 'paint material on single face'
        if hitob is not None:
            acob = bpy.context.view_layer.objects.active
            bpy.context.view_layer.objects.active = hitob
            findex = scenecast[3]
            np_print('findex', findex)
            me = hitob.data
            np_print('me', me)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bme = bmesh.from_edit_mesh(me)
            bme.faces.ensure_lookup_table()
            np_print('faces', bme.faces)
            np_print('face', bme.faces[findex])
            bmeface = bme.faces[findex]
            slots = list(hitob.material_slots)
            np_print('slots', list(slots))
            m = 0
            if list(slots) == []:
                hitob.data.materials.append(None)
            slots = list(hitob.material_slots)
            for i, s in enumerate(slots):
                np_print('s', s)
                if s.name == self.shadername:
                    m = 1
                    matindex = i
                elif s.material == None and self.shader == None:
                    m = 1
                    matindex = i
            if m == 0:
                hitob.data.materials.append(self.shader)
                matindex = len(slots) - 1
            hitob.active_material_index = matindex
            bpy.context.tool_settings.mesh_select_mode = False, False, True
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bmeface.select = True
            bmesh.update_edit_mesh(me, True)
            bpy.ops.object.material_slot_assign()
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.context.view_layer.objects.active = acob


    # ON-SCREEN INSTRUCTIONS:

    keys_aff = 'LMB - paint object / objects, CTRL - take material, ALT - paint single face'
    keys_nav = 'MMB, SCROLL - navigate'
    keys_neg = 'ESC - quit'

    display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg)


    col_bg_fill_main_run = addon_settings_graph('col_bg_fill_main_run')
    col_bg_fill_main_nav = addon_settings_graph('col_bg_fill_main_nav')

    # Drawing the small icon near the cursor and the shader name:
    # First color is for lighter themes, second for default and darker themes:
    if mode in {1,2,5,6}:
        square = [[17, 30], [17, 39], [26, 39], [26, 30]]
        cur = [[17, 36], [18, 35], [14, 31], [14, 30], [15, 30], [19, 34], [18, 35], [20, 37], [21, 37], [21, 36], [19, 34], [20, 33]]
        curpipe = [[18, 35], [14, 31], [14, 30], [15, 30], [19, 34], [18, 35]]
        curcap = [[18, 35], [20, 37], [21, 37], [21, 36], [19, 34], [18, 35]]
        scale = 2.8
        col_square = col_bg_fill_main_run
        for co in square:
            co[0] = round((co[0] * scale), 0) -35 + co2d[0]
            co[1] = round((co[1] * scale), 0) -88 + co2d[1]
        for co in cur:
            co[0] = round((co[0] * scale),0) -25 + co2d[0]
            co[1] = round((co[1] * scale),0) -86 + co2d[1]
        for co in curcap:
            co[0] = round((co[0] * scale),0) -25 + co2d[0]
            co[1] = round((co[1] * scale),0) -86 + co2d[1]
        for co in curpipe:
            co[0] = round((co[0] * scale),0) -25 + co2d[0]
            co[1] = round((co[1] * scale),0) -86 + co2d[1]
        bgl.glColor4f(*col_square)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        #bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x,y in cur:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        if mode in {2, 6}:
            bgl.glColor4f(1.0, 0.5, 0.5, 1.0)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x,y in curcap:
            bgl.glVertex2f(x,y)
        bgl.glEnd()

    else:
        square = [[17, 30], [17, 39], [26, 39], [26, 30]]
        cur = [[18, 30], [21, 33], [18, 36], [14, 32], [16, 32], [18, 30]]
        curtip = [[14, 32], [16, 32], [15, 33], [14, 32]]
        curbag = [[18, 30], [15, 33], [21, 33], [18, 30]]
        scale = 2.8
        if mode in (3, 7): col_square = col_bg_fill_main_nav
        else: col_square = (0.25, 0.35, 0.4, 0.87)
        for co in square:
            co[0] = round((co[0] * scale), 0) -35 + co2d[0]
            co[1] = round((co[1] * scale), 0) -88 + co2d[1]
        for co in cur:
            co[0] = round((co[0] * scale),0) -25 + co2d[0]
            co[1] = round((co[1] * scale),0) -84 + co2d[1]
        for co in curtip:
            co[0] = round((co[0] * scale),0) -25 + co2d[0]
            co[1] = round((co[1] * scale),0) -84 + co2d[1]
        for co in curbag:
            co[0] = round((co[0] * scale),0) -25 + co2d[0]
            co[1] = round((co[1] * scale),0) -84 + co2d[1]
        bgl.glColor4f(*col_square)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()
        #bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x,y in cur:
            bgl.glVertex2f(x,y)
        bgl.glEnd()
        '''
        if mode in {3, 7}:
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for x,y in curtip:
                bgl.glVertex2f(x,y)
            bgl.glEnd()
            bgl.glLineWidth(2)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x,y in curtip:
                bgl.glVertex2f(x,y)
            bgl.glEnd()
            bgl.glLineWidth(1)
        '''
        if self.shader is not None:
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            for x,y in curbag:
                bgl.glVertex2f(x,y)
            bgl.glEnd()

    bgl.glColor4f(0.25, 0.35, 0.4, 0.87)
    font_id = 0
    blf.size(font_id, 15, 72)
    blf.position(font_id, co2d[0] + 47, co2d[1] - 3, 0)
    blf.draw(font_id, self.shadername)

    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    font_id = 0
    blf.size(font_id, 15, 72)
    blf.position(font_id, co2d[0] + 46, co2d[1] - 2, 0)
    blf.draw(font_id, self.shadername)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

# Defining the operator that will use the graphical sets and make the drawing of the base:
class NP020ShaderBrush(bpy.types.Operator):
    bl_idname = "object.np_020_shader_brush"
    bl_label = "NP 020 Shader Brush"
    bl_options={'REGISTER', 'UNDO', 'PRESET'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if not event.ctrl and not event.shift and not event.alt and event.type == 'MOUSEMOVE':
            self.mode = 0
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.type == 'MOUSEMOVE':
            self.mode = 1
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.shift and event.type == 'MOUSEMOVE':
            self.mode = 2
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.alt and event.type == 'MOUSEMOVE':
            self.mode = 3
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.value == 'PRESS':
            self.mode = 1
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.shift and event.type == 'LEFT_CTRL' and event.value == 'PRESS':
            self.mode = 2
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.value == 'RELEASE':
            self.mode = 0
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_SHIFT' and event.value == 'PRESS' and self.mode == 1:
            self.mode = 2
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.type == 'LEFT_SHIFT' and event.value == 'RELEASE':
            self.mode = 1
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_CTRL' and event.type == 'LEFT_SHIFT' and event.value == 'RELEASE':
            self.mode = 0
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_ALT' and event.value == 'PRESS':
            self.mode = 3
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFT_ALT' and event.value == 'RELEASE':
            self.mode = 0
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.mode = 4
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.mode = 5
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.shift and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.mode = 6
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.alt and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.mode = 7
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.mode = 0
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.mode = 1
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.ctrl and event.shift and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.mode = 2
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        if event.alt and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.mode = 3
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'RIGHTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            self.co2d = ((event.mouse_region_x, event.mouse_region_y))
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback1_px, args, 'WINDOW', 'POST_PIXEL')

            self.region = bpy.context.region
            self.rv3d = bpy.context.region_data

            ob = bpy.context.active_object
            if ob is not None and ob.active_material is not None:
                self.shader = ob.active_material
                self.shadername = ob.active_material.name
            else:
                self.shader = None
                self.shadername = 'None'
            self.selob = bpy.context.selected_objects

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

def register():
    pass


def unregister():
    pass
