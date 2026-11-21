"""BoneCraft VRChat — Performance Tools.

Analyzes and optimizes avatar performance for VRChat across multiple
metrics including polygon count, bones, materials, and PhysBones.
Provides tools for decimation with shape key safety and automatic optimization.

Each module can be independently disabled from addon preferences.
"""

import logging

logger = logging.getLogger(__name__)

# Sub-modules are imported lazily during register() so that
# a failure in one module does not prevent others from loading.

_modules = []


def register():
    """Register all performance modules with error handling.

    Imports and reloads each module, then calls its register() function.
    Failures in individual modules do not prevent others from loading.
    """
    import importlib
    from boneforge.vrchat.performance import rank, decimation, optimizer

    module_list = [
        rank,
        decimation,
        optimizer,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all performance modules in reverse order.

    Calls unregister() on each module and clears the module list.
    """
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
