# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

from typing import Union

import bpy


# Name of the collection holding the shared collections
shared_collections_ROOT_NAME = ".shared_collections"


def get_shared_collections_root_collection() -> Union[bpy.types.Collection, None]:
    """Get the root collection holding all the collection used as shared collections."""
    return bpy.data.collections.get(shared_collections_ROOT_NAME, None)


def get_or_create_shared_collections_root_collection() -> bpy.types.Collection:
    """Get or create the root collection that holds shared collections.

    :return: The shared_collections root collection.
    """
    if not (root_collection := get_shared_collections_root_collection()):
        root_collection = bpy.data.collections.new(name=shared_collections_ROOT_NAME)
        # Use fake user to avoid this datablock to be removed even if unused
        root_collection.use_fake_user = True
    return root_collection


def get_shared_folder_by_name(name: str) -> bpy.types.Collection:
    """Get a shared collection by `name`.

    :return: The shared collection if found.
    """
    if not (root_collection := get_shared_collections_root_collection()):
        raise RuntimeError("No shared collections in this file")

    if not (col := root_collection.children.get(name, None)):
        raise ValueError(f"No shared collections named '{name}'")

    return col


def make_shared_folder_from_collection(collection: bpy.types.Collection):
    """Turn `collection` into a shared collection.

    :param collection: The collection.
    """
    # Discard scenes master collections
    if collection not in bpy.data.collections.values():
        raise ValueError("Scene collections cannot be used as shared collection")

    root = get_or_create_shared_collections_root_collection()

    if collection in root.children.values():
        raise ValueError(f"Collection '{collection.name}' is already a shared collection")

    root.children.link(collection)


def create_shared_folder(name: str) -> bpy.types.Collection:
    """Create and return a shared collection named `name`.

    :param name: The name of the shared collection.
    """
    if name in bpy.data.collections:
        raise ValueError(f"Collection '{name}' already exists")
    col = bpy.data.collections.new(name)
    make_shared_folder_from_collection(col)
    return col


def is_shared_folder(collection: bpy.types.Collection) -> bool:
    """Return whether `collection` is a shared collection.

    :param collection: The collection.
    :return: Whether the collection is a shared collection.
    """
    if not (root_collection := get_shared_collections_root_collection()):
        return False
    return collection.name in root_collection.children


def ensure_shared_folder(collection: bpy.types.Collection):
    """Raises ValueError if collection is not a shared collection.

    :param collection: The collection.
    """
    if not is_shared_folder(collection):
        raise ValueError(f"The collection {collection.name} is not a shared collection")


def delete_shared_folder(collection: bpy.types.Collection):
    """Delete the shared collection `collection`.

    :param collection: The shared collection to delete.
    """
    ensure_shared_folder(collection)
    bpy.data.collections.remove(collection)


def link_shared_folder(collection: bpy.types.Collection, scenes: list[bpy.types.Scene]):
    """
    Link the shared collection `collection` in each scene's collection in `scenes`.
    Does nothing for scenes in which `collection` is already linked.

    :param collection: The shared collection.
    :param scenes: The scenes to link the shared collection in.
    :return: The list of scenes in which the folder was acually linked.
    """
    ensure_shared_folder(collection)
    linked_scenes = []
    for scene in scenes:
        if collection.name not in scene.collection.children:
            scene.collection.children.link(collection)
            linked_scenes.append(scene)
    return linked_scenes


def unlink_shared_folder(
    collection: bpy.types.Collection, scenes: list[bpy.types.Scene]
) -> list[bpy.types.Scene]:
    """
    Unlink the shared collection `collection` from each scene in `scenes`.
    Does nothing for scenes in which `collection` is not linked.

    :param collection: The shared collection.
    :param scenes: The scenes to unlink the shared collection from.
    :return: The list of scenes from which the folder was acually unlinked.
    """
    ensure_shared_folder(collection)
    unlinked_scenes = []
    for scene in scenes:
        if collection.name in scene.collection.children:
            scene.collection.children.unlink(collection)
            unlinked_scenes.append(scene)
    return unlinked_scenes


def create_and_link_shared_folder(
    name: str, scenes: list[bpy.types.Scene]
) -> tuple[bpy.types.Collection, list[bpy.types.Scene]]:
    """Create new shared collection named `name` and link it in `scenes`.

    :param name: The shared collection name.
    :param scenes: The scenes to link the shared collection in.
    :return: The created shared collection collection and the list of scenes in which it was linked.
    """
    collection = create_shared_folder(name)
    linked_scenes = link_shared_folder(collection, scenes)
    return collection, linked_scenes


def get_scene_users(collection: bpy.types.Collection) -> list[bpy.types.Scene]:
    """Get all scene that uses `collection`.

    :param collection: The shared collection.
    """
    return [
        user
        for user in bpy.data.user_map(subset=[collection])[collection]
        if isinstance(user, bpy.types.Scene)
    ]


def get_scene_sequence_users(
    collection: bpy.types.Collection, sed: bpy.types.SequenceEditor
) -> list[bpy.types.Strip]:
    """Get all scene sequence strips with scenes that uses `collection`.

    :param collection: The shared collection.
    :param sed: The sequence editor containing the scene sequences.
    """
    scene_users = get_scene_users(collection)
    return [
        s
        for s in sed.sequences
        if isinstance(s, bpy.types.Strip) and s.scene in scene_users
    ]


def get_active_shared_folder(
    context: bpy.types.Context,
) -> Union[bpy.types.Collection, None]:
    """
    Get the shared collection for current `WindowManager.active_shared_folder_index` value.

    :return: The shared collection collection or None if not applicable.
    """
    if not (root := get_shared_collections_root_collection()):
        return None
    idx = context.window_manager.active_shared_folder_index
    if idx < 0 or idx >= len(root.children):
        return None
    return root.children[idx]


def set_active_shared_folder(
    context: bpy.types.Context, collection: bpy.types.Collection
):
    """Make `collection` the active shared collection."""
    context.window_manager.active_shared_folder_index = (
        get_shared_collections_root_collection().children.find(collection.name)
    )


def find_layer_collection(
    view_layer: bpy.types.ViewLayer, collection: bpy.types.Collection
) -> Union[bpy.types.LayerCollection, None]:
    """Find the first LayerCollection wrapping `collection` in `view_layer`.

    :param view_layer: The view layer to consider
    :param collection: The collection to look for
    :return: The layer collection if found, None otherwise
    """
    return next(
        (
            lc
            for lc in view_layer.layer_collection.children
            if lc.collection == collection
        ),
        None,
    )


def on_active_shared_folder_update(self, context: bpy.types.Context):
    """
    Make shared collection collection active in `context`'s scene if applicable.

    :param context: The context.
    """
    col = get_active_shared_folder(context)
    if not col or not (layer_col := find_layer_collection(context.view_layer, col)):
        return
    context.view_layer.active_layer_collection = layer_col


def register():
    # Active shared collection index property
    bpy.types.WindowManager.active_shared_folder_index = bpy.props.IntProperty(
        options=set(),
        update=on_active_shared_folder_update,
    )


def unregister():
    del bpy.types.WindowManager.active_shared_folder_index
