# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Header, Menu, Panel

from bpy.app.translations import (
    contexts as i18n_contexts,
)


def has_selected_ids_in_context(context):
    if getattr(context, "id", None) is not None:
        return True
    if len(context.selected_ids) > 0:
        return True

    return False


class OUTLINER_HT_header(Header):
    bl_space_type = 'OUTLINER'

    def draw(self, context):
        self.draw_editor_type_menu(context)
        layout = self.layout

        space = context.space_data
        display_mode = space.display_mode
        scene = context.scene
        ks = context.scene.keying_sets.active

        # addon prefs for the show search prop
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        # bfa - The tab to switch to properties
        # Editor types:
        # ('VIEW_3D', 'TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'NLA_EDITOR', 'IMAGE_EDITOR',
        # 'CLIP_EDITOR', 'TEXT_EDITOR', 'NODE_EDITOR', 'PROPERTIES', 'OUTLINER', 'USER_PREFERENCES', 'INFO', 'FILE_BROWSE)
        row = layout.row(align=True)
        row.operator("screen.space_type_set_or_cycle", text="", icon='BUTS').space_type = 'PROPERTIES'

        layout.prop(space, "display_mode", icon_only=True)

        #BFA - Always show header view and col entries
        OUTLINER_MT_editor_menus.draw_collapsible(context, layout) # Collapsing everything in OUTLINER_MT_editor_menus when ticking collapse menus checkbox
        '''
        if display_mode == 'DATA_API':
            OUTLINER_MT_editor_menus.draw_collapsible(context, layout)# Collapsing everything in OUTLINER_MT_editor_menus when ticking collapse menus checkbox
        if display_mode == 'LIBRARY_OVERRIDES':
            layout.prop(space, "lib_override_view_mode", text="")
        '''

        layout.separator_spacer()

        row = layout.row(align=True)

        row.prop(addon_prefs,"outliner_show_search", icon="VIEWZOOM", text = "") # show search text prop
        if addon_prefs.outliner_show_search:
            # No text filtering for library override hierarchies. The tree is lazy built to avoid
            # performance issues in complex files.
            if display_mode == 'LIBRARY_OVERRIDES' and space.lib_override_view_mode == 'HIERARCHIES':
                filter_text_supported = False
            else:
                row = layout.row(align=True)
                row.prop(space, "filter_text", text="")

        if display_mode == 'SEQUENCE':
            row = layout.row(align=True)
            row.prop(space, "use_sync_select", icon='UV_SYNC_SELECT', text="")

        row = layout.row(align=True)
        if display_mode in {'SCENES', 'VIEW_LAYER', 'LIBRARY_OVERRIDES'}:
            row.popover(
                panel="OUTLINER_PT_filter",
                text="",
                icon='FILTER',
            )

        if display_mode in {'LIBRARIES', 'ORPHAN_DATA'}:
            row.prop(space, "use_filter_id_type", text="", icon='FILTER')
            sub = row.row(align=True)
            if space.use_filter_id_type:
                sub.prop(space, "filter_id_type", text="", icon_only=True)
		#BFA - already shown elsewhere
        # if display_mode == 'VIEW_LAYER':
        #    layout.operator("outliner.collection_new", text="", icon='COLLECTION_NEW').nested = True

        #BFA - has a drop down and button with consistenty naming
        #elif display_mode == 'ORPHAN_DATA':
        #    layout.operator("outliner.orphans_purge", text="Purge").do_recursive = True

        if space.display_mode == 'DATA_API':
            layout.separator()

            row = layout.row(align=True)

            row.operator("outliner.keyingset_add_selected", icon='ADD', text="")
            row.operator("outliner.keyingset_remove_selected", icon='REMOVE', text="")


            if ks:
                row = layout.row()
                row.prop_search(scene.keying_sets, "active", scene, "keying_sets", text="")

                row = layout.row(align=True)
                row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
                row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')
            else:
                row = layout.row()
                row.label(text="No Keying Set Active")

#BFA - collection header menu
class   OUTLINER_MT_object_collection(Menu):
    bl_label = "Collection"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.move_to_collection", icon='GROUP')
        layout.operator("object.link_to_collection", icon='GROUP')

        layout.separator()
        layout.operator("collection.objects_remove", icon = "DELETE")
        layout.operator("collection.objects_remove_all", icon = "DELETE")

        layout.separator()

        layout.operator("collection.objects_add_active", icon='GROUP')
        layout.operator("collection.objects_remove_active", icon = "DELETE")


# BFA
class BFA_OUTLINER_PT_scene_ops(Panel):
    bl_label = "New Scene"
    bl_space_type = "OUTLINER"
    bl_region_type = "HEADER"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="New Scene")
        col.operator_enum(operator="scene.new", property="type")


class OUTLINER_MT_editor_menus(Menu):
    bl_idname = "OUTLINER_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        space = context.space_data

        #space = context.space_data
        display_mode = space.display_mode

        layout.menu("OUTLINER_MT_view") #BFA - view menu

        if display_mode == 'DATA_API':
            layout.menu("OUTLINER_MT_edit_datablocks")

        if display_mode == 'LIBRARY_OVERRIDES':
            layout.prop(space, "lib_override_view_mode", text="")

        elif display_mode in ('SCENES','VIEW_LAYER' ):

            layout.menu("OUTLINER_MT_object_collection", text = "Col")

            layout.separator()

            layout.operator("outliner.collection_new", text="", icon='COLLECTION_NEW')

            if display_mode == 'SCENES':
                # BFA - Outliner - Scene View - Add Scene creation operator to header
                layout.separator()
                layout.popover("BFA_OUTLINER_PT_scene_ops", text="", icon="SCENE_DATA")

        elif display_mode == 'ORPHAN_DATA':
            layout.separator()

            layout.operator("outliner.orphans_purge", text="Clean Up")
            layout.menu("TOPBAR_MT_file_cleanup", text = "", icon = "DOWNARROW_HLT")
# BFA
class OUTLINER_MT_pie_menus(Menu):
    bl_label = "Pie Menus"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.operator("wm.call_menu_pie", text = "View", icon = "MENU_PANEL").name = 'OUTLINER_MT_view_pie'

# BFA
class OUTLINER_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        context = bpy.context
        space = context.space_data


        layout.operator("outliner.show_active", icon = "CENTER")

        layout.separator()

        layout.operator("outliner.show_one_level", text = "Show One Level", icon = "HIERARCHY_DOWN")
        layout.operator("outliner.show_one_level", text = "Hide One Level", icon = "HIERARCHY_UP").open = False

        layout.operator("outliner.expanded_toggle", icon = 'INVERSE')
        layout.operator("outliner.show_hierarchy", icon = "HIERARCHY")

        layout.operator("outliner.select_box", icon = 'BORDER_RECT')

        layout.separator()

        layout.operator("outliner.select_all", text = "Select All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("outliner.select_all", text="None", icon='SELECT_NONE').action = 'DESELECT'
        layout.operator("outliner.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        # BFA - only shows in view menu entry, but not in the orphan data mode.
        if not (context.area.type == 'OUTLINER' and context.space_data.display_mode == 'ORPHAN_DATA'):
            layout.separator()
            layout.operator("outliner.orphans_manage", text="Manage Unused Data", icon = "ORPHAN_DATA")

        layout.separator()
        layout.menu("OUTLINER_MT_pie_menus")
        layout.menu("INFO_MT_area")



class OUTLINER_MT_context_menu(Menu):
    bl_label = "Outliner"

    @staticmethod
    def draw_common_operators(layout):
        layout.separator()

        ## BFA - The original from blender
        # layout.menu("OUTLINER_MT_liboverride", icon='LIBRARY_DATA_OVERRIDE')

        # layout.separator()

        # layout.menu("OUTLINER_MT_context_menu_view")

        # layout.separator()

        # layout.menu("INFO_MT_area")

        ## BFA - Moved the Library Override menu up a level
        layout.operator_menu_enum(
            "outliner.liboverride_operation",
            "selection_set",
            text="Make Library Override").type = 'OVERRIDE_LIBRARY_CREATE_HIERARCHY'
        layout.operator_menu_enum(
            "outliner.liboverride_operation",
            "selection_set",
            text="Reset Library Override").type = 'OVERRIDE_LIBRARY_RESET'
        layout.operator_menu_enum(
            "outliner.liboverride_operation",
            "selection_set",
            text="Clear Library Override").type = 'OVERRIDE_LIBRARY_CLEAR_SINGLE'

        layout.separator()

        layout.operator_menu_enum(
            "outliner.liboverride_troubleshoot_operation",
            "type",
            text="Troubleshoot Library Override").selection_set = 'SELECTED'

        layout.separator()

        layout.menu_contents("OUTLINER_MT_asset")



    def draw(self, context):
        space = context.space_data

        layout = self.layout

        if space.display_mode == 'VIEW_LAYER':
            OUTLINER_MT_collection_new.draw_without_context_menu(context, layout)
            layout.separator()

        OUTLINER_MT_context_menu.draw_common_operators(layout)


class OUTLINER_MT_context_menu_view(Menu):
    bl_label = "View"

    def draw(self, _context):
        layout = self.layout

        layout.operator("outliner.show_active", icon = "CENTER")

        layout.separator()

        layout.operator("outliner.show_one_level", text = "Show One Level", icon = "HIERARCHY_DOWN")
        layout.operator("outliner.show_one_level", text = "Hide One Level", icon = "HIERARCHY_UP").open = False

        layout.operator("outliner.expanded_toggle", icon = 'INVERSE')
        layout.operator("outliner.show_hierarchy", icon = "HIERARCHY")


class OUTLINER_MT_view_pie(Menu):
    bl_label = "View"

    def draw(self, _context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("outliner.show_hierarchy")
        pie.operator("outliner.show_active", icon='ZOOM_SELECTED')


class OUTLINER_MT_id_data(Menu):
    bl_label = "ID Data"

    @classmethod
    def poll(cls, context):
        return has_selected_ids_in_context(context)

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("outliner.id_operation", "type")

        id_linked = getattr(context, "id", None)
        if id_linked and id_linked.library:
            layout.separator()
            layout.operator("outliner.id_linked_relocate", text="Relocate", icon="LINK_DATA")


class OUTLINER_MT_edit_datablocks(Menu):
    bl_label = "Edit"

    def draw(self, _context):
        layout = self.layout

        layout.operator("outliner.keyingset_add_selected", icon = "KEYINGSET")
        layout.operator("outliner.keyingset_remove_selected", icon = "DELETE")

        layout.separator()

        layout.operator("outliner.drivers_add_selected", icon = "DRIVER")
        layout.operator("outliner.drivers_delete_selected", icon = "DELETE")

class OUTLINER_MT_collection_view_layer(Menu):
    bl_label = "View Layer"

    def draw(self, context):
        layout = self.layout

        layout.operator("outliner.collection_exclude_set", icon="CHECKBOX_HLT")
        layout.operator("outliner.collection_exclude_clear", icon="CHECKBOX_DEHLT")

        layout.operator("outliner.collection_holdout_set", icon="HOLDOUT_ON")
        layout.operator("outliner.collection_holdout_clear", icon="HOLDOUT_OFF")

        if context.engine == 'CYCLES':
            layout.operator("outliner.collection_indirect_only_set", icon="INDIRECT_ONLY_ON")
            layout.operator("outliner.collection_indirect_only_clear", icon="INDIRECT_ONLY_OFF")


class OUTLINER_MT_collection_visibility(Menu):
    bl_label = "Visibility"

    def draw(self, _context):
        layout = self.layout

        layout.operator("outliner.collection_isolate", text="Isolate", icon="HIDE_UNSELECTED")

        layout.separator()

        layout.operator("outliner.collection_show_inside", text="Show All Inside", icon="HIDE_OFF")
        layout.operator("outliner.collection_hide_inside", text="Hide All Inside", icon="HIDE_ON")
		# BFA - redundant view toggles, removed. TODO: They are usueful for batch operation (hold ALT to use on all)


class OUTLINER_MT_collection(Menu):
    bl_label = "Collection"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.operator("outliner.collection_new", text="New", icon='COLLECTION_NEW', text_ctxt=i18n_contexts.id_collection)
        layout.operator("outliner.collection_new", text="New Nested", icon='COLLECTION_NEW', text_ctxt=i18n_contexts.id_collection).nested = True
        layout.operator("outliner.collection_duplicate", text="Duplicate Collection", icon="DUPLICATE")
        layout.operator("outliner.collection_duplicate_linked", text="Duplicate Linked", icon="DUPLICATE") #BFA - exposed hidden operator
        layout.operator("outliner.id_copy", text="Copy", icon='COPYDOWN')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("outliner.delete", text="Delete", icon="DELETE")
        layout.operator("outliner.delete", text="Delete Hierarchy", icon="DELETE").hierarchy = True

        layout.separator()

        layout.operator("outliner.collection_objects_select", text="Select Objects", icon="RESTRICT_SELECT_OFF")
        layout.operator("outliner.collection_objects_deselect", text="Deselect Objects", icon = "SELECT_NONE")

        layout.separator()

        layout.operator("outliner.collection_instance", text="Instance to Scene", icon = "OUTLINER_OB_GROUP_INSTANCE")

        if space.display_mode != 'VIEW_LAYER':
            layout.operator("outliner.collection_link", text="Link to Scene", icon = "LINKED")

            layout.separator()

            row = layout.row(align=True)
            row.operator_enum("outliner.collection_color_tag_set", "color", icon_only=True)

        layout.operator("outliner.id_operation", text="Unlink", icon = "UNLINKED").type = 'UNLINK'

        layout.separator()

        layout.menu("OUTLINER_MT_collection_visibility")

        if space.display_mode == 'VIEW_LAYER':

            layout.separator()
			#layout.menu("OUTLINER_MT_collection_view_layer", icon='RENDERLAYERS') #BFA - redundant

            row = layout.row(align=True)
            row.operator_enum("outliner.collection_color_tag_set", "color", icon_only=True)

        layout.separator()

        layout.menu("OUTLINER_MT_id_data")

        layout.separator()

        OUTLINER_MT_context_menu.draw_common_operators(layout)


class OUTLINER_MT_collection_new(Menu):
    bl_label = "Collection"

    @staticmethod
    def draw_without_context_menu(_context, layout):
        layout.operator("outliner.collection_new", text="New Collection", icon = "GROUP").nested = False
        layout.operator("outliner.id_paste", text="Paste Data-Blocks", icon='PASTEDOWN')

    def draw(self, context):
        layout = self.layout
		# BFA - exposed hidden operators
        layout.operator("outliner.collection_new", text="New Nested", icon='COLLECTION_NEW').nested = True
        layout.operator("outliner.collection_new", text="New", icon='COLLECTION_NEW')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        OUTLINER_MT_context_menu.draw_common_operators(layout)


class OUTLINER_MT_object(Menu):
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout

        space = context.space_data
		# BFA - order changed to be consistent with other menus
        layout.operator("outliner.object_operation", text="Select", icon="RESTRICT_SELECT_OFF").type = 'SELECT'
        layout.operator("outliner.object_operation", text="Select Hierarchy", icon="RESTRICT_SELECT_OFF").type = 'SELECT_HIERARCHY'
        layout.operator("outliner.object_operation", text="Deselect", icon = "SELECT_NONE").type = 'DESELECT'

        layout.separator()

        layout.operator("object.duplicate", text="Duplicate", icon='DUPLICATE')
        layout.operator("object.duplicate", text="Duplicate Linked", icon='DUPLICATE').linked = True

        layout.separator()

        layout.operator("outliner.id_copy", text="Copy", icon='COPYDOWN')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("outliner.delete", text="Delete", icon="DELETE")

        layout.operator("outliner.delete", text="Delete Hierarchy", icon="DELETE").hierarchy = True

        layout.separator()

        if not (space.display_mode == 'VIEW_LAYER' and not space.use_filter_collection):
            layout.operator("outliner.id_operation", text="Unlink", icon = "UNLINKED").type = 'UNLINK'
            layout.separator()

        layout.separator()

        layout.menu("OUTLINER_MT_id_data")
        
        layout.separator()

        OUTLINER_MT_context_menu.draw_common_operators(layout)


class OUTLINER_MT_asset(Menu):
    bl_label = "Assets"

    @classmethod
    def poll(cls, context):
        return has_selected_ids_in_context(context)

    def draw(self, _context):
        layout = self.layout

        layout.operator("asset.mark", icon='ASSET_MANAGER')
        layout.operator("asset.clear", text="Clear Asset", icon = "CLEAR").set_fake_user = False
        layout.operator("asset.clear", text="Clear Asset (Set Fake User)", icon = "CLEAR").set_fake_user = True


# BFA - Now hidden moved up a level in Outliner
class OUTLINER_MT_liboverride(Menu):
    bl_label = "Library Override"

    @classmethod
    def poll(cls, context):
        return has_selected_ids_in_context(context)

    def draw(self, _context):
        layout = self.layout

        layout.operator_menu_enum(
            "outliner.liboverride_operation", "selection_set",
            text="Make",
        ).type = 'OVERRIDE_LIBRARY_CREATE_HIERARCHY'
        layout.operator_menu_enum(
            "outliner.liboverride_operation",
            "selection_set",
            text="Reset",
        ).type = 'OVERRIDE_LIBRARY_RESET'
        layout.operator_menu_enum(
            "outliner.liboverride_operation", "selection_set",
            text="Clear",
        ).type = 'OVERRIDE_LIBRARY_CLEAR_SINGLE'

        layout.separator()

        layout.operator_menu_enum(
            "outliner.liboverride_troubleshoot_operation", "type",
            text="Troubleshoot",
        ).selection_set = 'SELECTED'

# BFA - this has substantial changes, beware.
class OUTLINER_PT_filter(Panel):
    bl_space_type = 'OUTLINER'
    bl_region_type = 'HEADER'
    bl_label = "Filter"

    # BFA - Helper method to simplify drawing of properties            
    @staticmethod
    def draw_prop_row(layout, data, prop_name, text, *, icon=None):
        row = layout.row()
        
        if icon is not None:
            row.label(text='', icon=icon)
        
        row.prop(data, prop_name, text=text)
        return row

    def draw(self, context):
        layout = self.layout

        space = context.space_data
        display_mode = space.display_mode
        
        if display_mode == 'VIEW_LAYER':
            layout.label(text="Restriction Toggles")
            row = layout.row(align=True)
            row.separator()
            row.prop(space, "show_restrict_column_enable", icon_only=True)
            row.prop(space, "show_restrict_column_select", icon_only=True)
            row.prop(space, "show_restrict_column_hide", icon_only=True)
            row.prop(space, "show_restrict_column_viewport", icon_only=True)
            row.prop(space, "show_restrict_column_render", icon_only=True)
            row.prop(space, "show_restrict_column_holdout", icon_only=True)
            row.prop(space, "show_restrict_column_indirect_only", icon_only=True)
            layout.separator()
            
        elif display_mode == 'SCENES':
            layout.label(text="Restriction Toggles")
            row = layout.row(align=True)
            row.separator()
            row.prop(space, "show_restrict_column_select", icon_only=True)
            row.prop(space, "show_restrict_column_hide", icon_only=True)
            row.prop(space, "show_restrict_column_viewport", icon_only=True)
            row.prop(space, "show_restrict_column_render", icon_only=True)
            layout.separator()

        col = layout.column(align=True)
        
        if display_mode != 'DATA_API':
            col.prop(space, "use_sort_alpha")
        if display_mode != 'LIBRARY_OVERRIDES':
            col.prop(space, "use_sync_select", text="Sync Selection")
            col.prop(space, "show_mode_column", text="Show Mode Column")

        # Same exception for library overrides as in OUTLINER_HT_header.
        if display_mode == 'LIBRARY_OVERRIDES' and space.lib_override_view_mode == 'HIERARCHIES':
            filter_text_supported = False
        else:
            col = layout.column(align=True)
            col.label(text="Search")
            
            row = col.row()
            row.separator()
            col = row.column(align=True)
            
            col.prop(space, "use_filter_complete", text="Exact Match")
            col.prop(space, "use_filter_case_sensitive", text="Case Sensitive")

        if display_mode == 'LIBRARY_OVERRIDES' and space.lib_override_view_mode == 'PROPERTIES' and bpy.data.libraries:
            row = layout.row()
            row.label(icon='LIBRARY_DATA_OVERRIDE')
            row.prop(space, "use_filter_lib_override_system", text="System Overrides")

        if display_mode == 'VIEW_LAYER':
            layout.label(text="Filter")
            row = layout.row()
            row.separator()
            col = row.column(align=True)        

            self.draw_prop_row(col, space, "use_filter_view_layers", text="All View Layers", icon='RENDERLAYERS')
            self.draw_prop_row(col, space, "use_filter_collection", text="Collections", icon='OUTLINER_COLLECTION')
                
            row = col.row()
            row.label(icon='OBJECT_DATAMODE')
            row = row.row(align=True)
            row.alignment = 'LEFT'
            row.prop(space, "use_filter_object", text="Objects")

            if space.use_filter_object:
                row.label(icon='DISCLOSURE_TRI_DOWN')
            else:
                row.label(icon='DISCLOSURE_TRI_RIGHT')
            
            if space.use_filter_object:
                row = col.row(align=True)
                row.prop(space, "filter_state", text="")
                if space.filter_state != 'ALL':
                    row.prop(space, "filter_invert", text="", icon='ARROW_LEFTRIGHT')
                
                row = col.row()
                row.separator()
                col = row.column(align=True)
                
                self.draw_prop_row(col, space, "use_filter_object_content", text="Object Contents", icon='OBJECT_CONTENTS')
                self.draw_prop_row(col, space, "use_filter_children", text="Object Children", icon='CHILD')

                if bpy.data.meshes:
                    self.draw_prop_row(col, space, "use_filter_object_mesh", text="Meshes", icon='MESH_DATA')

                if bpy.data.armatures:
                    self.draw_prop_row(col, space, "use_filter_object_armature", text="Armatures", icon='ARMATURE_DATA')

                    if space.use_filter_object_armature:
                        self.draw_prop_row(col, space, "use_filter_pose_bones", text="Pose Bones", icon='BONE_DATA')

                if bpy.data.lights:
                    self.draw_prop_row(col, space, "use_filter_object_light", text="Lights", icon='LIGHT_DATA')

                if bpy.data.cameras:
                    self.draw_prop_row(col, space, "use_filter_object_camera", text="Cameras", icon='CAMERA_DATA')
                
                if bpy.data.grease_pencils:
                    self.draw_prop_row(col, space, "use_filter_object_grease_pencil", text="Grease Pencil", icon='STROKE')
                
                self.draw_prop_row(col, space, "use_filter_object_empty", text="Empties", icon='EMPTY_DATA')
                
                other_data = (
                    "curves",
                    "metaballs",
                    "hair_curves",
                    "pointclouds",
                    "volumes",
                    "lightprobes",
                    "lattices",
                    "fonts",
                    "speakers",
                )    
                
                has_others = any((getattr(bpy.data, data_type, False) for data_type in other_data))
                
                if has_others:
                    self.draw_prop_row(col, space, "use_filter_object_others", text="Others", icon='OBJECT_DATAMODE')

classes = (
    OUTLINER_HT_header,
    OUTLINER_MT_object_collection, # BFA - menu
    BFA_OUTLINER_PT_scene_ops, # BFA - menu
    OUTLINER_MT_editor_menus,
    OUTLINER_MT_pie_menus, # BFA - menu
    OUTLINER_MT_view, # BFA - menu
    OUTLINER_MT_edit_datablocks,
    OUTLINER_MT_collection,
    OUTLINER_MT_collection_new,
    OUTLINER_MT_collection_visibility,
    OUTLINER_MT_collection_view_layer,
    OUTLINER_MT_id_data,
    OUTLINER_MT_object,
    OUTLINER_MT_asset,
    OUTLINER_MT_liboverride,
    OUTLINER_MT_context_menu,
    OUTLINER_MT_context_menu_view,#BFA - not used
    OUTLINER_MT_view_pie,
    OUTLINER_PT_filter,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
