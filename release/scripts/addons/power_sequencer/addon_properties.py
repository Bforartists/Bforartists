# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors

# This file is part of Power Sequencer.

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
