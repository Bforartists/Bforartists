"""BoneCraft -- Rig UI & Viewport Controls.

This package owns the read-only sidebar panels for an armature: the
bone-collection manager, the visibility bookmarks, and the hotkey
popup. It does *not* generate or modify bones; it presents them.

Sub-modules
-----------
``collection_ui``    Bone Collection list, drag-reorder, color/icon
                     overrides, BoneCraft per-armature settings
                     (registered as ``Object.boneforge_settings``).
``bookmarks``        Named visibility bookmarks. Snapshot which bone
                     collections / layers are visible, restore them
                     in one click. Used by the auto-rigger after a
                     merge to pre-populate sensible bookmarks.
``hotkey_popup``     The Q / pie-menu popup that surfaces frequent
                     bone-collection toggles without leaving the
                     viewport.

Manifest id: ``phase1_panels`` (preserved from earlier versions so
existing user preferences continue to enable this package).

Known issue prior to 7.2.1
--------------------------
Earlier releases referenced the sub-modules by bare name inside
``register()`` without importing them at module top, which would
NameError on first register. Fixed in 7.2.1: sub-modules are now
imported via ``__import__`` (matching the other feature packages),
so a single sub-module failure cannot crash the whole package.
"""

import logging
import traceback

logger = logging.getLogger(__name__)

# Modules registered (in this order); populated by register() and
# walked in reverse by unregister().
_registered_submodules: list = []

# Sub-modules in dependency order. ``collection_ui`` defines the
# property group that ``bookmarks`` and ``hotkey_popup`` reference,
# so it must register first.
_SUBMODULE_NAMES = (
    "collection_ui",
    "bookmarks",
    "hotkey_popup",
)


def register():
    """Register every sub-module of ``ui_panels``.

    Failures in one sub-module do not prevent others from loading --
    the failure is logged with a full traceback and the loop
    continues. Sub-modules are imported via ``__import__`` so a
    raised ImportError surfaces with a meaningful message.
    """
    for submodule_name in _SUBMODULE_NAMES:
        try:
            submodule = __import__(
                f"{__package__}.{submodule_name}",
                fromlist=[submodule_name],
            )
            submodule.register()
            _registered_submodules.append(submodule)
        except Exception as exc:
            traceback.print_exc()
            logger.error(
                "[BoneCraft ui_panels] failed to register %s: %s: %s",
                submodule_name, type(exc).__name__, exc,
            )


def unregister():
    """Unregister sub-modules in reverse-of-registration order."""
    for submodule in reversed(_registered_submodules):
        try:
            submodule.unregister()
        except Exception as exc:
            traceback.print_exc()
            logger.error(
                "[BoneCraft ui_panels] failed to unregister %s: %s: %s",
                submodule.__name__, type(exc).__name__, exc,
            )
    _registered_submodules.clear()


# -- Tool Registry manifest ------------------------------------------

def _get_manifest():
    """Return the ``ToolManifest`` for the Rig UI & Viewport Controls.

    Lazy-imported because the registry module lives under
    ``boneforge.core`` and we want to avoid an eager dependency cycle
    if this package is imported before ``boneforge.core``.
    """
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="phase1_panels",  # stable id -- DO NOT rename.
        name="Rig UI & Viewport Controls",
        description=(
            "Bone-collection panel, visibility bookmarks, hotkey "
            "popup, 2D silhouette."
        ),
        icon="ARMATURE_DATA",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
