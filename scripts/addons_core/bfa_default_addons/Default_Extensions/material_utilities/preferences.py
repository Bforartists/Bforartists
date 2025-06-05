# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from bpy.types import (
    AddonPreferences,
    PropertyGroup,
    )
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
    )
from math import radians

from .enum_values import *

# Addon Preferences
class VIEW3D_MT_materialutilities_preferences(AddonPreferences):
    bl_idname = __package__

    new_material_name: StringProperty(
            name = "New Material name",
            description = "What Base name pattern to use for a new created Material\n"
                          "It is appended by an automatic numeric pattern depending\n"
                          "on the number of Scene's materials containing the Base",
            default = "Unnamed Material",
            )
    override_type: EnumProperty(
            name = 'Assignment method',
            description = '',
            items = mu_override_type_enums
            )
    fake_user: EnumProperty(
            name = "Set Fake User",
            description = "Default option for the Set Fake User (Turn fake user on or off)",
            items = mu_fake_user_set_enums,
            default = 'TOGGLE'
            )
    fake_user_affect: EnumProperty(
            name = "Affect",
            description = "Which materials of objects to affect",
            items = mu_fake_user_affect_enums,
            default = 'UNUSED'
            )
    link_to: EnumProperty(
            name = "Change Material Link To",
            description = "Default option for the Change Material Link operator",
            items = mu_link_to_enums,
            default = 'OBJECT'
            )
    link_to_affect: EnumProperty(
            name = "Affect",
            description = "Which materials of objects to affect by default with Change Material Link",
            items = mu_link_affect_enums,
            default = 'SELECTED'
            )
    search_show_limit: IntProperty(
            name = "Show 'Search' Limit",
            description = "How many materials should there be before the 'Search' option is shown "
                          "in the Assign Material and Select By Material menus\n"
                          "Set it to 0 to always show 'Search'",
            min = 0,
            default = 0
            )


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        box = layout.box()
        box.label(text = "Defaults")

        a = box.box()
        a.label(text = "Assign Material")
        a.prop(self, "new_material_name", icon = "MATERIAL")
        a.prop(self, "override_type", expand = False)

        b = box.box()
        b.label(text = "Set Fake User")
        b.row().prop(self, "fake_user", expand = False)
        b.row().prop(self, "fake_user_affect", expand = False)

        c = box.box()
        c.label(text = "Set Link To")
        c.row().prop(self, "link_to", expand = False)
        c.row().prop(self, "link_to_affect", expand = False)

        box = layout.box()
        box.label(text = "Miscellaneous")

        #col = box.column()
        #row = col.split(factor = 0.5)
        box.prop(self, "search_show_limit", expand = False)


def materialutilities_get_preferences(context):
    return context.preferences.addons[__package__].preferences
