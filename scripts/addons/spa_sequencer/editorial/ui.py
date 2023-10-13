# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.utils import register_classes, unregister_classes
from spa_sequencer.editorial.vse_io import HAS_OTIO


class SEQUENCER_MT_edit_conform(bpy.types.Menu):
    bl_idname = "SEQUENCER_MT_edit_conform"
    bl_label = "Conform"

    def draw(self, context):
        self.layout.operator("sequencer.edit_conform_shots_from_panels")
        self.layout.operator("sequencer.edit_conform_shots_from_editorial")


class SEQUENCER_MT_editorial(bpy.types.Menu):
    """Editorial operators menu"""

    bl_idname = "SEQUENCER_MT_editorial"
    bl_label = "Editorial"

    def draw(self, context):

        if HAS_OTIO:
            self.layout.menu("SEQUENCER_MT_edit_io")

        self.layout.menu("SEQUENCER_MT_edit_conform")


def draw_MT_editorial(self, context):
    self.layout.menu(SEQUENCER_MT_editorial.bl_idname)


classes = (
    SEQUENCER_MT_edit_conform,
    SEQUENCER_MT_editorial,
)


def register():
    register_classes(classes)
    bpy.types.SEQUENCER_MT_editor_menus.append(draw_MT_editorial)


def unregister():
    unregister_classes(classes)
    bpy.types.SEQUENCER_MT_editor_menus.remove(draw_MT_editorial)
