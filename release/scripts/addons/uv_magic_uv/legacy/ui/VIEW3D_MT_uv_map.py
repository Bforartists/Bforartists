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

import bpy
import bpy.utils

from ..op import (
    texture_lock,
    copy_paste_uv,
    preserve_uv_aspect,
    texture_projection,
    texture_wrap,
    transfer_uv,
    uvw,
    world_scale_uv
)
from ..op.world_scale_uv import MUV_OT_WorldScaleUV_ApplyProportionalToMesh
from ...utils.bl_class_registry import BlClassRegistry

__all__ = [
    'MUV_MT_CopyPasteUV',
    'MUV_MT_TransferUV',
    'MUV_MT_TextureLock',
    'MUV_MT_WorldScaleUV',
    'MUV_MT_TextureWrap',
    'MUV_MT_UVW',
    'MUV_MT_TextureProjection',
    'MUV_MT_PreserveUVAspect',
]


@BlClassRegistry(legacy=True)
class MUV_MT_CopyPasteUV(bpy.types.Menu):
    """
    Menu class: Master menu of Copy/Paste UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_menu"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV coordinate"

    def draw(self, _):
        layout = self.layout

        layout.label(text="Default")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_CopyUV.bl_idname,
                    text="Copy")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_PasteUV.bl_idname,
                    text="Paste")

        layout.separator()

        layout.label(text="Selection Sequence")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                    text="Copy")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                    text="Paste")


@BlClassRegistry(legacy=True)
class MUV_MT_TransferUV(bpy.types.Menu):
    """
    Menu class: Master menu of Transfer UV coordinate
    """

    bl_idname = "uv.muv_transfer_uv_menu"
    bl_label = "Transfer UV"
    bl_description = "Transfer UV coordinate"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.operator(transfer_uv.MUV_OT_TransferUV_CopyUV.bl_idname,
                        text="Copy")
        ops = layout.operator(transfer_uv.MUV_OT_TransferUV_PasteUV.bl_idname,
                              text="Paste")
        ops.invert_normals = sc.muv_transfer_uv_invert_normals
        ops.copy_seams = sc.muv_transfer_uv_copy_seams


@BlClassRegistry(legacy=True)
class MUV_MT_TextureLock(bpy.types.Menu):
    """
    Menu class: Master menu of Texture Lock
    """

    bl_idname = "uv.muv_texture_lock_menu"
    bl_label = "Texture Lock"
    bl_description = "Lock texture when vertices of mesh (Preserve UV)"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label("Normal Mode")
        layout.operator(
            texture_lock.MUV_OT_TextureLock_Lock.bl_idname,
            text="Lock"
            if not texture_lock.MUV_OT_TextureLock_Lock.is_ready(context)
            else "ReLock")
        ops = layout.operator(texture_lock.MUV_OT_TextureLock_Unlock.bl_idname,
                              text="Unlock")
        ops.connect = sc.muv_texture_lock_connect

        layout.separator()

        layout.label("Interactive Mode")
        layout.prop(sc, "muv_texture_lock_lock", text="Lock")


@BlClassRegistry(legacy=True)
class MUV_MT_WorldScaleUV(bpy.types.Menu):
    """
    Menu class: Master menu of world scale UV
    """

    bl_idname = "uv.muv_world_scale_uv_menu"
    bl_label = "World Scale UV"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.operator(world_scale_uv.MUV_OT_WorldScaleUV_Measure.bl_idname,
                        text="Measure")

        layout.operator(
            world_scale_uv.MUV_OT_WorldScaleUV_ApplyManual.bl_idname,
            text="Apply (Manual)")

        ops = layout.operator(
            world_scale_uv.MUV_OT_WorldScaleUV_ApplyScalingDensity.bl_idname,
            text="Apply (Same Desity)")
        ops.src_density = sc.muv_world_scale_uv_src_density
        ops.same_density = True

        ops = layout.operator(
            world_scale_uv.MUV_OT_WorldScaleUV_ApplyScalingDensity.bl_idname,
            text="Apply (Scaling Desity)")
        ops.src_density = sc.muv_world_scale_uv_src_density
        ops.same_density = False
        ops.tgt_scaling_factor = sc.muv_world_scale_uv_tgt_scaling_factor

        ops = layout.operator(
            MUV_OT_WorldScaleUV_ApplyProportionalToMesh.bl_idname,
            text="Apply (Proportional to Mesh)")
        ops.src_density = sc.muv_world_scale_uv_src_density
        ops.src_uv_area = sc.muv_world_scale_uv_src_uv_area
        ops.src_mesh_area = sc.muv_world_scale_uv_src_mesh_area
        ops.origin = sc.muv_world_scale_uv_origin


@BlClassRegistry(legacy=True)
class MUV_MT_TextureWrap(bpy.types.Menu):
    """
    Menu class: Master menu of Texture Wrap
    """

    bl_idname = "uv.muv_texture_wrap_menu"
    bl_label = "Texture Wrap"
    bl_description = ""

    def draw(self, _):
        layout = self.layout

        layout.operator(texture_wrap.MUV_OT_TextureWrap_Refer.bl_idname,
                        text="Refer")
        layout.operator(texture_wrap.MUV_OT_TextureWrap_Set.bl_idname,
                        text="Set")


@BlClassRegistry(legacy=True)
class MUV_MT_UVW(bpy.types.Menu):
    """
    Menu class: Master menu of UVW
    """

    bl_idname = "uv.muv_uvw_menu"
    bl_label = "UVW"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        ops = layout.operator(uvw.MUV_OT_UVW_BoxMap.bl_idname, text="Box")
        ops.assign_uvmap = sc.muv_uvw_assign_uvmap

        ops = layout.operator(uvw.MUV_OT_UVW_BestPlanerMap.bl_idname,
                              text="Best Planner")
        ops.assign_uvmap = sc.muv_uvw_assign_uvmap


@BlClassRegistry(legacy=True)
class MUV_MT_TextureProjection(bpy.types.Menu):
    """
    Menu class: Master menu of Texture Projection
    """

    bl_idname = "uv.muv_texture_projection_menu"
    bl_label = "Texture Projection"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.prop(sc, "muv_texture_projection_enable",
                    text="Texture Projection")
        layout.operator(
            texture_projection.MUV_OT_TextureProjection_Project.bl_idname,
            text="Project")


@BlClassRegistry(legacy=True)
class MUV_MT_PreserveUVAspect(bpy.types.Menu):
    """
    Menu class: Master menu of Preserve UV Aspect
    """

    bl_idname = "uv.muv_preserve_uv_aspect_menu"
    bl_label = "Preserve UV Aspect"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        for key in bpy.data.images.keys():
            ops = layout.operator(
                preserve_uv_aspect.MUV_OT_PreserveUVAspect.bl_idname, text=key)
            ops.dest_img_name = key
            ops.origin = sc.muv_preserve_uv_aspect_origin
