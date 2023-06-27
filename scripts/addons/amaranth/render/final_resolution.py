# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
UI: Final Resolution

Always wondered how big the render was going to be when rendering at a
certain %?
This feature displays a "Final Resolution" label with the size in pixels
of your render, it also displays the size for border renders.

On the 'Dimensions' panel, Render properties.
"""
import bpy


def render_final_resolution_ui(self, context):

    rd = context.scene.render
    final_res_x = (rd.resolution_x * rd.resolution_percentage) / 100
    final_res_y = (rd.resolution_y * rd.resolution_percentage) / 100
    final_res_x_border = round(
        (final_res_x * (rd.border_max_x - rd.border_min_x)))
    final_res_y_border = round(
        (final_res_y * (rd.border_max_y - rd.border_min_y)))

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    layout.separator()
    box = layout.box()
    col = box.column(align=True)
    col.active = False
    split = col.split(factor=0.4)

    col = split.column(align=True)
    row = col.row()
    row.alignment = 'RIGHT'
    row.label(text="Render Resolution")

    if rd.use_border:
        row = col.row()
        row.alignment = 'RIGHT'
        row.label(text="Region")

    col = split.column(align=True)
    col.label(text="{} x {}".format(
        str(final_res_x)[:-2], str(final_res_y)[:-2]))

    if rd.use_border:
        col.label(text="{} x {}".format(
            str(final_res_x_border), str(final_res_y_border)))


def register():
    bpy.types.RENDER_PT_format.append(render_final_resolution_ui)


def unregister():
    bpy.types.RENDER_PT_format.remove(render_final_resolution_ui)
