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
"""
Selects and grabs the strip handle or cut closest to the mouse cursor.
Hover near a cut and use this operator to slide it.
"""
import bpy

from math import floor

from .utils.functions import calculate_distance
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_grab_closest_cut(bpy.types.Operator):
    """
    *brief* Grab the handles that form the closest cut


    Selects and grabs the strip handle or cut closest to the mouse cursor.
    Hover near a cut and fire this tool to slide it.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "G", "value": "PRESS", "shift": True, "alt": True},
                {},
                "Grab closest handle or cut",
            )
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    select_linked: bpy.props.BoolProperty(
        name="Select Linked", description="Select strips that are linked in time", default=True
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        sequencer = bpy.ops.sequencer

        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        frame, channel = self.find_cut_closest_to_mouse(context, mouse_x, mouse_y)

        matching_strips = [
            s
            for s in context.sequences
            if (abs(s.frame_final_start - frame) <= 1 or abs(s.frame_final_end - frame) <= 1)
        ]
        if not self.select_linked:
            matching_strips = [s for s in matching_strips if s.channel == channel]
        sequencer.select_all(action="DESELECT")
        for s in matching_strips:
            s.select = True
        return bpy.ops.power_sequencer.grab_sequence_handles(frame=frame)

    def find_cut_closest_to_mouse(self, context, mouse_x, mouse_y):
        """
        Takes the mouse's coordinates in the sequencer area and returns the two
        strips who share the cut closest to the mouse. Use it to find the
        handle(s) to select with the grab on the fly operator
        """
        view2d = context.region.view2d

        closest_cut = (None, None)
        distance_to_closest_cut = 1000000.0

        for s in context.sequences:
            channel_offset = s.channel + 0.5
            start_x, start_y = view2d.view_to_region(s.frame_final_start, channel_offset)
            end_x, end_y = view2d.view_to_region(s.frame_final_start, channel_offset)

            distance_to_start = calculate_distance(start_x, start_y, mouse_x, mouse_y)
            distance_to_end = calculate_distance(end_x, end_y, mouse_x, mouse_y)

            if distance_to_start < distance_to_closest_cut:
                closest_cut = (start_x, start_y)
                distance_to_closest_cut = distance_to_start
            if distance_to_end < distance_to_closest_cut:
                closest_cut = (end_x, end_y)
                distance_to_closest_cut = distance_to_end

        closest_cut_local_coords = view2d.region_to_view(closest_cut[0], closest_cut[1])
        frame, channel = (round(closest_cut_local_coords[0]), floor(closest_cut_local_coords[1]))
        return frame, channel
