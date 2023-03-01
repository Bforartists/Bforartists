import bpy

from .panels import panel_factory_view3d


panel_classes = list(
    panel_factory_view3d(
        tools=["DRAW", "SMEAR", "AVERAGE", "BLUR"],
        icon_prefix="brush.paint_vertex.",
        tool_name_attr="vertex_tool",
        use_paint_attr="use_paint_vertex",
        tool_settings_attr="vertex_paint",
        mode="PAINT_VERTEX")
)


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
