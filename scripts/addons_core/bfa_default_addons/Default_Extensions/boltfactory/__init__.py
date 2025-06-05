# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    import importlib
    importlib.reload(Boltfactory)
    importlib.reload(createMesh)
else:
    from . import Boltfactory
    from . import createMesh

import bpy


# ### REGISTER ###


def register():
    import os

    Boltfactory.register()

    # Presets
    if register_preset_path := getattr(bpy.utils, "register_preset_path", None):
        register_preset_path(os.path.join(os.path.dirname(__file__)))


def unregister():
    import os

    # Presets
    if unregister_preset_path := getattr(bpy.utils, "unregister_preset_path", None):
        unregister_preset_path(os.path.join(os.path.dirname(__file__)))

    Boltfactory.unregister()


if __name__ == "__main__":
    register()
