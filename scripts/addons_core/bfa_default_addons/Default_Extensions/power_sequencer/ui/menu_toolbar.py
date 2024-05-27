# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


class POWER_SEQUENCER_MT_main(bpy.types.Menu):
    bl_label = "Power Sequencer"

    def draw(self, context):
        layout = self.layout

        layout.separator()

        layout.menu("POWER_SEQUENCER_MT_file")
        layout.menu("POWER_SEQUENCER_MT_edit")
        layout.menu("POWER_SEQUENCER_MT_select")
        layout.menu("POWER_SEQUENCER_MT_trim")
        layout.menu("POWER_SEQUENCER_MT_strips")
        layout.menu("POWER_SEQUENCER_MT_transitions")
        layout.menu("POWER_SEQUENCER_MT_audio")
        layout.menu("POWER_SEQUENCER_MT_playback")
        layout.menu("POWER_SEQUENCER_MT_preview")
        layout.menu("POWER_SEQUENCER_MT_markers")

        layout.separator()

        layout.operator("power_sequencer.render_apply_preset", text="Apply Render Preset")


class POWER_SEQUENCER_MT_playback(bpy.types.Menu):
    bl_label = "Playback"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.playback_speed_increase")
        layout.operator("power_sequencer.playback_speed_decrease")
        layout.operator("power_sequencer.playback_speed_set")


class POWER_SEQUENCER_MT_strips(bpy.types.Menu):
    bl_label = "Strip"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.speed_up_movie_strip")
        layout.operator("power_sequencer.speed_remove_effect")

        layout.separator()

        layout.operator("power_sequencer.concatenate_strips")
        layout.operator("power_sequencer.swap_strips")
        layout.operator("power_sequencer.toggle_selected_mute")
        layout.operator("power_sequencer.channel_offset")

        layout.separator()

        layout.operator("power_sequencer.make_hold_frame")


class POWER_SEQUENCER_MT_transitions(bpy.types.Menu):
    bl_label = "Transition"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.fade_add")
        layout.operator("power_sequencer.fade_clear")

        layout.separator()

        layout.operator("power_sequencer.crossfade_add")
        layout.operator("power_sequencer.crossfade_edit")
        layout.operator("power_sequencer.transitions_remove")


class POWER_SEQUENCER_MT_select(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("power_sequencer.select_linked_effect")

        layout.separator()

        layout.operator("power_sequencer.deselect_all_strips_left_or_right")
        layout.operator("power_sequencer.deselect_handles_and_grab")


class POWER_SEQUENCER_MT_edit(bpy.types.Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.delete_direct")
        layout.operator("power_sequencer.ripple_delete")

        layout.separator()

        layout.operator("power_sequencer.gap_remove")
        layout.operator(
            "power_sequencer.copy_selected_sequences", text="Copy Selected", icon="COPYDOWN"
        )

        layout.separator()

        layout.operator("power_sequencer.grab")
        layout.operator("power_sequencer.grab_closest_cut")
        layout.operator("power_sequencer.grab_sequence_handles")

        layout.separator()

        layout.operator("power_sequencer.trim_left_or_right_handles")
        layout.operator("power_sequencer.snap_selection")

        layout.separator()

        layout.operator("power_sequencer.scene_cycle")


class POWER_SEQUENCER_MT_markers(bpy.types.Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        layout.operator("power_sequencer.marker_delete_closest")
        layout.operator("power_sequencer.marker_delete_direct")

        layout.separator()

        layout.operator("power_sequencer.copy_markers_as_timecodes")
        layout.operator("power_sequencer.marker_snap_to_cursor")
        layout.operator("power_sequencer.set_preview_between_markers")
        layout.operator("power_sequencer.markers_snap_matching_strips")


class POWER_SEQUENCER_MT_file(bpy.types.Menu):
    bl_label = "File"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "power_sequencer.open_project_directory",
            text="Open Project Directory",
            icon="FILE_FOLDER",
        )
        layout.operator("power_sequencer.save_direct")
        layout.operator("power_sequencer.import_local_footage")


class POWER_SEQUENCER_MT_trim(bpy.types.Menu):
    bl_label = "Trim"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.trim_three_point_edit")
        layout.operator("power_sequencer.trim_to_surrounding_cuts")

        layout.separator()

        layout.operator("power_sequencer.mouse_trim")
        layout.operator("power_sequencer.mouse_trim_instantly")


class POWER_SEQUENCER_MT_preview(bpy.types.Menu):
    bl_label = "Preview"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.preview_closest_cut")
        layout.operator("power_sequencer.preview_to_selection")

        layout.separator()

        layout.operator("power_sequencer.set_timeline_range")


class POWER_SEQUENCER_MT_audio(bpy.types.Menu):
    bl_label = "Audio"

    def draw(self, context):
        layout = self.layout
        layout.operator("power_sequencer.align_audios")
        layout.operator("power_sequencer.toggle_waveforms")
        layout.operator("power_sequencer.mouse_toggle_mute")
