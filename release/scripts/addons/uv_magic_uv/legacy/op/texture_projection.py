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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

from collections import namedtuple

import bpy
import bgl
import bmesh
import mathutils
from bpy_extras import view3d_utils
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)

from ... import common
from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry


__all__ = [
    'Properties',
    'MUV_OT_TextureProjection',
    'MUV_OT_TextureProjection_Project',
]


Rect = namedtuple('Rect', 'x0 y0 x1 y1')
Rect2 = namedtuple('Rect2', 'x y width height')


def get_loaded_texture_name(_, __):
    items = [(key, key, "") for key in bpy.data.images.keys()]
    items.append(("None", "None", ""))
    return items


def get_canvas(context, magnitude):
    """
    Get canvas to be renderred texture
    """
    sc = context.scene
    prefs = context.preferences.addons["uv_magic_uv"].preferences

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
            len_x = tex_w * magnitude
            len_y = tex_h * magnitude
        else:
            len_x = region_w * magnitude
            len_y = region_h * magnitude

    x0 = int(center_x - len_x * 0.5)
    y0 = int(center_y - len_y * 0.5)
    x1 = int(center_x + len_x * 0.5)
    y1 = int(center_y + len_y * 0.5)

    return Rect(x0, y0, x1, y1)


def rect_to_rect2(rect):
    """
    Convert Rect1 to Rect2
    """

    return Rect2(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0)


def region_to_canvas(rg_vec, canvas):
    """
    Convert screen region to canvas
    """

    cv_rect = rect_to_rect2(canvas)
    cv_vec = mathutils.Vector()
    cv_vec.x = (rg_vec.x - cv_rect.x) / cv_rect.width
    cv_vec.y = (rg_vec.y - cv_rect.y) / cv_rect.height

    return cv_vec


def is_valid_context(context):
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


@PropertyClassRegistry(legacy=True)
class Properties:
    idname = "texture_projection"

    @classmethod
    def init_props(cls, scene):
        def get_func(_):
            return MUV_OT_TextureProjection.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_texture_projection_operator('INVOKE_REGION_WIN')

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
        scene.muv_texture_projection_tex_magnitude = FloatProperty(
            name="Magnitude",
            description="Texture Magnitude",
            default=0.5,
            min=0.0,
            max=100.0
        )
        scene.muv_texture_projection_tex_image = EnumProperty(
            name="Image",
            description="Texture Image",
            items=get_loaded_texture_name
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
            description="Size of renderered texture is fitted to window",
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
        del scene.muv_texture_projection_tex_magnitude
        del scene.muv_texture_projection_tex_image
        del scene.muv_texture_projection_tex_transparency
        del scene.muv_texture_projection_adjust_window
        del scene.muv_texture_projection_apply_tex_aspect
        del scene.muv_texture_projection_assign_uvmap


@BlClassRegistry(legacy=True)
class MUV_OT_TextureProjection(bpy.types.Operator):
    """
    Operation class: Texture Projection
    Render texture
    """

    bl_idname = "uv.muv_texture_projection_operator"
    bl_description = "Render selected texture"
    bl_label = "Texture renderer"

    __handle = None

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return False
        return is_valid_context(context)

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
        rect = get_canvas(context, sc.muv_texture_projection_tex_magnitude)
        positions = [
            [rect.x0, rect.y0],
            [rect.x0, rect.y1],
            [rect.x1, rect.y1],
            [rect.x1, rect.y0]
        ]
        tex_coords = [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [1.0, 0.0]
        ]

        # OpenGL configuration
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        if img.bindcode:
            bind = img.bindcode[0]
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, bind)
            bgl.glTexParameteri(
                bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
            bgl.glTexParameteri(
                bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
            bgl.glTexEnvi(
                bgl.GL_TEXTURE_ENV, bgl.GL_TEXTURE_ENV_MODE, bgl.GL_MODULATE)

        # render texture
        bgl.glBegin(bgl.GL_QUADS)
        bgl.glColor4f(1.0, 1.0, 1.0,
                      sc.muv_texture_projection_tex_transparency)
        for (v1, v2), (u, v) in zip(positions, tex_coords):
            bgl.glTexCoord2f(u, v)
            bgl.glVertex2f(v1, v2)
        bgl.glEnd()

    def invoke(self, context, _):
        if not MUV_OT_TextureProjection.is_running(context):
            MUV_OT_TextureProjection.handle_add(self, context)
        else:
            MUV_OT_TextureProjection.handle_remove()

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


@BlClassRegistry(legacy=True)
class MUV_OT_TextureProjection_Project(bpy.types.Operator):
    """
    Operation class: Project texture
    """

    bl_idname = "uv.muv_texture_projection_operator_project"
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
        return is_valid_context(context)

    def execute(self, context):
        sc = context.scene

        if sc.muv_texture_projection_tex_image == "None":
            self.report({'WARNING'}, "No textures are selected")
            return {'CANCELLED'}

        _, region, space = common.get_space(
            'VIEW_3D', 'WINDOW', 'VIEW_3D')

        # get faces to be texture projected
        obj = context.active_object
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
                            "Object must have more than one UV map")
                return {'CANCELLED'}

        uv_layer = bm.loops.layers.uv.verify()
        tex_layer = bm.faces.layers.tex.verify()

        sel_faces = [f for f in bm.faces if f.select]

        # transform 3d space to screen region
        v_screen = [
            view3d_utils.location_3d_to_region_2d(
                region,
                space.region_3d,
                world_mat * l.vert.co)
            for f in sel_faces for l in f.loops
        ]

        # transform screen region to canvas
        v_canvas = [
            region_to_canvas(
                v,
                get_canvas(bpy.context,
                           sc.muv_texture_projection_tex_magnitude)
            ) for v in v_screen
        ]

        # project texture to object
        i = 0
        for f in sel_faces:
            f[tex_layer].image = \
                bpy.data.images[sc.muv_texture_projection_tex_image]
            for l in f.loops:
                l[uv_layer].uv = v_canvas[i].to_2d()
                i = i + 1

        common.redraw_all_areas()
        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
