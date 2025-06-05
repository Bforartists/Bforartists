# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
