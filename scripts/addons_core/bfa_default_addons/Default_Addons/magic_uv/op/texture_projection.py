# SPDX-FileCopyrightText: 2017-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.7"
__date__ = "9 Sep 2022"

from collections import namedtuple
from math import sin, cos

import bpy
import bmesh
from bpy_extras import view3d_utils
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
)
import mathutils

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat

import gpu
from gpu_extras.batch import batch_for_shader

_Rect = namedtuple('Rect', 'x0 y0 x1 y1')
_Rect2 = namedtuple('Rect2', 'x y width height')


def _get_loaded_texture_name(_, __):
    items = [(key, key, "") for key in bpy.data.images.keys()]
    items.append(("None", "None", ""))
    return items


def _get_canvas(context):
    """
    Get canvas to be renderred texture
    """
    sc = context.scene
    user_prefs = compat.get_user_preferences(context)
    prefs = user_prefs.addons["magic_uv"].preferences

    region_w = context.region.width
    region_h = context.region.height
    canvas_w = region_w - prefs.texture_projection_canvas_padding[0] * 2.0
    canvas_h = region_h - prefs.texture_projection_canvas_padding[1] * 2.0

    img = bpy.data.images[sc.muv_texture_projection_tex_image]
    tex_w = img.size[0]
    tex_h = img.size[1]

    center_x = region_w * 0.5
    center_y = region_h * 0.5

    if sc.muv_texture_projection_adjust_window:
        ratio_x = canvas_w / tex_w
        ratio_y = canvas_h / tex_h
        if sc.muv_texture_projection_apply_tex_aspect:
            ratio = ratio_y if ratio_x > ratio_y else ratio_x
            len_x = ratio * tex_w
            len_y = ratio * tex_h
        else:
            len_x = canvas_w
            len_y = canvas_h
    else:
        if sc.muv_texture_projection_apply_tex_aspect:
            len_x = tex_w
            len_y = tex_h
        else:
            len_x = region_w
            len_y = region_h

    x0 = int(center_x - len_x * 0.5)
    y0 = int(center_y - len_y * 0.5)
    x1 = int(center_x + len_x * 0.5)
    y1 = int(center_y + len_y * 0.5)

    return _Rect(x0, y0, x1, y1)


def _rect_to_rect2(rect):
    """
    Convert Rect1 to Rect2
    """

    return _Rect2(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0)


def _region_to_canvas(rg_vec, canvas):
    """
    Convert screen region to canvas
    """

    cv_rect = _rect_to_rect2(canvas)
    cv_vec = mathutils.Vector()
    cv_vec.x = (rg_vec.x - cv_rect.x) / cv_rect.width
    cv_vec.y = (rg_vec.y - cv_rect.y) / cv_rect.height

    return cv_vec


def _create_affine_matrix(identity, scale, rotate, translate):
    if identity:
        return mathutils.Matrix.Identity(3)

    sx = scale[0]
    sy = scale[1]
    theta = rotate
    tx = translate[0]
    ty = translate[1]

    mat_scale = mathutils.Matrix((
        (sx, 0.0, 0.0),
        (0.0, sy, 0.0),
        (0.0, 0.0, 1.0)
    ))
    mat_rotate = mathutils.Matrix((
        (cos(theta), sin(theta), 0.0),
        (-sin(theta), cos(theta), 0.0),
        (0.0, 0.0, 1.0)
    ))
    mat_translate = mathutils.Matrix((
        (1.0, 0.0, tx),
        (0.0, 1.0, ty),
        (0.0, 0.0, 1.0)
    ))

    return compat.matmul(compat.matmul(mat_translate, mat_rotate), mat_scale)


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


@PropertyClassRegistry()
class _Properties:
    idname = "texture_projection"

    @classmethod
    def init_props(cls, scene):
        def get_func(_):
            return MUV_OT_TextureProjection.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_texture_projection('INVOKE_REGION_WIN')

        scene.muv_texture_projection_enabled = BoolProperty(
            name="Texture Projection Enabled",
            description="Texture Projection is enabled",
            default=False
        )
        scene.muv_texture_projection_enable = BoolProperty(
            name="Texture Projection Enabled",
            description="Texture Projection is enabled",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_texture_projection_tex_scaling = FloatVectorProperty(
            name="Scaling",
            description="Texture Scale",
            default=(0.5, 0.5),
            min=-100.0,
            max=100.0,
            size=2,
            subtype='XYZ'
        )
        scene.muv_texture_projection_tex_rotation = FloatProperty(
            name="Rotation",
            description="Texture Rotate",
            default=0.0,
            min=-360.0,
            max=360.0,
            subtype='ANGLE'
        )
        scene.muv_texture_projection_tex_translation = FloatVectorProperty(
            name="Translation",
            description="Texture Translate",
            default=(0.0, 0.0),
            min=-2000.0,
            max=2000.0,
            size=2,
            subtype='XYZ'
        )
        scene.muv_texture_projection_tex_image = EnumProperty(
            name="Image",
            description="Texture Image",
            items=_get_loaded_texture_name
        )
        scene.muv_texture_projection_tex_transparency = FloatProperty(
            name="Transparency",
            description="Texture Transparency",
            default=0.2,
            min=0.0,
            max=1.0
        )
        scene.muv_texture_projection_adjust_window = BoolProperty(
            name="Adjust Window",
            description="Scale of rendered texture is fitted to window",
            default=True
        )
        scene.muv_texture_projection_apply_tex_aspect = BoolProperty(
            name="Texture Aspect Ratio",
            description="Apply Texture Aspect ratio to displayed texture",
            default=True
        )
        scene.muv_texture_projection_assign_uvmap = BoolProperty(
            name="Assign UVMap",
            description="Assign UVMap when no UVmaps are available",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_texture_projection_enabled
        del scene.muv_texture_projection_tex_scaling
        del scene.muv_texture_projection_tex_rotation
        del scene.muv_texture_projection_tex_translation
        del scene.muv_texture_projection_tex_image
        del scene.muv_texture_projection_tex_transparency
        del scene.muv_texture_projection_adjust_window
        del scene.muv_texture_projection_apply_tex_aspect
        del scene.muv_texture_projection_assign_uvmap


@BlClassRegistry()
class MUV_OT_TextureProjection(bpy.types.Operator):
    """
    Operation class: Texture Projection
    Render texture
    """

    bl_idname = "uv.muv_texture_projection"
    bl_description = "Render selected texture"
    bl_label = "Texture renderer"

    __handle = None

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
        cls.__handle = bpy.types.SpaceView3D.draw_handler_add(
            MUV_OT_TextureProjection.draw_texture,
            (obj, context), 'WINDOW', 'POST_PIXEL')

    @classmethod
    def handle_remove(cls):
        if cls.__handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(cls.__handle, 'WINDOW')
            cls.__handle = None

    @classmethod
    def draw_texture(cls, _, context):
        sc = context.scene

        if not cls.is_running(context):
            return

        # no textures are selected
        if sc.muv_texture_projection_tex_image == "None":
            return

        # get texture to be renderred
        img = bpy.data.images[sc.muv_texture_projection_tex_image]

        # setup rendering region
        rect = _get_canvas(context)

        # Apply affine transformation.
        center = mathutils.Vector((
            (rect.x1 + rect.x0) / 2.0,
            (rect.y1 + rect.y0) / 2.0,
            0.0,
        ))
        p1 = mathutils.Vector((rect.x0 - center.x, rect.y0 - center.y, 1.0))
        p2 = mathutils.Vector((rect.x0 - center.x, rect.y1 - center.y, 1.0))
        p3 = mathutils.Vector((rect.x1 - center.x, rect.y1 - center.y, 1.0))
        p4 = mathutils.Vector((rect.x1 - center.x, rect.y0 - center.y, 1.0))
        mat_affine = _create_affine_matrix(
            sc.muv_texture_projection_adjust_window,
            sc.muv_texture_projection_tex_scaling,
            sc.muv_texture_projection_tex_rotation,
            sc.muv_texture_projection_tex_translation)
        p1 = compat.matmul(mat_affine, p1) + center
        p2 = compat.matmul(mat_affine, p2) + center
        p3 = compat.matmul(mat_affine, p3) + center
        p4 = compat.matmul(mat_affine, p4) + center

        positions = [
            [p1.x, p1.y],
            [p2.x, p2.y],
            [p3.x, p3.y],
            [p4.x, p4.y]
        ]
        tex_coords = [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [1.0, 0.0]
        ]

        # OpenGL configuration
        # render texture
        shader = gpu.shader.from_builtin('IMAGE_COLOR')
        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {"pos": positions, "texCoord": tex_coords},
        )

        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_sampler("image", gpu.texture.from_image(img))
        shader.uniform_float("color", (1.0, 1.0, 1.0, sc.muv_texture_projection_tex_transparency))
        batch.draw(shader)
        del batch

    def invoke(self, context, _):
        if not MUV_OT_TextureProjection.is_running(context):
            MUV_OT_TextureProjection.handle_add(self, context)
        else:
            MUV_OT_TextureProjection.handle_remove()

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_TextureProjection_Project(bpy.types.Operator):
    """
    Operation class: Project texture
    """

    bl_idname = "uv.muv_texture_projection_project"
    bl_label = "Project Texture"
    bl_description = "Project Texture"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        if not MUV_OT_TextureProjection.is_running(context):
            return False
        return _is_valid_context(context)

    def execute(self, context):
        sc = context.scene

        if sc.muv_texture_projection_tex_image == "None":
            self.report({'WARNING'}, "No textures are selected")
            return {'CANCELLED'}

        _, region, space = common.get_space('VIEW_3D', 'WINDOW', 'VIEW_3D')

        # get faces to be texture projected
        objs = common.get_uv_editable_objects(context)

        for obj in objs:
            world_mat = obj.matrix_world
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()

            # get UV and texture layer
            if not bm.loops.layers.uv:
                if sc.muv_texture_projection_assign_uvmap:
                    bm.loops.layers.uv.new()
                else:
                    self.report({'WARNING'},
                                "Object {} must have more than one UV map"
                                .format(obj.name))
                    return {'CANCELLED'}

            uv_layer = bm.loops.layers.uv.verify()
            if compat.check_version(2, 80, 0) < 0:
                tex_layer = bm.faces.layers.tex.verify()

            sel_faces = [f for f in bm.faces if f.select]

            # transform 3d space to screen region
            v_screen = [
                view3d_utils.location_3d_to_region_2d(
                    region,
                    space.region_3d,
                    compat.matmul(world_mat, l.vert.co))
                for f in sel_faces for l in f.loops
            ]

            # Apply affine transformation.
            rect = _get_canvas(bpy.context)
            center = mathutils.Vector((
                (rect.x1 + rect.x0) / 2.0,
                (rect.y1 + rect.y0) / 2.0,
                0.0,
            ))
            v_screen_transformed = []
            for v in v_screen:
                p1 = mathutils.Vector((v.x - center.x, v.y - center.y, 1.0))
                mat_affine = _create_affine_matrix(
                    sc.muv_texture_projection_adjust_window,
                    sc.muv_texture_projection_tex_scaling,
                    sc.muv_texture_projection_tex_rotation,
                    sc.muv_texture_projection_tex_translation)
                p1 = compat.matmul(mat_affine.inverted(), p1) + center
                v_screen_transformed.append(p1)

            # transform screen region to canvas
            v_canvas = [
                _region_to_canvas(
                    v,
                    rect
                ) for v in v_screen_transformed
            ]

            # assign image
            if compat.check_version(2, 80, 0) >= 0:
                node_tree = obj.active_material.node_tree
                output_node = next(n for n in node_tree.nodes
                                   if n.type == "OUTPUT_MATERIAL")

                nodes = common.find_texture_nodes_from_material(
                    obj.active_material)
                if len(nodes) >= 1:
                    tex_node = nodes[0]
                else:
                    tex_node = node_tree.nodes.new(type="ShaderNodeTexImage")
                tex_node.image = \
                    bpy.data.images[sc.muv_texture_projection_tex_image]
                node_tree.links.new(
                    output_node.inputs["Surface"], tex_node.outputs["Color"])
            else:
                for f in sel_faces:
                    f[tex_layer].image = \
                        bpy.data.images[sc.muv_texture_projection_tex_image]

            # project texture to object
            i = 0
            for f in sel_faces:
                for l in f.loops:
                    l[uv_layer].uv = v_canvas[i].to_2d()
                    i = i + 1

            common.redraw_all_areas()
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
