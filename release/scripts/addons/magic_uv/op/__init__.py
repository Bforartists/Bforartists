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
__version__ = "6.0"
__date__ = "26 Jan 2019"

if "bpy" in locals():
    import importlib
    importlib.reload(align_uv)
    importlib.reload(align_uv_cursor)
    importlib.reload(copy_paste_uv)
    importlib.reload(copy_paste_uv_object)
    importlib.reload(copy_paste_uv_uvedit)
    importlib.reload(flip_rotate_uv)
    importlib.reload(mirror_uv)
    importlib.reload(move_uv)
    importlib.reload(pack_uv)
    importlib.reload(preserve_uv_aspect)
    importlib.reload(select_uv)
    importlib.reload(smooth_uv)
    importlib.reload(texture_lock)
    importlib.reload(texture_projection)
    importlib.reload(texture_wrap)
    importlib.reload(transfer_uv)
    importlib.reload(unwrap_constraint)
    importlib.reload(uv_bounding_box)
    importlib.reload(uv_inspection)
    importlib.reload(uv_sculpt)
    importlib.reload(uvw)
    importlib.reload(world_scale_uv)
else:
    from . import align_uv
    from . import align_uv_cursor
    from . import copy_paste_uv
    from . import copy_paste_uv_object
    from . import copy_paste_uv_uvedit
    from . import flip_rotate_uv
    from . import mirror_uv
    from . import move_uv
    from . import pack_uv
    from . import preserve_uv_aspect
    from . import select_uv
    from . import smooth_uv
    from . import texture_lock
    from . import texture_projection
    from . import texture_wrap
    from . import transfer_uv
    from . import unwrap_constraint
    from . import uv_bounding_box
    from . import uv_inspection
    from . import uv_sculpt
    from . import uvw
    from . import world_scale_uv

import bpy
