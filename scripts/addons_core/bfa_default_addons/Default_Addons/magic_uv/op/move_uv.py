# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "kgeogeo, mem, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import BoolProperty
import bmesh
from mathutils import Vector

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    # Multiple objects editing mode is not supported in this feature.
    objs = common.get_uv_editable_objects(context)
    if len(objs) != 1:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


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

    bl_idname = "uv.muv_move_uv"
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

        # Creation of BMesh is high cost, so cache related objects.
        self.__cache = {}

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

    def _find_uv(self, bm, active_uv):
        topology_dict = []
        uvs = []
        for fidx, f in enumerate(bm.faces):
            for vidx, v in enumerate(f.verts):
                if v.select:
                    uvs.append(f.loops[vidx][active_uv].uv.copy())
                    topology_dict.append([fidx, vidx])

        return topology_dict, uvs

    def modal(self, _, event):
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
        obj = self.__cache["active_object"]
        bm = self.__cache["bmesh"]
        active_uv = self.__cache["active_uv"]
        for uv in self.__cache["target_uv"]:
            uv += dv
        bmesh.update_edit_mesh(obj.data)

        # check mouse preference
        confirm_btn = 'LEFTMOUSE'
        cancel_btn = 'RIGHTMOUSE'

        # cancelled
        if event.type == cancel_btn and event.value == 'PRESS':
            for (fidx, vidx), uv in zip(self.__topology_dict, self.__ini_uvs):
                bm.faces[fidx].loops[vidx][active_uv].uv = uv
            MUV_OT_MoveUV.__running = False
            self.__cache = {}
            return {'FINISHED'}
        # confirmed
        if event.type == confirm_btn and event.value == 'PRESS':
            MUV_OT_MoveUV.__running = False
            self.__cache = {}
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        MUV_OT_MoveUV.__running = True
        self.__operating = False
        self.__first_time = True

        context.window_manager.modal_handler_add(self)

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        active_uv = bm.loops.layers.uv.active
        self.__topology_dict, self.__ini_uvs = self._find_uv(bm, active_uv)

        # Optimization: Store temporary variables which cause heavy
        #               calculation.
        self.__cache["active_object"] = obj
        self.__cache["bmesh"] = bm
        self.__cache["active_uv"] = active_uv
        self.__cache["target_uv"] = []
        for fidx, vidx in self.__topology_dict:
            l = bm.faces[fidx].loops[vidx]
            self.__cache["target_uv"].append(l[active_uv].uv)

        if context.area:
            context.area.tag_redraw()

        return {'RUNNING_MODAL'}
