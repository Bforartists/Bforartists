# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.app.translations import (
    pgettext_iface as iface_,
)

import dataclasses

from nodeitems_builtins import node_tree_group_type
from .node_add_menu import draw_node_groups, add_empty_group


# BFA - Custom panels for the sidebar toolshelf
# BFA - to define padding, it helps to count 2 points per character.

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
        return context.space_data.geometry_nodes_type == 'TOOL'
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


class NODES_PT_relations_group_operations(bpy.types.Panel, NodePanel):
    bl_label = "Group"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"

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


class NODES_PT_toolshelf_shader_add_input(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeFresnel", pad=23),
                OperatorEntry("ShaderNodeNewGeometry", pad=19),
                OperatorEntry("ShaderNodeRGB", pad=28),
                OperatorEntry("ShaderNodeTexCoord", pad=2),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeAmbientOcclusion", pad=2),
                OperatorEntry("ShaderNodeAttribute", pad=20),
                OperatorEntry("ShaderNodeBevel", pad=25),
                OperatorEntry("ShaderNodeCameraData", pad=12),
                OperatorEntry("ShaderNodeVertexColor", pad=9),
                OperatorEntry("ShaderNodeFresnel", pad=21),
                Separator,
                OperatorEntry("ShaderNodeNewGeometry", pad=17),
                OperatorEntry("ShaderNodeHairInfo", pad=13),
                OperatorEntry("ShaderNodeLayerWeight", pad=11),
                OperatorEntry("ShaderNodeLightPath", pad=16),
                OperatorEntry("ShaderNodeObjectInfo", pad=14),
                Separator,
                OperatorEntry("ShaderNodeParticleInfo", pad=12),
                OperatorEntry("ShaderNodePointInfo", pad=17),
                OperatorEntry("ShaderNodeRGB", pad=26),
                OperatorEntry("ShaderNodeTangent", pad=19),
                OperatorEntry("ShaderNodeTexCoord", pad=0),
                OperatorEntry("ShaderNodeUVAlongStroke", pad=4, poll=is_shader_type(context, 'LINESTYLE')),
                Separator,
                OperatorEntry("ShaderNodeUVMap", pad=19),
                OperatorEntry("ShaderNodeValue", pad=23),
                OperatorEntry("ShaderNodeVolumeInfo", pad=11),
                OperatorEntry("ShaderNodeWireframe", pad=14),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_output(bpy.types.Panel, NodePanel):
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


class NODES_PT_toolshelf_shader_add_shader(bpy.types.Panel, NodePanel):
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
                OperatorEntry("ShaderNodeBsdfRayPortal", pad=6, poll=is_object and not is_eevee),
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


class NODES_PT_toolshelf_shader_add_displacement(bpy.types.Panel, NodePanel):
    bl_label = "Displacement"
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


class NODES_PT_toolshelf_shader_add_color(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeValToRGB", pad=8),
                OperatorEntry("ShaderNodeBrightContrast", pad=3),
                OperatorEntry("ShaderNodeGamma", pad=24),
                OperatorEntry("ShaderNodeHueSaturation", pad=0),
                OperatorEntry("ShaderNodeInvert", pad=16),
                OperatorEntry("ShaderNodeMix", text="Mix Color", pad=20, settings={"data_type": "'RGBA'"}),
                OperatorEntry("ShaderNodeRGBCurve", pad=16),
                Separator,
                OperatorEntry("ShaderNodeCombineColor", pad=3),
                OperatorEntry("ShaderNodeSeparateColor", pad=2),
                Separator,
                OperatorEntry("ShaderNodeShaderToRGB", pad=3, poll=is_engine(context, 'BLENDER_EEVEE')),
                OperatorEntry("ShaderNodeRGBToBW", pad=9),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeBlackbody", pad=10),
                OperatorEntry("ShaderNodeValToRGB", pad=8),
                OperatorEntry("ShaderNodeBrightContrast", pad=3),
                OperatorEntry("ShaderNodeGamma", pad=24),
                OperatorEntry("ShaderNodeHueSaturation", pad=0),
                OperatorEntry("ShaderNodeInvert", pad=16),
                OperatorEntry("ShaderNodeMix", text="Mix Color", pad=20, settings={"data_type": "'RGBA'"}),
                OperatorEntry("ShaderNodeLightFalloff", pad=16),
                OperatorEntry("ShaderNodeRGBCurve", pad=16),
                OperatorEntry("ShaderNodeWavelength", pad=7),
                Separator,
                OperatorEntry("ShaderNodeCombineColor", pad=3),
                OperatorEntry("ShaderNodeSeparateColor", pad=2),
                Separator,
                OperatorEntry("ShaderNodeShaderToRGB", pad=3, poll=is_engine(context, 'BLENDER_EEVEE')),
                OperatorEntry("ShaderNodeRGBToBW", pad=9),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_texture(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeTexEnvironment", pad=0),
                OperatorEntry("ShaderNodeTexImage", pad=10),
                OperatorEntry("ShaderNodeTexNoise", pad=12),
                OperatorEntry("ShaderNodeTexSky", pad=15),
                OperatorEntry("ShaderNodeTexVoronoi", pad=8),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeTexBrick", pad=13),
                OperatorEntry("ShaderNodeTexChecker", pad=7),
                OperatorEntry("ShaderNodeTexEnvironment", pad=0),
                OperatorEntry("ShaderNodeTexGabor", pad=11),
                OperatorEntry("ShaderNodeTexGradient", pad=7),
                OperatorEntry("ShaderNodeTexIES", pad=15),
                Separator,
                OperatorEntry("ShaderNodeTexImage", pad=10),
                OperatorEntry("ShaderNodeTexMagic", pad=11),
                OperatorEntry("ShaderNodeTexNoise", pad=12),
                OperatorEntry("ShaderNodeTexSky", pad=15),
                Separator,
                OperatorEntry("ShaderNodeTexVoronoi", pad=8),
                OperatorEntry("ShaderNodeTexWave", pad=12),
                OperatorEntry("ShaderNodeTexWhiteNoise", pad=0),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_utilities(bpy.types.Panel, NodePanel):
    bl_label = "Utilities"
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=20, settings={"data_type": "'FLOAT_VECTOR'"}),#
                OperatorEntry(operator="node.add_repeat_zone", pad=18, text="Repeat Zone", icon="REPEAT"),
                Separator,
                OperatorEntry("NodeCombineBundle", pad=17),
                OperatorEntry("NodeSeparateBundle", pad=16),
                Separator,
                OperatorEntry("GeometryNodeMenuSwitch", pad=22),
            )

        else:
            entries = (
                OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=20, settings={"data_type": "'FLOAT_VECTOR'"}),#
                OperatorEntry(operator="node.add_repeat_zone", pad=18, text="Repeat Zone", icon="REPEAT"),
                Separator,
                OperatorEntry("NodeClosureInput", pad=18),
                OperatorEntry("NodeClosureOutput", pad=16),
                OperatorEntry("NodeCombineBundle", pad=15),
                OperatorEntry("NodeSeparateBundle", pad=15),
                Separator,
                OperatorEntry("GeometryNodeMenuSwitch", pad=22),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_vector(bpy.types.Panel, NodePanel):
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_utilities"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeCombineXYZ", pad=12),
                OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=16, settings={"data_type": "'FLOAT_VECTOR'"}),
                OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), pad=17, settings={"data_type": "'VECTOR'"}),
                OperatorEntry("ShaderNodeSeparateXYZ", pad=2),
                Separator,
                OperatorEntry("ShaderNodeMapping", pad=23),
                OperatorEntry("ShaderNodeNormal", pad=25),
                OperatorEntry("ShaderNodeRadialTiling", pad=18),
                OperatorEntry("ShaderNodeVectorMath", pad=16),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeCombineXYZ", pad=12),
                OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=16, settings={"data_type": "'FLOAT_VECTOR'"}),
                OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), pad=17, settings={"data_type": "'VECTOR'"}),
                OperatorEntry("ShaderNodeSeparateXYZ", pad=12),
                Separator,
                OperatorEntry("ShaderNodeMapping", pad=23),
                OperatorEntry("ShaderNodeNormal", pad=25),
                OperatorEntry("ShaderNodeRadialTiling", pad=18),
                OperatorEntry("ShaderNodeVectorMath", pad=16),
                OperatorEntry("ShaderNodeVectorCurve", pad=12),
                OperatorEntry("ShaderNodeVectorRotate", pad=12),
                OperatorEntry("ShaderNodeVectorTransform", pad=8),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_math(bpy.types.Panel, NodePanel):
    bl_label = "Math"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_utilities"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences
        use_common = addon_prefs.Node_shader_add_common

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        if use_common:
            entries = (
                OperatorEntry("ShaderNodeClamp", pad=22),
                OperatorEntry("ShaderNodeFloatCurve", pad=13),
                OperatorEntry("ShaderNodeMapRange", pad=13),
                OperatorEntry("ShaderNodeMath", pad=24),
                OperatorEntry("ShaderNodeMix", pad=27),
            )
        else:
            entries = (
                OperatorEntry("ShaderNodeClamp", pad=22),
                OperatorEntry("ShaderNodeFloatCurve", pad=13),
                OperatorEntry("ShaderNodeMapRange", pad=13),
                OperatorEntry("ShaderNodeMath", pad=24),
                OperatorEntry("ShaderNodeMix", pad=27),
            )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_shader_add_script(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeScript", pad=20),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_input(bpy.types.Panel, NodePanel):
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeBokehImage", pad=11),
            OperatorEntry("CompositorNodeImage", pad=23),
            OperatorEntry("CompositorNodeImageInfo", pad=15),
            OperatorEntry("CompositorNodeImageCoordinates", pad=1),
            OperatorEntry("CompositorNodeMask", pad=25),
            OperatorEntry("CompositorNodeMovieClip", pad=16),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_input_constant(bpy.types.Panel, NodePanel):
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_input"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeRGB", pad=20),
            OperatorEntry("ShaderNodeValue", pad=18),
            OperatorEntry("CompositorNodeNormal", pad=16),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_input_scene(bpy.types.Panel, NodePanel):
    bl_label = "Scene"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_input"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeRLayers", pad=4),
            OperatorEntry("CompositorNodeSceneTime", pad=8),
            OperatorEntry("CompositorNodeTime", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_output(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("NodeEnableOutput", pad=15),
            OperatorEntry("CompositorNodeViewer", pad=15),
            Separator,
            OperatorEntry("CompositorNodeOutputFile", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_color(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodePremulKey", pad=13),
            OperatorEntry("ShaderNodeBlackbody", pad=20),
            OperatorEntry("ShaderNodeValToRGB", pad=18),
            OperatorEntry("CompositorNodeConvertColorSpace", pad=3),
            OperatorEntry("CompositorNodeConvertToDisplay", pad=5),
            OperatorEntry("CompositorNodeSetAlpha", pad=21),
            Separator,
            OperatorEntry("CompositorNodeInvert", pad=16),
            OperatorEntry("CompositorNodeRGBToBW", pad=18),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_color_adjust(bpy.types.Panel, NodePanel):
    bl_label = "Adjust"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_color"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeBrightContrast", pad=5),
            OperatorEntry("CompositorNodeColorBalance", pad=14),
            OperatorEntry("CompositorNodeColorCorrection", pad=10),

            OperatorEntry("CompositorNodeExposure", pad=22),
            OperatorEntry("CompositorNodeGamma", pad=25),
            OperatorEntry("CompositorNodeHueCorrect", pad=17),
            OperatorEntry("CompositorNodeHueSat", pad=1),
            OperatorEntry("CompositorNodeCurveRGB", pad=17),
            OperatorEntry("CompositorNodeTonemap", pad=21),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_color_mix(bpy.types.Panel, NodePanel):
    bl_label = "Mix"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_color"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeAlphaOver", pad=8),
            Separator,
            OperatorEntry("CompositorNodeCombineColor", pad=2),
            OperatorEntry("CompositorNodeSeparateColor", pad=2),
            Separator,
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Color"), pad=12, settings={"data_type": "'RGBA'"}),
            OperatorEntry("CompositorNodeZcombine", pad=2),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_filter(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeAntiAliasing", pad=1),
            OperatorEntry("CompositorNodeConvolve", pad=7),
            OperatorEntry("CompositorNodeDenoise", pad=9),
            OperatorEntry("CompositorNodeDespeckle", pad=5),
            Separator,
            OperatorEntry("CompositorNodeDilateErode", pad=2),
            OperatorEntry("CompositorNodeInpaint", pad=10),
            Separator,
            OperatorEntry("CompositorNodeFilter", pad=13),
            OperatorEntry("CompositorNodeGlare", pad=13),
            OperatorEntry("CompositorNodeKuwahara", pad=5),
            OperatorEntry("CompositorNodePixelate", pad=8),
            OperatorEntry("CompositorNodePosterize", pad=6),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_filter_blur(bpy.types.Panel, NodePanel):
    bl_label = "Blur"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_filter"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeBilateralblur", pad=7),
            OperatorEntry("CompositorNodeBlur", pad=22),
            OperatorEntry("CompositorNodeBokehBlur", pad=10),
            OperatorEntry("CompositorNodeDefocus", pad=14),
            OperatorEntry("CompositorNodeDBlur", pad=2),
            OperatorEntry("CompositorNodeVecBlur", pad=9),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_keying(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeChannelMatte", pad=5),
            OperatorEntry("CompositorNodeChromaMatte", pad=6),
            OperatorEntry("CompositorNodeColorMatte", pad=10),
            OperatorEntry("CompositorNodeColorSpill", pad=9),
            OperatorEntry("CompositorNodeDiffMatte", pad=1),
            OperatorEntry("CompositorNodeDistanceMatte", pad=4),
            OperatorEntry("CompositorNodeKeying", pad=15),
            OperatorEntry("CompositorNodeKeyingScreen", pad=2),
            OperatorEntry("CompositorNodeLumaMatte", pad=1),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_mask(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeCryptomatteV2", pad=18),
            OperatorEntry("CompositorNodeCryptomatte", pad=1),
            Separator,
            OperatorEntry("CompositorNodeBoxMask", pad=22),
            OperatorEntry("CompositorNodeEllipseMask", pad=17),
            Separator,
            OperatorEntry("CompositorNodeDoubleEdgeMask", pad=6),
            OperatorEntry("CompositorNodeIDMask", pad=24),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_tracking(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodePlaneTrackDeform", pad=0),
            OperatorEntry("CompositorNodeStabilize", pad=14),
            OperatorEntry("CompositorNodeTrackPos", pad=10),
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeTexBrick", pad=11),
            OperatorEntry("ShaderNodeTexChecker", pad=6),
            OperatorEntry("ShaderNodeTexGabor", pad=10),
            OperatorEntry("ShaderNodeTexGradient", pad=6),
            OperatorEntry("ShaderNodeTexMagic", pad=10),
            OperatorEntry("ShaderNodeTexNoise", pad=10),
            OperatorEntry("ShaderNodeTexVoronoi", pad=7),
            OperatorEntry("ShaderNodeTexWave", pad=11),
            OperatorEntry("ShaderNodeTexWhiteNoise", pad=0),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_transform(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeRotate", pad=17),
            OperatorEntry("CompositorNodeScale", pad=19),
            OperatorEntry("CompositorNodeTransform", pad=11),
            OperatorEntry("CompositorNodeTranslate", pad=13),
            Separator,
            OperatorEntry("CompositorNodeCornerPin", pad=10),
            OperatorEntry("CompositorNodeCrop", pad=20),
            Separator,
            OperatorEntry("CompositorNodeDisplace", pad=13),
            OperatorEntry("CompositorNodeFlip", pad=21),
            OperatorEntry("CompositorNodeMapUV", pad=14),
            Separator,
            OperatorEntry("CompositorNodeLensdist", pad=2),
            OperatorEntry("CompositorNodeMovieDistortion", pad=0),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_utilities(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("CompositorNodeLevels", pad=22),
            OperatorEntry("CompositorNodeNormalize", pad=16),
            Separator,
            OperatorEntry("CompositorNodeSplit", pad=26),
            OperatorEntry("CompositorNodeSwitch", pad=22),
            OperatorEntry("GeometryNodeIndexSwitch", pad=11),
            OperatorEntry("GeometryNodeMenuSwitch", pad=11),
            OperatorEntry("CompositorNodeSwitchView", pad=0, text="Switch Stereo View"),
            Separator,
            OperatorEntry("CompositorNodeRelativeToPixel", pad=5),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_utilities_math(bpy.types.Panel, NodePanel):
    bl_label = "Math"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeClamp", pad=22),
            OperatorEntry("ShaderNodeFloatCurve", pad=13),
            OperatorEntry("ShaderNodeMapRange", pad=13),
            OperatorEntry("ShaderNodeMath", pad=24),
            OperatorEntry("ShaderNodeMix", pad=27),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_utilities_vector(bpy.types.Panel, NodePanel):
    bl_label = "Vector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_compositor_add_utilities"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'CompositorNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeCombineXYZ", pad=4),
            OperatorEntry("ShaderNodeMapRange", pad=9, settings={"data_type": "'FLOAT_VECTOR'"}),
            OperatorEntry("ShaderNodeMix", text="Mix Vector", pad=9, settings={"data_type": "'VECTOR'"}),
            OperatorEntry("ShaderNodeSeparateXYZ", pad=4),
            Separator,
            OperatorEntry("ShaderNodeRadialTiling", pad=10),
            OperatorEntry("ShaderNodeVectorCurve", pad=3),
            OperatorEntry("ShaderNodeVectorMath", pad=7),
            OperatorEntry("ShaderNodeVectorRotate", pad=4),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_input(bpy.types.Panel, NodePanel):
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeCoordinates", pad=0),
            OperatorEntry("TextureNodeCurveTime", pad=12),
            OperatorEntry("TextureNodeImage", pad=9),
            OperatorEntry("TextureNodeTexture", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_output(bpy.types.Panel, NodePanel):
    bl_label = "Output"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeOutput", pad=4),
            OperatorEntry("TextureNodeViewer", pad=3),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_color(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeHueSaturation", pad=0),
            OperatorEntry("TextureNodeInvert", pad=16),
            OperatorEntry("TextureNodeMixRGB", pad=31),
            OperatorEntry("TextureNodeCurveRGB", pad=17),
            Separator,
            OperatorEntry("TextureNodeCombineColor", pad=12),
            OperatorEntry("TextureNodeSeparateColor", pad=12),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_converter(bpy.types.Panel, NodePanel):
    bl_label = "Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeValToRGB", pad=9),
            OperatorEntry("TextureNodeDistance", pad=14),
            OperatorEntry("TextureNodeMath", pad=20),
            OperatorEntry("TextureNodeRGBToBW", pad=10),
            Separator,
            OperatorEntry("TextureNodeValToNor", pad=1),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_distort(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeAt", pad=19),
            OperatorEntry("TextureNodeRotate", pad=12),
            OperatorEntry("TextureNodeScale", pad=14),
            OperatorEntry("TextureNodeTranslate", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_pattern(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeBricks", pad=4),
            OperatorEntry("TextureNodeChecker", pad=1),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_texture_add_texture(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("TextureNodeTexBlend", pad=18),
            OperatorEntry("TextureNodeTexClouds", pad=16),
            OperatorEntry("TextureNodeTexDistNoise", pad=1),
            OperatorEntry("TextureNodeTexMagic", pad=17),
            Separator,
            OperatorEntry("TextureNodeTexMarble", pad=9),
            OperatorEntry("TextureNodeTexNoise", pad=17),
            OperatorEntry("TextureNodeTexStucci", pad=10),
            OperatorEntry("TextureNodeTexVoronoi", pad=13),
            Separator,
            OperatorEntry("TextureNodeTexWood", pad=10),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_attribute(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeAttributeStatistic", pad=15),
            OperatorEntry("GeometryNodeAttributeDomainSize", pad=24),
            Separator,
            OperatorEntry("GeometryNodeBlurAttribute", pad=22),
            OperatorEntry("GeometryNodeCaptureAttribute", pad=15),
            OperatorEntry("GeometryNodeRemoveAttribute", pad=2),
            OperatorEntry("GeometryNodeStoreNamedAttribute", pad=7),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_input(bpy.types.Panel, NodePanel):
    bl_label = "Input"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout


class NODES_PT_toolshelf_gn_add_input_constant(bpy.types.Panel, NodePanel):
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("FunctionNodeInputBool",pad=8),
            OperatorEntry("GeometryNodeInputCollection",pad=5),
            OperatorEntry("FunctionNodeInputColor",pad=13),
            OperatorEntry("GeometryNodeInputImage",pad=11),
            OperatorEntry("FunctionNodeInputInt",pad=10),
            OperatorEntry("GeometryNodeInputMaterial",pad=9),
            OperatorEntry("GeometryNodeInputObject",pad=11),
            OperatorEntry("FunctionNodeInputRotation",pad=8),
            OperatorEntry("FunctionNodeInputString",pad=12),
            OperatorEntry("ShaderNodeValue",pad=12),
            OperatorEntry("FunctionNodeInputVector",pad=11),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_input_gizmo(bpy.types.Panel, NodePanel):
    bl_label = "Gizmo"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeGizmoDial", pad=13),
            OperatorEntry("GeometryNodeGizmoLinear", pad=9),
            OperatorEntry("GeometryNodeGizmoTransform", pad=2),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_input_file(bpy.types.Panel, NodePanel):
    bl_label = "Import"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeImportOBJ", pad=2),
            OperatorEntry("GeometryNodeImportPLY", pad=2),
            OperatorEntry("GeometryNodeImportSTL", pad=3),
            OperatorEntry("GeometryNodeImportCSV", pad=2),
            OperatorEntry("GeometryNodeImportText", pad=2),
            OperatorEntry("GeometryNodeImportVDB", pad=2),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_input_scene(bpy.types.Panel, NodePanel):
    bl_label = "Scene"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_input"

    def draw(self, context):
        layout = self.layout

        is_tool = is_tool_tree(context)
        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeTool3DCursor", pad=21, poll=is_tool),
            OperatorEntry("GeometryNodeInputActiveCamera", pad=14),
            OperatorEntry("GeometryNodeBoneInfo", pad=22),
            OperatorEntry("GeometryNodeCameraInfo", pad=18),
            OperatorEntry("GeometryNodeCollectionInfo", pad=14),
            OperatorEntry("GeometryNodeImageInfo", pad=21),
            OperatorEntry("GeometryNodeIsViewport", pad=20),
            OperatorEntry("GeometryNodeInputNamedLayerSelection", pad=0),
            OperatorEntry("GeometryNodeToolMousePosition", pad=14, poll=is_tool),
            OperatorEntry("GeometryNodeObjectInfo", pad=20),
            OperatorEntry("GeometryNodeInputSceneTime", pad=19),
            OperatorEntry("GeometryNodeSelfObject", pad=21),
            OperatorEntry("GeometryNodeViewportTransform", pad=6, poll=is_tool),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_output(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("NodeEnableOutput", pad=10),
            OperatorEntry("GeometryNodeViewer", pad=4),
            OperatorEntry("GeometryNodeWarning", pad=2),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeGeometryToInstance", pad=2),
            OperatorEntry("GeometryNodeJoinGeometry", pad=14),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_read(bpy.types.Panel, NodePanel):
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
        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeInputID", pad=24),
            OperatorEntry("GeometryNodeInputIndex", pad=19),
            OperatorEntry("GeometryNodeInputNamedAttribute", pad=1),
            OperatorEntry("GeometryNodeInputNormal", pad=17),
            OperatorEntry("GeometryNodeInputPosition", pad=16),
            OperatorEntry("GeometryNodeInputRadius", pad=18),
            OperatorEntry("GeometryNodeToolSelection", pad=13, poll=is_tool),
            OperatorEntry("GeometryNodeToolActiveElement", pad=4, poll=is_tool),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_sample(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeProximity", pad=1),
            OperatorEntry("GeometryNodeIndexOfNearest", pad=5),
            OperatorEntry("GeometryNodeRaycast", pad=21),
            OperatorEntry("GeometryNodeSampleIndex", pad=11),
            OperatorEntry("GeometryNodeSampleNearest", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_write(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeSetGeometryName", pad=1),
            OperatorEntry("GeometryNodeSetID", pad=25),
            OperatorEntry("GeometryNodeSetPosition", pad=15),
            OperatorEntry("GeometryNodeToolSetSelection", pad=13, poll=is_tool_tree(context)),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_operations(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeBake", pad=32),
            OperatorEntry("GeometryNodeBoundBox", pad=16),
            OperatorEntry("GeometryNodeConvexHull", pad=19),
            OperatorEntry("GeometryNodeDeleteGeometry", pad=11),
            OperatorEntry("GeometryNodeDuplicateElements", pad=7),
            OperatorEntry("GeometryNodeMergeByDistance", pad=8),
            OperatorEntry("GeometryNodeSortElements", pad=16),
            OperatorEntry("GeometryNodeTransform", pad=4),
            Separator,
            OperatorEntry("GeometryNodeSeparateComponents", pad=1),
            OperatorEntry("GeometryNodeSeparateGeometry", pad=6),
            OperatorEntry("GeometryNodeSplitToInstances", pad=9),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeInputCurveHandlePositions", pad=0),
            OperatorEntry("GeometryNodeCurveLength", pad=17),
            OperatorEntry("GeometryNodeInputTangent", pad=15),
            OperatorEntry("GeometryNodeInputCurveTilt", pad=24),
            OperatorEntry("GeometryNodeCurveEndpointSelection", pad=8),
            OperatorEntry("GeometryNodeCurveHandleTypeSelection", pad=2),
            OperatorEntry("GeometryNodeInputSplineCyclic", pad=14),
            OperatorEntry("GeometryNodeSplineLength", pad=18),
            OperatorEntry("GeometryNodeSplineParameter", pad=12),
            OperatorEntry("GeometryNodeInputSplineResolution", pad=12),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve_sample(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeSampleCurve"),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve_write(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeSetCurveNormal", pad=6),
            OperatorEntry("GeometryNodeSetCurveRadius", pad=7),
            OperatorEntry("GeometryNodeSetCurveTilt", pad=13),
            OperatorEntry("GeometryNodeSetCurveHandlePositions", pad=1),
            OperatorEntry("GeometryNodeCurveSetHandles", pad=8),
            OperatorEntry("GeometryNodeSetSplineCyclic", pad=8),
            OperatorEntry("GeometryNodeSetSplineResolution", pad=1),
            OperatorEntry("GeometryNodeCurveSplineType", pad=10),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve_operations(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeCurvesToGreasePencil", pad=5),
            OperatorEntry("GeometryNodeCurveToMesh", pad=21),
            OperatorEntry("GeometryNodeCurveToPoints", pad=20),
            OperatorEntry("GeometryNodeDeformCurvesOnSurface", pad=0),
            OperatorEntry("GeometryNodeFillCurve", pad=30),
            OperatorEntry("GeometryNodeFilletCurve", pad=27),
            OperatorEntry("GeometryNodeGreasePencilToCurves", pad=5),
            OperatorEntry("GeometryNodeInterpolateCurves", pad=13),
            OperatorEntry("GeometryNodeResampleCurve", pad=18),
            OperatorEntry("GeometryNodeReverseCurve", pad=21),
            OperatorEntry("GeometryNodeSubdivideCurve", pad=18),
            OperatorEntry("GeometryNodeTrimCurve", pad=27),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve_primitives(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeCurveArc", pad=22),
            OperatorEntry("GeometryNodeCurvePrimitiveBezierSegment", pad=1),
            OperatorEntry("GeometryNodeCurvePrimitiveCircle", pad=7),
            OperatorEntry("GeometryNodeCurvePrimitiveLine", pad=10),
            OperatorEntry("GeometryNodeCurveSpiral", pad=19),
            OperatorEntry("GeometryNodeCurveQuadraticBezier", pad=0),
            OperatorEntry("GeometryNodeCurvePrimitiveQuadrilateral", pad=6),
            OperatorEntry("GeometryNodeCurveStar", pad=22),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_curve_topology(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeCurveOfPoint", pad=11),
            OperatorEntry("GeometryNodeOffsetPointInCurve", pad=0),
            OperatorEntry("GeometryNodePointsOfCurve", pad=9),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_grease_pencil(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeInputNamedLayerSelection"),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_grease_pencil_write(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeSetGreasePencilColor", pad=7),
            OperatorEntry("GeometryNodeSetGreasePencilDepth", pad=6),
            OperatorEntry("GeometryNodeSetGreasePencilSoftness", pad=1),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_grease_pencil_operations(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeGreasePencilToCurves", pad=0),
            OperatorEntry("GeometryNodeMergeLayers", pad=18),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_instances(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeInstanceOnPoints", pad=8),
            OperatorEntry("GeometryNodeInstancesToPoints", pad=7),
            OperatorEntry("GeometryNodeRealizeInstances", pad=10),
            OperatorEntry("GeometryNodeRotateInstances", pad=11),
            OperatorEntry("GeometryNodeScaleInstances", pad=13),
            OperatorEntry("GeometryNodeTranslateInstances", pad=7),
            OperatorEntry("GeometryNodeSetInstanceTransform", pad=0),
            Separator,
            OperatorEntry("GeometryNodeInputInstanceBounds", pad=11),
            OperatorEntry("GeometryNodeInstanceTransform", pad=6),
            OperatorEntry("GeometryNodeInputInstanceRotation", pad=10),
            OperatorEntry("GeometryNodeInputInstanceScale", pad=14),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeInputMeshEdgeAngle", pad=21),
            OperatorEntry("GeometryNodeInputMeshEdgeNeighbors", pad=13),
            OperatorEntry("GeometryNodeInputMeshEdgeVertices", pad=17),
            OperatorEntry("GeometryNodeEdgesToFaceGroups", pad=3),
            OperatorEntry("GeometryNodeInputMeshFaceArea", pad=23),
            Separator,
            OperatorEntry("GeometryNodeMeshFaceSetBoundaries", pad=0),
            OperatorEntry("GeometryNodeInputMeshFaceNeighbors", pad=13),
            OperatorEntry("GeometryNodeToolFaceSet", pad=25, poll=is_tool_tree(context)),
            OperatorEntry("GeometryNodeInputMeshFaceIsPlanar", pad=15),
            OperatorEntry("GeometryNodeInputShadeSmooth", pad=13),
            OperatorEntry("GeometryNodeInputEdgeSmooth", pad=12),
            Separator,
            OperatorEntry("GeometryNodeInputMeshIsland", pad=19),
            OperatorEntry("GeometryNodeInputShortestEdgePaths", pad=5),
            OperatorEntry("GeometryNodeInputMeshVertexNeighbors", pad=9),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_sample(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeSampleNearestSurface", pad=0),
            OperatorEntry("GeometryNodeSampleUVSurface", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_write(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeToolSetFaceSet", pad=10, poll=is_tool_tree(context)),
            OperatorEntry("GeometryNodeSetMeshNormal", pad=2),
            OperatorEntry("GeometryNodeSetShadeSmooth", pad=0),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_operations(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeDualMesh", pad=23),
            OperatorEntry("GeometryNodeEdgePathsToCurves", pad=4),
            OperatorEntry("GeometryNodeEdgePathsToSelection", pad=0),
            OperatorEntry("GeometryNodeExtrudeMesh", pad=17),
            OperatorEntry("GeometryNodeFlipFaces", pad=23),
            Separator,
            OperatorEntry("GeometryNodeMeshBoolean", pad=16),
            OperatorEntry("GeometryNodeMeshToCurve", pad=15),
            OperatorEntry("GeometryNodeMeshToDensityGrid", pad=7),
            OperatorEntry("GeometryNodeMeshToPoints", pad=15),
            OperatorEntry("GeometryNodeMeshToSDFGrid", pad=11),
            OperatorEntry("GeometryNodeMeshToVolume", pad=13),
            OperatorEntry("GeometryNodeScaleElements", pad=14),
            Separator,
            OperatorEntry("GeometryNodeSplitEdges", pad=21),
            OperatorEntry("GeometryNodeSubdivideMesh", pad=13),
            OperatorEntry("GeometryNodeSubdivisionSurface", pad=6),
            OperatorEntry("GeometryNodeTriangulate", pad=21),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_primitives(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeMeshCone", pad=12),
            OperatorEntry("GeometryNodeMeshCube", pad=12),
            OperatorEntry("GeometryNodeMeshCylinder", pad=7),
            OperatorEntry("GeometryNodeMeshGrid", pad=14),
            Separator,
            OperatorEntry("GeometryNodeMeshIcoSphere", pad=2),
            OperatorEntry("GeometryNodeMeshCircle", pad=1),
            OperatorEntry("GeometryNodeMeshLine", pad=4),
            OperatorEntry("GeometryNodeMeshUVSphere", pad=3),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_topology(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeCornersOfEdge", pad=10),
            OperatorEntry("GeometryNodeCornersOfFace", pad=10),
            OperatorEntry("GeometryNodeCornersOfVertex", pad=7),
            OperatorEntry("GeometryNodeEdgesOfCorner", pad=10),
            Separator,
            OperatorEntry("GeometryNodeEdgesOfVertex", pad=10),
            OperatorEntry("GeometryNodeFaceOfCorner", pad=12),
            OperatorEntry("GeometryNodeOffsetCornerInFace", pad=1),
            OperatorEntry("GeometryNodeVertexOfCorner", pad=9),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_mesh_uv(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeUVPackIslands", pad=8),
            OperatorEntry("GeometryNodeUVTangent", pad=14),
            OperatorEntry("GeometryNodeUVUnwrap", pad=16),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_point(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeDistributePointsInVolume", pad=1),
            OperatorEntry("GeometryNodeDistributePointsInGrid", pad=7),
            OperatorEntry("GeometryNodeDistributePointsOnFaces", pad=3),
            Separator,
            OperatorEntry("GeometryNodePoints", pad=37),
            OperatorEntry("GeometryNodePointsToCurves", pad=19),
            OperatorEntry("GeometryNodePointsToSDFGrid", pad=16),
            OperatorEntry("GeometryNodePointsToVertices", pad=17),
            OperatorEntry("GeometryNodePointsToVolume", pad=18),
            OperatorEntry("GeometryNodeSetPointRadius", pad=19),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_volume(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            #OperatorEntry("GeometryNodeVolumeCube", pad=5),
            #OperatorEntry("GeometryNodeVolumeToMesh", pad=0),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_volume_read(bpy.types.Panel, NodePanel):
    bl_label = "Read"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeGetNamedGrid", pad=10),
            OperatorEntry("GeometryNodeGridInfo", pad=21),
            OperatorEntry("GeometryNodeInputVoxelIndex", pad=15),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_volume_sample(bpy.types.Panel, NodePanel):
    bl_label = "Sample"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeGridAdvect", pad=15),
            OperatorEntry("GeometryNodeSampleGrid", pad=15),
            OperatorEntry("GeometryNodeSampleGridIndex", pad=5),
            OperatorEntry("GeometryNodeGridCurl", pad=22),
            OperatorEntry("GeometryNodeGridDivergence", pad=10),
            OperatorEntry("GeometryNodeGridGradient", pad=15),
            OperatorEntry("GeometryNodeGridLaplacian", pad=13),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_volume_write(bpy.types.Panel, NodePanel):
    bl_label = "Write"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeStoreNamedGrid", pad=17),
            OperatorEntry("GeometryNodeSetGridBackground", pad=12),
            OperatorEntry("GeometryNodeSetGridTransform", pad=15),
        )

        self.draw_entries(context, layout, entries)
class NODES_PT_toolshelf_gn_add_volume_operations(bpy.types.Panel, NodePanel):
    bl_label = "Operations"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeGridToMesh", pad=20),
            OperatorEntry("GeometryNodeSDFGridBoolean", pad=14),
            OperatorEntry("GeometryNodeSDFGridFillet", pad=16),
            OperatorEntry("GeometryNodeSDFGridLaplacian", pad=8),
            OperatorEntry("GeometryNodeSDFGridMean", pad=14),
            OperatorEntry("GeometryNodeSDFGridMeanCurvature", pad=0),
            OperatorEntry("GeometryNodeSDFGridMedian", pad=12),
            OperatorEntry("GeometryNodeSDFGridOffset", pad=12),
            OperatorEntry("GeometryNodeFieldToGrid", pad=18),
            OperatorEntry("GeometryNodeGridPrune", pad=17),
            OperatorEntry("GeometryNodeGridVoxelize", pad=18),
            OperatorEntry("GeometryNodeVolumeToMesh", pad=16),
        )

        self.draw_entries(context, layout, entries)
class NODES_PT_toolshelf_gn_add_volume_primitives(bpy.types.Panel, NodePanel):
    bl_label = "Primitives"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "NODES_PT_toolshelf_gn_add_volume"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        layout = self.layout

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeVolumeCube", pad=5),
        )

        self.draw_entries(context, layout, entries)

class NODES_PT_toolshelf_gn_add_simulation(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry(operator="node.add_simulation_zone", text="Simulation Zone", icon="TIME"),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_material(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeReplaceMaterial", pad=3),
            OperatorEntry("GeometryNodeInputMaterialIndex", pad=7),
            OperatorEntry("GeometryNodeMaterialSelection", pad=1),
            OperatorEntry("GeometryNodeSetMaterial", pad=11),
            OperatorEntry("GeometryNodeSetMaterialIndex", pad=0),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_texture(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeTexBrick", pad=13),
            OperatorEntry("ShaderNodeTexChecker", pad=7),
            OperatorEntry("ShaderNodeTexGabor", pad=11),
            OperatorEntry("ShaderNodeTexGradient", pad=7),
            OperatorEntry("GeometryNodeImageTexture", pad=10),
            OperatorEntry("ShaderNodeTexMagic", pad=11),
            OperatorEntry("ShaderNodeTexNoise", pad=12),
            OperatorEntry("ShaderNodeTexVoronoi", pad=8),
            OperatorEntry("ShaderNodeTexWave", pad=12),
            OperatorEntry("ShaderNodeTexWhiteNoise", pad=1),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry(operator="node.add_foreach_geometry_element_zone", pad=1, text="For Each Element", icon="FOR_EACH"),
            OperatorEntry("GeometryNodeIndexSwitch", pad=8),
            OperatorEntry("GeometryNodeMenuSwitch", pad=9),
            OperatorEntry("FunctionNodeRandomValue", pad=6),
            OperatorEntry(operator="node.add_repeat_zone", pad=9, text="Repeat Zone", icon="REPEAT"),
            OperatorEntry("GeometryNodeSwitch", pad=19),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_color(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeValToRGB", pad=6),
            OperatorEntry("ShaderNodeRGBCurve", pad=6),
            Separator,
            OperatorEntry("FunctionNodeCombineColor", pad=1),
            OperatorEntry("ShaderNodeMix", text="Mix Color", pad=10, settings={"data_type": "'RGBA'"}),
            OperatorEntry("FunctionNodeSeparateColor", pad=1),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_text(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("FunctionNodeFormatString", pad=9),
            OperatorEntry("GeometryNodeStringJoin", pad=12),
            OperatorEntry("FunctionNodeMatchString", pad=11),
            OperatorEntry("FunctionNodeReplaceString", pad=8),
            OperatorEntry("FunctionNodeSliceString", pad=13),
            OperatorEntry("FunctionNodeStringLength", pad=10),
            OperatorEntry("FunctionNodeFindInString", pad=10),
            OperatorEntry("GeometryNodeStringToCurves", pad=5),
            OperatorEntry("FunctionNodeStringToValue", pad=7),
            OperatorEntry("FunctionNodeValueToString", pad=7),
            OperatorEntry("FunctionNodeInputSpecialCharacters", pad=0),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_vector(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("ShaderNodeCombineXYZ", pad=4),
            OperatorEntry("ShaderNodeMapRange", pad=9, settings={"data_type": "'FLOAT_VECTOR'"}),
            OperatorEntry("ShaderNodeMix", text="Mix Vector", pad=9, settings={"data_type": "'VECTOR'"}),
            OperatorEntry("ShaderNodeSeparateXYZ", pad=4),
            Separator,
            OperatorEntry("ShaderNodeRadialTiling", pad=10),
            OperatorEntry("ShaderNodeVectorCurve", pad=3),
            OperatorEntry("ShaderNodeVectorMath", pad=7),
            OperatorEntry("ShaderNodeVectorRotate", pad=4),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_bundle(bpy.types.Panel, NodePanel):
    bl_label = "Bundle"
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("NodeCombineBundle", pad=10),
            OperatorEntry("NodeSeparateBundle", pad=10),
            OperatorEntry("NodeJoinBundle", pad=19),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_closure(bpy.types.Panel, NodePanel):
    bl_label = "Closure"
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry(operator="node.add_closure_zone", text="Closure", icon="NODE_CLOSURE", pad=24),
            #OperatorEntry("NodeClosureInput", pad=12),
            #OperatorEntry("NodeClosureOutput", pad=8),
            OperatorEntry("NodeEvaluateClosure", pad=8),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_field(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("GeometryNodeAccumulateField", pad=7),
            OperatorEntry("GeometryNodeFieldAtIndex", pad=7),
            OperatorEntry("GeometryNodeFieldOnDomain", pad=3),
            OperatorEntry("GeometryNodeFieldAverage", pad=13),
            OperatorEntry("GeometryNodeFieldMinAndMax", pad=9),
            OperatorEntry("GeometryNodeFieldVariance", pad=12),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_math(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("FunctionNodeBitMath", pad=14),
            OperatorEntry("FunctionNodeBooleanMath", pad=4),
            OperatorEntry("FunctionNodeIntegerMath", pad=5),
            OperatorEntry("ShaderNodeClamp", pad=17),
            OperatorEntry("FunctionNodeCompare", pad=12),
            OperatorEntry("ShaderNodeFloatCurve", pad=8),
            Separator,
            OperatorEntry("FunctionNodeFloatToInt", pad=1),
            OperatorEntry("FunctionNodeHashValue", pad=8),
            OperatorEntry("ShaderNodeMapRange", pad=9),
            OperatorEntry("ShaderNodeMath", pad=19),
            OperatorEntry("ShaderNodeMix", pad=22),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_matrix(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("FunctionNodeCombineMatrix", pad=8),
            OperatorEntry("FunctionNodeCombineTransform", pad=1),
            OperatorEntry("FunctionNodeMatrixDeterminant", pad=2),
            OperatorEntry("FunctionNodeInvertMatrix", pad=12),
            OperatorEntry("FunctionNodeMatrixMultiply", pad=6),
            OperatorEntry("FunctionNodeProjectPoint", pad=13),
            OperatorEntry("FunctionNodeSeparateMatrix", pad=8),
            OperatorEntry("FunctionNodeSeparateTransform", pad=0),
            OperatorEntry("FunctionNodeTransformDirection", pad=1),
            OperatorEntry("FunctionNodeTransformPoint", pad=8),
            OperatorEntry("FunctionNodeTransposeMatrix", pad=6),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_rotation(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("FunctionNodeAlignRotationToVector", pad=2),
            OperatorEntry("FunctionNodeAxesToRotation", pad=15),
            OperatorEntry("FunctionNodeAxisAngleToRotation", pad=5),
            OperatorEntry("FunctionNodeEulerToRotation", pad=15),
            OperatorEntry("FunctionNodeInvertRotation", pad=17),
            OperatorEntry("FunctionNodeRotateRotation", pad=17),
            OperatorEntry("FunctionNodeRotateVector", pad=19),
            OperatorEntry("FunctionNodeRotationToAxisAngle", pad=5),
            OperatorEntry("FunctionNodeRotationToEuler", pad=15),
            OperatorEntry("FunctionNodeRotationToQuaternion", pad=4),
            OperatorEntry("FunctionNodeQuaternionToRotation", pad=4),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_utilities_deprecated(bpy.types.Panel, NodePanel):
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

        # BFA - NOTE: The padding must be manually updated if a new node item is added to the panel.
        # There is currently no way to determine the correct padding length other than trial-and-error.
        # When adding a new node, test different padding amounts until the button text is left-aligned with the rest of the panel items.
        entries = (
            OperatorEntry("FunctionNodeAlignEulerToVector", pad=2),
            OperatorEntry("FunctionNodeRotateEuler", pad=17),
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
    NODES_PT_toolshelf_shader_add_displacement,
    NODES_PT_toolshelf_shader_add_color,
    NODES_PT_toolshelf_shader_add_texture,
    NODES_PT_toolshelf_shader_add_utilities,
    NODES_PT_toolshelf_shader_add_vector,
    NODES_PT_toolshelf_shader_add_math,
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
    NODES_PT_toolshelf_compositor_add_tracking,
    NODES_PT_toolshelf_compositor_add_texture,
    NODES_PT_toolshelf_compositor_add_transform,
    NODES_PT_toolshelf_compositor_add_utilities,
    NODES_PT_toolshelf_compositor_add_utilities_math,
    NODES_PT_toolshelf_compositor_add_utilities_vector,
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
    NODES_PT_toolshelf_gn_add_volume_read,
    NODES_PT_toolshelf_gn_add_volume_sample,
    NODES_PT_toolshelf_gn_add_volume_write,
    NODES_PT_toolshelf_gn_add_volume_operations,
    NODES_PT_toolshelf_gn_add_volume_primitives,

    NODES_PT_toolshelf_gn_add_simulation,
    NODES_PT_toolshelf_gn_add_material,
    NODES_PT_toolshelf_gn_add_texture,

    NODES_PT_toolshelf_gn_add_utilities,
    NODES_PT_toolshelf_gn_add_utilities_color,
    NODES_PT_toolshelf_gn_add_utilities_text,
    NODES_PT_toolshelf_gn_add_utilities_vector,
    NODES_PT_toolshelf_gn_add_utilities_bundle,
    NODES_PT_toolshelf_gn_add_utilities_closure,
    NODES_PT_toolshelf_gn_add_utilities_field,
    NODES_PT_toolshelf_gn_add_utilities_math,
    NODES_PT_toolshelf_gn_add_utilities_matrix,
    NODES_PT_toolshelf_gn_add_utilities_rotation,
    NODES_PT_toolshelf_gn_add_utilities_deprecated,
    #-----------------------
)

# BFA - Custom panels for the sidebar toolshelf (END)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

