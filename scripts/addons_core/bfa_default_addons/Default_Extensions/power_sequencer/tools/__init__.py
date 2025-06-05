# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import os


def get_tool_classes():
    """Returns the list of tools in the add-on"""
    this_file = os.path.dirname(__file__)
    module_files = [
        f for f in os.listdir(this_file) if f.endswith(".py") and not f.startswith("__init__")
    ]
    module_paths = ["." + os.path.splitext(f)[0] for f in module_files]
    classes = []
    for path in module_paths:
        module = importlib.import_module(path, package=__package__)
        tool_names = [entry for entry in dir(module) if entry.startswith("POWER_SEQUENCER_TOOL")]
        classes.extend([getattr(module, name) for name in tool_names])
    return classes
