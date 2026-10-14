# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

# -----------------------------------------------------------------------------
# This addon is a Bforartists exclusive. Its folder ships the Legacy Add-ons
# (`Default_Addons`) and the Pre-downloaded Extensions (`Default_Extensions`),
# so they can be installed without internet access.
#
# Nothing is installed automatically. The install and remove operators live in
# `bl_pkg.bl_extension_ops` and are shown in the Extensions preferences, this
# add-on only shows the same buttons in its preferences.
# -----------------------------------------------------------------------------

import bpy

from bpy.types import (
    AddonPreferences,
    Context,
    UILayout,
)

bl_info = {
    "name": "Built-in Legacy Add-ons and Extensions",
    "author": "Draise (@trinumedia)",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "Preferences > Extensions",
    "description": "Ships the Legacy Add-ons and Pre-downloaded Extensions, to install without internet access",
    "warning": "Bforartists Exclusive",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "support": "OFFICIAL",
    "category": "Bforartists",
}


class DEFAULTADDON_APT_preferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context: Context):
        layout: UILayout = self.layout

        # BFA - the same buttons as in the Extensions preferences (#4568).
        from bl_pkg.bl_extension_ui import bfa_bundle_operators_draw
        bfa_bundle_operators_draw(context, layout.row())

        col = layout.column()
        col.label(text="Legacy Add-ons work offline, with the previous versions of the add-ons.", icon='INFO')
        col.label(text="Pre-downloaded Extensions replace them and can be updated when online.", icon='BLANK1')
        col.label(text="Disable a Legacy Add-on before you enable its Extension, and the other way around.", icon='ERROR')


classes = (
    DEFAULTADDON_APT_preferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
