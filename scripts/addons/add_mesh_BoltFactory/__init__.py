# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "BoltFactory",
    "author": "Aaron Keith",
    "version": (0, 4, 0),
    "blender":  (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Add a bolt or nut",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_mesh/boltfactory.html",
    "category": "Add Mesh",
}


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
    Boltfactory.register()



def unregister():
    Boltfactory.unregister()


if __name__ == "__main__":
    register()
