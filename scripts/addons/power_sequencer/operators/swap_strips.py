# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from operator import attrgetter

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_swap_strips(bpy.types.Operator):
    """
    *brief* Swaps the 2 strips between them


    Places the first strip in the channel and starting frame (frame_final_start) of the second
    strip, and places the second strip in the channel and starting frame (frame_final_end) of
    the first strip.  If there is no space for the swap, it does nothing.
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

    direction: bpy.props.EnumProperty(
        name="Direction",
        description="The direction to find the closest strip",
        items=[
            ("up", "Up", "The direction up from the selected strip"),
            ("down", "Down", "The direction down from the selected strip"),
        ],
        default="up",
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        if len(context.selected_sequences) != 2:
            return {"CANCELLED"}

        strip_1 = context.selected_sequences[0]
        if len(context.selected_sequences) == 1:
            strip_2 = self.find_closest_strip_vertical(context, strip_1, self.direction)
        else:
            strip_2 = context.selected_sequences[1]
        if not strip_2 or strip_1.lock or strip_2.lock:
            return {"CANCELLED"}

        # Swap a strip and one of its effects
        if hasattr(strip_1, "input_1") or hasattr(strip_2, "input_1"):
            if not self.are_linked(strip_1, strip_2):
                return {"CANCELLED"}
            self.swap_with_effect(strip_1, strip_2)
            return {"FINISHED"}

        s1_start, s1_channel = strip_1.frame_final_start, strip_1.channel
        s2_start, s2_channel = strip_2.frame_final_start, strip_2.channel

        self.move_to_end(strip_1, context)
        self.move_to_end(strip_2, context)

        s1_start_2 = strip_1.frame_final_start
        s2_start_2 = strip_2.frame_final_start

        group_1 = {
            s: s.channel
            for s in context.sequences
            if s.frame_final_start == s1_start_2 and s != strip_1
        }
        group_2 = {
            s: s.channel
            for s in context.sequences
            if s.frame_final_start == s2_start_2 and s != strip_2
        }

        strip_2.select = False
        bpy.ops.transform.seq_slide(
            value=(s2_start - strip_1.frame_final_start, s2_channel - strip_1.channel)
        )

        bpy.ops.sequencer.select_all(action="DESELECT")
        strip_2.select = True
        bpy.ops.transform.seq_slide(
            value=(s1_start - strip_2.frame_final_start, s1_channel - strip_2.channel)
        )

        if not self.fits(
            strip_1, group_1, s2_start, s1_channel, s2_channel, context
        ) or not self.fits(strip_2, group_2, s1_start, s2_channel, s1_channel, context):
            self.reconstruct(strip_1, s1_channel, group_1, context)
            self.reconstruct(strip_2, s2_channel, group_2, context)

            bpy.ops.sequencer.select_all(action="DESELECT")
            strip_1.select = True
            bpy.ops.transform.seq_slide(
                value=(s1_start - strip_1.frame_final_start, s1_channel - strip_1.channel)
            )

            bpy.ops.sequencer.select_all(action="DESELECT")
            strip_2.select = True
            bpy.ops.transform.seq_slide(
                value=(s2_start - strip_2.frame_final_start, s2_channel - strip_2.channel)
            )

            bpy.ops.sequencer.select_all(action="DESELECT")
            strip_1.select = True
            strip_2.select = True
            return {"CANCELLED"}

        bpy.ops.sequencer.select_all(action="DESELECT")
        strip_1.select = True
        strip_2.select = True
        return {"FINISHED"}

    def move_to_frame(self, strip, frame, context):
        """
        Moves a strip based on its frame_final_start without changing its
        duration.
        Args:
        - strip: The strip to be moved.
        - frame: The frame, the frame_final_start of the strip will be placed
                 at.
        """
        selected_strips = context.selected_sequences
        bpy.ops.sequencer.select_all(action="DESELECT")
        strip.select = True

        bpy.ops.transform.seq_slide(value=(frame - strip.frame_final_start, 0))

        bpy.ops.sequencer.select_all(action="DESELECT")
        for s in selected_strips:
            s.select = True

    def move_to_end(self, strip, context):
        """
        Moves a strip to an empty slot at the end of the sequencer, different
        than its initial slot.
        Args:
        - strip: The strip to move.
        """
        end_frame = max(context.sequences, key=attrgetter("frame_final_end")).frame_final_end
        self.move_to_frame(strip, end_frame, context)

    def fits(self, strip, group, frame, init_channel, target_channel, context):
        """
        Checks if a swap has been successful or not.
        Args:
        - strip: The core strip of the swap.
        - group: The effect strips of the core strip.
        - frame: The starting frame of the target location.
        - init_channel: The initial channel of the strip, before the swap took
                        place.
        - target_channel: The channel of the target location.
        Returns: True if the swap was successful, otherwise False.
        """
        if strip.frame_final_start != frame or strip.channel != target_channel:
            return False

        offset = strip.channel - init_channel
        for s in group.keys():
            if s.channel != group[s] + offset:
                return False

        return context.selected_sequences

    def reconstruct(self, strip, init_channel, group, context):
        """
        Reconstructs a failed swap, based on a core strip. After its done, the
        core strip is placed at the end of the sequencer, in an empty slot.
        Args:
        - strip: The core strip of the swap.
        - init_channel: The initial channel of the core strip.
        - group: A dictionary with the effect strips of the core strip, and
                 their target channels.
        """
        self.move_to_end(strip, context)
        bpy.ops.sequencer.select_all(action="DESELECT")
        strip.select = True
        bpy.ops.transform.seq_slide(value=(0, init_channel - strip.channel))

        for s in group.keys():
            channel = group[s]
            for u in group.keys():
                if u.channel == channel and u != s:
                    u.channel += 1
            s.channel = channel

    def find_closest_strip_vertical(self, context, strip, direction):
        """
        Finds the closest strip to a given strip in a specific direction.
        Args:
        - strip: The base strip.
        Returns: The closest strip to the given strip, in the proper direction.
                 If no strip is found, returns None.
        """
        strips_in_range = (
            s
            for s in context.sequences
            if strip.frame_final_start <= s.frame_final_start
            and s.frame_final_end <= strip.frame_final_end
        )
        if direction == "up":
            strips_above = [s for s in strips_in_range if s.channel > strip.channel]
            if not strips_above:
                return
            return min(strips_above, key=attrgetter("channel"))
        elif direction == "down":
            strips_below = [s for s in strips_in_range if s.channel < strip.channel]
            if not strips_below:
                return
            return max(strips_below, key=attrgetter("channel"))

    def are_linked(self, strip_1, strip_2):
        return (
            strip_1.frame_final_start == strip_2.frame_final_start
            and strip_1.frame_final_end == strip_2.frame_final_end
        )

    def swap_with_effect(self, strip_1, strip_2):
        effect_strip = strip_1 if hasattr(strip_1, "input_1") else strip_2
        other_strip = strip_1 if effect_strip != strip_1 else strip_2

        effect_strip_channel = effect_strip.channel
        other_strip_channel = other_strip.channel

        effect_strip.channel -= 1
        other_strip.channel = effect_strip_channel
        effect_strip.channel = other_strip_channel
