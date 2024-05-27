# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

# For VARS
from . import internals

# For FUNCTIONS
from .internals import (
    update_property_group,
    get_move_selection,
    get_move_active,
)

mode_converter = {
    'EDIT_MESH': 'EDIT',
    'EDIT_CURVE': 'EDIT',
    'EDIT_SURFACE': 'EDIT',
    'EDIT_TEXT': 'EDIT',
    'EDIT_ARMATURE': 'EDIT',
    'EDIT_METABALL': 'EDIT',
    'EDIT_LATTICE': 'EDIT',
    'POSE': 'POSE',
    'SCULPT': 'SCULPT',
    'PAINT_WEIGHT': 'WEIGHT_PAINT',
    'PAINT_VERTEX': 'VERTEX_PAINT',
    'PAINT_TEXTURE': 'TEXTURE_PAINT',
    'PARTICLE': 'PARTICLE_EDIT',
    'OBJECT': 'OBJECT',
    'PAINT_GPENCIL': 'PAINT_GPENCIL',
    'EDIT_GPENCIL': 'EDIT_GPENCIL',
    'SCULPT_GPENCIL': 'SCULPT_GPENCIL',
    'WEIGHT_GPENCIL': 'WEIGHT_GPENCIL',
    'VERTEX_GPENCIL': 'VERTEX_GPENCIL',
    }


rto_path = {
    "exclude": "exclude",
    "select": "collection.hide_select",
    "hide": "hide_viewport",
    "disable": "collection.hide_viewport",
    "render": "collection.hide_render",
    "holdout": "holdout",
    "indirect": "indirect_only",
    }

set_off_on = {
    "exclude": {
        "off": True,
        "on": False
        },
    "select": {
        "off": True,
        "on": False
        },
    "hide": {
        "off": True,
        "on": False
        },
    "disable": {
        "off": True,
        "on": False
        },
    "render": {
        "off": True,
        "on": False
        },
    "holdout": {
        "off": False,
        "on": True
        },
    "indirect": {
        "off": False,
        "on": True
        }
    }

get_off_on = {
    False: {
        "exclude": "on",
        "select": "on",
        "hide": "on",
        "disable": "on",
        "render": "on",
        "holdout": "off",
        "indirect": "off",
        },

    True: {
        "exclude": "off",
        "select": "off",
        "hide": "off",
        "disable": "off",
        "render": "off",
        "holdout": "on",
        "indirect": "on",
        }
    }


def get_rto(layer_collection, rto):
    if rto in ["exclude", "hide", "holdout", "indirect"]:
        return getattr(layer_collection, rto_path[rto])

    else:
        collection = getattr(layer_collection, "collection")
        return getattr(collection, rto_path[rto].split(".")[1])


def set_rto(layer_collection, rto, value):
    if rto in ["exclude", "hide", "holdout", "indirect"]:
        setattr(layer_collection, rto_path[rto], value)

    else:
        collection = getattr(layer_collection, "collection")
        setattr(collection, rto_path[rto].split(".")[1], value)


def apply_to_children(parent, apply_function, *args, **kwargs):
    # works for both Collections & LayerCollections
    child_lists = [parent.children]

    while child_lists:
        new_child_lists = []

        for child_list in child_lists:
            for child in child_list:
                apply_function(child, *args, **kwargs)

                if child.children:
                    new_child_lists.append(child.children)

        child_lists = new_child_lists


def isolate_rto(cls, self, view_layer, rto, *, children=False):
    off = set_off_on[rto]["off"]
    on = set_off_on[rto]["on"]

    laycol_ptr = internals.layer_collections[self.name]["ptr"]
    target = internals.rto_history[rto][view_layer]["target"]
    history = internals.rto_history[rto][view_layer]["history"]

    # get active collections
    active_layer_collections = [x["ptr"] for x in internals.layer_collections.values()
                                if get_rto(x["ptr"], rto) == on]

    # check if previous state should be restored
    if cls.isolated and self.name == target:
        # restore previous state
        for x, item in enumerate(internals.layer_collections.values()):
            set_rto(item["ptr"], rto, history[x])

        # reset target and history
        del internals.rto_history[rto][view_layer]

        cls.isolated = False

    # check if all RTOs should be activated
    elif (len(active_layer_collections) == 1 and
          active_layer_collections[0].name == self.name):
        # activate all collections
        for item in internals.layer_collections.values():
            set_rto(item["ptr"], rto, on)

        # reset target and history
        del internals.rto_history[rto][view_layer]

        cls.isolated = False

    else:
        # isolate collection

        internals.rto_history[rto][view_layer]["target"] = self.name

        # reset history
        history.clear()

        # save state
        for item in internals.layer_collections.values():
            history.append(get_rto(item["ptr"], rto))

        child_states = {}
        if children:
            # get child states
            def get_child_states(layer_collection):
                child_states[layer_collection.name] = get_rto(layer_collection, rto)

            apply_to_children(laycol_ptr, get_child_states)

        # isolate collection
        for item in internals.layer_collections.values():
            if item["name"] != laycol_ptr.name:
                set_rto(item["ptr"], rto, off)

        set_rto(laycol_ptr, rto, on)

        if rto not in ["exclude", "holdout", "indirect"]:
            # activate all parents
            laycol = internals.layer_collections[self.name]
            while laycol["id"] != 0:
                set_rto(laycol["ptr"], rto, on)
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

            elif rto == "exclude":
                # deactivate all children
                def deactivate_all_children(layer_collection):
                    set_rto(layer_collection, rto, True)

                apply_to_children(laycol_ptr, deactivate_all_children)

        cls.isolated = True


def isolate_sel_objs_collections(view_layer, rto, caller, *, use_active=False):
    selected_objects = get_move_selection()

    if use_active:
        selected_objects.add(get_move_active(always=True))

    if not selected_objects:
        return "No selected objects"

    off = set_off_on[rto]["off"]
    on = set_off_on[rto]["on"]

    if caller == "CM":
        history = internals.rto_history[rto+"_all"][view_layer]

    elif caller == "QCD":
        history = internals.qcd_history[view_layer]


    # if not isolated, isolate collections of selected objects
    if len(history) == 0:
        keep_history = False

        # save history and isolate RTOs
        for item in internals.layer_collections.values():
            history.append(get_rto(item["ptr"], rto))
            rto_state = off

            # check if any of the selected objects are in the collection
            if not set(selected_objects).isdisjoint(item["ptr"].collection.objects):
                rto_state = on

            if history[-1] != rto_state:
                keep_history = True

            if rto == "exclude":
                set_exclude_state(item["ptr"], rto_state)

            else:
                set_rto(item["ptr"], rto, rto_state)

                # activate all parents if needed
                if rto_state == on and rto not in ["holdout", "indirect"]:
                    laycol = item["parent"]
                    while laycol["id"] != 0:
                        set_rto(laycol["ptr"], rto, on)
                        laycol = laycol["parent"]


        if not keep_history:
            history.clear()

            return "Collection already isolated"


    else:
        for x, item in enumerate(internals.layer_collections.values()):
            set_rto(item["ptr"], rto, history[x])

        # clear history
        if caller == "CM":
            del internals.rto_history[rto+"_all"][view_layer]

        elif caller == "QCD":
            del internals.qcd_history[view_layer]


def disable_sel_objs_collections(view_layer, rto, caller):
    off = set_off_on[rto]["off"]
    on = set_off_on[rto]["on"]
    selected_objects = get_move_selection()

    if caller == "CM":
        history = internals.rto_history[rto+"_all"][view_layer]

    elif caller == "QCD":
        history = internals.qcd_history[view_layer]


    if not selected_objects and not history:
        # clear history
        if caller == "CM":
            del internals.rto_history[rto+"_all"][view_layer]

        elif caller == "QCD":
            del internals.qcd_history[view_layer]

        return "No selected objects"

    # if not disabled, disable collections of selected objects
    if len(history) == 0:
        # save history and disable RTOs
        for item in internals.layer_collections.values():
            history.append(get_rto(item["ptr"], rto))

            # check if any of the selected objects are in the collection
            if not set(selected_objects).isdisjoint(item["ptr"].collection.objects):
                if rto == "exclude":
                    set_exclude_state(item["ptr"], off)

                else:
                    set_rto(item["ptr"], rto, off)


    else:
        for x, item in enumerate(internals.layer_collections.values()):
            set_rto(item["ptr"], rto, history[x])

        # clear history
        if caller == "CM":
            del internals.rto_history[rto+"_all"][view_layer]

        elif caller == "QCD":
            del internals.qcd_history[view_layer]


def toggle_children(self, view_layer, rto):
    laycol_ptr = internals.layer_collections[self.name]["ptr"]
    # clear rto history
    del internals.rto_history[rto][view_layer]
    internals.rto_history[rto+"_all"].pop(view_layer, None)

    # toggle rto state
    state = not get_rto(laycol_ptr, rto)
    set_rto(laycol_ptr, rto, state)

    def set_state(layer_collection):
        set_rto(layer_collection, rto, state)

    apply_to_children(laycol_ptr, set_state)


def activate_all_rtos(view_layer, rto):
    off = set_off_on[rto]["off"]
    on = set_off_on[rto]["on"]

    history = internals.rto_history[rto+"_all"][view_layer]

    # if not activated, activate all
    if len(history) == 0:
        keep_history = False

        for item in reversed(list(internals.layer_collections.values())):
            if get_rto(item["ptr"], rto) == off:
                keep_history = True

            history.append(get_rto(item["ptr"], rto))

            set_rto(item["ptr"], rto, on)

        if not keep_history:
            history.clear()

        history.reverse()

    else:
        for x, item in enumerate(internals.layer_collections.values()):
            set_rto(item["ptr"], rto, history[x])

        # clear rto history
        del internals.rto_history[rto+"_all"][view_layer]


def invert_rtos(view_layer, rto):
    if rto == "exclude":
        orig_values = []

        for item in internals.layer_collections.values():
            orig_values.append(get_rto(item["ptr"], rto))

        for x, item in enumerate(internals.layer_collections.values()):
            set_rto(item["ptr"], rto, not orig_values[x])

    else:
        for item in internals.layer_collections.values():
            set_rto(item["ptr"], rto, not get_rto(item["ptr"], rto))

    # clear rto history
    internals.rto_history[rto].pop(view_layer, None)


def copy_rtos(view_layer, rto):
    if not internals.copy_buffer["RTO"]:
        # copy
        internals.copy_buffer["RTO"] = rto
        for laycol in internals.layer_collections.values():
            internals.copy_buffer["values"].append(get_off_on[
                                            get_rto(laycol["ptr"], rto)
                                            ][
                                            rto
                                            ]
                                        )

    else:
        # paste
        for x, laycol in enumerate(internals.layer_collections.values()):
            set_rto(laycol["ptr"],
                    rto,
                    set_off_on[rto][
                        internals.copy_buffer["values"][x]
                        ]
                    )

        # clear rto history
        internals.rto_history[rto].pop(view_layer, None)
        del internals.rto_history[rto+"_all"][view_layer]

        # clear copy buffer
        internals.copy_buffer["RTO"] = ""
        internals.copy_buffer["values"].clear()


def swap_rtos(view_layer, rto):
    if not internals.swap_buffer["A"]["values"]:
        # get A
        internals.swap_buffer["A"]["RTO"] = rto
        for laycol in internals.layer_collections.values():
            internals.swap_buffer["A"]["values"].append(get_off_on[
                                                get_rto(laycol["ptr"], rto)
                                                ][
                                                rto
                                                ]
                                            )

    else:
        # get B
        internals.swap_buffer["B"]["RTO"] = rto
        for laycol in internals.layer_collections.values():
            internals.swap_buffer["B"]["values"].append(get_off_on[
                                                get_rto(laycol["ptr"], rto)
                                                ][
                                                rto
                                                ]
                                            )

        # swap A with B
        for x, laycol in enumerate(internals.layer_collections.values()):
            set_rto(laycol["ptr"], internals.swap_buffer["A"]["RTO"],
                    set_off_on[
                        internals.swap_buffer["A"]["RTO"]
                        ][
                        internals.swap_buffer["B"]["values"][x]
                        ]
                    )

            set_rto(laycol["ptr"], internals.swap_buffer["B"]["RTO"],
                    set_off_on[
                        internals.swap_buffer["B"]["RTO"]
                        ][
                        internals.swap_buffer["A"]["values"][x]
                        ]
                    )


        # clear rto history
        swap_a = internals.swap_buffer["A"]["RTO"]
        swap_b = internals.swap_buffer["B"]["RTO"]

        internals.rto_history[swap_a].pop(view_layer, None)
        internals.rto_history[swap_a+"_all"].pop(view_layer, None)
        internals.rto_history[swap_b].pop(view_layer, None)
        internals.rto_history[swap_b+"_all"].pop(view_layer, None)

        # clear swap buffer
        internals.swap_buffer["A"]["RTO"] = ""
        internals.swap_buffer["A"]["values"].clear()
        internals.swap_buffer["B"]["RTO"] = ""
        internals.swap_buffer["B"]["values"].clear()


def clear_copy(rto):
    if internals.copy_buffer["RTO"] == rto:
        internals.copy_buffer["RTO"] = ""
        internals.copy_buffer["values"].clear()


def clear_swap(rto):
    if internals.swap_buffer["A"]["RTO"] == rto:
        internals.swap_buffer["A"]["RTO"] = ""
        internals.swap_buffer["A"]["values"].clear()
        internals.swap_buffer["B"]["RTO"] = ""
        internals.swap_buffer["B"]["values"].clear()


def link_child_collections_to_parent(laycol, collection, parent_collection):
    # store view layer RTOs for all children of the to be deleted collection
    child_states = {}
    def get_child_states(layer_collection):
        child_states[layer_collection.name] = (layer_collection.exclude,
                                               layer_collection.hide_viewport,
                                               layer_collection.holdout,
                                               layer_collection.indirect_only)

    apply_to_children(laycol["ptr"], get_child_states)

    # link any subcollections of the to be deleted collection to it's parent
    for subcollection in collection.children:
        if not subcollection.name in parent_collection.children:
            parent_collection.children.link(subcollection)

    # apply the stored view layer RTOs to the newly linked collections and their
    # children
    def restore_child_states(layer_collection):
        state = child_states.get(layer_collection.name)

        if state:
            layer_collection.exclude = state[0]
            layer_collection.hide_viewport = state[1]
            layer_collection.holdout = state[2]
            layer_collection.indirect_only = state[3]

    apply_to_children(laycol["parent"]["ptr"], restore_child_states)


def remove_collection(laycol, collection, context):
    # get selected row
    cm = context.scene.collection_manager
    selected_row_name = cm.cm_list_collection[cm.cm_list_index].name

    # delete collection
    bpy.data.collections.remove(collection)

    # update references
    internals.expanded.discard(laycol["name"])

    if internals.expand_history["target"] == laycol["name"]:
        internals.expand_history["target"] = ""

    if laycol["name"] in internals.expand_history["history"]:
        internals.expand_history["history"].remove(laycol["name"])

    if internals.qcd_slots.contains(name=laycol["name"]):
        internals.qcd_slots.del_slot(name=laycol["name"])

    if laycol["name"] in internals.qcd_slots.overrides:
        internals.qcd_slots.overrides.remove(laycol["name"])

    # reset history
    for rto in internals.rto_history.values():
        rto.clear()

    # update tree view
    update_property_group(context)

    # update selected row
    laycol = internals.layer_collections.get(selected_row_name, None)
    if laycol:
        cm.cm_list_index = laycol["row_index"]

    elif len(cm.cm_list_collection) <= cm.cm_list_index:
        cm.cm_list_index =  len(cm.cm_list_collection) - 1

        if cm.cm_list_index > -1:
            name = cm.cm_list_collection[cm.cm_list_index].name
            laycol = internals.layer_collections[name]
            while not laycol["visible"]:
                laycol = laycol["parent"]

            cm.cm_list_index = laycol["row_index"]


def select_collection_objects(is_master_collection, collection_name, replace, nested, selection_state=None):
    if bpy.context.mode != 'OBJECT':
        return

    if is_master_collection:
        target_collection = bpy.context.view_layer.layer_collection.collection

    else:
        laycol = internals.layer_collections[collection_name]
        target_collection = laycol["ptr"].collection

    if replace:
        bpy.ops.object.select_all(action='DESELECT')

    if selection_state == None:
        selection_state = get_move_selection().isdisjoint(target_collection.objects)

    def select_objects(collection, selection_state):
        for obj in collection.objects:
            try:
                obj.select_set(selection_state)
            except RuntimeError:
                pass

    select_objects(target_collection, selection_state)

    if nested:
        apply_to_children(target_collection, select_objects, selection_state)

def set_exclude_state(target_layer_collection, state):
    # get current child exclusion state
    child_exclusion = []

    def get_child_exclusion(layer_collection):
        child_exclusion.append([layer_collection, layer_collection.exclude])

    apply_to_children(target_layer_collection, get_child_exclusion)


    # set exclusion
    target_layer_collection.exclude = state


    # set correct state for all children
    for laycol in child_exclusion:
        laycol[0].exclude = laycol[1]
