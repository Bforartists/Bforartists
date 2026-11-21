"""BoneCraft VRChat — Naming Conventions.

Tools for detecting and applying bone naming conventions,
including preset loading and batch rename operations.

Modules:
  - detector: Scan bones and detect naming convention
  - presets: Load and apply JSON mapping presets
  - batch_rename: Find/replace, prefix, suffix, regex tools

Category: VRChat Naming.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all naming convention modules.

    Imports and reloads each module, then calls its register() function.
    Failures in individual modules do not prevent others from loading.
    """
    import importlib
    from boneforge.vrchat.naming import detector, presets, batch_rename

    module_list = [
        detector,
        presets,
        batch_rename,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all naming modules in reverse order.

    Calls unregister() on each module and clears the module list.
    """
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
