import bpy

from .common import BrushPanelBase


def icon_name_from_texture_brush(texture_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_texture."
    tool_name = texture_brush.image_tool
    icon_name = icon_prefix + tool_name.lower()
    return icon_name


def tool_name_from_texture_brush(texture_brush: bpy.types.Brush):
    return texture_brush.image_tool


def filter_texture_brush(texture_brush: bpy.types.Brush):
    return texture_brush.use_paint_image


TEXTURE_TOOLS = ["DRAW", "SOFTEN", "SMEAR", "CLONE", "FILL", "MASK"]
panel_classes = [
    type(
        f"BFA_PT_brush_texture_{tool_name}",
        (BrushPanelBase,),
        {
            "bl_label": tool_name.capitalize(),
            "tool_name": tool_name,
            "mode": "PAINT_TEXTURE",
            "tool_settings_attribute_name": "image_paint",
            "filter_brush": staticmethod(filter_texture_brush),
            "icon_name_from_brush": staticmethod(icon_name_from_texture_brush),
            "tool_name_from_brush": staticmethod(tool_name_from_texture_brush),
        },
    )
    for tool_name in TEXTURE_TOOLS
]


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
