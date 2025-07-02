# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy import context

#Add tab, Node Group panel
from nodeitems_builtins import node_tree_group_type


class NodePanel:
    @staticmethod
    def draw_text_button(layout, node=None, operator="node.add_node", text="", icon='NONE', settings=None):
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
            self.draw_text_button(col, "ShaderNodeAmbientOcclusion", text=" Ambient Occlusion  ", icon="NODE_AMBIENT_OCCLUSION")
            self.draw_text_button(col, "ShaderNodeAttribute", text=" Attribute          ", icon="NODE_ATTRIBUTE")
            self.draw_text_button(col, "ShaderNodeBevel", text=" Bevel               ", icon="BEVEL")
            self.draw_text_button(col, "ShaderNodeCameraData", text=" Camera Data   ", icon="CAMERA_DATA")
            self.draw_text_button(col, "ShaderNodeVertexColor", text=" Color Attribute ", icon="NODE_VERTEX_COLOR")
            self.draw_text_button(col, "ShaderNodeFresnel", text=" Fresnel              ", icon="NODE_FRESNEL")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeNewGeometry", text=" Geometry        ", icon="NODE_GEOMETRY")
            self.draw_text_button(col, "ShaderNodeHairInfo", text=" Curves Info       ", icon="NODE_HAIRINFO")
            self.draw_text_button(col, "ShaderNodeLayerWeight", text=" Layer Weight   ", icon="NODE_LAYERWEIGHT")
            self.draw_text_button(col, "ShaderNodeLightPath", text=" Light Path        ", icon="NODE_LIGHTPATH")
            self.draw_text_button(col, "ShaderNodeObjectInfo", text=" Object Info       ", icon="NODE_OBJECTINFO")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeParticleInfo", text=" Particle Info     ", icon="NODE_PARTICLEINFO")
            self.draw_text_button(col, "ShaderNodePointInfo", text=" Point Info         ", icon="POINT_INFO")
            self.draw_text_button(col, "ShaderNodeRGB", text=" RGB                 ", icon="NODE_RGB")
            self.draw_text_button(col, "ShaderNodeTangent", text=" Tangent             ", icon="NODE_TANGENT")
            self.draw_text_button(col, "ShaderNodeTexCoord", text=" Texture Coordinate", icon="NODE_TEXCOORDINATE")

            if context.space_data.shader_type == 'LINESTYLE':
                self.draw_text_button(col, "ShaderNodeUVALongStroke", text=" UV along stroke", icon="NODE_UVALONGSTROKE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeUVMap", text=" UV Map            ", icon="GROUP_UVS")
            self.draw_text_button(col, "ShaderNodeValue", text=" Value                ", icon="NODE_VALUE")
            self.draw_text_button(col, "ShaderNodeVolumeInfo", text=" Volume Info    ", icon="NODE_VOLUME_INFO")
            self.draw_text_button(col, "ShaderNodeWireframe", text=" Wireframe        ", icon="NODE_WIREFRAME")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_AMBIENT_OCCLUSION")
            props.use_transform = True
            props.type = "ShaderNodeAmbientOcclusion"

            props = flow.operator("node.add_node", text = "", icon = "NODE_ATTRIBUTE")
            props.use_transform = True
            props.type = "ShaderNodeAttribute"

            props = flow.operator("node.add_node", text="", icon = "BEVEL")
            props.use_transform = True
            props.type = "ShaderNodeBevel"

            props = flow.operator("node.add_node", text="", icon = "CAMERA_DATA")
            props.use_transform = True
            props.type = "ShaderNodeCameraData"

            props = flow.operator("node.add_node", text="", icon = "NODE_VERTEX_COLOR")
            props.use_transform = True
            props.type = "ShaderNodeVertexColor"

            props = flow.operator("node.add_node", text = "", icon = "NODE_FRESNEL")
            props.use_transform = True
            props.type = "ShaderNodeFresnel"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GEOMETRY")
            props.use_transform = True
            props.type = "ShaderNodeNewGeometry"

            props = flow.operator("node.add_node", text = "", icon = "NODE_HAIRINFO")
            props.use_transform = True
            props.type = "ShaderNodeHairInfo"

            props = flow.operator("node.add_node", text = "", icon = "NODE_LAYERWEIGHT")
            props.use_transform = True
            props.type = "ShaderNodeLayerWeight"

            props = flow.operator("node.add_node", text = "", icon = "NODE_LIGHTPATH")
            props.use_transform = True
            props.type = "ShaderNodeLightPath"

            props = flow.operator("node.add_node", text = "", icon = "NODE_OBJECTINFO")
            props.use_transform = True
            props.type = "ShaderNodeObjectInfo"

            props = flow.operator("node.add_node", text = "", icon = "NODE_PARTICLEINFO")
            props.use_transform = True
            props.type = "ShaderNodeParticleInfo"

            props = flow.operator("node.add_node", text = "", icon = "POINT_INFO")
            props.use_transform = True
            props.type = "ShaderNodePointInfo"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "ShaderNodeRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TANGENT")
            props.use_transform = True
            props.type = "ShaderNodeTangent"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TEXCOORDINATE")
            props.use_transform = True
            props.type = "ShaderNodeTexCoord"

            if context.space_data.shader_type == 'LINESTYLE':

                props = flow.operator("node.add_node", text = "", icon = "NODE_UVALONGSTROKE")
                props.use_transform = True
                props.type = "ShaderNodeUVALongStroke"

            props = flow.operator("node.add_node", text = "", icon = "GROUP_UVS")
            props.use_transform = True
            props.type = "ShaderNodeUVMap"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "ShaderNodeValue"

            props = flow.operator("node.add_node", text="", icon = "NODE_VOLUME_INFO")
            props.use_transform = True
            props.type = "ShaderNodeVolumeInfo"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WIREFRAME")
            props.use_transform = True
            props.type = "ShaderNodeWireframe"


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
            self.draw_text_button(col, "ShaderNodeOutputAOV", text=" AOV Output    ", icon="NODE_VALUE")

            if context.space_data.shader_type == 'OBJECT':
                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeOutputLight", text=" Light Output    ", icon="LIGHT")
                self.draw_text_button(col, "ShaderNodeOutputMaterial", text=" Material Output", icon="NODE_MATERIAL")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_text_button(col, "ShaderNodeOutputWorld", text=" World Output    ", icon="WORLD")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_text_button(col, "ShaderNodeOutputLineStyle", text=" Line Style Output", icon="NODE_LINESTYLE_OUTPUT")

        #### Image Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "ShaderNodeOutputAOV"

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text="", icon = "LIGHT")
                    props.use_transform = True
                    props.type = "ShaderNodeOutputLight"

                props = flow.operator("node.add_node", text="", icon = "NODE_MATERIAL")
                props.use_transform = True
                props.type = "ShaderNodeOutputMaterial"

            elif context.space_data.shader_type == 'WORLD':

                props = flow.operator("node.add_node", text="", icon = "WORLD")
                props.use_transform = True
                props.type = "ShaderNodeOutputWorld"

            elif context.space_data.shader_type == 'LINESTYLE':

                props = flow.operator("node.add_node", text="", icon = "NODE_LINESTYLE_OUTPUT")
                props.use_transform = True
                props.type = "ShaderNodeOutputLineStyle"


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
            self.draw_text_button(col, "CompositorNodeBokehImage", text=" Bokeh Image   ", icon="NODE_BOKEH_IMAGE")
            self.draw_text_button(col, "CompositorNodeImage", text=" Image              ", icon="FILE_IMAGE")
            self.draw_text_button(col, "CompositorNodeMask", text="Mask               ", icon="MOD_MASK")
            self.draw_text_button(col, "CompositorNodeMovieClip", text=" Movie Clip        ", icon="FILE_MOVIE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeTexture", text=" Texture             ", icon="TEXTURE")


        #### Image Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_BOKEH_IMAGE")
            props.use_transform = True
            props.type = "CompositorNodeBokehImage"

            props = flow.operator("node.add_node", text = "", icon = "FILE_IMAGE")
            props.use_transform = True
            props.type = "CompositorNodeImage"

            props = flow.operator("node.add_node", text = "", icon = "MOD_MASK")
            props.use_transform = True
            props.type = "CompositorNodeMask"

            props = flow.operator("node.add_node", text = "", icon = "FILE_MOVIE")
            props.use_transform = True
            props.type = "CompositorNodeMovieClip"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "CompositorNodeRGB"

            props = flow.operator("node.add_node", text = "", icon = "TEXTURE")
            props.use_transform = True
            props.type = "CompositorNodeTexture"



            props = flow.operator("node.add_node", text = "", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "CompositorNodeValue"


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
            self.draw_text_button(col, "CompositorNodeRGB", text=" RGB                ", icon="NODE_RGB")
            self.draw_text_button(col, "CompositorNodeValue", text=" Value               ", icon="NODE_VALUE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "CompositorNodeRGB"

            props = flow.operator("node.add_node", text="", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "CompositorNodeValue"


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
            self.draw_text_button(col, "CompositorNodeRLayers", text="  Render Layers              ", icon="RENDERLAYERS")
            self.draw_text_button(col, "CompositorNodeSceneTime", text="  Scene Time              ", icon="TIME")
            self.draw_text_button(col, "CompositorNodeTime", text="  Time Curve              ", icon="NODE_CURVE_TIME")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "RENDERLAYERS")
            props.use_transform = True
            props.type = "CompositorNodeRLayers"

            props = flow.operator("node.add_node", text = "", icon = "TIME")
            props.use_transform = True
            props.type = "CompositorNodeSceneTime"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CURVE_TIME")
            props.use_transform = True
            props.type = "CompositorNodeTime"


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
            self.draw_text_button(col, "CompositorNodeComposite", text=" Composite      ", icon="NODE_COMPOSITING")
            self.draw_text_button(col, "CompositorNodeViewer", text=" Viewer            ", icon="NODE_VIEWER")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeOutputFile", text=" File Output     ", icon="NODE_FILEOUTPUT")


        #### Image Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_COMPOSITING")
            props.use_transform = True
            props.type = "CompositorNodeComposite"

            props = flow.operator("node.add_node", text = "", icon = "NODE_FILEOUTPUT")
            props.use_transform = True
            props.type = "CompositorNodeOutputFile"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VIEWER")
            props.use_transform = True
            props.type = "CompositorNodeViewer"

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
            self.draw_text_button(col, "CompositorNodePremulKey", text=" Alpha Convert   ", icon="NODE_ALPHACONVERT")
            self.draw_text_button(col, "CompositorNodeValToRGB", text=" Color Ramp      ", icon="NODE_COLORRAMP")
            self.draw_text_button(col, "CompositorNodeConvertColorSpace", text=" Convert Colorspace      ", icon="COLOR_SPACE")
            self.draw_text_button(col, "CompositorNodeSetAlpha", text=" Set Alpha          ", icon="IMAGE_ALPHA")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeInvert", text=" Invert Color       ", icon="NODE_INVERT")
            self.draw_text_button(col, "CompositorNodeRGBToBW", text=" RGB to BW       ", icon="NODE_RGBTOBW")


        #### Image Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5


            props = flow.operator("node.add_node", text = "", icon = "NODE_ALPHACONVERT")
            props.use_transform = True
            props.type = "CompositorNodePremulKey"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "CompositorNodeValToRGB"

            props = flow.operator("node.add_node", text = "", icon = "COLOR_SPACE")
            props.use_transform = True
            props.type = "CompositorNodeConvertColorSpace"

            props = flow.operator("node.add_node", text = "", icon = "IMAGE_ALPHA")
            props.use_transform = True
            props.type = "CompositorNodeSetAlpha"

            props = flow.operator("node.add_node", text = "", icon = "NODE_INVERT")
            props.use_transform = True
            props.type = "CompositorNodeInvert"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBTOBW")
            props.use_transform = True
            props.type = "CompositorNodeRGBToBW"


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
            self.draw_text_button(col, "CompositorNodeBrightContrast", text=" Bright / Contrast", icon="BRIGHTNESS_CONTRAST")
            self.draw_text_button(col, "CompositorNodeColorBalance", text=" Color Balance", icon="NODE_COLORBALANCE")
            self.draw_text_button(col, "CompositorNodeColorCorrection", text=" Color Correction", icon="NODE_COLORCORRECTION")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeExposure", text=" Exposure", icon="EXPOSURE")
            self.draw_text_button(col, "CompositorNodeGamma", text=" Gamma", icon="NODE_GAMMA")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeHueCorrect", text=" Hue Correct", icon="NODE_HUESATURATION")
            self.draw_text_button(col, "CompositorNodeHueSat", text=" Hue/Saturation/Value", icon="NODE_HUESATURATION")
            self.draw_text_button(col, "CompositorNodeCurveRGB", text=" RGB Curves", icon="NODE_RGBCURVE")
            self.draw_text_button(col, "CompositorNodeTonemap", text=" Tonemap", icon="NODE_TONEMAP")



        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "BRIGHTNESS_CONTRAST")
            props.use_transform = True
            props.type = "CompositorNodeBrightContrast"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COLORBALANCE")
            props.use_transform = True
            props.type = "CompositorNodeColorBalance"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COLORCORRECTION")
            props.use_transform = True
            props.type = "CompositorNodeColorCorrection"

            props = flow.operator("node.add_node", text = "", icon = "EXPOSURE")
            props.use_transform = True
            props.type = "CompositorNodeExposure"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GAMMA")
            props.use_transform = True
            props.type = "CompositorNodeGamma"

            props = flow.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")
            props.use_transform = True
            props.type = "CompositorNodeHueCorrect"

            props = flow.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")
            props.use_transform = True
            props.type = "CompositorNodeHueSat"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "CompositorNodeCurveRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TONEMAP")
            props.use_transform = True
            props.type = "CompositorNodeTonemap"


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
            self.draw_text_button(col, "CompositorNodeAlphaOver", text=" Alpha Over", icon="IMAGE_ALPHA")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeCombineColor", text=" Combine Color", icon="COMBINE_COLOR")
            self.draw_text_button(col, "CompositorNodeSeparateColor", text=" Separate Color", icon="SEPARATE_COLOR")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeMixRGB", text=" Mix Color", icon="NODE_MIXRGB")
            self.draw_text_button(col, "CompositorNodeZcombine", text=" Z Combine", icon="NODE_ZCOMBINE")


        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "IMAGE_ALPHA")
            props.use_transform = True
            props.type = "CompositorNodeAlphaOver"

            props = flow.operator("node.add_node", text = "", icon = "COMBINE_COLOR")
            props.use_transform = True
            props.type = "CompositorNodeCombineColor"

            props = flow.operator("node.add_node", text = "", icon = "SEPARATE_COLOR")
            props.use_transform = True
            props.type = "CompositorNodeSeparateColor"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MIXRGB")
            props.use_transform = True
            props.type = "CompositorNodeMixRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_ZCOMBINE")
            props.use_transform = True
            props.type = "CompositorNodeZcombine"


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
            self.draw_text_button(col, "CompositorNodeAntiAliasing", text=" Anti Aliasing     ", icon="ANTIALIASED")
            self.draw_text_button(col, "CompositorNodeDenoise", text=" Denoise           ", icon="NODE_DENOISE")
            self.draw_text_button(col, "CompositorNodeDespeckle", text=" Despeckle         ", icon="NODE_DESPECKLE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDilateErode", text=" Dilate / Erode    ", icon="NODE_ERODE")
            self.draw_text_button(col, "CompositorNodeInpaint", text=" Inpaint              ", icon="NODE_IMPAINT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeFilter", text=" Filter                ", icon="FILTER")
            self.draw_text_button(col, "CompositorNodeGlare", text=" Glare                ", icon="NODE_GLARE")
            self.draw_text_button(col, "CompositorNodeKuwahara", text=" Kuwahara         ", icon="KUWAHARA")
            self.draw_text_button(col, "CompositorNodePixelate", text=" Pixelate            ", icon="NODE_PIXELATED")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodePosterize", text=" Posterize          ", icon="POSTERIZE")
            self.draw_text_button(col, "CompositorNodeSunBeams", text=" Sunbeams        ", icon="NODE_SUNBEAMS")



        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "ANTIALIASED")
            props.use_transform = True
            props.type = "CompositorNodeAntiAliasing"

            props = flow.operator("node.add_node", text = "", icon = "NODE_DENOISE")
            props.use_transform = True
            props.type = "CompositorNodeDenoise"

            props = flow.operator("node.add_node", text = "", icon = "NODE_DESPECKLE")
            props.use_transform = True
            props.type = "CompositorNodeDespeckle"

            props = flow.operator("node.add_node", text = "", icon = "NODE_ERODE")
            props.use_transform = True
            props.type = "CompositorNodeDilateErode"

            props = flow.operator("node.add_node", text = "", icon = "NODE_IMPAINT")
            props.use_transform = True
            props.type = "CompositorNodeInpaint"

            props = flow.operator("node.add_node", text = "", icon = "FILTER")
            props.use_transform = True
            props.type = "CompositorNodeFilter"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GLARE")
            props.use_transform = True
            props.type = "CompositorNodeGlare"

            props = flow.operator("node.add_node", text = "", icon = "KUWAHARA")
            props.use_transform = True
            props.type = "CompositorNodeKuwahara"

            props = flow.operator("node.add_node", text = "", icon = "NODE_PIXELATED")
            props.use_transform = True
            props.type = "CompositorNodePixelate"

            props = flow.operator("node.add_node", text = "", icon = "POSTERIZE")
            props.use_transform = True
            props.type = "CompositorNodePosterize"

            props = flow.operator("node.add_node", text = "", icon = "NODE_SUNBEAMS")
            props.use_transform = True
            props.type = "CompositorNodeSunBeams"


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
            self.draw_text_button(col, "CompositorNodeBilateralblur", text=" Bilateral Blur    ", icon="NODE_BILATERAL_BLUR")
            self.draw_text_button(col, "CompositorNodeBlur", text=" Blur                   ", icon="NODE_BLUR")
            self.draw_text_button(col, "CompositorNodeBokehBlur", text=" Bokeh Blur       ", icon="NODE_BOKEH_BLUR")
            self.draw_text_button(col, "CompositorNodeDefocus", text=" Defocus           ", icon="NODE_DEFOCUS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDBlur", text=" Directional Blur ", icon="NODE_DIRECITONALBLUR")
            self.draw_text_button(col, "CompositorNodeVecBlur", text=" Vector Blur       ", icon="NODE_VECTOR_BLUR")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_BILATERAL_BLUR")
            props.use_transform = True
            props.type = "CompositorNodeBilateralblur"

            props = flow.operator("node.add_node", text = "", icon = "NODE_BLUR")
            props.use_transform = True
            props.type = "CompositorNodeBlur"

            props = flow.operator("node.add_node", text = "", icon = "NODE_BOKEH_BLUR")
            props.use_transform = True
            props.type = "CompositorNodeBokehBlur"

            props = flow.operator("node.add_node", text = "", icon = "NODE_DEFOCUS")
            props.use_transform = True
            props.type = "CompositorNodeDefocus"

            props = flow.operator("node.add_node", text = "", icon = "NODE_DIRECITONALBLUR")
            props.use_transform = True
            props.type = "CompositorNodeDBlur"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTOR_BLUR")
            props.use_transform = True
            props.type = "CompositorNodeVecBlur"


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
            self.draw_text_button(col, "CompositorNodeChannelMatte", text=" Channel Key     ", icon="NODE_CHANNEL")
            self.draw_text_button(col, "CompositorNodeChromaMatte", text=" Chroma Key     ", icon="NODE_CHROMA")
            self.draw_text_button(col, "CompositorNodeColorMatte", text=" Color Key         ", icon="COLOR")
            self.draw_text_button(col, "CompositorNodeColorSpill", text=" Color Spill        ", icon="NODE_SPILL")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDiffMatte", text=" Difference Key ", icon="SELECT_DIFFERENCE")
            self.draw_text_button(col, "CompositorNodeDistanceMatte", text=" Distance Key   ", icon="DRIVER_DISTANCE")
            self.draw_text_button(col, "CompositorNodeKeying", text=" Keying              ", icon="NODE_KEYING")
            self.draw_text_button(col, "CompositorNodeKeyingScreen", text=" Keying Screen  ", icon="NODE_KEYINGSCREEN")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeLumaMatte", text=" Luminance Key ", icon="NODE_LUMINANCE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_CHANNEL")
            props.use_transform = True
            props.type = "CompositorNodeChannelMatte"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CHROMA")
            props.use_transform = True
            props.type = "CompositorNodeChromaMatte"

            props = flow.operator("node.add_node", text = "", icon = "COLOR")
            props.use_transform = True
            props.type = "CompositorNodeColorMatte"

            props = flow.operator("node.add_node", text="", icon = "NODE_SPILL")
            props.use_transform = True
            props.type = "CompositorNodeColorSpill"

            props = flow.operator("node.add_node", text = "", icon = "SELECT_DIFFERENCE")
            props.use_transform = True
            props.type = "CompositorNodeDiffMatte"

            props = flow.operator("node.add_node", text = "", icon = "DRIVER_DISTANCE")
            props.use_transform = True
            props.type = "CompositorNodeDistanceMatte"

            props = flow.operator("node.add_node", text = "", icon = "NODE_KEYING")
            props.use_transform = True
            props.type = "CompositorNodeKeying"

            props = flow.operator("node.add_node", text = "", icon = "NODE_KEYINGSCREEN")
            props.use_transform = True
            props.type = "CompositorNodeKeyingScreen"

            props = flow.operator("node.add_node", text = "", icon = "NODE_LUMINANCE")
            props.use_transform = True
            props.type = "CompositorNodeLumaMatte"


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
            self.draw_text_button(col, "CompositorNodeCryptomatteV2", text=" Cryptomatte    ", icon="CRYPTOMATTE")
            self.draw_text_button(col, "CompositorNodeCryptomatte", text=" Cryptomatte (Legacy)", icon="CRYPTOMATTE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeBoxMask", text=" Box Mask         ", icon="NODE_BOXMASK")
            self.draw_text_button(col, "CompositorNodeEllipseMask", text=" Ellipse Mask     ", icon="NODE_ELLIPSEMASK")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDoubleEdgeMask", text=" Double Edge Mask ", icon="NODE_DOUBLEEDGEMASK")
            self.draw_text_button(col, "CompositorNodeIDMask", text=" ID Mask           ", icon="MOD_MASK")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "CRYPTOMATTE")
            props.use_transform = True
            props.type = "CompositorNodeCryptomatte"

            props = flow.operator("node.add_node", text="", icon = "CRYPTOMATTE")
            props.use_transform = True
            props.type = "CompositorNodeCryptomatteV2"

            props = flow.operator("node.add_node", text = "", icon = "NODE_BOXMASK")
            props.use_transform = True
            props.type = "CompositorNodeBoxMask"

            props = flow.operator("node.add_node", text = "", icon = "NODE_ELLIPSEMASK")
            props.use_transform = True
            props.type = "CompositorNodeEllipseMask"

            props = flow.operator("node.add_node", text="", icon = "NODE_DOUBLEEDGEMASK")
            props.use_transform = True
            props.type = "CompositorNodeDoubleEdgeMask"

            props = flow.operator("node.add_node", text = "", icon = "MOD_MASK")
            props.use_transform = True
            props.type = "CompositorNodeIDMask"


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
            self.draw_text_button(col, "ShaderNodeTexBrick", text=" Brick Texture            ", icon="NODE_BRICK")
            self.draw_text_button(col, "ShaderNodeTexChecker", text=" Checker Texture       ", icon="NODE_CHECKER")
            self.draw_text_button(col, "ShaderNodeTexGabor", text=" Gabor Texture        ", icon="GABOR_NOISE")
            self.draw_text_button(col, "ShaderNodeTexGradient", text=" Gradient Texture      ", icon="NODE_GRADIENT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexMagic", text=" Magic Texture         ", icon="MAGIC_TEX")
            self.draw_text_button(col, "ShaderNodeTexNoise", text=" Noise Texture         ", icon="NOISE_TEX")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture       ", icon="VORONI_TEX")
            self.draw_text_button(col, "ShaderNodeTexWave", text=" Wave Texture          ", icon="NODE_WAVES")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise", text=" White Noise             ", icon="NODE_WHITE_NOISE")


        #### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_BRICK")
            props.use_transform = True
            props.type = "ShaderNodeTexBrick"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"

            props = flow.operator("node.add_node", text="", icon = "GABOR_NOISE")
            props.use_transform = True
            props.type = "ShaderNodeTexGabor"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GRADIENT")
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"

            props = flow.operator("node.add_node", text = "", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"

            props = flow.operator("node.add_node", text = "", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"

            props = flow.operator("node.add_node", text = "", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WAVES")
            props.use_transform = True
            props.type = "ShaderNodeTexWave"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WHITE_NOISE")
            props.use_transform = True
            props.type = "ShaderNodeTexWhiteNoise"


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
            self.draw_text_button(col, "CompositorNodePlaneTrackDeform", text=" Plane Track Deform ", icon="NODE_PLANETRACKDEFORM")
            self.draw_text_button(col, "CompositorNodeStabilize", text=" Stabilize 2D     ", icon="NODE_STABILIZE2D")
            self.draw_text_button(col, "CompositorNodeTrackPos", text=" Track Position  ", icon="NODE_TRACKPOSITION")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_PLANETRACKDEFORM")
            props.use_transform = True
            props.type = "CompositorNodePlaneTrackDeform"

            props = flow.operator("node.add_node", text = "", icon = "NODE_STABILIZE2D")
            props.use_transform = True
            props.type = "CompositorNodeStabilize"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TRACKPOSITION")
            props.use_transform = True
            props.type = "CompositorNodeTrackPos"


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
            self.draw_text_button(col, "CompositorNodeRotate", text=" Rotate", icon="TRANSFORM_ROTATE")
            self.draw_text_button(col, "CompositorNodeScale", text=" Scale", icon="TRANSFORM_SCALE")
            self.draw_text_button(col, "CompositorNodeTransform", text=" Transform", icon="NODE_TRANSFORM")
            self.draw_text_button(col, "CompositorNodeTranslate", text=" Translate", icon="TRANSFORM_MOVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeCornerPin", text=" Corner Pin", icon="NODE_CORNERPIN")
            self.draw_text_button(col, "CompositorNodeCrop", text=" Crop", icon="NODE_CROP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeDisplace", text=" Displace", icon="MOD_DISPLACE")
            self.draw_text_button(col, "CompositorNodeFlip", text=" Flip", icon="FLIP")
            self.draw_text_button(col, "CompositorNodeMapUV", text=" Map UV", icon="GROUP_UVS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeLensdist", text=" Lens Distortion ", icon="NODE_LENSDISTORT")
            self.draw_text_button(col, "CompositorNodeMovieDistortion", text=" Movie Distortion ", icon="NODE_MOVIEDISTORT")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "TRANSFORM_ROTATE")
            props.use_transform = True
            props.type = "CompositorNodeRotate"

            props = flow.operator("node.add_node", text = "", icon = "TRANSFORM_SCALE")
            props.use_transform = True
            props.type = "CompositorNodeScale"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TRANSFORM")
            props.use_transform = True
            props.type = "CompositorNodeTransform"

            props = flow.operator("node.add_node", text = "", icon = "TRANSFORM_MOVE")
            props.use_transform = True
            props.type = "CompositorNodeTranslate"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CORNERPIN")
            props.use_transform = True
            props.type = "CompositorNodeCornerPin"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CROP")
            props.use_transform = True
            props.type = "CompositorNodeCrop"

            props = flow.operator("node.add_node", text = "", icon = "MOD_DISPLACE")
            props.use_transform = True
            props.type = "CompositorNodeDisplace"

            props = flow.operator("node.add_node", text = "", icon = "FLIP")
            props.use_transform = True
            props.type = "CompositorNodeFlip"

            props = flow.operator("node.add_node", text = "", icon = "GROUP_UVS")
            props.use_transform = True
            props.type = "CompositorNodeMapUV"

            props = flow.operator("node.add_node", text = "", icon = "NODE_LENSDISTORT")
            props.use_transform = True
            props.type = "CompositorNodeLensdist"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MOVIEDISTORT")
            props.use_transform = True
            props.type = "CompositorNodeMovieDistortion"


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
            self.draw_text_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_text_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_text_button(col, "ShaderNodeMix", text="Mix              ", icon="NODE_MIX")
            self.draw_text_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_text_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeLevels", text=" Levels             ", icon="LEVELS")
            self.draw_text_button(col, "CompositorNodeNormalize", text=" Normalize        ", icon="NODE_NORMALIZE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeSplit", text=" Split                 ", icon="NODE_VIWERSPLIT")
            self.draw_text_button(col, "CompositorNodeSwitch", text=" Switch              ", icon="SWITCH_DIRECTION")
            self.draw_text_button(col, "CompositorNodeSwitchView", text=" Switch View    ", icon="VIEW_SWITCHACTIVECAM")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "CompositorNodeRelativeToPixel", text=" Relative to Pixel    ", icon="NODE_RELATIVE_TO_PIXEL")


        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_MAP_RANGE")
            props.use_transform = True
            props.type = "CompositorNodeMapRange"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "ShaderNodeMath"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CLAMP")
            props.use_transform = True
            props.type = "ShaderNodeClamp"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MIX")
            props.use_transform = True
            props.type = "ShaderNodeMix"

            props = flow.operator("node.add_node", text = "", icon = "FLOAT_CURVE")
            props.use_transform = True
            props.type = "ShaderNodeFloatCurve"

            props = flow.operator("node.add_node", text = "", icon = "LEVELS")
            props.use_transform = True
            props.type = "CompositorNodeLevels"

            props = flow.operator("node.add_node", text = "", icon = "NODE_NORMALIZE")
            props.use_transform = True
            props.type = "CompositorNodeNormalize"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VIWERSPLIT")
            props.use_transform = True
            props.type = "CompositorNodeSplit"

            props = flow.operator("node.add_node", text="", icon = "SWITCH_DIRECTION")
            props.use_transform = True
            props.type = "CompositorNodeSwitch"

            props = flow.operator("node.add_node", text = "", icon = "VIEW_SWITCHACTIVECAM")
            props.use_transform = True
            props.type = "CompositorNodeSwitchView"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RELATIVE_TO_PIXEL")
            props.use_transform = True
            props.type = "CompositorNodeRelativeToPixel"


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
            self.draw_text_button(col, "ShaderNodeCombineXYZ", text=" Combine XYZ  ", icon="NODE_COMBINEXYZ")
            self.draw_text_button(col, "ShaderNodeSeparateXYZ", text=" Separate XYZ  ", icon="NODE_SEPARATEXYZ")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMix", text=" Mix Vector       ", icon="NODE_MIX", settings={"data_type": "'VECTOR'"})
            self.draw_text_button(col, "ShaderNodeVectorCurve", text=" Vector Curves  ", icon="NODE_VECTOR")

            self.draw_text_button(col, "ShaderNodeVectorMath", text=" Vector Math     ", icon="NODE_VECTORMATH")
            self.draw_text_button(col, "ShaderNodeVectorRotate", text=" Vector Rotate   ", icon="TRANSFORM_ROTATE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "NODE_COMBINEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeCombineXYZ"

            props = flow.operator("node.add_node", text="", icon = "NODE_SEPARATEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeSeparateXYZ"

            props = flow.operator("node.add_node", text="", icon = "NODE_MIX")
            props.use_transform = True
            props.type = "ShaderNodeMix"
            ops = props.settings.add()
            ops.name = "data_type"
            ops.value = "'VECTOR'"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"

            props = flow.operator("node.add_node", text="", icon = "NODE_VECTORMATH")
            props.use_transform = True
            props.type = "ShaderNodeVectorMath"

            props = flow.operator("node.add_node", text="", icon = "TRANSFORM_ROTATE")
            props.use_transform = True
            props.type = "ShaderNodeVectorRotate"


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
            self.draw_text_button(col, "TextureNodeImage", text=" Image               ", icon="FILE_IMAGE")
            self.draw_text_button(col, "TextureNodeTexture", text=" Texture             ", icon="TEXTURE")

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
            self.draw_text_button(col, "TextureNodeTexBlend", text=" Blend                 ", icon="BLEND_TEX")
            self.draw_text_button(col, "TextureNodeTexClouds", text=" Clouds               ", icon="CLOUD_TEX")
            self.draw_text_button(col, "TextureNodeTexDistNoise", text=" Distorted Noise ", icon="NOISE_TEX")
            self.draw_text_button(col, "TextureNodeTexMagic", text=" Magic               ", icon="MAGIC_TEX")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeTexMarble", text=" Marble              ", icon="MARBLE_TEX")
            self.draw_text_button(col, "TextureNodeTexNoise", text=" Noise                 ", icon="NOISE_TEX")
            self.draw_text_button(col, "TextureNodeTexStucci", text=" Stucci                ", icon="STUCCI_TEX")
            self.draw_text_button(col, "TextureNodeTexVoronoi", text=" Voronoi             ", icon="VORONI_TEX")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeTexWood", text=" Wood                ", icon="WOOD_TEX")

        #### Icon Buttons

        else:

            row = layout.row()
            row.alignment = 'LEFT'

            props = row.operator("node.add_node", text="", icon = "BLEND_TEX")
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

            props = row.operator("node.add_node", text="", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexNoise"

            props = row.operator("node.add_node", text="", icon = "STUCCI_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexStucci"

            props = row.operator("node.add_node", text="", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexVoronoi"

            row = layout.row()
            row.alignment = 'LEFT'

            props = row.operator("node.add_node", text="", icon = "WOOD_TEX")
            props.use_transform = True
            props.type = "TextureNodeTexWood"


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
            self.draw_text_button(col, "ShaderNodeAddShader", text=" Add                   ", icon="NODE_ADD_SHADER")
            self.draw_text_button(col, "ShaderNodeBsdfMetallic", text=" Metallic             ", icon="METALLIC")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfAnisotropic", text=" Anisotopic BSDF", icon="NODE_ANISOTOPIC")
                self.draw_text_button(col, "ShaderNodeBsdfDiffuse", text=" Diffuse BSDF    ", icon="NODE_DIFFUSESHADER")
                self.draw_text_button(col, "ShaderNodeEmission", text=" Emission           ", icon="NODE_EMISSION")
                self.draw_text_button(col, "ShaderNodeBsdfGlass", text=" Glass BSDF       ", icon="NODE_GLASSHADER")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBsdfGlossy", text=" Glossy BSDF        ", icon="NODE_GLOSSYSHADER")
                self.draw_text_button(col, "ShaderNodeHoldout", text=" Holdout              ", icon="NODE_HOLDOUTSHADER")
                self.draw_text_button(col, "ShaderNodeMixShader", text=" Mix Shader        ", icon="NODE_MIXSHADER")
                self.draw_text_button(col, "ShaderNodeBsdfPrincipled", text=" Principled BSDF", icon="NODE_PRINCIPLED")

                col = layout.column(align=True)
                col.scale_y = 1.5

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfHairPrincipled", text=" Principled Hair BSDF  ", icon="CURVES")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_text_button(col, "ShaderNodeBsdfRefraction", text=" Refraction BSDF   ", icon="NODE_REFRACTIONSHADER")

                if engine == 'BLENDER_EEVEE':
                    self.draw_text_button(col, "ShaderNodeEeveeSpecular", text=" Specular BSDF     ", icon="NODE_GLOSSYSHADER")
                self.draw_text_button(col, "ShaderNodeSubsurfaceScattering", text=" Subsurface Scattering", icon="NODE_SSS")

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfToon", text=" Toon BSDF           ", icon="NODE_TOONSHADER")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBsdfTranslucent", text=" Translucent BSDF  ", icon="NODE_TRANSLUCENT")
                self.draw_text_button(col, "ShaderNodeBsdfTransparent", text=" Transparent BSDF  ", icon="NODE_TRANSPARENT")

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfSheen", text=" Sheen BSDF            ", icon="NODE_VELVET")
                self.draw_text_button(col, "ShaderNodeVolumeAbsorption", text=" Volume Absorption ", icon="NODE_VOLUMEABSORPTION")
                self.draw_text_button(col, "ShaderNodeVolumeScatter", text=" Volume Scatter   ", icon="NODE_VOLUMESCATTER")

            if context.space_data.shader_type == 'WORLD':
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBackground", text=" Background    ", icon="NODE_BACKGROUNDSHADER")
                self.draw_text_button(col, "ShaderNodeEmission", text=" Emission           ", icon="NODE_EMISSION")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume       ", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_text_button(col, "ShaderNodeMixShader", text=" Mix                   ", icon="NODE_MIXSHADER")


        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5


            props = flow.operator("node.add_node", text="", icon = "NODE_ADD_SHADER")
            props.use_transform = True
            props.type = "ShaderNodeAddShader"

            props = flow.operator("node.add_node", text="", icon = "METALLIC")
            props.use_transform = True
            props.type = "ShaderNodeBsdfMetallic"

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text = "", icon = "NODE_ANISOTOPIC")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfAnisotropic"

                props = flow.operator("node.add_node", text = "", icon = "NODE_DIFFUSESHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfDiffuse"

                props = flow.operator("node.add_node", text = "", icon = "NODE_EMISSION")
                props.use_transform = True
                props.type = "ShaderNodeEmission"

                props = flow.operator("node.add_node", text = "", icon = "NODE_GLASSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfGlass"

                props = flow.operator("node.add_node", text = "", icon = "NODE_GLOSSYSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBsdfGlossy"

                props = flow.operator("node.add_node", text = "", icon = "NODE_HOLDOUTSHADER")
                props.use_transform = True
                props.type = "ShaderNodeHoldout"

                props = flow.operator("node.add_node", text = "", icon = "NODE_MIXSHADER")
                props.use_transform = True
                props.type = "ShaderNodeMixShader"

                props = flow.operator("node.add_node", text="", icon = "NODE_PRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeBsdfPrincipled"

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text="", icon = "CURVES")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfHairPrincipled"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMEPRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeVolumePrincipled"

                if engine == 'BLENDER_EEVEE':

                    props = flow.operator("node.add_node", text="", icon = "NODE_GLOSSYSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeEeveeSpecular"

                props = flow.operator("node.add_node", text = "", icon = "NODE_SSS")
                props.use_transform = True
                props.type = "ShaderNodeSubsurfaceScattering"

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text = "", icon = "NODE_TOONSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfToon"

                props = flow.operator("node.add_node", text = "", icon = "NODE_TRANSLUCENT")
                props.use_transform = True
                props.type = "ShaderNodeBsdfTranslucent"

                props = flow.operator("node.add_node", text = "", icon = "NODE_TRANSPARENT")
                props.use_transform = True
                props.type = "ShaderNodeBsdfTransparent"

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text = "", icon = "NODE_VELVET")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfSheen"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMEABSORPTION")
                props.use_transform = True
                props.type = "ShaderNodeVolumeAbsorption"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMESCATTER")
                props.use_transform = True
                props.type = "ShaderNodeVolumeScatter"

            if context.space_data.shader_type == 'WORLD':

                props = flow.operator("node.add_node", text = "", icon = "NODE_BACKGROUNDSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBackground"

                props = flow.operator("node.add_node", text = "", icon = "NODE_EMISSION")
                props.use_transform = True
                props.type = "ShaderNodeEmission"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMEPRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeVolumePrincipled"

                props = flow.operator("node.add_node", text = "", icon = "NODE_MIXSHADER")
                props.use_transform = True
                props.type = "ShaderNodeMixShader"


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
            self.draw_text_button(col, "ShaderNodeTexBrick", text=" Brick Texture            ", icon="NODE_BRICK")
            self.draw_text_button(col, "ShaderNodeTexChecker", text=" Checker Texture       ", icon="NODE_CHECKER")
            self.draw_text_button(col, "ShaderNodeTexEnvironment", text=" Environment Texture", icon="NODE_ENVIRONMENT")
            self.draw_text_button(col, "ShaderNodeTexGabor", text=" Gabor Texture        ", icon="GABOR_NOISE")
            self.draw_text_button(col, "ShaderNodeTexGradient", text=" Gradient Texture      ", icon="NODE_GRADIENT")
            self.draw_text_button(col, "ShaderNodeTexIES", text=" IES Texture             ", icon="LIGHT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage", text=" Image Texture         ", icon="FILE_IMAGE")
            self.draw_text_button(col, "ShaderNodeTexMagic", text=" Magic Texture         ", icon="MAGIC_TEX")
            self.draw_text_button(col, "ShaderNodeTexNoise", text=" Noise Texture         ", icon="NOISE_TEX")
            self.draw_text_button(col, "ShaderNodeTexSky", text=" Sky Texture             ", icon="NODE_SKY")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture       ", icon="VORONI_TEX")
            self.draw_text_button(col, "ShaderNodeTexWave", text=" Wave Texture          ", icon="NODE_WAVES")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise", text=" White Noise             ", icon="NODE_WHITE_NOISE")


        #### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_BRICK")
            props.use_transform = True
            props.type = "ShaderNodeTexBrick"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"

            props = flow.operator("node.add_node", text = "", icon = "NODE_ENVIRONMENT")
            props.use_transform = True
            props.type = "ShaderNodeTexEnvironment"

            props = flow.operator("node.add_node", text="", icon = "GABOR_NOISE")
            props.use_transform = True
            props.type = "ShaderNodeTexGabor"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GRADIENT")
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"

            props = flow.operator("node.add_node", text="", icon = "LIGHT")
            props.use_transform = True
            props.type = "ShaderNodeTexIES"

            props = flow.operator("node.add_node", text = "", icon = "FILE_IMAGE")
            props.use_transform = True
            props.type = "ShaderNodeTexImage"

            props = flow.operator("node.add_node", text = "", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"

            props = flow.operator("node.add_node", text = "", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"

            props = flow.operator("node.add_node", text = "", icon = "NODE_SKY")
            props.use_transform = True
            props.type = "ShaderNodeTexSky"

            props = flow.operator("node.add_node", text = "", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WAVES")
            props.use_transform = True
            props.type = "ShaderNodeTexWave"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WHITE_NOISE")
            props.use_transform = True
            props.type = "ShaderNodeTexWhiteNoise"


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
            self.draw_text_button(col, "ShaderNodeBrightContrast", text=" Bright / Contrast ", icon="BRIGHTNESS_CONTRAST")
            self.draw_text_button(col, "ShaderNodeGamma", text=" Gamma              ", icon="NODE_GAMMA")
            self.draw_text_button(col, "ShaderNodeHueSaturation", text=" Hue / Saturation ", icon="NODE_HUESATURATION")
            self.draw_text_button(col, "ShaderNodeInvert", text=" Invert Color         ", icon="NODE_INVERT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeLightFalloff", text=" Light Falloff      ", icon="NODE_LIGHTFALLOFF")
            self.draw_text_button(col, "ShaderNodeMix", text=" Mix Color          ", icon="NODE_MIX", settings={"data_type": "'RGBA'"})
            self.draw_text_button(col, "ShaderNodeRGBCurve", text="  RGB Curves        ", icon="NODE_RGBCURVE")

        ##### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "BRIGHTNESS_CONTRAST")
            props.use_transform = True
            props.type = "ShaderNodeBrightContrast"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GAMMA")
            props.use_transform = True
            props.type = "ShaderNodeGamma"

            props = flow.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")
            props.use_transform = True
            props.type = "ShaderNodeHueSaturation"

            props = flow.operator("node.add_node", text = "", icon = "NODE_INVERT")
            props.use_transform = True
            props.type = "ShaderNodeInvert"

            props = flow.operator("node.add_node", text = "", icon = "NODE_LIGHTFALLOFF")
            props.use_transform = True
            props.type = "ShaderNodeLightFalloff"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MIX")
            props.use_transform = True
            props.type = "ShaderNodeMix"
            ops = props.settings.add()
            ops.name = "data_type"
            ops.value = "'RGBA'"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "ShaderNodeRGBCurve"


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
            self.draw_text_button(col, "TextureNodeCoordinates", text=" Coordinates       ", icon="NODE_TEXCOORDINATE")
            self.draw_text_button(col, "TextureNodeCurveTime", text=" Curve Time        ", icon="NODE_CURVE_TIME")

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
            self.draw_text_button(col, "TextureNodeBricks", text=" Bricks               ", icon="NODE_BRICK")
            self.draw_text_button(col, "TextureNodeChecker", text=" Checker            ", icon="NODE_CHECKER")

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
            self.draw_text_button(col, "TextureNodeCurveRGB", text=" RGB Curves       ", icon="NODE_RGBCURVE")
            self.draw_text_button(col, "TextureNodeHueSaturation", text=" Hue / Saturation", icon="NODE_HUESATURATION")
            self.draw_text_button(col, "TextureNodeInvert", text=" Invert Color       ", icon="NODE_INVERT")
            self.draw_text_button(col, "TextureNodeMixRGB", text=" Mix RGB            ", icon="NODE_MIXRGB")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeCompose", text=" Combine RGBA ", icon="NODE_COMBINERGB")
            self.draw_text_button(col, "TextureNodeDecompose", text=" Separate RGBA ", icon="NODE_SEPARATERGB")

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
            self.draw_text_button(col, "TextureNodeOutput", text=" Output               ", icon="NODE_OUTPUT")
            self.draw_text_button(col, "TextureNodeViewer", text=" Viewer              ", icon="NODE_VIEWER")

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
            self.draw_text_button(col, "TextureNodeValToRGB", text=" Color Ramp      ", icon="NODE_COLORRAMP")
            self.draw_text_button(col, "TextureNodeDistance", text=" Distance           ", icon="DRIVER_DISTANCE")
            self.draw_text_button(col, "TextureNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_text_button(col, "TextureNodeRGBToBW", text=" RGB to BW       ", icon="NODE_RGBTOBW")

            col = layout.column(align=True)
            self.draw_text_button(col, "TextureNodeValToNor", text=" Value to Normal ", icon="RECALC_NORMALS")

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
            self.draw_text_button(col, "ShaderNodeBump", text=" Bump               ", icon="NODE_BUMP")
            self.draw_text_button(col, "ShaderNodeDisplacement", text=" Displacement ", icon="MOD_DISPLACE")
            self.draw_text_button(col, "ShaderNodeMapping", text=" Mapping           ", icon="NODE_MAPPING")
            self.draw_text_button(col, "ShaderNodeNormal", text=" Normal            ", icon="RECALC_NORMALS")
            self.draw_text_button(col, "ShaderNodeNormalMap", text=" Normal Map     ", icon="NODE_NORMALMAP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeVectorCurve", text=" Vector Curves   ", icon="NODE_VECTOR")
            self.draw_text_button(col, "ShaderNodeVectorDisplacement", text=" Vector Displacement ", icon="VECTOR_DISPLACE")
            self.draw_text_button(col, "ShaderNodeVectorRotate", text=" Vector Rotate   ", icon="TRANSFORM_ROTATE")
            self.draw_text_button(col, "ShaderNodeVectorTransform", text=" Vector Transform ", icon="NODE_VECTOR_TRANSFORM")

        ##### Icon Buttons

        else:

            ##### --------------------------------- Vector ------------------------------------------- ####

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_BUMP")
            props.use_transform = True
            props.type = "ShaderNodeBump"

            props = flow.operator("node.add_node", text="", icon = "MOD_DISPLACE")
            props.use_transform = True
            props.type = "ShaderNodeDisplacement"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MAPPING")
            props.use_transform = True
            props.type = "ShaderNodeMapping"

            props = flow.operator("node.add_node", text = "", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "ShaderNodeNormal"

            props = flow.operator("node.add_node", text = "", icon = "NODE_NORMALMAP")
            props.use_transform = True
            props.type = "ShaderNodeNormalMap"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"

            props = flow.operator("node.add_node", text="", icon = "VECTOR_DISPLACE")
            props.use_transform = True
            props.type = "ShaderNodeVectorDisplacement"

            props = flow.operator("node.add_node", text="", icon = "TRANSFORM_ROTATE")
            props.use_transform = True
            props.type = "ShaderNodeVectorRotate"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTOR_TRANSFORM")
            props.use_transform = True
            props.type = "ShaderNodeVectorTransform"


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
            self.draw_text_button(col, "ShaderNodeBlackbody", text=" Blackbody        ", icon="NODE_BLACKBODY")
            self.draw_text_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_text_button(col, "ShaderNodeValToRGB", text=" ColorRamp       ", icon="NODE_COLORRAMP")
            self.draw_text_button(col, "ShaderNodeCombineColor", text=" Combine Color ", icon="COMBINE_COLOR")
            self.draw_text_button(col, "ShaderNodeCombineXYZ", text=" Combine XYZ   ", icon="NODE_COMBINEXYZ")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")
            self.draw_text_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_text_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_text_button(col, "ShaderNodeMix", text=" Mix                   ", icon="NODE_MIXSHADER")
            self.draw_text_button(col, "ShaderNodeRGBToBW", text=" RGB to BW      ", icon="NODE_RGBTOBW")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeSeparateColor", text=" Separate Color ", icon="SEPARATE_COLOR")
            self.draw_text_button(col, "ShaderNodeSeparateXYZ", text=" Separate XYZ   ", icon="NODE_SEPARATEXYZ")

            if engine == 'BLENDER_EEVEE_NEXT':
                self.draw_text_button(col, "ShaderNodeShaderToRGB", text=" Shader to RGB   ", icon="NODE_RGB")
            self.draw_text_button(col, "ShaderNodeVectorMath", text=" Vector Math     ", icon="NODE_VECTORMATH")
            self.draw_text_button(col, "ShaderNodeWavelength", text=" Wavelength     ", icon="NODE_WAVELENGTH")

        ##### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon= "NODE_BLACKBODY")
            props.use_transform = True
            props.type = "ShaderNodeBlackbody"

            props = flow.operator("node.add_node", text="", icon = "NODE_CLAMP")
            props.use_transform = True
            props.type = "ShaderNodeClamp"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "ShaderNodeValToRGB"

            props = flow.operator("node.add_node", text = "", icon = "COMBINE_COLOR")
            props.use_transform = True
            props.type = "ShaderNodeCombineColor"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COMBINEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeCombineXYZ"

            props = flow.operator("node.add_node", text = "", icon = "FLOAT_CURVE")
            props.use_transform = True
            props.type = "ShaderNodeFloatCurve"

            props = flow.operator("node.add_node", text="", icon = "NODE_MAP_RANGE")
            props.use_transform = True
            props.type = "ShaderNodeMapRange"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "ShaderNodeMath"

            props = flow.operator("node.add_node", text="", icon = "NODE_MIXSHADER")
            props.use_transform = True
            props.type = "ShaderNodeMix"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBTOBW")
            props.use_transform = True
            props.type = "ShaderNodeRGBToBW"

            props = flow.operator("node.add_node", text = "", icon = "SEPARATE_COLOR")
            props.use_transform = True
            props.type = "ShaderNodeSeparateColor"

            props = flow.operator("node.add_node", text = "", icon = "NODE_SEPARATEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeSeparateXYZ"

            if engine == 'BLENDER_EEVEE':

                props = flow.operator("node.add_node", text="", icon = "NODE_RGB")
                props.use_transform = True
                props.type = "ShaderNodeShaderToRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTORMATH")
            props.use_transform = True
            props.type = "ShaderNodeVectorMath"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WAVELENGTH")
            props.use_transform = True
            props.type = "ShaderNodeWavelength"


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
            self.draw_text_button(col, "TextureNodeAt", text=" At                      ", icon="NODE_AT")
            self.draw_text_button(col, "TextureNodeRotate", text=" Rotate              ", icon="TRANSFORM_ROTATE")
            self.draw_text_button(col, "TextureNodeScale", text=" Scale                ", icon="TRANSFORM_SCALE")
            self.draw_text_button(col, "TextureNodeTranslate", text=" Translate          ", icon="TRANSFORM_MOVE")

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
                self.draw_text_button(col, "NodeGroupInput", text=" Group Input      ", icon="GROUPINPUT")
                self.draw_text_button(col, "NodeGroupOutput", text=" Group Output    ", icon="GROUPOUTPUT")


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
                props = flow.operator("node.add_node", text = "", icon = "GROUPINPUT")
                props.use_transform = True
                props.type = "NodeGroupInput"

                props = flow.operator("node.add_node", text = "", icon = "GROUPOUTPUT")
                props.use_transform = True
                props.type = "NodeGroupOutput"


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
            self.draw_text_button(col, "NodeFrame", text=" Frame               ", icon="NODE_FRAME")
            self.draw_text_button(col, "NodeReroute", text=" Reroute             ", icon="NODE_REROUTE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_FRAME")
            props.use_transform = True
            props.type = "NodeFrame"

            props = flow.operator("node.add_node", text = "", icon = "NODE_REROUTE")
            props.use_transform = True
            props.type = "NodeReroute"



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
            self.draw_text_button(col, "GeometryNodeAttributeStatistic", text=" Attribute Statistics  ", icon="ATTRIBUTE_STATISTIC")
            self.draw_text_button(col, "GeometryNodeAttributeDomainSize", text=" Domain Size            ", icon="DOMAIN_SIZE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeBlurAttribute", text=" Blur Attribute          ", icon="BLUR_ATTRIBUTE")
            self.draw_text_button(col, "GeometryNodeCaptureAttribute", text=" Capture Attribute    ", icon="ATTRIBUTE_CAPTURE")
            self.draw_text_button(col, "GeometryNodeRemoveAttribute", text=" Remove Attribute   ", icon="ATTRIBUTE_REMOVE")
            self.draw_text_button(col, "GeometryNodeStoreNamedAttribute", text=" Store Named Attribute ", icon="ATTRIBUTE_STORE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "ATTRIBUTE_STATISTIC")
            props.use_transform = True
            props.type = "GeometryNodeAttributeStatistic"

            props = flow.operator("node.add_node", text="", icon = "DOMAIN_SIZE")
            props.use_transform = True
            props.type = "GeometryNodeAttributeDomainSize"

            props = flow.operator("node.add_node", text="", icon = "BLUR_ATTRIBUTE")
            props.use_transform = True
            props.type = "GeometryNodeBlurAttribute"

            props = flow.operator("node.add_node", text="", icon = "ATTRIBUTE_CAPTURE")
            props.use_transform = True
            props.type = "GeometryNodeCaptureAttribute"

            props = flow.operator("node.add_node", text="", icon = "ATTRIBUTE_REMOVE")
            props.use_transform = True
            props.type = "GeometryNodeRemoveAttribute"

            props = flow.operator("node.add_node", text="", icon = "ATTRIBUTE_STORE")
            props.use_transform = True
            props.type = "GeometryNodeStoreNamedAttribute"


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
            self.draw_text_button(col, "FunctionNodeInputBool", text=" Boolean                ", icon="INPUT_BOOL")
            self.draw_text_button(col, "GeometryNodeInputCollection", text="Collection           ", icon="OUTLINER_COLLECTION")
            self.draw_text_button(col, "FunctionNodeInputColor", text=" Color                    ", icon="COLOR")
            self.draw_text_button(col, "GeometryNodeInputImage", text=" Image                  ", icon="FILE_IMAGE")
            self.draw_text_button(col, "FunctionNodeInputInt", text=" Integer                 ", icon="INTEGER")
            self.draw_text_button(col, "GeometryNodeInputMaterial", text=" Material               ", icon="NODE_MATERIAL")
            self.draw_text_button(col, "GeometryNodeInputObject", text="Object               ", icon="OBJECT_DATA")
            self.draw_text_button(col, "FunctionNodeInputRotation", text=" Rotation               ", icon="ROTATION")
            self.draw_text_button(col, "FunctionNodeInputString", text=" String                    ", icon="STRING")
            self.draw_text_button(col, "ShaderNodeValue", text=" Value                    ", icon="NODE_VALUE")
            self.draw_text_button(col, "FunctionNodeInputVector", text=" Vector                   ", icon="NODE_VECTOR")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5


            props = flow.operator("node.add_node", text = "", icon = "INPUT_BOOL")
            props.use_transform = True
            props.type = "FunctionNodeInputBool"

            props = flow.operator("node.add_node", text = "", icon = "OUTLINER_COLLECTION")
            props.use_transform = True
            props.type = "GeometryNodeInputCollection"

            props = flow.operator("node.add_node", text = "", icon = "COLOR")
            props.use_transform = True
            props.type = "FunctionNodeInputColor"

            props = flow.operator("node.add_node", text="", icon = "FILE_IMAGE")
            props.use_transform = True
            props.type = "GeometryNodeInputImage"

            props = flow.operator("node.add_node", text = "", icon = "INTEGER")
            props.use_transform = True
            props.type = "FunctionNodeInputInt"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MATERIAL")
            props.use_transform = True
            props.type = "GeometryNodeInputMaterial"

            props = flow.operator("node.add_node", text = "", icon = "OBJECT_DATA")
            props.use_transform = True
            props.type = "GeometryNodeInputObject"

            props = flow.operator("node.add_node", text="", icon = "ROTATION")
            props.use_transform = True
            props.type = "FunctionNodeInputRotation"

            props = flow.operator("node.add_node", text = "", icon = "STRING")
            props.use_transform = True
            props.type = "FunctionNodeInputString"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VALUE")
            props.use_transform = True
            props.type = "ShaderNodeValue"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "FunctionNodeInputVector"


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
            self.draw_text_button(col, "GeometryNodeGizmoDial", text=" Dial Gizmo           ", icon="DIAL_GIZMO")
            self.draw_text_button(col, "GeometryNodeGizmoLinear", text=" Linear Gizmo        ", icon="LINEAR_GIZMO")
            self.draw_text_button(col, "GeometryNodeGizmoTransform", text=" Transform Gizmo ", icon="TRANSFORM_GIZMO")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5


            props = flow.operator("node.add_node", text = "", icon = "DIAL_GIZMO")
            props.use_transform = True
            props.type = "GeometryNodeGizmoDial"

            props = flow.operator("node.add_node", text = "", icon = "LINEAR_GIZMO")
            props.use_transform = True
            props.type = "GeometryNodeGizmoLinear"

            props = flow.operator("node.add_node", text="", icon = "TRANSFORM_GIZMO")
            props.use_transform = True
            props.type = "GeometryNodeGizmoTransform"


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
            self.draw_text_button(col, "GeometryNodeImportOBJ", text=" Import OBJ           ", icon="LOAD_OBJ")
            self.draw_text_button(col, "GeometryNodeImportPLY", text=" Import PLY           ", icon="LOAD_PLY")
            self.draw_text_button(col, "GeometryNodeImportSTL", text=" Import STL           ", icon="LOAD_STL")
            self.draw_text_button(col, "GeometryNodeImportCSV", text=" Import CSV           ", icon="LOAD_CSV")
            self.draw_text_button(col, "GeometryNodeImportText", text=" Import Text           ", icon="FILE_TEXT")
            self.draw_text_button(col, "GeometryNodeImportVDB", text=" Import OpenVDB   ", icon="FILE_VOLUME")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "LOAD_OBJ")
            props.use_transform = True
            props.type = "GeometryNodeImportOBJ"

            props = flow.operator("node.add_node", text = "", icon = "LOAD_PLY")
            props.use_transform = True
            props.type = "GeometryNodeImportPLY"

            props = flow.operator("node.add_node", text = "", icon = "LOAD_STL")
            props.use_transform = True
            props.type = "GeometryNodeImportSTL"

            props = flow.operator("node.add_node", text = "", icon = "LOAD_CSV")
            props.use_transform = True
            props.type = "GeometryNodeImportCSV"

            props = flow.operator("node.add_node", text = "", icon = "FILE_TEXT")
            props.use_transform = True
            props.type = "GeometryNodeImportText"

            props = flow.operator("node.add_node", text = "", icon = "FILE_VOLUME")
            props.use_transform = True
            props.type = "GeometryNodeImportVDB"



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
                self.draw_text_button(col, "GeometryNodeTool3DCursor", text=" Cursor                  ", icon="CURSOR")
            self.draw_text_button(col, "GeometryNodeInputActiveCamera", text=" Active Camera     ", icon="VIEW_SWITCHTOCAM")
            self.draw_text_button(col, "GeometryNodeCameraInfo", text=" Camera Info     ", icon="CAMERA_DATA")
            self.draw_text_button(col, "GeometryNodeCollectionInfo", text=" Collection Info     ", icon="COLLECTION_INFO")
            self.draw_text_button(col, "GeometryNodeImageInfo", text=" Image Info           ", icon="IMAGE_INFO")
            self.draw_text_button(col, "GeometryNodeIsViewport", text=" Is Viewport          ", icon="VIEW")
            self.draw_text_button(col, "GeometryNodeInputNamedLayerSelection", text=" Named Layer Selection  ", icon="NAMED_LAYER_SELECTION")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolMousePosition", text=" Mouse Position    ", icon="MOUSE_POSITION")
            self.draw_text_button(col, "GeometryNodeObjectInfo", text=" Object Info           ", icon="NODE_OBJECTINFO")
            self.draw_text_button(col, "GeometryNodeInputSceneTime", text=" Scene Time          ", icon="TIME")
            self.draw_text_button(col, "GeometryNodeSelfObject", text=" Self Object           ", icon="SELF_OBJECT")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeViewportTransform", text=" Viewport Transform ", icon="VIEWPORT_TRANSFORM")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "CURSOR")
                props.use_transform = True
                props.type = "GeometryNodeTool3DCursor"

            props = flow.operator("node.add_node", text="", icon = "VIEW_SWITCHTOCAM")
            props.use_transform = True
            props.type = "GeometryNodeInputActiveCamera"

            props = flow.operator("node.add_node", text="", icon = "CAMERA_DATA")
            props.use_transform = True
            props.type = "GeometryNodeCameraInfo"

            props = flow.operator("node.add_node", text = "", icon = "COLLECTION_INFO")
            props.use_transform = True
            props.type = "GeometryNodeCollectionInfo"

            props = flow.operator("node.add_node", text="", icon = "IMAGE_INFO")
            props.use_transform = True
            props.type = "GeometryNodeImageInfo"

            props = flow.operator("node.add_node", text = "", icon = "VIEW")
            props.use_transform = True
            props.type = "GeometryNodeIsViewport"

            props = flow.operator("node.add_node", text="", icon = "NAMED_LAYER_SELECTION")
            props.use_transform = True
            props.type = "GeometryNodeInputNamedLayerSelection"

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "MOUSE_POSITION")
                props.use_transform = True
                props.type = "GeometryNodeToolMousePosition"

            props = flow.operator("node.add_node", text = "", icon = "NODE_OBJECTINFO")
            props.use_transform = True
            props.type = "GeometryNodeObjectInfo"

            props = flow.operator("node.add_node", text = "", icon = "TIME")
            props.use_transform = True
            props.type = "GeometryNodeInputSceneTime"

            props = flow.operator("node.add_node", text="", icon = "SELF_OBJECT")
            props.use_transform = True
            props.type = "GeometryNodeSelfObject"

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "VIEWPORT_TRANSFORM")
                props.use_transform = True
                props.type = "GeometryNodeViewportTransform"


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
            self.draw_text_button(col, "GeometryNodeViewer", text=" Viewer   ", icon="NODE_VIEWER")
            self.draw_text_button(col, "GeometryNodeWarning", text=" Warning   ", icon="ERROR")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_VIEWER")
            props.use_transform = True
            props.type = "GeometryNodeViewer"

            props = flow.operator("node.add_node", text="", icon = "ERROR")
            props.use_transform = True
            props.type = "GeometryNodeWarning"


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
            self.draw_text_button(col, "GeometryNodeGeometryToInstance", text=" Geometry to Instance", icon="GEOMETRY_INSTANCE")
            self.draw_text_button(col, "GeometryNodeJoinGeometry", text=" Join Geometry           ", icon="JOIN")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "GEOMETRY_INSTANCE")
            props.use_transform = True
            props.type = "GeometryNodeGeometryToInstance"

            props = flow.operator("node.add_node", text = "", icon = "JOIN")
            props.use_transform = True
            props.type = "GeometryNodeJoinGeometry"


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
            self.draw_text_button(col, "GeometryNodeInputID", text=" ID                               ", icon="GET_ID")
            self.draw_text_button(col, "GeometryNodeInputIndex", text=" Index                          ", icon="INDEX")
            self.draw_text_button(col, "GeometryNodeInputNamedAttribute", text=" Named Attribute       ", icon="NAMED_ATTRIBUTE")
            self.draw_text_button(col, "GeometryNodeInputNormal", text=" Normal                      ", icon="RECALC_NORMALS")
            self.draw_text_button(col, "GeometryNodeInputPosition", text=" Position                     ", icon="POSITION")
            self.draw_text_button(col, "GeometryNodeInputRadius", text=" Radius                       ", icon="RADIUS")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolSelection", text=" Selection                    ", icon="RESTRICT_SELECT_OFF")
                self.draw_text_button(col, "GeometryNodeToolActiveElement", text=" Active Element          ", icon="ACTIVE_ELEMENT")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "GET_ID")
            props.use_transform = True
            props.type = "GeometryNodeInputID"

            props = flow.operator("node.add_node", text = "", icon = "INDEX")
            props.use_transform = True
            props.type = "GeometryNodeInputIndex"

            props = flow.operator("node.add_node", text = "", icon = "NAMED_ATTRIBUTE")
            props.use_transform = True
            props.type = "GeometryNodeInputNamedAttribute"

            props = flow.operator("node.add_node", text = "", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "GeometryNodeInputNormal"

            props = flow.operator("node.add_node", text = "", icon = "POSITION")
            props.use_transform = True
            props.type = "GeometryNodeInputPosition"

            props = flow.operator("node.add_node", text = "", icon = "RADIUS")
            props.use_transform = True
            props.type = "GeometryNodeInputRadius"

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "RESTRICT_SELECT_OFF")
                props.use_transform = True
                props.type = "GeometryNodeToolSelection"

                props = flow.operator("node.add_node", text="", icon = "ACTIVE_ELEMENT")
                props.use_transform = True
                props.type = "GeometryNodeToolActiveElement"



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
            self.draw_text_button(col, "GeometryNodeProximity", text=" Geometry Proximity   ", icon="GEOMETRY_PROXIMITY")
            self.draw_text_button(col, "GeometryNodeIndexOfNearest", text=" Index of Nearest        ", icon="INDEX_OF_NEAREST")
            self.draw_text_button(col, "GeometryNodeRaycast", text=" Raycast                      ", icon="RAYCAST")
            self.draw_text_button(col, "GeometryNodeSampleIndex", text=" Sample Index             ", icon="SAMPLE_INDEX")
            self.draw_text_button(col, "GeometryNodeSampleNearest", text=" Sample Nearest        ", icon="SAMPLE_NEAREST")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "GEOMETRY_PROXIMITY")
            props.use_transform = True
            props.type = "GeometryNodeMergeByDistance"

            props = flow.operator("node.add_node", text="", icon = "INDEX_OF_NEAREST")
            props.use_transform = True
            props.type = "GeometryNodeIndexOfNearest"

            props = flow.operator("node.add_node", text = "", icon = "RAYCAST")
            props.use_transform = True
            props.type = "GeometryNodeRaycast"

            props = flow.operator("node.add_node", text="", icon = "SAMPLE_INDEX")
            props.use_transform = True
            props.type = "GeometryNodeSampleIndex"

            props = flow.operator("node.add_node", text="", icon = "SAMPLE_NEAREST")
            props.use_transform = True
            props.type = "GeometryNodeSampleNearest"


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
            self.draw_text_button(col, "GeometryNodeSetGeometryName", text=" Set Geometry Name  ", icon="GEOMETRY_NAME")
            self.draw_text_button(col, "GeometryNodeSetID", text=" Set ID                          ", icon="SET_ID")
            self.draw_text_button(col, "GeometryNodeSetPosition", text=" Set Postion                 ", icon="SET_POSITION")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolSetSelection", text=" Set Selection                 ", icon="SET_SELECTION")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "GEOMETRY_NAME")
            props.use_transform = True
            props.type = "GeometryNodeSetGeometryName"

            props = flow.operator("node.add_node", text = "", icon = "SET_ID")
            props.use_transform = True
            props.type = "GeometryNodeSetID"

            props = flow.operator("node.add_node", text="", icon = "SET_POSITION")
            props.use_transform = True
            props.type = "GeometryNodeSetPosition"

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "SET_SELECTION")
                props.use_transform = True
                props.type = "GeometryNodeToolSetSelection"


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
            self.draw_text_button(col, "GeometryNodeBake", text=" Bake                            ", icon="BAKE")
            self.draw_text_button(col, "GeometryNodeBoundBox", text=" Bounding Box             ", icon="PIVOT_BOUNDBOX")
            self.draw_text_button(col, "GeometryNodeConvexHull", text=" Convex Hull                ", icon="CONVEXHULL")
            self.draw_text_button(col, "GeometryNodeDeleteGeometry", text=" Delete Geometry       ", icon="DELETE")
            self.draw_text_button(col, "GeometryNodeDuplicateElements", text=" Duplicate Geometry ", icon="DUPLICATE")
            self.draw_text_button(col, "GeometryNodeMergeByDistance", text=" Merge by Distance    ", icon="REMOVE_DOUBLES")
            self.draw_text_button(col, "GeometryNodeSortElements", text=" Sort Elements    ", icon="SORTSIZE")
            self.draw_text_button(col, "GeometryNodeTransform", text=" Transform Geometry  ", icon="NODE_TRANSFORM")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeSeparateComponents", text=" Separate Components", icon="SEPARATE")
            self.draw_text_button(col, "GeometryNodeSeparateGeometry", text=" Separate Geometry   ", icon="SEPARATE_GEOMETRY")
            self.draw_text_button(col, "GeometryNodeSplitToInstances", text=" Split to Instances   ", icon="SPLIT_TO_INSTANCES")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "BAKE")
            props.use_transform = True
            props.type = "GeometryNodeBake"

            props = flow.operator("node.add_node", text = "", icon = "PIVOT_BOUNDBOX")
            props.use_transform = True
            props.type = "GeometryNodeBoundBox"

            props = flow.operator("node.add_node", text = "", icon = "CONVEXHULL")
            props.use_transform = True
            props.type = "GeometryNodeConvexHull"

            props = flow.operator("node.add_node", text = "", icon = "DELETE")
            props.use_transform = True
            props.type = "GeometryNodeDeleteGeometry"

            props = flow.operator("node.add_node", text = "", icon = "DUPLICATE")
            props.use_transform = True
            props.type = "GeometryNodeDuplicateElements"

            props = flow.operator("node.add_node", text = "", icon = "REMOVE_DOUBLES")
            props.use_transform = True
            props.type = "GeometryNodeMergeByDistance"

            props = flow.operator("node.add_node", text="", icon = "SORTSIZE")
            props.use_transform = True
            props.type = "GeometryNodeSortElements"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TRANSFORM")
            props.use_transform = True
            props.type = "GeometryNodeTransform"

            props = flow.operator("node.add_node", text = "", icon = "SEPARATE")
            props.use_transform = True
            props.type = "GeometryNodeSeparateComponents"

            props = flow.operator("node.add_node", text = "", icon = "SEPARATE_GEOMETRY")
            props.use_transform = True
            props.type = "GeometryNodeSeparateGeometry"

            props = flow.operator("node.add_node", text = "", icon = "SPLIT_TO_INSTANCES")
            props.use_transform = True
            props.type = "GeometryNodeSplitToInstances"


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
            self.draw_text_button(col, "GeometryNodeInputCurveHandlePositions", text=" Curve Handle Positions ", icon="CURVE_HANDLE_POSITIONS")
            self.draw_text_button(col, "GeometryNodeCurveLength", text=" Curve Length              ", icon="PARTICLEBRUSH_LENGTH")
            self.draw_text_button(col, "GeometryNodeInputTangent", text=" Curve Tangent           ", icon="CURVE_TANGENT")
            self.draw_text_button(col, "GeometryNodeInputCurveTilt", text=" Curve Tilt                 ", icon="CURVE_TILT")
            self.draw_text_button(col, "GeometryNodeCurveEndpointSelection", text=" Endpoint Selection    ", icon="SELECT_LAST")
            self.draw_text_button(col, "GeometryNodeCurveHandleTypeSelection", text=" Handle Type Selection", icon="SELECT_HANDLETYPE")
            self.draw_text_button(col, "GeometryNodeInputSplineCyclic", text=" Is Spline Cyclic          ", icon="IS_SPLINE_CYCLIC")
            self.draw_text_button(col, "GeometryNodeSplineLength", text=" Spline Length             ", icon="SPLINE_LENGTH")
            self.draw_text_button(col, "GeometryNodeSplineParameter", text=" Spline Parameter      ", icon="CURVE_PARAMETER")
            self.draw_text_button(col, "GeometryNodeInputSplineResolution", text=" Spline Resolution        ", icon="SPLINE_RESOLUTION")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "CURVE_HANDLE_POSITIONS")
            props.use_transform = True
            props.type = "GeometryNodeInputCurveHandlePositions"

            props = flow.operator("node.add_node", text = "", icon = "PARTICLEBRUSH_LENGTH")
            props.use_transform = True
            props.type = "GeometryNodeCurveLength"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_TANGENT")
            props.use_transform = True
            props.type = "GeometryNodeInputTangent"

            props = flow.operator("node.add_node", text="", icon = "CURVE_TILT")
            props.use_transform = True
            props.type = "GeometryNodeInputCurveTilt"

            props = flow.operator("node.add_node", text="", icon = "SELECT_LAST")
            props.use_transform = True
            props.type = "GeometryNodeCurveEndpointSelection"

            props = flow.operator("node.add_node", text="", icon = "SELECT_HANDLETYPE")
            props.use_transform = True
            props.type = "GeometryNodeCurveHandleTypeSelection"

            props = flow.operator("node.add_node", text = "", icon = "IS_SPLINE_CYCLIC")
            props.use_transform = True
            props.type = "GeometryNodeInputSplineCyclic"

            props = flow.operator("node.add_node", text = "", icon = "SPLINE_LENGTH")
            props.use_transform = True
            props.type = "GeometryNodeSplineLength"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_PARAMETER")
            props.use_transform = True
            props.type = "GeometryNodeSplineParameter"

            props = flow.operator("node.add_node", text = "", icon = "SPLINE_RESOLUTION")
            props.use_transform = True
            props.type = "GeometryNodeInputSplineResolution"


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
            self.draw_text_button(col, "GeometryNodeSampleCurve", text=" Sample Curve ", icon="CURVE_SAMPLE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "CURVE_SAMPLE")
            props.use_transform = True
            props.type = "GeometryNodeSampleCurve"




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
            self.draw_text_button(col, "GeometryNodeSetCurveNormal", text=" Set Curve Normal        ", icon="CURVE_NORMAL")
            self.draw_text_button(col, "GeometryNodeSetCurveRadius", text=" Set Curve Radius        ", icon="SET_CURVE_RADIUS")
            self.draw_text_button(col, "GeometryNodeSetCurveTilt", text=" Set Curve Tilt             ", icon="SET_CURVE_TILT")
            self.draw_text_button(col, "GeometryNodeSetCurveHandlePositions", text=" Set Handle Positions   ", icon="SET_CURVE_HANDLE_POSITIONS")
            self.draw_text_button(col, "GeometryNodeCurveSetHandles", text=" Set Handle Type         ", icon="HANDLE_AUTO")
            self.draw_text_button(col, "GeometryNodeSetSplineCyclic", text=" Set Spline Cyclic        ", icon="TOGGLE_CYCLIC")
            self.draw_text_button(col, "GeometryNodeSetSplineResolution", text=" Set Spline Resolution   ", icon="SET_SPLINE_RESOLUTION")
            self.draw_text_button(col, "GeometryNodeCurveSplineType", text=" Set Spline Type            ", icon="SPLINE_TYPE")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "CURVE_NORMAL")
            props.use_transform = True
            props.type = "GeometryNodeSetCurveNormal"

            props = flow.operator("node.add_node", text = "", icon = "SET_CURVE_RADIUS")
            props.use_transform = True
            props.type = "GeometryNodeSetCurveRadius"

            props = flow.operator("node.add_node", text = "", icon = "SET_CURVE_TILT")
            props.use_transform = True
            props.type = "GeometryNodeSetCurveTilt"

            props = flow.operator("node.add_node", text = "", icon = "SET_CURVE_HANDLE_POSITIONS")
            props.use_transform = True
            props.type = "GeometryNodeSetCurveHandlePositions"

            props = flow.operator("node.add_node", text = "", icon = "HANDLE_AUTO")
            props.use_transform = True
            props.type = "GeometryNodeCurveSetHandles"

            props = flow.operator("node.add_node", text = "", icon = "TOGGLE_CYCLIC")
            props.use_transform = True
            props.type = "GeometryNodeSetSplineCyclic"

            props = flow.operator("node.add_node", text = "", icon = "SET_SPLINE_RESOLUTION")
            props.use_transform = True
            props.type = "GeometryNodeSetSplineResolution"

            props = flow.operator("node.add_node", text = "", icon = "SPLINE_TYPE")
            props.use_transform = True
            props.type = "GeometryNodeCurveSplineType"


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
            self.draw_text_button(col, "GeometryNodeCurvesToGreasePencil", text=" Curves to Grease Pencil", icon="OUTLINER_OB_GREASEPENCIL")
            self.draw_text_button(col, "GeometryNodeCurveToMesh", text=" Curve to Mesh            ", icon="OUTLINER_OB_MESH")
            self.draw_text_button(col, "GeometryNodeCurveToPoints", text=" Curve to Points          ", icon="POINTCLOUD_DATA")
            self.draw_text_button(col, "GeometryNodeDeformCurvesOnSurface", text=" Deform Curves on Surface ", icon="DEFORM_CURVES")
            self.draw_text_button(col, "GeometryNodeFillCurve", text=" Fill Curve                   ", icon="CURVE_FILL")
            self.draw_text_button(col, "GeometryNodeFilletCurve", text=" Fillet Curve                ", icon="CURVE_FILLET")
            self.draw_text_button(col, "GeometryNodeGreasePencilToCurves", text=" Grease Pencil to Curves", icon="OUTLINER_OB_CURVES")
            self.draw_text_button(col, "GeometryNodeInterpolateCurves", text=" Interpolate Curve    ", icon="INTERPOLATE_CURVE")
            self.draw_text_button(col, "GeometryNodeInterpolateCurves", text=" Merge Layers            ", icon="MERGE")
            self.draw_text_button(col, "GeometryNodeResampleCurve", text=" Resample Curve        ", icon="CURVE_RESAMPLE")
            self.draw_text_button(col, "GeometryNodeReverseCurve", text=" Reverse Curve           ", icon="SWITCH_DIRECTION")
            self.draw_text_button(col, "GeometryNodeSubdivideCurve", text=" Subdivide Curve       ", icon="SUBDIVIDE_EDGES")
            self.draw_text_button(col, "GeometryNodeTrimCurve", text=" Trim Curve                  ", icon="CURVE_TRIM")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "OUTLINER_OB_GREASEPENCIL")
            props.use_transform = True
            props.type = "GeometryNodeCurvesToGreasePencil"

            props = flow.operator("node.add_node", text = "", icon = "OUTLINER_OB_MESH")
            props.use_transform = True
            props.type = "GeometryNodeCurveToMesh"

            props = flow.operator("node.add_node", text = "", icon = "POINTCLOUD_DATA")
            props.use_transform = True
            props.type = "GeometryNodeCurveToPoints"

            props = flow.operator("node.add_node", text = "", icon = "DEFORM_CURVES")
            props.use_transform = True
            props.type = "GeometryNodeDeformCurvesOnSurface"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_FILL")
            props.use_transform = True
            props.type = "GeometryNodeFillCurve"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_FILLET")
            props.use_transform = True
            props.type = "GeometryNodeFilletCurve"

            props = flow.operator("node.add_node", text="", icon = "OUTLINER_OB_CURVES")
            props.use_transform = True
            props.type = "GeometryNodeGreasePencilToCurves"

            props = flow.operator("node.add_node", text="", icon = "INTERPOLATE_CURVE")
            props.use_transform = True
            props.type = "GeometryNodeInterpolateCurves"

            props = flow.operator("node.add_node", text="", icon = "MERGE")
            props.use_transform = True
            props.type = "GeometryNodeInterpolateCurves"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_RESAMPLE")
            props.use_transform = True
            props.type = "GeometryNodeResampleCurve"

            props = flow.operator("node.add_node", text = "", icon = "SWITCH_DIRECTION")
            props.use_transform = True
            props.type = "GeometryNodeReverseCurve"

            props = flow.operator("node.add_node", text = "", icon = "SUBDIVIDE_EDGES")
            props.use_transform = True
            props.type = "GeometryNodeSubdivideCurve"

            props = flow.operator("node.add_node", text="", icon = "CURVE_TRIM")
            props.use_transform = True
            props.type = "GeometryNodeTrimCurve"


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
            self.draw_text_button(col, "GeometryNodeCurveArc", text=" Arc                        ", icon="CURVE_ARC")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveBezierSegment", text=" Bezier Segment     ", icon="CURVE_BEZCURVE")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveCircle", text=" Curve Circle           ", icon="CURVE_BEZCIRCLE")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveLine", text=" Curve Line             ", icon="CURVE_LINE")
            self.draw_text_button(col, "GeometryNodeCurveSpiral", text=" Curve Spiral           ", icon="CURVE_SPIRAL")
            self.draw_text_button(col, "GeometryNodeCurveQuadraticBezier", text=" Quadratic Bezier    ", icon="CURVE_NCURVE")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveQuadrilateral", text=" Quadrilateral         ", icon="CURVE_QUADRILATERAL")
            self.draw_text_button(col, "GeometryNodeCurveStar", text=" Star                       ", icon="CURVE_STAR")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "CURVE_ARC")
            props.use_transform = True
            props.type = "GeometryNodeCurveArc"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_BEZCURVE")
            props.use_transform = True
            props.type = "GeometryNodeCurvePrimitiveBezierSegment"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_BEZCIRCLE")
            props.use_transform = True
            props.type = "GeometryNodeCurvePrimitiveCircle"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_LINE")
            props.use_transform = True
            props.type = "GeometryNodeCurvePrimitiveLine"

            props = flow.operator("node.add_node", text="", icon = "CURVE_SPIRAL")
            props.use_transform = True
            props.type = "GeometryNodeCurveSpiral"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_NCURVE")
            props.use_transform = True
            props.type = "GeometryNodeCurveQuadraticBezier"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_QUADRILATERAL")
            props.use_transform = True
            props.type = "GeometryNodeCurvePrimitiveQuadrilateral"

            props = flow.operator("node.add_node", text = "", icon = "CURVE_STAR")
            props.use_transform = True
            props.type = "GeometryNodeCurveStar"


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
            self.draw_text_button(col, "GeometryNodeCurveOfPoint", text=" Curve of Point              ", icon="CURVE_OF_POINT")
            self.draw_text_button(col, "GeometryNodeOffsetPointInCurve", text=" Offset Point in Curve   ", icon="OFFSET_POINT_IN_CURVE")
            self.draw_text_button(col, "GeometryNodePointsOfCurve", text=" Points of Curve            ", icon="POINT_OF_CURVE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "CURVE_OF_POINT")
            props.use_transform = True
            props.type = "GeometryNodeCurveOfPoint"

            props = flow.operator("node.add_node", text = "", icon = "OFFSET_POINT_IN_CURVE")
            props.use_transform = True
            props.type = "GeometryNodeOffsetPointInCurve"

            props = flow.operator("node.add_node", text = "", icon = "POINT_OF_CURVE")
            props.use_transform = True
            props.type = "GeometryNodePointsOfCurve"


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
            self.draw_text_button(col, "GeometryNodeInputNamedLayerSelection", text=" Named Layer Selection              ", icon="NAMED_LAYER_SELECTION")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NAMED_LAYER_SELECTION")
            props.use_transform = True
            props.type = "GeometryNodeInputNamedLayerSelection"


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
            self.draw_text_button(col, "GeometryNodeSetGreasePencilColor", text=" Set Grease Pencil Color              ", icon="COLOR")
            self.draw_text_button(col, "GeometryNodeSetGreasePencilDepth", text=" Set Grease Pencil Depth             ", icon="DEPTH")
            self.draw_text_button(col, "GeometryNodeSetGreasePencilSoftness", text=" Set Grease Pencil Softness             ", icon="FALLOFFSTROKE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "COLOR")
            props.use_transform = True
            props.type = "GeometryNodeSetGreasePencilColor"

            props = flow.operator("node.add_node", text = "", icon = "DEPTH")
            props.use_transform = True
            props.type = "GeometryNodeSetGreasePencilDepth"

            props = flow.operator("node.add_node", text = "", icon = "FALLOFFSTROKE")
            props.use_transform = True
            props.type = "GeometryNodeSetGreasePencilSoftness"


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
            self.draw_text_button(col, "GeometryNodeGreasePencilToCurves", text=" Set Grease Pencil to Curves              ", icon="OUTLINER_OB_CURVES")
            self.draw_text_button(col, "GeometryNodeMergeLayers", text=" Merge Layers                  ", icon="MERGE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "OUTLINER_OB_CURVES")
            props.use_transform = True
            props.type = "GeometryNodeGreasePencilToCurves"

            props = flow.operator("node.add_node", text = "", icon = "MERGE")
            props.use_transform = True
            props.type = "GeometryNodeMergeLayers"


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
            self.draw_text_button(col, "GeometryNodeInstanceOnPoints", text=" Instances on Points       ", icon="POINT_INSTANCE")
            self.draw_text_button(col, "GeometryNodeInstancesToPoints", text=" Instances to Points       ", icon="INSTANCES_TO_POINTS")
            self.draw_text_button(col, "GeometryNodeRealizeInstances", text=" Realize Instances         ", icon="MOD_INSTANCE")
            self.draw_text_button(col, "GeometryNodeRotateInstances", text=" Rotate Instances          ", icon="ROTATE_INSTANCE")
            self.draw_text_button(col, "GeometryNodeScaleInstances", text=" Scale Instances            ", icon="SCALE_INSTANCE")
            self.draw_text_button(col, "GeometryNodeTranslateInstances", text=" Translate Instances      ", icon="TRANSLATE_INSTANCE")
            self.draw_text_button(col, "GeometryNodeSetInstanceTransform", text=" Set Instance Transform      ", icon="INSTANCE_TRANSFORM")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeInstanceTransform", text=" Instance Transform     ", icon="INSTANCE_TRANSFORM_GET")
            self.draw_text_button(col, "GeometryNodeInputInstanceRotation", text=" Instance Rotation     ", icon="INSTANCE_ROTATE")
            self.draw_text_button(col, "GeometryNodeInputInstanceScale", text=" Instance Scale      ", icon="INSTANCE_SCALE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "POINT_INSTANCE")
            props.use_transform = True
            props.type = "GeometryNodeInstanceOnPoints"

            props = flow.operator("node.add_node", text = "", icon = "INSTANCES_TO_POINTS")
            props.use_transform = True
            props.type = "GeometryNodeInstancesToPoints"

            props = flow.operator("node.add_node", text = "", icon = "MOD_INSTANCE")
            props.use_transform = True
            props.type = "GeometryNodeRealizeInstances"

            props = flow.operator("node.add_node", text = "", icon = "ROTATE_INSTANCE")
            props.use_transform = True
            props.type = "GeometryNodeRotateInstances"

            props = flow.operator("node.add_node", text = "", icon = "SCALE_INSTANCE")
            props.use_transform = True
            props.type = "GeometryNodeTriangulate"

            props = flow.operator("node.add_node", text = "", icon = "TRANSLATE_INSTANCE")
            props.use_transform = True
            props.type = "GeometryNodeTranslateInstances"

            props = flow.operator("node.add_node", text="", icon = "INSTANCE_TRANSFORM")
            props.use_transform = True
            props.type = "GeometryNodeSetInstanceTransform"

            props = flow.operator("node.add_node", text = "", icon = "INSTANCE_TRANSFORM_GET")
            props.use_transform = True
            props.type = "GeometryNodeInstanceTransform"

            props = flow.operator("node.add_node", text = "", icon = "INSTANCE_ROTATE")
            props.use_transform = True
            props.type = "GeometryNodeInputInstanceRotation"

            props = flow.operator("node.add_node", text = "", icon = "INSTANCE_SCALE")
            props.use_transform = True
            props.type = "GeometryNodeInputInstanceScale"


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
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeAngle", text=" Edge Angle              ", icon="EDGE_ANGLE")
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeNeighbors", text=" Edge Neighbors       ", icon="EDGE_NEIGHBORS")
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeVertices", text=" Edge Vertices          ", icon="EDGE_VERTICES")
            self.draw_text_button(col, "GeometryNodeEdgesToFaceGroups", text=" Edges to Face Groups ", icon="FACEGROUP")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceArea", text=" Face Area                ", icon="FACEREGIONS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshFaceSetBoundaries", text=" Face Group Boundaries ", icon="SELECT_BOUNDARY")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceNeighbors", text=" Face Neighbors        ", icon="FACE_NEIGHBORS")

            if context.space_data.geometry_nodes_type == 'TOOL':
                self.draw_text_button(col, "GeometryNodeToolFaceSet", text=" Face Set        ", icon="FACE_SET")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceIsPlanar", text=" Is Face Planar         ", icon="PLANAR")
            self.draw_text_button(col, "GeometryNodeInputShadeSmooth", text=" Is Face Smooth     ", icon="SHADING_SMOOTH")
            self.draw_text_button(col, "GeometryNodeInputEdgeSmooth", text=" is Edge Smooth      ", icon="SHADING_EDGE_SMOOTH")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeInputMeshIsland", text=" Mesh Island             ", icon="UV_ISLANDSEL")
            self.draw_text_button(col, "GeometryNodeInputShortestEdgePaths", text=" Shortest Edge Path ", icon="SELECT_SHORTESTPATH")
            self.draw_text_button(col, "GeometryNodeInputMeshVertexNeighbors", text=" Vertex Neighbors   ", icon="VERTEX_NEIGHBORS")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "EDGE_ANGLE")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshEdgeAngle"

            props = flow.operator("node.add_node", text="", icon = "EDGE_NEIGHBORS")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshEdgeNeighbors"

            props = flow.operator("node.add_node", text="", icon = "EDGE_VERTICES")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshEdgeVertices"

            props = flow.operator("node.add_node", text="", icon = "FACEGROUP")
            props.use_transform = True
            props.type = "GeometryNodeEdgesToFaceGroups"

            props = flow.operator("node.add_node", text="", icon = "FACEREGIONS")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshFaceArea"

            props = flow.operator("node.add_node", text="", icon = "SELECT_BOUNDARY")
            props.use_transform = True
            props.type = "GeometryNodeMeshFaceSetBoundaries"

            props = flow.operator("node.add_node", text = "", icon = "FACE_NEIGHBORS")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshFaceNeighbors"

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "FACE_SET")
                props.use_transform = True
                props.type = "GeometryNodeToolFaceSet"

            props = flow.operator("node.add_node", text="", icon = "PLANAR")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshFaceIsPlanar"

            props = flow.operator("node.add_node", text = "", icon = "SHADING_SMOOTH")
            props.use_transform = True
            props.type = "GeometryNodeInputShadeSmooth"

            props = flow.operator("node.add_node", text="", icon = "SHADING_EDGE_SMOOTH")
            props.use_transform = True
            props.type = "GeometryNodeInputEdgeSmooth"

            props = flow.operator("node.add_node", text="", icon = "UV_ISLANDSEL")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshIsland"

            props = flow.operator("node.add_node", text = "", icon = "SELECT_SHORTESTPATH")
            props.use_transform = True
            props.type = "GeometryNodeInputShortestEdgePaths"

            props = flow.operator("node.add_node", text = "", icon = "VERTEX_NEIGHBORS")
            props.use_transform = True
            props.type = "GeometryNodeInputMeshVertexNeighbors"


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
            self.draw_text_button(col, "GeometryNodeSampleNearestSurface", text=" Sample Nearest Surface ", icon="SAMPLE_NEAREST_SURFACE")
            self.draw_text_button(col, "GeometryNodeSampleUVSurface", text=" Sample UV Surface   ", icon="SAMPLE_UV_SURFACE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "SAMPLE_NEAREST_SURFACE")
            props.use_transform = True
            props.type = "GeometryNodeSampleNearestSurface"

            props = flow.operator("node.add_node", text="", icon = "SAMPLE_UV_SURFACE")
            props.use_transform = True
            props.type = "GeometryNodeSampleUVSurface"


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
                self.draw_text_button(col, "GeometryNodeToolFaceSet", text=" Set Face Set   ", icon="FACE_SET")
            self.draw_text_button(col, "GeometryNodeSetMeshNormal", text=" Set Mesh Normal   ", icon="SET_SMOOTH")
            self.draw_text_button(col, "GeometryNodeSetShadeSmooth", text=" Set Shade Smooth   ", icon="SET_SHADE_SMOOTH")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.geometry_nodes_type == 'TOOL':
                props = flow.operator("node.add_node", text="", icon = "SET_FACE_SET")
                props.use_transform = True
                props.type = "GeometryNodeToolSetFaceSet"

            props = flow.operator("node.add_node", text = "", icon = "SET_SMOOTH")
            props.use_transform = True
            props.type = "GeometryNodeSetMeshNormal"

            props = flow.operator("node.add_node", text = "", icon = "SET_SHADE_SMOOTH")
            props.use_transform = True
            props.type = "GeometryNodeSetShadeSmooth"


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
            self.draw_text_button(col, "GeometryNodeDualMesh", text=" Dual Mesh               ", icon="DUAL_MESH")
            self.draw_text_button(col, "GeometryNodeEdgePathsToCurves", text=" Edge Paths to Curves ", icon="EDGE_PATHS_TO_CURVES")
            self.draw_text_button(col, "GeometryNodeEdgePathsToSelection", text=" Edge Paths to Selection ", icon="EDGE_PATH_TO_SELECTION")
            self.draw_text_button(col, "GeometryNodeExtrudeMesh", text=" Extrude Mesh             ", icon="EXTRUDE_REGION")
            self.draw_text_button(col, "GeometryNodeFlipFaces", text=" Flip Faces               ", icon="FLIP_NORMALS")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshBoolean", text=" Mesh Boolean           ", icon="MOD_BOOLEAN")
            self.draw_text_button(col, "GeometryNodeMeshToCurve", text=" Mesh to Curve          ", icon="OUTLINER_OB_CURVE")
            self.draw_text_button(col, "GeometryNodeMeshToPoints", text=" Mesh to Points          ", icon="MESH_TO_POINTS")
            self.draw_text_button(col, "GeometryNodeMeshToVolume", text=" Mesh to Volume         ", icon="MESH_TO_VOLUME")
            self.draw_text_button(col, "GeometryNodeScaleElements", text=" Scale Elements        ", icon="TRANSFORM_SCALE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeSplitEdges", text=" Split Edges               ", icon="SPLITEDGE")
            self.draw_text_button(col, "GeometryNodeSubdivideMesh", text=" Subdivide Mesh        ", icon="SUBDIVIDE_MESH")
            self.draw_text_button(col, "GeometryNodeSubdivisionSurface", text=" Subdivision Surface ", icon="SUBDIVIDE_EDGES")
            self.draw_text_button(col, "GeometryNodeTriangulate", text=" Triangulate              ", icon="MOD_TRIANGULATE")


        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "DUAL_MESH")
            props.use_transform = True
            props.type = "GeometryNodeDualMesh"

            props = flow.operator("node.add_node", text="", icon = "EDGE_PATHS_TO_CURVES")
            props.use_transform = True
            props.type = "GeometryNodeEdgePathsToCurves"

            props = flow.operator("node.add_node", text="", icon = "EDGE_PATH_TO_SELECTION")
            props.use_transform = True
            props.type = "GeometryNodeEdgePathsToSelection"

            props = flow.operator("node.add_node", text = "", icon = "EXTRUDE_REGION")
            props.use_transform = True
            props.type = "GeometryNodeExtrudeMesh"

            props = flow.operator("node.add_node", text = "", icon = "FLIP_NORMALS")
            props.use_transform = True
            props.type = "GeometryNodeFlipFaces"

            props = flow.operator("node.add_node", text = "", icon = "MOD_BOOLEAN")
            props.use_transform = True
            props.type = "GeometryNodeMeshBoolean"

            props = flow.operator("node.add_node", text = "", icon = "OUTLINER_OB_CURVE")
            props.use_transform = True
            props.type = "GeometryNodeMeshToCurve"

            props = flow.operator("node.add_node", text = "", icon = "MESH_TO_POINTS")
            props.use_transform = True
            props.type = "GeometryNodeMeshToPoints"

            props = flow.operator("node.add_node", text="", icon = "MESH_TO_VOLUME")
            props.use_transform = True
            props.type = "GeometryNodeMeshToVolume"

            props = flow.operator("node.add_node", text = "", icon = "TRANSFORM_SCALE")
            props.use_transform = True
            props.type = "GeometryNodeScaleElements"

            props = flow.operator("node.add_node", text = "", icon = "SPLITEDGE")
            props.use_transform = True
            props.type = "GeometryNodeSplitEdges"

            props = flow.operator("node.add_node", text = "", icon = "SUBDIVIDE_MESH")
            props.use_transform = True
            props.type = "GeometryNodeSubdivideMesh"

            props = flow.operator("node.add_node", text = "", icon = "SUBDIVIDE_EDGES")
            props.use_transform = True
            props.type = "GeometryNodeSubdivisionSurface"

            props = flow.operator("node.add_node", text = "", icon = "MOD_TRIANGULATE")
            props.use_transform = True
            props.type = "GeometryNodeTriangulate"


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
            self.draw_text_button(col, "GeometryNodeMeshCone", text=" Cone                       ", icon="MESH_CONE")
            self.draw_text_button(col, "GeometryNodeMeshCube", text=" Cube                       ", icon="MESH_CUBE")
            self.draw_text_button(col, "GeometryNodeMeshCylinder", text=" Cylinder                   ", icon="MESH_CYLINDER")
            self.draw_text_button(col, "GeometryNodeMeshGrid", text=" Grid                         ", icon="MESH_GRID")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshIcoSphere", text=" Ico Sphere               ", icon="MESH_ICOSPHERE")
            self.draw_text_button(col, "GeometryNodeMeshCircle", text=" Mesh Circle            ", icon="MESH_CIRCLE")
            self.draw_text_button(col, "GeometryNodeMeshLine", text=" Mesh Line                 ", icon="MESH_LINE")
            self.draw_text_button(col, "GeometryNodeMeshUVSphere", text=" UV Sphere                ", icon="MESH_UVSPHERE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "MESH_CONE")
            props.use_transform = True
            props.type = "GeometryNodeMeshCone"

            props = flow.operator("node.add_node", text = "", icon = "MESH_CUBE")
            props.use_transform = True
            props.type = "GeometryNodeMeshCube"

            props = flow.operator("node.add_node", text = "", icon = "MESH_CYLINDER")
            props.use_transform = True
            props.type = "GeometryNodeMeshCylinder"

            props = flow.operator("node.add_node", text = "", icon = "MESH_GRID")
            props.use_transform = True
            props.type = "GeometryNodeMeshGrid"

            props = flow.operator("node.add_node", text = "", icon = "MESH_ICOSPHERE")
            props.use_transform = True
            props.type = "GeometryNodeMeshIcoSphere"

            props = flow.operator("node.add_node", text = "", icon = "MESH_CIRCLE")
            props.use_transform = True
            props.type = "GeometryNodeMeshCircle"

            props = flow.operator("node.add_node", text = "", icon = "MESH_LINE")
            props.use_transform = True
            props.type = "GeometryNodeMeshLine"

            props = flow.operator("node.add_node", text = "", icon = "MESH_UVSPHERE")
            props.use_transform = True
            props.type = "GeometryNodeMeshUVSphere"


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
            self.draw_text_button(col, "GeometryNodeCornersOfEdge", text=" Corners of Edge          ", icon="CORNERS_OF_EDGE")
            self.draw_text_button(col, "GeometryNodeCornersOfFace", text=" Corners of Face          ", icon="CORNERS_OF_FACE")
            self.draw_text_button(col, "GeometryNodeCornersOfVertex", text=" Corners of Vertex       ", icon="CORNERS_OF_VERTEX")
            self.draw_text_button(col, "GeometryNodeEdgesOfCorner", text=" Edges of Corner          ", icon="EDGES_OF_CORNER")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeEdgesOfVertex", text=" Edges of Vertex          ", icon="EDGES_OF_VERTEX")
            self.draw_text_button(col, "GeometryNodeFaceOfCorner", text=" Face of Corner             ", icon="FACE_OF_CORNER")
            self.draw_text_button(col, "GeometryNodeOffsetCornerInFace", text=" Offset Corner In Face  ", icon="OFFSET_CORNER_IN_FACE")
            self.draw_text_button(col, "GeometryNodeVertexOfCorner", text=" Vertex of Corner          ", icon="VERTEX_OF_CORNER")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "CORNERS_OF_EDGE")
            props.use_transform = True
            props.type = "GeometryNodeCornersOfEdge"

            props = flow.operator("node.add_node", text = "", icon = "CORNERS_OF_FACE")
            props.use_transform = True
            props.type = "GeometryNodeCornersOfFace"

            props = flow.operator("node.add_node", text = "", icon = "CORNERS_OF_VERTEX")
            props.use_transform = True
            props.type = "GeometryNodeCornersOfVertex"

            props = flow.operator("node.add_node", text = "", icon = "EDGES_OF_CORNER")
            props.use_transform = True
            props.type = "GeometryNodeEdgesOfCorner"

            props = flow.operator("node.add_node", text = "", icon = "EDGES_OF_VERTEX")
            props.use_transform = True
            props.type = "GeometryNodeEdgesOfVertex"

            props = flow.operator("node.add_node", text = "", icon = "FACE_OF_CORNER")
            props.use_transform = True
            props.type = "GeometryNodeFaceOfCorner"

            props = flow.operator("node.add_node", text = "", icon = "OFFSET_CORNER_IN_FACE")
            props.use_transform = True
            props.type = "GeometryNodeOffsetCornerInFace"

            props = flow.operator("node.add_node", text = "", icon = "VERTEX_OF_CORNER")
            props.use_transform = True
            props.type = "GeometryNodeVertexOfCorner"


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
            self.draw_text_button(col, "GeometryNodeUVPackIslands", text=" Pack UV Islands  ", icon="PACKISLAND")
            self.draw_text_button(col, "GeometryNodeUVUnwrap", text=" UV Unwrap      ", icon="UNWRAP_ABF")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "VOLUME_CUBE")
            props.use_transform = True
            props.type = "GeometryNodeUVPackIslands"

            props = flow.operator("node.add_node", text="", icon = "VOLUME_TO_MESH")
            props.use_transform = True
            props.type = "GeometryNodeUVUnwrap"


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
            self.draw_text_button(col, "GeometryNodeDistributePointsInVolume", text=" Distribute Points in Volume  ", icon="VOLUME_DISTRIBUTE")
            self.draw_text_button(col, "GeometryNodeDistributePointsOnFaces", text=" Distribute Points on Faces  ", icon="POINT_DISTRIBUTE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodePoints", text=" Points                          ", icon="DECORATE")
            self.draw_text_button(col, "GeometryNodePointsToCurves", text=" Points to Curves          ", icon="POINTS_TO_CURVES")
            self.draw_text_button(col, "GeometryNodePointsToVertices", text=" Points to Vertices         ", icon="POINTS_TO_VERTICES")
            self.draw_text_button(col, "GeometryNodePointsToVolume", text=" Points to Volume         ", icon="POINT_TO_VOLUME")
            self.draw_text_button(col, "GeometryNodeSetPointRadius", text=" Set Point Radius          ", icon="SET_CURVE_RADIUS")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "VOLUME_DISTRIBUTE")
            props.use_transform = True
            props.type = "GeometryNodeDistributePointsInVolume"

            props = flow.operator("node.add_node", text = "", icon = "POINT_DISTRIBUTE")
            props.use_transform = True
            props.type = "GeometryNodeDistributePointsOnFaces"

            props = flow.operator("node.add_node", text="", icon = "DECORATE")
            props.use_transform = True
            props.type = "GeometryNodePoints"

            props = flow.operator("node.add_node", text="", icon = "POINTS_TO_CURVES")
            props.use_transform = True
            props.type = "GeometryNodePointsToCurves"

            props = flow.operator("node.add_node", text = "", icon = "POINTS_TO_VERTICES")
            props.use_transform = True
            props.type = "GeometryNodePointsToVertices"

            props = flow.operator("node.add_node", text = "", icon = "POINT_TO_VOLUME")
            props.use_transform = True
            props.type = "GeometryNodePointsToVolume"

            props = flow.operator("node.add_node", text = "", icon = "SET_CURVE_RADIUS")
            props.use_transform = True
            props.type = "GeometryNodeSetPointRadius"


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
            self.draw_text_button(col, "GeometryNodeVolumeCube", text=" Volume Cube       ", icon="VOLUME_CUBE")
            self.draw_text_button(col, "GeometryNodeVolumeToMesh", text=" Volume to Mesh       ", icon="VOLUME_TO_MESH")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "VOLUME_CUBE")
            props.use_transform = True
            props.type = "GeometryNodeVolumeCube"

            props = flow.operator("node.add_node", text="", icon = "VOLUME_TO_MESH")
            props.use_transform = True
            props.type = "GeometryNodeVolumeToMesh"

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
            self.draw_text_button(col, operator="node.add_simulation_zone", text=" Simulation Zone       ", icon="TIME")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_simulation_zone", text="", icon = "TIME")
            props.use_transform = True
            #props.type = "GeometryNodeVolumeCube"


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
            self.draw_text_button(col, "GeometryNodeReplaceMaterial", text=" Replace Material      ", icon="MATERIAL_REPLACE")
            self.draw_text_button(col, "GeometryNodeInputMaterialIndex", text=" Material Index           ", icon="MATERIAL_INDEX")
            self.draw_text_button(col, "GeometryNodeMaterialSelection", text=" Material Selection    ", icon="SELECT_BY_MATERIAL")
            self.draw_text_button(col, "GeometryNodeSetMaterial", text=" Set Material              ", icon="MATERIAL_ADD")
            self.draw_text_button(col, "GeometryNodeSetMaterialIndex", text=" Set Material Index   ", icon="SET_MATERIAL_INDEX")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "MATERIAL_REPLACE")
            props.use_transform = True
            props.type = "GeometryNodeReplaceMaterial"

            props = flow.operator("node.add_node", text = "", icon = "MATERIAL_INDEX")
            props.use_transform = True
            props.type = "GeometryNodeInputMaterialIndex"

            props = flow.operator("node.add_node", text = "", icon = "SELECT_BY_MATERIAL")
            props.use_transform = True
            props.type = "GeometryNodeMaterialSelection"

            props = flow.operator("node.add_node", text = "", icon = "MATERIAL_ADD")
            props.use_transform = True
            props.type = "GeometryNodeSetMaterial"

            props = flow.operator("node.add_node", text = "", icon = "SET_MATERIAL_INDEX")
            props.use_transform = True
            props.type = "GeometryNodeSetMaterialIndex"


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
            self.draw_text_button(col, "ShaderNodeTexBrick", text=" Brick Texture        ", icon="NODE_BRICK")
            self.draw_text_button(col, "ShaderNodeTexChecker", text=" Checker Texture   ", icon="NODE_CHECKER")
            self.draw_text_button(col, "ShaderNodeTexGradient", text=" Gradient Texture  ", icon="NODE_GRADIENT")
            self.draw_text_button(col, "GeometryNodeImageTexture", text=" Image Texture      ", icon="FILE_IMAGE")
            self.draw_text_button(col, "ShaderNodeTexMagic", text=" Magic Texture       ", icon="MAGIC_TEX")
            self.draw_text_button(col, "ShaderNodeTexNoise", text=" Noise Texture        ", icon="NOISE_TEX")
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture     ", icon="VORONI_TEX")
            self.draw_text_button(col, "ShaderNodeTexWave", text=" Wave Texture         ", icon="NODE_WAVES")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise", text=" White Noise            ", icon="NODE_WHITE_NOISE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_BRICK")
            props.use_transform = True
            props.type = "ShaderNodeTexBrick"

            props = flow.operator("node.add_node", text = "", icon = "NODE_CHECKER")
            props.use_transform = True
            props.type = "ShaderNodeTexChecker"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GRADIENT")
            props.use_transform = True
            props.type = "ShaderNodeTexGradient"

            props = flow.operator("node.add_node", text = "", icon = "FILE_IMAGE")
            props.use_transform = True
            props.type = "GeometryNodeImageTexture"

            props = flow.operator("node.add_node", text = "", icon = "MAGIC_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexMagic"

            props = flow.operator("node.add_node", text = "", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"

            props = flow.operator("node.add_node", text = "", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WAVES")
            props.use_transform = True
            props.type = "ShaderNodeTexWave"

            props = flow.operator("node.add_node", text = "", icon = "NODE_WHITE_NOISE")
            props.use_transform = True
            props.type = "ShaderNodeTexWhiteNoise"


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
            self.draw_text_button(col, operator="node.add_foreach_geometry_element_zone", text=" For Each Element    ", icon="FOR_EACH")
            self.draw_text_button(col, "GeometryNodeIndexSwitch", text=" Index Switch    ", icon="INDEX_SWITCH")
            self.draw_text_button(col, "GeometryNodeMenuSwitch", text=" Menu Switch    ", icon="MENU_SWITCH")
            self.draw_text_button(col, "FunctionNodeRandomValue", text=" Random Value  ", icon="RANDOM_FLOAT")
            self.draw_text_button(col, operator="node.add_repeat_zone", text=" Repeat Zone      ", icon="REPEAT")
            self.draw_text_button(col, "GeometryNodeSwitch", text=" Switch               ", icon="SWITCH")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "INDEX_SWITCH")
            props.use_transform = True
            props.type = "GeometryNodeIndexSwitch"

            props = flow.operator("node.add_node", text = "", icon = "MENU_SWITCH")
            props.use_transform = True
            props.type = "GeometryNodeMenuSwitch"

            props = flow.operator("node.add_node", text = "", icon = "RANDOM_FLOAT")
            props.use_transform = True
            props.type = "FunctionNodeRandomValue"

            props = flow.operator("node.add_repeat_zone", text="", icon = "REPEAT")
            props.use_transform = True
            #props.type = ""

            props = flow.operator("node.add_node", text = "", icon = "SWITCH")
            props.use_transform = True
            props.type = "GeometryNodeSwitch"




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
            self.draw_text_button(col, "ShaderNodeValToRGB", text=" ColorRamp           ", icon="NODE_COLORRAMP")
            self.draw_text_button(col, "ShaderNodeRGBCurve", text=" RGB Curves          ", icon="NODE_RGBCURVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "FunctionNodeCombineColor", text=" Combine Color      ", icon="COMBINE_COLOR")
            self.draw_text_button(col, "FunctionNodeSeparateColor", text=" Separate Color      ", icon="SEPARATE_COLOR")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "ShaderNodeValToRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "ShaderNodeRGBCurve"

            props = flow.operator("node.add_node", text = "", icon = "COMBINE_COLOR")
            props.use_transform = True
            props.type = "FunctionNodeCombineColor"

            props = flow.operator("node.add_node", text="", icon = "NODE_MIX")
            props.use_transform = True
            props.type = "ShaderNodeMix"
            ops = props.settings.add()
            ops.name = "data_type"
            ops.value = "'RGBA'"
            #props.settings = [{"name":"data_type", "value":"'RGBA'"}] # halp :(

            props = flow.operator("node.add_node", text = "", icon = "SEPARATE_COLOR")
            props.use_transform = True
            props.type = "FunctionNodeSeparateColor"


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
            self.draw_text_button(col, "FunctionNodeFormatString", text=" Format String            ", icon="FORMAT_STRING")
            self.draw_text_button(col, "GeometryNodeStringJoin", text=" Join Strings             ", icon="STRING_JOIN")
            self.draw_text_button(col, "FunctionNodeMatchString", text=" Match String            ", icon="MATCH_STRING")
            self.draw_text_button(col, "FunctionNodeReplaceString", text=" Replace Strings       ", icon="REPLACE_STRING")
            self.draw_text_button(col, "FunctionNodeSliceString", text=" Slice Strings            ", icon="STRING_SUBSTRING")
            self.draw_text_button(col, "FunctionNodeStringLength", text=" String Length           ", icon="STRING_LENGTH")
            self.draw_text_button(col, "FunctionNodeFindInString", text=" Find in String           ", icon="STRING_FIND")
            self.draw_text_button(col, "GeometryNodeStringToCurves", text=" String to Curves       ", icon="STRING_TO_CURVE")
            self.draw_text_button(col, "FunctionNodeValueToString", text=" Value to String         ", icon="VALUE_TO_STRING")
            self.draw_text_button(col, "FunctionNodeInputSpecialCharacters", text=" Special Characters  ", icon="SPECIAL")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "FORMAT_STRING")
            props.use_transform = True
            props.type = "FunctionNodeFormatString"

            props = flow.operator("node.add_node", text="", icon = "STRING_JOIN")
            props.use_transform = True
            props.type = "GeometryNodeStringJoin"

            props = flow.operator("node.add_node", text="", icon = "MATCH_STRING")
            props.use_transform = True
            props.type = "FunctionNodeMatchString"

            props = flow.operator("node.add_node", text="", icon = "REPLACE_STRING")
            props.use_transform = True
            props.type = "FunctionNodeReplaceString"

            props = flow.operator("node.add_node", text="", icon = "STRING_SUBSTRING")
            props.use_transform = True
            props.type = "FunctionNodeSliceString"

            props = flow.operator("node.add_node", text = "", icon = "STRING_LENGTH")
            props.use_transform = True
            props.type = "FunctionNodeStringLength"

            props = flow.operator("node.add_node", text="", icon = "STRING_FIND")
            props.use_transform = True
            props.type = "FunctionNodeFindInString"

            props = flow.operator("node.add_node", text = "", icon = "STRING_TO_CURVE")
            props.use_transform = True
            props.type = "GeometryNodeStringToCurves"

            props = flow.operator("node.add_node", text="", icon = "VALUE_TO_STRING")
            props.use_transform = True
            props.type = "FunctionNodeValueToString"

            props = flow.operator("node.add_node", text = "", icon = "SPECIAL")
            props.use_transform = True
            props.type = "FunctionNodeInputSpecialCharacters"


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
            self.draw_text_button(col, "ShaderNodeVectorCurve", text=" Vector Curves  ", icon="NODE_VECTOR")
            self.draw_text_button(col, "ShaderNodeVectorMath", text=" Vector Math      ", icon="NODE_VECTORMATH")
            self.draw_text_button(col, "ShaderNodeVectorRotate", text=" Vector Rotate    ", icon="NODE_VECTORROTATE")
            self.draw_text_button(col, "ShaderNodeCombineXYZ", text=" Combine XYZ   ", icon="NODE_COMBINEXYZ")
            self.draw_text_button(col, "ShaderNodeMix", text=" Mix Vector       ", icon="NODE_MIX", settings={"data_type": "'VECTOR'"})
            self.draw_text_button(col, "ShaderNodeSeparateXYZ", text=" Separate XYZ   ", icon="NODE_SEPARATEXYZ")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTOR")
            props.use_transform = True
            props.type = "ShaderNodeVectorCurve"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTORMATH")
            props.use_transform = True
            props.type = "ShaderNodeVectorMath"

            props = flow.operator("node.add_node", text = "", icon = "NODE_VECTORROTATE")
            props.use_transform = True
            props.type = "ShaderNodeVectorRotate"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COMBINEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeCombineXYZ"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MIX")
            props.use_transform = True
            props.type = "ShaderNodeMix"
            ops = props.settings.add()
            ops.name = "data_type"
            ops.value = "'VECTOR'"

            props = flow.operator("node.add_node", text = "", icon = "NODE_SEPARATEXYZ")
            props.use_transform = True
            props.type = "ShaderNodeSeparateXYZ"


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
            self.draw_text_button(col, "GeometryNodeAccumulateField", text=" Accumulate Field  ", icon="ACCUMULATE")
            self.draw_text_button(col, "GeometryNodeFieldAtIndex", text=" Evaluate at Index ", icon="FIELD_AT_INDEX")
            self.draw_text_button(col, "GeometryNodeFieldOnDomain", text=" Evaluate On Domain ", icon="FIELD_DOMAIN")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "ACCUMULATE")
            props.use_transform = True
            props.type = "GeometryNodeAccumulateField"

            props = flow.operator("node.add_node", text = "", icon = "FIELD_AT_INDEX")
            props.use_transform = True
            props.type = "GeometryNodeFieldAtIndex"

            props = flow.operator("node.add_node", text="", icon = "FIELD_DOMAIN")
            props.use_transform = True
            props.type = "GeometryNodeFieldOnDomain"


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
            self.draw_text_button(col, "FunctionNodeBooleanMath", text=" Boolean Math  ", icon="BOOLEAN_MATH")
            self.draw_text_button(col, "FunctionNodeIntegerMath", text=" Integer Math  ", icon="INTEGER_MATH")
            self.draw_text_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_text_button(col, "FunctionNodeCompare", text=" Compare          ", icon="FLOAT_COMPARE")
            self.draw_text_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "FunctionNodeFloatToInt", text=" Float to Integer ", icon="FLOAT_TO_INT")
            self.draw_text_button(col, "FunctionNodeHashValue", text=" Hash Value      ", icon="HASH")
            self.draw_text_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_text_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_text_button(col, "ShaderNodeMix", text=" Mix                   ", icon="NODE_MIXSHADER")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "BOOLEAN_MATH")
            props.use_transform = True
            props.type = "FunctionNodeBooleanMath"

            props = flow.operator("node.add_node", text="", icon = "INTEGER_MATH")
            props.use_transform = True
            props.type = "FunctionNodeIntegerMath"

            props = flow.operator("node.add_node", text="", icon = "NODE_CLAMP")
            props.use_transform = True
            props.type = "ShaderNodeClamp"

            props = flow.operator("node.add_node", text = "", icon = "FLOAT_COMPARE")
            props.use_transform = True
            props.type = "FunctionNodeCompare"

            props = flow.operator("node.add_node", text = "", icon = "FLOAT_CURVE")
            props.use_transform = True
            props.type = "ShaderNodeFloatCurve"

            props = flow.operator("node.add_node", text="", icon = "FLOAT_TO_INT")
            props.use_transform = True
            props.type = "FunctionNodeFloatToInt"

            props = flow.operator("node.add_node", text="", icon = "HASH")
            props.use_transform = True
            props.type = "FunctionNodeHashValue"

            props = flow.operator("node.add_node", text="", icon = "NODE_MAP_RANGE")
            props.use_transform = True
            props.type = "ShaderNodeMapRange"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "ShaderNodeMath"

            props = flow.operator("node.add_node", text="", icon = "NODE_MIXSHADER")
            props.use_transform = True
            props.type = "ShaderNodeMix"


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
            self.draw_text_button(col, "FunctionNodeCombineMatrix", text=" Combine Matrix     ", icon="COMBINE_MATRIX")
            self.draw_text_button(col, "FunctionNodeCombineTransform", text=" Combine Transform     ", icon="COMBINE_TRANSFORM")
            self.draw_text_button(col, "FunctionNodeMatrixDeterminant", text=" Matrix Determinant     ", icon="MATRIX_DETERMINANT")
            self.draw_text_button(col, "FunctionNodeInvertMatrix", text=" Invert Matrix", icon="INVERT_MATRIX")
            self.draw_text_button(col, "FunctionNodeMatrixMultiply", text=" Multiply Matrix ", icon="MULTIPLY_MATRIX")
            self.draw_text_button(col, "FunctionNodeProjectPoint", text=" Project Point   ", icon="PROJECT_POINT")
            self.draw_text_button(col, "FunctionNodeSeparateMatrix", text=" Separate Matrix   ", icon="SEPARATE_MATRIX")
            self.draw_text_button(col, "FunctionNodeSeparateTransform", text=" Separate Transform   ", icon="SEPARATE_TRANSFORM")
            self.draw_text_button(col, "FunctionNodeTransformDirection", text=" Transform Direction  ", icon="TRANSFORM_DIRECTION")
            self.draw_text_button(col, "FunctionNodeTransformPoint", text=" Transform Point  ", icon="TRANSFORM_POINT")
            self.draw_text_button(col, "FunctionNodeTransposeMatrix", text=" Transpose Matrix ", icon="TRANSPOSE_MATRIX")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "COMBINE_MATRIX")
            props.use_transform = True
            props.type = "FunctionNodeCombineMatrix"

            props = flow.operator("node.add_node", text="", icon = "COMBINE_TRANSFORM")
            props.use_transform = True
            props.type = "FunctionNodeCombineTransform"

            props = flow.operator("node.add_node", text="", icon = "MATRIX_DETERMINANT")
            props.use_transform = True
            props.type = "FunctionNodeMatrixDeterminant"

            props = flow.operator("node.add_node", text="", icon = "INVERT_MATRIX")
            props.use_transform = True
            props.type = "FunctionNodeInvertMatrix"

            props = flow.operator("node.add_node", text="", icon = "MULTIPLY_MATRIX")
            props.use_transform = True
            props.type = "FunctionNodeMatrixMultiply"

            props = flow.operator("node.add_node", text="", icon = "PROJECT_POINT")
            props.use_transform = True
            props.type = "FunctionNodeProjectPoint"

            props = flow.operator("node.add_node", text="", icon = "SEPARATE_MATRIX")
            props.use_transform = True
            props.type = "FunctionNodeSeparateMatrix"

            props = flow.operator("node.add_node", text="", icon = "SEPARATE_TRANSFORM")
            props.use_transform = True
            props.type = "FunctionNodeSeparateTransform"

            props = flow.operator("node.add_node", text="", icon = "TRANSFORM_DIRECTION")
            props.use_transform = True
            props.type = "FunctionNodeTransformDirection"

            props = flow.operator("node.add_node", text="", icon = "TRANSFORM_POINT")
            props.use_transform = True
            props.type = "FunctionNodeTransformPoint"

            props = flow.operator("node.add_node", text="", icon = "TRANSPOSE_MATRIX")
            props.use_transform = True
            props.type = "FunctionNodeTransposeMatrix"


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
            self.draw_text_button(col, "FunctionNodeAlignRotationToVector", text=" Align Rotation to Vector", icon="ALIGN_ROTATION_TO_VECTOR")
            self.draw_text_button(col, "FunctionNodeAxesToRotation", text=" Axes to Rotation ", icon="AXES_TO_ROTATION")
            self.draw_text_button(col, "FunctionNodeAxisAngleToRotation", text=" Axis Angle to Rotation", icon="AXIS_ANGLE_TO_ROTATION")
            self.draw_text_button(col, "FunctionNodeEulerToRotation", text=" Euler to Rotation ", icon="EULER_TO_ROTATION")
            self.draw_text_button(col, "FunctionNodeInvertRotation", text=" Invert Rotation    ", icon="INVERT_ROTATION")
            self.draw_text_button(col, "FunctionNodeRotateRotation", text=" Rotate Rotation         ", icon="ROTATE_EULER")
            self.draw_text_button(col, "FunctionNodeRotateVector", text=" Rotate Vector      ", icon="NODE_VECTORROTATE")
            self.draw_text_button(col, "FunctionNodeRotationToAxisAngle", text=" Rotation to Axis Angle", icon="ROTATION_TO_AXIS_ANGLE")
            self.draw_text_button(col, "FunctionNodeRotationToEuler", text=" Rotation to Euler  ", icon="ROTATION_TO_EULER")
            self.draw_text_button(col, "FunctionNodeRotationToQuaternion", text=" Rotation to Quaternion ", icon="ROTATION_TO_QUATERNION")
            self.draw_text_button(col, "FunctionNodeQuaternionToRotation", text=" Quaternion to Rotation ", icon="QUATERNION_TO_ROTATION")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "ALIGN_ROTATION_TO_VECTOR")
            props.use_transform = True
            props.type = "FunctionNodeAlignRotationToVector"

            props = flow.operator("node.add_node", text="", icon = "AXES_TO_ROTATION")
            props.use_transform = True
            props.type = "FunctionNodeAxesToRotation"

            props = flow.operator("node.add_node", text="", icon = "AXIS_ANGLE_TO_ROTATION")
            props.use_transform = True
            props.type = "FunctionNodeAxisAngleToRotation"

            props = flow.operator("node.add_node", text="", icon = "EULER_TO_ROTATION")
            props.use_transform = True
            props.type = "FunctionNodeEulerToRotation"

            props = flow.operator("node.add_node", text="", icon = "INVERT_ROTATION")
            props.use_transform = True
            props.type = "FunctionNodeInvertRotation"

            props = flow.operator("node.add_node", text="", icon = "ROTATE_EULER")
            props.use_transform = True
            props.type = "FunctionNodeRotateRotation"

            props = flow.operator("node.add_node", text="", icon = "NODE_VECTORROTATE")
            props.use_transform = True
            props.type = "FunctionNodeRotateVector"

            props = flow.operator("node.add_node", text="", icon = "ROTATION_TO_AXIS_ANGLE")
            props.use_transform = True
            props.type = "FunctionNodeRotationToAxisAngle"

            props = flow.operator("node.add_node", text="", icon = "ROTATION_TO_EULER")
            props.use_transform = True
            props.type = "FunctionNodeRotationToEuler"

            props = flow.operator("node.add_node", text="", icon = "ROTATION_TO_QUATERNION")
            props.use_transform = True
            props.type = "FunctionNodeRotationToQuaternion"

            props = flow.operator("node.add_node", text="", icon = "QUATERNION_TO_ROTATION")
            props.use_transform = True
            props.type = "FunctionNodeQuaternionToRotation"


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
            self.draw_text_button(col, "FunctionNodeAlignEulerToVector", text=" Align Euler to Vector", icon="ALIGN_EULER_TO_VECTOR")
            self.draw_text_button(col, "FunctionNodeRotateEuler", text=" Rotate Euler (Depreacated)        ", icon="ROTATE_EULER")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "ALIGN_EULER_TO_VECTOR")
            props.use_transform = True
            props.type = "FunctionNodeAlignEulerToVector"

            props = flow.operator("node.add_node", text = "", icon = "ROTATE_EULER")
            props.use_transform = True
            props.type = "FunctionNodeRotateEuler"


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
            self.draw_text_button(col, "ShaderNodeFresnel", text=" Fresnel              ", icon="NODE_FRESNEL")
            self.draw_text_button(col, "ShaderNodeNewGeometry", text=" Geometry        ", icon="NODE_GEOMETRY")
            self.draw_text_button(col, "ShaderNodeRGB", text=" RGB                 ", icon="NODE_RGB")
            self.draw_text_button(col, "ShaderNodeTexCoord", text="Texture Coordinate   ", icon="NODE_TEXCOORDINATE")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_FRESNEL")
            props.use_transform = True
            props.type = "ShaderNodeFresnel"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GEOMETRY")
            props.use_transform = True
            props.type = "ShaderNodeNewGeometry"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGB")
            props.use_transform = True
            props.type = "ShaderNodeRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_TEXCOORDINATE")
            props.use_transform = True
            props.type = "ShaderNodeTexCoord"


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
                self.draw_text_button(col, "ShaderNodeOutputMaterial", text=" Material Output", icon="NODE_MATERIAL")

            elif context.space_data.shader_type == 'WORLD':
                self.draw_text_button(col, "ShaderNodeOutputWorld", text=" World Output    ", icon="WORLD")

            elif context.space_data.shader_type == 'LINESTYLE':
                self.draw_text_button(col, "ShaderNodeOutputLineStyle", text=" Line Style Output", icon="NODE_LINESTYLE_OUTPUT")

        #### Image Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if context.space_data.shader_type == 'OBJECT':

                props = flow.operator("node.add_node", text="", icon = "NODE_MATERIAL")
                props.use_transform = True
                props.type = "ShaderNodeOutputMaterial"

            elif context.space_data.shader_type == 'WORLD':

                props = flow.operator("node.add_node", text="", icon = "WORLD")
                props.use_transform = True
                props.type = "ShaderNodeOutputWorld"

            elif context.space_data.shader_type == 'LINESTYLE':

                props = flow.operator("node.add_node", text="", icon = "NODE_LINESTYLE_OUTPUT")
                props.use_transform = True
                props.type = "ShaderNodeOutputLineStyle"


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
            self.draw_text_button(col, "ShaderNodeAddShader", text=" Add                   ", icon="NODE_ADD_SHADER")

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfHairPrincipled", text=" Hair BSDF          ", icon="CURVES")
                self.draw_text_button(col, "ShaderNodeMixShader", text=" Mix Shader        ", icon="NODE_MIXSHADER")
                self.draw_text_button(col, "ShaderNodeBsdfPrincipled", text=" Principled BSDF", icon="NODE_PRINCIPLED")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume", icon="NODE_VOLUMEPRINCIPLED")

                if engine == 'CYCLES':
                    self.draw_text_button(col, "ShaderNodeBsdfToon", text=" Toon BSDF           ", icon="NODE_TOONSHADER")

                col = layout.column(align=True)
                col.scale_y = 1.5

                self.draw_text_button(col, "ShaderNodeVolumeAbsorption", text=" Volume Absorption ", icon="NODE_VOLUMEABSORPTION")
                self.draw_text_button(col, "ShaderNodeVolumeScatter", text=" Volume Scatter   ", icon="NODE_VOLUMESCATTER")

            if context.space_data.shader_type == 'WORLD':
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBackground", text=" Background    ", icon="NODE_BACKGROUNDSHADER")
                self.draw_text_button(col, "ShaderNodeEmission", text=" Emission           ", icon="NODE_EMISSION")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled", text=" Principled Volume       ", icon="NODE_VOLUMEPRINCIPLED")
                self.draw_text_button(col, "ShaderNodeMixShader", text=" Mix                   ", icon="NODE_MIXSHADER")

        #### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5


            props = flow.operator("node.add_node", text="", icon = "NODE_ADD_SHADER")
            props.use_transform = True
            props.type = "ShaderNodeAddShader"

            if context.space_data.shader_type == 'OBJECT':

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text="", icon = "CURVES")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfHairPrincipled"

                props = flow.operator("node.add_node", text = "", icon = "NODE_MIXSHADER")
                props.use_transform = True
                props.type = "ShaderNodeMixShader"

                props = flow.operator("node.add_node", text="", icon = "NODE_PRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeBsdfPrincipled"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMEPRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeVolumePrincipled"

                if engine == 'CYCLES':

                    props = flow.operator("node.add_node", text = "", icon = "NODE_TOONSHADER")
                    props.use_transform = True
                    props.type = "ShaderNodeBsdfToon"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMEABSORPTION")
                props.use_transform = True
                props.type = "ShaderNodeVolumeAbsorption"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMESCATTER")
                props.use_transform = True
                props.type = "ShaderNodeVolumeScatter"

            if context.space_data.shader_type == 'WORLD':

                props = flow.operator("node.add_node", text = "", icon = "NODE_BACKGROUNDSHADER")
                props.use_transform = True
                props.type = "ShaderNodeBackground"

                props = flow.operator("node.add_node", text = "", icon = "NODE_EMISSION")
                props.use_transform = True
                props.type = "ShaderNodeEmission"

                props = flow.operator("node.add_node", text="", icon = "NODE_VOLUMEPRINCIPLED")
                props.use_transform = True
                props.type = "ShaderNodeVolumePrincipled"

                props = flow.operator("node.add_node", text = "", icon = "NODE_MIXSHADER")
                props.use_transform = True
                props.type = "ShaderNodeMixShader"


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
            self.draw_text_button(col, "ShaderNodeTexEnvironment", text=" Environment Texture", icon="NODE_ENVIRONMENT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage", text=" Image Texture         ", icon="FILE_IMAGE")
            self.draw_text_button(col, "ShaderNodeTexNoise", text=" Noise Texture         ", icon="NOISE_TEX")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexSky", text=" Sky Texture             ", icon="NODE_SKY")
            self.draw_text_button(col, "ShaderNodeTexVoronoi", text=" Voronoi Texture       ", icon="VORONI_TEX")


        #### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_ENVIRONMENT")
            props.use_transform = True
            props.type = "ShaderNodeTexEnvironment"

            props = flow.operator("node.add_node", text = "", icon = "FILE_IMAGE")
            props.use_transform = True
            props.type = "ShaderNodeTexImage"

            props = flow.operator("node.add_node", text = "", icon = "NOISE_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexNoise"

            props = flow.operator("node.add_node", text = "", icon = "NODE_SKY")
            props.use_transform = True
            props.type = "ShaderNodeTexSky"

            props = flow.operator("node.add_node", text = "", icon = "VORONI_TEX")
            props.use_transform = True
            props.type = "ShaderNodeTexVoronoi"


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
            self.draw_text_button(col, "ShaderNodeBrightContrast", text=" Bright / Contrast ", icon="BRIGHTNESS_CONTRAST")
            self.draw_text_button(col, "ShaderNodeGamma", text=" Gamma             ", icon="NODE_GAMMA")
            self.draw_text_button(col, "ShaderNodeHueSaturation", text=" Hue / Saturation ", icon="NODE_HUESATURATION")
            self.draw_text_button(col, "ShaderNodeInvert", text=" Invert                 ", icon="NODE_INVERT")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMixRGB", text=" Mix RGB           ", icon="NODE_MIXRGB")
            self.draw_text_button(col, "ShaderNodeRGBCurve", text="  RGB Curves        ", icon="NODE_RGBCURVE")

        ##### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "BRIGHTNESS_CONTRAST")
            props.use_transform = True
            props.type = "ShaderNodeBrightContrast"

            props = flow.operator("node.add_node", text = "", icon = "NODE_GAMMA")
            props.use_transform = True
            props.type = "ShaderNodeGamma"

            props = flow.operator("node.add_node", text = "", icon = "NODE_HUESATURATION")
            props.use_transform = True
            props.type = "ShaderNodeHueSaturation"

            props = flow.operator("node.add_node", text = "", icon = "NODE_INVERT")
            props.use_transform = True
            props.type = "ShaderNodeInvert"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MIXRGB")
            props.use_transform = True
            props.type = "ShaderNodeMixRGB"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBCURVE")
            props.use_transform = True
            props.type = "ShaderNodeRGBCurve"


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
            self.draw_text_button(col, "ShaderNodeMapping", text=" Mapping           ", icon="NODE_MAPPING")
            self.draw_text_button(col, "ShaderNodeNormal", text=" Normal            ", icon="RECALC_NORMALS")
            self.draw_text_button(col, "ShaderNodeNormalMap", text=" Normal Map     ", icon="NODE_NORMALMAP")

        ##### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "NODE_MAPPING")
            props.use_transform = True
            props.type = "ShaderNodeMapping"

            props = flow.operator("node.add_node", text = "", icon = "RECALC_NORMALS")
            props.use_transform = True
            props.type = "ShaderNodeNormal"

            props = flow.operator("node.add_node", text = "", icon = "NODE_NORMALMAP")
            props.use_transform = True
            props.type = "ShaderNodeNormalMap"


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
            self.draw_text_button(col, "ShaderNodeClamp", text=" Clamp              ", icon="NODE_CLAMP")
            self.draw_text_button(col, "ShaderNodeValToRGB", text=" ColorRamp       ", icon="NODE_COLORRAMP")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeFloatCurve", text=" Float Curve      ", icon="FLOAT_CURVE")
            self.draw_text_button(col, "ShaderNodeMapRange", text=" Map Range       ", icon="NODE_MAP_RANGE")
            self.draw_text_button(col, "ShaderNodeMath", text=" Math                 ", icon="NODE_MATH")
            self.draw_text_button(col, "ShaderNodeRGBToBW", text=" RGB to BW      ", icon="NODE_RGBTOBW")

        ##### Icon Buttons
        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text="", icon = "NODE_CLAMP")
            props.use_transform = True
            props.type = "ShaderNodeClamp"

            props = flow.operator("node.add_node", text = "", icon = "NODE_COLORRAMP")
            props.use_transform = True
            props.type = "ShaderNodeValToRGB"

            props = flow.operator("node.add_node", text = "", icon = "FLOAT_CURVE")
            props.use_transform = True
            props.type = "ShaderNodeFloatCurve"

            props = flow.operator("node.add_node", text="", icon = "NODE_MAP_RANGE")
            props.use_transform = True
            props.type = "ShaderNodeMapRange"

            props = flow.operator("node.add_node", text = "", icon = "NODE_MATH")
            props.use_transform = True
            props.type = "ShaderNodeMath"

            props = flow.operator("node.add_node", text = "", icon = "NODE_RGBTOBW")
            props.use_transform = True
            props.type = "ShaderNodeRGBToBW"


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
            self.draw_text_button(col, "ShaderNodeScript", text=" Script               ", icon="FILE_SCRIPT")

        ##### Icon Buttons

        else:

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            props = flow.operator("node.add_node", text = "", icon = "FILE_SCRIPT")
            props.use_transform = True
            props.type = "ShaderNodeScript"


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

