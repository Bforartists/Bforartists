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


import bpy
import os
import bpy.utils.previews

from bpy import context

bl_info = {
    "name": "Nodes Icons Panel",
    "author": "Reiner 'Tiles' Prokein",
    "version": (0, 9, 5),
    "blender": (2, 76, 0),
    "location": "Node Editor -> Tool Shelf + Properties Sidebar",
    "description": "Adds panels with Icon buttons in the Node editor",
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
        
                props = row.operator("node.add_node", text=" Image          ", icon_value = custom_icons["image"].icon_id)    
                props.use_transform = True
                props.type = "ShaderNodeTexImage"
        
        
                props = row.operator("node.add_node", text=" Environment", icon_value = custom_icons["environment"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexEnvironment"

                row = col.row(align=True)          
        
                props = row.operator("node.add_node", text=" Sky              ", icon_value = custom_icons["sky"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexSky"
         
                props = row.operator("node.add_node", text=" Noise            ", icon_value = custom_icons["noise"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexNoise"
       

                ##### --------------------------------- Connect ------------------------------------------- ####
        
                layout.label(text="Connect:")

                col = layout.column(align=True)
                row = col.row(align=True)            
        
                props = row.operator("node.add_node", text=" Add              ", icon_value = custom_icons["addshader"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeAddShader" 

                props = row.operator("node.add_node", text=" Mix            ", icon_value = custom_icons["mixshader"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMixShader"

                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Normal Map     ", icon_value = custom_icons["normalmap"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeNormalMap"

                 ##### --------------------------------- Shader ------------------------------------------- ####

                if context.space_data.shader_type == 'OBJECT':

                    layout.label(text="Shader:")

                    col = layout.column(align=True)
                    row = col.row(align=True)
                    
                    props = row.operator("node.add_node", text=" Principled        ", icon_value = custom_icons["node_principled_shader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfPrincipled"

                    col = layout.column(align=True)
                    row = col.row(align=True)     
        
                    props = row.operator("node.add_node", text=" Diffuse          ", icon_value = custom_icons["diffuseshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfDiffuse"
        
                    props = row.operator("node.add_node", text=" Emission        ", icon_value = custom_icons["emission"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeEmission"

                    row = col.row(align=True)  

                    props = row.operator("node.add_node", text=" Fresnel        ", icon_value = custom_icons["fresnel"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeFresnel"
        
                    props = row.operator("node.add_node", text=" Glass               ", icon_value = custom_icons["glasshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlass"   

                    col = layout.column(align=True)
                    row = col.row(align=True)  
         
                    props = row.operator("node.add_node", text=" Glossy          ", icon_value = custom_icons["glossyshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlossy"
        
                    props = row.operator("node.add_node", text=" Refraction     ", icon_value = custom_icons["refractionshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfRefraction"

                    row = col.row(align=True)  
         
                    props = row.operator("node.add_node", text=" Subsurface Scattering", icon_value = custom_icons["sss_shader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeSubsurfaceScattering"
        
                    props = row.operator("node.add_node", text=" Toon              ", icon_value = custom_icons["toonshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfToon"

                    col = layout.column(align=True)
                    row = col.row(align=True)  
        
                    props = row.operator("node.add_node", text=" Translucent      ", icon_value = custom_icons["translucentshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTranslucent"

                    props = row.operator("node.add_node", text=" Transparent    ", icon_value = custom_icons["transparentshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTransparent"

                    row = col.row(align=True)  

                    props = row.operator("node.add_node", text=" Velvet            ", icon_value = custom_icons["velvetshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfVelvet"

                elif context.space_data.shader_type == 'WORLD':

                    layout.label(text="Shader:")

                    col = layout.column(align=True)
                    row = col.row(align=True)       

                    props = row.operator("node.add_node", text=" Background            ", icon_value = custom_icons["backgroundshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBackground"

                ##### --------------------------------- Output ------------------------------------------- ####

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)
                
                if context.space_data.shader_type == 'OBJECT':
        
                    props = row.operator("node.add_node", text=" Material Output", icon_value = custom_icons["material_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputMaterial"
        
        
                    props = row.operator("node.add_node", text=" Lamp Output", icon_value = custom_icons["lamp_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLamp"

                elif context.space_data.shader_type == 'WORLD':
        
                    props = row.operator("node.add_node", text=" World Output", icon_value = custom_icons["world_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputWorld"

                elif context.space_data.shader_type == 'LINESTYLE':
        
                    props = row.operator("node.add_node", text=" Line Style Output", icon_value = custom_icons["linestyle_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLineStyle"

            #### Icon Buttons

            else:
          
                ##### --------------------------------- Textures ------------------------------------------- ####
         
                layout.label(text="Texture:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["image"].icon_id)
        
                props.use_transform = True
                props.type = "ShaderNodeTexImage"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["environment"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexEnvironment"
   
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["sky"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexSky"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["noise"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexNoise"


                ##### --------------------------------- Connect ------------------------------------------- ####
        
                layout.label(text="Connect:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["addshader"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeAddShader"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["mixshader"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMixShader"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["normalmap"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeNormalMap"

                ##### --------------------------------- Shader ------------------------------------------- ####

                if context.space_data.shader_type == 'OBJECT':

                    layout.label(text="Shader:")

                    row = layout.row()
                    row.alignment = 'LEFT' 

                    props = row.operator("node.add_node", text="", icon_value = custom_icons["node_principled_shader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfPrincipled"

                    row = layout.row()
                    row.alignment = 'LEFT' 
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["diffuseshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfDiffuse"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["emission"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeEmission"

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["fresnel"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeFresnel"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["glasshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeLayerWeight"

                    row = layout.row()
                    row.alignment = 'LEFT' 

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["glossyshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfGlossy"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["refractionshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfRefraction"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["sss_shader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeSubsurfaceScattering"

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["toonshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfToon"
        
                    row = layout.row()
                    row.alignment = 'LEFT'  
                    
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["translucentshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTranslucent"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["transparentshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfTransparent"

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["velvetshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfVelvet"

                elif context.space_data.shader_type == 'WORLD':

                    layout.label(text="Shader:")

                    row = layout.row()
                    row.alignment = 'LEFT' 

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["backgroundshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBackground"

                ##### --------------------------------- Output ------------------------------------------- ####
        
                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT'        

                if context.space_data.shader_type == 'OBJECT':
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["material_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputMaterial"

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["lamp_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLamp"

                elif context.space_data.shader_type == 'WORLD':
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["world_output"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeOutputWorld"

                elif context.space_data.shader_type == 'LINESTYLE':
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["linestyle_output"].icon_id)
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

                props = row.operator("node.add_node", text=" Image          ", icon_value = custom_icons["image"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeImage"

                props = row.operator("node.add_node", text=" Texture          ", icon_value = custom_icons["node_texture"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTexture"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Mask         ", icon_value = custom_icons["node_mask"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMask"
            
                props = row.operator("node.add_node", text=" Movie Clip         ", icon_value = custom_icons["node_movie"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMovieClip"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Render Layers         ", icon_value = custom_icons["render_layer"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeRLayers"
            
                props = row.operator("node.add_node", text=" RGB        ", icon_value = custom_icons["rgb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeRGB"
                          
        
                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Alpha Over          ", icon_value = custom_icons["alpha"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeAlphaOver"

                props = row.operator("node.add_node", text=" Bright / Contrast        ", icon_value = custom_icons["brightcontrast"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBrightContrast"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Color Balance         ", icon_value = custom_icons["colorbalance"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeColorBalance"

                props = row.operator("node.add_node", text=" Hue Saturation Value        ", icon_value = custom_icons["huesaturation"].icon_id)   
                props.use_transform = True
                props.type = "CompositorNodeHueSat"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" RGB Curves         ", icon_value = custom_icons["rgbcurve"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCurveRGB"
        
                props = row.operator("node.add_node", text=" Z Combine         ", icon_value = custom_icons["zcombine"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeZcombine"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)   

         
                props = row.operator("node.add_node", text=" Composite          ", icon_value = custom_icons["compositeoutput"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeComposite"
            
                props = row.operator("node.add_node", text=" Viewer          ", icon_value = custom_icons["node_viewer"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeViewer"

            #### Image Buttons

            else: 

                # ------------------------------- Input -----------------------------

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["image"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeImage"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_texture"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTexture"

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_mask"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMask"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_movie"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMovieClip"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["render_layer"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeRLayers"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["rgb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeRGB"

                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["alpha"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeAlphaOver"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["brightcontrast"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBrightContrast"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["colorbalance"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeColorBalance"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["huesaturation"].icon_id)   
                props.use_transform = True
                props.type = "CompositorNodeHueSat"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["rgbcurve"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCurveRGB"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["zcombine"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeZcombine"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["compositeoutput"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeComposite"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_viewer"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeViewer"

#--------------------------------------------------------------------- Texture Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'TextureNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Image          ", icon_value = custom_icons["image"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeImage"

                props = row.operator("node.add_node", text=" Texture          ", icon_value = custom_icons["node_texture"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeTexture"

                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" RGB Curves          ", icon_value = custom_icons["rgbcurve"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeCurveRGB"

                props = row.operator("node.add_node", text=" Hue / Saturation         ", icon_value = custom_icons["huesaturation"].icon_id)   
                props.use_transform = True
                props.type = "TextureNodeHueSaturation"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Invert         ", icon_value = custom_icons["invert"].icon_id)  
                props.use_transform = True
                props.type = "TextureNodeInvert"

                props = row.operator("node.add_node", text=" Mix RGB          ", icon_value = custom_icons["mixrgb"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeMixRGB"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Combine RGBA         ", icon_value = custom_icons["combinergb"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeCompose"                

                props = row.operator("node.add_node", text=" Separate RGBA         ", icon_value = custom_icons["separatergb"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeDecompose"

                layout.label(text="Textures:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Blend         ", icon_value = custom_icons["blend"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexBlend"

                props = row.operator("node.add_node", text=" Clouds         ", icon_value = custom_icons["clouds"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexClouds"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Distorted Noise        ", icon_value = custom_icons["distortednoise"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexDistNoise"

                props = row.operator("node.add_node", text=" Magic         ", icon_value = custom_icons["magic"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexMagic"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Marble         ", icon_value = custom_icons["marble"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexMarble"

                props = row.operator("node.add_node", text=" Musgrave        ", icon_value = custom_icons["musgrave"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexMusgrave"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Noise        ", icon_value = custom_icons["noise"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexNoise"

                props = row.operator("node.add_node", text=" Stucci         ", icon_value = custom_icons["stucci"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexStucci"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Voronoi         ", icon_value = custom_icons["voronoi"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexVoronoi"

                props = row.operator("node.add_node", text=" Wood        ", icon_value = custom_icons["wood"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexWood"

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Output         ", icon_value = custom_icons["output"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeOutput"

                props = row.operator("node.add_node", text=" Viewer        ", icon_value = custom_icons["node_viewer"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeViewer"

            #### Icon Buttons

            else: 

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'       

                props = row.operator("node.add_node", text="", icon_value = custom_icons["image"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeImage"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_texture"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeTexture"

                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon_value = custom_icons["rgbcurve"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeCurveRGB"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["huesaturation"].icon_id)   
                props.use_transform = True
                props.type = "TextureNodeHueSaturation"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["invert"].icon_id)  
                props.use_transform = True
                props.type = "TextureNodeInvert"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["mixrgb"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeMixRGB"

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon_value = custom_icons["combinergb"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeCompose"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["separatergb"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeDecompose"

                layout.label(text="Textures:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text="", icon_value = custom_icons["blend"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexBlend"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["clouds"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexClouds"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["distortednoise"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexDistNoise"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["magic"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexMagic"

                row = layout.row()
                row.alignment = 'LEFT'    

                props = row.operator("node.add_node", text="", icon_value = custom_icons["marble"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexMarble"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["musgrave"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexMusgrave"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["noise"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexNoise"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["stucci"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexStucci"

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon_value = custom_icons["voronoi"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexVoronoi"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["wood"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTexWood"

                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon_value = custom_icons["output"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeOutput"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_viewer"].icon_id)
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
        
                props = row.operator("node.add_node", text=" Wave            ", icon_value = custom_icons["waves"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexWave"
        
                props = row.operator("node.add_node", text=" Voronoi         ", icon_value = custom_icons["voronoi"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexVoronoi"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Musgrave      ", icon_value = custom_icons["musgrave"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexMusgrave"
         
                props = row.operator("node.add_node", text=" Gradient       ", icon_value = custom_icons["gradient"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexGradient"

                col = layout.column(align=True)
                row = col.row(align=True)
         
                props = row.operator("node.add_node", text=" Magic            ", icon_value = custom_icons["magic"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexMagic"
        
                props = row.operator("node.add_node", text=" Checker        ", icon_value = custom_icons["checker"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexChecker"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Brick             ", icon_value = custom_icons["brick"].icon_id)
                props.use_transform = True 
                props.type = "ShaderNodeTexBrick"
        
                props = row.operator("node.add_node", text=" Point Density", icon_value = custom_icons["pointcloud"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexPointDensity"

                ##### --------------------------------- Shader ------------------------------------------- ####
        
                layout.label(text="Shader:")

                

                if context.space_data.shader_type == 'OBJECT':

                    col = layout.column(align=True)
                    row = col.row(align=True)   
                
                    props = row.operator("node.add_node", text=" Ambient Occlusion  ", icon_value = custom_icons["ambient_occlusion"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeAmbientOcclusion"         
        
                    props = row.operator("node.add_node", text=" Anisotopic    ", icon_value = custom_icons["anisotopicshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfAnisotropic"
              
                    row = col.row(align=True) 
        
                    props = row.operator("node.add_node", text=" Hair               ", icon_value = custom_icons["hairshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfHair"       
        
                    props = row.operator("node.add_node", text=" Holdout        ", icon_value = custom_icons["holdoutshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeHoldout"

                col = layout.column(align=True)
                row = col.row(align=True)  
         
                props = row.operator("node.add_node", text=" Volume Absorption ", icon_value = custom_icons["volumeabsorptionshader"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVolumeAbsorption"
        
                props = row.operator("node.add_node", text=" Volume Scatter    ", icon_value = custom_icons["volumescatter"].icon_id)
                props.use_transform = True

            else:
                ##### --------------------------------- Textures ------------------------------------------- ####
         
                layout.label(text="Texture:")
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["waves"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexWave"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["voronoi"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexVoronoi"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["musgrave"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexMusgrave"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["gradient"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexGradient"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["magic"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexMagic"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["checker"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexChecker"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["brick"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexBrick"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["pointcloud"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexPointDensity"

 
                props.type = "ShaderNodeVolumeScatter"


                ##### --------------------------------- Shader ------------------------------------------- ####
        
                layout.label(text="Shader:")

                if context.space_data.shader_type == 'OBJECT':

                    row = layout.row()
                    row.alignment = 'LEFT'        

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["anisotopicshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfAnisotropic"
  
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["ambient_occlusion"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeAmbientOcclusion"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["hairshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfHair"
        
                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["holdoutshader"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeHoldout"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["volumeabsorptionshader"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVolumeAbsorption"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["volumescatter"].icon_id)
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

                props = row.operator("node.add_node", text=" Bokeh Image          ", icon_value = custom_icons["bokeh_image"].icon_id)    
                props.use_transform = True
                props.type = "CompositorNodeBokehImage"
           
                props = row.operator("node.add_node", text=" Time         ", icon_value = custom_icons["node_time"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTime"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Track Position         ", icon_value = custom_icons["trackposition"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTrackPos"
           
                props = row.operator("node.add_node", text=" Value          ", icon_value = custom_icons["value"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeValue"
        
                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                col = layout.column(align=True)
                row = col.row(align=True)   
            
                props = row.operator("node.add_node", text=" Color Correction         ", icon_value = custom_icons["colorcorrection"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeColorCorrection"

                props = row.operator("node.add_node", text=" Gamma        ", icon_value = custom_icons["gamma"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeGamma"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Hue Correct        ", icon_value = custom_icons["huesaturation"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeHueCorrect"
            
                props = row.operator("node.add_node", text=" Invert         ", icon_value = custom_icons["invert"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeInvert"

                col = layout.column(align=True)
                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Mix          ", icon_value = custom_icons["mixrgb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMixRGB"

                props = row.operator("node.add_node", text=" Tonemap         ", icon_value = custom_icons["tonemap"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTonemap"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                col = layout.column(align=True)
                row = col.row(align=True)   
        
                props = row.operator("node.add_node", text=" File Output         ", icon_value = custom_icons["fileoutput"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeOutputFile"

                props = row.operator("node.add_node", text=" Levels         ", icon_value = custom_icons["node_levels"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeLevels"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Split Viewer         ", icon_value = custom_icons["node_viewersplit"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSplitViewer"


            else:

                ##### Iconbuttons

                # ------------------------------- Input -----------------------------

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["bokeh_image"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBokehImage"
           
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_time"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTime" 
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["trackposition"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTrackPos"
           
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["value"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeValue"

                # ------------------------------- Color -----------------------------

                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT' 
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["colorcorrection"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeColorCorrection"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["gamma"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeGamma"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["huesaturation"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeHueCorrect"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["invert"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeInvert"

                row = layout.row()
                row.alignment = 'LEFT' 
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["mixrgb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMixRGB"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["tonemap"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeTonemap"

                # ------------------------------- Output -----------------------------

                layout.label(text="Output:")

                row = layout.row()
                row.alignment = 'LEFT' 
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["fileoutput"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeOutputFile"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_levels"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeLevels"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_viewersplit"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSplitViewer"

#--------------------------------------------------------------------- Texture Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'TextureNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Coordinates          ", icon_value = custom_icons["texcoordinate"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeCoordinates"

                props = row.operator("node.add_node", text=" Curve Time          ", icon_value = custom_icons["curve_time"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeCurveTime"

                layout.label(text="pattern:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Bricks         ", icon_value = custom_icons["brick"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeBricks"

                props = row.operator("node.add_node", text=" Checker        ", icon_value = custom_icons["checker"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeChecker"

            #### Icon Buttons

            else: 

                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'       

                props = row.operator("node.add_node", text="", icon_value = custom_icons["texcoordinate"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeCoordinates"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["curve_time"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeCurveTime"

                layout.label(text="pattern:")

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text="", icon_value = custom_icons["brick"].icon_id) 
                props.use_transform = True
                props.type = "TextureNodeBricks"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["checker"].icon_id)
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
        
                props = row.operator("node.add_node", text=" Bright / Contrast    ", icon_value = custom_icons["brightcontrast"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeBrightContrast"       
        
                props = row.operator("node.add_node", text=" Gamma         ", icon_value = custom_icons["gamma"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeGamma"

                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text="Hue / Saturation    ", icon_value = custom_icons["huesaturation"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeHueSaturation"
        
                props = row.operator("node.add_node", text=" Invert              ", icon_value = custom_icons["invert"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeInvert"
                
                col = layout.column(align=True)
                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Light Falloff           ", icon_value = custom_icons["lightfalloff"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeLightFalloff"
        
                props = row.operator("node.add_node", text=" Mix RGB           ", icon_value = custom_icons["mixrgb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMixRGB"

                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text="RGB Curves       ", icon_value = custom_icons["rgbcurve"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeRGBCurve"

                ##### --------------------------------- Vector ------------------------------------------- ####
        
                layout.label(text="Vector:")

                col = layout.column(align=True)
                row = col.row(align=True)         
        
                props = row.operator("node.add_node", text=" Bump            ", icon_value = custom_icons["bump"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeBump"
        
        
                props = row.operator("node.add_node", text=" Mapping          ", icon_value = custom_icons["mapping"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMapping"

                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Normal          ", icon_value = custom_icons["normal"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeNormal"
        
                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Vector Transform   ", icon_value = custom_icons["vector_transform"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVectorTransform"
        
                props = row.operator("node.add_node", text=" Vector Curves    ", icon_value = custom_icons["vector"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVectorCurve"

                ##### --------------------------------- Input ------------------------------------------- ####
        
                layout.label(text="Input:")

                col = layout.column(align=True)
                row = col.row(align=True)        
        
                props = row.operator("node.add_node", text=" Attribute     ", icon_value = custom_icons["attribute"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeAttribute"
        
                props = row.operator("node.add_node", text=" Camera Data   ", icon_value = custom_icons["cameradata"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCameraData"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Geometry        ", icon_value = custom_icons["geometry"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeNewGeometry"
        
                col = layout.column(align=True)
                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Hair Info     ", icon_value = custom_icons["hairinfo"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeHairInfo"
        
                props = row.operator("node.add_node", text=" Layer Weight   ", icon_value = custom_icons["layerweight"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeLayerWeight"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Light Path    ", icon_value = custom_icons["lightpath"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeLightPath"
        
                props = row.operator("node.add_node", text=" Object Info    ", icon_value = custom_icons["objectinfo"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeObjectInfo"
        
                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Particle Info", icon_value = custom_icons["particleinfo"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeParticleInfo"
        
                props = row.operator("node.add_node", text=" RGB               ", icon_value = custom_icons["rgb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeRGB"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Tangent        ", icon_value = custom_icons["tangent"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTangent"
        
                props = row.operator("node.add_node", text=" Texture Coordinate", icon_value = custom_icons["texcoordinate"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexCoord"

                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" UV Map       ", icon_value = custom_icons["uvmap"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeUVMap"
        
                props = row.operator("node.add_node", text=" Value            ", icon_value = custom_icons["value"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeValue"

                row = col.row(align=True)
        
                props = row.operator("node.add_node", text=" Wireframe", icon_value = custom_icons["wireframe"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeWireframe"

                if context.space_data.shader_type == 'LINESTYLE':

                    props = row.operator("node.add_node", text=" UV along stroke", icon_value = custom_icons["uvalongstroke"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeUVALongStroke"

            

                ##### --------------------------------- Converter ------------------------------------------- ####
        
                layout.label(text="Converter:")

                col = layout.column(align=True)
                row = col.row(align=True)           
        
                props = row.operator("node.add_node", text=" Combine HSV    ", icon_value = custom_icons["combinehsv"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCombineHSV"        
         
                props = row.operator("node.add_node", text=" Combine RGB   ", icon_value = custom_icons["combinergb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCombineRGB"

                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Combine XYZ    ", icon_value = custom_icons["combinexyz"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCombineXYZ" 

                col = layout.column(align=True)
                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Separate HSV    ", icon_value = custom_icons["separatehsv"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeSeparateHSV"

                props = row.operator("node.add_node", text=" Separate RGB    ", icon_value = custom_icons["separatergb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeSeparateRGB" 
                
                row = col.row(align=True)      
        
                props = row.operator("node.add_node", text=" Separate XYZ    ", icon_value = custom_icons["separatexyz"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeSeparateXYZ" 

                col = layout.column(align=True)
                row = col.row(align=True)           
        
                props = row.operator("node.add_node", text=" Blackbody        ", icon_value = custom_icons["blackbody"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeBlackbody"        
        
                props = row.operator("node.add_node", text=" ColorRamp      ", icon_value = custom_icons["colorramp"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeValToRGB"

                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" Math              ", icon_value = custom_icons["math"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMath"
        
                props = row.operator("node.add_node", text=" RGB to BW        ", icon_value = custom_icons["rgbtobw"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeRGBToBW"
        
                col = layout.column(align=True)
                row = col.row(align=True)       
        
                props = row.operator("node.add_node", text=" Vector Math       ", icon_value = custom_icons["vectormath"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVectorMath"
        
                props = row.operator("node.add_node", text=" Wavelength      ", icon_value = custom_icons["wavelength"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeWavelength"

            ##### --------------------------------- Script ------------------------------------------- ####
        
                layout.label(text="Script:")

                col = layout.column(align=True)
                row = col.row(align=True) 
        
                props = row.operator("node.add_node", text=" Script            ", icon_value = custom_icons["script"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeScript"  

            ##### Icon Buttons 

            else: 
                ##### --------------------------------- Color ------------------------------------------- ####
        
                layout.label(text="Color:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["brightcontrast"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeBrightContrast"
        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["gamma"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeGamma"
 
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["huesaturation"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeHueSaturation"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["invert"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeInvert"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["lightfalloff"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeLightFalloff"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["mixrgb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMixRGB"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["rgbcurve"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeRGBCurve"

                ##### --------------------------------- Vector ------------------------------------------- ####
        
                layout.label(text="Vector:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["bump"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeBump"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["mapping"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMapping"
     
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["normal"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeNormal"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["vector_transform"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVectorTransform"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["vector"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVectorCurve"

                ##### --------------------------------- Input ------------------------------------------- ####
        
                layout.label(text="Input:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["attribute"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeAttribute"
   
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["cameradata"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCameraData"


        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["geometry"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeNewGeometry"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["hairinfo"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeHairInfo"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["layerweight"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeLayerWeight"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["lightpath"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeLightPath"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["objectinfo"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeObjectInfo"
        
                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["particleinfo"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeParticleInfo"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["rgb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeRGB"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["tangent"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTangent"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["texcoordinate"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeTexCoord"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["uvmap"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeUVMap"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["value"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeValue"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["wireframe"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeWireframe"

                if context.space_data.shader_type == 'LINESTYLE':

                    props = row.operator("node.add_node", text = "", icon_value = custom_icons["uvalongstroke"].icon_id)
                    props.use_transform = True
                    props.type = "ShaderNodeUVALongStroke"


                ##### --------------------------------- Converter ------------------------------------------- ####
        
                layout.label(text="Converter:")

                row = layout.row()
                row.alignment = 'LEFT'

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combinehsv"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCombineHSV"   
                
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combinergb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCombineRGB"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combinexyz"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeCombineXYZ"     
        
                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separatehsv"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeSeparateHSV"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separatergb"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeSeparateRGB"      
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separatexyz"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeSeparateXYZ"     
                
                row = layout.row()
                row.alignment = 'LEFT'      
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["blackbody"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeBlackbody"        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["colorramp"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeValToRGB"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["math"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeMath"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["rgbtobw"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeRGBToBW"    

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["vectormath"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeVectorMath"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["wavelength"].icon_id)
                props.use_transform = True
                props.type = "ShaderNodeWavelength"

            ##### --------------------------------- Script ------------------------------------------- ####
        
                layout.label(text="Script:")

                row = layout.row()
                row.alignment = 'LEFT'        
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["script"].icon_id)
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

                props = row.operator("node.add_node", text=" Combine HSVA         ", icon_value = custom_icons["combinehsv"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCombHSVA"
            
                props = row.operator("node.add_node", text=" Combine RGBA         ", icon_value = custom_icons["combinergb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCombRGBA"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Combine YCbCrA       ", icon_value = custom_icons["combineycbcra"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCombYCCA"

                props = row.operator("node.add_node", text=" Combine YUVA       ", icon_value = custom_icons["combineyuva"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeCombYUVA"

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Separate HSVA         ", icon_value = custom_icons["separatehsv"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeSepHSVA"

                props = row.operator("node.add_node", text=" Separate RGBA         ", icon_value = custom_icons["separatergb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSepRGBA"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Separate YCbCrA       ", icon_value = custom_icons["separateycbcra"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeSepYCCA"

                props = row.operator("node.add_node", text=" Separate YUVA       ", icon_value = custom_icons["separateyuva"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSepYUVA"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Set Alpha         ", icon_value = custom_icons["alpha"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSetAlpha"
                
                props = row.operator("node.add_node", text=" Alpha Convert          ", icon_value = custom_icons["alphaconvert"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodePremulKey"

                row = col.row(align=True) 

                props = row.operator("node.add_node", text=" RGB to BW          ", icon_value = custom_icons["rgbtobw"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeRGBToBW"

                props = row.operator("node.add_node", text=" Color Ramp       ", icon_value = custom_icons["colorramp"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeValToRGB"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" ID Mask        ", icon_value = custom_icons["node_mask"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeIDMask"
            
                props = row.operator("node.add_node", text=" Math         ", icon_value = custom_icons["math"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMath"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Switch View         ", icon_value = custom_icons["switchview"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSwitchView"
        
                # ------------------------------- Filter -----------------------------

                layout.label(text="Filter:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Bilateral Blur          ", icon_value = custom_icons["bilateralblur"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBilateralblur"

                props = row.operator("node.add_node", text=" Blur      ", icon_value = custom_icons["blur"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeBlur"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Bokeh Blur         ", icon_value = custom_icons["bokeh_blur"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeBokehBlur"

                props = row.operator("node.add_node", text=" Directional Blur     ", icon_value = custom_icons["directionalblur"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDBlur"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Vector Blur       ", icon_value = custom_icons["vector_blur"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeVecBlur"

                props = row.operator("node.add_node", text=" Defocus         ", icon_value = custom_icons["defocus"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDefocus"

                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Despeckle       ", icon_value = custom_icons["despeckle"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDespeckle"

                props = row.operator("node.add_node", text=" Dilate / Erode      ", icon_value = custom_icons["erode"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDilateErode"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Filter        ", icon_value = custom_icons["filter"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeFilter"
            
                props = row.operator("node.add_node", text=" Glare         ", icon_value = custom_icons["glare"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeGlare"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Inpaint        ", icon_value = custom_icons["inpaint"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeInpaint"
            
                props = row.operator("node.add_node", text=" Pixelate         ", icon_value = custom_icons["pixelated"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodePixelate"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Sunbeams       ", icon_value = custom_icons["sunbeams"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeSunBeams"
                

             # ------------------------------- Vector -----------------------------

                layout.label(text="Vector:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Map Range         ", icon_value = custom_icons["range"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMapRange"

                props = row.operator("node.add_node", text=" Map Value     ", icon_value = custom_icons["value"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMapValue"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Normal         ", icon_value = custom_icons["normal"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeNormal"
            
                props = row.operator("node.add_node", text=" Normalize        ", icon_value = custom_icons["normalize"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeNormalize"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Vector Curves      ", icon_value = custom_icons["vector"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCurveVec"

            # ------------------------------- Matte -----------------------------

                layout.label(text="Matte:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Box Mask         ", icon_value = custom_icons["boxmask"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBoxMask"

                props = row.operator("node.add_node", text=" Double Edge Mask     ", icon_value = custom_icons["doubleedgemask"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDoubleEdgeMask"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Ellipse Mask       ", icon_value = custom_icons["ellipsemask"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeEllipseMask"

                col = layout.column(align=True)
                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Channel Key      ", icon_value = custom_icons["channel"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeChannelMatte"     
        
                props = row.operator("node.add_node", text=" Chroma Key         ", icon_value = custom_icons["chroma"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeChromaMatte"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Color Key         ", icon_value = custom_icons["color"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeColorMatte"

                props = row.operator("node.add_node", text=" Difference Key       ", icon_value = custom_icons["difference"].icon_id)   
                props.use_transform = True
                props.type = "CompositorNodeDiffMatte"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Distance Key      ", icon_value = custom_icons["node_distance"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDistanceMatte"

                props = row.operator("node.add_node", text=" Keying         ", icon_value = custom_icons["keying"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeKeying"

                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Keying Screen       ", icon_value = custom_icons["keyingscreen"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeKeyingScreen"

                props = row.operator("node.add_node", text=" Luminance Key        ", icon_value = custom_icons["luminance"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeLumaMatte"

            # ------------------------------- Distort -----------------------------

                layout.label(text="Distort:")

                col = layout.column(align=True)
                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Corner Pin        ", icon_value = custom_icons["cornerpin"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCornerPin"

                props = row.operator("node.add_node", text=" Crop     ", icon_value = custom_icons["crop"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCrop"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Displace        ", icon_value = custom_icons["displace"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeDisplace"
            
                props = row.operator("node.add_node", text=" Flip         ", icon_value = custom_icons["flip"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeFlip"

                col = layout.column(align=True)
                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Lens Distortion       ", icon_value = custom_icons["lensdistort"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeLensdist"

                props = row.operator("node.add_node", text=" Map UV     ", icon_value = custom_icons["uvmap"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMapUV"

                row = col.row(align=True)  
        
                props = row.operator("node.add_node", text=" Movie Distortion     ", icon_value = custom_icons["moviedistort"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeMovieDistortion"
            
                props = row.operator("node.add_node", text=" Plane Track Deform       ", icon_value = custom_icons["planetrackdeform"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodePlaneTrackDeform"

                col = layout.column(align=True)
                row = col.row(align=True)  
            
                props = row.operator("node.add_node", text=" Rotate         ", icon_value = custom_icons["node_rotate"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeRotate"
            
                props = row.operator("node.add_node", text=" Scale       ", icon_value = custom_icons["node scale"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeScale"

                row = col.row(align=True)  
      
                props = row.operator("node.add_node", text=" Transform       ", icon_value = custom_icons["transform"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTransform"

                props = row.operator("node.add_node", text=" Translate       ", icon_value = custom_icons["node_move"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeTranslate"

                col = layout.column(align=True)
                row = col.row(align=True)  

                props = row.operator("node.add_node", text=" Stabilize 2D        ", icon_value = custom_icons["stabilize2d"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeStabilize"

            #### Icon Buttons

            else: 
            # ------------------------------- Converter -----------------------------

                layout.label(text="Converter:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combinehsv"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCombHSVA"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combinergb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCombRGBA"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combineycbcra"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCombYCCA"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["combineyuva"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeCombYUVA"

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separatehsv"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeSepHSVA"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separatergb"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSepRGBA"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separateycbcra"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeSepYCCA"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["separateyuva"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSepYUVA"

                row = layout.row()
                row.alignment = 'LEFT'
                
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["alpha"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSetAlpha"  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["alphaconvert"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodePremulKey"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["rgbtobw"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeRGBToBW"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["colorramp"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeValToRGB"   
                
                row = layout.row()
                row.alignment = 'LEFT'            
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_mask"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeIDMask"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["math"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMath"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["switchview"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSwitchView"
        
                # ------------------------------- Filter -----------------------------

                layout.label(text="Filter:")

                row = layout.row()
                row.alignment = 'LEFT'    

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["bilateralblur"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBilateralblur"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["blur"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeBlur"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["bokeh_blur"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeBokehBlur"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["directionalblur"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDBlur"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["vector_blur"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeVecBlur"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["defocus"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDefocus"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["despeckle"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDespeckle"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["erode"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDilateErode"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["filter"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeFilter"
    
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["glare"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeGlare"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["inpaint"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeInpaint"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["pixelated"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodePixelate"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["sunbeams"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeSunBeams"

                row = layout.row()
                row.alignment = 'LEFT'  

                

             # ------------------------------- Vector -----------------------------

                layout.label(text="Vector:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["range"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMapRange"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["value"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMapValue"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["normal"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeNormal"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["normalize"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeNormalize"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["vector"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCurveVec"

            # ------------------------------- Matte -----------------------------

                layout.label(text="Matte:")

                row = layout.row()
                row.alignment = 'LEFT'   

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["boxmask"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeBoxMask"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["doubleedgemask"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDoubleEdgeMask"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["ellipsemask"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeEllipseMask"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["channel"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeChannelMatte" 
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["chroma"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeChromaMatte"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["color"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeColorMatte"
      
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["difference"].icon_id)   
                props.use_transform = True
                props.type = "CompositorNodeDiffMatte"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_distance"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeDistanceMatte" 
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["keying"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeKeying"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["keyingscreen"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeKeyingScreen"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["luminance"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeLumaMatte"

            # ------------------------------- Distort -----------------------------

                layout.label(text="Distort:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["cornerpin"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCornerPin"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["crop"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeCrop"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["displace"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeDisplace"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["flip"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeFlip"

                row = layout.row()
                row.alignment = 'LEFT'  
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["lensdistort"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeLensdist"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["uvmap"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeMapUV"
        
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["moviedistort"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeMovieDistortion"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["planetrackdeform"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodePlaneTrackDeform"

                row = layout.row()
                row.alignment = 'LEFT'  
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_rotate"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeRotate"
            
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node scale"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeScale"
                    
                props = row.operator("node.add_node", text = "", icon_value = custom_icons["transform"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeTransform"

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["node_move"].icon_id) 
                props.use_transform = True
                props.type = "CompositorNodeTranslate"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text = "", icon_value = custom_icons["stabilize2d"].icon_id)  
                props.use_transform = True
                props.type = "CompositorNodeStabilize"

#--------------------------------------------------------------------- Texture Node Tree --------------------------------------------------------------------------------

        elif context.space_data.tree_type == 'TextureNodeTree':

            #### Text Buttons

            if not scene.UItweaksNodes.icon_or_text: 

                layout.label(text="Converter:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" Color Ramp         ", icon_value = custom_icons["colorramp"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeValToRGB"

                props = row.operator("node.add_node", text=" Distance         ", icon_value = custom_icons["node_distance"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeDistance"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Math        ", icon_value = custom_icons["math"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeMath"

                props = row.operator("node.add_node", text=" RGB to BW        ", icon_value = custom_icons["rgbtobw"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeRGBToBW"

                row = col.row(align=True)   

                props = row.operator("node.add_node", text=" Value to Normal         ", icon_value = custom_icons["normal"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeValToNor"

                layout.label(text="Distort:")

                col = layout.column(align=True)
                row = col.row(align=True)    

                props = row.operator("node.add_node", text=" At        ", icon_value = custom_icons["node_at"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeAt"

                props = row.operator("node.add_node", text=" Rotate         ", icon_value = custom_icons["node_rotate"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeRotate"

                row = col.row(align=True)

                props = row.operator("node.add_node", text=" Scale        ", icon_value = custom_icons["node scale"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeScale"

                props = row.operator("node.add_node", text=" translate       ", icon_value = custom_icons["node_move"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeTranslate"

            #### Icon Buttons

            else: 

                layout.label(text="Converter:")

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon_value = custom_icons["colorramp"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeValToRGB"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_distance"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeDistance"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["math"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeMath"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["rgbtobw"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeRGBToBW"

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text="", icon_value = custom_icons["normal"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeValToNor"

                layout.label(text="Distort:")

                row = layout.row()
                row.alignment = 'LEFT'  

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_at"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeAt"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_rotate"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeRotate"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node scale"].icon_id)
                props.use_transform = True
                props.type = "TextureNodeScale"

                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_move"].icon_id)
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

            props = row.operator("node.add_node", text=" Frame       ", icon_value = custom_icons["frame"].icon_id)
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text=" Reroute      ", icon_value = custom_icons["reroute"].icon_id)
            props.use_transform = True
            props.type = "NodeReroute"

            if context.space_data.tree_type == 'CompositorNodeTree':
                row = col.row(align=True)
                props = row.operator("node.add_node", text=" Switch      ", icon_value = custom_icons["node_switch"].icon_id)
                props.use_transform = True
                props.type = "CompositorNodeSwitch"

        else: 

            ##### --------------------------------- Group ------------------------------------------- ####
        
            layout.label(text="Group:")

            row = layout.row()
            row.alignment = 'LEFT'        

            row.operator("node.group_edit", text = "", icon_value = custom_icons["editgroup"].icon_id).exit = False
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

            props = row.operator("node.add_node", text = "", icon_value = custom_icons["frame"].icon_id)
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text = "", icon_value = custom_icons["reroute"].icon_id)
            props.use_transform = True
            props.type = "NodeReroute"

            if context.space_data.tree_type == 'CompositorNodeTree':
                props = row.operator("node.add_node", text="", icon_value = custom_icons["node_switch"].icon_id)
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

    # All the Icons

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

    custom_icons.load("curve_time", os.path.join(icons_dir, "curve_time.png"), 'IMAGE')
    custom_icons.load("clouds", os.path.join(icons_dir, "clouds.png"), 'IMAGE')
    custom_icons.load("wood", os.path.join(icons_dir, "wood.png"), 'IMAGE')
    custom_icons.load("blend", os.path.join(icons_dir, "blend.png"), 'IMAGE')
    custom_icons.load("marble", os.path.join(icons_dir, "marble.png"), 'IMAGE')
    custom_icons.load("distortednoise", os.path.join(icons_dir, "distortednoise.png"), 'IMAGE')
    custom_icons.load("stucci", os.path.join(icons_dir, "stucci.png"), 'IMAGE')

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

    custom_icons.load("alpha", os.path.join(icons_dir, "alpha.png"), 'IMAGE')
    custom_icons.load("alphaconvert", os.path.join(icons_dir, "alphaconvert.png"), 'IMAGE')
    custom_icons.load("bokeh_image", os.path.join(icons_dir, "bokeh_image.png"), 'IMAGE')
    custom_icons.load("node_mask", os.path.join(icons_dir, "node_mask.png"), 'IMAGE')
    custom_icons.load("node_movie", os.path.join(icons_dir, "node_movie.png"), 'IMAGE')
    custom_icons.load("node_texture", os.path.join(icons_dir, "node_texture.png"), 'IMAGE')
    custom_icons.load("render_layer", os.path.join(icons_dir, "render_layer.png"), 'IMAGE')
    custom_icons.load("uvalongstroke", os.path.join(icons_dir, "uvalongstroke.png"), 'IMAGE')
    custom_icons.load("node_time", os.path.join(icons_dir, "node_time.png"), 'IMAGE')
    custom_icons.load("trackposition", os.path.join(icons_dir, "trackposition.png"), 'IMAGE')

    # Output

    custom_icons.load("material_output", os.path.join(icons_dir, "material_output.png"), 'IMAGE')
    custom_icons.load("lamp_output", os.path.join(icons_dir, "lamp_output.png"), 'IMAGE')
    custom_icons.load("world_output", os.path.join(icons_dir, "world_output.png"), 'IMAGE')

    custom_icons.load("compositeoutput", os.path.join(icons_dir, "composite_output.png"), 'IMAGE')
    custom_icons.load("fileoutput", os.path.join(icons_dir, "fileoutput.png"), 'IMAGE')
    custom_icons.load("linestyle_output", os.path.join(icons_dir, "linestyle_output.png"), 'IMAGE')
    custom_icons.load("node_viewer", os.path.join(icons_dir, "node_viewer.png"), 'IMAGE')
    custom_icons.load("node_viewersplit", os.path.join(icons_dir, "node_viewersplit.png"), 'IMAGE')
    custom_icons.load("node_levels", os.path.join(icons_dir, "node_levels.png"), 'IMAGE')
    custom_icons.load("output", os.path.join(icons_dir, "output.png"), 'IMAGE')

    # Filter

    custom_icons.load("bilateralblur", os.path.join(icons_dir, "bilateral_blur.png"), 'IMAGE')
    custom_icons.load("blur", os.path.join(icons_dir, "blur.png"), 'IMAGE')
    custom_icons.load("bokeh_blur", os.path.join(icons_dir, "bokeh_blur.png"), 'IMAGE')
    custom_icons.load("vector_blur", os.path.join(icons_dir, "vector_blur.png"), 'IMAGE')

    custom_icons.load("pixelated", os.path.join(icons_dir, "pixelated.png"), 'IMAGE')
    custom_icons.load("filter", os.path.join(icons_dir, "filter.png"), 'IMAGE')
    custom_icons.load("glare", os.path.join(icons_dir, "glare.png"), 'IMAGE')
    custom_icons.load("sunbeams", os.path.join(icons_dir, "sunbeams.png"), 'IMAGE')
    custom_icons.load("inpaint", os.path.join(icons_dir, "inpaint.png"), 'IMAGE')  
    custom_icons.load("erode", os.path.join(icons_dir, "erode.png"), 'IMAGE')
    custom_icons.load("directionalblur", os.path.join(icons_dir, "directionalblur.png"), 'IMAGE')
    custom_icons.load("defocus", os.path.join(icons_dir, "defocus.png"), 'IMAGE')
    custom_icons.load("despeckle", os.path.join(icons_dir, "despeckle.png"), 'IMAGE')

    # Shaders

    custom_icons.load("node_principled_shader", os.path.join(icons_dir, "node_principled_shader.png"), 'IMAGE')

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

    custom_icons.load("backgroundshader", os.path.join(icons_dir, "backgroundshader.png"), 'IMAGE')

    # Color

    custom_icons.load("brightcontrast", os.path.join(icons_dir, "brightcontrast.png"), 'IMAGE')
    custom_icons.load("gamma", os.path.join(icons_dir, "gamma.png"), 'IMAGE')
    custom_icons.load("huesaturation", os.path.join(icons_dir, "huesaturation.png"), 'IMAGE')
    custom_icons.load("invert", os.path.join(icons_dir, "invert.png"), 'IMAGE')
    custom_icons.load("lightfalloff", os.path.join(icons_dir, "lightfalloff.png"), 'IMAGE')
    custom_icons.load("mixrgb", os.path.join(icons_dir, "mixrgb.png"), 'IMAGE')
    custom_icons.load("rgbcurve", os.path.join(icons_dir, "rgbcurve.png"), 'IMAGE')
    
    custom_icons.load("colorbalance", os.path.join(icons_dir, "colorbalance.png"), 'IMAGE')
    custom_icons.load("zcombine", os.path.join(icons_dir, "zcombine.png"), 'IMAGE')
    custom_icons.load("tonemap", os.path.join(icons_dir, "tonemap.png"), 'IMAGE')
    custom_icons.load("colorcorrection", os.path.join(icons_dir, "colorcorrection.png"), 'IMAGE')

    # Vector

    custom_icons.load("bump", os.path.join(icons_dir, "bump.png"), 'IMAGE')
    custom_icons.load("mapping", os.path.join(icons_dir, "mapping.png"), 'IMAGE')
    custom_icons.load("normal", os.path.join(icons_dir, "normal.png"), 'IMAGE')
    custom_icons.load("normalmap", os.path.join(icons_dir, "normalmap.png"), 'IMAGE')
    custom_icons.load("vector_transform", os.path.join(icons_dir, "vector_transform.png"), 'IMAGE')
    custom_icons.load("vector", os.path.join(icons_dir, "vector.png"), 'IMAGE')
    custom_icons.load("normalize", os.path.join(icons_dir, "normalize.png"), 'IMAGE')
    custom_icons.load("range", os.path.join(icons_dir, "range.png"), 'IMAGE')

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

    custom_icons.load("switchview", os.path.join(icons_dir, "switchview.png"), 'IMAGE')
    custom_icons.load("combineyuva", os.path.join(icons_dir, "combineyuva.png"), 'IMAGE')
    custom_icons.load("combineycbcra", os.path.join(icons_dir, "combineycbcra.png"), 'IMAGE')   
    custom_icons.load("separateyuva", os.path.join(icons_dir, "separateyuva.png"), 'IMAGE')
    custom_icons.load("separateycbcra", os.path.join(icons_dir, "separateycbcra.png"), 'IMAGE')

    custom_icons.load("node_distance", os.path.join(icons_dir, "node_distance.png"), 'IMAGE')

    # Distort

    custom_icons.load("node_move", os.path.join(icons_dir, "node_move.png"), 'IMAGE')
    custom_icons.load("node_rotate", os.path.join(icons_dir, "node_rotate.png"), 'IMAGE')   
    custom_icons.load("node scale", os.path.join(icons_dir, "node scale.png"), 'IMAGE')
    custom_icons.load("node_at", os.path.join(icons_dir, "node_at.png"), 'IMAGE')

    custom_icons.load("transform", os.path.join(icons_dir, "transform.png"), 'IMAGE')
    custom_icons.load("crop", os.path.join(icons_dir, "crop.png"), 'IMAGE')
    custom_icons.load("displace", os.path.join(icons_dir, "displace.png"), 'IMAGE')
    custom_icons.load("flip", os.path.join(icons_dir, "flip.png"), 'IMAGE')
    custom_icons.load("lensdistort", os.path.join(icons_dir, "lensdistort.png"), 'IMAGE')
    custom_icons.load("moviedistort", os.path.join(icons_dir, "moviedistort.png"), 'IMAGE')
    custom_icons.load("stabilize2d", os.path.join(icons_dir, "stabilize2d.png"), 'IMAGE')
    custom_icons.load("planetrackdeform", os.path.join(icons_dir, "planetrackdeform.png"), 'IMAGE')
    custom_icons.load("cornerpin", os.path.join(icons_dir, "cornerpin.png"), 'IMAGE')

    # Script

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
    custom_icons.load("node_switch", os.path.join(icons_dir, "node_switch.png"), 'IMAGE')

    # Matte

    custom_icons.load("boxmask", os.path.join(icons_dir, "boxmask.png"), 'IMAGE')
    custom_icons.load("ellipsemask", os.path.join(icons_dir, "ellipsemask.png"), 'IMAGE')
    custom_icons.load("keying", os.path.join(icons_dir, "keying.png"), 'IMAGE')
    custom_icons.load("keyingscreen", os.path.join(icons_dir, "keyingscreen.png"), 'IMAGE')
    custom_icons.load("luminance", os.path.join(icons_dir, "luminance.png"), 'IMAGE')
    custom_icons.load("color", os.path.join(icons_dir, "color.png"), 'IMAGE')
    custom_icons.load("chroma", os.path.join(icons_dir, "chroma.png"), 'IMAGE')
    custom_icons.load("difference", os.path.join(icons_dir, "difference.png"), 'IMAGE')
    custom_icons.load("doubleedgemask", os.path.join(icons_dir, "doubleedgemask.png"), 'IMAGE')
    custom_icons.load("channel", os.path.join(icons_dir, "channel.png"), 'IMAGE')

    # DEVELOPMENTPLACEHOLDER

    #custom_icons.load("placeholder", os.path.join(icons_dir, "placeholder.png"), 'IMAGE')


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