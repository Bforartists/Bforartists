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

if "bpy" in locals():
    import importlib
    importlib.reload(align_uv_cursor_impl)
    importlib.reload(align_uv_impl)
    importlib.reload(copy_paste_uv_impl)
    importlib.reload(copy_paste_uv_uvedit_impl)
    importlib.reload(flip_rotate_impl)
    importlib.reload(mirror_uv_impl)
    importlib.reload(move_uv_impl)
    importlib.reload(pack_uv_impl)
    importlib.reload(preserve_uv_aspect_impl)
    importlib.reload(select_uv_impl)
    importlib.reload(smooth_uv_impl)
    importlib.reload(texture_lock_impl)
    importlib.reload(texture_wrap_impl)
    importlib.reload(transfer_uv_impl)
    importlib.reload(unwrap_constraint_impl)
    importlib.reload(uv_bounding_box_impl)
    importlib.reload(uv_inspection_impl)
    importlib.reload(uv_sculpt_impl)
    importlib.reload(uvw_impl)
    importlib.reload(world_scale_uv_impl)
else:
    from . import align_uv_cursor_impl
    from . import align_uv_impl
    from . import copy_paste_uv_impl
    from . import copy_paste_uv_uvedit_impl
    from . import flip_rotate_impl
    from . import mirror_uv_impl
    from . import move_uv_impl
    from . import pack_uv_impl
    from . import preserve_uv_aspect_impl
    from . import select_uv_impl
    from . import smooth_uv_impl
    from . import texture_lock_impl
    from . import texture_wrap_impl
    from . import transfer_uv_impl
    from . import unwrap_constraint_impl
    from . import uv_bounding_box_impl
    from . import uv_inspection_impl
    from . import uv_sculpt_impl
    from . import uvw_impl
    from . import world_scale_uv_impl

import bpy
