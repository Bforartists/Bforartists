# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.types import (
    Panel,
)
from bpy.app.translations import (
    contexts as i18n_contexts,
    pgettext_iface as iface_,
)
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
    AnnotationOnionSkin,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)
from rna_prop_ui import PropertyPanel

class toolshelf_calculate(Panel):

    @staticmethod
    def ts_width(layout, region, scale_y):

        # Currently this just checks the width,
        # we could have different layouts as preferences too.
        system = bpy.context.preferences.system
        view2d = region.view2d
        view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
        )
        width_scale = region.width * view2d_scale / system.ui_scale

        # how many rows. 4 is text buttons.

        if width_scale > 160.0:
            column_count = 4
        elif width_scale > 140.0:
            column_count = 3
        elif width_scale > 90:
            column_count = 2
        else:
            column_count = 1

        return column_count

# ------------------------------------- No limit ---------------------------------------------#


class SEQUENCER_PT_imagetab_clear(toolshelf_calculate, Panel):
    bl_label = "Clear"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Image"
    bl_options = {'HIDE_BG'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.vse_show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("sequencer.strip_transform_clear", text="Position", icon = "CLEARMOVE").property = 'POSITION'
            col.operator("sequencer.strip_transform_clear", text="Scale", icon = "CLEARSCALE").property = 'SCALE'
            col.operator("sequencer.strip_transform_clear", text="Rotation", icon = "CLEARROTATE").property = 'ROTATION'
            col.operator("sequencer.strip_transform_clear", text="All Transforms", icon = "CLEAR").property = 'ALL'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2
            col.operator_context = 'INVOKE_REGION_PREVIEW'

            if column_count == 3:

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEARMOVE").property = 'POSITION'
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEARSCALE").property = 'SCALE'
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEARROTATE").property = 'ROTATION'

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEAR").property = 'ALL'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEARMOVE").property = 'POSITION'
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEARSCALE").property = 'SCALE'

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEARROTATE").property = 'ROTATION'
                row.operator("sequencer.strip_transform_clear", text="", icon = "CLEAR").property = 'ALL'

            elif column_count == 1:

                col.operator("sequencer.strip_transform_clear", text="", icon = "CLEARMOVE").property = 'POSITION'
                col.operator("sequencer.strip_transform_clear", text="", icon = "CLEARSCALE").property = 'SCALE'
                col.operator("sequencer.strip_transform_clear", text="", icon = "CLEARROTATE").property = 'ROTATION'
                col.operator("sequencer.strip_transform_clear", text="", icon = "CLEAR").property = 'ALL'


class SEQUENCER_PT_imagetab_image(toolshelf_calculate, Panel):
    bl_label = "Image"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Image"
    bl_options = {'HIDE_BG'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.vse_show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("sequencer.strip_transform_fit", text="Scale To Fit", icon = "VIEW_FIT").fit_method = 'FIT'
            col.operator("sequencer.strip_transform_fit", text="Scale to Fill", icon = "VIEW_FILL").fit_method = 'FILL'
            col.operator("sequencer.strip_transform_fit", text="Stretch To Fill", icon = "VIEW_STRETCH").fit_method = 'STRETCH'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_FIT").fit_method = 'FIT'
                row.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_FILL").fit_method = 'FILL'
                row.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_STRETCH").fit_method = 'STRETCH'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_FIT").fit_method = 'FIT'
                row.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_FILL").fit_method = 'FILL'

                row = col.row(align=True)
                row.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_STRETCH").fit_method = 'STRETCH'

            elif column_count == 1:

                col.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_FIT").fit_method = 'FIT'
                col.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_FILL").fit_method = 'FILL'
                col.operator("sequencer.strip_transform_fit", text="", icon = "VIEW_STRETCH").fit_method = 'STRETCH'

# ------------------------------------- Just sequencer ---------------------------------------------#


class SEQUENCER_PT_sequencer_striptab_transform(toolshelf_calculate, Panel):
    bl_label = "Transform"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Strip"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        st = context.space_data

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.vse_show_toolshelf_tabs and st.view_type in {'SEQUENCER'}

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        layout.operator_context = 'INVOKE_REGION_WIN'

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("transform.seq_slide", text="Move", icon = "TRANSFORM_MOVE")
            col.operator("transform.transform", text="Move/Extend from Current Frame", icon = "SEQ_MOVE_EXTEND").mode = 'TIME_EXTEND'
            col.operator("sequencer.slip", text="Slip Strip Contents", icon = "SEQ_SLIP_CONTENTS")

            col.separator()

            col.operator("sequencer.snap", icon = "SEQ_SNAP_STRIP")
            col.operator("sequencer.offset_clear", icon = "SEQ_CLEAR_OFFSET")

            col.separator()

            col.operator("sequencer.swap", text="Swap Strip Left", icon = "SEQ_SWAP_LEFT").side = 'LEFT'
            col.operator("sequencer.swap", text="Swap Strip Right", icon = "SEQ_SWAP_RIGHT").side = 'RIGHT'

            col.separator()

            col.operator("sequencer.gap_remove", icon = "SEQ_REMOVE_GAPS").all = False
            col.operator("sequencer.gap_insert", icon = "SEQ_INSERT_GAPS")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.seq_slide", text="", icon = "TRANSFORM_MOVE")
                row.operator("transform.transform", text="", icon = "SEQ_MOVE_EXTEND").mode = 'TIME_EXTEND'
                row.operator("sequencer.slip", text="", icon = "SEQ_SLIP_CONTENTS")

                row = col.row(align=True)
                row.operator("sequencer.snap", text="", icon = "SEQ_SNAP_STRIP")
                row.operator("sequencer.offset_clear", text="", icon = "SEQ_CLEAR_OFFSET")
                row.operator("sequencer.swap", text="", icon = "SEQ_SWAP_LEFT").side = 'LEFT'

                row = col.row(align=True)
                row.operator("sequencer.swap", text="", icon = "SEQ_SWAP_RIGHT").side = 'RIGHT'
                row.operator("sequencer.gap_remove", text="", icon = "SEQ_REMOVE_GAPS").all = False
                row.operator("sequencer.gap_insert", text="", icon = "SEQ_INSERT_GAPS")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.seq_slide", text="", icon = "TRANSFORM_MOVE")
                row.operator("transform.transform", text="", icon = "SEQ_MOVE_EXTEND").mode = 'TIME_EXTEND'

                row = col.row(align=True)
                row.operator("sequencer.slip", text="", icon = "SEQ_SLIP_CONTENTS")
                row.operator("sequencer.snap", text="", icon = "SEQ_SNAP_STRIP")

                row = col.row(align=True)
                row.operator("sequencer.offset_clear", text="", icon = "SEQ_CLEAR_OFFSET")
                row.operator("sequencer.swap", text="", icon = "SEQ_SWAP_LEFT").side = 'LEFT'

                row = col.row(align=True)
                row.operator("sequencer.swap", text="", icon = "SEQ_SWAP_RIGHT").side = 'RIGHT'
                row.operator("sequencer.gap_remove", text="", icon = "SEQ_REMOVE_GAPS").all = False

                row = col.row(align=True)
                row.operator("sequencer.gap_insert", text="", icon = "SEQ_INSERT_GAPS")

            elif column_count == 1:

                col.operator("transform.seq_slide", text="", icon = "TRANSFORM_MOVE")
                col.operator("transform.transform", text="", icon = "SEQ_MOVE_EXTEND").mode = 'TIME_EXTEND'
                col.operator("sequencer.slip", text="", icon = "SEQ_SLIP_CONTENTS")

                col.separator()

                col.operator("sequencer.snap", text="", icon = "SEQ_SNAP_STRIP")
                col.operator("sequencer.offset_clear", text="", icon = "SEQ_CLEAR_OFFSET")

                col.separator()

                col.operator("sequencer.swap", text="", icon = "SEQ_SWAP_LEFT").side = 'LEFT'
                col.operator("sequencer.swap", text="", icon = "SEQ_SWAP_RIGHT").side = 'RIGHT'

                col.separator()

                col.operator("sequencer.gap_remove", text="", icon = "SEQ_REMOVE_GAPS").all = False
                col.operator("sequencer.gap_insert", text="", icon = "SEQ_INSERT_GAPS")


class SEQUENCER_PT_sequencer_striptab_split(toolshelf_calculate, Panel):
    bl_label = "Split"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Strip"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        st = context.space_data

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.vse_show_toolshelf_tabs and st.view_type in {'SEQUENCER'}

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        layout.operator_context = 'INVOKE_REGION_WIN'

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("sequencer.split", text="Split", icon='CUT').type = 'SOFT'
            col.operator("sequencer.split", text="Hold Split", icon='HOLD_SPLIT').type = 'HARD'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("sequencer.split", text="", icon='CUT').type = 'SOFT'
                row.operator("sequencer.split", text="", icon='HOLD_SPLIT').type = 'HARD'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("sequencer.split", text="", icon='CUT').type = 'SOFT'
                row.operator("sequencer.split", text="", icon='HOLD_SPLIT').type = 'HARD'

            elif column_count == 1:

                col.operator("sequencer.split", text="", icon='CUT').type = 'SOFT'
                col.operator("sequencer.split", text="", icon='HOLD_SPLIT').type = 'HARD'

classes = (
    SEQUENCER_PT_imagetab_clear,
    SEQUENCER_PT_imagetab_image,
    SEQUENCER_PT_sequencer_striptab_transform,
    SEQUENCER_PT_sequencer_striptab_split,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
