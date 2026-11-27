"""
ui_panel.py — Ghost Tool native viewport homes and animation header strips.

Preferences choose the full home: viewport header (default), right sidebar,
or Bforartists left Tool Shelf, plus the native Tool Settings row. Feature
popovers and full homes share drawers so their settings stay consistent.
"""

from __future__ import annotations

import textwrap

import bpy

from .ghost_data import AnchorState, DiffReference, GhostStore
from .snapshot import SnapshotStore
from .easing_presets import PRESET_ENUM_ITEMS
from .utils import log, warn, debug, report_failure


# ---------------------------------------------------------------------------
# Easing Settings PropertyGroup (needed by panels)
# ---------------------------------------------------------------------------

class GhostToolEasingSettings(bpy.types.PropertyGroup):
    """Scene-level state for the easing preset selector."""

    active_preset: bpy.props.EnumProperty(
        name="Easing Preset",
        description="Select an easing curve feel to apply between keyframes",
        items=PRESET_ENUM_ITEMS,
        default="EASE_IN_OUT",
    )  # type: ignore[assignment]
    custom_left_x: bpy.props.FloatProperty(
        name="Left Handle X",
        description="Horizontal position of the left keyframe's outgoing handle (0 = at keyframe, 1 = at next keyframe)",
        default=0.33, min=0.0, max=1.0,
    )  # type: ignore[assignment]
    custom_left_y: bpy.props.FloatProperty(
        name="Left Handle Y",
        description="Vertical position of the left keyframe's outgoing handle (0 = flat, positive = overshoot)",
        default=0.0, min=-2.0, max=2.0,
    )  # type: ignore[assignment]
    custom_right_x: bpy.props.FloatProperty(
        name="Right Handle X",
        description="Horizontal position of the right keyframe's incoming handle (0 = at keyframe, -1 = at previous keyframe)",
        default=-0.33, min=-1.0, max=0.0,
    )  # type: ignore[assignment]
    custom_right_y: bpy.props.FloatProperty(
        name="Right Handle Y",
        description="Vertical position of the right keyframe's incoming handle (0 = flat, positive = overshoot)",
        default=0.0, min=-2.0, max=2.0,
    )  # type: ignore[assignment]


_HELP_TOPICS = {
    "overview": (
        "Ghost Tool Workflow",
        "Generate markers, drag them with Shift+G, then refine the resulting animation curves.",
        "Enable Ghost Tools, choose the marker range and subdivision level, and generate markers. "
        "Drag a marker to reshape motion, pin important markers, and use snapshots before larger edits.",
    ),
    "onion_skin": (
        "Onion Skin",
        "Show translucent mesh poses before and after the current frame.",
        "Use onion skins to compare silhouette, spacing, and overlap. Reduce the range or opacity "
        "when the viewport becomes crowded.",
    ),
    "motion_trails": (
        "Motion Trails",
        "Draw the path and timing spacing of animated motion through the viewport.",
        "Arc lines reveal trajectory shape. Spacing ticks reveal acceleration: dense marks indicate "
        "slower movement and wider gaps indicate faster movement.",
    ),
    "marker_placement": (
        "Marker Placement",
        "Choose which frames become editable ghost markers.",
        "Set the frame range and subdivision level before generating. Higher subdivision produces "
        "more editable inbetweens but also creates a denser viewport.",
    ),
    "marker_display": (
        "Marker Display",
        "Control marker colors, size, labels, arcs, and mesh visualization.",
        "Display settings change only viewport presentation; they do not alter animation data. "
        "Use simpler display modes when working with dense shots.",
    ),
    "marker_tools": (
        "Marker Tools",
        "Edit, select, pin, snapshot, ease, and apply physics-shaped motion.",
        "Drag Marker is the main editing action. Choose what happens on confirmation, use falloff "
        "to affect neighbors, and take a snapshot before stamping Physics Feel keys.",
    ),
    "export_import": (
        "Export and Import",
        "Save Ghost Tool marker and snapshot data or restore it later.",
        "Export before transferring a setup or making destructive changes. Import replaces or "
        "reconstructs tool state but does not replace a normal .blend backup.",
    ),
    "settings": (
        "Ghost Tool Settings",
        "Adjust interaction, performance, and viewport behavior for the current scene.",
        "Keep marker counts and display complexity modest for heavy rigs. Add-on-wide visual "
        "defaults and the extended-help switch live in the installed add-on preferences.",
    ),
    "snapshots": (
        "Saved Snapshots",
        "Capture restorable Ghost Tool states before experimenting.",
        "Restore a snapshot to return to its captured curve state, toggle its overlay for comparison, "
        "or delete snapshots that are no longer useful.",
    ),
    "motion_paths": (
        "Motion Paths",
        "Pin a path to any bone or object and watch it follow the playhead.",
        "Add pins the selected bones (Pose mode) or objects. Follow adds a grey path for "
        "whatever is selected. Paths sample the bone itself, so they work with markers off; "
        "turn Markers on to drag keys along a path. A bone path traces its head or its tail: "
        "click H/T in the list to switch. The cube button hides a path behind geometry. "
        "Split colours a path differently before the playhead; Glow marks the path selected "
        "in the list. Range and style apply to all paths; a path can take its own range "
        "in its settings (the colour swatch). Folders and checkboxes organise the list; Apply to "
        "Checked copies the selected path's look. Handles shows each key's Bezier handles: Shift+G or "
        "click an end to drag it (Alt keeps the pair aligned). Draw to Keys turns Annotate strokes into "
        "location keys: the longest stroke is the path, each crossing dash a key.",
    ),
}


def _extended_help_enabled(context: bpy.types.Context) -> bool:
    addons = getattr(getattr(context, "preferences", None), "addons", None)
    addon = addons.get("ghost_tool") if addons is not None else None
    prefs = getattr(addon, "preferences", None)
    return bool(getattr(prefs, "show_extended_help", True))


def _draw_help_icon(layout, context: bpy.types.Context, topic: str) -> None:
    if not _extended_help_enabled(context):
        return
    operator = layout.operator(
        "ghost_tool.show_help_popup",
        text="",
        icon='QUESTION',
        emboss=False,
    )
    operator.topic = topic


class GHOST_OT_show_help_popup(bpy.types.Operator):
    """Display extended help for a Ghost Tool panel."""

    bl_idname = "ghost_tool.show_help_popup"
    bl_label = "Ghost Tool Help"
    bl_description = "Show detailed help for this Ghost Tool section"
    bl_options = {'REGISTER', 'INTERNAL'}

    topic: bpy.props.StringProperty(
        name="Help Topic",
        description="Internal identifier of the Ghost Tool help topic to display",
        default="overview",
    )  # type: ignore[assignment]

    def invoke(self, context, event):
        if self.topic not in _HELP_TOPICS:
            self.report({'WARNING'}, "Help topic not found")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=460)

    def draw(self, context):
        title, summary, details = _HELP_TOPICS[self.topic]
        layout = self.layout
        header = layout.box()
        header.label(text=title, icon='QUESTION')
        for line in textwrap.wrap(summary, width=62):
            header.label(text=line)
        body = layout.box()
        body.label(text="Details", icon='INFO')
        for line in textwrap.wrap(details, width=62):
            body.label(text=line)

    def execute(self, context):
        return {'FINISHED'}


class _GhostHelpPanelMixin:
    help_topic = "overview"

    def draw_header(self, context):
        _draw_help_icon(self.layout, context, self.help_topic)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 1 — THE GHOST TOOL LAYOUT  (one layout, three hosts)          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Ghost Tool has no 3D Viewport sidebar tab. It lives in the viewport header:
# an on/off ghost toggle and a "Ghost Tool" dropdown next to the Pose menu.
# The same layout also fills the floating toolbar and a separate window (a
# second viewport whose sidebar shows only Ghost Tool), for when a dropdown
# that closes on click-away is not enough.
#
# Groups follow the order you work in: show ghosts, onion skin, edit motion,
# compare, physics, look, settings.


def _row_label(layout, text: str, icon: str = 'NONE') -> None:
    row = layout.row()
    row.enabled = False
    row.label(text=text, icon=icon)


def _wrapped_label(layout, context, text: str, icon: str = 'NONE') -> None:
    """Keep the full target readable in narrow native panels and popovers."""
    region = getattr(context, 'region', None)
    width = getattr(region, 'width', 300) or 300
    # Native popovers retain the invoking viewport's WINDOW context, so
    # region.width is not their content width. Keep that route readable
    # at the smallest supported 12-unit review popover.
    if getattr(region, 'type', None) == 'WINDOW':
        width = min(width, 280)
    scale = getattr(getattr(getattr(context, 'preferences', None), 'view', None), 'ui_scale', 1.0)
    columns = max(16, min(64, int(width / (7.0 * scale)) - 8))
    for index, line in enumerate(textwrap.wrap(text, width=columns, break_long_words=True,
                                               break_on_hyphens=False) or ['']):
        layout.label(text=line, icon=icon if index == 0 else 'NONE')


def _options_fold(layout, key):
    try:
        header, body = layout.panel(key, default_closed=True)
    except (AttributeError, TypeError, ValueError):
        return layout.column()
    header.label(text="Options")
    return body


def _marker_target_bones(context):
    obj = context.active_object
    bones = []
    if obj is not None and obj.type == 'ARMATURE' and obj.pose:
        bones = [b.name for b in (getattr(context, 'selected_pose_bones', None) or [])]
        if not bones:
            bones = [b.name for b in obj.pose.bones if getattr(b.bone, 'select', False)]
        if not bones:
            bones = [b.name for b in obj.pose.bones]
    return bones


def _marker_target_text(context, *, compact=False):
    obj = context.active_object
    if obj is None:
        return "Target: select an animated object or pose bones"
    bones = _marker_target_bones(context)
    detail = f"{len(bones)} {'bone' if len(bones) == 1 else 'bones'}" if compact else ", ".join(bones)
    suffix = " / " + detail if bones else ""
    return "Markers: " + obj.name + suffix


def _snapshot_target_text(snapshot, *, compact=False):
    if compact:
        objects = len(snapshot.object_names)
        bones = len(snapshot.bone_names)
        text = f"Targets: {objects} {'object' if objects == 1 else 'objects'}"
        if bones:
            text += f", {bones} {'bone' if bones == 1 else 'bones'}"
        return text
    objects = ", ".join(sorted(snapshot.object_names)) or "No captured objects"
    bones = ", ".join(sorted(snapshot.bone_names))
    return "Targets: " + objects + (" / Bones: " + bones if bones else "")


def _draw_show_ghosts(layout, context, *, options_only=False) -> None:
    settings = context.scene.ghost_tool
    layout.prop(settings, "show_cached_markers", text="Show cached markers")
    _wrapped_label(layout, context, _marker_target_text(context, compact=True))
    if not options_only:
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("ghost_tool.generate_ghosts", text="Show Markers", icon='GHOST_ENABLED')
        row.operator("ghost_tool.clear_ghosts", text="", icon='TRASH')
    else:
        layout.operator("ghost_tool.clear_ghosts", text="Clear All Ghosts", icon='TRASH')
    _row_label(layout, "Location + rotation keys")

    if _marker_target_bones(context):
        header, targets = layout.panel('ghost_marker_targets', default_closed=True)
        header.label(text="Marker Targets")
        if targets is not None:
            _wrapped_label(targets, context, _marker_target_text(context))

    # The dedicated options drawer already provides the enclosing boundary;
    # its settings need no extra closed "Options" fold. Target fold keys are
    # shared with the full homes and retain independent state.
    if not options_only:
        layout = _options_fold(layout, 'ghost_marker_sampling_options')
    if layout is None:
        return

    col = layout.column(align=True)
    col.label(text="Frames")
    col.prop(settings, "ghost_range_mode", text="")
    if settings.ghost_range_mode == "AROUND_CURSOR":
        row = col.row(align=True)
        row.prop(settings, "ghosts_before", text="Before")
        row.prop(settings, "ghosts_after", text="After")
    elif settings.ghost_range_mode == "CUSTOM":
        row = col.row(align=True)
        row.prop(settings, "custom_range_start", text="Start")
        row.prop(settings, "custom_range_end", text="End")

    col = layout.column(align=True)
    col.label(text="Marker every")
    col.prop(settings, "ghost_mode", text="")
    if settings.ghost_mode == "FRAME_STEP":
        col.prop(settings, "frame_step", text="Frames")
    elif settings.ghost_mode == "SUBDIVISION":
        col.prop(settings, "subdivision_level", text="Detail", slider=True)

    col = layout.column(align=True)
    col.prop(settings, "live_point_ghosts", text="Live Update Markers")
    if settings.is_active:
        row = col.row(align=True)
        row.prop(settings, "live_freeze", text="Freeze", toggle=True,
                 icon='SNAP_ON' if settings.live_freeze else 'SNAP_OFF')
        row.prop(settings, "live_throttle_ms", text="Delay")


def _draw_onion_skin(layout, context, *, options_only=False) -> None:
    settings = context.scene.ghost_tool
    layout.prop(settings, "show_cached_skin", text="Show cached skin")
    if not options_only:
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("ghost_tool.generate_mesh_ghosts", text="Show Onion Skin", icon='MESH_DATA')
        row.operator("ghost_tool.clear_mesh_ghosts", text="", icon='TRASH')
    else:
        layout.operator("ghost_tool.clear_mesh_ghosts", text="Clear Onion Skin", icon='TRASH')
    from .mesh_ghosts import pinned_ghost_sources
    pinned = pinned_ghost_sources(context.scene)
    if pinned:
        names = ", ".join(obj.name for obj in pinned[:3]) + (", ..." if len(pinned) > 3 else "")
        _row_label(layout, f"Following {names}", icon='PINNED')
    else:
        _row_label(layout, "Every mesh or curve of each selected character")

    row = layout.row(align=True)
    row.prop(settings, "mesh_ghost_mode", expand=True)
    row.prop(settings, "mesh_ghost_xray", text="", toggle=True, icon='XRAY')

    col = layout.column(align=True)
    col.label(text="Frames")
    col.prop(settings, "mesh_ghost_frame_mode", text="")
    if settings.mesh_ghost_frame_mode == 'KEYFRAMES':
        col.prop(settings, "mesh_ghost_keyframe_skip", text="Every")
        if settings.mesh_ghost_keyframe_skip == 'CUSTOM':
            col.prop(settings, "mesh_ghost_keyframe_skip_custom", text="Every Nth")
    else:
        col.prop(settings, "mesh_ghost_step", text="Step")
    row = col.row(align=True)
    row.prop(settings, "mesh_ghost_past_count", text="Before")
    row.prop(settings, "mesh_ghost_future_count", text="After")

    col = layout.column(align=True)
    col.label(text="Fade")
    col.prop(settings, "mesh_ghost_opacity", text="Opacity", slider=True)
    col.prop(settings, "mesh_ghost_falloff", text="")

    col = layout.column(align=True)
    row = col.row(align=True)
    row.prop(settings, "show_mesh_past", text="Before", toggle=True,
             icon='REW' if settings.show_mesh_past else 'BLANK1')
    row.prop(settings, "show_mesh_future", text="After", toggle=True,
             icon='FF' if settings.show_mesh_future else 'BLANK1')
    col.prop(settings, "mesh_ghost_past_color", text="Before")
    col.prop(settings, "mesh_ghost_future_color", text="After")

    col = layout.column(align=True)
    col.prop(settings, "ghost_outline_enabled", text="Outline", toggle=True, icon='MOD_SOLIDIFY')
    if settings.ghost_outline_enabled:
        col.prop(settings, "ghost_outline_width", text="Width")
        col.prop(settings, "ghost_outline_color", text="")
    layout.prop(settings, "live_mesh_ghosts", text="Live Update Skin")


def _draw_edit_motion(layout, context) -> None:
    scene = context.scene
    settings = scene.ghost_tool
    store = GhostStore.get(scene)

    selected = store.get_selected()
    if selected:
        _wrapped_label(layout, context, "Selected markers: " + ", ".join(sorted({g.object_name for g in selected})))
    else:
        _wrapped_label(layout, context, "Drag target: the marker you pick in this viewport")

    row = layout.row()
    row.scale_y = 1.4
    _draw_marker_drag_button(row, text="Drag Marker  (Shift G)", icon='ORIENTATION_CURSOR')
    row = layout.row(align=True)
    row.operator("ghost_tool.select_ghost", text="Select", icon='RESTRICT_SELECT_OFF')
    row.operator("ghost_tool.box_select", text="Box Select", icon='SELECT_SET')

    col = layout.column(align=True)
    col.label(text="When you let go")
    col.prop(settings, "editing_mode", text="")
    if settings.editing_mode == 'RESHAPE':
        col.prop(settings, "curve_mode", text="")
    else:
        col.prop(settings, "smooth_neighbors_on_commit", text="Smooth Neighbours",
                 toggle=True, icon='MOD_SMOOTH')

    col = layout.column(align=True)
    col.label(text="Also move nearby frames")
    row = col.row(align=True)
    row.prop(settings, "sculpt_falloff_radius", text="Reach")
    sub = row.row(align=True)
    sub.enabled = settings.sculpt_falloff_radius > 0
    sub.prop(settings, "sculpt_falloff_curve", text="")

    if hasattr(scene, 'ghost_tool_easing'):
        easing = scene.ghost_tool_easing
        col = layout.column(align=True)
        col.label(text="Easing")
        col.prop(easing, "active_preset", text="")
        op = col.operator("ghost_tool.apply_easing", text="Apply Easing", icon='IPO_EASE_IN_OUT')
        op.preset = easing.active_preset
        for name in ("custom_left_x", "custom_left_y", "custom_right_x", "custom_right_y"):
            setattr(op, name, getattr(easing, name))
        if easing.active_preset == "CUSTOM":
            row = col.row(align=True)
            row.prop(easing, "custom_left_x", text="L.X")
            row.prop(easing, "custom_left_y", text="L.Y")
            row = col.row(align=True)
            row.prop(easing, "custom_right_x", text="R.X")
            row.prop(easing, "custom_right_y", text="R.Y")

    row = layout.row()
    row.operator("ghost_tool.paths_draw_to_keys", text="Draw to Keys…", icon='GREASEPENCIL')

    col = layout.column(align=True)
    col.label(text=f"Pinned markers: {len(store.get_pinned())}")
    row = col.row(align=True)
    row.operator("ghost_tool.pin_ghost", text="Pin", icon='PINNED')
    row.operator("ghost_tool.unpin_all", text="Unpin All", icon='UNPINNED')


def _draw_compare(layout, context) -> None:
    scene = context.scene
    settings = scene.ghost_tool
    snapshots = SnapshotStore.get(scene).get_all()

    col = layout.column(align=True)
    col.label(text=f"Saved snapshots ({len(snapshots)}/10)")
    from .target_binding import capture_label
    col.prop(scene, 'ghost_snapshot_scope', text='Scope')
    capture_summary = capture_label(context, compact=True)
    capture_details = capture_label(context)
    _wrapped_label(col, context, capture_summary)
    col.operator("ghost_tool.take_snapshot", text="Save Snapshot", icon='CAMERA_DATA')
    _wrapped_label(col, context, 'Saved with this blend file. Export JSON to transfer references.')
    store = SnapshotStore.get(scene)
    if store.storage_error:
        _wrapped_label(col, context, store.storage_error, icon='ERROR')
    if len(snapshots) >= 10:
        _wrapped_label(col, context, 'Capacity reached. Delete unwanted references before saving another.', icon='INFO')
    if not snapshots:
        _row_label(col, "Save a state before big edits")
    if capture_details != capture_summary:
        header, targets = layout.panel('ghost_capture_targets', default_closed=True)
        header.label(text='Capture Targets')
        if targets is not None:
            _wrapped_label(targets, context, capture_details)
    for snap in snapshots:
        card = layout.box()
        _wrapped_label(card, context, snap.name)
        if snap.parent_uid:
            _wrapped_label(card, context, 'Variant of: ' + snap.origin.get('name', 'Original reference'))
        reason = SnapshotStore.binding_reason(snap, scene)
        target_text = ('Targets: ' + ', '.join(sorted({b.summary() for b in snap.bindings}))) if snap.bindings and not reason else _snapshot_target_text(snap)
        _wrapped_label(card, context, _snapshot_target_text(snap, compact=True))
        if reason:
            _wrapped_label(card, context, reason, icon='ERROR')
            target_name = context.active_object.name if context.active_object else '(select a target)'
            _wrapped_label(card, context, 'Bind to: ' + target_name)
            card.operator('ghost_tool.bind_snapshot', text='Bind to Active Target').snapshot_uid = snap.uid
        missing = sorted(name for name in snap.object_names if scene.objects.get(name) is None)
        _wrapped_label(card, context, "Restore: complete captured curves" if snap.curve_data else "Restore: legacy sampled values")
        row = card.row(align=True)
        op = row.operator("ghost_tool.toggle_snapshot", text="Hide" if snap.is_visible else "Show",
                          icon='HIDE_OFF' if snap.is_visible else 'HIDE_ON')
        # One named action per row also remains readable in narrow panels.
        op.snapshot_uid = snap.uid
        op = card.row().operator("ghost_tool.restore_snapshot", text="Restore", icon='LOOP_BACK')
        op.snapshot_uid = snap.uid
        card.row().operator('ghost_tool.save_variant', text='Save Variant').parent_uid = snap.uid
        op = card.row().operator("ghost_tool.delete_snapshot", text="Delete", icon='TRASH')
        op.snapshot_uid = snap.uid
        header, targets = layout.panel(f'ghost_snapshot_targets_{snap.uid}', default_closed=True)
        header.label(text='Snapshot Targets')
        if targets is not None:
            _wrapped_label(targets, context, target_text)
            if missing and reason:
                _wrapped_label(targets, context, "Unavailable: " + ", ".join(missing), icon='ERROR')

    col = layout.column(align=True)
    col.label(text="Compare to a pose")
    col.prop(settings, "show_diff_overlay", text="Colour Bones by Change")
    row = col.row(align=True)
    row.operator("ghost_tool.pin_diff_reference", text="Set Reference", icon='PINNED')
    row.operator("ghost_tool.unpin_diff_reference", text="", icon='X')
    if settings.show_diff_overlay:
        diff_ref = DiffReference.get(scene)
        if diff_ref is None:
            _row_label(col, "No reference set", icon='INFO')
        else:
            is_stale = diff_ref.state == AnchorState.STALE
            col.label(text=f"Frame {diff_ref.anchor_frame}: {'stale' if is_stale else 'live'}",
                      icon='ERROR' if is_stale else 'CHECKMARK')
        col.prop(settings, "diff_max_distance", text="Max Distance")
        row = col.row(align=True)
        row.prop(settings, "diff_cool_color", text="")
        row.prop(settings, "diff_warm_color", text="")


def _draw_physics(layout, context) -> None:
    settings = context.scene.ghost_tool
    layout.operator("ghost_tool.physics_suggest", text="Suggest Physics Arc", icon='FORCE_FORCE')

    col = layout.column(align=True)
    col.prop(settings, "show_ballistic_preview", text="Show Throw Path", toggle=True, icon='FORCE_HARMONIC')
    if settings.show_ballistic_preview:
        row = col.row(align=True)
        row.prop(settings, "ballistic_gravity", text="Gravity")
        row.prop(settings, "ballistic_gravity_axis", text="")
        col.prop(settings, "ballistic_offset", text="Offset")

    col = layout.column(align=True)
    col.label(text="Physics feel")
    row = col.row(align=True)
    row.prop(settings, "archetype_active", text="")
    row.prop(settings, "show_archetype_preview", text="", toggle=True,
             icon='HIDE_OFF' if settings.show_archetype_preview else 'HIDE_ON')
    if settings.show_archetype_preview:
        row = col.row(align=True)
        row.prop(settings, "archetype_amplitude", text="Amplitude")
        row.prop(settings, "archetype_axis", text="")
        row = col.row(align=True)
        row.prop(settings, "archetype_start_frame", text="Start")
        row.prop(settings, "archetype_end_frame", text="End")
        col.operator("ghost_tool.archetype_bake", text="Stamp to Keys", icon='KEYFRAME_HLT')


def _draw_look(layout, context) -> None:
    scene = context.scene
    settings = scene.ghost_tool
    store = GhostStore.get(scene)

    col = layout.column(align=True)
    col.label(text="Colour markers by")
    col.prop(settings, "ghost_color_mode", text="")
    if settings.ghost_color_mode == "TIME":
        col.prop(settings, "ghost_past_color", text="Before")
        col.prop(settings, "ghost_future_color", text="After")
    elif settings.ghost_color_mode == "KEY_INBETWEEN":
        col.prop(settings, "ghost_key_color", text="Key")
        col.prop(settings, "ghost_inbetween_color", text="Inbetween")
    if settings.ghost_color_mode != "LEVEL":
        col.prop(settings, "ghost_fade_factor", text="Fade Distance", slider=True)
        col.prop(settings, "ghost_falloff_curve", text="")
        col.prop(settings, "ghost_min_alpha", text="Min Opacity", slider=True)

    col = layout.column(align=True)
    col.label(text="Show on the path")
    row = col.row(align=True)
    row.prop(settings, "show_arc_lines", text="Arc Lines", toggle=True, icon='CURVE_PATH')
    if settings.show_arc_lines:
        row.prop(settings, "arc_line_style", text="")
    col.prop(settings, "show_spacing_ticks", text="Spacing Ticks", toggle=True, icon='TIME')
    col.prop(settings, "show_acceleration_markers", text="Speed-up / Slow-down", toggle=True,
             icon='FORCE_TURBULENCE')
    col.prop(settings, "show_keyframe_markers", text="Keyframe Diamonds", toggle=True, icon='KEYFRAME_HLT')
    if settings.show_keyframe_markers:
        col.prop(settings, "keyframe_marker_color", text="")
    col.prop(settings, "show_key_bookends", text="Key Bookends", toggle=True, icon='KEYFRAME')
    if settings.show_key_bookends:
        col.prop(settings, "key_bookend_color", text="")
    col.prop(settings, "show_frame_numbers", text="Frame Numbers", toggle=True, icon='FONT_DATA')
    if settings.show_frame_numbers:
        col.prop(settings, "ghost_label_color", text="")
    col.prop(settings, "show_hover_frame_label", text="Frame Under Mouse", toggle=True, icon='FONT_DATA')
    if settings.show_hover_frame_label:
        col.prop(settings, "hover_highlight_color", text="")

    if settings.ghost_mode == "SUBDIVISION":
        row = layout.row(align=True)
        row.label(text="Levels")
        for level in range(1, 6):
            count = store.count_by_level(level)
            icon_lv = 'LAYER_ACTIVE' if settings.is_level_visible(level) else 'LAYER_USED'
            row.prop(settings, f"show_level_{level}", text=str(level), toggle=True,
                     icon=icon_lv if count > 0 else 'BLANK1')


def _draw_settings(layout, context) -> None:
    settings = context.scene.ghost_tool
    layout.prop(settings, "grab_radius", text="Grab Radius (px)", icon='CURSOR')
    col = layout.column(align=True)
    col.prop(settings, "use_custom_range", text="Limit to a Frame Range")
    if settings.use_custom_range:
        row = col.row(align=True)
        row.prop(settings, "custom_range_start", text="Start")
        row.prop(settings, "custom_range_end", text="End")
    row = layout.row(align=True)
    row.operator("ghost_tool.export_ghosts", text="Export", icon='EXPORT')
    row.operator("ghost_tool.import_ghosts", text="Import", icon='IMPORT')


def _row_icon(entry, is_active: bool) -> str:
    """Kind icon of a path row; the active bone's or object's row gets a dot instead."""
    if is_active:
        return 'RADIOBUT_ON'
    if entry.vertex_index >= 0:
        return 'VERTEXSEL'
    return 'BONE_DATA' if entry.bone_name else 'OBJECT_DATA'


class GHOST_UL_paths(bpy.types.UIList):
    bl_idname = "GHOST_UL_paths"

    def filter_items(self, context, data, propname):
        """List order and visibility come from motion_paths.list_rows: top-level paths, then each
        folder with its paths; a collapsed folder's paths are filtered out."""
        from .motion_paths import list_rows
        count = len(getattr(data, propname))
        flags, order = [0] * count, [0] * count
        for position, (index, shown) in enumerate(list_rows(data)):
            flags[index] = self.bitflag_filter_item if shown else 0
            order[index] = position   # Blender wants each item's new position, indexed by the item
        return flags, order

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        from .motion_paths import active_entry_index, entry_is_missing, folder_rows
        row = layout.row(align=True)
        row.prop(item, "checked", text="")
        if item.is_folder:
            fold = row.operator("ghost_tool.paths_toggle_folder", text="", emboss=False,
                                icon='RIGHTARROW' if item.collapsed else 'DOWNARROW_HLT')
            fold.index = index
            op = row.operator("ghost_tool.paths_toggle_visible", text="", emboss=False,
                              icon='HIDE_OFF' if item.visible else 'HIDE_ON')
            op.action, op.index = 'ONE', index
            row.prop(item, "object_name", text="", emboss=False, icon='FILE_FOLDER')
            rm = row.operator("ghost_tool.paths_remove", text="", icon='X', emboss=False)
            rm.index = index
            return
        if item.folder and item.folder in folder_rows(data):
            row.label(text="", icon='BLANK1')   # indent: this path is in the folder above it
        op = row.operator("ghost_tool.paths_toggle_visible", text="", emboss=False,
                          icon='HIDE_OFF' if item.visible else 'HIDE_ON')
        op.action, op.index = 'ONE', index
        swatch = row.operator("ghost_tool.paths_set_color", text="", icon='COLOR', emboss=False)
        swatch.index = index
        missing = entry_is_missing(item)
        sub = row.row(); sub.enabled = not missing
        sub.label(text=item.label + ("  (missing)" if missing else ""),
                  icon=_row_icon(item, index == active_entry_index(context)))
        if item.bone_name:
            flip = row.row(align=True)
            flip.operator_context = 'EXEC_DEFAULT'   # one click flips; no dialog
            anchor = flip.operator("ghost_tool.paths_set_color", text="T" if item.anchor == 'TAIL' else "H",
                                   emboss=False)
            anchor.index, anchor.anchor = index, 'HEAD' if item.anchor == 'TAIL' else 'TAIL'
        front = row.operator("ghost_tool.paths_toggle_front", text="", emboss=False,
                             icon='XRAY' if item.in_front else 'MESH_CUBE')
        front.action, front.index = 'ONE', index
        rm = row.operator("ghost_tool.paths_remove", text="", icon='X', emboss=False)
        rm.index = index


class GHOST_MT_paths_checked(bpy.types.Menu):
    bl_idname = "GHOST_MT_paths_checked"
    bl_label = "Checked"
    bl_description = "Actions on the checked rows of the motion path list"

    def draw(self, context):
        layout = self.layout
        for action, label, icon in (('SHOW', "Show", 'HIDE_OFF'), ('HIDE', "Hide", 'HIDE_ON'),
                                    ('RESET_RANGE', "Reset Range", 'LOOP_BACK'), ('REMOVE', "Remove", 'X')):
            layout.operator("ghost_tool.paths_checked_action", text=label, icon=icon).action = action
        layout.menu("GHOST_MT_paths_move_to", icon='FILE_FOLDER')
        layout.separator()
        layout.operator("ghost_tool.paths_apply_to_checked", text="Apply to Checked with Range",
                        icon='PASTEDOWN').include_range = True


class GHOST_MT_paths_move_to(bpy.types.Menu):
    bl_idname = "GHOST_MT_paths_move_to"
    bl_label = "Move to Folder"
    bl_description = "Move the checked paths into a folder, or to the top level"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("ghost_tool.paths_checked_action", text="Top Level", icon='TRIA_UP')
        op.action, op.folder = 'MOVE', ""
        for entry in context.scene.ghost_tool.motion_paths:
            if entry.is_folder:
                op = layout.operator("ghost_tool.paths_checked_action", text=entry.object_name, icon='FILE_FOLDER')
                op.action, op.folder = 'MOVE', entry.folder_key


def _range_props(settings) -> tuple[str, ...]:
    """The frame fields the chosen range mode needs."""
    if settings.paths_range_mode == 'AROUND_CURSOR':
        return ("paths_before", "paths_after")
    if settings.paths_range_mode == 'CUSTOM':
        return ("custom_range_start", "custom_range_end")
    return ()


def _draw_motion_paths(layout, context) -> None:
    settings = context.scene.ghost_tool
    row = layout.row(align=True)
    row.scale_y = 1.2
    row.operator("ghost_tool.paths_add_selected", text="Add Path for Selected", icon='ADD')
    row = layout.row(align=True)
    row.label(text=f"Motion paths · {sum(1 for e in settings.motion_paths if not e.is_folder)}")
    row.operator("ghost_tool.paths_toggle_visible", text="All on").action = 'ALL_ON'
    row.operator("ghost_tool.paths_toggle_visible", text="All off").action = 'ALL_OFF'
    row.operator("ghost_tool.paths_clear", text="", icon='TRASH')
    row = layout.row(align=True)
    row.operator("ghost_tool.paths_toggle_front", text="All in front", icon='XRAY').action = 'ALL_ON'
    row.operator("ghost_tool.paths_toggle_front", text="All behind", icon='MESH_CUBE').action = 'ALL_OFF'
    row = layout.row(align=True)
    row.operator("ghost_tool.paths_add_folder", text="Add Folder", icon='NEWFOLDER')
    row.operator("ghost_tool.paths_apply_to_checked", text="Apply to Checked", icon='PASTEDOWN')
    row.menu("GHOST_MT_paths_checked", text="Checked")
    layout.template_list("GHOST_UL_paths", "", settings, "motion_paths", settings, "motion_paths_index", rows=4, maxrows=8)
    col = layout.column(align=True)
    col.label(text="Range")
    col.prop(settings, "paths_range_mode", text="")
    fields = _range_props(settings)
    if fields:
        row = col.row(align=True)
        for name, label in zip(fields, ("Before", "After") if fields[0] == "paths_before" else ("Start", "End")):
            row.prop(settings, name, text=label)
    col.prop(settings, "paths_step", text="Every")
    col = layout.column(align=True)
    col.label(text="Style")
    col.prop(settings, "paths_style", expand=True)
    row = layout.row(align=True)
    row.prop(settings, "paths_show_markers", text="Markers", toggle=True)
    row.prop(settings, "paths_show_key_dots", text="Key dots", toggle=True)
    row.prop(settings, "paths_show_frame_numbers", text="Frame #", toggle=True)
    row.prop(settings, "paths_active_glow", text="Glow", toggle=True)
    row.prop(settings, "paths_show_handles", text="Handles", toggle=True)
    layout.operator("ghost_tool.paths_draw_to_keys", text="Draw to Keys…", icon='GREASEPENCIL')
    layout.operator("ghost_tool.path_handle_drag", text="Drag Path Handle", depress=_path_handle_drag_mode_active()).wait_for_click = True


#: (key, label, icon, draw function, help topic, open by default)
GHOST_SECTIONS: tuple = (
    ("show", "Show Ghosts", 'GHOST_ENABLED', _draw_show_ghosts, "marker_placement", True),
    ("onion", "Onion Skin", 'MESH_DATA', _draw_onion_skin, "onion_skin", False),
    ("paths", "Motion Paths", 'CURVE_PATH', _draw_motion_paths, "motion_paths", False),
    ("edit", "Edit Motion", 'ORIENTATION_CURSOR', _draw_edit_motion, "marker_tools", False),
    ("compare", "Compare", 'ARROW_LEFTRIGHT', _draw_compare, "snapshots", False),
    ("physics", "Physics", 'FORCE_FORCE', _draw_physics, "marker_tools", False),
    ("look", "Look", 'HIDE_OFF', _draw_look, "marker_display", False),
    ("settings", "Settings", 'PREFERENCES', _draw_settings, "settings", False),
)


def draw_ghost_tool(layout, context, prefix: str) -> None:
    """The whole Ghost Tool layout: status or welcome, then the collapsible groups."""
    scene = context.scene
    if not hasattr(scene, 'ghost_tool'):
        box = layout.box()
        box.label(text="Ghost Tool not initialized", icon='ERROR')
        box.operator("ghost_tool.initialize", text="Initialize Ghost Tool", icon='SETTINGS')
        return
    settings = scene.ghost_tool
    try:
        store = GhostStore.get(scene)
    except Exception as exc:
        box = layout.box()
        box.label(text="Ghost Tool: initialization error", icon='ERROR')
        box.label(text=str(exc)[:80])
        return

    if not settings.is_active:
        _row_label(layout, "Trace your animation's path")
        _row_label(layout, "and drag it to reshape motion")
        row = layout.row()
        row.scale_y = 1.5
        row.prop(settings, "is_active", text="Turn On Ghosts", toggle=True, icon='GHOST_ENABLED')
        return

    row = layout.row(align=True)
    row.label(text=f"{len(store)} markers, {len(store.get_pinned())} pinned", icon='GHOST_ENABLED')
    _draw_help_icon(row, context, "overview")
    for key, label, icon, draw, topic, is_open in GHOST_SECTIONS:
        header, body = layout.panel(f"ghost_tool_{prefix}_{key}", default_closed=not is_open)
        header.label(text=label, icon=icon)
        _draw_help_icon(header, context, topic)
        if body is None:
            continue
        try:
            draw(body, context)
        except Exception as exc:
            warn(f"Ghost Tool: could not draw {label}: {exc}")
            body.label(text="This section could not draw", icon='ERROR')


class GHOST_PT_paths_popover(bpy.types.Panel):
    bl_idname = "GHOST_PT_paths_popover"
    bl_label = "Motion Paths"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 18   # 3.6 rows carry a checkbox and an indent; at 14 names were cut to "Rig › ..."

    def draw(self, context):
        _draw_motion_paths(self.layout, context)

    @classmethod
    def poll(cls, context):
        return _feature_context(context)


def _feature_context(context):
    """Keep settings reachable when only a generation target is unavailable."""
    from .settings_editor import is_editor
    window = getattr(context, 'window', None)
    return (hasattr(getattr(context, 'scene', None), 'ghost_tool')
            and (window is None or window.as_pointer() not in _ghost_windows)
            and not is_editor(context))


class _GhostFeaturePopover:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 18
    section_key = ''

    @classmethod
    def poll(cls, context):
        return _feature_context(context)

    def draw(self, context):
        for key, _label, _icon, draw, _topic, _open in GHOST_SECTIONS:
            if key == self.section_key:
                if key in {'show', 'onion'}:
                    draw(self.layout, context, options_only=True)
                else:
                    draw(self.layout, context)
                return


class GHOST_PT_marker_options(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_marker_options'
    bl_label = 'Marker options'
    bl_description = 'Marker options: show or hide cached markers and choose targets and sampling'
    section_key = 'show'


class GHOST_PT_skin_options(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_skin_options'
    bl_label = 'Onion Skin options'
    bl_description = 'Onion Skin options: show or hide cached skin and choose sampling and appearance'
    section_key = 'onion'


class GHOST_PT_edit_popover(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_edit_popover'
    bl_label = 'Edit Motion'
    section_key = 'edit'


class GHOST_PT_compare_popover(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_compare_popover'
    bl_label = 'Compare'
    section_key = 'compare'


class GHOST_PT_physics_popover(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_physics_popover'
    bl_label = 'Physics'
    section_key = 'physics'


class GHOST_PT_look_popover(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_look_popover'
    bl_label = 'Look'
    section_key = 'look'


class GHOST_PT_settings_popover(_GhostFeaturePopover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_settings_popover'
    bl_label = 'Settings'
    section_key = 'settings'


_FEATURE_PANELS = {
    'show': 'GHOST_PT_marker_options', 'onion': 'GHOST_PT_skin_options',
    'paths': 'GHOST_PT_paths_popover', 'edit': 'GHOST_PT_edit_popover',
    'compare': 'GHOST_PT_compare_popover', 'physics': 'GHOST_PT_physics_popover',
    'look': 'GHOST_PT_look_popover', 'settings': 'GHOST_PT_settings_popover',
}


def _draw_feature_destination(layout, key, label, icon):
    layout.popover(panel=_FEATURE_PANELS[key], text=label, icon=icon)


def _draw_generation_pair(layout, key):
    """Only the operator polls its target; the adjacent options stay enabled."""
    row = layout.row(align=True)
    marker = key == 'show'
    row.operator('ghost_tool.generate_ghosts' if marker else 'ghost_tool.generate_mesh_ghosts',
                 text='Show Markers' if marker else 'Show Onion Skin',
                 icon='GHOST_ENABLED' if marker else 'MESH_DATA')
    row.popover(panel=_FEATURE_PANELS[key],
                text='Marker options' if marker else 'Onion Skin options')


def _draw_ghosts_toggle(layout, context):
    settings = context.scene.ghost_tool
    layout.prop(settings, 'is_active', text='Turn On Ghosts' if not settings.is_active else 'Ghosts On',
                toggle=True, icon='GHOST_ENABLED' if settings.is_active else 'GHOST_DISABLED')


def _draw_toolbar_menu(layout, context):
    _draw_ghosts_toggle(layout, context)
    for key, label, icon, _draw, _topic, _open in GHOST_SECTIONS:
        if key in {'show', 'onion'}:
            _draw_generation_pair(layout, key)
        else:
            _draw_feature_destination(layout, key, label, icon)
    layout.separator()
    # A native View-menu hide is independent of our persistent preference.
    # Offer direct recovery even when Ghost controls are logically enabled.
    native_visible = getattr(getattr(context, 'space_data', None), 'show_region_tool_header', True)
    show = not toolbar_visible(context) or not native_visible
    layout.operator('ghost_tool.set_toolbar_visibility',
                    text='Show Toolbar' if show else 'Hide Toolbar',
                    icon='HIDE_OFF' if show else 'HIDE_ON').show = show


class GHOST_PT_toolbar_menu(bpy.types.Panel):
    bl_idname = 'GHOST_PT_toolbar_menu'
    bl_label = 'Ghost'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 22

    @classmethod
    def poll(cls, context):
        return _main_home(context, 'TOOLBAR')

    def draw(self, context):
        _draw_toolbar_menu(self.layout, context)


def supports_tool_shelf() -> bool:
    return 'show_toolshelf_tabs' in bpy.types.SpaceView3D.bl_rna.properties


def display_location(context) -> str:
    """Resolve the persisted home safely, including direct-registration startup."""
    prefs = getattr(context, 'preferences', None)
    addon = getattr(prefs, 'addons', {}).get('ghost_tool')
    value = getattr(getattr(addon, 'preferences', None), 'display_location', 'TOOLBAR')
    if value not in {'SIDEBAR', 'TOOLS', 'TOOLBAR'}:
        return 'TOOLBAR'
    if value == 'TOOLS' and not supports_tool_shelf():
        return 'TOOLBAR'
    return value


def toolbar_visible(context) -> bool:
    """The persistent Ghost control visibility, independent of native row visibility."""
    prefs = getattr(context, 'preferences', None)
    addon = getattr(prefs, 'addons', {}).get('ghost_tool')
    return bool(getattr(getattr(addon, 'preferences', None), 'show_toolbar', True))


def _main_home(context, location) -> bool:
    from .settings_editor import is_editor
    window = getattr(context, 'window', None)
    return (hasattr(getattr(context, 'scene', None), 'ghost_tool')
            and (window is None or window.as_pointer() not in _ghost_windows)
            and not is_editor(context) and display_location(context) == location)


# Categories become available after layout. Pointers survive delayed callbacks
# safely when their corresponding RNA objects have been closed.
_pending_display_tabs: dict[tuple[int, int], tuple[str, int]] = {}


def _display_windows():
    return bpy.context.window_manager.windows


_pending_display_update = None


def schedule_display_location_update(*, visibility_only=False):
    """Defer preference-driven native viewport access until the main loop runs.

    Add-on registration also runs before startup windows are initialized.
    Migration can invoke these callbacks recursively. Coalesce requests and
    fetch fresh context when executing, rather than retaining startup RNA.
    """
    global _pending_display_update
    if bpy.app.background:
        return
    if not visibility_only or _pending_display_update is None:
        _pending_display_update = 'visibility' if visibility_only else 'location'
    if not bpy.app.timers.is_registered(_apply_display_location_update):
        bpy.app.timers.register(_apply_display_location_update,
                                first_interval=0.1, persistent=True)


def _apply_display_location_update():
    global _pending_display_update
    requested = _pending_display_update
    _pending_display_update = None
    if not bpy.app.background and requested is not None:
        if requested == 'visibility':
            update_toolbar_visibility(bpy.context)
        else:
            update_display_location(bpy.context)
    return None


def cancel_display_location_update():
    global _pending_display_update
    _pending_display_update = None
    if bpy.app.timers.is_registered(_apply_display_location_update):
        bpy.app.timers.unregister(_apply_display_location_update)


def _ordinary_viewports(context):
    from .settings_editor import is_editor
    from types import SimpleNamespace
    manager = getattr(context, 'window_manager', None)
    for window in getattr(manager, 'windows', ()):
        if window.as_pointer() in _ghost_windows or is_editor(SimpleNamespace(window=window)):
            continue
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                yield window, area


def _select_display_tabs():
    location = display_location(bpy.context)
    windows = {w.as_pointer(): w for w in _display_windows()}
    for key, (requested, attempts) in list(_pending_display_tabs.items()):
        window = windows.get(key[0])
        area = next((a for a in window.screen.areas if a.as_pointer() == key[1]), None) if window else None
        if requested != location or area is None or attempts >= 10:
            _pending_display_tabs.pop(key, None)
            continue
        kind = 'UI' if location == 'SIDEBAR' else 'TOOLS'
        region = next((r for r in area.regions if r.type == kind), None)
        try:
            if region is None:
                raise AttributeError('Region is not laid out yet')
            region.active_panel_category = "Ghost Tool"
        except (AttributeError, TypeError, RuntimeError):
            _pending_display_tabs[key] = (requested, attempts + 1)
        else:
            _pending_display_tabs.pop(key, None)
    return 0.1 if _pending_display_tabs else None


def update_display_location(context) -> None:
    """Reveal the selected home in ordinary viewports and schedule tab selection."""
    location = display_location(context)
    _pending_display_tabs.clear()
    if location == 'TOOLS':
        from .shelf_width import forget_all
        forget_all()
    for window, area in _ordinary_viewports(context):
        space = area.spaces.active
        if space is None:
            continue
        if location == 'SIDEBAR':
            space.show_region_ui = True
        elif location == 'TOOLS':
            space.show_region_toolbar = True
            space.show_toolshelf_tabs = True
        elif location == 'TOOLBAR' and toolbar_visible(context):
            space.show_region_tool_header = True
        area.tag_redraw()
        if location in {'SIDEBAR', 'TOOLS'}:
            _pending_display_tabs[(window.as_pointer(), area.as_pointer())] = (location, 0)
    if _pending_display_tabs and not bpy.app.timers.is_registered(_select_display_tabs):
        bpy.app.timers.register(_select_display_tabs, first_interval=0.05)


def update_toolbar_visibility(context) -> None:
    """Reveal the native row only on an explicit show preference/action."""
    if display_location(context) == 'TOOLBAR' and toolbar_visible(context):
        update_display_location(context)
    else:
        for _window, area in _ordinary_viewports(context):
            area.tag_redraw()


class GHOST_OT_set_toolbar_visibility(bpy.types.Operator):
    bl_idname = "ghost_tool.set_toolbar_visibility"
    bl_label = "Ghost Toolbar Visibility"
    bl_description = "Show or hide Ghost toolbar controls while keeping cached ghosts and settings"

    show: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        prefs = getattr(context, 'preferences', None)
        return getattr(prefs, 'addons', {}).get('ghost_tool') is not None

    @classmethod
    def description(cls, context, properties):
        if properties.show:
            return "Show Ghost controls and reveal the native Tool Settings row in ordinary viewports"
        return "Hide Ghost toolbar controls; keep native Tool Settings, cached ghosts, targets and settings"

    def execute(self, context):
        prefs = context.preferences.addons['ghost_tool'].preferences
        if self.show:
            prefs.display_location = 'TOOLBAR'
        prefs.show_toolbar = self.show
        # Explicit Show also recovers a row hidden using View after the last
        # preference update; assigning an unchanged RNA value is insufficient.
        update_toolbar_visibility(context)
        return {'FINISHED'}


class GHOST_PT_header_menu(bpy.types.Panel):
    """The Ghost Tool dropdown in the 3D Viewport header."""

    bl_idname = "GHOST_PT_header_menu"
    bl_label = "Ghost Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 14

    def draw(self, context: bpy.types.Context) -> None:
        _draw_toolbar_menu(self.layout, context)

    @classmethod
    def poll(cls, context):
        return _main_home(context, 'TOOLBAR')


class GHOST_PT_sidebar(bpy.types.Panel):
    bl_label = "Ghost Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ghost Tool"

    @classmethod
    def poll(cls, context):
        return _main_home(context, 'SIDEBAR')

    def draw_header(self, context):
        self.layout.prop(context.scene.ghost_tool, "is_active", text="", icon='GHOST_ENABLED')

    def draw(self, context):
        draw_ghost_tool(self.layout, context, "sidebar")


class GHOST_PT_tool_shelf(bpy.types.Panel):
    bl_label = "Ghost Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Ghost Tool"

    @classmethod
    def poll(cls, context):
        return (supports_tool_shelf() and _main_home(context, 'TOOLS')
                and bool(getattr(context.space_data, 'show_toolshelf_tabs', False)))

    def draw_header(self, context):
        self.layout.prop(context.scene.ghost_tool, "is_active", text="", icon='GHOST_ENABLED')

    def draw(self, context):
        draw_ghost_tool(self.layout, context, "shelf")


# Windows opened by "Open in Separate Window" (their sidebars show Ghost Tool).
_ghost_windows: set[int] = set()


class GHOST_PT_window(bpy.types.Panel):
    """Ghost Tool in the sidebar of its own separate window only."""

    bl_idname = "GHOST_PT_window"
    bl_label = "Ghost Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Ghost Tool"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        window = getattr(context, "window", None)
        return window is not None and window.as_pointer() in _ghost_windows

    def draw_header(self, context: bpy.types.Context) -> None:
        from .settings_editor import is_editor
        if is_editor(context):
            return
        if hasattr(context.scene, 'ghost_tool'):
            self.layout.prop(context.scene.ghost_tool, "is_active", text="", icon='GHOST_ENABLED')

    def draw(self, context: bpy.types.Context) -> None:
        from .settings_editor import is_editor, draw_editor
        if is_editor(context):
            draw_editor(self.layout, context)
        else:
            draw_ghost_tool(self.layout, context, "window")


class GHOST_OT_open_window(bpy.types.Operator):
    """Open Ghost Tool in its own window that stays open while you work"""

    bl_idname = "ghost_tool.open_window"
    bl_label = "Open in Separate Window"
    bl_description = (
        "Open a separate viewport window with Ghost Tool in its sidebar. It stays "
        "open while you work; move it anywhere, or to a second monitor"
    )
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.window is None or context.screen is None:
            cls.poll_message_set("Open a 3D Viewport window first")
            return False
        from .session_state import SessionState
        return SessionState.poll_available(cls)

    def execute(self, context: bpy.types.Context) -> set[str]:
        area = context.area if context.area and context.area.type == 'VIEW_3D' else next(
            (a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
        if area is None:
            return report_failure(self, "No 3D Viewport to open the window from",
                                  "Open a 3D Viewport and try again")
        before = set(context.window_manager.windows[:])
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        try:
            with context.temp_override(window=context.window, screen=context.screen, area=area, region=region):
                bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        except Exception as exc:
            return report_failure(self, "Could not open a new window", "Use Window > New Window instead", exc)
        new = [w for w in context.window_manager.windows if w not in before]
        if not new:
            return report_failure(self, "Could not open a new window", "Use Window > New Window instead")
        window = new[0]
        _ghost_windows.add(window.as_pointer())
        view = next((a for a in window.screen.areas if a.type == 'VIEW_3D'), None)
        if view is not None:
            view.spaces.active.show_region_ui = True

            window_pointer, area_pointer = window.as_pointer(), view.as_pointer()

            def _select_tab():
                live_window = next((w for w in bpy.context.window_manager.windows
                                    if w.as_pointer() == window_pointer), None)
                live_view = next((a for a in live_window.screen.areas if a.as_pointer() == area_pointer), None) if live_window else None
                if live_view is None:
                    return None
                ui = next((r for r in live_view.regions if r.type == 'UI'), None)
                try:
                    if ui is not None:
                        ui.active_panel_category = "Ghost Tool"
                except Exception:
                    return 0.1  # the tab exists after the first redraw
                return None

            bpy.app.timers.register(_select_tab, first_interval=0.05)
        return {'FINISHED'}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 4 — FLOATING TOOLBAR OPERATOR                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class GHOST_OT_floating_toolbar(bpy.types.Operator):
    """Pop out the Ghost Tool layout as a floating panel under the mouse."""

    bl_idname = "ghost_tool.floating_toolbar"
    bl_label = "Ghost Tool — Floating Toolbar"
    bl_options = {'REGISTER'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        return context.window_manager.invoke_popup(self, width=320)

    def draw(self, context: bpy.types.Context) -> None:
        draw_ghost_tool(self.layout, context, "popup")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 5 — TIMELINE / DOPESHEET HEADER EXTENSION                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _slow_label(refresh_ms: float) -> str:
    """Warning text for the header strip when a path refresh took over 200 ms."""
    return "paths are slow — reduce range" if refresh_ms > 200.0 else ""


def _draw_paths_segment(row, settings) -> None:
    row.separator(factor=0.5)
    row.prop(settings, "paths_enabled", text="Paths", icon='CURVE_PATH', toggle=True)
    row.operator("ghost_tool.paths_add_selected", text="Add", icon='BONE_DATA')
    row.prop(settings, "paths_follow_selection", text="Follow", icon='RESTRICT_SELECT_OFF', toggle=True)
    row.popover(panel="GHOST_PT_paths_popover", text="", icon='DOWNARROW_HLT')
    from .motion_paths import last_refresh_ms
    slow = _slow_label(last_refresh_ms())
    if slow:
        row.label(text=slow, icon='ERROR')


def _draw_timeline_header_extension(self, context: bpy.types.Context) -> None:
    """The owner's revised sketch, inline beside native Timeline controls."""
    scene = context.scene
    if not hasattr(scene, 'ghost_tool'):
        return
    settings = scene.ghost_tool
    self.layout.separator()
    self.layout.prop(settings, "is_active", text="",
                     icon='GHOST_ENABLED' if settings.is_active else 'GHOST_DISABLED', toggle=True)
    if not settings.is_active:
        return

    self.layout.separator(factor=0.5)
    row = self.layout.row(align=True)
    icon = 'GHOST_ENABLED' if settings.show_mesh_ghosts else 'GHOST_DISABLED'
    row.operator_menu_hold("ghost_tool.timeline_display", text="", icon=icon,
                           depress=settings.show_mesh_ghosts, menu='GHOST_MT_timeline_ghost_display').target = 'GHOST'
    _draw_timeline_counts(row, settings, 'GHOST')
    row.separator(factor=0.3)
    for mode, icon in (('WIRE', 'SHADING_WIRE'), ('SOLID', 'SHADING_SOLID')):
        op = row.operator("ghost_tool.timeline_mesh_style", text="", icon=icon,
                          depress=settings.mesh_ghost_mode == mode)
        op.mode = mode
    row.separator(factor=0.3)
    edit = row.row(align=True)
    edit.operator_context = 'INVOKE_DEFAULT'
    _draw_marker_drag_button(edit, text="", icon='ORIENTATION_CURSOR')
    edit.prop(settings, "paths_show_markers", text="", icon='KEYFRAME_HLT', toggle=True)
    row.separator(factor=0.3)
    row.operator_menu_hold("ghost_tool.timeline_display", text="", icon='CURVE_PATH',
                           depress=settings.paths_enabled, menu='GHOST_MT_timeline_path_display').target = 'PATH'
    _draw_timeline_counts(row, settings, 'PATH')


def _draw_graph_header_extension(self, context: bpy.types.Context) -> None:
    """Ghost toggle plus the motion-path segment in the Graph Editor header."""
    scene = context.scene
    if not hasattr(scene, 'ghost_tool'):
        return
    settings = scene.ghost_tool
    layout = self.layout
    layout.separator_spacer()
    row = layout.row(align=True)
    row.prop(settings, "is_active", text="", icon='GHOST_ENABLED' if settings.is_active else 'GHOST_DISABLED', toggle=True)
    if settings.is_active:
        _draw_paths_segment(row, settings)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 6 — 3D VIEWPORT HEADER EXTENSION                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _draw_viewport_view_menu(self, context: bpy.types.Context) -> None:
    """Recover hidden Ghost controls without duplicating the main header row."""
    if not _main_home(context, 'TOOLBAR'):
        return
    native_visible = getattr(getattr(context, 'space_data', None), 'show_region_tool_header', True)
    if toolbar_visible(context) and native_visible:
        return
    self.layout.separator()
    self.layout.operator('ghost_tool.set_toolbar_visibility',
                         text='Show Ghost Toolbar', icon='GHOST_ENABLED').show = True


def _toolbar_tier(context):
    """Keep the full animation toolbar at every width; retain other-mode access."""
    return 'FULL' if getattr(context, 'mode', 'OBJECT') in {'OBJECT', 'POSE'} else 'MINIMAL'


def _draw_viewport_tool_header(self, context):
    """Direct tools with adjacent counts; hold a tool for its own parameters."""
    if not _main_home(context, 'TOOLBAR') or not toolbar_visible(context):
        return
    settings = context.scene.ghost_tool
    row = self.layout.row(align=True)
    row.operator_context = 'INVOKE_DEFAULT'
    row.separator(factor=0.5)
    _draw_header_toggle(row, settings, 'MASTER', '',
                        'GHOST_ENABLED' if settings.is_active else 'GHOST_DISABLED',
                        'GHOST_MT_header_master')

    row.separator(factor=0.5)
    row.operator_menu_hold('ghost_tool.header_ghosts_display', text='Ghosts', icon='GHOST_ENABLED',
                           depress=settings.show_mesh_ghosts,
                           menu='GHOST_MT_header_ghosts')
    _draw_header_counts(row, settings, 'GHOST')
    for mode, icon in (('WIRE', 'SHADING_WIRE'), ('SOLID', 'SHADING_SOLID')):
        row.operator('ghost_tool.header_wire' if mode == 'WIRE' else 'ghost_tool.header_solid',
                     text='', icon=icon, depress=settings.mesh_ghost_mode == mode)

    row.separator(factor=0.5)
    row.operator_menu_hold('ghost_tool.header_paths_display', text='Paths', icon='CURVE_PATH',
                           depress=settings.paths_enabled,
                           menu='GHOST_MT_header_paths')
    _draw_header_counts(row, settings, 'PATH')
    row.operator('ghost_tool.paths_add_selected', text='', icon='ADD')
    _draw_header_toggle(row, settings, 'FOLLOW', '', 'RESTRICT_SELECT_OFF',
                        'GHOST_MT_header_follow')

    row.separator(factor=0.5)
    row.operator_menu_hold('ghost_tool.header_drag', text='Drag', icon='ORIENTATION_CURSOR',
                           depress=_marker_drag_mode_active(),
                           menu='GHOST_MT_header_drag')
    row.operator_menu_hold('ghost_tool.header_pin', text='Pin', icon='PINNED',
                           menu='GHOST_MT_header_pin')
    _draw_header_toggle(row, settings, 'MARKERS', '', 'KEYFRAME_HLT',
                        'GHOST_MT_header_markers')

    row.separator(factor=0.5)
    row.menu('GHOST_MT_header_arc', text='', icon='IPO_BEZIER')
    _draw_header_toggle(row, settings, 'SPACING', '', 'TIME', 'GHOST_MT_header_spacing')

    row.separator(factor=0.5)
    row.popover(panel='GHOST_PT_header_menu', text='Settings', icon='PREFERENCES')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def _draw_native_actions(layout, context):
    entries = (
        ("ghost_tool.generate_ghosts", "Show Markers", 'GHOST_ENABLED'),
        ("ghost_tool.pick_marker", "Drag Marker", 'ORIENTATION_CURSOR'),
        ("ghost_tool.take_snapshot", "Save Snapshot", 'CAMERA_DATA'),
    )
    try:
        from bl_ui.space_toolsystem_common import toolsystem_column_count
        columns = toolsystem_column_count(context.region)
    except (ImportError, AttributeError, TypeError):
        columns = 4
    col = layout.column(align=True)
    col.scale_y = 2
    if columns == 4:
        for idname, label, icon in entries:
            if idname == "ghost_tool.pick_marker":
                _draw_marker_drag_button(col, text=label, icon=icon)
            else:
                col.operator(idname, text=label, icon=icon)
    else:
        columns = max(1, columns)
        for start in range(0, len(entries), columns):
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.scale_x = 2
            for idname, label, icon in entries[start:start + columns]:
                if idname == "ghost_tool.pick_marker":
                    _draw_marker_drag_button(row, text="", icon=icon)
                else:
                    row.operator(idname, text="", icon=icon)


class GHOST_PT_shelf_object(bpy.types.Panel):
    bl_label = "Ghost Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(getattr(context.space_data, 'show_toolshelf_tabs', False))

    def draw(self, context):
        _draw_native_actions(self.layout, context)


class GHOST_PT_shelf_pose(bpy.types.Panel):
    bl_label = "Ghost Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Pose"
    bl_context = "posemode"
    bl_options = {'HIDE_BG'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and bool(getattr(context.space_data, 'show_toolshelf_tabs', False))

    def draw(self, context):
        _draw_native_actions(self.layout, context)


_shelf_registered = []


_HEADER_TOGGLES = {
    'MASTER': ('is_active', 'Ghost Tool', 'live updates'),
    'MARKERS': ('paths_show_markers', 'editable path markers', 'marker sampling and labels'),
    'FOLLOW': ('paths_follow_selection', 'following the current selection', 'path target settings'),
    'ARC': ('show_arc_lines', 'the ghost motion arc', 'arc appearance'),
    'SPACING': ('show_spacing_ticks', 'frame spacing ticks', 'spacing indicators'),
}


def _draw_marker_drag_button(layout, *, text="Drag", icon='ORIENTATION_CURSOR'):
    from .modal_operator import GHOST_OT_pick_marker
    op = layout.operator("ghost_tool.pick_marker", text=text, icon=icon,
                         depress=GHOST_OT_pick_marker.drag_mode_active())
    op.action = 'DRAG'
    return op


def _path_handle_drag_mode_active():
    from .path_handle_drag import GHOST_OT_path_handle_drag
    return GHOST_OT_path_handle_drag._active_wait_mode is not None


def _marker_drag_mode_active():
    from .modal_operator import GHOST_OT_pick_marker
    return GHOST_OT_pick_marker.drag_mode_active()


def _draw_m2_range(layout, settings, *, mode=True):
    """Label values at their input; leave irrelevant mode fields out."""
    if mode:
        layout.prop(settings, 'ghost_range_mode', text='Range')
    if settings.ghost_range_mode == 'AROUND_CURSOR':
        layout.prop(settings, 'ghosts_before', text='Previous (Frames)')
        layout.prop(settings, 'ghosts_after', text='Ahead (Frames)')
    elif settings.ghost_range_mode == 'CUSTOM':
        layout.prop(settings, 'custom_range_start', text='Start Frame')
        layout.prop(settings, 'custom_range_end', text='End Frame')


def _draw_m2_sampling(layout, settings, *, mode=True):
    if mode:
        layout.prop(settings, 'ghost_mode', text='Sampling')
    if settings.ghost_mode == 'FRAME_STEP':
        layout.prop(settings, 'frame_step', text='Every (Frames)')
    elif settings.ghost_mode == 'SUBDIVISION':
        layout.prop(settings, 'subdivision_level', text='Detail')


def _draw_m2_path_sampling(layout, settings):
    if settings.paths_sampling_mode == 'KEYFRAMES':
        layout.prop(settings, 'paths_keyframe_skip', text='Path Every (Keys)')
    else:
        layout.prop(settings, 'paths_step', text='Path Every (Frames)')


class _GhostM2Popover:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 20

    @classmethod
    def poll(cls, context):
        return _feature_context(context)


class GHOST_PT_m2_range(_GhostM2Popover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_m2_range'
    bl_label = 'Ghost Range'
    bl_description = 'Choose the frame range for generated ghost markers'

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False
        _draw_m2_range(self.layout.column(align=True), context.scene.ghost_tool)


class GHOST_PT_m2_sampling(_GhostM2Popover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_m2_sampling'
    bl_label = 'Ghost Sampling'
    bl_description = 'Choose frame spacing, subdivision detail or keyframes for ghost markers'

    def draw(self, context):
        settings = context.scene.ghost_tool
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False
        _draw_m2_sampling(self.layout.column(align=True), settings)
        self.layout.separator()
        self.layout.prop(settings, 'live_point_ghosts', text='Update While Scrubbing')
        if settings.live_point_ghosts or settings.live_mesh_ghosts:
            self.layout.prop(settings, 'live_freeze', text='Freeze Updates')


class GHOST_PT_m2_markers(_GhostM2Popover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_m2_markers'
    bl_label = 'Marker Tools'
    bl_description = 'Select, drag or pin ghost markers and adjust motion editing'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.ghost_tool
        layout.operator_context = 'INVOKE_DEFAULT'
        row = layout.row(align=True)
        row.operator('ghost_tool.pick_marker', text='Select', icon='RESTRICT_SELECT_OFF').action = 'SELECT'
        row.operator('ghost_tool.pick_marker', text='Box Select', icon='SELECT_SET').action = 'BOX'
        row = layout.row(align=True)
        _draw_marker_drag_button(row)
        row.operator('ghost_tool.pick_marker', text='Pin', icon='PINNED').action = 'PIN'
        layout.prop(settings, 'paths_show_markers', text='Path Markers')
        if settings.paths_use_marker_counts:
            layout.label(text='Path Marker Window')
            row = layout.row(align=True)
            row.prop(settings, 'paths_markers_before', text='Previous')
            row.prop(settings, 'paths_markers_after', text='Ahead')
        layout.popover(panel='GHOST_PT_edit_popover', text='Motion Editing Settings')


class GHOST_PT_m2_display(_GhostM2Popover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_m2_display'
    bl_label = 'Ghost Display'
    bl_description = 'Show or hide mesh ghosts independently of Solid/Wire style and motion paths'

    def draw(self, context):
        settings = context.scene.ghost_tool
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(settings, 'show_mesh_ghosts', text='Meshes')
        layout.prop(settings, 'mesh_ghost_mode', text='Style')
        layout.label(text='Hiding meshes keeps the selected style.')
        layout.separator()
        layout.prop(settings, 'show_arc_lines', text='Motion Arc')
        layout.prop(settings, 'show_spacing_ticks', text='Spacing Ticks')
        layout.separator()
        layout.popover(panel='GHOST_PT_skin_options', text='Mesh Ghost Settings')
        layout.popover(panel='GHOST_PT_look_popover', text='Marker Appearance')


class GHOST_PT_m2_paths(_GhostM2Popover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_m2_paths'
    bl_label = 'Motion Paths'
    bl_description = 'Show paths for selected objects or bones and edit labeled path sampling'

    def draw(self, context):
        settings = context.scene.ghost_tool
        layout = self.layout
        layout.operator('ghost_tool.paths_add_selected', text='Add Selected Path', icon='ADD')
        layout.prop(settings, 'paths_enabled', text='Show Paths')
        layout.prop(settings, 'paths_follow_selection', text='Follow Selection')
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(settings, 'paths_sampling_mode', text='Sampling')
        _draw_m2_path_sampling(layout, settings)
        layout.popover(panel='GHOST_PT_paths_popover', text='All Path Settings')


class GHOST_PT_m2_status(_GhostM2Popover, bpy.types.Panel):
    bl_idname = 'GHOST_PT_m2_status'
    bl_label = 'Generated Ghosts'
    bl_description = ('Read-only count of generated ghost markers. Adjust Range and Sampling '
                      'to change density; Generate refreshes paused updates')

    def draw(self, context):
        layout = self.layout
        layout.label(text=f'{len(GhostStore.get(context.scene))} Ghosts', icon='INFO')
        layout.label(text='Computed from generated marker data.')
        layout.label(text='One frame may contain several channel markers.')
        layout.label(text='Mesh ghosts and motion paths are separate displays.')
        layout.label(text='Adjust Range and Sampling to change density.')
        layout.label(text='Use Generate when live updates are paused.')


class GHOST_OT_header_toggle(bpy.types.Operator):
    bl_idname = 'ghost_tool.header_toggle'
    bl_label = 'Toggle Ghost Tool Display'
    bl_options = {'UNDO', 'INTERNAL'}

    target: bpy.props.EnumProperty(
        items=[(key, values[1], values[2]) for key, values in _HEADER_TOGGLES.items()],
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        if not hasattr(getattr(context, 'scene', None), 'ghost_tool'):
            cls.poll_message_set('Open a scene with Ghost Tool enabled')
            return False
        return True

    @classmethod
    def description(cls, context, properties):
        _, subject, options = _HEADER_TOGGLES.get(properties.target, _HEADER_TOGGLES['MASTER'])
        return f'Click to turn {subject} on/off; hold for {options}'

    def execute(self, context):
        settings = context.scene.ghost_tool
        name = _HEADER_TOGGLES[self.target][0]
        setattr(settings, name, not getattr(settings, name))
        from .utils import tag_viewport_redraw
        tag_viewport_redraw(context)
        return {'FINISHED'}


class _GhostHeaderNamedToggle:
    bl_options = {'UNDO', 'INTERNAL'}
    target = 'MARKERS'

    @classmethod
    def poll(cls, context):
        return GHOST_OT_header_toggle.poll(context)

    def execute(self, context):
        return GHOST_OT_header_toggle.execute(self, context)


class GHOST_OT_header_markers_display(_GhostHeaderNamedToggle, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_markers_display'
    bl_label = 'Markers Display'
    bl_description = 'Show or hide editable path markers; hold for marker sampling and labels'


class GHOST_OT_header_master(_GhostHeaderNamedToggle, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_master'
    bl_label = 'Ghost Tool'
    bl_description = 'Turn Ghost Tool on or off; hold for live update settings'
    target = 'MASTER'


class GHOST_OT_header_follow(_GhostHeaderNamedToggle, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_follow'
    bl_label = 'Follow Selection'
    bl_description = 'Show a motion path for the current selection; hold for target settings'
    target = 'FOLLOW'


class GHOST_OT_header_spacing(_GhostHeaderNamedToggle, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_spacing'
    bl_label = 'Spacing Ticks'
    bl_description = 'Show or hide frame spacing ticks; hold for spacing indicators'
    target = 'SPACING'


class _GhostHeaderDisplayAction:
    bl_options = {'UNDO', 'INTERNAL'}
    target = 'GHOST'

    @classmethod
    def poll(cls, context):
        return GHOST_OT_header_toggle.poll(context)

    def execute(self, context):
        return GHOST_OT_timeline_display.execute(self, context)


class GHOST_OT_header_ghosts_display(_GhostHeaderDisplayAction, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_ghosts_display'
    bl_label = 'Ghosts Display'
    bl_description = 'Show or hide ghost meshes; hold for sampling and appearance settings'


class GHOST_OT_header_paths_display(_GhostHeaderDisplayAction, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_paths_display'
    bl_label = 'Motion Paths Display'
    bl_description = 'Show or hide motion paths; hold for sampling and line settings'
    target = 'PATH'


class _GhostHeaderStyleAction:
    bl_options = {'UNDO', 'INTERNAL'}
    mode = 'WIRE'

    @classmethod
    def poll(cls, context):
        return GHOST_OT_header_toggle.poll(context)

    def execute(self, context):
        return GHOST_OT_timeline_mesh_style.execute(self, context)


class GHOST_OT_header_wire(_GhostHeaderStyleAction, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_wire'
    bl_label = 'Wire Ghosts'
    bl_description = 'Display ghost meshes as wireframes'


class GHOST_OT_header_solid(_GhostHeaderStyleAction, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_solid'
    bl_label = 'Solid Ghosts'
    bl_description = 'Display ghost meshes as solid silhouettes'
    mode = 'SOLID'


class _GhostHeaderMarkerAction:
    bl_options = {'INTERNAL'}
    action = 'DRAG'

    @classmethod
    def poll(cls, context):
        from .modal_operator import GHOST_OT_pick_marker
        return GHOST_OT_pick_marker.poll(context)

    def invoke(self, context, event):
        result = bpy.ops.ghost_tool.pick_marker('INVOKE_DEFAULT', action=self.action)
        # The picker owns the modal handler; this header launcher is complete.
        return {'CANCELLED'} if 'CANCELLED' in result else {'FINISHED'}


class GHOST_OT_header_drag(_GhostHeaderMarkerAction, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_drag'
    bl_label = 'Drag Markers'
    bl_description = 'Edit markers until selected again or Escape; hold for motion editing settings'


class GHOST_OT_header_pin(_GhostHeaderMarkerAction, bpy.types.Operator):
    bl_idname = 'ghost_tool.header_pin'
    bl_label = 'Pin Markers'
    bl_description = 'Pick a marker to pin or unpin; hold for pin tools'
    action = 'PIN'


def _draw_header_sampling_options(layout, settings, target):
    """Parameters only: the display action and counts already have one header home."""
    if target == 'GHOST':
        layout.prop(settings, 'mesh_ghost_frame_mode', text='Sampling')
        if settings.mesh_ghost_frame_mode == 'STEP':
            layout.prop(settings, 'mesh_ghost_step', text='Every (Frames)')
        else:
            layout.prop(settings, 'mesh_ghost_keyframe_skip', text='Keyframe Interval')
            if settings.mesh_ghost_keyframe_skip == 'CUSTOM':
                layout.prop(settings, 'mesh_ghost_keyframe_skip_custom', text='Every Nth Keyframe')
    else:
        layout.prop(settings, 'paths_sampling_mode', text='Sampling')
        _draw_m2_path_sampling(layout, settings)


class _GhostHeaderToolMenu:
    target = ''

    def draw(self, context):
        settings = context.scene.ghost_tool
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        if self.target == 'MASTER':
            layout.prop(settings, 'live_mesh_ghosts', text='Update Meshes While Scrubbing')
            layout.prop(settings, 'live_point_ghosts', text='Update Markers While Scrubbing')
            layout.prop(settings, 'live_freeze', text='Freeze Updates')
        elif self.target == 'GHOST':
            _draw_header_sampling_options(layout, settings, 'GHOST')
            layout.separator()
            layout.prop(settings, 'mesh_ghost_opacity', text='Opacity')
            layout.prop(settings, 'mesh_ghost_xray', text='In Front')
            layout.prop(settings, 'mesh_ghost_falloff', text='Fade')
        elif self.target == 'PATH':
            _draw_header_sampling_options(layout, settings, 'PATH')
            layout.separator()
            layout.prop(settings, 'paths_style', text='Line Style')
            layout.prop(settings, 'paths_show_frame_numbers', text='Frame Numbers')
            layout.prop(settings, 'paths_show_handles', text='Bezier Handles')
        elif self.target == 'MARKERS':
            layout.label(text='Sampling is shared with Motion Paths.')
            _draw_header_sampling_options(layout, settings, 'PATH')
            layout.separator()
            layout.prop(settings, 'paths_show_key_dots', text='Keyframe Dots')
            layout.prop(settings, 'show_frame_numbers', text='Marker Frame Numbers')
        elif self.target == 'DRAG':
            layout.prop(settings, 'editing_mode', text='When Released')
            if settings.editing_mode == 'RESHAPE':
                layout.prop(settings, 'curve_mode', text='Curve Shape')
            else:
                layout.prop(settings, 'smooth_neighbors_on_commit', text='Smooth Neighbours')
            layout.prop(settings, 'sculpt_falloff_radius', text='Nearby Frame Reach')
            layout.prop(settings, 'sculpt_falloff_curve', text='Falloff')
            layout.separator()
            layout.label(text='Drag stays active; select again or Esc to exit.')
        elif self.target == 'PIN':
            layout.label(text='Click a marker to pin or unpin it.')
            layout.label(text='Pinned markers stay fixed while reshaping.')
            layout.operator('ghost_tool.unpin_all', text='Unpin All Markers', icon='UNPINNED')
        elif self.target == 'FOLLOW':
            layout.label(text='Follow shows a path for the current selection.')
            layout.label(text='Added paths remain when the selection changes.')
            layout.prop(settings, 'paths_active_glow', text='Highlight Active Path')
        elif self.target == 'ARC':
            for style, label in (('SOLID', 'Solid'), ('SPEED', 'Speed Colored'), ('FADE', 'Fade')):
                layout.prop_enum(settings, 'arc_line_style', style, text=label)
        elif self.target == 'SPACING':
            layout.prop(settings, 'show_acceleration_markers', text='Acceleration Indicators')
        elif self.target == 'GENERATE':
            _draw_m2_range(layout, settings)
            _draw_m2_sampling(layout, settings)


class GHOST_MT_header_master(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Ghost Tool Updates'
    target = 'MASTER'


class GHOST_MT_header_ghosts(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Ghost Display Settings'
    target = 'GHOST'


class GHOST_MT_header_paths(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Motion Path Settings'
    target = 'PATH'


class GHOST_MT_header_markers(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Path Marker Settings'
    target = 'MARKERS'


class GHOST_MT_header_drag(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Drag Marker Settings'
    target = 'DRAG'


class GHOST_MT_header_pin(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Pinned Markers'
    target = 'PIN'


class GHOST_MT_header_follow(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Follow Selection Settings'
    target = 'FOLLOW'


class GHOST_MT_header_arc(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Arc Style'
    bl_description = 'Choose Solid, Speed Colored or Fade'
    target = 'ARC'


class GHOST_MT_header_spacing(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Frame Spacing Settings'
    target = 'SPACING'


class GHOST_MT_header_generate(_GhostHeaderToolMenu, bpy.types.Menu):
    bl_label = 'Generate Marker Settings'
    target = 'GENERATE'


class GHOST_OT_header_count_step(bpy.types.Operator):
    bl_idname = 'ghost_tool.header_count_step'
    bl_label = 'Adjust Before or Ahead Count'
    bl_options = {'UNDO', 'INTERNAL'}

    field: bpy.props.EnumProperty(items=[
        ('mesh_ghost_past_count', 'Ghosts Before', 'Ghost meshes before the playhead'),
        ('mesh_ghost_future_count', 'Ghosts Ahead', 'Ghost meshes ahead of the playhead'),
        ('paths_markers_before', 'Path Samples Before', 'Motion path samples before the playhead'),
        ('paths_markers_after', 'Path Samples Ahead', 'Motion path samples ahead of the playhead'),
    ], options={'HIDDEN', 'SKIP_SAVE'})
    delta: bpy.props.IntProperty(default=1, min=-1, max=1, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        if not hasattr(getattr(context, 'scene', None), 'ghost_tool'):
            cls.poll_message_set('Open a scene with Ghost Tool enabled')
            return False
        return True

    @classmethod
    def description(cls, context, properties):
        subject = 'ghost' if properties.field.startswith('mesh_ghost_') else 'motion path sample'
        side = 'before' if properties.field.endswith(('past_count', 'before')) else 'ahead of'
        verb = 'Add' if properties.delta > 0 else 'Remove'
        return f'{verb} one {subject} {side} the current frame'

    def execute(self, context):
        settings = context.scene.ghost_tool
        prop = settings.bl_rna.properties[self.field]
        value = max(prop.hard_min, min(prop.hard_max, getattr(settings, self.field) + self.delta))
        setattr(settings, self.field, value)
        from .utils import tag_viewport_redraw
        tag_viewport_redraw(context)
        return {'FINISHED'}


def _draw_header_counts(layout, settings, target):
    """Keep labeled native steppers beside the display they control at every width."""
    names = (('mesh_ghost_past_count', 'mesh_ghost_future_count') if target == 'GHOST'
             else ('paths_markers_before', 'paths_markers_after'))
    for name, label in zip(names, ('Before', 'Ahead')):
        stepper = layout.row(align=True)
        op = stepper.operator('ghost_tool.header_count_step', text='', icon='REMOVE')
        op.field, op.delta = name, -1
        field = stepper.row(align=True)
        field.ui_units_x = 5.0
        field.prop(settings, name, text=label)
        op = stepper.operator('ghost_tool.header_count_step', text='', icon='ADD')
        op.field, op.delta = name, 1


def _draw_header_toggle(layout, settings, target, text, icon, menu):
    name = _HEADER_TOGGLES[target][0]
    operator = {
        'MASTER': 'ghost_tool.header_master',
        'MARKERS': 'ghost_tool.header_markers_display',
        'FOLLOW': 'ghost_tool.header_follow',
        'SPACING': 'ghost_tool.header_spacing',
    }[target]
    layout.operator_menu_hold(operator, text=text, icon=icon,
                              depress=getattr(settings, name), menu=menu)


def _draw_timeline_range(layout, settings, *, show_mode=True) -> None:
    """Keep each range label attached to its editable scene property."""
    if show_mode:
        layout.prop(settings, "ghost_range_mode", text="Range")
    if settings.ghost_range_mode == 'AROUND_CURSOR':
        layout.prop(settings, "ghosts_before", text="Before")
        layout.prop(settings, "ghosts_after", text="After")
    elif settings.ghost_range_mode == 'CUSTOM':
        layout.prop(settings, "custom_range_start", text="Start Frame")
        layout.prop(settings, "custom_range_end", text="End Frame")


def _draw_timeline_sampling(layout, settings, *, show_mode=True) -> None:
    if show_mode:
        layout.prop(settings, "ghost_mode", text="Sampling")
    if settings.ghost_mode == 'FRAME_STEP':
        layout.prop(settings, "frame_step", text="Every (Frames)")
    elif settings.ghost_mode == 'SUBDIVISION':
        layout.prop(settings, "subdivision_level", text="Detail")


def _draw_timeline_marker_tools(layout) -> None:
    layout.operator_context = 'INVOKE_DEFAULT'
    _draw_marker_drag_button(layout)
    layout.operator("ghost_tool.pick_marker", text="Pin", icon='PINNED').action = 'PIN'


def _draw_timeline_display(layout, settings) -> None:
    row = layout.row(align=True)
    row.prop(settings, "show_arc_lines", text="Arc", icon='CURVE_PATH', toggle=True)
    row.prop(settings, "show_spacing_ticks", text="Spacing", icon='TIME', toggle=True)
    row = layout.row(align=True)
    row.operator("ghost_tool.toggle_mesh_visibility", text="Meshes", icon='HIDE_OFF',
                 depress=settings.show_mesh_ghosts)
    row.separator(factor=0.3)
    row.operator("ghost_tool.toggle_mesh_mode", text="Wire", icon='SHADING_WIRE',
                 depress=settings.mesh_ghost_mode == 'WIRE')


class GHOST_PT_timeline_status(bpy.types.Panel):
    """Read-only generated output, with an explanation instead of a fake input."""

    bl_idname = "GHOST_PT_timeline_status"
    bl_label = "Generated Ghosts"
    bl_description = (
        "Read-only count of generated ghost markers, not an editable frame count. "
        "Change Range and Sampling to control density; Generate refreshes paused updates"
    )
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 18

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"{len(GhostStore.get(context.scene))} Ghosts", icon='INFO')
        layout.label(text="Computed from generated marker data.")
        layout.label(text="One frame can contain several channel markers.")
        layout.label(text="Adjust Range and Sampling to change density.")
        layout.label(text="Use Generate when live updates are paused.")


class GHOST_PT_timeline_options(bpy.types.Panel):
    """Watchkeeper groups in the same order at every header width."""

    bl_idname = "GHOST_PT_timeline_options"
    bl_label = "Ghost Timeline Settings"
    bl_description = "Ghost range, sampling, marker tools, display and motion paths"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 20

    def draw(self, context):
        layout = self.layout
        settings = context.scene.ghost_tool
        layout.label(text="Ghosts", icon='GHOST_ENABLED')
        row = layout.row(align=True)
        row.operator("ghost_tool.generate_ghosts", text="Generate", icon='ADD')
        row.operator("ghost_tool.clear_ghosts", text="Clear Ghosts", icon='TRASH')

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Ghost Meshes")
        col.prop(settings, "show_mesh_ghosts", text="Show Ghosts")
        col.prop(settings, "mesh_ghost_frame_mode", text="Sampling")
        if settings.mesh_ghost_frame_mode == 'STEP':
            col.prop(settings, "mesh_ghost_step", text="Ghost Every (Frames)")
        else:
            col.prop(settings, "mesh_ghost_keyframe_skip", text="Every Keyframe")
            if settings.mesh_ghost_keyframe_skip == 'CUSTOM':
                col.prop(settings, "mesh_ghost_keyframe_skip_custom", text="Every Nth Keyframe")
        col.prop(settings, "mesh_ghost_past_count", text="Ghosts Before")
        col.prop(settings, "mesh_ghost_future_count", text="Ghosts After")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Range")
        _draw_timeline_range(col, settings)
        col = layout.column(align=True)
        col.label(text="Sampling")
        _draw_timeline_sampling(col, settings)
        col.prop(settings, "live_point_ghosts", text="Update While Scrubbing")
        if settings.live_point_ghosts or settings.live_mesh_ghosts:
            col.prop(settings, "live_freeze", text="Freeze Updates")

        layout.separator()
        layout.label(text="Marker Tools")
        _draw_timeline_marker_tools(layout.row(align=True))
        layout.label(text="Display")
        _draw_timeline_display(layout, settings)

        layout.separator()
        layout.label(text="Paths", icon='CURVE_PATH')
        row = layout.row(align=True)
        row.prop(settings, "paths_enabled", text="Paths", toggle=True)
        row.prop(settings, "paths_follow_selection", text="Follow Selection", toggle=True)
        layout.operator("ghost_tool.paths_add_selected", text="Add Selected Path", icon='ADD')
        layout.prop(settings, "paths_step", text="Path Every")
        layout.popover(panel="GHOST_PT_paths_popover", text="Path Settings")

        layout.separator()
        layout.label(text="Status")
        layout.popover(panel="GHOST_PT_timeline_status",
                       text=f"{len(GhostStore.get(context.scene))} Ghosts", icon='INFO')
        layout.separator()
        layout.operator("ghost_tool.floating_toolbar", text="Full Ghost Tools", icon='WINDOW')


def _draw_timeline_counts(layout, settings, target) -> None:
    """Two native numeric selectors: previous first, ahead second."""
    names = (('mesh_ghost_past_count', 'mesh_ghost_future_count') if target == 'GHOST'
             else ('paths_markers_before', 'paths_markers_after'))
    group = layout.row(align=True)
    for name, direction in zip(names, ('TRIA_LEFT', 'TRIA_RIGHT')):
        field = group.row(align=True)
        field.ui_units_x = 2.3
        field.prop(settings, name, text="", icon=direction)


class GHOST_OT_timeline_display(bpy.types.Operator):
    bl_idname = "ghost_tool.timeline_display"
    bl_label = "Toggle Ghost Display"
    bl_options = {'UNDO', 'INTERNAL'}

    target: bpy.props.EnumProperty(items=[('GHOST', "Ghosts", "Mesh ghosts"),
                                          ('PATH', "Motion Path", "Motion paths")],
                                   options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        subject = "ghost meshes" if properties.target == 'GHOST' else "motion paths"
        return f"Click to show/hide {subject}; hold to choose frame/keyframe sampling and display options"

    @classmethod
    def poll(cls, context):
        return hasattr(getattr(context, 'scene', None), 'ghost_tool')

    def execute(self, context):
        settings = context.scene.ghost_tool
        name = 'show_mesh_ghosts' if self.target == 'GHOST' else 'paths_enabled'
        if self.target == 'PATH' and not settings.paths_enabled:
            from .motion_paths import all_targets
            if not all_targets(context) and bpy.ops.ghost_tool.paths_add_selected.poll():
                bpy.ops.ghost_tool.paths_add_selected()
                return {'FINISHED'}
        setattr(settings, name, not getattr(settings, name))
        return {'FINISHED'}


class GHOST_OT_timeline_sampling(bpy.types.Operator):
    bl_idname = "ghost_tool.timeline_sampling"
    bl_label = "Set Sampling Mode"
    bl_options = {'UNDO', 'INTERNAL'}

    target: bpy.props.EnumProperty(items=[('GHOST', "Ghosts", "Mesh ghosts"),
                                          ('PATH', "Motion Path", "Motion paths")],
                                   options={'HIDDEN', 'SKIP_SAVE'})
    mode: bpy.props.EnumProperty(items=[('STEP', "Frame by Frame", "Sample every N frames"),
                                        ('KEYFRAMES', "By Keyframe", "Sample animation keys")],
                                 options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return hasattr(getattr(context, 'scene', None), 'ghost_tool')

    def execute(self, context):
        settings = context.scene.ghost_tool
        if self.target == 'GHOST':
            settings.mesh_ghost_frame_mode = self.mode
        else:
            # Keep the two header numbers meaningful when choosing keys in a
            # scene that still uses an older frame-based window.
            before, after = settings.paths_markers_before, settings.paths_markers_after
            settings.paths_markers_before, settings.paths_markers_after = before, after
            settings.paths_sampling_mode = self.mode
        return {'FINISHED'}


def _draw_timeline_sampling_menu(layout, settings, target):
    current = settings.mesh_ghost_frame_mode if target == 'GHOST' else settings.paths_sampling_mode
    for mode, label in (('STEP', "Frame by Frame"), ('KEYFRAMES', "By Keyframe")):
        op = layout.operator("ghost_tool.timeline_sampling", text=label,
                             icon='RADIOBUT_ON' if current == mode else 'RADIOBUT_OFF')
        op.target, op.mode = target, mode
    layout.separator()
    if target == 'GHOST':
        if current == 'STEP':
            layout.prop(settings, "mesh_ghost_step", text="Every (Frames)")
        else:
            layout.prop(settings, "mesh_ghost_keyframe_skip", text="Keyframe Interval")
            if settings.mesh_ghost_keyframe_skip == 'CUSTOM':
                layout.prop(settings, "mesh_ghost_keyframe_skip_custom", text="Every Nth Keyframe")
        layout.prop(settings, "mesh_ghost_opacity", text="Opacity")
        layout.prop(settings, "mesh_ghost_xray", text="In Front")
    else:
        if current == 'STEP':
            layout.prop(settings, "paths_step", text="Every (Frames)")
        else:
            layout.prop(settings, "paths_keyframe_skip", text="Every Nth Keyframe")
        layout.prop(settings, "paths_show_markers", text="Editable Markers")
        layout.prop(settings, "paths_show_frame_numbers", text="Frame Numbers")
    layout.separator()
    layout.operator("wm.call_panel", text="More Ghost Settings", icon='PREFERENCES').name = 'GHOST_PT_timeline_options'


class GHOST_MT_timeline_ghost_display(bpy.types.Menu):
    bl_label = "Ghost Display"

    def draw(self, context):
        _draw_timeline_sampling_menu(self.layout, context.scene.ghost_tool, 'GHOST')


class GHOST_MT_timeline_path_display(bpy.types.Menu):
    bl_label = "Motion Path Display"

    def draw(self, context):
        _draw_timeline_sampling_menu(self.layout, context.scene.ghost_tool, 'PATH')


def _prepare_timeline_markers(context):
    """Make the drawn path's editable markers available before starting a pick."""
    from . import motion_paths
    settings = context.scene.ghost_tool
    if not motion_paths.pinned_targets(context.scene):
        if not bpy.ops.ghost_tool.paths_add_selected.poll():
            return 0
        bpy.ops.ghost_tool.paths_add_selected()
    settings.paths_enabled = True
    settings.paths_show_markers = True
    motion_paths.refresh_paths(context)
    return motion_paths.sync_markers(context)


class GHOST_OT_timeline_edit_markers(bpy.types.Operator):
    bl_idname = "ghost_tool.timeline_edit_markers"
    bl_label = "Edit Motion-Line Markers"
    bl_description = "Select and drag a motion-line marker in the 3D Viewport; Escape cancels"

    @classmethod
    def poll(cls, context):
        from .session_state import SessionState
        settings = getattr(getattr(context, 'scene', None), 'ghost_tool', None)
        return bool(settings and settings.is_active and SessionState.poll_available(cls))

    def invoke(self, context, event):
        if not context.window or not any(a.type == 'VIEW_3D' for a in context.window.screen.areas):
            self.report({'WARNING'}, "Open a 3D Viewport to edit motion-line markers")
            return {'CANCELLED'}
        if not _prepare_timeline_markers(context):
            self.report({'INFO'}, "No editable markers on this path; select an animated object or extend the marker counts")
            return {'CANCELLED'}
        return bpy.ops.ghost_tool.pick_marker('INVOKE_DEFAULT', action='DRAG')


class GHOST_OT_timeline_mesh_style(bpy.types.Operator):
    """Choose an explicit style independently of the Show/Hide Ghosts toggle."""

    bl_idname = "ghost_tool.timeline_mesh_style"
    bl_label = "Set Ghost Mesh Style"
    bl_options = {'UNDO', 'INTERNAL'}

    mode: bpy.props.EnumProperty(
        items=[('WIRE', 'Wire Ghosts', 'Show ghost meshes as wireframes'),
               ('SOLID', 'Solid Ghosts', 'Show ghost meshes as solid silhouettes')],
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return hasattr(getattr(context, 'scene', None), 'ghost_tool')

    @classmethod
    def description(cls, context, properties):
        return ('Use wireframe ghost meshes; preserve Show/Hide Ghosts' if properties.mode == 'WIRE'
                else 'Use solid ghost meshes; preserve Show/Hide Ghosts')

    def execute(self, context):
        settings = context.scene.ghost_tool
        if settings.mesh_ghost_mode != self.mode:
            settings.mesh_ghost_mode = self.mode
        return {'FINISHED'}


CLASSES: tuple[type, ...] = (
    GhostToolEasingSettings,
    GHOST_OT_show_help_popup,
    GHOST_UL_paths,
    GHOST_MT_paths_checked,
    GHOST_MT_paths_move_to,
    GHOST_PT_paths_popover,
    GHOST_PT_marker_options,
    GHOST_PT_skin_options,
    GHOST_PT_edit_popover,
    GHOST_PT_compare_popover,
    GHOST_PT_physics_popover,
    GHOST_PT_look_popover,
    GHOST_PT_settings_popover,
    GHOST_PT_toolbar_menu,
    GHOST_OT_set_toolbar_visibility,
    GHOST_PT_header_menu,
    GHOST_PT_sidebar,
    GHOST_PT_window,
    GHOST_OT_open_window,
    GHOST_OT_floating_toolbar,
    GHOST_PT_timeline_status,
    GHOST_PT_timeline_options,
    GHOST_OT_timeline_mesh_style,
    GHOST_OT_timeline_edit_markers,
    GHOST_OT_timeline_display,
    GHOST_OT_timeline_sampling,
    GHOST_MT_timeline_ghost_display,
    GHOST_MT_timeline_path_display,
    GHOST_OT_header_toggle,
    GHOST_OT_header_markers_display,
    GHOST_OT_header_master,
    GHOST_OT_header_follow,
    GHOST_OT_header_spacing,
    GHOST_OT_header_ghosts_display,
    GHOST_OT_header_paths_display,
    GHOST_OT_header_wire,
    GHOST_OT_header_solid,
    GHOST_OT_header_drag,
    GHOST_OT_header_pin,
    GHOST_OT_header_count_step,
    GHOST_MT_header_master,
    GHOST_MT_header_ghosts,
    GHOST_MT_header_paths,
    GHOST_MT_header_markers,
    GHOST_MT_header_drag,
    GHOST_MT_header_pin,
    GHOST_MT_header_follow,
    GHOST_MT_header_arc,
    GHOST_MT_header_spacing,
    GHOST_MT_header_generate,
    GHOST_PT_m2_range,
    GHOST_PT_m2_sampling,
    GHOST_PT_m2_markers,
    GHOST_PT_m2_display,
    GHOST_PT_m2_paths,
    GHOST_PT_m2_status,
)

# Track header appends for clean unregistration
_header_appends: list[tuple] = []


def register() -> None:
    """Register all UI classes and header extensions."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    if supports_tool_shelf():
        for cls in (GHOST_PT_tool_shelf, GHOST_PT_shelf_object, GHOST_PT_shelf_pose):
            bpy.utils.register_class(cls)
            _shelf_registered.append(cls)

    bpy.types.Scene.ghost_tool_easing = bpy.props.PointerProperty(
        type=GhostToolEasingSettings,
        name="Ghost Tool Easing Settings",
    )

    # Append to Timeline header
    try:
        bpy.types.DOPESHEET_HT_header.append(_draw_timeline_header_extension)
        _header_appends.append(
            (bpy.types.DOPESHEET_HT_header, _draw_timeline_header_extension)
        )
    except Exception as exc:
        warn(f"Could not append to Dopesheet header: {exc}")

    # Graph Editor header: ghost toggle + motion-path segment
    try:
        bpy.types.GRAPH_HT_header.append(_draw_graph_header_extension)
        _header_appends.append(
            (bpy.types.GRAPH_HT_header, _draw_graph_header_extension)
        )
    except Exception as exc:
        warn(f"Could not append to Graph Editor header: {exc}")

    # Recovery stays in View; the main header no longer duplicates the row below.
    try:
        bpy.types.VIEW3D_MT_view.append(_draw_viewport_view_menu)
        _header_appends.append(
            (bpy.types.VIEW3D_MT_view, _draw_viewport_view_menu)
        )
    except Exception as exc:
        warn(f"Could not append Ghost toolbar recovery to View: {exc}")

    try:
        bpy.types.VIEW3D_HT_tool_header.append(_draw_viewport_tool_header)
        _header_appends.append((bpy.types.VIEW3D_HT_tool_header, _draw_viewport_tool_header))
    except Exception as exc:
        warn(f"Could not append Ghost controls to native Tool Settings: {exc}")

    log("UI panels and header strips registered.")


def unregister() -> None:
    """Unregister all UI classes and remove header extensions."""
    cancel_display_location_update()
    if bpy.app.timers.is_registered(_select_display_tabs):
        bpy.app.timers.unregister(_select_display_tabs)
    _pending_display_tabs.clear()
    # Remove header appends first
    for header_cls, func in _header_appends:
        try:
            header_cls.remove(func)
        except Exception as exc:
            warn(f"Warning removing header append: {exc}")
    _header_appends.clear()

    for cls in reversed(_shelf_registered):
        bpy.utils.unregister_class(cls)
    _shelf_registered.clear()

    if hasattr(bpy.types.Scene, 'ghost_tool_easing'):
        del bpy.types.Scene.ghost_tool_easing

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

    log("UI panels and header strips unregistered.")


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# tests/test_ghost_header_ui.py covers the header menu, the separate window,
# rotation markers and the onion-skin sources headless.
