"""Addon preferences with module toggles and settings I/O hooks."""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from . import constants
from .core.logging import get_logger, set_level
# --- HELP SYSTEM INTEGRATION ---
from .core.help_draw import draw_explainer_icon
from .core.explainers import MODES as EXPLAINER_MODES
from .ui.help_browser import draw_help_browser

_log = get_logger(__name__)


def _update_pie_hotkey(self, _context: bpy.types.Context) -> None:
    from .ui import header_menus
    header_menus.set_pie_hotkey_active(self.pie_hotkey_enabled)


def _update_timeline_quick(_self, context) -> None:
    """Redraw existing Timelines; configuring buttons never changes layout."""
    from .ui.timeline_strip import is_timeline
    ctx = context or bpy.context
    manager = getattr(ctx, "window_manager", None)
    for window in getattr(manager, "windows", ()):
        for area in window.screen.areas:
            if is_timeline(area):
                area.tag_redraw()


def _update_timeline_placement(_self, _context) -> None:
    _self.timeline_canvas_row_initialized = True
    from .ui.timeline_strip import reconcile_preferences
    reconcile_preferences()


def timeline_record(prefs, *, initialize=False):
    """Decode without scene writes; initialize preferences once after enable."""
    from .ui import timeline_config as model
    from .ui.timeline_catalog import ACTIONS, selected_quick_actions, quick_property_name
    if prefs is None:
        return model.recommended(ACTIONS)
    raw=prefs.timeline_layouts_json
    if raw:
        return model.decode(raw,ACTIONS)
    explicit=any(prefs.is_property_set(quick_property_name(action)) for action in ACTIONS)
    record=model.from_legacy(ACTIONS,selected_quick_actions(prefs)) if explicit else model.recommended(ACTIONS)
    if initialize:
        prefs.timeline_layouts_json=model.encode(record,ACTIONS)
    return record


def prepare_timeline_quick_preferences() -> None:
    """Prepare RNA after package imports, before preferences registration."""
    from .ui.timeline_catalog import (
        ACTIONS, DEFAULT_QUICK_ACTIONS, FAMILY, GROUPS, quick_property_name,
    )
    if getattr(AA_AddonPreferences, "is_registered", False):
        return
    annotations = AA_AddonPreferences.__annotations__
    for action, (_suffix, _arguments, label) in ACTIONS.items():
        annotations[quick_property_name(action)] = BoolProperty(
            name=label,
            description=f"Show a quick button beside {FAMILY[action][1]} in the Timeline toolbar",
            default=action in DEFAULT_QUICK_ACTIONS,
            update=_update_timeline_quick,
        )
    annotations["timeline_quick_family"] = EnumProperty(
        name="Family",
        description="Choose the family whose quick-button checkboxes you want to edit",
        items=[(key, label, f"Choose quick buttons for {label}")
               for key, label, _actions in GROUPS],
        default="tween",
    )


def draw_timeline_quick_settings(layout, context, prefs) -> None:
    """Shared quick-selection controls in the tool row and preferences."""
    from .ui.timeline_catalog import GROUPS, quick_property_name
    layout.prop(prefs, "timeline_toolbar_row")
    layout.label(text="Tool row at the bottom of the Timeline", icon="INFO")
    from .ui.timeline_strip import is_timeline
    if is_timeline(context.area):
        from .ui.timeline_overlay import draw_stage_controls
        draw_stage_controls(layout, context)
        layout.label(text="Stage applies to this workspace; layouts are unchanged")
    else:
        layout.label(text="Each workspace picks its stage with the row's stage button")
    layout.label(text="No separate editor or application required")
    layout.label(text="Saved in add-on preferences")
    layout.label(text="Layouts apply to all Timelines")
    layout.operator("animassist.toolbar_settings",text="Toolbar Settings",icon="PREFERENCES")
    layout.operator("animassist.restore_toolbar",text="Restore Recommended Layout",icon="LOOP_BACK")
    layout.label(text="More contains quick tools that do not fit this width")
    if not context.preferences.use_preferences_save:
        layout.label(text="Save Preferences to keep choices after restart", icon="INFO")
        layout.operator("wm.save_userpref", text="Save Preferences", icon="FILE_TICK")


class AA_AddonPreferences(bpy.types.AddonPreferences):
    # ZIP and extension installs may use B4_anim_assist or bl_ext.<repo>.<id>.
    bl_idname = __package__

    timeline_layouts_json: StringProperty(
        name="Toolbar Layout Library",
        description="Saved presentation and slider configurations; no animation or scene state",
        default="", options={"HIDDEN"}, update=_update_timeline_quick,
    )

    debug_mode: BoolProperty(  # type: ignore[valid-type]
        name="Debug Mode",
        description="Enable verbose logging to the console",
        default=False,
        update=lambda self, _ctx: set_level(self.debug_mode),
    )

    performance_mode: BoolProperty(  # type: ignore[valid-type]
        name="Performance Mode",
        description="Reduce UI updates and diagnostics for better performance",
        default=False,
    )

    diagnostics_visible: BoolProperty(  # type: ignore[valid-type]
        name="Show Diagnostics Panel",
        description="Show the diagnostics panel in Properties > Scene > Anim Assist > Help & Diagnostics",
        default=False,
    )

    explainer_mode: EnumProperty(  # type: ignore[valid-type]
        name="Hover Explainers",
        description=(
            "How much Anim Assist explains when the pointer rests on its controls: "
            "Full, Short (name and one line) or Off"
        ),
        items=EXPLAINER_MODES,
        default="FULL",
    )

    # --- HELP SYSTEM INTEGRATION ---
    show_explainer_help: BoolProperty(  # type: ignore[valid-type]
        name="Show Extended Help Popups",
        description=(
            "Show Anim Assist question-mark buttons that open detailed help popups; "
            "native Bforartists hover tooltips are unaffected"
        ),
        default=True,
    )
    compact_ui_mode: BoolProperty(  # type: ignore[valid-type]
        name="Compact UI Mode",
        description=(
            "Draw explainer icons without their neighbouring text labels to "
            "keep sidebar panels dense on small screens"
        ),
        default=False,
    )

    # Operator behaviour toggles (used by curve_tool_ops and anim_offset_ops).
    animassist_fast_offset: BoolProperty(  # type: ignore[valid-type]
        name="Fast Offset Mode",
        description="Only propagate Anim Offset on mouse release (faster for complex rigs)",
        default=False,
    )
    animassist_autokey_outside_margins: BoolProperty(  # type: ignore[valid-type]
        name="Auto-key Outside Margins",
        description="Auto-insert keys for frames outside the mask blend region during Anim Offset",
        default=False,
    )
    animassist_drag_sensitivity: IntProperty(  # type: ignore[valid-type]
        name="Drag Sensitivity",
        description="Mouse pixels needed to reach factor 1.0 in modal drag operators",
        default=200,
        min=10,
        max=2000,
    )

    # Key diagnostics defaults.
    p2_dense_min_gap: FloatProperty(  # type: ignore[valid-type]
        name="Dense Key Min Gap",
        description="Frames below this count as 'too dense' in the diagnostics scan",
        default=1.0,
        min=0.0,
    )
    p2_redundant_tolerance: FloatProperty(  # type: ignore[valid-type]
        name="Redundant Key Tolerance",
        description="Value tolerance for flagging a key as redundant (lies on a line)",
        default=1e-4,
        min=0.0,
    )
    p2_spike_ratio: FloatProperty(  # type: ignore[valid-type]
        name="Spike Ratio",
        description="Neighbour deviation ratio at which a key is flagged as a spike",
        default=4.0,
        min=1.0,
    )

    # Where Anim Assist appears (Properties > Scene > Anim Assist > Settings).
    timeline_canvas_row_initialized: BoolProperty(  # type: ignore[valid-type]
        name="Timeline Row Upgrade Applied",
        description="Remember that existing-header preferences were migrated to the canvas row",
        default=False,
        options={"HIDDEN"},
    )

    timeline_toolbar_row: BoolProperty(  # type: ignore[valid-type]
        name="Timeline Tool Row",
        description=(
            "Show an Anim Assist tool row at the bottom of the Timeline; "
            "uses a narrow band of canvas without resizing or creating editors"
        ),
        default=True,
        update=_update_timeline_placement,
    )
    timeline_paste_offset: FloatProperty(
        name="Paste Frame Offset",
        description="Add this frame offset to the copied absolute key times when pasting",
        default=0.0,
    )
    pie_hotkey_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Anim Assist Pie Menu Hotkey",
        description=(
            "Open the Anim Assist pie with a shortcut in the 3D Viewport, Graph Editor "
            "and Dope Sheet (Shift Alt D unless you change it)"
        ),
        default=False,
        update=_update_pie_hotkey,
    )
    header_menu_view3d: BoolProperty(  # type: ignore[valid-type]
        name="3D Viewport",
        description="Show the Anim Assist menu in the 3D Viewport header",
        default=True,
    )
    header_menu_graph: BoolProperty(  # type: ignore[valid-type]
        name="Graph Editor",
        description="Show the Anim Assist menu in the Graph Editor header",
        default=True,
    )
    header_menu_dopesheet: BoolProperty(  # type: ignore[valid-type]
        name="Dope Sheet",
        description="Show the Anim Assist menu in the Dope Sheet header",
        default=True,
    )

    header_menu_nla: BoolProperty(
        name="NLA Editor", description="Show the Anim Assist menu in the NLA Editor header", default=True,
    )

    # Feature module toggles.
    enable_selection: BoolProperty(name="Selection Tools", description="Enable keyframe and channel selection tools", default=True)  # type: ignore[valid-type]
    enable_keys: BoolProperty(name="Key Utilities", description="Enable key editing and metadata utilities", default=True)  # type: ignore[valid-type]
    enable_transform: BoolProperty(name="Transform Workflows", description="Enable transform and animation offset workflows", default=True)  # type: ignore[valid-type]
    enable_breakdown: BoolProperty(name="Breakdown Tools", description="Enable breakdown, inbetween, and pose comparison tools", default=True)  # type: ignore[valid-type]
    enable_trajectory: BoolProperty(name="Trajectory Tools", description="Enable trajectory overlays and arc diagnostics", default=True)  # type: ignore[valid-type]
    enable_retime: BoolProperty(name="Retime Tools", description="Enable keyframe timing, ripple, and time-warp tools", default=True)  # type: ignore[valid-type]
    enable_controls: BoolProperty(name="Temp Controls", description="Enable temporary proxy and rig control tools", default=True)  # type: ignore[valid-type]
    enable_matching: BoolProperty(name="Matching Workflows", description="Enable transform matching and IK/FK switching tools", default=True)  # type: ignore[valid-type]
    enable_layers: BoolProperty(name="Animation Layers", description="Enable the animation-layer workflow", default=True)  # type: ignore[valid-type]

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        box = layout.box()
        box.label(text="General", icon='PREFERENCES')

        row = box.row(align=True)
        row.prop(self, "debug_mode")
        draw_explainer_icon(row, context, "pref.debug_mode")

        row = box.row(align=True)
        row.prop(self, "performance_mode")
        draw_explainer_icon(row, context, "pref.performance_mode")

        row = box.row(align=True)
        row.prop(self, "diagnostics_visible")
        draw_explainer_icon(row, context, "pref.diagnostics_visible")

        row = box.row(align=True)
        row.label(text="Hover Explainers")
        row.prop(self, "explainer_mode", expand=True)
        draw_explainer_icon(row, context, "pref.explainer_mode")

        # --- EXPLAINER SYSTEM EXTENSION ---
        row = box.row(align=True)
        row.prop(self, "show_explainer_help")
        draw_explainer_icon(row, context, "pref.show_explainer_help")

        row = box.row(align=True)
        row.prop(self, "compact_ui_mode")
        draw_explainer_icon(row, context, "pref.compact_ui_mode")

        box = layout.box()
        box.label(text="Where Anim Assist Appears", icon='WINDOW')
        box.prop(self, "timeline_toolbar_row")
        box.prop(self, "pie_hotkey_enabled")
        col = box.column(heading="Header menu in", align=True)
        col.prop(self, "header_menu_view3d")
        col.prop(self, "header_menu_graph")
        col.prop(self, "header_menu_dopesheet")
        col.prop(self, "header_menu_nla")

        box = layout.box()
        box.label(text="Timeline Quick Tools", icon='PREFERENCES')
        draw_timeline_quick_settings(box, context, self)

        box = layout.box()
        box.label(text="Modules", icon='PACKAGE')
        col = box.column(align=True)
        for key in constants.MODULE_KEYS:
            row = col.row(align=True)
            row.prop(self, f"enable_{key}")
            draw_explainer_icon(row, context, f"pref.enable_{key}")

        box = layout.box()
        box.label(text="Tool Behaviour", icon='TOOL_SETTINGS')

        row = box.row(align=True)
        row.prop(self, "animassist_fast_offset")
        draw_explainer_icon(row, context, "pref.animassist_fast_offset")

        row = box.row(align=True)
        row.prop(self, "animassist_autokey_outside_margins")
        draw_explainer_icon(row, context, "pref.animassist_autokey_outside_margins")

        row = box.row(align=True)
        row.prop(self, "animassist_drag_sensitivity")
        draw_explainer_icon(row, context, "pref.animassist_drag_sensitivity")

        box = layout.box()
        box.label(text="Key Diagnostics", icon='VIEWZOOM')

        row = box.row(align=True)
        row.prop(self, "p2_dense_min_gap")
        draw_explainer_icon(row, context, "pref.p2_dense_min_gap")

        row = box.row(align=True)
        row.prop(self, "p2_redundant_tolerance")
        draw_explainer_icon(row, context, "pref.p2_redundant_tolerance")

        row = box.row(align=True)
        row.prop(self, "p2_spike_ratio")
        draw_explainer_icon(row, context, "pref.p2_spike_ratio")

        box = layout.box()
        box.label(text="Settings", icon='FILE_FOLDER')
        row = box.row(align=True)
        row.operator("anim_assist.export_settings", icon='EXPORT')
        draw_explainer_icon(row, context, "op.anim_assist.export_settings")
        row.operator("anim_assist.import_settings", icon='IMPORT')
        draw_explainer_icon(row, context, "op.anim_assist.import_settings")

        # --- HELP SYSTEM INTEGRATION ---
        draw_help_browser(layout, context)


def get_prefs(context: bpy.types.Context | None = None) -> AA_AddonPreferences | None:
    """Return the addon preferences instance, or *None* if unavailable."""
    ctx = context or bpy.context
    addons = getattr(getattr(ctx, "preferences", None), "addons", None)
    if addons is None:
        return None
    addon = addons.get(__package__) or addons.get(constants.ADDON_PACKAGE)
    if addon is None:
        return None
    return getattr(addon, "preferences", None)
