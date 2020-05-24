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
import bpy
import operator as op
from .. import operators
from itertools import groupby


keymaps_meta = {"Frames": "EMPTY", "Sequencer": "SEQUENCE_EDITOR", "Markers": "EMPTY"}


def set_keymap_property(properties, property_name, value):
    try:
        setattr(properties, property_name, value)
    except AttributeError:
        print(
            "Warning: property '%s' not found in keymap item '%s'"
            % (property_name, properties.__class__.__name__)
        )
    except Exception as e:
        print("Warning: %r" % e)


def register_shortcuts(operator_classes):
    def keymapgetter(operator):
        return operator[1]["keymap"]

    data = operator_classes
    data = map(lambda operator: op.attrgetter("bl_idname", "doc")(operator), data)
    data = {k: v for k, v in data if v != {}}
    data.update(operators.doc)
    data = sorted(data.items(), key=keymapgetter)
    data = groupby(data, key=keymapgetter)

    kms = []
    wm = bpy.context.window_manager
    for name, group in data:
        km = wm.keyconfigs.addon.keymaps.new(name=name, space_type=keymaps_meta[name])
        for bl_idname, d in group:
            for s in d["shortcuts"]:
                kmi = km.keymap_items.new(bl_idname, **s[0])
                for pn, pv in s[1].items():
                    set_keymap_property(kmi.properties, pn, pv)
                kms.append((km, kmi))
    return kms
