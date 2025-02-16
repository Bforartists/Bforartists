# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later
# BFA NOTE: For this document in merges, it is best to preserve the
# Bforartists one and compare the old Blender version with the new to see
# what changed.
# Once you compare Blender changes with an old version, splice it in manually.
import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bl_ui.properties_paint_common import (
    UnifiedPaintPanel,
    brush_basic_texpaint_settings,
    brush_basic_gpencil_weight_settings,
    brush_basic_grease_pencil_weight_settings,
    brush_basic_grease_pencil_vertex_settings,
    BrushAssetShelf,
)
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
    AnnotationOnionSkin,
    GreasePencilMaterialsPanel,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)
from bpy.app.translations import (
    pgettext_iface as iface_,
    pgettext_rpt as rpt_,
    contexts as i18n_contexts,
)


class VIEW3D_HT_tool_header(Header):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_HEADER"

    def draw(self, context):
        layout = self.layout

        self.draw_tool_settings(context)

        layout.separator_spacer()

        self.draw_mode_settings(context)

    def draw_tool_settings(self, context):
        layout = self.layout
        tool_mode = context.mode

        # Active Tool
        # -----------
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

        tool = ToolSelectPanelHelper.draw_active_tool_header(
            context,
            layout,
            tool_key=("VIEW_3D", tool_mode),
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
            if tool_mode != "PAINT_WEIGHT":
                layout.popover("VIEW3D_PT_tools_brush_texture")
            if tool_mode == "PAINT_TEXTURE":
                layout.popover("VIEW3D_PT_tools_mask_texture")
            layout.popover("VIEW3D_PT_tools_brush_stroke")
            layout.popover("VIEW3D_PT_tools_brush_falloff")
            layout.popover("VIEW3D_PT_tools_brush_display")

        # NOTE: general mode options should be added to `draw_mode_settings`.
        if tool_mode == "SCULPT":
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == "PAINT_VERTEX":
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == "PAINT_WEIGHT":
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == "PAINT_TEXTURE":
            if is_valid_context:
                draw_3d_brush_settings(layout, tool_mode)
        elif tool_mode == "EDIT_ARMATURE":
            pass
        elif tool_mode == "EDIT_CURVE":
            pass
        elif tool_mode == "EDIT_MESH":
            pass
        elif tool_mode == "POSE":
            pass
        elif tool_mode == "PARTICLE":
            # Disable, only shows "Brush" panel, which is already in the top-bar.
            # if tool.use_brushes:
            #     layout.popover_group(context=".paint_common", **popover_kw)
            pass
        elif tool_mode == "PAINT_GREASE_PENCIL":
            if is_valid_context:
                brush = context.tool_settings.gpencil_paint.brush
                if brush:
                    if brush.gpencil_tool != "ERASE":
                        if brush.gpencil_tool != "TINT":
                            layout.popover(
                                "VIEW3D_PT_tools_grease_pencil_v3_brush_advanced"
                            )

                        if brush.gpencil_tool not in {"FILL", "TINT"}:
                            layout.popover(
                                "VIEW3D_PT_tools_grease_pencil_v3_brush_stroke"
                            )
                    layout.popover("VIEW3D_PT_tools_grease_pencil_paint_appearance")
        elif tool_mode == "SCULPT_GREASE_PENCIL":
            if is_valid_context:
                brush = context.tool_settings.gpencil_sculpt_paint.brush
                if brush:
                    tool = brush.gpencil_sculpt_tool
                    if tool in {"SMOOTH", "RANDOMIZE"}:
                        layout.popover(
                            "VIEW3D_PT_tools_grease_pencil_sculpt_brush_popover"
                        )
                    layout.popover("VIEW3D_PT_tools_grease_pencil_sculpt_appearance")
        elif tool_mode == "WEIGHT_GPENCIL" or tool_mode == "WEIGHT_GREASE_PENCIL":
            if is_valid_context:
                layout.popover("VIEW3D_PT_tools_grease_pencil_weight_appearance")
        elif tool_mode == "VERTEX_GPENCIL" or tool_mode == "VERTEX_GREASE_PENCIL":
            if is_valid_context:
                layout.popover("VIEW3D_PT_tools_grease_pencil_vertex_appearance")

    def draw_mode_settings(self, context):
        layout = self.layout
        mode_string = context.mode
        tool_settings = context.tool_settings

        def row_for_mirror():
            row = layout.row(align=True)
            row.label(icon="MOD_MIRROR")
            sub = row.row(align=True)
            # sub.scale_x = 0.6 #bfa - just needed for text buttons. we use icons, and then the buttons are too small
            return row, sub

        if mode_string == "EDIT_ARMATURE":
            ob = context.object
            _row, sub = row_for_mirror()
            sub.prop(
                ob.data, "use_mirror_x", icon="MIRROR_X", toggle=True, icon_only=True
            )
        elif mode_string == "POSE":
            ob = context.object
            _row, sub = row_for_mirror()
            sub.prop(
                ob.pose, "use_mirror_x", icon="MIRROR_X", toggle=True, icon_only=True
            )
        elif mode_string in {
            "EDIT_MESH",
            "PAINT_WEIGHT",
            "SCULPT",
            "PAINT_VERTEX",
            "PAINT_TEXTURE",
        }:
            # Mesh Modes, Use Mesh Symmetry
            ob = context.object
            row, sub = row_for_mirror()
            sub.prop(
                ob, "use_mesh_mirror_x", icon="MIRROR_X", toggle=True, icon_only=True
            )
            sub.prop(
                ob, "use_mesh_mirror_y", icon="MIRROR_Y", toggle=True, icon_only=True
            )
            sub.prop(
                ob, "use_mesh_mirror_z", icon="MIRROR_Z", toggle=True, icon_only=True
            )
            if mode_string == "EDIT_MESH":
                layout.prop(tool_settings, "use_mesh_automerge", text="")
            elif mode_string == "PAINT_WEIGHT":
                row.popover(
                    panel="VIEW3D_PT_tools_weightpaint_symmetry_for_topbar", text=""
                )
            elif mode_string == "SCULPT":
                row.popover(panel="VIEW3D_PT_sculpt_symmetry_for_topbar", text="")
            elif mode_string == "PAINT_VERTEX":
                row.popover(
                    panel="VIEW3D_PT_tools_vertexpaint_symmetry_for_topbar", text=""
                )
        elif mode_string == "SCULPT_CURVES":
            ob = context.object
            _row, sub = row_for_mirror()
            sub.prop(
                ob.data, "use_mirror_x", icon="MIRROR_X", toggle=True, icon_only=True
            )
            sub.prop(
                ob.data, "use_mirror_y", icon="MIRROR_Y", toggle=True, icon_only=True
            )
            sub.prop(
                ob.data, "use_mirror_z", icon="MIRROR_Z", toggle=True, icon_only=True
            )

            row = layout.row(align=True)
            row.prop(
                ob.data,
                "use_sculpt_collision",
                icon="MOD_PHYSICS",
                icon_only=True,
                toggle=True,
            )
            sub = row.row(align=True)
            sub.active = ob.data.use_sculpt_collision
            sub.prop(ob.data, "surface_collision_distance")

        # Expand panels from the side-bar as popovers.
        popover_kw = {"space_type": "VIEW_3D", "region_type": "UI", "category": "Tool"}

        if mode_string == "SCULPT":
            layout.popover_group(context=".sculpt_mode", **popover_kw)
        elif mode_string == "PAINT_VERTEX":
            layout.popover_group(context=".vertexpaint", **popover_kw)
        elif mode_string == "PAINT_WEIGHT":
            layout.popover_group(context=".weightpaint", **popover_kw)
        elif mode_string == "PAINT_TEXTURE":
            layout.popover_group(context=".imagepaint", **popover_kw)
        elif mode_string == "EDIT_TEXT":
            layout.popover_group(context=".text_edit", **popover_kw)
        elif mode_string == "EDIT_ARMATURE":
            layout.popover_group(context=".armature_edit", **popover_kw)
        elif mode_string == "EDIT_METABALL":
            layout.popover_group(context=".mball_edit", **popover_kw)
        elif mode_string == "EDIT_LATTICE":
            layout.popover_group(context=".lattice_edit", **popover_kw)
        elif mode_string == "EDIT_CURVE":
            layout.popover_group(context=".curve_edit", **popover_kw)
        elif mode_string == "EDIT_MESH":
            layout.popover_group(context=".mesh_edit", **popover_kw)
        elif mode_string == "POSE":
            layout.popover_group(context=".posemode", **popover_kw)
        elif mode_string == "PARTICLE":
            layout.popover_group(context=".particlemode", **popover_kw)
        elif mode_string == "OBJECT":
            layout.popover_group(context=".objectmode", **popover_kw)

        if mode_string in {
            "EDIT_GREASE_PENCIL",
            "PAINT_GREASE_PENCIL",
            "SCULPT_GREASE_PENCIL",
            "WEIGHT_GREASE_PENCIL",
            "VERTEX_GREASE_PENCIL",
        }:
            row = layout.row(align=True)
            row.prop(tool_settings, "use_grease_pencil_multi_frame_editing", text="")

            if mode_string in {
                "EDIT_GREASE_PENCIL",
                "SCULPT_GREASE_PENCIL",
                "WEIGHT_GREASE_PENCIL",
                "VERTEX_GREASE_PENCIL",
            }:
                sub = row.row(align=True)
                if tool_settings.use_grease_pencil_multi_frame_editing:
                    sub.popover(
                        panel="VIEW3D_PT_grease_pencil_multi_frame",
                        text="",
                    )

            # BFA - menu
            if mode_string in {
                "EDIT_GREASE_PENCIL",
            }:
                sub = row.row(align=True)
                sub.popover(
                    panel="VIEW3D_PT_greasepencil_edit_options",
                    text="Options",
                )

        if mode_string == "PAINT_GREASE_PENCIL":
            layout.prop(
                tool_settings, "use_gpencil_draw_additive", text="", icon="FREEZE"
            )
            layout.prop(tool_settings, "use_gpencil_automerge_strokes", text="")
            layout.prop(
                tool_settings, "use_gpencil_weight_data_add", text="", icon="WPAINT_HLT"
            )
            layout.prop(
                tool_settings, "use_gpencil_draw_onback", text="", icon="MOD_OPACITY"
            )


class _draw_tool_settings_context_mode:
    @staticmethod
    def SCULPT(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        paint = context.tool_settings.sculpt
        brush = paint.brush

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        if brush is None:
            return False

        tool_settings = context.tool_settings
        capabilities = brush.sculpt_capabilities

        ups = tool_settings.unified_paint_settings

        if capabilities.has_color:
            row = layout.row(align=True)
            row.ui_units_x = 4
            UnifiedPaintPanel.prop_unified_color(row, context, brush, "color", text="")
            UnifiedPaintPanel.prop_unified_color(
                row, context, brush, "secondary_color", text=""
            )
            row.separator()
            layout.prop(brush, "blend", text="", expand=False)

        size = "size"
        size_owner = ups if ups.use_unified_size else brush
        if size_owner.use_locked_size == "SCENE":
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
            header=True,
        )

        # strength, use_strength_pressure
        pressure_name = (
            "use_pressure_strength" if capabilities.has_strength_pressure else None
        )
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "strength",
            pressure_name=pressure_name,
            unified_name="use_unified_strength",
            text="Strength",
            header=True,
        )

        # direction
        if not capabilities.has_direction:
            layout.row().prop(brush, "direction", expand=True, text="")

        return True

    @staticmethod
    def PAINT_TEXTURE(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        paint = context.tool_settings.image_paint
        brush = paint.brush

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        if brush is None:
            return False

        brush_basic_texpaint_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def PAINT_VERTEX(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        paint = context.tool_settings.vertex_paint
        brush = paint.brush

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        if brush is None:
            return False

        brush_basic_texpaint_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def PAINT_WEIGHT(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        paint = context.tool_settings.weight_paint
        brush = paint.brush

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

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
                header=True,
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
            header=True,
        )
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "strength",
            pressure_name="use_pressure_strength",
            unified_name="use_unified_strength",
            header=True,
        )

        return True

    @staticmethod
    def SCULPT_GREASE_PENCIL(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        paint = context.tool_settings.gpencil_sculpt_paint
        brush = paint.brush
        if brush is None:
            return False

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        tool_settings = context.tool_settings
        capabilities = brush.sculpt_capabilities

        ups = tool_settings.unified_paint_settings

        size = "size"
        size_owner = ups if ups.use_unified_size else brush
        if size_owner.use_locked_size == "SCENE":
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
            header=True,
        )

        # strength, use_strength_pressure
        pressure_name = (
            "use_pressure_strength" if capabilities.has_strength_pressure else None
        )
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "strength",
            pressure_name=pressure_name,
            unified_name="use_unified_strength",
            text="Strength",
            header=True,
        )

        # direction
        if brush.gpencil_sculpt_tool in {"THICKNESS", "STRENGTH", "PINCH", "TWIST"}:
            layout.row().prop(brush, "direction", expand=True, text="")

        # Brush falloff
        # layout.popover("VIEW3D_PT_tools_brush_falloff") # BFA - moved to be
        # consistent with other brushes in the properties_paint_common.py file

        return True

    @staticmethod
    def WEIGHT_GREASE_PENCIL(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        paint = context.tool_settings.gpencil_weight_paint
        brush = paint.brush
        if brush is None:
            return False

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        brush_basic_grease_pencil_weight_settings(layout, context, brush, compact=True)

        layout.popover("VIEW3D_PT_tools_grease_pencil_weight_options", text="Options")
        layout.popover(
            "VIEW3D_PT_tools_grease_pencil_brush_weight_falloff", text="Falloff"
        )

        return True

    @staticmethod
    def VERTEX_GREASE_PENCIL(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        tool_settings = context.tool_settings
        paint = tool_settings.gpencil_vertex_paint
        brush = paint.brush

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        if brush.gpencil_vertex_tool not in {"BLUR", "AVERAGE", "SMEAR"}:
            layout.separator(factor=0.4)
            ups = context.tool_settings.unified_paint_settings
            prop_owner = ups if ups.use_unified_color else brush

            sub = layout.row(align=True)
            sub.prop_with_popover(
                prop_owner,
                "color",
                text="",
                panel="TOPBAR_PT_grease_pencil_vertex_color",
            )
            sub.prop(prop_owner, "secondary_color", text="")
            sub.operator("paint.brush_colors_flip", icon="FILE_REFRESH", text="")

        brush_basic_grease_pencil_vertex_settings(layout, context, brush, compact=True)

        return True

    @staticmethod
    def PARTICLE(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        # See: `VIEW3D_PT_tools_brush`, basically a duplicate
        tool_settings = context.tool_settings
        settings = tool_settings.particle_edit
        brush = settings.brush
        tool = settings.tool
        if tool == "NONE":
            return False

        layout.prop(brush, "size", slider=True)
        if tool == "ADD":
            layout.prop(brush, "count")

            layout.prop(settings, "use_default_interpolate")
            layout.prop(brush, "steps", slider=True)
            layout.prop(settings, "default_key_count", slider=True)
        else:
            layout.prop(brush, "strength", slider=True)

            if tool == "LENGTH":
                layout.row().prop(brush, "length_mode", expand=True)
            elif tool == "PUFF":
                layout.row().prop(brush, "puff_mode", expand=True)
                layout.prop(brush, "use_puff_volume")
            elif tool == "COMB":
                row = layout.row()
                row.active = settings.is_editable
                row.prop(settings, "use_emitter_deflect", text="Deflect Emitter")
                sub = row.row(align=True)
                sub.active = settings.use_emitter_deflect
                sub.prop(settings, "emitter_distance", text="Distance")

        return True

    @staticmethod
    def SCULPT_CURVES(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        tool_settings = context.tool_settings
        paint = tool_settings.curves_sculpt
        brush = paint.brush

        BrushAssetShelf.draw_popup_selector(layout, context, brush)

        if brush is None:
            return False

        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "size",
            unified_name="use_unified_size",
            pressure_name="use_pressure_size",
            text="Radius",
            slider=True,
            header=True,
        )

        if brush.curves_sculpt_tool not in {"ADD", "DELETE"}:
            use_strength_pressure = brush.curves_sculpt_tool not in {"SLIDE"}
            UnifiedPaintPanel.prop_unified(
                layout,
                context,
                brush,
                "strength",
                unified_name="use_unified_strength",
                pressure_name="use_pressure_strength"
                if use_strength_pressure
                else None,
                header=True,
            )

        curves_tool = brush.curves_sculpt_tool

        if curves_tool == "COMB":
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover("VIEW3D_PT_tools_brush_falloff", text="Brush Falloff")
            layout.popover(
                "VIEW3D_PT_curves_sculpt_parameter_falloff", text="Curve Falloff"
            )
        elif curves_tool == "ADD":
            layout.prop(brush, "falloff_shape", expand=True)
            layout.prop(brush.curves_sculpt_settings, "add_amount")
            layout.popover("VIEW3D_PT_curves_sculpt_add_shape", text="Curve Shape")
            layout.prop(brush, "use_frontface", text="Front Faces Only")
        elif curves_tool == "GROW_SHRINK":
            layout.prop(brush, "direction", expand=True, text="")
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover(
                "VIEW3D_PT_curves_sculpt_grow_shrink_scaling", text="Scaling"
            )
            layout.popover("VIEW3D_PT_tools_brush_falloff")
        elif curves_tool == "SNAKE_HOOK":
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover("VIEW3D_PT_tools_brush_falloff")
        elif curves_tool == "DELETE":
            layout.prop(brush, "falloff_shape", expand=True)
        elif curves_tool == "SELECTION_PAINT":
            layout.prop(brush, "direction", expand=True, text="")
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover("VIEW3D_PT_tools_brush_falloff")
        elif curves_tool == "PINCH":
            layout.prop(brush, "direction", expand=True, text="")
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover("VIEW3D_PT_tools_brush_falloff")
        elif curves_tool == "SMOOTH":
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover("VIEW3D_PT_tools_brush_falloff")
        elif curves_tool == "PUFF":
            layout.prop(brush, "falloff_shape", expand=True)
            layout.popover("VIEW3D_PT_tools_brush_falloff")
        elif curves_tool == "DENSITY":
            layout.prop(brush, "falloff_shape", expand=True)
            row = layout.row(align=True)
            row.prop(brush.curves_sculpt_settings, "density_mode", text="", expand=True)
            row = layout.row(align=True)
            row.prop(
                brush.curves_sculpt_settings, "minimum_distance", text="Distance Min"
            )
            row.operator_context = "INVOKE_REGION_WIN"
            row.operator(
                "sculpt_curves.min_distance_edit", text="", icon="DRIVER_DISTANCE"
            )
            row = layout.row(align=True)
            row.enabled = brush.curves_sculpt_settings.density_mode != "REMOVE"
            row.prop(
                brush.curves_sculpt_settings, "density_add_attempts", text="Count Max"
            )
            layout.popover("VIEW3D_PT_tools_brush_falloff")
            layout.popover("VIEW3D_PT_curves_sculpt_add_shape", text="Curve Shape")
        elif curves_tool == "SLIDE":
            layout.popover("VIEW3D_PT_tools_brush_falloff")

        return True

    @staticmethod
    def PAINT_GREASE_PENCIL(context, layout, tool):
        if (tool is None) or (not tool.use_brushes):
            return False

        # These draw their own properties.
        if tool.idname in {
            "builtin.arc",
            "builtin.curve",
            "builtin.line",
            "builtin.box",
            "builtin.circle",
            "builtin.polyline",
        }:
            return False

        tool_settings = context.tool_settings
        paint = tool_settings.gpencil_paint

        brush = paint.brush
        if brush is None:
            return False

        row = layout.row(align=True)

        BrushAssetShelf.draw_popup_selector(row, context, brush)

        grease_pencil_tool = brush.gpencil_tool

        if grease_pencil_tool in {"DRAW", "FILL"}:
            from bl_ui.properties_paint_common import (
                brush_basic__draw_color_selector,
            )

            brush_basic__draw_color_selector(
                context, layout, brush, brush.gpencil_settings
            )

        if grease_pencil_tool == "TINT":
            row.separator(factor=0.4)
            row.prop_with_popover(
                brush, "color", text="", panel="TOPBAR_PT_grease_pencil_vertex_color"
            )

        from bl_ui.properties_paint_common import (
            brush_basic_grease_pencil_paint_settings,
        )

        brush_basic_grease_pencil_paint_settings(
            layout, context, brush, None, compact=True
        )

        return True


def draw_topbar_grease_pencil_layer_panel(context, layout):
    grease_pencil = context.object.data
    layer = grease_pencil.layers.active
    group = grease_pencil.layer_groups.active

    icon = "OUTLINER_DATA_GP_LAYER"
    node_name = None
    if layer or group:
        icon = (
            "OUTLINER_DATA_GP_LAYER" if layer else "GREASEPENCIL_LAYER_GROUP"
        )  # BFA - wip, icons needs updating
        node_name = layer.name if layer else group.name

        # Clamp long names otherwise the selector can get too wide.
        max_width = 25
        if len(node_name) > max_width:
            node_name = node_name[: max_width - 5] + ".." + node_name[-3:]

    sub = layout.row()
    sub.popover(
        panel="TOPBAR_PT_grease_pencil_layers",
        text=node_name,
        icon=icon,
    )


class VIEW3D_HT_header(Header):
    bl_space_type = "VIEW_3D"

    @staticmethod
    def draw_xform_template(layout, context):
        obj = context.active_object
        mode_string = context.mode
        object_mode = "OBJECT" if obj is None else obj.mode
        has_pose_mode = (object_mode == "POSE") or (
            object_mode == "WEIGHT_PAINT" and context.pose_object is not None
        )

        tool_settings = context.tool_settings

        # Mode & Transform Settings
        scene = context.scene

        # Orientation
        if object_mode in {"OBJECT", "EDIT", "EDIT_GREASE_PENCIL"} or has_pose_mode:
            orient_slot = scene.transform_orientation_slots[0]

            # BFA - WIP, add grease pencil curve type

            row = layout.row(align=True)
            row.prop_with_popover(
                orient_slot,
                "type",
                text="",
                panel="VIEW3D_PT_transform_orientations",
            )

        # Pivot
        if has_pose_mode or object_mode in {
            "OBJECT",
            "EDIT",
            "EDIT_GREASE_PENCIL",
            "SCULPT_GREASE_PENCIL",
        }:
            layout.prop(tool_settings, "transform_pivot_point", text="", icon_only=True)

        # Snap
        show_snap = False
        if obj is None:
            show_snap = True
        else:
            if has_pose_mode or (
                object_mode
                not in {
                    "SCULPT",
                    "SCULPT_CURVES",
                    "VERTEX_PAINT",
                    "WEIGHT_PAINT",
                    "TEXTURE_PAINT",
                    "PAINT_GREASE_PENCIL",
                    "SCULPT_GREASE_PENCIL",
                    "WEIGHT_GREASE_PENCIL",
                    "VERTEX_GREASE_PENCIL",
                }
            ):
                show_snap = True
            else:
                paint_settings = UnifiedPaintPanel.paint_settings(context)

                if paint_settings:
                    brush = paint_settings.brush
                    if (
                        brush
                        and hasattr(brush, "stroke_method")
                        and brush.stroke_method == "CURVE"
                    ):
                        show_snap = True

        if show_snap:
            snap_items = bpy.types.ToolSettings.bl_rna.properties[
                "snap_elements"
            ].enum_items
            snap_elements = tool_settings.snap_elements
            if len(snap_elements) == 1:
                text = ""
                for elem in snap_elements:
                    icon = snap_items[elem].icon
                    break
            else:
                text = iface_("Mix", i18n_contexts.editor_view3d)
                icon = "NONE"
            del snap_items, snap_elements

            row = layout.row(align=True)
            row.prop(tool_settings, "use_snap", text="")

            sub = row.row(align=True)
            sub.popover(
                panel="VIEW3D_PT_snapping",
                icon=icon,
                text=text,
                translate=False,
            )

        # Proportional editing
        if (
            object_mode
            in {
                "EDIT",
                "PARTICLE_EDIT",
                "SCULPT_GREASE_PENCIL",
                "EDIT_GREASE_PENCIL",
                "OBJECT",
            }
            and context.mode != "EDIT_ARMATURE"
        ):
            row = layout.row(align=True)
            kw = {}
            if object_mode == "OBJECT":
                attr = "use_proportional_edit_objects"
            else:
                attr = "use_proportional_edit"

                if tool_settings.use_proportional_edit:
                    if tool_settings.use_proportional_connected:
                        kw["icon"] = "PROP_CON"
                    elif tool_settings.use_proportional_projected:
                        kw["icon"] = "PROP_PROJECTED"
                    else:
                        kw["icon"] = "PROP_ON"
                else:
                    kw["icon"] = "PROP_OFF"

            row.prop(tool_settings, attr, icon_only=True, **kw)
            sub = row.row(align=True)
            # BFA hide UI via "if" statement instead of greying out
            if getattr(tool_settings, attr):
                sub.prop_with_popover(
                    tool_settings,
                    "proportional_edit_falloff",
                    text="",
                    icon_only=True,
                    panel="VIEW3D_PT_proportional_edit",
                )

        # BFA - handle types for curves, formerly in the control points menu
        if mode_string in {"EDIT_CURVE"}:
            layout.operator_menu_enum(
                "curve.handle_type_set", "type", text="", icon="HANDLE_AUTO"
            )

        if object_mode == "EDIT" and obj.type == "GREASEPENCIL":
            draw_topbar_grease_pencil_layer_panel(context, layout)

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        view = context.space_data
        shading = view.shading
        overlay = view.overlay

        # bfa - show hide the editormenu, editor suffix is needed.
        ALL_MT_editormenu_view3d.draw_hidden(context, layout)

        obj = context.active_object
        mode_string = context.mode
        object_mode = "OBJECT" if obj is None else obj.mode
        has_pose_mode = (object_mode == "POSE") or (
            object_mode == "WEIGHT_PAINT" and context.pose_object is not None
        )

        # Note: This is actually deadly in case enum_items have to be dynamically generated
        #       (because internal RNA array iterator will free everything immediately...).
        # XXX This is an RNA internal issue, not sure how to fix it.
        # Note: Tried to add an accessor to get translated UI strings instead of manual call
        #       to pgettext_iface below, but this fails because translated enum-items
        #       are always dynamically allocated.
        act_mode_item = bpy.types.Object.bl_rna.properties["mode"].enum_items[
            object_mode
        ]
        act_mode_i18n_context = bpy.types.Object.bl_rna.properties[
            "mode"
        ].translation_context

        row = layout.row(align=True)
        row.separator()

        sub = row.row(align=True)
        sub.operator_menu_enum(
            "object.mode_set",
            "mode",
            text=iface_(act_mode_item.name, act_mode_i18n_context),
            icon=act_mode_item.icon,
        )
        del act_mode_item

        layout.template_header_3D_mode()

        # Contains buttons like Mode, Pivot, Layer, Mesh Select Mode...
        if obj:
            # Particle edit
            if object_mode == "PARTICLE_EDIT":
                row = layout.row()
                row.prop(
                    tool_settings.particle_edit, "select_mode", text="", expand=True
                )
            elif object_mode in {"EDIT", "SCULPT_CURVES"} and obj.type == "CURVES":
                curves = obj.data

                row = layout.row(align=True)
                domain = curves.selection_domain
                row.operator(
                    "curves.set_selection_domain",
                    text="",
                    icon="CURVE_BEZCIRCLE",
                    depress=(domain == "POINT"),
                ).domain = "POINT"
                row.operator(
                    "curves.set_selection_domain",
                    text="",
                    icon="CURVE_PATH",
                    depress=(domain == "CURVE"),
                ).domain = "CURVE"

        # Grease Pencil
        if obj and obj.type == "GREASEPENCIL":
            # Select mode for Editing
            if object_mode == "EDIT":
                row = layout.row(align=True)
                row.operator(
                    "grease_pencil.set_selection_mode",
                    text="",
                    icon="GP_SELECT_POINTS",
                    depress=(tool_settings.gpencil_selectmode_edit == "POINT"),
                ).mode = "POINT"
                row.operator(
                    "grease_pencil.set_selection_mode",
                    text="",
                    icon="GP_SELECT_STROKES",
                    depress=(tool_settings.gpencil_selectmode_edit == "STROKE"),
                ).mode = "STROKE"
                row.operator(
                    "grease_pencil.set_selection_mode",
                    text="",
                    icon="GP_SELECT_BETWEEN_STROKES",
                    depress=(tool_settings.gpencil_selectmode_edit == "SEGMENT"),
                ).mode = "SEGMENT"

            if object_mode == "SCULPT_GREASE_PENCIL":
                row = layout.row(align=True)
                row.prop(tool_settings, "use_gpencil_select_mask_point", text="")
                row.prop(tool_settings, "use_gpencil_select_mask_stroke", text="")
                row.prop(tool_settings, "use_gpencil_select_mask_segment", text="")

            if object_mode == "VERTEX_GREASE_PENCIL":
                row = layout.row(align=True)
                row.prop(tool_settings, "use_gpencil_vertex_select_mask_point", text="")
                row.prop(
                    tool_settings, "use_gpencil_vertex_select_mask_stroke", text=""
                )
                row.prop(
                    tool_settings, "use_gpencil_vertex_select_mask_segment", text=""
                )

        overlay = view.overlay

        VIEW3D_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        if object_mode in {"PAINT_GREASE_PENCIL", "SCULPT_GREASE_PENCIL"}:
            # Grease pencil
            if object_mode == "PAINT_GREASE_PENCIL":
                sub = layout.row(align=True)
                sub.prop_with_popover(
                    tool_settings,
                    "gpencil_stroke_placement_view3d",
                    text="",
                    panel="VIEW3D_PT_grease_pencil_origin",
                )

            sub = layout.row(align=True)
            sub.active = tool_settings.gpencil_stroke_placement_view3d != "SURFACE"
            sub.prop_with_popover(
                tool_settings.gpencil_sculpt,
                "lock_axis",
                text="",
                panel="VIEW3D_PT_grease_pencil_lock",
            )

            draw_topbar_grease_pencil_layer_panel(context, layout)

            if object_mode == "PAINT_GREASE_PENCIL":
                # FIXME: this is bad practice!
                # Tool options are to be displayed in the top-bar.
                tool = context.workspace.tools.from_space_view3d_mode(object_mode)
                if tool and tool.idname == "builtin_brush.Draw":
                    settings = tool_settings.gpencil_sculpt.guide
                    row = layout.row(align=True)
                    row.prop(settings, "use_guide", text="", icon="GRID")
                    sub = row.row(align=True)
                    if settings.use_guide:
                        sub.popover(
                            panel="VIEW3D_PT_grease_pencil_guide",
                            text="Guides",
                        )

            if object_mode == "SCULPT_GREASE_PENCIL":
                layout.popover(
                    panel="VIEW3D_PT_grease_pencil_sculpt_automasking",
                    text="",
                    icon=VIEW3D_HT_header._grease_pencil_sculpt_automasking_icon(
                        tool_settings.gpencil_sculpt
                    ),
                )

            if object_mode == "SCULPT_GREASE_PENCIL":
                layout.popover(
                    panel="VIEW3D_PT_grease_pencil_sculpt_automasking",
                    text="",
                    icon=VIEW3D_HT_header._grease_pencil_sculpt_automasking_icon(
                        tool_settings.gpencil_sculpt
                    ),
                )

        elif object_mode == "SCULPT":
            # If the active tool supports it, show the canvas selector popover.
            from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

            tool = ToolSelectPanelHelper.tool_active_from_context(context)

            is_paint_tool = False
            if tool.use_brushes:
                paint = tool_settings.sculpt
                brush = paint.brush
                if brush:
                    is_paint_tool = brush.sculpt_tool in {"PAINT", "SMEAR"}
            else:
                is_paint_tool = tool and tool.use_paint_canvas

            shading = VIEW3D_PT_shading.get_shading(context)
            color_type = shading.color_type

            row = layout.row()
            row.active = is_paint_tool and color_type == "VERTEX"

            if context.preferences.experimental.use_sculpt_texture_paint:
                canvas_source = tool_settings.paint_mode.canvas_source
                icon = (
                    "GROUP_VCOL"
                    if canvas_source == "COLOR_ATTRIBUTE"
                    else canvas_source
                )
                row.popover(panel="VIEW3D_PT_slots_paint_canvas", icon=icon)
                # TODO: Update this boolean condition so that the Canvas button is only active when
                # the appropriate color types are selected in Solid mode, I.E. 'TEXTURE'
                row.active = is_paint_tool
            else:
                row.popover(panel="VIEW3D_PT_slots_color_attributes", icon="GROUP_VCOL")

            layout.popover(
                panel="VIEW3D_PT_sculpt_snapping",
                icon="SNAP_INCREMENT",
                text="",
                translate=False,
            )

            layout.popover(
                panel="VIEW3D_PT_sculpt_automasking",
                text="",
                icon=VIEW3D_HT_header._sculpt_automasking_icon(tool_settings.sculpt),
            )

        elif object_mode == "VERTEX_PAINT":
            row = layout.row()
            row.popover(panel="VIEW3D_PT_slots_color_attributes", icon="GROUP_VCOL")
        elif object_mode == "VERTEX_GREASE_PENCIL":
            draw_topbar_grease_pencil_layer_panel(context, layout)
        elif object_mode == "WEIGHT_PAINT":
            row = layout.row()
            row.popover(panel="VIEW3D_PT_slots_vertex_groups", icon="GROUP_VERTEX")

            layout.popover(
                panel="VIEW3D_PT_sculpt_snapping",
                icon="SNAP_INCREMENT",
                text="",
                translate=False,
            )
        elif object_mode == "WEIGHT_GREASE_PENCIL":
            row = layout.row()
            row.popover(panel="VIEW3D_PT_slots_vertex_groups", icon="GROUP_VERTEX")
            draw_topbar_grease_pencil_layer_panel(context, row)

        elif object_mode == "TEXTURE_PAINT":
            tool_mode = tool_settings.image_paint.mode
            icon = "MATERIAL" if tool_mode == "MATERIAL" else "IMAGE_DATA"

            row = layout.row()
            row.popover(panel="VIEW3D_PT_slots_projectpaint", icon=icon)
            row.popover(
                panel="VIEW3D_PT_mask",
                icon=VIEW3D_HT_header._texture_mask_icon(tool_settings.image_paint),
                text="",
            )
        else:
            # Transform settings depending on tool header visibility
            VIEW3D_HT_header.draw_xform_template(layout, context)

        layout.separator_spacer()

        # Viewport Settings
        layout.popover(
            panel="VIEW3D_PT_object_type_visibility",
            icon_value=view.icon_from_show_object_viewport,
            text="",
        )

        # Gizmo toggle & popover.
        row = layout.row(align=True)
        # FIXME: place-holder icon.
        row.prop(view, "show_gizmo", text="", toggle=True, icon="GIZMO")
        sub = row.row(align=True)
        sub.active = view.show_gizmo
        sub.popover(
            panel="VIEW3D_PT_gizmo_display",
            text="",
        )

        # Overlay toggle & popover.
        row = layout.row(align=True)
        row.prop(overlay, "show_overlays", icon="OVERLAY", text="")
        sub = row.row(align=True)
        sub.active = overlay.show_overlays
        sub.popover(panel="VIEW3D_PT_overlay", text="")

        if mode_string == "EDIT_MESH":
            sub.popover(
                panel="VIEW3D_PT_overlay_edit_mesh", text="", icon="EDITMODE_HLT"
            )
        if mode_string == "EDIT_CURVE":
            sub.popover(
                panel="VIEW3D_PT_overlay_edit_curve", text="", icon="EDITMODE_HLT"
            )
        elif mode_string == "EDIT_CURVES":
            sub.popover(
                panel="VIEW3D_PT_overlay_edit_curves", text="", icon="EDITMODE_HLT"
            )
        elif mode_string == "SCULPT":
            sub.popover(
                panel="VIEW3D_PT_overlay_sculpt", text="", icon="SCULPTMODE_HLT"
            )
        elif mode_string == "SCULPT_CURVES":
            sub.popover(
                panel="VIEW3D_PT_overlay_sculpt_curves", text="", icon="SCULPTMODE_HLT"
            )
        elif mode_string == "PAINT_WEIGHT":
            sub.popover(
                panel="VIEW3D_PT_overlay_weight_paint", text="", icon="WPAINT_HLT"
            )
        elif mode_string == "PAINT_TEXTURE":
            sub.popover(
                panel="VIEW3D_PT_overlay_texture_paint", text="", icon="TPAINT_HLT"
            )
        elif mode_string == "PAINT_VERTEX":
            sub.popover(
                panel="VIEW3D_PT_overlay_vertex_paint", text="", icon="VPAINT_HLT"
            )
        elif obj is not None and obj.type == "GREASEPENCIL":
            sub.popover(
                panel="VIEW3D_PT_overlay_grease_pencil_options",
                text="",
                icon="OUTLINER_DATA_GREASEPENCIL",
            )

        # Separate from `elif` chain because it may coexist with weight-paint.
        if has_pose_mode or (
            object_mode in {"EDIT_ARMATURE", "OBJECT"}
            and VIEW3D_PT_overlay_bones.is_using_wireframe(context)
        ):
            sub.popover(panel="VIEW3D_PT_overlay_bones", text="", icon="POSE_HLT")

        row = layout.row(align=True)
        row.active = (object_mode == "EDIT") or (shading.type in {"WIREFRAME", "SOLID"})

        # While exposing `shading.show_xray(_wireframe)` is correct.
        # this hides the key shortcut from users: #70433.
        if has_pose_mode:
            draw_depressed = overlay.show_xray_bone
        elif shading.type == "WIREFRAME":
            draw_depressed = shading.show_xray_wireframe
        else:
            draw_depressed = shading.show_xray
        row.operator(
            "view3d.toggle_xray",
            text="",
            icon="XRAY",
            depress=draw_depressed,
        )
        # BFA - custom operator from the Power User Tools to toggle the viewport silhuette
        row = layout.row(align=True)
        if context.preferences.addons.get("bfa_power_user_tools"):
            if context.window_manager.BFA_UI_addon_props.BFA_PROP_toggle_viewport:
                row.operator(
                    "view3d.viewport_silhouette_toggle", text="", icon="IMAGE_ALPHA"
                )

        row = layout.row(align=True)
        row.prop(shading, "type", text="", expand=True)
        sub = row.row(align=True)
        # TODO, currently render shading type ignores mesh two-side, until it's supported
        # show the shading popover which shows double-sided option.

        # sub.enabled = shading.type != 'RENDERED'
        sub.popover(panel="VIEW3D_PT_shading", text="")

    @staticmethod
    def _sculpt_automasking_icon(sculpt):
        automask_enabled = (
            sculpt.use_automasking_topology
            or sculpt.use_automasking_face_sets
            or sculpt.use_automasking_boundary_edges
            or sculpt.use_automasking_boundary_face_sets
            or sculpt.use_automasking_cavity
            or sculpt.use_automasking_cavity_inverted
            or sculpt.use_automasking_start_normal
            or sculpt.use_automasking_view_normal
        )

        return "MOD_MASK" if automask_enabled else "MOD_MASK_OFF"  # BFA - mask icon

    @staticmethod
    def _grease_pencil_sculpt_automasking_icon(gpencil_sculpt):
        automask_enabled = (
            gpencil_sculpt.use_automasking_stroke
            or gpencil_sculpt.use_automasking_layer_stroke
            or gpencil_sculpt.use_automasking_material_stroke
            or gpencil_sculpt.use_automasking_material_active
            or gpencil_sculpt.use_automasking_layer_active
        )

        return "MOD_MASK" if automask_enabled else "MOD_MASK_OFF"  # BFA - mask icon

    @staticmethod
    def _texture_mask_icon(ipaint):
        mask_enabled = ipaint.use_stencil_layer or ipaint.use_cavity
        return "MOD_MASK" if mask_enabled else "MOD_MASK_OFF"  # BFA - mask icon


# BFA - show hide the editormenu, editor suffix is needed.
class ALL_MT_editormenu_view3d(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def _texture_mask_icon(ipaint):
        mask_enabled = ipaint.use_stencil_layer or ipaint.use_cavity
        return "MOD_MASK" if mask_enabled else "MOD_MASK_OFF"

    @staticmethod
    def draw_menus(layout, context):
        row = layout.row(align=True)
        row.template_header()  # editor type menus

    # bfa - do not place any content here, it does not belong into this class !!!


class VIEW3D_MT_editor_menus(Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mode_string = context.mode
        edit_object = context.edit_object
        tool_settings = context.tool_settings

        layout.menu("SCREEN_MT_user_menu", text="Quick")  # BFA
        layout.menu("VIEW3D_MT_view")
        layout.menu("VIEW3D_MT_view_navigation")  # BFA

        # Select Menu
        if mode_string in {"PAINT_WEIGHT", "PAINT_VERTEX", "PAINT_TEXTURE"}:
            mesh = obj.data
            if mesh.use_paint_mask:
                layout.menu("VIEW3D_MT_select_paint_mask")
            elif mesh.use_paint_mask_vertex and mode_string in {
                "PAINT_WEIGHT",
                "PAINT_VERTEX",
            }:
                layout.menu("VIEW3D_MT_select_paint_mask_vertex")
        elif mode_string not in {
            "SCULPT",
            "SCULPT_CURVES",
            "PAINT_GREASE_PENCIL",
            "SCULPT_GREASE_PENCIL",
            "WEIGHT_GREASE_PENCIL",
            "VERTEX_GREASE_PENCIL",
        }:
            layout.menu("VIEW3D_MT_select_" + mode_string.lower())

        if mode_string == "OBJECT":
            layout.menu("VIEW3D_MT_add")
        elif mode_string == "EDIT_MESH":
            layout.menu(
                "VIEW3D_MT_mesh_add",
                text="Add",
                text_ctxt=i18n_contexts.operator_default,
            )
        elif mode_string == "EDIT_CURVE":
            layout.menu(
                "VIEW3D_MT_curve_add",
                text="Add",
                text_ctxt=i18n_contexts.operator_default,
            )
        elif mode_string == "EDIT_CURVES":
            layout.menu(
                "VIEW3D_MT_edit_curves_add",
                text="Add",
                text_ctxt=i18n_contexts.operator_default,
            )
        elif mode_string == "EDIT_SURFACE":
            layout.menu(
                "VIEW3D_MT_surface_add",
                text="Add",
                text_ctxt=i18n_contexts.operator_default,
            )
        elif mode_string == "EDIT_METABALL":
            layout.menu(
                "VIEW3D_MT_metaball_add",
                text="Add",
                text_ctxt=i18n_contexts.operator_default,
            )
        elif mode_string == "EDIT_ARMATURE":
            layout.menu(
                "TOPBAR_MT_edit_armature_add",
                text="Add",
                text_ctxt=i18n_contexts.operator_default,
            )

        if edit_object:
            layout.menu("VIEW3D_MT_edit_" + edit_object.type.lower())

            if mode_string == "EDIT_MESH":
                layout.menu("VIEW3D_MT_edit_mesh_vertices")
                layout.menu("VIEW3D_MT_edit_mesh_edges")
                layout.menu("VIEW3D_MT_edit_mesh_faces")
                layout.menu("VIEW3D_MT_uv_map", text="UV")
                layout.template_node_operator_asset_root_items()
            elif mode_string in {"EDIT_CURVE", "EDIT_SURFACE"}:
                layout.menu("VIEW3D_MT_edit_curve_ctrlpoints")
                layout.menu("VIEW3D_MT_edit_curve_segments")
            elif mode_string == "EDIT_POINT_CLOUD":
                layout.template_node_operator_asset_root_items()
            elif mode_string == "EDIT_CURVES":
                layout.menu("VIEW3D_MT_edit_curves_control_points")
                layout.menu("VIEW3D_MT_edit_curves_segments")
                layout.template_node_operator_asset_root_items()
            elif mode_string == "EDIT_GREASE_PENCIL":
                layout.menu("VIEW3D_MT_edit_greasepencil_point")
                layout.menu("VIEW3D_MT_edit_greasepencil_stroke")

        elif obj:
            if mode_string not in {
                "PAINT_TEXTURE",
                "SCULPT_CURVES",
                "SCULPT_GREASE_PENCIL",
                "VERTEX_GREASE_PENCIL",
            }:
                layout.menu("VIEW3D_MT_" + mode_string.lower())
            if mode_string in {"SCULPT", "PAINT_VERTEX", "PAINT_TEXTURE"}:  # BFA
                layout.menu("VIEW3D_MT_brush")  # BFA
            if mode_string == "SCULPT":
                layout.menu("VIEW3D_MT_mask")
                layout.menu("VIEW3D_MT_face_sets")
                layout.template_node_operator_asset_root_items()
            elif mode_string == "SCULPT_CURVES":
                layout.menu("VIEW3D_MT_select_sculpt_curves")
                layout.menu("VIEW3D_MT_sculpt_curves")
                layout.template_node_operator_asset_root_items()
            elif mode_string == "VERTEX_GREASE_PENCIL":
                layout.menu("VIEW3D_MT_select_edit_grease_pencil")
                layout.menu("VIEW3D_MT_paint_vertex_grease_pencil")
                layout.template_node_operator_asset_root_items()
            elif mode_string == "SCULPT_GREASE_PENCIL":
                is_selection_mask = (
                    tool_settings.use_gpencil_select_mask_point
                    or tool_settings.use_gpencil_select_mask_stroke
                    or tool_settings.use_gpencil_select_mask_segment
                )
                if is_selection_mask:
                    layout.menu("VIEW3D_MT_select_edit_grease_pencil")
            else:
                layout.template_node_operator_asset_root_items()

        else:
            layout.menu("VIEW3D_MT_object")
            layout.template_node_operator_asset_root_items()


# ********** Menu **********


# ********** Utilities **********


class ShowHideMenu:
    bl_label = "Show/Hide"
    _operator_name = ""

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "{:s}.reveal".format(self._operator_name),
            text="Show Hidden",
            icon="HIDE_OFF",
        )
        layout.operator(
            "{:s}.hide".format(self._operator_name),
            text="Hide Selected",
            icon="HIDE_ON",
        ).unselected = False
        layout.operator(
            "{:s}.hide".format(self._operator_name),
            text="Hide Unselected",
            icon="HIDE_UNSELECTED",
        ).unselected = True


# Standard transforms which apply to all cases (mix-in class, not used directly).
class VIEW3D_MT_transform_base:
    bl_label = "Transform"
    bl_category = "View"

    # TODO: get rid of the custom text strings?
    def draw(self, context):
        layout = self.layout
        # BFA - removed translate, rotate and resize as redundant
        layout.operator("transform.tosphere", text="To Sphere", icon="TOSPHERE")
        layout.operator("transform.shear", text="Shear", icon="SHEAR")
        layout.operator("transform.bend", text="Bend", icon="BEND")
        layout.operator("transform.push_pull", text="Push/Pull", icon="PUSH_PULL")

        if context.mode in {
            'EDIT_MESH',
            'EDIT_ARMATURE',
            'EDIT_SURFACE',
            'EDIT_CURVE',
            'EDIT_CURVES',
            'EDIT_LATTICE',
            'EDIT_METABALL',
        }:
            layout.operator("transform.vertex_warp", text="Warp", icon="MOD_WARP")
            layout.operator_context = "EXEC_REGION_WIN"
            layout.operator(
                "transform.vertex_random", text="Randomize", icon="RANDOMIZE"
            ).offset = 0.1
            layout.operator_context = "INVOKE_REGION_WIN"


# Generic transform menu - geometry types
class VIEW3D_MT_transform(VIEW3D_MT_transform_base, Menu):
    def draw(self, context):
        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # generic...
        layout = self.layout
        if context.mode == "EDIT_MESH":
            layout.operator(
                "transform.shrink_fatten", text="Shrink/Fatten", icon="SHRINK_FATTEN"
            )
            layout.operator("transform.skin_resize", icon="MOD_SKIN")
        elif context.mode in {"EDIT_CURVE", "EDIT_GREASE_PENCIL", "EDIT_CURVES"}:
            layout.operator(
                "transform.transform", text="Radius", icon="SHRINK_FATTEN"
            ).mode = "CURVE_SHRINKFATTEN"

        if context.mode != "EDIT_CURVES" and context.mode != "EDIT_GREASE_PENCIL":
            layout.separator()
            props = layout.operator(
                "transform.translate",
                text="Move Texture Space",
                icon="MOVE_TEXTURESPACE",
            )
            props.texture_space = True
            props = layout.operator(
                "transform.resize",
                text="Scale Texture Space",
                icon="SCALE_TEXTURESPACE",
            )
            props.texture_space = True


# Object-specific extensions to Transform menu
class VIEW3D_MT_transform_object(VIEW3D_MT_transform_base, Menu):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # object-specific option follow...
        layout.separator()

        layout.operator(
            "transform.translate", text="Move Texture Space", icon="MOVE_TEXTURESPACE"
        ).texture_space = True
        layout.operator(
            "transform.resize", text="Scale Texture Space", icon="SCALE_TEXTURESPACE"
        ).texture_space = True

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"
        # XXX: see `alignmenu()` in `edit.c` of b2.4x to get this working.
        layout.operator(
            "transform.transform",
            text="Align to Transform Orientation",
            icon="ALIGN_TRANSFORM",
        ).mode = "ALIGN"

        layout.separator()

        layout.operator("object.randomize_transform", icon="RANDOMIZE_TRANSFORM")
        layout.operator("object.align", icon="ALIGN")

        # TODO: there is a strange context bug here.
        """
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.transform_axis_target")
        """


# Armature EditMode extensions to Transform menu
class VIEW3D_MT_transform_armature(VIEW3D_MT_transform_base, Menu):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # armature specific extensions follow...
        obj = context.object
        if obj.type == "ARMATURE" and obj.mode in {"EDIT", "POSE"}:
            if obj.data.display_type == "BBONE":
                layout.separator()

                layout.operator(
                    "transform.transform", text="Scale BBone", icon="TRANSFORM_SCALE"
                ).mode = "BONE_SIZE"
            elif obj.data.display_type == "ENVELOPE":
                layout.separator()

                layout.operator(
                    "transform.transform",
                    text="Scale Envelope Distance",
                    icon="TRANSFORM_SCALE",
                ).mode = "BONE_SIZE"
                layout.operator(
                    "transform.transform", text="Scale Radius", icon="TRANSFORM_SCALE"
                ).mode = "BONE_ENVELOPE"

        if context.edit_object and context.edit_object.type == "ARMATURE":
            layout.separator()

            layout.operator("armature.align", icon="ALIGN")


class VIEW3D_MT_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "transform.mirror", text="Interactive Mirror", icon="TRANSFORM_MIRROR"
        )

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"

        for space_name, space_id in (("Global", "GLOBAL"), ("Local", "LOCAL")):
            for axis_index, axis_name in enumerate("XYZ"):
                props = layout.operator(
                    "transform.mirror",
                    text="{:s} {:s}".format(axis_name, iface_(space_name)),
                    translate=False,
                    icon="MIRROR_" + axis_name,
                )  # BFA: set icon
                props.constraint_axis[axis_index] = True
                props.orient_type = space_id

            if space_id == "GLOBAL":
                layout.separator()

        if _context.edit_object and _context.edit_object.type in {"MESH", "SURFACE"}:
            layout.separator()
            layout.operator("object.vertex_group_mirror", icon="MIRROR_VERTEXGROUP")


class VIEW3D_MT_snap(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "view3d.snap_selected_to_cursor",
            text="Selection to Cursor",
            icon="SELECTIONTOCURSOR",
        ).use_offset = False
        layout.operator(
            "view3d.snap_selected_to_cursor",
            text="Selection to Cursor (Keep Offset)",
            icon="SELECTIONTOCURSOROFFSET",
        ).use_offset = True
        layout.operator(
            "view3d.snap_selected_to_active",
            text="Selection to Active",
            icon="SELECTIONTOACTIVE",
        )
        layout.operator(
            "view3d.snap_selected_to_grid",
            text="Selection to Grid",
            icon="SELECTIONTOGRID",
        )

        layout.separator()

        layout.operator(
            "view3d.snap_cursor_to_selected",
            text="Cursor to Selected",
            icon="CURSORTOSELECTION",
        )
        layout.operator(
            "view3d.snap_cursor_to_center",
            text="Cursor to World Origin",
            icon="CURSORTOCENTER",
        )
        layout.operator(
            "view3d.snap_cursor_to_active",
            text="Cursor to Active",
            icon="CURSORTOACTIVE",
        )
        layout.operator(
            "view3d.snap_cursor_to_grid", text="Cursor to Grid", icon="CURSORTOGRID"
        )


# bfa - Tooltip and operator for Clear Seam.
class VIEW3D_MT_uv_map_clear_seam(bpy.types.Operator):
    """Clears the UV Seam for selected edges"""  # BFA - blender will use this as a tooltip for menu items and buttons.

    bl_idname = (
        "mesh.clear_seam"  # unique identifier for buttons and menu items to reference.
    )
    bl_label = "Clear seam"  # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}  # enable undo for the operator.

    def execute(
        self, context
    ):  # execute() is called by blender when running the operator.
        bpy.ops.mesh.mark_seam(clear=True)
        return {"FINISHED"}


class VIEW3D_MT_uv_map(Menu):
    bl_label = "UV Mapping"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("uv.unwrap", "method")

        layout.separator()

        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("uv.smart_project", icon="MOD_UVPROJECT")
        layout.operator("uv.lightmap_pack", icon="LIGHTMAPPACK")
        layout.operator("uv.follow_active_quads", icon="FOLLOWQUADS")

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("uv.cube_project", icon="CUBEPROJECT")
        layout.operator("uv.cylinder_project", icon="CYLINDERPROJECT")
        layout.operator("uv.sphere_project", icon="SPHEREPROJECT")

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator(
            "uv.project_from_view", icon="PROJECTFROMVIEW"
        ).scale_to_bounds = False
        layout.operator(
            "uv.project_from_view",
            text="Project from View (Bounds)",
            icon="PROJECTFROMVIEW_BOUNDS",
        ).scale_to_bounds = True

        layout.separator()

        layout.operator("mesh.mark_seam", icon="MARK_SEAM").clear = False
        layout.operator(
            "mesh.mark_seam", text="Clear Seam", icon="CLEAR_SEAM"
        ).clear = True

        layout.separator()

        layout.operator("uv.reset", icon="RESET")

        layout.template_node_operator_asset_menu_items(catalog_path="UV")


# ********** View menus **********


# bfa - set active camera does not exist in blender
class VIEW3D_MT_switchactivecamto(bpy.types.Operator):
    """Sets the current selected camera as the active camera to render from\nYou need to have a camera object selected"""

    bl_idname = "view3d.switchactivecamto"
    bl_label = "Set active Camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context = bpy.context
        scene = context.scene
        if context.active_object is not None:
            currentCameraObj = bpy.data.objects[bpy.context.active_object.name]
            scene.camera = currentCameraObj
        return {"FINISHED"}


# bfa menu
class VIEW3D_MT_view_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.cursor3d", text="Set 3D Cursor", icon="CURSOR")


# BFA - Hidden legacy operators exposed to GUI
class VIEW3D_MT_view_annotations(Menu):
    bl_label = "Annotations (Legacy)"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "gpencil.annotate",
            text="Draw Annotation",
            icon="PAINT_DRAW",
        ).mode = "DRAW"
        layout.operator(
            "gpencil.annotate", text="Draw Line Annotation", icon="PAINT_DRAW"
        ).mode = "DRAW_STRAIGHT"
        layout.operator(
            "gpencil.annotate", text="Draw Polyline Annotation", icon="PAINT_DRAW"
        ).mode = "DRAW_POLY"
        layout.operator(
            "gpencil.annotate", text="Erase Annotation", icon="ERASE"
        ).mode = "ERASER"

        layout.separator()

        layout.operator(
            "gpencil.annotation_add", text="Add Annotation Layer", icon="ADD"
        )
        layout.operator(
            "gpencil.annotation_active_frame_delete",
            text="Erase Annotation Active Keyframe",
            icon="DELETE",
        )


class VIEW3D_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        engine = context.engine

        layout.prop(view, "show_region_toolbar")
        layout.prop(view, "show_region_ui")
        layout.prop(view, "show_region_tool_header")
        layout.prop(view, "show_region_asset_shelf")
        layout.prop(view, "show_region_hud")
        layout.prop(
            overlay, "show_toolshelf_tabs", text="Tool Shelf Tabs"
        )  # bfa - the toolshelf tabs.

        layout.separator()

        layout.menu("VIEW3D_MT_view_legacy")  # bfa menu

        layout.separator()

        layout.menu("VIEW3D_MT_view_annotations")  # bfa menu

        layout.separator()

        layout.operator(
            "render.opengl", text="OpenGL Render Image", icon="RENDER_STILL"
        )
        layout.operator(
            "render.opengl", text="OpenGL Render Animation", icon="RENDER_ANIMATION"
        ).animation = True
        props = layout.operator(
            "render.opengl", text="Viewport Render Keyframes", icon="RENDER_ANIMATION"
        )
        props.animation = True
        props.render_keyed_only = True

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator(
            "view3d.clip_border", text="Clipping Border", icon="CLIPPINGBORDER"
        )

        if engine == "CYCLES":
            layout.operator("view3d.render_border", icon="RENDERBORDER")
            layout.operator("view3d.clear_render_border", icon="RENDERBORDER_CLEAR")

        layout.separator()

        layout.menu("VIEW3D_MT_view_cameras", text="Cameras")

        layout.separator()

        layout.menu("VIEW3D_MT_view_align")
        layout.menu("VIEW3D_MT_view_align_selected")

        layout.separator()

        layout.operator(
            "view3d.localview", text="Toggle Local View", icon="VIEW_GLOBAL_LOCAL"
        )
        layout.operator("view3d.localview_remove_from", icon="VIEW_REMOVE_LOCAL")

        layout.separator()

        if context.mode in ["PAINT_TEXTURE", "PAINT_VERTEX", "PAINT_WEIGHT", "SCULPT"]:
            layout.operator(
                "view3d.view_selected", text="Frame Last Stroke", icon="VIEW_SELECTED"
            ).use_all_regions = False
        else:
            layout.operator(
                "view3d.view_selected", text="Frame Selected", icon="VIEW_SELECTED"
            ).use_all_regions = False

        if view.region_quadviews:
            layout.operator(
                "view3d.view_selected",
                text="Frame Selected (Quad View)",
                icon="ALIGNCAMERA_ACTIVE",
            ).use_all_regions = True
        layout.operator(
            "view3d.view_all", text="Frame All", icon="VIEWALL"
        ).center = False
        if view.region_quadviews:
            layout.operator(
                "view3d.view_all", text="Frame All (Quad View)", icon="VIEWALL"
            ).use_all_regions = True
        layout.operator(
            "view3d.view_all",
            text="Center Cursor and Frame All",
            icon="VIEWALL_RESETCURSOR",
        ).center = True

        layout.separator()

        layout.operator("screen.region_quadview", icon="QUADVIEW")

        layout.separator()

        layout.menu("INFO_MT_area")
        layout.menu("VIEW3D_MT_view_pie_menus")  # bfa menu


class VIEW3D_MT_view_local(Menu):
    bl_label = "Local View"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "view3d.localview", text="Toggle Local View", icon="VIEW_GLOBAL_LOCAL"
        )
        layout.operator("view3d.localview_remove_from", icon="VIEW_REMOVE_LOCAL")


# bfa menu
class VIEW3D_MT_view_pie_menus(Menu):
    bl_label = "Pie menus"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "wm.call_menu_pie", text="Object Mode", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_object_mode_pie"
        layout.operator(
            "wm.call_menu_pie", text="View", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_view_pie"
        layout.operator(
            "wm.call_menu_pie", text="Transform", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_transform_gizmo_pie"
        layout.operator(
            "wm.call_menu_pie", text="Shading", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_shading_pie"
        layout.operator(
            "wm.call_menu_pie", text="Pivot", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_pivot_pie"
        layout.operator(
            "wm.call_menu_pie", text="Snap", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_snap_pie"
        layout.operator(
            "wm.call_menu_pie", text="Orientations", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_orientations_pie"
        layout.operator(
            "wm.call_menu_pie", text="Proportional Editing Falloff", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_proportional_editing_falloff_pie"
        layout.operator(
            "wm.call_menu_pie", text="Sculpt Mask Edit", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_sculpt_mask_edit_pie"
        layout.operator(
            "wm.call_menu_pie", text="Sculpt Faces Sets Edit", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_sculpt_face_sets_edit_pie"
        layout.operator(
            "wm.call_menu_pie", text="Automasking", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_sculpt_automasking_pie"
        layout.operator(
            "wm.call_menu_pie", text="Weightpaint Vertexgroup Lock", icon="MENU_PANEL"
        ).name = "VIEW3D_MT_wpaint_vgroup_lock_pie"
        layout.operator(
            "wm.call_menu_pie", text="Keyframe Insert", icon="MENU_PANEL"
        ).name = "ANIM_MT_keyframe_insert_pie"
        layout.separator()

        layout.operator(
            "wm.call_menu_pie", text="Greasepencil Snap", icon="MENU_PANEL"
        ).name = "GPENCIL_MT_snap_pie"

        layout.separator()

        layout.operator(
            "wm.toolbar_fallback_pie", text="Fallback Tool", icon="MENU_PANEL"
        )  # BFA
        layout.operator(
            "view3d.object_mode_pie_or_toggle", text="Modes", icon="MENU_PANEL"
        )  # BFA


class VIEW3D_MT_view_cameras(Menu):
    bl_label = "Cameras"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.object_as_camera", icon="VIEW_SWITCHACTIVECAM")
        layout.operator(
            "view3d.switchactivecamto",
            text="Set Active Camera",
            icon="VIEW_SWITCHACTIVECAM",
        )
        layout.operator(
            "view3d.view_camera", text="Active Camera", icon="VIEW_SWITCHTOCAM"
        )
        layout.operator("view3d.view_center_camera", icon="VIEWCAMERACENTER")


class VIEW3D_MT_view_viewpoint(Menu):
    bl_label = "Viewpoint"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "view3d.view_camera",
            text="Camera",
            icon="CAMERA_DATA",
            text_ctxt=i18n_contexts.editor_view3d,
        )  # BFA - Icon

        layout.separator()

        layout.operator(
            "view3d.view_axis",
            text="Top",
            icon="VIEW_TOP",
            text_ctxt=i18n_contexts.editor_view3d,
        ).type = "TOP"  # BFA - Icon
        layout.operator(
            "view3d.view_axis",
            text="Bottom",
            icon="VIEW_BOTTOM",
            text_ctxt=i18n_contexts.editor_view3d,
        ).type = "BOTTOM"  # BFA - Icon

        layout.separator()

        layout.operator(
            "view3d.view_axis",
            text="Front",
            icon="VIEW_FRONT",
            text_ctxt=i18n_contexts.editor_view3d,
        ).type = "FRONT"  # BFA - Icon
        layout.operator(
            "view3d.view_axis",
            text="Back",
            icon="VIEW_BACK",
            text_ctxt=i18n_contexts.editor_view3d,
        ).type = "BACK"  # BFA - Icon

        layout.separator()

        layout.operator(
            "view3d.view_axis",
            text="Right",
            icon="VIEW_RIGHT",
            text_ctxt=i18n_contexts.editor_view3d,
        ).type = "RIGHT"  # BFA - Icon
        layout.operator(
            "view3d.view_axis",
            text="Left",
            icon="VIEW_LEFT",
            text_ctxt=i18n_contexts.editor_view3d,
        ).type = "LEFT"  # BFA - Icon


# bfa menu
class VIEW3D_MT_view_navigation_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "EXEC_REGION_WIN"

        layout.operator("transform.translate", text="Move", icon="TRANSFORM_MOVE")
        layout.operator("transform.rotate", text="Rotate", icon="TRANSFORM_ROTATE")
        layout.operator("transform.resize", text="Scale", icon="TRANSFORM_SCALE")


class VIEW3D_MT_view_navigation(Menu):
    bl_label = "Navigation"

    def draw(self, _context):
        from math import pi

        layout = self.layout

        layout.menu("VIEW3D_MT_view_navigation_legacy")  # bfa menu

        layout.operator(
            "view3d.view_orbit", text="Orbit Down", icon="ORBIT_DOWN"
        ).type = "ORBITDOWN"
        layout.operator(
            "view3d.view_orbit", text="Orbit Up", icon="ORBIT_UP"
        ).type = "ORBITUP"
        layout.operator(
            "view3d.view_orbit", text="Orbit Right", icon="ORBIT_RIGHT"
        ).type = "ORBITRIGHT"
        layout.operator(
            "view3d.view_orbit", text="Orbit Left", icon="ORBIT_LEFT"
        ).type = "ORBITLEFT"
        props = layout.operator(
            "view3d.view_orbit", text="Orbit Opposite", icon="ORBIT_OPPOSITE"
        )
        props.type = "ORBITRIGHT"
        props.angle = pi

        layout.separator()

        layout.operator(
            "view3d.view_roll", text="Roll Left", icon="ROLL_LEFT"
        ).angle = pi / -12.0
        layout.operator(
            "view3d.view_roll", text="Roll Right", icon="ROLL_RIGHT"
        ).angle = pi / 12.0

        layout.separator()

        layout.operator(
            "view3d.view_pan", text="Pan Down", icon="PAN_DOWN"
        ).type = "PANDOWN"
        layout.operator("view3d.view_pan", text="Pan Up", icon="PAN_UP").type = "PANUP"
        layout.operator(
            "view3d.view_pan", text="Pan Right", icon="PAN_RIGHT"
        ).type = "PANRIGHT"
        layout.operator(
            "view3d.view_pan", text="Pan Left", icon="PAN_LEFT"
        ).type = "PANLEFT"

        layout.separator()

        layout.operator("view3d.zoom_border", text="Zoom Border", icon="ZOOM_BORDER")
        layout.operator("view3d.zoom", text="Zoom In", icon="ZOOM_IN").delta = 1
        layout.operator("view3d.zoom", text="Zoom Out", icon="ZOOM_OUT").delta = -1
        layout.operator(
            "view3d.zoom_camera_1_to_1", text="Zoom Camera 1:1", icon="ZOOM_CAMERA"
        )
        layout.operator("view3d.dolly", text="Dolly View", icon="DOLLY")
        layout.operator("view3d.view_center_pick", icon="CENTERTOMOUSE")

        layout.separator()

        layout.operator("view3d.fly", icon="FLY_NAVIGATION")
        layout.operator("view3d.walk", icon="WALK_NAVIGATION")
        layout.operator("view3d.navigate", icon="VIEW_NAVIGATION")

        layout.separator()

        layout.operator(
            "screen.animation_play", text="Playback Animation", icon="TRIA_RIGHT"
        )


class VIEW3D_MT_view_align(Menu):
    bl_label = "Align View"

    def draw(self, _context):
        layout = self.layout
        i18n_text_ctxt = bpy.app.translations.contexts_C_to_py[
            "BLT_I18NCONTEXT_EDITOR_VIEW3D"
        ]  # bfa - needed by us

        layout.operator(
            "view3d.camera_to_view",
            text="Align Active Camera to View",
            icon="ALIGNCAMERA_VIEW",
        )
        layout.operator(
            "view3d.camera_to_view_selected",
            text="Align Active Camera to Selected",
            icon="ALIGNCAMERA_ACTIVE",
        )
        layout.operator("view3d.view_center_cursor", icon="CENTERTOCURSOR")

        layout.separator()

        layout.operator("view3d.view_lock_to_active", icon="LOCKTOACTIVE")
        layout.operator("view3d.view_center_lock", icon="LOCKTOCENTER")
        layout.operator("view3d.view_lock_clear", icon="LOCK_CLEAR")

        layout.separator()

        layout.operator(
            "view3d.view_persportho",
            text="Perspective/Orthographic",
            icon="PERSP_ORTHO",
        )

        layout.separator()

        layout.operator(
            "view3d.view_axis", text="Top", icon="VIEW_TOP", text_ctxt=i18n_text_ctxt
        ).type = "TOP"
        layout.operator(
            "view3d.view_axis",
            text="Bottom",
            icon="VIEW_BOTTOM",
            text_ctxt=i18n_text_ctxt,
        ).type = "BOTTOM"
        layout.operator(
            "view3d.view_axis",
            text="Front",
            icon="VIEW_FRONT",
            text_ctxt=i18n_text_ctxt,
        ).type = "FRONT"
        layout.operator(
            "view3d.view_axis", text="Back", icon="VIEW_BACK", text_ctxt=i18n_text_ctxt
        ).type = "BACK"
        layout.operator(
            "view3d.view_axis",
            text="Right",
            icon="VIEW_RIGHT",
            text_ctxt=i18n_text_ctxt,
        ).type = "RIGHT"
        layout.operator(
            "view3d.view_axis", text="Left", icon="VIEW_LEFT", text_ctxt=i18n_text_ctxt
        ).type = "LEFT"


class VIEW3D_MT_view_align_selected(Menu):
    bl_label = "Align View to Active"

    def draw(self, _context):
        layout = self.layout
        i18n_text_ctxt = bpy.app.translations.contexts_C_to_py[
            "BLT_I18NCONTEXT_EDITOR_VIEW3D"
        ]
        props = layout.operator(
            "view3d.view_axis",
            text="Top",
            icon="VIEW_ACTIVE_TOP",
            text_ctxt=i18n_text_ctxt,
        )
        props.align_active = True
        props.type = "TOP"

        props = layout.operator(
            "view3d.view_axis",
            text="Bottom",
            icon="VIEW_ACTIVE_BOTTOM",
            text_ctxt=i18n_text_ctxt,
        )
        props.align_active = True
        props.type = "BOTTOM"

        props = layout.operator(
            "view3d.view_axis",
            text="Front",
            icon="VIEW_ACTIVE_FRONT",
            text_ctxt=i18n_text_ctxt,
        )
        props.align_active = True
        props.type = "FRONT"

        props = layout.operator(
            "view3d.view_axis",
            text="Back",
            icon="VIEW_ACTIVE_BACK",
            text_ctxt=i18n_text_ctxt,
        )
        props.align_active = True
        props.type = "BACK"

        props = layout.operator(
            "view3d.view_axis",
            text="Right",
            icon="VIEW_ACTIVE_RIGHT",
            text_ctxt=i18n_text_ctxt,
        )
        props.align_active = True
        props.type = "RIGHT"

        props = layout.operator(
            "view3d.view_axis",
            text="Left",
            icon="VIEW_ACTIVE_LEFT",
            text_ctxt=i18n_text_ctxt,
        )
        props.align_active = True
        props.type = "LEFT"


class VIEW3D_MT_view_regions(Menu):
    bl_label = "View Regions"

    def draw(self, _context):
        layout = self.layout
        layout.operator("view3d.clip_border", text="Clipping Region...")
        layout.operator("view3d.render_border", text="Render Region...")

        layout.separator()

        layout.operator("view3d.clear_render_border")


# ********** Select menus, suffix from context.mode **********


class VIEW3D_MT_select_object_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.select_more", text="More", icon="SELECTMORE")
        layout.operator("object.select_less", text="Less", icon="SELECTLESS")

        layout.separator()

        props = layout.operator(
            "object.select_hierarchy",
            text_ctxt=i18n_contexts.default,
            text="Parent",
            icon="PARENT",
        )
        props.extend = False
        props.direction = "PARENT"

        props = layout.operator("object.select_hierarchy", text="Child", icon="CHILD")
        props.extend = False
        props.direction = "CHILD"

        layout.separator()

        props = layout.operator(
            "object.select_hierarchy", text="Extend Parent", icon="PARENT"
        )
        props.extend = True
        props.direction = "PARENT"

        props = layout.operator(
            "object.select_hierarchy", text="Extend Child", icon="CHILD"
        )
        props.extend = True
        props.direction = "CHILD"


class VIEW3D_MT_select_object(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "object.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "object.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "object.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.menu("VIEW3D_MT_select_grouped")  # bfa menu
        layout.menu("VIEW3D_MT_select_linked")  # bfa menu
        layout.menu("VIEW3D_MT_select_by_type")  # bfa menu

        layout.separator()
        layout.operator("object.select_random", text="Random", icon="RANDOMIZE")
        layout.operator(
            "object.select_mirror", text="Mirror Selection", icon="TRANSFORM_MIRROR"
        )

        layout.operator("object.select_pattern", text="By Pattern", icon="PATTERN")
        layout.operator(
            "object.select_camera", text="Active Camera", icon="CAMERA_DATA"
        )

        layout.separator()

        layout.menu("VIEW3D_MT_select_object_more_less", text="Select More/Less")


# BFA menu


class VIEW3D_MT_select_object_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.select_box", icon="BOX_MASK")
        layout.operator("view3d.select_circle", icon="CIRCLE_SELECT")


# BFA menu
class VIEW3D_MT_select_by_type(Menu):
    bl_label = "All by Type"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.select_by_type", text="Mesh", icon="OUTLINER_OB_MESH"
        ).type = "MESH"
        layout.operator(
            "object.select_by_type", text="Curve", icon="OUTLINER_OB_CURVE"
        ).type = "CURVE"
        layout.operator(
            "object.select_by_type", text="Surface", icon="OUTLINER_OB_SURFACE"
        ).type = "SURFACE"
        layout.operator(
            "object.select_by_type", text="Meta", icon="OUTLINER_OB_META"
        ).type = "META"
        layout.operator(
            "object.select_by_type", text="Font", icon="OUTLINER_OB_FONT"
        ).type = "FONT"

        layout.separator()

        layout.operator(
            "object.select_by_type", text="Armature", icon="OUTLINER_OB_ARMATURE"
        ).type = "ARMATURE"
        layout.operator(
            "object.select_by_type", text="Lattice", icon="OUTLINER_OB_LATTICE"
        ).type = "LATTICE"
        layout.operator(
            "object.select_by_type", text="Empty", icon="OUTLINER_OB_EMPTY"
        ).type = "EMPTY"
        layout.operator(
            "object.select_by_type", text="GPencil", icon="GREASEPENCIL"
        ).type = "GREASEPENCIL"

        layout.separator()

        layout.operator(
            "object.select_by_type", text="Camera", icon="OUTLINER_OB_CAMERA"
        ).type = "CAMERA"
        layout.operator(
            "object.select_by_type", text="Light", icon="OUTLINER_OB_LIGHT"
        ).type = "LIGHT"
        layout.operator(
            "object.select_by_type", text="Speaker", icon="OUTLINER_OB_SPEAKER"
        ).type = "SPEAKER"
        layout.operator(
            "object.select_by_type", text="Probe", icon="OUTLINER_OB_LIGHTPROBE"
        ).type = "LIGHT_PROBE"


# BFA menu
class VIEW3D_MT_select_grouped(Menu):
    bl_label = "Grouped"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.select_grouped", text="Siblings", icon="SIBLINGS"
        ).type = "SIBLINGS"
        layout.operator(
            "object.select_grouped", text="Parent", icon="PARENT"
        ).type = "PARENT"
        layout.operator(
            "object.select_grouped", text="Children", icon="CHILD_RECURSIVE"
        ).type = "CHILDREN_RECURSIVE"
        layout.operator(
            "object.select_grouped", text="Immediate Children", icon="CHILD"
        ).type = "CHILDREN"

        layout.separator()

        layout.operator("object.select_grouped", text="Type", icon="TYPE").type = "TYPE"
        layout.operator(
            "object.select_grouped", text="Collection", icon="GROUP"
        ).type = "COLLECTION"
        layout.operator("object.select_grouped", text="Hook", icon="HOOK").type = "HOOK"

        layout.separator()

        layout.operator("object.select_grouped", text="Pass", icon="PASS").type = "PASS"
        layout.operator(
            "object.select_grouped", text="Color", icon="COLOR"
        ).type = "COLOR"
        layout.operator(
            "object.select_grouped", text="Keying Set", icon="KEYINGSET"
        ).type = "KEYINGSET"
        layout.operator(
            "object.select_grouped", text="Light Type", icon="LIGHT"
        ).type = "LIGHT_TYPE"


# bfa menu
class VIEW3D_MT_select_linked(Menu):
    bl_label = "Linked"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.select_linked", text="Object Data", icon="OBJECT_DATA"
        ).type = "OBDATA"
        layout.operator(
            "object.select_linked", text="Material", icon="MATERIAL_DATA"
        ).type = "MATERIAL"
        layout.operator(
            "object.select_linked", text="Instanced Collection", icon="GROUP"
        ).type = "DUPGROUP"
        layout.operator(
            "object.select_linked", text="Particle System", icon="PARTICLES"
        ).type = "PARTICLE"
        layout.operator(
            "object.select_linked", text="Library", icon="LIBRARY"
        ).type = "LIBRARY"
        layout.operator(
            "object.select_linked", text="Library (Object Data)", icon="LIBRARY_OBJECT"
        ).type = "LIBRARY_OBDATA"


# BFA - not used


class VIEW3D_MT_select_pose_more_less(Menu):
    bl_label = "Select More/Less"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "pose.select_hierarchy",
            text="Parent",
            text_ctxt=i18n_contexts.default,
            icon="PARENT",
        )
        props.extend = False
        props.direction = "PARENT"

        props = layout.operator("pose.select_hierarchy", text="Child", icon="CHILD")
        props.extend = False
        props.direction = "CHILD"

        layout.separator()

        props = layout.operator(
            "pose.select_hierarchy", text="Extend Parent", icon="PARENT"
        )
        props.extend = True
        props.direction = "PARENT"

        props = layout.operator(
            "pose.select_hierarchy", text="Extend Child", icon="CHILD"
        )
        props.extend = True
        props.direction = "CHILD"


class VIEW3D_MT_select_pose(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "pose.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "pose.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "pose.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator_menu_enum("pose.select_grouped", "type", text="Grouped")
        layout.operator("pose.select_linked", text="Linked", icon="LINKED")

        layout.menu("POSE_MT_selection_sets_select", text="Bone Selection Set")

        layout.operator(
            "pose.select_constraint_target",
            text="Constraint Target",
            icon="CONSTRAINT_BONE",
        )

        layout.separator()

        layout.operator("object.select_pattern", text="By Pattern", icon="PATTERN")

        layout.separator()

        layout.operator("pose.select_mirror", text="Flip Active", icon="FLIP")

        layout.separator()

        props = layout.operator("pose.select_hierarchy", text="Parent", icon="PARENT")
        props.extend = False
        props.direction = "PARENT"

        props = layout.operator("pose.select_hierarchy", text="Child", icon="CHILD")
        props.extend = False
        props.direction = "CHILD"

        layout.separator()

        props = layout.operator(
            "pose.select_hierarchy", text="Extend Parent", icon="PARENT"
        )
        props.extend = True
        props.direction = "PARENT"

        props = layout.operator(
            "pose.select_hierarchy", text="Extend Child", icon="CHILD"
        )
        props.extend = True
        props.direction = "CHILD"


class VIEW3D_MT_select_particle(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "particle.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "particle.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "particle.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("particle.select_more", text="More", icon="SELECTMORE")
        layout.operator("particle.select_less", text="Less", icon="SELECTLESS")

        layout.separator()

        layout.operator("particle.select_linked", text="Linked", icon="LINKED")

        layout.separator()

        layout.operator("particle.select_random", text="Random", icon="RANDOMIZE")

        layout.separator()

        layout.operator("particle.select_roots", text="Roots", icon="SELECT_ROOT")
        layout.operator("particle.select_tips", text="Tips", icon="SELECT_TIP")


class VIEW3D_MT_edit_mesh_select_similar(Menu):
    bl_label = "Select Similar"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("mesh.select_similar", "type")

        layout.separator()

        layout.operator(
            "mesh.select_similar_region", text="Face Regions", icon="FACEREGIONS"
        )


class VIEW3D_MT_edit_mesh_select_by_trait(Menu):
    bl_label = "Select All by Trait"

    def draw(self, context):
        layout = self.layout
        _is_vert_mode, _is_edge_mode, is_face_mode = (
            context.tool_settings.mesh_select_mode
        )

        if is_face_mode is False:
            layout.operator(
                "mesh.select_non_manifold",
                text="Non Manifold",
                icon="SELECT_NONMANIFOLD",
            )
        layout.operator("mesh.select_loose", text="Loose Geometry", icon="SELECT_LOOSE")
        layout.operator(
            "mesh.select_interior_faces", text="Interior Faces", icon="SELECT_INTERIOR"
        )
        layout.operator(
            "mesh.select_face_by_sides",
            text="Faces by Sides",
            icon="SELECT_FACES_BY_SIDE",
        )
        layout.operator("mesh.select_by_pole_count", text="Poles by Count", icon="POLE")

        layout.separator()

        layout.operator(
            "mesh.select_ungrouped",
            text="Ungrouped Vertices",
            icon="SELECT_UNGROUPED_VERTS",
        )


class VIEW3D_MT_edit_mesh_select_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.select_more", text="More", icon="SELECTMORE")
        layout.operator("mesh.select_less", text="Less", icon="SELECTLESS")

        layout.separator()

        layout.operator("mesh.select_next_item", text="Next Active", icon="NEXTACTIVE")
        layout.operator(
            "mesh.select_prev_item", text="Previous Active", icon="PREVIOUSACTIVE"
        )


class VIEW3D_MT_edit_mesh_select_linked(Menu):
    bl_label = "Select Linked"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.select_linked", text="Linked")
        layout.operator("mesh.shortest_path_select", text="Shortest Path")
        layout.operator("mesh.faces_select_linked_flat", text="Linked Flat Faces")


class VIEW3D_MT_edit_mesh_select_loops(Menu):
    bl_label = "Select Loops"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.loop_multi_select", text="Edge Loops").ring = False
        layout.operator("mesh.loop_multi_select", text="Edge Rings").ring = True

        layout.separator()

        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")


class VIEW3D_MT_select_edit_mesh(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu

        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        # primitive
        layout.operator(
            "mesh.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "mesh.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "mesh.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("mesh.select_linked", text="Linked", icon="LINKED")
        layout.operator(
            "mesh.faces_select_linked_flat", text="Linked Flat Faces", icon="LINKED"
        )
        layout.operator(
            "mesh.select_linked_pick", text="Linked Pick Select", icon="LINKED"
        ).deselect = False
        layout.operator(
            "mesh.select_linked_pick", text="Linked Pick Deselect", icon="LINKED"
        ).deselect = True

        layout.separator()

        # other
        layout.menu("VIEW3D_MT_edit_mesh_select_similar")

        # numeric
        layout.separator()
        layout.operator("mesh.select_random", text="Random", icon="RANDOMIZE")
        layout.operator("mesh.select_nth", icon="CHECKER_DESELECT")

        layout.separator()
        layout.operator(
            "mesh.select_mirror", text="Mirror Selection", icon="TRANSFORM_MIRROR"
        )
        layout.operator(
            "mesh.select_axis", text="Side of Active", icon="SELECT_SIDEOFACTIVE"
        )
        layout.operator(
            "mesh.shortest_path_select",
            text="Shortest Path",
            icon="SELECT_SHORTESTPATH",
        )

        # geometric
        layout.separator()
        layout.operator(
            "mesh.edges_select_sharp", text="Sharp Edges", icon="SELECT_SHARPEDGES"
        )

        layout.separator()

        # loops
        layout.operator(
            "mesh.loop_multi_select", text="Edge Loops", icon="SELECT_EDGELOOP"
        ).ring = False
        layout.operator(
            "mesh.loop_multi_select", text="Edge Rings", icon="SELECT_EDGERING"
        ).ring = True
        layout.operator(
            "mesh.loop_to_region", text="Loop Inner Region", icon="SELECT_LOOPINNER"
        )
        layout.operator(
            "mesh.region_to_loop", text="Boundary Loop", icon="SELECT_BOUNDARY"
        )

        layout.separator()
        layout.menu("VIEW3D_MT_edit_mesh_select_by_trait")

        # attribute
        layout.separator()
        layout.operator(
            "mesh.select_by_attribute", text="By Attribute", icon="NODE_ATTRIBUTE"
        )

        # more/less
        layout.separator()
        layout.menu("VIEW3D_MT_edit_mesh_select_more_less")

        layout.separator()

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


class VIEW3D_MT_select_edit_curve(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu

        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "curve.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "curve.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "curve.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("curve.select_linked", text="Linked", icon="LINKED")
        layout.operator(
            "curve.select_linked_pick", text="Linked Pick Select", icon="LINKED"
        ).deselect = False
        layout.operator(
            "curve.select_linked_pick", text="Linked Pick Deselect", icon="LINKED"
        ).deselect = True

        layout.separator()

        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")  # bfa menu

        layout.separator()

        layout.operator("curve.select_random", text="Random", icon="RANDOMIZE")
        layout.operator("curve.select_nth", icon="CHECKER_DESELECT")

        layout.separator()

        layout.operator("curve.de_select_first", icon="SELECT_FIRST")
        layout.operator("curve.de_select_last", icon="SELECT_LAST")
        layout.operator("curve.select_next", text="Next", icon="NEXTACTIVE")
        layout.operator("curve.select_previous", text="Previous", icon="PREVIOUSACTIVE")

        layout.separator()

        layout.operator("curve.select_more", text="More", icon="SELECTMORE")
        layout.operator("curve.select_less", text="Less", icon="SELECTLESS")


# bfa menu
class VIEW3D_MT_select_edit_curve_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.select_similar", text="Type", icon="TYPE").type = "TYPE"
        layout.operator(
            "curve.select_similar", text="Radius", icon="RADIUS"
        ).type = "RADIUS"
        layout.operator(
            "curve.select_similar", text="Weight", icon="MOD_VERTEX_WEIGHT"
        ).type = "WEIGHT"
        layout.operator(
            "curve.select_similar", text="Direction", icon="SWITCH_DIRECTION"
        ).type = "DIRECTION"


class VIEW3D_MT_select_edit_surface(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "curve.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "curve.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "curve.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("curve.select_linked", text="Linked", icon="LINKED")
        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")  # bfa menu

        layout.separator()

        layout.operator("curve.select_random", text="Random", icon="RANDOMIZE")
        layout.operator("curve.select_nth", icon="CHECKER_DESELECT")

        layout.separator()

        layout.operator(
            "curve.select_row", text="Control Point row", icon="CONTROLPOINTROW"
        )

        layout.separator()

        layout.operator("curve.select_more", text="More", icon="SELECTMORE")
        layout.operator("curve.select_less", text="Less", icon="SELECTLESS")


class VIEW3D_MT_select_edit_text(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("font.select_all", text="All", icon="SELECT_ALL")

        layout.separator()

        layout.operator(
            "font.move_select", text="Line End", icon="HAND"
        ).type = "LINE_END"
        layout.operator(
            "font.move_select", text="Line Begin", icon="HAND"
        ).type = "LINE_BEGIN"

        layout.separator()

        layout.operator("font.move_select", text="Top", icon="HAND").type = "TEXT_BEGIN"
        layout.operator(
            "font.move_select", text="Bottom", icon="HAND"
        ).type = "TEXT_END"

        layout.separator()

        layout.operator(
            "font.move_select", text="Previous Block", icon="HAND"
        ).type = "PREVIOUS_PAGE"
        layout.operator(
            "font.move_select", text="Next Block", icon="HAND"
        ).type = "NEXT_PAGE"

        layout.separator()

        layout.operator(
            "font.move_select", text="Previous Character", icon="HAND"
        ).type = "PREVIOUS_CHARACTER"
        layout.operator(
            "font.move_select", text="Next Character", icon="HAND"
        ).type = "NEXT_CHARACTER"

        layout.separator()

        layout.operator(
            "font.move_select", text="Previous Word", icon="HAND"
        ).type = "PREVIOUS_WORD"
        layout.operator(
            "font.move_select", text="Next Word", icon="HAND"
        ).type = "NEXT_WORD"

        layout.separator()

        layout.operator(
            "font.move_select", text="Previous Line", icon="HAND"
        ).type = "PREVIOUS_LINE"
        layout.operator(
            "font.move_select", text="Next Line", icon="HAND"
        ).type = "NEXT_LINE"


class VIEW3D_MT_select_edit_metaball(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "mball.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "mball.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "mball.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.menu("VIEW3D_MT_select_edit_metaball_select_similar")  # bfa menu

        layout.separator()

        layout.operator(
            "mball.select_random_metaelems", text="Random", icon="RANDOMIZE"
        )


# bfa menu
class VIEW3D_MT_select_edit_metaball_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("mball.select_similar", text="Type", icon="TYPE").type = "TYPE"
        layout.operator(
            "mball.select_similar", text="Radius", icon="RADIUS"
        ).type = "RADIUS"
        layout.operator(
            "mball.select_similar", text="Stiffness", icon="BEND"
        ).type = "STIFFNESS"
        layout.operator(
            "mball.select_similar", text="Rotation", icon="ROTATE"
        ).type = "ROTATION"


class VIEW3D_MT_edit_lattice_context_menu(Menu):
    bl_label = "Lattice"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_edit_lattice_flip")  # bfa menu - blender uses enum
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("lattice.make_regular", icon="MAKE_REGULAR")


class VIEW3D_MT_select_edit_lattice(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "lattice.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "lattice.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "lattice.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("lattice.select_mirror", text="Mirror", icon="TRANSFORM_MIRROR")
        layout.operator("lattice.select_random", text="Random", icon="RANDOMIZE")

        layout.separator()

        layout.operator(
            "lattice.select_ungrouped",
            text="Ungrouped Vertices",
            icon="SELECT_UNGROUPED_VERTS",
        )

        layout.separator()

        layout.operator("lattice.select_more", text="More", icon="SELECTMORE")
        layout.operator("lattice.select_less", text="Less", icon="SELECTLESS")


class VIEW3D_MT_select_edit_armature(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "armature.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "armature.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "armature.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator_menu_enum("armature.select_similar", "type", text="Similar")

        layout.separator()

        layout.operator(
            "armature.select_mirror", text="Mirror Selection", icon="TRANSFORM_MIRROR"
        ).extend = False
        layout.operator("object.select_pattern", text="By Pattern", icon="PATTERN")

        layout.separator()

        layout.operator("armature.select_linked", text="Linked", icon="LINKED")

        layout.separator()

        props = layout.operator(
            "armature.select_hierarchy",
            text="Parent",
            text_ctxt=i18n_contexts.default,
            icon="PARENT",
        )
        props.extend = False
        props.direction = "PARENT"

        props = layout.operator("armature.select_hierarchy", text="Child", icon="CHILD")
        props.extend = False
        props.direction = "CHILD"

        layout.separator()

        props = layout.operator(
            "armature.select_hierarchy", text="Extend Parent", icon="PARENT"
        )
        props.extend = True
        props.direction = "PARENT"

        props = layout.operator(
            "armature.select_hierarchy", text="Extend Child", icon="CHILD"
        )
        props.extend = True
        props.direction = "CHILD"

        layout.separator()

        layout.operator("armature.select_more", text="More", icon="SELECTMORE")
        layout.operator("armature.select_less", text="Less", icon="SELECTLESS")


# bfa menu
class VIEW3D_PT_greasepencil_edit_options(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings.gpencil_sculpt

        layout.prop(settings, "use_scale_thickness", text="Scale Thickness")


# BFA - legacy menu
class VIEW3D_MT_select_greasepencil_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("view3d.select_box", icon="BORDER_RECT")
        layout.operator("view3d.select_circle", icon="CIRCLE_SELECT")


class VIEW3D_MT_select_edit_grease_pencil(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_greasepencil_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "grease_pencil.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "grease_pencil.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "grease_pencil.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("grease_pencil.select_linked", text="Linked", icon="LINKED")
        layout.operator_menu_enum("grease_pencil.select_similar", "mode")

        layout.separator()

        layout.operator(
            "grease_pencil.select_alternate", text="Alternated", icon="ALTERNATED"
        )
        layout.operator("grease_pencil.select_random", text="Random", icon="RANDOMIZE")

        layout.separator()

        props = layout.operator(
            "grease_pencil.select_ends", text="First", icon="SELECT_TIP"
        )
        props.amount_start = 1
        props.amount_end = 0
        props = layout.operator(
            "grease_pencil.select_ends", text="Last", icon="SELECT_ROOT"
        )
        props.amount_start = 0
        props.amount_end = 1

        layout.separator()
        # BFA - moved below
        layout.operator("grease_pencil.select_more", text="More", icon="SELECTMORE")
        layout.operator("grease_pencil.select_less", text="Less", icon="SELECTLESS")


class VIEW3D_MT_paint_grease_pencil(Menu):
    bl_label = "Draw"

    def draw(self, _context):
        layout = self.layout

        layout.menu("GREASE_PENCIL_MT_layer_active", text="Active Layer")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_greasepencil_animation")  # BFA - menu
        layout.operator(
            "grease_pencil.interpolate_sequence",
            text="Interpolate Sequence",
            icon="SEQUENCE",
        )

        layout.separator()

        layout.menu("VIEW3D_MT_edit_greasepencil_showhide")
        layout.menu("VIEW3D_MT_edit_greasepencil_cleanup")

        layout.separator()

        layout.operator("paint.sample_color", icon="EYEDROPPER").merged = False


class VIEW3D_MT_paint_vertex_grease_pencil(Menu):
    bl_label = "Paint"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "grease_pencil.vertex_color_set",
            text="Set Color Attribute",
            icon="NODE_VERTEX_COLOR",
        )
        layout.operator("grease_pencil.stroke_reset_vertex_color", icon="RESET")
        layout.separator()
        layout.operator(
            "grease_pencil.vertex_color_invert", text="Invert", icon="NODE_INVERT"
        )
        layout.operator(
            "grease_pencil.vertex_color_levels", text="Levels", icon="LEVELS"
        )
        layout.operator(
            "grease_pencil.vertex_color_hsv",
            text="Hue/Saturation/Value",
            icon="HUESATVAL",
        )
        layout.operator(
            "grease_pencil.vertex_color_brightness_contrast",
            text="Brightness/Contrast",
            icon="BRIGHTNESS_CONTRAST",
        )


# bfa menu
class VIEW3D_MT_select_paint_mask_face_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout = self.layout

        layout.operator("paint.face_select_more", text="More", icon="SELECTMORE")
        layout.operator("paint.face_select_less", text="Less", icon="SELECTLESS")


class VIEW3D_MT_select_paint_mask_vertex(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_select_object_legacy")  # bfa menu
        layout.operator_menu_enum("view3d.select_lasso", "mode")

        layout.separator()

        layout.operator(
            "paint.vert_select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "paint.vert_select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "paint.vert_select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator(
            "paint.vert_select_ungrouped",
            text="Ungrouped Vertices",
            icon="SELECT_UNGROUPED_VERTS",
        )
        layout.operator("paint.vert_select_linked", text="Select Linked", icon="LINKED")

        layout.separator()

        layout.menu("VIEW3D_MT_select_paint_mask_vertex_more_less")  # bfa menu


# bfa menu
class VIEW3D_MT_select_paint_mask_vertex_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout = self.layout

        layout.operator("paint.vert_select_more", text="More", icon="SELECTMORE")
        layout.operator("paint.vert_select_less", text="Less", icon="SELECTLESS")


class VIEW3D_MT_select_edit_point_cloud(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("point_cloud.select_all", text="All").action = 'SELECT'
        layout.operator("point_cloud.select_all", text="None").action = 'DESELECT'
        layout.operator("point_cloud.select_all", text="Invert").action = 'INVERT'

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


# BFA - not used
class VIEW3D_MT_edit_curves_select_more_less(Menu):
    bl_label = "Select More/Less"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curves.select_more", text="More", icon="SELECTMORE")
        layout.operator("curves.select_less", text="Less", icon="SELECTLESS")


class VIEW3D_MT_select_edit_curves(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "curves.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "curves.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "curves.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("curves.select_random", text="Random", icon="RANDOMIZE")

        layout.separator()

        layout.operator("curves.select_ends", text="Endpoints", icon="SELECT_TIP")
        layout.operator("curves.select_linked", text="Linked", icon="LINKED")

        layout.separator()

        # layout.menu("VIEW3D_MT_edit_curves_select_more_less") # BFA - not used
        layout.operator("curves.select_more", text="More", icon="SELECTMORE")
        layout.operator("curves.select_less", text="Less", icon="SELECTLESS")

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


class VIEW3D_MT_select_sculpt_curves(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "curves.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "curves.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "curves.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator("sculpt_curves.select_random", text="Random", icon="RANDOMIZE")

        layout.separator()

        layout.operator("curves.select_ends", text="Endpoints", icon="SELECT_TIP")
        layout.operator("sculpt_curves.select_grow", text="Grow", icon="SELECTMORE")

        layout.template_node_operator_asset_menu_items(catalog_path="Select")


class VIEW3D_MT_mesh_add(Menu):
    bl_idname = "VIEW3D_MT_mesh_add"
    bl_label = "Mesh"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        # BFA - make sure you can see it in the header
        layout.operator(
            "WM_OT_search_single_menu", text="Search...", icon="VIEWZOOM"
        ).menu_idname = "VIEW3D_MT_mesh_add"

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator("mesh.primitive_plane_add", text="Plane", icon="MESH_PLANE")
        layout.operator("mesh.primitive_cube_add", text="Cube", icon="MESH_CUBE")
        layout.operator("mesh.primitive_circle_add", text="Circle", icon="MESH_CIRCLE")
        layout.operator(
            "mesh.primitive_uv_sphere_add", text="UV Sphere", icon="MESH_UVSPHERE"
        )
        layout.operator(
            "mesh.primitive_ico_sphere_add", text="Ico Sphere", icon="MESH_ICOSPHERE"
        )
        layout.operator(
            "mesh.primitive_cylinder_add", text="Cylinder", icon="MESH_CYLINDER"
        )
        layout.operator("mesh.primitive_cone_add", text="Cone", icon="MESH_CONE")
        layout.operator("mesh.primitive_torus_add", text="Torus", icon="MESH_TORUS")

        layout.separator()

        layout.operator("mesh.primitive_grid_add", text="Grid", icon="MESH_GRID")
        layout.operator("mesh.primitive_monkey_add", text="Monkey", icon="MESH_MONKEY")

        layout.template_node_operator_asset_menu_items(catalog_path="Add")


class VIEW3D_MT_curve_add(Menu):
    bl_idname = "VIEW3D_MT_curve_add"
    bl_label = "Curve"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator(
            "curve.primitive_bezier_curve_add", text="Bézier", icon="CURVE_BEZCURVE"
        )
        layout.operator(
            "curve.primitive_bezier_circle_add", text="Circle", icon="CURVE_BEZCIRCLE"
        )

        layout.separator()

        layout.operator(
            "curve.primitive_nurbs_curve_add", text="Nurbs Curve", icon="CURVE_NCURVE"
        )
        layout.operator(
            "curve.primitive_nurbs_circle_add",
            text="Nurbs Circle",
            icon="CURVE_NCIRCLE",
        )
        layout.operator(
            "curve.primitive_nurbs_path_add", text="Path", icon="CURVE_PATH"
        )

        layout.separator()

        layout.operator(
            "object.curves_empty_hair_add", text="Empty Hair", icon="OUTLINER_OB_CURVES"
        )
        layout.operator("object.quick_fur", text="Fur", icon="OUTLINER_OB_CURVES")

        experimental = context.preferences.experimental
        if experimental.use_new_curves_tools:
            layout.operator(
                "object.curves_random_add", text="Random", icon="OUTLINER_OB_CURVES"
            )


class VIEW3D_MT_surface_add(Menu):
    bl_idname = "VIEW3D_MT_surface_add"
    bl_label = "Surface"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator(
            "surface.primitive_nurbs_surface_curve_add",
            text="Surface Curve",
            icon="SURFACE_NCURVE",
        )
        layout.operator(
            "surface.primitive_nurbs_surface_circle_add",
            text="Surface Circle",
            icon="SURFACE_NCIRCLE",
        )
        layout.operator(
            "surface.primitive_nurbs_surface_surface_add",
            text="Surface Patch",
            icon="SURFACE_NSURFACE",
        )
        layout.operator(
            "surface.primitive_nurbs_surface_cylinder_add",
            text="Surface Cylinder",
            icon="SURFACE_NCYLINDER",
        )
        layout.operator(
            "surface.primitive_nurbs_surface_sphere_add",
            text="Surface Sphere",
            icon="SURFACE_NSPHERE",
        )
        layout.operator(
            "surface.primitive_nurbs_surface_torus_add",
            text="Surface Torus",
            icon="SURFACE_NTORUS",
        )


class VIEW3D_MT_edit_metaball_context_menu(Menu):
    bl_label = "Metaball"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        # Add
        layout.operator("mball.duplicate_move", icon="DUPLICATE")

        layout.separator()

        # Modify
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_meta_showhide")  # BFA - added to context menu

        # Remove
        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("mball.delete_metaelems", text="Delete", icon="DELETE")


class VIEW3D_MT_metaball_add(Menu):
    bl_idname = "VIEW3D_MT_metaball_add"
    bl_label = "Metaball"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator_enum("object.metaball_add", "type")


class TOPBAR_MT_edit_curve_add(Menu):
    bl_idname = "TOPBAR_MT_edit_curve_add"
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, context):
        layout = self.layout

        is_surf = context.active_object.type == "SURFACE"

        layout.operator_context = "EXEC_REGION_WIN"

        if is_surf:
            VIEW3D_MT_surface_add.draw(self, context)
        else:
            VIEW3D_MT_curve_add.draw(self, context)


class TOPBAR_MT_edit_armature_add(Menu):
    bl_idname = "TOPBAR_MT_edit_armature_add"
    bl_label = "Armature"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator(
            "armature.bone_primitive_add", text="Single Bone", icon="BONE_DATA"
        )


class VIEW3D_MT_armature_add(Menu):
    bl_idname = "VIEW3D_MT_armature_add"
    bl_label = "Armature"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("object.armature_add", text="Single Bone", icon="BONE_DATA")


class VIEW3D_MT_light_add(Menu):
    bl_idname = "VIEW3D_MT_light_add"
    bl_context = i18n_contexts.id_light
    bl_label = "Light"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator_enum("object.light_add", "type")


class VIEW3D_MT_lightprobe_add(Menu):
    bl_idname = "VIEW3D_MT_lightprobe_add"
    bl_label = "Light Probe"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator_enum("object.lightprobe_add", "type")


class VIEW3D_MT_camera_add(Menu):
    bl_idname = "VIEW3D_MT_camera_add"
    bl_label = "Camera"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("object.camera_add", text="Camera", icon="OUTLINER_OB_CAMERA")


class VIEW3D_MT_volume_add(Menu):
    bl_idname = "VIEW3D_MT_volume_add"
    bl_label = "Volume"
    bl_translation_context = i18n_contexts.id_id
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout
        layout.operator(
            "object.volume_import", text="Import OpenVDB", icon="FILE_VOLUME"
        )
        layout.operator(
            "object.volume_add",
            text="Empty",
            text_ctxt=i18n_contexts.id_volume,
            icon="OUTLINER_OB_VOLUME",
        )


class VIEW3D_MT_grease_pencil_add(Menu):
    bl_idname = "VIEW3D_MT_grease_pencil_add"
    bl_label = "Grease Pencil"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout
        layout.operator(
            "object.grease_pencil_add", text="Blank", icon="EMPTY_AXIS"
        ).type = "EMPTY"
        layout.operator(
            "object.grease_pencil_add", text="Stroke", icon="STROKE"
        ).type = "STROKE"
        layout.operator(
            "object.grease_pencil_add", text="Monkey", icon="MONKEY"
        ).type = "MONKEY"
        layout.separator()

        layout.operator(
            "object.grease_pencil_add", text="Scene Line Art", icon="LINEART_SCENE"
        ).type = "LINEART_SCENE"
        layout.operator(
            "object.grease_pencil_add",
            text="Collection Line Art",
            icon="LINEART_COLLECTION",
        ).type = "LINEART_COLLECTION"
        layout.operator(
            "object.grease_pencil_add", text="Object Line Art", icon="LINEART_OBJECT"
        ).type = "LINEART_OBJECT"


class VIEW3D_MT_empty_add(Menu):
    bl_idname = "VIEW3D_MT_empty_add"
    bl_label = "Empty"
    bl_translation_context = i18n_contexts.operator_default
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator_enum("object.empty_add", "type")


class VIEW3D_MT_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, context):
        layout = self.layout

        if layout.operator_context == "EXEC_REGION_WIN":
            layout.operator_context = "INVOKE_REGION_WIN"
            layout.operator(
                "WM_OT_search_single_menu", text="Search...", icon="VIEWZOOM"
            ).menu_idname = "VIEW3D_MT_add"
            layout.separator()
        else:
            # BFA - make sure you can see it in the header
            layout.operator(
                "WM_OT_search_single_menu", text="Search...", icon="VIEWZOOM"
            ).menu_idname = "VIEW3D_MT_add"

        layout.separator()

        # NOTE: don't use 'EXEC_SCREEN' or operators won't get the `v3d` context.

        # NOTE: was `EXEC_AREA`, but this context does not have the `rv3d`, which prevents
        #       "align_view" to work on first call (see #32719).
        layout.operator_context = "EXEC_REGION_WIN"

        # layout.operator_menu_enum("object.mesh_add", "type", text="Mesh", icon='OUTLINER_OB_MESH')
        layout.menu("VIEW3D_MT_mesh_add", icon="OUTLINER_OB_MESH")

        # layout.operator_menu_enum("object.curve_add", "type", text="Curve", icon='OUTLINER_OB_CURVE')
        layout.menu("VIEW3D_MT_curve_add", icon="OUTLINER_OB_CURVE")
        # layout.operator_menu_enum("object.surface_add", "type", text="Surface", icon='OUTLINER_OB_SURFACE')
        layout.menu("VIEW3D_MT_surface_add", icon="OUTLINER_OB_SURFACE")
        layout.menu("VIEW3D_MT_metaball_add", text="Metaball", icon="OUTLINER_OB_META")
        layout.operator("object.text_add", text="Text", icon="OUTLINER_OB_FONT")
        if context.preferences.experimental.use_new_point_cloud_type:
            layout.operator(
                "object.pointcloud_add",
                text="Point Cloud",
                icon="OUTLINER_OB_POINTCLOUD",
            )
        layout.menu(
            "VIEW3D_MT_volume_add",
            text="Volume",
            text_ctxt=i18n_contexts.id_id,
            icon="OUTLINER_OB_VOLUME",
        )
        layout.menu(
            "VIEW3D_MT_grease_pencil_add",
            text="Grease Pencil",
            icon="OUTLINER_OB_GREASEPENCIL",
        )

        layout.separator()

        if VIEW3D_MT_armature_add.is_extended():
            layout.menu("VIEW3D_MT_armature_add", icon="OUTLINER_OB_ARMATURE")
        else:
            layout.operator(
                "object.armature_add", text="Armature", icon="OUTLINER_OB_ARMATURE"
            )

        layout.operator(
            "object.add", text="Lattice", icon="OUTLINER_OB_LATTICE"
        ).type = "LATTICE"
        layout.separator()

        layout.operator_menu_enum(
            "object.empty_add",
            "type",
            text="Empty",
            text_ctxt=i18n_contexts.id_id,
            icon="OUTLINER_OB_EMPTY",
        )
        layout.menu("VIEW3D_MT_image_add", text="Image", icon="OUTLINER_OB_IMAGE")

        layout.separator()

        layout.operator(
            "object.speaker_add", text="Speaker", icon="OUTLINER_OB_SPEAKER"
        )
        layout.separator()

        if VIEW3D_MT_camera_add.is_extended():
            layout.menu("VIEW3D_MT_camera_add", icon="OUTLINER_OB_CAMERA")
        else:
            VIEW3D_MT_camera_add.draw(self, context)

        layout.menu("VIEW3D_MT_light_add", icon="OUTLINER_OB_LIGHT")

        layout.separator()

        layout.menu("VIEW3D_MT_lightprobe_add", icon="OUTLINER_OB_LIGHTPROBE")

        layout.separator()

        layout.operator_menu_enum(
            "object.effector_add",
            "type",
            text="Force Field",
            icon="OUTLINER_OB_FORCE_FIELD",
        )

        layout.separator()

        has_collections = bool(bpy.data.collections)
        col = layout.column()
        col.enabled = has_collections

        if not has_collections or len(bpy.data.collections) > 10:
            col.operator_context = "INVOKE_REGION_WIN"
            col.operator(
                "object.collection_instance_add",
                text="Collection Instance"
                if has_collections
                else "No Collections to Instance",
                icon="OUTLINER_OB_GROUP_INSTANCE",
            )
        else:
            col.operator_menu_enum(
                "object.collection_instance_add",
                "collection",
                text="Collection Instance",
                icon="OUTLINER_OB_GROUP_INSTANCE",
            )


class VIEW3D_MT_image_add(Menu):
    bl_label = "Add Image"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, _context):
        layout = self.layout
        # Explicitly set background mode on/off as operator will try to
        # auto-detect which mode to use otherwise.
        layout.operator(
            "object.empty_image_add", text="Reference", icon="IMAGE_REFERENCE"
        ).background = False
        layout.operator(
            "object.empty_image_add", text="Background", icon="IMAGE_BACKGROUND"
        ).background = True
        layout.operator(
            "image.import_as_mesh_planes", text="Mesh Plane", icon="MESH_PLANE"
        )


class VIEW3D_MT_object_relations(Menu):
    bl_label = "Relations"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.make_dupli_face", icon="MAKEDUPLIFACE")

        layout.separator()

        layout.operator_menu_enum("object.make_local", "type", text="Make Local")
        layout.menu("VIEW3D_MT_make_single_user")


# bfa menu
class VIEW3D_MT_origin_set(Menu):
    bl_label = "Set Origin"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.origin_set", icon="GEOMETRY_TO_ORIGIN", text="Geometry to Origin"
        ).type = "GEOMETRY_ORIGIN"
        layout.operator(
            "object.origin_set", icon="ORIGIN_TO_GEOMETRY", text="Origin to Geometry"
        ).type = "ORIGIN_GEOMETRY"
        layout.operator(
            "object.origin_set", icon="ORIGIN_TO_CURSOR", text="Origin to 3D Cursor"
        ).type = "ORIGIN_CURSOR"
        layout.operator(
            "object.origin_set",
            icon="ORIGIN_TO_CENTEROFMASS",
            text="Origin to Center of Mass (Surface)",
        ).type = "ORIGIN_CENTER_OF_MASS"
        layout.operator(
            "object.origin_set",
            icon="ORIGIN_TO_VOLUME",
            text="Origin to Center of Mass (Volume)",
        ).type = "ORIGIN_CENTER_OF_VOLUME"


# ********** Object menu **********


class VIEW3D_MT_object_liboverride(Menu):
    bl_label = "Library Override"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.make_override_library", text="Make", icon="LIBRARY")
        layout.operator("object.reset_override_library", text="Reset", icon="RESET")
        layout.operator("object.clear_override_library", text="Clear", icon="CLEAR")


class VIEW3D_MT_object(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        view = context.space_data

        layout.menu("VIEW3D_MT_transform_object")
        layout.menu("VIEW3D_MT_origin_set")  # bfa menu
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("object.duplicate_move", icon="DUPLICATE")
        layout.operator("object.duplicate_move_linked", icon="DUPLICATE")
        layout.operator("object.join", icon="JOIN")

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"
        myvar = layout.operator("object.delete", text="Delete", icon="DELETE")
        myvar.use_global = False
        myvar.confirm = False
        myvar = layout.operator("object.delete", text="Delete Global", icon="DELETE")
        myvar.use_global = True
        myvar.confirm = False

        layout.separator()

        layout.operator("view3d.copybuffer", text="Copy Objects", icon="COPYDOWN")
        layout.operator("view3d.pastebuffer", text="Paste Objects", icon="PASTEDOWN")

        layout.separator()

        layout.menu("VIEW3D_MT_object_asset")

        layout.separator()

        layout.menu("VIEW3D_MT_object_liboverride")
        layout.menu("VIEW3D_MT_object_relations")
        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_object_constraints")
        layout.menu("VIEW3D_MT_object_track")
        layout.menu("VIEW3D_MT_make_links")

        layout.separator()

        layout.menu("VIEW3D_MT_object_collection")

        # BFA: shading just for mesh and curve objects
        if ob is None:
            pass

        elif ob.type in {"MESH", "CURVE", "SURFACE"}:
            layout.separator()

            layout.operator("object.shade_smooth", icon="SHADING_SMOOTH")
            if ob and ob.type == "MESH":
                layout.operator("object.shade_auto_smooth", icon="NORMAL_SMOOTH")
            layout.operator("object.shade_flat", icon="SHADING_FLAT")

        layout.separator()

        layout.menu("VIEW3D_MT_object_animation")
        layout.menu("VIEW3D_MT_object_rigid_body")

        layout.separator()

        layout.menu("VIEW3D_MT_object_quick_effects")
        layout.menu("VIEW3D_MT_subdivision_set")  # bfa menu

        layout.separator()

        layout.menu("VIEW3D_MT_object_convert")

        layout.separator()

        layout.menu("VIEW3D_MT_object_showhide")
        layout.menu("VIEW3D_MT_object_cleanup")

        if ob is None:
            pass

        elif ob.type == "CAMERA":
            layout.operator_context = "INVOKE_REGION_WIN"

            layout.separator()

            if ob.data.type == "PERSP":
                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Focal Length",
                    icon="LENS_ANGLE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.lens"
                props.input_scale = 0.1
                if ob.data.lens_unit == "MILLIMETERS":
                    props.header_text = "Camera Focal Length: %.1fmm"
                else:
                    props.header_text = "Camera Focal Length: %.1f\u00b0"

            else:
                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Camera Lens Scale",
                    icon="LENS_SCALE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.ortho_scale"
                props.input_scale = 0.01
                props.header_text = "Camera Lens Scale: %.3f"

            if not ob.data.dof.focus_object:
                if (
                    view
                    and view.camera == ob
                    and view.region_3d.view_perspective == "CAMERA"
                ):
                    props = layout.operator(
                        "ui.eyedropper_depth", text="DOF Distance (Pick)", icon="DOF"
                    )
                else:
                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Focus Distance",
                        icon="DOF",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.dof.focus_distance"
                    props.input_scale = 0.02
                    props.header_text = "Focus Distance: %.3f"

        elif ob.type in {"CURVE", "FONT"}:
            layout.operator_context = "INVOKE_REGION_WIN"

            layout.separator()

            props = layout.operator(
                "wm.context_modal_mouse", text="Adjust Extrusion", icon="EXTRUDESIZE"
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.extrude"
            props.input_scale = 0.01
            props.header_text = "Extrude: %.3f"

            props = layout.operator(
                "wm.context_modal_mouse", text="Adjust Offset", icon="WIDTH_SIZE"
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.offset"
            props.input_scale = 0.01
            props.header_text = "Offset %.3f"

        elif ob.type == "EMPTY":
            layout.operator_context = "INVOKE_REGION_WIN"

            layout.separator()

            props = layout.operator(
                "wm.context_modal_mouse",
                text="Adjust Empty Display Size",
                icon="DRAWSIZE",
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "empty_display_size"
            props.input_scale = 0.01
            props.header_text = "Empty Diosplay Size: %.3f"

        elif ob.type == "LIGHT":
            light = ob.data

            layout.operator_context = "INVOKE_REGION_WIN"

            layout.separator()

            props = layout.operator(
                "wm.context_modal_mouse",
                text="Adjust Light Power",
                icon="LIGHT_STRENGTH",
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.energy"
            props.input_scale = 1.0
            props.header_text = "Light Power: %.3f"

            if light.type == "AREA":
                if light.shape in {"RECTANGLE", "ELLIPSE"}:
                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Area Light X Size",
                        icon="LIGHT_SIZE",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size"
                    props.header_text = "Light Size X: %.3f"

                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Area Light Y Size",
                        icon="LIGHT_SIZE",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size_y"
                    props.header_text = "Light Size Y: %.3f"
                else:
                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Area Light Size",
                        icon="LIGHT_SIZE",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size"
                    props.header_text = "Light Size: %.3f"

            elif light.type in {"SPOT", "POINT"}:
                props = layout.operator(
                    "wm.context_modal_mouse", text="Adjust Light Radius", icon="RADIUS"
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.shadow_soft_size"
                props.header_text = "Light Radius: %.3f"

            elif light.type == "SUN":
                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Sun Light Angle",
                    icon="ANGLE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.angle"
                props.header_text = "Light Angle: %.3f"

            if light.type == "SPOT":
                layout.separator()

                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Spot Light Size",
                    icon="LIGHT_SIZE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_size"
                props.input_scale = 0.01
                props.header_text = "Spot Size: %.2f"

                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Spot Light Blend",
                    icon="SPOT_BLEND",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_blend"
                props.input_scale = -0.01
                props.header_text = "Spot Blend: %.2f"

            if light.type in {"SPOT", "SUN", "AREA"}:
                props = layout.operator(
                    "object.transform_axis_target",
                    text="Interactive Light Track",
                    icon="NODE_LIGHTPATH",
                )

        layout.template_node_operator_asset_menu_items(catalog_path="Object")


class VIEW3D_MT_object_animation(Menu):
    bl_label = "Animation"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "anim.keyframe_insert", text="Insert Keyframe", icon="KEYFRAMES_INSERT"
        )
        layout.operator(
            "anim.keyframe_insert_menu",
            text="Insert Keyframe with Keying Set",
            icon="KEYFRAMES_INSERT",
        ).always_prompt = True
        layout.operator(
            "anim.keyframe_delete_v3d", text="Delete Keyframes", icon="KEYFRAMES_REMOVE"
        )
        layout.operator(
            "anim.keyframe_clear_v3d", text="Clear Keyframes", icon="KEYFRAMES_CLEAR"
        )
        layout.operator(
            "anim.keying_set_active_set", text="Change Keying Set", icon="KEYINGSET"
        )

        layout.separator()

        layout.operator("nla.bake", text="Bake Action", icon="BAKE_ACTION")
        layout.operator(
            "gpencil.bake_mesh_animation",
            text="Bake Mesh to Grease Pencil",
            icon="BAKE_ACTION",
        )


class VIEW3D_MT_object_rigid_body(Menu):
    bl_label = "Rigid Body"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "rigidbody.objects_add", text="Add Active", icon="RIGID_ADD_ACTIVE"
        ).type = "ACTIVE"
        layout.operator(
            "rigidbody.objects_add", text="Add Passive", icon="RIGID_ADD_PASSIVE"
        ).type = "PASSIVE"

        layout.separator()

        layout.operator("rigidbody.objects_remove", text="Remove", icon="RIGID_REMOVE")

        layout.separator()

        layout.operator(
            "rigidbody.shape_change", text="Change Shape", icon="RIGID_CHANGE_SHAPE"
        )
        layout.operator(
            "rigidbody.mass_calculate",
            text="Calculate Mass",
            icon="RIGID_CALCULATE_MASS",
        )
        layout.operator(
            "rigidbody.object_settings_copy",
            text="Copy from Active",
            icon="RIGID_COPY_FROM_ACTIVE",
        )
        layout.operator(
            "object.visual_transform_apply",
            text="Apply Transformation",
            icon="RIGID_APPLY_TRANS",
        )
        layout.operator(
            "rigidbody.bake_to_keyframes",
            text="Bake To Keyframes",
            icon="RIGID_BAKE_TO_KEYFRAME",
        )

        layout.separator()

        layout.operator(
            "rigidbody.connect", text="Connect", icon="RIGID_CONSTRAINTS_CONNECT"
        )


class VIEW3D_MT_object_clear(Menu):
    bl_label = "Clear"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "object.location_clear",
            text="Location",
            text_ctxt=i18n_contexts.default,
            icon="CLEARMOVE",
        ).clear_delta = False
        layout.operator(
            "object.rotation_clear",
            text="Rotation",
            text_ctxt=i18n_contexts.default,
            icon="CLEARROTATE",
        ).clear_delta = False
        layout.operator(
            "object.scale_clear",
            text="Scale",
            text_ctxt=i18n_contexts.default,
            icon="CLEARSCALE",
        ).clear_delta = False

        layout.separator()

        layout.operator("object.origin_clear", text="Origin", icon="CLEARORIGIN")


class VIEW3D_MT_object_context_menu(Menu):
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        obj = context.object

        selected_objects_len = len(context.selected_objects)

        # If nothing is selected
        # (disabled for now until it can be made more useful).
        """
        if selected_objects_len == 0:

            layout.menu("VIEW3D_MT_add", text="Add", text_ctxt=i18n_contexts.operator_default)
            layout.operator("view3d.pastebuffer", text="Paste Objects", icon='PASTEDOWN')

            return
        """

        # If something is selected

        # Individual object types.
        if obj is None:
            pass

        elif obj.type == "CAMERA":
            layout.operator_context = "INVOKE_REGION_WIN"

            layout.operator(
                "view3d.object_as_camera",
                text="Set Active Camera",
                icon="VIEW_SWITCHACTIVECAM",
            )

            if obj.data.type == "PERSP":
                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Focal Length",
                    icon="LENS_ANGLE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.lens"
                props.input_scale = 0.1
                if obj.data.lens_unit == "MILLIMETERS":
                    props.header_text = rpt_("Camera Focal Length: %.1fmm")
                else:
                    props.header_text = rpt_("Camera Focal Length: %.1f\u00b0")

            else:
                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Camera Lens Scale",
                    icon="LENS_SCALE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.ortho_scale"
                props.input_scale = 0.01
                props.header_text = rpt_("Camera Lens Scale: %.3f")

            if not obj.data.dof.focus_object:
                if (
                    view
                    and view.camera == obj
                    and view.region_3d.view_perspective == "CAMERA"
                ):
                    props = layout.operator(
                        "ui.eyedropper_depth", text="DOF Distance (Pick)", icon="DOF"
                    )
                else:
                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Focus Distance",
                        icon="DOF",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.dof.focus_distance"
                    props.input_scale = 0.02
                    props.header_text = rpt_("Focus Distance: %.3f")

            layout.separator()

        elif obj.type in {"CURVE", "FONT"}:
            layout.operator_context = "INVOKE_REGION_WIN"

            props = layout.operator(
                "wm.context_modal_mouse", text="Adjust Extrusion", icon="EXTRUDESIZE"
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.extrude"
            props.input_scale = 0.01
            props.header_text = rpt_("Extrude: %.3f")

            props = layout.operator(
                "wm.context_modal_mouse", text="Adjust Offset", icon="WIDTH_SIZE"
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.offset"
            props.input_scale = 0.01
            props.header_text = rpt_("Offset: %.3f")

            layout.separator()

        elif obj.type == "EMPTY":
            layout.operator_context = "INVOKE_REGION_WIN"

            props = layout.operator(
                "wm.context_modal_mouse",
                text="Adjust Empty Display Size",
                icon="DRAWSIZE",
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "empty_display_size"
            props.input_scale = 0.01
            props.header_text = rpt_("Empty Display Size: %.3f")

            layout.separator()

            if obj.empty_display_type == "IMAGE":
                layout.operator(
                    "image.convert_to_mesh_plane",
                    text="Convert to Mesh Plane",
                    icon="MESH_PLANE",
                )
                layout.operator("grease_pencil.trace_image", icon="FILE_IMAGE")

                layout.separator()

        elif obj.type == "LIGHT":
            light = obj.data

            layout.operator_context = "INVOKE_REGION_WIN"

            props = layout.operator(
                "wm.context_modal_mouse",
                text="Adjust Light Power",
                icon="LIGHT_STRENGTH",
            )
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.energy"
            props.input_scale = 1.0
            props.header_text = rpt_("Light Power: %.3f")

            if light.type == "AREA":
                if light.shape in {"RECTANGLE", "ELLIPSE"}:
                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Area Light X Size",
                        icon="LIGHT_SIZE",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size"
                    props.header_text = rpt_("Light Size X: %.3f")

                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Area Light Y Size",
                        icon="LIGHT_SIZE",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size_y"
                    props.header_text = rpt_("Light Size Y: %.3f")
                else:
                    props = layout.operator(
                        "wm.context_modal_mouse",
                        text="Adjust Area Light Size",
                        icon="LIGHT_SIZE",
                    )
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size"
                    props.header_text = rpt_("Light Size: %.3f")

            elif light.type in {"SPOT", "POINT"}:
                props = layout.operator(
                    "wm.context_modal_mouse", text="Adjust Light Radius", icon="RADIUS"
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.shadow_soft_size"
                props.header_text = rpt_("Light Radius: %.3f")

            elif light.type == "SUN":
                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Sun Light Angle",
                    icon="ANGLE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.angle"
                props.header_text = rpt_("Light Angle: %.3f")

            if light.type == "SPOT":
                layout.separator()

                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Spot Light Size",
                    icon="LIGHT_SIZE",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_size"
                props.input_scale = 0.01
                props.header_text = rpt_("Spot Size: %.2f")

                props = layout.operator(
                    "wm.context_modal_mouse",
                    text="Adjust Spot Light Blend",
                    icon="SPOT_BLEND",
                )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_blend"
                props.input_scale = -0.01
                props.header_text = rpt_("Spot Blend: %.2f")

            # BFA - added for consistency and accessibility from context menu
            if light.type in {"SPOT", "SUN", "AREA"}:
                props = layout.operator(
                    "object.transform_axis_target",
                    text="Interactive Light Track",
                    icon="NODE_LIGHTPATH",
                )
            layout.separator()

        # Shared among some object types.
        if obj is not None:
            if obj.type in {"MESH", "CURVE", "SURFACE"}:
                layout.operator(
                    "object.shade_smooth", text="Shade Smooth", icon="SHADING_SMOOTH"
                )
                if obj.type == "MESH":
                    layout.operator("object.shade_auto_smooth", icon="NORMAL_SMOOTH")
                layout.operator(
                    "object.shade_flat", text="Shade Flat", icon="SHADING_FLAT"
                )
                layout.separator()

            if obj.type in {"MESH", "CURVE", "SURFACE", "ARMATURE", "GREASEPENCIL"}:
                if selected_objects_len > 1:
                    layout.operator("object.join")

            if obj.type in {
                "MESH",
                "CURVE",
                "CURVES",
                "SURFACE",
                "POINTCLOUD",
                "META",
                "FONT",
            }:
                layout.operator_menu_enum("object.convert", "target")

            if obj.type in {
                "MESH",
                "CURVE",
                "CURVES",
                "SURFACE",
                "GREASEPENCIL",
                "LATTICE",
                "ARMATURE",
                "META",
                "FONT",
                "POINTCLOUD",
            } or (obj.type == "EMPTY" and obj.instance_collection is not None):
                layout.operator_context = "INVOKE_REGION_WIN"
                layout.operator_menu_enum(
                    "object.origin_set", text="Set Origin", property="type"
                )
                layout.operator_context = "INVOKE_DEFAULT"

                layout.separator()

        # Shared among all object types
        layout.operator("view3d.copybuffer", text="Copy Objects", icon="COPYDOWN")
        layout.operator("view3d.pastebuffer", text="Paste Objects", icon="PASTEDOWN")

        layout.separator()

        layout.operator("object.duplicate_move", icon="DUPLICATE")
        layout.operator("object.duplicate_move_linked", icon="DUPLICATE")

        layout.separator()

        props = layout.operator(
            "wm.call_panel", text="Rename Active Object", icon="RENAME"
        )
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.separator()

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.menu("VIEW3D_MT_object_parent")

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("object.move_to_collection", icon="GROUP")

        layout.separator()
        if view and view.local_view:
            layout.operator(
                "view3d.localview", text="Toggle Local View", icon="VIEW_GLOBAL_LOCAL"
            )  # BFA - Can toggle in, so toggle out too
            layout.operator("view3d.localview_remove_from", icon="VIEW_REMOVE_LOCAL")
        else:
            # BFA - made it relevant to local view conditional
            layout.operator(
                "view3d.localview", text="Toggle Local View", icon="VIEW_GLOBAL_LOCAL"
            )

        layout.separator()

        layout.operator(
            "anim.keyframe_insert", text="Insert Keyframe", icon="KEYFRAMES_INSERT"
        )
        layout.operator(
            "anim.keyframe_insert_menu",
            text="Insert Keyframe with Keying Set",
            icon="KEYFRAMES_INSERT",
        ).always_prompt = True

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator(
            "object.delete", text="Delete", icon="DELETE"
        ).use_global = False

        layout.separator()

        layout.menu("VIEW3D_MT_object_showhide")  # BFA - added to context menu

        layout.template_node_operator_asset_menu_items(catalog_path="Object")


class VIEW3D_MT_object_shading(Menu):
    # XXX, this menu is a place to store shading operator in object mode
    bl_label = "Shading"

    def draw(self, _context):
        layout = self.layout
        layout.operator("object.shade_smooth", text="Smooth", icon="SHADING_SMOOTH")
        layout.operator("object.shade_flat", text="Flat", icon="SHADING_FLAT")


class VIEW3D_MT_object_apply(Menu):
    bl_label = "Apply"

    def draw(self, _context):
        layout = self.layout

        # Need invoke for the popup confirming the multi-user data operation
        layout.operator_context = "INVOKE_DEFAULT"

        props = layout.operator(
            "object.transform_apply",
            text="Location",
            text_ctxt=i18n_contexts.default,
            icon="APPLYMOVE",
        )
        props.location, props.rotation, props.scale = True, False, False

        props = layout.operator(
            "object.transform_apply",
            text="Rotation",
            text_ctxt=i18n_contexts.default,
            icon="APPLYROTATE",
        )
        props.location, props.rotation, props.scale = False, True, False

        props = layout.operator(
            "object.transform_apply",
            text="Scale",
            text_ctxt=i18n_contexts.default,
            icon="APPLYSCALE",
        )
        props.location, props.rotation, props.scale = False, False, True

        props = layout.operator(
            "object.transform_apply",
            text="All Transforms",
            text_ctxt=i18n_contexts.default,
            icon="APPLYALL",
        )
        props.location, props.rotation, props.scale = True, True, True

        props = layout.operator(
            "object.transform_apply",
            text="Rotation & Scale",
            text_ctxt=i18n_contexts.default,
            icon="APPLY_ROTSCALE",
        )
        props.location, props.rotation, props.scale = False, True, True

        layout.separator()

        layout.operator(
            "object.transforms_to_deltas",
            text="Location to Deltas",
            text_ctxt=i18n_contexts.default,
            icon="APPLYMOVEDELTA",
        ).mode = "LOC"
        layout.operator(
            "object.transforms_to_deltas",
            text="Rotation to Deltas",
            text_ctxt=i18n_contexts.default,
            icon="APPLYROTATEDELTA",
        ).mode = "ROT"
        layout.operator(
            "object.transforms_to_deltas",
            text="Scale to Deltas",
            text_ctxt=i18n_contexts.default,
            icon="APPLYSCALEDELTA",
        ).mode = "SCALE"
        layout.operator(
            "object.transforms_to_deltas",
            text="All Transforms to Deltas",
            text_ctxt=i18n_contexts.default,
            icon="APPLYALLDELTA",
        ).mode = "ALL"
        layout.operator("object.anim_transforms_to_deltas", icon="APPLYANIDELTA")

        layout.separator()

        layout.operator(
            "object.visual_transform_apply",
            text="Visual Transform",
            text_ctxt=i18n_contexts.default,
            icon="VISUALTRANSFORM",
        )
        layout.operator("object.duplicates_make_real", icon="MAKEDUPLIREAL")
        layout.operator(
            "object.parent_inverse_apply",
            text="Parent Inverse",
            text_ctxt=i18n_contexts.default,
            icon="APPLY_PARENT_INVERSE",
        )
        # layout.operator("object.duplicates_make_real") # BFA - redundant
        # layout.operator("object.parent_inverse_apply", text="Parent Inverse",
        # text_ctxt=i18n_contexts.default)  # BFA - redundant

        layout.template_node_operator_asset_menu_items(catalog_path="Object/Apply")


class VIEW3D_MT_object_parent(Menu):
    bl_label = "Parent"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        from bl_ui_utils.layout import operator_context

        layout = self.layout

        layout.operator_enum("object.parent_set", "type")

        layout.separator()

        with operator_context(layout, "EXEC_REGION_WIN"):
            layout.operator(
                "object.parent_no_inverse_set", icon="PARENT"
            ).keep_transform = False
            props = layout.operator(
                "object.parent_no_inverse_set",
                text="Make Parent without Inverse (Keep Transform)",
                icon="PARENT",
            )
            props.keep_transform = True

            layout.operator(
                "curves.surface_set",
                text="Object (Attach Curves to Surface)",
                icon="PARENT_CURVE",
            )

        layout.separator()

        layout.operator_enum("object.parent_clear", "type")


class VIEW3D_MT_object_track(Menu):
    bl_label = "Track"
    bl_translation_context = i18n_contexts.constraint

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "object.track_set", text="Damped Track Constraint", icon="CONSTRAINT_DATA"
        ).type = "DAMPTRACK"
        layout.operator(
            "object.track_set", text="Track to Constraint", icon="CONSTRAINT_DATA"
        ).type = "TRACKTO"
        layout.operator(
            "object.track_set", text="Lock Track Constraint", icon="CONSTRAINT_DATA"
        ).type = "LOCKTRACK"

        layout.separator()

        layout.operator(
            "object.track_clear", text="Clear Track", icon="CLEAR_TRACK"
        ).type = "CLEAR"
        layout.operator(
            "object.track_clear",
            text="Clear Track - Keep Transformation",
            icon="CLEAR_TRACK",
        ).type = "CLEAR_KEEP_TRANSFORM"


# BFA - not referenced in the 3D View Editor - but referenced by hotkey M in Blender keymap.


class VIEW3D_MT_object_collection(Menu):
    bl_label = "Collection"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("object.move_to_collection", icon="GROUP")

        layout.operator("object.link_to_collection", icon="GROUP")

        layout.separator()

        layout.operator("collection.create", icon="COLLECTION_NEW")
        # layout.operator_menu_enum("collection.objects_remove", "collection")  # BUGGY
        layout.operator("collection.objects_remove", icon="DELETE")
        layout.operator("collection.objects_remove_all", icon="DELETE")

        layout.separator()

        layout.operator("collection.objects_add_active", icon="GROUP")
        layout.operator("collection.objects_remove_active", icon="DELETE")


class VIEW3D_MT_object_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.constraint_add_with_targets", icon="CONSTRAINT_DATA")
        layout.operator("object.constraints_copy", icon="COPYDOWN")

        layout.separator()

        layout.operator("object.constraints_clear", icon="CLEAR_CONSTRAINT")


# BFA - not used
class VIEW3D_MT_object_modifiers(Menu):
    bl_label = "Modifiers"

    def draw(self, _context):
        active_object = bpy.context.active_object
        supported_types = {
            "MESH",
            "CURVE",
            "CURVES",
            "SURFACE",
            "FONT",
            "VOLUME",
            "GREASEPENCIL",
            "LATTICE",
            "POINTCLOUD",
        }

        layout = self.layout

        if active_object:
            if active_object.type in supported_types:
                layout.menu("OBJECT_MT_modifier_add", text="Add Modifier")

        layout.operator(
            "object.modifiers_copy_to_selected",
            text="Copy Modifiers to Selected Objects",
        )

        layout.separator()

        layout.operator("object.modifiers_clear")


class VIEW3D_MT_object_quick_effects(Menu):
    bl_label = "Quick Effects"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.quick_fur", icon="CURVES")
        layout.operator("object.quick_explode", icon="MOD_EXPLODE")
        layout.operator("object.quick_smoke", icon="MOD_SMOKE")
        layout.operator("object.quick_liquid", icon="MOD_FLUIDSIM")
        layout.template_node_operator_asset_menu_items(
            catalog_path="Object/Quick Effects"
        )


class VIEW3D_MT_object_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.hide_view_clear", text="Show Hidden", icon="HIDE_OFF")

        layout.separator()

        layout.operator(
            "object.hide_view_set", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "object.hide_view_set", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_object_cleanup(Menu):
    bl_label = "Clean Up"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "object.vertex_group_clean",
            text="Clean Vertex Group Weights",
            icon="CLEAN_CHANNELS",
        ).group_select_mode = "ALL"
        layout.operator(
            "object.vertex_group_limit_total",
            text="Limit Total Vertex Groups",
            icon="WEIGHT_LIMIT_TOTAL",
        ).group_select_mode = "ALL"

        layout.separator()

        layout.operator(
            "object.material_slot_remove_unused",
            text="Remove Unused Material Slots",
            icon="DELETE",
        )


class VIEW3D_MT_object_asset(Menu):
    bl_label = "Asset"

    def draw(self, _context):
        layout = self.layout

        layout.operator("asset.mark", icon="ASSIGN")
        layout.operator(
            "asset.clear", text="Clear Asset", icon="CLEAR"
        ).set_fake_user = False
        layout.operator(
            "asset.clear", text="Clear Asset (Set Fake User)", icon="CLEAR"
        ).set_fake_user = True


class VIEW3D_MT_make_single_user(Menu):
    bl_label = "Make Single User"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "EXEC_REGION_WIN"

        props = layout.operator(
            "object.make_single_user", text="Object", icon="MAKE_SINGLE_USER"
        )
        props.object = True
        props.obdata = props.material = props.animation = props.obdata_animation = False

        props = layout.operator(
            "object.make_single_user", text="Object & Data", icon="MAKE_SINGLE_USER"
        )
        props.object = props.obdata = True
        props.material = props.animation = props.obdata_animation = False

        props = layout.operator(
            "object.make_single_user",
            text="Object & Data & Materials",
            icon="MAKE_SINGLE_USER",
        )
        props.object = props.obdata = props.material = True
        props.animation = props.obdata_animation = False

        props = layout.operator(
            "object.make_single_user", text="Materials", icon="MAKE_SINGLE_USER"
        )
        props.material = True
        props.object = props.obdata = props.animation = props.obdata_animation = False

        props = layout.operator(
            "object.make_single_user", text="Object Animation", icon="MAKE_SINGLE_USER"
        )
        props.animation = True
        props.object = props.obdata = props.material = props.obdata_animation = False

        props = layout.operator(
            "object.make_single_user",
            text="Object Data Animation",
            icon="MAKE_SINGLE_USER",
        )
        props.obdata_animation = props.obdata = True
        props.object = props.material = props.animation = False


class VIEW3D_MT_object_convert(Menu):
    bl_label = "Convert"

    def draw(self, context):
        layout = self.layout
        ob = context.active_object

        if ob and ob.type != "EMPTY":
            layout.operator_enum("object.convert", "target")

        else:
            # Potrace lib dependency.
            if bpy.app.build_options.potrace:
                layout.operator(
                    "image.convert_to_mesh_plane",
                    text="Convert to Mesh Plane",
                    icon="MESH_PLANE",
                )
                layout.operator(
                    "grease_pencil.trace_image", icon="OUTLINER_OB_GREASEPENCIL"
                )

        if ob and ob.type == "CURVES":
            layout.operator(
                "curves.convert_to_particle_system",
                text="Particle System",
                icon="PARTICLES",
            )

        layout.template_node_operator_asset_menu_items(catalog_path="Object/Convert")


class VIEW3D_MT_make_links(Menu):
    bl_label = "Link/Transfer Data"

    def draw(self, _context):
        layout = self.layout
        operator_context_default = layout.operator_context

        if len(bpy.data.scenes) > 10:
            layout.operator_context = "INVOKE_REGION_WIN"
            layout.operator(
                "object.make_links_scene",
                text="Link Objects to Scene",
                icon="OUTLINER_OB_EMPTY",
            )
        else:
            layout.operator_context = "EXEC_REGION_WIN"
            layout.operator_menu_enum(
                "object.make_links_scene", "scene", text="Link Objects to Scene"
            )

        layout.separator()

        layout.operator_context = operator_context_default

        layout.operator_enum("object.make_links_data", "type")  # inline

        layout.separator()

        layout.operator("object.join_uvs", text="Copy UV Maps", icon="TRANSFER_UV")

        layout.separator()
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("object.data_transfer", icon="TRANSFER_DATA")
        layout.operator("object.datalayout_transfer", icon="TRANSFER_DATA_LAYOUT")

        layout.separator()
        layout.operator_menu_enum("object.light_linking_receivers_link", "link_state")
        layout.operator_menu_enum("object.light_linking_blockers_link", "link_state")


# BFA wip menu, removed?
class VIEW3D_MT_brush_paint_modes(Menu):
    bl_label = "Enabled Modes"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        layout.prop(brush, "use_paint_sculpt", text="Sculpt")
        layout.prop(brush, "use_paint_uv_sculpt", text="UV Sculpt")
        layout.prop(brush, "use_paint_vertex", text="Vertex Paint")
        layout.prop(brush, "use_paint_weight", text="Weight Paint")
        layout.prop(brush, "use_paint_image", text="Texture Paint")
        layout.prop(brush, "use_paint_sculpt_curves", text="Sculpt Curves")


# bfa menu
class VIEW3D_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = getattr(settings, "brush", None)
        obj = context.active_object
        mesh = context.object.data  # face selection masking for painting

        # skip if no active brush
        if not brush:
            layout.label(
                text="No Brush selected. Please select a brush first", icon="INFO"
            )
            return

        tex_slot = brush.texture_slot
        mask_tex_slot = brush.mask_texture_slot

        # brush tool
        if context.sculpt_object:
            layout.operator("brush.reset", icon="BRUSH_RESET")

        if tex_slot.map_mode == "STENCIL":
            layout.separator()

            layout.operator(
                "brush.stencil_control",
                text="Move Stencil Texture",
                icon="TRANSFORM_MOVE",
            ).mode = "TRANSLATION"
            layout.operator(
                "brush.stencil_control",
                text="Rotate Stencil Texture",
                icon="TRANSFORM_ROTATE",
            ).mode = "ROTATION"
            layout.operator(
                "brush.stencil_control",
                text="Scale Stencil Texture",
                icon="TRANSFORM_SCALE",
            ).mode = "SCALE"
            layout.operator(
                "brush.stencil_reset_transform",
                text="Reset Stencil Texture position",
                icon="RESET",
            )

        if mask_tex_slot.map_mode == "STENCIL":
            layout.separator()

            myvar = layout.operator(
                "brush.stencil_control",
                text="Move Stencil Mask Texture",
                icon="TRANSFORM_MOVE",
            )
            myvar.mode = "TRANSLATION"
            myvar.texmode = "SECONDARY"
            myvar = layout.operator(
                "brush.stencil_control",
                text="Rotate Stencil Mask Texture",
                icon="TRANSFORM_ROTATE",
            )
            myvar.mode = "ROTATION"
            myvar.texmode = "SECONDARY"
            myvar = layout.operator(
                "brush.stencil_control",
                text="Scale Stencil Mask Texture",
                icon="TRANSFORM_SCALE",
            )
            myvar.mode = "SCALE"
            myvar.texmode = "SECONDARY"
            layout.operator(
                "brush.stencil_reset_transform",
                text="Reset Stencil Mask Texture position",
                icon="RESET",
            ).mask = True

        # If face selection masking for painting is active
        if mesh.use_paint_mask:
            layout.separator()

            layout.menu(
                "VIEW3D_MT_facemask_showhide"
            )  # bfa - show hide for face mask tool

        # Color picker just in vertex and texture paint
        if obj.mode in {"VERTEX_PAINT", "TEXTURE_PAINT"}:
            layout.separator()

            layout.operator(
                "paint.sample_color", text="Color Picker", icon="EYEDROPPER"
            )


# bfa - show hide menu for face selection masking
class VIEW3D_MT_facemask_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.face_select_reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "paint.face_select_hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "paint.face_select_hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_paint_vertex(Menu):
    bl_label = "Paint"

    def draw(self, _context):
        layout = self.layout

        layout.operator("paint.vertex_color_set", icon="COLOR")  # BFA - Expose operator
        layout.operator("paint.vertex_color_smooth", icon="PARTICLEBRUSH_SMOOTH")
        layout.operator("paint.vertex_color_dirt", icon="DIRTY_VERTEX")
        layout.operator("paint.vertex_color_from_weight", icon="VERTCOLFROMWEIGHT")

        layout.separator()

        layout.operator(
            "paint.vertex_color_invert", text="Invert", icon="REVERSE_COLORS"
        )
        layout.operator("paint.vertex_color_levels", text="Levels", icon="LEVELS")
        layout.operator(
            "paint.vertex_color_hsv", text="Hue/Saturation/Value", icon="HUESATVAL"
        )
        layout.operator(
            "paint.vertex_color_brightness_contrast",
            text="Brightness/Contrast",
            icon="BRIGHTNESS_CONTRAST",
        )

        layout.separator()

        layout.operator("paint.vertex_color_set")
        layout.operator("paint.sample_color").merged = False


class VIEW3D_MT_hook(Menu):
    bl_label = "Hooks"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "EXEC_AREA"
        layout.operator("object.hook_add_newob", icon="HOOK_NEW")
        layout.operator("object.hook_add_selob", icon="HOOK_SELECTED").use_bone = False
        layout.operator(
            "object.hook_add_selob",
            text="Hook to Selected Object Bone",
            icon="HOOK_BONE",
        ).use_bone = True

        if any([mod.type == "HOOK" for mod in context.active_object.modifiers]):
            layout.separator()

            layout.operator_menu_enum(
                "object.hook_assign", "modifier", icon="HOOK_ASSIGN"
            )
            layout.operator_menu_enum(
                "object.hook_remove", "modifier", icon="HOOK_REMOVE"
            )

            layout.separator()

            layout.operator_menu_enum(
                "object.hook_select", "modifier", icon="HOOK_SELECT"
            )
            layout.operator_menu_enum(
                "object.hook_reset", "modifier", icon="HOOK_RESET"
            )
            layout.operator_menu_enum(
                "object.hook_recenter", "modifier", icon="HOOK_RECENTER"
            )


class VIEW3D_MT_vertex_group(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "EXEC_AREA"
        layout.operator("object.vertex_group_assign_new", icon="GROUP_VERTEX")

        ob = context.active_object
        if ob.mode == "EDIT" or (
            ob.mode == "WEIGHT_PAINT"
            and ob.type == "MESH"
            and ob.data.use_paint_mask_vertex
        ):
            if ob.vertex_groups.active:
                layout.separator()

                layout.operator(
                    "object.vertex_group_assign",
                    text="Assign to Active Group",
                    icon="ADD_TO_ACTIVE",
                )
                layout.operator(
                    "object.vertex_group_remove_from",
                    text="Remove from Active Group",
                    icon="REMOVE_SELECTED_FROM_ACTIVE_GROUP",
                ).use_all_groups = False
                layout.operator(
                    "object.vertex_group_remove_from",
                    text="Remove from All",
                    icon="REMOVE_FROM_ALL_GROUPS",
                ).use_all_groups = True

        if ob.vertex_groups.active:
            layout.separator()

            layout.operator_menu_enum(
                "object.vertex_group_set_active", "group", text="Set Active Group"
            )
            layout.operator(
                "object.vertex_group_remove",
                text="Remove Active Group",
                icon="REMOVE_ACTIVE_GROUP",
            ).all = False
            layout.operator(
                "object.vertex_group_remove",
                text="Remove All Groups",
                icon="REMOVE_ALL_GROUPS",
            ).all = True


class VIEW3D_MT_greasepencil_vertex_group(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "EXEC_AREA"

        layout.operator(
            "object.vertex_group_add", text="Add New Group", icon="GROUP_VERTEX"
        )


class VIEW3D_MT_paint_weight_lock(Menu):
    bl_label = "Vertex Group Locks"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "object.vertex_group_lock", text="Lock All", icon="LOCKED"
        )
        props.action, props.mask = "LOCK", "ALL"
        props = layout.operator(
            "object.vertex_group_lock", text="Lock Selected", icon="LOCKED"
        )
        props.action, props.mask = "LOCK", "SELECTED"
        props = layout.operator(
            "object.vertex_group_lock", text="Lock Unselected", icon="LOCKED"
        )
        props.action, props.mask = "LOCK", "UNSELECTED"
        props = layout.operator(
            "object.vertex_group_lock",
            text="Lock Only Selected",
            icon="RESTRICT_SELECT_OFF",
        )
        props.action, props.mask = "LOCK", "INVERT_UNSELECTED"

        layout.separator()

        props = layout.operator(
            "object.vertex_group_lock", text="Unlock All", icon="UNLOCKED"
        )
        props.action, props.mask = "UNLOCK", "ALL"
        props = layout.operator(
            "object.vertex_group_lock", text="Unlock Selected", icon="UNLOCKED"
        )
        props.action, props.mask = "UNLOCK", "SELECTED"
        props = layout.operator(
            "object.vertex_group_lock", text="Unlock Unselected", icon="UNLOCKED"
        )
        props.action, props.mask = "UNLOCK", "UNSELECTED"
        props = layout.operator(
            "object.vertex_group_lock",
            text="Lock Only Unselected",
            icon="RESTRICT_SELECT_ON",
        )
        props.action, props.mask = "UNLOCK", "INVERT_UNSELECTED"

        layout.separator()

        props = layout.operator(
            "object.vertex_group_lock", text="Invert Locks", icon="INVERSE"
        )
        props.action, props.mask = "INVERT", "ALL"


class VIEW3D_MT_paint_weight(Menu):
    bl_label = "Weights"

    @staticmethod
    def draw_generic(layout, is_editmode=False):
        layout.menu("VIEW3D_MT_paint_weight_legacy", text="Legacy")  # bfa menu

        if not is_editmode:
            layout.operator(
                "paint.weight_from_bones",
                text="Assign Automatic from Bones",
                icon="BONE_DATA",
            ).type = "AUTOMATIC"
            layout.operator(
                "paint.weight_from_bones",
                text="Assign from Bone Envelopes",
                icon="ENVELOPE_MODIFIER",
            ).type = "ENVELOPES"

            layout.separator()

        layout.operator(
            "object.vertex_group_normalize_all",
            text="Normalize All",
            icon="WEIGHT_NORMALIZE_ALL",
        )
        layout.operator(
            "object.vertex_group_normalize", text="Normalize", icon="WEIGHT_NORMALIZE"
        )

        layout.separator()

        layout.operator(
            "object.vertex_group_mirror", text="Mirror", icon="WEIGHT_MIRROR"
        )
        layout.operator(
            "object.vertex_group_invert", text="Invert", icon="WEIGHT_INVERT"
        )
        layout.operator("object.vertex_group_clean", text="Clean", icon="WEIGHT_CLEAN")

        layout.separator()

        layout.operator(
            "object.vertex_group_quantize", text="Quantize", icon="WEIGHT_QUANTIZE"
        )
        layout.operator(
            "object.vertex_group_levels", text="Levels", icon="WEIGHT_LEVELS"
        )
        layout.operator(
            "object.vertex_group_smooth", text="Smooth", icon="WEIGHT_SMOOTH"
        )

        if not is_editmode:
            props = layout.operator(
                "object.data_transfer",
                text="Transfer Weights",
                icon="WEIGHT_TRANSFER_WEIGHTS",
            )
            props.use_reverse_transfer = True
            props.data_type = "VGROUP_WEIGHTS"

        layout.operator(
            "object.vertex_group_limit_total",
            text="Limit Total",
            icon="WEIGHT_LIMIT_TOTAL",
        )

        if not is_editmode:
            layout.separator()

            # Primarily for shortcut discoverability.
            layout.operator("paint.weight_set", icon="MOD_VERTEX_WEIGHT")

        layout.separator()

        layout.menu("VIEW3D_MT_paint_weight_lock", text="Locks")

    def draw(self, context):
        obj = context.active_object
        if obj.type == "MESH":
            self.draw_generic(self.layout, is_editmode=False)


# BFA menu
class VIEW3D_MT_paint_weight_legacy(Menu):
    bl_label = "Legacy"

    @staticmethod
    def draw_generic(layout, is_editmode=False):
        if not is_editmode:
            layout.separator()

            # Primarily for shortcut discoverability.
            layout.operator(
                "paint.weight_sample", text="Sample Weight", icon="EYEDROPPER"
            )
            layout.operator(
                "paint.weight_sample_group", text="Sample Group", icon="EYEDROPPER"
            )

            layout.separator()

            # Primarily for shortcut discoverability.
            layout.operator(
                "paint.weight_gradient", text="Gradient (Linear)", icon="GRADIENT"
            ).type = "LINEAR"
            layout.operator(
                "paint.weight_gradient", text="Gradient (Radial)", icon="GRADIENT"
            ).type = "RADIAL"

    def draw(self, _context):
        self.draw_generic(self.layout, is_editmode=False)


# BFA menu
class VIEW3D_MT_subdivision_set(Menu):
    bl_label = "Subdivide"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator(
            "object.subdivision_set", text="Level 0", icon="SUBDIVIDE_EDGES"
        )
        myvar.relative = False
        myvar.level = 0
        myvar = layout.operator(
            "object.subdivision_set", text="Level 1", icon="SUBDIVIDE_EDGES"
        )
        myvar.relative = False
        myvar.level = 1
        myvar = layout.operator(
            "object.subdivision_set", text="Level 2", icon="SUBDIVIDE_EDGES"
        )
        myvar.relative = False
        myvar.level = 2
        myvar = layout.operator(
            "object.subdivision_set", text="Level 3", icon="SUBDIVIDE_EDGES"
        )
        myvar.relative = False
        myvar.level = 3
        myvar = layout.operator(
            "object.subdivision_set", text="Level 4", icon="SUBDIVIDE_EDGES"
        )
        myvar.relative = False
        myvar.level = 4
        myvar = layout.operator(
            "object.subdivision_set", text="Level 5", icon="SUBDIVIDE_EDGES"
        )
        myvar.relative = False
        myvar.level = 5


# BFA - heavily modified, careful!
class VIEW3D_MT_sculpt(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_sculpt_legacy")  # bfa menu
        layout.menu("VIEW3D_MT_bfa_sculpt_transform")  # bfa menu

        layout.separator()

        # Fair Positions
        props = layout.operator(
            "sculpt.face_set_edit", text="Fair Positions", icon="POSITION"
        )
        props.mode = "FAIR_POSITIONS"

        # Fair Tangency
        props = layout.operator(
            "sculpt.face_set_edit", text="Fair Tangency", icon="NODE_TANGENT"
        )
        props.mode = "FAIR_TANGENCY"

        layout.separator()

        # Add
        props = layout.operator(
            "sculpt.trim_box_gesture", text="Box Add", icon="BOX_ADD"
        )
        props.trim_mode = "JOIN"

        props = layout.operator(
            "sculpt.trim_lasso_gesture", text="Lasso Add", icon="LASSO_ADD"
        )
        props.trim_mode = "JOIN"

        layout.separator()

        # BFA - added icons to these
        sculpt_filters_types = [
            (
                "SMOOTH",
                iface_("Smooth", i18n_contexts.operator_default),
                "PARTICLEBRUSH_SMOOTH",
            ),
            ("SURFACE_SMOOTH", iface_("Surface Smooth"), "SURFACE_SMOOTH"),
            ("INFLATE", iface_("Inflate"), "INFLATE"),
            ("RELAX", iface_("Relax Topology"), "RELAX_TOPOLOGY"),
            ("RELAX_FACE_SETS", iface_("Relax Face Sets"), "RELAX_FACE_SETS"),
            ("SHARPEN", iface_("Sharpen"), "SHARPEN"),
            ("ENHANCE_DETAILS", iface_("Enhance Details"), "ENHANCE"),
            ("ERASE_DISPLACEMENT", iface_("Erase Multires Displacement"), "DELETE"),
            ("RANDOM", iface_("Randomize"), "RANDOMIZE"),
        ]
        # BFA - added icons to the list above
        for filter_type, ui_name, icon in sculpt_filters_types:
            props = layout.operator(
                "sculpt.mesh_filter", text=ui_name, icon=icon, translate=False
            )
            props.type = filter_type

        layout.separator()

        layout.menu("VIEW3D_MT_subdivision_set")  # BFA - add subdivion set menu
        layout.operator(
            "sculpt.sample_color", text="Sample Color", icon="EYEDROPPER"
        )  # BFA - icon added

        layout.separator()

        layout.menu("VIEW3D_MT_sculpt_set_pivot", text="Set Pivot")
        layout.menu("VIEW3D_MT_sculpt_showhide")  # BFA - menu

        layout.separator()

        # Rebuild BVH
        layout.operator("sculpt.optimize", icon="FILE_REFRESH")

        layout.operator(
            "object.transfer_mode", text="Transfer Sculpt Mode", icon="TRANSFER_SCULPT"
        )


# bfa menu
class VIEW3D_MT_sculpt_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", icon="TRANSFORM_MOVE")
        layout.operator("transform.rotate", icon="TRANSFORM_ROTATE")
        layout.operator("transform.resize", text="Scale", icon="TRANSFORM_SCALE")

        layout.separator()

        props = layout.operator("paint.hide_show", text="Box Hide", icon="BOX_HIDE")
        props.action = "HIDE"

        props = layout.operator("paint.hide_show", text="Box Show", icon="BOX_SHOW")
        props.action = "SHOW"

        layout.separator()

        props = layout.operator(
            "paint.hide_show_lasso_gesture", text="Lasso Hide", icon="LASSO_HIDE"
        )
        props.action = "HIDE"

        props = layout.operator(
            "paint.hide_show_lasso_gesture", text="Lasso Show", icon="LASSO_SHOW"
        )
        props.action = "SHOW"

        layout.separator()

        props = layout.operator(
            "paint.hide_show_line_gesture", text="Line Hide", icon="LINE_HIDE"
        )
        props.action = "HIDE"

        props = layout.operator(
            "paint.hide_show_line_gesture", text="Line Show", icon="LINE_SHOW"
        )
        props.action = "SHOW"

        layout.separator()

        props = layout.operator(
            "paint.hide_show_polyline_gesture",
            text="Polyline Hide",
            icon="POLYLINE_HIDE",
        )
        props.action = "HIDE"

        props = layout.operator(
            "paint.hide_show_polyline_gesture",
            text="Polyline Show",
            icon="POLYLINE_SHOW",
        )
        props.action = "SHOW"

        layout.separator()

        props = layout.operator(
            "sculpt.trim_box_gesture", text="Box Trim", icon="BOX_TRIM"
        )
        props.trim_mode = "DIFFERENCE"

        props = layout.operator(
            "sculpt.trim_lasso_gesture", text="Lasso Trim", icon="LASSO_TRIM"
        )
        props.trim_mode = "DIFFERENCE"

        props = layout.operator(
            "sculpt.trim_line_gesture", text="Line Trim", icon="LINE_TRIM"
        )
        props.trim_mode = "DIFFERENCE"

        layout.separator()

        layout.operator(
            "sculpt.project_line_gesture", text="Line Project", icon="LINE_PROJECT"
        )


# bfa menu
class VIEW3D_MT_bfa_sculpt_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("sculpt.mesh_filter", text="Sphere", icon="SPHERE")
        props.type = "SPHERE"


# bfa menu
class VIEW3D_MT_bfa_sculpt_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "sculpt.face_set_change_visibility",
            text="Toggle Visibility",
            icon="HIDE_OFF",
        )
        props.mode = "TOGGLE"

        props = layout.operator(
            "sculpt.face_set_change_visibility",
            text="Hide Active Face Set",
            icon="HIDE_ON",
        )
        props.mode = "HIDE_ACTIVE"

        props = layout.operator("paint.hide_show_all", text="Show All", icon="HIDE_OFF")
        props.action = "SHOW"

        props = layout.operator(
            "paint.visibility_invert", text="Invert Visible", icon="HIDE_ON"
        )

        props = layout.operator(
            "paint.hide_show_masked", text="Hide Masked", icon="MOD_MASK_OFF"
        )
        props.action = "HIDE"


# BFA - not used
class VIEW3D_MT_sculpt_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", icon="TRANSFORM_MOVE")
        layout.operator("transform.rotate", icon="TRANSFORM_ROTATE")
        layout.operator("transform.resize", text="Scale", icon="TRANSFORM_SCALE")

        layout.separator()
        props = layout.operator("sculpt.mesh_filter", text="Sphere", icon="SPHERE")
        props.type = "SPHERE"


# BFA - menu
class VIEW3D_MT_sculpt_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "sculpt.face_set_change_visibility",
            text="Toggle Visibility",
            icon="HIDE_OFF",
        )
        props.mode = "TOGGLE"

        props = layout.operator(
            "sculpt.face_set_change_visibility",
            text="Hide Active Face Set",
            icon="HIDE_ON",
        )
        props.mode = "HIDE_ACTIVE"

        props = layout.operator("paint.hide_show_all", text="Show All", icon="HIDE_OFF")
        props.action = "SHOW"

        props = layout.operator(
            "paint.visibility_invert", text="Invert Visible", icon="HIDE_ON"
        )

        props = layout.operator(
            "paint.hide_show_masked", text="Hide Masked", icon="MOD_MASK_OFF"
        )
        props.action = "HIDE"


# BFA - not used
class VIEW3D_MT_sculpt_trim(Menu):
    bl_label = "Trim/Add"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("sculpt.trim_box_gesture", text="Box Trim")
        props.trim_mode = "DIFFERENCE"

        props = layout.operator("sculpt.trim_lasso_gesture", text="Lasso Trim")
        props.trim_mode = "DIFFERENCE"

        props = layout.operator("sculpt.trim_line_gesture", text="Line Trim")
        props.trim_mode = "DIFFERENCE"

        props = layout.operator("sculpt.trim_polyline_gesture", text="Polyline Trim")
        props.trim_mode = "DIFFERENCE"

        layout.separator()

        props = layout.operator("sculpt.trim_box_gesture", text="Box Add")
        props.trim_mode = "JOIN"

        props = layout.operator("sculpt.trim_lasso_gesture", text="Lasso Add")
        props.trim_mode = "JOIN"

        props = layout.operator("sculpt.trim_polyline_gesture", text="Polyline Add")
        props.trim_mode = "JOIN"


class VIEW3D_MT_sculpt_curves(Menu):
    bl_label = "Curves"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "curves.snap_curves_to_surface",
            text="Snap to Deformed Surface",
            icon="SNAP_SURFACE",
        ).attach_mode = "DEFORM"
        layout.operator(
            "curves.snap_curves_to_surface",
            text="Snap to Nearest Surface",
            icon="SNAP_TO_ADJACENT",
        ).attach_mode = "NEAREST"
        layout.separator()
        layout.operator(
            "curves.convert_to_particle_system",
            text="Convert to Particle System",
            icon="PARTICLES",
        )

        layout.template_node_operator_asset_menu_items(catalog_path="Curves")


class VIEW3D_MT_mask(Menu):
    bl_label = "Mask"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_mask_legacy")  # bfa menu

        props = layout.operator(
            "paint.mask_flood_fill", text="Invert Mask", icon="INVERT_MASK"
        )
        props.mode = "INVERT"

        props = layout.operator(
            "paint.mask_flood_fill", text="Fill Mask", icon="FILL_MASK"
        )
        props.mode = "VALUE"
        props.value = 1

        props = layout.operator(
            "paint.mask_flood_fill", text="Clear Mask", icon="CLEAR_MASK"
        )
        props.mode = "VALUE"
        props.value = 0

        layout.separator()

        props = layout.operator(
            "sculpt.mask_filter", text="Smooth Mask", icon="PARTICLEBRUSH_SMOOTH"
        )
        props.filter_type = "SMOOTH"

        props = layout.operator(
            "sculpt.mask_filter", text="Sharpen Mask", icon="SHARPEN"
        )
        props.filter_type = "SHARPEN"

        props = layout.operator(
            "sculpt.mask_filter", text="Grow Mask", icon="SELECTMORE"
        )
        props.filter_type = "GROW"

        props = layout.operator(
            "sculpt.mask_filter", text="Shrink Mask", icon="SELECTLESS"
        )
        props.filter_type = "SHRINK"

        props = layout.operator(
            "sculpt.mask_filter", text="Increase Contrast", icon="INC_CONTRAST"
        )
        props.filter_type = "CONTRAST_INCREASE"
        props.auto_iteration_count = False

        props = layout.operator(
            "sculpt.mask_filter", text="Decrease Contrast", icon="DEC_CONTRAST"
        )
        props.filter_type = "CONTRAST_DECREASE"
        props.auto_iteration_count = False

        layout.separator()

        props = layout.operator(
            "sculpt.expand", text="Expand Mask by Topology", icon="MESH_DATA"
        )
        props.target = "MASK"
        props.falloff_type = "GEODESIC"
        props.invert = False
        props.use_auto_mask = False
        props.use_mask_preserve = True

        props = layout.operator(
            "sculpt.expand", text="Expand Mask by Curvature", icon="CURVE_DATA"
        )
        props.target = "MASK"
        props.falloff_type = "NORMALS"
        props.invert = False
        props.use_mask_preserve = True

        layout.separator()

        props = layout.operator(
            "mesh.paint_mask_extract", text="Mask Extract", icon="PACKAGE"
        )

        layout.separator()

        props = layout.operator(
            "mesh.paint_mask_slice", text="Mask Slice", icon="MASK_SLICE"
        )
        props.fill_holes = False
        props.new_object = False
        props = layout.operator(
            "mesh.paint_mask_slice",
            text="Mask Slice and Fill Holes",
            icon="MASK_SLICE_FILL",
        )
        props.new_object = False
        props = layout.operator(
            "mesh.paint_mask_slice",
            text="Mask Slice to New Object",
            icon="MASK_SLICE_NEW",
        )

        layout.separator()

        props = layout.operator(
            "sculpt.mask_from_cavity", text="Mask From Cavity", icon="DIRTY_VERTEX"
        )
        props.settings_source = "OPERATOR"

        props = layout.operator(
            "sculpt.mask_from_boundary", text="Mask from Mesh Boundary"
        )
        props.settings_source = "OPERATOR"
        props.boundary_mode = "MESH"

        props = layout.operator(
            "sculpt.mask_from_boundary", text="Mask from Face Sets Boundary"
        )
        props.settings_source = "OPERATOR"
        props.boundary_mode = "FACE_SETS"

        layout.separator()

        layout.menu("VIEW3D_MT_random_mask", text="Random Mask")

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


# bfa menu
class VIEW3D_MT_mask_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "paint.mask_box_gesture", text="Box Mask", icon="BOX_MASK"
        )
        props.mode = "VALUE"
        props.value = 0

        props = layout.operator(
            "paint.mask_lasso_gesture", text="Lasso Mask", icon="LASSO_MASK"
        )


class VIEW3D_MT_face_sets_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "sculpt.face_set_change_visibility",
            text="Toggle Visibility",
            icon="HIDE_UNSELECTED",
        ).mode = "TOGGLE"

        layout.separator()

        layout.operator(
            "paint.hide_show_all", text="Show All Geometry", icon="HIDE_OFF"
        ).action = "SHOW"
        layout.operator(
            "sculpt.face_set_change_visibility",
            text="Hide Active Face Set",
            icon="HIDE_ON",
        ).mode = "HIDE_ACTIVE"


class VIEW3D_MT_face_sets(Menu):
    bl_label = "Face Sets"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "sculpt.face_sets_create", text="Face Set from Masked", icon="MOD_MASK"
        ).mode = "MASKED"
        layout.operator(
            "sculpt.face_sets_create", text="Face Set from Visible", icon="FILL_MASK"
        ).mode = "VISIBLE"
        layout.operator(
            "sculpt.face_sets_create",
            text="Face Set from Edit Mode Selection",
            icon="EDITMODE_HLT",
        ).mode = "SELECTION"

        layout.separator()

        layout.menu("VIEW3D_MT_face_sets_init", text="Initialize Face Sets")

        layout.separator()

        layout.operator(
            "sculpt.face_set_edit", text="Grow Face Set", icon="SELECTMORE"
        ).mode = "GROW"
        layout.operator(
            "sculpt.face_set_edit", text="Shrink Face Set", icon="SELECTLESS"
        ).mode = "SHRINK"
        props = layout.operator(
            "sculpt.expand", text="Expand Face Set by Topology", icon="FACE_MAPS"
        )
        props.target = "FACE_SETS"
        props.falloff_type = "GEODESIC"
        props.invert = False
        props.use_mask_preserve = False
        props.use_modify_active = False

        props = layout.operator(
            "sculpt.expand", text="Expand Active Face Set", icon="FACE_MAPS_ACTIVE"
        )
        props.target = "FACE_SETS"
        props.falloff_type = "BOUNDARY_FACE_SET"
        props.invert = False
        props.use_mask_preserve = False
        props.use_modify_active = True

        layout.separator()

        layout.operator(
            "mesh.face_set_extract", text="Extract Face Set", icon="SEPARATE"
        )

        layout.separator()

        layout.operator(
            "sculpt.face_sets_randomize_colors", text="Randomize Colors", icon="COLOR"
        )

        layout.separator()

        layout.menu("VIEW3D_MT_face_sets_showhide")

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


class VIEW3D_MT_sculpt_set_pivot(Menu):
    bl_label = "Sculpt Set Pivot"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "sculpt.set_pivot_position", text="Pivot to Origin", icon="PIVOT_TO_ORIGIN"
        )
        props.mode = "ORIGIN"

        props = layout.operator(
            "sculpt.set_pivot_position",
            text="Pivot to Unmasked",
            icon="PIVOT_TO_UNMASKED",
        )
        props.mode = "UNMASKED"

        props = layout.operator(
            "sculpt.set_pivot_position",
            text="Pivot to Mask Border",
            icon="PIVOT_TO_MASKBORDER",
        )
        props.mode = "BORDER"

        props = layout.operator(
            "sculpt.set_pivot_position",
            text="Pivot to Active Vertex",
            icon="PIVOT_TO_ACTIVE_VERT",
        )
        props.mode = "ACTIVE"

        props = layout.operator(
            "sculpt.set_pivot_position",
            text="Pivot to Surface Under Cursor",
            icon="PIVOT_TO_SURFACE",
        )
        props.mode = "SURFACE"


class VIEW3D_MT_face_sets_init(Menu):
    bl_label = "Face Sets Init"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "sculpt.face_sets_init", text="By Loose Parts", icon="SELECT_LOOSE"
        ).mode = "LOOSE_PARTS"
        layout.operator(
            "sculpt.face_sets_init",
            text="By Face Set Boundaries",
            icon="SELECT_BOUNDARY",
        ).mode = "FACE_SET_BOUNDARIES"
        layout.operator(
            "sculpt.face_sets_init", text="By Materials", icon="MATERIAL_DATA"
        ).mode = "MATERIALS"
        layout.operator(
            "sculpt.face_sets_init", text="By Normals", icon="RECALC_NORMALS"
        ).mode = "NORMALS"
        layout.operator(
            "sculpt.face_sets_init", text="By UV Seams", icon="MARK_SEAM"
        ).mode = "UV_SEAMS"
        layout.operator(
            "sculpt.face_sets_init", text="By Edge Creases", icon="CREASE"
        ).mode = "CREASES"
        layout.operator(
            "sculpt.face_sets_init", text="By Edge Bevel Weight", icon="BEVEL"
        ).mode = "BEVEL_WEIGHT"
        layout.operator(
            "sculpt.face_sets_init", text="By Sharp Edges", icon="SELECT_SHARPEDGES"
        ).mode = "SHARP_EDGES"


class VIEW3D_MT_random_mask(Menu):
    bl_label = "Random Mask"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "sculpt.mask_init", text="Per Vertex", icon="SELECT_UNGROUPED_VERTS"
        ).mode = "RANDOM_PER_VERTEX"
        layout.operator(
            "sculpt.mask_init", text="Per Face Set", icon="FACESEL"
        ).mode = "RANDOM_PER_FACE_SET"
        layout.operator(
            "sculpt.mask_init", text="Per Loose Part", icon="SELECT_LOOSE"
        ).mode = "RANDOM_PER_LOOSE_PART"


class VIEW3D_MT_particle(Menu):
    bl_label = "Particle"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        particle_edit = tool_settings.particle_edit

        layout.operator("particle.mirror", icon="TRANSFORM_MIRROR")

        layout.operator("particle.remove_doubles", icon="REMOVE_DOUBLES")

        layout.separator()

        if particle_edit.select_mode == "POINT":
            layout.operator("particle.subdivide", icon="SUBDIVIDE_EDGES")

        layout.operator("particle.unify_length", icon="RULER")
        layout.operator("particle.rekey", icon="KEY_HLT")
        layout.operator("particle.weight_set", icon="MOD_VERTEX_WEIGHT")

        layout.separator()

        layout.menu("VIEW3D_MT_particle_showhide")

        layout.separator()

        layout.operator("particle.delete", icon="DELETE")


class VIEW3D_MT_particle_context_menu(Menu):
    bl_label = "Particle"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        particle_edit = tool_settings.particle_edit

        layout.operator("particle.rekey", icon="KEY_HLT")

        layout.separator()

        layout.operator("particle.delete", icon="DELETE")

        layout.separator()

        layout.operator("particle.remove_doubles", icon="REMOVE_DOUBLES")
        layout.operator("particle.unify_length", icon="RULER")

        if particle_edit.select_mode == "POINT":
            layout.operator("particle.subdivide", icon="SUBDIVIDE_EDGES")

        layout.operator("particle.weight_set", icon="MOD_VERTEX_WEIGHT")

        layout.separator()

        layout.operator("particle.mirror")

        if particle_edit.select_mode == "POINT":
            layout.separator()

            layout.operator(
                "particle.select_all", text="All", icon="SELECT_ALL"
            ).action = "SELECT"
            layout.operator(
                "particle.select_all", text="None", icon="SELECT_NONE"
            ).action = "DESELECT"
            layout.operator(
                "particle.select_all", text="Invert", icon="INVERSE"
            ).action = "INVERT"

            layout.separator()

            layout.operator("particle.select_roots", icon="SELECT_ROOT")
            layout.operator("particle.select_tips", icon="SELECT_TIP")

            layout.separator()

            layout.operator("particle.select_random", icon="RANDOMIZE")

            layout.separator()

            layout.operator("particle.select_more", icon="SELECTMORE")
            layout.operator("particle.select_less", icon="SELECTLESS")

            layout.operator(
                "particle.select_linked", text="Select Linked", icon="LINKED"
            )

        layout.separator()

        layout.menu("VIEW3D_MT_particle_showhide")  # BFA - added to context menu


class VIEW3D_MT_particle_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("particle.reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "particle.hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "particle.hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_pose(Menu):
    bl_label = "Pose"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform_armature")

        layout.menu("VIEW3D_MT_pose_transform")
        layout.menu("VIEW3D_MT_pose_apply")

        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.menu("VIEW3D_MT_object_animation")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_slide")
        layout.menu("VIEW3D_MT_pose_propagate")

        layout.separator()

        layout.operator("pose.copy", icon="COPYDOWN")
        layout.operator("pose.paste", icon="PASTEDOWN").flipped = False
        layout.operator(
            "pose.paste", icon="PASTEFLIPDOWN", text="Paste Pose Flipped"
        ).flipped = True

        layout.separator()

        layout.menu("VIEW3D_MT_pose_motion")

        layout.separator()

        layout.operator(
            "armature.move_to_collection",
            text="Move to Bone Collection",
            icon="GROUP_BONE",
        )  # BFA - added for consistency
        layout.menu("VIEW3D_MT_bone_collections")

        layout.separator()

        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_pose_ik")
        layout.menu("VIEW3D_MT_pose_constraints")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_names")
        layout.operator("pose.quaternions_flip", icon="FLIP")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_showhide")
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")

        layout.separator()
        layout.operator("POSELIB.create_pose_asset")


class VIEW3D_MT_pose_transform(Menu):
    bl_label = "Clear Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.transforms_clear", text="All", icon="CLEAR")
        layout.operator("pose.user_transforms_clear", icon="NODE_TRANSFORM_CLEAR")

        layout.separator()

        layout.operator(
            "pose.loc_clear",
            text="Location",
            text_ctxt=i18n_contexts.default,
            icon="CLEARMOVE",
        )
        layout.operator(
            "pose.rot_clear",
            text="Rotation",
            text_ctxt=i18n_contexts.default,
            icon="CLEARROTATE",
        )
        layout.operator(
            "pose.scale_clear",
            text="Scale",
            text_ctxt=i18n_contexts.default,
            icon="CLEARSCALE",
        )

        layout.separator()

        layout.operator(
            "pose.user_transforms_clear", text="Reset Unkeyed", icon="RESET"
        )


class VIEW3D_MT_pose_slide(Menu):
    bl_label = "In-Betweens"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.blend_with_rest", icon="PUSH_POSE")
        layout.operator("pose.push", icon="POSE_FROM_BREAKDOWN")
        layout.operator("pose.relax", icon="POSE_RELAX_TO_BREAKDOWN")
        layout.operator("pose.breakdown", icon="BREAKDOWNER_POSE")
        layout.operator("pose.blend_to_neighbor", icon="BLEND_TO_NEIGHBOUR")


class VIEW3D_MT_pose_propagate(Menu):
    bl_label = "Propagate"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "pose.propagate", text="To Next Keyframe", icon="PROPAGATE_NEXT"
        ).mode = "NEXT_KEY"
        layout.operator(
            "pose.propagate",
            text="To Last Keyframe (Make Cyclic)",
            icon="PROPAGATE_PREVIOUS",
        ).mode = "LAST_KEY"

        layout.separator()

        layout.operator(
            "pose.propagate", text="On Selected Keyframes", icon="PROPAGATE_SELECTED"
        ).mode = "SELECTED_KEYS"

        layout.separator()

        layout.operator(
            "pose.propagate", text="On Selected Markers", icon="PROPAGATE_MARKER"
        ).mode = "SELECTED_MARKERS"


class VIEW3D_MT_pose_motion(Menu):
    bl_label = "Motion Paths"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "pose.paths_calculate", text="Calculate", icon="MOTIONPATHS_CALCULATE"
        )
        layout.operator("pose.paths_clear", text="Clear", icon="MOTIONPATHS_CLEAR")
        layout.operator(
            "pose.paths_update",
            text="Update Armature Motion Paths",
            icon="MOTIONPATHS_UPDATE",
        )
        layout.operator(
            "object.paths_update_visible",
            text="Update All Motion Paths",
            icon="MOTIONPATHS_UPDATE_ALL",
        )


class VIEW3D_MT_bone_collections(Menu):
    bl_label = "Bone Collections"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if not (ob and ob.type == "ARMATURE"):
            return False
        if not ob.data.is_editable:
            return False
        return True

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "armature.assign_to_collection", text="Add", icon="COLLECTION_BONE_ADD"
        )  # BFA - shortned label

        layout.separator()

        layout.operator("armature.collection_show_all", icon="SHOW_UNSELECTED")
        props = layout.operator(
            "armature.collection_create_and_assign",  # BFA - shortned label
            text="Assign to New",
            icon="COLLECTION_BONE_NEW",
        )
        props.name = "New Collection"


class VIEW3D_MT_pose_ik(Menu):
    bl_label = "Inverse Kinematics"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.ik_add", icon="ADD_IK")
        layout.operator("pose.ik_clear", icon="CLEAR_IK")


class VIEW3D_MT_pose_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "pose.constraint_add_with_targets",
            text="Add (with Targets)",
            icon="CONSTRAINT_DATA",
        )
        layout.operator("pose.constraints_copy", icon="COPYDOWN")
        layout.operator("pose.constraints_clear", icon="CLEAR_CONSTRAINT")


class VIEW3D_MT_pose_names(Menu):
    bl_label = "Names"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator(
            "pose.autoside_names", text="Auto-Name Left/Right", icon="RENAME_X"
        ).axis = "XAXIS"
        layout.operator(
            "pose.autoside_names", text="Auto-Name Front/Back", icon="RENAME_Y"
        ).axis = "YAXIS"
        layout.operator(
            "pose.autoside_names", text="Auto-Name Top/Bottom", icon="RENAME_Z"
        ).axis = "ZAXIS"
        layout.operator("pose.flip_names", icon="FLIP")


class VIEW3D_MT_pose_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "pose.hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "pose.hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_pose_apply(Menu):
    bl_label = "Apply"

    def draw(self, _context):
        layout = self.layout

        layout.operator("pose.armature_apply", icon="MOD_ARMATURE")
        layout.operator(
            "pose.armature_apply",
            text="Apply Selected as Rest Pose",
            icon="MOD_ARMATURE_SELECTED",
        ).selected = True
        layout.operator("pose.visual_transform_apply", icon="APPLYMOVE")

        layout.separator()

        props = layout.operator("object.assign_property_defaults", icon="ASSIGN")
        props.process_bones = True


class VIEW3D_MT_pose_context_menu(Menu):
    bl_label = "Pose"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator(
            "anim.keyframe_insert", text="Insert Keyframe", icon="KEYFRAMES_INSERT"
        )
        layout.operator(
            "anim.keyframe_insert_menu",
            text="Insert Keyframe with Keying Set",
            icon="KEYFRAMES_INSERT",
        ).always_prompt = True

        layout.separator()

        layout.operator("pose.copy", icon="COPYDOWN")
        layout.operator("pose.paste", icon="PASTEDOWN").flipped = False
        layout.operator(
            "pose.paste", icon="PASTEFLIPDOWN", text="Paste X-Flipped Pose"
        ).flipped = True

        layout.separator()

        props = layout.operator(
            "wm.call_panel", text="Rename Active Bone...", icon="RENAME"
        )
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.separator()

        layout.operator("pose.push", icon="PUSH_POSE")
        layout.operator("pose.relax", icon="RELAX_POSE")
        layout.operator("pose.breakdown", icon="BREAKDOWNER_POSE")
        layout.operator("pose.blend_to_neighbor", icon="BLEND_TO_NEIGHBOUR")

        layout.separator()

        layout.operator(
            "pose.paths_calculate",
            text="Calculate Motion Paths",
            icon="MOTIONPATHS_CALCULATE",
        )
        layout.operator(
            "pose.paths_clear", text="Clear Motion Paths", icon="MOTIONPATHS_CLEAR"
        )
        layout.operator(
            "pose.paths_update",
            text="Update Armature Motion Paths",
            icon="MOTIONPATHS_UPDATE",
        )

        layout.separator()

        layout.operator(
            "armature.move_to_collection",
            text="Move to Bone Collection",
            icon="GROUP_BONE",
        )  # BFA - added to context menu

        layout.separator()

        layout.operator("pose.reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "pose.hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        # BFA - added for consistentcy with header
        layout.operator(
            "pose.hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True

        layout.separator()

        layout.operator("pose.user_transforms_clear", icon="NODE_TRANSFORM_CLEAR")


class BoneOptions:
    def draw(self, context):
        layout = self.layout

        options = [
            "show_wire",
            "use_deform",
            "use_envelope_multiply",
            "use_inherit_rotation",
        ]

        if context.mode == "EDIT_ARMATURE":
            bone_props = bpy.types.EditBone.bl_rna.properties
            data_path_iter = "selected_bones"
            opt_suffix = ""
            options.append("lock")
        else:  # pose-mode
            bone_props = bpy.types.Bone.bl_rna.properties
            data_path_iter = "selected_pose_bones"
            opt_suffix = "bone."

        for opt in options:
            props = layout.operator(
                "wm.context_collection_boolean_set",
                text=bone_props[opt].name,
                text_ctxt=i18n_contexts.default,
            )
            props.data_path_iter = data_path_iter
            props.data_path_item = opt_suffix + opt
            props.type = self.type


class VIEW3D_MT_bone_options_toggle(Menu, BoneOptions):
    bl_label = "Toggle Bone Options"
    type = "TOGGLE"


class VIEW3D_MT_bone_options_enable(Menu, BoneOptions):
    bl_label = "Enable Bone Options"
    type = "ENABLE"


class VIEW3D_MT_bone_options_disable(Menu, BoneOptions):
    bl_label = "Disable Bone Options"
    type = "DISABLE"


# ********** Edit Menus, suffix from ob.type **********


class VIEW3D_MT_edit_mesh(Menu):
    bl_label = "Mesh"

    def draw(self, _context):
        layout = self.layout

        with_bullet = bpy.app.build_options.bullet

        layout.menu("VIEW3D_MT_edit_mesh_legacy")  # bfa menu

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mesh.duplicate_move", text="Duplicate", icon="DUPLICATE")
        layout.menu("VIEW3D_MT_edit_mesh_extrude")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_merge", text="Merge")
        layout.menu("VIEW3D_MT_edit_mesh_split", text="Split")
        layout.operator_menu_enum("mesh.separate", "type")

        layout.separator()

        # layout.operator("mesh.bisect") # BFA - moved to legacy
        layout.operator("mesh.knife_project", icon="KNIFE_PROJECT")
        # layout.operator("mesh.knife_tool") # BFA - moved to legacy

        if with_bullet:
            layout.operator("mesh.convex_hull", icon="CONVEXHULL")

        layout.separator()

        layout.operator("mesh.symmetrize", icon="SYMMETRIZE", text="Symmetrize")
        layout.operator("mesh.symmetry_snap", icon="SNAP_SYMMETRY")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_normals")
        layout.menu("VIEW3D_MT_edit_mesh_shading")
        layout.menu("VIEW3D_MT_edit_mesh_weights")
        layout.operator("mesh.attribute_set", icon="NODE_ATTRIBUTE")
        layout.menu("VIEW3D_MT_edit_mesh_sort_elements")  # bfa menu
        layout.menu("VIEW3D_MT_subdivision_set")  # bfa menu

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_showhide")
        layout.menu("VIEW3D_MT_edit_mesh_clean")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_delete")
        layout.menu("VIEW3D_MT_edit_mesh_dissolve")  # bfa menu
        layout.menu("VIEW3D_MT_edit_mesh_select_mode")


# bfa menu
class VIEW3D_MT_edit_mesh_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.bisect", text="Bisect", icon="BISECT")
        layout.operator("mesh.knife_tool", text="Knife", icon="KNIFE")


# bfa menu
class VIEW3D_MT_edit_mesh_sort_elements(Menu):
    bl_label = "Sort Elements"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "mesh.sort_elements", text="View Z Axis", icon="Z_ICON"
        ).type = "VIEW_ZAXIS"
        layout.operator(
            "mesh.sort_elements", text="View X Axis", icon="X_ICON"
        ).type = "VIEW_XAXIS"
        layout.operator(
            "mesh.sort_elements", text="Cursor Distance", icon="CURSOR"
        ).type = "CURSOR_DISTANCE"
        layout.operator(
            "mesh.sort_elements", text="Material", icon="MATERIAL"
        ).type = "MATERIAL"
        layout.operator(
            "mesh.sort_elements", text="Selected", icon="RESTRICT_SELECT_OFF"
        ).type = "SELECTED"
        layout.operator(
            "mesh.sort_elements", text="Randomize", icon="RANDOMIZE"
        ).type = "RANDOMIZE"
        layout.operator(
            "mesh.sort_elements", text="Reverse", icon="SWITCH_DIRECTION"
        ).type = "REVERSE"

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


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

        is_vert_mode, is_edge_mode, is_face_mode = (
            context.tool_settings.mesh_select_mode
        )
        selected_verts_len, selected_edges_len, selected_faces_len = (
            count_selected_items_for_objects_in_mode()
        )

        del count_selected_items_for_objects_in_mode

        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = "INVOKE_REGION_WIN"

        # If nothing is selected
        # (disabled for now until it can be made more useful).
        """
        # If nothing is selected
        if not (selected_verts_len or selected_edges_len or selected_faces_len):
            layout.menu("VIEW3D_MT_mesh_add", text="Add", text_ctxt=i18n_contexts.operator_default)

            return
        """

        # Else something is selected

        row = layout.row()

        if is_vert_mode:
            col = row.column(align=True)

            col.label(text="Vertex", icon="VERTEXSEL")
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide", icon="SUBDIVIDE_EDGES")

            col.separator()

            col.operator(
                "mesh.extrude_vertices_move",
                text="Extrude Vertices",
                icon="EXTRUDE_REGION",
            )

            col.separator()  # BFA - Seperated Legacy operator to be in own group like in the Legacy Menu, also consistent order

            col.operator(
                "mesh.bevel", text="Bevel Vertices", icon="BEVEL"
            ).affect = "VERTICES"

            col.separator()  # BFA - Seperated Legacy operator to be in own group like in the Legacy Menu, also consistent order

            if selected_verts_len > 1:
                col.separator()
                col.operator(
                    "mesh.edge_face_add", text="Make Edge/Face", icon="MAKE_EDGEFACE"
                )
                col.operator(
                    "mesh.vert_connect_path",
                    text="Connect Vertex Path",
                    icon="VERTEXCONNECTPATH",
                )
                col.operator(
                    "mesh.vert_connect",
                    text="Connect Vertex Pairs",
                    icon="VERTEXCONNECT",
                )

            col.separator()

            # Deform Operators
            col.operator("transform.push_pull", text="Push/Pull", icon="PUSH_PULL")
            col.operator(
                "transform.shrink_fatten", text="Shrink Fatten", icon="SHRINK_FATTEN"
            )
            col.operator("transform.shear", text="Shear", icon="SHEAR")
            col.operator_context = "EXEC_REGION_WIN"
            col.operator(
                "transform.vertex_random", text="Randomize Vertices", icon="RANDOMIZE"
            )
            col.operator_context = "INVOKE_REGION_WIN"
            col.operator(
                "mesh.vertices_smooth_laplacian",
                text="Smooth Laplacian",
                icon="SMOOTH_LAPLACIAN",
            )

            col.separator()

            col.menu("VIEW3D_MT_snap", text="Snap Vertices")
            col.operator(
                "transform.mirror", text="Mirror Vertices", icon="TRANSFORM_MIRROR"
            )

            col.separator()

            col.operator("transform.vert_crease", icon="VERTEX_CREASE")

            col.separator()

            # Removal Operators
            if selected_verts_len > 1:
                col.menu("VIEW3D_MT_edit_mesh_merge", text="Merge Vertices")
            col.operator("mesh.split", icon="SPLIT")
            col.operator_menu_enum("mesh.separate", "type")
            col.operator("mesh.dissolve_verts", icon="DISSOLVE_VERTS")
            col.operator(
                "mesh.delete", text="Delete Vertices", icon="DELETE"
            ).type = "VERT"

        if is_edge_mode:
            col = row.column(align=True)
            col.label(text="Edge", icon="EDGESEL")
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide", icon="SUBDIVIDE_EDGES")

            col.separator()

            col.operator(
                "mesh.extrude_edges_move", text="Extrude Edges", icon="EXTRUDE_REGION"
            )

            col.separator()  # BFA-Draise - Seperated Legacy operator to be in own group like in the Legacy Menu, also consistent order

            col.operator(
                "mesh.bevel", text="Bevel Edges", icon="BEVEL"
            ).affect = "EDGES"

            col.separator()  # BFA-Draise - Seperated Legacy operator to be in own group like in the Legacy Menu, also consistent order

            if (
                selected_edges_len >= 1
            ):  # BFA-Draise - Changed order of Make Edge before Bridge Edge Loop for consistency with Vertex Context
                col.operator(
                    "mesh.edge_face_add", text="Make Edge/Face", icon="MAKE_EDGEFACE"
                )
            if selected_edges_len >= 2:
                col.operator("mesh.bridge_edge_loops", icon="BRIDGE_EDGELOOPS")
            if selected_edges_len >= 2:
                col.operator("mesh.fill", icon="FILL")

            col.separator()

            col.operator("mesh.loopcut_slide", icon="LOOP_CUT_AND_SLIDE")
            col.operator("mesh.offset_edge_loops_slide", icon="SLIDE_EDGE")

            col.separator()

            col.operator("mesh.knife_tool", icon="KNIFE")

            col.separator()

            # Deform Operators
            col.operator(
                "mesh.edge_rotate", text="Rotate Edge CW", icon="ROTATECW"
            ).use_ccw = False
            col.operator("mesh.edge_split", icon="SPLITEDGE")

            col.separator()

            # Edge Flags
            col.operator("transform.edge_crease", icon="CREASE")
            col.operator("transform.edge_bevelweight", icon="BEVEL")

            col.separator()

            col.operator("mesh.mark_sharp", icon="MARKSHARPEDGES")
            col.operator(
                "mesh.mark_sharp", text="Clear Sharp", icon="CLEARSHARPEDGES"
            ).clear = True
            col.operator("mesh.set_sharpness_by_angle", icon="MARKSHARPANGLE")

            if with_freestyle:
                col.separator()

                col.operator(
                    "mesh.mark_freestyle_edge", icon="MARK_FS_EDGE"
                ).clear = False
                col.operator(
                    "mesh.mark_freestyle_edge",
                    text="Clear Freestyle Edge",
                    icon="CLEAR_FS_EDGE",
                ).clear = True

            col.separator()

            # Removal Operators
            col.operator("mesh.unsubdivide", icon="UNSUBDIVIDE")
            col.operator("mesh.split", icon="SPLIT")
            col.operator_menu_enum("mesh.separate", "type")
            col.operator("mesh.dissolve_edges", icon="DISSOLVE_EDGES")
            col.operator(
                "mesh.delete", text="Delete Edges", icon="DELETE"
            ).type = "EDGE"

        if is_face_mode:
            col = row.column(align=True)

            col.label(text="Face", icon="FACESEL")
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide", icon="SUBDIVIDE_EDGES")

            col.separator()

            col.operator(
                "view3d.edit_mesh_extrude_move_normal",
                text="Extrude Faces",
                icon="EXTRUDE_REGION",
            )
            col.operator(
                "view3d.edit_mesh_extrude_move_shrink_fatten",
                text="Extrude Faces Along Normals",
                icon="EXTRUDE_REGION",
            )
            col.operator(
                "mesh.extrude_faces_move",
                text="Extrude Individual Faces",
                icon="EXTRUDE_REGION",
            )

            col.separator()  # BFA-Draise - Legacy Operator Group

            # BFA-Draise - Legacy Operator Added to own group with consistent order
            col.operator("mesh.inset", icon="INSET_FACES")

            col.separator()

            col.separator()  # BFA-Draise - Seperated extrude operators to be in own group for consistency

            if selected_faces_len >= 2:
                col.operator(
                    "mesh.bridge_edge_loops",
                    text="Bridge Faces",
                    icon="BRIDGE_EDGELOOPS",
                )

            # BFA-Draise - changed order after "Poke" for consistency to other menus
            col.operator("mesh.poke", icon="POKEFACES")

            # Modify Operators
            col.menu("VIEW3D_MT_uv_map", text="UV Unwrap Faces")

            col.separator()

            props = col.operator("mesh.quads_convert_to_tris", icon="TRIANGULATE")
            props.quad_method = props.ngon_method = "BEAUTY"
            col.operator("mesh.tris_convert_to_quads", icon="TRISTOQUADS")

            col.separator()

            col.operator("mesh.faces_shade_smooth", icon="SHADING_SMOOTH")
            col.operator("mesh.faces_shade_flat", icon="SHADING_FLAT")

            col.separator()

            # Removal Operators
            col.operator("mesh.unsubdivide", icon="UNSUBDIVIDE")
            col.operator("mesh.split", icon="SPLIT")
            col.operator_menu_enum("mesh.separate", "type")
            col.operator("mesh.dissolve_faces", icon="DISSOLVE_FACES")
            col.operator(
                "mesh.delete", text="Delete Faces", icon="DELETE"
            ).type = "FACE"

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_showhide")  # BFA - added to context menu


class VIEW3D_MT_edit_mesh_select_mode(Menu):
    bl_label = "Mesh Select Mode"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator(
            "mesh.select_mode", text="Vertex", icon="VERTEXSEL"
        ).type = "VERT"
        layout.operator("mesh.select_mode", text="Edge", icon="EDGESEL").type = "EDGE"
        layout.operator("mesh.select_mode", text="Face", icon="FACESEL").type = "FACE"


# bfa operator for separated tooltip
class VIEW3D_MT_edit_mesh_extrude_dupli(bpy.types.Operator):
    """Duplicate or Extrude to Cursor\nCreates a slightly rotated copy of the current mesh selection\nThe tool can also extrude the selected geometry, dependant of the selection\nHotkey tool!"""  # BFA - blender will use this as a tooltip for menu items and buttons.

    bl_idname = "mesh.dupli_extrude_cursor_norotate"  # unique identifier for buttons and menu items to reference.
    bl_label = "Duplicate or Extrude to Cursor"  # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}  # enable undo for the operator.

    def execute(
        self, context
    ):  # execute() is called by blender when running the operator.
        bpy.ops.mesh.dupli_extrude_cursor("INVOKE_DEFAULT", rotate_source=False)
        return {"FINISHED"}


# bfa operator for separated tooltip
class VIEW3D_MT_edit_mesh_extrude_dupli_rotate(bpy.types.Operator):
    """Duplicate or Extrude to Cursor Rotated\nCreates a slightly rotated copy of the current mesh selection, and rotates the source slightly\nThe tool can also extrude the selected geometry, dependant of the selection\nHotkey tool!"""  # BFA-  blender will use this as a tooltip for menu items and buttons.

    bl_idname = "mesh.dupli_extrude_cursor_rotate"  # unique identifier for buttons and menu items to reference.
    bl_label = (
        "Duplicate or Extrude to Cursor Rotated"  # display name in the interface.
    )
    bl_options = {"REGISTER", "UNDO"}  # enable undo for the operator.

    def execute(
        self, context
    ):  # execute() is called by blender when running the operator.
        bpy.ops.mesh.dupli_extrude_cursor("INVOKE_DEFAULT", rotate_source=True)
        return {"FINISHED"}


class VIEW3D_MT_edit_mesh_extrude(Menu):
    bl_label = "Extrude"

    def draw(self, context):
        from math import pi

        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"

        tool_settings = context.tool_settings
        select_mode = tool_settings.mesh_select_mode
        ob = context.object
        mesh = ob.data

        if mesh.total_face_sel:
            layout.operator(
                "view3d.edit_mesh_extrude_move_normal",
                text="Extrude Faces",
                icon="EXTRUDE_REGION",
            )
            layout.operator(
                "view3d.edit_mesh_extrude_move_shrink_fatten",
                text="Extrude Faces Along Normals",
                icon="EXTRUDE_REGION",
            )
            layout.operator(
                "mesh.extrude_faces_move",
                text="Extrude Individual Faces",
                icon="EXTRUDE_REGION",
            )
            layout.operator(
                "view3d.edit_mesh_extrude_manifold_normal",
                text="Extrude Manifold",
                icon="EXTRUDE_REGION",
            )

        if mesh.total_edge_sel and (select_mode[0] or select_mode[1]):
            layout.operator(
                "mesh.extrude_edges_move", text="Extrude Edges", icon="EXTRUDE_REGION"
            )

        if mesh.total_vert_sel and select_mode[0]:
            layout.operator(
                "mesh.extrude_vertices_move",
                text="Extrude Vertices",
                icon="EXTRUDE_REGION",
            )

        layout.separator()

        layout.operator("mesh.extrude_repeat", icon="REPEAT")
        layout.operator("mesh.spin", icon="SPIN").angle = pi * 2
        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Extrude")


class VIEW3D_MT_edit_mesh_vertices(Menu):
    bl_label = "Vertex"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"

        layout.menu("VIEW3D_MT_edit_mesh_vertices_legacy")  # bfa menu
        layout.operator(
            "mesh.dupli_extrude_cursor", icon="EXTRUDE_REGION"
        ).rotate_source = True

        layout.separator()

        layout.operator(
            "mesh.edge_face_add", text="Make Edge/Face", icon="MAKE_EDGEFACE"
        )
        layout.operator(
            "mesh.vert_connect_path",
            text="Connect Vertex Path",
            icon="VERTEXCONNECTPATH",
        )
        layout.operator(
            "mesh.vert_connect", text="Connect Vertex Pairs", icon="VERTEXCONNECT"
        )

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator(
            "mesh.vertices_smooth_laplacian",
            text="Smooth Laplacian",
            icon="SMOOTH_LAPLACIAN",
        )
        layout.operator_context = "INVOKE_REGION_WIN"

        layout.separator()

        layout.operator("transform.vert_crease", icon="VERTEX_CREASE")

        layout.separator()

        layout.operator("mesh.blend_from_shape", icon="BLENDFROMSHAPE")
        layout.operator(
            "mesh.shape_propagate_to_all",
            text="Propagate to Shapes",
            icon="SHAPEPROPAGATE",
        )

        layout.separator()

        layout.menu("VIEW3D_MT_vertex_group")
        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.operator("object.vertex_parent_set", icon="VERTEX_PARENT")


# bfa menu
class VIEW3D_MT_edit_mesh_vertices_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator(
            "mesh.bevel", text="Bevel Vertices", icon="BEVEL"
        ).affect = "VERTICES"

        layout.separator()

        props = layout.operator("mesh.rip_move", text="Rip Vertices", icon="RIP")
        props.MESH_OT_rip.use_fill = False
        props = layout.operator(
            "mesh.rip_move", text="Rip Vertices and Fill", icon="RIP_FILL"
        )
        props.MESH_OT_rip.use_fill = True
        layout.operator(
            "mesh.rip_edge_move", text="Rip Vertices and Extend", icon="EXTEND_VERTICES"
        )

        layout.separator()

        layout.operator(
            "transform.vert_slide", text="Slide Vertices", icon="SLIDE_VERTEX"
        )
        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator(
            "mesh.vertices_smooth", text="Smooth Vertices", icon="SMOOTH_VERTEX"
        ).factor = 0.5
        layout.operator_context = "INVOKE_REGION_WIN"

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


class VIEW3D_MT_edit_mesh_edges(Menu):
    bl_label = "Edge"

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.menu("VIEW3D_MT_edit_mesh_edges_legacy")  # bfa menu

        layout.operator("mesh.bridge_edge_loops", icon="BRIDGE_EDGELOOPS")
        layout.operator("mesh.screw", icon="MOD_SCREW")

        layout.separator()

        layout.operator("mesh.subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator("mesh.subdivide_edgering", icon="SUBDIV_EDGERING")
        layout.operator("mesh.unsubdivide", icon="UNSUBDIVIDE")

        layout.separator()

        layout.operator(
            "mesh.edge_rotate", text="Rotate Edge CW", icon="ROTATECW"
        ).use_ccw = False
        layout.operator(
            "mesh.edge_rotate", text="Rotate Edge CCW", icon="ROTATECCW"
        ).use_ccw = True

        layout.separator()

        layout.operator("transform.edge_crease", icon="CREASE")
        layout.operator("transform.edge_bevelweight", icon="BEVEL")

        layout.separator()

        layout.operator("mesh.mark_sharp", icon="MARKSHARPEDGES")
        layout.operator(
            "mesh.mark_sharp", text="Clear Sharp", icon="CLEARSHARPEDGES"
        ).clear = True

        layout.operator(
            "mesh.mark_sharp", text="Mark Sharp from Vertices", icon="MARKSHARPVERTS"
        ).use_verts = True
        props = layout.operator(
            "mesh.mark_sharp", text="Clear Sharp from Vertices", icon="CLEARSHARPVERTS"
        )
        props.use_verts = True
        props.clear = True

        layout.operator("mesh.set_sharpness_by_angle", icon="MARKSHARPANGLE")

        if with_freestyle:
            layout.separator()

            layout.operator(
                "mesh.mark_freestyle_edge", icon="MARK_FS_EDGE"
            ).clear = False
            layout.operator(
                "mesh.mark_freestyle_edge",
                text="Clear Freestyle Edge",
                icon="CLEAR_FS_EDGE",
            ).clear = True


# bfa menu
class VIEW3D_MT_edit_mesh_edges_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.bevel", text="Bevel Edges", icon="BEVEL").affect = "EDGES"

        layout.separator()

        layout.operator("transform.edge_slide", icon="SLIDE_EDGE")
        props = layout.operator("mesh.loopcut_slide", icon="LOOP_CUT_AND_SLIDE")
        props.TRANSFORM_OT_edge_slide.release_confirm = False
        layout.operator("mesh.offset_edge_loops_slide", icon="OFFSET_EDGE_SLIDE")

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


class VIEW3D_MT_edit_mesh_faces_data(Menu):
    bl_label = "Face Data"

    def draw(self, _context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator("mesh.colors_rotate", icon="ROTATE_COLORS")
        layout.operator("mesh.colors_reverse", icon="REVERSE_COLORS")

        layout.separator()

        layout.operator("mesh.uvs_rotate", icon="ROTATE_UVS")
        layout.operator("mesh.uvs_reverse", icon="REVERSE_UVS")

        layout.separator()

        layout.operator("mesh.flip_quad_tessellation", icon="FLIP")

        if with_freestyle:
            layout.separator()
            layout.operator("mesh.mark_freestyle_face", icon="MARKFSFACE").clear = False
            layout.operator(
                "mesh.mark_freestyle_face",
                text="Clear Freestyle Face",
                icon="CLEARFSFACE",
            ).clear = True
        layout.template_node_operator_asset_menu_items(catalog_path="Face/Face Data")


class VIEW3D_MT_edit_mesh_faces(Menu):
    bl_label = "Face"
    bl_idname = "VIEW3D_MT_edit_mesh_faces"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.menu("VIEW3D_MT_edit_mesh_faces_legacy")  # bfa menu

        layout.operator("mesh.poke", icon="POKEFACES")
        layout.operator(
            "view3d.edit_mesh_extrude_move_normal",
            text="Extrude Faces",
            icon="EXTRUDE_REGION",
        )
        layout.operator(
            "view3d.edit_mesh_extrude_move_shrink_fatten",
            text="Extrude Faces Along Normals",
            icon="EXTRUDE_REGION",
        )
        layout.operator(
            "mesh.extrude_faces_move",
            text="Extrude Individual Faces",
            icon="EXTRUDE_REGION",
        )

        layout.separator()

        props = layout.operator("mesh.quads_convert_to_tris", icon="TRIANGULATE")
        props.quad_method = props.ngon_method = "BEAUTY"
        layout.operator("mesh.tris_convert_to_quads", icon="TRISTOQUADS")
        layout.operator("mesh.solidify", text="Solidify Faces", icon="SOLIDIFY")
        layout.operator("mesh.wireframe", icon="WIREFRAME")

        layout.separator()

        layout.operator("mesh.fill", icon="FILL")
        layout.operator("mesh.fill_grid", icon="GRIDFILL")
        layout.operator("mesh.beautify_fill", icon="BEAUTIFY")

        layout.separator()

        layout.operator("mesh.intersect", icon="INTERSECT")
        layout.operator("mesh.intersect_boolean", icon="BOOLEAN_INTERSECT")

        layout.separator()

        layout.operator("mesh.face_split_by_edges", icon="SPLITBYEDGES")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_faces_data")

        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


# bfa menu
class VIEW3D_MT_edit_mesh_faces_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, context):
        # bfa - checking if in edit mode and in wich select mode we are.
        # We need to check for all three select modes, or the menu remains empty.
        # See also the specials menu
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

        is_vert_mode, is_edge_mode, is_face_mode = (
            context.tool_settings.mesh_select_mode
        )
        selected_verts_len, selected_edges_len, selected_faces_len = (
            count_selected_items_for_objects_in_mode()
        )

        del count_selected_items_for_objects_in_mode

        layout = self.layout

        layout.operator("mesh.inset", icon="INSET_FACES")

        # bfa - we need the check, or BFA will crash at this operator
        if selected_faces_len >= 2:
            layout.operator(
                "mesh.bridge_edge_loops", text="Bridge Faces", icon="BRIDGE_EDGELOOPS"
            )


class VIEW3D_MT_edit_mesh_normals_select_strength(Menu):
    bl_label = "Select by Face Strength"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "mesh.mod_weighted_strength", text="Weak", icon="FACESEL"
        )
        props.set = False
        props.face_strength = "WEAK"

        props = layout.operator(
            "mesh.mod_weighted_strength", text="Medium", icon="FACESEL"
        )
        props.set = False
        props.face_strength = "MEDIUM"

        props = layout.operator(
            "mesh.mod_weighted_strength", text="Strong", icon="FACESEL"
        )
        props.set = False
        props.face_strength = "STRONG"


class VIEW3D_MT_edit_mesh_normals_set_strength(Menu):
    bl_label = "Set Face Strength"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator(
            "mesh.mod_weighted_strength", text="Weak", icon="NORMAL_SETSTRENGTH"
        )
        props.set = True
        props.face_strength = "WEAK"

        props = layout.operator(
            "mesh.mod_weighted_strength", text="Medium", icon="NORMAL_SETSTRENGTH"
        )
        props.set = True
        props.face_strength = "MEDIUM"

        props = layout.operator(
            "mesh.mod_weighted_strength", text="Strong", icon="NORMAL_SETSTRENGTH"
        )
        props.set = True
        props.face_strength = "STRONG"


class VIEW3D_MT_edit_mesh_normals_average(Menu):
    bl_label = "Average"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "mesh.average_normals", text="Custom Normal", icon="NORMAL_AVERAGE"
        ).average_type = "CUSTOM_NORMAL"
        layout.operator(
            "mesh.average_normals", text="Face Area", icon="NORMAL_AVERAGE"
        ).average_type = "FACE_AREA"
        layout.operator(
            "mesh.average_normals", text="Corner Angle", icon="NORMAL_AVERAGE"
        ).average_type = "CORNER_ANGLE"


class VIEW3D_MT_edit_mesh_normals(Menu):
    bl_label = "Normals"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "mesh.normals_make_consistent",
            text="Recalculate Outside",
            icon="RECALC_NORMALS",
        ).inside = False
        layout.operator(
            "mesh.normals_make_consistent",
            text="Recalculate Inside",
            icon="RECALC_NORMALS_INSIDE",
        ).inside = True
        layout.operator("mesh.flip_normals", text="Flip", icon="FLIP_NORMALS")

        layout.separator()

        layout.operator(
            "mesh.set_normals_from_faces", text="Set from Faces", icon="SET_FROM_FACES"
        )

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("transform.rotate_normal", text="Rotate", icon="NORMAL_ROTATE")
        layout.operator(
            "mesh.point_normals", text="Point normals to target", icon="NORMAL_TARGET"
        )

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("mesh.merge_normals", text="Merge", icon="MERGE")
        layout.operator("mesh.split_normals", text="Split", icon="SPLIT")
        layout.menu(
            "VIEW3D_MT_edit_mesh_normals_average",
            text="Average",
            text_ctxt=i18n_contexts.id_mesh,
        )

        layout.separator()

        layout.operator(
            "mesh.normals_tools", text="Copy Vectors", icon="COPYDOWN"
        ).mode = "COPY"
        layout.operator(
            "mesh.normals_tools", text="Paste Vectors", icon="PASTEDOWN"
        ).mode = "PASTE"

        layout.operator(
            "mesh.smooth_normals", text="Smooth Vectors", icon="NORMAL_SMOOTH"
        )
        layout.operator(
            "mesh.normals_tools", text="Reset Vectors", icon="RESET"
        ).mode = "RESET"

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_normals_select_strength", icon="HAND")
        layout.menu("VIEW3D_MT_edit_mesh_normals_set_strength", icon="MESH_PLANE")
        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Normals")


class VIEW3D_MT_edit_mesh_shading(Menu):
    bl_label = "Shading"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.faces_shade_smooth", icon="SHADING_SMOOTH")
        layout.operator("mesh.faces_shade_flat", icon="SHADING_FLAT")

        layout.separator()

        layout.operator(
            "mesh.mark_sharp", text="Smooth Edges", icon="SHADING_EDGE_SMOOTH"
        ).clear = True
        layout.operator(
            "mesh.mark_sharp", text="Sharp Edges", icon="SHADING_EDGE_SHARP"
        )

        layout.separator()

        props = layout.operator(
            "mesh.mark_sharp", text="Smooth Vertices", icon="SHADING_VERT_SMOOTH"
        )
        props.use_verts = True
        props.clear = True

        layout.operator(
            "mesh.mark_sharp", text="Sharp Vertices", icon="SHADING_VERT_SHARP"
        ).use_verts = True
        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Shading")


class VIEW3D_MT_edit_mesh_weights(Menu):
    bl_label = "Weights"

    def draw(self, _context):
        layout = self.layout
        VIEW3D_MT_paint_weight.draw_generic(layout, is_editmode=True)
        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Weights")


class VIEW3D_MT_edit_mesh_clean(Menu):
    bl_label = "Clean Up"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.delete_loose", icon="DELETE")

        layout.separator()

        layout.operator("mesh.decimate", icon="DECIMATE")
        layout.operator("mesh.dissolve_degenerate", icon="DEGENERATE_DISSOLVE")
        layout.operator("mesh.dissolve_limited", icon="DISSOLVE_LIMITED")
        layout.operator("mesh.face_make_planar", icon="MAKE_PLANAR")

        layout.separator()

        layout.operator("mesh.vert_connect_nonplanar", icon="SPLIT_NONPLANAR")
        layout.operator("mesh.vert_connect_concave", icon="SPLIT_CONCAVE")
        layout.operator("mesh.fill_holes", icon="FILL_HOLE")

        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Clean Up")


class VIEW3D_MT_edit_mesh_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("mesh.delete", "type")

        layout.separator()

        layout.operator("mesh.delete_edgeloop", text="Edge Loops", icon="DELETE")


# bfa menu
class VIEW3D_MT_edit_mesh_dissolve(Menu):
    bl_label = "Dissolve"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.dissolve_verts", icon="DISSOLVE_VERTS")
        layout.operator("mesh.dissolve_edges", icon="DISSOLVE_EDGES")
        layout.operator("mesh.dissolve_faces", icon="DISSOLVE_FACES")

        layout.separator()

        layout.operator("mesh.dissolve_limited", icon="DISSOLVE_LIMITED")
        layout.operator("mesh.dissolve_mode", icon="DISSOLVE_SELECTION")

        layout.separator()

        layout.operator("mesh.edge_collapse", icon="EDGE_COLLAPSE")

        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Delete")


class VIEW3D_MT_edit_mesh_merge(Menu):
    bl_label = "Merge"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("mesh.merge", "type")

        layout.separator()

        layout.operator(
            "mesh.remove_doubles", text="By Distance", icon="REMOVE_DOUBLES"
        )

        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Merge")


class VIEW3D_MT_edit_mesh_split(Menu):
    bl_label = "Split"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.split", text="Selection", icon="SPLIT")

        layout.separator()

        layout.operator_enum("mesh.edge_split", "type")

        layout.template_node_operator_asset_menu_items(catalog_path="Mesh/Split")


class VIEW3D_MT_edit_mesh_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "mesh.hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "mesh.hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


# bfa menu
class VIEW3D_MT_sculpt_grease_pencil_copy(Menu):
    bl_label = "Copy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("gpencil.copy", text="Copy", icon="COPYDOWN")


class VIEW3D_MT_edit_greasepencil_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("grease_pencil.delete", icon="DELETE")

        layout.separator()

        layout.operator(
            "grease_pencil.delete_frame",
            text="Delete Active Keyframe (Active Layer)",
            icon="DELETE",
        ).type = "ACTIVE_FRAME"  # BFA - redundant, in animation menu
        layout.operator(
            "grease_pencil.delete_frame",
            text="Delete Active Keyframes (All Layers)",
            icon="DELETE_ALL",
        ).type = "ALL_FRAMES"  # BFA - redundant, in animation menu


# Edit Curve
# draw_curve is used by VIEW3D_MT_edit_curve and VIEW3D_MT_edit_surface
def draw_curve(self, context):
    layout = self.layout

    edit_object = context.edit_object

    layout.menu("VIEW3D_MT_transform")
    layout.menu("VIEW3D_MT_mirror")
    layout.menu("VIEW3D_MT_snap")

    layout.separator()

    if edit_object.type == "SURFACE":
        layout.operator("curve.spin", icon="SPIN")
    layout.operator("curve.duplicate_move", text="Duplicate", icon="DUPLICATE")

    layout.separator()

    layout.operator("curve.split", icon="SPLIT")
    layout.operator("curve.separate", icon="SEPARATE")

    layout.separator()

    layout.operator("curve.cyclic_toggle", icon="TOGGLE_CYCLIC")
    if edit_object.type == "CURVE":
        layout.operator("curve.decimate", icon="DECIMATE")
        layout.operator_menu_enum("curve.spline_type_set", "type")

    layout.separator()

    # BFA - redundant operators, located exclusively in VIEW3D_MT_edit_curve_ctrlpoints

    layout.menu("VIEW3D_MT_edit_curve_showhide")

    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_delete")
    if edit_object.type == "CURVE":
        layout.operator("curve.dissolve_verts", icon="DISSOLVE_VERTS")


class VIEW3D_MT_edit_curve(Menu):
    bl_label = "Curve"

    draw = draw_curve


class VIEW3D_MT_edit_curve_ctrlpoints(Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type in {"CURVE", "SURFACE"}:
            layout.operator(
                "curve.extrude_move", text="Extrude Curve", icon="EXTRUDE_REGION"
            )
            layout.operator("curve.vertex_add", icon="EXTRUDE_REGION")

            layout.separator()

            layout.operator("curve.make_segment", icon="MAKE_CURVESEGMENT")

            layout.separator()

            if edit_object.type == "CURVE":
                layout.operator("transform.tilt", icon="TILT")
                layout.operator("curve.tilt_clear", icon="CLEAR_TILT")

                layout.separator()

                layout.operator("curve.normals_make_consistent", icon="RECALC_NORMALS")

                layout.separator()

            layout.operator("curve.smooth", icon="PARTICLEBRUSH_SMOOTH")
            if edit_object.type == "CURVE":
                layout.operator("curve.smooth_weight", icon="SMOOTH_WEIGHT")
                layout.operator("curve.smooth_radius", icon="SMOOTH_RADIUS")
                layout.operator("curve.smooth_tilt", icon="SMOOTH_TILT")

            layout.separator()

        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.operator("object.vertex_parent_set", icon="VERTEX_PARENT")


class VIEW3D_MT_edit_curve_segments(Menu):
    bl_label = "Segments"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator("curve.switch_direction", icon="SWITCH_DIRECTION")


class VIEW3D_MT_edit_curve_clean(Menu):
    bl_label = "Clean Up"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.decimate", icon="DECIMATE")


class VIEW3D_MT_edit_curve_context_menu(Menu):
    bl_label = "Curve"

    def draw(self, _context):
        # TODO(campbell): match mesh vertex menu.

        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"

        # Add
        layout.operator("curve.subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator(
            "curve.extrude_move", text="Extrude Curve", icon="EXTRUDE_REGION"
        )
        layout.operator("curve.make_segment", icon="MAKE_CURVESEGMENT")
        layout.operator("curve.duplicate_move", text="Duplicate", icon="DUPLICATE")

        layout.separator()

        # Transform
        layout.operator(
            "transform.transform", text="Radius", icon="SHRINK_FATTEN"
        ).mode = "CURVE_SHRINKFATTEN"
        layout.operator("transform.tilt", icon="TILT")
        layout.operator("curve.tilt_clear", icon="CLEAR_TILT")
        layout.operator("curve.smooth", icon="PARTICLEBRUSH_SMOOTH")
        layout.operator("curve.smooth_tilt", icon="SMOOTH_TILT")
        layout.operator("curve.smooth_radius", icon="SMOOTH_RADIUS")

        layout.separator()

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        # Modify
        layout.operator_menu_enum("curve.spline_type_set", "type")
        layout.operator_menu_enum("curve.handle_type_set", "type")
        layout.operator("curve.cyclic_toggle", icon="TOGGLE_CYCLIC")
        layout.operator("curve.switch_direction", icon="SWITCH_DIRECTION")

        layout.separator()

        layout.operator("curve.normals_make_consistent", icon="RECALC_NORMALS")
        layout.operator("curve.spline_weight_set", icon="MOD_VERTEX_WEIGHT")
        layout.operator("curve.radius_set", icon="RADIUS")

        layout.separator()

        # Remove
        layout.operator("curve.split", icon="SPLIT")
        layout.operator("curve.decimate", icon="DECIMATE")
        layout.operator("curve.separate", icon="SEPARATE")
        layout.operator("curve.dissolve_verts", icon="DISSOLVE_VERTS")
        layout.operator(
            "curve.delete", text="Delete Segment", icon="DELETE"
        ).type = "SEGMENT"
        layout.operator(
            "curve.delete", text="Delete Point", icon="DELETE"
        ).type = "VERT"

        layout.separator()

        layout.menu("VIEW3D_MT_edit_curve_showhide")  # BFA - added to context menu


class VIEW3D_MT_edit_curve_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curve.delete", text="Vertices", icon="DELETE").type = "VERT"
        layout.operator("curve.delete", text="Segment", icon="DELETE").type = "SEGMENT"


class VIEW3D_MT_edit_curve_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "curve.hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "curve.hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_edit_surface(Menu):
    bl_label = "Surface"

    draw = draw_curve


class VIEW3D_MT_edit_font_chars(Menu):
    bl_label = "Special Characters"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "font.text_insert", text="Copyright \u00a9", icon="COPYRIGHT"
        ).text = "\u00a9"
        layout.operator(
            "font.text_insert", text="Registered Trademark \u00ae", icon="TRADEMARK"
        ).text = "\u00ae"

        layout.separator()

        layout.operator(
            "font.text_insert", text="Degree \u00b0", icon="DEGREE"
        ).text = "\u00b0"
        layout.operator(
            "font.text_insert", text="Multiplication \u00d7", icon="MULTIPLICATION"
        ).text = "\u00d7"
        layout.operator(
            "font.text_insert", text="Circle \u2022", icon="CIRCLE"
        ).text = "\u2022"

        layout.separator()

        layout.operator(
            "font.text_insert", text="Superscript \u00b9", icon="SUPER_ONE"
        ).text = "\u00b9"
        layout.operator(
            "font.text_insert", text="Superscript \u00b2", icon="SUPER_TWO"
        ).text = "\u00b2"
        layout.operator(
            "font.text_insert", text="Superscript \u00b3", icon="SUPER_THREE"
        ).text = "\u00b3"

        layout.separator()

        layout.operator(
            "font.text_insert", text="Guillemet \u00bb", icon="DOUBLE_RIGHT"
        ).text = "\u00bb"
        layout.operator(
            "font.text_insert", text="Guillemet \u00ab", icon="DOUBLE_LEFT"
        ).text = "\u00ab"
        layout.operator(
            "font.text_insert", text="Per Mille \u2030", icon="PROMILLE"
        ).text = "\u2030"

        layout.separator()

        layout.operator(
            "font.text_insert", text="Euro \u20ac", icon="EURO"
        ).text = "\u20ac"
        layout.operator(
            "font.text_insert", text="Florin \u0192", icon="DUTCH_FLORIN"
        ).text = "\u0192"
        layout.operator(
            "font.text_insert", text="Pound \u00a3", icon="POUND"
        ).text = "\u00a3"
        layout.operator(
            "font.text_insert", text="Yen \u00a5", icon="YEN"
        ).text = "\u00a5"

        layout.separator()

        layout.operator(
            "font.text_insert", text="German Eszett \u00df", icon="GERMAN_S"
        ).text = "\u00df"
        layout.operator(
            "font.text_insert",
            text="Inverted Question Mark \u00bf",
            icon="SPANISH_QUESTION",
        ).text = "\u00bf"
        layout.operator(
            "font.text_insert",
            text="Inverted Exclamation Mark \u00a1",
            icon="SPANISH_EXCLAMATION",
        ).text = "\u00a1"


class VIEW3D_MT_edit_font_kerning(Menu):
    bl_label = "Kerning"

    def draw(self, context):
        layout = self.layout

        ob = context.active_object
        text = ob.data
        kerning = text.edit_format.kerning

        layout.operator(
            "font.change_spacing", text="Decrease Kerning", icon="DECREASE_KERNING"
        ).delta = -1.0
        layout.operator(
            "font.change_spacing", text="Increase Kerning", icon="INCREASE_KERNING"
        ).delta = 1.0
        layout.operator(
            "font.change_spacing", text="Reset Kerning", icon="RESET"
        ).delta = -kerning


# bfa menu
class VIEW3D_MT_edit_font_move(Menu):
    bl_label = "Move Cursor"

    def draw(self, _context):
        layout = self.layout

        layout.operator_enum("font.move", "type")


class VIEW3D_MT_edit_font_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "font.delete", text="Previous Character", icon="DELETE"
        ).type = "PREVIOUS_CHARACTER"
        layout.operator(
            "font.delete", text="Next Character", icon="DELETE"
        ).type = "NEXT_CHARACTER"
        layout.operator(
            "font.delete", text="Previous Word", icon="DELETE"
        ).type = "PREVIOUS_WORD"
        layout.operator(
            "font.delete", text="Next Word", icon="DELETE"
        ).type = "NEXT_WORD"


class VIEW3D_MT_edit_font(Menu):
    bl_label = "Text"

    def draw(self, _context):
        layout = self.layout

        layout.operator("font.text_cut", text="Cut", icon="CUT")
        layout.operator("font.text_copy", text="Copy", icon="COPYDOWN")
        layout.operator("font.text_paste", text="Paste", icon="PASTEDOWN")

        layout.separator()

        layout.operator("font.text_paste_from_file", icon="PASTEDOWN")

        layout.separator()

        layout.operator(
            "font.case_set", text="To Uppercase", icon="SET_UPPERCASE"
        ).case = "UPPER"
        layout.operator(
            "font.case_set", text="To Lowercase", icon="SET_LOWERCASE"
        ).case = "LOWER"

        layout.separator()

        layout.operator("FONT_OT_text_insert_unicode", icon="UNICODE")
        layout.menu("VIEW3D_MT_edit_font_chars")
        layout.menu("VIEW3D_MT_edit_font_move")  # bfa menu

        layout.separator()

        layout.operator(
            "font.style_toggle", text="Toggle Bold", icon="BOLD"
        ).style = "BOLD"
        layout.operator(
            "font.style_toggle", text="Toggle Italic", icon="ITALIC"
        ).style = "ITALIC"
        layout.operator(
            "font.style_toggle", text="Toggle Underline", icon="UNDERLINE"
        ).style = "UNDERLINE"
        layout.operator(
            "font.style_toggle", text="Toggle Small Caps", icon="SMALL_CAPS"
        ).style = "SMALL_CAPS"

        layout.menu("VIEW3D_MT_edit_font_kerning")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_font_delete")


class VIEW3D_MT_edit_font_context_menu(Menu):
    bl_label = "Text"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator("font.text_cut", text="Cut", icon="CUT")
        layout.operator("font.text_copy", text="Copy", icon="COPYDOWN")
        layout.operator("font.text_paste", text="Paste", icon="PASTEDOWN")

        layout.separator()

        layout.operator("font.select_all", icon="SELECT_ALL")

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

        layout.operator("mball.duplicate_metaelems", text="Duplicate", icon="DUPLICATE")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_meta_showhide")

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("mball.delete_metaelems", text="Delete", icon="DELETE")


class VIEW3D_MT_edit_meta_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mball.reveal_metaelems", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "mball.hide_metaelems", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "mball.hide_metaelems", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_edit_lattice(Menu):
    bl_label = "Lattice"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.menu("VIEW3D_MT_edit_lattice_flip")  # bfa menu - blender uses enum

        layout.separator()

        layout.operator("lattice.make_regular", icon="MAKE_REGULAR")

        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.operator("object.vertex_parent_set", icon="VERTEX_PARENT")


# bfa menu - blender uses enum
class VIEW3D_MT_edit_lattice_flip(Menu):
    bl_label = "Flip"

    def draw(self, context):
        layout = self.layout

        layout.operator("lattice.flip", text=" U (X) axis", icon="FLIP_X").axis = "U"
        layout.operator("lattice.flip", text=" V (Y) axis", icon="FLIP_Y").axis = "V"
        layout.operator("lattice.flip", text=" W (Z) axis", icon="FLIP_Z").axis = "W"


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

        layout.operator(
            "transform.transform", text="Set Bone Roll", icon="SET_ROLL"
        ).mode = "BONE_ROLL"
        layout.operator(
            "armature.roll_clear", text="Clear Bone Roll", icon="CLEAR_ROLL"
        )

        layout.separator()

        layout.operator("armature.extrude_move", icon="EXTRUDE_REGION")
        layout.operator("armature.click_extrude", icon="EXTRUDE_REGION")

        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked", icon="EXTRUDE_REGION")

        layout.operator("armature.duplicate_move", icon="DUPLICATE")
        layout.operator("armature.fill", icon="FILLBETWEEN")

        layout.separator()

        layout.operator("armature.split", icon="SPLIT")
        layout.operator("armature.separate", icon="SEPARATE")
        layout.operator("armature.symmetrize", icon="SYMMETRIZE")

        layout.separator()

        layout.operator("armature.subdivide", text="Subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator(
            "armature.switch_direction",
            text="Switch Direction",
            icon="SWITCH_DIRECTION",
        )

        layout.separator()

        layout.menu("VIEW3D_MT_edit_armature_names")

        layout.separator()

        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator(
            "armature.move_to_collection",
            text="Move to Bone Collection",
            icon="GROUP_BONE",
        )
        layout.menu("VIEW3D_MT_bone_collections")

        layout.separator()

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("armature.parent_set", text="Make Parent", icon="PARENT_SET")
        layout.operator(
            "armature.parent_clear", text="Clear Parent", icon="PARENT_CLEAR"
        )

        layout.separator()

        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")
        layout.menu(
            "VIEW3D_MT_armature_showhide"
        )  # bfa - the new show hide menu with split tooltip

        layout.separator()

        layout.operator("armature.delete", icon="DELETE")
        layout.operator("armature.dissolve", icon="DELETE")


# BFA menu
class VIEW3D_MT_armature_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.reveal", text="Show Hidden", icon="HIDE_OFF")
        layout.operator(
            "armature.hide", text="Hide Selected", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "armature.hide", text="Hide Unselected", icon="HIDE_UNSELECTED"
        ).unselected = True


class VIEW3D_MT_armature_context_menu(Menu):
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data

        layout.operator_context = "INVOKE_REGION_WIN"

        # Add
        layout.operator("armature.subdivide", text="Subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator("armature.duplicate_move", text="Duplicate", icon="DUPLICATE")
        layout.operator("armature.extrude_move", icon="EXTRUDE_REGION")
        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked", icon="EXTRUDE_REGION")

        layout.separator()

        layout.operator("armature.fill", icon="FILLBETWEEN")

        layout.separator()

        # Modify
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.operator(
            "armature.switch_direction",
            text="Switch Direction",
            icon="SWITCH_DIRECTION",
        )
        layout.operator("armature.symmetrize", icon="SYMMETRIZE")
        layout.menu("VIEW3D_MT_edit_armature_names")

        layout.separator()

        layout.operator("armature.parent_set", text="Make Parent", icon="PARENT_SET")
        layout.operator(
            "armature.parent_clear", text="Clear Parent", icon="PARENT_CLEAR"
        )

        layout.separator()

        # Remove
        layout.operator("armature.split", icon="SPLIT")
        layout.operator("armature.separate", icon="SEPARATE")

        layout.separator()

        layout.operator(
            "armature.move_to_collection",
            text="Move to Bone Collection",
            icon="GROUP_BONE",
        )  # BFA - added to context menu

        layout.separator()

        layout.menu("VIEW3D_MT_armature_showhide")  # BFA - added to context menu

        layout.separator()

        layout.operator("armature.dissolve", icon="DELETE")
        layout.operator("armature.delete", icon="DELETE")


class VIEW3D_MT_edit_armature_names(Menu):
    bl_label = "Names"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator(
            "armature.autoside_names", text="Auto-Name Left/Right", icon="RENAME_X"
        ).type = "XAXIS"
        layout.operator(
            "armature.autoside_names", text="Auto-Name Front/Back", icon="RENAME_Y"
        ).type = "YAXIS"
        layout.operator(
            "armature.autoside_names", text="Auto-Name Top/Bottom", icon="RENAME_Z"
        ).type = "ZAXIS"
        layout.operator("armature.flip_names", text="Flip Names", icon="FLIP")


class VIEW3D_MT_edit_armature_parent(Menu):
    bl_label = "Parent"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout

        layout.operator("armature.parent_set", text="Make", icon="PARENT_SET")
        layout.operator("armature.parent_clear", text="Clear", icon="PARENT_CLEAR")


class VIEW3D_MT_edit_armature_roll(Menu):
    bl_label = "Recalculate Bone Roll"

    def draw(self, _context):
        layout = self.layout

        layout.label(text="- Positive: -")
        layout.operator(
            "armature.calculate_roll", text="Local + X Tangent", icon="ROLL_X_TANG_POS"
        ).type = "POS_X"
        layout.operator(
            "armature.calculate_roll", text="Local + Z Tangent", icon="ROLL_Z_TANG_POS"
        ).type = "POS_Z"
        layout.operator(
            "armature.calculate_roll", text="Global + X Axis", icon="ROLL_X_POS"
        ).type = "GLOBAL_POS_X"
        layout.operator(
            "armature.calculate_roll", text="Global + Y Axis", icon="ROLL_Y_POS"
        ).type = "GLOBAL_POS_Y"
        layout.operator(
            "armature.calculate_roll", text="Global + Z Axis", icon="ROLL_Z_POS"
        ).type = "GLOBAL_POS_Z"
        layout.label(text="- Negative: -")
        layout.operator(
            "armature.calculate_roll", text="Local - X Tangent", icon="ROLL_X_TANG_NEG"
        ).type = "NEG_X"
        layout.operator(
            "armature.calculate_roll", text="Local - Z Tangent", icon="ROLL_Z_TANG_NEG"
        ).type = "NEG_Z"
        layout.operator(
            "armature.calculate_roll", text="Global - X Axis", icon="ROLL_X_NEG"
        ).type = "GLOBAL_NEG_X"
        layout.operator(
            "armature.calculate_roll", text="Global - Y Axis", icon="ROLL_Y_NEG"
        ).type = "GLOBAL_NEG_Y"
        layout.operator(
            "armature.calculate_roll", text="Global - Z Axis", icon="ROLL_Z_NEG"
        ).type = "GLOBAL_NEG_Z"
        layout.label(text="- Other: -")
        layout.operator(
            "armature.calculate_roll", text="Active Bone", icon="BONE_DATA"
        ).type = "ACTIVE"
        layout.operator(
            "armature.calculate_roll", text="View Axis", icon="MANIPUL"
        ).type = "VIEW"
        layout.operator(
            "armature.calculate_roll", text="Cursor", icon="CURSOR"
        ).type = "CURSOR"


class VIEW3D_MT_edit_armature_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "EXEC_AREA"

        layout.operator("armature.delete", text="Bones", icon="DELETE")

        layout.separator()

        layout.operator("armature.dissolve", text="Dissolve Bones", icon="DELETE")


# BFA - menu
class VIEW3D_MT_edit_grease_pencil_arrange_strokes(Menu):
    bl_label = "Arrange Strokes"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "grease_pencil.reorder", text="Bring Forward", icon="MOVE_UP"
        ).direction = "UP"
        layout.operator(
            "grease_pencil.reorder", text="Send Backward", icon="MOVE_DOWN"
        ).direction = "DOWN"
        layout.operator(
            "grease_pencil.reorder", text="Bring to Front", icon="MOVE_TO_TOP"
        ).direction = "TOP"
        layout.operator(
            "grease_pencil.reorder", text="Send to Back", icon="MOVE_TO_BOTTOM"
        ).direction = "BOTTOM"


class VIEW3D_MT_weight_grease_pencil(Menu):
    bl_label = "Weights"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "grease_pencil.vertex_group_normalize_all",
            text="Normalize All",
            icon="WEIGHT_NORMALIZE_ALL",
        )
        layout.operator(
            "grease_pencil.vertex_group_normalize",
            text="Normalize",
            icon="WEIGHT_NORMALIZE",
        )

        layout.separator()

        layout.operator(
            "grease_pencil.weight_invert", text="Invert Weight", icon="WEIGHT_INVERT"
        )
        layout.operator(
            "grease_pencil.vertex_group_smooth", text="Smooth", icon="WEIGHT_SMOOTH"
        )

        layout.separator()

        layout.operator(
            "grease_pencil.weight_sample", text="Sample Weight", icon="EYEDROPPER"
        )


class VIEW3D_MT_edit_greasepencil_animation(Menu):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "grease_pencil.insert_blank_frame",
            text="Insert Blank Keyframe (Active Layer)",
            icon="ADD",
        )
        layout.operator(
            "grease_pencil.insert_blank_frame",
            text="Insert Blank Keyframe (All Layers)",
            icon="ADD_ALL",
        ).all_layers = True

        layout.separator()
        layout.operator(
            "grease_pencil.frame_duplicate",
            text="Duplicate Active Keyframe (Active Layer)",
            icon="DUPLICATE",
        ).all = False
        layout.operator(
            "grease_pencil.frame_duplicate",
            text="Duplicate Active Keyframe (All Layers)",
            icon="DUPLICATE_ALL",
        ).all = True

        layout.separator()
        layout.operator(
            "grease_pencil.active_frame_delete",
            text="Delete Active Keyframe (Active Layer)",
            icon="DELETE",
        ).all = False
        layout.operator(
            "grease_pencil.active_frame_delete",
            text="Delete Active Keyframe (All Layers)",
            icon="DELETE_ALL",
        ).all = True


class VIEW3D_MT_edit_greasepencil_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "grease_pencil.layer_reveal", text="Show All Layers", icon="HIDE_OFF"
        )

        layout.separator()

        layout.operator(
            "grease_pencil.layer_hide", text="Hide Active Layer", icon="HIDE_ON"
        ).unselected = False
        layout.operator(
            "grease_pencil.layer_hide",
            text="Hide Inactive Layers",
            icon="HIDE_UNSELECTED",
        ).unselected = True


class VIEW3D_MT_edit_greasepencil_cleanup(Menu):
    bl_label = "Clean Up"

    def draw(self, context):
        ob = context.object

        layout = self.layout

        layout.operator("grease_pencil.clean_loose", icon="DELETE_LOOSE")
        layout.operator("grease_pencil.frame_clean_duplicate", icon="DELETE_DUPLICATE")

        if ob.mode == "EDIT":  # BFA - should only show in edit mode
            layout.operator(
                "grease_pencil.stroke_merge_by_distance",
                text="Merge by Distance",
                icon="REMOVE_DOUBLES",
            )
            layout.operator("grease_pencil.reproject", icon="REPROJECT")


class VIEW3D_MT_edit_greasepencil(Menu):
    bl_label = "Grease Pencil"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("GREASE_PENCIL_MT_snap")

        layout.separator()

        layout.menu("GREASE_PENCIL_MT_layer_active", text="Active Layer")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_greasepencil_animation", text="Animation")
        layout.operator(
            "grease_pencil.interpolate_sequence",
            text="Interpolate Sequence",
            icon="SEQUENCE",
        ).use_selection = True
        layout.operator(
            "grease_pencil.duplicate_move", text="Duplicate", icon="DUPLICATE"
        )

        layout.separator()

        layout.operator("grease_pencil.copy", text="Copy", icon="COPYDOWN")
        layout.operator("grease_pencil.paste", text="Paste", icon="PASTEDOWN").type = 'ACTIVE'
        layout.operator("grease_pencil.paste", text="Paste by Layer").type = 'LAYER'

        layout.operator_menu_enum("grease_pencil.dissolve", "type")
        layout.menu("VIEW3D_MT_edit_greasepencil_delete")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_greasepencil_cleanup")
        layout.menu("VIEW3D_MT_edit_greasepencil_showhide")

        layout.separator()
        layout.operator_menu_enum("grease_pencil.separate", "mode", text="Separate")


class VIEW3D_MT_edit_greasepencil_stroke(Menu):
    bl_label = "Stroke"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        settings = tool_settings.gpencil_sculpt
        mode = (
            tool_settings.gpencil_selectmode_edit
        )  # bfa - the select mode for grease pencils

        layout.operator(
            "grease_pencil.stroke_subdivide", text="Subdivide", icon="SUBDIVIDE_EDGES"
        )
        layout.operator(
            "grease_pencil.stroke_subdivide_smooth",
            text="Subdivide and Smooth",
            icon="SUBDIVIDE_EDGES",
        )
        # bfa - not in stroke mode. It is greyed out for this mode, so hide.
        if mode != "STROKE":
            layout.operator(
                "grease_pencil.stroke_simplify", text="Fixed", icon="MOD_SIMPLIFY"
            ).mode = "FIXED"
            layout.operator(
                "grease_pencil.stroke_simplify", text="Adaptive"
            ).mode = "ADAPTIVE"
            layout.operator(
                "grease_pencil.stroke_simplify", text="Sample"
            ).mode = "SAMPLE"
            layout.operator(
                "grease_pencil.stroke_simplify", text="Merge"
            ).mode = "MERGE"
        layout.separator()
        layout.operator_menu_enum("grease_pencil.join_selection", "type", text="Join")

        layout.separator()

        layout.menu("GREASE_PENCIL_MT_move_to_layer")
        layout.menu("VIEW3D_MT_grease_pencil_assign_material")
        layout.operator("grease_pencil.set_active_material", icon="MATERIAL")
        layout.menu("VIEW3D_MT_edit_grease_pencil_arrange_strokes")  # BFA - menu

        layout.separator()

        layout.operator(
            "grease_pencil.cyclical_set", text="Close", icon="TOGGLE_CLOSE"
        ).type = "CLOSE"
        layout.operator(
            "grease_pencil.cyclical_set", text="Toggle Cyclic", icon="TOGGLE_CYCLIC"
        ).type = "TOGGLE"
        layout.operator_menu_enum(
            "grease_pencil.caps_set", text="Set Caps", property="type"
        )
        layout.operator("grease_pencil.stroke_switch_direction", icon="FLIP")
        layout.operator(
            "grease_pencil.set_start_point", text="Set Start Point", icon="STARTPOINT"
        )

        layout.separator()

        layout.operator(
            "grease_pencil.set_uniform_thickness",
            text="Normalize Thickness",
            icon="MOD_THICKNESS",
        )
        layout.operator(
            "grease_pencil.set_uniform_opacity",
            text="Normalize Opacity",
            icon="MOD_OPACITY",
        )

        layout.separator()

        layout.operator_menu_enum("grease_pencil.set_curve_type", property="type")
        layout.operator("grease_pencil.set_curve_resolution", icon="SPLINE_RESOLUTION")

        layout.separator()

        layout.operator("grease_pencil.reset_uvs", icon="RESET")


class VIEW3D_MT_edit_greasepencil_point(Menu):
    bl_label = "Point"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "grease_pencil.extrude_move", text="Extrude", icon="EXTRUDE_REGION"
        )

        layout.separator()

        layout.operator(
            "grease_pencil.stroke_smooth", text="Smooth", icon="PARTICLEBRUSH_SMOOTH"
        )

        layout.separator()

        layout.menu("VIEW3D_MT_greasepencil_vertex_group")

        layout.separator()

        layout.operator_menu_enum("grease_pencil.set_handle_type", property="type")


class VIEW3D_MT_edit_curves_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout

        layout.operator("curves.add_bezier", text="Bezier", icon="CURVE_BEZCURVE")
        layout.operator("curves.add_circle", text="Circle", icon="CURVE_BEZCIRCLE")


class VIEW3D_MT_edit_curves(Menu):
    bl_label = "Curves"

    def draw(self, _context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform")
        layout.separator()
        layout.operator("curves.duplicate_move", icon="DUPLICATE")
        layout.separator()
        layout.operator("curves.attribute_set", icon="NODE_ATTRIBUTE")
        layout.operator("curves.delete", icon="DELETE")
        layout.operator("curves.cyclic_toggle", icon="TOGGLE_CYCLIC")
        layout.operator_menu_enum("curves.curve_type_set", "type")
        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


class VIEW3D_MT_edit_curves_control_points(Menu):
    bl_label = "Control Points"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curves.extrude_move", icon="EXTRUDE_REGION")
        layout.operator_menu_enum("curves.handle_type_set", "type")


class VIEW3D_MT_edit_curves_segments(Menu):
    bl_label = "Segments"

    def draw(self, _context):
        layout = self.layout

        layout.operator("curves.subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator("curves.switch_direction", icon="SWITCH_DIRECTION")


class VIEW3D_MT_edit_curves_context_menu(Menu):
    bl_label = "Curves"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator("curves.subdivide", icon="SUBDIVIDE_EDGES")
        layout.operator("curves.extrude_move", icon="EXTRUDE_REGION")

        layout.separator()

        layout.operator_menu_enum("curves.handle_type_set", "type")


class VIEW3D_MT_edit_pointcloud(Menu):
    bl_label = "Point Cloud"

    def draw(self, context):
        layout = self.layout
        layout.template_node_operator_asset_menu_items(catalog_path=self.bl_label)


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
        # pie.operator_enum("view3d.view_axis", "type") #BFA - Opted to the
        # operators that contain consistenty iconography

        # 4 - LEFT
        pie.operator(
            "view3d.view_axis", text="Left", icon="VIEW_LEFT"
        ).type = "LEFT"  # BFA - Icon changed
        # 6 - RIGHT
        pie.operator(
            "view3d.view_axis", text="Right", icon="VIEW_RIGHT"
        ).type = "RIGHT"  # BFA - Icon changed
        # 2 - BOTTOM
        pie.operator(
            "view3d.view_axis", text="Bottom", icon="VIEW_BOTTOM"
        ).type = "BOTTOM"  # BFA - Icon changed
        # 8 - TOP
        pie.operator(
            "view3d.view_axis", text="Top", icon="VIEW_TOP"
        ).type = "TOP"  # BFA - Icon changed
        # 7 - TOP - LEFT
        pie.operator(
            "view3d.view_axis", text="Back", icon="VIEW_BACK"
        ).type = "BACK"  # BFA - Icon Added
        # 9 - TOP - RIGHT
        pie.operator(
            "view3d.view_axis", text="Front", icon="VIEW_FRONT"
        ).type = "FRONT"  # BFA - Icon Added

        # 1 - BOTTOM - LEFT
        pie.operator("view3d.view_camera", text="View Camera", icon="CAMERA_DATA")
        # 3 - BOTTOM - RIGHT
        pie.operator("view3d.view_selected", text="View Selected", icon="VIEW_SELECTED")


class VIEW3D_MT_transform_gizmo_pie(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        # 1: Left
        pie.operator(
            "view3d.transform_gizmo_set", text="Move", icon="TRANSFORM_MOVE"
        ).type = {"TRANSLATE"}
        # 2: Right
        pie.operator(
            "view3d.transform_gizmo_set", text="Rotate", icon="TRANSFORM_ROTATE"
        ).type = {"ROTATE"}
        # 3: Down
        pie.operator(
            "view3d.transform_gizmo_set", text="Scale", icon="TRANSFORM_SCALE"
        ).type = {"SCALE"}
        # 4: Up
        pie.prop(context.space_data, "show_gizmo", text="Show Gizmos", icon="GIZMO")
        # 5: Up/Left
        pie.operator("view3d.transform_gizmo_set", text="All", icon="GIZMO").type = {
            "TRANSLATE",
            "ROTATE",
            "SCALE",
        }


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

        pie.prop_enum(view.shading, "type", value="WIREFRAME")
        pie.prop_enum(view.shading, "type", value="SOLID")

        # Note this duplicates "view3d.toggle_xray" logic, so we can see the active item: #58661.
        if context.pose_object:
            pie.prop(view.overlay, "show_xray_bone", icon="XRAY")
        else:
            xray_active = (context.mode == "EDIT_MESH") or (
                view.shading.type in {"SOLID", "WIREFRAME"}
            )
            if xray_active:
                sub = pie
            else:
                sub = pie.row()
                sub.active = False
            sub.prop(
                view.shading,
                "show_xray_wireframe"
                if (view.shading.type == "WIREFRAME")
                else "show_xray",
                text="Toggle X-Ray",
                icon="XRAY",
            )

        pie.prop(view.overlay, "show_overlays", text="Toggle Overlays", icon="OVERLAY")

        pie.prop_enum(view.shading, "type", value="MATERIAL")
        pie.prop_enum(view.shading, "type", value="RENDERED")


class VIEW3D_MT_pivot_pie(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        tool_settings = context.tool_settings
        obj = context.active_object
        mode = context.mode

        pie.prop_enum(
            tool_settings, "transform_pivot_point", value="BOUNDING_BOX_CENTER"
        )
        pie.prop_enum(tool_settings, "transform_pivot_point", value="CURSOR")
        pie.prop_enum(
            tool_settings, "transform_pivot_point", value="INDIVIDUAL_ORIGINS"
        )
        pie.prop_enum(tool_settings, "transform_pivot_point", value="MEDIAN_POINT")
        pie.prop_enum(tool_settings, "transform_pivot_point", value="ACTIVE_ELEMENT")
        if (obj is None) or (mode in {"OBJECT", "POSE", "WEIGHT_PAINT"}):
            pie.prop(tool_settings, "use_transform_pivot_point_align")
        if mode in {"EDIT_GPENCIL", "EDIT_GREASE_PENCIL"}:
            pie.prop(tool_settings.gpencil_sculpt, "use_scale_thickness")


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

        pie.operator(
            "view3d.snap_cursor_to_grid", text="Cursor to Grid", icon="CURSORTOGRID"
        )
        pie.operator(
            "view3d.snap_selected_to_grid",
            text="Selection to Grid",
            icon="SELECTIONTOGRID",
        )
        pie.operator(
            "view3d.snap_cursor_to_selected",
            text="Cursor to Selected",
            icon="CURSORTOSELECTION",
        )
        pie.operator(
            "view3d.snap_selected_to_cursor",
            text="Selection to Cursor",
            icon="SELECTIONTOCURSOR",
        ).use_offset = False
        pie.operator(
            "view3d.snap_selected_to_cursor",
            text="Selection to Cursor (Keep Offset)",
            icon="SELECTIONTOCURSOROFFSET",
        ).use_offset = True
        pie.operator(
            "view3d.snap_selected_to_active",
            text="Selection to Active",
            icon="SELECTIONTOACTIVE",
        )
        pie.operator(
            "view3d.snap_cursor_to_center",
            text="Cursor to World Origin",
            icon="CURSORTOCENTER",
        )
        pie.operator(
            "view3d.snap_cursor_to_active",
            text="Cursor to Active",
            icon="CURSORTOACTIVE",
        )


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

        props = pie.operator(
            "paint.mask_flood_fill", text="Invert Mask", icon="INVERT_MASK"
        )  # BFA - icon
        props.mode = "INVERT"
        props = pie.operator(
            "paint.mask_flood_fill", text="Clear Mask", icon="CLEAR_MASK"
        )  # BFA - icon
        props.mode = "VALUE"
        props.value = 0.0
        props = pie.operator(
            "sculpt.mask_filter", text="Smooth Mask", icon="PARTICLEBRUSH_SMOOTH"
        )  # BFA - icon
        props.filter_type = "SMOOTH"
        props = pie.operator(
            "sculpt.mask_filter", text="Sharpen Mask", icon="SHARPEN"
        )  # BFA - icon
        props.filter_type = "SHARPEN"
        props = pie.operator(
            "sculpt.mask_filter", text="Grow Mask", icon="SELECTMORE"
        )  # BFA - icon
        props.filter_type = "GROW"
        props = pie.operator(
            "sculpt.mask_filter", text="Shrink Mask", icon="SELECTLESS"
        )  # BFA - icon
        props.filter_type = "SHRINK"
        props = pie.operator(
            "sculpt.mask_filter", text="Increase Contrast", icon="INC_CONTRAST"
        )  # BFA - icon
        props.filter_type = "CONTRAST_INCREASE"
        props.auto_iteration_count = False
        props = pie.operator(
            "sculpt.mask_filter", text="Decrease Contrast", icon="DEC_CONTRAST"
        )  # BFA - icon
        props.filter_type = "CONTRAST_DECREASE"
        props.auto_iteration_count = False


class VIEW3D_MT_sculpt_automasking_pie(Menu):
    bl_label = "Automasking"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        tool_settings = context.tool_settings
        sculpt = tool_settings.sculpt

        pie.prop(sculpt, "use_automasking_topology", text="Topology")
        pie.prop(sculpt, "use_automasking_face_sets", text="Face Sets")
        pie.prop(sculpt, "use_automasking_boundary_edges", text="Mesh Boundary")
        pie.prop(
            sculpt, "use_automasking_boundary_face_sets", text="Face Sets Boundary"
        )
        pie.prop(sculpt, "use_automasking_cavity", text="Cavity")
        pie.prop(sculpt, "use_automasking_cavity_inverted", text="Cavity (Inverted)")
        pie.prop(sculpt, "use_automasking_start_normal", text="Area Normal")
        pie.prop(sculpt, "use_automasking_view_normal", text="View Normal")


class VIEW3D_MT_grease_pencil_sculpt_automasking_pie(Menu):
    bl_label = "Automasking"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        tool_settings = context.tool_settings
        sculpt = tool_settings.gpencil_sculpt

        pie.prop(sculpt, "use_automasking_stroke", text="Stroke")
        pie.prop(sculpt, "use_automasking_layer_stroke", text="Layer")
        pie.prop(sculpt, "use_automasking_material_stroke", text="Material")
        pie.prop(sculpt, "use_automasking_layer_active", text="Active Layer")
        pie.prop(sculpt, "use_automasking_material_active", text="Active Material")


class VIEW3D_MT_sculpt_face_sets_edit_pie(Menu):
    bl_label = "Face Sets Edit"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        props = pie.operator(
            "sculpt.face_sets_create", text="Face Set from Masked", icon="MOD_MASK"
        )  # BFA - Icon
        props.mode = "MASKED"

        props = pie.operator(
            "sculpt.face_sets_create", text="Face Set from Visible", icon="FILL_MASK"
        )  # BFA - Icon
        props.mode = "VISIBLE"

        pie.operator(
            "paint.visibility_invert", text="Invert Visible", icon="INVERT_MASK"
        )  # BFA - Icon

        props = pie.operator("paint.hide_show_all", icon="HIDE_OFF")  # BFA - Icon
        props.action = "SHOW"


class VIEW3D_MT_wpaint_vgroup_lock_pie(Menu):
    bl_label = "Vertex Group Locks"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        # 1: Left
        props = pie.operator("object.vertex_group_lock", icon="LOCKED", text="Lock All")
        props.action, props.mask = "LOCK", "ALL"
        # 2: Right
        props = pie.operator(
            "object.vertex_group_lock", icon="UNLOCKED", text="Unlock All"
        )
        props.action, props.mask = "UNLOCK", "ALL"
        # 3: Down
        props = pie.operator(
            "object.vertex_group_lock", icon="UNLOCKED", text="Unlock Selected"
        )
        props.action, props.mask = "UNLOCK", "SELECTED"
        # 4: Up
        props = pie.operator(
            "object.vertex_group_lock", icon="LOCKED", text="Lock Selected"
        )
        props.action, props.mask = "LOCK", "SELECTED"
        # 5: Up/Left
        props = pie.operator(
            "object.vertex_group_lock", icon="LOCKED", text="Lock Unselected"
        )
        props.action, props.mask = "LOCK", "UNSELECTED"
        # 6: Up/Right
        props = pie.operator(
            "object.vertex_group_lock",
            text="Lock Only Selected",
            icon="RESTRICT_SELECT_OFF",
        )
        props.action, props.mask = "LOCK", "INVERT_UNSELECTED"
        # 7: Down/Left
        props = pie.operator(
            "object.vertex_group_lock",
            text="Lock Only Unselected",
            icon="RESTRICT_SELECT_ON",
        )
        props.action, props.mask = "UNLOCK", "INVERT_UNSELECTED"
        # 8: Down/Right
        props = pie.operator(
            "object.vertex_group_lock", text="Invert Locks", icon="INVERSE"
        )
        props.action, props.mask = "INVERT", "ALL"


# ********** Panel **********


class VIEW3D_PT_active_tool(Panel, ToolActivePanelHelper):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    # See comment below.
    # bl_options = {'HIDE_HEADER'}

    # Don't show in properties editor.
    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"


# FIXME(campbell): remove this second panel once 'HIDE_HEADER' works with category tabs,
# Currently pinning allows ordering headerless panels below panels with headers.
class VIEW3D_PT_active_tool_duplicate(Panel, ToolActivePanelHelper):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_options = {"HIDE_HEADER"}

    # Only show in properties editor.
    @classmethod
    def poll(cls, context):
        return context.area.type != "VIEW_3D"


# BFA - heavily modified, careful
class VIEW3D_PT_view3d_properties(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "View"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()

        subcol = col.column()
        subcol.active = bool(
            view.region_3d.view_perspective != "CAMERA" or view.region_quadviews
        )
        subcol.prop(view, "lens", text="Focal Length")

        subcol = col.column(align=True)
        subcol.prop(view, "clip_start", text="Clip Near")
        subcol.prop(
            view, "clip_end", text="Clip Far", text_ctxt=i18n_contexts.id_camera
        )

        subcol.separator()

        col = layout.column()

        subcol = col.column()
        subcol.use_property_split = False
        row = subcol.row()
        split = row.split(factor=0.65)
        split.prop(view, "use_local_camera")
        if view.use_local_camera:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if view.use_local_camera:
            row = subcol.row()
            row.use_property_split = True
            row.prop(view, "camera", text="")

        row = subcol.row(align=True)
        if view.region_3d.view_perspective == "CAMERA":
            row = subcol.row()
            subcol.prop(view.overlay, "show_camera_passepartout", text="Passepartout")

        subcol.use_property_split = False
        subcol.prop(view, "use_render_border")


# BFA - not used
# class VIEW3D_PT_view3d_lock(Panel):


# bfa panel
class VIEW3D_PT_view3d_properties_edit(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Edit"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        layout.prop(tool_settings, "lock_object_mode")


# bfa panel
class VIEW3D_PT_view3d_camera_lock(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
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
        sub.active = bool(
            view.region_3d.view_perspective != "CAMERA" or view.region_quadviews
        )

        sub.prop(view, "lock_object")
        lock_object = view.lock_object
        if lock_object:
            if lock_object.type == "ARMATURE":
                sub.prop_search(
                    view,
                    "lock_bone",
                    lock_object.data,
                    "edit_bones" if lock_object.mode == "EDIT" else "bones",
                    text="Bone",
                )
        else:
            col = layout.column(align=True)
            col.use_property_split = False
            col.prop(view, "lock_cursor", text="Lock To 3D Cursor")

        col.use_property_split = False
        col.prop(view, "lock_camera", text="Camera to View")
        col.prop(view.region_3d, "lock_rotation", text="Lock View Rotation")


class VIEW3D_PT_view3d_cursor(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "3D Cursor"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        cursor = context.scene.cursor

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.column().prop(cursor, "location", text="Location")
        rotation_mode = cursor.rotation_mode
        if rotation_mode == "QUATERNION":
            layout.column().prop(cursor, "rotation_quaternion", text="Rotation")
        elif rotation_mode == "AXIS_ANGLE":
            layout.column().prop(cursor, "rotation_axis_angle", text="Rotation")
        else:
            layout.column().prop(cursor, "rotation_euler", text="Rotation")
        layout.prop(cursor, "rotation_mode", text="")


class VIEW3D_PT_collections(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Collections"
    bl_options = {"DEFAULT_CLOSED"}

    def _draw_collection(
        self, layout, view_layer, use_local_collections, collection, index
    ):
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

            icon = "BLANK1"
            # has_objects = True
            if child.has_selected_objects(view_layer):
                icon = "LAYER_ACTIVE"
            elif child.has_objects():
                icon = "LAYER_USED"
            else:
                # has_objects = False
                pass

            row = layout.row()
            row.use_property_decorate = False
            sub = row.split(factor=0.98)
            subrow = sub.row()
            subrow.alignment = "LEFT"
            subrow.operator(
                "object.hide_collection",
                text=child.name,
                icon=icon,
                emboss=False,
            ).collection_index = index

            sub = row.split()
            subrow = sub.row(align=True)
            subrow.alignment = "RIGHT"
            if not use_local_collections:
                subrow.active = (
                    collection.is_visible
                )  # Parent collection runtime visibility
                subrow.prop(child, "hide_viewport", text="", emboss=False)
            else:
                subrow.active = (
                    collection.visible_get()
                )  # Parent collection runtime visibility
                icon = "HIDE_OFF" if child.visible_get() else "HIDE_ON"
                props = subrow.operator(
                    "object.hide_collection", text="", icon=icon, emboss=False
                )
                props.collection_index = index
                props.toggle = True

        for child in collection.children:
            index = self._draw_collection(
                layout, view_layer, use_local_collections, child, index
            )

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
        self._draw_collection(
            layout,
            view_layer,
            view.use_local_collections,
            view_layer.layer_collection,
            0,
        )


class VIEW3D_PT_object_type_visibility(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Selectability & Visibility"
    bl_ui_units_x = 8

    # Allows derived classes to pass view data other than context.space_data.
    # This is used by the official VR add-on, which passes XrSessionSettings
    # since VR has a 3D view that only exists for the duration of the VR session.
    def draw_ex(self, _context, view, show_select):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text="Selectability & Visibility")
        layout.separator()
        col = layout.column(align=True)

        attr_object_types = (
            ("mesh", "Mesh", "OUTLINER_OB_MESH"),
            ("curve", "Curve", "OUTLINER_OB_CURVE"),
            ("surf", "Surface", "OUTLINER_OB_SURFACE"),
            ("meta", "Meta", "OUTLINER_OB_META"),
            ("font", "Text", "OUTLINER_OB_FONT"),
            (None, None, None),
            ("curves", "Hair Curves", "HAIR_DATA"),
            ("pointcloud", "Point Cloud", "OUTLINER_OB_POINTCLOUD"),
            ("volume", "Volume", "OUTLINER_OB_VOLUME"),
            ("grease_pencil", "Grease Pencil", "OUTLINER_OB_GREASEPENCIL"),
            ("armature", "Armature", "OUTLINER_OB_ARMATURE"),
            (None, None, None),
            ("lattice", "Lattice", "OUTLINER_OB_LATTICE"),
            ("empty", "Empty", "OUTLINER_OB_EMPTY"),
            ("light", "Light", "OUTLINER_OB_LIGHT"),
            ("light_probe", "Light Probe", "OUTLINER_OB_LIGHTPROBE"),
            ("camera", "Camera", "OUTLINER_OB_CAMERA"),
            ("speaker", "Speaker", "OUTLINER_OB_SPEAKER"),
        )

        for attr, attr_name, attr_icon in attr_object_types:
            if attr is None:
                col.separator()
                continue

            if attr == "curves" and not hasattr(bpy.data, "hair_curves"):
                continue
            elif attr == "pointcloud" and not hasattr(bpy.data, "pointclouds"):
                continue

            attr_v = "show_object_viewport_" + attr
            icon_v = "HIDE_OFF" if getattr(view, attr_v) else "HIDE_ON"

            row = col.row(align=True)
            row.label(text=attr_name, icon=attr_icon)

            if show_select:
                attr_s = "show_object_select_" + attr
                icon_s = (
                    "RESTRICT_SELECT_OFF"
                    if getattr(view, attr_s)
                    else "RESTRICT_SELECT_ON"
                )

                rowsub = row.row(align=True)
                rowsub.active = getattr(view, attr_v)
                rowsub.prop(view, attr_s, text="", icon=icon_s, emboss=False)

            row.prop(view, attr_v, text="", icon=icon_v, emboss=False)

    def draw(self, context):
        view = context.space_data
        self.draw_ex(context, view, True)


class VIEW3D_PT_shading(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Shading"
    bl_ui_units_x = 12

    @classmethod
    def get_shading(cls, context):
        # Get settings from 3D viewport or OpenGL render engine
        view = context.space_data
        if view.type == "VIEW_3D":
            return view.shading
        else:
            return context.scene.display.shading

    def draw(self, _context):
        layout = self.layout
        layout.label(text="Viewport Shading")


class VIEW3D_PT_shading_lighting(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Lighting"
    bl_parent_id = "VIEW3D_PT_shading"

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        if shading.type in {"SOLID", "MATERIAL"}:
            return True
        if shading.type == "RENDERED":
            engine = context.scene.render.engine
            if engine == "BLENDER_EEVEE_NEXT":
                return True
        return False

    def draw(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        col = layout.column()
        split = col.split(factor=0.9)

        if shading.type == "SOLID":
            row = split.row()
            row.separator()
            row.prop(shading, "light", expand=True)
            col = split.column()

            split = layout.split(factor=0.9)
            col = split.column()
            sub = col.row()

            if shading.light == "STUDIO":
                prefs = context.preferences
                system = prefs.system

                if not system.use_studio_light_edit:
                    sub.scale_y = 0.6  # Smaller studio-light preview.
                    row = sub.row()
                    row.separator()
                    row.template_icon_view(shading, "studio_light", scale_popup=3.0)
                else:
                    row = sub.row()
                    row.separator()
                    row.prop(
                        system,
                        "use_studio_light_edit",
                        text="Disable Studio Light Edit",
                        icon="NONE",
                        toggle=True,
                    )

                col = split.column()
                col.operator(
                    "screen.userpref_show", emboss=False, text="", icon="PREFERENCES"
                ).section = "LIGHTS"

                split = layout.split(factor=0.9)
                col = split.column()

                row = col.row()
                row.separator()
                row.prop(
                    shading,
                    "use_world_space_lighting",
                    text="",
                    icon="WORLD",
                    toggle=True,
                )
                row = row.row()
                if shading.use_world_space_lighting:
                    row.prop(shading, "studiolight_rotate_z", text="Rotation")
                    col = split.column()  # to align properly with above

            elif shading.light == "MATCAP":
                sub.scale_y = 0.6  # smaller matcap preview
                row = sub.row()
                row.separator()
                row.template_icon_view(shading, "studio_light", scale_popup=3.0)

                col = split.column()
                col.operator(
                    "screen.userpref_show", emboss=False, text="", icon="PREFERENCES"
                ).section = "LIGHTS"
                col.operator(
                    "view3d.toggle_matcap_flip",
                    emboss=False,
                    text="",
                    icon="ARROW_LEFTRIGHT",
                )

        elif shading.type == "MATERIAL":
            row = col.row()
            row.separator()
            row.prop(shading, "use_scene_lights")
            row = col.row()
            row.separator()
            row.prop(shading, "use_scene_world")
            col = layout.column()
            split = col.split(factor=0.9)

            if not shading.use_scene_world:
                col = split.column()
                sub = col.row()
                sub.scale_y = 0.6
                row = sub.row()
                row.separator()
                row.template_icon_view(shading, "studio_light", scale_popup=3)

                col = split.column()
                col.operator(
                    "screen.userpref_show", emboss=False, text="", icon="PREFERENCES"
                ).section = "LIGHTS"

                split = layout.split(factor=0.9)
                col = split.column()

                engine = context.scene.render.engine
                row = col.row()
                if engine == "BLENDER_WORKBENCH":
                    row.separator()
                    row.prop(
                        shading,
                        "use_studiolight_view_rotation",
                        text="",
                        icon="WORLD",
                        toggle=True,
                    )
                row = row.row()
                row.prop(shading, "studiolight_rotate_z", text="Rotation")

                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_intensity")
                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_background_alpha")
                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_background_blur")
                col = split.column()  # to align properly with above

        elif shading.type == "RENDERED":
            row = col.row()
            row.separator()
            row.prop(shading, "use_scene_lights_render")
            row = col.row()
            row.separator()
            row.prop(shading, "use_scene_world_render")

            if not shading.use_scene_world_render:
                col = layout.column()
                split = col.split(factor=0.9)

                col = split.column()
                sub = col.row()
                sub.scale_y = 0.6
                row = sub.row()
                row.separator()
                row.template_icon_view(shading, "studio_light", scale_popup=3)

                col = split.column()
                col.operator(
                    "screen.userpref_show", emboss=False, text="", icon="PREFERENCES"
                ).section = "LIGHTS"

                split = layout.split(factor=0.9)
                col = split.column()
                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_rotate_z", text="Rotation")
                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_intensity")
                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_background_alpha")
                engine = context.scene.render.engine
                row = col.row()
                row.separator()
                row.prop(shading, "studiolight_background_blur")
                col = split.column()  # to align properly with above
            else:
                row = col.row()
                row.separator()
                row.label(icon="DISCLOSURE_TRI_RIGHT")


class VIEW3D_PT_shading_color(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Wire Color"
    bl_parent_id = "VIEW3D_PT_shading"

    def _draw_color_type(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        layout.grid_flow(columns=3, align=True).prop(shading, "color_type", expand=True)
        if shading.color_type == "SINGLE":
            layout.row().prop(shading, "single_color", text="")

    def _draw_background_color(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        layout.row().label(text="Background")
        layout.row().prop(shading, "background_type", expand=True)
        if shading.background_type == "VIEWPORT":
            layout.row().prop(shading, "background_color", text="")

    def draw(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)

        self.layout.row().prop(shading, "wireframe_color_type", expand=True)
        self.layout.separator()

        if shading.type == "SOLID":
            layout.row().label(text="Color")
            self._draw_color_type(context)
            self.layout.separator()
            self._draw_background_color(context)
        elif shading.type == "WIREFRAME":
            self._draw_background_color(context)


class VIEW3D_PT_shading_options(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Options"
    bl_parent_id = "VIEW3D_PT_shading"

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        return shading.type in {"WIREFRAME", "SOLID"}

    def draw(self, context):
        layout = self.layout

        shading = VIEW3D_PT_shading.get_shading(context)

        col = layout.column()

        if shading.type == "SOLID":
            row = col.row()
            row.separator()
            row.prop(shading, "show_backface_culling")

        row = col.row()

        if shading.type == "WIREFRAME":
            split = layout.split()
            col = split.column()
            row = col.row()
            row.separator()
            row.prop(shading, "show_xray_wireframe")
            col = split.column()
            if shading.show_xray_wireframe:
                col.prop(shading, "xray_alpha_wireframe", text="")
            else:
                col.label(icon="DISCLOSURE_TRI_RIGHT")
        elif shading.type == "SOLID":
            xray_active = shading.show_xray and shading.xray_alpha != 1

            split = layout.split()
            col = split.column()
            col.use_property_split = False
            row = col.row()
            row.separator()
            row.prop(shading, "show_xray")
            col = split.column()
            if shading.show_xray:
                col.use_property_split = False
                col.prop(shading, "xray_alpha", text="")
            else:
                col.label(icon="DISCLOSURE_TRI_RIGHT")

            split = layout.split()
            split.active = not xray_active
            col = split.column()
            col.use_property_split = False
            row = col.row()
            row.separator()
            row.prop(shading, "show_shadows")
            col = split.column()
            if shading.show_shadows:
                col.use_property_split = False
                row = col.row(align=True)
                row.prop(shading, "shadow_intensity", text="")
                row.popover(
                    panel="VIEW3D_PT_shading_options_shadow",
                    icon="PREFERENCES",
                    text="",
                )
            else:
                col.label(icon="DISCLOSURE_TRI_RIGHT")

            row = col.row()
            if not xray_active:
                row.separator()
                row.prop(shading, "use_dof", text="Depth of Field")

        if shading.type in {"WIREFRAME", "SOLID"}:
            split = layout.split()
            col = split.column()
            col.use_property_split = False
            row = col.row()
            row.separator()
            row.prop(shading, "show_object_outline")
            col = split.column()
            if shading.show_object_outline:
                col.use_property_split = False
                col.prop(shading, "object_outline_color", text="")
            else:
                col.label(icon="DISCLOSURE_TRI_RIGHT")

        if shading.type == "SOLID":
            col = layout.column()
            if shading.light in {"STUDIO", "MATCAP"}:
                studio_light = shading.selected_studio_light
                if (
                    studio_light is not None
                ) and studio_light.has_specular_highlight_pass:
                    row = col.row()
                    row.separator()
                    row.prop(
                        shading, "show_specular_highlight", text="Specular Lighting"
                    )


class VIEW3D_PT_shading_options_shadow(Panel):
    bl_label = "Shadow Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

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
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene

        col = layout.column(align=True)
        col.prop(scene.display, "matcap_ssao_samples")
        col.prop(scene.display, "matcap_ssao_distance")
        col.prop(scene.display, "matcap_ssao_attenuation")


class VIEW3D_PT_shading_cavity(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Cavity"
    bl_parent_id = "VIEW3D_PT_shading"

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        return shading.type in {'SOLID'}

    def draw_header(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)
        xray_active = shading.show_xray and shading.xray_alpha != 1

        row = layout.row()
        row.active = not xray_active
        row.prop(shading, "show_cavity")
        if shading.show_cavity:
            row.prop(shading, "cavity_type", text="Type")

    def draw(self, context):
        layout = self.layout
        shading = VIEW3D_PT_shading.get_shading(context)
        xray_active = shading.show_xray and shading.xray_alpha != 1

        col = layout.column()

        if shading.show_cavity and not xray_active:
            if shading.cavity_type in {"WORLD", "BOTH"}:
                row = col.row()
                row.separator()
                row.separator()
                row.label(text="World Space")
                row = col.row()
                row.separator()
                row.separator()
                row.separator()
                row.use_property_split = True
                row.prop(shading, "cavity_ridge_factor", text="Ridge")
                row = col.row()
                row.separator()
                row.separator()
                row.separator()
                row.use_property_split = True
                row.prop(shading, "cavity_valley_factor", text="Valley")
                row.popover(
                    panel="VIEW3D_PT_shading_options_ssao",
                    icon="PREFERENCES",
                    text="",
                )

            if shading.cavity_type in {"SCREEN", "BOTH"}:
                row = col.row()
                row.separator()
                row.separator()
                row.label(text="Screen Space")
                row = col.row()
                row.separator()
                row.separator()
                row.separator()
                row.use_property_split = True
                row.prop(shading, "curvature_ridge_factor", text="Ridge")
                row = col.row()
                row.separator()
                row.separator()
                row.separator()
                row.use_property_split = True
                row.prop(shading, "curvature_valley_factor", text="Valley")


class VIEW3D_PT_shading_render_pass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Render Pass"
    bl_parent_id = "VIEW3D_PT_shading"
    COMPAT_ENGINES = {"BLENDER_EEVEE_NEXT"}

    @classmethod
    def poll(cls, context):
        return (context.space_data.shading.type == "MATERIAL") or (
            context.engine in cls.COMPAT_ENGINES
            and context.space_data.shading.type == "RENDERED"
        )

    def draw(self, context):
        shading = context.space_data.shading

        layout = self.layout
        row = layout.row()
        row.separator()
        row.prop(shading, "render_pass", text="")


class VIEW3D_PT_shading_compositor(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Compositor"
    bl_parent_id = "VIEW3D_PT_shading"
    bl_order = 10

    @classmethod
    def poll(cls, context):
        return context.space_data.shading.type in {"MATERIAL", "RENDERED"}

    def draw(self, context):
        shading = context.space_data.shading
        row = self.layout.row()
        row.prop(shading, "use_compositor", expand=True)


class VIEW3D_PT_gizmo_display(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Gizmos"
    bl_ui_units_x = 12  # BFA - wider

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        view = context.space_data

        prefs = context.preferences
        prefsview = prefs.view

        col = layout.column()
        col.label(text="Viewport Gizmos")
        col.separator()

        col.active = view.show_gizmo
        colsub = col.column()
        # BFA - these are shown below to float left under a label
        # colsub.prop(view, "show_gizmo_navigate", text="Navigate")
        # colsub.prop(view, "show_gizmo_tool", text="Active Tools")
        # colsub.prop(view, "show_gizmo_modifier", text="Active Modifier")
        # colsub.prop(view, "show_gizmo_context", text="Active Object")

        row = colsub.row()
        row.separator()
        row.prop(view, "show_gizmo_navigate", text="Navigate")

        # BFA - these are shown below with a conditional display
        # col = layout.column()
        # col.active = view.show_gizmo and view.show_gizmo_context
        # col.label(text="Object Gizmos")
        # col.prop(scene.transform_orientation_slots[1], "type", text="")
        # col.prop(view, "show_gizmo_object_translate", text="Move", text_ctxt=i18n_contexts.operator_default)
        # col.prop(view, "show_gizmo_object_rotate", text="Rotate", text_ctxt=i18n_contexts.operator_default)
        # col.prop(view, "show_gizmo_object_scale", text="Scale", text_ctxt=i18n_contexts.operator_default)

        row = colsub.row()
        row.separator()
        row.prop(view, "show_gizmo_tool", text="Active Tools")
        row = colsub.row()
        row.separator()
        row.prop(view, "show_gizmo_modifier", text="Active Modifier")

        split = col.split()
        row = split.row()
        row.separator()
        row.prop(view, "show_gizmo_context", text="Active Object")

        row = split.row(align=True)
        if not view.show_gizmo_context:
            row.label(icon="DISCLOSURE_TRI_RIGHT")
        else:
            row.label(icon="DISCLOSURE_TRI_DOWN")
            split = col.split()
            row = split.row()
            row.separator()

            col = layout.column(align=True)
            if view.show_gizmo and view.show_gizmo_context:
                col.label(text="Object Gizmos")
                row = col.row()
                row.separator()
                row.prop(scene.transform_orientation_slots[1], "type", text="")
                row = col.row()
                row.separator()
                row.prop(
                    view,
                    "show_gizmo_object_translate",
                    text="Move",
                    text_ctxt=i18n_contexts.operator_default,
                )  # BFA
                row = col.row()
                row.separator()
                row.prop(
                    view,
                    "show_gizmo_object_rotate",
                    text="Rotate",
                    text_ctxt=i18n_contexts.operator_default,
                )  # BFA
                row = col.row()
                row.separator()
                row.prop(
                    view,
                    "show_gizmo_object_scale",
                    text="Scale",
                    text_ctxt=i18n_contexts.operator_default,
                )  # BFA

        # Match order of object type visibility
        col = layout.column(align=True)
        col.active = view.show_gizmo
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
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Overlays"
    bl_ui_units_x = 14

    def draw(self, _context):
        layout = self.layout
        layout.label(text="Viewport Overlays")


class VIEW3D_PT_overlay_guides(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay"
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

        split = col.split()
        col = split.column()
        col.use_property_split = False
        col.prop(overlay, "show_ortho_grid")
        col = split.column()

        if overlay.show_ortho_grid:
            col.prop(
                overlay,
                "show_floor",
                text="Floor",
                text_ctxt=i18n_contexts.editor_view3d,
            )
        else:
            col.label(icon="DISCLOSURE_TRI_RIGHT")

        if overlay.show_ortho_grid:
            col = layout.column(heading="Axes", align=False)

            row = col.row()
            row.use_property_split = True
            row.use_property_decorate = False
            row.separator()
            row.prop(overlay, "show_axis_x", text="X", toggle=True)
            row.prop(overlay, "show_axis_y", text="Y", toggle=True)
            row.prop(overlay, "show_axis_z", text="Z", toggle=True)

            if overlay.show_floor:
                col = layout.column()
                col.use_property_split = True
                col.use_property_decorate = False
                row = col.row()
                row.separator()
                row.prop(overlay, "grid_scale", text="Grid Scale")
                if scene.unit_settings.system == "NONE":
                    col = layout.column()
                    col.use_property_split = True
                    col.use_property_decorate = False
                    row = col.row()
                    row.separator()
                    row.prop(overlay, "grid_subdivisions", text="Subdivisions")

        layout.separator()

        layout.label(text="Options")

        split = layout.split()
        split.active = display_all
        sub = split.column()
        sub.prop(overlay, "show_text", text="Text Info")
        sub.prop(overlay, "show_stats", text="Statistics")
        if view.region_3d.view_perspective == "CAMERA":
            sub.prop(overlay, "show_camera_guides", text="Camera Guides")

        sub = split.column()
        sub.prop(overlay, "show_cursor", text="3D Cursor")
        sub.prop(overlay, "show_annotation", text="Annotations")

        if shading.type == "MATERIAL":
            row = col.row()
            row.active = shading.render_pass == "COMBINED"
            row.separator()
            row.prop(overlay, "show_look_dev")


class VIEW3D_PT_overlay_object(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay"
    bl_label = "Objects"

    def draw(self, context):
        shading = VIEW3D_PT_shading.get_shading(context)

        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column(align=True)
        col.active = display_all

        split = col.split()

        sub = split.column(align=True)
        row = sub.row()
        row.separator()
        row.prop(overlay, "show_extras", text="Extras")

        row = sub.row()
        row.separator()
        row.active = overlay.show_extras
        row.prop(overlay, "show_light_colors")

        row = sub.row()
        row.separator()
        row.prop(overlay, "show_relationship_lines")
        row = sub.row()
        row.separator()
        row.prop(overlay, "show_outline_selected")

        sub = split.column(align=True)
        sub.prop(overlay, "show_bones", text="Bones")
        sub.prop(overlay, "show_motion_paths")

        split = col.split()
        col = split.column()
        col.use_property_split = False
        row = col.row()
        row.separator()
        row.prop(overlay, "show_object_origins", text="Origins")
        col = split.column()
        if overlay.show_object_origins:
            col.prop(overlay, "show_object_origins_all", text="Origins (All)")
        else:
            col.label(icon="DISCLOSURE_TRI_RIGHT")

        if shading.type == "WIREFRAME" or shading.show_xray:
            layout.separator()
            layout.prop(overlay, "bone_wire_alpha")


class VIEW3D_PT_overlay_geometry(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay"
    bl_label = "Geometry"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays
        is_wireframes = view.shading.type == "WIREFRAME"

        col = layout.column(align=True)
        col.active = display_all
        split = col.split()
        row = split.row()
        row.separator()
        row.prop(overlay, "show_wireframes")

        row = split.row(align=True)
        if overlay.show_wireframes or is_wireframes:
            row.prop(overlay, "wireframe_threshold", text="")
            row.prop(overlay, "wireframe_opacity", text="Opacity")
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")

        row = col.row()
        row.separator()
        row.prop(overlay, "show_face_orientation")

        # These properties should be always available in the UI for all modes
        # other than Object.
        # Even when the Fade Inactive Geometry overlay is not affecting the
        # current active object depending on its mode, it will always affect
        # the rest of the scene.
        if context.mode != "OBJECT":
            col = layout.column(align=True)
            col.active = display_all
            split = col.split()
            row = split.row()
            row.separator()
            row.prop(overlay, "show_fade_inactive")

            row = split.row(align=True)
            if overlay.show_fade_inactive:
                row.prop(overlay, "fade_inactive_alpha", text="")
            else:
                row.label(icon="DISCLOSURE_TRI_RIGHT")

        # sub.prop(overlay, "show_onion_skins")


class VIEW3D_PT_overlay_viewer_node(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay"
    bl_label = "Viewer Node"

    # BFA - We modified this method
    def draw(self, context):
        layout = self.layout
        view = context.space_data
        if not view.show_viewer:
            layout.label(text="Viewer Nodes Overlay Is Disabled", icon="ERROR")
            return

        overlay = view.overlay
        display_all = overlay.show_overlays
        col = layout.column(align=True)
        col.active = display_all
        split = col.split()
        row = split.row()
        row.separator()
        row.prop(overlay, "show_viewer_attribute", text="Color Overlay")

        row = split.row(align=True)
        if not overlay.show_viewer_attribute:
            row.label(icon="DISCLOSURE_TRI_RIGHT")
        else:
            row.label(icon="DISCLOSURE_TRI_DOWN")
            split = col.split()
            row = split.row()
            row.separator()
            col2 = row.column()
            split = col2.split()
            row = split.row()
            row.separator()
            row.use_property_split = True
            row.prop(overlay, "viewer_attribute_opacity", text="Opacity")

        split = col.split()
        row = split.row()
        row.separator()
        row.prop(overlay, "show_viewer_text", text="Text Overlay")


class VIEW3D_PT_overlay_motion_tracking(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay"
    bl_label = "Motion Tracking"

    def draw_header(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays
        layout.active = display_all

        row = layout.row()
        split = row.split()
        split.prop(view, "show_reconstruction", text=self.bl_label)
        if view.show_reconstruction:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

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
            row = sub.row()
            row.separator()
            row.prop(view, "show_camera_path", text="Camera Path")

            sub = split.column()
            sub.prop(view, "show_bundle_names", text="Marker Names")

            col = layout.column()
            col.active = display_all
            col.label(text="Tracks")
            row = col.row(align=True)
            row.separator()
            row.prop(view, "tracks_display_type", text="")
            row.prop(view, "tracks_display_size", text="Size")


class VIEW3D_PT_overlay_edit_mesh(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Mesh Edit Mode"
    bl_ui_units_x = 12

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Mesh Edit Mode Overlays")

        view = context.space_data
        shading = view.shading
        overlay = view.overlay
        display_all = overlay.show_overlays

        is_any_solid_shading = not (shading.show_xray or (shading.type == "WIREFRAME"))

        col = layout.column()
        col.active = display_all

        split = col.split()

        sub = split.column()
        row = sub.row()
        row.separator()
        row.prop(overlay, "show_faces", text="Faces")
        sub = split.column()
        sub.active = is_any_solid_shading
        sub.prop(overlay, "show_face_center", text="Center")

        row = col.row(align=True)
        row.separator()
        row.prop(overlay, "show_edge_crease", text="Creases", toggle=True)
        row.prop(
            overlay,
            "show_edge_sharp",
            text="Sharp",
            text_ctxt=i18n_contexts.plural,
            toggle=True,
        )
        row.prop(overlay, "show_edge_bevel_weight", text="Bevel", toggle=True)
        row.prop(overlay, "show_edge_seams", text="Seams", toggle=True)

        if context.preferences.view.show_developer_ui:
            col.label(text="Developer")
            row = col.row()
            row.separator()
            row.prop(overlay, "show_extra_indices", text="Indices")


class VIEW3D_PT_overlay_edit_mesh_shading(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay_edit_mesh"
    bl_label = "Shading"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

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

        row = col.row()
        row.separator()
        split = row.split(factor=0.55)
        split.prop(overlay, "show_retopology", text="Retopology")
        if overlay.show_retopology:
            split.prop(overlay, "retopology_offset", text="")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        row = col.row()
        row.separator()
        split = row.split(factor=0.55)
        split.prop(overlay, "show_weight", text="Vertex Group Weights")
        if overlay.show_weight:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if overlay.show_weight:
            row = col.row()
            row.separator()
            row.separator()
            row.use_property_split = True
            row.prop(
                tool_settings, "vertex_group_user", text="Zero Weights", expand=True
            )

        if shading.type == "WIREFRAME":
            xray = shading.show_xray_wireframe and shading.xray_alpha_wireframe < 1.0
        elif shading.type == "SOLID":
            xray = shading.show_xray and shading.xray_alpha < 1.0
        else:
            xray = False
        statvis_active = not xray
        row = col.row()
        row.active = statvis_active
        row.separator()
        split = row.split(factor=0.55)
        split.prop(overlay, "show_statvis", text="Mesh Analysis")
        if overlay.show_statvis:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if overlay.show_statvis:
            col = col.column()
            col.active = statvis_active

            sub = col.split()
            row = sub.row()
            row.separator()
            row.separator()
            row.use_property_split = True
            row.prop(statvis, "type", text="Type")

            statvis_type = statvis.type
            if statvis_type == "OVERHANG":
                row = col.row(align=True)
                row.separator()
                row.prop(statvis, "overhang_min", text="Minimum")
                row.prop(statvis, "overhang_max", text="Maximum")
                row = col.row(align=True)
                row.separator()
                row.row().prop(statvis, "overhang_axis", expand=True)
            elif statvis_type == "THICKNESS":
                row = col.row(align=True)
                row.separator()
                row.prop(statvis, "thickness_min", text="Minimum")
                row.prop(statvis, "thickness_max", text="Maximum")
                col.prop(statvis, "thickness_samples")
            elif statvis_type == "INTERSECT":
                pass
            elif statvis_type == "DISTORT":
                row = col.row(align=True)
                row.separator()
                row.prop(statvis, "distort_min", text="Minimum")
                row.prop(statvis, "distort_max", text="Maximum")
            elif statvis_type == "SHARP":
                row = col.row(align=True)
                row.separator()
                row.prop(statvis, "sharp_min", text="Minimum")
                row.prop(statvis, "sharp_max", text="Maximum")


class VIEW3D_PT_overlay_edit_mesh_measurement(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay_edit_mesh"
    bl_label = "Measurement"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        split = col.split()

        sub = split.column()
        row = sub.row()
        row.separator()
        row.prop(overlay, "show_extra_edge_length", text="Edge Length")
        row = sub.row()
        row.separator()
        row.prop(overlay, "show_extra_edge_angle", text="Edge Angle")

        sub = split.column()
        sub.prop(overlay, "show_extra_face_area", text="Face Area")
        sub.prop(overlay, "show_extra_face_angle", text="Face Angle")


class VIEW3D_PT_overlay_edit_mesh_normals(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay_edit_mesh"
    bl_label = "Normals"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all
        split = col.split()

        row = split.row(align=True)
        row.separator()
        row.separator()
        row.prop(overlay, "show_vertex_normals", text="", icon="NORMALS_VERTEX")
        row.prop(overlay, "show_split_normals", text="", icon="NORMALS_VERTEX_FACE")
        row.prop(overlay, "show_face_normals", text="", icon="NORMALS_FACE")

        sub = split.row(align=True)
        if (
            overlay.show_vertex_normals
            or overlay.show_face_normals
            or overlay.show_split_normals
        ):
            sub.use_property_split = True
            if overlay.use_normals_constant_screen_size:
                sub.prop(overlay, "normals_constant_screen_size", text="Size")
            else:
                sub.prop(overlay, "normals_length", text="Size")
        else:
            sub.label(icon="DISCLOSURE_TRI_RIGHT")

        row.prop(
            overlay, "use_normals_constant_screen_size", text="", icon="FIXED_SIZE"
        )


class VIEW3D_PT_overlay_edit_mesh_freestyle(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay_edit_mesh"
    bl_label = "Freestyle"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and bpy.app.build_options.freestyle

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        row = col.row()
        row.separator()
        row.prop(overlay, "show_freestyle_edge_marks", text="Edge Marks")
        row.prop(overlay, "show_freestyle_face_marks", text="Face Marks")


class VIEW3D_PT_overlay_edit_curve(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Curve Edit Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_CURVE"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        layout.label(text="Curve Edit Mode Overlays")

        col = layout.column()
        col.active = display_all

        row = col.row()
        row.prop(overlay, "display_handle", text="Handles")

        col = layout.column(align=True)
        col.active = display_all
        split = col.split()
        row = split.row(align=True)
        # row.separator()
        # row.separator()
        row.prop(overlay, "show_curve_normals")

        row = split.row(align=True)
        if overlay.show_curve_normals:
            row.prop(overlay, "normals_length", text="")
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")


class VIEW3D_PT_overlay_edit_curves(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Curves Edit Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_CURVES"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        layout.label(text="Curves Edit Mode Overlays")

        col = layout.column()
        col.active = display_all

        row = col.row()
        row.prop(overlay, "display_handle", text="Handles")


class VIEW3D_PT_overlay_sculpt(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = ".sculpt_mode"
    bl_region_type = "HEADER"
    bl_label = "Sculpt"
    bl_ui_units_x = 13

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT"

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        layout.label(text="Sculpt Mode Overlays")

        col = layout.column(align=True)
        col.active = display_all
        split = col.split()
        row = split.row()
        row.separator()
        row.prop(overlay, "show_sculpt_mask", text="Show Mask")

        row = split.row(align=True)
        if overlay.show_sculpt_mask:
            row.prop(overlay, "sculpt_mode_mask_opacity", text="")
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")

        col = layout.column(align=True)
        col.active = display_all
        split = col.split()
        row = split.row()
        row.separator()
        row.prop(overlay, "show_sculpt_face_sets", text="Show Face Sets")

        row = split.row(align=True)
        if overlay.show_sculpt_face_sets:
            row.prop(overlay, "sculpt_mode_face_sets_opacity", text="")
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")


class VIEW3D_PT_overlay_sculpt_curves(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = ".curves_sculpt"
    bl_region_type = "HEADER"
    bl_label = "Sculpt"
    bl_ui_units_x = 13

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT_CURVES"

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay

        layout.label(text="Curve Sculpt Overlays")

        row = layout.row(align=True)
        row.active = overlay.show_overlays
        row.use_property_decorate = False
        row.separator(factor=3)
        row.use_property_split = True
        row.prop(overlay, "sculpt_mode_mask_opacity", text="Selection Opacity")

        col = layout.column()
        split = col.split()
        row = split.row()
        row.active = overlay.show_overlays
        row.separator()
        row.prop(overlay, "show_sculpt_curves_cage", text="Curves Cage")

        row = split.row(align=True)
        row.active = overlay.show_overlays
        if overlay.show_sculpt_curves_cage:
            row.prop(overlay, "sculpt_curves_cage_opacity", text="")
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")


class VIEW3D_PT_overlay_bones(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Bones"
    bl_ui_units_x = 14

    @staticmethod
    def is_using_wireframe(context):
        mode = context.mode

        if mode in {"POSE", "PAINT_WEIGHT"}:
            armature = context.pose_object
        elif mode == "EDIT_ARMATURE":
            armature = context.edit_object
        else:
            return False

        return armature and armature.display_type == "WIRE"

    @classmethod
    def poll(cls, context):
        mode = context.mode
        return (
            (mode == "POSE")
            or (mode == "PAINT_WEIGHT" and context.pose_object)
            or (
                mode == "EDIT_ARMATURE"
                and VIEW3D_PT_overlay_bones.is_using_wireframe(context)
            )
        )

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        mode = context.mode
        overlay = view.overlay
        display_all = overlay.show_overlays

        layout.label(text="Armature Overlays")

        col = layout.column()
        col.active = display_all

        if mode == "POSE":
            col = layout.column(align=True)
            col.active = display_all
            split = col.split()
            row = split.row(align=True)
            row.separator()
            row.separator()
            row.prop(overlay, "show_xray_bone")

            row = split.row(align=True)
            if display_all and overlay.show_xray_bone:
                row.prop(overlay, "xray_alpha_bone", text="")
            else:
                row.label(icon="DISCLOSURE_TRI_RIGHT")

        elif mode == "PAINT_WEIGHT":
            row = col.row()
            row.separator()
            row.prop(overlay, "show_xray_bone")


class VIEW3D_PT_overlay_texture_paint(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Texture Paint"
    bl_ui_units_x = 13

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_TEXTURE"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        layout.label(text="Texture Paint Overlays")

        col = layout.column()
        col.active = display_all
        row = col.row()
        row.separator()
        row.label(text="Stencil Mask Opacity")
        row.prop(overlay, "texture_paint_mode_opacity", text="")


class VIEW3D_PT_overlay_vertex_paint(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Vertex Paint"

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_VERTEX"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        layout.label(text="Vertex Paint Overlays")

        col = layout.column()
        col.active = display_all
        row = col.row()
        row.separator()
        row.label(text="Stencil Mask Opacity")
        row.prop(overlay, "vertex_paint_mode_opacity", text="")
        row = col.row()
        row.separator()
        row.prop(overlay, "show_paint_wire")


class VIEW3D_PT_overlay_weight_paint(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Weight Paint"
    bl_ui_units_x = 13

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays
        tool_settings = context.tool_settings

        layout.label(text="Weight Paint Overlays")

        col = layout.column()
        col.active = display_all

        row = col.row()
        row.separator()
        row.label(text="Opacity")
        row.prop(overlay, "weight_paint_mode_opacity", text="")
        row = col.split(factor=0.36)
        row.label(text="     Zero Weights")
        sub = row.row()
        sub.prop(tool_settings, "vertex_group_user", expand=True)

        row = col.row()
        row.separator()
        row.prop(overlay, "show_wpaint_contours")
        row = col.row()
        row.separator()
        row.prop(overlay, "show_paint_wire")


class VIEW3D_PT_snapping(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Snapping"

    def draw(self, context):
        tool_settings = context.tool_settings
        obj = context.active_object
        object_mode = "OBJECT" if obj is None else obj.mode

        layout = self.layout
        col = layout.column()

        col.label(text="Snap Target")
        row = col.row(align=True)
        row.prop(tool_settings, "snap_target", expand=True)

        col.label(text="Snap Base")
        col.prop(tool_settings, "snap_elements_base", expand=True)

        col.label(text="Snap Target for Individual Elements")
        col.prop(tool_settings, "snap_elements_individual", expand=True)

        col.separator()

        if "INCREMENT" in tool_settings.snap_elements:
            col.prop(tool_settings, "use_snap_grid_absolute")

        if "VOLUME" in tool_settings.snap_elements:
            col.prop(tool_settings, "use_snap_peel_object")

        if "FACE_NEAREST" in tool_settings.snap_elements:
            col.prop(tool_settings, "use_snap_to_same_target")
            if object_mode == "EDIT":
                col.prop(tool_settings, "snap_face_nearest_steps")

        col.separator()

        col.prop(tool_settings, "use_snap_align_rotation")
        col.prop(tool_settings, "use_snap_backface_culling")

        col.separator()

        if obj:
            col.label(text="Target Selection")
            col_targetsel = col.column(align=True)
            if object_mode == "EDIT" and obj.type not in {"LATTICE", "META", "FONT"}:
                col_targetsel.prop(
                    tool_settings,
                    "use_snap_self",
                    text="Include Active",
                    icon="EDITMODE_HLT",
                )
                col_targetsel.prop(
                    tool_settings,
                    "use_snap_edit",
                    text="Include Edited",
                    icon="OUTLINER_DATA_MESH",
                )
                col_targetsel.prop(
                    tool_settings,
                    "use_snap_nonedit",
                    text="Include Non-Edited",
                    icon="OUTLINER_OB_MESH",
                )
            col_targetsel.prop(
                tool_settings,
                "use_snap_selectable",
                text="Exclude Non-Selectable",
                icon="RESTRICT_SELECT_OFF",
            )

        col.label(text="Affect")
        row = col.row(align=True)
        row.prop(
            tool_settings,
            "use_snap_translate",
            text="Move",
            text_ctxt=i18n_contexts.operator_default,
            toggle=True,
        )
        row.prop(
            tool_settings,
            "use_snap_rotate",
            text="Rotate",
            text_ctxt=i18n_contexts.operator_default,
            toggle=True,
        )
        row.prop(
            tool_settings,
            "use_snap_scale",
            text="Scale",
            text_ctxt=i18n_contexts.operator_default,
            toggle=True,
        )
        col.label(text="Rotation Increment")
        row = col.row(align=True)
        row.prop(tool_settings, "snap_angle_increment_3d", text="")
        row.prop(tool_settings, "snap_angle_increment_3d_precision", text="")


class VIEW3D_PT_sculpt_snapping(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        col = layout.column()

        col.label(text="Rotation Increment")
        row = col.row(align=True)
        row.prop(tool_settings, "snap_angle_increment_3d", text="")


class VIEW3D_PT_proportional_edit(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Proportional Editing"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        col = layout.column()
        col.active = (
            tool_settings.use_proportional_edit_objects
            if context.mode == "OBJECT"
            else tool_settings.use_proportional_edit
        )

        if context.mode != "OBJECT":
            col.prop(tool_settings, "use_proportional_connected")
            sub = col.column()
            sub.active = not tool_settings.use_proportional_connected
            sub.prop(tool_settings, "use_proportional_projected")
            col.separator()

        col.prop(tool_settings, "proportional_edit_falloff", expand=True)
        col.prop(tool_settings, "proportional_distance")


class VIEW3D_PT_transform_orientations(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
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
        row.operator(
            "transform.create_orientation", text="", icon="ADD", emboss=False
        ).use = True

        if orientation:
            row = layout.row(align=False)
            row.prop(orientation, "name", text="", icon="OBJECT_ORIGIN")
            row.operator(
                "transform.delete_orientation", text="", icon="X", emboss=False
            )


class VIEW3D_PT_grease_pencil_origin(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Stroke Placement"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        layout.label(text="Stroke Placement")

        row = layout.row()
        col = row.column()
        col.prop(tool_settings, "gpencil_stroke_placement_view3d", expand=True)

        if tool_settings.gpencil_stroke_placement_view3d == "SURFACE":
            row = layout.row()
            row.label(text="Offset")
            row = layout.row()
            row.prop(tool_settings, "gpencil_surface_offset", text="")
            row = layout.row()
            row.prop(tool_settings, "use_gpencil_project_only_selected")

        if tool_settings.gpencil_stroke_placement_view3d == "STROKE":
            row = layout.row()
            row.label(text="Target")
            row = layout.row()
            row.prop(tool_settings, "gpencil_stroke_snap_mode", expand=True)


class VIEW3D_PT_grease_pencil_lock(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Drawing Plane"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        layout.label(text="Drawing Plane")

        row = layout.row()
        col = row.column()
        col.prop(tool_settings.gpencil_sculpt, "lock_axis", expand=True)


class VIEW3D_PT_grease_pencil_guide(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Guides"

    def draw(self, context):
        settings = context.tool_settings.gpencil_sculpt.guide

        layout = self.layout
        layout.label(text="Guides")

        col = layout.column()
        col.active = settings.use_guide
        col.prop(settings, "type", expand=True)

        if settings.type in {"ISO", "PARALLEL", "RADIAL"}:
            col.prop(settings, "angle")
            row = col.row(align=True)

        col.prop(settings, "use_snapping")
        if settings.use_snapping:
            if settings.type == "RADIAL":
                col.prop(settings, "angle_snap")
            else:
                col.prop(settings, "spacing")

        if settings.type in {"CIRCULAR", "RADIAL"} or settings.use_snapping:
            col.label(text="Reference Point")
            row = col.row(align=True)
            row.prop(settings, "reference_point", expand=True)
            if settings.reference_point == "CUSTOM":
                col.prop(settings, "location", text="Custom Location")
            elif settings.reference_point == "OBJECT":
                col.prop(settings, "reference_object", text="Object Location")
                if not settings.reference_object:
                    col.label(text="No object selected, using cursor")


class VIEW3D_PT_overlay_grease_pencil_options(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Grease Pencil Options"
    bl_ui_units_x = 13

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == "GREASEPENCIL"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay

        ob = context.object

        layout.label(
            text={
                "PAINT_GREASE_PENCIL": iface_("Draw Grease Pencil"),
                "EDIT_GREASE_PENCIL": iface_("Edit Grease Pencil"),
                "WEIGHT_GREASE_PENCIL": iface_("Weight Grease Pencil"),
                "OBJECT": iface_("Grease Pencil"),
                "SCULPT_GREASE_PENCIL": iface_("Sculpt Grease Pencil"),
                "VERTEX_GREASE_PENCIL": iface_("Vertex Grease Pencil"),
            }[context.mode],
            translate=False,
        )

        col = layout.column(align=True)

        row = col.row()
        row.separator()
        row.prop(overlay, "use_gpencil_onion_skin", text="Onion Skin")

        row = col.row()
        row.use_property_split = False
        split = row.split(factor=0.5)
        row = split.row()
        row.separator()
        row.prop(overlay, "use_gpencil_fade_layers")
        row = split.row()
        if overlay.use_gpencil_fade_layers:
            row.prop(overlay, "gpencil_fade_layer", text="", slider=True)
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")

        row = col.row()
        row.use_property_split = False
        split = row.split(factor=0.5)
        row = split.row()
        row.separator()
        row.prop(overlay, "use_gpencil_fade_objects")
        row = split.row(align=True)
        if overlay.use_gpencil_fade_objects:
            row.prop(overlay, "gpencil_fade_objects", text="", slider=True)
            row.prop(
                overlay,
                "use_gpencil_fade_gp_objects",
                text="",
                icon="OUTLINER_OB_GREASEPENCIL",
            )
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")

        if ob.mode in {
            "EDIT",
            "SCULPT_GREASE_PENCIL",
            "WEIGHT_GREASE_PENCIL",
            "VERTEX_GREASE_PENCIL",
        }:
            col = layout.column(align=True)
            row = col.row()
            row.separator()
            row.prop(overlay, "use_gpencil_edit_lines", text="Edit Lines")
            row = col.row()
            row.separator()
            row.prop(
                overlay, "use_gpencil_multiedit_line_only", text="Only in Multiframe"
            )

        if ob.mode == "EDIT":
            col = layout.column(align=True)
            row = col.row()
            row.separator()
            row.prop(overlay, "use_gpencil_show_directions")
            row = col.row()
            row.separator()
            row.prop(overlay, "use_gpencil_show_material_name", text="Material Name")

        if ob.mode in {"PAINT_GREASE_PENCIL", "VERTEX_GREASE_PENCIL"}:
            layout.label(text="Vertex Paint")
            row = layout.row()
            shading = VIEW3D_PT_shading.get_shading(context)
            row.enabled = shading.type not in {"WIREFRAME", "RENDERED"}
            row.separator()
            row.prop(
                overlay, "gpencil_vertex_paint_opacity", text="Opacity", slider=True
            )


class VIEW3D_PT_overlay_grease_pencil_canvas_options(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay_grease_pencil_options"
    bl_label = "Canvas"
    bl_ui_units_x = 13

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == "GREASEPENCIL"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay

        layout.use_property_decorate = False  # No animation.

        col = layout.column()
        row = col.row()
        row.use_property_split = False
        split = row.split(factor=0.5)
        row = split.row()
        row.separator()
        row.prop(overlay, "use_gpencil_grid")
        row = split.row()
        if overlay.use_gpencil_grid:
            row.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            row.label(icon="DISCLOSURE_TRI_RIGHT")

        if overlay.use_gpencil_grid:
            row = col.row()
            row.separator(factor=2.0)
            row.use_property_split = True
            row.prop(overlay, "gpencil_grid_opacity", text="Opacity", slider=True)
            row.prop(overlay, "use_gpencil_canvas_xray", text="", icon="XRAY")

            col = col.column(align=True)
            col.use_property_split = True
            row = col.row(align=True)
            row.separator(factor=3.5)
            row.prop(overlay, "gpencil_grid_subdivisions")
            row = col.row(align=True)
            row.separator(factor=3.5)
            row.prop(overlay, "gpencil_grid_color", text="Grid Color")

            col = col.column(align=True)
            row = col.row()
            row.separator(factor=2.0)
            row.prop(overlay, "gpencil_grid_scale", text="Scale", expand=True)
            row = col.row()
            row.separator(factor=2.0)
            row.prop(overlay, "gpencil_grid_offset", text="Offset", expand=True)


class VIEW3D_PT_quad_view(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Quad View"
    bl_options = {"DEFAULT_CLOSED"}

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
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"

    # NOTE: this is just a wrapper around the generic GP Panel


class VIEW3D_PT_annotation_onion(AnnotationOnionSkin, Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_parent_id = "VIEW3D_PT_grease_pencil"

    # NOTE: this is just a wrapper around the generic GP Panel


class TOPBAR_PT_annotation_layers(Panel, AnnotationDataPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Layers"
    bl_ui_units_x = 14


class VIEW3D_PT_view3d_stereo(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Stereoscopy"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        scene = context.scene

        multiview = scene.render.use_multiview
        return multiview

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        basic_stereo = context.scene.render.views_format == "STEREO_3D"

        col = layout.column()
        col.row().prop(view, "stereo_3d_camera", expand=True)

        col.label(text="Display")
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

        if context.scene.render.use_multiview:
            layout.separator()
            layout.operator("wm.set_stereo_3d", icon="CAMERA_STEREO")


class VIEW3D_PT_context_properties(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_label = "Properties"
    bl_options = {"DEFAULT_CLOSED"}

    @staticmethod
    def _active_context_member(context):
        obj = context.object
        if obj:
            object_mode = obj.mode
            if object_mode == "POSE":
                return "active_pose_bone"
            elif object_mode == "EDIT" and obj.type == "ARMATURE":
                return "active_bone"
            else:
                return "object"

        return ""

    @classmethod
    def poll(cls, context):
        import rna_prop_ui

        member = cls._active_context_member(context)

        if member:
            context_member, member = rna_prop_ui.rna_idprop_context_value(
                context, member, object
            )
            return context_member and rna_prop_ui.rna_idprop_has_properties(
                context_member
            )

        return False

    def draw(self, context):
        import rna_prop_ui

        member = VIEW3D_PT_context_properties._active_context_member(context)

        if member:
            # Draw with no edit button
            rna_prop_ui.draw(self.layout, context, member, object, use_edit=False)


class VIEW3D_PT_grease_pencil_multi_frame(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Multi Frame"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        settings = tool_settings.gpencil_sculpt

        col = layout.column(align=True)
        col.prop(settings, "use_multiframe_falloff")

        # Falloff curve
        if settings.use_multiframe_falloff:
            layout.template_curve_mapping(
                settings, "multiframe_falloff_curve", brush=True
            )


class VIEW3D_MT_greasepencil_material_active(Menu):
    bl_label = "Active Material"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob is None or len(ob.material_slots) == 0:
            return False

        return True

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"
        ob = context.active_object

        for slot in ob.material_slots:
            mat = slot.material
            if not mat:
                continue
            mat.id_data.preview_ensure()
            if mat and mat.id_data and mat.id_data.preview:
                icon = mat.id_data.preview.icon_id
                layout.operator(
                    "grease_pencil.set_material", text=mat.name, icon_value=icon
                ).slot = mat.name


class VIEW3D_MT_grease_pencil_assign_material(Menu):
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout
        ob = context.active_object
        mat_active = ob.active_material

        if len(ob.material_slots) == 0:
            row = layout.row()
            row.label(text="No Materials", icon="INFO")  # BFA - icon added
            row.enabled = False
            return

        for slot in ob.material_slots:
            mat = slot.material
            if mat:
                layout.operator(
                    "grease_pencil.stroke_material_set",
                    text=mat.name,
                    icon="LAYER_ACTIVE" if mat == mat_active else "BLANK1",
                ).material = mat.name


class VIEW3D_MT_greasepencil_edit_context_menu(Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        mode = (
            tool_settings.gpencil_selectmode_edit
        )  # bfa - the select mode for grease pencils

        is_stroke_mode = tool_settings.gpencil_selectmode_edit in {
            "STROKE",
            "SEGMENT",
        }  # BFA - added segment mode to show context menu

        layout.operator_context = "INVOKE_REGION_WIN"

        row = layout.row()

        if is_stroke_mode:
            col = row.column(align=True)
            col.label(text="Stroke", icon="GP_SELECT_STROKES")

            col.separator()

            # Main Strokes Operators
            col.operator(
                "grease_pencil.stroke_subdivide",
                text="Subdivide",
                icon="SUBDIVIDE_EDGES",
            )
            col.operator(
                "grease_pencil.stroke_subdivide_smooth",
                text="Subdivide and Smooth",
                icon="SUBDIVIDE_EDGES",
            )

            # Deform Operators
            col.operator(
                "grease_pencil.stroke_smooth", text="Smooth", icon="SMOOTH_VERTEX"
            )
            col.operator(
                "transform.transform", text="Radius", icon="RADIUS"
            ).mode = "CURVE_SHRINKFATTEN"

            col.separator()

            col.menu("GREASE_PENCIL_MT_move_to_layer")
            col.menu("VIEW3D_MT_grease_pencil_assign_material")
            col.operator(
                "grease_pencil.set_active_material",
                text="Set as Active Material",
                icon="MATERIAL_DATA",
            )
            col.menu(
                "VIEW3D_MT_edit_grease_pencil_arrange_strokes"
            )  # BFA - menu alternative

            col.separator()

            col.menu("VIEW3D_MT_mirror")
            col.menu("GREASE_PENCIL_MT_snap", text="Snap")

            col.separator()

            # Copy/paste
            col.operator(
                "grease_pencil.duplicate_move", text="Duplicate", icon="DUPLICATE"
            )
            col.operator("grease_pencil.copy", text="Copy", icon="COPYDOWN")
            col.operator("grease_pencil.paste", text="Paste", icon="PASTEDOWN").type = "ACTIVE"
            col.operator("grease_pencil.paste", text="Paste by Layer").type = 'LAYER'

            col.separator()

            # bfa - not in stroke mode. It is greyed out for this mode, so hide.
            if mode != "STROKE":
                col.operator(
                    "grease_pencil.stroke_simplify",
                    text="Simplify",
                    icon="MOD_SIMPLIFY",
                )

                col.separator()

            col.operator(
                "grease_pencil.separate", text="Separate", icon="SEPARATE"
            ).mode = "SELECTED"

        else:
            col = row.column(align=True)
            col.label(text="Point", icon="GP_SELECT_POINTS")

            col.separator()

            col.operator(
                "grease_pencil.extrude_move", text="Extrude", icon="EXTRUDE_REGION"
            )

            col.separator()

            col.operator(
                "grease_pencil.stroke_subdivide",
                text="Subdivide",
                icon="SUBDIVIDE_EDGES",
            )
            col.operator(
                "grease_pencil.stroke_subdivide_smooth",
                text="Subdivide and Smooth",
                icon="SUBDIVIDE_EDGES",
            )

            col.separator()

            col.operator(
                "grease_pencil.stroke_smooth",
                text="Smooth Points",
                icon="SMOOTH_VERTEX",
            )
            col.operator("grease_pencil.set_start_point", text="Set Start Point")

            col.separator()

            col.menu("VIEW3D_MT_mirror", text="Mirror")
            col.menu("GREASE_PENCIL_MT_snap", text="Snap")

            col.separator()

            # Copy/paste
            col.operator(
                "grease_pencil.duplicate_move", text="Duplicate", icon="DUPLICATE"
            )
            col.operator("grease_pencil.copy", text="Copy", icon="COPYDOWN")
            col.operator("grease_pencil.paste", text="Paste", icon="PASTEDOWN")

            col.separator()

            # Removal Operators
            col.operator(
                "grease_pencil.stroke_merge_by_distance", icon="REMOVE_DOUBLES"
            ).use_unselected = False
            col.operator_enum("grease_pencil.dissolve", "type")

            col.separator()

            col.operator(
                "grease_pencil.stroke_simplify", text="Simplify", icon="MOD_SIMPLIFY"
            )

            col.separator()

            col.operator(
                "grease_pencil.separate", text="Separate", icon="SEPARATE"
            ).mode = "SELECTED"


class GREASE_PENCIL_MT_Layers(Menu):
    bl_label = "Layers"

    def draw(self, context):
        layout = self.layout
        grease_pencil = context.active_object.data

        layout.operator("grease_pencil.layer_add", text="New Layer", icon="ADD")

        if not grease_pencil.layers:
            return

        layout.separator()

        # Display layers in layer stack order. The last layer is the top most layer.
        for i in range(len(grease_pencil.layers) - 1, -1, -1):
            layer = grease_pencil.layers[i]
            if layer == grease_pencil.layers.active:
                icon = "DOT"
            else:
                icon = "NONE"
            layout.operator(
                "grease_pencil.layer_active", text=layer.name, icon=icon
            ).layer = i


class VIEW3D_PT_greasepencil_draw_context_menu(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Draw"
    bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        settings = tool_settings.gpencil_paint
        brush = settings.brush
        gp_settings = brush.gpencil_settings

        is_pin_vertex = gp_settings.brush_draw_mode == "VERTEXCOLOR"
        is_vertex = (
            settings.color_mode == "VERTEXCOLOR"
            or brush.gpencil_tool == "TINT"
            or is_pin_vertex
        )

        if brush.gpencil_tool not in {"ERASE", "CUTTER", "EYEDROPPER"} and is_vertex:
            split = layout.split(factor=0.1)
            split.prop(brush, "color", text="")
            split.template_color_picker(brush, "color", value_slider=True)

            col = layout.column()
            col.separator()
            col.prop_menu_enum(gp_settings, "vertex_mode", text="Mode")
            col.separator()

        if brush.gpencil_tool not in {"FILL", "CUTTER", "ERASE"}:
            radius = (
                "size" if (brush.use_locked_size == "VIEW") else "unprojected_radius"
            )
            layout.prop(brush, radius, text="Radius", slider=True)
        if brush.gpencil_tool == "ERASE":
            layout.prop(brush, "size", slider=True)
        if brush.gpencil_tool not in {"ERASE", "FILL", "CUTTER"}:
            layout.prop(gp_settings, "pen_strength")

        layer = context.object.data.layers.active

        if layer:
            layout.label(text="Active Layer")
            row = layout.row(align=True)
            row.operator_context = "EXEC_REGION_WIN"
            row.menu("GREASE_PENCIL_MT_Layers", text="", icon="OUTLINER_DATA_GP_LAYER")
            row.prop(layer, "name", text="")
            row.operator("grease_pencil.layer_remove", text="", icon="X")

        layout.label(text="Active Material")
        row = layout.row(align=True)
        row.menu("VIEW3D_MT_greasepencil_material_active", text="", icon="MATERIAL")
        ob = context.active_object
        if ob.active_material:
            row.prop(ob.active_material, "name", text="")


class VIEW3D_PT_greasepencil_sculpt_context_menu(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Sculpt"
    bl_ui_units_x = 12

    def draw(self, context):
        tool_settings = context.tool_settings
        brush = tool_settings.gpencil_sculpt_paint.brush
        layout = self.layout

        ups = tool_settings.unified_paint_settings
        size_owner = ups if ups.use_unified_size else brush
        strength_owner = ups if ups.use_unified_strength else brush
        layout.prop(size_owner, "size", text="")
        layout.prop(strength_owner, "strength", text="")

        layer = context.object.data.layers.active

        if layer:
            layout.label(text="Active Layer")
            row = layout.row(align=True)
            row.operator_context = "EXEC_REGION_WIN"
            row.menu("GREASE_PENCIL_MT_Layers", text="", icon="OUTLINER_DATA_GP_LAYER")
            row.prop(layer, "name", text="")
            row.operator("grease_pencil.layer_remove", text="", icon="X")


class VIEW3D_PT_greasepencil_vertex_paint_context_menu(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Vertex Paint"
    bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        settings = tool_settings.gpencil_vertex_paint
        brush = settings.brush
        gp_settings = brush.gpencil_settings

        col = layout.column()

        if brush.gpencil_vertex_tool in {"DRAW", "REPLACE"}:
            split = layout.split(factor=0.1)
            split.prop(tool_settings.unified_paint_settings, "color", text="")
            split.template_color_picker(
                tool_settings.unified_paint_settings, "color", value_slider=True
            )

            col = layout.column()
            col.separator()
            col.prop(gp_settings, "vertex_mode", text="")
            col.separator()

        row = col.row(align=True)
        row.prop(tool_settings.unified_paint_settings, "size", text="Radius")
        row.prop(brush, "use_pressure_size", text="", icon="STYLUS_PRESSURE")

        if brush.gpencil_vertex_tool in {"DRAW", "BLUR", "SMEAR"}:
            row = layout.row(align=True)
            row.prop(brush, "strength", slider=True)
            row.prop(brush, "use_pressure_strength", text="", icon="STYLUS_PRESSURE")

        layer = context.object.data.layers.active

        if layer:
            layout.label(text="Active Layer")
            row = layout.row(align=True)
            row.operator_context = "EXEC_REGION_WIN"
            row.menu("GREASE_PENCIL_MT_Layers", text="", icon="OUTLINER_DATA_GP_LAYER")
            row.prop(layer, "name", text="")
            row.operator("grease_pencil.layer_remove", text="", icon="X")


class VIEW3D_PT_greasepencil_weight_context_menu(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Weight Paint"
    bl_ui_units_x = 12

    def draw(self, context):
        tool_settings = context.tool_settings
        settings = tool_settings.gpencil_weight_paint
        brush = settings.brush
        layout = self.layout

        # Weight settings
        brush_basic_grease_pencil_weight_settings(layout, context, brush)


class VIEW3D_PT_grease_pencil_sculpt_automasking(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Auto-Masking"
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        tool_settings = context.scene.tool_settings

        layout.label(text="Auto-Masking")

        col = layout.column(align=True)
        col.prop(tool_settings.gpencil_sculpt, "use_automasking_stroke", text="Stroke")
        col.prop(
            tool_settings.gpencil_sculpt, "use_automasking_layer_stroke", text="Layer"
        )
        col.prop(
            tool_settings.gpencil_sculpt,
            "use_automasking_material_stroke",
            text="Material",
        )
        col.separator()
        col.prop(
            tool_settings.gpencil_sculpt,
            "use_automasking_layer_active",
            text="Active Layer",
        )
        col.prop(
            tool_settings.gpencil_sculpt,
            "use_automasking_material_active",
            text="Active Material",
        )


class VIEW3D_PT_paint_vertex_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Vertex Paint"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.vertex_paint.brush
        capabilities = brush.vertex_paint_capabilities

        if capabilities.has_color:
            split = layout.split(factor=0.1)
            UnifiedPaintPanel.prop_unified_color(
                split, context, brush, "color", text=""
            )
            UnifiedPaintPanel.prop_unified_color_picker(
                split, context, brush, "color", value_slider=True
            )
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
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Texture Paint"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.image_paint.brush
        capabilities = brush.image_paint_capabilities

        if capabilities.has_color:
            split = layout.split(factor=0.1)
            UnifiedPaintPanel.prop_unified_color(
                split, context, brush, "color", text=""
            )
            UnifiedPaintPanel.prop_unified_color_picker(
                split, context, brush, "color", value_slider=True
            )
            layout.prop(brush, "blend", text="")

        if capabilities.has_radius:
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


class VIEW3D_PT_paint_weight_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Weights"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.weight_paint.brush
        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            "weight",
            unified_name="use_unified_weight",
            slider=True,
        )
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


# BFA - these are made consistent with the Sidebar>Tool>Brush Settings>Advanced Automasking panel, heavily changed
class VIEW3D_PT_sculpt_automasking(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Global Auto Masking"
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        sculpt = tool_settings.sculpt
        layout.label(text="Global Auto Masking")
        layout.label(text="Overrides brush settings", icon="QUESTION")

        col = layout.column(align=True)

        # topology automasking
        col.use_property_split = False
        row = col.row()
        row.separator()
        row.prop(sculpt, "use_automasking_topology")

        # face masks automasking
        row = col.row()
        row.separator()
        row.prop(sculpt, "use_automasking_face_sets")

        col = layout.column(align=True)
        col.use_property_split = False

        col = layout.column()
        split = col.split(factor=0.9)
        split.use_property_split = False
        row = split.row()
        row.separator()
        row.prop(sculpt, "use_automasking_boundary_edges", text="Mesh Boundary")

        if (
            sculpt.use_automasking_boundary_edges
            or sculpt.use_automasking_boundary_face_sets
        ):
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        # col = layout.column()
        split = col.split(factor=0.9)
        split.use_property_split = False
        row = split.row()
        row.separator()
        row.prop(
            sculpt, "use_automasking_boundary_face_sets", text="Face Sets Boundary"
        )

        if (
            sculpt.use_automasking_boundary_edges
            or sculpt.use_automasking_boundary_face_sets
        ):
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if (
            sculpt.use_automasking_boundary_edges
            or sculpt.use_automasking_boundary_face_sets
        ):
            col = layout.column()
            col.use_property_split = True
            row = col.row()
            row.separator(factor=3.5)
            row.prop(
                sculpt, "automasking_boundary_edges_propagation_steps", text="Steps"
            )

        col = layout.column()
        split = col.split(factor=0.9)
        split.use_property_split = False
        row = split.row()
        row.separator()
        row.prop(sculpt, "use_automasking_cavity", text="Cavity")

        is_cavity_active = (
            sculpt.use_automasking_cavity or sculpt.use_automasking_cavity_inverted
        )

        if is_cavity_active:
            props = row.operator("sculpt.mask_from_cavity", text="Create Mask")
            props.settings_source = "SCENE"
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        split = col.split(factor=0.9)
        split.use_property_split = False
        row = split.row()
        row.separator()
        row.prop(sculpt, "use_automasking_cavity_inverted", text="Cavity (inverted)")

        is_cavity_active = (
            sculpt.use_automasking_cavity or sculpt.use_automasking_cavity_inverted
        )

        if is_cavity_active:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if is_cavity_active:
            col = layout.column(align=True)
            row = col.row()
            row.separator(factor=3.5)
            props = row.operator("sculpt.mask_from_cavity", text="Create Mask")
            props.settings_source = "SCENE"
            row = col.row()
            row.separator(factor=3.5)
            row.prop(sculpt, "automasking_cavity_factor", text="Factor")
            row = col.row()
            row.separator(factor=3.5)
            row.prop(sculpt, "automasking_cavity_blur_steps", text="Blur")

            col = layout.column()
            col.use_property_split = False
            row = col.row()
            row.separator(factor=3.5)
            row.prop(sculpt, "use_automasking_custom_cavity_curve", text="Custom Curve")

            if sculpt.use_automasking_custom_cavity_curve:
                col.template_curve_mapping(sculpt, "automasking_cavity_curve")

        col = layout.column()
        split = col.split(factor=0.9)
        split.use_property_split = False
        row = split.row()
        row.separator()
        row.prop(sculpt, "use_automasking_view_normal", text="View Normal")

        if sculpt.use_automasking_view_normal:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if sculpt.use_automasking_view_normal:
            row = col.row()
            row.use_property_split = False
            row.separator(factor=3.5)
            row.prop(sculpt, "use_automasking_view_occlusion", text="Occlusion")
            subcol = col.column(align=True)
            if not sculpt.use_automasking_view_occlusion:
                subcol.use_property_split = True
                row = subcol.row()
                row.separator(factor=3.5)
                row.prop(sculpt, "automasking_view_normal_limit", text="Limit")
                row = subcol.row()
                row.separator(factor=3.5)
                row.prop(sculpt, "automasking_view_normal_falloff", text="Falloff")

        # col = layout.column()
        split = col.split(factor=0.9)
        split.use_property_split = False
        row = split.row()
        row.separator()
        row.prop(sculpt, "use_automasking_start_normal", text="Area Normal")

        if sculpt.use_automasking_start_normal:
            split.label(icon="DISCLOSURE_TRI_DOWN")
        else:
            split.label(icon="DISCLOSURE_TRI_RIGHT")

        if sculpt.use_automasking_start_normal:
            col = layout.column(align=True)
            row = col.row()
            row.use_property_split = True  # BFA - label outside
            row.separator(factor=3.5)
            row.prop(sculpt, "automasking_start_normal_limit", text="Limit")
            row = col.row()
            row.use_property_split = True  # BFA - label outside
            row.separator(factor=3.5)
            row.prop(sculpt, "automasking_start_normal_falloff", text="Falloff")
            col.separator()


class VIEW3D_PT_sculpt_context_menu(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.sculpt.brush
        capabilities = brush.sculpt_capabilities

        if capabilities.has_color:
            split = layout.split(factor=0.1)
            UnifiedPaintPanel.prop_unified_color(
                split, context, brush, "color", text=""
            )
            UnifiedPaintPanel.prop_unified_color_picker(
                split, context, brush, "color", value_slider=True
            )
            layout.prop(brush, "blend", text="")

        ups = context.tool_settings.unified_paint_settings
        size = "size"
        size_owner = ups if ups.use_unified_size else brush
        if size_owner.use_locked_size == "SCENE":
            size = "unprojected_radius"

        UnifiedPaintPanel.prop_unified(
            layout,
            context,
            brush,
            size,
            unified_name="use_unified_size",
            pressure_name="use_pressure_size",
            text="Radius",
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

        if capabilities.has_auto_smooth:
            layout.prop(brush, "auto_smooth_factor", slider=True)

        if capabilities.has_normal_weight:
            layout.prop(brush, "normal_weight", slider=True)

        if capabilities.has_pinch_factor:
            text = "Pinch"
            if brush.sculpt_tool in {"BLOB", "SNAKE_HOOK"}:
                text = "Magnify"
            layout.prop(brush, "crease_pinch_factor", slider=True, text=text)

        if capabilities.has_rake_factor:
            layout.prop(brush, "rake_factor", slider=True)

        if capabilities.has_plane_offset:
            layout.prop(brush, "plane_offset", slider=True)
            layout.prop(brush, "plane_trim", slider=True, text="Distance")

        if capabilities.has_height:
            layout.prop(brush, "height", slider=True, text="Height")


class TOPBAR_PT_grease_pencil_materials(GreasePencilMaterialsPanel, Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Materials"
    bl_ui_units_x = 14

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == "GREASEPENCIL"


class TOPBAR_PT_grease_pencil_vertex_color(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_label = "Color Attribute"
    bl_ui_units_x = 10

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == "GREASEPENCIL"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        ob = context.object
        if ob.mode == "PAINT_GREASE_PENCIL":
            paint = context.scene.tool_settings.gpencil_paint
        elif ob.mode == "VERTEX_GREASE_PENCIL":
            paint = context.scene.tool_settings.gpencil_vertex_paint
        use_unified_paint = ob.mode != "PAINT_GREASE_PENCIL"

        ups = context.tool_settings.unified_paint_settings
        brush = paint.brush
        prop_owner = ups if use_unified_paint and ups.use_unified_color else brush

        col = layout.column()
        col.template_color_picker(prop_owner, "color", value_slider=True)

        sub_row = layout.row(align=True)
        if use_unified_paint:
            UnifiedPaintPanel.prop_unified_color(
                sub_row, context, brush, "color", text=""
            )
            UnifiedPaintPanel.prop_unified_color(
                sub_row, context, brush, "secondary_color", text=""
            )
        else:
            sub_row.prop(brush, "color", text="")
            sub_row.prop(brush, "secondary_color", text="")

        sub_row.operator("paint.brush_colors_flip", icon="FILE_REFRESH", text="")

        row = layout.row(align=True)
        row.template_ID(paint, "palette", new="palette.new")
        if paint.palette:
            layout.template_palette(paint, "palette", color=True)

        gp_settings = brush.gpencil_settings
        if brush.gpencil_tool in {"DRAW", "FILL"}:
            row = layout.row(align=True)
            row.prop(gp_settings, "vertex_mode", text="Mode")
            row = layout.row(align=True)
            row.prop(gp_settings, "vertex_color_factor", slider=True, text="Mix Factor")


class VIEW3D_PT_curves_sculpt_add_shape(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Curves Sculpt Add Curve Options"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = False  # BFA - set to False
        layout.use_property_decorate = False  # No animation.

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        col = layout.column(align=True)
        col.label(text="Interpolate")

        row = col.row()
        row.separator()
        row.prop(brush.curves_sculpt_settings, "use_length_interpolate", text="Length")
        row = col.row()
        row.separator()
        row.prop(brush.curves_sculpt_settings, "use_radius_interpolate", text="Radius")
        row = col.row()
        row.separator()
        row.prop(brush.curves_sculpt_settings, "use_shape_interpolate", text="Shape")
        row = col.row()
        row.separator()
        row.prop(
            brush.curves_sculpt_settings,
            "use_point_count_interpolate",
            text="Point Count",
        )

        layout.use_property_split = True

        col = layout.column()
        col.active = not brush.curves_sculpt_settings.use_length_interpolate
        col.prop(brush.curves_sculpt_settings, "curve_length", text="Length")

        col = layout.column()
        col.active = not brush.curves_sculpt_settings.use_radius_interpolate
        col.prop(brush.curves_sculpt_settings, "curve_radius", text="Radius")

        col = layout.column()
        col.active = not brush.curves_sculpt_settings.use_point_count_interpolate
        col.prop(brush.curves_sculpt_settings, "points_per_curve", text="Points")


class VIEW3D_PT_curves_sculpt_parameter_falloff(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Curves Sculpt Parameter Falloff"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        layout.template_curve_mapping(
            brush.curves_sculpt_settings, "curve_parameter_falloff"
        )
        row = layout.row(align=True)
        row.operator(
            "brush.sculpt_curves_falloff_preset", icon="SMOOTHCURVE", text=""
        ).shape = "SMOOTH"
        row.operator(
            "brush.sculpt_curves_falloff_preset", icon="SPHERECURVE", text=""
        ).shape = "ROUND"
        row.operator(
            "brush.sculpt_curves_falloff_preset", icon="ROOTCURVE", text=""
        ).shape = "ROOT"
        row.operator(
            "brush.sculpt_curves_falloff_preset", icon="SHARPCURVE", text=""
        ).shape = "SHARP"
        row.operator(
            "brush.sculpt_curves_falloff_preset", icon="LINCURVE", text=""
        ).shape = "LINE"
        row.operator(
            "brush.sculpt_curves_falloff_preset", icon="NOCURVE", text=""
        ).shape = "MAX"


class VIEW3D_PT_curves_sculpt_grow_shrink_scaling(Panel):
    # Only for popover, these are dummy values.
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_label = "Curves Grow/Shrink Scaling"
    bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        layout.prop(brush.curves_sculpt_settings, "use_uniform_scale")
        layout.prop(brush.curves_sculpt_settings, "minimum_length")


class VIEW3D_PT_viewport_debug(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_parent_id = "VIEW3D_PT_overlay"
    bl_label = "Viewport Debug"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        return prefs.experimental.use_viewport_debug

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay

        layout.prop(overlay, "use_debug_freeze_view_culling")


class View3DAssetShelf(BrushAssetShelf):
    bl_space_type = "VIEW_3D"


class AssetShelfHiddenByDefault:
    # Take #BrushAssetShelf.bl_options but remove the 'DEFAULT_VISIBLE' flag.
    bl_options = {
        option for option in BrushAssetShelf.bl_options if option != "DEFAULT_VISIBLE"
    }


class VIEW3D_AST_brush_sculpt(View3DAssetShelf, bpy.types.AssetShelf):
    mode = "SCULPT"
    mode_prop = "use_paint_sculpt"
    brush_type_prop = "sculpt_brush_type"
    tool_prop = "sculpt_tool"


class VIEW3D_AST_brush_sculpt_curves(View3DAssetShelf, bpy.types.AssetShelf):
    mode = "SCULPT_CURVES"
    mode_prop = "use_paint_sculpt_curves"
    brush_type_prop = "curves_sculpt_brush_type"
    tool_prop = "curves_sculpt_tool"


class VIEW3D_AST_brush_vertex_paint(View3DAssetShelf, bpy.types.AssetShelf):
    mode = "VERTEX_PAINT"
    mode_prop = "use_paint_vertex"
    brush_type_prop = "vertex_brush_type"
    tool_prop = "vertex_tool"


class VIEW3D_AST_brush_weight_paint(
    AssetShelfHiddenByDefault, View3DAssetShelf, bpy.types.AssetShelf
):
    mode = "WEIGHT_PAINT"
    mode_prop = "use_paint_weight"
    brush_type_prop = "weight_brush_type"
    tool_prop = "weight_tool"


class VIEW3D_AST_brush_texture_paint(View3DAssetShelf, bpy.types.AssetShelf):
    mode = "TEXTURE_PAINT"
    mode_prop = "use_paint_image"
    brush_type_prop = "image_brush_type"
    tool_prop = "image_tool"


class VIEW3D_AST_brush_gpencil_paint(View3DAssetShelf, bpy.types.AssetShelf):
    mode = "PAINT_GREASE_PENCIL"
    mode_prop = "use_paint_grease_pencil"
    brush_type_prop = "gpencil_brush_type"
    tool_prop = "gpencil_tool"


class VIEW3D_AST_brush_gpencil_sculpt(View3DAssetShelf, bpy.types.AssetShelf):
    mode = "SCULPT_GREASE_PENCIL"
    mode_prop = "use_sculpt_grease_pencil"
    brush_type_prop = "gpencil_sculpt_brush_type"
    tool_prop = "gpencil_sculpt_tool"


class VIEW3D_AST_brush_gpencil_vertex(
    AssetShelfHiddenByDefault, View3DAssetShelf, bpy.types.AssetShelf
):
    mode = "VERTEX_GREASE_PENCIL"
    mode_prop = "use_vertex_grease_pencil"
    brush_type_prop = "gpencil_vertex_brush_type"
    tool_prop = "gpencil_vertex_tool"


class VIEW3D_AST_brush_gpencil_weight(
    AssetShelfHiddenByDefault, View3DAssetShelf, bpy.types.AssetShelf
):
    mode = "WEIGHT_GREASE_PENCIL"
    mode_prop = "use_weight_grease_pencil"
    brush_type_prop = "gpencil_weight_brush_type"
    tool_prop = "gpencil_weight_tool"


# BFA - material object collection asset shelf
class VIEW3D_AST_object(bpy.types.AssetShelf):
    bl_space_type = "VIEW_3D"
    bl_options = {"STORE_ENABLED_CATALOGS_IN_PREFERENCES"}
    mode = "OBJECT"

    @classmethod
    def asset_poll(cls, asset):
        if (
            asset.id_type == "NODETREE"
            and "Geometry Nodes" in asset.metadata.tags
            and "3D View" in asset.metadata.tags
        ):
            return True
        return asset.id_type in {"MATERIAL", "OBJECT", "COLLECTION", "WORLD"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"


classes = (
    VIEW3D_HT_header,
    VIEW3D_HT_tool_header,
    ALL_MT_editormenu_view3d,  # bfa menu
    VIEW3D_MT_editor_menus,
    VIEW3D_MT_transform,
    VIEW3D_MT_transform_object,
    VIEW3D_MT_transform_armature,
    VIEW3D_MT_mirror,
    VIEW3D_MT_snap,
    VIEW3D_MT_uv_map_clear_seam,  # bfa - Tooltip and operator for Clear Seam.
    VIEW3D_MT_uv_map,
    VIEW3D_MT_switchactivecamto,  # bfa - set active camera does not exist in blender
    VIEW3D_MT_view_legacy,  # bfa menu
    VIEW3D_MT_view_annotations,  # bfa menu
    VIEW3D_MT_view,
    VIEW3D_MT_view_local,
    VIEW3D_MT_view_cameras,
    VIEW3D_MT_view_pie_menus,  # bfa menu
    VIEW3D_MT_view_navigation_legacy,  # bfa menu
    VIEW3D_MT_view_navigation,
    VIEW3D_MT_view_align,
    VIEW3D_MT_view_align_selected,
    VIEW3D_MT_view_viewpoint,
    VIEW3D_MT_view_regions,
    VIEW3D_MT_select_object,
    VIEW3D_MT_select_object_legacy,  # bfa menu
    VIEW3D_MT_select_by_type,  # bfa menu
    VIEW3D_MT_select_grouped,  # bfa menu
    VIEW3D_MT_select_linked,  # bfa menu
    VIEW3D_MT_select_object_more_less,
    VIEW3D_MT_select_pose,
    VIEW3D_MT_select_pose_more_less,
    VIEW3D_MT_select_particle,
    VIEW3D_MT_edit_mesh,
    VIEW3D_MT_edit_mesh_legacy,  # bfa menu
    VIEW3D_MT_edit_mesh_sort_elements,  # bfa menu
    VIEW3D_MT_edit_mesh_select_similar,
    VIEW3D_MT_edit_mesh_select_by_trait,
    VIEW3D_MT_edit_mesh_select_more_less,
    VIEW3D_MT_select_edit_mesh,
    VIEW3D_MT_select_edit_curve,
    VIEW3D_MT_select_edit_curve_select_similar,  # bfa menu
    VIEW3D_MT_select_edit_surface,
    VIEW3D_MT_select_edit_text,
    VIEW3D_MT_select_edit_metaball,
    VIEW3D_MT_edit_lattice_context_menu,
    VIEW3D_MT_select_edit_metaball_select_similar,  # bfa menu
    VIEW3D_MT_select_edit_lattice,
    VIEW3D_MT_select_edit_armature,
    VIEW3D_PT_greasepencil_edit_options,  # BFA - menu
    VIEW3D_MT_select_greasepencil_legacy,  # BFA - legacy menu
    VIEW3D_MT_select_edit_grease_pencil,
    VIEW3D_MT_select_paint_mask_face_more_less,  # bfa menu
    VIEW3D_MT_select_paint_mask_vertex,
    VIEW3D_MT_select_paint_mask_vertex_more_less,  # bfa menu
    VIEW3D_MT_select_edit_point_cloud,
    VIEW3D_MT_edit_curves_select_more_less,
    VIEW3D_MT_select_edit_curves,
    VIEW3D_MT_select_sculpt_curves,
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
    VIEW3D_MT_grease_pencil_add,
    VIEW3D_MT_empty_add,
    VIEW3D_MT_add,
    VIEW3D_MT_image_add,
    VIEW3D_MT_origin_set,  # bfa menu
    VIEW3D_MT_object,
    VIEW3D_MT_object_animation,
    VIEW3D_MT_object_asset,
    VIEW3D_MT_object_rigid_body,
    VIEW3D_MT_object_clear,
    VIEW3D_MT_object_context_menu,
    VIEW3D_MT_object_convert,
    VIEW3D_MT_object_shading,
    VIEW3D_MT_object_apply,
    VIEW3D_MT_object_relations,
    VIEW3D_MT_object_liboverride,
    VIEW3D_MT_object_parent,
    VIEW3D_MT_object_track,
    VIEW3D_MT_object_collection,
    VIEW3D_MT_object_constraints,
    # VIEW3D_MT_object_modifiers, # bfa - renamed and moved to properties editor
    VIEW3D_MT_object_quick_effects,
    VIEW3D_MT_object_showhide,
    VIEW3D_MT_object_cleanup,
    VIEW3D_MT_make_single_user,
    VIEW3D_MT_make_links,
    VIEW3D_MT_brush_paint_modes,  # BFA wip menu, removed?
    VIEW3D_MT_brush,  # BFA - menu
    VIEW3D_MT_facemask_showhide,  # BFA - menu
    VIEW3D_MT_paint_vertex,
    VIEW3D_MT_hook,
    VIEW3D_MT_vertex_group,
    VIEW3D_MT_greasepencil_vertex_group,
    VIEW3D_MT_paint_weight,
    VIEW3D_MT_paint_weight_legacy,  # BFA - menu
    VIEW3D_MT_paint_weight_lock,
    VIEW3D_MT_subdivision_set,  # BFA - menu
    VIEW3D_MT_sculpt,
    VIEW3D_MT_sculpt_legacy,  # BFA - menu
    VIEW3D_MT_bfa_sculpt_transform,  # BFA - menu
    VIEW3D_MT_bfa_sculpt_showhide,  # BFA - menu
    VIEW3D_MT_sculpt_set_pivot,
    VIEW3D_MT_sculpt_transform,  # BFA - not used
    VIEW3D_MT_sculpt_showhide,  # BFA - menu
    VIEW3D_MT_sculpt_trim,  # BFA - not used
    VIEW3D_MT_mask,
    VIEW3D_MT_mask_legacy,  # BFA - menu
    VIEW3D_MT_face_sets_showhide,  # BFA - menu
    VIEW3D_MT_face_sets,
    VIEW3D_MT_face_sets_init,
    VIEW3D_MT_random_mask,
    VIEW3D_MT_particle,
    VIEW3D_MT_particle_context_menu,
    VIEW3D_MT_particle_showhide,
    VIEW3D_MT_pose,
    VIEW3D_MT_pose_transform,
    VIEW3D_MT_pose_slide,
    VIEW3D_MT_pose_propagate,
    VIEW3D_MT_pose_motion,
    VIEW3D_MT_bone_collections,
    VIEW3D_MT_pose_ik,
    VIEW3D_MT_pose_constraints,
    VIEW3D_MT_pose_names,
    VIEW3D_MT_pose_showhide,
    VIEW3D_MT_pose_apply,
    VIEW3D_MT_pose_context_menu,
    VIEW3D_MT_bone_options_toggle,
    VIEW3D_MT_bone_options_enable,
    VIEW3D_MT_bone_options_disable,
    VIEW3D_MT_edit_mesh_context_menu,
    VIEW3D_MT_edit_mesh_select_mode,
    VIEW3D_MT_edit_mesh_select_linked,
    VIEW3D_MT_edit_mesh_select_loops,
    VIEW3D_MT_edit_mesh_extrude_dupli,  # bfa operator for separated tooltip
    VIEW3D_MT_edit_mesh_extrude_dupli_rotate,  # bfa operator for separated tooltip
    VIEW3D_MT_edit_mesh_extrude,
    VIEW3D_MT_edit_mesh_vertices,
    VIEW3D_MT_edit_mesh_vertices_legacy,  # BFA - menu
    VIEW3D_MT_edit_mesh_edges,
    VIEW3D_MT_edit_mesh_edges_legacy,  # BFA - menu
    VIEW3D_MT_edit_mesh_faces,
    VIEW3D_MT_edit_mesh_faces_legacy,  # BFA - menu
    VIEW3D_MT_edit_mesh_faces_data,
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
    VIEW3D_MT_edit_mesh_dissolve,  # BFA - menu
    VIEW3D_MT_edit_mesh_showhide,
    VIEW3D_MT_greasepencil_material_active,
    VIEW3D_MT_paint_grease_pencil,
    VIEW3D_MT_paint_vertex_grease_pencil,
    VIEW3D_MT_edit_grease_pencil_arrange_strokes,  # BFA - menu
    VIEW3D_MT_sculpt_grease_pencil_copy,  # BFA - menu
    VIEW3D_MT_edit_greasepencil_showhide,
    VIEW3D_MT_edit_greasepencil_cleanup,
    VIEW3D_MT_weight_grease_pencil,
    VIEW3D_MT_greasepencil_edit_context_menu,
    VIEW3D_MT_grease_pencil_assign_material,
    VIEW3D_MT_edit_greasepencil,
    VIEW3D_MT_edit_greasepencil_delete,  # BFA - not used
    VIEW3D_MT_edit_greasepencil_stroke,
    VIEW3D_MT_edit_greasepencil_point,
    VIEW3D_MT_edit_greasepencil_animation,
    VIEW3D_MT_edit_curve,
    VIEW3D_MT_edit_curve_ctrlpoints,
    VIEW3D_MT_edit_curve_segments,
    VIEW3D_MT_edit_curve_clean,
    VIEW3D_MT_edit_curve_context_menu,
    VIEW3D_MT_edit_curve_delete,
    VIEW3D_MT_edit_curve_showhide,
    VIEW3D_MT_edit_surface,
    VIEW3D_MT_edit_font,
    VIEW3D_MT_edit_font_chars,
    VIEW3D_MT_edit_font_kerning,
    VIEW3D_MT_edit_font_move,  # BFA - menu
    VIEW3D_MT_edit_font_delete,
    VIEW3D_MT_edit_font_context_menu,
    VIEW3D_MT_edit_meta,
    VIEW3D_MT_edit_meta_showhide,
    VIEW3D_MT_edit_lattice,
    VIEW3D_MT_edit_lattice_flip,  # BFA - menu - blender uses enum
    VIEW3D_MT_edit_armature,
    VIEW3D_MT_armature_showhide,  # BFA - menu
    VIEW3D_MT_armature_context_menu,
    VIEW3D_MT_edit_armature_parent,
    VIEW3D_MT_edit_armature_roll,
    VIEW3D_MT_edit_armature_names,
    VIEW3D_MT_edit_armature_delete,
    VIEW3D_MT_edit_curves,
    VIEW3D_MT_edit_curves_add,
    VIEW3D_MT_edit_curves_segments,
    VIEW3D_MT_edit_curves_control_points,
    VIEW3D_MT_edit_curves_context_menu,
    VIEW3D_MT_edit_pointcloud,
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
    VIEW3D_MT_sculpt_automasking_pie,
    VIEW3D_MT_grease_pencil_sculpt_automasking_pie,
    VIEW3D_MT_wpaint_vgroup_lock_pie,
    VIEW3D_MT_sculpt_face_sets_edit_pie,
    VIEW3D_MT_sculpt_curves,
    VIEW3D_PT_active_tool,
    VIEW3D_PT_active_tool_duplicate,
    VIEW3D_PT_view3d_properties,
    VIEW3D_PT_view3d_properties_edit,  # bfa panel
    # VIEW3D_PT_view3d_lock, # BFA - not used, and Blender hotkeys doesn't call this, so ommitted
    VIEW3D_PT_view3d_camera_lock,  # bfa panel
    VIEW3D_PT_view3d_cursor,
    VIEW3D_PT_collections,
    VIEW3D_PT_object_type_visibility,
    VIEW3D_PT_grease_pencil,
    VIEW3D_PT_annotation_onion,
    VIEW3D_PT_grease_pencil_multi_frame,
    VIEW3D_PT_grease_pencil_sculpt_automasking,
    VIEW3D_PT_quad_view,
    VIEW3D_PT_view3d_stereo,
    VIEW3D_PT_shading,
    VIEW3D_PT_shading_lighting,
    VIEW3D_PT_shading_color,
    VIEW3D_PT_shading_options,
    VIEW3D_PT_shading_options_shadow,
    VIEW3D_PT_shading_options_ssao,
    VIEW3D_PT_shading_cavity,
    VIEW3D_PT_shading_render_pass,
    VIEW3D_PT_shading_compositor,
    VIEW3D_PT_gizmo_display,
    VIEW3D_PT_overlay,
    VIEW3D_PT_overlay_guides,
    VIEW3D_PT_overlay_object,
    VIEW3D_PT_overlay_geometry,
    VIEW3D_PT_overlay_viewer_node,
    VIEW3D_PT_overlay_motion_tracking,
    VIEW3D_PT_overlay_edit_mesh,
    VIEW3D_PT_overlay_edit_mesh_shading,
    VIEW3D_PT_overlay_edit_mesh_measurement,
    VIEW3D_PT_overlay_edit_mesh_normals,
    VIEW3D_PT_overlay_edit_mesh_freestyle,
    VIEW3D_PT_overlay_edit_curve,
    VIEW3D_PT_overlay_edit_curves,
    VIEW3D_PT_overlay_texture_paint,
    VIEW3D_PT_overlay_vertex_paint,
    VIEW3D_PT_overlay_weight_paint,
    VIEW3D_PT_overlay_bones,
    VIEW3D_PT_overlay_sculpt,
    VIEW3D_PT_overlay_sculpt_curves,
    VIEW3D_PT_snapping,
    VIEW3D_PT_sculpt_snapping,
    VIEW3D_PT_proportional_edit,
    VIEW3D_PT_grease_pencil_origin,
    VIEW3D_PT_grease_pencil_lock,
    VIEW3D_PT_grease_pencil_guide,
    VIEW3D_PT_transform_orientations,
    VIEW3D_PT_overlay_grease_pencil_options,
    VIEW3D_PT_overlay_grease_pencil_canvas_options,
    VIEW3D_PT_context_properties,
    VIEW3D_PT_paint_vertex_context_menu,
    VIEW3D_PT_paint_texture_context_menu,
    VIEW3D_PT_paint_weight_context_menu,
    VIEW3D_PT_sculpt_automasking,
    VIEW3D_PT_sculpt_context_menu,
    TOPBAR_PT_grease_pencil_materials,
    TOPBAR_PT_grease_pencil_vertex_color,
    TOPBAR_PT_annotation_layers,
    VIEW3D_PT_curves_sculpt_add_shape,
    VIEW3D_PT_curves_sculpt_parameter_falloff,
    VIEW3D_PT_curves_sculpt_grow_shrink_scaling,
    VIEW3D_PT_viewport_debug,
    VIEW3D_AST_brush_sculpt,
    VIEW3D_AST_brush_sculpt_curves,
    VIEW3D_AST_brush_vertex_paint,
    VIEW3D_AST_brush_weight_paint,
    VIEW3D_AST_brush_texture_paint,
    VIEW3D_AST_brush_gpencil_paint,
    VIEW3D_AST_brush_gpencil_sculpt,
    VIEW3D_AST_brush_gpencil_vertex,
    VIEW3D_AST_brush_gpencil_weight,
    VIEW3D_AST_object,  # bfa assetshelf
    GREASE_PENCIL_MT_Layers,
    VIEW3D_PT_greasepencil_draw_context_menu,
    VIEW3D_PT_greasepencil_sculpt_context_menu,
    VIEW3D_PT_greasepencil_vertex_paint_context_menu,
    VIEW3D_PT_greasepencil_weight_context_menu,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
