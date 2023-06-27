# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""User interface for texturing tools."""

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import (
    Operator,
    Menu,
    UIList,
    Panel,
    Brush,
    Material,
    Light,
    World,
    ParticleSettings,
    FreestyleLineStyle,
)

# from .ui import TextureButtonsPanel

from .shading_properties import pov_context_tex_datablock
from bl_ui.properties_paint_common import brush_texture_settings

# Example of wrapping every class 'as is'
from bl_ui import properties_texture

# unused, replaced by pov_context_tex_datablock (no way to use?):
# from bl_ui.properties_texture import context_tex_datablock
# from bl_ui.properties_texture import texture_filter_common #unused yet?

for member in dir(properties_texture):
    subclass = getattr(properties_texture, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_texture


class TextureButtonsPanel:
    """Use this class to define buttons from the texture tab properties."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "texture"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        tex = context.texture
        rd = context.scene.render
        return tex and (rd.engine in cls.COMPAT_ENGINES)


class TEXTURE_MT_POV_specials(Menu):
    """Use this class to define pov texture slot operations buttons."""

    bl_label = "Texture Specials"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        layout.operator("texture.slot_copy", icon="COPYDOWN")
        layout.operator("texture.slot_paste", icon="PASTEDOWN")


class WORLD_TEXTURE_SLOTS_UL_POV_layerlist(UIList):
    """Use this class to show pov texture slots list."""

    index: bpy.props.IntProperty(name="index")
    # should active_propname be index or..?

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # world = context.scene.world  # .pov  # NOT USED
        # active_data = world.pov # NOT USED
        # tex = context.texture #may be needed later?

        # We could write some code to decide which icon to use here...
        # custom_icon = 'TEXTURE'

        # ob = data
        slot = item
        # ma = slot.name
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # You should always start your row layout by a label (icon + text), or a non-embossed text field,
            # this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            # Note "data" names should never be translated!
            if slot:
                layout.prop(slot, "texture", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="New", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class MATERIAL_TEXTURE_SLOTS_UL_POV_layerlist(UIList):
    """Use this class to show pov texture slots list."""

    #    texture_slots:
    index: bpy.props.IntProperty(name="index")
    # foo  = random prop

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # ob = data
        slot = item
        # ma = slot.name
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # You should always start your row layout by a label (icon + text), or a non-embossed text field,
            # this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            # Note "data" names should never be translated!
            if slot:
                layout.prop(slot, "texture", text="", emboss=False, icon="TEXTURE")
            else:
                layout.label(text="New", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class TEXTURE_PT_context(TextureButtonsPanel, Panel):
    """Rewrite of this existing class to modify it."""

    bl_label = ""
    bl_context = "texture"
    bl_options = {"HIDE_HEADER"}
    COMPAT_ENGINES = {"POVRAY_RENDER", "BLENDER_EEVEE", "BLENDER_WORKBENCH"}
    # register but not unregistered because
    # the modified parts concern only POVRAY_RENDER

    @classmethod
    def poll(cls, context):
        return (
            context.scene.texture_context
            not in ("MATERIAL", "WORLD", "LIGHT", "PARTICLES", "LINESTYLE")
            or context.scene.render.engine != "POVRAY_RENDER"
        )

    def draw(self, context):
        layout = self.layout
        tex = context.texture
        space = context.space_data
        pin_id = space.pin_id
        use_pin_id = space.use_pin_id
        user = context.texture_user

        col = layout.column()

        if not (use_pin_id and isinstance(pin_id, bpy.types.Texture)):
            pin_id = None

        if not pin_id:
            col.template_texture_user()

        if user or pin_id:
            col.separator()

            if pin_id:
                col.template_ID(space, "pin_id")
            else:
                propname = context.texture_user_property.identifier
                col.template_ID(user, propname, new="texture.new")

            if tex:
                col.separator()

                split = col.split(factor=0.2)
                split.label(text="Type")
                split.prop(tex, "type", text="")


class TEXTURE_PT_POV_context_texture(TextureButtonsPanel, Panel):
    """Use this class to show pov texture context buttons."""

    bl_label = ""
    bl_options = {"HIDE_HEADER"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        # if not (hasattr(context, "pov_texture_slot") or hasattr(context, "texture_node")):
        #     return False
        return (
            context.material
            or context.scene.world
            or context.light
            or context.texture
            or context.line_style
            or context.particle_system
            or isinstance(context.space_data.pin_id, ParticleSettings)
            or context.texture_user
        ) and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mat = context.view_layer.objects.active.active_material
        wld = context.scene.world

        layout.prop(scene, "texture_context", expand=True)
        if scene.texture_context == "MATERIAL" and mat is not None:

            row = layout.row()
            row.template_list(
                "MATERIAL_TEXTURE_SLOTS_UL_POV_layerlist",
                "",
                mat,
                "pov_texture_slots",
                mat.pov,
                "active_texture_index",
                rows=2,
                maxrows=16,
                type="DEFAULT",
            )
            col = row.column(align=True)
            col.operator("pov.textureslotadd", icon="ADD", text="")
            col.operator("pov.textureslotremove", icon="REMOVE", text="")
            # XXX todo: recreate for pov_texture_slots?
            # col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
            # col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
            col.separator()

            if mat.pov_texture_slots:
                index = mat.pov.active_texture_index
                slot = mat.pov_texture_slots[index]
                try:
                    povtex = slot.texture  # slot.name
                    tex = bpy.data.textures[povtex]
                    col.prop(tex, "use_fake_user", text="")
                    # layout.label(text='Linked Texture data browser:')
                    # propname = slot.texture_search
                    # if slot.texture was a pointer to texture data rather than just a name string:
                    # layout.template_ID(povtex, "texture", new="texture.new")
                except KeyError:
                    tex = None
                row = layout.row(align=True)
                row.prop_search(
                    slot, "texture_search", bpy.data, "textures", text="", icon="TEXTURE"
                )

                row.operator("pov.textureslotupdate", icon="FILE_REFRESH", text="")
                # try:
                #     bpy.context.tool_settings.image_paint.brush.texture = bpy.data.textures[
                #         slot.texture_search
                #     ]
                #     bpy.context.tool_settings.image_paint.brush.mask_texture = bpy.data.textures[
                #         slot.texture_search
                #     ]
                # except KeyError:
                #     # texture not hand-linked by user
                #     pass

                if tex:
                    layout.separator()
                    split = layout.split(factor=0.2)
                    split.label(text="Type")
                    split.prop(tex, "type", text="")

            # else:
            # for i in range(18):  # length of material texture slots
            # mat.pov_texture_slots.add()
        elif scene.texture_context == "WORLD" and wld is not None:

            row = layout.row()
            row.template_list(
                "WORLD_TEXTURE_SLOTS_UL_POV_layerlist",
                "",
                wld,
                "pov_texture_slots",
                wld.pov,
                "active_texture_index",
                rows=2,
                maxrows=16,
                type="DEFAULT",
            )
            col = row.column(align=True)
            col.operator("pov.textureslotadd", icon="ADD", text="")
            col.operator("pov.textureslotremove", icon="REMOVE", text="")

            # todo: recreate for pov_texture_slots?
            # col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
            # col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
            col.separator()

            if wld.pov_texture_slots:
                index = wld.pov.active_texture_index
                slot = wld.pov_texture_slots[index]
                povtex = slot.texture  # slot.name
                tex = bpy.data.textures[povtex]
                col.prop(tex, "use_fake_user", text="")
                # layout.label(text='Linked Texture data browser:')
                # propname = slot.texture_search # NOT USED
                # if slot.texture was a pointer to texture data rather than just a name string:
                # layout.template_ID(povtex, "texture", new="texture.new")

                layout.prop_search(
                    slot, "texture_search", bpy.data, "textures", text="", icon="TEXTURE"
                )
                try:
                    bpy.context.tool_settings.image_paint.brush.texture = bpy.data.textures[
                        slot.texture_search
                    ]
                    bpy.context.tool_settings.image_paint.brush.mask_texture = bpy.data.textures[
                        slot.texture_search
                    ]
                except KeyError:
                    # texture not hand-linked by user
                    pass

                if tex:
                    layout.separator()
                    split = layout.split(factor=0.2)
                    split.label(text="Type")
                    split.prop(tex, "type", text="")


class TEXTURE_OT_POV_context_texture_update(Operator):
    """Use this class for the texture slot update button."""

    bl_idname = "pov.textureslotupdate"
    bl_label = "Update"
    bl_description = "Update texture_slot"
    bl_options = {"REGISTER", "UNDO"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mate = context.view_layer.objects.active.active_material
        return mate and engine in cls.COMPAT_ENGINES

    def execute(self, context):
        # tex.use_fake_user = True
        mat = context.view_layer.objects.active.active_material
        index = mat.pov.active_texture_index
        slot = mat.pov_texture_slots[index]
        povtex = slot.texture  # slot.name
        tex = bpy.data.textures[povtex]

        # Switch paint brush and paint brush mask
        # to this texture so settings remain contextual
        bpy.context.tool_settings.image_paint.brush.texture = bpy.data.textures[slot.texture_search]
        bpy.context.tool_settings.image_paint.brush.mask_texture = bpy.data.textures[
            slot.texture_search
        ]

        return {"FINISHED"}


# Commented out below is a reminder of what existed in Blender Internal
# attributes need to be recreated
"""
        slot = getattr(context, "texture_slot", None)
        node = getattr(context, "texture_node", None)
        space = context.space_data

        #attempt at replacing removed space_data
        mtl = getattr(context, "material", None)
        if mtl != None:
            spacedependant = mtl
        wld = getattr(context, "world", None)
        if wld != None:
            spacedependant = wld
        lgt = getattr(context, "light", None)
        if lgt != None:
            spacedependant = lgt


        #idblock = context.particle_system.settings

        tex = getattr(context, "texture", None)
        if tex != None:
            spacedependant = tex



        scene = context.scene
        idblock = scene.pov#pov_context_tex_datablock(context)
        pin_id = space.pin_id

        #spacedependant.use_limited_texture_context = True

        if space.use_pin_id and not isinstance(pin_id, Texture):
            idblock = id_tex_datablock(pin_id)
            pin_id = None

        if not space.use_pin_id:
            layout.row().prop(spacedependant, "texture_context", expand=True)
            pin_id = None

        if spacedependant.texture_context == 'OTHER':
            if not pin_id:
                layout.template_texture_user()
            user = context.texture_user
            if user or pin_id:
                layout.separator()

                row = layout.row()

                if pin_id:
                    row.template_ID(space, "pin_id")
                else:
                    propname = context.texture_user_property.identifier
                    row.template_ID(user, propname, new="texture.new")

                if tex:
                    split = layout.split(factor=0.2)
                    if tex.use_nodes:
                        if slot:
                            split.label(text="Output:")
                            split.prop(slot, "output_node", text="")
                    else:
                        split.label(text="Type:")
                        split.prop(tex, "type", text="")
            return

        tex_collection = (pin_id is None) and (node is None) and (spacedependant.texture_context not in ('LINESTYLE','OTHER'))

        if tex_collection:

            pov = getattr(context, "pov", None)
            active_texture_index = getattr(spacedependant, "active_texture_index", None)
            print (pov)
            print(idblock)
            print(active_texture_index)
            row = layout.row()

            row.template_list("TEXTURE_UL_texslots", "", idblock, "texture_slots",
                              idblock, "active_texture_index", rows=2, maxrows=16, type="DEFAULT")

            # row.template_list("WORLD_TEXTURE_SLOTS_UL_List", "texture_slots", world,
                              # world.texture_slots, world, "active_texture_index", rows=2)

            col = row.column(align=True)
            col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
            col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
            col.menu("TEXTURE_MT_POV_specials", icon='DOWNARROW_HLT', text="")

        if tex_collection:
            layout.template_ID(idblock, "active_texture", new="texture.new")
        elif node:
            layout.template_ID(node, "texture", new="texture.new")
        elif idblock:
            layout.template_ID(idblock, "texture", new="texture.new")

        if pin_id:
            layout.template_ID(space, "pin_id")

        if tex:
            split = layout.split(factor=0.2)
            if tex.use_nodes:
                if slot:
                    split.label(text="Output:")
                    split.prop(slot, "output_node", text="")
            else:
                split.label(text="Type:")
"""


class TEXTURE_PT_colors(TextureButtonsPanel, Panel):
    """Use this class to show pov color ramps."""

    bl_label = "Colors"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        tex = context.texture

        layout.prop(tex, "use_color_ramp", text="Ramp")
        if tex.use_color_ramp:
            layout.template_color_ramp(tex, "color_ramp", expand=True)

        split = layout.split()

        col = split.column()
        col.label(text="RGB Multiply:")
        sub = col.column(align=True)
        sub.prop(tex, "factor_red", text="R")
        sub.prop(tex, "factor_green", text="G")
        sub.prop(tex, "factor_blue", text="B")

        col = split.column()
        col.label(text="Adjust:")
        col.prop(tex, "intensity")
        col.prop(tex, "contrast")
        col.prop(tex, "saturation")

        col = layout.column()
        col.prop(tex, "use_clamp", text="Clamp")


# Texture Slot Panels #


class TEXTURE_OT_POV_texture_slot_add(Operator):
    """Use this class for the add texture slot button."""

    bl_idname = "pov.textureslotadd"
    bl_label = "Add"
    bl_description = "Add texture_slot"
    bl_options = {"REGISTER", "UNDO"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def execute(self, context):
        idblock = pov_context_tex_datablock(context)
        slot_brush = bpy.data.brushes.new("POVtextureSlot")
        context.tool_settings.image_paint.brush = slot_brush
        tex = bpy.data.textures.new(name="Texture", type="IMAGE")
        # tex.use_fake_user = True
        # mat = context.view_layer.objects.active.active_material
        slot = idblock.pov_texture_slots.add()
        slot.name = tex.name
        slot.texture = tex.name
        slot.texture_search = tex.name
        # Switch paint brush and paint brush mask
        # to this texture so settings remain contextual
        bpy.context.tool_settings.image_paint.brush.texture = tex
        bpy.context.tool_settings.image_paint.brush.mask_texture = tex
        idblock.pov.active_texture_index = len(idblock.pov_texture_slots) - 1

        # for area in bpy.context.screen.areas:
        # if area.type in ['PROPERTIES']:
        # area.tag_redraw()

        return {"FINISHED"}


class TEXTURE_OT_POV_texture_slot_remove(Operator):
    """Use this class for the remove texture slot button."""

    bl_idname = "pov.textureslotremove"
    bl_label = "Remove"
    bl_description = "Remove texture_slot"
    bl_options = {"REGISTER", "UNDO"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def execute(self, context):
        idblock = pov_context_tex_datablock(context)
        # mat = context.view_layer.objects.active.active_material
        # tex_slot = idblock.pov_texture_slots.remove(idblock.pov.active_texture_index) # not used
        # tex_to_delete = context.tool_settings.image_paint.brush.texture
        # bpy.data.textures.remove(tex_to_delete, do_unlink=True, do_id_user=True, do_ui_user=True)
        idblock.pov_texture_slots.remove(idblock.pov.active_texture_index)
        if idblock.pov.active_texture_index > 0:
            idblock.pov.active_texture_index -= 1
            # try:
            # tex = idblock.pov_texture_slots[idblock.pov.active_texture_index].texture
            # except IndexError:
            # No more slots
            return {"FINISHED"}
        # Switch paint brush to previous texture so settings remain contextual
        # if 'tex' in locals(): # Would test is the tex variable is assigned / exists
        # bpy.context.tool_settings.image_paint.brush.texture = bpy.data.textures[tex]
        # bpy.context.tool_settings.image_paint.brush.mask_texture = bpy.data.textures[tex]

        return {"FINISHED"}


class TextureSlotPanel(TextureButtonsPanel):
    """Use this class to show pov texture slots panel."""

    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "pov_texture_slot"):
            return False

        engine = context.scene.render.engine
        # return TextureButtonsPanel.poll(cls, context) and (engine in cls.COMPAT_ENGINES)
        return TextureButtonsPanel.poll(context) and (engine in cls.COMPAT_ENGINES)


class TEXTURE_PT_POV_type(TextureButtonsPanel, Panel):
    """Use this class to define pov texture type buttons."""

    bl_label = "POV Textures"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout
        # world = context.world # unused
        tex = context.texture

        split = layout.split(factor=0.2)
        split.label(text="Pattern")
        split.prop(tex.pov, "tex_pattern_type", text="")

        # row = layout.row()
        # row.template_list("WORLD_TEXTURE_SLOTS_UL_List", "texture_slots", world,
        # world.texture_slots, world, "active_texture_index")


class TEXTURE_PT_POV_preview(TextureButtonsPanel, Panel):
    """Use this class to define pov texture preview panel."""

    bl_label = "Preview"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if not hasattr(context, "pov_texture_slot"):
            return False
        tex = context.texture
        # mat = bpy.context.active_object.active_material #unused
        return tex and (tex.pov.tex_pattern_type != "emulator") and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        tex = context.texture
        slot = getattr(context, "pov_texture_slot", None)
        # idblock = pov_context_tex_datablock(context) # unused
        layout = self.layout
        # if idblock:
        # layout.template_preview(tex, parent=idblock, slot=slot)
        if tex.pov.tex_pattern_type != "emulator":
            layout.operator("tex.preview_update")
        else:
            layout.template_preview(tex, slot=slot)


class TEXTURE_PT_POV_parameters(TextureButtonsPanel, Panel):
    """Use this class to define pov texture pattern buttons."""

    bl_label = "POV Pattern Options"
    bl_options = {"HIDE_HEADER"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        # mat = bpy.context.active_object.active_material # Unused
        tex = context.texture
        if tex is not None and tex.pov.tex_pattern_type != "emulator":
            layout = self.layout
            if tex.pov.tex_pattern_type == "agate":
                layout.prop(tex.pov, "modifier_turbulence", text="Agate Turbulence")
            if tex.pov.tex_pattern_type in {"spiral1", "spiral2"}:
                layout.prop(tex.pov, "modifier_numbers", text="Number of arms")
            if tex.pov.tex_pattern_type == "tiling":
                layout.prop(tex.pov, "modifier_numbers", text="Pattern number")
            if tex.pov.tex_pattern_type == "magnet":
                layout.prop(tex.pov, "magnet_style", text="Magnet style")
            align = True
            if tex.pov.tex_pattern_type == "quilted":
                row = layout.row(align=align)
                row.prop(tex.pov, "modifier_control0", text="Control0")
                row.prop(tex.pov, "modifier_control1", text="Control1")
            if tex.pov.tex_pattern_type == "brick":
                col = layout.column(align=align)
                row = col.row()
                row.prop(tex.pov, "brick_size_x", text="Brick size X")
                row.prop(tex.pov, "brick_size_y", text="Brick size Y")
                row = col.row()
                row.prop(tex.pov, "brick_size_z", text="Brick size Z")
                row.prop(tex.pov, "brick_mortar", text="Brick mortar")
            if tex.pov.tex_pattern_type in {"julia", "mandel", "magnet"}:
                col = layout.column(align=align)
                if tex.pov.tex_pattern_type == "julia":
                    row = col.row()
                    row.prop(tex.pov, "julia_complex_1", text="Complex 1")
                    row.prop(tex.pov, "julia_complex_2", text="Complex 2")
                if tex.pov.tex_pattern_type == "magnet" and tex.pov.magnet_style == "julia":
                    row = col.row()
                    row.prop(tex.pov, "julia_complex_1", text="Complex 1")
                    row.prop(tex.pov, "julia_complex_2", text="Complex 2")
                row = col.row()
                if tex.pov.tex_pattern_type in {"julia", "mandel"}:
                    row.prop(tex.pov, "f_exponent", text="Exponent")
                if tex.pov.tex_pattern_type == "magnet":
                    row.prop(tex.pov, "magnet_type", text="Type")
                row.prop(tex.pov, "f_iter", text="Iterations")
                row = col.row()
                row.prop(tex.pov, "f_ior", text="Interior")
                row.prop(tex.pov, "f_ior_fac", text="Factor I")
                row = col.row()
                row.prop(tex.pov, "f_eor", text="Exterior")
                row.prop(tex.pov, "f_eor_fac", text="Factor E")
            if tex.pov.tex_pattern_type == "gradient":
                layout.label(text="Gradient orientation:")
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.prop(tex.pov, "grad_orient_x", text="X")
                column_flow.prop(tex.pov, "grad_orient_y", text="Y")
                column_flow.prop(tex.pov, "grad_orient_z", text="Z")
            if tex.pov.tex_pattern_type == "pavement":
                layout.prop(tex.pov, "pave_sides", text="Pavement:number of sides")
                col = layout.column(align=align)
                column_flow = col.column_flow(columns=3, align=True)
                column_flow.prop(tex.pov, "pave_tiles", text="Tiles")
                if tex.pov.pave_sides == "4" and tex.pov.pave_tiles == 6:
                    column_flow.prop(tex.pov, "pave_pat_35", text="Pattern")
                if tex.pov.pave_sides == "6" and tex.pov.pave_tiles == 5:
                    column_flow.prop(tex.pov, "pave_pat_22", text="Pattern")
                if tex.pov.pave_sides == "4" and tex.pov.pave_tiles == 5:
                    column_flow.prop(tex.pov, "pave_pat_12", text="Pattern")
                if tex.pov.pave_sides == "3" and tex.pov.pave_tiles == 6:
                    column_flow.prop(tex.pov, "pave_pat_12", text="Pattern")
                if tex.pov.pave_sides == "6" and tex.pov.pave_tiles == 4:
                    column_flow.prop(tex.pov, "pave_pat_7", text="Pattern")
                if tex.pov.pave_sides == "4" and tex.pov.pave_tiles == 4:
                    column_flow.prop(tex.pov, "pave_pat_5", text="Pattern")
                if tex.pov.pave_sides == "3" and tex.pov.pave_tiles == 5:
                    column_flow.prop(tex.pov, "pave_pat_4", text="Pattern")
                if tex.pov.pave_sides == "6" and tex.pov.pave_tiles == 3:
                    column_flow.prop(tex.pov, "pave_pat_3", text="Pattern")
                if tex.pov.pave_sides == "3" and tex.pov.pave_tiles == 4:
                    column_flow.prop(tex.pov, "pave_pat_3", text="Pattern")
                if tex.pov.pave_sides == "4" and tex.pov.pave_tiles == 3:
                    column_flow.prop(tex.pov, "pave_pat_2", text="Pattern")
                if tex.pov.pave_sides == "6" and tex.pov.pave_tiles == 6:
                    column_flow.label(text="!!! 5 tiles!")
                column_flow.prop(tex.pov, "pave_form", text="Form")
            if tex.pov.tex_pattern_type == "function":
                layout.prop(tex.pov, "func_list", text="Functions")
            if tex.pov.tex_pattern_type == "function" and tex.pov.func_list != "NONE":
                func = None
                if tex.pov.func_list in {"f_noise3d", "f_ph", "f_r", "f_th"}:
                    func = 0
                if tex.pov.func_list in {
                    "f_comma",
                    "f_crossed_trough",
                    "f_cubic_saddle",
                    "f_cushion",
                    "f_devils_curve",
                    "f_enneper",
                    "f_glob",
                    "f_heart",
                    "f_hex_x",
                    "f_hex_y",
                    "f_hunt_surface",
                    "f_klein_bottle",
                    "f_kummer_surface_v1",
                    "f_lemniscate_of_gerono",
                    "f_mitre",
                    "f_nodal_cubic",
                    "f_noise_generator",
                    "f_odd",
                    "f_paraboloid",
                    "f_pillow",
                    "f_piriform",
                    "f_quantum",
                    "f_quartic_paraboloid",
                    "f_quartic_saddle",
                    "f_sphere",
                    "f_steiners_roman",
                    "f_torus_gumdrop",
                    "f_umbrella",
                }:
                    func = 1
                if tex.pov.func_list in {
                    "f_bicorn",
                    "f_bifolia",
                    "f_boy_surface",
                    "f_superellipsoid",
                    "f_torus",
                }:
                    func = 2
                if tex.pov.func_list in {
                    "f_ellipsoid",
                    "f_folium_surface",
                    "f_hyperbolic_torus",
                    "f_kampyle_of_eudoxus",
                    "f_parabolic_torus",
                    "f_quartic_cylinder",
                    "f_torus2",
                }:
                    func = 3
                if tex.pov.func_list in {
                    "f_blob2",
                    "f_cross_ellipsoids",
                    "f_flange_cover",
                    "f_isect_ellipsoids",
                    "f_kummer_surface_v2",
                    "f_ovals_of_cassini",
                    "f_rounded_box",
                    "f_spikes_2d",
                    "f_strophoid",
                }:
                    func = 4
                if tex.pov.func_list in {
                    "f_algbr_cyl1",
                    "f_algbr_cyl2",
                    "f_algbr_cyl3",
                    "f_algbr_cyl4",
                    "f_blob",
                    "f_mesh1",
                    "f_poly4",
                    "f_spikes",
                }:
                    func = 5
                if tex.pov.func_list in {
                    "f_devils_curve_2d",
                    "f_dupin_cyclid",
                    "f_folium_surface_2d",
                    "f_hetero_mf",
                    "f_kampyle_of_eudoxus_2d",
                    "f_lemniscate_of_gerono_2d",
                    "f_polytubes",
                    "f_ridge",
                    "f_ridged_mf",
                    "f_spiral",
                    "f_witch_of_agnesi",
                }:
                    func = 6
                if tex.pov.func_list in {"f_helix1", "f_helix2", "f_piriform_2d", "f_strophoid_2d"}:
                    func = 7
                if tex.pov.func_list == "f_helical_torus":
                    func = 8
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.label(text="X")
                column_flow.prop(tex.pov, "func_plus_x", text="")
                column_flow.prop(tex.pov, "func_x", text="Value")
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.label(text="Y")
                column_flow.prop(tex.pov, "func_plus_y", text="")
                column_flow.prop(tex.pov, "func_y", text="Value")
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.label(text="Z")
                column_flow.prop(tex.pov, "func_plus_z", text="")
                column_flow.prop(tex.pov, "func_z", text="Value")
                row = layout.row(align=align)
                if func > 0:
                    row.prop(tex.pov, "func_P0", text="P0")
                if func > 1:
                    row.prop(tex.pov, "func_P1", text="P1")
                row = layout.row(align=align)
                if func > 2:
                    row.prop(tex.pov, "func_P2", text="P2")
                if func > 3:
                    row.prop(tex.pov, "func_P3", text="P3")
                row = layout.row(align=align)
                if func > 4:
                    row.prop(tex.pov, "func_P4", text="P4")
                if func > 5:
                    row.prop(tex.pov, "func_P5", text="P5")
                row = layout.row(align=align)
                if func > 6:
                    row.prop(tex.pov, "func_P6", text="P6")
                if func > 7:
                    row.prop(tex.pov, "func_P7", text="P7")
                    row = layout.row(align=align)
                    row.prop(tex.pov, "func_P8", text="P8")
                    row.prop(tex.pov, "func_P9", text="P9")
            # ------------------------- End Patterns ------------------------- #

            layout.prop(tex.pov, "warp_types", text="Warp types")  # warp
            if tex.pov.warp_types == "TOROIDAL":
                layout.prop(tex.pov, "warp_tor_major_radius", text="Major radius")
            if tex.pov.warp_types not in {"CUBIC", "NONE"}:
                layout.prop(tex.pov, "warp_orientation", text="Warp orientation")
            col = layout.column(align=align)
            row = col.row()
            row.prop(tex.pov, "warp_dist_exp", text="Distance exponent")
            row = col.row()
            row.prop(tex.pov, "modifier_frequency", text="Frequency")
            row.prop(tex.pov, "modifier_phase", text="Phase")

            row = layout.row()

            row.label(text="Offset:")
            row.label(text="Scale:")
            row.label(text="Rotate:")
            col = layout.column(align=align)
            row = col.row()
            row.prop(tex.pov, "tex_mov_x", text="X")
            row.prop(tex.pov, "tex_scale_x", text="X")
            row.prop(tex.pov, "tex_rot_x", text="X")
            row = col.row()
            row.prop(tex.pov, "tex_mov_y", text="Y")
            row.prop(tex.pov, "tex_scale_y", text="Y")
            row.prop(tex.pov, "tex_rot_y", text="Y")
            row = col.row()
            row.prop(tex.pov, "tex_mov_z", text="Z")
            row.prop(tex.pov, "tex_scale_z", text="Z")
            row.prop(tex.pov, "tex_rot_z", text="Z")
            row = layout.row()

            row.label(text="Turbulence:")
            col = layout.column(align=align)
            row = col.row()
            row.prop(tex.pov, "warp_turbulence_x", text="X")
            row.prop(tex.pov, "modifier_octaves", text="Octaves")
            row = col.row()
            row.prop(tex.pov, "warp_turbulence_y", text="Y")
            row.prop(tex.pov, "modifier_lambda", text="Lambda")
            row = col.row()
            row.prop(tex.pov, "warp_turbulence_z", text="Z")
            row.prop(tex.pov, "modifier_omega", text="Omega")


class TEXTURE_PT_POV_mapping(TextureSlotPanel, Panel):
    """Use this class to define POV texture mapping buttons."""

    bl_label = "Mapping"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    @classmethod
    def poll(cls, context):
        idblock = pov_context_tex_datablock(context)
        if isinstance(idblock, Brush) and not context.sculpt_object:
            return False

        if not getattr(context, "texture_slot", None):
            return False

        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout

        idblock = pov_context_tex_datablock(context)
        mat = bpy.context.active_object.active_material
        # tex = context.texture_slot
        tex = mat.pov_texture_slots[mat.active_texture_index]
        if not isinstance(idblock, Brush):
            split = layout.split(percentage=0.3)
            col = split.column()
            col.label(text="Coordinates:")
            col = split.column()
            col.prop(tex, "texture_coords", text="")

            if tex.texture_coords == "ORCO":
                """
                ob = context.object
                if ob and ob.type == 'MESH':
                    split = layout.split(percentage=0.3)
                    split.label(text="Mesh:")
                    split.prop(ob.data, "texco_mesh", text="")
                """
            elif tex.texture_coords == "UV":
                split = layout.split(percentage=0.3)
                split.label(text="Map:")
                ob = context.object
                if ob and ob.type == "MESH":
                    split.prop_search(tex, "uv_layer", ob.data, "uv_textures", text="")
                else:
                    split.prop(tex, "uv_layer", text="")

            elif tex.texture_coords == "OBJECT":
                split = layout.split(percentage=0.3)
                split.label(text="Object:")
                split.prop(tex, "object", text="")

            elif tex.texture_coords == "ALONG_STROKE":
                split = layout.split(percentage=0.3)
                split.label(text="Use Tips:")
                split.prop(tex, "use_tips", text="")

        if isinstance(idblock, Brush):
            if context.sculpt_object or context.image_paint_object:
                brush_texture_settings(layout, idblock, context.sculpt_object)
        else:
            if isinstance(idblock, FreestyleLineStyle):
                split = layout.split(percentage=0.3)
                split.label(text="Projection:")
                split.prop(tex, "mapping", text="")

                split = layout.split(percentage=0.3)
                split.separator()
                row = split.row()
                row.prop(tex, "mapping_x", text="")
                row.prop(tex, "mapping_y", text="")
                row.prop(tex, "mapping_z", text="")

            elif isinstance(idblock, Material):
                split = layout.split(percentage=0.3)
                split.label(text="Projection:")
                split.prop(tex, "mapping", text="")

                split = layout.split()

                col = split.column()
                if tex.texture_coords in {"ORCO", "UV"}:
                    col.prop(tex, "use_from_dupli")
                    if idblock.type == "VOLUME" and tex.texture_coords == "ORCO":
                        col.prop(tex, "use_map_to_bounds")
                elif tex.texture_coords == "OBJECT":
                    col.prop(tex, "use_from_original")
                    if idblock.type == "VOLUME":
                        col.prop(tex, "use_map_to_bounds")
                else:
                    col.label()

                col = split.column()
                row = col.row()
                row.prop(tex, "mapping_x", text="")
                row.prop(tex, "mapping_y", text="")
                row.prop(tex, "mapping_z", text="")

            row = layout.row()
            row.column().prop(tex, "offset")
            row.column().prop(tex, "scale")


class TEXTURE_PT_POV_influence(TextureSlotPanel, Panel):
    """Use this class to define pov texture influence buttons."""

    bl_label = "Influence"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_context = 'texture'

    @classmethod
    def poll(cls, context):
        idblock = pov_context_tex_datablock(context)
        if (
            # isinstance(idblock, Brush) and # Brush used for everything since 2.8
            context.scene.texture_context
            == "OTHER"
        ):  # XXX replace by isinstance(idblock, bpy.types.Brush) and ...
            return False

        # Specify below also for pov_world_texture_slots, lights etc.
        # to display for various types of slots but only when any
        if not getattr(idblock, "pov_texture_slots", None):
            return False

        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):

        layout = self.layout

        idblock = pov_context_tex_datablock(context)
        # tex = context.pov_texture_slot
        # mat = bpy.context.active_object.active_material
        texslot = idblock.pov_texture_slots[
            idblock.pov.active_texture_index
        ]  # bpy.data.textures[mat.active_texture_index]
        # below tex unused yet ...maybe for particles?
        try:
            tex = bpy.data.textures[
                idblock.pov_texture_slots[idblock.pov.active_texture_index].texture
            ]  # NOT USED
        except KeyError:
            tex = None  # NOT USED

        def factor_but(layout, toggle, factor, name):
            row = layout.row(align=True)
            row.prop(texslot, toggle, text="")
            sub = row.row(align=True)
            sub.active = getattr(texslot, toggle)
            sub.prop(texslot, factor, text=name, slider=True)
            return sub  # XXX, temp. use_map_normal needs to override.

        if isinstance(idblock, Material):
            split = layout.split()

            col = split.column()
            if idblock.pov.type in {"SURFACE", "WIRE"}:

                split = layout.split()

                col = split.column()
                col.label(text="Diffuse:")
                factor_but(col, "use_map_diffuse", "diffuse_factor", "Intensity")
                factor_but(col, "use_map_color_diffuse", "diffuse_color_factor", "Color")
                factor_but(col, "use_map_alpha", "alpha_factor", "Alpha")
                factor_but(col, "use_map_translucency", "translucency_factor", "Translucency")

                col.label(text="Specular:")
                factor_but(col, "use_map_specular", "specular_factor", "Intensity")
                factor_but(col, "use_map_color_spec", "specular_color_factor", "Color")
                factor_but(col, "use_map_hardness", "hardness_factor", "Hardness")

                col = split.column()
                col.label(text="Shading:")
                factor_but(col, "use_map_ambient", "ambient_factor", "Ambient")
                factor_but(col, "use_map_emit", "emit_factor", "Emit")
                factor_but(col, "use_map_mirror", "mirror_factor", "Mirror")
                factor_but(col, "use_map_raymir", "raymir_factor", "Ray Mirror")

                col.label(text="Geometry:")
                # XXX replace 'or' when displacement is fixed to not rely on normal influence value.
                sub_tmp = factor_but(col, "use_map_normal", "normal_factor", "Normal")
                sub_tmp.active = texslot.use_map_normal or texslot.use_map_displacement
                # END XXX

                factor_but(col, "use_map_warp", "warp_factor", "Warp")
                factor_but(col, "use_map_displacement", "displacement_factor", "Displace")

            elif idblock.pov.type == "HALO":
                layout.label(text="Halo:")

                split = layout.split()

                col = split.column()
                factor_but(col, "use_map_color_diffuse", "diffuse_color_factor", "Color")
                factor_but(col, "use_map_alpha", "alpha_factor", "Alpha")

                col = split.column()
                factor_but(col, "use_map_raymir", "raymir_factor", "Size")
                factor_but(col, "use_map_hardness", "hardness_factor", "Hardness")
                factor_but(col, "use_map_translucency", "translucency_factor", "Add")
            elif idblock.pov.type == "VOLUME":
                layout.label(text="Volume:")

                split = layout.split()

                col = split.column()
                factor_but(col, "use_map_density", "density_factor", "Density")
                factor_but(col, "use_map_emission", "emission_factor", "Emission")
                factor_but(col, "use_map_scatter", "scattering_factor", "Scattering")
                factor_but(col, "use_map_reflect", "reflection_factor", "Reflection")

                col = split.column()
                col.label(text=" ")
                factor_but(col, "use_map_color_emission", "emission_color_factor", "Emission Color")
                factor_but(
                    col,
                    "use_map_color_transmission",
                    "transmission_color_factor",
                    "Transmission Color",
                )
                factor_but(
                    col, "use_map_color_reflection", "reflection_color_factor", "Reflection Color"
                )

                layout.label(text="Geometry:")

                split = layout.split()

                col = split.column()
                factor_but(col, "use_map_warp", "warp_factor", "Warp")

                col = split.column()
                factor_but(col, "use_map_displacement", "displacement_factor", "Displace")

        elif isinstance(idblock, Light):
            split = layout.split()

            col = split.column()
            factor_but(col, "use_map_color", "color_factor", "Color")

            col = split.column()
            factor_but(col, "use_map_shadow", "shadow_factor", "Shadow")

        elif isinstance(idblock, World):
            split = layout.split()

            col = split.column()
            factor_but(col, "use_map_blend", "blend_factor", "Blend")
            factor_but(col, "use_map_horizon", "horizon_factor", "Horizon")

            col = split.column()
            factor_but(col, "use_map_zenith_up", "zenith_up_factor", "Zenith Up")
            factor_but(col, "use_map_zenith_down", "zenith_down_factor", "Zenith Down")
        elif isinstance(idblock, ParticleSettings):
            split = layout.split()

            col = split.column()
            col.label(text="General:")
            factor_but(col, "use_map_time", "time_factor", "Time")
            factor_but(col, "use_map_life", "life_factor", "Lifetime")
            factor_but(col, "use_map_density", "density_factor", "Density")
            factor_but(col, "use_map_size", "size_factor", "Size")

            col = split.column()
            col.label(text="Physics:")
            factor_but(col, "use_map_velocity", "velocity_factor", "Velocity")
            factor_but(col, "use_map_damp", "damp_factor", "Damp")
            factor_but(col, "use_map_gravity", "gravity_factor", "Gravity")
            factor_but(col, "use_map_field", "field_factor", "Force Fields")

            layout.label(text="Hair:")

            split = layout.split()

            col = split.column()
            factor_but(col, "use_map_length", "length_factor", "Length")
            factor_but(col, "use_map_clump", "clump_factor", "Clump")
            factor_but(col, "use_map_twist", "twist_factor", "Twist")

            col = split.column()
            factor_but(col, "use_map_kink_amp", "kink_amp_factor", "Kink Amplitude")
            factor_but(col, "use_map_kink_freq", "kink_freq_factor", "Kink Frequency")
            factor_but(col, "use_map_rough", "rough_factor", "Rough")

        elif isinstance(idblock, FreestyleLineStyle):
            split = layout.split()

            col = split.column()
            factor_but(col, "use_map_color_diffuse", "diffuse_color_factor", "Color")
            col = split.column()
            factor_but(col, "use_map_alpha", "alpha_factor", "Alpha")

        layout.separator()

        if not isinstance(idblock, ParticleSettings):
            split = layout.split()

            col = split.column()
            # col.prop(tex, "blend_type", text="Blend") #deprecated since 2.8
            # col.prop(tex, "use_rgb_to_intensity") #deprecated since 2.8
            # color is used on gray-scale textures even when use_rgb_to_intensity is disabled.
            # col.prop(tex, "color", text="") #deprecated since 2.8

            col = split.column()
            # col.prop(tex, "invert", text="Negative") #deprecated since 2.8
            # col.prop(tex, "use_stencil") #deprecated since 2.8

        # if isinstance(idblock, (Material, World)):
        # col.prop(tex, "default_value", text="DVar", slider=True)


class TEXTURE_PT_POV_tex_gamma(TextureButtonsPanel, Panel):
    """Use this class to define pov texture gamma buttons."""

    bl_label = "Image Gamma"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        tex = context.texture

        self.layout.prop(tex.pov, "tex_gamma_enable", text="", icon="SEQ_LUMA_WAVEFORM")

    def draw(self, context):
        layout = self.layout

        tex = context.texture

        layout.active = tex.pov.tex_gamma_enable
        layout.prop(tex.pov, "tex_gamma_value", text="Gamma Value")


# commented out below UI for texture only custom code inside exported material:
# class TEXTURE_PT_povray_replacement_text(TextureButtonsPanel, Panel):
# bl_label = "Custom POV Code"
# COMPAT_ENGINES = {'POVRAY_RENDER'}

# def draw(self, context):
# layout = self.layout

# tex = context.texture

# col = layout.column()
# col.label(text="Replace properties with:")
# col.prop(tex.pov, "replacement_text", text="")


classes = (
    WORLD_TEXTURE_SLOTS_UL_POV_layerlist,
    TEXTURE_MT_POV_specials,
    # TEXTURE_PT_context # todo: solve UI design for painting
    TEXTURE_PT_POV_context_texture,
    TEXTURE_PT_colors,
    TEXTURE_PT_POV_type,
    TEXTURE_PT_POV_preview,
    TEXTURE_PT_POV_parameters,
    TEXTURE_PT_POV_tex_gamma,
    MATERIAL_TEXTURE_SLOTS_UL_POV_layerlist,
    TEXTURE_OT_POV_texture_slot_add,
    TEXTURE_OT_POV_texture_slot_remove,
    TEXTURE_OT_POV_context_texture_update,
    TEXTURE_PT_POV_influence,
    TEXTURE_PT_POV_mapping,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        # if cls != TEXTURE_PT_context:
        unregister_class(cls)
