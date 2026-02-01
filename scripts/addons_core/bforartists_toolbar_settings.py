# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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
    "name": "User Settings",
    "author": "Reiner 'Tiles' Prokein, Blenux (Juso3D)",
    "version": (1, 2, 1),
    "blender": (3, 0, 0),
    "location": "User Preferences > Addons",
    "description": "DO NOT TURN OFF! This addon contains the settings for Bforartists.",
    "warning": "",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "support": "OFFICIAL",
    "category": "Bforartists",
}

import bpy

from bpy.types import Operator, Scene, AddonPreferences
from bpy.props import BoolProperty, EnumProperty, IntProperty
import bpy.utils.previews

_icons = None

class BFA_OT_toolbar_settings_prefs(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    # Enums Tabs
    bfa_pref_tab_types: EnumProperty(name='Preference Tabs Types', description='', items=[
        ('Topbar', 'Topbar', 'Topbar Options', 0, 0),
        ('Toolbar', 'Toolbar', 'Toolbar Options', 0, 1),
        ('Nodes', 'Nodes', 'Nodes Options', 0, 2),
        ('NLA', 'NLA', 'NLA Options', 0, 3),
        ('Outliner', 'Outliner', 'Outliner Options', 0, 4),
        ('Other', 'Other', 'Other Options', 0, 5),
    ])

    bfa_topbar_types: EnumProperty(name='Topbar Types', description='', items=[
        ('Files', 'Files', 'Files Options', 0, 0),
        ('Mesh Edit', 'Mesh Edit', 'Mesh Edit Options', 0, 1),
        ('Primitives', 'Primitives', 'Primitives Options', 0, 2),
        ('Image', 'Image', '', 0, 3),
        ('Tools', 'Tools', '', 0, 4),
        ('Animation', 'Animation', '', 0, 5),
        ('Edit', 'Edit', '', 0, 6),
        ('Misc', 'Misc', '', 0, 7)
    ])

    bfa_toolbar_types: EnumProperty(name='Toolbar Types', description='', items=[
        ('Files', 'Files', 'Files Options', 0, 0),
        ('Mesh Edit', 'Mesh Edit', 'Mesh Edit Options', 0, 1),
        ('Primitives', 'Primitives', 'Primitives Options', 0, 2),
        ('Image', 'Image', '', 0, 3),
        ('Tools', 'Tools', '', 0, 4),
        ('Animation', 'Animation', '', 0, 5),
        ('Edit', 'Edit', '', 0, 6),
        ('Misc', 'Misc', '', 0, 7)
    ])

    #bfa_options: EnumProperty(name='Adv Options', description='', items=[
    #    ('Reset', 'Reset', 'Reset Options', 0, 0),
    #    ('Other', 'Other', 'Other Options', 0, 1),])

    # File Topbar
    topbar_file_cbox: BoolProperty(name="Files", default=True, description = "Display the Files Topbar Operators\nAll Modes",)
    topbar_file_load_save : BoolProperty(name="Load / Save", default=True, description = "Display the Load Save Topbar\nAll Modes", )
    topbar_file_recover : BoolProperty(name="Recover", default=False, description = "Display the Recover Topbar\nAll Modes", )
    topbar_file_link_append : BoolProperty(name="Link / Append", default=False, description = "Display the Link Append Topbar\nAll Modes", )
    topbar_file_import_menu : BoolProperty(name="Import Menu", default=True, description = "Display the Import Menu\nAll Modes", )
    topbar_file_export_menu : BoolProperty(name="Export Menu", default=True, description = "Display the Export Menu\nAll Modes", )
    topbar_file_import_common : BoolProperty(name="Import Common", default=False, description = "Display the Import Common Topbar - FBX, Obj, Alembic\nAll Modes", )
    topbar_file_import_common2 : BoolProperty(name="Import Common2", default=False, description = "Display the Import Common2 Topbar - BVH, 3DS\nAll Modes", )
    topbar_file_import_uncommon : BoolProperty(name="Import Uncommon", default=False, description = "Display the Import Uncommon Topbar - STL, PLY, WRL, SVG\nAll Modes", )
    topbar_file_export_common : BoolProperty(name="Export Common", default=False, description = "Display the Export Common Topbar - FBX, Obj, Alembic\nAll Modes", )
    topbar_file_export_common2 : BoolProperty(name="Export Common2", default=False, description = "Display the Export Common2 Topbar - BVH, 3DS\nAll Modes", )
    topbar_file_export_uncommon : BoolProperty(name="Export Uncommon", default=False, description = "Display the Export Uncommon Topbar - STL, PLY, WRL, SVG\nAll Modes", )
    topbar_file_render : BoolProperty(name="Render", default=True, description = "Display the Render Topbar\nAll Modes", )
    topbar_file_render_opengl : BoolProperty(name="Render OpenGL", default=False, description = "Display the Render OpenGL Topbar\nAll Modes", )
    topbar_file_render_misc : BoolProperty(name="Render Misc", default=False, description = "Display the Render Misc Topbar\nAll Modes", )


    # Mesh Edit Topbar
    topbar_mesh_cbox: BoolProperty(name='Mesh Edit', default=True, description = "Display the Topbar Mesh Edit Operators\nAll Modes",)
    topbar_mesh_vertices_splitconnect : BoolProperty(name="Vertices Split Connect", default=True, description = "Display the Mesh Edit Vertices Split / Connect\nMesh Object, Edit Mode", )
    topbar_mesh_vertices_misc : BoolProperty(name="Vertices Misc", default=False, description = "Display the Mesh Edit Vertices Misc Topbar with misc tools\nMesh Object, Edit Mode", )
    topbar_mesh_edges_subdiv : BoolProperty(name="Edges Subdiv", default=False, description = "Display the Mesh Edit Edges Subdiv Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_edges_sharp : BoolProperty(name="Edges Sharp", default=True, description = "Display the Mesh Edit Edges Sharp Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_edges_freestyle : BoolProperty(name="Edges Freestyle", default=False, description = "Display the Mesh Edit Edges Freestyle Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_edges_rotate : BoolProperty(name="Edges Rotate", default=True, description = "Display the Mesh Edit Edges Rotate Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_edges_misc : BoolProperty(name="Edges Misc", default=True, description = "Display the Mesh Edit Edges MiscTopbar\nMesh Object, Edit Mode", )
    topbar_mesh_faces_general : BoolProperty(name="Faces General", default=False, description = "Display the Mesh Edit Faces General Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_faces_freestyle : BoolProperty(name="Faces Freestyle", default=False, description = "Display the Mesh Edit Faces Freestyle Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_faces_tris : BoolProperty(name="Faces Tris", default=True, description = "Display the Mesh Edit Faces Tris Topbar\nMesh Object, Edit Mode", )
    topbar_mesh_faces_rotatemisc : BoolProperty(name="Faces Rotate Misc", default=False, description = "Display the Mesh Edit Faces Rotate Misc Toolbar\nMesh Object, Edit Mode", )
    topbar_mesh_cleanup : BoolProperty(name="Cleanup", default=False, description = "Display the Mesh Edit Cleanup Topbar\nMesh Object, Edit Mode", )


    # Primitives Topbar
    topbar_primitives_cbox: BoolProperty(name='Primitives', default=True, description = "Display the Topbar Primitives Operators\nAll Modes",)
    topbar_primitives_mesh : BoolProperty(name="Mesh", default=True, description = "Display the Mesh primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_curve : BoolProperty(name="Curve", default=False, description = "Display the Curve primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_surface : BoolProperty(name="Surface", default=False, description = "Display the Surface primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_metaball : BoolProperty(name="Metaball", default=False, description = "Display the Metaball primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_point_cloud : BoolProperty(name="Point Cloud", default=False, description = "Display the Point Cloud primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_volume : BoolProperty(name="Volume", default=False, description = "Display the Volume primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_gpencil : BoolProperty(name="Grease Pencil", default=True, description = "Display the Grease Pencil primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_gpencil_lineart : BoolProperty(name="Grease Pencil Line Art", default=False, description = "Display the Grease Pencil Line Art primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_light : BoolProperty(name="Light", default=False, description = "Display the Light primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_other : BoolProperty(name="Other", default=True, description = "Display the Other primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_empties : BoolProperty(name="Empties", default=False, description = "Display the Empties primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_image : BoolProperty(name="Image", default=False, description = "Display the Image primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_lightprobe : BoolProperty(name="Light Probe", default=False, description = "Display the Light Probe primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_forcefield : BoolProperty(name="Force Field", default=False, description = "Display the Force Field primitive Topbar\nDisplay is mode dependant", )
    topbar_primitives_collection : BoolProperty(name="Collection", default=False, description = "Display the Collection primitive Topbar\nDisplay is mode dependant", )


    # Image Topbar
    topbar_image_cbox: BoolProperty(name='Image', default=False, description = "Display the Topbar Image Operators\nAll Modes",)
    topbar_image_uv_mirror : BoolProperty(name="UV Mirror", default=True, description = "Display the UV Mirror Topbar\nAll Modes", )
    topbar_image_uv_rotate : BoolProperty(name="UV Rotate", default=True, description = "Display the UV Rotate Topbar\nAll Modes", )
    topbar_image_uv_align : BoolProperty(name="UV Align", default=True, description = "Display the UV Align Topbar\nAll Modes", )
    topbar_image_uv_unwrap : BoolProperty(name="UV Tools - UV Unwrap", default=True, description = "Display the UV Unwrap Topbar\nAll Modes", )
    topbar_image_uv_modify : BoolProperty(name="UV Tools - Modify UV", default=True, description = "Display the UV Modify Topbar\nAll Modes", )


    # Tools Topbar
    topbar_tools_cbox: BoolProperty(name='Tools', default=True, description = "Display the Topbar Tools Operators\nAll Modes",)
    topbar_tools_parent : BoolProperty(name="Parent", default=False, description = "Display the Parent Topbar\nDisplay is mode and content dependant", )
    topbar_tools_objectdata : BoolProperty(name="Object Data", default=False, description = "Display the Object Data Topbar\nDisplay is mode and content dependant", )
    topbar_tools_link_to_scn : BoolProperty(name="Link to SCN", default=False, description = "Display the Link to SCN dropdown box\nDisplay is mode and content dependant", )
    topbar_tools_linked_objects : BoolProperty(name="Linked Objects", default=False, description = "Display the Linked Objects Topbar\nDisplay is mode and content dependant", )
    topbar_tools_join : BoolProperty(name="Join", default=False, description = "Display the Join Topbar\nDisplay is mode and content dependant", )
    topbar_tools_origin : BoolProperty(name="Origin", default=False, description = "Display the Origin Topbar\nDisplay is mode and content dependant", )
    topbar_tools_shading : BoolProperty(name="Shading", default=True, description = "Display the Edit Topbar\nDisplay is mode and content dependant", )
    topbar_tools_datatransfer : BoolProperty(name="Data Transfer", default=False, description = "Display the Edit Topbar\nDisplay is mode and content dependant", )
    topbar_tools_relations : BoolProperty(name="Relations", default=False, description = "Display the Relations Topbar\nDisplay is mode and content dependant", )


    # Animation Topbar
    topbar_animation_cbox: BoolProperty(name='Animation', default=False, description = "Display the Topbar Animation Operators\nAll Modes",)
    topbar_animation_keyframes : BoolProperty(name="Keyframes", default=True, description = "Display the keyframes Topbar\nDisplay is mode and content dependant", )
    topbar_animation_range : BoolProperty(name="Range", default=False, description = "Display the Range Topbar\nAll Modes", )
    topbar_animation_play : BoolProperty(name="Play", default=False, description = "Display the Play Topbar\nAll Modes", )
    topbar_animation_sync : BoolProperty(name="Sync", default=False, description = "Display the Sync Topbar\nAll Modes", )
    topbar_animation_keyframetype : BoolProperty(name="Keyframe Type", default=False, description = "Display the Keyframe Type Topbar\nAll Modes", )
    topbar_animation_keyingset : BoolProperty(name="Keying Set", default=False, description = "Display the Keying Set Topbar\nAll Modes", )

    # Edit Topbar
    topbar_edit_cbox: BoolProperty(name='Edit', default=True, description = "Display the Topbar Edit Operators\nAll Modes",)
    topbar_edit_edit : BoolProperty(name="Edit", default=False, description = "Display the Edit Topbar\nDisplay is mode and content dependant", )
    topbar_edit_weightinedit : BoolProperty(name="Weight in Edit", default=False, description = "Display the Weight in Edit Topbar\nDisplay is mode and content dependant", )
    topbar_edit_objectapply : BoolProperty(name="Object Apply", default=True, description = "Display the Object Apply Topbar\nDisplay is mode and content dependant", )
    topbar_edit_objectapply2 : BoolProperty(name="Object Apply 2", default=False, description = "Display the Object Apply 2 Topbar\nDisplay is mode and content dependant", )
    topbar_edit_objectapplydeltas : BoolProperty(name="Object Apply Deltas", default=False, description = "Display the Object Apply Deltas Topbar\nDisplay is mode and content dependant", )
    topbar_edit_objectclear : BoolProperty(name="Object Clear", default=False, description = "Display the Object Clear Topbar\nDisplay is mode and content dependant", )

    # Misc Topbar
    topbar_misc_cbox: BoolProperty(name='Misc', default=True, description = "Display the Topbar Misc Operators\nAll Modes",)
    topbar_misc_viewport : BoolProperty(name="Viewport", default=False, description = "Display the Viewport Topbar\nAll Modes", )
    topbar_misc_undoredo : BoolProperty(name="Undo / Redo", default=True, description = "Display the Undo Redo Topbar\nAll Modes", )
    topbar_misc_undohistory : BoolProperty(name="Undo History", default=True, description = "Display the Undo History Topbar\nAll Modes", )
    topbar_misc_repeat : BoolProperty(name="Repeat", default=True, description = "Display the Repeat Topbar\nAll Modes", )
    topbar_misc_scene : BoolProperty(name="Scene", default=False, description = "Display the Scene dropdown box", )
    topbar_misc_viewlayer : BoolProperty(name="View Layer", default=False, description = "Display the View Layer dropdown box", )
    topbar_misc_last : BoolProperty(name="Last", default=True, description = "Display the Adjust Last Operator panel\nAll Modes", )
    topbar_misc_operatorsearch : BoolProperty(name="Operator Search", default=True, description = "Display the Operator Search\nAll Modes", )
    topbar_misc_info : BoolProperty(name="Info", default=False, description = "Displays the Info and Messages string", )

    #### Same for Toolbar ####

    # File Toolbar
    file_load_save : BoolProperty(name="Load / Save", default=True, description = "Display the Load Save Toolbar\nAll Modes", )
    file_recover : BoolProperty(name="Recover", default=False, description = "Display the Recover Toolbar\nAll Modes", )
    file_link_append : BoolProperty(name="Link / Append", default=False, description = "Display the Link Append Toolbar\nAll Modes", )
    file_import_menu : BoolProperty(name="Import Menu", default=True, description = "Display the Import Menu\nAll Modes", )
    file_export_menu : BoolProperty(name="Export Menu", default=True, description = "Display the Export Menu\nAll Modes", )
    file_import_common : BoolProperty(name="Import Common", default=False, description = "Display the Import Common Toolbar - FBX, Obj, Alembic\nAll Modes", )
    file_import_common2 : BoolProperty(name="Import Common2", default=False, description = "Display the Import Common2 Toolbar - BVH, 3DS\nAll Modes", )
    file_import_uncommon : BoolProperty(name="Import Uncommon", default=False, description = "Display the Import Uncommon Toolbar - STL, PLY, WRL, SVG\nAll Modes", )
    file_export_common : BoolProperty(name="Export Common", default=False, description = "Display the Export Common Toolbar - FBX, Obj, Alembic\nAll Modes", )
    file_export_common2 : BoolProperty(name="Export Common2", default=False, description = "Display the Export Common2 Toolbar - BVH, 3DS\nAll Modes", )
    file_export_uncommon : BoolProperty(name="Export Uncommon", default=False, description = "Display the Export Uncommon Toolbar - STL, PLY, WRL, SVG\nAll Modes", )
    file_render : BoolProperty(name="Render", default=True, description = "Display the Render Toolbar\nAll Modes", )
    file_render_opengl : BoolProperty(name="Render OpenGL", default=False, description = "Display the Render OpenGL Toolbar\nAll Modes", )
    file_render_misc : BoolProperty(name="Render Misc", default=False, description = "Display the Render Misc Toolbar\nAll Modes", )


    # Mesh Edit Toolbar
    mesh_vertices_splitconnect : BoolProperty(name="Vertices Split Connect", default=True, description = "Display the Mesh Edit Vertices Split / Connect\nMesh Object, Edit Mode", )
    mesh_vertices_misc : BoolProperty(name="Vertices Misc", default=False, description = "Display the Mesh Edit Vertices Misc Toolbar with misc tools\nMesh Object, Edit Mode", )
    mesh_edges_subdiv : BoolProperty(name="Edges Subdiv", default=False, description = "Display the Mesh Edit Edges Subdiv Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_sharp : BoolProperty(name="Edges Sharp", default=True, description = "Display the Mesh Edit Edges Sharp Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_freestyle : BoolProperty(name="Edges Freestyle", default=False, description = "Display the Mesh Edit Edges Freestyle Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_rotate : BoolProperty(name="Edges Rotate", default=True, description = "Display the Mesh Edit Edges Rotate Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_misc : BoolProperty(name="Edges Misc", default=True, description = "Display the Mesh Edit Edges MiscToolbar\nMesh Object, Edit Mode", )
    mesh_faces_general : BoolProperty(name="Faces General", default=False, description = "Display the Mesh Edit Faces General Toolbar\nMesh Object, Edit Mode", )
    mesh_faces_freestyle : BoolProperty(name="Faces Freestyle", default=False, description = "Display the Mesh Edit Faces Freestyle Toolbar\nMesh Object, Edit Mode", )
    mesh_faces_tris : BoolProperty(name="Faces Tris", default=True, description = "Display the Mesh Edit Faces Tris Toolbar\nMesh Object, Edit Mode", )
    mesh_faces_rotatemisc : BoolProperty(name="Faces Rotate Misc", default=False, description = "Display the Mesh Edit Faces Rotate Misc Toolbar\nMesh Object, Edit Mode", )
    mesh_cleanup : BoolProperty(name="Cleanup", default=False, description = "Display the Mesh Edit Cleanup Toolbar\nMesh Object, Edit Mode", )


    # Primitives Toolbar
    primitives_mesh : BoolProperty(name="Mesh", default=True, description = "Display the Mesh primitive Toolbar\nDisplay is mode dependant", )
    primitives_curve : BoolProperty(name="Curve", default=False, description = "Display the Curve primitive Toolbar\nDisplay is mode dependant", )
    primitives_surface : BoolProperty(name="Surface", default=False, description = "Display the Surface primitive Toolbar\nDisplay is mode dependant", )
    primitives_metaball : BoolProperty(name="Metaball", default=False, description = "Display the Metaball primitive Toolbar\nDisplay is mode dependant", )
    primitives_point_cloud : BoolProperty(name="Point Cloud", default=False, description = "Display the Point Cloud primitive Toolbar\nDisplay is mode dependant", )
    primitives_volume : BoolProperty(name="Volume", default=False, description = "Display the Volume primitive Toolbar\nDisplay is mode dependant", )
    primitives_gpencil : BoolProperty(name="Grease Pencil", default=True, description = "Display the Grease Pencil primitive Toolbar\nDisplay is mode dependant", )
    primitives_gpencil_lineart : BoolProperty(name="Grease Pencil Line Art", default=False, description = "Display the Grease Pencil Line Art primitive Toolbar\nDisplay is mode dependant", )
    primitives_light : BoolProperty(name="Light", default=False, description = "Display the Light primitive Toolbar\nDisplay is mode dependant", )
    primitives_other : BoolProperty(name="Other", default=True, description = "Display the Other primitive Toolbar\nDisplay is mode dependant", )
    primitives_empties : BoolProperty(name="Empties", default=False, description = "Display the Empties primitive Toolbar\nDisplay is mode dependant", )
    primitives_image : BoolProperty(name="Image", default=False, description = "Display the Image primitive Toolbar\nDisplay is mode dependant", )
    primitives_lightprobe : BoolProperty(name="Light Probe", default=False, description = "Display the Light Probe primitive Toolbar\nDisplay is mode dependant", )
    primitives_forcefield : BoolProperty(name="Force Field", default=False, description = "Display the Force Field primitive Toolbar\nDisplay is mode dependant", )
    primitives_collection : BoolProperty(name="Collection", default=False, description = "Display the Collection primitive Toolbar\nDisplay is mode dependant", )


    # Image Toolbar
    image_uv_mirror : BoolProperty(name="UV Mirror", default=True, description = "Display the UV Mirror Toolbar\nAll Modes", )
    image_uv_rotate : BoolProperty(name="UV Rotate", default=True, description = "Display the UV Rotate Toolbar\nAll Modes", )
    image_uv_align : BoolProperty(name="UV Align", default=True, description = "Display the UV Align Toolbar\nAll Modes", )
    image_uv_unwrap : BoolProperty(name="UV Tools - UV Unwrap", default=True, description = "Display the UV Unwrap Toolbar\nAll Modes", )
    image_uv_modify : BoolProperty(name="UV Tools - Modify UV", default=True, description = "Display the UV Modify Toolbar\nAll Modes", )


    # Tools Toolbar
    tools_parent : BoolProperty(name="Parent", default=False, description = "Display the Parent Toolbar\nDisplay is mode and content dependant", )
    tools_objectdata : BoolProperty(name="Object Data", default=False, description = "Display the Object Data Toolbar\nDisplay is mode and content dependant", )
    tools_link_to_scn : BoolProperty(name="Link to SCN", default=False, description = "Display the Link to SCN dropdown box\nDisplay is mode and content dependant", )
    tools_linked_objects : BoolProperty(name="Linked Objects", default=False, description = "Display the Linked Objects Toolbar\nDisplay is mode and content dependant", )
    tools_join : BoolProperty(name="Join", default=False, description = "Display the Join Toolbar\nDisplay is mode and content dependant", )
    tools_origin : BoolProperty(name="Origin", default=False, description = "Display the Origin Toolbar\nDisplay is mode and content dependant", )
    tools_shading : BoolProperty(name="Shading", default=True, description = "Display the Edit Toolbar\nDisplay is mode and content dependant", )
    tools_datatransfer : BoolProperty(name="Data Transfer", default=False, description = "Display the Edit Toolbar\nDisplay is mode and content dependant", )
    tools_relations : BoolProperty(name="Relations", default=False, description = "Display the Relations Toolbar\nDisplay is mode and content dependant", )


    # Animation Toolbar
    animation_keyframes : BoolProperty(name="Keyframes", default=True, description = "Display the keyframes Toolbar\nDisplay is mode and content dependant", )
    animation_range : BoolProperty(name="Range", default=False, description = "Display the Range Toolbar\nAll Modes", )
    animation_play : BoolProperty(name="Play", default=False, description = "Display the Play Toolbar\nAll Modes", )
    animation_sync : BoolProperty(name="Sync", default=False, description = "Display the Sync Toolbar\nAll Modes", )
    animation_keyframetype : BoolProperty(name="Keyframe Type", default=False, description = "Display the Keyframe Type Toolbar\nAll Modes", )
    animation_keyingset : BoolProperty(name="Keying Set", default=False, description = "Display the Keying Set Toolbar\nAll Modes", )


    # Edit Toolbar
    edit_edit : BoolProperty(name="Edit", default=False, description = "Display the Edit Toolbar\nDisplay is mode and content dependant", )
    edit_weightinedit : BoolProperty(name="Weight in Edit", default=False, description = "Display the Weight in Edit Toolbar\nDisplay is mode and content dependant", )
    edit_objectapply : BoolProperty(name="Object Apply", default=True, description = "Display the Object Apply Toolbar\nDisplay is mode and content dependant", )
    edit_objectapply2 : BoolProperty(name="Object Apply 2", default=False, description = "Display the Object Apply 2 Toolbar\nDisplay is mode and content dependant", )
    edit_objectapplydeltas : BoolProperty(name="Object Apply Deltas", default=False, description = "Display the Object Apply Deltas Toolbar\nDisplay is mode and content dependant", )
    edit_objectclear : BoolProperty(name="Object Clear", default=False, description = "Display the Object Clear Toolbar\nDisplay is mode and content dependant", )


    # Misc Toolbar
    misc_viewport : BoolProperty(name="Viewport", default=False, description = "Display the Viewport toolbar\nAll Modes", )
    misc_undoredo : BoolProperty(name="Undo / Redo", default=True, description = "Display the Undo Redo toolbar\nAll Modes", )
    misc_undohistory : BoolProperty(name="Undo History", default=True, description = "Display the Undo History Toolbar\nAll Modes", )
    misc_repeat : BoolProperty(name="Repeat", default=True, description = "Display the Repeat Toolbar\nAll Modes", )
    misc_scene : BoolProperty(name="Scene", default=False, description = "Display the Scene dropdown box", )
    misc_viewlayer : BoolProperty(name="View Layer", default=False, description = "Display the View Layer dropdown box", )
    misc_last : BoolProperty(name="Last", default=True, description = "Display the Adjust Last Operator panel\nAll Modes", )
    misc_operatorsearch : BoolProperty(name="Operator Search", default=True, description = "Display the Operator Search\nAll Modes", )
    misc_info : BoolProperty(name="Info", default=False, description = "Displays the Info and Messages string", )

    # Node Editor
    Node_text_or_icon : BoolProperty(name="Icon / Text Buttons", default = False, description = "Switch Between Icons or Text Buttons")
    Node_shader_add_common : BoolProperty(name="Common", default = False, description = "Display just the common shader nodes")

    # Outliner Booleans
    outliner_show_search : BoolProperty(name="Show Search", default = False, description = "Show the search form")

    # Other Options
    bfa_button_style: BoolProperty(name='Checkerbox/Button Toggle', description='Switch between Checkerbox or Button Type', default=False)

    # Toolbar Options
    topbar_show_quicktoggle : BoolProperty(name="Show Topbar Quick Toggle", default = False, description = "Show the quick toggle buttons per type in the topbar")
    toolbar_show_quicktoggle : BoolProperty(name="Show Toolbar Quick Toggle", default = False, description = "Show the quick toggle buttons in the toolbar editor")

    # NLA Editor, switch tweak methods
    nla_tweak_isolate_action : BoolProperty(name="Isolate", default = False, description = "Edit action in isolate mode")


    def draw(self, context, ):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        layout = self.layout
        box = layout.box()
        row = box.row()
        row.alignment = 'Center'.upper()
        row.label(text='Bforartists Preferences Manager',)

        grid = box.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True, align=True)
        grid.prop(addon_prefs, 'bfa_pref_tab_types', text='Types', icon= "BLENDER", emboss=True, expand=True,)

        # Topbar Options
        if (addon_prefs.bfa_pref_tab_types == 'Topbar'):

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The File Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_file_load_save", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_recover", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_link_append", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_import_menu", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_export_menu", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_import_common", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_import_common2", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_import_uncommon", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_export_common", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_export_common2", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_export_uncommon", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_render", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_render_opengl", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_file_render_misc", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Mesh Edit Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_mesh_vertices_splitconnect", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_vertices_misc", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_edges_subdiv", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_edges_sharp", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_edges_freestyle", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_edges_rotate", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_edges_misc", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_faces_general", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_faces_freestyle", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_faces_tris", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_faces_rotatemisc", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_mesh_cleanup", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Primitives Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_primitives_mesh", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_curve", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_surface", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_metaball", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_point_cloud", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_volume", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_gpencil", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_gpencil_lineart", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_light", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_other", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_empties", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_image", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_lightprobe", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_forcefield", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_primitives_collection", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Image Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_image_uv_mirror", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_image_uv_rotate", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_image_uv_align", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_image_uv_unwrap", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_image_uv_modify", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Tools Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_tools_parent", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_objectdata", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_link_to_scn", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_linked_objects", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_join", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_origin", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_shading", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_datatransfer", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_tools_relations", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Animation Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_animation_keyframes", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_animation_range", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_animation_play", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_animation_sync", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_animation_keyframetype", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_animation_keyingset", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Edit Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_edit_edit", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_edit_weightinedit", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_edit_objectapply", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_edit_objectapply2", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_edit_objectapplydeltas", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Misc Topbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_misc_viewport", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_undoredo", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_undohistory", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_repeat", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_scene", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_viewlayer", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_last", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_info", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "topbar_misc_operatorsearch", toggle=addon_prefs.bfa_button_style)

            row = layout.row(align=True)
            row.separator()

        # Toolbar Options
        if (addon_prefs.bfa_pref_tab_types == 'Toolbar'):

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The File Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "file_load_save", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_recover", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_link_append", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_import_menu", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_export_menu", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_import_common", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_import_common2", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_import_uncommon", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_export_common", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_export_common2", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_export_uncommon", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_render", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_render_opengl", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "file_render_misc", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Mesh Edit Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "mesh_vertices_splitconnect", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_vertices_misc", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_edges_subdiv", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_edges_sharp", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_edges_freestyle", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_edges_rotate", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_edges_misc", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_faces_general", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_faces_freestyle", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_faces_tris", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_faces_rotatemisc", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "mesh_cleanup", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Primitives Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "primitives_mesh", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_curve", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_surface", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_metaball", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_point_cloud", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_volume", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_gpencil", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_gpencil_lineart", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_light", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_other", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_empties", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_image", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_lightprobe", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_forcefield", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "primitives_collection", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Image Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "image_uv_mirror", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "image_uv_rotate", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "image_uv_align", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "image_uv_unwrap", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "image_uv_modify", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Tools Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "tools_parent", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_objectdata", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_link_to_scn", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_linked_objects", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_join", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_origin", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_shading", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_datatransfer", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "tools_relations", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Animation Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "animation_keyframes", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "animation_range", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "animation_play", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "animation_sync", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "animation_keyframetype", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "animation_keyingset", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Edit Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "edit_edit", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "edit_weightinedit", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "edit_objectapply", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "edit_objectapply2", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "edit_objectapplydeltas", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Misc Toolbar Container")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "misc_viewport", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_undoredo", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_undohistory", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_repeat", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_scene", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_viewlayer", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_last", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_info", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "misc_operatorsearch", toggle=addon_prefs.bfa_button_style)

            row = layout.row(align=True)
            row.separator()

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="The Toolbar Quicktoggle")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=True, align=True)

            grid.prop(self, "topbar_show_quicktoggle", toggle=addon_prefs.bfa_button_style)
            grid.prop(self, "toolbar_show_quicktoggle", toggle=addon_prefs.bfa_button_style)

        # Node Editor Options
        if (addon_prefs.bfa_pref_tab_types == 'Nodes'):

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="Text or Icon Buttons in the Properties Sidebar")
            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)
            grid.prop(self, "Node_text_or_icon", toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="Show Only The Most Common Nodes")
            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)
            grid.prop(self, "Node_shader_add_common", toggle=addon_prefs.bfa_button_style)

        # Outliner Options
        if (addon_prefs.bfa_pref_tab_types == 'Outliner'):

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="Show/Hide Search in the Outliner.")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)

            grid.prop(self, "outliner_show_search", toggle=addon_prefs.bfa_button_style)

        # Other Options
        if (addon_prefs.bfa_pref_tab_types == 'Other'):

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="Addon Options")
            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)
            grid.prop(addon_prefs, 'bfa_button_style', text='Button Style', icon="NONE", emboss=True, expand=True, toggle=addon_prefs.bfa_button_style)

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="Topbar Defaults Option")

            box.operator("bfa.reset_topbar")
            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)

            grid.operator("bfa.reset_files",)
            grid.operator("bfa.reset_meshedit",)
            grid.operator("bfa.reset_primitives",)
            grid.operator("bfa.reset_image",)
            grid.operator("bfa.reset_tools",)
            grid.operator("bfa.reset_animation",)
            grid.operator("bfa.reset_edit",)
            grid.operator("bfa.reset_misc",)


        # NLA Options
        if (addon_prefs.bfa_pref_tab_types == 'NLA'):

            box = layout.box()
            row = box.row()
            row.alignment = 'Center'.upper()
            row.label(text="Toggle Between Action Tweak Mode All and Isolated")

            grid = box.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)

            grid.prop(self, "nla_tweak_isolate_action", toggle=addon_prefs.bfa_button_style)


##### Topbar Reset Functions ####
def bfa_reset_files(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Files Defaults #
        reset("topbar_file_cbox")
        reset("topbar_file_load_save")
        reset("topbar_file_recover")
        reset("topbar_file_link_append")
        reset("topbar_file_import_menu")
        reset("topbar_file_export_menu")
        reset("topbar_file_import_common")
        reset("topbar_file_import_common2")
        reset("topbar_file_import_uncommon")
        reset("topbar_file_export_common")
        reset("topbar_file_export_common2")
        reset("topbar_file_export_uncommon")
        reset("topbar_file_render")
        reset("topbar_file_render_opengl")
        reset("topbar_file_render_misc")


def bfa_reset_meshedit(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Mesh Edit Defaults #
        reset("topbar_mesh_cbox")
        reset("topbar_mesh_vertices_splitconnect")
        reset("topbar_mesh_vertices_misc")
        reset("topbar_mesh_edges_subdiv")
        reset("topbar_mesh_edges_sharp")
        reset("topbar_mesh_edges_freestyle")
        reset("topbar_mesh_edges_rotate")
        reset("topbar_mesh_edges_misc")
        reset("topbar_mesh_faces_general")
        reset("topbar_mesh_faces_freestyle")
        reset("topbar_mesh_faces_tris")
        reset("topbar_mesh_faces_rotatemisc")
        reset("topbar_mesh_cleanup")


def bfa_reset_primitives(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Primitives Defaults #
        reset("topbar_primitives_cbox")
        reset("topbar_primitives_mesh")
        reset("topbar_primitives_curve")
        reset("topbar_primitives_surface")
        reset("topbar_primitives_metaball")
        reset("topbar_primitives_point_cloud")
        reset("topbar_primitives_volume")
        reset("topbar_primitives_gpencil")
        reset("topbar_primitives_gpencil_lineart")
        reset("topbar_primitives_light")
        reset("topbar_primitives_other")
        reset("topbar_primitives_empties")
        reset("topbar_primitives_image")
        reset("topbar_primitives_lightprobe")
        reset("topbar_primitives_forcefield")
        reset("topbar_primitives_collection")


def bfa_reset_image(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Images Defaults #
        reset("topbar_image_cbox")
        reset("topbar_image_uv_mirror")
        reset("topbar_image_uv_rotate")
        reset("topbar_image_uv_align",)
        reset("topbar_image_uv_unwrap")
        reset("topbar_image_uv_modify")


def bfa_reset_tools(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Tools Defaults #
        reset("topbar_tools_cbox")
        reset("topbar_tools_parent")
        reset("topbar_tools_objectdata")
        reset("topbar_tools_link_to_scn")
        reset("topbar_tools_linked_objects")
        reset("topbar_tools_join")
        reset("topbar_tools_origin")
        reset("topbar_tools_shading")
        reset("topbar_tools_datatransfer")
        reset("topbar_tools_relations")


def bfa_reset_animation(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Animation Defaults #
        reset("topbar_animation_cbox")
        reset("topbar_animation_keyframes")
        reset("topbar_animation_range")
        reset("topbar_animation_play")
        reset("topbar_animation_sync")
        reset("topbar_animation_keyframetype")
        reset("topbar_animation_keyingset")


def bfa_reset_edit(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Edit Defaults #
        reset("topbar_edit_cbox")
        reset("topbar_edit_edit")
        reset("topbar_edit_weightinedit")
        reset("topbar_edit_objectapply")
        reset("topbar_edit_objectapply2")
        reset("topbar_edit_objectapplydeltas")


def bfa_reset_misc(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Topbar Misc Defaults #
        reset("topbar_misc_cbox")
        reset("topbar_misc_viewport")
        reset("topbar_misc_undoredo")
        reset("topbar_misc_undohistory")
        reset("topbar_misc_repeat")
        reset("topbar_misc_scene")
        reset("topbar_misc_viewlayer")
        reset("topbar_misc_last")
        reset("topbar_misc_info")
        reset("topbar_misc_operatorsearch")

##### Topbar Reset Operators ####
class BFA_OT_reset_topbar(Operator):
    """ Reset Topbar To Defaults """
    bl_idname = "bfa.reset_topbar"
    bl_label = "Reset All"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_files(layout_function,)
        bfa_reset_meshedit(layout_function,)
        bfa_reset_primitives(layout_function,)
        bfa_reset_image(layout_function,)
        bfa_reset_tools(layout_function,)
        bfa_reset_edit(layout_function,)
        bfa_reset_animation(layout_function,)
        bfa_reset_misc(layout_function,)

        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset
        reset("bfa_topbar_types")

        prefs = bpy.context.scene
        reset = prefs.property_unset
        reset("bfa_defaults")

        self.report({'INFO'}, message='Topbar Set to Defaults')

        return {'FINISHED'}

class BFA_OT_reset_files(Operator):
    """ Reset Topbar Files To Defaults """
    bl_idname = "bfa.reset_files"
    bl_label = "Files"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_files(layout_function,)

        self.report({'INFO'}, message='Topbar Files Set to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_meshedit(Operator):
    """ Reset Topbar Mesh Edit To Defaults """
    bl_idname = "bfa.reset_meshedit"
    bl_label = "Mesh Edit"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_meshedit(layout_function,)
        self.report({'INFO'}, message='Topbar Mesh Edit Set to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_primitives(Operator):
    """ Reset Topbar Primitives To Defaults """
    bl_idname = "bfa.reset_primitives"
    bl_label = "Primitives"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_primitives(layout_function,)
        self.report({'INFO'}, message='Topbar Primitives Set to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_image(Operator):
    """ Reset Topbar Image To Defaults """
    bl_idname = "bfa.reset_image"
    bl_label = "Images"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_image(layout_function,)
        self.report({'INFO'}, message='Topbar Image to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_tools(Operator):
    """ Reset Topbar Tools To Defaults """
    bl_idname = "bfa.reset_tools"
    bl_label = "Tools"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_tools(layout_function,)
        self.report({'INFO'}, message='Topbar Tools Set to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_animation(Operator):
    """ Reset Topbar Animation To Defaults """
    bl_idname = "bfa.reset_animation"
    bl_label = "Animation"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_animation(layout_function,)
        self.report({'INFO'}, message='Topbar Animation Set to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_edit(Operator):
    """ Reset Topbar Edit To Defaults """
    bl_idname = "bfa.reset_edit"
    bl_label = "Edit"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_edit(layout_function,)
        self.report({'INFO'}, message='Topbar Edit Set to Defaults')
        return {'FINISHED'}

class BFA_OT_reset_misc(Operator):
    """ Reset Topbar Misc To Defaults """
    bl_idname = "bfa.reset_misc"
    bl_label = "Misc"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_misc(layout_function,)
        self.report({'INFO'}, message='Topbar Misc Set to Defaults')
        return {'FINISHED'}

##### Toolbar Reset Functions ####
def bfa_reset_toolbar_files(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Files Defaults #
        # Reset the area property for file_toolbars visibility to default (True/visible)
        if bpy.context.area:
            bpy.context.area.file_toolbars = True

        reset("file_load_save")
        reset("file_recover")
        reset("file_link_append")
        reset("file_import_menu")
        reset("file_export_menu")
        reset("file_import_common")
        reset("file_import_common2")
        reset("file_import_uncommon")
        reset("file_export_common")
        reset("file_export_common2")
        reset("file_export_uncommon")
        reset("file_render")
        reset("file_render_opengl")
        reset("file_render_misc")

def bfa_reset_toolbar_meshedit(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Mesh Edit Defaults #
        # Reset the area property for meshedit_toolbars visibility to default (True/visible)
        if bpy.context.area:
            bpy.context.area.meshedit_toolbars = True

        reset("mesh_vertices_splitconnect")
        reset("mesh_vertices_misc")
        reset("mesh_edges_subdiv")
        reset("mesh_edges_sharp")
        reset("mesh_edges_freestyle")
        reset("mesh_edges_rotate")
        reset("mesh_edges_misc")
        reset("mesh_faces_general")
        reset("mesh_faces_freestyle")
        reset("mesh_faces_tris")
        reset("mesh_faces_rotatemisc")
        reset("mesh_cleanup")

def bfa_reset_toolbar_primitives(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Primitives Defaults #
        # Reset the area property for primitives_toolbars visibility to default (True/visible)
        if bpy.context.area:
            bpy.context.area.primitives_toolbars = True

        reset("primitives_mesh")
        reset("primitives_curve")
        reset("primitives_surface")
        reset("primitives_metaball")
        reset("primitives_point_cloud")
        reset("primitives_volume")
        reset("primitives_gpencil")
        reset("primitives_gpencil_lineart")
        reset("primitives_light")
        reset("primitives_other")
        reset("primitives_empties")
        reset("primitives_image")
        reset("primitives_lightprobe")
        reset("primitives_forcefield")
        reset("primitives_collection")

def bfa_reset_toolbar_image(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Image Defaults #
        # Reset the area property for image_toolbars visibility to default (True/visible)
        if bpy.context.area:
            bpy.context.area.image_toolbars = False

        reset("image_uv_mirror")
        reset("image_uv_rotate")
        reset("image_uv_align")
        reset("image_uv_unwrap")
        reset("image_uv_modify")

def bfa_reset_toolbar_tools(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Tools Defaults #
        # Reset the area property for tools_toolbars visibility to default (True/visible)
        if bpy.context.area:
            bpy.context.area.tools_toolbars = True

        reset("tools_parent")
        reset("tools_objectdata")
        reset("tools_link_to_scn")
        reset("tools_linked_objects")
        reset("tools_join")
        reset("tools_origin")
        reset("tools_shading")
        reset("tools_datatransfer")
        reset("tools_relations")

def bfa_reset_toolbar_animation(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Animation Defaults #
        # Reset the area property for animation_toolbars visibility
        if bpy.context.area:
            bpy.context.area.animation_toolbars = False

        reset("animation_keyframes")
        reset("animation_range")
        reset("animation_play")
        reset("animation_sync")
        reset("animation_keyframetype")
        reset("animation_keyingset")

def bfa_reset_toolbar_edit(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Edit Defaults #
        # Reset the area property for edit_toolbars visibility
        if bpy.context.area:
            bpy.context.area.edit_toolbars = True

        reset("edit_edit")
        reset("edit_weightinedit")
        reset("edit_objectapply")
        reset("edit_objectapply2")
        reset("edit_objectapplydeltas")
        reset("edit_objectclear")

def bfa_reset_toolbar_misc(layout_function,):
        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset

        # Toolbar Misc Defaults #
        # Reset the area property for misc_toolbars visibility
        if bpy.context.area:
            bpy.context.area.misc_toolbars = True

        reset("misc_viewport")
        reset("misc_undoredo")
        reset("misc_undohistory")
        reset("misc_repeat")
        reset("misc_scene")
        reset("misc_viewlayer")
        reset("misc_last")
        reset("misc_info")
        reset("misc_operatorsearch")

##### Toolbar Reset Operators ####
class BFA_OT_reset_toolbar(Operator):
    """ Reset Toolbar To Defaults """
    bl_idname = "bfa.reset_toolbar"
    bl_label = "Reset Toolbar All"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_files(layout_function,)
        bfa_reset_toolbar_meshedit(layout_function,)
        bfa_reset_toolbar_primitives(layout_function,)
        bfa_reset_toolbar_image(layout_function,)
        bfa_reset_toolbar_tools(layout_function,)
        bfa_reset_toolbar_edit(layout_function,)
        bfa_reset_toolbar_animation(layout_function,)
        bfa_reset_toolbar_misc(layout_function,)

        prefs = bpy.context.preferences.addons[__name__].preferences
        reset = prefs.property_unset
        reset("bfa_toolbar_types")

        prefs = bpy.context.scene
        reset = prefs.property_unset
        reset("bfa_defaults")

        self.report({'INFO'}, message='Topbar Set to Defaults')

        return {'FINISHED'}

class BFA_OT_reset_toolbar_files(Operator):
    """ Reset Toolbar Files To Defaults """
    bl_idname = "bfa.reset_toolbar_files"
    bl_label = "Files"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_files(layout_function,)
        self.report({'INFO'}, message='Toolbar Files Set to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_meshedit(Operator):
    """ Reset Toolbar Mesh Edit To Defaults """
    bl_idname = "bfa.reset_toolbar_meshedit"
    bl_label = "Mesh Edit"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_meshedit(layout_function,)
        self.report({'INFO'}, message='Toolbar Mesh Edit Set to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_primitives(Operator):
    """ Reset Toolbar Primitives To Defaults """
    bl_idname = "bfa.reset_toolbar_primitives"
    bl_label = "Primitives"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_primitives(layout_function,)
        self.report({'INFO'}, message='Toolbar Primitives Set to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_image(Operator):
    """ Reset Toolbar Image To Defaults """
    bl_idname = "bfa.reset_toolbar_image"
    bl_label = "Images"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_image(layout_function,)
        self.report({'INFO'}, message='Toolbar Image to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_tools(Operator):
    """ Reset Toolbar Tools To Defaults """
    bl_idname = "bfa.reset_toolbar_tools"
    bl_label = "Tools"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_tools(layout_function,)
        self.report({'INFO'}, message='Toolbar Tools Set to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_animation(Operator):
    """ Reset Toolbar Animation To Defaults """
    bl_idname = "bfa.reset_toolbar_animation"
    bl_label = "Animation"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_animation(layout_function,)
        self.report({'INFO'}, message='Toolbar Animation Set to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_edit(Operator):
    """ Reset Toolbar Edit To Defaults """
    bl_idname = "bfa.reset_toolbar_edit"
    bl_label = "Edit"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_edit(layout_function,)
        self.report({'INFO'}, message='Toolbar Edit Set to Defaults')
        return {'FINISHED'}
    
class BFA_OT_reset_toolbar_misc(Operator):
    """ Reset Toolbar Misc To Defaults """
    bl_idname = "bfa.reset_toolbar_misc"
    bl_label = "Misc"
    bl_options = {"REGISTER"}

    def execute(self, context):
        layout = self.layout
        layout_function = layout
        bfa_reset_toolbar_misc(layout_function,)
        self.report({'INFO'}, message='Toolbar Misc Set to Defaults')
        return {'FINISHED'}


classes = (
    BFA_OT_toolbar_settings_prefs,
    ###### Topbar Reset Operators #####
    BFA_OT_reset_topbar,
    BFA_OT_reset_files,
    BFA_OT_reset_meshedit,
    BFA_OT_reset_primitives,
    BFA_OT_reset_image,
    BFA_OT_reset_tools,
    BFA_OT_reset_animation,
    BFA_OT_reset_edit,
    BFA_OT_reset_misc,
    ##### Toolbar Reset Operators #####
    BFA_OT_reset_toolbar,
    BFA_OT_reset_toolbar_files,
    BFA_OT_reset_toolbar_meshedit,
    BFA_OT_reset_toolbar_primitives,
    BFA_OT_reset_toolbar_image,
    BFA_OT_reset_toolbar_tools,
    BFA_OT_reset_toolbar_animation,
    BFA_OT_reset_toolbar_edit,
    BFA_OT_reset_toolbar_misc,
)


# Registration
def register():
    from bpy.utils import register_class
    for cls in classes:
       register_class(cls)

    Scene.bfa_defaults = BoolProperty(name='BFA Defaults', description='Resets Topbar to Default State', default=False)
    Scene.bfa_toolbar_defaults = BoolProperty(name='BFA Toolbar Defaults', description='Resets Toolbar to Default State', default=False)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
       unregister_class(cls)

    del Scene.bfa_defaults
    del Scene.bfa_toolbar_defaults


if __name__ == "__main__":
    register()
