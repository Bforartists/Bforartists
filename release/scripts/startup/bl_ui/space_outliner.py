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
from bpy.types import Header, Menu, Panel
from bpy.app.translations import (
    contexts as i18n_contexts,
    pgettext_iface as iface_,
)


################################ Switch between the editors ##########################################

# Editor types:
# ('VIEW_3D', 'TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'NLA_EDITOR', 'IMAGE_EDITOR',
# 'CLIP_EDITOR', 'TEXT_EDITOR', 'NODE_EDITOR', 'PROPERTIES', 'OUTLINER', 'USER_PREFERENCES', 'INFO', 'FILE_BROWSE)

class OUTLINER_OT_switch_editors_to_properties(bpy.types.Operator):
    """Switch to Properties editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_properties"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Properties Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="PROPERTIES")
        return {'FINISHED'}

class OUTLINER_OT_switch_editors_to_outliner(bpy.types.Operator):
    """Switch to Outliner Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_outliner"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Outliner Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="OUTLINER")
        return {'FINISHED'}


class OUTLINER_HT_header(Header):
    bl_space_type = 'OUTLINER'

    def draw(self, context):
        layout = self.layout

        space = context.space_data
        display_mode = space.display_mode
        scene = context.scene
        ks = context.scene.keying_sets.active

        # addon prefs for the show search prop
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        row = layout.row(align=True)
        row.operator("wm.switch_editor_to_properties", text="", icon='BUTS')

        layout.prop(space, "display_mode", icon_only=True)

        OUTLINER_MT_editor_menus.draw_collapsible(context, layout) # Collapsing everything in OUTLINER_MT_editor_menus when ticking collapse menus checkbox

        layout.separator_spacer()

        row = layout.row(align=True)

        row.prop(addon_prefs,"outliner_show_search", icon='VIEWZOOM', text = "") # show search text prop
        if addon_prefs.outliner_show_search:
            row.prop(space, "filter_text", text="")

        if display_mode == 'SEQUENCE':
            row = layout.row(align=True)
            row.prop(space, "use_sync_select", icon='UV_SYNC_SELECT', text="")

        row = layout.row(align=True)
        if display_mode in {'SCENES', 'VIEW_LAYER'}:
            row.popover(
                panel="OUTLINER_PT_filter",
                text="",
                icon='FILTER',
            )
        elif display_mode in {'LIBRARIES', 'ORPHAN_DATA'}:
            row.prop(space, "use_filter_id_type", text="", icon='FILTER')
            sub = row.row(align=True)
            if space.use_filter_id_type:
                sub.prop(space, "filter_id_type", text="", icon_only=True)

        if space.display_mode == 'DATA_API':
            layout.separator()

            if ks:
                row = layout.row()
                row.prop_search(scene.keying_sets, "active", scene, "keying_sets", text="")

                row = layout.row(align=True)
                row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
                row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')
            else:
                row = layout.row()
                row.label(text="No Keying Set Active")

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

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class OUTLINER_MT_editor_menus(Menu):
    bl_idname = "OUTLINER_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        space = context.space_data

        space = context.space_data
        display_mode = space.display_mode

        layout.menu("OUTLINER_MT_view") # bfa - view menu

        if display_mode == 'DATA_API':
            layout.menu("OUTLINER_MT_edit_datablocks")

        elif display_mode == 'VIEW_LAYER':
            layout.menu("OUTLINER_MT_object_collection", text = "Col")

            layout.separator()

            layout.operator("outliner.collection_new", text="", icon='COLLECTION_NEW')

        elif display_mode == 'ORPHAN_DATA':
            layout.separator()

            layout.operator("outliner.orphans_purge", text="Purge")


# Workaround to separate the tooltips for Hide one level
class OUTLINER_MT_view_hide_one_level(bpy.types.Operator):
    """Collapse all entries by one level """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "outliner.hide_one_level"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide one level"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.outliner.show_one_level(open = False)
        return {'FINISHED'}


# Workaround to separate the tooltips
class OUTLINER_MT_view_select_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "outliner.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.outliner.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class OUTLINER_MT_view_select_none(bpy.types.Operator):
    """Deselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "outliner.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.outliner.select_all(action = 'DESELECT')
        return {'FINISHED'}


class OUTLINER_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.operator("outliner.show_active", icon = "CENTER")

        layout.separator()

        layout.operator("outliner.show_one_level", text = "Show One Level", icon = "HIERARCHY_DOWN")
        layout.operator("outliner.hide_one_level", text = "Hide One Level", icon = "HIERARCHY_UP") # bfa - separated tooltip
        layout.operator("outliner.expanded_toggle", icon = 'INVERSE')
        layout.operator("outliner.show_hierarchy", icon = "HIERARCHY")

        layout.separator()

        layout.operator("outliner.select_box", icon = 'BORDER_RECT')

        layout.separator()

        layout.operator("outliner.select_all", text = "Select All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("outliner.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("outliner.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.menu("INFO_MT_area")


class OUTLINER_MT_edit_datablocks(Menu):
    bl_label = "Edit"

    def draw(self, _context):
        layout = self.layout

        layout.operator("outliner.keyingset_add_selected", icon = "KEYINGSET")
        layout.operator("outliner.keyingset_remove_selected", icon = "DELETE")

        layout.separator()

        layout.operator("outliner.drivers_add_selected", icon = "DRIVER")
        layout.operator("outliner.drivers_delete_selected", icon = "DELETE")


class OUTLINER_MT_collection_visibility(Menu):
    bl_label = "Visibility"

    def draw(self, _context):
        layout = self.layout

        layout.operator("outliner.collection_isolate", text="Isolate", icon="HIDE_UNSELECTED")

        layout.separator()

        layout.operator("outliner.collection_show_inside", text="Show All Inside", icon="HIDE_OFF")
        layout.operator("outliner.collection_hide_inside", text="Hide All Inside", icon="HIDE_ON")


class OUTLINER_MT_collection(Menu):
    bl_label = "Collection"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.operator("outliner.collection_new", text="New", icon='COLLECTION_NEW')
        layout.operator("outliner.collection_new", text="New Nested", icon='COLLECTION_NEW').nested = True
        layout.operator("outliner.collection_duplicate", text="Duplicate Collection", icon = "DUPLICATE")
        layout.operator("outliner.collection_duplicate_linked", text="Duplicate Linked", icon = "DUPLICATE")
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
        layout.operator("outliner.id_operation", text="Unlink", icon = "UNLINKED").type = 'UNLINK'

        layout.separator()

        layout.menu("OUTLINER_MT_collection_visibility")

        layout.separator()

        layout.operator_menu_enum("outliner.id_operation", "type", text="ID Data")


class OUTLINER_MT_collection_new(Menu):
    bl_label = "Collection"

    @staticmethod
    def draw_without_context_menu(context, layout):
        layout.operator("outliner.collection_new", text="New Collection").nested = False
        layout.operator("outliner.id_paste", text="Paste Data-Blocks", icon='PASTEDOWN')

    def draw(self, context):
        layout = self.layout

        layout.operator("outliner.collection_new", text="New Nested", icon='COLLECTION_NEW').nested = True
        layout.operator("outliner.collection_new", text="New", icon='COLLECTION_NEW')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')


class OUTLINER_MT_object(Menu):
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout

        space = context.space_data
        obj = context.active_object
        object_mode = 'OBJECT' if obj is None else obj.mode

        layout.operator("outliner.object_operation", text="Select", icon="RESTRICT_SELECT_OFF").type = 'SELECT'
        layout.operator("outliner.object_operation", text="Select Hierarchy", icon="RESTRICT_SELECT_OFF").type = 'SELECT_HIERARCHY'
        layout.operator("outliner.object_operation", text="Deselect", icon = "SELECT_NONE").type = 'DESELECT'

        layout.separator()

        layout.operator("outliner.id_copy", text="Copy", icon='COPYDOWN')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("outliner.delete", text="Delete", icon="DELETE")

        layout.operator("outliner.delete", text="Delete Hierarchy", icon="DELETE").hierarchy = True

        layout.separator()

        if object_mode in {'EDIT', 'POSE'}:
            name = bpy.types.Object.bl_rna.properties["mode"].enum_items[object_mode].name
            layout.operator("outliner.object_operation",
                            text=iface_("%s Set", i18n_contexts.operator_default) % name).type = 'OBJECT_MODE_ENTER'
            layout.operator("outliner.object_operation",
                            text=iface_("%s Clear", i18n_contexts.operator_default) % name).type = 'OBJECT_MODE_EXIT'
            del name

            layout.separator()

        if not (space.display_mode == 'VIEW_LAYER' and not space.use_filter_collection):
            layout.operator("outliner.id_operation", text="Unlink", icon = "UNLINKED").type = 'UNLINK'
            layout.separator()

        layout.operator_menu_enum("outliner.id_operation", "type", text="ID Data")


class OUTLINER_PT_filter(Panel):
    bl_space_type = 'OUTLINER'
    bl_region_type = 'HEADER'
    bl_label = "Filter"

    def draw(self, context):
        layout = self.layout

        space = context.space_data
        display_mode = space.display_mode

        if display_mode == 'VIEW_LAYER':
            layout.label(text="Restriction Toggles:")
            row = layout.row(align=True)
            row.prop(space, "show_restrict_column_enable", text="")
            row.prop(space, "show_restrict_column_select", text="")
            row.prop(space, "show_restrict_column_hide", text="")
            row.prop(space, "show_restrict_column_viewport", text="")
            row.prop(space, "show_restrict_column_render", text="")
            row.prop(space, "show_restrict_column_holdout", text="")
            row.prop(space, "show_restrict_column_indirect_only", text="")
            layout.separator()
        elif display_mode == 'SCENES':
            layout.label(text="Restriction Toggles:")
            row = layout.row(align=True)
            row.prop(space, "show_restrict_column_select", text="")
            row.prop(space, "show_restrict_column_hide", text="")
            row.prop(space, "show_restrict_column_viewport", text="")
            row.prop(space, "show_restrict_column_render", text="")
            layout.separator()

        if display_mode != 'DATA_API':
            col = layout.column(align=True)
            col.prop(space, "use_sort_alpha")

        row = layout.row(align=True)
        row.prop(space, "use_sync_select", text="Sync Selection")

        col = layout.column(align=True)
        col.label(text="Search:")
        col.prop(space, "use_filter_complete", text="Exact Match")
        col.prop(space, "use_filter_case_sensitive", text="Case Sensitive")

        if display_mode != 'VIEW_LAYER':
            return

        layout.label(text="Filter:")

        col = layout.column(align=True)

        row = col.row()
        row.label(icon='GROUP')
        row.prop(space, "use_filter_collection", text="Collections")
        row = col.row()
        row.label(icon='OBJECT_DATAMODE')
        row.prop(space, "use_filter_object", text="Objects")
        row.prop(space, "filter_state", text="")

        sub = col.column(align=True)
        sub.active = space.use_filter_object

        row = sub.row()
        row.label(icon='OBJECT_DATAMODE')
        row.prop(space, "use_filter_object_content", text="Object Contents")
        row = sub.row()
        row.label(icon='CHILD')
        row.prop(space, "use_filter_children", text="Object Children")

        if bpy.data.meshes:
            row = sub.row()
            row.label(icon='MESH_DATA')
            row.prop(space, "use_filter_object_mesh", text="Meshes")
        if bpy.data.armatures:
            row = sub.row()
            row.label(icon='ARMATURE_DATA')
            row.prop(space, "use_filter_object_armature", text="Armatures")
        if bpy.data.lights:
            row = sub.row()
            row.label(icon='LIGHT_DATA')
            row.prop(space, "use_filter_object_light", text="Lights")
        if bpy.data.cameras:
            row = sub.row()
            row.label(icon='CAMERA_DATA')
            row.prop(space, "use_filter_object_camera", text="Cameras")
        row = sub.row()
        row.label(icon='EMPTY_DATA')
        row.prop(space, "use_filter_object_empty", text="Empties")

        if (
                bpy.data.curves or
                bpy.data.metaballs or
                (hasattr(bpy.data, "hairs") and bpy.data.hairs) or
                (hasattr(bpy.data, "pointclouds") and bpy.data.pointclouds) or
                bpy.data.volumes or
                bpy.data.lightprobes or
                bpy.data.lattices or
                bpy.data.fonts or
                bpy.data.speakers
        ):
            row = sub.row()
            row.label(icon='BLANK1')
            row.prop(space, "use_filter_object_others", text="Others")


classes = (
    OUTLINER_OT_switch_editors_to_properties,
    OUTLINER_OT_switch_editors_to_outliner,
    OUTLINER_HT_header,
    OUTLINER_MT_object_collection,
    ALL_MT_editormenu,
    OUTLINER_MT_editor_menus,
    OUTLINER_MT_view_hide_one_level,
    OUTLINER_MT_view_select_inverse,
    OUTLINER_MT_view_select_none,
    OUTLINER_MT_view,
    OUTLINER_MT_edit_datablocks,
    OUTLINER_MT_collection,
    OUTLINER_MT_collection_new,
    OUTLINER_MT_collection_visibility,
    OUTLINER_MT_object,
    OUTLINER_PT_filter,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
