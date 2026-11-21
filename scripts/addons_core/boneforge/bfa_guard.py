"""BoneCraft runtime validation.

This build of BoneCraft is exclusive to Bforartists. In other hosts it
registers only an install guidance notice and does not load functional
feature packages.
"""

import logging
import sys

logger = logging.getLogger(__name__)

# The add-on package id as Blender sees it (folder name of the
# installed add-on). AddonPreferences.bl_idname must match it.
_ADDON_ID = __package__ or "boneforge"

_DOWNLOAD_URL = "https://www.bforartists.de/download/"

LOCK_TITLE = "BoneCraft — Bforartists required"
LOCK_LINES = (
    "This build of BoneCraft is exclusive to Bforartists.",
    "It will not run in standard Blender.",
    "Install it in Bforartists, or download Bforartists below.",
)


# -- Host validation ----------------------------------------------------

def detection_signals():
    """Return internal host-validation indicators for this process."""
    signals = []
    try:
        import bpy
    except ImportError:
        # Not running inside a Blender-derived host at all (unit
        # tests, linters). The guard has nothing to decide here.
        return signals

    app = bpy.app

    try:
        if getattr(app, "bforartists_version", None):
            signals.append("app.bforartists_version")
    except Exception:
        pass

    try:
        if "bforartists" in (getattr(app, "binary_path", "") or "").lower():
            signals.append("binary_path")
    except Exception:
        pass

    try:
        if "bforartists" in (sys.executable or "").lower():
            signals.append("sys.executable")
    except Exception:
        pass

    for resource_kind in ("USER", "LOCAL", "SYSTEM"):
        try:
            resource_dir = bpy.utils.resource_path(resource_kind) or ""
        except Exception:
            continue
        if "bforartists" in resource_dir.lower():
            signals.append("resource_path:%s" % resource_kind)

    return signals


def is_bforartists():
    """True when the running host is Bforartists."""
    return bool(detection_signals())


def require_bforartists(caller="boneforge"):
    """Raise ``RuntimeError`` unless running inside Bforartists.

    Inline re-checks in other modules use their own private copies of
    the detection; this helper exists for any future module that wants
    a guard without duplicating it.
    """
    if not is_bforartists():
        raise RuntimeError(
            "[%s] BoneCraft is exclusive to Bforartists and cannot "
            "run in standard Blender. Get Bforartists at %s"
            % (caller, _DOWNLOAD_URL)
        )


# -- Notice-only UI -----------------------------------------------------

def _build_lockout_classes():
    """Create the stub classes lazily so this module can be imported
    outside Blender (tests) without touching ``bpy.types``."""
    import bpy

    class BONEFORGE_OT_get_bforartists(bpy.types.Operator):
        """Open the Bforartists download page"""
        bl_idname = "boneforge.get_bforartists"
        bl_label = "Get Bforartists"

        def execute(self, context):
            bpy.ops.wm.url_open(url=_DOWNLOAD_URL)
            return {'FINISHED'}

    class BoneForgeLockedPreferences(bpy.types.AddonPreferences):
        bl_idname = _ADDON_ID

        def draw(self, context):
            layout = self.layout
            box = layout.box()
            box.alert = True
            box.label(text=LOCK_TITLE, icon='ERROR')
            for line in LOCK_LINES:
                box.label(text=line)
            row = box.row()
            row.operator(
                BONEFORGE_OT_get_bforartists.bl_idname, icon='URL',
            )

    return (BONEFORGE_OT_get_bforartists, BoneForgeLockedPreferences)


_lockout_classes = ()


def _popup_draw(self, context):
    for line in LOCK_LINES:
        self.layout.label(text=line)


def _notify_locked():
    """One-shot timer callback: surface the lock in the UI."""
    try:
        import bpy
        window_manager = bpy.context.window_manager
        if window_manager is not None:
            window_manager.popup_menu(
                _popup_draw, title=LOCK_TITLE, icon='ERROR',
            )
    except Exception:
        # Headless / background mode has no UI — console log suffices.
        pass
    return None


def register_lockout():
    """Register the notice-only UI for unsupported hosts."""
    global _lockout_classes
    import bpy

    logger.error(
        "[BoneCraft] Host is not Bforartists. "
        "No BoneCraft functionality has been registered. "
        "Exclusive package validation did not pass.",
    )

    _lockout_classes = _build_lockout_classes()
    for stub_class in _lockout_classes:
        try:
            bpy.utils.register_class(stub_class)
        except Exception:
            logger.exception(
                "[BoneCraft] notice stub %s failed to register",
                stub_class.__name__,
            )

    try:
        bpy.app.timers.register(_notify_locked, first_interval=0.5)
    except Exception:
        pass


def unregister_lockout():
    """Tear the notice-only UI back down."""
    global _lockout_classes
    import bpy

    for stub_class in reversed(_lockout_classes):
        try:
            bpy.utils.unregister_class(stub_class)
        except Exception:
            pass
    _lockout_classes = ()
