# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.app.translations import (
    pgettext_iface as iface_,
)

import dataclasses

from nodeitems_builtins import node_tree_group_type
from .node_add_menu import draw_node_groups, add_empty_group


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

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        row = layout.row()
        row.prop(addon_prefs,"Node_text_or_icon", text="Icon Buttons")


class NODES_PT_toolshelf_shader_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        if use_common:
            entries = (
                "ShaderNodeFresnel",
                "ShaderNodeNewGeometry",
                "ShaderNodeRGB",
                "ShaderNodeTexCoord",
            )
        else:
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


class NODES_PT_toolshelf_shader_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        is_object_shader = is_shader_type(context, 'OBJECT')
        is_cycles =  is_engine(context, 'CYCLES')

        if use_common:
            entries = (
                OperatorEntry("ShaderNodeOutputMaterial", should_draw=is_object_shader),
                OperatorEntry("ShaderNodeOutputWorld", should_draw=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeOutputLineStyle", should_draw=is_shader_type(context, 'LINESTYLE')),
            )
        else:
            entries = (
                "ShaderNodeOutputAOV",
                OperatorEntry("ShaderNodeOutputLight", should_draw=is_object_shader and is_cycles),
                OperatorEntry("ShaderNodeOutputMaterial", should_draw=is_object_shader),
                OperatorEntry("ShaderNodeOutputWorld", should_draw=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeOutputLineStyle", should_draw=is_shader_type(context, 'LINESTYLE')),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_input_constant(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_input"

    def draw(self, context):
        layout = self.layout

        entries = (
            "CompositorNodeRGB",
            "ShaderNodeValue",
            "CompositorNodeNormal",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_input_scene(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Scene"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_input"

    def draw(self, context):
        layout = self.layout

        entries = (
            "CompositorNodeRLayers",
            "CompositorNodeSceneTime",
            "CompositorNodeTime",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "CompositorNodeComposite",
            "CompositorNodeViewer",
            Separator,
            "CompositorNodeOutputFile",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree') # Just in texture and compositing mode

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


class NODES_PT_toolshelf_compositor_add_color_adjust(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Adjust"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_color"

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


class NODES_PT_toolshelf_compositor_add_color_mix(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mix"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_color"

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


class NODES_PT_toolshelf_compositor_add_filter(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Filter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_filter_blur(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Blur"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_filter"

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


class NODES_PT_toolshelf_compositor_add_keying(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Keying"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_mask(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mask"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_texture(bpy.types.Panel, NodePanel):
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_tracking(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Tracking"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_transform(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Transform"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_utility(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Utilities"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_compositor_add_vector(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

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


class NODES_PT_toolshelf_texture_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeCoordinates",
            "TextureNodeCurveTime",
            "TextureNodeImage",
            "TextureNodeTexture",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_texture(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Textures"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

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


class NODES_PT_toolshelf_texture_add_pattern(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Pattern"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeBricks",
            "TextureNodeChecker",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

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


class NODES_PT_toolshelf_texture_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeOutput",
            "TextureNodeViewer",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_converter(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

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


class NODES_PT_toolshelf_texture_add_distort(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Distort"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "TextureNodeAt",
            "TextureNodeRotate",
            "TextureNodeScale",
            "TextureNodeTranslate",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_shader(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Shader"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and context.space_data.shader_type in ('OBJECT', 'WORLD'))

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        is_object = is_shader_type(context, 'OBJECT')
        is_eevee = is_engine(context, 'BLENDER_EEVEE')

        if use_common:
            entries = (
                "ShaderNodeAddShader",
                OperatorEntry("ShaderNodeBackground", should_draw=is_shader_type(context, 'WORLD')),
                "ShaderNodeEmission",
                "ShaderNodeMixShader",
                OperatorEntry("ShaderNodeBsdfPrincipled", should_draw=is_object),
                OperatorEntry("ShaderNodeBsdfHairPrincipled", should_draw=is_object and not is_eevee),
                OperatorEntry("ShaderNodeVolumePrincipled"),
                OperatorEntry("ShaderNodeBsdfToon", should_draw=is_object and not is_eevee),
                "ShaderNodeVolumeAbsorption",
                "ShaderNodeVolumeScatter",
            )
        else:
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


class NODES_PT_toolshelf_shader_add_texture(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common
        
        if use_common:
            entries = (
                "ShaderNodeTexEnvironment",
                "ShaderNodeTexImage",
                "ShaderNodeTexNoise",
                "ShaderNodeTexSky",
                "ShaderNodeTexVoronoi",
            )
        else:
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


class NODES_PT_toolshelf_shader_add_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'
    
    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common
        
        if use_common:
            entries = (
                "ShaderNodeBrightContrast",
                "ShaderNodeGamma",
                "ShaderNodeHueSaturation",
                "ShaderNodeInvert",
                Separator,
                OperatorEntry("ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"}),
                "ShaderNodeRGBCurve",
            )
        else:
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


class NODES_PT_toolshelf_shader_add_vector(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        if use_common:
            entries = (
                "ShaderNodeMapping",
                "ShaderNodeNormal",
                "ShaderNodeNormalMap",
            )
        else:
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


class NODES_PT_toolshelf_shader_add_converter(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        if use_common:
            entries = (
                "ShaderNodeClamp",
                "ShaderNodeValToRGB",
                Separator,
                "ShaderNodeFloatCurve",
                "ShaderNodeMapRange",
                "ShaderNodeMath",
                "ShaderNodeRGBToBW",
            )
        else:
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


class NODES_PT_toolshelf_shader_add_script(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Script"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "ShaderNodeScript",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_relations_group_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Group"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

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


class NODES_PT_relations_nodegroups(bpy.types.Panel, NodePanel):
    bl_label = "Nodegroups"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in node_tree_group_type)

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.scale_y = 1.5
        add_empty_group(col)
        draw_node_groups(context, col)
        return


class NODES_PT_relations_layout(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Layout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

    def draw(self, context):
        layout = self.layout

        entries = (
            "NodeFrame",
            "NodeReroute",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_attribute(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Attribute"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_input(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_input_constant(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

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


class NODES_PT_toolshelf_gn_add_input_gizmo(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Gizmo"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeGizmoDial",
            "GeometryNodeGizmoLinear",
            "GeometryNodeGizmoTransform",
        )
        
        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_input_file(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Import"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

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


class NODES_PT_toolshelf_gn_add_input_scene(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Scene"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

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


class NODES_PT_toolshelf_gn_add_output(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeViewer",
            "GeometryNodeWarning",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Geometry"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeGeometryToInstance",
            "GeometryNodeJoinGeometry",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_geometry_sample(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_geometry_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeSetGeometryName",
            "GeometryNodeSetID",
            "GeometryNodeSetPosition",
            OperatorEntry("GeometryNodeToolSetSelection", should_draw=is_tool_tree(context)),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_curve(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Curve"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_curve_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_curve_sample(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeSampleCurve",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_curve_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_curve_primitives(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Primitives"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_curve_topology(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Topology"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeCurveOfPoint",
            "GeometryNodeOffsetPointInCurve",
            "GeometryNodePointsOfCurve",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_grease_pencil(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Grease Pencil"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_grease_pencil_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_grease_pencil"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeInputNamedLayerSelection",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_grease_pencil_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_grease_pencil"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeSetGreasePencilColor",
            "GeometryNodeSetGreasePencilDepth",
            "GeometryNodeSetGreasePencilSoftness",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_grease_pencil_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_grease_pencil"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeGreasePencilToCurves",
            "GeometryNodeMergeLayers",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_instances(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Instances"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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
            "GeometryNodeInputInstanceBounds"
            "GeometryNodeInstanceTransform",
            "GeometryNodeInputInstanceRotation",
            "GeometryNodeInputInstanceScale",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mesh"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_mesh_read(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_mesh_sample(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeSampleNearestSurface",
            "GeometryNodeSampleUVSurface",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_write(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("GeometryNodeToolSetFaceSet", should_draw=is_tool_tree(context)),
            "GeometryNodeSetMeshNormal",
            "GeometryNodeSetShadeSmooth",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_operations(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_mesh_primitives(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Primitives"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_mesh_topology(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Topology"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_mesh_uv(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "UV"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeUVPackIslands",
            "GeometryNodeUVUnwrap",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_point(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Point"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_volume(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Volume"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeVolumeCube",
            "GeometryNodeVolumeToMesh",
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_simulation(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Simulation"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry(operator="node.add_simulation_zone", text="Simulation Zone", icon="TIME"),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_material(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Material"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_texture(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Texture"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Utilities"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities_color(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Color"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities_text(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Text"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities_vector(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities_field(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Field"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "GeometryNodeAccumulateField",
            "GeometryNodeFieldAtIndex",
            "GeometryNodeFieldOnDomain",
            "GeometryNodeFieldAverage",
            "GeometryNodeFieldMinAndMax",
            "GeometryNodeFieldVariance"
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_math(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Math"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "FunctionNodeBitMath",
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


class NODES_PT_toolshelf_gn_add_utilities_matrix(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Matrix"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities_rotation(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Rotation"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

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


class NODES_PT_toolshelf_gn_add_utilities_deprecated(bpy.types.Panel, NodePanel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Deprecated"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        entries = (
            "FunctionNodeAlignEulerToVector",
            "FunctionNodeRotateEuler",
        )

        self.draw_entries(context, layout, entries)


classes = (
    #-----------------------
    # Display Properties
    NODES_PT_toolshelf_display_settings_add,
    NODES_PT_toolshelf_display_settings_relations,
    #-----------------------

    #-----------------------
    # Relations Tab Panels
    NODES_PT_relations_group_operations,
    NODES_PT_relations_nodegroups,
    NODES_PT_relations_layout,
    #-----------------------

    #-----------------------
    # Shader Nodes - Add
    NODES_PT_toolshelf_shader_add_input,
    NODES_PT_toolshelf_shader_add_output,
    NODES_PT_toolshelf_shader_add_shader,
    NODES_PT_toolshelf_shader_add_texture,
    NODES_PT_toolshelf_shader_add_color,
    NODES_PT_toolshelf_shader_add_vector,
    NODES_PT_toolshelf_shader_add_converter,
    NODES_PT_toolshelf_shader_add_script,
    #-----------------------

    #-----------------------
    # Compositor Nodes - Add
    NODES_PT_toolshelf_compositor_add_input,
    NODES_PT_toolshelf_compositor_add_input_constant,
    NODES_PT_toolshelf_compositor_add_input_scene,
    NODES_PT_toolshelf_compositor_add_output,
    NODES_PT_toolshelf_compositor_add_color,
    NODES_PT_toolshelf_compositor_add_color_adjust,
    NODES_PT_toolshelf_compositor_add_color_mix,
    NODES_PT_toolshelf_compositor_add_filter,
    NODES_PT_toolshelf_compositor_add_filter_blur,
    NODES_PT_toolshelf_compositor_add_keying,
    NODES_PT_toolshelf_compositor_add_mask,
    NODES_PT_toolshelf_compositor_add_texture,
    NODES_PT_toolshelf_compositor_add_tracking,
    NODES_PT_toolshelf_compositor_add_transform,
    NODES_PT_toolshelf_compositor_add_utility,
    NODES_PT_toolshelf_compositor_add_vector,
    #-----------------------

    #-----------------------
    # Texture Nodes - Add
    NODES_PT_toolshelf_texture_add_input,
    NODES_PT_toolshelf_texture_add_output,
    NODES_PT_toolshelf_texture_add_color,
    NODES_PT_toolshelf_texture_add_converter,
    NODES_PT_toolshelf_texture_add_distort,
    NODES_PT_toolshelf_texture_add_pattern,
    NODES_PT_toolshelf_texture_add_texture,
    #-----------------------


    #-----------------------
    # Geometry Nodes - Add
    NODES_PT_toolshelf_gn_add_attribute,

    NODES_PT_toolshelf_gn_add_input,
    NODES_PT_toolshelf_gn_add_input_constant,
    NODES_PT_toolshelf_gn_add_input_gizmo,
    NODES_PT_toolshelf_gn_add_input_file,
    NODES_PT_toolshelf_gn_add_input_scene,

    NODES_PT_toolshelf_gn_add_output,

    NODES_PT_toolshelf_gn_add_geometry,
    NODES_PT_toolshelf_gn_add_geometry_read,
    NODES_PT_toolshelf_gn_add_geometry_sample,
    NODES_PT_toolshelf_gn_add_geometry_write,
    NODES_PT_toolshelf_gn_add_geometry_operations,

    NODES_PT_toolshelf_gn_add_curve,
    NODES_PT_toolshelf_gn_add_curve_read,
    NODES_PT_toolshelf_gn_add_curve_sample,
    NODES_PT_toolshelf_gn_add_curve_write,
    NODES_PT_toolshelf_gn_add_curve_operations,
    NODES_PT_toolshelf_gn_add_curve_primitives,
    NODES_PT_toolshelf_gn_add_curve_topology,

    NODES_PT_toolshelf_gn_add_grease_pencil,
    NODES_PT_toolshelf_gn_add_grease_pencil_read,
    NODES_PT_toolshelf_gn_add_grease_pencil_write,
    NODES_PT_toolshelf_gn_add_grease_pencil_operations,

    NODES_PT_toolshelf_gn_add_instances,

    NODES_PT_toolshelf_gn_add_mesh,
    NODES_PT_toolshelf_gn_add_mesh_read,
    NODES_PT_toolshelf_gn_add_mesh_sample,
    NODES_PT_toolshelf_gn_add_mesh_write,
    NODES_PT_toolshelf_gn_add_mesh_operations,
    NODES_PT_toolshelf_gn_add_mesh_primitives,
    NODES_PT_toolshelf_gn_add_mesh_topology,
    NODES_PT_toolshelf_gn_add_mesh_uv,

    NODES_PT_toolshelf_gn_add_point,
    NODES_PT_toolshelf_gn_add_volume,
    NODES_PT_toolshelf_gn_add_simulation,
    NODES_PT_toolshelf_gn_add_material,
    NODES_PT_toolshelf_gn_add_texture,

    NODES_PT_toolshelf_gn_add_utilities,
    NODES_PT_toolshelf_gn_add_utilities_color,
    NODES_PT_toolshelf_gn_add_utilities_text,
    NODES_PT_toolshelf_gn_add_utilities_vector,
    NODES_PT_toolshelf_gn_add_utilities_field,
    NODES_PT_toolshelf_gn_add_utilities_math,
    NODES_PT_toolshelf_gn_add_utilities_matrix,
    NODES_PT_toolshelf_gn_add_utilities_rotation,
    NODES_PT_toolshelf_gn_add_utilities_deprecated,
    #-----------------------
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

