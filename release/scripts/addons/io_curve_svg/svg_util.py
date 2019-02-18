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

# <pep8 compliant>

import re

def srgb_to_linearrgb(c):
    if c < 0.04045:
        return 0.0 if c < 0.0 else c * (1.0 / 12.92)
    else:
        return pow((c + 0.055) * (1.0 / 1.055), 2.4)


def check_points_equal(point_a, point_b):
    return (abs(point_a[0] - point_b[0]) < 1e-6 and
            abs(point_a[1] - point_b[1]) < 1e-6)

match_number = r"-?\d+(\.\d+)?([eE][-+]?\d+)?"
match_first_comma = r"^\s*(?=,)"
match_comma_pair = r",\s*(?=,)"
match_last_comma = r",\s*$"

pattern = f"({match_number})|{match_first_comma}|{match_comma_pair}|{match_last_comma}"
re_pattern = re.compile(pattern)

def parse_array_of_floats(text):
    elements = re_pattern.findall(text)
    return [value_to_float(v[0]) for v in elements]

def value_to_float(value_encoded: str):
    if len(value_encoded) == 0:
        return 0
    return float(value_encoded)

