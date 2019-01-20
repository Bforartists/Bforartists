# <pep8-80 compliant>

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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

from collections import namedtuple

import bpy
import mathutils


_Rect = namedtuple('Rect', 'x0 y0 x1 y1')
_Rect2 = namedtuple('Rect2', 'x y width height')


def get_loaded_texture_name(_, __):
    items = [(key, key, "") for key in bpy.data.images.keys()]
    items.append(("None", "None", ""))
    return items


def get_canvas(context, magnitude):
    """
    Get canvas to be renderred texture
    """
    sc = context.scene
    prefs = context.user_preferences.addons["uv_magic_uv"].preferences

    region_w = context.region.width
    region_h = context.region.height
    canvas_w = region_w - prefs.texture_projection_canvas_padding[0] * 2.0
    canvas_h = region_h - prefs.texture_projection_canvas_padding[1] * 2.0

    img = bpy.data.images[sc.muv_texture_projection_tex_image]
    tex_w = img.size[0]
    tex_h = img.size[1]

    center_x = region_w * 0.5
    center_y = region_h * 0.5

    if sc.muv_texture_projection_adjust_window:
        ratio_x = canvas_w / tex_w
        ratio_y = canvas_h / tex_h
        if sc.muv_texture_projection_apply_tex_aspect:
            ratio = ratio_y if ratio_x > ratio_y else ratio_x
            len_x = ratio * tex_w
            len_y = ratio * tex_h
        else:
            len_x = canvas_w
            len_y = canvas_h
    else:
        if sc.muv_texture_projection_apply_tex_aspect:
            len_x = tex_w * magnitude
            len_y = tex_h * magnitude
        else:
            len_x = region_w * magnitude
            len_y = region_h * magnitude

    x0 = int(center_x - len_x * 0.5)
    y0 = int(center_y - len_y * 0.5)
    x1 = int(center_x + len_x * 0.5)
    y1 = int(center_y + len_y * 0.5)

    return _Rect(x0, y0, x1, y1)


def rect_to_rect2(rect):
    """
    Convert Rect1 to Rect2
    """

    return _Rect2(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0)


def region_to_canvas(rg_vec, canvas):
    """
    Convert screen region to canvas
    """

    cv_rect = rect_to_rect2(canvas)
    cv_vec = mathutils.Vector()
    cv_vec.x = (rg_vec.x - cv_rect.x) / cv_rect.width
    cv_vec.y = (rg_vec.y - cv_rect.y) / cv_rect.height

    return cv_vec


def is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True
