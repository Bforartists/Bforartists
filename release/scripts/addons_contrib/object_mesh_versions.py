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
    "version": (1, 4, 4),
    "blender": (2, 7, 0),
    "location": "View3D > Properties",
    "warning": "",
    "wiki_url": "https://github.com/kostex/blenderscripts/",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object"}


class KTX_MeshInit(bpy.types.Operator):
    bl_label = "Initialise Mesh Versioning"
    bl_idname = "ktx.meshversions_init"
    bl_description = "Initialise the current object to support versioning"

    def execute(self, context):
        unique_id = str(time.time())
        context.object.data.ktx_mesh_id = context.object.ktx_object_id = unique_id
        return {'FINISHED'}


class KTX_MeshSelect(bpy.types.Operator):
    bl_label = "Select Mesh"
    bl_idname = "ktx.meshversions_select"
    bl_description = "Link the selected mesh to the current object"

    m_index = StringProperty()

    def execute(self, context):
        c_mode = bpy.context.object.mode
        if c_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        obj = context.object
        obj.data = bpy.data.meshes[self.m_index]
        bpy.ops.object.mode_set(mode=c_mode)
        return {'FINISHED'}


class KTX_MeshRemove(bpy.types.Operator):
    bl_label = "Remove Mesh"
    bl_idname = "ktx.meshversions_remove"
    bl_description = "Remove/Delete the selected mesh"

    m_index = StringProperty()

    def execute(self, context):
        bpy.data.meshes.remove(bpy.data.meshes[self.m_index])
        return {'FINISHED'}


class KTX_Cleanup(bpy.types.Operator):
    bl_label = "Cleanup Mode"
    bl_idname = "ktx.cleanup"
    bl_description = "Cleanup Mode"

    def execute(self, context):
        for o in bpy.data.objects:
            o.select = False
        context.scene.objects.active = None
        return {'FINISHED'}


class KTX_MeshCreate(bpy.types.Operator):
    bl_label = "Create Mesh Version"
    bl_idname = "ktx.meshversions_create"
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


class KTX_Mesh_Versions(bpy.types.Panel):
    bl_label = "KTX Mesh Versions"
    bl_idname = "ktx.meshversions"
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
                        row.operator("ktx.meshversions_create")
                        box = layout.box()
                        box.scale_y = 0.65
                        box.label("Currently active mesh: " + obj.data.name)
                        for m in bpy.data.meshes:
                            if m.ktx_mesh_id == obj.ktx_object_id:
                                mesh_name = m.name
                                row = box.row(align=True)
                                row.operator("ktx.meshversions_select", text="", icon='RIGHTARROW').m_index = mesh_name
                                row.prop(m, "name", text="", icon='MESH_DATA')
                                if m.users == 0:
                                    row.operator("ktx.meshversions_remove", text="", icon="X").m_index = mesh_name
                                icon = 'PINNED' if m.use_fake_user else 'UNPINNED'
                                row.prop(m, "use_fake_user", text="", icon=icon)
                        box.label()
                        row = layout.row(align=True)
                        row.operator("ktx.cleanup", text="Cleanup Mode")
                    else:
                        layout.operator("ktx.meshversions_init")
                else:
                    layout.label("Select a Mesh Object")
                    layout.operator("ktx.cleanup", text="Cleanup Mode")

            else:
                layout.label('All Meshes (Cleanup/Pin):')
                box = layout.box()
                box.scale_y = 0.65
                for m in bpy.data.meshes:
                    mesh_name = m.name
                    row = box.row(align=True)
                    row.prop(m, "name", text="", icon='MESH_DATA')
                    if m.users == 0:
                        row.operator("ktx.meshversions_remove", text="", icon="X").m_index = mesh_name
                    icon = 'PINNED' if m.use_fake_user else 'UNPINNED'
                    row.prop(m, "use_fake_user", text="", icon=icon)
                box.label()
        else:
            layout.label("No Meshes Exist")


def register():
    bpy.types.Object.ktx_object_id = bpy.props.StringProperty(name="KTX Object ID", description="Unique ID to 'link' one object to multiple meshes")
    bpy.types.Mesh.ktx_mesh_id = bpy.props.StringProperty(name="KTX Mesh ID", description="Unique ID to 'link' multiple meshes to one object")
    bpy.types.Scene.ktx_defpin = bpy.props.BoolProperty(name="Auto Pinning", description="When creating a new version, set pinning to ON automatically (FAKE_USER=TRUE)", default=False)
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Mesh.ktx_mesh_id
    del bpy.types.Object.ktx_object_id
    del bpy.types.Scene.ktx_defpin


if __name__ == "__main__":
    register()
