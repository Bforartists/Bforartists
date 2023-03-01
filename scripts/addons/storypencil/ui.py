# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from bpy.types import (
    Menu,
    Panel,
)

from .synchro import get_main_window,  validate_sync, window_id


# ------------------------------------------------------
# Defines UI panel
# ------------------------------------------------------
# ------------------------------------------------------------------
# Define panel class for manual switch parameters.
# ------------------------------------------------------------------
class STORYPENCIL_PT_Settings(Panel):
    bl_idname = "STORYPENCIL_PT_Settings"
    bl_label = "Settings"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Storypencil'

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != 'SEQUENCER':
            return False

        return True

    # ------------------------------
    # Draw UI
    # ------------------------------
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False


class STORYPENCIL_PT_General(Panel):
    bl_idname = "STORYPENCIL_PT_General"
    bl_label = "General"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Storypencil'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "STORYPENCIL_PT_Settings"

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != 'SEQUENCER':
            return False

        return True

    # ------------------------------
    # Draw UI
    # ------------------------------
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene

        setup_ready = scene.storypencil_main_workspace is not None
        row = layout.row()
        row.alert = not setup_ready
        row.prop(scene, "storypencil_main_workspace", text="VSE Workspace")

        row = layout.row()
        if scene.storypencil_main_scene is None:
            row.alert = True
        row.prop(scene, "storypencil_main_scene", text="VSE Scene")

        layout.separator()

        row = layout.row()
        if scene.storypencil_main_workspace and scene.storypencil_edit_workspace:
            if scene.storypencil_main_workspace.name == scene.storypencil_edit_workspace.name:
                row.alert = True
        if scene.storypencil_edit_workspace is None:
            row.alert = True
        row.prop(scene, "storypencil_edit_workspace", text="Drawing Workspace")


class STORYPENCIL_PT_RenderPanel(Panel):
    bl_label = "Render Strips"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Storypencil'
    bl_parent_id = "STORYPENCIL_PT_Settings"

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != 'SEQUENCER':
            return False

        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        settings = scene.render.image_settings

        is_video = settings.file_format in {'FFMPEG', 'AVI_JPEG', 'AVI_RAW'}
        row = layout.row()
        if scene.storypencil_render_render_path is None:
            row.alert = True
        row.prop(scene, "storypencil_render_render_path")

        row = layout.row()
        row.prop(scene, "storypencil_render_onlyselected")

        row = layout.row()
        row.prop(scene.render.image_settings, "file_format")

        if settings.file_format == 'FFMPEG':
            row = layout.row()
            row.prop(scene.render.ffmpeg, "format")

        row = layout.row()
        row.enabled = is_video
        row.prop(scene.render.ffmpeg, "audio_codec")

        row = layout.row()
        row.prop(scene, "storypencil_add_render_strip")

        row = layout.row()
        row.enabled = scene.storypencil_add_render_strip
        row.prop(scene, "storypencil_render_channel")

        if not is_video:
            row = layout.row()
            row.prop(scene, "storypencil_render_step")

            row = layout.row()
            row.prop(scene, "storypencil_render_numbering")

            row = layout.row()
            row.prop(scene, "storypencil_add_render_byfolder")


# ------------------------------------------------------------------
# Define panel class for new base scene creation.
# ------------------------------------------------------------------
class STORYPENCIL_PT_SettingsNew(Panel):
    bl_idname = "STORYPENCIL_PT_SettingsNew"
    bl_label = "New Scenes"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Storypencil'
    bl_parent_id = "STORYPENCIL_PT_Settings"

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != 'SEQUENCER':
            return False

        return True

    # ------------------------------
    # Draw UI
    # ------------------------------
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene
        row = layout.row()
        row.prop(scene, "storypencil_name_prefix", text="Name Prefix")
        row = layout.row()
        row.prop(scene, "storypencil_name_suffix", text="Name Suffix")
        row = layout.row()
        row.prop(scene, "storypencil_scene_duration", text="Frames")

        row = layout.row()
        if scene.storypencil_base_scene is None:
            row.alert = True
        row.prop(scene, "storypencil_base_scene", text="Template Scene")


class STORYPENCIL_PT_ModePanel(Panel):
    bl_label = "Edit Scenes"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Storypencil'
    bl_parent_id = "STORYPENCIL_PT_Settings"

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != 'SEQUENCER':
            return False

        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        wm = bpy.context.window_manager
        scene = context.scene
        win_id = window_id(context.window)

        col = layout.column(align=True)
        col.prop(scene, "storypencil_mode", text="Mode")

        col.prop(wm.storypencil_settings,
                    "show_main_strip_range", text="Show Strip Range")


        if scene.storypencil_mode == 'WINDOW':
            if not validate_sync(window_manager=wm) or win_id == wm.storypencil_settings.main_window_id:
                col.prop(wm.storypencil_settings, "active",
                        text="Timeline Synchronization")

        if scene.storypencil_mode == 'SWITCH':
            col.separator()
            col = layout.column(heading="Audio", align=True)
            col.prop(scene, "storypencil_copy_sounds", text="Copy to Scene")

            subcol = col.column(align=True)
            subcol.prop(scene, 'storypencil_skip_sound_mute')
            subcol.enabled = scene.storypencil_copy_sounds is True or scene.storypencil_mode == 'WINDOW'
