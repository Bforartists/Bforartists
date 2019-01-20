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

import bpy
import bgl
import bmesh
from bpy_extras import view3d_utils
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)

from ... import common
from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry
from ...impl import texture_projection_impl as impl


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
            items=impl.get_loaded_texture_name
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
        return impl.is_valid_context(context)

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
        rect = impl.get_canvas(context, sc.muv_texture_projection_tex_magnitude)
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
        return impl.is_valid_context(context)

    def execute(self, context):
        sc = context.scene

        if sc.muv_texture_projection_tex_image == "None":
            self.report({'WARNING'}, "No textures are selected")
            return {'CANCELLED'}

        _, region, space = common.get_space_legacy(
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
            impl.region_to_canvas(
                v,
                impl.get_canvas(bpy.context,
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
