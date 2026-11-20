"""BoneCraft -- Advanced Rigging Systems.

Riggers' verbs that go beyond bone collections and weight painting.
Everything here either *creates* a Blender constraint setup, *adds*
driver wiring, or *audits* an existing rig for shipping issues.

Sub-modules
-----------
``rig_validator``   Audit pass that flags shipping risks: unbaked
                    constraints, off-axis bone rolls, deform bones
                    without weights, mesh references to missing
                    vertex groups. Surfaces results in the Task
                    Board so users can fix-and-recheck without
                    leaving the panel.
``space_switch``    Builds the parent / world / ik-target switch
                    setup used on hands and feet. Wires a
                    Copy Transforms constraint with custom-property
                    drivers; the operator names the bones with the
                    canonical ``.space`` suffix so the validator
                    recognises them later.
``control_layer``   Animator usability layer for generated control
                    rigs: no-pop IK/FK snap + frame-range bake, pole
                    follow, IK pin, foot-roll keying, lock-free limb
                    inheritance, global rig scale, and per-character
                    control state. Built on the pure ``control_math``
                    kernel.
``spline_ik``       Convert a chain into a spline-IK rig with
                    auto-generated control bones spaced along the
                    curve.
``ribbon``          Bezier-ribbon setup -- a curve plus a row of
                    bones plus a Spline IK plus shape widgets from
                    ``weights.shapes``.
``chain_dynamics``  Wire a chain into a soft-body / cloth driver so
                    physics bakes back into pose-bone rotation.
``viseme``          Attach an action / shape-key strip per phoneme
                    to a viseme rig. Used by ``vrchat.visemes`` and
                    by the ``advanced_rigging`` viseme panel.
``sdk_system``      Set-Driven-Key authoring -- pick a driver bone,
                    set min/max poses, BoneCraft writes the F-Curve
                    data. Faster than Blender's Driver Editor for
                    common cases.
``rig_notes``       Per-armature README field, stored as a custom
                    property; rendered as a panel in the Rig Builder
                    sidebar.
``game_export``     Stub kept registered so the manifest entry
                    remains valid; real game-export logic moved to
                    ``vrchat.export.vrchat_export`` and
                    ``io_hub.game_export`` in earlier versions.

Manifest id: ``phase2c_advanced``.
"""

import logging
import traceback

logger = logging.getLogger(__name__)

# Sub-modules registered in order; walked in reverse on teardown.
_registered_submodules: list = []

# Order matters: ``rig_validator`` registers the result schema
# other sub-modules push findings into.
_SUBMODULE_NAMES = (
    "rig_validator",
    "space_switch",
    "control_layer",
    "spline_ik",
    "ribbon",
    "chain_dynamics",
    "viseme",
    "sdk_system",
    "rig_notes",
    "game_export",
)


def register():
    """Register every sub-module of ``advanced_rigging``."""
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
                "[BoneCraft advanced_rigging] failed to register %s: "
                "%s: %s",
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
                "[BoneCraft advanced_rigging] failed to unregister "
                "%s: %s: %s",
                submodule.__name__, type(exc).__name__, exc,
            )
    _registered_submodules.clear()


# -- Tool Registry manifest ------------------------------------------

def _get_manifest():
    """Return the ``ToolManifest`` for Advanced Rigging Systems."""
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="phase2c_advanced",  # stable id -- DO NOT rename.
        name="Advanced Rigging Systems",
        description=(
            "Rig validator, space-switch, spline IK, ribbons, chain "
            "dynamics, viseme, SDK, rig notes."
        ),
        icon="CONSTRAINT",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
