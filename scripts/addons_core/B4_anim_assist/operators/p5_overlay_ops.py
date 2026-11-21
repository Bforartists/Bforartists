# --- TRAJECTORY VISUALIZATION ---
"""Overlay operators.

Operators that manage the trajectory overlay lifecycle:

* **Enable** — registers draw handlers, runs initial sampling.
* **Disable** — tears down draw handlers, clears draw data.
* **Refresh** — re-samples all visible targets and rebuilds draw data.
* **Isolate** — switches display mode to ISOLATE for a named target.
* **Mute Unselected** — hides trajectories for non-selected bones/objects.
* **Run Diagnostics** — runs all enabled detectors, updates issue list.
"""

from __future__ import annotations

import bpy

from ..core.logging import get_logger
from ..core import draw_registry as dreg
from ..core import runtime as rts_mod
from ..core import cache as cache_mod
from ..core.p5_properties import get_p5
from ..core.p5_sampling import (
    sample_path_fast,
    sample_path_constraints,
)
from ..core.p5_path_cache import (
    make_target_key,
    get_entry,
    store_entry,
    invalidate_all as cache_invalidate_all,
)
from ..core.p5_issues import run_all_detectors, arc_quality_score
from ..core.p5_draw import (
    build_draw_data,
    set_draw_data,
    clear_draw_data,
    draw_paths_3d,
    draw_labels_2d,
    set_handler_ids,
    clear_handler_ids,
    get_handler_ids,
)
from ..core.p5_colors import palette_by_id as get_palette

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared poll
# ---------------------------------------------------------------------------

def _p5_poll(context) -> bool:
    """Common poll for all trajectory operators: need a VIEW_3D area and a scene."""
    if not hasattr(context, "scene") or context.scene is None:
        return False
    return get_p5(context) is not None


def _p5_overlay_active_poll(context) -> bool:
    """Poll that additionally requires the overlay to be enabled."""
    if not _p5_poll(context):
        return False
    p5 = get_p5(context)
    return p5 is not None and p5.overlay_enabled


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_frame_range(context, p5):
    """Return (frame_start, frame_end) based on the scope mode."""
    scene = context.scene
    mode = p5.scope_mode
    if mode == "AROUND_CURRENT":
        cur = scene.frame_current
        return (float(cur - p5.window_before), float(cur + p5.window_after))
    elif mode == "CUSTOM":
        return (float(p5.custom_start), float(p5.custom_end))
    else:  # FULL_RANGE
        return (float(scene.frame_start), float(scene.frame_end))


def _resolve_targets(context, p5):
    """Return a list of (obj, bone_name) tuples for the current display mode."""
    targets = []
    mode = p5.display_mode

    if mode == "ISOLATE":
        # Isolate target is "object_name::bone_name" or "object_name::".
        iso = p5.isolate_target
        if iso:
            parts = iso.split("::", 1)
            obj_name = parts[0]
            bone_name = parts[1] if len(parts) > 1 and parts[1] else None
            obj = bpy.data.objects.get(obj_name)
            if obj:
                targets.append((obj, bone_name))
        return targets

    obj = getattr(context, "active_object", None)
    if obj is None:
        return targets

    if mode == "ACTIVE":
        if obj.type == "ARMATURE" and context.mode == "POSE":
            bone = getattr(context, "active_pose_bone", None)
            if bone:
                targets.append((obj, bone.name))
            else:
                targets.append((obj, None))
        else:
            targets.append((obj, None))
    elif mode == "MULTI":
        if obj.type == "ARMATURE" and context.mode == "POSE":
            for pb in context.selected_pose_bones or []:
                targets.append((obj, pb.name))
                if len(targets) >= p5.max_display_targets:
                    break
        else:
            for sel_obj in context.selected_objects or []:
                targets.append((sel_obj, None))
                if len(targets) >= p5.max_display_targets:
                    break

    return targets


def _is_animation_playing(context) -> bool:
    """Return True while timeline playback is active in the current screen."""
    screen = getattr(context, "screen", None)
    return bool(getattr(screen, "is_animation_playing", False))


def _effective_use_constraints(context, p5) -> bool:
    """Constraint sampling is intentionally disabled during playback."""
    return bool(p5.use_constraints) and not _is_animation_playing(context)


def _sample_target(context, p5, obj, bone_name, frame_start, frame_end):
    """Sample a single target, using cache if fresh."""
    key = make_target_key(obj.name, bone_name)
    entry = get_entry(key)
    if entry is not None:
        return entry.samples

    step = p5.sample_step
    max_samp = p5.max_samples
    use_cons = _effective_use_constraints(context, p5)

    if use_cons:
        samples = sample_path_constraints(
            context, obj, bone_name,
            frame_start, frame_end, step,
            max_samples=max_samp,
        )
    else:
        action = None
        adata = getattr(obj, "animation_data", None)
        if adata:
            action = adata.action
        samples = sample_path_fast(
            obj, bone_name, action,
            frame_start, frame_end, step,
            max_samples=max_samp,
        )

    store_entry(
        key, samples,
        frame_start=frame_start,
        frame_end=frame_end,
        step=step,
        use_constraints=use_cons,
        space_mode=p5.space_mode,
    )
    return samples


def _build_all_draw_data(context, p5, *, run_diagnostics: bool = False):
    """Sample all targets, run detectors, build draw data, and push to draw module."""
    targets = _resolve_targets(context, p5)
    frame_start, frame_end = _resolve_frame_range(context, p5)
    palette = get_palette(p5.color_preset)

    all_paths = []
    all_issues = []

    for obj, bone_name in targets:
        samples = _sample_target(context, p5, obj, bone_name, frame_start, frame_end)
        if not samples:
            continue

        issues = []
        if run_diagnostics:
            issues = run_all_detectors(
                samples,
                drift_tolerance=p5.drift_tolerance,
                pop_ratio=p5.pop_ratio,
                spacing_hi=p5.spacing_hi,
                spacing_lo=p5.spacing_lo,
                enable_drift=p5.enable_drift_detect,
                enable_flat=p5.enable_flat_detect,
                enable_zigzag=p5.enable_zigzag_detect,
                enable_pop=p5.enable_pop_detect,
                enable_spacing=p5.enable_spacing_detect,
                enable_reversal=p5.enable_reversal_detect,
                enable_stops=p5.enable_stop_detect,
                enable_apex_contact=p5.enable_apex_contact_detect,
            )
        all_issues.extend(issues)

        label = bone_name or obj.name
        dd = build_draw_data(
            samples, issues,
            palette=palette,
            label=label,
            show_frame_ticks=p5.show_frame_ticks,
            show_keyframe_ticks=p5.show_keyframe_ticks,
            show_velocity=p5.show_velocity,
            show_tangent=p5.show_tangent,
            show_ghost_points=p5.show_ghost_points,
            show_frame_numbers=p5.show_frame_numbers,
            show_spacing_color=p5.show_spacing_color,
            show_deviation_heatmap=p5.show_deviation_heatmap,
            current_frame=float(context.scene.frame_current),
            path_width=p5.path_width,
        )
        all_paths.append(dd)

    score = -1.0
    if run_diagnostics and all_paths:
        score = arc_quality_score(
            # Flatten all samples for the aggregate score.
            [s for t in targets
             for s in _sample_target(context, p5, t[0], t[1], frame_start, frame_end)],
            all_issues,
        )

    gen = cache_mod.get_cache().generation
    set_draw_data(all_paths, all_issues, score, gen)
    return len(all_paths), len(all_issues)


# ---------------------------------------------------------------------------
# Enable overlay
# ---------------------------------------------------------------------------

class AA_OT_p5_enable_overlay(bpy.types.Operator):
    """Enable the trajectory overlay in the 3D viewport."""

    bl_idname = "animassist.p5_enable_overlay"
    bl_label = "Enable Trajectory Overlay"
    bl_description = "Register viewport draw handlers and display trajectory paths"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_poll(context)

    def execute(self, context):
        p5 = get_p5(context)
        if p5 is None:
            self.report({"WARNING"}, "Trajectory properties not available")
            return {"CANCELLED"}

        state = rts_mod.get_state()

        # Already enabled?
        h3d, h2d = get_handler_ids()
        if h3d >= 0 or h2d >= 0:
            self.report({"INFO"}, "Overlay already active")
            return {"CANCELLED"}

        # Register draw handlers.
        hid_3d = dreg.register_handler(
            "VIEW_3D", "WINDOW", draw_paths_3d, "POST_VIEW",
            tag="p5_trajectory_3d",
        )
        hid_2d = dreg.register_handler(
            "VIEW_3D", "WINDOW", draw_labels_2d, "POST_PIXEL",
            tag="p5_trajectory_2d",
        )
        set_handler_ids(hid_3d, hid_2d)

        p5.overlay_enabled = True
        state.overlay_enabled = True
        state.active_overlay_tags.add("p5_trajectory")

        # Initial sampling.
        try:
            n_paths, n_issues = _build_all_draw_data(context, p5)
            _log.info("Trajectory overlay enabled: %d paths, %d issues", n_paths, n_issues)
        except Exception:
            _log.exception("Initial trajectory sampling failed")

        # Tag viewport for redraw.
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Disable overlay
# ---------------------------------------------------------------------------

class AA_OT_p5_disable_overlay(bpy.types.Operator):
    """Disable the trajectory overlay."""

    bl_idname = "animassist.p5_disable_overlay"
    bl_label = "Disable Trajectory Overlay"
    bl_description = "Unregister draw handlers and clear trajectory display"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_poll(context)

    def execute(self, context):
        p5 = get_p5(context)

        h3d, h2d = get_handler_ids()
        for hid in (h3d, h2d):
            if hid >= 0:
                dreg.unregister_handler(hid)
        clear_handler_ids()
        clear_draw_data()

        if p5 is not None:
            p5.overlay_enabled = False
        state = rts_mod.get_state()
        state.overlay_enabled = False
        state.active_overlay_tags.discard("p5_trajectory")

        cache_invalidate_all()

        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        _log.info("Trajectory overlay disabled")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Refresh overlay
# ---------------------------------------------------------------------------

class AA_OT_p5_refresh_overlay(bpy.types.Operator):
    """Re-sample all visible trajectories and rebuild draw data."""

    bl_idname = "animassist.p5_refresh_overlay"
    bl_label = "Refresh Trajectory Overlay"
    bl_description = "Invalidate cache and re-sample all visible trajectory paths"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return _p5_overlay_active_poll(context)

    def execute(self, context):
        p5 = get_p5(context)
        if p5 is None or not p5.overlay_enabled:
            self.report({"WARNING"}, "Overlay not active")
            return {"CANCELLED"}

        # Bump generation to invalidate all cached entries.
        cache_mod.get_cache().bump_generation()
        cache_invalidate_all()

        try:
            n_paths, n_issues = _build_all_draw_data(context, p5)
            self.report({"INFO"}, f"Refreshed: {n_paths} paths, {n_issues} issues")
        except Exception:
            _log.exception("Refresh failed")
            self.report({"ERROR"}, "Could not refresh the overlay. Details are in the system console (Window > Toggle System Console)")

        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Isolate target
# ---------------------------------------------------------------------------

class AA_OT_p5_isolate_target(bpy.types.Operator):
    """Switch to ISOLATE mode for a specific target."""

    bl_idname = "animassist.p5_isolate_target"
    bl_label = "Isolate Target"
    bl_description = "Show only the trajectory for this bone or object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_poll(context)

    target_key: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Target Key",
        description="Target key in object_name::bone_name format",
        default="",
    )

    def execute(self, context):
        p5 = get_p5(context)
        if p5 is None:
            return {"CANCELLED"}

        p5.display_mode = "ISOLATE"
        p5.isolate_target = self.target_key

        if p5.overlay_enabled:
            cache_invalidate_all()
            try:
                _build_all_draw_data(context, p5)
            except Exception:
                _log.exception("Isolate rebuild failed")

            for area in context.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Mute unselected
# ---------------------------------------------------------------------------

class AA_OT_p5_mute_unselected(bpy.types.Operator):
    """Hide trajectories for non-selected bones or objects."""

    bl_idname = "animassist.p5_mute_unselected"
    bl_label = "Mute Unselected"
    bl_description = "Restrict trajectory display to currently selected targets only"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_poll(context)

    def execute(self, context):
        p5 = get_p5(context)
        if p5 is None:
            return {"CANCELLED"}

        # Switch to MULTI mode — which already only shows selected.
        p5.display_mode = "MULTI"

        if p5.overlay_enabled:
            cache_invalidate_all()
            try:
                _build_all_draw_data(context, p5)
            except Exception:
                _log.exception("Mute unselected rebuild failed")

            for area in context.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Run diagnostics
# ---------------------------------------------------------------------------

class AA_OT_p5_run_diagnostics(bpy.types.Operator):
    """Run all enabled arc/motion detectors and update the issue list."""

    bl_idname = "animassist.p5_run_diagnostics"
    bl_label = "Run Arc Diagnostics"
    bl_description = "Detect arc drift, pops, spacing issues, and other motion problems"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return _p5_overlay_active_poll(context)

    def execute(self, context):
        p5 = get_p5(context)
        if p5 is None:
            self.report({"WARNING"}, "Trajectory properties not available")
            return {"CANCELLED"}

        if not p5.overlay_enabled:
            self.report({"WARNING"}, "Enable overlay first")
            return {"CANCELLED"}

        try:
            n_paths, n_issues = _build_all_draw_data(context, p5, run_diagnostics=True)
            self.report({"INFO"}, f"Diagnostics: {n_issues} issues found")
        except Exception:
            _log.exception("Diagnostics failed")
            self.report({"ERROR"}, "Could not run overlay diagnostics. Details are in the system console (Window > Toggle System Console)")

        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return {"FINISHED"}


def trails_shown() -> bool:
    """True while the trajectory overlay's draw handlers are registered."""
    h3d, h2d = get_handler_ids()
    return h3d >= 0 or h2d >= 0


class AA_OT_timeline_trails_toggle(bpy.types.Operator):
    """Show world motion trails, or hide them when they are shown."""

    bl_idname = "animassist.timeline_trails_toggle"
    bl_label = "Show or Hide Trails"
    bl_description = "Show world motion trails in the 3D Viewport, or hide them when they are shown"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p5_poll(context)

    def execute(self, context):
        if trails_shown():
            return bpy.ops.animassist.p5_disable_overlay()
        return bpy.ops.animassist.p5_enable_overlay()


CLASSES: tuple[type, ...] = (
    AA_OT_p5_enable_overlay,
    AA_OT_p5_disable_overlay,
    AA_OT_timeline_trails_toggle,
    AA_OT_p5_refresh_overlay,
    AA_OT_p5_isolate_target,
    AA_OT_p5_mute_unselected,
    AA_OT_p5_run_diagnostics,
)
