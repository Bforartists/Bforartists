# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import bpy
import math
from bpy.types import Header, Menu, Panel
from .properties_paint_common import (
    UnifiedPaintPanel,
    brush_texture_settings,
    brush_texpaint_common,
    brush_mask_texture_settings,
)
from .properties_grease_pencil_common import (
    GreasePencilDrawingToolsPanel,
    GreasePencilStrokeEditPanel,
    GreasePencilStrokeSculptPanel,
    GreasePencilBrushPanel,
    GreasePencilBrushCurvesPanel,
    GreasePencilDataPanel,
    GreasePencilPaletteColorPanel,
)
from bpy.app.translations import pgettext_iface as iface_


class ImagePaintPanel(UnifiedPaintPanel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'


class BrushButtonsPanel(UnifiedPaintPanel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        toolsettings = context.tool_settings.image_paint
        return sima.show_paint and toolsettings.brush


class UVToolsPanel:
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Tools"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and not context.tool_settings.use_uv_sculpt


# Workaround to separate the tooltips for Toggle Maximize Area
class IMAGE_MT_view_view_fit(bpy.types.Operator):
    """View Fit\nFits the content area into the window"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "image.view_all_fit"        # unique identifier for buttons and menu items to reference.
    bl_label = "View Fit"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.image.view_all(fit_view = True)
        return {'FINISHED'}  


class IMAGE_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        uv = sima.uv_editor

        show_uvedit = sima.show_uvedit
        show_render = sima.show_render

        layout.operator("image.properties", icon='MENU_PANEL')
        layout.operator("image.toolshelf", icon='MENU_PANEL')

        layout.separator()

        layout.operator("image.view_zoom_in", icon = "ZOOM_IN")
        layout.operator("image.view_zoom_out", icon = "ZOOM_OUT")

        layout.separator()

        ratios = ((1, 8), (1, 4), (1, 2), (1, 1), (2, 1), (4, 1), (8, 1))

        for a, b in ratios:
            layout.operator("image.view_zoom_ratio", text=iface_("Zoom %d:%d") % (a, b), translate=False, icon = "ZOOM_SET").ratio = a / b

        layout.separator()

        if show_uvedit:
            layout.operator("image.view_selected", icon = "VIEW_SELECTED")

        layout.operator("image.view_all", icon = "VIEWALL" )
        layout.operator("image.view_all_fit", text="View Fit", icon = "VIEW_FIT")

        layout.separator()

        if show_render:
            layout.operator("image.render_border", icon = "RENDERBORDER")
            layout.operator("image.clear_render_border", icon = "RENDERBORDER_CLEAR")

            layout.separator()

            layout.operator("image.cycle_render_slot", text="Render Slot Cycle Next", icon = "FRAME_NEXT")
            layout.operator("image.cycle_render_slot", text="Render Slot Cycle Previous", icon = "FRAME_PREV").reverse = True

            layout.separator()

        layout.operator("screen.area_dupli", icon = "NEW_WINDOW")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area", icon = "MAXIMIZE_AREA") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area", icon = "FULLSCREEN_AREA").use_hide_panels = True


# Workaround to separate the tooltips
class IMAGE_MT_select_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_all(action = 'INVERT')
        return {'FINISHED'}  

# Workaround to separate the tooltips
class IMAGE_MT_select_linked_pick_extend(bpy.types.Operator):
    """Linked Pick Extend\nSelect all UV vertices under the mouse with extend method\nHotkey Only tool! """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_linked_pick_extend"        # unique identifier for buttons and menu items to reference.
    bl_label = "Linked Pick Extend"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_linked_pick(extend = True)
        return {'FINISHED'} 

# Workaround to separate the tooltips
class IMAGE_MT_select_linked_extend(bpy.types.Operator):
    """Linked Extend\nSelect all UV vertices linked to the active keymap extended"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_linked_extend"        # unique identifier for buttons and menu items to reference.
    bl_label = "Linked Extend"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_linked(extend = True)
        return {'FINISHED'} 


class IMAGE_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("uv.select_border", text = "Border Select", icon='BORDER_RECT').pinned = False
        layout.operator("uv.select_border", text="Border Select Pinned", icon='BORDER_RECT').pinned = True
        layout.operator("uv.circle_select", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("uv.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("uv.select_all_inverse", text="Inverse", icon = 'INVERSE')

        layout.separator()
     
        layout.operator("uv.select_linked", text="Linked", icon = "LINKED").extend = False
        layout.operator("uv.select_linked_extend", text="Linked Extend", icon = "LINKED")
        layout.operator("uv.select_linked_pick", text="Linked Pick", icon = "LINKED").extend = False
        layout.operator("uv.select_linked_pick_extend", text="Linked Pick Extend", icon = "LINKED")

        layout.separator()

        layout.operator("uv.select_pinned", text = "Pinned", icon = "PINNED")
        layout.operator("uv.select_split",text = "Split", icon = "SPLIT")

        layout.separator()

        layout.operator("uv.select_more", text="More", icon = "SELECTMORE")
        layout.operator("uv.select_less", text="Less", icon = "SELECTLESS")


class IMAGE_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings
        settings = toolsettings.image_paint
        brush = settings.brush

        layout.label(text = "For addons")


class IMAGE_MT_image(Menu):
    bl_label = "Image"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image

        layout.operator("image.new", icon='IMAGE_DATA')
        layout.operator("image.open", icon='FILE_FOLDER')

        show_render = sima.show_render

        layout.operator("image.read_renderlayers", icon = "RENDERLAYERS")

        layout.operator("image.save_dirty", text="Save All Images", icon = "SAVE_ALL")

        if ima:
            if not show_render:
                layout.operator("image.replace", icon='FILE_FOLDER')
                layout.operator("image.reload", icon = "FILE_REFRESH")

            layout.operator("image.save", icon='FILE_TICK')
            layout.operator("image.save_as", icon='SAVE_AS')
            layout.operator("image.save_as", text="Save a Copy", icon='SAVE_COPY').copy = True

            if ima.source == 'SEQUENCE':
                layout.operator("image.save_sequence", icon='SAVE_All')

            layout.operator("image.external_edit", "Edit Externally", icon = "EDIT_EXTERNAL")

            layout.separator()

            layout.menu("IMAGE_MT_image_invert")

            if not show_render:
                if not ima.packed_file:
                    layout.separator()
                    layout.operator("image.pack", icon = "PACKAGE")

                # only for dirty && specific image types, perhaps
                # this could be done in operator poll too
                if ima.is_dirty:
                    if ima.source in {'FILE', 'GENERATED'} and ima.type != 'OPEN_EXR_MULTILAYER':
                        if ima.packed_file:
                            layout.separator()
                        layout.operator("image.pack", text="Pack As PNG", icon = "PACKAGE").as_png = True


class IMAGE_MT_image_invert(Menu):
    bl_label = "Invert"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("image.invert", text="Invert Image Colors", icon = "REVERSE_COLORS")
        props.invert_r = True
        props.invert_g = True
        props.invert_b = True

        layout.separator()

        layout.operator("image.invert", text="Invert Red Channel", icon = "REVERSE_RED").invert_r = True
        layout.operator("image.invert", text="Invert Green Channel", icon = "REVERSE_GREEN").invert_g = True
        layout.operator("image.invert", text="Invert Blue Channel", icon = "REVERSE_BLUE").invert_b = True
        layout.operator("image.invert", text="Invert Alpha Channel", icon = "IMAGE_ALPHA").invert_a = True


class IMAGE_MT_uvs_showhide(Menu):
    bl_label = "Show/Hide Faces"

    def draw(self, context):
        layout = self.layout

        layout.operator("uv.reveal", icon = "RESTRICT_VIEW_OFF")
        layout.operator("uv.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("uv.hide", text="Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True

class IMAGE_MT_uvs_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'

        layout.operator("uv.snap_selected", text="Selected to Pixels").target = 'PIXELS'
        layout.operator("uv.snap_selected", text="Selected to Cursor").target = 'CURSOR'
        layout.operator("uv.snap_selected", text="Selected to Cursor (Offset)").target = 'CURSOR_OFFSET'
        layout.operator("uv.snap_selected", text="Selected to Adjacent Unselected").target = 'ADJACENT_UNSELECTED'

        layout.separator()

        layout.operator("uv.snap_cursor", text="Cursor to Pixels").target = 'PIXELS'
        layout.operator("uv.snap_cursor", text="Cursor to Selected").target = 'SELECTED'


class IMAGE_MT_uvs_snap_panel(Panel, UVToolsPanel):
    bl_label = "Snap"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and not context.tool_settings.use_uv_sculpt

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'

        col = layout.column(align=True)

        col.operator("uv.snap_selected", text="Selected to Pixels", icon = "SNAP_TO_PIXELS").target = 'PIXELS'
        col.operator("uv.snap_selected", text="Selected to Cursor", icon = "SELECTIONTOCURSOR").target = 'CURSOR'
        col.operator("uv.snap_selected", text="Selected to Cursor (Offset)", icon = "SELECTIONTOCURSOROFFSET").target = 'CURSOR_OFFSET'
        col.operator("uv.snap_selected", text="Selected to Adjacent Unselected", icon = "SNAP_TO_ADJACENT").target = 'ADJACENT_UNSELECTED'

        col = layout.column(align=True)

        col.operator("uv.snap_cursor", text="Cursor to Pixels", icon = "CURSOR_TO_PIXELS").target = 'PIXELS'
        col.operator("uv.snap_cursor", text="Cursor to Selected", icon = "CURSORTOSELECTION").target = 'SELECTED'

class IMAGE_MT_uvs_weldalign(Menu):
    bl_label = "Weld/Align"

    def draw(self, context):
        layout = self.layout

        layout.operator("uv.weld")  # W, 1
        layout.operator("uv.remove_doubles")
        layout.operator_enum("uv.align", "axis")  # W, 2/3/4



class IMAGE_MT_uvs(Menu):
    bl_label = "UVs"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        uv = sima.uv_editor
        toolsettings = context.tool_settings

        layout.menu("IMAGE_MT_uvs_showhide")

        layout.separator()

        # Export UV layout is an addon


class IMAGE_MT_uvs_select_mode(Menu):
    bl_label = "UV Select Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        toolsettings = context.tool_settings

        # do smart things depending on whether uv_select_sync is on

        if toolsettings.use_uv_select_sync:
            props = layout.operator("wm.context_set_value", text="Vertex", icon='VERTEXSEL')
            props.value = "(True, False, False)"
            props.data_path = "tool_settings.mesh_select_mode"

            props = layout.operator("wm.context_set_value", text="Edge", icon='EDGESEL')
            props.value = "(False, True, False)"
            props.data_path = "tool_settings.mesh_select_mode"

            props = layout.operator("wm.context_set_value", text="Face", icon='FACESEL')
            props.value = "(False, False, True)"
            props.data_path = "tool_settings.mesh_select_mode"

        else:
            props = layout.operator("wm.context_set_string", text="Vertex", icon='UV_VERTEXSEL')
            props.value = 'VERTEX'
            props.data_path = "tool_settings.uv_select_mode"

            props = layout.operator("wm.context_set_string", text="Edge", icon='UV_EDGESEL')
            props.value = 'EDGE'
            props.data_path = "tool_settings.uv_select_mode"

            props = layout.operator("wm.context_set_string", text="Face", icon='UV_FACESEL')
            props.value = 'FACE'
            props.data_path = "tool_settings.uv_select_mode"

            props = layout.operator("wm.context_set_string", text="Island", icon='UV_ISLANDSEL')
            props.value = 'ISLAND'
            props.data_path = "tool_settings.uv_select_mode"


class IMAGE_HT_header(Header):
    bl_space_type = 'IMAGE_EDITOR'

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image
        iuser = sima.image_user
        toolsettings = context.tool_settings
        mode = sima.mode

        show_render = sima.show_render
        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        MASK_MT_editor_menus.draw_collapsible(context, layout)

        layout.template_ID(sima, "image", new="image.new", open="image.open")
        if not show_render:
            layout.prop(sima, "use_image_pin", text="")

        layout.prop(sima, "mode", text="")

        if show_maskedit:
            row = layout.row()
            row.template_ID(sima, "mask", new="mask.new")

        layout.prop(sima, "pivot_point", icon_only=True)

        # uv editing
        if show_uvedit:
            uvedit = sima.uv_editor

            layout.prop(toolsettings, "use_uv_select_sync", text="")

            if toolsettings.use_uv_select_sync:
                layout.template_edit_mode_selection()
            else:
                layout.prop(toolsettings, "uv_select_mode", text="", expand=True)
                layout.prop(uvedit, "sticky_select_mode", icon_only=True)

            row = layout.row(align=True)
            row.prop(toolsettings, "proportional_edit", icon_only=True)
            if toolsettings.proportional_edit != 'DISABLED':
                row.prop(toolsettings, "proportional_edit_falloff", icon_only=True)

            row = layout.row(align=True)
            row.prop(toolsettings, "use_snap", text="")
            row.prop(toolsettings, "snap_uv_element", icon_only=True)
            if toolsettings.snap_uv_element != 'INCREMENT':
                row.prop(toolsettings, "snap_target", text="")

            mesh = context.edit_object.data
            layout.prop_search(mesh.uv_textures, "active", mesh, "uv_textures", text="")

        if ima:
            if ima.is_stereo_3d:
                row = layout.row()
                row.prop(sima, "show_stereo_3d", text="")

            # layers
            layout.template_image_layers(ima, iuser)

            # draw options
            row = layout.row(align=True)
            row.prop(sima, "draw_channels", text="", expand=True)

            row = layout.row(align=True)
            if ima.type == 'COMPOSITE':
                row.operator("image.record_composite", icon='REC')
            if ima.type == 'COMPOSITE' and ima.source in {'MOVIE', 'SEQUENCE'}:
                row.operator("image.play_composite", icon='PLAY')

        if show_uvedit or show_maskedit or mode == 'PAINT':
            layout.prop(sima, "use_realtime_update", icon_only=True, icon='LOCKED')

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class MASK_MT_editor_menus(Menu):
    bl_idname = "MASK_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        sima = context.space_data
        ima = sima.image

        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit

        layout.menu("IMAGE_MT_view")

        if show_uvedit:
            layout.menu("IMAGE_MT_select")
        if show_maskedit:
            layout.menu("MASK_MT_select")

        if ima and ima.is_dirty:
            layout.menu("IMAGE_MT_image", text="Image*")
        else:
            layout.menu("IMAGE_MT_image", text="Image")

        if show_uvedit:
            layout.menu("IMAGE_MT_uvs")
        if show_maskedit:
            layout.menu("MASK_MT_mask")


# -----------------------------------------------------------------------------
# Mask (similar code in space_clip.py, keep in sync)
# note! - panel placement does _not_ fit well with image panels... need to fix

from .properties_mask_common import (
    MASK_PT_mask,
    MASK_PT_layers,
    MASK_PT_spline,
    MASK_PT_point,
    MASK_PT_display,
    MASK_PT_tools,
)


class IMAGE_PT_mask(MASK_PT_mask, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'


class IMAGE_PT_mask_layers(MASK_PT_layers, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'


class IMAGE_PT_mask_display(MASK_PT_display, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'


class IMAGE_PT_active_mask_spline(MASK_PT_spline, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'


class IMAGE_PT_active_mask_point(MASK_PT_point, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'


class IMAGE_PT_tools_mask(MASK_PT_tools, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Mask'


# --- end mask ---


class IMAGE_PT_image_properties(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Image"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima.image)

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        iuser = sima.image_user

        layout.template_image(sima, "image", iuser, multiview=True)


class IMAGE_PT_game_properties(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Game Properties"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        # display even when not in game mode because these settings effect the 3d view
        return (sima and sima.image and not sima.show_maskedit)  # and (rd.engine == 'BLENDER_GAME')

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image

        split = layout.split()
        col = split.column()
        col.prop(ima, "use_animation")
        sub = col.column(align=True)
        sub.active = ima.use_animation
        sub.prop(ima, "frame_start", text="Start")
        sub.prop(ima, "frame_end", text="End")
        sub.prop(ima, "fps", text="Speed")

        col = split.column()
        col.prop(ima, "use_tiles")
        sub = col.column(align=True)
        sub.active = ima.use_tiles or ima.use_animation
        sub.prop(ima, "tiles_x", text="X")
        sub.prop(ima, "tiles_y", text="Y")

        split = layout.split()
        col = split.column()
        col.label(text="Clamp:")
        col.prop(ima, "use_clamp_x", text="X")
        col.prop(ima, "use_clamp_y", text="Y")

        col = split.column()
        col.label(text="Mapping:")
        col.prop(ima, "mapping", expand=True)


class IMAGE_PT_view_properties(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima and (sima.image or sima.show_uvedit))
        

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image

        show_render = sima.show_render
        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit
        uvedit = sima.uv_editor

        toolsettings = context.tool_settings
        paint = toolsettings.image_paint

        split = layout.split()

        col = split.column()
        if ima:
            col.prop(ima, "display_aspect", text="Aspect Ratio")

            col = split.column()
            col.label(text="Coordinates:")
            col.prop(sima, "show_repeat", text="Repeat")
            if show_uvedit:
                col.prop(uvedit, "show_normalized_coords", text="Normalized")

        elif show_uvedit:
            col.label(text="Coordinates:")
            col.prop(uvedit, "show_normalized_coords", text="Normalized")

        if show_uvedit or show_maskedit:
            col = layout.column()
            col.label("Cursor Location:")
            col.row().prop(sima, "cursor_location", text="")

        if show_uvedit:
            col.separator()

            col.label(text="UVs:")
            col.row().prop(uvedit, "edge_draw_type", expand=True)

            split = layout.split()

            col = split.column()
            col.prop(uvedit, "show_faces")
            col.prop(uvedit, "show_smooth_edges", text="Smooth")
            col.prop(uvedit, "show_modified_edges", text="Modified")

            col = split.column()
            col.prop(uvedit, "show_stretch", text="Stretch")
            sub = col.column()
            sub.active = uvedit.show_stretch
            sub.row().prop(uvedit, "draw_stretch_type", expand=True)

            col = layout.column()
            col.prop(uvedit, "show_other_objects")
            row = col.row()
            row.active = uvedit.show_other_objects
            row.prop(uvedit, "other_uv_filter", text="Filter")

        if show_render and ima:
            layout.separator()
            render_slot = ima.render_slots.active
            layout.prop(render_slot, "name", text="Slot Name")

        layout.prop(sima, "use_realtime_update")
        if show_uvedit:
            layout.prop(toolsettings, "show_uv_local_view")

        layout.prop(uvedit, "show_other_objects")
        layout.prop(uvedit, "show_metadata")
        if paint.brush and (context.image_paint_object or sima.mode == 'PAINT'):
            layout.prop(uvedit, "show_texpaint")
            layout.prop(toolsettings, "show_uv_local_view", text="Show Same Material")


class IMAGE_PT_tools_align_uvs(Panel, UVToolsPanel):
    bl_label = "UV Align"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and not context.tool_settings.use_uv_sculpt

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'

        split = layout.split()
        col = split.column(align=True)
        col.operator("transform.mirror", text="Mirror X", icon = "MIRROR_X").constraint_axis[0] = True
        col.operator("transform.mirror", text="Mirror Y", icon = "MIRROR_Y").constraint_axis[1] = True
        col = split.column(align=True)
        col.operator("transform.rotate", text="Rotate +90°", icon = "ROTATE_PLUS_90").value = math.pi / 2
        col.operator("transform.rotate", text="Rotate  - 90°", icon = "ROTATE_MINUS_90").value = math.pi / -2

        split = layout.split()
        col = split.column(align=True)
        col.operator("uv.align", text="Straighten", icon = "STRAIGHTEN").axis = 'ALIGN_S'
        col.operator("uv.align", text="Straighten X", icon = "STRAIGHTEN_X").axis = 'ALIGN_T'
        col.operator("uv.align", text="Straighten Y", icon = "STRAIGHTEN_Y").axis = 'ALIGN_U'
        col = split.column(align=True)
        col.operator("uv.align", text="Align Auto", icon = "ALIGNAUTO").axis = 'ALIGN_AUTO'
        col.operator("uv.align", text="Align X", icon = "ALIGNHORIZONTAL").axis = 'ALIGN_X'
        col.operator("uv.align", text="Align Y", icon = "ALIGNVERTICAL").axis = 'ALIGN_Y'


class IMAGE_PT_tools_uvs(Panel, UVToolsPanel):
    bl_label = "UV Tools"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and not context.tool_settings.use_uv_sculpt

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("uv.weld", icon='WELD')
        row.operator("uv.stitch", icon = "STITCH")
        col.operator("uv.remove_doubles", icon='REMOVE_DOUBLES')
        col.operator("uv.average_islands_scale", icon ="AVERAGEISLANDSCALE")
        col.operator("uv.pack_islands", icon ="PACKISLAND")
        col.operator("mesh.faces_mirror_uv", icon ="COPYMIRRORED")

        col.operator("uv.minimize_stretch", icon = "MINIMIZESTRETCH")

        layout.label(text="UV Unwrap:")
        row = layout.row(align=True)
        row.operator("uv.pin", icon = "PINNED").clear = False
        row.operator("uv.pin", text="Unpin", icon = "UNPINNED").clear = True
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("uv.mark_seam", text="Mark Seam", icon ="MARK_SEAM").clear = False
        row.operator("uv.mark_seam", text="Clear Seam", icon ="CLEAR_SEAM").clear = True
        col.operator("uv.seams_from_islands", text="Mark Seams from Islands", icon ="SEAMSFROMISLAND")
        col.operator("uv.unwrap", text = "Unwrap ABF", icon='UNWRAP_ABF').method='ANGLE_BASED'
        col.operator("uv.unwrap", text = "Unwrap LSCM", icon='UNWRAP_LSCM').method='CONFORMAL'  


class IMAGE_PT_paint(Panel, ImagePaintPanel):
    bl_label = "Paint"
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout

        settings = context.tool_settings.image_paint
        brush = settings.brush

        col = layout.column()
        col.template_ID_preview(settings, "brush", new="brush.add", rows=2, cols=6)

        if brush:
            brush_texpaint_common(self, context, layout, brush, settings)

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_paint


class IMAGE_PT_tools_brush_overlay(BrushButtonsPanel, Panel):
    bl_label = "Overlay"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Options"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush
        tex_slot = brush.texture_slot
        tex_slot_mask = brush.mask_texture_slot

        col = layout.column()

        col.label(text="Curve:")

        row = col.row(align=True)
        if brush.use_cursor_overlay:
            row.prop(brush, "use_cursor_overlay", toggle=True, text="", icon='RESTRICT_VIEW_OFF')
        else:
            row.prop(brush, "use_cursor_overlay", toggle=True, text="", icon='RESTRICT_VIEW_ON')

        sub = row.row(align=True)
        sub.prop(brush, "cursor_overlay_alpha", text="Alpha")
        sub.prop(brush, "use_cursor_overlay_override", toggle=True, text="", icon='BRUSH_DATA')

        col.active = brush.brush_capabilities.has_overlay
        col.label(text="Texture:")
        row = col.row(align=True)
        if tex_slot.map_mode != 'STENCIL':
            if brush.use_primary_overlay:
                row.prop(brush, "use_primary_overlay", toggle=True, text="", icon='RESTRICT_VIEW_OFF')
            else:
                row.prop(brush, "use_primary_overlay", toggle=True, text="", icon='RESTRICT_VIEW_ON')

        sub = row.row(align=True)
        sub.prop(brush, "texture_overlay_alpha", text="Alpha")
        sub.prop(brush, "use_primary_overlay_override", toggle=True, text="", icon='BRUSH_DATA')

        col.label(text="Mask Texture:")

        row = col.row(align=True)
        if tex_slot_mask.map_mode != 'STENCIL':
            if brush.use_secondary_overlay:
                row.prop(brush, "use_secondary_overlay", toggle=True, text="", icon='RESTRICT_VIEW_OFF')
            else:
                row.prop(brush, "use_secondary_overlay", toggle=True, text="", icon='RESTRICT_VIEW_ON')

        sub = row.row(align=True)
        sub.prop(brush, "mask_overlay_alpha", text="Alpha")
        sub.prop(brush, "use_secondary_overlay_override", toggle=True, text="", icon='BRUSH_DATA')


class IMAGE_PT_tools_brush_texture(BrushButtonsPanel, Panel):
    bl_label = "Texture"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush

        col = layout.column()
        col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

        brush_texture_settings(col, brush, 0)


class IMAGE_PT_tools_mask_texture(BrushButtonsPanel, Panel):
    bl_label = "Texture Mask"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.image_paint.brush

        col = layout.column()

        col.template_ID_preview(brush, "mask_texture", new="texture.new", rows=3, cols=8)

        brush_mask_texture_settings(col, brush)


class IMAGE_PT_tools_brush_tool(BrushButtonsPanel, Panel):
    bl_label = "Tool"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Options"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush

        layout.prop(brush, "image_tool", text="")

        row = layout.row(align=True)
        row.prop(brush, "use_paint_sculpt", text="", icon='SCULPTMODE_HLT')
        row.prop(brush, "use_paint_vertex", text="", icon='VPAINT_HLT')
        row.prop(brush, "use_paint_weight", text="", icon='WPAINT_HLT')
        row.prop(brush, "use_paint_image", text="", icon='TPAINT_HLT')


class IMAGE_PT_paint_stroke(BrushButtonsPanel, Panel):
    bl_label = "Paint Stroke"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush

        col = layout.column()

        col.label(text="Stroke Method:")

        col.prop(brush, "stroke_method", text="")

        if brush.use_anchor:
            col.separator()
            col.prop(brush, "use_edge_to_edge", "Edge To Edge")

        if brush.use_airbrush:
            col.separator()
            col.prop(brush, "rate", text="Rate", slider=True)

        if brush.use_space:
            col.separator()
            row = col.row(align=True)
            row.prop(brush, "spacing", text="Spacing")
            row.prop(brush, "use_pressure_spacing", toggle=True, text="")

        if brush.use_line or brush.use_curve:
            col.separator()
            row = col.row(align=True)
            row.prop(brush, "spacing", text="Spacing")

        if brush.use_curve:
            col.separator()
            col.template_ID(brush, "paint_curve", new="paintcurve.new")
            col.operator("paintcurve.draw")

        col = layout.column()
        col.separator()

        row = col.row(align=True)
        row.prop(brush, "use_relative_jitter", icon_only=True)
        if brush.use_relative_jitter:
            row.prop(brush, "jitter", slider=True)
        else:
            row.prop(brush, "jitter_absolute")
        row.prop(brush, "use_pressure_jitter", toggle=True, text="")

        col = layout.column()
        col.separator()

        if brush.brush_capabilities.has_smooth_stroke:
            col.prop(brush, "use_smooth_stroke")

            sub = col.column()
            sub.active = brush.use_smooth_stroke
            sub.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
            sub.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)

            col.separator()

        col.prop(toolsettings, "input_samples")


class IMAGE_PT_paint_curve(BrushButtonsPanel, Panel):
    bl_label = "Paint Curve"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush

        layout.template_curve_mapping(brush, "curve")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
        row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
        row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
        row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
        row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'


class IMAGE_PT_tools_imagepaint_symmetry(BrushButtonsPanel, Panel):
    bl_category = "Tools"
    bl_context = "imagepaint"
    bl_label = "Tiling"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        ipaint = toolsettings.image_paint

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(ipaint, "tile_x", text="X", toggle=True)
        row.prop(ipaint, "tile_y", text="Y", toggle=True)


class IMAGE_PT_tools_brush_appearance(BrushButtonsPanel, Panel):
    bl_label = "Appearance"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Options"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush

        if brush is None:  # unlikely but can happen
            layout.label(text="Brush Unset")
            return

        col = layout.column(align=True)

        col.prop(toolsettings, "show_brush")
        sub = col.column()
        sub.active = toolsettings.show_brush
        sub.prop(brush, "cursor_color_add", text="")

        col.separator()

        col.prop(brush, "use_custom_icon")
        sub = col.column()
        sub.active = brush.use_custom_icon
        sub.prop(brush, "icon_filepath", text="")


class IMAGE_PT_tools_paint_options(BrushButtonsPanel, Panel):
    bl_label = "Image Paint"
    bl_category = "Options"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        # brush = toolsettings.image_paint.brush

        ups = toolsettings.unified_paint_settings

        col = layout.column(align=True)
        col.label(text="Unified Settings:")
        row = col.row()
        row.prop(ups, "use_unified_size", text="Size")
        row.prop(ups, "use_unified_strength", text="Strength")
        col.prop(ups, "use_unified_color", text="Color")


        layout.label(text = "Addons Brush")
        layout.menu("IMAGE_MT_brush")


class IMAGE_PT_uv_sculpt_curve(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "UV Sculpt Curve"
    bl_category = "Tools"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        toolsettings = context.tool_settings.image_paint
        return sima.show_uvedit and context.tool_settings.use_uv_sculpt and not (sima.show_paint and toolsettings.brush)

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        uvsculpt = toolsettings.uv_sculpt
        brush = uvsculpt.brush

        layout.template_curve_mapping(brush, "curve")

        row = layout.row(align=True)
        row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
        row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
        row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
        row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
        row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'


class IMAGE_PT_uv_sculpt(Panel, ImagePaintPanel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Tools"
    bl_label = "UV Sculpt"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        toolsettings = context.tool_settings.image_paint
        return sima.show_uvedit and context.tool_settings.use_uv_sculpt and not (sima.show_paint and toolsettings.brush)

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        uvsculpt = toolsettings.uv_sculpt
        brush = uvsculpt.brush

        if brush:
            col = layout.column()

            row = col.row(align=True)
            self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
            self.prop_unified_size(row, context, brush, "use_pressure_size")

            row = col.row(align=True)
            self.prop_unified_strength(row, context, brush, "strength", slider=True, text="Strength")
            self.prop_unified_strength(row, context, brush, "use_pressure_strength")

        col = layout.column()
        col.prop(toolsettings, "uv_sculpt_lock_borders")
        col.prop(toolsettings, "uv_sculpt_all_islands")

        col.prop(toolsettings, "uv_sculpt_tool")
        if toolsettings.uv_sculpt_tool == 'RELAX':
            col.prop(toolsettings, "uv_relax_method")

        col.prop(uvsculpt, "show_brush")




class IMAGE_PT_options_uvs(Panel, UVToolsPanel):
    bl_label = "UV Options"
    bl_category = "Options"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        uv = sima.uv_editor
        toolsettings = context.tool_settings

        col = layout.column(align=True)
        col.prop(toolsettings, "use_uv_sculpt")
        
        col.separator()
        
        # brush size
        row = col.row(align=True)
        row.label(text = "Brush Size:")
        myvar = row.operator("wm.radial_control", text = "", icon = "BRUSHSIZE")
        myvar.data_path_primary = 'tool_settings.uv_sculpt.brush.size'
        myvar.data_path_secondary = 'tool_settings.unified_paint_settings.size'
        myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
        myvar.rotation_path = 'tool_settings.uv_sculpt.brush.texture_slot.angle'
        myvar.color_path = 'tool_settings.uv_sculpt.brush.cursor_color_add'
        myvar.fill_color_path = ''
        myvar.fill_color_override_path = ''
        myvar.fill_color_override_test_path = ''
        myvar.zoom_path = ''
        myvar.image_id = 'tool_settings.uv_sculpt.brush'
        myvar.secondary_tex = False
        
        #brush strength
        row = col.row(align=True)
        row.label(text = "Brush Strength:")
        myvar = row.operator("wm.radial_control", text = "", icon = "BRUSHSTRENGTH")
        myvar.data_path_primary = 'tool_settings.uv_sculpt.brush.strength'
        myvar.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
        myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
        myvar.rotation_path = 'tool_settings.uv_sculpt.brush.texture_slot.angle'
        myvar.color_path = 'tool_settings.uv_sculpt.brush.cursor_color_add'
        myvar.fill_color_path = ''
        myvar.fill_color_override_path = ''
        myvar.fill_color_override_test_path = ''
        myvar.zoom_path = ''
        myvar.image_id = 'tool_settings.uv_sculpt.brush'
        myvar.secondary_tex = False
        
        
        col.prop(uv, "use_live_unwrap")
        col.prop(uv, "use_snap_to_pixels")
        col.prop(uv, "lock_bounds")


class ImageScopesPanel:
    @classmethod
    def poll(cls, context):
        sima = context.space_data
        if not (sima and sima.image):
            return False
        # scopes are not updated in paint modes, hide
        if sima.mode == 'PAINT':
            return False
        ob = context.active_object
        if ob and ob.mode in {'TEXTURE_PAINT', 'EDIT'}:
            return False
        return True


class IMAGE_PT_view_histogram(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Histogram"
    bl_category = "Scopes"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        hist = sima.scopes.histogram

        layout.template_histogram(sima.scopes, "histogram")
        row = layout.row(align=True)
        row.prop(hist, "mode", expand=True)
        row.prop(hist, "show_line", text="")


class IMAGE_PT_view_waveform(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Waveform"
    bl_category = "Scopes"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data

        layout.template_waveform(sima, "scopes")
        row = layout.split(percentage=0.75)
        row.prop(sima.scopes, "waveform_alpha")
        row.prop(sima.scopes, "waveform_mode", text="")


class IMAGE_PT_view_vectorscope(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Vectorscope"
    bl_category = "Scopes"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        layout.template_vectorscope(sima, "scopes")
        layout.prop(sima.scopes, "vectorscope_alpha")


class IMAGE_PT_sample_line(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Sample Line"
    bl_category = "Scopes"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        hist = sima.sample_histogram

        layout.operator("image.sample_line")
        layout.template_histogram(sima, "sample_histogram")
        row = layout.row(align=True)
        row.prop(hist, "mode", expand=True)
        row.prop(hist, "show_line", text="")


class IMAGE_PT_scope_sample(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Scope Samples"
    bl_category = "Scopes"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data

        row = layout.row()
        row.prop(sima.scopes, "use_full_resolution")
        sub = row.row()
        sub.active = not sima.scopes.use_full_resolution
        sub.prop(sima.scopes, "accuracy")


# Grease Pencil properties
class IMAGE_PT_grease_pencil(GreasePencilDataPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    # NOTE: this is just a wrapper around the generic GP Panel


# Grease Pencil palette colors
class IMAGE_PT_grease_pencil_palettecolor(GreasePencilPaletteColorPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    # NOTE: this is just a wrapper around the generic GP Panel


# Grease Pencil drawing tools
class IMAGE_PT_tools_grease_pencil_draw(GreasePencilDrawingToolsPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'


# Grease Pencil stroke editing tools
class IMAGE_PT_tools_grease_pencil_edit(GreasePencilStrokeEditPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'


# Grease Pencil stroke sculpting tools
class IMAGE_PT_tools_grease_pencil_sculpt(GreasePencilStrokeSculptPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'


# Grease Pencil drawing brushes
class IMAGE_PT_tools_grease_pencil_brush(GreasePencilBrushPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'


# Grease Pencil drawing curves
class IMAGE_PT_tools_grease_pencil_brushcurves(GreasePencilBrushCurvesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'

class IMAGE_PT_tools_transform_uvs(Panel, UVToolsPanel):
    bl_label = "Transform"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and not context.tool_settings.use_uv_sculpt

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        row = col.row(align=False)
        row.alignment = 'LEFT'
        row.operator("transform.translate", icon ='TRANSFORM_MOVE', text = "")
        row.operator("transform.rotate", icon ='TRANSFORM_ROTATE', text = "")
        row.operator("transform.resize", icon ='TRANSFORM_SCALE', text = "")
        row.operator("transform.shear", icon = 'SHEAR', text = "")



classes = (
    IMAGE_MT_view,
    IMAGE_MT_view_view_fit,
    IMAGE_MT_select_inverse,
    IMAGE_MT_select_linked_pick_extend,
    IMAGE_MT_select_linked_extend,
    IMAGE_MT_select,
    IMAGE_MT_brush,
    IMAGE_MT_image,
    IMAGE_MT_image_invert,
    IMAGE_MT_uvs,
    IMAGE_MT_uvs_weldalign,
    IMAGE_MT_uvs_showhide,
    IMAGE_MT_uvs_snap,
    IMAGE_MT_uvs_snap_panel,
    IMAGE_MT_uvs_select_mode,
    IMAGE_HT_header,
    MASK_MT_editor_menus,
    ALL_MT_editormenu,
    IMAGE_PT_mask,
    IMAGE_PT_mask_layers,
    IMAGE_PT_mask_display,
    IMAGE_PT_active_mask_spline,
    IMAGE_PT_active_mask_point,
    IMAGE_PT_image_properties,
    IMAGE_PT_game_properties,
    IMAGE_PT_view_properties,   
    IMAGE_PT_tools_align_uvs,
    IMAGE_PT_tools_uvs,
    IMAGE_PT_options_uvs,
    IMAGE_PT_paint,
    IMAGE_PT_tools_brush_overlay,
    IMAGE_PT_tools_brush_texture,
    IMAGE_PT_tools_mask,
    IMAGE_PT_tools_mask_texture,
    IMAGE_PT_tools_brush_tool,
    IMAGE_PT_paint_stroke,
    IMAGE_PT_paint_curve,
    IMAGE_PT_tools_imagepaint_symmetry,
    IMAGE_PT_tools_brush_appearance,
    IMAGE_PT_tools_paint_options,
    IMAGE_PT_uv_sculpt,
    IMAGE_PT_uv_sculpt_curve,
    IMAGE_PT_view_histogram,
    IMAGE_PT_view_waveform,
    IMAGE_PT_view_vectorscope,
    IMAGE_PT_sample_line,
    IMAGE_PT_scope_sample,
    IMAGE_PT_grease_pencil,
    IMAGE_PT_grease_pencil_palettecolor,
    IMAGE_PT_tools_grease_pencil_draw,
    IMAGE_PT_tools_grease_pencil_edit,
    IMAGE_PT_tools_grease_pencil_sculpt,
    IMAGE_PT_tools_grease_pencil_brush,
    IMAGE_PT_tools_grease_pencil_brushcurves,
    IMAGE_PT_tools_transform_uvs,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
