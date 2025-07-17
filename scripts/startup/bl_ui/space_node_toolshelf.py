# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.app.translations import (
    pgettext_iface as iface_,
)

import dataclasses

#Add tab, Node Group panel
from nodeitems_builtins import node_tree_group_type


# Null object used to abstractly represent a separator
Separator = object()


@dataclasses.dataclass
class OperatorEntry:
    node : str = None
    operator : str = "node.add_node"
    text : str = ""
    icon : str = None
    props : dict = None
    settings : dict = None
    should_draw : bool = True

    as_dict = dataclasses.asdict


def is_shader_type(context, valid_types):
    if not isinstance(valid_types, set):
        valid_types = {valid_types,}

    try:
        return context.space_data.shader_type in valid_types
    except AttributeError:
        return False


def is_engine(context, valid_engines):
    if not isinstance(valid_engines, set):
        valid_engines = {valid_engines,}

    try:
        return context.engine in valid_engines
    except AttributeError:
        return False


def is_tool_tree(context):
    try:
        return context.space_data.geometry_nodes_type == 'TOOL'
    except AttributeError:
        return False


class NodePanel:
    @staticmethod
    def draw_text_button(layout, node=None, operator="node.add_node", text="", icon=None, settings=None, props=None, pad=0, **kwargs):
        is_add_node_operator = operator == "node.add_node"
        
        # Determine icon automatically from node bl_rna when adding non-zone nodes and no icon is specified
        if is_add_node_operator:
            bl_rna = bpy.types.Node.bl_rna_get_subclass(node)
            if icon is None:
                icon = getattr(bl_rna, "icon", "NONE")

            if text == "":
                text = getattr(bl_rna, "name", iface_("Unknown"))

        if text != "" and pad > 0:
            text = " " + text.strip().ljust(pad)
        
        if is_add_node_operator or text != "":
            props = layout.operator(operator, text=text, icon=icon)
        else:    
            props = layout.operator(operator, icon=icon)
        
        if is_add_node_operator:
            props.use_transform = True
        elif props is not None:
            for prop_key, prop_value in props.items():
                setattr(props, prop_key, prop_value)

        if node is not None:
            props.type = node

        if settings is not None:
            for name, value in settings.items():
                ops = props.settings.add()
                ops.name = name
                ops.value = value

    @staticmethod
    def draw_icon_button(layout, node=None, operator="node.add_node", icon=None, settings=None, props=None, **kwargs):
        is_add_node_operator = operator == "node.add_node"

        # Determine icon automatically from node bl_rna when adding non-zone nodes and no icon is specified
        if icon is None and is_add_node_operator:
            bl_rna = bpy.types.Node.bl_rna_get_subclass(node)
            icon = getattr(bl_rna, "icon", "NONE")
            
        props = layout.operator(operator, text="", icon=icon)
        
        if is_add_node_operator:
            props.use_transform = True
        elif props is not None:
            for prop_key, prop_value in props.items():
                setattr(props, prop_key, prop_value)

        if node is not None:
            props.type = node

        if settings is not None:
            for name, value in settings.items():
                ops = props.settings.add()
                ops.name = name
                ops.value = value

    def draw_entries(self, context, layout, entries):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        # Draw Text Buttons
        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5

            for entry in entries:
                if entry is Separator:
                    col.separator(factor=2/3)
                elif isinstance(entry, OperatorEntry):
                    if entry.should_draw:
                        self.draw_text_button(col, **entry.as_dict())
                else:
                    self.draw_text_button(col, entry)

        # Draw Icon Buttons
        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            for entry in entries:
                if entry is Separator:
                    flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
                    flow.scale_x = 1.5
                    flow.scale_y = 1.5
                elif isinstance(entry, OperatorEntry):
                    if entry.should_draw:
                        self.draw_icon_button(flow, **entry.as_dict())
                else:
                    self.draw_icon_button(flow, entry)


class NODES_PT_toolshelf_display_settings_add(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Add"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree is not None

    @staticmethod
    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        row = layout.row()
        row.prop(addon_prefs,"Node_text_or_icon", text="Icon Buttons")

        if (context.space_data.tree_type in {'ShaderNodeTree'}):
            row.prop(addon_prefs,"Node_shader_add_common", text = "Common")


class NODES_PT_toolshelf_display_settings_relations(bpy.types.Panel):
    """The prop to turn on or off text or icon buttons in the node editor tool shelf."""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "Relations"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree is not None

    @staticmethod
    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        row = layout.row()
        row.prop(addon_prefs,"Node_text_or_icon", text="Icon Buttons")


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
        layout = self.layout

        entries = (
            "ShaderNodeAmbientOcclusion",
            "ShaderNodeAttribute",
            "ShaderNodeBevel",
            "ShaderNodeCameraData",
            "ShaderNodeVertexColor",
            "ShaderNodeFresnel",
            Separator,
            "ShaderNodeNewGeometry",
            "ShaderNodeHairInfo",
            "ShaderNodeLayerWeight",
            "ShaderNodeLightPath",
            "ShaderNodeObjectInfo",
            Separator,
            "ShaderNodeParticleInfo",
            "ShaderNodePointInfo",
            "ShaderNodeRGB",
            "ShaderNodeTangent",
            "ShaderNodeTexCoord",
            OperatorEntry("ShaderNodeUVAlongStroke", should_draw=is_shader_type(context, 'LINESTYLE')),
            Separator,
            "ShaderNodeUVMap",
            "ShaderNodeValue",
            "ShaderNodeVolumeInfo",
            "ShaderNodeWireframe",
        )

        self.draw_entries(context, layout, entries)


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
        layout = self.layout

        is_object_shader = is_shader_type(context, 'OBJECT')
        is_cycles =  is_engine(context, 'CYCLES')

        entries = (
            "ShaderNodeOutputAOV",
            OperatorEntry("ShaderNodeOutputLight", should_draw=is_object_shader and is_cycles),
            OperatorEntry("ShaderNodeOutputMaterial", should_draw=is_object_shader),
            OperatorEntry("ShaderNodeOutputWorld", should_draw=is_shader_type(context, 'WORLD')),
            OperatorEntry("ShaderNodeOutputLineStyle", should_draw=is_shader_type(context, 'LINESTYLE')),
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeBokehImage",
            "CompositorNodeImage",
            "CompositorNodeImageInfo",
            "CompositorNodeImageCoordinates",
            "CompositorNodeMask",
            "CompositorNodeMovieClip",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeRGB",
            "ShaderNodeValue",
            "CompositorNodeNormal",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeRLayers",
            "CompositorNodeSceneTime",
            "CompositorNodeTime",
        )
        
        self.draw_entries(context, layout, entries)

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
        layout = self.layout

        entries = (
            "CompositorNodeComposite",
            "CompositorNodeViewer",
            Separator,
            "CompositorNodeOutputFile",
        )
        
        self.draw_entries(context, layout, entries)


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
        layout = self.layout

        entries = (
            "CompositorNodePremulKey",
            "ShaderNodeBlackbody",
            "ShaderNodeValToRGB",
            "CompositorNodeConvertColorSpace",
            "CompositorNodeSetAlpha",
            Separator,
            "CompositorNodeInvert",
            "CompositorNodeRGBToBW",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeBrightContrast",
            "CompositorNodeColorBalance",
            "CompositorNodeColorCorrection",

            "CompositorNodeExposure",
            "CompositorNodeGamma",
            "CompositorNodeHueCorrect",
            "CompositorNodeHueSat",
            "CompositorNodeCurveRGB",
            "CompositorNodeTonemap",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeAlphaOver",
            Separator,
            "CompositorNodeCombineColor",
            "CompositorNodeSeparateColor",
            Separator,
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Color"), settings={"data_type": "'RGBA'"}),
            "CompositorNodeZcombine",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeAntiAliasing",
            "CompositorNodeDenoise",
            "CompositorNodeDespeckle",
            Separator,
            "CompositorNodeDilateErode",
            "CompositorNodeInpaint",
            Separator,
            "CompositorNodeFilter",
            "CompositorNodeGlare",
            "CompositorNodeKuwahara",
            "CompositorNodePixelate",
            "CompositorNodePosterize",
            "CompositorNodeSunBeams",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeBilateralblur",
            "CompositorNodeBlur",
            "CompositorNodeBokehBlur",
            "CompositorNodeDefocus",
            "CompositorNodeDBlur",
            "CompositorNodeVecBlur",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeChannelMatte",
            "CompositorNodeChromaMatte",
            "CompositorNodeColorMatte",
            "CompositorNodeColorSpill",
            "CompositorNodeDiffMatte",
            "CompositorNodeDistanceMatte",
            "CompositorNodeKeying",
            "CompositorNodeKeyingScreen",
            "CompositorNodeLumaMatte",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeCryptomatteV2",
            "CompositorNodeCryptomatte",
            Separator,
            "CompositorNodeBoxMask",
            "CompositorNodeEllipseMask",
            Separator,
            "CompositorNodeDoubleEdgeMask",
            "CompositorNodeIDMask",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeTexBrick",
            "ShaderNodeTexChecker",
            "ShaderNodeTexGabor",
            "ShaderNodeTexGradient",
            "ShaderNodeTexMagic",
            "ShaderNodeTexNoise",
            "ShaderNodeTexVoronoi",
            "ShaderNodeTexWave",
            "ShaderNodeTexWhiteNoise",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeRotate",
            "CompositorNodeScale",
            "CompositorNodeTransform",
            "CompositorNodeTranslate",
            Separator,
            "CompositorNodeCornerPin",
            "CompositorNodeCrop",
            Separator,
            "CompositorNodeDisplace",
            "CompositorNodeFlip",
            "CompositorNodeMapUV",
            Separator,
            "CompositorNodeLensdist",
            "CompositorNodeMovieDistortion",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "CompositorNodeRotate",
            "CompositorNodeScale",
            "CompositorNodeTransform",
            "CompositorNodeTranslate",
            Separator,
            "CompositorNodeCornerPin",
            "CompositorNodeCrop",
            Separator,
            "CompositorNodeDisplace",
            "CompositorNodeFlip",
            "CompositorNodeMapUV",
            Separator,
            "CompositorNodeLensdist",
            "CompositorNodeMovieDistortion",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeMapRange",
            "ShaderNodeMath",
            "ShaderNodeMix",
            "ShaderNodeClamp",
            "ShaderNodeFloatCurve",
            Separator,
            "CompositorNodeLevels",
            "CompositorNodeNormalize",
            Separator,
            "CompositorNodeSplit",
            "CompositorNodeSwitch",
            OperatorEntry("CompositorNodeSwitchView", text="Switch Stereo View"),
            Separator,
            "CompositorNodeRelativeToPixel",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeCombineXYZ",
            "ShaderNodeSeparateXYZ",
            Separator,
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), settings={"data_type": "'VECTOR'"}),
            "ShaderNodeVectorCurve",
            "ShaderNodeVectorMath",
            "ShaderNodeVectorRotate",
        )
        
        self.draw_entries(context, layout, entries)


#Input nodes tab, textures common panel. Texture mode
class NODES_PT_Input_input_tex(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeCoordinates",
            "TextureNodeCurveTime",
            "TextureNodeImage",
            "TextureNodeTexture",
        )
        
        self.draw_entries(context, layout, entries)


#Input nodes tab, textures advanced panel. Just in Texture mode
class NODES_PT_Input_textures_tex(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Textures"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in shader and texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeTexBlend",
            "TextureNodeTexClouds",
            "TextureNodeTexDistNoise",
            "TextureNodeTexMagic",
            Separator,
            "TextureNodeTexMarble",
            "TextureNodeTexNoise",
            "TextureNodeTexStucci",
            "TextureNodeTexVoronoi",
            Separator,
            "TextureNodeTexWood",
        )
        
        self.draw_entries(context, layout, entries)


#Input nodes tab, Pattern panel. # Just in texture mode
class NODES_PT_Input_pattern(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pattern"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeBricks",
            "TextureNodeChecker",
        )
        
        self.draw_entries(context, layout, entries)


#Input nodes tab, Color panel. Just in texture mode
class NODES_PT_Input_color_tex(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture and compositing mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeHueSaturation",
            "TextureNodeInvert",
            "TextureNodeMixRGB",
            "TextureNodeCurveRGB",
            Separator,
            "TextureNodeCombineColor",
            "TextureNodeSeparateColor",
        )
        
        self.draw_entries(context, layout, entries)


#Input nodes tab, Output panel, Texture mode
class NODES_PT_Input_output_tex(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeOutput",
            "TextureNodeViewer",
        )
        
        self.draw_entries(context, layout, entries)


#Modify nodes tab, converter panel. Just in texture mode
class NODES_PT_converter_tex(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeValToRGB",
            "TextureNodeDistance",
            "TextureNodeMath",
            "TextureNodeRGBToBW",
            Separator,
            "TextureNodeValToNor",
        )
        
        self.draw_entries(context, layout, entries)


#Modify nodes tab, distort panel. Just in texture mode
class NODES_PT_distort_tex(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Distort"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree') # Just in texture mode

    @staticmethod
    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeAt",
            "TextureNodeRotate",
            "TextureNodeScale",
            "TextureNodeTranslate",
        )
        
        self.draw_entries(context, layout, entries)


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
        layout = self.layout

        is_object = is_shader_type(context, 'OBJECT')
        is_eevee = is_engine(context, 'BLENDER_EEVEE')

        entries = (
            "ShaderNodeAddShader",
            OperatorEntry("ShaderNodeBackground", should_draw=is_shader_type(context, 'WORLD')),
            OperatorEntry("ShaderNodeBsdfDiffuse", should_draw=is_object),
            "ShaderNodeEmission",
            OperatorEntry("ShaderNodeBsdfGlass", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfGlossy", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfHair", should_draw=is_object and not is_eevee),
            OperatorEntry("ShaderNodeHoldout", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfMetallic", should_draw=is_object),
            "ShaderNodeMixShader",
            OperatorEntry("ShaderNodeBsdfPrincipled", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfHairPrincipled", should_draw=is_object and not is_eevee),
            OperatorEntry("ShaderNodeVolumePrincipled"),
            OperatorEntry("ShaderNodeBsdfRayPortal", should_draw=is_object and not is_eevee),
            OperatorEntry("ShaderNodeBsdfRefraction", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfSheen", should_draw=is_object and not is_eevee),
            OperatorEntry("ShaderNodeEeveeSpecular", should_draw=is_object and is_eevee),
            OperatorEntry("ShaderNodeSubsurfaceScattering", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfToon", should_draw=is_object and not is_eevee),
            OperatorEntry("ShaderNodeBsdfTranslucent", should_draw=is_object),
            OperatorEntry("ShaderNodeBsdfTransparent", should_draw=is_object),
            "ShaderNodeVolumeAbsorption",
            "ShaderNodeVolumeScatter",
            "ShaderNodeVolumeCoefficients",
        )

        self.draw_entries(context, layout, entries)


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
        layout = self.layout

        entries = (
            "ShaderNodeTexBrick",
            "ShaderNodeTexChecker",
            "ShaderNodeTexEnvironment",
            "ShaderNodeTexGabor",
            "ShaderNodeTexGradient",
            "ShaderNodeTexIES",
            Separator,
            "ShaderNodeTexImage",
            "ShaderNodeTexMagic",
            "ShaderNodeTexNoise",
            "ShaderNodeTexSky",
            Separator,
            "ShaderNodeTexVoronoi",
            "ShaderNodeTexWave",
            "ShaderNodeTexWhiteNoise",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeBrightContrast",
            "ShaderNodeGamma",
            "ShaderNodeHueSaturation",
            "ShaderNodeInvert",
            Separator,
            "ShaderNodeLightFalloff",
            OperatorEntry("ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"}),
            "ShaderNodeRGBCurve",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeBump",
            "ShaderNodeDisplacement",
            "ShaderNodeMapping",
            "ShaderNodeNormal",
            "ShaderNodeNormalMap",
            Separator,
            "ShaderNodeVectorCurve",
            "ShaderNodeVectorDisplacement",
            "ShaderNodeVectorRotate",
            "ShaderNodeVectorTransform",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeBlackbody",
            "ShaderNodeClamp",
            "ShaderNodeValToRGB",
            "ShaderNodeCombineColor",
            "ShaderNodeCombineXYZ",
            Separator,
            "ShaderNodeFloatCurve",
            "ShaderNodeMapRange",
            "ShaderNodeMath",
            "ShaderNodeMix",
            "ShaderNodeRGBToBW",
            Separator,
            "ShaderNodeSeparateColor",
            "ShaderNodeSeparateXYZ",
            OperatorEntry("ShaderNodeShaderToRGB", should_draw=is_engine(context, 'BLENDER_EEVEE')),
            "ShaderNodeVectorMath",
            "ShaderNodeWavelength",
        )

        self.draw_entries(context, layout, entries)


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
        in_group = context.space_data.edit_tree in context.blend_data.node_groups.values()
        
        entries = (
            OperatorEntry(operator="node.group_make", icon="NODE_MAKEGROUP"),
            OperatorEntry(operator="node.group_insert", text="Insert into Group", icon="NODE_GROUPINSERT"),
            OperatorEntry(operator="node.group_ungroup", icon="NODE_UNGROUP"),
            Separator,
            OperatorEntry(operator="node.group_edit", text="Toggle Edit Group", icon="NODE_EDITGROUP", props={"exit" : False}),
            Separator,
            OperatorEntry("NodeGroupInput", should_draw=in_group),
            OperatorEntry("NodeGroupOutput", should_draw=in_group),
        )

        self.draw_entries(context, layout, entries)


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
        layout.label(text = "Add Node Group:")

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

        entries = (
            "NodeFrame",
            "NodeReroute",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeAttributeStatistic",
            "GeometryNodeAttributeDomainSize",
            Separator,
            "GeometryNodeBlurAttribute",
            "GeometryNodeCaptureAttribute",
            "GeometryNodeRemoveAttribute",
            "GeometryNodeStoreNamedAttribute",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "FunctionNodeInputBool",
            "GeometryNodeInputCollection",
            "FunctionNodeInputColor",
            "GeometryNodeInputImage",
            "FunctionNodeInputInt",
            "GeometryNodeInputMaterial",
            "GeometryNodeInputObject",
            "FunctionNodeInputRotation",
            "FunctionNodeInputString",
            "ShaderNodeValue",
            "FunctionNodeInputVector",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeGizmoDial",
            "GeometryNodeGizmoLinear",
            "GeometryNodeGizmoTransform",
        )
        
        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeImportOBJ",
            "GeometryNodeImportPLY",
            "GeometryNodeImportSTL",
            "GeometryNodeImportCSV",
            "GeometryNodeImportText",
            "GeometryNodeImportVDB",
        )

        self.draw_entries(context, layout, entries)


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

        is_tool = is_tool_tree(context)
        entries = (
            OperatorEntry("GeometryNodeTool3DCursor", should_draw=is_tool),
            "GeometryNodeInputActiveCamera",
            "GeometryNodeCameraInfo",
            "GeometryNodeCollectionInfo",
            "GeometryNodeImageInfo",
            "GeometryNodeIsViewport",
            "GeometryNodeInputNamedLayerSelection",
            OperatorEntry("GeometryNodeToolMousePosition", should_draw=is_tool),
            "GeometryNodeObjectInfo",
            "GeometryNodeInputSceneTime",
            "GeometryNodeSelfObject",
            OperatorEntry("GeometryNodeViewportTransform", should_draw=is_tool),
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeViewer",
            "GeometryNodeWarning",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeGeometryToInstance",
            "GeometryNodeJoinGeometry",
        )

        self.draw_entries(context, layout, entries)


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

        is_tool = is_tool_tree(context)
        entries = (
            "GeometryNodeInputID",
            "GeometryNodeInputIndex",
            "GeometryNodeInputNamedAttribute",
            "GeometryNodeInputNormal",
            "GeometryNodeInputPosition",
            "GeometryNodeInputRadius",
            OperatorEntry("GeometryNodeToolSelection", should_draw=is_tool),
            OperatorEntry("GeometryNodeToolActiveElement", should_draw=is_tool),
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeProximity",
            "GeometryNodeIndexOfNearest",
            "GeometryNodeRaycast",
            "GeometryNodeSampleIndex",
            "GeometryNodeSampleNearest",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeSetGeometryName",
            "GeometryNodeSetID",
            "GeometryNodeSetPosition",
            OperatorEntry("GeometryNodeToolSetSelection", should_draw=is_tool_tree(context)),
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeBake",
            "GeometryNodeBoundBox",
            "GeometryNodeConvexHull",
            "GeometryNodeDeleteGeometry",
            "GeometryNodeDuplicateElements",
            "GeometryNodeMergeByDistance",
            "GeometryNodeSortElements",
            "GeometryNodeTransform",
            Separator,
            "GeometryNodeSeparateComponents",
            "GeometryNodeSeparateGeometry",
            "GeometryNodeSplitToInstances",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeInputCurveHandlePositions",
            "GeometryNodeCurveLength",
            "GeometryNodeInputTangent",
            "GeometryNodeInputCurveTilt",
            "GeometryNodeCurveEndpointSelection",
            "GeometryNodeCurveHandleTypeSelection",
            "GeometryNodeInputSplineCyclic",
            "GeometryNodeSplineLength",
            "GeometryNodeSplineParameter",
            "GeometryNodeInputSplineResolution",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeSampleCurve",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeSetCurveNormal",
            "GeometryNodeSetCurveRadius",
            "GeometryNodeSetCurveTilt",
            "GeometryNodeSetCurveHandlePositions",
            "GeometryNodeCurveSetHandles",
            "GeometryNodeSetSplineCyclic",
            "GeometryNodeSetSplineResolution",
            "GeometryNodeCurveSplineType",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeCurvesToGreasePencil",
            "GeometryNodeCurveToMesh",
            "GeometryNodeCurveToPoints",
            "GeometryNodeDeformCurvesOnSurface",
            "GeometryNodeFillCurve",
            "GeometryNodeFilletCurve",
            "GeometryNodeGreasePencilToCurves",
            "GeometryNodeInterpolateCurves",
            "GeometryNodeResampleCurve",
            "GeometryNodeReverseCurve",
            "GeometryNodeSubdivideCurve",
            "GeometryNodeTrimCurve",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeCurveArc",
            "GeometryNodeCurvePrimitiveBezierSegment",
            "GeometryNodeCurvePrimitiveCircle",
            "GeometryNodeCurvePrimitiveLine",
            "GeometryNodeCurveSpiral",
            "GeometryNodeCurveQuadraticBezier",
            "GeometryNodeCurvePrimitiveQuadrilateral",
            "GeometryNodeCurveStar",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeCurveOfPoint",
            "GeometryNodeOffsetPointInCurve",
            "GeometryNodePointsOfCurve",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeInputNamedLayerSelection",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeSetGreasePencilColor",
            "GeometryNodeSetGreasePencilDepth",
            "GeometryNodeSetGreasePencilSoftness",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeGreasePencilToCurves",
            "GeometryNodeMergeLayers",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeInstanceOnPoints",
            "GeometryNodeInstancesToPoints",
            "GeometryNodeRealizeInstances",
            "GeometryNodeRotateInstances",
            "GeometryNodeScaleInstances",
            "GeometryNodeTranslateInstances",
            "GeometryNodeSetInstanceTransform",
            Separator,
            "GeometryNodeInstanceTransform",
            "GeometryNodeInputInstanceRotation",
            "GeometryNodeInputInstanceScale",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeInputMeshEdgeAngle",
            "GeometryNodeInputMeshEdgeNeighbors",
            "GeometryNodeInputMeshEdgeVertices",
            "GeometryNodeEdgesToFaceGroups",
            "GeometryNodeInputMeshFaceArea",
            Separator,
            "GeometryNodeMeshFaceSetBoundaries",
            "GeometryNodeInputMeshFaceNeighbors",
            OperatorEntry("GeometryNodeToolFaceSet", should_draw=is_tool_tree(context)),
            "GeometryNodeInputMeshFaceIsPlanar",
            "GeometryNodeInputShadeSmooth",
            "GeometryNodeInputEdgeSmooth",
            Separator,
            "GeometryNodeInputMeshIsland",
            "GeometryNodeInputShortestEdgePaths",
            "GeometryNodeInputMeshVertexNeighbors",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeSampleNearestSurface",
            "GeometryNodeSampleUVSurface",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            OperatorEntry("GeometryNodeToolSetFaceSet", should_draw=is_tool_tree(context)),
            "GeometryNodeSetMeshNormal",
            "GeometryNodeSetShadeSmooth",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeDualMesh",
            "GeometryNodeEdgePathsToCurves",
            "GeometryNodeEdgePathsToSelection",
            "GeometryNodeExtrudeMesh",
            "GeometryNodeFlipFaces",
            Separator,
            "GeometryNodeMeshBoolean",
            "GeometryNodeMeshToCurve",
            "GeometryNodeMeshToPoints",
            "GeometryNodeMeshToVolume",
            "GeometryNodeScaleElements",
            Separator,
            "GeometryNodeSplitEdges",
            "GeometryNodeSubdivideMesh",
            "GeometryNodeSubdivisionSurface",
            "GeometryNodeTriangulate",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeMeshCone",
            "GeometryNodeMeshCube",
            "GeometryNodeMeshCylinder",
            "GeometryNodeMeshGrid",
            Separator,
            "GeometryNodeMeshIcoSphere",
            "GeometryNodeMeshCircle",
            "GeometryNodeMeshLine",
            "GeometryNodeMeshUVSphere",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeCornersOfEdge",
            "GeometryNodeCornersOfFace",
            "GeometryNodeCornersOfVertex",
            "GeometryNodeEdgesOfCorner",
            Separator,
            "GeometryNodeEdgesOfVertex",
            "GeometryNodeFaceOfCorner",
            "GeometryNodeOffsetCornerInFace",
            "GeometryNodeVertexOfCorner",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeUVPackIslands",
            "GeometryNodeUVUnwrap",
        )

        self.draw_entries(context, layout, entries)


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

        
        entries = (
            "GeometryNodeDistributePointsInVolume",
            "GeometryNodeDistributePointsOnFaces",
            Separator,
            "GeometryNodePoints",
            "GeometryNodePointsToCurves",
            "GeometryNodePointsToVertices",
            "GeometryNodePointsToVolume",
            "GeometryNodeSetPointRadius",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeVolumeCube",
            "GeometryNodeVolumeToMesh",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            OperatorEntry(operator="node.add_simulation_zone", text="Simulation Zone", icon="TIME"),
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeReplaceMaterial",
            "GeometryNodeInputMaterialIndex",
            "GeometryNodeMaterialSelection",
            "GeometryNodeSetMaterial",
            "GeometryNodeSetMaterialIndex",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "ShaderNodeTexBrick",
            "ShaderNodeTexChecker",
            "ShaderNodeTexGradient",
            "GeometryNodeImageTexture",
            "ShaderNodeTexMagic",
            "ShaderNodeTexNoise",
            "ShaderNodeTexVoronoi",
            "ShaderNodeTexWave",
            "ShaderNodeTexWhiteNoise",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            OperatorEntry(operator="node.add_foreach_geometry_element_zone", text="For Each Element", icon="FOR_EACH"),
            "GeometryNodeIndexSwitch",
            "GeometryNodeMenuSwitch",
            "FunctionNodeRandomValue",
            OperatorEntry(operator="node.add_repeat_zone", text="Repeat Zone", icon="REPEAT"),
            "GeometryNodeSwitch",
        )

        self.draw_entries(context, layout, entries)

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

        entries = (
            "ShaderNodeValToRGB",
            "ShaderNodeRGBCurve",
            Separator,
            "FunctionNodeCombineColor",
            OperatorEntry("ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"}),
            "FunctionNodeSeparateColor",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "FunctionNodeFormatString",
            "GeometryNodeStringJoin",
            "FunctionNodeMatchString",
            "FunctionNodeReplaceString",
            "FunctionNodeSliceString",
            "FunctionNodeStringLength",
            "FunctionNodeFindInString",
            "GeometryNodeStringToCurves",
            "FunctionNodeValueToString",
            "FunctionNodeInputSpecialCharacters",
        )

        self.draw_entries(context, layout, entries)

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

        entries = (
            "ShaderNodeVectorCurve",
            "ShaderNodeVectorMath",
            "ShaderNodeVectorRotate",
            "ShaderNodeCombineXYZ",
            OperatorEntry("ShaderNodeMix", text="Mix Vector", settings={"data_type": "'VECTOR'"}),
            "ShaderNodeSeparateXYZ",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "GeometryNodeAccumulateField",
            "GeometryNodeFieldAtIndex",
            "GeometryNodeFieldOnDomain",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "FunctionNodeBooleanMath",
            "FunctionNodeIntegerMath",
            "ShaderNodeClamp",
            "FunctionNodeCompare",
            "ShaderNodeFloatCurve",
            Separator,
            "FunctionNodeFloatToInt",
            "FunctionNodeHashValue",
            "ShaderNodeMapRange",
            "ShaderNodeMath",
            "ShaderNodeMix",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "FunctionNodeCombineMatrix",
            "FunctionNodeCombineTransform",
            "FunctionNodeMatrixDeterminant",
            "FunctionNodeInvertMatrix",
            "FunctionNodeMatrixMultiply",
            "FunctionNodeProjectPoint",
            "FunctionNodeSeparateMatrix",
            "FunctionNodeSeparateTransform",
            "FunctionNodeTransformDirection",
            "FunctionNodeTransformPoint",
            "FunctionNodeTransposeMatrix",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "FunctionNodeAlignRotationToVector",
            "FunctionNodeAxesToRotation",
            "FunctionNodeAxisAngleToRotation",
            "FunctionNodeEulerToRotation",
            "FunctionNodeInvertRotation",
            "FunctionNodeRotateRotation",
            "FunctionNodeRotateVector",
            "FunctionNodeRotationToAxisAngle",
            "FunctionNodeRotationToEuler",
            "FunctionNodeRotationToQuaternion",
            "FunctionNodeQuaternionToRotation",
        )

        self.draw_entries(context, layout, entries)


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

        entries = (
            "FunctionNodeAlignEulerToVector",
            "FunctionNodeRotateEuler",
        )

        self.draw_entries(context, layout, entries)


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
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if not addon_prefs.Node_text_or_icon:

        ##### --------------------------------- Textures common ------------------------------------------- ####

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeFresnel")
            self.draw_text_button(col, "ShaderNodeNewGeometry")
            self.draw_text_button(col, "ShaderNodeRGB")
            self.draw_text_button(col, "ShaderNodeTexCoord")

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
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5

            if is_shader_type(context, 'OBJECT'):
                self.draw_text_button(col, "ShaderNodeOutputMaterial")

            elif is_shader_type(context, 'WORLD'):
                self.draw_text_button(col, "ShaderNodeOutputWorld")

            elif is_shader_type(context, 'LINESTYLE'):
                self.draw_text_button(col, "ShaderNodeOutputLineStyle")

        #### Image Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if is_shader_type(context, 'OBJECT'):
                self.draw_icon_button(flow, "ShaderNodeOutputMaterial")

            elif is_shader_type(context, 'WORLD'):
                self.draw_icon_button(flow, "ShaderNodeOutputWorld")

            elif is_shader_type(context, 'LINESTYLE'):
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
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #### Text Buttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeAddShader")

            if is_shader_type(context, 'OBJECT'):

                if is_engine(context, 'CYCLES'):
                    self.draw_text_button(col, "ShaderNodeBsdfHairPrincipled")
                self.draw_text_button(col, "ShaderNodeMixShader")
                self.draw_text_button(col, "ShaderNodeBsdfPrincipled")

                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeVolumePrincipled")

                if is_engine(context, 'CYCLES'):
                    self.draw_text_button(col, "ShaderNodeBsdfToon")

                col = layout.column(align=True)
                col.scale_y = 1.5

                self.draw_text_button(col, "ShaderNodeVolumeAbsorption")
                self.draw_text_button(col, "ShaderNodeVolumeScatter")

            if is_shader_type(context, 'WORLD'):
                col = layout.column(align=True)
                col.scale_y = 1.5
                self.draw_text_button(col, "ShaderNodeBackground")
                self.draw_text_button(col, "ShaderNodeEmission")
                self.draw_text_button(col, "ShaderNodeVolumePrincipled")
                self.draw_text_button(col, "ShaderNodeMixShader")

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.draw_icon_button(flow, "ShaderNodeAddShader")

            if is_shader_type(context, 'OBJECT'):

                if is_engine(context, 'CYCLES'):
                    self.draw_icon_button(flow, "ShaderNodeBsdfHairPrincipled")
                self.draw_icon_button(flow, "ShaderNodeMixShader")
                self.draw_icon_button(flow, "ShaderNodeBsdfPrincipled")
                self.draw_icon_button(flow, "ShaderNodeVolumePrincipled")

                if is_engine(context, 'CYCLES'):
                    self.draw_icon_button(flow, "ShaderNodeBsdfToon")
                self.draw_icon_button(flow, "ShaderNodeVolumeAbsorption")
                self.draw_icon_button(flow, "ShaderNodeVolumeScatter")

            if is_shader_type(context, 'WORLD'):
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
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexEnvironment")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage")
            self.draw_text_button(col, "ShaderNodeTexNoise")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexSky")
            self.draw_text_button(col, "ShaderNodeTexVoronoi")

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

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeBrightContrast")
            self.draw_text_button(col, "ShaderNodeGamma")
            self.draw_text_button(col, "ShaderNodeHueSaturation")
            self.draw_text_button(col, "ShaderNodeInvert")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMixRGB")
            self.draw_text_button(col, "ShaderNodeRGBCurve")

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

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMapping")
            self.draw_text_button(col, "ShaderNodeNormal")
            self.draw_text_button(col, "ShaderNodeNormalMap")
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

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeClamp")
            self.draw_text_button(col, "ShaderNodeValToRGB")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeFloatCurve")
            self.draw_text_button(col, "ShaderNodeMapRange")
            self.draw_text_button(col, "ShaderNodeMath")
            self.draw_text_button(col, "ShaderNodeRGBToBW")

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

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeScript")

        ##### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "ShaderNodeScript")


classes = (
    NODES_PT_toolshelf_display_settings_add,
    NODES_PT_toolshelf_display_settings_relations,
    NODES_PT_shader_add_input,
    NODES_PT_shader_add_output,
    NODES_PT_shader_add_shader,
    NODES_PT_shader_add_texture,
    NODES_PT_shader_add_color,
    NODES_PT_shader_add_vector,
    NODES_PT_shader_add_converter,

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
    NODES_PT_Input_pattern,
    NODES_PT_Input_color_tex,
    NODES_PT_Input_output_tex,
    NODES_PT_converter_tex,
    NODES_PT_distort_tex,


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

