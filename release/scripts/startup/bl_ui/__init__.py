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

# <pep8 compliant>

# note, properties_animviz is a helper module only.

if "bpy" in locals():
    from importlib import reload
    for val in _modules_loaded.values():
        reload(val)
    del reload
_modules = [
    "properties_animviz",
    "properties_constraint",
    "properties_data_armature",
    "properties_data_bone",
    "properties_data_camera",
    "properties_data_curve",
    "properties_data_empty",
    "properties_data_lamp",
    "properties_data_lattice",
    "properties_data_mesh",
    "properties_data_metaball",
    "properties_data_modifier",
    "properties_data_speaker",
    "properties_game",
    "properties_mask_common",
    "properties_material",
    "properties_object",
    "properties_paint_common",
    "properties_grease_pencil_common",
    "properties_particle",
    "properties_physics_cloth",
    "properties_physics_common",
    "properties_physics_dynamicpaint",
    "properties_physics_field",
    "properties_physics_fluid",
    "properties_physics_rigidbody",
    "properties_physics_rigidbody_constraint",
    "properties_physics_smoke",
    "properties_physics_softbody",
    "properties_render",
    "properties_render_layer",
    "properties_scene",
    "properties_texture",
    "properties_world",
    "space_clip",
    "space_console",
    "space_dopesheet",
    "space_filebrowser",
    "space_graph",
    "space_image",
    "space_info",
    "space_logic",
    "space_nla",
    "space_node",
    "space_outliner",
    "space_properties",
    "space_sequencer",
    "space_text",
    "space_time",
    "space_userpref",
    "space_view3d",
    "space_view3d_toolbar",
    "space_toolbar",
]

import bpy

if bpy.app.build_options.freestyle:
    _modules.append("properties_freestyle")
__import__(name=__name__, fromlist=_modules)
_namespace = globals()
_modules_loaded = {name: _namespace[name] for name in _modules if name != "bpy"}
del _namespace

# bfa - text or icon buttons, the prop
class UITweaksData(bpy.types.PropertyGroup):
    icon_or_text = bpy.props.BoolProperty(name="Icon / Text Buttons", description="Displays some buttons as text or iconbuttons", default = True) # Our prop

############################ Toolbar props File #################################

# bfa - Load Save
class UIToolbarLoadsave(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Load / Save", description="Display the Load / Save Toolbar", default = True)

# bfa - Link Append
class UIToolbarLinkappend(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Link Append", description="Display the Link Append Toolbar", default = True)

# bfa - Import common
class UIToolbarImportCommon(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Import common", description="Display the Import common Toolbar", default = True)

# bfa - Import uncommon
class UIToolbarImportUncommon(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Import uncommon", description="Display the Import uncommon Toolbar", default = True)

# bfa - Export common
class UIToolbarExportCommon(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Export common", description="Display the Export common Toolbar", default = True)

# bfa - Export uncommon
class UIToolbarExportUncommon(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Export uncommon", description="Display the Export uncommon Toolbar", default = True)

# bfa - Render
class UIToolbarFileRender(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Render", description="Display the Render Toolbar", default = True)

# bfa - Render Víew
class UIToolbarFileRenderView(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Render Open GL", description="Display the Render View Toolbar", default = True)

# bfa - Render Misc
class UIToolbarFileRenderMisc(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Render Misc", description="Display the Render Misc Toolbar", default = True)

############################ Toolbar props View #################################

# bfa - Align
class UIToolbarViewAlign(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Align", description="Display the Align Toolbar", default = True)

# bfa - Camera
class UIToolbarViewCamera(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Camera", description="Display the Camera Toolbar", default = True)

############################ Toolbar props Primitives #################################

# bfa - Mesh
class UIToolbarPrimitivesMesh(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Mesh", description="Display the Mesh Toolbar\nThis toolbar is just visible in Object and Edit mode", default = True)

# bfa - Curve
class UIToolbarPrimitivesCurve(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Curve", description="Display the Curve Toolbar\nThis toolbar is just visible in Object and Edit mode", default = True)

# bfa - Surface
class UIToolbarPrimitivesSurface(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Surface", description="Display the Surface Toolbar\nThis toolbar is just visible in Object and Edit mode", default = True)

# bfa - Metaball
class UIToolbarPrimitivesMetaball(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Metaball", description="Display the Metaball Toolbar\nThis toolbar is just visible in Object and Edit mode", default = True)

# bfa - Lamp
class UIToolbarPrimitivesLamp(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Lamp", description="Display the Lamp Toolbar\nThis toolbar is just visible in Object mode", default = True)

# bfa - Other
class UIToolbarPrimitivesOther(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Other", description="Display the Other Toolbar\nThis toolbar is just visible in Object mode", default = True)

# bfa - Empties
class UIToolbarPrimitivesEmpties(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Empties", description="Display the Empties Toolbar\nThis toolbar is just visible in Object mode", default = True)

# bfa - Force Field
class UIToolbarPrimitivesForcefield(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Force Field", description="Display the Force Field Toolbar\nThis toolbar is just visible in Object mode", default = True)

############################ Toolbar props image #################################

# bfa - Common
class UIToolbarImageUVCommon(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="UV Common", description="Display the UV Common Toolbar", default = True)

# bfa - Misc
class UIToolbarImageUVMisc(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="UV Misc", description="Display the UV Misc Toolbar", default = True)

# bfa - Align
class UIToolbarImageUVAlign(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="UV Align", description="Display the UV Align Toolbar", default = True)

############################ Toolbar props Tools #################################

# bfa - History
class UIToolbarToolsHistory(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="History", description="Display the History Toolbar", default = True)

# bfa - Relations
class UIToolbarToolsRelations(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Relations", description="Display the Relations Toolbar\nThis tools are just visible in Object mode", default = True)

# bfa - Edit
class UIToolbarToolsEdit(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Edit", description="Display the Edit Toolbar\nThis tools are just visible in Object and Edit mode", default = True)

############################ Toolbar props animation #################################

# bfa - Keyframes
class UIToolbarAnimationKeyframes(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Keyframes", description="Display the Keyframes Toolbar\nThis tools are just visible in Object and Pose mode", default = True)

# bfa - Range
class UIToolbarAnimationRange(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Range", description="Display the Range Toolbar", default = True)

# bfa - Play
class UIToolbarAnimationPlay(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Play", description="Display the Play Toolbar", default = True)

# bfa - Sync
class UIToolbarAnimationSync(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Sync", description="Display the Sync Toolbar", default = True)

 # bfa - Keyingset
class UIToolbarAnimationKeyingset(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Keyingset", description="Display the Keyingset Toolbar", default = True)

############################ Toolbar props edit #################################

# bfa - Edit
class UIToolbarEditEdit(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Edit", description="Display the Edit Toolbar\nThis tools are just visible in Edit mode", default = True)

# bfa - Weight in Edit
class UIToolbarEditWeight(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Weigth in Edit", description="Display the Weight in Edit Toolbar\nThis tools are just visible in Edit and Weightpaint mode", default = True)

############################ Toolbar props misc #################################

# bfa - Misc
class UIToolbarMiscMisc(bpy.types.PropertyGroup):
    bool = bpy.props.BoolProperty(name="Misc", description="Display the Misc Toolbar", default = True)


#################################


def register():
    
    # Subtab bools
    bpy.types.WindowManager.subtab_3dview_properties_view_lock = bpy.props.BoolProperty(name="Lock", description="Contains the Lock Items", default = False)
    bpy.types.WindowManager.subtab_3dview_properties_display_misc = bpy.props.BoolProperty(name="Miscellaneous", description="Contains miscellaneous settings", default = False)
    bpy.types.WindowManager.subtab_3dview_properties_bgimg_settings = bpy.props.BoolProperty(name="Settings", description="Contains Settings", default = False)
    bpy.types.WindowManager.subtab_3dview_properties_bgimg_align = bpy.props.BoolProperty(name="Align", description="Contains Align Tools", default = False)
    bpy.types.WindowManager.subtab_3dview_properties_meshdisplay_overlay = bpy.props.BoolProperty(name="Overlay Options", description="Contains Overlay Settings", default = False)
    bpy.types.WindowManager.subtab_3dview_properties_meshdisplay_info = bpy.props.BoolProperty(name="Info Options", description="Contains Info Settings", default = False)

    # Subtab bools Rendertab panels
    bpy.types.WindowManager.SP_render_render_options = bpy.props.BoolProperty(name="Options", description="Contains Options", default = False)
    bpy.types.WindowManager.SP_render_output_options = bpy.props.BoolProperty(name="Options", description="Contains Options", default = False)
    bpy.types.WindowManager.SP_render_metadata_stampoptions = bpy.props.BoolProperty(name="Stamp Options", description="Contains Options for Stamp output", default = False)
    bpy.types.WindowManager.SP_render_metadata_enabled = bpy.props.BoolProperty(name="Enabled Metadata", description="Contains the enabled / disabled Metadata Options", default = False)
    bpy.types.WindowManager.SP_render_dimensions_options = bpy.props.BoolProperty(name="Advanced", description="Contains advanced Options", default = False)
    bpy.types.WindowManager.SP_render_sampling_options = bpy.props.BoolProperty(name="Options", description="Contains Options", default = False)
    bpy.types.WindowManager.SP_render_light_paths_options = bpy.props.BoolProperty(name="Options", description="Contains Options", default = False)
    bpy.types.WindowManager.SP_render_sampling_vomume = bpy.props.BoolProperty(name="Options", description="Contains Volume Sampling Settings", default = False)
    bpy.types.WindowManager.SP_render_postpro_BI_options = bpy.props.BoolProperty(name="Advanced", description="Contains more settings", default = False)

    #Subtab Bools Scene Panel
    bpy.types.WindowManager.SP_scene_colmanagement_render = bpy.props.BoolProperty(name="Render", description="Contains Color Management Render Settings", default = False)
    bpy.types.WindowManager.SP_scene_audio_options = bpy.props.BoolProperty(name="Options", description="Contains Audio Options", default = False)

    #Subtab Bools Object Panel
    bpy.types.WindowManager.SP_object_display_options = bpy.props.BoolProperty(name="Options", description="Contains some more options", default = False)

    #Subtab Bools Data Panel
    bpy.types.WindowManager.SP_data_texspace_manual = bpy.props.BoolProperty(name="Manual Transform", description="Contains the transform edit boxes for manual Texture space", default = False)

    #Subtab Bools Material Panel
    bpy.types.WindowManager.SP_material_options = bpy.props.BoolProperty(name="Options", description="Contains some more options", default = False)
    bpy.types.WindowManager.SP_material_settings_options = bpy.props.BoolProperty(name="Viewport Options", description="Contains some Viewport options", default = False)
    bpy.types.WindowManager.SP_material_shading_diffuseramp = bpy.props.BoolProperty(name="Ramp Options", description="Contains some Ramp options", default = False)
    bpy.types.WindowManager.SP_material_shading_specularramp = bpy.props.BoolProperty(name="Ramp Options", description="Contains some Ramp options", default = False)


    # bfa - Our data block for icon or text buttons
    bpy.utils.register_class(UITweaksData) # Our data block
    bpy.types.Scene.UItweaks = bpy.props.PointerProperty(type=UITweaksData) # Bind reference of type of our data block to type Scene objects

    ############################ Toolbar props File #################################

    # bfa - Load Save
    bpy.utils.register_class(UIToolbarLoadsave) # Our data block
    bpy.types.Scene.toolbar_file_loadsave = bpy.props.PointerProperty(type=UIToolbarLoadsave) # Bind reference of type of our data block to type Scene objects

    # bfa - Link Append
    bpy.utils.register_class(UIToolbarLinkappend) # Our data block
    bpy.types.Scene.toolbar_file_linkappend = bpy.props.PointerProperty(type=UIToolbarLinkappend)

    # bfa - Import common
    bpy.utils.register_class(UIToolbarImportCommon) # Our data block
    bpy.types.Scene.toolbar_file_importcommon = bpy.props.PointerProperty(type=UIToolbarImportCommon)

    # bfa - Import uncommon
    bpy.utils.register_class(UIToolbarImportUncommon) # Our data block
    bpy.types.Scene.toolbar_file_importuncommon = bpy.props.PointerProperty(type=UIToolbarImportUncommon)

    # bfa - Export common
    bpy.utils.register_class(UIToolbarExportCommon) # Our data block
    bpy.types.Scene.toolbar_file_exportcommon = bpy.props.PointerProperty(type=UIToolbarExportCommon)

    # bfa - Export uncommon
    bpy.utils.register_class(UIToolbarExportUncommon) # Our data block
    bpy.types.Scene.toolbar_file_exportuncommon = bpy.props.PointerProperty(type=UIToolbarExportUncommon)

    # bfa - Render
    bpy.utils.register_class(UIToolbarFileRender) # Our data block
    bpy.types.Scene.toolbar_file_render = bpy.props.PointerProperty(type=UIToolbarFileRender)

    # bfa - Render view
    bpy.utils.register_class(UIToolbarFileRenderView) # Our data block
    bpy.types.Scene.toolbar_file_render_view = bpy.props.PointerProperty(type=UIToolbarFileRenderView)

    # bfa - Render misc
    bpy.utils.register_class(UIToolbarFileRenderMisc) # Our data block
    bpy.types.Scene.toolbar_file_render_misc = bpy.props.PointerProperty(type=UIToolbarFileRenderMisc)


    ############################ Toolbar props View #################################

    # bfa - Align
    bpy.utils.register_class(UIToolbarViewAlign) # Our data block
    bpy.types.Scene.toolbar_view_align = bpy.props.PointerProperty(type=UIToolbarViewAlign) 

    # bfa - Camera
    bpy.utils.register_class(UIToolbarViewCamera) # Our data block
    bpy.types.Scene.toolbar_view_camera = bpy.props.PointerProperty(type=UIToolbarViewCamera)

    ############################ Toolbar props Primitives #################################

    # bfa - Mesh
    bpy.utils.register_class(UIToolbarPrimitivesMesh) # Our data block
    bpy.types.Scene.toolbar_primitives_mesh = bpy.props.PointerProperty(type=UIToolbarPrimitivesMesh)

    # bfa - Curve
    bpy.utils.register_class(UIToolbarPrimitivesCurve) # Our data block
    bpy.types.Scene.toolbar_primitives_curve = bpy.props.PointerProperty(type=UIToolbarPrimitivesCurve)

    # bfa - Surface
    bpy.utils.register_class(UIToolbarPrimitivesSurface) # Our data block
    bpy.types.Scene.toolbar_primitives_surface = bpy.props.PointerProperty(type=UIToolbarPrimitivesSurface)

    # bfa - Metaball
    bpy.utils.register_class(UIToolbarPrimitivesMetaball) # Our data block
    bpy.types.Scene.toolbar_primitives_metaball = bpy.props.PointerProperty(type=UIToolbarPrimitivesMetaball)

    # bfa - Lamp
    bpy.utils.register_class(UIToolbarPrimitivesLamp) # Our data block
    bpy.types.Scene.toolbar_primitives_lamp = bpy.props.PointerProperty(type=UIToolbarPrimitivesLamp)

    # bfa - Other
    bpy.utils.register_class(UIToolbarPrimitivesOther) # Our data block
    bpy.types.Scene.toolbar_primitives_other = bpy.props.PointerProperty(type=UIToolbarPrimitivesOther)

    # bfa - Empties
    bpy.utils.register_class(UIToolbarPrimitivesEmpties) # Our data block
    bpy.types.Scene.toolbar_primitives_empties = bpy.props.PointerProperty(type=UIToolbarPrimitivesEmpties)

    # bfa - Force Field
    bpy.utils.register_class(UIToolbarPrimitivesForcefield) # Our data block
    bpy.types.Scene.toolbar_primitives_forcefield = bpy.props.PointerProperty(type=UIToolbarPrimitivesForcefield)

    ############################ Toolbar props Image #################################

    # bfa - File
    bpy.utils.register_class(UIToolbarImageUVCommon) # Our data block
    bpy.types.Scene.toolbar_image_uvcommon = bpy.props.PointerProperty(type=UIToolbarImageUVCommon)

    # bfa - Misc
    bpy.utils.register_class(UIToolbarImageUVMisc) # Our data block
    bpy.types.Scene.toolbar_image_uvmisc = bpy.props.PointerProperty(type=UIToolbarImageUVMisc)

    # bfa - Align
    bpy.utils.register_class(UIToolbarImageUVAlign) # Our data block
    bpy.types.Scene.toolbar_image_uvalign = bpy.props.PointerProperty(type=UIToolbarImageUVAlign)

    ############################ Toolbar props Tools #################################

    # bfa - History
    bpy.utils.register_class(UIToolbarToolsHistory) # Our data block
    bpy.types.Scene.toolbar_tools_history = bpy.props.PointerProperty(type=UIToolbarToolsHistory)

    # bfa - Relations
    bpy.utils.register_class(UIToolbarToolsRelations) # Our data block
    bpy.types.Scene.toolbar_tools_relations = bpy.props.PointerProperty(type=UIToolbarToolsRelations)

    # bfa - Edit
    bpy.utils.register_class(UIToolbarToolsEdit) # Our data block
    bpy.types.Scene.toolbar_tools_edit = bpy.props.PointerProperty(type=UIToolbarToolsEdit)

    ############################ Toolbar props animation #################################

    # bfa - Keyframes
    bpy.utils.register_class(UIToolbarAnimationKeyframes) # Our data block
    bpy.types.Scene.toolbar_animation_keyframes = bpy.props.PointerProperty(type=UIToolbarAnimationKeyframes)
    
    # bfa - Range
    bpy.utils.register_class(UIToolbarAnimationRange) # Our data block
    bpy.types.Scene.toolbar_animation_range = bpy.props.PointerProperty(type=UIToolbarAnimationRange)
    
    # bfa - Play
    bpy.utils.register_class(UIToolbarAnimationPlay) # Our data block
    bpy.types.Scene.toolbar_animation_play = bpy.props.PointerProperty(type=UIToolbarAnimationPlay)
    
    # bfa - Animation
    bpy.utils.register_class(UIToolbarAnimationSync) # Our data block
    bpy.types.Scene.toolbar_animation_sync = bpy.props.PointerProperty(type=UIToolbarAnimationSync)
    
    # bfa - Animation
    bpy.utils.register_class(UIToolbarAnimationKeyingset) # Our data block
    bpy.types.Scene.toolbar_animation_keyingset = bpy.props.PointerProperty(type=UIToolbarAnimationKeyingset)

    ############################ Toolbar props edit #################################

    # bfa - Edit
    bpy.utils.register_class(UIToolbarEditEdit) # Our data block
    bpy.types.Scene.toolbar_edit_edit= bpy.props.PointerProperty(type=UIToolbarEditEdit)

    # bfa - Weight in Edit
    bpy.utils.register_class(UIToolbarEditWeight) # Our data block
    bpy.types.Scene.toolbar_edit_weight= bpy.props.PointerProperty(type=UIToolbarEditWeight)

    ############################ Toolbar props misc #################################

    # bfa - Misc
    bpy.utils.register_class(UIToolbarMiscMisc) # Our data block
    bpy.types.Scene.toolbar_misc_misc = bpy.props.PointerProperty(type=UIToolbarMiscMisc)

    #######################################################################

    bpy.utils.register_module(__name__)

    # space_userprefs.py
    from bpy.props import StringProperty, EnumProperty
    from bpy.types import WindowManager

    def addon_filter_items(self, context):
        import addon_utils

        items = [('All', "All", "All Add-ons"),
                 ('User', "User", "All Add-ons Installed by User"),
                 ('Enabled', "Enabled", "All Enabled Add-ons"),
                 ('Disabled', "Disabled", "All Disabled Add-ons"),
                 ]

        items_unique = set()

        for mod in addon_utils.modules(refresh=False):
            info = addon_utils.module_bl_info(mod)
            items_unique.add(info["category"])

        items.extend([(cat, cat, "") for cat in sorted(items_unique)])
        return items

    WindowManager.addon_search = StringProperty(
            name="Search",
            description="Search within the selected filter",
            options={'TEXTEDIT_UPDATE'},
            )
    WindowManager.addon_filter = EnumProperty(
            items=addon_filter_items,
            name="Category",
            description="Filter addons by category",
            )

    WindowManager.addon_support = EnumProperty(
            items=[('OFFICIAL', "Official", "Officially supported"),
                   ('COMMUNITY', "Community", "Maintained by community developers"),
                   ('TESTING', "Testing", "Newly contributed scripts (excluded from release builds)")
                   ],
            name="Support",
            description="Display support level",
            default={'OFFICIAL', 'COMMUNITY'},
            options={'ENUM_FLAG'},
            )
    # done...


def unregister():

    # Subtab Bools
    del bpy.types.WindowManager.subtab_3dview_properties_view_lock # Unregister our flag when unregister.    
    del bpy.types.WindowManager.subtab_3dview_properties_display_misc # Unregister our flag when unregister.  
    del bpy.types.WindowManager.subtab_3dview_properties_bgimg_settings
    del bpy.types.WindowManager.subtab_3dview_properties_bgimg_align
    del bpy.types.WindowManager.subtab_3dview_properties_meshdisplay_overlay
    del bpy.types.WindowManager.subtab_3dview_properties_meshdisplay_info

    # Subtab bools Rendertab panels
    del bpy.types.WindowManager.SP_render_render_options
    del bpy.types.WindowManager.SP_render_output_options
    del bpy.types.WindowManager.SP_render_metadata_stampoptions
    del bpy.types.WindowManager.SP_render_metadata_enabled
    del bpy.types.WindowManager.SP_render_dimensions_options
    del bpy.types.WindowManager.SP_render_sampling_options
    del bpy.types.WindowManager.SP_render_light_paths_options
    del bpy.types.WindowManager.SP_render_sampling_vomume
    del bpy.types.WindowManager.SP_render_postpro_BI_options

    #Subtab Bools Scene Panel
    del bpy.types.WindowManager.SP_scene_colmanagement_render
    del bpy.types.WindowManager.SP_scene_audio_options

    #Subtab Bools Object Panel
    del bpy.types.WindowManager.SP_object_display_options

    #Subtab Bools Data Panel
    del bpy.types.WindowManager.SP_data_texspace_manual

    #Subtab Bools Material Panel
    del bpy.types.WindowManager.SP_material_options   
    del bpy.types.WindowManager.SP_material_settings_options   
    del bpy.types.WindowManager.SP_material_shading_diffuseramp
    del bpy.types.WindowManager.SP_material_shading_specularramp

    # bfa - Our data block for icon or text buttons
    bpy.utils.unregister_class(UITweaksData) # Our data block
    del bpy.types.Scene.UItweaks # Unregister our data block when unregister.

    ############################ Toolbar props File #################################

    bpy.utils.unregister_class(UIToolbarLoadsave) # Our data block
    bpy.utils.unregister_class(UIToolbarLinkappend)
    bpy.utils.unregister_class(UIToolbarImportCommon)
    bpy.utils.unregister_class(UIToolbarImportUncommon)
    bpy.utils.unregister_class(UIToolbarExportCommon)
    bpy.utils.unregister_class(UIToolbarExportUncommon)
    bpy.utils.unregister_class(UIToolbarFileRender)

    ############################ Toolbar props File #################################

    bpy.utils.unregister_class(UIToolbarViewAlign)
    bpy.utils.unregister_class(UIToolbarViewCamera)

    ############################ Toolbar props Primitives #################################

    bpy.utils.unregister_class(UIToolbarPrimitivesMesh)
    bpy.utils.unregister_class(UIToolbarPrimitivesCurve)
    bpy.utils.unregister_class(UIToolbarPrimitivesSurface)
    bpy.utils.unregister_class(UIToolbarPrimitivesMetaball)
    bpy.utils.unregister_class(UIToolbarPrimitivesLamp)
    bpy.utils.unregister_class(UIToolbarPrimitivesOther)
    bpy.utils.unregister_class(UIToolbarPrimitivesEmpties)
    bpy.utils.unregister_class(UIToolbarPrimitivesForcefield)

    ############################ Toolbar props Image #################################

    bpy.utils.unregister_class(UIToolbarImageUVCommon)
    bpy.utils.unregister_class(UIToolbarImageUVMisc)
    bpy.utils.unregister_class(UIToolbarImageUVAlign)

    ############################ Toolbar props Tools #################################

    bpy.utils.unregister_class(UIToolbarToolsHistory)
    bpy.utils.unregister_class(UIToolbarToolsRelations)
    bpy.utils.unregister_class(UIToolbarToolsEdit)

    ############################ Toolbar props Animation #################################

    bpy.utils.unregister_class(UIToolbarAnimationKeyframes)
    bpy.utils.unregister_class(UIToolbarAnimationRange)
    bpy.utils.unregister_class(UIToolbarAnimationPlay)
    bpy.utils.unregister_class(UIToolbarAnimationSync)
    bpy.utils.unregister_class(UIToolbarAnimationKeyingset)

    ############################ Toolbar props Edit #################################

    bpy.utils.unregister_class(UIToolbarEditEdit)
    bpy.utils.unregister_class(UIToolbarEditWeight)

    ############################ Toolbar props Misc #################################

    bpy.utils.unregister_class(UIToolbarMiscMisc)

    ############################################################################

    bpy.utils.unregister_module(__name__)

# Define a default UIList, when a list does not need any custom drawing...
# Keep in sync with its #defined name in UI_interface.h
class UI_UL_list(bpy.types.UIList):
    # These are common filtering or ordering operations (same as the default C ones!).
    @staticmethod
    def filter_items_by_name(pattern, bitflag, items, propname="name", flags=None, reverse=False):
        """
        Set FILTER_ITEM for items which name matches filter_name one (case-insensitive).
        pattern is the filtering pattern.
        propname is the name of the string property to use for filtering.
        flags must be a list of integers the same length as items, or None!
        return a list of flags (based on given flags if not None),
        or an empty list if no flags were given and no filtering has been done.
        """
        import fnmatch

        if not pattern or not items:  # Empty pattern or list = no filtering!
            return flags or []

        if flags is None:
            flags = [0] * len(items)

        # Implicitly add heading/trailing wildcards.
        pattern = "*" + pattern + "*"

        for i, item in enumerate(items):
            name = getattr(item, propname, None)
            # This is similar to a logical xor
            if bool(name and fnmatch.fnmatchcase(name, pattern)) is not bool(reverse):
                flags[i] |= bitflag
        return flags

    @staticmethod
    def sort_items_helper(sort_data, key, reverse=False):
        """
        Common sorting utility. Returns a neworder list mapping org_idx -> new_idx.
        sort_data must be an (unordered) list of tuples [(org_idx, ...), (org_idx, ...), ...].
        key must be the same kind of callable you would use for sorted() builtin function.
        reverse will reverse the sorting!
        """
        sort_data.sort(key=key, reverse=reverse)
        neworder = [None] * len(sort_data)
        for newidx, (orgidx, *_) in enumerate(sort_data):
            neworder[orgidx] = newidx
        return neworder

    @classmethod
    def sort_items_by_name(cls, items, propname="name"):
        """
        Re-order items using their names (case-insensitive).
        propname is the name of the string property to use for sorting.
        return a list mapping org_idx -> new_idx,
               or an empty list if no sorting has been done.
        """
        _sort = [(idx, getattr(it, propname, "")) for idx, it in enumerate(items)]
        return cls.sort_items_helper(_sort, lambda e: e[1].lower())


bpy.utils.register_class(UI_UL_list)
