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

bl_info = {
    "name": "Face info / select by type",
    "author": "CoDEmanX",
    "version": (0, 0, 3),
    "blender": (2, 62, 0),
    "location": "Properties > Object data > Face info / select",
    "description": "Displays triangle, quad and ngon count of the active object. Allows to select faces by these types.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Mesh/Face_Info_Select",
    "tracker_url": "https://developer.blender.org/T31926",
    "support": 'TESTING',
    "category": "Mesh"
}

# Written by CoDEmanX for frivus


import bpy
from bpy.props import EnumProperty

class DATA_OT_facetype_select(bpy.types.Operator):
    """Select all faces of a certain type"""
    bl_idname = "data.facetype_select"
    bl_label = "Select by face type"
    bl_options = {'REGISTER', 'UNDO'}

    face_type = EnumProperty(name="Select faces:",
                             items = (("3","Triangles","Faces made up of 3 vertices"),
                                      ("4","Quads","Faces made up of 4 vertices"),
                                      ("5","Ngons","Faces made up of 5 and more vertices")),
                             default = "5")
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        context.tool_settings.mesh_select_mode=(False, False, True)

        if self.face_type == "3":
            bpy.ops.mesh.select_face_by_sides(number=3, type='EQUAL')
        elif self.face_type == "4":
            bpy.ops.mesh.select_face_by_sides(number=4, type='EQUAL')
        else:
            bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER')

        return {'FINISHED'}


class DATA_PT_info_panel(bpy.types.Panel):
    """Creates a face info / select panel in the Object properties window"""
    bl_label = "Face info / select"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout

        ob = context.active_object

        info_str = ""
        tris = quads = ngons = 0

        for p in ob.data.polygons:
            count = p.loop_total
            if count == 3:
                tris += 1
            elif count == 4:
                quads += 1
            else:
                ngons += 1

        info_str = "  Ngons: %i  Quads: %i  Tris: %i" % (ngons, quads, tris)

        col = layout.column()
        col.label(info_str, icon='MESH_DATA')

        col = layout.column()
        col.label("Select faces by type:")

        row = layout.row()
        row.operator("data.facetype_select", text="Ngons").face_type = "5"
        row.operator("data.facetype_select", text="Quads").face_type = "4"
        row.operator("data.facetype_select", text="Tris").face_type = "3"


def register():
    bpy.utils.register_class(DATA_PT_info_panel)
    bpy.utils.register_class(DATA_OT_facetype_select)


def unregister():
    bpy.utils.unregister_class(DATA_PT_info_panel)
    bpy.utils.unregister_class(DATA_OT_facetype_select)


if __name__ == "__main__":
    register()
