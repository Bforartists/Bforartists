# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from mathutils import Vector
from bpy.props import EnumProperty, BoolProperty, FloatVectorProperty
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "align_uv_cursor"

    @classmethod
    def init_props(cls, scene):
        def auvc_get_cursor_loc(self):
            area, _, space = common.get_space('IMAGE_EDITOR', 'WINDOW',
                                              'IMAGE_EDITOR')
            if compat.check_version(2, 80, 0) < 0:
                bd_size = common.get_uvimg_editor_board_size(area)
            else:
                bd_size = [1.0, 1.0]
            loc = space.cursor_location

            if bd_size[0] < 0.000001:
                cx = 0.0
            else:
                cx = loc[0] / bd_size[0]
            if bd_size[1] < 0.000001:
                cy = 0.0
            else:
                cy = loc[1] / bd_size[1]

            self['muv_align_uv_cursor_cursor_loc'] = Vector((cx, cy))
            return self.get('muv_align_uv_cursor_cursor_loc', (0.0, 0.0))

        def auvc_set_cursor_loc(self, value):
            self['muv_align_uv_cursor_cursor_loc'] = value
            area, _, space = common.get_space('IMAGE_EDITOR', 'WINDOW',
                                              'IMAGE_EDITOR')
            if compat.check_version(2, 80, 0) < 0:
                bd_size = common.get_uvimg_editor_board_size(area)
            else:
                bd_size = [1.0, 1.0]
            cx = bd_size[0] * value[0]
            cy = bd_size[1] * value[1]
            space.cursor_location = Vector((cx, cy))

        scene.muv_align_uv_cursor_enabled = BoolProperty(
            name="Align UV Cursor Enabled",
            description="Align UV Cursor is enabled",
            default=False
        )

        scene.muv_align_uv_cursor_cursor_loc = FloatVectorProperty(
            name="UV Cursor Location",
            size=2,
            precision=4,
            soft_min=-1.0,
            soft_max=1.0,
            step=1,
            default=(0.000, 0.000),
            get=auvc_get_cursor_loc,
            set=auvc_set_cursor_loc
        )
        scene.muv_align_uv_cursor_align_method = EnumProperty(
            name="Align Method",
            description="Align Method",
            default='TEXTURE',
            items=[
                ('TEXTURE', "Texture", "Align to texture"),
                ('UV', "UV", "Align to UV"),
                ('UV_SEL', "UV (Selected)", "Align to Selected UV")
            ]
        )

        scene.muv_uv_cursor_location_enabled = BoolProperty(
            name="UV Cursor Location Enabled",
            description="UV Cursor Location is enabled",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_align_uv_cursor_enabled
        del scene.muv_align_uv_cursor_cursor_loc
        del scene.muv_align_uv_cursor_align_method

        del scene.muv_uv_cursor_location_enabled


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_AlignUVCursor(bpy.types.Operator):

    bl_idname = "uv.muv_align_uv_cursor"
    bl_label = "Align UV Cursor"
    bl_description = "Align cursor to the center of UV island"
    bl_options = {'REGISTER', 'UNDO'}

    position = EnumProperty(
        items=(
            ('CENTER', "Center", "Align to Center"),
            ('LEFT_TOP', "Left Top", "Align to Left Top"),
            ('LEFT_MIDDLE', "Left Middle", "Align to Left Middle"),
            ('LEFT_BOTTOM', "Left Bottom", "Align to Left Bottom"),
            ('MIDDLE_TOP', "Middle Top", "Align to Middle Top"),
            ('MIDDLE_BOTTOM', "Middle Bottom", "Align to Middle Bottom"),
            ('RIGHT_TOP', "Right Top", "Align to Right Top"),
            ('RIGHT_MIDDLE', "Right Middle", "Align to Right Middle"),
            ('RIGHT_BOTTOM', "Right Bottom", "Align to Right Bottom")
        ),
        name="Position",
        description="Align position",
        default='CENTER'
    )
    base = EnumProperty(
        items=(
            ('TEXTURE', "Texture", "Align based on Texture"),
            ('UV', "UV", "Align to UV"),
            ('UV_SEL', "UV (Selected)", "Align to Selected UV")
        ),
        name="Base",
        description="Align base",
        default='TEXTURE'
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        area, _, space = common.get_space('IMAGE_EDITOR', 'WINDOW',
                                          'IMAGE_EDITOR')
        if compat.check_version(2, 80, 0) < 0:
            bd_size = common.get_uvimg_editor_board_size(area)
        else:
            bd_size = [1.0, 1.0]

        large_value = 1e7
        if self.base == 'UV':
            objs = common.get_uv_editable_objects(context)
            no_selected_face = True
            if objs:
                max_ = Vector((-large_value, -large_value))
                min_ = Vector((large_value, large_value))
                for obj in objs:
                    bm = bmesh.from_edit_mesh(obj.data)
                    if not bm.loops.layers.uv:
                        return None
                    uv_layer = bm.loops.layers.uv.verify()

                    for f in bm.faces:
                        if (not context.tool_settings.use_uv_select_sync and
                                not f.select):
                            continue
                        for l in f.loops:
                            uv = l[uv_layer].uv
                            max_.x = max(max_.x, uv.x)
                            max_.y = max(max_.y, uv.y)
                            min_.x = min(min_.x, uv.x)
                            min_.y = min(min_.y, uv.y)
                            no_selected_face = False
            if no_selected_face:
                max_ = Vector((1.0, 1.0))
                min_ = Vector((0.0, 0.0))
            center = Vector((
                (max_.x + min_.x) / 2.0, (max_.y + min_.y) / 2.0
            ))

        # pylint: disable=R1702
        elif self.base == 'UV_SEL':
            objs = common.get_uv_editable_objects(context)
            no_selected_face = True
            if objs:
                max_ = Vector((-large_value, -large_value))
                min_ = Vector((large_value, large_value))
                for obj in objs:
                    bm = bmesh.from_edit_mesh(obj.data)
                    if not bm.loops.layers.uv:
                        return None
                    uv_layer = bm.loops.layers.uv.verify()

                    if context.tool_settings.use_uv_select_sync:
                        for v in bm.verts:
                            if not v.select:
                                continue
                            for l in v.link_loops:
                                uv = l[uv_layer].uv
                                max_.x = max(max_.x, uv.x)
                                max_.y = max(max_.y, uv.y)
                                min_.x = min(min_.x, uv.x)
                                min_.y = min(min_.y, uv.y)
                                no_selected_face = False
                    else:
                        for f in bm.faces:
                            if not f.select:
                                continue
                            for l in f.loops:
                                if not l[uv_layer].select:
                                    continue
                                uv = l[uv_layer].uv
                                max_.x = max(max_.x, uv.x)
                                max_.y = max(max_.y, uv.y)
                                min_.x = min(min_.x, uv.x)
                                min_.y = min(min_.y, uv.y)
                                no_selected_face = False
            if no_selected_face:
                max_ = Vector((1.0, 1.0))
                min_ = Vector((0.0, 0.0))
            center = Vector((
                (max_.x + min_.x) / 2.0, (max_.y + min_.y) / 2.0
            ))

        elif self.base == 'TEXTURE':
            min_ = Vector((0.0, 0.0))
            max_ = Vector((1.0, 1.0))
            center = Vector((0.5, 0.5))
        else:
            self.report({'ERROR'}, "Unknown Operation")
            return {'CANCELLED'}

        if self.position == 'CENTER':
            cx = center.x
            cy = center.y
        elif self.position == 'LEFT_TOP':
            cx = min_.x
            cy = max_.y
        elif self.position == 'LEFT_MIDDLE':
            cx = min_.x
            cy = center.y
        elif self.position == 'LEFT_BOTTOM':
            cx = min_.x
            cy = min_.y
        elif self.position == 'MIDDLE_TOP':
            cx = center.x
            cy = max_.y
        elif self.position == 'MIDDLE_BOTTOM':
            cx = center.x
            cy = min_.y
        elif self.position == 'RIGHT_TOP':
            cx = max_.x
            cy = max_.y
        elif self.position == 'RIGHT_MIDDLE':
            cx = max_.x
            cy = center.y
        elif self.position == 'RIGHT_BOTTOM':
            cx = max_.x
            cy = min_.y
        else:
            self.report({'ERROR'}, "Unknown Operation")
            return {'CANCELLED'}

        cx = cx * bd_size[0]
        cy = cy * bd_size[1]

        space.cursor_location = Vector((cx, cy))

        return {'FINISHED'}
