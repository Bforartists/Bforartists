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
# meta-androcto,  Hidesato Ikeya, zmj100, luxuy_BlenderCN, TrumanBlending, PKHG, #
# Oscurart, Stanislav Blinov, komi3D, BlenderLab, Paul Marshall (brikbot), metalliandy, #
# macouno, CoDEmanX, dustractor, Liero, #

bl_info = {
    "name": "Edit Tools2",
    "author": "meta-androcto",
    "version": (0, 2, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Toolshelf > Tools & Specials (W-key)",
    "description": "Add extra mesh edit tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Mesh"}

# Import From Folder
from .mesh_select_tools import mesh_select_by_direction
from .mesh_select_tools import mesh_select_by_edge_length
from .mesh_select_tools import mesh_select_by_pi
from .mesh_select_tools import mesh_select_by_type
from .mesh_select_tools import mesh_select_connected_faces
from .mesh_select_tools import mesh_index_select
from .mesh_select_tools import mesh_selection_topokit
from .mesh_select_tools import mesh_info_select

# Import From Files
if "bpy" in locals():
    import importlib
    importlib.reload(face_inset_fillet)
    importlib.reload(mesh_filletplus)
    importlib.reload(mesh_vertex_chamfer)
    importlib.reload(mesh_mextrude_plus)
    importlib.reload(mesh_offset_edges)
    importlib.reload(pkhg_faces)
    importlib.reload(mesh_edge_roundifier)
    importlib.reload(mesh_cut_faces)
    importlib.reload(split_solidify)
    importlib.reload(mesh_to_wall)
    importlib.reload(mesh_edges_length)
    importlib.reload(random_vertices)
    importlib.reload(mesh_fastloop)
    importlib.reload(mesh_edgetools)
    importlib.reload(mesh_pen_tool)
    importlib.reload(vfe_specials)

else:
    from . import face_inset_fillet
    from . import mesh_filletplus
    from . import mesh_vertex_chamfer
    from . import mesh_mextrude_plus
    from . import mesh_offset_edges
    from . import pkhg_faces
    from . import mesh_edge_roundifier
    from . import mesh_cut_faces
    from . import split_solidify
    from . import mesh_to_wall
    from . import mesh_edges_length
    from . import random_vertices
    from . import mesh_fastloop
    from . import mesh_edgetools
    from . import mesh_pen_tool
    from . import vfe_specials

import bpy
from bpy.props import BoolProperty
from bpy_extras import view3d_utils
### ------ MENUS ====== ###


class VIEW3D_MT_edit_mesh_extras(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "VIEW3D_MT_edit_mesh_extras"
    bl_label = "Edit Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        mode = context.tool_settings.mesh_select_mode
        if mode[0]:
            split = layout.split()
            col = split.column()
            col.label(text="Vert")
            col.operator("mesh.vertex_chamfer",
                         text="Vertex Chamfer")
            col.operator("mesh.random_vertices",
                         text="Random Vertices")

            row = split.row(align=True)
            col = split.column()
            col.label(text="Utilities")
            col.operator("object_ot.fastloop",
                         text="Fast loop")
            col.operator('mesh.flip_normals', text='Normals Flip')
            col.operator('mesh.remove_doubles', text='Remove Doubles')
            col.operator('mesh.subdivide', text='Subdivide')
            col.operator('mesh.dissolve_limited', text='Dissolve Limited')

        elif mode[1]:
            split = layout.split()
            col = split.column()
            col.label(text="Edge")
            col.operator("fillet.op0_id",
                         text="Edge Fillet Plus")
            col.operator("mesh.offset_edges",
                         text="Offset Edges")
            col.operator("mesh.edge_roundifier",
                         text="Edge Roundify")
            col.operator("object.mesh_edge_length_set",
                         text="Set Edge Length")
            col.operator("bpt.mesh_to_wall",
                         text="Edge(s) to Wall")
            row = split.row(align=True)
            col = split.column()
            col.label(text="Utilities")
            col.operator("object_ot.fastloop",
                         text="Fast loop")
            col.operator('mesh.flip_normals', text='Normals Flip')
            col.operator('mesh.remove_doubles', text='Remove Doubles')

            col.operator('mesh.subdivide', text='Subdivide')
            col.operator('mesh.dissolve_limited', text='Dissolve Limited')

        elif mode[2]:
            split = layout.split()
            col = split.column()
            col.label(text="Face")
            col.operator("object.mextrude",
                         text="Multi Extrude")
            col.operator("faceinfillet.op0_id",
                         text="Face Inset Fillet")
            col.operator("mesh.add_faces_to_object",
                         text="PKHG Faces")
            col.operator("mesh.ext_cut_faces",
                         text="Cut Faces")
            col.operator("sp_sol.op0_id",
                         text="Split Solidify")

            row = split.row(align=True)
            col = split.column()
            col.label(text="Utilities")
            col.operator("object_ot.fastloop",
                         text="Fast loop")
            col.operator('mesh.flip_normals', text='Normals Flip')
            col.operator('mesh.remove_doubles', text='Remove Doubles')
            col.operator('mesh.subdivide', text='Subdivide')
            col.operator('mesh.dissolve_limited', text='Dissolve Limited')

class EditToolsPanel(bpy.types.Panel):
    bl_label = 'Mesh Edit Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'mesh_edit'
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        VERTDROP = scene.UTVertDrop
        EDGEDROP = scene.UTEdgeDrop
        FACEDROP = scene.UTFaceDrop
        UTILS1DROP = scene.UTUtils1Drop
        view = context.space_data
        toolsettings = context.tool_settings
        layout = self.layout

        # Vert options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
#        row.alignment = 'CENTER'
        row.prop(scene, "UTVertDrop", icon="TRIA_DOWN")
        if not VERTDROP:
            row.menu("mesh.vert_select_tools", icon="RESTRICT_SELECT_OFF", text="")
            row.menu("VIEW3D_MT_Select_Vert", icon="VERTEXSEL", text="")
        if VERTDROP:
            row = col.row(align=True)
            row.label(text="Vert Tools:", icon="VERTEXSEL")
            row = layout.split(0.70)
            row.operator('mesh.vertex_chamfer', text='Chamfer')
            row.operator('help.vertexchamfer', text='?')
            row = layout.split(0.70)
            row.operator('mesh.random_vertices', text='Random Vertices')
            row.operator('help.random_vert', text='?')

        # Edge options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
#        row.alignment = 'CENTER'
        row.prop(scene, "UTEdgeDrop", icon="TRIA_DOWN")
        if not EDGEDROP:
            row.menu("mesh.edge_select_tools", icon="RESTRICT_SELECT_OFF", text="")
            row.menu("VIEW3D_MT_Select_Edge", icon="EDGESEL", text="")
        if EDGEDROP:
            layout = self.layout
            row = layout.row()
            row.label(text="Edge Tools:", icon="EDGESEL")
            row.menu("VIEW3D_MT_edit_mesh_edgetools", icon="GRID")
            row.menu("VIEW3D_MT_edit_mesh_edgelength", icon="SNAP_EDGE", text="")
            row = layout.split(0.70)
            row.operator('fillet.op0_id', text='Fillet plus')
            row.operator('help.edge_fillet', text='?')
            row = layout.split(0.70)
            row.operator('mesh.offset_edges', text='Offset Edges')
            row.operator('help.offset_edges', text='?')
            row = layout.split(0.70)
            row.operator('mesh.edge_roundifier', text='Roundify')
            row.operator('help.roundify', text='?')
            row = layout.split(0.70)
            row.operator('object.mesh_edge_length_set', text='Set Edge Length')
            row.operator('help.roundify', text='?')
            row = layout.split(0.70)
            row.operator('bpt.mesh_to_wall', text='Mesh to wall')
            row.operator('help.wall', text='?')

        # Face options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
#        row.alignment = 'CENTER'
        row.prop(scene, "UTFaceDrop", icon="TRIA_DOWN")

        if not FACEDROP:
            row.menu("mesh.face_select_tools", icon="RESTRICT_SELECT_OFF", text="")
            row.menu("VIEW3D_MT_Select_Face", icon="FACESEL", text="")
        if FACEDROP:
            layout = self.layout
            row = layout.row()
            row.label(text="Face Tools:", icon="FACESEL")
            row = layout.split(0.70)
            row.operator('object.mextrude', text='Multi Extrude')
            row.operator('help.mextrude', text='?')
            row = layout.split(0.70)
            row.operator('faceinfillet.op0_id', text='Inset Fillet')
            row.operator('help.face_inset', text='?')
            row = layout.split(0.70)
            row.operator('mesh.ext_cut_faces', text='Cut Faces')
            row.operator('help.cut_faces', text='?')
            row = layout.split(0.70)
            row.operator('sp_sol.op0_id', text='Split Solidify')
            row.operator('help.solidify', text='?')

        # Utils options
        box1 = self.layout.box()
        col = box1.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "UTUtils1Drop", icon="TRIA_DOWN")

        if not UTILS1DROP:
            row.menu("mesh.utils specials", icon="SOLO_OFF", text="")
            row.menu("VIEW3D_MT_Edit_MultiMET", icon="LOOPSEL", text="")
        if UTILS1DROP:
            layout = self.layout
            row = layout.row()
            row.label(text="Utilities:")
            row = layout.row()
            row = layout.split(0.70)
            row.operator('object_ot.fastloop', text='Fast Loop')
            row.operator('help.random_vert', text='?')
            row = layout.row()
            row.operator('mesh.flip_normals', text='Normals Flip')
            row = layout.row()
            row.operator('mesh.remove_doubles', text='Remove Doubles')
            row = layout.row()
            row.operator('mesh.subdivide', text='Subdivide')
            row = layout.row()
            row.operator('mesh.dissolve_limited', text='Dissolve Limited')
            row = layout.row(align=True)
            row.operator('mesh.select_vert_index', icon="VERTEXSEL", text="Vert Index")
            row.operator('mesh.select_edge_index', icon="EDGESEL", text="Edge Index")
            row.operator('mesh.select_face_index', icon="FACESEL", text="Face Index")

# ********** Edit Multiselect **********
class VIEW3D_MT_Edit_MultiMET(bpy.types.Menu):
    bl_label = "Multi Select"
    bl_description = "Multi Select Modes"
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        prop = layout.operator("wm.context_set_value", text="Vertex Select",
                               icon='VERTEXSEL')
        prop.value = "(True, False, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Edge Select",
                               icon='EDGESEL')
        prop.value = "(False, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Face Select",
                               icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge Select",
                               icon='EDITMODE_HLT')
        prop.value = "(True, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Face Select",
                               icon='ORTHO')
        prop.value = "(True, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Edge & Face Select",
                               icon='SNAP_FACE')
        prop.value = "(False, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge & Face Select",
                               icon='SNAP_VOLUME')
        prop.value = "(True, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

# Select Tools
class VIEW3D_MT_Select_Vert(bpy.types.Menu):
    bl_label = "Select Vert"
    bl_description = "Vert Select Modes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        prop = layout.operator("wm.context_set_value", text="Vertex Select",
                               icon='VERTEXSEL')
        prop.value = "(True, False, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge Select",
                               icon='EDITMODE_HLT')
        prop.value = "(True, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Face Select",
                               icon='ORTHO')
        prop.value = "(True, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

class VIEW3D_MT_Select_Edge(bpy.types.Menu):
    bl_label = "Select Edge"
    bl_description = "Edge Select Modes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        prop = layout.operator("wm.context_set_value", text="Edge Select",
                               icon='EDGESEL')
        prop.value = "(False, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge Select",
                               icon='EDITMODE_HLT')
        prop.value = "(True, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Edge & Face Select",
                               icon='SNAP_FACE')
        prop.value = "(False, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

class VIEW3D_MT_Select_Face(bpy.types.Menu):
    bl_label = "Select Face"
    bl_description = "Face Select Modes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        prop = layout.operator("wm.context_set_value", text="Face Select",
                               icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Face Select",
                               icon='ORTHO')
        prop.value = "(True, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Edge & Face Select",
                               icon='SNAP_FACE')
        prop.value = "(False, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

class VIEW3D_MT_selectface_edit_mesh_add(bpy.types.Menu):
    bl_label = "Select by Face"
    bl_idname = "mesh.face_select_tools"
    bl_description = "Face Select Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Face Select')
        layout.operator("mesh.select_all").action = 'TOGGLE'
        layout.operator("mesh.select_all", text="Inverse").action = 'INVERT'
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
    bl_label = "Select by Edge"
    bl_idname = "mesh.edge_select_tools"
    bl_description = "Edge Select Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Edge Select')
        layout.operator("mesh.select_all").action = 'TOGGLE'
        layout.operator("mesh.select_all", text="Inverse").action = 'INVERT'
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
    bl_label = "Select by Vert"
    bl_idname = "mesh.vert_select_tools"
    bl_description = "Vert Select Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Vert Select')
        layout.operator("mesh.select_all").action = 'TOGGLE'
        layout.operator("mesh.select_all", text="Inverse").action = 'INVERT'
        layout.separator()
        layout.operator("mesh.select_vert_index",
            text="By Vert Index")
        layout.operator("mesh.select_by_direction",
            text="By Direction")
        layout.operator("mesh.select_by_pi",
            text="By Pi")
        layout.separator()
        layout.operator("mesh.v2v_by_edge",
            text="Neighbors by Edge")
        layout.operator("mesh.e2e_eve",
            text="Neighbors by Vert")
        layout.operator("mesh.e2e_efe",
            text="Neighbors by Face")
        layout.operator("mesh.v2v_facewise",
            text="Neighbors by Face - Edge")

class VIEW3D_MT_utils_specials(bpy.types.Menu):
    bl_label = "Specials Menu"
    bl_idname = "mesh.utils specials"
    bl_description = "Utils Quick Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text = 'Fast Specials')
        layout.menu("VIEW3D_MT_edit_mesh_clean")
        layout.operator("mesh.subdivide", text="Subdivide").smoothness = 0.0
        layout.operator("mesh.merge", text="Merge...")
        layout.operator("mesh.remove_doubles")
        layout.operator("mesh.inset")
        layout.operator("mesh.bevel", text="Bevel")
        layout.operator("mesh.bridge_edge_loops")
        layout.operator("mesh.normals_make_consistent", text="Recalculate Outside").inside = False
        layout.operator("mesh.normals_make_consistent", text="Recalculate Inside").inside = True
        layout.operator("mesh.flip_normals")


# Addons Preferences

class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="----Mesh Edit Tools----")
        layout.label(text="Collection of extra Mesh Edit Functions")
        layout.label(text="Edit Mode toolshelf or W key specials")

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu('VIEW3D_MT_edit_mesh_extras')
    self.layout.menu('VIEW3D_MT_edit_mesh_edgetools')

# Define "Select" Menu
def menu_select(self, context):
    if context.tool_settings.mesh_select_mode[2]:
        self.layout.menu("mesh.face_select_tools", icon="FACESEL")
    if context.tool_settings.mesh_select_mode[1]:
        self.layout.menu("mesh.edge_select_tools", icon="EDGESEL")
    if context.tool_settings.mesh_select_mode[0]:
        self.layout.menu("mesh.vert_select_tools", icon="VERTEXSEL")

def register():

    bpy.types.Scene.UTVertDrop = bpy.props.BoolProperty(
        name="Vert",
        default=False,
        description="Vert Tools")
    bpy.types.Scene.UTEdgeDrop = bpy.props.BoolProperty(
        name="Edge",
        default=False,
        description="Edge Tools")
    bpy.types.Scene.UTFaceDrop = bpy.props.BoolProperty(
        name="Face",
        default=False,
        description="Face Tools")
    bpy.types.Scene.UTUtils1Drop = bpy.props.BoolProperty(
        name="Utils",
        default=False,
        description="Misc Utils")

    mesh_pen_tool.register()
    vfe_specials.register()
    bpy.utils.register_module(__name__)
    wm = bpy.context.window_manager

    # Add "Extras" menu to the "" menu
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_edit_mesh.prepend(menu_select)
    try:
        bpy.types.VIEW3D_MT_Select_Edit_Mesh.prepend(menu_select)
    except:
        pass

def unregister():
    mesh_pen_tool.unregister()
    vfe_specials.unregister()
    del bpy.types.Scene.UTVertDrop
    del bpy.types.Scene.UTEdgeDrop
    del bpy.types.Scene.UTFaceDrop
    del bpy.types.Scene.UTUtils1Drop
    wm = bpy.context.window_manager
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "" menu.
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_select)
    try:
        bpy.types.VIEW3D_MT_Select_Edit_Mesh.remove(menu_select)
    except:
        pass

if __name__ == "__main__":
    register()
