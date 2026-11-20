"""BoneCraft -- Weight & Deform Tools.

Operators, panels, and helpers that sit between the rig and the
mesh: vertex-group manipulation, deform-bone toggling, mush /
proximity-wrap modifiers, and the shared custom-shape geometry
library used by other packages to draw bone widgets.

Sub-modules
-----------
``shapes``           Re-usable widget geometry generators (circles,
                     diamonds, sphere wires). Other packages
                     (``advanced_rigging.ribbon``,
                     ``advanced_rigging.spline_ik``,
                     ``autorig.face_gen``) import from here, so
                     ``shapes`` registers first.
``weight_mirror``    Topology-aware mirror across the YZ plane,
                     with a falls-back-to-Blender-symmetrize toggle
                     when topology isn't symmetric.
``weight_transfer``  Wraps Blender's data-transfer modifier with
                     bake-and-clean-up so the result is a clean
                     vertex-group set, not a stack of modifiers.
``weight_table``     Tabular editor for per-vertex weights against
                     a chosen vertex-group set; pin / lock / scrub.
``weight_tools``     Flood-fill, normalise, smooth, prune-zero --
                     the small everyday verbs.
``deform_control``   Toggle ``bone.use_deform`` in bulk; useful
                     when a control rig has helper bones that
                     should not contribute to the bind.
``delta_mush``       Helpers that pre-bake a delta-mush smooth into
                     vertex groups so a game export keeps the
                     visual result without the modifier.
``proximity_wrap``   Wrap modifier preset for snapping clothing to
                     a body mesh during fitting.

Manifest id: ``phase2b_weights``.
"""

import logging
import traceback

logger = logging.getLogger(__name__)

# Sub-modules registered in order; walked in reverse on teardown.
_registered_submodules: list = []

# Order matters: ``shapes`` defines geometry generators imported by
# other sub-modules, so it must register first.
_SUBMODULE_NAMES = (
    "shapes",
    "weight_mirror",
    "weight_transfer",
    "weight_table",
    "weight_tools",
    "deform_control",
    "delta_mush",
    "proximity_wrap",
)


def register():
    """Register every sub-module of ``weights``.

    A failure in one sub-module is logged with a full traceback;
    the loop keeps going so a single bug cannot disable the whole
    package.
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
                "[BoneCraft weights] failed to register %s: %s: %s",
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
                "[BoneCraft weights] failed to unregister %s: %s: %s",
                submodule.__name__, type(exc).__name__, exc,
            )
    _registered_submodules.clear()


# -- Tool Registry manifest ------------------------------------------

def _get_manifest():
    """Return the ``ToolManifest`` for Weight & Deform Tools."""
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="phase2b_weights",  # stable id -- DO NOT rename.
        name="Weight & Deform Tools",
        description=(
            "Weight mirror, weight transfer, weight table, deform "
            "control, delta mush, proximity wrap, shapes library."
        ),
        icon="MOD_VERTEX_WEIGHT",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
