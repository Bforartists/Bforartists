# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors

# This file is part of Power Sequencer.

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_playback_speed_increase(bpy.types.Operator):
    """
    *brief* Increase playback speed up to triple


    Playback speed may be set to any of the following speeds:

    * Normal (1x)
    * Fast (1.33x)
    * Faster (1.66x)
    * Double (2x)
    * Triple (3x)

    Activating this operator will increase playback speed through each
    of these steps until maximum speed is reached.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "PERIOD", "value": "PRESS"}, {}, "Increase playback speed")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        scene = context.scene

        speeds = ["NORMAL", "FAST", "FASTER", "DOUBLE", "TRIPLE"]
        playback_speed = scene.power_sequencer.playback_speed

        index = min(speeds.index(playback_speed) + 1, len(speeds) - 1)
        scene.power_sequencer.playback_speed = speeds[index]

        return {"FINISHED"}
