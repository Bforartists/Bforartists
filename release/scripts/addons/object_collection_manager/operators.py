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

from copy import deepcopy

from bpy.types import (
    Operator,
)

from bpy.props import (
    BoolProperty,
    StringProperty,
    IntProperty
)

from . import internals

from .internals import (
    expanded,
    layer_collections,
    qcd_slots,
    rto_history,
    expand_history,
    phantom_history,
    copy_buffer,
    swap_buffer,
    update_property_group,
    get_modifiers,
    get_move_selection,
    get_move_active,
    update_qcd_header,
    send_report,
)

from .operator_utils import (
    get_rto,
    set_rto,
    apply_to_children,
    isolate_rto,
    toggle_children,
    activate_all_rtos,
    invert_rtos,
    copy_rtos,
    swap_rtos,
    clear_copy,
    clear_swap,
)

class SetActiveCollection(Operator):
    '''Set the active collection'''
    bl_label = "Set Active Collection"
    bl_idname = "view3d.set_active_collection"
    bl_options = {'UNDO'}

    collection_index: IntProperty()
    collection_name: StringProperty()

    def execute(self, context):
        if self.collection_index == -1:
            layer_collection = context.view_layer.layer_collection

        else:
            laycol = layer_collections[self.collection_name]
            layer_collection = laycol["ptr"]

            # set selection to this row
            cm = context.scene.collection_manager
            cm.cm_list_index = laycol["row_index"]

        context.view_layer.active_layer_collection = layer_collection

        if context.view_layer.active_layer_collection != layer_collection:
            self.report({'WARNING'}, "Can't set excluded collection as active")

        return {'FINISHED'}


class ExpandAllOperator(Operator):
    '''Expand/Collapse all collections'''
    bl_label = "Expand All Items"
    bl_idname = "view3d.expand_all_items"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global expand_history

        if len(expanded) > 0:
            expanded.clear()
            context.scene.collection_manager.cm_list_index = 0
        else:
            for laycol in layer_collections.values():
                if laycol["ptr"].children:
                    expanded.add(laycol["name"])

        # clear expand history
        expand_history["target"] = ""
        expand_history["history"].clear()

        # update tree view
        update_property_group(context)

        return {'FINISHED'}


class ExpandSublevelOperator(Operator):
    bl_label = "Expand Sublevel Items"
    bl_description = (
        "  * Ctrl+LMB - Expand/Collapse all sublevels\n"
        "  * Shift+LMB - Isolate tree/Restore\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.expand_sublevel"
    bl_options = {'REGISTER', 'UNDO'}

    expand: BoolProperty()
    name: StringProperty()
    index: IntProperty()

    def invoke(self, context, event):
        global expand_history
        cls = ExpandSublevelOperator

        modifiers = get_modifiers(event)

        if modifiers == {"alt"}:
            expand_history["target"] = ""
            expand_history["history"].clear()

        elif modifiers == {"ctrl"}:
            # expand/collapse all subcollections
            expand = None

            # check whether to expand or collapse
            if self.name in expanded:
                expanded.remove(self.name)
                expand = False
            else:
                expanded.add(self.name)
                expand = True

            # do expanding/collapsing
            def set_expanded(layer_collection):
                if expand:
                    expanded.add(layer_collection.name)
                else:
                    expanded.discard(layer_collection.name)

            apply_to_children(layer_collections[self.name]["ptr"], set_expanded)

            expand_history["target"] = ""
            expand_history["history"].clear()

        elif modifiers == {"shift"}:
            def isolate_tree(current_laycol):
                parent = current_laycol["parent"]

                for laycol in parent["children"]:
                    if laycol["name"] != current_laycol["name"] and laycol["name"] in expanded:
                        expanded.remove(laycol["name"])
                        expand_history["history"].append(laycol["name"])

                if parent["parent"]:
                    isolate_tree(parent)

            if self.name == expand_history["target"]:
                for item in expand_history["history"]:
                    expanded.add(item)

                expand_history["target"] = ""
                expand_history["history"].clear()

            else:
                expand_history["target"] = ""
                expand_history["history"].clear()

                isolate_tree(layer_collections[self.name])
                expand_history["target"] = self.name

        else:
            # expand/collapse collection
            if self.expand:
                expanded.add(self.name)
            else:
                expanded.remove(self.name)

            expand_history["target"] = ""
            expand_history["history"].clear()

        # set the selected row to the collection you're expanding/collapsing to
        # preserve the tree view's scrolling
        context.scene.collection_manager.cm_list_index = self.index

        #update tree view
        update_property_group(context)

        return {'FINISHED'}


class CMSetCollectionOperator(Operator):
    bl_label = "Set Object Collection"
    bl_description = (
        "  * LMB - Move object to collection.\n"
        "  * Shift+LMB - Add/Remove object from collection"
        )
    bl_idname = "view3d.set_collection"
    bl_options = {'REGISTER', 'UNDO'}

    collection_index: IntProperty()
    collection_name: StringProperty()

    def invoke(self, context, event):
        if self.collection_index == 0:
            target_collection = context.view_layer.layer_collection.collection

        else:
            laycol = layer_collections[self.collection_name]
            target_collection = laycol["ptr"].collection

        selected_objects = get_move_selection()
        active_object = get_move_active()

        internals.move_triggered = True

        if not selected_objects:
            return {'CANCELLED'}

        if event.shift:
            # add objects to collection

            # make sure there is an active object
            if not active_object:
                active_object = selected_objects[0]

            # check if in collection
            if not active_object.name in target_collection.objects:
                # add to collection
                for obj in selected_objects:
                    if obj.name not in target_collection.objects:
                        target_collection.objects.link(obj)

            else:
                warnings = False
                master_warning = False

                # remove from collections
                for obj in selected_objects:
                    if obj.name in target_collection.objects:

                        # disallow removing if only one
                        if len(obj.users_collection) == 1:
                            warnings = True
                            master_laycol = context.view_layer.layer_collection
                            master_collection = master_laycol.collection

                            if obj.name not in master_collection.objects:
                                master_collection.objects.link(obj)

                            else:
                                master_warning = True
                                continue


                        # remove from collection
                        target_collection.objects.unlink(obj)

                if warnings:
                    if master_warning:
                        send_report(
                        "Error removing 1 or more objects from the Scene Collection.\n"
                        "Objects would be left without a collection."
                        )
                        self.report({"WARNING"},
                        "Error removing 1 or more objects from the Scene Collection."
                        "  Objects would be left without a collection."
                        )

                    else:
                        self.report({"INFO"}, "1 or more objects moved to Scene Collection.")


        else:
            # move objects to collection
            for obj in selected_objects:
                if obj.name not in target_collection.objects:
                    target_collection.objects.link(obj)

                # remove from all other collections
                for collection in obj.users_collection:
                    if collection != target_collection:
                        collection.objects.unlink(obj)

        # update the active object if needed
        if not context.active_object:
            try:
                context.view_layer.objects.active = active_object

            except RuntimeError: # object not in visible collection
                pass

        # update qcd header UI
        update_qcd_header()

        return {'FINISHED'}


class CMExcludeOperator(Operator):
    bl_label = "[EC] Exclude from View Layer"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.exclude_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        global rto_history
        cls = CMExcludeOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        orig_active_collection = context.view_layer.active_layer_collection
        laycol_ptr = layer_collections[self.name]["ptr"]

        if not view_layer in rto_history["exclude"]:
            rto_history["exclude"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del rto_history["exclude"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "exclude")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "exclude")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "exclude", children=True)

        else:
            # toggle exclusion

            # reset exclude history
            del rto_history["exclude"][view_layer]


            # get current child exclusion state
            child_exclusion = []

            def get_child_exclusion(layer_collection):
                child_exclusion.append([layer_collection, layer_collection.exclude])

            apply_to_children(laycol_ptr, get_child_exclusion)


            # toggle exclusion of collection
            laycol_ptr.exclude = not laycol_ptr.exclude


            # set correct state for all children
            for laycol in child_exclusion:
                laycol[0].exclude = laycol[1]

            cls.isolated = False

        # reset active collection
        context.view_layer.active_layer_collection = orig_active_collection

        # reset exclude all history
        if view_layer in rto_history["exclude_all"]:
            del rto_history["exclude_all"][view_layer]

        return {'FINISHED'}


class CMUnExcludeAllOperator(Operator):
    bl_label = "[EC Global] Exclude from View Layer"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_exclude_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global rto_history

        orig_active_collection = context.view_layer.active_layer_collection
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in rto_history["exclude_all"]:
            rto_history["exclude_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del rto_history["exclude_all"][view_layer]
            clear_copy("exclude")
            clear_swap("exclude")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "exclude")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "exclude")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "exclude")

        else:
            activate_all_rtos(view_layer, "exclude")

        # reset active collection
        context.view_layer.active_layer_collection = orig_active_collection

        return {'FINISHED'}


class CMRestrictSelectOperator(Operator):
    bl_label = "[SS] Disable Selection"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.restrict_select_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        global rto_history
        cls = CMRestrictSelectOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = layer_collections[self.name]["ptr"]

        if not view_layer in rto_history["select"]:
            rto_history["select"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del rto_history["select"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "select")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "select")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "select", children=True)

        else:
            # toggle selectable

            # reset select history
            del rto_history["select"][view_layer]

            # toggle selectability of collection
            laycol_ptr.collection.hide_select = not laycol_ptr.collection.hide_select

            cls.isolated = False

        # reset select all history
        if view_layer in rto_history["select_all"]:
            del rto_history["select_all"][view_layer]

        return {'FINISHED'}


class CMUnRestrictSelectAllOperator(Operator):
    bl_label = "[SS Global] Disable Selection"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_restrict_select_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global rto_history

        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in rto_history["select_all"]:
            rto_history["select_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del rto_history["select_all"][view_layer]
            clear_copy("select")
            clear_swap("select")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "select")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "select")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "select")

        else:
            activate_all_rtos(view_layer, "select")

        return {'FINISHED'}


class CMHideOperator(Operator):
    bl_label = "[VV] Hide in Viewport"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.hide_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        global rto_history
        cls = CMHideOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = layer_collections[self.name]["ptr"]

        if not view_layer in rto_history["hide"]:
            rto_history["hide"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del rto_history["hide"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "hide")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "hide")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "hide", children=True)

        else:
            # toggle visible

            # reset hide history
            del rto_history["hide"][view_layer]

            # toggle view of collection
            laycol_ptr.hide_viewport = not laycol_ptr.hide_viewport

            cls.isolated = False

        # reset hide all history
        if view_layer in rto_history["hide_all"]:
            del rto_history["hide_all"][view_layer]

        return {'FINISHED'}


class CMUnHideAllOperator(Operator):
    bl_label = "[VV Global] Hide in Viewport"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_hide_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global rto_history

        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in rto_history["hide_all"]:
            rto_history["hide_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del rto_history["hide_all"][view_layer]
            clear_copy("hide")
            clear_swap("hide")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "hide")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "hide")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "hide")

        else:
            activate_all_rtos(view_layer, "hide")

        return {'FINISHED'}


class CMDisableViewportOperator(Operator):
    bl_label = "[DV] Disable in Viewports"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.disable_viewport_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        global rto_history
        cls = CMDisableViewportOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = layer_collections[self.name]["ptr"]

        if not view_layer in rto_history["disable"]:
            rto_history["disable"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del rto_history["disable"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "disable")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "disable")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "disable", children=True)

        else:
            # toggle disable

            # reset disable history
            del rto_history["disable"][view_layer]

            # toggle disable of collection in viewport
            laycol_ptr.collection.hide_viewport = not laycol_ptr.collection.hide_viewport

            cls.isolated = False

        # reset disable all history
        if view_layer in rto_history["disable_all"]:
            del rto_history["disable_all"][view_layer]

        return {'FINISHED'}


class CMUnDisableViewportAllOperator(Operator):
    bl_label = "[DV Global] Disable in Viewports"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_disable_viewport_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global rto_history

        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in rto_history["disable_all"]:
            rto_history["disable_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del rto_history["disable_all"][view_layer]
            clear_copy("disable")
            clear_swap("disable")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "disable")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "disable")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "disable")

        else:
            activate_all_rtos(view_layer, "disable")

        return {'FINISHED'}


class CMDisableRenderOperator(Operator):
    bl_label = "[RR] Disable in Renders"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.disable_render_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        global rto_history
        cls = CMDisableRenderOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = layer_collections[self.name]["ptr"]

        if not view_layer in rto_history["render"]:
            rto_history["render"][view_layer] = {"target": "", "history": []}


        if modifiers == {"alt"}:
            del rto_history["render"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "render")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "render")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "render", children=True)

        else:
            # toggle renderable

            # reset render history
            del rto_history["render"][view_layer]

            # toggle renderability of collection
            laycol_ptr.collection.hide_render = not laycol_ptr.collection.hide_render

            cls.isolated = False

        # reset render all history
        if view_layer in rto_history["render_all"]:
            del rto_history["render_all"][view_layer]

        return {'FINISHED'}


class CMUnDisableRenderAllOperator(Operator):
    bl_label = "[RR Global] Disable in Renders"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_disable_render_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global rto_history

        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in rto_history["render_all"]:
            rto_history["render_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del rto_history["render_all"][view_layer]
            clear_copy("render")
            clear_swap("render")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "render")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "render")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "render")

        else:
            activate_all_rtos(view_layer, "render")

        return {'FINISHED'}


class CMRemoveCollectionOperator(Operator):
    '''Remove Collection'''
    bl_label = "Remove Collection"
    bl_idname = "view3d.remove_collection"
    bl_options = {'UNDO'}

    collection_name: StringProperty()

    def execute(self, context):
        global rto_history
        global expand_history
        global qcd_slots

        cm = context.scene.collection_manager

        laycol = layer_collections[self.collection_name]
        collection = laycol["ptr"].collection
        parent_collection = laycol["parent"]["ptr"].collection
        selected_row_name = cm.cm_list_collection[cm.cm_list_index].name


        # shift all objects in this collection to the parent collection
        for obj in collection.objects:
            if obj.name not in parent_collection.objects:
                parent_collection.objects.link(obj)


        # shift all child collections to the parent collection
        if collection.children:
            for subcollection in collection.children:
                parent_collection.children.link(subcollection)


        # remove collection, update expanded, and update tree view
        bpy.data.collections.remove(collection)
        expanded.discard(self.collection_name)

        if expand_history["target"] == self.collection_name:
            expand_history["target"] = ""

        if self.collection_name in expand_history["history"]:
            expand_history["history"].remove(self.collection_name)

        update_property_group(context)


        # update selected row
        laycol = layer_collections.get(selected_row_name, None)
        if laycol:
            cm.cm_list_index = laycol["row_index"]

        elif len(cm.cm_list_collection) == cm.cm_list_index:
            cm.cm_list_index -=  1

            if cm.cm_list_index > -1:
                name = cm.cm_list_collection[cm.cm_list_index].name
                laycol = layer_collections[name]
                while not laycol["visible"]:
                    laycol = laycol["parent"]

                cm.cm_list_index = laycol["row_index"]


        # update qcd
        if qcd_slots.contains(name=self.collection_name):
            qcd_slots.del_slot(name=self.collection_name)

        if self.collection_name in qcd_slots.overrides:
            qcd_slots.overrides.remove(self.collection_name)

        # reset history
        for rto in rto_history.values():
            rto.clear()

        return {'FINISHED'}

rename = [False]
class CMNewCollectionOperator(Operator):
    bl_label = "Add New Collection"
    bl_idname = "view3d.add_collection"
    bl_options = {'UNDO'}

    child: BoolProperty()

    @classmethod
    def description(cls, context, properties):
        if properties.child:
            tooltip = (
                "Add New SubCollection.\n"
                "Add a new subcollection to the currently selected collection"
                )

        else:
            tooltip = (
                "Add New Collection.\n"
                "Add a new collection as a sibling of the currently selected collection"
                )

        return tooltip

    def execute(self, context):
        global rto_history

        new_collection = bpy.data.collections.new('Collection')
        cm = context.scene.collection_manager


        # if there are collections
        if len(cm.cm_list_collection) > 0:
            if not cm.cm_list_index == -1:
                # get selected collection
                laycol = layer_collections[cm.cm_list_collection[cm.cm_list_index].name]

                # add new collection
                if self.child:
                    laycol["ptr"].collection.children.link(new_collection)
                    expanded.add(laycol["name"])

                    # update tree view property
                    update_property_group(context)

                    cm.cm_list_index = layer_collections[new_collection.name]["row_index"]

                else:
                    laycol["parent"]["ptr"].collection.children.link(new_collection)

                    # update tree view property
                    update_property_group(context)

                    cm.cm_list_index = layer_collections[new_collection.name]["row_index"]

            else:
                context.scene.collection.children.link(new_collection)

                # update tree view property
                update_property_group(context)

                cm.cm_list_index = layer_collections[new_collection.name]["row_index"]

        # if no collections add top level collection and select it
        else:
            context.scene.collection.children.link(new_collection)

            # update tree view property
            update_property_group(context)

            cm.cm_list_index = 0


        # set new collection to active
        layer_collection = layer_collections[new_collection.name]["ptr"]
        context.view_layer.active_layer_collection = layer_collection

        global rename
        rename[0] = True

        # reset history
        for rto in rto_history.values():
            rto.clear()

        return {'FINISHED'}


class CMPhantomModeOperator(Operator):
    '''Toggle Phantom Mode'''
    bl_label = "Toggle Phantom Mode"
    bl_idname = "view3d.toggle_phantom_mode"

    def execute(self, context):
        global phantom_history
        global rto_history

        cm = context.scene.collection_manager
        view_layer = context.view_layer

        # enter Phantom Mode
        if not cm.in_phantom_mode:

            cm.in_phantom_mode = True

            # save current visibility state
            phantom_history["view_layer"] = view_layer.name

            def save_visibility_state(layer_collection):
                phantom_history["initial_state"][layer_collection.name] = {
                            "exclude": layer_collection.exclude,
                            "select": layer_collection.collection.hide_select,
                            "hide": layer_collection.hide_viewport,
                            "disable": layer_collection.collection.hide_viewport,
                            "render": layer_collection.collection.hide_render,
                                }

            apply_to_children(view_layer.layer_collection, save_visibility_state)

            # save current rto history
            for rto, history, in rto_history.items():
                if history.get(view_layer.name, None):
                    phantom_history[rto+"_history"] = deepcopy(history[view_layer.name])



        else: # return to normal mode
            def restore_visibility_state(layer_collection):
                phantom_laycol = phantom_history["initial_state"][layer_collection.name]

                layer_collection.exclude = phantom_laycol["exclude"]
                layer_collection.collection.hide_select = phantom_laycol["select"]
                layer_collection.hide_viewport = phantom_laycol["hide"]
                layer_collection.collection.hide_viewport = phantom_laycol["disable"]
                layer_collection.collection.hide_render = phantom_laycol["render"]

            apply_to_children(view_layer.layer_collection, restore_visibility_state)


            # restore previous rto history
            for rto, history, in rto_history.items():
                if view_layer.name in history:
                    del history[view_layer.name]

                if phantom_history[rto+"_history"]:
                    history[view_layer.name] = deepcopy(phantom_history[rto+"_history"])

                phantom_history[rto+"_history"].clear()

            cm.in_phantom_mode = False


        return {'FINISHED'}
