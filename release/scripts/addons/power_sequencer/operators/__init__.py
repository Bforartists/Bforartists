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
import importlib
import os


def get_operator_classes():
    """Returns the list of operators in the add-on"""
    this_file = os.path.dirname(__file__)
    module_files = [
        f
        for f in os.listdir(this_file)
        if f.endswith(".py") and not f.startswith("__init__")
    ]
    module_paths = ["." + os.path.splitext(f)[0] for f in module_files]
    classes = []
    for path in module_paths:
        module = importlib.import_module(path, package="power_sequencer.operators")
        operator_names = [
            entry for entry in dir(module) if entry.startswith("POWER_SEQUENCER_OT")
        ]
        classes.extend([getattr(module, name) for name in operator_names])
    return classes


doc = {
    "sequencer.refresh_all": {
        "name": "Refresh All",
        "description": "",
        "shortcuts": [
            ({"type": "R", "value": "PRESS", "shift": True}, {}, "Refresh All")
        ],
        "demo": "",
        "keymap": "Sequencer",
    }
}
