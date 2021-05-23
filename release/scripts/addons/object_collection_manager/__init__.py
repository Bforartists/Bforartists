# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2011, Ryan Inch

bl_info = {
    "name": "Collection Manager",
    "description": "Manage collections and their objects",
    "author": "Ryan Inch",
    "version": (2, 21, 4),
    "blender": (2, 80, 0),
    "location": "View3D - Object Mode (Shortcut - M)",
    "warning": '',  # used for warning icon and text in addons panel
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/collection_manager.html",
    "tracker_url": "https://blenderartists.org/t/release-addon-collection-manager-feedback/1186198/",
    "category": "Interface",
}


if "bpy" in locals():
    import importlib

    importlib.reload(cm_init)
    importlib.reload(internals)
    importlib.reload(operator_utils)
    importlib.reload(operators)
    importlib.reload(qcd_move_widget)
    importlib.reload(qcd_operators)
    importlib.reload(ui)
    importlib.reload(qcd_init)
    importlib.reload(preferences)

else:
    from . import cm_init
    from . import internals
    from . import operator_utils
    from . import operators
    from . import qcd_move_widget
    from . import qcd_operators
    from . import ui
    from . import qcd_init
    from . import preferences

import bpy

def register():
    cm_init.register_cm()

    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.register_qcd()

def unregister():
    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.unregister_qcd()

    cm_init.unregister_cm()


if __name__ == "__main__":
    register()
