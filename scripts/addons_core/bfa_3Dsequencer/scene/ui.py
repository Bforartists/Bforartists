# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

import bpy

from ..sync.core import get_sync_settings
from ..utils import register_classes, unregister_classes


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

        # BFA (#6780): opt-in batch operator - clamp every scene strip's scene
        # frame range to its visible extent in the timeline, with lead-in/out
        # padding (operator dialog). Only the scene render range is affected.
        layout.operator(
            "sequencer.sync_scene_strip_ranges",
            text="Sync Scene Strip Frame Ranges",
            icon="TIME",
        )

        # Operator to update to active scene strip
        layout.operator('sequencer.change_3d_view_scene', text='Toggle Active Scene Strip', icon="FILE_REFRESH")

        # Operator to playback the master scene
        # BFA (#6780): legacy sync only - in built-in sync mode playback is
        # natively synchronized bidirectionally, so this master-scene jump is
        # unnecessary there.
        if get_sync_settings().is_legacy():
            layout.operator('wm.timeline_sync_play_master', icon="PLAY")

        #layout.operator("sequencer.shot_new", text="New...")  #BFA - temporariliy removed
        #layout.operator("sequencer.shot_duplicate")  #BFA - temporariliy removed
        #layout.operator("sequencer.shot_delete", text="Delete...")  #BFA - temporariliy removed

        #layout.operator("sequencer.shot_rename", text="Rename...")  #BFA - temporariliy removed

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
