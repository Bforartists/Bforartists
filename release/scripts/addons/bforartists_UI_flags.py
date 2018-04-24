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
    "name": "Bforartists UI Flags",
    "author": "Bforartists",
    "version": (1, 0),
    "blender": (2, 76, 0),
    "location": "User Preferences > Addons",
    "description": "UI Flags. DO NOT TURN OFF! This addon contains flags for various UI elements",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface",
    }

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty


class bforartists_UI_flags(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

#--------------------------------------------------------------------------------------------------------------------------

    # Subtab bools
    subtab_3dview_properties_display_obj_related = BoolProperty(name="Object related", description="Contains some object related viewport settings", default = False)
    subtab_3dview_properties_bgimg_settings = BoolProperty(name="Settings", description="Contains Settings", default = False)
    subtab_3dview_properties_bgimg_align = BoolProperty(name="Align", description="Contains Align Tools", default = False)
    subtab_3dview_properties_meshdisplay_overlay = BoolProperty(name="Overlay Options", description="Contains Overlay Settings", default = False)
    subtab_3dview_properties_meshdisplay_info = BoolProperty(name="Info Options", description="Contains Info Settings", default = False)

    # Subtab Mesh Tools
    SP_3Dview_mesh_tools_transform = BoolProperty(name="Transform", description="Transform tools", default = True)
    SP_3Dview_mesh_tools_deform = BoolProperty(name="Deform", description="Deform tools", default = False)
    SP_3Dview_mesh_tools_Modify = BoolProperty(name="Modify", description="Modify Tools", default = True)
    SP_3Dview_mesh_tools_merge_separate = BoolProperty(name="Merge / Separate", description="Merge Separate tools", default = True)
    SP_3Dview_mesh_tools_dissolve = BoolProperty(name="Dissolve", description="Contains Overlay Settings", default = False)

    # Subtab bools Rendertab panels
    SP_render_output_options = BoolProperty(name="Options", description="Contains Options", default = False)
    SP_render_metadata_stampoptions = BoolProperty(name="Stamp Options", description="Contains Options for Stamp output", default = False)
    SP_render_metadata_enabled = BoolProperty(name="Enabled Metadata", description="Contains the enabled / disabled Metadata Options", default = False)
    SP_render_dimensions_options = BoolProperty(name="Advanced", description="Contains advanced Options", default = False)
    SP_render_sampling_options = BoolProperty(name="Options", description="Contains Options", default = False)
    SP_render_light_paths_options = BoolProperty(name="Options", description="Contains Options", default = False)
    SP_render_postpro_BI_options = BoolProperty(name="Advanced", description="Contains more settings", default = False)

    #Subtab Bools Scene Panel
    SP_scene_colmanagement_render = BoolProperty(name="Render", description="Contains Color Management Render Settings", default = False)
    SP_scene_audio_options = BoolProperty(name="Options", description="Contains Audio Options", default = False)

    #Subtab Bools Object Panel
    SP_object_display_options = BoolProperty(name="Options", description="Contains some more options", default = False)
    SP_object_display_wireframecols = BoolProperty(name="Wireframe Colors", description="Contains the Wireframe color options\nRequires a selected object", default = False)

    #Subtab Bools Data Panel
    SP_data_texspace_manual = BoolProperty(name="Manual Transform", description="Contains the transform edit boxes for manual Texture space", default = False)

    #Subtab Bools Material Panel
    SP_material_options = BoolProperty(name="Options", description="Contains some more options", default = False)
    SP_material_settings_options = BoolProperty(name="Viewport Options", description="Contains some Viewport options", default = False)
    SP_material_shading_diffuseramp = BoolProperty(name="Ramp Options", description="Contains some Ramp options", default = False)
    SP_material_shading_specularramp = BoolProperty(name="Ramp Options", description="Contains some Ramp options", default = False)

    # Node Editor, text or icon buttons

    Node_text_or_icon = BoolProperty(name="Icon / Text Buttons", description="Display the buttons in the Node editor tool shelf as text or iconbuttons\nSave User preferences to save the current state", default = False)

    # Compact paint panel

    brushpanel_display_options = BoolProperty(name="Display Options", description="Contains Display options for the Brush panel", default = False)
    brushpanel_hide_colorpicker = BoolProperty(name="Hide Colorpicker", description="Here you can hide the color picker", default = True)
    brushpanel_hide_palette = BoolProperty(name="Hide Palette", description="Here you can display a much smaller brush menu", default = True)

#------------------------------------------------------------------------------------------------------------------------------


    def draw(self, context):
        layout = self.layout
        layout.label(text="This flags are used for various options in the Bforartists UI")
        layout.label(text="Here you can adjust the default states if you want.")

        layout.separator()

        layout.label(text="Subtab bools")

        row = layout.row()

        row.prop(self, "subtab_3dview_properties_display_obj_related")
        row.prop(self, "subtab_3dview_properties_bgimg_settings")
        row.prop(self, "subtab_3dview_properties_bgimg_align")

        row = layout.row()

        row.prop(self, "subtab_3dview_properties_meshdisplay_overlay")
        row.prop(self, "subtab_3dview_properties_meshdisplay_info")

        # ---------------------------

        layout.label(text="Subtab Mesh Tools")

        row = layout.row()

        row.prop(self, "SP_3Dview_mesh_tools_transform")
        row.prop(self, "SP_3Dview_mesh_tools_deform")
        row.prop(self, "SP_3Dview_mesh_tools_Modify")
        row.prop(self, "SP_3Dview_mesh_tools_merge_separate")

        row = layout.row()

        row.prop(self, "SP_3Dview_mesh_tools_dissolve")

        # ---------------------------

        layout.label(text="Subtab bools Rendertab panels")

        row = layout.row()

        row.prop(self, "SP_render_output_options")
        row.prop(self, "SP_render_metadata_stampoptions")
        row.prop(self, "SP_render_metadata_enabled")
        row.prop(self, "SP_render_dimensions_options")

        row = layout.row()

        row.prop(self, "SP_render_sampling_options")
        row.prop(self, "SP_render_light_paths_options")
        row.prop(self, "SP_render_postpro_BI_options")

        # ---------------------------

        layout.label(text="Subtab Bools Scene Panel")

        row = layout.row()

        row.prop(self, "SP_scene_colmanagement_render")
        row.prop(self, "SP_scene_audio_options")

        layout.label(text="Subtab Bools Object Panel")

        row = layout.row()

        row.prop(self, "SP_object_display_options")  
        row.prop(self, "SP_object_display_wireframecols")  

        # ---------------------------

        layout.label(text="Subtab Bools Data Panel")

        row = layout.row()

        row.prop(self, "SP_data_texspace_manual")

        # ---------------------------

        layout.label(text="Subtab Bools Material Panel")

        row = layout.row()

        row.prop(self, "SP_material_options")
        row.prop(self, "SP_material_settings_options")
        row.prop(self, "SP_material_shading_diffuseramp")
        row.prop(self, "SP_material_shading_specularramp")

        row = layout.row()

        row.prop(self, "Node_text_or_icon")

        layout.label(text="Compact Brush Panel")

        row = layout.row()

        row.prop(self, "brushpanel_display_options")
        row.prop(self, "brushpanel_hide_colorpicker")
        row.prop(self, "brushpanel_hide_palette")
        

class OBJECT_OT_BFA_UI_flags(Operator):
    """Display UI Flags"""
    bl_idname = "object.addon_prefs_ui_flags"
    bl_label = "Bforartists UI Flags"
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
    bpy.utils.register_class(OBJECT_OT_BFA_UI_flags)
    bpy.utils.register_class(bforartists_UI_flags)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_BFA_UI_flags)
    bpy.utils.unregister_class(bforartists_UI_flags)