"""BoneCraft -- Auto-Rigging Wizard.

The largest single feature in BoneCraft: an in-viewport auto-rigger
that places markers on a target mesh, infers landmarks, generates a
body / finger / face rig, retargets a Mixamo / Rigify reference, and
hands the result off to ``weights`` for skinning.

The wizard is *step-driven* -- the user moves through Place, Infer,
Generate, Skin, Retarget. State for each step lives on a
``WizardSession`` PropertyGroup (see ``session.py``) on the scene,
so a half-finished rig survives a save/load round-trip.

Sub-modules (in registration order)
-----------------------------------
``session``       PropertyGroup definitions -- the data model the
                  wizard mutates. Registered first because every
                  other sub-module references the property types.
``skin_gen``      Skinning pipeline: heat-map, AO-weighted
                  proximity, Voxel Heat Diffuse fall-back. Pure
                  helper -- no UI.
``inference``     Operators that run the marker-to-landmark
                  inference. Reads ``session`` state, writes back
                  inferred positions.
``wizard``        The main wizard panel + operators (Next, Back,
                  Reset). Calls into ``body_gen``, ``finger_gen``,
                  ``face_gen``, ``merge``.
``body_gen``      Builds the spine / arms / legs armature.
``finger_gen``    Builds the finger chains; called per-hand.
``face_gen``      Builds eye, jaw, lid, brow controls. Imports
                  shape primitives from ``weights.shapes``.
``merge``         Glues body + face + fingers into one armature
                  with a single root and clean parenting; runs
                  ``ui_panels.bookmarks`` and ``animation.correctives``
                  hooks for a turnkey rig.
``retarget``      Mixamo / Rigify -> BoneCraft bone mapping. Uses
                  the constant tables in ``constants.py``.
``quick_human``   v3.3.6+ ``BF_OT_AddHumanArmature`` -- one-click
                  human metarig add for users who don't want to
                  walk through the wizard.
``mannequin``     v3.8.0+ procedural mannequin generator -- builds
                  a low-poly, weight-matched mesh under the rig so
                  the user has something to skin against
                  immediately.

Manifest id: ``phase3_autorig``.
"""

import logging
import traceback

logger = logging.getLogger(__name__)

# Sub-modules in successful-registration order; walked in reverse
# on teardown.
_registered_submodules: list = []

# Strict dependency order:
#   1. Session PropertyGroups (leaf -> root)
#   2. Skin pipeline helpers
#   3. Inference operators
#   4. Wizard shell + step operators
#   5. Rig generators (body, fingers, face, merge)
#   6. Retarget tables
#   7. Quick-human one-click operator
#   8. Mannequin generator
_SUBMODULE_NAMES = (
    "session",
    "skin_gen",
    "inference",
    "wizard",
    "tools",             # Place Rig Markers: the wizard's marker placement as a viewport tool
    "body_gen",
    "finger_gen",
    "face_gen",
    "merge",
    "retarget",
    "quick_human",
    "rig_assets",        # BoneCraft Rigs asset library + shelf
    "mannequin",
    "rig_build",     # control-rig construction engine (BFA)
    "joint_correctives",   # bend-driven corrective shape keys (BFA)
    "face_controls",       # eye aim, lids, lip follow on wizard faces (BFA)
    "skirt_rig",           # skirt bones that follow the legs (BFA)
)


def register():
    """Register every sub-module of ``autorig``.

    Sub-modules are imported in dependency order so that property
    groups declared in ``session`` are available when the wizard
    operators reference them. A failure in one sub-module is logged
    but does not prevent the others from loading.
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
                "[BoneCraft autorig] failed to register %s: %s: %s",
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
                "[BoneCraft autorig] failed to unregister %s: %s: %s",
                submodule.__name__, type(exc).__name__, exc,
            )
    _registered_submodules.clear()


# -- Tool Registry manifest ------------------------------------------

def _get_manifest():
    """Return the ``ToolManifest`` for Auto-Rigging Wizard.

    Lazy-imported to avoid an eager dependency cycle if this package
    is imported before ``boneforge.core``.
    """
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="phase3_autorig",  # stable id -- DO NOT rename.
        name="Auto-Rigging Wizard",
        description=(
            "In-viewport auto-rigger: body / finger / face generators, "
            "Mixamo/Rigify retarget, mannequin, and one-click human metarig."
        ),
        icon="ARMATURE_DATA",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
