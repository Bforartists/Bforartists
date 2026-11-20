"""
preferences.py — Addon preferences for Ghost Tool.

Stores user-configurable defaults for ghost appearance, colors, and keymaps.
Registered via bpy.types.AddonPreferences so they persist across sessions
and are accessible from Edit > Preferences > Add-ons.
"""

from __future__ import annotations

import bpy

from .utils import log, warn, debug


# ---------------------------------------------------------------------------
# Keymap storage (module-level for clean unregistration)
# ---------------------------------------------------------------------------

_addon_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def _update_display_location(self, context):
    from .ui_panel import schedule_display_location_update
    schedule_display_location_update()


def _update_toolbar_visibility(self, context):
    from .ui_panel import schedule_display_location_update
    schedule_display_location_update(visibility_only=True)


def _update_shelf_width(self, context):
    from .shelf_width import forget_all
    forget_all()


def migrate_display_location(context):
    """Replace the retired header choice without renumbering saved locations."""
    addon = context.preferences.addons.get('ghost_tool')
    prefs = addon.preferences if addon else None
    # RNA returns an empty identifier for saved HEADER=0 after its removal.
    # AddonPreferences does not expose its storage through IDProperty access.
    if prefs is not None and prefs.display_location not in {'TOOLBAR', 'SIDEBAR', 'TOOLS'}:
        prefs.display_location = 'TOOLBAR'
        prefs.show_toolbar = True


# ---------------------------------------------------------------------------
# Addon Preferences
# ---------------------------------------------------------------------------

class GhostToolPreferences(bpy.types.AddonPreferences):
    """User-configurable preferences for the Ghost Tool addon.

    These settings persist across Blender sessions via the preferences
    system.  They control visual appearance, interaction behavior, and
    default keymap assignments.
    """

    bl_idname = "ghost_tool"

    display_location: bpy.props.EnumProperty(
        name="Display Location",
        description="Choose where the full Ghost Tool controls appear in the 3D Viewport",
        items=(
            # Keep the pre-existing RNA numbers: 0 was the retired HEADER.
            ('TOOLBAR', "Top Toolbar", "Keep Ghost Tool in the viewport Tool Settings row", 3),
            ('SIDEBAR', "Right Sidebar (N)", "Show Ghost Tool in the right sidebar", 1),
            ('TOOLS', "Left Tool Shelf (T)", "Show Ghost Tool in the Bforartists left Tool Shelf", 2),
        ),
        default='TOOLBAR',
        update=_update_display_location,
    )  # type: ignore[assignment]

    show_toolbar: bpy.props.BoolProperty(
        name="Show Ghost Toolbar",
        description="Show Ghost controls in the native Tool Settings row; hiding them keeps cached ghosts and settings",
        default=True,
        update=_update_toolbar_visibility,
    )  # type: ignore[assignment]

    auto_widen_shelf: bpy.props.BoolProperty(
        name="Widen Narrow Shelf",
        description="Widen the left Ghost shelf once to match an open right sidebar, or use 240 pixels when closed; keep later manual resizing",
        default=True,
        update=_update_shelf_width,
    )  # type: ignore[assignment]

    show_extended_help: bpy.props.BoolProperty(
        name="Show Extended Help Popups",
        description=(
            "Show Ghost Tool question-mark buttons that open detailed help popups; "
            "native Bforartists hover tooltips are unaffected"
        ),
        default=True,
    )  # type: ignore[assignment]

    # --- Ghost appearance ---

    ghost_radius: bpy.props.FloatProperty(
        name="Ghost Radius",
        description="World-space radius of ghost marker circles",
        default=0.05,
        min=0.005,
        max=1.0,
        precision=3,
    )  # type: ignore[assignment]

    ghost_opacity: bpy.props.FloatProperty(
        name="Ghost Opacity",
        description="Overall opacity of ghost markers",
        default=0.85,
        min=0.1,
        max=1.0,
    )  # type: ignore[assignment]

    # --- Colors per generation level ---

    level_1_color: bpy.props.FloatVectorProperty(
        name="Level 1 Color",
        description="Color for first-generation ghosts",
        subtype='COLOR',
        size=3,
        default=(0.2, 0.7, 1.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    level_2_color: bpy.props.FloatVectorProperty(
        name="Level 2 Color",
        description="Color for second-generation ghosts",
        subtype='COLOR',
        size=3,
        default=(0.3, 1.0, 0.5),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    level_3_color: bpy.props.FloatVectorProperty(
        name="Level 3 Color",
        description="Color for third-generation ghosts",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.8, 0.2),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    level_4_color: bpy.props.FloatVectorProperty(
        name="Level 4 Color",
        description="Color for fourth-generation ghosts",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.4, 0.2),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    level_5_color: bpy.props.FloatVectorProperty(
        name="Level 5 Color",
        description="Color for fifth-generation ghosts",
        subtype='COLOR',
        size=3,
        default=(0.9, 0.2, 0.8),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    # --- Ghost colors (Phase 3) ---

    past_ghost_color: bpy.props.FloatVectorProperty(
        name="Past Ghost Color",
        description="Default color for ghosts before the current frame",
        subtype='COLOR',
        size=3,
        default=(0.25, 0.55, 1.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    future_ghost_color: bpy.props.FloatVectorProperty(
        name="Future Ghost Color",
        description="Default color for ghosts after the current frame",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.55, 0.15),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    key_ghost_color: bpy.props.FloatVectorProperty(
        name="Key Ghost Color",
        description="Default color for ghosts at keyframe positions",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.85, 0.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    inbetween_ghost_color: bpy.props.FloatVectorProperty(
        name="Inbetween Ghost Color",
        description="Default color for ghosts between keyframes",
        subtype='COLOR',
        size=3,
        default=(0.4, 0.75, 1.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    outline_color: bpy.props.FloatVectorProperty(
        name="Outline Color",
        description="Default color for mesh ghost outlines",
        subtype='COLOR',
        size=3,
        default=(0.0, 0.0, 0.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    outline_width: bpy.props.FloatProperty(
        name="Outline Width",
        description="Default width for mesh ghost outlines",
        default=0.002,
        min=0.0005,
        max=0.05,
        precision=4,
    )  # type: ignore[assignment]

    # --- Motion arc ---

    arc_color: bpy.props.FloatVectorProperty(
        name="Arc Color",
        description="Color of the motion arc line",
        subtype='COLOR',
        size=3,
        default=(0.5, 0.5, 0.5),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    arc_line_width: bpy.props.FloatProperty(
        name="Arc Line Width",
        description="Width of the motion arc line in pixels",
        default=2.0,
        min=1.0,
        max=10.0,
    )  # type: ignore[assignment]

    # --- Spacing ticks ---

    tick_cool_color: bpy.props.FloatVectorProperty(
        name="Tick Cool Color",
        description="Color for slow-motion spacing ticks (dense frames)",
        subtype='COLOR',
        size=3,
        default=(0.2, 0.4, 1.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    tick_warm_color: bpy.props.FloatVectorProperty(
        name="Tick Warm Color",
        description="Color for fast-motion spacing ticks (sparse frames)",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.3, 0.1),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    # --- Interaction ---

    default_subdivision_level: bpy.props.IntProperty(
        name="Default Subdivision Level",
        description="Default number of subdivision passes for new ghost generation",
        default=1,
        min=1,
        max=5,
    )  # type: ignore[assignment]

    grab_radius: bpy.props.IntProperty(
        name="Grab Radius",
        description="Screen-space pixel radius for ghost picking",
        default=20,
        min=5,
        max=100,
    )  # type: ignore[assignment]

    default_curve_mode: bpy.props.EnumProperty(
        name="Default Curve Mode",
        description="Default curve shape preservation mode for ghost dragging",
        items=[
            # FREE: Handles move independently (most flexible)
            ("FREE", "Free", "Handles adjust freely"),
            # LOCKED: Both handles rotate together (preserves curve angle)
            ("LOCKED", "Locked", "Handle angle preserved"),
            # SMOOTH: Handles equidistant from control point (even distribution)
            ("SMOOTH", "Smooth", "Handles redistributed evenly"),
        ],
        default="FREE",
    )  # type: ignore[assignment]

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the preferences panel in Edit > Preferences > Add-ons.

        Args:
            context: The current Blender context.
        """
        layout = self.layout

        layout.prop(self, "display_location")
        if self.display_location == 'TOOLBAR':
            layout.prop(self, "show_toolbar")
        elif self.display_location == 'TOOLS':
            layout.prop(self, "auto_widen_shelf")
        from .ui_panel import supports_tool_shelf
        if self.display_location == 'TOOLS' and not supports_tool_shelf():
            layout.label(text="Left Tool Shelf requires Bforartists; using Top Toolbar.", icon='INFO')
        layout.separator()

        help_box = layout.box()
        help_box.label(text="Help", icon='QUESTION')
        help_box.prop(self, "show_extended_help")

        # Ghost appearance section
        box = layout.box()
        box.label(text="Ghost Appearance", icon='GHOST_ENABLED')
        box.prop(self, "ghost_radius")
        box.prop(self, "ghost_opacity")

        # Level colors
        col = box.column(align=True)
        col.prop(self, "level_1_color")
        col.prop(self, "level_2_color")
        col.prop(self, "level_3_color")
        col.prop(self, "level_4_color")
        col.prop(self, "level_5_color")

        # Time-based colors: TIME and KEY_INBETWEEN modes
        box = layout.box()
        box.label(text="Time-Based Colors", icon='TIME')
        # Past/Future colors: distinguish ghosts before vs. after playhead
        row = box.row()
        row.prop(self, "past_ghost_color", text="Past")
        row.prop(self, "future_ghost_color", text="Future")
        # Key/Inbetween colors: distinguish keyframes from interpolated positions
        row = box.row()
        row.prop(self, "key_ghost_color", text="Key")
        row.prop(self, "inbetween_ghost_color", text="Inbetween")

        # Outline defaults
        box = layout.box()
        box.label(text="Outline", icon='MOD_SOLIDIFY')
        box.prop(self, "outline_color")
        box.prop(self, "outline_width")

        # Motion arc section
        box = layout.box()
        box.label(text="Motion Arc", icon='CURVE_PATH')
        box.prop(self, "arc_color")
        box.prop(self, "arc_line_width")

        # Spacing ticks section: visual timing feedback
        box = layout.box()
        box.label(text="Spacing Ticks", icon='TIME')
        # Cool = slow motion (dense frames), Warm = fast motion (sparse frames)
        row = box.row()
        row.prop(self, "tick_cool_color", text="Cool (Slow)")
        row.prop(self, "tick_warm_color", text="Warm (Fast)")

        # Interaction section
        box = layout.box()
        box.label(text="Interaction", icon='CURSOR')
        box.prop(self, "default_subdivision_level")
        box.prop(self, "grab_radius")
        box.prop(self, "default_curve_mode")


# ---------------------------------------------------------------------------
# Keymap Registration
# ---------------------------------------------------------------------------

def register_keymaps() -> None:
    """Register the default hotkeys for ghost operators.

    Assigns Shift+G in Pose Mode and Object Mode for the ghost drag operator.
    Assigns B in Pose Mode and Object Mode for the box select operator.
    """
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return

    # Pose mode keymap
    km = kc.keymaps.new(name='Pose', space_type='VIEW_3D')
    kmi = km.keymap_items.new(
        "ghost_tool.drag_ghost",
        type='G',
        value='PRESS',
        shift=True,
    )
    _addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        "ghost_tool.box_select",
        type='B',
        value='PRESS',
        shift=True,
    )
    _addon_keymaps.append((km, kmi))

    # Object mode keymap
    km = kc.keymaps.new(name='Object Mode', space_type='VIEW_3D')
    kmi = km.keymap_items.new(
        "ghost_tool.drag_ghost",
        type='G',
        value='PRESS',
        shift=True,
    )
    _addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        "ghost_tool.box_select",
        type='B',
        value='PRESS',
        shift=True,
    )
    _addon_keymaps.append((km, kmi))

    log("Keymaps registered (Shift+G for ghost drag, Shift+B for box select)")


def unregister_keymaps() -> None:
    """Remove all addon keymaps."""
    for km, kmi in _addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception as exc:
            warn(f"Failed to remove keymap item: {exc}")
    _addon_keymaps.clear()
    log("Keymaps unregistered")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GhostToolPreferences,
)


def register() -> None:
    """Register preferences and keymaps."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    register_keymaps()
    migrate_display_location(bpy.context)
    from .ui_panel import schedule_display_location_update
    schedule_display_location_update()


def unregister() -> None:
    """Unregister preferences and keymaps."""
    unregister_keymaps()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Preferences appear in Edit > Preferences > Add-ons > Ghost Tool
# >>> # Navigate to the preferences panel
# >>> # All color swatches, sliders, and dropdowns should be visible
#
# Test 2: Keymap assignment
# >>> # In Pose Mode, Shift+G should invoke ghost_tool.drag_ghost
# >>> # Verify via Edit > Preferences > Keymap search
