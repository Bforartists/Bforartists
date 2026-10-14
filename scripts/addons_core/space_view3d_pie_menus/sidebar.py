# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .prefs import get_addon_prefs, draw_prefs

class VIEW3D_PT_extra_pies(bpy.types.Panel):
    bl_label = "Extra Pies"
    bl_idname = "VIEW3D_PT_extra_pies"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Extra Pies'

    @classmethod
    def poll(cls, context):
        # BFA - the panel can still poll while the add-on is being disabled, after its preferences are gone.
        try:
            prefs = get_addon_prefs(context)
        except KeyError:
            return False
        return prefs.show_in_sidebar

    def draw(self, context):
        layout = self.layout

        draw_prefs(layout, context, compact=True)

registry = [
    VIEW3D_PT_extra_pies,
]