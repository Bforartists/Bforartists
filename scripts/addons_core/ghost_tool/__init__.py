"""
Ghost Tool — Ghost keyframe visualization and manipulation for Bforartists.

This addon gives animators the ability to visualize and directly
manipulate in-between frames in 3D space.  It generates "ghost" markers at
mathematically interpolated positions between existing keyframes, displays
them as draggable 3D handles in the viewport, and recalculates f-curves in
real time as ghosts are moved.

Addon registration file.  All modules are imported and their register/
unregister functions are called in the correct dependency order.
"""

bl_info = {
    "name": "Ghost Tool",
    "author": "GoingGhost",
    "version": (4, 3, 3),
    "blender": (4, 0, 0),
    "location": "View3D > Header > Ghost Tool",
    "description": "Ghost animation tools for Bforartists with scoped snapshots, independent variants, saved references and undoable restoration.",
    "category": "Animation",
    "doc_url": "",
    "tracker_url": "",
}

import bpy

# ---------------------------------------------------------------------------
# Bforartists detection
# ---------------------------------------------------------------------------

def _is_bforartists() -> bool:
    """Return True when running inside Bforartists, False for standard Blender."""
    if getattr(bpy.app, "bforartists", False):
        return True

    build_branch = getattr(bpy.app, "build_branch", b"")
    if isinstance(build_branch, bytes):
        build_branch = build_branch.decode("utf-8", errors="ignore")
    if build_branch.lower().startswith("bfa"):
        return True

    binary_path = getattr(bpy.app, "binary_path", "")
    if "bforartists" in binary_path.lower():
        return True

    version_str = getattr(bpy.app, "version_string", "")
    if "bforartists" in version_str.lower():
        return True

    return False


# ---------------------------------------------------------------------------
# Real addon internals (only touched when running inside Bforartists)
# ---------------------------------------------------------------------------

_modules_loaded = False
_real_addon_registered = False


def _clear_pycache():
    """Remove stale __pycache__ bytecode to prevent version mismatch issues."""
    import os
    import shutil
    from . import utils

    addon_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(addon_dir, "__pycache__")

    if os.path.isdir(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            utils.log(f"Cleared __pycache__ at {cache_dir}")
        except (OSError, IOError) as exc:
            utils.warn(f"Could not clear __pycache__: {exc}")


def _import_modules(*, reload_modules: bool = True):
    """Import all submodules.  Handles both first-load and reload scenarios."""
    global _modules_loaded

    import importlib

    from . import utils
    from . import ghost_data
    from . import session_state
    from . import ghost_cache
    from . import ghost_pipeline
    from . import fcurve_utils
    from . import easing_presets
    from . import target_binding
    from . import snapshot_storage
    from . import snapshot
    from . import physics_archetypes   # pure math, zero bpy — no classes to register
    from . import physics_suggest
    from . import export_import
    from . import modal_operator
    from . import selection_operators
    from . import diff_mode
    from . import viewport_draw
    from . import ui_panel
    from . import preferences
    from . import shelf_width
    from . import api
    from . import mesh_ghosts
    from . import motion_paths
    from . import path_handle_drag
    from . import draw_to_keys_math
    from . import draw_to_keys
    from . import settings_editor

    if _modules_loaded and reload_modules:
        importlib.reload(utils)
        importlib.reload(ghost_data)
        importlib.reload(session_state)
        importlib.reload(ghost_cache)
        importlib.reload(ghost_pipeline)
        importlib.reload(fcurve_utils)
        importlib.reload(easing_presets)
        importlib.reload(target_binding)
        importlib.reload(snapshot_storage)
        importlib.reload(snapshot)
        importlib.reload(physics_archetypes)
        importlib.reload(physics_suggest)
        importlib.reload(export_import)
        importlib.reload(modal_operator)
        importlib.reload(selection_operators)
        importlib.reload(diff_mode)
        importlib.reload(mesh_ghosts)
        importlib.reload(motion_paths)
        importlib.reload(path_handle_drag)
        importlib.reload(draw_to_keys_math)
        importlib.reload(draw_to_keys)
        importlib.reload(settings_editor)
        importlib.reload(viewport_draw)
        importlib.reload(ui_panel)
        importlib.reload(preferences)
        importlib.reload(shelf_width)
        importlib.reload(api)

    _modules_loaded = True

    return {
        "utils": utils,
        "ghost_data": ghost_data,
        "session_state": session_state,
        "ghost_cache": ghost_cache,
        "ghost_pipeline": ghost_pipeline,
        "fcurve_utils": fcurve_utils,
        "easing_presets": easing_presets,
        "snapshot_storage": snapshot_storage,
        "snapshot": snapshot,
        "physics_archetypes": physics_archetypes,
        "physics_suggest": physics_suggest,
        "export_import": export_import,
        "modal_operator": modal_operator,
        "selection_operators": selection_operators,
        "diff_mode": diff_mode,
        "mesh_ghosts": mesh_ghosts,
        "motion_paths": motion_paths,
        "path_handle_drag": path_handle_drag,
        "draw_to_keys": draw_to_keys,
        "settings_editor": settings_editor,
        "viewport_draw": viewport_draw,
        "ui_panel": ui_panel,
        "preferences": preferences,
        "shelf_width": shelf_width,
        "api": api,
    }


# ---------------------------------------------------------------------------
# Registration Order
# ---------------------------------------------------------------------------

_REGISTER_ORDER = [
    "ghost_data",
    "session_state",
    "ghost_pipeline",
    "easing_presets",
    "snapshot_storage",
    "snapshot",
    "physics_suggest",
    "export_import",
    "modal_operator",
    "selection_operators",
    "diff_mode",          # Must come before viewport_draw (draw_diff_overlay is called from there)
    "mesh_ghosts",
    "motion_paths",
    "path_handle_drag",   # before preferences: its Shift+G item must precede the marker drag's
    "draw_to_keys",
    "viewport_draw",
    "ui_panel",
    "settings_editor",
    "preferences",
    "shelf_width",
]


def _register_supported() -> None:
    """Register the full Ghost Tool addon (Bforartists only)."""
    from . import utils
    import traceback

    _clear_pycache()

    modules = _import_modules()

    utils.log("Registering addon...")

    registered = []

    for module_name in _REGISTER_ORDER:
        module = modules.get(module_name)
        if module and hasattr(module, 'register'):
            try:
                module.register()
                registered.append(module)
                utils.log(f"  Registered: {module_name}")
            except Exception as exc:
                utils.warn(f"ERROR registering {module_name}: {exc}")
                traceback.print_exc()

                for prev_mod in reversed(registered):
                    try:
                        prev_mod.unregister()
                    except Exception:
                        traceback.print_exc()

                raise RuntimeError(
                    f"Ghost Tool registration failed at {module_name}: {exc}"
                ) from exc

    utils.log(f"Addon v{'.'.join(str(v) for v in bl_info['version'])} registered.")


def _unregister_supported() -> None:
    """Unregister the full Ghost Tool addon (Bforartists only)."""
    from . import utils

    # Unregister the exact class objects registered above. Reloading here
    # creates fresh classes without Blender RNA metadata and leaks the originals.
    modules = _import_modules(reload_modules=False)

    utils.log("Unregistering addon...")
    errors = []
    modules["session_state"].SessionState.cancel_active()

    for module_name in reversed(_REGISTER_ORDER):
        module = modules.get(module_name)
        if module and hasattr(module, 'unregister'):
            try:
                module.unregister()
                utils.log(f"  Unregistered: {module_name}")
            except Exception as exc:
                errors.append(f"{module_name}: {exc}")
                utils.warn(f"ERROR unregistering {module_name}: {exc}")
                import traceback
                traceback.print_exc()

    try:
        from . import api
        api.clear_all_callbacks()
    except Exception as exc:
        utils.warn(f"Failed to clear API callbacks during unregister: {exc}")

    from .fcurve_utils import invalidate_keyframe_cache, clear_frame_cache
    invalidate_keyframe_cache()
    clear_frame_cache()

    try:
        from .session_state import SessionState
        SessionState.clear_all_instances()
    except Exception as exc:
        utils.warn(f"Failed to clear SessionState during unregister: {exc}")

    try:
        from .ghost_data import DiffReference
        DiffReference.clear_all()
    except Exception as exc:
        utils.warn(f"Failed to clear DiffReference instances during unregister: {exc}")

    if errors:
        raise RuntimeError("Ghost Tool teardown failed: " + "; ".join(errors))

    utils.log("Addon unregistered.")


# ---------------------------------------------------------------------------
# Unsupported-platform stub (visible in Blender addon preferences)
# ---------------------------------------------------------------------------

class GHOSTTOOL_AP_preferences_stub(bpy.types.AddonPreferences):
    """Static preferences panel shown on standard Blender."""
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Ghost Tool is a Bforartists exclusive.", icon='ERROR')
        box.label(text="This add-on does not work in standard Blender.")
        box.operator("wm.url_open", text="Get Bforartists", icon='URL').url = "https://www.bforartists.de"


_stub_registered = False


# ---------------------------------------------------------------------------
# Public register / unregister
# ---------------------------------------------------------------------------

def register() -> None:
    global _real_addon_registered, _stub_registered

    if not _is_bforartists():
        if not _stub_registered:
            bpy.utils.register_class(GHOSTTOOL_AP_preferences_stub)
            _stub_registered = True
        print("[Ghost Tool] Bforartists exclusive — not available for standard Blender.")
        return

    _register_supported()
    _real_addon_registered = True


def unregister() -> None:
    global _real_addon_registered, _stub_registered

    if not _real_addon_registered:
        if _stub_registered:
            try:
                bpy.utils.unregister_class(GHOSTTOOL_AP_preferences_stub)
            except RuntimeError:
                pass
            _stub_registered = False
        return

    _unregister_supported()
    _real_addon_registered = False


# ---------------------------------------------------------------------------
# Allow running as a script for quick testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    register()
