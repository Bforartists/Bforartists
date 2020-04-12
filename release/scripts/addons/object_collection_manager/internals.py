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

from . import persistent_data

import bpy

from bpy.types import (
    PropertyGroup,
    Operator,
)

from bpy.props import (
    StringProperty,
    IntProperty,
)

move_triggered = False
move_selection = []
move_active = None

layer_collections = {}
collection_tree = []
collection_state = {}
expanded = []
row_index = 0

max_lvl = 0
def get_max_lvl():
    return max_lvl


class QCDSlots():
    _slots = {}
    overrides = {}
    allow_update = True

    def __init__(self):
        self._slots = persistent_data.slots
        self.overrides = persistent_data.overrides

    def __iter__(self):
        return self._slots.items().__iter__()

    def __repr__(self):
        return self._slots.__repr__()

    def contains(self, *, idx=None, name=None):
        if idx:
            return idx in self._slots.keys()

        if name:
            return name in self._slots.values()

        raise

    def get_data_for_blend(self):
        return f"{self._slots.__repr__()}\n{self.overrides.__repr__()}"

    def load_blend_data(self, data):
        decoupled_data = data.split("\n")
        blend_slots = eval(decoupled_data[0])
        blend_overrides = eval(decoupled_data[1])

        self._slots.clear()
        self.overrides.clear()

        for key, value in blend_slots.items():
            self._slots[key] = value

        for key, value in blend_overrides.items():
            self.overrides[key] = value

    def length(self):
        return len(self._slots)

    def get_idx(self, name, r_value=None):
        for idx, slot_name in self._slots.items():
            if slot_name == name:
                return idx

        return r_value

    def get_name(self, idx, r_value=None):
        if idx in self._slots:
            return self._slots[idx]

        return r_value

    def add_slot(self, idx, name):
        self._slots[idx] = name

        if name in self.overrides:
            del self.overrides[name]

    def update_slot(self, idx, name):
        self.add_slot(idx, name)

    def del_slot(self, *, idx=None, name=None):
        if idx and not name:
            del self._slots[idx]
            return

        if name and not idx:
            slot_idx = self.get_idx(name)
            del self._slots[slot_idx]
            return

        raise

    def add_override(self, name):
        qcd_slots.del_slot(name=name)
        qcd_slots.overrides[name] = True

    def clear_slots(self):
        self._slots.clear()

    def update_qcd(self):
        for idx, name in list(self._slots.items()):
            if not layer_collections.get(name, None):
                qcd_slots.del_slot(name=name)

    def auto_numerate(self, *, renumerate=False):
        global max_lvl

        if self.length() < 20:
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

                        if (not self.contains(idx=str(num)) and
                            not self.contains(name=laycol["name"])):
                                self.add_slot(str(num), laycol["name"])

                        num += 1

                lvl += 1

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
        int(self.qcd_slot_idx)

    except ValueError:
        if self.qcd_slot_idx == "":
            qcd_slots.add_override(self.name)

        if qcd_slots.contains(name=self.name):
            qcd_slots.allow_update = False
            self.qcd_slot_idx = qcd_slots.get_idx(self.name)
            qcd_slots.allow_update = True

        if self.name in qcd_slots.overrides:
            qcd_slots.allow_update = False
            self.qcd_slot_idx = ""
            qcd_slots.allow_update = True

        return

    if qcd_slots.contains(name=self.name):
        qcd_slots.del_slot(name=self.name)
        update_needed = True

    if qcd_slots.contains(idx=self.qcd_slot_idx):
        qcd_slots.add_override(qcd_slots.get_name(self.qcd_slot_idx))
        update_needed = True

    if int(self.qcd_slot_idx) > 20:
        self.qcd_slot_idx = "20"

    if int(self.qcd_slot_idx) < 1:
        self.qcd_slot_idx = "1"

    qcd_slots.add_slot(self.qcd_slot_idx, self.name)

    if update_needed:
        update_property_group(context)


class CMListCollection(PropertyGroup):
    name: StringProperty(update=update_col_name)
    last_name: StringProperty()
    qcd_slot_idx: StringProperty(name="QCD Slot", update=update_qcd_slot)


def update_collection_tree(context, *, renumerate_qcd=False):
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

    qcd_slots.update_qcd()

    qcd_slots.auto_numerate(renumerate=renumerate_qcd)


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


def update_property_group(context, *, renumerate_qcd=False):
    global collection_tree
    global qcd_slots

    qcd_slots.allow_update = False

    update_collection_tree(context, renumerate_qcd=renumerate_qcd)
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
        new_cm_listitem.qcd_slot_idx = qcd_slots.get_idx(laycol["name"], "")

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


def generate_state():
    global layer_collections

    state = {
        "name": [],
        "exclude": [],
        "select": [],
        "hide": [],
        "disable": [],
        "render": [],
        }

    for name, laycol in layer_collections.items():
        state["name"].append(name)
        state["exclude"].append(laycol["ptr"].exclude)
        state["select"].append(laycol["ptr"].collection.hide_select)
        state["hide"].append(laycol["ptr"].hide_viewport)
        state["disable"].append(laycol["ptr"].collection.hide_viewport)
        state["render"].append(laycol["ptr"].collection.hide_render)

    return state


def get_move_selection():
    global move_selection

    if not move_selection:
        move_selection = [obj.name for obj in bpy.context.selected_objects]

    return [bpy.data.objects[name] for name in move_selection]


def get_move_active():
    global move_active
    global move_selection

    if not move_active:
        move_active = getattr(bpy.context.view_layer.objects.active, "name", None)

    if move_active not in [obj.name for obj in get_move_selection()]:
        move_active = None

    return bpy.data.objects[move_active] if move_active else None


def update_qcd_header():
    cm = bpy.context.scene.collection_manager
    cm.update_header.clear()
    new_update_header = cm.update_header.add()
    new_update_header.name = "updated"


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
