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

import bpy
from bpy.types import Panel
from bpy.props import StringProperty


bl_info = {
    "name": "KTX Selectbuffer",
    "description": "Enable boolean operations on selections",
    "author": "Roel Koster, @koelooptiemanna, irc:kostex",
    "version": (1, 4, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Properties",
    "warning": "",
    "wiki_url": "https://github.com/kostex/blenderscripts/",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "3D View"}


class Oldbuffer:
    data = []


class KTX_Selectbuffer_Mutate(bpy.types.Operator):
    bl_label = "select buffer mutate"
    bl_idname = "ktx.selectbuffer_mutate"
    bl_description = ("A.union(B) elements from both A and B\n"
                      "A.difference(B) elements in A but not in B\n"
                      "A.symmetric_difference(B) elements in either A or B but not both\n"
                      "A.intersection(B) elements common to A and B")

    operation : StringProperty()

    def execute(self, context):
        old_buffer = bpy.context.scene.ktx_selectbuffer
        emode = bpy.context.tool_settings.mesh_select_mode

        c_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        if emode[0]:
            all_vefs = bpy.context.object.data.vertices
        elif emode[1]:
            all_vefs = bpy.context.object.data.edges
        elif emode[2]:
            all_vefs = bpy.context.object.data.polygons

        selected_vefs = [vef for vef in all_vefs if vef.select]
        selected_vefs_buffer = []
        for vef in selected_vefs:
            selected_vefs_buffer.append(vef.index)
        if self.operation == 'union':
            resulting_vefs = set(old_buffer.data).union(selected_vefs_buffer)
        elif self.operation == 'difference':
            resulting_vefs = set(old_buffer.data).difference(selected_vefs_buffer)
        elif self.operation == 'sym_difference':
            resulting_vefs = set(old_buffer.data).symmetric_difference(selected_vefs_buffer)
        elif self.operation == 'intersection':
            resulting_vefs = set(old_buffer.data).intersection(selected_vefs_buffer)
        elif self.operation == 'set':
            resulting_vefs = selected_vefs_buffer
        elif self.operation == 'clear':
            resulting_vefs = []
        old_buffer.data = resulting_vefs
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for vef in resulting_vefs:
            all_vefs[vef].select = True
        bpy.ops.object.mode_set(mode=c_mode)

        bpy.ops.ed.undo_push()

        return {'FINISHED'}


class KTX_Selectbuffer(bpy.types.Panel):
    bl_label = "KTX Selectbuffer"
    bl_idname = "ktx.selectbuffer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        obj = bpy.context.object
        layout = self.layout
        row = layout.row()
        col = row.column()
        if obj == None:
            col.label(text='Select/Create something first')
        else:
            if obj.type == 'MESH':
                c_mode = bpy.context.object.mode
                if c_mode == 'EDIT':
                    col.operator("ktx.selectbuffer_mutate", text="Set").operation = 'set'
                    col.operator("ktx.selectbuffer_mutate", text="Clear").operation = 'clear'
                    col.operator("ktx.selectbuffer_mutate", text="Union").operation = 'union'
                    col.operator("ktx.selectbuffer_mutate", text="Difference").operation = 'difference'
                    col.operator("ktx.selectbuffer_mutate", text="Symmetric Difference").operation = 'sym_difference'
                    col.operator("ktx.selectbuffer_mutate", text="Intersection").operation = 'intersection'
                else:
                    col.label(text='Enter EDIT Mode to use')
            else:
                col.label(text='Select a Mesh Object')


classes = (
    KTX_Selectbuffer,
    KTX_Selectbuffer_Mutate
)


def register():
    from bpy.utils import register_class

    bpy.types.Scene.ktx_selectbuffer = Oldbuffer

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    del bpy.types.Scene.ktx_selectbuffer

    for cls in classes:
        unregister_class(cls)


if __name__ == "__main__":
    register()
