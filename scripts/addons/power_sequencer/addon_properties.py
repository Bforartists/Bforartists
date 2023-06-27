# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


class PowerSequencerProperties(bpy.types.PropertyGroup):
    playback_speed: bpy.props.EnumProperty(
        items=[
            ("NORMAL", "Normal (1x)", ""),
            ("DOUBLE", "Double (2x)", ""),
            ("TRIPLE", "Triple (3x)", ""),
        ],
        name="Playback",
        default="NORMAL",
    )

    active_tab: bpy.props.StringProperty(
        name="Active Tab", description="The name of the active tab in the UI", default="Sequencer"
    )


def register_properties():
    bpy.utils.register_class(PowerSequencerProperties)
    bpy.types.Scene.power_sequencer = bpy.props.PointerProperty(type=PowerSequencerProperties)


def unregister_properties():
    bpy.utils.unregister_class(PowerSequencerProperties)
