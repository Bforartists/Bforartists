# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel, Menu
from bpy.props import StringProperty
from nodeitems_utils import node_categories_iter, NodeItemCustom

from . import operators

from .utils.constants import blend_types, geo_combine_operations, operations
from .utils.nodes import get_nodes_links, nw_check, NWBase


def drawlayout(context, layout, mode='non-panel'):
    tree_type = context.space_data.tree_type

    col = layout.column(align=True)
    col.menu(NWMergeNodesMenu.bl_idname)
    col.separator()

    col = layout.column(align=True)
    col.menu(NWSwitchNodeTypeMenu.bl_idname, text="Switch Node Type")
    col.separator()

    if tree_type == 'ShaderNodeTree':
        col = layout.column(align=True)
        col.operator(operators.NWAddTextureSetup.bl_idname, text="Add Texture Setup", icon='NODE_SEL')
        col.operator(operators.NWAddPrincipledSetup.bl_idname, text="Add Principled Setup", icon='NODE_SEL')
        col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWDetachOutputs.bl_idname, icon='UNLINKED')
    col.operator(operators.NWSwapLinks.bl_idname)
    col.menu(NWAddReroutesMenu.bl_idname, text="Add Reroutes", icon='LAYER_USED')
    col.separator()

    col = layout.column(align=True)
    col.menu(NWLinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected", icon='LINKED')
    if tree_type != 'GeometryNodeTree':
        col.operator(operators.NWLinkToOutputNode.bl_idname, icon='DRIVER')
    col.separator()

    col = layout.column(align=True)
    if mode == 'panel':
        row = col.row(align=True)
        row.operator(operators.NWClearLabel.bl_idname).option = True
        row.operator(operators.NWModifyLabels.bl_idname)
    else:
        col.operator(operators.NWClearLabel.bl_idname).option = True
        col.operator(operators.NWModifyLabels.bl_idname)
    col.menu(NWBatchChangeNodesMenu.bl_idname, text="Batch Change")
    col.separator()
    col.menu(NWCopyToSelectedMenu.bl_idname, text="Copy to Selected")
    col.separator()

    col = layout.column(align=True)
    if tree_type == 'CompositorNodeTree':
        col.operator(operators.NWResetBG.bl_idname, icon='ZOOM_PREVIOUS')
    if tree_type != 'GeometryNodeTree':
        col.operator(operators.NWReloadImages.bl_idname, icon='FILE_REFRESH')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWFrameSelected.bl_idname, icon='STICKY_UVS_LOC')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWAlignNodes.bl_idname, icon='CENTER_ONLY')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWDeleteUnused.bl_idname, icon='CANCEL')
    col.separator()


class NodeWranglerPanel(Panel, NWBase):
    bl_idname = "NODE_PT_nw_node_wrangler"
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Node Wrangler"
    bl_region_type = "UI"
    bl_category = "Node Wrangler"

    prepend: StringProperty(
        name='prepend',
    )
    append: StringProperty()
    remove: StringProperty()

    def draw(self, context):
        self.layout.label(text="(Quick access: Shift+W)")
        drawlayout(context, self.layout, mode='panel')


#
#  M E N U S
#
class NodeWranglerMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_node_wrangler_menu"
    bl_label = "Node Wrangler"

    def draw(self, context):
        self.layout.operator_context = 'INVOKE_DEFAULT'
        drawlayout(context, self.layout)


class NWMergeNodesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_nodes_menu"
    bl_label = "Merge Selected Nodes"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(NWMergeShadersMenu.bl_idname, text="Use Shaders")
        if type == 'GeometryNodeTree':
            layout.menu(NWMergeGeometryMenu.bl_idname, text="Use Geometry Nodes")
            layout.menu(NWMergeMathMenu.bl_idname, text="Use Math Nodes")
        else:
            layout.menu(NWMergeMixMenu.bl_idname, text="Use Mix Nodes")
            layout.menu(NWMergeMathMenu.bl_idname, text="Use Math Nodes")
            props = layout.operator(operators.NWMergeNodes.bl_idname, text="Use Z-Combine Nodes")
            props.mode = 'MIX'
            props.merge_type = 'ZCOMBINE'
            props = layout.operator(operators.NWMergeNodes.bl_idname, text="Use Alpha Over Nodes")
            props.mode = 'MIX'
            props.merge_type = 'ALPHAOVER'


class NWMergeGeometryMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_geometry_menu"
    bl_label = "Merge Selected Nodes using Geometry Nodes"

    def draw(self, context):
        layout = self.layout
        # The boolean node + Join Geometry node
        for type, name, description in geo_combine_operations:
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'GEOMETRY'


class NWMergeShadersMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_shaders_menu"
    bl_label = "Merge Selected Nodes using Shaders"

    def draw(self, context):
        layout = self.layout
        for type in ('MIX', 'ADD'):
            name = f'{type.capitalize()} Shader'
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'SHADER'


class NWMergeMixMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_mix_menu"
    bl_label = "Merge Selected Nodes using Mix"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MIX'


class NWConnectionListOutputs(Menu, NWBase):
    bl_idname = "NODE_MT_nw_connection_list_out"
    bl_label = "From:"

    def draw(self, context):
        layout = self.layout
        nodes, links = get_nodes_links(context)

        n1 = nodes[context.scene.NWLazySource]
        for index, output in enumerate(n1.outputs):
            # Only show sockets that are exposed.
            if output.enabled:
                layout.operator(
                    operators.NWCallInputsMenu.bl_idname,
                    text=output.name,
                    icon="RADIOBUT_OFF").from_socket = index


class NWConnectionListInputs(Menu, NWBase):
    bl_idname = "NODE_MT_nw_connection_list_in"
    bl_label = "To:"

    def draw(self, context):
        layout = self.layout
        nodes, links = get_nodes_links(context)

        n2 = nodes[context.scene.NWLazyTarget]

        for index, input in enumerate(n2.inputs):
            # Only show sockets that are exposed.
            # This prevents, for example, the scale value socket
            # of the vector math node being added to the list when
            # the mode is not 'SCALE'.
            if input.enabled:
                op = layout.operator(operators.NWMakeLink.bl_idname, text=input.name, icon="FORWARD")
                op.from_socket = context.scene.NWSourceSocket
                op.to_socket = index


class NWMergeMathMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_merge_math_menu"
    bl_label = "Merge Selected Nodes using Math"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MATH'


class NWBatchChangeNodesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_batch_change_nodes_menu"
    bl_label = "Batch Change Selected Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(NWBatchChangeBlendTypeMenu.bl_idname)
        layout.menu(NWBatchChangeOperationMenu.bl_idname)


class NWBatchChangeBlendTypeMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_batch_change_blend_type_menu"
    bl_label = "Batch Change Blend Type"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(operators.NWBatchChangeNodes.bl_idname, text=name)
            props.blend_type = type
            props.operation = 'CURRENT'


class NWBatchChangeOperationMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_batch_change_operation_menu"
    bl_label = "Batch Change Math Operation"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(operators.NWBatchChangeNodes.bl_idname, text=name)
            props.blend_type = 'CURRENT'
            props.operation = type


class NWCopyToSelectedMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_copy_node_properties_menu"
    bl_label = "Copy to Selected"

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.NWCopySettings.bl_idname, text="Settings from Active")
        layout.menu(NWCopyLabelMenu.bl_idname)


class NWCopyLabelMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_copy_label_menu"
    bl_label = "Copy Label"

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.NWCopyLabel.bl_idname, text="from Active Node's Label").option = 'FROM_ACTIVE'
        layout.operator(operators.NWCopyLabel.bl_idname, text="from Linked Node's Label").option = 'FROM_NODE'
        layout.operator(operators.NWCopyLabel.bl_idname, text="from Linked Output's Name").option = 'FROM_SOCKET'


class NWAddReroutesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_add_reroutes_menu"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroute Nodes to Selected Nodes' Outputs"

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.NWAddReroutes.bl_idname, text="to All Outputs").option = 'ALL'
        layout.operator(operators.NWAddReroutes.bl_idname, text="to Loose Outputs").option = 'LOOSE'
        layout.operator(operators.NWAddReroutes.bl_idname, text="to Linked Outputs").option = 'LINKED'


class NWLinkActiveToSelectedMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_active_to_selected_menu"
    bl_label = "Link Active to Selected"

    def draw(self, context):
        layout = self.layout
        layout.menu(NWLinkStandardMenu.bl_idname)
        layout.menu(NWLinkUseNodeNameMenu.bl_idname)
        layout.menu(NWLinkUseOutputsNamesMenu.bl_idname)


class NWLinkStandardMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_standard_menu"
    bl_label = "To All Selected"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = False
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = False


class NWLinkUseNodeNameMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_use_node_name_menu"
    bl_label = "Use Node Name/Label"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = True
        props.use_outputs_names = False
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = True
        props.use_outputs_names = False


class NWLinkUseOutputsNamesMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_link_use_outputs_names_menu"
    bl_label = "Use Outputs Names"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = True
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = True


class NWAttributeMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_nw_node_attribute_menu"
    bl_label = "Attributes"

    @classmethod
    def poll(cls, context):
        valid = False
        if nw_check(context):
            snode = context.space_data
            valid = snode.tree_type == 'ShaderNodeTree'
        return valid

    def draw(self, context):
        l = self.layout
        nodes, links = get_nodes_links(context)
        mat = context.object.active_material

        objs = []
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                if slot.material == mat:
                    objs.append(obj)
        attrs = []
        for obj in objs:
            if obj.data.attributes:
                for attr in obj.data.attributes:
                    attrs.append(attr.name)
        attrs = list(set(attrs))  # get a unique list

        if attrs:
            for attr in attrs:
                l.operator(operators.NWAddAttrNode.bl_idname, text=attr).attr_name = attr
        else:
            l.label(text="No attributes on objects with this material")


class NWSwitchNodeTypeMenu(Menu, NWBase):
    bl_idname = "NODE_MT_nw_switch_node_type_menu"
    bl_label = "Switch Type to..."

    def draw(self, context):
        layout = self.layout
        categories = [c for c in node_categories_iter(context)
                      if c.name not in ['Group', 'Script']]
        for cat in categories:
            idname = f"NODE_MT_nw_switch_{cat.identifier}_submenu"
            if hasattr(bpy.types, idname):
                layout.menu(idname)
            else:
                layout.label(text="Unable to load altered node lists.")
                layout.label(text="Please re-enable Node Wrangler.")
                break


def draw_switch_category_submenu(self, context):
    layout = self.layout
    if self.category.name == 'Layout':
        for node in self.category.items(context):
            if node.nodetype != 'NodeFrame':
                props = layout.operator(operators.NWSwitchNodeType.bl_idname, text=node.label)
                props.to_type = node.nodetype
    else:
        for node in self.category.items(context):
            if isinstance(node, NodeItemCustom):
                node.draw(self, layout, context)
                continue
            props = layout.operator(operators.NWSwitchNodeType.bl_idname, text=node.label)
            props.to_type = node.nodetype

#
#  APPENDAGES TO EXISTING UI
#


def select_parent_children_buttons(self, context):
    layout = self.layout
    layout.operator(operators.NWSelectParentChildren.bl_idname,
                    text="Select frame's members (children)").option = 'CHILD'
    layout.operator(operators.NWSelectParentChildren.bl_idname, text="Select parent frame").option = 'PARENT'


def attr_nodes_menu_func(self, context):
    col = self.layout.column(align=True)
    col.menu("NODE_MT_nw_node_attribute_menu")
    col.separator()


def multipleimages_menu_func(self, context):
    col = self.layout.column(align=True)
    col.operator(operators.NWAddMultipleImages.bl_idname, text="Multiple Images")
    col.operator(operators.NWAddSequence.bl_idname, text="Image Sequence")
    col.separator()


def bgreset_menu_func(self, context):
    self.layout.operator(operators.NWResetBG.bl_idname)


def save_viewer_menu_func(self, context):
    if nw_check(context):
        if context.space_data.tree_type == 'CompositorNodeTree':
            if context.scene.node_tree.nodes.active:
                if context.scene.node_tree.nodes.active.type == "VIEWER":
                    self.layout.operator(operators.NWSaveViewer.bl_idname, icon='FILE_IMAGE')


def reset_nodes_button(self, context):
    node_active = context.active_node
    node_selected = context.selected_nodes
    node_ignore = ["FRAME", "REROUTE", "GROUP"]

    # Check if active node is in the selection and respective type
    if (len(node_selected) == 1) and node_active and node_active.select and node_active.type not in node_ignore:
        row = self.layout.row()
        row.operator(operators.NWResetNodes.bl_idname, text="Reset Node", icon="FILE_REFRESH")
        self.layout.separator()

    elif (len(node_selected) == 1) and node_active and node_active.select and node_active.type == "FRAME":
        row = self.layout.row()
        row.operator(operators.NWResetNodes.bl_idname, text="Reset Nodes in Frame", icon="FILE_REFRESH")
        self.layout.separator()


classes = (
    NodeWranglerPanel,
    NodeWranglerMenu,
    NWMergeNodesMenu,
    NWMergeGeometryMenu,
    NWMergeShadersMenu,
    NWMergeMixMenu,
    NWConnectionListOutputs,
    NWConnectionListInputs,
    NWMergeMathMenu,
    NWBatchChangeNodesMenu,
    NWBatchChangeBlendTypeMenu,
    NWBatchChangeOperationMenu,
    NWCopyToSelectedMenu,
    NWCopyLabelMenu,
    NWAddReroutesMenu,
    NWLinkActiveToSelectedMenu,
    NWLinkStandardMenu,
    NWLinkUseNodeNameMenu,
    NWLinkUseOutputsNamesMenu,
    NWAttributeMenu,
    NWSwitchNodeTypeMenu,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # menu items
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)
    bpy.types.NODE_MT_category_SH_NEW_INPUT.prepend(attr_nodes_menu_func)
    bpy.types.NODE_PT_backdrop.append(bgreset_menu_func)
    bpy.types.NODE_PT_active_node_generic.append(save_viewer_menu_func)
    bpy.types.NODE_MT_category_SH_NEW_TEXTURE.prepend(multipleimages_menu_func)
    bpy.types.NODE_MT_category_CMP_INPUT.prepend(multipleimages_menu_func)
    bpy.types.NODE_PT_active_node_generic.prepend(reset_nodes_button)
    bpy.types.NODE_MT_node.prepend(reset_nodes_button)


def unregister():
    # menu items
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    bpy.types.NODE_MT_category_SH_NEW_INPUT.remove(attr_nodes_menu_func)
    bpy.types.NODE_PT_backdrop.remove(bgreset_menu_func)
    bpy.types.NODE_PT_active_node_generic.remove(save_viewer_menu_func)
    bpy.types.NODE_MT_category_SH_NEW_TEXTURE.remove(multipleimages_menu_func)
    bpy.types.NODE_MT_category_CMP_INPUT.remove(multipleimages_menu_func)
    bpy.types.NODE_PT_active_node_generic.remove(reset_nodes_button)
    bpy.types.NODE_MT_node.remove(reset_nodes_button)

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
