# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.types import (
    Panel,
)

from bl_ui.space_toolsystem_common import (
    Separator,
    OperatorEntry,
    draw_entries,
    toolsystem_column_count,
)
from bl_ui.space_sequencer import are_selected_strips_connected # BFA - Helper function


class SEQUENCER_PT_imagetab_clear(Panel):
    bl_label = "Clear"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Image"
    bl_options = {'HIDE_BG'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sequencer.strip_transform_clear", text="Position", icon="CLEARMOVE", props={'property' : 'POSITION'}),
            OperatorEntry("sequencer.strip_transform_clear", text="Scale", icon="CLEARSCALE", props={'property' : 'SCALE'}),
            OperatorEntry("sequencer.strip_transform_clear", text="Rotation", icon="CLEARROTATE", props={'property' : 'ROTATION'}),
            OperatorEntry("sequencer.strip_transform_clear", text="All Transforms", icon="CLEAR", props={'property' : 'ALL'}),
        )

        draw_entries(layout, context, entries)


class SEQUENCER_PT_imagetab_image(Panel):
    bl_label = "Image"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Image"
    bl_options = {'HIDE_BG'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sequencer.strip_transform_fit", text="Scale To Fit", icon="VIEW_FIT", props={"fit_method" : 'FIT'}),
            OperatorEntry("sequencer.strip_transform_fit", text="Scale to Fill", icon="VIEW_FILL", props={"fit_method" : 'FILL'}),
            OperatorEntry("sequencer.strip_transform_fit", text="Stretch To Fill", icon="VIEW_STRETCH", props={"fit_method" : 'STRETCH'}),
        )

        draw_entries(layout, context, entries)

# ------------------------------------- Just sequencer ---------------------------------------------#


class SEQUENCER_PT_sequencer_striptab_transform(Panel):
    bl_label = "Transform"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Strip"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs and space.view_type in {'SEQUENCER'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("transform.seq_slide", text="Move", icon="TRANSFORM_MOVE"),
            OperatorEntry("transform.transform", text="Move/Extend from Current Frame", icon="SEQ_MOVE_EXTEND", props={'mode' : 'TIME_EXTEND'}),
            OperatorEntry("sequencer.slip", text="Slip Strip Contents", icon="SEQ_SLIP_CONTENTS"),
            Separator,
            OperatorEntry("sequencer.snap", icon="SEQ_SNAP_STRIP"),
            OperatorEntry("sequencer.offset_clear", icon="SEQ_CLEAR_OFFSET"),
            Separator,
            OperatorEntry("sequencer.swap", text="Swap Strip Left", icon="SEQ_SWAP_LEFT", props={'side' : 'LEFT'}),
            OperatorEntry("sequencer.swap", text="Swap Strip Right", icon="SEQ_SWAP_RIGHT", props={'side' : 'RIGHT'}),
            Separator,
            OperatorEntry("sequencer.gap_remove", text="Remove Gap", icon="SEQ_REMOVE_GAPS", props={'all' : False}),
            OperatorEntry("sequencer.gap_remove", text="Remove Gap (All)", icon="SEQ_REMOVE_GAPS_ALL", props={'all' : True}),
            OperatorEntry("sequencer.gap_insert", text="Inset Gap", icon="SEQ_INSERT_GAPS"),
        )

        draw_entries(layout, context, entries)


class SEQUENCER_PT_sequencer_striptab_split(Panel):
    bl_label = "Split"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Strip"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs and space.view_type in {'SEQUENCER'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sequencer.split", text="Split", icon='CUT', props={'type' : 'SOFT'}),
            OperatorEntry("sequencer.split", text="Hold Split", icon='HOLD_SPLIT', props={'type' : 'HARD'}),
        )

        draw_entries(layout, context, entries)


class SEQUENCER_PT_sequencer_striptab_retiming(Panel):
    bl_label = "Retiming"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Strip"
    bl_options = {'HIDE_BG'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs and space.view_type in {'SEQUENCER'}

    def draw_strip_context(self, context):
        layout = self.layout

        try:
            # Determine the active strip from the pinned sequencer scene (respect workspace pin)
            seq_scene = context.sequencer_scene or context.scene
            ed_local = getattr(seq_scene, "sequence_editor", None)

            strip = getattr(ed_local, "active_strip", None) or context.active_strip
            strip_type = getattr(strip, "type", None)

            if not strip_type in {'MOVIE', 'IMAGE', 'SOUND'}:
                raise Exception
            
            retiming_show_icon = 'MOD_TIME' if getattr(strip, "show_retiming_keys", False) else 'TIME'
            retiming_show_label = "Disable Retiming" if getattr(strip, "show_retiming_keys", False) else "Enable Retiming"

            entries = (
                OperatorEntry("sequencer.retiming_show", icon=retiming_show_icon, text=retiming_show_label),
                Separator,
                OperatorEntry("sequencer.retiming_segment_speed_set", icon="SET_TIME"),
                Separator,
                OperatorEntry("sequencer.retiming_reset", icon="KEYFRAMES_REMOVE"),
            )

            draw_entries(layout, context, entries)

        except Exception:
            if toolsystem_column_count(context.region) > 1:
                func = layout.label_multiline
            else:
                func = layout.label

            func(text="Select a movie or sound strip.", icon="QUESTION")

    def draw_retiming_context(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sequencer.retiming_show", icon='MOD_TIME', text="Disable Retiming"),
            Separator,
            OperatorEntry("sequencer.retiming_segment_speed_set", icon="SET_TIME"),
            Separator,
            OperatorEntry("sequencer.retiming_key_add", icon="KEYFRAMES_INSERT"),
            OperatorEntry("sequencer.retiming_freeze_frame_add", icon="KEYTYPE_MOVING_HOLD_VEC"),
            OperatorEntry("sequencer.retiming_transition_add", icon="NODE_CURVE_TIME"),
            OperatorEntry("sequencer.retiming_key_delete", text="Delete Retiming Key", icon="DELETE"),
            Separator,
            OperatorEntry("sequencer.retiming_reset", icon="KEYFRAMES_REMOVE"),
        )

        draw_entries(layout, context, entries)

    def draw(self, context):
        seq_scene = context.sequencer_scene or context.scene
        ed = getattr(seq_scene, "sequence_editor", None)
        active_strip = getattr(ed, "active_strip", None) or context.active_strip

        if getattr(ed, "selected_retiming_keys", False) or getattr(active_strip, "show_retiming_keys", False):
            self.draw_retiming_context(context)
        else:
            self.draw_strip_context(context)


class SEQUENCER_PT_sequencer_striptab_connect(Panel):
    bl_label = "Connect"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Strip"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs and space.view_type in {'SEQUENCER'}
    
    def draw(self, context):
        layout = self.layout

        if are_selected_strips_connected(context):
            entries = (OperatorEntry("sequencer.disconnect", icon="UNLINKED"),)
        else:
            entries = (OperatorEntry("sequencer.connect", icon="LINKED", props={'toggle' : False}),)

        draw_entries(layout, context, entries)


classes = (
    SEQUENCER_PT_imagetab_clear,
    SEQUENCER_PT_imagetab_image,
    SEQUENCER_PT_sequencer_striptab_transform,
    SEQUENCER_PT_sequencer_striptab_split,
    SEQUENCER_PT_sequencer_striptab_retiming,
    SEQUENCER_PT_sequencer_striptab_connect,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
