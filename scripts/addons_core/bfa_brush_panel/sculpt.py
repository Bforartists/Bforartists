import bpy

from .panels import panel_factory_view3d


panel_classes = list(
    panel_factory_view3d(
        tools=[
            (
                "Draw",  # Panel category (tab)
                "Draw",  # Panel label
                "DRAW",
                "DRAW_SHARP",
            ),
            (
                "Draw",  # Panel category (tab)
                "Clay",  # Panel label
                "CLAY",
                "CLAY_STRIPS",
                "CLAY_THUMB",
            ),
            (
                "Draw",  # Panel category (tab)
                "Layer",  # Panel label
                "LAYER",
            ),
            (
                "Draw",  # Panel category (tab)
                "Inflate",  # Panel label
                "INFLATE",
            ),
            (
                "Draw",  # Panel category (tab)
                "Blob",  # Panel label
                "BLOB",
            ),
            (
                "Draw",  # Panel category (tab)
                "Crease",  # Panel label
                "CREASE",
            ),
            (
                "Surface",  # Panel category (tab)
                "Smooth",  # Panel label
                "SMOOTH",
            ),
            (
                "Surface",  # Panel category (tab)
                "Flatten",  # Panel label
                "FLATTEN",
            ),
            (
                "Surface",  # Panel category (tab)
                "Fill",  # Panel label
                "FILL",
            ),
            (
                "Surface",  # Panel category (tab)
                "Scrape",  # Panel label
                "SCRAPE",
                "MULTIPLANE_SCRAPE",
            ),
            (
                "Deform",  # Panel category (tab)
                "Pinch",  # Panel label
                "PINCH",
            ),
            (
                "Deform",  # Panel category (tab)
                "Grab",  # Panel label
                "GRAB",
            ),
            (
                "Deform",  # Panel category (tab)
                "Elastic Deform",  # Panel label
                "ELASTIC_DEFORM",
            ),
            (
                "Deform",  # Panel category (tab)
                "Snake Hook",  # Panel label
                "SNAKE_HOOK",
            ),
            (
                "Deform",  # Panel category (tab)
                "Thumb",  # Panel label
                "THUMB",
            ),
            (
                "Deform",  # Panel category (tab)
                "Pose",  # Panel label
                "POSE",
            ),
            (
                "Deform",  # Panel category (tab)
                "Nudge",  # Panel label
                "NUDGE",
            ),
            (
                "Deform",  # Panel category (tab)
                "Rotate",  # Panel label
                "ROTATE",
            ),
            (
                "Deform",  # Panel category (tab)
                "Topology",  # Panel label
                "TOPOLOGY",
            ),
            (
                "Deform",  # Panel category (tab)
                "Boundary",  # Panel label
                "BOUNDARY",
            ),
            (
                "Misc",  # Panel category (tab)
                "Cloth",  # Panel label
                "CLOTH",
            ),
            (
                "Misc",  # Panel category (tab)
                "Simplify",  # Panel label
                "SIMPLIFY",
            ),
            (
                "Misc",  # Panel category (tab)
                "Mask",  # Panel label
                "MASK",
            ),
            (
                "Misc",  # Panel category (tab)
                "Draw Face Sets",  # Panel label
                "DRAW_FACE_SETS",
            ),
            (
                "Misc",  # Panel category (tab)
                "Displacement",  # Panel label
                "DISPLACEMENT_ERASER",
                "DISPLACEMENT_SMEAR",
            ),
            (
                "Misc",  # Panel category (tab)
                "Paint",  # Panel label
                "PAINT",
            ),
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
