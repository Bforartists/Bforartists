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

from .internals import (
    layer_collections,
    rto_history,
    copy_buffer,
    swap_buffer,
)

rto_path = {
    "exclude": "exclude",
    "select": "collection.hide_select",
    "hide": "hide_viewport",
    "disable": "collection.hide_viewport",
    "render": "collection.hide_render"
    }


def get_rto(layer_collection, rto):
    if rto in ["exclude", "hide"]:
        return getattr(layer_collection, rto_path[rto])

    else:
        collection = getattr(layer_collection, "collection")
        return getattr(collection, rto_path[rto].split(".")[1])


def set_rto(layer_collection, rto, value):
    if rto in ["exclude", "hide"]:
        setattr(layer_collection, rto_path[rto], value)

    else:
        collection = getattr(layer_collection, "collection")
        setattr(collection, rto_path[rto].split(".")[1], value)


def apply_to_children(laycol, apply_function):
    laycol_iter_list = [laycol.children]

    while len(laycol_iter_list) > 0:
        new_laycol_iter_list = []

        for laycol_iter in laycol_iter_list:
            for layer_collection in laycol_iter:
                apply_function(layer_collection)

                if len(layer_collection.children) > 0:
                    new_laycol_iter_list.append(layer_collection.children)

        laycol_iter_list = new_laycol_iter_list


def isolate_rto(cls, self, view_layer, rto, *, children=False):
    laycol_ptr = layer_collections[self.name]["ptr"]
    target = rto_history[rto][view_layer]["target"]
    history = rto_history[rto][view_layer]["history"]

    # get active collections
    active_layer_collections = [x["ptr"] for x in layer_collections.values()
                                if not get_rto(x["ptr"], rto)]

    # check if previous state should be restored
    if cls.isolated and self.name == target:
        # restore previous state
        for x, item in enumerate(layer_collections.values()):
            set_rto(item["ptr"], rto, history[x])

        # reset target and history
        del rto_history[rto][view_layer]

        cls.isolated = False

    # check if all RTOs should be activated
    elif (len(active_layer_collections) == 1 and
          active_layer_collections[0].name == self.name):
        # activate all collections
        for item in layer_collections.values():
            set_rto(item["ptr"], rto, False)

        # reset target and history
        del rto_history[rto][view_layer]

        cls.isolated = False

    else:
        # isolate collection

        rto_history[rto][view_layer]["target"] = self.name

        # reset history
        history.clear()

        # save state
        for item in layer_collections.values():
            history.append(get_rto(item["ptr"], rto))

        child_states = {}
        if children:
            # get child states
            def get_child_states(layer_collection):
                child_states[layer_collection.name] = get_rto(layer_collection, rto)

            apply_to_children(laycol_ptr, get_child_states)

        # isolate collection
        for item in layer_collections.values():
            if item["name"] != laycol_ptr.name:
                set_rto(item["ptr"], rto, True)

        set_rto(laycol_ptr, rto, False)

        if rto != "exclude":
            # activate all parents
            laycol = layer_collections[self.name]
            while laycol["id"] != 0:
                set_rto(laycol["ptr"], rto, False)
                laycol = laycol["parent"]

            if children:
                # restore child states
                def restore_child_states(layer_collection):
                    set_rto(layer_collection, rto, child_states[layer_collection.name])

                apply_to_children(laycol_ptr, restore_child_states)

        else:
            if children:
                # restore child states
                def restore_child_states(layer_collection):
                    set_rto(layer_collection, rto, child_states[layer_collection.name])

                apply_to_children(laycol_ptr, restore_child_states)

            else:
                # deactivate all children
                def deactivate_all_children(layer_collection):
                    set_rto(layer_collection, rto, True)

                apply_to_children(laycol_ptr, deactivate_all_children)

        cls.isolated = True


def toggle_children(self, view_layer, rto):
    laycol_ptr = layer_collections[self.name]["ptr"]
    # clear rto history
    del rto_history[rto][view_layer]
    rto_history[rto+"_all"].pop(view_layer, None)

    # toggle rto state
    state = not get_rto(laycol_ptr, rto)
    set_rto(laycol_ptr, rto, state)

    def set_state(layer_collection):
        set_rto(layer_collection, rto, state)

    apply_to_children(laycol_ptr, set_state)


def activate_all_rtos(view_layer, rto):
    history = rto_history[rto+"_all"][view_layer]

    # if not activated, activate all
    if len(history) == 0:
        keep_history = False

        for item in reversed(list(layer_collections.values())):
            if get_rto(item["ptr"], rto) == True:
                keep_history = True

            history.append(get_rto(item["ptr"], rto))

            set_rto(item["ptr"], rto, False)

        if not keep_history:
            history.clear()

        history.reverse()

    else:
        for x, item in enumerate(layer_collections.values()):
            set_rto(item["ptr"], rto, history[x])

        # clear rto history
        del rto_history[rto+"_all"][view_layer]


def invert_rtos(view_layer, rto):
    if rto == "exclude":
        orig_values = []

        for item in layer_collections.values():
            orig_values.append(get_rto(item["ptr"], rto))

        for x, item in enumerate(layer_collections.values()):
            set_rto(item["ptr"], rto, not orig_values[x])

    else:
        for item in layer_collections.values():
            set_rto(item["ptr"], rto, not get_rto(item["ptr"], rto))

    # clear rto history
    rto_history[rto].pop(view_layer, None)


def copy_rtos(view_layer, rto):
    if not copy_buffer["RTO"]:
        # copy
        copy_buffer["RTO"] = rto
        for laycol in layer_collections.values():
            copy_buffer["values"].append(get_rto(laycol["ptr"], rto))

    else:
        # paste
        for x, laycol in enumerate(layer_collections.values()):
            set_rto(laycol["ptr"], rto, copy_buffer["values"][x])

        # clear rto history
        rto_history[rto].pop(view_layer, None)
        del rto_history[rto+"_all"][view_layer]

        # clear copy buffer
        copy_buffer["RTO"] = ""
        copy_buffer["values"].clear()


def swap_rtos(view_layer, rto):
    if not swap_buffer["A"]["values"]:
        # get A
        swap_buffer["A"]["RTO"] = rto
        for laycol in layer_collections.values():
            swap_buffer["A"]["values"].append(get_rto(laycol["ptr"], rto))

    else:
        # get B
        swap_buffer["B"]["RTO"] = rto
        for laycol in layer_collections.values():
            swap_buffer["B"]["values"].append(get_rto(laycol["ptr"], rto))

        # swap A with B
        for x, laycol in enumerate(layer_collections.values()):
            set_rto(laycol["ptr"], swap_buffer["A"]["RTO"], swap_buffer["B"]["values"][x])
            set_rto(laycol["ptr"], swap_buffer["B"]["RTO"], swap_buffer["A"]["values"][x])


        # clear rto history
        swap_a = swap_buffer["A"]["RTO"]
        swap_b = swap_buffer["B"]["RTO"]

        rto_history[swap_a].pop(view_layer, None)
        rto_history[swap_a+"_all"].pop(view_layer, None)
        rto_history[swap_b].pop(view_layer, None)
        rto_history[swap_b+"_all"].pop(view_layer, None)

        # clear swap buffer
        swap_buffer["A"]["RTO"] = ""
        swap_buffer["A"]["values"].clear()
        swap_buffer["B"]["RTO"] = ""
        swap_buffer["B"]["values"].clear()


def clear_copy(rto):
    if copy_buffer["RTO"] == rto:
        copy_buffer["RTO"] = ""
        copy_buffer["values"].clear()


def clear_swap(rto):
    if swap_buffer["A"]["RTO"] == rto:
        swap_buffer["A"]["RTO"] = ""
        swap_buffer["A"]["values"].clear()
        swap_buffer["B"]["RTO"] = ""
        swap_buffer["B"]["values"].clear()
