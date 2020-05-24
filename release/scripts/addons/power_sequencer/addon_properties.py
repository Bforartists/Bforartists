#
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
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
import bpy


class PowerSequencerProperties(bpy.types.PropertyGroup):
    playback_speed: bpy.props.EnumProperty(
        items=[
            ("NORMAL", "Normal (1x)", ""),
            ("FAST", "Fast (1.33x)", ""),
            ("FASTER", "Faster (1.66x)", ""),
            ("DOUBLE", "Double (2x)", ""),
            ("TRIPLE", "Triple (3x)", ""),
        ],
        name="Playback",
        default="NORMAL",
    )

    frame_pre: bpy.props.IntProperty(name="Frame before frame_change", default=0, min=0)

    active_tab: bpy.props.StringProperty(
        name="Active Tab", description="The name of the active tab in the UI", default="Sequencer"
    )


def register_properties():
    bpy.utils.register_class(PowerSequencerProperties)
    bpy.types.Scene.power_sequencer = bpy.props.PointerProperty(type=PowerSequencerProperties)


def unregister_properties():
    bpy.utils.unregister_class(PowerSequencerProperties)
