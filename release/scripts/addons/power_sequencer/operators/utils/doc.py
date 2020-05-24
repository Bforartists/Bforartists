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
Utilities to convert operator names and docstrings to human-readable text.
Used to generate names for Blender's operator search, and to generate Power Sequencer's documentation.
"""


upper_match = lambda m: m.string


def doc_idname(s):
    """
    Returns the id_name of the operator to register shortcuts in Blender's keymaps or call from other operators.
    """
    out = ".".join(map(str.lower, s.split("_OT_")))
    return out


def doc_name(s):
    """
    Returns the operator's name in a human readable format for Blender's operator search.
    Removes POWER_SEQUENCER_OT_ from an operator's identifier
    and converts it to title case.
    """
    out = s.split("_OT")[-1]
    out = out.replace("_", " ").lstrip().title()
    return out


def doc_brief(s):
    """
    Returns the first line of an operator's docstring to use as a summary of how the operator works.
    The line in question must contain *brief*.
    """
    return " ".join(s.split("\n\n")[0].split()[1:]) if s.startswith("*brief*") else s


def doc_description(s):
    """
    Returns the lines after the brief line in an operator's documentation strings. See doc_brief above.
    """
    return "\n".join(map(lambda x: x.strip(), s.split("\n"))).strip()
