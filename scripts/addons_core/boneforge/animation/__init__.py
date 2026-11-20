"""BoneCraft -- Animation Workflow.

Lives next to ``ui_panels`` but is concerned with *animating* an
existing rig rather than presenting it: pose snapshots, F-Curve
tools, Rigify-specific helpers, and corrective shape keys driven by
bone rotation.

Sub-modules
-----------
``pose_library``     Disk-backed pose library (a thin layer over
                     Blender's Asset Browser data) so a single rig
                     can carry its own pose set without depending on
                     the global asset library.
``graph_tools``      Graph Editor + Dope Sheet utilities -- snap
                     handles, set tangents in bulk, scrub easing.
``rigify_enhance``   IK/FK match, snap-to-bone, switch limbs --
                     wraps the Rigify rig_ui add-on with a panel
                     that looks consistent across Rigify versions.
``correctives``      Corrective shape keys driven by a bone's local
                     rotation. Drivers are wired automatically; the
                     UI exposes a "Sculpt at this pose" workflow.

Disabled in this release (kept on disk for re-enable):
``anim_layers`` -- removed in v3.0.16 because Blender's NLA already
covers the workflow.
``tween``       -- removed in v3.0.26 because the Dope Sheet's
                  breakdown / blend-to-neighbour keys cover it.

Manifest id: ``phase2_animation``.
"""

import logging
import traceback

logger = logging.getLogger(__name__)

# Sub-modules in successful-registration order; walked in reverse
# for unregister.
_registered_submodules: list = []

# Sub-modules in dependency order. ``correctives`` registers a
# driver utility ``rigify_enhance`` may call, so it loads last.
_SUBMODULE_NAMES = (
    "pose_library",
    "graph_tools",
    "rigify_enhance",
    "correctives",
)


def register():
    """Register every sub-module of ``animation``.

    Sub-modules are imported by name through ``__import__`` so a
    failure surfaces with a clean ImportError. A failure in one
    sub-module is logged but does not prevent the others from
    loading.
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
                "[BoneCraft animation] failed to register %s: %s: %s",
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
                "[BoneCraft animation] failed to unregister %s: %s: %s",
                submodule.__name__, type(exc).__name__, exc,
            )
    _registered_submodules.clear()


# -- Tool Registry manifest ------------------------------------------

def _get_manifest():
    """Return the ``ToolManifest`` for Animation Workflow.

    Lazy-imported because the registry module lives under
    ``boneforge.core`` and we want to avoid an eager dependency cycle
    if this package is imported before ``boneforge.core``.
    """
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="phase2_animation",  # stable id -- DO NOT rename.
        name="Animation Workflow",
        description=(
            "Pose library, graph/viewport tools, Rigify enhancement, "
            "corrective shape keys."
        ),
        icon="ACTION",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
