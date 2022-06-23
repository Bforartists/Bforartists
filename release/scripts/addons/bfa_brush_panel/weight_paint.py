from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

import bpy

from .common import column_count
from .icon_manager import BrushIcon, get_brush_icon


def icon_name_from_weight_brush(weight_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_weight."
    idname = weight_brush.weight_tool
    icon_name = icon_prefix + idname.lower()
    return icon_name


@dataclass
class WeightBrushButton:
    brush_name: str
    brush_icon: BrushIcon

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
        # TODO: make "weight_paint" variable to support other paint modes
        op.paint_settings_attr_name = "weight_paint"
        op.brush_name = self.brush_name
        op.dynamic_description = self.brush_name if icon_only else "Set Brush"


def get_weight_brush_buttons():
    """Get mapping from tool name to weight brush buttons from brushes in the blend file"""
    buttons: Dict[str, List[WeightBrushButton]] = defaultdict(list)
    brush: bpy.types.Brush
    for brush in sorted(bpy.data.brushes, key=lambda b: b.name):
        if not brush.use_paint_weight:
            continue
        icon = get_brush_icon(brush, icon_name_from_weight_brush)
        buttons[brush.weight_tool].append(WeightBrushButton(brush.name, icon))
        # TODO: support linked brushes
    return buttons


class WeightBrushPanelBase(bpy.types.Panel):
    bl_label = "Brush"  # Override this
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    tool_name = ""  # Override this

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        buttons = get_weight_brush_buttons()
        num_cols = column_count(context.region)
        if num_cols == 4:
            col = layout.column(align=True)
            icon_only = False
        else:
            col = layout.column_flow(columns=num_cols, align=True)
            icon_only = True

        for but in buttons[self.tool_name]:
            but.draw(context, col, icon_only=icon_only)


WEIGHT_TOOLS = ["DRAW", "SMEAR", "AVERAGE", "BLUR"]
panel_classes = [type(f"BFA_PT_brush_weight_{tool_name}", (WeightBrushPanelBase,),
                      {"bl_label": tool_name.capitalize(), "tool_name": tool_name})
                 for tool_name in WEIGHT_TOOLS]


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
