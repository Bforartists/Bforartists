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
import time
from datetime import datetime
from bpy.types import Menu, Panel
from bpy.props import StringProperty, BoolProperty


bl_info = {
    "name": "KTX Mesh Versions",
    "description": "Keep multiple mesh versions of an object",
    "author": "Roel Koster, @koelooptiemanna, irc:kostex",
    "version": (1, 5, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Properties",
    "warning": "",
    "wiki_url": "https://github.com/kostex/blenderscripts/",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object"}


class KTXMESHVERSIONS_OT_Init(bpy.types.Operator):
    bl_label = "Initialise Mesh Versioning"
    bl_idname = "ktxmeshversions.init"
    bl_description = "Initialise the current object to support versioning"

    def execute(self, context):
        unique_id = str(time.time())
        context.object.data.ktx_mesh_id = context.object.ktx_object_id = unique_id
        return {'FINISHED'}


class KTXMESHVERSIONS_OT_Select(bpy.types.Operator):
    bl_label = "Select Mesh"
    bl_idname = "ktxmeshversions.select"
    bl_description = "Link the selected mesh to the current object"

    m_index : StringProperty()

    def execute(self, context):
        c_mode = bpy.context.object.mode
        if c_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        obj = context.object
        obj.data = bpy.data.meshes[self.m_index]
        bpy.ops.object.mode_set(mode=c_mode)
        return {'FINISHED'}


class KTXMESHVERSIONS_OT_Remove(bpy.types.Operator):
    bl_label = "Remove Mesh"
    bl_idname = "ktxmeshversions.remove"
    bl_description = "Remove/Delete the selected mesh"

    m_index : StringProperty()

    def execute(self, context):
        bpy.data.meshes.remove(bpy.data.meshes[self.m_index])
        return {'FINISHED'}


class KTXMESHVERSIONS_OT_Cleanup(bpy.types.Operator):
    bl_label = "Cleanup Mode"
    bl_idname = "ktxmeshversions.cleanup"
    bl_description = "Cleanup Mode"

    def execute(self, context):
        for o in bpy.data.objects:
            o.select = False
        context.scene.objects.active = None
        return {'FINISHED'}


class KTXMESHVERSIONS_OT_Create(bpy.types.Operator):
    bl_label = "Create Mesh Version"
    bl_idname = "ktxmeshversions.create"
    bl_description = ("Create a copy of the mesh data of the current object\n"
                      "and set it as active")

    def execute(self, context):
        defpin = bpy.context.scene.ktx_defpin
        obj = context.object
        if obj.type == 'MESH':
            c_mode = bpy.context.object.mode
            me = obj.data
            if c_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            new_mesh = me.copy()
            obj.data = new_mesh
            obj.data.use_fake_user = defpin
            bpy.ops.object.mode_set(mode=c_mode)
        return {'FINISHED'}


class KTXMESHVERSIONS_PT_mainPanel(bpy.types.Panel):
    bl_label = "KTX Mesh Versions"
    bl_idname = "KTXMESHVERSIONS_PT_mainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scene = context.scene
        obj = context.object
        layout = self.layout

        meshes_exist = bool(bpy.data.meshes.items() != [])
        if meshes_exist:
            if obj != None:
                if obj.type == 'MESH':
                    if obj.ktx_object_id != '' and (obj.data.ktx_mesh_id == obj.ktx_object_id):
                        icon = 'PINNED' if scene.ktx_defpin else 'UNPINNED'
                        row = layout.row(align=True)
                        row.prop(scene, "ktx_defpin", text="", icon=icon)
                        row.operator("ktxmeshversions.create")
                        box = layout.box()
                        box.scale_y = 1.0
                        box.label(text="Currently active mesh: " + obj.data.name)
                        for m in bpy.data.meshes:
                            if m.ktx_mesh_id == obj.ktx_object_id:
                                mesh_name = m.name
                                row = box.row(align=True)
                                row.operator("ktxmeshversions.select", text="", icon='RIGHTARROW').m_index = mesh_name
                                row.prop(m, "name", text="", icon='MESH_DATA')
                                if m.users == 0:
                                    row.operator("ktxmeshversions.remove", text="", icon="X").m_index = mesh_name
                                icon = 'PINNED' if m.use_fake_user else 'UNPINNED'
                                row.prop(m, "use_fake_user", text="", icon=icon)
                        box.label(text="")
                        row = layout.row(align=True)
                        row.operator("ktxmeshversions.cleanup", text="Cleanup Mode")
                    else:
                        layout.operator("ktxmeshversions.init")
                else:
                    layout.label(text="Select a Mesh Object")
                    layout.operator("ktxmeshversions.cleanup", text="Cleanup Mode")

            else:
                layout.label(text="All Meshes (Cleanup/Pin):")
                box = layout.box()
                box.scale_y = 1.0
                for m in bpy.data.meshes:
                    mesh_name = m.name
                    row = box.row(align=True)
                    row.prop(m, "name", text="", icon='MESH_DATA')
                    if m.users == 0:
                        row.operator("ktxmeshversions.remove", text="", icon="X").m_index = mesh_name
                    icon = 'PINNED' if m.use_fake_user else 'UNPINNED'
                    row.prop(m, "use_fake_user", text="", icon=icon)
                box.label(text="")
        else:
            layout.label(text="No Meshes Exist")


classes = (
    KTXMESHVERSIONS_PT_mainPanel,
    KTXMESHVERSIONS_OT_Init,
    KTXMESHVERSIONS_OT_Create,
    KTXMESHVERSIONS_OT_Remove,
    KTXMESHVERSIONS_OT_Select,
    KTXMESHVERSIONS_OT_Cleanup
)


def register():
    from bpy.utils import register_class
    
    bpy.types.Object.ktx_object_id = bpy.props.StringProperty(name="KTX Object ID", description="Unique ID to 'link' one object to multiple meshes")
    bpy.types.Mesh.ktx_mesh_id = bpy.props.StringProperty(name="KTX Mesh ID", description="Unique ID to 'link' multiple meshes to one object")
    bpy.types.Scene.ktx_defpin = bpy.props.BoolProperty(name="Auto Pinning", description="When creating a new version, set pinning to ON automatically (FAKE_USER=TRUE)", default=False)

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    del bpy.types.Mesh.ktx_mesh_id
    del bpy.types.Object.ktx_object_id
    del bpy.types.Scene.ktx_defpin

    for cls in classes:
        unregister_class(cls)


if __name__ == "__main__":
    register()
