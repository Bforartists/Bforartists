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

from .internals import (
    layer_collections,
    qcd_slots,
    update_property_group,
    get_modifiers,
)

from .operators import rto_history

move_triggered = False
move_selection = []
move_active = None

def get_move_selection():
    global move_selection

    if not move_selection:
        move_selection = bpy.context.selected_objects

    return move_selection

def get_move_active():
    global move_active
    global move_selection

    if not move_active:
        move_active = bpy.context.view_layer.objects.active

    if move_active not in get_move_selection():
        move_active = None

    if move_active:
        try:
            move_active.name

        except:
            move_active = None
            move_selection = []

            # update header widget
            cm = bpy.context.scene.collection_manager
            cm.update_header.clear()
            new_update_header = cm.update_header.add()
            new_update_header.name = "updated"

    return move_active

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
        global move_triggered

        selected_objects = get_move_selection()
        active_object = get_move_active()
        move_triggered = True
        qcd_laycol = qcd_slots.get_name(self.slot)

        if qcd_laycol:
            qcd_laycol = layer_collections[qcd_laycol]["ptr"]

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


        if not context.active_object:
            try:
                context.view_layer.objects.active = active_object
            except:
                pass

        # update header UI
        cm = bpy.context.scene.collection_manager
        cm.update_header.clear()
        new_update_header = cm.update_header.add()
        new_update_header.name = "updated"

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
            "  * Shift-Click to toggle QCD slot.\n"
            "  * Ctrl-Click to move objects to QCD slot.\n"
            "  * Ctrl-Shift-Click to toggle objects' slot"
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
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()
    toggle: BoolProperty()

    def execute(self, context):
        global qcd_slots
        global layer_collections
        global rto_history

        qcd_laycol = qcd_slots.get_name(self.slot)

        if qcd_laycol:
            qcd_laycol = layer_collections[qcd_laycol]["ptr"]

        else:
            return {'CANCELLED'}

        if self.toggle:
            # get current child exclusion state
            child_exclusion = []

            laycol_iter_list = [qcd_laycol.children]
            while len(laycol_iter_list) > 0:
                new_laycol_iter_list = []
                for laycol_iter in laycol_iter_list:
                    for layer_collection in laycol_iter:
                        child_exclusion.append([layer_collection, layer_collection.exclude])
                        if len(layer_collection.children) > 0:
                            new_laycol_iter_list.append(layer_collection.children)

                laycol_iter_list = new_laycol_iter_list

            # toggle exclusion of qcd_laycol
            qcd_laycol.exclude = not qcd_laycol.exclude

            # set correct state for all children
            for laycol in child_exclusion:
                laycol[0].exclude = laycol[1]

            # set layer as active layer collection
            context.view_layer.active_layer_collection = qcd_laycol

        else:
            for laycol in layer_collections.values():
                if laycol["name"] != qcd_laycol.name:
                    laycol["ptr"].exclude = True

            qcd_laycol.exclude = False

            # exclude all children
            laycol_iter_list = [qcd_laycol.children]
            while len(laycol_iter_list) > 0:
                new_laycol_iter_list = []
                for laycol_iter in laycol_iter_list:
                    for layer_collection in laycol_iter:
                        layer_collection.exclude = True
                        if len(layer_collection.children) > 0:
                            new_laycol_iter_list.append(layer_collection.children)

                laycol_iter_list = new_laycol_iter_list

            # set layer as active layer collection
            context.view_layer.active_layer_collection = qcd_laycol

        # update header UI
        cm = bpy.context.scene.collection_manager
        cm.update_header.clear()
        new_update_header = cm.update_header.add()
        new_update_header.name = "updated"

        view_layer = context.view_layer.name
        if view_layer in rto_history["exclude"]:
            del rto_history["exclude"][view_layer]
        if view_layer in rto_history["exclude_all"]:
            del rto_history["exclude_all"][view_layer]

        return {'FINISHED'}


class RenumerateQCDSlots(Operator):
    '''Re-numerate QCD slots\n  * Ctrl-Click to include collections marked by the user as non QCD slots'''
    bl_label = "Re-numerate QCD Slots"
    bl_idname = "view3d.renumerate_qcd_slots"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global qcd_slots

        qcd_slots.clear()

        if event.ctrl:
            qcd_slots.overrides.clear()

        update_property_group(context, renumerate=True)

        return {'FINISHED'}
