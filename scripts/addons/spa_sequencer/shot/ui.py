# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.utils import register_classes, unregister_classes


class SEQUENCER_MT_shot_clean_up(bpy.types.Menu):
    """Shot clean-up menu"""

    bl_idname = "SEQUENCER_MT_shot_clean_up"
    bl_label = "Clean Up"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.shot_chronological_numbering")


class SEQUENCER_MT_shot(bpy.types.Menu):
    """Shot operators menu"""

    bl_idname = "SEQUENCER_MT_shot"
    bl_label = "Shot"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.shot_new", text="New...")
        layout.operator("sequencer.shot_duplicate")
        layout.operator("sequencer.shot_delete", text="Delete...")
        layout.separator()
        layout.operator("sequencer.shot_rename", text="Rename...")
        layout.operator("sequencer.shot_timing_adjust")
        layout.separator()
        layout.menu("SEQUENCER_MT_shot_clean_up")


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
