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
    Boltfactory.register()


def unregister():
    Boltfactory.unregister()


if __name__ == "__main__":
    register()
