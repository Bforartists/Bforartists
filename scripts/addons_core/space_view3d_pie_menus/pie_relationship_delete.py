# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from typing import Any

import bpy
from bpy.types import Object, Collection, Operator, Menu, ID
from bpy.props import StringProperty, CollectionProperty
from bpy_extras import id_map_utils

from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class OUTLINER_MT_relationship_pie(Menu):
    bl_label = 'Object Relationships'
    bl_idname = 'OUTLINER_MT_relationship_pie'

    @classmethod
    def poll(cls, context):
        if context.area.type == 'VIEW_3D':
            return True
        if context.area.type == 'OUTLINER':
            return bool(outliner_get_active_id(context))
        return False

    def draw(self, context):
        layout = self.layout

        active_id = get_active_id(context)

        pie = layout.menu_pie()
        # 4 - LEFT
        if context.area.type == 'VIEW_3D':
            pie.operator(
                OBJECT_OT_unlink_from_scene.bl_idname,
                icon='TRASH',
                text="Unlink From Scene",
            )
        else:
            pie.operator(
                'outliner.id_operation', icon='TRASH', text='Unlink From Scene'
            ).type = 'UNLINK'
        # 6 - RIGHT
        if context.area.type == 'VIEW_3D':
            op = pie.operator('object.delete', icon='X', text="Delete From File")
            op.use_global = True
            op.confirm = False
        elif any([type(id) in (bpy.types.Object, bpy.types.Collection) for id in context.selected_ids]):
            # NOTE: Objects and other types of IDs cannot be deleted with the same operator, strangely enough.
            # If we wanted to support that, we could implement a wrapper operator, but it's a very rare case, so this feels fine.
            pie.operator('outliner.delete', icon='X', text='Delete From File')
        else:
            pie.operator('outliner.id_operation', icon='X', text="Delete IDs From File").type='DELETE'
        # 2 - BOTTOM
        pie.operator('outliner.pie_purge_orphans', icon='ORPHAN_DATA')
        # 8 - TOP
        id = get_active_id(context)
        if id:
            remap = pie.operator(
                'outliner.remap_users_ui', icon='FILE_REFRESH', text="Remap Users"
            )
            remap.id_type = id.id_type
            remap.id_name_source = id.name
            if id.library:
                remap.library_path_source = id.library.filepath
        else:
            pie.separator()
        # 7 - TOP - LEFT
        pie.operator(OUTLINER_OT_list_users_of_datablock.bl_idname, icon='LOOP_BACK')
        # 9 - TOP - RIGHT
        pie.operator(
            OUTLINER_OT_list_dependencies_of_datablock.bl_idname, icon='LOOP_FORWARDS'
        )
        # 1 - BOTTOM - LEFT
        if context.area.type == 'OUTLINER' and active_id:
            pie.operator(
                'outliner.id_operation',
                text="Unlink From Collection",
                icon="OUTLINER_COLLECTION",
            ).type = 'UNLINK'
        else:
            pie.separator()
        # 3 - BOTTOM - RIGHT
        if context.area.type == 'OUTLINER' and active_id:
            pie.operator(
                'outliner.delete', text="Delete Hierarchy", icon="OUTLINER"
            ).hierarchy = True
        else:
            pie.operator(
                OBJECT_OT_instancer_empty_to_collection.bl_idname, icon='LINKED'
            )


class OUTLINER_OT_pie_purge_orphans(Operator):
    """Clear all orphaned data-blocks without any users from the file"""

    bl_idname = "outliner.pie_purge_orphans"
    bl_label = "Purge Unused Data"

    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Call Blender's purge function, but in a way that works from any editor, not only the 3D View."""

        orig_ui = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                break
        else:
            orig_ui = context.area.ui_type
            context.area.ui_type = 'VIEW_3D'
            area = context.area

        with context.temp_override(area=area):
            ret = bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=True
            )

        if orig_ui:
            context.area.ui_type = orig_ui

        return ret


class OBJECT_OT_unlink_from_scene(Operator):
    """Unlink selected objects or collections from the current scene"""

    bl_idname = "object.unlink_from_scene"
    bl_label = "Unlink Selected From Scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.area.type == 'OUTLINER':
            any_selected = bool(
                get_objects_to_unlink(context) or get_collections_to_unlink(context)
            )
        elif context.area.type == 'VIEW_3D':
            any_selected = bool(get_objects_to_unlink(context))
        else:
            any_selected = False

        if not any_selected:
            cls.poll_message_set("Nothing is selected.")
        return any_selected

    def execute(self, context):
        unlink_collections_from_scene(get_collections_to_unlink(context), context.scene)
        unlink_objects_from_scene(get_objects_to_unlink(context), context.scene)

        return {'FINISHED'}


class RelationshipOperatorMixin:
    datablock_name: StringProperty()
    datablock_storage: StringProperty()
    library_filepath: StringProperty()

    def get_datablock(self, context) -> ID | None:
        if self.datablock_name and self.datablock_storage:
            storage = getattr(bpy.data, self.datablock_storage)
            lib_path = self.library_filepath or None
            return storage.get((self.datablock_name, lib_path))
        elif context.area.type == 'OUTLINER':
            return outliner_get_active_id(context)
        else:
            return context.active_object

    @classmethod
    def poll(cls, context):
        id = get_active_id(context)
        if context.area.type == 'OUTLINER':
            if id == None:
                cls.poll_message_set("No active ID.")
                return False
            return True
        elif context.area.type == '3D_VIEW':
            if id == None:
                cls.poll_message_set("No active object.")
                return False

        return True

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self, width=600)

    def get_datablocks_to_display(self, id: ID) -> list[ID]:
        raise NotImplementedError

    def get_label(self):
        return "Listing datablocks that reference this:"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        datablock = self.get_datablock(context)
        if not datablock:
            layout.alert = True
            layout.label(
                text=f"Failed to find datablock: {self.datablock_storage}, {self.datablock_name}, {self.library_filepath}"
            )
            return

        row = layout.row()
        split = row.split()
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text=self.get_label())
        id_row = split.row(align=True)
        name_row = id_row.row()
        name_row.enabled = False
        name_row.prop(datablock, 'name', icon=get_datablock_icon(datablock), text="")
        fake_user_row = id_row.row()
        fake_user_row.prop(datablock, 'use_fake_user', text="")

        layout.separator()

        datablocks = self.get_datablocks_to_display(datablock)
        if not datablocks:
            layout.label(text="There are none.")
            return

        for user in self.get_datablocks_to_display(datablock):
            if user == datablock:
                # Scenes are users of themself for technical reasons,
                # I think it's confusing to display that.
                continue
            row = layout.row()
            name_row = row.row()
            name_row.enabled = False
            name_row.prop(user, 'name', icon=get_datablock_icon(user), text="")
            op_row = row.row()
            op = op_row.operator(type(self).bl_idname, text="", icon='LOOP_FORWARDS')
            op.datablock_name = user.name
            storage = get_id_storage_by_type_str(user.id_type)[1]
            if not storage:
                print("Error: Can't find storage: ", user.name, user.id_type)
            op.datablock_storage = storage
            if user.library:
                op.library_filepath = user.library.filepath
                name_row.prop(
                    user.library,
                    'filepath',
                    icon=get_library_icon(user.library.filepath),
                    text="",
                )

    def execute(self, context):
        return {'FINISHED'}


class OUTLINER_OT_list_users_of_datablock(RelationshipOperatorMixin, Operator):
    """Show list of users of this datablock"""

    bl_idname = "object.list_datablock_users"
    bl_label = "List Datablock Users"

    datablock_name: StringProperty()
    datablock_storage: StringProperty()
    library_filepath: StringProperty()

    def get_datablocks_to_display(self, datablock: ID) -> list[ID]:
        user_map = bpy.data.user_map()
        users = user_map[datablock]
        return sorted(users, key=lambda u: (str(type(u)), u.name))


class OUTLINER_OT_list_dependencies_of_datablock(RelationshipOperatorMixin, Operator):
    """Show list of dependencies of this datablock"""

    bl_idname = "object.list_datablock_dependencies"
    bl_label = "List Datablock Dependencies"

    def get_label(self):
        return "Listing datablocks that are referenced by this:"

    def get_datablocks_to_display(self, datablock: ID) -> list[ID]:
        dependencies = id_map_utils.get_id_reference_map().get(datablock)
        if not dependencies:
            return []
        return sorted(dependencies, key=lambda u: (str(type(u)), u.name))


class RemapTarget(bpy.types.PropertyGroup):
    pass


class OUTLINER_OT_remap_users_ui(bpy.types.Operator):
    """Remap users of a selected ID to any other ID of the same type"""

    bl_idname = "outliner.remap_users_ui"
    bl_label = "Remap Users"
    bl_options = {'INTERNAL', 'UNDO'}

    def update_library_path(self, context):
        # Prepare the ID selector.
        remap_targets = context.scene.remap_targets
        remap_targets.clear()
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        for id in get_id_storage_by_type_str(self.id_type)[0]:
            if id == source_id:
                continue
            if (self.library_path == 'Local Data' and not id.library) or (
                id.library and (self.library_path == id.library.filepath)
            ):
                id_entry = remap_targets.add()
                id_entry.name = id.name

    library_path: StringProperty(
        name="Library",
        description="Library path, if we want to remap to a linked ID",
        update=update_library_path,
    )
    id_type: StringProperty(description="ID type, eg. 'OBJECT' or 'MESH'")
    library_path_source: StringProperty()
    id_name_source: StringProperty(
        name="Source ID Name", description="Name of the ID we're remapping the users of"
    )
    id_name_target: StringProperty(
        name="Target ID Name", description="Name of the ID we're remapping users to"
    )

    def invoke(self, context, _event):
        # Populate the remap_targets string list with possible options based on
        # what was passed to the operator.

        assert (
            self.id_type and self.id_name_source
        ), "Error: UI must provide ID and ID type to this operator."

        # Prepare the library selector.
        remap_target_libraries = context.scene.remap_target_libraries
        remap_target_libraries.clear()
        local = remap_target_libraries.add()
        local.name = "Local Data"
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        for lib in bpy.data.libraries:
            for id in lib.users_id:
                if type(id) == type(source_id):
                    lib_entry = remap_target_libraries.add()
                    lib_entry.name = lib.filepath
                    break

        self.library_path = "Local Data"
        if source_id.name[-4] == ".":
            storage = get_id_storage_by_type_str(self.id_type)[0]
            suggestion = storage.get(source_id.name[:-4])
            if suggestion:
                self.id_name_target = suggestion.name
                if suggestion.library:
                    self.library_path = suggestion.library.filepath

        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        row = layout.row()
        id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        id_icon = get_datablock_icon(id)
        split = row.split()
        split.row().label(text="Anything that was referencing this:")
        row = split.row()
        row.prop(self, 'id_name_source', text="", icon=id_icon)
        row.enabled = False

        layout.separator()
        col = layout.column()
        col.label(text="Will now reference this instead: ")
        if len(scene.remap_target_libraries) > 1:
            col.prop_search(
                self,
                'library_path',
                scene,
                'remap_target_libraries',
                icon=get_library_icon(self.library_path),
            )
        col.prop_search(
            self,
            'id_name_target',
            scene,
            'remap_targets',
            text="Datablock",
            icon=id_icon,
        )

    def execute(self, context):
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        target_id = get_id(self.id_name_target, self.id_type, self.library_path)
        assert source_id and target_id, "Error: Failed to find source or target."

        source_id.user_remap(target_id)
        return {'FINISHED'}


class OBJECT_OT_instancer_empty_to_collection(Operator):
    """Replace the Empty that instances a collection, with the collection itself"""

    bl_idname = "object.instancer_empty_to_collection"
    bl_label = "Instancer Empty To Collection"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if context.area.ui_type == 'OUTLINER':
            obj = outliner_get_active_id(context)

        if not (
            obj
            and obj.type == 'EMPTY'
            and obj.instance_type == 'COLLECTION'
            and obj.instance_collection
        ):
            cls.poll_message_set("Active object is not an instancer empty.")
            return False
        if obj.instance_collection in set(context.scene.collection.children):
            cls.poll_message_set(
                f'Collection "{obj.instance_collection.name}" is already in the scene.'
            )
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        if context.area.ui_type == 'OUTLINER':
            obj = outliner_get_active_id(context)

        coll = obj.instance_collection
        bpy.data.objects.remove(obj)
        context.scene.collection.children.link(coll)

        self.report({'INFO'}, f'Added "{coll.name}" directly to the scene.')

        return {'FINISHED'}


def get_objects_to_unlink(context) -> list[Object]:
    if context.area.type == 'OUTLINER':
        selected_objs = [id for id in context.selected_ids if type(id) == Object]
    elif context.area.type == 'VIEW_3D':
        selected_objs = context.selected_objects

    scene_objs = set(context.scene.objects)
    return [ob for ob in selected_objs if ob in scene_objs]


def unlink_objects_from_scene(objects, scene):
    for obj in objects:
        for coll in [scene.collection] + scene.collection.children_recursive:
            if obj.name in coll.objects:
                coll.objects.unlink(obj)


def get_collections_to_unlink(context) -> list[Collection]:
    if context.area.type == 'OUTLINER':
        return [id for id in context.selected_ids if type(id) == Collection]
    return []


def unlink_collections_from_scene(collections_to_unlink, scene):
    for coll_to_unlink in collections_to_unlink:
        for coll in scene.collection.children_recursive:
            if coll_to_unlink.name in coll.children:
                coll.children.unlink(coll_to_unlink)


def get_active_id(context) -> ID | None:
    if context.area.ui_type == 'OUTLINER':
        return outliner_get_active_id(context)
    else:
        return context.active_object


def outliner_get_active_id(context):
    """Helper function for Blender 3.6 and 4.0 cross-compatibility."""
    if not context.area.type == 'OUTLINER':
        return

    if hasattr(context, 'id'):
        # Blender 4.0: Active ID is explicitly exposed to PyAPI, yay.
        return context.id
    elif len(context.selected_ids) > 0:
        # Blender 3.6 and below: We can only hope first selected ID happens to be the active one.
        return context.selected_ids[0]


# List of datablock type information tuples:
# (type_class, type_enum_string, bpy.data.<collprop_name>)
def get_id_info() -> list[tuple[type, str, str]]:
    bpy_prop_collection = type(bpy.data.objects)
    id_info = []
    for prop_name in dir(bpy.data):
        prop = getattr(bpy.data, prop_name)
        if type(prop) == bpy_prop_collection:
            if len(prop) == 0:
                # We can't get full info about the ID type if there isn't at least one entry of it.
                # But we shouldn't need it, since we don't have any entries of it!
                continue
            typ = type(prop[0])
            if issubclass(typ, bpy.types.NodeTree):
                typ = bpy.types.NodeTree
            id_info.append((typ, prop[0].id_type, prop_name))
    return id_info


def get_id_storage_by_type_str(typ_name: str):
    for typ, typ_str, container_str in get_id_info():
        if typ_str == typ_name:
            return getattr(bpy.data, container_str), container_str


def get_datablock_types_enum_items() -> list[tuple[str, str, str, str, int]]:
    """Return the items needed to define an EnumProperty representing a datablock type selector."""
    enum_items = bpy.types.DriverTarget.bl_rna.properties['id_type'].enum_items
    ret = []
    for i, typ in enumerate(enum_items):
        ret.append((typ.identifier, typ.name, typ.name, typ.icon, i))
    ret.append(('SCREEN', 'Screen', 'Screen', 'RESTRICT_VIEW_OFF', len(ret)))
    ret.append(('METABALL', 'Metaball', 'Metaball', 'OUTLINER_OB_META', len(ret)))
    ret.append(('CACHE_FILE', 'Cache File', 'Cache File', 'MOD_MESHDEFORM', len(ret)))
    ret.append(
        (
            'POINT_CLOUD',
            'Point Cloud',
            'Point Cloud',
            'OUTLINER_OB_POINTCLOUD',
            len(ret),
        )
    )
    ret.append(
        ('HAIR_CURVES', 'Hair Curves', 'Hair Curves', 'OUTLINER_OB_CURVES', len(ret))
    )
    ret.append(('PAINT_CURVE', 'Paint Curve', 'Paint Curve', 'FORCE_CURVE', len(ret)))
    ret.append(('MOVIE_CLIP', 'Movie Clip', 'Movie Clip', 'FILE_MOVIE', len(ret)))
    return ret


# List of 5-tuples that can be used to define the items of an EnumProperty.
ID_TYPE_ENUM_ITEMS: list[tuple[str, str, str, str, int]] = (
    get_datablock_types_enum_items()
)

# Map datablock type enum strings to their name and icon strings.
ID_TYPE_INFO: dict[str, tuple[str, str]] = {
    tup[0]: (tup[1], tup[3]) for tup in ID_TYPE_ENUM_ITEMS
}


def get_datablock_icon(id) -> str:
    id_type = get_fundamental_id_type(id)[1]
    return ID_TYPE_INFO[id_type][1]


def get_fundamental_id_type(datablock: ID) -> tuple[Any, str]:
    """Certain datablocks have very specific types.
    This function should return their fundamental type, ie. parent class."""
    id_info = get_id_info()
    for typ, typ_str, _container_str in id_info:
        if isinstance(datablock, typ):
            return typ, typ_str

    raise Exception(
        f"Failed to get fundamental ID type of ID: {datablock.name}, {type(datablock)}"
    )


def get_id(id_name: str, id_type: str, lib_path="") -> ID:
    container = get_id_storage_by_type_str(id_type)[0]
    if lib_path and lib_path != 'Local Data':
        return container.get((id_name, lib_path))
    return container.get((id_name, None))


def get_library_icon(lib_path: str) -> str:
    """Return the library or the broken library icon, as appropriate."""
    if lib_path == 'Local Data':
        return 'FILE_BLEND'
    filepath = os.path.abspath(bpy.path.abspath(lib_path))
    if not os.path.exists(filepath):
        return 'LIBRARY_DATA_BROKEN'

    return 'LIBRARY_DATA_DIRECT'


registry = [
    OUTLINER_MT_relationship_pie,
    OUTLINER_OT_pie_purge_orphans,
    OBJECT_OT_unlink_from_scene,
    OUTLINER_OT_list_users_of_datablock,
    OUTLINER_OT_list_dependencies_of_datablock,
    RemapTarget,
    OUTLINER_OT_remap_users_ui,
    OBJECT_OT_instancer_empty_to_collection,
]


def register():
    bpy.types.Scene.remap_targets = CollectionProperty(type=RemapTarget)
    bpy.types.Scene.remap_target_libraries = CollectionProperty(type=RemapTarget)

    for keymap_name in ("Object Mode", "Outliner"):
        WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
            keymap_name=keymap_name,
            pie_name=OUTLINER_MT_relationship_pie.bl_idname,
            hotkey_kwargs={'type': "X", 'value': "PRESS"},
            on_drag=False,
        )


def unregister():
    try:
        del bpy.types.Scene.remap_targets
        del bpy.types.Scene.remap_target_libraries
    except AttributeError:
        # Blender Log also implements these same things, which can result in errors.
        pass
