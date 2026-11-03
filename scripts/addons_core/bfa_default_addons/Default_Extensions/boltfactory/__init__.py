# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later
"""
Boltfactory Extension registration file
"""

import os

if "bpy" not in locals():
    import bpy
    from . import Boltfactory
    from . import createMesh
else:
    import importlib
    importlib.reload(Boltfactory)
    importlib.reload(createMesh)


def register():
    """Register Boltfactory in Blender"""

    Boltfactory.register()

    # Install Presets
    if register_preset_path := getattr(bpy.utils, "register_preset_path", None):
        register_preset_path(os.path.join(os.path.dirname(__file__)))


def unregister():
    """Un-Register Boltfactory in Blender"""

    # Remove Presets
    if unregister_preset_path := getattr(bpy.utils, "unregister_preset_path", None):
        unregister_preset_path(os.path.join(os.path.dirname(__file__)))

    Boltfactory.unregister()


if __name__ == "__main__":
    register()
