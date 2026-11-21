"""Where Rig Builder's panels live, and when they draw compact.

Pure Python (no ``bpy``) so it is unit-testable outside Bforartists.
Rig Builder lives only in Properties > Scene tab (owner decision,
2026-10-08): the Scene tab exists whatever is selected, so Rig Builder
is always reachable. ``taskboard/sidebar.py`` applies
:data:`SCENE_PLACEMENT` to the Rig Builder panel classes.
"""

RB_CATEGORY = "Rig Builder"
COMPACT_WIDTH = 220

SCENE_PLACEMENT = {
    "bl_space_type": "PROPERTIES",
    "bl_region_type": "WINDOW",
    "bl_context": "scene",
    "bl_category": "",
}


def is_compact(region_width, ui_scale):
    """True when the region is too narrow for Rig Builder's full layout."""
    return region_width < COMPACT_WIDTH * ui_scale
