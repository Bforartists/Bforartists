"""BoneCraft VRChat Visemes — Viseme and Expression Mapping.

Register viseme mapper and face tracking subsystems.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all viseme and expression modules."""
    import importlib
    from boneforge.vrchat.visemes import vrchat_mapper, face_tracking

    module_list = [
        vrchat_mapper,
        face_tracking,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all viseme and expression modules."""
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
