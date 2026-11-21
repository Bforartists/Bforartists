"""BoneCraft — Control Picker / Rig UI layer (R7, BF-UI-01).

A clean-room, BoneCraft-native graphical control picker for generated rigs:
a clickable control layout (auto-generated from a rig's bone collections,
import/export as BoneCraft JSON), named selection sets with side-mirror,
inline IK/FK from the control-usability layer, per-control colour, per-character
state, and a floating popup picker.

Interaction model chosen by the R6 spike: a ``UILayout`` grid of per-control
operator buttons backed by a selection operator (sets the active bone always;
extends the viewport selection where a 3D area exists). ``Bone.select`` is gone
in Bforartists 5.2, so selection routes through the active-bone API + pose
operators — never a raw select flag.

Bforartists-exclusive: this whole package registers only behind the BFA guard
and is asserted absent under standard Blender in ``test_bfa_lock.py``.

Manifest id: ``control_ui``.
"""
import logging
import traceback

logger = logging.getLogger(__name__)

_SUBMODULES = ("picker", "selection_sets", "picker_editor", "popup")
_registered = []


def register():
    for name in _SUBMODULES:
        try:
            mod = __import__("%s.%s" % (__package__, name), fromlist=[name])
            mod.register()
            _registered.append(mod)
        except Exception as exc:
            traceback.print_exc()
            logger.error("[BoneCraft control_ui] failed to register %s: %s",
                         name, exc)


def unregister():
    for mod in reversed(_registered):
        try:
            mod.unregister()
        except Exception:
            traceback.print_exc()
    _registered.clear()


def _get_manifest():
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="control_ui",
        name="Control Picker / Rig UI",
        description=(
            "Graphical control picker for generated rigs: clickable control "
            "layout, selection sets + mirror, inline IK/FK, popup picker."
        ),
        icon="RESTRICT_SELECT_OFF",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
