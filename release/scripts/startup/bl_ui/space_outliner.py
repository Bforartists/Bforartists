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

        #layout.separator_spacer()

        row = layout.row(align=True)

        row.prop(addon_prefs,"outliner_show_search", icon='VIEWZOOM', text = "") # show search text prop
        if addon_prefs.outliner_show_search:
            row.prop(space, "filter_text", text="")

        layout.separator_spacer()

        row = layout.row(align=True)
        if display_mode in {'VIEW_LAYER'}:
            row.popover(
                panel="OUTLINER_PT_filter",
                text="",
                icon='FILTER',
            )
        elif display_mode in {'LIBRARIES', 'ORPHAN_DATA'}:
            row.prop(space, "use_filter_id_type", text="", icon='FILTER')
            sub = row.row(align=True)
            sub.active = space.use_filter_id_type
            sub.prop(space, "filter_id_type", text="", icon_only=True)

        if display_mode == 'VIEW_LAYER':
            layout.operator("outliner.collection_new", text="", icon='GROUP')

        elif display_mode == 'ORPHAN_DATA':
            layout.operator("outliner.orphans_purge", text="Purge")

        elif space.display_mode == 'DATA_API':
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

        layout.menu("OUTLINER_MT_view") # bfa - view menu

        if space.display_mode == 'DATA_API':
            layout.menu("OUTLINER_MT_edit_datablocks")
            

# Workaround to separate the tooltips for Hide one level
class OUTLINER_MT_view_hide_one_level(bpy.types.Operator):
    """Hide one level\nCollapse all entries by one level """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "outliner.hide_one_level"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide one level"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.outliner.show_one_level(open = False)
        return {'FINISHED'}


# Workaround to separate the tooltips
class OUTLINER_MT_view_select_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "outliner.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.outliner.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class OUTLINER_MT_view_select_none(bpy.types.Operator):
    """None\nDeselects everything """      # blender will use this as a tooltip for menu items and buttons.
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


class OUTLINER_MT_collection_view_layer(Menu):
    bl_label = "View Layer"

    def draw(self, context):
        layout = self.layout

        layout.operator("outliner.collection_exclude_set", icon='RENDERLAYERS')
        layout.operator("outliner.collection_exclude_clear", icon='CLEAR')

        if context.engine == 'CYCLES':
            layout.operator("outliner.collection_indirect_only_set", icon='RENDERLAYERS')
            layout.operator("outliner.collection_indirect_only_clear", icon='CLEAR')

            layout.operator("outliner.collection_holdout_set", icon='RENDERLAYERS')
            layout.operator("outliner.collection_holdout_clear", icon='CLEAR')


class OUTLINER_MT_collection_visibility(Menu):
    bl_label = "Visibility"

    def draw(self, _context):
        layout = self.layout

        layout.operator("outliner.collection_isolate", text="Isolate")

        layout.separator()

        layout.operator("outliner.collection_show", text="Show", icon="HIDE_OFF")
        layout.operator("outliner.collection_show_inside", text="Show All Inside", icon="HIDE_OFF")
        layout.operator("outliner.collection_hide", text="Hide", icon="HIDE_ON")
        layout.operator("outliner.collection_hide_inside", text="Hide All Inside", icon="HIDE_ON")

        layout.separator()

        layout.operator("outliner.collection_enable", text="Enable in Viewports", icon="RESTRICT_VIEW_OFF")
        layout.operator("outliner.collection_disable", text="Disable in Viewports", icon="HIDE_ON")

        layout.separator()

        layout.operator("outliner.collection_enable_render", text="Enable in Render", icon="RESTRICT_RENDER_OFF")
        layout.operator("outliner.collection_disable_render", text="Disable in Render", icon="RESTRICT_RENDER_ON")


class OUTLINER_MT_collection(Menu):
    bl_label = "Collection"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.operator("outliner.collection_new", text="New", icon='GROUP')
        layout.operator("outliner.collection_new", text="New Nested", icon='GROUP').nested = True
        layout.operator("outliner.collection_duplicate", text="Duplicate Collection", icon = "DUPLICATE")
        layout.operator("outliner.collection_duplicate_linked", text="Duplicate Linked", icon = "DUPLICATE")
        layout.operator("outliner.id_copy", text="Copy", icon='COPYDOWN')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("outliner.collection_delete", text="Delete", icon="DELETE").hierarchy = False
        layout.operator("outliner.collection_delete", text="Delete Hierarchy", icon="DELETE").hierarchy = True

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

        if space.display_mode == 'VIEW_LAYER':
            layout.separator()
            layout.menu("OUTLINER_MT_collection_view_layer")

        layout.separator()

        layout.operator_menu_enum("outliner.id_operation", "type", text="ID Data")


class OUTLINER_MT_collection_new(Menu):
    bl_label = "Collection"

    def draw(self, context):
        layout = self.layout

        layout.operator("outliner.collection_new", text="New", icon='GROUP')
        layout.operator("outliner.collection_new", text="New Nested", icon='GROUP').nested = True
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')


class OUTLINER_MT_object(Menu):
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout

        space = context.space_data
        obj = context.active_object
        object_mode = 'OBJECT' if obj is None else obj.mode

        layout.operator("outliner.id_copy", text="Copy", icon='COPYDOWN')
        layout.operator("outliner.id_paste", text="Paste", icon='PASTEDOWN')

        layout.separator()

        layout.operator("outliner.object_operation", text="Delete", icon="DELETE").type = 'DELETE'

        if space.display_mode == 'VIEW_LAYER' and not space.use_filter_collection:
            layout.operator("outliner.object_operation", text="Delete Hierarchy", icon="DELETE").type = 'DELETE_HIERARCHY'

        layout.separator()

        layout.operator("outliner.object_operation", text="Select", icon="RESTRICT_SELECT_OFF").type = 'SELECT'
        layout.operator("outliner.object_operation", text="Select Hierarchy", icon="RESTRICT_SELECT_OFF").type = 'SELECT_HIERARCHY'
        layout.operator("outliner.object_operation", text="Deselect", icon = "SELECT_NONE").type = 'DESELECT'

        layout.separator()

        if object_mode in {'EDIT', 'POSE'}:
            name = bpy.types.Object.bl_rna.properties["mode"].enum_items[object_mode].name
            layout.operator("outliner.object_operation", text=f"{name:s} Set").type = 'OBJECT_MODE_ENTER'
            layout.operator("outliner.object_operation", text=f"{name:s} Clear").type = 'OBJECT_MODE_EXIT'
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

        layout.prop(space, "use_filter_complete", text="Exact Match Search")
        layout.prop(space, "use_filter_case_sensitive", text="Case Sensitive Search")

        layout.separator()

        if display_mode != 'DATA_API':
            layout.prop(space, "use_sort_alpha")
            layout.prop(space, "show_restrict_columns")
            layout.separator()

        col = layout.column(align=True)

        col.prop(space, "use_filter_collection", text="Collections", icon='GROUP')
        col.prop(space, "use_filter_object", text="Objects", icon='OBJECT_DATAMODE')

        sub = col.column(align=True)
        sub.active = space.use_filter_object

        if bpy.data.meshes:
            sub.prop(space, "use_filter_object_mesh", text="Meshes", icon='MESH_DATA')
        if bpy.data.armatures:
            sub.prop(space, "use_filter_object_armature", text="Armatures", icon='ARMATURE_DATA')
        if bpy.data.lights:
            sub.prop(space, "use_filter_object_light", text="Lights", icon='LIGHT_DATA')
        if bpy.data.cameras:
            sub.prop(space, "use_filter_object_camera", text="Cameras", icon='CAMERA_DATA')

        sub.prop(space, "use_filter_object_empty", text="Empties", icon='EMPTY_DATA')

        if (
                bpy.data.curves or
                bpy.data.metaballs or
                bpy.data.lightprobes or
                bpy.data.lattices or
                bpy.data.fonts or
                bpy.data.speakers
        ):
            sub.prop(space, "use_filter_object_others", text="Others")

        subsub = sub.column(align=False)
        subsub.prop(space, "filter_state", text="")
        subsub.prop(space, "use_filter_object_content", text="Object Contents")
        subsub.prop(space, "use_filter_children", text="Object Children")


classes = (
    OUTLINER_OT_switch_editors_to_properties,
    OUTLINER_OT_switch_editors_to_outliner,
    OUTLINER_HT_header,
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
    OUTLINER_MT_collection_view_layer,
    OUTLINER_MT_object,
    OUTLINER_PT_filter,

)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
