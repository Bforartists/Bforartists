# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

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

# For VARS
from . import internals

# For FUNCTIONS
from .internals import (
    update_property_group,
    generate_state,
    check_state,
    get_modifiers,
    get_move_selection,
    get_move_active,
    update_qcd_header,
    send_report,
)

from .operator_utils import (
    apply_to_children,
    isolate_rto,
    toggle_children,
    activate_all_rtos,
    invert_rtos,
    copy_rtos,
    swap_rtos,
    clear_copy,
    clear_swap,
    link_child_collections_to_parent,
    remove_collection,
    select_collection_objects,
    set_exclude_state,
    isolate_sel_objs_collections,
    disable_sel_objs_collections,
)

from . import ui

class SetActiveCollection(Operator):
    '''Set the active collection'''
    bl_label = "Set Active Collection"
    bl_idname = "view3d.set_active_collection"
    bl_options = {'UNDO'}

    is_master_collection: BoolProperty()
    collection_name: StringProperty()

    def execute(self, context):
        if self.is_master_collection:
            layer_collection = context.view_layer.layer_collection

        else:
            laycol = internals.layer_collections[self.collection_name]
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

    def execute(self, context):
        if len(internals.expanded) > 0:
            internals.expanded.clear()
            context.scene.collection_manager.cm_list_index = 0
        else:
            for laycol in internals.layer_collections.values():
                if laycol["ptr"].children:
                    internals.expanded.add(laycol["name"])

        # clear expand history
        internals.expand_history["target"] = ""
        internals.expand_history["history"].clear()

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

    expand: BoolProperty()
    name: StringProperty()
    index: IntProperty()

    def invoke(self, context, event):
        cls = ExpandSublevelOperator

        modifiers = get_modifiers(event)

        if modifiers == {"alt"}:
            internals.expand_history["target"] = ""
            internals.expand_history["history"].clear()

        elif modifiers == {"ctrl"}:
            # expand/collapse all subcollections
            expand = None

            # check whether to expand or collapse
            if self.name in internals.expanded:
                internals.expanded.remove(self.name)
                expand = False
            else:
                internals.expanded.add(self.name)
                expand = True

            # do expanding/collapsing
            def set_expanded(layer_collection):
                if expand:
                    internals.expanded.add(layer_collection.name)
                else:
                    internals.expanded.discard(layer_collection.name)

            apply_to_children(internals.layer_collections[self.name]["ptr"], set_expanded)

            internals.expand_history["target"] = ""
            internals.expand_history["history"].clear()

        elif modifiers == {"shift"}:
            def isolate_tree(current_laycol):
                parent = current_laycol["parent"]

                for laycol in parent["children"]:
                    if (laycol["name"] != current_laycol["name"]
                    and laycol["name"] in internals.expanded):
                        internals.expanded.remove(laycol["name"])
                        internals.expand_history["history"].append(laycol["name"])

                if parent["parent"]:
                    isolate_tree(parent)

            if self.name == internals.expand_history["target"]:
                for item in internals.expand_history["history"]:
                    internals.expanded.add(item)

                internals.expand_history["target"] = ""
                internals.expand_history["history"].clear()

            else:
                internals.expand_history["target"] = ""
                internals.expand_history["history"].clear()

                isolate_tree(internals.layer_collections[self.name])
                internals.expand_history["target"] = self.name

        else:
            # expand/collapse collection
            if self.expand:
                internals.expanded.add(self.name)
            else:
                internals.expanded.remove(self.name)

            internals.expand_history["target"] = ""
            internals.expand_history["history"].clear()

        # set the selected row to the collection you're expanding/collapsing to
        # preserve the tree view's scrolling
        context.scene.collection_manager.cm_list_index = self.index

        #update tree view
        update_property_group(context)

        return {'FINISHED'}


class CMSelectCollectionObjectsOperator(Operator):
    bl_label = "Select All Objects in the Collection"
    bl_description = (
        "  * LMB - Select all objects in collection.\n"
        "  * Shift+LMB - Add/Remove collection objects from selection.\n"
        "  * Ctrl+LMB - Isolate nested selection.\n"
        "  * Ctrl+Shift+LMB - Add/Remove nested from selection"
        )
    bl_idname = "view3d.select_collection_objects"
    bl_options = {'REGISTER', 'UNDO'}

    is_master_collection: BoolProperty()
    collection_name: StringProperty()

    def invoke(self, context, event):
        modifiers = get_modifiers(event)

        if modifiers == {"shift"}:
            select_collection_objects(
                is_master_collection=self.is_master_collection,
                collection_name=self.collection_name,
                replace=False,
                nested=False
                )

        elif modifiers == {"ctrl"}:
            select_collection_objects(
                is_master_collection=self.is_master_collection,
                collection_name=self.collection_name,
                replace=True,
                nested=True
                )

        elif modifiers == {"ctrl", "shift"}:
            select_collection_objects(
                is_master_collection=self.is_master_collection,
                collection_name=self.collection_name,
                replace=False,
                nested=True
                )

        else:
            select_collection_objects(
                is_master_collection=self.is_master_collection,
                collection_name=self.collection_name,
                replace=True,
                nested=False
                )

        return {'FINISHED'}


class SelectAllCumulativeObjectsOperator(Operator):
    '''Select all objects that are present in more than one collection'''
    bl_label = "Select All Cumulative Objects"
    bl_idname = "view3d.select_all_cumulative_objects"

    def execute(self, context):
        selected_cumulative_objects = 0
        total_cumulative_objects = 0

        bpy.ops.object.select_all(action='DESELECT')

        for obj in bpy.data.objects:
            if len(obj.users_collection) > 1:
                if obj.visible_get():
                    obj.select_set(True)
                    if obj.select_get() == True: # needed because obj.select_set can fail silently
                        selected_cumulative_objects +=1

                total_cumulative_objects += 1

        self.report({'INFO'}, f"{selected_cumulative_objects}/{total_cumulative_objects} Cumulative Objects Selected")

        return {'FINISHED'}


class CMSendObjectsToCollectionOperator(Operator):
    bl_label = "Send Objects to Collection"
    bl_description = (
        "  * LMB - Move objects to collection.\n"
        "  * Shift+LMB - Add/Remove objects from collection"
        )
    bl_idname = "view3d.send_objects_to_collection"
    bl_options = {'REGISTER', 'UNDO'}

    is_master_collection: BoolProperty()
    collection_name: StringProperty()

    def invoke(self, context, event):
        if self.is_master_collection:
            target_collection = context.view_layer.layer_collection.collection

        else:
            laycol = internals.layer_collections[self.collection_name]
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
                active_object = tuple(selected_objects)[0]

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
        cls = CMExcludeOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        orig_active_collection = context.view_layer.active_layer_collection
        orig_active_object = context.view_layer.objects.active
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["exclude"]:
            internals.rto_history["exclude"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del internals.rto_history["exclude"][view_layer]
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
            del internals.rto_history["exclude"][view_layer]

            set_exclude_state(laycol_ptr, not laycol_ptr.exclude)

            cls.isolated = False

        # restore active collection
        context.view_layer.active_layer_collection = orig_active_collection

        # restore active object if possible
        if orig_active_object:
            if orig_active_object.name in context.view_layer.objects:
                context.view_layer.objects.active = orig_active_object

        # reset exclude all history
        if view_layer in internals.rto_history["exclude_all"]:
            del internals.rto_history["exclude_all"][view_layer]

        return {'FINISHED'}


class CMUnExcludeAllOperator(Operator):
    bl_label = "[EC Global] Exclude from View Layer"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_exclude_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        orig_active_collection = context.view_layer.active_layer_collection
        orig_active_object = context.view_layer.objects.active
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["exclude_all"]:
            internals.rto_history["exclude_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["exclude_all"][view_layer]
            clear_copy("exclude")
            clear_swap("exclude")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "exclude")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "exclude")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "exclude")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "exclude", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "exclude", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        else:
            activate_all_rtos(view_layer, "exclude")

        # restore active collection
        context.view_layer.active_layer_collection = orig_active_collection

        # restore active object if possible
        if orig_active_object:
            if orig_active_object.name in context.view_layer.objects:
                context.view_layer.objects.active = orig_active_object

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
        cls = CMRestrictSelectOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["select"]:
            internals.rto_history["select"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del internals.rto_history["select"][view_layer]
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
            del internals.rto_history["select"][view_layer]

            # toggle selectability of collection
            laycol_ptr.collection.hide_select = not laycol_ptr.collection.hide_select

            cls.isolated = False

        # reset select all history
        if view_layer in internals.rto_history["select_all"]:
            del internals.rto_history["select_all"][view_layer]

        return {'FINISHED'}


class CMUnRestrictSelectAllOperator(Operator):
    bl_label = "[SS Global] Disable Selection"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_restrict_select_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["select_all"]:
            internals.rto_history["select_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["select_all"][view_layer]
            clear_copy("select")
            clear_swap("select")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "select")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "select")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "select")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "select", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "select", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

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
        cls = CMHideOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["hide"]:
            internals.rto_history["hide"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del internals.rto_history["hide"][view_layer]
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
            del internals.rto_history["hide"][view_layer]

            # toggle view of collection
            laycol_ptr.hide_viewport = not laycol_ptr.hide_viewport

            cls.isolated = False

        # reset hide all history
        if view_layer in internals.rto_history["hide_all"]:
            del internals.rto_history["hide_all"][view_layer]

        return {'FINISHED'}


class CMUnHideAllOperator(Operator):
    bl_label = "[VV Global] Hide in Viewport"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_hide_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["hide_all"]:
            internals.rto_history["hide_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["hide_all"][view_layer]
            clear_copy("hide")
            clear_swap("hide")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "hide")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "hide")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "hide")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "hide", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "hide", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

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
        cls = CMDisableViewportOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["disable"]:
            internals.rto_history["disable"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del internals.rto_history["disable"][view_layer]
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
            del internals.rto_history["disable"][view_layer]

            # toggle disable of collection in viewport
            laycol_ptr.collection.hide_viewport = not laycol_ptr.collection.hide_viewport

            cls.isolated = False

        # reset disable all history
        if view_layer in internals.rto_history["disable_all"]:
            del internals.rto_history["disable_all"][view_layer]

        return {'FINISHED'}


class CMUnDisableViewportAllOperator(Operator):
    bl_label = "[DV Global] Disable in Viewports"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_disable_viewport_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["disable_all"]:
            internals.rto_history["disable_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["disable_all"][view_layer]
            clear_copy("disable")
            clear_swap("disable")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "disable")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "disable")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "disable")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "disable", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "disable", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

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
        cls = CMDisableRenderOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["render"]:
            internals.rto_history["render"][view_layer] = {"target": "", "history": []}


        if modifiers == {"alt"}:
            del internals.rto_history["render"][view_layer]
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
            del internals.rto_history["render"][view_layer]

            # toggle renderability of collection
            laycol_ptr.collection.hide_render = not laycol_ptr.collection.hide_render

            cls.isolated = False

        # reset render all history
        if view_layer in internals.rto_history["render_all"]:
            del internals.rto_history["render_all"][view_layer]

        return {'FINISHED'}


class CMUnDisableRenderAllOperator(Operator):
    bl_label = "[RR Global] Disable in Renders"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_disable_render_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["render_all"]:
            internals.rto_history["render_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["render_all"][view_layer]
            clear_copy("render")
            clear_swap("render")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "render")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "render")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "render")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "render", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "render", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        else:
            activate_all_rtos(view_layer, "render")

        return {'FINISHED'}


class CMHoldoutOperator(Operator):
    bl_label = "[HH] Holdout"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.holdout_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        cls = CMHoldoutOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["holdout"]:
            internals.rto_history["holdout"][view_layer] = {"target": "", "history": []}

        if modifiers == {"alt"}:
            del internals.rto_history["holdout"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "holdout")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "holdout")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "holdout", children=True)

        else:
            # toggle holdout

            # reset holdout history
            del internals.rto_history["holdout"][view_layer]

            # toggle holdout of collection in viewport
            laycol_ptr.holdout = not laycol_ptr.holdout

            cls.isolated = False

        # reset holdout all history
        if view_layer in internals.rto_history["holdout_all"]:
            del internals.rto_history["holdout_all"][view_layer]

        return {'FINISHED'}


class CMUnHoldoutAllOperator(Operator):
    bl_label = "[HH Global] Holdout"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_holdout_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["holdout_all"]:
            internals.rto_history["holdout_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["holdout_all"][view_layer]
            clear_copy("holdout")
            clear_swap("holdout")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "holdout")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "holdout")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "holdout")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "holdout", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "holdout", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        else:
            activate_all_rtos(view_layer, "holdout")

        return {'FINISHED'}


class CMIndirectOnlyOperator(Operator):
    bl_label = "[IO] Indirect Only"
    bl_description = (
        "  * Shift+LMB - Isolate/Restore.\n"
        "  * Shift+Ctrl+LMB - Isolate nested/Restore.\n"
        "  * Ctrl+LMB - Toggle nested.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.indirect_only_collection"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty()

    # static class var
    isolated = False

    def invoke(self, context, event):
        cls = CMIndirectOnlyOperator

        modifiers = get_modifiers(event)
        view_layer = context.view_layer.name
        laycol_ptr = internals.layer_collections[self.name]["ptr"]

        if not view_layer in internals.rto_history["indirect"]:
            internals.rto_history["indirect"][view_layer] = {"target": "", "history": []}


        if modifiers == {"alt"}:
            del internals.rto_history["indirect"][view_layer]
            cls.isolated = False

        elif modifiers == {"shift"}:
            isolate_rto(cls, self, view_layer, "indirect")

        elif modifiers == {"ctrl"}:
            toggle_children(self, view_layer, "indirect")

            cls.isolated = False

        elif modifiers == {"ctrl", "shift"}:
            isolate_rto(cls, self, view_layer, "indirect", children=True)

        else:
            # toggle indirect only

            # reset indirect history
            del internals.rto_history["indirect"][view_layer]

            # toggle indirect only of collection
            laycol_ptr.indirect_only = not laycol_ptr.indirect_only

            cls.isolated = False

        # reset indirect all history
        if view_layer in internals.rto_history["indirect_all"]:
            del internals.rto_history["indirect_all"][view_layer]

        return {'FINISHED'}


class CMUnIndirectOnlyAllOperator(Operator):
    bl_label = "[IO Global] Indirect Only"
    bl_description = (
        "  * LMB - Enable all/Restore.\n"
        "  * Shift+LMB - Invert.\n"
        "  * Shift+Ctrl+LMB - Isolate collections w/ selected objects.\n"
        "  * Shift+Alt+LMB - Disable collections w/ selected objects.\n"
        "  * Ctrl+LMB - Copy/Paste RTOs.\n"
        "  * Ctrl+Alt+LMB - Swap RTOs.\n"
        "  * Alt+LMB - Discard history"
        )
    bl_idname = "view3d.un_indirect_only_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        view_layer = context.view_layer.name
        modifiers = get_modifiers(event)

        if not view_layer in internals.rto_history["indirect_all"]:
            internals.rto_history["indirect_all"][view_layer] = []

        if modifiers == {"alt"}:
            # clear all states
            del internals.rto_history["indirect_all"][view_layer]
            clear_copy("indirect")
            clear_swap("indirect")

        elif modifiers == {"ctrl"}:
            copy_rtos(view_layer, "indirect")

        elif modifiers == {"ctrl", "alt"}:
            swap_rtos(view_layer, "indirect")

        elif modifiers == {"shift"}:
            invert_rtos(view_layer, "indirect")

        elif modifiers == {"shift", "ctrl"}:
            error = isolate_sel_objs_collections(view_layer, "indirect", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        elif modifiers == {"shift", "alt"}:
            error = disable_sel_objs_collections(view_layer, "indirect", "CM")

            if error:
                self.report({"WARNING"}, error)
                return {'CANCELLED'}

        else:
            activate_all_rtos(view_layer, "indirect")

        return {'FINISHED'}


class CMRemoveCollectionOperator(Operator):
    '''Remove Collection'''
    bl_label = "Remove Collection"
    bl_idname = "view3d.remove_collection"
    bl_options = {'UNDO'}

    collection_name: StringProperty()

    def execute(self, context):
        laycol = internals.layer_collections[self.collection_name]
        collection = laycol["ptr"].collection
        parent_collection = laycol["parent"]["ptr"].collection


        # shift all objects in this collection to the parent collection
        for obj in collection.objects:
            if obj.name not in parent_collection.objects:
                parent_collection.objects.link(obj)


        # shift all child collections to the parent collection preserving view layer RTOs
        if collection.children:
            link_child_collections_to_parent(laycol, collection, parent_collection)

        # remove collection, update references, and update tree view
        remove_collection(laycol, collection, context)

        return {'FINISHED'}


class CMRemoveEmptyCollectionsOperator(Operator):
    bl_label = "Remove Empty Collections"
    bl_idname = "view3d.remove_empty_collections"
    bl_options = {'UNDO'}

    without_objects: BoolProperty()

    @classmethod
    def description(cls, context, properties):
        if properties.without_objects:
            tooltip = (
                "Purge All Collections Without Objects.\n"
                "Deletes all collections that don't contain objects even if they have subcollections"
                )

        else:
            tooltip = (
                "Remove Empty Collections.\n"
                "Delete collections that don't have any subcollections or objects"
                )

        return tooltip

    def execute(self, context):
        if self.without_objects:
            empty_collections = [laycol["name"]
                                for laycol in internals.layer_collections.values()
                                if not laycol["ptr"].collection.objects]
        else:
            empty_collections = [laycol["name"]
                                for laycol in internals.layer_collections.values()
                                if not laycol["children"] and
                                not laycol["ptr"].collection.objects]

        for name in empty_collections:
            laycol = internals.layer_collections[name]
            collection = laycol["ptr"].collection
            parent_collection = laycol["parent"]["ptr"].collection

            # link all child collections to the parent collection preserving view layer RTOs
            if collection.children:
                link_child_collections_to_parent(laycol, collection, parent_collection)

            # remove collection, update references, and update tree view
            remove_collection(laycol, collection, context)

        self.report({"INFO"}, f"Removed {len(empty_collections)} collections")

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
        new_collection = bpy.data.collections.new("New Collection")
        cm = context.scene.collection_manager

        # prevent adding collections when collections are filtered
        # and the selection is ambiguous
        if cm.cm_list_index == -1 and ui.CM_UL_items.filtering:
            send_report("Cannot create new collection.\n"
                        "No collection is selected and collections are filtered."
                       )
            return {'CANCELLED'}

        if cm.cm_list_index > -1 and not ui.CM_UL_items.visible_items[cm.cm_list_index]:
            send_report("Cannot create new collection.\n"
                        "The selected collection isn't visible."
                       )
            return {'CANCELLED'}


        # if there are collections
        if len(cm.cm_list_collection) > 0:
            if not cm.cm_list_index == -1:
                # get selected collection
                laycol = internals.layer_collections[cm.cm_list_collection[cm.cm_list_index].name]

                # add new collection
                if self.child:
                    laycol["ptr"].collection.children.link(new_collection)
                    internals.expanded.add(laycol["name"])

                    # update tree view property
                    update_property_group(context)

                    cm.cm_list_index = internals.layer_collections[new_collection.name]["row_index"]

                else:
                    laycol["parent"]["ptr"].collection.children.link(new_collection)

                    # update tree view property
                    update_property_group(context)

                    cm.cm_list_index = internals.layer_collections[new_collection.name]["row_index"]

            else:
                context.scene.collection.children.link(new_collection)

                # update tree view property
                update_property_group(context)

                cm.cm_list_index = internals.layer_collections[new_collection.name]["row_index"]

        # if no collections add top level collection and select it
        else:
            context.scene.collection.children.link(new_collection)

            # update tree view property
            update_property_group(context)

            cm.cm_list_index = 0


        # set new collection to active
        layer_collection = internals.layer_collections[new_collection.name]["ptr"]
        context.view_layer.active_layer_collection = layer_collection

        # show the new collection when collections are filtered.
        ui.CM_UL_items.new_collections.append(new_collection.name)

        global rename
        rename[0] = True

        # reset history
        for rto in internals.rto_history.values():
            rto.clear()

        return {'FINISHED'}


class CMPhantomModeOperator(Operator):
    bl_label = "Toggle Phantom Mode"
    bl_idname = "view3d.toggle_phantom_mode"
    bl_description = (
        "Phantom Mode\n"
        "Saves the state of all RTOs and only allows changes to them, on exit all RTOs are returned to their saved state.\n"
        "Note: modifying collections (except RTOs) externally will exit Phantom Mode and your initial state will be lost"
        )

    def execute(self, context):
        cm = context.scene.collection_manager
        view_layer = context.view_layer

        # enter Phantom Mode
        if not cm.in_phantom_mode:

            cm.in_phantom_mode = True

            # save current visibility state
            internals.phantom_history["view_layer"] = view_layer.name

            def save_visibility_state(layer_collection):
                internals.phantom_history["initial_state"][layer_collection.name] = {
                            "exclude": layer_collection.exclude,
                            "select": layer_collection.collection.hide_select,
                            "hide": layer_collection.hide_viewport,
                            "disable": layer_collection.collection.hide_viewport,
                            "render": layer_collection.collection.hide_render,
                            "holdout": layer_collection.holdout,
                            "indirect": layer_collection.indirect_only,
                                }

            apply_to_children(view_layer.layer_collection, save_visibility_state)

            # save current rto history
            for rto, history, in internals.rto_history.items():
                if history.get(view_layer.name, None):
                    internals.phantom_history[rto+"_history"] = deepcopy(history[view_layer.name])



        else: # return to normal mode
            def restore_visibility_state(layer_collection):
                phantom_laycol = internals.phantom_history["initial_state"][layer_collection.name]

                layer_collection.exclude = phantom_laycol["exclude"]
                layer_collection.collection.hide_select = phantom_laycol["select"]
                layer_collection.hide_viewport = phantom_laycol["hide"]
                layer_collection.collection.hide_viewport = phantom_laycol["disable"]
                layer_collection.collection.hide_render = phantom_laycol["render"]
                layer_collection.holdout = phantom_laycol["holdout"]
                layer_collection.indirect_only = phantom_laycol["indirect"]

            apply_to_children(view_layer.layer_collection, restore_visibility_state)


            # restore previous rto history
            for rto, history, in internals.rto_history.items():
                if view_layer.name in history:
                    del history[view_layer.name]

                if internals.phantom_history[rto+"_history"]:
                    history[view_layer.name] = deepcopy(internals.phantom_history[rto+"_history"])

                internals.phantom_history[rto+"_history"].clear()

            cm.in_phantom_mode = False


        return {'FINISHED'}


class CMApplyPhantomModeOperator(Operator):
    '''Apply changes and quit Phantom Mode'''
    bl_label = "Apply Phantom Mode"
    bl_idname = "view3d.apply_phantom_mode"

    def execute(self, context):
        cm = context.scene.collection_manager
        cm.in_phantom_mode = False

        return {'FINISHED'}


class CMDisableObjectsOperator(Operator):
    '''Disable selected objects in viewports'''
    bl_label = "Disable Selected"
    bl_idname = "view3d.disable_selected_objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            obj.hide_viewport = True

        return {'FINISHED'}


class CMDisableUnSelectedObjectsOperator(Operator):
    '''Disable unselected objects in viewports'''
    bl_label = "Disable Unselected"
    bl_idname = "view3d.disable_unselected_objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj in context.visible_objects and not obj in context.selected_objects:
                obj.hide_viewport = True

        return {'FINISHED'}


class CMRestoreDisabledObjectsOperator(Operator):
    '''Restore disabled objects in viewports'''
    bl_label = "Restore Disabled Objects"
    bl_idname = "view3d.restore_disabled_objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.name in context.view_layer.objects and obj.hide_viewport:
                obj.hide_viewport = False
                obj.select_set(True)

        return {'FINISHED'}


class CMUndoWrapper(Operator):
    bl_label = "Undo"
    bl_description = "Undo previous action"
    bl_idname = "view3d.undo_wrapper"

    @classmethod
    def poll(self, context):
        return bpy.ops.ed.undo.poll()

    def execute(self, context):
        internals.collection_state.clear()
        internals.collection_state.update(generate_state())
        bpy.ops.ed.undo()
        update_property_group(context)

        check_state(context, cm_popup=True)

        # clear buffers
        internals.copy_buffer["RTO"] = ""
        internals.copy_buffer["values"].clear()

        internals.swap_buffer["A"]["RTO"] = ""
        internals.swap_buffer["A"]["values"].clear()
        internals.swap_buffer["B"]["RTO"] = ""
        internals.swap_buffer["B"]["values"].clear()

        return {'FINISHED'}


class CMRedoWrapper(Operator):
    bl_label = "Redo"
    bl_description = "Redo previous action"
    bl_idname = "view3d.redo_wrapper"

    @classmethod
    def poll(self, context):
        return bpy.ops.ed.redo.poll()

    def execute(self, context):
        bpy.ops.ed.redo()
        update_property_group(context)

        return {'FINISHED'}
