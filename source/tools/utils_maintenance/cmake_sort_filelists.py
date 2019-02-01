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
Sorts CMake path lists
- Don't cross blank newline boundaries.
- Don't cross different path prefix boundaries.
"""

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

def sort_cmake_file_lists(fn, data_src):
    lines = data_src.splitlines(keepends=True)

    def can_sort(l):
        l = l.split("#", 1)[0].strip()
        if l.endswith(SOURCE_EXT):
            if "(" not in l and ')' not in l:
                return True

    def can_sort_compat(a, b):
        a = a.split("/")
        b = b.split("/")
        if len(a) == 1 and len(b) == 1:
            return True
        return a[:-1] == b[:-1]

    i = 0
    while i < len(lines):
        if can_sort(lines[i]):
            j = i
            while j + 1 < len(lines):
                if not can_sort(lines[j + 1]):
                    break
                if not can_sort_compat(lines[i], lines[j + 1]):
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
    is_text=lambda fn: fn.endswith("CMakeLists.txt"),
    text_operation=sort_cmake_file_lists,
)
