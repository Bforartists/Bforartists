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


@BlClassRegistry()
class MUV_MT_CopyPasteUV_Object(bpy.types.Menu):
    """
    Menu class: Master menu of Copy/Paste UV coordinate among object
    """

    bl_idname = "MUV_MT_CopyPasteUV_Object"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV coordinate among object"

    def draw(self, _):
        layout = self.layout

        layout.menu(MUV_MT_CopyPasteUVObject_CopyUV.bl_idname, text="Copy")
        layout.menu(MUV_MT_CopyPasteUVObject_PasteUV.bl_idname, text="Paste")
