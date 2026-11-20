"""BoneCraft VRChat — Hair Physics System.

Provides PhysBone chain detection, configuration, generation, and collider setup
for hair, tails, skirts, and other physics-enabled accessories.

Modules:
  - detector: Scan armature for bone chain candidates
  - physbone: PhysBone parameter presets and configuration
  - generator: Generate bone chains through mesh geometry
  - collision: Place colliders for hair physics interaction

Category: Hair Physics.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all hair physics modules.

    Imports and reloads each module, then calls its register() function.
    Failures in individual modules do not prevent others from loading.
    """
    import importlib
    from boneforge.vrchat.hair import detector, physbone, generator, collision

    module_list = [
        detector,
        physbone,
        generator,
        collision,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all hair physics modules in reverse order.

    Calls unregister() on each module and clears the module list.
    """
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
