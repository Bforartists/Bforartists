import bpy

from .panels import panel_factory_image_editor


panel_classes = list(
    panel_factory_image_editor(
        tools=["DRAW", "SOFTEN", "SMEAR", "CLONE", "FILL", "MASK"],
        icon_prefix="brush.paint_texture.",
        tool_name_attr="image_tool",
        use_paint_attr="use_paint_image",
        tool_settings_attr="image_paint",
    )
)


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
