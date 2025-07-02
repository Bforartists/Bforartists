# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy import context

#Add tab, Node Group panel
from nodeitems_builtins import node_tree_group_type


class NodePanel:
    @staticmethod
    def draw_button(layout, node=None, operator="node.add_node", text="", icon='NONE', settings=None):
        props = layout.operator(operator, text=text, icon=icon)
        props.use_transform = True

        if node is not None:
            props.type = node

        if settings is not None:
            for name, value in settings.items():
                ops = props.settings.add()
                ops.name = name
                ops.value = value


# Icon or text buttons in shader editor and compositor in the ADD panel
class NODES_PT_shader_comp_textoricon_shader_add(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Add"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in {'ShaderNodeTree'})

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        row = layout.row()
        row.prop(addon_prefs,"Node_text_or_icon", text = "Icon Buttons")
        row.prop(addon_prefs,"Node_shader_add_common", text = "Common")


# Icon or text buttons in compositor in the ADD panel
class NODES_PT_shader_comp_textoricon_compositor_add(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Add"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in {'CompositorNodeTree'})

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        row = layout.row()
        row.prop(addon_prefs,"Node_text_or_icon", text = "Icon Buttons")


# Icon or text buttons in shader editor and compositor in the RELATIONS panel
class NODES_PT_shader_comp_textoricon_relations(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Relations"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in {'ShaderNodeTree', 'CompositorNodeTree'})

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        layout.prop(addon_prefs,"Node_text_or_icon", text = "Icon Buttons")


# Icon or text buttons in geometry node editor in the ADD panel
class NODES_PT_geom_textoricon_add(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Add"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in 'GeometryNodeTree')

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        layout.prop(addon_prefs,"Node_text_or_icon", text = "Icon Buttons")


# Icon or text buttons in geometry node editor in the RELATIONS panel
class NODES_PT_geom_textoricon_relations(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Relations"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in 'GeometryNodeTree')

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        layout.prop(addon_prefs,"Node_text_or_icon", text = "Icon Buttons")


# Shader editor, Input panel
class NODES_PT_shader_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader mode

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeAmbientOcclusion", text=" Ambient Occlusion  ", icon="NODE_AMBIENT_OCCLUSION")
            self.draw_button(col, "ShaderNodeAttribute", text=" Attribute          ", icon="NODE_ATTRIBUTE")
            self.draw_button(col, "ShaderNodeBevel", text=" Bevel               ", icon="BEVEL")
            self.draw_button(col, "ShaderNodeCameraData", text=" Camera Data   ", icon="CAMERA_DATA")
            self.draw_button(col, "ShaderNodeVertexColor", text=" Color Attribute ", icon="NODE_VERTEX_COLOR")
            self.draw_button(col, "ShaderNodeFresnel", text=" Fresnel              ", icon="NODE_FRESNEL")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeNewGeometry", text=" Geometry        ", icon="NODE_GEOMETRY")
            self.draw_button(col, "ShaderNodeHairInfo", text=" Curves Info       ", icon="NODE_HAIRINFO")
            self.draw_button(col, "ShaderNodeLayerWeight", text=" Layer Weight   ", icon="NODE_LAYERWEIGHT")
            self.draw_button(col, "ShaderNodeLightPath", text=" Light Path        ", icon="NODE_LIGHTPATH")
            self.draw_button(col, "ShaderNodeObjectInfo", text=" Object Info       ", icon="NODE_OBJECTINFO")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeParticleInfo", text=" Particle Info     ", icon="NODE_PARTICLEINFO")
            self.draw_button(col, "ShaderNodePointInfo", text=" Point Info         ", icon="POINT_INFO")
            self.draw_button(col, "ShaderNodeRGB", text=" RGB                 ", icon="NODE_RGB")
            self.draw_button(col, "ShaderNodeTangent", text=" Tangent             ", icon="NODE_TANGENT")
            self.draw_button(col, "ShaderNodeTexCoord", text=" Texture Coordinate", icon="NODE_TEXCOORDINATE")

            if context.space_data.shader_type == 'LINESTYLE':
                self.draw_button(col, "ShaderNodeUVALongStroke", text=" UV along stroke", icon="NODE_UVALONGSTROKE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeUVMap", text=" UV Map            ", icon="GROUP_UVS")
            self.draw_button(col, "ShaderNodeValue", text=" Value                ", icon="NODE_VALUE")
            self.draw_button(col, "ShaderNodeVolumeInfo", text=" Volume Info    ", icon="NODE_VOLUME_INFO")
            self.draw_button(col, "ShaderNodeWireframe", text=" Wireframe        ", icon="NODE_WIREFRAME")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeAmbientOcclusion", text="", icon="NODE_AMBIENT_OCCLUSION")
            self.draw_button(flow, "ShaderNodeAttribute", text="", icon="NODE_ATTRIBUTE")
            self.draw_button(flow, "ShaderNodeBevel", text="", icon="BEVEL")
            self.draw_button(flow, "ShaderNodeCameraData", text="", icon="CAMERA_DATA")
            self.draw_button(flow, "ShaderNodeVertexColor", text="", icon="NODE_VERTEX_COLOR")
            self.draw_button(flow, "ShaderNodeFresnel", text="", icon="NODE_FRESNEL")
            self.draw_button(flow, "ShaderNodeNewGeometry", text="", icon="NODE_GEOMETRY")
            self.draw_button(flow, "ShaderNodeHairInfo", text="", icon="NODE_HAIRINFO")
            self.draw_button(flow, "ShaderNodeLayerWeight", text="", icon="NODE_LAYERWEIGHT")
            self.draw_button(flow, "ShaderNodeLightPath", text="", icon="NODE_LIGHTPATH")
            self.draw_button(flow, "ShaderNodeObjectInfo", text="", icon="NODE_OBJECTINFO")
            self.draw_button(flow, "ShaderNodeParticleInfo", text="", icon="NODE_PARTICLEINFO")
            self.draw_button(flow, "ShaderNodePointInfo", text="", icon="POINT_INFO")
            self.draw_button(flow, "ShaderNodeRGB", text="", icon="NODE_RGB")
            self.draw_button(flow, "ShaderNodeTangent", text="", icon="NODE_TANGENT")
            self.draw_button(flow, "ShaderNodeTexCoord", text="", icon="NODE_TEXCOORDINATE")

            if context.space_data.shader_type == 'LINESTYLE':
                self.draw_button(flow, "ShaderNodeUVALongStroke", text="", icon="NODE_UVALONGSTROKE")
            self.draw_button(flow, "ShaderNodeUVMap", text="", icon="GROUP_UVS")
            self.draw_button(flow, "ShaderNodeValue", text="", icon="NODE_VALUE")
            self.draw_button(flow, "ShaderNodeVolumeInfo", text="", icon="NODE_VOLUME_INFO")
            self.draw_button(flow, "ShaderNodeWireframe", text="", icon="NODE_WIREFRAME")


#Shader editor , Output panel
class NODES_PT_shader_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader mode

    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        engine = context.engine

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeOutputAOV", text=" AOV Output    ", icon="NODE_VALUE")

            if context.space_data.shader_type == 'OBJECT':
                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeOutputLight", text=" Light Output    ", icon="LIGHT")
                self.draw_button(col, "ShaderNodeOutputMaterial", text=" Material Output", icon="NODE_MATERIAL")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_button(col, "ShaderNodeOutputWorld", text=" World Output    ", icon="WORLD")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_button(col, "ShaderNodeOutputLineStyle", text=" Line Style Output", icon="NODE_LINESTYLE_OUTPUT")

        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeOutputAOV", text="", icon="NODE_VALUE")

            if context.space_data.shader_type == 'OBJECT':
                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeOutputLight", text="", icon="LIGHT")
                self.draw_button(flow, "ShaderNodeOutputMaterial", text="", icon="NODE_MATERIAL")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_button(flow, "ShaderNodeOutputWorld", text="", icon="WORLD")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_button(flow, "ShaderNodeOutputLineStyle", text="", icon="NODE_LINESTYLE_OUTPUT")


#Compositor, Add tab, input panel
class NODES_PT_comp_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in geometry node editor

    @staticmethod
    def draw(self, context):
        layout = self.layout

        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

       #### Text Buttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeBokehImage", text=" Bokeh Image   ", icon="NODE_BOKEH_IMAGE")
            self.draw_button(col, "CompositorNodeImage", text=" Image              ", icon="FILE_IMAGE")
            self.draw_button(col, "CompositorNodeMask", text="Mask               ", icon="MOD_MASK")
            self.draw_button(col, "CompositorNodeMovieClip", text=" Movie Clip        ", icon="FILE_MOVIE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeTexture", text=" Texture             ", icon="TEXTURE")


        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeBokehImage", text="", icon="NODE_BOKEH_IMAGE")
            self.draw_button(flow, "CompositorNodeImage", text="", icon="FILE_IMAGE")
            self.draw_button(flow, "CompositorNodeMask", text="", icon="MOD_MASK")
            self.draw_button(flow, "CompositorNodeMovieClip", text="", icon="FILE_MOVIE")
            self.draw_button(flow, "CompositorNodeRGB", text="", icon="NODE_RGB")
            self.draw_button(flow, "CompositorNodeTexture", text="", icon="TEXTURE")
            self.draw_button(flow, "CompositorNodeValue", text="", icon="NODE_VALUE")


#Compositor, Add tab, Constant supbanel
class NODES_PT_comp_add_input_constant(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_comp_add_input"

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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeRGB", text=" RGB                ", icon="NODE_RGB")
            self.draw_button(col, "CompositorNodeValue", text=" Value               ", icon="NODE_VALUE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeRGB", text="", icon="NODE_RGB")
            self.draw_button(flow, "CompositorNodeValue", text="", icon="NODE_VALUE")


#Compositor, Add tab, Scene supbanel
class NODES_PT_comp_add_input_scene(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Scene"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_comp_add_input"

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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeRLayers", text="  Render Layers              ", icon="RENDERLAYERS")
            self.draw_button(col, "CompositorNodeSceneTime", text="  Scene Time              ", icon="TIME")
            self.draw_button(col, "CompositorNodeTime", text="  Time Curve              ", icon="NODE_CURVE_TIME")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeRLayers", text="", icon="RENDERLAYERS")
            self.draw_button(flow, "CompositorNodeSceneTime", text="", icon="TIME")
            self.draw_button(flow, "CompositorNodeTime", text="", icon="NODE_CURVE_TIME")


#Compositor, Add tab, Output Panel
class NODES_PT_comp_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeComposite", text=" Composite      ", icon="NODE_COMPOSITING")
            self.draw_button(col, "CompositorNodeViewer", text=" Viewer            ", icon="NODE_VIEWER")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeOutputFile", text=" File Output     ", icon="NODE_FILEOUTPUT")


        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeComposite", text="", icon="NODE_COMPOSITING")
            self.draw_button(flow, "CompositorNodeOutputFile", text="", icon="NODE_FILEOUTPUT")
            self.draw_button(flow, "CompositorNodeViewer", text="", icon="NODE_VIEWER")

#Compositor, Add tab, Color Panel
class NODES_PT_comp_add_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodePremulKey", text=" Alpha Convert   ", icon="NODE_ALPHACONVERT")
            self.draw_button(col, "CompositorNodeValToRGB", text=" Color Ramp      ", icon="NODE_COLORRAMP")
            self.draw_button(col, "CompositorNodeConvertColorSpace", text=" Convert Colorspace      ", icon="COLOR_SPACE")
            self.draw_button(col, "CompositorNodeSetAlpha", text=" Set Alpha          ", icon="IMAGE_ALPHA")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeInvert", text=" Invert Color       ", icon="NODE_INVERT")
            self.draw_button(col, "CompositorNodeRGBToBW", text=" RGB to BW       ", icon="NODE_RGBTOBW")


        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_button(flow, "CompositorNodePremulKey", text="", icon="NODE_ALPHACONVERT")
            self.draw_button(flow, "CompositorNodeValToRGB", text="", icon="NODE_COLORRAMP")
            self.draw_button(flow, "CompositorNodeConvertColorSpace", text="", icon="COLOR_SPACE")
            self.draw_button(flow, "CompositorNodeSetAlpha", text="", icon="IMAGE_ALPHA")
            self.draw_button(flow, "CompositorNodeInvert", text="", icon="NODE_INVERT")
            self.draw_button(flow, "CompositorNodeRGBToBW", text="", icon="NODE_RGBTOBW")


#Compositor, Add tab, Color, Adjust supbanel
class NODES_PT_comp_add_color_adjust(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Adjust"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_comp_add_color"

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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeBrightContrast", text=" Bright / Contrast", icon="BRIGHTNESS_CONTRAST")
            self.draw_button(col, "CompositorNodeColorBalance", text=" Color Balance", icon="NODE_COLORBALANCE")
            self.draw_button(col, "CompositorNodeColorCorrection", text=" Color Correction", icon="NODE_COLORCORRECTION")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeExposure", text=" Exposure", icon="EXPOSURE")
            self.draw_button(col, "CompositorNodeGamma", text=" Gamma", icon="NODE_GAMMA")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeHueCorrect", text=" Hue Correct", icon="NODE_HUESATURATION")
            self.draw_button(col, "CompositorNodeHueSat", text=" Hue/Saturation/Value", icon="NODE_HUESATURATION")
            self.draw_button(col, "CompositorNodeCurveRGB", text=" RGB Curves", icon="NODE_RGBCURVE")
            self.draw_button(col, "CompositorNodeTonemap", text=" Tonemap", icon="NODE_TONEMAP")



        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeBrightContrast", text="", icon="BRIGHTNESS_CONTRAST")
            self.draw_button(flow, "CompositorNodeColorBalance", text="", icon="NODE_COLORBALANCE")
            self.draw_button(flow, "CompositorNodeColorCorrection", text="", icon="NODE_COLORCORRECTION")
            self.draw_button(flow, "CompositorNodeExposure", text="", icon="EXPOSURE")
            self.draw_button(flow, "CompositorNodeGamma", text="", icon="NODE_GAMMA")
            self.draw_button(flow, "CompositorNodeHueCorrect", text="", icon="NODE_HUESATURATION")
            self.draw_button(flow, "CompositorNodeHueSat", text="", icon="NODE_HUESATURATION")
            self.draw_button(flow, "CompositorNodeCurveRGB", text="", icon="NODE_RGBCURVE")
            self.draw_button(flow, "CompositorNodeTonemap", text="", icon="NODE_TONEMAP")


#Compositor, Add tab, Color, Mix supbanel
class NODES_PT_comp_add_color_mix(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mix"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_comp_add_color"

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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeAlphaOver", text=" Alpha Over", icon="IMAGE_ALPHA")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeCombineColor", text=" Combine Color", icon="COMBINE_COLOR")
            self.draw_button(col, "CompositorNodeSeparateColor", text=" Separate Color", icon="SEPARATE_COLOR")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeMixRGB", text=" Mix Color", icon="NODE_MIXRGB")
            self.draw_button(col, "CompositorNodeZcombine", text=" Z Combine", icon="NODE_ZCOMBINE")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeAlphaOver", text="", icon="IMAGE_ALPHA")
            self.draw_button(flow, "CompositorNodeCombineColor", text="", icon="COMBINE_COLOR")
            self.draw_button(flow, "CompositorNodeSeparateColor", text="", icon="SEPARATE_COLOR")
            self.draw_button(flow, "CompositorNodeMixRGB", text="", icon="NODE_MIXRGB")
            self.draw_button(flow, "CompositorNodeZcombine", text="", icon="NODE_ZCOMBINE")


#Compositor, Add tab, Filter Panel
class NODES_PT_comp_add_filter(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Filter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeAntiAliasing", text=" Anti Aliasing     ", icon="ANTIALIASED")
            self.draw_button(col, "CompositorNodeDenoise", text=" Denoise           ", icon="NODE_DENOISE")
            self.draw_button(col, "CompositorNodeDespeckle", text=" Despeckle         ", icon="NODE_DESPECKLE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeDilateErode", text=" Dilate / Erode    ", icon="NODE_ERODE")
            self.draw_button(col, "CompositorNodeInpaint", text=" Inpaint              ", icon="NODE_IMPAINT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeFilter", text=" Filter                ", icon="FILTER")
            self.draw_button(col, "CompositorNodeGlare", text=" Glare                ", icon="NODE_GLARE")
            self.draw_button(col, "CompositorNodeKuwahara", text=" Kuwahara         ", icon="KUWAHARA")
            self.draw_button(col, "CompositorNodePixelate", text=" Pixelate            ", icon="NODE_PIXELATED")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodePosterize", text=" Posterize          ", icon="POSTERIZE")
            self.draw_button(col, "CompositorNodeSunBeams", text=" Sunbeams        ", icon="NODE_SUNBEAMS")



        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeAntiAliasing", text="", icon="ANTIALIASED")
            self.draw_button(flow, "CompositorNodeDenoise", text="", icon="NODE_DENOISE")
            self.draw_button(flow, "CompositorNodeDespeckle", text="", icon="NODE_DESPECKLE")
            self.draw_button(flow, "CompositorNodeDilateErode", text="", icon="NODE_ERODE")
            self.draw_button(flow, "CompositorNodeInpaint", text="", icon="NODE_IMPAINT")
            self.draw_button(flow, "CompositorNodeFilter", text="", icon="FILTER")
            self.draw_button(flow, "CompositorNodeGlare", text="", icon="NODE_GLARE")
            self.draw_button(flow, "CompositorNodeKuwahara", text="", icon="KUWAHARA")
            self.draw_button(flow, "CompositorNodePixelate", text="", icon="NODE_PIXELATED")
            self.draw_button(flow, "CompositorNodePosterize", text="", icon="POSTERIZE")
            self.draw_button(flow, "CompositorNodeSunBeams", text="", icon="NODE_SUNBEAMS")


#Compositor, Add tab, Filter, Blur supbanel
class NODES_PT_comp_add_filter_blur(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Blur"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_comp_add_filter"

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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeBilateralblur", text=" Bilateral Blur    ", icon="NODE_BILATERAL_BLUR")
            self.draw_button(col, "CompositorNodeBlur", text=" Blur                   ", icon="NODE_BLUR")
            self.draw_button(col, "CompositorNodeBokehBlur", text=" Bokeh Blur       ", icon="NODE_BOKEH_BLUR")
            self.draw_button(col, "CompositorNodeDefocus", text=" Defocus           ", icon="NODE_DEFOCUS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeDBlur", text=" Directional Blur ", icon="NODE_DIRECITONALBLUR")
            self.draw_button(col, "CompositorNodeVecBlur", text=" Vector Blur       ", icon="NODE_VECTOR_BLUR")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeBilateralblur", text="", icon="NODE_BILATERAL_BLUR")
            self.draw_button(flow, "CompositorNodeBlur", text="", icon="NODE_BLUR")
            self.draw_button(flow, "CompositorNodeBokehBlur", text="", icon="NODE_BOKEH_BLUR")
            self.draw_button(flow, "CompositorNodeDefocus", text="", icon="NODE_DEFOCUS")
            self.draw_button(flow, "CompositorNodeDBlur", text="", icon="NODE_DIRECITONALBLUR")
            self.draw_button(flow, "CompositorNodeVecBlur", text="", icon="NODE_VECTOR_BLUR")


#Compositor, Add tab, Keying Panel
class NODES_PT_comp_add_keying(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Keying"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeChannelMatte", text=" Channel Key     ", icon="NODE_CHANNEL")
            self.draw_button(col, "CompositorNodeChromaMatte", text=" Chroma Key     ", icon="NODE_CHROMA")
            self.draw_button(col, "CompositorNodeColorMatte", text=" Color Key         ", icon="COLOR")
            self.draw_button(col, "CompositorNodeColorSpill", text=" Color Spill        ", icon="NODE_SPILL")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeDiffMatte", text=" Difference Key ", icon="SELECT_DIFFERENCE")
            self.draw_button(col, "CompositorNodeDistanceMatte", text=" Distance Key   ", icon="DRIVER_DISTANCE")
            self.draw_button(col, "CompositorNodeKeying", text=" Keying              ", icon="NODE_KEYING")
            self.draw_button(col, "CompositorNodeKeyingScreen", text=" Keying Screen  ", icon="NODE_KEYINGSCREEN")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeLumaMatte", text=" Luminance Key ", icon="NODE_LUMINANCE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeChannelMatte", text="", icon="NODE_CHANNEL")
            self.draw_button(flow, "CompositorNodeChromaMatte", text="", icon="NODE_CHROMA")
            self.draw_button(flow, "CompositorNodeColorMatte", text="", icon="COLOR")
            self.draw_button(flow, "CompositorNodeColorSpill", text="", icon="NODE_SPILL")
            self.draw_button(flow, "CompositorNodeDiffMatte", text="", icon="SELECT_DIFFERENCE")
            self.draw_button(flow, "CompositorNodeDistanceMatte", text="", icon="DRIVER_DISTANCE")
            self.draw_button(flow, "CompositorNodeKeying", text="", icon="NODE_KEYING")
            self.draw_button(flow, "CompositorNodeKeyingScreen", text="", icon="NODE_KEYINGSCREEN")
            self.draw_button(flow, "CompositorNodeLumaMatte", text="", icon="NODE_LUMINANCE")


#Compositor, Add tab, Mask Panel
class NODES_PT_comp_add_mask(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mask"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeCryptomatteV2", text=" Cryptomatte    ", icon="CRYPTOMATTE")
            self.draw_button(col, "CompositorNodeCryptomatte", text=" Cryptomatte (Legacy)", icon="CRYPTOMATTE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeBoxMask", text=" Box Mask         ", icon="NODE_BOXMASK")
            self.draw_button(col, "CompositorNodeEllipseMask", text=" Ellipse Mask     ", icon="NODE_ELLIPSEMASK")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeDoubleEdgeMask", text=" Double Edge Mask ", icon="NODE_DOUBLEEDGEMASK")
            self.draw_button(col, "CompositorNodeIDMask", text=" ID Mask           ", icon="MOD_MASK")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeCryptomatte", text="", icon="CRYPTOMATTE")
            self.draw_button(flow, "CompositorNodeCryptomatteV2", text="", icon="CRYPTOMATTE")
            self.draw_button(flow, "CompositorNodeBoxMask", text="", icon="NODE_BOXMASK")
            self.draw_button(flow, "CompositorNodeEllipseMask", text="", icon="NODE_ELLIPSEMASK")
            self.draw_button(flow, "CompositorNodeDoubleEdgeMask", text="", icon="NODE_DOUBLEEDGEMASK")
            self.draw_button(flow, "CompositorNodeIDMask", text="", icon="MOD_MASK")


#Compositor, Add tab, Texture Panel
class NODES_PT_comp_add_texture(bpy.types.Panel, NodePanel):
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexBrick", text=" Brick Texture            ", icon="NODE_BRICK")
            self.draw_button(col, "ShaderNodeTexChecker", text=" Checker Texture       ", icon="NODE_CHECKER")
            self.draw_button(col, "ShaderNodeTexGabor", text=" Gabor Texture        ", icon="GABOR_NOISE")
            self.draw_button(col, "ShaderNodeTexGradient", text=" Gradient Texture      ", icon="NODE_GRADIENT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexMagic", text=" Magic Texture         ", icon="MAGIC_TEX")
            self.draw_button(col, "ShaderNodeTexNoise", text=" Noise Texture         ", icon="NOISE_TEX")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture       ", icon="VORONI_TEX")
            self.draw_button(col, "ShaderNodeTexWave", text=" Wave Texture          ", icon="NODE_WAVES")
            self.draw_button(col, "ShaderNodeTexWhiteNoise", text=" White Noise             ", icon="NODE_WHITE_NOISE")


        #### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeTexBrick", text="", icon="NODE_BRICK")
            self.draw_button(flow, "ShaderNodeTexChecker", text="", icon="NODE_CHECKER")
            self.draw_button(flow, "ShaderNodeTexGabor", text="", icon="GABOR_NOISE")
            self.draw_button(flow, "ShaderNodeTexGradient", text="", icon="NODE_GRADIENT")
            self.draw_button(flow, "ShaderNodeTexMagic", text="", icon="MAGIC_TEX")
            self.draw_button(flow, "ShaderNodeTexNoise", text="", icon="NOISE_TEX")
            self.draw_button(flow, "ShaderNodeTexVoronoi", text="", icon="VORONI_TEX")
            self.draw_button(flow, "ShaderNodeTexWave", text="", icon="NODE_WAVES")
            self.draw_button(flow, "ShaderNodeTexWhiteNoise", text="", icon="NODE_WHITE_NOISE")


#Compositor, Add tab, Tracking Panel
class NODES_PT_comp_add_tracking(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Tracking"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodePlaneTrackDeform", text=" Plane Track Deform ", icon="NODE_PLANETRACKDEFORM")
            self.draw_button(col, "CompositorNodeStabilize", text=" Stabilize 2D     ", icon="NODE_STABILIZE2D")
            self.draw_button(col, "CompositorNodeTrackPos", text=" Track Position  ", icon="NODE_TRACKPOSITION")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodePlaneTrackDeform", text="", icon="NODE_PLANETRACKDEFORM")
            self.draw_button(flow, "CompositorNodeStabilize", text="", icon="NODE_STABILIZE2D")
            self.draw_button(flow, "CompositorNodeTrackPos", text="", icon="NODE_TRACKPOSITION")


#Compositor, Add tab, Transform Panel
class NODES_PT_comp_add_transform(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Transform"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeRotate", text=" Rotate", icon="TRANSFORM_ROTATE")
            self.draw_button(col, "CompositorNodeScale", text=" Scale", icon="TRANSFORM_SCALE")
            self.draw_button(col, "CompositorNodeTransform", text=" Transform", icon="NODE_TRANSFORM")
            self.draw_button(col, "CompositorNodeTranslate", text=" Translate", icon="TRANSFORM_MOVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeCornerPin", text=" Corner Pin", icon="NODE_CORNERPIN")
            self.draw_button(col, "CompositorNodeCrop", text=" Crop", icon="NODE_CROP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeDisplace", text=" Displace", icon="MOD_DISPLACE")
            self.draw_button(col, "CompositorNodeFlip", text=" Flip", icon="FLIP")
            self.draw_button(col, "CompositorNodeMapUV", text=" Map UV", icon="GROUP_UVS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeLensdist", text=" Lens Distortion ", icon="NODE_LENSDISTORT")
            self.draw_button(col, "CompositorNodeMovieDistortion", text=" Movie Distortion ", icon="NODE_MOVIEDISTORT")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeRotate", text="", icon="TRANSFORM_ROTATE")
            self.draw_button(flow, "CompositorNodeScale", text="", icon="TRANSFORM_SCALE")
            self.draw_button(flow, "CompositorNodeTransform", text="", icon="NODE_TRANSFORM")
            self.draw_button(flow, "CompositorNodeTranslate", text="", icon="TRANSFORM_MOVE")
            self.draw_button(flow, "CompositorNodeCornerPin", text="", icon="NODE_CORNERPIN")
            self.draw_button(flow, "CompositorNodeCrop", text="", icon="NODE_CROP")
            self.draw_button(flow, "CompositorNodeDisplace", text="", icon="MOD_DISPLACE")
            self.draw_button(flow, "CompositorNodeFlip", text="", icon="FLIP")
            self.draw_button(flow, "CompositorNodeMapUV", text="", icon="GROUP_UVS")
            self.draw_button(flow, "CompositorNodeLensdist", text="", icon="NODE_LENSDISTORT")
            self.draw_button(flow, "CompositorNodeMovieDistortion", text="", icon="NODE_MOVIEDISTORT")


#Compositor, Add tab, Utility Panel
class NODES_PT_comp_add_utility(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Utilities"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_button(col, "ShaderNodeMix", text="Mix              ", icon="NODE_MIX")
            self.draw_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeLevels", text=" Levels             ", icon="LEVELS")
            self.draw_button(col, "CompositorNodeNormalize", text=" Normalize        ", icon="NODE_NORMALIZE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeSplit", text=" Split                 ", icon="NODE_VIWERSPLIT")
            self.draw_button(col, "CompositorNodeSwitch", text=" Switch              ", icon="SWITCH_DIRECTION")
            self.draw_button(col, "CompositorNodeSwitchView", text=" Switch View    ", icon="VIEW_SWITCHACTIVECAM")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "CompositorNodeRelativeToPixel", text=" Relative to Pixel    ", icon="NODE_RELATIVE_TO_PIXEL")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "CompositorNodeMapRange", text="", icon="NODE_MAP_RANGE")
            self.draw_button(flow, "ShaderNodeMath", text="", icon="NODE_MATH")
            self.draw_button(flow, "ShaderNodeClamp", text="", icon="NODE_CLAMP")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIX")
            self.draw_button(flow, "ShaderNodeFloatCurve", text="", icon="FLOAT_CURVE")
            self.draw_button(flow, "CompositorNodeLevels", text="", icon="LEVELS")
            self.draw_button(flow, "CompositorNodeNormalize", text="", icon="NODE_NORMALIZE")
            self.draw_button(flow, "CompositorNodeSplit", text="", icon="NODE_VIWERSPLIT")
            self.draw_button(flow, "CompositorNodeSwitch", text="", icon="SWITCH_DIRECTION")
            self.draw_button(flow, "CompositorNodeSwitchView", text="", icon="VIEW_SWITCHACTIVECAM")
            self.draw_button(flow, "CompositorNodeRelativeToPixel", text="", icon="NODE_RELATIVE_TO_PIXEL")


#Compositor, Add tab, Vector Panel
class NODES_PT_comp_add_vector(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeCombineXYZ", text=" Combine XYZ  ", icon="NODE_COMBINEXYZ")
            self.draw_button(col, "ShaderNodeSeparateXYZ", text=" Separate XYZ  ", icon="NODE_SEPARATEXYZ")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeMix", text=" Mix Vector       ", icon="NODE_MIX", settings={"data_type": "'VECTOR'"})
            self.draw_button(col, "ShaderNodeVectorCurve", text=" Vector Curves  ", icon="NODE_VECTOR")

            self.draw_button(col, "ShaderNodeVectorMath", text=" Vector Math     ", icon="NODE_VECTORMATH")
            self.draw_button(col, "ShaderNodeVectorRotate", text=" Vector Rotate   ", icon="TRANSFORM_ROTATE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeCombineXYZ", text="", icon="NODE_COMBINEXYZ")
            self.draw_button(flow, "ShaderNodeSeparateXYZ", text="", icon="NODE_SEPARATEXYZ")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIX", settings={"data_type": "'VECTOR'"})
            self.draw_button(flow, "ShaderNodeVectorCurve", text="", icon="NODE_VECTOR")
            self.draw_button(flow, "ShaderNodeVectorMath", text="", icon="NODE_VECTORMATH")
            self.draw_button(flow, "ShaderNodeVectorRotate", text="", icon="TRANSFORM_ROTATE")


#Input nodes tab, textures common panel. Texture mode
class NODES_PT_Input_input_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeImage", text=" Image               ", icon="FILE_IMAGE")
            self.draw_button(col, "TextureNodeTexture", text=" Texture             ", icon="TEXTURE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeImage", text="", icon="FILE_IMAGE")
            self.draw_button(flow, "TextureNodeTexture", text="", icon="TEXTURE")


#Input nodes tab, textures advanced panel. Just in Texture mode
class NODES_PT_Input_textures_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeTexBlend", text=" Blend                 ", icon="BLEND_TEX")
            self.draw_button(col, "TextureNodeTexClouds", text=" Clouds               ", icon="CLOUD_TEX")
            self.draw_button(col, "TextureNodeTexDistNoise", text=" Distorted Noise ", icon="NOISE_TEX")
            self.draw_button(col, "TextureNodeTexMagic", text=" Magic               ", icon="MAGIC_TEX")

            col = layout.column(align=True)
            self.draw_button(col, "TextureNodeTexMarble", text=" Marble              ", icon="MARBLE_TEX")
            self.draw_button(col, "TextureNodeTexNoise", text=" Noise                 ", icon="NOISE_TEX")
            self.draw_button(col, "TextureNodeTexStucci", text=" Stucci                ", icon="STUCCI_TEX")
            self.draw_button(col, "TextureNodeTexVoronoi", text=" Voronoi             ", icon="VORONI_TEX")

            col = layout.column(align=True)
            self.draw_button(col, "TextureNodeTexWood", text=" Wood                ", icon="WOOD_TEX")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeTexBlend", text="", icon="BLEND_TEX")
            self.draw_button(flow, "TextureNodeTexClouds", text="", icon="CLOUD_TEX")
            self.draw_button(flow, "TextureNodeTexDistNoise", text="", icon="NOISE_TEX")
            self.draw_button(flow, "TextureNodeTexMagic", text="", icon="MAGIC_TEX")
            self.draw_button(flow, "TextureNodeTexMarble", text="", icon="MARBLE_TEX")
            self.draw_button(flow, "TextureNodeTexNoise", text="", icon="NOISE_TEX")
            self.draw_button(flow, "TextureNodeTexStucci", text="", icon="STUCCI_TEX")
            self.draw_button(flow, "TextureNodeTexVoronoi", text="", icon="VORONI_TEX")
            self.draw_button(flow, "TextureNodeTexWood", text="", icon="WOOD_TEX")


#Shader Editor - Shader panel
class NODES_PT_shader_add_shader(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and (context.space_data.tree_type == 'ShaderNodeTree' and context.space_data.shader_type in ( 'OBJECT', 'WORLD')) # Just in shader mode, Just in Object and World

    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
        engine = context.engine

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeAddShader", text=" Add                   ", icon="NODE_ADD_SHADER")
            self.draw_button(col, "ShaderNodeBsdfMetallic", text=" Metallic             ", icon="METALLIC")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeBsdfAnisotropic", text=" Anisotopic BSDF", icon="NODE_ANISOTOPIC")
                self.draw_button(col, "ShaderNodeBsdfDiffuse", text=" Diffuse BSDF    ", icon="NODE_DIFFUSESHADER")
                self.draw_button(col, "ShaderNodeEmission", text=" Emission           ", icon="NODE_EMISSION")
                self.draw_button(col, "ShaderNodeBsdfGlass", text=" Glass BSDF       ", icon="NODE_GLASSHADER")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_button(col, "ShaderNodeBsdfGlossy", text=" Glossy BSDF        ", icon="NODE_GLOSSYSHADER")
                self.draw_button(col, "ShaderNodeHoldout", text=" Holdout              ", icon="NODE_HOLDOUTSHADER")
                self.draw_button(col, "ShaderNodeMixShader", text=" Mix Shader        ", icon="NODE_MIXSHADER")
                self.draw_button(col, "ShaderNodeBsdfPrincipled", text=" Principled BSDF", icon="NODE_PRINCIPLED")

                col = layout.column(align=True)
                col.scale_y = 1.5

                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeBsdfHairPrincipled", text=" Principled Hair BSDF  ", icon="CURVES")
                self.draw_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_button(col, "ShaderNodeBsdfRefraction", text=" Refraction BSDF   ", icon="NODE_REFRACTIONSHADER")

                if engine == 'BLENDER_EEVEE':
                    self.draw_button(col, "ShaderNodeEeveeSpecular", text=" Specular BSDF     ", icon="NODE_GLOSSYSHADER")
                self.draw_button(col, "ShaderNodeSubsurfaceScattering", text=" Subsurface Scattering", icon="NODE_SSS")

                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeBsdfToon", text=" Toon BSDF           ", icon="NODE_TOONSHADER")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_button(col, "ShaderNodeBsdfTranslucent", text=" Translucent BSDF  ", icon="NODE_TRANSLUCENT")
                self.draw_button(col, "ShaderNodeBsdfTransparent", text=" Transparent BSDF  ", icon="NODE_TRANSPARENT")

                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeBsdfSheen", text=" Sheen BSDF            ", icon="NODE_VELVET")
                self.draw_button(col, "ShaderNodeVolumeAbsorption", text=" Volume Absorption ", icon="NODE_VOLUMEABSORPTION")
                self.draw_button(col, "ShaderNodeVolumeScatter", text=" Volume Scatter   ", icon="NODE_VOLUMESCATTER")

            if context.space_data.shader_type == 'WORLD':
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_button(col, "ShaderNodeBackground", text=" Background    ", icon="NODE_BACKGROUNDSHADER")
                self.draw_button(col, "ShaderNodeEmission", text=" Emission           ", icon="NODE_EMISSION")
                self.draw_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume       ", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_button(col, "ShaderNodeMixShader", text=" Mix                   ", icon="NODE_MIXSHADER")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_button(flow, "ShaderNodeAddShader", text="", icon="NODE_ADD_SHADER")
            self.draw_button(flow, "ShaderNodeBsdfMetallic", text="", icon="METALLIC")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeBsdfAnisotropic", text="", icon="NODE_ANISOTOPIC")
                self.draw_button(flow, "ShaderNodeBsdfDiffuse", text="", icon="NODE_DIFFUSESHADER")
                self.draw_button(flow, "ShaderNodeEmission", text="", icon="NODE_EMISSION")
                self.draw_button(flow, "ShaderNodeBsdfGlass", text="", icon="NODE_GLASSHADER")
                self.draw_button(flow, "ShaderNodeBsdfGlossy", text="", icon="NODE_GLOSSYSHADER")
                self.draw_button(flow, "ShaderNodeHoldout", text="", icon="NODE_HOLDOUTSHADER")
                self.draw_button(flow, "ShaderNodeMixShader", text="", icon="NODE_MIXSHADER")
                self.draw_button(flow, "ShaderNodeBsdfPrincipled", text="", icon="NODE_PRINCIPLED")

                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeBsdfHairPrincipled", text="", icon="CURVES")
                self.draw_button(flow, "ShaderNodeVolumePrincipled", text="", icon="NODE_VOLUMEPRINCIPLED")

                if engine == 'BLENDER_EEVEE':
                    self.draw_button(flow, "ShaderNodeEeveeSpecular", text="", icon="NODE_GLOSSYSHADER")
                self.draw_button(flow, "ShaderNodeSubsurfaceScattering", text="", icon="NODE_SSS")

                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeBsdfToon", text="", icon="NODE_TOONSHADER")
                self.draw_button(flow, "ShaderNodeBsdfTranslucent", text="", icon="NODE_TRANSLUCENT")
                self.draw_button(flow, "ShaderNodeBsdfTransparent", text="", icon="NODE_TRANSPARENT")

                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeBsdfSheen", text="", icon="NODE_VELVET")
                self.draw_button(flow, "ShaderNodeVolumeAbsorption", text="", icon="NODE_VOLUMEABSORPTION")
                self.draw_button(flow, "ShaderNodeVolumeScatter", text="", icon="NODE_VOLUMESCATTER")

            if context.space_data.shader_type == 'WORLD':
                self.draw_button(flow, "ShaderNodeBackground", text="", icon="NODE_BACKGROUNDSHADER")
                self.draw_button(flow, "ShaderNodeEmission", text="", icon="NODE_EMISSION")
                self.draw_button(flow, "ShaderNodeVolumePrincipled", text="", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_button(flow, "ShaderNodeMixShader", text="", icon="NODE_MIXSHADER")


#Shader Editor - Texture panel
class NODES_PT_shader_add_texture(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and (context.space_data.tree_type == 'ShaderNodeTree') # Just in shader and texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
        engine = context.engine

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexBrick", text=" Brick Texture            ", icon="NODE_BRICK")
            self.draw_button(col, "ShaderNodeTexChecker", text=" Checker Texture       ", icon="NODE_CHECKER")
            self.draw_button(col, "ShaderNodeTexEnvironment", text=" Environment Texture", icon="NODE_ENVIRONMENT")
            self.draw_button(col, "ShaderNodeTexGabor", text=" Gabor Texture        ", icon="GABOR_NOISE")
            self.draw_button(col, "ShaderNodeTexGradient", text=" Gradient Texture      ", icon="NODE_GRADIENT")
            self.draw_button(col, "ShaderNodeTexIES", text=" IES Texture             ", icon="LIGHT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage", text=" Image Texture         ", icon="FILE_IMAGE")
            self.draw_text_button(col, "ShaderNodeTexMagic", text=" Magic Texture         ", icon="MAGIC_TEX")
            self.draw_text_button(col, "ShaderNodeTexNoise", text=" Noise Texture         ", icon="NOISE_TEX")
            self.draw_text_button(col, "ShaderNodeTexSky", text=" Sky Texture             ", icon="NODE_SKY")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture       ", icon="VORONI_TEX")
            self.draw_button(col, "ShaderNodeTexWave", text=" Wave Texture          ", icon="NODE_WAVES")
            self.draw_button(col, "ShaderNodeTexWhiteNoise", text=" White Noise             ", icon="NODE_WHITE_NOISE")


        #### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeTexBrick", text="", icon="NODE_BRICK")
            self.draw_button(flow, "ShaderNodeTexChecker", text="", icon="NODE_CHECKER")
            self.draw_button(flow, "ShaderNodeTexEnvironment", text="", icon="NODE_ENVIRONMENT")
            self.draw_button(flow, "ShaderNodeTexGabor", text="", icon="GABOR_NOISE")
            self.draw_button(flow, "ShaderNodeTexGradient", text="", icon="NODE_GRADIENT")
            self.draw_button(flow, "ShaderNodeTexIES", text="", icon="LIGHT")
            self.draw_button(flow, "ShaderNodeTexImage", text="", icon="FILE_IMAGE")
            self.draw_button(flow, "ShaderNodeTexMagic", text="", icon="MAGIC_TEX")
            self.draw_button(flow, "ShaderNodeTexNoise", text="", icon="NOISE_TEX")
            self.draw_button(flow, "ShaderNodeTexPointDensity", text="", icon="NODE_POINTCLOUD")
            self.draw_button(flow, "ShaderNodeTexSky", text="", icon="NODE_SKY")
            self.draw_button(flow, "ShaderNodeTexVoronoi", text="", icon="VORONI_TEX")
            self.draw_button(flow, "ShaderNodeTexWave", text="", icon="NODE_WAVES")
            self.draw_button(flow, "ShaderNodeTexWhiteNoise", text="", icon="NODE_WHITE_NOISE")


#Shader Editor - Color panel
class NODES_PT_shader_add_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and (context.space_data.tree_type == 'ShaderNodeTree')

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeBrightContrast", text=" Bright / Contrast ", icon="BRIGHTNESS_CONTRAST")
            self.draw_button(col, "ShaderNodeGamma", text=" Gamma              ", icon="NODE_GAMMA")
            self.draw_button(col, "ShaderNodeHueSaturation", text=" Hue / Saturation ", icon="NODE_HUESATURATION")
            self.draw_button(col, "ShaderNodeInvert", text=" Invert Color         ", icon="NODE_INVERT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeLightFalloff", text=" Light Falloff      ", icon="NODE_LIGHTFALLOFF")
            self.draw_button(col, "ShaderNodeMix", text=" Mix Color          ", icon="NODE_MIX", settings={"data_type": "'RGBA'"})
            self.draw_button(col, "ShaderNodeRGBCurve", text="  RGB Curves        ", icon="NODE_RGBCURVE")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeBrightContrast", text="", icon="BRIGHTNESS_CONTRAST")
            self.draw_button(flow, "ShaderNodeGamma", text="", icon="NODE_GAMMA")
            self.draw_button(flow, "ShaderNodeHueSaturation", text="", icon="NODE_HUESATURATION")
            self.draw_button(flow, "ShaderNodeInvert", text="", icon="NODE_INVERT")
            self.draw_button(flow, "ShaderNodeLightFalloff", text="", icon="NODE_LIGHTFALLOFF")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIX", settings={"data_type": "'RGBA'"})
            self.draw_button(flow, "ShaderNodeRGBCurve", text="", icon="NODE_RGBCURVE")


#Input nodes tab, Input panel. Just in texture mode
class NODES_PT_Input_input_advanced_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeCoordinates", text=" Coordinates       ", icon="NODE_TEXCOORDINATE")
            self.draw_button(col, "TextureNodeCurveTime", text=" Curve Time        ", icon="NODE_CURVE_TIME")

        #### Icon Buttons

        else:
            row = layout.row()
            row.alignment = 'LEFT'
            self.draw_button(flow, "TextureNodeCoordinates", text="", icon="NODE_TEXCOORDINATE")
            self.draw_button(flow, "TextureNodeCurveTime", text="", icon="NODE_CURVE_TIME")


#Input nodes tab, Pattern panel. # Just in texture mode
class NODES_PT_Input_pattern(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeBricks", text=" Bricks               ", icon="NODE_BRICK")
            self.draw_button(col, "TextureNodeChecker", text=" Checker            ", icon="NODE_CHECKER")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeBricks", text="", icon="NODE_BRICK")
            self.draw_button(flow, "TextureNodeChecker", text="", icon="NODE_CHECKER")


#Input nodes tab, Color panel. Just in texture mode
class NODES_PT_Input_color_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeCurveRGB", text=" RGB Curves       ", icon="NODE_RGBCURVE")
            self.draw_button(col, "TextureNodeHueSaturation", text=" Hue / Saturation", icon="NODE_HUESATURATION")
            self.draw_button(col, "TextureNodeInvert", text=" Invert Color       ", icon="NODE_INVERT")
            self.draw_button(col, "TextureNodeMixRGB", text=" Mix RGB            ", icon="NODE_MIXRGB")

            col = layout.column(align=True)
            self.draw_button(col, "TextureNodeCompose", text=" Combine RGBA ", icon="NODE_COMBINERGB")
            self.draw_button(col, "TextureNodeDecompose", text=" Separate RGBA ", icon="NODE_SEPARATERGB")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeCurveRGB", text="", icon="NODE_RGBCURVE")
            self.draw_button(flow, "TextureNodeHueSaturation", text="", icon="NODE_HUESATURATION")
            self.draw_button(flow, "TextureNodeInvert", text="", icon="NODE_INVERT")
            self.draw_button(flow, "TextureNodeMixRGB", text="", icon="NODE_MIXRGB")
            self.draw_button(flow, "TextureNodeCompose", text="", icon="NODE_COMBINERGB")
            self.draw_button(flow, "TextureNodeDecompose", text="", icon="NODE_SEPARATERGB")


#Input nodes tab, Output panel, Texture mode
class NODES_PT_Input_output_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeOutput", text=" Output               ", icon="NODE_OUTPUT")
            self.draw_button(col, "TextureNodeViewer", text=" Viewer              ", icon="NODE_VIEWER")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeOutput", text="", icon="NODE_OUTPUT")
            self.draw_button(flow, "TextureNodeViewer", text="", icon="NODE_VIEWER")


#Modify nodes tab, converter panel. Just in texture mode
class NODES_PT_Modify_converter_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeValToRGB", text=" Color Ramp      ", icon="NODE_COLORRAMP")
            self.draw_button(col, "TextureNodeDistance", text=" Distance           ", icon="DRIVER_DISTANCE")
            self.draw_button(col, "TextureNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_button(col, "TextureNodeRGBToBW", text=" RGB to BW       ", icon="NODE_RGBTOBW")

            col = layout.column(align=True)
            self.draw_button(col, "TextureNodeValToNor", text=" Value to Normal ", icon="RECALC_NORMALS")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeValToRGB", text="", icon="NODE_COLORRAMP")
            self.draw_button(flow, "TextureNodeDistance", text="", icon="DRIVER_DISTANCE")
            self.draw_button(flow, "TextureNodeMath", text="", icon="NODE_MATH")
            self.draw_button(flow, "TextureNodeRGBToBW", text="", icon="NODE_RGBTOBW")
            self.draw_button(flow, "TextureNodeValToNor", text="", icon="RECALC_NORMALS")


#Shader Editor - Vector panel
class NODES_PT_shader_add_vector(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader and compositing mode

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeBump", text=" Bump               ", icon="NODE_BUMP")
            self.draw_button(col, "ShaderNodeDisplacement", text=" Displacement ", icon="MOD_DISPLACE")
            self.draw_button(col, "ShaderNodeMapping", text=" Mapping           ", icon="NODE_MAPPING")
            self.draw_button(col, "ShaderNodeNormal", text=" Normal            ", icon="RECALC_NORMALS")
            self.draw_button(col, "ShaderNodeNormalMap", text=" Normal Map     ", icon="NODE_NORMALMAP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeVectorCurve", text=" Vector Curves   ", icon="NODE_VECTOR")
            self.draw_button(col, "ShaderNodeVectorDisplacement", text=" Vector Displacement ", icon="VECTOR_DISPLACE")
            self.draw_button(col, "ShaderNodeVectorRotate", text=" Vector Rotate   ", icon="TRANSFORM_ROTATE")
            self.draw_button(col, "ShaderNodeVectorTransform", text=" Vector Transform ", icon="NODE_VECTOR_TRANSFORM")

        ##### Icon Buttons

        else:

            ##### --------------------------------- Vector ------------------------------------------- ####

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeBump", text="", icon="NODE_BUMP")
            self.draw_button(flow, "ShaderNodeDisplacement", text="", icon="MOD_DISPLACE")
            self.draw_button(flow, "ShaderNodeMapping", text="", icon="NODE_MAPPING")
            self.draw_button(flow, "ShaderNodeNormal", text="", icon="RECALC_NORMALS")
            self.draw_button(flow, "ShaderNodeNormalMap", text="", icon="NODE_NORMALMAP")
            self.draw_button(flow, "ShaderNodeVectorCurve", text="", icon="NODE_VECTOR")
            self.draw_button(flow, "ShaderNodeVectorDisplacement", text="", icon="VECTOR_DISPLACE")
            self.draw_button(flow, "ShaderNodeVectorRotate", text="", icon="TRANSFORM_ROTATE")
            self.draw_button(flow, "ShaderNodeVectorTransform", text="", icon="NODE_VECTOR_TRANSFORM")


#Shader Editor - Converter panel
class NODES_PT_shader_add_converter(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == False and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader and compositing mode

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        engine = context.engine

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeBlackbody", text=" Blackbody        ", icon="NODE_BLACKBODY")
            self.draw_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_button(col, "ShaderNodeValToRGB", text=" ColorRamp       ", icon="NODE_COLORRAMP")
            self.draw_button(col, "ShaderNodeCombineColor", text=" Combine Color ", icon="COMBINE_COLOR")
            self.draw_button(col, "ShaderNodeCombineXYZ", text=" Combine XYZ   ", icon="NODE_COMBINEXYZ")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")
            self.draw_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_button(col, "ShaderNodeMix", text=" Mix                   ", icon="NODE_MIXSHADER")
            self.draw_button(col, "ShaderNodeRGBToBW", text=" RGB to BW      ", icon="NODE_RGBTOBW")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeSeparateColor", text=" Separate Color ", icon="SEPARATE_COLOR")
            self.draw_button(col, "ShaderNodeSeparateXYZ", text=" Separate XYZ   ", icon="NODE_SEPARATEXYZ")

            if engine == 'BLENDER_EEVEE_NEXT':
                self.draw_button(col, "ShaderNodeShaderToRGB", text=" Shader to RGB   ", icon="NODE_RGB")
            self.draw_button(col, "ShaderNodeVectorMath", text=" Vector Math     ", icon="NODE_VECTORMATH")
            self.draw_button(col, "ShaderNodeWavelength", text=" Wavelength     ", icon="NODE_WAVELENGTH")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeBlackbody", text="", icon="NODE_BLACKBODY")
            self.draw_button(flow, "ShaderNodeClamp", text="", icon="NODE_CLAMP")
            self.draw_button(flow, "ShaderNodeValToRGB", text="", icon="NODE_COLORRAMP")
            self.draw_button(flow, "ShaderNodeCombineColor", text="", icon="COMBINE_COLOR")
            self.draw_button(flow, "ShaderNodeCombineXYZ", text="", icon="NODE_COMBINEXYZ")
            self.draw_button(flow, "ShaderNodeFloatCurve", text="", icon="FLOAT_CURVE")
            self.draw_button(flow, "ShaderNodeMapRange", text="", icon="NODE_MAP_RANGE")
            self.draw_button(flow, "ShaderNodeMath", text="", icon="NODE_MATH")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIXSHADER")
            self.draw_button(flow, "ShaderNodeRGBToBW", text="", icon="NODE_RGBTOBW")
            self.draw_button(flow, "ShaderNodeSeparateColor", text="", icon="SEPARATE_COLOR")
            self.draw_button(flow, "ShaderNodeSeparateXYZ", text="", icon="NODE_SEPARATEXYZ")

            if engine == 'BLENDER_EEVEE':
                self.draw_button(flow, "ShaderNodeShaderToRGB", text="", icon="NODE_RGB")
            self.draw_button(flow, "ShaderNodeVectorMath", text="", icon="NODE_VECTORMATH")
            self.draw_button(flow, "ShaderNodeWavelength", text="", icon="NODE_WAVELENGTH")


#Modify nodes tab, distort panel. Just in texture mode
class NODES_PT_Modify_distort_tex(bpy.types.Panel, NodePanel):
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
            self.draw_button(col, "TextureNodeAt", text=" At                      ", icon="NODE_AT")
            self.draw_button(col, "TextureNodeRotate", text=" Rotate              ", icon="TRANSFORM_ROTATE")
            self.draw_button(col, "TextureNodeScale", text=" Scale                ", icon="TRANSFORM_SCALE")
            self.draw_button(col, "TextureNodeTranslate", text=" Translate          ", icon="TRANSFORM_MOVE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "TextureNodeAt", text="", icon="NODE_AT")
            self.draw_button(flow, "TextureNodeRotate", text="", icon="TRANSFORM_ROTATE")
            self.draw_button(flow, "TextureNodeScale", text="", icon="TRANSFORM_SCALE")
            self.draw_button(flow, "TextureNodeTranslate", text="", icon="TRANSFORM_MOVE")


# ------------- Relations tab -------------------------------

#Shader Editor - Relations tab, Group Panel
class NODES_PT_Relations_group(bpy.types.Panel, NodePanel):
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
            col.scale_y = 1.5

            col.operator("node.group_make", text = " Make Group      ", icon = "NODE_MAKEGROUP")
            col.operator("node.group_insert", text = " Insert into Group ", icon = "NODE_GROUPINSERT")
            col.operator("node.group_ungroup", text = " Ungroup           ", icon = "NODE_UNGROUP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            col.operator("node.group_edit", text = " Toggle Edit Group", icon = "NODE_EDITGROUP").exit = False

            col = layout.column(align=True)
            col.scale_y = 1.5

            space_node = context.space_data
            node_tree = space_node.edit_tree
            all_node_groups = context.blend_data.node_groups

            if node_tree in all_node_groups.values():
                self.draw_button(col, "NodeGroupInput", text=" Group Input      ", icon="GROUPINPUT")
                self.draw_button(col, "NodeGroupOutput", text=" Group Output    ", icon="GROUPOUTPUT")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            flow.operator("node.group_make", text = "", icon = "NODE_MAKEGROUP")
            flow.operator("node.group_insert", text = "", icon = "NODE_GROUPINSERT")
            flow.operator("node.group_ungroup", text = "", icon = "NODE_UNGROUP")

            flow.operator("node.group_edit", text = "", icon = "NODE_EDITGROUP").exit = False

            space_node = context.space_data
            node_tree = space_node.edit_tree
            all_node_groups = context.blend_data.node_groups

            if node_tree in all_node_groups.values():
                self.draw_button(flow, "NodeGroupInput", text="", icon="GROUPINPUT")
                self.draw_button(flow, "NodeGroupOutput", text="", icon="GROUPOUTPUT")


#Shader Editor - Relations tab, Node Group Panel
# from nodeitems_builtin, not directly importable
def contains_group(nodetree, group):
    if nodetree == group:
        return True
    else:
        for node in nodetree.nodes:
            if node.bl_idname in node_tree_group_type.values() and node.node_tree is not None:
                if contains_group(node.node_tree, group):
                    return True
    return False

class NODES_PT_Input_node_group(bpy.types.Panel, NodePanel):
    bl_label = "Node Group"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in node_tree_group_type)

    def draw(self, context):
        layout = self.layout

        layout.label( text = "Add Node Group:")

        if context is None:
            return
        space = context.space_data
        if not space:
            return
        ntree = space.edit_tree
        if not ntree:
            return

        for group in context.blend_data.node_groups:
            if group.bl_idname != ntree.bl_idname:
                continue
            # filter out recursive groups
            if contains_group(group, ntree):
                continue
            # filter out hidden nodetrees
            if group.name.startswith('.'):
                continue

            props = layout.operator("node.add_node", text=group.name, icon="NODETREE")
            props.use_transform = True
            props.type = node_tree_group_type[group.bl_idname]

            ops = props.settings.add()
            ops.name = "node_tree"
            ops.value = "bpy.data.node_groups['{0}']".format(group.name)


#Relations tab, Layout Panel
class NODES_PT_Relations_layout(bpy.types.Panel, NodePanel):
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
            col.scale_y = 1.5
            self.draw_button(col, "NodeFrame", text=" Frame               ", icon="NODE_FRAME")
            self.draw_button(col, "NodeReroute", text=" Reroute             ", icon="NODE_REROUTE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "NodeFrame", text="", icon="NODE_FRAME")
            self.draw_button(flow, "NodeReroute", text="", icon="NODE_REROUTE")



# ------------- Geometry Nodes Editor - Add tab -------------------------------

#add attribute panel
class NODES_PT_geom_add_attribute(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Attribute"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeAttributeStatistic", text=" Attribute Statistics  ", icon="ATTRIBUTE_STATISTIC")
            self.draw_button(col, "GeometryNodeAttributeDomainSize", text=" Domain Size            ", icon="DOMAIN_SIZE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeBlurAttribute", text=" Blur Attribute          ", icon="BLUR_ATTRIBUTE")
            self.draw_button(col, "GeometryNodeCaptureAttribute", text=" Capture Attribute    ", icon="ATTRIBUTE_CAPTURE")
            self.draw_button(col, "GeometryNodeRemoveAttribute", text=" Remove Attribute   ", icon="ATTRIBUTE_REMOVE")
            self.draw_button(col, "GeometryNodeStoreNamedAttribute", text=" Store Named Attribute ", icon="ATTRIBUTE_STORE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeAttributeStatistic", text="", icon="ATTRIBUTE_STATISTIC")
            self.draw_button(flow, "GeometryNodeAttributeDomainSize", text="", icon="DOMAIN_SIZE")
            self.draw_button(flow, "GeometryNodeBlurAttribute", text="", icon="BLUR_ATTRIBUTE")
            self.draw_button(flow, "GeometryNodeCaptureAttribute", text="", icon="ATTRIBUTE_CAPTURE")
            self.draw_button(flow, "GeometryNodeRemoveAttribute", text="", icon="ATTRIBUTE_REMOVE")
            self.draw_button(flow, "GeometryNodeStoreNamedAttribute", text="", icon="ATTRIBUTE_STORE")


#add input panel
class NODES_PT_geom_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

    @staticmethod
    def draw(self, context):
        layout = self.layout


#add input panel, constant supbanel
class NODES_PT_geom_add_input_constant(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_input"

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
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeInputBool", text=" Boolean                ", icon="INPUT_BOOL")
            self.draw_button(col, "GeometryNodeInputCollection", text="Collection           ", icon="OUTLINER_COLLECTION")
            self.draw_button(col, "FunctionNodeInputColor", text=" Color                    ", icon="COLOR")
            self.draw_button(col, "GeometryNodeInputImage", text=" Image                  ", icon="FILE_IMAGE")
            self.draw_button(col, "FunctionNodeInputInt", text=" Integer                 ", icon="INTEGER")
            self.draw_button(col, "GeometryNodeInputMaterial", text=" Material               ", icon="NODE_MATERIAL")
            self.draw_button(col, "GeometryNodeInputObject", text="Object               ", icon="OBJECT_DATA")
            self.draw_button(col, "FunctionNodeInputRotation", text=" Rotation               ", icon="ROTATION")
            self.draw_button(col, "FunctionNodeInputString", text=" String                    ", icon="STRING")
            self.draw_button(col, "ShaderNodeValue", text=" Value                    ", icon="NODE_VALUE")
            self.draw_button(col, "FunctionNodeInputVector", text=" Vector                   ", icon="NODE_VECTOR")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_button(flow, "FunctionNodeInputBool", text="", icon="INPUT_BOOL")
            self.draw_button(flow, "GeometryNodeInputCollection", text="", icon="OUTLINER_COLLECTION")
            self.draw_button(flow, "FunctionNodeInputColor", text="", icon="COLOR")
            self.draw_button(flow, "GeometryNodeInputImage", text="", icon="FILE_IMAGE")
            self.draw_button(flow, "FunctionNodeInputInt", text="", icon="INTEGER")
            self.draw_button(flow, "GeometryNodeInputMaterial", text="", icon="NODE_MATERIAL")
            self.draw_button(flow, "GeometryNodeInputObject", text="", icon="OBJECT_DATA")
            self.draw_button(flow, "FunctionNodeInputRotation", text="", icon="ROTATION")
            self.draw_button(flow, "FunctionNodeInputString", text="", icon="STRING")
            self.draw_button(flow, "ShaderNodeValue", text="", icon="NODE_VALUE")
            self.draw_button(flow, "FunctionNodeInputVector", text="", icon="NODE_VECTOR")


#add input panel, gizmo supbanel
class NODES_PT_geom_add_input_gizmo(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Gizmo"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_input"

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeGizmoDial", text=" Dial Gizmo           ", icon="DIAL_GIZMO")
            self.draw_button(col, "GeometryNodeGizmoLinear", text=" Linear Gizmo        ", icon="LINEAR_GIZMO")
            self.draw_button(col, "GeometryNodeGizmoTransform", text=" Transform Gizmo ", icon="TRANSFORM_GIZMO")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_button(flow, "GeometryNodeGizmoDial", text="", icon="DIAL_GIZMO")
            self.draw_button(flow, "GeometryNodeGizmoLinear", text="", icon="LINEAR_GIZMO")
            self.draw_button(flow, "GeometryNodeGizmoTransform", text="", icon="TRANSFORM_GIZMO")


#add input panel, file supbanel
class NODES_PT_geom_add_input_file(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Import"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_input"

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeImportOBJ", text=" Import OBJ           ", icon="LOAD_OBJ")
            self.draw_button(col, "GeometryNodeImportPLY", text=" Import PLY           ", icon="LOAD_PLY")
            self.draw_button(col, "GeometryNodeImportSTL", text=" Import STL           ", icon="LOAD_STL")
            self.draw_button(col, "GeometryNodeImportCSV", text=" Import CSV           ", icon="LOAD_CSV")
            self.draw_button(col, "GeometryNodeImportText", text=" Import Text           ", icon="FILE_TEXT")
            self.draw_button(col, "GeometryNodeImportVDB", text=" Import OpenVDB   ", icon="FILE_VOLUME")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeImportOBJ", text="", icon="LOAD_OBJ")
            self.draw_button(flow, "GeometryNodeImportPLY", text="", icon="LOAD_PLY")
            self.draw_button(flow, "GeometryNodeImportSTL", text="", icon="LOAD_STL")
            self.draw_button(flow, "GeometryNodeImportCSV", text="", icon="LOAD_CSV")
            self.draw_button(flow, "GeometryNodeImportText", text="", icon="FILE_TEXT")
            self.draw_button(flow, "GeometryNodeImportVDB", text="", icon="FILE_VOLUME")



#add input panel, scene subpanel
class NODES_PT_geom_add_input_scene(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Scene"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_input"

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
            col.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeTool3DCursor", text=" Cursor                  ", icon="CURSOR")
            self.draw_button(col, "GeometryNodeInputActiveCamera", text=" Active Camera     ", icon="VIEW_SWITCHTOCAM")
            self.draw_button(col, "GeometryNodeCameraInfo", text=" Camera Info     ", icon="CAMERA_DATA")
            self.draw_button(col, "GeometryNodeCollectionInfo", text=" Collection Info     ", icon="COLLECTION_INFO")
            self.draw_button(col, "GeometryNodeImageInfo", text=" Image Info           ", icon="IMAGE_INFO")
            self.draw_button(col, "GeometryNodeIsViewport", text=" Is Viewport          ", icon="VIEW")
            self.draw_button(col, "GeometryNodeInputNamedLayerSelection", text=" Named Layer Selection  ", icon="NAMED_LAYER_SELECTION")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeToolMousePosition", text=" Mouse Position    ", icon="MOUSE_POSITION")
            self.draw_button(col, "GeometryNodeObjectInfo", text=" Object Info           ", icon="NODE_OBJECTINFO")
            self.draw_button(col, "GeometryNodeInputSceneTime", text=" Scene Time          ", icon="TIME")
            self.draw_button(col, "GeometryNodeSelfObject", text=" Self Object           ", icon="SELF_OBJECT")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeViewportTransform", text=" Viewport Transform ", icon="VIEWPORT_TRANSFORM")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeTool3DCursor", text="", icon="CURSOR")
            self.draw_button(flow, "GeometryNodeInputActiveCamera", text="", icon="VIEW_SWITCHTOCAM")
            self.draw_button(flow, "GeometryNodeCameraInfo", text="", icon="CAMERA_DATA")
            self.draw_button(flow, "GeometryNodeCollectionInfo", text="", icon="COLLECTION_INFO")
            self.draw_button(flow, "GeometryNodeImageInfo", text="", icon="IMAGE_INFO")
            self.draw_button(flow, "GeometryNodeIsViewport", text="", icon="VIEW")
            self.draw_button(flow, "GeometryNodeInputNamedLayerSelection", text="", icon="NAMED_LAYER_SELECTION")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeToolMousePosition", text="", icon="MOUSE_POSITION")
            self.draw_button(flow, "GeometryNodeObjectInfo", text="", icon="NODE_OBJECTINFO")
            self.draw_button(flow, "GeometryNodeInputSceneTime", text="", icon="TIME")
            self.draw_button(flow, "GeometryNodeSelfObject", text="", icon="SELF_OBJECT")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeViewportTransform", text="", icon="VIEWPORT_TRANSFORM")


#add output panel
class NODES_PT_geom_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeViewer", text=" Viewer   ", icon="NODE_VIEWER")
            self.draw_button(col, "GeometryNodeWarning", text=" Warning   ", icon="ERROR")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeViewer", text="", icon="NODE_VIEWER")
            self.draw_button(flow, "GeometryNodeWarning", text="", icon="ERROR")


#add geometry panel
class NODES_PT_geom_add_geometry(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Geometry"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeGeometryToInstance", text=" Geometry to Instance", icon="GEOMETRY_INSTANCE")
            self.draw_button(col, "GeometryNodeJoinGeometry", text=" Join Geometry           ", icon="JOIN")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeGeometryToInstance", text="", icon="GEOMETRY_INSTANCE")
            self.draw_button(flow, "GeometryNodeJoinGeometry", text="", icon="JOIN")


#add geometry panel, read subpanel
class NODES_PT_geom_add_geometry_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInputID", text=" ID                               ", icon="GET_ID")
            self.draw_button(col, "GeometryNodeInputIndex", text=" Index                          ", icon="INDEX")
            self.draw_button(col, "GeometryNodeInputNamedAttribute", text=" Named Attribute       ", icon="NAMED_ATTRIBUTE")
            self.draw_button(col, "GeometryNodeInputNormal", text=" Normal                      ", icon="RECALC_NORMALS")
            self.draw_button(col, "GeometryNodeInputPosition", text=" Position                     ", icon="POSITION")
            self.draw_button(col, "GeometryNodeInputRadius", text=" Radius                       ", icon="RADIUS")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeToolSelection", text=" Selection                    ", icon="RESTRICT_SELECT_OFF")
                self.draw_button(col, "GeometryNodeToolActiveElement", text=" Active Element          ", icon="ACTIVE_ELEMENT")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeInputID", text="", icon="GET_ID")
            self.draw_button(flow, "GeometryNodeInputIndex", text="", icon="INDEX")
            self.draw_button(flow, "GeometryNodeInputNamedAttribute", text="", icon="NAMED_ATTRIBUTE")
            self.draw_button(flow, "GeometryNodeInputNormal", text="", icon="RECALC_NORMALS")
            self.draw_button(flow, "GeometryNodeInputPosition", text="", icon="POSITION")
            self.draw_button(flow, "GeometryNodeInputRadius", text="", icon="RADIUS")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeToolSelection", text="", icon="RESTRICT_SELECT_OFF")
                self.draw_button(flow, "GeometryNodeToolActiveElement", text="", icon="ACTIVE_ELEMENT")



#add geometry panel, sample subpanel
class NODES_PT_geom_add_geometry_sample(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeProximity", text=" Geometry Proximity   ", icon="GEOMETRY_PROXIMITY")
            self.draw_button(col, "GeometryNodeIndexOfNearest", text=" Index of Nearest        ", icon="INDEX_OF_NEAREST")
            self.draw_button(col, "GeometryNodeRaycast", text=" Raycast                      ", icon="RAYCAST")
            self.draw_button(col, "GeometryNodeSampleIndex", text=" Sample Index             ", icon="SAMPLE_INDEX")
            self.draw_button(col, "GeometryNodeSampleNearest", text=" Sample Nearest        ", icon="SAMPLE_NEAREST")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeMergeByDistance", text="", icon="GEOMETRY_PROXIMITY")
            self.draw_button(flow, "GeometryNodeIndexOfNearest", text="", icon="INDEX_OF_NEAREST")
            self.draw_button(flow, "GeometryNodeRaycast", text="", icon="RAYCAST")
            self.draw_button(flow, "GeometryNodeSampleIndex", text="", icon="SAMPLE_INDEX")
            self.draw_button(flow, "GeometryNodeSampleNearest", text="", icon="SAMPLE_NEAREST")


#add geometry panel, write subpanel
class NODES_PT_geom_add_geometry_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSetGeometryName", text=" Set Geometry Name  ", icon="GEOMETRY_NAME")
            self.draw_button(col, "GeometryNodeSetID", text=" Set ID                          ", icon="SET_ID")
            self.draw_button(col, "GeometryNodeSetPosition", text=" Set Postion                 ", icon="SET_POSITION")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeToolSetSelection", text=" Set Selection                 ", icon="SET_SELECTION")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeSetGeometryName", text="", icon="GEOMETRY_NAME")
            self.draw_button(flow, "GeometryNodeSetID", text="", icon="SET_ID")
            self.draw_button(flow, "GeometryNodeSetPosition", text="", icon="SET_POSITION")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeToolSetSelection", text="", icon="SET_SELECTION")


#add geometry panel, operations subpanel
class NODES_PT_geom_add_geometry_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeBake", text=" Bake                            ", icon="BAKE")
            self.draw_button(col, "GeometryNodeBoundBox", text=" Bounding Box             ", icon="PIVOT_BOUNDBOX")
            self.draw_button(col, "GeometryNodeConvexHull", text=" Convex Hull                ", icon="CONVEXHULL")
            self.draw_button(col, "GeometryNodeDeleteGeometry", text=" Delete Geometry       ", icon="DELETE")
            self.draw_button(col, "GeometryNodeDuplicateElements", text=" Duplicate Geometry ", icon="DUPLICATE")
            self.draw_button(col, "GeometryNodeMergeByDistance", text=" Merge by Distance    ", icon="REMOVE_DOUBLES")
            self.draw_button(col, "GeometryNodeSortElements", text=" Sort Elements    ", icon="SORTSIZE")
            self.draw_button(col, "GeometryNodeTransform", text=" Transform Geometry  ", icon="NODE_TRANSFORM")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSeparateComponents", text=" Separate Components", icon="SEPARATE")
            self.draw_button(col, "GeometryNodeSeparateGeometry", text=" Separate Geometry   ", icon="SEPARATE_GEOMETRY")
            self.draw_button(col, "GeometryNodeSplitToInstances", text=" Split to Instances   ", icon="SPLIT_TO_INSTANCES")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeBake", text="", icon="BAKE")
            self.draw_button(flow, "GeometryNodeBoundBox", text="", icon="PIVOT_BOUNDBOX")
            self.draw_button(flow, "GeometryNodeConvexHull", text="", icon="CONVEXHULL")
            self.draw_button(flow, "GeometryNodeDeleteGeometry", text="", icon="DELETE")
            self.draw_button(flow, "GeometryNodeDuplicateElements", text="", icon="DUPLICATE")
            self.draw_button(flow, "GeometryNodeMergeByDistance", text="", icon="REMOVE_DOUBLES")
            self.draw_button(flow, "GeometryNodeSortElements", text="", icon="SORTSIZE")
            self.draw_button(flow, "GeometryNodeTransform", text="", icon="NODE_TRANSFORM")
            self.draw_button(flow, "GeometryNodeSeparateComponents", text="", icon="SEPARATE")
            self.draw_button(flow, "GeometryNodeSeparateGeometry", text="", icon="SEPARATE_GEOMETRY")
            self.draw_button(flow, "GeometryNodeSplitToInstances", text="", icon="SPLIT_TO_INSTANCES")


#add Curves panel
class NODES_PT_geom_add_curve(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Curve"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

    @staticmethod
    def draw(self, context):
        layout = self.layout

#add Curves panel, read subpanel
class NODES_PT_geom_add_curve_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInputCurveHandlePositions", text=" Curve Handle Positions ", icon="CURVE_HANDLE_POSITIONS")
            self.draw_button(col, "GeometryNodeCurveLength", text=" Curve Length              ", icon="PARTICLEBRUSH_LENGTH")
            self.draw_button(col, "GeometryNodeInputTangent", text=" Curve Tangent           ", icon="CURVE_TANGENT")
            self.draw_button(col, "GeometryNodeInputCurveTilt", text=" Curve Tilt                 ", icon="CURVE_TILT")
            self.draw_button(col, "GeometryNodeCurveEndpointSelection", text=" Endpoint Selection    ", icon="SELECT_LAST")
            self.draw_button(col, "GeometryNodeCurveHandleTypeSelection", text=" Handle Type Selection", icon="SELECT_HANDLETYPE")
            self.draw_button(col, "GeometryNodeInputSplineCyclic", text=" Is Spline Cyclic          ", icon="IS_SPLINE_CYCLIC")
            self.draw_button(col, "GeometryNodeSplineLength", text=" Spline Length             ", icon="SPLINE_LENGTH")
            self.draw_button(col, "GeometryNodeSplineParameter", text=" Spline Parameter      ", icon="CURVE_PARAMETER")
            self.draw_button(col, "GeometryNodeInputSplineResolution", text=" Spline Resolution        ", icon="SPLINE_RESOLUTION")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeInputCurveHandlePositions", text="", icon="CURVE_HANDLE_POSITIONS")
            self.draw_button(flow, "GeometryNodeCurveLength", text="", icon="PARTICLEBRUSH_LENGTH")
            self.draw_button(flow, "GeometryNodeInputTangent", text="", icon="CURVE_TANGENT")
            self.draw_button(flow, "GeometryNodeInputCurveTilt", text="", icon="CURVE_TILT")
            self.draw_button(flow, "GeometryNodeCurveEndpointSelection", text="", icon="SELECT_LAST")
            self.draw_button(flow, "GeometryNodeCurveHandleTypeSelection", text="", icon="SELECT_HANDLETYPE")
            self.draw_button(flow, "GeometryNodeInputSplineCyclic", text="", icon="IS_SPLINE_CYCLIC")
            self.draw_button(flow, "GeometryNodeSplineLength", text="", icon="SPLINE_LENGTH")
            self.draw_button(flow, "GeometryNodeSplineParameter", text="", icon="CURVE_PARAMETER")
            self.draw_button(flow, "GeometryNodeInputSplineResolution", text="", icon="SPLINE_RESOLUTION")


#add Curves panel, read subpanel
class NODES_PT_geom_add_curve_sample(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSampleCurve", text=" Sample Curve ", icon="CURVE_SAMPLE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeSampleCurve", text="", icon="CURVE_SAMPLE")




#add Curves panel, write subpanel
class NODES_PT_geom_add_curve_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSetCurveNormal", text=" Set Curve Normal        ", icon="CURVE_NORMAL")
            self.draw_button(col, "GeometryNodeSetCurveRadius", text=" Set Curve Radius        ", icon="SET_CURVE_RADIUS")
            self.draw_button(col, "GeometryNodeSetCurveTilt", text=" Set Curve Tilt             ", icon="SET_CURVE_TILT")
            self.draw_button(col, "GeometryNodeSetCurveHandlePositions", text=" Set Handle Positions   ", icon="SET_CURVE_HANDLE_POSITIONS")
            self.draw_button(col, "GeometryNodeCurveSetHandles", text=" Set Handle Type         ", icon="HANDLE_AUTO")
            self.draw_button(col, "GeometryNodeSetSplineCyclic", text=" Set Spline Cyclic        ", icon="TOGGLE_CYCLIC")
            self.draw_button(col, "GeometryNodeSetSplineResolution", text=" Set Spline Resolution   ", icon="SET_SPLINE_RESOLUTION")
            self.draw_button(col, "GeometryNodeCurveSplineType", text=" Set Spline Type            ", icon="SPLINE_TYPE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeSetCurveNormal", text="", icon="CURVE_NORMAL")
            self.draw_button(flow, "GeometryNodeSetCurveRadius", text="", icon="SET_CURVE_RADIUS")
            self.draw_button(flow, "GeometryNodeSetCurveTilt", text="", icon="SET_CURVE_TILT")
            self.draw_button(flow, "GeometryNodeSetCurveHandlePositions", text="", icon="SET_CURVE_HANDLE_POSITIONS")
            self.draw_button(flow, "GeometryNodeCurveSetHandles", text="", icon="HANDLE_AUTO")
            self.draw_button(flow, "GeometryNodeSetSplineCyclic", text="", icon="TOGGLE_CYCLIC")
            self.draw_button(flow, "GeometryNodeSetSplineResolution", text="", icon="SET_SPLINE_RESOLUTION")
            self.draw_button(flow, "GeometryNodeCurveSplineType", text="", icon="SPLINE_TYPE")


#add Curves panel, operations subpanel
class NODES_PT_geom_add_curve_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeCurvesToGreasePencil", text=" Curves to Grease Pencil", icon="OUTLINER_OB_GREASEPENCIL")
            self.draw_button(col, "GeometryNodeCurveToMesh", text=" Curve to Mesh            ", icon="OUTLINER_OB_MESH")
            self.draw_button(col, "GeometryNodeCurveToPoints", text=" Curve to Points          ", icon="POINTCLOUD_DATA")
            self.draw_button(col, "GeometryNodeDeformCurvesOnSurface", text=" Deform Curves on Surface ", icon="DEFORM_CURVES")
            self.draw_button(col, "GeometryNodeFillCurve", text=" Fill Curve                   ", icon="CURVE_FILL")
            self.draw_button(col, "GeometryNodeFilletCurve", text=" Fillet Curve                ", icon="CURVE_FILLET")
            self.draw_button(col, "GeometryNodeGreasePencilToCurves", text=" Grease Pencil to Curves", icon="OUTLINER_OB_CURVES")
            self.draw_button(col, "GeometryNodeInterpolateCurves", text=" Interpolate Curve    ", icon="INTERPOLATE_CURVE")
            self.draw_button(col, "GeometryNodeInterpolateCurves", text=" Merge Layers            ", icon="MERGE")
            self.draw_button(col, "GeometryNodeResampleCurve", text=" Resample Curve        ", icon="CURVE_RESAMPLE")
            self.draw_button(col, "GeometryNodeReverseCurve", text=" Reverse Curve           ", icon="SWITCH_DIRECTION")
            self.draw_button(col, "GeometryNodeSubdivideCurve", text=" Subdivide Curve       ", icon="SUBDIVIDE_EDGES")
            self.draw_button(col, "GeometryNodeTrimCurve", text=" Trim Curve                  ", icon="CURVE_TRIM")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeCurvesToGreasePencil", text="", icon="OUTLINER_OB_GREASEPENCIL")
            self.draw_button(flow, "GeometryNodeCurveToMesh", text="", icon="OUTLINER_OB_MESH")
            self.draw_button(flow, "GeometryNodeCurveToPoints", text="", icon="POINTCLOUD_DATA")
            self.draw_button(flow, "GeometryNodeDeformCurvesOnSurface", text="", icon="DEFORM_CURVES")
            self.draw_button(flow, "GeometryNodeFillCurve", text="", icon="CURVE_FILL")
            self.draw_button(flow, "GeometryNodeFilletCurve", text="", icon="CURVE_FILLET")
            self.draw_button(flow, "GeometryNodeGreasePencilToCurves", text="", icon="OUTLINER_OB_CURVES")
            self.draw_button(flow, "GeometryNodeInterpolateCurves", text="", icon="INTERPOLATE_CURVE")
            self.draw_button(flow, "GeometryNodeInterpolateCurves", text="", icon="MERGE")
            self.draw_button(flow, "GeometryNodeResampleCurve", text="", icon="CURVE_RESAMPLE")
            self.draw_button(flow, "GeometryNodeReverseCurve", text="", icon="SWITCH_DIRECTION")
            self.draw_button(flow, "GeometryNodeSubdivideCurve", text="", icon="SUBDIVIDE_EDGES")
            self.draw_button(flow, "GeometryNodeTrimCurve", text="", icon="CURVE_TRIM")


#add Curves panel, Primitives subpanel
class NODES_PT_geom_add_curve_primitives(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Primitives"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeCurveArc", text=" Arc                        ", icon="CURVE_ARC")
            self.draw_button(col, "GeometryNodeCurvePrimitiveBezierSegment", text=" Bezier Segment     ", icon="CURVE_BEZCURVE")
            self.draw_button(col, "GeometryNodeCurvePrimitiveCircle", text=" Curve Circle           ", icon="CURVE_BEZCIRCLE")
            self.draw_button(col, "GeometryNodeCurvePrimitiveLine", text=" Curve Line             ", icon="CURVE_LINE")
            self.draw_button(col, "GeometryNodeCurveSpiral", text=" Curve Spiral           ", icon="CURVE_SPIRAL")
            self.draw_button(col, "GeometryNodeCurveQuadraticBezier", text=" Quadratic Bezier    ", icon="CURVE_NCURVE")
            self.draw_button(col, "GeometryNodeCurvePrimitiveQuadrilateral", text=" Quadrilateral         ", icon="CURVE_QUADRILATERAL")
            self.draw_button(col, "GeometryNodeCurveStar", text=" Star                       ", icon="CURVE_STAR")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeCurveArc", text="", icon="CURVE_ARC")
            self.draw_button(flow, "GeometryNodeCurvePrimitiveBezierSegment", text="", icon="CURVE_BEZCURVE")
            self.draw_button(flow, "GeometryNodeCurvePrimitiveCircle", text="", icon="CURVE_BEZCIRCLE")
            self.draw_button(flow, "GeometryNodeCurvePrimitiveLine", text="", icon="CURVE_LINE")
            self.draw_button(flow, "GeometryNodeCurveSpiral", text="", icon="CURVE_SPIRAL")
            self.draw_button(flow, "GeometryNodeCurveQuadraticBezier", text="", icon="CURVE_NCURVE")
            self.draw_button(flow, "GeometryNodeCurvePrimitiveQuadrilateral", text="", icon="CURVE_QUADRILATERAL")
            self.draw_button(flow, "GeometryNodeCurveStar", text="", icon="CURVE_STAR")


#add Curve panel, Topology subpanel
class NODES_PT_geom_add_curve_topology(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Topology"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeCurveOfPoint", text=" Curve of Point              ", icon="CURVE_OF_POINT")
            self.draw_button(col, "GeometryNodeOffsetPointInCurve", text=" Offset Point in Curve   ", icon="OFFSET_POINT_IN_CURVE")
            self.draw_button(col, "GeometryNodePointsOfCurve", text=" Points of Curve            ", icon="POINT_OF_CURVE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeCurveOfPoint", text="", icon="CURVE_OF_POINT")
            self.draw_button(flow, "GeometryNodeOffsetPointInCurve", text="", icon="OFFSET_POINT_IN_CURVE")
            self.draw_button(flow, "GeometryNodePointsOfCurve", text="", icon="POINT_OF_CURVE")


#add Grease Pencil panel
class NODES_PT_geom_add_grease_pencil(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Grease Pencil"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

    @staticmethod
    def draw(self, context):
        layout = self.layout


#add Grease Pencil panel, Read subpanel
class NODES_PT_geom_add_grease_pencil_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_grease_pencil"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInputNamedLayerSelection", text=" Named Layer Selection              ", icon="NAMED_LAYER_SELECTION")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeInputNamedLayerSelection", text="", icon="NAMED_LAYER_SELECTION")


#add Grease Pencil panel, Read subpanel
class NODES_PT_geom_add_grease_pencil_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_grease_pencil"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSetGreasePencilColor", text=" Set Grease Pencil Color              ", icon="COLOR")
            self.draw_button(col, "GeometryNodeSetGreasePencilDepth", text=" Set Grease Pencil Depth             ", icon="DEPTH")
            self.draw_button(col, "GeometryNodeSetGreasePencilSoftness", text=" Set Grease Pencil Softness             ", icon="FALLOFFSTROKE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeSetGreasePencilColor", text="", icon="COLOR")
            self.draw_button(flow, "GeometryNodeSetGreasePencilDepth", text="", icon="DEPTH")
            self.draw_button(flow, "GeometryNodeSetGreasePencilSoftness", text="", icon="FALLOFFSTROKE")


#add Grease Pencil panel, Read subpanel
class NODES_PT_geom_add_grease_pencil_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_grease_pencil"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeGreasePencilToCurves", text=" Set Grease Pencil to Curves              ", icon="OUTLINER_OB_CURVES")
            self.draw_button(col, "GeometryNodeMergeLayers", text=" Merge Layers                  ", icon="MERGE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeGreasePencilToCurves", text="", icon="OUTLINER_OB_CURVES")
            self.draw_button(flow, "GeometryNodeMergeLayers", text="", icon="MERGE")


#add mesh panel
class NODES_PT_geom_add_instances(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Instances"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInstanceOnPoints", text=" Instances on Points       ", icon="POINT_INSTANCE")
            self.draw_button(col, "GeometryNodeInstancesToPoints", text=" Instances to Points       ", icon="INSTANCES_TO_POINTS")
            self.draw_button(col, "GeometryNodeRealizeInstances", text=" Realize Instances         ", icon="MOD_INSTANCE")
            self.draw_button(col, "GeometryNodeRotateInstances", text=" Rotate Instances          ", icon="ROTATE_INSTANCE")
            self.draw_button(col, "GeometryNodeScaleInstances", text=" Scale Instances            ", icon="SCALE_INSTANCE")
            self.draw_button(col, "GeometryNodeTranslateInstances", text=" Translate Instances      ", icon="TRANSLATE_INSTANCE")
            self.draw_button(col, "GeometryNodeSetInstanceTransform", text=" Set Instance Transform      ", icon="INSTANCE_TRANSFORM")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInstanceTransform", text=" Instance Transform     ", icon="INSTANCE_TRANSFORM_GET")
            self.draw_button(col, "GeometryNodeInputInstanceRotation", text=" Instance Rotation     ", icon="INSTANCE_ROTATE")
            self.draw_button(col, "GeometryNodeInputInstanceScale", text=" Instance Scale      ", icon="INSTANCE_SCALE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeInstanceOnPoints", text="", icon="POINT_INSTANCE")
            self.draw_button(flow, "GeometryNodeInstancesToPoints", text="", icon="INSTANCES_TO_POINTS")
            self.draw_button(flow, "GeometryNodeRealizeInstances", text="", icon="MOD_INSTANCE")
            self.draw_button(flow, "GeometryNodeRotateInstances", text="", icon="ROTATE_INSTANCE")
            self.draw_button(flow, "GeometryNodeTriangulate", text="", icon="SCALE_INSTANCE")
            self.draw_button(flow, "GeometryNodeTranslateInstances", text="", icon="TRANSLATE_INSTANCE")
            self.draw_button(flow, "GeometryNodeSetInstanceTransform", text="", icon="INSTANCE_TRANSFORM")
            self.draw_button(flow, "GeometryNodeInstanceTransform", text="", icon="INSTANCE_TRANSFORM_GET")
            self.draw_button(flow, "GeometryNodeInputInstanceRotation", text="", icon="INSTANCE_ROTATE")
            self.draw_button(flow, "GeometryNodeInputInstanceScale", text="", icon="INSTANCE_SCALE")


#add mesh panel
class NODES_PT_geom_add_mesh(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mesh"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

    @staticmethod
    def draw(self, context):
        layout = self.layout


#add mesh panel, read subpanel
class NODES_PT_geom_add_mesh_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInputMeshEdgeAngle", text=" Edge Angle              ", icon="EDGE_ANGLE")
            self.draw_button(col, "GeometryNodeInputMeshEdgeNeighbors", text=" Edge Neighbors       ", icon="EDGE_NEIGHBORS")
            self.draw_button(col, "GeometryNodeInputMeshEdgeVertices", text=" Edge Vertices          ", icon="EDGE_VERTICES")
            self.draw_button(col, "GeometryNodeEdgesToFaceGroups", text=" Edges to Face Groups ", icon="FACEGROUP")
            self.draw_button(col, "GeometryNodeInputMeshFaceArea", text=" Face Area                ", icon="FACEREGIONS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeMeshFaceSetBoundaries", text=" Face Group Boundaries ", icon="SELECT_BOUNDARY")
            self.draw_button(col, "GeometryNodeInputMeshFaceNeighbors", text=" Face Neighbors        ", icon="FACE_NEIGHBORS")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeToolFaceSet", text=" Face Set        ", icon="FACE_SET")
            self.draw_button(col, "GeometryNodeInputMeshFaceIsPlanar", text=" Is Face Planar         ", icon="PLANAR")
            self.draw_button(col, "GeometryNodeInputShadeSmooth", text=" Is Face Smooth     ", icon="SHADING_SMOOTH")
            self.draw_button(col, "GeometryNodeInputEdgeSmooth", text=" is Edge Smooth      ", icon="SHADING_EDGE_SMOOTH")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeInputMeshIsland", text=" Mesh Island             ", icon="UV_ISLANDSEL")
            self.draw_button(col, "GeometryNodeInputShortestEdgePaths", text=" Shortest Edge Path ", icon="SELECT_SHORTESTPATH")
            self.draw_button(col, "GeometryNodeInputMeshVertexNeighbors", text=" Vertex Neighbors   ", icon="VERTEX_NEIGHBORS")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeInputMeshEdgeAngle", text="", icon="EDGE_ANGLE")
            self.draw_button(flow, "GeometryNodeInputMeshEdgeNeighbors", text="", icon="EDGE_NEIGHBORS")
            self.draw_button(flow, "GeometryNodeInputMeshEdgeVertices", text="", icon="EDGE_VERTICES")
            self.draw_button(flow, "GeometryNodeEdgesToFaceGroups", text="", icon="FACEGROUP")
            self.draw_button(flow, "GeometryNodeInputMeshFaceArea", text="", icon="FACEREGIONS")
            self.draw_button(flow, "GeometryNodeMeshFaceSetBoundaries", text="", icon="SELECT_BOUNDARY")
            self.draw_button(flow, "GeometryNodeInputMeshFaceNeighbors", text="", icon="FACE_NEIGHBORS")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeToolFaceSet", text="", icon="FACE_SET")
            self.draw_button(flow, "GeometryNodeInputMeshFaceIsPlanar", text="", icon="PLANAR")
            self.draw_button(flow, "GeometryNodeInputShadeSmooth", text="", icon="SHADING_SMOOTH")
            self.draw_button(flow, "GeometryNodeInputEdgeSmooth", text="", icon="SHADING_EDGE_SMOOTH")
            self.draw_button(flow, "GeometryNodeInputMeshIsland", text="", icon="UV_ISLANDSEL")
            self.draw_button(flow, "GeometryNodeInputShortestEdgePaths", text="", icon="SELECT_SHORTESTPATH")
            self.draw_button(flow, "GeometryNodeInputMeshVertexNeighbors", text="", icon="VERTEX_NEIGHBORS")


#add mesh panel, sample subpanel
class NODES_PT_geom_add_mesh_sample(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSampleNearestSurface", text=" Sample Nearest Surface ", icon="SAMPLE_NEAREST_SURFACE")
            self.draw_button(col, "GeometryNodeSampleUVSurface", text=" Sample UV Surface   ", icon="SAMPLE_UV_SURFACE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeSampleNearestSurface", text="", icon="SAMPLE_NEAREST_SURFACE")
            self.draw_button(flow, "GeometryNodeSampleUVSurface", text="", icon="SAMPLE_UV_SURFACE")


#add mesh panel, write subpanel
class NODES_PT_geom_add_mesh_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(col, "GeometryNodeToolFaceSet", text=" Set Face Set   ", icon="FACE_SET")
            self.draw_button(col, "GeometryNodeSetMeshNormal", text=" Set Mesh Normal   ", icon="SET_SMOOTH")
            self.draw_button(col, "GeometryNodeSetShadeSmooth", text=" Set Shade Smooth   ", icon="SET_SHADE_SMOOTH")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_button(flow, "GeometryNodeToolSetFaceSet", text="", icon="SET_FACE_SET")
            self.draw_button(flow, "GeometryNodeSetMeshNormal", text="", icon="SET_SMOOTH")
            self.draw_button(flow, "GeometryNodeSetShadeSmooth", text="", icon="SET_SHADE_SMOOTH")


#add mesh panel, operations subpanel
class NODES_PT_geom_add_mesh_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeDualMesh", text=" Dual Mesh               ", icon="DUAL_MESH")
            self.draw_button(col, "GeometryNodeEdgePathsToCurves", text=" Edge Paths to Curves ", icon="EDGE_PATHS_TO_CURVES")
            self.draw_button(col, "GeometryNodeEdgePathsToSelection", text=" Edge Paths to Selection ", icon="EDGE_PATH_TO_SELECTION")
            self.draw_button(col, "GeometryNodeExtrudeMesh", text=" Extrude Mesh             ", icon="EXTRUDE_REGION")
            self.draw_button(col, "GeometryNodeFlipFaces", text=" Flip Faces               ", icon="FLIP_NORMALS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeMeshBoolean", text=" Mesh Boolean           ", icon="MOD_BOOLEAN")
            self.draw_button(col, "GeometryNodeMeshToCurve", text=" Mesh to Curve          ", icon="OUTLINER_OB_CURVE")
            self.draw_button(col, "GeometryNodeMeshToPoints", text=" Mesh to Points          ", icon="MESH_TO_POINTS")
            self.draw_button(col, "GeometryNodeMeshToVolume", text=" Mesh to Volume         ", icon="MESH_TO_VOLUME")
            self.draw_button(col, "GeometryNodeScaleElements", text=" Scale Elements        ", icon="TRANSFORM_SCALE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeSplitEdges", text=" Split Edges               ", icon="SPLITEDGE")
            self.draw_button(col, "GeometryNodeSubdivideMesh", text=" Subdivide Mesh        ", icon="SUBDIVIDE_MESH")
            self.draw_button(col, "GeometryNodeSubdivisionSurface", text=" Subdivision Surface ", icon="SUBDIVIDE_EDGES")
            self.draw_button(col, "GeometryNodeTriangulate", text=" Triangulate              ", icon="MOD_TRIANGULATE")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeDualMesh", text="", icon="DUAL_MESH")
            self.draw_button(flow, "GeometryNodeEdgePathsToCurves", text="", icon="EDGE_PATHS_TO_CURVES")
            self.draw_button(flow, "GeometryNodeEdgePathsToSelection", text="", icon="EDGE_PATH_TO_SELECTION")
            self.draw_button(flow, "GeometryNodeExtrudeMesh", text="", icon="EXTRUDE_REGION")
            self.draw_button(flow, "GeometryNodeFlipFaces", text="", icon="FLIP_NORMALS")
            self.draw_button(flow, "GeometryNodeMeshBoolean", text="", icon="MOD_BOOLEAN")
            self.draw_button(flow, "GeometryNodeMeshToCurve", text="", icon="OUTLINER_OB_CURVE")
            self.draw_button(flow, "GeometryNodeMeshToPoints", text="", icon="MESH_TO_POINTS")
            self.draw_button(flow, "GeometryNodeMeshToVolume", text="", icon="MESH_TO_VOLUME")
            self.draw_button(flow, "GeometryNodeScaleElements", text="", icon="TRANSFORM_SCALE")
            self.draw_button(flow, "GeometryNodeSplitEdges", text="", icon="SPLITEDGE")
            self.draw_button(flow, "GeometryNodeSubdivideMesh", text="", icon="SUBDIVIDE_MESH")
            self.draw_button(flow, "GeometryNodeSubdivisionSurface", text="", icon="SUBDIVIDE_EDGES")
            self.draw_button(flow, "GeometryNodeTriangulate", text="", icon="MOD_TRIANGULATE")


#add mesh panel, primitives subpanel
class NODES_PT_geom_add_mesh_primitives(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Primitives"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeMeshCone", text=" Cone                       ", icon="MESH_CONE")
            self.draw_button(col, "GeometryNodeMeshCube", text=" Cube                       ", icon="MESH_CUBE")
            self.draw_button(col, "GeometryNodeMeshCylinder", text=" Cylinder                   ", icon="MESH_CYLINDER")
            self.draw_button(col, "GeometryNodeMeshGrid", text=" Grid                         ", icon="MESH_GRID")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeMeshIcoSphere", text=" Ico Sphere               ", icon="MESH_ICOSPHERE")
            self.draw_button(col, "GeometryNodeMeshCircle", text=" Mesh Circle            ", icon="MESH_CIRCLE")
            self.draw_button(col, "GeometryNodeMeshLine", text=" Mesh Line                 ", icon="MESH_LINE")
            self.draw_button(col, "GeometryNodeMeshUVSphere", text=" UV Sphere                ", icon="MESH_UVSPHERE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeMeshCone", text="", icon="MESH_CONE")
            self.draw_button(flow, "GeometryNodeMeshCube", text="", icon="MESH_CUBE")
            self.draw_button(flow, "GeometryNodeMeshCylinder", text="", icon="MESH_CYLINDER")
            self.draw_button(flow, "GeometryNodeMeshGrid", text="", icon="MESH_GRID")
            self.draw_button(flow, "GeometryNodeMeshIcoSphere", text="", icon="MESH_ICOSPHERE")
            self.draw_button(flow, "GeometryNodeMeshCircle", text="", icon="MESH_CIRCLE")
            self.draw_button(flow, "GeometryNodeMeshLine", text="", icon="MESH_LINE")
            self.draw_button(flow, "GeometryNodeMeshUVSphere", text="", icon="MESH_UVSPHERE")


#add mesh panel, topology subpanel
class NODES_PT_geom_add_mesh_topology(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Topology"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeCornersOfEdge", text=" Corners of Edge          ", icon="CORNERS_OF_EDGE")
            self.draw_button(col, "GeometryNodeCornersOfFace", text=" Corners of Face          ", icon="CORNERS_OF_FACE")
            self.draw_button(col, "GeometryNodeCornersOfVertex", text=" Corners of Vertex       ", icon="CORNERS_OF_VERTEX")
            self.draw_button(col, "GeometryNodeEdgesOfCorner", text=" Edges of Corner          ", icon="EDGES_OF_CORNER")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeEdgesOfVertex", text=" Edges of Vertex          ", icon="EDGES_OF_VERTEX")
            self.draw_button(col, "GeometryNodeFaceOfCorner", text=" Face of Corner             ", icon="FACE_OF_CORNER")
            self.draw_button(col, "GeometryNodeOffsetCornerInFace", text=" Offset Corner In Face  ", icon="OFFSET_CORNER_IN_FACE")
            self.draw_button(col, "GeometryNodeVertexOfCorner", text=" Vertex of Corner          ", icon="VERTEX_OF_CORNER")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeCornersOfEdge", text="", icon="CORNERS_OF_EDGE")
            self.draw_button(flow, "GeometryNodeCornersOfFace", text="", icon="CORNERS_OF_FACE")
            self.draw_button(flow, "GeometryNodeCornersOfVertex", text="", icon="CORNERS_OF_VERTEX")
            self.draw_button(flow, "GeometryNodeEdgesOfCorner", text="", icon="EDGES_OF_CORNER")
            self.draw_button(flow, "GeometryNodeEdgesOfVertex", text="", icon="EDGES_OF_VERTEX")
            self.draw_button(flow, "GeometryNodeFaceOfCorner", text="", icon="FACE_OF_CORNER")
            self.draw_button(flow, "GeometryNodeOffsetCornerInFace", text="", icon="OFFSET_CORNER_IN_FACE")
            self.draw_button(flow, "GeometryNodeVertexOfCorner", text="", icon="VERTEX_OF_CORNER")


#add volume panel
class NODES_PT_geom_add_mesh_uv(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "UV"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeUVPackIslands", text=" Pack UV Islands  ", icon="PACKISLAND")
            self.draw_button(col, "GeometryNodeUVUnwrap", text=" UV Unwrap      ", icon="UNWRAP_ABF")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeUVPackIslands", text="", icon="VOLUME_CUBE")
            self.draw_button(flow, "GeometryNodeUVUnwrap", text="", icon="VOLUME_TO_MESH")


#add mesh panel
class NODES_PT_geom_add_point(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Point"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeDistributePointsInVolume", text=" Distribute Points in Volume  ", icon="VOLUME_DISTRIBUTE")
            self.draw_button(col, "GeometryNodeDistributePointsOnFaces", text=" Distribute Points on Faces  ", icon="POINT_DISTRIBUTE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodePoints", text=" Points                          ", icon="DECORATE")
            self.draw_button(col, "GeometryNodePointsToCurves", text=" Points to Curves          ", icon="POINTS_TO_CURVES")
            self.draw_button(col, "GeometryNodePointsToVertices", text=" Points to Vertices         ", icon="POINTS_TO_VERTICES")
            self.draw_button(col, "GeometryNodePointsToVolume", text=" Points to Volume         ", icon="POINT_TO_VOLUME")
            self.draw_button(col, "GeometryNodeSetPointRadius", text=" Set Point Radius          ", icon="SET_CURVE_RADIUS")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeDistributePointsInVolume", text="", icon="VOLUME_DISTRIBUTE")
            self.draw_button(flow, "GeometryNodeDistributePointsOnFaces", text="", icon="POINT_DISTRIBUTE")
            self.draw_button(flow, "GeometryNodePoints", text="", icon="DECORATE")
            self.draw_button(flow, "GeometryNodePointsToCurves", text="", icon="POINTS_TO_CURVES")
            self.draw_button(flow, "GeometryNodePointsToVertices", text="", icon="POINTS_TO_VERTICES")
            self.draw_button(flow, "GeometryNodePointsToVolume", text="", icon="POINT_TO_VOLUME")
            self.draw_button(flow, "GeometryNodeSetPointRadius", text="", icon="SET_CURVE_RADIUS")


#add volume panel
class NODES_PT_geom_add_volume(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Volume"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeVolumeCube", text=" Volume Cube       ", icon="VOLUME_CUBE")
            self.draw_button(col, "GeometryNodeVolumeToMesh", text=" Volume to Mesh       ", icon="VOLUME_TO_MESH")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeVolumeCube", text="", icon="VOLUME_CUBE")
            self.draw_button(flow, "GeometryNodeVolumeToMesh", text="", icon="VOLUME_TO_MESH")

#add simulation panel
class NODES_PT_geom_add_simulation(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Simulation"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, operator="node.add_simulation_zone", text=" Simulation Zone       ", icon="TIME")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, operator="node.add_simulation_zone", text="", icon="TIME")


#add material panel
class NODES_PT_geom_add_material(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Material"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeReplaceMaterial", text=" Replace Material      ", icon="MATERIAL_REPLACE")
            self.draw_button(col, "GeometryNodeInputMaterialIndex", text=" Material Index           ", icon="MATERIAL_INDEX")
            self.draw_button(col, "GeometryNodeMaterialSelection", text=" Material Selection    ", icon="SELECT_BY_MATERIAL")
            self.draw_button(col, "GeometryNodeSetMaterial", text=" Set Material              ", icon="MATERIAL_ADD")
            self.draw_button(col, "GeometryNodeSetMaterialIndex", text=" Set Material Index   ", icon="SET_MATERIAL_INDEX")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeReplaceMaterial", text="", icon="MATERIAL_REPLACE")
            self.draw_button(flow, "GeometryNodeInputMaterialIndex", text="", icon="MATERIAL_INDEX")
            self.draw_button(flow, "GeometryNodeMaterialSelection", text="", icon="SELECT_BY_MATERIAL")
            self.draw_button(flow, "GeometryNodeSetMaterial", text="", icon="MATERIAL_ADD")
            self.draw_button(flow, "GeometryNodeSetMaterialIndex", text="", icon="SET_MATERIAL_INDEX")


#add vector panel
class NODES_PT_geom_add_texture(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexBrick", text=" Brick Texture        ", icon="NODE_BRICK")
            self.draw_button(col, "ShaderNodeTexChecker", text=" Checker Texture   ", icon="NODE_CHECKER")
            self.draw_button(col, "ShaderNodeTexGradient", text=" Gradient Texture  ", icon="NODE_GRADIENT")
            self.draw_button(col, "GeometryNodeImageTexture", text=" Image Texture      ", icon="FILE_IMAGE")
            self.draw_button(col, "ShaderNodeTexMagic", text=" Magic Texture       ", icon="MAGIC_TEX")
            self.draw_button(col, "ShaderNodeTexNoise", text=" Noise Texture        ", icon="NOISE_TEX")
            self.draw_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture     ", icon="VORONI_TEX")
            self.draw_button(col, "ShaderNodeTexWave", text=" Wave Texture         ", icon="NODE_WAVES")
            self.draw_button(col, "ShaderNodeTexWhiteNoise", text=" White Noise            ", icon="NODE_WHITE_NOISE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeTexBrick", text="", icon="NODE_BRICK")
            self.draw_button(flow, "ShaderNodeTexChecker", text="", icon="NODE_CHECKER")
            self.draw_button(flow, "ShaderNodeTexGradient", text="", icon="NODE_GRADIENT")
            self.draw_button(flow, "GeometryNodeImageTexture", text="", icon="FILE_IMAGE")
            self.draw_button(flow, "ShaderNodeTexMagic", text="", icon="MAGIC_TEX")
            self.draw_button(flow, "ShaderNodeTexNoise", text="", icon="NOISE_TEX")
            self.draw_button(flow, "ShaderNodeTexVoronoi", text="", icon="VORONI_TEX")
            self.draw_button(flow, "ShaderNodeTexWave", text="", icon="NODE_WAVES")
            self.draw_button(flow, "ShaderNodeTexWhiteNoise", text="", icon="NODE_WHITE_NOISE")


#add utilities panel
class NODES_PT_geom_add_utilities(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Utilities"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, operator="node.add_foreach_geometry_element_zone", text=" For Each Element    ", icon="FOR_EACH")
            self.draw_button(col, "GeometryNodeIndexSwitch", text=" Index Switch    ", icon="INDEX_SWITCH")
            self.draw_button(col, "GeometryNodeMenuSwitch", text=" Menu Switch    ", icon="MENU_SWITCH")
            self.draw_button(col, "FunctionNodeRandomValue", text=" Random Value  ", icon="RANDOM_FLOAT")
            self.draw_button(col, operator="node.add_repeat_zone", text=" Repeat Zone      ", icon="REPEAT")
            self.draw_button(col, "GeometryNodeSwitch", text=" Switch               ", icon="SWITCH")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeIndexSwitch", text="", icon="INDEX_SWITCH")
            self.draw_button(flow, "GeometryNodeMenuSwitch", text="", icon="MENU_SWITCH")
            self.draw_button(flow, "FunctionNodeRandomValue", text="", icon="RANDOM_FLOAT")
            self.draw_button(flow, operator="node.add_repeat_zone", text="", icon="REPEAT")
            self.draw_button(flow, "GeometryNodeSwitch", text="", icon="SWITCH")


#add utilities panel, color subpanel
class NODES_PT_geom_add_utilities_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeValToRGB", text=" ColorRamp           ", icon="NODE_COLORRAMP")
            self.draw_button(col, "ShaderNodeRGBCurve", text=" RGB Curves          ", icon="NODE_RGBCURVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeCombineColor", text=" Combine Color      ", icon="COMBINE_COLOR")
            self.draw_button(col, "FunctionNodeSeparateColor", text=" Separate Color      ", icon="SEPARATE_COLOR")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeValToRGB", text="", icon="NODE_COLORRAMP")
            self.draw_button(flow, "ShaderNodeRGBCurve", text="", icon="NODE_RGBCURVE")
            self.draw_button(flow, "FunctionNodeCombineColor", text="", icon="COMBINE_COLOR")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIX", settings={"data_type": "'RGBA'"})
            self.draw_button(flow, "FunctionNodeSeparateColor", text="", icon="SEPARATE_COLOR")


#add utilities panel, text subpanel
class NODES_PT_geom_add_utilities_text(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Text"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeFormatString", text=" Format String            ", icon="FORMAT_STRING")
            self.draw_button(col, "GeometryNodeStringJoin", text=" Join Strings             ", icon="STRING_JOIN")
            self.draw_button(col, "FunctionNodeMatchString", text=" Match String            ", icon="MATCH_STRING")
            self.draw_button(col, "FunctionNodeReplaceString", text=" Replace Strings       ", icon="REPLACE_STRING")
            self.draw_button(col, "FunctionNodeSliceString", text=" Slice Strings            ", icon="STRING_SUBSTRING")
            self.draw_button(col, "FunctionNodeStringLength", text=" String Length           ", icon="STRING_LENGTH")
            self.draw_button(col, "FunctionNodeFindInString", text=" Find in String           ", icon="STRING_FIND")
            self.draw_button(col, "GeometryNodeStringToCurves", text=" String to Curves       ", icon="STRING_TO_CURVE")
            self.draw_button(col, "FunctionNodeValueToString", text=" Value to String         ", icon="VALUE_TO_STRING")
            self.draw_button(col, "FunctionNodeInputSpecialCharacters", text=" Special Characters  ", icon="SPECIAL")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "FunctionNodeFormatString", text="", icon="FORMAT_STRING")
            self.draw_button(flow, "GeometryNodeStringJoin", text="", icon="STRING_JOIN")
            self.draw_button(flow, "FunctionNodeMatchString", text="", icon="MATCH_STRING")
            self.draw_button(flow, "FunctionNodeReplaceString", text="", icon="REPLACE_STRING")
            self.draw_button(flow, "FunctionNodeSliceString", text="", icon="STRING_SUBSTRING")
            self.draw_button(flow, "FunctionNodeStringLength", text="", icon="STRING_LENGTH")
            self.draw_button(flow, "FunctionNodeFindInString", text="", icon="STRING_FIND")
            self.draw_button(flow, "GeometryNodeStringToCurves", text="", icon="STRING_TO_CURVE")
            self.draw_button(flow, "FunctionNodeValueToString", text="", icon="VALUE_TO_STRING")
            self.draw_button(flow, "FunctionNodeInputSpecialCharacters", text="", icon="SPECIAL")


#add utilities panel, vector subpanel
class NODES_PT_geom_add_utilities_vector(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeVectorCurve", text=" Vector Curves  ", icon="NODE_VECTOR")
            self.draw_button(col, "ShaderNodeVectorMath", text=" Vector Math      ", icon="NODE_VECTORMATH")
            self.draw_button(col, "ShaderNodeVectorRotate", text=" Vector Rotate    ", icon="NODE_VECTORROTATE")
            self.draw_button(col, "ShaderNodeCombineXYZ", text=" Combine XYZ   ", icon="NODE_COMBINEXYZ")
            self.draw_button(col, "ShaderNodeMix", text=" Mix Vector       ", icon="NODE_MIX", settings={"data_type": "'VECTOR'"})
            self.draw_button(col, "ShaderNodeSeparateXYZ", text=" Separate XYZ   ", icon="NODE_SEPARATEXYZ")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeVectorCurve", text="", icon="NODE_VECTOR")
            self.draw_button(flow, "ShaderNodeVectorMath", text="", icon="NODE_VECTORMATH")
            self.draw_button(flow, "ShaderNodeVectorRotate", text="", icon="NODE_VECTORROTATE")
            self.draw_button(flow, "ShaderNodeCombineXYZ", text="", icon="NODE_COMBINEXYZ")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIX", settings={"data_type": "'VECTOR'"})
            self.draw_button(flow, "ShaderNodeSeparateXYZ", text="", icon="NODE_SEPARATEXYZ")


#add utilities panel, field subpanel
class NODES_PT_geom_add_utilities_field(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Field"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "GeometryNodeAccumulateField", text=" Accumulate Field  ", icon="ACCUMULATE")
            self.draw_button(col, "GeometryNodeFieldAtIndex", text=" Evaluate at Index ", icon="FIELD_AT_INDEX")
            self.draw_button(col, "GeometryNodeFieldOnDomain", text=" Evaluate On Domain ", icon="FIELD_DOMAIN")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "GeometryNodeAccumulateField", text="", icon="ACCUMULATE")
            self.draw_button(flow, "GeometryNodeFieldAtIndex", text="", icon="FIELD_AT_INDEX")
            self.draw_button(flow, "GeometryNodeFieldOnDomain", text="", icon="FIELD_DOMAIN")


#add utilities panel, math subpanel
class NODES_PT_geom_add_utilities_math(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Math"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeBooleanMath", text=" Boolean Math  ", icon="BOOLEAN_MATH")
            self.draw_button(col, "FunctionNodeIntegerMath", text=" Integer Math  ", icon="INTEGER_MATH")
            self.draw_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_button(col, "FunctionNodeCompare", text=" Compare          ", icon="FLOAT_COMPARE")
            self.draw_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeFloatToInt", text=" Float to Integer ", icon="FLOAT_TO_INT")
            self.draw_button(col, "FunctionNodeHashValue", text=" Hash Value      ", icon="HASH")
            self.draw_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_button(col, "ShaderNodeMix", text=" Mix                   ", icon="NODE_MIXSHADER")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "FunctionNodeBooleanMath", text="", icon="BOOLEAN_MATH")
            self.draw_button(flow, "FunctionNodeIntegerMath", text="", icon="INTEGER_MATH")
            self.draw_button(flow, "ShaderNodeClamp", text="", icon="NODE_CLAMP")
            self.draw_button(flow, "FunctionNodeCompare", text="", icon="FLOAT_COMPARE")
            self.draw_button(flow, "ShaderNodeFloatCurve", text="", icon="FLOAT_CURVE")
            self.draw_button(flow, "FunctionNodeFloatToInt", text="", icon="FLOAT_TO_INT")
            self.draw_button(flow, "FunctionNodeHashValue", text="", icon="HASH")
            self.draw_button(flow, "ShaderNodeMapRange", text="", icon="NODE_MAP_RANGE")
            self.draw_button(flow, "ShaderNodeMath", text="", icon="NODE_MATH")
            self.draw_button(flow, "ShaderNodeMix", text="", icon="NODE_MIXSHADER")


#add utilities panel, matrix subpanel
class NODES_PT_geom_add_utilities_matrix(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Matrix"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeCombineMatrix", text=" Combine Matrix     ", icon="COMBINE_MATRIX")
            self.draw_button(col, "FunctionNodeCombineTransform", text=" Combine Transform     ", icon="COMBINE_TRANSFORM")
            self.draw_button(col, "FunctionNodeMatrixDeterminant", text=" Matrix Determinant     ", icon="MATRIX_DETERMINANT")
            self.draw_button(col, "FunctionNodeInvertMatrix", text=" Invert Matrix", icon="INVERT_MATRIX")
            self.draw_button(col, "FunctionNodeMatrixMultiply", text=" Multiply Matrix ", icon="MULTIPLY_MATRIX")
            self.draw_button(col, "FunctionNodeProjectPoint", text=" Project Point   ", icon="PROJECT_POINT")
            self.draw_button(col, "FunctionNodeSeparateMatrix", text=" Separate Matrix   ", icon="SEPARATE_MATRIX")
            self.draw_button(col, "FunctionNodeSeparateTransform", text=" Separate Transform   ", icon="SEPARATE_TRANSFORM")
            self.draw_button(col, "FunctionNodeTransformDirection", text=" Transform Direction  ", icon="TRANSFORM_DIRECTION")
            self.draw_button(col, "FunctionNodeTransformPoint", text=" Transform Point  ", icon="TRANSFORM_POINT")
            self.draw_button(col, "FunctionNodeTransposeMatrix", text=" Transpose Matrix ", icon="TRANSPOSE_MATRIX")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "FunctionNodeCombineMatrix", text="", icon="COMBINE_MATRIX")
            self.draw_button(flow, "FunctionNodeCombineTransform", text="", icon="COMBINE_TRANSFORM")
            self.draw_button(flow, "FunctionNodeMatrixDeterminant", text="", icon="MATRIX_DETERMINANT")
            self.draw_button(flow, "FunctionNodeInvertMatrix", text="", icon="INVERT_MATRIX")
            self.draw_button(flow, "FunctionNodeMatrixMultiply", text="", icon="MULTIPLY_MATRIX")
            self.draw_button(flow, "FunctionNodeProjectPoint", text="", icon="PROJECT_POINT")
            self.draw_button(flow, "FunctionNodeSeparateMatrix", text="", icon="SEPARATE_MATRIX")
            self.draw_button(flow, "FunctionNodeSeparateTransform", text="", icon="SEPARATE_TRANSFORM")
            self.draw_button(flow, "FunctionNodeTransformDirection", text="", icon="TRANSFORM_DIRECTION")
            self.draw_button(flow, "FunctionNodeTransformPoint", text="", icon="TRANSFORM_POINT")
            self.draw_button(flow, "FunctionNodeTransposeMatrix", text="", icon="TRANSPOSE_MATRIX")


#add utilities panel, rotation subpanel
class NODES_PT_geom_add_utilities_rotation(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Rotation"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeAlignRotationToVector", text=" Align Rotation to Vector", icon="ALIGN_ROTATION_TO_VECTOR")
            self.draw_button(col, "FunctionNodeAxesToRotation", text=" Axes to Rotation ", icon="AXES_TO_ROTATION")
            self.draw_button(col, "FunctionNodeAxisAngleToRotation", text=" Axis Angle to Rotation", icon="AXIS_ANGLE_TO_ROTATION")
            self.draw_button(col, "FunctionNodeEulerToRotation", text=" Euler to Rotation ", icon="EULER_TO_ROTATION")
            self.draw_button(col, "FunctionNodeInvertRotation", text=" Invert Rotation    ", icon="INVERT_ROTATION")
            self.draw_button(col, "FunctionNodeRotateRotation", text=" Rotate Rotation         ", icon="ROTATE_EULER")
            self.draw_button(col, "FunctionNodeRotateVector", text=" Rotate Vector      ", icon="NODE_VECTORROTATE")
            self.draw_button(col, "FunctionNodeRotationToAxisAngle", text=" Rotation to Axis Angle", icon="ROTATION_TO_AXIS_ANGLE")
            self.draw_button(col, "FunctionNodeRotationToEuler", text=" Rotation to Euler  ", icon="ROTATION_TO_EULER")
            self.draw_button(col, "FunctionNodeRotationToQuaternion", text=" Rotation to Quaternion ", icon="ROTATION_TO_QUATERNION")
            self.draw_button(col, "FunctionNodeQuaternionToRotation", text=" Quaternion to Rotation ", icon="QUATERNION_TO_ROTATION")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "FunctionNodeAlignRotationToVector", text="", icon="ALIGN_ROTATION_TO_VECTOR")
            self.draw_button(flow, "FunctionNodeAxesToRotation", text="", icon="AXES_TO_ROTATION")
            self.draw_button(flow, "FunctionNodeAxisAngleToRotation", text="", icon="AXIS_ANGLE_TO_ROTATION")
            self.draw_button(flow, "FunctionNodeEulerToRotation", text="", icon="EULER_TO_ROTATION")
            self.draw_button(flow, "FunctionNodeInvertRotation", text="", icon="INVERT_ROTATION")
            self.draw_button(flow, "FunctionNodeRotateRotation", text="", icon="ROTATE_EULER")
            self.draw_button(flow, "FunctionNodeRotateVector", text="", icon="NODE_VECTORROTATE")
            self.draw_button(flow, "FunctionNodeRotationToAxisAngle", text="", icon="ROTATION_TO_AXIS_ANGLE")
            self.draw_button(flow, "FunctionNodeRotationToEuler", text="", icon="ROTATION_TO_EULER")
            self.draw_button(flow, "FunctionNodeRotationToQuaternion", text="", icon="ROTATION_TO_QUATERNION")
            self.draw_button(flow, "FunctionNodeQuaternionToRotation", text="", icon="QUATERNION_TO_ROTATION")


#add utilities panel, deprecated subpanel
class NODES_PT_geom_add_utilities_deprecated(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Deprecated"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_geom_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') # Just in geometry node editor

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
            col.scale_y = 1.5
            self.draw_button(col, "FunctionNodeAlignEulerToVector", text=" Align Euler to Vector", icon="ALIGN_EULER_TO_VECTOR")
            self.draw_button(col, "FunctionNodeRotateEuler", text=" Rotate Euler (Depreacated)        ", icon="ROTATE_EULER")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "FunctionNodeAlignEulerToVector", text="", icon="ALIGN_EULER_TO_VECTOR")
            self.draw_button(flow, "FunctionNodeRotateEuler", text="", icon="ROTATE_EULER")


# ---------------- shader editor common. This content shows when you activate the common switch in the display panel.

# Shader editor, Input panel
class NODES_PT_shader_add_input_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == True and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader mode

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeFresnel", text=" Fresnel              ", icon="NODE_FRESNEL")
            self.draw_button(col, "ShaderNodeNewGeometry", text=" Geometry        ", icon="NODE_GEOMETRY")
            self.draw_button(col, "ShaderNodeRGB", text=" RGB                 ", icon="NODE_RGB")
            self.draw_button(col, "ShaderNodeTexCoord", text="Texture Coordinate   ", icon="NODE_TEXCOORDINATE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeFresnel", text="", icon="NODE_FRESNEL")
            self.draw_button(flow, "ShaderNodeNewGeometry", text="", icon="NODE_GEOMETRY")
            self.draw_button(flow, "ShaderNodeRGB", text="", icon="NODE_RGB")
            self.draw_button(flow, "ShaderNodeTexCoord", text="", icon="NODE_TEXCOORDINATE")


#Shader editor , Output panel
class NODES_PT_shader_add_output_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        return addon_prefs.Node_shader_add_common == True and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader mode

    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        engine = context.engine

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5

            if context.space_data.shader_type == 'OBJECT':
                self.draw_button(col, "ShaderNodeOutputMaterial", text=" Material Output", icon="NODE_MATERIAL")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_button(col, "ShaderNodeOutputWorld", text=" World Output    ", icon="WORLD")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_button(col, "ShaderNodeOutputLineStyle", text=" Line Style Output", icon="NODE_LINESTYLE_OUTPUT")

        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.shader_type == 'OBJECT':
                self.draw_button(flow, "ShaderNodeOutputMaterial", text="", icon="NODE_MATERIAL")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_button(flow, "ShaderNodeOutputWorld", text="", icon="WORLD")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_button(flow, "ShaderNodeOutputLineStyle", text="", icon="NODE_LINESTYLE_OUTPUT")


#Shader Editor - Shader panel
class NODES_PT_shader_add_shader_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == True and (context.space_data.tree_type == 'ShaderNodeTree' and context.space_data.shader_type in ( 'OBJECT', 'WORLD')) # Just in shader mode, Just in Object and World

    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
        engine = context.engine

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeAddShader", text=" Add                   ", icon="NODE_ADD_SHADER")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeBsdfHairPrincipled", text=" Hair BSDF          ", icon="CURVES")
                self.draw_button(col, "ShaderNodeMixShader", text=" Mix Shader        ", icon="NODE_MIXSHADER")
                self.draw_button(col, "ShaderNodeBsdfPrincipled", text=" Principled BSDF", icon="NODE_PRINCIPLED")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume", icon="NODE_VOLUMEPRINCIPLED")

                if engine == 'CYCLES':
                    self.draw_button(col, "ShaderNodeBsdfToon", text=" Toon BSDF           ", icon="NODE_TOONSHADER")

                col = layout.column(align=True)
                col.scale_y = 1.5

                self.draw_button(col, "ShaderNodeVolumeAbsorption", text=" Volume Absorption ", icon="NODE_VOLUMEABSORPTION")
                self.draw_button(col, "ShaderNodeVolumeScatter", text=" Volume Scatter   ", icon="NODE_VOLUMESCATTER")

            if context.space_data.shader_type == 'WORLD':
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_button(col, "ShaderNodeBackground", text=" Background    ", icon="NODE_BACKGROUNDSHADER")
                self.draw_button(col, "ShaderNodeEmission", text=" Emission           ", icon="NODE_EMISSION")
                self.draw_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume       ", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_button(col, "ShaderNodeMixShader", text=" Mix                   ", icon="NODE_MIXSHADER")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_button(flow, "ShaderNodeAddShader", text="", icon="NODE_ADD_SHADER")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeBsdfHairPrincipled", text="", icon="CURVES")
                self.draw_button(flow, "ShaderNodeMixShader", text="", icon="NODE_MIXSHADER")
                self.draw_button(flow, "ShaderNodeBsdfPrincipled", text="", icon="NODE_PRINCIPLED")
                self.draw_button(flow, "ShaderNodeVolumePrincipled", text="", icon="NODE_VOLUMEPRINCIPLED")

                if engine == 'CYCLES':
                    self.draw_button(flow, "ShaderNodeBsdfToon", text="", icon="NODE_TOONSHADER")
                self.draw_button(flow, "ShaderNodeVolumeAbsorption", text="", icon="NODE_VOLUMEABSORPTION")
                self.draw_button(flow, "ShaderNodeVolumeScatter", text="", icon="NODE_VOLUMESCATTER")

            if context.space_data.shader_type == 'WORLD':
                self.draw_button(flow, "ShaderNodeBackground", text="", icon="NODE_BACKGROUNDSHADER")
                self.draw_button(flow, "ShaderNodeEmission", text="", icon="NODE_EMISSION")
                self.draw_button(flow, "ShaderNodeVolumePrincipled", text="", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_button(flow, "ShaderNodeMixShader", text="", icon="NODE_MIXSHADER")


#Shader Editor - Texture panel
class NODES_PT_shader_add_texture_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == True and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader and texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
        engine = context.engine

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexEnvironment", text=" Environment Texture", icon="NODE_ENVIRONMENT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexImage", text=" Image Texture         ", icon="FILE_IMAGE")
            self.draw_button(col, "ShaderNodeTexNoise", text=" Noise Texture         ", icon="NOISE_TEX")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeTexSky", text=" Sky Texture             ", icon="NODE_SKY")
            self.draw_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture       ", icon="VORONI_TEX")


        #### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeTexEnvironment", text="", icon="NODE_ENVIRONMENT")
            self.draw_button(flow, "ShaderNodeTexImage", text="", icon="FILE_IMAGE")
            self.draw_button(flow, "ShaderNodeTexNoise", text="", icon="NOISE_TEX")
            self.draw_button(flow, "ShaderNodeTexSky", text="", icon="NODE_SKY")
            self.draw_button(flow, "ShaderNodeTexVoronoi", text="", icon="VORONI_TEX")


#Shader Editor - Color panel
class NODES_PT_shader_add_color_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == True and context.space_data.tree_type == 'ShaderNodeTree'

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeBrightContrast", text=" Bright / Contrast ", icon="BRIGHTNESS_CONTRAST")
            self.draw_button(col, "ShaderNodeGamma", text=" Gamma             ", icon="NODE_GAMMA")
            self.draw_button(col, "ShaderNodeHueSaturation", text=" Hue / Saturation ", icon="NODE_HUESATURATION")
            self.draw_button(col, "ShaderNodeInvert", text=" Invert                 ", icon="NODE_INVERT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeMixRGB", text=" Mix RGB           ", icon="NODE_MIXRGB")
            self.draw_button(col, "ShaderNodeRGBCurve", text="  RGB Curves        ", icon="NODE_RGBCURVE")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeBrightContrast", text="", icon="BRIGHTNESS_CONTRAST")
            self.draw_button(flow, "ShaderNodeGamma", text="", icon="NODE_GAMMA")
            self.draw_button(flow, "ShaderNodeHueSaturation", text="", icon="NODE_HUESATURATION")
            self.draw_button(flow, "ShaderNodeInvert", text="", icon="NODE_INVERT")
            self.draw_button(flow, "ShaderNodeMixRGB", text="", icon="NODE_MIXRGB")
            self.draw_button(flow, "ShaderNodeRGBCurve", text="", icon="NODE_RGBCURVE")


#Shader Editor - Vector panel
class NODES_PT_shader_add_vector_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == True and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader and compositing mode

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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeMapping", text=" Mapping           ", icon="NODE_MAPPING")
            self.draw_button(col, "ShaderNodeNormal", text=" Normal            ", icon="RECALC_NORMALS")
            self.draw_button(col, "ShaderNodeNormalMap", text=" Normal Map     ", icon="NODE_NORMALMAP")

        ##### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeMapping", text="", icon="NODE_MAPPING")
            self.draw_button(flow, "ShaderNodeNormal", text="", icon="RECALC_NORMALS")
            self.draw_button(flow, "ShaderNodeNormalMap", text="", icon="NODE_NORMALMAP")


#Shader Editor - Converter panel
class NODES_PT_shader_add_converter_common(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        return addon_prefs.Node_shader_add_common == True and context.space_data.tree_type == 'ShaderNodeTree' # Just in shader and compositing mode

    @staticmethod
    def draw(self, context):
        layout = self.layout
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        engine = context.engine

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_button(col, "ShaderNodeValToRGB", text=" ColorRamp       ", icon="NODE_COLORRAMP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")
            self.draw_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_button(col, "ShaderNodeRGBToBW", text=" RGB to BW      ", icon="NODE_RGBTOBW")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeClamp", text="", icon="NODE_CLAMP")
            self.draw_button(flow, "ShaderNodeValToRGB", text="", icon="NODE_COLORRAMP")
            self.draw_button(flow, "ShaderNodeFloatCurve", text="", icon="FLOAT_CURVE")
            self.draw_button(flow, "ShaderNodeMapRange", text="", icon="NODE_MAP_RANGE")
            self.draw_button(flow, "ShaderNodeMath", text="", icon="NODE_MATH")
            self.draw_button(flow, "ShaderNodeRGBToBW", text="", icon="NODE_RGBTOBW")


#Shader Editor - Script panel
class NODES_PT_shader_add_script(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Script"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
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
            col.scale_y = 1.5
            self.draw_button(col, "ShaderNodeScript", text=" Script               ", icon="FILE_SCRIPT")

        ##### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_button(flow, "ShaderNodeScript", text="", icon="FILE_SCRIPT")


classes = (
    NODES_PT_shader_comp_textoricon_shader_add,
    NODES_PT_shader_comp_textoricon_compositor_add,
    NODES_PT_shader_comp_textoricon_relations,
    NODES_PT_geom_textoricon_add,
    NODES_PT_geom_textoricon_relations,
    NODES_PT_shader_add_input,
    NODES_PT_shader_add_output,

    #-----------------------

    #Compositor nodes add tab
    NODES_PT_comp_add_input,
    NODES_PT_comp_add_input_constant,
    NODES_PT_comp_add_input_scene,
    NODES_PT_comp_add_output,
    NODES_PT_comp_add_color,
    NODES_PT_comp_add_color_adjust,
    NODES_PT_comp_add_color_mix,
    NODES_PT_comp_add_filter,
    NODES_PT_comp_add_filter_blur,
    NODES_PT_comp_add_keying,
    NODES_PT_comp_add_mask,
    NODES_PT_comp_add_texture,
    NODES_PT_comp_add_tracking,
    NODES_PT_comp_add_transform,
    NODES_PT_comp_add_utility,
    NODES_PT_comp_add_vector,

    #-----------------------

    NODES_PT_Input_input_tex,
    NODES_PT_Input_textures_tex,
    NODES_PT_shader_add_shader,
    NODES_PT_shader_add_texture,
    NODES_PT_shader_add_color,
    NODES_PT_Input_input_advanced_tex,
    NODES_PT_Input_pattern,
    NODES_PT_Input_color_tex,
    NODES_PT_Input_output_tex,
    NODES_PT_Modify_converter_tex,
    NODES_PT_shader_add_vector,
    NODES_PT_shader_add_converter,
    NODES_PT_Modify_distort_tex,


    #-----------------------

    #geometry nodes relations tab
    NODES_PT_Relations_group,
    NODES_PT_Input_node_group,
    NODES_PT_Relations_layout,

    #geometry nodes add tab
    NODES_PT_geom_add_attribute,

    NODES_PT_geom_add_input,
    NODES_PT_geom_add_input_constant,
    NODES_PT_geom_add_input_gizmo,
    NODES_PT_geom_add_input_file,
    NODES_PT_geom_add_input_scene,

    NODES_PT_geom_add_output,

    NODES_PT_geom_add_geometry,
    NODES_PT_geom_add_geometry_read,
    NODES_PT_geom_add_geometry_sample,
    NODES_PT_geom_add_geometry_write,
    NODES_PT_geom_add_geometry_operations,

    NODES_PT_geom_add_curve,
    NODES_PT_geom_add_curve_read,
    NODES_PT_geom_add_curve_sample,
    NODES_PT_geom_add_curve_write,
    NODES_PT_geom_add_curve_operations,
    NODES_PT_geom_add_curve_primitives,
    NODES_PT_geom_add_curve_topology,

    NODES_PT_geom_add_grease_pencil,
    NODES_PT_geom_add_grease_pencil_read,
    NODES_PT_geom_add_grease_pencil_write,
    NODES_PT_geom_add_grease_pencil_operations,

    NODES_PT_geom_add_instances,

    NODES_PT_geom_add_mesh,
    NODES_PT_geom_add_mesh_read,
    NODES_PT_geom_add_mesh_sample,
    NODES_PT_geom_add_mesh_write,
    NODES_PT_geom_add_mesh_operations,
    NODES_PT_geom_add_mesh_primitives,
    NODES_PT_geom_add_mesh_topology,
    NODES_PT_geom_add_mesh_uv,

    NODES_PT_geom_add_point,
    NODES_PT_geom_add_volume,
    NODES_PT_geom_add_simulation,
    NODES_PT_geom_add_material,
    NODES_PT_geom_add_texture,

    NODES_PT_geom_add_utilities,
    NODES_PT_geom_add_utilities_color,
    NODES_PT_geom_add_utilities_text,
    NODES_PT_geom_add_utilities_vector,
    NODES_PT_geom_add_utilities_field,
    NODES_PT_geom_add_utilities_math,
    NODES_PT_geom_add_utilities_matrix,
    NODES_PT_geom_add_utilities_rotation,
    NODES_PT_geom_add_utilities_deprecated,

    #----------------------------------

    #- shader editor common classes
    NODES_PT_shader_add_input_common,
    NODES_PT_shader_add_output_common,
    NODES_PT_shader_add_shader_common,
    NODES_PT_shader_add_texture_common,
    NODES_PT_shader_add_color_common,
    NODES_PT_shader_add_vector_common,
    NODES_PT_shader_add_converter_common,

    NODES_PT_shader_add_script,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

