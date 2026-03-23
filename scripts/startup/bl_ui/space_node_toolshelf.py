# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.app.translations import (
    pgettext_iface as iface_,
)

import dataclasses

from nodeitems_builtins import node_tree_group_type
from bl_ui.node_add_menu import draw_node_groups, add_empty_group


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


class NODES_PT_relations_group_operations(bpy.types.Panel, NodePanel):
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


class NODES_PT_toolshelf_shader_add_input_constant(bpy.types.Panel, NodePanel):
    bl_label = "Constant"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_input"

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
            OperatorEntry("CompositorNodeBokehImage", pad=13),
            OperatorEntry("NodeGroupInput", pad=14),
            OperatorEntry("CompositorNodeImage", pad=24),
            OperatorEntry("CompositorNodeImageInfo", pad=16),
            OperatorEntry("CompositorNodeImageCoordinates", pad=2),
            OperatorEntry("CompositorNodeMask", pad=27),
            OperatorEntry("CompositorNodeMovieClip", pad=18),
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
            OperatorEntry("FunctionNodeInputBool", pad=17),
            OperatorEntry("CompositorNodeRGB", pad=22),
            OperatorEntry("FunctionNodeInputInt", pad=19),
            OperatorEntry("FunctionNodeInputIntVector", pad=7),
            OperatorEntry("FunctionNodeInputMenu", pad=23),
            OperatorEntry("GeometryNodeInputObject", pad=22),
            OperatorEntry("CompositorNodeNormal", pad=20),
            OperatorEntry("ShaderNodeValue", pad=23),
            OperatorEntry("FunctionNodeInputVector", pad=21),
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
            OperatorEntry("GeometryNodeInputActiveCamera", pad=4),
            OperatorEntry("GeometryNodeCameraInfo", pad=7),
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
            OperatorEntry("NodeEnableOutput", pad=12),
            OperatorEntry("CompositorNodeViewer", pad=25),
            Separator,
            OperatorEntry("CompositorNodeOutputFile", pad=17),
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
            OperatorEntry("CompositorNodePremulKey", pad=15),
            OperatorEntry("CompositorNodeAlphaOver", pad=21),
            OperatorEntry("CompositorNodeSetAlpha", pad=23),
            Separator,
            OperatorEntry("CompositorNodeCombineColor", pad=13),
            OperatorEntry("CompositorNodeSeparateColor", pad=14),
            Separator,
            OperatorEntry("CompositorNodeZcombine", pad=12),
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Color"), pad=22, settings={"data_type": "'RGBA'"}),
            Separator,
            OperatorEntry("ShaderNodeBlackbody", pad=21),
            OperatorEntry("ShaderNodeValToRGB", pad=19),
            OperatorEntry("CompositorNodeConvertColorSpace", pad=4),
            OperatorEntry("CompositorNodeConvertToDisplay", pad=6),
            Separator,
            OperatorEntry("CompositorNodeInvert", pad=17),
            OperatorEntry("CompositorNodeRGBToBW", pad=19),
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
            OperatorEntry("CompositorNodeBrightContrast", pad=4),
            OperatorEntry("CompositorNodeColorBalance", pad=15),
            OperatorEntry("CompositorNodeColorCorrection", pad=10),
            OperatorEntry("CompositorNodeExposure", pad=23),
            OperatorEntry("ShaderNodeGamma", pad=26),
            OperatorEntry("CompositorNodeHueCorrect", pad=18),
            OperatorEntry("CompositorNodeHueSat", pad=1),
            OperatorEntry("CompositorNodeCurveRGB", pad=18),
            OperatorEntry("CompositorNodeTonemap", pad=22),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_compositor_add_creative(bpy.types.Panel, NodePanel):
    bl_label = "Creative"
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
            OperatorEntry("CompositorNodeKuwahara", pad=12),
            OperatorEntry("CompositorNodePixelate", pad=16),
            OperatorEntry("CompositorNodePosterize", pad=13),
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
            OperatorEntry("CompositorNodeAntiAliasing", pad=0),
            OperatorEntry("CompositorNodeConvolve", pad=7),
            OperatorEntry("CompositorNodeDenoise", pad=9),
            OperatorEntry("CompositorNodeDespeckle", pad=5),
            Separator,
            OperatorEntry("CompositorNodeDilateErode", pad=2),
            OperatorEntry("CompositorNodeMaskToSDF", pad=0),
            OperatorEntry("CompositorNodeInpaint", pad=10),
            Separator,
            OperatorEntry("CompositorNodeFilter", pad=13),
            OperatorEntry("CompositorNodeGlare", pad=13),
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
            OperatorEntry("CompositorNodeChannelMatte", pad=6),
            OperatorEntry("CompositorNodeChromaMatte", pad=7),
            OperatorEntry("CompositorNodeColorMatte", pad=11),
            OperatorEntry("CompositorNodeColorSpill", pad=9),
            OperatorEntry("CompositorNodeDiffMatte", pad=2),
            OperatorEntry("CompositorNodeDistanceMatte", pad=5),
            OperatorEntry("CompositorNodeKeying", pad=16),
            OperatorEntry("CompositorNodeKeyingScreen", pad=3),
            OperatorEntry("CompositorNodeLumaMatte", pad=2),
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
            OperatorEntry("CompositorNodeCryptomatteV2", pad=17),
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
            OperatorEntry("CompositorNodePlaneTrackDeform", pad=1),
            OperatorEntry("CompositorNodeStabilize", pad=14),
            OperatorEntry("CompositorNodeTrackPos", pad=11),
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
            OperatorEntry("ShaderNodeTexBrick", pad=14),
            OperatorEntry("ShaderNodeTexChecker", pad=9),
            OperatorEntry("ShaderNodeTexGabor", pad=12),
            OperatorEntry("ShaderNodeTexGradient", pad=8),
            OperatorEntry("ShaderNodeTexMagic", pad=12),
            OperatorEntry("ShaderNodeTexNoise", pad=13),
            OperatorEntry("ShaderNodeTexVoronoi", pad=8),
            OperatorEntry("ShaderNodeTexWave", pad=13),
            OperatorEntry("ShaderNodeTexWhiteNoise", pad=1),
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
            OperatorEntry("CompositorNodeLevels", pad=33),
            OperatorEntry("CompositorNodeNormalize", pad=26),
            Separator,
            OperatorEntry("NodeImplicitConversion", pad=8),
            OperatorEntry("CompositorNodeSplit", pad=35),
            OperatorEntry("CompositorNodeSwitch", pad=31),
            OperatorEntry("GeometryNodeIndexSwitch", pad=19),
            OperatorEntry("GeometryNodeMenuSwitch", pad=19),
            OperatorEntry("CompositorNodeSwitchView", pad=8, text="Switch Stereo View"),
            Separator,
            OperatorEntry("CompositorNodeRelativeToPixel", pad=13),
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


class NODES_PT_toolshelf_compositor_add_utilities_matrix(bpy.types.Panel, NodePanel):
    bl_label = "Matrix"
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
            OperatorEntry("FunctionNodeCombineMatrix", pad=8),
            OperatorEntry("FunctionNodeMatrixDeterminant", pad=14, text="Determinant"),
            OperatorEntry("FunctionNodeInvertMatrix", pad=13),
            OperatorEntry("FunctionNodeMatrixMultiply", pad=6),
            OperatorEntry("FunctionNodeProjectPoint", pad=13),
            OperatorEntry("FunctionNodeSeparateMatrix", pad=8),
            OperatorEntry("FunctionNodeTransformDirection", pad=1),
            OperatorEntry("FunctionNodeTransformPoint", pad=8),
            OperatorEntry("FunctionNodeTransposeMatrix", pad=6),
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
            OperatorEntry("ShaderNodeCombineXYZ", pad=16),
            OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=20, settings={"data_type": "'FLOAT_VECTOR'"}),
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), pad=20, settings={"data_type": "'VECTOR'"}),
            OperatorEntry("ShaderNodeSeparateXYZ", pad=16),
            Separator,
            OperatorEntry("ShaderNodeRadialTiling", pad=18),
            OperatorEntry("ShaderNodeVectorCurve", pad=15),
            OperatorEntry("ShaderNodeVectorMath", pad=18),
            OperatorEntry("ShaderNodeVectorRotate", pad=15),
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
            OperatorEntry("FunctionNodeInputBool",pad=9),
            OperatorEntry("GeometryNodeInputCollection",pad=5),
            OperatorEntry("FunctionNodeInputColor",pad=13),
            OperatorEntry("GeometryNodeInputFont",pad=13),
            OperatorEntry("GeometryNodeInputImage",pad=11),
            OperatorEntry("FunctionNodeInputInt",pad=10),
            OperatorEntry("GeometryNodeInputMaterial",pad=9),
            OperatorEntry("FunctionNodeInputMenu",pad=13),
            OperatorEntry("GeometryNodeInputObject",pad=12),
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
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'GeometryNodeTree') and (not is_tool_tree(context))

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
            OperatorEntry("GeometryNodeTool3DCursor", pad=22, poll=is_tool),
            OperatorEntry("GeometryNodeInputActiveCamera", pad=15),
            OperatorEntry("GeometryNodeBoneInfo", pad=22),
            OperatorEntry("GeometryNodeCameraInfo", pad=18),
            OperatorEntry("GeometryNodeCollectionInfo", pad=14),
            OperatorEntry("GeometryNodeImageInfo", pad=21),
            OperatorEntry("GeometryNodeIsViewport", pad=20),
            OperatorEntry("GeometryNodeInputNamedLayerSelection", pad=1),
            OperatorEntry("GeometryNodeToolMousePosition", pad=14, poll=is_tool),
            OperatorEntry("GeometryNodeObjectInfo", pad=21),
            OperatorEntry("GeometryNodeInputSceneTime", pad=20),
            OperatorEntry("GeometryNodeSelfObject", pad=22),
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
            OperatorEntry("GeometryNodeViewer", pad=24),
            OperatorEntry("GeometryNodeWarning", pad=22),
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
            OperatorEntry("GeometryNodeInputID", pad=25),
            OperatorEntry("GeometryNodeInputIndex", pad=19),
            OperatorEntry("GeometryNodeInputNamedAttribute", pad=1),
            OperatorEntry("GeometryNodeInputNormal", pad=18),
            OperatorEntry("GeometryNodeInputPosition", pad=16),
            OperatorEntry("GeometryNodeInputRadius", pad=18),
            OperatorEntry("GeometryNodeToolSelection", pad=14, poll=is_tool),
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
            OperatorEntry("GeometryNodeSetGeometryName", pad=2),
            OperatorEntry("GeometryNodeSetID", pad=25),
            OperatorEntry("GeometryNodeSetPosition", pad=15),
            OperatorEntry("GeometryNodeToolSetSelection", pad=13, poll=is_tool_tree(context)),
        )

        self.draw_entries(context, layout, entries)


class NODES_PT_toolshelf_gn_add_geometry_material(bpy.types.Panel, NodePanel):
    bl_label = "Material"
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
            OperatorEntry("GeometryNodeReplaceMaterial", pad=3),
            OperatorEntry("GeometryNodeInputMaterialIndex", pad=7),
            OperatorEntry("GeometryNodeMaterialSelection", pad=1),
            OperatorEntry("GeometryNodeSetMaterial", pad=11),
            OperatorEntry("GeometryNodeSetMaterialIndex", pad=0),
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
            OperatorEntry("GeometryNodeSetCurveNormal", pad=7),
            OperatorEntry("GeometryNodeSetCurveRadius", pad=7),
            OperatorEntry("GeometryNodeSetCurveTilt", pad=13),
            OperatorEntry("GeometryNodeSetCurveHandlePositions", pad=0),
            OperatorEntry("GeometryNodeCurveSetHandles", pad=8),
            OperatorEntry("GeometryNodeSetNURBSOrder", pad=8),
            OperatorEntry("GeometryNodeSetNURBSWeight", pad=5),
            OperatorEntry("GeometryNodeSetSplineCyclic", pad=8),
            OperatorEntry("GeometryNodeSetSplineResolution", pad=0),
            OperatorEntry("GeometryNodeCurveSplineType", pad=11),
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
            OperatorEntry("GeometryNodeCurveToMesh", pad=22),
            OperatorEntry("GeometryNodeCurveToPoints", pad=20),
            OperatorEntry("GeometryNodeCurvesToGreasePencil", pad=6),
            OperatorEntry("GeometryNodeDeformCurvesOnSurface", pad=1),
            OperatorEntry("GeometryNodeFillCurve", pad=30),
            OperatorEntry("GeometryNodeFilletCurve", pad=27),
            OperatorEntry("GeometryNodeInterpolateCurves", pad=13),
            OperatorEntry("GeometryNodeResampleCurve", pad=18),
            OperatorEntry("GeometryNodeReverseCurve", pad=21),
            OperatorEntry("GeometryNodeSubdivideCurve", pad=17),
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
            OperatorEntry("GeometryNodeCurveOfPoint", pad=12),
            OperatorEntry("GeometryNodeOffsetPointInCurve", pad=1),
            OperatorEntry("GeometryNodePointsOfCurve", pad=10),
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
            OperatorEntry("GeometryNodeInstanceOnPoints", pad=9),
            OperatorEntry("GeometryNodeInstancesToPoints", pad=8),
            Separator,
            OperatorEntry("GeometryNodeRealizeInstances", pad=12),
            OperatorEntry("GeometryNodeRotateInstances", pad=13),
            OperatorEntry("GeometryNodeSetInstanceTransform", pad=1),
            OperatorEntry("GeometryNodeScaleInstances", pad=15),
            OperatorEntry("GeometryNodeTranslateInstances", pad=8),
            Separator,
            OperatorEntry("GeometryNodeInputInstanceBounds", pad=12),
            OperatorEntry("GeometryNodeInstanceTransform", pad=7),
            OperatorEntry("GeometryNodeInputInstanceRotation", pad=11),
            OperatorEntry("GeometryNodeInputInstanceScale", pad=16),
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
            OperatorEntry("GeometryNodeInputMeshFaceArea", pad=24),
            Separator,
            OperatorEntry("GeometryNodeMeshFaceSetBoundaries", pad=0),
            OperatorEntry("GeometryNodeInputMeshFaceNeighbors", pad=14),
            OperatorEntry("GeometryNodeToolFaceSet", pad=26, poll=is_tool_tree(context)),
            OperatorEntry("GeometryNodeInputMeshFaceIsPlanar", pad=17),
            OperatorEntry("GeometryNodeInputShadeSmooth", pad=14),
            OperatorEntry("GeometryNodeInputEdgeSmooth", pad=14),
            Separator,
            OperatorEntry("GeometryNodeInputMeshIsland", pad=21),
            OperatorEntry("GeometryNodeInputShortestEdgePaths", pad=7),
            OperatorEntry("GeometryNodeInputMeshVertexNeighbors", pad=12),
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
            OperatorEntry("GeometryNodeDualMesh", pad=24),
            OperatorEntry("GeometryNodeEdgePathsToCurves", pad=4),
            OperatorEntry("GeometryNodeEdgePathsToSelection", pad=0),
            OperatorEntry("GeometryNodeExtrudeMesh", pad=17),
            OperatorEntry("GeometryNodeFlipFaces", pad=23),
            Separator,
            OperatorEntry("GeometryNodeMeshBoolean", pad=16),
            OperatorEntry("GeometryNodeMeshToCurve", pad=15),
            OperatorEntry("GeometryNodeMeshToDensityGrid", pad=4),
            OperatorEntry("GeometryNodeMeshToPoints", pad=15),
            OperatorEntry("GeometryNodeMeshToSDFGrid", pad=10),
            OperatorEntry("GeometryNodeMeshToVolume", pad=12),
            Separator,
            OperatorEntry("GeometryNodeScaleElements", pad=14),
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
            OperatorEntry("GeometryNodeMeshCone", pad=28),
            OperatorEntry("GeometryNodeMeshCube", pad=28),
            OperatorEntry("GeometryNodeMeshCylinder", pad=23),
            OperatorEntry("GeometryNodeMeshGrid", pad=30),
            Separator,
            OperatorEntry("GeometryNodeMeshIcoSphere", pad=18),
            OperatorEntry("GeometryNodeMeshCircle", pad=17),
            OperatorEntry("GeometryNodeMeshLine", pad=19),
            OperatorEntry("GeometryNodeMeshUVSphere", pad=19),
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
            Separator,
            OperatorEntry("GeometryNodeEdgesOfCorner", pad=10),
            OperatorEntry("GeometryNodeEdgesOfVertex", pad=10),
            Separator,
            OperatorEntry("GeometryNodeFaceOfCorner", pad=12),
            OperatorEntry("GeometryNodeOffsetCornerInFace", pad=1),
            OperatorEntry("GeometryNodeVertexOfCorner", pad=9),
        )


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
            OperatorEntry("GeometryNodeUVTangent", pad=16),
            OperatorEntry("GeometryNodeUVUnwrap", pad=17),
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
            OperatorEntry("GeometryNodePointsToVolume", pad=17),
            Separator,
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
        entries = ()

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
            OperatorEntry("GeometryNodeSampleGrid", pad=18),
            OperatorEntry("GeometryNodeSampleGridIndex", pad=6),
            Separator,
            OperatorEntry("GeometryNodeGridAdvect", pad=18),
            OperatorEntry("GeometryNodeGridCurl", pad=23),
            OperatorEntry("GeometryNodeGridDivergence", pad=11),
            OperatorEntry("GeometryNodeGridGradient", pad=16),
            OperatorEntry("GeometryNodeGridLaplacian", pad=14),
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
            OperatorEntry("GeometryNodeSetGridBackground", pad=12),
            OperatorEntry("GeometryNodeSetGridTransform", pad=15),
            OperatorEntry("GeometryNodeStoreNamedGrid", pad=17),
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
            OperatorEntry("GeometryNodeGridToMesh", pad=23),
            OperatorEntry("GeometryNodeGridToPoints", pad=22),
            OperatorEntry("GeometryNodeVolumeToMesh", pad=17),
            Separator,
            OperatorEntry("GeometryNodeSDFGridBoolean", pad=15),
            OperatorEntry("GeometryNodeSDFGridFillet", pad=20),
            OperatorEntry("GeometryNodeSDFGridLaplacian", pad=12),
            OperatorEntry("GeometryNodeSDFGridMean", pad=19),
            OperatorEntry("GeometryNodeSDFGridMeanCurvature", pad=0),
            OperatorEntry("GeometryNodeSDFGridMedian", pad=16),
            OperatorEntry("GeometryNodeSDFGridOffset", pad=18),
            Separator,
            OperatorEntry("GeometryNodeFieldToGrid", pad=23),
            OperatorEntry("GeometryNodeGridClip", pad=29),
            OperatorEntry("GeometryNodeGridDilateAndErode", pad=11),
            OperatorEntry("GeometryNodeGridMean", pad=26),
            OperatorEntry("GeometryNodeGridMedian", pad=23),
            OperatorEntry("GeometryNodeGridPrune", pad=25),
            OperatorEntry("GeometryNodeGridVoxelize", pad=21),
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
            OperatorEntry("GeometryNodeCubeGridTopology", pad=5),
            OperatorEntry("GeometryNodeVolumeCube", pad=17),
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


class NODES_PT_toolshelf_gn_add_color(bpy.types.Panel, NodePanel):
    bl_label = "Color"
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
            OperatorEntry("ShaderNodeBlackbody", pad=19),
            OperatorEntry("ShaderNodeValToRGB", pad=17),
            OperatorEntry("ShaderNodeGamma", pad=24),
            OperatorEntry("ShaderNodeMix", text="Mix Color", pad=21, settings={"data_type": "'RGBA'"}),
            OperatorEntry("ShaderNodeRGBCurve", pad=18),
            Separator,
            OperatorEntry("FunctionNodeCombineColor", pad=12),
            OperatorEntry("FunctionNodeSeparateColor", pad=12),
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
            OperatorEntry("ShaderNodeTexBrick", pad=15),
            OperatorEntry("ShaderNodeTexChecker", pad=9),
            OperatorEntry("ShaderNodeTexGabor", pad=13),
            OperatorEntry("ShaderNodeTexGradient", pad=8),
            OperatorEntry("GeometryNodeImageTexture", pad=11),
            OperatorEntry("ShaderNodeTexMagic", pad=12),
            OperatorEntry("ShaderNodeTexNoise", pad=13),
            OperatorEntry("ShaderNodeTexVoronoi", pad=8),
            OperatorEntry("ShaderNodeTexWave", pad=12),
            OperatorEntry("ShaderNodeTexWhiteNoise", pad=0),
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
            OperatorEntry("NodeImplicitConversion", pad=6),
            OperatorEntry(operator="node.add_foreach_geometry_element_zone", pad=9, text="For Each Element", icon="FOR_EACH"),
            OperatorEntry("GeometryNodeIndexSwitch", pad=17),
            OperatorEntry("GeometryNodeMenuSwitch", pad=17),
            OperatorEntry("FunctionNodeRandomValue", pad=14),
            OperatorEntry(operator="node.add_repeat_zone", pad=17, text="Repeat Zone", icon="REPEAT"),
            OperatorEntry("GeometryNodeSwitch", pad=27),
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
            OperatorEntry("FunctionNodeFormatString", pad=11),
            OperatorEntry("GeometryNodeStringJoin", pad=14),
            OperatorEntry("FunctionNodeMatchString", pad=13),
            OperatorEntry("FunctionNodeReplaceString", pad=10),
            OperatorEntry("FunctionNodeSliceString", pad=15),
            OperatorEntry("FunctionNodeTrimString", pad=15),
            Separator,
            OperatorEntry("FunctionNodeFindInString", pad=10),
            OperatorEntry("FunctionNodeStringLength", pad=10),
            OperatorEntry("GeometryNodeStringToCurves", pad=6),
            OperatorEntry("FunctionNodeStringToValue", pad=8),
            OperatorEntry("FunctionNodeValueToString", pad=7),
            Separator,
            OperatorEntry("FunctionNodeInputSpecialCharacters", pad=1),
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
            OperatorEntry("ShaderNodeCombineXYZ", pad=16),
            OperatorEntry("ShaderNodeMapRange", text=iface_("Map Range"), pad=20, settings={"data_type": "'FLOAT_VECTOR'"}),
            OperatorEntry("ShaderNodeMix", text=iface_("Mix Vector"), pad=20, settings={"data_type": "'VECTOR'"}),
            OperatorEntry("ShaderNodeSeparateXYZ", pad=16),
            Separator,
            OperatorEntry("ShaderNodeRadialTiling", pad=18),
            OperatorEntry("ShaderNodeVectorCurve", pad=14),
            OperatorEntry("ShaderNodeVectorMath", pad=17),
            OperatorEntry("ShaderNodeVectorRotate", pad=15),
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
            OperatorEntry("NodeCombineBundle", pad=14),
            OperatorEntry("NodeSeparateBundle", pad=15),
            OperatorEntry("NodeGetBundleItem", pad=14),
            OperatorEntry("NodeStoreBundleItem", pad=11),
            OperatorEntry("NodeJoinBundle", pad=22),
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
            OperatorEntry("FunctionNodeMatrixDeterminant", pad=14, text="Determinant"),
            OperatorEntry("FunctionNodeInvertMatrix", pad=13),
            OperatorEntry("FunctionNodeMatrixMultiply", pad=6),
            OperatorEntry("FunctionNodeMatrixSVD", pad=16),
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
            OperatorEntry("FunctionNodeInvertRotation", pad=18),
            OperatorEntry("ShaderNodeMix", text="Mix Rotation", pad=22, settings={"data_type": "'ROTATION'"}),
            OperatorEntry("FunctionNodeRotateRotation", pad=17),
            OperatorEntry("FunctionNodeRotateVector", pad=20),
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
    NODES_PT_toolshelf_shader_add_input_constant,
    NODES_PT_toolshelf_shader_add_output,
    NODES_PT_toolshelf_shader_add_shader,
    NODES_PT_toolshelf_shader_add_displacement,
    NODES_PT_toolshelf_shader_add_color,
    NODES_PT_toolshelf_shader_add_texture,
    NODES_PT_toolshelf_shader_add_utilities,
    NODES_PT_toolshelf_shader_add_math,
    NODES_PT_toolshelf_shader_add_vector,
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

