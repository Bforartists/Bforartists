# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import (
    BoolProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

class CarverPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    Enable_Tab_01: BoolProperty(
        name="Info",
        description="Some general information and settings about the add-on",
        default=False
    )
    Enable_Tab_02: BoolProperty(
        name="Hotkeys",
        description="List of the shortcuts used during carving",
        default=False
    )
    bpy.types.Scene.Key_Create: StringProperty(
        name="Object creation",
        description="Object creation",
        maxlen=1,
        default="C"
    )
    bpy.types.Scene.Key_Update: StringProperty(
        name="Auto Bevel Update",
        description="Auto Bevel Update",
        maxlen=1,
        default="A",
    )
    bpy.types.Scene.Key_Bool: StringProperty(
        name="Boolean type",
        description="Boolean operation type",
        maxlen=1,
        default="T",
    )
    bpy.types.Scene.Key_Brush: StringProperty(
            name="Brush Mode",
            description="Brush Mode",
            maxlen=1,
            default="B",
    )
    bpy.types.Scene.Key_Help: StringProperty(
        name="Help display",
        description="Help display",
        maxlen=1,
        default="H",
    )
    bpy.types.Scene.Key_Instant: StringProperty(
        name="Instantiate",
        description="Instantiate object",
        maxlen=1,
        default="I",
    )
    bpy.types.Scene.Key_Close: StringProperty(
        name="Close polygonal shape",
        description="Close polygonal shape",
        maxlen=1,
        default="X",
    )
    bpy.types.Scene.Key_Apply: StringProperty(
        name="Apply operation",
        description="Apply operation",
        maxlen=1,
        default="Q",
    )
    bpy.types.Scene.Key_Scale: StringProperty(
        name="Scale object",
        description="Scale object",
        maxlen=1,
        default="S",
    )
    bpy.types.Scene.Key_Gapy: StringProperty(
        name="Gap rows",
        description="Scale gap between columns",
        maxlen=1,
        default="J",
    )
    bpy.types.Scene.Key_Gapx: StringProperty(
        name="Gap columns",
        description="Scale gap between columns",
        maxlen=1,
        default="U",
    )
    bpy.types.Scene.Key_Depth: StringProperty(
        name="Depth",
        description="Cursor depth or solidify pattern",
        maxlen=1,
        default="D",
    )
    bpy.types.Scene.Key_BrushDepth: StringProperty(
        name="Brush Depth",
        description="Brush depth",
        maxlen=1,
        default="C",
    )
    bpy.types.Scene.Key_Subadd: StringProperty(
        name="Add subdivision",
        description="Add subdivision",
        maxlen=1,
        default="X",
    )
    bpy.types.Scene.Key_Subrem: StringProperty(
        name="Remove subdivision",
        description="Remove subdivision",
        maxlen=1,
        default="W",
    )
    bpy.types.Scene.Key_Randrot: StringProperty(
        name="Random rotation",
        description="Random rotation",
        maxlen=1,
        default="R",
    )
    bpy.types.Scene.ProfilePrefix: StringProperty(
        name="Profile prefix",
        description="Prefix to look for profiles with",
        default="Carver_Profile-"
    )

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        print("DRAW !")

        icon_1 = "TRIA_RIGHT" if not self.Enable_Tab_01 else "TRIA_DOWN"
        box = layout.box()

        box.prop(self, "Enable_Tab_01", text="Info and Settings", emboss=False, icon=icon_1)
        if self.Enable_Tab_01:
            box.label(text="Carver Operator:", icon="LAYER_ACTIVE")
            box.label(text="Select a Mesh Object and press [CTRL]+[SHIFT]+[X] to carve",
                         icon="LAYER_USED")
            box.label(text="To finish carving press [ESC] or [RIGHT CLICK]",
                         icon="LAYER_USED")
            box.prop(scene, "ProfilePrefix", text="Profile prefix")

        icon_2 = "TRIA_RIGHT" if not self.Enable_Tab_02 else "TRIA_DOWN"
        box = layout.box()
        box.prop(self, "Enable_Tab_02", text="Keys", emboss=False, icon=icon_2)
        if self.Enable_Tab_02:
            split = box.split(align=True)
            box = split.box()
            col = box.column(align=True)
            col.label(text="Object Creation:")
            col.prop(scene, "Key_Create", text="")
            col.label(text="Auto bevel update:")
            col.prop(scene, "Key_Update", text="")
            col.label(text="Boolean operation type:")
            col.prop(scene, "Key_Bool", text="")
            col.label(text="Brush Depth:")
            col.prop(scene, "Key_BrushDepth", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Brush Mode:")
            col.prop(scene, "Key_Brush", text="")
            col.label(text="Help display:")
            col.prop(scene, "Key_Help", text="")
            col.label(text="Instantiate object:")
            col.prop(scene, "Key_Instant", text="")
            col.label(text="Random rotation:")
            col.prop(scene, "Key_Randrot", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Close polygonal shape:")
            col.prop(scene, "Key_Close", text="")
            col.label(text="Apply operation:")
            col.prop(scene, "Key_Apply", text="")
            col.label(text="Scale object:")
            col.prop(scene, "Key_Scale", text="")
            col.label(text="Subdiv add:")
            col.prop(scene, "Key_Subadd", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Gap rows:")
            col.prop(scene, "Key_Gapy", text="")
            col.label(text="Gap columns:")
            col.prop(scene, "Key_Gapx", text="")
            col.label(text="Depth / Solidify:")
            col.prop(scene, "Key_Depth", text="")
            col.label(text="Subdiv Remove:")
            col.prop(scene, "Key_Subrem", text="")

def register():
    bpy.utils.register_class(CarverPrefs)

def unregister():
    bpy.utils.unregister_class(CarverPrefs)
