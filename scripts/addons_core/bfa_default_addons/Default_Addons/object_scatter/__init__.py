# SPDX-FileCopyrightText: 2010-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Scatter Objects",
    "author": "Jacques Lucke",
    "version": (0, 2),
    "blender": (3, 0, 0),
    "location": "3D View",
    "description": "Distribute object instances on another object.",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/object/scatter_objects.html",
    "tracker_url": "https://projects.blender.org/blender/blender-addons/issues",
    "support": 'OFFICIAL',
    "category": "Object",
}

from . import ui
from . import operator

def register():
    ui.register()
    operator.register()

def unregister():
    ui.unregister()
    operator.unregister()
