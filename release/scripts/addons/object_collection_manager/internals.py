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

# Copyright 2011, Ryan Inch

import bpy

from bpy.types import (
    PropertyGroup,
    Operator,
)

from bpy.props import StringProperty

layer_collections = {}

collection_tree = []

expanded = []

max_lvl = 0
row_index = 0

def get_max_lvl():
    return max_lvl

def update_col_name(self, context):
    if self.name != self.last_name:
        if self.name == '':
            self.name = self.last_name
            return

        if self.last_name != '':
            layer_collections[self.last_name]["ptr"].collection.name = self.name

            update_property_group(context)

        self.last_name = self.name

class CMListCollection(PropertyGroup):
    name: StringProperty(update=update_col_name)
    last_name: StringProperty()


def update_collection_tree(context):
    global max_lvl
    global row_index
    collection_tree.clear()
    layer_collections.clear()
    max_lvl = 0
    row_index = 0

    layer_collection = context.view_layer.layer_collection
    init_laycol_list = layer_collection.children

    master_laycol = {"id": 0,
                     "name": layer_collection.name,
                     "lvl": -1,
                     "row_index": -1,
                     "visible": True,
                     "has_children": True,
                     "expanded": True,
                     "parent": None,
                     "children": [],
                     "ptr": layer_collection
                     }

    get_all_collections(context, init_laycol_list, master_laycol, master_laycol["children"], visible=True)

    for laycol in master_laycol["children"]:
        collection_tree.append(laycol)


def get_all_collections(context, collections, parent, tree, level=0, visible=False):
    global row_index
    global max_lvl

    if level > max_lvl:
        max_lvl = level

    for item in collections:
        laycol = {"id": len(layer_collections) +1,
                  "name": item.name,
                  "lvl": level,
                  "row_index": row_index,
                  "visible":  visible,
                  "has_children": False,
                  "expanded": False,
                  "parent": parent,
                  "children": [],
                  "ptr": item
                  }

        row_index += 1

        layer_collections[item.name] = laycol
        tree.append(laycol)

        if len(item.children) > 0:
            laycol["has_children"] = True

            if item.name in expanded and laycol["visible"]:
                laycol["expanded"] = True
                get_all_collections(context, item.children, laycol, laycol["children"], level+1,  visible=True)

            else:
                get_all_collections(context, item.children, laycol, laycol["children"], level+1)


def update_property_group(context):
    update_collection_tree(context)
    context.scene.collection_manager.cm_list_collection.clear()
    create_property_group(context, collection_tree)


def create_property_group(context, tree):
    global in_filter

    cm = context.scene.collection_manager

    for laycol in tree:
        new_cm_listitem = cm.cm_list_collection.add()
        new_cm_listitem.name = laycol["name"]

        if laycol["has_children"]:
            create_property_group(context, laycol["children"])


def get_modifiers(event):
    modifiers = []

    if event.alt:
        modifiers.append("alt")

    if event.ctrl:
        modifiers.append("ctrl")

    if event.oskey:
        modifiers.append("oskey")

    if event.shift:
        modifiers.append("shift")

    return set(modifiers)


class CMSendReport(Operator):
    bl_label = "Send Report"
    bl_idname = "view3d.cm_send_report"

    message: StringProperty()

    def draw(self, context):
        layout = self.layout

        first = True
        string = ""

        for num, char in enumerate(self.message):
            if char == "\n":
                if first:
                    layout.row().label(text=string, icon='ERROR')
                    first = False
                else:
                    layout.row().label(text=string, icon='BLANK1')

                string = ""
                continue

            string = string + char

        if first:
            layout.row().label(text=string, icon='ERROR')
        else:
            layout.row().label(text=string, icon='BLANK1')

    def invoke(self, context, event):
        wm = context.window_manager

        max_len = 0
        length = 0

        for char in self.message:
            if char == "\n":
                if length > max_len:
                    max_len = length
                length = 0
            else:
                length += 1

        if length > max_len:
            max_len = length

        return wm.invoke_popup(self, width=(30 + (max_len*5.5)))

    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}

def send_report(message):
    def report():
        window = bpy.context.window_manager.windows[0]
        ctx = {'window': window, 'screen': window.screen, }
        bpy.ops.view3d.cm_send_report(ctx, 'INVOKE_DEFAULT', message=message)

    bpy.app.timers.register(report)
