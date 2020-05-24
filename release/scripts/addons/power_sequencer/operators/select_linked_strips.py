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
