# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from operator import attrgetter

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_copy_selected_sequences(bpy.types.Operator):
    """
    *brief* Copy/cut strips without offset from current time indicator


    Copies the selected sequences without frame offset and optionally
    deletes the selection to give a cut to clipboard effect. This
    operator overrides the default Blender copy method which includes
    cursor offset when pasting, which is atypical of copy/paste methods.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/w6z1Jb1.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "C", "value": "PRESS", "ctrl": True},
                {"delete_selection": False},
                "Copy Selected Strips",
            ),
            (
                {"type": "X", "value": "PRESS", "ctrl": True},
                {"delete_selection": True},
                "Cut Selected Strips",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    delete_selection: bpy.props.BoolProperty(
        name="Delete selection",
        description="Delete selected strips: acts like cut and paste",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        cursor_start_frame = context.scene.frame_current
        sequencer = bpy.ops.sequencer

        # Deactivate audio playback and video preview
        scene = context.scene
        initial_audio_setting = scene.use_audio_scrub
        initial_proxy_size = context.space_data.proxy_render_size
        scene.use_audio_scrub = False
        context.space_data.proxy_render_size = "NONE"

        first_sequence = min(context.selected_sequences, key=attrgetter("frame_final_start"))
        context.scene.frame_current = first_sequence.frame_final_start
        sequencer.copy()
        context.scene.frame_current = cursor_start_frame

        scene.use_audio_scrub = initial_audio_setting
        context.space_data.proxy_render_size = initial_proxy_size

        if self.delete_selection:
            sequencer.delete()

        plural_string = "s" if len(context.selected_sequences) != 1 else ""
        action_verb = "Cut" if self.delete_selection else "Copied"
        report_message = "{!s} {!s} sequence{!s} to the clipboard.".format(
            action_verb, str(len(context.selected_sequences)), plural_string
        )
        self.report({"INFO"}, report_message)
        return {"FINISHED"}
