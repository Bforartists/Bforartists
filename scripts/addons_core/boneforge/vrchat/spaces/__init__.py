"""BoneCraft VRChat Spaces — Custom UI Panel Organization.

Register four main workspace panels for the VRChat Avatar Builder:
Window 1: Avatar Builder (primary workflow)
Window 2: Rig Mapping (humanoid and naming)
Window 3: Physics Workshop (cloth sim and chains)
Window 4: Publish (optimization and export)

Category: VRChat Spaces.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all space modules."""
    import importlib
    from boneforge.vrchat.spaces import window1, window2, window3, window4

    module_list = [
        window1,
        window2,
        window3,
        window4,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all space modules."""
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
