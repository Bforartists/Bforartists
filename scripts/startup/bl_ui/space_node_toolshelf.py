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


@dataclasses.dataclass(slots=True)
class OperatorEntry:
    node : str = None
    operator : str = "node.add_node"
    text : str = ""
    icon : str = None
    props : dict = None
    settings : dict = None
    should_draw : bool = True

    as_dict = dataclasses.asdict

    def __post_init__(self):
        is_add_node_operator = (self.operator == "node.add_node")
        
        # Determine icon automatically from node bl_rna when adding non-zone nodes and no icon is specified
        if is_add_node_operator:
            bl_rna = bpy.types.Node.bl_rna_get_subclass(self.node)
            if self.icon is None:
                self.icon = getattr(bl_rna, "icon", "NONE")

            if self.text == "":
                self.text = getattr(bl_rna, "name", iface_("Unknown"))

    def __len__(self):
        return len(self.text)


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
    

def calculate_padding(items):
    lengths = []

    for i in items:
        if isinstance(i, OperatorEntry):
            lengths.append(len(i))
        
    return max(lengths)


class NodePanel:
    @staticmethod
    def draw_text_button(layout, node=None, operator="node.add_node", text="", icon=None, settings=None, props=None, pad=0, **kwargs):
        if text != "" and pad > 0:
            # This scaled_padding was derived just by trying different values and testing what works
            scaled_padding = int(((pad - len(text)) * 1.35) + len(text))
            text = " " + text.strip().ljust(scaled_padding)
        
        if (operator == "node.add_node") or (text != ""):
            props = layout.operator(operator, text=text, icon=icon)
        else:    
            props = layout.operator(operator, icon=icon)
        
        if hasattr(props, "use_transform"):
            props.use_transform = True

        if props is not None:
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
        props = layout.operator(operator, text="", icon=icon)
        props.use_transform = True

        if props is not None:
            for prop_key, prop_value in props.items():
                setattr(props, prop_key, prop_value)

        if node is not None:
            props.type = node

        if settings is not None:
            for name, value in settings.items():
                ops = props.settings.add()
                ops.name = name
                ops.value = value

    def draw_entries(self, context, layout, entries, pad=0):
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
                        self.draw_text_button(col, pad=pad, **entry.as_dict())
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
                OperatorEntry("ShaderNodeFresnel"),
                OperatorEntry("ShaderNodeNewGeometry"),
                OperatorEntry("ShaderNodeRGB"),
                OperatorEntry("ShaderNodeTexCoord"),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeAmbientOcclusion"),
                OperatorEntry("ShaderNodeAttribute"),
                OperatorEntry("ShaderNodeBevel"),
                OperatorEntry("ShaderNodeCameraData"),
                OperatorEntry("ShaderNodeVertexColor"),
                OperatorEntry("ShaderNodeFresnel"),
                Separator,
                OperatorEntry("ShaderNodeNewGeometry"),
                OperatorEntry("ShaderNodeHairInfo"),
                OperatorEntry("ShaderNodeLayerWeight"),
                OperatorEntry("ShaderNodeLightPath"),
                OperatorEntry("ShaderNodeObjectInfo"),
                Separator,
                OperatorEntry("ShaderNodeParticleInfo"),
                OperatorEntry("ShaderNodePointInfo"),
                OperatorEntry("ShaderNodeRGB"),
                OperatorEntry("ShaderNodeTangent"),
                OperatorEntry("ShaderNodeTexCoord"),
                OperatorEntry("ShaderNodeUVAlongStroke", should_draw=is_shader_type(context, 'LINESTYLE')),
                Separator,
                OperatorEntry("ShaderNodeUVMap"),
                OperatorEntry("ShaderNodeValue"),
                OperatorEntry("ShaderNodeVolumeInfo"),
                OperatorEntry("ShaderNodeWireframe"),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
                OperatorEntry("ShaderNodeOutputAOV"),
                OperatorEntry("ShaderNodeOutputLight", should_draw=is_object_shader and is_cycles),
                OperatorEntry("ShaderNodeOutputMaterial", should_draw=is_object_shader),
                OperatorEntry("ShaderNodeOutputWorld", should_draw=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeOutputLineStyle", should_draw=is_shader_type(context, 'LINESTYLE')),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeBokehImage"),
            OperatorEntry("CompositorNodeImage"),
            OperatorEntry("CompositorNodeImageInfo"),
            OperatorEntry("CompositorNodeImageCoordinates"),
            OperatorEntry("CompositorNodeMask"),
            OperatorEntry("CompositorNodeMovieClip"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeRGB"),
            OperatorEntry("ShaderNodeValue"),
            OperatorEntry("CompositorNodeNormal"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeRLayers"),
            OperatorEntry("CompositorNodeSceneTime"),
            OperatorEntry("CompositorNodeTime"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeComposite"),
            OperatorEntry("CompositorNodeViewer"),
            Separator,
            OperatorEntry("CompositorNodeOutputFile"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodePremulKey"),
            OperatorEntry("ShaderNodeBlackbody"),
            OperatorEntry("ShaderNodeValToRGB"),
            OperatorEntry("CompositorNodeConvertColorSpace"),
            OperatorEntry("CompositorNodeSetAlpha"),
            Separator,
            OperatorEntry("CompositorNodeInvert"),
            OperatorEntry("CompositorNodeRGBToBW"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeBrightContrast"),
            OperatorEntry("CompositorNodeColorBalance"),
            OperatorEntry("CompositorNodeColorCorrection"),

            OperatorEntry("CompositorNodeExposure"),
            OperatorEntry("CompositorNodeGamma"),
            OperatorEntry("CompositorNodeHueCorrect"),
            OperatorEntry("CompositorNodeHueSat"),
            OperatorEntry("CompositorNodeCurveRGB"),
            OperatorEntry("CompositorNodeTonemap"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeAlphaOver"),
            Separator,
            OperatorEntry("CompositorNodeCombineColor"),
            OperatorEntry("CompositorNodeSeparateColor"),
            Separator,
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Color"), settings={"data_type": "'RGBA'"}),
            OperatorEntry("CompositorNodeZcombine"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeAntiAliasing"),
            OperatorEntry("CompositorNodeDenoise"),
            OperatorEntry("CompositorNodeDespeckle"),
            Separator,
            OperatorEntry("CompositorNodeDilateErode"),
            OperatorEntry("CompositorNodeInpaint"),
            Separator,
            OperatorEntry("CompositorNodeFilter"),
            OperatorEntry("CompositorNodeGlare"),
            OperatorEntry("CompositorNodeKuwahara"),
            OperatorEntry("CompositorNodePixelate"),
            OperatorEntry("CompositorNodePosterize"),
            OperatorEntry("CompositorNodeSunBeams"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeBilateralblur"),
            OperatorEntry("CompositorNodeBlur"),
            OperatorEntry("CompositorNodeBokehBlur"),
            OperatorEntry("CompositorNodeDefocus"),
            OperatorEntry("CompositorNodeDBlur"),
            OperatorEntry("CompositorNodeVecBlur"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeChannelMatte"),
            OperatorEntry("CompositorNodeChromaMatte"),
            OperatorEntry("CompositorNodeColorMatte"),
            OperatorEntry("CompositorNodeColorSpill"),
            OperatorEntry("CompositorNodeDiffMatte"),
            OperatorEntry("CompositorNodeDistanceMatte"),
            OperatorEntry("CompositorNodeKeying"),
            OperatorEntry("CompositorNodeKeyingScreen"),
            OperatorEntry("CompositorNodeLumaMatte"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeCryptomatteV2"),
            OperatorEntry("CompositorNodeCryptomatte"),
            Separator,
            OperatorEntry("CompositorNodeBoxMask"),
            OperatorEntry("CompositorNodeEllipseMask"),
            Separator,
            OperatorEntry("CompositorNodeDoubleEdgeMask"),
            OperatorEntry("CompositorNodeIDMask"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeTexBrick"),
            OperatorEntry("ShaderNodeTexChecker"),
            OperatorEntry("ShaderNodeTexGabor"),
            OperatorEntry("ShaderNodeTexGradient"),
            OperatorEntry("ShaderNodeTexMagic"),
            OperatorEntry("ShaderNodeTexNoise"),
            OperatorEntry("ShaderNodeTexVoronoi"),
            OperatorEntry("ShaderNodeTexWave"),
            OperatorEntry("ShaderNodeTexWhiteNoise"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodePlaneTrackDeform"),
            OperatorEntry("CompositorNodeStabilize"),
            OperatorEntry("CompositorNodeTrackPos"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("CompositorNodeRotate"),
            OperatorEntry("CompositorNodeScale"),
            OperatorEntry("CompositorNodeTransform"),
            OperatorEntry("CompositorNodeTranslate"),
            Separator,
            OperatorEntry("CompositorNodeCornerPin"),
            OperatorEntry("CompositorNodeCrop"),
            Separator,
            OperatorEntry("CompositorNodeDisplace"),
            OperatorEntry("CompositorNodeFlip"),
            OperatorEntry("CompositorNodeMapUV"),
            Separator,
            OperatorEntry("CompositorNodeLensdist"),
            OperatorEntry("CompositorNodeMovieDistortion"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeMapRange"),
            OperatorEntry("ShaderNodeMath"),
            OperatorEntry("ShaderNodeMix"),
            OperatorEntry("ShaderNodeClamp"),
            OperatorEntry("ShaderNodeFloatCurve"),
            Separator,
            OperatorEntry("CompositorNodeLevels"),
            OperatorEntry("CompositorNodeNormalize"),
            Separator,
            OperatorEntry("CompositorNodeSplit"),
            OperatorEntry("CompositorNodeSwitch"),
            OperatorEntry("CompositorNodeSwitchView", text="Switch Stereo View"),
            Separator,
            OperatorEntry("CompositorNodeRelativeToPixel"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeCombineXYZ"),
            OperatorEntry("ShaderNodeSeparateXYZ"),
            Separator,
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), settings={"data_type": "'VECTOR'"}),
            OperatorEntry("ShaderNodeVectorCurve"),
            OperatorEntry("ShaderNodeVectorMath"),
            OperatorEntry("ShaderNodeVectorRotate"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeCoordinates"),
            OperatorEntry("TextureNodeCurveTime"),
            OperatorEntry("TextureNodeImage"),
            OperatorEntry("TextureNodeTexture"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeTexBlend"),
            OperatorEntry("TextureNodeTexClouds"),
            OperatorEntry("TextureNodeTexDistNoise"),
            OperatorEntry("TextureNodeTexMagic"),
            Separator,
            OperatorEntry("TextureNodeTexMarble"),
            OperatorEntry("TextureNodeTexNoise"),
            OperatorEntry("TextureNodeTexStucci"),
            OperatorEntry("TextureNodeTexVoronoi"),
            Separator,
            OperatorEntry("TextureNodeTexWood"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeBricks"),
            OperatorEntry("TextureNodeChecker"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeHueSaturation"),
            OperatorEntry("TextureNodeInvert"),
            OperatorEntry("TextureNodeMixRGB"),
            OperatorEntry("TextureNodeCurveRGB"),
            Separator,
            OperatorEntry("TextureNodeCombineColor"),
            OperatorEntry("TextureNodeSeparateColor"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeOutput"),
            OperatorEntry("TextureNodeViewer"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeValToRGB"),
            OperatorEntry("TextureNodeDistance"),
            OperatorEntry("TextureNodeMath"),
            OperatorEntry("TextureNodeRGBToBW"),
            Separator,
            OperatorEntry("TextureNodeValToNor"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("TextureNodeAt"),
            OperatorEntry("TextureNodeRotate"),
            OperatorEntry("TextureNodeScale"),
            OperatorEntry("TextureNodeTranslate"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
                OperatorEntry("ShaderNodeAddShader"),
                OperatorEntry("ShaderNodeBackground", should_draw=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeEmission"),
                OperatorEntry("ShaderNodeMixShader"),
                OperatorEntry("ShaderNodeBsdfPrincipled", should_draw=is_object),
                OperatorEntry("ShaderNodeBsdfHairPrincipled", should_draw=is_object and not is_eevee),
                OperatorEntry("ShaderNodeVolumePrincipled"),
                OperatorEntry("ShaderNodeBsdfToon", should_draw=is_object and not is_eevee),
                OperatorEntry("ShaderNodeVolumeAbsorption"),
                OperatorEntry("ShaderNodeVolumeScatter"),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeAddShader"),
                OperatorEntry("ShaderNodeBackground", should_draw=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeBsdfDiffuse", should_draw=is_object),
                OperatorEntry("ShaderNodeEmission"),
                OperatorEntry("ShaderNodeBsdfGlass", should_draw=is_object),
                OperatorEntry("ShaderNodeBsdfGlossy", should_draw=is_object),
                OperatorEntry("ShaderNodeBsdfHair", should_draw=is_object and not is_eevee),
                OperatorEntry("ShaderNodeHoldout", should_draw=is_object),
                OperatorEntry("ShaderNodeBsdfMetallic", should_draw=is_object),
                OperatorEntry("ShaderNodeMixShader"),
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
                OperatorEntry("ShaderNodeVolumeAbsorption"),
                OperatorEntry("ShaderNodeVolumeScatter"),
                OperatorEntry("ShaderNodeVolumeCoefficients"),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
                OperatorEntry("ShaderNodeTexEnvironment"),
                OperatorEntry("ShaderNodeTexImage"),
                OperatorEntry("ShaderNodeTexNoise"),
                OperatorEntry("ShaderNodeTexSky"),
                OperatorEntry("ShaderNodeTexVoronoi"),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeTexBrick"),
                OperatorEntry("ShaderNodeTexChecker"),
                OperatorEntry("ShaderNodeTexEnvironment"),
                OperatorEntry("ShaderNodeTexGabor"),
                OperatorEntry("ShaderNodeTexGradient"),
                OperatorEntry("ShaderNodeTexIES"),
                Separator,
                OperatorEntry("ShaderNodeTexImage"),
                OperatorEntry("ShaderNodeTexMagic"),
                OperatorEntry("ShaderNodeTexNoise"),
                OperatorEntry("ShaderNodeTexSky"),
                Separator,
                OperatorEntry("ShaderNodeTexVoronoi"),
                OperatorEntry("ShaderNodeTexWave"),
                OperatorEntry("ShaderNodeTexWhiteNoise"),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
                OperatorEntry("ShaderNodeBrightContrast"),
                OperatorEntry("ShaderNodeGamma"),
                OperatorEntry("ShaderNodeHueSaturation"),
                OperatorEntry("ShaderNodeInvert"),
                Separator,
                OperatorEntry("ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"}),
                OperatorEntry("ShaderNodeRGBCurve"),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeBrightContrast"),
                OperatorEntry("ShaderNodeGamma"),
                OperatorEntry("ShaderNodeHueSaturation"),
                OperatorEntry("ShaderNodeInvert"),
                Separator,
                OperatorEntry("ShaderNodeLightFalloff"),
                OperatorEntry("ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"}),
                OperatorEntry("ShaderNodeRGBCurve"),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
                OperatorEntry("ShaderNodeMapping"),
                OperatorEntry("ShaderNodeNormal"),
                OperatorEntry("ShaderNodeNormalMap"),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeBump"),
                OperatorEntry("ShaderNodeDisplacement"),
                OperatorEntry("ShaderNodeMapping"),
                OperatorEntry("ShaderNodeNormal"),
                OperatorEntry("ShaderNodeNormalMap"),
                Separator,
                OperatorEntry("ShaderNodeVectorCurve"),
                OperatorEntry("ShaderNodeVectorDisplacement"),
                OperatorEntry("ShaderNodeVectorRotate"),
                OperatorEntry("ShaderNodeVectorTransform"),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
                OperatorEntry("ShaderNodeClamp"),
                OperatorEntry("ShaderNodeValToRGB"),
                Separator,
                OperatorEntry("ShaderNodeFloatCurve"),
                OperatorEntry("ShaderNodeMapRange"),
                OperatorEntry("ShaderNodeMath"),
                OperatorEntry("ShaderNodeRGBToBW"),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeBlackbody"),
                OperatorEntry("ShaderNodeClamp"),
                OperatorEntry("ShaderNodeValToRGB"),
                OperatorEntry("ShaderNodeCombineColor"),
                OperatorEntry("ShaderNodeCombineXYZ"),
                Separator,
                OperatorEntry("ShaderNodeFloatCurve"),
                OperatorEntry("ShaderNodeMapRange"),
                OperatorEntry("ShaderNodeMath"),
                OperatorEntry("ShaderNodeMix"),
                OperatorEntry("ShaderNodeRGBToBW"),
                Separator,
                OperatorEntry("ShaderNodeSeparateColor"),
                OperatorEntry("ShaderNodeSeparateXYZ"),
                OperatorEntry("ShaderNodeShaderToRGB", should_draw=is_engine(context, 'BLENDER_EEVEE')),
                OperatorEntry("ShaderNodeVectorMath"),
                OperatorEntry("ShaderNodeWavelength"),
            )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeScript"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("NodeFrame"),
            OperatorEntry("NodeReroute"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeAttributeStatistic"),
            OperatorEntry("GeometryNodeAttributeDomainSize"),
            Separator,
            OperatorEntry("GeometryNodeBlurAttribute"),
            OperatorEntry("GeometryNodeCaptureAttribute"),
            OperatorEntry("GeometryNodeRemoveAttribute"),
            OperatorEntry("GeometryNodeStoreNamedAttribute"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("FunctionNodeInputBool"),
            OperatorEntry("GeometryNodeInputCollection"),
            OperatorEntry("FunctionNodeInputColor"),
            OperatorEntry("GeometryNodeInputImage"),
            OperatorEntry("FunctionNodeInputInt"),
            OperatorEntry("GeometryNodeInputMaterial"),
            OperatorEntry("GeometryNodeInputObject"),
            OperatorEntry("FunctionNodeInputRotation"),
            OperatorEntry("FunctionNodeInputString"),
            OperatorEntry("ShaderNodeValue"),
            OperatorEntry("FunctionNodeInputVector"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeGizmoDial"),
            OperatorEntry("GeometryNodeGizmoLinear"),
            OperatorEntry("GeometryNodeGizmoTransform"),
        )
        
        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeImportOBJ"),
            OperatorEntry("GeometryNodeImportPLY"),
            OperatorEntry("GeometryNodeImportSTL"),
            OperatorEntry("GeometryNodeImportCSV"),
            OperatorEntry("GeometryNodeImportText"),
            OperatorEntry("GeometryNodeImportVDB"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeInputActiveCamera"),
            OperatorEntry("GeometryNodeCameraInfo"),
            OperatorEntry("GeometryNodeCollectionInfo"),
            OperatorEntry("GeometryNodeImageInfo"),
            OperatorEntry("GeometryNodeIsViewport"),
            OperatorEntry("GeometryNodeInputNamedLayerSelection"),
            OperatorEntry("GeometryNodeToolMousePosition", should_draw=is_tool),
            OperatorEntry("GeometryNodeObjectInfo"),
            OperatorEntry("GeometryNodeInputSceneTime"),
            OperatorEntry("GeometryNodeSelfObject"),
            OperatorEntry("GeometryNodeViewportTransform", should_draw=is_tool),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeViewer"),
            OperatorEntry("GeometryNodeWarning"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeGeometryToInstance"),
            OperatorEntry("GeometryNodeJoinGeometry"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeInputID"),
            OperatorEntry("GeometryNodeInputIndex"),
            OperatorEntry("GeometryNodeInputNamedAttribute"),
            OperatorEntry("GeometryNodeInputNormal"),
            OperatorEntry("GeometryNodeInputPosition"),
            OperatorEntry("GeometryNodeInputRadius"),
            OperatorEntry("GeometryNodeToolSelection", should_draw=is_tool),
            OperatorEntry("GeometryNodeToolActiveElement", should_draw=is_tool),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeProximity"),
            OperatorEntry("GeometryNodeIndexOfNearest"),
            OperatorEntry("GeometryNodeRaycast"),
            OperatorEntry("GeometryNodeSampleIndex"),
            OperatorEntry("GeometryNodeSampleNearest"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeSetGeometryName"),
            OperatorEntry("GeometryNodeSetID"),
            OperatorEntry("GeometryNodeSetPosition"),
            OperatorEntry("GeometryNodeToolSetSelection", should_draw=is_tool_tree(context)),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeBake"),
            OperatorEntry("GeometryNodeBoundBox"),
            OperatorEntry("GeometryNodeConvexHull"),
            OperatorEntry("GeometryNodeDeleteGeometry"),
            OperatorEntry("GeometryNodeDuplicateElements"),
            OperatorEntry("GeometryNodeMergeByDistance"),
            OperatorEntry("GeometryNodeSortElements"),
            OperatorEntry("GeometryNodeTransform"),
            Separator,
            OperatorEntry("GeometryNodeSeparateComponents"),
            OperatorEntry("GeometryNodeSeparateGeometry"),
            OperatorEntry("GeometryNodeSplitToInstances"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeInputCurveHandlePositions"),
            OperatorEntry("GeometryNodeCurveLength"),
            OperatorEntry("GeometryNodeInputTangent"),
            OperatorEntry("GeometryNodeInputCurveTilt"),
            OperatorEntry("GeometryNodeCurveEndpointSelection"),
            OperatorEntry("GeometryNodeCurveHandleTypeSelection"),
            OperatorEntry("GeometryNodeInputSplineCyclic"),
            OperatorEntry("GeometryNodeSplineLength"),
            OperatorEntry("GeometryNodeSplineParameter"),
            OperatorEntry("GeometryNodeInputSplineResolution"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeSampleCurve"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeSetCurveNormal"),
            OperatorEntry("GeometryNodeSetCurveRadius"),
            OperatorEntry("GeometryNodeSetCurveTilt"),
            OperatorEntry("GeometryNodeSetCurveHandlePositions"),
            OperatorEntry("GeometryNodeCurveSetHandles"),
            OperatorEntry("GeometryNodeSetSplineCyclic"),
            OperatorEntry("GeometryNodeSetSplineResolution"),
            OperatorEntry("GeometryNodeCurveSplineType"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeCurvesToGreasePencil"),
            OperatorEntry("GeometryNodeCurveToMesh"),
            OperatorEntry("GeometryNodeCurveToPoints"),
            OperatorEntry("GeometryNodeDeformCurvesOnSurface"),
            OperatorEntry("GeometryNodeFillCurve"),
            OperatorEntry("GeometryNodeFilletCurve"),
            OperatorEntry("GeometryNodeGreasePencilToCurves"),
            OperatorEntry("GeometryNodeInterpolateCurves"),
            OperatorEntry("GeometryNodeResampleCurve"),
            OperatorEntry("GeometryNodeReverseCurve"),
            OperatorEntry("GeometryNodeSubdivideCurve"),
            OperatorEntry("GeometryNodeTrimCurve"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeCurveArc"),
            OperatorEntry("GeometryNodeCurvePrimitiveBezierSegment"),
            OperatorEntry("GeometryNodeCurvePrimitiveCircle"),
            OperatorEntry("GeometryNodeCurvePrimitiveLine"),
            OperatorEntry("GeometryNodeCurveSpiral"),
            OperatorEntry("GeometryNodeCurveQuadraticBezier"),
            OperatorEntry("GeometryNodeCurvePrimitiveQuadrilateral"),
            OperatorEntry("GeometryNodeCurveStar"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeCurveOfPoint"),
            OperatorEntry("GeometryNodeOffsetPointInCurve"),
            OperatorEntry("GeometryNodePointsOfCurve"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeInputNamedLayerSelection"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeSetGreasePencilColor"),
            OperatorEntry("GeometryNodeSetGreasePencilDepth"),
            OperatorEntry("GeometryNodeSetGreasePencilSoftness"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeGreasePencilToCurves"),
            OperatorEntry("GeometryNodeMergeLayers"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeInstanceOnPoints"),
            OperatorEntry("GeometryNodeInstancesToPoints"),
            OperatorEntry("GeometryNodeRealizeInstances"),
            OperatorEntry("GeometryNodeRotateInstances"),
            OperatorEntry("GeometryNodeScaleInstances"),
            OperatorEntry("GeometryNodeTranslateInstances"),
            OperatorEntry("GeometryNodeSetInstanceTransform"),
            Separator,
            OperatorEntry("GeometryNodeInputInstanceBounds"),
            OperatorEntry("GeometryNodeInstanceTransform"),
            OperatorEntry("GeometryNodeInputInstanceRotation"),
            OperatorEntry("GeometryNodeInputInstanceScale"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeInputMeshEdgeAngle"),
            OperatorEntry("GeometryNodeInputMeshEdgeNeighbors"),
            OperatorEntry("GeometryNodeInputMeshEdgeVertices"),
            OperatorEntry("GeometryNodeEdgesToFaceGroups"),
            OperatorEntry("GeometryNodeInputMeshFaceArea"),
            Separator,
            OperatorEntry("GeometryNodeMeshFaceSetBoundaries"),
            OperatorEntry("GeometryNodeInputMeshFaceNeighbors"),
            OperatorEntry("GeometryNodeToolFaceSet", should_draw=is_tool_tree(context)),
            OperatorEntry("GeometryNodeInputMeshFaceIsPlanar"),
            OperatorEntry("GeometryNodeInputShadeSmooth"),
            OperatorEntry("GeometryNodeInputEdgeSmooth"),
            Separator,
            OperatorEntry("GeometryNodeInputMeshIsland"),
            OperatorEntry("GeometryNodeInputShortestEdgePaths"),
            OperatorEntry("GeometryNodeInputMeshVertexNeighbors"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeSampleNearestSurface"),
            OperatorEntry("GeometryNodeSampleUVSurface"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeSetMeshNormal"),
            OperatorEntry("GeometryNodeSetShadeSmooth"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeDualMesh"),
            OperatorEntry("GeometryNodeEdgePathsToCurves"),
            OperatorEntry("GeometryNodeEdgePathsToSelection"),
            OperatorEntry("GeometryNodeExtrudeMesh"),
            OperatorEntry("GeometryNodeFlipFaces"),
            Separator,
            OperatorEntry("GeometryNodeMeshBoolean"),
            OperatorEntry("GeometryNodeMeshToCurve"),
            OperatorEntry("GeometryNodeMeshToPoints"),
            OperatorEntry("GeometryNodeMeshToVolume"),
            OperatorEntry("GeometryNodeScaleElements"),
            Separator,
            OperatorEntry("GeometryNodeSplitEdges"),
            OperatorEntry("GeometryNodeSubdivideMesh"),
            OperatorEntry("GeometryNodeSubdivisionSurface"),
            OperatorEntry("GeometryNodeTriangulate"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeMeshCone"),
            OperatorEntry("GeometryNodeMeshCube"),
            OperatorEntry("GeometryNodeMeshCylinder"),
            OperatorEntry("GeometryNodeMeshGrid"),
            Separator,
            OperatorEntry("GeometryNodeMeshIcoSphere"),
            OperatorEntry("GeometryNodeMeshCircle"),
            OperatorEntry("GeometryNodeMeshLine"),
            OperatorEntry("GeometryNodeMeshUVSphere"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeCornersOfEdge"),
            OperatorEntry("GeometryNodeCornersOfFace"),
            OperatorEntry("GeometryNodeCornersOfVertex"),
            OperatorEntry("GeometryNodeEdgesOfCorner"),
            Separator,
            OperatorEntry("GeometryNodeEdgesOfVertex"),
            OperatorEntry("GeometryNodeFaceOfCorner"),
            OperatorEntry("GeometryNodeOffsetCornerInFace"),
            OperatorEntry("GeometryNodeVertexOfCorner"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeUVPackIslands"),
            OperatorEntry("GeometryNodeUVUnwrap"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeDistributePointsInVolume"),
            OperatorEntry("GeometryNodeDistributePointsOnFaces"),
            Separator,
            OperatorEntry("GeometryNodePoints"),
            OperatorEntry("GeometryNodePointsToCurves"),
            OperatorEntry("GeometryNodePointsToVertices"),
            OperatorEntry("GeometryNodePointsToVolume"),
            OperatorEntry("GeometryNodeSetPointRadius"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeVolumeCube"),
            OperatorEntry("GeometryNodeVolumeToMesh"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeReplaceMaterial"),
            OperatorEntry("GeometryNodeInputMaterialIndex"),
            OperatorEntry("GeometryNodeMaterialSelection"),
            OperatorEntry("GeometryNodeSetMaterial"),
            OperatorEntry("GeometryNodeSetMaterialIndex"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeTexBrick"),
            OperatorEntry("ShaderNodeTexChecker"),
            OperatorEntry("ShaderNodeTexGradient"),
            OperatorEntry("GeometryNodeImageTexture"),
            OperatorEntry("ShaderNodeTexMagic"),
            OperatorEntry("ShaderNodeTexNoise"),
            OperatorEntry("ShaderNodeTexVoronoi"),
            OperatorEntry("ShaderNodeTexWave"),
            OperatorEntry("ShaderNodeTexWhiteNoise"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeIndexSwitch"),
            OperatorEntry("GeometryNodeMenuSwitch"),
            OperatorEntry("FunctionNodeRandomValue"),
            OperatorEntry(operator="node.add_repeat_zone", text="Repeat Zone", icon="REPEAT"),
            OperatorEntry("GeometryNodeSwitch"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeValToRGB"),
            OperatorEntry("ShaderNodeRGBCurve"),
            Separator,
            OperatorEntry("FunctionNodeCombineColor"),
            OperatorEntry("ShaderNodeMix", text="Mix Color", settings={"data_type": "'RGBA'"}),
            OperatorEntry("FunctionNodeSeparateColor"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("FunctionNodeFormatString"),
            OperatorEntry("GeometryNodeStringJoin"),
            OperatorEntry("FunctionNodeMatchString"),
            OperatorEntry("FunctionNodeReplaceString"),
            OperatorEntry("FunctionNodeSliceString"),
            OperatorEntry("FunctionNodeStringLength"),
            OperatorEntry("FunctionNodeFindInString"),
            OperatorEntry("GeometryNodeStringToCurves"),
            OperatorEntry("FunctionNodeValueToString"),
            OperatorEntry("FunctionNodeInputSpecialCharacters"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("ShaderNodeVectorCurve"),
            OperatorEntry("ShaderNodeVectorMath"),
            OperatorEntry("ShaderNodeVectorRotate"),
            OperatorEntry("ShaderNodeCombineXYZ"),
            OperatorEntry("ShaderNodeMix", text="Mix Vector", settings={"data_type": "'VECTOR'"}),
            OperatorEntry("ShaderNodeSeparateXYZ"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("GeometryNodeAccumulateField"),
            OperatorEntry("GeometryNodeFieldAtIndex"),
            OperatorEntry("GeometryNodeFieldOnDomain"),
            OperatorEntry("GeometryNodeFieldAverage"),
            OperatorEntry("GeometryNodeFieldMinAndMax"),
            OperatorEntry("GeometryNodeFieldVariance"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("FunctionNodeBitMath"),
            OperatorEntry("FunctionNodeBooleanMath"),
            OperatorEntry("FunctionNodeIntegerMath"),
            OperatorEntry("ShaderNodeClamp"),
            OperatorEntry("FunctionNodeCompare"),
            OperatorEntry("ShaderNodeFloatCurve"),
            Separator,
            OperatorEntry("FunctionNodeFloatToInt"),
            OperatorEntry("FunctionNodeHashValue"),
            OperatorEntry("ShaderNodeMapRange"),
            OperatorEntry("ShaderNodeMath"),
            OperatorEntry("ShaderNodeMix"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("FunctionNodeCombineMatrix"),
            OperatorEntry("FunctionNodeCombineTransform"),
            OperatorEntry("FunctionNodeMatrixDeterminant"),
            OperatorEntry("FunctionNodeInvertMatrix"),
            OperatorEntry("FunctionNodeMatrixMultiply"),
            OperatorEntry("FunctionNodeProjectPoint"),
            OperatorEntry("FunctionNodeSeparateMatrix"),
            OperatorEntry("FunctionNodeSeparateTransform"),
            OperatorEntry("FunctionNodeTransformDirection"),
            OperatorEntry("FunctionNodeTransformPoint"),
            OperatorEntry("FunctionNodeTransposeMatrix"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("FunctionNodeAlignRotationToVector"),
            OperatorEntry("FunctionNodeAxesToRotation"),
            OperatorEntry("FunctionNodeAxisAngleToRotation"),
            OperatorEntry("FunctionNodeEulerToRotation"),
            OperatorEntry("FunctionNodeInvertRotation"),
            OperatorEntry("FunctionNodeRotateRotation"),
            OperatorEntry("FunctionNodeRotateVector"),
            OperatorEntry("FunctionNodeRotationToAxisAngle"),
            OperatorEntry("FunctionNodeRotationToEuler"),
            OperatorEntry("FunctionNodeRotationToQuaternion"),
            OperatorEntry("FunctionNodeQuaternionToRotation"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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
            OperatorEntry("FunctionNodeAlignEulerToVector"),
            OperatorEntry("FunctionNodeRotateEuler"),
        )

        self.draw_entries(context, layout, entries, pad=calculate_padding(entries))


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

