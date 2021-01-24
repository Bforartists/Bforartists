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
import operator

from .utils.global_settings import SequenceTypes
from .utils.functions import convert_duration_to_frames
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_make_hold_frame(bpy.types.Operator):
    """
    *brief* Make a hold frame from the active strip

    Converts the image under the cursor to a hold frame, to create a pause effect in the video,
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
        return context.scene.sequence_editor.active_strip.type in SequenceTypes.VIDEO

    def invoke(self, context, event):
        window_manager = context.window_manager
        return window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene
        active = scene.sequence_editor.active_strip
        sequencer = bpy.ops.sequencer
        transform = bpy.ops.transform

        frame_start = scene.frame_current

        if not active.frame_final_start <= frame_start < active.frame_final_end:
            return {"FINISHED"}

        if frame_start == active.frame_final_start:
            scene.frame_current = frame_start + 1

        # Detect the gap automatically
        offset = convert_duration_to_frames(context, self.strip_duration)
        if self.strip_duration <= 0.0:
            try:
                next_strip_start = next(
                    s
                    for s in sorted(context.sequences, key=operator.attrgetter("frame_final_start"))
                    if s.frame_final_start > active.frame_final_end
                ).frame_final_start
                offset = next_strip_start - active.frame_final_end
            except Exception:
                pass

        active.select = True
        source_blend_type = active.blend_type
        sequencer.split(frame=scene.frame_current, type="SOFT", side="RIGHT")
        transform.seq_slide(value=(offset, 0))
        sequencer.split(frame=scene.frame_current + offset + 1, type="SOFT", side="LEFT")
        transform.seq_slide(value=(-offset, 0))

        sequencer.meta_make()
        active = scene.sequence_editor.active_strip
        active.name = "Hold frame"
        active.blend_type = source_blend_type
        active.select_right_handle = True
        transform.seq_slide(value=(offset, 0))

        scene.frame_current = frame_start

        active.select = True
        active.select_right_handle = False
        active.select_left_handle = False
        return {"FINISHED"}
