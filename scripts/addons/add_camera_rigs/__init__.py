# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Add Camera Rigs",
    "author": "Wayne Dixon, Brian Raschko, Kris Wittig, Damien Picard, Flavio Perez",
    "version": (1, 5, 1),
    "blender": (3, 3, 0),
    "location": "View3D > Add > Camera > Dolly or Crane Rig",
    "description": "Adds a Camera Rig with UI",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/camera/camera_rigs.html",
    "tracker_url": "https://github.com/waylow/add_camera_rigs/issues",
    "category": "Camera",
}

import bpy
import os

from . import build_rigs
from . import operators
from . import ui_panels
from . import prefs
from . import composition_guides_menu

# =========================================================================
# Registration:
# =========================================================================

def register():
    build_rigs.register()
    operators.register()
    ui_panels.register()
    prefs.register()
    composition_guides_menu.register()


def unregister():
    build_rigs.unregister()
    operators.unregister()
    ui_panels.unregister()
    prefs.unregister()
    composition_guides_menu.unregister()


if __name__ == "__main__":
    register()
