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
import os
import bpy.utils.previews

bl_info = {
    "name": "Nodes Icons Panel",
    "author": "Reiner 'Tiles' Prokein",
    "version": (0, 9, 1),
    "blender": (2, 76, 0),
    "location": "",
    "description": "Adds a panel with Icon buttons in the Node editor",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"}

# text or icon buttons, the prop
class UITweaksDataNodes(bpy.types.PropertyGroup):
    icon_or_text = bpy.props.BoolProperty(name="Icon / Text Buttons", description="Displays some buttons as text or iconbuttons", default = True) # Our prop

class NodesIconPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "All Nodes"
    bl_idname = "nodes.common_buttons"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "All Nodes"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene
        layout.prop(scene.UItweaksNodes, "icon_or_text")

        ##### Textbuttons

        if not scene.UItweaksNodes.icon_or_text: 

        ##### --------------------------------- Textures ------------------------------------------- ####     
               
            layout.label(text="Texture:")

            col = layout.column(align=True)
            row = col.row(align=True)       
        
            props = row.operator("node.add_node", text=" Image          ", text_ctxt=default_context, icon_value = custom_icons["image"].icon_id)    
            props.use_transform = True
            props.type = "ShaderNodeTexImage"
        
        
            props = row.operator("node.add_node", text=" Environment", text_ctxt=default_context, icon_value = custom_icons["environment"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexEnvironment"

            row = col.row(align=True)          
        
            props = row.operator("node.add_node", text=" Sky              ", text_ctxt=default_context, icon_value = custom_icons["sky"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexSky"
         
            props = row.operator("node.add_node", text=" Noise            ", text_ctxt=default_context, icon_value = custom_icons["noise"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"
        
            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Wave            ", text_ctxt=default_context, icon_value = custom_icons["waves"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexWave"
        
            props = row.operator("node.add_node", text=" Voronoi         ", text_ctxt=default_context, icon_value = custom_icons["voronoi"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"

            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Musgrave      ", text_ctxt=default_context, icon_value = custom_icons["musgrave"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexMusgrave"
         
            props = row.operator("node.add_node", text=" Gradient       ", text_ctxt=default_context, icon_value = custom_icons["gradient"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"

            row = col.row(align=True)
         
            props = row.operator("node.add_node", text=" Magic            ", text_ctxt=default_context, icon_value = custom_icons["magic"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"
        
            props = row.operator("node.add_node", text=" Checker        ", text_ctxt=default_context, icon_value = custom_icons["checker"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"

            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Brick             ", text_ctxt=default_context, icon_value = custom_icons["brick"].icon_id)
            props.use_transform = True 
            props.type = "ShaderNodeTexBrick"
        
            props = row.operator("node.add_node", text=" Point Density", text_ctxt=default_context, icon_value = custom_icons["pointcloud"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexPointDensity"

            ##### --------------------------------- Shader ------------------------------------------- ####
        
            layout.label(text="Shader:")

            col = layout.column(align=True)
            row = col.row(align=True)            
        
            props = row.operator("node.add_node", text=" Add              ", text_ctxt=default_context, icon_value = custom_icons["addshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeAddShader" 

            props = row.operator("node.add_node", text=" Mix            ", text_ctxt=default_context, icon_value = custom_icons["mixshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMixShader"

            row = col.row(align=True)  
        
            props = row.operator("node.add_node", text=" Anisotopic    ", text_ctxt=default_context, icon_value = custom_icons["anisotopicshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfAnisotropic"

            props = row.operator("node.add_node", text=" Ambient Occlusion  ", text_ctxt=default_context, icon_value = custom_icons["ambient_occlusion"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeAmbientOcclusion"

            row = col.row(align=True)   
        
            props = row.operator("node.add_node", text=" Diffuse          ", text_ctxt=default_context, icon_value = custom_icons["diffuseshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfDiffuse"
        
            props = row.operator("node.add_node", text=" Emission        ", text_ctxt=default_context, icon_value = custom_icons["emission"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeEmission"

            row = col.row(align=True)  
        
            props = row.operator("node.add_node", text=" Glas               ", text_ctxt=default_context, icon_value = custom_icons["glasshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLayerWeight"   
         
            props = row.operator("node.add_node", text=" Glossy          ", text_ctxt=default_context, icon_value = custom_icons["glossyshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfGlossy"

            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" Hair               ", text_ctxt=default_context, icon_value = custom_icons["hairshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfHair"       
        
            props = row.operator("node.add_node", text=" Holdout        ", text_ctxt=default_context, icon_value = custom_icons["holdoutshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeHoldout"

            row = col.row(align=True)  
        
            props = row.operator("node.add_node", text=" Refraction     ", text_ctxt=default_context, icon_value = custom_icons["refractionshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfRefraction"
         
            props = row.operator("node.add_node", text=" Subsurface Scattering", text_ctxt=default_context, icon_value = custom_icons["sss_shader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSubsurfaceScattering"

            row = col.row(align=True)    
        
            props = row.operator("node.add_node", text=" Toon              ", text_ctxt=default_context, icon_value = custom_icons["toonshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfToon"
        
            props = row.operator("node.add_node", text=" Translucent      ", text_ctxt=default_context, icon_value = custom_icons["translucentshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfTranslucent"

            row = col.row(align=True)  
        
            props = row.operator("node.add_node", text=" Transparent    ", text_ctxt=default_context, icon_value = custom_icons["transparentshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfTransparent"

            props = row.operator("node.add_node", text=" Velvet            ", text_ctxt=default_context, icon_value = custom_icons["velvetshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfVelvet"

            row = col.row(align=True)  
         
            props = row.operator("node.add_node", text=" Volume Absorption ", text_ctxt=default_context, icon_value = custom_icons["volumeabsorptionshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVolumeAbsorption"
        
            props = row.operator("node.add_node", text=" Volume Scatter    ", text_ctxt=default_context, icon_value = custom_icons["volumescatter"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVolumeScatter"

            ##### --------------------------------- Color ------------------------------------------- ####
        
            layout.label(text="Color:")

            col = layout.column(align=True)
            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" Bright / Contrast    ", text_ctxt=default_context, icon_value = custom_icons["brightcontrast"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBrightContrast"       
        
            props = row.operator("node.add_node", text=" Gamma         ", text_ctxt=default_context, icon_value = custom_icons["gamma"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeGamma"

            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text="Hue / Saturation    ", text_ctxt=default_context, icon_value = custom_icons["huesaturation"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeHueSaturation"
        
            props = row.operator("node.add_node", text=" Invert              ", text_ctxt=default_context, icon_value = custom_icons["invert"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeInvert"
        
            row = col.row(align=True) 

            props = row.operator("node.add_node", text=" Light Falloff           ", text_ctxt=default_context, icon_value = custom_icons["lightfalloff"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLightFalloff"
        
            props = row.operator("node.add_node", text=" Mix RGB           ", text_ctxt=default_context, icon_value = custom_icons["mixrgb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMixRGB"

            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text="RGB Curves       ", text_ctxt=default_context, icon_value = custom_icons["rgbcurve"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeRGBCurve"

            ##### --------------------------------- Vector ------------------------------------------- ####
        
            layout.label(text="Vector:")

            col = layout.column(align=True)
            row = col.row(align=True)         
        
            props = row.operator("node.add_node", text=" Bump            ", text_ctxt=default_context, icon_value = custom_icons["bump"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBump"
        
        
            props = row.operator("node.add_node", text=" Mapping          ", text_ctxt=default_context, icon_value = custom_icons["mapping"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMapping"

            row = col.row(align=True) 

            props = row.operator("node.add_node", text=" Normal          ", text_ctxt=default_context, icon_value = custom_icons["normal"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeNormal"
        
            props = row.operator("node.add_node", text=" Normal Map     ", text_ctxt=default_context, icon_value = custom_icons["normalmap"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeNormalMap"
        
            row = col.row(align=True)  
        
            props = row.operator("node.add_node", text=" Vector Transform   ", text_ctxt=default_context, icon_value = custom_icons["vector_transform"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVectorTransform"
        
            props = row.operator("node.add_node", text=" Vector Curves    ", text_ctxt=default_context, icon_value = custom_icons["vector"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"

            ##### --------------------------------- Input ------------------------------------------- ####
        
            layout.label(text="Input:")

            col = layout.column(align=True)
            row = col.row(align=True)        
        
            props = row.operator("node.add_node", text=" Attribute     ", text_ctxt=default_context, icon_value = custom_icons["attribute"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeAttribute"
        
        
            props = row.operator("node.add_node", text=" Camera Data   ", text_ctxt=default_context, icon_value = custom_icons["cameradata"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCameraData"

            row = col.row(align=True)
    
            props = row.operator("node.add_node", text=" Fresnel        ", text_ctxt=default_context, icon_value = custom_icons["fresnel"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeFresnel"
        
            props = row.operator("node.add_node", text=" Geometry        ", text_ctxt=default_context, icon_value = custom_icons["geometry"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeNewGeometry"
        
            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Hair Info     ", text_ctxt=default_context, icon_value = custom_icons["hairinfo"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeHairInfo"
        
            props = row.operator("node.add_node", text=" Layer Weight   ", text_ctxt=default_context, icon_value = custom_icons["layerweight"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLayerWeight"

            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Light Path    ", text_ctxt=default_context, icon_value = custom_icons["lightpath"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLightPath"
        
            props = row.operator("node.add_node", text=" Object Info    ", text_ctxt=default_context, icon_value = custom_icons["objectinfo"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeObjectInfo"
        
            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" Particle Info", text_ctxt=default_context, icon_value = custom_icons["particleinfo"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeParticleInfo"
        
            props = row.operator("node.add_node", text=" RGB               ", text_ctxt=default_context, icon_value = custom_icons["rgb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeRGB"

            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Tangent        ", text_ctxt=default_context, icon_value = custom_icons["tangent"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTangent"
        
            props = row.operator("node.add_node", text=" Texture Coordinate", text_ctxt=default_context, icon_value = custom_icons["texcoordinate"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexCoord"

            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" UV Map       ", text_ctxt=default_context, icon_value = custom_icons["uvmap"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeUVMap"
        
            props = row.operator("node.add_node", text=" Value            ", text_ctxt=default_context, icon_value = custom_icons["value"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeValue"

            row = col.row(align=True)
        
            props = row.operator("node.add_node", text=" Wireframe", text_ctxt=default_context, icon_value = custom_icons["wireframe"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeWireframe"

            ##### --------------------------------- Output ------------------------------------------- ####
        
            layout.label(text="Output:")

            col = layout.column(align=True)
            row = col.row(align=True)        
        
            props = row.operator("node.add_node", text=" Material Output", text_ctxt=default_context, icon_value = custom_icons["material_output"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeOutputMaterial"
        
        
            props = row.operator("node.add_node", text=" Lamp Output", text_ctxt=default_context, icon_value = custom_icons["lamp_output"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeOutputLamp"

            ##### --------------------------------- Converter ------------------------------------------- ####
        
            layout.label(text="Converter:")

            col = layout.column(align=True)
            row = col.row(align=True)           
        
            props = row.operator("node.add_node", text=" Blackbody        ", text_ctxt=default_context, icon_value = custom_icons["blackbody"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBlackbody"        
        
            props = row.operator("node.add_node", text=" ColorRamp      ", text_ctxt=default_context, icon_value = custom_icons["colorramp"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeValToRGB"

            row = col.row(align=True) 

            props = row.operator("node.add_node", text=" Combine HSV    ", text_ctxt=default_context, icon_value = custom_icons["combinehsv"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCombineHSV"        
         
            props = row.operator("node.add_node", text=" Combine RGB   ", text_ctxt=default_context, icon_value = custom_icons["combinergb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCombineRGB"

            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" Combine XYZ    ", text_ctxt=default_context, icon_value = custom_icons["combinexyz"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCombineXYZ" 
        
            props = row.operator("node.add_node", text=" Math              ", text_ctxt=default_context, icon_value = custom_icons["math"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMath"

            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" RGB to BW        ", text_ctxt=default_context, icon_value = custom_icons["rgbtobw"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeRGBToBW"
        
            props = row.operator("node.add_node", text=" Separate HSV    ", text_ctxt=default_context, icon_value = custom_icons["separatehsv"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSeparateHSV"

            row = col.row(align=True)   
        
            props = row.operator("node.add_node", text=" Separate RGB    ", text_ctxt=default_context, icon_value = custom_icons["separatergb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSeparateRGB"      
        
            props = row.operator("node.add_node", text=" Separate XYZ    ", text_ctxt=default_context, icon_value = custom_icons["separatexyz"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSeparateXYZ" 
            
            row = col.row(align=True)       
        
            props = row.operator("node.add_node", text=" Vector Math       ", text_ctxt=default_context, icon_value = custom_icons["vectormath"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVectorMath"
        
            props = row.operator("node.add_node", text=" Wavelength      ", text_ctxt=default_context, icon_value = custom_icons["wavelength"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeWavelength"

        ##### --------------------------------- Script ------------------------------------------- ####
        
            layout.label(text="Script:")

            col = layout.column(align=True)
            row = col.row(align=True) 
        
            props = row.operator("node.add_node", text=" Script            ", text_ctxt=default_context, icon_value = custom_icons["script"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeScript"  

        ##### --------------------------------- Converter ------------------------------------------- ####
        
            layout.label(text="Group:")

            col = layout.column(align=True)
            row = col.row(align=True)       

            row.operator("node.group_edit", text=" Edit Group     ", icon_value = custom_icons["editgroup"].icon_id).exit = False
            row.operator("node.group_edit", text = "Exit Edit Group  ", icon_value = custom_icons["exiteditgroup"].icon_id).exit = True

            row = col.row(align=True)  

            row.operator("node.group_insert", text = " Group Insert    ", icon_value = custom_icons["groupinsert"].icon_id)
            row.operator("node.group_make", text = " Make Group     ", icon_value = custom_icons["makegroup"].icon_id)

            row = col.row(align=True)  

            row.operator("node.group_ungroup", text = " Ungroup        ", icon_value = custom_icons["ungroup"].icon_id)

        ##### --------------------------------- Layout ------------------------------------------- ####
        
            layout.label(text="Layout:")

            col = layout.column(align=True)
            row = col.row(align=True)         

            props = row.operator("node.add_node", text=" Frame       ", text_ctxt=default_context, icon_value = custom_icons["frame"].icon_id)
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text=" Reroute      ", text_ctxt=default_context, icon_value = custom_icons["reroute"].icon_id)
            props.use_transform = True
            props.type = "NodeReroute"


        ##### Icon Buttons 

        else: 

        ##### --------------------------------- Textures ------------------------------------------- ####
         
            layout.label(text="Texture:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["image"].icon_id)
        
            props.use_transform = True
            props.type = "ShaderNodeTexImage"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["environment"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexEnvironment"
   
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["sky"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexSky"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["noise"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"
        
            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["waves"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexWave"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["voronoi"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["musgrave"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexMusgrave"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["gradient"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"
        
            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["magic"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["checker"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["brick"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexBrick"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["pointcloud"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexPointDensity"

            ##### --------------------------------- Shader ------------------------------------------- ####
        
            layout.label(text="Shader:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["addshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeAddShader"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["mixshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMixShader"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["anisotopicshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfAnisotropic"
  
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["ambient_occlusion"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeAmbientOcclusion"

            row = layout.row()
            row.alignment = 'LEFT' 
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["diffuseshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfDiffuse"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["emission"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeEmission"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["glasshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLayerWeight"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["glossyshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfGlossy"

            row = layout.row()
            row.alignment = 'LEFT' 
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["hairshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfHair"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["holdoutshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeHoldout"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["refractionshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfRefraction"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["sss_shader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSubsurfaceScattering"

            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["toonshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfToon"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["translucentshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfTranslucent"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["transparentshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfTransparent"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["velvetshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBsdfVelvet"

            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["volumeabsorptionshader"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVolumeAbsorption"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["volumescatter"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVolumeScatter"

            ##### --------------------------------- Color ------------------------------------------- ####
        
            layout.label(text="Color:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["brightcontrast"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBrightContrast"
        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["gamma"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeGamma"
 
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["huesaturation"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeHueSaturation"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["invert"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeInvert"
        
            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["lightfalloff"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLightFalloff"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["mixrgb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMixRGB"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["rgbcurve"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeRGBCurve"

            ##### --------------------------------- Vector ------------------------------------------- ####
        
            layout.label(text="Vector:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["bump"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBump"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["mapping"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMapping"
     
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["normal"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeNormal"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["normalmap"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeNormalMap"
        
            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["vector_transform"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVectorTransform"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["vector"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"

            ##### --------------------------------- Input ------------------------------------------- ####
        
            layout.label(text="Input:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["attribute"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeAttribute"
   
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["cameradata"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCameraData"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["fresnel"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeFresnel"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["geometry"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeNewGeometry"
        
            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["hairinfo"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeHairInfo"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["layerweight"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLayerWeight"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["lightpath"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeLightPath"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["objectinfo"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeObjectInfo"
        
            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["particleinfo"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeParticleInfo"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["rgb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeRGB"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["tangent"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTangent"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["texcoordinate"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeTexCoord"

            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["uvmap"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeUVMap"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["value"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeValue"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["wireframe"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeWireframe"

            ##### --------------------------------- Output ------------------------------------------- ####
        
            layout.label(text="Output:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["material_output"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeOutputMaterial"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["lamp_output"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeOutputLamp"


            ##### --------------------------------- Converter ------------------------------------------- ####
        
            layout.label(text="Converter:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["blackbody"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeBlackbody"        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["colorramp"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeValToRGB"

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["combinehsv"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCombineHSV"        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["combinergb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCombineRGB"

            row = layout.row()
            row.alignment = 'LEFT'
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["combinexyz"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeCombineXYZ" 
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["math"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeMath"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["rgbtobw"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeRGBToBW"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["separatehsv"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSeparateHSV"

            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["separatergb"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSeparateRGB"      
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["separatexyz"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeSeparateXYZ"       
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["vectormath"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeVectorMath"
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["wavelength"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeWavelength"

        ##### --------------------------------- Script ------------------------------------------- ####
        
            layout.label(text="Script:")

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["script"].icon_id)
            props.use_transform = True
            props.type = "ShaderNodeScript"  

        ##### --------------------------------- Converter ------------------------------------------- ####
        
            layout.label(text="Group:")

            row = layout.row()
            row.alignment = 'LEFT'        

            row.operator("node.group_edit", text="", icon_value = custom_icons["editgroup"].icon_id).exit = False
            row.operator("node.group_edit", text = "", icon_value = custom_icons["exiteditgroup"].icon_id).exit = True
            row.operator("node.group_insert", text = "", icon_value = custom_icons["groupinsert"].icon_id)
            row.operator("node.group_make", text = "", icon_value = custom_icons["makegroup"].icon_id)

            row = layout.row()
            row.alignment = 'LEFT'

            row.operator("node.group_ungroup", text = "", icon_value = custom_icons["ungroup"].icon_id)

        ##### --------------------------------- Layout ------------------------------------------- ####
        
            layout.label(text="Layout:")

            row = layout.row()
            row.alignment = 'LEFT'        

            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["frame"].icon_id)
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text="", text_ctxt=default_context, icon_value = custom_icons["reroute"].icon_id)
            props.use_transform = True
            props.type = "NodeReroute"

 # -----------------------------------------------------------   
    
# global variable to store icons in
custom_icons = None

def register():
    
    bpy.utils.register_class(NodesIconPanel)
     
    # Our external Icons
    global custom_icons

    custom_icons = bpy.utils.previews.new()

    # Use this for addons
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    # Use this for testing the script in the scripting layout
    #script_path = bpy.context.space_data.text.filepath
    #icons_dir = os.path.join(os.path.dirname(script_path), "icons")

    # Textures

    custom_icons.load("brick", os.path.join(icons_dir, "brick.png"), 'IMAGE')
    custom_icons.load("checker", os.path.join(icons_dir, "checker.png"), 'IMAGE')
    custom_icons.load("environment", os.path.join(icons_dir, "environment.png"), 'IMAGE')
    custom_icons.load("gradient", os.path.join(icons_dir, "gradient.png"), 'IMAGE')
    custom_icons.load("image", os.path.join(icons_dir, "image.png"), 'IMAGE')
    custom_icons.load("magic", os.path.join(icons_dir, "magic.png"), 'IMAGE')
    custom_icons.load("musgrave", os.path.join(icons_dir, "musgrave.png"), 'IMAGE')
    custom_icons.load("noise", os.path.join(icons_dir, "noise.png"), 'IMAGE')
    custom_icons.load("pointcloud", os.path.join(icons_dir, "pointcloud.png"), 'IMAGE')
    custom_icons.load("sky", os.path.join(icons_dir, "sky.png"), 'IMAGE')
    custom_icons.load("voronoi", os.path.join(icons_dir, "voronoi.png"), 'IMAGE')
    custom_icons.load("waves", os.path.join(icons_dir, "waves.png"), 'IMAGE')

    # Input

    custom_icons.load("attribute", os.path.join(icons_dir, "attribute.png"), 'IMAGE')
    custom_icons.load("cameradata", os.path.join(icons_dir, "cameradata.png"), 'IMAGE')
    custom_icons.load("fresnel", os.path.join(icons_dir, "fresnel.png"), 'IMAGE')
    custom_icons.load("geometry", os.path.join(icons_dir, "geometry.png"), 'IMAGE')
    custom_icons.load("hairinfo", os.path.join(icons_dir, "hairinfo.png"), 'IMAGE')
    custom_icons.load("layerweight", os.path.join(icons_dir, "layerweight.png"), 'IMAGE')
    custom_icons.load("lightpath", os.path.join(icons_dir, "lightpath.png"), 'IMAGE')
    custom_icons.load("objectinfo", os.path.join(icons_dir, "objectinfo.png"), 'IMAGE')
    custom_icons.load("particleinfo", os.path.join(icons_dir, "particleinfo.png"), 'IMAGE')
    custom_icons.load("rgb", os.path.join(icons_dir, "rgb.png"), 'IMAGE')
    custom_icons.load("tangent", os.path.join(icons_dir, "tangent.png"), 'IMAGE')
    custom_icons.load("texcoordinate", os.path.join(icons_dir, "texcoordinate.png"), 'IMAGE')
    custom_icons.load("uvmap", os.path.join(icons_dir, "uvmap.png"), 'IMAGE')
    custom_icons.load("value", os.path.join(icons_dir, "value.png"), 'IMAGE')
    custom_icons.load("wireframe", os.path.join(icons_dir, "wireframe.png"), 'IMAGE')

    # Output

    custom_icons.load("material_output", os.path.join(icons_dir, "material_output.png"), 'IMAGE')
    custom_icons.load("lamp_output", os.path.join(icons_dir, "lamp_output.png"), 'IMAGE')

    # Shaders

    custom_icons.load("addshader", os.path.join(icons_dir, "addshader.png"), 'IMAGE')
    custom_icons.load("anisotopicshader", os.path.join(icons_dir, "anisotopicshader.png"), 'IMAGE')
    custom_icons.load("ambient_occlusion", os.path.join(icons_dir, "ambient_occlusion.png"), 'IMAGE')
    custom_icons.load("diffuseshader", os.path.join(icons_dir, "diffuseshader.png"), 'IMAGE')
    custom_icons.load("emission", os.path.join(icons_dir, "emission.png"), 'IMAGE')
    custom_icons.load("glasshader", os.path.join(icons_dir, "glasshader.png"), 'IMAGE')
    custom_icons.load("glossyshader", os.path.join(icons_dir, "glossyshader.png"), 'IMAGE')
    custom_icons.load("hairshader", os.path.join(icons_dir, "hairshader.png"), 'IMAGE')
    custom_icons.load("holdoutshader", os.path.join(icons_dir, "holdoutshader.png"), 'IMAGE')
    custom_icons.load("mixshader", os.path.join(icons_dir, "mixshader.png"), 'IMAGE')
    custom_icons.load("refractionshader", os.path.join(icons_dir, "refractionshader.png"), 'IMAGE')
    custom_icons.load("sss_shader", os.path.join(icons_dir, "sss_shader.png"), 'IMAGE')
    custom_icons.load("toonshader", os.path.join(icons_dir, "toonshader.png"), 'IMAGE')
    custom_icons.load("translucentshader", os.path.join(icons_dir, "translucentshader.png"), 'IMAGE')
    custom_icons.load("transparentshader", os.path.join(icons_dir, "transparentshader.png"), 'IMAGE')
    custom_icons.load("velvetshader", os.path.join(icons_dir, "velvetshader.png"), 'IMAGE')
    custom_icons.load("volumeabsorptionshader", os.path.join(icons_dir, "volumeabsorptionshader.png"), 'IMAGE')
    custom_icons.load("volumescatter", os.path.join(icons_dir, "volumescatter.png"), 'IMAGE')

    # Color

    custom_icons.load("brightcontrast", os.path.join(icons_dir, "brightcontrast.png"), 'IMAGE')
    custom_icons.load("gamma", os.path.join(icons_dir, "gamma.png"), 'IMAGE')
    custom_icons.load("huesaturation", os.path.join(icons_dir, "huesaturation.png"), 'IMAGE')
    custom_icons.load("invert", os.path.join(icons_dir, "invert.png"), 'IMAGE')
    custom_icons.load("lightfalloff", os.path.join(icons_dir, "lightfalloff.png"), 'IMAGE')
    custom_icons.load("mixrgb", os.path.join(icons_dir, "mixrgb.png"), 'IMAGE')
    custom_icons.load("rgbcurve", os.path.join(icons_dir, "rgbcurve.png"), 'IMAGE')

    # Vector

    custom_icons.load("bump", os.path.join(icons_dir, "bump.png"), 'IMAGE')
    custom_icons.load("mapping", os.path.join(icons_dir, "mapping.png"), 'IMAGE')
    custom_icons.load("normal", os.path.join(icons_dir, "normal.png"), 'IMAGE')
    custom_icons.load("normalmap", os.path.join(icons_dir, "normalmap.png"), 'IMAGE')
    custom_icons.load("vector_transform", os.path.join(icons_dir, "vector_transform.png"), 'IMAGE')
    custom_icons.load("vector", os.path.join(icons_dir, "vector.png"), 'IMAGE')

    # Converter

    custom_icons.load("blackbody", os.path.join(icons_dir, "blackbody.png"), 'IMAGE')
    custom_icons.load("colorramp", os.path.join(icons_dir, "colorramp.png"), 'IMAGE')
    custom_icons.load("combinehsv", os.path.join(icons_dir, "combinehsv.png"), 'IMAGE')
    custom_icons.load("combinergb", os.path.join(icons_dir, "combinergb.png"), 'IMAGE')   
    custom_icons.load("combinexyz", os.path.join(icons_dir, "combinexyz.png"), 'IMAGE')
    custom_icons.load("math", os.path.join(icons_dir, "math.png"), 'IMAGE')
    custom_icons.load("rgbtobw", os.path.join(icons_dir, "rgbtobw.png"), 'IMAGE')
    custom_icons.load("separatehsv", os.path.join(icons_dir, "separatehsv.png"), 'IMAGE')
    custom_icons.load("separatergb", os.path.join(icons_dir, "separatergb.png"), 'IMAGE')
    custom_icons.load("separatexyz", os.path.join(icons_dir, "separatexyz.png"), 'IMAGE')   
    custom_icons.load("vectormath", os.path.join(icons_dir, "vectormath.png"), 'IMAGE')
    custom_icons.load("wavelength", os.path.join(icons_dir, "wavelength.png"), 'IMAGE')

    # Converter

    custom_icons.load("script", os.path.join(icons_dir, "script.png"), 'IMAGE')

    # Group

    custom_icons.load("editgroup", os.path.join(icons_dir, "editgroup.png"), 'IMAGE')
    custom_icons.load("exiteditgroup", os.path.join(icons_dir, "exiteditgroup.png"), 'IMAGE')
    custom_icons.load("groupinsert", os.path.join(icons_dir, "groupinsert.png"), 'IMAGE')
    custom_icons.load("makegroup", os.path.join(icons_dir, "makegroup.png"), 'IMAGE')
    custom_icons.load("ungroup", os.path.join(icons_dir, "ungroup.png"), 'IMAGE')   

    # Layout

    custom_icons.load("frame", os.path.join(icons_dir, "frame.png"), 'IMAGE')
    custom_icons.load("reroute", os.path.join(icons_dir, "reroute.png"), 'IMAGE')

    # Our data block for icon or text buttons
    bpy.utils.register_class(UITweaksDataNodes) # Our data block
    bpy.types.Scene.UItweaksNodes = bpy.props.PointerProperty(type=UITweaksDataNodes) # Bind reference of type of our data block to type Scene objects
    
    
    
def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
    bpy.utils.unregister_class(NodesIconPanel)
    bpy.utils.unregister_class(UITweaksDataNodes)
     
# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.

if __name__ == "__main__":
    register()