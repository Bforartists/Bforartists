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
from operator import attrgetter

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_jump_to_cut(bpy.types.Operator):
    """
    *brief* Jump to next/previous cut


    Jump to the next or the previous cut in the edit.  Unlike Blender's default tool, also
    works during playback.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "UP_ARROW", "value": "PRESS"},
                {"direction": "RIGHT"},
                "Jump to next cut or keyframe",
            ),
            (
                {"type": "DOWN_ARROW", "value": "PRESS"},
                {"direction": "LEFT"},
                "Jump to previous cut or keyframe",
            ),
        ],
        "keymap": "Frames",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        name="Direction",
        description="Jump direction, either forward or backward",
        items=[
            ("RIGHT", "Forward", "Jump forward in time"),
            ("LEFT", "Backward", "Jump backward in time"),
        ],
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        frame_current = context.scene.frame_current
        sorted_sequences = sorted(
            context.sequences, key=attrgetter("frame_final_start", "frame_final_end")
        )

        fcurves = []
        animation_data = context.scene.animation_data
        if animation_data and animation_data.action:
            fcurves = animation_data.action.fcurves

        frame_target = -1
        if self.direction == "RIGHT":
            sequences = [s for s in sorted_sequences if s.frame_final_end > frame_current]
            for s in sequences:

                frame_target = (
                    s.frame_final_end
                    if s.frame_final_start <= frame_current
                    else s.frame_final_start
                )

                for f in fcurves:
                    for k in f.keyframe_points:
                        frame = k.co[0]
                        if frame <= context.scene.frame_current:
                            continue
                        frame_target = min(frame_target, frame)
                break

        elif self.direction == "LEFT":
            sequences = [
                s for s in reversed(sorted_sequences) if s.frame_final_start < frame_current
            ]
            for s in sequences:

                frame_target = (
                    s.frame_final_start if s.frame_final_end >= frame_current else s.frame_final_end
                )

                for f in fcurves:
                    for k in f.keyframe_points:
                        frame = k.co[0]
                        if frame >= context.scene.frame_current:
                            continue
                        frame_target = max(frame_target, frame)
                break

        if frame_target != -1:
            context.scene.frame_current = max(1, frame_target)

        return {"FINISHED"}
