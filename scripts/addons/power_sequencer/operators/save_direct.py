# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later


import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_save_direct(bpy.types.Operator):
    """
    Saves current file without prompting for confirmation. Overrides Blender default
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "S", "value": "PRESS", "ctrl": True}, {}, "Direct Save")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene

    def execute(self, context):
        if bpy.data.is_saved:
            bpy.ops.wm.save_mainfile()
        else:
            # FIXME: what does this override do?
            context_override = {"dict": "override"}
            with context.temp_override(**context_override):
                bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        self.report({"INFO"}, "File saved")
        return {"FINISHED"}
