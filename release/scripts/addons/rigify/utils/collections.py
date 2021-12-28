#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy


#=============================================
# Collection management
#=============================================

def find_layer_collection_by_collection(layer_collection, collection):
    if collection == layer_collection.collection:
        return layer_collection

    # go recursive
    for child in layer_collection.children:
        layer_collection = find_layer_collection_by_collection(child, collection)
        if layer_collection:
            return layer_collection


def list_layer_collections(layer_collection, visible=False, selectable=False):
    """Returns a list of the collection and its children, with optional filtering by settings."""

    if layer_collection.exclude:
        return []

    collection = layer_collection.collection
    is_visible = not (layer_collection.hide_viewport or collection.hide_viewport)
    is_selectable = is_visible and not collection.hide_select

    if (selectable and not is_selectable) or (visible and not is_visible):
        return []

    found = [layer_collection]

    for child in layer_collection.children:
        found += list_layer_collections(child, visible, selectable)

    return found


def filter_layer_collections_by_object(layer_collections, obj):
    """Returns a subset of collections that contain the given object."""
    return [lc for lc in layer_collections if obj in lc.collection.objects.values()]


def ensure_collection(context, collection_name, hidden=False) -> bpy.types.Collection:
    """Check if a collection with a certain name exists.
    If yes, return it, if not, create it in the scene root collection.
    """
    view_layer = context.view_layer
    active_layer_coll = bpy.context.layer_collection
    active_collection = active_layer_coll.collection

    collection = bpy.data.collections.get(collection_name)
    if not collection:
        # Create the collection
        collection = bpy.data.collections.new(collection_name)
        collection.hide_viewport = hidden
        collection.hide_render = hidden

        layer_collection = None
    else:
        layer_collection = find_layer_collection_by_collection(view_layer.layer_collection, collection)

    if not layer_collection:
        # Let the new collection be a child of the active one.
        active_collection.children.link(collection)
        layer_collection = [c for c in active_layer_coll.children if c.collection == collection][0]

        layer_collection.exclude = True

    # Make the new collection active.
    view_layer.active_layer_collection = layer_collection
    return collection
