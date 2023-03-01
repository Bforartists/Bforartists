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
)

from bpy.app.translations import pgettext_iface as iface_


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


class IMAGE_PT_uvtab_transform(toolshelf_calculate, Panel):
    bl_label = "Transform"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("transform.rotate", text="Rotate +90°", icon="ROTATE_PLUS_90").value = math.pi / 2
            col.operator("transform.rotate", text="Rotate  - 90°", icon="ROTATE_MINUS_90").value = math.pi / -2
            col.operator_context = 'INVOKE_DEFAULT'

            col.separator()

            col.operator("transform.shear", icon='SHEAR')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.rotate", text="", icon="ROTATE_PLUS_90").value = math.pi / 2
                row.operator("transform.rotate", text="", icon="ROTATE_MINUS_90").value = math.pi / -2
                row.operator("transform.shear", text="", icon='SHEAR')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.rotate", text="", icon="ROTATE_PLUS_90").value = math.pi / 2
                row.operator("transform.rotate", text="", icon="ROTATE_MINUS_90").value = math.pi / -2

                row = col.row(align=True)
                row.operator("transform.shear", text="", icon='SHEAR')

            elif column_count == 1:

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("transform.rotate", text="", icon="ROTATE_PLUS_90").value = math.pi / 2
                col.operator("transform.rotate", text="", icon="ROTATE_MINUS_90").value = math.pi / -2
                col.operator_context = 'INVOKE_DEFAULT'

                col.separator()

                col.operator("transform.shear", text="", icon='SHEAR')


class IMAGE_PT_uvtab_mirror(toolshelf_calculate, Panel):
    bl_label = "Mirror"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.faces_mirror_uv", icon="COPYMIRRORED")

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("transform.mirror", text="X Axis", icon="MIRROR_X").constraint_axis[0] = True
            col.operator("transform.mirror", text="Y Axis", icon="MIRROR_Y").constraint_axis[1] = True

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.faces_mirror_uv", text="", icon="COPYMIRRORED")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("transform.mirror", text="", icon="MIRROR_X").constraint_axis[0] = True
                row.operator("transform.mirror", text="", icon="MIRROR_Y").constraint_axis[1] = True

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.faces_mirror_uv", text="", icon="COPYMIRRORED")

                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("transform.mirror", text="", icon="MIRROR_X").constraint_axis[0] = True
                row.operator("transform.mirror", text="", icon="MIRROR_Y").constraint_axis[1] = True

            elif column_count == 1:

                col.operator("mesh.faces_mirror_uv", text="", icon="COPYMIRRORED")

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("transform.mirror", text="", icon="MIRROR_X").constraint_axis[0] = True
                col.operator("transform.mirror", text="", icon="MIRROR_Y").constraint_axis[1] = True


class IMAGE_PT_uvtab_snap(toolshelf_calculate, Panel):
    bl_label = "Snap"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("uv.snap_selected", text="Selected to Pixels", icon="SNAP_TO_PIXELS").target = 'PIXELS'
            col.operator("uv.snap_selected", text="Selected to Cursor", icon="SELECTIONTOCURSOR").target = 'CURSOR'
            col.operator("uv.snap_selected", text="Selected to Cursor (Offset)",
                         icon="SELECTIONTOCURSOROFFSET").target = 'CURSOR_OFFSET'
            col.operator("uv.snap_selected", text="Selected to Adjacent Unselected",
                         icon="SNAP_TO_ADJACENT").target = 'ADJACENT_UNSELECTED'

            col.separator()

            col.operator("uv.snap_cursor", text="Cursor to Pixels", icon="CURSOR_TO_PIXELS").target = 'PIXELS'
            col.operator("uv.snap_cursor", text="Cursor to Selected", icon="CURSORTOSELECTION").target = 'SELECTED'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("uv.snap_selected", text="", icon="SNAP_TO_PIXELS").target = 'PIXELS'
                row.operator("uv.snap_selected", text="", icon="SELECTIONTOCURSOR").target = 'CURSOR'
                row.operator("uv.snap_selected", text="", icon="SELECTIONTOCURSOROFFSET").target = 'CURSOR_OFFSET'

                row = col.row(align=True)
                row.operator("uv.snap_selected", text="", icon="SNAP_TO_ADJACENT").target = 'ADJACENT_UNSELECTED'
                row.operator("uv.snap_cursor", text="", icon="CURSOR_TO_PIXELS").target = 'PIXELS'
                row.operator("uv.snap_cursor", text="", icon="CURSORTOSELECTION").target = 'SELECTED'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("uv.snap_selected", text="", icon="SNAP_TO_PIXELS").target = 'PIXELS'
                row.operator("uv.snap_selected", text="", icon="SELECTIONTOCURSOR").target = 'CURSOR'

                row = col.row(align=True)
                row.operator("uv.snap_selected", text="", icon="SELECTIONTOCURSOROFFSET").target = 'CURSOR_OFFSET'
                row.operator("uv.snap_selected", text="", icon="SNAP_TO_ADJACENT").target = 'ADJACENT_UNSELECTED'

                row = col.row(align=True)
                row.operator("uv.snap_cursor", text="", icon="CURSOR_TO_PIXELS").target = 'PIXELS'
                row.operator("uv.snap_cursor", text="", icon="CURSORTOSELECTION").target = 'SELECTED'

            elif column_count == 1:

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("uv.snap_selected", text="", icon="SNAP_TO_PIXELS").target = 'PIXELS'
                col.operator("uv.snap_selected", text="", icon="SELECTIONTOCURSOR").target = 'CURSOR'
                col.operator("uv.snap_selected", text="", icon="SELECTIONTOCURSOROFFSET").target = 'CURSOR_OFFSET'
                col.operator("uv.snap_selected", text="", icon="SNAP_TO_ADJACENT").target = 'ADJACENT_UNSELECTED'

                col.separator()

                col.operator("uv.snap_cursor", text="", icon="CURSOR_TO_PIXELS").target = 'PIXELS'
                col.operator("uv.snap_cursor", text="", icon="CURSORTOSELECTION").target = 'SELECTED'


class IMAGE_PT_uvtab_unwrap(toolshelf_calculate, Panel):
    bl_label = "Unwrap"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("uv.unwrap", text="Unwrap ABF", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
            col.operator("uv.unwrap", text="Unwrap Conformal", icon='UNWRAP_LSCM').method = 'CONFORMAL'

            col.separator()

            col.operator_context = 'INVOKE_DEFAULT'
            col.operator("uv.smart_project", icon="MOD_UVPROJECT")
            col.operator("uv.lightmap_pack", icon="LIGHTMAPPACK")
            col.operator("uv.follow_active_quads", icon="FOLLOWQUADS")

            col.separator()

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("uv.cube_project", icon="CUBEPROJECT")
            col.operator("uv.cylinder_project", icon="CYLINDERPROJECT")
            col.operator("uv.sphere_project", icon="SPHEREPROJECT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("uv.unwrap", text="", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
                row.operator("uv.unwrap", text="", icon='UNWRAP_LSCM').method = 'CONFORMAL'
                row.operator_context = 'INVOKE_DEFAULT'
                row.operator("uv.smart_project", text="", icon="MOD_UVPROJECT")

                row = col.row(align=True)
                row.operator("uv.lightmap_pack", text="", icon="LIGHTMAPPACK")
                row.operator("uv.follow_active_quads", text="", icon="FOLLOWQUADS")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("uv.cube_project", text="", icon="CUBEPROJECT")

                row = col.row(align=True)
                row.operator("uv.cylinder_project", text="", icon="CYLINDERPROJECT")
                row.operator("uv.sphere_project", text="", icon="SPHEREPROJECT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("uv.unwrap", text="", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
                row.operator("uv.unwrap", text="", icon='UNWRAP_LSCM').method = 'CONFORMAL'

                row = col.row(align=True)
                row.operator_context = 'INVOKE_DEFAULT'
                row.operator("uv.smart_project", text="", icon="MOD_UVPROJECT")
                row.operator("uv.lightmap_pack", text="", icon="LIGHTMAPPACK")

                row = col.row(align=True)
                row.operator("uv.follow_active_quads", text="", icon="FOLLOWQUADS")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("uv.cube_project", text="", icon="CUBEPROJECT")

                row = col.row(align=True)
                row.operator("uv.cylinder_project", text="", icon="CYLINDERPROJECT")
                row.operator("uv.sphere_project", text="", icon="SPHEREPROJECT")

            elif column_count == 1:

                col.operator("uv.unwrap", text="", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
                col.operator("uv.unwrap", text="", icon='UNWRAP_LSCM').method = 'CONFORMAL'

                col.separator()

                col.operator_context = 'INVOKE_DEFAULT'
                col.operator("uv.smart_project", text="", icon="MOD_UVPROJECT")
                col.operator("uv.lightmap_pack", text="", icon="LIGHTMAPPACK")
                col.operator("uv.follow_active_quads", text="", icon="FOLLOWQUADS")

                col.separator()

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("uv.cube_project", text="", icon="CUBEPROJECT")
                col.operator("uv.cylinder_project", text="", icon="CYLINDERPROJECT")
                col.operator("uv.sphere_project", text="", icon="SPHEREPROJECT")


class IMAGE_PT_uvtab_merge(toolshelf_calculate, Panel):
    bl_label = "Merge"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("uv.weld", text="At Center", icon='MERGE_CENTER')
            col.operator("uv.snap_selected", text="At Cursor", icon='MERGE_CURSOR').target = 'CURSOR'

            col.separator()

            col.operator("uv.remove_doubles", text="By Distance", icon='REMOVE_DOUBLES')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("uv.weld", text="", icon='MERGE_CENTER')
                row.operator("uv.snap_selected", text="", icon='MERGE_CURSOR').target = 'CURSOR'
                row.operator("uv.remove_doubles", text="", icon='REMOVE_DOUBLES')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("uv.weld", text="", icon='MERGE_CENTER')
                row.operator("uv.snap_selected", text="", icon='MERGE_CURSOR').target = 'CURSOR'

                row = col.row(align=True)
                row.operator("uv.remove_doubles", text="", icon='REMOVE_DOUBLES')

            elif column_count == 1:

                col.operator("uv.weld", text="", icon='MERGE_CENTER')
                col.operator("uv.snap_selected", text="", icon='MERGE_CURSOR').target = 'CURSOR'

                col.separator()

                col.operator("uv.remove_doubles", text="", icon='REMOVE_DOUBLES')


class IMAGE_PT_uvtab_uvtools(toolshelf_calculate, Panel):
    bl_label = "UV Tools"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("uv.pin", icon="PINNED").clear = False
            col.operator("uv.pin", text="Unpin", icon="UNPINNED").clear = True
            col.operator("uv.select_split", text="Split Selection", icon='SPLIT')

            col.separator()

            col.operator("uv.pack_islands", icon="PACKISLAND")
            col.operator("uv.average_islands_scale", icon="AVERAGEISLANDSCALE")
            col.operator("uv.minimize_stretch", icon="MINIMIZESTRETCH")
            col.operator("uv.stitch", icon="STITCH")

            col.separator()

            col.operator("uv.mark_seam", icon="MARK_SEAM").clear = False
            col.operator("uv.clear_seam", text="Clear Seam", icon='CLEAR_SEAM')
            col.operator("uv.seams_from_islands", icon="SEAMSFROMISLAND")

            col.separator()

            col.operator("uv.reset", icon="RESET")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("uv.pin", text="", icon="PINNED").clear = False
                row.operator("uv.pin", text="", icon="UNPINNED").clear = True
                row.operator("uv.select_split", text="", icon='SPLIT')

                row = col.row(align=True)
                row.operator("uv.pack_islands", text="", icon="PACKISLAND")
                row.operator("uv.average_islands_scale", text="", icon="AVERAGEISLANDSCALE")
                row.operator("uv.minimize_stretch", text="", icon="MINIMIZESTRETCH")

                row = col.row(align=True)
                row.operator("uv.stitch", text="", icon="STITCH")
                row.operator("uv.mark_seam", text="", icon="MARK_SEAM").clear = False
                row.operator("uv.clear_seam", text="", icon='CLEAR_SEAM')

                row = col.row(align=True)
                row.operator("uv.seams_from_islands", text="", icon="SEAMSFROMISLAND")
                row.operator("uv.reset", text="", icon="RESET")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("uv.pin", text="", icon="PINNED").clear = False
                row.operator("uv.pin", text="", icon="UNPINNED").clear = True

                row = col.row(align=True)
                row.operator("uv.select_split", text="", icon='SPLIT')
                row.operator("uv.pack_islands", text="", icon="PACKISLAND")

                row = col.row(align=True)
                row.operator("uv.average_islands_scale", text="", icon="AVERAGEISLANDSCALE")
                row.operator("uv.minimize_stretch", text="", icon="MINIMIZESTRETCH")

                row = col.row(align=True)
                row.operator("uv.stitch", text="", icon="STITCH")
                row.operator("uv.mark_seam", text="", icon="MARK_SEAM").clear = False

                row = col.row(align=True)
                row.operator("uv.clear_seam", text="", icon='CLEAR_SEAM')
                row.operator("uv.seams_from_islands", text="", icon="SEAMSFROMISLAND")
                row = col.row(align=True)
                row.operator("uv.reset", text="", icon="RESET")

            elif column_count == 1:

                col.operator("uv.pin", text="", icon="PINNED").clear = False
                col.operator("uv.pin", text="", icon="UNPINNED").clear = True
                col.operator("uv.select_split", text="", icon='SPLIT')

                col.separator()

                col.operator("uv.pack_islands", text="", icon="PACKISLAND")
                col.operator("uv.average_islands_scale", text="", icon="AVERAGEISLANDSCALE")
                col.operator("uv.minimize_stretch", text="", icon="MINIMIZESTRETCH")
                col.operator("uv.stitch", text="", icon="STITCH")

                col.separator()

                col.operator("uv.mark_seam", text="", icon="MARK_SEAM").clear = False
                col.operator("uv.clear_seam", text="", icon='CLEAR_SEAM')
                col.operator("uv.seams_from_islands", text="", icon="SEAMSFROMISLAND")

                col.separator()

                col.operator("uv.reset", text="", icon="RESET")


class IMAGE_PT_uvtab_align(toolshelf_calculate, Panel):
    bl_label = "Align"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        view = context.space_data
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        # overlay = view.overlay
        # return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.uv_show_toolshelf_tabs and show_uvedit == True and sima.mode == 'UV'

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y=1.75)

        obj = context.object

        # text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("uv.align", text="Straighten", icon="ALIGN").axis = 'ALIGN_S'
            col.operator("uv.align", text="Straighten X", icon="STRAIGHTEN_X").axis = 'ALIGN_T'
            col.operator("uv.align", text="Straighten Y", icon="STRAIGHTEN_Y").axis = 'ALIGN_U'
            col.operator("uv.align", text="Align Auto", icon="ALIGNAUTO").axis = 'ALIGN_AUTO'
            col.operator("uv.align", text="Align X", icon="ALIGNHORIZONTAL").axis = 'ALIGN_X'
            col.operator("uv.align", text="Align Y", icon="ALIGNVERTICAL").axis = 'ALIGN_Y'
            col.operator("uv.align_rotation", text="Align Rotation", icon="DRIVER_ROTATIONAL_DIFFERENCE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("uv.align", text="", icon="ALIGN").axis = 'ALIGN_S'
                row.operator("uv.align", text="", icon="STRAIGHTEN_X").axis = 'ALIGN_T'
                row.operator("uv.align", text="", icon="STRAIGHTEN_Y").axis = 'ALIGN_U'

                row = col.row(align=True)
                row.operator("uv.align", text="", icon="ALIGNAUTO").axis = 'ALIGN_AUTO'
                row.operator("uv.align", text="", icon="ALIGNHORIZONTAL").axis = 'ALIGN_X'
                row.operator("uv.align", text="", icon="ALIGNVERTICAL").axis = 'ALIGN_Y'

                row = col.row(align=True)
                row.operator("uv.align_rotation", text="", icon="DRIVER_ROTATIONAL_DIFFERENCE")
                row.label(text="")
                row.label(text="")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("uv.align", text="", icon="ALIGN").axis = 'ALIGN_S'
                row.operator("uv.align", text="", icon="STRAIGHTEN_X").axis = 'ALIGN_T'

                row = col.row(align=True)
                row.operator("uv.align", text="", icon="STRAIGHTEN_Y").axis = 'ALIGN_U'
                row.operator("uv.align", text="", icon="ALIGNAUTO").axis = 'ALIGN_AUTO'

                row = col.row(align=True)
                row.operator("uv.align", text="", icon="ALIGNHORIZONTAL").axis = 'ALIGN_X'
                row.operator("uv.align", text="", icon="ALIGNVERTICAL").axis = 'ALIGN_Y'

                row = col.row(align=True)
                row.operator("uv.align_rotation", text="", icon="DRIVER_ROTATIONAL_DIFFERENCE")
                row.label(text="")

            elif column_count == 1:

                col.operator("uv.align", text="", icon="ALIGN").axis = 'ALIGN_S'
                col.operator("uv.align", text="", icon="STRAIGHTEN_X").axis = 'ALIGN_T'
                col.operator("uv.align", text="", icon="STRAIGHTEN_Y").axis = 'ALIGN_U'
                col.operator("uv.align", text="", icon="ALIGNAUTO").axis = 'ALIGN_AUTO'
                col.operator("uv.align", text="", icon="ALIGNHORIZONTAL").axis = 'ALIGN_X'
                col.operator("uv.align", text="", icon="ALIGNVERTICAL").axis = 'ALIGN_Y'
                col.operator("uv.align_rotation", text="", icon="DRIVER_ROTATIONAL_DIFFERENCE")


classes = (

    IMAGE_PT_uvtab_transform,
    IMAGE_PT_uvtab_mirror,
    IMAGE_PT_uvtab_snap,
    IMAGE_PT_uvtab_unwrap,
    IMAGE_PT_uvtab_merge,
    IMAGE_PT_uvtab_uvtools,
    IMAGE_PT_uvtab_align,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
