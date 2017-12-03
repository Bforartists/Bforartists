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

# This script installs three new tabs in the Tool Shelf in the Node Editor.
# It contains all the add nodes. But better arranged and with icons.
# And it installs a panel in the Properties sidebar.
# Here you can adjust if you want to display the buttons as text buttons with icons.
# Or as pure icon buttons.

# Note that this version is not compatible with Blender. It relies at icons in the Bfoartists iconsheet which doesn't exist in Blender.


import bpy
import os
import bpy.utils.previews

from bpy import context

bl_info = {
    "name": "Nodes Icons Panel",
    "author": "Reiner 'Tiles' Prokein",
    "version": (0, 9, 7),
    "blender": (2, 79, 0),
    "location": "Node Editor -> Tool Shelf + Properties Sidebar",
    "description": "DO NOT TURN OFF! - Adds panels with Icon buttons in the Node editor",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"}

# text or icon buttons, the prop
class UITweaksDataNodes(bpy.types.PropertyGroup):
    icon_or_text = bpy.props.BoolProperty(name="Icon / Text Buttons", description="Display the buttons in the Node editor tool shelf as text or iconbuttons\nTo make the change permanent save the startup file\nBeware of the layout, this is also saved with the startup file!", default = False) # Our prop

# The text or icon prop is in the properties sidebar
class NodesIconsPanelProp(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene
        layout.prop(scene.UItweaksNodes, "icon_or_text")

#Input nodes tab, Input common panel
class NodesIconsPanelInput(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input Common"
    bl_idname = "nodes.nip_input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Inputnodes"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

#--------------------------------------------------------------------- Shader Node Tree --------------------------------------------------------------------------------

        if context.space_data.tree_type == 'ShaderNodeTree':

            ##### Textbuttons

            if not scene.UItweaksNodes.icon_or_text: 

            ##### --------------------------------- Textures ------------------------------------------- ####     
               
                layout.label(text="Texture:")

                col = layout.column(align=True)
                row = col.row(align=True)       
        
                props = row.operator("node.add_node", text=" Image          ", icon = "NODE_IMAGE")    
                props.use_transform = True
                props.type = "ShaderNodeTexImage"
        
        
                props = row.operator("node.add_node", text=" Environment", icon = "NODE_ENVIRONMENT")
                props.use_transform = True
                props.type = "ShaderNodeTexEnvironment"

                row = col.row(align=True)          
        
                props = row.operator("node.add_node", text=" Sky              ", icon = "NODE_SKY")
                props.use_transform = True
                props.type = "ShaderNodeTexSky"
         
                props = row.operator("node.add_node", text=" Noise            ", icon = "NODE_NOISE")
                props.use_transform = True
                props.type = "ShaderNodeTexNoise"
       

                ##### --------------------------------- Connect ------------------------------------------- ####
        
                layout.label(text="Connect:")

                col = layout.column(align=True)
                row = col.row(align=True)            
        
                props = row.operator("node.add_node", text=" Add              ", icon = "NODE_ADD_SHADER")
                props.use_transform = True
                props.type = "ShaderNodeAddShader" 

                props = row.operator("node.add_node", text=" Mix            ", icon = "NODE_MIXSHADER")
                props.use_transform = True
                props.type = "ShaderNodeMixShader"

                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Normal Map     ", icon = "NODE_NORMALMAP")
                props.use_transform = True
                props.type = "ShaderNodeNormalMap"

                 ##### --------------------------------- Shader ------------------------------------------- ####

                if context.space_data.shader_type == 'OBJECT':

                    layout.label(text="Shader:")

                    col = layout.column(align=True)
                    row = col.row(align=True)
                    
                    props = row.operator("node.add_node", text=" Principled        ", icon = "NODE_PRINCIPLED")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfPrincipled"

                    col = layout.column(align=True)
                    row = col.row(align=True)     
        
                    props = row.operator("node.add_node", text=" Diffuse          ", icon = "NODE_DIFFUSESHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfDiffuse"
        
                    props = row.operator("node.add_node", text=" Emission        ", icon = "NODE_EMISSION")
                    props.use_transform = True
                    props.type = "ShaderNodeEmission"

                    row = col.row(align=True)  

                    props = row.operator("node.add_node", text=" Fresnel        ", icon = "NODE_FRESNEL")
                    props.use_transform = True
                    props.type = "ShaderNodeFresnel"
        
                    props = row.operator("node.add_node", text=" Glass               ", icon = "NODE_GLASSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlass"   

                    col = layout.column(align=True)
                    row = col.row(align=True)  
         
                    props = row.operator("node.add_node", text=" Glossy          ", icon = "NODE_GLOSSYSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlossy"
        
                    props = row.operator("node.add_node", text=" Refraction     ", icon = "NODE_REFRACTIONSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfRefraction"

                    row = col.row(align=True)  
         
                    props = row.operator("node.add_node", text=" Subsurface Scattering", icon = "NODE_SSS")
                    props.use_transform = True
                    props.type = "ShaderNodeSubsurfaceScattering"
        
                    props = row.operator("node.add_node", text=" Toon              ", icon = "NODE_TOONSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfToon"

                    col = layout.column(align=True)
                    row = col.row(align=True)  
        
                    props = row.operator("node.add_node", text=" Translucent      ", icon = "NODE_TRANSLUCENT")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTranslucent"

                    props = row.operator("node.add_node", text=" Transparent    ", icon = "NODE_TRANSPARENT")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTransparent"

                    row = col.row(align=True)  

                    props = row.operator("node.add_node", text=" Velvet            ", icon = "NODE_VELVET")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfVelvet"

                elif context.space_data.shader_type == 'WORLD':

                    layout.label(text="Shader:")

                    col = layout.column(align=True)
                    row = col.row(align=True)       

                    props = row.operator("node.add_node", text=" Background            ", icon = "NODE_BACKGROUNDSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBackground"

                ##### --------------------------------- Output ------------------------------------------- ####

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)
                
                if context.space_data.shader_type == 'OBJECT':
        
                    props = row.operator("node.add_node", text=" Material Output", icon = "NODE_MATERIALOUTPUT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputMaterial"
        
        
                    props = row.operator("node.add_node", text=" Lamp Output", icon = "NODE_LAMP")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLamp"

                elif context.space_data.shader_type == 'WORLD':
        
                    props = row.operator("node.add_node", text=" World Output", icon = "NODE_WORLDOUTPUT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputWorld"

                elif context.space_data.shader_type == 'LINESTYLE':
        
                    props = row.operator("node.add_node", text=" Line Style Output", icon = "NODE_LINESTYLE_OUTPUT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLineStyle"

            #### Icon Buttons

            else:
          
                ##### --------------------------------- Textures ------------------------------------------- ####
         
                layout.label(text="Texture:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_IMAGE")  
        
                props.use_transform = True
                props.type = "ShaderNodeTexImage"

                props = row.operator("node.add_node", text = "", icon = "NODE_ENVIRONMENT")
                props.use_transform = True
                props.type = "ShaderNodeTexEnvironment"
   
                props = row.operator("node.add_node", text = "", icon = "NODE_SKY")
                props.use_transform = True
                props.type = "ShaderNodeTexSky"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_NOISE")
                props.use_transform = True
                props.type = "ShaderNodeTexNoise"


                ##### --------------------------------- Connect ------------------------------------------- ####
        
                layout.label(text="Connect:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_ADD_SHADER")
                props.use_transform = True
                props.type = "ShaderNodeAddShader"

                props = row.operator("node.add_node", text = "", icon = "NODE_MIXSHADER")
                props.use_transform = True
                props.type = "ShaderNodeMixShader"

                props = row.operator("node.add_node", text = "", icon = "NODE_NORMALMAP")
                props.use_transform = True
                props.type = "ShaderNodeNormalMap"

                ##### --------------------------------- Shader ------------------------------------------- ####

                if context.space_data.shader_type == 'OBJECT':

                    layout.label(text="Shader:")

                    row = layout.row()
                    row.alignment = 'LEFT' 

                    props = row.operator("node.add_node", text="", icon = "NODE_PRINCIPLED")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfPrincipled"

                    row = layout.row()
                    row.alignment = 'LEFT' 
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_DIFFUSESHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfDiffuse"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_EMISSION")
                    props.use_transform = True
                    props.type = "ShaderNodeEmission"

                    props = row.operator("node.add_node", text = "", icon = "NODE_FRESNEL")
                    props.use_transform = True
                    props.type = "ShaderNodeFresnel"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_GLASSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlass"

                    row = layout.row()
                    row.alignment = 'LEFT' 

                    props = row.operator("node.add_node", text = "", icon = "NODE_GLOSSYSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlossy"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_REFRACTIONSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfRefraction"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_SSS")
                    props.use_transform = True
                    props.type = "ShaderNodeSubsurfaceScattering"

                    props = row.operator("node.add_node", text = "", icon = "NODE_TOONSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfToon"
        
                    row = layout.row()
                    row.alignment = 'LEFT'  
                    
                    props = row.operator("node.add_node", text = "", icon = "NODE_TRANSLUCENT")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTranslucent"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_TRANSPARENT")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTransparent"

                    props = row.operator("node.add_node", text = "", icon = "NODE_VELVET")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfVelvet"

                elif context.space_data.shader_type == 'WORLD':

                    layout.label(text="Shader:")

                    row = layout.row()
                    row.alignment = 'LEFT' 

                    props = row.operator("node.add_node", text = "", icon = "NODE_BACKGROUNDSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBackground"

                ##### --------------------------------- Output ------------------------------------------- ####
        
                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT'        

                if context.space_data.shader_type == 'OBJECT':
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_MATERIALOUTPUT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputMaterial"

                    props = row.operator("node.add_node", text = "", icon = "NODE_LAMP")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLamp"

                elif context.space_data.shader_type == 'WORLD':
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_WORLDOUTPUT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputWorld"

                elif context.space_data.shader_type == 'LINESTYLE':
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_LINESTYLE_OUTPUT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLineStyle"

#--------------------------------------------------------------------- Compositing Node Tree --------------------------------------------------------------------------------
        elif context.space_data.tree_type == 'CompositorNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                # ------------------------------- Input -----------------------------

                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Image          ", icon = "NODE_IMAGE")  
                props.use_transform = True
                props.type = "CompositorNodeImage"

                props = row.operator("node.add_node", text=" Texture          ", icon = "NODE_TEXTURE")
                props.use_transform = True
                props.type = "CompositorNodeTexture"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Mask         ", icon = "NODE_MASK") 
                props.use_transform = True
                props.type = "CompositorNodeMask"
            
                props = row.operator("node.add_node", text=" Movie Clip         ", icon = "NODE_MOVIE")
                props.use_transform = True
                props.type = "CompositorNodeMovieClip"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Render Layers         ", icon = "NODE_RENDERLAYER")
                props.use_transform = True
                props.type = "CompositorNodeRLayers"
            
                props = row.operator("node.add_node", text=" RGB        ", icon = "NODE_RGB")
                props.use_transform = True
                props.type = "CompositorNodeRGB"
                          
        
                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Alpha Over          ", icon = "NODE_ALPHA")
                props.use_transform = True
                props.type = "CompositorNodeAlphaOver"

                props = row.operator("node.add_node", text=" Bright / Contrast        ", icon = "NODE_BRIGHT_CONTRAST")
                props.use_transform = True
                props.type = "CompositorNodeBrightContrast"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Color Balance         ", icon = "NODE_COLORBALANCE")
                props.use_transform = True
                props.type = "CompositorNodeColorBalance"

                props = row.operator("node.add_node", text=" Hue Saturation Value        ", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "CompositorNodeHueSat"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" RGB Curves         ", icon = "NODE_RGBCURVE")
                props.use_transform = True
                props.type = "CompositorNodeCurveRGB"
        
                props = row.operator("node.add_node", text=" Z Combine         ", icon = "NODE_ZCOMBINE")
                props.use_transform = True
                props.type = "CompositorNodeZcombine"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)   

         
                props = row.operator("node.add_node", text=" Composite          ", icon = "NODE_COMPOSITE_OUTPUT")
                props.use_transform = True
                props.type = "CompositorNodeComposite"
            
                props = row.operator("node.add_node", text=" Viewer          ", icon = "NODE_VIEWER")
                props.use_transform = True
                props.type = "CompositorNodeViewer"

            #### Image Buttons

            else: 

                # ------------------------------- Input -----------------------------

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text = "", icon = "NODE_IMAGE")  
                props.use_transform = True
                props.type = "CompositorNodeImage"

                props = row.operator("node.add_node", text = "", icon = "NODE_TEXTURE")
                props.use_transform = True
                props.type = "CompositorNodeTexture"

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text = "", icon = "NODE_MASK") 
                props.use_transform = True
                props.type = "CompositorNodeMask"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_MOVIE")
                props.use_transform = True
                props.type = "CompositorNodeMovieClip"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_RENDERLAYER") 
                props.use_transform = True
                props.type = "CompositorNodeRLayers"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_RGB")
                props.use_transform = True
                props.type = "CompositorNodeRGB"

                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_ALPHA") 
                props.use_transform = True
                props.type = "CompositorNodeAlphaOver"

                props = row.operator("node.add_node", text = "", icon = "NODE_BRIGHT_CONTRAST")
                props.use_transform = True
                props.type = "CompositorNodeBrightContrast"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_COLORBALANCE")
                props.use_transform = True
                props.type = "CompositorNodeColorBalance"

                props = row.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "CompositorNodeHueSat"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_RGBCURVE")
                props.use_transform = True
                props.type = "CompositorNodeCurveRGB"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_ZCOMBINE")
                props.use_transform = True
                props.type = "CompositorNodeZcombine"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_COMPOSITE_OUTPUT")
                props.use_transform = True
                props.type = "CompositorNodeComposite"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_VIEWER")
                props.use_transform = True
                props.type = "CompositorNodeViewer"

#--------------------------------------------------------------------- Texture Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'TextureNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Image          ", icon = "NODE_IMAGE")  
                props.use_transform = True
                props.type = "TextureNodeImage"

                props = row.operator("node.add_node", text=" Texture          ", icon = "NODE_TEXTURE")
                props.use_transform = True
                props.type = "TextureNodeTexture"

                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" RGB Curves          ", icon = "NODE_RGBCURVE")
                props.use_transform = True
                props.type = "TextureNodeCurveRGB"

                props = row.operator("node.add_node", text=" Hue / Saturation         ", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "TextureNodeHueSaturation"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Invert         ", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "TextureNodeInvert"

                props = row.operator("node.add_node", text=" Mix RGB          ", icon = "NODE_MIXRGB") 
                props.use_transform = True
                props.type = "TextureNodeMixRGB"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Combine RGBA         ", icon = "NODE_COMBINERGB")
                props.use_transform = True
                props.type = "TextureNodeCompose"                

                props = row.operator("node.add_node", text=" Separate RGBA         ", icon = "NODE_SEPARATERGB")
                props.use_transform = True
                props.type = "TextureNodeDecompose"

                layout.label(text="Textures:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Blend         ", icon = "NODE_BLEND")
                props.use_transform = True
                props.type = "TextureNodeTexBlend"

                props = row.operator("node.add_node", text=" Clouds         ", icon = "NODE_CLOUDS")
                props.use_transform = True
                props.type = "TextureNodeTexClouds"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Distorted Noise        ", icon = "NODE_DISTORTEDNOISE")
                props.use_transform = True
                props.type = "TextureNodeTexDistNoise"

                props = row.operator("node.add_node", text=" Magic         ", icon = "NODE_MAGIC")
                props.use_transform = True
                props.type = "TextureNodeTexMagic"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Marble         ", icon = "NODE_MARBLE")
                props.use_transform = True
                props.type = "TextureNodeTexMarble"

                props = row.operator("node.add_node", text=" Musgrave        ", icon = "NODE_MUSGRAVE")
                props.use_transform = True
                props.type = "TextureNodeTexMusgrave"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Noise        ", icon = "NODE_NOISE")
                props.use_transform = True
                props.type = "TextureNodeTexNoise"

                props = row.operator("node.add_node", text=" Stucci         ", icon = "NODE_STUCCI")
                props.use_transform = True
                props.type = "TextureNodeTexStucci"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Voronoi         ", icon = "NODE_VORONI")
                props.use_transform = True
                props.type = "TextureNodeTexVoronoi"

                props = row.operator("node.add_node", text=" Wood        ", icon = "NODE_WOOD")
                props.use_transform = True
                props.type = "TextureNodeTexWood"

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Output         ", icon = "NODE_OUTPUT")
                props.use_transform = True
                props.type = "TextureNodeOutput"

                props = row.operator("node.add_node", text=" Viewer        ", icon = "NODE_VIEWER")
                props.use_transform = True
                props.type = "TextureNodeViewer"

            #### Icon Buttons

            else: 

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'       

                props = row.operator("node.add_node", text="", icon = "NODE_IMAGE")  
                props.use_transform = True
                props.type = "TextureNodeImage"

                props = row.operator("node.add_node", text="", icon = "NODE_TEXTURE")
                props.use_transform = True
                props.type = "TextureNodeTexture"

                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon = "NODE_RGBCURVE")
                props.use_transform = True
                props.type = "TextureNodeCurveRGB"

                props = row.operator("node.add_node", text="", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "TextureNodeHueSaturation"

                props = row.operator("node.add_node", text="", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "TextureNodeInvert"

                props = row.operator("node.add_node", text="", icon = "NODE_MIXRGB") 
                props.use_transform = True
                props.type = "TextureNodeMixRGB"

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon = "NODE_COMBINERGB")
                props.use_transform = True
                props.type = "TextureNodeCompose"

                props = row.operator("node.add_node", text="", icon = "NODE_SEPARATERGB")
                props.use_transform = True
                props.type = "TextureNodeDecompose"

                layout.label(text="Textures:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text="", icon = "NODE_BLEND")
                props.use_transform = True
                props.type = "TextureNodeTexBlend"

                props = row.operator("node.add_node", text="", icon = "NODE_CLOUDS")
                props.use_transform = True
                props.type = "TextureNodeTexClouds"

                props = row.operator("node.add_node", text="", icon = "NODE_DISTORTEDNOISE")
                props.use_transform = True
                props.type = "TextureNodeTexDistNoise"

                props = row.operator("node.add_node", text="", icon = "NODE_MAGIC")
                props.use_transform = True
                props.type = "TextureNodeTexMagic"

                row = layout.row()
                row.alignment = 'LEFT'    

                props = row.operator("node.add_node", text="", icon = "NODE_MARBLE")
                props.use_transform = True
                props.type = "TextureNodeTexMarble"

                props = row.operator("node.add_node", text="", icon = "NODE_MUSGRAVE")
                props.use_transform = True
                props.type = "TextureNodeTexMusgrave"

                props = row.operator("node.add_node", text="", icon = "NODE_NOISE")
                props.use_transform = True
                props.type = "TextureNodeTexNoise"

                props = row.operator("node.add_node", text="", icon = "NODE_STUCCI")
                props.use_transform = True
                props.type = "TextureNodeTexStucci"

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon = "NODE_VORONI")
                props.use_transform = True
                props.type = "TextureNodeTexVoronoi"

                props = row.operator("node.add_node", text="", icon = "NODE_WOOD")
                props.use_transform = True
                props.type = "TextureNodeTexWood"

                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon = "NODE_OUTPUT")
                props.use_transform = True
                props.type = "TextureNodeOutput"

                props = row.operator("node.add_node", text="", icon = "NODE_VIEWER")
                props.use_transform = True
                props.type = "TextureNodeViewer"

#Input nodes tab, Input Advanced panel
class NodesIconsPanelInputAdvanced(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input Advanced"
    bl_idname = "nodes.nip_input_advanced"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Inputnodes"
    bl_options = {'DEFAULT_CLOSED'}
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

#--------------------------------------------------------------------- Shader Node Tree --------------------------------------------------------------------------------

        if context.space_data.tree_type == 'ShaderNodeTree':

            ##### Textbuttons

            if not scene.UItweaksNodes.icon_or_text: 

            ##### --------------------------------- Textures ------------------------------------------- ####     
               
                layout.label(text="Texture:")

                col = layout.column(align=True)
                row = col.row(align=True)       
        
                props = row.operator("node.add_node", text=" Wave            ", icon = "NODE_WAVES")
                props.use_transform = True
                props.type = "ShaderNodeTexWave"
        
                props = row.operator("node.add_node", text=" Voronoi         ", icon = "NODE_VORONI")
                props.use_transform = True
                props.type = "ShaderNodeTexVoronoi"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Musgrave      ", icon = "NODE_MUSGRAVE")
                props.use_transform = True
                props.type = "ShaderNodeTexMusgrave"
         
                props = row.operator("node.add_node", text=" Gradient       ", icon = "NODE_GRADIENT")
                props.use_transform = True
                props.type = "ShaderNodeTexGradient"

                col = layout.column(align=True)
                row = col.row(align=True)
         
                props = row.operator("node.add_node", text=" Magic            ", icon = "NODE_MAGIC")
                props.use_transform = True
                props.type = "ShaderNodeTexMagic"
        
                props = row.operator("node.add_node", text=" Checker        ", icon = "NODE_CHECKER")
                props.use_transform = True
                props.type = "ShaderNodeTexChecker"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Brick             ", icon = "NODE_BRICK")
                props.use_transform = True 
                props.type = "ShaderNodeTexBrick"
        
                props = row.operator("node.add_node", text=" Point Density", icon = "NODE_POINTCLOUD")
                props.use_transform = True
                props.type = "ShaderNodeTexPointDensity"

                ##### --------------------------------- Shader ------------------------------------------- ####
        
                layout.label(text="Shader:")

                

                if context.space_data.shader_type == 'OBJECT':

                    col = layout.column(align=True)
                    row = col.row(align=True)   
                
                    props = row.operator("node.add_node", text=" Ambient Occlusion  ", icon = "NODE_AMBIENT_OCCLUSION")
                    props.use_transform = True
                    props.type = "ShaderNodeAmbientOcclusion"         
        
                    props = row.operator("node.add_node", text=" Anisotopic    ", icon = "NODE_ANISOTOPIC")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfAnisotropic"
              
                    row = col.row(align=True) 
        
                    props = row.operator("node.add_node", text=" Hair               ", icon = "NODE_HAIRSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfHair"       
        
                    props = row.operator("node.add_node", text=" Holdout        ", icon = "NODE_HOLDOUTSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeHoldout"

                col = layout.column(align=True)
                row = col.row(align=True)  
         
                props = row.operator("node.add_node", text=" Volume Absorption ", icon = "NODE_VOLUMEABSORPTION")
                props.use_transform = True
                props.type = "ShaderNodeVolumeAbsorption"
        
                props = row.operator("node.add_node", text=" Volume Scatter    ", icon = "NODE_VOLUMESCATTER")
                props.use_transform = True
                props.type = "ShaderNodeVolumeScatter"
                
            else:
                ##### --------------------------------- Textures ------------------------------------------- ####
         
                layout.label(text="Texture:")
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_WAVES")
                props.use_transform = True
                props.type = "ShaderNodeTexWave"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VORONI")
                props.use_transform = True
                props.type = "ShaderNodeTexVoronoi"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MUSGRAVE")
                props.use_transform = True
                props.type = "ShaderNodeTexMusgrave"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_GRADIENT")
                props.use_transform = True
                props.type = "ShaderNodeTexGradient"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MAGIC")
                props.use_transform = True
                props.type = "ShaderNodeTexMagic"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_CHECKER")
                props.use_transform = True
                props.type = "ShaderNodeTexChecker"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_BRICK")
                props.use_transform = True
                props.type = "ShaderNodeTexBrick"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_POINTCLOUD")
                props.use_transform = True
                props.type = "ShaderNodeTexPointDensity"

 
                


                ##### --------------------------------- Shader ------------------------------------------- ####
        
                layout.label(text="Shader:")

                if context.space_data.shader_type == 'OBJECT':

                    row = layout.row()
                    row.alignment = 'LEFT'        

                    props = row.operator("node.add_node", text = "", icon = "NODE_ANISOTOPIC")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfAnisotropic"
  
                    props = row.operator("node.add_node", text = "", icon = "NODE_AMBIENT_OCCLUSION")
                    props.use_transform = True
                    props.type = "ShaderNodeAmbientOcclusion"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_HAIRSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfHair"
        
                    props = row.operator("node.add_node", text = "", icon = "NODE_HOLDOUTSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeHoldout"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VOLUMEABSORPTION")
                props.use_transform = True
                props.type = "ShaderNodeVolumeAbsorption"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VOLUMESCATTER")
                props.use_transform = True
                props.type = "ShaderNodeVolumeScatter"

#--------------------------------------------------------------------- Compositing Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'CompositorNodeTree':

            ##### Textbuttons

            if not scene.UItweaksNodes.icon_or_text:

                # ------------------------------- Input -----------------------------

                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Bokeh Image          ", icon = "NODE_BOKEH_IMAGE")    
                props.use_transform = True
                props.type = "CompositorNodeBokehImage"
           
                props = row.operator("node.add_node", text=" Time         ", icon = "NODE_TIME")
                props.use_transform = True
                props.type = "CompositorNodeTime"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Track Position         ", icon = "NODE_TRACKPOSITION")
                props.use_transform = True
                props.type = "CompositorNodeTrackPos"
           
                props = row.operator("node.add_node", text=" Value          ", icon = "NODE_VALUE")
                props.use_transform = True
                props.type = "CompositorNodeValue"
        
                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True)   
            
                props = row.operator("node.add_node", text=" Color Correction         ", icon = "NODE_COLORCORRECTION")
                props.use_transform = True
                props.type = "CompositorNodeColorCorrection"

                props = row.operator("node.add_node", text=" Gamma        ", icon = "NODE_GAMMA")
                props.use_transform = True
                props.type = "CompositorNodeGamma"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Hue Correct        ", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "CompositorNodeHueCorrect"
            
                props = row.operator("node.add_node", text=" Invert         ", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "CompositorNodeInvert"

                col = layout.column(align=True)
                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Mix          ", icon = "NODE_MIXRGB") 
                props.use_transform = True
                props.type = "CompositorNodeMixRGB"

                props = row.operator("node.add_node", text=" Tonemap         ", icon = "NODE_TONEMAP")
                props.use_transform = True
                props.type = "CompositorNodeTonemap"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)   
        
                props = row.operator("node.add_node", text=" File Output         ", icon = "NODE_FILEOUTPUT") 
                props.use_transform = True
                props.type = "CompositorNodeOutputFile"

                props = row.operator("node.add_node", text=" Levels         ", icon = "NODE_LEVELS")
                props.use_transform = True
                props.type = "CompositorNodeLevels"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Split Viewer         ", icon = "NODE_VIWERSPLIT")
                props.use_transform = True
                props.type = "CompositorNodeSplitViewer"


            else:

                ##### Iconbuttons

                # ------------------------------- Input -----------------------------

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_BOKEH_IMAGE")
                props.use_transform = True
                props.type = "CompositorNodeBokehImage"
           
                props = row.operator("node.add_node", text = "", icon = "NODE_TIME")
                props.use_transform = True
                props.type = "CompositorNodeTime" 
            
                props = row.operator("node.add_node", text = "", icon = "NODE_TRACKPOSITION")
                props.use_transform = True
                props.type = "CompositorNodeTrackPos"
           
                props = row.operator("node.add_node", text = "", icon = "NODE_VALUE")
                props.use_transform = True
                props.type = "CompositorNodeValue"

                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT' 
            
                props = row.operator("node.add_node", text = "", icon = "NODE_COLORCORRECTION")
                props.use_transform = True
                props.type = "CompositorNodeColorCorrection"

                props = row.operator("node.add_node", text = "", icon = "NODE_GAMMA")
                props.use_transform = True
                props.type = "CompositorNodeGamma"

                props = row.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "CompositorNodeHueCorrect"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "CompositorNodeInvert"

                row = layout.row()
                row.alignment = 'LEFT' 
            
                props = row.operator("node.add_node", text = "", icon = "NODE_MIXRGB") 
                props.use_transform = True
                props.type = "CompositorNodeMixRGB"

                props = row.operator("node.add_node", text = "", icon = "NODE_TONEMAP")
                props.use_transform = True
                props.type = "CompositorNodeTonemap"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT' 
        
                props = row.operator("node.add_node", text = "", icon = "NODE_FILEOUTPUT") 
                props.use_transform = True
                props.type = "CompositorNodeOutputFile"

                props = row.operator("node.add_node", text = "", icon = "NODE_LEVELS")
                props.use_transform = True
                props.type = "CompositorNodeLevels"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VIWERSPLIT")
                props.use_transform = True
                props.type = "CompositorNodeSplitViewer"

#--------------------------------------------------------------------- Texture Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'TextureNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Coordinates          ", icon = "NODE_TEXCOORDINATE") 
                props.use_transform = True
                props.type = "TextureNodeCoordinates"

                props = row.operator("node.add_node", text=" Curve Time          ", icon = "NODE_CURVE_TIME")
                props.use_transform = True
                props.type = "TextureNodeCurveTime"

                layout.label(text="pattern:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Bricks         ", icon = "NODE_BRICK") 
                props.use_transform = True
                props.type = "TextureNodeBricks"

                props = row.operator("node.add_node", text=" Checker        ", icon = "NODE_CHECKER")
                props.use_transform = True
                props.type = "TextureNodeChecker"

            #### Icon Buttons

            else: 

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'       

                props = row.operator("node.add_node", text="", icon = "NODE_TEXCOORDINATE") 
                props.use_transform = True
                props.type = "TextureNodeCoordinates"

                props = row.operator("node.add_node", text="", icon = "NODE_CURVE_TIME")
                props.use_transform = True
                props.type = "TextureNodeCurveTime"

                layout.label(text="pattern:")

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text="", icon = "NODE_BRICK") 
                props.use_transform = True
                props.type = "TextureNodeBricks"

                props = row.operator("node.add_node", text="", icon = "NODE_CHECKER")
                props.use_transform = True
                props.type = "TextureNodeChecker"

#Modify nodes tab, Modify common panel
class NodesIconsPanelModify(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Modify common"
    bl_idname = "nodes.nip_modify"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Modifynodes"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

#--------------------------------------------------------------------- Shader Node Tree --------------------------------------------------------------------------------

        if context.space_data.tree_type == 'ShaderNodeTree':

            ##### Textbuttons

            if not scene.UItweaksNodes.icon_or_text: 


                ##### --------------------------------- Color ------------------------------------------- ####
        
                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Bright / Contrast    ", icon = "NODE_BRIGHT_CONTRAST")
                props.use_transform = True
                props.type = "ShaderNodeBrightContrast"       
        
                props = row.operator("node.add_node", text=" Gamma         ", icon = "NODE_GAMMA")
                props.use_transform = True
                props.type = "ShaderNodeGamma"

                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text="Hue / Saturation    ", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "ShaderNodeHueSaturation"
        
                props = row.operator("node.add_node", text=" Invert              ", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "ShaderNodeInvert"
                
                col = layout.column(align=True)
                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Light Falloff           ", icon = "NODE_LIGHTFALLOFF")
                props.use_transform = True
                props.type = "ShaderNodeLightFalloff"
        
                props = row.operator("node.add_node", text=" Mix RGB           ", icon = "NODE_MIXRGB") 
                props.use_transform = True
                props.type = "ShaderNodeMixRGB"

                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text="RGB Curves       ", icon = "NODE_RGBCURVE")
                props.use_transform = True
                props.type = "ShaderNodeRGBCurve"

                ##### --------------------------------- Vector ------------------------------------------- ####
        
                layout.label(text="Vector:")

                col = layout.column(align=True)
                row = col.row(align=True)         
        
                props = row.operator("node.add_node", text=" Bump            ", icon = "NODE_BUMP")
                props.use_transform = True
                props.type = "ShaderNodeBump"
        
        
                props = row.operator("node.add_node", text=" Mapping          ", icon = "NODE_MAPPING")
                props.use_transform = True
                props.type = "ShaderNodeMapping"

                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Normal          ", icon = "NODE_NORMAL")
                props.use_transform = True
                props.type = "ShaderNodeNormal"
        
                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Vector Transform   ", icon = "NODE_VECTOR_TRANSFORM")
                props.use_transform = True
                props.type = "ShaderNodeVectorTransform"
        
                props = row.operator("node.add_node", text=" Vector Curves    ", icon = "NODE_VECTOR")
                props.use_transform = True
                props.type = "ShaderNodeVectorCurve"

                ##### --------------------------------- Input ------------------------------------------- ####
        
                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)        
        
                props = row.operator("node.add_node", text=" Attribute     ", icon = "NODE_ATTRIBUTE")
                props.use_transform = True
                props.type = "ShaderNodeAttribute"
        
                props = row.operator("node.add_node", text=" Camera Data   ", icon = "NODE_CAMERADATA")
                props.use_transform = True
                props.type = "ShaderNodeCameraData"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Geometry        ", icon = "NODE_GEOMETRY")
                props.use_transform = True
                props.type = "ShaderNodeNewGeometry"
        
                col = layout.column(align=True)
                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Hair Info     ", icon = "NODE_HAIRINFO")
                props.use_transform = True
                props.type = "ShaderNodeHairInfo"
        
                props = row.operator("node.add_node", text=" Layer Weight   ", icon = "NODE_LAYERWEIGHT")
                props.use_transform = True
                props.type = "ShaderNodeLayerWeight"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Light Path    ", icon = "NODE_LIGHTPATH")
                props.use_transform = True
                props.type = "ShaderNodeLightPath"
        
                props = row.operator("node.add_node", text=" Object Info    ", icon = "NODE_OBJECTINFO")
                props.use_transform = True
                props.type = "ShaderNodeObjectInfo"
        
                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Particle Info", icon = "NODE_PARTICLEINFO")
                props.use_transform = True
                props.type = "ShaderNodeParticleInfo"
        
                props = row.operator("node.add_node", text=" RGB               ", icon = "NODE_RGB")
                props.use_transform = True
                props.type = "ShaderNodeRGB"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Tangent        ", icon = "NODE_TANGENT")
                props.use_transform = True
                props.type = "ShaderNodeTangent"
        
                props = row.operator("node.add_node", text=" Texture Coordinate", icon = "NODE_TEXCOORDINATE") 
                props.use_transform = True
                props.type = "ShaderNodeTexCoord"

                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" UV Map       ", icon = "NODE_UVMAP")
                props.use_transform = True
                props.type = "ShaderNodeUVMap"
        
                props = row.operator("node.add_node", text=" Value            ", icon = "NODE_VALUE")
                props.use_transform = True
                props.type = "ShaderNodeValue"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Wireframe", icon = "NODE_WIREFRAME")
                props.use_transform = True
                props.type = "ShaderNodeWireframe"

                if context.space_data.shader_type == 'LINESTYLE':

                    props = row.operator("node.add_node", text=" UV along stroke", icon = "NODE_UVALONGSTROKE")
                    props.use_transform = True
                    props.type = "ShaderNodeUVALongStroke"

            

                ##### --------------------------------- Converter ------------------------------------------- ####
        
                layout.label(text="Converter:")

                col = layout.column(align=True)
                row = col.row(align=True)           
        
                props = row.operator("node.add_node", text=" Combine HSV    ", icon = "NODE_COMBINEHSV")
                props.use_transform = True
                props.type = "ShaderNodeCombineHSV"        
         
                props = row.operator("node.add_node", text=" Combine RGB   ", icon = "NODE_COMBINERGB")
                props.use_transform = True
                props.type = "ShaderNodeCombineRGB"

                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Combine XYZ    ", icon = "NODE_COMBINEXYZ")
                props.use_transform = True
                props.type = "ShaderNodeCombineXYZ" 

                col = layout.column(align=True)
                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Separate HSV    ", icon = "NODE_SEPARATEHSV") 
                props.use_transform = True
                props.type = "ShaderNodeSeparateHSV"

                props = row.operator("node.add_node", text=" Separate RGB    ", icon = "NODE_SEPARATERGB")
                props.use_transform = True
                props.type = "ShaderNodeSeparateRGB" 
                
                row = col.row(align=True)      
        
                props = row.operator("node.add_node", text=" Separate XYZ    ", icon = "NODE_SEPARATEXYZ")
                props.use_transform = True
                props.type = "ShaderNodeSeparateXYZ" 

                col = layout.column(align=True)
                row = col.row(align=True)           
        
                props = row.operator("node.add_node", text=" Blackbody        ", icon = "NODE_BLACKBODY")
                props.use_transform = True
                props.type = "ShaderNodeBlackbody"        
        
                props = row.operator("node.add_node", text=" ColorRamp      ", icon = "NODE_COLORRAMP")
                props.use_transform = True
                props.type = "ShaderNodeValToRGB"

                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Math              ", icon = "NODE_MATH")
                props.use_transform = True
                props.type = "ShaderNodeMath"
        
                props = row.operator("node.add_node", text=" RGB to BW        ", icon = "NODE_RGBTOBW")
                props.use_transform = True
                props.type = "ShaderNodeRGBToBW"
        
                col = layout.column(align=True)
                row = col.row(align=True)       
        
                props = row.operator("node.add_node", text=" Vector Math       ", icon = "NODE_VECTORMATH")
                props.use_transform = True
                props.type = "ShaderNodeVectorMath"
        
                props = row.operator("node.add_node", text=" Wavelength      ", icon = "NODE_WAVELENGTH")
                props.use_transform = True
                props.type = "ShaderNodeWavelength"

            ##### --------------------------------- Script ------------------------------------------- ####
        
                layout.label(text="Script:")

                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Script            ", icon = "NODE_SCRIPT")
                props.use_transform = True
                props.type = "ShaderNodeScript"  

            ##### Icon Buttons 

            else: 
                ##### --------------------------------- Color ------------------------------------------- ####
        
                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_BRIGHT_CONTRAST")
                props.use_transform = True
                props.type = "ShaderNodeBrightContrast"
        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_GAMMA")
                props.use_transform = True
                props.type = "ShaderNodeGamma"
 
                props = row.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "ShaderNodeHueSaturation"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "ShaderNodeInvert"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_LIGHTFALLOFF")
                props.use_transform = True
                props.type = "ShaderNodeLightFalloff"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MIXRGB") 
                props.use_transform = True
                props.type = "ShaderNodeMixRGB"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_RGBCURVE")
                props.use_transform = True
                props.type = "ShaderNodeRGBCurve"

                ##### --------------------------------- Vector ------------------------------------------- ####
        
                layout.label(text="Vector:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_BUMP")
                props.use_transform = True
                props.type = "ShaderNodeBump"

                props = row.operator("node.add_node", text = "", icon = "NODE_MAPPING")
                props.use_transform = True
                props.type = "ShaderNodeMapping"
     
                props = row.operator("node.add_node", text = "", icon = "NODE_NORMAL")
                props.use_transform = True
                props.type = "ShaderNodeNormal"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VECTOR_TRANSFORM")
                props.use_transform = True
                props.type = "ShaderNodeVectorTransform"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VECTOR")
                props.use_transform = True
                props.type = "ShaderNodeVectorCurve"

                ##### --------------------------------- Input ------------------------------------------- ####
        
                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_ATTRIBUTE")
                props.use_transform = True
                props.type = "ShaderNodeAttribute"
   
                props = row.operator("node.add_node", text = "", icon = "NODE_CAMERADATA")
                props.use_transform = True
                props.type = "ShaderNodeCameraData"


        
                props = row.operator("node.add_node", text = "", icon = "NODE_GEOMETRY")
                props.use_transform = True
                props.type = "ShaderNodeNewGeometry"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_HAIRINFO")
                props.use_transform = True
                props.type = "ShaderNodeHairInfo"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_LAYERWEIGHT")
                props.use_transform = True
                props.type = "ShaderNodeLayerWeight"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_LIGHTPATH")
                props.use_transform = True
                props.type = "ShaderNodeLightPath"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_OBJECTINFO")
                props.use_transform = True
                props.type = "ShaderNodeObjectInfo"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_PARTICLEINFO")
                props.use_transform = True
                props.type = "ShaderNodeParticleInfo"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_RGB")
                props.use_transform = True
                props.type = "ShaderNodeRGB"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_TANGENT")
                props.use_transform = True
                props.type = "ShaderNodeTangent"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_TEXCOORDINATE") 
                props.use_transform = True
                props.type = "ShaderNodeTexCoord"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_UVMAP")
                props.use_transform = True
                props.type = "ShaderNodeUVMap"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VALUE")
                props.use_transform = True
                props.type = "ShaderNodeValue"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_WIREFRAME")
                props.use_transform = True
                props.type = "ShaderNodeWireframe"

                if context.space_data.shader_type == 'LINESTYLE':

                    props = row.operator("node.add_node", text = "", icon = "NODE_UVALONGSTROKE")
                    props.use_transform = True
                    props.type = "ShaderNodeUVALongStroke"


                ##### --------------------------------- Converter ------------------------------------------- ####
        
                layout.label(text="Converter:")

                row = layout.row()
                row.alignment = 'LEFT'

                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINEHSV")
                props.use_transform = True
                props.type = "ShaderNodeCombineHSV"   
                
                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINERGB")
                props.use_transform = True
                props.type = "ShaderNodeCombineRGB"

                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINEXYZ")
                props.use_transform = True
                props.type = "ShaderNodeCombineXYZ"     
        
                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_SEPARATEHSV") 
                props.use_transform = True
                props.type = "ShaderNodeSeparateHSV"

                props = row.operator("node.add_node", text = "", icon = "NODE_SEPARATERGB")
                props.use_transform = True
                props.type = "ShaderNodeSeparateRGB"      
        
                props = row.operator("node.add_node", text = "", icon = "NODE_SEPARATEXYZ")
                props.use_transform = True
                props.type = "ShaderNodeSeparateXYZ"     
                
                row = layout.row()
                row.alignment = 'LEFT'      
        
                props = row.operator("node.add_node", text = "", icon= "NODE_BLACKBODY")
                props.use_transform = True
                props.type = "ShaderNodeBlackbody"        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_COLORRAMP")
                props.use_transform = True
                props.type = "ShaderNodeValToRGB"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MATH")
                props.use_transform = True
                props.type = "ShaderNodeMath"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_RGBTOBW")
                props.use_transform = True
                props.type = "ShaderNodeRGBToBW"    

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VECTORMATH")
                props.use_transform = True
                props.type = "ShaderNodeVectorMath"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_WAVELENGTH")
                props.use_transform = True
                props.type = "ShaderNodeWavelength"

            ##### --------------------------------- Script ------------------------------------------- ####
        
                layout.label(text="Script:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon = "NODE_SCRIPT")
                props.use_transform = True
                props.type = "ShaderNodeScript"  
            
#--------------------------------------------------------------------- Compositing Node Tree --------------------------------------------------------------------------------
        elif context.space_data.tree_type == 'CompositorNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 
            # ------------------------------- Converter -----------------------------

                layout.label(text="Converter:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Combine HSVA         ", icon = "NODE_COMBINEHSV")
                props.use_transform = True
                props.type = "CompositorNodeCombHSVA"
            
                props = row.operator("node.add_node", text=" Combine RGBA         ", icon = "NODE_COMBINERGB")
                props.use_transform = True
                props.type = "CompositorNodeCombRGBA"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Combine YCbCrA       ", icon = "NODE_COMBINEYCBCRA")
                props.use_transform = True
                props.type = "CompositorNodeCombYCCA"

                props = row.operator("node.add_node", text=" Combine YUVA       ", icon = "NODE_COMBINEYUVA")  
                props.use_transform = True
                props.type = "CompositorNodeCombYUVA"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Separate HSVA         ", icon = "NODE_SEPARATEHSV") 
                props.use_transform = True
                props.type = "CompositorNodeSepHSVA"

                props = row.operator("node.add_node", text=" Separate RGBA         ", icon = "NODE_SEPARATERGB")
                props.use_transform = True
                props.type = "CompositorNodeSepRGBA"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Separate YCbCrA       ", icon = "NODE_SEPARATE_YCBCRA") 
                props.use_transform = True
                props.type = "CompositorNodeSepYCCA"

                props = row.operator("node.add_node", text=" Separate YUVA       ", icon = "NODE_SEPARATE_YUVA") 
                props.use_transform = True
                props.type = "CompositorNodeSepYUVA"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Set Alpha         ", icon = "NODE_ALPHA")
                props.use_transform = True
                props.type = "CompositorNodeSetAlpha"
                
                props = row.operator("node.add_node", text=" Alpha Convert          ", icon = "NODE_ALPHACONVERT")
                props.use_transform = True
                props.type = "CompositorNodePremulKey"

                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" RGB to BW          ", icon = "NODE_RGBTOBW")
                props.use_transform = True
                props.type = "CompositorNodeRGBToBW"

                props = row.operator("node.add_node", text=" Color Ramp       ", icon = "NODE_COLORRAMP")
                props.use_transform = True
                props.type = "CompositorNodeValToRGB"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" ID Mask        ", icon = "NODE_MASK") 
                props.use_transform = True
                props.type = "CompositorNodeIDMask"
            
                props = row.operator("node.add_node", text=" Math         ", icon = "NODE_MATH")
                props.use_transform = True
                props.type = "CompositorNodeMath"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Switch View         ", icon = "NODE_SWITCHVIEW")
                props.use_transform = True
                props.type = "CompositorNodeSwitchView"
        
                # ------------------------------- Filter -----------------------------

                layout.label(text="Filter:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Bilateral Blur          ", icon = "NODE_BILATERAL_BLUR")
                props.use_transform = True
                props.type = "CompositorNodeBilateralblur"

                props = row.operator("node.add_node", text=" Blur      ", icon = "NODE_BLUR") 
                props.use_transform = True
                props.type = "CompositorNodeBlur"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Bokeh Blur         ", icon = "NODE_BOKEH_BLUR") 
                props.use_transform = True
                props.type = "CompositorNodeBokehBlur"

                props = row.operator("node.add_node", text=" Directional Blur     ", icon = "NODE_DIRECITONALBLUR")
                props.use_transform = True
                props.type = "CompositorNodeDBlur"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Vector Blur       ", icon = "NODE_VECTOR_BLUR")
                props.use_transform = True
                props.type = "CompositorNodeVecBlur"

                props = row.operator("node.add_node", text=" Defocus         ", icon = "NODE_DEFOCUS")
                props.use_transform = True
                props.type = "CompositorNodeDefocus"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Despeckle       ", icon = "NODE_DESPECKLE")
                props.use_transform = True
                props.type = "CompositorNodeDespeckle"

                props = row.operator("node.add_node", text=" Dilate / Erode      ", icon = "NODE_ERODE")
                props.use_transform = True
                props.type = "CompositorNodeDilateErode"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Filter        ", icon = "NODE_FILTER") 
                props.use_transform = True
                props.type = "CompositorNodeFilter"
            
                props = row.operator("node.add_node", text=" Glare         ", icon = "NODE_GLARE")
                props.use_transform = True
                props.type = "CompositorNodeGlare"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Inpaint        ", icon = "NODE_IMPAINT")
                props.use_transform = True
                props.type = "CompositorNodeInpaint"
            
                props = row.operator("node.add_node", text=" Pixelate         ", icon = "NODE_PIXELATED")
                props.use_transform = True
                props.type = "CompositorNodePixelate"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Sunbeams       ", icon = "NODE_SUNBEAMS") 
                props.use_transform = True
                props.type = "CompositorNodeSunBeams"
                

             # ------------------------------- Vector -----------------------------

                layout.label(text="Vector:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Map Range         ", icon = "NODE_RANGE")
                props.use_transform = True
                props.type = "CompositorNodeMapRange"

                props = row.operator("node.add_node", text=" Map Value     ", icon = "NODE_VALUE")
                props.use_transform = True
                props.type = "CompositorNodeMapValue"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Normal         ", icon = "NODE_NORMAL")
                props.use_transform = True
                props.type = "CompositorNodeNormal"
            
                props = row.operator("node.add_node", text=" Normalize        ", icon = "NODE_NORMALIZE")
                props.use_transform = True
                props.type = "CompositorNodeNormalize"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Vector Curves      ", icon = "NODE_VECTOR")
                props.use_transform = True
                props.type = "CompositorNodeCurveVec"

            # ------------------------------- Matte -----------------------------

                layout.label(text="Matte:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Box Mask         ", icon = "NODE_BOXMASK")
                props.use_transform = True
                props.type = "CompositorNodeBoxMask"

                props = row.operator("node.add_node", text=" Double Edge Mask     ", icon = "NODE_DOUBLEEDGEMASK")
                props.use_transform = True
                props.type = "CompositorNodeDoubleEdgeMask"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Ellipse Mask       ", icon = "NODE_ELLIPSEMASK")  
                props.use_transform = True
                props.type = "CompositorNodeEllipseMask"

                col = layout.column(align=True)
                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Channel Key      ", icon = "NODE_CHANNEL")
                props.use_transform = True
                props.type = "CompositorNodeChannelMatte"     
        
                props = row.operator("node.add_node", text=" Chroma Key         ", icon = "NODE_CHROMA")
                props.use_transform = True
                props.type = "CompositorNodeChromaMatte"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Color Key         ", icon = "NODE_COLOR")
                props.use_transform = True
                props.type = "CompositorNodeColorMatte"

                props = row.operator("node.add_node", text=" Difference Key       ", icon = "NODE_DIFFERENCE")   
                props.use_transform = True
                props.type = "CompositorNodeDiffMatte"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Distance Key      ", icon = "NODE_DISTANCE")
                props.use_transform = True
                props.type = "CompositorNodeDistanceMatte"

                props = row.operator("node.add_node", text=" Keying         ", icon = "NODE_KEYING")
                props.use_transform = True
                props.type = "CompositorNodeKeying"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Keying Screen       ", icon = "NODE_KEYINGSCREEN") 
                props.use_transform = True
                props.type = "CompositorNodeKeyingScreen"

                props = row.operator("node.add_node", text=" Luminance Key        ", icon = "NODE_LUMINANCE") 
                props.use_transform = True
                props.type = "CompositorNodeLumaMatte"

            # ------------------------------- Distort -----------------------------

                layout.label(text="Distort:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Corner Pin        ", icon = "NODE_CORNERPIN")
                props.use_transform = True
                props.type = "CompositorNodeCornerPin"

                props = row.operator("node.add_node", text=" Crop     ", icon = "NODE_CROP")
                props.use_transform = True
                props.type = "CompositorNodeCrop"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Displace        ", icon = "NODE_DISPLACE") 
                props.use_transform = True
                props.type = "CompositorNodeDisplace"
            
                props = row.operator("node.add_node", text=" Flip         ", icon = "NODE_FLIP")  
                props.use_transform = True
                props.type = "CompositorNodeFlip"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Lens Distortion       ", icon = "NODE_LENSDISTORT")
                props.use_transform = True
                props.type = "CompositorNodeLensdist"

                props = row.operator("node.add_node", text=" Map UV     ", icon = "NODE_UVMAP")
                props.use_transform = True
                props.type = "CompositorNodeMapUV"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Movie Distortion     ", icon = "NODE_MOVIEDISTORT") 
                props.use_transform = True
                props.type = "CompositorNodeMovieDistortion"
            
                props = row.operator("node.add_node", text=" Plane Track Deform       ", icon = "NODE_PLANETRACKDEFORM")
                props.use_transform = True
                props.type = "CompositorNodePlaneTrackDeform"

                col = layout.column(align=True)
                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Rotate         ", icon = "NODE_ROTATE")  
                props.use_transform = True
                props.type = "CompositorNodeRotate"
            
                props = row.operator("node.add_node", text=" Scale       ", icon = "NODE_SCALE")
                props.use_transform = True
                props.type = "CompositorNodeScale"

                row = col.row(align=True)  
      
                props = row.operator("node.add_node", text=" Transform       ", icon = "NODE_TRANSFORM")
                props.use_transform = True
                props.type = "CompositorNodeTransform"

                props = row.operator("node.add_node", text=" Translate       ", icon = "NODE_MOVE") 
                props.use_transform = True
                props.type = "CompositorNodeTranslate"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Stabilize 2D        ", icon = "NODE_STABILIZE2D")  
                props.use_transform = True
                props.type = "CompositorNodeStabilize"

            #### Icon Buttons

            else: 
            # ------------------------------- Converter -----------------------------

                layout.label(text="Converter:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINEHSV")
                props.use_transform = True
                props.type = "CompositorNodeCombHSVA"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINERGB")
                props.use_transform = True
                props.type = "CompositorNodeCombRGBA"

                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINEYCBCRA")
                props.use_transform = True
                props.type = "CompositorNodeCombYCCA"

                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINEYUVA")  
                props.use_transform = True
                props.type = "CompositorNodeCombYUVA"

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text = "", icon = "NODE_SEPARATEHSV")  
                props.use_transform = True
                props.type = "CompositorNodeSepHSVA"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_SEPARATERGB")
                props.use_transform = True
                props.type = "CompositorNodeSepRGBA"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_SEPARATE_YCBCRA") 
                props.use_transform = True
                props.type = "CompositorNodeSepYCCA"

                props = row.operator("node.add_node", text = "", icon = "NODE_COMBINEYUVA")  
                props.use_transform = True
                props.type = "CompositorNodeSepYUVA"

                row = layout.row()
                row.alignment = 'LEFT'
                
                props = row.operator("node.add_node", text = "", icon = "NODE_ALPHA")
                props.use_transform = True
                props.type = "CompositorNodeSetAlpha"  

                props = row.operator("node.add_node", text = "", icon = "NODE_ALPHACONVERT")
                props.use_transform = True
                props.type = "CompositorNodePremulKey"

                props = row.operator("node.add_node", text = "", icon = "NODE_RGBTOBW")
                props.use_transform = True
                props.type = "CompositorNodeRGBToBW"

                props = row.operator("node.add_node", text = "", icon = "NODE_COLORRAMP")
                props.use_transform = True
                props.type = "CompositorNodeValToRGB"   
                
                row = layout.row()
                row.alignment = 'LEFT'            
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MASK") 
                props.use_transform = True
                props.type = "CompositorNodeIDMask"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_MATH")
                props.use_transform = True
                props.type = "CompositorNodeMath"

                props = row.operator("node.add_node", text = "", icon = "NODE_SWITCHVIEW")
                props.use_transform = True
                props.type = "CompositorNodeSwitchView"
        
                # ------------------------------- Filter -----------------------------

                layout.label(text="Filter:")

                row = layout.row()
                row.alignment = 'LEFT'    

                props = row.operator("node.add_node", text = "", icon = "NODE_BILATERAL_BLUR")
                props.use_transform = True
                props.type = "CompositorNodeBilateralblur"

                props = row.operator("node.add_node", text = "", icon = "NODE_BLUR") 
                props.use_transform = True
                props.type = "CompositorNodeBlur"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_BOKEH_BLUR") 
                props.use_transform = True
                props.type = "CompositorNodeBokehBlur"

                props = row.operator("node.add_node", text = "", icon = "NODE_DIRECITONALBLUR")
                props.use_transform = True
                props.type = "CompositorNodeDBlur"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_VECTOR_BLUR")
                props.use_transform = True
                props.type = "CompositorNodeVecBlur"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_DEFOCUS")
                props.use_transform = True
                props.type = "CompositorNodeDefocus"

                props = row.operator("node.add_node", text = "", icon = "NODE_DESPECKLE")
                props.use_transform = True
                props.type = "CompositorNodeDespeckle"

                props = row.operator("node.add_node", text = "", icon = "NODE_ERODE")
                props.use_transform = True
                props.type = "CompositorNodeDilateErode"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_FILTER")  
                props.use_transform = True
                props.type = "CompositorNodeFilter"
    
                props = row.operator("node.add_node", text = "", icon = "NODE_GLARE")
                props.use_transform = True
                props.type = "CompositorNodeGlare"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_IMPAINT")
                props.use_transform = True
                props.type = "CompositorNodeInpaint"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_PIXELATED")
                props.use_transform = True
                props.type = "CompositorNodePixelate"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_SUNBEAMS") 
                props.use_transform = True
                props.type = "CompositorNodeSunBeams"

                row = layout.row()
                row.alignment = 'LEFT'  

                

             # ------------------------------- Vector -----------------------------

                layout.label(text="Vector:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_RANGE")
                props.use_transform = True
                props.type = "CompositorNodeMapRange"

                props = row.operator("node.add_node", text = "", icon = "NODE_VALUE")
                props.use_transform = True
                props.type = "CompositorNodeMapValue"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_NORMAL")
                props.use_transform = True
                props.type = "CompositorNodeNormal"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_NORMALIZE")
                props.use_transform = True
                props.type = "CompositorNodeNormalize"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_VECTOR")
                props.use_transform = True
                props.type = "CompositorNodeCurveVec"

            # ------------------------------- Matte -----------------------------

                layout.label(text="Matte:")

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text = "", icon = "NODE_BOXMASK")
                props.use_transform = True
                props.type = "CompositorNodeBoxMask"

                props = row.operator("node.add_node", text="", icon = "NODE_DOUBLEEDGEMASK")
                props.use_transform = True
                props.type = "CompositorNodeDoubleEdgeMask"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_ELLIPSEMASK")  
                props.use_transform = True
                props.type = "CompositorNodeEllipseMask"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_CHANNEL")
                props.use_transform = True
                props.type = "CompositorNodeChannelMatte" 
        
                props = row.operator("node.add_node", text = "", icon = "NODE_CHROMA")
                props.use_transform = True
                props.type = "CompositorNodeChromaMatte"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_COLOR")
                props.use_transform = True
                props.type = "CompositorNodeColorMatte"
      
                props = row.operator("node.add_node", text = "", icon = "NODE_DIFFERENCE") 
                props.use_transform = True
                props.type = "CompositorNodeDiffMatte"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_DISTANCE")
                props.use_transform = True
                props.type = "CompositorNodeDistanceMatte" 
            
                props = row.operator("node.add_node", text = "", icon = "NODE_KEYING")
                props.use_transform = True
                props.type = "CompositorNodeKeying"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_KEYINGSCREEN") 
                props.use_transform = True
                props.type = "CompositorNodeKeyingScreen"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_LUMINANCE") 
                props.use_transform = True
                props.type = "CompositorNodeLumaMatte"

            # ------------------------------- Distort -----------------------------

                layout.label(text="Distort:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_CORNERPIN")
                props.use_transform = True
                props.type = "CompositorNodeCornerPin"

                props = row.operator("node.add_node", text = "", icon = "NODE_CROP")
                props.use_transform = True
                props.type = "CompositorNodeCrop"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_DISPLACE") 
                props.use_transform = True
                props.type = "CompositorNodeDisplace"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_FLIP")  
                props.use_transform = True
                props.type = "CompositorNodeFlip"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon = "NODE_LENSDISTORT")
                props.use_transform = True
                props.type = "CompositorNodeLensdist"

                props = row.operator("node.add_node", text = "", icon = "NODE_UVMAP")
                props.use_transform = True
                props.type = "CompositorNodeMapUV"
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MOVIEDISTORT") 
                props.use_transform = True
                props.type = "CompositorNodeMovieDistortion"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_PLANETRACKDEFORM")
                props.use_transform = True
                props.type = "CompositorNodePlaneTrackDeform"

                row = layout.row()
                row.alignment = 'LEFT'  
            
                props = row.operator("node.add_node", text = "", icon = "NODE_ROTATE") 
                props.use_transform = True
                props.type = "CompositorNodeRotate"
            
                props = row.operator("node.add_node", text = "", icon = "NODE_SCALE")
                props.use_transform = True
                props.type = "CompositorNodeScale"
                    
                props = row.operator("node.add_node", text = "", icon = "NODE_TRANSFORM")
                props.use_transform = True
                props.type = "CompositorNodeTransform"

                props = row.operator("node.add_node", text = "", icon = "NODE_MOVE") 
                props.use_transform = True
                props.type = "CompositorNodeTranslate"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon = "NODE_STABILIZE2D")  
                props.use_transform = True
                props.type = "CompositorNodeStabilize"

#--------------------------------------------------------------------- Texture Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'TextureNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                layout.label(text="Converter:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Color Ramp         ", icon = "NODE_COLORRAMP")
                props.use_transform = True
                props.type = "TextureNodeValToRGB"

                props = row.operator("node.add_node", text=" Distance         ", icon = "NODE_DISTANCE")
                props.use_transform = True
                props.type = "TextureNodeDistance"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Math        ", icon = "NODE_MATH")
                props.use_transform = True
                props.type = "TextureNodeMath"

                props = row.operator("node.add_node", text=" RGB to BW        ", icon = "NODE_RGBTOBW")
                props.use_transform = True
                props.type = "TextureNodeRGBToBW"

                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Value to Normal         ", icon = "NODE_NORMAL")
                props.use_transform = True
                props.type = "TextureNodeValToNor"

                layout.label(text="Distort:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" At        ", icon = "NODE_AT")
                props.use_transform = True
                props.type = "TextureNodeAt"

                props = row.operator("node.add_node", text=" Rotate         ", icon = "NODE_ROTATE") 
                props.use_transform = True
                props.type = "TextureNodeRotate"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Scale        ", icon = "NODE_SCALE")
                props.use_transform = True
                props.type = "TextureNodeScale"

                props = row.operator("node.add_node", text=" translate       ", icon = "NODE_MOVE") 
                props.use_transform = True
                props.type = "TextureNodeTranslate"

            #### Icon Buttons

            else: 

                layout.label(text="Converter:")

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon = "NODE_COLORRAMP")
                props.use_transform = True
                props.type = "TextureNodeValToRGB"

                props = row.operator("node.add_node", text="", icon = "NODE_DISTANCE")
                props.use_transform = True
                props.type = "TextureNodeDistance"

                props = row.operator("node.add_node", text="", icon = "NODE_MATH")
                props.use_transform = True
                props.type = "TextureNodeMath"

                props = row.operator("node.add_node", text="", icon = "NODE_RGBTOBW")
                props.use_transform = True
                props.type = "TextureNodeRGBToBW"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text="", icon = "NODE_NORMAL")
                props.use_transform = True
                props.type = "TextureNodeValToNor"

                layout.label(text="Distort:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text="", icon = "NODE_AT")
                props.use_transform = True
                props.type = "TextureNodeAt"

                props = row.operator("node.add_node", text="", icon = "NODE_ROTATE") 
                props.use_transform = True
                props.type = "TextureNodeRotate"

                props = row.operator("node.add_node", text="", icon = "NODE_SCALE")
                props.use_transform = True
                props.type = "TextureNodeScale"

                props = row.operator("node.add_node", text="", icon = "NODE_MOVE") 
                props.use_transform = True
                props.type = "TextureNodeTranslate"

#Relations tab, Relations Panel
class NodesIconsPanelRelations(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Relations"
    bl_idname = "nodes.nip_relations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Relations"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        ##### Textbuttons

        if not scene.UItweaksNodes.icon_or_text: 

             ##### --------------------------------- Group ------------------------------------------- ####
        
            layout.label(text="Group Nodes:")

            col = layout.column(align=True)
            row = col.row(align=True)       

            row.operator("node.group_edit", text=" Edit Group     ", icon = "NODE_EDITGROUP").exit = False
            row.operator("node.group_edit", text = "Exit Edit Group  ", icon = "NODE_EXITEDITGROUP").exit = True

            row = col.row(align=True)  

            row.operator("node.group_insert", text = " Group Insert    ", icon = "NODE_GROUPINSERT")
            row.operator("node.group_make", text = " Make Group     ", icon = "NODE_MAKEGROUP")

            row = col.row(align=True)  

            row.operator("node.group_ungroup", text = " Ungroup        ", icon = "NODE_UNGROUP")
  

            ##### --------------------------------- Layout ------------------------------------------- ####
        
            layout.label(text="Layout:")

            col = layout.column(align=True)
            row = col.row(align=True)         

            props = row.operator("node.add_node", text=" Frame       ", icon = "NODE_FRAME")
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text=" Reroute      ", icon = "NODE_REROUTE")
            props.use_transform = True
            props.type = "NodeReroute"

            if context.space_data.tree_type == 'CompositorNodeTree':
                row = col.row(align=True)
                props = row.operator("node.add_node", text=" Switch      ", icon = "NODE_SWITCH")
                props.use_transform = True
                props.type = "CompositorNodeSwitch"

        else: 

            ##### --------------------------------- Group ------------------------------------------- ####
        
            layout.label(text="Group:")

            row = layout.row()
            row.alignment = 'LEFT'        

            row.operator("node.group_edit", text = "", icon = "NODE_EDITGROUP").exit = False
            row.operator("node.group_edit", text = "", icon = "NODE_EXITEDITGROUP").exit = True
            row.operator("node.group_insert", text = "", icon = "NODE_GROUPINSERT")
            row.operator("node.group_make", text = "", icon = "NODE_MAKEGROUP")

            row = layout.row()
            row.alignment = 'LEFT'

            row.operator("node.group_ungroup", text = "", icon = "NODE_UNGROUP")

            ##### --------------------------------- Layout ------------------------------------------- ####
        
            layout.label(text="Layout:")

            row = layout.row()
            row.alignment = 'LEFT'        

            props = row.operator("node.add_node", text = "", icon = "NODE_FRAME")
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text = "", icon = "NODE_REROUTE")
            props.use_transform = True
            props.type = "NodeReroute"

            if context.space_data.tree_type == 'CompositorNodeTree':
                props = row.operator("node.add_node", text="", icon = "NODE_SWITCH")
                props.use_transform = True
                props.type = "CompositorNodeSwitch"

 # ----------------------------------------------------------- 
    
# global variable to store icons in 
custom_icons = None

def register():
    
    bpy.utils.register_class(NodesIconsPanelProp)
    bpy.utils.register_class(NodesIconsPanelInput)
    bpy.utils.register_class(NodesIconsPanelInputAdvanced)
    bpy.utils.register_class(NodesIconsPanelModify)
    bpy.utils.register_class(NodesIconsPanelRelations)
     
    # Our external Icons
    global custom_icons

    custom_icons = bpy.utils.previews.new()

    # Use this for addons
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    # Use this for testing the script in the scripting layout
    #script_path = bpy.context.space_data.text.filepath
    #icons_dir = os.path.join(os.path.dirname(script_path), "icons")


    # Our data block for icon or text buttons
    bpy.utils.register_class(UITweaksDataNodes) # Our data block
    bpy.types.Scene.UItweaksNodes = bpy.props.PointerProperty(type=UITweaksDataNodes) # Bind reference of type of our data block to type Scene objects
    
    
def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    bpy.utils.unregister_class(NodesIconsPanelProp)
    bpy.utils.unregister_class(NodesIconsPanelInput)
    bpy.utils.unregister_class(NodesIconsPanelInputAdvanced)
    bpy.utils.unregister_class(NodesIconsPanelModify)
    bpy.utils.unregister_class(NodesIconsPanelRelations)

    bpy.utils.unregister_class(UITweaksDataNodes)
     
# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.

if __name__ == "__main__":
    register()