# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Header, Menu, Panel
from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
)
from bl_ui.utils import PresetPanel
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)
from bl_ui.properties_material import (
    EEVEE_MATERIAL_PT_settings,
    MATERIAL_PT_viewport,
)
from bl_ui.properties_world import (
    WORLD_PT_viewport_display
)
from bl_ui.properties_data_light import (
    DATA_PT_light,
    DATA_PT_EEVEE_light,
)


################################ Switch between the editors ##########################################

class NODE_OT_switch_editors_to_compositor(bpy.types.Operator):
    """Switch to the Comppositor Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_compositor"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "Switch to Compositor Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        bpy.ops.wm.context_set_enum(
            data_path="area.ui_type", value="CompositorNodeTree")
        return {'FINISHED'}


class NODE_OT_switch_editors_to_geometry(bpy.types.Operator):
    """Switch to the Geometry Node Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_geometry"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "Switch to Geometry Node Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        bpy.ops.wm.context_set_enum(
            data_path="area.ui_type", value="GeometryNodeTree")
        return {'FINISHED'}


class NODE_OT_switch_editors_to_shadereditor(bpy.types.Operator):
    """Switch to the Shader Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_shadereditor"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "Switch to Shader Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        bpy.ops.wm.context_set_enum(
            data_path="area.ui_type", value="ShaderNodeTree")
        return {'FINISHED'}


# The blank buttons, we don't want to switch to the editor in which we are already.


class NODE_OT_switch_editors_in_compositor(bpy.types.Operator):
    """Compositor Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_compositor"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "You are in Compositor Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        return {'FINISHED'}


class NODE_OT_switch_editors_in_geometry(bpy.types.Operator):
    """Geometry Node Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_geometry"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "You are in Geometry Node Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        return {'FINISHED'}


class NODE_OT_switch_editors_in_shadereditor(bpy.types.Operator):
    """Shader Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_shadereditor"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "You are in Shader Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        return {'FINISHED'}


############################# END ##################################


class NODE_HT_header(Header):
    bl_space_type = 'NODE_EDITOR'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        snode = context.space_data
        overlay = snode.overlay
        snode_id = snode.id
        id_from = snode.id_from
        tool_settings = context.tool_settings
        is_compositor = snode.tree_type == 'CompositorNodeTree'
        not_group = (len(snode.path) > 1) # bfa - don't show up arrow if at top level.

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # Now expanded via the `ui_type`.
        # layout.prop(snode, "tree_type", text="")

        display_pin = True
        if snode.tree_type == 'ShaderNodeTree':
            row = layout.row(align = True)
            row.operator("wm.switch_editor_to_compositor", text="", icon='NODE_COMPOSITING')
            row.operator("wm.switch_editor_to_geometry", text="", icon='GEOMETRY_NODES')
            row.operator("wm.switch_editor_in_shadereditor", text="", icon='SHADER_ACTIVE')

            layout.prop(snode, "shader_type", text="")

            ob = context.object
            if snode.shader_type == 'OBJECT' and ob:
                ob_type = ob.type

                NODE_MT_editor_menus.draw_collapsible(context, layout)
                ## BFA - moved below to a different solution
                # # No shader nodes for EEVEE lights.
                # if snode_id and not (context.engine == 'BLENDER_EEVEE' and ob_type == 'LIGHT'):
                #     row = layout.row()
                #     row.prop(snode_id, "use_nodes")

                # layout.separator_spacer()

                types_that_support_material = {
                    'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'GPENCIL', 'VOLUME', 'CURVES', 'POINTCLOUD',
                }
                # disable material slot buttons when pinned, cannot find correct slot within id_from (#36589)
                # disable also when the selected object does not support materials
                has_material_slots = not snode.pin and ob_type in types_that_support_material

                if ob_type != 'LIGHT':
                    row = layout.row()
                    row.enabled = has_material_slots
                    row.ui_units_x = 4
                    row.popover(panel="NODE_PT_material_slots")

                row = layout.row()
                row.enabled = has_material_slots

                # Show material.new when no active ID/slot exists
                if not id_from and ob_type in types_that_support_material:
                    row.template_ID(ob, "active_material", new="material.new")
                # Material ID, but not for Lights
                if id_from and ob_type != 'LIGHT':
                    row.template_ID(id_from, "active_material", new="material.new")

            if snode.shader_type == 'WORLD':
                NODE_MT_editor_menus.draw_collapsible(context, layout)
				## BFA - moved below to a different solution
                #if snode_id:
                #    row = layout.row()
                #    row.prop(snode_id, "use_nodes")
				#
                #layout.separator_spacer()
                row = layout.row()
                row.enabled = not snode.pin
                row.template_ID(scene, "world", new="world.new")

            if snode.shader_type == 'LINESTYLE':
                view_layer = context.view_layer
                lineset = view_layer.freestyle_settings.linesets.active

                if lineset is not None:
                    NODE_MT_editor_menus.draw_collapsible(context, layout)
					## BFA - moved below to a different solution
                    #if snode_id:
                    #    row = layout.row()
                    #    row.prop(snode_id, "use_nodes")
					#
                    #layout.separator_spacer()

                    row = layout.row()
                    row.enabled = not snode.pin
                    row.template_ID(lineset, "linestyle", new="scene.freestyle_linestyle_new")

        elif snode.tree_type == 'TextureNodeTree':
            layout.prop(snode, "texture_type", text="")

            NODE_MT_editor_menus.draw_collapsible(context, layout)
			## BFA - moved below to a different solution
            #if snode_id:
            #    layout.prop(snode_id, "use_nodes")
			#
            #layout.separator_spacer()
            if id_from:
                if snode.texture_type == 'BRUSH':
                    layout.template_ID(id_from, "texture", new="texture.new")
                else:
                    layout.template_ID(id_from, "active_texture", new="texture.new")

        elif snode.tree_type == 'CompositorNodeTree':
			#BFA - Editor Switchers
            row = layout.row(align = True)
            row.operator("wm.switch_editor_in_compositor", text="", icon='NODE_COMPOSITING_ACTIVE')
            row.operator("wm.switch_editor_to_geometry", text="", icon='GEOMETRY_NODES')
            row.operator("wm.switch_editor_to_shadereditor", text="", icon='NODE_MATERIAL')

            NODE_MT_editor_menus.draw_collapsible(context, layout)

        elif snode.tree_type == 'GeometryNodeTree':
			#BFA - Editor Switchers
            row = layout.row(align = True)
            row.operator("wm.switch_editor_to_compositor", text="", icon='NODE_COMPOSITING')
            row.operator("wm.switch_editor_in_geometry", text="", icon='GEOMETRY_NODES_ACTIVE')
            row.operator("wm.switch_editor_to_shadereditor", text="", icon='NODE_MATERIAL')

            layout.prop(snode, "geometry_nodes_type", text="")
            NODE_MT_editor_menus.draw_collapsible(context, layout)
            layout.separator_spacer()

            if snode.geometry_nodes_type == 'MODIFIER':
                ob = context.object

                row = layout.row()
                if snode.pin:
                    row.enabled = False
                    row.template_ID(snode, "node_tree", new="node.new_geometry_node_group_assign")
                elif ob:
                    active_modifier = ob.modifiers.active
                    if active_modifier and active_modifier.type == 'NODES':
                        if active_modifier.node_group:
                            row.template_ID(active_modifier, "node_group", new="object.geometry_node_tree_copy_assign")
                        else:
                            row.template_ID(active_modifier, "node_group", new="node.new_geometry_node_group_assign")
                    else:
                        row.template_ID(snode, "node_tree", new="node.new_geometry_nodes_modifier")
            else:
                layout.template_ID(snode, "geometry_nodes_tool_tree", new="node.new_geometry_node_group_tool")
                if snode.node_tree:
                    layout.popover(panel="NODE_PT_geometry_node_tool_object_types", text="Types")
                    layout.popover(panel="NODE_PT_geometry_node_tool_mode", text="Modes")
                display_pin = False
        else:
            # Custom node tree is edited as independent ID block
            NODE_MT_editor_menus.draw_collapsible(context, layout)

			#layout.separator_spacer() #BFA - removed

            layout.template_ID(snode, "node_tree", new="node.new_node_tree")

        #################### options at the right ###################################


        layout.separator_spacer()

        # Put pin on the right for Compositing
        if is_compositor:
            layout.prop(snode, "pin", text="", emboss=False)

        # -------------------- BFA - use nodes ---------------------------

        if snode.tree_type == 'ShaderNodeTree':

            if snode.shader_type == 'OBJECT' and ob:

                # No shader nodes for Eevee lights
                if snode_id and not (context.engine == 'BLENDER_EEVEE' and ob_type == 'LIGHT'):
                    row = layout.row()
                    row.prop(snode_id, "use_nodes")

            if snode.shader_type == 'WORLD':

                if snode_id:
                    row = layout.row()
                    row.prop(snode_id, "use_nodes")

            if snode.shader_type == 'LINESTYLE':

                if lineset is not None:

                    if snode_id:
                        row = layout.row()
                        row.prop(snode_id, "use_nodes")


        elif snode.tree_type == 'TextureNodeTree':

            if snode_id:
                layout.prop(snode_id, "use_nodes")


        elif snode.tree_type == 'CompositorNodeTree':

            if snode_id:
                layout.prop(snode_id, "use_nodes")


        # ----------------- rest of the options


        # Put pin next to ID block
        if not is_compositor and display_pin:
            layout.prop(snode, "pin", text="", emboss=False)

        # bfa - don't show up arrow if at top level.
        if not_group:
            layout.operator("node.tree_path_parent", text="", icon='FILE_PARENT')
        else:
            pass

        # Backdrop
        if is_compositor:
            row = layout.row(align=True)
            row.prop(snode, "show_backdrop", toggle=True)
            sub = row.row(align=True)
            if snode.show_backdrop:
                sub.operator("node.backimage_move", text="", icon ='TRANSFORM_MOVE')
                sub.operator("node.backimage_zoom", text="", icon = "ZOOM_IN").factor = 1.2
                sub.operator("node.backimage_zoom", text="", icon = "ZOOM_OUT").factor = 1.0 / 1.2
                sub.operator("node.backimage_fit", text="", icon = "VIEW_FIT")
                sub.separator()
                sub.prop(snode, "backdrop_channels", icon_only=True, text="", expand=True)

        # Snap
        row = layout.row(align=True)
        row.prop(tool_settings, "use_snap_node", text="")
        if tool_settings.use_snap:
            row.prop(tool_settings, "snap_node_element", icon_only=True)
            if tool_settings.snap_node_element != 'GRID':
                row.prop(tool_settings, "snap_target", text="")

        # Overlay toggle & popover
        row = layout.row(align=True)
        row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
        sub = row.row(align=True)
        sub.active = overlay.show_overlays
        sub.popover(panel="NODE_PT_overlay", text="")

# BFA - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class NODE_MT_editor_menus(Menu):
    bl_idname = "NODE_MT_editor_menus"
    bl_label = ""

    def draw(self, _context):
        layout = self.layout

        layout.menu("SCREEN_MT_user_menu", text = "Quick") #BFA - Quick favourites menu
        layout.menu("NODE_MT_view")
        layout.menu("NODE_MT_select")
        layout.menu("NODE_MT_add")
        layout.menu("NODE_MT_node")


class NODE_MT_add(bpy.types.Menu):
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        import nodeitems_utils

        layout = self.layout

        #BFA - changed to show in all add menus for discoverability, instead of being conditional to the invoked region by hotkey only.

        layout.operator_context = 'INVOKE_REGION_WIN'

        snode = context.space_data
        if snode.tree_type == 'GeometryNodeTree':
            layout.operator("WM_OT_search_single_menu", text="Search...", icon='VIEWZOOM').menu_idname = "NODE_MT_geometry_node_add_all"
            layout.separator()
            layout.menu_contents("NODE_MT_geometry_node_add_all")
        elif snode.tree_type == 'CompositorNodeTree':
            layout.operator("WM_OT_search_single_menu", text="Search...", icon='VIEWZOOM').menu_idname = "NODE_MT_compositor_node_add_all"
            layout.separator()
            layout.menu_contents("NODE_MT_compositor_node_add_all")
        elif snode.tree_type == 'ShaderNodeTree':
            layout.operator("WM_OT_search_single_menu", text="Search...", icon='VIEWZOOM').menu_idname = "NODE_MT_shader_node_add_all"
            layout.separator()
            layout.menu_contents("NODE_MT_shader_node_add_all")
        elif snode.tree_type == 'TextureNodeTree':
            layout.operator("WM_OT_search_single_menu", text="Search...", icon='VIEWZOOM').menu_idname = "NODE_MT_texture_node_add_all"
            layout.separator()
            layout.menu_contents("NODE_MT_texture_node_add_all")
        elif nodeitems_utils.has_node_categories(context):
            # Actual node sub-menus are defined by draw functions from node categories.
            nodeitems_utils.draw_node_categories_menu(self, context)

#BFA - expose the pie menus to header
class NODE_MT_pie_menus(Menu):
    bl_label = "Pie Menus"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.operator("wm.call_menu_pie", text = "View", icon = "MENU_PANEL").name = 'NODE_MT_view_pie'


class NODE_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        snode = context.space_data

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(snode, "show_region_toolbar")
        layout.prop(snode, "show_region_ui")
        layout.prop(addon_prefs, "node_show_toolshelf_tabs")

        layout.separator()

        layout.menu("NODE_MT_view_annotations")

        layout.separator()

        sub = layout.column()
        sub.operator_context = 'EXEC_REGION_WIN'
        sub.operator("view2d.zoom_in", icon = "ZOOM_IN")
        sub.operator("view2d.zoom_out", icon = "ZOOM_OUT")

        layout.operator("view2d.zoom_border", icon = "ZOOM_BORDER")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("node.view_selected", icon='VIEW_SELECTED')
        layout.operator("node.view_all", icon = "VIEWALL" )

        if context.space_data.show_backdrop:

            layout.separator()

            layout.operator("node.viewer_border", text = "Set Viewer Region", icon = "RENDERBORDER")
            layout.operator("node.clear_viewer_border", text = "Clear Viewer Region", icon = "RENDERBORDER_CLEAR")

        layout.separator()

        layout.menu("NODE_MT_pie_menus")
        layout.menu("INFO_MT_area")


class NODE_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.menu("NODE_MT_select_legacy")
        layout.operator_menu_enum("node.select_lasso", "mode")

        layout.separator()

        layout.operator("node.select_all",text = "All", icon = 'SELECT_ALL').action = 'SELECT'
        layout.operator("node.select_all", text="None", icon='SELECT_NONE').action = 'DESELECT'
        layout.operator("node.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("node.select_linked_from", text = "Linked From", icon = "LINKED")
        layout.operator("node.select_linked_to", text = "Linked To", icon = "LINKED")

        layout.separator()

        layout.operator("node.select_grouped", text = "Grouped Extend", icon = "GROUP").extend = True
        layout.operator("node.select_grouped", text = "Grouped", icon = "GROUP").extend = False
        layout.operator("node.select_same_type_step", text="Activate Same Type Previous", icon = "PREVIOUSACTIVE").prev = True
        layout.operator("node.select_same_type_step", text="Activate Same Type Next", icon = "NEXTACTIVE").prev = False

        layout.separator()

        layout.operator("node.find_node", icon='VIEWZOOM')


class NODE_MT_select_legacy(Menu):
    bl_label = "Legacy"

    def draw(self, _context):
        layout = self.layout

        layout.operator("node.select_box", icon = "BORDER_RECT").tweak = False
        layout.operator("node.select_circle", icon = "CIRCLE_SELECT")

class NODE_MT_node_group_separate(Menu):
    bl_label = "Separate"

    def draw(self, context):
        layout = self.layout

        layout.operator("node.group_separate", text = "Copy", icon = "SEPARATE_COPY").type = 'COPY'
        layout.operator("node.group_separate", text = "Move", icon = "SEPARATE").type = 'MOVE'


class NODE_MT_node(Menu):
    bl_label = "Node"

    def draw(self, context):
        layout = self.layout
        snode = context.space_data
        is_compositor = snode.tree_type == 'CompositorNodeTree'

        myvar = layout.operator("transform.translate", icon = "TRANSFORM_MOVE")
        myvar.release_confirm = True
        layout.operator("transform.rotate", icon = "TRANSFORM_ROTATE")
        layout.operator("transform.resize",  icon = "TRANSFORM_SCALE")

        layout.separator()
        layout.operator("node.clipboard_copy", text="Copy", icon='COPYDOWN')
        row = layout.row()
        row.operator_context = 'EXEC_DEFAULT'
        layout.operator("node.clipboard_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("node.duplicate_move_keep_inputs", text = "Duplicate Keep Input", icon = "DUPLICATE")
        layout.operator("node.duplicate_move", icon = "DUPLICATE")
        layout.operator("node.duplicate_move_linked", icon = "DUPLICATE")
        layout.operator("node.delete", icon = "DELETE")
        layout.operator("node.delete_reconnect", icon = "DELETE")

        layout.separator()

        layout.operator("node.join", text="Join in New Frame", icon = "JOIN")
        layout.operator("node.detach", text="Remove from Frame", icon = "DELETE")
        layout.operator("node.parent_set", text = "Frame Make Parent", icon = "PARENT_SET")

        layout.separator() #BFA - exposed context menu operator to header

        props = layout.operator("wm.call_panel", text="Rename...", icon = "RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.separator()
		## BFA - set to sub-menu
        layout.menu("NODE_MT_node_links")

        layout.separator()
		## BFA - set to sub-menu
        layout.menu("NODE_MT_node_group_separate")

        layout.separator()
		## BFA - set majority to sub-menu
        layout.menu("NODE_MT_context_menu_show_hide_menu")

        if is_compositor:

            layout.separator()

            layout.operator("node.read_viewlayers", icon='RENDERLAYERS')
            layout.operator("node.render_changed", icon='RENDERLAYERS')


class NODE_MT_node_links(Menu):
    bl_label = "Links"

    def draw(self, _context):
        layout = self.layout

        layout.operator("node.link_make", icon = "LINK_DATA").replace = False
        layout.operator("node.link_make", text="Make and Replace Links", icon = "LINK_REPLACE").replace = True
        layout.operator("node.links_cut", text="Cut Links", icon = "CUT_LINKS")
        layout.operator("node.links_detach", icon = "DETACH_LINKS")
        layout.operator("node.move_detach_links", text = "Detach Links Move", icon = "DETACH_LINKS_MOVE")
        layout.operator("node.links_mute", icon = "MUTE_IPO_ON")


class NODE_MT_context_menu_show_hide_menu(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout
        snode = context.space_data
        is_compositor = snode.tree_type == 'CompositorNodeTree'

        layout.operator("node.hide_toggle", icon = "HIDE_ON")
        layout.operator("node.mute_toggle", icon = "TOGGLE_NODE_MUTE")

        # Node previews are only available in the Compositor.
        if is_compositor:
            layout.operator("node.preview_toggle", icon = "TOGGLE_NODE_PREVIEW")

        layout.separator()

        layout.operator("node.hide_socket_toggle", icon = "HIDE_OFF")
        layout.operator("node.options_toggle", icon = "TOGGLE_NODE_OPTIONS")
        layout.operator("node.collapse_hide_unused_toggle", icon = "HIDE_UNSELECTED")

# BFA - Hidden legacy operators exposed to GUI
class NODE_MT_view_annotations(Menu):
    bl_label = "Annotations (Legacy)"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.annotate", text="Draw Annotation", icon='PAINT_DRAW',).mode = 'DRAW'
        layout.operator("gpencil.annotate", text="Draw Line Annotation", icon='PAINT_DRAW').mode = 'DRAW_STRAIGHT'
        layout.operator("gpencil.annotate", text="Draw Polyline Annotation", icon='PAINT_DRAW').mode = 'DRAW_POLY'
        layout.operator("gpencil.annotate", text="Erase Annotation", icon='ERASE').mode = 'ERASER'

        layout.separator()

        layout.operator("gpencil.annotation_add", text="Add Annotation Layer", icon='ADD')
        layout.operator("gpencil.annotation_active_frame_delete", text="Erase Annotation Active Keyframe", icon='DELETE')

class NODE_MT_view_pie(Menu):
    bl_label = "View"

    def draw(self, _context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("node.view_all")
        pie.operator("node.view_selected", icon='ZOOM_SELECTED')


class NODE_PT_active_tool(ToolActivePanelHelper, Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"


class NODE_PT_material_slots(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Slot"
    bl_ui_units_x = 12

    def draw_header(self, context):
        ob = context.object
        self.bl_label = (
            iface_("Slot %d") % (ob.active_material_index + 1) if ob.material_slots else
            iface_("Slot")
        )

    # Duplicate part of 'EEVEE_MATERIAL_PT_context_material'.
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()

        ob = context.object
        col.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index")

        col = row.column(align=True)
        col.operator("object.material_slot_add", icon='ADD', text="")
        col.operator("object.material_slot_remove", icon='REMOVE', text="")

        col.separator()

        col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

        if len(ob.material_slots) > 1:
            col.separator()

            col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if ob.mode == 'EDIT':
            row = layout.row(align=True)
            row.operator("object.material_slot_assign", text="Assign")
            row.operator("object.material_slot_select", text="Select")
            row.operator("object.material_slot_deselect", text="Deselect")


class NODE_PT_geometry_node_tool_object_types(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Object Types"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout

        snode = context.space_data
        group = snode.node_tree

        types = [
            ("is_type_mesh", "Mesh", 'MESH_DATA'),
            ("is_type_curve", "Hair Curves", 'CURVES'),
        ]
        if context.preferences.experimental.use_new_point_cloud_type:
            types.append(("is_type_point_cloud", "Point Cloud", 'POINTCLOUD_DATA'))

        col = layout.column()
        col.active = group.is_tool
        for prop, name, icon in types:
            row = col.row(align=True)
            row.label(text=name, icon=icon)
            row.prop(group, prop, text="")


class NODE_PT_geometry_node_tool_mode(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Modes"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout

        snode = context.space_data
        group = snode.node_tree

        modes = (
            ("is_mode_object", "Object Mode", 'OBJECT_DATAMODE'),
            ("is_mode_edit", "Edit Mode", 'EDITMODE_HLT'),
            ("is_mode_sculpt", "Sculpt Mode", 'SCULPTMODE_HLT'),
        )

        col = layout.column()
        col.active = group.is_tool
        for prop, name, icon in modes:
            row = col.row(align=True)
            row.label(text=name, icon=icon)
            row.prop(group, prop, text="")


class NODE_PT_node_color_presets(PresetPanel, Panel):
    """Predefined node color"""
    bl_label = "Color Presets"
    preset_subdir = "node_color"
    preset_operator = "script.execute_preset"
    preset_add_operator = "node.node_color_preset_add"


class NODE_MT_node_color_context_menu(Menu):
    bl_label = "Node Color Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("node.node_copy_color", icon='COPY_ID')


class NODE_MT_context_menu_select_menu(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("node.select_grouped", text = "Grouped", icon = "GROUP").extend = False

        layout.separator()

        layout.operator("node.select_linked_from", text = "Linked from", icon = "LINKED")
        layout.operator("node.select_linked_to", text = "Linked to", icon = "LINKED")

        layout.separator()

        layout.operator("node.select_same_type_step", text="Activate Same Type Previous", icon = "PREVIOUSACTIVE").prev = True
        layout.operator("node.select_same_type_step", text="Activate Same Type Next", icon = "NEXTACTIVE").prev = False


class NODE_MT_context_menu(Menu):
    bl_label = "Node"

    def draw(self, context):
        snode = context.space_data
        is_nested = (len(snode.path) > 1)
        is_geometrynodes = snode.tree_type == 'GeometryNodeTree'

        selected_nodes_len = len(context.selected_nodes)
        active_node = context.active_node

        layout = self.layout

        # If no nodes are selected.
        if selected_nodes_len == 0:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.menu("NODE_MT_add", icon="ADD")
            layout.operator("node.clipboard_paste", text="Paste", icon="PASTEDOWN")

            layout.separator()

            layout.operator("node.find_node", text="Find...", icon="VIEWZOOM")

            layout.separator()

            if is_geometrynodes:
                layout.operator_context = 'INVOKE_DEFAULT'
                layout.operator("node.select", text="Clear Viewer", icon="HIDE_ON").clear_viewer = True

            layout.operator("node.links_cut", icon = 'CUT_LINKS')
            layout.operator("node.links_mute", icon = 'MUTE_IPO_ON')

            if is_nested:
                layout.separator()

                layout.operator("node.tree_path_parent", text="Exit Group", icon='FILE_PARENT')

            return

        if is_geometrynodes:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("node.link_viewer", text="Link to Viewer", icon="HIDE_OFF")

            layout.separator()

        layout.operator("node.clipboard_copy", text="Copy", icon="COPYDOWN")
        layout.operator("node.clipboard_paste", text="Paste", icon="PASTEDOWN")

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.duplicate_move", icon = "DUPLICATE")

        layout.separator()

        layout.operator("node.delete", icon='DELETE')
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("node.delete_reconnect", icon='DELETE')

        if selected_nodes_len > 1:
            layout.separator()

            layout.operator("node.link_make", icon = "LINK_DATA").replace = False
            layout.operator("node.link_make", text="Make and Replace Links", icon = "LINK_DATA").replace = True
            layout.operator("node.links_detach", icon = "DETACH_LINKS")

        layout.separator()

        layout.operator("node.group_make", text="Make Group", icon="NODE_MAKEGROUP")
        layout.operator("node.group_insert", text="Insert Into Group", icon = 'NODE_GROUPINSERT')

        if active_node and active_node.type == 'GROUP':
            layout.operator("node.group_edit", text="Toggle Edit Group", icon="NODE_EDITGROUP").exit = False
            layout.operator("node.group_ungroup", text="Ungroup", icon="NODE_UNGROUP")

        if is_nested:
            layout.operator("node.tree_path_parent", text="Exit Group", icon='FILE_PARENT')

        layout.separator()

        layout.operator("node.join", text="Join in New Frame", icon = 'JOIN')
        layout.operator("node.detach", text="Remove from Frame", icon = 'DELETE')

        layout.separator()

        props = layout.operator("wm.call_panel", text="Rename...", icon = "RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.separator()

        layout.menu("NODE_MT_context_menu_select_menu")
        layout.menu("NODE_MT_context_menu_show_hide_menu")

        if active_node:
            layout.separator()
            props = layout.operator("wm.doc_view_manual", text="Blender Online Manual", icon='URL')
            props.doc_id = active_node.bl_idname


class NODE_PT_active_node_generic(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Node"

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout
        node = context.active_node

        layout.prop(node, "name", icon='NODE')
        layout.prop(node, "label", icon='NODE')


class NODE_PT_active_node_color(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Color"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODE_PT_active_node_generic"

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw_header(self, context):
        node = context.active_node
        self.layout.prop(node, "use_custom_color", text="")

    def draw_header_preset(self, _context):
        NODE_PT_node_color_presets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        node = context.active_node

        layout.enabled = node.use_custom_color

        row = layout.row()
        row.prop(node, "color", text="")
        row.menu("NODE_MT_node_color_context_menu", text="", icon='DOWNARROW_HLT')


class NODE_PT_active_node_properties(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Properties"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout
        node = context.active_node
        # set "node" context pointer for the panel layout
        layout.context_pointer_set("node", node)

        if hasattr(node, "draw_buttons_ext"):
            node.draw_buttons_ext(context, layout)
        elif hasattr(node, "draw_buttons"):
            node.draw_buttons(context, layout)

        # XXX this could be filtered further to exclude socket types
        # which don't have meaningful input values (e.g. cycles shader)
        value_inputs = [socket for socket in node.inputs if self.show_socket_input(socket)]
        if value_inputs:
            layout.separator()
            layout.label(text="Inputs:")
            for socket in value_inputs:
                row = layout.row()
                socket.draw(
                    context,
                    row,
                    node,
                    iface_(socket.label if socket.label else socket.name, socket.bl_rna.translation_context),
                )

    def show_socket_input(self, socket):
        return hasattr(socket, "draw") and socket.enabled and not socket.is_linked


class NODE_PT_texture_mapping(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Texture Mapping"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and hasattr(node, "texture_mapping") and (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        node = context.active_node
        mapping = node.texture_mapping

        layout.prop(mapping, "vector_type")

        layout.separator()

        col = layout.column(align=True)
        col.prop(mapping, "mapping_x", text="Projection X")
        col.prop(mapping, "mapping_y", text="Y")
        col.prop(mapping, "mapping_z", text="Z")

        layout.separator()

        layout.prop(mapping, "translation")
        layout.prop(mapping, "rotation")
        layout.prop(mapping, "scale")


# Node Backdrop options
class NODE_PT_backdrop(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Backdrop"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'CompositorNodeTree'

    def draw_header(self, context):
        snode = context.space_data
        self.layout.prop(snode, "show_backdrop", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        snode = context.space_data
        layout.active = snode.show_backdrop

        col = layout.column()
		##BFA - removed as double entry
		#col.prop(snode, "backdrop_channels", text="Channels")
        col.prop(snode, "backdrop_zoom", text="Zoom")

        col.prop(snode, "backdrop_offset", text="Offset")
		##BFA - removed as double entry
        #col.separator()
		#
        #col.operator("node.backimage_move", text="Move")
        #col.operator("node.backimage_fit", text="Fit")

class NODE_PT_quality(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Options"
    bl_label = "Performance"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'CompositorNodeTree' and snode.node_tree is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        snode = context.space_data
        tree = snode.node_tree
        prefs = bpy.context.preferences

        use_realtime = False
        col = layout.column()
        if prefs.experimental.use_experimental_compositors:
            col.prop(tree, "execution_mode")
            use_realtime = tree.execution_mode == 'REALTIME'
        col.prop(tree, "precision")

        col = layout.column()
        col.active = not use_realtime
        col.prop(tree, "render_quality", text="Render")
        col.prop(tree, "edit_quality", text="Edit")
        col.prop(tree, "chunk_size")

        col = layout.column()
        col.use_property_split = False
        col.active = not use_realtime
        col.prop(tree, "use_opencl")
        col.prop(tree, "use_groupnode_buffer")
        col.prop(tree, "use_two_pass")
        col.prop(tree, "use_viewer_border")

        col = layout.column()
        col.use_property_split = False
        col.prop(snode, "use_auto_render")


class NODE_PT_overlay(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Overlays"
    bl_ui_units_x = 7

    def draw(self, context):
        layout = self.layout
        layout.label(text="Node Editor Overlays")

        snode = context.space_data
        overlay = snode.overlay

        layout.active = overlay.show_overlays

        col = layout.column()
        col.prop(overlay, "show_wire_color", text="Wire Colors")

        col.separator()

        col.prop(overlay, "show_context_path", text="Context Path")
        col.prop(snode, "show_annotation", text="Annotations")

        if snode.supports_previews:
            col.separator()
            col.prop(overlay, "show_previews", text="Previews")
            if snode.tree_type == 'ShaderNodeTree':
                row = col.row()
                row.prop(overlay, "preview_shape", expand=True)
                row.active = overlay.show_previews

        if snode.tree_type == 'GeometryNodeTree':
            col.separator()
            col.prop(overlay, "show_timing", text="Timings")
            col.prop(overlay, "show_named_attributes", text="Named Attributes")


class NODE_MT_node_tree_interface_context_menu(Menu):
    bl_label = "Node Tree Interface Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("node.interface_item_duplicate", icon='DUPLICATE')


class NODE_PT_node_tree_interface_new_input(Panel):
    '''Add a new Item to the interface list'''
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "New Item"
    bl_ui_units_x = 7

    def draw(self, context):
        layout = self.layout
        layout.label(text="Add new Item")

        layout.operator('node.interface_item_new_input', text='Input ', icon='GROUPINPUT').item_type='INPUT'
        layout.operator('node.interface_item_new_output', text='Output', icon='GROUPOUTPUT').item_type='OUTPUT'
        layout.operator('node.interface_item_new_panel', text='Panel', icon='MENU_PANEL').item_type='PANEL'


class NODE_PT_node_tree_interface(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Group"
    bl_label = "Interface"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        tree = snode.edit_tree
        if tree is None:
            return False
        if tree.is_embedded_data:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        snode = context.space_data
        tree = snode.edit_tree

        split = layout.row()
        split.template_node_tree_interface(tree.interface)

        ops_col = split.column(align=True)
        ops_col.alignment = 'RIGHT'
        #ops_col.operator_menu_enum("node.interface_item_new", "item_type", icon='ADD', text="") # bfa - keep as reminder. Blender might add more content!
        ops_col.popover(panel="NODE_PT_node_tree_interface_new_input", text="")

        ops_col.separator()
        ops_col.operator("node.interface_item_duplicate", text='', icon='DUPLICATE')
        ops_col.operator("node.interface_item_remove", icon='REMOVE', text="")

        ops_col.separator()

        ops_col.operator("node.interface_item_move", icon='TRIA_UP', text="").direction = "UP" # BFA operator for GUI buttons to re-order
        ops_col.operator("node.interface_item_move", icon='TRIA_DOWN', text="").direction = "DOWN" # BFA operator for GUI buttons to re-order

        active_item = tree.interface.active
        if active_item is not None:
            layout.use_property_split = True
            layout.use_property_decorate = False

            if active_item.item_type == 'SOCKET':
                layout.prop(active_item, "socket_type", text="Type")
                layout.prop(active_item, "description")
                # Display descriptions only for Geometry Nodes, since it's only used in the modifier panel.
                if tree.type == 'GEOMETRY':
                    field_socket_types = {
                        "NodeSocketInt",
                        "NodeSocketColor",
                        "NodeSocketVector",
                        "NodeSocketBool",
                        "NodeSocketFloat",
                    }
                    if active_item.socket_type in field_socket_types:
                        if 'OUTPUT' in active_item.in_out:
                            layout.prop(active_item, "attribute_domain")
                        layout.prop(active_item, "default_attribute_name")
                layout.use_property_split = True
                active_item.draw(context, layout)

            if active_item.item_type == 'PANEL':
                layout.prop(active_item, "description")

                layout.use_property_split = False
                layout.prop(active_item, "default_closed", text="Closed by Default")


class NODE_PT_node_tree_properties(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Group"
    bl_label = "Properties"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        group = snode.edit_tree
        if group is None:
            return False
        if group.is_embedded_data:
            return False
        if group.bl_idname != "GeometryNodeTree":
            return False
        return True

    def draw(self, context):
        layout = self.layout
        snode = context.space_data
        group = snode.edit_tree
        layout.use_property_split = False
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(group, "is_modifier")
        col.prop(group, "is_tool")


def draw_socket_item_in_list(uilist, layout, item, icon):
    if uilist.layout_type in {'DEFAULT', 'COMPACT'}:
        row = layout.row(align=True)
        row.template_node_socket(color=item.color)
        row.prop(item, "name", text="", emboss=False, icon_value=icon)
    elif uilist.layout_type == 'GRID':
        layout.alignment = 'CENTER'
        layout.template_node_socket(color=item.color)


class NODE_UL_simulation_zone_items(bpy.types.UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data, _active_propname, _index):
        draw_socket_item_in_list(self, layout, item, icon)


class NODE_PT_simulation_zone_items(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Simulation State"

    input_node_type = 'GeometryNodeSimulationInput'
    output_node_type = 'GeometryNodeSimulationOutput'

    @classmethod
    def get_output_node(cls, context):
        node = context.active_node
        if node.bl_idname == cls.input_node_type:
            return node.paired_output
        if node.bl_idname == cls.output_node_type:
            return node

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        node = context.active_node
        if node is None or node.bl_idname not in [cls.input_node_type, cls.output_node_type]:
            return False
        if cls.get_output_node(context) is None:
            return False
        return True

    def draw(self, context):
        layout = self.layout

        output_node = self.get_output_node(context)

        split = layout.row()

        split.template_list(
            "NODE_UL_simulation_zone_items",
            "",
            output_node,
            "state_items",
            output_node,
            "active_index")

        ops_col = split.column()

        add_remove_col = ops_col.column(align=True)
        add_remove_col.operator("node.simulation_zone_item_add", icon='ADD', text="")
        add_remove_col.operator("node.simulation_zone_item_remove", icon='REMOVE', text="")

        ops_col.separator()

        up_down_col = ops_col.column(align=True)
        props = up_down_col.operator("node.simulation_zone_item_move", icon='TRIA_UP', text="")
        props.direction = 'UP'
        props = up_down_col.operator("node.simulation_zone_item_move", icon='TRIA_DOWN', text="")
        props.direction = 'DOWN'

        active_item = output_node.active_item
        if active_item is not None:
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout.prop(active_item, "socket_type")
            if active_item.socket_type in {'VECTOR', 'INT', 'BOOLEAN', 'FLOAT', 'RGBA', 'ROTATION'}:
                layout.prop(active_item, "attribute_domain")


class NODE_UL_repeat_zone_items(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        draw_socket_item_in_list(self, layout, item, icon)


class NODE_PT_repeat_zone_items(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Repeat"

    input_node_type = 'GeometryNodeRepeatInput'
    output_node_type = 'GeometryNodeRepeatOutput'

    @classmethod
    def get_output_node(cls, context):
        node = context.active_node
        if node.bl_idname == cls.input_node_type:
            return node.paired_output
        if node.bl_idname == cls.output_node_type:
            return node
        return None

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        node = context.active_node
        if node is None or node.bl_idname not in (cls.input_node_type, cls.output_node_type):
            return False
        if cls.get_output_node(context) is None:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        output_node = self.get_output_node(context)
        split = layout.row()
        split.template_list(
            "NODE_UL_repeat_zone_items",
            "",
            output_node,
            "repeat_items",
            output_node,
            "active_index")

        ops_col = split.column()

        add_remove_col = ops_col.column(align=True)
        add_remove_col.operator("node.repeat_zone_item_add", icon='ADD', text="")
        add_remove_col.operator("node.repeat_zone_item_remove", icon='REMOVE', text="")

        ops_col.separator()

        up_down_col = ops_col.column(align=True)
        props = up_down_col.operator("node.repeat_zone_item_move", icon='TRIA_UP', text="")
        props.direction = 'UP'
        props = up_down_col.operator("node.repeat_zone_item_move", icon='TRIA_DOWN', text="")
        props.direction = 'DOWN'

        active_item = output_node.active_item
        if active_item is not None:
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout.prop(active_item, "socket_type")

        layout.prop(output_node, "inspection_index")


class NODE_UL_bake_node_items(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        draw_socket_item_in_list(self, layout, item, icon)


class NODE_PT_bake_node_items(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Bake Items"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        node = context.active_node
        if node is None:
            return False
        if node.bl_idname != "GeometryNodeBake":
            return False
        return True

    def draw(self, context):
        layout = self.layout
        node = context.active_node
        split = layout.row()
        split.template_list(
            "NODE_UL_bake_node_items",
            "",
            node,
            "bake_items",
            node,
            "active_index")

        ops_col = split.column()

        add_remove_col = ops_col.column(align=True)
        add_remove_col.operator("node.bake_node_item_add", icon='ADD', text="")
        add_remove_col.operator("node.bake_node_item_remove", icon='REMOVE', text="")

        ops_col.separator()

        up_down_col = ops_col.column(align=True)
        props = up_down_col.operator("node.bake_node_item_move", icon='TRIA_UP', text="")
        props.direction = 'UP'
        props = up_down_col.operator("node.bake_node_item_move", icon='TRIA_DOWN', text="")
        props.direction = 'DOWN'

        active_item = node.active_item
        if active_item is not None:
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout.prop(active_item, "socket_type")
            if active_item.socket_type in {'VECTOR', 'INT', 'BOOLEAN', 'FLOAT', 'RGBA', 'ROTATION'}:
                layout.prop(active_item, "attribute_domain")
                layout.prop(active_item, "is_attribute")


class NODE_PT_index_switch_node_items(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Index Switch"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        node = context.active_node
        if node is None or node.bl_idname != 'GeometryNodeIndexSwitch':
            return False
        return True

    def draw(self, context):
        layout = self.layout
        node = context.active_node
        layout.operator("node.index_switch_item_add", icon='ADD', text="Add Item")
        col = layout.column()
        for i, item in enumerate(node.index_switch_items):
            row = col.row()
            row.label(text=node.inputs[i + 1].name)
            row.operator("node.index_switch_item_remove", icon='REMOVE', text="").index = i


# Grease Pencil properties
class NODE_PT_annotation(AnnotationDataPanel, Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    # NOTE: this is just a wrapper around the generic GP Panel

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode is not None and snode.node_tree is not None


def node_draw_tree_view(_layout, _context):
    pass


# Adapt properties editor panel to display in node editor. We have to
# copy the class rather than inherit due to the way bpy registration works.
def node_panel(cls):
    node_cls_dict = cls.__dict__.copy()

    # Needed for re-registration.
    node_cls_dict.pop("bl_rna", None)

    node_cls = type('NODE_' + cls.__name__, cls.__bases__, node_cls_dict)

    node_cls.bl_space_type = 'NODE_EDITOR'
    node_cls.bl_region_type = 'UI'
    node_cls.bl_category = "Options"
    if hasattr(node_cls, "bl_parent_id"):
        node_cls.bl_parent_id = "NODE_" + node_cls.bl_parent_id

    return node_cls
## BFA - new view menu for consistency
class NODE_PT_view(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type in ('CompositorNodeTree', 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        snode = context.space_data

        # Auto-offset nodes (called "insert_offset" in code)
        layout.prop(snode, "use_insert_offset")

classes = (
    ALL_MT_editormenu,
    NODE_HT_header,
    NODE_MT_editor_menus,
    NODE_MT_add,
    NODE_MT_pie_menus,
    NODE_MT_view,
    NODE_MT_select,
    NODE_MT_select_legacy,
    NODE_MT_node_group_separate,
    NODE_MT_node,
    NODE_MT_node_links,
    NODE_MT_node_color_context_menu,
    NODE_MT_context_menu_show_hide_menu,
    NODE_MT_context_menu_select_menu,
    NODE_MT_context_menu,
    NODE_MT_view_pie,
    NODE_MT_view_annotations,
    NODE_PT_material_slots,
    NODE_PT_geometry_node_tool_object_types,
    NODE_PT_geometry_node_tool_mode,
    NODE_PT_node_color_presets,
    NODE_MT_node_tree_interface_context_menu,
    NODE_PT_node_tree_interface_new_input,
    NODE_PT_node_tree_interface,
    NODE_PT_node_tree_properties,
    NODE_PT_active_node_generic,
    NODE_PT_active_node_color,
    NODE_PT_texture_mapping,
    NODE_PT_active_tool,
    NODE_PT_backdrop,
    NODE_PT_quality,
    NODE_PT_annotation,
    NODE_PT_overlay,
    NODE_UL_simulation_zone_items,
    NODE_PT_simulation_zone_items,
    NODE_UL_repeat_zone_items,
    NODE_UL_bake_node_items,
    NODE_PT_bake_node_items,
    NODE_PT_index_switch_node_items,
    NODE_PT_repeat_zone_items,
    NODE_PT_active_node_properties,

    node_panel(EEVEE_MATERIAL_PT_settings),
    node_panel(MATERIAL_PT_viewport),
    node_panel(WORLD_PT_viewport_display),
    node_panel(DATA_PT_light),
    node_panel(DATA_PT_EEVEE_light),
    NODE_PT_view,

    #bfa - toggles
    NODE_OT_switch_editors_to_compositor,
    NODE_OT_switch_editors_to_geometry,
    NODE_OT_switch_editors_to_shadereditor,
    NODE_OT_switch_editors_in_compositor,
    NODE_OT_switch_editors_in_geometry,
    NODE_OT_switch_editors_in_shadereditor,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
