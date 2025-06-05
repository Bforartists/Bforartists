# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
            ("RIGHT", "Right", "Jump forward in time"),
            ("LEFT", "Left", "Jump backward in time"),
        ],
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        frame_current = context.scene.frame_current

        fcurves = []
        animation_data = context.scene.animation_data
        if animation_data and animation_data.action:
            fcurves = animation_data.action.fcurves

        frame_target = -1

        # First find the closest cut, then if that sequence has an associated
        # fcurve, loop through the curve's keyframes.
        if self.direction == "RIGHT":
            frame_target = 100_000_000
            for s in context.sequences:
                if s.frame_final_end <= frame_current:
                    continue

                candidates = [frame_target, s.frame_final_end]
                if s.frame_final_start > frame_current:
                    candidates.append(s.frame_final_start)

                frame_target = min(candidates)

                for f in fcurves:
                    if s.name not in f.data_path:
                        continue

                    for k in f.keyframe_points:
                        frame = k.co[0]
                        if frame <= frame_current:
                            continue
                        frame_target = min(frame_target, frame)

        elif self.direction == "LEFT":
            for s in context.sequences:
                if s.frame_final_start >= frame_current:
                    continue

                candidates = [frame_target, s.frame_final_start]
                if s.frame_final_end < frame_current:
                    candidates.append(s.frame_final_end)

                frame_target = max(candidates)

                for f in fcurves:
                    if s.name not in f.data_path:
                        continue

                    for k in f.keyframe_points:
                        frame = k.co[0]
                        if frame >= frame_current:
                            continue
                        frame_target = max(frame_target, frame)

        if frame_target > 0 and frame_target != 100_000_000:
            context.scene.frame_current = int(frame_target)

        return {"FINISHED"}
