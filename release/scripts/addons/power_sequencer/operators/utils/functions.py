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
from math import floor, sqrt
from operator import attrgetter

import bpy

from .global_settings import SequenceTypes


def calculate_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def convert_duration_to_frames(context, duration):
    return round(duration * context.scene.render.fps / context.scene.render.fps_base)


def find_linked(context, sequences, selected_sequences):
    """
    Takes a list of sequences and returns a list of all the sequences
    and effects that are linked in time

    Args:
    - sequences: a list of sequences

    Returns a list of all the linked sequences, but not the sequences passed to the function
    """
    start, end = get_frame_range(context, sequences, selected_sequences)
    sequences_in_range = [s for s in sequences if is_in_range(context, s, start, end)]
    effects = (s for s in sequences_in_range if s.type in SequenceTypes.EFFECT)
    selected_effects = (s for s in sequences if s.type in SequenceTypes.EFFECT)

    linked_sequences = []

    # Filter down to effects that have at least one of seq as input and
    # Append input sequences that aren't in the source list to linked_sequences
    for e in effects:
        if not hasattr(e, "input_2"):
            continue
        for s in sequences:
            if e.input_2 == s:
                linked_sequences.append(e)
                if e.input_1 not in sequences:
                    linked_sequences.append(e.input_1)
            elif e.input_1 == s:
                linked_sequences.append(e)
                if e.input_2 not in sequences:
                    linked_sequences.append(e.input_2)

    # Find inputs of selected effects that are not selected
    for e in selected_effects:
        try:
            if e.input_1 not in sequences:
                linked_sequences.append(e.input_1)
            if e.input_count == 2:
                if e.input_2 not in sequences:
                    linked_sequences.append(e.input_2)
        except AttributeError:
            continue

    return linked_sequences


def find_neighboring_markers(context, frame=None):
    """Returns a tuple containing the closest marker to the left and to the right of the frame"""
    markers = context.scene.timeline_markers

    if not (frame and markers):
        return None, None

    markers = sorted(markers, key=attrgetter("frame"))

    previous_marker, next_marker = None, None
    for m in markers:
        previous_marker = m if m.frame < frame else previous_marker
        if m.frame > frame:
            next_marker = m
            break

    return previous_marker, next_marker


def find_sequences_after(context, sequence):
    """
    Finds the strips following the sequences passed to the function
    Args:
    - Sequences, the sequences to check
    Returns all the strips after the sequence in the current context
    """
    return [s for s in context.sequences if s.frame_final_start > sequence.frame_final_start]


def find_snap_candidate(context, frame=0):
    """
    Returns the cut frame closest to the `frame` argument
    """
    snap_candidate = 1000000

    for s in context.sequences:
        start_to_frame = frame - s.frame_final_start
        end_to_frame = frame - s.frame_final_end

        distance_to_start = abs(start_to_frame)
        distance_to_end = abs(end_to_frame)

        candidate = (
            frame - start_to_frame
            if min(distance_to_start, distance_to_end) == distance_to_start
            else frame - end_to_frame
        )

        if abs(frame - candidate) < abs(frame - snap_candidate):
            snap_candidate = candidate

    return snap_candidate


def find_strips_mouse(context, frame, channel, select_linked=False):
    """
    Finds a list of sequences to select based on the frame and channel the mouse cursor is at

    Args:
    - frame: the frame the mouse or cursor is on
    - channel: the channel the mouse is hovering
    - select_linked: find and append the sequences linked in time if True

    Returns the sequence(s) under the mouse cursor as a list
    Returns an empty list if nothing found
    """
    sequences = [
        s
        for s in context.sequences
        if not s.lock and s.channel == channel and s.frame_final_start <= frame <= s.frame_final_end
    ]
    if select_linked:
        linked_strips = [
            s
            for s in context.sequences
            if s.frame_final_start == sequences[0].frame_final_start
            and s.frame_final_end == sequences[0].frame_final_end
        ]
        sequences.extend(linked_strips)
    return sequences


def get_frame_range(context, sequences=[], get_from_start=False):
    """
    Returns a tuple with the minimum and maximum frames of the
    list of passed sequences.
    Args:
        - sequences, the sequences to use
        - get_from_start, the returned start frame is set to 1 if
        this boolean is True
    """
    start, end = -1, -1
    start = (
        1
        if get_from_start
        else min(sequences, key=attrgetter("frame_final_start")).frame_final_start
    )
    end = max(sequences, key=attrgetter("frame_final_end")).frame_final_end
    return start, end


def get_mouse_frame_and_channel(context, event):
    """
    Convert mouse coordinates from the event, from
    pixels to frame, channel.
    Returns a tuple of frame, channel as integers
    """
    view2d = context.region.view2d
    frame, channel = view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
    return round(frame), floor(channel)


def is_in_range(context, sequence, start, end):
    """
    Checks if a single sequence's start or end is in the range

    Args:
    - sequence: the sequence to check for
    - start, end: the start and end frames
    Returns True if the sequence is within the range, False otherwise
    """
    s_start = sequence.frame_final_start
    s_end = sequence.frame_final_end
    return start <= s_start <= end or start <= s_end <= end


def set_preview_range(context, start, end):
    """Sets the preview range and timeline render range"""
    if not (start and end) and start != 0:
        raise AttributeError("Missing start or end parameter")

    scene = context.scene

    scene.frame_start = start
    scene.frame_end = end
    scene.frame_preview_start = start
    scene.frame_preview_end = end


def slice_selection(context, sequences):
    """
    Takes a list of sequences and breaks it down
    into multiple lists of connected sequences

    Returns a list of lists of sequences,
    each list corresponding to a block of sequences
    that are connected in time and sorted by frame_final_start
    """
    # Find when 2 sequences are not connected in time
    if not sequences:
        return []

    break_ids = [0]
    sorted_sequences = sorted(sequences, key=attrgetter("frame_final_start"))
    last_sequence = sorted_sequences[0]
    last_biggest_frame_end = last_sequence.frame_final_end
    index = 0
    for s in sorted_sequences:
        if s.frame_final_start > last_biggest_frame_end + 1:
            break_ids.append(index)
        last_biggest_frame_end = max(last_biggest_frame_end, s.frame_final_end)
        last_sequence = s
        index += 1

    # Create lists
    break_ids.append(len(sorted_sequences))
    cuts_count = len(break_ids) - 1
    broken_selection = []
    index = 0
    while index < cuts_count:
        temp_list = []
        index_range = range(break_ids[index], break_ids[index + 1] - 1)
        if len(index_range) == 0:
            temp_list.append(sorted_sequences[break_ids[index]])
        else:
            for counter in range(break_ids[index], break_ids[index + 1]):
                temp_list.append(sorted_sequences[counter])
        if temp_list:
            broken_selection.append(temp_list)
        index += 1
    return broken_selection


def trim_strips(context, start_frame, end_frame, to_trim=[], to_delete=[]):
    """
    Remove the footage and audio between start_frame and end_frame.
    """
    trim_start = min(start_frame, end_frame)
    trim_end = max(start_frame, end_frame)

    to_trim = [s for s in to_trim if s.type in SequenceTypes.CUTABLE]

    for s in to_trim:
        # Cut strip longer than the trim range in three
        is_strip_longer_than_trim_range = (
            s.frame_final_start < trim_start and s.frame_final_end > trim_end
        )
        if is_strip_longer_than_trim_range:
            bpy.ops.sequencer.select_all(action="DESELECT")
            s.select = True
            bpy.ops.sequencer.cut(frame=trim_start, type="SOFT", side="RIGHT")
            bpy.ops.sequencer.cut(frame=trim_end, type="SOFT", side="LEFT")
            to_delete.append(context.selected_sequences[0])
            continue

        # Resize strips that overlap the trim range
        elif s.frame_final_start < trim_end and s.frame_final_end > trim_end:
            s.frame_final_start = trim_end
        elif s.frame_final_end > trim_start and s.frame_final_start < trim_start:
            s.frame_final_end = trim_start

    delete_strips(to_delete)
    return {"FINISHED"}


def delete_strips(to_delete=[]):
    """
    Remove the footage and audio between start_frame and end_frame.
    """
    if to_delete == []:
        return
    bpy.ops.sequencer.select_all(action="DESELECT")
    for s in to_delete:
        s.select = True
    bpy.ops.sequencer.delete()


def find_closest_surrounding_cuts(context, frame):
    """
    Returns a tuple of (strip_before, strip_after), the two closest sequences around a gap.
    If the frame is in the middle of a strip, both strips may be the same.
    """
    strip_before = max(
        context.sequences,
        key=lambda s: s.frame_final_end
        if s.frame_final_end <= frame
        else s.frame_final_start
        if s.frame_final_start <= frame
        else 0,
    )
    strip_after = min(
        context.sequences,
        key=lambda s: s.frame_final_start
        if s.frame_final_start >= frame
        else s.frame_final_end
        if s.frame_final_end >= frame
        else 1000000,
    )
    return strip_before, strip_after


def find_closest_surrounding_cuts_frames(context, frame):
    before, after = find_closest_surrounding_cuts(context, frame)
    if before == after:
        frame_left, frame_right = before.frame_final_start, before.frame_final_end
    else:
        frame_left, frame_right = before.frame_final_end, after.frame_final_start
    return frame_left, frame_right


def get_sequences_under_cursor(context):
    frame = context.scene.frame_current
    under_cursor = [
        s
        for s in context.sequences
        if s.frame_final_start <= frame and s.frame_final_end >= frame and not s.lock
    ]
    return under_cursor


def ripple_move(context, sequences, duration_frames, delete=False):
    """Moves sequences in the list and ripples the change to all sequences after them, in the corresponding channels
    The `duration_frames` can be positive or negative.
    If `delete` is True, deletes every sequence in `sequences`.
    """
    channels = {s.channel for s in sequences}
    first_strip = min(sequences, key=lambda s: s.frame_final_start)
    to_ripple = [
        s
        for s in context.sequences
        if s.channel in channels and s.frame_final_start >= first_strip.frame_final_start
    ]

    if delete:
        bpy.ops.sequencer.select_all(action="DESELECT")
        for s in sequences:
            s.select = True
        bpy.ops.sequencer.delete()
    else:
        to_ripple = set(to_ripple + sequences)

    # Use the built-in seq_slide operator to move strips, for best performances
    initial_selection = context.selected_sequences
    bpy.ops.sequencer.select_all(action="DESELECT")
    for s in to_ripple:
        s.select = True
    bpy.ops.transform.seq_slide(value=(duration_frames, 0))
    bpy.ops.sequencer.select_all(action="DESELECT")
    for s in initial_selection:
        s.select = True


def apply_time_offset(context, sequences=[], offset=0):
    """Offsets a list of sequences in time using bpy.ops.transform.seq_slide. Mutates and restores the
    user's selection. Use this function to ensure maximum performances and avoid having to figure
    out the logic to move strips in the right order.
    """
    selection = context.selected_sequences
    bpy.ops.sequencer.select_all(action="DESELECT")
    for s in sequences:
        s.select = True
    bpy.ops.transform.seq_slide(value=(offset, 0))
    bpy.ops.sequencer.select_all(action="DESELECT")
    for s in selection:
        s.select = True
