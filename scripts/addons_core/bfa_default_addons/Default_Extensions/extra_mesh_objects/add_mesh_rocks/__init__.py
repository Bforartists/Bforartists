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
