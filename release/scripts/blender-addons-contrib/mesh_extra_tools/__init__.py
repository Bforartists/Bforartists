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
# Contributed to by
# meta-androcto #

bl_info = {
    "name": "Extra Tools",
    "author": "various",
    "version": (0, 1),
    "blender": (2, 71, 0),
    "location": "View3D > Toolshelf > Tools Tab & Specials (W-key)",
    "description": "Add extra mesh edit tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/create/?project=3&type=Bug",
    "category": "Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(mesh_bump)
    imp.reload(face_inset_fillet)
    imp.reload(mesh_bevel_witold)
    imp.reload(mesh_filletplus)
    imp.reload(mesh_normal_smooth)
    imp.reload(mesh_polyredux)
    imp.reload(mesh_vertex_chamfer)
    imp.reload(mesh_mextrude_plus)

else:
    from . import mesh_bump
    from . import face_inset_fillet
    from . import mesh_bevel_witold
    from . import mesh_filletplus
    from . import mesh_normal_smooth
    from . import mesh_polyredux
    from . import mesh_vertex_chamfer
    from . import mesh_mextrude_plus

import bpy

class VIEW3D_MT_edit_mesh_extras(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "VIEW3D_MT_edit_mesh_extras"
    bl_label = "Extra Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("faceinfillet.op0_id",
            text="Face Inset Fillet")
        layout.operator("fillet.op0_id",
            text="Edge Fillet Plus")
        layout.operator("object.mextrude",
            text="Multi Extrude")
        layout.operator("mesh.bump",
            text="Inset Extrude Bump")
        layout.operator("mesh.mbevel",
            text="Bevel Selected")
        layout.operator("mesh.vertex_chamfer",
            text="Vertex Chamfer")
        layout.operator("mesh.polyredux",
            text="Poly Redux")
        layout.operator("normal.smooth",
            text="Normal Smooth")


class ExtrasPanel(bpy.types.Panel):
    bl_label = 'Mesh Extra Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'mesh_edit'
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.split(0.80)
        row.operator('faceinfillet.op0_id', text = 'Face Inset Fillet', icon = 'PLUGIN')
        row.operator('help.face_inset', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('fillet.op0_id', text = 'Edge Fillet plus', icon = 'PLUGIN')
        row.operator('help.edge_fillet', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('object.mextrude', text = 'Multi Face Extrude', icon = 'PLUGIN')
        row.operator('help.mextrude', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('mesh.bump', text = 'Inset Bump', icon = 'PLUGIN')
        row.operator('help.bump', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('mesh.mbevel', text = 'Bevel Selected', icon = 'PLUGIN')
        row.operator('help.edge_bevel', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('mesh.vertex_chamfer', text = 'Vertex Chamfer' , icon = 'PLUGIN')
        row.operator('help.vertexchamfer', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('mesh.polyredux', text = 'Poly Redux', icon = 'PLUGIN')
        row.operator('help.polyredux', text = '', icon = 'INFO')
        row = layout.split(0.80)
        row.operator('normal.smooth', text = 'Normal Smooth', icon = 'PLUGIN')
        row.operator('help.normal_smooth', text = '', icon = 'INFO')
        row = layout.split(0.50)
        row.operator('mesh.flip_normals', text = 'Normals Flip')
        row.operator('mesh.remove_doubles', text = 'Remove Doubles')


# Multi Extrude Panel

class ExtrudePanel(bpy.types.Panel):
    bl_label = 'Multi Extrude Plus'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.split(0.80)
        row.operator('object.mextrude', text = 'Multi Face Extrude', icon = 'PLUGIN')
        row.operator('help.mextrude', text = '', icon = 'INFO')

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu('VIEW3D_MT_edit_mesh_extras', icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
