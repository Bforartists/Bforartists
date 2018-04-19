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
    "name": "Toolbar Settings Bforartists",
    "author": "Bforartists",
    "version": (1, 0),
    "blender": (2, 76, 0),
    "location": "User Preferences > Addons",
    "description": "Toolbar Settings. DO NOT TURN OFF! This addon contains the settings for the toolbar editor",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface",
    }


import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty


class bforartists_toolbar_settings(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    # file

    file_load_save = BoolProperty(name="Load / Save", default=True, description = "Display the Load Save Toolbar\nAll Modes", )
    file_link_append = BoolProperty(name="Link / Append", default=False, description = "Display the Link Append Toolbar\nAll Modes", )

    file_import_menu = BoolProperty(name="Import Menu", default=True, description = "Display the Import Menu\nAll Modes", )
    file_export_menu = BoolProperty(name="Export Menu", default=True, description = "Display the Export Menu\nAll Modes", )

    file_import_common = BoolProperty(name="Import Common", default=False, description = "Display the Import Common Toolbar - FBX, Obj, Alembic\nAll Modes", )
    file_import_common2 = BoolProperty(name="Import Common2", default=False, description = "Display the Import Common2 Toolbar - Collada, BVH, 3DS\nAll Modes", )
    file_import_uncommon = BoolProperty(name="Import Uncommon", default=False, description = "Display the Import Uncommon Toolbar - STL, PLY, WRL, SVG\nAll Modes", )
    file_export_common = BoolProperty(name="Export Common", default=False, description = "Display the Export Common Toolbar - FBX, Obj, Alembic\nAll Modes", )
    file_export_common2 = BoolProperty(name="Export Common2", default=False, description = "Display the Export Common2 Toolbar - Collada, BVH, 3DS\nAll Modes", )
    file_export_uncommon = BoolProperty(name="Export Uncommon", default=False, description = "Display the Export Uncommon Toolbar - STL, PLY, WRL, SVG\nAll Modes", )


    file_render = BoolProperty(name="Render", default=True, description = "Display the Render Toolbar\nAll Modes", )
    file_render_opengl = BoolProperty(name="Render Open GL", default=False, description = "Display the Render Open GL Toolbar\nAll Modes", )
    file_render_misc = BoolProperty(name="Render Misc", default=False, description = "Display the Render Misc Toolbar\nAll Modes", )
    file_window_search = BoolProperty(name="Window Search", default=False, description = "Display the Search Toolbar\nAll Modes", )

    # meshedit

    mesh_vertices_splitconnect = BoolProperty(name="Vertices Splitconnect", default=True, description = "Display the the Mesh Edit Vertices Split / Connect\nMesh Object, Edit Mode", )
    mesh_vertices_misc = BoolProperty(name="Vertices Misc", default=False, description = "Display the the Mesh Edit Vertices Misc Toolbar with misc tools\nMesh Object, Edit Mode", )

    mesh_edges_subdiv = BoolProperty(name="Edges Subdiv", default=False, description = "Display the the Mesh Edit Edges Subdiv Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_sharp = BoolProperty(name="Edges Sharp", default=True, description = "Display the the Mesh Edit Edges Sharp Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_freestyle = BoolProperty(name="Edges Freestyle", default=False, description = "Display the the Mesh Edit Edges Freestyle Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_rotate = BoolProperty(name="Edges Rotate", default=True, description = "Display the the Mesh Edit Edges Rotate Toolbar\nMesh Object, Edit Mode", )
    mesh_edges_misc = BoolProperty(name="Edges Misc", default=True, description = "Display the the Mesh Edit Edges MiscToolbar\nMesh Object, Edit Mode", )

    mesh_faces_general = BoolProperty(name="Faces General", default=False, description = "Display the Mesh Edit Faces General Toolbar\nMesh Object, Edit Mode", )
    mesh_faces_freestyle = BoolProperty(name="Faces Freestyle", default=False, description = "Display the Mesh Edit Faces Freestyle Toolbar\nMesh Object, Edit Mode", )
    mesh_faces_tris = BoolProperty(name="Faces Tris", default=True, description = "Display the Mesh Edit Faces Tris Toolbar\nMesh Object, Edit Mode", )
    mesh_faces_rotatemisc = BoolProperty(name="Faces Rotate Misc", default=False, description = "Display the Mesh Edit Faces Rotate Misc Toolbar\nMesh Object, Edit Mode", )

    mesh_cleanup = BoolProperty(name="Cleanup", default=False, description = "Display the Mesh Edit Cleanup Toolbar\nMesh Object, Edit Mode", )

    # primitives

    primitives_mesh = BoolProperty(name="Mesh", default=True, description = "Display the Mesh Toolbar\nDisplay is mode dependant", )
    primitives_curve = BoolProperty(name="Curve", default=False, description = "Display the Curve Toolbar\nDisplay is mode dependant", )
    primitives_surface = BoolProperty(name="Surface", default=False, description = "Display the Surface Toolbar\nDisplay is mode dependant", )
    primitives_metaball = BoolProperty(name="Metaball", default=False, description = "Display the Metaball Toolbar\nDisplay is mode dependant", )
    primitives_lamp = BoolProperty(name="Lamp", default=False, description = "Display the Lamp Toolbar\nDisplay is mode dependant", )
    primitives_other = BoolProperty(name="Other", default=True, description = "Display the Other Toolbar\nDisplay is mode dependant", )
    primitives_empties = BoolProperty(name="Empties", default=False, description = "Display the Empties Toolbar\nDisplay is mode dependant", )
    primitives_forcefield = BoolProperty(name="Force Field", default=False, description = "Display the Forcefield Toolbar\nDisplay is mode dependant", )

    # Image

    image_uv_align = BoolProperty(name="UV Align", default=True, description = "Display the UV Align Toolbar\nAll Modes", )
    image_uv_unwrap = BoolProperty(name="UV Tools - UV Unwrap", default=True, description = "Display the UV Unwrap Toolbar\nAll Modes", )
    image_uv_modify = BoolProperty(name="UV Tools - Modify UV", default=True, description = "Display the UV Modify Toolbar\nAll Modes", )

    # Tools

    tools_group = BoolProperty(name="Group", default=True, description = "Display the Group Toolbar\nDisplay is mode and content dependant", )
    tools_parent = BoolProperty(name="Parent", default=True, description = "Display the Parent Toolbar\nDisplay is mode and content dependant", )
    tools_objectdata = BoolProperty(name="Object Data", default=False, description = "Display the Object Data Toolbar\nDisplay is mode and content dependant", )
    tools_link_to_scn = BoolProperty(name="Link to SCN", default=False, description = "Display the Link to SCN dropdown box\nDisplay is mode and content dependant", )
    tools_linked_objects = BoolProperty(name="Linked Objects", default=True, description = "Display the Linked objects Toolbar\nDisplay is mode and content dependant", )
    tools_join = BoolProperty(name="Join", default=True, description = "Display the Join Toolbar\nDisplay is mode and content dependant", )
    tools_origin = BoolProperty(name="Origin", default=True, description = "Display the Origin Toolbar\nDisplay is mode and content dependant", )
    tools_shading = BoolProperty(name="Shading", default=True, description = "Display the Edit Toolbar\nDisplay is mode and content dependant", )
    tools_datatransfer = BoolProperty(name="Data Transfer", default=False, description = "Display the Edit Toolbar\nDisplay is mode and content dependant", )
    tools_relations = BoolProperty(name="Relations", default=False, description = "Display the Relations Toolbar\nDisplay is mode and content dependant", )

    # Animation

    animation_keyframes = BoolProperty(name="Keyframes", default=True, description = "Display the keyframes Toolbar\nDisplay is mode and content dependant", )
    animation_range = BoolProperty(name="Range", default=False, description = "Display the Range Toolbar\nAll Modes", )
    animation_play = BoolProperty(name="Play", default=False, description = "Display the Play Toolbar\nAll Modes", )
    animation_sync = BoolProperty(name="Sync", default=False, description = "Display the Sync Toolbar\nAll Modes", )
    animation_keyframetype = BoolProperty(name="Keyframetype", default=False, description = "Display the Keyframe Type Toolbar\nAll Modes", )
    animation_keyingset = BoolProperty(name="Keyingset", default=False, description = "Display the Keyingset Toolbar\nAll Modes", )
    
    # edit

    edit_edit = BoolProperty(name="Edit", default=True, description = "Display the Edit Toolbar\nDisplay is mode and content dependant", )
    edit_weightinedit = BoolProperty(name="Weight in Edit", default=True, description = "Display the Weight in Edit Toolbar\nDisplay is mode and content dependant", )
    edit_objectapply = BoolProperty(name="Object Apply", default=True, description = "Display the Object Apply Toolbar\nDisplay is mode and content dependant", )
    edit_objectapplydeltas = BoolProperty(name="Object Apply Deltas", default=False, description = "Display the Object Apply Deltas Toolbar\nDisplay is mode and content dependant", )
    edit_objectclear = BoolProperty(name="Object Clear", default=True, description = "Display the Object Clear Toolbar\nDisplay is mode and content dependant", )

    # misc

    misc_undoredo = BoolProperty(name="Undo / Redo", default=True, description = "Display the Undo Redo toolbar\nAll Modes", )
    misc_undohistory = BoolProperty(name="Undo History", default=True, description = "Display the Undo History Toolbar\nAll Modes", )
    misc_repeat = BoolProperty(name="Repeat", default=True, description = "Display the Repeat Toolbar\nAll Modes", )
    misc_scene = BoolProperty(name="Scene", default=True, description = "Display the Scene dropdown box", )
    misc_misc = BoolProperty(name="Misc", default=False, description = "Display the Misc Toolbar\nAll Modes", )


    def draw(self, context):
        layout = self.layout
        layout.label(text="Here you can turn on or off the single toolbars in the toolbar editor. Don't forget to save User Settings.")
        layout.label(text="The corresponding toolbar container has to be enabled in the toolbar.")

        layout.separator()

        layout.label(text="The File toolbar container")

        row = layout.row()

        row.prop(self, "file_load_save")
        row.prop(self, "file_link_append")
        row.prop(self, "file_import_menu")
        row.prop(self, "file_export_menu")

        row = layout.row()

        row.prop(self, "file_import_common")
        row.prop(self, "file_import_common2")
        row.prop(self, "file_import_uncommon")
        row.prop(self, "file_export_common")

        row = layout.row()

        row.prop(self, "file_export_common2")
        row.prop(self, "file_export_uncommon")

        row = layout.row()

        row.prop(self, "file_render")
        row.prop(self, "file_render_opengl")
        row.prop(self, "file_render_misc")
        row.prop(self, "file_window_search")

        layout.label(text="The Mesh Edit toolbar container")

        row = layout.row()

        row.prop(self, "mesh_vertices_splitconnect")
        row.prop(self, "mesh_vertices_misc")

        row.prop(self, "mesh_edges_subdiv")

        row = layout.row()

        row.prop(self, "mesh_edges_sharp")
        row.prop(self, "mesh_edges_freestyle")
        row.prop(self, "mesh_edges_rotate")
        row.prop(self, "mesh_edges_misc")

        row = layout.row()

        row.prop(self, "mesh_faces_general")
        row.prop(self, "mesh_faces_freestyle")
        row.prop(self, "mesh_faces_tris")

        row = layout.row()

        row.prop(self, "mesh_faces_rotatemisc")
        row.prop(self, "mesh_cleanup")      

        layout.label(text="The Primitives toolbar container")

        row = layout.row()

        row.prop(self, "primitives_mesh")
        row.prop(self, "primitives_curve")
        row.prop(self, "primitives_surface")
        row.prop(self, "primitives_metaball")

        row = layout.row()

        row.prop(self, "primitives_lamp")
        row.prop(self, "primitives_other")
        row.prop(self, "primitives_empties")
        row.prop(self, "primitives_forcefield")

        layout.label(text="The Image toolbar container")

        row = layout.row()

        row.prop(self, "image_uv_align")
        row.prop(self, "image_uv_unwrap")
        row.prop(self, "image_uv_modify")      
        
        layout.label(text="The Tools toolbar container")

        row = layout.row()

        row.prop(self, "tools_group")
        row.prop(self, "tools_parent")
        row.prop(self, "tools_objectdata")
        row.prop(self, "tools_link_to_scn")

        row = layout.row()

        row.prop(self, "tools_linked_objects")
        row.prop(self, "tools_join")
        row.prop(self, "tools_origin")
        row.prop(self, "tools_shading")

        row = layout.row()

        row.prop(self, "tools_datatransfer")
        row.prop(self, "tools_relations")

        layout.label(text="The Animation toolbar container")

        row = layout.row()

        row.prop(self, "animation_keyframes")
        row.prop(self, "animation_range")
        row.prop(self, "animation_play")
        row.prop(self, "animation_sync")

        row = layout.row()
        
        row.prop(self, "animation_keyframetype")
        row.prop(self, "animation_keyingset")

        layout.label(text="The Edit toolbar container")

        row = layout.row()

        row.prop(self, "edit_edit")
        row.prop(self, "edit_weightinedit")
        row.prop(self, "edit_objectapply")
        row.prop(self, "edit_objectapplydeltas")

        layout.label(text="The Misc toolbar container")

        row = layout.row()

        row.prop(addon_prefs, "misc_undoredo")
        row.prop(addon_prefs, "misc_undohistory")
        row.prop(addon_prefs, "misc_repeat")
        row.prop(self, "misc_scene")
        row.prop(self, "misc_misc")
        


class OBJECT_OT_BFA_Toolbar_prefs(Operator):
    """Display example preferences"""
    bl_idname = "object.addon_prefs_example"
    bl_label = "Addon Preferences Example"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        info = ("Boolean %r" %( addon_prefs.boolean))

        self.report({'INFO'}, info)
        print(info)

        return {'FINISHED'}


# Registration
def register():
    bpy.utils.register_class(OBJECT_OT_BFA_Toolbar_prefs)
    bpy.utils.register_class(bforartists_toolbar_settings)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_BFA_Toolbar_prefs)
    bpy.utils.unregister_class(bforartists_toolbar_settings)