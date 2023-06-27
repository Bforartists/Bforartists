# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy.utils

from ..op.copy_paste_uv import (
    MUV_MT_CopyPasteUV_CopyUV,
    MUV_MT_CopyPasteUV_PasteUV,
    MUV_MT_CopyPasteUV_SelSeqCopyUV,
    MUV_MT_CopyPasteUV_SelSeqPasteUV,
)
from ..op.transfer_uv import (
    MUV_OT_TransferUV_CopyUV,
    MUV_OT_TransferUV_PasteUV,
)
from ..op.uvw import (
    MUV_OT_UVW_BoxMap,
    MUV_OT_UVW_BestPlanerMap,
)
from ..op.preserve_uv_aspect import MUV_OT_PreserveUVAspect
from ..op.texture_lock import (
    MUV_OT_TextureLock_Lock,
    MUV_OT_TextureLock_Unlock,
)
from ..op.texture_wrap import (
    MUV_OT_TextureWrap_Refer,
    MUV_OT_TextureWrap_Set,
)
from ..op.world_scale_uv import (
    MUV_OT_WorldScaleUV_Measure,
    MUV_OT_WorldScaleUV_ApplyManual,
    MUV_OT_WorldScaleUV_ApplyScalingDensity,
    MUV_OT_WorldScaleUV_ApplyProportionalToMesh,
)
from ..op.texture_projection import MUV_OT_TextureProjection_Project
from ..utils.bl_class_registry import BlClassRegistry


@BlClassRegistry()
class MUV_MT_CopyPasteUV(bpy.types.Menu):
    """
    Menu class: Master menu of Copy/Paste UV coordinate
    """

    bl_idname = "MUV_MT_CopyPasteUV"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV coordinate"

    def draw(self, _):
        layout = self.layout

        layout.label(text="Default")
        layout.menu(MUV_MT_CopyPasteUV_CopyUV.bl_idname, text="Copy")
        layout.menu(MUV_MT_CopyPasteUV_PasteUV.bl_idname, text="Paste")

        layout.separator()

        layout.label(text="Selection Sequence")
        layout.menu(MUV_MT_CopyPasteUV_SelSeqCopyUV.bl_idname, text="Copy")
        layout.menu(MUV_MT_CopyPasteUV_SelSeqPasteUV.bl_idname, text="Paste")


@BlClassRegistry()
class MUV_MT_TransferUV(bpy.types.Menu):
    """
    Menu class: Master menu of Transfer UV coordinate
    """

    bl_idname = "MUV_MT_TransferUV"
    bl_label = "Transfer UV"
    bl_description = "Transfer UV coordinate"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.operator(MUV_OT_TransferUV_CopyUV.bl_idname, text="Copy")
        ops = layout.operator(MUV_OT_TransferUV_PasteUV.bl_idname,
                              text="Paste")
        ops.invert_normals = sc.muv_transfer_uv_invert_normals
        ops.copy_seams = sc.muv_transfer_uv_copy_seams


@BlClassRegistry()
class MUV_MT_TextureLock(bpy.types.Menu):
    """
    Menu class: Master menu of Texture Lock
    """

    bl_idname = "MUV_MT_TextureLock"
    bl_label = "Texture Lock"
    bl_description = "Lock texture when vertices of mesh (Preserve UV)"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Normal Mode")
        layout.operator(
            MUV_OT_TextureLock_Lock.bl_idname,
            text="Lock"
            if not MUV_OT_TextureLock_Lock.is_ready(context)
            else "ReLock")
        ops = layout.operator(MUV_OT_TextureLock_Unlock.bl_idname,
                              text="Unlock")
        ops.connect = sc.muv_texture_lock_connect

        layout.separator()

        layout.label(text="Interactive Mode")
        layout.prop(sc, "muv_texture_lock_lock", text="Lock")


@BlClassRegistry()
class MUV_MT_WorldScaleUV(bpy.types.Menu):
    """
    Menu class: Master menu of world scale UV
    """

    bl_idname = "MUV_MT_WorldScaleUV"
    bl_label = "World Scale UV"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.operator(MUV_OT_WorldScaleUV_Measure.bl_idname, text="Measure")

        ops = layout.operator(MUV_OT_WorldScaleUV_ApplyManual.bl_idname,
                              text="Apply (Manual)")
        ops.show_dialog = True

        ops = layout.operator(
            MUV_OT_WorldScaleUV_ApplyScalingDensity.bl_idname,
            text="Apply (Same Desity)")
        ops.src_density = sc.muv_world_scale_uv_src_density
        ops.same_density = True
        ops.show_dialog = True

        ops = layout.operator(
            MUV_OT_WorldScaleUV_ApplyScalingDensity.bl_idname,
            text="Apply (Scaling Desity)")
        ops.src_density = sc.muv_world_scale_uv_src_density
        ops.same_density = False
        ops.show_dialog = True

        ops = layout.operator(
            MUV_OT_WorldScaleUV_ApplyProportionalToMesh.bl_idname,
            text="Apply (Proportional to Mesh)")
        ops.src_density = sc.muv_world_scale_uv_src_density
        ops.src_uv_area = sc.muv_world_scale_uv_src_uv_area
        ops.src_mesh_area = sc.muv_world_scale_uv_src_mesh_area
        ops.show_dialog = True


@BlClassRegistry()
class MUV_MT_TextureWrap(bpy.types.Menu):
    """
    Menu class: Master menu of Texture Wrap
    """

    bl_idname = "MUV_MT_TextureWrap"
    bl_label = "Texture Wrap"
    bl_description = ""

    def draw(self, _):
        layout = self.layout

        layout.operator(MUV_OT_TextureWrap_Refer.bl_idname, text="Refer")
        layout.operator(MUV_OT_TextureWrap_Set.bl_idname, text="Set")


@BlClassRegistry()
class MUV_MT_UVW(bpy.types.Menu):
    """
    Menu class: Master menu of UVW
    """

    bl_idname = "MUV_MT_UVW"
    bl_label = "UVW"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        ops = layout.operator(MUV_OT_UVW_BoxMap.bl_idname, text="Box")
        ops.assign_uvmap = sc.muv_uvw_assign_uvmap

        ops = layout.operator(MUV_OT_UVW_BestPlanerMap.bl_idname,
                              text="Best Planner")
        ops.assign_uvmap = sc.muv_uvw_assign_uvmap


@BlClassRegistry()
class MUV_MT_PreserveUVAspect(bpy.types.Menu):
    """
    Menu class: Master menu of Preserve UV Aspect
    """

    bl_idname = "MUV_MT_PreserveUVAspect"
    bl_label = "Preserve UV Aspect"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        for key in bpy.data.images.keys():
            ops = layout.operator(MUV_OT_PreserveUVAspect.bl_idname, text=key)
            ops.dest_img_name = key
            ops.origin = sc.muv_preserve_uv_aspect_origin


@BlClassRegistry()
class MUV_MT_TextureProjection(bpy.types.Menu):
    """
    Menu class: Master menu of Texture Projection
    """

    bl_idname = "MUV_MT_TextureProjection"
    bl_label = "Texture Projection"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.prop(sc, "muv_texture_projection_enable",
                    text="Texture Projection")
        layout.operator(MUV_OT_TextureProjection_Project.bl_idname,
                        text="Project")
