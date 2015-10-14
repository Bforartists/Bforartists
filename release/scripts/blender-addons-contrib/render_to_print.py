# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "Render to Print",
    "author": "Marco Crippa <thekrypt77@tiscali.it>, Dealga McArdle",
    "version": (0, 2),
    "blender": (2, 58, 0),
    "location": "Render > Render to Print",
    "description": "Set the size of the render for a print",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Render/Render to Print",
    "tracker_url": "https://developer.blender.org/T24219",
    "category": "Render"}


import math
import bpy
from bpy.types import Panel, Operator, Scene, PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       PointerProperty,
                       )


paper_presets = (
    ("custom_1_1", "custom", ""),
    ("A0_84.1_118.9", "A0 (84.1x118.9 cm)", ""),
    ("A1_59.4_84.1", "A1 (59.4x84.1 cm)", ""),
    ("A2_42.0_59.4", "A2 (42.0x59.4 cm)", ""),
    ("A3_29.7_42.0", "A3 (29.7 42.0 cm)", ""),
    ("A4_21.0_29.7", "A4 (21.0x29.7 cm)", ""),
    ("A5_14.8_21.0", "A5 (14.8x21.0 cm)", ""),
    ("A6_10.5_14.8", "A6 (10.5x14.8 cm)", ""),
    ("A7_7.4_10.5", "A7 (7.4x10.5 cm)", ""),
    ("A8_5.2_7.4", "A8 (5.2x7.4 cm)", ""),
    ("A9_3.7_5.2", "A9 (3.7x5.2 cm)", ""),
    ("A10_2.6_3.7", "A10 (2.6x3.7 cm)", ""),

    ("B0_100.0_141.4", "B0 (100.0x141.4 cm)", ""),
    ("B1_70.7_100.0", "B1 (70.7x100.0 cm)", ""),
    ("B2_50.0_70.7", "B2 (50.0x70.7 cm)", ""),
    ("B3_35.3_50.0", "B3 (35.3x50.0 cm)", ""),
    ("B4_25.0_35.3", "B4 (25.0x35.3 cm)", ""),
    ("B5_17.6_25.0", "B5 (17.6x25.0 cm)", ""),
    ("B6_12.5_17.6", "B6 (12.5x17.6 cm)", ""),
    ("B7_8.8_12.5", "B7 (8.8x12.5 cm)", ""),
    ("B8_6.2_8.8", "B8 (6.2x8.8 cm)", ""),
    ("B9_4.4_6.2", "B9 (4.4x6.2 cm)", ""),
    ("B10_3.1_4.4", "B10 (3.1x4.4 cm)", ""),

    ("C0_91.7_129.7", "C0 (91.7x129.7 cm)", ""),
    ("C1_64.8_91.7", "C1 (64.8x91.7 cm)", ""),
    ("C2_45.8_64.8", "C2 (45.8x64.8 cm)", ""),
    ("C3_32.4_45.8", "C3 (32.4x45.8 cm)", ""),
    ("C4_22.9_32.4", "C4 (22.9x32.4 cm)", ""),
    ("C5_16.2_22.9", "C5 (16.2x22.9 cm)", ""),
    ("C6_11.4_16.2", "C6 (11.4x16.2 cm)", ""),
    ("C7_8.1_11.4", "C7 (8.1x11.4 cm)", ""),
    ("C8_5.7_8.1", "C8 (5.7x8.1 cm)", ""),
    ("C9_4.0_5.7", "C9 (4.0x5.7 cm)", ""),
    ("C10_2.8_4.0", "C10 (2.8x4.0 cm)", ""),

    ("Letter_21.6_27.9", "Letter (21.6x27.9 cm)", ""),
    ("Legal_21.6_35.6", "Legal (21.6x35.6 cm)", ""),
    ("Legal junior_20.3_12.7", "Legal junior (20.3x12.7 cm)", ""),
    ("Ledger_43.2_27.9", "Ledger (43.2x27.9 cm)", ""),
    ("Tabloid_27.9_43.2", "Tabloid (27.9x43.2 cm)", ""),

    ("ANSI C_43.2_55.9", "ANSI C (43.2x55.9 cm)", ""),
    ("ANSI D_55.9_86.4", "ANSI D (55.9x86.4 cm)", ""),
    ("ANSI E_86.4_111.8", "ANSI E (86.4x111.8 cm)", ""),

    ("Arch A_22.9_30.5", "Arch A (22.9x30.5 cm)", ""),
    ("Arch B_30.5_45.7", "Arch B (30.5x45.7 cm)", ""),
    ("Arch C_45.7_61.0", "Arch C (45.7x61.0 cm)", ""),
    ("Arch D_61.0_91.4", "Arch D (61.0x91.4 cm)", ""),
    ("Arch E_91.4_121.9", "Arch E (91.4x121.9 cm)", ""),
    ("Arch E1_76.2_106.7", "Arch E1 (76.2x106.7 cm)", ""),
    ("Arch E2_66.0_96.5", "Arch E2 (66.0x96.5 cm)", ""),
    ("Arch E3_68.6_99.1", "Arch E3 (68.6x99.1 cm)", ""),
    )


def paper_enum_parse(idname):
    tipo, dim_w, dim_h = idname.split("_")
    return tipo, float(dim_w), float(dim_h)


paper_presets_data = {idname: paper_enum_parse(idname)
                      for idname, name, descr in paper_presets}


def update_settings_cb(self, context):
    # annoying workaround for recursive call
    if update_settings_cb.level is False:
        update_settings_cb.level = True
        pixels_from_print(self)
        update_settings_cb.level = False

update_settings_cb.level = False


class RenderPrintSertings(PropertyGroup):
    unit_from = EnumProperty(
            name="Set from",
            description="Set from",
            items=(
                ("CM_TO_PIXELS", "CM -> Pixel", "Centermeters to Pixels"),
                ("PIXELS_TO_CM", "Pixel -> CM", "Pixels to Centermeters")
                ),
            default="CM_TO_PIXELS",
            )
    orientation = EnumProperty(
            name="Page Orientation",
            description="Set orientation",
            items=(
                ("Portrait", "Portrait", "Portrait"),
                ("Landscape", "Landscape", "Landscape")
            ),
            default="Portrait",
            update=update_settings_cb,
            )
    preset = EnumProperty(
            name="Select Preset",
            description="Select from preset",
            items=paper_presets,
            default="custom_1_1",
            update=update_settings_cb,
            )
    dpi = IntProperty(
            name="DPI",
            description="Dots per Inch",
            default=300,
            min=72, max=1800,
            update=update_settings_cb,
            )
    width_cm = FloatProperty(
            name="Width",
            description="Width in CM",
            default=5.0,
            min=1.0, max=100000.0,
            update=update_settings_cb,
            )
    height_cm = FloatProperty(
            name="Height",
            description="Height in CM",
            default=3.0,
            min=1.0, max=100000.0,
            update=update_settings_cb,
            )
    width_px = IntProperty(
            name="Pixel Width",
            description="Pixel Width",
            default=900,
            min=4, max=10000,
            update=update_settings_cb,
            )
    height_px = IntProperty(
            name="Pixel Height",
            description="Pixel Height",
            default=600,
            min=4, max=10000,
            update=update_settings_cb,
            )


def pixels_from_print(ps):
    tipo, dim_w, dim_h = paper_presets_data[ps.preset]

    if ps.unit_from == "CM_TO_PIXELS":
        if tipo == "custom":
            dim_w = ps.width_cm
            dim_h = ps.height_cm
            ps.width_cm = dim_w
            ps.height_cm = dim_h
        elif tipo != "custom" and ps.orientation == "Landscape":
            ps.width_cm = dim_h
            ps.height_cm = dim_w
        elif tipo != "custom" and ps.orientation == "Portrait":
            ps.width_cm = dim_w
            ps.height_cm = dim_h

        ps.width_px = math.ceil((ps.width_cm * ps.dpi) / 2.54)
        ps.height_px = math.ceil((ps.height_cm * ps.dpi) / 2.54)
    else:
        if tipo != "custom" and ps.orientation == "Landscape":
            ps.width_cm = dim_h
            ps.height_cm = dim_w
            ps.width_px = math.ceil((ps.width_cm * ps.dpi) / 2.54)
            ps.height_px = math.ceil((ps.height_cm * ps.dpi) / 2.54)
        elif tipo != "custom" and ps.orientation == "Portrait":
            ps.width_cm = dim_w
            ps.height_cm = dim_h
            ps.width_px = math.ceil((ps.width_cm * ps.dpi) / 2.54)
            ps.height_px = math.ceil((ps.height_cm * ps.dpi) / 2.54)

        ps.width_cm = (ps.width_px / ps.dpi) * 2.54
        ps.height_cm = (ps.height_px / ps.dpi) * 2.54


class RENDER_PT_print(Panel):
    bl_label = "Render to Print"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):

        layout = self.layout
        scene = context.scene
        ps = scene.print_settings

        row = layout.row(align=True)
        row1 = layout.row(align=True)
        row2 = layout.row(align=True)
        row3 = layout.row(align=True)
        row4 = layout.row(align=True)
        row5 = layout.row(align=True)
        row6 = layout.row(align=True)
        row7 = layout.row(align=True)
        col = layout.column(align=True)

        row.prop(ps, "unit_from")
        row1.prop(ps, "orientation")
        row2.prop(ps, "preset")

        col.separator()
        row3.prop(ps, "width_cm")
        row3.separator()
        row3.prop(ps, "height_cm")
        col.separator()
        row4.prop(ps, "dpi")
        col.separator()
        row5.prop(ps, "width_px")
        row5.separator()
        row5.prop(ps, "height_px")

        col.separator()
        row6.label("Inch Width: %.2f" % (ps.width_cm / 2.54))
        row6.label("Inch Height: %.2f" % (ps.height_cm / 2.54))
        col.separator()

        row7.operator("render.apply_size", icon="RENDER_STILL")

        #  this if else deals with hiding UI elements when logic demands it.
        tipo = paper_presets_data[ps.preset][0]

        if tipo != "custom":
            row.active = False
            row.enabled = False

        if ps.unit_from == "CM_TO_PIXELS":
            row5.active = False
            row5.enabled = False

            if tipo == "custom":
                row3.active = True
                row3.enabled = True
                row1.active = False
                row1.enabled = False
            elif tipo != "custom" and ps.orientation == "Landscape":
                row3.active = False
                row3.enabled = False
                row1.active = True
                row1.enabled = True
            elif tipo != "custom" and ps.orientation == "Portrait":
                row3.active = False
                row3.enabled = False
                row1.active = True
                row1.enabled = True
        else:
            row3.active = False
            row3.enabled = False

            if tipo == "custom":
                row1.active = False
                row1.enabled = False
            elif tipo != "custom" and ps.orientation == "Landscape":
                row1.active = True
                row1.enabled = True
                row5.active = False
                row5.enabled = False
            elif tipo != "custom" and ps.orientation == "Portrait":
                row1.active = True
                row1.enabled = True
                row5.active = False
                row5.enabled = False


class RENDER_OT_apply_size(Operator):
    bl_idname = "render.apply_size"
    bl_label = "Apply Print to Render"
    bl_description = "Set the render dimension"

    def execute(self, context):

        scene = context.scene
        ps = scene.print_settings

        pixels_from_print(ps)

        render = scene.render
        render.resolution_x = ps.width_px
        render.resolution_y = ps.height_px

        return {'FINISHED'}


def register():
    bpy.utils.register_class(RENDER_OT_apply_size)
    bpy.utils.register_class(RENDER_PT_print)
    bpy.utils.register_class(RenderPrintSertings)

    Scene.print_settings = PointerProperty(type=RenderPrintSertings)


def unregister():
    bpy.utils.unregister_class(RENDER_OT_apply_size)
    bpy.utils.unregister_class(RENDER_PT_print)
    bpy.utils.unregister_class(RenderPrintSertings)
    del Scene.print_settings


if __name__ == "__main__":
    register()
