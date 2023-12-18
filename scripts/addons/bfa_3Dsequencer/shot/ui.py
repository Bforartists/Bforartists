# SPDX-License-Identifier: GPL-3.0-or-later
# BFA - temporariliy removed

import bpy

from bfa_3Dsequencer.utils import register_classes, unregister_classes


class SEQUENCER_MT_shot_clean_up(bpy.types.Menu):
    """Scene clean-up menu"""

    bl_idname = "SEQUENCER_MT_shot_clean_up"
    bl_label = "Clean Up"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.shot_chronological_numbering")


class SEQUENCER_MT_shot(bpy.types.Menu):
    """Scene operators menu"""

    bl_idname = "SEQUENCER_MT_shot"
    bl_label = "Scene"

    def draw(self, context):
        layout = self.layout

        #layout.operator("sequencer.shot_new", text="New...")  #BFA - temporariliy removed
        #layout.operator("sequencer.shot_duplicate")  #BFA - temporariliy removed
        #layout.operator("sequencer.shot_delete", text="Delete...")  #BFA - temporariliy removed
        #layout.separator()
        #layout.operator("sequencer.shot_rename", text="Rename...")  #BFA - temporariliy removed
        layout.operator("sequencer.shot_timing_adjust", icon="TIME")
        #layout.separator()
        #layout.menu("SEQUENCER_MT_shot_clean_up")  #BFA - temporariliy removed


def draw_MT_shot(self, context):
    layout = self.layout
    layout.menu(SEQUENCER_MT_shot.bl_idname)


classes = (
    SEQUENCER_MT_shot,
    SEQUENCER_MT_shot_clean_up,
)


def register():
    register_classes(classes)

    # Add SEQUENCER_MT_shot to the sequencer editor menus
    bpy.types.SEQUENCER_MT_editor_menus.append(draw_MT_shot)


def unregister():
    unregister_classes(classes)

    # Remove SEQUENCER_MT_shot from the sequencer editor menus
    bpy.types.SEQUENCER_MT_editor_menus.remove(draw_MT_shot)
