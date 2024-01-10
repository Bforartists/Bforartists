# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

import bpy

from bfa_3Dsequencer.sync.core import get_sync_settings, sync_system_update

from bfa_3Dsequencer.utils import register_classes, unregister_classes



class WM_OT_timeline_sync_toggle(bpy.types.Operator):
    bl_idname = "wm.timeline_sync_toggle"
    bl_label = "Toggle 3D View Sync"
    bl_description = "Toggles syncronization between the Timeline scene strips from the Master Scene and 3D View. \nTo use, set the sequencer Timeline to the Master Scene, \nThen toggle to syncronize the 3D View with the Sequencer"
    bl_options = set()

    def execute(self, context: bpy.types.Context):
        sync_settings = get_sync_settings()
        sync_settings.enabled = not sync_settings.enabled

        # Setup with active space's data if applicable
        if (
            sync_settings.enabled
            and isinstance(context.space_data, bpy.types.SpaceSequenceEditor)
            and context.space_data.scene_override
        ):
            # Use overriden scene defined in the SpaceSequence editor as master scene
            sync_settings.master_scene = context.space_data.scene_override

        # Trigger sync system update
        sync_system_update(context)

        return {"FINISHED"}


class WM_OT_timeline_sync_play_master(bpy.types.Operator):
    bl_idname = "wm.timeline_sync_play_master"
    bl_label = "Play Master Scene"
    bl_description = "Toggle playback of master scene in the Timeline"
    bl_options = set()

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_settings().master_scene is not None

    def execute(self, context: bpy.types.Context):
        # Trigger playback on master scene using context override.
        with context.temp_override(scene=get_sync_settings().master_scene):
            bpy.ops.screen.animation_play("INVOKE_DEFAULT")
        return {"FINISHED"}


class SEQUENCER_OT_change_3d_view_scene(bpy.types.Operator):
    """Change scene to active strip scene"""
    bl_idname = "sequencer.change_3d_view_scene"
    bl_label = "Toggle Scene Strip"
    bl_description = "Updates the current scene to active scene strip \nIf timeline in sequencer not set, this toggles the current scene to active scene strip in the sequencer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the active strip
        seq_editor = context.scene.sequence_editor
        if seq_editor is None or seq_editor.active_strip is None:
            self.report({'WARNING'}, "No active strip")
            return {'CANCELLED'}

        strip = seq_editor.active_strip

        # Check if the strip is a scene strip
        if strip.type != 'SCENE':
            self.report({'WARNING'}, "Active strip is not a scene strip")
            return {'CANCELLED'}

        # Get the scene from the strip
        scene = strip.scene
        if scene is None:
            self.report({'WARNING'}, "Scene strip has no scene")
            return {'CANCELLED'}

        # Change the current scene to the strip's scene
        context.window.scene = scene

        return {'FINISHED'}


classes = (
    WM_OT_timeline_sync_toggle,
    WM_OT_timeline_sync_play_master,
    SEQUENCER_OT_change_3d_view_scene,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
