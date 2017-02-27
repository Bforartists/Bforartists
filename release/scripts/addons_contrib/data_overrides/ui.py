### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>

import bpy, os
from bpy.types import Operator, Panel, UIList
from bpy.props import *

from data_overrides.util import *
from data_overrides.override import *


'''
def id_data_children(id_data):
    if isinstance(id_data, bpy.types.Object):
        if id_data.dupli_type == 'GROUP' and id_data.dupli_group:
            yield id_data.dupli_group
    elif isinstance(id_data, bpy.types.Group):
        for ob in id_data.objects:
            yield ob


def template_id_overrides(layout, context, overrides, id_data, max_level):
    split = layout.split(0.05)

    col = split.column()
    icon = 'DISCLOSURE_TRI_DOWN' if overrides.show_expanded else 'DISCLOSURE_TRI_RIGHT'
    col.prop(overrides, "show_expanded", text="", icon=icon, icon_only=True, emboss=False)

    col = split.column()

    for data, override_type in id_override_targets(id_data):
        col.label(data.path_from_id())

    if max_level <= 0 or max_level > 1:
        for id_child in id_data_children(id_data):
            template_id_overrides(col, context, overrides, id_child, max_level-1)


def template_overrides(layout, context, localroot, max_level=0):
    overrides = localroot.overrides
    for id_child in id_data_children(localroot):
        template_id_overrides(layout, context, overrides, id_child, max_level)

class OBJECT_PT_SimulationOverrides(Panel):
    """Simulation Overrides"""
    bl_label = "Simulation Overrides"
    bl_idname = "OBJECT_PT_SimulationOverrides"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        ob = context.object

        box = layout.box()
        template_overrides(box, context, ob)
'''


class SCENE_OT_Override_Add(Operator):
    """Add Datablock Override"""
    bl_idname = "scene.override_add"
    bl_label = "Add Override"
    bl_property = "id_block"

    def id_block_items(self, context):
        return [id_data_enum_item(id_data) for id_data in bpy.data.objects]

    id_block = EnumProperty(name="ID", description="ID datablock for which to add overrides", items=id_block_items)

    def invoke(self, context, evemt):
        context.window_manager.invoke_search_popup(self)
        return {'CANCELLED'}

    def execute(self, context):
        scene = context.scene

        id_data = id_data_from_enum(self.id_block)
        add_override(scene, id_data)
        
        return {'FINISHED'}


class SCENE_OT_Override_AddCustomProperty(Operator):
    """Add Custom Property Override"""
    bl_idname = "scene.override_add_custom_property"
    bl_label = "Add Custom Property Override"
    bl_options = {'REGISTER', 'UNDO'}

    propname = StringProperty(name="Property", description="Path to the custom property to override")

    @classmethod
    def poll(cls, context):
        if not context.scene:
            return False
        if not hasattr(context, "id_data_override"):
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    def execute(self, context):
        print("AAAAAA")
        scene = context.scene
        override = context.id_data_override

        if not self.propname:
            print("no propname?")
            return {'CANCELLED'}

        print("adding %s" % self.propname)
        override.add_custom_property(self.propname)
        return {'FINISHED'}

def template_overrides(layout, context, scene):
    for override in scene.overrides:
        override.draw(context, layout)


class SCENE_PT_Overrides(Panel):
    """Scene Overrides"""
    bl_label = "Scene Overrides"
    bl_idname = "SCENE_PT_Overrides"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("scene.override_add")

        box = layout.box()
        template_overrides(box, context, scene)


# ======================================================================================


classes = (
#    OBJECT_PT_SimulationOverrides,
    SCENE_OT_Override_Add,
    SCENE_OT_Override_AddCustomProperty,
    SCENE_PT_Overrides,
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
