"""BoneCraft VRChat — Clothing Merge System.

Provides clothing item merging with bone matching, collision detection,
weight transfer, and armature integration.

Modules:
  - bone_match: Bone matching with confidence scoring
  - collision: Bone name collision detection and resolution
  - merge: Main merge engine with 6-step process

Category: Clothing.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all clothing merge modules.

    Imports and reloads each module, then calls its register() function.
    Failures in individual modules do not prevent others from loading.
    """
    import importlib
    from boneforge.vrchat.clothing import bone_match, collision, merge

    module_list = [
        bone_match,
        collision,
        merge,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all clothing merge modules in reverse order.

    Calls unregister() on each module and clears the module list.
    """
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
