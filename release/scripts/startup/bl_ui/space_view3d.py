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

# <pep8 compliant>f
import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bl_ui.properties_paint_common import (
    UnifiedPaintPanel,
    brush_basic_texpaint_settings,
)
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
    AnnotationOnionSkin,
    GreasePencilMaterialsPanel,
    GreasePencilVertexcolorPanel,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)
from bpy.app.translations import contexts as i18n_contexts


class VIEW3D_HT_header(Header):
    bl_space_type = 'VIEW_3D'

    @staticmethod
    def draw_xform_template(layout, context):
        obj = context.active_object
        object_mode = 'OBJECT' if obj is None else obj.mode
        has_pose_mode = (
            (object_mode == 'POSE') or
            (object_mode == 'WEIGHT_PAINT' and context.pose_object is not None)
        )

        tool_settings = context.tool_settings

        # Mode & Transform Settings
        scene = context.scene

        # Orientation
        if object_mode in {'OBJECT', 'EDIT', 'EDIT_GPENCIL'} or has_pose_mode:
            orient_slot = scene.transform_orientation_slots[0]
            row = layout.row(align=True)

            row.prop_with_popover(orient_slot, "type", text="", panel="VIEW3D_PT_transform_orientations",)

        # Pivot
        if object_mode in {'OBJECT', 'EDIT', 'EDIT_GPENCIL', 'SCULPT_GPENCIL'} or has_pose_mode:
            layout.prop(tool_settings, "transform_pivot_point", text="", icon_only=True)

        # Snap
        show_snap = False
        if obj is None:
            show_snap = True
        else:
            if (object_mode not in {
                    'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT', 'TEXTURE_PAINT',
                    'PAINT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL', 'VERTEX_GPENCIL'
            }) or has_pose_mode:
                show_snap = True
            else:

                paint_settings = UnifiedPaintPanel.paint_settings(context)

                if paint_settings:
                    brush = paint_settings.brush
                    if brush and hasattr(brush, "stroke_method") and brush.stroke_method == 'CURVE':
                        show_snap = True
        if show_snap:
            snap_items = bpy.types.ToolSettings.bl_rna.properties["snap_elements"].enum_items
            snap_elements = tool_settings.snap_elements
            if len(snap_elements) == 1:
                text = ""
                for elem in snap_elements:
                    icon = snap_items[elem].icon
                    break
            else:
                text = "Mix"
                icon = 'NONE'
            del snap_items, snap_elements

            row = layout.row(align=True)
            row.prop(tool_settings, "use_snap", text="")

            sub = row.row(align=True)
            sub.popover(
                panel="VIEW3D_PT_snapping",
                icon=icon,
                text=text,
            )

        # Proportional editing
        if object_mode in {'EDIT', 'PARTICLE_EDIT', 'SCULPT_GPENCIL', 'EDIT_GPENCIL', 'OBJECT'}:
            row = layout.row(align=True)
            kw = {}
            if object_mode == 'OBJECT':
                attr = "use_proportional_edit_objects"
            else:
                attr = "use_proportional_edit"

                if tool_settings.use_proportional_edit:
                    if tool_settings.use_proportional_connected:
                        kw["icon"] = 'PROP_CON'
                    elif tool_settings.use_proportional_projected:
                        kw["icon"] = 'PROP_PROJECTED'
                    else:
                        kw["icon"] = 'PROP_ON'
                else:
                    kw["icon"] = 'PROP_OFF'

            row.prop(tool_settings, attr, icon_only=True, **kw) # proportional editing button

            # We can have the proportional editing on in the editing modes but off in object mode and vice versa.
            # So two separated lines to display the settings, just when it is on.

            # proportional editing settings, editing modes
            if object_mode != 'OBJECT' and tool_settings.use_proportional_edit is True:
                sub = row.row(align=True)
                sub.prop_with_popover(tool_settings,"proportional_edit_falloff",text="", icon_only=True, panel="VIEW3D_PT_proportional_edit")

            # proportional editing settings, just in object mode
            if object_mode == 'OBJECT' and tool_settings.use_proportional_edit_objects is True:
                sub = row.row(align=True)
                sub.prop_with_popover(tool_settings,"proportional_edit_falloff",text="", icon_only=True, panel="VIEW3D_PT_proportional_edit")


    def draw(self, context):
        layout = self.layout

        view = context.space_data
        shading = view.shading
        overlay = view.overlay
        tool_settings = context.tool_settings

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        show_region_tool_header = view.show_region_tool_header

        obj = context.active_object
        # mode_string = context.mode
        object_mode = 'OBJECT' if obj is None else obj.mode
        has_pose_mode = (
            (object_mode == 'POSE') or
            (object_mode == 'WEIGHT_PAINT' and context.pose_object is not None)
        )

        # Note: This is actually deadly in case enum_items have to be dynamically generated
        #       (because internal RNA array iterator will free everything immediately...).
        # XXX This is an RNA internal issue, not sure how to fix it.
        # Note: Tried to add an accessor to get translated UI strings instead of manual call
        #       to pgettext_iface below, but this fails because translated enumitems
        #       are always dynamically allocated.
        act_mode_item = bpy.types.Object.bl_rna.properties["mode"].enum_items[object_mode]
        act_mode_i18n_context = bpy.types.Object.bl_rna.properties["mode"].translation_context

        row = layout.row(align=True)
        row.separator()

        sub = row.row()
        #sub.ui_units_x = 5.5 # width of mode edit box
        sub.operator_menu_enum("object.mode_set", "mode", text=act_mode_item.name, icon=act_mode_item.icon)
        del act_mode_item

        layout.template_header_3D_mode()

        # Contains buttons like Mode, Pivot, Layer, Mesh Select Mode
        if obj:
            # Particle edit
            if object_mode == 'PARTICLE_EDIT':
                row = layout.row()
                row.prop(tool_settings.particle_edit, "select_mode", text="", expand=True)

        # Grease Pencil
        if obj and obj.type == 'GPENCIL' and context.gpencil_data:
            gpd = context.gpencil_data

            if gpd.is_stroke_paint_mode:
                row = layout.row()
                sub = row.row(align=True)
                sub.prop(tool_settings, "use_gpencil_draw_onback", text="", icon='MOD_OPACITY')
                sub.separator(factor=0.4)
                sub.prop(tool_settings, "use_gpencil_weight_data_add", text="", icon='WPAINT_HLT')
                sub.separator(factor=0.4)
                sub.prop(tool_settings, "use_gpencil_draw_additive", text="", icon='FREEZE')

            # Select mode for Editing
            if gpd.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(tool_settings, "gpencil_selectmode_edit", text="", expand=True)

            # Select mode for Sculpt
            if gpd.is_stroke_sculpt_mode:
                row = layout.row(align=True)
                row.prop(tool_settings, "use_gpencil_select_mask_point", text="")
                row.prop(tool_settings, "use_gpencil_select_mask_stroke", text="")
                row.prop(tool_settings, "use_gpencil_select_mask_segment", text="")

            # Select mode for Vertex Paint
            if gpd.is_stroke_vertex_mode:
                row = layout.row(align=True)
                row.prop(tool_settings, "use_gpencil_vertex_select_mask_point", text="")
                row.prop(tool_settings, "use_gpencil_vertex_select_mask_stroke", text="")
                row.prop(tool_settings, "use_gpencil_vertex_select_mask_segment", text="")

            if (
                    gpd.use_stroke_edit_mode or
                    gpd.is_stroke_sculpt_mode or
                    gpd.is_stroke_weight_mode or
                    gpd.is_stroke_vertex_mode
            ):
                row = layout.row(align=True)

                row.prop(gpd, "use_multiedit", text="", icon='GP_MULTIFRAME_EDITING')

                if gpd.use_multiedit:
                    sub = row.row(align=True)
                    sub.popover(panel="VIEW3D_PT_gpencil_multi_frame", text="")

            if gpd.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.popover(
                    panel="VIEW3D_PT_tools_grease_pencil_interpolate",
                    text="Interpolate"
                )
        VIEW3D_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        if object_mode in {'PAINT_GPENCIL', 'SCULPT_GPENCIL'}:
            # Grease pencil
            if object_mode == 'PAINT_GPENCIL':
                layout.prop_with_popover(
                    tool_settings,
                    "gpencil_stroke_placement_view3d",
                    text="",
                    panel="VIEW3D_PT_gpencil_origin",
                )

            if object_mode in {'PAINT_GPENCIL', 'SCULPT_GPENCIL'}:
                layout.prop_with_popover(
                    tool_settings.gpencil_sculpt,
                    "lock_axis",
                    text="",
                    panel="VIEW3D_PT_gpencil_lock",
                )

            if object_mode == 'PAINT_GPENCIL':
                # FIXME: this is bad practice!
                # Tool options are to be displayed in the topbar.
                if context.workspace.tools.from_space_view3d_mode(object_mode).idname == "builtin_brush.Draw":
                    settings = tool_settings.gpencil_sculpt.guide
                    row = layout.row(align=True)
                    row.prop(settings, "use_guide", text="", icon='GRID')
                    sub = row.row(align=True)
                    sub.active = settings.use_guide
                    sub.popover(
                        panel="VIEW3D_PT_gpencil_guide",
                        text="Guides",
                    )

        elif not show_region_tool_header:
            # Transform settings depending on tool header visibility
            VIEW3D_HT_header.draw_xform_template(layout, context)

        # Mode & Transform Settings
        scene = context.scene

        # Collection Visibility
        # layout.popover(panel="VIEW3D_PT_collections", icon='GROUP', text="")

        # Viewport Settings
        if context.space_data.region_3d.view_perspective == "CAMERA":
            layout.prop(view, "lock_camera", icon = "LOCK_TO_CAMVIEW", icon_only=True )
        layout.popover(panel = "VIEW3D_PT_object_type_visibility", icon_value = view.icon_from_show_object_viewport, text="")


        # Gizmo toggle & popover.
        row = layout.row(align=True)
        # FIXME: place-holder icon.
        row.prop(view, "show_gizmo", text="", toggle=True, icon='GIZMO')
        sub = row.row(align=True)
        sub.active = view.show_gizmo
        sub.popover(
            panel="VIEW3D_PT_gizmo_display",
            text="",
        )

        # Overlay toggle & popover.
        row = layout.row(align=True)
        row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
        sub = row.row(align=True)
        sub.active = overlay.show_overlays
        sub.popover(panel="VIEW3D_PT_overlay", text="")

        row = layout.row()
        row.active = (object_mode == 'EDIT') or (shading.type in {'WIREFRAME', 'SOLID'})

        # While exposing 'shading.show_xray(_wireframe)' is correct.
        # this hides the key shortcut from users: T70433.
        if has_pose_mode:
            draw_depressed = overlay.show_xray_bone
        elif shading.type == 'WIREFRAME':
            draw_depressed = shading.show_xray_wireframe
        else:
            draw_depressed = shading.show_xray
        row.operator(
            "view3d.toggle_xray",
            text="",
            icon='XRAY',
            depress=draw_depressed,
        )

        row = layout.row(align=True)
        row.prop(shading, "type", text="", expand=True)
        sub = row.row(align=True)
        # TODO, currently render shading type ignores mesh two-side, until it's supported
        # show the shading popover which shows double-sided option.

        # sub.enabled = shading.type != 'RENDERED'
        sub.popover(panel="VIEW3D_PT_shading", text="")

class VIEW3D_HT_tool_header(Header):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOL_HEADER'

    def draw(self, context):
        layout = self.layout

        # mode_string = context.mode
        obj = context.active_object
        tool_settings = context.tool_settings

        self.draw_tool_settings(context)

        layout.separator_spacer()

        VIEW3D_HT_header.draw_xform_template(layout, context)

        self.draw_mode_settings(context)

    def draw_tool_settings(self, context):
        layout = self.layout
        tool_mode = context.mode

        # Active Tool
        # -----------
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        tool = ToolSelectPanelHelper.draw_active_tool_header(
            context, layout,
            tool_key=('VIEW_3D', tool_mode),
        )

        # Object Mode Options
        # -------------------

        # Example of how tool_settings can be accessed as pop-overs.

        # TODO(campbell): editing options should be after active tool options
        # (obviously separated for from the users POV)
        draw_fn = getattr(_draw_tool_settings_context_mode, tool_mode, None)
        if draw_fn is not None:
            is_valid_context = draw_fn(context, layout, tool)

        def draw_3d_brush_settings(layout, tool_mode):
            layout.popover("VIEW3D_PT_tools_brush_settings_advanced", text="Brush")
            if tool_mode != 'PAINT_WEIGHT':
                layout.popover("VIEW3D_PT_tools_brush_texture")
            if tool_mode == 'PAINT_TEXTURE':
                layout.popover("VIEW3D_PT_tools_mask_texture")
            layout.popover("VIEW3D_PT_tools_brush_stroke")
            layout.popover("VIEW3D_PT_tools_brush_falloff")
            layout.popover("VIEW3D_PT_tools_brush_display")

        # Note: general mode options should be added to 'draw_mode_settings'.
        if tool_mode == 'SCULPT':
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == 'PAINT_VERTEX':
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == 'PAINT_WEIGHT':
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == 'PAINT_TEXTURE':
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == 'EDIT_ARMATURE':
            pass
        elif tool_mode == 'EDIT_CURVE':
            pass
        elif tool_mode == 'EDIT_MESH':
            pass
        elif tool_mode == 'POSE':
            pass
        elif tool_mode == 'PARTICLE':
            # Disable, only shows "Brush" panel, which is already in the top-bar.
            # if tool.has_datablock:
            #     layout.popover_group(context=".paint_common", **popover_kw)
            pass
        elif tool_mode == 'PAINT_GPENCIL':
            if is_valid_context:
                brush = context.tool_settings.gpencil_paint.brush
                if brush.gpencil_tool != 'ERASE':
                    if brush.gpencil_tool != 'TINT':
                        layout.popover("VIEW3D_PT_tools_grease_pencil_brush_advanced")

                    if brush.gpencil_tool not in {'FILL', 'TINT'}:
                        layout.popover("VIEW3D_PT_tools_grease_pencil_brush_stroke")

                    layout.popover("VIEW3D_PT_tools_grease_pencil_paint_appearance")
        elif tool_mode == 'SCULPT_GPENCIL':
            if is_valid_context:
                brush = context.tool_settings.gpencil_sculpt_paint.brush
                tool = brush.gpencil_tool
                if tool in ('SMOOTH', 'RANDOMIZE'):
                    layout.popover("VIEW3D_PT_tools_grease_pencil_sculpt_options")
                layout.popover("VIEW3D_PT_tools_grease_pencil_sculpt_appearance")
        elif tool_mode == 'WEIGHT_GPENCIL':
            if is_valid_context:
                layout.popover("VIEW3D_PT_tools_grease_pencil_weight_appearance")
        elif tool_mode == 'VERTEX_GPENCIL':
            if is_valid_context:
                layout.popover("VIEW3D_PT_tools_grease_pencil_vertex_appearance")

    def draw_mode_settings(self, context):
        layout = self.layout
        mode_string = context.mode

        def row_for_mirror():
            row = layout.row(align=True)
            #row.label(icon='MOD_MIRROR')
            sub = row.row(align=True)
            sub.scale_x = 0.6
            return row, sub

        if mode_string == 'EDIT_MESH':
            _row, sub = row_for_mirror()
            sub.prop(context.object.data, "use_mirror_x", text="    ", icon='MIRROR_X', toggle=True)
            sub.prop(context.object.data, "use_mirror_y", text="    ", icon='MIRROR_Y', toggle=True)
            sub.prop(context.object.data, "use_mirror_z", text="    ", icon='MIRROR_Z', toggle=True)
            tool_settings = context.tool_settings
            layout.prop(tool_settings, "use_mesh_automerge", text="")
        elif mode_string == 'EDIT_ARMATURE':
            _row, sub = row_for_mirror()
            sub.prop(context.object.data, "use_mirror_x", text="    ", icon='MIRROR_X', toggle=True)
        elif mode_string == 'POSE':
            _row, sub = row_for_mirror()
            sub.prop(context.object.pose, "use_mirror_x", text="    ", icon='MIRROR_X', toggle=True)
        elif mode_string == 'PAINT_WEIGHT':
            row, sub = row_for_mirror()
            wpaint = context.tool_settings.weight_paint
            sub.prop(wpaint, "use_symmetry_x", text="    ", icon='MIRROR_X', toggle=True)
            sub.prop(wpaint, "use_symmetry_y", text="    ", icon='MIRROR_Y', toggle=True)
            sub.prop(wpaint, "use_symmetry_z", text="    ", icon='MIRROR_Z', toggle=True)
            row.popover(panel="VIEW3D_PT_tools_weightpaint_symmetry_for_topbar", text="")
        elif mode_string == 'SCULPT':
            row, sub = row_for_mirror()
            sculpt = context.tool_settings.sculpt
            sub.prop(sculpt, "use_symmetry_x", text="    ", icon='MIRROR_X', toggle=True)
            sub.prop(sculpt, "use_symmetry_y", text="    ", icon='MIRROR_Y', toggle=True)
            sub.prop(sculpt, "use_symmetry_z", text="    ", icon='MIRROR_Z', toggle=True)
            row.popover(panel="VIEW3D_PT_sculpt_symmetry_for_topbar", text="")
        elif mode_string == 'PAINT_TEXTURE':
            _row, sub = row_for_mirror()
            ipaint = context.tool_settings.image_paint
            sub.prop(ipaint, "use_symmetry_x", text="    ", icon='MIRROR_X', toggle=True)
            sub.prop(ipaint, "use_symmetry_y", text="    ", icon='MIRROR_Y', toggle=True)
            sub.prop(ipaint, "use_symmetry_z", text="    ", icon='MIRROR_Z', toggle=True)
            # No need for a popover, the panel only has these options.
        elif mode_string == 'PAINT_VERTEX':
            row, sub = row_for_mirror()
            vpaint = context.tool_settings.vertex_paint
            sub.prop(vpaint, "use_symmetry_x", text="    ", icon='MIRROR_X', toggle=True)
            sub.prop(vpaint, "use_symmetry_y", text="    ", icon='MIRROR_Y', toggle=True)
            sub.prop(vpaint, "use_symmetry_z", text="    ", icon='MIRROR_Z', toggle=True)
            row.popover(panel="VIEW3D_PT_tools_vertexpaint_symmetry_for_topbar", text="")

        # Expand panels from the side-bar as popovers.
        popover_kw = {"space_type": 'VIEW_3D', "region_type": 'UI', "category": "Tool"}

        if mode_string == 'SCULPT':
            layout.popover_group(context=".sculpt_mode", **popover_kw)
        elif mode_string == 'PAINT_VERTEX':
            layout.popover_group(context=".vertexpaint", **popover_kw)
        elif mode_string == 'PAINT_WEIGHT':
            layout.popover_group(context=".weightpaint", **popover_kw)
        elif mode_string == 'PAINT_TEXTURE':
            layout.popover_group(context=".imagepaint", **popover_kw)
        elif mode_string == 'EDIT_TEXT':
            layout.popover_group(context=".text_edit", **popover_kw)
        elif mode_string == 'EDIT_ARMATURE':
            layout.popover_group(context=".armature_edit", **popover_kw)
        elif mode_string == 'EDIT_METABALL':
            layout.popover_group(context=".mball_edit", **popover_kw)
        elif mode_string == 'EDIT_LATTICE':
            layout.popover_group(context=".lattice_edit", **popover_kw)
        elif mode_string == 'EDIT_CURVE':
            layout.popover_group(context=".curve_edit", **popover_kw)
        elif mode_string == 'EDIT_MESH':
            layout.popover_group(context=".mesh_edit", **popover_kw)
        elif mode_string == 'POSE':
            layout.popover_group(context=".posemode", **popover_kw)
        elif mode_string == 'PARTICLE':
            layout.popover_group(context=".particlemode", **popover_kw)
        elif mode_string == 'OBJECT':
            layout.popover_group(context=".objectmode", **popover_kw)
        elif mode_string in {'PAINT_GPENCIL', 'EDIT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}:
            # Grease pencil layer.
            gpl = context.active_gpencil_layer
            if gpl and gpl.info is not None:
                text = gpl.info
                maxw = 25
                if len(text) > maxw:
                    text = text[:maxw - 5] + '..' + text[-3:]
            else:
                text = ""

            layout.label(text="Layer:")
            sub = layout.row()
            sub.ui_units_x = 8
            sub.popover(
                panel="TOPBAR_PT_gpencil_layers",
                text=text,
            )


class _draw_tool_settings_context_mode:
    @staticmethod
    def SCULPT(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False

        paint = context.tool_settings.sculpt
        layout.template_ID_preview(paint, "brush", rows=3, cols=8, hide_buttons=True)

        brush = paint.brush
        if brush is None:
            return False

        tool_settings = context.tool_settings
        capabilities = brush.sculpt_capabilities

        ups = tool_settings.unified_paint_settings

        size = "size"
        size_owner = ups if ups.use_unified_size else brush
        if size_owner.use_locked_size == 'SCENE':
            size = "unprojected_radius"

        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            size,
            pressure_name="use_pressure_size",
            unified_name="use_unified_size",
            text="Radius",
            slider=True,
            header=True
        )

        # strength, use_strength_pressure
        pressure_name = "use_pressure_strength" if capabilities.has_strength_pressure else None
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "strength",
            pressure_name=pressure_name,
            unified_name="use_unified_strength",
            text="Strength",
            header=True
        )

        # direction
        if not capabilities.has_direction:
            layout.row().prop(brush, "direction", expand=True, text="")

        return True

    @staticmethod
    def PAINT_TEXTURE(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False

        paint = context.tool_settings.image_paint
        layout.template_ID_preview(paint, "brush", rows=3, cols=8, hide_buttons=True)

        brush = paint.brush
        if brush is None:
            return False

        brush_basic_texpaint_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def PAINT_VERTEX(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False

        paint = context.tool_settings.vertex_paint
        layout.template_ID_preview(paint, "brush", rows=3, cols=8, hide_buttons=True)

        brush = paint.brush
        if brush is None:
            return False

        brush_basic_texpaint_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def PAINT_WEIGHT(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False

        paint = context.tool_settings.weight_paint
        layout.template_ID_preview(paint, "brush", rows=3, cols=8, hide_buttons=True)
        brush = paint.brush
        if brush is None:
            return False

        capabilities = brush.weight_paint_capabilities
        if capabilities.has_weight:
            UnifiedPaintPanel.prop_unified(
                layout,
                context,
                brush,
                "weight",
                unified_name="use_unified_weight",
                slider=True,
                header=True
            )

        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "size",
            pressure_name="use_pressure_size",
            unified_name="use_unified_size",
            slider=True,
            text="Radius",
            header=True
        )
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "strength",
            pressure_name="use_pressure_strength",
            unified_name="use_unified_strength",
            header=True
        )

        return True

    @staticmethod
    def PAINT_GPENCIL(context, layout, tool):
        if tool is None:
            return False

        # is_paint = True
        # FIXME: tools must use their own UI drawing!
        if tool.idname in {
                "builtin.line",
                "builtin.box",
                "builtin.circle",
                "builtin.arc",
                "builtin.curve",
                "builtin.polyline",
        }:
            # is_paint = False
            pass
        elif tool.idname == "builtin.cutter":
            row = layout.row(align=True)
            row.prop(context.tool_settings.gpencil_sculpt, "intersection_threshold")
            return False
        elif not tool.has_datablock:
            return False

        paint = context.tool_settings.gpencil_paint
        brush = paint.brush
        if brush is None:
            return False

        gp_settings = brush.gpencil_settings

        def draw_color_selector():
            ma = gp_settings.material
            row = layout.row(align=True)
            if not gp_settings.use_material_pin:
                ma = context.object.active_material
            icon_id = 0
            if ma:
                icon_id = ma.id_data.preview.icon_id
                txt_ma = ma.name
                maxw = 25
                if len(txt_ma) > maxw:
                    txt_ma = txt_ma[:maxw - 5] + '..' + txt_ma[-3:]
            else:
                txt_ma = ""

            sub = row.row()
            sub.ui_units_x = 8
            sub.popover(
                panel="TOPBAR_PT_gpencil_materials",
                text=txt_ma,
                icon_value=icon_id,
            )

            row.prop(gp_settings, "use_material_pin", text="")

            if brush.gpencil_tool in {'DRAW', 'FILL'}:
                row.separator(factor=1.0)
                subrow = row.row(align=True)
                row.prop_enum(settings, "color_mode", 'MATERIAL', text="", icon='MATERIAL')
                row.prop_enum(settings, "color_mode", 'VERTEXCOLOR', text="", icon='VPAINT_HLT')
                sub_row = row.row(align=True)
                sub_row.enabled = settings.color_mode == 'VERTEXCOLOR'
                sub_row.prop_with_popover(brush, "color", text="", panel="TOPBAR_PT_gpencil_vertexcolor")

        row = layout.row(align=True)
        tool_settings = context.scene.tool_settings
        settings = tool_settings.gpencil_paint
        row.template_ID_preview(settings, "brush", rows=3, cols=8, hide_buttons=True)

        if context.object and brush.gpencil_tool in {'FILL', 'DRAW'}:
            draw_color_selector()

        if context.object and brush.gpencil_tool == 'TINT':
            row.separator(factor=0.4)
            row.prop_with_popover(brush, "color", text="", panel="TOPBAR_PT_gpencil_vertexcolor")

        from bl_ui.properties_paint_common import (
            brush_basic_gpencil_paint_settings,
        )
        brush_basic_gpencil_paint_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def SCULPT_GPENCIL(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False
        paint = context.tool_settings.gpencil_sculpt_paint
        brush = paint.brush

        from bl_ui.properties_paint_common import (
            brush_basic_gpencil_sculpt_settings,
        )
        brush_basic_gpencil_sculpt_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def WEIGHT_GPENCIL(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False
        paint = context.tool_settings.gpencil_weight_paint
        brush = paint.brush

        from bl_ui.properties_paint_common import (
            brush_basic_gpencil_weight_settings,
        )
        brush_basic_gpencil_weight_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def VERTEX_GPENCIL(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False

        paint = context.tool_settings.gpencil_vertex_paint
        brush = paint.brush

        row = layout.row(align=True)
        tool_settings = context.scene.tool_settings
        settings = tool_settings.gpencil_vertex_paint
        row.template_ID_preview(settings, "brush", rows=3, cols=8, hide_buttons=True)

        if brush.gpencil_vertex_tool not in {'BLUR', 'AVERAGE', 'SMEAR'}:
            row.separator(factor=0.4)
            row.prop_with_popover(brush, "color", text="", panel="TOPBAR_PT_gpencil_vertexcolor")

        from bl_ui.properties_paint_common import (
            brush_basic_gpencil_vertex_settings,
        )

        brush_basic_gpencil_vertex_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def PARTICLE(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return False

        # See: 'VIEW3D_PT_tools_brush', basically a duplicate
        settings = context.tool_settings.particle_edit
        brush = settings.brush
        tool = settings.tool
        if tool == 'NONE':
            return False

        layout.prop(brush, "size", slider=True)
        if tool == 'ADD':
            layout.prop(brush, "count")

            layout.prop(settings, "use_default_interpolate")
            layout.prop(brush, "steps", slider=True)
            layout.prop(settings, "default_key_count", slider=True)
        else:
            layout.prop(brush, "strength", slider=True)

            if tool == 'LENGTH':
                layout.row().prop(brush, "length_mode", expand=True)
            elif tool == 'PUFF':
                layout.row().prop(brush, "puff_mode", expand=True)
                layout.prop(brush, "use_puff_volume")
            elif tool == 'COMB':
                row = layout.row()
                row.active = settings.is_editable
                row.prop(settings, "use_emitter_deflect", text="Deflect Emitter")
                sub = row.row(align=True)
                sub.active = settings.use_emitter_deflect
                sub.prop(settings, "emitter_distance", text="Distance")

        return True


# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class VIEW3D_MT_editor_menus(Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mode_string = context.mode
        edit_object = context.edit_object
        gp_edit = obj and obj.mode in {'EDIT_GPENCIL', 'PAINT_GPENCIL', 'SCULPT_GPENCIL',
                                       'WEIGHT_GPENCIL', 'VERTEX_GPENCIL'}
        ts = context.scene.tool_settings

        layout.menu("SCREEN_MT_user_menu", text = "Quick") # Quick favourites menu
        layout.menu("VIEW3D_MT_view")
        layout.menu("VIEW3D_MT_view_navigation")

        # Select Menu
        if gp_edit:
            if mode_string not in {'PAINT_GPENCIL', 'WEIGHT_GPENCIL'}:
                if mode_string == 'SCULPT_GPENCIL' and \
                    (ts.use_gpencil_select_mask_point or
                     ts.use_gpencil_select_mask_stroke or
                     ts.use_gpencil_select_mask_segment):
                    layout.menu("VIEW3D_MT_select_gpencil")
                    layout.menu("VIEW3D_MT_sculpt_gpencil_copy")
                elif mode_string == 'EDIT_GPENCIL':
                    layout.menu("VIEW3D_MT_select_gpencil")
                elif mode_string == 'VERTEX_GPENCIL':
                    layout.menu("VIEW3D_MT_select_gpencil")
                    layout.menu("VIEW3D_MT_gpencil_animation")
                    layout.menu("GPENCIL_MT_layer_active", text = "Active Layer")

        elif mode_string in {'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE'}:
            mesh = obj.data
            if mesh.use_paint_mask:
                layout.menu("VIEW3D_MT_select_paint_mask")
            elif mesh.use_paint_mask_vertex and mode_string in {'PAINT_WEIGHT', 'PAINT_VERTEX'}:
                layout.menu("VIEW3D_MT_select_paint_mask_vertex")
        elif mode_string != 'SCULPT':
            layout.menu("VIEW3D_MT_select_%s" % mode_string.lower())

        if gp_edit:
            pass
        elif mode_string == 'OBJECT':
            layout.menu("VIEW3D_MT_add", text="Add", text_ctxt=i18n_contexts.operator_default)
        elif mode_string == 'EDIT_MESH':
            layout.menu("VIEW3D_MT_mesh_add", text="Add", text_ctxt=i18n_contexts.operator_default)
        elif mode_string == 'EDIT_CURVE':
            layout.menu("VIEW3D_MT_curve_add", text="Add", text_ctxt=i18n_contexts.operator_default)
        elif mode_string == 'EDIT_SURFACE':
            layout.menu("VIEW3D_MT_surface_add", text="Add", text_ctxt=i18n_contexts.operator_default)
        elif mode_string == 'EDIT_METABALL':
            layout.menu("VIEW3D_MT_metaball_add", text="Add", text_ctxt=i18n_contexts.operator_default)
        elif mode_string == 'EDIT_ARMATURE':
            layout.menu("TOPBAR_MT_edit_armature_add", text="Add", text_ctxt=i18n_contexts.operator_default)

        if gp_edit:
            if obj and obj.mode == 'PAINT_GPENCIL':
                layout.menu("VIEW3D_MT_paint_gpencil")
            elif obj and obj.mode == 'EDIT_GPENCIL':
                layout.menu("VIEW3D_MT_edit_gpencil")
                layout.menu("VIEW3D_MT_edit_gpencil_stroke")
                layout.menu("VIEW3D_MT_edit_gpencil_point")
            elif obj and obj.mode == 'WEIGHT_GPENCIL':
                layout.menu("VIEW3D_MT_weight_gpencil")

        elif edit_object:
            layout.menu("VIEW3D_MT_edit_%s" % edit_object.type.lower())

            if mode_string == 'EDIT_MESH':
                layout.menu("VIEW3D_MT_edit_mesh_vertices")
                layout.menu("VIEW3D_MT_edit_mesh_edges")
                layout.menu("VIEW3D_MT_edit_mesh_faces")
                layout.menu("VIEW3D_MT_uv_map", text="UV")
            elif mode_string in {'EDIT_CURVE', 'EDIT_SURFACE'}:
                layout.menu("VIEW3D_MT_edit_curve_ctrlpoints")
                layout.menu("VIEW3D_MT_edit_curve_segments")

        elif obj:
            if mode_string != 'PAINT_TEXTURE':
                layout.menu("VIEW3D_MT_%s" % mode_string.lower())
            if mode_string in {'SCULPT', 'PAINT_VERTEX', 'PAINT_WEIGHT', 'PAINT_TEXTURE'}:
                layout.menu("VIEW3D_MT_brush")
            if mode_string == 'SCULPT':
                layout.menu("VIEW3D_MT_mask")
                layout.menu("VIEW3D_MT_face_sets")

        else:
            layout.menu("VIEW3D_MT_object")


# ********** Menu **********


# ********** Utilities **********


class ShowHideMenu:
    bl_label = "Show/Hide"
    _operator_name = ""

    def draw(self, _context):
        layout = self.layout

        layout.operator("%s.reveal" % self._operator_name, text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("%s.hide" % self._operator_name, text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("%s.hide" % self._operator_name, text="Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


# Standard transforms which apply to all cases
# NOTE: this doesn't seem to be able to be used directly
class VIEW3D_MT_transform_base(Menu):
    bl_label = "Transform"
    bl_category = "View"

    # TODO: get rid of the custom text strings?
    def draw(self, context):
        layout = self.layout

        obj = context.object

        layout.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
        layout.operator("transform.shear", text="Shear", icon = "SHEAR")
        layout.operator("transform.bend", text="Bend", icon = "BEND")
        layout.operator("transform.push_pull", text="Push/Pull", icon = 'PUSH_PULL')

        if context.mode != 'OBJECT':
            layout.operator("transform.vertex_warp", text="Warp", icon = "MOD_WARP")
            layout.operator_context = 'EXEC_DEFAULT'
            layout.operator("transform.vertex_random", text="Randomize", icon = 'RANDOMIZE').offset = 0.1
            layout.operator_context = 'INVOKE_REGION_WIN'


# Generic transform menu - geometry types
class VIEW3D_MT_transform(VIEW3D_MT_transform_base):
    def draw(self, context):
        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        obj = context.object

        # generic
        layout = self.layout

        if obj.type == 'MESH':
            layout.operator("transform.shrink_fatten", text="Shrink Fatten", icon = 'SHRINK_FATTEN')
            layout.operator("transform.skin_resize", icon = "MOD_SKIN")

        elif obj.type == 'CURVE':
            layout.operator("transform.transform", text="Shrink Fatten", icon = 'SHRINK_FATTEN').mode = 'CURVE_SHRINKFATTEN'

        layout.separator()

        layout.operator("transform.translate", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True


# Object-specific extensions to Transform menu
class VIEW3D_MT_transform_object(VIEW3D_MT_transform_base):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # object-specific option follow
        layout.separator()

        layout.operator("transform.translate", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        # XXX see alignmenu() in edit.c of b2.4x to get this working
        layout.operator("transform.transform", text="Align to Transform Orientation", icon = "ALIGN_TRANSFORM").mode = 'ALIGN'

        layout.separator()

        layout.operator("object.randomize_transform", icon = "RANDOMIZE_TRANSFORM")
        layout.operator("object.align", icon = "ALIGN")

        # TODO: there is a strange context bug here.
        """
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.transform_axis_target")
        """


# Armature EditMode extensions to Transform menu
class VIEW3D_MT_transform_armature(VIEW3D_MT_transform_base):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # armature specific extensions follow
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:
            if obj.data.display_type == 'BBONE':
                layout.separator()

                layout.operator("transform.transform", text="Scale BBone", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'
            elif obj.data.display_type == 'ENVELOPE':
                layout.separator()

                layout.operator("transform.transform", text="Scale Envelope Distance", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'
                layout.operator("transform.transform", text="Scale Radius", icon='TRANSFORM_SCALE').mode = 'BONE_ENVELOPE'

        if context.edit_object and context.edit_object.type == 'ARMATURE':
            layout.separator()

            layout.operator("armature.align", icon = "ALIGN")


class VIEW3D_MT_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.mirror", text="Interactive Mirror", icon='TRANSFORM_MIRROR')

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'

        props = layout.operator("transform.mirror", text="X Global", icon = "MIRROR_X")
        props.constraint_axis = (True, False, False)
        props.orient_type = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Y Global", icon = "MIRROR_Y")
        props.constraint_axis = (False, True, False)
        props.orient_type = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Z Global", icon = "MIRROR_Z")
        props.constraint_axis = (False, False, True)
        props.orient_type = 'GLOBAL'

        layout.separator()

        props = layout.operator("transform.mirror", text="X Local", icon = "MIRROR_X")
        props.constraint_axis = (True, False, False)
        props.orient_type = 'LOCAL'
        props = layout.operator("transform.mirror", text="Y Local", icon = "MIRROR_Y")
        props.constraint_axis = (False, True, False)
        props.orient_type = 'LOCAL'
        props = layout.operator("transform.mirror", text="Z Local", icon = "MIRROR_Z")
        props.constraint_axis = (False, False, True)
        props.orient_type = 'LOCAL'

        if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:

            layout.separator()

            layout.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP")


class VIEW3D_MT_snap(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout


        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon = "SELECTIONTOCURSOR").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
        layout.operator("view3d.snap_selected_to_active", text="Selection to Active", icon = "SELECTIONTOACTIVE")
        layout.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon = "SELECTIONTOGRID")

        layout.separator()

        layout.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon = "CURSORTOSELECTION")
        layout.operator("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon = "CURSORTOCENTER")
        layout.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon = "CURSORTOACTIVE")
        layout.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon = "CURSORTOGRID")


# Tooltip and operator for Clear Seam.
class VIEW3D_MT_uv_map_clear_seam(bpy.types.Operator):
    """Clears the UV Seam for selected edges"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.clear_seam"        # unique identifier for buttons and menu items to reference.
    bl_label = "Clear seam"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.mark_seam(clear=True)
        return {'FINISHED'}


class VIEW3D_MT_uv_map(Menu):
    bl_label = "UV Mapping"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings

        layout.operator("uv.unwrap", text = "Unwrap ABF", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
        layout.operator("uv.unwrap", text = "Unwrap Conformal", icon='UNWRAP_LSCM').method = 'CONFORMAL'

        layout.separator()

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("uv.smart_project", icon = "MOD_UVPROJECT")
        layout.operator("uv.lightmap_pack", icon = "LIGHTMAPPACK")
        layout.operator("uv.follow_active_quads", icon = "FOLLOWQUADS")

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("uv.cube_project", icon = "CUBEPROJECT")
        layout.operator("uv.cylinder_project", icon = "CYLINDERPROJECT")
        layout.operator("uv.sphere_project", icon = "SPHEREPROJECT")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("uv.project_from_view", icon = "PROJECTFROMVIEW").scale_to_bounds = False
        layout.operator("uv.project_from_view", text="Project from View (Bounds)", icon = "PROJECTFROMVIEW").scale_to_bounds = True

        layout.separator()

        layout.operator("mesh.mark_seam", icon = "MARK_SEAM").clear = False
        layout.operator("mesh.clear_seam", text="Clear Seam", icon = 'CLEAR_SEAM')

        layout.separator()

        layout.operator("uv.reset", icon = "RESET")


# ********** View menus **********


    # Workaround to separate the tooltips
class VIEW3D_MT_view_view_selected_all_regions(bpy.types.Operator):
    """Move the View to the selection center in all Quad View views"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_selected_all_regions"        # unique identifier for buttons and menu items to reference.
    bl_label = "View Selected All Regions"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_selected(use_all_regions = True)
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_view_all_all_regions(bpy.types.Operator):
    """View all objects in scene in all four Quad View views\nJust relevant for Quad View """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_all_all_regions"        # unique identifier for buttons and menu items to reference.
    bl_label = "View All all Regions"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_all(use_all_regions = True)
        return {'FINISHED'}

    # Workaround to separate the tooltips
class VIEW3D_MT_view_center_cursor_and_view_all(bpy.types.Operator):
    """Views all objects in scene and centers the 3D cursor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_all_center_cursor"        # unique identifier for buttons and menu items to reference.
    bl_label = "Center Cursor and Frame All"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_all(center = True)
        return {'FINISHED'}

class VIEW3D_MT_switchactivecamto(bpy.types.Operator):
    """Sets the current selected camera as the active camera to render from\nYou need to have a camera object selected"""
    bl_idname = "view3d.switchactivecamto"
    bl_label = "Set active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        context = bpy.context
        scene = context.scene
        if context.active_object is not None:
            currentCameraObj = bpy.data.objects[bpy.context.active_object.name]
            scene.camera = currentCameraObj
        return {'FINISHED'}


class VIEW3D_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        layout.prop(view, "show_region_toolbar")
        layout.prop(view, "show_region_ui")
        layout.prop(view, "show_region_tool_header")
        layout.prop(view, "show_region_hud")

        layout.separator()

        layout.operator("render.opengl", text="OpenGL Render Image", icon='RENDER_STILL')
        layout.operator("render.opengl", text="OpenGL Render Animation", icon='RENDER_ANIMATION').animation = True
        props = layout.operator("render.opengl", text="OpenGL Render Keyframes", icon='RENDER_ANIMATION')
        props.animation = True
        props.render_keyed_only = True

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.clip_border", text="Clipping Border", icon = "CLIPPINGBORDER")
        layout.operator("view3d.render_border", icon = "RENDERBORDER")
        layout.operator("view3d.clear_render_border", icon = "RENDERBORDER_CLEAR")

        layout.separator()

        layout.operator("view3d.object_as_camera", icon = 'VIEW_SWITCHACTIVECAM')
        layout.operator("view3d.switchactivecamto", text="Set Active Camera", icon ="VIEW_SWITCHACTIVECAM")
        layout.operator("view3d.view_camera", text="Active Camera", icon = 'VIEW_SWITCHTOCAM')
        layout.operator("view3d.view_center_camera", icon = "VIEWCAMERACENTER")

        layout.separator()

        layout.menu("VIEW3D_MT_view_align")
        layout.menu("VIEW3D_MT_view_align_selected")

        layout.separator()

        layout.operator("view3d.localview", text="Toggle Local View", icon = "VIEW_GLOBAL_LOCAL")
        layout.operator("view3d.localview_remove_from", icon = "VIEW_REMOVE_LOCAL")

        layout.separator()

        layout.operator("view3d.view_selected", text="View Selected", icon = "VIEW_SELECTED").use_all_regions = False
        if view.region_quadviews:
            layout.operator("view3d.view_selected_all_regions", text="View Selected (Quad View)", icon = "ALIGNCAMERA_ACTIVE")
        layout.operator("view3d.view_all", text="Frame All", icon = "VIEWALL").center = False
        if view.region_quadviews:
            layout.operator("view3d.view_all_all_regions", text = "View All (Quad View)", icon = "VIEWALL" ) # bfa - separated tooltip
        layout.operator("view3d.view_all_center_cursor", text="Center Cursor and Frame All", icon = "VIEWALL_RESETCURSOR") # bfa - separated tooltip

        layout.separator()

        layout.menu("INFO_MT_area")

class VIEW3D_MT_view_navigation(Menu):
    bl_label = "Navi"

    def draw(self, _context):
        from math import pi
        layout = self.layout

        layout.operator("view3d.view_orbit", text= "Orbit Down", icon = "ORBIT_DOWN").type='ORBITDOWN'
        layout.operator("view3d.view_orbit", text= "Orbit Up", icon = "ORBIT_UP").type='ORBITUP'
        layout.operator("view3d.view_orbit", text= "Orbit Right", icon = "ORBIT_RIGHT").type='ORBITRIGHT'
        layout.operator("view3d.view_orbit", text= "Orbit Left", icon = "ORBIT_LEFT").type='ORBITLEFT'
        props = layout.operator("view3d.view_orbit", text = "Orbit Opposite", icon = "ORBIT_OPPOSITE")
        props.type = 'ORBITRIGHT'
        props.angle = pi

        layout.separator()

        layout.operator("view3d.view_roll", text="Roll Left", icon = "ROLL_LEFT").angle = pi / -12.0
        layout.operator("view3d.view_roll", text="Roll Right", icon = "ROLL_RIGHT").angle = pi / 12.0

        layout.separator()

        layout.operator("view3d.view_pan", text= "Pan Down", icon = "PAN_DOWN").type = 'PANDOWN'
        layout.operator("view3d.view_pan", text= "Pan Up", icon = "PAN_UP").type = 'PANUP'
        layout.operator("view3d.view_pan", text= "Pan Right", icon = "PAN_RIGHT").type = 'PANRIGHT'
        layout.operator("view3d.view_pan", text= "Pan Left", icon = "PAN_LEFT").type = 'PANLEFT'

        layout.separator()

        layout.operator("view3d.zoom_border", text="Zoom Border", icon = "ZOOM_BORDER")
        layout.operator("view3d.zoom", text="Zoom In", icon = "ZOOM_IN").delta = 1
        layout.operator("view3d.zoom", text="Zoom Out", icon = "ZOOM_OUT").delta = -1
        layout.operator("view3d.zoom_camera_1_to_1", text="Zoom Camera 1:1", icon = "ZOOM_CAMERA")
        layout.operator("view3d.dolly", text="Dolly View", icon = "DOLLY")
        layout.operator("view3d.view_center_pick", icon = "CENTERTOMOUSE")

        layout.separator()

        layout.operator("view3d.fly", icon = "FLY_NAVIGATION")
        layout.operator("view3d.walk", icon = "WALK_NAVIGATION")
        layout.operator("view3d.navigate", icon = "VIEW_NAVIGATION")

        layout.separator()

        layout.operator("screen.animation_play", text="Playback Animation", icon = "TRIA_RIGHT")


class VIEW3D_MT_view_align(Menu):
    bl_label = "Align View"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.camera_to_view", text="Align Active Camera to View", icon = "ALIGNCAMERA_VIEW")
        layout.operator("view3d.camera_to_view_selected", text="Align Active Camera to Selected", icon = "ALIGNCAMERA_ACTIVE")
        layout.operator("view3d.view_center_cursor", icon = "CENTERTOCURSOR")

        layout.separator()

        layout.operator("view3d.view_lock_to_active", icon = "LOCKTOACTIVE")
        layout.operator("view3d.view_center_lock", icon = "LOCKTOCENTER")
        layout.operator("view3d.view_lock_clear", icon = "LOCK_CLEAR")

        layout.separator()

        layout.operator("view3d.view_persportho", text="Perspective/Orthographic", icon = "PERSP_ORTHO")

        layout.separator()

        layout.operator("view3d.view_axis", text="Top", icon ="VIEW_TOP").type = 'TOP'
        layout.operator("view3d.view_axis", text="Bottom", icon ="VIEW_BOTTOM").type = 'BOTTOM'
        layout.operator("view3d.view_axis", text="Front", icon ="VIEW_FRONT").type = 'FRONT'
        layout.operator("view3d.view_axis", text="Back", icon ="VIEW_BACK").type = 'BACK'
        layout.operator("view3d.view_axis", text="Right", icon ="VIEW_RIGHT").type = 'RIGHT'
        layout.operator("view3d.view_axis", text="Left", icon ="VIEW_LEFT").type = 'LEFT'


class VIEW3D_MT_view_align_selected(Menu):
    bl_label = "Align View to Active"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("view3d.view_axis", text="Top", icon = "VIEW_ACTIVE_TOP")
        props.align_active = True
        props.type = 'TOP'

        props = layout.operator("view3d.view_axis", text="Bottom", icon ="VIEW_ACTIVE_BOTTOM")
        props.align_active = True
        props.type = 'BOTTOM'

        props = layout.operator("view3d.view_axis", text="Front", icon ="VIEW_ACTIVE_FRONT")
        props.align_active = True
        props.type = 'FRONT'

        props = layout.operator("view3d.view_axis", text="Back", icon ="VIEW_ACTIVE_BACK")
        props.align_active = True
        props.type = 'BACK'

        props = layout.operator("view3d.view_axis", text="Right" , icon ="VIEW_ACTIVE_RIGHT")
        props.align_active = True
        props.type = 'RIGHT'

        props = layout.operator("view3d.view_axis", text="Left", icon ="VIEW_ACTIVE_LEFT")
        props.align_active = True
        props.type = 'LEFT'


# ********** Select menus, suffix from context.mode **********

class VIEW3D_MT_select_object_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout = self.layout

        layout.operator("object.select_more", text="More", icon = "SELECTMORE")
        layout.operator("object.select_less", text="Less", icon = "SELECTLESS")

        layout.separator()

        props = layout.operator("object.select_hierarchy", text="Parent", icon = "PARENT")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("object.select_hierarchy", text="Child", icon = "CHILD")
        props.extend = False
        props.direction = 'CHILD'

        layout.separator()

        props = layout.operator("object.select_hierarchy", text="Extend Parent", icon = "PARENT")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("object.select_hierarchy", text="Extend Child", icon = "CHILD")
        props.extend = True
        props.direction = 'CHILD'


# Workaround to separate the tooltips
class VIEW3D_MT_select_object_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_object_none(bpy.types.Operator):
    """Deselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_object(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("object.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("object.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.menu ("VIEW3D_MT_select_grouped")
        layout.menu ("VIEW3D_MT_select_linked")
        layout.menu ("VIEW3D_MT_select_by_type")

        layout.separator()
        layout.operator("object.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("object.select_mirror", text="Mirror Selection", icon = "TRANSFORM_MIRROR")

        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")
        layout.operator("object.select_camera", text="Active Camera", icon = "CAMERA_DATA")

        layout.separator()

        layout.menu("VIEW3D_MT_select_object_more_less")



class VIEW3D_MT_select_by_type(Menu):
    bl_label = "All by Type"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_by_type", text= "Mesh", icon = "OUTLINER_OB_MESH").type = 'MESH'
        layout.operator("object.select_by_type", text= "Curve", icon = "OUTLINER_OB_CURVE").type = 'CURVE'
        layout.operator("object.select_by_type", text= "Surface", icon = "OUTLINER_OB_SURFACE").type = 'SURFACE'
        layout.operator("object.select_by_type", text= "Meta", icon = "OUTLINER_OB_META").type = 'META'
        layout.operator("object.select_by_type", text= "Font", icon = "OUTLINER_OB_FONT").type = 'FONT'

        layout.separator()

        layout.operator("object.select_by_type", text= "Armature", icon = "OUTLINER_OB_ARMATURE").type = 'ARMATURE'
        layout.operator("object.select_by_type", text= "Lattice", icon = "OUTLINER_OB_LATTICE").type = 'LATTICE'
        layout.operator("object.select_by_type", text= "Empty", icon = "OUTLINER_OB_EMPTY").type = 'EMPTY'
        layout.operator("object.select_by_type", text= "GPencil", icon = "GREASEPENCIL").type = 'GPENCIL'

        layout.separator()

        layout.operator("object.select_by_type", text= "Camera", icon = "OUTLINER_OB_CAMERA").type = 'CAMERA'
        layout.operator("object.select_by_type", text= "Light", icon = "OUTLINER_OB_LIGHT").type = 'LIGHT'
        layout.operator("object.select_by_type", text= "Speaker", icon = "OUTLINER_OB_SPEAKER").type = 'SPEAKER'
        layout.operator("object.select_by_type", text= "Probe", icon = "OUTLINER_OB_LIGHTPROBE").type = 'LIGHT_PROBE'

class VIEW3D_MT_select_grouped(Menu):
    bl_label = "Grouped"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_grouped", text= "Siblings", icon = "SIBLINGS").type = 'SIBLINGS'
        layout.operator("object.select_grouped", text= "Parent", icon = "PARENT").type = 'PARENT'
        layout.operator("object.select_grouped", text= "Children", icon = "CHILD_RECURSIVE").type = 'CHILDREN_RECURSIVE'
        layout.operator("object.select_grouped", text= "Immediate Children", icon = "CHILD").type = 'CHILDREN'

        layout.separator()

        layout.operator("object.select_grouped", text= "Type", icon = "TYPE").type = 'TYPE'
        layout.operator("object.select_grouped", text= "Collection", icon = "GROUP").type = 'COLLECTION'
        layout.operator("object.select_grouped", text= "Hook", icon = "HOOK").type = 'HOOK'

        layout.separator()

        layout.operator("object.select_grouped", text= "Pass", icon = "PASS").type = 'PASS'
        layout.operator("object.select_grouped", text= "Color", icon = "COLOR").type = 'COLOR'
        layout.operator("object.select_grouped", text= "Keying Set", icon = "KEYINGSET").type = 'KEYINGSET'
        layout.operator("object.select_grouped", text= "Light Type", icon = "LIGHT").type = 'LIGHT_TYPE'


class VIEW3D_MT_select_linked(Menu):
    bl_label = "Linked"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_linked", text= "Object Data", icon = "OBJECT_DATA").type = 'OBDATA'
        layout.operator("object.select_linked", text= "Material", icon = "MATERIAL_DATA").type = 'MATERIAL'
        layout.operator("object.select_linked", text= "Instanced Collection", icon = "GROUP").type = 'DUPGROUP'
        layout.operator("object.select_linked", text= "Particle System", icon = "PARTICLES").type = 'PARTICLE'
        layout.operator("object.select_linked", text= "Library", icon = "LIBRARY").type = 'LIBRARY'
        layout.operator("object.select_linked", text= "Library (Object Data)", icon = "LIBRARY_OBJECT").type = 'LIBRARY_OBDATA'


# Workaround to separate the tooltips
class VIEW3D_MT_select_pose_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "pose.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.pose.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_pose_none(bpy.types.Operator):
    """Deselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "pose.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.pose.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_pose(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("pose.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("pose.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator_menu_enum("pose.select_grouped", "type", text="Grouped")
        layout.operator("pose.select_linked", text="Linked", icon = "LINKED")
        layout.operator("pose.select_constraint_target", text="Constraint Target", icon = "CONSTRAINT_BONE")

        layout.separator()

        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")

        layout.separator()

        layout.operator("pose.select_mirror", text="Flip Active", icon = "FLIP")

        layout.separator()

        props = layout.operator("pose.select_hierarchy", text="Parent", icon = "PARENT")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child", icon = "CHILD")
        props.extend = False
        props.direction = 'CHILD'

        layout.separator()

        props = layout.operator("pose.select_hierarchy", text="Extend Parent", icon = "PARENT")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Extend Child", icon = "CHILD")
        props.extend = True
        props.direction = 'CHILD'


# Workaround to separate the tooltips
class VIEW3D_MT_select_particle_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "particle.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.particle.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_particle_none(bpy.types.Operator):
    """Deselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "particle.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.particle.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_particle(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("particle.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("particle.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("particle.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("particle.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("particle.select_less", text = "Less", icon = "SELECTLESS")

        layout.separator()

        layout.operator("particle.select_linked", text="Linked", icon = "LINKED")

        layout.separator()


        layout.operator("particle.select_random", text = "Random", icon = "RANDOMIZE")

        layout.separator()

        layout.operator("particle.select_roots", text="Roots", icon = "SELECT_ROOT")
        layout.operator("particle.select_tips", text="Tips", icon = "SELECT_TIP")


class VIEW3D_MT_edit_mesh_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, _context):
        layout = self.layout

        select_mode = _context.tool_settings.mesh_select_mode

        # Vertices select mode
        if tuple(select_mode) == (True, False, False):

            layout.operator("mesh.select_similar", text= "Normal", icon = "RECALC_NORMALS").type='NORMAL'
            layout.operator("mesh.select_similar", text= "Amount of Adjacent Faces", icon = "FACESEL").type='FACE'
            layout.operator("mesh.select_similar", text= "Vertex Groups", icon = "GROUP_VERTEX").type='VGROUP'
            layout.operator("mesh.select_similar", text= "Amount of connecting Edges", icon = "EDGESEL").type='EDGE'

        # Edges select mode
        if tuple(select_mode) == (False, True, False):

            layout.operator("mesh.select_similar", text= "Length", icon = "RULER").type='LENGTH'
            layout.operator("mesh.select_similar", text= "Direction", icon = "SWITCH_DIRECTION").type='DIR'
            layout.operator("mesh.select_similar", text= "Amount of Faces around an edge", icon = "FACESEL").type='FACE'
            layout.operator("mesh.select_similar", text= "Face Angles", icon = "ANGLE").type='FACE_ANGLE'
            layout.operator("mesh.select_similar", text= "Crease", icon = "CREASE").type='CREASE'
            layout.operator("mesh.select_similar", text= "Bevel", icon = "BEVEL").type='BEVEL'
            layout.operator("mesh.select_similar", text= "Seam", icon = "MARK_SEAM").type='SEAM'
            layout.operator("mesh.select_similar", text= "Sharpness", icon = "SELECT_SHARPEDGES").type='SHARP'
            layout.operator("mesh.select_similar", text= "Freestyle Edge Marks", icon = "MARK_FS_EDGE").type='FREESTYLE_EDGE'

        # Faces select mode
        if tuple(select_mode) == (False, False, True ):

            layout.operator("mesh.select_similar", text= "Material", icon = "MATERIAL").type='MATERIAL'
            layout.operator("mesh.select_similar", text= "Area", icon = "AREA").type='AREA'
            layout.operator("mesh.select_similar", text= "Polygon Sides", icon = "POLYGONSIDES").type='SIDES'
            layout.operator("mesh.select_similar", text= "Perimeter", icon = "PERIMETER").type='PERIMETER'
            layout.operator("mesh.select_similar", text= "Normal", icon = "RECALC_NORMALS").type='NORMAL'
            layout.operator("mesh.select_similar", text= "Co-Planar", icon = "MAKE_PLANAR").type='COPLANAR'
            layout.operator("mesh.select_similar", text= "Flat / Smooth", icon = "SHADING_SMOOTH").type='SMOOTH'
            layout.operator("mesh.select_similar", text= "Face Map", icon = "TEXTURE").type='FACE_MAP'
            layout.operator("mesh.select_similar", text= "Freestyle Face Marks", icon = "MARKFSFACE").type='FREESTYLE_FACE'

        layout.separator()

        layout.operator("mesh.select_similar_region", text="Face Regions", icon = "FACEREGIONS")


class VIEW3D_MT_edit_mesh_select_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.select_more", text="More", icon = "SELECTMORE")
        layout.operator("mesh.select_less", text="Less", icon = "SELECTLESS")

        layout.separator()

        layout.operator("mesh.select_next_item", text="Next Active", icon = "NEXTACTIVE")
        layout.operator("mesh.select_prev_item", text="Previous Active", icon = "PREVIOUSACTIVE")


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_mesh_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_mesh_none(bpy.types.Operator):
    """Deselects everything """       # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_edit_mesh(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        # primitive
        layout.operator("mesh.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("mesh.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("mesh.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("mesh.select_linked", text="Linked", icon = "LINKED")
        layout.operator("mesh.faces_select_linked_flat", text="Linked Flat Faces", icon = "LINKED")
        layout.operator("mesh.select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("mesh.select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True

        layout.separator()

        # other
        layout.menu("VIEW3D_MT_edit_mesh_select_similar")

        layout.separator()

        # numeric
        layout.operator("mesh.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("mesh.select_nth", icon = "CHECKER_DESELECT")

        layout.separator()

        layout.operator("mesh.select_mirror", text="Mirror Selection", icon = "TRANSFORM_MIRROR")
        layout.operator("mesh.select_axis", text="Side of Active", icon = "SELECT_SIDEOFACTIVE")
        layout.operator("mesh.shortest_path_select", text="Shortest Path", icon = "SELECT_SHORTESTPATH")

        layout.separator()

        # geometric
        layout.operator("mesh.edges_select_sharp", text="Sharp Edges", icon = "SELECT_SHARPEDGES")

        layout.separator()

        # topology
        tool_settings = _context.tool_settings
        if tool_settings.mesh_select_mode[2] is False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold", icon = "SELECT_NONMANIFOLD")
        layout.operator("mesh.select_loose", text="Loose Geometry", icon = "SELECT_LOOSE")
        layout.operator("mesh.select_interior_faces", text="Interior Faces", icon = "SELECT_INTERIOR")
        layout.operator("mesh.select_face_by_sides", text="Faces by Sides", icon = "SELECT_FACES_BY_SIDE")

        layout.separator()

        # loops
        layout.operator("mesh.loop_multi_select", text="Edge Loops", icon = "SELECT_EDGELOOP").ring = False
        layout.operator("mesh.loop_multi_select", text="Edge Rings", icon = "SELECT_EDGERING").ring = True
        layout.operator("mesh.loop_to_region", text = "Loop Inner Region", icon = "SELECT_LOOPINNER")
        layout.operator("mesh.region_to_loop", text = "Boundary Loop", icon = "SELECT_BOUNDARY")

        layout.separator()

        layout.operator("mesh.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_select_more_less")


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_curve_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "curve.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.curve.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_curve_none(bpy.types.Operator):
    """Deselects everything """       # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "curve.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.curve.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_edit_curve(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("curve.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("curve.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()


        layout.operator("curve.select_linked", text="Linked", icon = "LINKED")
        layout.operator("curve.select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("curve.select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True

        layout.separator()

        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")

        layout.separator()

        layout.operator("curve.select_random", text= "Random", icon = "RANDOMIZE")
        layout.operator("curve.select_nth", icon = "CHECKER_DESELECT")

        layout.separator()

        layout.operator("curve.de_select_first", icon = "SELECT_FIRST")
        layout.operator("curve.de_select_last", icon = "SELECT_LAST")
        layout.operator("curve.select_next", text = "Next", icon = "NEXTACTIVE")
        layout.operator("curve.select_previous", text = "Previous", icon = "PREVIOUSACTIVE")

        layout.separator()

        layout.operator("curve.select_more", text= "More", icon = "SELECTMORE")
        layout.operator("curve.select_less", text= "Less", icon = "SELECTLESS")

class VIEW3D_MT_select_edit_curve_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.select_similar", text="Type", icon = "TYPE").type = 'TYPE'
        layout.operator("curve.select_similar", text="Radius", icon = "RADIUS").type = 'RADIUS'
        layout.operator("curve.select_similar", text="Weight", icon = "MOD_VERTEX_WEIGHT").type = 'WEIGHT'
        layout.operator("curve.select_similar", text="Direction", icon = "SWITCH_DIRECTION").type = 'DIRECTION'


class VIEW3D_MT_select_edit_surface(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("curve.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("curve.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("curve.select_linked", text="Linked", icon = "LINKED")
        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")

        layout.separator()

        layout.operator("curve.select_random", text= "Random", icon = "RANDOMIZE")
        layout.operator("curve.select_nth", icon = "CHECKER_DESELECT")


        layout.separator()

        layout.operator("curve.select_row", text = "Control Point row", icon = "CONTROLPOINTROW")

        layout.separator()

        layout.operator("curve.select_more", text= "More", icon = "SELECTMORE")
        layout.operator("curve.select_less", text= "Less", icon = "SELECTLESS")


class VIEW3D_MT_select_edit_text(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("font.select_all", text="All", icon = "SELECT_ALL")

        layout.separator()

        layout.operator("font.move_select", text = "Line End", icon = "HAND").type = 'LINE_END'
        layout.operator("font.move_select", text = "Line Begin", icon = "HAND").type = 'LINE_BEGIN'

        layout.separator()

        layout.operator("font.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("font.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'

        layout.separator()

        layout.operator("font.move_select", text = "Previous Word", icon = "HAND").type = 'PREVIOUS_WORD'
        layout.operator("font.move_select", text = "Next Word", icon = "HAND").type = 'NEXT_WORD'

        layout.separator()

        layout.operator("font.move_select", text = "Previous Line", icon = "HAND").type = 'PREVIOUS_LINE'
        layout.operator("font.move_select", text = "Next Line", icon = "HAND").type = 'NEXT_LINE'


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_metaball_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_metaball_none(bpy.types.Operator):
    """Deselects everything """           # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_edit_metaball(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mball.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("mball.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("mball.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.menu("VIEW3D_MT_select_edit_metaball_select_similar")

        layout.separator()

        layout.operator("mball.select_random_metaelems", text = "Random", icon = "RANDOMIZE")


class VIEW3D_MT_select_edit_metaball_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("mball.select_similar", text="Type", icon = "TYPE").type = 'TYPE'
        layout.operator("mball.select_similar", text="Radius", icon = "RADIUS").type = 'RADIUS'
        layout.operator("mball.select_similar", text="Stiffness", icon = "BEND").type = 'STIFFNESS'
        layout.operator("mball.select_similar", text="Rotation", icon = "ROTATE").type = 'ROTATION'


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_lattice_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "lattice.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.lattice.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_lattice_none(bpy.types.Operator):
    """Deselects everything """        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "lattice.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.lattice.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_edit_lattice_context_menu(Menu):
    bl_label = "Lattice Context Menu"

    def draw(self, context):
        layout = self.layout

        layout = self.layout

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_edit_lattice_flip")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("lattice.make_regular", icon = 'MAKE_REGULAR')


class VIEW3D_MT_select_edit_lattice(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("lattice.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("lattice.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("lattice.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("lattice.select_mirror", text = "Mirror", icon = "TRANSFORM_MIRROR")
        layout.operator("lattice.select_random", text = "Random", icon = "RANDOMIZE")

        layout.separator()

        layout.operator("lattice.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")

        layout.separator()

        layout.operator("lattice.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("lattice.select_less", text = "Less", icon = "SELECTLESS")


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_armature_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "armature.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.armature.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_armature_none(bpy.types.Operator):
    """Deselects everything """          # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "armature.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.armature.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_edit_armature(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("armature.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("armature.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("armature.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator_menu_enum("armature.select_similar", "type", text="Similar")

        layout.separator()

        layout.operator("armature.select_mirror", text="Mirror Selection", icon = "TRANSFORM_MIRROR").extend = False
        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")

        layout.separator()

        layout.operator("armature.select_linked", text="Linked")

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Parent", icon = "PARENT")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child", icon = "CHILD")
        props.extend = False
        props.direction = 'CHILD'

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Extend Parent", icon = "PARENT")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Extend Child", icon = "CHILD")
        props.extend = True
        props.direction = 'CHILD'

        layout.separator()

        layout.operator("armature.select_more", text="More", icon = "SELECTMORE")
        layout.operator("armature.select_less", text="Less", icon = "SELECTLESS")


# Workaround to separate the tooltips
class VIEW3D_MT_select_gpencil_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "gpencil.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.gpencil.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_gpencil_none(bpy.types.Operator):
    """Deselects everything """          # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "gpencil.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.gpencil.select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_gpencil(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("gpencil.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("gpencil.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("gpencil.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("gpencil.select_linked", text="Linked", icon = "LINKED")
        layout.operator("gpencil.select_alternate", icon = "ALTERNATED")
        layout.menu("VIEW3D_MT_select_gpencil_grouped", text="Grouped")

        if _context.mode == 'VERTEX_GPENCIL':
            layout.operator("gpencil.select_vertex_color", text="Vertex Color")

        layout.separator()

        layout.operator("gpencil.select_first", text = "First", icon = "SELECT_FIRST")
        layout.operator("gpencil.select_last", text = "Last", icon = "SELECT_LAST")

        layout.separator()

        layout.operator("gpencil.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("gpencil.select_less", text = "Less", icon = "SELECTLESS")


class VIEW3D_MT_select_gpencil_grouped(Menu):
    bl_label = "Grouped"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.select_grouped", text="Layer", icon = "LAYER").type = 'LAYER'
        layout.operator("gpencil.select_grouped", text="Color", icon = "COLOR").type = 'MATERIAL'


# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.face_select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.face_select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_none(bpy.types.Operator):
    """Deselects everything """        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.face_select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.face_select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_paint_mask(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("paint.face_select_all", text="All", icon = 'SELECT_ALL').action = 'SELECT'
        layout.operator("paint.face_select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("paint.face_select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("paint.face_select_linked", text="Linked", icon = "LINKED")
        layout.operator("paint.face_select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("paint.face_select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True


# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_vertex_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.vert_select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.vert_select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_vertex_none(bpy.types.Operator):
    """Deselects everything """       # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.vert_select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.vert_select_all(action = 'DESELECT')
        return {'FINISHED'}


class VIEW3D_MT_select_paint_mask_vertex(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("paint.vert_select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("paint.vert_select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("paint.vert_select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("paint.vert_select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")


class VIEW3D_MT_angle_control(Menu):
    bl_label = "Angle Control"

    @classmethod
    def poll(cls, context):
        settings = UnifiedPaintPanel.paint_settings(context)
        if not settings:
            return False

        brush = settings.brush
        tex_slot = brush.texture_slot

        return tex_slot.has_texture_angle and tex_slot.has_texture_angle_source

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        sculpt = (context.sculpt_object is not None)

        tex_slot = brush.texture_slot

        layout.prop(tex_slot, "use_rake", text="Rake")

        if brush.brush_capabilities.has_random_texture_angle and tex_slot.has_random_texture_angle:
            if sculpt:
                if brush.sculpt_capabilities.has_random_texture_angle:
                    layout.prop(tex_slot, "use_random", text="Random")
            else:
                layout.prop(tex_slot, "use_random", text="Random")


class VIEW3D_MT_mesh_add(Menu):
    bl_idname = "VIEW3D_MT_mesh_add"
    bl_label = "Mesh"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.primitive_plane_add", text="Plane", icon='MESH_PLANE')
        layout.operator("mesh.primitive_cube_add", text="Cube", icon='MESH_CUBE')
        layout.operator("mesh.primitive_circle_add", text="Circle", icon='MESH_CIRCLE')
        layout.operator("mesh.primitive_uv_sphere_add", text="UV Sphere", icon='MESH_UVSPHERE')
        layout.operator("mesh.primitive_ico_sphere_add", text="Ico Sphere", icon='MESH_ICOSPHERE')
        layout.operator("mesh.primitive_cylinder_add", text="Cylinder", icon='MESH_CYLINDER')
        layout.operator("mesh.primitive_cone_add", text="Cone", icon='MESH_CONE')
        layout.operator("mesh.primitive_torus_add", text="Torus", icon='MESH_TORUS')

        layout.separator()

        layout.operator("mesh.primitive_grid_add", text="Grid", icon='MESH_GRID')
        layout.operator("mesh.primitive_monkey_add", text="Monkey", icon='MESH_MONKEY')


class VIEW3D_MT_curve_add(Menu):
    bl_idname = "VIEW3D_MT_curve_add"
    bl_label = "Curve"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("curve.primitive_bezier_curve_add", text="Bezier", icon='CURVE_BEZCURVE')
        layout.operator("curve.primitive_bezier_circle_add", text="Circle", icon='CURVE_BEZCIRCLE')

        layout.separator()

        layout.operator("curve.primitive_nurbs_curve_add", text="Nurbs Curve", icon='CURVE_NCURVE')
        layout.operator("curve.primitive_nurbs_circle_add", text="Nurbs Circle", icon='CURVE_NCIRCLE')
        layout.operator("curve.primitive_nurbs_path_add", text="Path", icon='CURVE_PATH')


class VIEW3D_MT_surface_add(Menu):
    bl_idname = "VIEW3D_MT_surface_add"
    bl_label = "Surface"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("surface.primitive_nurbs_surface_curve_add", text="Surface Curve", icon='SURFACE_NCURVE')
        layout.operator("surface.primitive_nurbs_surface_circle_add", text="Surface Circle", icon='SURFACE_NCIRCLE')
        layout.operator("surface.primitive_nurbs_surface_surface_add", text="Surface Patch", icon='SURFACE_NSURFACE')
        layout.operator("surface.primitive_nurbs_surface_cylinder_add", text="Surface Cylinder", icon='SURFACE_NCYLINDER')
        layout.operator("surface.primitive_nurbs_surface_sphere_add", text="Surface Sphere", icon='SURFACE_NSPHERE')
        layout.operator("surface.primitive_nurbs_surface_torus_add", text="Surface Torus", icon='SURFACE_NTORUS')


class VIEW3D_MT_edit_metaball_context_menu(Menu):
    bl_label = "Metaball Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        # Add
        layout.operator("mball.duplicate_move", icon = "DUPLICATE")

        layout.separator()

        # Modify
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        # Remove
        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("mball.delete_metaelems", text="Delete", icon = "DELETE")


class VIEW3D_MT_metaball_add(Menu):
    bl_idname = "VIEW3D_MT_metaball_add"
    bl_label = "Metaball"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.metaball_add", "type")


class TOPBAR_MT_edit_curve_add(Menu):
    bl_idname = "TOPBAR_MT_edit_curve_add"
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, context):
        is_surf = context.active_object.type == 'SURFACE'

        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'

        if is_surf:
            VIEW3D_MT_surface_add.draw(self, context)
        else:
            VIEW3D_MT_curve_add.draw(self, context)


class TOPBAR_MT_edit_armature_add(Menu):
    bl_idname = "TOPBAR_MT_edit_armature_add"
    bl_label = "Armature"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("armature.bone_primitive_add", text="Single Bone", icon='BONE_DATA')


class VIEW3D_MT_armature_add(Menu):
    bl_idname = "VIEW3D_MT_armature_add"
    bl_label = "Armature"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.armature_add", text="Single Bone", icon='BONE_DATA')


class VIEW3D_MT_light_add(Menu):
    bl_idname = "VIEW3D_MT_light_add"
    bl_label = "Light"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.light_add", "type")


class VIEW3D_MT_lightprobe_add(Menu):
    bl_idname = "VIEW3D_MT_lightprobe_add"
    bl_label = "Light Probe"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.lightprobe_add", "type")


class VIEW3D_MT_camera_add(Menu):
    bl_idname = "VIEW3D_MT_camera_add"
    bl_label = "Camera"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.camera_add", text="Camera", icon='OUTLINER_OB_CAMERA')


class VIEW3D_MT_volume_add(Menu):
    bl_idname = "VIEW3D_MT_volume_add"
    bl_label = "Volume"

    def draw(self, _context):
        layout = self.layout
        layout.operator("object.volume_import", text="Import OpenVDB...", icon='VOLUME_DATA')
        layout.operator("object.volume_add", text="Empty", icon='VOLUME_DATA')


class VIEW3D_MT_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, context):
        layout = self.layout

        # note, don't use 'EXEC_SCREEN' or operators won't get the 'v3d' context.

        # Note: was EXEC_AREA, but this context does not have the 'rv3d', which prevents
        #       "align_view" to work on first call (see [#32719]).
        layout.operator_context = 'EXEC_REGION_WIN'

        # layout.operator_menu_enum("object.mesh_add", "type", text="Mesh", icon='OUTLINER_OB_MESH')
        layout.menu("VIEW3D_MT_mesh_add", icon='OUTLINER_OB_MESH')

        # layout.operator_menu_enum("object.curve_add", "type", text="Curve", icon='OUTLINER_OB_CURVE')
        layout.menu("VIEW3D_MT_curve_add", icon='OUTLINER_OB_CURVE')
        # layout.operator_menu_enum("object.surface_add", "type", text="Surface", icon='OUTLINER_OB_SURFACE')
        layout.menu("VIEW3D_MT_surface_add", icon='OUTLINER_OB_SURFACE')
        layout.menu("VIEW3D_MT_metaball_add", text="Metaball", icon='OUTLINER_OB_META')
        layout.operator("object.text_add", text="Text", icon='OUTLINER_OB_FONT')
        if hasattr(bpy.data, "hairs"):
            layout.operator("object.hair_add", text="Hair", icon='OUTLINER_OB_HAIR')
        if hasattr(bpy.data, "pointclouds"):
            layout.operator("object.pointcloud_add", text="Point Cloud", icon='OUTLINER_OB_POINTCLOUD')
        layout.menu("VIEW3D_MT_volume_add", text="Volume", icon='OUTLINER_OB_VOLUME')
        layout.operator_menu_enum("object.gpencil_add", "type", text="Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')
        layout.separator()

        if VIEW3D_MT_armature_add.is_extended():
            layout.menu("VIEW3D_MT_armature_add", icon='OUTLINER_OB_ARMATURE')
        else:
            layout.operator("object.armature_add", text="Armature", icon='OUTLINER_OB_ARMATURE')

        layout.operator("object.add", text="Lattice", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.operator_menu_enum("object.empty_add", "type", text="Empty", icon='OUTLINER_OB_EMPTY')
        layout.menu("VIEW3D_MT_image_add", text="Image", icon='OUTLINER_OB_IMAGE')

        layout.separator()

        layout.operator("object.speaker_add", text="Speaker", icon='OUTLINER_OB_SPEAKER')
        layout.separator()

        if VIEW3D_MT_camera_add.is_extended():
            layout.menu("VIEW3D_MT_camera_add", icon='OUTLINER_OB_CAMERA')
        else:
            VIEW3D_MT_camera_add.draw(self, context)

        layout.menu("VIEW3D_MT_light_add", icon='OUTLINER_OB_LIGHT')

        layout.separator()

        layout.menu("VIEW3D_MT_lightprobe_add", icon='OUTLINER_OB_LIGHTPROBE')

        layout.separator()

        layout.operator_menu_enum("object.effector_add", "type", text="Force Field", icon='OUTLINER_OB_FORCE_FIELD')

        layout.separator()

        has_collections = bool(bpy.data.collections)
        col = layout.column()
        col.enabled = has_collections

        if not has_collections or len(bpy.data.collections) > 10:
            col.operator_context = 'INVOKE_REGION_WIN'
            col.operator(
                "object.collection_instance_add",
                text="Collection Instance" if has_collections else "No Collections to Instance",
                icon='OUTLINER_OB_GROUP_INSTANCE',
            )
        else:
            col.operator_menu_enum(
                "object.collection_instance_add",
                "collection",
                text="Collection Instance",
                icon='OUTLINER_OB_GROUP_INSTANCE',
            )


class VIEW3D_MT_image_add(Menu):
    bl_label = "Add Image"

    def draw(self, _context):
        layout = self.layout
        layout.operator("object.load_reference_image", text="Reference", icon='IMAGE_REFERENCE')
        layout.operator("object.load_background_image", text="Background", icon='IMAGE_BACKGROUND')


class VIEW3D_MT_object_relations(Menu):
    bl_label = "Relations"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.proxy_make", text="Make Proxy", icon='MAKE_PROXY')

        if bpy.app.use_override_library:
            layout.operator("object.make_override_library", text="Make Library Override", icon = "LIBRARY_DATA_OVERRIDE")

        layout.operator("object.make_dupli_face", icon = "MAKEDUPLIFACE")

        layout.separator()

        layout.operator_menu_enum("object.make_local", "type", text="Make Local")
        layout.menu("VIEW3D_MT_make_single_user")

        layout.separator()

        layout.operator("object.data_transfer", icon ='TRANSFER_DATA')
        layout.operator("object.datalayout_transfer", icon ='TRANSFER_DATA_LAYOUT')

class VIEW3D_MT_origin_set(Menu):
    bl_label = "Set Origin"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.origin_set", icon ='GEOMETRY_TO_ORIGIN', text = "Geometry to Origin").type='GEOMETRY_ORIGIN'
        layout.operator("object.origin_set", icon ='ORIGIN_TO_GEOMETRY', text = "Origin to Geometry").type='ORIGIN_GEOMETRY'
        layout.operator("object.origin_set", icon ='ORIGIN_TO_CURSOR', text = "Origin to 3D Cursor").type='ORIGIN_CURSOR'
        layout.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text = "Origin to Center of Mass (Surface)").type='ORIGIN_CENTER_OF_MASS'
        layout.operator("object.origin_set", icon ='ORIGIN_TO_VOLUME', text = "Origin to Center of Mass (Volume)").type='ORIGIN_CENTER_OF_VOLUME'


# ********** Object menu **********

# Workaround to separate the tooltips
class VIEW3D_MT_object_delete_global(bpy.types.Operator):
    """Deletes the selected object(s) globally in all opened scenes"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.delete_global"        # unique identifier for buttons and menu items to reference.
    bl_label = "Delete Global"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.delete(use_global = True)
        return {'FINISHED'}


class VIEW3D_MT_object(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        is_eevee = context.scene.render.engine == 'BLENDER_EEVEE'
        view = context.space_data

        layout.menu("VIEW3D_MT_transform_object")
        layout.menu("VIEW3D_MT_origin_set")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("object.duplicate_move", icon = "DUPLICATE")
        layout.operator("object.duplicate_move_linked", icon = "DUPLICATE")
        layout.operator("object.join", icon ='JOIN')

        layout.separator()

        layout.operator_context = 'EXEC_DEFAULT'
        myvar = layout.operator("object.delete", text="Delete", icon = "DELETE")
        myvar.use_global = False
        myvar.confirm = False
        layout.operator("object.delete_global", text="Delete Global", icon = "DELETE") # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.copybuffer", text="Copy Objects", icon='COPYDOWN')
        layout.operator("view3d.pastebuffer", text="Paste Objects", icon='PASTEDOWN')

        layout.separator()

        layout.menu("VIEW3D_MT_object_parent")
        #layout.menu("VIEW3D_MT_object_collection") # bfa, turned off
        layout.menu("VIEW3D_MT_object_relations")
        layout.menu("VIEW3D_MT_object_constraints")
        layout.menu("VIEW3D_MT_object_track")
        layout.menu("VIEW3D_MT_make_links", text="Make Links")

        # shading just for mesh objects
        if obj is None:
            pass

        elif obj.type == 'MESH':

            layout.separator()

            layout.operator("object.shade_smooth", icon ='SHADING_SMOOTH')
            layout.operator("object.shade_flat", icon ='SHADING_FLAT')

        layout.separator()

        layout.menu("VIEW3D_MT_object_animation")
        layout.menu("VIEW3D_MT_object_rigid_body")

        layout.separator()

        layout.menu("VIEW3D_MT_object_quick_effects")
        layout.menu("VIEW3D_MT_subdivision_set")

        layout.separator()

        layout.menu("VIEW3D_MT_object_convert")

        layout.separator()

        layout.menu("VIEW3D_MT_object_showhide")


        if obj is None:
            pass

        elif obj.type == 'CAMERA':
            layout.operator_context = 'INVOKE_REGION_WIN'

            layout.separator()

            if obj.data.type == 'PERSP':
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Angle", icon = "LENS_ANGLE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.lens"
                props.input_scale = 0.1
                if obj.data.lens_unit == 'MILLIMETERS':
                    props.header_text = "Camera Lens Angle: %.1fmm"
                else:
                    props.header_text = "Camera Lens Angle: %.1f\u00B0"

            else:
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Scale", icon = "LENS_SCALE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.ortho_scale"
                props.input_scale = 0.01
                props.header_text = "Camera Lens Scale: %.3f"

            if not obj.data.dof.focus_object:
                if view and view.camera == obj and view.region_3d.view_perspective == 'CAMERA':
                    props = layout.operator("ui.eyedropper_depth", text="DOF Distance (Pick)", icon = "DOF")
                else:
                    props = layout.operator("wm.context_modal_mouse", text="DOF Distance", icon = "DOF")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.dof.focus_distance"
                    props.input_scale = 0.02
                    props.header_text = "DOF Distance: %.3f"

        elif obj.type in {'CURVE', 'FONT'}:
            layout.operator_context = 'INVOKE_REGION_WIN'

            layout.separator()

            props = layout.operator("wm.context_modal_mouse", text="Extrude Size", icon = "EXTRUDESIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.extrude"
            props.input_scale = 0.01
            props.header_text = "Extrude Size: %.3f"

            props = layout.operator("wm.context_modal_mouse", text="Width Size", icon = "WIDTH_SIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.offset"
            props.input_scale = 0.01
            props.header_text = "Width Size: %.3f"


        elif obj.type == 'EMPTY':
            layout.operator_context = 'INVOKE_REGION_WIN'

            layout.separator()

            props = layout.operator("wm.context_modal_mouse", text="Empty Draw Size", icon = "DRAWSIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "empty_display_size"
            props.input_scale = 0.01
            props.header_text = "Empty Draw Size: %.3f"

        elif obj.type == 'LIGHT':
            light = obj.data
            layout.operator_context = 'INVOKE_REGION_WIN'

            layout.separator()

            emission_node = None
            if light.node_tree:
                for node in light.node_tree.nodes:
                    if getattr(node, "type", None) == 'EMISSION':
                        emission_node = node
                        break

            if is_eevee and not emission_node:
                props = layout.operator("wm.context_modal_mouse", text="Energy", icon = "LIGHT_STRENGTH")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.energy"
                props.header_text = "Light Energy: %.3f"

            if emission_node is not None:
                props = layout.operator("wm.context_modal_mouse", text="Energy", icon = "LIGHT_STRENGTH")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = (
                    "data.node_tree"
                    ".nodes[\"" + emission_node.name + "\"]"
                    ".inputs[\"Strength\"].default_value"
                )
                props.header_text = "Light Energy: %.3f"
                props.input_scale = 0.1

            if light.type == 'AREA':
                props = layout.operator("wm.context_modal_mouse", text="Size X", icon = "LIGHT_SIZE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.size"
                props.header_text = "Light Size X: %.3f"

                if light.shape in {'RECTANGLE', 'ELLIPSE'}:
                    props = layout.operator("wm.context_modal_mouse", text="Size Y", icon = "LIGHT_SIZE")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size_y"
                    props.header_text = "Light Size Y: %.3f"

            elif light.type in {'SPOT', 'POINT', 'SUN'}:
                props = layout.operator("wm.context_modal_mouse", text="Radius", icon = "RADIUS")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.shadow_soft_size"
                props.header_text = "Light Radius: %.3f"

            if light.type == 'SPOT':
                layout.separator()

                props = layout.operator("wm.context_modal_mouse", text="Spot Size", icon = "LIGHT_SIZE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_size"
                props.input_scale = 0.01
                props.header_text = "Spot Size: %.2f"

                props = layout.operator("wm.context_modal_mouse", text="Spot Blend", icon = "SPOT_BLEND")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_blend"
                props.input_scale = -0.01
                props.header_text = "Spot Blend: %.2f"

class VIEW3D_MT_object_convert(Menu):
    bl_label = "Convert To"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        layout.operator_enum("object.convert", "target")

        # check if object exists at all.
        if obj is not None and obj.type == 'GPENCIL':

            layout.separator()

            layout.operator("gpencil.convert", text="Convert Gpencil to Path", icon = "OUTLINER_OB_CURVE").type = 'PATH'
            layout.operator("gpencil.convert", text="Convert Gpencil to Bezier Curves", icon = "OUTLINER_OB_CURVE").type = 'CURVE'
            layout.operator("gpencil.convert", text="Convert Gpencil to Mesh", icon = "OUTLINER_OB_MESH").type = 'POLY'


class VIEW3D_MT_object_animation(Menu):
    bl_label = "Animation"

    def draw(self, _context):
        layout = self.layout

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe", icon= 'KEYFRAMES_INSERT')
        layout.operator("anim.keyframe_delete_v3d", text="Delete Keyframes", icon= 'KEYFRAMES_REMOVE')
        layout.operator("anim.keyframe_clear_v3d", text="Clear Keyframes", icon= 'KEYFRAMES_CLEAR')
        layout.operator("anim.keying_set_active_set", text="Change Keying Set", icon='TRIA_RIGHT')

        layout.separator()

        layout.operator("nla.bake", text="Bake Action", icon= 'BAKE_ACTION')


class VIEW3D_MT_object_rigid_body(Menu):
    bl_label = "Rigid Body"

    def draw(self, _context):
        layout = self.layout

        layout.operator("rigidbody.objects_add", text="Add Active", icon='RIGID_ADD_ACTIVE').type = 'ACTIVE'
        layout.operator("rigidbody.objects_add", text="Add Passive", icon='RIGID_ADD_PASSIVE').type = 'PASSIVE'

        layout.separator()

        layout.operator("rigidbody.objects_remove", text="Remove", icon='RIGID_REMOVE')

        layout.separator()

        layout.operator("rigidbody.shape_change", text="Change Shape", icon='RIGID_CHANGE_SHAPE')
        layout.operator("rigidbody.mass_calculate", text="Calculate Mass", icon='RIGID_CALCULATE_MASS')
        layout.operator("rigidbody.object_settings_copy", text="Copy from Active", icon='RIGID_COPY_FROM_ACTIVE')
        layout.operator("object.visual_transform_apply", text="Apply Transformation", icon='RIGID_APPLY_TRANS')
        layout.operator("rigidbody.bake_to_keyframes", text="Bake To Keyframes", icon='RIGID_BAKE_TO_KEYFRAME')

        layout.separator()

        layout.operator("rigidbody.connect", text="Connect", icon='RIGID_CONSTRAINTS_CONNECT')


class VIEW3D_MT_object_clear(Menu):
    bl_label = "Clear"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.location_clear", text="Location", icon = "CLEARMOVE").clear_delta = False
        layout.operator("object.rotation_clear", text="Rotation", icon = "CLEARROTATE").clear_delta = False
        layout.operator("object.scale_clear", text="Scale", icon = "CLEARSCALE").clear_delta = False

        layout.separator()

        layout.operator("object.origin_clear", text="Origin", icon = "CLEARORIGIN")


class VIEW3D_MT_object_context_menu(Menu):
    bl_label = "Object Context Menu"

    def draw(self, context):

        layout = self.layout
        view = context.space_data

        obj = context.object

        selected_objects_len = len(context.selected_objects)

        # If nothing is selected
        # (disabled for now until it can be made more useful).
        '''
        if selected_objects_len == 0:

            layout.menu("VIEW3D_MT_add", text="Add", text_ctxt=i18n_contexts.operator_default)
            layout.operator("view3d.pastebuffer", text="Paste Objects", icon='PASTEDOWN')

            return
        '''

        # If something is selected
        if obj is not None and obj.type in {'MESH', 'CURVE', 'SURFACE'}:
            layout.operator("object.shade_smooth", text="Shade Smooth", icon ='SHADING_SMOOTH')
            layout.operator("object.shade_flat", text="Shade Flat", icon ='SHADING_FLAT')

            layout.separator()

        if obj is None:
            pass
        elif obj.type == 'MESH':
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator_menu_enum("object.origin_set", text="Set Origin", property="type")

            layout.operator_context = 'INVOKE_DEFAULT'
            # If more than one object is selected
            if selected_objects_len > 1:
                layout.operator("object.join", icon = "JOIN")

            layout.separator()

        elif obj.type == 'CAMERA':
            layout.operator_context = 'INVOKE_REGION_WIN'

            if obj.data.type == 'PERSP':
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Angle", icon = "LENS_ANGLE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.lens"
                props.input_scale = 0.1
                if obj.data.lens_unit == 'MILLIMETERS':
                    props.header_text = "Camera Lens Angle: %.1fmm"
                else:
                    props.header_text = "Camera Lens Angle: %.1f\u00B0"

            else:
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Scale", icon = "LENS_SCALE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.ortho_scale"
                props.input_scale = 0.01
                props.header_text = "Camera Lens Scale: %.3f"

            if not obj.data.dof.focus_object:
                if view and view.camera == obj and view.region_3d.view_perspective == 'CAMERA':
                    props = layout.operator("ui.eyedropper_depth", text="DOF Distance (Pick)", icon = "DOF")
                else:
                    props = layout.operator("wm.context_modal_mouse", text="DOF Distance", icon = "DOF")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.dof_distance"
                    props.input_scale = 0.02
                    props.header_text = "DOF Distance: %.3f"

            layout.separator()

        elif obj.type in {'CURVE', 'FONT'}:
            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Extrude Size", icon = "EXTRUDESIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.extrude"
            props.input_scale = 0.01
            props.header_text = "Extrude Size: %.3f"

            props = layout.operator("wm.context_modal_mouse", text="Width Size", icon = "WIDTH_SIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.offset"
            props.input_scale = 0.01
            props.header_text = "Width Size: %.3f"

            layout.separator()

            layout.operator("object.convert", text="Convert to Mesh", icon = "MESH_DATA").target = 'MESH'
            layout.operator("object.convert", text="Convert to Grease Pencil", icon ="GREASEPENCIL").target = 'GPENCIL'
            layout.operator_menu_enum("object.origin_set", text="Set Origin", property="type", icon ="ORIGIN")

            layout.separator()

        elif obj.type == 'GPENCIL':
            layout.operator("gpencil.convert", text="Convert to Path", icon ="CURVE_PATH").type = 'PATH'
            layout.operator("gpencil.convert", text="Convert to Bezier Curve", icon ="OUTLINER_DATA_CURVE").type = 'CURVE'
            layout.operator("gpencil.convert", text="Convert to Polygon Curve", icon ="OUTLINER_DATA_MESH").type = 'POLY'

            layout.operator_menu_enum("object.origin_set", text="Set Origin", property="type")

            layout.separator()

        elif obj.type == 'EMPTY':
            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Empty Draw Size", icon = "DRAWSIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "empty_display_size"
            props.input_scale = 0.01
            props.header_text = "Empty Draw Size: %.3f"

            layout.separator()

        elif obj.type == 'LIGHT':
            light = obj.data

            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Power", icon = "LIGHT_STRENGTH")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.energy"
            props.header_text = "Light Power: %.3f"

            if light.type == 'AREA':
                props = layout.operator("wm.context_modal_mouse", text="Size X", icon = "LIGHT_SIZE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.size"
                props.header_text = "Light Size X: %.3f"

                if light.shape in {'RECTANGLE', 'ELLIPSE'}:
                    props = layout.operator("wm.context_modal_mouse", text="Size Y", icon = "LIGHT_SIZE")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size_y"
                    props.header_text = "Light Size Y: %.3f"

            elif light.type in {'SPOT', 'POINT'}:
                props = layout.operator("wm.context_modal_mouse", text="Radius", icon = "RADIUS")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.shadow_soft_size"
                props.header_text = "Light Radius: %.3f"

            elif light.type == 'SUN':
                props = layout.operator("wm.context_modal_mouse", text="Angle", icon = "ANGLE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.angle"
                props.header_text = "Light Angle: %.3f"

            if light.type == 'SPOT':
                layout.separator()

                props = layout.operator("wm.context_modal_mouse", text="Spot Size", icon = "LIGHT_SIZE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_size"
                props.input_scale = 0.01
                props.header_text = "Spot Size: %.2f"

                props = layout.operator("wm.context_modal_mouse", text="Spot Blend", icon = "SPOT_BLEND")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_blend"
                props.input_scale = -0.01
                props.header_text = "Spot Blend: %.2f"

            layout.separator()

        layout.operator("view3d.copybuffer", text="Copy Objects", icon='COPYDOWN')
        layout.operator("view3d.pastebuffer", text="Paste Objects", icon='PASTEDOWN')

        layout.separator()

        layout.operator("object.duplicate_move", icon='DUPLICATE')
        layout.operator("object.duplicate_move_linked", icon = "DUPLICATE")

        layout.separator()

        props = layout.operator("wm.call_panel", text="Rename Active Object", icon='RENAME')
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.separator()

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.menu("VIEW3D_MT_object_parent")
        layout.operator_context = 'INVOKE_REGION_WIN'

        if view and view.local_view:
            layout.operator("view3d.localview_remove_from", icon= 'VIEW_REMOVE_LOCAL')
        else:
            layout.operator("object.move_to_collection", icon= 'GROUP')

        layout.separator()

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe", icon= 'KEYFRAMES_INSERT')

        layout.separator()

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("object.delete", text="Delete", icon = "DELETE").use_global = False


class VIEW3D_MT_object_shading(Menu):
    # XXX, this menu is a place to store shading operator in object mode
    bl_label = "Shading"

    def draw(self, _context):
        layout = self.layout
        layout.operator("object.shade_smooth", text="Smooth", icon = "SHADING_SMOOTH")
        layout.operator("object.shade_flat", text="Flat", icon = "SHADING_FLAT")


class VIEW3D_MT_object_apply(Menu):
    bl_label = "Apply"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("object.transform_apply", text="Location", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE")
        props.location, props.rotation, props.scale = True, False, False

        props = layout.operator("object.transform_apply", text="Rotation", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
        props.location, props.rotation, props.scale = False, True, False

        props = layout.operator("object.transform_apply", text="Scale", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
        props.location, props.rotation, props.scale = False, False, True

        props = layout.operator("object.transform_apply", text="All Transforms", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
        props.location, props.rotation, props.scale = True, True, True

        props = layout.operator("object.transform_apply", text="Rotation & Scale", text_ctxt=i18n_contexts.default, icon = "APPLY_ROTSCALE")
        props.location, props.rotation, props.scale = False, True, True

        layout.separator()

        layout.operator("object.transforms_to_deltas", text="Location to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
        layout.operator("object.transforms_to_deltas", text="Rotation to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
        layout.operator("object.transforms_to_deltas", text="Scale to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'
        layout.operator("object.transforms_to_deltas", text="All Transforms to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'
        layout.operator("object.anim_transforms_to_deltas", icon = "APPLYANIDELTA")

        layout.separator()

        layout.operator("object.visual_transform_apply", text="Visual Transform", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
        layout.operator("object.duplicates_make_real", icon = "MAKEDUPLIREAL")


class VIEW3D_MT_object_parent(Menu):
    bl_label = "Parent"

    def draw(self, _context):
        layout = self.layout
        operator_context_default = layout.operator_context

        layout.operator_enum("object.parent_set", "type")

        layout.separator()

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("object.parent_no_inverse_set", icon = "PARENT")
        layout.operator_context = operator_context_default

        layout.separator()

        layout.operator_enum("object.parent_clear", "type")


class VIEW3D_MT_object_track(Menu):
    bl_label = "Track"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.track_set", text = "Damped Track Constraint", icon = "CONSTRAINT_DATA").type = "DAMPTRACK"
        layout.operator("object.track_set", text = "Track to Constraint", icon = "CONSTRAINT_DATA").type = "TRACKTO"
        layout.operator("object.track_set", text = "Lock Track Constraint", icon = "CONSTRAINT_DATA").type = "LOCKTRACK"

        layout.separator()

        layout.operator("object.track_clear", text= "Clear Track", icon = "CLEAR_TRACK").type = 'CLEAR'
        layout.operator("object.track_clear", text= "Clear Track - Keep Transformation", icon = "CLEAR_TRACK").type = 'CLEAR_KEEP_TRANSFORM'


class VIEW3D_MT_object_collection(Menu):
    bl_label = "Collection"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.move_to_collection", icon='GROUP')
        layout.operator("object.link_to_collection", icon='GROUP')

        layout.separator()

        layout.operator("collection.create", icon='COLLECTION_NEW')
        # layout.operator_menu_enum("collection.objects_remove", "collection")  # BUGGY
        layout.operator("collection.objects_remove", icon = "DELETE")
        layout.operator("collection.objects_remove_all", icon = "DELETE")

        layout.separator()

        layout.operator("collection.objects_add_active", icon='GROUP')
        layout.operator("collection.objects_remove_active", icon = "DELETE")


class VIEW3D_MT_object_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.constraint_add_with_targets", icon = "CONSTRAINT_DATA")
        layout.operator("object.constraints_copy", icon = "COPYDOWN")

        layout.separator()

        layout.operator("object.constraints_clear", icon = "CLEAR_CONSTRAINT")


class VIEW3D_MT_object_quick_effects(Menu):
    bl_label = "Quick Effects"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.quick_fur", icon = "HAIR")
        layout.operator("object.quick_explode", icon = "MOD_EXPLODE")
        layout.operator("object.quick_smoke", icon = "MOD_SMOKE")
        layout.operator("object.quick_liquid", icon = "MOD_FLUIDSIM")


# Workaround to separate the tooltips for Show Hide
class VIEW3D_hide_view_set_unselected(bpy.types.Operator):
    """Hides the unselected Object(s)"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.hide_view_set(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_object_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.hide_view_clear", text="Show Hidden", icon = "HIDE_OFF")

        layout.separator()

        layout.operator("object.hide_view_set", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("object.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_make_single_user(Menu):
    bl_label = "Make Single User"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = 'EXEC_DEFAULT'

        props = layout.operator("object.make_single_user", text="Object", icon='MAKE_SINGLE_USER')
        props.object = True
        props.obdata = props.material = props.animation = False

        props = layout.operator("object.make_single_user", text="Object & Data", icon='MAKE_SINGLE_USER')
        props.object = props.obdata = True
        props.material = props.animation = False

        props = layout.operator("object.make_single_user", text="Object & Data & Materials", icon='MAKE_SINGLE_USER')
        props.object = props.obdata = props.material = True
        props.animation = False

        props = layout.operator("object.make_single_user", text="Materials", icon='MAKE_SINGLE_USER')
        props.material = True
        props.object = props.obdata = props.animation = False

        props = layout.operator("object.make_single_user", text="Object Animation", icon='MAKE_SINGLE_USER')
        props.animation = True
        props.object = props.obdata = props.material = False


class VIEW3D_MT_make_links(Menu):
    bl_label = "Make Links"

    def draw(self, _context):
        layout = self.layout
        operator_context_default = layout.operator_context

        if len(bpy.data.scenes) > 10:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("object.make_links_scene", text="Objects to Scene", icon='OUTLINER_OB_EMPTY')
        else:
            layout.operator_context = 'EXEC_REGION_WIN'
            layout.operator_menu_enum("object.make_links_scene", "scene", text="Objects to Scene")

        layout.separator()

        layout.operator_context = operator_context_default

        layout.operator_enum("object.make_links_data", "type")  # inline

        layout.separator()

        layout.operator("object.join_uvs", icon = "TRANSFER_UV")  # stupid place to add this!


class VIEW3D_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = getattr(settings, "brush", None)
        obj = context.active_object
        mesh = context.object.data # face selection masking for painting

        # skip if no active brush
        if not brush:
            layout.label(text="No Brushes currently available. Please add a texture first.", icon='INFO')
            return

        tex_slot = brush.texture_slot
        mask_tex_slot = brush.mask_texture_slot

        # brush tool
        if context.sculpt_object:
            layout.operator("brush.reset", icon = "BRUSH_RESET")

            layout.separator()

            #radial control button brush size
            myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
            myvar.data_path_primary = 'tool_settings.sculpt.brush.size'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.size'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
            myvar.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
            myvar.fill_color_path = ''
            myvar.fill_color_override_path = ''
            myvar.fill_color_override_test_path = ''
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.sculpt.brush'
            myvar.secondary_tex = False

            #radial control button brush strength
            myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
            myvar.data_path_primary = 'tool_settings.sculpt.brush.strength'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
            myvar.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
            myvar.fill_color_path = ''
            myvar.fill_color_override_path = ''
            myvar.fill_color_override_test_path = ''
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.sculpt.brush'
            myvar.secondary_tex = False

            if tex_slot.has_texture_angle:

                #radial control button brushsize for texture paint mode
                myvar = layout.operator("wm.radial_control", text = "Texture Brush Angle", icon = "BRUSHANGLE")
                myvar.data_path_primary = 'tool_settings.sculpt.brush.texture_slot.angle'
                myvar.data_path_secondary = ''
                myvar.use_secondary = ''
                myvar.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
                myvar.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
                myvar.fill_color_path = ''
                myvar.fill_color_override_path = ''
                myvar.fill_color_override_test_path = ''
                myvar.zoom_path = ''
                myvar.image_id = 'tool_settings.sculpt.brush'
                myvar.secondary_tex = False

        elif context.image_paint_object:

            if not brush:
                return

            #radial control button brushsize
            myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
            myvar.data_path_primary = 'tool_settings.image_paint.brush.size'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.size'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
            myvar.rotation_path = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
            myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
            myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
            myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
            myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
            myvar.zoom_path = 'space_data.zoom'
            myvar.image_id = 'tool_settings.image_paint.brush'
            myvar.secondary_tex = True

            #radial control button brushsize
            myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
            myvar.data_path_primary = 'tool_settings.image_paint.brush.strength'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
            myvar.rotation_path = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
            myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
            myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
            myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
            myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.image_paint.brush'
            myvar.secondary_tex = True

            if tex_slot.has_texture_angle:

                #radial control button brushsize for texture paint mode
                myvar = layout.operator("wm.radial_control", text = "Texture Brush Angle", icon = "BRUSHANGLE")
                myvar.data_path_primary = 'tool_settings.image_paint.brush.texture_slot.angle'
                myvar.data_path_secondary = ''
                myvar.use_secondary = ''
                myvar.rotation_path = 'tool_settings.image_paint.brush.texture_slot.angle'
                myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
                myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
                myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
                myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
                myvar.zoom_path = ''
                myvar.image_id = 'tool_settings.image_paint.brush'
                myvar.secondary_tex = False

            if mask_tex_slot.has_texture_angle:

                #radial control button brushsize
                myvar = layout.operator("wm.radial_control", text = "Texure Mask Brush Angle", icon = "BRUSHANGLE")
                myvar.data_path_primary = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
                myvar.data_path_secondary = ''
                myvar.use_secondary = ''
                myvar.rotation_path = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
                myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
                myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
                myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
                myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
                myvar.zoom_path = ''
                myvar.image_id = 'tool_settings.image_paint.brush'
                myvar.secondary_tex = True

        elif context.vertex_paint_object:

            #radial control button brush size
            myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
            myvar.data_path_primary = 'tool_settings.vertex_paint.brush.size'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.size'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
            myvar.rotation_path = 'tool_settings.vertex_paint.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.vertex_paint.brush.cursor_color_add'
            myvar.fill_color_path = 'tool_settings.vertex_paint.brush.color'
            myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
            myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.vertex_paint.brush'
            myvar.secondary_tex = False

            #radial control button brush strength
            myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
            myvar.data_path_primary = 'tool_settings.vertex_paint.brush.strength'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
            myvar.rotation_path = 'tool_settings.vertex_paint.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.vertex_paint.brush.cursor_color_add'
            myvar.fill_color_path = 'tool_settings.vertex_paint.brush.color'
            myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
            myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.vertex_paint.brush'
            myvar.secondary_tex = False

            if tex_slot.has_texture_angle:

                #radial control button brushsize for texture paint mode
                myvar = layout.operator("wm.radial_control", text = "Texture Brush Angle", icon = "BRUSHANGLE")
                myvar.data_path_primary = 'tool_settings.vertex_paint.brush.texture_slot.angle'
                myvar.data_path_secondary = ''
                myvar.use_secondary = ''
                myvar.rotation_path = 'tool_settings.vertex_paint.brush.texture_slot.angle'
                myvar.color_path = 'tool_settings.vertex_paint.brush.cursor_color_add'
                myvar.fill_color_path = 'tool_settings.vertex_paint.brush.color'
                myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
                myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
                myvar.zoom_path = ''
                myvar.image_id = 'tool_settings.vertex_paint.brush'
                myvar.secondary_tex = False


        elif context.weight_paint_object:

            #radial control button brush size
            myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
            myvar.data_path_primary = 'tool_settings.weight_paint.brush.size'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.size'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
            myvar.rotation_path = 'tool_settings.weight_paint.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.weight_paint.brush.cursor_color_add'
            myvar.fill_color_path = ''
            myvar.fill_color_override_path = ''
            myvar.fill_color_override_test_path = ''
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.weight_paint.brush'
            myvar.secondary_tex = False

            #radial control button brush strength
            myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
            myvar.data_path_primary = 'tool_settings.weight_paint.brush.strength'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
            myvar.rotation_path = 'tool_settings.weight_paint.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.weight_paint.brush.cursor_color_add'
            myvar.fill_color_path = ''
            myvar.fill_color_override_path = ''
            myvar.fill_color_override_test_path = ''
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.weight_paint.brush'
            myvar.secondary_tex = False

            #radial control button brush weight
            myvar = layout.operator("wm.radial_control", text = "Brush Weight", icon = "BRUSHSTRENGTH")
            myvar.data_path_primary = 'tool_settings.weight_paint.brush.weight'
            myvar.data_path_secondary = 'tool_settings.unified_paint_settings.weight'
            myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_weight'
            myvar.rotation_path = 'tool_settings.weight_paint.brush.texture_slot.angle'
            myvar.color_path = 'tool_settings.weight_paint.brush.cursor_color_add'
            myvar.fill_color_path = ''
            myvar.fill_color_override_path = ''
            myvar.fill_color_override_test_path = ''
            myvar.zoom_path = ''
            myvar.image_id = 'tool_settings.weight_paint.brush'
            myvar.secondary_tex = False

        if tex_slot.map_mode == 'STENCIL':

            layout.separator()

            layout.operator("brush.stencil_control", text = 'Move Stencil Texture', icon ='TRANSFORM_MOVE').mode = 'TRANSLATION'
            layout.operator("brush.stencil_control", text = 'Rotate Stencil Texture', icon ='TRANSFORM_ROTATE').mode = 'ROTATION'
            layout.operator("brush.stencil_control", text = 'Scale Stencil Texture', icon ='TRANSFORM_SCALE').mode = 'SCALE'
            layout.operator("brush.stencil_reset_transform", text = "Reset Stencil Texture position", icon = "RESET")

        if mask_tex_slot.map_mode == 'STENCIL':

            layout.separator()

            myvar = layout.operator("brush.stencil_control", text = "Move Stencil Mask Texture", icon ='TRANSFORM_MOVE')
            myvar.mode = 'TRANSLATION'
            myvar.texmode = 'SECONDARY'
            myvar = layout.operator("brush.stencil_control", text = "Rotate Stencil Mask Texture", icon ='TRANSFORM_ROTATE')
            myvar.mode = 'ROTATION'
            myvar.texmode = 'SECONDARY'
            myvar = layout.operator("brush.stencil_control", text = "Scale Stencil Mask Texture", icon ='TRANSFORM_SCALE')
            myvar.mode = 'SCALE'
            myvar.texmode = 'SECONDARY'
            layout.operator("brush.stencil_reset_transform", text = "Reset Stencil Mask Texture position", icon = "RESET").mask = True


        # If face selection masking for painting is active
        if mesh.use_paint_mask:

            layout.separator()

            layout.menu("VIEW3D_MT_facemask_showhide") ### show hide for face mask tool

        # Color picker just in vertex and texture paint
        if obj.mode in {'VERTEX_PAINT', 'TEXTURE_PAINT'}:

            layout.separator()

            layout.operator("paint.sample_color", text = "Color Picker", icon='EYEDROPPER')


class VIEW3D_MT_brush_curve_presets(Menu):
    bl_label = "Curve Preset"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings.image_paint
        brush = toolsettings.brush

        layout.operator("brush.curve_preset", icon='SHARPCURVE', text="Sharp").shape = 'SHARP'
        layout.operator("brush.curve_preset", icon='SMOOTHCURVE', text="Smooth").shape = 'SMOOTH'
        layout.operator("brush.curve_preset", icon='NOCURVE', text="Max").shape = 'MAX'
        layout.operator("brush.curve_preset", icon='LINCURVE', text="Line").shape = 'LINE'
        layout.operator("brush.curve_preset", icon='ROOTCURVE', text="Root").shape = 'ROOT'
        layout.operator("brush.curve_preset", icon='SPHERECURVE', text="Round").shape = 'ROUND'

# Show hide menu for face selection masking
class VIEW3D_MT_facemask_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.face_select_reveal", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("paint.face_select_hide", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("paint.face_select_hide", text="Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


class VIEW3D_MT_paint_vertex(Menu):
    bl_label = "Paint"

    def draw(self, _context):
        layout = self.layout

        layout.operator("paint.vertex_color_set", icon = "COLOR")
        layout.operator("paint.vertex_color_smooth", icon = "PARTICLEBRUSH_SMOOTH")
        layout.operator("paint.vertex_color_dirt", icon = "DIRTY_VERTEX")
        layout.operator("paint.vertex_color_from_weight", icon = "VERTCOLFROMWEIGHT")

        layout.separator()

        layout.operator("paint.vertex_color_invert", text="Invert", icon = "REVERSE_COLORS")
        layout.operator("paint.vertex_color_levels", text="Levels", icon = "LEVELS")
        layout.operator("paint.vertex_color_hsv", text="Hue Saturation Value", icon = "HUESATVAL")
        layout.operator("paint.vertex_color_brightness_contrast", text="Bright/Contrast", icon = "BRIGHTNESS_CONTRAST")


class VIEW3D_MT_paint_vertex_specials(Menu):
    bl_label = "Vertex Paint Context Menu"

    def draw(self, context):
        layout = self.layout
        # TODO: populate with useful items.
        layout.operator("paint.vertex_color_set", icon = "COLOR")
        layout.separator()
        layout.operator("paint.vertex_color_smooth", icon = "PARTICLEBRUSH_SMOOTH")


class VIEW3D_MT_paint_texture_specials(Menu):
    bl_label = "Texture Paint Context Menu"

    def draw(self, context):
        layout = self.layout
        # TODO: populate with useful items.
        layout.operator("image.save_dirty", icon = "FILE_TICK")


class VIEW3D_MT_hook(Menu):
    bl_label = "Hooks"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.hook_add_newob", icon = "HOOK_NEW")
        layout.operator("object.hook_add_selob", icon = "HOOK_SELECTED").use_bone = False
        layout.operator("object.hook_add_selob", text="Hook to Selected Object Bone", icon = "HOOK_BONE").use_bone = True

        if any([mod.type == 'HOOK' for mod in context.active_object.modifiers]):
            layout.separator()

            layout.operator_menu_enum("object.hook_assign", "modifier", icon = "HOOK_ASSIGN")
            layout.operator_menu_enum("object.hook_remove", "modifier", icon = "HOOK_REMOVE")

            layout.separator()

            layout.operator_menu_enum("object.hook_select", "modifier", icon = "HOOK_SELECT")
            layout.operator_menu_enum("object.hook_reset", "modifier", icon = "HOOK_RESET")
            layout.operator_menu_enum("object.hook_recenter", "modifier", icon = "HOOK_RECENTER")


class VIEW3D_MT_vertex_group(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.vertex_group_assign_new", icon = "GROUP_VERTEX")

        ob = context.active_object
        if ob.mode == 'EDIT' or (ob.mode == 'WEIGHT_PAINT' and ob.type == 'MESH' and ob.data.use_paint_mask_vertex):
            if ob.vertex_groups.active:
                layout.separator()

                layout.operator("object.vertex_group_assign", text="Assign to Active Group", icon = "ADD_TO_ACTIVE")
                layout.operator("object.vertex_group_remove_from", text="Remove from Active Group", icon = "REMOVE_SELECTED_FROM_ACTIVE_GROUP").use_all_groups = False
                layout.operator("object.vertex_group_remove_from", text="Remove from All", icon = "REMOVE_FROM_ALL_GROUPS").use_all_groups = True

        if ob.vertex_groups.active:
            layout.separator()

            layout.operator_menu_enum("object.vertex_group_set_active", "group", text="Set Active Group")
            layout.operator("object.vertex_group_remove", text="Remove Active Group", icon = "REMOVE_ACTIVE_GROUP").all = False
            layout.operator("object.vertex_group_remove", text="Remove All Groups", icon = "REMOVE_ALL_GROUPS").all = True


class VIEW3D_MT_gpencil_vertex_group(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_AREA'
        ob = context.active_object

        layout.operator("object.vertex_group_add", text="Add New Group", icon = "GROUP_VERTEX")
        ob = context.active_object
        if ob.vertex_groups.active:
            layout.separator()

            layout.operator("gpencil.vertex_group_assign", text="Assign", icon = "ADD_TO_ACTIVE")
            layout.operator("gpencil.vertex_group_remove_from", text="Remove", icon = "REMOVE_SELECTED_FROM_ACTIVE_GROUP")

            layout.operator("gpencil.vertex_group_select", text="Select", icon = "SELECT_ALL" )
            layout.operator("gpencil.vertex_group_deselect", text="Deselect", icon = "SELECT_NONE" )

class VIEW3D_MT_paint_weight_lock(Menu):
    bl_label = "Vertex Group Locks"

    def draw(self, _context):
        layout = self.layout

        op = layout.operator("object.vertex_group_lock", text="Lock All", icon='LOCKED')
        op.action, op.mask = 'LOCK', 'ALL'
        op = layout.operator("object.vertex_group_lock", text="Unlock All", icon='UNLOCKED')
        op.action, op.mask = 'UNLOCK', 'ALL'
        op = layout.operator("object.vertex_group_lock", text="Lock Selected", icon='LOCKED')
        op.action, op.mask = 'LOCK', 'SELECTED'
        op = layout.operator("object.vertex_group_lock", text="Unlock Selected", icon='UNLOCKED')
        op.action, op.mask = 'UNLOCK', 'SELECTED'
        op = layout.operator("object.vertex_group_lock", text="Lock Unselected", icon='LOCKED')
        op.action, op.mask = 'LOCK', 'UNSELECTED'
        op = layout.operator("object.vertex_group_lock",  text="Unlock Unselected", icon='UNLOCKED')
        op.action, op.mask = 'UNLOCK', 'UNSELECTED'
        op = layout.operator("object.vertex_group_lock", text="Lock Only Selected", icon='RESTRICT_SELECT_OFF')
        op.action, op.mask = 'LOCK', 'INVERT_UNSELECTED'
        op = layout.operator("object.vertex_group_lock", text="Lock Only Unselected", icon='RESTRICT_SELECT_ON')
        op.action, op.mask = 'UNLOCK', 'INVERT_UNSELECTED'
        op = layout.operator("object.vertex_group_lock", text="Invert Locks", icon='INVERSE')
        op.action, op.mask = 'INVERT', 'ALL'


class VIEW3D_MT_paint_weight(Menu):
    bl_label = "Weights"

    @staticmethod
    def draw_generic(layout, is_editmode=False):

        if not is_editmode:

            layout.operator("paint.weight_from_bones", text = "Assign Automatic From Bones", icon = "BONE_DATA").type = 'AUTOMATIC'
            layout.operator("paint.weight_from_bones", text = "Assign From Bone Envelopes", icon = "ENVELOPE_MODIFIER").type = 'ENVELOPES'

            layout.separator()

        layout.operator("object.vertex_group_normalize_all", text = "Normalize All", icon='WEIGHT_NORMALIZE_ALL')
        layout.operator("object.vertex_group_normalize", text = "Normalize", icon='WEIGHT_NORMALIZE')

        layout.separator()

        layout.operator("object.vertex_group_mirror", text="Mirror", icon='WEIGHT_MIRROR')
        layout.operator("object.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT')
        layout.operator("object.vertex_group_clean", text="Clean", icon='WEIGHT_CLEAN')

        layout.separator()

        layout.operator("object.vertex_group_quantize", text = "Quantize", icon = "WEIGHT_QUANTIZE")
        layout.operator("object.vertex_group_levels", text = "Levels", icon = 'WEIGHT_LEVELS')
        layout.operator("object.vertex_group_smooth", text = "Smooth", icon='WEIGHT_SMOOTH')

        if not is_editmode:
            props = layout.operator("object.data_transfer", text="Transfer Weights", icon = 'WEIGHT_TRANSFER_WEIGHTS')
            props.use_reverse_transfer = True
            props.data_type = 'VGROUP_WEIGHTS'

        layout.operator("object.vertex_group_limit_total", text="Limit Total", icon='WEIGHT_LIMIT_TOTAL')
        layout.operator("object.vertex_group_fix", text="Fix Deforms", icon='WEIGHT_FIX_DEFORMS')

        if not is_editmode:
            layout.separator()

            layout.operator("paint.weight_set", icon = "MOD_VERTEX_WEIGHT")

        layout.menu("VIEW3D_MT_paint_weight_lock", text="Locks")

    def draw(self, _context):
        self.draw_generic(self.layout, is_editmode=False)


class VIEW3D_MT_subdivision_set(Menu):
    bl_label = "Subdivide"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("object.subdivision_set", text = "Level 0", icon = "SUBDIVIDE_EDGES")
        myvar.relative = False
        myvar.level = 0
        myvar = layout.operator("object.subdivision_set", text = "Level 1", icon = "SUBDIVIDE_EDGES")
        myvar.relative = False
        myvar.level = 1
        myvar = layout.operator("object.subdivision_set", text = "Level 2", icon = "SUBDIVIDE_EDGES")
        myvar.relative = False
        myvar.level = 2
        myvar = layout.operator("object.subdivision_set", text = "Level 3", icon = "SUBDIVIDE_EDGES")
        myvar.relative = False
        myvar.level = 3
        myvar = layout.operator("object.subdivision_set", text = "Level 4", icon = "SUBDIVIDE_EDGES")
        myvar.relative = False
        myvar.level = 4
        myvar = layout.operator("object.subdivision_set", text = "Level 5", icon = "SUBDIVIDE_EDGES")
        myvar.relative = False
        myvar.level = 5


class VIEW3D_MT_paint_weight_specials(Menu):
    bl_label = "Weights Context Menu"

    def draw(self, context):
        layout = self.layout
        # TODO: populate with useful items.
        layout.operator("paint.weight_set")
        layout.separator()
        layout.operator("object.vertex_group_normalize", text="Normalize", icon='WEIGHT_NORMALIZE')
        layout.operator("object.vertex_group_clean", text="Clean", icon='WEIGHT_CLEAN')
        layout.operator("object.vertex_group_smooth", text="Smooth", icon='WEIGHT_SMOOTH')


class VIEW3D_MT_sculpt(Menu):
    bl_label = "Sculpt"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("paint.hide_show", text="Show All", icon = "HIDE_OFF")
        props.action = 'SHOW'
        props.area = 'ALL'

        props = layout.operator("paint.hide_show", text="Show Bounding Box", icon = "HIDE_OFF")
        props.action = 'SHOW'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Hide Bounding Box", icon = "HIDE_ON")
        props.action = 'HIDE'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Hide Masked", icon = "HIDE_ON")
        props.action = 'HIDE'
        props.area = 'MASKED'

        layout.separator()

        layout.menu("VIEW3D_MT_sculpt_set_pivot", text="Set Pivot")

        layout.separator()

        layout.operator("sculpt.optimize", icon = "FILE_REFRESH")


class VIEW3D_MT_mask(Menu):
    bl_label = "Mask"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("paint.mask_flood_fill", text="Invert Mask", icon = "INVERT_MASK")
        props.mode = 'INVERT'

        props = layout.operator("paint.mask_flood_fill", text="Fill Mask", icon = "FILL_MASK")
        props.mode = 'VALUE'
        props.value = 1

        props = layout.operator("paint.mask_flood_fill", text="Clear Mask", icon = "CLEAR_MASK")
        props.mode = 'VALUE'
        props.value = 0

        props = layout.operator("view3d.select_box", text="Box Mask", icon = "BOX_MASK")
        props = layout.operator("paint.mask_lasso_gesture", text="Lasso Mask", icon = "LASSO_MASK")

        layout.separator()

        props = layout.operator("sculpt.mask_filter", text='Smooth Mask', icon = "PARTICLEBRUSH_SMOOTH")
        props.filter_type = 'SMOOTH'
        props.auto_iteration_count = True

        props = layout.operator("sculpt.mask_filter", text='Sharpen Mask', icon = "SHARPEN")
        props.filter_type = 'SHARPEN'
        props.auto_iteration_count = True

        props = layout.operator("sculpt.mask_filter", text='Grow Mask', icon = "SELECTMORE")
        props.filter_type = 'GROW'
        props.auto_iteration_count = True

        props = layout.operator("sculpt.mask_filter", text='Shrink Mask', icon = "SELECTLESS")
        props.filter_type = 'SHRINK'
        props.auto_iteration_count = True

        props = layout.operator("sculpt.mask_filter", text='Increase Contrast', icon = "INC_CONTRAST")
        props.filter_type = 'CONTRAST_INCREASE'
        props.auto_iteration_count = False

        props = layout.operator("sculpt.mask_filter", text='Decrease Contrast', icon = "DEC_CONTRAST")
        props.filter_type = 'CONTRAST_DECREASE'
        props.auto_iteration_count = False

        layout.separator()

        props = layout.operator("sculpt.mask_expand", text="Expand Mask By Topology", icon = "MESH_DATA")
        props.use_normals = False
        props.keep_previous_mask = False
        props.invert = True
        props.smooth_iterations = 2
        props.create_face_set = False

        props = layout.operator("sculpt.mask_expand", text="Expand Mask By Curvature", icon = "CURVE_DATA")
        props.use_normals = True
        props.keep_previous_mask = True
        props.invert = False
        props.smooth_iterations = 0
        props.create_face_set = False

        layout.separator()

        props = layout.operator("mesh.paint_mask_extract", text="Mask Extract", icon = "PACKAGE")

        layout.separator()

        props = layout.operator("mesh.paint_mask_slice", text="Mask Slice", icon = "MOD_MASK")
        props.fill_holes = False
        props.new_object = False
        props = layout.operator("mesh.paint_mask_slice", text="Mask Slice and Fill Holes", icon = "MOD_MASK")
        props.new_object = False
        props = layout.operator("mesh.paint_mask_slice", text="Mask Slice to New Object", icon = "MOD_MASK")

        layout.separator()

        props = layout.operator("sculpt.dirty_mask", text='Dirty Mask', icon = "DIRTY_VERTEX")


class VIEW3D_MT_face_sets(Menu):
    bl_label = "Face Sets"

    def draw(self, _context):
        layout = self.layout


        op = layout.operator("sculpt.face_sets_create", text='Face Set From Masked', icon = "MOD_MASK")
        op.mode = 'MASKED'

        op = layout.operator("sculpt.face_sets_create", text='Face Set From Visible', icon = "FILL_MASK")
        op.mode = 'VISIBLE'

        op = layout.operator("sculpt.face_sets_create", text='Face Set From Edit Mode Selection', icon = "EDITMODE_HLT")
        op.mode = 'SELECTION'

        layout.separator()

        layout.menu("VIEW3D_MT_face_sets_init", text="Init Face Sets")

        layout.separator()

        op = layout.operator("sculpt.face_set_change_visibility", text='Invert Visible Face Sets', icon = "INVERT_MASK")
        op.mode = 'INVERT'

        op = layout.operator("sculpt.face_set_change_visibility", text='Show All Face Sets', icon = "HIDE_OFF")
        op.mode = 'SHOW_ALL'
        op = layout.operator("sculpt.face_set_change_visibility", text='Toggle Visibility', icon = "HIDE_UNSELECTED")
        op.mode = 'TOGGLE'
        op = layout.operator("sculpt.face_set_change_visibility", text='Hide Active Face Sets', icon = "HIDE_ON")
        op.mode = 'HIDE_ACTIVE'

        layout.separator()

        op = layout.operator("sculpt.face_sets_randomize_colors", text='Randomize Colors', icon = "COLOR")


class VIEW3D_MT_sculpt_set_pivot(Menu):
    bl_label = "Sculpt Set Pivot"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("sculpt.set_pivot_position", text="Pivot to Origin", icon = "PIVOT_TO_ORIGIN")
        props.mode = 'ORIGIN'

        props = layout.operator("sculpt.set_pivot_position", text="Pivot to Unmasked", icon = "PIVOT_TO_UNMASKED")
        props.mode = 'UNMASKED'

        props = layout.operator("sculpt.set_pivot_position", text="Pivot to Mask Border", icon = "PIVOT_TO_MASKBORDER")
        props.mode = 'BORDER'

        props = layout.operator("sculpt.set_pivot_position", text="Pivot to Active Vertex", icon = "PIVOT_TO_ACTIVE_VERT")
        props.mode = 'ACTIVE'

        props = layout.operator("sculpt.set_pivot_position", text="Pivot to Surface Under Cursor", icon = "PIVOT_TO_SURFACE")
        props.mode = 'SURFACE'


class VIEW3D_MT_sculpt_specials(Menu):
    bl_label = "Sculpt Context Menu"

    def draw(self, context):
        layout = self.layout
        # TODO: populate with useful items.
        layout.operator("object.shade_smooth", icon = 'SHADING_SMOOTH')
        layout.operator("object.shade_flat", icon = 'SHADING_FLAT')


class VIEW3D_MT_hide_mask(Menu):
    bl_label = "Hide/Mask"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("paint.hide_show", text="Show All", icon = "HIDE_OFF")
        props.action = 'SHOW'
        props.area = 'ALL'

        props = layout.operator("paint.hide_show", text="Hide Bounding Box", icon = "HIDE_ON")
        props.action = 'HIDE'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Show Bounding Box", icon = "HIDE_OFF")
        props.action = 'SHOW'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Hide Masked", icon = "HIDE_ON")
        props.area = 'MASKED'
        props.action = 'HIDE'

        layout.separator()

        props = layout.operator("paint.mask_flood_fill", text="Invert Mask", icon = "INVERT_MASK")
        props.mode = 'INVERT'

        props = layout.operator("paint.mask_flood_fill", text="Fill Mask", icon = "FILL_MASK")
        props.mode = 'VALUE'
        props.value = 1

        props = layout.operator("paint.mask_flood_fill", text="Clear Mask", icon = "CLEAR_MASK")
        props.mode = 'VALUE'
        props.value = 0

        props = layout.operator("view3d.select_box", text="Box Mask", icon = "BOX_MASK")
        props = layout.operator("paint.mask_lasso_gesture", text="Lasso Mask", icon = "LASSO_MASK")


class VIEW3D_MT_face_sets_init(Menu):
    bl_label = "Face Sets Init"

    def draw(self, _context):
        layout = self.layout

        op = layout.operator("sculpt.face_sets_init", text='By Loose Parts', icon = "SELECT_LOOSE")
        op.mode = 'LOOSE_PARTS'

        op = layout.operator("sculpt.face_sets_init", text='By Materials', icon = "MATERIAL_DATA")
        op.mode = 'MATERIALS'

        op = layout.operator("sculpt.face_sets_init", text='By Normals', icon = "RECALC_NORMALS")
        op.mode = 'NORMALS'

        op = layout.operator("sculpt.face_sets_init", text='By UV Seams', icon = "MARK_SEAM")
        op.mode = 'UV_SEAMS'

        op = layout.operator("sculpt.face_sets_init", text='By Edge Creases', icon = "CREASE")
        op.mode = 'CREASES'

        op = layout.operator("sculpt.face_sets_init", text='By Edge Bevel Weight', icon = "BEVEL")
        op.mode = 'BEVEL_WEIGHT'

        op = layout.operator("sculpt.face_sets_init", text='By Sharp Edges', icon = "SELECT_SHARPEDGES")
        op.mode = 'SHARP_EDGES'

        op = layout.operator("sculpt.face_sets_init", text='By Face Maps', icon = "FACE_MAPS")
        op.mode = 'FACE_MAPS'


class VIEW3D_MT_particle(Menu):
    bl_label = "Particle"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        particle_edit = tool_settings.particle_edit

        layout.operator("particle.mirror", icon = "TRANSFORM_MIRROR")

        layout.operator("particle.remove_doubles", icon='REMOVE_DOUBLES')

        layout.separator()

        if particle_edit.select_mode == 'POINT':
            layout.operator("particle.subdivide", icon = "SUBDIVIDE_EDGES")

        layout.operator("particle.unify_length", icon = "RULER")
        layout.operator("particle.rekey", icon = "KEY_HLT")
        layout.operator("particle.weight_set", icon = "MOD_VERTEX_WEIGHT")

        layout.separator()

        layout.menu("VIEW3D_MT_particle_show_hide")

        layout.separator()

        layout.operator("particle.delete", icon = "DELETE")

        layout.separator()


        #radial control button brush size
        myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
        myvar.data_path_primary = 'tool_settings.particle_edit.brush.size'

        #radial control button brush strength
        myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
        myvar.data_path_primary = 'tool_settings.particle_edit.brush.strength'


class VIEW3D_MT_particle_context_menu(Menu):
    bl_label = "Particle Context Menu"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        particle_edit = tool_settings.particle_edit

        layout.operator("particle.rekey", icon = "KEY_HLT")

        layout.separator()

        layout.operator("particle.delete", icon = "DELETE")

        layout.separator()

        layout.operator("particle.remove_doubles", icon='REMOVE_DOUBLES')
        layout.operator("particle.unify_length", icon = "RULER")

        if particle_edit.select_mode == 'POINT':
            layout.operator("particle.subdivide", icon = "SUBDIVIDE_EDGES")

        layout.operator("particle.weight_set", icon = "MOD_VERTEX_WEIGHT")

        layout.separator()

        layout.operator("particle.mirror")

        if particle_edit.select_mode == 'POINT':
            layout.separator()

            layout.operator("particle.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
            layout.operator("particle.select_all", text="None", icon = 'SELECT_NONE').action = 'DESELECT'
            layout.operator("particle.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

            layout.separator()

            layout.operator("particle.select_roots", icon = "SELECT_ROOT")
            layout.operator("particle.select_tips", icon = "SELECT_TIP")

            layout.separator()

            layout.operator("particle.select_random", icon = "RANDOMIZE")

            layout.separator()

            layout.operator("particle.select_more", icon = "SELECTMORE")
            layout.operator("particle.select_less", icon = "SELECTLESS")

            layout.operator("particle.select_linked", text="Select Linked", icon = "LINKED")


# Workaround to separate the tooltips for Show Hide for Particles in Particle mode
class VIEW3D_particle_hide_unselected(bpy.types.Operator):
    """Hide the unselected Particles"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "particle.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.particle.hide(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_particle_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("particle.reveal", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("particle.hide", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("particle.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip

class VIEW3D_MT_pose(Menu):
    bl_label = "Pose"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_pose_transform")
        layout.menu("VIEW3D_MT_pose_apply")

        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.menu("VIEW3D_MT_object_animation")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_slide")
        layout.menu("VIEW3D_MT_pose_propagate")

        layout.separator()

        layout.operator("pose.copy", icon='COPYDOWN')
        layout.operator("pose.paste", icon='PASTEDOWN').flipped = False
        layout.operator("pose.paste", icon='PASTEFLIPDOWN', text="Paste Pose Flipped").flipped = True

        layout.separator()

        layout.menu("VIEW3D_MT_pose_library")
        layout.menu("VIEW3D_MT_pose_motion")
        layout.menu("VIEW3D_MT_pose_group")

        layout.separator()

        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_pose_ik")
        layout.menu("VIEW3D_MT_pose_constraints")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_names")
        layout.operator("pose.quaternions_flip", icon = "FLIP")

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("armature.armature_layers", text="Change Armature Layers", icon = "LAYER")
        layout.operator("pose.bone_layers", text="Change Bone Layers", icon = "LAYER")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_show_hide")
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")


class VIEW3D_MT_pose_transform(Menu):
    bl_label = "Clear Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.transforms_clear", text="All", icon = "CLEAR")
        layout.operator("pose.user_transforms_clear", icon = "CLEAR")

        layout.separator()

        layout.operator("pose.loc_clear", text="Location", icon = "CLEARMOVE")
        layout.operator("pose.rot_clear", text="Rotation", icon = "CLEARROTATE")
        layout.operator("pose.scale_clear", text="Scale", icon = "CLEARSCALE")

        layout.separator()

        layout.operator("pose.user_transforms_clear", text="Reset Unkeyed", icon = "RESET")


class VIEW3D_MT_pose_slide(Menu):
    bl_label = "In-Betweens"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.push_rest", icon = 'PUSH_POSE')
        layout.operator("pose.relax_rest", icon = 'RELAX_POSE')
        layout.operator("pose.push", icon = 'PUSH_POSE')
        layout.operator("pose.relax", icon = 'RELAX_POSE')
        layout.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE')


class VIEW3D_MT_pose_propagate(Menu):
    bl_label = "Propagate"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.propagate", icon = "PROPAGATE").mode = 'WHILE_HELD'

        layout.separator()

        layout.operator("pose.propagate", text="To Next Keyframe", icon = "PROPAGATE").mode = 'NEXT_KEY'
        layout.operator("pose.propagate", text="To Last Keyframe (Make Cyclic)", icon = "PROPAGATE").mode = 'LAST_KEY'

        layout.separator()

        layout.operator("pose.propagate", text="On Selected Keyframes", icon = "PROPAGATE").mode = 'SELECTED_KEYS'

        layout.separator()

        layout.operator("pose.propagate", text="On Selected Markers", icon = "PROPAGATE").mode = 'SELECTED_MARKERS'


class VIEW3D_MT_pose_library(Menu):
    bl_label = "Pose Library"

    def draw(self, _context):
        layout = self.layout

        layout.operator("poselib.browse_interactive", text="Browse Poses", icon = "FILEBROWSER")

        layout.separator()

        layout.operator("poselib.pose_add", text="Add Pose", icon = "LIBRARY")
        layout.operator("poselib.pose_rename", text="Rename Pose", icon='RENAME')
        layout.operator("poselib.pose_remove", text="Remove Pose", icon = "DELETE")


class VIEW3D_MT_pose_motion(Menu):
    bl_label = "Motion Paths"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.paths_calculate", text="Calculate", icon ='MOTIONPATHS_CALCULATE')
        layout.operator("pose.paths_clear", text="Clear", icon ='MOTIONPATHS_CLEAR')


class VIEW3D_MT_pose_group(Menu):
    bl_label = "Bone Groups"

    def draw(self, context):
        layout = self.layout

        pose = context.active_object.pose

        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.group_assign", text="Assign to New Group", icon = "NEW_GROUP").type = 0

        if pose.bone_groups:
            active_group = pose.bone_groups.active_index + 1
            layout.operator("pose.group_assign", text="Assign to Group", icon = "ADD_TO_ACTIVE").type = active_group

            layout.separator()

            # layout.operator_context = 'INVOKE_AREA'
            layout.operator("pose.group_unassign", icon = "REMOVE_SELECTED_FROM_ACTIVE_GROUP")
            layout.operator("pose.group_remove", icon = "REMOVE_FROM_ALL_GROUPS")


class VIEW3D_MT_pose_ik(Menu):
    bl_label = "Inverse Kinematics"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.ik_add", icon= "ADD_IK")
        layout.operator("pose.ik_clear", icon = "CLEAR_IK")


class VIEW3D_MT_pose_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.constraint_add_with_targets", text="Add (With Targets)", icon = "CONSTRAINT_DATA")
        layout.operator("pose.constraints_copy", icon = "COPYDOWN")
        layout.operator("pose.constraints_clear", icon = "CLEAR_CONSTRAINT")

class VIEW3D_MT_pose_names(Menu):
    bl_label = "Names"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("pose.autoside_names", text="AutoName Left/Right", icon = "STRING").axis = 'XAXIS'
        layout.operator("pose.autoside_names", text="AutoName Front/Back", icon = "STRING").axis = 'YAXIS'
        layout.operator("pose.autoside_names", text="AutoName Top/Bottom", icon = "STRING").axis = 'ZAXIS'
        layout.operator("pose.flip_names", icon = "FLIP")


# Workaround to separate the tooltips for Show Hide for Armature in Pose mode
class VIEW3D_MT_pose_hide_unselected(bpy.types.Operator):
    """Hide unselected Bones"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "pose.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.pose.hide(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_pose_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.reveal", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("pose.hide", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("pose.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_pose_apply(Menu):
    bl_label = "Apply"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.armature_apply", icon = "MOD_ARMATURE")
        layout.operator("pose.armature_apply", text="Apply Selected as Rest Pose", icon = "MOD_ARMATURE").selected = True
        layout.operator("pose.visual_transform_apply", icon = "APPLYMOVE")

        layout.separator()

        props = layout.operator("object.assign_property_defaults", icon = "ASSIGN")
        props.process_bones = True


class VIEW3D_MT_pose_context_menu(Menu):
    bl_label = "Pose Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe", icon= 'KEYFRAMES_INSERT')

        layout.separator()

        layout.operator("pose.copy", icon='COPYDOWN')
        layout.operator("pose.paste", icon='PASTEDOWN').flipped = False
        layout.operator("pose.paste", icon='PASTEFLIPDOWN', text="Paste X-Flipped Pose").flipped = True

        layout.separator()

        props = layout.operator("wm.call_panel", text="Rename Active Bone...", icon='RENAME')
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.separator()

        layout.operator("pose.push", icon = 'PUSH_POSE')
        layout.operator("pose.relax", icon = 'RELAX_POSE')
        layout.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE')

        layout.separator()

        layout.operator("pose.paths_calculate", text="Calculate Motion Paths", icon ='MOTIONPATHS_CALCULATE')
        layout.operator("pose.paths_clear", text="Clear Motion Paths", icon ='MOTIONPATHS_CLEAR')

        layout.separator()

        layout.operator("pose.hide", icon = "HIDE_ON").unselected = False
        layout.operator("pose.reveal", icon = "HIDE_OFF")

        layout.separator()

        layout.operator("pose.user_transforms_clear", icon = "CLEAR")


class BoneOptions:
    def draw(self, context):
        layout = self.layout

        options = [
            "show_wire",
            "use_deform",
            "use_envelope_multiply",
            "use_inherit_rotation",
        ]

        if context.mode == 'EDIT_ARMATURE':
            bone_props = bpy.types.EditBone.bl_rna.properties
            data_path_iter = "selected_bones"
            opt_suffix = ""
            options.append("lock")
        else:  # pose-mode
            bone_props = bpy.types.Bone.bl_rna.properties
            data_path_iter = "selected_pose_bones"
            opt_suffix = "bone."

        for opt in options:
            props = layout.operator("wm.context_collection_boolean_set", text=bone_props[opt].name,
                                    text_ctxt=i18n_contexts.default)
            props.data_path_iter = data_path_iter
            props.data_path_item = opt_suffix + opt
            props.type = self.type


class VIEW3D_MT_bone_options_toggle(Menu, BoneOptions):
    bl_label = "Toggle Bone Options"
    type = 'TOGGLE'


class VIEW3D_MT_bone_options_enable(Menu, BoneOptions):
    bl_label = "Enable Bone Options"
    type = 'ENABLE'


class VIEW3D_MT_bone_options_disable(Menu, BoneOptions):
    bl_label = "Disable Bone Options"
    type = 'DISABLE'


# ********** Edit Menus, suffix from ob.type **********


class VIEW3D_MT_edit_mesh(Menu):
    bl_label = "Mesh"

    def draw(self, _context):
        layout = self.layout

        with_bullet = bpy.app.build_options.bullet

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mesh.duplicate_move", text="Duplicate", icon = "DUPLICATE")
        layout.menu("VIEW3D_MT_edit_mesh_extrude")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_merge", text="Merge")
        layout.menu("VIEW3D_MT_edit_mesh_split", text="Split")
        layout.operator_menu_enum("mesh.separate", "type")

        layout.separator()

        layout.operator("mesh.knife_project", icon='KNIFE_PROJECT')

        if with_bullet:
            layout.operator("mesh.convex_hull", icon = "CONVEXHULL")

        layout.separator()

        layout.operator("mesh.symmetrize", icon = "SYMMETRIZE", text = "Symmetrize")
        layout.operator("mesh.symmetry_snap", icon = "SNAP_SYMMETRY")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_normals")
        layout.menu("VIEW3D_MT_edit_mesh_shading")
        layout.menu("VIEW3D_MT_edit_mesh_weights")
        layout.menu("VIEW3D_MT_edit_mesh_sort_elements")
        layout.menu("VIEW3D_MT_subdivision_set")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_show_hide")
        layout.menu("VIEW3D_MT_edit_mesh_clean")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_delete")
        layout.menu("VIEW3D_MT_edit_mesh_dissolve")
        layout.menu("VIEW3D_MT_edit_mesh_select_mode")

class VIEW3D_MT_edit_mesh_sort_elements(Menu):
    bl_label = "Sort Elements"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.sort_elements", text="View Z Axis", icon = "Z_ICON").type = 'VIEW_ZAXIS'
        layout.operator("mesh.sort_elements", text="View X Axis", icon = "X_ICON").type = 'VIEW_XAXIS'
        layout.operator("mesh.sort_elements", text="Cursor Distance", icon = "CURSOR").type = 'CURSOR_DISTANCE'
        layout.operator("mesh.sort_elements", text="Material", icon = "MATERIAL").type = 'MATERIAL'
        layout.operator("mesh.sort_elements", text="Selected", icon = "RESTRICT_SELECT_OFF").type = 'SELECTED'
        layout.operator("mesh.sort_elements", text="Randomize", icon = "RANDOMIZE").type = 'RANDOMIZE'
        layout.operator("mesh.sort_elements", text="Reverse", icon = "SWITCH_DIRECTION").type = 'REVERSE'


class VIEW3D_MT_edit_mesh_context_menu(Menu):
    bl_label = ""

    def draw(self, context):

        def count_selected_items_for_objects_in_mode():
            selected_verts_len = 0
            selected_edges_len = 0
            selected_faces_len = 0
            for ob in context.objects_in_mode_unique_data:
                v, e, f = ob.data.count_selected_items()
                selected_verts_len += v
                selected_edges_len += e
                selected_faces_len += f
            return (selected_verts_len, selected_edges_len, selected_faces_len)

        is_vert_mode, is_edge_mode, is_face_mode = context.tool_settings.mesh_select_mode
        selected_verts_len, selected_edges_len, selected_faces_len = count_selected_items_for_objects_in_mode()

        del count_selected_items_for_objects_in_mode

        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        # If nothing is selected
        # (disabled for now until it can be made more useful).
        '''
        # If nothing is selected
        if not (selected_verts_len or selected_edges_len or selected_faces_len):
            layout.menu("VIEW3D_MT_mesh_add", text="Add", text_ctxt=i18n_contexts.operator_default)

            return
        '''

        # Else something is selected

        row = layout.row()

        if is_vert_mode:
            col = row.column()

            col.label(text="Vertex Context Menu", icon='VERTEXSEL')
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES")

            col.separator()

            col.operator("mesh.extrude_vertices_move", text="Extrude Vertices", icon='EXTRUDE_REGION')
            col.operator("mesh.bevel", text="Bevel Vertices", icon='BEVEL').vertex_only = True

            if selected_verts_len > 1:
                col.separator()
                col.operator("mesh.edge_face_add", text="Make Edge/Face", icon='MAKE_EDGEFACE')
                col.operator("mesh.vert_connect_path", text="Connect Vertex Path", icon = "VERTEXCONNECTPATH")
                col.operator("mesh.vert_connect", text="Connect Vertex Pairs", icon = "VERTEXCONNECT")

            col.separator()

            # Deform Operators
            col.operator("transform.push_pull", text="Push/Pull", icon = 'PUSH_PULL')
            col.operator("transform.shrink_fatten", text="Shrink/Fatten", icon = 'SHRINK_FATTEN')
            col.operator("transform.shear", text="Shear", icon = "SHEAR")
            col.operator_context = 'EXEC_DEFAULT'
            col.operator("transform.vertex_random", text="Randomize Vertices")
            col.operator_context = 'INVOKE_REGION_WIN'
            col.operator("mesh.vertices_smooth_laplacian", text="Smooth Laplacian", icon = "SMOOTH_LAPLACIAN")

            col.separator()

            col.menu("VIEW3D_MT_snap", text="Snap Vertices")
            col.operator("transform.mirror", text="Mirror Vertices", icon='TRANSFORM_MIRROR')

            col.separator()

            # Removal Operators
            if selected_verts_len > 1:
                col.menu("VIEW3D_MT_edit_mesh_merge", text="Merge Vertices")
            col.operator("mesh.split", icon = "SPLIT")
            col.operator_menu_enum("mesh.separate", "type")
            col.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS')
            col.operator("mesh.delete", text="Delete Vertices", icon = "DELETE").type = 'VERT'

        if is_edge_mode:
            render = context.scene.render

            col = row.column()
            col.label(text="Edge Context Menu", icon='EDGESEL')
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES")

            col.separator()

            col.operator("mesh.extrude_edges_move", text="Extrude Edges", icon='EXTRUDE_REGION')
            col.operator("mesh.bevel", text="Bevel Edges", icon = "BEVEL").vertex_only = False
            if selected_edges_len >= 2:
                col.operator("mesh.bridge_edge_loops", icon = "BRIDGE_EDGELOOPS")
            if selected_edges_len >= 1:
                col.operator("mesh.edge_face_add", text="Make Edge/Face", icon='MAKE_EDGEFACE')
            if selected_edges_len >= 2:
                col.operator("mesh.fill", icon = "FILL")

            col.separator()

            col.operator("mesh.loopcut_slide", icon = "LOOP_CUT_AND_SLIDE")
            col.operator("mesh.offset_edge_loops_slide", icon = "SLIDE_EDGE")

            col.separator()

            col.operator("mesh.knife_tool", icon = 'KNIFE')

            col.separator()

            # Deform Operators
            col.operator("mesh.edge_rotate", text="Rotate Edge CW", icon = "ROTATECW").use_ccw = False
            col.operator("mesh.edge_split", icon = "SPLITEDGE")

            col.separator()

            # Edge Flags
            col.operator("transform.edge_crease", icon = "CREASE")
            col.operator("transform.edge_bevelweight", icon = "BEVEL")

            col.separator()

            col.operator("mesh.mark_seam").clear = False
            col.operator("mesh.mark_seam", text="Clear Seam").clear = True

            col.separator()

            col.operator("mesh.mark_sharp", icon = "MARKSHARPEDGES")
            col.operator("mesh.mark_sharp", text="Clear Sharp", icon = "CLEARSHARPEDGES").clear = True

            if render.use_freestyle:
                col.separator()

                col.operator("mesh.mark_freestyle_edge", icon = "MARK_FS_EDGE").clear = False
                col.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge", icon = "CLEAR_FS_EDGE").clear = True

            col.separator()

            # Removal Operators
            col.operator("mesh.unsubdivide", icon = "UNSUBDIVIDE")
            col.operator("mesh.split", icon = "SPLIT")
            col.operator_menu_enum("mesh.separate", "type")
            col.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES')
            col.operator("mesh.delete", text="Delete Edges", icon = "DELETE").type = 'EDGE'

        if is_face_mode:
            col = row.column()

            col.label(text="Face Context Menu", icon='FACESEL')
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES")

            col.separator()

            col.operator("view3d.edit_mesh_extrude_move_normal", text="Extrude Faces", icon = 'EXTRUDE_REGION')
            col.operator("view3d.edit_mesh_extrude_move_shrink_fatten", text="Extrude Faces Along Normals", icon = 'EXTRUDE_REGION')
            col.operator("mesh.extrude_faces_move", text="Extrude Individual Faces", icon = 'EXTRUDE_REGION')

            col.operator("mesh.poke", icon = "POKEFACES")

            if selected_faces_len >= 2:
                col.operator("mesh.bridge_edge_loops", text="Bridge Faces", icon = "BRIDGE_EDGELOOPS")

            col.separator()

            # Modify Operators
            col.menu("VIEW3D_MT_uv_map", text="UV Unwrap Faces")

            col.separator()

            props = col.operator("mesh.quads_convert_to_tris", icon = "TRIANGULATE")
            props.quad_method = props.ngon_method = 'BEAUTY'
            col.operator("mesh.tris_convert_to_quads", icon = "TRISTOQUADS")

            col.separator()

            col.operator("mesh.faces_shade_smooth", icon = 'SHADING_SMOOTH')
            col.operator("mesh.faces_shade_flat", icon = 'SHADING_FLAT')

            col.separator()

            # Removal Operators
            col.operator("mesh.unsubdivide", icon = "UNSUBDIVIDE")
            col.operator("mesh.split", icon = "SPLIT")
            col.operator_menu_enum("mesh.separate", "type")
            col.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES')
            col.operator("mesh.delete", text="Delete Faces", icon = "DELETE").type = 'FACE'


class VIEW3D_MT_edit_mesh_select_mode(Menu):
    bl_label = "Mesh Select Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.select_mode", text="Vertex", icon='VERTEXSEL').type = 'VERT'
        layout.operator("mesh.select_mode", text="Edge", icon='EDGESEL').type = 'EDGE'
        layout.operator("mesh.select_mode", text="Face", icon='FACESEL').type = 'FACE'


class VIEW3D_MT_edit_mesh_extrude_dupli(bpy.types.Operator):
    """Duplicate or Extrude to Cursor\nCreates a slightly rotated copy of the current mesh selection\nThe tool can also extrude the selected geometry, dependant of the selection\nHotkey tool! """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.dupli_extrude_cursor_norotate"        # unique identifier for buttons and menu items to reference.
    bl_label = "Duplicate or Extrude to Cursor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.dupli_extrude_cursor('INVOKE_DEFAULT',rotate_source = False)
        return {'FINISHED'}

class VIEW3D_MT_edit_mesh_extrude_dupli_rotate(bpy.types.Operator):
    """Duplicate or Extrude to Cursor Rotated\nCreates a slightly rotated copy of the current mesh selection, and rotates the source slightly\nThe tool can also extrude the selected geometry, dependant of the selection\nHotkey tool!"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.dupli_extrude_cursor_rotate"        # unique identifier for buttons and menu items to reference.
    bl_label = "Duplicate or Extrude to Cursor Rotated"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.dupli_extrude_cursor('INVOKE_DEFAULT', rotate_source = True)
        return {'FINISHED'}



class VIEW3D_MT_edit_mesh_extrude(Menu):
    bl_label = "Extrude"

    _extrude_funcs = {
        'VERT': lambda layout:
            layout.operator("mesh.extrude_vertices_move", text="Extrude Vertices", icon='EXTRUDE_REGION'),
        'EDGE': lambda layout:
            layout.operator("mesh.extrude_edges_move", text="Extrude Edges", icon='EXTRUDE_REGION'),
        'DUPLI_EXTRUDE': lambda layout:
            layout.operator("mesh.dupli_extrude_cursor_norotate", text="Dupli Extrude", icon='DUPLI_EXTRUDE'),
        'DUPLI_EX_ROTATE': lambda layout:
            layout.operator("mesh.dupli_extrude_cursor_rotate", text="Dupli Extrude Rotate", icon='DUPLI_EXTRUDE_ROTATE'),
    }

    @staticmethod
    def extrude_options(context):
        tool_settings = context.tool_settings
        select_mode = tool_settings.mesh_select_mode
        mesh = context.object.data

        menu = []
        if mesh.total_edge_sel and (select_mode[0] or select_mode[1]):
            menu += ['EDGE']
        if mesh.total_vert_sel and select_mode[0]:
            menu += ['VERT']
        menu += ['DUPLI_EXTRUDE', 'DUPLI_EX_ROTATE']

        # should never get here
        return menu

    def draw(self, context):
        from math import pi

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        for menu_id in self.extrude_options(context):
            self._extrude_funcs[menu_id](layout)

        layout.separator()

        layout.operator("mesh.extrude_repeat", icon = "REPEAT")
        layout.operator("mesh.spin", icon = "SPIN").angle = pi * 2


class VIEW3D_MT_edit_mesh_vertices(Menu):
    bl_label = "Vertex"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.edge_face_add", text="Make Edge/Face", icon='MAKE_EDGEFACE')
        layout.operator("mesh.vert_connect_path", text = "Connect Vertex Path", icon = "VERTEXCONNECTPATH")
        layout.operator("mesh.vert_connect", text = "Connect Vertex Pairs", icon = "VERTEXCONNECT")

        layout.separator()

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("mesh.vertices_smooth_laplacian", text="Smooth Laplacian", icon = "SMOOTH_LAPLACIAN")
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.separator()

        layout.operator("mesh.blend_from_shape", icon = "BLENDFROMSHAPE")
        layout.operator("mesh.shape_propagate_to_all", text="Propagate to Shapes", icon = "SHAPEPROPAGATE")

        layout.separator()

        layout.menu("VIEW3D_MT_vertex_group")
        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")


class VIEW3D_MT_edit_mesh_edges_data(Menu):
    bl_label = "Edge Data"

    def draw(self, context):
        layout = self.layout

        render = context.scene.render

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("transform.edge_crease", icon = "CREASE")
        layout.operator("transform.edge_bevelweight", icon = "BEVEL")

        layout.separator()

        layout.operator("mesh.mark_seam", icon = 'MARK_SEAM').clear = False
        layout.operator("mesh.mark_seam", text="Clear Seam", icon = 'CLEAR_SEAM').clear = True

        layout.separator()

        layout.operator("mesh.mark_sharp", icon = "MARKSHARPEDGES")
        layout.operator("mesh.mark_sharp", text="Clear Sharp", icon = "CLEARSHARPEDGES").clear = True

        layout.operator("mesh.mark_sharp", text="Mark Sharp from Vertices").use_verts = True
        props = layout.operator("mesh.mark_sharp", text="Clear Sharp from Vertices", icon = "CLEARSHARPEDGES")
        props.use_verts = True
        props.clear = True

        if render.use_freestyle:
            layout.separator()

            layout.operator("mesh.mark_freestyle_edge", icon = "MARK_FS_EDGE").clear = False
            layout.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge", icon = "CLEAR_FS_EDGE").clear = True


class VIEW3D_MT_edit_mesh_edges(Menu):
    bl_label = "Edge"

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.bridge_edge_loops", icon = "BRIDGE_EDGELOOPS")
        layout.operator("mesh.screw", icon = "MOD_SCREW")

        layout.separator()

        layout.operator("mesh.subdivide", icon='SUBDIVIDE_EDGES')
        layout.operator("mesh.subdivide_edgering", icon = "SUBDIV_EDGERING")
        layout.operator("mesh.unsubdivide", icon = "UNSUBDIVIDE")

        layout.separator()

        layout.operator("mesh.edge_rotate", text="Rotate Edge CW", icon = "ROTATECW").use_ccw = False
        layout.operator("mesh.edge_rotate", text="Rotate Edge CCW", icon = "ROTATECW").use_ccw = True

        layout.operator("mesh.offset_edge_loops_slide", icon = "OFFSET_EDGE_SLIDE")

        layout.separator()

        layout.operator("transform.edge_crease", icon = "CREASE")
        layout.operator("transform.edge_bevelweight", icon = "BEVEL")

        layout.separator()

        layout.operator("mesh.mark_sharp", icon = "MARKSHARPEDGES")
        layout.operator("mesh.mark_sharp", text="Clear Sharp", icon = "CLEARSHARPEDGES").clear = True

        layout.operator("mesh.mark_sharp", text="Mark Sharp from Vertices", icon = "MARKSHARPEDGES").use_verts = True
        props = layout.operator("mesh.mark_sharp", text="Clear Sharp from Vertices", icon = "CLEARSHARPEDGES")
        props.use_verts = True
        props.clear = True

        if with_freestyle:
            layout.separator()

            layout.operator("mesh.mark_freestyle_edge", icon = "MARK_FS_EDGE").clear = False
            layout.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge", icon = "CLEAR_FS_EDGE").clear = True


class VIEW3D_MT_edit_mesh_faces_data(Menu):
    bl_label = "Face Data"

    def draw(self, _context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.colors_rotate", icon = "ROTATE_COLORS")
        layout.operator("mesh.colors_reverse", icon = "REVERSE_COLORS")

        layout.separator()

        layout.operator("mesh.uvs_rotate", icon = "ROTATE_UVS")
        layout.operator("mesh.uvs_reverse", icon = "REVERSE_UVS")

        layout.separator()

        if with_freestyle:
            layout.operator("mesh.mark_freestyle_face", icon = "MARKFSFACE").clear = False
            layout.operator("mesh.mark_freestyle_face", text="Clear Freestyle Face", icon = "CLEARFSFACE").clear = True


class VIEW3D_MT_edit_mesh_faces(Menu):
    bl_label = "Face"
    bl_idname = "VIEW3D_MT_edit_mesh_faces"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.poke", icon = "POKEFACES")

        layout.separator()

        props = layout.operator("mesh.quads_convert_to_tris", icon = "TRIANGULATE")
        props.quad_method = props.ngon_method = 'BEAUTY'
        layout.operator("mesh.tris_convert_to_quads", icon = "TRISTOQUADS")
        layout.operator("mesh.solidify", text="Solidify Faces", icon = "SOLIDIFY")
        layout.operator("mesh.wireframe", icon = "WIREFRAME")

        layout.separator()

        layout.operator("mesh.fill", icon = "FILL")
        layout.operator("mesh.fill_grid", icon = "GRIDFILL")
        layout.operator("mesh.beautify_fill", icon = "BEAUTIFY")

        layout.separator()

        layout.operator("mesh.intersect", icon = "INTERSECT")
        layout.operator("mesh.intersect_boolean", icon = "BOOLEAN_INTERSECT")

        layout.separator()

        layout.operator("mesh.face_split_by_edges", icon = "SPLITBYEDGES")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_faces_data")


# Workaround to separate the tooltips for Recalculate Outside and Recalculate Inside
class VIEW3D_normals_make_consistent_inside(bpy.types.Operator):
    """Make selected faces and normals point inside the mesh"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.normals_recalculate_inside"        # unique identifier for buttons and menu items to reference.
    bl_label = "Recalculate Inside"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.normals_make_consistent(inside=True)
        return {'FINISHED'}


class VIEW3D_MT_edit_mesh_normals_select_strength(Menu):
    bl_label = "Select by Face Strength"

    def draw(self, _context):
        layout = self.layout

        op = layout.operator("mesh.mod_weighted_strength", text="Weak", icon='FACESEL')
        op.set = False
        op.face_strength = 'WEAK'

        op = layout.operator("mesh.mod_weighted_strength", text="Medium", icon='FACESEL')
        op.set = False
        op.face_strength = 'MEDIUM'

        op = layout.operator("mesh.mod_weighted_strength", text="Strong", icon='FACESEL')
        op.set = False
        op.face_strength = 'STRONG'


class VIEW3D_MT_edit_mesh_normals_set_strength(Menu):
    bl_label = "Select by Face Strength"

    def draw(self, _context):
        layout = self.layout

        op = layout.operator("mesh.mod_weighted_strength", text="Weak", icon='NORMAL_SETSTRENGTH')
        op.set = True
        op.face_strength = 'WEAK'

        op = layout.operator("mesh.mod_weighted_strength", text="Medium", icon='NORMAL_SETSTRENGTH')
        op.set = True
        op.face_strength = 'MEDIUM'

        op = layout.operator("mesh.mod_weighted_strength", text="Strong", icon='NORMAL_SETSTRENGTH')
        op.set = True
        op.face_strength = 'STRONG'


class VIEW3D_MT_edit_mesh_normals_average(Menu):
    bl_label = "Average"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.average_normals", text="Custom Normal", icon = "NORMAL_AVERAGE").average_type = 'CUSTOM_NORMAL'
        layout.operator("mesh.average_normals", text="Face Area", icon = "NORMAL_AVERAGE").average_type = 'FACE_AREA'
        layout.operator("mesh.average_normals", text="Corner Angle", icon = "NORMAL_AVERAGE").average_type = 'CORNER_ANGLE'


class VIEW3D_MT_edit_mesh_normals(Menu):
    bl_label = "Normals"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.normals_make_consistent", text="Recalculate Outside", icon = 'RECALC_NORMALS').inside = False
        layout.operator("mesh.normals_recalculate_inside", text="Recalculate Inside", icon = 'RECALC_NORMALS_INSIDE') # bfa - separated tooltip
        layout.operator("mesh.flip_normals", text = "Flip", icon = 'FLIP_NORMALS')

        layout.separator()

        layout.operator("mesh.set_normals_from_faces", text="Set From Faces", icon = 'SET_FROM_FACES')

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("transform.rotate_normal", text="Rotate", icon = "NORMAL_ROTATE")
        layout.operator("mesh.point_normals", text="Point normals to target", icon = "NORMAL_TARGET")

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("mesh.merge_normals", text="Merge", icon = "MERGE")
        layout.operator("mesh.split_normals", text="Split", icon = "SPLIT")
        layout.menu("VIEW3D_MT_edit_mesh_normals_average", text="Average")

        layout.separator()

        layout.operator("mesh.normals_tools", text="Copy Vectors", icon = "COPYDOWN").mode = 'COPY'
        layout.operator("mesh.normals_tools", text="Paste Vectors", icon = "PASTEDOWN").mode = 'PASTE'
        layout.operator("mesh.smooth_normals", text="Smooth Vectors", icon = "NORMAL_SMOOTH")
        layout.operator("mesh.normals_tools", text="Reset Vectors", icon = "RESET").mode = 'RESET'

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_normals_select_strength", text="Select by Face Strength")
        layout.menu("VIEW3D_MT_edit_mesh_normals_set_strength", text="Set Face Strength")


class VIEW3D_MT_edit_mesh_shading(Menu):
    bl_label = "Shading"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.faces_shade_smooth", icon = 'SHADING_SMOOTH')
        layout.operator("mesh.faces_shade_flat", icon = 'SHADING_FLAT')

        layout.separator()

        layout.operator("mesh.mark_sharp", text="Smooth Edges", icon = 'SHADING_SMOOTH').clear = True
        layout.operator("mesh.mark_sharp", text="Sharp Edges", icon = 'SHADING_FLAT')

        layout.separator()

        props = layout.operator("mesh.mark_sharp", text="Smooth Vertices", icon = 'SHADING_SMOOTH')
        props.use_verts = True
        props.clear = True

        layout.operator("mesh.mark_sharp", text="Sharp Vertices", icon = 'SHADING_FLAT').use_verts = True


class VIEW3D_MT_edit_mesh_weights(Menu):
    bl_label = "Weights"

    def draw(self, _context):
        VIEW3D_MT_paint_weight.draw_generic(self.layout, is_editmode=True)


class VIEW3D_MT_edit_mesh_clean(Menu):
    bl_label = "Clean Up"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.delete_loose", icon = "DELETE")

        layout.separator()

        layout.operator("mesh.decimate", icon = "DECIMATE")
        layout.operator("mesh.dissolve_degenerate", icon = "DEGENERATE_DISSOLVE")
        layout.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED')
        layout.operator("mesh.face_make_planar", icon = "MAKE_PLANAR")

        layout.separator()

        layout.operator("mesh.vert_connect_nonplanar", icon = "SPLIT_NONPLANAR")
        layout.operator("mesh.vert_connect_concave", icon = "SPLIT_CONCAVE")
        layout.operator("mesh.fill_holes", icon = "FILL_HOLE")


class VIEW3D_MT_edit_mesh_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("mesh.delete", "type")

        layout.separator()

        layout.operator("mesh.delete_edgeloop", text="Edge Loops", icon = "DELETE")


class VIEW3D_MT_edit_mesh_dissolve(Menu):
    bl_label = "Dissolve"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS')
        layout.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES')
        layout.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES')

        layout.separator()

        layout.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED')

        layout.separator()

        layout.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE')


# Workaround to separate the tooltips for Show Hide for Mesh in Edit Mode
class VIEW3D_mesh_hide_unselected(bpy.types.Operator):
    """Hide unselected geometry in Edit Mode"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.hide(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_edit_mesh_merge(Menu):
    bl_label = "Merge"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("mesh.merge", "type")

        layout.separator()

        layout.operator("mesh.remove_doubles", text="By Distance", icon = "REMOVE_DOUBLES")


class VIEW3D_MT_edit_mesh_split(Menu):
    bl_label = "Split"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.split", text="Selection", icon = "SPLIT")

        layout.separator()

        layout.operator_enum("mesh.edge_split", "type")


class VIEW3D_MT_edit_mesh_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.reveal", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("mesh.hide", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("mesh.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_edit_gpencil_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("gpencil.delete", "type")

        layout.separator()

        layout.operator("gpencil.delete", text="Delete Active Keyframe (Active Layer)", icon = 'DELETE').type = 'FRAME'
        layout.operator("gpencil.active_frames_delete_all", text="Delete Active Keyframes (All Layers)", icon = 'DELETE')


class VIEW3D_MT_sculpt_gpencil_copy(Menu):
    bl_label = "Copy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("gpencil.copy", text="Copy", icon='COPYDOWN')


# Edit Curve
# draw_curve is used by VIEW3D_MT_edit_curve and VIEW3D_MT_edit_surface


def draw_curve(self, _context):
    layout = self.layout

    edit_object = _context.edit_object

    layout.menu("VIEW3D_MT_transform")
    layout.menu("VIEW3D_MT_mirror")
    layout.menu("VIEW3D_MT_snap")

    layout.separator()

    if edit_object.type == 'SURFACE':
        layout.operator("curve.spin", icon = 'SPIN')
    layout.operator("curve.duplicate_move", text = "Duplicate", icon = "DUPLICATE")

    layout.separator()

    layout.operator("curve.split", icon = "SPLIT")
    layout.operator("curve.separate", icon = "SEPARATE")

    layout.separator()

    layout.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC')
    if edit_object.type == 'CURVE':
        layout.operator("curve.decimate", icon = "DECIMATE")
        layout.operator_menu_enum("curve.spline_type_set", "type")

    layout.separator()

    if edit_object.type == 'CURVE':
        layout.operator("transform.tilt", icon = "TILT")
        layout.operator("curve.tilt_clear", icon = "CLEAR_TILT")

    layout.separator()

    if edit_object.type == 'CURVE':
        layout.menu("VIEW3D_MT_edit_curve_handle_type_set")
        layout.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS')

    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_show_hide")

    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_delete")
    if edit_object.type == 'CURVE':
        layout.operator("curve.dissolve_verts", icon='DISSOLVE_VERTS')


class VIEW3D_MT_edit_curve(Menu):
    bl_label = "Curve"

    draw = draw_curve


class VIEW3D_MT_edit_curve_ctrlpoints(Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type in {'CURVE', 'SURFACE'}:
            layout.operator("curve.extrude_move", text = "Extrude Curve", icon = 'EXTRUDE_REGION')

            layout.separator()

            layout.operator("curve.make_segment", icon = "MAKE_CURVESEGMENT")

            layout.separator()

            if edit_object.type == 'CURVE':
                layout.operator("transform.tilt", icon = 'TILT')
                layout.operator("curve.tilt_clear",icon = "CLEAR_TILT")

                layout.separator()

                layout.menu("VIEW3D_MT_edit_curve_handle_type_set")
                layout.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS')

                layout.separator()

            layout.operator("curve.smooth", icon = 'SHADING_SMOOTH')
            if edit_object.type == 'CURVE':
                layout.operator("curve.smooth_weight", icon = "SMOOTH_WEIGHT")
                layout.operator("curve.smooth_radius", icon = "SMOOTH_RADIUS")
                layout.operator("curve.smooth_tilt", icon = "SMOOTH_TILT")

            layout.separator()

        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")


class VIEW3D_MT_edit_curve_handle_type_set(Menu):
    bl_label = "Set Handle Type"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.handle_type_set", icon = 'HANDLE_AUTO', text="Automatic").type = 'AUTOMATIC'
        layout.operator("curve.handle_type_set", icon = 'HANDLE_VECTOR', text="Vector").type = 'VECTOR'
        layout.operator("curve.handle_type_set", icon = 'HANDLE_ALIGNED',text="Aligned").type = 'ALIGNED'
        layout.operator("curve.handle_type_set", icon = 'HANDLE_FREE', text="Free").type = 'FREE_ALIGN'

        layout.separator()

        layout.operator("curve.handle_type_set", icon = 'HANDLE_FREE', text="Toggle Free / Aligned").type = 'TOGGLE_FREE_ALIGN'


class VIEW3D_MT_edit_curve_segments(Menu):
    bl_label = "Segments"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.subdivide", icon = 'SUBDIVIDE_EDGES')
        layout.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION')


class VIEW3D_MT_edit_curve_context_menu(Menu):
    bl_label = "Curve Context Menu"

    def draw(self, _context):
        # TODO(campbell): match mesh vertex menu.

        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        # Add
        layout.operator("curve.subdivide", icon = 'SUBDIVIDE_EDGES')
        layout.operator("curve.extrude_move", icon = 'EXTRUDE_REGION')
        layout.operator("curve.make_segment", icon = "MAKE_CURVESEGMENT")
        layout.operator("curve.duplicate_move", icon = "DUPLICATE")

        layout.separator()

        # Transform
        layout.operator("transform.transform", text="Radius").mode = 'CURVE_SHRINKFATTEN'
        layout.operator("transform.tilt", icon = 'TILT')
        layout.operator("curve.tilt_clear", icon = "CLEAR_TILT")
        layout.operator("curve.smooth", icon = 'SHADING_SMOOTH')
        layout.operator("curve.smooth_tilt", icon = "SMOOTH_TILT")
        layout.operator("curve.smooth_radius", icon = "SMOOTH_RADIUS")

        layout.separator()

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        # Modify
        layout.operator_menu_enum("curve.spline_type_set", "type")
        layout.operator_menu_enum("curve.handle_type_set", "type")
        layout.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC')
        layout.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION')

        layout.separator()

        layout.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS')
        layout.operator("curve.spline_weight_set", icon = "MOD_VERTEX_WEIGHT")
        layout.operator("curve.radius_set", icon = "RADIUS")

        layout.separator()

        # Remove
        layout.operator("curve.split", icon = "SPLIT")
        layout.operator("curve.decimate", icon = "DECIMATE")
        layout.operator("curve.separate", icon = "SEPARATE")
        layout.operator("curve.dissolve_verts", icon='DISSOLVE_VERTS')
        layout.operator("curve.delete", text="Delete Segment", icon = "DELETE").type = 'SEGMENT'
        layout.operator("curve.delete", text="Delete Point", icon = "DELETE").type = 'VERT'



class VIEW3D_MT_edit_curve_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.delete", text="Vertices", icon = "DELETE").type = 'VERT'
        layout.operator("curve.delete", text="Segment", icon = "DELETE").type = 'SEGMENT'


# Workaround to separate the tooltips for Show Hide for Curve in Edit Mode
class VIEW3D_curve_hide_unselected(bpy.types.Operator):
    """Hide unselected Control Points"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "curve.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.curve.hide(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_edit_curve_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.reveal", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("curve.hide", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("curve.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_edit_surface(Menu):
    bl_label = "Surface"

    draw = draw_curve


class VIEW3D_MT_edit_font_chars(Menu):
    bl_label = "Special Characters"

    def draw(self, _context):
        layout = self.layout

        layout.operator("font.text_insert", text="Copyright", icon = "COPYRIGHT").text = "\u00A9"
        layout.operator("font.text_insert", text="Registered Trademark", icon = "TRADEMARK").text = "\u00AE"

        layout.separator()

        layout.operator("font.text_insert", text="Degree Sign", icon = "DEGREE").text = "\u00B0"
        layout.operator("font.text_insert", text="Multiplication Sign", icon = "MULTIPLICATION").text = "\u00D7"
        layout.operator("font.text_insert", text="Circle", icon = "CIRCLE").text = "\u008A"

        layout.separator()

        layout.operator("font.text_insert", text="Superscript 1", icon = "SUPER_ONE").text = "\u00B9"
        layout.operator("font.text_insert", text="Superscript 2", icon = "SUPER_TWO").text = "\u00B2"
        layout.operator("font.text_insert", text="Superscript 3", icon = "SUPER_THREE").text = "\u00B3"

        layout.separator()

        layout.operator("font.text_insert", text="Double >>", icon = "DOUBLE_RIGHT").text = "\u00BB"
        layout.operator("font.text_insert", text="Double <<", icon = "DOUBLE_LEFT").text = "\u00AB"
        layout.operator("font.text_insert", text="Promillage", icon = "PROMILLE").text = "\u2030"

        layout.separator()

        layout.operator("font.text_insert", text="Dutch Florin", icon = "DUTCH_FLORIN").text = "\u00A4"
        layout.operator("font.text_insert", text="British Pound", icon = "POUND").text = "\u00A3"
        layout.operator("font.text_insert", text="Japanese Yen", icon = "YEN").text = "\u00A5"

        layout.separator()

        layout.operator("font.text_insert", text="German S", icon = "GERMAN_S").text = "\u00DF"
        layout.operator("font.text_insert", text="Spanish Question Mark", icon = "SPANISH_QUESTION").text = "\u00BF"
        layout.operator("font.text_insert", text="Spanish Exclamation Mark", icon = "SPANISH_EXCLAMATION").text = "\u00A1"


class VIEW3D_MT_edit_font_kerning(Menu):
    bl_label = "Kerning"

    def draw(self, context):
        layout = self.layout

        ob = context.active_object
        text = ob.data
        kerning = text.edit_format.kerning

        layout.operator("font.change_spacing", text="Decrease Kerning", icon = "DECREASE_KERNING").delta = -1
        layout.operator("font.change_spacing", text="Increase Kerning", icon = "INCREASE_KERNING").delta = 1
        layout.operator("font.change_spacing", text="Reset Kerning", icon = "RESET").delta = -kerning


class VIEW3D_MT_edit_font_move(Menu):
    bl_label = "Move Cursor"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("font.move", "type")


class VIEW3D_MT_edit_font_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("font.delete", text="Previous Character", icon = "DELETE").type = 'PREVIOUS_CHARACTER'
        layout.operator("font.delete", text="Next Character", icon = "DELETE").type = 'NEXT_CHARACTER'
        layout.operator("font.delete", text="Previous Word", icon = "DELETE").type = 'PREVIOUS_WORD'
        layout.operator("font.delete", text="Next Word", icon = "DELETE").type = 'NEXT_WORD'


class VIEW3D_MT_edit_font(Menu):
    bl_label = "Text"

    def draw(self, _context):
        layout = self.layout

        layout.operator("font.text_cut", text="Cut", icon = "CUT")
        layout.operator("font.text_copy", text="Copy", icon='COPYDOWN')
        layout.operator("font.text_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("font.text_paste_from_file", icon='PASTEDOWN')

        layout.separator()

        layout.operator("font.case_set", text="To Uppercase", icon = "SET_UPPERCASE").case = 'UPPER'
        layout.operator("font.case_set", text="To Lowercase", icon = "SET_LOWERCASE").case = 'LOWER'

        layout.separator()

        layout.menu("VIEW3D_MT_edit_font_chars")
        layout.menu("VIEW3D_MT_edit_font_move")

        layout.separator()

        layout.operator("font.style_toggle", text="Toggle Bold", icon='BOLD').style = 'BOLD'
        layout.operator("font.style_toggle", text="Toggle Italic", icon='ITALIC').style = 'ITALIC'
        layout.operator("font.style_toggle", text="Toggle Underline", icon='UNDERLINE').style = 'UNDERLINE'
        layout.operator("font.style_toggle", text="Toggle Small Caps", icon='SMALL_CAPS').style = 'SMALL_CAPS'

        layout.menu("VIEW3D_MT_edit_font_kerning")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_font_delete")


class VIEW3D_MT_edit_font_context_menu(Menu):
    bl_label = "Text Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("font.text_cut", text="Cut", icon = "CUT")
        layout.operator("font.text_copy", text="Copy", icon='COPYDOWN')
        layout.operator("font.text_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("font.select_all")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_font")


class VIEW3D_MT_edit_meta(Menu):
    bl_label = "Metaball"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mball.duplicate_metaelems", text = "Duplicate", icon = "DUPLICATE")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_meta_showhide")

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("mball.delete_metaelems", text="Delete", icon = "DELETE")


# Workaround to separate the tooltips for Show Hide for Curve in Edit Mode
class VIEW3D_MT_edit_meta_showhide_unselected(bpy.types.Operator):
    """Hide unselected metaelement(s)"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.hide_metaelems_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.hide_metaelems(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_edit_meta_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mball.reveal_metaelems", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("mball.hide_metaelems", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("mball.hide_metaelems_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_edit_lattice(Menu):
    bl_label = "Lattice"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.menu("VIEW3D_MT_edit_lattice_flip")

        layout.separator()

        layout.operator("lattice.make_regular", icon = 'MAKE_REGULAR')

        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")

class VIEW3D_MT_edit_lattice_flip(Menu):
    bl_label = "Flip"

    def draw(self, context):
        layout = self.layout

        layout.operator("lattice.flip", text = " U (X) axis", icon = "FLIP_X").axis = 'U'
        layout.operator("lattice.flip", text = " V (Y) axis", icon = "FLIP_Y").axis = 'V'
        layout.operator("lattice.flip", text = " W (Z) axis", icon = "FLIP_Z").axis = 'W'


class VIEW3D_MT_edit_armature(Menu):
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data

        layout.menu("VIEW3D_MT_transform_armature")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_armature_roll")

        layout.operator("transform.transform", text="Set Bone Roll", icon = "SET_ROLL").mode = 'BONE_ROLL'
        layout.operator("armature.roll_clear", text="Clear Bone Roll", icon = "CLEAR_ROLL")

        layout.separator()

        layout.operator("armature.extrude_move", icon = 'EXTRUDE_REGION')

        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked", icon = "EXTRUDE_REGION")

        layout.operator("armature.duplicate_move", icon = "DUPLICATE")
        layout.operator("armature.fill", icon = "FILLBETWEEN")

        layout.separator()

        layout.operator("armature.split", icon = "SPLIT")
        layout.operator("armature.separate", icon = "SEPARATE")
        layout.operator("armature.symmetrize", icon = "SYMMETRIZE")

        layout.separator()

        layout.operator("armature.subdivide", text="Subdivide", icon = 'SUBDIVIDE_EDGES')
        layout.operator("armature.switch_direction", text="Switch Direction", icon = "SWITCH_DIRECTION")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_armature_names")

        layout.separator()

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("armature.armature_layers", icon = "LAYER")
        layout.operator("armature.bone_layers", icon = "LAYER")

        layout.separator()

        layout.operator("armature.parent_set", text="Make Parent", icon='PARENT_SET')
        layout.operator("armature.parent_clear", text="Clear Parent", icon='PARENT_CLEAR')

        layout.separator()

        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")
        layout.menu("VIEW3D_MT_armature_show_hide") # bfa - the new show hide menu with split tooltip

        layout.separator()

        layout.operator("armature.delete", icon = "DELETE")
        layout.operator("armature.dissolve", icon = "DELETE")


# Workaround to separate the tooltips for Show Hide for Armature in Edit Mode
class VIEW3D_armature_hide_unselected(bpy.types.Operator):
    """Hide unselected Bones in Edit Mode"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "armature.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.armature.hide(unselected = True)
        return {'FINISHED'}


class VIEW3D_MT_armature_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.reveal", text="Show Hidden", icon = "HIDE_OFF")
        layout.operator("armature.hide", text="Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("armature.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_armature_context_menu(Menu):
    bl_label = "Armature Context Menu"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data

        layout.operator_context = 'INVOKE_REGION_WIN'

        # Add
        layout.operator("armature.subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES")
        layout.operator("armature.duplicate_move", text="Duplicate", icon = "DUPLICATE")
        layout.operator("armature.extrude_move", icon='EXTRUDE_REGION')
        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked", icon='EXTRUDE_REGION')

        layout.separator()

        layout.operator("armature.fill", icon = "FILLBETWEEN")

        layout.separator()

        # Modify
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.operator("armature.switch_direction", text="Switch Direction", icon = "SWITCH_DIRECTION")
        layout.operator("armature.symmetrize", icon = "SYMMETRIZE")
        layout.menu("VIEW3D_MT_edit_armature_names")

        layout.separator()

        layout.operator("armature.parent_set", text="Make Parent", icon='PARENT_SET')
        layout.operator("armature.parent_clear", text="Clear Parent", icon='PARENT_CLEAR')

        layout.separator()

        # Remove
        layout.operator("armature.split", icon = "SPLIT")
        layout.operator("armature.separate", icon = "SEPARATE")
        layout.operator("armature.dissolve", icon = "DELETE")
        layout.operator("armature.delete", icon = "DELETE")


class VIEW3D_MT_edit_armature_names(Menu):
    bl_label = "Names"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("armature.autoside_names", text="AutoName Left/Right", icon = "STRING").type = 'XAXIS'
        layout.operator("armature.autoside_names", text="AutoName Front/Back", icon = "STRING").type = 'YAXIS'
        layout.operator("armature.autoside_names", text="AutoName Top/Bottom", icon = "STRING").type = 'ZAXIS'
        layout.operator("armature.flip_names", text="Flip Names", icon = "FLIP")


class VIEW3D_MT_edit_armature_roll(Menu):
    bl_label = "Recalculate Bone Roll"
    def draw(self, _context):
        layout = self.layout

        layout.label(text="- Positive: -")
        layout.operator("armature.calculate_roll", text= "Local + X Tangent", icon = "ROLL_X_TANG_POS").type = 'POS_X'
        layout.operator("armature.calculate_roll", text= "Local + Z Tangent", icon = "ROLL_Z_TANG_POS").type = 'POS_Z'
        layout.operator("armature.calculate_roll", text= "Global + X Axis", icon = "ROLL_X_POS").type = 'GLOBAL_POS_X'
        layout.operator("armature.calculate_roll", text= "Global + Y Axis", icon = "ROLL_Y_POS").type = 'GLOBAL_POS_Y'
        layout.operator("armature.calculate_roll", text= "Global + Z Axis", icon = "ROLL_Z_POS").type = 'GLOBAL_POS_Z'
        layout.label(text="- Negative: -")
        layout.operator("armature.calculate_roll", text= "Local - X Tangent", icon = "ROLL_X_TANG_NEG").type = 'NEG_X'
        layout.operator("armature.calculate_roll", text= "Local - Z Tangent", icon = "ROLL_Z_TANG_NEG").type = 'NEG_Z'
        layout.operator("armature.calculate_roll", text= "Global - X Axis", icon = "ROLL_X_NEG").type = 'GLOBAL_NEG_X'
        layout.operator("armature.calculate_roll", text= "Global - Y Axis", icon = "ROLL_Y_NEG").type = 'GLOBAL_NEG_Y'
        layout.operator("armature.calculate_roll", text= "Global - Z Axis", icon = "ROLL_Z_NEG").type = 'GLOBAL_NEG_Z'
        layout.label(text="- Other: -")
        layout.operator("armature.calculate_roll", text= "Active Bone", icon = "BONE_DATA").type = 'ACTIVE'
        layout.operator("armature.calculate_roll", text= "View Axis", icon = "MANIPUL").type = 'VIEW'
        layout.operator("armature.calculate_roll", text= "Cursor", icon = "CURSOR").type = 'CURSOR'

# bfa - not functional in the BFA keymap. But menu class remains for the Blender keymap. DO NOT DELETE!
class VIEW3D_MT_edit_armature_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'

        layout.operator("armature.delete", text="Bones", icon = "DELETE")

        layout.separator()

        layout.operator("armature.dissolve", text="Dissolve Bones", icon = "DELETE")


# ********** Grease Pencil menus **********
class VIEW3D_MT_gpencil_autoweights(Menu):
    bl_label = "Generate Weights"

    def draw(self, _context):
        layout = self.layout
        layout.operator("gpencil.generate_weights", text="With Empty Groups", icon = "PARTICLEBRUSH_WEIGHT").mode = 'NAME'
        layout.operator("gpencil.generate_weights", text="With Automatic Weights", icon = "PARTICLEBRUSH_WEIGHT").mode = 'AUTO'


class VIEW3D_MT_gpencil_simplify(Menu):
    bl_label = "Simplify"

    def draw(self, _context):
        layout = self.layout
        layout.operator("gpencil.stroke_simplify_fixed", text="Fixed", icon = "MOD_SIMPLIFY")
        layout.operator("gpencil.stroke_simplify", text="Adaptative", icon = "MOD_SIMPLIFY")
        layout.operator("gpencil.stroke_sample", text="Sample", icon = "MOD_SIMPLIFY")


class VIEW3D_MT_paint_gpencil(Menu):
    bl_label = "Draw"

    def draw(self, _context):

        layout = self.layout

        layout.menu("GPENCIL_MT_layer_active", text="Active Layer")

        layout.separator()

        layout.operator("gpencil.interpolate", text="Interpolate", icon = "INTERPOLATE")
        layout.operator("gpencil.interpolate_sequence", text="Sequence", icon = "SEQUENCE")

        layout.separator()

        layout.menu("VIEW3D_MT_gpencil_animation")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_gpencil_showhide")
        layout.menu("GPENCIL_MT_cleanup")

        layout.separator()

        #radial control button brush size
        myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
        myvar.data_path_primary = 'tool_settings.gpencil_paint.brush.size'

        #radial control button brush strength
        myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
        myvar.data_path_primary = 'tool_settings.gpencil_paint.brush.gpencil_settings.pen_strength'

        #radial control button brush strength
        myvar = layout.operator("wm.radial_control", text = "Eraser Radius (Old Toolsystem)", icon = "BRUSHSIZE")
        myvar.data_path_primary = 'preferences.edit.grease_pencil_eraser_radius'


class VIEW3D_MT_edit_gpencil_showhide(Menu):
    bl_label = "Show/hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("gpencil.reveal", text="Show All Layers", icon = "HIDE_OFF")

        layout.separator()

        layout.operator("gpencil.hide", text="Hide Active Layer", icon = "HIDE_ON").unselected = False
        layout.operator("gpencil.hide", text="Hide Inactive Layers", icon = "HIDE_UNSELECTED").unselected = True


class VIEW3D_MT_assign_material(Menu):
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout
        ob = context.active_object
        mat_active = ob.active_material

        for slot in ob.material_slots:
            mat = slot.material
            if mat:
                layout.operator("gpencil.stroke_change_color", text=mat.name,
                                icon='LAYER_ACTIVE' if mat == mat_active else 'BLANK1').material = mat.name


class VIEW3D_MT_gpencil_copy_layer(Menu):
    bl_label = "Copy Layer to Object"

    def draw(self, context):
        layout = self.layout
        view_layer = context.view_layer
        obact = context.active_object
        gpl = context.active_gpencil_layer

        done = False
        if gpl is not None:
            for ob in view_layer.objects:
                if ob.type == 'GPENCIL' and ob != obact:
                    layout.operator("gpencil.layer_duplicate_object", text=ob.name, icon = "DUPLICATE").object = ob.name
                    done = True

            if done is False:
                layout.label(text="No destination object", icon='ERROR')
        else:
            layout.label(text="No layer to copy", icon='ERROR')


class VIEW3D_MT_edit_gpencil(Menu):
    bl_label = "Grease Pencil"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_edit_gpencil_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("GPENCIL_MT_snap")

        layout.separator()

        layout.menu("GPENCIL_MT_layer_active", text="Active Layer")

        layout.separator()

        layout.menu("VIEW3D_MT_gpencil_animation")

        layout.separator()

        layout.operator("gpencil.duplicate_move", text="Duplicate", icon = "DUPLICATE")
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame", icon = "DUPLICATE")
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame All Layers", icon = "DUPLICATE").mode = 'ALL'

        layout.separator()

        layout.operator("gpencil.stroke_split", text="Split", icon = "SPLIT")

        layout.separator()

        layout.operator("gpencil.copy", text="Copy", icon='COPYDOWN')
        layout.operator("gpencil.paste", text="Paste", icon='PASTEDOWN').type = 'ACTIVE'
        layout.operator("gpencil.paste", text="Paste by Layer", icon='PASTEDOWN').type = 'LAYER'

        layout.separator()

        layout.menu("VIEW3D_MT_edit_gpencil_delete")
        layout.operator_menu_enum("gpencil.dissolve", "type")

        layout.separator()

        layout.menu("GPENCIL_MT_cleanup")
        layout.menu("VIEW3D_MT_edit_gpencil_hide", text = "Show/Hide")

        layout.separator()

        layout.operator_menu_enum("gpencil.stroke_separate", "mode")


class VIEW3D_MT_edit_gpencil_hide(Menu):
    bl_label = "Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.reveal", text="Show Hidden Layer", icon = "HIDE_OFF")
        layout.operator("gpencil.hide", text="Hide selected Layer", icon = "HIDE_ON").unselected = False
        layout.operator("gpencil.hide", text="Hide unselected Layer", icon = "HIDE_UNSELECTED").unselected = True

        layout.separator()

        layout.operator("gpencil.selection_opacity_toggle", text="Toggle Opacity", icon = "HIDE_OFF")


class VIEW3D_MT_edit_gpencil_arrange_strokes(Menu):
    bl_label = "Arrange Strokes"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.stroke_arrange", text="Bring Forward", icon='MOVE_UP').direction = 'UP'
        layout.operator("gpencil.stroke_arrange", text="Send Backward", icon='MOVE_DOWN').direction = 'DOWN'
        layout.operator("gpencil.stroke_arrange", text="Bring to Front", icon='MOVE_TO_TOP').direction = 'TOP'
        layout.operator("gpencil.stroke_arrange", text="Send to Back", icon='MOVE_TO_BOTTOM').direction = 'BOTTOM'


class VIEW3D_MT_edit_gpencil_stroke(Menu):
    bl_label = "Stroke"

    def draw(self, _context):
        layout = self.layout
        settings = _context.tool_settings.gpencil_sculpt

        layout.operator("gpencil.stroke_subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES").only_selected = False
        layout.menu("VIEW3D_MT_gpencil_simplify")
        layout.operator("gpencil.stroke_trim", text="Trim", icon = "CUT")

        layout.separator()

        layout.operator("gpencil.stroke_join", text="Join", icon = "JOIN").type = 'JOIN'
        layout.operator("gpencil.stroke_join", text="Join and Copy", icon = "JOIN").type = 'JOINCOPY'

        layout.separator()

        layout.menu("GPENCIL_MT_move_to_layer")
        layout.menu("VIEW3D_MT_assign_material")
        layout.operator("gpencil.set_active_material", text="Set as Active Material", icon = "MATERIAL")
        layout.menu("VIEW3D_MT_edit_gpencil_arrange_strokes")

        layout.separator()

        # Convert
        op = layout.operator("gpencil.stroke_cyclical_set", text="Close", icon = 'TOGGLE_CYCLIC')
        op.type = 'CLOSE'
        op.geometry = True
        layout.operator("gpencil.stroke_cyclical_set", text="Toggle Cyclic", icon = 'TOGGLE_CYCLIC').type = 'TOGGLE'
        layout.operator_menu_enum("gpencil.stroke_caps_set", text="Toggle Caps", property="type")
        layout.operator("gpencil.stroke_flip", text="Switch Direction", icon = "FLIP")

        layout.separator()

        layout.operator_menu_enum("gpencil.reproject", property="type", text="Reproject Strokes")
        layout.prop(settings, "use_scale_thickness")

        layout.separator()
        layout.operator("gpencil.reset_transform_fill", text="Reset Fill Transform")


class VIEW3D_MT_edit_gpencil_point(Menu):
    bl_label = "Point"

    def draw(self, _context):
        layout = self.layout

        layout.operator("gpencil.extrude_move", text="Extrude Points", icon = "EXTRUDE_REGION")

        layout.separator()

        layout.operator("gpencil.stroke_smooth", text="Smooth Points", icon = "PARTICLEBRUSH_SMOOTH").only_selected = True

        layout.separator()

        layout.operator("gpencil.stroke_merge", text="Merge Points", icon = "MERGE")

        # TODO: add new RIP operator

        layout.separator()

        layout.menu("VIEW3D_MT_gpencil_vertex_group")


class VIEW3D_MT_weight_gpencil(Menu):
    bl_label = "Weights"

    def draw(self, context):
        layout = self.layout

        #layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("gpencil.vertex_group_normalize_all", text="Normalize All", icon = "WEIGHT_NORMALIZE_ALL")
        layout.operator("gpencil.vertex_group_normalize", text="Normalize", icon = "WEIGHT_NORMALIZE")

        layout.separator()

        layout.operator("gpencil.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT')
        layout.operator("gpencil.vertex_group_smooth", text="Smooth", icon='WEIGHT_SMOOTH')

        layout.menu("VIEW3D_MT_gpencil_autoweights")

        if context.mode == 'WEIGHT_GPENCIL':

            #radial control button brush size
            myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
            myvar.data_path_primary = 'tool_settings.gpencil_sculpt.brush.size'

            #radial control button brush strength
            myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
            myvar.data_path_primary = 'tool_settings.gpencil_sculpt.brush.strength'


class VIEW3D_MT_vertex_gpencil(Menu):
    bl_label = "Paint"

    def draw(self, _context):
        layout = self.layout
        layout.operator("gpencil.vertex_color_set", text="Set Vertex Colors")
        layout.separator()
        layout.operator("gpencil.vertex_color_invert", text="Invert")
        layout.operator("gpencil.vertex_color_levels", text="Levels")
        layout.operator("gpencil.vertex_color_hsv", text="Hue Saturation Value")
        layout.operator("gpencil.vertex_color_brightness_contrast", text="Bright/Contrast")

        layout.separator()
        layout.menu("VIEW3D_MT_join_palette")


class VIEW3D_MT_gpencil_animation(Menu):
    bl_label = "Animation"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'GPENCIL' and ob.mode != 'OBJECT'

    def draw(self, _context):
        layout = self.layout

        layout.operator("gpencil.blank_frame_add", text="Insert Blank Keyframe (Active Layer)", icon = "ADD")
        layout.operator("gpencil.blank_frame_add", text="Insert Blank Keyframe (All Layers)", icon = "ADD").all_layers = True

        layout.separator()

        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Keyframe (Active Layer)", icon = "DUPLICATE")
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Keyframe (All Layers)", icon = "DUPLICATE").mode = 'ALL'

        layout.separator()

        layout.operator("gpencil.delete", text="Delete Active Keyframe (Active Layer)", icon = "DELETE").type = 'FRAME'
        layout.operator("gpencil.active_frames_delete_all", text="Delete Active Keyframes (All Layers)", icon = "DELETE")


class VIEW3D_MT_edit_gpencil_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.bend", text="Bend", icon = "BEND")
        layout.operator("transform.shear", text="Shear", icon = "SHEAR")
        layout.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
        layout.operator("transform.transform", text="Shrink Fatten", icon = 'SHRINK_FATTEN').mode = 'GPENCIL_SHRINKFATTEN'


class VIEW3D_MT_object_mode_pie(Menu):
    bl_label = "Mode"

    def draw(self, _context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_enum("object.mode_set", "mode")


class VIEW3D_MT_view_pie(Menu):
    bl_label = "View"
    bl_idname = "VIEW3D_MT_view_pie"

    def draw(self, _context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_enum("view3d.view_axis", "type")
        pie.operator("view3d.view_camera", text="View Camera", icon='CAMERA_DATA')
        pie.operator("view3d.view_selected", text="View Selected", icon='VIEW_SELECTED')


class VIEW3D_MT_transform_gizmo_pie(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        # 1: Left
        pie.operator("view3d.transform_gizmo_set", text="Move").type = {'TRANSLATE'}
        # 2: Right
        pie.operator("view3d.transform_gizmo_set", text="Rotate").type = {'ROTATE'}
        # 3: Down
        pie.operator("view3d.transform_gizmo_set", text="Scale").type = {'SCALE'}
        # 4: Up
        pie.prop(context.space_data, "show_gizmo", text="Show Gizmos", icon='GIZMO')
        # 5: Up/Left
        pie.operator("view3d.transform_gizmo_set", text="All").type = {'TRANSLATE', 'ROTATE', 'SCALE'}


class VIEW3D_MT_shading_pie(Menu):
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        view = context.space_data

        pie.prop(view.shading, "type", expand=True)


class VIEW3D_MT_shading_ex_pie(Menu):
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        view = context.space_data

        pie.prop_enum(view.shading, "type", value='WIREFRAME')
        pie.prop_enum(view.shading, "type", value='SOLID')

        # Note this duplicates "view3d.toggle_xray" logic, so we can see the active item: T58661.
        if context.pose_object:
            pie.prop(view.overlay, "show_xray_bone", icon='XRAY')
        else:
            xray_active = (
                (context.mode == 'EDIT_MESH') or
                (view.shading.type in {'SOLID', 'WIREFRAME'})
            )
            if xray_active:
                sub = pie
            else:
                sub = pie.row()
                sub.active = False
            sub.prop(
                view.shading,
                "show_xray_wireframe" if (view.shading.type == 'WIREFRAME') else "show_xray",
                text="Toggle X-Ray",
                icon='XRAY',
            )

        pie.prop(view.overlay, "show_overlays", text="Toggle Overlays", icon='OVERLAY')

        pie.prop_enum(view.shading, "type", value='MATERIAL')
        pie.prop_enum(view.shading, "type", value='RENDERED')


class VIEW3D_MT_pivot_pie(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        obj = context.active_object
        mode = context.mode

        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='BOUNDING_BOX_CENTER')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='CURSOR')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='INDIVIDUAL_ORIGINS')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='MEDIAN_POINT')
        pie.prop_enum(context.scene.tool_settings, "transform_pivot_point", value='ACTIVE_ELEMENT')
        if (obj is None) or (mode in {'OBJECT', 'POSE', 'WEIGHT_PAINT'}):
            pie.prop(context.scene.tool_settings, "use_transform_pivot_point_align", text="Only Origins")


class VIEW3D_MT_orientations_pie(Menu):
    bl_label = "Orientation"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        scene = context.scene

        pie.prop(scene.transform_orientation_slots[0], "type", expand=True)


class VIEW3D_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon='CURSOR')
        pie.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon='RESTRICT_SELECT_OFF')
        pie.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='CURSOR')
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon='RESTRICT_SELECT_OFF').use_offset = False
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon='RESTRICT_SELECT_OFF').use_offset = True
        pie.operator("view3d.snap_selected_to_active", text="Selection to Active", icon='RESTRICT_SELECT_OFF')
        pie.operator("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon='CURSOR')
        pie.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon='CURSOR')


class VIEW3D_MT_proportional_editing_falloff_pie(Menu):
    bl_label = "Proportional Editing Falloff"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        tool_settings = context.scene.tool_settings

        pie.prop(tool_settings, "proportional_edit_falloff", expand=True)


class VIEW3D_MT_sculpt_mask_edit_pie(Menu):
    bl_label = "Mask Edit"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        op = pie.operator("paint.mask_flood_fill", text='Invert Mask')
        op.mode = 'INVERT'
        op = pie.operator("paint.mask_flood_fill", text='Clear Mask')
        op.mode = 'VALUE'
        op.value = 0.0
        op = pie.operator("sculpt.mask_filter", text='Smooth Mask')
        op.filter_type = 'SMOOTH'
        op.auto_iteration_count = True
        op = pie.operator("sculpt.mask_filter", text='Sharpen Mask')
        op.filter_type = 'SHARPEN'
        op.auto_iteration_count = True
        op = pie.operator("sculpt.mask_filter", text='Grow Mask')
        op.filter_type = 'GROW'
        op.auto_iteration_count = True
        op = pie.operator("sculpt.mask_filter", text='Shrink Mask')
        op.filter_type = 'SHRINK'
        op.auto_iteration_count = True
        op = pie.operator("sculpt.mask_filter", text='Increase Contrast')
        op.filter_type = 'CONTRAST_INCREASE'
        op.auto_iteration_count = False
        op = pie.operator("sculpt.mask_filter", text='Decrease Contrast')
        op.filter_type = 'CONTRAST_DECREASE'
        op.auto_iteration_count = False


class VIEW3D_MT_sculpt_face_sets_edit_pie(Menu):
    bl_label = "Face Sets Edit"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        op = pie.operator("sculpt.face_sets_create", text='Face Set From Masked')
        op.mode = 'MASKED'

        op = pie.operator("sculpt.face_sets_create", text='Face Set From Visible')
        op.mode = 'VISIBLE'

        op = pie.operator("sculpt.face_set_change_visibility", text='Invert Visible')
        op.mode = 'INVERT'

        op = pie.operator("sculpt.face_set_change_visibility", text='Show All')
        op.mode = 'SHOW_ALL'


class VIEW3D_MT_wpaint_vgroup_lock_pie(Menu):
    bl_label = "Vertex Group Locks"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        # 1: Left
        op = pie.operator("object.vertex_group_lock", icon='LOCKED', text="Lock All")
        op.action, op.mask = 'LOCK', 'ALL'
        # 2: Right
        op = pie.operator("object.vertex_group_lock", icon='UNLOCKED', text="Unlock All")
        op.action, op.mask = 'UNLOCK', 'ALL'
        # 3: Down
        op = pie.operator("object.vertex_group_lock", icon='UNLOCKED', text="Unlock Selected")
        op.action, op.mask = 'UNLOCK', 'SELECTED'
        # 4: Up
        op = pie.operator("object.vertex_group_lock", icon='LOCKED', text="Lock Selected")
        op.action, op.mask = 'LOCK', 'SELECTED'
        # 5: Up/Left
        op = pie.operator("object.vertex_group_lock", icon='LOCKED', text="Lock Unselected")
        op.action, op.mask = 'LOCK', 'UNSELECTED'
        # 6: Up/Right
        op = pie.operator("object.vertex_group_lock", text="Lock Only Selected")
        op.action, op.mask = 'LOCK', 'INVERT_UNSELECTED'
        # 7: Down/Left
        op = pie.operator("object.vertex_group_lock", text="Lock Only Unselected")
        op.action, op.mask = 'UNLOCK', 'INVERT_UNSELECTED'
        # 8: Down/Right
        op = pie.operator("object.vertex_group_lock", text="Invert Locks")
        op.action, op.mask = 'INVERT', 'ALL'


# ********** Panel **********

class VIEW3D_PT_active_tool(Panel, ToolActivePanelHelper):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    # See comment below.
    # bl_options = {'HIDE_HEADER'}

    # Don't show in properties editor.
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'


# FIXME(campbell): remove this second panel once 'HIDE_HEADER' works with category tabs,
# Currently pinning allows ordering headerless panels below panels with headers.
class VIEW3D_PT_active_tool_duplicate(Panel, ToolActivePanelHelper):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_options = {'HIDE_HEADER'}

    # Only show in properties editor.
    @classmethod
    def poll(cls, context):
        return context.area.type != 'VIEW_3D'


class VIEW3D_PT_view3d_properties(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "View"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()

        subcol = col.column()
        subcol.active = bool(view.region_3d.view_perspective != 'CAMERA' or view.region_quadviews)
        subcol.prop(view, "lens", text="Focal Length")

        subcol = col.column(align=True)
        subcol.prop(view, "clip_start", text="Clip Near")
        subcol.prop(view, "clip_end", text="Clip Far")

        subcol.separator()

        col = layout.column()

        subcol = col.column()
        subcol.use_property_split = False
        subcol.prop(view, "use_local_camera")

        if view.use_local_camera:
            subcol = col.column()
            subcol.use_property_split = True
            subcol.prop(view, "camera", text="")

        subcol.use_property_split = False
        subcol.prop(view, "use_render_border")


class VIEW3D_PT_view3d_properties_edit(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Edit"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        layout.prop(tool_settings, "lock_object_mode")


class VIEW3D_PT_view3d_camera_lock(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Camera Lock"
    bl_parent_id = "VIEW3D_PT_view3d_properties"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        view = context.space_data

        col = layout.column(align=True)
        sub = col.column()
        sub.active = bool(view.region_3d.view_perspective != 'CAMERA' or view.region_quadviews)

        sub.prop(view, "lock_object")
        lock_object = view.lock_object
        if lock_object:
            if lock_object.type == 'ARMATURE':
                sub.prop_search(
                    view, "lock_bone", lock_object.data,
                    "edit_bones" if lock_object.mode == 'EDIT'
                    else "bones",
                    text="",
                )
        else:
            col = layout.column(align=True)
            col.use_property_split = False
            col.prop(view, "lock_cursor", text="Lock To 3D Cursor")

        col.use_property_split = False
        col.prop(view, "lock_camera", text="Camera to View")


class VIEW3D_PT_view3d_cursor(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "3D Cursor"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        cursor = context.scene.cursor

        layout.column().prop(cursor, "location", text="Location")
        rotation_mode = cursor.rotation_mode
        if rotation_mode == 'QUATERNION':
            layout.column().prop(cursor, "rotation_quaternion", text="Rotation")
        elif rotation_mode == 'AXIS_ANGLE':
            layout.column().prop(cursor, "rotation_axis_angle", text="Rotation")
        else:
            layout.column().prop(cursor, "rotation_euler", text="Rotation")
        layout.prop(cursor, "rotation_mode", text="")


class VIEW3D_PT_collections(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Collections"
    bl_options = {'DEFAULT_CLOSED'}

    def _draw_collection(self, layout, view_layer, use_local_collections, collection, index):
        need_separator = index
        for child in collection.children:
            index += 1

            if child.exclude:
                continue

            if child.collection.hide_viewport:
                continue

            if need_separator:
                layout.separator()
                need_separator = False

            icon = 'BLANK1'
            # has_objects = True
            if child.has_selected_objects(view_layer):
                icon = 'LAYER_ACTIVE'
            elif child.has_objects():
                icon = 'LAYER_USED'
            else:
                # has_objects = False
                pass

            row = layout.row()
            row.use_property_decorate = False
            sub = row.split(factor=0.98)
            subrow = sub.row()
            subrow.alignment = 'LEFT'
            subrow.operator(
                "object.hide_collection", text=child.name, icon=icon, emboss=False,
            ).collection_index = index

            sub = row.split()
            subrow = sub.row(align=True)
            subrow.alignment = 'RIGHT'
            if not use_local_collections:
                subrow.active = collection.is_visible  # Parent collection runtime visibility
                subrow.prop(child, "hide_viewport", text="", emboss=False)
            else:
                subrow.active = collection.visible_get()  # Parent collection runtime visibility
                icon = 'HIDE_OFF' if child.visible_get() else 'HIDE_ON'
                props = subrow.operator("object.hide_collection", text="", icon=icon, emboss=False)
                props.collection_index = index
                props.toggle = True

        for child in collection.children:
            index = self._draw_collection(layout, view_layer, use_local_collections, child, index)

        return index

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        view = context.space_data
        view_layer = context.view_layer

        layout.use_property_split = False
        layout.prop(view, "use_local_collections")
        layout.separator()

        # We pass index 0 here because the index is increased
        # so the first real index is 1
        # And we start with index as 1 because we skip the master collection
        self._draw_collection(layout, view_layer, view.use_local_collections, view_layer.layer_collection, 0)


class VIEW3D_PT_object_type_visibility(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "View Object Types"
    bl_ui_units_x = 6

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        view = context.space_data

        layout.label(text="Object Types Visibility")
        col = layout.column()

        attr_object_types = (
            # Geometry
            ("mesh", "Mesh          "),
            ("curve", "Curve       "),
            ("surf", "Surface     "),
            ("meta", "Meta         "),
            ("font", "Text           "),
            ("hair", "Hair"),
            ("pointcloud", "Point Cloud"),
            ("volume", "Volume"),
            ("grease_pencil", "Grease Pencil"),
            (None, None),
            # Other
            ("armature", "Armature  "),
            ("lattice", "Lattice      "),
            ("empty", "Empty        "),
            ("light", "Light        "),
            ("light_probe", "Light Probe  "),
            ("camera", "Camera     "),
            ("speaker", "Speaker    "),
        )

        for attr, attr_name in attr_object_types:
            if attr is None:
                col.separator()
                continue

            if attr == "hair" and not hasattr(bpy.data, "hairs"):
                continue
            elif attr == "pointcloud" and not hasattr(bpy.data, "pointclouds"):
                continue

            attr_v = "show_object_viewport_" f"{attr:s}"
            attr_s = "show_object_select_" f"{attr:s}"

            icon_v = 'HIDE_OFF' if getattr(view, attr_v) else 'HIDE_ON'
            icon_s = 'RESTRICT_SELECT_OFF' if getattr(view, attr_s) else 'RESTRICT_SELECT_ON'

            row = col.row(align=True)
            row.alignment = 'RIGHT'

            row.label(text=attr_name)
            row.prop(view, attr_v, text="", icon=icon_v, emboss=False)
            rowsub = row.row(align=True)
            rowsub.active = getattr(view, attr_v)
            rowsub.prop(view, attr_s, text="", icon=icon_s, emboss=False)


class VIEW3D_PT_shading(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Shading"
    bl_ui_units_x = 12

    @classmethod
    def get_shading(cls, context):
        # Get settings from 3D viewport or OpenGL render engine
        view = context.space_data
        if view.type == 'VIEW_3D':
            return view.shading
        else:
            return context.scene.display.shading

    def draw(self, _context):
        layout = self.layout
        layout.label(text="Viewport Shading")


class VIEW3D_PT_shading_lighting(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Lighting"
    bl_parent_id = 'VIEW3D_PT_shading'

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        engine = context.scene.render.engine
        return shading.type in {'SOLID', 'MATERIAL'} or engine == 'BLENDER_EEVEE' and shading.type == 'RENDERED'

    def draw(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        col = layout.column()
        split = col.split(factor=0.9)

        if shading.type == 'SOLID':
            split.row().prop(shading, "light", expand=True)
            col = split.column()

            split = layout.split(factor=0.9)
            col = split.column()
            sub = col.row()

            if shading.light == 'STUDIO':
                prefs = context.preferences
                system = prefs.system

                if not system.use_studio_light_edit:
                    sub.scale_y = 0.6  # smaller studiolight preview
                    sub.template_icon_view(shading, "studio_light", scale_popup=3.0)
                else:
                    sub.prop(system, "use_studio_light_edit", text="Disable Studio Light Edit", icon='NONE', toggle=True)

                col = split.column()
                col.operator("preferences.studiolight_show", emboss=False, text="", icon='PREFERENCES')

                split = layout.split(factor=0.9)
                col = split.column()

                row = col.row()
                row.prop(shading, "use_world_space_lighting", text="", icon='WORLD', toggle=True)
                row = row.row()
                if shading.use_world_space_lighting:
                    row.prop(shading, "studiolight_rotate_z", text="Rotation")
                    col = split.column()  # to align properly with above

            elif shading.light == 'MATCAP':
                sub.scale_y = 0.6  # smaller matcap preview
                sub.template_icon_view(shading, "studio_light", scale_popup=3.0)

                col = split.column()
                col.operator("preferences.studiolight_show", emboss=False, text="", icon='PREFERENCES')
                col.operator("view3d.toggle_matcap_flip", emboss=False, text="", icon='ARROW_LEFTRIGHT')

        elif shading.type == 'MATERIAL':
            col.prop(shading, "use_scene_lights")
            col.prop(shading, "use_scene_world")
            col = layout.column()
            split = col.split(factor=0.9)

            if not shading.use_scene_world:
                col = split.column()
                sub = col.row()
                sub.scale_y = 0.6
                sub.template_icon_view(shading, "studio_light", scale_popup=3)

                col = split.column()
                col.operator("preferences.studiolight_show", emboss=False, text="", icon='PREFERENCES')

                split = layout.split(factor=0.9)
                col = split.column()
                col.prop(shading, "studiolight_rotate_z", text="Rotation")
                col.prop(shading, "studiolight_intensity")
                col.prop(shading, "studiolight_background_alpha")
                col.prop(shading, "studiolight_background_blur")
                col = split.column()  # to align properly with above

        elif shading.type == 'RENDERED':
            col.prop(shading, "use_scene_lights_render")
            col.prop(shading, "use_scene_world_render")

            if not shading.use_scene_world_render:
                col = layout.column()
                split = col.split(factor=0.9)

                col = split.column()
                sub = col.row()
                sub.scale_y = 0.6
                sub.template_icon_view(shading, "studio_light", scale_popup=3)

                col = split.column()
                col.operator("preferences.studiolight_show", emboss=False, text="", icon='PREFERENCES')

                split = layout.split(factor=0.9)
                col = split.column()
                col.prop(shading, "studiolight_rotate_z", text="Rotation")
                col.prop(shading, "studiolight_intensity")
                col.prop(shading, "studiolight_background_alpha")
                col.prop(shading, "studiolight_background_blur")
                col = split.column()  # to align properly with above


class VIEW3D_PT_shading_color(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Color"
    bl_parent_id = 'VIEW3D_PT_shading'

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        return shading.type in {'WIREFRAME', 'SOLID'}

    def _draw_color_type(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        layout.grid_flow(columns=3, align=True).prop(shading, "color_type", expand=True)
        if shading.color_type == 'SINGLE':
            layout.row().prop(shading, "single_color", text="")

    def _draw_background_color(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        layout.row().label(text="Background")
        layout.row().prop(shading, "background_type", expand=True)
        if shading.background_type == 'VIEWPORT':
            layout.row().prop(shading, "background_color", text="")

    def draw(self, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        if shading.type == 'WIREFRAME':
            self.layout.row().prop(shading, "wireframe_color_type", expand=True)
        else:
            self._draw_color_type(context)
            self.layout.separator()
        self._draw_background_color(context)


class VIEW3D_PT_shading_options(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Options"
    bl_parent_id = 'VIEW3D_PT_shading'

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        return shading.type in {'WIREFRAME', 'SOLID'}

    def draw(self, context):
        layout = self.layout

        shading = VIEW3D_PT_shading.get_shading(context)

        col = layout.column()

        if shading.type == 'SOLID':
            col.prop(shading, "show_backface_culling")

        row = col.row(align=True)

        if shading.type == 'WIREFRAME':
            row.prop(shading, "show_xray_wireframe")
            sub = row.row()
            sub.use_property_split = True
            sub.active = shading.show_xray_wireframe
            sub.prop(shading, "xray_alpha_wireframe", text="")

        elif shading.type == 'SOLID':
            row.prop(shading, "show_xray", text="")
            sub = row.row()
            sub.active = shading.show_xray
            sub.prop(shading, "xray_alpha", text="X-Ray")
            # X-ray mode is off when alpha is 1.0
            xray_active = shading.show_xray and shading.xray_alpha != 1

            row = col.row(align=True)
            row.prop(shading, "show_shadows", text="")
            row.active = not xray_active
            sub = row.row(align=True)
            sub.active = shading.show_shadows
            sub.prop(shading, "shadow_intensity", text="Shadow")
            sub.popover(
                panel="VIEW3D_PT_shading_options_shadow",
                icon='PREFERENCES',
                text="",
            )

            col = layout.column()

            row = col.row()
            row.prop(shading, "show_cavity")

            if shading.show_cavity:
                row.prop(shading, "cavity_type", text="Type")

                if shading.cavity_type in {'WORLD', 'BOTH'}:
                    col.label(text="World Space")
                    sub = col.row(align=True)
                    sub.prop(shading, "cavity_ridge_factor", text="Ridge")
                    sub.prop(shading, "cavity_valley_factor", text="Valley")
                    sub.popover(
                        panel="VIEW3D_PT_shading_options_ssao",
                        icon='PREFERENCES',
                        text="",
                    )

                if shading.cavity_type in {'SCREEN', 'BOTH'}:
                    col.label(text="Screen Space")
                    sub = col.row(align=True)
                    sub.prop(shading, "curvature_ridge_factor", text="Ridge")
                    sub.prop(shading, "curvature_valley_factor", text="Valley")

            row = col.row()
            row.prop(shading, "use_dof", text="Depth Of Field")

        if shading.type in {'WIREFRAME', 'SOLID'}:
            row = layout.split()
            row.prop(shading, "show_object_outline")
            sub = row.row()
            if shading.show_object_outline:
                sub.prop(shading, "object_outline_color", text="")

        if shading.type == 'SOLID':
            col = layout.column()
            if shading.light in {'STUDIO', 'MATCAP'}:
                col.active = shading.selected_studio_light.has_specular_highlight_pass
                col.prop(shading, "show_specular_highlight", text="Specular Lighting")


class VIEW3D_PT_shading_options_shadow(Panel):
    bl_label = "Shadow Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene

        col = layout.column()
        col.prop(scene.display, "light_direction")
        col.prop(scene.display, "shadow_shift")
        col.prop(scene.display, "shadow_focus")


class VIEW3D_PT_shading_options_ssao(Panel):
    bl_label = "SSAO Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene

        col = layout.column(align=True)
        col.prop(scene.display, "matcap_ssao_samples")
        col.prop(scene.display, "matcap_ssao_distance")
        col.prop(scene.display, "matcap_ssao_attenuation")


class VIEW3D_PT_shading_render_pass(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Render Pass"
    bl_parent_id = 'VIEW3D_PT_shading'
    COMPAT_ENGINES = {'BLENDER_EEVEE'}

    @classmethod
    def poll(cls, context):
        return (
            (context.space_data.shading.type == 'MATERIAL') or
            (context.engine in cls.COMPAT_ENGINES and context.space_data.shading.type == 'RENDERED')
        )

    def draw(self, context):
        shading = context.space_data.shading

        layout = self.layout
        layout.prop(shading, "render_pass", text="")


class VIEW3D_PT_gizmo_display(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Gizmo"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        view = context.space_data

        col = layout.column()
        col.label(text="Viewport Gizmos")

        col.active = view.show_gizmo
        colsub = col.column(align = True)
        row = colsub.row()
        row.separator()
        row.prop(view, "show_gizmo_navigate", text="Navigate")
        row = colsub.row()
        row.separator()
        row.prop(view, "show_gizmo_tool", text="Active Tools")
        row = colsub.row()
        row.separator()
        row.prop(view, "show_gizmo_context", text="Active Object")

        col = layout.column( align = True)
        col.active = view.show_gizmo_context
        col.label(text="Object Gizmos")
        row = col.row()
        row.separator()
        row.prop(scene.transform_orientation_slots[1], "type", text="")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_object_translate", text="Move")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_object_rotate", text="Rotate")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_object_scale", text="Scale")

        # Match order of object type visibility
        col = layout.column(align = True)
        col.label(text="Empty")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_empty_image", text="Image")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_empty_force_field", text="Force Field")

        col.label(text="Light")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_light_size", text="Size")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_light_look_at", text="Look At")

        col.label(text="Camera")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_camera_lens", text="Lens")
        row = col.row()
        row.separator()
        row.prop(view, "show_gizmo_camera_dof_distance", text="Focus Distance")


class VIEW3D_PT_overlay(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Overlays"
    bl_ui_units_x = 13

    def draw(self, _context):
        layout = self.layout
        layout.label(text="Viewport Overlays")


class VIEW3D_PT_overlay_guides(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Guides"

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        scene = context.scene

        overlay = view.overlay
        shading = view.shading
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        split = col.split()
        sub = split.column()

        row = sub.row()
        row_el = row.column()
        row_el.prop(overlay, "show_ortho_grid", text="Grid")
        grid_active = bool(
            view.region_quadviews or
            (view.region_3d.is_orthographic_side_view and not view.region_3d.is_perspective)
        )
        row_el.active = grid_active
        row.prop(overlay, "show_floor", text="Floor")

        if overlay.show_floor or overlay.show_ortho_grid:
            sub = col.row(align=True)
            sub.active = (overlay.show_floor and not view.region_3d.is_orthographic_side_view) or (overlay.show_ortho_grid and grid_active)
            sub.prop(overlay, "grid_scale", text="Scale")
            sub = sub.row(align=True)
            sub.active = scene.unit_settings.system == 'NONE'
            sub.prop(overlay, "grid_subdivisions", text="Subdivisions")

        sub = split.column()
        row = sub.row()
        row.label(text="Axes")

        subrow = row.row(align=True)
        subrow.prop(overlay, "show_axis_x", text="X", toggle=True)
        subrow.prop(overlay, "show_axis_y", text="Y", toggle=True)
        subrow.prop(overlay, "show_axis_z", text="Z", toggle=True)

        split = col.split()
        sub = split.column()
        sub.prop(overlay, "show_text", text="Text Info")
        sub.prop(overlay, "show_stats", text="Statistics")

        sub = split.column()
        sub.prop(overlay, "show_cursor", text="3D Cursor")
        sub.prop(overlay, "show_annotation", text="Annotations")

        if shading.type == 'MATERIAL':
            row = col.row()
            row.active = shading.render_pass == 'COMBINED'
            row.prop(overlay, "show_look_dev")


class VIEW3D_PT_overlay_object(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Objects"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column(align=True)
        col.active = display_all

        split = col.split()

        sub = split.column(align=True)
        sub.prop(overlay, "show_extras", text="Extras")
        sub.prop(overlay, "show_relationship_lines")
        sub.prop(overlay, "show_outline_selected")

        sub = split.column(align=True)
        sub.prop(overlay, "show_bones", text="Bones")
        sub.prop(overlay, "show_motion_paths")
        sub.prop(overlay, "show_object_origins", text="Origins")
        subsub = sub.column()
        subsub.active = overlay.show_object_origins
        subsub.prop(overlay, "show_object_origins_all", text="Origins (All)")


class VIEW3D_PT_overlay_geometry(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Geometry"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays
        is_wireframes = view.shading.type == 'WIREFRAME'

        col = layout.column()
        col.active = display_all

        row = col.row(align=True)
        if not is_wireframes:
            row.prop(overlay, "show_wireframes", text="")
        sub = row.row()
        sub.active = overlay.show_wireframes or is_wireframes
        sub.prop(overlay, "wireframe_threshold", text="Wireframe")

        col = layout.column(align=True)
        col.active = display_all

        col.prop(overlay, "show_face_orientation")

        # sub.prop(overlay, "show_onion_skins")


class VIEW3D_PT_overlay_motion_tracking(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Motion Tracking"

    def draw_header(self, context):
        view = context.space_data
        self.layout.prop(view, "show_reconstruction", text="")

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        if view.show_reconstruction:
            split = col.split()

            sub = split.column(align=True)
            sub.active = view.show_reconstruction
            sub.prop(view, "show_camera_path", text="Camera Path")

            sub = split.column()
            sub.prop(view, "show_bundle_names", text="Marker Names")

            col = layout.column()
            col.label(text="Tracks:")
            row = col.row(align=True)
            row.prop(view, "tracks_display_type", text="")
            row.prop(view, "tracks_display_size", text="Size")


class VIEW3D_PT_overlay_edit_mesh(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Mesh Edit Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        shading = view.shading
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        split = col.split()

        sub = split.column()
        sub.active = not ((shading.type == 'WIREFRAME') or shading.show_xray)
        sub.prop(overlay, "show_edges", text="Edges")
        sub = split.column()
        sub.prop(overlay, "show_faces", text="Faces")
        sub = split.column()
        sub.prop(overlay, "show_face_center", text="Center")

        row = col.row(align=True)
        row.prop(overlay, "show_edge_crease", text="Creases", toggle=True)
        row.prop(overlay, "show_edge_sharp", text="Sharp", text_ctxt=i18n_contexts.plural, toggle=True)
        row.prop(overlay, "show_edge_bevel_weight", text="Bevel", toggle=True)
        row.prop(overlay, "show_edge_seams", text="Seams", toggle=True)

        if context.preferences.view.show_developer_ui:
            col.label(text="Developer")
            col.prop(overlay, "show_extra_indices", text="Indices")


class VIEW3D_PT_overlay_edit_mesh_shading(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay_edit_mesh'
    bl_label = "Shading"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        shading = view.shading
        overlay = view.overlay
        tool_settings = context.tool_settings
        display_all = overlay.show_overlays
        statvis = tool_settings.statvis

        col = layout.column()
        col.active = display_all

        col.prop(overlay, "show_occlude_wire")

        col.prop(overlay, "show_weight", text="Vertex Group Weights")
        if overlay.show_weight:
            row = col.split(factor=0.33)
            row.label(text="Zero Weights")
            sub = row.row()
            sub.prop(tool_settings, "vertex_group_user", expand=True)

        if shading.type == 'WIREFRAME':
            xray = shading.show_xray_wireframe and shading.xray_alpha_wireframe < 1.0
        elif shading.type == 'SOLID':
            xray = shading.show_xray and shading.xray_alpha < 1.0
        else:
            xray = False
        statvis_active = not xray
        row = col.row()
        row.active = statvis_active
        row.prop(overlay, "show_statvis", text="Mesh Analysis")
        if overlay.show_statvis:
            col = col.column()
            col.active = statvis_active

            sub = col.split()
            sub.label(text="Type")
            sub.prop(statvis, "type", text="")

            statvis_type = statvis.type
            if statvis_type == 'OVERHANG':
                row = col.row(align=True)
                row.prop(statvis, "overhang_min", text="Minimum")
                row.prop(statvis, "overhang_max", text="Maximum")
                col.row().prop(statvis, "overhang_axis", expand=True)
            elif statvis_type == 'THICKNESS':
                row = col.row(align=True)
                row.prop(statvis, "thickness_min", text="Minimum")
                row.prop(statvis, "thickness_max", text="Maximum")
                col.prop(statvis, "thickness_samples")
            elif statvis_type == 'INTERSECT':
                pass
            elif statvis_type == 'DISTORT':
                row = col.row(align=True)
                row.prop(statvis, "distort_min", text="Minimum")
                row.prop(statvis, "distort_max", text="Maximum")
            elif statvis_type == 'SHARP':
                row = col.row(align=True)
                row.prop(statvis, "sharp_min", text="Minimum")
                row.prop(statvis, "sharp_max", text="Maximum")


class VIEW3D_PT_overlay_edit_mesh_measurement(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay_edit_mesh'
    bl_label = "Measurement"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        split = col.split()

        sub = split.column()
        sub.prop(overlay, "show_extra_edge_length", text="Edge Length")
        sub.prop(overlay, "show_extra_edge_angle", text="Edge Angle")

        sub = split.column()
        sub.prop(overlay, "show_extra_face_area", text="Face Area")
        sub.prop(overlay, "show_extra_face_angle", text="Face Angle")


class VIEW3D_PT_overlay_edit_mesh_normals(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay_edit_mesh'
    bl_label = "Normals"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        row = col.row(align=True)
        row.prop(overlay, "show_vertex_normals", text="", icon='NORMALS_VERTEX')
        row.prop(overlay, "show_split_normals", text="", icon='NORMALS_VERTEX_FACE')
        row.prop(overlay, "show_face_normals", text="", icon='NORMALS_FACE')

        sub = row.row(align=True)
        sub.active = overlay.show_vertex_normals or overlay.show_face_normals or overlay.show_split_normals
        sub.prop(overlay, "normals_length", text="Size")


class VIEW3D_PT_overlay_edit_mesh_freestyle(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Freestyle"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and bpy.app.build_options.freestyle

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        row = col.row()
        row.prop(overlay, "show_freestyle_edge_marks", text="Edge Marks")
        row.prop(overlay, "show_freestyle_face_marks", text="Face Marks")


class VIEW3D_PT_overlay_edit_curve(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Curve Edit Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_CURVE'

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        row = col.row()
        row.prop(overlay, "display_handle", text="Handles")

        row = col.row()
        row.prop(overlay, "show_curve_normals", text="")
        sub = row.row()
        sub.active = overlay.show_curve_normals
        sub.prop(overlay, "normals_length", text="Normals")


class VIEW3D_PT_overlay_sculpt(Panel):
    bl_space_type = 'VIEW_3D'
    bl_context = ".sculpt_mode"
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Sculpt"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'SCULPT' and
            (context.sculpt_object and context.tool_settings.sculpt)
        )

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        sculpt = tool_settings.sculpt

        view = context.space_data
        overlay = view.overlay

        row = layout.row(align=True)
        row.prop(sculpt, "show_mask", text="")
        sub = row.row()
        sub.active = sculpt.show_mask
        sub.prop(overlay, "sculpt_mode_mask_opacity", text="Mask")

        row = layout.row(align=True)
        row.prop(sculpt, "show_face_sets", text="")
        sub = row.row()
        sub.active = sculpt.show_face_sets
        row.prop(overlay, "sculpt_mode_face_sets_opacity", text="Face Sets")


class VIEW3D_PT_overlay_pose(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Pose Mode"

    @classmethod
    def poll(cls, context):
        mode = context.mode
        return (
            (mode == 'POSE') or
            (mode == 'PAINT_WEIGHT' and context.pose_object)
        )

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        mode = context.mode
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        if mode == 'POSE':
            row = col.row()
            row.prop(overlay, "show_xray_bone", text="")
            sub = row.row()
            sub.active = display_all and overlay.show_xray_bone
            sub.prop(overlay, "xray_alpha_bone", text="Fade Geometry")
        else:
            row = col.row()
            row.prop(overlay, "show_xray_bone")


class VIEW3D_PT_overlay_texture_paint(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Texture Paint"

    @classmethod
    def poll(cls, context):
        return context.mode == 'PAINT_TEXTURE'

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all
        col.prop(overlay, "texture_paint_mode_opacity")


class VIEW3D_PT_overlay_vertex_paint(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Vertex Paint"

    @classmethod
    def poll(cls, context):
        return context.mode == 'PAINT_VERTEX'

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        col.prop(overlay, "vertex_paint_mode_opacity", text="Opacity")
        col.prop(overlay, "show_paint_wire")


class VIEW3D_PT_overlay_weight_paint(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Weight Paint"

    @classmethod
    def poll(cls, context):
        return context.mode == 'PAINT_WEIGHT'

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        col.prop(overlay, "weight_paint_mode_opacity", text="Opacity")
        row = col.split(factor=0.33)
        row.label(text="Zero Weights")
        sub = row.row()
        sub.prop(context.tool_settings, "vertex_group_user", expand=True)

        col.prop(overlay, "show_wpaint_contours")
        col.prop(overlay, "show_paint_wire")


class VIEW3D_PT_snapping(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Snapping"

    def draw(self, context):
        tool_settings = context.tool_settings
        snap_elements = tool_settings.snap_elements
        obj = context.active_object
        object_mode = 'OBJECT' if obj is None else obj.mode

        layout = self.layout
        col = layout.column()
        col.label(text="Snap to")
        col.prop(tool_settings, "snap_elements", expand=True)

        col.separator()
        if 'INCREMENT' in snap_elements:
            col.prop(tool_settings, "use_snap_grid_absolute")

        if snap_elements != {'INCREMENT'}:
            col.label(text="Snap with")
            row = col.row(align=True)
            row.prop(tool_settings, "snap_target", expand=True)

            col.prop(tool_settings, "use_snap_backface_culling")

            if obj:
                if object_mode == 'EDIT':
                    col.prop(tool_settings, "use_snap_self")
                if object_mode in {'OBJECT', 'POSE', 'EDIT', 'WEIGHT_PAINT'}:
                    col.prop(tool_settings, "use_snap_align_rotation")

            if 'FACE' in snap_elements:
                col.prop(tool_settings, "use_snap_project")

            if 'VOLUME' in snap_elements:
                col.prop(tool_settings, "use_snap_peel_object")

        col.label(text="Affect")
        row = col.row(align=True)
        row.prop(tool_settings, "use_snap_translate", text="Move", toggle=True)
        row.prop(tool_settings, "use_snap_rotate", text="Rotate", toggle=True)
        row.prop(tool_settings, "use_snap_scale", text="Scale", toggle=True)


class VIEW3D_PT_proportional_edit(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Proportional Editing"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        col = layout.column()

        if context.mode != 'OBJECT':
            col.prop(tool_settings, "use_proportional_connected")
            sub = col.column()
            sub.active = not tool_settings.use_proportional_connected
            sub.prop(tool_settings, "use_proportional_projected")
            col.separator()

        col.prop(tool_settings, "proportional_edit_falloff", expand=True)


class VIEW3D_PT_transform_orientations(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Transform Orientations"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout
        layout.label(text="Transform Orientations")

        scene = context.scene
        orient_slot = scene.transform_orientation_slots[0]
        orientation = orient_slot.custom_orientation

        row = layout.row()
        col = row.column()
        col.prop(orient_slot, "type", expand=True)
        row.operator("transform.create_orientation", text="", icon='ADD', emboss=False).use = True

        if orientation:
            row = layout.row(align=False)
            row.prop(orientation, "name", text="", icon='OBJECT_ORIGIN')
            row.operator("transform.delete_orientation", text="", icon='X', emboss=False)


class VIEW3D_PT_gpencil_origin(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Stroke Placement"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        gpd = context.gpencil_data

        layout.label(text="Stroke Placement")

        row = layout.row()
        col = row.column()
        col.prop(tool_settings, "gpencil_stroke_placement_view3d", expand=True)

        if tool_settings.gpencil_stroke_placement_view3d == 'SURFACE':
            row = layout.row()
            row.label(text="Offset")
            row = layout.row()
            row.prop(gpd, "zdepth_offset", text="")

        if tool_settings.gpencil_stroke_placement_view3d == 'STROKE':
            row = layout.row()
            row.label(text="Target")
            row = layout.row()
            row.prop(tool_settings, "gpencil_stroke_snap_mode", expand=True)


class VIEW3D_PT_gpencil_lock(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Drawing Plane"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Drawing Plane")

        row = layout.row()
        col = row.column()
        col.prop(context.tool_settings.gpencil_sculpt, "lock_axis", expand=True)


class VIEW3D_PT_gpencil_guide(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Guides"

    def draw(self, context):
        settings = context.tool_settings.gpencil_sculpt.guide

        layout = self.layout
        layout.label(text="Guides")

        col = layout.column()
        col.active = settings.use_guide
        col.prop(settings, "type", expand=True)

        if settings.type in {'ISO', 'PARALLEL', 'RADIAL'}:
            col.prop(settings, "angle")
            row = col.row(align=True)

        col.prop(settings, "use_snapping")
        if settings.use_snapping:

            if settings.type == 'RADIAL':
                col.prop(settings, "angle_snap")
            else:
                col.prop(settings, "spacing")

        if settings.type in {'CIRCULAR', 'RADIAL'} or settings.use_snapping:
            col.label(text="Reference Point")
            row = col.row(align=True)
            row.prop(settings, "reference_point", expand=True)
            if settings.reference_point == 'CUSTOM':
                col.prop(settings, "location", text="Custom Location")
            elif settings.reference_point == 'OBJECT':
                col.prop(settings, "reference_object", text="Object Location")
                if not settings.reference_object:
                    col.label(text="No object selected, using cursor")


class VIEW3D_PT_overlay_gpencil_options(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text={
            'PAINT_GPENCIL': "Draw Grease Pencil",
            'EDIT_GPENCIL': "Edit Grease Pencil",
            'SCULPT_GPENCIL': "Sculpt Grease Pencil",
            'WEIGHT_GPENCIL': "Weight Grease Pencil",
            'VERTEX_GPENCIL': "Vertex Grease Pencil",
            'OBJECT': "Grease Pencil",
        }[context.mode])

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay

        layout.prop(overlay, "use_gpencil_onion_skin", text="Onion Skin")

        col = layout.column()
        row = col.row()
        row.prop(overlay, "use_gpencil_grid", text="")
        sub = row.row(align=True)
        sub.active = overlay.use_gpencil_grid
        sub.prop(overlay, "gpencil_grid_opacity", text="Canvas", slider=True)
        sub.prop(overlay, "use_gpencil_canvas_xray", text="", icon='XRAY')

        row = col.row()
        row.prop(overlay, "use_gpencil_fade_layers", text="")
        sub = row.row()
        sub.active = overlay.use_gpencil_fade_layers
        sub.prop(overlay, "gpencil_fade_layer", text="Fade Layers", slider=True)

        row = col.row()
        row.prop(overlay, "use_gpencil_fade_objects", text="")
        sub = row.row(align=True)
        sub.active = overlay.use_gpencil_fade_objects
        sub.prop(overlay, "gpencil_fade_objects", text="Fade Objects", slider=True)
        sub.prop(overlay, "use_gpencil_fade_gp_objects", text="", icon='OUTLINER_OB_GREASEPENCIL')

        if context.object.mode in {'EDIT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL', 'VERTEX_GPENCIL'}:
            split = layout.split()
            col = split.column()
            col.prop(overlay, "use_gpencil_edit_lines", text="Edit Lines")
            col = split.column()
            col.prop(overlay, "use_gpencil_multiedit_line_only", text="Only in Multiframe")

            if context.object.mode == 'EDIT_GPENCIL':
                split = layout.split()
                col = split.column()
                col.prop(overlay, "use_gpencil_show_directions")
                col = split.column()
                col.prop(overlay, "use_gpencil_show_material_name",  text="Material Name")

            layout.prop(overlay, "vertex_opacity", text="Vertex Opacity", slider=True)

        if context.object.mode in {'PAINT_GPENCIL', 'VERTEX_GPENCIL'}:
            layout.label(text="Vertex Paint")
            layout.prop(overlay, "gpencil_vertex_paint_opacity", text="Opacity", slider=True)


class VIEW3D_PT_quad_view(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Quad View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.region_quadviews

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        region = view.region_quadviews[2]
        col = layout.column()
        col.prop(region, "lock_rotation")
        row = col.row()
        row.enabled = region.lock_rotation
        row.prop(region, "show_sync_view")
        row = col.row()
        row.enabled = region.lock_rotation and region.show_sync_view
        row.prop(region, "use_box_clip")


# Annotation properties
class VIEW3D_PT_grease_pencil(AnnotationDataPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    # NOTE: this is just a wrapper around the generic GP Panel


class VIEW3D_PT_annotation_onion(AnnotationOnionSkin, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_parent_id = 'VIEW3D_PT_grease_pencil'

    # NOTE: this is just a wrapper around the generic GP Panel


class TOPBAR_PT_annotation_layers(Panel, AnnotationDataPanel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Layers"
    bl_ui_units_x = 14


class VIEW3D_PT_view3d_stereo(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Stereoscopy"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene

        multiview = scene.render.use_multiview
        return multiview

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        basic_stereo = context.scene.render.views_format == 'STEREO_3D'

        col = layout.column()
        col.row().prop(view, "stereo_3d_camera", expand=True)

        col.label(text="Display:")
        row = col.row()
        row.active = basic_stereo
        row.prop(view, "show_stereo_3d_cameras")
        row = col.row()
        row.active = basic_stereo
        split = row.split()
        split.prop(view, "show_stereo_3d_convergence_plane")
        split = row.split()
        split.prop(view, "stereo_3d_convergence_plane_alpha", text="Alpha")
        split.active = view.show_stereo_3d_convergence_plane
        row = col.row()
        split = row.split()
        split.prop(view, "show_stereo_3d_volume")
        split = row.split()
        split.prop(view, "stereo_3d_volume_alpha", text="Alpha")


class VIEW3D_PT_context_properties(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_label = "Properties"
    bl_options = {'DEFAULT_CLOSED'}

    @staticmethod
    def _active_context_member(context):
        obj = context.object
        if obj:
            object_mode = obj.mode
            if object_mode == 'POSE':
                return "active_pose_bone"
            elif object_mode == 'EDIT' and obj.type == 'ARMATURE':
                return "active_bone"
            else:
                return "object"

        return ""

    @classmethod
    def poll(cls, context):
        import rna_prop_ui
        member = cls._active_context_member(context)

        if member:
            context_member, member = rna_prop_ui.rna_idprop_context_value(context, member, object)
            return context_member and rna_prop_ui.rna_idprop_has_properties(context_member)

        return False

    def draw(self, context):
        import rna_prop_ui
        member = VIEW3D_PT_context_properties._active_context_member(context)

        if member:
            # Draw with no edit button
            rna_prop_ui.draw(self.layout, context, member, object, False)


# Grease Pencil Object - Multiframe falloff tools
class VIEW3D_PT_gpencil_multi_frame(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Multi Frame"

    def draw(self, context):
        gpd = context.gpencil_data
        settings = context.tool_settings.gpencil_sculpt

        layout = self.layout
        col = layout.column(align=True)
        col.prop(settings, "use_multiframe_falloff")

        # Falloff curve
        if gpd.use_multiedit and settings.use_multiframe_falloff:
            layout.template_curve_mapping(settings, "multiframe_falloff_curve", brush=True)


class VIEW3D_MT_gpencil_edit_context_menu(Menu):
    bl_label = ""

    def draw(self, context):

        is_point_mode = context.tool_settings.gpencil_selectmode_edit == 'POINT'
        is_stroke_mode = context.tool_settings.gpencil_selectmode_edit == 'STROKE'
        is_segment_mode = context.tool_settings.gpencil_selectmode_edit == 'SEGMENT'

        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        row = layout.row()

        if is_point_mode or is_segment_mode:
            col = row.column()

            col.label(text="Point Context Menu", icon='GP_SELECT_POINTS')
            col.separator()

            # Additive Operators
            col.operator("gpencil.stroke_subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES").only_selected = True

            col.separator()

            col.operator("gpencil.extrude_move", text="Extrude Points", icon = 'EXTRUDE_REGION')

            col.separator()

            # Deform Operators
            col.operator("gpencil.stroke_smooth", text="Smooth Points", icon = "PARTICLEBRUSH_SMOOTH").only_selected = True
            col.operator("transform.bend", text="Bend", icon = "BEND")
            col.operator("transform.shear", text="Shear", icon = "SHEAR")
            col.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
            col.operator("transform.transform", text="Shrink Fatten", icon = 'SHRINK_FATTEN').mode = 'GPENCIL_SHRINKFATTEN'

            col.separator()

            col.menu("VIEW3D_MT_mirror", text="Mirror Points")
            col.menu("VIEW3D_MT_snap", text="Snap Points")

            col.separator()

            # Duplicate operators
            col.operator("gpencil.duplicate_move", text="Duplicate", icon='DUPLICATE')
            col.operator("gpencil.copy", text="Copy", icon='COPYDOWN')
            col.operator("gpencil.paste", text="Paste", icon='PASTEDOWN').type = 'ACTIVE'
            col.operator("gpencil.paste", text="Paste by Layer", icon='PASTEDOWN').type = 'LAYER'

            col.separator()

            # Removal Operators
            col.operator("gpencil.stroke_merge", text="Merge Points", icon = "MERGE")
            col.operator("gpencil.stroke_merge_by_distance", icon = "MERGE").use_unselected = False
            col.operator("gpencil.stroke_split", text="Split", icon = "SPLIT")
            col.operator("gpencil.stroke_separate", text="Separate", icon = "SEPARATE").mode = 'POINT'

            col.separator()

            col.operator("gpencil.delete", text="Delete Points", icon = "DELETE").type = 'POINTS'
            col.operator("gpencil.dissolve", text="Dissolve Points", icon = "DELETE").type = 'POINTS'
            col.operator("gpencil.dissolve", text="Dissolve Between", icon = "DELETE").type = 'BETWEEN'
            col.operator("gpencil.dissolve", text="Dissolve Unselected", icon = "DELETE").type = 'UNSELECT'

        if is_stroke_mode:

            col = row.column()
            col.label(text="Stroke Context Menu", icon='GP_SELECT_STROKES')
            col.separator()

            # Main Strokes Operators
            col.operator("gpencil.stroke_subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES").only_selected = False
            col.menu("VIEW3D_MT_gpencil_simplify")
            col.operator("gpencil.stroke_trim", text="Trim", icon = "CUT")

            col.separator()

            col.operator("gpencil.stroke_smooth", text="Smooth Stroke", icon = "PARTICLEBRUSH_SMOOTH").only_selected = False
            col.operator("transform.transform", text="Shrink Fatten", icon = 'SHRINK_FATTEN').mode = 'GPENCIL_SHRINKFATTEN'

            col.separator()

            # Layer and Materials operators
            col.menu("GPENCIL_MT_move_to_layer")
            col.menu("VIEW3D_MT_assign_material")
            col.operator("gpencil.set_active_material", text="Set as Active Material", icon = "MATERIAL_DATA")
            col.operator_menu_enum("gpencil.stroke_arrange", "direction", text="Arrange Strokes")

            col.separator()

            col.menu("VIEW3D_MT_mirror", text="Mirror Stroke")
            col.menu("VIEW3D_MT_snap", text="Snap Stroke")

            col.separator()

            # Duplicate operators
            col.operator("gpencil.duplicate_move", text="Duplicate", icon='DUPLICATE')
            col.operator("gpencil.copy", text="Copy", icon='COPYDOWN')
            col.operator("gpencil.paste", text="Paste", icon='PASTEDOWN').type = 'ACTIVE'
            col.operator("gpencil.paste", text="Paste by Layer", icon='PASTEDOWN').type = 'LAYER'

            col.separator()

            # Removal Operators
            col.operator("gpencil.stroke_merge_by_distance", icon = "MERGE").use_unselected = True
            col.operator_menu_enum("gpencil.stroke_join", "type", text="Join", icon ='JOIN')
            col.operator("gpencil.stroke_split", text="Split", icon = "SPLIT")
            col.operator("gpencil.stroke_separate", text="Separate", icon = "SEPARATE").mode = 'STROKE'

            col.separator()

            col.operator("gpencil.delete", text="Delete Strokes", icon = "DELETE").type = 'STROKES'

            col.separator()

            col.operator("gpencil.reproject", text="Reproject Strokes", icon = "REPROJECT")


class VIEW3D_PT_gpencil_draw_context_menu(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Draw Context Menu"
    bl_ui_units_x = 12

    def draw(self, context):
        ts = context.tool_settings
        settings = ts.gpencil_paint
        brush = settings.brush
        gp_settings = brush.gpencil_settings

        layout = self.layout
        is_vertex = settings.color_mode == 'VERTEXCOLOR' or brush.gpencil_tool == 'TINT'

        if brush.gpencil_tool not in {'ERASE', 'CUTTER', 'EYEDROPPER'} and is_vertex:
            split = layout.split(factor=0.1)
            split.prop(brush, "color", text="")
            split.template_color_picker(brush, "color", value_slider=True)

            col = layout.column()
            col.separator()
            col.prop_menu_enum(gp_settings, "vertex_mode", text="Mode")
            col.separator()

        if brush.gpencil_tool not in {'FILL', 'CUTTER'}:
            layout.prop(brush, "size", slider=True)
        if brush.gpencil_tool not in {'ERASE', 'FILL', 'CUTTER'}:
            layout.prop(gp_settings, "pen_strength")

        # Layers
        draw_gpencil_layer_active(context, layout)
        # Material
        if not is_vertex:
            draw_gpencil_material_active(context, layout)


class VIEW3D_PT_gpencil_vertex_context_menu(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Vertex Paint Context Menu"
    bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout
        ts = context.tool_settings
        settings = ts.gpencil_vertex_paint
        brush = settings.brush
        gp_settings = brush.gpencil_settings

        col = layout.column()

        if brush.gpencil_vertex_tool in {'DRAW', 'REPLACE'}:
            split = layout.split(factor=0.1)
            split.prop(brush, "color", text="")
            split.template_color_picker(brush, "color", value_slider=True)

            col = layout.column()
            col.separator()
            col.prop_menu_enum(gp_settings, "vertex_mode", text="Mode")
            col.separator()

        row = col.row(align=True)
        row.prop(brush, "size", text="Radius")
        row.prop(gp_settings, "use_pressure", text="", icon='STYLUS_PRESSURE')

        if brush.gpencil_vertex_tool in {'DRAW', 'BLUR', 'SMEAR'}:
            row = layout.row(align=True)
            row.prop(gp_settings, "pen_strength", slider=True)
            row.prop(gp_settings, "use_strength_pressure", text="", icon='STYLUS_PRESSURE')

        # Layers
        draw_gpencil_layer_active(context, layout)


class VIEW3D_PT_paint_vertex_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Vertex Paint Context Menu"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.vertex_paint.brush
        capabilities = brush.vertex_paint_capabilities

        if capabilities.has_color:
            split = layout.split(factor=0.1)
            UnifiedPaintPanel.prop_unified_color(split, context, brush, "color", text="")
            UnifiedPaintPanel.prop_unified_color_picker(split, context, brush, "color", value_slider=True)
            layout.prop(brush, "blend", text="")

        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "size",
            unified_name="use_unified_size",
            pressure_name="use_pressure_size",
            slider=True,
        )
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "strength",
            unified_name="use_unified_strength",
            pressure_name="use_pressure_strength",
            slider=True,
        )


class VIEW3D_PT_paint_texture_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Texture Paint Context Menu"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.image_paint.brush
        capabilities = brush.image_paint_capabilities

        if capabilities.has_color:
            split = layout.split(factor=0.1)
            UnifiedPaintPanel.prop_unified_color(split, context, brush, "color", text="")
            UnifiedPaintPanel.prop_unified_color_picker(split, context, brush, "color", value_slider=True)
            layout.prop(brush, "blend", text="")

        if capabilities.has_radius:
            UnifiedPaintPanel.prop_unified(layout, context, brush, "size", unified_name="use_unified_size", pressure_name="use_pressure_size", slider=True,)
            UnifiedPaintPanel.prop_unified(layout, context, brush, "strength", unified_name="use_unified_strength", pressure_name="use_pressure_strength", slider=True,)


class VIEW3D_PT_paint_weight_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Weights Context Menu"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.weight_paint.brush
        UnifiedPaintPanel.prop_unified(layout, context, brush, "weight", unified_name="use_unified_weight", slider=True,)
        UnifiedPaintPanel.prop_unified(layout, context, brush, "size", unified_name="use_unified_size", pressure_name="use_pressure_size", slider=True,)
        UnifiedPaintPanel.prop_unified(layout, context, brush, "strength", unified_name="use_unified_strength", pressure_name="use_pressure_strength", slider=True)


def draw_gpencil_layer_active(context, layout):
        gpl = context.active_gpencil_layer
        if gpl:
            layout.label(text="Active Layer")
            row = layout.row(align=True)
            row.operator_context = 'EXEC_REGION_WIN'
            row.operator_menu_enum("gpencil.layer_change", "layer", text="", icon='GREASEPENCIL')
            row.prop(gpl, "info", text="")
            row.operator("gpencil.layer_remove", text="", icon='X')


def draw_gpencil_material_active(context, layout):
        ob = context.active_object
        if ob and len(ob.material_slots) > 0 and ob.active_material_index >= 0:
            ma = ob.material_slots[ob.active_material_index].material
            if ma:
                layout.label(text="Active Material")
                row = layout.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator_menu_enum("gpencil.material_set", "slot", text="", icon='MATERIAL')
                row.prop(ma, "name", text="")

class VIEW3D_PT_gpencil_sculpt_context_menu(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Sculpt Context Menu"
    bl_ui_units_x = 12

    def draw(self, context):
        ts = context.tool_settings
        settings = ts.gpencil_sculpt_paint
        brush = settings.brush

        layout = self.layout

        layout.prop(brush, "size", slider=True)
        layout.prop(brush, "strength")

        # Layers
        draw_gpencil_layer_active(context, layout)


class VIEW3D_PT_gpencil_weight_context_menu(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Weight Paint Context Menu"
    bl_ui_units_x = 12

    def draw(self, context):
        ts = context.tool_settings
        settings = ts.gpencil_weight_paint
        brush = settings.brush

        layout = self.layout

        layout.prop(brush, "size", slider=True)
        layout.prop(brush, "strength")
        layout.prop(brush, "weight")

        # Layers
        draw_gpencil_layer_active(context, layout)


class VIEW3D_MT_gpencil_sculpt(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_assign_material")
        layout.separator()

        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame", icon = "DUPLICATE")
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame All Layers", icon = "DUPLICATE").mode = 'ALL'

        layout.separator()

        layout.operator("gpencil.stroke_subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES")
        layout.operator("gpencil.stroke_simplify_fixed", text="Simplify", icon = "MOD_SIMPLIFY")
        layout.operator("gpencil.stroke_simplify", text="Simplify Adaptative", icon = "MOD_SIMPLIFY")

        if context.mode == 'WEIGHT_GPENCIL':
            layout.separator()
            layout.menu("VIEW3D_MT_gpencil_autoweights")

        layout.separator()

        #radial control button brush size
        myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
        myvar.data_path_primary = 'tool_settings.gpencil_sculpt.brush.size'

        #radial control button brush strength
        myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
        myvar.data_path_primary = 'tool_settings.gpencil_sculpt.brush.strength'

        layout.separator()

        # line edit toggles from the keympap
        props = layout.operator("wm.context_toggle", text="Toggle Edit Lines", icon='STROKE')
        props.data_path = "space_data.overlay.use_gpencil_edit_lines"

        props = layout.operator("wm.context_toggle", text="Toggle Multiline Edit Only", icon='STROKE')
        props.data_path = "space_data.overlay.use_gpencil_multiedit_line_only"


class VIEW3D_PT_sculpt_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_label = "Sculpt Context Menu"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.sculpt.brush
        capabilities = brush.sculpt_capabilities

        UnifiedPaintPanel.prop_unified(layout, context, brush, "size", unified_name="use_unified_size", pressure_name="use_pressure_size", slider=True,)
        UnifiedPaintPanel.prop_unified(layout, context, brush, "strength", unified_name="use_unified_strength", pressure_name="use_pressure_strength", slider=True,)

        if capabilities.has_auto_smooth:
            layout.prop(brush, "auto_smooth_factor", slider=True)

        if capabilities.has_normal_weight:
            layout.prop(brush, "normal_weight", slider=True)

        if capabilities.has_pinch_factor:
            text = "Pinch"
            if brush.sculpt_tool in {'BLOB', 'SNAKE_HOOK'}:
                text = "Magnify"
            layout.prop(brush, "crease_pinch_factor", slider=True, text=text)

        if capabilities.has_rake_factor:
            layout.prop(brush, "rake_factor", slider=True)

        if capabilities.has_plane_offset:
            layout.prop(brush, "plane_offset", slider=True)
            layout.prop(brush, "plane_trim", slider=True, text="Distance")

        if capabilities.has_height:
            layout.prop(brush, "height", slider=True, text="Height")


class TOPBAR_PT_gpencil_materials(GreasePencilMaterialsPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Materials"
    bl_ui_units_x = 14

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'


class TOPBAR_PT_gpencil_vertexcolor(GreasePencilVertexcolorPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Vertex Color"
    bl_ui_units_x = 10

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'


classes = (
    VIEW3D_HT_header,
    VIEW3D_HT_tool_header,
    ALL_MT_editormenu,
    VIEW3D_MT_editor_menus,
    VIEW3D_MT_transform,
    VIEW3D_MT_transform_base,
    VIEW3D_MT_transform_object,
    VIEW3D_MT_transform_armature,
    VIEW3D_MT_mirror,
    VIEW3D_MT_snap,
    VIEW3D_MT_uv_map_clear_seam,
    VIEW3D_MT_uv_map,
    VIEW3D_MT_view_view_selected_all_regions,
    VIEW3D_MT_view_all_all_regions,
    VIEW3D_MT_view_center_cursor_and_view_all,
    VIEW3D_MT_switchactivecamto,
    VIEW3D_MT_view,
    VIEW3D_MT_view_navigation,
    VIEW3D_MT_view_align,
    VIEW3D_MT_view_align_selected,
    VIEW3D_MT_select_object_inverse,
    VIEW3D_MT_select_object_none,
    VIEW3D_MT_select_object,
    VIEW3D_MT_select_by_type,
    VIEW3D_MT_select_grouped,
    VIEW3D_MT_select_linked,
    VIEW3D_MT_select_object_more_less,
    VIEW3D_MT_select_pose_inverse,
    VIEW3D_MT_select_pose_none,
    VIEW3D_MT_select_pose,
    VIEW3D_MT_select_particle_inverse,
    VIEW3D_MT_select_particle_none,
    VIEW3D_MT_select_particle,
    VIEW3D_MT_edit_mesh,
    VIEW3D_MT_edit_mesh_sort_elements,
    VIEW3D_MT_edit_mesh_select_similar,
    VIEW3D_MT_edit_mesh_select_more_less,
    VIEW3D_MT_select_edit_mesh_inverse,
    VIEW3D_MT_select_edit_mesh_none,
    VIEW3D_MT_select_edit_mesh,
    VIEW3D_MT_select_edit_curve_inverse,
    VIEW3D_MT_select_edit_curve_none,
    VIEW3D_MT_select_edit_curve,
    VIEW3D_MT_select_edit_curve_select_similar,
    VIEW3D_MT_select_edit_surface,
    VIEW3D_MT_select_edit_text,
    VIEW3D_MT_select_edit_metaball_inverse,
    VIEW3D_MT_select_edit_metaball_none,
    VIEW3D_MT_select_edit_metaball,
    VIEW3D_MT_edit_lattice_context_menu,
    VIEW3D_MT_select_edit_metaball_select_similar,
    VIEW3D_MT_select_edit_lattice_inverse,
    VIEW3D_MT_select_edit_lattice_none,
    VIEW3D_MT_select_edit_lattice,
    VIEW3D_MT_select_edit_armature_inverse,
    VIEW3D_MT_select_edit_armature_none,
    VIEW3D_MT_select_edit_armature,
    VIEW3D_MT_select_gpencil,
    VIEW3D_MT_select_gpencil_inverse,
    VIEW3D_MT_select_gpencil_none,
    VIEW3D_MT_select_gpencil_grouped,
    VIEW3D_MT_select_paint_mask_inverse,
    VIEW3D_MT_select_paint_mask_none,
    VIEW3D_MT_select_paint_mask,
    VIEW3D_MT_select_paint_mask_vertex_inverse,
    VIEW3D_MT_select_paint_mask_vertex_none,
    VIEW3D_MT_select_paint_mask_vertex,
    VIEW3D_MT_angle_control,
    VIEW3D_MT_mesh_add,
    VIEW3D_MT_curve_add,
    VIEW3D_MT_surface_add,
    VIEW3D_MT_edit_metaball_context_menu,
    VIEW3D_MT_metaball_add,
    TOPBAR_MT_edit_curve_add,
    TOPBAR_MT_edit_armature_add,
    VIEW3D_MT_armature_add,
    VIEW3D_MT_light_add,
    VIEW3D_MT_lightprobe_add,
    VIEW3D_MT_camera_add,
    VIEW3D_MT_volume_add,
    VIEW3D_MT_add,
    VIEW3D_MT_image_add,
    VIEW3D_MT_origin_set,
    VIEW3D_MT_object_delete_global,
    VIEW3D_MT_object,
    VIEW3D_MT_object_convert,
    VIEW3D_MT_object_animation,
    VIEW3D_MT_object_rigid_body,
    VIEW3D_MT_object_clear,
    VIEW3D_MT_object_context_menu,
    VIEW3D_MT_object_shading,
    VIEW3D_MT_object_apply,
    VIEW3D_MT_object_relations,
    VIEW3D_MT_object_parent,
    VIEW3D_MT_object_track,
    VIEW3D_MT_object_collection,
    VIEW3D_MT_object_constraints,
    VIEW3D_MT_object_quick_effects,
    VIEW3D_hide_view_set_unselected,
    VIEW3D_MT_object_showhide,
    VIEW3D_MT_make_single_user,
    VIEW3D_MT_make_links,
    VIEW3D_MT_brush,
    VIEW3D_MT_brush_curve_presets,
    VIEW3D_MT_facemask_showhide,
    VIEW3D_MT_paint_vertex,
    VIEW3D_MT_paint_vertex_specials,
    VIEW3D_MT_paint_texture_specials,
    VIEW3D_MT_hook,
    VIEW3D_MT_vertex_group,
    VIEW3D_MT_gpencil_vertex_group,
    VIEW3D_MT_paint_weight,
    VIEW3D_MT_paint_weight_lock,
    VIEW3D_MT_paint_weight_specials,
    VIEW3D_MT_subdivision_set,
    VIEW3D_MT_sculpt_specials,
    VIEW3D_MT_sculpt,
    VIEW3D_MT_sculpt_set_pivot,
    VIEW3D_MT_mask,
    VIEW3D_MT_face_sets,
    VIEW3D_MT_face_sets_init,
    VIEW3D_MT_hide_mask,
    VIEW3D_MT_particle,
    VIEW3D_MT_particle_context_menu,
    VIEW3D_particle_hide_unselected,
    VIEW3D_MT_particle_show_hide,
    VIEW3D_MT_pose,
    VIEW3D_MT_pose_transform,
    VIEW3D_MT_pose_slide,
    VIEW3D_MT_pose_propagate,
    VIEW3D_MT_pose_library,
    VIEW3D_MT_pose_motion,
    VIEW3D_MT_pose_group,
    VIEW3D_MT_pose_ik,
    VIEW3D_MT_pose_constraints,
    VIEW3D_MT_pose_names,
    VIEW3D_MT_pose_hide_unselected,
    VIEW3D_MT_pose_show_hide,
    VIEW3D_MT_pose_apply,
    VIEW3D_MT_pose_context_menu,
    VIEW3D_MT_bone_options_toggle,
    VIEW3D_MT_bone_options_enable,
    VIEW3D_MT_bone_options_disable,
    VIEW3D_MT_edit_mesh_context_menu,
    VIEW3D_MT_edit_mesh_select_mode,
    VIEW3D_MT_edit_mesh_extrude_dupli,
    VIEW3D_MT_edit_mesh_extrude_dupli_rotate,
    VIEW3D_MT_edit_mesh_extrude,
    VIEW3D_MT_edit_mesh_vertices,
    VIEW3D_MT_edit_mesh_edges,
    VIEW3D_MT_edit_mesh_edges_data,
    VIEW3D_MT_edit_mesh_faces,
    VIEW3D_MT_edit_mesh_faces_data,
    VIEW3D_normals_make_consistent_inside,
    VIEW3D_MT_edit_mesh_normals,
    VIEW3D_MT_edit_mesh_normals_select_strength,
    VIEW3D_MT_edit_mesh_normals_set_strength,
    VIEW3D_MT_edit_mesh_normals_average,
    VIEW3D_MT_edit_mesh_shading,
    VIEW3D_MT_edit_mesh_weights,
    VIEW3D_MT_edit_mesh_clean,
    VIEW3D_MT_edit_mesh_delete,
    VIEW3D_MT_edit_mesh_merge,
    VIEW3D_MT_edit_mesh_split,
    VIEW3D_MT_edit_mesh_dissolve,
    VIEW3D_mesh_hide_unselected,
    VIEW3D_curve_hide_unselected,
    VIEW3D_MT_edit_mesh_show_hide,
    VIEW3D_MT_paint_gpencil,
    VIEW3D_MT_edit_gpencil_showhide,
    VIEW3D_MT_assign_material,
    VIEW3D_MT_edit_gpencil,
    VIEW3D_MT_edit_gpencil_stroke,
    VIEW3D_MT_edit_gpencil_point,
    VIEW3D_MT_edit_gpencil_hide,
    VIEW3D_MT_edit_gpencil_arrange_strokes,
    VIEW3D_MT_edit_gpencil_delete,
    VIEW3D_MT_sculpt_gpencil_copy,
    VIEW3D_MT_weight_gpencil,
    VIEW3D_MT_vertex_gpencil,
    VIEW3D_MT_gpencil_simplify,
    VIEW3D_MT_gpencil_copy_layer,
    VIEW3D_MT_edit_curve,
    VIEW3D_MT_edit_curve_ctrlpoints,
    VIEW3D_MT_edit_curve_handle_type_set,
    VIEW3D_MT_edit_curve_segments,
    VIEW3D_MT_edit_curve_context_menu,
    VIEW3D_MT_edit_curve_delete,
    VIEW3D_MT_edit_curve_show_hide,
    VIEW3D_MT_edit_surface,
    VIEW3D_MT_edit_font,
    VIEW3D_MT_edit_font_chars,
    VIEW3D_MT_edit_font_kerning,
    VIEW3D_MT_edit_font_move,
    VIEW3D_MT_edit_font_delete,
    VIEW3D_MT_edit_font_context_menu,
    VIEW3D_MT_edit_meta,
    VIEW3D_MT_edit_meta_showhide_unselected,
    VIEW3D_MT_edit_meta_showhide,
    VIEW3D_MT_edit_lattice,
    VIEW3D_MT_edit_lattice_flip,
    VIEW3D_MT_edit_armature,
    VIEW3D_armature_hide_unselected,
    VIEW3D_MT_armature_show_hide,
    VIEW3D_MT_armature_context_menu,
    VIEW3D_MT_edit_armature_roll,
    VIEW3D_MT_edit_armature_names,
    VIEW3D_MT_edit_armature_delete,
    VIEW3D_MT_gpencil_animation,
    VIEW3D_MT_edit_gpencil_transform,
    VIEW3D_MT_object_mode_pie,
    VIEW3D_MT_view_pie,
    VIEW3D_MT_transform_gizmo_pie,
    VIEW3D_MT_shading_pie,
    VIEW3D_MT_shading_ex_pie,
    VIEW3D_MT_pivot_pie,
    VIEW3D_MT_snap_pie,
    VIEW3D_MT_orientations_pie,
    VIEW3D_MT_proportional_editing_falloff_pie,
    VIEW3D_MT_sculpt_mask_edit_pie,
    VIEW3D_MT_wpaint_vgroup_lock_pie,
    VIEW3D_MT_sculpt_face_sets_edit_pie,
    VIEW3D_PT_active_tool,
    VIEW3D_PT_active_tool_duplicate,
    VIEW3D_PT_view3d_properties,
    VIEW3D_PT_view3d_properties_edit,
    VIEW3D_PT_view3d_camera_lock,
    VIEW3D_PT_view3d_cursor,
    VIEW3D_PT_collections,
    VIEW3D_PT_object_type_visibility,
    VIEW3D_PT_grease_pencil,
    VIEW3D_PT_annotation_onion,
    VIEW3D_PT_gpencil_multi_frame,
    VIEW3D_MT_gpencil_autoweights,
    VIEW3D_MT_gpencil_edit_context_menu,
    VIEW3D_MT_gpencil_sculpt,
    VIEW3D_PT_quad_view,
    VIEW3D_PT_view3d_stereo,
    VIEW3D_PT_shading,
    VIEW3D_PT_shading_lighting,
    VIEW3D_PT_shading_color,
    VIEW3D_PT_shading_options,
    VIEW3D_PT_shading_options_shadow,
    VIEW3D_PT_shading_options_ssao,
    VIEW3D_PT_shading_render_pass,
    VIEW3D_PT_gizmo_display,
    VIEW3D_PT_overlay,
    VIEW3D_PT_overlay_guides,
    VIEW3D_PT_overlay_object,
    VIEW3D_PT_overlay_geometry,
    VIEW3D_PT_overlay_motion_tracking,
    VIEW3D_PT_overlay_edit_mesh,
    VIEW3D_PT_overlay_edit_mesh_shading,
    VIEW3D_PT_overlay_edit_mesh_measurement,
    VIEW3D_PT_overlay_edit_mesh_normals,
    VIEW3D_PT_overlay_edit_mesh_freestyle,
    VIEW3D_PT_overlay_edit_curve,
    VIEW3D_PT_overlay_texture_paint,
    VIEW3D_PT_overlay_vertex_paint,
    VIEW3D_PT_overlay_weight_paint,
    VIEW3D_PT_overlay_pose,
    VIEW3D_PT_overlay_sculpt,
    VIEW3D_PT_snapping,
    VIEW3D_PT_proportional_edit,
    VIEW3D_PT_gpencil_origin,
    VIEW3D_PT_gpencil_lock,
    VIEW3D_PT_gpencil_guide,
    VIEW3D_PT_transform_orientations,
    VIEW3D_PT_overlay_gpencil_options,
    VIEW3D_PT_context_properties,
    VIEW3D_PT_paint_vertex_context_menu,
    VIEW3D_PT_paint_texture_context_menu,
    VIEW3D_PT_paint_weight_context_menu,
    VIEW3D_PT_gpencil_vertex_context_menu,
    VIEW3D_PT_gpencil_sculpt_context_menu,
    VIEW3D_PT_gpencil_weight_context_menu,
    VIEW3D_PT_gpencil_draw_context_menu,
    VIEW3D_PT_sculpt_context_menu,
    TOPBAR_PT_gpencil_materials,
    TOPBAR_PT_gpencil_vertexcolor,
    TOPBAR_PT_annotation_layers,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
