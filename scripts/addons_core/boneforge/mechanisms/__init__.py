"""BoneCraft Mechanisms: interlocking mechanical rigs built from native bones and constraints.

Records live on the armature (``Armature.bonecraft_mech``); the pure planner
turns them into tagged bones, constraints, drivers and actions; ``build.py``
applies them in place. Registered as ToolManifest ``mechanisms``.
"""
import logging

logger = logging.getLogger(__name__)

# Blender-side submodules, registered in this order (Task 9 onward add to it).
_SUBMODULES = ("records", "build", "ops", "test_sweep", "guide", "ui", "validate", "tools")


def register():
    for name in _SUBMODULES:
        try:
            __import__(f"{__name__}.{name}", fromlist=[name]).register()
        except Exception as exc:                       # noqa: BLE001 - one broken module must not block the rest
            logger.error("[BoneCraft] mechanisms.%s failed to register: %s", name, exc)


def unregister():
    for name in reversed(_SUBMODULES):
        try:
            __import__(f"{__name__}.{name}", fromlist=[name]).unregister()
        except Exception:                              # noqa: BLE001
            pass


def _get_manifest():
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="mechanisms",
        name="Mechanisms",
        description="Hinges, slides, telescopes, pistons, gears, follows and sequences for mechanical rigs.",
        icon="MOD_BUILD",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
