"""BoneCraft VRChat Export — FBX and sidecar generation.

Registers all VRChat export modules. Each module can be independently
disabled from addon preferences without affecting others.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all export modules with error handling."""
    import importlib
    from boneforge.vrchat.export import vrchat_export, sidecar

    module_list = [
        vrchat_export,
        sidecar,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all export modules in reverse order."""
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
