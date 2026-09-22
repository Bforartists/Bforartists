# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.app.translations import (
    pgettext_iface as iface_,
)

import functools
import dataclasses

from nodeitems_builtins import node_tree_group_type
from bl_ui.node_add_menu import draw_node_groups, add_empty_group, AddNodeMenu
from bl_ui import (
    node_add_menu_compositor,
    node_add_menu_geometry,
    node_add_menu_shader,
    node_add_menu_texture,
)


# BFA - Custom panels for the sidebar toolshelf
# BFA - to define padding, it helps to count 2 points per character.

# Null object used to abstractly represent a separator
Separator = object()


class CompositorNodesPanel:
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')


class GeometryNodesPanel:
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')


class ShaderNodesPanel:
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree')


class TextureNodesPanel:
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')


class ChildLayoutWrapper:
    def __init__(self, layout, parent):
        self.layout = layout
        self.parent = parent
    
    def separator(self, factor=None):
        if use_icon_buttons():
            parent = self.parent

            flow = parent.layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.layout = flow
        else:
            layout = self.layout
            layout.separator(factor=2/3)
        
    def __getattr__(self, name):
       return getattr(self.layout, name)
    

class LayoutDummy:
    def __init__(self, actual_class):
        self.actual_class = actual_class
    
    @property
    def layout(self):
        parent = self.actual_class

        if parent.layout_container is None:
            return ChildLayoutWrapper(parent.layout, parent=parent)
        else:
            return ChildLayoutWrapper(parent.layout_container, parent=parent)
        
    def __getattr__(self, name):
       return getattr(self.actual_class, name)


def use_icon_buttons(context=None):
    if context is None:
        context = bpy.context

    return context.preferences.addons["bforartists_toolbar_settings"].preferences.Node_text_or_icon


class AddNodePanel(bpy.types.Panel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    layout_container = None
    menu_path = None

    @classmethod
    def do_nothing(cls, *args, **kwargs):
        return

    draw_assets_for_catalog = do_nothing
    draw_menu = do_nothing

    @staticmethod
    def operator_label(label):
        return label if not use_icon_buttons() else ""

    @classmethod
    def node_operator(cls, layout, node_type, *_, label=None, **kwargs):
        return AddNodeMenu.node_operator(layout, node_type, label=cls.operator_label(label), **kwargs)

    @classmethod
    def node_operator_with_searchable_enum(cls, context, layout, node_type, *args, label=None, **kwargs):
        return AddNodeMenu.node_operator(layout, node_type, label=cls.operator_label(label), **kwargs)

    node_operator_with_outputs = node_operator_with_searchable_enum
    node_operator_with_searchable_enum_socket = node_operator_with_searchable_enum
        
    def __getattr__(self, name):
       return functools.partial(getattr(AddNodeMenu, name), icon_only=use_icon_buttons())

    def draw(self, context):
        if use_icon_buttons(context):
            flow = self.layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
            flow.scale_x = 1.5
            flow.scale_y = 1.5

            self.layout_container = flow
            self.layout_base.draw(LayoutDummy(self), context)
        else:
            col = self.layout.column(align=True)
            col.scale_y = 1.5

            self.layout_container = col
            self.layout_base.draw(LayoutDummy(self), context)


@dataclasses.dataclass(slots=True)
class OperatorEntry:
    node : str = None
    operator : str = "node.add_node"
    text : str = ""
    icon : str = None
    props : dict = None
    settings : dict = None
    poll : bool = True
    pad : int = 0

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
        return context.space_data.node_tree_sub_type == 'TOOL'
    except AttributeError:
        return False


class NodePanel:
    @staticmethod
    def draw_text_button(layout, node=None, operator="node.add_node", text="", icon=None, settings=None, props=None, pad=0, **kwargs):
        if (operator == "node.add_node") or (text != ""):
            text = " " + text + (" "*pad)
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
                    if entry.poll:
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
                    if entry.poll:
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


class NODES_PT_relations_group_operations(AddNodePanel):
    bl_label = "Group"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

    @classmethod
    def poll(self, context):
        tree = context.space_data.edit_tree 
        return tree in context.blend_data.node_groups.values()

    def draw(self, context):
        layout = self.layout
        in_group = context.space_data.edit_tree in context.blend_data.node_groups.values()

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("NodeGroupInput", poll=in_group),
            OperatorEntry("NodeGroupOutput", poll=in_group),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_relations_nodegroups(AddNodePanel):
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


class NODES_PT_relations_layout(AddNodePanel):
    bl_label = "Layout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("NodeFrame"),
            OperatorEntry("NodeReroute"),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_input(AddNodePanel):
    bl_label = "Input"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_input_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeAttribute", pad=20),
                OperatorEntry("ShaderNodeFresnel", pad=22),
                OperatorEntry("ShaderNodeNewGeometry", pad=18),
                OperatorEntry("ShaderNodeTexCoord", pad=1),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeAmbientOcclusion", pad=2),
                OperatorEntry("ShaderNodeAttribute", pad=20),
                OperatorEntry("ShaderNodeBevel", pad=26),
                OperatorEntry("ShaderNodeCameraData", pad=13),
                OperatorEntry("ShaderNodeVertexColor", pad=10),
                OperatorEntry("ShaderNodeHairInfo", pad=15),
                Separator,
                OperatorEntry("ShaderNodeFresnel", pad=22),
                OperatorEntry("ShaderNodeNewGeometry", pad=18),
                OperatorEntry("ShaderNodeLayerWeight", pad=12),
                OperatorEntry("ShaderNodeLightPath", pad=16),
                OperatorEntry("ShaderNodeObjectInfo", pad=14),
                Separator,
                OperatorEntry("ShaderNodeParticleInfo", pad=12),
                OperatorEntry("ShaderNodePointInfo", pad=16 ),
                OperatorEntry("ShaderNodeRaycast", pad=21),
                OperatorEntry("ShaderNodeTangent", pad=20),
                OperatorEntry("ShaderNodeTexCoord", pad=1),
                OperatorEntry("ShaderNodeUVAlongStroke", pad=4, poll=is_shader_type(context, 'LINESTYLE')),
                Separator,
                OperatorEntry("ShaderNodeUVMap", pad=19),
                OperatorEntry("ShaderNodeValue", pad=23),
                OperatorEntry("ShaderNodeVolumeInfo", pad=11),
                OperatorEntry("ShaderNodeWireframe", pad=14),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_input_constant(AddNodePanel):
    bl_label = "Constant"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_input"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_input_constant_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeRGB", pad=20),
                OperatorEntry("FunctionNodeInputInt",pad=16),
                OperatorEntry("ShaderNodeValue", pad=18),
                OperatorEntry("FunctionNodeInputVector",pad=17),
            )
        else:
            entries = (
                OperatorEntry("FunctionNodeInputBool",pad=16),
                OperatorEntry("ShaderNodeRGB", pad=20),
                OperatorEntry("FunctionNodeInputInt",pad=16),
                OperatorEntry("FunctionNodeInputMenu",pad=19),
                OperatorEntry("ShaderNodeValue", pad=18),
                OperatorEntry("FunctionNodeInputVector",pad=17),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_output(AddNodePanel):
    bl_label = "Output"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_output_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        is_object_shader = is_shader_type(context, 'OBJECT')
        is_cycles =  is_engine(context, 'CYCLES')

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeOutputLineStyle", pad=1, poll=is_shader_type(context, 'LINESTYLE')),
                OperatorEntry("ShaderNodeOutputMaterial", pad=4, poll=is_object_shader),
                OperatorEntry("ShaderNodeOutputWorld", pad=8, poll=is_shader_type(context, 'WORLD')),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeOutputAOV", pad=10),
                OperatorEntry("ShaderNodeOutputLight", pad=9, poll=is_object_shader and is_cycles),
                OperatorEntry("ShaderNodeOutputLineStyle", pad=1, poll=is_shader_type(context, 'LINESTYLE')),
                OperatorEntry("ShaderNodeOutputMaterial", pad=4, poll=is_object_shader),
                OperatorEntry("ShaderNodeOutputWorld", pad=8, poll=is_shader_type(context, 'WORLD')),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_shader(AddNodePanel):
    bl_label = "Shader"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_shader_base

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and context.space_data.shader_type in ('OBJECT', 'WORLD'))

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        is_object = is_shader_type(context, 'OBJECT')
        is_eevee = is_engine(context, 'BLENDER_EEVEE')

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeAddShader", pad=18),
                OperatorEntry("ShaderNodeMixShader", pad=20),
                Separator,
                OperatorEntry("ShaderNodeBackground", pad=18, poll=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeEmission", pad=23),
                OperatorEntry("ShaderNodeBsdfPrincipled", pad=12, poll=is_object),
                OperatorEntry("ShaderNodeBsdfHairPrincipled", pad=4, poll=is_object and not is_eevee),
                OperatorEntry("ShaderNodeBsdfToon", pad=20, poll=is_object and not is_eevee),
                Separator,
                OperatorEntry("ShaderNodeVolumePrincipled", pad=8),
                OperatorEntry("ShaderNodeVolumeAbsorption", pad=7),
                OperatorEntry("ShaderNodeVolumeScatter", pad=13),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeAddShader", pad=18),
                OperatorEntry("ShaderNodeMixShader", pad=20),
                Separator,
                OperatorEntry("ShaderNodeBackground", pad=18, poll=is_shader_type(context, 'WORLD')),
                OperatorEntry("ShaderNodeBsdfDiffuse", pad=16, poll=is_object),
                OperatorEntry("ShaderNodeEmission", pad=23),
                OperatorEntry("ShaderNodeBsdfGlass", pad=19, poll=is_object),
                OperatorEntry("ShaderNodeBsdfGlossy", pad=17, poll=is_object),
                OperatorEntry("ShaderNodeBsdfHair", pad=22, poll=is_object and not is_eevee),
                OperatorEntry("ShaderNodeHoldout", pad=26, poll=is_object),
                OperatorEntry("ShaderNodeBsdfMetallic", pad=16, poll=is_object),
                OperatorEntry("ShaderNodeBsdfPrincipled", pad=12, poll=is_object),
                OperatorEntry("ShaderNodeBsdfHairPrincipled", pad=4, poll=is_object and not is_eevee),
                OperatorEntry("ShaderNodeBsdfRayPortal", pad=11, poll=is_object and not is_eevee),
                OperatorEntry("ShaderNodeBsdfRefraction", pad=11, poll=is_object),
                OperatorEntry("ShaderNodeBsdfSheen", pad=18, poll=is_object and not is_eevee),
                OperatorEntry("ShaderNodeEeveeSpecular", pad=13, poll=is_object and is_eevee),
                OperatorEntry("ShaderNodeSubsurfaceScattering", pad=1, poll=is_object),
                OperatorEntry("ShaderNodeBsdfToon", pad=20, poll=is_object and not is_eevee),
                OperatorEntry("ShaderNodeBsdfTranslucent", pad=9, poll=is_object),
                OperatorEntry("ShaderNodeBsdfTransparent", pad=9, poll=is_object),
                Separator,
                OperatorEntry("ShaderNodeVolumePrincipled", pad=8),
                OperatorEntry("ShaderNodeVolumeAbsorption", pad=7),
                OperatorEntry("ShaderNodeVolumeScatter", pad=13),
                OperatorEntry("ShaderNodeVolumeCoefficients", pad=5),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_displacement(AddNodePanel):
    bl_label = "Displacement"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_displacement_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeBump", pad=29),
                OperatorEntry("ShaderNodeDisplacement", pad=16),
                OperatorEntry("ShaderNodeNormalMap", pad=18),
                OperatorEntry("ShaderNodeVectorDisplacement", pad=5),
            )

        else:
            entries = (
                OperatorEntry("ShaderNodeBump", pad=29),
                OperatorEntry("ShaderNodeDisplacement", pad=16),
                OperatorEntry("ShaderNodeNormalMap", pad=18),
                OperatorEntry("ShaderNodeVectorDisplacement", pad=5),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_color(AddNodePanel):
    bl_label = "Color"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_color_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeBrightContrast", pad=2),
                OperatorEntry("ShaderNodeValToRGB", pad=17),
                OperatorEntry("ShaderNodeGamma", pad=24),
                OperatorEntry("ShaderNodeHueSaturation", pad=0),
                OperatorEntry("ShaderNodeInvert", pad=17),
                OperatorEntry("ShaderNodeMix", text="Mix Color", pad=21, settings={"data_type": "'RGBA'"}),
                OperatorEntry("ShaderNodeRGBCurve", pad=18),
                Separator,
                OperatorEntry("ShaderNodeCombineColor", pad=12),
                OperatorEntry("ShaderNodeSeparateColor", pad=12),
                Separator,
                OperatorEntry("ShaderNodeShaderToRGB", pad=13, poll=is_engine(context, 'BLENDER_EEVEE')),
                OperatorEntry("ShaderNodeRGBToBW", pad=19),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeBlackbody", pad=19),
                OperatorEntry("ShaderNodeBrightContrast", pad=2),
                OperatorEntry("ShaderNodeValToRGB", pad=17),
                OperatorEntry("ShaderNodeGamma", pad=24),
                OperatorEntry("ShaderNodeHueSaturation", pad=0),
                OperatorEntry("ShaderNodeInvert", pad=17),
                OperatorEntry("ShaderNodeLightFalloff", pad=17),
                OperatorEntry("ShaderNodeMix", text="Mix Color", pad=21, settings={"data_type": "'RGBA'"}),
                OperatorEntry("ShaderNodeRGBCurve", pad=18),
                OperatorEntry("ShaderNodeWavelength", pad=17),
                Separator,
                OperatorEntry("ShaderNodeCombineColor", pad=12),
                OperatorEntry("ShaderNodeSeparateColor", pad=12),
                Separator,
                OperatorEntry("ShaderNodeShaderToRGB", pad=13, poll=is_engine(context, 'BLENDER_EEVEE')),
                OperatorEntry("ShaderNodeRGBToBW", pad=19),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_texture(AddNodePanel):
    bl_label = "Texture"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_texture_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeTexEnvironment", pad=0),
                OperatorEntry("ShaderNodeTexImage", pad=12),
                OperatorEntry("ShaderNodeTexNoise", pad=13),
                OperatorEntry("ShaderNodeTexSky", pad=16),
                OperatorEntry("ShaderNodeTexVoronoi", pad=8),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeTexBrick", pad=15),
                OperatorEntry("ShaderNodeTexChecker", pad=9),
                OperatorEntry("ShaderNodeTexEnvironment", pad=0),
                OperatorEntry("ShaderNodeTexGabor", pad=12),
                OperatorEntry("ShaderNodeTexGradient", pad=8),
                OperatorEntry("ShaderNodeTexIES", pad=16),
                Separator,
                OperatorEntry("ShaderNodeTexImage", pad=12),
                OperatorEntry("ShaderNodeTexMagic", pad=12),
                OperatorEntry("ShaderNodeTexNoise", pad=13),
                OperatorEntry("ShaderNodeTexSky", pad=16),
                Separator,
                OperatorEntry("ShaderNodeTexVoronoi", pad=8),
                OperatorEntry("ShaderNodeTexWave", pad=12),
                OperatorEntry("ShaderNodeTexWhiteNoise", pad=0),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_utilities(AddNodePanel):
    bl_label = "Utilities"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_utilities_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry(operator="node.add_repeat_zone", pad=24, text="Repeat Zone", icon="REPEAT"),
                Separator,
                OperatorEntry("NodeCombineBundle", pad=17),
                OperatorEntry("NodeSeparateBundle", pad=17),
                Separator,
                OperatorEntry("GeometryNodeMenuSwitch", pad=23),
            )

        else:
            entries = (
                OperatorEntry(operator="node.add_repeat_zone", pad=24, text="Repeat Zone", icon="REPEAT"),
                Separator,
                OperatorEntry("NodeImplicitConversion", pad=11),
                OperatorEntry(operator="node.add_closure_zone", text="Closure", icon="NODE_CLOSURE", pad=32),
                OperatorEntry("NodeEvaluateClosure", pad=16),
                OperatorEntry("NodeCombineBundle", pad=17),
                OperatorEntry("NodeSeparateBundle", pad=17),
                OperatorEntry("NodeJoinBundle", pad=25),
                Separator,
                OperatorEntry("GeometryNodeMenuSwitch", pad=23),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_math(AddNodePanel):
    bl_label = "Math"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_utilities"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_math_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeClamp", pad=24),
                OperatorEntry("ShaderNodeFloatCurve", pad=15),
                OperatorEntry("ShaderNodeMapRange", pad=15),
                OperatorEntry("ShaderNodeMath", pad=26),
                OperatorEntry("ShaderNodeMix", pad=28),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeClamp", pad=24),
                OperatorEntry("ShaderNodeFloatCurve", pad=15),
                OperatorEntry("ShaderNodeMapRange", pad=15),
                OperatorEntry("ShaderNodeMath", pad=26),
                OperatorEntry("ShaderNodeMix", pad=28),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_vector(AddNodePanel):
    bl_label = "Vector"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_utilities"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_vector_base

    def __draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeCombineXYZ", pad=16),
                OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=20, settings={"data_type": "'FLOAT_VECTOR'"}),
                OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), pad=20, settings={"data_type": "'VECTOR'"}),
                OperatorEntry("ShaderNodeSeparateXYZ", pad=16),
                Separator,
                OperatorEntry("ShaderNodeMapping", pad=24),
                OperatorEntry("ShaderNodeNormal", pad=27),
                OperatorEntry("ShaderNodeRadialTiling", pad=18),
                OperatorEntry("ShaderNodeVectorMath", pad=18),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeCombineXYZ", pad=16),
                OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=20, settings={"data_type": "'FLOAT_VECTOR'"}),
                OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), pad=20, settings={"data_type": "'VECTOR'"}),
                OperatorEntry("ShaderNodeSeparateXYZ", pad=16),
                Separator,
                OperatorEntry("ShaderNodeMapping", pad=24),
                OperatorEntry("ShaderNodeNormal", pad=27),
                OperatorEntry("ShaderNodeRadialTiling", pad=18),
                OperatorEntry("ShaderNodeVectorCurve", pad=15),
                OperatorEntry("ShaderNodeVectorMath", pad=18),
                OperatorEntry("ShaderNodeVectorRotate", pad=15),
                OperatorEntry("ShaderNodeVectorTransform", pad=8),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_input(AddNodePanel, CompositorNodesPanel):
    bl_label = "Input"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_input_base


class NODES_PT_toolshelf_compositor_add_input_constant(AddNodePanel, CompositorNodesPanel):
    bl_label = "Constant"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_input"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_input_constant_base


class NODES_PT_toolshelf_compositor_add_input_scene(AddNodePanel, CompositorNodesPanel):
    bl_label = "Scene"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_input"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_input_scene_base


class NODES_PT_toolshelf_compositor_add_output(AddNodePanel, CompositorNodesPanel):
    bl_label = "Output"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_output_base


class NODES_PT_toolshelf_compositor_add_color(AddNodePanel, CompositorNodesPanel):
    bl_label = "Color"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_color_base


class NODES_PT_toolshelf_compositor_add_color_adjust(AddNodePanel, CompositorNodesPanel):
    bl_label = "Adjust"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_color"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_color_adjust_base


class NODES_PT_toolshelf_compositor_add_creative(AddNodePanel, CompositorNodesPanel):
    bl_label = "Creative"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_creative_base


class NODES_PT_toolshelf_compositor_add_filter(AddNodePanel, CompositorNodesPanel):
    bl_label = "Filter"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_filter_base


class NODES_PT_toolshelf_compositor_add_filter_blur(AddNodePanel, CompositorNodesPanel):
    bl_label = "Blur"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_filter"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_filter_blur_base


class NODES_PT_toolshelf_compositor_add_keying(AddNodePanel, CompositorNodesPanel):
    bl_label = "Keying"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_keying_base


class NODES_PT_toolshelf_compositor_add_mask(AddNodePanel, CompositorNodesPanel):
    bl_label = "Mask"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_mask_base


class NODES_PT_toolshelf_compositor_add_tracking(AddNodePanel, CompositorNodesPanel):
    bl_label = "Tracking"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_tracking_base


class NODES_PT_toolshelf_compositor_add_texture(AddNodePanel, CompositorNodesPanel):
    bl_label = "Texture"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_texture_base


class NODES_PT_toolshelf_compositor_add_transform(AddNodePanel, CompositorNodesPanel):
    bl_label = "Transform"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_transform_base


class NODES_PT_toolshelf_compositor_add_utilities(AddNodePanel, CompositorNodesPanel):
    bl_label = "Utilities"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_utilities_base


class NODES_PT_toolshelf_compositor_add_utilities_math(AddNodePanel, CompositorNodesPanel):
    bl_label = "Math"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_math_base


class NODES_PT_toolshelf_compositor_add_utilities_matrix(AddNodePanel, CompositorNodesPanel):
    bl_label = "Matrix"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_utilities_matrix_base


class NODES_PT_toolshelf_compositor_add_utilities_rotation(AddNodePanel, CompositorNodesPanel):
    bl_label = "Rotation"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_rotation_base


class NODES_PT_toolshelf_compositor_add_utilities_vector(AddNodePanel, CompositorNodesPanel):
    bl_label = "Vector"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_vector_base


class NODES_PT_toolshelf_compositor_add_utilities_text(AddNodePanel, CompositorNodesPanel):
    bl_label = "Text"
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"
    layout_base = node_add_menu_compositor.NODE_MT_compositor_node_text_base


class NODES_PT_toolshelf_texture_add_input(AddNodePanel):
    bl_label = "Input"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_input_base


class NODES_PT_toolshelf_texture_add_output(AddNodePanel):
    bl_label = "Output"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_output_base


class NODES_PT_toolshelf_texture_add_color(AddNodePanel):
    bl_label = "Color"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_color_base


class NODES_PT_toolshelf_texture_add_converter(AddNodePanel):
    bl_label = "Converter"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_converter_base


class NODES_PT_toolshelf_texture_add_distort(AddNodePanel):
    bl_label = "Distort"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_distort_base


class NODES_PT_toolshelf_texture_add_pattern(AddNodePanel):
    bl_label = "Pattern"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_pattern_base


class NODES_PT_toolshelf_texture_add_texture(AddNodePanel):
    bl_label = "Textures"
    layout_base = node_add_menu_texture.NODE_MT_texture_node_texture_base


class NODES_PT_toolshelf_gn_add_input(AddNodePanel, GeometryNodesPanel):
    bl_label = "Input"
    layout_base = node_add_menu_geometry.NODE_MT_gn_input_base

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_input_constant(AddNodePanel, GeometryNodesPanel):
    bl_label = "Constant"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"
    layout_base = node_add_menu_geometry.NODE_MT_gn_input_constant_base


class NODES_PT_toolshelf_gn_add_input_gizmo(AddNodePanel, GeometryNodesPanel):
    bl_label = "Gizmo"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"
    
    layout_base = node_add_menu_geometry.NODE_MT_gn_input_gizmo_base

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') and (not is_tool_tree(context))


class NODES_PT_toolshelf_gn_add_input_file(AddNodePanel, GeometryNodesPanel):
    bl_label = "Import"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"
    layout_base = node_add_menu_geometry.NODE_MT_gn_input_import_base


class NODES_PT_toolshelf_gn_add_input_scene(AddNodePanel, GeometryNodesPanel):
    bl_label = "Scene"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"
    layout_base = node_add_menu_geometry.NODE_MT_gn_input_scene_base


class NODES_PT_toolshelf_gn_add_output(AddNodePanel, GeometryNodesPanel):
    bl_label = "Output"
    layout_base = node_add_menu_geometry.NODE_MT_gn_output_base


class NODES_PT_toolshelf_gn_add_attribute(AddNodePanel, GeometryNodesPanel):
    bl_label = "Attribute"
    layout_base = node_add_menu_geometry.NODE_MT_gn_attribute_base


class NODES_PT_toolshelf_gn_add_geometry(AddNodePanel, GeometryNodesPanel):
    bl_label = "Geometry"
    layout_base = node_add_menu_geometry.NODE_MT_gn_geometry_base


class NODES_PT_toolshelf_gn_add_geometry_read(AddNodePanel, GeometryNodesPanel):
    bl_label = "Read"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"
    layout_base = node_add_menu_geometry.NODE_MT_gn_geometry_read_base


class NODES_PT_toolshelf_gn_add_geometry_sample(AddNodePanel, GeometryNodesPanel):
    bl_label = "Sample"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"
    layout_base = node_add_menu_geometry.NODE_MT_gn_geometry_sample_base


class NODES_PT_toolshelf_gn_add_geometry_write(AddNodePanel, GeometryNodesPanel):
    bl_label = "Write"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"
    layout_base = node_add_menu_geometry.NODE_MT_gn_geometry_write_base


class NODES_PT_toolshelf_gn_add_geometry_material(AddNodePanel, GeometryNodesPanel):
    bl_label = "Material"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"
    layout_base = node_add_menu_geometry.NODE_MT_gn_material_base


class NODES_PT_toolshelf_gn_add_geometry_operations(AddNodePanel, GeometryNodesPanel):
    bl_label = "Operations"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_geometry"
    layout_base = node_add_menu_geometry.NODE_MT_gn_geometry_operations_base


class NODES_PT_toolshelf_gn_add_curve(AddNodePanel, GeometryNodesPanel):
    bl_label = "Curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_base

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_curve_read(AddNodePanel, GeometryNodesPanel):
    bl_label = "Read"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_read_base


class NODES_PT_toolshelf_gn_add_curve_sample(AddNodePanel, GeometryNodesPanel):
    bl_label = "Sample"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_sample_base


class NODES_PT_toolshelf_gn_add_curve_write(AddNodePanel, GeometryNodesPanel):
    bl_label = "Write"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_write_base


class NODES_PT_toolshelf_gn_add_curve_operations(AddNodePanel, GeometryNodesPanel):
    bl_label = "Operations"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_operations_base


class NODES_PT_toolshelf_gn_add_curve_primitives(AddNodePanel, GeometryNodesPanel):
    bl_label = "Primitives"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_primitives_base


class NODES_PT_toolshelf_gn_add_curve_topology(AddNodePanel, GeometryNodesPanel):
    bl_label = "Topology"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_curve"
    layout_base = node_add_menu_geometry.NODE_MT_gn_curve_topology_base


class NODES_PT_toolshelf_gn_add_grease_pencil(AddNodePanel, GeometryNodesPanel):
    bl_label = "Grease Pencil"
    layout_base = node_add_menu_geometry.NODE_MT_gn_grease_pencil_base

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_grease_pencil_read(AddNodePanel, GeometryNodesPanel):
    bl_label = "Read"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_grease_pencil"
    layout_base = node_add_menu_geometry.NODE_MT_gn_grease_pencil_read_base


class NODES_PT_toolshelf_gn_add_grease_pencil_write(AddNodePanel, GeometryNodesPanel):
    bl_label = "Write"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_grease_pencil"
    layout_base = node_add_menu_geometry.NODE_MT_gn_grease_pencil_write_base


class NODES_PT_toolshelf_gn_add_grease_pencil_operations(AddNodePanel, GeometryNodesPanel):
    bl_label = "Operations"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_grease_pencil"
    layout_base = node_add_menu_geometry.NODE_MT_gn_grease_pencil_operations_base


class NODES_PT_toolshelf_gn_add_instances(AddNodePanel, GeometryNodesPanel):
    bl_label = "Instances"
    layout_base = node_add_menu_geometry.NODE_MT_gn_instance_base


class NODES_PT_toolshelf_gn_add_mesh(AddNodePanel, GeometryNodesPanel):
    bl_label = "Mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_base

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_mesh_read(AddNodePanel, GeometryNodesPanel):
    bl_label = "Read"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_read_base


class NODES_PT_toolshelf_gn_add_mesh_sample(AddNodePanel, GeometryNodesPanel):
    bl_label = "Sample"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_sample_base


class NODES_PT_toolshelf_gn_add_mesh_write(AddNodePanel, GeometryNodesPanel):
    bl_label = "Write"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_write_base


class NODES_PT_toolshelf_gn_add_mesh_operations(AddNodePanel, GeometryNodesPanel):
    bl_label = "Operations"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_operations_base


class NODES_PT_toolshelf_gn_add_mesh_primitives(AddNodePanel, GeometryNodesPanel):
    bl_label = "Primitives"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_primitives_base


class NODES_PT_toolshelf_gn_add_mesh_topology(AddNodePanel, GeometryNodesPanel):
    bl_label = "Topology"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_topology_base


class NODES_PT_toolshelf_gn_add_mesh_uv(AddNodePanel, GeometryNodesPanel):
    bl_label = "UV"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_mesh"
    layout_base = node_add_menu_geometry.NODE_MT_gn_mesh_uv_base


class NODES_PT_toolshelf_gn_add_point(AddNodePanel, GeometryNodesPanel):
    bl_label = "Point"
    layout_base = node_add_menu_geometry.NODE_MT_gn_point_base


class NODES_PT_toolshelf_gn_add_volume(AddNodePanel, GeometryNodesPanel):
    bl_label = "Volume"
    layout_base = node_add_menu_geometry.NODE_MT_gn_volume_base


class NODES_PT_toolshelf_gn_add_volume_read(AddNodePanel, GeometryNodesPanel):
    bl_label = "Read"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"
    layout_base = node_add_menu_geometry.NODE_MT_gn_volume_read_base


class NODES_PT_toolshelf_gn_add_volume_sample(AddNodePanel, GeometryNodesPanel):
    bl_label = "Sample"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"
    layout_base = node_add_menu_geometry.NODE_MT_gn_volume_sample_base


class NODES_PT_toolshelf_gn_add_volume_write(AddNodePanel, GeometryNodesPanel):
    bl_label = "Write"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"
    layout_base = node_add_menu_geometry.NODE_MT_gn_volume_write_base


class NODES_PT_toolshelf_gn_add_volume_operations(AddNodePanel, GeometryNodesPanel):
    bl_label = "Operations"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"
    layout_base = node_add_menu_geometry.NODE_MT_gn_volume_operations_base


class NODES_PT_toolshelf_gn_add_volume_primitives(AddNodePanel, GeometryNodesPanel):
    bl_label = "Primitives"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"
    layout_base = node_add_menu_geometry.NODE_MT_gn_volume_primitives_base


class NODES_PT_toolshelf_gn_add_simulation(AddNodePanel, GeometryNodesPanel):
    bl_label = "Simulation"
    layout_base = node_add_menu_geometry.NODE_MT_gn_simulation_base


class NODES_PT_toolshelf_gn_add_color(AddNodePanel, GeometryNodesPanel):
    bl_label = "Color"
    layout_base = node_add_menu_geometry.NODE_MT_gn_color_base


class NODES_PT_toolshelf_gn_add_texture(AddNodePanel, GeometryNodesPanel):
    bl_label = "Texture"
    layout_base = node_add_menu_geometry.NODE_MT_gn_texture_base


class NODES_PT_toolshelf_gn_add_utilities(AddNodePanel, GeometryNodesPanel):
    bl_label = "Utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_base


class NODES_PT_toolshelf_gn_add_utilities_math(AddNodePanel, GeometryNodesPanel):
    bl_label = "Math"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_math_base


class NODES_PT_toolshelf_gn_add_utilities_text(AddNodePanel, GeometryNodesPanel):
    bl_label = "Text"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_text_base


class NODES_PT_toolshelf_gn_add_utilities_vector(AddNodePanel, GeometryNodesPanel):
    bl_label = "Vector"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_vector_base


class NODES_PT_toolshelf_gn_add_utilities_bundle(AddNodePanel, GeometryNodesPanel):
    bl_label = "Bundle"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_category_utilities_bundle_base


class NODES_PT_toolshelf_gn_add_utilities_closure(AddNodePanel, GeometryNodesPanel):
    bl_label = "Closure"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_category_utilities_closure_base


class NODES_PT_toolshelf_gn_add_utilities_field(AddNodePanel, GeometryNodesPanel):
    bl_label = "Field"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_field_base


class NODES_PT_toolshelf_gn_add_utilities_lists(AddNodePanel, GeometryNodesPanel):
    bl_label = "Lists"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_list_base


class NODES_PT_toolshelf_gn_add_utilities_matrix(AddNodePanel, GeometryNodesPanel):
    bl_label = "Matrix"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_matrix_base


class NODES_PT_toolshelf_gn_add_utilities_rotation(AddNodePanel, GeometryNodesPanel):
    bl_label = "Rotation"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_rotation_base


class NODES_PT_toolshelf_gn_add_utilities_sound(AddNodePanel, GeometryNodesPanel):
    bl_label = "Sound"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_sound_base


class NODES_PT_toolshelf_gn_add_utilities_deprecated(AddNodePanel, GeometryNodesPanel):
    bl_label = "Deprecated"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_utilities"
    layout_base = node_add_menu_geometry.NODE_MT_gn_utilities_deprecated_base


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
    NODES_PT_toolshelf_shader_add_input_constant,
    NODES_PT_toolshelf_shader_add_output,
    NODES_PT_toolshelf_shader_add_shader,
    NODES_PT_toolshelf_shader_add_displacement,
    NODES_PT_toolshelf_shader_add_color,
    NODES_PT_toolshelf_shader_add_texture,
    NODES_PT_toolshelf_shader_add_utilities,
    NODES_PT_toolshelf_shader_add_math,
    NODES_PT_toolshelf_shader_add_vector,
    #-----------------------

    #-----------------------
    # Compositor Nodes - Add
    NODES_PT_toolshelf_compositor_add_input,
    NODES_PT_toolshelf_compositor_add_input_constant,
    NODES_PT_toolshelf_compositor_add_input_scene,
    NODES_PT_toolshelf_compositor_add_output,
    NODES_PT_toolshelf_compositor_add_color,
    NODES_PT_toolshelf_compositor_add_color_adjust,
    NODES_PT_toolshelf_compositor_add_creative,
    NODES_PT_toolshelf_compositor_add_filter,
    NODES_PT_toolshelf_compositor_add_filter_blur,
    NODES_PT_toolshelf_compositor_add_keying,
    NODES_PT_toolshelf_compositor_add_mask,
    NODES_PT_toolshelf_compositor_add_tracking,
    NODES_PT_toolshelf_compositor_add_texture,
    NODES_PT_toolshelf_compositor_add_transform,
    NODES_PT_toolshelf_compositor_add_utilities,
    NODES_PT_toolshelf_compositor_add_utilities_math,
    NODES_PT_toolshelf_compositor_add_utilities_matrix,
    NODES_PT_toolshelf_compositor_add_utilities_rotation,
    NODES_PT_toolshelf_compositor_add_utilities_vector,
    NODES_PT_toolshelf_compositor_add_utilities_text,
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
    NODES_PT_toolshelf_gn_add_input,
    NODES_PT_toolshelf_gn_add_input_constant,
    NODES_PT_toolshelf_gn_add_input_gizmo,
    NODES_PT_toolshelf_gn_add_input_file,
    NODES_PT_toolshelf_gn_add_input_scene,

    NODES_PT_toolshelf_gn_add_output,
    
    NODES_PT_toolshelf_gn_add_attribute,

    NODES_PT_toolshelf_gn_add_geometry,
    NODES_PT_toolshelf_gn_add_geometry_read,
    NODES_PT_toolshelf_gn_add_geometry_sample,
    NODES_PT_toolshelf_gn_add_geometry_write,
    NODES_PT_toolshelf_gn_add_geometry_material,
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
    NODES_PT_toolshelf_gn_add_volume_read,
    NODES_PT_toolshelf_gn_add_volume_sample,
    NODES_PT_toolshelf_gn_add_volume_write,
    NODES_PT_toolshelf_gn_add_volume_operations,
    NODES_PT_toolshelf_gn_add_volume_primitives,

    NODES_PT_toolshelf_gn_add_simulation,
    NODES_PT_toolshelf_gn_add_color,
    NODES_PT_toolshelf_gn_add_texture,

    NODES_PT_toolshelf_gn_add_utilities,
    NODES_PT_toolshelf_gn_add_utilities_math,
    NODES_PT_toolshelf_gn_add_utilities_text,
    NODES_PT_toolshelf_gn_add_utilities_vector,
    NODES_PT_toolshelf_gn_add_utilities_bundle,
    NODES_PT_toolshelf_gn_add_utilities_closure,
    NODES_PT_toolshelf_gn_add_utilities_field,
    NODES_PT_toolshelf_gn_add_utilities_lists,
    NODES_PT_toolshelf_gn_add_utilities_matrix,
    NODES_PT_toolshelf_gn_add_utilities_rotation,
    NODES_PT_toolshelf_gn_add_utilities_sound,
    NODES_PT_toolshelf_gn_add_utilities_deprecated,
    #-----------------------
)

# BFA - Custom panels for the sidebar toolshelf (END)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

