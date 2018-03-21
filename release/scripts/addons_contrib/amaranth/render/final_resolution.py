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
    layout = self.layout

    final_res_x = (rd.resolution_x * rd.resolution_percentage) / 100
    final_res_y = (rd.resolution_y * rd.resolution_percentage) / 100

    if rd.use_border:
        final_res_x_border = round(
            (final_res_x * (rd.border_max_x - rd.border_min_x)))
        final_res_y_border = round(
            (final_res_y * (rd.border_max_y - rd.border_min_y)))
        layout.label(text="Final Resolution: {} x {} [Border: {} x {}]".format(
                     str(final_res_x)[:-2], str(final_res_y)[:-2],
                     str(final_res_x_border), str(final_res_y_border)))
    else:
        layout.label(text="Final Resolution: {} x {}".format(
                     str(final_res_x)[:-2], str(final_res_y)[:-2]))


def register():
    bpy.types.RENDER_PT_dimensions.append(render_final_resolution_ui)


def unregister():
    bpy.types.RENDER_PT_dimensions.remove(render_final_resolution_ui)
