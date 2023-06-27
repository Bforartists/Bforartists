# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from ..op.copy_paste_uv_uvedit import (
    MUV_OT_CopyPasteUVUVEdit_CopyUV,
    MUV_OT_CopyPasteUVUVEdit_PasteUV,
    MUV_OT_CopyPasteUVUVEdit_CopyUVIsland,
    MUV_OT_CopyPasteUVUVEdit_PasteUVIsland,
)
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_UVEdit_CopyPasteUV(bpy.types.Panel):
    """
    Panel class: Copy/Paste UV on Property Panel on UV/ImageEditor
    """

    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Copy/Paste UV"
    bl_category = "Magic UV"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Face:")
        row = layout.row(align=True)
        row.operator(MUV_OT_CopyPasteUVUVEdit_CopyUV.bl_idname, text="Copy")
        row.operator(MUV_OT_CopyPasteUVUVEdit_PasteUV.bl_idname, text="Paste")

        layout.separator()

        layout.label(text="Island:")
        row = layout.row(align=True)
        row.operator(MUV_OT_CopyPasteUVUVEdit_CopyUVIsland.bl_idname,
                     text="Copy")
        ops = row.operator(MUV_OT_CopyPasteUVUVEdit_PasteUVIsland.bl_idname,
                           text="Paste")
        ops.unique_target = sc.muv_copy_paste_uv_uvedit_unique_target
        layout.prop(sc, "muv_copy_paste_uv_uvedit_unique_target")
