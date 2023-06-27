# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "McBuff, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

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


def _is_valid_context_for_measure(context):
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


def _is_valid_context_for_apply(context):
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


def _measure_wsuv_info(obj, calc_method='MESH',
                       tex_selection_method='FIRST', tex_size=None,
                       only_selected=True):
    mesh_areas = common.measure_mesh_area(obj, calc_method, only_selected)
    uv_areas = common.measure_uv_area(obj, calc_method, tex_selection_method,
                                      tex_size, only_selected)

    if not uv_areas:
        return None, mesh_areas, None

    if len(mesh_areas) != len(uv_areas):
        raise ValueError("mesh_area and uv_area must be same length")

    densities = []
    for mesh_area, uv_area in zip(mesh_areas, uv_areas):
        if mesh_area == 0.0:
            densities.append(0.0)
        else:
            densities.append(sqrt(uv_area) / sqrt(mesh_area))

    return uv_areas, mesh_areas, densities


def _measure_wsuv_info_from_faces(obj, bm, faces, uv_layer, tex_layer,
                                  tex_selection_method='FIRST', tex_size=None):
    mesh_area = common.measure_mesh_area_from_faces(bm, faces)
    uv_area = common.measure_uv_area_from_faces(
        obj, bm, faces, uv_layer, tex_layer, tex_selection_method, tex_size)

    if not uv_area:
        return None, mesh_area, None

    if mesh_area == 0.0:
        density = 0.0
    else:
        density = sqrt(uv_area) / sqrt(mesh_area)

    return uv_area, mesh_area, density


def _apply(faces, uv_layer, origin, factor):
    # calculate origin
    if origin == 'CENTER':
        origin = Vector((0.0, 0.0))
        num = 0
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin = origin + uv
                num = num + 1
        origin = origin / num
    elif origin == 'LEFT_TOP':
        origin = Vector((100000.0, -100000.0))
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = max(origin.y, uv.y)
    elif origin == 'LEFT_CENTER':
        origin = Vector((100000.0, 0.0))
        num = 0
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = origin.y + uv.y
                num = num + 1
        origin.y = origin.y / num
    elif origin == 'LEFT_BOTTOM':
        origin = Vector((100000.0, 100000.0))
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = min(origin.x, uv.x)
                origin.y = min(origin.y, uv.y)
    elif origin == 'CENTER_TOP':
        origin = Vector((0.0, -100000.0))
        num = 0
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = origin.x + uv.x
                origin.y = max(origin.y, uv.y)
                num = num + 1
        origin.x = origin.x / num
    elif origin == 'CENTER_BOTTOM':
        origin = Vector((0.0, 100000.0))
        num = 0
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = origin.x + uv.x
                origin.y = min(origin.y, uv.y)
                num = num + 1
        origin.x = origin.x / num
    elif origin == 'RIGHT_TOP':
        origin = Vector((-100000.0, -100000.0))
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = max(origin.y, uv.y)
    elif origin == 'RIGHT_CENTER':
        origin = Vector((-100000.0, 0.0))
        num = 0
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = origin.y + uv.y
                num = num + 1
        origin.y = origin.y / num
    elif origin == 'RIGHT_BOTTOM':
        origin = Vector((-100000.0, 100000.0))
        for f in faces:
            for l in f.loops:
                uv = l[uv_layer].uv
                origin.x = max(origin.x, uv.x)
                origin.y = min(origin.y, uv.y)

    # update UV coordinate
    for f in faces:
        for l in f.loops:
            uv = l[uv_layer].uv
            diff = uv - origin
            l[uv_layer].uv = origin + diff * factor


def _get_target_textures(_, __):
    objs = common.get_uv_editable_objects(bpy.context)
    images = []
    for obj in objs:
        images.extend(common.find_images(obj))

    items = []
    items.append(("[Average]", "[Average]", "Average of all textures"))
    items.append(("[Max]", "[Max]", "Max of all textures"))
    items.append(("[Min]", "[Min]", "Min of all textures"))
    items.extend([(img.name, img.name, "") for img in images])
    return items


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
            description="Source UV Area (Average if calculation method is UV "
                        "Island or Face)",
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
            default='CENTER',
        )
        scene.muv_world_scale_uv_measure_tgt_texture = EnumProperty(
            name="Texture",
            description="Texture to be measured",
            items=_get_target_textures
        )
        scene.muv_world_scale_uv_apply_tgt_texture = EnumProperty(
            name="Texture",
            description="Texture to be applied",
            items=_get_target_textures
        )
        scene.muv_world_scale_uv_tgt_area_calc_method = EnumProperty(
            name="Area Calculation Method",
            description="How to calculate target area",
            items=[
                ('MESH', "Mesh", "Calculate area by whole faces in mesh"),
                ('UV ISLAND', "UV Island", "Calculate area each UV islands"),
                ('FACE', "Face", "Calculate area each face")
            ],
            default='MESH'
        )
        scene.muv_world_scale_uv_measure_only_selected = BoolProperty(
            name="Only Selected",
            description="Measure with only selected faces",
            default=True,
        )
        scene.muv_world_scale_uv_apply_only_selected = BoolProperty(
            name="Only Selected",
            description="Apply to only selected faces",
            default=True,
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
        del scene.muv_world_scale_uv_measure_tgt_texture
        del scene.muv_world_scale_uv_apply_tgt_texture
        del scene.muv_world_scale_uv_tgt_area_calc_method
        del scene.muv_world_scale_uv_measure_only_selected
        del scene.muv_world_scale_uv_apply_only_selected


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_WorldScaleUV_Measure(bpy.types.Operator):
    """
    Operation class: Measure face size
    """

    bl_idname = "uv.muv_world_scale_uv_measure"
    bl_label = "Measure World Scale UV"
    bl_description = "Measure face size for scale calculation"
    bl_options = {'REGISTER', 'UNDO'}

    tgt_texture = EnumProperty(
        name="Texture",
        description="Texture to be applied",
        items=_get_target_textures
    )
    only_selected = BoolProperty(
        name="Only Selected",
        description="Measure with only selected faces",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context_for_measure(context)

    @staticmethod
    def setup_argument(ops, scene):
        try:
            ops.tgt_texture = scene.muv_world_scale_uv_measure_tgt_texture
        except TypeError:
            # Workaround for the error raised when the items of EnumProperty
            # are deleted.
            ops.tgt_texture = "[Average]"
        ops.only_selected = scene.muv_world_scale_uv_measure_only_selected

    def execute(self, context):
        sc = context.scene
        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]

        if self.tgt_texture == "[Average]":
            uv_areas, mesh_areas, densities = _measure_wsuv_info(
                obj, calc_method='MESH', tex_selection_method='AVERAGE',
                only_selected=self.only_selected)
        elif self.tgt_texture == "[Max]":
            uv_areas, mesh_areas, densities = _measure_wsuv_info(
                obj, calc_method='MESH', tex_selection_method='MAX',
                only_selected=self.only_selected)
        elif self.tgt_texture == "[Min]":
            uv_areas, mesh_areas, densities = _measure_wsuv_info(
                obj, calc_method='MESH', tex_selection_method='MIN',
                only_selected=self.only_selected)
        else:
            texture = bpy.data.images[self.tgt_texture]
            uv_areas, mesh_areas, densities = _measure_wsuv_info(
                obj, calc_method='MESH', tex_selection_method='USER_SPECIFIED',
                only_selected=self.only_selected, tex_size=texture.size)
        if not uv_areas:
            self.report({'WARNING'},
                        "Object must have more than one UV map and texture")
            return {'CANCELLED'}

        sc.muv_world_scale_uv_src_uv_area = uv_areas[0]
        sc.muv_world_scale_uv_src_mesh_area = mesh_areas[0]
        sc.muv_world_scale_uv_src_density = densities[0]

        self.report({'INFO'},
                    "UV Area: {0}, Mesh Area: {1}, Texel Density: {2}"
                    .format(uv_areas[0], mesh_areas[0], densities[0]))

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_WorldScaleUV_ApplyManual(bpy.types.Operator):
    """
    Operation class: Apply scaled UV (Manual)
    """

    bl_idname = "uv.muv_world_scale_uv_apply_manual"
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
    tgt_area_calc_method = EnumProperty(
        name="Area Calculation Method",
        description="How to calculate target area",
        items=[
            ('MESH', "Mesh", "Calculate area by whole faces in mesh"),
            ('UV ISLAND', "UV Island", "Calculate area each UV islands"),
            ('FACE', "Face", "Calculate area each face")
        ],
        default='MESH'
    )
    only_selected = BoolProperty(
        name="Only Selected",
        description="Apply to only selected faces",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context_for_apply(context)

    @staticmethod
    def setup_argument(ops, scene):
        ops.tgt_density = scene.muv_world_scale_uv_tgt_density
        ops.tgt_texture_size = scene.muv_world_scale_uv_tgt_texture_size
        ops.origin = scene.muv_world_scale_uv_origin
        ops.show_dialog = False
        ops.tgt_area_calc_method = \
            scene.muv_world_scale_uv_tgt_area_calc_method
        ops.only_selected = scene.muv_world_scale_uv_apply_only_selected

    def __apply_manual(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}
            uv_layer = bm.loops.layers.uv.verify()
            tex_layer = common.find_texture_layer(bm)
            faces_list = common.get_faces_list(
                bm, self.tgt_area_calc_method, self.only_selected)

            tex_size = self.tgt_texture_size

            factors = []
            for faces in faces_list:
                uv_area, _, density = _measure_wsuv_info_from_faces(
                    obj, bm, faces, uv_layer, tex_layer,
                    tex_selection_method='USER_SPECIFIED', tex_size=tex_size)

                if not uv_area:
                    self.report({'WARNING'},
                                "Object {} must have more than one UV map"
                                .format(obj.name))
                    return {'CANCELLED'}

                tgt_density = self.tgt_density
                factor = tgt_density / density

                _apply(faces, uv_layer, self.origin, factor)
                factors.append(factor)

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'},
                        "Scaling factor of object {}: {}"
                        .format(obj.name, factors))

        return {'FINISHED'}

    def draw(self, _):
        layout = self.layout

        layout.label(text="Target:")
        layout.prop(self, "only_selected")
        layout.prop(self, "tgt_texture_size")
        layout.prop(self, "tgt_density")
        layout.prop(self, "origin")
        layout.prop(self, "tgt_area_calc_method")

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

    bl_idname = "uv.muv_world_scale_uv_apply_scaling_density"
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
    tgt_texture = EnumProperty(
        name="Texture",
        description="Texture to be applied",
        items=_get_target_textures
    )
    tgt_area_calc_method = EnumProperty(
        name="Area Calculation Method",
        description="How to calculate target area",
        items=[
            ('MESH', "Mesh", "Calculate area by whole faces in mesh"),
            ('UV ISLAND', "UV Island", "Calculate area each UV islands"),
            ('FACE', "Face", "Calculate area each face")
        ],
        default='MESH'
    )
    only_selected = BoolProperty(
        name="Only Selected",
        description="Apply to only selected faces",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context_for_apply(context)

    @staticmethod
    def setup_argument(ops, scene):
        ops.tgt_scaling_factor = \
            scene.muv_world_scale_uv_tgt_scaling_factor
        ops.origin = scene.muv_world_scale_uv_origin
        ops.src_density = scene.muv_world_scale_uv_src_density
        ops.same_density = False
        ops.show_dialog = False
        try:
            ops.tgt_texture = scene.muv_world_scale_uv_apply_tgt_texture
        except TypeError:
            # Workaround for the error raised when the items of EnumProperty
            # are deleted.
            ops.tgt_texture = "[Average]"
        ops.tgt_area_calc_method = \
            scene.muv_world_scale_uv_tgt_area_calc_method
        ops.only_selected = scene.muv_world_scale_uv_apply_only_selected

    def __apply_scaling_density(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}
            uv_layer = bm.loops.layers.uv.verify()
            tex_layer = common.find_texture_layer(bm)
            faces_list = common.get_faces_list(
                bm, self.tgt_area_calc_method, self.only_selected)

            factors = []
            for faces in faces_list:
                if self.tgt_texture == "[Average]":
                    uv_area, _, density = _measure_wsuv_info_from_faces(
                        obj, bm, faces, uv_layer, tex_layer,
                        tex_selection_method='AVERAGE')
                elif self.tgt_texture == "[Max]":
                    uv_area, _, density = _measure_wsuv_info_from_faces(
                        obj, bm, faces, uv_layer, tex_layer,
                        tex_selection_method='MAX')
                elif self.tgt_texture == "[Min]":
                    uv_area, _, density = _measure_wsuv_info_from_faces(
                        obj, bm, faces, uv_layer, tex_layer,
                        tex_selection_method='MIN')
                else:
                    tgt_texture = bpy.data.images[self.tgt_texture]
                    uv_area, _, density = _measure_wsuv_info_from_faces(
                        obj, bm, faces, uv_layer, tex_layer,
                        tex_selection_method='USER_SPECIFIED',
                        tex_size=tgt_texture.size)

                if not uv_area:
                    self.report({'WARNING'},
                                "Object {} must have more than one UV map and "
                                "texture".format(obj.name))
                    return {'CANCELLED'}

                tgt_density = self.src_density * self.tgt_scaling_factor
                factor = tgt_density / density

                _apply(faces, uv_layer, self.origin, factor)
                factors.append(factor)

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'},
                        "Scaling factor of object {}: {}"
                        .format(obj.name, factors))

        return {'FINISHED'}

    def draw(self, _):
        layout = self.layout

        layout.label(text="Source:")
        col = layout.column()
        col.prop(self, "src_density")
        col.enabled = False

        layout.separator()

        layout.label(text="Target:")
        if not self.same_density:
            layout.prop(self, "tgt_scaling_factor")
        layout.prop(self, "only_selected")
        layout.prop(self, "tgt_texture")
        layout.prop(self, "origin")
        layout.prop(self, "tgt_area_calc_method")

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

    bl_idname = "uv.muv_world_scale_uv_apply_proportional_to_mesh"
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
    tgt_texture = EnumProperty(
        name="Texture",
        description="Texture to be applied",
        items=_get_target_textures
    )
    tgt_area_calc_method = EnumProperty(
        name="Area Calculation Method",
        description="How to calculate target area",
        items=[
            ('MESH', "Mesh", "Calculate area by whole faces in mesh"),
            ('UV ISLAND', "UV Island", "Calculate area each UV islands"),
            ('FACE', "Face", "Calculate area each face")
        ],
        default='MESH'
    )
    only_selected = BoolProperty(
        name="Only Selected",
        description="Apply to only selected faces",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context_for_apply(context)

    @staticmethod
    def setup_argument(ops, scene):
        ops.origin = scene.muv_world_scale_uv_origin
        ops.src_density = scene.muv_world_scale_uv_src_density
        ops.src_uv_area = scene.muv_world_scale_uv_src_uv_area
        ops.src_mesh_area = scene.muv_world_scale_uv_src_mesh_area
        ops.show_dialog = False
        try:
            ops.tgt_texture = scene.muv_world_scale_uv_apply_tgt_texture
        except TypeError:
            # Workaround for the error raised when the items of EnumProperty
            # are deleted.
            ops.tgt_texture = "[Average]"
        ops.tgt_area_calc_method = \
            scene.muv_world_scale_uv_tgt_area_calc_method
        ops.only_selected = scene.muv_world_scale_uv_apply_only_selected

    def __apply_proportional_to_mesh(self, context):
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

            if not bm.loops.layers.uv:
                self.report({'WARNING'},
                            "Object {} must have more than one UV map"
                            .format(obj.name))
                return {'CANCELLED'}
            uv_layer = bm.loops.layers.uv.verify()
            tex_layer = common.find_texture_layer(bm)
            faces_list = common.get_faces_list(
                bm, self.tgt_area_calc_method, self.only_selected)

            factors = []
            for faces in faces_list:
                if self.tgt_texture == "[Average]":
                    uv_area, mesh_area, density = \
                        _measure_wsuv_info_from_faces(
                            obj, bm, faces, uv_layer, tex_layer,
                            tex_selection_method='AVERAGE')
                elif self.tgt_texture == "[Max]":
                    uv_area, mesh_area, density = \
                        _measure_wsuv_info_from_faces(
                            obj, bm, faces, uv_layer, tex_layer,
                            tex_selection_method='MAX')
                elif self.tgt_texture == "[Min]":
                    uv_area, mesh_area, density = \
                        _measure_wsuv_info_from_faces(
                            obj, bm, faces, uv_layer, tex_layer,
                            tex_selection_method='MIN')
                else:
                    tgt_texture = bpy.data.images[self.tgt_texture]
                    uv_area, mesh_area, density = \
                        _measure_wsuv_info_from_faces(
                            obj, bm, faces, uv_layer, tex_layer,
                            tex_selection_method='USER_SPECIFIED',
                            tex_size=tgt_texture.size)
                if not uv_area:
                    self.report({'WARNING'},
                                "Object {} must have more than one UV map and "
                                "texture".format(obj.name))
                    return {'CANCELLED'}

                tgt_density = self.src_density * sqrt(mesh_area) / sqrt(
                    self.src_mesh_area)
                factor = tgt_density / density

                _apply(faces, uv_layer, self.origin, factor)
                factors.append(factor)

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'},
                        "Scaling factor of object {}: {}"
                        .format(obj.name, factors))

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

        layout.label(text="Target:")
        layout.prop(self, "only_selected")
        layout.prop(self, "origin")
        layout.prop(self, "tgt_area_calc_method")
        layout.prop(self, "tgt_texture")

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
