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
__version__ = "4.1"
__date__ = "13 Nov 2016"


bl_info = {
    "name": "Magic UV",
    "author": "Nutti",
    "version": (4, 1),
    "blender": (2, 77, 0),
    "location": "View3D > U, View3D > Property Panel, ImageEditor > Property Panel, ImageEditor > UVs",
    "description": "UV Manipulator Tools",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/UV/Copy_Paste_UVs",
    "tracker_url": "https://github.com/nutti/Copy-And-Paste-UV",
    "category": "UV"
}

if "bpy" in locals():
    import imp
    imp.reload(muv_preferences)
    imp.reload(muv_menu)
    imp.reload(muv_common)
    imp.reload(muv_props)
    imp.reload(muv_cpuv_ops)
    imp.reload(muv_cpuv_selseq_ops)
    imp.reload(muv_fliprot_ops)
    imp.reload(muv_transuv_ops)
    imp.reload(muv_uvbb_ops)
    imp.reload(muv_mvuv_ops)
    imp.reload(muv_texproj_ops)
    imp.reload(muv_packuv_ops)
    imp.reload(muv_texlock_ops)
    imp.reload(muv_mirroruv_ops)
    imp.reload(muv_wsuv_ops)
    imp.reload(muv_unwrapconst_ops)
else:
    from . import muv_preferences
    from . import muv_menu
    from . import muv_common
    from . import muv_props
    from . import muv_cpuv_ops
    from . import muv_cpuv_selseq_ops
    from . import muv_fliprot_ops
    from . import muv_transuv_ops
    from . import muv_uvbb_ops
    from . import muv_mvuv_ops
    from . import muv_texproj_ops
    from . import muv_packuv_ops
    from . import muv_texlock_ops
    from . import muv_mirroruv_ops
    from . import muv_wsuv_ops
    from . import muv_unwrapconst_ops

import bpy


def view3d_uvmap_menu_fn(self, context):
    self.layout.separator()
    self.layout.menu(muv_menu.MUV_CPUVMenu.bl_idname, icon="PLUGIN")
    self.layout.operator(muv_fliprot_ops.MUV_FlipRot.bl_idname, icon="PLUGIN")
    self.layout.menu(muv_menu.MUV_TransUVMenu.bl_idname, icon="PLUGIN")
    self.layout.operator(muv_mvuv_ops.MUV_MVUV.bl_idname, icon="PLUGIN")
    self.layout.menu(muv_menu.MUV_TexLockMenu.bl_idname, icon="PLUGIN")
    self.layout.operator(muv_mirroruv_ops.MUV_MirrorUV.bl_idname, icon="PLUGIN")
    self.layout.menu(muv_menu.MUV_WSUVMenu.bl_idname, icon="PLUGIN")
    self.layout.operator(muv_unwrapconst_ops.MUV_UnwrapConstraint.bl_idname, icon='PLUGIN')


def image_uvs_menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(muv_packuv_ops.MUV_PackUV.bl_idname, icon="PLUGIN")


def view3d_object_menu_fn(self, context):
    self.layout.separator()
    self.layout.menu(muv_menu.MUV_CPUVObjMenu.bl_idname, icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_uv_map.append(view3d_uvmap_menu_fn)
    bpy.types.IMAGE_MT_uvs.append(image_uvs_menu_fn)
    bpy.types.VIEW3D_MT_object.append(view3d_object_menu_fn)
    muv_props.init_props(bpy.types.Scene)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_uv_map.remove(view3d_uvmap_menu_fn)
    bpy.types.IMAGE_MT_uvs.remove(image_uvs_menu_fn)
    bpy.types.VIEW3D_MT_object.remove(view3d_object_menu_fn)
    muv_props.clear_props(bpy.types.Scene)


if __name__ == "__main__":
    register()
