"""BoneCraft VRChat Humanoid — Humanoid Bone Mapping and Validation.

Register humanoid mapper, eye setup, and validation subsystems.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all humanoid modules."""
    import importlib
    from boneforge.vrchat.humanoid import mapper, eye_setup, validator

    module_list = [
        mapper,
        eye_setup,
        validator,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all humanoid modules."""
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
