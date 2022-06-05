# SPDX-License-Identifier: GPL-2.0-or-later

import importlib


# Submodules to load during register
submodules = (
    'copy_mirror_parameters',
    'upgrade_face',
)

loaded_submodules = []


def register():
    # Lazily load modules to make reloading easier. Loading this way
    # hides the sub-modules and their dependencies from initial_load_order.
    loaded_submodules[:] = [
        importlib.import_module(__name__ + '.' + name) for name in submodules
    ]

    for mod in loaded_submodules:
        mod.register()


def unregister():
    for mod in reversed(loaded_submodules):
        mod.unregister()

    loaded_submodules.clear()
