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
    importlib.reload(view3d_copy_paste_uv_editmode)
    importlib.reload(view3d_copy_paste_uv_objectmode)
    importlib.reload(view3d_uv_manipulation)
    importlib.reload(view3d_uv_mapping)
    importlib.reload(uvedit_copy_paste_uv)
    importlib.reload(VIEW3D_MT_object)
    importlib.reload(VIEW3D_MT_uv_map)
    importlib.reload(IMAGE_MT_uvs)
else:
    from . import view3d_copy_paste_uv_editmode
    from . import view3d_copy_paste_uv_objectmode
    from . import view3d_uv_manipulation
    from . import view3d_uv_mapping
    from . import uvedit_copy_paste_uv
    from . import VIEW3D_MT_object
    from . import VIEW3D_MT_uv_map
    from . import IMAGE_MT_uvs

import bpy
