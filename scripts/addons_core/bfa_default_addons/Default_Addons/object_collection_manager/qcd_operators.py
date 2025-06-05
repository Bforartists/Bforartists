# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

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
    get_modifiers,
    get_move_selection,
    get_move_active,
    update_qcd_header,
)

from .operator_utils import (
    mode_converter,
    apply_to_children,
    select_collection_objects,
    set_exclude_state,
    isolate_sel_objs_collections,
    disable_sel_objs_collections,
)

class LockedObjects():
    def __init__(self):
        self.objs = []
        self.mode = ""

def get_locked_objs(context):
    # get objects not in object mode
    locked = LockedObjects()
    if context.mode == 'OBJECT':
        return locked

    if context.view_layer.objects.active:
        active = context.view_layer.objects.active
        locked.mode = mode_converter[context.mode]

        for obj in context.view_layer.objects:
            if obj.mode != 'OBJECT':
                if obj.mode not in ['POSE', 'WEIGHT_PAINT'] or obj == active:
                    if obj.mode == active.mode:
                        locked.objs.append(obj)

    return locked



class QCDAllBase():
    meta_op = False
    meta_report = None

    context = None
    view_layer = ""
    history = None
    orig_active_collection = None
    orig_active_object = None
    locked = None

    @classmethod
    def init(cls, context):
        cls.context = context
        cls.orig_active_collection = context.view_layer.active_layer_collection
        cls.view_layer = context.view_layer.name
        cls.orig_active_object = context.view_layer.objects.active

        if not cls.view_layer in internals.qcd_history:
            internals.qcd_history[cls.view_layer] = []

        cls.history = internals.qcd_history[cls.view_layer]

        cls.locked = get_locked_objs(context)

    @classmethod
    def apply_history(cls):
        for x, item in enumerate(internals.layer_collections.values()):
            item["ptr"].exclude = cls.history[x]

        # clear rto history
        del internals.qcd_history[cls.view_layer]

        internals.qcd_collection_state.clear()
        cls.history = None

    @classmethod
    def finalize(cls):
        # restore active collection
        cls.context.view_layer.active_layer_collection = cls.orig_active_collection

        # restore active object if possible
        if cls.orig_active_object:
            if cls.orig_active_object.name in cls.context.view_layer.objects:
                cls.context.view_layer.objects.active = cls.orig_active_object

        # restore locked objects back to their original mode
        # needed because of exclude child updates
        if cls.context.view_layer.objects.active:
            if cls.locked.objs:
                bpy.ops.object.mode_set(mode=cls.locked.mode)

    @classmethod
    def clear(cls):
        cls.context = None
        cls.view_layer = ""
        cls.history = None
        cls.orig_active_collection = None
        cls.orig_active_object = None
        cls.locked = None


class EnableAllQCDSlotsMeta(Operator):
    '''QCD All Meta Operator'''
    bl_label = "Quick View Toggles"
    bl_idname = "view3d.enable_all_qcd_slots_meta"

    @classmethod
    def description(cls, context, properties):
        hotkey_string = (
            "  * LMB - Enable all slots/Restore.\n"
            "  * Alt+LMB - Discard History.\n"
            "  * LMB+Hold - Menu"
            )

        return hotkey_string

    def invoke(self, context, event):
        qab = QCDAllBase

        modifiers = get_modifiers(event)

        qab.meta_op = True

        if modifiers == {"alt"}:
            bpy.ops.view3d.discard_qcd_history()

        else:
            qab.init(context)

            if not qab.history:
                bpy.ops.view3d.enable_all_qcd_slots()

            else:
                qab.apply_history()
                qab.finalize()


        if qab.meta_report:
            self.report({"INFO"}, qab.meta_report)
            qab.meta_report = None

        qab.meta_op = False


        return {'FINISHED'}


class EnableAllQCDSlots(Operator):
    '''Toggles between the current state and all enabled'''
    bl_label = "Enable All QCD Slots"
    bl_idname = "view3d.enable_all_qcd_slots"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        qab = QCDAllBase

        # validate qcd slots
        if not dict(internals.qcd_slots):
            if qab.meta_op:
                qab.meta_report = "No QCD slots."
            else:
                self.report({"INFO"}, "No QCD slots.")

            return {'CANCELLED'}

        qab.init(context)

        if not qab.history:
            keep_history = False

            for laycol in internals.layer_collections.values():
                is_qcd_slot = internals.qcd_slots.contains(name=laycol["name"])

                qab.history.append(laycol["ptr"].exclude)

                if is_qcd_slot and laycol["ptr"].exclude:
                    keep_history = True
                    set_exclude_state(laycol["ptr"], False)


            if not keep_history:
                # clear rto history
                del internals.qcd_history[qab.view_layer]
                qab.clear()

                if qab.meta_op:
                    qab.meta_report = "All QCD slots are already enabled."

                else:
                    self.report({"INFO"}, "All QCD slots are already enabled.")

                return {'CANCELLED'}

            internals.qcd_collection_state.clear()
            internals.qcd_collection_state.update(internals.generate_state(qcd=True))

        else:
            qab.apply_history()

        qab.finalize()

        return {'FINISHED'}


class EnableAllQCDSlotsIsolated(Operator):
    '''Toggles between the current state and all enabled (non-QCD collections disabled)'''
    bl_label = "Enable All QCD Slots Isolated"
    bl_idname = "view3d.enable_all_qcd_slots_isolated"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        qab = QCDAllBase

        # validate qcd slots
        if not dict(internals.qcd_slots):
            self.report({"INFO"}, "No QCD slots.")

            return {'CANCELLED'}

        qab.init(context)

        if qab.locked.objs and not internals.qcd_slots.object_in_slots(qab.orig_active_object):
            # clear rto history
            del internals.qcd_history[qab.view_layer]
            qab.clear()

            self.report({"WARNING"}, "Cannot execute.  The active object would be lost.")

            return {'CANCELLED'}

        if not qab.history:
            keep_history = False

            for laycol in internals.layer_collections.values():
                is_qcd_slot = internals.qcd_slots.contains(name=laycol["name"])

                qab.history.append(laycol["ptr"].exclude)

                if is_qcd_slot and laycol["ptr"].exclude:
                    keep_history = True
                    set_exclude_state(laycol["ptr"], False)

                if not is_qcd_slot and not laycol["ptr"].exclude:
                    keep_history = True
                    set_exclude_state(laycol["ptr"], True)


            if not keep_history:
                # clear rto history
                del internals.qcd_history[qab.view_layer]
                qab.clear()

                self.report({"INFO"}, "All QCD slots are already enabled and isolated.")
                return {'CANCELLED'}

            internals.qcd_collection_state.clear()
            internals.qcd_collection_state.update(internals.generate_state(qcd=True))

        else:
            qab.apply_history()

        qab.finalize()

        return {'FINISHED'}

class IsolateSelectedObjectsCollections(Operator):
    '''Isolate collections (via EC) that contain the selected objects'''
    bl_label = "Isolate Selected Objects Collections"
    bl_idname = "view3d.isolate_selected_objects_collections"

    def execute(self, context):
        qab = QCDAllBase
        qab.init(context)

        use_active = bool(context.mode != 'OBJECT')

        # isolate
        error = isolate_sel_objs_collections(qab.view_layer, "exclude", "QCD", use_active=use_active)

        if error:
            qab.clear()
            self.report({"WARNING"}, error)
            return {'CANCELLED'}

        qab.finalize()

        internals.qcd_collection_state.clear()
        internals.qcd_collection_state.update(internals.generate_state(qcd=True))

        return {'FINISHED'}


class DisableSelectedObjectsCollections(Operator):
    '''Disable all collections that contain the selected objects'''
    bl_label = "Disable Selected Objects Collections"
    bl_idname = "view3d.disable_selected_objects_collections"

    def execute(self, context):
        qab = QCDAllBase
        qab.init(context)

        if qab.locked.objs:
            # clear rto history
            del internals.qcd_history[qab.view_layer]
            qab.clear()

            self.report({"WARNING"}, "Can only be executed in Object Mode")
            return {'CANCELLED'}

        # disable
        error = disable_sel_objs_collections(qab.view_layer, "exclude", "QCD")

        if error:
            qab.clear()
            self.report({"WARNING"}, error)
            return {'CANCELLED'}

        qab.finalize()

        internals.qcd_collection_state.clear()
        internals.qcd_collection_state.update(internals.generate_state(qcd=True))

        return {'FINISHED'}


class DisableAllNonQCDSlots(Operator):
    '''Toggles between the current state and all non-QCD collections disabled'''
    bl_label = "Disable All Non QCD Slots"
    bl_idname = "view3d.disable_all_non_qcd_slots"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        qab = QCDAllBase

        # validate qcd slots
        if not dict(internals.qcd_slots):
            self.report({"INFO"}, "No QCD slots.")

            return {'CANCELLED'}

        qab.init(context)

        if qab.locked.objs and not internals.qcd_slots.object_in_slots(qab.orig_active_object):
            # clear rto history
            del internals.qcd_history[qab.view_layer]
            qab.clear()

            self.report({"WARNING"}, "Cannot execute.  The active object would be lost.")

            return {'CANCELLED'}

        if not qab.history:
            keep_history = False

            for laycol in internals.layer_collections.values():
                is_qcd_slot = internals.qcd_slots.contains(name=laycol["name"])

                qab.history.append(laycol["ptr"].exclude)

                if not is_qcd_slot and not laycol["ptr"].exclude:
                    keep_history = True
                    set_exclude_state(laycol["ptr"], True)

            if not keep_history:
                # clear rto history
                del internals.qcd_history[qab.view_layer]
                qab.clear()

                self.report({"INFO"}, "All non QCD slots are already disabled.")
                return {'CANCELLED'}

            internals.qcd_collection_state.clear()
            internals.qcd_collection_state.update(internals.generate_state(qcd=True))

        else:
            qab.apply_history()

        qab.finalize()

        return {'FINISHED'}


class DisableAllCollections(Operator):
    '''Toggles between the current state and all collections disabled'''
    bl_label = "Disable All collections"
    bl_idname = "view3d.disable_all_collections"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        qab = QCDAllBase

        qab.init(context)

        if qab.locked.objs:
            # clear rto history
            del internals.qcd_history[qab.view_layer]
            qab.clear()

            self.report({"WARNING"}, "Cannot execute.  The active object would be lost.")

            return {'CANCELLED'}

        if not qab.history:
            for laycol in internals.layer_collections.values():

                qab.history.append(laycol["ptr"].exclude)

            if all(qab.history): # no collections are enabled
                # clear rto history
                del internals.qcd_history[qab.view_layer]
                qab.clear()

                self.report({"INFO"}, "All collections are already disabled.")
                return {'CANCELLED'}

            for laycol in internals.layer_collections.values():
                laycol["ptr"].exclude = True

            internals.qcd_collection_state.clear()
            internals.qcd_collection_state.update(internals.generate_state(qcd=True))

        else:
            qab.apply_history()

        qab.finalize()

        return {'FINISHED'}


class SelectAllQCDObjects(Operator):
    '''Select all objects in QCD slots'''
    bl_label = "Select All QCD Objects"
    bl_idname = "view3d.select_all_qcd_objects"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        qab = QCDAllBase

        if context.mode != 'OBJECT':
            self.report({"WARNING"}, "Can only be executed in Object Mode")
            return {'CANCELLED'}

        if not context.selectable_objects:
            if qab.meta_op:
                qab.meta_report = "No objects present to select."

            else:
                self.report({"INFO"}, "No objects present to select.")

            return {'CANCELLED'}

        orig_selected_objects = context.selected_objects

        bpy.ops.object.select_all(action='DESELECT')

        for slot, collection_name in internals.qcd_slots:
            select_collection_objects(
                is_master_collection=False,
                collection_name=collection_name,
                replace=False,
                nested=False,
                selection_state=True
                )

        if context.selected_objects == orig_selected_objects:
            for slot, collection_name in internals.qcd_slots:
                select_collection_objects(
                    is_master_collection=False,
                    collection_name=collection_name,
                    replace=False,
                    nested=False,
                    selection_state=False
                    )


        return {'FINISHED'}


class DiscardQCDHistory(Operator):
    '''Discard QCD History'''
    bl_label = "Discard History"
    bl_idname = "view3d.discard_qcd_history"

    def execute(self, context):
        qab = QCDAllBase

        view_layer = context.view_layer.name

        if view_layer in internals.qcd_history:
            del internals.qcd_history[view_layer]
            qab.clear()

        # update header UI
        update_qcd_header()

        return {'FINISHED'}


class MoveToQCDSlot(Operator):
    '''Move object(s) to QCD slot'''
    bl_label = "Move To QCD Slot"
    bl_idname = "view3d.move_to_qcd_slot"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()
    toggle: BoolProperty()

    def execute(self, context):

        selected_objects = get_move_selection()
        active_object = get_move_active()
        internals.move_triggered = True

        qcd_laycol = None
        slot_name = internals.qcd_slots.get_name(self.slot)

        if slot_name:
            qcd_laycol = internals.layer_collections[slot_name]["ptr"]

        else:
            return {'CANCELLED'}


        if not selected_objects:
            return {'CANCELLED'}

        # adds object to slot
        if self.toggle:
            if not active_object:
                active_object = tuple(selected_objects)[0]

            if not active_object.name in qcd_laycol.collection.objects:
                for obj in selected_objects:
                    if obj.name not in qcd_laycol.collection.objects:
                        qcd_laycol.collection.objects.link(obj)

            else:
                for obj in selected_objects:
                    if obj.name in qcd_laycol.collection.objects:

                        if len(obj.users_collection) == 1:
                            continue

                        qcd_laycol.collection.objects.unlink(obj)


        # moves object to slot
        else:
            for obj in selected_objects:
                if obj.name not in qcd_laycol.collection.objects:
                    qcd_laycol.collection.objects.link(obj)

                for collection in obj.users_collection:
                    qcd_idx = internals.qcd_slots.get_idx(collection.name)
                    if qcd_idx != self.slot:
                        collection.objects.unlink(obj)


        # update the active object if needed
        if not context.active_object:
            try:
                context.view_layer.objects.active = active_object

            except RuntimeError: # object not in visible slot
                pass

        # update header UI
        update_qcd_header()

        return {'FINISHED'}


class ViewMoveQCDSlot(Operator):
    bl_label = ""
    bl_idname = "view3d.view_move_qcd_slot"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    @classmethod
    def description(cls, context, properties):
        slot_name = internals.qcd_slots.get_name(properties.slot)
        slot_string = f"QCD Slot {properties.slot}: \"{slot_name}\"\n"
        selection_hotkeys = ""

        if context.mode == 'OBJECT':
            selection_hotkeys = (
                ".\n"
                "  * Alt+LMB - Select objects in slot.\n"
                "  * Alt+Shift+LMB - Toggle objects' selection for slot"
                )

        hotkey_string = (
            "  * LMB - Isolate slot.\n"
            "  * Shift+LMB - Toggle slot.\n"
            "  * Ctrl+LMB - Move objects to slot.\n"
            "  * Ctrl+Shift+LMB - Toggle objects' slot"
            + selection_hotkeys
            )

        return f"{slot_string}{hotkey_string}"

    def invoke(self, context, event):
        modifiers = get_modifiers(event)

        if modifiers == {"shift"}:
            bpy.ops.view3d.view_qcd_slot(slot=self.slot, toggle=True)

        elif modifiers == {"ctrl"}:
            bpy.ops.view3d.move_to_qcd_slot(slot=self.slot, toggle=False)

        elif modifiers == {"ctrl", "shift"}:
            bpy.ops.view3d.move_to_qcd_slot(slot=self.slot, toggle=True)

        elif modifiers == {"alt"}:
            select_collection_objects(
                is_master_collection=False,
                collection_name=internals.qcd_slots.get_name(self.slot),
                replace=True,
                nested=False
                )

        elif modifiers == {"alt", "shift"}:
            select_collection_objects(
                is_master_collection=False,
                collection_name=internals.qcd_slots.get_name(self.slot),
                replace=False,
                nested=False
                )

        else:
            bpy.ops.view3d.view_qcd_slot(slot=self.slot, toggle=False)

        return {'FINISHED'}

class ViewQCDSlot(Operator):
    '''View objects in QCD slot'''
    bl_label = "View QCD Slot"
    bl_idname = "view3d.view_qcd_slot"
    bl_options = {'UNDO'}

    slot: StringProperty()
    toggle: BoolProperty()

    def execute(self, context):
        qcd_laycol = None
        slot_name = internals.qcd_slots.get_name(self.slot)

        if slot_name:
            qcd_laycol = internals.layer_collections[slot_name]["ptr"]

        else:
            return {'CANCELLED'}


        orig_active_object = context.view_layer.objects.active
        locked = get_locked_objs(context)


        if self.toggle:
            # check if slot can be toggled off.
            if not qcd_laycol.exclude:
                if not set(locked.objs).isdisjoint(qcd_laycol.collection.objects):
                    return {'CANCELLED'}

            # toggle exclusion of qcd_laycol
            set_exclude_state(qcd_laycol, not qcd_laycol.exclude)

        else:
            # exclude all collections
            for laycol in internals.layer_collections.values():
                if laycol["name"] != qcd_laycol.name:
                    # prevent exclusion if locked objects in this collection
                    if set(locked.objs).isdisjoint(laycol["ptr"].collection.objects):
                        laycol["ptr"].exclude = True
                    else:
                        laycol["ptr"].exclude = False

            # un-exclude target collection
            qcd_laycol.exclude = False

            # exclude all children
            def exclude_all_children(layer_collection):
                # prevent exclusion if locked objects in this collection
                if set(locked.objs).isdisjoint(layer_collection.collection.objects):
                    layer_collection.exclude = True
                else:
                    layer_collection.exclude = False

            apply_to_children(qcd_laycol, exclude_all_children)

        if orig_active_object:
            try:
                if orig_active_object.name in context.view_layer.objects:
                    context.view_layer.objects.active = orig_active_object
            except RuntimeError:
                # Blender appears to have a race condition here for versions 3.4+,
                # so if the active object is no longer in the view layer when
                # attempting to set it just do nothing.
                pass

        # restore locked objects back to their original mode
        # needed because of exclude child updates
        if context.view_layer.objects.active:
            if locked.objs:
                bpy.ops.object.mode_set(mode=locked.mode)

        # set layer as active layer collection
        context.view_layer.active_layer_collection = qcd_laycol


        # update header UI
        update_qcd_header()

        view_layer = context.view_layer.name
        if view_layer in internals.rto_history["exclude"]:
            del internals.rto_history["exclude"][view_layer]
        if view_layer in internals.rto_history["exclude_all"]:
            del internals.rto_history["exclude_all"][view_layer]


        return {'FINISHED'}


class UnassignedQCDSlot(Operator):
    bl_label = ""
    bl_idname = "view3d.unassigned_qcd_slot"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    @classmethod
    def description(cls, context, properties):
        slot_string = f"Unassigned QCD Slot {properties.slot}:\n"

        hotkey_string = (
            "  * LMB - Create slot.\n"
            "  * Shift+LMB - Create and isolate slot.\n"
            "  * Ctrl+LMB - Create and move objects to slot.\n"
            "  * Ctrl+Shift+LMB - Create and add objects to slot"
            )

        return f"{slot_string}{hotkey_string}"

    def invoke(self, context, event):
        modifiers = get_modifiers(event)

        new_collection = bpy.data.collections.new(f"Collection {self.slot}")
        context.scene.collection.children.link(new_collection)
        internals.qcd_slots.add_slot(f"{self.slot}", new_collection.name)

        # update tree view property
        update_property_group(context)

        if modifiers == {"shift"}:
            bpy.ops.view3d.view_qcd_slot(slot=self.slot, toggle=False)

        elif modifiers == {"ctrl"}:
            bpy.ops.view3d.move_to_qcd_slot(slot=self.slot, toggle=False)

        elif modifiers == {"ctrl", "shift"}:
            bpy.ops.view3d.move_to_qcd_slot(slot=self.slot, toggle=True)

        else:
            pass

        return {'FINISHED'}


class CreateAllQCDSlots(Operator):
    bl_label = "Create All QCD Slots"
    bl_description = "Create any missing QCD slots so you have a full 20"
    bl_idname = "view3d.create_all_qcd_slots"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for slot_number in range(1, 21):
            if not internals.qcd_slots.get_name(f"{slot_number}"):
                new_collection = bpy.data.collections.new(f"Collection {slot_number}")
                context.scene.collection.children.link(new_collection)
                internals.qcd_slots.add_slot(f"{slot_number}", new_collection.name)

        # update tree view property
        update_property_group(context)

        return {'FINISHED'}


class RenumerateQCDSlots(Operator):
    bl_label = "Renumber QCD Slots"
    bl_description = (
        "Renumber QCD slots.\n"
        "  * LMB - Renumber (breadth first) from slot 1.\n"
        "  * +Ctrl - Linear.\n"
        "  * +Alt - Reset.\n"
        "  * +Shift - Constrain to branch"
        )
    bl_idname = "view3d.renumerate_qcd_slots"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        modifiers = get_modifiers(event)

        beginning = False
        depth_first = False
        constrain = False

        if 'alt' in modifiers:
            beginning=True

        if 'ctrl' in modifiers:
            depth_first=True

        if 'shift' in modifiers:
            constrain=True

        internals.qcd_slots.renumerate(beginning=beginning,
                             depth_first=depth_first,
                             constrain=constrain)

        update_property_group(context)

        return {'FINISHED'}
