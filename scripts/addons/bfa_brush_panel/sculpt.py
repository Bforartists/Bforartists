import bpy

from .panels import panel_factory_view3d


panel_classes = list(
    panel_factory_view3d(
        tools=[
(           "Draw", # Panel label and category
            "DRAW",
            "DRAW_SHARP",
            "CLAY",
            "CLAY_STRIPS",
            "CLAY_THUMB",
            "LAYER",
            "INFLATE",
            "BLOB",
            "CREASE"),
(           "Surface", # Panel label and category 
            "SMOOTH",
            "FLATTEN",
            "FILL",
            "SCRAPE",
            "MULTIPLANE_SCRAPE"),
(           "Deform", # Panel label and category  
            "PINCH",
            "GRAB",
            "ELASTIC_DEFORM",
            "SNAKE_HOOK",
            "THUMB",
            "POSE",
            "NUDGE",
            "ROTATE",
            "TOPOLOGY",
            "BOUNDARY"),
(           "Misc", # Panel label and category 
            "CLOTH",
            "SIMPLIFY",
            "MASK",
            "DRAW_FACE_SETS",
            "DISPLACEMENT_ERASER",
            "DISPLACEMENT_SMEAR",
            "PAINT"),
        ],
        icon_prefix="brush.sculpt.",
        tool_name_attr="sculpt_tool",
        use_paint_attr="use_paint_sculpt",
        tool_settings_attr="sculpt",
        mode="SCULPT",
    )
)


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
