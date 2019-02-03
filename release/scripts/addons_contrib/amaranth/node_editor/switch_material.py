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
Material Selector

Quickly switch materials in the active mesh without going to the Properties editor

Based on 'Afeitadora's work on Elysiun
http://www.elysiun.com/forum/showthread.php?290097-Dynamic-Object-Dropdown-List&p=2361851#post2361851

"""

import bpy

def ui_node_editor_material_select(self, context):

    act_ob = context.active_object

    if act_ob and context.active_object.type in {'MESH', 'CURVE', 'SURFACE', 'META'} and \
        context.space_data.tree_type == 'ShaderNodeTree' and \
        context.space_data.shader_type == 'OBJECT':

        if act_ob.active_material:
            mat_name = act_ob.active_material.name
        else:
            mat_name = "No Material"

        self.layout.operator_menu_enum("material.menu_select",
                                       "material_select",
                                        text=mat_name,
                                       icon="MATERIAL")

class AMNodeEditorMaterialSelect(bpy.types.Operator):
    bl_idname = "material.menu_select"
    bl_label = "Select Material"
    bl_description = "Switch to another material in this mesh"

    def avail_materials(self,context):
        items = [(str(i),x.name,x.name, "MATERIAL", i) for i,x in enumerate(bpy.context.active_object.material_slots)]
        return items
    material_select: bpy.props.EnumProperty(items = avail_materials, name = "Available Materials")

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self,context):
        bpy.context.active_object.active_material_index = int(self.material_select)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(AMNodeEditorMaterialSelect)
    bpy.types.NODE_HT_header.append(ui_node_editor_material_select)

def unregister():
    bpy.utils.unregister_class(AMNodeEditorMaterialSelect)
    bpy.types.NODE_HT_header.remove(ui_node_editor_material_select)
