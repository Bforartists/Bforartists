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
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy
from bpy.props import BoolProperty, EnumProperty
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat

if compat.check_version(2, 80, 0) >= 0:
    from ..lib import bglx as bgl
else:
    import bgl


def _is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    for space in context.area.spaces:
        if (space.type == 'IMAGE_EDITOR') or (space.type == 'VIEW_3D'):
            break
    else:
        return False

    return True


def _update_uvinsp_info(context):
    sc = context.scene
    props = sc.muv_props.uv_inspection

    obj = context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    if common.check_version(2, 73, 0) >= 0:
        bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    if context.tool_settings.use_uv_select_sync:
        sel_faces = [f for f in bm.faces]
    else:
        sel_faces = [f for f in bm.faces if f.select]
    props.overlapped_info = common.get_overlapped_uv_info(
        bm, sel_faces, uv_layer, sc.muv_uv_inspection_show_mode)
    props.flipped_info = common.get_flipped_uv_info(sel_faces, uv_layer)


@PropertyClassRegistry()
class _Properties:
    idname = "uv_inspection"

    @classmethod
    def init_props(cls, scene):
        class Props():
            overlapped_info = []
            flipped_info = []

        scene.muv_props.uv_inspection = Props()

        def get_func(_):
            return MUV_OT_UVInspection_Render.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_ot_uv_inspection_render('INVOKE_REGION_WIN')

        scene.muv_uv_inspection_enabled = BoolProperty(
            name="UV Inspection Enabled",
            description="UV Inspection is enabled",
            default=False
        )
        scene.muv_uv_inspection_show = BoolProperty(
            name="UV Inspection Showed",
            description="UV Inspection is showed",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_uv_inspection_show_overlapped = BoolProperty(
            name="Overlapped",
            description="Show overlapped UVs",
            default=False
        )
        scene.muv_uv_inspection_show_flipped = BoolProperty(
            name="Flipped",
            description="Show flipped UVs",
            default=False
        )
        scene.muv_uv_inspection_show_mode = EnumProperty(
            name="Mode",
            description="Show mode",
            items=[
                ('PART', "Part", "Show only overlapped/flipped part"),
                ('FACE', "Face", "Show overlapped/flipped face")
            ],
            default='PART'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.uv_inspection
        del scene.muv_uv_inspection_enabled
        del scene.muv_uv_inspection_show
        del scene.muv_uv_inspection_show_overlapped
        del scene.muv_uv_inspection_show_flipped
        del scene.muv_uv_inspection_show_mode


@BlClassRegistry()
class MUV_OT_UVInspection_Render(bpy.types.Operator):
    """
    Operation class: Render UV Inspection
    No operation (only rendering)
    """

    bl_idname = "uv.muv_ot_uv_inspection_render"
    bl_description = "Render overlapped/flipped UVs"
    bl_label = "Overlapped/Flipped UV renderer"

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
        sie = bpy.types.SpaceImageEditor
        cls.__handle = sie.draw_handler_add(
            MUV_OT_UVInspection_Render.draw, (obj, context),
            'WINDOW', 'POST_PIXEL')

    @classmethod
    def handle_remove(cls):
        if cls.__handle is not None:
            bpy.types.SpaceImageEditor.draw_handler_remove(
                cls.__handle, 'WINDOW')
            cls.__handle = None

    @staticmethod
    def draw(_, context):
        sc = context.scene
        props = sc.muv_props.uv_inspection
        user_prefs = compat.get_user_preferences(context)
        prefs = user_prefs.addons["magic_uv"].preferences

        if not MUV_OT_UVInspection_Render.is_running(context):
            return

        # OpenGL configuration
        bgl.glEnable(bgl.GL_BLEND)

        # render overlapped UV
        if sc.muv_uv_inspection_show_overlapped:
            color = prefs.uv_inspection_overlapped_color
            for info in props.overlapped_info:
                if sc.muv_uv_inspection_show_mode == 'PART':
                    for poly in info["polygons"]:
                        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                        bgl.glColor4f(color[0], color[1], color[2], color[3])
                        for uv in poly:
                            x, y = context.region.view2d.view_to_region(
                                uv.x, uv.y)
                            bgl.glVertex2f(x, y)
                        bgl.glEnd()
                elif sc.muv_uv_inspection_show_mode == 'FACE':
                    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                    bgl.glColor4f(color[0], color[1], color[2], color[3])
                    for uv in info["subject_uvs"]:
                        x, y = context.region.view2d.view_to_region(uv.x, uv.y)
                        bgl.glVertex2f(x, y)
                    bgl.glEnd()

        # render flipped UV
        if sc.muv_uv_inspection_show_flipped:
            color = prefs.uv_inspection_flipped_color
            for info in props.flipped_info:
                if sc.muv_uv_inspection_show_mode == 'PART':
                    for poly in info["polygons"]:
                        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                        bgl.glColor4f(color[0], color[1], color[2], color[3])
                        for uv in poly:
                            x, y = context.region.view2d.view_to_region(
                                uv.x, uv.y)
                            bgl.glVertex2f(x, y)
                        bgl.glEnd()
                elif sc.muv_uv_inspection_show_mode == 'FACE':
                    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                    bgl.glColor4f(color[0], color[1], color[2], color[3])
                    for uv in info["uvs"]:
                        x, y = context.region.view2d.view_to_region(uv.x, uv.y)
                        bgl.glVertex2f(x, y)
                    bgl.glEnd()

        bgl.glDisable(bgl.GL_BLEND)

    def invoke(self, context, _):
        if not MUV_OT_UVInspection_Render.is_running(context):
            _update_uvinsp_info(context)
            MUV_OT_UVInspection_Render.handle_add(self, context)
        else:
            MUV_OT_UVInspection_Render.handle_remove()

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_UVInspection_Update(bpy.types.Operator):
    """
    Operation class: Update
    """

    bl_idname = "uv.muv_ot_uv_inspection_update"
    bl_label = "Update UV Inspection"
    bl_description = "Update UV Inspection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        if not MUV_OT_UVInspection_Render.is_running(context):
            return False
        return _is_valid_context(context)

    def execute(self, context):
        _update_uvinsp_info(context)

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}
