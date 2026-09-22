# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
from bpy.app.translations import (
    pgettext_iface as iface_,
)

import functools

from nodeitems_builtins import node_tree_group_type
from bl_ui.node_add_menu import AddNodeMenu
from bl_ui import (
    node_add_menu,
    node_add_menu_compositor,
    node_add_menu_geometry,
    node_add_menu_shader,
    node_add_menu_texture,
)



def generate_panel(name, base, template, pathing_dict=None):
    if pathing_dict is None:
        pathing_dict = {}

    attrs = {
        "bl_label": base.bl_label, 
        "layout_base": base, 
        "pathing_dict": pathing_dict
    }

    if hasattr(base, "menu_path"):
        attrs["menu_path"] = base.menu_path

        path = "/".join(base.menu_path.split("/")[:-1])
        attrs["bl_parent_id"] = pathing_dict[path]

    if "poll" in base.__dict__:
        attrs["poll"] = base.poll

    return type(name, (AddNodePanel, template), attrs)


def generate_panels(menus, template):
    pathing_dict = {}
    pathing_dict = generate_pathing_dict(pathing_dict, menus)

    menus = tuple(
        generate_panel(bl_idname, layout_base, template, pathing_dict)
        for bl_idname, layout_base in menus.items()
    )

    return menus


def generate_pathing_dict(pathing_dict, menus):
    for name, menu in menus.items():
        if hasattr(menu, "menu_path"):
            menu_path = menu.menu_path
        else:
            menu_path = menu.bl_label

        pathing_dict[menu_path] = name

    return pathing_dict


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


def use_icon_buttons(context=None):
    if context is None:
        context = bpy.context

    return context.preferences.addons["bforartists_toolbar_settings"].preferences.Node_text_or_icon


def filter_common(context=None):
    if context is None:
        context = bpy.context

    return context.preferences.addons["bforartists_toolbar_settings"].preferences.Node_shader_add_common


class LayoutWrapper:
    def __init__(self, parent):
        self.owner = parent

    def __getattr__(self, name):
        if name in {"separator"}:
            return getattr(self.owner, name)
        else:
            return getattr(self.owner.layout_container, name)

# 
class PanelWrapper:
    def __init__(self, actual_class, context):
        if use_icon_buttons(context):
            self.layout_container = self.add_grid_flow(actual_class.layout)
        else:
            self.layout_container = self.add_column(actual_class.layout)
        
        self.base_layout = actual_class.layout
        self.actual_class = actual_class

    @staticmethod
    def add_grid_flow(layout):
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=True)
        flow.scale_x = 1.5
        flow.scale_y = 1.5
        return flow

    @staticmethod
    def add_column(layout):
        col = layout.column(align=True)
        col.scale_y = 1.5
        return col

    def separator(self, factor=None):
        if use_icon_buttons():
            self.layout_container = self.add_grid_flow(self.base_layout)
        else:
            self.layout_container.separator(factor=2/3)
    
    @property
    def layout(self):
        return LayoutWrapper(parent=self)
        
    def __getattr__(self, name):
        return getattr(self.actual_class, name)


class AddNodePanel(bpy.types.Panel):
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add"

    menu_path = None

    @staticmethod
    def operator_label(label):
        return label if not use_icon_buttons() else ""

    @classmethod
    def node_operator(cls, layout, node_type, *_, label=None, **kwargs):
        return AddNodeMenu.node_operator(layout, node_type, label=cls.operator_label(label), **kwargs)

    @classmethod
    def node_operator_ignore_extra_entries(cls, context, layout, node_type, *args, label=None, **kwargs):
        return AddNodeMenu.node_operator(layout, node_type, label=cls.operator_label(label), **kwargs)

    node_operator_with_searchable_enum = node_operator_ignore_extra_entries
    node_operator_with_outputs = node_operator_ignore_extra_entries
    node_operator_with_searchable_enum_socket = node_operator_ignore_extra_entries

    @classmethod
    def do_nothing(cls, *args, **kwargs):
        return

    draw_assets_for_catalog = do_nothing
    draw_menu = do_nothing

    def __getattr__(self, name):
        func = getattr(AddNodeMenu, name)

        if name not in {"new_empty_group"}:
            return functools.partial(func, icon_only=use_icon_buttons())
       
        return func

    @property
    def draw_layout(self):
        if hasattr(self, "draw_common") and filter_common():
            return self.draw_common

        return self.layout_base.draw

    def draw(self, context):
        self.draw_layout(PanelWrapper(self, context), context)


def is_shader_type(context, valid_types):
    if not isinstance(valid_types, set):
        valid_types = {valid_types,}

    try:
        return context.space_data.shader_type in valid_types
    except AttributeError:
        return False


def is_object_type(context, valid_types):
    if not isinstance(valid_types, set):
        valid_types = {valid_types,}

    try:
        owner = context.space_data.id_from
        if owner is None:
            return True

        return owner.type in valid_types
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
    bl_category = "Relations"

    @classmethod
    def poll(self, context):
        tree = context.space_data.edit_tree 
        return tree in context.blend_data.node_groups.values()

    # NOTE - Needs to be a staticmethod since the class instance is supplied explicitly
    @staticmethod
    def draw_layout(self, context):
        layout = self.layout
        self.node_operator(layout, "NodeGroupInput")
        self.node_operator(layout, "NodeGroupOutput")


class NODES_PT_relations_nodegroups(AddNodePanel):
    bl_label = "Nodegroups"
    bl_category = "Relations"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type in node_tree_group_type)

    # NOTE - Needs to be a staticmethod since the class instance is supplied explicitly
    @staticmethod 
    def draw_layout(self, context):
        layout = self.layout
        self.new_empty_group(layout)
        self.draw_group_menu(context, layout)


class NODES_PT_relations_layout(AddNodePanel):
    bl_label = "Layout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Relations"
    layout_base = node_add_menu.NODE_MT_layout_base


class NODES_PT_toolshelf_shader_add_input(AddNodePanel, ShaderNodesPanel):
    bl_label = "Input"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_input_base

    @staticmethod
    def draw_common(self, context):
        layout = self.layout

        is_object = is_shader_type(context, 'OBJECT')
        is_light = is_object_type(context, 'LIGHT')

        self.node_operator(layout, "ShaderNodeAttribute")
        self.node_operator(layout, "ShaderNodeFresnel", poll=is_object and not is_light)
        self.node_operator(layout, "ShaderNodeNewGeometry")
        self.node_operator(layout, "ShaderNodeTexCoord")


class NODES_PT_toolshelf_shader_add_input_constant(AddNodePanel, ShaderNodesPanel):
    bl_label = "Constant"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_input"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_input_constant_base

    @staticmethod
    def draw_common(self, _context):
        layout = self.layout

        self.node_operator(layout, "ShaderNodeRGB")
        self.node_operator(layout, "FunctionNodeInputInt")
        self.node_operator(layout, "ShaderNodeValue")
        self.node_operator(layout, "FunctionNodeInputVector")


class NODES_PT_toolshelf_shader_add_output(AddNodePanel, ShaderNodesPanel):
    bl_label = "Output"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_output_base

    @staticmethod
    def draw_common(self, context):
        layout = self.layout

        self.node_operator(layout, "ShaderNodeOutputLineStyle", poll=is_shader_type(context, 'LINESTYLE'))
        self.node_operator(layout, "ShaderNodeOutputMaterial", poll=is_shader_type(context, 'OBJECT'))
        self.node_operator(layout, "ShaderNodeOutputWorld", poll=is_shader_type(context, 'WORLD'))


class NODES_PT_toolshelf_shader_add_shader(AddNodePanel, ShaderNodesPanel):
    bl_label = "Shader"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_shader_base

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and context.space_data.shader_type in ('OBJECT', 'WORLD'))

    @staticmethod
    def draw_common(self, context):
        layout = self.layout

        is_object = is_shader_type(context, 'OBJECT')
        is_eevee = is_engine(context, 'BLENDER_EEVEE')

        self.node_operator(layout, "ShaderNodeAddShader")
        self.node_operator(layout, "ShaderNodeMixShader")
        layout.separator()
        self.node_operator(layout, "ShaderNodeBackground", poll=is_shader_type(context, 'WORLD'))
        self.node_operator(layout, "ShaderNodeEmission")
        self.node_operator(layout, "ShaderNodeBsdfPrincipled", poll=is_object)
        self.node_operator(layout, "ShaderNodeBsdfHairPrincipled", poll=is_object and not is_eevee)
        self.node_operator(layout, "ShaderNodeBsdfToon", poll=is_object and not is_eevee)
        layout.separator()
        self.node_operator(layout, "ShaderNodeVolumePrincipled")
        self.node_operator(layout, "ShaderNodeVolumeAbsorption")
        self.node_operator(layout, "ShaderNodeVolumeScatter")


class NODES_PT_toolshelf_shader_add_displacement(AddNodePanel, ShaderNodesPanel):
    bl_label = "Displacement"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_displacement_base


class NODES_PT_toolshelf_shader_add_color(AddNodePanel, ShaderNodesPanel):
    bl_label = "Color"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_color_base
    
    @staticmethod
    def draw_common(self, context):
        layout = self.layout

        self.node_operator(layout, "ShaderNodeBrightContrast")
        self.node_operator(layout, "ShaderNodeValToRGB")
        self.node_operator(layout, "ShaderNodeGamma")
        self.node_operator(layout, "ShaderNodeHueSaturation")
        self.node_operator(layout, "ShaderNodeInvert")
        self.color_mix_node(context, layout)
        self.node_operator(layout, "ShaderNodeRGBCurve")
        layout.separator()
        self.node_operator(layout, "ShaderNodeCombineColor")
        self.node_operator(layout, "ShaderNodeSeparateColor")
        layout.separator()
        self.node_operator(layout, "ShaderNodeRGBToBW")
        self.node_operator(layout, "ShaderNodeShaderToRGB", poll=is_engine(context, 'BLENDER_EEVEE'))


class NODES_PT_toolshelf_shader_add_texture(AddNodePanel, ShaderNodesPanel):
    bl_label = "Texture"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_texture_base
    
    @staticmethod
    def draw_common(self, _context):
        layout = self.layout

        self.node_operator(layout, "ShaderNodeTexEnvironment")
        self.node_operator(layout, "ShaderNodeTexImage")
        self.node_operator(layout, "ShaderNodeTexNoise")
        self.node_operator(layout, "ShaderNodeTexSky")
        self.node_operator(layout, "ShaderNodeTexVoronoi")


class NODES_PT_toolshelf_shader_add_utilities(AddNodePanel, ShaderNodesPanel):
    bl_label = "Utilities"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_utilities_base
    
    @staticmethod
    def draw_common(self, _context):
        layout = self.layout

        self.repeat_zone(layout, label="Repeat")
        self.node_operator(layout, "NodeCombineBundle")
        self.node_operator(layout, "NodeJoinBundle")
        self.node_operator(layout, "NodeSeparateBundle")
        layout.separator()
        self.node_operator(layout, "GeometryNodeIndexSwitch")
        self.node_operator(layout, "GeometryNodeMenuSwitch")
        self.node_operator(layout, "GeometryNodeSwitch")


class NODES_PT_toolshelf_shader_add_math(AddNodePanel, ShaderNodesPanel):
    bl_label = "Math"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_utilities"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_math_base


class NODES_PT_toolshelf_shader_add_vector(AddNodePanel, ShaderNodesPanel):
    bl_label = "Vector"
    bl_parent_id = "NODES_PT_toolshelf_shader_add_utilities"
    layout_base = node_add_menu_shader.NODE_MT_shader_node_vector_base
    
    @staticmethod
    def draw_common(self, _context):
        layout = self.layout

        self.node_operator(layout, "ShaderNodeCombineXYZ")
        props = self.node_operator(layout, "ShaderNodeMapRange")
        ops = props.settings.add()
        ops.name = "data_type"
        ops.value = "'FLOAT_VECTOR'"
        props = self.node_operator(layout, "ShaderNodeMix", label=iface_("Mix Vector"))
        ops = props.settings.add()
        ops.name = "data_type"
        ops.value = "'VECTOR'"
        self.node_operator(layout, "ShaderNodeSeparateXYZ")
        layout.separator()
        self.node_operator(layout, "ShaderNodeMapping")
        self.node_operator(layout, "ShaderNodeNormal")
        self.node_operator(layout, "ShaderNodeRadialTiling")
        self.node_operator(layout, "ShaderNodeVectorMath")


compositor_nodes_panels = {
    "NODES_PT_toolshelf_compositor_add_input" : node_add_menu_compositor.NODE_MT_compositor_node_input_base,
    "NODES_PT_toolshelf_compositor_add_input_constant" : node_add_menu_compositor.NODE_MT_compositor_node_input_constant_base,
    "NODES_PT_toolshelf_compositor_add_input_scene" : node_add_menu_compositor.NODE_MT_compositor_node_input_scene_base,
    "NODES_PT_toolshelf_compositor_add_output" : node_add_menu_compositor.NODE_MT_compositor_node_output_base,
    "NODES_PT_toolshelf_compositor_add_color" : node_add_menu_compositor.NODE_MT_compositor_node_color_base,
    "NODES_PT_toolshelf_compositor_add_color_adjust" : node_add_menu_compositor.NODE_MT_compositor_node_color_adjust_base,
    "NODES_PT_toolshelf_compositor_add_creative" : node_add_menu_compositor.NODE_MT_compositor_node_creative_base,
    "NODES_PT_toolshelf_compositor_add_filter" : node_add_menu_compositor.NODE_MT_compositor_node_filter_base,
    "NODES_PT_toolshelf_compositor_add_filter_blur" : node_add_menu_compositor.NODE_MT_compositor_node_filter_blur_base,
    "NODES_PT_toolshelf_compositor_add_keying" : node_add_menu_compositor.NODE_MT_compositor_node_keying_base,
    "NODES_PT_toolshelf_compositor_add_mask" : node_add_menu_compositor.NODE_MT_compositor_node_mask_base,
    "NODES_PT_toolshelf_compositor_add_tracking" : node_add_menu_compositor.NODE_MT_compositor_node_tracking_base,
    "NODES_PT_toolshelf_compositor_add_texture" : node_add_menu_compositor.NODE_MT_compositor_node_texture_base,
    "NODES_PT_toolshelf_compositor_add_transform" : node_add_menu_compositor.NODE_MT_compositor_node_transform_base,
    "NODES_PT_toolshelf_compositor_add_utilities" : node_add_menu_compositor.NODE_MT_compositor_node_utilities_base,
    "NODES_PT_toolshelf_compositor_add_utilities_math" : node_add_menu_compositor.NODE_MT_compositor_node_math_base,
    "NODES_PT_toolshelf_compositor_add_utilities_matrix" : node_add_menu_compositor.NODE_MT_compositor_utilities_matrix_base,
    "NODES_PT_toolshelf_compositor_add_utilities_rotation" : node_add_menu_compositor.NODE_MT_compositor_node_rotation_base,
    "NODES_PT_toolshelf_compositor_add_utilities_vector" : node_add_menu_compositor.NODE_MT_compositor_node_vector_base,
    "NODES_PT_toolshelf_compositor_add_utilities_text" : node_add_menu_compositor.NODE_MT_compositor_node_text_base,
}


texture_nodes_panels = {
    "NODES_PT_toolshelf_texture_add_input" : node_add_menu_texture.NODE_MT_texture_node_input_base,
    "NODES_PT_toolshelf_texture_add_output" : node_add_menu_texture.NODE_MT_texture_node_output_base,
    "NODES_PT_toolshelf_texture_add_color" : node_add_menu_texture.NODE_MT_texture_node_color_base,
    "NODES_PT_toolshelf_texture_add_converter" : node_add_menu_texture.NODE_MT_texture_node_converter_base,
    "NODES_PT_toolshelf_texture_add_distort" : node_add_menu_texture.NODE_MT_texture_node_distort_base,
    "NODES_PT_toolshelf_texture_add_pattern" : node_add_menu_texture.NODE_MT_texture_node_pattern_base,
    "NODES_PT_toolshelf_texture_add_texture" : node_add_menu_texture.NODE_MT_texture_node_texture_base,
}


geometry_nodes_panels = {
    "NODES_PT_toolshelf_gn_add_input" : node_add_menu_geometry.NODE_MT_gn_input_base,
    "NODES_PT_toolshelf_gn_add_input_constant" : node_add_menu_geometry.NODE_MT_gn_input_constant_base,
    "NODES_PT_toolshelf_gn_add_input_gizmo" : node_add_menu_geometry.NODE_MT_gn_input_gizmo_base,
    "NODES_PT_toolshelf_gn_add_input_file" : node_add_menu_geometry.NODE_MT_gn_input_import_base,
    "NODES_PT_toolshelf_gn_add_input_scene" : node_add_menu_geometry.NODE_MT_gn_input_scene_base,

    "NODES_PT_toolshelf_gn_add_output" : node_add_menu_geometry.NODE_MT_gn_output_base,
    
    "NODES_PT_toolshelf_gn_add_attribute" : node_add_menu_geometry.NODE_MT_gn_attribute_base,

    "NODES_PT_toolshelf_gn_add_geometry" : node_add_menu_geometry.NODE_MT_gn_geometry_base,
    "NODES_PT_toolshelf_gn_add_geometry_read" : node_add_menu_geometry.NODE_MT_gn_geometry_read_base,
    "NODES_PT_toolshelf_gn_add_geometry_sample" : node_add_menu_geometry.NODE_MT_gn_geometry_sample_base,
    "NODES_PT_toolshelf_gn_add_geometry_write" : node_add_menu_geometry.NODE_MT_gn_geometry_write_base,
    "NODES_PT_toolshelf_gn_add_geometry_material" : node_add_menu_geometry.NODE_MT_gn_material_base,
    "NODES_PT_toolshelf_gn_add_geometry_operations" : node_add_menu_geometry.NODE_MT_gn_geometry_operations_base,

    "NODES_PT_toolshelf_gn_add_curve" : node_add_menu_geometry.NODE_MT_gn_curve_base,
    "NODES_PT_toolshelf_gn_add_curve_read" : node_add_menu_geometry.NODE_MT_gn_curve_read_base,
    "NODES_PT_toolshelf_gn_add_curve_sample" : node_add_menu_geometry.NODE_MT_gn_curve_sample_base,
    "NODES_PT_toolshelf_gn_add_curve_write" : node_add_menu_geometry.NODE_MT_gn_curve_write_base,
    "NODES_PT_toolshelf_gn_add_curve_operations" : node_add_menu_geometry.NODE_MT_gn_curve_operations_base,
    "NODES_PT_toolshelf_gn_add_curve_primitives" : node_add_menu_geometry.NODE_MT_gn_curve_primitives_base,
    "NODES_PT_toolshelf_gn_add_curve_topology" : node_add_menu_geometry.NODE_MT_gn_curve_topology_base,

    "NODES_PT_toolshelf_gn_add_grease_pencil" : node_add_menu_geometry.NODE_MT_gn_grease_pencil_base,
    "NODES_PT_toolshelf_gn_add_grease_pencil_read" : node_add_menu_geometry.NODE_MT_gn_grease_pencil_read_base,
    "NODES_PT_toolshelf_gn_add_grease_pencil_write" : node_add_menu_geometry.NODE_MT_gn_grease_pencil_write_base,
    "NODES_PT_toolshelf_gn_add_grease_pencil_operations" : node_add_menu_geometry.NODE_MT_gn_grease_pencil_operations_base,

    "NODES_PT_toolshelf_gn_add_instances" : node_add_menu_geometry.NODE_MT_gn_instance_base,

    "NODES_PT_toolshelf_gn_add_mesh" : node_add_menu_geometry.NODE_MT_gn_mesh_base,
    "NODES_PT_toolshelf_gn_add_mesh_read" : node_add_menu_geometry.NODE_MT_gn_mesh_read_base,
    "NODES_PT_toolshelf_gn_add_mesh_sample" : node_add_menu_geometry.NODE_MT_gn_mesh_sample_base,
    "NODES_PT_toolshelf_gn_add_mesh_write" : node_add_menu_geometry.NODE_MT_gn_mesh_write_base,
    "NODES_PT_toolshelf_gn_add_mesh_operations" : node_add_menu_geometry.NODE_MT_gn_mesh_operations_base,
    "NODES_PT_toolshelf_gn_add_mesh_primitives" : node_add_menu_geometry.NODE_MT_gn_mesh_primitives_base,
    "NODES_PT_toolshelf_gn_add_mesh_topology" : node_add_menu_geometry.NODE_MT_gn_mesh_topology_base,
    "NODES_PT_toolshelf_gn_add_mesh_uv" : node_add_menu_geometry.NODE_MT_gn_mesh_uv_base,

    "NODES_PT_toolshelf_gn_add_point" : node_add_menu_geometry.NODE_MT_gn_point_base,

    "NODES_PT_toolshelf_gn_add_volume" : node_add_menu_geometry.NODE_MT_gn_volume_base,
    "NODES_PT_toolshelf_gn_add_volume_read" : node_add_menu_geometry.NODE_MT_gn_volume_read_base,
    "NODES_PT_toolshelf_gn_add_volume_sample" : node_add_menu_geometry.NODE_MT_gn_volume_sample_base,
    "NODES_PT_toolshelf_gn_add_volume_write" : node_add_menu_geometry.NODE_MT_gn_volume_write_base,
    "NODES_PT_toolshelf_gn_add_volume_operations" : node_add_menu_geometry.NODE_MT_gn_volume_operations_base,
    "NODES_PT_toolshelf_gn_add_volume_primitives" : node_add_menu_geometry.NODE_MT_gn_volume_primitives_base,

    "NODES_PT_toolshelf_gn_add_simulation" : node_add_menu_geometry.NODE_MT_gn_simulation_base,
    "NODES_PT_toolshelf_gn_add_color" : node_add_menu_geometry.NODE_MT_gn_color_base,
    "NODES_PT_toolshelf_gn_add_texture" : node_add_menu_geometry.NODE_MT_gn_texture_base,

    "NODES_PT_toolshelf_gn_add_utilities" : node_add_menu_geometry.NODE_MT_gn_utilities_base,
    "NODES_PT_toolshelf_gn_add_utilities_math" : node_add_menu_geometry.NODE_MT_gn_utilities_math_base,
    "NODES_PT_toolshelf_gn_add_utilities_text" : node_add_menu_geometry.NODE_MT_gn_utilities_text_base,
    "NODES_PT_toolshelf_gn_add_utilities_vector" : node_add_menu_geometry.NODE_MT_gn_utilities_vector_base,
    "NODES_PT_toolshelf_gn_add_utilities_bundle" : node_add_menu_geometry.NODE_MT_category_utilities_bundle_base,
    "NODES_PT_toolshelf_gn_add_utilities_closure" : node_add_menu_geometry.NODE_MT_category_utilities_closure_base,
    "NODES_PT_toolshelf_gn_add_utilities_field" : node_add_menu_geometry.NODE_MT_gn_utilities_field_base,
    "NODES_PT_toolshelf_gn_add_utilities_lists" : node_add_menu_geometry.NODE_MT_gn_utilities_list_base,
    "NODES_PT_toolshelf_gn_add_utilities_matrix" : node_add_menu_geometry.NODE_MT_gn_utilities_matrix_base,
    "NODES_PT_toolshelf_gn_add_utilities_rotation" : node_add_menu_geometry.NODE_MT_gn_utilities_rotation_base,
    "NODES_PT_toolshelf_gn_add_utilities_sound" : node_add_menu_geometry.NODE_MT_gn_utilities_sound_base,
    "NODES_PT_toolshelf_gn_add_utilities_deprecated" : node_add_menu_geometry.NODE_MT_gn_utilities_deprecated_base,
}


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
    *generate_panels(compositor_nodes_panels, template=CompositorNodesPanel),
    *generate_panels(texture_nodes_panels, template=TextureNodesPanel),
    *generate_panels(geometry_nodes_panels, template=GeometryNodesPanel),
)

# BFA - Custom panels for the sidebar toolshelf (END)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

