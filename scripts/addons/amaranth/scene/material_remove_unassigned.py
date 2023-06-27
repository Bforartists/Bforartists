# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy


# FEATURE: Delete Materials not assigned to any verts
class AMTH_OBJECT_OT_material_remove_unassigned(bpy.types.Operator):

    """Remove materials not assigned to any vertex"""
    bl_idname = "object.amaranth_object_material_remove_unassigned"
    bl_label = "Remove Unassigned Materials"

    @classmethod
    def poll(cls, context):
        return context.active_object.material_slots

    def execute(self, context):

        scene = context.scene
        act_ob = context.active_object
        count = len(act_ob.material_slots)
        materials_removed = []
        act_ob.active_material_index = 0
        is_visible = True

        if act_ob not in context.visible_objects:
            is_visible = False
            n = -1
            for lay in act_ob.layers:
                n += 1
                if lay:
                    break

            scene.layers[n] = True

        for slot in act_ob.material_slots:
            count -= 1

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            act_ob.active_material_index = count
            bpy.ops.object.material_slot_select()

            if act_ob.data.total_vert_sel == 0 or \
                (len(act_ob.material_slots) == 1 and not
                    act_ob.material_slots[0].material):
                materials_removed.append(
                    "%s" %
                    act_ob.active_material.name if act_ob.active_material else "Empty")
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.material_slot_remove()
            else:
                pass

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")

        if materials_removed:
            print(
                "\n* Removed %s Unassigned Materials \n" %
                len(materials_removed))

            count_mr = 0

            for mr in materials_removed:
                count_mr += 1
                print(
                    "%0.2d. %s" %
                    (count_mr, materials_removed[count_mr - 1]))

            print("\n")
            self.report({"INFO"}, "Removed %s Unassigned Materials" %
                        len(materials_removed))

        if not is_visible:
            scene.layers[n] = False

        return {"FINISHED"}


def ui_material_remove_unassigned(self, context):
    self.layout.operator(
        AMTH_OBJECT_OT_material_remove_unassigned.bl_idname,
        icon="X")

# // FEATURE: Delete Materials not assigned to any verts


def register():
    bpy.utils.register_class(AMTH_OBJECT_OT_material_remove_unassigned)
    bpy.types.MATERIAL_MT_context_menu.append(ui_material_remove_unassigned)


def unregister():
    bpy.utils.unregister_class(AMTH_OBJECT_OT_material_remove_unassigned)
    bpy.types.MATERIAL_MT_context_menu.remove(ui_material_remove_unassigned)
