# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_select_linked_strips(bpy.types.Operator):
    """
    Add/Remove linked strips near mouse pointer to/from selection without the need to
    previously have clicked/manually selected
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "L", "value": "PRESS"}, {}, "Add/Remove Linked to/from Selection")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor

    def execute(self, context):
        # save current selection first
        selection = set(context.selected_sequences)

        # if previously selected strips are linked select links as well to toggle them too
        bpy.ops.sequencer.select_linked()
        selection_new = set(context.selected_sequences).difference(selection)
        # deselect & select only the linked strips near mouse pointer
        bpy.ops.sequencer.select_all(action="DESELECT")
        # re-enable linked + add selection near mouse pointer
        for s in selection_new:
            s.select = True
        bpy.ops.sequencer.select_linked()
        bpy.ops.sequencer.select_linked_pick("INVOKE_DEFAULT", extend=True)
        selection_new = set(context.selected_sequences)

        # identify if linked strips under mouse pointer need to be added or removed
        action = len(selection.intersection(selection_new)) != len(selection_new)

        # re-enable previous selection
        for s in selection:
            s.select = True

        # take care of toggle for strips under mouse
        for s in selection_new:
            s.select = action
        return {"FINISHED"}
