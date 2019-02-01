# <pep8-80 compliant>

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

__author__ = "kgeogeo, mem, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy
from bpy.props import BoolProperty
import bmesh
from mathutils import Vector

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry


def _is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True


def _find_uv(context):
    bm = bmesh.from_edit_mesh(context.object.data)
    topology_dict = []
    uvs = []
    active_uv = bm.loops.layers.uv.active
    for fidx, f in enumerate(bm.faces):
        for vidx, v in enumerate(f.verts):
            if v.select:
                uvs.append(f.loops[vidx][active_uv].uv.copy())
                topology_dict.append([fidx, vidx])

    return topology_dict, uvs


@PropertyClassRegistry()
class _Properties:
    idname = "move_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_move_uv_enabled = BoolProperty(
            name="Move UV Enabled",
            description="Move UV is enabled",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_move_uv_enabled


@BlClassRegistry()
class MUV_OT_MoveUV(bpy.types.Operator):
    """
    Operator class: Move UV
    """

    bl_idname = "uv.muv_ot_move_uv"
    bl_label = "Move UV"
    bl_options = {'REGISTER', 'UNDO'}

    __running = False

    def __init__(self):
        self.__topology_dict = []
        self.__prev_mouse = Vector((0.0, 0.0))
        self.__offset_uv = Vector((0.0, 0.0))
        self.__prev_offset_uv = Vector((0.0, 0.0))
        self.__first_time = True
        self.__ini_uvs = []
        self.__operating = False

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return False
        if cls.is_running(context):
            return False
        return _is_valid_context(context)

    @classmethod
    def is_running(cls, _):
        return cls.__running

    def modal(self, context, event):
        if self.__first_time is True:
            self.__prev_mouse = Vector((
                event.mouse_region_x, event.mouse_region_y))
            self.__first_time = False
            return {'RUNNING_MODAL'}

        # move UV
        div = 10000
        self.__offset_uv += Vector((
            (event.mouse_region_x - self.__prev_mouse.x) / div,
            (event.mouse_region_y - self.__prev_mouse.y) / div))
        ouv = self.__offset_uv
        pouv = self.__prev_offset_uv
        vec = Vector((ouv.x - ouv.y, ouv.x + ouv.y))
        dv = vec - pouv
        self.__prev_offset_uv = vec
        self.__prev_mouse = Vector((
            event.mouse_region_x, event.mouse_region_y))

        # check if operation is started
        if not self.__operating:
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.__operating = True
            return {'RUNNING_MODAL'}

        # update UV
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        active_uv = bm.loops.layers.uv.active
        for fidx, vidx in self.__topology_dict:
            l = bm.faces[fidx].loops[vidx]
            l[active_uv].uv = l[active_uv].uv + dv
        bmesh.update_edit_mesh(obj.data)

        # check mouse preference
        confirm_btn = 'LEFTMOUSE'
        cancel_btn = 'RIGHTMOUSE'

        # cancelled
        if event.type == cancel_btn and event.value == 'PRESS':
            for (fidx, vidx), uv in zip(self.__topology_dict, self.__ini_uvs):
                bm.faces[fidx].loops[vidx][active_uv].uv = uv
            MUV_OT_MoveUV.__running = False
            return {'FINISHED'}
        # confirmed
        if event.type == confirm_btn and event.value == 'PRESS':
            MUV_OT_MoveUV.__running = False
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        MUV_OT_MoveUV.__running = True
        self.__operating = False
        self.__first_time = True

        context.window_manager.modal_handler_add(self)
        self.__topology_dict, self.__ini_uvs = _find_uv(context)

        if context.area:
            context.area.tag_redraw()

        return {'RUNNING_MODAL'}
