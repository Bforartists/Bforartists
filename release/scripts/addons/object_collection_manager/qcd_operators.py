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
    Operator,
)

from bpy.props import (
    BoolProperty,
    StringProperty,
    IntProperty
)

from . import internals

from .internals import (
    layer_collections,
    rto_history,
    qcd_slots,
    update_property_group,
    get_modifiers,
    get_move_selection,
    get_move_active,
    update_qcd_header,
)

from .operator_utils import (
    apply_to_children,
)


class MoveToQCDSlot(Operator):
    '''Move object(s) to QCD slot'''
    bl_label = "Move To QCD Slot"
    bl_idname = "view3d.move_to_qcd_slot"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()
    toggle: BoolProperty()

    def execute(self, context):
        global qcd_slots
        global layer_collections

        selected_objects = get_move_selection()
        active_object = get_move_active()
        internals.move_triggered = True

        qcd_laycol = None
        slot_name = qcd_slots.get_name(self.slot)

        if slot_name:
            qcd_laycol = layer_collections[slot_name]["ptr"]

        else:
            return {'CANCELLED'}


        if not selected_objects:
            return {'CANCELLED'}

        # adds object to slot
        if self.toggle:
            if not active_object:
                active_object = selected_objects[0]

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
                    qcd_idx = qcd_slots.get_idx(collection.name)
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
        global qcd_slots

        slot_name = qcd_slots.get_name(properties.slot)

        slot_string = f"QCD Slot {properties.slot}: \"{slot_name}\"\n"

        hotkey_string = (
            "  * LMB - Isolate slot.\n"
            "  * Shift+LMB - Toggle slot.\n"
            "  * Ctrl+LMB - Move objects to slot.\n"
            "  * Ctrl+Shift+LMB - Toggle objects' slot"
            )

        return f"{slot_string}{hotkey_string}"

    def invoke(self, context, event):
        global layer_collections
        global qcd_history

        modifiers = get_modifiers(event)

        if modifiers == {"shift"}:
            bpy.ops.view3d.view_qcd_slot(slot=self.slot, toggle=True)

            return {'FINISHED'}

        elif modifiers == {"ctrl"}:
            bpy.ops.view3d.move_to_qcd_slot(slot=self.slot, toggle=False)
            return {'FINISHED'}

        elif modifiers == {"ctrl", "shift"}:
            bpy.ops.view3d.move_to_qcd_slot(slot=self.slot, toggle=True)
            return {'FINISHED'}

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
        global qcd_slots
        global layer_collections
        global rto_history

        qcd_laycol = None
        slot_name = qcd_slots.get_name(self.slot)

        if slot_name:
            qcd_laycol = layer_collections[slot_name]["ptr"]

        else:
            return {'CANCELLED'}


        # get objects not in object mode
        locked_active_obj = context.view_layer.objects.active
        locked_objs = []
        locked_objs_mode = ""
        for obj in context.view_layer.objects:
            if obj.mode != 'OBJECT':
                if obj.mode not in ['POSE', 'WEIGHT_PAINT'] or obj == locked_active_obj:
                    locked_objs.append(obj)
                    locked_objs_mode = obj.mode


        if self.toggle:
            # check if slot can be toggled off.
            for obj in qcd_laycol.collection.objects:
                if obj.mode != 'OBJECT':
                    if obj.mode not in ['POSE', 'WEIGHT_PAINT'] or obj == locked_active_obj:
                        return {'CANCELLED'}

            # get current child exclusion state
            child_exclusion = []

            def get_child_exclusion(layer_collection):
                child_exclusion.append([layer_collection, layer_collection.exclude])

            apply_to_children(qcd_laycol, get_child_exclusion)

            # toggle exclusion of qcd_laycol
            qcd_laycol.exclude = not qcd_laycol.exclude

            # set correct state for all children
            for laycol in child_exclusion:
                laycol[0].exclude = laycol[1]

            # restore locked objects back to their original mode
            # needed because of exclude child updates
            if locked_objs:
                context.view_layer.objects.active = locked_active_obj
                bpy.ops.object.mode_set(mode=locked_objs_mode)

            # set layer as active layer collection
            context.view_layer.active_layer_collection = qcd_laycol

        else:
            # exclude all collections
            for laycol in layer_collections.values():
                if laycol["name"] != qcd_laycol.name:
                    # prevent exclusion if locked objects in this collection
                    if set(locked_objs).isdisjoint(laycol["ptr"].collection.objects):
                        laycol["ptr"].exclude = True
                    else:
                        laycol["ptr"].exclude = False

            # un-exclude target collection
            qcd_laycol.exclude = False

            # exclude all children
            def exclude_all_children(layer_collection):
                # prevent exclusion if locked objects in this collection
                if set(locked_objs).isdisjoint(layer_collection.collection.objects):
                    layer_collection.exclude = True
                else:
                    layer_collection.exclude = False

            apply_to_children(qcd_laycol, exclude_all_children)

            # restore locked objects back to their original mode
            # needed because of exclude child updates
            if locked_objs:
                context.view_layer.objects.active = locked_active_obj
                bpy.ops.object.mode_set(mode=locked_objs_mode)

            # set layer as active layer collection
            context.view_layer.active_layer_collection = qcd_laycol


        # update header UI
        update_qcd_header()

        view_layer = context.view_layer.name
        if view_layer in rto_history["exclude"]:
            del rto_history["exclude"][view_layer]
        if view_layer in rto_history["exclude_all"]:
            del rto_history["exclude_all"][view_layer]


        return {'FINISHED'}


class RenumerateQCDSlots(Operator):
    bl_label = "Renumber QCD Slots"
    bl_description = (
        "Renumber QCD slots.\n"
        "  * LMB - Renumber starting from the slot designated 1.\n"
        "  * Alt+LMB - Renumber from the beginning"
        )
    bl_idname = "view3d.renumerate_qcd_slots"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global qcd_slots

        modifiers = get_modifiers(event)

        if modifiers == {'alt'}:
            qcd_slots.renumerate(beginning=True)

        else:
            qcd_slots.renumerate()

        update_property_group(context)

        return {'FINISHED'}
