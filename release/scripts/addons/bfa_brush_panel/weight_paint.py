from collections import defaultdict
from typing import Dict, List

import bpy

from .common import BrushButton, column_count
from .icon_system import get_brush_icon


def icon_name_from_weight_brush(weight_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_weight."
    idname = weight_brush.weight_tool
    icon_name = icon_prefix + idname.lower()
    return icon_name


def get_weight_brush_buttons():
    """Get mapping from tool name to weight brush buttons from brushes in the blend file"""
    buttons: Dict[str, List[BrushButton]] = defaultdict(list)
    brush: bpy.types.Brush
    for brush in sorted(bpy.data.brushes, key=lambda b: b.name):
        if not brush.use_paint_weight:
            continue
        # TODO: since #get_weight_brush_buttons is currently called every draw anyways
        # we can move #get_brush_icon into draw method of brush button.
        # Alternatively we can also just load icons only once when the addon loads
        # this would have worked if we don't want to support dynamic and custom icons
        icon = get_brush_icon(brush, icon_name_from_weight_brush)
        buttons[brush.weight_tool].append(BrushButton(brush.name, icon, "weight_paint"))
        # TODO: support linked brushes
    return buttons


# TODO: generalize this base calss to work with all modes
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
panel_classes = [
    type(
        f"BFA_PT_brush_weight_{tool_name}",
        (WeightBrushPanelBase,),
        {
            "bl_label": tool_name.capitalize(),
            "tool_name": tool_name,
        },
    )
    for tool_name in WEIGHT_TOOLS
]


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
