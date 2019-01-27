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
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from .properties_paint_common import (
    UnifiedPaintPanel,
)
from .properties_grease_pencil_common import (
    AnnotationDataPanel,
    AnnotationOnionSkin,
    GreasePencilMaterialsPanel,
)
from bpy.app.translations import contexts as i18n_contexts


class VIEW3D_HT_header(Header):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        shading = view.shading
        # mode_string = context.mode
        obj = context.active_object
        overlay = view.overlay
        tool_settings = context.tool_settings

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        object_mode = 'OBJECT' if obj is None else obj.mode

        act_mode_item = bpy.types.Object.bl_rna.properties["mode"].enum_items[object_mode]
        
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

            if gpd.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(tool_settings, "gpencil_selectmode", text="", expand=True)

            if gpd.use_stroke_edit_mode or gpd.is_stroke_sculpt_mode or gpd.is_stroke_weight_mode:
                row = layout.row(align=True)

                if gpd.is_stroke_sculpt_mode:
                    row.prop(tool_settings.gpencil_sculpt, "use_select_mask", text="")
                    row.separator()

                row.prop(gpd, "use_multiedit", text="", icon='GP_MULTIFRAME_EDITING')

                sub = row.row(align=True)
                sub.active = gpd.use_multiedit
                sub.popover(
                    panel="VIEW3D_PT_gpencil_multi_frame",
                    text="Multiframe"
                )

            if gpd.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(tool_settings.gpencil_sculpt, "use_select_mask", text="")

                row.popover(
                    panel="VIEW3D_PT_tools_grease_pencil_interpolate",
                    text="Interpolate"
                )
        VIEW3D_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        # Mode & Transform Settings
        scene = context.scene

        # Orientation
        if object_mode in {'OBJECT', 'EDIT', 'POSE', 'EDIT_GPENCIL'}:
            orient_slot = scene.transform_orientation_slots[0]
            custom_orientation = orient_slot.custom_orientation
            trans_name, trans_icon = orient_slot.ui_info()

            row = layout.row(align=True)

            sub = row.row()
            sub.ui_units_x = 4
            sub.popover(
                panel="VIEW3D_PT_transform_orientations",
                text=trans_name,
                icon_value=trans_icon,
            )

        # Snap
        show_snap = False
        if obj is None:
            show_snap = True
        else:
            if object_mode not in {'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT', 'TEXTURE_PAINT',
                                   'PAINT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}:
                show_snap = True
            else:

                from .properties_paint_common import UnifiedPaintPanel
                paint_settings = UnifiedPaintPanel.paint_settings(context)

                if paint_settings:
                    brush = paint_settings.brush
                    if brush and brush.stroke_method == 'CURVE':
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
        if obj:
            gpd = context.gpencil_data
            if object_mode in {'EDIT', 'PARTICLE_EDIT'}:
                row = layout.row(align=True)
                row.prop(tool_settings, "proportional_edit", icon_only=True)
                sub = row.row(align=True)
                sub.active = tool_settings.proportional_edit != 'DISABLED'
                sub.prop(tool_settings, "proportional_edit_falloff", icon_only=True)

            elif object_mode == 'OBJECT':
                row = layout.row(align=True)
                row.prop(tool_settings, "use_proportional_edit_objects", icon_only=True)
                sub = row.row(align=True)
                sub.active = tool_settings.use_proportional_edit_objects
                sub.prop(tool_settings, "proportional_edit_falloff", icon_only=True)

            elif gpd is not None and obj.type == 'GPENCIL':
                if gpd.use_stroke_edit_mode or gpd.is_stroke_sculpt_mode:
                    row = layout.row(align=True)
                    row.prop(tool_settings, "proportional_edit", icon_only=True)

                    sub = row.row(align=True)
                    sub.active = tool_settings.proportional_edit != 'DISABLED'
                    sub.prop(tool_settings, "proportional_edit_falloff", icon_only=True)
        else:
            if context.gpencil_data and context.gpencil_data.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(tool_settings, "proportional_edit", icon_only=True)
                sub = row.row(align=True)
                sub.active = tool_settings.proportional_edit != 'DISABLED'
                sub.prop(tool_settings, "proportional_edit_falloff", icon_only=True)

        # Pivot
        if object_mode in {'OBJECT', 'EDIT', 'POSE', 'EDIT_GPENCIL', 'SCULPT_GPENCIL'}:
            pivot_point = tool_settings.transform_pivot_point
            act_pivot_point = bpy.types.ToolSettings.bl_rna.properties["transform_pivot_point"].enum_items[pivot_point]
            row = layout.row(align=True)
            row.popover(
                panel="VIEW3D_PT_pivot_point",
                icon=act_pivot_point.icon,
                text="",
            )
        # grease pencil
        if object_mode == 'PAINT_GPENCIL':
            origin = tool_settings.gpencil_stroke_placement_view3d
            gp_origin = tool_settings.bl_rna.properties["gpencil_stroke_placement_view3d"].enum_items[origin]

            or_icon = getattr(gp_origin, "icon", "BLANK1")
            or_name = getattr(gp_origin, "name", "Stroke Placement")
            layout.popover(
                panel="VIEW3D_PT_gpencil_origin",
                text=or_name,
                icon=or_icon,
            )

        if object_mode in {'PAINT_GPENCIL', 'SCULPT_GPENCIL'}:
            lock = tool_settings.gpencil_sculpt.lock_axis
            gp_lock = tool_settings.gpencil_sculpt.bl_rna.properties["lock_axis"].enum_items[lock]

            lk_icon = getattr(gp_lock, "icon", "BLANK1")
            lk_name = getattr(gp_lock, "name", "None")
            row = layout.row()
            row.enabled = tool_settings.gpencil_stroke_placement_view3d in {'ORIGIN', 'CURSOR'}
            row.popover(
                panel="VIEW3D_PT_gpencil_lock",
                text=lk_name,
                icon=lk_icon,
            )
            
        if object_mode in {'PAINT_GPENCIL'}:
            if context.workspace.tools.from_space_view3d_mode(object_mode).name == "Draw":
                settings = tool_settings.gpencil_sculpt.guide
                row = layout.row(align=True)
                row.prop(settings, "use_guide", text="", icon='GRID')
                sub = row.row(align=True)
                sub.active = settings.use_guide
                sub.popover(
                    panel="VIEW3D_PT_gpencil_guide",
                    text="Guides"
                )

        layout.separator_spacer()

        # Collection Visibility
        layout.popover(
            panel="VIEW3D_PT_collections",
            icon='GROUP',
            text="",
        )

        # Viewport Settings
        layout.popover(
            panel="VIEW3D_PT_object_type_visibility",
            icon_value=view.icon_from_show_object_viewport,
            text="",
        )

        row = layout.row(align=True)
        row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
        sub = row.row(align=True)
        sub.active = overlay.show_overlays
        sub.popover(panel="VIEW3D_PT_overlay")

        row = layout.row()
        row.active = (shading.type in {'WIREFRAME', 'SOLID'}) or object_mode in {'EDIT'}

        if shading.type == 'WIREFRAME':
            row.prop(shading, "show_xray_wireframe", text="", icon='XRAY')
        else:
            row.prop(shading, "show_xray", text="", icon='XRAY')

        row = layout.row(align=True)
        row.prop(shading, "type", text="", expand=True)
        sub = row.row(align=True)
        # TODO, currently render shading type ignores mesh two-side, until it's supported
        # show the shading popover which shows double-sided option.

        # sub.enabled = shading.type != 'RENDERED'
        sub.popover(panel="VIEW3D_PT_shading")

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
    bl_space_type = 'VIEW3D_MT_editor_menus'
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mode_string = context.mode
        edit_object = context.edit_object
        gp_edit = obj and obj.mode in {'EDIT_GPENCIL', 'PAINT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}

        layout.menu("VIEW3D_MT_view")
        layout.menu("VIEW3D_MT_view_navigation")
        

        # Select Menu
        if gp_edit:
            if mode_string not in {'PAINT_GPENCIL', 'WEIGHT_GPENCIL'}:
                layout.menu("VIEW3D_MT_select_gpencil")
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
            layout.menu("VIEW3D_MT_add", text="Add")
        elif mode_string == 'EDIT_MESH':
            layout.menu("VIEW3D_MT_mesh_add", text="Add")
        elif mode_string == 'EDIT_CURVE':
            layout.menu("VIEW3D_MT_curve_add", text="Add")
        elif mode_string == 'EDIT_SURFACE':
            layout.menu("VIEW3D_MT_surface_add", text="Add")
        elif mode_string == 'EDIT_METABALL':
            layout.menu("VIEW3D_MT_metaball_add", text="Add")
        elif mode_string == 'EDIT_ARMATURE':
            layout.menu("TOPBAR_MT_edit_armature_add", text="Add")

        if gp_edit:
            if obj and obj.mode == 'PAINT_GPENCIL':
                layout.menu("VIEW3D_MT_paint_gpencil")
            elif obj and obj.mode == 'EDIT_GPENCIL':
                layout.menu("VIEW3D_MT_edit_gpencil")
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
                layout.menu("VIEW3D_MT_hide_mask")
        else:
            layout.menu("VIEW3D_MT_object")


# ********** Menu **********


# ********** Utilities **********


class ShowHideMenu:
    bl_label = "Show/Hide"
    _operator_name = ""

    def draw(self, context):
        layout = self.layout

        layout.operator("%s.reveal" % self._operator_name, text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("%s.hide" % self._operator_name, text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("%s.hide" % self._operator_name, text="Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


# Standard transforms which apply to all cases
# NOTE: this doesn't seem to be able to be used directly
class VIEW3D_MT_transform_base(Menu):
    bl_label = "Transform"
    bl_category = "View"

    # TODO: get rid of the custom text strings?
    def draw(self, context):
        layout = self.layout

        layout.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
        layout.operator("transform.shear", text="Shear", icon = "SHEAR")
        layout.operator("transform.bend", text="Bend", icon = "BEND")
        layout.operator("transform.push_pull", text="Push/Pull", icon = 'PUSH_PULL')

        if context.mode != 'OBJECT':
            layout.operator("transform.vertex_warp", text="Warp", icon = "MOD_WARP")
            layout.operator("transform.vertex_random", text="Randomize", icon = 'RANDOMIZE')
            layout.operator("transform.skin_resize", text="Skin Resize", icon = "MOD_SKIN")


# Generic transform menu - geometry types
class VIEW3D_MT_transform(VIEW3D_MT_transform_base):
    def draw(self, context):
        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # generic
        layout = self.layout
        layout.operator("transform.shrink_fatten", text="Shrink Fatten", icon = 'SHRINK_FATTEN')

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

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.mirror", text="Interactive Mirror", icon='TRANSFORM_MIRROR')

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'

        props = layout.operator("transform.mirror", text="X Global", icon = "MIRROR_X")
        props.constraint_axis = (True, False, False)
        props.constraint_orientation = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Y Global", icon = "MIRROR_Y")
        props.constraint_axis = (False, True, False)
        props.constraint_orientation = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Z Global", icon = "MIRROR_Z")
        props.constraint_axis = (False, False, True)
        props.constraint_orientation = 'GLOBAL'

        if context.edit_object:
            layout.separator()

            props = layout.operator("transform.mirror", text="X Local", icon = "MIRROR_X")
            props.constraint_axis = (True, False, False)
            props.constraint_orientation = 'LOCAL'
            props = layout.operator("transform.mirror", text="Y Local", icon = "MIRROR_Y")
            props.constraint_axis = (False, True, False)
            props.constraint_orientation = 'LOCAL'
            props = layout.operator("transform.mirror", text="Z Local", icon = "MIRROR_Z")
            props.constraint_axis = (False, False, True)
            props.constraint_orientation = 'LOCAL'

            layout.separator()

            layout.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP")


class VIEW3D_MT_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
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


class VIEW3D_MT_uv_map(Menu):
    bl_label = "UV Mapping"

    def draw(self, context):
        layout = self.layout

        layout.operator("uv.unwrap")

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("uv.smart_project")
        layout.operator("uv.lightmap_pack")
        layout.operator("uv.follow_active_quads")

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("uv.cube_project")
        layout.operator("uv.cylinder_project")
        layout.operator("uv.sphere_project")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("uv.project_from_view").scale_to_bounds = False
        layout.operator("uv.project_from_view", text="Project from View (Bounds)").scale_to_bounds = True

        layout.separator()

        layout.operator("mesh.mark_seam").clear = False
        layout.operator("mesh.mark_seam", text="Clear Seam").clear = True

        layout.separator()

        layout.operator("uv.reset")


class VIEW3D_MT_edit_proportional(Menu):
    bl_label = "Proportional Editing"

    def draw(self, context):
        layout = self.layout

        layout.props_enum(tool_settings, "proportional_edit")

        layout.separator()

        layout.label(text="Falloff:")
        layout.props_enum(tool_settings, "proportional_edit_falloff")


# ********** View menus **********


    # Workaround to separate the tooltips
class VIEW3D_MT_view_view_selected_all_regions(bpy.types.Operator):
    """View Selected All Regions\nMove the View to the selection center in all Quad View views"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_selected_all_regions"        # unique identifier for buttons and menu items to reference.
    bl_label = "View Selected All Regions"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_selected(use_all_regions = True)
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_view_all_all_regions(bpy.types.Operator):
    """View All all Regions\nView all objects in scene in all four Quad View views\nJust relevant for Quad View """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_all_all_regions"        # unique identifier for buttons and menu items to reference.
    bl_label = "View All all Regions"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_all(use_all_regions = True)
        return {'FINISHED'}

    # Workaround to separate the tooltips
class VIEW3D_MT_view_center_cursor_and_view_all(bpy.types.Operator):
    """Center Cursor and View All\nViews all objects in scene and centers the 3D cursor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_all_center_cursor"        # unique identifier for buttons and menu items to reference.
    bl_label = "Center Cursor and View All"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_all(center = True)
        return {'FINISHED'}


class VIEW3D_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        layout.operator("view3d.toolshelf", text = "Tool Shelf", icon='MENU_PANEL')
        layout.operator("view3d.properties", text = "Sidebar", icon='MENU_PANEL')

        layout.separator()

        layout.operator("render.opengl", icon='RENDER_STILL')
        layout.operator("render.opengl", text="Viewport Render Animation", icon='RENDER_ANIMATION').animation = True

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.clip_border", text="Clipping Border", icon = "CLIPPINGBORDER")
        layout.operator("view3d.render_border", text="Render Border", icon = "RENDERBORDER")
        layout.operator("view3d.clear_render_border", text="Clear Render Border", icon = "RENDERBORDER_CLEAR")

        layout.separator()

        layout.operator("view3d.object_as_camera", icon = 'VIEW_SWITCHACTIVECAM')
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
        layout.operator("view3d.view_all", text="View All", icon = "VIEWALL").center = False
        if view.region_quadviews:
            layout.operator("view3d.view_all_all_regions", text = "View All (Quad View)", icon = "VIEWALL" ) # bfa - separated tooltip
        layout.operator("view3d.view_all_center_cursor", text="Center Cursor and View All", icon = "VIEWALL_RESETCURSOR") # bfa - separated tooltip

        layout.separator()

        layout.menu("INFO_MT_area")

class VIEW3D_MT_view_navigation(Menu):
    bl_label = "Navi"

    def draw(self, context):
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

        layout.separator()

        layout.operator("transform.translate", icon='TRANSFORM_MOVE')
        layout.operator("transform.rotate", icon='TRANSFORM_ROTATE')
        layout.operator("transform.resize", icon='TRANSFORM_SCALE', text="Scale")



class VIEW3D_MT_view_align(Menu):
    bl_label = "Align View"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.camera_to_view", text="Align Active Camera to View", icon = "ALIGNCAMERA_VIEW")
        layout.operator("view3d.camera_to_view_selected", text="Align Active Camera to Selected", icon = "ALIGNCAMERA_ACTIVE")
        layout.operator("view3d.view_center_cursor", icon = "CENTERTOCURSOR")

        layout.separator()

        layout.operator("view3d.view_lock_to_active", icon = "LOCKTOACTIVE")
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

    def draw(self, context):
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

    def draw(self, context):
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
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_object(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("object.select_all", text="None").action = 'DESELECT'
        layout.operator("object.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.menu ("VIEW3D_MT_select_by_type")
        layout.operator("object.select_camera", text="Active Camera", icon = "CAMERA_DATA")
        layout.operator("object.select_mirror", text="Selection", icon = "TRANSFORM_MIRROR")
        layout.operator("object.select_random", text="Random", icon = "RANDOMIZE")

        layout.separator()

        layout.menu("VIEW3D_MT_select_object_more_less")

        layout.separator()

        layout.menu ("VIEW3D_MT_select_grouped")
        layout.menu ("VIEW3D_MT_select_linked")
        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")

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
        layout.operator("object.select_by_type", text= "Light", icon = "OUTLINER_OB_LAMP").type = 'LIGHT'
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
        layout.operator("object.select_grouped", text= "Collection", icon = "LAYER").type = 'COLLECTION'
        layout.operator("object.select_grouped", text= "Hook", icon = "HOOK").type = 'HOOK'

        layout.separator()

        layout.operator("object.select_grouped", text= "Pass", icon = "PASS").type = 'PASS'
        layout.operator("object.select_grouped", text= "Color", icon = "COLOR").type = 'COLOR'
        layout.operator("object.select_grouped", text= "Keying Set", icon = "KEYINGSET").type = 'KEYINGSET'
        layout.operator("object.select_grouped", text= "Light Type", icon = "LAMP").type = 'LIGHT_TYPE'


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


class VIEW3D_MT_select_pose_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, context):
        layout = self.layout

        layout = self.layout

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
class VIEW3D_MT_select_pose_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "pose.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.pose.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_pose(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("pose.select_all", text="None").action = 'DESELECT'
        layout.operator("pose.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("pose.select_mirror", text="Flip Active", icon = "FLIP")

        layout.separator()

        layout.operator("pose.select_constraint_target", text="Constraint Target", icon = "CONSTRAINT_BONE")
        layout.operator("pose.select_linked", text="Linked", icon = "LINKED")

        layout.separator()

        layout.menu("VIEW3D_MT_select_pose_more_less")

        layout.separator()

        layout.operator_menu_enum("pose.select_grouped", "type", text="Grouped")
        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")


# Workaround to separate the tooltips
class VIEW3D_MT_select_particle_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "particle.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.particle.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_particle(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("particle.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("particle.select_all", text="None").action = 'DESELECT'
        layout.operator("particle.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("particle.select_linked", text = "Linked", icon = "LINKED")

        layout.separator()

        layout.operator("particle.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("particle.select_less", text = "Less", icon = "SELECTLESS")

        layout.separator()

        layout.operator("particle.select_random", text = "Random", icon = "RANDOMIZE")

        layout.separator()

        layout.operator("particle.select_roots", text="Roots", icon = "SELECT_ROOT")
        layout.operator("particle.select_tips", text="Tips", icon = "SELECT_TIP")


class VIEW3D_MT_edit_mesh_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        select_mode = context.tool_settings.mesh_select_mode 

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

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.select_more", text="More", icon = "SELECTMORE")
        layout.operator("mesh.select_less", text="Less", icon = "SELECTLESS")

        layout.separator()

        layout.operator("mesh.select_next_item", text="Next Active", icon = "NEXTACTIVE")
        layout.operator("mesh.select_prev_item", text="Previous Active", icon = "PREVIOUSACTIVE")


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_mesh_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_edit_mesh(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        # primitive
        layout.operator("mesh.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("mesh.select_all", text="None").action = 'DESELECT'
        layout.operator("mesh.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        # numeric
        layout.operator("mesh.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("mesh.select_nth", icon = "CHECKER_DESELECT")

        layout.separator()

        # geometric
        layout.operator("mesh.edges_select_sharp", text="Sharp Edges", icon = "SELECT_SHARPEDGES")

        layout.separator()

        # other 
        layout.menu("VIEW3D_MT_edit_mesh_select_similar")

        layout.separator()

        # topology
        tool_settings = context.tool_settings
        if tool_settings.mesh_select_mode[2] is False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold", icon = "SELECT_NONMANIFOLD")
        layout.operator("mesh.select_loose", text="Loose Geometry", icon = "SELECT_LOOSE")
        layout.operator("mesh.select_interior_faces", text="Interior Faces", icon = "SLEECT_INTERIOR")
        layout.operator("mesh.select_face_by_sides", text="Faces by Sides", icon = "SELECT_FACES_BY_SIDE")

        layout.separator()

        layout.operator("mesh.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_select_more_less")

        layout.separator()

        # loops
        layout.operator("mesh.loop_multi_select", text="Edge Loops", icon = "SELECT_EDGELOOP").ring = False
        layout.operator("mesh.loop_multi_select", text="Edge Rings", icon = "SELECT_EDGERING").ring = True
        layout.operator("mesh.loop_to_region", text = "Loop Inner Region", icon = "SELECT_LOOPINNER")
        layout.operator("mesh.region_to_loop", text = "Boundary Loop", icon = "SELECT_BOUNDARY")

        layout.separator()

        layout.operator("mesh.shortest_path_select", text="Shortest Path", icon = "SELECT_SHORTESTPATH")

        layout.separator()

        layout.operator("mesh.select_linked", text="Linked", icon = "LINKED")        
        layout.operator("mesh.faces_select_linked_flat", text="Linked Flat Faces", icon = "LINKED")
        layout.operator("mesh.select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("mesh.select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True

        layout.separator()

        layout.operator("mesh.select_axis", text="Side of Active", icon = "SELECT_SIDEOFACTIVE")
        layout.operator("mesh.select_mirror", text="Mirror Selection", icon = "TRANSFORM_MIRROR")

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_curve_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "curve.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.curve.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_edit_curve(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("curve.select_all", text="None").action = 'DESELECT'
        layout.operator("curve.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("curve.select_random", text= "Random", icon = "RANDOMIZE")
        layout.operator("curve.select_nth", icon = "CHECKER_DESELECT")
        layout.operator("curve.select_linked", text="Linked", icon = "LINKED")
        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")

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

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("curve.select_all", text="None").action = 'DESELECT'
        layout.operator("curve.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("curve.select_random", text= "Random", icon = "RANDOMIZE")
        layout.operator("curve.select_nth", icon = "CHECKER_DESELECT")
        layout.operator("curve.select_linked", text="Linked", icon = "LINKED")
        layout.operator("curve.select_similar", text="Similar")

        layout.separator()

        layout.operator("curve.select_row", text = "Control Point row", icon = "CONTROLPOINTROW")

        layout.separator()

        layout.operator("curve.select_more", text= "More", icon = "SELECTMORE")
        layout.operator("curve.select_less", text= "Less", icon = "SELECTLESS")

class VIEW3D_MT_select_edit_text(Menu):
    # intentional name mismatch
    # select menu for 3d-text doesn't make sense
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.text_cut", text="Cut", icon = "CUT")
        layout.operator("font.text_copy", text="Copy", icon='COPYDOWN')
        layout.operator("font.text_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("font.text_paste_from_file", icon = "PASTEFILE")

        layout.separator()

        layout.operator("font.select_all", icon = "SELECT_ALL")

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_metaball_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_edit_metaball(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("mball.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("mball.select_all", text="None").action = 'DESELECT'
        layout.operator("mball.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("mball.select_random_metaelems", text = "Random", icon = "RANDOMIZE")

        layout.separator()

        layout.menu("VIEW3D_MT_select_edit_metaball_select_similar")

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
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "lattice.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.lattice.select_all(action = 'INVERT')
        return {'FINISHED'}


class VIEW3D_MT_select_edit_lattice(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("lattice.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("lattice.select_all", text="None").action = 'DESELECT'
        layout.operator("lattice.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("lattice.select_mirror", text = "Mirror", icon = "TRANSFORM_MIRROR")
        layout.operator("lattice.select_random", text = "Random", icon = "RANDOMIZE")

        layout.separator()

        layout.operator("lattice.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("lattice.select_less", text = "Less", icon = "SELECTLESS")

        layout.separator()

        layout.operator("lattice.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")


# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_armature_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "armature.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.armature.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_edit_armature(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("armature.select_all", text="None").action = 'DESELECT'
        layout.operator("armature.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("armature.select_mirror", text="Mirror", icon = "TRANSFORM_MIRROR").extend = False

        layout.separator()

        layout.operator("armature.select_more", text="More", icon = "SELECTMORE")
        layout.operator("armature.select_less", text="Less", icon = "SELECTLESS")

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

        layout.operator_menu_enum("armature.select_similar", "type", text="Similar")
        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")


class VIEW3D_MT_select_gpencil(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("gpencil.select_all", text="None").action = 'DESELECT'
        layout.operator("gpencil.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("gpencil.select_box", icon='BORDER_RECT')
        layout.operator("gpencil.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("gpencil.select_linked", text="Linked", icon = "LINKED")
        layout.operator("gpencil.select_alternate")
        layout.menu("VIEW3D_MT_select_gpencil_grouped", text="Grouped")

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
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.face_select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.face_select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_paint_mask(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.face_select_all", text="All", icon = 'SELECT_ALL').action = 'SELECT'
        layout.operator("paint.face_select_all", text="None").action = 'DESELECT'
        layout.operator("paint.face_select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()
        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon = 'BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("paint.face_select_linked", text="Linked", icon = "LINKED")


# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_vertex_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.vert_select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.vert_select_all(action = 'INVERT')
        return {'FINISHED'}


class VIEW3D_MT_select_paint_mask_vertex(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.vert_select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("paint.vert_select_all", text="None").action = 'DESELECT'
        layout.operator("paint.vert_select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("view3d.select_lasso", icon='BORDER_LASSO').mode = 'ADD'
        layout.operator("view3d.select_box", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

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

    def draw(self, context):
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

    def draw(self, context):
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

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("surface.primitive_nurbs_surface_curve_add", text="Nurbs Curve", icon='SURFACE_NCURVE')
        layout.operator("surface.primitive_nurbs_surface_circle_add", text="Nurbs Circle", icon='SURFACE_NCIRCLE')
        layout.operator("surface.primitive_nurbs_surface_surface_add", text="Nurbs Surface", icon='SURFACE_NSURFACE')
        layout.operator("surface.primitive_nurbs_surface_cylinder_add",
                        text="Nurbs Cylinder", icon='SURFACE_NCYLINDER')
        layout.operator("surface.primitive_nurbs_surface_sphere_add", text="Nurbs Sphere", icon='SURFACE_NSPHERE')
        layout.operator("surface.primitive_nurbs_surface_torus_add", text="Nurbs Torus", icon='SURFACE_NTORUS')


class VIEW3D_MT_metaball_add(Menu):
    bl_idname = "VIEW3D_MT_metaball_add"
    bl_label = "Metaball"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.metaball_add", "type")


class TOPBAR_MT_edit_curve_add(Menu):
    bl_idname = "TOPBAR_MT_edit_curve_add"
    bl_label = "Add"

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

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("armature.bone_primitive_add", text="Single Bone", icon='BONE_DATA')


class VIEW3D_MT_armature_add(Menu):
    bl_idname = "VIEW3D_MT_armature_add"
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.armature_add", text="Single Bone", icon='BONE_DATA')


class VIEW3D_MT_light_add(Menu):
    bl_idname = "VIEW3D_MT_light_add"
    bl_label = "Light"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.light_add", "type")


class VIEW3D_MT_lightprobe_add(Menu):
    bl_idname = "VIEW3D_MT_lightprobe_add"
    bl_label = "Light Probe"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.lightprobe_add", "type")


class VIEW3D_MT_camera_add(Menu):
    bl_idname = "VIEW3D_MT_camera_add"
    bl_label = "Camera"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.camera_add", text="Camera", icon='OUTLINER_OB_CAMERA')


class VIEW3D_MT_add(Menu):
    bl_label = "Add"

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
        layout.operator_menu_enum("object.gpencil_add", "type", text="Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')
        layout.separator()

        layout.menu("VIEW3D_MT_armature_add", icon='OUTLINER_OB_ARMATURE')
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

    def draw(self, context):
        layout = self.layout
        layout.operator("object.load_reference_image", text="Reference", icon='IMAGE_REFERENCE')
        layout.operator("object.load_background_image", text="Background", icon='IMAGE_BACKGROUND')


class VIEW3D_MT_object_relations(Menu):
    bl_label = "Relations"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.proxy_make", text="Make Proxy", icon='MAKE_PROXY')

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
        layout.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text = "Origin to Center of Mass (Volume)").type='ORIGIN_CENTER_OF_VOLUME'


# ********** Object menu **********

# Workaround to separate the tooltips
class VIEW3D_MT_object_delete_global(bpy.types.Operator):
    """Delete global\nDeletes the selected object(s) globally in all opened scenes"""      # blender will use this as a tooltip for menu items and buttons.
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
        layout.menu("VIEW3D_MT_object_collection")
        layout.menu("VIEW3D_MT_object_relations")
        layout.menu("VIEW3D_MT_object_constraints")
        layout.menu("VIEW3D_MT_object_track")
        layout.menu("VIEW3D_MT_make_links", text="Make Links")

        layout.separator()

        layout.operator("object.shade_smooth", icon ='SHADING_SMOOTH')
        layout.operator("object.shade_flat", icon ='SHADING_FLAT')

        layout.separator()

        layout.menu("VIEW3D_MT_object_animation")
        layout.menu("VIEW3D_MT_object_rigid_body")

        layout.separator()

        layout.menu("VIEW3D_MT_object_quick_effects")

        layout.separator()

        layout.operator_menu_enum("object.convert", "target")

        layout.separator()

        layout.menu("VIEW3D_MT_object_showhide")


class VIEW3D_MT_object_animation(Menu):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe", icon= 'KEYFRAMES_INSERT')
        layout.operator("anim.keyframe_delete_v3d", text="Delete Keyframes", icon= 'KEYFRAMES_REMOVE')
        layout.operator("anim.keyframe_clear_v3d", text="Clear Keyframes", icon= 'KEYFRAMES_CLEAR')
        layout.operator("anim.keying_set_active_set", text="Change Keying Set", icon='TRIA_RIGHT')

        layout.separator()

        layout.operator("nla.bake", text="Bake Action", icon= 'BAKE_ACTION')


class VIEW3D_MT_object_rigid_body(Menu):
    bl_label = "Rigid Body"

    def draw(self, context):
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

    def draw(self, context):
        layout = self.layout

        layout.operator("object.location_clear", text="Location", icon = "CLEARMOVE").clear_delta = False
        layout.operator("object.rotation_clear", text="Rotation", icon = "CLEARROTATE").clear_delta = False
        layout.operator("object.scale_clear", text="Scale", icon = "CLEARSCALE").clear_delta = False

        layout.separator()

        layout.operator("object.origin_clear", text="Origin", icon = "CLEARORIGIN")


class VIEW3D_MT_object_specials(Menu):
    bl_label = "Object Context Menu"

    def draw(self, context):

        layout = self.layout
        view = context.space_data

        obj = context.object
        is_eevee = context.scene.render.engine == 'BLENDER_EEVEE'

        selected_objects_len = len(context.selected_objects)

        # If nothing is selected
        # (disabled for now until it can be made more useful).
        '''
        if selected_objects_len == 0:

            layout.menu("VIEW3D_MT_add", text="Add")
            layout.operator("view3d.pastebuffer", text="Paste Objects", icon='PASTEDOWN')

            return
        '''

        # If something is selected

        if obj is None:
            pass
        elif obj.type == 'MESH':

            layout.operator("object.shade_smooth", text="Shade Smooth")
            layout.operator("object.shade_flat", text="Shade Flat")

            layout.separator()

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator_menu_enum("object.origin_set", text="Set Origin", property="type")

            layout.operator_context = 'INVOKE_DEFAULT'
            # If more than one object is selected
            if selected_objects_len > 1:
                layout.operator("object.join")

        elif obj.type == 'CAMERA':
            layout.operator_context = 'INVOKE_REGION_WIN'

            if obj.data.type == 'PERSP':
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Angle")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.lens"
                props.input_scale = 0.1
                if obj.data.lens_unit == 'MILLIMETERS':
                    props.header_text = "Camera Lens Angle: %.1fmm"
                else:
                    props.header_text = "Camera Lens Angle: %.1f\u00B0"

            else:
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Scale")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.ortho_scale"
                props.input_scale = 0.01
                props.header_text = "Camera Lens Scale: %.3f"

            if not obj.data.dof_object:
                if view and view.camera == obj and view.region_3d.view_perspective == 'CAMERA':
                    props = layout.operator("ui.eyedropper_depth", text="DOF Distance (Pick)")
                else:
                    props = layout.operator("wm.context_modal_mouse", text="DOF Distance")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.dof_distance"
                    props.input_scale = 0.02
                    props.header_text = "DOF Distance: %.3f"

        elif obj.type in {'CURVE', 'FONT'}:
            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Extrude Size")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.extrude"
            props.input_scale = 0.01
            props.header_text = "Extrude Size: %.3f"

            props = layout.operator("wm.context_modal_mouse", text="Width Size")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.offset"
            props.input_scale = 0.01
            props.header_text = "Width Size: %.3f"

            layout.operator("object.convert", text="Convert to Mesh").target = 'MESH'

            layout.operator_menu_enum("object.origin_set", text="Set Origin", property="type")

        elif obj.type == 'GPENCIL':
            layout.operator("gpencil.convert", text="Convert to Path").type = 'PATH'
            layout.operator("gpencil.convert", text="Convert to Bezier Curves").type = 'CURVE'
            layout.operator("gpencil.convert", text="Convert to Mesh").type = 'POLY'

            layout.operator_menu_enum("object.origin_set", text="Set Origin", property="type")

        elif obj.type == 'EMPTY':
            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Empty Draw Size")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "empty_display_size"
            props.input_scale = 0.01
            props.header_text = "Empty Draw Size: %.3f"

        elif obj.type == 'LIGHT':
            light = obj.data

            layout.operator_context = 'INVOKE_REGION_WIN'

            emission_node = None
            if light.node_tree:
                for node in light.node_tree.nodes:
                    if getattr(node, "type", None) == 'EMISSION':
                        emission_node = node
                        break

            if is_eevee and not emission_node:
                props = layout.operator("wm.context_modal_mouse", text="Energy")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.energy"
                props.header_text = "Light Energy: %.3f"

            if emission_node is not None:
                props = layout.operator("wm.context_modal_mouse", text="Energy")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = (
                    "data.node_tree"
                    ".nodes[\"" + emission_node.name + "\"]"
                    ".inputs[\"Strength\"].default_value"
                )
                props.header_text = "Light Energy: %.3f"
                props.input_scale = 0.1

            if light.type == 'AREA':
                props = layout.operator("wm.context_modal_mouse", text="Size X")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.size"
                props.header_text = "Light Size X: %.3f"

                if light.shape in {'RECTANGLE', 'ELLIPSE'}:
                    props = layout.operator("wm.context_modal_mouse", text="Size Y")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size_y"
                    props.header_text = "Light Size Y: %.3f"

            elif light.type in {'SPOT', 'POINT', 'SUN'}:
                props = layout.operator("wm.context_modal_mouse", text="Radius")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.shadow_soft_size"
                props.header_text = "Light Radius: %.3f"

            if light.type == 'SPOT':
                layout.separator()

                props = layout.operator("wm.context_modal_mouse", text="Spot Size")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.spot_size"
                props.input_scale = 0.01
                props.header_text = "Spot Size: %.2f"

                props = layout.operator("wm.context_modal_mouse", text="Spot Blend")
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

        layout.menu("VIEW3D_MT_snap")
        layout.menu("VIEW3D_MT_object_parent")
        layout.operator_context = 'INVOKE_REGION_WIN'

        if view and view.local_view:
            layout.operator("view3d.localview_remove_from")
        else:
            layout.operator("object.move_to_collection")

        layout.separator()

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe")

        layout.separator()

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("object.delete", text="Delete").use_global = False


class VIEW3D_MT_object_shading(Menu):
    # XXX, this menu is a place to store shading operator in object mode
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.shade_smooth", text="Smooth")
        layout.operator("object.shade_flat", text="Flat")


class VIEW3D_MT_object_apply(Menu):
    bl_label = "Apply"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("object.transform_apply", text="Location", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE") 
        props.location, props.rotation, props.scale = True, False, False

        props = layout.operator("object.transform_apply", text="Rotation", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
        props.location, props.rotation, props.scale = False, True, False

        props = layout.operator("object.transform_apply", text="Scale", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
        props.location, props.rotation, props.scale = False, False, True
        props = layout.operator("object.transform_apply", text="Rotation & Scale", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
        props.location, props.rotation, props.scale = False, True, True

        layout.separator()

        layout.operator("object.transforms_to_deltas", text="Location to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
        layout.operator("object.transforms_to_deltas", text="Rotation to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
        layout.operator("object.transforms_to_deltas", text="Scale to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'
        layout.operator("object.transforms_to_deltas", text="All Transforms to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'
        layout.operator("object.anim_transforms_to_deltas", icon = "APPLYANIDELTA")

        layout.separator()

        layout.operator("object.visual_transform_apply", text="Visual Transform", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
        layout.operator("object.convert", text="Visual Geometry to Mesh", text_ctxt=i18n_contexts.default,).target = 'MESH'
        layout.operator("object.duplicates_make_real", icon = "MAKEDUPLIREAL")


class VIEW3D_MT_object_parent(Menu):
    bl_label = "Parent"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("object.parent_set", "type")

        layout.separator()

        layout.operator_enum("object.parent_clear", "type")


class VIEW3D_MT_object_track(Menu):
    bl_label = "Track"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.track_set", text = "Damped Track Constraint", icon = "CONSTRAINT_DATA").type = "DAMPTRACK"
        layout.operator("object.track_set", text = "Track to Constraint", icon = "CONSTRAINT_DATA").type = "TRACKTO"
        layout.operator("object.track_set", text = "Lock Track Constraint", icon = "CONSTRAINT_DATA").type = "LOCKTRACK"

        layout.separator()

        layout.operator("object.track_clear", text= "Clear Track", icon = "CLEAR_TRACK").type = 'CLEAR'
        layout.operator("object.track_clear", text= "Clear Track - Keep Transformation", icon = "CLEAR_TRACK").type = 'CLEAR_KEEP_TRANSFORM'


class VIEW3D_MT_object_collection(Menu):
    bl_label = "Collection"

    def draw(self, context):
        layout = self.layout

        layout.operator("collection.create", icon='GROUP')
        # layout.operator_menu_enum("collection.objects_remove", "collection")  # BUGGY
        layout.operator("collection.objects_remove", icon = "DELETE")
        layout.operator("collection.objects_remove_all", icon = "DELETE")

        layout.separator()

        layout.operator("collection.objects_add_active", icon='GROUP')
        layout.operator("collection.objects_remove_active", icon = "DELETE")


class VIEW3D_MT_object_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.constraint_add_with_targets", icon = "CONSTRAINT_DATA")
        layout.operator("object.constraints_copy", icon = "COPYDOWN")

        layout.separator()

        layout.operator("object.constraints_clear", icon = "CLEAR_CONSTRAINT")


class VIEW3D_MT_object_quick_effects(Menu):
    bl_label = "Quick Effects"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.quick_fur", icon = "HAIR")
        layout.operator("object.quick_explode", icon = "MOD_EXPLODE")
        layout.operator("object.quick_smoke", icon = "MOD_SMOKE")
        layout.operator("object.quick_fluid", icon = "MOD_FLUIDSIM")


# Workaround to separate the tooltips for Show Hide
class VIEW3D_hide_view_set_unselected(bpy.types.Operator):
    """Hide Unselected\nHides the unselected Object(s)"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.hide_view_set(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_object_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.hide_view_clear", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")

        layout.separator()

        layout.operator("object.hide_view_set", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("object.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_make_single_user(Menu):
    bl_label = "Make Single User"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("object.make_single_user", text="Object")
        props.object = True
        props.obdata = props.material = props.animation = False

        props = layout.operator("object.make_single_user", text="Object & Data")
        props.object = props.obdata = True
        props.material = props.animation = False

        props = layout.operator("object.make_single_user", text="Object & Data & Materials")
        props.object = props.obdata = props.material = True
        props.animation = False

        props = layout.operator("object.make_single_user", text="Materials")
        props.material = True
        props.object = props.obdata = props.animation = False

        props = layout.operator("object.make_single_user", text="Object Animation")
        props.animation = True
        props.object = props.obdata = props.material = False


class VIEW3D_MT_make_links(Menu):
    bl_label = "Make Links"

    def draw(self, context):
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

        layout.operator("object.join_uvs")  # stupid place to add this!


class VIEW3D_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        settings = UnifiedPaintPanel.paint_settings(context)
        brush = getattr(settings, "brush", None)

        ups = tool_settings.unified_paint_settings
        layout.prop(ups, "use_unified_size", text="Unified Size")
        layout.prop(ups, "use_unified_strength", text="Unified Strength")
        if context.image_paint_object or context.vertex_paint_object:
            layout.prop(ups, "use_unified_color", text="Unified Color")
        layout.separator()

        # skip if no active brush
        if not brush:
            layout.label(text="No Brushes currently available", icon='INFO')
            return

        # brush paint modes
        layout.menu("VIEW3D_MT_brush_paint_modes")

        # brush tool
        if context.sculpt_object:
            layout.operator("brush.reset")
            layout.prop_menu_enum(brush, "sculpt_tool")
        elif context.image_paint_object:
            layout.prop_menu_enum(brush, "image_tool")
        elif context.vertex_paint_object:
            layout.prop_menu_enum(brush, "vertex_tool")
        elif context.weight_paint_object:
            layout.prop_menu_enum(brush, "weight_tool")

        # TODO: still missing a lot of brush options here

        # sculpt options
        if context.sculpt_object:

            sculpt_tool = brush.sculpt_tool

            layout.separator()
            layout.operator_menu_enum("brush.curve_preset", "shape", text="Curve Preset")
            layout.separator()

            if sculpt_tool != 'GRAB':
                layout.prop_menu_enum(brush, "stroke_method")

                if sculpt_tool in {'DRAW', 'PINCH', 'INFLATE', 'LAYER', 'CLAY'}:
                    layout.prop_menu_enum(brush, "direction")

                if sculpt_tool == 'LAYER':
                    layout.prop(brush, "use_persistent")
                    layout.operator("sculpt.set_persistent_base")

        layout.separator()

        layout.menu("VIEW3D_MT_facemask_showhide") ### show hide for face mask tool

        layout.operator("paint.sample_color", text = "Color Picker", icon='EYEDROPPER')

# Show hide menu for face selection masking
class VIEW3D_MT_facemask_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.face_select_reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("paint.face_select_hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("paint.face_select_hide", text="Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


class VIEW3D_MT_brush_paint_modes(Menu):
    bl_label = "Enabled Modes"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        layout.prop(brush, "use_paint_sculpt", text="Sculpt")
        layout.prop(brush, "use_paint_vertex", text="Vertex Paint")
        layout.prop(brush, "use_paint_weight", text="Weight Paint")
        layout.prop(brush, "use_paint_image", text="Texture Paint")


class VIEW3D_MT_paint_vertex(Menu):
    bl_label = "Paint"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.vertex_color_set", icon = "COLOR")
        layout.operator("paint.vertex_color_smooth", icon = "SMOOTH")
        layout.operator("paint.vertex_color_dirt", icon = "DIRTY_VERTEX")
        layout.operator("paint.vertex_color_from_weight", icon = "VERTCOLFROMWEIGHT")

        layout.separator()

        layout.operator("paint.vertex_color_invert", text="Invert", icon = "REVERSE_COLORS")
        layout.operator("paint.vertex_color_levels", text="Levels", icon = "LEVELS")
        layout.operator("paint.vertex_color_hsv", text="Hue Saturation Value", icon = "HUESATVAL")
        layout.operator("paint.vertex_color_brightness_contrast", text="Bright/Contrast", icon = "BRIGHTNESS_CONTRAST")



class VIEW3D_MT_hook(Menu):
    bl_label = "Hooks"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.hook_add_newob", icon = "HOOK_NEW")
        layout.operator("object.hook_add_selob", icon = "HOOK_SELECTED").use_bone = False
        layout.operator("object.hook_add_selob", text="Hook to Selected Object Bone", icon = "HOOK_BONE").use_bone = True

        if [mod.type == 'HOOK' for mod in context.active_object.modifiers]:
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
        layout.operator("object.vertex_group_assign_new")

        ob = context.active_object
        if ob.mode == 'EDIT' or (ob.mode == 'WEIGHT_PAINT' and ob.type == 'MESH' and ob.data.use_paint_mask_vertex):
            if ob.vertex_groups.active:
                layout.separator()

                layout.operator("object.vertex_group_assign", text="Assign to Active Group")
                layout.operator("object.vertex_group_remove_from", text="Remove from Active Group",).use_all_groups = False
                layout.operator("object.vertex_group_remove_from", text="Remove from All").use_all_groups = True

        if ob.vertex_groups.active:
            layout.separator()

            layout.operator_menu_enum("object.vertex_group_set_active", "group", text="Set Active Group")
            layout.operator("object.vertex_group_remove", text="Remove Active Group", icon = "REMOVE_ACTIVE_GROUP").all = False
            layout.operator("object.vertex_group_remove", text="Remove All Groups", icon = "REMOVE_ALL_GROUPS").all = True


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

    def draw(self, context):
        self.draw_generic(self.layout, is_editmode=False)


class VIEW3D_MT_sculpt(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        sculpt = tool_settings.sculpt

        layout.prop(sculpt, "use_symmetry_x")
        layout.prop(sculpt, "use_symmetry_y")
        layout.prop(sculpt, "use_symmetry_z")

        layout.separator()

        layout.prop(sculpt, "lock_x")
        layout.prop(sculpt, "lock_y")
        layout.prop(sculpt, "lock_z")

        layout.separator()

        layout.prop(sculpt, "use_threaded", text="Threaded Sculpt")
        layout.prop(sculpt, "show_low_resolution")
        layout.prop(sculpt, "show_brush")
        layout.prop(sculpt, "use_deform_only")
        layout.prop(sculpt, "show_diffuse_color")
        layout.prop(sculpt, "show_mask")


class VIEW3D_MT_hide_mask(Menu):
    bl_label = "Hide/Mask"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("paint.hide_show", text="Show All", icon = "RESTRICT_VIEW_OFF")
        props.action = 'SHOW'
        props.area = 'ALL'

        props = layout.operator("paint.hide_show", text="Hide Bounding Box", icon = "RESTRICT_VIEW_ON")
        props.action = 'HIDE'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Show Bounding Box", icon = "RESTRICT_VIEW_OFF")
        props.action = 'SHOW'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Hide Masked", icon = "RESTRICT_VIEW_ON")
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
            layout.operator("particle.subdivide")

        layout.operator("particle.unify_length", icon = "RULER")
        layout.operator("particle.rekey", icon = "KEY_HLT")
        layout.operator("particle.weight_set", icon = "MOD_VERTEX_WEIGHT")

        layout.separator()

        layout.menu("VIEW3D_MT_particle_show_hide")

        layout.separator()

        layout.operator("particle.delete", icon = "DELETE")


class VIEW3D_MT_particle_specials(Menu):
    bl_label = "Particle Context Menu"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        particle_edit = tool_settings.particle_edit

        layout.operator("particle.rekey")

        layout.separator()

        layout.operator("particle.delete")

        layout.separator()

        layout.operator("particle.remove_doubles")
        layout.operator("particle.unify_length")

        if particle_edit.select_mode == 'POINT':
            layout.operator("particle.subdivide")

        layout.operator("particle.weight_set")

        layout.separator()

        layout.operator("particle.mirror")

        if particle_edit.select_mode == 'POINT':
            layout.separator()

            layout.operator("particle.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
            layout.operator("particle.select_all", text="None").action = 'DESELECT'
            layout.operator("particle.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

            layout.separator()

            layout.operator("particle.select_roots")
            layout.operator("particle.select_tips")

            layout.separator()

            layout.operator("particle.select_random", icon = "RANDOMIZE")

            layout.separator()

            layout.operator("particle.select_more", icon = "SELECTMORE")
            layout.operator("particle.select_less", icon = "SELECTLESS")

            layout.separator()

            layout.operator("particle.select_linked", icon = "LINKED")


# Workaround to separate the tooltips for Show Hide for Particles in Particle mode
class VIEW3D_particle_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide the unselected Particles"""      # blender will use this as a tooltip for menu items and buttons.
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

        layout.operator("particle.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("particle.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("particle.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip

class VIEW3D_MT_pose(Menu):
    bl_label = "Pose"

    def draw(self, context):
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

        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.autoside_names", text="AutoName Left/Right", icon = "STRING").axis = 'XAXIS'
        layout.operator("pose.autoside_names", text="AutoName Front/Back", icon = "STRING").axis = 'YAXIS'
        layout.operator("pose.autoside_names", text="AutoName Top/Bottom", icon = "STRING").axis = 'ZAXIS'

        layout.operator("pose.flip_names", icon = "FLIP")
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

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.transforms_clear", text="All")

        layout.separator()

        layout.operator("pose.loc_clear", text="Location")
        layout.operator("pose.rot_clear", text="Rotation")
        layout.operator("pose.scale_clear", text="Scale")

        layout.separator()

        layout.operator("pose.user_transforms_clear", text="Reset Unkeyed")


class VIEW3D_MT_pose_slide(Menu):
    bl_label = "In-Betweens"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.push", icon = 'PUSH_POSE')
        layout.operator("pose.relax", icon = 'RELAX_POSE')
        layout.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE')


class VIEW3D_MT_pose_propagate(Menu):
    bl_label = "Propagate"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.propagate").mode = 'WHILE_HELD'

        layout.separator()

        layout.operator("pose.propagate", text="To Next Keyframe").mode = 'NEXT_KEY'
        layout.operator("pose.propagate", text="To Last Keyframe (Make Cyclic)").mode = 'LAST_KEY'

        layout.separator()

        layout.operator("pose.propagate", text="On Selected Keyframes", icon = "PROPAGATE").mode = 'SELECTED_KEYS'

        layout.separator()

        layout.operator("pose.propagate", text="On Selected Markers", icon = "PROPAGATE").mode = 'SELECTED_MARKERS'


class VIEW3D_MT_pose_library(Menu):
    bl_label = "Pose Library"

    def draw(self, context):
        layout = self.layout

        layout.operator("poselib.browse_interactive", text="Browse Poses")

        layout.separator()

        layout.operator("poselib.pose_add", text="Add Pose", icon = "LIBRARY")
        layout.operator("poselib.pose_rename", text="Rename Pose", icon = "STRING")
        layout.operator("poselib.pose_remove", text="Remove Pose", icon = "DELETE")


class VIEW3D_MT_pose_motion(Menu):
    bl_label = "Motion Paths"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.paths_calculate", text="Calculate")
        layout.operator("pose.paths_clear", text="Clear")


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

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.ik_add", icon= "ADD_IK")
        layout.operator("pose.ik_clear", icon = "CLEAR_IK")


class VIEW3D_MT_pose_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.constraint_add_with_targets", text="Add (With Targets)", icon = "CONSTRAINT_DATA")
        layout.operator("pose.constraints_copy", icon = "COPYDOWN")
        layout.operator("pose.constraints_clear", icon = "CLEAR_CONSTRAINT")


# Workaround to separate the tooltips for Show Hide for Armature in Pose mode
class VIEW3D_MT_pose_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected Bones"""      # blender will use this as a tooltip for menu items and buttons.
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

        layout.operator("pose.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("pose.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("pose.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_pose_apply(Menu):
    bl_label = "Apply"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.armature_apply", icon = "MOD_ARMATURE")
        layout.operator("pose.visual_transform_apply", icon = "APPLYMOVE")

        layout.separator()

        props = layout.operator("object.assign_property_defaults")
        props.process_bones = True


class VIEW3D_MT_pose_specials(Menu):
    bl_label = "Pose Context Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe")

        layout.separator()

        layout.operator("pose.copy", icon='COPYDOWN')
        layout.operator("pose.paste", icon='PASTEDOWN').flipped = False
        layout.operator("pose.paste", icon='PASTEFLIPDOWN', text="Paste X-Flipped Pose").flipped = True

        layout.separator()

        layout.operator("pose.paths_calculate", text="Calculate")
        layout.operator("pose.paths_clear", text="Clear")

        layout.separator()

        layout.operator("pose.push")
        layout.operator("pose.relax")
        layout.operator("pose.breakdown")

        layout.separator()

        layout.operator("pose.paths_calculate")
        layout.operator("pose.paths_clear")

        layout.separator()

        layout.operator("pose.hide").unselected = False
        layout.operator("pose.reveal")

        layout.separator()

        layout.operator("pose.user_transforms_clear")


class BoneOptions:
    def draw(self, context):
        layout = self.layout

        options = [
            "show_wire",
            "use_deform",
            "use_envelope_multiply",
            "use_inherit_rotation",
            "use_inherit_scale",
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

    def draw(self, context):
        layout = self.layout

        with_bullet = bpy.app.build_options.bullet

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mesh.duplicate_move", text="Duplicate", icon = "DUPLICATE")
        layout.menu("VIEW3D_MT_edit_mesh_extrude")
        layout.operator("mesh.split", icon = "SPLIT")
        layout.operator("mesh.bisect", icon = 'BISECT')
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

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_show_hide")
        layout.operator_menu_enum("mesh.separate", "type")
        layout.menu("VIEW3D_MT_edit_mesh_clean")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_delete")

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


class VIEW3D_MT_edit_mesh_specials(Menu):
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
            layout.menu("VIEW3D_MT_mesh_add", text="Add")

            return
        '''

        # Else something is selected

        row = layout.row()

        if is_vert_mode:
            col = row.column()

            col.label(text="Vertex Context Menu", icon='VERTEXSEL')
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide")

            col.separator()

            col.operator("mesh.extrude_vertices_move", text="Extrude Vertices", icon='EXTRUDE_REGION')
            col.operator("mesh.bevel", text="Bevel Vertices").vertex_only = True

            if selected_verts_len > 1:
                col.separator()
                col.operator("mesh.edge_face_add", text="New Edge/Face from Vertices")
                col.operator("mesh.vert_connect_path", text="Connect Vertex Path")
                col.operator("mesh.vert_connect", text="Connect Vertex Pairs")

            col.separator()

            # Deform Operators
            col.operator("transform.push_pull", text="Push/Pull")
            col.operator("transform.shrink_fatten", text="Shrink/Fatten")
            col.operator("transform.shear", text="Shear")
            col.operator("transform.vert_slide", text="Slide Vertices")
            col.operator("transform.vertex_random", text="Randomize Vertices")
            col.operator("mesh.vertices_smooth", text="Smooth Vertices")
            col.operator("mesh.vertices_smooth_laplacian", text="Smooth Laplacian")

            col.separator()

            col.menu("VIEW3D_MT_snap", text="Snap Vertices")
            col.operator("transform.mirror", text="Mirror Vertices")

            col.separator()

            # Removal Operators
            if selected_verts_len > 1:
                col.operator("mesh.merge", text="Merge Vertices")
                col.operator("mesh.remove_doubles", text="Remove Double Vertices")
            col.operator("mesh.dissolve_verts")
            col.operator("mesh.delete", text="Delete Vertices", icon = "DELETE").type = 'VERT'

        if is_edge_mode:
            render = context.scene.render

            col = row.column()
            col.label(text="Edge Context Menu", icon='EDGESEL')
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide")

            col.separator()

            col.operator("mesh.extrude_edges_move", text="Extrude Edges", icon='EXTRUDE_REGION'),
            col.operator("mesh.bevel", text="Bevel Edges").vertex_only = False
            if selected_edges_len >= 2:
                col.operator("mesh.bridge_edge_loops")

            col.separator()

            col.operator("mesh.loopcut_slide")
            col.operator("mesh.offset_edge_loops_slide")
            col.operator("mesh.knife_tool")
            col.operator("mesh.bisect")
            col.operator("mesh.bridge_edge_loops", text="Bridge Edge Loops")

            col.separator()

            # Deform Operators
            col.operator("mesh.edge_rotate", text="Rotate Edge CW").use_ccw = False
            col.operator("transform.edge_slide")
            col.operator("mesh.edge_split")

            col.separator()

            # Edge Flags
            col.operator("transform.edge_crease")
            col.operator("transform.edge_bevelweight")

            col.separator()

            col.operator("mesh.mark_seam").clear = False
            col.operator("mesh.mark_seam", text="Clear Seam").clear = True

            col.separator()

            col.operator("mesh.mark_sharp")
            col.operator("mesh.mark_sharp", text="Clear Sharp").clear = True

            if render.use_freestyle:
                col.separator()

                col.operator("mesh.mark_freestyle_edge").clear = False
                col.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge").clear = True

            col.separator()

            # Removal Operators
            col.operator("mesh.unsubdivide")
            col.operator("mesh.dissolve_edges")
            col.operator("mesh.delete", text="Delete Edges", icon = "DELETE").type = 'EDGE'

        if is_face_mode:
            col = row.column()

            col.label(text="Face Context Menu", icon='FACESEL')
            col.separator()

            # Additive Operators
            col.operator("mesh.subdivide", text="Subdivide")

            col.separator()

            col.operator("view3d.edit_mesh_extrude_move_normal", text="Extrude Faces", icon = 'EXTRUDE_REGION'),
            col.operator("view3d.edit_mesh_extrude_move_shrink_fatten", text="Extrude Faces Along Normals", icon = 'EXTRUDE_REGION'),
            col.operator("mesh.extrude_faces_move", text="Extrude Individual Faces", icon = 'EXTRUDE_REGION'),

            col.operator("mesh.inset"),
            col.operator("mesh.poke")

            if selected_faces_len >= 2:
                col.operator("mesh.bridge_edge_loops", text="Bridge Faces")

            col.separator()

            # Modify Operators
            col.menu("VIEW3D_MT_uv_map", text="UV Unwrap Faces")

            col.separator()

            props = col.operator("mesh.quads_convert_to_tris")
            props.quad_method = props.ngon_method = 'BEAUTY'
            col.operator("mesh.tris_convert_to_quads")

            col.separator()

            col.operator("mesh.faces_shade_smooth")
            col.operator("mesh.faces_shade_flat")

            col.separator()

            # Removal Operators
            col.operator("mesh.unsubdivide")
            col.operator("mesh.dissolve_faces")
            col.operator("mesh.delete", text="Delete Faces", icon = "DELETE").type = 'FACE'


class VIEW3D_MT_edit_mesh_select_mode(Menu):
    bl_label = "Mesh Select Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.select_mode", text="Vertex", icon='VERTEXSEL').type = 'VERT'
        layout.operator("mesh.select_mode", text="Edge", icon='EDGESEL').type = 'EDGE'
        layout.operator("mesh.select_mode", text="Face", icon='FACESEL').type = 'FACE'


class VIEW3D_MT_edit_mesh_extrude(Menu):
    bl_label = "Extrude"

    _extrude_funcs = {
        'VERT': lambda layout:
            layout.operator("mesh.extrude_vertices_move", text="Extrude Vertices", icon='EXTRUDE_REGION'),
        'EDGE': lambda layout:
            layout.operator("mesh.extrude_edges_move", text="Extrude Edges", icon='EXTRUDE_REGION'),
        'REGION': lambda layout:
            layout.operator("view3d.edit_mesh_extrude_move_normal", text="Extrude Faces", icon='EXTRUDE_REGION'),
        'REGION_VERT_NORMAL': lambda layout:
            layout.operator("view3d.edit_mesh_extrude_move_shrink_fatten", text="Extrude Faces Along Normals", icon='EXTRUDE_REGION'),
        'FACE': lambda layout:
            layout.operator("mesh.extrude_faces_move", text="Extrude Individual Faces", icon='EXTRUDE_REGION'),
    }

    @staticmethod
    def extrude_options(context):
        tool_settings = context.tool_settings
        select_mode = tool_settings.mesh_select_mode
        mesh = context.object.data

        menu = []
        if mesh.total_face_sel:
            menu += ['REGION', 'REGION_VERT_NORMAL', 'FACE']
        if mesh.total_edge_sel and (select_mode[0] or select_mode[1]):
            menu += ['EDGE']
        if mesh.total_vert_sel and select_mode[0]:
            menu += ['VERT']

        # should never get here
        return menu

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        for menu_id in self.extrude_options(context):
            self._extrude_funcs[menu_id](layout)


class VIEW3D_MT_edit_mesh_vertices(Menu):
    bl_label = "Vertex"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.extrude_vertices_move", text="Extrude Vertices", icon = 'EXTRUDE_REGION')
        layout.operator("mesh.bevel", text="Bevel Vertices", icon='BEVEL').vertex_only = True

        layout.separator()

        layout.operator("mesh.edge_face_add", text="New Edge/Face from Vertices", icon='MAKE_EDGEFACE')
        layout.operator("mesh.vert_connect_path", text = "Connect Vertex Path", icon = "VERTEXCONNECTPATH")
        layout.operator("mesh.vert_connect", text = "Connect Vertex Pairs", icon = "VERTEXCONNECT")

        layout.separator()

        props = layout.operator("mesh.rip_move", text="Rip Vertices", icon = "RIP")
        props.MESH_OT_rip.use_fill = False
        props = layout.operator("mesh.rip_move", text="Rip Vertices and Fill", icon = "RIP_FILL")
        props.MESH_OT_rip.use_fill = True
        layout.operator("mesh.rip_edge_move", text="Rip Vertices and Extend", icon = "EXTEND_VERTICES")

        layout.separator()

        layout.operator("transform.vert_slide", text="Slide Vertices", icon = 'SLIDE_VERTEX')
        layout.operator("mesh.vertices_smooth", text="Smooth Vertices", icon = 'SMOOTH_VERTEX')

        layout.separator()

        layout.operator("mesh.blend_from_shape", icon = "BLENDFROMSHAPE")
        layout.operator("mesh.shape_propagate_to_all", text="Propagate to Shapes", icon = "SHAPEPROPAGATE")

        layout.separator()

        layout.operator("mesh.merge", text="Merge Vertices", icon = "MERGE")
        layout.operator("mesh.remove_doubles", text="Remove Double Vertices", icon = 'REMOVE_DOUBLES')

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

        layout.operator("mesh.extrude_edges_move", text="Extrude Edges", icon = 'EXTRUDE_REGION'),
        layout.operator("mesh.bevel", text="Bevel Edges", icon='BEVEL').vertex_only = False
        layout.operator("mesh.bridge_edge_loops", icon = "BRIDGE_EDGELOOPS")

        layout.separator()

        layout.operator("mesh.subdivide", icon='SUBDIVIDE_EDGES')
        layout.operator("mesh.subdivide_edgering", icon = "SUBDIV_EDGERING")
        layout.operator("mesh.unsubdivide", icon = "UNSUBDIVIDE")

        layout.separator()

        layout.operator("mesh.edge_rotate", text="Rotate Edge CW", icon = "ROTATECW").use_ccw = False
        layout.operator("mesh.edge_rotate", text="Rotate Edge CCW", icon = "ROTATECW").use_ccw = True

        layout.separator()

        layout.operator("transform.edge_slide", icon='SLIDE_EDGE')
        layout.operator("mesh.edge_split", icon = "SPLITEDGE")

        layout.separator()

        layout.operator("transform.edge_crease", icon = "CREASE")
        layout.operator("transform.edge_bevelweight", icon = "BEVEL")

        layout.separator()

        layout.operator("mesh.mark_seam", icon = 'MARK_SEAM').clear = False
        layout.operator("mesh.mark_seam", text="Clear Seam", icon = 'CLEAR_SEAM').clear = True

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

    def draw(self, context):
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

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("view3d.edit_mesh_extrude_move_normal", text="Extrude Faces", icon = 'EXTRUDE_REGION')
        layout.operator("view3d.edit_mesh_extrude_move_shrink_fatten", text="Extrude Faces Along Normals", icon = 'SHRINK_FATTEN')
        layout.operator("mesh.extrude_faces_move", text="Extrude Individual Faces", icon = 'EXTRUDE_REGION')

        layout.separator()

        layout.operator("mesh.inset", icon='INSET_FACES')
        layout.operator("mesh.poke", icon = "POKEFACES")
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

        layout.operator("mesh.faces_shade_smooth", icon = 'SHADING_SMOOTH')
        layout.operator("mesh.faces_shade_flat", icon = 'SHADING_FLAT')

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_faces_data")


# Workaround to separate the tooltips for Recalculate Outside and Recalculate Inside
class VIEW3D_normals_make_consistent_inside(bpy.types.Operator):
    """Recalculate Normals Inside\nMake selected faces and normals point inside the mesh"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.normals_recalculate_inside"        # unique identifier for buttons and menu items to reference.
    bl_label = "Recalculate Inside"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.normals_make_consistent(inside=True)
        return {'FINISHED'}


class VIEW3D_MT_edit_mesh_normals(Menu):
    bl_label = "Normals"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.normals_make_consistent", text="Recalculate Outside", icon = 'RECALC_NORMALS').inside = False
        layout.operator("mesh.normals_recalculate_inside", text="Recalculate Inside", icon = 'RECALC_NORMALS_INSIDE') # bfa - separated tooltip

        layout.separator()

        layout.operator("mesh.flip_normals", icon = 'FLIP_NORMALS')
        layout.operator("mesh.set_normals_from_faces", text="Set From Faces", icon = 'SET_FROM_FACES')

        layout.operator("transform.rotate_normal", text="Rotate Normal")
        layout.operator("mesh.point_normals", text="Point normals to target")

        layout.operator("mesh.merge_normals", text="Merge")
        layout.operator("mesh.split_normals", text="Split")

        layout.operator("mesh.average_normals", text="Average Normals")

        layout.label(text="Normal Vector")

        layout.operator("mesh.normals_tools", text="Copy").mode = 'COPY'
        layout.operator("mesh.normals_tools", text="Paste").mode = 'PASTE'

        layout.operator("mesh.normals_tools", text="Multiply").mode = 'MULTIPLY'
        layout.operator("mesh.normals_tools", text="Add").mode = 'ADD'

        layout.operator("mesh.normals_tools", text="Reset").mode = 'RESET'

        layout.operator("mesh.smoothen_normals", text="Smoothen")

        layout.label(text="Face Strength")
        layout.operator("mesh.mod_weighted_strength", text="Face Select", icon='FACESEL').set = False
        layout.operator("mesh.mod_weighted_strength", text="Set Strength", icon='ADD').set = True


class VIEW3D_MT_edit_mesh_shading(Menu):
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.faces_shade_smooth", text="Smooth Faces", icon = 'SHADING_SMOOTH')
        layout.operator("mesh.faces_shade_flat", text="Flat Faces", icon = 'SHADING_FLAT')

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

    def draw(self, context):
        VIEW3D_MT_paint_weight.draw_generic(self.layout, is_editmode=True)


class VIEW3D_MT_edit_mesh_clean(Menu):
    bl_label = "Clean Up"

    def draw(self, context):
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
        layout.operator("mesh.remove_doubles", icon = "REMOVE_DOUBLES")
        layout.operator("mesh.fill_holes", icon = "FILL_HOLE")


class VIEW3D_MT_edit_mesh_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("mesh.delete", "type")

        layout.separator()

        layout.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS')
        layout.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES')
        layout.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES')

        layout.separator()

        layout.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED') 

        layout.separator()

        layout.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE')
        layout.operator("mesh.delete_edgeloop", text="Edge Loops", icon = "DELETE")


# Workaround to separate the tooltips for Show Hide for Mesh in Edit Mode
class VIEW3D_mesh_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected geometry in Edit Mode"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.hide(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_edit_mesh_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("mesh.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("mesh.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_edit_gpencil_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("gpencil.delete", "type")

        layout.separator()

        layout.operator_enum("gpencil.dissolve", "type")

        layout.separator()

        layout.operator("gpencil.active_frames_delete_all", icon = "DELETE")
# Edit Curve
# draw_curve is used by VIEW3D_MT_edit_curve and VIEW3D_MT_edit_surface


def draw_curve(self, context):
    layout = self.layout

    layout.menu("VIEW3D_MT_transform")
    layout.menu("VIEW3D_MT_mirror")
    layout.menu("VIEW3D_MT_snap")

    layout.separator()

    layout.operator("curve.spin", icon = 'SPIN')
    layout.operator("curve.duplicate_move", icon = "DUPLICATE")

    layout.separator()

    layout.operator("curve.split", icon = "SPLIT")
    layout.operator("curve.separate", icon = "SEPARATE")
    layout.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC')
    layout.operator("curve.decimate", icon = "DECIMATE")
    layout.operator_menu_enum("curve.spline_type_set", "type")

    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_show_hide")
    layout.menu("VIEW3D_MT_edit_curve_delete")


class VIEW3D_MT_edit_curve(Menu):
    bl_label = "Curve"

    draw = draw_curve


class VIEW3D_MT_edit_curve_ctrlpoints(Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type in {'CURVE', 'SURFACE'}:
            layout.operator("curve.extrude_move", icon = 'EXTRUDE_REGION')

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
        layout.operator("curve.handle_type_set", icon = 'HANDLE_ALIGN',text="Aligned").type = 'ALIGNED'
        layout.operator("curve.handle_type_set", icon = 'HANDLE_FREE', text="Free").type = 'FREE_ALIGN'

        layout.separator()

        layout.operator("curve.handle_type_set", icon = 'HANDLE_FREE', text="Toggle Free / Aligned").type = 'TOGGLE_FREE_ALIGN'


class VIEW3D_MT_edit_curve_segments(Menu):
    bl_label = "Segments"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.subdivide", icon = 'SUBDIVIDE_EDGES')
        layout.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION')


class VIEW3D_MT_edit_curve_specials(Menu):
    bl_label = "Curve Context Menu"

    def draw(self, context):
        # TODO(campbell): match mesh vertex menu.

        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction")

        layout.separator()

        layout.operator("curve.duplicate_move", icon = "DUPLICATE")
        layout.operator("curve.split")
        layout.operator("curve.cyclic_toggle")
        layout.operator_menu_enum("curve.spline_type_set", "type")

        layout.separator()

        layout.operator("curve.make_segment")

        layout.separator()

        layout.operator("transform.tilt")
        layout.operator("curve.tilt_clear")

        layout.separator()

        layout.operator_menu_enum("curve.handle_type_set", "type")
        layout.operator("curve.normals_make_consistent")

        layout.separator()

        layout.operator("curve.spline_weight_set")
        layout.operator("curve.radius_set")

        layout.separator()

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("curve.decimate")
        layout.operator("curve.delete", text="Delete Point").type = 'VERT'
        layout.operator("curve.delete", text="Delete Segment").type = 'SEGMENT'
        layout.operator("curve.dissolve_verts")


class VIEW3D_MT_edit_curve_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.delete", text="Vertices", icon = "DELETE").type = 'VERT'
        layout.operator("curve.delete", text="Segment", icon = "DELETE").type = 'SEGMENT'

        layout.separator()

        layout.operator("curve.dissolve_verts", icon='DISSOLVE_VERTS')


# Workaround to separate the tooltips for Show Hide for Curve in Edit Mode
class VIEW3D_curve_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected Control Points"""      # blender will use this as a tooltip for menu items and buttons.
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

        layout.operator("curve.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("curve.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("curve.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # bfa - separated tooltip


class VIEW3D_MT_edit_surface(Menu):
    bl_label = "Surface"

    draw = draw_curve


class VIEW3D_MT_edit_font(Menu):
    bl_label = "Text"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_edit_text_chars")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_font_move_select")

        layout.separator()

        layout.operator("font.style_toggle", text="Toggle Bold", icon = 'BOLD').style = 'BOLD'
        layout.operator("font.style_toggle", text="Toggle Italic", icon = 'ITALIC').style = 'ITALIC'

        layout.separator()

        layout.operator("font.style_toggle", text="Toggle Underline", icon = 'UNDERLINED').style = 'UNDERLINE'
        layout.operator("font.style_toggle", text="Toggle Small Caps", icon = "SMALL_CAPS").style = 'SMALL_CAPS'

        layout.separator()

        layout.operator("font.case_set", icon = 'SET_UPPERCASE', text = "Set Uppercase").case = 'UPPER'
        layout.operator("font.case_set", icon = 'SET_LOWERCASE', text = "Set Lowercase").case = 'LOWER'

        layout.separator()

        layout.operator("font.delete", icon = "DELETE").type = 'NEXT_OR_SELECTION'


# move_select submenu
class VIEW3D_MT_edit_font_move_select(Menu):
    bl_label = "Select Text"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.move_select", text = "Line End", icon = "HAND").type = 'LINE_END'
        layout.operator("font.move_select", text = "Line Begin", icon = "HAND").type = 'LINE_BEGIN'
        layout.operator("font.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("font.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'
        layout.operator("font.move_select", text = "Previous Word", icon = "HAND").type = 'PREVIOUS_WORD'
        layout.operator("font.move_select", text = "Next Word", icon = "HAND").type = 'NEXT_WORD'
        layout.operator("font.move_select", text = "Previous Line", icon = "HAND").type = 'PREVIOUS_LINE'
        layout.operator("font.move_select", text = "Next Line", icon = "HAND").type = 'NEXT_LINE'
        layout.operator("font.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("font.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'


class VIEW3D_MT_edit_text_chars(Menu):
    bl_label = "Special Characters"

    def draw(self, context):
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


class VIEW3D_MT_edit_meta(Menu):
    bl_label = "Metaball"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mball.duplicate_metaelems", icon = "DUPLICATE")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_meta_showhide")

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("mball.delete_metaelems", text="Delete", icon = "DELETE")


# Workaround to separate the tooltips for Show Hide for Curve in Edit Mode
class VIEW3D_MT_edit_meta_showhide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected metaelement(s)"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.hide_metaelems_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.hide_metaelems(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_edit_meta_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mball.reveal_metaelems", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("mball.hide_metaelems", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("mball.hide_metaelems_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") 


class VIEW3D_MT_edit_lattice(Menu):
    bl_label = "Lattice"

    def draw(self, context):
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
        layout.menu("VIEW3D_MT_edit_armature_roll")

        layout.separator()

        layout.operator("armature.extrude_move", icon = 'EXTRUDE_REGION')

        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked", icon = "EXTRUDE_REGION")

        layout.operator("armature.duplicate_move", icon = "DUPLICATE")
        layout.operator("armature.merge", icon = "MERGE")
        layout.operator("armature.fill", icon = "FILLBETWEEN")
        layout.operator("armature.split", icon = "SPLIT")
        layout.operator("armature.separate", icon = "SEPARATE")

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

        layout.menu("VIEW3D_MT_edit_armature_parent")

        layout.separator()

        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")
        layout.menu("VIEW3D_MT_armature_show_hide") # bfa - the new show hide menu with split tooltip

        layout.separator()

        layout.menu("VIEW3D_MT_edit_armature_delete")


# Workaround to separate the tooltips for Show Hide for Armature in Edit Mode
class VIEW3D_armature_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected Bones in Edit Mode"""      # blender will use this as a tooltip for menu items and buttons.
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

        layout.operator("armature.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("armature.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("armature.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_armature_specials(Menu):
    bl_label = "Armature Context Menu"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("armature.subdivide", text="Subdivide")

        layout.operator("armature.duplicate_move", text="Duplicate", icon = "DUPLICATE")

        layout.operator("armature.extrude_move", icon='EXTRUDE_REGION')
        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked", icon='EXTRUDE_REGION')

        layout.separator()

        layout.operator("armature.fill")

        layout.operator("armature.switch_direction", text="Switch Direction")
        layout.operator("armature.symmetrize")

        layout.menu("VIEW3D_MT_edit_armature_names")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_armature_parent")

        layout.separator()

        layout.operator("armature.split")
        layout.operator("armature.merge")
        layout.operator("armature.dissolve")
        layout.operator("armature.delete")


class VIEW3D_MT_edit_armature_names(Menu):
    bl_label = "Names"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("armature.autoside_names", text="AutoName Left/Right", icon = "STRING").type = 'XAXIS'
        layout.operator("armature.autoside_names", text="AutoName Front/Back", icon = "STRING").type = 'YAXIS'
        layout.operator("armature.autoside_names", text="AutoName Top/Bottom", icon = "STRING").type = 'ZAXIS'
        layout.operator("armature.flip_names", text="Flip Names", icon = "FLIP")


class VIEW3D_MT_edit_armature_parent(Menu):
    bl_label = "Parent"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.parent_set", text="Make", icon='PARENT_SET')
        layout.operator("armature.parent_clear", text="Clear", icon='PARENT_CLEAR')


class VIEW3D_MT_edit_armature_roll(Menu):
    bl_label = "Bone Roll"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_edit_recalc_roll")

        layout.separator()

        layout.operator("transform.transform", text="Set Roll", icon = "SET_ROLL").mode = 'BONE_ROLL'
        layout.operator("armature.roll_clear", icon = "CLEAR_ROLL")


class VIEW3D_MT_edit_recalc_roll(Menu):
    bl_label = "Recalculate Roll"

    def draw(self, context):
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


class VIEW3D_MT_edit_armature_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'

        layout.operator("armature.delete", text="Bones", icon = "DELETE")

        layout.separator()

        layout.operator("armature.dissolve", text="Dissolve Bones", icon = "DELETE")


# ********** Grease Pencil Stroke menus **********
class VIEW3D_MT_gpencil_autoweights(Menu):
    bl_label = "Generate Weights"

    def draw(self, context):
        layout = self.layout
        layout.operator("gpencil.generate_weights", text="With Empty Groups", icon = "ADD").mode = 'NAME'
        layout.operator("gpencil.generate_weights", text="With Automatic Weights").mode = 'AUTO'


class VIEW3D_MT_gpencil_simplify(Menu):
    bl_label = "Simplify"

    def draw(self, context):
        layout = self.layout
        layout.operator("gpencil.stroke_simplify_fixed", text="Fixed", icon = "MOD_SIMPLIFY")
        layout.operator("gpencil.stroke_simplify", text="Adaptative", icon = "MOD_SIMPLIFY")


class VIEW3D_MT_paint_gpencil(Menu):
    bl_label = "Strokes"

    def draw(self, context):

        layout = self.layout

        layout.menu("VIEW3D_MT_gpencil_animation")
        layout.menu("VIEW3D_MT_edit_gpencil_interpolate")

        layout.separator()

        layout.operator("gpencil.delete", text="Delete Frame", icon = "DELETE").type = 'FRAME'
        layout.operator("gpencil.active_frames_delete_all", icon = "DELETE")


class VIEW3D_MT_assign_material(Menu):
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout
        ob = context.active_object

        for slot in ob.material_slots:
            mat = slot.material
            if mat:
                layout.operator("gpencil.stroke_change_color", text=mat.name, icon = "COLOR").material = mat.name


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
    bl_label = "Strokes"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_edit_gpencil_transform")

        layout.separator()
        layout.menu("GPENCIL_MT_snap")

        layout.separator()

        layout.menu("VIEW3D_MT_gpencil_animation")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_gpencil_interpolate")

        layout.separator()

        layout.operator("gpencil.duplicate_move", text="Duplicate", icon = "DUPLICATE")
        layout.operator("gpencil.stroke_smooth", text="Smooth", icon = "SMOOTH")
        layout.operator("gpencil.stroke_subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES")
        layout.menu("VIEW3D_MT_gpencil_simplify")

        layout.separator()

        #layout.operator_menu_enum("gpencil.stroke_separate", "mode", text="Separate")
        layout.menu("GPENCIL_MT_separate")
        layout.operator("gpencil.stroke_split", text="Split", icon = "SPLIT")
        layout.operator("gpencil.stroke_join", text="Join", icon = "JOIN").type = 'JOIN'
        layout.operator("gpencil.stroke_join", text="Join and Copy", icon = "JOIN").type = 'JOINCOPY'

        layout.separator()

        layout.operator("gpencil.stroke_flip", text="Flip Direction", icon = "FLIP")

        layout.separator()

        layout.operator("gpencil.copy", text="Copy", icon='COPYDOWN')
        layout.operator("gpencil.paste", text="Paste", icon='PASTEDOWN').type = 'COPY'
        layout.operator("gpencil.paste", text="Paste & Merge", icon = "MERGE").type = 'MERGE'

        layout.separator()

        layout.operator_menu_enum("gpencil.move_to_layer", "layer", text="Move to Layer")
        layout.menu("VIEW3D_MT_assign_material")
        layout.operator_menu_enum("gpencil.stroke_arrange", "direction", text="Arrange Strokes")

        layout.separator()

        layout.operator_menu_enum("gpencil.convert", "type", text="Convert to Geometry")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_gpencil_delete")
        layout.operator("gpencil.stroke_cyclical_set", text="Toggle Cyclic", icon = 'TOGGLE_CYCLIC').type = 'TOGGLE'
        
        layout.operator_menu_enum("gpencil.stroke_caps_set", text="Toggle Caps...", property="type")

        layout.separator()

        layout.menu("GPENCIL_MT_cleanup")


class VIEW3D_MT_weight_gpencil(Menu):
    bl_label = "Weights"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT')
        layout.operator("gpencil.vertex_group_smooth", text="Smooth", icon='WEIGHT_SMOOTH')

        layout.separator()
        layout.menu("VIEW3D_MT_gpencil_autoweights")


class VIEW3D_MT_gpencil_animation(Menu):
    bl_label = "Animation"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'GPENCIL' and ob.mode != 'OBJECT'

    @staticmethod
    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.blank_frame_add", icon = "ADD")
        layout.operator("gpencil.active_frames_delete_all", text="Delete Frame(s)", icon = "DELETE")

        layout.separator()
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame", icon = "DUPLICATE")
        layout.operator("gpencil.frame_duplicate", text="Duplicate All Layers", icon = "DUPLICATE").mode = 'ALL'


class VIEW3D_MT_edit_gpencil_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate", icon='TRANSFORM_MOVE')
        layout.operator("transform.rotate", icon='TRANSFORM_ROTATE')
        layout.operator("transform.resize", text="Scale", icon='TRANSFORM_SCALE')

        layout.separator()

        layout.operator("transform.bend", text="Bend", icon = "BEND")
        layout.operator("transform.shear", text="Shear", icon = "SHEAR")
        layout.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
        layout.operator("transform.transform", text="Shrink Fatten", icon = 'SHRINK_FATTEN').mode = 'GPENCIL_SHRINKFATTEN'

        layout.separator()

        layout.operator("gpencil.reproject")


class VIEW3D_MT_edit_gpencil_interpolate(Menu):
    bl_label = "Interpolate"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.interpolate", text="Interpolate", icon = "INTERPOLATE")
        layout.operator("gpencil.interpolate_sequence", text="Sequence", icon = "SEQUENCE")


class VIEW3D_MT_object_mode_pie(Menu):
    bl_label = "Mode"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_enum("object.mode_set", "mode")


class VIEW3D_MT_view_pie(Menu):
    bl_label = "View"
    bl_idname = "VIEW3D_MT_view_pie"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_enum("view3d.view_axis", "type")
        pie.operator("view3d.view_camera", text="View Camera", icon='CAMERA_DATA')
        pie.operator("view3d.view_selected", text="View Selected", icon='VIEW_SELECTED')


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
        if (
                (context.mode == 'POSE') or
                ((context.mode == 'WEIGHT_PAINT') and (context.active_object.find_armature()))
        ):
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

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon='PIVOT_CURSOR')
        pie.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon='RESTRICT_SELECT_OFF')
        pie.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='PIVOT_CURSOR')
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon='RESTRICT_SELECT_OFF').use_offset = False
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon='RESTRICT_SELECT_OFF').use_offset = True
        pie.operator("view3d.snap_selected_to_active", text="Selection to Active", icon='RESTRICT_SELECT_OFF')
        pie.operator("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon='PIVOT_CURSOR')
        pie.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon='PIVOT_CURSOR')


class VIEW3D_MT_proportional_editing_falloff_pie(Menu):
    bl_label = "Proportional Editing Falloff"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        tool_settings = context.scene.tool_settings

        pie.prop(tool_settings, "proportional_edit_falloff", expand=True)


# ********** Panel **********


class VIEW3D_PT_view3d_properties(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)
        col = flow.column()

        subcol = col.column()
        subcol.active = bool(view.region_3d.view_perspective != 'CAMERA' or view.region_quadviews)
        subcol.prop(view, "lens", text="Focal Length")

        subcol = col.column(align=True)
        subcol.prop(view, "clip_start", text="Clip Start")
        subcol.prop(view, "clip_end", text="End")

        subcol.separator()

        col = flow.column()

        subcol = col.column()
        subcol.enabled = not view.lock_camera_and_layers
        subcol.prop(view, "camera", text="Local Camera")

        subcol = col.column(align=True)
        subcol.prop(view, "use_render_border")
        subcol.active = view.region_3d.view_perspective != 'CAMERA'


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
        subcol = col.column()
        subcol.active = bool(view.region_3d.view_perspective != 'CAMERA' or view.region_quadviews)

        subcol.prop(view, "lock_object")
        lock_object = view.lock_object
        if lock_object:
            if lock_object.type == 'ARMATURE':
                subcol.prop_search(
                    view, "lock_bone", lock_object.data,
                    "edit_bones" if lock_object.mode == 'EDIT'
                    else "bones",
                    text=""
                )
        else:
            subcol.prop(view, "lock_cursor", text="Lock to 3D Cursor")

        col.prop(view, "lock_camera")


class VIEW3D_PT_view3d_cursor(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "3D Cursor"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        scene = context.scene

        layout.column().prop(scene, "cursor_location", text="Location")


class VIEW3D_PT_collections(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Collections Visibility"
    bl_ui_units_x = 10

    def _draw_collection(self, layout, view_layer, collection, index):
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
            has_objects = True
            if child.has_selected_objects(view_layer):
                icon = 'LAYER_ACTIVE'
            elif child.has_objects():
                icon = 'LAYER_USED'
            else:
                has_objects = False

            has_visible_objects = has_objects and child.has_visible_objects(view_layer)

            row = layout.row()
            sub = row.split(factor=0.98)
            subrow = sub.row()
            subrow.alignment = 'LEFT'
            subrow.active = has_visible_objects
            subrow.operator("object.hide_collection", text=child.name, icon=icon, emboss=False).collection_index = index

            sub = row.split()
            subrow = sub.row(align=True)
            subrow.alignment = 'RIGHT'
            icon = 'HIDE_OFF' if has_visible_objects else 'HIDE_ON'
            props = subrow.operator("object.hide_collection", text="", icon=icon, emboss=False)
            props.collection_index = index
            props.toggle = True
            subrow.prop(child.collection, "hide_select", text="", emboss=False)

        for child in collection.children:
            index = self._draw_collection(layout, view_layer, child, index)

        return index

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        layout.label(text="Collections Visibility")
        col = layout.column()

        view_layer = context.view_layer
        # We pass index 0 here beause the index is increased
        # so the first real index is 1
        # And we start with index as 1 because we skip the master collection
        self._draw_collection(layout, view_layer, view_layer.layer_collection, 0)


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
            ("mesh", "Mesh"),
            ("curve", "Curve"),
            ("surf", "Surface"),
            ("meta", "Meta"),
            ("font", "Font"),
            (None, None),
            # Other
            ("armature", "Armature"),
            ("lattice", "Lattice"),
            ("empty", "Empty"),
            ("grease_pencil", "Grease Pencil"),
            ("camera", "Camera"),
            ("light", "Light"),
            ("light_probe", "Light Probe"),
            ("speaker", "Speaker"),
        )

        for attr, attr_name in attr_object_types:
            if attr is None:
                col.separator()
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

    def draw(self, context):
        pass


class VIEW3D_PT_shading_lighting(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Lighting"
    bl_parent_id = 'VIEW3D_PT_shading'

    @classmethod
    def poll(cls, context):
        shading = VIEW3D_PT_shading.get_shading(context)
        return shading.type in {'SOLID', 'MATERIAL'}

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

                if not system.edit_studio_light:
                    sub.scale_y = 0.6  # smaller studiolight preview
                    sub.template_icon_view(shading, "studio_light", scale_popup=3.0)
                else:
                    sub.prop(system, "edit_studio_light", text="Disable Studio Light Edit", icon='NONE', toggle=True)

                col = split.column()
                col.operator("wm.studiolight_userpref_show", emboss=False, text="", icon='PREFERENCES')

                split = layout.split(factor=0.9)
                col = split.column()

                row = col.row()
                row.prop(shading, "use_world_space_lighting", text="", icon='WORLD', toggle=True)
                row = row.row()
                row.active = shading.use_world_space_lighting
                row.prop(shading, "studiolight_rotate_z", text="Rotation")
                col = split.column()  # to align properly with above

            elif shading.light == 'MATCAP':
                sub.scale_y = 0.6  # smaller matcap preview

                sub.template_icon_view(shading, "studio_light", scale_popup=3.0)

                col = split.column()
                col.operator("wm.studiolight_userpref_show", emboss=False, text="", icon='PREFERENCES')
                col.operator("view3d.toggle_matcap_flip", emboss=False, text="", icon='ARROW_LEFTRIGHT')

        elif shading.type == 'MATERIAL':
            col.prop(shading, "use_scene_lights")
            col.prop(shading, "use_scene_world")

            if not shading.use_scene_world:
                col = layout.column()
                split = col.split(factor=0.9)

                col = split.column()
                sub = col.row()
                sub.scale_y = 0.6
                sub.template_icon_view(shading, "studio_light", scale_popup=3)

                col = split.column()
                col.operator("wm.studiolight_userpref_show", emboss=False, text="", icon='PREFERENCES')

                if shading.selected_studio_light.type == 'WORLD':
                    split = layout.split(factor=0.9)
                    col = split.column()
                    col.prop(shading, "studiolight_rotate_z", text="Rotation")
                    col.prop(shading, "studiolight_background_alpha")
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

        layout.row().prop(shading, "color_type", expand=True)
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
        if shading.type != 'WIREFRAME':
            self._draw_color_type(context)
            self.layout.separator()
        self._draw_background_color(context)


class VIEW3D_PT_shading_options(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Options"
    bl_parent_id = 'VIEW3D_PT_shading'

    def draw(self, context):
        layout = self.layout

        shading = VIEW3D_PT_shading.get_shading(context)

        col = layout.column()

        if shading.type != 'WIREFRAME':
            col.prop(shading, "show_backface_culling")

        row = col.row()

        if shading.type == 'WIREFRAME':
            row.prop(shading, "show_xray_wireframe", text="")
            sub = row.row()
            sub.active = shading.show_xray_wireframe
            sub.prop(shading, "xray_alpha_wireframe", text="X-Ray")
        elif shading.type == 'SOLID':
            row.prop(shading, "show_xray", text="")
            sub = row.row()
            sub.active = shading.show_xray
            sub.prop(shading, "xray_alpha", text="X-Ray")

            row = col.row()
            row.prop(shading, "show_shadows", text="")
            row.active = not shading.show_xray
            sub = row.row(align=True)
            sub.active = shading.show_shadows
            sub.prop(shading, "shadow_intensity", text="Shadow")
            sub.popover(
                panel="VIEW3D_PT_shading_options_shadow",
                icon='PREFERENCES',
                text=""
            )

            col = layout.column()

            row = col.row()
            row.active = not shading.show_xray
            row.prop(shading, "show_cavity")

            if shading.show_cavity and not shading.show_xray:
                row.prop(shading, "cavity_type", text="Type")

                if shading.cavity_type in {'WORLD', 'BOTH'}:
                    col.label(text="World Space")
                    sub = col.row(align=True)
                    sub.prop(shading, "cavity_ridge_factor", text="Ridge")
                    sub.prop(shading, "cavity_valley_factor", text="Valley")
                    sub.popover(
                        panel="VIEW3D_PT_shading_options_ssao",
                        icon='PREFERENCES',
                        text=""
                    )

                if shading.cavity_type in {'SCREEN', 'BOTH'}:
                    col.label(text="Screen Space")
                    sub = col.row(align=True)
                    sub.prop(shading, "curvature_ridge_factor", text="Ridge")
                    sub.prop(shading, "curvature_valley_factor", text="Valley")

        if shading.type in {'WIREFRAME', 'SOLID'}:
            row = layout.split()
            row.prop(shading, "show_object_outline")
            sub = row.row()
            sub.active = shading.show_object_outline
            sub.prop(shading, "object_outline_color", text="")

            col = layout.column()
            if (shading.light == 'STUDIO') and (shading.type != 'WIREFRAME'):
                col.prop(shading, "show_specular_highlight", text="Specular Lighting")


class VIEW3D_PT_shading_options_shadow(Panel):
    bl_label = "Shadow Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    @classmethod
    def poll(cls, context):
        return True

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

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene

        col = layout.column(align=True)
        col.prop(scene.display, "matcap_ssao_samples")
        col.prop(scene.display, "matcap_ssao_distance")
        col.prop(scene.display, "matcap_ssao_attenuation")


class VIEW3D_PT_overlay(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Overlays"
    bl_ui_units_x = 13

    def draw(self, context):
        pass


class VIEW3D_PT_overlay_gizmo(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Gizmo"

    def draw_header(self, context):
        view = context.space_data
        self.layout.prop(view, "show_gizmo", text="")

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        row = col.row(align=True)
        row.active = view.show_gizmo
        row.prop(view, "show_gizmo_navigate", text="Navigate", toggle=True)
        row.prop(view, "show_gizmo_context", text="Active Object", toggle=True)
        row.prop(view, "show_gizmo_tool", text="Active Tools", toggle=True)


class VIEW3D_PT_overlay_guides(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Guides"

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        shading = view.shading
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        split = col.split()
        sub = split.column()
        sub.prop(overlay, "show_floor", text="Grid")

        if overlay.show_floor:
            sub = col.column(align=True)
            sub.active = bool(overlay.show_floor or view.region_quadviews or not view.region_3d.is_perspective)
            subsub = sub.row(align=True)
            subsub.active = overlay.show_floor
            subsub.prop(overlay, "grid_scale", text="Scale")
            subsub.prop(overlay, "grid_subdivisions", text="Subdivisions")

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
        sub = split.column()
        sub.prop(overlay, "show_cursor", text="3D Cursor")

        if shading.type == 'MATERIAL':
            col.prop(overlay, "show_look_dev")

        col.prop(overlay, "show_annotation", text="Annotations")


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

        row = col.row()
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
        overlay = view.overlay
        shading = view.shading
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        split = col.split()

        sub = split.column()
        sub.prop(overlay, "show_edges", text="Edges")
        sub = split.column()
        sub.prop(overlay, "show_faces", text="Faces")
        sub = split.column()
        if shading.type == 'WIREFRAME':
            sub.active = not shading.show_xray_wireframe
        else:
            sub.active = not shading.show_xray
        sub.prop(overlay, "show_face_center", text="Center")

        row = col.row(align=True)
        row.prop(overlay, "show_edge_crease", text="Creases", toggle=True)
        row.prop(overlay, "show_edge_sharp", text="Sharp", text_ctxt=i18n_contexts.plural, toggle=True)
        row.prop(overlay, "show_edge_bevel_weight", text="Bevel", toggle=True)
        row.prop(overlay, "show_edge_seams", text="Seams", toggle=True)


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

        col.prop(overlay, "show_statvis", text="Mesh Analysis")
        if overlay.show_statvis:
            col = col.column()

            sub = col.split()
            sub.active = overlay.show_statvis
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


class VIEW3D_PT_overlay_edit_mesh_developer(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay_edit_mesh'
    bl_label = "Developer"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and context.preferences.view.show_developer_ui

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        col.prop(overlay, "show_extra_indices", text="Indices")


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
        row.prop(overlay, "show_curve_handles", text="Handles")

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

        layout.prop(sculpt, "show_diffuse_color")
        layout.prop(sculpt, "show_mask")


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
            (mode == 'PAINT_WEIGHT' and context.active_object.find_armature())
        )

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        mode = context.mode
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all
        col.prop(overlay, "show_transparent_bones")

        if mode == 'POSE':
            row = col.row()
            row.prop(overlay, "show_xray_bone", text="")
            sub = row.row()
            sub.active = display_all and overlay.show_xray_bone
            sub.prop(overlay, "xray_alpha_bone", text="Fade Geometry")
        else:
            row = col.row()
            row.prop(overlay, "show_xray_bone")


class VIEW3D_PT_overlay_edit_armature(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Armature Edit Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_ARMATURE'

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all
        col.prop(overlay, "show_transparent_bones")


class VIEW3D_PT_overlay_paint(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return context.mode in {'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text={
            'PAINT_TEXTURE': "Texture Paint",
            'PAINT_VERTEX': "Vertex Paint",
            'PAINT_WEIGHT': "Weight Paint",
        }[context.mode])

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()
        col.active = display_all

        col.prop(overlay, {
            'PAINT_TEXTURE': "texture_paint_mode_opacity",
            'PAINT_VERTEX': "vertex_paint_mode_opacity",
            'PAINT_WEIGHT': "weight_paint_mode_opacity",
        }[context.mode], text="Opacity")

        if context.mode == 'PAINT_WEIGHT':
            row = col.split(factor=0.33)
            row.label(text="Zero Weights")
            sub = row.row()
            sub.prop(context.tool_settings, "vertex_group_user", expand=True)

            col.prop(overlay, "show_wpaint_contours")

        if context.mode in {'PAINT_WEIGHT', 'PAINT_VERTEX'}:
            col.prop(overlay, "show_paint_wire")


class VIEW3D_PT_pivot_point(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Pivot Point"
    bl_ui_units_x = 8

    def draw(self, context):
        tool_settings = context.tool_settings
        obj = context.active_object
        mode = context.mode

        layout = self.layout
        col = layout.column()
        col.label(text="Pivot Point")
        col.prop(tool_settings, "transform_pivot_point", expand=True)

        if (obj is None) or (mode in {'OBJECT', 'POSE', 'WEIGHT_PAINT'}):
            col.separator()

            col.prop(
                tool_settings,
                "use_transform_pivot_point_align",
                text="Only Origins",
            )


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
        col.label(text="Snapping")
        col.prop(tool_settings, "snap_elements", expand=True)

        col.separator()
        if 'INCREMENT' in snap_elements:
            col.prop(tool_settings, "use_snap_grid_absolute")

        if snap_elements != {'INCREMENT'}:
            col.label(text="Target")
            row = col.row(align=True)
            row.prop(tool_settings, "snap_target", expand=True)

            if obj:
                if object_mode == 'EDIT':
                    col.prop(tool_settings, "use_snap_self")
                if object_mode in {'OBJECT', 'POSE', 'EDIT'}:
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

    @staticmethod
    def draw(self, context):
        from math import pi
        settings = context.tool_settings.gpencil_sculpt.guide

        layout = self.layout
        layout.label(text="Guides")
        
        col = layout.column()
        col.active = settings.use_guide
        col.prop(settings, "type", expand=True)
                
        if settings.type in {'PARALLEL'}:
            col.prop(settings, "angle")
            row = col.row(align=True)
        
        col.prop(settings, "use_snapping")        
        if settings.use_snapping:
            
            if settings.type in {'RADIAL'}:
                col.prop(settings, "angle_snap")
            else:
                col.prop(settings, "spacing")
        
        col.label(text="Reference Point")
        row = col.row(align=True)
        row.prop(settings, "reference_point", expand=True)    
        if settings.reference_point in {'CUSTOM'}:
            col.prop(settings, "location", text="Custom Location")        
        if settings.reference_point in {'OBJECT'}:
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
        sub = row.row()
        sub.active = overlay.use_gpencil_grid
        sub.prop(overlay, "gpencil_grid_opacity", text="Canvas", slider=True)

        row = col.row()
        row.prop(overlay, "use_gpencil_paper", text="")
        sub = row.row()
        sub.active = overlay.use_gpencil_paper
        sub.prop(overlay, "gpencil_paper_opacity", text="Fade 3D Objects", slider=True)

        if context.object.mode == 'PAINT_GPENCIL':
            row = col.row()
            row.prop(overlay, "use_gpencil_fade_layers", text="")
            sub = row.row()
            sub.active = overlay.use_gpencil_fade_layers
            sub.prop(overlay, "gpencil_fade_layer", text="Fade Layers", slider=True)

        if context.object.mode in {'EDIT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}:
            layout.prop(overlay, "use_gpencil_edit_lines", text="Edit Lines")
            layout.prop(overlay, "use_gpencil_multiedit_line_only", text="Show Edit Lines only in multiframe")
            layout.prop(overlay, "vertex_opacity", text="Vertex Opacity", slider=True)


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
    bl_category = "View"
    bl_label = "Properties"
    bl_options = {'DEFAULT_CLOSED'}

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

    @staticmethod
    def draw(self, context):
        gpd = context.gpencil_data
        settings = context.tool_settings.gpencil_sculpt

        layout = self.layout
        col = layout.column(align=True)
        col.prop(settings, "use_multiframe_falloff")

        # Falloff curve
        if gpd.use_multiedit and settings.use_multiframe_falloff:
            layout.template_curve_mapping(settings, "multiframe_falloff_curve", brush=True)


class VIEW3D_MT_gpencil_edit_specials(Menu):
    bl_label = "Grease Pencil Specials"

    def draw(self, context):
        layout = self.layout
        is_3d_view = context.space_data.type == 'VIEW_3D'

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("VIEW3D_MT_assign_material")
        layout.separator()

        layout.operator("gpencil.stroke_smooth", text="Smooth")
        layout.operator("gpencil.stroke_subdivide", text="Subdivide")
        layout.operator("gpencil.stroke_simplify_fixed", text="Simplify")
        layout.operator("gpencil.stroke_simplify", text="Simplify Adaptive")

        layout.separator()
        layout.menu("GPENCIL_MT_separate", text="Separate")

        layout.separator()
        layout.operator("gpencil.stroke_split", text="Split")

        layout.separator()
        layout.operator_menu_enum("gpencil.stroke_arrange", "direction", text="Arrange Strokes")

        layout.separator()
        layout.menu("VIEW3D_MT_gpencil_copy_layer")

        layout.separator()

        layout.operator("gpencil.stroke_merge", text="Merge")
        layout.operator("gpencil.stroke_join", text="Join").type = 'JOIN'
        layout.operator("gpencil.stroke_join", text="Join & Copy").type = 'JOINCOPY'
        layout.operator("gpencil.stroke_flip", text="Flip Direction")
        layout.operator_menu_enum("gpencil.stroke_caps_set", text="Toggle Caps...", property="type")

        layout.separator()
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame")
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame All Layers").mode = 'ALL'

        if is_3d_view:
            layout.separator()
            layout.menu("GPENCIL_MT_cleanup")


class VIEW3D_MT_gpencil_sculpt_specials(Menu):
    bl_label = "Grease Pencil Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_assign_material")
        layout.separator()

        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame")
        layout.operator("gpencil.frame_duplicate", text="Duplicate Active Frame All Layers").mode = 'ALL'

        layout.separator()

        layout.operator("gpencil.stroke_subdivide", text="Subdivide")
        layout.operator("gpencil.stroke_simplify_fixed", text="Simplify")
        layout.operator("gpencil.stroke_simplify", text="Simplify Adaptative")

        if context.mode == 'WEIGHT_GPENCIL':
            layout.separator()
            layout.menu("VIEW3D_MT_gpencil_autoweights")


class TOPBAR_PT_gpencil_materials(GreasePencilMaterialsPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Materials"
    bl_ui_units_x = 14


classes = (
    VIEW3D_HT_header,
    ALL_MT_editormenu,
    VIEW3D_MT_editor_menus,
    VIEW3D_MT_transform,
    VIEW3D_MT_transform_base,
    VIEW3D_MT_transform_object,
    VIEW3D_MT_transform_armature,
    VIEW3D_MT_mirror,
    VIEW3D_MT_snap,
    VIEW3D_MT_uv_map,
    VIEW3D_MT_edit_proportional,
    VIEW3D_MT_view_view_selected_all_regions,
    VIEW3D_MT_view_all_all_regions,
    VIEW3D_MT_view_center_cursor_and_view_all,
    VIEW3D_MT_view,
    VIEW3D_MT_view_navigation,
    VIEW3D_MT_view_align,
    VIEW3D_MT_view_align_selected,
    VIEW3D_MT_select_object_inverse,
    VIEW3D_MT_select_object,
    VIEW3D_MT_select_by_type,
    VIEW3D_MT_select_grouped,
    VIEW3D_MT_select_linked,
    VIEW3D_MT_select_object_more_less,
    VIEW3D_MT_select_pose_inverse,
    VIEW3D_MT_select_pose,
    VIEW3D_MT_select_pose_more_less,
    VIEW3D_MT_select_particle_inverse,
    VIEW3D_MT_select_particle,
    VIEW3D_MT_edit_mesh,
    VIEW3D_MT_edit_mesh_sort_elements,
    VIEW3D_MT_edit_mesh_select_similar,
    VIEW3D_MT_edit_mesh_select_more_less,
    VIEW3D_MT_select_edit_mesh_inverse,
    VIEW3D_MT_select_edit_mesh,
    VIEW3D_MT_select_edit_curve_inverse,
    VIEW3D_MT_select_edit_curve,
    VIEW3D_MT_select_edit_curve_select_similar,
    VIEW3D_MT_select_edit_surface,
    VIEW3D_MT_select_edit_text,
    VIEW3D_MT_select_edit_metaball_inverse,
    VIEW3D_MT_select_edit_metaball,
    VIEW3D_MT_select_edit_metaball_select_similar,
    VIEW3D_MT_select_edit_lattice_inverse,
    VIEW3D_MT_select_edit_lattice,
    VIEW3D_MT_select_edit_armature_inverse,
    VIEW3D_MT_select_edit_armature,
    VIEW3D_MT_select_gpencil,
    VIEW3D_MT_select_gpencil_grouped,
    VIEW3D_MT_select_paint_mask_inverse,
    VIEW3D_MT_select_paint_mask,
    VIEW3D_MT_select_paint_mask_vertex_inverse,
    VIEW3D_MT_select_paint_mask_vertex,
    VIEW3D_MT_angle_control,
    VIEW3D_MT_mesh_add,
    VIEW3D_MT_curve_add,
    VIEW3D_MT_surface_add,
    VIEW3D_MT_metaball_add,
    TOPBAR_MT_edit_curve_add,
    TOPBAR_MT_edit_armature_add,
    VIEW3D_MT_armature_add,
    VIEW3D_MT_light_add,
    VIEW3D_MT_lightprobe_add,
    VIEW3D_MT_camera_add,
    VIEW3D_MT_add,
    VIEW3D_MT_image_add,
    VIEW3D_MT_origin_set,
    VIEW3D_MT_object_delete_global,
    VIEW3D_MT_object,
    VIEW3D_MT_object_animation,
    VIEW3D_MT_object_rigid_body,
    VIEW3D_MT_object_clear,
    VIEW3D_MT_object_specials,
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
    VIEW3D_MT_facemask_showhide,
    VIEW3D_MT_brush_paint_modes,
    VIEW3D_MT_paint_vertex,
    VIEW3D_MT_hook,
    VIEW3D_MT_vertex_group,
    VIEW3D_MT_paint_weight,
    VIEW3D_MT_sculpt,
    VIEW3D_MT_hide_mask,
    VIEW3D_MT_particle,
    VIEW3D_MT_particle_specials,
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
    VIEW3D_MT_pose_hide_unselected,
    VIEW3D_MT_pose_show_hide,
    VIEW3D_MT_pose_apply,
    VIEW3D_MT_pose_specials,
    VIEW3D_MT_bone_options_toggle,
    VIEW3D_MT_bone_options_enable,
    VIEW3D_MT_bone_options_disable,
    VIEW3D_MT_edit_mesh_specials,
    VIEW3D_MT_edit_mesh_select_mode,
    VIEW3D_MT_edit_mesh_extrude,
    VIEW3D_MT_edit_mesh_vertices,
    VIEW3D_MT_edit_mesh_edges,
    VIEW3D_MT_edit_mesh_edges_data,
    VIEW3D_MT_edit_mesh_faces,
    VIEW3D_MT_edit_mesh_faces_data,
    VIEW3D_normals_make_consistent_inside,
    VIEW3D_MT_edit_mesh_normals,
    VIEW3D_MT_edit_mesh_shading,
    VIEW3D_MT_edit_mesh_weights,
    VIEW3D_MT_edit_mesh_clean,
    VIEW3D_MT_edit_mesh_delete,
    VIEW3D_mesh_hide_unselected,
    VIEW3D_curve_hide_unselected,
    VIEW3D_MT_edit_mesh_show_hide,
    VIEW3D_MT_paint_gpencil,
    VIEW3D_MT_assign_material,
    VIEW3D_MT_edit_gpencil,
    VIEW3D_MT_edit_gpencil_delete,
    VIEW3D_MT_weight_gpencil,
    VIEW3D_MT_gpencil_animation,
    VIEW3D_MT_gpencil_simplify,
    VIEW3D_MT_gpencil_copy_layer,
    VIEW3D_MT_edit_curve,
    VIEW3D_MT_edit_curve_ctrlpoints,
    VIEW3D_MT_edit_curve_handle_type_set,
    VIEW3D_MT_edit_curve_segments,
    VIEW3D_MT_edit_curve_specials,
    VIEW3D_MT_edit_curve_delete,
    VIEW3D_MT_edit_curve_show_hide,
    VIEW3D_MT_edit_surface,
    VIEW3D_MT_edit_font,
    VIEW3D_MT_edit_font_move_select,
    VIEW3D_MT_edit_text_chars,
    VIEW3D_MT_edit_meta,
    VIEW3D_MT_edit_meta_showhide_unselected,
    VIEW3D_MT_edit_meta_showhide,
    VIEW3D_MT_edit_lattice,
    VIEW3D_MT_edit_lattice_flip,
    VIEW3D_MT_edit_armature,
    VIEW3D_armature_hide_unselected,
    VIEW3D_MT_armature_show_hide,
    VIEW3D_MT_armature_specials,
    VIEW3D_MT_edit_armature_parent,
    VIEW3D_MT_edit_armature_roll,
    VIEW3D_MT_edit_recalc_roll,
    VIEW3D_MT_edit_armature_names,
    VIEW3D_MT_edit_armature_delete,
    VIEW3D_MT_edit_gpencil_transform,
    VIEW3D_MT_edit_gpencil_interpolate,
    VIEW3D_MT_object_mode_pie,
    VIEW3D_MT_view_pie,
    VIEW3D_MT_shading_pie,
    VIEW3D_MT_shading_ex_pie,
    VIEW3D_MT_pivot_pie,
    VIEW3D_MT_snap_pie,
    VIEW3D_MT_orientations_pie,
    VIEW3D_MT_proportional_editing_falloff_pie,
    VIEW3D_PT_view3d_properties,
    VIEW3D_PT_view3d_camera_lock,
    VIEW3D_PT_view3d_cursor,
    VIEW3D_PT_collections,
    VIEW3D_PT_object_type_visibility,
    VIEW3D_PT_grease_pencil,
    VIEW3D_PT_annotation_onion,
    VIEW3D_PT_gpencil_multi_frame,
    VIEW3D_MT_gpencil_autoweights,
    VIEW3D_MT_gpencil_edit_specials,
    VIEW3D_MT_gpencil_sculpt_specials,
    VIEW3D_PT_quad_view,
    VIEW3D_PT_view3d_stereo,
    VIEW3D_PT_shading,
    VIEW3D_PT_shading_lighting,
    VIEW3D_PT_shading_color,
    VIEW3D_PT_shading_options,
    VIEW3D_PT_shading_options_shadow,
    VIEW3D_PT_shading_options_ssao,
    VIEW3D_PT_overlay,
    VIEW3D_PT_overlay_gizmo,
    VIEW3D_PT_overlay_guides,
    VIEW3D_PT_overlay_object,
    VIEW3D_PT_overlay_geometry,
    VIEW3D_PT_overlay_motion_tracking,
    VIEW3D_PT_overlay_edit_mesh,
    VIEW3D_PT_overlay_edit_mesh_shading,
    VIEW3D_PT_overlay_edit_mesh_measurement,
    VIEW3D_PT_overlay_edit_mesh_normals,
    VIEW3D_PT_overlay_edit_mesh_freestyle,
    VIEW3D_PT_overlay_edit_mesh_developer,
    VIEW3D_PT_overlay_edit_curve,
    VIEW3D_PT_overlay_edit_armature,
    VIEW3D_PT_overlay_paint,
    VIEW3D_PT_overlay_pose,
    VIEW3D_PT_overlay_sculpt,
    VIEW3D_PT_pivot_point,
    VIEW3D_PT_snapping,
    VIEW3D_PT_gpencil_origin,
    VIEW3D_PT_gpencil_lock,
    VIEW3D_PT_gpencil_guide,
    VIEW3D_PT_transform_orientations,
    VIEW3D_PT_overlay_gpencil_options,
    VIEW3D_PT_context_properties,
    TOPBAR_PT_gpencil_materials,
    TOPBAR_PT_annotation_layers,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
