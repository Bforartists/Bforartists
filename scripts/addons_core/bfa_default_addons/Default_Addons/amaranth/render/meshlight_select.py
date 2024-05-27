# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Select Meshlights

Select all the meshes that emit light. On the header of the 3D View, top
of the select menu.
"""

import bpy
from amaranth import utils


class AMTH_OBJECT_OT_select_meshlights(bpy.types.Operator):

    """Select light emitting meshes"""
    bl_idname = "object.select_meshlights"
    bl_label = "Select Meshlights"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "CYCLES"

    def execute(self, context):
        # Deselect everything first
        bpy.ops.object.select_all(action="DESELECT")

        for ob in context.scene.objects:
            if utils.cycles_is_emission(context, ob):
                ob.select_set(True)
                context.view_layer.objects.active = ob

        if not context.selected_objects and not context.view_layer.objects.active:
            self.report({"INFO"}, "No meshlights to select")

        return {"FINISHED"}


def button_select_meshlights(self, context):
    if utils.cycles_exists() and utils.cycles_active(context):
        self.layout.operator('object.select_meshlights', icon="LIGHT_SUN")


def register():
    bpy.utils.register_class(AMTH_OBJECT_OT_select_meshlights)
    bpy.types.VIEW3D_MT_select_object.append(button_select_meshlights)


def unregister():
    bpy.utils.unregister_class(AMTH_OBJECT_OT_select_meshlights)
    bpy.types.VIEW3D_MT_select_object.remove(button_select_meshlights)
