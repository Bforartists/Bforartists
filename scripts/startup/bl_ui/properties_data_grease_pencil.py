# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
from bpy.types import Panel, Menu, UIList, Operator # BFA - needed for move layer up and down operators
from rna_prop_ui import PropertyPanel
from .space_properties import PropertiesAnimationMixin

# BFA - needed for move layer up and down operators
from bpy.props import (
    EnumProperty,
)

class DataButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return hasattr(context, "grease_pencil") and context.grease_pencil


class LayerDataButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        grease_pencil = context.grease_pencil
        return grease_pencil and grease_pencil.layers.active


class GREASE_PENCIL_UL_masks(UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        mask = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(mask, "name", text="", emboss=False, icon_value=icon)
            row.prop(mask, "invert", text="", emboss=False)
            row.prop(mask, "hide", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.prop(mask, "name", text="", emboss=False, icon_value=icon)


class GreasePencil_LayerMaskPanel:
    def draw_header(self, context):
        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active

        self.layout.prop(layer, "use_masks", text="", toggle=0)

    def draw(self, context):
        layout = self.layout
        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active

        layout = self.layout
        layout.enabled = layer.use_masks

        if not layer:
            return

        rows = 4
        row = layout.row()
        col = row.column()
        col.template_list(
            "GREASE_PENCIL_UL_masks", "", layer, "mask_layers", layer.mask_layers,
            "active_mask_index", rows=rows, sort_lock=True,
        )

        col = row.column(align=True)
        col.menu("GREASE_PENCIL_MT_layer_mask_add", icon='ADD', text="")
        col.operator("grease_pencil.layer_mask_remove", icon='REMOVE', text="")

        col.separator()

        sub = col.column(align=True)
        sub.operator("grease_pencil.layer_mask_reorder", icon='TRIA_UP', text="").direction = 'UP'
        sub.operator("grease_pencil.layer_mask_reorder", icon='TRIA_DOWN', text="").direction = 'DOWN'


class GreasePencil_LayerTransformPanel:
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active
        layout.active = not layer.lock

        row = layout.row(align=True)
        row.prop(layer, "translation")

        row = layout.row(align=True)
        row.prop(layer, "rotation")

        row = layout.row(align=True)
        row.prop(layer, "scale")


class GreasePencil_LayerAdjustmentsPanel:
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active
        layout.active = not layer.lock

        # Layer options
        col = layout.column(align=True)

        col.prop(layer, "tint_color")
        col.prop(layer, "tint_factor", text="Factor", slider=True)

        col = layout.row(align=True)
        col.prop(layer, "radius_offset", text="Stroke Thickness")


class GreasePencil_LayerRelationsPanel:
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active
        layout.active = not layer.lock

        row = layout.row(align=True)
        row.prop(layer, "parent", text="Parent")

        if layer.parent and layer.parent.type == 'ARMATURE':
            row = layout.row(align=True)
            row.prop_search(layer, "parent_bone", layer.parent.data, "bones", text="Bone")

        layout.separator()

        col = layout.row(align=True)
        col.prop(layer, "pass_index")

        col = layout.row(align=True)
        col.prop_search(layer, "viewlayer_render", context.scene, "view_layers", text="View Layer")

        col = layout.row(align=True)
        # Only enable this property when a view layer is selected.
        if  bool(layer.viewlayer_render):
            col.use_property_split = False
            col.prop(layer, "use_viewlayer_masks")


class GreasePencil_LayerDisplayPanel:
    bl_label = "Display"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active

        layout.prop(layer, "channel_color", text="Channel Color")


class GREASE_PENCIL_MT_layer_mask_add(Menu):
    bl_label = "Add Mask"

    def draw(self, context):
        layout = self.layout

        grease_pencil = context.grease_pencil
        active_layer = grease_pencil.layers.active
        found = False
        for layer in grease_pencil.layers:
            if layer == active_layer or layer.name in active_layer.mask_layers:
                continue

            found = True
            props = layout.operator("grease_pencil.layer_mask_add", text=layer.name, icon="GREASEPENCIL")
            props.name = layer.name

        if not found:
            layout.label(text="No layers to add")


class DATA_PT_context_grease_pencil(DataButtonsPanel, Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout

        ob = context.object
        grease_pencil = context.grease_pencil
        space = context.space_data

        if ob:
            layout.template_ID(ob, "data")
        elif grease_pencil:
            layout.template_ID(space, "pin_id")


class GREASE_PENCIL_MT_grease_pencil_add_layer_extra(Menu):
    bl_label = "Add Extra"

    def draw(self, context):
        layout = self.layout
        grease_pencil = context.grease_pencil
        layer = grease_pencil.layers.active
        space = context.space_data

        if space.type == 'PROPERTIES':
            layout.operator("grease_pencil.layer_group_add", text="Add Group", icon = "GROUP")

            layout.operator("grease_pencil.layer_group_remove", text="Delete Group", icon = 'DELETE').keep_children = False
            layout.operator("grease_pencil.layer_group_remove", text="Ungroup", icon = 'NODE_UNGROUP').keep_children = True

        layout.separator()
        layout.operator("grease_pencil.layer_move_top", text="Move to Top", icon='TRIA_UP_BAR') # bfa - added move up/down operators
        layout.operator("grease_pencil.layer_move_bottom", text="Move to Bottom", icon='TRIA_DOWN_BAR') # bfa - added move up/down operators

        layout.separator()
        layout.operator("grease_pencil.layer_duplicate", text="Duplicate", icon='DUPLICATE').empty_keyframes = False
        layout.operator("grease_pencil.layer_duplicate", text="Duplicate Empty Keyframes", icon='DUPLICATE' ).empty_keyframes = True

        layout.separator()
        layout.operator("grease_pencil.layer_reveal", icon='RESTRICT_VIEW_OFF', text="Show All")
        layout.operator("grease_pencil.layer_hide", icon='RESTRICT_VIEW_ON', text="Hide Others").unselected = True

        layout.separator()
        layout.operator("grease_pencil.layer_lock_all", icon='LOCKED', text="Lock All").lock = True
        layout.operator("grease_pencil.layer_lock_all", icon='UNLOCKED', text="Unlock All").lock = False

        layout.separator()
        layout.operator("grease_pencil.layer_merge", text="Merge Down", icon = 'MERGE').mode = 'ACTIVE'
        layout.operator("grease_pencil.layer_merge", text="Merge Group", icon = 'MERGE').mode = 'GROUP'
        layout.operator("grease_pencil.layer_merge", text="Merge All", icon = 'MERGE').mode = 'ALL'

        layout.separator()
        layout.operator("grease_pencil.relative_layer_mask_add", text="Mask with Layer Above").mode = 'ABOVE'
        layout.operator("grease_pencil.relative_layer_mask_add", text="Mask with Layer Below").mode = 'BELOW'

        layout.separator()
        layout.operator("grease_pencil.layer_duplicate_object", text="Copy Layer to Selected", icon = 'PASTEDOWN').only_active = True
        layout.operator("grease_pencil.layer_duplicate_object", text="Copy All Layers to Selected", icon = 'PASTEDOWN').only_active = False


class GREASE_PENCIL_MT_group_context_menu(Menu):
    bl_label = "Layer Group"

    def draw(self, context):
        layout = self.layout
        layout.operator("grease_pencil.layer_group_remove", text="Delete Group", icon = 'DELETE').keep_children = False
        layout.operator("grease_pencil.layer_group_remove", text="Ungroup", icon = 'NODE_UNGROUP').keep_children = True
        layout.operator("grease_pencil.layer_merge", text="Merge Group").mode = 'GROUP'

        layout.separator()
        row = layout.row(align=True)
        row.operator_enum("grease_pencil.layer_group_color_tag", "color_tag", icon_only=True)


class DATA_PT_grease_pencil_layers(DataButtonsPanel, Panel):
    bl_label = "Layers"

    @classmethod
    def draw_settings(cls, layout, grease_pencil):
        layer = grease_pencil.layers.active
        is_layer_active = layer is not None
        is_group_active = grease_pencil.layer_groups.active is not None

        row = layout.row()
        row.template_grease_pencil_layer_tree()

        col = row.column()
        sub = col.column(align=True)
        sub.operator_context = 'EXEC_DEFAULT'
        sub.operator("grease_pencil.layer_add", icon='ADD', text="")
        sub.operator("grease_pencil.layer_group_add", icon='COLLECTION_NEW', text="")

        sub.separator()

        if is_layer_active:
            sub.operator("grease_pencil.layer_remove", icon='REMOVE', text="")
        if is_group_active:
            sub.operator("grease_pencil.layer_group_remove", icon='REMOVE', text="").keep_children = True

        col.menu("GREASE_PENCIL_MT_grease_pencil_add_layer_extra", icon='DOWNARROW_HLT', text="") # BFA - moved below per standards

        sub = col.column(align=True)
        sub.operator("grease_pencil.layer_move", icon='TRIA_UP', text="").direction = 'UP'
        sub.operator("grease_pencil.layer_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
        #sub.operator_context = 'EXEC_DEFAULT'
        #sub.operator("grease_pencil.interface_item_move", icon='TRIA_UP', text="").direction = 'UP' # BFA - WIP - operator for GUI buttons to re-order in and out of groups
        #sub.operator("grease_pencil.interface_item_move", icon='TRIA_DOWN', text="").direction = 'DOWN' # BFA - WIP - operator for GUI buttons to re-order in and out of groups

        col.separator()

        sub = col.column(align=True)
        sub.operator("grease_pencil.layer_isolate", icon="HIDE_OFF", text="").affect_visibility = True # BFA - added for v2 consistency
        sub.operator("grease_pencil.layer_isolate", icon="LOCKED", text="").affect_visibility = False # BFA - added for v2 consistency

        col.separator()

        if not is_layer_active:
            return

        layout.use_property_split = True
        layout.use_property_decorate = True
		# BFA - expose props to top level
        col = layout.column(align=True)
        col.use_property_split = False

        col.separator()

        col.prop(grease_pencil, "use_autolock_layers", text="Autolock Inactive Layers")

        if layer:
            col.prop(layer, "ignore_locked_materials")

        # Layer main properties
        row = layout.row(align=True)
        row.prop(layer, "blend_mode", text="Blend Mode")

        row = layout.row(align=True)
        row.prop(layer, "opacity", text="Opacity", slider=True)

        row = layout.row(align=True)
        row.use_property_split = False
        row.prop(layer, "use_lights", text="Lights")
        row.prop_decorator(layer, "use_lights")

    def draw(self, context):
        layout = self.layout
        grease_pencil = context.grease_pencil

        self.draw_settings(layout, grease_pencil)


class DATA_PT_grease_pencil_layer_masks(LayerDataButtonsPanel, GreasePencil_LayerMaskPanel, Panel):#
    bl_label = "Masks"
    bl_parent_id = "DATA_PT_grease_pencil_layers"
    bl_options = {'DEFAULT_CLOSED'}


class DATA_PT_grease_pencil_layer_transform(LayerDataButtonsPanel, GreasePencil_LayerTransformPanel, Panel):
    bl_label = "Transform"
    bl_parent_id = "DATA_PT_grease_pencil_layers"
    bl_options = {'DEFAULT_CLOSED'}


class DATA_PT_grease_pencil_layer_adjustments(LayerDataButtonsPanel, GreasePencil_LayerAdjustmentsPanel, Panel):
    bl_label = "Adjustments"
    bl_parent_id = "DATA_PT_grease_pencil_layers"
    bl_options = {'DEFAULT_CLOSED'}


class DATA_PT_grease_pencil_layer_relations(LayerDataButtonsPanel, GreasePencil_LayerRelationsPanel, Panel):
    bl_label = "Relations"
    bl_parent_id = "DATA_PT_grease_pencil_layers"
    bl_options = {'DEFAULT_CLOSED'}


class DATA_PT_grease_pencil_layer_display(LayerDataButtonsPanel, GreasePencil_LayerDisplayPanel, Panel):
    bl_label = "Display"
    bl_parent_id = "DATA_PT_grease_pencil_layers"
    bl_options = {'DEFAULT_CLOSED'}


class DATA_PT_grease_pencil_onion_skinning(DataButtonsPanel, Panel):
    bl_label = "Onion Skinning"

    def draw(self, context):
        grease_pencil = context.grease_pencil

        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(grease_pencil, "onion_mode")
        col.prop(grease_pencil, "onion_factor", text="Opacity", slider=True)
        col.prop(grease_pencil, "onion_keyframe_type")

        if grease_pencil.onion_mode == 'ABSOLUTE':
            col = layout.column(align=True)
            col.prop(grease_pencil, "ghost_before_range", text="Frames Before")
            col.prop(grease_pencil, "ghost_after_range", text="Frames After")
        elif grease_pencil.onion_mode == 'RELATIVE':
            col = layout.column(align=True)
            col.prop(grease_pencil, "ghost_before_range", text="Keyframes Before")
            col.prop(grease_pencil, "ghost_after_range", text="Keyframes After")


class DATA_PT_grease_pencil_onion_skinning_custom_colors(DataButtonsPanel, Panel):
    bl_parent_id = "DATA_PT_grease_pencil_onion_skinning"
    bl_label = "Custom Colors"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        grease_pencil = context.grease_pencil
        self.layout.prop(grease_pencil, "use_ghost_custom_colors", text="")

    def draw(self, context):
        grease_pencil = context.grease_pencil

        layout = self.layout
        layout.use_property_split = True
        layout.enabled = grease_pencil.users <= 1 and grease_pencil.use_ghost_custom_colors

        layout.prop(grease_pencil, "before_color", text="Before")
        layout.prop(grease_pencil, "after_color", text="After")


class DATA_PT_grease_pencil_onion_skinning_display(DataButtonsPanel, Panel):
    bl_parent_id = "DATA_PT_grease_pencil_onion_skinning"
    bl_label = "Display"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        grease_pencil = context.grease_pencil

        layout = self.layout
        layout.use_property_split = False
        # This was done in GPv2 but it's not entirely clear why. Presumably it was
        # to indicate that the settings will affect the onion skinning of the
        # other users.
        layout.enabled = grease_pencil.users <= 1

        col = layout.column(align=True)
        col.prop(grease_pencil, "use_onion_fade", text="Fade")
        sub = layout.column()
        sub.active = grease_pencil.onion_mode in {'RELATIVE', 'SELECTED'}
        sub.prop(grease_pencil, "use_onion_loop", text="Show Start Frame")


class DATA_PT_grease_pencil_settings(DataButtonsPanel, Panel):
    bl_label = "Settings"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        grease_pencil = context.grease_pencil
        col = layout.column(align=True)
        col.prop(grease_pencil, "stroke_depth_order", text="Stroke Depth Order")


class DATA_PT_grease_pencil_animation(DataButtonsPanel, PropertiesAnimationMixin, PropertyPanel, Panel):
    _animated_id_context_property = "grease_pencil"


class DATA_PT_grease_pencil_custom_props(DataButtonsPanel, PropertyPanel, Panel):
    _context_path = "object.data"
    _property_type = bpy.types.GreasePencilv3


class GREASE_PENCIL_UL_attributes(UIList):
    def filter_items(self, _context, data, property):
        attributes = getattr(data, property)
        flags = []
        indices = [i for i in range(len(attributes))]

        # Filtering by name
        if self.filter_name:
            flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, attributes, "name", reverse=self.use_filter_invert,
            )
        if not flags:
            flags = [self.bitflag_filter_item] * len(attributes)

        # Filtering internal attributes
        for idx, item in enumerate(attributes):
            flags[idx] = 0 if item.is_internal else flags[idx]

        # Reorder by name.
        if self.use_filter_sort_alpha:
            indices = bpy.types.UI_UL_list.sort_items_by_name(attributes, "name")

        return flags, indices

    def draw_item(self, _context, layout, _data, attribute, _icon, _active_data, _active_propname, _index):
        data_type = attribute.bl_rna.properties["data_type"].enum_items[attribute.data_type]

        split = layout.split(factor=0.50)
        split.emboss = 'NONE'
        split.prop(attribute, "name", text="")
        sub = split.row()
        sub.alignment = 'RIGHT'
        sub.active = False
        sub.label(text=data_type.name)

class DATA_PT_grease_pencil_attributes(DataButtonsPanel, Panel):
    bl_label = "Attributes"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        grease_pencil = context.grease_pencil

        layout = self.layout
        row = layout.row()

        col = row.column()
        col.template_list(
            "GREASE_PENCIL_UL_attributes",
            "attributes",
            grease_pencil,
            "attributes",
            grease_pencil.attributes,
            "active_index",
            rows=3,
        )

        col = row.column(align=True)
        col.operator("geometry.attribute_add", icon='ADD', text="")
        col.operator("geometry.attribute_remove", icon='REMOVE', text="")


## BFA - WIP - operator for GUI buttons to re-order items through groups - Start
class GREASE_PENCIL_OT_interface_item_move(DataButtonsPanel, Operator):
    '''Move the active layer to the specified direction\nYou can also alternatively drag and drop the active layer or group to reorder and change hierarchy'''
    bl_idname = "grease_pencil.interface_item_move"
    bl_label = "Move Item"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        description="Specifies which direction the active item is moved towards",
        items=(
            ('UP', "Move Up", ""),
            ('DOWN', "Move Down", "")
        ),
    )

    @classmethod
    def poll(cls, context):
        return context.grease_pencil is not None and context.grease_pencil.layers.active is not None

    def execute(self, context):
        grease_pencil = context.grease_pencil
        layers = grease_pencil.layers

        # The selected layer
        active_layer = layers.active

        # BFA - WIP
        # In theory the layer_groups are shown on a seperate indice, but names are ok.
        # We can detect the layer_parent by name, and do something like move_to_layer_group either to None (root) or name
        # We cannot detect if next in index is a layer_group or not yet.
        # Refer to node.py  NODE_OT_interface_item_move for info on how this could potentially work

        if self.direction == 'DOWN':
            # Move the active layer down
            layers.move(active_layer, 'DOWN')  # Move down normally
            self.report({'INFO'}, 'Layer moved down')

        elif self.direction == 'UP':
            layers.move(active_layer, 'UP')  # Move up normally
            self.report({'INFO'}, 'Layer moved up')

        return {'FINISHED'}

## BFA - operator for GUI buttons to re-order items - End


classes = (
    GREASE_PENCIL_UL_masks,
    GREASE_PENCIL_MT_layer_mask_add,
    DATA_PT_context_grease_pencil,
    DATA_PT_grease_pencil_layers,
    DATA_PT_grease_pencil_layer_masks,
    DATA_PT_grease_pencil_layer_transform,
    DATA_PT_grease_pencil_layer_adjustments,
    DATA_PT_grease_pencil_layer_relations,
    DATA_PT_grease_pencil_layer_display,
    DATA_PT_grease_pencil_onion_skinning,
    DATA_PT_grease_pencil_onion_skinning_custom_colors,
    DATA_PT_grease_pencil_onion_skinning_display,
    DATA_PT_grease_pencil_settings,
    DATA_PT_grease_pencil_custom_props,
    GREASE_PENCIL_MT_grease_pencil_add_layer_extra,
    GREASE_PENCIL_MT_group_context_menu,
    DATA_PT_grease_pencil_animation,
    GREASE_PENCIL_UL_attributes,
    DATA_PT_grease_pencil_attributes
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
