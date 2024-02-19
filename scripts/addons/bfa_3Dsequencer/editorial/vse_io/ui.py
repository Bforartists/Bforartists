# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

# BFA - temporariliy removed


import bpy

from bfa_3Dsequencer.utils import register_classes, unregister_classes


class SEQUENCER_MT_edit_io(bpy.types.Menu):
    bl_idname = "SEQUENCER_MT_edit_io"
    bl_label = "Timeline I/O"

    def draw(self, context):
        self.layout.operator("import.vse_otio", text="Import Timeline...")
        self.layout.operator("export.vse_otio", text="Export Timeline...")


classes = (SEQUENCER_MT_edit_io,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
