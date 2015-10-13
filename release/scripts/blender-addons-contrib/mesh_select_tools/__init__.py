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
#  GNU General Public License for more details
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
# ##### END GPL LICENSE BLOCK #####
# menu & updates by meta-androcto #
# contributed to by Macouno, dustractor, liero, CoDEmanX, meta-androcto #

bl_info = {
    "name": "Select Tools",
    "author": "Multiple Authors",
    "version": (0, 3),
    "blender": (2, 64, 0),
    "location": "Editmode Select Menu/Toolshelf Tools Tab",
    "description": "Adds More vert/face/edge select modes.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/create/?project=3&type=Bug",
    "category": "Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(mesh_select_by_direction)
    imp.reload(mesh_select_by_edge_length)
    imp.reload(mesh_select_by_pi)
    imp.reload(mesh_select_by_type)
    imp.reload(mesh_select_connected_faces)
    imp.reload(mesh_select_innermost)
    imp.reload(mesh_index_select)
    imp.reload(mesh_selection_topokit)
    imp.reload(mesh_info_select)
else:
    from . import mesh_select_by_direction
    from . import mesh_select_by_edge_length
    from . import mesh_select_by_pi
    from . import mesh_select_by_type
    from . import mesh_select_connected_faces
    from . import mesh_select_innermost
    from . import mesh_index_select
    from . import mesh_selection_topokit
    from . import mesh_info_select

import bpy, bmesh

class VIEW3D_MT_selectface_edit_mesh_add(bpy.types.Menu):
    # Define the "Mesh_Select_Tools" menu
    bl_idname = "mesh.face_select_tools"
    bl_label = "Select by Face"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Face Select')
        layout.separator()
        layout.operator("data.facetype_select",
            text="Triangles").face_type = "3"
        layout.operator("data.facetype_select",
            text="Quads").face_type = "4"
        layout.operator("data.facetype_select",
            text="Ngons").face_type = "5"
        layout.separator()
        layout.operator("mesh.select_vert_index",
            text="By Face Index")
        layout.operator("mesh.select_by_direction",
            text="By Direction")
        layout.operator("mesh.select_by_pi",
            text="By Pi")
        layout.operator("mesh.select_connected_faces",
            text="By Connected Faces")
        layout.operator("mesh.e2e_efe",
            text="Neighbors by Face")
        layout.operator("mesh.f2f_fvnef",
            text="Neighbors by Vert not Edge")
        layout.operator("mesh.conway",
            text="Conway")

class VIEW3D_MT_selectedge_edit_mesh_add(bpy.types.Menu):
    # Define the "Mesh_Select_Tools" menu
    bl_idname = "mesh.edge_select_tools"
    bl_label = "Select by Edge"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Edge Select')
        layout.separator()
        layout.operator("mesh.select_vert_index",
            text="By Edge Index")
        layout.operator("mesh.select_by_direction",
            text="By Direction")
        layout.operator("mesh.select_by_pi",
            text="By Pi")
        layout.operator("mesh.select_by_edge_length",
            text="By Edge Length")
        layout.separator()
        layout.operator("mesh.e2e_eve",
            text="Neighbors by Vert")
        layout.operator("mesh.e2e_evfe",
            text="Neighbors by Vert + Face")
        layout.operator("mesh.e2e_efnve",
            text="Lateral Neighbors")
        layout.operator("mesh.e2e_evnfe",
            text="Longitudinal Edges")
#        layout.operator("mesh.je",
#            text="only_edge_selection")

class VIEW3D_MT_selectvert_edit_mesh_add(bpy.types.Menu):
    # Define the "Mesh_Select_Tools" menu
    bl_idname = "mesh.vert_select_tools"
    bl_label = "Select by Vert"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Vert Select')
        layout.separator()
        layout.operator("mesh.select_vert_index",
            text="By Vert Index")
        layout.operator("mesh.select_by_direction",
            text="By Direction")
        layout.operator("mesh.select_by_pi",
            text="By Pi")
#        layout.operator("mesh.select_innermost",
#            text="innermost")
        layout.separator()
        layout.operator("mesh.v2v_by_edge",
            text="Neighbors by Edge")
        layout.operator("mesh.e2e_eve",
            text="Neighbors by Vert")
        layout.operator("mesh.e2e_efe",
            text="Neighbors by Face")
        layout.operator("mesh.v2v_facewise",
            text="Neighbors by Face - Edge")
#        layout.operator("mesh.ie",
#            text="inner_edge_selection")

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    if context.tool_settings.mesh_select_mode[2]:
        self.layout.menu("mesh.face_select_tools", icon="PLUGIN")
    if context.tool_settings.mesh_select_mode[1]:
        self.layout.menu("mesh.edge_select_tools", icon="PLUGIN")
    if context.tool_settings.mesh_select_mode[0]:
        self.layout.menu("mesh.vert_select_tools", icon="PLUGIN")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_MT_select_edit_mesh.append(menu_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_func)

if __name__ == "__main__":
	register()
