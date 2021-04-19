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

"""
When a source file declares a struct which isn't used anywhere else in the file.
Remove it.

There may be times this is needed, however there can typically be removed.
"""

import os
import sys
import re

from typing import (
    Dict,
    Optional,
)

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

re_words = re.compile("[A-Za-z_][A-Za-z_0-9]*")
re_match_struct = re.compile(r"struct\s+([A-Za-z_][A-Za-z_0-9]*)\s*;")

def clean_structs(fn: str, data_src: str) -> Optional[str]:
    import re

    word_occurance: Dict[str, int] = {}
    for w_match in re_words.finditer(data_src):
        w = w_match.group(0)
        try:
            word_occurance[w] += 1
        except KeyError:
            word_occurance[w] = 1

    lines = data_src.splitlines(keepends=True)

    i = 0
    while i < len(lines):
        m = re_match_struct.match(lines[i])
        if m is not None:
            struct_name = m.group(1)
            if word_occurance[struct_name] == 1:
                print(struct_name, fn)
                del lines[i]
                i -= 1

        i += 1

    data_dst = "".join(lines)
    if data_src != data_dst:
        return data_dst
    return None

run(
    directories=[os.path.join(SOURCE_DIR, d) for d in SOURCE_DIRS],
    is_text=lambda fn: fn.endswith(SOURCE_EXT),
    text_operation=clean_structs,
    use_multiprocess=False,
)
