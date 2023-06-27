# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.7"
__date__ = "9 Sep 2022"

from math import pi, cos, tan, sin

import bpy
import bmesh
from mathutils import Vector
from bpy_extras import view3d_utils
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from bpy.props import (
    BoolProperty,
    IntProperty,
    EnumProperty,
    FloatProperty,
)

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat

import gpu
from gpu_extras.batch import batch_for_shader


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


def _get_strength(p, len_, factor):
    f = factor

    if p > len_:
        return 0.0

    if p < 0.0:
        return f

    return (len_ - p) * f / len_


@PropertyClassRegistry()
class _Properties:
    idname = "uv_sculpt"

    @classmethod
    def init_props(cls, scene):
        def get_func(_):
            return MUV_OT_UVSculpt.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_uv_sculpt('INVOKE_REGION_WIN')

        scene.muv_uv_sculpt_enabled = BoolProperty(
            name="UV Sculpt",
            description="UV Sculpt is enabled",
            default=False
        )
        scene.muv_uv_sculpt_enable = BoolProperty(
            name="UV Sculpt Showed",
            description="UV Sculpt is enabled",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_uv_sculpt_radius = IntProperty(
            name="Radius",
            description="Radius of the brush",
            min=1,
            max=500,
            default=30
        )
        scene.muv_uv_sculpt_strength = FloatProperty(
            name="Strength",
            description="How powerful the effect of the brush when applied",
            min=0.0,
            max=1.0,
            default=0.03,
        )
        scene.muv_uv_sculpt_tools = EnumProperty(
            name="Tools",
            description="Select Tools for the UV sculpt brushes",
            items=[
                ('GRAB', "Grab", "Grab UVs"),
                ('RELAX', "Relax", "Relax UVs"),
                ('PINCH', "Pinch", "Pinch UVs")
            ],
            default='GRAB'
        )
        scene.muv_uv_sculpt_show_brush = BoolProperty(
            name="Show Brush",
            description="Show Brush",
            default=True
        )
        scene.muv_uv_sculpt_pinch_invert = BoolProperty(
            name="Invert",
            description="Pinch UV to invert direction",
            default=False
        )
        scene.muv_uv_sculpt_relax_method = EnumProperty(
            name="Method",
            description="Algorithm used for relaxation",
            items=[
                ('HC', "HC", "Use HC method for relaxation"),
                ('LAPLACIAN', "Laplacian",
                 "Use laplacian method for relaxation")
            ],
            default='HC'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_uv_sculpt_enabled
        del scene.muv_uv_sculpt_enable
        del scene.muv_uv_sculpt_radius
        del scene.muv_uv_sculpt_strength
        del scene.muv_uv_sculpt_tools
        del scene.muv_uv_sculpt_show_brush
        del scene.muv_uv_sculpt_pinch_invert
        del scene.muv_uv_sculpt_relax_method


def location_3d_to_region_2d_extra(region, rv3d, coord):
    coord_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, coord)
    if coord_2d is None:
        prj = rv3d.perspective_matrix @ Vector(
            (coord[0], coord[1], coord[2], 1.0))
        width_half = region.width / 2.0
        height_half = region.height / 2.0
        coord_2d = Vector((
            width_half + width_half * (prj.x / prj.w),
            height_half + height_half * (prj.y / prj.w)
        ))
    return coord_2d


@BlClassRegistry()
class MUV_OT_UVSculpt(bpy.types.Operator):
    """
    Operation class: UV Sculpt in View3D
    """

    bl_idname = "uv.muv_uv_sculpt"
    bl_label = "UV Sculpt"
    bl_description = "UV Sculpt in View3D"
    bl_options = {'REGISTER'}

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
        if not cls.__handle:
            sv = bpy.types.SpaceView3D
            cls.__handle = sv.draw_handler_add(cls.draw_brush, (obj, context),
                                               "WINDOW", "POST_PIXEL")
        if not cls.__timer:
            cls.__timer = context.window_manager.event_timer_add(
                0.1, window=context.window)
            context.window_manager.modal_handler_add(obj)

    @classmethod
    def handle_remove(cls, context):
        if cls.__handle:
            sv = bpy.types.SpaceView3D
            sv.draw_handler_remove(cls.__handle, "WINDOW")
            cls.__handle = None
        if cls.__timer:
            context.window_manager.event_timer_remove(cls.__timer)
            cls.__timer = None

    @classmethod
    def draw_brush(cls, obj, context):
        sc = context.scene
        user_prefs = compat.get_user_preferences(context)
        prefs = user_prefs.addons["magic_uv"].preferences

        num_segment = 180
        theta = 2 * pi / num_segment
        fact_t = tan(theta)
        fact_r = cos(theta)

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.bind()
        shader.uniform_float("color", prefs.uv_sculpt_brush_color)

        x = sc.muv_uv_sculpt_radius * cos(0.0)
        y = sc.muv_uv_sculpt_radius * sin(0.0)
        coords = []
        for _ in range(num_segment):
            coords.append([x + obj.current_mco.x, y + obj.current_mco.y])
            tx = -y
            ty = x
            x = x + tx * fact_t
            y = y + ty * fact_t
            x = x * fact_r
            y = y * fact_r

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        batch.draw(shader)
        del batch

    def __init__(self):
        self.__loop_info = {}       # { Object: loop_info }
        self.__stroking = False
        self.current_mco = Vector((0.0, 0.0))
        self.__initial_mco = Vector((0.0, 0.0))

    def __stroke_init(self, context, _):
        sc = context.scene

        self.__initial_mco = self.current_mco

        objs = common.get_uv_editable_objects(context)

        # get influenced UV
        self.__loop_info = {}
        for obj in objs:
            world_mat = obj.matrix_world
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            _, region, space = common.get_space('VIEW_3D', 'WINDOW', 'VIEW_3D')

            self.__loop_info[obj] = []
            for f in bm.faces:
                if not f.select:
                    continue
                for i, l in enumerate(f.loops):
                    loc_2d = location_3d_to_region_2d_extra(
                        region, space.region_3d,
                        compat.matmul(world_mat, l.vert.co))
                    diff = loc_2d - self.__initial_mco
                    if diff.length < sc.muv_uv_sculpt_radius:
                        info = {
                            "face_idx": f.index,
                            "loop_idx": i,
                            "initial_vco": l.vert.co.copy(),
                            "initial_vco_2d": loc_2d,
                            "initial_uv": l[uv_layer].uv.copy(),
                            "strength": _get_strength(
                                diff.length, sc.muv_uv_sculpt_radius,
                                sc.muv_uv_sculpt_strength)
                        }
                        self.__loop_info[obj].append(info)

    def __stroke_apply(self, context, _):
        sc = context.scene
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            world_mat = obj.matrix_world
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            mco = self.current_mco

            if sc.muv_uv_sculpt_tools == 'GRAB':
                for info in self.__loop_info[obj]:
                    diff_uv = (mco - self.__initial_mco) * info["strength"]
                    l = bm.faces[info["face_idx"]].loops[info["loop_idx"]]
                    l[uv_layer].uv = info["initial_uv"] + diff_uv / 100.0

            elif sc.muv_uv_sculpt_tools == 'PINCH':
                _, region, space = common.get_space(
                    'VIEW_3D', 'WINDOW', 'VIEW_3D')
                loop_info = []
                for f in bm.faces:
                    if not f.select:
                        continue
                    for i, l in enumerate(f.loops):
                        loc_2d = location_3d_to_region_2d_extra(
                            region, space.region_3d,
                            compat.matmul(world_mat, l.vert.co))
                        diff = loc_2d - self.__initial_mco
                        if diff.length < sc.muv_uv_sculpt_radius:
                            info = {
                                "face_idx": f.index,
                                "loop_idx": i,
                                "initial_vco": l.vert.co.copy(),
                                "initial_vco_2d": loc_2d,
                                "initial_uv": l[uv_layer].uv.copy(),
                                "strength": _get_strength(
                                    diff.length, sc.muv_uv_sculpt_radius,
                                    sc.muv_uv_sculpt_strength)
                            }
                            loop_info.append(info)

                # mouse coordinate to UV coordinate
                ray_vec = view3d_utils.region_2d_to_vector_3d(
                    region, space.region_3d, mco)
                ray_vec.normalize()
                ray_orig = view3d_utils.region_2d_to_origin_3d(
                    region, space.region_3d, mco)
                ray_tgt = ray_orig + ray_vec * 1000000.0
                mwi = world_mat.inverted()
                ray_orig_obj = compat.matmul(mwi, ray_orig)
                ray_tgt_obj = compat.matmul(mwi, ray_tgt)
                ray_dir_obj = ray_tgt_obj - ray_orig_obj
                ray_dir_obj.normalize()
                tree = BVHTree.FromBMesh(bm)
                loc, _, fidx, _ = tree.ray_cast(ray_orig_obj, ray_dir_obj)
                if not loc:
                    return
                loops = [l for l in bm.faces[fidx].loops]
                uvs = [Vector((l[uv_layer].uv.x, l[uv_layer].uv.y, 0.0))
                       for l in loops]
                target_uv = barycentric_transform(
                    loc,
                    loops[0].vert.co, loops[1].vert.co, loops[2].vert.co,
                    uvs[0], uvs[1], uvs[2])
                target_uv = Vector((target_uv.x, target_uv.y))

                # move to target UV coordinate
                for info in loop_info:
                    l = bm.faces[info["face_idx"]].loops[info["loop_idx"]]
                    if sc.muv_uv_sculpt_pinch_invert:
                        diff_uv = \
                            (l[uv_layer].uv - target_uv) * info["strength"]
                    else:
                        diff_uv = \
                            (target_uv - l[uv_layer].uv) * info["strength"]
                    l[uv_layer].uv = l[uv_layer].uv + diff_uv / 10.0

            elif sc.muv_uv_sculpt_tools == 'RELAX':
                _, region, space = common.get_space(
                    'VIEW_3D', 'WINDOW', 'VIEW_3D')

                # get vertex and loop relation
                vert_db = {}
                for f in bm.faces:
                    for l in f.loops:
                        if l.vert in vert_db:
                            vert_db[l.vert]["loops"].append(l)
                        else:
                            vert_db[l.vert] = {"loops": [l]}

                # get relaxation information
                for k in vert_db.keys():
                    d = vert_db[k]
                    d["uv_sum"] = Vector((0.0, 0.0))
                    d["uv_count"] = 0

                    for l in d["loops"]:
                        ln = l.link_loop_next
                        lp = l.link_loop_prev
                        d["uv_sum"] = d["uv_sum"] + ln[uv_layer].uv
                        d["uv_sum"] = d["uv_sum"] + lp[uv_layer].uv
                        d["uv_count"] = d["uv_count"] + 2
                    d["uv_p"] = d["uv_sum"] / d["uv_count"]
                    d["uv_b"] = d["uv_p"] - d["loops"][0][uv_layer].uv
                for k in vert_db.keys():
                    d = vert_db[k]
                    d["uv_sum_b"] = Vector((0.0, 0.0))
                    for l in d["loops"]:
                        ln = l.link_loop_next
                        lp = l.link_loop_prev
                        dn = vert_db[ln.vert]
                        dp = vert_db[lp.vert]
                        d["uv_sum_b"] = d["uv_sum_b"] + dn["uv_b"] + dp["uv_b"]

                # apply
                for f in bm.faces:
                    if not f.select:
                        continue
                    for i, l in enumerate(f.loops):
                        loc_2d = location_3d_to_region_2d_extra(
                            region, space.region_3d,
                            compat.matmul(world_mat, l.vert.co))
                        diff = loc_2d - self.__initial_mco
                        if diff.length >= sc.muv_uv_sculpt_radius:
                            continue
                        db = vert_db[l.vert]
                        strength = _get_strength(diff.length,
                                                 sc.muv_uv_sculpt_radius,
                                                 sc.muv_uv_sculpt_strength)

                        base = (1.0 - strength) * l[uv_layer].uv
                        if sc.muv_uv_sculpt_relax_method == 'HC':
                            t = 0.5 * \
                                (db["uv_b"] + db["uv_sum_b"] / d["uv_count"])
                            diff = strength * (db["uv_p"] - t)
                            target_uv = base + diff
                        elif sc.muv_uv_sculpt_relax_method == 'LAPLACIAN':
                            diff = strength * db["uv_p"]
                            target_uv = base + diff
                        else:
                            continue

                        l[uv_layer].uv = target_uv

            bmesh.update_edit_mesh(obj.data)

    def __stroke_exit(self, context, _):
        sc = context.scene
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            mco = self.current_mco

            if sc.muv_uv_sculpt_tools == 'GRAB':
                for info in self.__loop_info[obj]:
                    diff_uv = (mco - self.__initial_mco) * info["strength"]
                    l = bm.faces[info["face_idx"]].loops[info["loop_idx"]]
                    l[uv_layer].uv = info["initial_uv"] + diff_uv / 100.0

            bmesh.update_edit_mesh(obj.data)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if not MUV_OT_UVSculpt.is_running(context):
            MUV_OT_UVSculpt.handle_remove(context)
            return {'FINISHED'}

        self.current_mco = Vector((event.mouse_region_x, event.mouse_region_y))

        region_types = [
            'HEADER',
            'UI',
            'TOOLS',
            'TOOL_PROPS',
        ]
        if not common.mouse_on_area(event, 'VIEW_3D') or \
           common.mouse_on_regions(event, 'VIEW_3D', region_types):
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                if not self.__stroking:
                    self.__stroke_init(context, event)
                self.__stroking = True
            elif event.value == 'RELEASE':
                if self.__stroking:
                    self.__stroke_exit(context, event)
                self.__stroking = False
            return {'RUNNING_MODAL'}
        elif event.type == 'MOUSEMOVE':
            if self.__stroking:
                self.__stroke_apply(context, event)
            return {'RUNNING_MODAL'}
        elif event.type == 'TIMER':
            if self.__stroking:
                self.__stroke_apply(context, event)
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, _):
        if context.area:
            context.area.tag_redraw()

        if MUV_OT_UVSculpt.is_running(context):
            MUV_OT_UVSculpt.handle_remove(context)
        else:
            MUV_OT_UVSculpt.handle_add(self, context)

        return {'RUNNING_MODAL'}
