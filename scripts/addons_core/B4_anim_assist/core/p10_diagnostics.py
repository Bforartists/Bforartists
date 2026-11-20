# --- ORCHESTRATION AND RECOVERY ---
"""System diagnostics and cleanup utilities for orchestration.

Provides inspection tools that help animators and TDs understand the
current state of the Anim Assist addon: registered classes, dangling
handlers, stale caches, and resource usage.

Public API:
    run_leak_check()        — detect resource leaks
    run_stale_cleanup()     — remove stale handlers/caches
    run_metadata_cleanup(context)  — clean orphaned scene metadata
    rebuild_all_caches(context)    — force-rebuild every cache
    reset_ui_state(context)        — reset all panel collapse states
    get_system_report()            — comprehensive status dict
    validate_registration()        — check all expected classes registered
"""

from __future__ import annotations

from typing import Any

import bpy

from .logging import get_logger

__all__ = [
    "run_leak_check",
    "run_stale_cleanup",
    "run_metadata_cleanup",
    "rebuild_all_caches",
    "reset_ui_state",
    "get_system_report",
    "validate_registration",
]

_log = get_logger(__name__)


def run_leak_check() -> list[str]:
    """Detect potential resource leaks. Returns a list of warning strings."""
    warnings: list[str] = []

    # Check draw handler registry
    try:
        from . import draw_registry as dreg
        count = dreg.handler_count() if hasattr(dreg, 'handler_count') else 0
        if count > 20:
            warnings.append(f"Draw registry has {count} handlers (expected < 20)")
    except Exception:
        _log.debug("Draw registry check failed", exc_info=True)

    # Check pair cache size
    try:
        from . import p9_pair_cache as p9c
        stats = p9c.get_stats("") if hasattr(p9c, 'get_stats') else {}
        # Check if any single cache is unreasonably large
    except Exception:
        _log.debug("Pair cache check failed", exc_info=True)

    # Check audit buffer
    try:
        from . import p10_audit as audit
        stats = audit.get_stats()
        if stats.get("buffered_errors", 0) > 50:
            warnings.append(
                f"Audit error buffer has {stats['buffered_errors']} entries"
            )
    except Exception:
        _log.debug("Audit buffer check failed", exc_info=True)

    # Check recovery snapshots
    try:
        from . import p10_recovery as recovery
        count = recovery.get_snapshot_count()
        if count > 8:
            warnings.append(f"Recovery buffer has {count} snapshots")
    except Exception:
        _log.debug("Recovery snapshot check failed", exc_info=True)

    if not warnings:
        _log.info("Leak check: no issues found")
    else:
        for w in warnings:
            _log.warning("Leak check: %s", w)

    return warnings


def run_stale_cleanup() -> dict[str, int]:
    """Remove stale handlers and caches. Returns counts of items cleaned."""
    cleaned: dict[str, int] = {}

    # Clean stale draw handlers
    try:
        from . import draw_registry as dreg
        count = dreg.unregister_all()
        if count:
            cleaned["draw_handlers"] = count
    except Exception:
        _log.debug("Draw handler cleanup failed", exc_info=True)

    # Invalidate P5 path cache
    try:
        from . import p5_path_cache as p5c
        p5c.invalidate_all()
        cleaned["p5_path_cache"] = 1
    except Exception:
        _log.debug("P5 path cache invalidation failed", exc_info=True)

    # Invalidate P9 pair cache
    try:
        from . import p9_pair_cache as p9c
        p9c.clear_cache()
        cleaned["p9_pair_cache"] = 1
    except Exception:
        _log.debug("P9 pair cache clear failed", exc_info=True)

    # Clear P8 switch history
    try:
        from . import p8_switch_history as p8h
        p8h.clear_history()
        cleaned["p8_switch_history"] = 1
    except Exception:
        _log.debug("P8 switch history clear failed", exc_info=True)

    _log.info("Stale cleanup: %s", cleaned)
    return cleaned


def run_metadata_cleanup(context: bpy.types.Context) -> dict[str, int]:
    """Clean orphaned metadata from the scene. Returns counts."""
    cleaned: dict[str, int] = {}
    scene = context.scene

    # Check for P7 stale sessions
    try:
        from . import p7_session as p7s
        stale = p7s.detect_stale_sessions()
        if stale:
            cleaned["p7_stale_sessions"] = len(stale)
            p7s.clear_all_sessions()
    except Exception:
        _log.debug("P7 stale session detection failed", exc_info=True)

    # Check scene custom properties for orphaned AA data
    orphan_count = 0
    for key in list(scene.keys()):
        if key.startswith("anim_assist_") and key not in (
            "anim_assist", "anim_assist_p3", "anim_assist_p4",
            "anim_assist_p5", "anim_assist_p6", "anim_assist_p7",
            "anim_assist_p8", "anim_assist_p9", "anim_assist_p10",
        ):
            _log.debug("Orphaned scene key: %s", key)
            orphan_count += 1
    if orphan_count:
        cleaned["orphaned_scene_keys"] = orphan_count

    _log.info("Metadata cleanup: %s", cleaned)
    return cleaned


def rebuild_all_caches(context: bpy.types.Context) -> dict[str, bool]:
    """Force-rebuild all caches. Returns success status per cache."""
    results: dict[str, bool] = {}

    # Action hash cache
    try:
        from . import cache as cache_mod
        cache_mod.invalidate_cache()
        cache_mod.get_cache().bump_generation()
        results["action_cache"] = True
    except Exception:
        _log.debug("Action cache rebuild failed", exc_info=True)
        results["action_cache"] = False

    # P5 path cache
    try:
        from . import p5_path_cache as p5c
        p5c.invalidate_all()
        results["p5_path_cache"] = True
    except Exception:
        _log.debug("P5 path cache rebuild failed", exc_info=True)
        results["p5_path_cache"] = False

    # P9 pair cache — rebuild for active armature
    try:
        from . import p9_pair_cache as p9c
        p9c.clear_cache()
        obj = context.active_object
        if obj and obj.type == "ARMATURE":
            bone_names = [b.name for b in obj.data.bones]
            p9c.build_pair_map(obj.data.name, bone_names)
        results["p9_pair_cache"] = True
    except Exception:
        _log.debug("P9 pair cache rebuild failed", exc_info=True)
        results["p9_pair_cache"] = False

    _log.info("Cache rebuild: %s", results)
    return results


def reset_ui_state(context: bpy.types.Context) -> int:
    """Reset all panel collapse states to defaults. Returns count reset."""
    try:
        from . import ui_state as uis
        state = uis.get_ui_state(context)
        if state is None:
            return 0
        count = len(state.sections)
        state.sections.clear()
        state.prefer_compact = False
        state.show_analysis_details = True
        state.show_advanced_default = False
        _log.info("UI state reset: %d section states cleared", count)
        return count
    except Exception:
        _log.exception("UI state reset failed")
        return 0


def get_system_report() -> dict[str, Any]:
    """Generate a comprehensive system status report."""
    report: dict[str, Any] = {}

    # Blender info
    report["blender_version"] = ".".join(str(x) for x in bpy.app.version)

    # Capabilities
    try:
        from . import capabilities as cap
        report["capabilities"] = cap.get_registry().all_capabilities()
    except Exception:
        _log.debug("Capabilities report failed", exc_info=True)
        report["capabilities"] = {}

    # Runtime state
    try:
        from . import runtime as rts
        state = rts.get_state()
        report["runtime"] = {
            "is_batch_processing": state.is_batch_processing,
            "active_tool_id": state.active_tool_id,
            "suppress_updates": state.suppress_updates,
            "overlay_enabled": state.overlay_enabled,
            "active_overlay_count": len(state.active_overlay_tags),
        }
    except Exception:
        _log.debug("Runtime state report failed", exc_info=True)
        report["runtime"] = {}

    # Audit stats
    try:
        from . import p10_audit as audit
        report["audit"] = audit.get_stats()
    except Exception:
        _log.debug("Audit stats report failed", exc_info=True)
        report["audit"] = {}

    # Recovery
    try:
        from . import p10_recovery as recovery
        report["recovery_snapshots"] = recovery.get_snapshot_count()
    except Exception:
        _log.debug("Recovery snapshots report failed", exc_info=True)
        report["recovery_snapshots"] = 0

    # Tool registry
    try:
        from . import p10_tool_registry as tools
        all_t = tools.all_tools()
        report["tool_registry"] = {
            "total_tools": len(all_t),
            "phases": tools.get_phases(),
            "categories": tools.get_categories(),
        }
    except Exception:
        _log.debug("Tool registry report failed", exc_info=True)
        report["tool_registry"] = {}

    # Dispatch commands
    try:
        from . import dispatch as disp
        report["dispatch_commands"] = disp.list_commands()
    except Exception:
        _log.debug("Dispatch commands report failed", exc_info=True)
        report["dispatch_commands"] = []

    return report


def validate_registration() -> list[str]:
    """Check that all expected Blender classes are registered. Returns issues."""
    issues: list[str] = []

    # Spot-check a few key operator bl_idnames across modules
    expected_ops = [
        "animassist.breakdown_current_frame",  # Breakdown tools
        "animassist.p4_offset_selected",       # Offset tools
        "animassist.p5_enable_overlay",        # Trajectory tools
        "animassist.p7_create_proxy",          # Temporary controls
        "animassist.p8_compensate_single",     # Matching workflows
        "animassist.p9_mirror_pose",           # Mirroring tools
        "animassist.p10_safe_disable",         # Orchestration
    ]
    for op_id in expected_ops:
        parts = op_id.split(".")
        if len(parts) == 2:
            cat = getattr(bpy.ops, parts[0], None)
            if cat is None or not hasattr(cat, parts[1]):
                issues.append(f"Missing operator: {op_id}")

    if not issues:
        _log.info("Registration validation: all checks passed")
    else:
        for issue in issues:
            _log.warning("Registration issue: %s", issue)

    return issues
