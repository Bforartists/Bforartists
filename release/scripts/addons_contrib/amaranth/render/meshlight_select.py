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
                ob.select = True
                context.scene.objects.active = ob

        if not context.selected_objects and not context.scene.objects.active:
            self.report({"INFO"}, "No meshlights to select")

        return {"FINISHED"}


def button_select_meshlights(self, context):
    if utils.cycles_exists() and utils.cycles_active(context):
        self.layout.operator('object.select_meshlights', icon="LAMP_SUN")


def register():
    bpy.utils.register_class(AMTH_OBJECT_OT_select_meshlights)
    bpy.types.VIEW3D_MT_select_object.append(button_select_meshlights)


def unregister():
    bpy.utils.unregister_class(AMTH_OBJECT_OT_select_meshlights)
    bpy.types.VIEW3D_MT_select_object.remove(button_select_meshlights)
