# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
    kc = wm.keyconfigs.addon
    if kc is not None:
        for name, group in data:
            km = wm.keyconfigs.addon.keymaps.new(name=name, space_type=keymaps_meta[name])
            for bl_idname, d in group:
                for s in d["shortcuts"]:
                    kmi = km.keymap_items.new(bl_idname, **s[0])
                    for pn, pv in s[1].items():
                        set_keymap_property(kmi.properties, pn, pv)
                    kms.append((km, kmi))
    return kms
