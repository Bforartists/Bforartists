#!/usr/bin/env python3

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os
import sys

PWD = os.path.dirname(__file__)
sys.path.append(os.path.join(PWD, "modules"))

from batch_edit_text import run

SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(os.path.join(PWD, "..", "..", ".."))))

# TODO, move to config file
SOURCE_DIRS = (
    "source",
    "intern/ghost",
)

SOURCE_EXT = (
    # C/C++
    ".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx", ".inl",
    # Objective C
    ".m", ".mm",
)


def sort_struct_lists(fn, data_src):
    import re

    # eg:
    #    extern StructRNA;
    re_match_struct = re.compile(r"struct\s+[A-Za-z_][A-Za-z_0-9]*\s*;")
    # eg:
    #    extern StructRNA RNA_LightProbe;
    re_match_struct_type = re.compile(r"struct\s+[A-Za-z_][A-Za-z_0-9]*\s+[A-Za-z_][A-Za-z_0-9]*\s*;")

    #    typedef struct BMBVHTree BMBVHTree;
    re_match_typedef_struct_type = re.compile(r"typedef\s+struct\s+[A-Za-z_][A-Za-z_0-9]*\s+[A-Za-z_][A-Za-z_0-9]*\s*;")

    re_match_enum = re.compile(r"enum\s+[A-Za-z_][A-Za-z_0-9]*\s*;")

    # eg:
    #    extern char datatoc_splash_png[];
    re_match_datatoc = re.compile(r"extern\s+(char)\s+datatoc_[A-Za-z_].*;")

    lines = data_src.splitlines(keepends=True)

    def can_sort(l):
        if re_match_struct.match(l):
            return 1
        if re_match_struct_type.match(l):
            return 2
        if re_match_typedef_struct_type.match(l):
            return 3
        if re_match_enum.match(l):
            return 4
        # Disable for now.
        # if re_match_datatoc.match(l):
        #     return 5
        return None

    i = 0
    while i < len(lines):
        i_type = can_sort(lines[i])
        if i_type is not None:
            j = i
            while j + 1 < len(lines):
                if can_sort(lines[j + 1]) != i_type:
                    break
                j = j + 1
            if i != j:
                lines[i:j + 1] = list(sorted(lines[i:j + 1]))
            i = j
        i = i + 1

    data_dst = "".join(lines)
    if data_src != data_dst:
        return data_dst


run(
    directories=[os.path.join(SOURCE_DIR, d) for d in SOURCE_DIRS],
    is_text=lambda fn: fn.endswith(SOURCE_EXT),
    text_operation=sort_struct_lists,
    use_multiprocess=True,
)
