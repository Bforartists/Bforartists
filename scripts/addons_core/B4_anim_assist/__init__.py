"""Anim Assist - Production animation workflow tools that complement Animaide."""

bl_info = {
    "name": "Anim Assist",
    "author": "Developer",
    "version": (12, 11, 1),
    "blender": (4, 2, 0),
    "location": "Properties > Scene > Anim Assist; Graph Editor and Dope Sheet > Sidebar > Anim Assist; editor header menus",
    "description": "Animation tools with configurable Timeline sliders and named toolbar layouts, for Bforartists.",
    "category": "Animation",
}

from . import constants
from .core.logging import get_logger
from .core.registry import ClassRegistry
from .core import lifecycle as lifecycle_mod
from .core import properties as prop_mod
from .core import cache as cache_mod
from .core import runtime as rts_mod
from .core import capabilities as cap_mod
from .core import hotkeys as hk_mod
from .core import migration as mig_mod
from .core import dispatch as dispatch_mod
from .core import help_registry as help_reg_mod
from .core import help_phase1_entries as help_phase1_mod
from .core import help_phase2_entries as help_phase2_mod
from .core import help_phase3_entries as help_phase3_mod
from .core import p3_properties as p3_prop_mod
from .core import pose_compare as pose_compare_mod
from .core import breakdown_core as breakdown_core_mod
from .core import help_phase4_entries as help_phase4_mod
from .core import p4_properties as p4_prop_mod
from .core import p4_offset_math as p4_offset_math_mod
from .core import draw_registry as dreg_mod
from .core import app_handlers as app_handlers_mod
from .core import help_phase5_entries as help_phase5_mod
from .core import p5_properties as p5_prop_mod
from .core import p5_path_cache as p5_cache_mod
from .core import help_phase6_entries as help_phase6_mod
from .core import p6_properties as p6_prop_mod
from .core import help_phase7_entries as help_phase7_mod
from .core import p7_properties as p7_prop_mod
from .core import p7_session as p7_session_mod
from .core import help_phase8_entries as help_phase8_mod
from .core import p8_properties as p8_prop_mod
from .core import p8_switch_history as p8_hist_mod
from .core import help_phase9_entries as help_phase9_mod
from .core import p9_properties as p9_prop_mod
from .core import p9_pair_cache as p9_cache_mod
from .core import help_phase10_entries as help_phase10_mod
from .core import p10_properties as p10_prop_mod
from .core import p10_tool_registry as p10_tool_reg_mod
from .core import p10_audit as p10_audit_mod
from .core import p10_recovery as p10_recovery_mod
from .core import help_phase11_entries as help_phase11_mod
from .core import p11_properties as p11_prop_mod
# --- LIPSYNC LAYER (Phase 12) ---
from .core import help_phase12_entries as help_phase12_mod
from .core import p12_properties as p12_prop_mod
from .core import p12_session as p12_session_mod
# --- v12: hybrid PREVIEW/SHIPPED + shape keys ---
from .core import p12_driver_engine as p12_driver_mod
from .operators import p12_mode_ops as p12_mode_mod
from .core import ui_state as ui_state_mod
from .prefs import AA_AddonPreferences, prepare_timeline_quick_preferences
from . import operators as ops_pkg
from . import ui as ui_pkg

_log = get_logger(__name__)
_registry: ClassRegistry | None = None


def _build_registry() -> ClassRegistry:
    reg = ClassRegistry()
    reg.extend(prop_mod.CLASSES)
    prepare_timeline_quick_preferences()
    reg.add(AA_AddonPreferences)
    reg.extend(ops_pkg.CLASSES)
    reg.extend(ui_pkg.CLASSES)
    return reg


def _is_bforartists() -> bool:
    import bpy as _bpy
    if getattr(_bpy.app, "bforartists", False):
        return True
    build_branch = getattr(_bpy.app, "build_branch", b"")
    if isinstance(build_branch, bytes):
        build_branch = build_branch.decode("utf-8", errors="ignore")
    if build_branch.lower().startswith("bfa"):
        return True
    binary_path = getattr(_bpy.app, "binary_path", "")
    if "bforartists" in binary_path.lower():
        return True
    version_str = getattr(_bpy.app, "version_string", "")
    if "bforartists" in version_str.lower():
        return True
    return False


def register() -> None:
    if not _is_bforartists():
        raise RuntimeError(
            "Anim Assist is exclusive to Bforartists and cannot be used with "
            "standard Blender. Please install Bforartists: https://www.bforartists.de"
        )

    try:
        lifecycle_mod.purge_zombie_classes()
    except Exception:
        _log.debug("Zombie class purge failed - continuing", exc_info=True)

    global _registry
    _registry = _build_registry()
    try:
        _registry.register()
        prop_mod.register_properties()
        p3_prop_mod.register_properties()
        p4_prop_mod.register_properties()
        p5_prop_mod.register_properties()
        p6_prop_mod.register_properties()
        p7_prop_mod.register_properties()
        p8_prop_mod.register_properties()
        p9_prop_mod.register_properties()
        p10_prop_mod.register_properties()
        p11_prop_mod.register_properties()
        try:
            p12_prop_mod.register_properties()
        except Exception:
            _log.exception("Lipsync property registration failed - continuing")
        ui_state_mod.register_properties()
        ui_pkg.headers.register()
        ui_pkg.header_toolbars.register()
        ui_pkg.header_menus.register()
        cache_mod.init()
        rts_mod.init()
        dreg_mod.init()
        app_handlers_mod.register()
        cap_mod.init()
        hk_mod.get_manager().register_defaults()

        # --- v12: lipsync driver namespace + handlers ---
        try:
            p12_driver_mod.register_driver_namespace()
            p12_driver_mod.register_handlers()
            p12_mode_mod.register_render_handlers()
        except Exception:
            _log.exception("Lipsync driver/handler registration failed - continuing")

        for help_register, label in (
            (help_phase1_mod.register, "Help"),
            (help_phase2_mod.register, "Key editing help"),
            (help_phase3_mod.register, "Breakdown help"),
            (help_phase4_mod.register, "Offset help"),
            (help_phase5_mod.register, "Trajectory help"),
            (help_phase6_mod.register, "Retiming help"),
            (help_phase7_mod.register, "Proxy/bake help"),
            (help_phase8_mod.register, "Matching help"),
            (help_phase9_mod.register, "Mirroring help"),
            (help_phase10_mod.register, "Orchestration help"),
            (help_phase11_mod.register, "Animation layer help"),
            (help_phase12_mod.register, "Lipsync help"),
        ):
            try:
                help_register()
            except Exception:
                _log.exception("%s registry seed failed - continuing", label)

        # Seed on enable/restart independently of the saved first-run flag.
        p10_tool_reg_mod.seed_registered_tools()

        try:
            from .prefs import get_prefs
            from .core.logging import set_level
            prefs = get_prefs()
            if prefs is not None:
                set_level(bool(prefs.debug_mode))
        except Exception:
            _log.debug("Could not sync logging level from preferences", exc_info=True)

        # bpy.data is restricted while Blender enables add-ons, so the open
        # file's check and migration usually wait for the next timer tick.
        mig_mod.check_open_file_when_ready()

        _log.info("Anim Assist %s registered", constants.ADDON_VERSION_STRING)

    except Exception:
        _log.exception("Registration failed; attempting rollback")
        try:
            p12_mode_mod.unregister_render_handlers()
            p12_driver_mod.unregister_handlers()
            p12_driver_mod.unregister_driver_namespace()
        except Exception:
            _log.debug("Lipsync driver rollback failed", exc_info=True)
        for help_unreg in (
            help_phase12_mod.unregister, help_phase11_mod.unregister,
            help_phase10_mod.unregister, help_phase9_mod.unregister,
            help_phase8_mod.unregister, help_phase7_mod.unregister,
            help_phase6_mod.unregister, help_phase5_mod.unregister,
            help_phase4_mod.unregister, help_phase3_mod.unregister,
            help_phase2_mod.unregister, help_phase1_mod.unregister,
        ):
            try:
                help_unreg()
            except Exception:
                _log.debug("Help rollback failed", exc_info=True)
        try:
            help_reg_mod.clear_all_help()
        except Exception:
            _log.debug("Help registry clear failed", exc_info=True)

        for unreg, label in (
            (p12_prop_mod.unregister_properties, "Lipsync"),
            (p11_prop_mod.unregister_properties, "Animation layer"),
            (p10_prop_mod.unregister_properties, "Orchestration"),
            (p9_prop_mod.unregister_properties, "Mirroring"),
            (p8_prop_mod.unregister_properties, "Matching"),
            (p7_prop_mod.unregister_properties, "Proxy/bake"),
            (p6_prop_mod.unregister_properties, "Retiming"),
            (p5_prop_mod.unregister_properties, "Trajectory"),
            (p4_prop_mod.unregister_properties, "Offset"),
            (p3_prop_mod.unregister_properties, "Breakdown"),
        ):
            try:
                unreg()
            except Exception:
                _log.debug("%s property rollback failed", label, exc_info=True)

        for cleanup in (
            mig_mod.cancel_pending_check,
            p10_tool_reg_mod.clear,
            ui_pkg.header_menus.unregister,
            ui_pkg.header_toolbars.unregister,
            ui_pkg.headers.unregister,
            hk_mod.shutdown,
            cap_mod.shutdown,
            app_handlers_mod.unregister,
            dreg_mod.shutdown,
            rts_mod.shutdown,
            cache_mod.shutdown,
            ui_state_mod.unregister_properties,
            prop_mod.unregister_properties,
        ):
            try:
                cleanup()
            except Exception:
                _log.debug("Rollback cleanup failed: %s", cleanup, exc_info=True)

        if _registry is not None:
            try:
                _registry.unregister()
            except Exception:
                _log.debug("Rollback class unregister failed", exc_info=True)
            _registry = None
        raise


def unregister() -> None:
    global _registry

    # --- v12: lipsync driver/handler teardown FIRST so depsgraph stops calling our function ---
    try:
        p12_mode_mod.unregister_render_handlers()
    except Exception:
        _log.debug("Lipsync render-handler teardown failed", exc_info=True)
    try:
        p12_driver_mod.unregister_handlers()
        p12_driver_mod.unregister_driver_namespace()
    except Exception:
        _log.debug("Lipsync driver teardown failed", exc_info=True)

    for help_cleanup in (
        help_phase12_mod.unregister,
        help_phase11_mod.unregister,
        help_phase10_mod.unregister,
        help_phase9_mod.unregister,
        help_phase8_mod.unregister,
        help_phase7_mod.unregister,
        help_phase6_mod.unregister,
        help_phase5_mod.unregister,
        help_phase4_mod.unregister,
        help_phase3_mod.unregister,
        help_phase2_mod.unregister,
        help_phase1_mod.unregister,
        help_reg_mod.clear_all_help,
    ):
        try:
            help_cleanup()
        except Exception:
            _log.exception("Help teardown failed: %s", help_cleanup)

    def _p6_clear_singletons() -> None:
        try:
            from .operators.p6_retime_ops import clear_last_backup
            clear_last_backup()
        except Exception:
            pass
        try:
            from .operators.p6_gap_ops import clear_cached_gaps
            clear_cached_gaps()
        except Exception:
            pass
        try:
            from .operators.p6_diag_ops import clear_cached_diag
            clear_cached_diag()
        except Exception:
            pass

    def _p4_clear_singletons() -> None:
        try:
            p4_offset_math_mod.clear_last()
        except Exception:
            pass

    def _p3_clear_singletons() -> None:
        try:
            pose_compare_mod.clear()
        except Exception:
            pass
        try:
            breakdown_core_mod._LAST_OPTIONS = None  # type: ignore[attr-defined]
        except Exception:
            pass

    for cleanup in (
        mig_mod.cancel_pending_check,
        ui_pkg.header_menus.unregister,
        ui_pkg.header_toolbars.unregister,
        ui_pkg.headers.unregister,
        hk_mod.shutdown,
        dispatch_mod.clear,
        cap_mod.shutdown,
        app_handlers_mod.unregister,
        dreg_mod.shutdown,
        rts_mod.shutdown,
        cache_mod.shutdown,
        # --- LIPSYNC LAYER (Phase 12) ---
        p12_session_mod.clear_all_sessions,
        p12_prop_mod.unregister_properties,
        # --- ANIMATION LAYER MANAGEMENT ---
        p11_prop_mod.unregister_properties,
        # --- ORCHESTRATION AND RECOVERY ---
        p10_audit_mod.clear_all,
        p10_recovery_mod.clear_snapshots,
        p10_tool_reg_mod.clear,
        p10_prop_mod.unregister_properties,
        # --- MIRRORING AND PAIR DETECTION ---
        p9_cache_mod.clear_cache,
        p9_prop_mod.unregister_properties,
        # --- MATCHING AND SPACE SWITCHING ---
        p8_hist_mod.clear_history,
        p8_prop_mod.unregister_properties,
        # --- PROXY AND BAKE CONTROLS ---
        p7_session_mod.clear_all_sessions,
        p7_prop_mod.unregister_properties,
        # --- RETIMING AND TIMING DIAGNOSTICS ---
        _p6_clear_singletons,
        p6_prop_mod.unregister_properties,
        # --- TRAJECTORY VISUALIZATION ---
        p5_cache_mod.invalidate_all,
        p5_prop_mod.unregister_properties,
        # --- TRANSFORM OFFSET CONTROLS ---
        _p4_clear_singletons,
        p4_prop_mod.unregister_properties,
        # --- BREAKDOWN AND INBETWEEN TOOLS ---
        _p3_clear_singletons,
        p3_prop_mod.unregister_properties,
        # --- UI STATE AND REGISTRATION ---
        ui_state_mod.unregister_properties,
        prop_mod.unregister_properties,
    ):
        try:
            cleanup()
        except Exception:
            _log.exception("Cleanup failed during unregister: %s", cleanup)

    if _registry is not None:
        try:
            _registry.unregister()
        except Exception:
            _log.exception("Class registry unregister failed")
        finally:
            _registry = None

    _log.info("Anim Assist %s unregistered", constants.ADDON_VERSION_STRING)
