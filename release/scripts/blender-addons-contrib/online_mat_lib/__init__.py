#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/
#  or write to the Free Software Foundation, Inc., 51 Franklin Street,
#  Fifth Floor, Boston, MA 02110-1301, USA.
#
#  The Original Code is Copyright (C) 2012 by Peter Cassetta    ###
#  All rights reserved.
#
#  Contact:                        matlib@peter.cassetta.info   ###
#  Information:  http://peter.cassetta.info/material-library/   ###
#
#  The Original Code is: all of this file.
#
#  Contributor(s): Peter Cassetta.
#
#  ***** END GPL LICENSE BLOCK *****

bl_info = {
    "name": "Online Material Library",
    "author": "Peter Cassetta",
    "version": (0, 6, 1),
    "blender": (2, 74, 5),
    "location": "Properties > Material > Online Material Library",
    "description": "Browse and download materials from online CC0 libraries.",
    "warning": "Beta version",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Material/Online_Material_Library",
    "tracker_url": "",
    "category": "Material"}

node_types = {
    'SHADER': {
        'EMISSION': 'ShaderNodeEmission',
        'HOLDOUT': 'ShaderNodeHoldout',
        'OUTPUT': 'ShaderNodeOutput',
        'HAIR_INFO': 'ShaderNodeHairInfo',
        'ATTRIBUTE': 'ShaderNodeAttribute',
        'BACKGROUND': 'ShaderNodeBackground',
        'TEX_VORONOI': 'ShaderNodeTexVoronoi',
        'OBJECT_INFO': 'ShaderNodeObjectInfo',
        'MATH': 'ShaderNodeMath',
        'BSDF_TRANSPARENT': 'ShaderNodeBsdfTransparent',
        'VALTORGB': 'ShaderNodeValToRGB',
        'INVERT': 'ShaderNodeInvert',
        'PARTICLE_INFO': 'ShaderNodeParticleInfo',
        'BSDF_VELVET': 'ShaderNodeBsdfVelvet',
        'TEX_MAGIC': 'ShaderNodeTexMagic',
        'WAVELENGTH': 'ShaderNodeWavelength',
        'SEPHSV': 'ShaderNodeSeparateHSV',
        'MIX_SHADER': 'ShaderNodeMixShader',
        'TEX_GRADIENT': 'ShaderNodeTexGradient',
        'OUTPUT_WORLD': 'ShaderNodeOutputWorld',
        'TEX_SKY': 'ShaderNodeTexSky',
        'SQUEEZE': 'ShaderNodeSqueeze',
        'LIGHT_PATH': 'ShaderNodeLightPath',
        'BSDF_TOON': 'ShaderNodeBsdfToon',
        'TEX_CHECKER': 'ShaderNodeTexChecker',
        'AMBIENT_OCCLUSION': 'ShaderNodeAmbientOcclusion',
        'BSDF_GLASS': 'ShaderNodeBsdfGlass',
        'SEPRGB': 'ShaderNodeSeparateRGB',
        'MATERIAL': 'ShaderNodeMaterial',
        'TEX_WAVE': 'ShaderNodeTexWave',
        'BRIGHTCONTRAST': 'ShaderNodeBrightContrast',
        'CAMERA': 'ShaderNodeCameraData',
        'HUE_SAT': 'ShaderNodeHueSaturation',
        'OUTPUT_LAMP': 'ShaderNodeOutputLamp',
        'BSDF_DIFFUSE': 'ShaderNodeBsdfDiffuse',
        'VALUE': 'ShaderNodeValue',
        'BSDF_ANISOTROPIC': 'ShaderNodeBsdfAnisotropic',
        'NEW_GEOMETRY': 'ShaderNodeNewGeometry',
        'MAPPING': 'ShaderNodeMapping',
        'TEX_IMAGE': 'ShaderNodeTexImage',
        'LIGHT_FALLOFF': 'ShaderNodeLightFalloff',
        'COMBRGB': 'ShaderNodeCombineRGB',
        'GAMMA': 'ShaderNodeGamma',
        'BLACKBODY': 'ShaderNodeBlackbody',
        'TEX_COORD': 'ShaderNodeTexCoord',
        'COMBHSV': 'ShaderNodeCombineHSV',
        'TEX_BRICK': 'ShaderNodeTexBrick',
        'BUMP': 'ShaderNodeBump',
        'SCRIPT': 'ShaderNodeScript',
        'VECT_MATH': 'ShaderNodeVectorMath',
        'TEX_NOISE': 'ShaderNodeTexNoise',
        'CURVE_VEC': 'ShaderNodeVectorCurve',
        'GEOMETRY': 'ShaderNodeGeometry',
        'BSDF_TRANSLUCENT': 'ShaderNodeBsdfTranslucent',
        'CURVE_RGB': 'ShaderNodeRGBCurve',
        'TEX_ENVIRONMENT': 'ShaderNodeTexEnvironment',
        'OUTPUT_MATERIAL': 'ShaderNodeOutputMaterial',
        'BSDF_HAIR': 'ShaderNodeBsdfHair',
        'RGB': 'ShaderNodeRGB',
        'WIREFRAME': 'ShaderNodeWireframe',
        'MIX_RGB': 'ShaderNodeMixRGB',
        'LAYER_WEIGHT': 'ShaderNodeLayerWeight',
        'SUBSURFACE_SCATTERING': 'ShaderNodeSubsurfaceScattering',
        'BSDF_REFRACTION': 'ShaderNodeBsdfRefraction',
        'NORMAL': 'ShaderNodeNormal',
        'GROUP': 'ShaderNodeGroup',
        'FRESNEL': 'ShaderNodeFresnel',
        'BSDF_GLOSSY': 'ShaderNodeBsdfGlossy',
        'TANGENT': 'ShaderNodeTangent',
        'ADD_SHADER': 'ShaderNodeAddShader',
        'TEXTURE': 'ShaderNodeTexture',
        'VECT_TRANSFORM': 'ShaderNodeVectorTransform',
        'MATERIAL_EXT': 'ShaderNodeExtendedMaterial',
        'TEX_MUSGRAVE': 'ShaderNodeTexMusgrave',
        'NORMAL_MAP': 'ShaderNodeNormalMap',
        'RGBTOBW': 'ShaderNodeRGBToBW'},
    'COMPOSITING': {
        'KEYING': 'CompositorNodeKeying',
        'TRANSFORM': 'CompositorNodeTransform',
        'MAP_VALUE': 'CompositorNodeMapValue',
        'DESPECKLE': 'CompositorNodeDespeckle',
        'IMAGE': 'CompositorNodeImage',
        'SEPHSVA': 'CompositorNodeSepHSVA',
        'VALUE': 'CompositorNodeValue',
        'MATH': 'CompositorNodeMath',
        'COLORCORRECTION': 'CompositorNodeColorCorrection',
        'VALTORGB': 'CompositorNodeValToRGB',
        'INVERT': 'CompositorNodeInvert',
        'ALPHAOVER': 'CompositorNodeAlphaOver',
        'MIX_RGB': 'CompositorNodeMixRGB',
        'BOKEHBLUR': 'CompositorNodeBokehBlur',
        'CHANNEL_MATTE': 'CompositorNodeChannelMatte',
        'ROTATE': 'CompositorNodeRotate',
        'DOUBLEEDGEMASK': 'CompositorNodeDoubleEdgeMask',
        'TRACKPOS': 'CompositorNodeTrackPos',
        'CROP': 'CompositorNodeCrop',
        'TEXTURE': 'CompositorNodeTexture',
        'INPAINT': 'CompositorNodeInpaint',
        'DISTANCE_MATTE': 'CompositorNodeDistanceMatte',
        'DILATEERODE': 'CompositorNodeDilateErode',
        'COMPOSITE': 'CompositorNodeComposite',
        'FLIP': 'CompositorNodeFlip',
        'SETALPHA': 'CompositorNodeSetAlpha',
        'DEFOCUS': 'CompositorNodeDefocus',
        'BRIGHTCONTRAST': 'CompositorNodeBrightContrast',
        'COMBYCCA': 'CompositorNodeCombYCCA',
        'HUE_SAT': 'CompositorNodeHueSat',
        'SEPRGBA': 'CompositorNodeSepRGBA',
        'SCALE': 'CompositorNodeScale',
        'CHROMA_MATTE': 'CompositorNodeChromaMatte',
        'LEVELS': 'CompositorNodeLevels',
        'COMBYUVA': 'CompositorNodeCombYUVA',
        'DBLUR': 'CompositorNodeDBlur',
        'MAP_UV': 'CompositorNodeMapUV',
        'GAMMA': 'CompositorNodeGamma',
        'PIXELATE': 'CompositorNodePixelate',
        'KEYINGSCREEN': 'CompositorNodeKeyingScreen',
        'TIME': 'CompositorNodeTime',
        'MOVIECLIP': 'CompositorNodeMovieClip',
        'OUTPUT_FILE': 'CompositorNodeOutputFile',
        'BOXMASK': 'CompositorNodeBoxMask',
        'COMBRGBA': 'CompositorNodeCombRGBA',
        'MASK': 'CompositorNodeMask',
        'BLUR': 'CompositorNodeBlur',
        'SWITCH': 'CompositorNodeSwitch',
        'CURVE_VEC': 'CompositorNodeCurveVec',
        'FILTER': 'CompositorNodeFilter',
        'TONEMAP': 'CompositorNodeTonemap',
        'VIEWER': 'CompositorNodeViewer',
        'SEPYCCA': 'CompositorNodeSepYCCA',
        'ELLIPSEMASK': 'CompositorNodeEllipseMask',
        'PLANETRACKDEFORM': 'CompositorNodePlaneTrackDeform',
        'COMBHSVA': 'CompositorNodeCombHSVA',
        'VECBLUR': 'CompositorNodeVecBlur',
        'SEPYUVA': 'CompositorNodeSepYUVA',
        'MAP_RANGE': 'CompositorNodeMapRange',
        'HUECORRECT': 'CompositorNodeHueCorrect',
        'STABILIZE2D': 'CompositorNodeStabilize',
        'COLORBALANCE': 'CompositorNodeColorBalance',
        'CURVE_RGB': 'CompositorNodeCurveRGB',
        'TRANSLATE': 'CompositorNodeTranslate',
        'PREMULKEY': 'CompositorNodePremulKey',
        'COLOR_MATTE': 'CompositorNodeColorMatte',
        'DIFF_MATTE': 'CompositorNodeDiffMatte',
        'LENSDIST': 'CompositorNodeLensdist',
        'LUMA_MATTE': 'CompositorNodeLumaMatte',
        'GROUP': 'CompositorNodeGroup',
        'NORMAL': 'CompositorNodeNormal',
        'ID_MASK': 'CompositorNodeIDMask',
        'MOVIEDISTORTION': 'CompositorNodeMovieDistortion',
        'DISPLACE': 'CompositorNodeDisplace',
        'SPLITVIEWER': 'CompositorNodeSplitViewer',
        'BOKEHIMAGE': 'CompositorNodeBokehImage',
        'COLOR_SPILL': 'CompositorNodeColorSpill',
        'NORMALIZE': 'CompositorNodeNormalize',
        'RGB': 'CompositorNodeRGB',
        'ZCOMBINE': 'CompositorNodeZcombine',
        'RGBTOBW': 'CompositorNodeRGBToBW',
        'BILATERALBLUR': 'CompositorNodeBilateralblur',
        'GLARE': 'CompositorNodeGlare'},
    'TEXTURE': {
        'IMAGE': 'TextureNodeImage',
        'ROTATE': 'TextureNodeRotate',
        'TEX_VORONOI': 'TextureNodeTexVoronoi',
        'CURVE_TIME': 'TextureNodeCurveTime',
        'TEX_DISTNOISE': 'TextureNodeTexDistNoise',
        'MATH': 'TextureNodeMath',
        'TEX_NOISE': 'TextureNodeTexNoise',
        'INVERT': 'TextureNodeInvert',
        'CHECKER': 'TextureNodeChecker',
        'VALTONOR': 'TextureNodeValToNor',
        'TEX_BLEND': 'TextureNodeTexBlend',
        'TEX_MAGIC': 'TextureNodeTexMagic',
        'TEX_MUSGRAVE': 'TextureNodeTexMusgrave',
        'BRICKS': 'TextureNodeBricks',
        'VALTORGB': 'TextureNodeValToRGB',
        'AT': 'TextureNodeAt',
        'MIX_RGB': 'TextureNodeMixRGB',
        'CURVE_RGB': 'TextureNodeCurveRGB',
        'TRANSLATE': 'TextureNodeTranslate',
        'TEXTURE': 'TextureNodeTexture',
        'TEX_WOOD': 'TextureNodeTexWood',
        'TEX_MARBLE': 'TextureNodeTexMarble',
        'GROUP': 'TextureNodeGroup',
        'HUE_SAT': 'TextureNodeHueSaturation',
        'TEX_STUCCI': 'TextureNodeTexStucci',
        'SCALE': 'TextureNodeScale',
        'DECOMPOSE': 'TextureNodeDecompose',
        'VIEWER': 'TextureNodeViewer',
        'OUTPUT': 'TextureNodeOutput',
        'DISTANCE': 'TextureNodeDistance',
        'TEX_CLOUDS': 'TextureNodeTexClouds',
        'COMPOSE': 'TextureNodeCompose',
        'COORD': 'TextureNodeCoordinates',
        'RGBTOBW': 'TextureNodeRGBToBW'}
}

import bpy
from bpy_extras.io_utils import ExportHelper
import os.path
import http.client
import xml.dom.minidom

library = ""
library_data = []
update_data = ["Up-to-date.", ""]

library_enum_items = [("peter.cassetta.info/material-library/release/", "Peter's Library - Release", "Stable library hosted on peter.cassetta.info (Default)"),
                      ("peter.cassetta.info/material-library/testing/", "Peter's Library - Testing", "Continually updated library hosted on peter.cassetta.info (Online only)"),
                      ("bundled", "Bundled Library", "The library bundled with this add-on (Offline only)")]
bpy.types.Scene.mat_lib_library = bpy.props.EnumProperty(name = "Select library:", items = library_enum_items, description = "Choose a library", options = {'SKIP_SAVE'})

working_mode = "none"
mat_lib_host = ""
mat_lib_location = ""
mat_lib_cached_files = -1

matlibpath = ""

def findLibrary():
    global matlibpath
    for p in bpy.utils.script_paths():
        matlibpath = os.path.join(p, "addons_contrib", "online_mat_lib", "material-library")
        if os.path.exists(matlibpath):
            break
    return matlibpath    

findLibrary()

mat_lib_contents = "Please refresh."
mat_lib_category_filenames = []
mat_lib_category_types = []
mat_lib_category_names = []
mat_lib_categories = 0

category_contents = "None"
category_name = ""
category_filename = ""
category_materials = 0

category_type = "none"
category_special = "none"

sub_category_contents = "None"
sub_category_name = ""
sub_category_filename = ""
sub_category_categories = 0
sub_category_names = []
sub_category_filenames = []

material_names = []
material_filenames = []
material_contributors = []
material_ratings = []
material_fireflies = []
material_speeds = []
material_complexities = []
material_groups = []
material_scripts = []
material_images = []
material_filesizes = []
material_dimensions = []
material_tileabilities = []
material_lines = []

material_file_contents = ""

current_material_number = -1
current_material_cached = False
current_material_previewed = False
material_detail_view = "RENDER"
preview_message = []
node_message = []
save_filename = ""
script_stack = []
group_stack = []
curve_stack = []
group_curve_stack = []
group_script_stack = []
node_groups = []
osl_scripts = []
mapping_curves = []
group_scripts = []
group_curves = []

bpy.types.Scene.mat_lib_auto_preview = bpy.props.BoolProperty(name = "Auto-download previews", description = "Automatically download material previews in online mode", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_show_osl_materials = bpy.props.BoolProperty(name = "Show OSL materials", description = "Enable to show materials with OSL shading scripts", default = False, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_show_textured_materials = bpy.props.BoolProperty(name = "Show textured materials", description = "Enable to show materials with image textures", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_osl_only_trusted = bpy.props.BoolProperty(name = "Use OSL scripts from trusted sources only", description = "Disable to allow downloading OSL scripts from anywhere on the web (Not recommended)", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_images_only_trusted = bpy.props.BoolProperty(name = "Use image textures from trusted sources only", description = "Disable to allow downloading image textures from anywhere on the web (Not recommended)", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_external_groups = bpy.props.BoolProperty(name = "Write nodegroups to separate files", description = "Enable to write nodegroups to separate .bcg files when saving materials to disk", default = False, options = {'SKIP_SAVE'})


tools_enum_items = [("material", "Material Tools", "Material import-export tools"), ("nodegroup", "Nodegroup Tools", "Nodegroup import-export tools")]
bpy.types.Scene.mat_lib_tools_view = bpy.props.EnumProperty(items = tools_enum_items, name = "View", description = "Change tools view")

bpy.types.Scene.mat_lib_bcm_write = bpy.props.StringProperty(name = "Text Datablock", description = "Name of text datablock to write .bcm data to", default="bcm_file", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcg_write = bpy.props.StringProperty(name = "Text Datablock", description = "Name of text datablock to write .bcg data to", default="bcg_file", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcm_read = bpy.props.StringProperty(name = "Text Datablock", description = "Name of text datablock to read .bcm data from", default="bcm_file", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcg_read = bpy.props.StringProperty(name = "Text Datablock", description = "Name of text datablock to read .bcg data from", default="bcg_file", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcm_name = bpy.props.StringProperty(name = "Material Name", description = "Specify a name for the new material", default="Untitled", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcg_name = bpy.props.StringProperty(name = "Nodegroup Name", description = "Specify a name for the new nodegroup", default="Untitled", options = {'SKIP_SAVE'})

bpy.types.Scene.mat_lib_bcm_save_location = bpy.props.StringProperty(name = "Save location", description = "Directory to save .bcm files in", default=matlibpath + os.sep + "my-materials" + os.sep, options = {'SKIP_SAVE'}, subtype="DIR_PATH")
bpy.types.Scene.mat_lib_bcg_save_location = bpy.props.StringProperty(name = "Save location", description = "Directory to save .bcg files in", default=matlibpath + os.sep + "my-materials" + os.sep, options = {'SKIP_SAVE'}, subtype="DIR_PATH")
bpy.types.Scene.mat_lib_bcm_open_location = bpy.props.StringProperty(name = "Open location", description = "Location of .bcm file to open", default=matlibpath + os.sep + "my-materials" + os.sep + "untitled.bcm", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcg_open_location = bpy.props.StringProperty(name = "Open location", description = "Location of .bcg file to open", default=matlibpath + os.sep + "my-materials" + os.sep + "untitled.bcg", options = {'SKIP_SAVE'})

#subcategory_enum_items = [("None0", "None", "No Subcategory Selected")]
#bpy.types.Scene.mat_lib_material_subcategory = bpy.props.EnumProperty(name = "", items = subcategory_enum_items, description = "Choose a subcategory", options = {'SKIP_SAVE'})

class OnlineMaterialLibraryPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Online Material Library"
    bl_idname = "OnlineMaterialLibraryPanel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    def draw(self, context):
        global show_success_message
        global show_success_message_timeout
        global current_material_number
        global mat_lib_contents
        global prev_show_osl
        global prev_show_textured
        global prev_category
        global save_filename
        
        layout = self.layout
        
        if context.scene.render.engine == "CYCLES":
            #Cycles is enabled!
            row = layout.row()
            
            if category_type is not "info" and category_type is not "settings" and category_type is not "tools":
                if mat_lib_contents == "" or mat_lib_contents == "Please refresh.":
                    if matlibpath == "error":
                        row.label(text="ERROR: Could not find installation path!", icon='ERROR')
                    else:
                        #Material Library Contents variable is empty -- show welcome message
                        row.label(text="Online Material Library Add-on -- Version 0.6", icon='SMOOTH')
                        
                        row = layout.row()
                        rowcol = row.column(align=True)
                        rowcol.alignment = 'EXPAND'
                        rowcol.prop(context.scene, "mat_lib_library", text="")
                        
                        rowcolrow = rowcol.row(align=True)
                        rowcolrow.alignment = 'EXPAND'
                        if "bundled" not in context.scene.mat_lib_library:
                            rowcolrow.operator("material.libraryconnect", text="Connect", icon='WORLD').mode = "online"
                        if "testing" not in context.scene.mat_lib_library:
                            rowcolrow.operator("material.libraryconnect", text="Work Offline", icon='DISK_DRIVE').mode = "offline"
                    
                elif working_mode is not "none":
                    #We have a valid material library
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(bpy.context.scene, "mat_lib_material_category")
                else:
                    #Could not retrive a valid material library
                    row.label(text="Could not retrieve material library.", icon='CANCEL')
                    row = layout.row()
                    row.label(text=str(mat_lib_contents))
                    row = layout.row()
                    row.label(text="..." + str(mat_lib_contents)[-50:])
                    
                    row = layout.row()
                    rowcol = row.column(align=True)
                    rowcol.alignment = 'EXPAND'
                    rowcol.prop(context.scene, "mat_lib_library", text="")
                    
                    rowcolrow = rowcol.row(align=True)
                    rowcolrow.alignment = 'EXPAND'
                    if "bundled" not in context.scene.mat_lib_library:
                        rowcolrow.operator("material.libraryconnect", text="Attempt Reconnect", icon='WORLD').mode = "online"
                    if "testing" not in context.scene.mat_lib_library:
                        rowcolrow.operator("material.libraryconnect", text="Work Offline", icon='DISK_DRIVE').mode = "offline"
            
            if category_type == "none":
                #Not browsing category
                if working_mode is not "none":
                    row = layout.row()
                    rowcol = row.column(align=True)
                    rowcol.alignment = 'EXPAND'
                    rowcol.prop(context.scene, "mat_lib_library", text="")
                    
                    rowcolrow = rowcol.row(align=True)
                    rowcolrow.alignment = 'EXPAND'
                    if "bundled" not in context.scene.mat_lib_library:
                        if working_mode == "online":
                            rowcolrow.operator("material.libraryconnect", text="Reconnect", icon='WORLD').mode = "online"
                        else:
                            rowcolrow.operator("material.libraryconnect", text="Connect", icon='WORLD').mode = "online"
                    if "testing" not in context.scene.mat_lib_library:
                        if working_mode == "offline":
                            rowcolrow.operator("material.libraryconnect", text="Reload Library", icon='DISK_DRIVE').mode = "offline"
                        else:
                            rowcolrow.operator("material.libraryconnect", text="Work Offline", icon='DISK_DRIVE').mode = "offline"
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.operator("material.libraryinfo", text="Info", icon='INFO')
                row.operator("material.librarytools", text="Tools", icon='MODIFIER')
                row.operator("material.librarysettings", text="Settings", icon='SETTINGS')
                
                if "Up-to-date." not in update_data[0]:
                    row = layout.row()
                    row.label(text=update_data[0])
                    row.operator("wm.url_open", text="Get latest version", icon='WORLD').url = update_data[1]
                    
            elif category_type == "info":
                row.label(text="Add-on Info", icon='INFO')
                row.operator("material.libraryhome", text="", icon='LOOP_BACK')
                
                row = layout.row()
                row.operator("wm.url_open", text="All materials are CC0 - learn more.", icon='TRIA_RIGHT', emboss=False).url = "http://creativecommons.org/publicdomain/zero/1.0/"
                
                row = layout.row()
                row.operator("wm.url_open", text="Stay up-to-date on this add-on's development!", icon='TRIA_RIGHT', emboss=False).url = "http://blenderartists.org/forum/showthread.php?256334"
                
                if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.66:
                    row = layout.row()
                    row.operator("wm.url_open", text="Material previews generated with B.M.P.S.", icon='TRIA_RIGHT', emboss=False).url = "https://svn.blender.org/svnroot/bf-blender/trunk/lib/tests/rendering/cycles/blend_files/bmps.blend"
                    row = layout.row()
                    row.operator("wm.url_open", text="B.M.P.S. created by Robin \"tuqueque\" Marín", icon='TRIA_RIGHT', emboss=False).url = "http://blenderartists.org/forum/showthread.php?151903-b.m.p.s.-1.5!"
            
            elif category_type == "settings":
                row.label(text="Add-on Settings", icon='SETTINGS')
                row.operator("material.libraryhome", text="", icon='LOOP_BACK')
                
                row = layout.row()
                row.label(text="Browsing settings")
                row = layout.row()
                box = row.box()
                boxrow = box.row()
                boxrow.prop(bpy.context.scene, "mat_lib_auto_preview")
                boxrow = box.row()
                boxrow.prop(bpy.context.scene, "mat_lib_show_osl_materials")
                boxrow = box.row()
                boxrow.prop(bpy.context.scene, "mat_lib_show_textured_materials")
                
                row = layout.row()
                row.label(text="Security settings")
                row = layout.row()
                box = row.box()
                boxrow = box.row()
                boxrow.prop(bpy.context.scene, "mat_lib_osl_only_trusted")
                boxrow = box.row()
                boxrow.prop(bpy.context.scene, "mat_lib_images_only_trusted")
                row = layout.row()
                row.label(text="Export settings")
                row = layout.row()
                box = row.box()
                boxrow = box.row()
                boxrow.prop(bpy.context.scene, "mat_lib_external_groups")
                
                row = layout.row()
                row.label(text="Cached data for active library:")
                
                row = layout.row()
                if mat_lib_cached_files == 0:
                    row.label(text="No cached files.")
                elif mat_lib_cached_files == -2:
                    row.label(text="The Bundled library contains no cached files.")
                elif mat_lib_cached_files == 1:
                    row.label(text="1 cached file.")
                    row.operator("material.libraryclearcache", text="Clear Cache", icon='CANCEL')
                elif mat_lib_cached_files != -1:
                    row.label(text=str(mat_lib_cached_files) + " cached files.")
                    row.operator("material.libraryclearcache", text="Clear Cache", icon='CANCEL')
                else:
                    row.label(text="Please select a library first.", icon="ERROR")
            
            elif category_type == "tools":
                row.label(text="Import-Export Tools", icon='MODIFIER')
                row.operator("material.libraryhome", text="", icon='LOOP_BACK')
                
                row = layout.row()
                row.prop(bpy.context.scene, "mat_lib_tools_view")
                
                if context.scene.mat_lib_tools_view == "material":
                    row = layout.row()
                    row.label(text="Write material data to text as .bcm:")
                    
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(bpy.context.scene, "mat_lib_bcm_write", text="", icon="TEXT")
                    row.operator("material.libraryconvert", text="Write to text", icon='MATERIAL_DATA')
                
                    row = layout.row()
                    row.label(text="Save material(s) as .bcm files:")
                    
                    row = layout.row()
                    col = row.column(align=True)
                    col.alignment = 'EXPAND'
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcm_save_location", text="")
                    colrow = col.row(align=True)
                    colrow.alignment = 'EXPAND'
                    colrow.operator("material.libraryconvert", text="Save active", icon='DISK_DRIVE').save_location = context.scene.mat_lib_bcm_save_location
                    save_button = colrow.operator("material.libraryconvert", text="Save all materials", icon='DISK_DRIVE')
                    save_button.save_location = context.scene.mat_lib_bcm_save_location
                    save_button.all_materials = True
                    
                    row = layout.row()
                    row.label(text="Open a local .bcm file:")
                     
                    row = layout.row()
                    col = row.column(align=True)
                    col.alignment = 'EXPAND'
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcm_open_location", text="")
                    colrow.operator("buttons.file_browse", text="", icon='FILESEL').relative_path = False
                    colrow = col.row(align=True)
                    colrow.alignment = 'EXPAND'
                    colrow.operator("material.libraryadd", text="Add to materials", icon='ZOOMIN').open_location = context.scene.mat_lib_bcm_open_location
                    colrow.operator("material.libraryapply", text="Apply to active", icon='PASTEDOWN').open_location = context.scene.mat_lib_bcm_open_location
                
                    row = layout.row()
                    row.label(text="Read .bcm data in a text block to a material:")
                     
                    row = layout.row()
                    col = row.column(align=True)
                    col.alignment = 'EXPAND'
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcm_read", text="", icon='TEXT')
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcm_name", text="", icon='MATERIAL')
                    colrow = col.row(align=True)
                    colrow.alignment = 'EXPAND'
                    colrow.operator("material.libraryadd", text="Add to materials", icon='ZOOMIN').text_block = context.scene.mat_lib_bcm_read
                    colrow.operator("material.libraryapply", text="Apply to active", icon='PASTEDOWN').text_block = context.scene.mat_lib_bcm_read
                else:
                    row = layout.row()
                    row.label(text="Write nodegroup data to text as .bcg:")
                    
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(bpy.context.scene, "mat_lib_bcg_write", text="", icon="TEXT")
                    row.operator("material.libraryconvertgroup", text="Write to text", icon='NODETREE')
                    
                    row = layout.row()
                    row.label(text="Save nodegroup(s) as .bcg files:")
                    
                    row = layout.row()
                    col = row.column(align=True)
                    col.alignment = 'EXPAND'
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcg_save_location", text="")
                    colrow = col.row(align=True)
                    colrow.alignment = 'EXPAND'
                    colrow.operator("material.libraryconvertgroup", text="Save active", icon='DISK_DRIVE').save_location = context.scene.mat_lib_bcg_save_location
                    save_button = colrow.operator("material.libraryconvertgroup", text="Save all nodegroups", icon='DISK_DRIVE')
                    save_button.save_location = context.scene.mat_lib_bcg_save_location
                    save_button.all_groups = True
                    
                    row = layout.row()
                    row.label(text="Open a local .bcg file:")
                     
                    row = layout.row()
                    col = row.column(align=True)
                    col.alignment = 'EXPAND'
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcg_open_location", text="")
                    colrow.operator("buttons.file_browse", text="", icon='FILESEL').relative_path = False
                    colrow = col.row(align=True)
                    colrow.alignment = 'EXPAND'
                    colrow.operator("material.libraryaddgroup", text="Add to nodegroups", icon='ZOOMIN').open_location = context.scene.mat_lib_bcg_open_location
                    colrow.operator("material.libraryinsertgroup", text="Insert into active", icon='PASTEDOWN').open_location = context.scene.mat_lib_bcg_open_location
                    
                    row = layout.row()
                    row.label(text="Read .bcg data in a text block to a nodegroup:")
                     
                    row = layout.row()
                    col = row.column(align=True)
                    col.alignment = 'EXPAND'
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcg_read", text="", icon='TEXT')
                    colrow = col.row()
                    colrow.prop(context.scene, "mat_lib_bcg_name", text="", icon='NODETREE')
                    colrow = col.row(align=True)
                    colrow.alignment = 'EXPAND'
                    colrow.operator("material.libraryaddgroup", text="Add to nodegroups", icon='ZOOMIN').text_block = context.scene.mat_lib_bcg_read
                    colrow.operator("material.libraryinsertgroup", text="Insert into active", icon='PASTEDOWN').text_block = context.scene.mat_lib_bcg_read
                
            elif category_type == "category":
                #Browsing category - show materials
                row = layout.row()
                matwrap = row.box()
                if category_materials == 0:
                    matwrap.label(text="No materials in this category.")
                i = 0
                while i < category_materials:
                    if category_special == "none":
                        mat_icon = 'MATERIAL'
                    elif category_special == "Nodegroups":
                        mat_icon = 'NODETREE'
                    elif category_special == "Image Textures":
                        mat_icon = 'IMAGE_RGB'
                    elif category_special == "OSL Scripts":
                        mat_icon = 'TEXT'
                    if i == current_material_number:
                        matwraprow = matwrap.row()
                        matwrapbox = matwraprow.box()
                        matwrapboxrow = matwrapbox.row()
                        matwrapboxrow.operator("material.libraryviewmaterial", text=material_names[i], icon=mat_icon, emboss=False).material = i
                        matwrapboxrowcol = matwrapboxrow.column()
                        matwrapboxrowcolrow = matwrapboxrowcol.row()
                        matwrapboxrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapboxrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapboxrowcol = matwrapboxrow.column()
                        matwrapboxrowcolrow = matwrapboxrowcol.row()
                        matwrapboxrowcolrowsplit = matwrapboxrowcolrow.split(percentage=0.8)
                        matwrapboxrowcolrowsplitrow = matwrapboxrowcolrowsplit.row()
                        
                        #Ratings
                        if material_ratings[i] == 0:
                            matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="Not rated.", emboss=False).material = i
                        else:
                            e = 0
                            while e < material_ratings[i]:
                                matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_ON', emboss=False).material = i
                                e = e + 1
                            
                            if material_ratings[i] is not 5:    
                                e = 0
                                while e < (5 - material_ratings[i]):
                                    matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_OFF', emboss=False).material = i
                                    e = e + 1
                    else:
                        matwraprow = matwrap.row()
                        matwrapcol = matwraprow.column()
                        matwrapcolrow = matwrapcol.row()
                        matwrapcolrow.operator("material.libraryviewmaterial", text=material_names[i], icon=mat_icon, emboss=False).material = i
                        matwrapcolrowcol = matwrapcolrow.column()
                        matwrapcolrowcolrow = matwrapcolrowcol.row()
                        matwrapcolrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapcolrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapcolrowcol = matwrapcolrow.column()
                        matwrapcolrowcolrow = matwrapcolrowcol.row()
                        matwrapcolrowcolrowsplit = matwrapcolrowcolrow.split(percentage=0.8)
                        matwrapcolrowcolrowsplitrow = matwrapcolrowcolrowsplit.row()
                        
                        #Ratings
                        if material_ratings[i] == 0:
                            matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="Not rated.", emboss=False).material = i
                        else:
                            e = 0
                            while e < material_ratings[i]:
                                matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_ON', emboss=False).material = i
                                e = e + 1
                            
                            if material_ratings[i] is not 5:    
                                e = 0
                                while e < (5 - material_ratings[i]):
                                    matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_OFF', emboss=False).material = i
                                    e = e + 1
                    i = i + 1
                
                if current_material_number is not -1:
                    #Display selected material's info
                    row = layout.row()
                    infobox = row.box()
                    inforow = infobox.row()
                    
                    #Material name
                    inforow.label(text=(material_names[current_material_number]))
                    
                    if library == "release":
                        #Cache indicator/button
                        if current_material_cached:
                            inforow.label(text="", icon="SAVE_COPY")
                        else:
                            if category_special == "none":
                                cache_op = "material.librarycache"
                            elif category_special == "Image Textures":
                                cache_op = "material.librarycacheimage"
                            elif category_special == "Nodegroups":
                                cache_op = "material.librarycachegroup"
                            elif category_special == "OSL Scripts":
                                cache_op = "material.librarycachescript"
                            inforow.operator(cache_op, text="", icon="LONGDISPLAY", emboss=False).filename = material_filenames[current_material_number]
                    
                    #Close button
                    inforow.operator("material.libraryviewmaterial", text="", icon='PANEL_CLOSE').material = -1
                    
                    inforowsplit = infobox.split(percentage=0.5)
                    
                    #Display a preview
                    inforowcol = inforowsplit.column()
                    previewrow = inforowcol.row()
                    
                    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.66:
                        #Use a texture preview in Blender versions before 2.66,
                        #in which the Cycles material preview was added.
                        #Two previews in a single region do not work well together.
                        if bpy.data.textures.find("mat_lib_preview_texture") == -1:
                            bpy.data.textures.new("mat_lib_preview_texture", "IMAGE")
                            
                        if category_special == "none" or category_special == "Image Textures":
                            preview_texture = bpy.data.textures['mat_lib_preview_texture']
                            previewrow.template_preview(preview_texture)
                        
                            previewrow = inforowcol.row()
                            #Preview download button
                            if current_material_previewed == False:
                                preview_button = previewrow.operator("material.librarypreview", text="Preview material", icon='COLOR')
                                preview_button.name = material_names[current_material_number]
                                preview_button.filename = material_filenames[current_material_number]
                            else:
                                if category_special == 'Image Textures':
                                    previewrow.label(text="Image Preview")
                                else:
                                    previewrow.label(text="Material Preview")
                        else:
                            if material_contributors[current_material_number] != "Unknown":
                                previewrow.label(text="By %s." % material_contributors[current_material_number])
                            else:
                                previewrow.label(text="Author unknown.")
                        previewing = False
                    else:
                        previewing = context.active_object.material_slots[-1].material.name == "mat_lib_preview_material"
                        previewrow = inforowcol.row()
                        if material_contributors[current_material_number] != "Unknown":
                            previewrow.label(text="By %s." % material_contributors[current_material_number])
                        else:
                            previewrow.label(text="Author unknown.")
                        previewrow = inforowcol.row()
                        if material_ratings[current_material_number] != 0:
                            previewrow.label(text="Rating: %s of 5 stars." % str(material_ratings[current_material_number]))
                        else:
                            previewrow.label(text="Not rated.")
                    
                    #Display material details
                    inforowcol = inforowsplit.column(align=True)
                    inforowcol.alignment = 'EXPAND'
                    matDetails(self, context, inforowcol)
                    
                    #Display material functions
                    inforow = infobox.row(align=True)
                    inforow.alignment = 'EXPAND'
                    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) >= 2.66 and category_special == "none":
                        inforowcol = inforow.column()
                        if previewing:
                            inforowcol.operator("material.libraryremovepreview", text="", icon='CANCEL')
                        else:
                            inforowcol.operator("material.librarypreview", text="", icon='COLOR')
                        inforowcol = inforow.column()
                        functions = inforowcol.row(align=True)
                        functions.alignment = 'EXPAND'
                        functions.enabled = not previewing
                    else:
                        functions = inforow
                    
                    if category_special == "none":
                        #Display material "Add" button
                        mat_button = functions.operator("material.libraryadd", text="Add", icon='ZOOMIN')
                        mat_button.mat_name = material_names[current_material_number]
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display material "Apply" button
                        mat_button = functions.operator("material.libraryapply", text="Apply", icon='PASTEDOWN')
                        mat_button.mat_name = material_names[current_material_number]
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display material "Save" button
                        mat_button = functions.operator("material.librarysave", text="Save as...", icon='DISK_DRIVE')
                        mat_button.filepath = os.path.join(matlibpath, "my-materials", material_filenames[current_material_number] + ".bcm")
                        mat_button.filename = material_filenames[current_material_number]
                        save_filename = material_filenames[current_material_number]
                        
                    elif category_special == "Nodegroups":
                        #Display nodegroup "Add" button
                        mat_button = functions.operator("material.libraryaddgroup", text="Add", icon='ZOOMIN')
                        mat_button.group_name = material_names[current_material_number]
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display nodegroup "Insert" button
                        mat_button = functions.operator("material.libraryinsertgroup", text="Insert", icon='PASTEDOWN')
                        mat_button.group_name = material_names[current_material_number]
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display nodegroup "Save" button
                        mat_button = functions.operator("material.librarysavegroup", text="Save as...", icon='DISK_DRIVE')
                        mat_button.filepath = os.path.join(matlibpath, "my-materials", material_filenames[current_material_number] + ".bcg")
                        mat_button.filename = material_filenames[current_material_number]
                        save_filename = material_filenames[current_material_number]
                        
                    elif category_special == "Image Textures":
                        #Display image "Add" button
                        mat_button = functions.operator("material.libraryaddimage", text="Add", icon='ZOOMIN')
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display image "Insert" button
                        mat_button = functions.operator("material.libraryinsertimage", text="Insert", icon='PASTEDOWN')
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display image "Save" button
                        mat_button = functions.operator("material.librarysaveimage", text="Save as...", icon='DISK_DRIVE')
                        mat_button.filepath = os.path.join(matlibpath, "my-materials", material_filenames[current_material_number])
                        mat_button.filename = material_filenames[current_material_number]
                        mat_button.filename_ext = "." + material_filenames[current_material_number].split(".")[-1]
                        mat_button.filter_glob = "*." + material_filenames[current_material_number].split(".")[-1]
                        save_filename = material_filenames[current_material_number]
                        
                    elif category_special == "OSL Scripts":
                        #Display script "Add" button
                        mat_button = functions.operator("material.libraryaddscript", text="Add", icon='ZOOMIN')
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display script "Insert" button
                        mat_button = functions.operator("material.libraryinsertscript", text="Insert", icon='PASTEDOWN')
                        mat_button.filename = material_filenames[current_material_number]
                        
                        #Display script "Save" button
                        mat_button = functions.operator("material.librarysavescript", text="Save as...", icon='DISK_DRIVE')
                        mat_button.filepath = os.path.join(matlibpath, "my-materials", material_filenames[current_material_number])
                        mat_button.filename = material_filenames[current_material_number]
                        mat_button.filename_ext = "." + material_filenames[current_material_number].split(".")[-1]
                        mat_button.filter_glob = "*." + material_filenames[current_material_number].split(".")[-1]
                        save_filename = material_filenames[current_material_number]
                        
        else:
            #Dude, you gotta switch to Cycles to use this.
            row = layout.row()
            row.label(text="Sorry, Cycles only at the moment.",icon='ERROR')

class libraryCategory:
    def __init__(self, title, folder):
        self.title = title
        self.folder = folder
        self.materials = []

class libraryMaterial:
    def __init__(self, name, href, contrib, stars, fireflies, speed, complexity, groups, scripts, images, filesize, dimensions, tileable, lines):
        self.name = name
        self.href = href
        self.contrib = contrib
        self.stars = stars
        self.fireflies = fireflies
        self.speed = speed
        self.complexity = complexity
        self.groups = groups
        self.scripts = scripts
        self.images = images
        self.filesize = filesize
        self.dimensions = dimensions
        self.tileable = tileable
        self.lines = lines

def handleCategories(categories):
    for index, category in enumerate(categories):
        handleCategory(category, index)

def handleCategory(category, index):
    if 'addon' in category.attributes:
        needed_version = float(category.attributes['addon'].value)
        this_version = bl_info["version"][0] + (bl_info["version"][1] / 10.0)
        
        #Check this addon's compatibility with this category
        if needed_version > this_version:
            print('\n\n-Category "' + category.attributes['title'].value + '" not used; its materials are for a newer version of this add-on.')
            return
    
    if 'bl' in category.attributes:
        bl_version = bpy.app.version[0] + (bpy.app.version[1] / 100)
        
        #Check Blender's compatibility with this category
        if category.attributes['bl'].value[-1] == "-":
            #This option is for if Blender's compatiblity
            #with a category started only with a specific
            #version, but has not yet ended; this will
            #look like the following: bl="2.64-"
            bl_lower = float(category.attributes['bl'].value[:-1])
            if bl_lower > bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
            
        elif category.attributes['bl'].value[0] == "-":
            #This option is for if Blender's compatiblity
            #with a category ended at some point, and will
            #look like the following: bl="-2.73"
            bl_upper = float(category.attributes['bl'].value[1:])
            if bl_upper < bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
            
        else:
            #This option is for if Blender's compatiblity
            #with a category started with a certain version,
            #then ended with another; it will look
            #like the following: bl="2.64-2.73"
            bl_lower = float(category.attributes['bl'].value.split('-')[0])
            bl_upper = float(category.attributes['bl'].value.split('-')[1])
            if bl_upper < bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
            elif bl_lower > bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
    
    if library is not "bundled":
        if not os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category.attributes['folder'].value)):
            print("Folder \"/" + category.attributes['folder'].value + "/\" does not exist; creating now.")
            if library == "composite":
                os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", category.attributes['folder'].value))
            else:
                os.mkdir(os.path.join(matlibpath, mat_lib_host, library, "cycles", category.attributes['folder'].value))
        
        if 'remove' in category.attributes:
            if library == "composite":
                if os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", category.attributes['folder'].value)):
                    for the_file in os.listdir(os.path.join(matlibpath, mat_lib_host, "cycles", category.attributes['folder'].value)):
                        file_path = os.path.join(matlibpath, mat_lib_host, "cycles", category.attributes['folder'].value, the_file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            for sub_file in os.listdir(file_path):
                                if os.path.isfile(file_path + sub_file):
                                    os.remove(file_path + sub_file)
                            os.rmdir(file_path)
                    os.rmdir(os.path.join(matlibpath, mat_lib_host, "cycles", category.attributes['folder'].value))
            else:
                if os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category.attributes['folder'].value)):
                    for the_file in os.listdir(os.path.join(matlibpath, mat_lib_host, library, "cycles", category.attributes['folder'].value)):
                        file_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", category.attributes['folder'].value, the_file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            for sub_file in os.listdir(file_path):
                                if os.path.isfile(file_path + sub_file):
                                    os.remove(file_path + sub_file)
                            os.rmdir(file_path)
                    os.rmdir(os.path.join(matlibpath, mat_lib_host, library, "cycles", category.attributes['folder'].value))
                return
    
    print ('\n\n-Category "' + category.attributes['title'].value + '"; located in folder "/' + category.attributes['folder'].value + '/".')
    library_data.append(libraryCategory(category.attributes['title'].value, category.attributes['folder'].value))
    if category.attributes['folder'].value == "groups":
        handleMaterials(category.getElementsByTagName("group"), index)
    elif category.attributes['folder'].value == "textures":
        handleMaterials(category.getElementsByTagName("image"), index)
    elif category.attributes['folder'].value == "scripts":
        handleMaterials(category.getElementsByTagName("script"), index)
    else:
        handleMaterials(category.getElementsByTagName("material"), index)

def handleMaterials(materials, index):
    for material in materials:
        handleMaterial(material, index)

def handleMaterial(material, index):
    if 'addon' in material.attributes:
        needed_version = float(material.attributes['addon'].value)
        this_version = bl_info["version"][0] + (bl_info["version"][1] / 10.0)
        
        #Check this addon's compatibility with this material
        if needed_version > this_version:
            print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is for a newer version of this add-on.')
            return
    
    if 'bl' in material.attributes:
        bl_version = bpy.app.version[0] + (bpy.app.version[1] / 100)
        
        #Check Blender's compatibility with this material
        if material.attributes['bl'].value[-1] == "-":
            #This option is for if Blender's compatiblity
            #with a material started only with a specific
            #version, but has not yet ended; this will
            #look like the following: bl="2.64-"
            bl_lower = float(material.attributes['bl'].value[:-1])
            if bl_lower > bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
            
        elif material.attributes['bl'].value[0] == "-":
            #This option is for if Blender's compatiblity
            #with a material ended at some point, and will
            #look like the following: bl="-2.73"
            bl_upper = float(material.attributes['bl'].value[1:])
            if bl_upper < bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
            
        else:
            #This option is for if Blender's compatiblity
            #with a material started with a certain version,
            #then ended with another; it will
            #look like the following: bl="2.64-2.73"
            bl_lower = float(material.attributes['bl'].value.split('-')[0])
            bl_upper = float(material.attributes['bl'].value.split('-')[1])
            if bl_upper < bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
            elif bl_lower > bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
    
    if 'by' in material.attributes:
        contributor = material.attributes['by'].value
    else:
        contributor = "Unknown"
    
    if 'stars' in material.attributes:
        stars = material.attributes['stars'].value
    else:
        stars = '0'
    
    if 'fireflies' in material.attributes:
        fireflies = material.attributes['fireflies'].value
    else:
        fireflies = 'low'
    
    if 'speed' in material.attributes:
        speed = material.attributes['speed'].value
    else:
        speed = 'good'
    
    if 'complexity' in material.attributes:
        complexity = material.attributes['complexity'].value
    else:
        complexity = 'simple'
    
    if 'groups' in material.attributes:
        groups = material.attributes['groups'].value
    else:
        groups = '0'
    
    if 'scripts' in material.attributes:
        scripts = material.attributes['scripts'].value
    else:
        scripts = '0'
    
    if 'images' in material.attributes:
        images = material.attributes['images'].value
    else:
        images = '0'
    
    if 'filesize' in material.attributes:
        filesize = material.attributes['filesize'].value
    else:
        filesize = 'unknown'
    
    if 'dimensions' in material.attributes:
        dimensions = material.attributes['dimensions'].value
    else:
        dimensions = "unknown"
    
    if 'tileable' in material.attributes:
        tileable = material.attributes['tileable'].value
    else:
        tileable = "unknown"
    
    if 'lines' in material.attributes:
        lines = material.attributes['lines'].value
    else:
        lines = "unknown"
    
    library_data[index].materials.append(
        libraryMaterial(
        material.attributes['name'].value,
        material.attributes['href'].value,
        contributor,
        int(stars),
        fireflies,
        speed,
        complexity,
        groups,
        scripts,
        images,
        filesize,
        dimensions,
        tileable,
        lines))
    
    print ('\n  -Material "' + 
        material.attributes['name'].value + 
        '"\n    -Filename: "' + 
        material.attributes['href'].value + 
        '.bcm"\n    -Rating: ' + stars + 
        ' stars\n    -Contributed by "' + 
        contributor + '"')

class LibraryConnect(bpy.types.Operator):
    '''Connect to selected material library'''
    bl_idname = "material.libraryconnect"
    bl_label = "Connect to selected material library"
    mode = bpy.props.StringProperty()

    def execute(self, context):
        global library_data
        global library
        global update_data
        
        global mat_lib_contents
        global mat_lib_categories
        global mat_lib_category_names
        global mat_lib_category_types
        global mat_lib_category_filenames
        
        global category_enum_items
        global subcategory_enum_items
        
        global show_success_message
        global show_success_message_timeout
        
        global prev_category
        global mat_lib_host
        global mat_lib_location
        global working_mode
        
        findLibrary()
        
        if self.mode == "online":
            mat_lib_host = context.scene.mat_lib_library[:context.scene.mat_lib_library.index("/")]
            mat_lib_location = context.scene.mat_lib_library[(context.scene.mat_lib_library.index(mat_lib_host) + len(mat_lib_host)):]
            print(mat_lib_host)
            print(mat_lib_location)
        elif "bundled" not in context.scene.mat_lib_library:
            mat_lib_host = context.scene.mat_lib_library[:context.scene.mat_lib_library.index("/")]
        
        #Pre-create preview image
        if not os.path.exists(os.path.join(matlibpath, "mat_lib_preview_image.jpg")):
            f = open(os.path.join(matlibpath, "mat_lib_preview_image.jpg"), 'w+b')
            f.close()
        
        if self.mode == "online":
            #Connect and download
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/index.xml")
            
            if "release" in context.scene.mat_lib_library:
                response = connection.getresponse().read()
                
                #Cache the index.xml file for offline use
                library_file = open(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "index.xml"), mode="w+b")
                library_file.write(response)
                library_file.close()
                
                #Create /groups/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "groups")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "groups"))
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "textures")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "scripts")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "scripts"))
                library = "release"
            elif "testing" in context.scene.mat_lib_library:
                response = connection.getresponse().read()
                
                #Create /groups/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "testing", "cycles", "groups")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "testing", "cycles", "groups"))
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "testing", "cycles", "textures")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "testing", "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "testing", "cycles", "scripts")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "testing", "cycles", "scripts"))
                library = "testing"
            else:
                response = connection.getresponse().read()
                
                #Cache the index.xml file for offline use
                library_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "index.xml"), mode="w+b")
                library_file.write(response)
                library_file.close()
                
                #Create /groups/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", "groups"))
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts"))
                library = "composite"
                
            #Convert the response to a string
            mat_lib_contents = str(response)
            
            #Check for connection errors
            if "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" not in mat_lib_contents:
                self.report({'ERROR'}, "Error connecting; see console for details.")
                print("Received following response from server:\n" + mat_lib_contents)
                return {'CANCELLED'}
            
            #Format nicely
            mat_lib_contents = mat_lib_contents.replace("b'<?xml version=\"1.0\" encoding=\"UTF-8\"?>",'')
            mat_lib_contents = mat_lib_contents.replace("\\r\\n",'')
            mat_lib_contents = mat_lib_contents.replace("\\t",'')[:-1]
            mat_lib_contents = mat_lib_contents.replace("\\",'')
            
        else:
            if "release" in context.scene.mat_lib_library:
                #Check for cached index.xml file
                if os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "index.xml")):
                    library_file = open(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "index.xml"), mode="r", encoding="UTF-8")
                    mat_lib_contents = library_file.read()
                    library_file.close()
                else:
                    self.report({'ERROR'}, "No cached library exists!")
                    return {'CANCELLED'}
                
                #Create /groups/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "groups")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "groups"))
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "textures")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "scripts")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "release", "cycles", "scripts"))
                library = "release"
            elif context.scene.mat_lib_library == "bundled":
                #Check for index.xml file
                if os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "index.xml")):
                    library_file = open(os.path.join(matlibpath, "bundled", "cycles", "index.xml"), mode="r", encoding="UTF-8")
                    mat_lib_contents = library_file.read()
                    library_file.close()
                else:
                    self.report({'ERROR'}, "Bundled library does not exist!")
                    return {'CANCELLED'}
                library = "bundled"
            else:
                #Check for cached index.xml file
                if os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "index.xml")):
                    library_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "index.xml"), mode="r", encoding="UTF-8")
                    mat_lib_contents = library_file.read()
                    library_file.close()
                else:
                    self.report({'ERROR'}, "No cached library exists!")
                    return {'CANCELLED'}
                
                #Create /groups/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", "groups"))
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts")):
                    os.mkdir(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts"))
                library = "composite"
            
            if '<?xml version="1.0" encoding="UTF-8"?>' not in mat_lib_contents:
                self.report({'ERROR'}, "Cached XML file is invalid!")
                return {'CANCELLED'}
            
            #Format nicely
            mat_lib_contents = mat_lib_contents.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
            mat_lib_contents = mat_lib_contents.replace("\r\n",'')
            mat_lib_contents = mat_lib_contents.replace("\n",'')
            mat_lib_contents = mat_lib_contents.replace("\t",'')
            mat_lib_contents = mat_lib_contents.replace("\\",'')
        
        #Clear important lists
        library_data = []
        mat_lib_category_names = []
        mat_lib_category_types = []
        mat_lib_category_filenames = []
            
        dom = xml.dom.minidom.parseString(mat_lib_contents)
        
        if self.mode == "online":
            if library == "composite":
                rev_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "revision_data.ini"), mode="r", encoding="UTF-8")
                rev_data = rev_file.read()
                rev_file.close()
            else:
                rev_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "revision_data.ini"), mode="r", encoding="UTF-8")
                rev_data = rev_file.read()
                rev_file.close()
            
            if "revision=" in rev_data:
                revision = int(rev_data[9:])
            else:
                revision = -1
                print("The revision_data.ini file is invalid; clearing cache and re-creating.")
            
            if revision is not int(dom.getElementsByTagName("library")[0].attributes['rev'].value):
                bpy.ops.material.libraryclearcache()
            
            if library == "composite":
                rev_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "revision_data.ini"), mode="w", encoding="UTF-8")
            else:
                rev_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "revision_data.ini"), mode="w", encoding="UTF-8")
            rev_file.write("revision=" + dom.getElementsByTagName("library")[0].attributes['rev'].value)
            rev_file.close()
            
            if 'addon' in dom.getElementsByTagName("library")[0].attributes:
                current_version = float(dom.getElementsByTagName("library")[0].attributes['addon'].value)
                this_version = bl_info["version"][0] + (bl_info["version"][1] / 10.0)
                if current_version > this_version:
                    update_data = ["Add-on is outdated.", dom.getElementsByTagName("library")[0].attributes['download'].value]
        
        print ("\n\n---Material Library---")
        categories = dom.getElementsByTagName("category")
        handleCategories(categories)
        
        for cat in library_data:
            #Find category names
            mat_lib_category_names.append(cat.title)
            #Find category types
            #NOTE: Will have to redo this.
            #mat_lib_category_types = safeEval(mat_lib_contents[(mat_lib_contents.index('[types]') + 7):mat_lib_contents.index('[/types]')])
            #Get category filenames
            mat_lib_category_filenames.append(cat.folder)
            
        #Find amount of categories
        mat_lib_categories = len(mat_lib_category_names)
        
        #Set enum items for category dropdown
        category_enum_items = [("None0", "None", "No category selected")]
        
        i = 0
        while i < mat_lib_categories:
            print ("Adding category #%d" % (i + 1))
            category_enum_items.append(((mat_lib_category_names[i] + str(i + 1)), mat_lib_category_names[i], (mat_lib_category_names[i] + " category")))
            i = i + 1
        bpy.types.Scene.mat_lib_material_category = bpy.props.EnumProperty(items = category_enum_items, name = "", description = "Choose a category", update=libraryCategoryUpdate)
        bpy.context.scene.mat_lib_material_category = "None0";
        
        #No errors - set working mode
        working_mode = self.mode
        
        self.report({'INFO'}, "Retrieved library!")
        
        return {'FINISHED'}

class LibraryInfo(bpy.types.Operator):
    '''Display add-on info'''
    bl_idname = "material.libraryinfo"
    bl_label = "Display add-on info"

    def execute(self, context):
        global category_type
        
        category_type = "info"
        
        return {'FINISHED'}

class LibraryTools(bpy.types.Operator):
    '''Display material tools'''
    bl_idname = "material.librarytools"
    bl_label = "Display material tools"

    def execute(self, context):
        global category_type
        
        category_type = "tools"
        
        return {'FINISHED'}

class LibrarySettings(bpy.types.Operator):
    '''Display add-on settings'''
    bl_idname = "material.librarysettings"
    bl_label = "Display add-on settings"

    def execute(self, context):
        global category_type
        global mat_lib_cached_files
        
        category_type = "settings"
        if library == "":
            return {'FINISHED'}
        elif library == "bundled":
            mat_lib_cached_files = -2
            return {'FINISHED'}
        elif library == "composite":
            cached_data_path = os.path.join(matlibpath, mat_lib_host, "cycles" + os.sep)
        else:
            cached_data_path = os.path.join(matlibpath, mat_lib_host, library, "cycles" + os.sep)
        mat_lib_cached_files = 0
        for root, dirs, files in os.walk(cached_data_path):
            for name in files:
                if ".jpg" in name.lower():
                    mat_lib_cached_files += 1
                elif ".png" in name.lower():
                    mat_lib_cached_files += 1
                elif ".osl" in name.lower():
                    mat_lib_cached_files += 1
                elif ".osl" in name.lower():
                    mat_lib_cached_files += 1
                elif ".bcm" in name:
                    mat_lib_cached_files += 1
                elif ".bcg" in name:
                    mat_lib_cached_files += 1
        
        return {'FINISHED'}

class LibraryHome(bpy.types.Operator):
    '''Go back'''
    bl_idname = "material.libraryhome"
    bl_label = "Go back"

    def execute(self, context):
        global category_type
        
        category_type = "none"
        
        return {'FINISHED'}

def libraryCategoryUpdate(self, context):
    print("Updating Material Category.")        
        
    global category_contents
    global category_name
    global category_filename
    global category_materials
    
    global material_names
    global material_filenames
    global material_contributors
    global material_ratings
    global material_fireflies
    global material_speeds
    global material_complexities
    global material_groups
    global material_scripts
    global material_images
    global material_filesizes
    global material_dimensions
    global material_tileabilities
    global material_lines
    
    global current_material_number
    
    global category_type
    global category_special
    
    #Check if the category is None
    if bpy.context.scene.mat_lib_material_category != "None0":
        #Selected category is not None; select category.
        
        findLibrary()
    
        i = 0
        while i < len(category_enum_items):
            if category_enum_items[i][0] == bpy.context.scene.mat_lib_material_category:
                #Set category filename for refresh button
                category_filename = mat_lib_category_filenames[i - 1]
                #Set category name for special type checking
                category_name = mat_lib_category_names[i - 1]
                category_index = i - 1
            i = i + 1
        
        current_material_number = -1
        
        material_names = []
        material_filenames = []
        material_contributors = []
        material_ratings = []
        material_fireflies = []
        material_speeds = []
        material_complexities = []
        material_groups = []
        material_scripts = []
        material_images = []
        material_filesizes = []
        material_dimensions = []
        material_tileabilities = []
        material_lines = []
        
        for mat in library_data[category_index].materials:
            if (bpy.context.scene.mat_lib_show_osl_materials or mat.scripts == '0') and (bpy.context.scene.mat_lib_show_textured_materials or mat.images == '0'):
                #Get material names
                material_names.append(mat.name)
                #Get material filenames
                material_filenames.append(mat.href)
                #Get material contributors
                material_contributors.append(mat.contrib)
                #Get material ratings
                material_ratings.append(mat.stars)
                #Get material firefly levels
                material_fireflies.append(mat.fireflies)
                #Get material render speeds
                material_speeds.append(mat.speed)
                #Get material complexities
                material_complexities.append(mat.complexity)
                #Get material node groups
                material_groups.append(mat.groups)
                #Get material OSL scripts
                material_scripts.append(mat.scripts)
                #Get material image textures
                material_images.append(mat.images)
                #Get material filesizes
                material_filesizes.append(mat.filesize)
                #Get material image size
                material_dimensions.append(mat.dimensions)
                #Get material image tileabilities
                material_tileabilities.append(mat.tileable)
                #Get material script code lines
                material_lines.append(mat.lines)
        
        #Set amount of materials in selected category
        category_materials = len(material_names)
        
        category_type = "category"
        
        category_special = "none"
        if category_name == "Nodegroups" or category_name == "Image Textures" or category_name == "OSL Scripts":
            category_special = category_name
        
        #else:
        #    self.report({'ERROR'}, "Invalid category! See console for details.")
        #    print ("Invalid category!")
        #    print (category_contents)
    else:
        #Selected category is None
        category_contents = "None"
        current_material_number = -1
        category_type = "none"
    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) >= 2.66 and context.active_object.material_slots[-1].material.name == "mat_lib_preview_material":
        bpy.ops.material.libraryremovepreview()

category_enum_items = [("None0", "None", "No category selected")]
bpy.types.Scene.mat_lib_material_category = bpy.props.EnumProperty(items = category_enum_items, name = "", description = "Choose a category", update=libraryCategoryUpdate)

def matDetails(self, context, inforowcol):
    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) >= 2.66 and (category_special == "none" or category_special == "Image Textures"):
        inforowcolrow = inforowcol.row()
        if material_contributors[current_material_number] != "Unknown":
            inforowcolrow.label(text="By %s." % material_contributors[current_material_number])
        else:
            inforowcolrow.label(text="Author unknown.")
    
    inforowcolrow = inforowcol.row()
        
    if category_special != 'none':
        inforowcolrow.label(text="Filesize: %s" % material_filesizes[current_material_number])
        inforowcolrow = inforowcol.row()
        
        if category_special != "Image Textures":
            if material_complexities[current_material_number] == "simple":
                inforowcolrow.label(text="Complexity: Simple")
            elif material_complexities[current_material_number] == "intermediate":
                inforowcolrow.label(text="Complexity: Intermediate")
            elif material_complexities[current_material_number] == "complex":
                inforowcolrow.label(text="Complexity: Complex")
        else:
            inforowcolrow.label(text="Size: %s px" % material_dimensions[current_material_number])
                
        if category_special == "OSL Scripts":
            inforowcolrow = inforowcol.row()
            inforowcolrow.label(text="Lines: %s" % material_lines[current_material_number])
        else:
            if category_special == "Image Textures":
                inforowcolrow = inforowcol.row()
                inforowcolrow.label(text="Extension: %s" % material_filenames[current_material_number][-3:].upper())
        
            inforowcolrow = inforowcol.row()
            if material_tileabilities[current_material_number] == "yes":
                inforowcolrow.label(text="Tileable: Yes")
            elif material_tileabilities[current_material_number] == "no":
                inforowcolrow.label(text="Tileable: No")
            elif material_tileabilities[current_material_number] != "n/a":
                inforowcolrow.label(text="Tileable: Unknown")
    else:
        if material_fireflies[current_material_number] == "high":
            inforowcolrow.label(text="Firefly Level: High")
            inforowcolrow.label(text="", icon='PARTICLES')
        elif material_fireflies[current_material_number] == "medium":
            inforowcolrow.label(text="Firefly Level: Medium")
            inforowcolrow.label(text="", icon='MOD_PARTICLES')
        else:
            inforowcolrow.label(text="Firefly Level: Low")
        inforowcolrow = inforowcol.row()
        
        if material_complexities[current_material_number] == "simple":
            inforowcolrow.label(text="Complexity: Simple")
        elif material_complexities[current_material_number] == "intermediate":
            inforowcolrow.label(text="Complexity: Intermediate")
        elif material_complexities[current_material_number] == "complex":
            inforowcolrow.label(text="Complexity: Complex")
        inforowcolrow = inforowcol.row()
        
        if material_speeds[current_material_number] == "slow":
            inforowcolrow.label(text="Render Speed: Slow")
            inforowcolrow.label(text="", icon='PREVIEW_RANGE')
        elif material_speeds[current_material_number] == "fair":
            inforowcolrow.label(text="Render Speed: Fair")
            inforowcolrow.label(text="", icon='TIME')
        else:
            inforowcolrow.label(text="Render Speed: Good")
        inforowcolrow = inforowcol.row()
        if material_groups[current_material_number] == "0":
            inforowcolrow.label(text="Node Groups: 0")
        else:
            inforowcolrow.label(text="Node Groups: %s" % material_groups[current_material_number])
            inforowcolrow.label(text="", icon='NODETREE')
        inforowcolrow = inforowcol.row()
        
        if material_scripts[current_material_number] == "0":
            inforowcolrow.label(text="OSL Scripts: 0")
        else:
            inforowcolrow.label(text="OSL Scripts: %s" % material_scripts[current_material_number])
            inforowcolrow.label(text="", icon='TEXT')
        inforowcolrow = inforowcol.row()
        
        if material_images[current_material_number] == "0":
            inforowcolrow.label(text="Images: 0")
        else:
            inforowcolrow.label(text="Images: %s" % material_images[current_material_number])
            inforowcolrow.label(text="", icon='IMAGE_RGB')

class ViewMaterial(bpy.types.Operator):
    '''View material details'''
    bl_idname = "material.libraryviewmaterial"
    bl_label = "view material details"
    material = bpy.props.IntProperty()
    
    def execute(self, context):
        global current_material_number
        global current_material_cached
        global current_material_previewed
        
        findLibrary()
        
        if current_material_number == self.material:
            if current_material_previewed:
                current_material_previewed = True
            else:
                current_material_previewed = False
        else:
            current_material_previewed = False
        
        current_material_number = self.material
        current_material_cached = False
        
        if self.material == -1:
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) >= 2.66 and context.active_object.material_slots[-1].material.name == "mat_lib_preview_material":
                bpy.ops.material.libraryremovepreview()
            return {'FINISHED'}
        
        if library == "composite":
            if os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, material_filenames[self.material] + ".bcm")):
                current_material_cached = True
        elif library != "bundled":
            if os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, material_filenames[self.material] + ".bcm")):
                current_material_cached = True
        
        if context.scene.mat_lib_auto_preview == True:
            bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
            if len(preview_message) == 2:
                self.report({preview_message[0]}, preview_message[1])
        elif working_mode == "offline":
            bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
            if len(preview_message) == 2:
                self.report({preview_message[0]}, preview_message[1])
        elif library == "composite":
            if os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, material_filenames[self.material] + ".jpg")):
                bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
                self.report({preview_message[0]}, preview_message[1])
            else:
                bpy.data.images["mat_lib_preview_image.jpg"].source = 'GENERATED'
                bpy.data.images["mat_lib_preview_image.jpg"].generated_width = 128
                bpy.data.images["mat_lib_preview_image.jpg"].generated_height = 128
                #Do everything possible to get Blender to update the preview.
                bpy.data.images["mat_lib_preview_image.jpg"].reload()
                bpy.ops.wm.redraw_timer()
                bpy.data.scenes[bpy.context.scene.name].update()
                bpy.data.scenes[bpy.context.scene.name].frame_set(bpy.data.scenes[bpy.context.scene.name].frame_current)
        else:
            if os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, material_filenames[self.material] + ".jpg")):
                bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
                self.report({preview_message[0]}, preview_message[1])
            else:
                bpy.data.images["mat_lib_preview_image.jpg"].source = 'GENERATED'
                bpy.data.images["mat_lib_preview_image.jpg"].generated_width = 128
                bpy.data.images["mat_lib_preview_image.jpg"].generated_height = 128
                #Do everything possible to get Blender to update the preview.
                bpy.data.images["mat_lib_preview_image.jpg"].reload()
                bpy.ops.wm.redraw_timer()
                bpy.data.scenes[bpy.context.scene.name].update()
                bpy.data.scenes[bpy.context.scene.name].frame_set(bpy.data.scenes[bpy.context.scene.name].frame_current)
        return {'FINISHED'}

class LibraryClearCache(bpy.types.Operator):
    '''Delete active library's cached previews, materials, textures, scripts, and node groups'''
    bl_idname = "material.libraryclearcache"
    bl_label = "delete cached previews and materials"
    
    def execute(self, context):
        global mat_lib_cached_files
        findLibrary()
        
        if library == "bundled":
            self.report({'ERROR'}, "The bundled library is local only and contains no cached online data.")
            return {'CANCELLED'}
        elif library == "composite":
            cached_data_path = os.path.join(matlibpath, mat_lib_host, "cycles" + os.sep)
        elif library == "testing" or library == "release":
            cached_data_path = os.path.join(matlibpath, mat_lib_host, library, "cycles" + os.sep)
        elif library == "":
            self.report({'ERROR'}, "No library selected!")
            return {'CANCELLED'}
        else:
            self.report({'ERROR'}, "Unrecognized library type!")
            return {'CANCELLED'}
        
        for root, dirs, files in os.walk(cached_data_path):
            for name in files:
                if name[-4:].lower() == ".jpg":
                    print("Deleting \"" + os.path.join(root, name) + "\".")
                    os.remove(os.path.join(root, name))
                elif name[-4:].lower() == ".png":
                    print("Deleting \"" + os.path.join(root, name) + "\".")
                    os.remove(os.path.join(root, name))
                elif name[-4:].lower() == ".osl":
                    print("Deleting \"" + os.path.join(root, name) + "\".")
                    os.remove(os.path.join(root, name))
                elif name[-4:].lower() == ".oso":
                    print("Deleting \"" + os.path.join(root, name) + "\".")
                    os.remove(os.path.join(root, name))
                elif name[-4:].lower() == ".bcg":
                    print("Deleting \"" + os.path.join(root, name) + "\".")
                    os.remove(os.path.join(root, name))
                elif name[-4:].lower() == ".bcm":
                    print("Deleting \"" + os.path.join(root, name) + "\".")
                    os.remove(os.path.join(root, name))
        
        mat_lib_cached_files = 0
        
        self.report({'INFO'}, "Preview cache cleared.")
        return {'FINISHED'}

class LibraryPreview(bpy.types.Operator):
    '''Preview material'''
    bl_idname = "material.librarypreview"
    bl_label = "preview material"
    name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
        
    def execute(self, context):
        global parent_category_filename
        global category_filename
        global preview_message
        global library
        global current_material_previewed
        
        findLibrary()
        
        previewed = 'status_none'
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.66 and category_special != "OSL Scripts" and category_special != "Nodegroups":
            if category_special == "Image Textures":
                self.filename = self.filename[:self.filename.rindex(".")] + "_preview"
            
            #Check for a cached preview
            if library == "bundled":
                image_path = os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename + ".jpg")
            elif library == "composite":
                image_path = os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".jpg")
            else:
                image_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".jpg")
            
            if os.path.exists(image_path):
                #Cached preview exists
                cached_image = open(image_path, 'r+b')
                response = cached_image.read()
                cached_image.close()
                f = open(os.path.join(matlibpath, "mat_lib_preview_image.jpg"), 'w+b')
                f.write(response)
                f.close()
                previewed = 'status_applied'
                
            elif working_mode == "online":
                #This preview doesn't exist yet; let's download it.
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".jpg")
                response = connection.getresponse().read()
                f = open(os.path.join(matlibpath, "mat_lib_preview_image.jpg"), 'w+b')
                f.write(response)
                f.close()
                
                #Cache this preview
                f = open(image_path, 'w+b')
                f.write(response)
                f.close()
                previewed = 'status_applied'
                
            elif category_special == 'none' or category_special == 'Image Textures':
                previewed = 'status_cannot_download'
            
            #Check if has texture
            if bpy.data.images.find("mat_lib_preview_image.jpg") == -1:
                bpy.ops.image.open(filepath=os.path.join(matlibpath, "mat_lib_preview_image.jpg"))
            
            if "mat_lib_preview_texture" not in bpy.data.textures:
                 bpy.data.textures.new("mat_lib_preview_texture", "IMAGE")
            
            if not previewed:
                bpy.data.images["mat_lib_preview_image.jpg"].source = 'GENERATED'
                bpy.data.images["mat_lib_preview_image.jpg"].generated_width = 128
                bpy.data.images["mat_lib_preview_image.jpg"].generated_height = 128
            else:
                bpy.data.images["mat_lib_preview_image.jpg"].source = 'FILE'
            
            if bpy.data.textures["mat_lib_preview_texture"].image != bpy.data.images["mat_lib_preview_image.jpg"]:
                bpy.data.textures["mat_lib_preview_texture"].image = bpy.data.images["mat_lib_preview_image.jpg"]
            
            if bpy.data.images["mat_lib_preview_image.jpg"].filepath != os.path.join(matlibpath, "mat_lib_preview_image.jpg"):
                bpy.data.images["mat_lib_preview_image.jpg"].filepath = os.path.join(matlibpath, "mat_lib_preview_image.jpg")
                
            #Do everything possible to get Blender to update the preview.
            bpy.data.images["mat_lib_preview_image.jpg"].reload()
            bpy.ops.wm.redraw_timer()
            bpy.data.scenes[bpy.context.scene.name].update()
            bpy.data.scenes[bpy.context.scene.name].frame_set(bpy.data.scenes[bpy.context.scene.name].frame_current)
        elif category_special == "none":
            if bpy.data.materials.find("mat_lib_preview_material") == -1:
                preview_material = bpy.data.materials.new("mat_lib_preview_material")
                preview_material.use_nodes = True
            else:
                preview_material = bpy.data.materials["mat_lib_preview_material"]
            if len(context.active_object.material_slots) == 0 or context.active_object.material_slots[-1].material.name != "mat_lib_preview_material":
                bpy.ops.object.material_slot_add()
                context.active_object.material_slots[context.active_object.active_material_index].material = preview_material
            context.active_object.active_material_index = len(context.active_object.material_slots) - 1
            bpy.ops.material.libraryapply(mat_name="mat_lib_preview_material", filename=material_filenames[current_material_number])
            previewed = 'status_applied'
        elif category_special == "Image Textures":
            self.filename = self.filename[:self.filename.rindex(".")] + "_preview"
            
            #Check for a cached preview
            if library == "bundled":
                image_path = os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename + ".jpg")
            elif library == "composite":
                image_path = os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".jpg")
            else:
                image_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".jpg")
            
            if os.path.exists(image_path):
                #Cached preview exists
                cached_image = open(image_path, 'r+b')
                response = cached_image.read()
                cached_image.close()
                f = open(os.path.join(matlibpath, "mat_lib_preview_image.jpg"), 'w+b')
                f.write(response)
                f.close()
                previewed = 'status_applied'
                
            elif working_mode == "online":
                #This preview doesn't exist yet; let's download it.
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".jpg")
                response = connection.getresponse().read()
                f = open(os.path.join(matlibpath, "mat_lib_preview_image.jpg"), 'w+b')
                f.write(response)
                f.close()
                
                #Cache this preview
                f = open(image_path, 'w+b')
                f.write(response)
                f.close()
                previewed = 'status_applied'
                
            else:
                previewed = 'status_cannot_download'
            
            if bpy.data.images.find("mat_lib_preview_image.jpg") == -1:
                bpy.ops.image.open(filepath=os.path.join(matlibpath, "mat_lib_preview_image.jpg"))
            
            if bpy.data.materials.find("mat_lib_preview_material") == -1:
                preview_material = bpy.data.materials.new("mat_lib_preview_material")
                preview_material.use_nodes = True
            else:
                preview_material = bpy.data.materials["mat_lib_preview_material"]
            if len(context.active_object.material_slots) == 0 or context.active_object.material_slots[-1].material.name != "mat_lib_preview_material":
                bpy.ops.object.material_slot_add()
                context.active_object.material_slots[context.active_object.active_material_index].material = preview_material
            context.active_object.active_material_index = len(context.active_object.material_slots) - 1
            
            bpy.data.images["mat_lib_preview_image.jpg"].reload()
            
            #Set up material to preview this image
            bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.clear()
            bpy.data.materials["mat_lib_preview_material"].preview_render_type = 'FLAT'
            output_node = bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.new(node_types['SHADER']["OUTPUT_MATERIAL"])
            output_node.location = [200, 100]
            emission_node = bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.new(node_types['SHADER']["EMISSION"])
            emission_node.location = [0, 100]
            emission_node.inputs['Strength'].default_value = 1.0
            image_node = bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.new(node_types['SHADER']["TEX_IMAGE"])
            image_node.location = [-200, 100]
            image_node.image = bpy.data.images['mat_lib_preview_image.jpg']
            if material_tileabilities[current_material_number] == "yes":
                mapping_node = bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.new(node_types['SHADER']["MAPPING"])
                mapping_node.location = [-500, 100]
                mapping_node.scale = [2.0, 2.0, 2.0]
                coords_node = bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.new(node_types['SHADER']["TEX_COORD"])
                coords_node.location = [-700, 100]
            else:
                coords_node = bpy.data.materials["mat_lib_preview_material"].node_tree.nodes.new(node_types['SHADER']["TEX_COORD"])
                coords_node.location = [-400, 100]
            
            bpy.data.materials["mat_lib_preview_material"].node_tree.links.new(output_node.inputs['Surface'], emission_node.outputs['Emission'])
            bpy.data.materials["mat_lib_preview_material"].node_tree.links.new(emission_node.inputs['Color'], image_node.outputs['Color'])
            if material_tileabilities[current_material_number] == "yes":
                bpy.data.materials["mat_lib_preview_material"].node_tree.links.new(image_node.inputs['Vector'], mapping_node.outputs['Vector'])
                bpy.data.materials["mat_lib_preview_material"].node_tree.links.new(mapping_node.inputs['Vector'], coords_node.outputs['Window'])
            else:
                bpy.data.materials["mat_lib_preview_material"].node_tree.links.new(image_node.inputs['Vector'], coords_node.outputs['Window'])
        
        current_material_previewed = False
        if previewed == 'status_applied':
            self.report({'INFO'}, "Preview applied.")
            preview_message = ['INFO', "Preview applied."]
            current_material_previewed = True
        elif previewed == 'status_cannot_download':
            self.report({'WARNING'}, "Preview does not exist; cannot download in offline mode.")
            preview_message = ['WARNING', "Preview does not exist; cannot download in offline mode."]
        else:
            preview_message = []
        
        return {'FINISHED'}

class LibraryRemovePreview(bpy.types.Operator):
    '''Remove preview'''
    bl_idname = "material.libraryremovepreview"
    bl_label = "remove preview material"
    name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
        
    def execute(self, context):
        global current_material_previewed
        
        findLibrary()
        context.active_object.active_material_index = len(context.active_object.material_slots) - 1
        bpy.ops.object.material_slot_remove()
        
        current_material_previewed = False
        
        return {'FINISHED'}

class AddLibraryMaterial(bpy.types.Operator):
    '''Add material to scene'''
    bl_idname = "material.libraryadd"
    bl_label = "add material to scene"
    mat_name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    open_location = bpy.props.StringProperty()
    text_block = bpy.props.StringProperty()
    
    def execute(self, context):
        global material_file_contents
        global library
        global node_message
        global current_material_cached
        global osl_scripts
        global node_groups
        global mapping_curves
        
        findLibrary()
        
        if self.open_location == "" and self.text_block == "":
            if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm")):
                bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm"), mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm")):
                bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm"), mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename + ".bcm")):
                bcm_file = open(os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename + ".bcm"), mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif working_mode == "online":
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".bcm")
                response = connection.getresponse().read()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in str(response)[2:40]:
                    self.report({'ERROR'}, "Material file is either outdated or invalid.")
                    self.filename = ""
                    return {'CANCELLED'}
                
                #Cache material
                if library == "composite":
                    bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm"), mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                else:
                    bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm"), mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                
                material_file_contents = str(response)
            else:
                self.report({'ERROR'}, "Material is not cached; cannot download in offline mode!")
                return {'CANCELLED'}
            print (material_file_contents)
            mat_name = self.mat_name
        elif self.open_location is not "":
            if ".bcm" in self.open_location:
                bcm_file = open(self.open_location, mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in material_file_contents:
                    self.open_location = ""
                    self.report({'ERROR'}, "Material file is either outdated or invalid.")
                    return {'CANCELLED'}
                mat_name = ""
                for word in self.open_location.split(os.sep)[-1][:-4].split("_"):
                    if mat_name is not "":
                        mat_name += " "
                    mat_name += word.capitalize()
            else:
                self.report({'ERROR'}, "Not a .bcm file.")
                self.open_location = ""
                return {'CANCELLED'}
        else:
            if self.text_block in bpy.data.texts:
                #Read from a text datablock
                material_file_contents = bpy.data.texts[self.text_block].as_string()
            else:
                self.report({'ERROR'}, "Requested text block does not exist.")
                self.text_block = ""
                return {'CANCELLED'}
                
            print(material_file_contents)
            #Check file for validitity
            if '<?xml version="1.0" encoding="UTF-8"?>' not in material_file_contents[0:40]:
                self.report({'ERROR'}, "Material data is either outdated or invalid.")
                self.text_block = ""
                return {'CANCELLED'}
            mat_name = ""
            
            separator = ""
            if context.scene.mat_lib_bcm_name is "":
                separator = ""
                if "_" in self.text_block:
                    separator = "_"
                elif "-" in self.text_block:
                    separator = "-"
                elif " " in self.text_block:
                    separator = " "
                    
                if separator is not "":
                    for word in self.text_block.split(separator):
                        if mat_name is not "":
                            mat_name += " "
                        mat_name += word.capitalize()
                else:
                    mat_name = self.text_block
            else:
                mat_name = context.scene.mat_lib_bcm_name
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[0:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.mat_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Material file is either invalid or outdated.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Create new material
        new_mat = bpy.data.materials.new(mat_name)
        new_mat.use_nodes = True
        new_mat.node_tree.nodes.clear()
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        #Create internal OSL scripts
        scripts = dom.getElementsByTagName("script")
        osl_scripts = []
        for s in scripts:
            osl_datablock = bpy.data.texts.new(name=s.attributes['name'].value)
            osl_text = s.toxml()[s.toxml().index(">"):s.toxml().rindex("<")]
            osl_text = osl_text[1:].replace("<br/>","\n").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&amp;", "&")
            osl_datablock.write(osl_text)
            osl_scripts.append(osl_datablock)
        
        #Create internal node groups
        groups = dom.getElementsByTagName("group")
        node_groups = []
        for g in groups:
            group_text = g.toxml()#[g.toxml().index(">"):g.toxml().rindex("<")]
            group_datablock = addNodeGroup(g.attributes['name'].value, group_text)
            node_groups.append(group_datablock)
        
        #Prepare curve data
        mapping_curves = []
        curves = dom.getElementsByTagName("curve")
        for curve in curves:
            curve_points = []
            cdom = xml.dom.minidom.parseString(curve.toxml())
            points = cdom.getElementsByTagName("point")
            for point in points:
                loc_x = float(point.attributes['loc'].value.replace(" ", "").split(",")[0])
                loc_y = float(point.attributes['loc'].value.replace(" ", "").split(",")[1])
                curve_points.append(curvePoint(point.attributes['type'].value, loc_x, loc_y))
            mapping_curves.append(mappingCurve(curve.attributes['extend'].value, curve_points))
        
        #Add nodes
        nodes = dom.getElementsByTagName("node")
        addNodes(nodes, new_mat.node_tree)
        if node_message:
            self.report({node_message[0]}, node_message[1])
            if node_message[0] == "ERROR":
                node_message = []
                self.mat_name = ""
                self.filename = ""
                self.open_location = ""
                self.text_block = ""
                return {'CANCELLED'}
            node_message = []
        
        #Create links
        links = dom.getElementsByTagName("link")
        createLinks(links, new_mat.node_tree)
        
        m = dom.getElementsByTagName("material")[0]
        
        #Set viewport color
        new_mat.diffuse_color = color(m.attributes["view_color"].value)
        
        valid_preview_types = ['FLAT', 'SPHERE', 'CUBE', 'MONKEY', 'HAIR', 'SPHERE_A']
        if "preview_type" in m.attributes and m.attributes['preview_type'].value in valid_preview_types:
            new_mat.preview_render_type = m.attributes['preview_type'].value
            
        #Set sample-as-lamp-ness
        if m.attributes["sample_lamp"].value == "True":
            sample_lamp = True
        else:
            sample_lamp = False
        new_mat.cycles.sample_as_light = sample_lamp
        
        self.mat_name = ""
        self.filename = ""
        self.open_location = ""
        self.text_block = ""
        self.report({'INFO'}, "Material added.")
        current_material_cached = True
        
        return {'FINISHED'}

class ApplyLibraryMaterial(bpy.types.Operator):
    '''Apply to active material'''
    bl_idname = "material.libraryapply"
    bl_label = "Apply to active material"
    mat_name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    open_location = bpy.props.StringProperty()
    text_block = bpy.props.StringProperty()
    
    def execute(self, context):
        global material_file_contents
        global library
        global node_message
        global current_material_cached
        global osl_scripts
        global node_groups
        global mapping_curves
        
        findLibrary()
        
        mat_name = ""
        material_file_contents = ""
        if not bpy.context.active_object:
            self.mat_name = ""
            self.filename = ""
            self.open_location = ""
            self.text_block = ""
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        if self.open_location == "" and self.text_block == "":
            if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm")):
                bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm"), mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm")):
                bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm"), mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename + ".bcm")):
                bcm_file = open(os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename + ".bcm"), mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif working_mode == "online":
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".bcm")
                response = connection.getresponse().read()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in str(response)[2:40]:
                    self.report({'ERROR'}, "Material file is either outdated or invalid.")
                    self.mat_name = ""
                    self.filename = ""
                    return {'CANCELLED'}
                
                #Cache material
                if library == "composite":
                    bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm"), mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                else:
                    bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm"), mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                
                material_file_contents = str(response)
            else:
                self.report({'ERROR'}, "Material is not cached; cannot download in offline mode!")
                self.mat_name = ""
                self.filename = ""
                return {'CANCELLED'}
            mat_name = self.mat_name
        elif self.open_location is not "":
            if ".bcm" in self.open_location:
                material_file_contents = ""
                bcm_file = open(self.open_location, mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
                
                mat_name = ""
                for word in self.open_location.split(os.sep)[-1][:-4].split("_"):
                    if mat_name is not "":
                        mat_name += " "
                    mat_name += word.capitalize()
            else:
                self.open_location = ""
                self.report({'ERROR'}, "Not a .bcm file.")
                return {'CANCELLED'}
        else:
            if self.text_block in bpy.data.texts:
                #Read from a text datablock
                material_file_contents = ""
                material_file_contents = bpy.data.texts[self.text_block].as_string()
            else:
                self.report({'ERROR'}, "Requested text block does not exist.")
                self.text_block = "";
                return {'CANCELLED'}
            
            if context.scene.mat_lib_bcm_name is "":
                separator = ""
                if "_" in self.text_block:
                    separator = "_"
                elif "-" in self.text_block:
                    separator = "-"
                elif " " in self.text_block:
                    separator = " "
                    
                if separator is not "":
                    for word in self.text_block.split(separator):
                        if mat_name is not "":
                            mat_name += " "
                        mat_name += word.capitalize()
                else:
                    mat_name = self.text_block
            else:
                mat_name = context.scene.mat_lib_bcm_name
        
        
        if context.active_object.active_material:
            context.active_object.active_material.name = mat_name
        else:
            new_material = bpy.data.materials.new(mat_name)
            if len(context.active_object.material_slots.keys()) is 0:
                bpy.ops.object.material_slot_add()
            context.active_object.material_slots[context.active_object.active_material_index].material = new_material
        
        #Prepare material for new nodes
        context.active_object.active_material.use_nodes = True
        context.active_object.active_material.node_tree.nodes.clear()
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[0:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.mat_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Material file is either invalid or outdated.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        #Create internal OSL scripts
        scripts = dom.getElementsByTagName("script")
        osl_scripts = []
        for s in scripts:
            osl_datablock = bpy.data.texts.new(name=s.attributes['name'].value)
            osl_text = s.toxml()[s.toxml().index(">"):s.toxml().rindex("<")]
            osl_text = osl_text[1:].replace("<br/>","\n").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&amp;", "&")
            osl_datablock.write(osl_text)
            osl_scripts.append(osl_datablock)
        
        #Create internal node groups
        groups = dom.getElementsByTagName("group")
        node_groups = []
        for g in groups:
            group_text = g.toxml()
            group_datablock = addNodeGroup(g.attributes['name'].value, group_text)
            node_groups.append(group_datablock)
        
        #Prepare curve data
        mapping_curves = []
        curves = dom.getElementsByTagName("curve")
        for curve in curves:
            curve_points = []
            cdom = xml.dom.minidom.parseString(curve.toxml())
            points = cdom.getElementsByTagName("point")
            for point in points:
                loc_x = float(point.attributes['loc'].value.replace(" ", "").split(",")[0])
                loc_y = float(point.attributes['loc'].value.replace(" ", "").split(",")[1])
                curve_points.append(curvePoint(point.attributes['type'].value, loc_x, loc_y))
            mapping_curves.append(mappingCurve(curve.attributes['extend'].value, curve_points))
        
        #Add nodes
        nodes = dom.getElementsByTagName("node")
        addNodes(nodes, context.active_object.active_material.node_tree)
        if node_message:
            self.report({node_message[0]}, node_message[1])
            if node_message[0] == "ERROR":
                node_message = []
                self.mat_name = ""
                self.filename = ""
                self.open_location = ""
                self.text_block = ""
                return {'CANCELLED'}
            node_message = []
            
        #Create links
        links = dom.getElementsByTagName("link")
        createLinks(links, context.active_object.active_material.node_tree)
        
        m = dom.getElementsByTagName("material")[0]
        
        #Set viewport color
        context.active_object.active_material.diffuse_color = color(m.attributes["view_color"].value)
        
        valid_preview_types = ['FLAT', 'SPHERE', 'CUBE', 'MONKEY', 'HAIR', 'SPHERE_A']
        if "preview_type" in m.attributes and m.attributes['preview_type'].value in valid_preview_types:
            context.active_object.active_material.preview_render_type = m.attributes['preview_type'].value
        else:
            context.active_object.active_material.preview_render_type = 'SPHERE'
        
        #Set sample-as-lamp-ness
        if boolean(m.attributes["sample_lamp"].value):
            sample_lamp = True
        else:
            sample_lamp = False
        context.active_object.active_material.cycles.sample_as_light = sample_lamp
        
        self.mat_name = ""
        self.filename = ""
        self.open_location = ""
        self.text_block = ""
        self.report({'INFO'}, "Material applied.")
        current_material_cached = True
        
        return {'FINISHED'}

class CacheLibraryMaterial(bpy.types.Operator):
    '''Cache material to disk'''
    bl_idname = "material.librarycache"
    bl_label = "cache material to disk"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global material_file_contents
        global current_material_cached
        
        findLibrary()
        
        if working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".bcm")
            response = connection.getresponse().read()
        else:
            self.report({'ERROR'}, "Cannot cache material in offline mode.")
            return {'CANCELLED'}
        
        material_file_contents = str(response)
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[2:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.report({'ERROR'}, "Invalid material file.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        #Create external OSL scripts and nodegroups, and cache image textures
        nodes = dom.getElementsByTagName("node")
        for node in nodes:
            node_data = node.attributes
            if node_data['type'].value == "TEX_IMAGE" or node_data['type'].value == "TEX_ENVIRONMENT":
                if node_data['image'].value and '.' in node_data['image'].value:
                    if "file://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot cache image texture located at %s." % node_data['image'].value)
                    elif "http://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot cache image texture hosted at %s." % node_data['image'].value)
                    else:
                        ext = "." + node_data['image'].value.split(".")[-1]
                        image_name = node_data['image'].value[:-4]
                        
                        if ext.lower() != ".jpg" and ext.lower() != ".png":
                            node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                            else:
                                image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                        else:
                            node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                            image_filepath = ""
            elif node_data['type'].value == "SCRIPT":
                if node_data['script'].value and '.' in node_data['script'].value:
                    if "file://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot cache OSL script located at %s." % node_data['script'].value)
                    elif "http://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot cache OSL script hosted at %s." % node_data['script'].value)
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                            else:
                                script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            script_filepath = ""
            elif node_data['type'].value == "GROUP":
                if node_data['group'].value and '.' in node_data['group'].value:
                    if "file://" in node_data['group'].value:
                        self.report({'ERROR'}, "Cannot cache nodegroup located at %s." % node_data['group'].value)
                    elif "http://" in node_data['group'].value:
                        self.report({'ERROR'}, "Cannot cache nodegroup hosted at %s." % node_data['group'].value)
                    else:
                        group_name = node_data['group'].value[:-4]
                        
                        if ("." + node_data['group'].value.split(".")[-1]).lower != ".bcg":
                            node_message = ['ERROR', "The nodegroup file referenced by this group node is not .bcg; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")):
                            group_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")):
                            group_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "groups", group_name + ".bcg")):
                            group_filepath = os.path.join(matlibpath, "bundled", "cycles", "groups", group_name + ".bcg")
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/groups/" + group_name + ".bcg")
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                group_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")
                                group_file = open(group_filepath, mode="w+b")
                                group_file.write(response)
                                group_file.close()
                            else:
                                group_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")
                                group_file = open(group_filepath, mode="w+b")
                                group_file.write(response)
                                group_file.close()
                        else:
                            node_message = ['ERROR', "The nodegroup file, \"%s\", is not cached; cannot download in offline mode." % (group_name + ".bcg")]
                            group_filepath = ""
                    
        
        if library == "composite":
            bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcm"), mode="w+b")
            bcm_file.write(response)
            bcm_file.close()
        elif library != "bundled":
            bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcm"), mode="w+b")
            bcm_file.write(response)
            bcm_file.close()
        else:
            self.report({'ERROR'}, "Cannot cache materials from this library.")
            return {'CANCELLED'}
            
        current_material_cached = True
        self.report({'INFO'}, "Material cached.")
        return {'FINISHED'}

class SaveLibraryMaterial(bpy.types.Operator, ExportHelper):
    '''Save material to disk'''
    bl_idname = "material.librarysave"
    bl_label = "Save material to disk"
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    
    #ExportHelper uses this
    filename_ext = ".bcm"

    filter_glob = bpy.props.StringProperty(
            default="*.bcm",
            options={'HIDDEN'},
            )
    
    def execute(self, context):
        global material_file_contents
        global save_filename
        global current_material_cached
        
        findLibrary()
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename)):
            bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename), mode="r+b")
            response = bcm_file.read()
            bcm_file.close()
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename)):
            bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename), mode="r+b")
            response = bcm_file.read()
            bcm_file.close()
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename)):
            bcm_file = open(os.path.join(matlibpath, "bundled", "cycles", category_filename, self.filename), mode="r+b")
            response = bcm_file.read()
            bcm_file.close()
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache material
            if library == "composite":
                bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename), mode="w+b")
                bcm_file.write(response)
                bcm_file.close()
            else:
                bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename), mode="w+b")
                bcm_file.write(response)
                bcm_file.close()
        else:
            self.report({'ERROR'}, "Material is not cached; cannot download in offline mode.")
            return {'FINISHED'}
        
        material_file_contents = str(response)
        
        bcm_file = open(self.filepath, mode="w+b")
        bcm_file.write(response)
        bcm_file.close()
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[0:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.report({'ERROR'}, "Invalid material file.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        bcm_file = open(self.filepath, mode="r", encoding="UTF-8")
        material_file_contents = bcm_file.read()
        bcm_file.close()
        
        #Create external OSL scripts and nodegroup files, and cache image textures
        nodes = dom.getElementsByTagName("node")
        for node in nodes:
            node_data = node.attributes
            if node_data['type'].value == "TEX_IMAGE" or node_data['type'].value == "TEX_ENVIRONMENT":
                if node_data['image'].value:
                    if 'image' in node_data:
                        original_xml = " image=\"%s\"" % node_data['image'].value
                    else:
                        break
                    if "file://" in node_data['image'].value:
                        if os.path.exists(node_data['image'].value[7:]):
                            image_file = open(node_data['image'].value[7:], mode="r+b")
                            image_data = image_file.read()
                            image_file.close()
                            copied_image = open(self.filepath[:-len(self.filename)] + node_data['image'].value.split(os.sep)[-1], mode="w+b")
                            copied_image.write(image_data)
                            copied_image.close()
                            image_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['image'].value.split(os.sep)[-1])
                        else:
                            image_location = ""
                    elif "http://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot save image texture hosted at %s." % node_data['image'].value)
                        image_location = ""
                    else:
                        ext = "." + node_data['image'].value.split(".")[-1]
                        image_name = node_data['image'].value[:-4]
                        
                        if ext.lower() != ".jpg" and ext.lower() != ".png":
                            node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                            else:
                                image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                        else:
                            node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                            image_filepath = ""
                        image_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['image'].value)
                        
                        if image_filepath:
                            print(image_filepath)
                            image_file = open(image_filepath, mode="r+b")
                            image_data = image_file.read()
                            image_file.close()
                            saved_image = open(self.filepath[:-len(self.filename)] + node_data['image'].value, mode="w+b")
                            saved_image.write(image_data)
                            saved_image.close()
                    image_location = "file://" + self.filepath[:-len(self.filename)] + node_data['image'].value
                    updated_xml = original_xml.replace(node_data['image'].value, image_location)
                    material_file_contents = material_file_contents.replace(original_xml, updated_xml)
            elif node_data['type'].value == "SCRIPT":
                if node_data['script'].value:
                    original_xml = " script=\"%s\"" % node_data['script'].value
                    
                    if "file://" in node_data['script'].value:
                        if os.path.exists(node_data['script'].value[7:]):
                            script_file = open(node_data['script'].value[7:], mode="r+b")
                            script_data = script_file.read()
                            script_file.close()
                            copied_script = open(self.filepath[:-len(self.filename)] + node_data['script'].value.split(os.sep)[-1], mode="w+b")
                            copied_script.write(script_data)
                            copied_script.close()
                            script_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['script'].value.split(os.sep)[-1])
                        else:
                            script_location = ""
                    elif "http://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot save OSL script hosted at %s." % node_data['script'].value)
                        script_location = ""
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache OSL script
                            if library == "composite":
                                script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                            else:
                                script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            script_filepath = ""
                        
                        if script_filepath:
                            print(script_filepath)
                            script_file = open(script_filepath, mode="r+b")
                            script_data = script_file.read()
                            script_file.close()
                            saved_script = open(self.filepath[:-len(self.filename)] + node_data['script'].value, mode="w+b")
                            saved_script.write(script_data)
                            saved_script.close()
                    script_location = "file://" + self.filepath[:-len(self.filename)] + node_data['script'].value
                    updated_xml = original_xml.replace(node_data['script'].value, script_location)
                    material_file_contents = material_file_contents.replace(original_xml, updated_xml)
            elif node_data['type'].value == "GROUP":
                if node_data['group'].value:
                    original_xml = " group=\"%s\"" % node_data['group'].value
                    
                    if "file://" in node_data['group'].value:
                        if os.path.exists(node_data['group'].value[7:]):
                            group_file = open(node_data['group'].value[7:], mode="r+b")
                            group_data = group_file.read()
                            group_file.close()
                            copied_group = open(self.filepath[:-len(self.filename)] + node_data['group'].value.split(os.sep)[-1], mode="w+b")
                            copied_group.write(group_data)
                            copied_group.close()
                            group_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['group'].value.split(os.sep)[-1])
                        else:
                            group_location = ""
                    elif "http://" in node_data['group'].value:
                        self.report({'ERROR'}, "Cannot save nodegroup hosted at %s." % node_data['group'].value)
                        group_location = ""
                    else:
                        group_name = node_data['group'].value[:-4]
                        
                        if ("." + node_data['group'].value.split(".")[-1]).lower() != ".bcg":
                            node_message = ['ERROR', "The nodegroup file referenced by this group node is not .bcg; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")):
                            group_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")):
                            group_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "groups", group_name + ".bcg")):
                            group_filepath = os.path.join(matlibpath, "bundled", "cycles", "groups", group_name + ".bcg")
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/groups/" + group_name + ".bcg")
                            response = connection.getresponse().read()
                            
                            #Cache nodegroup
                            if library == "composite":
                                group_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")
                                group_file = open(group_filepath, mode="w+b")
                                group_file.write(response)
                                group_file.close()
                            else:
                                group_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")
                                group_file = open(group_filepath, mode="w+b")
                                group_file.write(response)
                                group_file.close()
                        else:
                            node_message = ['ERROR', "The nodegroup file, \"%s\", is not cached; cannot download in offline mode." % (group_name + ".bcg")]
                            group_filepath = ""
                        
                        if group_filepath:
                            print(group_filepath)
                            group_file = open(group_filepath, mode="r+b")
                            group_data = group_file.read()
                            group_file.close()
                            saved_group = open(self.filepath[:-len(self.filename)] + node_data['group'].value, mode="w+b")
                            saved_group.write(group_data)
                            saved_group.close()
                    group_location = "file://" + self.filepath[:-len(self.filename)] + node_data['group'].value
                    updated_xml = original_xml.replace(node_data['group'].value, group_location)
                    material_file_contents = material_file_contents.replace(original_xml, updated_xml)
        
        bcm_file = open(self.filepath, mode="w", encoding="UTF-8")
        bcm_file.write(material_file_contents)
        bcm_file.close()
        
        self.report({'INFO'}, "Material saved.")
        current_material_cached = True
        
        return {'FINISHED'}

class AddLibraryGroup(bpy.types.Operator):
    '''Add nodegroup to scene'''
    bl_idname = "material.libraryaddgroup"
    bl_label = "add nodegroup to scene"
    group_name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    open_location = bpy.props.StringProperty()
    text_block = bpy.props.StringProperty()
    
    def execute(self, context):
        global group_file_contents
        global library
        global node_message
        global current_material_cached
        
        findLibrary()
        
        if self.open_location == "" and self.text_block == "":
            if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename + ".bcg")):
                bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename + ".bcg"), mode="r", encoding="UTF-8")
                group_file_contents = ""
                group_file_contents = bcg_file.read()
                bcg_file.close()
            elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename + ".bcg")):
                bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename + ".bcg"), mode="r", encoding="UTF-8")
                group_file_contents = ""
                group_file_contents = bcg_file.read()
                bcg_file.close()
            elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "groups", self.filename + ".bcg")):
                bcg_file = open(os.path.join(matlibpath, "bundled", "cycles", "groups", self.filename + ".bcg"), mode="r", encoding="UTF-8")
                group_file_contents = bcg_file.read()
                bcg_file.close()
            elif working_mode == "online":
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/groups/" + self.filename + ".bcg")
                response = connection.getresponse().read()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in str(response)[2:40]:
                    self.report({'ERROR'}, "Nodegroup file is invalid.")
                    self.filename = ""
                    return {'CANCELLED'}
                
                #Cache nodegroup
                if library == "composite":
                    bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename + ".bcg"), mode="w+b")
                    bcg_file.write(response)
                    bcg_file.close()
                else:
                    bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename + ".bcg"), mode="w+b")
                    bcg_file.write(response)
                    bcg_file.close()
                
                group_file_contents = str(response)
            else:
                self.report({'ERROR'}, "Nodegroup is not cached; cannot download in offline mode!")
                return {'CANCELLED'}
            print (group_file_contents)
            group_name = self.group_name
        elif self.open_location is not "":
            if self.open_location[-4:] == ".bcg":
                bcg_file = open(self.open_location, mode="r", encoding="UTF-8")
                group_file_contents = bcg_file.read()
                bcg_file.close()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in group_file_contents:
                    self.open_location = ""
                    self.report({'ERROR'}, "Nodegroup file is invalid.")
                    return {'CANCELLED'}
                group_name = ""
                for word in self.open_location.split(os.sep)[-1][:-4].split("_"):
                    if group_name is not "":
                        group_name += " "
                    group_name += word.capitalize()
            else:
                self.report({'ERROR'}, "Not a .bcg file.")
                self.open_location = ""
                return {'CANCELLED'}
        else:
            if self.text_block in bpy.data.texts:
                #Read from a text datablock
                group_file_contents = bpy.data.texts[self.text_block].as_string()
            else:
                self.report({'ERROR'}, "Requested text block does not exist.")
                self.text_block = ""
                return {'CANCELLED'}
                
            #Check file for validitity
            if '<?xml version="1.0" encoding="UTF-8"?>' not in group_file_contents[0:38]:
                self.report({'ERROR'}, "Nodegroup data is invalid.")
                self.text_block = ""
                return {'CANCELLED'}
            group_name = ""
            
            separator = ""
            if context.scene.mat_lib_bcg_name is "":
                separator = ""
                if "_" in self.text_block:
                    separator = "_"
                elif "-" in self.text_block:
                    separator = "-"
                elif " " in self.text_block:
                    separator = " "
                    
                if separator is not "":
                    for word in self.text_block.split(separator):
                        if group_name is not "":
                            group_name += " "
                        group_name += word.capitalize()
                else:
                    group_name = self.text_block
            else:
                group_name = context.scene.mat_lib_bcg_name
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in group_file_contents[0:40]:
            group_file_contents = group_file_contents[group_file_contents.index("<group"):(group_file_contents.rindex("</group>") + 8)]
        else:
            self.group_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Nodegroup file is invalid.")
            print(group_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(group_file_contents)
        
        #Create node group
        group = dom.getElementsByTagName("group")[0]
        group_text = group.toxml()
        addNodeGroup(group_name, group_text)
        
        self.group_name = ""
        self.filename = ""
        self.open_location = ""
        self.text_block = ""
        self.report({'INFO'}, "Nodegroup added.")
        current_material_cached = True
        
        return {'FINISHED'}

class InsertLibraryGroup(bpy.types.Operator):
    '''Insert nodegroup into active material'''
    bl_idname = "material.libraryinsertgroup"
    bl_label = "insert nodegroup into active material"
    group_name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    open_location = bpy.props.StringProperty()
    text_block = bpy.props.StringProperty()
    
    def execute(self, context):
        global group_file_contents
        global library
        global node_message
        global current_material_cached
        
        findLibrary()
        
        if not context.active_object:
            self.group_name = ""
            self.filename = ""
            self.open_location = ""
            self.text_block = ""
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        if not context.active_object.active_material:
            self.group_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "No material selected!")
            return {'CANCELLED'}
            
        if not context.active_object.active_material.use_nodes:
            self.group_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Active material does not use nodes!")
            return {'CANCELLED'}
        
        if self.open_location == "" and self.text_block == "":
            if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename + ".bcg")):
                bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename + ".bcg"), mode="r", encoding="UTF-8")
                group_file_contents = ""
                group_file_contents = bcg_file.read()
                bcg_file.close()
            elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename + ".bcg")):
                bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename + ".bcg"), mode="r", encoding="UTF-8")
                group_file_contents = ""
                group_file_contents = bcg_file.read()
                bcg_file.close()
            elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "groups", self.filename + ".bcg")):
                bcg_file = open(os.path.join(matlibpath, "bundled", "cycles", "groups", self.filename + ".bcg"), mode="r", encoding="UTF-8")
                group_file_contents = bcg_file.read()
                bcg_file.close()
            elif working_mode == "online":
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/groups/" + self.filename + ".bcg")
                response = connection.getresponse().read()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in str(response)[2:40]:
                    self.report({'ERROR'}, "Nodegroup file is invalid.")
                    self.filename = ""
                    return {'CANCELLED'}
                
                #Cache nodegroup
                if library == "composite":
                    bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename + ".bcg"), mode="w+b")
                    bcg_file.write(response)
                    bcg_file.close()
                else:
                    bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename + ".bcg"), mode="w+b")
                    bcg_file.write(response)
                    bcg_file.close()
                
                group_file_contents = str(response)
            else:
                self.report({'ERROR'}, "Nodegroup is not cached; cannot download in offline mode!")
                return {'CANCELLED'}
            print (group_file_contents)
            group_name = self.group_name
        elif self.open_location is not "":
            if self.open_location[-4:] == ".bcg":
                bcg_file = open(self.open_location, mode="r", encoding="UTF-8")
                group_file_contents = bcg_file.read()
                bcg_file.close()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in group_file_contents:
                    self.open_location = ""
                    self.report({'ERROR'}, "Nodegroup file is invalid.")
                    return {'CANCELLED'}
                group_name = ""
                for word in self.open_location.split(os.sep)[-1][:-4].split("_"):
                    if group_name is not "":
                        group_name += " "
                    group_name += word.capitalize()
            else:
                self.report({'ERROR'}, "Not a .bcg file.")
                self.open_location = ""
                return {'CANCELLED'}
        else:
            if self.text_block in bpy.data.texts:
                #Read from a text datablock
                group_file_contents = bpy.data.texts[self.text_block].as_string()
            else:
                self.report({'ERROR'}, "Requested text block does not exist.")
                self.text_block = ""
                return {'CANCELLED'}
                
            #Check file for validitity
            if '<?xml version="1.0" encoding="UTF-8"?>' not in group_file_contents[0:38]:
                self.report({'ERROR'}, "Nodegroup data is invalid.")
                self.text_block = ""
                return {'CANCELLED'}
            group_name = ""
            
            separator = ""
            if context.scene.mat_lib_bcg_name is "":
                separator = ""
                if "_" in self.text_block:
                    separator = "_"
                elif "-" in self.text_block:
                    separator = "-"
                elif " " in self.text_block:
                    separator = " "
                    
                if separator is not "":
                    for word in self.text_block.split(separator):
                        if group_name is not "":
                            group_name += " "
                        group_name += word.capitalize()
                else:
                    group_name = self.text_block
            else:
                group_name = context.scene.mat_lib_bcg_name
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in group_file_contents[0:40]:
            group_file_contents = group_file_contents[group_file_contents.index("<group"):(group_file_contents.rindex("</group>") + 8)]
        else:
            self.group_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Nodegroup file is invalid.")
            print(group_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(group_file_contents)
        
        #Create node group
        group = dom.getElementsByTagName("group")[0]
        group_text = group.toxml()
        new_nodegroup = addNodeGroup(group_name, group_text)
        
        #Insert the nodegroup as a group node into the active material
        context.active_object.active_material.node_tree.nodes.new(node_types['SHADER']['GROUP'], new_nodegroup)
        
        self.group_name = ""
        self.filename = ""
        self.open_location = ""
        self.text_block = ""
        self.report({'INFO'}, "Nodegroup inserted.")
        current_material_cached = True
        
        return {'FINISHED'}

class CacheLibraryGroup(bpy.types.Operator):
    '''Cache nodegroup to disk'''
    bl_idname = "material.librarycachegroup"
    bl_label = "cache nodegroup to disk"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global group_file_contents
        global current_material_cached
        
        findLibrary()
        
        if working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/groups/" + self.filename + ".bcg")
            response = connection.getresponse().read()
        else:
            self.report({'ERROR'}, "Cannot cache nodegroup in offline mode.")
            return {'CANCELLED'}
        
        group_file_contents = str(response)
        if '<?xml version="1.0" encoding="UTF-8"?>' in group_file_contents[2:40]:
            group_file_contents = group_file_contents[group_file_contents.index("<group"):(group_file_contents.rindex("</group>") + 8)]
        else:
            self.report({'ERROR'}, "Invalid nodegroup file.")
            print(group_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(group_file_contents)
        
        #Create external OSL scripts and cache image textures
        nodes = dom.getElementsByTagName("groupnode")
        for node in nodes:
            node_data = node.attributes
            if node_data['type'].value == "TEX_IMAGE" or node_data['type'].value == "TEX_ENVIRONMENT":
                if node_data['image'].value and '.' in node_data['image'].value:
                    if "file://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot cache image texture located at %s." % node_data['image'].value)
                    elif "http://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot cache image texture hosted at %s." % node_data['image'].value)
                    else:
                        ext = "." + node_data['image'].value.split(".")[-1]
                        image_name = node_data['image'].value[:-4]
                        
                        if ext.lower() != ".jpg" and ext.lower() != ".png":
                            node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                            else:
                                image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
            elif node_data['type'].value == "SCRIPT":
                if node_data['script'].value and '.' in node_data['script'].value:
                    if "file://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot cache OSL script located at %s." % node_data['script'].value)
                    elif "http://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot cache OSL script hosted at %s." % node_data['script'].value)
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                            else:
                                script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
        
        if library == "composite":
            bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", category_filename, self.filename + ".bcg"), mode="w+b")
            bcg_file.write(response)
            bcg_file.close()
        elif library != "bundled":
            bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", category_filename, self.filename + ".bcg"), mode="w+b")
            bcg_file.write(response)
            bcg_file.close()
        else:
            self.report({'ERROR'}, "Cannot cache nodegroups from this library.")
            return {'CANCELLED'}
            
        current_material_cached = True
        self.report({'INFO'}, "Nodegroup cached.")
        return {'FINISHED'}

class SaveLibraryGroup(bpy.types.Operator, ExportHelper):
    '''Save nodegroup to disk'''
    bl_idname = "material.librarysavegroup"
    bl_label = "Save nodegroup to disk"
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    
    #ExportHelper uses this
    filename_ext = ".bcg"

    filter_glob = bpy.props.StringProperty(
            default="*.bcg",
            options={'HIDDEN'},
            )
    
    def execute(self, context):
        global group_file_contents
        global save_filename
        global current_material_cached
        
        findLibrary()
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename)):
            bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename), mode="r+b")
            response = bcg_file.read()
            bcg_file.close()
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename)):
            bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename), mode="r+b")
            response = bcg_file.read()
            bcg_file.close()
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "groups", self.filename)):
            bcg_file = open(os.path.join(matlibpath, "bundled", "cycles", "groups", self.filename), mode="r+b")
            response = bcg_file.read()
            bcg_file.close()
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/groups/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache nodegroup
            if library == "composite":
                bcg_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", self.filename), mode="w+b")
                bcg_file.write(response)
                bcg_file.close()
            else:
                bcg_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", self.filename), mode="w+b")
                bcg_file.write(response)
                bcg_file.close()
        else:
            self.report({'ERROR'}, "Nodegroup is not cached; cannot download in offline mode.")
            return {'FINISHED'}
        
        group_file_contents = str(response)
        
        bcg_file = open(self.filepath, mode="w+b")
        bcg_file.write(response)
        bcg_file.close()
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in group_file_contents[0:40]:
            group_file_contents = group_file_contents[group_file_contents.index("<group"):(group_file_contents.rindex("</group>") + 8)]
        else:
            self.report({'ERROR'}, "Invalid nodegroup file.")
            print(group_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(group_file_contents)
        
        bcg_file = open(self.filepath, mode="r", encoding="UTF-8")
        group_file_contents = bcg_file.read()
        bcg_file.close()
        
        #Create external OSL scripts and cache image textures
        nodes = dom.getElementsByTagName("groupnode")
        for node in nodes:
            node_data = node.attributes
            if node_data['type'].value == "TEX_IMAGE" or node_data['type'].value == "TEX_ENVIRONMENT":
                if node_data['image'].value:
                    if 'image' in node_data:
                        original_xml = " image=\"%s\"" % node_data['image'].value
                    else:
                        break
                    if "file://" in node_data['image'].value:
                        if os.path.exists(node_data['image'].value[7:]):
                            image_file = open(node_data['image'].value[7:], mode="r+b")
                            image_data = image_file.read()
                            image_file.close()
                            copied_image = open(self.filepath[:-len(self.filename)] + node_data['image'].value.split(os.sep)[-1], mode="w+b")
                            copied_image.write(image_data)
                            copied_image.close()
                            image_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['image'].value.split(os.sep)[-1])
                        else:
                            image_location = ""
                    elif "http://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot save image texture hosted at %s." % node_data['image'].value)
                        image_location = ""
                    else:
                        ext = "." + node_data['image'].value.split(".")[-1]
                        image_name = node_data['image'].value[:-4]
                        
                        if ext.lower() != ".jpg" and ext.lower() != ".png":
                            node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                            else:
                                image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                        else:
                            node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                            image_filepath = ""
                        image_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['image'].value)
                        
                        if image_filepath:
                            print(image_filepath)
                            image_file = open(image_filepath, mode="r+b")
                            image_data = image_file.read()
                            image_file.close()
                            saved_image = open(self.filepath[:-len(self.filename)] + node_data['image'].value, mode="w+b")
                            saved_image.write(image_data)
                            saved_image.close()
                    image_location = "file://" + self.filepath[:-len(self.filename)] + node_data['image'].value
                    updated_xml = original_xml.replace(node_data['image'].value, image_location)
                    group_file_contents = group_file_contents.replace(original_xml, updated_xml)
            elif node_data['type'].value == "SCRIPT":
                if node_data['script'].value:
                    original_xml = " script=\"%s\"" % node_data['script'].value
                    
                    if "file://" in node_data['script'].value:
                        if os.path.exists(node_data['script'].value[7:]):
                            script_file = open(node_data['script'].value[7:], mode="r+b")
                            script_data = script_file.read()
                            script_file.close()
                            copied_script = open(self.filepath[:-len(self.filename)] + node_data['script'].value.split(os.sep)[-1], mode="w+b")
                            copied_script.write(script_data)
                            copied_script.close()
                            script_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['script'].value.split(os.sep)[-1])
                        else:
                            script_location = ""
                    elif "http://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot save OSL script hosted at %s." % node_data['script'].value)
                        script_location = ""
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            break
                            
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache OSL script
                            if library == "composite":
                                script_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                            else:
                                script_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            script_filepath = ""
                        
                        if script_filepath:
                            print(script_filepath)
                            script_file = open(script_filepath, mode="r+b")
                            script_data = script_file.read()
                            script_file.close()
                            saved_script = open(self.filepath[:-len(self.filename)] + node_data['script'].value, mode="w+b")
                            saved_script.write(script_data)
                            saved_script.close()
                    script_location = "file://" + self.filepath[:-len(self.filename)] + node_data['script'].value
                    updated_xml = original_xml.replace(node_data['script'].value, script_location)
                    group_file_contents = group_file_contents.replace(original_xml, updated_xml)
        
        bcg_file = open(self.filepath, mode="w", encoding="UTF-8")
        bcg_file.write(group_file_contents)
        bcg_file.close()
        
        self.report({'INFO'}, "Nodegroup saved.")
        current_material_cached = True
        
        return {'FINISHED'}

class AddLibraryImage(bpy.types.Operator):
    '''Add image to scene'''
    bl_idname = "material.libraryaddimage"
    bl_label = "add image to scene"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global library
        global current_material_cached
        
        findLibrary()
        
        if self.filename[-4:].lower() != ".jpg" and self.filename[-4:].lower() != ".png":
            self.report({'ERROR'}, "The requested image file is not .jpg or .png; not downloading.")
            return {'CANCELLED'}
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)):
            image_path = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)):
            image_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", self.filename)):
            image_path = os.path.join(matlibpath, "bundled", "cycles", "textures", self.filename)
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/textures/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache image
            if library == "composite":
                img_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename), mode="w+b")
                img_file.write(response)
                img_file.close()
                image_path = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)
            else:
                img_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename), mode="w+b")
                img_file.write(response)
                img_file.close()
                image_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)
        else:
            self.report({'ERROR'}, "Image is not cached; cannot download in offline mode!")
            return {'CANCELLED'}
        
        bpy.ops.image.open(filepath=image_path)
        
        self.report({'INFO'}, "Image added.")
        current_material_cached = True
        
        return {'FINISHED'}

class InsertLibraryImage(bpy.types.Operator):
    '''Insert image into active material'''
    bl_idname = "material.libraryinsertimage"
    bl_label = "insert image into active material"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global library
        global current_material_cached
        
        findLibrary()
        
        if not context.active_object:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        if not context.active_object.active_material:
            self.report({'ERROR'}, "No material selected!")
            return {'CANCELLED'}
            
        if not context.active_object.active_material.use_nodes:
            self.report({'ERROR'}, "Active material does not use nodes!")
            return {'CANCELLED'}
        
        if self.filename[-4:].lower() != ".jpg" and self.filename[-4:].lower() != ".png":
            self.report({'ERROR'}, "The requested image file is not .jpg or .png; not downloading.")
            return {'CANCELLED'}
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)):
            image_path = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)):
            image_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", self.filename)):
            image_path = os.path.join(matlibpath, "bundled", "cycles", "textures", self.filename)
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/textures/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache image
            if library == "composite":
                img_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename), mode="w+b")
                img_file.write(response)
                img_file.close()
                image_path = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)
            else:
                img_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename), mode="w+b")
                img_file.write(response)
                img_file.close()
                image_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)
        else:
            self.report({'ERROR'}, "Image is not cached; cannot download in offline mode!")
            return {'CANCELLED'}
        
        new_image = bpy.ops.image.open(filepath=image_path)
        
        new_node = context.active_object.active_material.node_tree.nodes.new(node_types['SHADER']['TEX_IMAGE'])
        image_datablock = bpy.data.images.new(name=self.filename, width=4, height=4)
        image_datablock.source = 'FILE'
        image_datablock.filepath = image_path
        new_node.image = image_datablock
        
        self.report({'INFO'}, "Image texture node inserted.")
        current_material_cached = True
        
        return {'FINISHED'}

class CacheLibraryImage(bpy.types.Operator):
    '''Cache image to disk'''
    bl_idname = "material.librarycacheimage"
    bl_label = "cache image to disk"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global current_material_cached
        
        findLibrary()
        
        if working_mode == "online":
            if self.filename[-4:].lower() != ".jpg" and self.filename[-4:].lower() != ".png":
                self.report({'ERROR'}, "The requested image file is not .jpg or .png; not downloading.")
                return {'CANCELLED'}
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/textures/" + self.filename)
            response = connection.getresponse().read()
        else:
            self.report({'ERROR'}, "Cannot cache image in offline mode.")
            return {'CANCELLED'}
        
        if library == "composite":
            bcm_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename), mode="w+b")
            bcm_file.write(response)
            bcm_file.close()
        elif library != "bundled":
            bcm_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename), mode="w+b")
            bcm_file.write(response)
            bcm_file.close()
        else:
            self.report({'ERROR'}, "Cannot cache images from this library.")
            return {'CANCELLED'}
            
        current_material_cached = True
        self.report({'INFO'}, "Image cached.")
        return {'FINISHED'}

class SaveLibraryImage(bpy.types.Operator, ExportHelper):
    '''Save image to disk'''
    bl_idname = "material.librarysaveimage"
    bl_label = "Save image to disk"
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    
    #ExportHelper uses this
    filename_ext = bpy.props.StringProperty(default=".jpg")

    filter_glob = bpy.props.StringProperty(
            default="*.jpg",
            options={'HIDDEN'},
            )
    
    def execute(self, context):
        global save_filename
        global current_material_cached
        
        findLibrary()
        
        if self.filename[-4:].lower() != ".jpg" and self.filename[-4:].lower() != ".png":
            self.report({'ERROR'}, "The requested image file is not .jpg or .png; not downloading.")
            return {'CANCELLED'}
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename)):
            img_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename), mode="r+b")
            response = img_file.read()
            img_file.close()
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename)):
            img_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename), mode="r+b")
            response = img_file.read()
            img_file.close()
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", self.filename)):
            img_file = open(os.path.join(matlibpath, "bundled", "cycles", "textures", self.filename), mode="r+b")
            response = img_file.read()
            img_file.close()
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/textures/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache image
            if library == "composite":
                img_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", self.filename), mode="w+b")
                img_file.write(response)
                img_file.close()
            else:
                img_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", self.filename), mode="w+b")
                img_file.write(response)
                img_file.close()
        else:
            self.report({'ERROR'}, "Image is not cached; cannot download in offline mode.")
            return {'CANCELLED'}
        
        img_file = open(self.filepath, mode="w+b")
        img_file.write(response)
        img_file.close()
        
        self.report({'INFO'}, "Image saved.")
        current_material_cached = True
        
        return {'FINISHED'}

class AddLibraryScript(bpy.types.Operator):
    '''Add OSL script as a text datablock'''
    bl_idname = "material.libraryaddscript"
    bl_label = "add script as a text datablock"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global library
        global current_material_cached
        
        findLibrary()
        
        if self.filename[-4:].lower() != ".osl" and self.filename[-4:].lower() != ".oso":
            self.report({'ERROR'}, "The requested OSL script file is not .osl or .oso; not downloading.")
            return {'CANCELLED'}
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)):
            script_path = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)):
            script_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", self.filename)):
            script_path = os.path.join(matlibpath, "bundled", "cycles", "scripts", self.filename)
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/scripts/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache image
            if library == "composite":
                osl_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename), mode="w+b")
                osl_file.write(response)
                osl_file.close()
                script_path = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)
            else:
                osl_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename), mode="w+b")
                osl_file.write(response)
                osl_file.close()
                script_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)
        else:
            self.report({'ERROR'}, "OSL script is not cached; cannot download in offline mode!")
            return {'CANCELLED'}
        
        script_datablock = bpy.data.texts.new(name=self.filename)
        osl_file = open(script_path, encoding="UTF-8")
        script_text = osl_file.read()
        osl_file.close()
        script_datablock.write(script_text)
        
        self.report({'INFO'}, "OSL script added as a text datablock.")
        current_material_cached = True
        
        return {'FINISHED'}

class InsertLibraryScript(bpy.types.Operator):
    '''Insert OSL script into active material'''
    bl_idname = "material.libraryinsertscript"
    bl_label = "insert script into active material"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global library
        global current_material_cached
        
        findLibrary()
        
        if not context.active_object:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        
        if not context.active_object.active_material:
            self.report({'ERROR'}, "No material selected!")
            return {'CANCELLED'}
            
        if not context.active_object.active_material.use_nodes:
            self.report({'ERROR'}, "Active material does not use nodes!")
            return {'CANCELLED'}
        
        if self.filename[-4:].lower() != ".osl" and self.filename[-4:].lower() != ".oso":
            self.report({'ERROR'}, "The requested OSL script file is not .osl or .oso; not downloading.")
            return {'CANCELLED'}
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)):
            script_path = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)):
            script_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", self.filename)):
            script_path = os.path.join(matlibpath, "bundled", "cycles", "scripts", self.filename)
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/scripts/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache image
            if library == "composite":
                osl_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename), mode="w+b")
                osl_file.write(response)
                osl_file.close()
                script_path = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)
            else:
                osl_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename), mode="w+b")
                osl_file.write(response)
                osl_file.close()
                script_path = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)
        else:
            self.report({'ERROR'}, "Image is not cached; cannot download in offline mode!")
            return {'CANCELLED'}
        
        new_node = context.active_object.active_material.node_tree.nodes.new(node_types['SHADER']['SCRIPT'])
        new_node.mode = 'EXTERNAL'
        new_node.filepath = script_path
        
        self.report({'INFO'}, "OSL script node inserted.")
        current_material_cached = True
        
        return {'FINISHED'}

class CacheLibraryScript(bpy.types.Operator):
    '''Cache OSL script to disk'''
    bl_idname = "material.librarycachescript"
    bl_label = "cache script to disk"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global current_material_cached
        
        findLibrary()
        
        if working_mode == "online":
            if self.filename[-4:].lower() != ".osl" and self.filename[-4:].lower() != ".oso":
                self.report({'ERROR'}, "The requested OSL script file is not .osl or .oso; not downloading.")
                return {'CANCELLED'}
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/scripts/" + self.filename)
            response = connection.getresponse().read()
        else:
            self.report({'ERROR'}, "Cannot cache OSL script in offline mode.")
            return {'CANCELLED'}
        
        if library == "composite":
            osl_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename), mode="w+b")
            osl_file.write(response)
            osl_file.close()
        elif library != "bundled":
            osl_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename), mode="w+b")
            osl_file.write(response)
            osl_file.close()
        else:
            self.report({'ERROR'}, "Cannot cache OSL scripts from this library.")
            return {'CANCELLED'}
            
        current_material_cached = True
        self.report({'INFO'}, "OSL script cached.")
        return {'FINISHED'}

class SaveLibraryScript(bpy.types.Operator, ExportHelper):
    '''Save OSL script to disk'''
    bl_idname = "material.librarysavescript"
    bl_label = "Save script to disk"
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    
    #ExportHelper uses this
    filename_ext = bpy.props.StringProperty(default=".osl")

    filter_glob = bpy.props.StringProperty(
            default="*.osl",
            options={'HIDDEN'},
            )
    
    def execute(self, context):
        global save_filename
        global current_material_cached
        
        findLibrary()
        
        if self.filename[-4:].lower() != ".osl" and self.filename[-4:].lower() != ".oso":
            self.report({'ERROR'}, "The requested OSL script is not .osl or .oso; not downloading.")
            return {'CANCELLED'}
        
        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename)):
            osl_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename), mode="r+b")
            response = osl_file.read()
            osl_file.close()
        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename)):
            osl_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename), mode="r+b")
            response = osl_file.read()
            osl_file.close()
        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", self.filename)):
            osl_file = open(os.path.join(matlibpath, "bundled", "cycles", "scripts", self.filename), mode="r+b")
            response = osl_file.read()
            osl_file.close()
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/scripts/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache script
            if library == "composite":
                osl_file = open(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", self.filename), mode="w+b")
                osl_file.write(response)
                osl_file.close()
            else:
                osl_file = open(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", self.filename), mode="w+b")
                osl_file.write(response)
                osl_file.close()
        else:
            self.report({'ERROR'}, "Script is not cached; cannot download in offline mode.")
            return {'CANCELLED'}
        
        osl_file = open(self.filepath, mode="w+b")
        osl_file.write(response)
        osl_file.close()
        
        self.report({'INFO'}, "Script saved.")
        current_material_cached = True
        
        return {'FINISHED'}

def createLinks(links, node_tree):
    for dom_link in links:
        input_index = int(dom_link.attributes['input'].value)
        output_index = int(dom_link.attributes['output'].value)
        if dom_link.attributes['to'].value == 'o':
            input = node_tree.outputs[input_index]
        else:
            input = node_tree.nodes[int(dom_link.attributes['to'].value)].inputs[input_index]
        
        if dom_link.attributes['from'].value == 'i':
            output = node_tree.inputs[output_index]
        else:
            output = node_tree.nodes[int(dom_link.attributes['from'].value)].outputs[output_index]
        
        node_tree.links.new(input, output)

class curvePoint:
    def __init__(self, type, loc_x, loc_y):
        self.type = type
        self.loc_x = loc_x
        self.loc_y = loc_y

class mappingCurve:
    def __init__(self, extend, points):
        self.extend = extend
        self.points = points

def addNodeGroup(name, group_text):
    global group_curves
    global group_scripts
    
    group = bpy.data.node_groups.new(name, 'SHADER')
    
    group_text = group_text[group_text.index("<group"):group_text.rindex("</group>") + 8]
    gdom = xml.dom.minidom.parseString(group_text)
    
    #Prepare curve data
    curves = gdom.getElementsByTagName("groupcurve")
    group_curves = []
    for curve in curves:
        curve_points = []
        cdom = xml.dom.minidom.parseString(curve.toxml())
        points = cdom.getElementsByTagName("point")
        for point in points:
            loc_x = float(point.attributes['loc'].value.replace(" ", "").split(",")[0])
            loc_y = float(point.attributes['loc'].value.replace(" ", "").split(",")[1])
            curve_points.append(curvePoint(point.attributes['type'].value, loc_x, loc_y))
        group_curves.append(mappingCurve(curve.attributes['extend'].value, curve_points))
    
    #Create internal OSL scripts
    scripts = gdom.getElementsByTagName("groupscript")
    group_scripts = []
    for s in scripts:
        osl_datablock = bpy.data.texts.new(name=s.attributes['name'].value)
        osl_text = s.toxml()[s.toxml().index(">"):s.toxml().rindex("<")]
        osl_text = osl_text[1:].replace("<br/>","\n").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&amp;", "&")
        osl_datablock.write(osl_text)
        group_scripts.append(osl_datablock)
    
    nodes = gdom.getElementsByTagName("groupnode")
    addNodes(nodes, group, True)
    
    inputs = gdom.getElementsByTagName("groupinput")
    for input in inputs:
        input_data = input.attributes
        input_type = input_data['type'].value
        new_input = group.inputs.new(input_data['name'].value, input_data['type'].value)
        if 'value' in input_data:
            input_value = input_data['value'].value
            if input_type == 'RGBA':
                new_input.default_value = color(input_value)
            elif input_type == 'VECTOR':
                new_input.default_value = vector(input_value)
            elif input_type == 'VALUE':
                new_input.default_value = float(input_value)
            elif input_type == 'INT':
                new_input.default_value = int(input_value)
            elif input_type == 'BOOL':
                new_input.default_value = boolean(input_value)
            elif output_type != 'SHADER':
                new_input.default_value = str(input_value)
    
    outputs = gdom.getElementsByTagName("groupoutput")
    for output in outputs:
        output_data = output.attributes
        output_type = output_data['type'].value
        new_output = group.outputs.new(output_data['name'].value, output_data['type'].value)
        if 'value' in output_data:
            output_value = output_data['value'].value
            if output_type == 'RGBA':
                new_output.default_value = color(output_value)
            elif output_type == 'VECTOR':
                new_output.default_value = vector(output_value)
            elif output_type == 'VALUE':
                new_output.default_value = float(output_value)
            elif output_type == 'INT':
                new_output.default_value = int(output_value)
            elif output_type == 'BOOL':
                new_output.default_value = boolean(output_value)
            elif output_type != 'SHADER':
                new_output.default_value = str(output_value)
    
    links = gdom.getElementsByTagName("grouplink")
    createLinks(links, group)
    
    return group

def addNodes(nodes, node_tree, group_mode = False):
    global node_message
    global osl_scripts
    global node_groups
    
    for dom_node in nodes:
        node_type = dom_node.attributes['type'].value
        loc = dom_node.attributes['loc'].value
        node_location = [int(loc[:loc.index(",")]), int(loc[(loc.index(",") + 1):])]
        node_data = dom_node.attributes
        
        #Below here checks the type of the node and adds the correct type
        
        #INPUT TYPES
        #This is totally crafty, but some of these nodes actually
        # store their values as their output's default value!
        if node_type == "ATTRIBUTE":
            print ("ATTRIBUTE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.attribute_name = node_data['attribute'].value
        
        elif node_type == "CAMERA":
            print ("CAMERA")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "FRESNEL":
            print ("FRESNEL")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['IOR'].default_value = float(node_data['ior'].value)
                
        elif node_type == "LAYER_WEIGHT":
            print ("LAYER_WEIGHT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Blend'].default_value = float(node_data['blend'].value)
                
        elif node_type == "LIGHT_PATH":
            print ("LIGHT_PATH")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "NEW_GEOMETRY":
            print ("NEW_GEOMETRY")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "HAIR_INFO":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.66:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            print ("HAIR_INFO")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "OBJECT_INFO":
            print ("OBJECT_INFO")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "PARTICLE_INFO":
            print ("PARTICLE_INFO")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "RGB":
            print ("RGB")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.outputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "TANGENT":
            print ("TANGENT")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.direction_type = node_data['direction'].value
            node.axis = node_data['axis'].value
        
        elif node_type == "TEX_COORD":
            print ("TEX_COORD")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.64 and "dupli" in node_data:
                node.from_dupli = boolean(node_data['dupli'].value)
        
        elif node_type == "VALUE":
            print ("VALUE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.outputs['Value'].default_value = float(node_data['value'].value)
            
            #OUTPUT TYPES
        elif node_type == "OUTPUT_LAMP":
            print ("OUTPUT_LAMP")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "OUTPUT_MATERIAL":
            print ("OUTPUT_MATERIAL")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "OUTPUT_WORLD":
            print ("OUTPUT_WORLD")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
            #SHADER TYPES
        elif node_type == "ADD_SHADER":
            print ("ADD_SHADER")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            
        elif node_type == "AMBIENT_OCCLUSION":
            print ("AMBIENT_OCCLUSION")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "BACKGROUND":
            print ("BACKGROUND")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
            
        elif node_type == "BSDF_ANISOTROPIC":
            print ("BSDF_ANISOTROPIC")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
            node.inputs['Anisotropy'].default_value = float(node_data['anisotropy'].value)
            node.inputs['Rotation'].default_value = float(node_data['rotation'].value)
            
        elif node_type == "BSDF_DIFFUSE":
            print ("BSDF_DIFFUSE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
        
        elif node_type == "BSDF_GLASS":
            print ("BSDF_GLASS")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.distribution = node_data['distribution'].value
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
            node.inputs['IOR'].default_value = float(node_data['ior'].value)
            
        elif node_type == "BSDF_GLOSSY":
            print ("BSDF_GLOSSY")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.distribution = node_data['distribution'].value
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
        
        elif node_type == "BSDF_REFRACTION":
            print ("BSDF_REFRACTION")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.distribution = node_data['distribution'].value
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
            node.inputs['IOR'].default_value = float(node_data['ior'].value)
        
        elif node_type == "BSDF_TRANSLUCENT":
            print ("BSDF_TRANSLUCENT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "BSDF_TRANSPARENT":
            print ("BSDF_TRANSPARENT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "BSDF_VELVET":
            print ("BSDF_VELVET")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Sigma'].default_value = float(node_data['sigma'].value)
        
        elif node_type == "EMISSION":
            print ("EMISSION")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
        
        elif node_type == "HOLDOUT":
            print ("HOLDOUT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "MIX_SHADER":
            print ("MIX_SHADER")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
        
            #TEXTURE TYPES
        elif node_type == "TEX_BRICK":
            print ("TEX_BRICK")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.offset = float(node_data['offset'].value)
            node.offset_frequency = float(node_data['offset_freq'].value)
            node.squash = float(node_data['squash'].value)
            node.squash_frequency = float(node_data['squash_freq'].value)
            node.inputs['Color1'].default_value = color(node_data['color1'].value)
            node.inputs['Color2'].default_value = color(node_data['color2'].value)
            node.inputs['Mortar'].default_value = color(node_data['mortar'].value)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Mortar Size'].default_value = float(node_data['mortar_size'].value)
            node.inputs['Bias'].default_value = float(node_data['bias'].value)
            node.inputs['Brick Width'].default_value = float(node_data['width'].value)
            node.inputs['Row Height'].default_value = float(node_data['height'].value)
            
        elif node_type == "TEX_CHECKER":
            print ("TEX_CHECKER")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color1'].default_value = color(node_data['color1'].value)
            node.inputs['Color2'].default_value = color(node_data['color2'].value)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            
        elif node_type == "TEX_ENVIRONMENT":
            print ("TEX_ENVIRONMENT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.color_space = node_data['color_space'].value
            node.projection = node_data['projection'].value
            if 'image' in node_data:
                if "file://" in node_data['image'].value:
                    image_filepath = node_data['image'].value[7:]
                    image_name = node_data['image'].value.split(os.sep)[-1]
                    image_datablock = bpy.data.images.new(name=image_name, width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                elif "http://" in node_data['image'].value and bpy.context.scene.mat_lib_images_only_trusted == False:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value.split("/")[-1][:-4]
                    image_host = node_data['image'].value[7:].split("/")[0]
                    image_location = node_data['image'].value[(7 + len(image_host)):]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                    
                    connection = http.client.HTTPConnection(image_host)
                    connection.request("GET", image_location)
                    response = connection.getresponse().read()
                    #Save image texture
                    image_filepath = os.path.join(matlibpath, "my-materials", image_name + ext)
                    image_file = open(image_filepath, mode="w+b")
                    image_file.write(response)
                    image_file.close()
                    image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                else:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value[:-4]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                        
                    if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                    elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                    elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)
                    elif working_mode == "online":
                        connection = http.client.HTTPConnection(mat_lib_host)
                        connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                        response = connection.getresponse().read()
                        
                        #Cache image texture
                        if library == "composite":
                            image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                        else:
                            image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                    else:
                        node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                        image_filepath = ""
                    if image_filepath != "":
                        image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                        image_datablock.source = node_data['source'].value
                        image_datablock.filepath = image_filepath
                        node.image = image_datablock
                        if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                            node.image_user.frame_duration = int(node_data['frame_duration'].value)
                            node.image_user.frame_start = int(node_data['frame_start'].value)
                            node.image_user.frame_offset = int(node_data['frame_offset'].value)
                            node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                            node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
            
        elif node_type == "TEX_GRADIENT":
            print ("TEX_GRADIENT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.gradient_type = node_data['gradient'].value
        
        elif node_type == "TEX_IMAGE":
            print ("TEX_IMAGE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.color_space = node_data['color_space'].value
            if "projection" in node_data:
                node.projection = node_data['projection'].value
            if 'image' in node_data:
                if "file://" in node_data['image'].value:
                    image_filepath = node_data['image'].value[7:]
                    image_name = node_data['image'].value.split(os.sep)[-1]
                    image_datablock = bpy.data.images.new(name=image_name, width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                elif "http://" in node_data['image'].value and bpy.context.scene.mat_lib_images_only_trusted == False:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value.split("/")[-1][:-4]
                    image_host = node_data['image'].value[7:].split("/")[0]
                    image_location = node_data['image'].value[(7 + len(image_host)):]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                    
                    connection = http.client.HTTPConnection(image_host)
                    connection.request("GET", image_location)
                    response = connection.getresponse().read()
                    #Save image texture
                    image_filepath = os.path.join(matlibpath, "my-materials", image_name + ext)
                    image_file = open(image_filepath, mode="w+b")
                    image_file.write(response)
                    image_file.close()
                    image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                else:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value[:-4]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                        
                    if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                    elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                    elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(matlibpath, "bundled", "cycles", "textures", image_name + ext)
                    elif working_mode == "online":
                        connection = http.client.HTTPConnection(mat_lib_host)
                        connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                        response = connection.getresponse().read()
                        
                        #Cache image texture
                        if library == "composite":
                            image_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                        else:
                            image_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                    else:
                        node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                        image_filepath = ""
                    if image_filepath != "":
                        image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                        image_datablock.source = node_data['source'].value
                        image_datablock.filepath = image_filepath
                        node.image = image_datablock
                        if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                            node.image_user.frame_duration = int(node_data['frame_duration'].value)
                            node.image_user.frame_start = int(node_data['frame_start'].value)
                            node.image_user.frame_offset = int(node_data['frame_offset'].value)
                            node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                            node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                
        elif node_type == "TEX_MAGIC":
            print ("TEX_MAGIC")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.turbulence_depth = int(node_data['depth'].value)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Distortion'].default_value = float(node_data['distortion'].value)
        
        elif node_type == "TEX_MUSGRAVE":
            print ("TEX_MUSGRAVE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.musgrave_type = node_data['musgrave'].value
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Detail'].default_value = float(node_data['detail'].value)
            node.inputs['Dimension'].default_value = float(node_data['dimension'].value)
            node.inputs['Lacunarity'].default_value = float(node_data['lacunarity'].value)
            node.inputs['Offset'].default_value = float(node_data['offset'].value)
            node.inputs['Gain'].default_value = float(node_data['gain'].value)
        
        elif node_type == "TEX_NOISE":
            print ("TEX_NOISE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Detail'].default_value = float(node_data['detail'].value)
            node.inputs['Distortion'].default_value = float(node_data['distortion'].value)
                        
        elif node_type == "TEX_SKY":
            print ("TEX_SKY")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.sun_direction = vector(node_data['sun_direction'].value)
            node.turbidity = float(node_data['turbidity'].value)
        
        elif node_type == "TEX_VORONOI":
            print ("TEX_VORONOI")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.coloring = node_data['coloring'].value
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
        
        elif node_type == "TEX_WAVE":
            print ("TEX_WAVE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.wave_type = node_data['wave'].value
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Distortion'].default_value = float(node_data['distortion'].value)
            node.inputs['Detail'].default_value = float(node_data['detail'].value)
            node.inputs['Detail Scale'].default_value = float(node_data['detail_scale'].value)
        
            #COLOR TYPES
        elif node_type == "BRIGHTCONTRAST":
            print ("BRIGHTCONTRAST")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Bright'].default_value = float(node_data['bright'].value)
            node.inputs['Contrast'].default_value = float(node_data['contrast'].value)
            
        elif node_type == "CURVE_RGB":
            print ("CURVE_RGB")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.66:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            if group_mode:
                curve_c = group_curves[int(node_data['curve_c'].value)]
                curve_r = group_curves[int(node_data['curve_r'].value)]
                curve_g = group_curves[int(node_data['curve_g'].value)]
                curve_b = group_curves[int(node_data['curve_b'].value)]
            else:
                curve_c = mapping_curves[int(node_data['curve_c'].value)]
                curve_r = mapping_curves[int(node_data['curve_r'].value)]
                curve_g = mapping_curves[int(node_data['curve_g'].value)]
                curve_b = mapping_curves[int(node_data['curve_b'].value)]
            
            #C Curve
            node.mapping.curves[3].extend = curve_c.extend
            if len(curve_c.points) > 2:
                p = 2
                while p < len(curve_c.points):
                    node.mapping.curves[3].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_c.points):
                node.mapping.curves[3].points[p].location = (curve_c.points[p].loc_x, curve_c.points[p].loc_y)
                node.mapping.curves[3].points[p].handle_type = curve_c.points[p].type
                p += 1
            
            #R Curve
            node.mapping.curves[0].extend = curve_r.extend
            if len(curve_r.points) > 2:
                p = 2
                while p < len(curve_r.points):
                    node.mapping.curves[0].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_r.points):
                node.mapping.curves[0].points[p].location = (curve_r.points[p].loc_x, curve_r.points[p].loc_y)
                node.mapping.curves[0].points[p].handle_type = curve_r.points[p].type
                p += 1
            
            #G Curve
            node.mapping.curves[1].extend = curve_g.extend
            if len(curve_g.points) > 2:
                p = 2
                while p < len(curve_g.points):
                    node.mapping.curves[1].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_g.points):
                node.mapping.curves[1].points[p].location = (curve_g.points[p].loc_x, curve_g.points[p].loc_y)
                node.mapping.curves[1].points[p].handle_type = curve_g.points[p].type
                p += 1
            
            #B Curve
            node.mapping.curves[2].extend = curve_b.extend
            if len(curve_b.points) > 2:
                p = 2
                while p < len(curve_b.points):
                    node.mapping.curves[2].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_b.points):
                node.mapping.curves[2].points[p].location = (curve_b.points[p].loc_x, curve_b.points[p].loc_y)
                node.mapping.curves[2].points[p].handle_type = curve_b.points[p].type
                p += 1
        
        elif node_type == "GAMMA":
            print ("GAMMA")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Gamma'].default_value = float(node_data['gamma'].value)
        
        elif node_type == "HUE_SAT":
            print ("HUE_SAT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Hue'].default_value = float(node_data['hue'].value)
            node.inputs['Saturation'].default_value = float(node_data['saturation'].value)
            node.inputs['Value'].default_value = float(node_data['value'].value)
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            
        elif node_type == "INVERT":
            print ("INVERT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "LIGHT_FALLOFF":
            print ("LIGHT_FALLOFF")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
            node.inputs['Smooth'].default_value = float(node_data['smooth'].value)
        
        elif node_type == "MIX_RGB":
            print ("MIX_RGB")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.blend_type = node_data['blend_type'].value
            if "use_clamp" in node_data:
                node.use_clamp = boolean(node_data['use_clamp'].value)
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color1'].default_value = color(node_data['color1'].value)
            node.inputs['Color2'].default_value = color(node_data['color2'].value)
        
            #VECTOR TYPES
        elif node_type == "BUMP":
            print ("BUMP")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs["Strength"].default_value = float(node_data['strength'].value)
            
        elif node_type == "CURVE_VEC":
            print ("CURVE_VEC")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.66:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Vector'].default_value = vector(node_data['vector'].value)
            if group_mode:
                curve_x = group_curves[int(node_data['curve_x'].value)]
                curve_y = group_curves[int(node_data['curve_y'].value)]
                curve_z = group_curves[int(node_data['curve_z'].value)]
            else:
                curve_x = mapping_curves[int(node_data['curve_x'].value)]
                curve_y = mapping_curves[int(node_data['curve_y'].value)]
                curve_z = mapping_curves[int(node_data['curve_z'].value)]
            
            #X Curve
            node.mapping.curves[0].extend = curve_x.extend
            if len(curve_x.points) > 2:
                p = 2
                while p < len(curve_x.points):
                    node.mapping.curves[0].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_x.points):
                node.mapping.curves[0].points[p].location = (curve_x.points[p].loc_x, curve_x.points[p].loc_y)
                node.mapping.curves[0].points[p].handle_type = curve_x.points[p].type
                p += 1
            
            #Y Curve
            node.mapping.curves[1].extend = curve_y.extend
            if len(curve_y.points) > 2:
                p = 2
                while p < len(curve_y.points):
                    node.mapping.curves[1].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_y.points):
                node.mapping.curves[1].points[p].location = (curve_y.points[p].loc_x, curve_y.points[p].loc_y)
                node.mapping.curves[1].points[p].handle_type = curve_y.points[p].type
                p += 1
            
            #Z Curve
            node.mapping.curves[2].extend = curve_z.extend
            if len(curve_z.points) > 2:
                p = 2
                while p < len(curve_z.points):
                    node.mapping.curves[2].points.new(0.0, 0.0)
                    p += 1
            p = 0
            while p < len(curve_z.points):
                node.mapping.curves[2].points[p].location = (curve_z.points[p].loc_x, curve_z.points[p].loc_y)
                node.mapping.curves[2].points[p].handle_type = curve_z.points[p].type
                p += 1
            
        elif node_type == "MAPPING":
            print ("MAPPING")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.translation = vector(node_data['translation'].value)
            node.rotation = vector(node_data['rotation'].value)
            node.scale = vector(node_data['scale'].value)
            if boolean(node_data['use_min'].value):
                node.use_min = True
                node.min = vector(node_data['min'].value)
            if boolean(node_data['use_max'].value):
                node.use_max = True
                node.max = vector(node_data['max'].value)
            node.inputs['Vector'].default_value = vector(node_data['vector'].value)
        
        elif node_type == "NORMAL":
            print ("NORMAL")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.outputs['Normal'].default_value = vector(node_data['vector_output'].value)
            node.inputs['Normal'].default_value = vector(node_data['vector_input'].value)
            
        elif node_type == "NORMAL_MAP":
            print ("NORMAL_MAP")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.space = node_data['space'].value
            node.uv_map = node_data['uv_map'].value
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            
            #CONVERTOR TYPES
        elif node_type == "COMBRGB":
            print ("COMBRGB")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['R'].default_value = float(node_data['red'].value)
            node.inputs['G'].default_value = float(node_data['green'].value)
            node.inputs['B'].default_value = float(node_data['blue'].value)
        
        elif node_type == "MATH":
            print ("MATH")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.operation = node_data['operation'].value
            if "use_clamp" in node_data:
                node.use_clamp = boolean(node_data['use_clamp'].value)
            node.inputs[0].default_value = float(node_data['value1'].value)
            node.inputs[1].default_value = float(node_data['value2'].value)
        
        elif node_type == "RGBTOBW":
            print ("RGBTOBW")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "SEPRGB":
            print ("SEPRGB")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.inputs['Image'].default_value = color(node_data['image'].value)
        
        elif node_type == "VALTORGB":
            print ("VALTORGB")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.color_ramp.interpolation = node_data['interpolation'].value
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            
            #Delete the first stop which comes with the ramp by default
            node.color_ramp.elements.remove(node.color_ramp.elements[0])
            
            # The first stop will be "stop1", so set i to 1
            i = 1
            while i <= int(node_data['stops'].value):
                #Each color stop element is formatted like this:
                #            stop1="0.35|rgba(1, 0.5, 0.8, 0.5)"
                #The "|" separates the stop's position and color.
                element_data = node_data[("stop" + str(i))].value.split('|')
                if i == 1:
                    element = node.color_ramp.elements[0]
                    element.position = float(element_data[0])
                else:
                    element = node.color_ramp.elements.new(float(element_data[0]))
                element.color = color(element_data[1])
                i = i + 1
            
        elif node_type == "VECT_MATH":
            print ("VECT_MATH")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.operation = node_data['operation'].value
            node.inputs[0].default_value = vector(node_data['vector1'].value)
            node.inputs[1].default_value = vector(node_data['vector2'].value)
            
            #MISCELLANEOUS NODE TYPES
        elif node_type == "FRAME":
            #Don't attempt to add frame nodes in builds previous
            #to 2.65, as Blender's nodes.new() operator was
            #unable to add FRAME nodes. Was fixed with r51926.
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) >= 2.65:
                print("FRAME")
                node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "REROUTE":
            print ("REROUTE")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
        
        elif node_type == "SCRIPT":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains an OSL script node.
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly."""]
                return
            print ("SCRIPT")
            node = node_tree.nodes.new(node_types['SHADER'][node_type])
            node.mode = node_data['mode'].value
            if node_data['mode'].value == 'EXTERNAL':
                if 'script' in node_data:
                    if "file://" in node_data['script'].value:
                        node.filepath = node_data['script'].value[7:]
                    elif "http://" in node_data['script'].value and bpy.context.scene.mat_lib_osl_only_trusted == False:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value.split("/")[-1][:-4]
                        osl_host = node_data['script'].value[7:].split("/")[0]
                        script_location = node_data['script'].value[(7 + len(osl_host)):]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            return
                        
                        connection = http.client.HTTPConnection(osl_host)
                        connection.request("GET", script_location + script_name + ext)
                        response = connection.getresponse().read()
                        #Save OSL script
                        osl_filepath = os.path.join(matlibpath, "my-materials", script_name + ext)
                        osl_file = open(osl_filepath, mode="w+b")
                        osl_file.write(response)
                        osl_file.close()
                        node.filepath = osl_filepath
                        
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            return
                        
                        if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            osl_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            osl_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)):
                            osl_filepath = os.path.join(matlibpath, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache OSL script
                            if library == "composite":
                                osl_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "scripts", script_name + ext)
                                osl_file = open(osl_filepath, mode="w+b")
                                osl_file.write(response)
                                osl_file.close()
                            else:
                                osl_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                osl_file = open(osl_filepath, mode="w+b")
                                osl_file.write(response)
                                osl_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            osl_filepath = ""
                        node.filepath = osl_filepath
            else:
                if 'script' in node_data:
                    if group_mode:
                        node.script = group_scripts[int(node_data['script'].value)]
                    else:
                        node.script = osl_scripts[int(node_data['script'].value)]
            if node.inputs:
                for input in node.inputs:
                    if input.name.lower() in node_data:
                        if input.type == 'RGBA':
                            input.default_value = color(node_data[input.name.lower()].value)
                        elif input.type == 'VECTOR':
                            input.default_value = vector(node_data[input.name.lower()].value)
                        elif input.type == 'VALUE':
                            input.default_value = float(node_data[input.name.lower()].value)
                        elif input.type == 'INT':
                            input.default_value = int(node_data[input.name.lower()].value)
                        elif input.type == 'BOOL':
                            input.default_value = boolean(node_data[input.name.lower()].value)
                        elif input.type != 'SHADER':
                            input.default_value = str(node_data[input.name.lower()].value)
                    elif input.type != "SHADER":
                        node_message = ['WARNING', "There was no value specified for input \"%s\", leaving at default." % input.name]
            
        elif node_type == "GROUP":
            print ("GROUP")
            if 'group' in node_data and "." in node_data['group'].value:
                if "file://" in node_data['group'].value:
                    group_filepath = node_data['group'].value[7:]
                    
                    group_name = group_filepath.replace("_", " ")
                    
                    if node_data['group'].value[-4:].lower() != ".bcg":
                        node_message = ['ERROR', "The node group file referenced by this group node is not .bcg."]
                        return
                    
                    if os.sep in group_name:
                        group_name = group_name.split(os.sep)[-1]
                    group_name = group_name[:-4].title()
                elif "http://" in node_data['group'].value and bpy.context.scene.mat_lib_groups_only_trusted == False:
                    group_name = node_data['group'].value.replace("_", " ").split("/")[-1][:-4].title()
                    group_host = node_data['group'].value[7:].split("/")[0]
                    group_location = node_data['group'].value[(7 + len(group_host)):]
                    
                    if node_data['group'].value[-4:].lower() != ".bcg":
                        node_message = ['ERROR', "The node group file referenced by this group node is not .bcg; not downloading."]
                        return
                    
                    connection = http.client.HTTPConnection(group_host)
                    connection.request("GET", group_location + group_name + ".bcg")
                    response = connection.getresponse().read()
                    #Save node group
                    group_filepath = os.path.join(matlibpath, "my-materials", group_name + ".bcg")
                    group_file = open(group_filepath, mode="w+b")
                    group_file.write(response)
                    group_file.close()
                    
                else:
                    group_name = node_data['group'].value.replace("_", " ")[:-4].title()
                    
                    if node_data['group'].value[-4:].lower() != ".bcg":
                        node_message = ['ERROR', "The node group file referenced by this group node is not .bcg; not downloading."]
                        return
                    
                    if library == "composite" and os.path.exists(os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")):
                        group_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")
                    elif library != "bundled" and os.path.exists(os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")):
                        group_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")
                    elif library == "bundled" and os.path.exists(os.path.join(matlibpath, "bundled", "cycles", "groups", group_name + ".bcg")):
                        group_filepath = os.path.join(matlibpath, "bundled", "cycles", "groups", group_name + ".bcg")
                    elif working_mode == "online":
                        connection = http.client.HTTPConnection(mat_lib_host)
                        connection.request("GET", mat_lib_location + "cycles/groups/" + group_name + ".bcg")
                        response = connection.getresponse().read()
                        
                        #Cache node group
                        if library == "composite":
                            group_filepath = os.path.join(matlibpath, mat_lib_host, "cycles", "groups", group_name + ".bcg")
                        else:
                            group_filepath = os.path.join(matlibpath, mat_lib_host, library, "cycles", "groups", group_name + ".bcg")
                        group_file = open(group_filepath, mode="w+b")
                        group_file.write(response)
                        group_file.close()
                    else:
                        node_message = ['ERROR', "The node group file, \"%s\", is not cached; cannot download in offline mode." % (group_name + ".bcg")]
                    
                if group_filepath:
                    group_file = open(group_filepath, mode="r", encoding="UTF-8")
                    group_text = group_file.read()
                    group_file.close()
                    node_group = addNodeGroup(group_name, group_text)
                else:
                    node_group = None
            elif 'group' in node_data:
                node_group = node_groups[int(node_data['group'].value)]
            if node_group:
                node = node_tree.nodes.new(node_types['SHADER'][node_type], node_group)
            if node.inputs:
                for input in node.inputs:
                    if input.name.lower().replace(" ", "_") in node_data:
                        if input.type == 'RGBA':
                            input.default_value = color(node_data[input.name.lower().replace(" ", "_")].value)
                        elif input.type == 'VECTOR':
                            input.default_value = vector(node_data[input.name.lower().replace(" ", "_")].value)
                        elif input.type == 'VALUE':
                            input.default_value = float(node_data[input.name.lower().replace(" ", "_")].value)
                        elif input.type == 'INT':
                            input.default_value = int(node_data[input.name.lower().replace(" ", "_")].value)
                        elif input.type == 'BOOL':
                            input.default_value = boolean(node_data[input.name.lower().replace(" ", "_")].value)
                        elif input.type != 'SHADER':
                            input.default_value = str(node_data[input.name.lower().replace(" ", "_")].value)
                    elif input.type != 'SHADER':
                        node_message = ['WARNING', "There was no value specified for input \"%s\", leaving at default." % input.name]
                    print(input.type)
            
        else:
            node_message = ['ERROR', """The material file contains the node type \"%s\", which is not known.
The material file may contain an error, or you may need to check for updates to this add-on.""" % node_type]
            return
        node.location = node_location
        
        #Give the node a custom label
        if 'label' in node_data:
            node.label = node_data['label'].value
        
        #Give the node a custom color if needed and able to
        if 'custom_color' in node_data and hasattr(node, 'use_custom_color'):
            node.use_custom_color = True
            node.color = color(node_data['custom_color'].value)
        
        #Collapse node if needed and able to
        if 'hide' in node_data and hasattr(node, 'hide'):
            node.hide = boolean(node_data['hide'].value)
        
        #Mute node if needed and able to
        if 'mute' in node_data and hasattr(node, 'mute'):
            node.mute = boolean(node_data['mute'].value)
        
        #Set node width
        if 'width' in node_data and bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.66:
            if node.hide:
                node.width = int(node_data['width'].value)
            else:
                node.width = int(node_data['width'].value)

def boolean(string):
    if string == "True":
        boolean = True
    elif string == "False":
        boolean = False
    elif string == "true":
        boolean = True
    elif string == "false":
        boolean = False
    else:
        print('Error converting string to a boolean')
        return
    return boolean

def color(string):
    if "rgba" in string:
        colors = string[5:-1].replace(" ", "").split(",")
        r = float(colors[0])
        g = float(colors[1])
        b = float(colors[2])
        a = float(colors[3])
        color = [r,g,b,a]
    elif "rgb" in string:
        colors = string[4:-1].replace(" ", "").split(",")
        r = float(colors[0])
        g = float(colors[1])
        b = float(colors[2])
        color = [r,g,b]
    else:
        print('Error converting string to a color')
        return
    return color

def vector(string):
    import mathutils
    if "Vector" in string:
        vectors = string[7:-1].replace(" ", "").split(",")
        x = float(vectors[0])
        y = float(vectors[1])
        z = float(vectors[2])
        vector = mathutils.Vector((x, y, z))
    else:
        print('Error converting string to a vector')
        return
    return vector

class MaterialConvert(bpy.types.Operator):
    '''Convert material(s) to the .bcm format'''
    bl_idname = "material.libraryconvert"
    bl_label = "Convert Cycles Material to .bcm"
    save_location = bpy.props.StringProperty()
    all_materials = bpy.props.BoolProperty()

    def execute(self, context):
        global material_file_contents
        global script_stack
        global group_stack
        global curve_stack
        
        if self.all_materials:
            #For all_materials, access the materials with an index
            mat = 0
            loop_length = len(bpy.data.materials)
        else:
            if not context.active_object:
                self.save_location = ""
                self.all_materials = False
                self.report({'ERROR'}, "No object selected!")
                return {'CANCELLED'}
            if not context.active_object.active_material:
                self.save_location = ""
                self.all_materials = False
                self.report({'ERROR'}, "No material selected!")
                return {'CANCELLED'}
            #For single materials, access the materials with a name
            mat = context.active_object.active_material.name
            loop_length = 1
        
        if self.save_location is "":
            if context.scene.mat_lib_bcm_write is not "":
                txt = context.scene.mat_lib_bcm_write
            else:
                txt = "bcm_file"
            
            if txt not in bpy.data.texts:
                bpy.data.texts.new(txt)
        
        j = 0
        while j < loop_length:
            if self.save_location is not "":
                if self.all_materials:
                    filename = bpy.data.materials[mat].name.replace("(", "")
                else:
                    filename = mat.replace("(", "")
                filename = filename.replace(")", "")
                filename = filename.replace("!", "")
                filename = filename.replace("@", "")
                filename = filename.replace("#", "")
                filename = filename.replace("$", "")
                filename = filename.replace("%", "")
                filename = filename.replace("&", "")
                filename = filename.replace("*", "")
                filename = filename.replace("/", "")
                filename = filename.replace("|", "")
                filename = filename.replace("\\", "")
                filename = filename.replace("'", "")
                filename = filename.replace("\"", "")
                filename = filename.replace("?", "")
                filename = filename.replace(";", "")
                filename = filename.replace(":", "")
                filename = filename.replace("[", "")
                filename = filename.replace("]", "")
                filename = filename.replace("{", "")
                filename = filename.replace("}", "")
                filename = filename.replace("`", "")
                filename = filename.replace("~", "")
                filename = filename.replace("+", "")
                filename = filename.replace("=", "")
                filename = filename.replace(".", "")
                filename = filename.replace(",", "")
                filename = filename.replace("<", "")
                filename = filename.replace(">", "")
                filename = filename.replace(" ", "_")
                filename = filename.replace("-", "_")
                filename = filename.lower()
            
            material_file_contents = ""
            write('<?xml version="1.0" encoding="UTF-8"?>')
            
            red = smallFloat(bpy.data.materials[mat].diffuse_color.r)
            green = smallFloat(bpy.data.materials[mat].diffuse_color.g)
            blue = smallFloat(bpy.data.materials[mat].diffuse_color.b)
            write("\n<material view_color=\"%s\"" % ("rgb(" + red + ", " + green + ", " + blue + ")"))
            
            write(" sample_lamp=\"" + str(bpy.data.materials[mat].cycles.sample_as_light) + "\"")
            if bpy.data.materials[mat].preview_render_type != 'SPHERE':
                write(" preview_type=\"%s\"" % bpy.data.materials[mat].preview_render_type)
            write(">\n\t<nodes>")
            
            group_warning = False
            frame_warning = False
            for node in bpy.data.materials[mat].node_tree.nodes:
                if hasattr(node, 'node_tree'):
                    node_type = "GROUP"
                    #group_warning = True
                    write("\n\t\t<node type=\"GROUP\"")
                        
                    #Write node custom color
                    if hasattr(node, 'use_custom_color') and node.use_custom_color:
                        r = smallFloat(node.color.r)
                        g = smallFloat(node.color.g)
                        b = smallFloat(node.color.b)
                        write(" custom_color=\"%s\"" % ("rgb(" + r + ", " + g + ", " + b + ")"))
                    
                    #Write node label
                    if node.label:
                        write(" label=\"%s\"" % node.label)
                    
                    #Write node hidden-ness
                    if hasattr(node, 'hide') and node.hide:
                        write(" hide=\"True\"")
                    
                    #Write node mute-ness
                    if hasattr(node, 'mute') and node.mute:
                        write(" mute=\"True\"")
                    
                    if self.save_location is not "" and context.scene.mat_lib_external_groups:
                        group_filename = node.node_tree.name.lower()
                        group_filename = group_filename.replace("(", "").replace(")", "").replace("!", "").replace("@", "")
                        group_filename = group_filename.replace("#", "").replace("$", "").replace("%", "").replace("&", "")
                        group_filename = group_filename.replace("*", "").replace("/", "").replace("|", "").replace("\\", "")
                        group_filename = group_filename.replace("'", "").replace("\"", "").replace("?", "").replace(";", "")
                        group_filename = group_filename.replace(":", "").replace("[", "").replace("]", "").replace("{", "")
                        group_filename = group_filename.replace("}", "").replace("`", "").replace("~", "").replace("+", "")
                        group_filename = group_filename.replace("=", "").replace(".", "").replace(",", "").replace("<", "")
                        group_filename = self.save_location + group_filename.replace(">", "").replace(" ", "_").replace("-", "_") + ".bcg"
                        write(" group=\"file://%s\"" % group_filename)
                        group_file = open(group_filename, mode="w", encoding="UTF-8")
                        group_file.write(getGroupData(node.node_tree.name).replace("\n\t\t", "\n").replace("\n<group", "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<group"))
                        group_file.close()
                    else:
                        if node.node_tree.name in group_stack:
                            write(" group=\"%s\"" % group_stack.index(node.node_tree.name))
                        else:
                            write(" group=\"%s\"" % len(group_stack))
                            group_stack.append(node.node_tree.name)
                    
                    if node.inputs:
                        for input in node.inputs:
                            if input.type == 'RGBA':
                                input_value = rgba(input.default_value)
                            elif input.type == 'VECTOR':
                                input_value = smallVector(input.default_value)
                            elif input.type == 'VALUE':
                                input_value = smallFloat(input.default_value)
                            elif input.type == 'INT':
                                input_value = str(input.default_value)
                            elif input.type == 'BOOL':
                                input_value = str(input.default_value)
                            elif input.type != 'SHADER':
                                input_value = str(input.default_value)
                            
                            if input.type != 'SHADER':
                                write(" %s=\"%s\"" % (input.name.lower().replace(" ", "_"), input_value))
                    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.65:
                        if node.hide:
                            write(" width=\"%s\"" % int(node.width_hidden))
                        else:
                            write(" width=\"%s\"" % int(node.width))
                    write(getLocation(node))
                    write(" />")
                    
                elif node.type == 'FRAME' and bpy.app.version[0] + (bpy.app.version[1] / 100.0) >= 2.65:
                    #Don't attempt to write frame nodes in builds previous
                    #to 2.65, as Blender's nodes.new() operator was
                    #unable to add FRAME nodes. Was fixed with r51926.
                    frame_warning = True
                    print("Skipping frame node; this Blender version will not support adding it back."\
                        "\nFrame nodes are not supported prior to Blender 2.65.")
                else:
                    #Write node opening bracket
                    write("\n\t\t<node ")
                    
                    #Write node type
                    write("type=\"%s\"" % node.type)
                    
                    #Write node custom color
                    if hasattr(node, 'use_custom_color') and node.use_custom_color:
                        r = smallFloat(node.color.r)
                        g = smallFloat(node.color.g)
                        b = smallFloat(node.color.b)
                        write(" custom_color=\"%s\"" % ("rgb(" + r + ", " + g + ", " + b + ")"))
                    
                    #Write node label
                    if node.label:
                        write(" label=\"%s\"" % node.label)
                    
                    #Write node hidden-ness
                    if hasattr(node, 'hide') and node.hide:
                        write(" hide=\"True\"")
                    
                    #Write node mute-ness
                    if hasattr(node, 'mute') and node.mute:
                        write(" mute=\"True\"")
                        
                    #Write node data
                    write(getNodeData(node))
                    
                    #Write node closing bracket
                    write(" />")
            
            write("\n\t</nodes>")
            
            write("\n\t<links>")
            writeNodeLinks(bpy.data.materials[mat].node_tree)
            write("\n\t</links>")
            
            #Add any curves if needed.
            if curve_stack:
                write("\n\t<curves>")
                i = 0
                while i < len(curve_stack):
                    write(getCurveData(i))
                    i += 1
                write("\n\t</curves>")
                curve_stack = []
            
            #Add any groups if needed.
            if group_stack:
                write("\n\t<groups>")
                i = 0
                while i < len(group_stack):
                    write(getGroupData(i))
                    i += 1
                write("\n\t</groups>")
                group_stack = []
            
            #Add any scripts if needed.
            if script_stack:
                write("\n\t<scripts>")
                i = 0
                while i < len(script_stack):
                    write("\n\t\t<script name=\"%s\" id=\"%s\">\n" % (script_stack[i], str(i)))
                    first_line = True
                    for l in bpy.data.texts[script_stack[i]].lines:
                        if first_line == True:
                            write(l.body.replace("<", "lt;").replace(">", "gt;"))
                            first_line = False
                        else:
                            write("<br />" + l.body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;"))
                    write("\n\t\t</script>")
                    i += 1
                write("\n\t</scripts>")
                script_stack = []
            write("\n</material>")
            
            if self.save_location == "":
                bpy.data.texts[txt].clear()
                bpy.data.texts[txt].write(material_file_contents)
                if not self.all_materials:
                    if frame_warning:
                        self.report({'WARNING'}, "Material \"" + mat + "\" contains a frame node which was skipped; see console for details.")
                    else:
                        self.report({'INFO'}, "Material \"" + mat + "\" written to Text \"" + txt + "\" as .bcm")
            else:
                print(context.scene.mat_lib_bcm_save_location + filename + ".bcm")
                bcm_file = open(context.scene.mat_lib_bcm_save_location + filename + ".bcm", mode="w", encoding="UTF-8")
                bcm_file.write(material_file_contents)
                bcm_file.close()
                if not self.all_materials:
                    if frame_warning:
                        self.report({'WARNING'}, "Material \"" + mat + "\" contains a frame node which was skipped; see console for details.")
                    else:
                        self.report({'INFO'}, "Material \"" + mat + "\" saved to \"" + filename + ".bcm\"")
            j += 1
            if self.all_materials:
                mat += 1
        if self.all_materials and not group_warning and not frame_warning:
            self.report({'INFO'}, "All materials successfully saved!")
        
        self.save_location = ""
        self.all_materials = False
        return {'FINISHED'}
    
class GroupConvert(bpy.types.Operator):
    '''Convert group(s) to the .bcg format'''
    bl_idname = "material.libraryconvertgroup"
    bl_label = "Convert Cycles Nodegroup to .bcg"
    save_location = bpy.props.StringProperty()
    all_groups = bpy.props.BoolProperty()
    
    def execute(self, context):
        global material_file_contents
        global script_stack
        global group_stack
        
        if self.all_groups:
            #For all_groups, access the node groups with an index
            group = 0
            loop_length = len(bpy.data.node_groups)
        else:
            if not context.active_object:
                self.save_location = ""
                self.all_groups = False
                self.report({'ERROR'}, "No object selected!")
                return {'CANCELLED'}
            if not context.active_object.active_material:
                self.save_location = ""
                self.all_groups = False
                self.report({'ERROR'}, "No material selected!")
                return {'CANCELLED'}
            if not context.active_object.active_material.node_tree.nodes.active or context.active_object.active_material.node_tree.nodes.active.type != 'GROUP':
                self.save_location = ""
                self.all_groups = False
                self.report({'ERROR'}, "No active group node!")
                return {'CANCELLED'}
            
            #For single groups, access the node group with a name
            group = context.active_object.active_material.node_tree.nodes.active.node_tree.name
            loop_length = 1
        
        if self.save_location == "":
            if context.scene.mat_lib_bcg_write != "":
                txt = context.scene.mat_lib_bcg_write
            else:
                txt = "bcg_file"
            
            if txt not in bpy.data.texts:
                bpy.data.texts.new(txt)
        
        j = 0
        while j < loop_length:
            if self.save_location != "":
                if self.all_groups:
                    filename = bpy.data.node_groups[group].name.replace("(", "")
                else:
                    filename = group.replace("(", "")
                filename = filename.replace(")", "")
                filename = filename.replace("!", "")
                filename = filename.replace("@", "")
                filename = filename.replace("#", "")
                filename = filename.replace("$", "")
                filename = filename.replace("%", "")
                filename = filename.replace("&", "")
                filename = filename.replace("*", "")
                filename = filename.replace("/", "")
                filename = filename.replace("|", "")
                filename = filename.replace("\\", "")
                filename = filename.replace("'", "")
                filename = filename.replace("\"", "")
                filename = filename.replace("?", "")
                filename = filename.replace(";", "")
                filename = filename.replace(":", "")
                filename = filename.replace("[", "")
                filename = filename.replace("]", "")
                filename = filename.replace("{", "")
                filename = filename.replace("}", "")
                filename = filename.replace("`", "")
                filename = filename.replace("~", "")
                filename = filename.replace("+", "")
                filename = filename.replace("=", "")
                filename = filename.replace(".", "")
                filename = filename.replace(",", "")
                filename = filename.replace("<", "")
                filename = filename.replace(">", "")
                filename = filename.replace(" ", "_")
                filename = filename.replace("-", "_")
                filename = filename.lower()
                group_location = self.save_location + filename + ".bcg"
                group_file = open(group_location, mode="w", encoding="UTF-8")
                group_file.write(getGroupData(bpy.data.node_groups[group].name).replace("\n\t\t", "\n").replace("\n<group", "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<group"))
                group_file.close()
                if not self.all_groups:
                    self.report({'INFO'}, "Nodegroup \"" + group + "\" saved to \"" + filename + ".bcg\"")
            else:
                bpy.data.texts[txt].clear()
                bpy.data.texts[txt].write(getGroupData(group).replace("\n\t\t", "\n").replace("\n<group", "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<group"))
                self.report({'INFO'}, "Nodegroup \"" + group + "\" saved to \"" + txt + "\"")
            j += 1
            if self.all_groups:
                group += 1
        if self.all_groups:
            self.report({'INFO'}, "All nodegroups successfully saved!")
        
        self.save_location = ""
        self.all_groups = False
        return {'FINISHED'}

def getGroupData(index):
    global group_script_stack
    global group_curve_stack
    
    group_text = ("\n\t\t<group")
    if type(index) == int:
        group_text += (" name=\"%s\" id=\"%s\"" % (group_stack[index], str(index)))
        index = group_stack[index]
    
    group_text += (">\n\t\t\t<groupnodes>")
    for node in bpy.data.node_groups[index].nodes:
        #Write node opening bracket
        group_text += ("\n\t\t\t\t<groupnode ")
        
        #Write node type
        group_text += ("type=\"%s\"" % node.type)
        
        #Write node custom color
        if hasattr(node, 'use_custom_color') and node.use_custom_color:
            r = smallFloat(node.color.r)
            g = smallFloat(node.color.g)
            b = smallFloat(node.color.b)
            group_text += (" custom_color=\"%s\"" % ("rgb(" + r + ", " + g + ", " + b + ")"))
        
        #Write node label
        if node.label:
            group_text += (" label=\"%s\"" % node.label)
        
        #Write node hidden-ness
        if hasattr(node, 'hide') and node.hide:
            group_text += (" hide=\"True\"")
        
        #Write node mute-ness
        if hasattr(node, 'mute') and node.mute:
            group_text += (" mute=\"True\"")
        
        #Write node data
        group_text += getNodeData(node, True)
        
        #Write node closing bracket
        group_text += (" />")
    group_text += ("\n\t\t\t</groupnodes>")
    
    if bpy.data.node_groups[index].inputs:
        group_text += ("\n\t\t\t<groupinputs>")
        for input in bpy.data.node_groups[index].inputs:
            group_text += ("\n\t\t\t\t<groupinput name=\"%s\" type=\"%s\"" % (input.name, input.type))
            if input.type == 'RGBA':
                input_value = rgba(input.default_value)
            elif input.type == 'VECTOR':
                input_value = smallVector(input.default_value)
            elif input.type == 'VALUE':
                input_value = smallFloat(input.default_value)
            elif input.type == 'INT':
                input_value = str(input.default_value)
            elif input.type == 'BOOL':
                input_value = str(input.default_value)
            elif input.type != 'SHADER':
                input_value = str(input.default_value)
                            
            if input.type != 'SHADER':
                group_text += (" value=\"%s\"" % input_value)
            group_text += (" />")
        group_text += ("\n\t\t\t</groupinputs>")
        
    if bpy.data.node_groups[index].outputs:
        group_text += ("\n\t\t\t<groupoutputs>")
        for output in bpy.data.node_groups[index].outputs:
            group_text += ("\n\t\t\t\t<groupoutput name=\"%s\" type=\"%s\"" % (output.name, output.type))
            if output.type == 'RGBA':
                output_value = rgba(output.default_value)
            elif output.type == 'VECTOR':
                output_value = smallVector(output.default_value)
            elif output.type == 'VALUE':
                output_value = smallFloat(output.default_value)
            elif output.type == 'INT':
                output_value = str(output.default_value)
            elif output.type == 'BOOL':
                output_value = str(output.default_value)
            elif hasattr(output, 'default_value'):
                output_value = str(output.default_value)
            else:
                output_value = ""
            if output_value:
                group_text += (" value=\"%s\"" % output_value)
            group_text += (" />")
        group_text += ("\n\t\t\t</groupoutputs>")
    
    if bpy.data.node_groups[index].links:
        group_text += ("\n\t\t\t<grouplinks>")
        group_text += getNodeGroupLinks(bpy.data.node_groups[index])
        group_text += ("\n\t\t\t</grouplinks>")
    
    if group_curve_stack:
        group_text += ("\n\t\t\t<groupcurves>")
        i = 0
        while i < len(group_curve_stack):
            group_text += getCurveData(i, True).replace("\t<curve", "\t\t\t<groupcurve").replace("\t</curve", "\t\t\t</groupcurve").replace("<point", "\t\t<point")
            i += 1
        group_text += ("\n\t\t\t</groupcurves>")
        group_curve_stack = []
    
    if group_script_stack:
        group_text += ("\n\t\t\t<groupscripts>")
        i = 0
        while i < len(group_script_stack):
            group_text += ("\n\t\t\t\t<groupscript name=\"%s\" id=\"%s\">\n" % (group_script_stack[i], str(i)))
            first_line = True
            for l in bpy.data.texts[group_script_stack[i]].lines:
                if first_line == True:
                    group_text += (l.body.replace("<", "lt;").replace(">", "gt;"))
                    first_line = False
                else:
                    group_text += ("<br />" + l.body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;"))
            group_text += ("\n\t\t\t\t</groupscript>")
            i += 1
        group_text += ("\n\t\t\t</groupscripts>")
        group_script_stack = []
    
    group_text += ("\n\t\t</group>")
    return group_text

def getCurveData(index, group_mode = False):
    text = ""
    if group_mode:
        text += ("\n\t\t<curve extend=\"%s\" id=\"%s\">" % (group_curve_stack[index].extend, index))
        p = 0
        while p < len(group_curve_stack[index].points):
            text += ("\n\t\t\t<point type=\"%s\" loc=\"%s, %s\" />" % (group_curve_stack[index].points[p].handle_type, smallFloat(group_curve_stack[index].points[p].location.x), smallFloat(group_curve_stack[index].points[p].location.y)))
            p += 1
    else:
        text += ("\n\t\t<curve extend=\"%s\" id=\"%s\">" % (curve_stack[index].extend, index))
        p = 0
        while p < len(curve_stack[index].points):
            text += ("\n\t\t\t<point type=\"%s\" loc=\"%s, %s\" />" % (curve_stack[index].points[p].handle_type, smallFloat(curve_stack[index].points[p].location.x), smallFloat(curve_stack[index].points[p].location.y)))
            p += 1
    
    text += ("\n\t\t</curve>")
    return text

def getNodeData(node, group_mode = False):
    global material_file_contents
    global curve_stack
    global script_stack
    
    text = ""
    
    I = node.inputs
    O = node.outputs
    
    if "NodeGroup" in str(node.items):
        node_type = "GROUP"
    else:
        node_type = node.type
        
    if node_type == "GROUP":
        print("GROUP NODE!")
        text += ("ERROR: NESTED GROUP NODES NOT YET SUPPORTED.")
        
        #INPUT TYPES
    elif node_type == "ATTRIBUTE":
        print("ATTRIBUTE")
        text += (" attribute=\"%s\"" % node.attribute_name)
    
    elif node_type == "CAMERA":
        print("CAMERA")
        
    elif node_type == "FRESNEL":
        print("FRESNEL")
        text += (" ior=\"%s\"" % smallFloat(I['IOR'].default_value))
    
    elif node_type == "LAYER_WEIGHT":
        print("LAYER_WEIGHT")
        text += (" blend=\"%s\"" % smallFloat(I['Blend'].default_value))
    
    elif node_type == "LIGHT_PATH":
        print("LIGHT_PATH")
    
    elif node_type == "NEW_GEOMETRY":
        print("NEW_GEOMETRY")
    
    elif node_type == "HAIR_INFO":
        print("HAIR_INFO")
    
    elif node_type == "OBJECT_INFO":
        print("OBJECT_INFO")
    
    elif node_type == "PARTICLE_INFO":
        print("PARTICLE_INFO")
    
    elif node_type == "RGB":
        print("RGB")
        text += (" color=\"%s\"" % rgba(O['Color'].default_value))
    
    elif node_type == "TANGENT":
        print("TANGENT")
        text += (" direction=\"%s\"" % node.direction_type)
        text += (" axis=\"%s\"" % node.axis)
    
    elif node_type == "TEX_COORD":
        print("TEX_COORD")
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.64:
            text += (" dupli=\"%s\"" % node.from_dupli)
        else:
            text += (" dupli=\"False\"")
    
    elif node_type == "VALUE":
        print("VALUE")
        text += (" value=\"%s\"" % smallFloat(O['Value'].default_value))
        
        #OUTPUT TYPES
    elif node_type == "OUTPUT_LAMP":
        print("OUTPUT_LAMP")
    
    elif node_type == "OUTPUT_MATERIAL":
        print("OUTPUT_MATERIAL")
    
    elif node_type == "OUTPUT_WORLD":
        print("OUTPUT_WORLD")
    
        #SHADER TYPES
    elif node_type == "ADD_SHADER":
        print("ADD_SHADER")
    
    elif node_type == "AMBIENT_OCCLUSION":
        print("AMBIENT_OCCLUSION")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "BACKGROUND":
        print("BACKGROUND")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
    
    elif node_type == "BSDF_ANISOTROPIC":
        print("BSDF_ANISOTROPIC")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
        text += (" anisotropy=\"%s\"" % smallFloat(I['Anisotropy'].default_value))
        text += (" rotation=\"%s\"" % smallFloat(I['Rotation'].default_value))
    
    elif node_type == "BSDF_DIFFUSE":
        print("BSDF_DIFFUSE")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
    
    elif node_type == "BSDF_GLASS":
        print("BSDF_GLASS")
        text += (" distribution=\"%s\"" % node.distribution)
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
        text += (" ior=\"%s\"" % smallFloat(I['IOR'].default_value))
    
    elif node_type == "BSDF_GLOSSY":
        print("BSDF_GLOSSY")
        text += (" distribution=\"%s\"" % node.distribution)
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
    
    elif node_type == "BSDF_REFRACTION":
        print("BSDF_REFRACTION")
        text += (" distribution=\"%s\"" % node.distribution)
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
        text += (" ior=\"%s\"" % smallFloat(I['IOR'].default_value))
    
    elif node_type == "BSDF_TRANSLUCENT":
        print("BSDF_TRANSLUCENT")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "BSDF_TRANSPARENT":
        print("BSDF_TRANSPARENT")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "BSDF_VELVET":
        print("BSDF_VELVET")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" sigma=\"%s\"" % smallFloat(I['Sigma'].default_value))
    
    elif node_type == "EMISSION":
        print("EMISSION")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
    
    elif node_type == "HOLDOUT":
        print("HOLDOUT")
    
    elif node_type == "MIX_SHADER":
        print("MIX_SHADER")
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        
        #TEXTURE TYPES
    elif node_type == "TEX_BRICK":
        print ("TEX_BRICK")
        text += (" offset=\"%s\"" % smallFloat(node.offset))
        text += (" offset_freq=\"%s\"" % str(node.offset_frequency))
        text += (" squash=\"%s\"" % smallFloat(node.squash))
        text += (" squash_freq=\"%s\"" % str(node.squash_frequency))
        text += (" color1=\"%s\"" % rgba(I['Color1'].default_value))
        text += (" color2=\"%s\"" % rgba(I['Color2'].default_value))
        text += (" mortar=\"%s\"" % rgba(I['Mortar'].default_value))
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        text += (" mortar_size=\"%s\"" % smallFloat(I['Mortar Size'].default_value))
        text += (" bias=\"%s\"" % smallFloat(I['Bias'].default_value))
        text += (" width=\"%s\"" % smallFloat(I['Brick Width'].default_value))
        text += (" height=\"%s\"" % smallFloat(I['Row Height'].default_value))
            
    elif node_type == "TEX_CHECKER":
        print("TEX_CHECKER")
        text += (" color1=\"%s\"" % rgba(I['Color1'].default_value))
        text += (" color2=\"%s\"" % rgba(I['Color2'].default_value))
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
    
    elif node_type == "TEX_ENVIRONMENT":
        print("TEX_ENVIRONMENT")
        if node.image:
            text += (" image=\"file://%s\"" % os.path.realpath(bpy.path.abspath(node.image.filepath)))
            text += (" source=\"%s\"" % node.image.source)
            if node.image.source == "SEQUENCE" or node.image.source == "MOVIE":
                text += (" frame_duration=\"%s\"" % str(node.image_user.frame_duration))
                text += (" frame_start=\"%s\"" % str(node.image_user.frame_start))
                text += (" frame_offset=\"%s\"" % str(node.image_user.frame_offset))
                text += (" cyclic=\"%s\"" % str(node.image_user.use_cyclic))
                text += (" auto_refresh=\"%s\"" % str(node.image_user.use_auto_refresh))
        else:
            text += (" image=\"\"")
        text += (" color_space=\"%s\"" % node.color_space)
        text += (" projection=\"%s\"" % node.projection)
    
    elif node_type == "TEX_GRADIENT":
        print("TEX_GRADIENT")
        text += (" gradient=\"%s\"" % node.gradient_type)
    
    elif node_type == "TEX_IMAGE":
        print("TEX_IMAGE")
        if node.image:
            text += (" image=\"file://%s\"" % os.path.realpath(bpy.path.abspath(node.image.filepath)))
            text += (" source=\"%s\"" % node.image.source)
            if node.image.source == "SEQUENCE" or node.image.source == "MOVIE":
                text += (" frame_duration=\"%s\"" % str(node.image_user.frame_duration))
                text += (" frame_start=\"%s\"" % str(node.image_user.frame_start))
                text += (" frame_offset=\"%s\"" % str(node.image_user.frame_offset))
                text += (" cyclic=\"%s\"" % str(node.image_user.use_cyclic))
                text += (" auto_refresh=\"%s\"" % str(node.image_user.use_auto_refresh))
        else:
            text += (" image=\"\"")
        text += (" color_space=\"%s\"" % node.color_space)
        text += (" projection=\"%s\"" % node.projection)
        if node.projection == "BOX":
            text += (" blend=\"%s\"" % smallFloat(node.projection_blend))
        else:
            text += (" projection=\"FLAT\"")
    
    elif node_type == "TEX_MAGIC":
        print("TEX_MAGIC")
        text += (" depth=\"%s\"" % str(node.turbulence_depth))
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        text += (" distortion=\"%s\"" % smallFloat(I['Distortion'].default_value))
    
    elif node_type == "TEX_MUSGRAVE":
        print("TEX_MUSGRAVE")
        text += (" musgrave=\"%s\"" % node.musgrave_type)
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        text += (" detail=\"%s\"" % smallFloat(I['Detail'].default_value))
        text += (" dimension=\"%s\"" % smallFloat(I['Dimension'].default_value))
        text += (" lacunarity=\"%s\"" % smallFloat(I['Lacunarity'].default_value))
        text += (" offset=\"%s\"" % smallFloat(I['Offset'].default_value))
        text += (" gain=\"%s\"" % smallFloat(I['Gain'].default_value))
    
    elif node_type == "TEX_NOISE":
        print("TEX_NOISE")
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        text += (" detail=\"%s\"" % smallFloat(I['Detail'].default_value))
        text += (" distortion=\"%s\"" % smallFloat(I['Distortion'].default_value))
    
    elif node_type == "TEX_SKY":
        print("TEX_SKY")
        text += (" sun_direction=\"%s\"" % smallVector(node.sun_direction))
        text += (" turbidity=\"%s\"" % smallFloat(node.turbidity))
    
    elif node_type == "TEX_VORONOI":
        print("TEX_VORONOI")
        text += (" coloring=\"%s\"" % node.coloring)
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
    
    elif node_type == "TEX_WAVE":
        print("TEX_WAVE")
        text += (" wave=\"%s\"" % node.wave_type)
        text += (" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        text += (" distortion=\"%s\"" % smallFloat(I['Distortion'].default_value))
        text += (" detail=\"%s\"" % smallFloat(I['Detail'].default_value))
        text += (" detail_scale=\"%s\"" % smallFloat(I['Detail Scale'].default_value))
    
        #COLOR TYPES
    elif node_type == "BRIGHTCONTRAST":
        print("BRIGHTCONTRAST")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" bright=\"%s\"" % smallFloat(I['Bright'].default_value))
        text += (" contrast=\"%s\"" % smallFloat(I['Contrast'].default_value))
        
    elif node_type == "CURVE_RGB":
        print("CURVE_RGB")
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        if group_mode:
            text += (" curve_c=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[3])
            text += (" curve_r=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[0])
            text += (" curve_g=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[1])
            text += (" curve_b=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[2])
        else:
            text += (" curve_c=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[3])
            text += (" curve_r=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[0])
            text += (" curve_g=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[1])
            text += (" curve_b=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[2])
    
    elif node_type == "GAMMA":
        print("GAMMA")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        text += (" gamma=\"%s\"" % smallFloat(I['Gamma'].default_value))
    
    elif node_type == "HUE_SAT":
        print("HUE_SAT")
        text += (" hue=\"%s\"" % smallFloat(I['Hue'].default_value))
        text += (" saturation=\"%s\"" % smallFloat(I['Saturation'].default_value))
        text += (" value=\"%s\"" % smallFloat(I['Value'].default_value))
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "LIGHT_FALLOFF":
        print("LIGHT_FALLOFF")
        text += (" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
        text += (" smooth=\"%s\"" % smallFloat(I['Smooth'].default_value))
    
    elif node_type == "MIX_RGB":
        print("MIX_RGB")
        text += (" blend_type=\"%s\"" % node.blend_type)
        text += (" use_clamp=\"%s\"" % str(node.use_clamp))
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        text += (" color1=\"%s\"" % rgba(I[1].default_value))
        text += (" color2=\"%s\"" % rgba(I[2].default_value))
    
    elif node_type == "INVERT":
        print("INVERT")
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        
        #VECTOR TYPES
    elif node_type == "BUMP":
        print("BUMP")
        text += (" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
    
    elif node_type == "CURVE_VEC":
        print("CURVE_VEC")
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        text += (" vector=\"%s\"" % smallVector(I['Vector'].default_value))
        
        if group_mode:
            text += (" curve_x=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[0])
            text += (" curve_y=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[1])
            text += (" curve_z=\"%s\"" % len(group_curve_stack))
            group_curve_stack.append(node.mapping.curves[2])
        else:
            text += (" curve_x=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[0])
            text += (" curve_y=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[1])
            text += (" curve_z=\"%s\"" % len(curve_stack))
            curve_stack.append(node.mapping.curves[2])
        
    elif node_type == "MAPPING":
        print("MAPPING")
        text += (" translation=\"%s\"" % smallVector(node.translation))
        text += (" rotation=\"%s\"" % smallVector(node.rotation))
        text += (" scale=\"%s\"" % smallVector(node.scale))
        
        text += (" use_min=\"%s\"" % str(node.use_min))
        if node.use_min:
            text += (" min=\"%s\"" % smallVector(node.min))
        
        text += (" use_max=\"%s\"" % str(node.use_max))
        if node.use_max:
            text += (" max=\"%s\"" % smallVector(node.max))
        
        vec = I[0].default_value
        text += (" vector=\"%s\"" % smallVector(I['Vector'].default_value))
    
    elif node_type == "NORMAL":
        print("NORMAL")
        text += (" vector_output=\"%s\"" % smallVector(O['Normal'].default_value))
        text += (" vector_input=\"%s\"" % smallVector(I['Normal'].default_value))
        
    elif node_type == "NORMAL_MAP":
        print("NORMAL_MAP")
        text += (" space=\"%s\"" % node.space)
        text += (" uv_map=\"%s\"" % node.uv_map)
        text += (" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
        
        #CONVERTER TYPES
    elif node_type == "COMBRGB":
        print("COMBRGB")
        text += (" red=\"%s\"" % smallFloat(I['R'].default_value))
        text += (" green=\"%s\"" % smallFloat(I['G'].default_value))
        text += (" blue=\"%s\"" % smallFloat(I['B'].default_value))
    
    elif node_type == "MATH":
        print("MATH")
        text += (" operation=\"%s\"" % node.operation)
        text += (" use_clamp=\"%s\"" % str(node.use_clamp))
        text += (" value1=\"%s\"" % smallFloat(I[0].default_value))
        text += (" value2=\"%s\"" % smallFloat(I[1].default_value))
        
    elif node_type == "RGBTOBW":
        print ("RGBTOBW")
        text += (" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "SEPRGB":
        print("SEPRGB")
        text += (" image=\"%s\"" % rgba(I['Image'].default_value))
    
    elif node_type == "VALTORGB":
        print("VALTORGB")
        text += (" interpolation=\"%s\"" % str(node.color_ramp.interpolation))
        text += (" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        text += (" stops=\"%s\"" % str(len(node.color_ramp.elements)))
        
        k = 1
        while k <= len(node.color_ramp.elements):
            text += (" stop%s=\"%s\"" % 
            (str(k), 
             (smallFloat(node.color_ramp.elements[k-1].position) +
             "|" + 
             rgba(node.color_ramp.elements[k-1].color))
            ))
            k += 1
    
    elif node_type == "VECT_MATH":
        print("VECT_MATH")
        text += (" operation=\"%s\"" % node.operation)
        text += (" vector1=\"%s\"" % smallVector(I[0].default_value))
        text += (" vector2=\"%s\"" % smallVector(I[1].default_value))
        
        #MISCELLANEOUS NODE TYPES
    elif node_type == "FRAME":
        print("FRAME")
    
    elif node_type == "REROUTE":
        print("REROUTE")
    
    elif node_type == "SCRIPT":
        print("SCRIPT")
        text += (" mode=\"%s\"" % node.mode)
        if node.mode == 'EXTERNAL':
            if node.filepath:
                text += (" script=\"file://%s\"" % os.path.realpath(bpy.path.abspath(node.filepath)))
        else:
            if node.script:
                if group_mode:
                    if node.script.name in group_script_stack:
                        text += (" script=\"%s\"" % group_script_stack.index(node.script.name))
                    else:
                        text += (" script=\"%s\"" % len(group_script_stack))
                        group_script_stack.append(node.script.name)
                else:
                    if node.script.name in script_stack:
                        text += (" script=\"%s\"" % script_stack.index(node.script.name))
                    else:
                        text += (" script=\"%s\"" % len(script_stack))
                        script_stack.append(node.script.name)
        if node.inputs:
            for input in node.inputs:
                if input.type == 'RGBA':
                    input_value = rgba(input.default_value)
                elif input.type == 'VECTOR':
                    input_value = smallVector(input.default_value)
                elif input.type == 'VALUE':
                    input_value = smallFloat(input.default_value)
                elif input.type == 'INT':
                    input_value = str(input.default_value)
                elif input.type == 'BOOL':
                    input_value = str(input.default_value)
                elif input.type != 'SHADER':
                    input_value = str(input.default_value)
                
                if input.type != 'SHADER':
                    text += (" %s=\"%s\"" % (input.name.lower(), input_value))
    else:
        return " ERROR: UNKNOWN NODE TYPE. "
    
    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.65:
        if node.hide:
            text += (" width=\"%s\"" % int(node.width_hidden))
        else:
            text += (" width=\"%s\"" % int(node.width))
    text += getLocation(node)
    return text
    
def rgba(color):
    red = smallFloat(color[0])
    green = smallFloat(color[1])
    blue = smallFloat(color[2])
    alpha = smallFloat(color[3])
    return ("rgba(" + red + ", " + green + ", " + blue + ", " + alpha + ")")

def smallFloat(float):
    if len(str(float)) < (6 + str(float).index(".")):
        return str(float)
    else:
        return str(float)[:(6 + str(float).index("."))]

def smallVector(vector):
    return "Vector(" + smallFloat(vector[0]) + ", " + smallFloat(vector[1]) + ", " + smallFloat(vector[2]) + ")"

def write (string):
    global material_file_contents
    material_file_contents += string

def getLocation(node):
    #X location
    x = str(int(node.location.x))
    #Y location
    y = str(int(node.location.y))
    
    return (" loc=\"" + x + ", " + y + "\"")
    
def writeNodeLinks(node_tree):
    global material_file_contents
    
    #Loop through the links
    i = 0
    while i < len(node_tree.links):
        material_file_contents += ("\n\t\t<link ")
        
        to_node_name = node_tree.links[i].to_node.name
        #Loop through nodes to check name
        e = 0
        while e < len(node_tree.nodes):
            #Write the index if name matches
            if to_node_name == node_tree.nodes[e].name:
                material_file_contents += "to=\"%d\"" % e
                #Set input socket's name
                to_socket = node_tree.links[i].to_socket.path_from_id()
                material_file_contents += (" input=\"%s\"" % to_socket[(to_socket.index("inputs[") + 7):-1])
                e = len(node_tree.nodes)
            e = e + 1
            
        
        from_node_name = node_tree.links[i].from_node.name
        #Loop through nodes to check name
        e = 0
        while e < len(node_tree.nodes):
            #Write the index if name matches
            if from_node_name == node_tree.nodes[e].name:
                material_file_contents += " from=\"%d\"" % e
                #Set input socket's name
                from_socket = node_tree.links[i].from_socket.path_from_id()
                material_file_contents += (" output=\"%s\"" % from_socket[(from_socket.index("outputs[") + 8):-1])
                e = len(node_tree.nodes)
            e = e + 1
        material_file_contents += (" />")
        i = i + 1
    
def getNodeGroupLinks(node_tree):
    link_text = ""
    
    #Loop through the links
    i = 0
    while i < len(node_tree.links):
        link_text += ("\n\t\t\t\t<grouplink ")
        
        if node_tree.links[i].to_node != None:
            to_node_name = node_tree.links[i].to_node.name
            #Loop through nodes to check name
            e = 0
            while e < len(node_tree.nodes):
                #Write the index if name matches
                if to_node_name == node_tree.nodes[e].name:
                    link_text += ("to=\"%s\"" % str(e))
                    #Set input socket's name
                    to_socket = node_tree.links[i].to_socket.path_from_id()
                    link_text += (" input=\"%s\"" % to_socket[(to_socket.index("inputs[") + 7):-1])
                    e = len(node_tree.nodes)
                e = e + 1
        else:
             link_text += ("to=\"o\"")
             to_socket = node_tree.links[i].to_socket.path_from_id()
             link_text += (" input=\"%s\"" % to_socket[(to_socket.index("outputs[") + 8):-1])
        
        if node_tree.links[i].from_node != None:
            from_node_name = node_tree.links[i].from_node.name
            #Loop through nodes to check name
            e = 0
            while e < len(node_tree.nodes):
                #Write the index if name matches
                if from_node_name == node_tree.nodes[e].name:
                    link_text += (" from=\"%d\"" % e)
                    #Set input socket's name
                    from_socket = node_tree.links[i].from_socket.path_from_id()
                    link_text += (" output=\"%s\"" % from_socket[(from_socket.index("outputs[") + 8):-1])
                    e = len(node_tree.nodes)
                e = e + 1
        else:
             link_text += (" from=\"i\"")
             from_socket = node_tree.links[i].from_socket.path_from_id()
             link_text += (" output=\"%s\"" % from_socket[(from_socket.index("inputs[") + 7):-1])
        link_text += (" />")
        i = i + 1
    
    return link_text

def register():
    bpy.utils.register_class(OnlineMaterialLibraryPanel)
    bpy.utils.register_class(LibraryConnect)
    bpy.utils.register_class(LibraryInfo)
    bpy.utils.register_class(LibrarySettings)
    bpy.utils.register_class(LibraryTools)
    bpy.utils.register_class(LibraryHome)
    bpy.utils.register_class(ViewMaterial)
    bpy.utils.register_class(LibraryClearCache)
    bpy.utils.register_class(LibraryPreview)
    bpy.utils.register_class(LibraryRemovePreview)
    bpy.utils.register_class(AddLibraryMaterial)
    bpy.utils.register_class(ApplyLibraryMaterial)
    bpy.utils.register_class(CacheLibraryMaterial)
    bpy.utils.register_class(SaveLibraryMaterial)
    bpy.utils.register_class(AddLibraryGroup)
    bpy.utils.register_class(InsertLibraryGroup)
    bpy.utils.register_class(CacheLibraryGroup)
    bpy.utils.register_class(SaveLibraryGroup)
    bpy.utils.register_class(AddLibraryImage)
    bpy.utils.register_class(InsertLibraryImage)
    bpy.utils.register_class(CacheLibraryImage)
    bpy.utils.register_class(SaveLibraryImage)
    bpy.utils.register_class(AddLibraryScript)
    bpy.utils.register_class(InsertLibraryScript)
    bpy.utils.register_class(CacheLibraryScript)
    bpy.utils.register_class(SaveLibraryScript)
    bpy.utils.register_class(MaterialConvert)
    bpy.utils.register_class(GroupConvert)

def unregister():
    bpy.utils.unregister_class(OnlineMaterialLibraryPanel)
    bpy.utils.unregister_class(LibraryConnect)
    bpy.utils.unregister_class(LibraryInfo)
    bpy.utils.unregister_class(LibrarySettings)
    bpy.utils.unregister_class(LibraryTools)
    bpy.utils.unregister_class(LibraryHome)
    bpy.utils.unregister_class(ViewMaterial)
    bpy.utils.unregister_class(LibraryClearCache)
    bpy.utils.unregister_class(LibraryPreview)
    bpy.utils.unregister_class(LibraryRemovePreview)
    bpy.utils.unregister_class(AddLibraryMaterial)
    bpy.utils.unregister_class(ApplyLibraryMaterial)
    bpy.utils.unregister_class(CacheLibraryMaterial)
    bpy.utils.unregister_class(SaveLibraryMaterial)
    bpy.utils.unregister_class(AddLibraryGroup)
    bpy.utils.unregister_class(InsertLibraryGroup)
    bpy.utils.unregister_class(CacheLibraryGroup)
    bpy.utils.unregister_class(SaveLibraryGroup)
    bpy.utils.unregister_class(AddLibraryImage)
    bpy.utils.unregister_class(InsertLibraryImage)
    bpy.utils.unregister_class(CacheLibraryImage)
    bpy.utils.unregister_class(SaveLibraryImage)
    bpy.utils.unregister_class(AddLibraryScript)
    bpy.utils.unregister_class(InsertLibraryScript)
    bpy.utils.unregister_class(CacheLibraryScript)
    bpy.utils.unregister_class(SaveLibraryScript)
    bpy.utils.unregister_class(MaterialConvert)
    bpy.utils.unregister_class(GroupConvert)

if __name__ == "__main__":
    register()