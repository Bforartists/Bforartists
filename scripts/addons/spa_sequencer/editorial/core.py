# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import re
from typing import NamedTuple

import bpy


class StripsGroup(NamedTuple):
    group_id: str
    strips: list[bpy.types.Sequence]

    @property
    def frame_start(self):
        """First frame of that group."""
        return self.strips[0].frame_final_start if self.strips else 0

    @property
    def frame_end(self):
        """Last frame of that group."""
        return self.strips[-1].frame_final_end if self.strips else 0

    @property
    def frame_duration(self):
        """Total duration of that group."""
        return self.frame_end - self.frame_start


def gather_strips_groups_by_regex(
    strips: list[bpy.types.Sequence], regex_group_id: str
) -> list[StripsGroup]:
    """
    Build groups of consecutive strips with similar group id - defined by
    `regex_group_id` - in their name.

    :param strips: The sorted list of strips.
    :param regex_group_id: The regex defining how to extract group id from strip name.
        Must be a single capture group expression.
    """
    regex = re.compile(regex_group_id)

    # List to gather consecutive strips by identical group id.
    strips_groups: list[StripsGroup] = []

    for strip in strips:
        group_id = ""
        # Extract group identifier from name.
        res = regex.match(strip.name)
        if res:
            group_id = res.group(1)

        # Append strip to previous group if it matches
        if strips_groups:
            prev_group = strips_groups[-1]
            if prev_group.group_id == group_id:
                prev_group.strips.append(strip)
                continue

        # Otherwise, create a new group from this strip
        group = StripsGroup(group_id, [strip])
        strips_groups.append(group)

    return strips_groups
