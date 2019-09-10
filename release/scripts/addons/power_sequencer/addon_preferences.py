#
# Copyright (C) 2016-2019 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
"""
Add-on preferences and interface in the Blender preferences window.
"""
import bpy


def get_preferences(context):
    return context.preferences.addons[__package__].preferences

class PowerSequencerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    proxy_25: bpy.props.BoolProperty(name="25%", default=False)
    proxy_50: bpy.props.BoolProperty(name="50%", default=False)
    proxy_75: bpy.props.BoolProperty(name="75%", default=False)
    proxy_100: bpy.props.BoolProperty(name="100%", default=False)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Proxy")

        row = layout.row()
        row.prop(self, "proxy_25")
        row.prop(self, "proxy_50")
        row.prop(self, "proxy_75")
        row.prop(self, "proxy_100")


register_preferences, unregister_preferences = bpy.utils.register_classes_factory(
    [PowerSequencerPreferences]
)
