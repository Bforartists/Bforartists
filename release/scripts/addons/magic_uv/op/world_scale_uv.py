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

__author__ = "McBuff, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.0"
__date__ = "26 Jan 2019"

from math import sqrt

import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntVectorProperty,
    BoolProperty,
)
import bmesh
from mathutils import Vector

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


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


def _measure_wsuv_info(obj, tex_size=None):
    mesh_area = common.measure_mesh_area(obj)
    uv_area = common.measure_uv_area(obj, tex_size)

    if not uv_area:
        return None, mesh_area, None

    if mesh_area == 0.0:
        density = 0.0
    else:
        density = sqrt(uv_area) / sqrt(mesh_area)

    return uv_area, mesh_area, density


def _apply(obj, origin, factor):
    bm = bmesh.from_edit_mesh(obj.data)
    if common.check_version(2, 73, 0) >= 0:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    sel_faces = [f for f in bm.faces if f.select]

    uv_layer = bm.loops.layers.uv.verify()

    # calculate origin
    if origin == 'CENTER':
        origin = Vector((0.0, 0.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin = origin + uv
                num = num + 1
        origin = origin / num
    elif origin == 'LEFT_TOP':
        origin = Vector((100000.0, -100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = max(origin.y, uv.y)
    elif origin == 'LEFT_CENTER':
        origin = Vector((100000.0, 0.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = origin.y + uv.y
                num = num + 1
        origin.y = origin.y / num
    elif origin == 'LEFT_BOTTOM':
        origin = Vector((100000.0, 100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = min(origin.y, uv.y)
    elif origin == 'CENTER_TOP':
        origin = Vector((0.0, -100000.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = origin.x + uv.x
                origin.y = max(origin.y, uv.y)
                num = num + 1
        origin.x = origin.x / num
    elif origin == 'CENTER_BOTTOM':
        origin = Vector((0.0, 100000.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = origin.x + uv.x
                origin.y = min(origin.y, uv.y)
                num = num + 1
        origin.x = origin.x / num
    elif origin == 'RIGHT_TOP':
        origin = Vector((-100000.0, -100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = max(origin.y, uv.y)
    elif origin == 'RIGHT_CENTER':
        origin = Vector((-100000.0, 0.0))
        num = 0
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = origin.y + uv.y
                num = num + 1
        origin.y = origin.y / num
    elif origin == 'RIGHT_BOTTOM':
        origin = Vector((-100000.0, 100000.0))
        for f in sel_faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = min(origin.y, uv.y)

    # update UV coordinate
    for f in sel_faces:
        for l in f.loops:
            uv = l[uv_layer].uv
            diff = uv - origin
            l[uv_layer].uv = origin + diff * factor

    bmesh.update_edit_mesh(obj.data)


@PropertyClassRegistry()
class _Properties:
    idname = "world_scale_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_world_scale_uv_enabled = BoolProperty(
            name="World Scale UV Enabled",
            description="World Scale UV is enabled",
            default=False
        )
        scene.muv_world_scale_uv_src_mesh_area = FloatProperty(
            name="Mesh Area",
            description="Source Mesh Area",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_src_uv_area = FloatProperty(
            name="UV Area",
            description="Source UV Area",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_src_density = FloatProperty(
            name="Density",
            description="Source Texel Density",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_tgt_density = FloatProperty(
            name="Density",
            description="Target Texel Density",
            default=0.0,
            min=0.0
        )
        scene.muv_world_scale_uv_tgt_scaling_factor = FloatProperty(
            name="Scaling Factor",
            default=1.0,
            max=1000.0,
            min=0.00001
        )
        scene.muv_world_scale_uv_tgt_texture_size = IntVectorProperty(
            name="Texture Size",
            size=2,
            min=1,
            soft_max=10240,
            default=(1024, 1024),
        )
        scene.muv_world_scale_uv_mode = EnumProperty(
            name="Mode",
            description="Density calculation mode",
            items=[
                ('PROPORTIONAL_TO_MESH', "Proportional to Mesh",
                 "Apply density proportionaled by mesh size"),
                ('SCALING_DENSITY', "Scaling Density",
                 "Apply scaled density from source"),
                ('SAME_DENSITY', "Same Density",
                 "Apply same density of source"),
                ('MANUAL', "Manual", "Specify density and size by manual"),
            ],
            default='MANUAL'
        )
        scene.muv_world_scale_uv_origin = EnumProperty(
            name="Origin",
            description="Aspect Origin",
            items=[
                ('CENTER', "Center", "Center"),
                ('LEFT_TOP', "Left Top", "Left Bottom"),
                ('LEFT_CENTER', "Left Center", "Left Center"),
                ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
                ('CENTER_TOP', "Center Top", "Center Top"),
                ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
                ('RIGHT_TOP', "Right Top", "Right Top"),
                ('RIGHT_CENTER', "Right Center", "Right Center"),
                ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

            ],
            default='CENTER'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_world_scale_uv_enabled
        del scene.muv_world_scale_uv_src_mesh_area
        del scene.muv_world_scale_uv_src_uv_area
        del scene.muv_world_scale_uv_src_density
        del scene.muv_world_scale_uv_tgt_density
        del scene.muv_world_scale_uv_tgt_scaling_factor
        del scene.muv_world_scale_uv_mode
        del scene.muv_world_scale_uv_origin


@BlClassRegistry()
class MUV_OT_WorldScaleUV_Measure(bpy.types.Operator):
    """
    Operation class: Measure face size
    """

    bl_idname = "uv.muv_ot_world_scale_uv_measure"
    bl_label = "Measure World Scale UV"
    bl_description = "Measure face size for scale calculation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        sc = context.scene
        obj = context.active_object

        uv_area, mesh_area, density = _measure_wsuv_info(obj)
        if not uv_area:
            self.report({'WARNING'},
                        "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        sc.muv_world_scale_uv_src_uv_area = uv_area
        sc.muv_world_scale_uv_src_mesh_area = mesh_area
        sc.muv_world_scale_uv_src_density = density

        self.report({'INFO'},
                    "UV Area: {0}, Mesh Area: {1}, Texel Density: {2}"
                    .format(uv_area, mesh_area, density))

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_WorldScaleUV_ApplyManual(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Manual)
    """

    bl_idname = "uv.muv_ot_world_scale_uv_apply_manual"
    bl_label = "Apply World Scale UV (Manual)"
    bl_description = "Apply scaled UV based on user specification"
    bl_options = {'REGISTER', 'UNDO'}

    tgt_density = FloatProperty(
        name="Density",
        description="Target Texel Density",
        default=1.0,
        min=0.0
    )
    tgt_texture_size = IntVectorProperty(
        name="Texture Size",
        size=2,
        min=1,
        soft_max=10240,
        default=(1024, 1024),
    )
    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', "Center", "Center"),
            ('LEFT_TOP', "Left Top", "Left Bottom"),
            ('LEFT_CENTER', "Left Center", "Left Center"),
            ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
            ('CENTER_TOP', "Center Top", "Center Top"),
            ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
            ('RIGHT_TOP', "Right Top", "Right Top"),
            ('RIGHT_CENTER', "Right Center", "Right Center"),
            ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

        ],
        default='CENTER'
    )
    show_dialog = BoolProperty(
        name="Show Diaglog Menu",
        description="Show dialog menu if true",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __apply_manual(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        tex_size = self.tgt_texture_size
        uv_area, _, density = _measure_wsuv_info(obj, tex_size)
        if not uv_area:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}

        tgt_density = self.tgt_density
        factor = tgt_density / density

        _apply(context.active_object, self.origin, factor)
        self.report({'INFO'}, "Scaling factor: {0}".format(factor))

        return {'FINISHED'}

    def draw(self, _):
        layout = self.layout

        layout.prop(self, "tgt_density")
        layout.prop(self, "tgt_texture_size")
        layout.prop(self, "origin")

        layout.separator()

    def invoke(self, context, _):
        if self.show_dialog:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)

        return self.execute(context)

    def execute(self, context):
        return self.__apply_manual(context)


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_WorldScaleUV_ApplyScalingDensity(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Scaling Density)
    """

    bl_idname = "uv.muv_ot_world_scale_uv_apply_scaling_density"
    bl_label = "Apply World Scale UV (Scaling Density)"
    bl_description = "Apply scaled UV with scaling density"
    bl_options = {'REGISTER', 'UNDO'}

    tgt_scaling_factor = FloatProperty(
        name="Scaling Factor",
        default=1.0,
        max=1000.0,
        min=0.00001
    )
    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', "Center", "Center"),
            ('LEFT_TOP', "Left Top", "Left Bottom"),
            ('LEFT_CENTER', "Left Center", "Left Center"),
            ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
            ('CENTER_TOP', "Center Top", "Center Top"),
            ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
            ('RIGHT_TOP', "Right Top", "Right Top"),
            ('RIGHT_CENTER', "Right Center", "Right Center"),
            ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

        ],
        default='CENTER'
    )
    src_density = FloatProperty(
        name="Density",
        description="Source Texel Density",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    same_density = BoolProperty(
        name="Same Density",
        description="Apply same density",
        default=False,
        options={'HIDDEN'}
    )
    show_dialog = BoolProperty(
        name="Show Diaglog Menu",
        description="Show dialog menu if true",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __apply_scaling_density(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        uv_area, _, density = _measure_wsuv_info(obj)
        if not uv_area:
            self.report({'WARNING'},
                        "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        tgt_density = self.src_density * self.tgt_scaling_factor
        factor = tgt_density / density

        _apply(context.active_object, self.origin, factor)
        self.report({'INFO'}, "Scaling factor: {0}".format(factor))

        return {'FINISHED'}

    def draw(self, _):
        layout = self.layout

        layout.label(text="Source:")
        col = layout.column()
        col.prop(self, "src_density")
        col.enabled = False

        layout.separator()

        if not self.same_density:
            layout.prop(self, "tgt_scaling_factor")
        layout.prop(self, "origin")

        layout.separator()

    def invoke(self, context, _):
        sc = context.scene

        if self.show_dialog:
            wm = context.window_manager

            if self.same_density:
                self.tgt_scaling_factor = 1.0
            else:
                self.tgt_scaling_factor = \
                    sc.muv_world_scale_uv_tgt_scaling_factor
                self.src_density = sc.muv_world_scale_uv_src_density

            return wm.invoke_props_dialog(self)

        return self.execute(context)

    def execute(self, context):
        if self.same_density:
            self.tgt_scaling_factor = 1.0

        return self.__apply_scaling_density(context)


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_WorldScaleUV_ApplyProportionalToMesh(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Proportional to mesh)
    """

    bl_idname = "uv.muv_ot_world_scale_uv_apply_proportional_to_mesh"
    bl_label = "Apply World Scale UV (Proportional to mesh)"
    bl_description = "Apply scaled UV proportionaled to mesh"
    bl_options = {'REGISTER', 'UNDO'}

    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', "Center", "Center"),
            ('LEFT_TOP', "Left Top", "Left Bottom"),
            ('LEFT_CENTER', "Left Center", "Left Center"),
            ('LEFT_BOTTOM', "Left Bottom", "Left Bottom"),
            ('CENTER_TOP', "Center Top", "Center Top"),
            ('CENTER_BOTTOM', "Center Bottom", "Center Bottom"),
            ('RIGHT_TOP', "Right Top", "Right Top"),
            ('RIGHT_CENTER', "Right Center", "Right Center"),
            ('RIGHT_BOTTOM', "Right Bottom", "Right Bottom")

        ],
        default='CENTER'
    )
    src_density = FloatProperty(
        name="Source Density",
        description="Source Texel Density",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    src_uv_area = FloatProperty(
        name="Source UV Area",
        description="Source UV Area",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    src_mesh_area = FloatProperty(
        name="Source Mesh Area",
        description="Source Mesh Area",
        default=0.0,
        min=0.0,
        options={'HIDDEN'}
    )
    show_dialog = BoolProperty(
        name="Show Diaglog Menu",
        description="Show dialog menu if true",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def __apply_proportional_to_mesh(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        uv_area, mesh_area, density = _measure_wsuv_info(obj)
        if not uv_area:
            self.report({'WARNING'},
                        "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        tgt_density = self.src_density * sqrt(mesh_area) / sqrt(
            self.src_mesh_area)

        factor = tgt_density / density

        _apply(context.active_object, self.origin, factor)
        self.report({'INFO'}, "Scaling factor: {0}".format(factor))

        return {'FINISHED'}

    def draw(self, _):
        layout = self.layout

        layout.label(text="Source:")
        col = layout.column(align=True)
        col.prop(self, "src_density")
        col.prop(self, "src_uv_area")
        col.prop(self, "src_mesh_area")
        col.enabled = False

        layout.separator()
        layout.prop(self, "origin")

        layout.separator()

    def invoke(self, context, _):
        if self.show_dialog:
            wm = context.window_manager
            sc = context.scene

            self.src_density = sc.muv_world_scale_uv_src_density
            self.src_mesh_area = sc.muv_world_scale_uv_src_mesh_area

            return wm.invoke_props_dialog(self)

        return self.execute(context)

    def execute(self, context):
        return self.__apply_proportional_to_mesh(context)
