# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from ..op.copy_paste_uv_object import (
    MUV_MT_CopyPasteUVObject_CopyUV,
    MUV_MT_CopyPasteUVObject_PasteUV,
)
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_View3D_Object_CopyPasteUV(bpy.types.Panel):
    """
    Panel class: Copy/Paste UV on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Copy/Paste UV"
    bl_category = "Edit"
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        row = layout.row(align=True)
        row.menu(MUV_MT_CopyPasteUVObject_CopyUV.bl_idname, text="Copy")
        row.menu(MUV_MT_CopyPasteUVObject_PasteUV.bl_idname, text="Paste")
        layout.prop(sc, "muv_copy_paste_uv_object_copy_seams",
                    text="Seams")
