# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.sync.core import get_sync_settings
from spa_sequencer.utils import register_classes, unregister_classes


class SEQUENCER_PT_SyncPanel(bpy.types.Panel):
    """Timeline Synchronization Panel."""

    bl_label = "Timeline Synchronization"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Sequencer"

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False
        settings = get_sync_settings()
        self.layout.operator(
            "wm.timeline_sync_toggle",
            text="Synchronize",
            icon="UV_SYNC_SELECT",
            depress=settings.enabled,
        )
        self.layout.prop(settings, "master_scene")


class SEQUENCER_PT_SyncPanelAdvancedSettings(bpy.types.Panel):
    """Timeline Synchronization advanced settings Panel."""

    bl_label = "Advanced Settings"
    bl_parent_id = "SEQUENCER_PT_SyncPanel"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Sequencer"

    def draw(self, context):
        settings = get_sync_settings()
        self.layout.prop(settings, "keep_gpencil_tool_settings")
        self.layout.prop(settings, "bidirectional")
        self.layout.prop(settings, "use_preview_range")
        self.layout.prop(settings, "sync_all_windows")
        self.layout.prop(settings, "active_follows_playhead")


classes = (
    SEQUENCER_PT_SyncPanel,
    SEQUENCER_PT_SyncPanelAdvancedSettings,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
