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

from bpy.props import (
    StringProperty,
    IntProperty,
)

layer_collections = {}
collection_tree = []
expanded = []
row_index = 0

max_lvl = 0
def get_max_lvl():
    return max_lvl


class QCDSlots():
    _slots = {}
    overrides = {}
    allow_update = True

    def __iter__(self):
        return self._slots.items().__iter__()

    def __repr__(self):
        return self._slots.__repr__()

    def __contains__(self, key):
        try:
            int(key)
            return key in self._slots

        except ValueError:
            return key in self._slots.values()

        return False

    def get_data_for_blend(self):
        return f"{self._slots.__repr__()}\n{self.overrides.__repr__()}"

    def load_blend_data(self, data):
        decoupled_data = data.split("\n")
        blend_slots = eval(decoupled_data[0])
        blend_overrides = eval(decoupled_data[1])

        self._slots = blend_slots
        self.overrides = blend_overrides

    def length(self):
        return len(self._slots)

    def get_idx(self, name, r_value=None):
        for k, v in self._slots.items():
            if v == name:
                return k

        return r_value

    def get_name(self, idx, r_value=None):
        if idx in self._slots:
            return self._slots[idx]

        return r_value

    def add_slot(self, idx, name):
        self._slots[idx] = name

    def update_slot(self, idx, name):
        self._slots[idx] = name

    def del_slot(self, slot):
        try:
            int(slot)
            del self._slots[slot]

        except ValueError:
            idx = self.get_idx(slot)
            del self._slots[idx]

    def clear(self):
        self._slots.clear()

qcd_slots = QCDSlots()


def update_col_name(self, context):
    global layer_collections
    global qcd_slots

    if self.name != self.last_name:
        if self.name == '':
            self.name = self.last_name
            return

        if self.last_name != '':
            # update collection name
            layer_collections[self.last_name]["ptr"].collection.name = self.name

            # update qcd_slot
            idx = qcd_slots.get_idx(self.last_name)
            if idx:
                qcd_slots.update_slot(idx, self.name)

            update_property_group(context)

        self.last_name = self.name

def update_qcd_slot(self, context):
    global qcd_slots

    if not qcd_slots.allow_update:
        return

    update_needed = False

    try:
        int(self.qcd_slot)
    except:

        if self.qcd_slot == "":
            qcd_slots.del_slot(self.name)
            qcd_slots.overrides[self.name] = True

        if self.name in qcd_slots:
            qcd_slots.allow_update = False
            self.qcd_slot = qcd_slots.get_idx(self.name)
            qcd_slots.allow_update = True

        if self.name in qcd_slots.overrides:
            qcd_slots.allow_update = False
            self.qcd_slot = ""
            qcd_slots.allow_update = True

        return

    if self.name in qcd_slots:
        qcd_slots.del_slot(self.name)
        update_needed = True

    if self.qcd_slot in qcd_slots:
        qcd_slots.overrides[qcd_slots.get_name(self.qcd_slot)] = True
        qcd_slots.del_slot(self.qcd_slot)
        update_needed = True

    if int(self.qcd_slot) > 20:
        self.qcd_slot = "20"

    if int(self.qcd_slot) < 1:
        self.qcd_slot = "1"

    qcd_slots.add_slot(self.qcd_slot, self.name)

    if self.name in qcd_slots.overrides:
        del qcd_slots.overrides[self.name]


    if update_needed:
        update_property_group(context)


class CMListCollection(PropertyGroup):
    name: StringProperty(update=update_col_name)
    last_name: StringProperty()
    qcd_slot: StringProperty(name="QCD Slot", update=update_qcd_slot)


def update_collection_tree(context, renumerate=False):
    global max_lvl
    global row_index
    global collection_tree
    global layer_collections
    global qcd_slots

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

    # update qcd
    for x in range(20):
        qcd_slot = qcd_slots.get_name(str(x+1))
        if qcd_slot and not layer_collections.get(qcd_slot, None):
            qcd_slots.del_slot(qcd_slot)

    # update autonumeration
    if qcd_slots.length() < 20:
        lvl = 0
        num = 1
        while lvl <= max_lvl:
            if num > 20:
                break

            for laycol in layer_collections.values():
                if num > 20:
                    break

                if int(laycol["lvl"]) == lvl:
                    if laycol["name"] in qcd_slots.overrides:
                        if not renumerate:
                            num += 1
                        continue

                    if str(num) not in qcd_slots and laycol["name"] not in qcd_slots:
                        qcd_slots.add_slot(str(num), laycol["name"])

                    num += 1

            lvl += 1


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


def update_property_group(context, renumerate=False):
    global collection_tree
    global qcd_slots

    qcd_slots.allow_update = False

    update_collection_tree(context, renumerate)
    context.scene.collection_manager.cm_list_collection.clear()
    create_property_group(context, collection_tree)

    qcd_slots.allow_update = True


def create_property_group(context, tree):
    global in_filter
    global qcd_slots

    cm = context.scene.collection_manager

    for laycol in tree:
        new_cm_listitem = cm.cm_list_collection.add()
        new_cm_listitem.name = laycol["name"]
        new_cm_listitem.qcd_slot = qcd_slots.get_idx(laycol["name"], "")

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
