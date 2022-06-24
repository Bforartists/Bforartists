import bpy

from .common import BrushPanelBase


def icon_name_from_vertex_brush(vertex_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_vertex."
    tool_name = vertex_brush.vertex_tool
    icon_name = icon_prefix + tool_name.lower()
    return icon_name


def tool_name_from_vertex_brush(vertex_brush: bpy.types.Brush):
    return vertex_brush.vertex_tool


def filter_vertex_brush(vertex_brush: bpy.types.Brush):
    return vertex_brush.use_paint_vertex


VERTEX_TOOLS = ["DRAW", "SMEAR", "AVERAGE", "BLUR"]
panel_classes = [
    type(
        f"BFA_PT_brush_vertex_{tool_name}",
        (BrushPanelBase,),
        {
            "bl_label": tool_name.capitalize(),
            "tool_name": tool_name,
            "mode": "PAINT_VERTEX",
            "tool_settings_attribute_name": "vertex_paint",
            "filter_brush": staticmethod(filter_vertex_brush),
            "icon_name_from_brush": staticmethod(icon_name_from_vertex_brush),
            "tool_name_from_brush": staticmethod(tool_name_from_vertex_brush),
        },
    )
    for tool_name in VERTEX_TOOLS
]


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
