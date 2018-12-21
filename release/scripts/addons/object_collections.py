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

import bpy
from bpy.types import (
        Operator,
        Panel,
        Menu,
        )


from bpy.props import (
        EnumProperty,
        IntProperty,
        )


bl_info = {
    "name": "Collections",
    "author": "Dalai Felinto",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "description": "Panel to set/unset object collections",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}


# #####################################################################################
# Operators
# #####################################################################################

class OBJECT_OT_collection_add(Operator):
    """Add an object to a new collection"""
    bl_idname = "object.collection_add"
    bl_label = "Add to New Collection"

    def execute(self, context):
        scene = context.scene
        collection = scene.master_collection.collections.new()
        collection.objects.link(context.object)
        return {'FINISHED'}


class OBJECT_OT_collection_remove(Operator):
    """Remove the active object from this collection"""
    bl_idname = "object.collection_remove"
    bl_label = "Remove from Collection"

    def execute(self, context):
        collection = context.scene_collection
        collection.objects.unlink(context.object)
        return {'FINISHED'}


def get_collection_from_id_recursive(collection, collection_id, current_id):
    """Return len of collection and the collection if it was a match"""
    if collection_id == current_id:
        return collection, 0

    current_id += 1

    for collection_nested in collection.collections:
        matched_collection, current_id = get_collection_from_id_recursive(
                                                 collection_nested,
                                                 collection_id,
                                                 current_id)
        if matched_collection is not None:
            return matched_collection, 0

    return None, current_id


def get_collection_from_id(scene, collection_id):
    master_collection = scene.master_collection
    return get_collection_from_id_recursive(master_collection, collection_id, 0)[0]


def collection_items_recursive(path, collection, items, current_id, object_name):
    name = collection.name
    current_id += 1

    if object_name not in collection.objects:
        items.append((str(current_id), path + name, ""))
        path += name + " / "

    for collection_nested in collection.collections:
        current_id = collection_items_recursive(path, collection_nested, items, current_id, object_name)
    return current_id


def collection_items(self, context):
    items = []

    master_collection = context.scene.master_collection
    object_name = context.object.name

    if object_name not in master_collection.objects:
        items.append(('0', "Master Collection", "", 'COLLAPSEMENU', 0))

    current_id = 0
    for collection in master_collection.collections:
        current_id = collection_items_recursive("", collection, items, current_id, object_name)

    return items


class OBJECT_OT_collection_link(Operator):
    """Add an object to an existing collection"""
    bl_idname = "object.collection_link"
    bl_label = "Link to Collection"

    collection_index: IntProperty(
            name="Collection Index",
            default=-1,
            options={'SKIP_SAVE'},
            )

    type: EnumProperty(
            name="",
            description="Dynamic enum for collections",
            items=collection_items,
            )

    def execute(self, context):
        if self.collection_index == -1:
            self.collection_index = int(self.type)

        collection = get_collection_from_id(context.scene, self.collection_index)

        if collection is None:
            # It should never ever happen!
            self.report({'ERROR'}, "Unexpected error: collection {0} is invalid".format(
                    self.collection_index))
            return {'CANCELLED'}

        collection.objects.link(context.object)
        return {'FINISHED'}

    def invoke(self, context, events):
        if self.collection_index != -1:
            return self.execute(context)

        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def find_collection_parent(collection, collection_parent):
    for collection_nested in collection_parent.collections:
        if collection_nested == collection:
            return collection_parent

        found_collection = find_collection_parent(collection, collection_nested)
        if found_collection:
            return found_collection
    return None


class OBJECT_OT_collection_unlink(Operator):
    """Unlink the collection from all objects"""
    bl_idname = "object.collection_unlink"
    bl_label = "Unlink Collection"

    def execute(self, context):
        collection = context.scene_collection
        master_collection = context.scene.master_collection

        collection_parent = find_collection_parent(collection, master_collection)
        if collection_parent is None:
            self.report({'ERROR'}, "Cannot find {0}'s parent".format(collection.name))
            return {'CANCELLED'}

        collection_parent.collections.remove(collection)
        return {'CANCELLED'}


def select_collection_objects(collection):
    for ob in collection.objects:
        ob.select_set(True)

    for collection_nested in collection.collections:
        select_collection_objects(collection_nested)


class OBJECT_OT_collection_select(Operator):
    """Select all objects in collection"""
    bl_idname = "object.collection_select"
    bl_label = "Select Collection"

    def execute(self, context):
        collection = context.scene_collection
        select_collection_objects(collection)
        return {'FINISHED'}


# #####################################################################################
# Interface
# #####################################################################################

class COLLECTION_MT_specials(Menu):
    bl_label = "Collection Specials"

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.active = context.scene_collection != context.scene.master_collection
        col.operator("object.collection_unlink", icon='X', text="Unlink Collection")

        layout.operator("object.collection_select", text="Select Collection")


def all_collections_get(context):
    """Iterator over all scene collections
    """
    def all_collections_recursive_get(collection_parent, collections):
        collections.append(collection_parent)
        for collection_nested in collection_parent.collections:
            all_collections_recursive_get(collection_nested, collections)

    scene = context.scene
    master_collection = scene.master_collection

    collections = []

    all_collections_recursive_get(master_collection, collections)

    return collections


class OBJECT_PT_collections(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label = "Collections"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        obj = context.object
        master_collection = bpy.context.scene.master_collection

        if master_collection.collections:
            row.operator("object.collection_link", text="Add to Collection")
        else:
            row.operator("object.collection_link", text="Add to Collection").collection_index = 0
        row.operator("object.collection_add", text="", icon='ADD')

        obj_name = obj.name
        for collection in all_collections_get(context):
            collection_objects = collection.objects
            if obj_name in collection.objects:
                col = layout.column(align=True)
                col.context_pointer_set("scene_collection", collection)

                row = col.box().row()
                if collection == master_collection:
                    row.label(text=collection.name)
                else:
                    row.prop(collection, "name", text="")
                row.operator("object.collection_remove", text="", icon='X', emboss=False)
                row.menu("COLLECTION_MT_specials", icon='DOWNARROW_HLT', text="")


# #####################################################################################
# Register/Unregister
# #####################################################################################

classes = (
    COLLECTION_MT_specials,
    OBJECT_PT_collections,
    OBJECT_OT_collection_add,
    OBJECT_OT_collection_remove,
    OBJECT_OT_collection_link,
    OBJECT_OT_collection_unlink,
    OBJECT_OT_collection_select,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
