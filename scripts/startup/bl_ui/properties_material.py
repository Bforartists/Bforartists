# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Menu, Panel, UIList
from bpy.app.translations import contexts as i18n_contexts
from rna_prop_ui import PropertyPanel
from bpy_extras.node_utils import find_node_input


class MATERIAL_MT_context_menu(Menu):
    bl_label = "Material Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("material.copy", icon='COPYDOWN')
        layout.operator("object.material_slot_copy", icon='COPYDOWN')
        layout.operator("material.paste", icon='PASTEDOWN')
        layout.operator("object.material_slot_remove_unused", icon='DELETE')


class MATERIAL_UL_matslots(UIList):

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        # assert(isinstance(item, bpy.types.MaterialSlot)
        # ob = data
        slot = item
        ma = slot.material

        layout.context_pointer_set("id", ma)
        layout.context_pointer_set("material_slot", slot)

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class MaterialButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and (context.engine in cls.COMPAT_ENGINES) and not mat.grease_pencil


class MATERIAL_PT_preview(MaterialButtonsPanel, Panel):
    bl_label = "Preview"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_EEVEE'}

    def draw(self, context):
        self.layout.template_preview(context.material)


class MATERIAL_PT_custom_props(MaterialButtonsPanel, PropertyPanel, Panel):
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }
    _context_path = "material"
    _property_type = bpy.types.Material


class EEVEE_MATERIAL_PT_context_material(MaterialButtonsPanel, Panel):
    bl_label = ""
    bl_context = "material"
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        mat = context.material

        if (ob and ob.type == 'GPENCIL') or (mat and mat.grease_pencil):
            return False

        return (ob or mat) and (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        # bfa - no remove in edit mode
        obj = context.active_object
        object_mode = 'OBJECT' if obj is None else obj.mode

        if ob:
            is_sortable = len(ob.material_slots) > 1
            rows = 3
            if is_sortable:
                rows = 5

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")

            # bfa - no remove in edit mode
            sub = col.column()
            sub.active = (object_mode != 'EDIT')
            sub.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.separator()

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        row = layout.row()

        if ob:
            row.template_ID(ob, "active_material", new="material.new")

            if slot:
                icon_link = 'MESH_DATA' if slot.link == 'DATA' else 'OBJECT_DATA'
                row.prop(slot, "link", icon=icon_link, icon_only=True)

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        elif mat:
            row.template_ID(space, "pin_id")


def panel_node_draw(layout, ntree, _output_type, input_name):
    node = ntree.get_output_node('EEVEE')

    if node:
        input = find_node_input(node, input_name)
        if input:
            layout.template_node_view(ntree, node, input)
        else:
            layout.label(text="Incompatible output node")
    else:
        layout.label(text="No output node")


class EEVEE_MATERIAL_PT_surface(MaterialButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "material"
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}

    def draw(self, context):
        layout = self.layout

        mat = context.material

        if mat.use_nodes:
            layout.use_property_split = True
            panel_node_draw(layout, mat.node_tree, 'OUTPUT_MATERIAL', "Surface")
        else:
            layout.prop(mat, "use_nodes", icon='NODETREE')
            layout.use_property_split = True
            layout.prop(mat, "diffuse_color", text="Base Color")
            layout.prop(mat, "metallic")
            layout.prop(mat, "specular_intensity", text="Specular")
            layout.prop(mat, "roughness")


class EEVEE_MATERIAL_PT_volume(MaterialButtonsPanel, Panel):
    bl_label = "Volume"
    bl_translation_context = i18n_contexts.id_id
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        mat = context.material
        return mat and mat.use_nodes and (engine in cls.COMPAT_ENGINES) and not mat.grease_pencil

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        mat = context.material

        panel_node_draw(layout, mat.node_tree, 'OUTPUT_MATERIAL', "Volume")


class EEVEE_MATERIAL_PT_displacement(MaterialButtonsPanel, Panel):
    bl_label = "Displacement"
    bl_translation_context = i18n_contexts.id_id
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        mat = context.material
        return mat and mat.use_nodes and (engine in cls.COMPAT_ENGINES) and not mat.grease_pencil

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        mat = context.material

        panel_node_draw(layout, mat.node_tree, 'OUTPUT_MATERIAL', "Displacement")


class EEVEE_MATERIAL_PT_thickness(MaterialButtonsPanel, Panel):
    bl_label = "Thickness"
    bl_translation_context = i18n_contexts.id_id
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_EEVEE_NEXT'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        mat = context.material
        return mat and mat.use_nodes and (engine in cls.COMPAT_ENGINES) and not mat.grease_pencil

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        mat = context.material

        panel_node_draw(layout, mat.node_tree, 'OUTPUT_MATERIAL', "Thickness")


def draw_material_settings(self, context):
    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    mat = context.material

    layout.use_property_split = False
    layout.prop(mat, "use_backface_culling")
    layout.use_property_split = True

    layout.prop(mat, "blend_method")
    layout.prop(mat, "shadow_method")

    row = layout.row()
    if ((mat.blend_method == 'CLIP') or (mat.shadow_method == 'CLIP')):
        row.prop(mat, "alpha_threshold")

    if mat.blend_method not in {'OPAQUE', 'CLIP', 'HASHED'}:
        layout.use_property_split = False
        layout.prop(mat, "show_transparent_back")
        layout.use_property_split = True

    col = layout.column()

    subcol = col.column()
    subcol.use_property_split = False
    row = subcol.row()
    split = row.split(factor=0.55)
    split.prop(mat, "use_screen_refraction")
    if mat.use_screen_refraction:
        split.prop(mat, "refraction_depth", text="")
    else:
        split.label(icon='DISCLOSURE_TRI_RIGHT')

    subcol = col.column()
    subcol.use_property_split = False
    row = subcol.row()
    split = row.split(factor=0.55)
    split.prop(mat, "use_sss_translucency")
    if mat.use_sss_translucency:
        split.prop(mat, "pass_index", text="")
    else:
        split.label(icon='DISCLOSURE_TRI_RIGHT')


class EEVEE_MATERIAL_PT_settings(MaterialButtonsPanel, Panel):
    bl_label = "Settings"
    bl_context = "material"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}

    def draw(self, context):
        draw_material_settings(self, context)


class EEVEE_MATERIAL_PT_viewport_settings(MaterialButtonsPanel, Panel):
    bl_label = "Settings"
    bl_context = "material"
    bl_parent_id = "MATERIAL_PT_viewport"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        draw_material_settings(self, context)


class EEVEE_NEXT_MATERIAL_PT_settings(MaterialButtonsPanel, Panel):
    bl_label = "Settings"
    bl_context = "material"
    COMPAT_ENGINES = {'BLENDER_EEVEE_NEXT'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mat = context.material

        layout.prop(mat, "pass_index")


class EEVEE_NEXT_MATERIAL_PT_settings_surface(MaterialButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "material"
    bl_parent_id = "EEVEE_NEXT_MATERIAL_PT_settings"
    COMPAT_ENGINES = {'BLENDER_EEVEE_NEXT'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mat = context.material

        col = layout.column()
        col.label(text="Backface Culling")
        col.use_property_split = False
        row = col.row()
        row.separator()
        row.prop(mat, "use_backface_culling", text="Camera")
        row = col.row()
        row.separator()
        row.prop(mat, "use_backface_culling_shadow", text="Shadow")

        col = layout.column(align=True)
        col.prop(mat, "displacement_method", text="Displacement")
        col = col.column(align=True)
        col.enabled = mat.displacement_method != 'BUMP'
        col.prop(mat, "max_vertex_displacement", text="Max Distance")

        if mat.displacement_method == 'DISPLACEMENT':
            layout.label(text="Unsupported displacement method", icon='ERROR')

        layout.use_property_split = False
        layout.prop(mat, "use_transparent_shadow")
        layout.use_property_split = True

        col = layout.column()
        col.prop(mat, "surface_render_method", text="Render Method")
        col.use_property_split = False
        row = col.row()
        row.separator()
        if mat.surface_render_method == 'BLENDED':
            row.prop(mat, "show_transparent_back", text="Transparency Overlap")
        elif mat.surface_render_method == 'DITHERED':
            row.prop(mat, "use_screen_refraction", text="Raytraced Transmission")

        col = layout.column()
        col.use_property_split = False
        col.prop(mat, "thickness_mode", text="Thickness")
        if mat.surface_render_method == 'DITHERED':
            col.prop(mat, "use_thickness_from_shadow", text="From Shadow")

        col = layout.column()
        col.use_property_split = False
        col.label(text="Light Probe Volume")
        row = col.row()
        row.separator()
        row.prop(mat, "lightprobe_volume_single_sided", text="Single Sided")


class EEVEE_NEXT_MATERIAL_PT_settings_volume(MaterialButtonsPanel, Panel):
    bl_label = "Volume"
    bl_context = "material"
    bl_parent_id = "EEVEE_NEXT_MATERIAL_PT_settings"
    COMPAT_ENGINES = {'BLENDER_EEVEE_NEXT'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mat = context.material

        layout.prop(mat, "volume_intersection_method", text="Intersection")


class MATERIAL_PT_viewport(MaterialButtonsPanel, Panel):
    bl_label = "Viewport Display"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and not mat.grease_pencil

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        mat = context.material

        col = layout.column()
        col.prop(mat, "diffuse_color", text="Color")
        col.prop(mat, "metallic")
        col.prop(mat, "roughness")


class MATERIAL_PT_lineart(MaterialButtonsPanel, Panel):
    bl_label = "Line Art"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and not mat.grease_pencil

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        mat = context.material
        lineart = mat.lineart

        row = layout.row()
        split = row.split(factor=0.4)
        row = split.row()
        row.prop(lineart, "use_material_mask", text="Material Mask")
        row = split.row()
        if lineart.use_material_mask:
            row.label(icon='DISCLOSURE_TRI_DOWN')
        else:
            row.label(icon='DISCLOSURE_TRI_RIGHT')
        row = split.row()
        row.alignment = 'RIGHT'
        row.prop_decorator(lineart, "use_material_mask")

        layout.use_property_split = True

        col = layout.column(align=True)
        if lineart.use_material_mask:
            row = col.row(align=True, heading="      Masks")
            for i in range(8):
                row.prop(lineart, "use_material_mask_bits", text=str(i),
                         index=i, toggle=True)  # bfa - labels on the maks bits
                if i == 3:
                    row = col.row(align=True)

        row = layout.row(align=True, heading="Custom Occlusion")
        row.prop(lineart, "mat_occlusion", text="Levels")

        col = layout.column()
        split = col.split(factor=.4)
        split.use_property_split = False
        split.prop(lineart, "use_intersection_priority_override", text="Intersection Priority")

        split.alignment = 'LEFT'
        if lineart.use_intersection_priority_override:
            row = split.row()
            row.prop(lineart, "intersection_priority", text="")
            row.prop_decorator(lineart, "intersection_priority")
        else:
            split.label(icon='DISCLOSURE_TRI_RIGHT')


classes = (
    MATERIAL_MT_context_menu,
    MATERIAL_UL_matslots,
    MATERIAL_PT_preview,
    EEVEE_MATERIAL_PT_context_material,
    EEVEE_MATERIAL_PT_surface,
    EEVEE_MATERIAL_PT_volume,
    EEVEE_MATERIAL_PT_displacement,
    EEVEE_MATERIAL_PT_thickness,
    EEVEE_MATERIAL_PT_settings,
    EEVEE_NEXT_MATERIAL_PT_settings,
    EEVEE_NEXT_MATERIAL_PT_settings_surface,
    EEVEE_NEXT_MATERIAL_PT_settings_volume,
    MATERIAL_PT_lineart,
    MATERIAL_PT_viewport,
    EEVEE_MATERIAL_PT_viewport_settings,
    MATERIAL_PT_custom_props,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
