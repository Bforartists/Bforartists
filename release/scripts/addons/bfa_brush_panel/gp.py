import bpy

from .panels import panel_factory_view3d


panel_classes = list(
    panel_factory_view3d(
        tools=["DRAW", "ERASE", "FILL", "TINT"],
        icon_prefix="brush.gpencil_draw.",
        tool_name_attr="gpencil_tool",
        use_paint_attr="use_paint_grease_pencil",
        tool_settings_attr="gpencil_paint",
        mode="PAINT_GPENCIL",
    )
)


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
