
from dataclasses import dataclass

import bpy

from .icon_system import BrushIcon


def column_count(region: bpy.types.Region):
    system = bpy.context.preferences.system
    view2d = region.view2d
    view2d_scale = view2d.region_to_view(1.0, 0.0)[0] - view2d.region_to_view(0.0, 0.0)[0]
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


@dataclass
class BrushButton:
    brush_name: str
    brush_icon: BrushIcon
    tool_settings_attribute_name: str
    """Attribute used to set brush (e.g 'weight_paint')"""

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout, icon_only=False):
        active_brush = context.tool_settings.weight_paint.brush
        is_active = False
        if active_brush is not None:
            is_active = active_brush.name == self.brush_name

        op = layout.operator(
            "bfa.set_brush",
            text="" if icon_only else self.brush_name,
            icon=self.brush_icon.icon_name,
            icon_value=self.brush_icon.icon_value,
            depress=is_active,
        )
        op.paint_settings_attr_name = self.tool_settings_attribute_name
        op.brush_name = self.brush_name
        op.dynamic_description = self.brush_name if icon_only else "Set Brush"
