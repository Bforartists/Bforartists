# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Paul "BrikBot" Marshall
# Created: July 1, 2011
# Last Modified: September 26, 2013
# Homepage (blog): http://post.darkarsenic.com/
#                       //blog.darkarsenic.com/
# Thanks to Meta-Androco, RickyBlender, Ace Dragon, and PKHG for ideas
#   and testing.
#
# Coded in IDLE, tested in Blender 2.68a.  NumPy Recommended.
# Search for "@todo" to quickly find sections that need work.

bl_info = {
    "name": "Rock Generator",
    "author": "Paul Marshall (brikbot)",
    "version": (1, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Rock Generator",
    "description": "Adds a mesh rock to the Add Mesh menu",
    "doc_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
    "Scripts/Add_Mesh/Rock_Generator",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Add Mesh",
}

if "bpy" in locals():
    import importlib
    importlib.reload(rockgen)

else:
    from . import rockgen

import bpy


# Register:
def register():
    rockgen.register()


def unregister():
    rockgen.unregister()


if __name__ == "__main__":
    register()
