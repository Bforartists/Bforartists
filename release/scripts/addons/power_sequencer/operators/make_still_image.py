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
import bpy
import operator

from .utils.global_settings import SequenceTypes
from .utils.functions import convert_duration_to_frames
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_make_still_image(bpy.types.Operator):
    """
    *brief* Make still image from active strip


    Converts image under the cursor to a still image, to create a pause effect in the video,
    using the active sequence
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    strip_duration: bpy.props.FloatProperty(
        name="Strip Duration",
        description="The duration in seconds of the new strip, if 0.0 it will use the gap as its duration",
        default=0.0,
        min=0.0,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def invoke(self, context, event):
        window_manager = context.window_manager
        return window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene
        active = scene.sequence_editor.active_strip
        sequencer = bpy.ops.sequencer
        transform = bpy.ops.transform

        start_frame = scene.frame_current
        offset = convert_duration_to_frames(context, self.strip_duration)

        if active.type not in SequenceTypes.VIDEO:
            self.report(
                {"ERROR_INVALID_INPUT"},
                "You must select a video or meta strip. \
                You selected a strip of type"
                + str(active.type)
                + " instead.",
            )
            return {"CANCELLED"}

        if not active.frame_final_start <= start_frame < active.frame_final_end:
            self.report(
                {"ERROR_INVALID_INPUT"},
                "Your time cursor must be on the frame you want \
                        to convert to a still image.",
            )
            return {"CANCELLED"}

        if start_frame == active.frame_final_start:
            scene.frame_current = start_frame + 1

        if self.strip_duration <= 0.0:
            strips = sorted(
                scene.sequence_editor.sequences, key=operator.attrgetter("frame_final_start")
            )

            for s in strips:
                if s.frame_final_start > active.frame_final_start and s.channel == active.channel:
                    next = s
                    break
            offset = next.frame_final_start - active.frame_final_end

        active.select = True
        source_blend_type = active.blend_type
        sequencer.cut(frame=scene.frame_current, type="SOFT", side="RIGHT")
        transform.seq_slide(value=(offset, 0))
        sequencer.cut(frame=scene.frame_current + offset + 1, type="SOFT", side="LEFT")
        transform.seq_slide(value=(-offset, 0))

        sequencer.meta_make()
        active = scene.sequence_editor.active_strip
        active.name = "Still image"
        active.blend_type = source_blend_type
        active.select_right_handle = True
        transform.seq_slide(value=(offset, 0))

        scene.frame_current = start_frame

        active.select = True
        active.select_right_handle = False
        active.select_left_handle = False
        return {"FINISHED"}
