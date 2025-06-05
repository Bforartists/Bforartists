# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy


mu_override_type_enums = [
    ('OVERRIDE_ALL', "Override all assigned slots",
        "Remove any current material slots, and assign the current material"),
    ('OVERRIDE_CURRENT', 'Assign material to currently selected slot',
        'Only assign the material to the material slot that\'s currently selected'),
    ('OVERRIDE_SLOTS', 'Assign material to each slot',
        'Keep the material slots, but assign the selected material in each slot'),
    ('APPEND_MATERIAL', 'Append Material',
        'Add the material in a new slot, and assign it to the whole object')
]

mu_clean_slots_enums = (('ACTIVE', "Active object", "Materials of active object only"),
                        ('SELECTED', "Selected objects", "Materials of selected objects"),
                        ('SCENE', "Scene objects", "Materials of objects in current scene"),
                        ('ALL', "All", "All materials in this blend file"))

mu_affect_enums = (('ACTIVE', "Active object", "Affect the active object only"),
                   ('SELECTED', "Selected objects", "Affect all selected objects"),
                   ('SCENE', "Scene objects", "Affect all objects in the current scene"),
                   ('ALL', "All", "All objects in this blend file"))

mu_fake_user_set_enums = (('ON', "On", "Enable fake user"),
                          ('OFF', "Off", "Disable fake user"),
                          ('TOGGLE', "Toggle", "Toggle fake user"))
mu_fake_user_affect_enums = (('ACTIVE', "Active object", "Materials of active object only"),
                             ('SELECTED', "Selected objects", "Materials of selected objects"),
                             ('SCENE', "Scene objects", "Materials of objects in current scene"),
                             ('USED', "Used", "All materials used by objects"),
                             ('UNUSED', "Unused", "Currently unused materials"),
                             ('ALL', "All", "All materials in this blend file"))

mu_link_to_enums = (('DATA', "Data", "Link the materials to the data"),
                    ('OBJECT', "Object", "Link the materials to the object"),
                    ('TOGGLE', "Toggle", "Toggle what the materials are currently linked to"))
mu_link_affect_enums = (('ACTIVE', "Active object", "Materials of active object only"),
                        ('SELECTED', "Selected objects", "Materials of selected objects"),
                        ('SCENE', "Scene objects", "Materials of objects in current scene"),
                        ('ALL', "All", "All materials in this blend file"))

mu_material_slot_move_enums = (('TOP', "Top", "Move slot to the top"),
                               ('BOTTOM', "Bottom", "Move slot to the bottom"))
