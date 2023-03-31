# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty
from nodeitems_utils import node_categories_iter

from . import operators
from . import interface

from .utils.constants import nice_hotkey_name


# Principled prefs
class NWPrincipledPreferences(bpy.types.PropertyGroup):
    base_color: StringProperty(
        name='Base Color',
        default='diffuse diff albedo base col color basecolor',
        description='Naming Components for Base Color maps')
    sss_color: StringProperty(
        name='Subsurface Color',
        default='sss subsurface',
        description='Naming Components for Subsurface Color maps')
    metallic: StringProperty(
        name='Metallic',
        default='metallic metalness metal mtl',
        description='Naming Components for metallness maps')
    specular: StringProperty(
        name='Specular',
        default='specularity specular spec spc',
        description='Naming Components for Specular maps')
    normal: StringProperty(
        name='Normal',
        default='normal nor nrm nrml norm',
        description='Naming Components for Normal maps')
    bump: StringProperty(
        name='Bump',
        default='bump bmp',
        description='Naming Components for bump maps')
    rough: StringProperty(
        name='Roughness',
        default='roughness rough rgh',
        description='Naming Components for roughness maps')
    gloss: StringProperty(
        name='Gloss',
        default='gloss glossy glossiness',
        description='Naming Components for glossy maps')
    displacement: StringProperty(
        name='Displacement',
        default='displacement displace disp dsp height heightmap',
        description='Naming Components for displacement maps')
    transmission: StringProperty(
        name='Transmission',
        default='transmission transparency',
        description='Naming Components for transmission maps')
    emission: StringProperty(
        name='Emission',
        default='emission emissive emit',
        description='Naming Components for emission maps')
    alpha: StringProperty(
        name='Alpha',
        default='alpha opacity',
        description='Naming Components for alpha maps')
    ambient_occlusion: StringProperty(
        name='Ambient Occlusion',
        default='ao ambient occlusion',
        description='Naming Components for AO maps')


# Addon prefs
class NWNodeWrangler(bpy.types.AddonPreferences):
    bl_idname = __package__

    merge_hide: EnumProperty(
        name="Hide Mix nodes",
        items=(
            ("ALWAYS", "Always", "Always collapse the new merge nodes"),
            ("NON_SHADER", "Non-Shader", "Collapse in all cases except for shaders"),
            ("NEVER", "Never", "Never collapse the new merge nodes")
        ),
        default='NON_SHADER',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specify whether to collapse them or show the full node with options expanded")
    merge_position: EnumProperty(
        name="Mix Node Position",
        items=(
            ("CENTER", "Center", "Place the Mix node between the two nodes"),
            ("BOTTOM", "Bottom", "Place the Mix node at the same height as the lowest node")
        ),
        default='CENTER',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specify the position of the new nodes")

    show_hotkey_list: BoolProperty(
        name="Show Hotkey List",
        default=False,
        description="Expand this box into a list of all the hotkeys for functions in this addon"
    )
    hotkey_list_filter: StringProperty(
        name="        Filter by Name",
        default="",
        description="Show only hotkeys that have this text in their name",
        options={'TEXTEDIT_UPDATE'}
    )
    show_principled_lists: BoolProperty(
        name="Show Principled naming tags",
        default=False,
        description="Expand this box into a list of all naming tags for principled texture setup"
    )
    principled_tags: bpy.props.PointerProperty(type=NWPrincipledPreferences)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "merge_position")
        col.prop(self, "merge_hide")

        box = layout.box()
        col = box.column(align=True)
        col.prop(
            self,
            "show_principled_lists",
            text='Edit tags for auto texture detection in Principled BSDF setup',
            toggle=True)
        if self.show_principled_lists:
            tags = self.principled_tags

            col.prop(tags, "base_color")
            col.prop(tags, "sss_color")
            col.prop(tags, "metallic")
            col.prop(tags, "specular")
            col.prop(tags, "rough")
            col.prop(tags, "gloss")
            col.prop(tags, "normal")
            col.prop(tags, "bump")
            col.prop(tags, "displacement")
            col.prop(tags, "transmission")
            col.prop(tags, "emission")
            col.prop(tags, "alpha")
            col.prop(tags, "ambient_occlusion")

        box = layout.box()
        col = box.column(align=True)
        hotkey_button_name = "Show Hotkey List"
        if self.show_hotkey_list:
            hotkey_button_name = "Hide Hotkey List"
        col.prop(self, "show_hotkey_list", text=hotkey_button_name, toggle=True)
        if self.show_hotkey_list:
            col.prop(self, "hotkey_list_filter", icon="VIEWZOOM")
            col.separator()
            for hotkey in kmi_defs:
                if hotkey[7]:
                    hotkey_name = hotkey[7]

                    if self.hotkey_list_filter.lower() in hotkey_name.lower():
                        row = col.row(align=True)
                        row.label(text=hotkey_name)
                        keystr = nice_hotkey_name(hotkey[1])
                        if hotkey[4]:
                            keystr = "Shift " + keystr
                        if hotkey[5]:
                            keystr = "Alt " + keystr
                        if hotkey[3]:
                            keystr = "Ctrl " + keystr
                        row.label(text=keystr)


#
#  REGISTER/UNREGISTER CLASSES AND KEYMAP ITEMS
#
switch_category_menus = []
addon_keymaps = []
# kmi_defs entry: (identifier, key, action, CTRL, SHIFT, ALT, props, nice name)
# props entry: (property name, property value)
kmi_defs = (
    # MERGE NODES
    # NWMergeNodes with Ctrl (AUTO).
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_0', 'PRESS', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), "Merge Nodes (Automatic)"),
    (operators.NWMergeNodes.bl_idname, 'ZERO', 'PRESS', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), "Merge Nodes (Automatic)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), "Merge Nodes (Add)"),
    (operators.NWMergeNodes.bl_idname, 'EQUAL', 'PRESS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), "Merge Nodes (Add)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), "Merge Nodes (Multiply)"),
    (operators.NWMergeNodes.bl_idname, 'EIGHT', 'PRESS', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), "Merge Nodes (Multiply)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), "Merge Nodes (Subtract)"),
    (operators.NWMergeNodes.bl_idname, 'MINUS', 'PRESS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), "Merge Nodes (Subtract)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), "Merge Nodes (Divide)"),
    (operators.NWMergeNodes.bl_idname, 'SLASH', 'PRESS', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), "Merge Nodes (Divide)"),
    (operators.NWMergeNodes.bl_idname, 'COMMA', 'PRESS', True, False, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Less than)"),
    (operators.NWMergeNodes.bl_idname, 'PERIOD', 'PRESS', True, False, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Greater than)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PERIOD', 'PRESS', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'ZCOMBINE'),), "Merge Nodes (Z-Combine)"),
    # NWMergeNodes with Ctrl Alt (MIX or ALPHAOVER)
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_0', 'PRESS', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'ALPHAOVER'),), "Merge Nodes (Alpha Over)"),
    (operators.NWMergeNodes.bl_idname, 'ZERO', 'PRESS', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'ALPHAOVER'),), "Merge Nodes (Alpha Over)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Add)"),
    (operators.NWMergeNodes.bl_idname, 'EQUAL', 'PRESS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Add)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Multiply)"),
    (operators.NWMergeNodes.bl_idname, 'EIGHT', 'PRESS', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Multiply)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Subtract)"),
    (operators.NWMergeNodes.bl_idname, 'MINUS', 'PRESS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Subtract)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Divide)"),
    (operators.NWMergeNodes.bl_idname, 'SLASH', 'PRESS', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Divide)"),
    # NWMergeNodes with Ctrl Shift (MATH)
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Add)"),
    (operators.NWMergeNodes.bl_idname, 'EQUAL', 'PRESS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Add)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Multiply)"),
    (operators.NWMergeNodes.bl_idname, 'EIGHT', 'PRESS', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Multiply)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Subtract)"),
    (operators.NWMergeNodes.bl_idname, 'MINUS', 'PRESS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Subtract)"),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Divide)"),
    (operators.NWMergeNodes.bl_idname, 'SLASH', 'PRESS', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Divide)"),
    (operators.NWMergeNodes.bl_idname, 'COMMA', 'PRESS', True, True, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Less than)"),
    (operators.NWMergeNodes.bl_idname, 'PERIOD', 'PRESS', True, True, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Greater than)"),
    # BATCH CHANGE NODES
    # NWBatchChangeNodes with Alt
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_0', 'PRESS', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), "Batch change blend type (Mix)"),
    (operators.NWBatchChangeNodes.bl_idname, 'ZERO', 'PRESS', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), "Batch change blend type (Mix)"),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), "Batch change blend type (Add)"),
    (operators.NWBatchChangeNodes.bl_idname, 'EQUAL', 'PRESS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), "Batch change blend type (Add)"),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), "Batch change blend type (Multiply)"),
    (operators.NWBatchChangeNodes.bl_idname, 'EIGHT', 'PRESS', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), "Batch change blend type (Multiply)"),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), "Batch change blend type (Subtract)"),
    (operators.NWBatchChangeNodes.bl_idname, 'MINUS', 'PRESS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), "Batch change blend type (Subtract)"),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), "Batch change blend type (Divide)"),
    (operators.NWBatchChangeNodes.bl_idname, 'SLASH', 'PRESS', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), "Batch change blend type (Divide)"),
    (operators.NWBatchChangeNodes.bl_idname, 'COMMA', 'PRESS', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'LESS_THAN'),), "Batch change blend type (Current)"),
    (operators.NWBatchChangeNodes.bl_idname, 'PERIOD', 'PRESS', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'GREATER_THAN'),), "Batch change blend type (Current)"),
    (operators.NWBatchChangeNodes.bl_idname, 'DOWN_ARROW', 'PRESS', False, False, True,
        (('blend_type', 'NEXT'), ('operation', 'NEXT'),), "Batch change blend type (Next)"),
    (operators.NWBatchChangeNodes.bl_idname, 'UP_ARROW', 'PRESS', False, False, True,
        (('blend_type', 'PREV'), ('operation', 'PREV'),), "Batch change blend type (Previous)"),
    # LINK ACTIVE TO SELECTED
    # Don't use names, don't replace links (K)
    (operators.NWLinkActiveToSelected.bl_idname, 'K', 'PRESS', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', False),), "Link active to selected (Don't replace links)"),
    # Don't use names, replace links (Shift K)
    (operators.NWLinkActiveToSelected.bl_idname, 'K', 'PRESS', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', False),), "Link active to selected (Replace links)"),
    # Use node name, don't replace links (')
    (operators.NWLinkActiveToSelected.bl_idname, 'QUOTE', 'PRESS', False, False, False,
        (('replace', False), ('use_node_name', True), ('use_outputs_names', False),), "Link active to selected (Don't replace links, node names)"),
    # Use node name, replace links (Shift ')
    (operators.NWLinkActiveToSelected.bl_idname, 'QUOTE', 'PRESS', False, True, False,
        (('replace', True), ('use_node_name', True), ('use_outputs_names', False),), "Link active to selected (Replace links, node names)"),
    # Don't use names, don't replace links (;)
    (operators.NWLinkActiveToSelected.bl_idname, 'SEMI_COLON', 'PRESS', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', True),), "Link active to selected (Don't replace links, output names)"),
    # Don't use names, replace links (')
    (operators.NWLinkActiveToSelected.bl_idname, 'SEMI_COLON', 'PRESS', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', True),), "Link active to selected (Replace links, output names)"),
    # CHANGE MIX FACTOR
    (operators.NWChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', False,
     False, True, (('option', -0.1),), "Reduce Mix Factor by 0.1"),
    (operators.NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', False,
     False, True, (('option', 0.1),), "Increase Mix Factor by 0.1"),
    (operators.NWChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', False,
     True, True, (('option', -0.01),), "Reduce Mix Factor by 0.01"),
    (operators.NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', False,
     True, True, (('option', 0.01),), "Increase Mix Factor by 0.01"),
    (operators.NWChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS',
     True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (operators.NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS',
     True, True, True, (('option', 1.0),), "Set Mix Factor to 1.0"),
    (operators.NWChangeMixFactor.bl_idname, 'NUMPAD_0', 'PRESS',
     True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (operators.NWChangeMixFactor.bl_idname, 'ZERO', 'PRESS', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (operators.NWChangeMixFactor.bl_idname, 'NUMPAD_1', 'PRESS', True, True, True, (('option', 1.0),), "Mix Factor to 1.0"),
    (operators.NWChangeMixFactor.bl_idname, 'ONE', 'PRESS', True, True, True, (('option', 1.0),), "Set Mix Factor to 1.0"),
    # CLEAR LABEL (Alt L)
    (operators.NWClearLabel.bl_idname, 'L', 'PRESS', False, False, True, (('option', False),), "Clear node labels"),
    # MODIFY LABEL (Alt Shift L)
    (operators.NWModifyLabels.bl_idname, 'L', 'PRESS', False, True, True, None, "Modify node labels"),
    # Copy Label from active to selected
    (operators.NWCopyLabel.bl_idname, 'V', 'PRESS', False, True, False,
     (('option', 'FROM_ACTIVE'),), "Copy label from active to selected"),
    # DETACH OUTPUTS (Alt Shift D)
    (operators.NWDetachOutputs.bl_idname, 'D', 'PRESS', False, True, True, None, "Detach outputs"),
    # LINK TO OUTPUT NODE (O)
    (operators.NWLinkToOutputNode.bl_idname, 'O', 'PRESS', False, False, False, None, "Link to output node"),
    # SELECT PARENT/CHILDREN
    # Select Children
    (operators.NWSelectParentChildren.bl_idname, 'RIGHT_BRACKET', 'PRESS',
     False, False, False, (('option', 'CHILD'),), "Select children"),
    # Select Parent
    (operators.NWSelectParentChildren.bl_idname, 'LEFT_BRACKET', 'PRESS',
     False, False, False, (('option', 'PARENT'),), "Select Parent"),
    # Add Texture Setup
    (operators.NWAddTextureSetup.bl_idname, 'T', 'PRESS', True, False, False, None, "Add texture setup"),
    # Add Principled BSDF Texture Setup
    (operators.NWAddPrincipledSetup.bl_idname, 'T', 'PRESS', True, True, False, None, "Add Principled texture setup"),
    # Reset backdrop
    (operators.NWResetBG.bl_idname, 'Z', 'PRESS', False, False, False, None, "Reset backdrop image zoom"),
    # Delete unused
    (operators.NWDeleteUnused.bl_idname, 'X', 'PRESS', False, False, True, None, "Delete unused nodes"),
    # Frame Selected
    (operators.NWFrameSelected.bl_idname, 'P', 'PRESS', False, True, False, None, "Frame selected nodes"),
    # Swap Links
    (operators.NWSwapLinks.bl_idname, 'S', 'PRESS', False, False, True, None, "Swap Links"),
    # Preview Node
    (operators.NWPreviewNode.bl_idname, 'LEFTMOUSE', 'PRESS', True, True,
     False, (('run_in_geometry_nodes', False),), "Preview node output"),
    (operators.NWPreviewNode.bl_idname, 'LEFTMOUSE', 'PRESS', False, True,
     True, (('run_in_geometry_nodes', True),), "Preview node output"),
    # Reload Images
    (operators.NWReloadImages.bl_idname, 'R', 'PRESS', False, False, True, None, "Reload images"),
    # Lazy Mix
    (operators.NWLazyMix.bl_idname, 'RIGHTMOUSE', 'PRESS', True, True, False, None, "Lazy Mix"),
    # Lazy Connect
    (operators.NWLazyConnect.bl_idname, 'RIGHTMOUSE', 'PRESS', False, False, True, (('with_menu', False),), "Lazy Connect"),
    # Lazy Connect with Menu
    (operators.NWLazyConnect.bl_idname, 'RIGHTMOUSE', 'PRESS', False,
     True, True, (('with_menu', True),), "Lazy Connect with Socket Menu"),
    # Viewer Tile Center
    (operators.NWViewerFocus.bl_idname, 'LEFTMOUSE', 'DOUBLE_CLICK', False, False, False, None, "Set Viewers Tile Center"),
    # Align Nodes
    (operators.NWAlignNodes.bl_idname, 'EQUAL', 'PRESS', False, True,
     False, None, "Align selected nodes neatly in a row/column"),
    # Reset Nodes (Back Space)
    (operators.NWResetNodes.bl_idname, 'BACK_SPACE', 'PRESS', False, False,
     False, None, "Revert node back to default state, but keep connections"),
    # MENUS
    ('wm.call_menu', 'W', 'PRESS', False, True, False, (('name', interface.NodeWranglerMenu.bl_idname),), "Node Wrangler menu"),
    ('wm.call_menu', 'SLASH', 'PRESS', False, False, False,
     (('name', interface.NWAddReroutesMenu.bl_idname),), "Add Reroutes menu"),
    ('wm.call_menu', 'NUMPAD_SLASH', 'PRESS', False, False, False,
     (('name', interface.NWAddReroutesMenu.bl_idname),), "Add Reroutes menu"),
    ('wm.call_menu', 'BACK_SLASH', 'PRESS', False, False, False,
     (('name', interface.NWLinkActiveToSelectedMenu.bl_idname),), "Link active to selected (menu)"),
    ('wm.call_menu', 'C', 'PRESS', False, True, False,
     (('name', interface.NWCopyToSelectedMenu.bl_idname),), "Copy to selected (menu)"),
    ('wm.call_menu', 'S', 'PRESS', False, True, False,
     (('name', interface.NWSwitchNodeTypeMenu.bl_idname),), "Switch node type menu"),
)

classes = (
    NWPrincipledPreferences, NWNodeWrangler
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # keymaps
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
        for (identifier, key, action, CTRL, SHIFT, ALT, props, nicename) in kmi_defs:
            kmi = km.keymap_items.new(identifier, key, action, ctrl=CTRL, shift=SHIFT, alt=ALT)
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi))

    # switch submenus
    switch_category_menus.clear()
    for cat in node_categories_iter(None):
        if cat.name not in ['Group', 'Script']:
            idname = f"NODE_MT_nw_switch_{cat.identifier}_submenu"
            switch_category_type = type(idname, (bpy.types.Menu,), {
                "bl_space_type": 'NODE_EDITOR',
                "bl_label": cat.name,
                "category": cat,
                "poll": cat.poll,
                "draw": interface.draw_switch_category_submenu,
            })

            switch_category_menus.append(switch_category_type)

            bpy.utils.register_class(switch_category_type)


def unregister():
    for cat_types in switch_category_menus:
        bpy.utils.unregister_class(cat_types)
    switch_category_menus.clear()

    # keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
