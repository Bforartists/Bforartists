import bpy

from spa_sequencer.utils import register_classes, unregister_classes


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
