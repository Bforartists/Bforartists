# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel, Menu, Operator
from bl_ui.generic_column_menu import (
    GenericColumnMenu,
    fetch_op_data,
    InvokeMenuOperator,
)  # BFA


class ModifierButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
    bl_options = {'HIDE_HEADER'}


class ModifierAddMenu:
    MODIFIER_TYPES_TO_LABELS = {
        enum_it.identifier: enum_it.name
        for enum_it in bpy.types.Modifier.bl_rna.properties["type"].enum_items_static
    }
    MODIFIER_TYPES_TO_ICONS = {
        enum_it.identifier: enum_it.icon
        for enum_it in bpy.types.Modifier.bl_rna.properties["type"].enum_items_static
    }
    MODIFIER_TYPES_I18N_CONTEXT = bpy.types.Modifier.bl_rna.properties["type"].translation_context

    @classmethod
    def operator_modifier_add(cls, layout, mod_type):
        layout.operator(
            "object.modifier_add",
            text=cls.MODIFIER_TYPES_TO_LABELS[mod_type],
            # Although these are operators, the label actually comes from an (enum) property,
            # so the property's translation context must be used here.
            text_ctxt=cls.MODIFIER_TYPES_I18N_CONTEXT,
            icon=cls.MODIFIER_TYPES_TO_ICONS[mod_type],
        ).type = mod_type


# BFA - menu
class DATA_MT_modifiers_special(Menu):
    bl_label = "Modifiers Special"

    def draw(self, _context):
        active_object = bpy.context.active_object
        supported_types = {
            "MESH",
            "CURVE",
            "CURVES",
            "SURFACE",
            "FONT",
            "VOLUME",
            "GREASEPENCIL",
        }

        layout = self.layout

        # bfa - pastedown icon by purpose, it copies, then pastes the modifiers to the selected objects
        layout.operator(
            "object.modifiers_copy_to_selected",
            text="Copy Modifiers to Selected Objects",
            icon="PASTEDOWN",
        )

        layout.separator()

        layout.operator("object.modifiers_clear", icon="CLEAR")


class DATA_PT_modifiers(ModifierButtonsPanel, Panel):
    bl_label = "Modifiers"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    # BFA - changed to be columns
    def draw(self, context):
        layout = self.layout
        ob = context.object
        if not ob:
            return
        ob_type = ob.type
        geometry_nodes_supported = ob_type in {
            'MESH', 'CURVE', 'CURVES',
            'FONT', 'VOLUME', 'POINTCLOUD', 'GREASEPENCIL',
        }

        if geometry_nodes_supported:
            # BFA - changed to be columns
            flow = layout.grid_flow(
                row_major=True, columns=0, even_columns=True, even_rows=False
            )
            col1 = flow.column()
            col2 = flow.column()
            col1.operator("object.add_modifier_menu", icon="ADD")
            row = col2.row()
            row.operator("object.add_asset_modifier_menu", icon="ADD")
            row.menu("DATA_MT_modifiers_special", icon="DOWNARROW_HLT", text="")

        else:
            row = layout.row()
            row.operator("object.add_modifier_menu", icon="ADD")
            if geometry_nodes_supported:
                row.operator("object.add_asset_modifier_menu", icon="ADD")
            row.menu("DATA_MT_modifiers_special", icon="DOWNARROW_HLT", text="")

        layout.template_modifiers()


# BFA - Heavily modified to be a column menu
class OBJECT_MT_modifier_add(ModifierAddMenu, Menu):
    bl_label = ""
    bl_options = {'SEARCH_ON_KEY_PRESS'}
    search_header = "Modifier"

    @staticmethod
    def draw_menu_column(layout, menu, icon="NONE"):
        header = menu.bl_label
        menu_idname = menu.__name__

        col = layout.column()
        if layout.operator_context != "INVOKE_REGION_WIN":
            col.label(text=header, icon=icon)
            col.separator()
        col.menu_contents(menu_idname)

    def draw(self, context):
        layout = self.layout.row()
        ob_type = context.object.type

        if layout.operator_context == "INVOKE_REGION_WIN":
            layout.label(text=self.search_header)

        if ob_type in {"MESH"}:
            self.draw_menu_column(
                layout, menu=OBJECT_MT_modifier_add_normals
            )  # BFA - moved to the front, closer to where they originally were
        if ob_type in {
            "MESH",
            "CURVE",
            "CURVES",
            "FONT",
            "SURFACE",
            "LATTICE",
            "GREASEPENCIL",
            "POINTCLOUD",
        }:
            self.draw_menu_column(layout, menu=OBJECT_MT_modifier_add_edit)
        if ob_type in {"MESH", "CURVE", "FONT", "SURFACE", "VOLUME", "GREASEPENCIL"}:
            self.draw_menu_column(layout, menu=OBJECT_MT_modifier_add_generate)
        if ob_type in {
            "MESH",
            "CURVE",
            "FONT",
            "SURFACE",
            "LATTICE",
            "VOLUME",
            "GREASEPENCIL",
        }:
            self.draw_menu_column(layout, menu=OBJECT_MT_modifier_add_deform)
        if ob_type in {"MESH", "CURVE", "FONT", "SURFACE", "LATTICE"}:
            self.draw_menu_column(layout, menu=OBJECT_MT_modifier_add_physics)
        if ob_type in {"GREASEPENCIL"}:
            self.draw_menu_column(layout, menu=OBJECT_MT_modifier_add_color)


# BFA - moved to another button menu below
# if geometry_nodes_supported:
#    layout.menu_contents("OBJECT_MT_modifier_add_root_catalogs")


class OBJECT_MT_modifier_add_edit(ModifierAddMenu, Menu):
    bl_label = "Edit"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'DATA_TRANSFER')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'MESH_CACHE')
        if ob_type in {'MESH', 'CURVE', 'CURVES', 'FONT', 'POINTCLOUD'}:
            self.operator_modifier_add(layout, 'MESH_SEQUENCE_CACHE')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'UV_PROJECT')
            self.operator_modifier_add(layout, 'UV_WARP')
            self.operator_modifier_add(layout, 'VERTEX_WEIGHT_EDIT')
            self.operator_modifier_add(layout, 'VERTEX_WEIGHT_MIX')
            self.operator_modifier_add(layout, 'VERTEX_WEIGHT_PROXIMITY')
        if ob_type == 'GREASEPENCIL':
            self.operator_modifier_add(layout, 'GREASE_PENCIL_TEXTURE')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_TIME')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_VERTEX_WEIGHT_PROXIMITY')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_VERTEX_WEIGHT_ANGLE')
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_generate(ModifierAddMenu, Menu):
    bl_label = "Generate"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'ARRAY')
            self.operator_modifier_add(layout, 'BEVEL')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'BOOLEAN')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'BUILD')
            self.operator_modifier_add(layout, 'DECIMATE')
            self.operator_modifier_add(layout, 'EDGE_SPLIT')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'MASK')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'MIRROR')
        if ob_type == 'VOLUME':
            self.operator_modifier_add(layout, 'MESH_TO_VOLUME')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'MULTIRES')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'REMESH')
            self.operator_modifier_add(layout, 'SCREW')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'SKIN')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'SOLIDIFY')
            self.operator_modifier_add(layout, 'SUBSURF')
            self.operator_modifier_add(layout, 'TRIANGULATE')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'VOLUME_TO_MESH')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'WELD')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'WIREFRAME')
        if ob_type == 'GREASEPENCIL':
            self.operator_modifier_add(layout, 'GREASE_PENCIL_ARRAY')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_BUILD')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_DASH')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_ENVELOPE')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_LENGTH')
            self.operator_modifier_add(layout, 'LINEART')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_MIRROR')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_MULTIPLY')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_OUTLINE')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_SIMPLIFY')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_SUBDIV')
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_deform(ModifierAddMenu, Menu):
    bl_label = "Deform"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'ARMATURE')
            self.operator_modifier_add(layout, 'CAST')
            self.operator_modifier_add(layout, 'CURVE')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'DISPLACE')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'HOOK')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'LAPLACIANDEFORM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'LATTICE')
            self.operator_modifier_add(layout, 'MESH_DEFORM')
            self.operator_modifier_add(layout, 'SHRINKWRAP')
            self.operator_modifier_add(layout, 'SIMPLE_DEFORM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
            self.operator_modifier_add(layout, 'SMOOTH')
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'CORRECTIVE_SMOOTH')
            self.operator_modifier_add(layout, 'LAPLACIANSMOOTH')
            self.operator_modifier_add(layout, 'SURFACE_DEFORM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'WARP')
            self.operator_modifier_add(layout, 'WAVE')
        if ob_type == 'VOLUME':
            self.operator_modifier_add(layout, 'VOLUME_DISPLACE')
        if ob_type == 'GREASEPENCIL':
            self.operator_modifier_add(layout, 'GREASE_PENCIL_ARMATURE')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_HOOK')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_LATTICE')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_NOISE')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_OFFSET')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_SHRINKWRAP')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_SMOOTH')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_THICKNESS')
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_normals(ModifierAddMenu, Menu):
    bl_label = "Normals"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'NORMAL_EDIT')
            self.operator_modifier_add(layout, 'WEIGHTED_NORMAL')
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_physics(ModifierAddMenu, Menu):
    bl_label = "Physics"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        if ob_type == 'MESH':
            self.operator_modifier_add(layout, 'CLOTH')
            self.operator_modifier_add(layout, 'COLLISION')
            self.operator_modifier_add(layout, 'DYNAMIC_PAINT')
            self.operator_modifier_add(layout, 'EXPLODE')
            self.operator_modifier_add(layout, 'FLUID')
            self.operator_modifier_add(layout, 'OCEAN')
            self.operator_modifier_add(layout, 'PARTICLE_INSTANCE')
            self.operator_modifier_add(layout, 'PARTICLE_SYSTEM')
        if ob_type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'LATTICE'}:
            self.operator_modifier_add(layout, 'SOFT_BODY')
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


class OBJECT_MT_modifier_add_color(ModifierAddMenu, Menu):
    bl_label = "Color"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        if ob_type == 'GREASEPENCIL':
            self.operator_modifier_add(layout, 'GREASE_PENCIL_COLOR')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_OPACITY')
            self.operator_modifier_add(layout, 'GREASE_PENCIL_TINT')
        layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


# BFA - Modifier Assets
class OBJECT_MT_modifier_add_assets(ModifierAddMenu, Menu):
    bl_label = "Assets"
    bl_description = (
        "Add a modifier nodegroup to all selected objects"  # BFA - inversed
    )
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        ob_type = context.object.type
        geometry_nodes_supported = ob_type in {
            'MESH',
            'CURVE',
            'CURVES',
            'FONT',
            'VOLUME',
            'POINTCLOUD',
            'GREASEPENCIL',
        }

        if layout.operator_context == 'EXEC_REGION_WIN':
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator(
                "wm.search_single_menu", text="Search...", icon="VIEWZOOM"
            ).menu_idname = self.bl_idname
            layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'

        layout.separator()
        self.operator_modifier_add(layout, "NODES")
        layout.separator()

        if ob_type in {'GREASEPENCIL'}:
            layout.menu("OBJECT_MT_modifier_add_color_assets")

        layout.separator()
        if geometry_nodes_supported:
            layout.menu_contents("OBJECT_MT_modifier_add_root_catalogs")


# BFA - Modifier Assets
class AssetSubmenu:
    def draw(self, context):
        self.layout.template_modifier_asset_menu_items(catalog_path=self.bl_label)


# BFA - Modifier Assets
class OBJECT_MT_modifier_add_edit_assets(AssetSubmenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_edit.bl_label


# BFA - Modifier Assets
class OBJECT_MT_modifier_add_generate_assets(AssetSubmenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_generate.bl_label


# BFA - Modifier Assets
class OBJECT_MT_modifier_add_deform_assets(AssetSubmenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_deform.bl_label


# BFA - Modifier Assets
class OBJECT_MT_modifier_add_physics_assets(AssetSubmenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_physics.bl_label


# BFA - Modifier Assets
class OBJECT_MT_modifier_add_color_assets(AssetSubmenu, ModifierAddMenu, Menu):
    bl_label = OBJECT_MT_modifier_add_color.bl_label


# BFA - Modifier Assets
class OBJECT_OT_add_asset_modifier_menu(InvokeMenuOperator, Operator):
    bl_idname = "object.add_asset_modifier_menu"
    bl_label = "Add Asset Modifier"
    bl_description = (
        "Add a modifier nodegroup to all selected objects"  # BFA - inversed
    )
    menu_id = "OBJECT_MT_modifier_add_assets"
    space_type = 'PROPERTIES'
    space_context = 'MODIFIER'


class DATA_PT_gpencil_modifiers(ModifierButtonsPanel, Panel):
    bl_label = "Modifiers"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'

    def draw(self, _context):
        layout = self.layout
        layout.operator(
            "object.add_gpencil_modifier_menu", text="Add Modifier", icon="ADD"
        )  # BFA icon
        layout.template_grease_pencil_modifiers()


# BFA - Grease Pencil Modifier add menu
class OBJECT_MT_gpencil_modifier_add(GenericColumnMenu, Menu):
    bl_description = (
        "Add a procedural operation/effect to the active grease pencil object"
    )

    op_id = "object.gpencil_modifier_add"
    # OPERATOR_DATA, TRANSLATION_CONTEXT = fetch_op_data(class_name="GpencilModifier")
    search_header = "Grease Pencil Modifier"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'

    def draw(self, _context):
        layout = self.layout.row()

        self.draw_operator_column(
            layout,
            header="Modify",
            types=('GP_TEXTURE', 'GP_TIME', 'GP_WEIGHT_ANGLE', 'GP_WEIGHT_PROXIMITY'),
        )
        self.draw_operator_column(
            layout,
            header="Generate",
            types=(
                'GP_ARRAY',
                'GP_BUILD',
                'GP_DASH',
                'GP_ENVELOPE',
                'GP_LENGTH',
                'GP_LINEART',
                'GP_MIRROR',
                'GP_MULTIPLY',
                'GP_OUTLINE',
                'GP_SIMPLIFY',
                'GP_SUBDIV',
            ),
        )
        self.draw_operator_column(
            layout,
            header="Deform",
            types=(
                'GP_ARMATURE',
                'GP_HOOK',
                'GP_LATTICE',
                'GP_NOISE',
                'GP_OFFSET',
                'SHRINKWRAP',
                'GP_SMOOTH',
                'GP_THICK',
            ),
        )
        self.draw_operator_column(
            layout, header="Color", types=('GP_COLOR', 'GP_OPACITY', 'GP_TINT')
        )


class OBJECT_OT_add_gpencil_modifier_menu(InvokeMenuOperator, Operator):
    bl_idname = "object.add_gpencil_modifier_menu"
    bl_label = "Add Grease Pencil Modifier"
    bl_description = (
        "Add a procedural operation/effect to the active grease pencil object"
    )

    menu_id = "OBJECT_MT_gpencil_modifier_add"
    space_type = 'PROPERTIES'
    space_context = 'MODIFIER'


# BFA - floating menu for consistency
class AddModifierMenu(Operator):
    bl_idname = "object.add_modifier_menu"
    bl_label = "Add Modifier"
    bl_description = "Add a procedural operation/effect to all selected objects"  # BFA - defaults to all

    @classmethod
    def poll(cls, context):
        # NOTE: This operator only exists to add a poll to the add modifier shortcut in the property editor.
        space = context.space_data
        return space and space.type == 'PROPERTIES' and space.context == 'MODIFIER'

    def invoke(self, _context, _event):
        return bpy.ops.wm.call_menu(name="OBJECT_MT_modifier_add")


classes = (
    DATA_PT_modifiers,
    DATA_MT_modifiers_special,  # bfa - former VIEW3D_MT_object_modifiers menu from the object menu
    OBJECT_MT_modifier_add,
    OBJECT_MT_modifier_add_edit,
    OBJECT_MT_modifier_add_generate,
    OBJECT_MT_modifier_add_deform,
    OBJECT_MT_modifier_add_normals,
    OBJECT_MT_modifier_add_physics,
    OBJECT_MT_modifier_add_color,
    OBJECT_MT_modifier_add_assets,  # BFA
    OBJECT_MT_modifier_add_color_assets,  # BFA
    OBJECT_OT_add_asset_modifier_menu,  # BFA
    DATA_PT_gpencil_modifiers,
    OBJECT_MT_gpencil_modifier_add,  # BFA
    OBJECT_OT_add_gpencil_modifier_menu,  # BFA
    AddModifierMenu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
