# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy import context

#Add tab, Node Group panel
from nodeitems_builtins import node_tree_group_type


class NodePanel:
    @staticmethod
    def draw_text_button(layout, node=None, operator="node.add_node", text="", icon=None, settings=None, pad=0):
        if text != "" and pad > 0:
            text = " " + text.strip().ljust(pad)

        # Determine icon automatically from node bl_rna when adding non-zone nodes and no icon is specified
        if icon is None and operator == "node.add_node":
            bl_rna = bpy.types.Node.bl_rna_get_subclass(node)
            icon = getattr(bl_rna, "icon", "NONE")
        
        props = layout.operator(operator, text=text, icon=icon)
        props.use_transform = True

        if node is not None:
            props.type = node

        if settings is not None:
            for name, value in settings.items():
                ops = props.settings.add()
                ops.name = name
                ops.value = value

    @staticmethod
    def draw_icon_button(layout, node=None, operator="node.add_node", icon=None, settings=None):
        # Determine icon automatically from node bl_rna when adding non-zone nodes and no icon is specified
        if icon is None and operator == "node.add_node":
            bl_rna = bpy.types.Node.bl_rna_get_subclass(node)
            icon = getattr(bl_rna, "icon", "NONE")
            
        props = layout.operator(operator, text="", icon=icon)
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
            self.draw_text_button(col, "ShaderNodeAmbientOcclusion", text="Ambient Occlusion")
            self.draw_text_button(col, "ShaderNodeAttribute", text="Attribute")
            self.draw_text_button(col, "ShaderNodeBevel", text="Bevel")
            self.draw_text_button(col, "ShaderNodeCameraData", text="Camera Data")
            self.draw_text_button(col, "ShaderNodeVertexColor", text="Color Attribute")
            self.draw_text_button(col, "ShaderNodeFresnel", text="Fresnel")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeNewGeometry", text="Geometry")
            self.draw_text_button(col, "ShaderNodeHairInfo", text="Curves Info")
            self.draw_text_button(col, "ShaderNodeLayerWeight", text="Layer Weight")
            self.draw_text_button(col, "ShaderNodeLightPath", text="Light Path")
            self.draw_text_button(col, "ShaderNodeObjectInfo", text="Object Info")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeParticleInfo", text="Particle Info")
            self.draw_text_button(col, "ShaderNodePointInfo", text="Point Info")
            self.draw_text_button(col, "ShaderNodeRGB", text="RGB")
            self.draw_text_button(col, "ShaderNodeTangent", text="Tangent")
            self.draw_text_button(col, "ShaderNodeTexCoord", text="Texture Coordinate")

            if context.space_data.shader_type == 'LINESTYLE':
                self.draw_text_button(col, "ShaderNodeUVALongStroke", text="UV along stroke")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeUVMap", text="UV Map")
            self.draw_text_button(col, "ShaderNodeValue", text="Value")
            self.draw_text_button(col, "ShaderNodeVolumeInfo", text="Volume Info")
            self.draw_text_button(col, "ShaderNodeWireframe", text="Wireframe")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeAmbientOcclusion")
            self.draw_icon_button(flow, "ShaderNodeAttribute")
            self.draw_icon_button(flow, "ShaderNodeBevel")
            self.draw_icon_button(flow, "ShaderNodeCameraData")
            self.draw_icon_button(flow, "ShaderNodeVertexColor")
            self.draw_icon_button(flow, "ShaderNodeFresnel")
            self.draw_icon_button(flow, "ShaderNodeNewGeometry")
            self.draw_icon_button(flow, "ShaderNodeHairInfo")
            self.draw_icon_button(flow, "ShaderNodeLayerWeight")
            self.draw_icon_button(flow, "ShaderNodeLightPath")
            self.draw_icon_button(flow, "ShaderNodeObjectInfo")
            self.draw_icon_button(flow, "ShaderNodeParticleInfo")
            self.draw_icon_button(flow, "ShaderNodePointInfo")
            self.draw_icon_button(flow, "ShaderNodeRGB")
            self.draw_icon_button(flow, "ShaderNodeTangent")
            self.draw_icon_button(flow, "ShaderNodeTexCoord")

            if context.space_data.shader_type == 'LINESTYLE':
                self.draw_icon_button(flow, "ShaderNodeUVALongStroke")
            self.draw_icon_button(flow, "ShaderNodeUVMap")
            self.draw_icon_button(flow, "ShaderNodeValue")
            self.draw_icon_button(flow, "ShaderNodeVolumeInfo")
            self.draw_icon_button(flow, "ShaderNodeWireframe")


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
            self.draw_text_button(col, "ShaderNodeOutputAOV", text="AOV Output")

            if context.space_data.shader_type == 'OBJECT':
                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeOutputLight", text="Light Output")
                self.draw_text_button(col, "ShaderNodeOutputMaterial", text="Material Output")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_text_button(col, "ShaderNodeOutputWorld", text="World Output")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_text_button(col, "ShaderNodeOutputLineStyle", text="Line Style Output")

        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeOutputAOV")

            if context.space_data.shader_type == 'OBJECT':
                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeOutputLight")
                self.draw_icon_button(flow, "ShaderNodeOutputMaterial")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_icon_button(flow, "ShaderNodeOutputWorld")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_icon_button(flow, "ShaderNodeOutputLineStyle")


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
            self.draw_text_button(col, "CompositorNodeBokehImage", text="Bokeh Image")
            self.draw_text_button(col, "CompositorNodeImage", text="Image")
            self.draw_text_button(col, "CompositorNodeMask", text="Mask")
            self.draw_text_button(col, "CompositorNodeMovieClip", text="Movie Clip")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeTexture", text="Texture")


        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeBokehImage")
            self.draw_icon_button(flow, "CompositorNodeImage")
            self.draw_icon_button(flow, "CompositorNodeMask")
            self.draw_icon_button(flow, "CompositorNodeMovieClip")
            self.draw_icon_button(flow, "CompositorNodeRGB")
            self.draw_icon_button(flow, "CompositorNodeTexture")
            self.draw_icon_button(flow, "CompositorNodeValue")


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
            self.draw_text_button(col, "CompositorNodeRGB", text="RGB")
            self.draw_text_button(col, "CompositorNodeValue", text="Value")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeRGB")
            self.draw_icon_button(flow, "CompositorNodeValue")


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
            self.draw_text_button(col, "CompositorNodeRLayers", text=" Render Layers")
            self.draw_text_button(col, "CompositorNodeSceneTime", text=" Scene Time")
            self.draw_text_button(col, "CompositorNodeTime", text=" Time Curve")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeRLayers")
            self.draw_icon_button(flow, "CompositorNodeSceneTime")
            self.draw_icon_button(flow, "CompositorNodeTime")


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
            self.draw_text_button(col, "CompositorNodeComposite", text="Composite")
            self.draw_text_button(col, "CompositorNodeViewer", text="Viewer")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeOutputFile", text="File Output")


        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeComposite")
            self.draw_icon_button(flow, "CompositorNodeOutputFile")
            self.draw_icon_button(flow, "CompositorNodeViewer")

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
            self.draw_text_button(col, "CompositorNodePremulKey", text="Alpha Convert")
            self.draw_text_button(col, "CompositorNodeValToRGB", text="Color Ramp")
            self.draw_text_button(col, "CompositorNodeConvertColorSpace", text="Convert Colorspace")
            self.draw_text_button(col, "CompositorNodeSetAlpha", text="Set Alpha")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeInvert", text="Invert Color")
            self.draw_text_button(col, "CompositorNodeRGBToBW", text="RGB to BW")


        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_icon_button(flow, "CompositorNodePremulKey")
            self.draw_icon_button(flow, "CompositorNodeValToRGB")
            self.draw_icon_button(flow, "CompositorNodeConvertColorSpace")
            self.draw_icon_button(flow, "CompositorNodeSetAlpha")
            self.draw_icon_button(flow, "CompositorNodeInvert")
            self.draw_icon_button(flow, "CompositorNodeRGBToBW")


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
            self.draw_text_button(col, "CompositorNodeBrightContrast", text=" Bright / Contrast")
            self.draw_text_button(col, "CompositorNodeColorBalance", text="Color Balance")
            self.draw_text_button(col, "CompositorNodeColorCorrection", text="Color Correction")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeExposure", text="Exposure")
            self.draw_text_button(col, "CompositorNodeGamma", text="Gamma")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeHueCorrect", text="Hue Correct")
            self.draw_text_button(col, "CompositorNodeHueSat", text=" Hue/Saturation/Value")
            self.draw_text_button(col, "CompositorNodeCurveRGB", text="RGB Curves")
            self.draw_text_button(col, "CompositorNodeTonemap", text="Tonemap")



        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeBrightContrast")
            self.draw_icon_button(flow, "CompositorNodeColorBalance")
            self.draw_icon_button(flow, "CompositorNodeColorCorrection")
            self.draw_icon_button(flow, "CompositorNodeExposure")
            self.draw_icon_button(flow, "CompositorNodeGamma")
            self.draw_icon_button(flow, "CompositorNodeHueCorrect")
            self.draw_icon_button(flow, "CompositorNodeHueSat")
            self.draw_icon_button(flow, "CompositorNodeCurveRGB")
            self.draw_icon_button(flow, "CompositorNodeTonemap")


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
            self.draw_text_button(col, "CompositorNodeAlphaOver", text="Alpha Over")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeCombineColor", text="Combine Color")
            self.draw_text_button(col, "CompositorNodeSeparateColor", text="Separate Color")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeMixRGB", text="Mix Color")
            self.draw_text_button(col, "CompositorNodeZcombine", text="Z Combine")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeAlphaOver")
            self.draw_icon_button(flow, "CompositorNodeCombineColor")
            self.draw_icon_button(flow, "CompositorNodeSeparateColor")
            self.draw_icon_button(flow, "CompositorNodeMixRGB")
            self.draw_icon_button(flow, "CompositorNodeZcombine")


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
            self.draw_text_button(col, "CompositorNodeAntiAliasing", text="Anti Aliasing")
            self.draw_text_button(col, "CompositorNodeDenoise", text="Denoise")
            self.draw_text_button(col, "CompositorNodeDespeckle", text="Despeckle")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDilateErode", text=" Dilate / Erode")
            self.draw_text_button(col, "CompositorNodeInpaint", text="Inpaint")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeFilter", text="Filter")
            self.draw_text_button(col, "CompositorNodeGlare", text="Glare")
            self.draw_text_button(col, "CompositorNodeKuwahara", text="Kuwahara")
            self.draw_text_button(col, "CompositorNodePixelate", text="Pixelate")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodePosterize", text="Posterize")
            self.draw_text_button(col, "CompositorNodeSunBeams", text="Sunbeams")



        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeAntiAliasing")
            self.draw_icon_button(flow, "CompositorNodeDenoise")
            self.draw_icon_button(flow, "CompositorNodeDespeckle")
            self.draw_icon_button(flow, "CompositorNodeDilateErode")
            self.draw_icon_button(flow, "CompositorNodeInpaint")
            self.draw_icon_button(flow, "CompositorNodeFilter")
            self.draw_icon_button(flow, "CompositorNodeGlare")
            self.draw_icon_button(flow, "CompositorNodeKuwahara")
            self.draw_icon_button(flow, "CompositorNodePixelate")
            self.draw_icon_button(flow, "CompositorNodePosterize")
            self.draw_icon_button(flow, "CompositorNodeSunBeams")


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
            self.draw_text_button(col, "CompositorNodeBilateralblur", text="Bilateral Blur")
            self.draw_text_button(col, "CompositorNodeBlur", text="Blur")
            self.draw_text_button(col, "CompositorNodeBokehBlur", text="Bokeh Blur")
            self.draw_text_button(col, "CompositorNodeDefocus", text="Defocus")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDBlur", text="Directional Blur")
            self.draw_text_button(col, "CompositorNodeVecBlur", text="Vector Blur")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeBilateralblur")
            self.draw_icon_button(flow, "CompositorNodeBlur")
            self.draw_icon_button(flow, "CompositorNodeBokehBlur")
            self.draw_icon_button(flow, "CompositorNodeDefocus")
            self.draw_icon_button(flow, "CompositorNodeDBlur")
            self.draw_icon_button(flow, "CompositorNodeVecBlur")


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
            self.draw_text_button(col, "CompositorNodeChannelMatte", text="Channel Key")
            self.draw_text_button(col, "CompositorNodeChromaMatte", text="Chroma Key")
            self.draw_text_button(col, "CompositorNodeColorMatte", text="Color Key")
            self.draw_text_button(col, "CompositorNodeColorSpill", text="Color Spill")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDiffMatte", text="Difference Key")
            self.draw_text_button(col, "CompositorNodeDistanceMatte", text="Distance Key")
            self.draw_text_button(col, "CompositorNodeKeying", text="Keying")
            self.draw_text_button(col, "CompositorNodeKeyingScreen", text="Keying Screen")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeLumaMatte", text="Luminance Key")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeChannelMatte")
            self.draw_icon_button(flow, "CompositorNodeChromaMatte")
            self.draw_icon_button(flow, "CompositorNodeColorMatte")
            self.draw_icon_button(flow, "CompositorNodeColorSpill")
            self.draw_icon_button(flow, "CompositorNodeDiffMatte")
            self.draw_icon_button(flow, "CompositorNodeDistanceMatte")
            self.draw_icon_button(flow, "CompositorNodeKeying")
            self.draw_icon_button(flow, "CompositorNodeKeyingScreen")
            self.draw_icon_button(flow, "CompositorNodeLumaMatte")


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
            self.draw_text_button(col, "CompositorNodeCryptomatteV2", text="Cryptomatte")
            self.draw_text_button(col, "CompositorNodeCryptomatte", text=" Cryptomatte (Legacy)")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeBoxMask", text="Box Mask")
            self.draw_text_button(col, "CompositorNodeEllipseMask", text="Ellipse Mask")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDoubleEdgeMask", text="Double Edge Mask")
            self.draw_text_button(col, "CompositorNodeIDMask", text="ID Mask")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeCryptomatte")
            self.draw_icon_button(flow, "CompositorNodeCryptomatteV2")
            self.draw_icon_button(flow, "CompositorNodeBoxMask")
            self.draw_icon_button(flow, "CompositorNodeEllipseMask")
            self.draw_icon_button(flow, "CompositorNodeDoubleEdgeMask")
            self.draw_icon_button(flow, "CompositorNodeIDMask")


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
            self.draw_text_button(col, "ShaderNodeTexBrick", text="Brick Texture")
            self.draw_text_button(col, "ShaderNodeTexChecker", text="Checker Texture")
            self.draw_text_button(col, "ShaderNodeTexGabor", text="Gabor Texture")
            self.draw_text_button(col, "ShaderNodeTexGradient", text="Gradient Texture")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexMagic", text="Magic Texture")
            self.draw_text_button(col, "ShaderNodeTexNoise", text="Noise Texture")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text="Voronoi Texture")
            self.draw_text_button(col, "ShaderNodeTexWave", text="Wave Texture")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise", text="White Noise")


        #### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeTexBrick")
            self.draw_icon_button(flow, "ShaderNodeTexChecker")
            self.draw_icon_button(flow, "ShaderNodeTexGabor")
            self.draw_icon_button(flow, "ShaderNodeTexGradient")
            self.draw_icon_button(flow, "ShaderNodeTexMagic")
            self.draw_icon_button(flow, "ShaderNodeTexNoise")
            self.draw_icon_button(flow, "ShaderNodeTexVoronoi")
            self.draw_icon_button(flow, "ShaderNodeTexWave")
            self.draw_icon_button(flow, "ShaderNodeTexWhiteNoise")


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
            self.draw_text_button(col, "CompositorNodePlaneTrackDeform", text="Plane Track Deform")
            self.draw_text_button(col, "CompositorNodeStabilize", text=" Stabilize 2D")
            self.draw_text_button(col, "CompositorNodeTrackPos", text="Track Position")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodePlaneTrackDeform")
            self.draw_icon_button(flow, "CompositorNodeStabilize")
            self.draw_icon_button(flow, "CompositorNodeTrackPos")


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
            self.draw_text_button(col, "CompositorNodeRotate", text="Rotate")
            self.draw_text_button(col, "CompositorNodeScale", text="Scale")
            self.draw_text_button(col, "CompositorNodeTransform", text="Transform")
            self.draw_text_button(col, "CompositorNodeTranslate", text="Translate")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeCornerPin", text="Corner Pin")
            self.draw_text_button(col, "CompositorNodeCrop", text="Crop")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDisplace", text="Displace")
            self.draw_text_button(col, "CompositorNodeFlip", text="Flip")
            self.draw_text_button(col, "CompositorNodeMapUV", text="Map UV")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeLensdist", text="Lens Distortion")
            self.draw_text_button(col, "CompositorNodeMovieDistortion", text="Movie Distortion")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeRotate")
            self.draw_icon_button(flow, "CompositorNodeScale")
            self.draw_icon_button(flow, "CompositorNodeTransform")
            self.draw_icon_button(flow, "CompositorNodeTranslate")
            self.draw_icon_button(flow, "CompositorNodeCornerPin")
            self.draw_icon_button(flow, "CompositorNodeCrop")
            self.draw_icon_button(flow, "CompositorNodeDisplace")
            self.draw_icon_button(flow, "CompositorNodeFlip")
            self.draw_icon_button(flow, "CompositorNodeMapUV")
            self.draw_icon_button(flow, "CompositorNodeLensdist")
            self.draw_icon_button(flow, "CompositorNodeMovieDistortion")


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
            self.draw_text_button(col, "ShaderNodeMapRange", text="Map Range")
            self.draw_text_button(col, "ShaderNodeMath", text="Math")
            self.draw_text_button(col, "ShaderNodeMix", text="Mix")
            self.draw_text_button(col, "ShaderNodeClamp", text="Clamp")
            self.draw_text_button(col, "ShaderNodeFloatCurve", text="Float Curve")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeLevels", text="Levels")
            self.draw_text_button(col, "CompositorNodeNormalize", text="Normalize")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeSplit", text="Split")
            self.draw_text_button(col, "CompositorNodeSwitch", text="Switch")
            self.draw_text_button(col, "CompositorNodeSwitchView", text="Switch View")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeRelativeToPixel", text="Relative to Pixel")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "CompositorNodeMapRange")
            self.draw_icon_button(flow, "ShaderNodeMath")
            self.draw_icon_button(flow, "ShaderNodeClamp")
            self.draw_icon_button(flow, "ShaderNodeMix")
            self.draw_icon_button(flow, "ShaderNodeFloatCurve")
            self.draw_icon_button(flow, "CompositorNodeLevels")
            self.draw_icon_button(flow, "CompositorNodeNormalize")
            self.draw_icon_button(flow, "CompositorNodeSplit")
            self.draw_icon_button(flow, "CompositorNodeSwitch")
            self.draw_icon_button(flow, "CompositorNodeSwitchView")
            self.draw_icon_button(flow, "CompositorNodeRelativeToPixel")


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
            self.draw_text_button(col, "ShaderNodeCombineXYZ", text="Combine XYZ")
            self.draw_text_button(col, "ShaderNodeSeparateXYZ", text="Separate XYZ")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMix", text="Mix Vector", settings={"data_type": "'VECTOR'"})
            self.draw_text_button(col, "ShaderNodeVectorCurve", text="Vector Curves")

            self.draw_text_button(col, "ShaderNodeVectorMath", text="Vector Math")
            self.draw_text_button(col, "ShaderNodeVectorRotate", text="Vector Rotate")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeCombineXYZ")
            self.draw_icon_button(flow, "ShaderNodeSeparateXYZ")
            self.draw_icon_button(flow, "ShaderNodeMix", settings={"data_type": "'VECTOR'"})
            self.draw_icon_button(flow, "ShaderNodeVectorCurve")
            self.draw_icon_button(flow, "ShaderNodeVectorMath")
            self.draw_icon_button(flow, "ShaderNodeVectorRotate")


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
            self.draw_text_button(col, "TextureNodeImage", text="Image")
            self.draw_text_button(col, "TextureNodeTexture", text="Texture")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeImage")
            self.draw_icon_button(flow, "TextureNodeTexture")


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
            self.draw_text_button(col, "TextureNodeTexBlend", text="Blend")
            self.draw_text_button(col, "TextureNodeTexClouds", text="Clouds")
            self.draw_text_button(col, "TextureNodeTexDistNoise", text="Distorted Noise")
            self.draw_text_button(col, "TextureNodeTexMagic", text="Magic")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeTexMarble", text="Marble")
            self.draw_text_button(col, "TextureNodeTexNoise", text="Noise")
            self.draw_text_button(col, "TextureNodeTexStucci", text="Stucci")
            self.draw_text_button(col, "TextureNodeTexVoronoi", text="Voronoi")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeTexWood", text="Wood")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeTexBlend")
            self.draw_icon_button(flow, "TextureNodeTexClouds")
            self.draw_icon_button(flow, "TextureNodeTexDistNoise")
            self.draw_icon_button(flow, "TextureNodeTexMagic")
            self.draw_icon_button(flow, "TextureNodeTexMarble")
            self.draw_icon_button(flow, "TextureNodeTexNoise")
            self.draw_icon_button(flow, "TextureNodeTexStucci")
            self.draw_icon_button(flow, "TextureNodeTexVoronoi")
            self.draw_icon_button(flow, "TextureNodeTexWood")


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
            self.draw_text_button(col, "ShaderNodeAddShader", text="Add")
            self.draw_text_button(col, "ShaderNodeBsdfMetallic", text="Metallic")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfAnisotropic", text="Anisotopic BSDF")
                self.draw_text_button(col, "ShaderNodeBsdfDiffuse", text="Diffuse BSDF")
                self.draw_text_button(col, "ShaderNodeEmission", text="Emission")
                self.draw_text_button(col, "ShaderNodeBsdfGlass", text="Glass BSDF")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBsdfGlossy", text="Glossy BSDF")
                self.draw_text_button(col, "ShaderNodeHoldout", text="Holdout")
                self.draw_text_button(col, "ShaderNodeMixShader", text="Mix Shader")
                self.draw_text_button(col, "ShaderNodeBsdfPrincipled", text="Principled BSDF")

                col = layout.column(align=True)
                col.scale_y = 1.5

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfHairPrincipled", text="Principled Hair BSDF")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text="Principled Volume")
                self.draw_text_button(col, "ShaderNodeBsdfRefraction", text="Refraction BSDF")

                if engine == 'BLENDER_EEVEE':
                    self.draw_text_button(col, "ShaderNodeEeveeSpecular", text="Specular BSDF")
                self.draw_text_button(col, "ShaderNodeSubsurfaceScattering", text="Subsurface Scattering")

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfToon", text="Toon BSDF")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBsdfTranslucent", text="Translucent BSDF")
                self.draw_text_button(col, "ShaderNodeBsdfTransparent", text="Transparent BSDF")

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfSheen", text="Sheen BSDF")
                self.draw_text_button(col, "ShaderNodeVolumeAbsorption", text="Volume Absorption")
                self.draw_text_button(col, "ShaderNodeVolumeScatter", text="Volume Scatter")

            if context.space_data.shader_type == 'WORLD':
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBackground", text="Background")
                self.draw_text_button(col, "ShaderNodeEmission", text="Emission")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text="Principled Volume")
                self.draw_text_button(col, "ShaderNodeMixShader", text="Mix")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_icon_button(flow, "ShaderNodeAddShader")
            self.draw_icon_button(flow, "ShaderNodeBsdfMetallic")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeBsdfAnisotropic")
                self.draw_icon_button(flow, "ShaderNodeBsdfDiffuse")
                self.draw_icon_button(flow, "ShaderNodeEmission")
                self.draw_icon_button(flow, "ShaderNodeBsdfGlass")
                self.draw_icon_button(flow, "ShaderNodeBsdfGlossy")
                self.draw_icon_button(flow, "ShaderNodeHoldout")
                self.draw_icon_button(flow, "ShaderNodeMixShader")
                self.draw_icon_button(flow, "ShaderNodeBsdfPrincipled")

                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeBsdfHairPrincipled")
                self.draw_icon_button(flow, "ShaderNodeVolumePrincipled")

                if engine == 'BLENDER_EEVEE':
                    self.draw_icon_button(flow, "ShaderNodeEeveeSpecular")
                self.draw_icon_button(flow, "ShaderNodeSubsurfaceScattering")

                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeBsdfToon")
                self.draw_icon_button(flow, "ShaderNodeBsdfTranslucent")
                self.draw_icon_button(flow, "ShaderNodeBsdfTransparent")

                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeBsdfSheen")
                self.draw_icon_button(flow, "ShaderNodeVolumeAbsorption")
                self.draw_icon_button(flow, "ShaderNodeVolumeScatter")

            if context.space_data.shader_type == 'WORLD':
                self.draw_icon_button(flow, "ShaderNodeBackground")
                self.draw_icon_button(flow, "ShaderNodeEmission")
                self.draw_icon_button(flow, "ShaderNodeVolumePrincipled")
                self.draw_icon_button(flow, "ShaderNodeMixShader")


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
            self.draw_text_button(col, "ShaderNodeTexBrick", text="Brick Texture")
            self.draw_text_button(col, "ShaderNodeTexChecker", text="Checker Texture")
            self.draw_text_button(col, "ShaderNodeTexEnvironment", text="Environment Texture")
            self.draw_text_button(col, "ShaderNodeTexGabor", text="Gabor Texture")
            self.draw_text_button(col, "ShaderNodeTexGradient", text="Gradient Texture")
            self.draw_text_button(col, "ShaderNodeTexIES", text="IES Texture")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage", text="Image Texture")
            self.draw_text_button(col, "ShaderNodeTexMagic", text="Magic Texture")
            self.draw_text_button(col, "ShaderNodeTexNoise", text="Noise Texture")
            self.draw_text_button(col, "ShaderNodeTexSky", text="Sky Texture")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text="Voronoi Texture")
            self.draw_text_button(col, "ShaderNodeTexWave", text="Wave Texture")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise", text="White Noise")


        #### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeTexBrick")
            self.draw_icon_button(flow, "ShaderNodeTexChecker")
            self.draw_icon_button(flow, "ShaderNodeTexEnvironment")
            self.draw_icon_button(flow, "ShaderNodeTexGabor")
            self.draw_icon_button(flow, "ShaderNodeTexGradient")
            self.draw_icon_button(flow, "ShaderNodeTexIES")
            self.draw_icon_button(flow, "ShaderNodeTexImage")
            self.draw_icon_button(flow, "ShaderNodeTexMagic")
            self.draw_icon_button(flow, "ShaderNodeTexNoise")
            self.draw_icon_button(flow, "ShaderNodeTexPointDensity")
            self.draw_icon_button(flow, "ShaderNodeTexSky")
            self.draw_icon_button(flow, "ShaderNodeTexVoronoi")
            self.draw_icon_button(flow, "ShaderNodeTexWave")
            self.draw_icon_button(flow, "ShaderNodeTexWhiteNoise")


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
            self.draw_text_button(col, "ShaderNodeBrightContrast", text=" Bright / Contrast")
            self.draw_text_button(col, "ShaderNodeGamma", text="Gamma")
            self.draw_text_button(col, "ShaderNodeHueSaturation", text=" Hue / Saturation")
            self.draw_text_button(col, "ShaderNodeInvert", text="Invert Color")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeLightFalloff", text="Light Falloff")
            self.draw_text_button(col, "ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"})
            self.draw_text_button(col, "ShaderNodeRGBCurve", text=" RGB Curves")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeBrightContrast")
            self.draw_icon_button(flow, "ShaderNodeGamma")
            self.draw_icon_button(flow, "ShaderNodeHueSaturation")
            self.draw_icon_button(flow, "ShaderNodeInvert")
            self.draw_icon_button(flow, "ShaderNodeLightFalloff")
            self.draw_icon_button(flow, "ShaderNodeMix", settings={"data_type": "'RGBA'"})
            self.draw_icon_button(flow, "ShaderNodeRGBCurve")


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
            self.draw_text_button(col, "TextureNodeCoordinates", text="Coordinates")
            self.draw_text_button(col, "TextureNodeCurveTime", text="Curve Time")

        #### Icon Buttons

        else:
            row = layout.row()
            row.alignment = 'LEFT'
            self.draw_icon_button(flow, "TextureNodeCoordinates")
            self.draw_icon_button(flow, "TextureNodeCurveTime")


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
            self.draw_text_button(col, "TextureNodeBricks", text="Bricks")
            self.draw_text_button(col, "TextureNodeChecker", text="Checker")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeBricks")
            self.draw_icon_button(flow, "TextureNodeChecker")


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
            self.draw_text_button(col, "TextureNodeCurveRGB", text="RGB Curves")
            self.draw_text_button(col, "TextureNodeHueSaturation", text=" Hue / Saturation")
            self.draw_text_button(col, "TextureNodeInvert", text="Invert Color")
            self.draw_text_button(col, "TextureNodeMixRGB", text="Mix RGB")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeCompose", text="Combine RGBA")
            self.draw_text_button(col, "TextureNodeDecompose", text="Separate RGBA")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeCurveRGB")
            self.draw_icon_button(flow, "TextureNodeHueSaturation")
            self.draw_icon_button(flow, "TextureNodeInvert")
            self.draw_icon_button(flow, "TextureNodeMixRGB")
            self.draw_icon_button(flow, "TextureNodeCompose")
            self.draw_icon_button(flow, "TextureNodeDecompose")


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
            self.draw_text_button(col, "TextureNodeOutput", text="Output")
            self.draw_text_button(col, "TextureNodeViewer", text="Viewer")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeOutput")
            self.draw_icon_button(flow, "TextureNodeViewer")


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
            self.draw_text_button(col, "TextureNodeValToRGB", text="Color Ramp")
            self.draw_text_button(col, "TextureNodeDistance", text="Distance")
            self.draw_text_button(col, "TextureNodeMath", text="Math")
            self.draw_text_button(col, "TextureNodeRGBToBW", text="RGB to BW")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeValToNor", text="Value to Normal")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeValToRGB")
            self.draw_icon_button(flow, "TextureNodeDistance")
            self.draw_icon_button(flow, "TextureNodeMath")
            self.draw_icon_button(flow, "TextureNodeRGBToBW")
            self.draw_icon_button(flow, "TextureNodeValToNor")


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
            self.draw_text_button(col, "ShaderNodeBump", text="Bump")
            self.draw_text_button(col, "ShaderNodeDisplacement", text="Displacement")
            self.draw_text_button(col, "ShaderNodeMapping", text="Mapping")
            self.draw_text_button(col, "ShaderNodeNormal", text="Normal")
            self.draw_text_button(col, "ShaderNodeNormalMap", text="Normal Map")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeVectorCurve", text="Vector Curves")
            self.draw_text_button(col, "ShaderNodeVectorDisplacement", text="Vector Displacement")
            self.draw_text_button(col, "ShaderNodeVectorRotate", text="Vector Rotate")
            self.draw_text_button(col, "ShaderNodeVectorTransform", text="Vector Transform")

        ##### Icon Buttons

        else:

            ##### --------------------------------- Vector ------------------------------------------- ####

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeBump")
            self.draw_icon_button(flow, "ShaderNodeDisplacement")
            self.draw_icon_button(flow, "ShaderNodeMapping")
            self.draw_icon_button(flow, "ShaderNodeNormal")
            self.draw_icon_button(flow, "ShaderNodeNormalMap")
            self.draw_icon_button(flow, "ShaderNodeVectorCurve")
            self.draw_icon_button(flow, "ShaderNodeVectorDisplacement")
            self.draw_icon_button(flow, "ShaderNodeVectorRotate")
            self.draw_icon_button(flow, "ShaderNodeVectorTransform")


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
            self.draw_text_button(col, "ShaderNodeBlackbody", text="Blackbody")
            self.draw_text_button(col, "ShaderNodeClamp", text="Clamp")
            self.draw_text_button(col, "ShaderNodeValToRGB", text="ColorRamp")
            self.draw_text_button(col, "ShaderNodeCombineColor", text="Combine Color")
            self.draw_text_button(col, "ShaderNodeCombineXYZ", text="Combine XYZ")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeFloatCurve", text="Float Curve")
            self.draw_text_button(col, "ShaderNodeMapRange", text="Map Range")
            self.draw_text_button(col, "ShaderNodeMath", text="Math")
            self.draw_text_button(col, "ShaderNodeMix", text="Mix")
            self.draw_text_button(col, "ShaderNodeRGBToBW", text="RGB to BW")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeSeparateColor", text="Separate Color")
            self.draw_text_button(col, "ShaderNodeSeparateXYZ", text="Separate XYZ")

            if engine == 'BLENDER_EEVEE_NEXT':
                self.draw_text_button(col, "ShaderNodeShaderToRGB", text="Shader to RGB")
            self.draw_text_button(col, "ShaderNodeVectorMath", text="Vector Math")
            self.draw_text_button(col, "ShaderNodeWavelength", text="Wavelength")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeBlackbody")
            self.draw_icon_button(flow, "ShaderNodeClamp")
            self.draw_icon_button(flow, "ShaderNodeValToRGB")
            self.draw_icon_button(flow, "ShaderNodeCombineColor")
            self.draw_icon_button(flow, "ShaderNodeCombineXYZ")
            self.draw_icon_button(flow, "ShaderNodeFloatCurve")
            self.draw_icon_button(flow, "ShaderNodeMapRange")
            self.draw_icon_button(flow, "ShaderNodeMath")
            self.draw_icon_button(flow, "ShaderNodeMix")
            self.draw_icon_button(flow, "ShaderNodeRGBToBW")
            self.draw_icon_button(flow, "ShaderNodeSeparateColor")
            self.draw_icon_button(flow, "ShaderNodeSeparateXYZ")

            if engine == 'BLENDER_EEVEE':
                self.draw_icon_button(flow, "ShaderNodeShaderToRGB")
            self.draw_icon_button(flow, "ShaderNodeVectorMath")
            self.draw_icon_button(flow, "ShaderNodeWavelength")


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
            self.draw_text_button(col, "TextureNodeAt", text="At")
            self.draw_text_button(col, "TextureNodeRotate", text="Rotate")
            self.draw_text_button(col, "TextureNodeScale", text="Scale")
            self.draw_text_button(col, "TextureNodeTranslate", text="Translate")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "TextureNodeAt")
            self.draw_icon_button(flow, "TextureNodeRotate")
            self.draw_icon_button(flow, "TextureNodeScale")
            self.draw_icon_button(flow, "TextureNodeTranslate")


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
                self.draw_text_button(col, "NodeGroupInput", text="Group Input")
                self.draw_text_button(col, "NodeGroupOutput", text="Group Output")


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
                self.draw_icon_button(flow, "NodeGroupInput")
                self.draw_icon_button(flow, "NodeGroupOutput")


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
            self.draw_text_button(col, "NodeFrame", text="Frame")
            self.draw_text_button(col, "NodeReroute", text="Reroute")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "NodeFrame")
            self.draw_icon_button(flow, "NodeReroute")



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
            self.draw_text_button(col, "GeometryNodeAttributeStatistic", text="Attribute Statistics")
            self.draw_text_button(col, "GeometryNodeAttributeDomainSize", text="Domain Size")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeBlurAttribute", text="Blur Attribute")
            self.draw_text_button(col, "GeometryNodeCaptureAttribute", text="Capture Attribute")
            self.draw_text_button(col, "GeometryNodeRemoveAttribute", text="Remove Attribute")
            self.draw_text_button(col, "GeometryNodeStoreNamedAttribute", text="Store Named Attribute")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeAttributeStatistic")
            self.draw_icon_button(flow, "GeometryNodeAttributeDomainSize")
            self.draw_icon_button(flow, "GeometryNodeBlurAttribute")
            self.draw_icon_button(flow, "GeometryNodeCaptureAttribute")
            self.draw_icon_button(flow, "GeometryNodeRemoveAttribute")
            self.draw_icon_button(flow, "GeometryNodeStoreNamedAttribute")


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
            self.draw_text_button(col, "FunctionNodeInputBool", text="Boolean")
            self.draw_text_button(col, "GeometryNodeInputCollection", text="Collection")
            self.draw_text_button(col, "FunctionNodeInputColor", text="Color")
            self.draw_text_button(col, "GeometryNodeInputImage", text="Image")
            self.draw_text_button(col, "FunctionNodeInputInt", text="Integer")
            self.draw_text_button(col, "GeometryNodeInputMaterial", text="Material")
            self.draw_text_button(col, "GeometryNodeInputObject", text="Object")
            self.draw_text_button(col, "FunctionNodeInputRotation", text="Rotation")
            self.draw_text_button(col, "FunctionNodeInputString", text="String")
            self.draw_text_button(col, "ShaderNodeValue", text="Value")
            self.draw_text_button(col, "FunctionNodeInputVector", text="Vector")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_icon_button(flow, "FunctionNodeInputBool")
            self.draw_icon_button(flow, "GeometryNodeInputCollection")
            self.draw_icon_button(flow, "FunctionNodeInputColor")
            self.draw_icon_button(flow, "GeometryNodeInputImage")
            self.draw_icon_button(flow, "FunctionNodeInputInt")
            self.draw_icon_button(flow, "GeometryNodeInputMaterial")
            self.draw_icon_button(flow, "GeometryNodeInputObject")
            self.draw_icon_button(flow, "FunctionNodeInputRotation")
            self.draw_icon_button(flow, "FunctionNodeInputString")
            self.draw_icon_button(flow, "ShaderNodeValue")
            self.draw_icon_button(flow, "FunctionNodeInputVector")


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
            self.draw_text_button(col, "GeometryNodeGizmoDial", text="Dial Gizmo")
            self.draw_text_button(col, "GeometryNodeGizmoLinear", text="Linear Gizmo")
            self.draw_text_button(col, "GeometryNodeGizmoTransform", text="Transform Gizmo")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_icon_button(flow, "GeometryNodeGizmoDial")
            self.draw_icon_button(flow, "GeometryNodeGizmoLinear")
            self.draw_icon_button(flow, "GeometryNodeGizmoTransform")


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
            self.draw_text_button(col, "GeometryNodeImportOBJ", text="Import OBJ")
            self.draw_text_button(col, "GeometryNodeImportPLY", text="Import PLY")
            self.draw_text_button(col, "GeometryNodeImportSTL", text="Import STL")
            self.draw_text_button(col, "GeometryNodeImportCSV", text="Import CSV")
            self.draw_text_button(col, "GeometryNodeImportText", text="Import Text")
            self.draw_text_button(col, "GeometryNodeImportVDB", text="Import OpenVDB")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeImportOBJ")
            self.draw_icon_button(flow, "GeometryNodeImportPLY")
            self.draw_icon_button(flow, "GeometryNodeImportSTL")
            self.draw_icon_button(flow, "GeometryNodeImportCSV")
            self.draw_icon_button(flow, "GeometryNodeImportText")
            self.draw_icon_button(flow, "GeometryNodeImportVDB")



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
                self.draw_text_button(col, "GeometryNodeTool3DCursor", text="Cursor")
            self.draw_text_button(col, "GeometryNodeInputActiveCamera", text="Active Camera")
            self.draw_text_button(col, "GeometryNodeCameraInfo", text="Camera Info")
            self.draw_text_button(col, "GeometryNodeCollectionInfo", text="Collection Info")
            self.draw_text_button(col, "GeometryNodeImageInfo", text="Image Info")
            self.draw_text_button(col, "GeometryNodeIsViewport", text="Is Viewport")
            self.draw_text_button(col, "GeometryNodeInputNamedLayerSelection", text="Named Layer Selection")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolMousePosition", text="Mouse Position")
            self.draw_text_button(col, "GeometryNodeObjectInfo", text="Object Info")
            self.draw_text_button(col, "GeometryNodeInputSceneTime", text="Scene Time")
            self.draw_text_button(col, "GeometryNodeSelfObject", text="Self Object")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeViewportTransform", text="Viewport Transform")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeTool3DCursor")
            self.draw_icon_button(flow, "GeometryNodeInputActiveCamera")
            self.draw_icon_button(flow, "GeometryNodeCameraInfo")
            self.draw_icon_button(flow, "GeometryNodeCollectionInfo")
            self.draw_icon_button(flow, "GeometryNodeImageInfo")
            self.draw_icon_button(flow, "GeometryNodeIsViewport")
            self.draw_icon_button(flow, "GeometryNodeInputNamedLayerSelection")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeToolMousePosition")
            self.draw_icon_button(flow, "GeometryNodeObjectInfo")
            self.draw_icon_button(flow, "GeometryNodeInputSceneTime")
            self.draw_icon_button(flow, "GeometryNodeSelfObject")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeViewportTransform")


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
            self.draw_text_button(col, "GeometryNodeViewer", text="Viewer")
            self.draw_text_button(col, "GeometryNodeWarning", text="Warning")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeViewer")
            self.draw_icon_button(flow, "GeometryNodeWarning")


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
            self.draw_text_button(col, "GeometryNodeGeometryToInstance", text="Geometry to Instance")
            self.draw_text_button(col, "GeometryNodeJoinGeometry", text="Join Geometry")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeGeometryToInstance")
            self.draw_icon_button(flow, "GeometryNodeJoinGeometry")


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
            self.draw_text_button(col, "GeometryNodeInputID", text="ID")
            self.draw_text_button(col, "GeometryNodeInputIndex", text="Index")
            self.draw_text_button(col, "GeometryNodeInputNamedAttribute", text="Named Attribute")
            self.draw_text_button(col, "GeometryNodeInputNormal", text="Normal")
            self.draw_text_button(col, "GeometryNodeInputPosition", text="Position")
            self.draw_text_button(col, "GeometryNodeInputRadius", text="Radius")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolSelection", text="Selection")
                self.draw_text_button(col, "GeometryNodeToolActiveElement", text="Active Element")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeInputID")
            self.draw_icon_button(flow, "GeometryNodeInputIndex")
            self.draw_icon_button(flow, "GeometryNodeInputNamedAttribute")
            self.draw_icon_button(flow, "GeometryNodeInputNormal")
            self.draw_icon_button(flow, "GeometryNodeInputPosition")
            self.draw_icon_button(flow, "GeometryNodeInputRadius")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeToolSelection")
                self.draw_icon_button(flow, "GeometryNodeToolActiveElement")



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
            self.draw_text_button(col, "GeometryNodeProximity", text="Geometry Proximity")
            self.draw_text_button(col, "GeometryNodeIndexOfNearest", text="Index of Nearest")
            self.draw_text_button(col, "GeometryNodeRaycast", text="Raycast")
            self.draw_text_button(col, "GeometryNodeSampleIndex", text="Sample Index")
            self.draw_text_button(col, "GeometryNodeSampleNearest", text="Sample Nearest")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeMergeByDistance")
            self.draw_icon_button(flow, "GeometryNodeIndexOfNearest")
            self.draw_icon_button(flow, "GeometryNodeRaycast")
            self.draw_icon_button(flow, "GeometryNodeSampleIndex")
            self.draw_icon_button(flow, "GeometryNodeSampleNearest")


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
            self.draw_text_button(col, "GeometryNodeSetGeometryName", text="Set Geometry Name")
            self.draw_text_button(col, "GeometryNodeSetID", text="Set ID")
            self.draw_text_button(col, "GeometryNodeSetPosition", text="Set Postion")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolSetSelection", text="Set Selection")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeSetGeometryName")
            self.draw_icon_button(flow, "GeometryNodeSetID")
            self.draw_icon_button(flow, "GeometryNodeSetPosition")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeToolSetSelection")


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
            self.draw_text_button(col, "GeometryNodeBake", text="Bake")
            self.draw_text_button(col, "GeometryNodeBoundBox", text="Bounding Box")
            self.draw_text_button(col, "GeometryNodeConvexHull", text="Convex Hull")
            self.draw_text_button(col, "GeometryNodeDeleteGeometry", text="Delete Geometry")
            self.draw_text_button(col, "GeometryNodeDuplicateElements", text="Duplicate Geometry")
            self.draw_text_button(col, "GeometryNodeMergeByDistance", text="Merge by Distance")
            self.draw_text_button(col, "GeometryNodeSortElements", text="Sort Elements")
            self.draw_text_button(col, "GeometryNodeTransform", text="Transform Geometry")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeSeparateComponents", text="Separate Components")
            self.draw_text_button(col, "GeometryNodeSeparateGeometry", text="Separate Geometry")
            self.draw_text_button(col, "GeometryNodeSplitToInstances", text="Split to Instances")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeBake")
            self.draw_icon_button(flow, "GeometryNodeBoundBox")
            self.draw_icon_button(flow, "GeometryNodeConvexHull")
            self.draw_icon_button(flow, "GeometryNodeDeleteGeometry")
            self.draw_icon_button(flow, "GeometryNodeDuplicateElements")
            self.draw_icon_button(flow, "GeometryNodeMergeByDistance")
            self.draw_icon_button(flow, "GeometryNodeSortElements")
            self.draw_icon_button(flow, "GeometryNodeTransform")
            self.draw_icon_button(flow, "GeometryNodeSeparateComponents")
            self.draw_icon_button(flow, "GeometryNodeSeparateGeometry")
            self.draw_icon_button(flow, "GeometryNodeSplitToInstances")


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
            self.draw_text_button(col, "GeometryNodeInputCurveHandlePositions", text="Curve Handle Positions")
            self.draw_text_button(col, "GeometryNodeCurveLength", text="Curve Length")
            self.draw_text_button(col, "GeometryNodeInputTangent", text="Curve Tangent")
            self.draw_text_button(col, "GeometryNodeInputCurveTilt", text="Curve Tilt")
            self.draw_text_button(col, "GeometryNodeCurveEndpointSelection", text="Endpoint Selection")
            self.draw_text_button(col, "GeometryNodeCurveHandleTypeSelection", text="Handle Type Selection")
            self.draw_text_button(col, "GeometryNodeInputSplineCyclic", text="Is Spline Cyclic")
            self.draw_text_button(col, "GeometryNodeSplineLength", text="Spline Length")
            self.draw_text_button(col, "GeometryNodeSplineParameter", text="Spline Parameter")
            self.draw_text_button(col, "GeometryNodeInputSplineResolution", text="Spline Resolution")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeInputCurveHandlePositions")
            self.draw_icon_button(flow, "GeometryNodeCurveLength")
            self.draw_icon_button(flow, "GeometryNodeInputTangent")
            self.draw_icon_button(flow, "GeometryNodeInputCurveTilt")
            self.draw_icon_button(flow, "GeometryNodeCurveEndpointSelection")
            self.draw_icon_button(flow, "GeometryNodeCurveHandleTypeSelection")
            self.draw_icon_button(flow, "GeometryNodeInputSplineCyclic")
            self.draw_icon_button(flow, "GeometryNodeSplineLength")
            self.draw_icon_button(flow, "GeometryNodeSplineParameter")
            self.draw_icon_button(flow, "GeometryNodeInputSplineResolution")


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
            self.draw_text_button(col, "GeometryNodeSampleCurve", text="Sample Curve")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeSampleCurve")




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
            self.draw_text_button(col, "GeometryNodeSetCurveNormal", text="Set Curve Normal")
            self.draw_text_button(col, "GeometryNodeSetCurveRadius", text="Set Curve Radius")
            self.draw_text_button(col, "GeometryNodeSetCurveTilt", text="Set Curve Tilt")
            self.draw_text_button(col, "GeometryNodeSetCurveHandlePositions", text="Set Handle Positions")
            self.draw_text_button(col, "GeometryNodeCurveSetHandles", text="Set Handle Type")
            self.draw_text_button(col, "GeometryNodeSetSplineCyclic", text="Set Spline Cyclic")
            self.draw_text_button(col, "GeometryNodeSetSplineResolution", text="Set Spline Resolution")
            self.draw_text_button(col, "GeometryNodeCurveSplineType", text="Set Spline Type")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeSetCurveNormal")
            self.draw_icon_button(flow, "GeometryNodeSetCurveRadius")
            self.draw_icon_button(flow, "GeometryNodeSetCurveTilt")
            self.draw_icon_button(flow, "GeometryNodeSetCurveHandlePositions")
            self.draw_icon_button(flow, "GeometryNodeCurveSetHandles")
            self.draw_icon_button(flow, "GeometryNodeSetSplineCyclic")
            self.draw_icon_button(flow, "GeometryNodeSetSplineResolution")
            self.draw_icon_button(flow, "GeometryNodeCurveSplineType")


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
            self.draw_text_button(col, "GeometryNodeCurvesToGreasePencil", text="Curves to Grease Pencil")
            self.draw_text_button(col, "GeometryNodeCurveToMesh", text="Curve to Mesh")
            self.draw_text_button(col, "GeometryNodeCurveToPoints", text="Curve to Points")
            self.draw_text_button(col, "GeometryNodeDeformCurvesOnSurface", text="Deform Curves on Surface")
            self.draw_text_button(col, "GeometryNodeFillCurve", text="Fill Curve")
            self.draw_text_button(col, "GeometryNodeFilletCurve", text="Fillet Curve")
            self.draw_text_button(col, "GeometryNodeGreasePencilToCurves", text="Grease Pencil to Curves")
            self.draw_text_button(col, "GeometryNodeInterpolateCurves", text="Interpolate Curve")
            self.draw_text_button(col, "GeometryNodeInterpolateCurves", text="Merge Layers")
            self.draw_text_button(col, "GeometryNodeResampleCurve", text="Resample Curve")
            self.draw_text_button(col, "GeometryNodeReverseCurve", text="Reverse Curve")
            self.draw_text_button(col, "GeometryNodeSubdivideCurve", text="Subdivide Curve")
            self.draw_text_button(col, "GeometryNodeTrimCurve", text="Trim Curve")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeCurvesToGreasePencil")
            self.draw_icon_button(flow, "GeometryNodeCurveToMesh")
            self.draw_icon_button(flow, "GeometryNodeCurveToPoints")
            self.draw_icon_button(flow, "GeometryNodeDeformCurvesOnSurface")
            self.draw_icon_button(flow, "GeometryNodeFillCurve")
            self.draw_icon_button(flow, "GeometryNodeFilletCurve")
            self.draw_icon_button(flow, "GeometryNodeGreasePencilToCurves")
            self.draw_icon_button(flow, "GeometryNodeInterpolateCurves")
            self.draw_icon_button(flow, "GeometryNodeInterpolateCurves")
            self.draw_icon_button(flow, "GeometryNodeResampleCurve")
            self.draw_icon_button(flow, "GeometryNodeReverseCurve")
            self.draw_icon_button(flow, "GeometryNodeSubdivideCurve")
            self.draw_icon_button(flow, "GeometryNodeTrimCurve")


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
            self.draw_text_button(col, "GeometryNodeCurveArc", text="Arc")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveBezierSegment", text="Bezier Segment")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveCircle", text="Curve Circle")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveLine", text="Curve Line")
            self.draw_text_button(col, "GeometryNodeCurveSpiral", text="Curve Spiral")
            self.draw_text_button(col, "GeometryNodeCurveQuadraticBezier", text="Quadratic Bezier")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveQuadrilateral", text="Quadrilateral")
            self.draw_text_button(col, "GeometryNodeCurveStar", text="Star")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeCurveArc")
            self.draw_icon_button(flow, "GeometryNodeCurvePrimitiveBezierSegment")
            self.draw_icon_button(flow, "GeometryNodeCurvePrimitiveCircle")
            self.draw_icon_button(flow, "GeometryNodeCurvePrimitiveLine")
            self.draw_icon_button(flow, "GeometryNodeCurveSpiral")
            self.draw_icon_button(flow, "GeometryNodeCurveQuadraticBezier")
            self.draw_icon_button(flow, "GeometryNodeCurvePrimitiveQuadrilateral")
            self.draw_icon_button(flow, "GeometryNodeCurveStar")


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
            self.draw_text_button(col, "GeometryNodeCurveOfPoint", text="Curve of Point")
            self.draw_text_button(col, "GeometryNodeOffsetPointInCurve", text="Offset Point in Curve")
            self.draw_text_button(col, "GeometryNodePointsOfCurve", text="Points of Curve")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeCurveOfPoint")
            self.draw_icon_button(flow, "GeometryNodeOffsetPointInCurve")
            self.draw_icon_button(flow, "GeometryNodePointsOfCurve")


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
            self.draw_text_button(col, "GeometryNodeInputNamedLayerSelection", text="Named Layer Selection")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeInputNamedLayerSelection")


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
            self.draw_text_button(col, "GeometryNodeSetGreasePencilColor", text="Set Grease Pencil Color")
            self.draw_text_button(col, "GeometryNodeSetGreasePencilDepth", text="Set Grease Pencil Depth")
            self.draw_text_button(col, "GeometryNodeSetGreasePencilSoftness", text="Set Grease Pencil Softness")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeSetGreasePencilColor")
            self.draw_icon_button(flow, "GeometryNodeSetGreasePencilDepth")
            self.draw_icon_button(flow, "GeometryNodeSetGreasePencilSoftness")


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
            self.draw_text_button(col, "GeometryNodeGreasePencilToCurves", text="Set Grease Pencil to Curves")
            self.draw_text_button(col, "GeometryNodeMergeLayers", text="Merge Layers")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeGreasePencilToCurves")
            self.draw_icon_button(flow, "GeometryNodeMergeLayers")


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
            self.draw_text_button(col, "GeometryNodeInstanceOnPoints", text="Instances on Points")
            self.draw_text_button(col, "GeometryNodeInstancesToPoints", text="Instances to Points")
            self.draw_text_button(col, "GeometryNodeRealizeInstances", text="Realize Instances")
            self.draw_text_button(col, "GeometryNodeRotateInstances", text="Rotate Instances")
            self.draw_text_button(col, "GeometryNodeScaleInstances", text="Scale Instances")
            self.draw_text_button(col, "GeometryNodeTranslateInstances", text="Translate Instances")
            self.draw_text_button(col, "GeometryNodeSetInstanceTransform", text="Set Instance Transform")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeInstanceTransform", text="Instance Transform")
            self.draw_text_button(col, "GeometryNodeInputInstanceRotation", text="Instance Rotation")
            self.draw_text_button(col, "GeometryNodeInputInstanceScale", text="Instance Scale")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeInstanceOnPoints")
            self.draw_icon_button(flow, "GeometryNodeInstancesToPoints")
            self.draw_icon_button(flow, "GeometryNodeRealizeInstances")
            self.draw_icon_button(flow, "GeometryNodeRotateInstances")
            self.draw_icon_button(flow, "GeometryNodeTriangulate")
            self.draw_icon_button(flow, "GeometryNodeTranslateInstances")
            self.draw_icon_button(flow, "GeometryNodeSetInstanceTransform")
            self.draw_icon_button(flow, "GeometryNodeInstanceTransform")
            self.draw_icon_button(flow, "GeometryNodeInputInstanceRotation")
            self.draw_icon_button(flow, "GeometryNodeInputInstanceScale")


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
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeAngle", text="Edge Angle")
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeNeighbors", text="Edge Neighbors")
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeVertices", text="Edge Vertices")
            self.draw_text_button(col, "GeometryNodeEdgesToFaceGroups", text="Edges to Face Groups")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceArea", text="Face Area")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshFaceSetBoundaries", text="Face Group Boundaries")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceNeighbors", text="Face Neighbors")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolFaceSet", text="Face Set")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceIsPlanar", text="Is Face Planar")
            self.draw_text_button(col, "GeometryNodeInputShadeSmooth", text="Is Face Smooth")
            self.draw_text_button(col, "GeometryNodeInputEdgeSmooth", text="is Edge Smooth")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeInputMeshIsland", text="Mesh Island")
            self.draw_text_button(col, "GeometryNodeInputShortestEdgePaths", text="Shortest Edge Path")
            self.draw_text_button(col, "GeometryNodeInputMeshVertexNeighbors", text="Vertex Neighbors")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeInputMeshEdgeAngle")
            self.draw_icon_button(flow, "GeometryNodeInputMeshEdgeNeighbors")
            self.draw_icon_button(flow, "GeometryNodeInputMeshEdgeVertices")
            self.draw_icon_button(flow, "GeometryNodeEdgesToFaceGroups")
            self.draw_icon_button(flow, "GeometryNodeInputMeshFaceArea")
            self.draw_icon_button(flow, "GeometryNodeMeshFaceSetBoundaries")
            self.draw_icon_button(flow, "GeometryNodeInputMeshFaceNeighbors")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeToolFaceSet")
            self.draw_icon_button(flow, "GeometryNodeInputMeshFaceIsPlanar")
            self.draw_icon_button(flow, "GeometryNodeInputShadeSmooth")
            self.draw_icon_button(flow, "GeometryNodeInputEdgeSmooth")
            self.draw_icon_button(flow, "GeometryNodeInputMeshIsland")
            self.draw_icon_button(flow, "GeometryNodeInputShortestEdgePaths")
            self.draw_icon_button(flow, "GeometryNodeInputMeshVertexNeighbors")


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
            self.draw_text_button(col, "GeometryNodeSampleNearestSurface", text="Sample Nearest Surface")
            self.draw_text_button(col, "GeometryNodeSampleUVSurface", text="Sample UV Surface")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeSampleNearestSurface")
            self.draw_icon_button(flow, "GeometryNodeSampleUVSurface")


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
                self.draw_text_button(col, "GeometryNodeToolFaceSet", text="Set Face Set")
            self.draw_text_button(col, "GeometryNodeSetMeshNormal", text="Set Mesh Normal")
            self.draw_text_button(col, "GeometryNodeSetShadeSmooth", text="Set Shade Smooth")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_icon_button(flow, "GeometryNodeToolSetFaceSet")
            self.draw_icon_button(flow, "GeometryNodeSetMeshNormal")
            self.draw_icon_button(flow, "GeometryNodeSetShadeSmooth")


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
            self.draw_text_button(col, "GeometryNodeDualMesh", text="Dual Mesh")
            self.draw_text_button(col, "GeometryNodeEdgePathsToCurves", text="Edge Paths to Curves")
            self.draw_text_button(col, "GeometryNodeEdgePathsToSelection", text="Edge Paths to Selection")
            self.draw_text_button(col, "GeometryNodeExtrudeMesh", text="Extrude Mesh")
            self.draw_text_button(col, "GeometryNodeFlipFaces", text="Flip Faces")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshBoolean", text="Mesh Boolean")
            self.draw_text_button(col, "GeometryNodeMeshToCurve", text="Mesh to Curve")
            self.draw_text_button(col, "GeometryNodeMeshToPoints", text="Mesh to Points")
            self.draw_text_button(col, "GeometryNodeMeshToVolume", text="Mesh to Volume")
            self.draw_text_button(col, "GeometryNodeScaleElements", text="Scale Elements")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeSplitEdges", text="Split Edges")
            self.draw_text_button(col, "GeometryNodeSubdivideMesh", text="Subdivide Mesh")
            self.draw_text_button(col, "GeometryNodeSubdivisionSurface", text="Subdivision Surface")
            self.draw_text_button(col, "GeometryNodeTriangulate", text="Triangulate")


        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeDualMesh")
            self.draw_icon_button(flow, "GeometryNodeEdgePathsToCurves")
            self.draw_icon_button(flow, "GeometryNodeEdgePathsToSelection")
            self.draw_icon_button(flow, "GeometryNodeExtrudeMesh")
            self.draw_icon_button(flow, "GeometryNodeFlipFaces")
            self.draw_icon_button(flow, "GeometryNodeMeshBoolean")
            self.draw_icon_button(flow, "GeometryNodeMeshToCurve")
            self.draw_icon_button(flow, "GeometryNodeMeshToPoints")
            self.draw_icon_button(flow, "GeometryNodeMeshToVolume")
            self.draw_icon_button(flow, "GeometryNodeScaleElements")
            self.draw_icon_button(flow, "GeometryNodeSplitEdges")
            self.draw_icon_button(flow, "GeometryNodeSubdivideMesh")
            self.draw_icon_button(flow, "GeometryNodeSubdivisionSurface")
            self.draw_icon_button(flow, "GeometryNodeTriangulate")


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
            self.draw_text_button(col, "GeometryNodeMeshCone", text="Cone")
            self.draw_text_button(col, "GeometryNodeMeshCube", text="Cube")
            self.draw_text_button(col, "GeometryNodeMeshCylinder", text="Cylinder")
            self.draw_text_button(col, "GeometryNodeMeshGrid", text="Grid")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshIcoSphere", text="Ico Sphere")
            self.draw_text_button(col, "GeometryNodeMeshCircle", text="Mesh Circle")
            self.draw_text_button(col, "GeometryNodeMeshLine", text="Mesh Line")
            self.draw_text_button(col, "GeometryNodeMeshUVSphere", text="UV Sphere")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeMeshCone")
            self.draw_icon_button(flow, "GeometryNodeMeshCube")
            self.draw_icon_button(flow, "GeometryNodeMeshCylinder")
            self.draw_icon_button(flow, "GeometryNodeMeshGrid")
            self.draw_icon_button(flow, "GeometryNodeMeshIcoSphere")
            self.draw_icon_button(flow, "GeometryNodeMeshCircle")
            self.draw_icon_button(flow, "GeometryNodeMeshLine")
            self.draw_icon_button(flow, "GeometryNodeMeshUVSphere")


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
            self.draw_text_button(col, "GeometryNodeCornersOfEdge", text="Corners of Edge")
            self.draw_text_button(col, "GeometryNodeCornersOfFace", text="Corners of Face")
            self.draw_text_button(col, "GeometryNodeCornersOfVertex", text="Corners of Vertex")
            self.draw_text_button(col, "GeometryNodeEdgesOfCorner", text="Edges of Corner")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeEdgesOfVertex", text="Edges of Vertex")
            self.draw_text_button(col, "GeometryNodeFaceOfCorner", text="Face of Corner")
            self.draw_text_button(col, "GeometryNodeOffsetCornerInFace", text="Offset Corner In Face")
            self.draw_text_button(col, "GeometryNodeVertexOfCorner", text="Vertex of Corner")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeCornersOfEdge")
            self.draw_icon_button(flow, "GeometryNodeCornersOfFace")
            self.draw_icon_button(flow, "GeometryNodeCornersOfVertex")
            self.draw_icon_button(flow, "GeometryNodeEdgesOfCorner")
            self.draw_icon_button(flow, "GeometryNodeEdgesOfVertex")
            self.draw_icon_button(flow, "GeometryNodeFaceOfCorner")
            self.draw_icon_button(flow, "GeometryNodeOffsetCornerInFace")
            self.draw_icon_button(flow, "GeometryNodeVertexOfCorner")


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
            self.draw_text_button(col, "GeometryNodeUVPackIslands", text="Pack UV Islands")
            self.draw_text_button(col, "GeometryNodeUVUnwrap", text="UV Unwrap")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeUVPackIslands")
            self.draw_icon_button(flow, "GeometryNodeUVUnwrap")


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
            self.draw_text_button(col, "GeometryNodeDistributePointsInVolume", text="Distribute Points in Volume")
            self.draw_text_button(col, "GeometryNodeDistributePointsOnFaces", text="Distribute Points on Faces")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodePoints", text="Points")
            self.draw_text_button(col, "GeometryNodePointsToCurves", text="Points to Curves")
            self.draw_text_button(col, "GeometryNodePointsToVertices", text="Points to Vertices")
            self.draw_text_button(col, "GeometryNodePointsToVolume", text="Points to Volume")
            self.draw_text_button(col, "GeometryNodeSetPointRadius", text="Set Point Radius")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeDistributePointsInVolume")
            self.draw_icon_button(flow, "GeometryNodeDistributePointsOnFaces")
            self.draw_icon_button(flow, "GeometryNodePoints")
            self.draw_icon_button(flow, "GeometryNodePointsToCurves")
            self.draw_icon_button(flow, "GeometryNodePointsToVertices")
            self.draw_icon_button(flow, "GeometryNodePointsToVolume")
            self.draw_icon_button(flow, "GeometryNodeSetPointRadius")


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
            self.draw_text_button(col, "GeometryNodeVolumeCube", text="Volume Cube")
            self.draw_text_button(col, "GeometryNodeVolumeToMesh", text="Volume to Mesh")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeVolumeCube")
            self.draw_icon_button(flow, "GeometryNodeVolumeToMesh")

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
            self.draw_text_button(col, operator="node.add_simulation_zone", text="Simulation Zone", icon="TIME")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, operator="node.add_simulation_zone", icon="TIME")


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
            self.draw_text_button(col, "GeometryNodeReplaceMaterial", text="Replace Material")
            self.draw_text_button(col, "GeometryNodeInputMaterialIndex", text="Material Index")
            self.draw_text_button(col, "GeometryNodeMaterialSelection", text="Material Selection")
            self.draw_text_button(col, "GeometryNodeSetMaterial", text="Set Material")
            self.draw_text_button(col, "GeometryNodeSetMaterialIndex", text="Set Material Index")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeReplaceMaterial")
            self.draw_icon_button(flow, "GeometryNodeInputMaterialIndex")
            self.draw_icon_button(flow, "GeometryNodeMaterialSelection")
            self.draw_icon_button(flow, "GeometryNodeSetMaterial")
            self.draw_icon_button(flow, "GeometryNodeSetMaterialIndex")


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
            self.draw_text_button(col, "ShaderNodeTexBrick", text="Brick Texture")
            self.draw_text_button(col, "ShaderNodeTexChecker", text="Checker Texture")
            self.draw_text_button(col, "ShaderNodeTexGradient", text="Gradient Texture")
            self.draw_text_button(col, "GeometryNodeImageTexture", text="Image Texture")
            self.draw_text_button(col, "ShaderNodeTexMagic", text="Magic Texture")
            self.draw_text_button(col, "ShaderNodeTexNoise", text="Noise Texture")
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text="Voronoi Texture")
            self.draw_text_button(col, "ShaderNodeTexWave", text="Wave Texture")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise", text="White Noise")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeTexBrick")
            self.draw_icon_button(flow, "ShaderNodeTexChecker")
            self.draw_icon_button(flow, "ShaderNodeTexGradient")
            self.draw_icon_button(flow, "GeometryNodeImageTexture")
            self.draw_icon_button(flow, "ShaderNodeTexMagic")
            self.draw_icon_button(flow, "ShaderNodeTexNoise")
            self.draw_icon_button(flow, "ShaderNodeTexVoronoi")
            self.draw_icon_button(flow, "ShaderNodeTexWave")
            self.draw_icon_button(flow, "ShaderNodeTexWhiteNoise")


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
            self.draw_text_button(col, operator="node.add_foreach_geometry_element_zone", text="For Each Element", icon="FOR_EACH")
            self.draw_text_button(col, "GeometryNodeIndexSwitch", text="Index Switch")
            self.draw_text_button(col, "GeometryNodeMenuSwitch", text="Menu Switch")
            self.draw_text_button(col, "FunctionNodeRandomValue", text="Random Value")
            self.draw_text_button(col, operator="node.add_repeat_zone", text="Repeat Zone", icon="REPEAT")
            self.draw_text_button(col, "GeometryNodeSwitch", text="Switch")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeIndexSwitch")
            self.draw_icon_button(flow, "GeometryNodeMenuSwitch")
            self.draw_icon_button(flow, "FunctionNodeRandomValue")
            self.draw_icon_button(flow, operator="node.add_repeat_zone", icon="REPEAT")
            self.draw_icon_button(flow, "GeometryNodeSwitch")


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
            self.draw_text_button(col, "ShaderNodeValToRGB", text="ColorRamp")
            self.draw_text_button(col, "ShaderNodeRGBCurve", text="RGB Curves")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "FunctionNodeCombineColor", text="Combine Color")
            self.draw_text_button(col, "FunctionNodeSeparateColor", text="Separate Color")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeValToRGB")
            self.draw_icon_button(flow, "ShaderNodeRGBCurve")
            self.draw_icon_button(flow, "FunctionNodeCombineColor")
            self.draw_icon_button(flow, "ShaderNodeMix", settings={"data_type": "'RGBA'"})
            self.draw_icon_button(flow, "FunctionNodeSeparateColor")


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
            self.draw_text_button(col, "FunctionNodeFormatString", text="Format String")
            self.draw_text_button(col, "GeometryNodeStringJoin", text="Join Strings")
            self.draw_text_button(col, "FunctionNodeMatchString", text="Match String")
            self.draw_text_button(col, "FunctionNodeReplaceString", text="Replace Strings")
            self.draw_text_button(col, "FunctionNodeSliceString", text="Slice Strings")
            self.draw_text_button(col, "FunctionNodeStringLength", text="String Length")
            self.draw_text_button(col, "FunctionNodeFindInString", text="Find in String")
            self.draw_text_button(col, "GeometryNodeStringToCurves", text="String to Curves")
            self.draw_text_button(col, "FunctionNodeValueToString", text="Value to String")
            self.draw_text_button(col, "FunctionNodeInputSpecialCharacters", text="Special Characters")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "FunctionNodeFormatString")
            self.draw_icon_button(flow, "GeometryNodeStringJoin")
            self.draw_icon_button(flow, "FunctionNodeMatchString")
            self.draw_icon_button(flow, "FunctionNodeReplaceString")
            self.draw_icon_button(flow, "FunctionNodeSliceString")
            self.draw_icon_button(flow, "FunctionNodeStringLength")
            self.draw_icon_button(flow, "FunctionNodeFindInString")
            self.draw_icon_button(flow, "GeometryNodeStringToCurves")
            self.draw_icon_button(flow, "FunctionNodeValueToString")
            self.draw_icon_button(flow, "FunctionNodeInputSpecialCharacters")


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
            self.draw_text_button(col, "ShaderNodeVectorCurve", text="Vector Curves")
            self.draw_text_button(col, "ShaderNodeVectorMath", text="Vector Math")
            self.draw_text_button(col, "ShaderNodeVectorRotate", text="Vector Rotate")
            self.draw_text_button(col, "ShaderNodeCombineXYZ", text="Combine XYZ")
            self.draw_text_button(col, "ShaderNodeMix", text="Mix Vector", settings={"data_type": "'VECTOR'"})
            self.draw_text_button(col, "ShaderNodeSeparateXYZ", text="Separate XYZ")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeVectorCurve")
            self.draw_icon_button(flow, "ShaderNodeVectorMath")
            self.draw_icon_button(flow, "ShaderNodeVectorRotate")
            self.draw_icon_button(flow, "ShaderNodeCombineXYZ")
            self.draw_icon_button(flow, "ShaderNodeMix", settings={"data_type": "'VECTOR'"})
            self.draw_icon_button(flow, "ShaderNodeSeparateXYZ")


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
            self.draw_text_button(col, "GeometryNodeAccumulateField", text="Accumulate Field")
            self.draw_text_button(col, "GeometryNodeFieldAtIndex", text="Evaluate at Index")
            self.draw_text_button(col, "GeometryNodeFieldOnDomain", text="Evaluate On Domain")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeAccumulateField")
            self.draw_icon_button(flow, "GeometryNodeFieldAtIndex")
            self.draw_icon_button(flow, "GeometryNodeFieldOnDomain")


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
            self.draw_text_button(col, "FunctionNodeBooleanMath", text="Boolean Math")
            self.draw_text_button(col, "FunctionNodeIntegerMath", text="Integer Math")
            self.draw_text_button(col, "ShaderNodeClamp", text="Clamp")
            self.draw_text_button(col, "FunctionNodeCompare", text="Compare")
            self.draw_text_button(col, "ShaderNodeFloatCurve", text="Float Curve")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "FunctionNodeFloatToInt", text="Float to Integer")
            self.draw_text_button(col, "FunctionNodeHashValue", text="Hash Value")
            self.draw_text_button(col, "ShaderNodeMapRange", text="Map Range")
            self.draw_text_button(col, "ShaderNodeMath", text="Math")
            self.draw_text_button(col, "ShaderNodeMix", text="Mix")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "FunctionNodeBooleanMath")
            self.draw_icon_button(flow, "FunctionNodeIntegerMath")
            self.draw_icon_button(flow, "ShaderNodeClamp")
            self.draw_icon_button(flow, "FunctionNodeCompare")
            self.draw_icon_button(flow, "ShaderNodeFloatCurve")
            self.draw_icon_button(flow, "FunctionNodeFloatToInt")
            self.draw_icon_button(flow, "FunctionNodeHashValue")
            self.draw_icon_button(flow, "ShaderNodeMapRange")
            self.draw_icon_button(flow, "ShaderNodeMath")
            self.draw_icon_button(flow, "ShaderNodeMix")


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
            self.draw_text_button(col, "FunctionNodeCombineMatrix", text="Combine Matrix")
            self.draw_text_button(col, "FunctionNodeCombineTransform", text="Combine Transform")
            self.draw_text_button(col, "FunctionNodeMatrixDeterminant", text="Matrix Determinant")
            self.draw_text_button(col, "FunctionNodeInvertMatrix", text="Invert Matrix")
            self.draw_text_button(col, "FunctionNodeMatrixMultiply", text="Multiply Matrix")
            self.draw_text_button(col, "FunctionNodeProjectPoint", text="Project Point")
            self.draw_text_button(col, "FunctionNodeSeparateMatrix", text="Separate Matrix")
            self.draw_text_button(col, "FunctionNodeSeparateTransform", text="Separate Transform")
            self.draw_text_button(col, "FunctionNodeTransformDirection", text="Transform Direction")
            self.draw_text_button(col, "FunctionNodeTransformPoint", text="Transform Point")
            self.draw_text_button(col, "FunctionNodeTransposeMatrix", text="Transpose Matrix")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "FunctionNodeCombineMatrix")
            self.draw_icon_button(flow, "FunctionNodeCombineTransform")
            self.draw_icon_button(flow, "FunctionNodeMatrixDeterminant")
            self.draw_icon_button(flow, "FunctionNodeInvertMatrix")
            self.draw_icon_button(flow, "FunctionNodeMatrixMultiply")
            self.draw_icon_button(flow, "FunctionNodeProjectPoint")
            self.draw_icon_button(flow, "FunctionNodeSeparateMatrix")
            self.draw_icon_button(flow, "FunctionNodeSeparateTransform")
            self.draw_icon_button(flow, "FunctionNodeTransformDirection")
            self.draw_icon_button(flow, "FunctionNodeTransformPoint")
            self.draw_icon_button(flow, "FunctionNodeTransposeMatrix")


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
            self.draw_text_button(col, "FunctionNodeAlignRotationToVector", text="Align Rotation to Vector")
            self.draw_text_button(col, "FunctionNodeAxesToRotation", text="Axes to Rotation")
            self.draw_text_button(col, "FunctionNodeAxisAngleToRotation", text="Axis Angle to Rotation")
            self.draw_text_button(col, "FunctionNodeEulerToRotation", text="Euler to Rotation")
            self.draw_text_button(col, "FunctionNodeInvertRotation", text="Invert Rotation")
            self.draw_text_button(col, "FunctionNodeRotateRotation", text="Rotate Rotation")
            self.draw_text_button(col, "FunctionNodeRotateVector", text="Rotate Vector")
            self.draw_text_button(col, "FunctionNodeRotationToAxisAngle", text="Rotation to Axis Angle")
            self.draw_text_button(col, "FunctionNodeRotationToEuler", text="Rotation to Euler")
            self.draw_text_button(col, "FunctionNodeRotationToQuaternion", text="Rotation to Quaternion")
            self.draw_text_button(col, "FunctionNodeQuaternionToRotation", text="Quaternion to Rotation")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "FunctionNodeAlignRotationToVector")
            self.draw_icon_button(flow, "FunctionNodeAxesToRotation")
            self.draw_icon_button(flow, "FunctionNodeAxisAngleToRotation")
            self.draw_icon_button(flow, "FunctionNodeEulerToRotation")
            self.draw_icon_button(flow, "FunctionNodeInvertRotation")
            self.draw_icon_button(flow, "FunctionNodeRotateRotation")
            self.draw_icon_button(flow, "FunctionNodeRotateVector")
            self.draw_icon_button(flow, "FunctionNodeRotationToAxisAngle")
            self.draw_icon_button(flow, "FunctionNodeRotationToEuler")
            self.draw_icon_button(flow, "FunctionNodeRotationToQuaternion")
            self.draw_icon_button(flow, "FunctionNodeQuaternionToRotation")


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
            self.draw_text_button(col, "FunctionNodeAlignEulerToVector", text="Align Euler to Vector")
            self.draw_text_button(col, "FunctionNodeRotateEuler", text=" Rotate Euler (Depreacated)        ")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "FunctionNodeAlignEulerToVector")
            self.draw_icon_button(flow, "FunctionNodeRotateEuler")


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
            self.draw_text_button(col, "ShaderNodeFresnel", text="Fresnel")
            self.draw_text_button(col, "ShaderNodeNewGeometry", text="Geometry")
            self.draw_text_button(col, "ShaderNodeRGB", text="RGB")
            self.draw_text_button(col, "ShaderNodeTexCoord", text="Texture Coordinate")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeFresnel")
            self.draw_icon_button(flow, "ShaderNodeNewGeometry")
            self.draw_icon_button(flow, "ShaderNodeRGB")
            self.draw_icon_button(flow, "ShaderNodeTexCoord")


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
                self.draw_text_button(col, "ShaderNodeOutputMaterial", text="Material Output")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_text_button(col, "ShaderNodeOutputWorld", text="World Output")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_text_button(col, "ShaderNodeOutputLineStyle", text="Line Style Output")

        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.shader_type == 'OBJECT':
                self.draw_icon_button(flow, "ShaderNodeOutputMaterial")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_icon_button(flow, "ShaderNodeOutputWorld")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_icon_button(flow, "ShaderNodeOutputLineStyle")


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
            self.draw_text_button(col, "ShaderNodeAddShader", text="Add")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfHairPrincipled", text="Hair BSDF")
                self.draw_text_button(col, "ShaderNodeMixShader", text="Mix Shader")
                self.draw_text_button(col, "ShaderNodeBsdfPrincipled", text="Principled BSDF")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text="Principled Volume")

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfToon", text="Toon BSDF")

                col = layout.column(align=True)
                col.scale_y = 1.5

                self.draw_text_button(col, "ShaderNodeVolumeAbsorption", text="Volume Absorption")
                self.draw_text_button(col, "ShaderNodeVolumeScatter", text="Volume Scatter")

            if context.space_data.shader_type == 'WORLD':
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBackground", text="Background")
                self.draw_text_button(col, "ShaderNodeEmission", text="Emission")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text="Principled Volume")
                self.draw_text_button(col, "ShaderNodeMixShader", text="Mix")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_icon_button(flow, "ShaderNodeAddShader")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeBsdfHairPrincipled")
                self.draw_icon_button(flow, "ShaderNodeMixShader")
                self.draw_icon_button(flow, "ShaderNodeBsdfPrincipled")
                self.draw_icon_button(flow, "ShaderNodeVolumePrincipled")

                if engine == 'CYCLES':
                    self.draw_icon_button(flow, "ShaderNodeBsdfToon")
                self.draw_icon_button(flow, "ShaderNodeVolumeAbsorption")
                self.draw_icon_button(flow, "ShaderNodeVolumeScatter")

            if context.space_data.shader_type == 'WORLD':
                self.draw_icon_button(flow, "ShaderNodeBackground")
                self.draw_icon_button(flow, "ShaderNodeEmission")
                self.draw_icon_button(flow, "ShaderNodeVolumePrincipled")
                self.draw_icon_button(flow, "ShaderNodeMixShader")


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
            self.draw_text_button(col, "ShaderNodeTexEnvironment", text="Environment Texture")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage", text="Image Texture")
            self.draw_text_button(col, "ShaderNodeTexNoise", text="Noise Texture")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexSky", text="Sky Texture")
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text="Voronoi Texture")


        #### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeTexEnvironment")
            self.draw_icon_button(flow, "ShaderNodeTexImage")
            self.draw_icon_button(flow, "ShaderNodeTexNoise")
            self.draw_icon_button(flow, "ShaderNodeTexSky")
            self.draw_icon_button(flow, "ShaderNodeTexVoronoi")


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
            self.draw_text_button(col, "ShaderNodeBrightContrast", text=" Bright / Contrast")
            self.draw_text_button(col, "ShaderNodeGamma", text="Gamma")
            self.draw_text_button(col, "ShaderNodeHueSaturation", text=" Hue / Saturation")
            self.draw_text_button(col, "ShaderNodeInvert", text="Invert")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMixRGB", text="Mix RGB")
            self.draw_text_button(col, "ShaderNodeRGBCurve", text=" RGB Curves")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeBrightContrast")
            self.draw_icon_button(flow, "ShaderNodeGamma")
            self.draw_icon_button(flow, "ShaderNodeHueSaturation")
            self.draw_icon_button(flow, "ShaderNodeInvert")
            self.draw_icon_button(flow, "ShaderNodeMixRGB")
            self.draw_icon_button(flow, "ShaderNodeRGBCurve")


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
            self.draw_text_button(col, "ShaderNodeMapping", text="Mapping")
            self.draw_text_button(col, "ShaderNodeNormal", text="Normal")
            self.draw_text_button(col, "ShaderNodeNormalMap", text="Normal Map")

        ##### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeMapping")
            self.draw_icon_button(flow, "ShaderNodeNormal")
            self.draw_icon_button(flow, "ShaderNodeNormalMap")


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
            self.draw_text_button(col, "ShaderNodeClamp", text="Clamp")
            self.draw_text_button(col, "ShaderNodeValToRGB", text="ColorRamp")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeFloatCurve", text="Float Curve")
            self.draw_text_button(col, "ShaderNodeMapRange", text="Map Range")
            self.draw_text_button(col, "ShaderNodeMath", text="Math")
            self.draw_text_button(col, "ShaderNodeRGBToBW", text="RGB to BW")

        ##### Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeClamp")
            self.draw_icon_button(flow, "ShaderNodeValToRGB")
            self.draw_icon_button(flow, "ShaderNodeFloatCurve")
            self.draw_icon_button(flow, "ShaderNodeMapRange")
            self.draw_icon_button(flow, "ShaderNodeMath")
            self.draw_icon_button(flow, "ShaderNodeRGBToBW")


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
            self.draw_text_button(col, "ShaderNodeScript", text="Script")

        ##### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeScript")


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

