# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from operator import attrgetter

from .utils.global_settings import SequenceTypes
from .utils.functions import (
    find_sequences_after,
    get_mouse_frame_and_channel,
    ripple_move,
)
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


def find_sequences_before(context, strip):
    """
    Returns a list of sequences that are before the strip in the current context
    """
    return [s for s in context.sequences if s.frame_final_end <= strip.frame_final_start]


class POWER_SEQUENCER_OT_concatenate_strips(bpy.types.Operator):
    """
    *brief* Remove space between strips

    Concatenates selected strips in a channel, i.e. removes the gap between them. If a single
    strip is selected, either the next strip in the channel will be concatenated, or all
    strips in the channel will be concatenated depending on which shortcut is used.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/YyEL8YP.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "C", "value": "PRESS"},
                {"concatenate_all": False, "is_towards_left": True},
                ("Concatenate and select the next strip in the channel"),
            ),
            (
                {"type": "C", "value": "PRESS", "shift": True},
                {"concatenate_all": True, "is_towards_left": True},
                "Concatenate all strips in selected channels",
            ),
            (
                {"type": "C", "value": "PRESS", "alt": True},
                {"concatenate_all": False, "is_towards_left": False},
                ("Concatenate and select the previous strip in the channel towards the right"),
            ),
            (
                {"type": "C", "value": "PRESS", "shift": True, "alt": True},
                {"concatenate_all": True, "is_towards_left": False},
                "Shift Alt C; Concatenate all strips in channel towards the right",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    concatenate_all: bpy.props.BoolProperty(
        name="Concatenate all strips in channel",
        description=("If only one strip selected, concatenate" " the entire channel"),
        default=False,
    )
    is_towards_left: bpy.props.BoolProperty(
        name="To Left",
        description="Concatenate strips moving them back in time (default) or forward in time",
        default=True,
    )
    do_ripple: bpy.props.BoolProperty(
        name="Ripple Edit",
        description="Ripple the time offset to strips after the concatenated one",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        if not context.selected_sequences:
            frame, channel = get_mouse_frame_and_channel(context, event)
            bpy.ops.power_sequencer.select_closest_to_mouse(frame=frame, channel=channel)
        return self.execute(context)

    def execute(self, context):
        selection = context.selected_sequences
        channels = {s.channel for s in selection}

        is_one_strip_per_channel = len(selection) == len(channels)
        if is_one_strip_per_channel:
            for s in selection:
                candidates = (
                    find_sequences_before(context, s)
                    if not self.is_towards_left
                    else find_sequences_after(context, s)
                )
                to_concatenate = [
                    strip
                    for strip in candidates
                    if strip.channel == s.channel
                    and not strip.lock
                    and strip.type in SequenceTypes.CUTABLE
                ]
                if not to_concatenate:
                    continue
                self.concatenate(context, s, to_concatenate)

        else:
            for channel in channels:
                to_concatenate = [s for s in selection if s.channel == channel]
                strip_target = (
                    min(to_concatenate, key=lambda s: s.frame_final_start)
                    if self.is_towards_left
                    else max(to_concatenate, key=lambda s: s.frame_final_start)
                )
                to_concatenate.remove(strip_target)
                self.concatenate(context, strip_target, to_concatenate, force_all=True)

        return {"FINISHED"}

    def concatenate(self, context, strip_target, sequences, force_all=False):
        to_concatenate = sorted(sequences, key=attrgetter("frame_final_start"))
        to_concatenate = (
            list(reversed(to_concatenate)) if not self.is_towards_left else to_concatenate
        )
        to_concatenate = (
            [to_concatenate[0]] if not (self.concatenate_all or force_all) else to_concatenate
        )

        attribute_target = "frame_final_end" if self.is_towards_left else "frame_final_start"
        attribute_concat = "frame_final_start" if self.is_towards_left else "frame_final_end"
        concatenate_start = getattr(strip_target, attribute_target)
        last_gap = 0
        for s in to_concatenate:
            if isinstance(s, bpy.types.EffectSequence):
                concatenate_start = (
                    s.frame_final_end - last_gap
                    if self.is_towards_left
                    else s.frame_final_start - last_gap
                )
                continue
            concat_strip_frame = getattr(s, attribute_concat)
            gap = concat_strip_frame - concatenate_start
            if self.do_ripple and self.is_towards_left:
                ripple_move(context, [s], -gap)
            else:
                s.frame_start -= gap
            concatenate_start = s.frame_final_end if self.is_towards_left else s.frame_final_start
            last_gap = gap

        if not (self.concatenate_all or force_all):
            strip_target.select = False
            to_concatenate[0].select = True
