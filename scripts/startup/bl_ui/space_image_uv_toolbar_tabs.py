# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

import bpy
from bpy.types import Panel
import math

from bl_ui.properties_paint_common import (
    UnifiedPaintPanel,
    brush_texture_settings,
    brush_basic_texpaint_settings,
    brush_settings,
    brush_settings_advanced,
    draw_color_settings,
    ClonePanel,
    BrushSelectPanel,
    TextureMaskPanel,
    ColorPalettePanel,
    StrokePanel,
    SmoothStrokePanel,
    FalloffPanel,
    DisplayPanel,
)
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
    toolsystem_column_count,
)

from bpy.app.translations import pgettext_iface as iface_

from bl_ui.space_toolsystem_common import (
    toolsystem_column_count,
    Separator,
    OperatorEntry,
    MenuEntry,
    SetOperatorContext,
    draw_entries,
)


class IMAGE_PT_uvtab_transform(Panel):
    bl_label = "Transform"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = [
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("transform.rotate", text="Rotate Clockwise 90\u00B0", icon="ROTATE_PLUS_90", props={"value": math.pi / 2}),
            OperatorEntry("transform.rotate", text="Rotate Counter-Clockwise 90\u00B0", icon="ROTATE_MINUS_90", props={"value": math.pi / -2}),
            SetOperatorContext('INVOKE_DEFAULT'),
            Separator,
            OperatorEntry("transform.shear", icon='SHEAR'),
        ]

        ts = context.tool_settings
        if ts.use_uv_select_sync:
            is_vert_mode, is_edge_mode, _ = ts.mesh_select_mode
        else:
            uv_select_mode = ts.uv_select_mode
            is_vert_mode = uv_select_mode == 'VERTEX'
            is_edge_mode = uv_select_mode == 'EDGE'

        if is_vert_mode or is_edge_mode:
            if is_vert_mode:
                entries.extend([
                    SetOperatorContext('INVOKE_DEFAULT'),
                    OperatorEntry("transform.vert_slide", icon='SLIDE_VERTEX'),
                ])

            if is_edge_mode:
                entries.extend([
                    SetOperatorContext('INVOKE_DEFAULT'),
                    OperatorEntry("transform.edge_slide", icon='SLIDE_EDGE'),
                ])

        entries.extend([
            OperatorEntry("uv.randomize_uv_transform", icon='RANDOMIZE'),
        ])

        draw_entries(layout, context, entries)


class IMAGE_PT_uvtab_mirror(Panel):
    bl_label = "Mirror"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("uv.copy_mirrored_faces", icon="COPYMIRRORED"),
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("transform.mirror", text="X Axis", icon="MIRROR_X", props={"constraint_axis": (True, False, False)}),
            OperatorEntry("transform.mirror", text="Y Axis", icon="MIRROR_Y", props={"constraint_axis": (False, True, False)}),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_uvtab_snap(Panel):
    bl_label = "Snap"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = (
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("uv.snap_selected", text="Selected to Pixels", icon="SNAP_TO_PIXELS", props={"target": 'PIXELS'}),
            OperatorEntry("uv.snap_selected", text="Selected to Cursor", icon="SELECTIONTOCURSOR", props={"target": 'CURSOR'}),
            OperatorEntry("uv.snap_selected", text="Selected to Cursor (Offset),", icon="SELECTIONTOCURSOROFFSET", props={"target": 'CURSOR_OFFSET'}),
            OperatorEntry("uv.snap_selected", text="Selected to Adjacent Unselected", icon="SNAP_TO_ADJACENT", props={"target": 'ADJACENT_UNSELECTED'}),
            Separator,
            OperatorEntry("uv.snap_cursor", text="Cursor to Pixels", icon="CURSOR_TO_PIXELS", props={"target": 'PIXELS'}),
            OperatorEntry("uv.snap_cursor", text="Cursor to Selected", icon="CURSORTOSELECTION", props={"target": 'SELECTED'}),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_uvtab_unwrap(Panel):
    bl_label = "Unwrap"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("uv.unwrap", text="Unwrap Angle Based", icon='UNWRAP_ABF', props={"method": 'ANGLE_BASED'}),
            OperatorEntry("uv.unwrap", text="Unwrap Conformal", icon='UNWRAP_LSCM', props={"method": 'CONFORMAL'}),
            Separator,
            SetOperatorContext('INVOKE_DEFAULT'),
            OperatorEntry("uv.smart_project", icon="MOD_UVPROJECT"),
            OperatorEntry("uv.lightmap_pack", icon="LIGHTMAPPACK"),
            OperatorEntry("uv.follow_active_quads", icon="FOLLOWQUADS"),
            Separator,
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("uv.cube_project", icon="CUBEPROJECT"),
            OperatorEntry("uv.cylinder_project", icon="CYLINDERPROJECT"),
            OperatorEntry("uv.sphere_project", icon="SPHEREPROJECT"),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_uvtab_merge(Panel):
    bl_label = "Merge"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("uv.weld", text="At Center", icon='MERGE_CENTER'),
            OperatorEntry("uv.snap_selected", text="At Cursor", icon='MERGE_CURSOR', props={"target": 'CURSOR'}),
            Separator,
            OperatorEntry("uv.remove_doubles", text="By Distance", icon='REMOVE_DOUBLES'),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_uvtab_uvtools(Panel):
    bl_label = "UV Tools"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("uv.pin", icon="PINNED", props={"clear": False}),
            OperatorEntry("uv.pin", text="Unpin", icon="UNPINNED", props={"clear": True}),
            OperatorEntry("uv.select_split", text="Split Selection", icon='SPLIT'),
            Separator,
            OperatorEntry("uv.pack_islands", icon="PACKISLAND"),
            OperatorEntry("uv.average_islands_scale", icon="AVERAGEISLANDSCALE"),
            OperatorEntry("uv.minimize_stretch", icon="MINIMIZESTRETCH"),
            OperatorEntry("uv.stitch", icon="STITCH"),
            Separator,
            OperatorEntry("uv.mark_seam", icon="MARK_SEAM", props={"clear": False}),
            OperatorEntry("uv.clear_seam", text="Clear Seam", icon='CLEAR_SEAM'),
            OperatorEntry("uv.seams_from_islands", icon="SEAMSFROMISLAND"),
            Separator,
            OperatorEntry("uv.reset", icon="RESET"),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_uvtab_align(Panel):
    bl_label = "Align"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("uv.align", text="Straighten", icon="ALIGN", props={"axis": 'ALIGN_S'}),
            OperatorEntry("uv.align", text="Straighten X", icon="STRAIGHTEN_X", props={"axis": 'ALIGN_T'}),
            OperatorEntry("uv.align", text="Straighten Y", icon="STRAIGHTEN_Y", props={"axis": 'ALIGN_U'}),
            OperatorEntry("uv.align", text="Align Auto", icon="ALIGNAUTO", props={"axis": 'ALIGN_AUTO'}),
            OperatorEntry("uv.align", text="Align X", icon="ALIGN_X", props={"axis": 'ALIGN_X'}),
            OperatorEntry("uv.align", text="Align Y", icon="ALIGN_Y", props={"axis": 'ALIGN_Y'}),
            OperatorEntry("uv.align_rotation", text="Align Rotation", icon="DRIVER_ROTATIONAL_DIFFERENCE"),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_image_masktab_add(Panel):
    bl_label = "Add"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs == True and sima.mode != 'UV' and sima.ui_mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        entries = (
            SetOperatorContext('INVOKE_REGION_WIN'),
            OperatorEntry("mask.primitive_circle_add", text="Circle", icon='MESH_CIRCLE'),
            OperatorEntry("mask.primitive_square_add", text="Square", icon='MESH_PLANE'),
            Separator,
            OperatorEntry("mask.add_vertex_slide", text="Add Vertex and Slide", icon='SLIDE_VERTEX'),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_image_masktab_transform(Panel):
    bl_label = "Transform"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs == True and sima.mode != 'UV' and sima.ui_mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("transform.tosphere", text="To Sphere", icon="TOSPHERE"),
            OperatorEntry("transform.shear", text="Shear", icon="SHEAR"),
            OperatorEntry("transform.push_pull", text="Push/Pull", icon="PUSH_PULL"),
            Separator,
            OperatorEntry("transform.transform", text="Scale Feather", icon='SHRINK_FATTEN', props={"mode": 'MASK_SHRINKFATTEN'}),
            OperatorEntry("mask.feather_weight_clear", text="  Clear Feather Weight", icon="CLEAR"),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_image_masktab_mask(Panel):
    bl_label = "Mask"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs == True and sima.mode != 'UV' and sima.ui_mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mask.parent_set", icon="PARENT_SET"),
            OperatorEntry("mask.parent_clear", icon="PARENT_CLEAR"),
            Separator,
            OperatorEntry("mask.cyclic_toggle", icon='TOGGLE_CYCLIC'),
            OperatorEntry("mask.switch_direction", icon='SWITCH_DIRECTION'),
            OperatorEntry("mask.normals_make_consistent", icon="RECALC_NORMALS"),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_image_masktab_handletype(Panel):
    bl_label = "Set Handle Type"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs == True and sima.mode != 'UV' and sima.ui_mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mask.handle_type_set", text="Auto", icon="HANDLE_AUTO", props={"type": 'AUTO'}),
            OperatorEntry("mask.handle_type_set", text="Vector", icon="HANDLE_VECTOR", props={"type": 'VECTOR'}),
            OperatorEntry("mask.handle_type_set", text="Aligned Single", icon='HANDLE_ALIGN_SINGLE', props={"type": 'ALIGNED'}),
            OperatorEntry("mask.handle_type_set", text="Aligned", icon='HANDLE_ALIGNED', props={"type": 'ALIGNED_DOUBLESIDE'}),
            OperatorEntry("mask.handle_type_set", text="Free", icon="HANDLE_FREE", props={"type": 'FREE'}),
        )

        draw_entries(layout, context, entries)


class IMAGE_PT_image_masktab_animation(Panel):
    bl_label = "Animation"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        return space.show_toolshelf_tabs == True and sima.mode != 'UV' and sima.ui_mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mask.shape_key_insert", text="Insert Shape Key", icon="KEYFRAMES_INSERT"),
            OperatorEntry("mask.shape_key_clear", text="Clear Shape", icon="CLEAR"),
            OperatorEntry("mask.shape_key_feather_reset", text="Reset Feather Animation", icon='RESET'),
            OperatorEntry("mask.shape_key_rekey", text="Re-key Shape Points", icon="SHAPEKEY_DATA"),
        )

        draw_entries(layout, context, entries)


classes = (
    IMAGE_PT_uvtab_transform,
    IMAGE_PT_uvtab_mirror,
    IMAGE_PT_uvtab_snap,
    IMAGE_PT_uvtab_unwrap,
    IMAGE_PT_uvtab_merge,
    IMAGE_PT_uvtab_uvtools,
    IMAGE_PT_uvtab_align,

    IMAGE_PT_image_masktab_add,
    IMAGE_PT_image_masktab_transform,
    IMAGE_PT_image_masktab_mask,
    IMAGE_PT_image_masktab_handletype,
    IMAGE_PT_image_masktab_animation,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
