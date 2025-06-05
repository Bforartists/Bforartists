# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.7"
__date__ = "9 Sep 2022"

from enum import IntEnum
import math

import bpy
import mathutils
import bmesh
from bpy.props import BoolProperty, EnumProperty

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat

import gpu
from gpu_extras.batch import batch_for_shader


MAX_VALUE = 100000.0


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "uv_bounding_box"

    @classmethod
    def init_props(cls, scene):
        class Props():
            uv_info_ini = []
            ctrl_points_ini = []
            ctrl_points = []

        scene.muv_props.uv_bounding_box = Props()

        def get_func(_):
            return MUV_OT_UVBoundingBox.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_uv_bounding_box('INVOKE_REGION_WIN')

        scene.muv_uv_bounding_box_enabled = BoolProperty(
            name="UV Bounding Box Enabled",
            description="UV Bounding Box is enabled",
            default=False
        )
        scene.muv_uv_bounding_box_show = BoolProperty(
            name="UV Bounding Box Showed",
            description="UV Bounding Box is showed",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_uv_bounding_box_uniform_scaling = BoolProperty(
            name="Uniform Scaling",
            description="Enable Uniform Scaling",
            default=False
        )
        scene.muv_uv_bounding_box_boundary = EnumProperty(
            name="Boundary",
            description="Boundary",
            default='UV_SEL',
            items=[
                ('UV', "UV", "Boundary is decided by UV"),
                ('UV_SEL', "UV (Selected)",
                 "Boundary is decided by Selected UV")
            ]
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.uv_bounding_box
        del scene.muv_uv_bounding_box_enabled
        del scene.muv_uv_bounding_box_show
        del scene.muv_uv_bounding_box_uniform_scaling
        del scene.muv_uv_bounding_box_boundary


class CommandBase:
    """
    Custom class: Base class of command
    """

    def __init__(self):
        self.op = 'NONE'        # operation

    def to_matrix(self):
        # mat = I
        mat = mathutils.Matrix()
        mat.identity()
        return mat


class TranslationCommand(CommandBase):
    """
    Custom class: Translation operation
    """

    def __init__(self, ix, iy):
        super().__init__()
        self.op = 'TRANSLATION'
        self.__x = ix       # current x
        self.__y = iy       # current y
        self.__ix = ix      # initial x
        self.__iy = iy      # initial y

    def to_matrix(self):
        # mat = Mt
        dx = self.__x - self.__ix
        dy = self.__y - self.__iy
        return mathutils.Matrix.Translation((dx, dy, 0))

    def set(self, x, y):
        self.__x = x
        self.__y = y


class RotationCommand(CommandBase):
    """
    Custom class: Rotation operation
    """

    def __init__(self, ix, iy, cx, cy):
        super().__init__()
        self.op = 'ROTATION'
        self.__x = ix       # current x
        self.__y = iy       # current y
        self.__cx = cx      # center of rotation x
        self.__cy = cy      # center of rotation y
        dx = self.__x - self.__cx
        dy = self.__y - self.__cy
        self.__iangle = math.atan2(dy, dx)      # initial rotation angle

    def to_matrix(self):
        # mat = Mt * Mr * Mt^-1
        dx = self.__x - self.__cx
        dy = self.__y - self.__cy
        angle = math.atan2(dy, dx) - self.__iangle
        mti = mathutils.Matrix.Translation((-self.__cx, -self.__cy, 0.0))
        mr = mathutils.Matrix.Rotation(angle, 4, 'Z')
        mt = mathutils.Matrix.Translation((self.__cx, self.__cy, 0.0))
        return compat.matmul(compat.matmul(mt, mr), mti)

    def set(self, x, y):
        self.__x = x
        self.__y = y


class ScalingCommand(CommandBase):
    """
    Custom class: Scaling operation
    """

    def __init__(self, ix, iy, ox, oy, dir_x, dir_y, mat):
        super().__init__()
        self.op = 'SCALING'
        self.__ix = ix          # initial x
        self.__iy = iy          # initial y
        self.__x = ix           # current x
        self.__y = iy           # current y
        self.__ox = ox          # origin of scaling x
        self.__oy = oy          # origin of scaling y
        self.__dir_x = dir_x    # direction of scaling x
        self.__dir_y = dir_y    # direction of scaling y
        self.__mat = mat
        # initial origin of scaling = M(to original transform) * (ox, oy)
        iov = compat.matmul(mat, mathutils.Vector((ox, oy, 0.0)))
        self.__iox = iov.x      # initial origin of scaling X
        self.__ioy = iov.y      # initial origin of scaling y

    def to_matrix(self):
        """
        mat = M(to original transform)^-1 * Mt(to origin) * Ms *
              Mt(to origin)^-1 * M(to original transform)
        """
        m = self.__mat
        mi = self.__mat.inverted()
        mtoi = mathutils.Matrix.Translation((-self.__iox, -self.__ioy, 0.0))
        mto = mathutils.Matrix.Translation((self.__iox, self.__ioy, 0.0))
        # every point must be transformed to origin
        t = compat.matmul(m, mathutils.Vector((self.__ix, self.__iy, 0.0)))
        tix, tiy = t.x, t.y
        t = compat.matmul(m, mathutils.Vector((self.__ox, self.__oy, 0.0)))
        tox, toy = t.x, t.y
        t = compat.matmul(m, mathutils.Vector((self.__x, self.__y, 0.0)))
        tx, ty = t.x, t.y
        ms = mathutils.Matrix()
        ms.identity()
        if self.__dir_x == 1:
            ms[0][0] = (tx - tox) * self.__dir_x / (tix - tox)
        if self.__dir_y == 1:
            ms[1][1] = (ty - toy) * self.__dir_y / (tiy - toy)
        return compat.matmul(compat.matmul(compat.matmul(
            compat.matmul(mi, mto), ms), mtoi), m)

    def set(self, x, y):
        self.__x = x
        self.__y = y


class UniformScalingCommand(CommandBase):
    """
    Custom class: Uniform Scaling operation
    """

    def __init__(self, ix, iy, ox, oy, mat):
        super().__init__()
        self.op = 'SCALING'
        self.__ix = ix          # initial x
        self.__iy = iy          # initial y
        self.__x = ix           # current x
        self.__y = iy           # current y
        self.__ox = ox          # origin of scaling x
        self.__oy = oy          # origin of scaling y
        self.__mat = mat
        # initial origin of scaling = M(to original transform) * (ox, oy)
        iov = compat.matmul(mat, mathutils.Vector((ox, oy, 0.0)))
        self.__iox = iov.x      # initial origin of scaling x
        self.__ioy = iov.y      # initial origin of scaling y
        self.__dir_x = 1
        self.__dir_y = 1

    def to_matrix(self):
        """
        mat = M(to original transform)^-1 * Mt(to origin) * Ms *
              Mt(to origin)^-1 * M(to original transform)
        """
        m = self.__mat
        mi = self.__mat.inverted()
        mtoi = mathutils.Matrix.Translation((-self.__iox, -self.__ioy, 0.0))
        mto = mathutils.Matrix.Translation((self.__iox, self.__ioy, 0.0))
        # every point must be transformed to origin
        t = compat.matmul(m, mathutils.Vector((self.__ix, self.__iy, 0.0)))
        tix, tiy = t.x, t.y
        t = compat.matmul(m, mathutils.Vector((self.__ox, self.__oy, 0.0)))
        tox, toy = t.x, t.y
        t = compat.matmul(m, mathutils.Vector((self.__x, self.__y, 0.0)))
        tx, ty = t.x, t.y
        ms = mathutils.Matrix()
        ms.identity()
        tir = math.sqrt((tix - tox) * (tix - tox) + (tiy - toy) * (tiy - toy))
        tr = math.sqrt((tx - tox) * (tx - tox) + (ty - toy) * (ty - toy))

        sr = tr / tir

        if ((tx - tox) * (tix - tox)) > 0:
            self.__dir_x = 1
        else:
            self.__dir_x = -1
        if ((ty - toy) * (tiy - toy)) > 0:
            self.__dir_y = 1
        else:
            self.__dir_y = -1

        ms[0][0] = sr * self.__dir_x
        ms[1][1] = sr * self.__dir_y

        return compat.matmul(compat.matmul(compat.matmul(
            compat.matmul(mi, mto), ms), mtoi), m)

    def set(self, x, y):
        self.__x = x
        self.__y = y


class CommandExecuter:
    """
    Custom class: manage command history and execute command
    """

    def __init__(self):
        self.__cmd_list = []        # history
        self.__cmd_list_redo = []   # redo list

    def execute(self, begin=0, end=-1):
        """
        create matrix from history
        """
        mat = mathutils.Matrix()
        mat.identity()
        for i, cmd in enumerate(self.__cmd_list):
            if begin <= i and (end == -1 or i <= end):
                mat = compat.matmul(cmd.to_matrix(), mat)
        return mat

    def undo_size(self):
        """
        get history size
        """
        return len(self.__cmd_list)

    def top(self):
        """
        get top of history
        """
        if len(self.__cmd_list) <= 0:
            return None
        return self.__cmd_list[-1]

    def append(self, cmd):
        """
        append command
        """
        self.__cmd_list.append(cmd)
        self.__cmd_list_redo = []

    def undo(self):
        """
        undo command
        """
        if len(self.__cmd_list) <= 0:
            return
        self.__cmd_list_redo.append(self.__cmd_list.pop())

    def redo(self):
        """
        redo command
        """
        if len(self.__cmd_list_redo) <= 0:
            return
        self.__cmd_list.append(self.__cmd_list_redo.pop())

    def pop(self):
        if len(self.__cmd_list) <= 0:
            return None
        return self.__cmd_list.pop()

    def push(self, cmd):
        self.__cmd_list.append(cmd)


class State(IntEnum):
    """
    Enum: State definition used by MUV_UVBBStateMgr
    """
    NONE = 0
    TRANSLATING = 1
    SCALING_1 = 2
    SCALING_2 = 3
    SCALING_3 = 4
    SCALING_4 = 5
    SCALING_5 = 6
    SCALING_6 = 7
    SCALING_7 = 8
    SCALING_8 = 9
    ROTATING = 10
    UNIFORM_SCALING_1 = 11
    UNIFORM_SCALING_2 = 12
    UNIFORM_SCALING_3 = 13
    UNIFORM_SCALING_4 = 14


class StateBase:
    """
    Custom class: Base class of state
    """

    def __init__(self):
        pass

    def update(self, context, event, ctrl_points, mouse_view):
        raise NotImplementedError


class StateNone(StateBase):
    """
    Custom class:
    No state
    Wait for event from mouse
    """

    def __init__(self, cmd_exec):
        super().__init__()
        self.__cmd_exec = cmd_exec

    def update(self, context, event, ctrl_points, mouse_view):
        """
        Update state
        """
        user_prefs = compat.get_user_preferences(context)
        prefs = user_prefs.addons["magic_uv"].preferences
        cp_react_size = prefs.uv_bounding_box_cp_react_size
        is_uscaling = context.scene.muv_uv_bounding_box_uniform_scaling
        if (event.type == 'LEFTMOUSE') and (event.value == 'PRESS'):
            x, y = context.region.view2d.view_to_region(
                mouse_view.x, mouse_view.y)
            for i, p in enumerate(ctrl_points):
                px, py = context.region.view2d.view_to_region(p.x, p.y)
                in_cp_x = px - cp_react_size < x < px + cp_react_size
                in_cp_y = py - cp_react_size < y < py + cp_react_size
                if in_cp_x and in_cp_y:
                    if is_uscaling:
                        arr = [1, 3, 6, 8]
                        if i in arr:
                            return (
                                State.UNIFORM_SCALING_1 +
                                arr.index(i)
                            )
                    else:
                        return State.TRANSLATING + i

        return State.NONE


class StateTranslating(StateBase):
    """
    Custom class: Translating state
    """

    def __init__(self, cmd_exec, ctrl_points):
        super().__init__()
        self.__cmd_exec = cmd_exec
        ix, iy = ctrl_points[0].x, ctrl_points[0].y
        self.__cmd_exec.append(TranslationCommand(ix, iy))

    def update(self, context, event, ctrl_points, mouse_view):
        if event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                return State.NONE
        if event.type == 'MOUSEMOVE':
            x, y = mouse_view.x, mouse_view.y
            self.__cmd_exec.top().set(x, y)
        return State.TRANSLATING


class StateScaling(StateBase):
    """
    Custom class: Scaling state
    """

    def __init__(self, cmd_exec, state, ctrl_points):
        super().__init__()
        self.__state = state
        self.__cmd_exec = cmd_exec
        dir_x_list = [1, 1, 1, 0, 0, 1, 1, 1]
        dir_y_list = [1, 0, 1, 1, 1, 1, 0, 1]
        idx = state - 2
        ix, iy = ctrl_points[idx + 1].x, ctrl_points[idx + 1].y
        ox, oy = ctrl_points[8 - idx].x, ctrl_points[8 - idx].y
        dir_x, dir_y = dir_x_list[idx], dir_y_list[idx]
        mat = self.__cmd_exec.execute(end=self.__cmd_exec.undo_size())
        self.__cmd_exec.append(
            ScalingCommand(ix, iy, ox, oy, dir_x, dir_y, mat.inverted()))

    def update(self, context, event, ctrl_points, mouse_view):
        if event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                return State.NONE
        if event.type == 'MOUSEMOVE':
            x, y = mouse_view.x, mouse_view.y
            self.__cmd_exec.top().set(x, y)
        return self.__state


class StateUniformScaling(StateBase):
    """
    Custom class: Uniform Scaling state
    """

    def __init__(self, cmd_exec, state, ctrl_points):
        super().__init__()
        self.__state = state
        self.__cmd_exec = cmd_exec
        icp_idx = [1, 3, 6, 8]
        ocp_idx = [8, 6, 3, 1]
        idx = state - State.UNIFORM_SCALING_1
        ix, iy = ctrl_points[icp_idx[idx]].x, ctrl_points[icp_idx[idx]].y
        ox, oy = ctrl_points[ocp_idx[idx]].x, ctrl_points[ocp_idx[idx]].y
        mat = self.__cmd_exec.execute(end=self.__cmd_exec.undo_size())
        self.__cmd_exec.append(UniformScalingCommand(
            ix, iy, ox, oy, mat.inverted()))

    def update(self, context, event, ctrl_points, mouse_view):
        if event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                return State.NONE
        if event.type == 'MOUSEMOVE':
            x, y = mouse_view.x, mouse_view.y
            self.__cmd_exec.top().set(x, y)

        return self.__state


class StateRotating(StateBase):
    """
    Custom class: Rotating state
    """

    def __init__(self, cmd_exec, ctrl_points):
        super().__init__()
        self.__cmd_exec = cmd_exec
        ix, iy = ctrl_points[9].x, ctrl_points[9].y
        ox, oy = ctrl_points[0].x, ctrl_points[0].y
        self.__cmd_exec.append(RotationCommand(ix, iy, ox, oy))

    def update(self, context, event, ctrl_points, mouse_view):
        if event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                return State.NONE
        if event.type == 'MOUSEMOVE':
            x, y = mouse_view.x, mouse_view.y
            self.__cmd_exec.top().set(x, y)
        return State.ROTATING


class StateManager:
    """
    Custom class: Manage state about this feature
    """

    def __init__(self, cmd_exec):
        self.__cmd_exec = cmd_exec          # command executer
        self.__state = State.NONE   # current state
        self.__state_obj = StateNone(self.__cmd_exec)

    def __update_state(self, next_state, ctrl_points):
        """
        Update state
        """

        if next_state == self.__state:
            return
        obj = None
        if next_state == State.TRANSLATING:
            obj = StateTranslating(self.__cmd_exec, ctrl_points)
        elif State.SCALING_1 <= next_state <= State.SCALING_8:
            obj = StateScaling(
                self.__cmd_exec, next_state, ctrl_points)
        elif next_state == State.ROTATING:
            obj = StateRotating(self.__cmd_exec, ctrl_points)
        elif next_state == State.NONE:
            obj = StateNone(self.__cmd_exec)
        elif (State.UNIFORM_SCALING_1 <= next_state <=
              State.UNIFORM_SCALING_4):
            obj = StateUniformScaling(
                self.__cmd_exec, next_state, ctrl_points)

        if obj is not None:
            self.__state_obj = obj

        self.__state = next_state

    def update(self, context, ctrl_points, event):
        mouse_region = mathutils.Vector((
            event.mouse_region_x, event.mouse_region_y))
        mouse_view = mathutils.Vector((context.region.view2d.region_to_view(
            mouse_region.x, mouse_region.y)))
        next_state = self.__state_obj.update(
            context, event, ctrl_points, mouse_view)
        self.__update_state(next_state, ctrl_points)

        return self.__state


@BlClassRegistry()
class MUV_OT_UVBoundingBox(bpy.types.Operator):
    """
    Operation class: UV Bounding Box
    """

    bl_idname = "uv.muv_uv_bounding_box"
    bl_label = "UV Bounding Box"
    bl_description = "Internal operation for UV Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.__timer = None
        self.__cmd_exec = CommandExecuter()         # Command executor
        self.__state_mgr = StateManager(self.__cmd_exec)   # State Manager

    __handle = None
    __timer = None

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return False
        return _is_valid_context(context)

    @classmethod
    def is_running(cls, _):
        return 1 if cls.__handle else 0

    @classmethod
    def handle_add(cls, obj, context):
        if cls.__handle is None:
            sie = bpy.types.SpaceImageEditor
            cls.__handle = sie.draw_handler_add(
                cls.draw_bb, (obj, context), "WINDOW", "POST_PIXEL")
        if cls.__timer is None:
            cls.__timer = context.window_manager.event_timer_add(
                0.1, window=context.window)
            context.window_manager.modal_handler_add(obj)

    @classmethod
    def handle_remove(cls, context):
        if cls.__handle is not None:
            sie = bpy.types.SpaceImageEditor
            sie.draw_handler_remove(cls.__handle, "WINDOW")
            cls.__handle = None
        if cls.__timer is not None:
            context.window_manager.event_timer_remove(cls.__timer)
            cls.__timer = None

    @classmethod
    def draw_bb(cls, _, context):
        """
        Draw bounding box
        """
        props = context.scene.muv_props.uv_bounding_box

        if not MUV_OT_UVBoundingBox.is_running(context):
            return

        if not _is_valid_context(context):
            return

        user_prefs = compat.get_user_preferences(context)
        prefs = user_prefs.addons["magic_uv"].preferences
        cp_size = prefs.uv_bounding_box_cp_size

        gpu.state.program_point_size_set(False)
        gpu.state.point_size_set(cp_size)
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 1.0))

        points = [mathutils.Vector(context.region.view2d.view_to_region(cp.x, cp.y)) for cp in props.ctrl_points]
        batch = batch_for_shader(shader, 'POINTS', {"pos": points})
        batch.draw(shader)
        del batch

    def __get_uv_info(self, context):
        """
        Get UV coordinate
        """
        sc = context.scene
        objs = common.get_uv_editable_objects(context)
        uv_info = []

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            if not bm.loops.layers.uv:
                continue
            uv_layer = bm.loops.layers.uv.verify()
            for f in bm.faces:
                if not f.select:
                    continue
                for i, l in enumerate(f.loops):
                    if sc.muv_uv_bounding_box_boundary == 'UV_SEL':
                        if l[uv_layer].select:
                            uv_info.append({
                                "bmesh": bm,
                                "fidx": f.index,
                                "lidx": i,
                                "uv": l[uv_layer].uv.copy()
                            })
                    elif sc.muv_uv_bounding_box_boundary == 'UV':
                        uv_info.append({
                            "bmesh": bm,
                            "fidx": f.index,
                            "lidx": i,
                            "uv": l[uv_layer].uv.copy()
                        })
        if not uv_info:
            return None
        return uv_info

    def __get_ctrl_point(self, uv_info_ini):
        """
        Get control point
        """
        left = MAX_VALUE
        right = -MAX_VALUE
        top = -MAX_VALUE
        bottom = MAX_VALUE

        for info in uv_info_ini:
            uv = info["uv"]
            if uv.x < left:
                left = uv.x
            if uv.x > right:
                right = uv.x
            if uv.y < bottom:
                bottom = uv.y
            if uv.y > top:
                top = uv.y

        points = [
            mathutils.Vector((
                (left + right) * 0.5, (top + bottom) * 0.5, 0.0
            )),
            mathutils.Vector((left, top, 0.0)),
            mathutils.Vector((left, (top + bottom) * 0.5, 0.0)),
            mathutils.Vector((left, bottom, 0.0)),
            mathutils.Vector(((left + right) * 0.5, top, 0.0)),
            mathutils.Vector(((left + right) * 0.5, bottom, 0.0)),
            mathutils.Vector((right, top, 0.0)),
            mathutils.Vector((right, (top + bottom) * 0.5, 0.0)),
            mathutils.Vector((right, bottom, 0.0)),
            mathutils.Vector(((left + right) * 0.5, top + 0.03, 0.0))
        ]

        return points

    def __update_uvs(self, context, uv_info_ini, trans_mat):
        """
        Update UV coordinate
        """

        for info in uv_info_ini:
            bm = info["bmesh"]
            uv_layer = bm.loops.layers.uv.verify()
            fidx = info["fidx"]
            lidx = info["lidx"]
            uv = info["uv"]
            v = mathutils.Vector((uv.x, uv.y, 0.0))
            av = compat.matmul(trans_mat, v)
            bm.faces[fidx].loops[lidx][uv_layer].uv = mathutils.Vector(
                (av.x, av.y))

        objs = common.get_uv_editable_objects(context)
        for obj in objs:
            bmesh.update_edit_mesh(obj.data)

    def __update_ctrl_point(self, ctrl_points_ini, trans_mat):
        """
        Update control point
        """
        return [compat.matmul(trans_mat, cp) for cp in ctrl_points_ini]

    def modal(self, context, event):
        props = context.scene.muv_props.uv_bounding_box
        common.redraw_all_areas()

        if not MUV_OT_UVBoundingBox.is_running(context):
            return {'FINISHED'}

        if not _is_valid_context(context):
            MUV_OT_UVBoundingBox.handle_remove(context)
            return {'FINISHED'}

        region_types = [
            'HEADER',
            'UI',
            'TOOLS',
        ]
        if not common.mouse_on_area(event, 'IMAGE_EDITOR') or \
           common.mouse_on_regions(event, 'IMAGE_EDITOR', region_types):
            return {'PASS_THROUGH'}

        if event.type == 'TIMER':
            trans_mat = self.__cmd_exec.execute()
            self.__update_uvs(context, props.uv_info_ini, trans_mat)
            props.ctrl_points = self.__update_ctrl_point(
                props.ctrl_points_ini, trans_mat)

        state = self.__state_mgr.update(context, props.ctrl_points, event)
        if state == State.NONE:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, _):
        props = context.scene.muv_props.uv_bounding_box

        if MUV_OT_UVBoundingBox.is_running(context):
            MUV_OT_UVBoundingBox.handle_remove(context)
            return {'FINISHED'}

        props.uv_info_ini = self.__get_uv_info(context)
        if props.uv_info_ini is None:
            return {'CANCELLED'}

        MUV_OT_UVBoundingBox.handle_add(self, context)

        props.ctrl_points_ini = self.__get_ctrl_point(props.uv_info_ini)
        trans_mat = self.__cmd_exec.execute()
        # Update is needed in order to display control point
        self.__update_uvs(context, props.uv_info_ini, trans_mat)
        props.ctrl_points = self.__update_ctrl_point(
            props.ctrl_points_ini, trans_mat)

        return {'RUNNING_MODAL'}
