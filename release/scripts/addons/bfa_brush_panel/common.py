from typing import Callable

import bpy

from .icon_system import get_brush_icon


def column_count(region: bpy.types.Region):
    system = bpy.context.preferences.system
    view2d = region.view2d
    view2d_scale = (
        view2d.region_to_view(1.0, 0.0)[0] - view2d.region_to_view(0.0, 0.0)[0]
    )
    width_scale = region.width * view2d_scale / system.ui_scale

    if width_scale > 160.0:
        column_count = 4
    elif width_scale > 120.0:
        column_count = 3
    elif width_scale > 80:
        column_count = 2
    else:
        column_count = 1

    return column_count


def draw_brush_button(
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    icon_only: bool,
    brush: bpy.types.Brush,
    tool_settings_attribute_name: str,
    icon_name_from_brush: Callable[[bpy.types.Brush], str],
    tool_name_from_brush: Callable[[bpy.types.Brush], str],
):
    brush_name = brush.name
    icon = get_brush_icon(brush, icon_name_from_brush, tool_name_from_brush)
    active_brush = getattr(context.tool_settings, tool_settings_attribute_name).brush

    is_active = False
    if active_brush is not None:
        is_active = active_brush.name == brush_name

    op = layout.operator(
        "bfa.set_brush",
        text="" if icon_only else brush_name,
        icon=icon.icon_name,
        icon_value=icon.icon_value,
        depress=is_active,
    )

    op.tool_settings_attribute_name = tool_settings_attribute_name
    op.brush_name = brush_name
    op.dynamic_description = brush_name if icon_only else "Set Brush"


class BrushPanelBase(bpy.types.Panel):
    bl_label = "Brush"  # Override this
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    tool_name = ""  # Override this
    tool_settings_attribute_name = ""  # Override this

    @staticmethod
    def icon_name_from_brush(brush: bpy.types.Brush):
        # Override this
        raise NotImplementedError

    @staticmethod
    def tool_name_from_brush(brush: bpy.types.Brush):
        # Override this
        raise NotImplementedError

    @staticmethod
    def filter_brush(brush: bpy.types.Brush):
        # Override this
        raise NotImplementedError

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        num_cols = column_count(context.region)
        if num_cols == 4:
            col = layout.column(align=True)
            icon_only = False
        else:
            col = layout.column_flow(columns=num_cols, align=True)
            icon_only = True

        for brush in sorted(bpy.data.brushes, key=lambda brush: brush.name):
            if not self.filter_brush(brush):
                continue
            if self.tool_name_from_brush(brush) == self.tool_name:
                draw_brush_button(
                    context,
                    col,
                    icon_only,
                    brush,
                    self.tool_settings_attribute_name,
                    self.icon_name_from_brush,
                    self.tool_name_from_brush,
                )
