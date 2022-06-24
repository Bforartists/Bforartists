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
