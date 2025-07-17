# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy import context
from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
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
    def draw_text_button(layout, node=None, operator="node.add_node", text="", icon=None, settings=None, pad=0, **kwargs):
        # Determine icon automatically from node bl_rna when adding non-zone nodes and no icon is specified
        if operator == "node.add_node":
            bl_rna = bpy.types.Node.bl_rna_get_subclass(node)
            if icon is None:
                icon = getattr(bl_rna, "icon", "NONE")

            if text == "":
                text = getattr(bl_rna, "name", iface_("Unknown"))

        if text != "" and pad > 0:
            text = " " + text.strip().ljust(pad)
        
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
    def draw_icon_button(layout, node=None, operator="node.add_node", icon=None, settings=None, **kwargs):
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        engine = context.engine
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

        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
        engine = context.engine

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

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
        layout = self.layout#### Textbuttons
        default_context = bpy.app.translations.contexts.default

        scene = context.scene
        engine = context.engine

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene
        engine = context.engine
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
                self.draw_text_button(col, "NodeGroupInput")
                self.draw_text_button(col, "NodeGroupOutput")


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
            self.draw_text_button(col, "NodeFrame")
            self.draw_text_button(col, "NodeReroute")

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
            self.draw_text_button(col, "GeometryNodeAttributeStatistic")
            self.draw_text_button(col, "GeometryNodeAttributeDomainSize")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeBlurAttribute")
            self.draw_text_button(col, "GeometryNodeCaptureAttribute")
            self.draw_text_button(col, "GeometryNodeRemoveAttribute")
            self.draw_text_button(col, "GeometryNodeStoreNamedAttribute")

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
            self.draw_text_button(col, "FunctionNodeInputBool")
            self.draw_text_button(col, "GeometryNodeInputCollection")
            self.draw_text_button(col, "FunctionNodeInputColor")
            self.draw_text_button(col, "GeometryNodeInputImage")
            self.draw_text_button(col, "FunctionNodeInputInt")
            self.draw_text_button(col, "GeometryNodeInputMaterial")
            self.draw_text_button(col, "GeometryNodeInputObject")
            self.draw_text_button(col, "FunctionNodeInputRotation")
            self.draw_text_button(col, "FunctionNodeInputString")
            self.draw_text_button(col, "ShaderNodeValue")
            self.draw_text_button(col, "FunctionNodeInputVector")

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
            self.draw_text_button(col, "GeometryNodeGizmoDial")
            self.draw_text_button(col, "GeometryNodeGizmoLinear")
            self.draw_text_button(col, "GeometryNodeGizmoTransform")

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
            self.draw_text_button(col, "GeometryNodeImportOBJ")
            self.draw_text_button(col, "GeometryNodeImportPLY")
            self.draw_text_button(col, "GeometryNodeImportSTL")
            self.draw_text_button(col, "GeometryNodeImportCSV")
            self.draw_text_button(col, "GeometryNodeImportText")
            self.draw_text_button(col, "GeometryNodeImportVDB")

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

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeTool3DCursor")
            self.draw_text_button(col, "GeometryNodeInputActiveCamera")
            self.draw_text_button(col, "GeometryNodeCameraInfo")
            self.draw_text_button(col, "GeometryNodeCollectionInfo")
            self.draw_text_button(col, "GeometryNodeImageInfo")
            self.draw_text_button(col, "GeometryNodeIsViewport")
            self.draw_text_button(col, "GeometryNodeInputNamedLayerSelection")

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeToolMousePosition")
            self.draw_text_button(col, "GeometryNodeObjectInfo")
            self.draw_text_button(col, "GeometryNodeInputSceneTime")
            self.draw_text_button(col, "GeometryNodeSelfObject")

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeViewportTransform")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if is_tool_tree(context):
                self.draw_icon_button(flow, "GeometryNodeTool3DCursor")
            self.draw_icon_button(flow, "GeometryNodeInputActiveCamera")
            self.draw_icon_button(flow, "GeometryNodeCameraInfo")
            self.draw_icon_button(flow, "GeometryNodeCollectionInfo")
            self.draw_icon_button(flow, "GeometryNodeImageInfo")
            self.draw_icon_button(flow, "GeometryNodeIsViewport")
            self.draw_icon_button(flow, "GeometryNodeInputNamedLayerSelection")

            if is_tool_tree(context):
                self.draw_icon_button(flow, "GeometryNodeToolMousePosition")
            self.draw_icon_button(flow, "GeometryNodeObjectInfo")
            self.draw_icon_button(flow, "GeometryNodeInputSceneTime")
            self.draw_icon_button(flow, "GeometryNodeSelfObject")

            if is_tool_tree(context):
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
            self.draw_text_button(col, "GeometryNodeViewer")
            self.draw_text_button(col, "GeometryNodeWarning")

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
            self.draw_text_button(col, "GeometryNodeGeometryToInstance")
            self.draw_text_button(col, "GeometryNodeJoinGeometry")

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
            self.draw_text_button(col, "GeometryNodeInputID")
            self.draw_text_button(col, "GeometryNodeInputIndex")
            self.draw_text_button(col, "GeometryNodeInputNamedAttribute")
            self.draw_text_button(col, "GeometryNodeInputNormal")
            self.draw_text_button(col, "GeometryNodeInputPosition")
            self.draw_text_button(col, "GeometryNodeInputRadius")

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeToolSelection")
                self.draw_text_button(col, "GeometryNodeToolActiveElement")

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

            if is_tool_tree(context):
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
            self.draw_text_button(col, "GeometryNodeProximity")
            self.draw_text_button(col, "GeometryNodeIndexOfNearest")
            self.draw_text_button(col, "GeometryNodeRaycast")
            self.draw_text_button(col, "GeometryNodeSampleIndex")
            self.draw_text_button(col, "GeometryNodeSampleNearest")

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
            self.draw_text_button(col, "GeometryNodeSetGeometryName")
            self.draw_text_button(col, "GeometryNodeSetID")
            self.draw_text_button(col, "GeometryNodeSetPosition")

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeToolSetSelection")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5
            self.draw_icon_button(flow, "GeometryNodeSetGeometryName")
            self.draw_icon_button(flow, "GeometryNodeSetID")
            self.draw_icon_button(flow, "GeometryNodeSetPosition")

            if is_tool_tree(context):
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
            self.draw_text_button(col, "GeometryNodeBake")
            self.draw_text_button(col, "GeometryNodeBoundBox")
            self.draw_text_button(col, "GeometryNodeConvexHull")
            self.draw_text_button(col, "GeometryNodeDeleteGeometry")
            self.draw_text_button(col, "GeometryNodeDuplicateElements")
            self.draw_text_button(col, "GeometryNodeMergeByDistance")
            self.draw_text_button(col, "GeometryNodeSortElements")
            self.draw_text_button(col, "GeometryNodeTransform")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeSeparateComponents")
            self.draw_text_button(col, "GeometryNodeSeparateGeometry")
            self.draw_text_button(col, "GeometryNodeSplitToInstances")

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
            self.draw_text_button(col, "GeometryNodeInputCurveHandlePositions")
            self.draw_text_button(col, "GeometryNodeCurveLength")
            self.draw_text_button(col, "GeometryNodeInputTangent")
            self.draw_text_button(col, "GeometryNodeInputCurveTilt")
            self.draw_text_button(col, "GeometryNodeCurveEndpointSelection")
            self.draw_text_button(col, "GeometryNodeCurveHandleTypeSelection")
            self.draw_text_button(col, "GeometryNodeInputSplineCyclic")
            self.draw_text_button(col, "GeometryNodeSplineLength")
            self.draw_text_button(col, "GeometryNodeSplineParameter")
            self.draw_text_button(col, "GeometryNodeInputSplineResolution")

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
            self.draw_text_button(col, "GeometryNodeSampleCurve")

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
            self.draw_text_button(col, "GeometryNodeSetCurveNormal")
            self.draw_text_button(col, "GeometryNodeSetCurveRadius")
            self.draw_text_button(col, "GeometryNodeSetCurveTilt")
            self.draw_text_button(col, "GeometryNodeSetCurveHandlePositions")
            self.draw_text_button(col, "GeometryNodeCurveSetHandles")
            self.draw_text_button(col, "GeometryNodeSetSplineCyclic")
            self.draw_text_button(col, "GeometryNodeSetSplineResolution")
            self.draw_text_button(col, "GeometryNodeCurveSplineType")

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
            self.draw_text_button(col, "GeometryNodeCurvesToGreasePencil")
            self.draw_text_button(col, "GeometryNodeCurveToMesh")
            self.draw_text_button(col, "GeometryNodeCurveToPoints")
            self.draw_text_button(col, "GeometryNodeDeformCurvesOnSurface")
            self.draw_text_button(col, "GeometryNodeFillCurve")
            self.draw_text_button(col, "GeometryNodeFilletCurve")
            self.draw_text_button(col, "GeometryNodeGreasePencilToCurves")
            self.draw_text_button(col, "GeometryNodeInterpolateCurves")
            self.draw_text_button(col, "GeometryNodeInterpolateCurves")
            self.draw_text_button(col, "GeometryNodeResampleCurve")
            self.draw_text_button(col, "GeometryNodeReverseCurve")
            self.draw_text_button(col, "GeometryNodeSubdivideCurve")
            self.draw_text_button(col, "GeometryNodeTrimCurve")

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
            self.draw_text_button(col, "GeometryNodeCurveArc")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveBezierSegment")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveCircle")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveLine")
            self.draw_text_button(col, "GeometryNodeCurveSpiral")
            self.draw_text_button(col, "GeometryNodeCurveQuadraticBezier")
            self.draw_text_button(col, "GeometryNodeCurvePrimitiveQuadrilateral")
            self.draw_text_button(col, "GeometryNodeCurveStar")

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
            self.draw_text_button(col, "GeometryNodeCurveOfPoint")
            self.draw_text_button(col, "GeometryNodeOffsetPointInCurve")
            self.draw_text_button(col, "GeometryNodePointsOfCurve")

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
            self.draw_text_button(col, "GeometryNodeInputNamedLayerSelection")

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
            self.draw_text_button(col, "GeometryNodeSetGreasePencilColor")
            self.draw_text_button(col, "GeometryNodeSetGreasePencilDepth")
            self.draw_text_button(col, "GeometryNodeSetGreasePencilSoftness")

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
            self.draw_text_button(col, "GeometryNodeGreasePencilToCurves")
            self.draw_text_button(col, "GeometryNodeMergeLayers")

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
            self.draw_text_button(col, "GeometryNodeInstanceOnPoints")
            self.draw_text_button(col, "GeometryNodeInstancesToPoints")
            self.draw_text_button(col, "GeometryNodeRealizeInstances")
            self.draw_text_button(col, "GeometryNodeRotateInstances")
            self.draw_text_button(col, "GeometryNodeScaleInstances")
            self.draw_text_button(col, "GeometryNodeTranslateInstances")
            self.draw_text_button(col, "GeometryNodeSetInstanceTransform")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeInstanceTransform")
            self.draw_text_button(col, "GeometryNodeInputInstanceRotation")
            self.draw_text_button(col, "GeometryNodeInputInstanceScale")

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
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeAngle")
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeNeighbors")
            self.draw_text_button(col, "GeometryNodeInputMeshEdgeVertices")
            self.draw_text_button(col, "GeometryNodeEdgesToFaceGroups")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceArea")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshFaceSetBoundaries")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceNeighbors")

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeToolFaceSet")
            self.draw_text_button(col, "GeometryNodeInputMeshFaceIsPlanar")
            self.draw_text_button(col, "GeometryNodeInputShadeSmooth")
            self.draw_text_button(col, "GeometryNodeInputEdgeSmooth")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeInputMeshIsland")
            self.draw_text_button(col, "GeometryNodeInputShortestEdgePaths")
            self.draw_text_button(col, "GeometryNodeInputMeshVertexNeighbors")

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

            if is_tool_tree(context):
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
            self.draw_text_button(col, "GeometryNodeSampleNearestSurface")
            self.draw_text_button(col, "GeometryNodeSampleUVSurface")

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

            if is_tool_tree(context):
                self.draw_text_button(col, "GeometryNodeToolFaceSet")
            self.draw_text_button(col, "GeometryNodeSetMeshNormal")
            self.draw_text_button(col, "GeometryNodeSetShadeSmooth")

        #### Icon Buttons

        else:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            if is_tool_tree(context):
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
            self.draw_text_button(col, "GeometryNodeDualMesh")
            self.draw_text_button(col, "GeometryNodeEdgePathsToCurves")
            self.draw_text_button(col, "GeometryNodeEdgePathsToSelection")
            self.draw_text_button(col, "GeometryNodeExtrudeMesh")
            self.draw_text_button(col, "GeometryNodeFlipFaces")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshBoolean")
            self.draw_text_button(col, "GeometryNodeMeshToCurve")
            self.draw_text_button(col, "GeometryNodeMeshToPoints")
            self.draw_text_button(col, "GeometryNodeMeshToVolume")
            self.draw_text_button(col, "GeometryNodeScaleElements")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeSplitEdges")
            self.draw_text_button(col, "GeometryNodeSubdivideMesh")
            self.draw_text_button(col, "GeometryNodeSubdivisionSurface")
            self.draw_text_button(col, "GeometryNodeTriangulate")


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
            self.draw_text_button(col, "GeometryNodeMeshCone")
            self.draw_text_button(col, "GeometryNodeMeshCube")
            self.draw_text_button(col, "GeometryNodeMeshCylinder")
            self.draw_text_button(col, "GeometryNodeMeshGrid")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeMeshIcoSphere")
            self.draw_text_button(col, "GeometryNodeMeshCircle")
            self.draw_text_button(col, "GeometryNodeMeshLine")
            self.draw_text_button(col, "GeometryNodeMeshUVSphere")

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
            self.draw_text_button(col, "GeometryNodeCornersOfEdge")
            self.draw_text_button(col, "GeometryNodeCornersOfFace")
            self.draw_text_button(col, "GeometryNodeCornersOfVertex")
            self.draw_text_button(col, "GeometryNodeEdgesOfCorner")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodeEdgesOfVertex")
            self.draw_text_button(col, "GeometryNodeFaceOfCorner")
            self.draw_text_button(col, "GeometryNodeOffsetCornerInFace")
            self.draw_text_button(col, "GeometryNodeVertexOfCorner")

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
            self.draw_text_button(col, "GeometryNodeUVPackIslands")
            self.draw_text_button(col, "GeometryNodeUVUnwrap")

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
            self.draw_text_button(col, "GeometryNodeDistributePointsInVolume")
            self.draw_text_button(col, "GeometryNodeDistributePointsOnFaces")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "GeometryNodePoints")
            self.draw_text_button(col, "GeometryNodePointsToCurves")
            self.draw_text_button(col, "GeometryNodePointsToVertices")
            self.draw_text_button(col, "GeometryNodePointsToVolume")
            self.draw_text_button(col, "GeometryNodeSetPointRadius")

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
            self.draw_text_button(col, "GeometryNodeVolumeCube")
            self.draw_text_button(col, "GeometryNodeVolumeToMesh")

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
            self.draw_text_button(col, "GeometryNodeReplaceMaterial")
            self.draw_text_button(col, "GeometryNodeInputMaterialIndex")
            self.draw_text_button(col, "GeometryNodeMaterialSelection")
            self.draw_text_button(col, "GeometryNodeSetMaterial")
            self.draw_text_button(col, "GeometryNodeSetMaterialIndex")

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
            self.draw_text_button(col, "ShaderNodeTexBrick")
            self.draw_text_button(col, "ShaderNodeTexChecker")
            self.draw_text_button(col, "ShaderNodeTexGradient")
            self.draw_text_button(col, "GeometryNodeImageTexture")
            self.draw_text_button(col, "ShaderNodeTexMagic")
            self.draw_text_button(col, "ShaderNodeTexNoise")
            self.draw_text_button(col, "ShaderNodeTexVoronoi")
            self.draw_text_button(col, "ShaderNodeTexWave")
            self.draw_text_button(col, "ShaderNodeTexWhiteNoise")

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
            self.draw_text_button(col, "GeometryNodeIndexSwitch")
            self.draw_text_button(col, "GeometryNodeMenuSwitch")
            self.draw_text_button(col, "FunctionNodeRandomValue")
            self.draw_text_button(col, operator="node.add_repeat_zone", text="Repeat Zone", icon="REPEAT")
            self.draw_text_button(col, "GeometryNodeSwitch")

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
            self.draw_text_button(col, "ShaderNodeValToRGB")
            self.draw_text_button(col, "ShaderNodeRGBCurve")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "FunctionNodeCombineColor")
            self.draw_text_button(col, "FunctionNodeSeparateColor")

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
            self.draw_text_button(col, "FunctionNodeFormatString")
            self.draw_text_button(col, "GeometryNodeStringJoin")
            self.draw_text_button(col, "FunctionNodeMatchString")
            self.draw_text_button(col, "FunctionNodeReplaceString")
            self.draw_text_button(col, "FunctionNodeSliceString")
            self.draw_text_button(col, "FunctionNodeStringLength")
            self.draw_text_button(col, "FunctionNodeFindInString")
            self.draw_text_button(col, "GeometryNodeStringToCurves")
            self.draw_text_button(col, "FunctionNodeValueToString")
            self.draw_text_button(col, "FunctionNodeInputSpecialCharacters")

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
            self.draw_text_button(col, "ShaderNodeVectorCurve")
            self.draw_text_button(col, "ShaderNodeVectorMath")
            self.draw_text_button(col, "ShaderNodeVectorRotate")
            self.draw_text_button(col, "ShaderNodeCombineXYZ")
            self.draw_text_button(col, "ShaderNodeMix", settings={"data_type": "'VECTOR'"})
            self.draw_text_button(col, "ShaderNodeSeparateXYZ")

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
            self.draw_text_button(col, "GeometryNodeAccumulateField")
            self.draw_text_button(col, "GeometryNodeFieldAtIndex")
            self.draw_text_button(col, "GeometryNodeFieldOnDomain")

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
            self.draw_text_button(col, "FunctionNodeBooleanMath")
            self.draw_text_button(col, "FunctionNodeIntegerMath")
            self.draw_text_button(col, "ShaderNodeClamp")
            self.draw_text_button(col, "FunctionNodeCompare")
            self.draw_text_button(col, "ShaderNodeFloatCurve")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "FunctionNodeFloatToInt")
            self.draw_text_button(col, "FunctionNodeHashValue")
            self.draw_text_button(col, "ShaderNodeMapRange")
            self.draw_text_button(col, "ShaderNodeMath")
            self.draw_text_button(col, "ShaderNodeMix")

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
            self.draw_text_button(col, "FunctionNodeCombineMatrix")
            self.draw_text_button(col, "FunctionNodeCombineTransform")
            self.draw_text_button(col, "FunctionNodeMatrixDeterminant")
            self.draw_text_button(col, "FunctionNodeInvertMatrix")
            self.draw_text_button(col, "FunctionNodeMatrixMultiply")
            self.draw_text_button(col, "FunctionNodeProjectPoint")
            self.draw_text_button(col, "FunctionNodeSeparateMatrix")
            self.draw_text_button(col, "FunctionNodeSeparateTransform")
            self.draw_text_button(col, "FunctionNodeTransformDirection")
            self.draw_text_button(col, "FunctionNodeTransformPoint")
            self.draw_text_button(col, "FunctionNodeTransposeMatrix")

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
            self.draw_text_button(col, "FunctionNodeAlignRotationToVector")
            self.draw_text_button(col, "FunctionNodeAxesToRotation")
            self.draw_text_button(col, "FunctionNodeAxisAngleToRotation")
            self.draw_text_button(col, "FunctionNodeEulerToRotation")
            self.draw_text_button(col, "FunctionNodeInvertRotation")
            self.draw_text_button(col, "FunctionNodeRotateRotation")
            self.draw_text_button(col, "FunctionNodeRotateVector")
            self.draw_text_button(col, "FunctionNodeRotationToAxisAngle")
            self.draw_text_button(col, "FunctionNodeRotationToEuler")
            self.draw_text_button(col, "FunctionNodeRotationToQuaternion")
            self.draw_text_button(col, "FunctionNodeQuaternionToRotation")

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
            self.draw_text_button(col, "FunctionNodeAlignEulerToVector")
            self.draw_text_button(col, "FunctionNodeRotateEuler")

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
            self.draw_text_button(col, "ShaderNodeFresnel")
            self.draw_text_button(col, "ShaderNodeNewGeometry")
            self.draw_text_button(col, "ShaderNodeRGB")
            self.draw_text_button(col, "ShaderNodeTexCoord")

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

        #### Icon Buttons

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
            self.draw_text_button(col, "ShaderNodeTexEnvironment")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexImage")
            self.draw_text_button(col, "ShaderNodeTexNoise")

            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeTexSky")
            self.draw_text_button(col, "ShaderNodeTexVoronoi")


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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene

        ##### Textbuttons

        if not addon_prefs.Node_text_or_icon:
            col = layout.column(align=True)
            col.scale_y = 1.5
            self.draw_text_button(col, "ShaderNodeMapping")
            self.draw_text_button(col, "ShaderNodeNormal")
            self.draw_text_button(col, "ShaderNodeNormalMap")

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
        default_context = bpy.app.translations.contexts.default

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        scene = context.scene

        ##### Textbuttons

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
    NODES_PT_shader_comp_textoricon_shader_add,
    NODES_PT_shader_comp_textoricon_compositor_add,
    NODES_PT_shader_comp_textoricon_relations,
    NODES_PT_geom_textoricon_add,
    NODES_PT_geom_textoricon_relations,
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

