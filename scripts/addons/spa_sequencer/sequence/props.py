# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.sync.core import get_sync_settings

from spa_sequencer.utils import register_classes, unregister_classes


class SequenceSettings(bpy.types.PropertyGroup):
    """
    Sequence related settings.
    """

    overlay_dopesheet: bpy.props.BoolProperty(
        name="Dopesheet Overlay",
        description="Display Sequence timeline overlay in dopesheet editors",
        default=True,
    )

    def shot_active_index_get_cb(self):
        """Get sequence active shot index."""
        return get_sync_settings().last_master_strip_idx

    def shot_active_index_set_cb(self, idx):
        """Set sequence active shot index."""
        # Move to beginning of shot strip in master scene.
        scene = get_sync_settings().master_scene
        frame = scene.sequence_editor.sequences[idx].frame_final_start
        scene.frame_set(frame)

    shot_active_index: bpy.props.IntProperty(
        name="Active Shot Index",
        description="Index of the active shot in sequence",
        get=shot_active_index_get_cb,
        set=shot_active_index_set_cb,
        options=set(),
    )


class SequencePanelSettings(bpy.types.PropertyGroup):
    camera_viewport_is_expanded: bpy.props.BoolProperty(
        name="Expand 'Viewport Display' panel", default=False
    )
    camera_dof_is_expanded: bpy.props.BoolProperty(
        name="Expand 'Depth of Field' panel", default=False
    )
    camera_bg_is_expanded: bpy.props.BoolProperty(
        name="Expand 'Background Image' panel", default=False
    )


classes = (SequenceSettings, SequencePanelSettings)


def register():
    register_classes(classes)

    bpy.types.WindowManager.sequence_settings = bpy.props.PointerProperty(
        type=SequenceSettings,
        name="Sequence Settings",
    )

    bpy.types.WindowManager.sequence_panel_settings = bpy.props.PointerProperty(
        type=SequencePanelSettings,
        name="Sequence Panel Settings",
    )
    bpy.types.Scene.parent_scene = bpy.props.PointerProperty(
        name="Parent Scene",
        type=bpy.types.Scene,
        description="Parent of the current scene, collections from parent scene are shared into child scene by default",
    )


def unregister():
    del bpy.types.WindowManager.sequence_settings
    del bpy.types.WindowManager.sequence_panel_settings
    del bpy.types.Scene.parent_scene

    unregister_classes(classes)
