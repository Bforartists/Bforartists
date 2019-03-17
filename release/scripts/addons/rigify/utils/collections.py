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
import math

from .errors import MetarigError


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


def ensure_widget_collection(context):
    wgts_collection_name = "Widgets"

    view_layer = context.view_layer
    layer_collection = bpy.context.layer_collection
    collection = layer_collection.collection

    widget_collection = bpy.data.collections.get(wgts_collection_name)
    if not widget_collection:
        # ------------------------------------------
        # Create the widget collection
        widget_collection = bpy.data.collections.new(wgts_collection_name)
        widget_collection.hide_viewport = True
        widget_collection.hide_render = True

        widget_layer_collection = None
    else:
        widget_layer_collection = find_layer_collection_by_collection(view_layer.layer_collection, widget_collection)

    if not widget_layer_collection:
        # Add the widget collection to the tree
        collection.children.link(widget_collection)
        widget_layer_collection = [c for c in layer_collection.children if c.collection == widget_collection][0]

    # Make the widget the active collection for the upcoming added (widget) objects
    view_layer.active_layer_collection = widget_layer_collection
    return widget_collection
