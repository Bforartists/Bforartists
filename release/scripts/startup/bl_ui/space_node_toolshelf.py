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
import bpy
from bpy import context

# The text or icon prop is in the properties sidebar
class NODES_PT_Prop(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Iconortext"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene
        layout.prop(addon_prefs,"Node_text_or_icon")


###-------------- Input tab --------------

#Input nodes tab, connect panel. Just in shader mode
class NODES_PT_Input_connect(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Connect"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)      
        
            props = col.operator("node.add_node", text=" Add                   ", icon = "NODE_ADD_SHADER")
            props.use_transform = True
            props.type = "ShaderNodeAddShader" 

            props = col.operator("node.add_node", text=" Mix                   ", icon = "NODE_MIXSHADER")
            props.use_transform = True
            props.type = "ShaderNodeMixShader"   

            props = col.operator("node.add_node", text=" Normal Map     ", icon = "NODE_NORMALMAP")
            props.use_transform = True
            props.type = "ShaderNodeNormalMap"

        #### Icon Buttons

        else:

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

#Input nodes tab, textures common panel. Shader Mode
class NODES_PT_Input_input_shader(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

        ##### --------------------------------- Textures common ------------------------------------------- ####     

            col = layout.column(align=True)     
        
            props = col.operator("node.add_node", text=" Image               ", icon = "FILE_IMAGE")    
            props.use_transform = True
            props.type = "ShaderNodeTexImage"
              
            props = col.operator("node.add_node", text=" Environment    ", icon = "NODE_ENVIRONMENT")
            props.use_transform = True
            props.type = "ShaderNodeTexEnvironment"         

        #### Icon Buttons

        else:

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text = "", icon = "FILE_IMAGE")  
        
            props.use_transform = True
            props.type = "ShaderNodeTexImage"

            props = row.operator("node.add_node", text = "", icon = "NODE_ENVIRONMENT")
            props.use_transform = True
            props.type = "ShaderNodeTexEnvironment"


#Input nodes tab, textures common panel. Compositing mode
class NODES_PT_Input_input_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
        
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon: 

            col = layout.column(align=True)  

            props = col.operator("node.add_node", text=" Image              ", icon = "FILE_IMAGE")  
            props.use_transform = True
            props.type = "CompositorNodeImage"

            props = col.operator("node.add_node", text=" Texture             ", icon = "TEXTURE")
            props.use_transform = True
            props.type = "CompositorNodeTexture"

            props = col.operator("node.add_node", text=" Mask                 ", icon = "MOD_MASK") 
            props.use_transform = True
            props.type = "CompositorNodeMask"
            
            props = col.operator("node.add_node", text=" Movie Clip        ", icon = "FILE_MOVIE")
            props.use_transform = True
            props.type = "CompositorNodeMovieClip"

            col = layout.column(align=True) 
            
            props = col.operator("node.add_node", text=" Render Layers  ", icon = "RENDERLAYERS")
            props.use_transform = True
            props.type = "CompositorNodeRLayers"
            
            props = col.operator("node.add_node", text=" RGB                 ", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "CompositorNodeRGB"

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" Mix                  ", icon = "NODE_MIXRGB") 
            props.use_transform = True
            props.type = "CompositorNodeMixRGB"
                          

        #### Image Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'   

            props = row.operator("node.add_node", text = "", icon = "FILE_IMAGE")  
            props.use_transform = True
            props.type = "CompositorNodeImage"

            props = row.operator("node.add_node", text = "", icon = "TEXTURE")
            props.use_transform = True
            props.type = "CompositorNodeTexture"

            row = layout.row()
            row.alignment = 'LEFT' 

            props = row.operator("node.add_node", text = "", icon = "MOD_MASK") 
            props.use_transform = True
            props.type = "CompositorNodeMask"
            
            props = row.operator("node.add_node", text = "", icon = "FILE_MOVIE")
            props.use_transform = True
            props.type = "CompositorNodeMovieClip"
            
            props = row.operator("node.add_node", text = "", icon = "RENDERLAYERS") 
            props.use_transform = True
            props.type = "CompositorNodeRLayers"
            
            props = row.operator("node.add_node", text = "", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "CompositorNodeRGB"

            row = layout.row()
            row.alignment = 'LEFT' 

            props = row.operator("node.add_node", text = "", icon = "NODE_MIXRGB") 
            props.use_transform = True
            props.type = "CompositorNodeMixRGB"


#Input nodes tab, textures common panel. Texture mode
class NODES_PT_Input_input_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)  

            props = col.operator("node.add_node", text=" Image               ", icon = "FILE_IMAGE")  
            props.use_transform = True
            props.type = "TextureNodeImage"

            props = col.operator("node.add_node", text=" Texture             ", icon = "TEXTURE")
            props.use_transform = True
            props.type = "TextureNodeTexture"


        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'       

            props = row.operator("node.add_node", text="", icon = "FILE_IMAGE")  
            props.use_transform = True
            props.type = "TextureNodeImage"

            props = row.operator("node.add_node", text="", icon = "TEXTURE")
            props.use_transform = True
            props.type = "TextureNodeTexture"



 

#Input nodes tab, textures advanced panel. Just in Texture mode
class NODES_PT_Input_textures_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Textures"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in shader and texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" Blend                 ", icon = "BLEND_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexBlend"

            props = col.operator("node.add_node", text=" Clouds               ", icon = "CLOUD_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexClouds"

            props = col.operator("node.add_node", text=" Distorted Noise ", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexDistNoise"

            props = col.operator("node.add_node", text=" Magic               ", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexMagic"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Marble              ", icon = "MARBLE_TEX")
            props.use_transform = True  
            props.type = "TextureNodeTexMarble"

            props = col.operator("node.add_node", text=" Musgrave          ", icon = "MUSGRAVE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexMusgrave"

            props = col.operator("node.add_node", text=" Noise                 ", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexNoise"

            props = col.operator("node.add_node", text=" Stucci                ", icon = "STUCCI_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexStucci"

            col = layout.column(align=True) 
                 
            props = col.operator("node.add_node", text=" Voronoi             ", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexVoronoi"

            props = col.operator("node.add_node", text=" Wood                ", icon = "WOOD_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexWood"

        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text="", icon = "NODE_BLEND")
            props.use_transform = True
            props.type = "TextureNodeTexBlend"

            props = row.operator("node.add_node", text="", icon = "CLOUD_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexClouds"

            props = row.operator("node.add_node", text="", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexDistNoise"

            props = row.operator("node.add_node", text="", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexMagic"

            row = layout.row()
            row.alignment = 'LEFT'    

            props = row.operator("node.add_node", text="", icon = "MARBLE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexMarble"

            props = row.operator("node.add_node", text="", icon = "MUSGRAVE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexMusgrave"

            props = row.operator("node.add_node", text="", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexNoise"

            props = row.operator("node.add_node", text="", icon = "STUCCI_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexStucci"

            row = layout.row()
            row.alignment = 'LEFT' 

            props = row.operator("node.add_node", text="", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexVoronoi"

            props = row.operator("node.add_node", text="", icon = "WOOD_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexWood"


#Input nodes tab, Shader panel with prinicipled shader. Just in shader mode with Object and World mode
class NODES_PT_Input_shader(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and context.space_data.shader_type in ( 'OBJECT', 'WORLD')) # Just in shader mode, Just in Object and World
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            if context.space_data.shader_type == 'OBJECT':

                col = layout.column(align=True)
                    
                props = col.operator("node.add_node", text=" Principled         ", icon = "NODE_PRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeBsdfPrincipled"

            elif context.space_data.shader_type == 'WORLD':

                col = layout.column(align=True)     

                props = col.operator("node.add_node", text=" Background    ", icon = "NODE_BACKGROUNDSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBackground"
                
            props = col.operator("node.add_node", text=" Principled Volume       ", icon = "NODE_PRINCIPLED")
            props.use_transform = True
            props.type = "ShaderNodeVolumePrincipled"


        #### Icon Buttons

        else:

            if context.space_data.shader_type == 'OBJECT':

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text="", icon = "NODE_PRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeBsdfPrincipled"

            elif context.space_data.shader_type == 'WORLD':

                row = layout.row()
                row.alignment = 'LEFT' 

                props = row.operator("node.add_node", text = "", icon = "NODE_BACKGROUNDSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBackground"


#Input nodes tab, Shader common panel. Just in shader mode with Object mode
class NODES_PT_Input_shader_common(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Shader Common"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree'and context.space_data.shader_type == 'OBJECT') # Just in shader mode with Object mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

#--------------------------------------------------------------------- Shader Node Tree --------------------------------------------------------------------------------

        if not addon_prefs.Node_text_or_icon:

            if context.space_data.shader_type == 'OBJECT':

                col = layout.column(align=True)

                props = col.operator("node.add_node", text=" Diffuse               ", icon = "NODE_DIFFUSESHADER")
                props.use_transform = True 
                props.type = "ShaderNodeBsdfDiffuse"
        
                props = col.operator("node.add_node", text=" Emission           ", icon = "NODE_EMISSION")
                props.use_transform = True
                props.type = "ShaderNodeEmission"

                props = col.operator("node.add_node", text=" Fresnel              ", icon = "NODE_FRESNEL")
                props.use_transform = True
                props.type = "ShaderNodeFresnel"
        
                props = col.operator("node.add_node", text=" Glass                  ", icon = "NODE_GLASSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfGlass"   

                col = layout.column(align=True)
         
                props = col.operator("node.add_node", text=" Glossy                ", icon = "NODE_GLOSSYSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfGlossy"
        
                props = col.operator("node.add_node", text=" Refraction         ", icon = "NODE_REFRACTIONSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfRefraction"
         
                props = col.operator("node.add_node", text=" Subsurface Scattering ", icon = "NODE_SSS")
                props.use_transform = True
                props.type = "ShaderNodeSubsurfaceScattering"
        
                props = col.operator("node.add_node", text=" Toon                    ", icon = "NODE_TOONSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfToon"

                col = layout.column(align=True)
        
                props = col.operator("node.add_node", text=" Translucent       ", icon = "NODE_TRANSLUCENT")
                props.use_transform = True
                props.type = "ShaderNodeBsdfTranslucent"

                props = col.operator("node.add_node", text=" Transparent      ", icon = "NODE_TRANSPARENT")
                props.use_transform = True
                props.type = "ShaderNodeBsdfTransparent"

                props = col.operator("node.add_node", text=" Velvet              ", icon = "NODE_VELVET")
                props.use_transform = True
                props.type = "ShaderNodeBsdfVelvet"


        #### Icon Buttons

        else:

            if context.space_data.shader_type == 'OBJECT':

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


#Input nodes tab, Shader Advanced panel. Just in shader mode
class NODES_PT_Input_shader_advanced(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Shader Advanced"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        if not addon_prefs.Node_text_or_icon:

            if context.space_data.shader_type == 'OBJECT':

                col = layout.column(align=True) 
                
                props = col.operator("node.add_node", text=" Ambient Occlusion  ", icon = "NODE_AMBIENT_OCCLUSION")
                props.use_transform = True
                props.type = "ShaderNodeAmbientOcclusion"         
        
                props = col.operator("node.add_node", text=" Anisotopic         ", icon = "NODE_ANISOTOPIC")
                props.use_transform = True
                props.type = "ShaderNodeBsdfAnisotropic"
        
                props = col.operator("node.add_node", text=" Hair                   ", icon = "HAIR")
                props.use_transform = True
                props.type = "ShaderNodeBsdfHair"       
        
                props = col.operator("node.add_node", text=" Holdout            ", icon = "NODE_HOLDOUTSHADER")
                props.use_transform = True
                props.type = "ShaderNodeHoldout"

            col = layout.column(align=True)
         
            props = col.operator("node.add_node", text=" Volume Absorption ", icon = "NODE_VOLUMEABSORPTION")
            props.use_transform = True
            props.type = "ShaderNodeVolumeAbsorption"
        
            props = col.operator("node.add_node", text=" Volume Scatter ", icon = "NODE_VOLUMESCATTER")
            props.use_transform = True
            props.type = "ShaderNodeVolumeScatter"

        #### Icon Buttons
                
        else:

            if context.space_data.shader_type == 'OBJECT':

                row = layout.row()
                row.alignment = 'LEFT'        

                props = row.operator("node.add_node", text = "", icon = "NODE_ANISOTOPIC")
                props.use_transform = True
                props.type = "ShaderNodeBsdfAnisotropic"
  
                props = row.operator("node.add_node", text = "", icon = "NODE_AMBIENT_OCCLUSION")
                props.use_transform = True
                props.type = "ShaderNodeAmbientOcclusion"
        
                props = row.operator("node.add_node", text = "", icon = "HAIR")
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

#Input nodes tab, textures advanced panel. Just in shader mode
class NODES_PT_Input_textures_shader(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Textures"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader and texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Brick                ", icon = "NODE_BRICK")
            props.use_transform = True
            props.type = "ShaderNodeTexBrick"

            props = col.operator("node.add_node", text=" Checker           ", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"

            props = col.operator("node.add_node", text=" Gradient           ", icon = "NODE_GRADIENT")
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"

            props = col.operator("node.add_node", text=" Magic               ", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Musgrave         ", icon = "MUSGRAVE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMusgrave"
                
            props = col.operator("node.add_node", text=" Noise                ", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"

            props = col.operator("node.add_node", text=" Sky                    ", icon = "NODE_SKY")
            props.use_transform = True
            props.type = "ShaderNodeTexSky"

            props = col.operator("node.add_node", text=" Point Density   ", icon = "NODE_POINTCLOUD")
            props.use_transform = True
            props.type = "ShaderNodeTexPointDensity"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Wave                ", icon = "NODE_WAVES")
            props.use_transform = True
            props.type = "ShaderNodeTexWave"
        
            props = col.operator("node.add_node", text=" Voronoi             ", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"

        #### Icon Buttons

        else:
        
            row = layout.row()
            row.alignment = 'LEFT'

            props = row.operator("node.add_node", text = "", icon = "NODE_BRICK")
            props.use_transform = True
            props.type = "ShaderNodeTexBrick"

            props = row.operator("node.add_node", text = "", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"

            props = row.operator("node.add_node", text = "", icon = "NODE_GRADIENT")
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"

            props = row.operator("node.add_node", text = "", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"

            row = layout.row()
            row.alignment = 'LEFT' 

            props = row.operator("node.add_node", text = "", icon = "MUSGRAVE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMusgrave"

            props = row.operator("node.add_node", text = "", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"

            props = row.operator("node.add_node", text = "", icon = "NODE_POINTCLOUD")
            props.use_transform = True
            props.type = "ShaderNodeTexPointDensity"

            props = row.operator("node.add_node", text = "", icon = "NODE_SKY")
            props.use_transform = True
            props.type = "ShaderNodeTexSky"

            row = layout.row()
            row.alignment = 'LEFT' 
        
            props = row.operator("node.add_node", text = "", icon = "NODE_WAVES")
            props.use_transform = True
            props.type = "ShaderNodeTexWave"
        
            props = row.operator("node.add_node", text = "", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"


#Input nodes tab, Input panel. Just in texture and compositing mode
class NODES_PT_Input_input_advanced_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input Advanced"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in texture and compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)    

            props = col.operator("node.add_node", text=" Bokeh Image   ", icon = "NODE_BOKEH_IMAGE")    
            props.use_transform = True
            props.type = "CompositorNodeBokehImage"
           
            props = col.operator("node.add_node", text=" Time                 ", icon = "TIME")
            props.use_transform = True
            props.type = "CompositorNodeTime" 
            
            props = col.operator("node.add_node", text=" Track Position  ", icon = "NODE_TRACKPOSITION")
            props.use_transform = True
            props.type = "CompositorNodeTrackPos"
           
            props = col.operator("node.add_node", text=" Value               ", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "CompositorNodeValue"
       
         
        ##### Iconbuttons

        else:            

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "NODE_BOKEH_IMAGE")
            props.use_transform = True
            props.type = "CompositorNodeBokehImage"
           
            props = row.operator("node.add_node", text = "", icon = "TIME")
            props.use_transform = True
            props.type = "CompositorNodeTime" 
            
            props = row.operator("node.add_node", text = "", icon = "NODE_TRACKPOSITION")
            props.use_transform = True
            props.type = "CompositorNodeTrackPos"
           
            props = row.operator("node.add_node", text = "", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "CompositorNodeValue"


#Input nodes tab, Input panel. Just in texture mode
class NODES_PT_Input_input_advanced_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input Advanced"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon: 

            col = layout.column(align=True)    

            props = col.operator("node.add_node", text=" Coordinates       ", icon = "NODE_TEXCOORDINATE") 
            props.use_transform = True
            props.type = "TextureNodeCoordinates"

            props = col.operator("node.add_node", text=" Curve Time        ", icon = "NODE_CURVE_TIME")
            props.use_transform = True
            props.type = "TextureNodeCurveTime"

        #### Icon Buttons

        else: 

                row = layout.row()
                row.alignment = 'LEFT'       

                props = row.operator("node.add_node", text="", icon = "NODE_TEXCOORDINATE") 
                props.use_transform = True
                props.type = "TextureNodeCoordinates"

                props = row.operator("node.add_node", text="", icon = "NODE_CURVE_TIME")
                props.use_transform = True
                props.type = "TextureNodeCurveTime"


#Input nodes tab, Pattern panel. # Just in texture mode
class NODES_PT_Input_pattern(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pattern"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon: 

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Bricks               ", icon = "NODE_BRICK") 
            props.use_transform = True
            props.type = "TextureNodeBricks"

            props = col.operator("node.add_node", text=" Checker            ", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "TextureNodeChecker"

        #### Icon Buttons

        else:

            row = layout.row()
            row.alignment = 'LEFT'   

            props = row.operator("node.add_node", text="", icon = "NODE_BRICK") 
            props.use_transform = True
            props.type = "TextureNodeBricks"

            props = row.operator("node.add_node", text="", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "TextureNodeChecker"


#Input nodes tab, Color panel. Just in compositing mode
class NODES_PT_Input_color_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in texture and compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon: 

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" Alpha Over       ", icon = "IMAGE_ALPHA")
            props.use_transform = True
            props.type = "CompositorNodeAlphaOver"

            props = col.operator("node.add_node", text=" Bright / Contrast", icon = "NODE_BRIGHT_CONTRAST")
            props.use_transform = True
            props.type = "CompositorNodeBrightContrast" 
        
            props = col.operator("node.add_node", text=" Color Balance  ", icon = "NODE_COLORBALANCE")
            props.use_transform = True
            props.type = "CompositorNodeColorBalance"

            props = col.operator("node.add_node", text=" Hue Saturation Value", icon = "NODE_HUESATURATION")   
            props.use_transform = True
            props.type = "CompositorNodeHueSat"

            col = layout.column(align=True) 
        
            props = col.operator("node.add_node", text=" RGB Curves     ", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "CompositorNodeCurveRGB"
        
            props = col.operator("node.add_node", text=" Z Combine      ", icon = "NODE_ZCOMBINE")
            props.use_transform = True
            props.type = "CompositorNodeZcombine"

        #### Image Buttons

        else:

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "IMAGE_ALPHA") 
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


#Input nodes tab, Color panel. Just in texture mode
class NODES_PT_Input_color_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture and compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)  

            props = col.operator("node.add_node", text=" RGB Curves       ", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "TextureNodeCurveRGB"

            props = col.operator("node.add_node", text=" Hue / Saturation", icon = "NODE_HUESATURATION")   
            props.use_transform = True
            props.type = "TextureNodeHueSaturation"

            props = col.operator("node.add_node", text=" Invert                ", icon = "NODE_INVERT")  
            props.use_transform = True
            props.type = "TextureNodeInvert"

            props = col.operator("node.add_node", text=" Mix RGB            ", icon = "NODE_MIXRGB") 
            props.use_transform = True
            props.type = "TextureNodeMixRGB"

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" Combine RGBA ", icon = "NODE_COMBINERGB")
            props.use_transform = True
            props.type = "TextureNodeCompose"                

            props = col.operator("node.add_node", text=" Separate RGBA ", icon = "NODE_SEPARATERGB")
            props.use_transform = True
            props.type = "TextureNodeDecompose"

        #### Icon Buttons

        else: 

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


#Input nodes tab, Input Advanced panel. Just in compositing mode
class NODES_PT_Input_color_advanced(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color Advanced"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

#--------------------------------------------------------------------- Compositing Node Tree --------------------------------------------------------------------------------

        if context.space_data.tree_type == 'CompositorNodeTree':

            ##### Textbuttons

            if not addon_prefs.Node_text_or_icon:

                col = layout.column(align=True) 
            
                props = col.operator("node.add_node", text=" Color Correction", icon = "NODE_COLORCORRECTION")
                props.use_transform = True
                props.type = "CompositorNodeColorCorrection"

                props = col.operator("node.add_node", text=" Gamma           ", icon = "NODE_GAMMA")
                props.use_transform = True
                props.type = "CompositorNodeGamma"

                props = col.operator("node.add_node", text=" Hue Correct    ", icon = "NODE_HUESATURATION")   
                props.use_transform = True
                props.type = "CompositorNodeHueCorrect"
            
                props = col.operator("node.add_node", text=" Invert              ", icon = "NODE_INVERT")  
                props.use_transform = True
                props.type = "CompositorNodeInvert"

                col = layout.column(align=True)

                props = col.operator("node.add_node", text=" Tonemap         ", icon = "NODE_TONEMAP")
                props.use_transform = True 
                props.type = "CompositorNodeTonemap"

            
            ##### Iconbuttons

            else:            

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

                props = row.operator("node.add_node", text = "", icon = "NODE_TONEMAP")
                props.use_transform = True
                props.type = "CompositorNodeTonemap"


#Input nodes tab, Output panel, Shader mode 
class NODES_PT_Input_output_shader(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)
                
            if context.space_data.shader_type == 'OBJECT':
        
                props = col.operator("node.add_node", text=" Material Output", icon = "NODE_MATERIALOUTPUT")
                props.use_transform = True
                props.type = "ShaderNodeOutputMaterial"
        
        
                props = col.operator("node.add_node", text=" Lamp Output    ", icon = "LAMP_SUN")
                props.use_transform = True
                props.type = "ShaderNodeOutputLamp"

            elif context.space_data.shader_type == 'WORLD':
        
                props = col.operator("node.add_node", text=" World Output    ", icon = "WORLD")
                props.use_transform = True
                props.type = "ShaderNodeOutputWorld"

            elif context.space_data.shader_type == 'LINESTYLE':
        
                props = col.operator("node.add_node", text=" Line Style Output", icon = "NODE_LINESTYLE_OUTPUT")
                props.use_transform = True
                props.type = "ShaderNodeOutputLineStyle"

        #### Icon Buttons

        else:

            row = layout.row()
            row.alignment = 'LEFT'        

            if context.space_data.shader_type == 'OBJECT':
        
                props = row.operator("node.add_node", text = "", icon = "NODE_MATERIALOUTPUT")
                props.use_transform = True
                props.type = "ShaderNodeOutputMaterial"

                props = row.operator("node.add_node", text = "", icon = "LAMP_SUN")
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


#Input nodes tab, Output panel, Compositing mode
class NODES_PT_Input_output_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon: 

            col = layout.column(align=True)  
         
            props = col.operator("node.add_node", text=" Composite      ", icon = "NODE_COMPOSITE_OUTPUT")
            props.use_transform = True
            props.type = "CompositorNodeComposite"
            
            props = col.operator("node.add_node", text=" Viewer            ", icon = "NODE_VIEWER")
            props.use_transform = True
            props.type = "CompositorNodeViewer"

            col = layout.column(align=True)  
        
            props = col.operator("node.add_node", text=" File Output     ", icon = "NODE_FILEOUTPUT") 
            props.use_transform = True
            props.type = "CompositorNodeOutputFile"

            props = col.operator("node.add_node", text=" Levels             ", icon = "LEVELS")
            props.use_transform = True
            props.type = "CompositorNodeLevels"
        
            props = col.operator("node.add_node", text=" Split Viewer    ", icon = "NODE_VIWERSPLIT")
            props.use_transform = True
            props.type = "CompositorNodeSplitViewer"

        #### Image Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "NODE_COMPOSITE_OUTPUT")
            props.use_transform = True
            props.type = "CompositorNodeComposite"
            
            props = row.operator("node.add_node", text = "", icon = "NODE_VIEWER")
            props.use_transform = True
            props.type = "CompositorNodeViewer"

            row = layout.row()
            row.alignment = 'LEFT' 
        
            props = row.operator("node.add_node", text = "", icon = "NODE_FILEOUTPUT") 
            props.use_transform = True
            props.type = "CompositorNodeOutputFile"

            props = row.operator("node.add_node", text = "", icon = "LEVELS")
            props.use_transform = True
            props.type = "CompositorNodeLevels"
        
            props = row.operator("node.add_node", text = "", icon = "NODE_VIWERSPLIT")
            props.use_transform = True
            props.type = "CompositorNodeSplitViewer"


#Input nodes tab, Output panel, Texture modce
class NODES_PT_Input_output_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Input"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default
        
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences


        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Output               ", icon = "NODE_OUTPUT")
            props.use_transform = True
            props.type = "TextureNodeOutput"

            props = col.operator("node.add_node", text=" Viewer              ", icon = "NODE_VIEWER")
            props.use_transform = True
            props.type = "TextureNodeViewer"

        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT' 

            props = row.operator("node.add_node", text="", icon = "NODE_OUTPUT")
            props.use_transform = True
            props.type = "TextureNodeOutput"

            props = row.operator("node.add_node", text="", icon = "NODE_VIEWER")
            props.use_transform = True
            props.type = "TextureNodeViewer"


# ------------- Modify tab -------------------------------

#Modify nodes tab, Modify common panel. Just in compositing mode
class NODES_PT_Modify_matte(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Matte"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

            #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Box Mask         ", icon = "NODE_BOXMASK")
            props.use_transform = True
            props.type = "CompositorNodeBoxMask"

            props = col.operator("node.add_node", text=" Double Edge Mask ", icon = "NODE_DOUBLEEDGEMASK")
            props.use_transform = True
            props.type = "CompositorNodeDoubleEdgeMask" 
            
            props = col.operator("node.add_node", text=" Ellipse Mask     ", icon = "NODE_ELLIPSEMASK")  
            props.use_transform = True
            props.type = "CompositorNodeEllipseMask"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Channel Key     ", icon = "NODE_CHANNEL")
            props.use_transform = True
            props.type = "CompositorNodeChannelMatte"     
        
            props = col.operator("node.add_node", text=" Chroma Key     ", icon = "NODE_CHROMA")
            props.use_transform = True
            props.type = "CompositorNodeChromaMatte" 
            
            props = col.operator("node.add_node", text=" Color Key         ", icon = "COLOR")
            props.use_transform = True
            props.type = "CompositorNodeColorMatte"

            props = col.operator("node.add_node", text=" Color Spill        ", icon = "NODE_SPILL")
            props.use_transform = True
            props.type = "CompositorNodeColorSpill"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Difference Key ", icon = "SELECT_DIFFERENCE")   
            props.use_transform = True
            props.type = "CompositorNodeDiffMatte"     

            props = col.operator("node.add_node", text=" Distance Key   ", icon = "DRIVER_DISTANCE")
            props.use_transform = True
            props.type = "CompositorNodeDistanceMatte"

            props = col.operator("node.add_node", text=" Keying              ", icon = "NODE_KEYING")
            props.use_transform = True
            props.type = "CompositorNodeKeying"
            
            props = col.operator("node.add_node", text=" Keying Screen  ", icon = "NODE_KEYINGSCREEN") 
            props.use_transform = True
            props.type = "CompositorNodeKeyingScreen"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Luminance Key ", icon = "NODE_LUMINANCE") 
            props.use_transform = True
            props.type = "CompositorNodeLumaMatte"

        #### Icon Buttons

        else: 

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
            
            props = row.operator("node.add_node", text = "", icon = "COLOR")
            props.use_transform = True
            props.type = "CompositorNodeColorMatte"

            props = row.operator("node.add_node", text="", icon = "NODE_SPILL")
            props.use_transform = True
            props.type = "CompositorNodeColorSpill"

            row = layout.row()
            row.alignment = 'LEFT' 
      
            props = row.operator("node.add_node", text = "", icon = "SELECT_DIFFERENCE") 
            props.use_transform = True
            props.type = "CompositorNodeDiffMatte"

            props = row.operator("node.add_node", text = "", icon = "DRIVER_DISTANCE")
            props.use_transform = True
            props.type = "CompositorNodeDistanceMatte" 
            
            props = row.operator("node.add_node", text = "", icon = "NODE_KEYING")
            props.use_transform = True
            props.type = "CompositorNodeKeying"
            
            props = row.operator("node.add_node", text = "", icon = "NODE_KEYINGSCREEN") 
            props.use_transform = True
            props.type = "CompositorNodeKeyingScreen"

            row = layout.row()
            row.alignment = 'LEFT' 
            
            props = row.operator("node.add_node", text = "", icon = "NODE_LUMINANCE") 
            props.use_transform = True
            props.type = "CompositorNodeLumaMatte"


#Modify nodes tab, Filter panel. Just in compositing mode
class NODES_PT_Modify_filter(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Filter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" Bilateral Blur    ", icon = "NODE_BILATERAL_BLUR")
            props.use_transform = True
            props.type = "CompositorNodeBilateralblur"

            props = col.operator("node.add_node", text=" Blur                   ", icon = "NODE_BLUR") 
            props.use_transform = True
            props.type = "CompositorNodeBlur" 
        
            props = col.operator("node.add_node", text=" Bokeh Blur       ", icon = "NODE_BOKEH_BLUR") 
            props.use_transform = True
            props.type = "CompositorNodeBokehBlur"

            props = col.operator("node.add_node", text=" Directional Blur ", icon = "NODE_DIRECITONALBLUR")
            props.use_transform = True
            props.type = "CompositorNodeDBlur"

            col = layout.column(align=True)  

            props = col.operator("node.add_node", text=" Vector Blur       ", icon = "NODE_VECTOR_BLUR")
            props.use_transform = True
            props.type = "CompositorNodeVecBlur"

            props = col.operator("node.add_node", text=" Defocus             ", icon = "NODE_DEFOCUS")
            props.use_transform = True
            props.type = "CompositorNodeDefocus"

            props = col.operator("node.add_node", text=" Despeckle         ", icon = "NODE_DESPECKLE")
            props.use_transform = True
            props.type = "CompositorNodeDespeckle"

            props = col.operator("node.add_node", text=" Dilate / Erode    ", icon = "NODE_ERODE")
            props.use_transform = True
            props.type = "CompositorNodeDilateErode"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Filter                ", icon = "FILTER") 
            props.use_transform = True
            props.type = "CompositorNodeFilter"
            
            props = col.operator("node.add_node", text=" Glare                ", icon = "NODE_GLARE")
            props.use_transform = True
            props.type = "CompositorNodeGlare"

            row = col.row(align=True)  
            
            props = col.operator("node.add_node", text=" Inpaint              ", icon = "NODE_IMPAINT")
            props.use_transform = True
            props.type = "CompositorNodeInpaint"
            
            props = col.operator("node.add_node", text=" Pixelate            ", icon = "NODE_PIXELATED")
            props.use_transform = True
            props.type = "CompositorNodePixelate"

            col = layout.column(align=True) 
        
            props = col.operator("node.add_node", text=" Sunbeams        ", icon = "NODE_SUNBEAMS") 
            props.use_transform = True
            props.type = "CompositorNodeSunBeams"

        #### Icon Buttons

        else:

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

            props = row.operator("node.add_node", text = "", icon = "FILTER")  
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

#Modify nodes tab, Input panel. Just in shader mode
class NODES_PT_Modify_input(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

            ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)      
        
            props = col.operator("node.add_node", text=" Attribute          ", icon = "NODE_ATTRIBUTE")
            props.use_transform = True
            props.type = "ShaderNodeAttribute"
        
            props = col.operator("node.add_node", text=" Camera Data   ", icon = "NODE_CAMERADATA")
            props.use_transform = True
            props.type = "ShaderNodeCameraData"
        
            props = col.operator("node.add_node", text=" Geometry        ", icon = "NODE_GEOMETRY")
            props.use_transform = True
            props.type = "ShaderNodeNewGeometry"
        
            col = layout.column(align=True)
        
            props = col.operator("node.add_node", text=" Hair Info           ", icon = "NODE_HAIRINFO")
            props.use_transform = True
            props.type = "ShaderNodeHairInfo"
        
            props = col.operator("node.add_node", text=" Layer Weight   ", icon = "NODE_LAYERWEIGHT")
            props.use_transform = True
            props.type = "ShaderNodeLayerWeight"
        
            props = col.operator("node.add_node", text=" Light Path        ", icon = "NODE_LIGHTPATH")
            props.use_transform = True
            props.type = "ShaderNodeLightPath"
        
            props = col.operator("node.add_node", text=" Object Info       ", icon = "NODE_OBJECTINFO")
            props.use_transform = True
            props.type = "ShaderNodeObjectInfo"
        
            col = layout.column(align=True)
        
            props = col.operator("node.add_node", text=" Particle Info     ", icon = "NODE_PARTICLEINFO")
            props.use_transform = True
            props.type = "ShaderNodeParticleInfo"
        
            props = col.operator("node.add_node", text=" RGB                 ", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "ShaderNodeRGB"
        
            props = col.operator("node.add_node", text=" Tangent             ", icon = "NODE_TANGENT")
            props.use_transform = True
            props.type = "ShaderNodeTangent"
        
            props = col.operator("node.add_node", text=" Texture Coordinate ", icon = "NODE_TEXCOORDINATE") 
            props.use_transform = True
            props.type = "ShaderNodeTexCoord"

            col = layout.column(align=True)
        
            props = col.operator("node.add_node", text=" UV Map            ", icon = "GROUP_UVS")
            props.use_transform = True
            props.type = "ShaderNodeUVMap"
        
            props = col.operator("node.add_node", text=" Value                ", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "ShaderNodeValue"

            row = col.row(align=True)
        
            props = col.operator("node.add_node", text=" Wireframe        ", icon = "NODE_WIREFRAME")
            props.use_transform = True
            props.type = "ShaderNodeWireframe"

            if context.space_data.shader_type == 'LINESTYLE':

                props = col.operator("node.add_node", text=" UV along stroke", icon = "NODE_UVALONGSTROKE")
                props.use_transform = True
                props.type = "ShaderNodeUVALongStroke"

        ##### Icon Buttons 

        else: 

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
        
            props = row.operator("node.add_node", text = "", icon = "GROUP_UVS")
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


#Modify nodes tab, converter panel. Just in shader mode
class NODES_PT_Modify_converter_shader(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader and compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)        
        
            props = col.operator("node.add_node", text=" Combine HSV   ", icon = "NODE_COMBINEHSV")
            props.use_transform = True
            props.type = "ShaderNodeCombineHSV"        
         
            props = col.operator("node.add_node", text=" Combine RGB   ", icon = "NODE_COMBINERGB")
            props.use_transform = True
            props.type = "ShaderNodeCombineRGB"
        
            props = col.operator("node.add_node", text=" Combine XYZ   ", icon = "NODE_COMBINEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeCombineXYZ" 

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Separate HSV   ", icon = "NODE_SEPARATEHSV") 
            props.use_transform = True
            props.type = "ShaderNodeSeparateHSV"

            props = col.operator("node.add_node", text=" Separate RGB   ", icon = "NODE_SEPARATERGB")
            props.use_transform = True
            props.type = "ShaderNodeSeparateRGB"    
        
            props = col.operator("node.add_node", text=" Separate XYZ   ", icon = "NODE_SEPARATEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeSeparateXYZ" 

            col = layout.column(align=True)       
        
            props = col.operator("node.add_node", text=" Blackbody        ", icon = "NODE_BLACKBODY")
            props.use_transform = True
            props.type = "ShaderNodeBlackbody"        
        
            props = col.operator("node.add_node", text=" ColorRamp       ", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "ShaderNodeValToRGB"

            props = col.operator("node.add_node", text=" Math                 ", icon = "NODE_MATH")
            props.use_transform = True   
            props.type = "ShaderNodeMath"
        
            props = col.operator("node.add_node", text=" RGB to BW      ", icon = "NODE_RGBTOBW")
            props.use_transform = True
            props.type = "ShaderNodeRGBToBW"
        
            col = layout.column(align=True)       
        
            props = col.operator("node.add_node", text=" Vector Math     ", icon = "NODE_VECTORMATH")
            props.use_transform = True
            props.type = "ShaderNodeVectorMath"
        
            props = col.operator("node.add_node", text=" Wavelength     ", icon = "NODE_WAVELENGTH")
            props.use_transform = True
            props.type = "ShaderNodeWavelength"
        

        ##### Icon Buttons 

        else: 

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
            

#Modify nodes tab, converter panel. Just in compositing mode
class NODES_PT_Modify_converter_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

            #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)   

            props = col.operator("node.add_node", text=" Combine HSVA ", icon = "NODE_COMBINEHSV")
            props.use_transform = True
            props.type = "CompositorNodeCombHSVA"
            
            props = col.operator("node.add_node", text=" Combine RGBA ", icon = "NODE_COMBINERGB")
            props.use_transform = True
            props.type = "CompositorNodeCombRGBA"

            props = col.operator("node.add_node", text=" Combine YCbCrA ", icon = "NODE_COMBINEYCBCRA")
            props.use_transform = True
            props.type = "CompositorNodeCombYCCA"

            props = col.operator("node.add_node", text=" Combine YUVA ", icon = "NODE_COMBINEYUVA")  
            props.use_transform = True
            props.type = "CompositorNodeCombYUVA"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Separate HSVA ", icon = "NODE_SEPARATEHSV") 
            props.use_transform = True
            props.type = "CompositorNodeSepHSVA"

            props = col.operator("node.add_node", text=" Separate RGBA ", icon = "NODE_SEPARATERGB")
            props.use_transform = True
            props.type = "CompositorNodeSepRGBA"
        
            props = col.operator("node.add_node", text=" Separate YCbCrA ", icon = "NODE_SEPARATE_YCBCRA") 
            props.use_transform = True
            props.type = "CompositorNodeSepYCCA"

            props = col.operator("node.add_node", text=" Separate YUVA ", icon = "NODE_SEPARATE_YUVA") 
            props.use_transform = True
            props.type = "CompositorNodeSepYUVA"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Set Alpha          ", icon = "IMAGE_ALPHA")
            props.use_transform = True
            props.type = "CompositorNodeSetAlpha"
                
            props = col.operator("node.add_node", text=" Alpha Convert  ", icon = "NODE_ALPHACONVERT")
            props.use_transform = True
            props.type = "CompositorNodePremulKey"

            props = col.operator("node.add_node", text=" RGB to BW       ", icon = "NODE_RGBTOBW")
            props.use_transform = True
            props.type = "CompositorNodeRGBToBW"

            props = col.operator("node.add_node", text=" Color Ramp      ", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "CompositorNodeValToRGB"

            col = layout.column(align=True)
        
            props = col.operator("node.add_node", text=" ID Mask           ", icon = "MOD_MASK") 
            props.use_transform = True
            props.type = "CompositorNodeIDMask"
            
            props = col.operator("node.add_node", text=" Math                 ", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "CompositorNodeMath"

            props = col.operator("node.add_node", text=" Switch View    ", icon = "VIEW_SWITCHACTIVECAM")
            props.use_transform = True
            props.type = "CompositorNodeSwitchView"
        

        #### Icon Buttons

        else: 

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
                
            props = row.operator("node.add_node", text = "", icon = "IMAGE_ALPHA")
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
        
            props = row.operator("node.add_node", text = "", icon = "MOD_MASK") 
            props.use_transform = True
            props.type = "CompositorNodeIDMask"
            
            props = row.operator("node.add_node", text = "", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "CompositorNodeMath"

            props = row.operator("node.add_node", text = "", icon = "VIEW_SWITCHACTIVECAM")
            props.use_transform = True
            props.type = "CompositorNodeSwitchView"


#Modify nodes tab, converter panel. Just in texture mode
class NODES_PT_Modify_converter_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Color Ramp      ", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "TextureNodeValToRGB"

            props = col.operator("node.add_node", text=" Distance           ", icon = "DRIVER_DISTANCE")
            props.use_transform = True
            props.type = "TextureNodeDistance"

            props = col.operator("node.add_node", text=" Math                 ", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "TextureNodeMath"

            props = col.operator("node.add_node", text=" RGB to BW       ", icon = "NODE_RGBTOBW")
            props.use_transform = True
            props.type = "TextureNodeRGBToBW"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Value to Normal ", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "TextureNodeValToNor"

        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT' 

            props = row.operator("node.add_node", text="", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "TextureNodeValToRGB"

            props = row.operator("node.add_node", text="", icon = "DRIVER_DISTANCE")
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

            props = row.operator("node.add_node", text="", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "TextureNodeValToNor"


#Modify nodes tab, vector panel. Just in shader mode
class NODES_PT_Modify_vector_shader(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader and compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)    
        
            props = col.operator("node.add_node", text=" Bump               ", icon = "NODE_BUMP")
            props.use_transform = True   
            props.type = "ShaderNodeBump"
        
            props = col.operator("node.add_node", text=" Mapping           ", icon = "NODE_MAPPING")
            props.use_transform = True
            props.type = "ShaderNodeMapping"

            props = col.operator("node.add_node", text=" Normal            ", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "ShaderNodeNormal"
                
            col = layout.column(align=True) 
                
            props = col.operator("node.add_node", text=" Vector Curves ", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"

            props = col.operator("node.add_node", text=" Vector Transform ", icon = "NODE_VECTOR_TRANSFORM")
            props.use_transform = True
            props.type = "ShaderNodeVectorTransform"

        ##### Icon Buttons 

        else: 

            ##### --------------------------------- Vector ------------------------------------------- ####

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text = "", icon = "NODE_BUMP")
            props.use_transform = True
            props.type = "ShaderNodeBump"

            props = row.operator("node.add_node", text = "", icon = "NODE_MAPPING")
            props.use_transform = True
            props.type = "ShaderNodeMapping"
     
            props = row.operator("node.add_node", text = "", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "ShaderNodeNormal"
        
            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"
        
            props = row.operator("node.add_node", text = "", icon = "NODE_VECTOR_TRANSFORM")
            props.use_transform = True
            props.type = "ShaderNodeVectorTransform"


#Modify nodes tab, vector panel. Just in compositing mode
class NODES_PT_Modify_vector_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

            #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)  

            props = col.operator("node.add_node", text=" Map Range       ", icon = "NODE_RANGE")
            props.use_transform = True
            props.type = "CompositorNodeMapRange"

            props = col.operator("node.add_node", text=" Map Value       ", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "CompositorNodeMapValue"
        
            props = col.operator("node.add_node", text=" Normal            ", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "CompositorNodeNormal"
            
            props = col.operator("node.add_node", text=" Normalize        ", icon = "NODE_NORMALIZE")
            props.use_transform = True
            props.type = "CompositorNodeNormalize"

            col = layout.column(align=True)
        
            props = col.operator("node.add_node", text=" Vector Curves  ", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "CompositorNodeCurveVec"


        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "NODE_RANGE")
            props.use_transform = True
            props.type = "CompositorNodeMapRange"

            props = row.operator("node.add_node", text = "", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "CompositorNodeMapValue"
        
            props = row.operator("node.add_node", text = "", icon = "RECALC_NORMALS")
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


#Modify nodes tab, distort panel. Just in texture mode
class NODES_PT_Modify_distort_tex(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Distort"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene 

            #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" At                      ", icon = "NODE_AT")
            props.use_transform = True
            props.type = "TextureNodeAt"

            props = col.operator("node.add_node", text=" Rotate              ", icon = "TRANSFORM_ROTATE") 
            props.use_transform = True    
            props.type = "TextureNodeRotate"

            props = col.operator("node.add_node", text=" Scale                ", icon = "TRANSFORM_SCALE")
            props.use_transform = True
            props.type = "TextureNodeScale"

            props = col.operator("node.add_node", text=" Translate          ", icon = "TRANSFORM_MOVE") 
            props.use_transform = True
            props.type = "TextureNodeTranslate"

        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text="", icon = "NODE_AT")
            props.use_transform = True
            props.type = "TextureNodeAt"

            props = row.operator("node.add_node", text="", icon = "TRANSFORM_ROTATE") 
            props.use_transform = True
            props.type = "TextureNodeRotate"

            props = row.operator("node.add_node", text="", icon = "TRANSFORM_SCALE")
            props.use_transform = True
            props.type = "TextureNodeScale"

            props = row.operator("node.add_node", text="", icon = "TRANSFORM_MOVE") 
            props.use_transform = True
            props.type = "TextureNodeTranslate"


#Modify nodes tab, distort panel. Just in compositing mode
class NODES_PT_Modify_distort_comp(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Distort"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in compositing mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene      

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True) 

            props = col.operator("node.add_node", text=" Corner Pin        ", icon = "NODE_CORNERPIN")
            props.use_transform = True
            props.type = "CompositorNodeCornerPin"

            props = col.operator("node.add_node", text=" Crop                 ", icon = "NODE_CROP")
            props.use_transform = True
            props.type = "CompositorNodeCrop"
        
            props = col.operator("node.add_node", text=" Displace          ", icon = "MOD_DISPLACE") 
            props.use_transform = True
            props.type = "CompositorNodeDisplace"
            
            props = col.operator("node.add_node", text=" Flip                   ", icon = "FLIP")  
            props.use_transform = True
            props.type = "CompositorNodeFlip"

            col = layout.column(align=True)  
        
            props = col.operator("node.add_node", text=" Lens Distortion ", icon = "NODE_LENSDISTORT")
            props.use_transform = True
            props.type = "CompositorNodeLensdist"

            props = col.operator("node.add_node", text=" Map UV            ", icon = "GROUP_UVS")
            props.use_transform = True
            props.type = "CompositorNodeMapUV"
        
            props = col.operator("node.add_node", text=" Movie Distortion ", icon = "NODE_MOVIEDISTORT") 
            props.use_transform = True
            props.type = "CompositorNodeMovieDistortion"
            
            props = col.operator("node.add_node", text=" Plane Track Deform ", icon = "NODE_PLANETRACKDEFORM")
            props.use_transform = True
            props.type = "CompositorNodePlaneTrackDeform"

            col = layout.column(align=True)
            
            props = col.operator("node.add_node", text=" Rotate               ", icon = "TRANSFORM_ROTATE")  
            props.use_transform = True
            props.type = "CompositorNodeRotate"
            
            props = col.operator("node.add_node", text=" Scale                ", icon = "TRANSFORM_SCALE")
            props.use_transform = True
            props.type = "CompositorNodeScale"
      
            props = col.operator("node.add_node", text=" Transform         ", icon = "NODE_TRANSFORM")
            props.use_transform = True
            props.type = "CompositorNodeTransform"

            props = col.operator("node.add_node", text=" Translate          ", icon = "TRANSFORM_MOVE") 
            props.use_transform = True
            props.type = "CompositorNodeTranslate"

            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Stabilize 2D     ", icon = "NODE_STABILIZE2D")  
            props.use_transform = True
            props.type = "CompositorNodeStabilize"

        #### Icon Buttons

        else:

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "NODE_CORNERPIN")
            props.use_transform = True
            props.type = "CompositorNodeCornerPin"

            props = row.operator("node.add_node", text = "", icon = "NODE_CROP")
            props.use_transform = True
            props.type = "CompositorNodeCrop"
        
            props = row.operator("node.add_node", text = "", icon = "MOD_DISPLACE") 
            props.use_transform = True
            props.type = "CompositorNodeDisplace"
            
            props = row.operator("node.add_node", text = "", icon = "FLIP")  
            props.use_transform = True
            props.type = "CompositorNodeFlip"

            row = layout.row()
            row.alignment = 'LEFT'  
        
            props = row.operator("node.add_node", text = "", icon = "NODE_LENSDISTORT")
            props.use_transform = True
            props.type = "CompositorNodeLensdist"

            props = row.operator("node.add_node", text = "", icon = "GROUP_UVS")
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
            
            props = row.operator("node.add_node", text = "", icon = "TRANSFORM_ROTATE") 
            props.use_transform = True
            props.type = "CompositorNodeRotate"
            
            props = row.operator("node.add_node", text = "", icon = "TRANSFORM_SCALE")
            props.use_transform = True
            props.type = "CompositorNodeScale"
                    
            props = row.operator("node.add_node", text = "", icon = "NODE_TRANSFORM")
            props.use_transform = True
            props.type = "CompositorNodeTransform"

            props = row.operator("node.add_node", text = "", icon = "TRANSFORM_MOVE") 
            props.use_transform = True
            props.type = "CompositorNodeTranslate"

            row = layout.row()
            row.alignment = 'LEFT'  

            props = row.operator("node.add_node", text = "", icon = "NODE_STABILIZE2D")  
            props.use_transform = True
            props.type = "CompositorNodeStabilize"


#Modify nodes tab,color common panel. Just in shader mode.
class NODES_PT_Modify_color(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree')
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
                
            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Bright / Contrast ", icon = "NODE_BRIGHT_CONTRAST")
            props.use_transform = True
            props.type = "ShaderNodeBrightContrast"       
        
            props = col.operator("node.add_node", text=" Gamma             ", icon = "NODE_GAMMA")
            props.use_transform = True
            props.type = "ShaderNodeGamma"
        
            props = col.operator("node.add_node", text=" Hue / Saturation ", icon = "NODE_HUESATURATION")   
            props.use_transform = True
            props.type = "ShaderNodeHueSaturation"
        
            props = col.operator("node.add_node", text=" Invert                 ", icon = "NODE_INVERT")  
            props.use_transform = True
            props.type = "ShaderNodeInvert"
                
            col = layout.column(align=True)

            props = col.operator("node.add_node", text=" Light Falloff      ", icon = "NODE_LIGHTFALLOFF")
            props.use_transform = True
            props.type = "ShaderNodeLightFalloff"
        
            props = col.operator("node.add_node", text=" Mix RGB           ", icon = "NODE_MIXRGB") 
            props.use_transform = True
            props.type = "ShaderNodeMixRGB"
        
            props = col.operator("node.add_node", text="  RGB Curves        ", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "ShaderNodeRGBCurve"


        ##### Icon Buttons 

        else:

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


#Modify nodes tab, Script panel. Just in shader mode
class NODES_PT_Modify_script(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Script"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Modify"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader mode
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

            ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)
        
            props = col.operator("node.add_node", text=" Script               ", icon = "FILE_SCRIPT")
            props.use_transform = True
            props.type = "ShaderNodeScript"  

        ##### Icon Buttons 

        else: 

            row = layout.row()
            row.alignment = 'LEFT'        
        
            props = row.operator("node.add_node", text = "", icon = "FILE_SCRIPT")
            props.use_transform = True
            props.type = "ShaderNodeScript"  


# ------------- Relations tab -------------------------------
            
#Relations tab, Relations Panel
class NODES_PT_Relations_group(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Group"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)  

            col.operator("node.group_edit", text=" Edit Group         ", icon = "NODE_EDITGROUP").exit = False
            col.operator("node.group_edit", text = "Exit Edit Group ", icon = "NODE_EXITEDITGROUP").exit = True
            col.operator("node.group_insert", text = " Group Insert      ", icon = "NODE_GROUPINSERT")
            col.operator("node.group_make", text = " Make Group      ", icon = "NODE_MAKEGROUP")

            col = layout.column(align=True)  

            col.operator("node.group_ungroup", text = " Ungroup           ", icon = "NODE_UNGROUP")

        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'        

            row.operator("node.group_edit", text = "", icon = "NODE_EDITGROUP").exit = False
            row.operator("node.group_edit", text = "", icon = "NODE_EXITEDITGROUP").exit = True
            row.operator("node.group_insert", text = "", icon = "NODE_GROUPINSERT")
            row.operator("node.group_make", text = "", icon = "NODE_MAKEGROUP")

            row = layout.row()
            row.alignment = 'LEFT'

            row.operator("node.group_ungroup", text = "", icon = "NODE_UNGROUP")


#Relations tab, Relations Panel
class NODES_PT_Relations_layout(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Layout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"
    
    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        
        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:

            col = layout.column(align=True)     

            props = col.operator("node.add_node", text=" Frame               ", icon = "NODE_FRAME")
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = col.operator("node.add_node", text=" Reroute             ", icon = "NODE_REROUTE")
            props.use_transform = True
            props.type = "NodeReroute"

            if context.space_data.tree_type == 'CompositorNodeTree':
                col = layout.column(align=True)   
                props = col.operator("node.add_node", text=" Switch              ", icon = "SWITCH_DIRECTION")
                props.use_transform = True
                props.type = "CompositorNodeSwitch"

        #### Icon Buttons

        else: 

            row = layout.row()
            row.alignment = 'LEFT'        

            props = row.operator("node.add_node", text = "", icon = "NODE_FRAME")
            props.use_transform = True
            props.type = "NodeFrame"      
        
            props = row.operator("node.add_node", text = "", icon = "NODE_REROUTE")
            props.use_transform = True
            props.type = "NodeReroute"

            if context.space_data.tree_type == 'CompositorNodeTree':
                props = row.operator("node.add_node", text="", icon = "SWITCH_DIRECTION")
                props.use_transform = True
                props.type = "CompositorNodeSwitch"


classes = (
    NODES_PT_Prop,
    NODES_PT_Input_connect,
    NODES_PT_Input_input_shader,
    NODES_PT_Input_input_comp,
    NODES_PT_Input_input_tex,
    NODES_PT_Input_textures_tex,
    NODES_PT_Input_shader,
    NODES_PT_Input_shader_common,
    NODES_PT_Input_shader_advanced,
    NODES_PT_Input_textures_shader,
    NODES_PT_Input_input_advanced_comp,
    NODES_PT_Input_input_advanced_tex,
    NODES_PT_Input_pattern,
    NODES_PT_Input_color_comp,
    NODES_PT_Input_color_tex,
    NODES_PT_Input_color_advanced,
    NODES_PT_Input_output_shader,
    NODES_PT_Input_output_comp,
    NODES_PT_Input_output_tex,
    NODES_PT_Modify_matte,
    NODES_PT_Modify_filter,
    NODES_PT_Modify_input,
    NODES_PT_Modify_color,
    NODES_PT_Modify_converter_shader,
    NODES_PT_Modify_converter_comp,
    NODES_PT_Modify_converter_tex,
    NODES_PT_Modify_vector_shader,
    NODES_PT_Modify_vector_comp,
    NODES_PT_Modify_distort_tex,
    NODES_PT_Modify_distort_comp,
    NODES_PT_Modify_script,
    NODES_PT_Relations_group,
    NODES_PT_Relations_layout, 
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

