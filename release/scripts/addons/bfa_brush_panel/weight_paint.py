import bpy

from .common import BrushPanelBase


def icon_name_from_weight_brush(weight_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_weight."
    tool_name = weight_brush.weight_tool
    icon_name = icon_prefix + tool_name.lower()
    return icon_name


def tool_name_from_weight_brush(weight_brush: bpy.types.Brush):
    return weight_brush.weight_tool


def filter_weight_brush(weight_brush: bpy.types.Brush):
    return weight_brush.use_paint_weight


WEIGHT_TOOLS = ["DRAW", "SMEAR", "AVERAGE", "BLUR"]
panel_classes = [
    type(
        f"BFA_PT_brush_weight_{tool_name}",
        (BrushPanelBase,),
        {
            "bl_label": tool_name.capitalize(),
            "tool_name": tool_name,
            "mode": "PAINT_WEIGHT",
            "tool_settings_attribute_name": "weight_paint",
            "filter_brush": staticmethod(filter_weight_brush),
            "icon_name_from_brush": staticmethod(icon_name_from_weight_brush),
            "tool_name_from_brush": staticmethod(tool_name_from_weight_brush),
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
