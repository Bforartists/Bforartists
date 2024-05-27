# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Carver",
    "author": "Pixivore, Cedric LEPILLER, Ted Milker, Clarkx",
    "description": "Multiple tools to carve or to create objects",
    "version": (1, 2, 2),
    "blender": (3, 4, 0),
    "location": "3D View > Ctrl/Shift/x",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/object/carver.html",
    "support": 'COMMUNITY',
    "category": "Object"
    }

if "bpy" in locals():
    import importlib

    importlib.reload(carver_utils)
    importlib.reload(carver_profils)
    importlib.reload(carver_draw)
    importlib.reload(carver_operator)

import bpy

from bpy.props import (
        BoolProperty,
        StringProperty,
        IntProperty
)
from bpy.types import (AddonPreferences, WorkSpaceTool)
from bpy.utils.toolsystem import ToolDef

from . import (
    carver_utils,
    carver_profils,
    carver_draw,
    carver_operator,
)

# TODO : Create an icon for Carver MT
# Add an icon in the toolbar
# class CarverTool(WorkSpaceTool):
#     bl_space_type='VIEW_3D'
#     bl_context_mode='OBJECT'
#     bl_idname = "carver.operator"
#     bl_label = "Carver"
#     bl_description = (
#         "Multiple tools to carve \n"
#         "or to create objects"
#     )
#
#   #Icons : \blender-2.80\2.80\datafiles\icons
#   #Todo: Create a new icon for Carver
#     bl_icon = "ops.mesh.knife_tool"
#     bl_widget = None
#     bl_keymap = (
#         ("carver.operator", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
#       )
#
#     def draw_settings(context, layout, tool):
#         layout.prop(tool.operator_properties, "carver")


class CarverPreferences(AddonPreferences):
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
    Key_Create: StringProperty(
        name="Object creation",
        description="Object creation",
        maxlen=1,
        default="C"
    )
    Key_Update: StringProperty(
        name="Auto Bevel Update",
        description="Auto Bevel Update",
        maxlen=1,
        default="A",
    )
    Key_Bool: StringProperty(
        name="Boolean type",
        description="Boolean operation type",
        maxlen=1,
        default="T",
    )
    Key_Brush: StringProperty(
            name="Brush Mode",
            description="Brush Mode",
            maxlen=1,
            default="B",
    )
    Key_Help: StringProperty(
        name="Help display",
        description="Help display",
        maxlen=1,
        default="H",
    )
    Key_Instant: StringProperty(
        name="Instantiate",
        description="Instantiate object",
        maxlen=1,
        default="I",
    )
    Key_Close: StringProperty(
        name="Close polygonal shape",
        description="Close polygonal shape",
        maxlen=1,
        default="X",
    )
    Key_Apply: StringProperty(
        name="Apply operation",
        description="Apply operation",
        maxlen=1,
        default="Q",
    )
    Key_Scale: StringProperty(
        name="Scale object",
        description="Scale object",
        maxlen=1,
        default="S",
    )
    Key_Gapy: StringProperty(
        name="Gap rows",
        description="Scale gap between columns",
        maxlen=1,
        default="J",
    )
    Key_Gapx: StringProperty(
        name="Gap columns",
        description="Scale gap between columns",
        maxlen=1,
        default="U",
    )
    Key_Depth: StringProperty(
        name="Depth",
        description="Cursor depth or solidify pattern",
        maxlen=1,
        default="D",
    )
    Key_BrushDepth: StringProperty(
        name="Brush Depth",
        description="Brush depth",
        maxlen=1,
        default="C",
    )
    Key_Subadd: StringProperty(
        name="Add subdivision",
        description="Add subdivision",
        maxlen=1,
        default="X",
    )
    Key_Subrem: StringProperty(
        name="Remove subdivision",
        description="Remove subdivision",
        maxlen=1,
        default="W",
    )
    Key_Randrot: StringProperty(
        name="Random rotation",
        description="Random rotation",
        maxlen=1,
        default="R",
    )
    ProfilePrefix: StringProperty(
        name="Profile prefix",
        description="Prefix to look for profiles with",
        default="Carver_Profile-",
    )
    LineWidth: IntProperty(
        name="Line Width",
        description="Thickness of the drawing lines",
        default=1,
    )
    Key_Snap: StringProperty(
        name="Grid Snap",
        description="Grid Snap",
        maxlen=1,
        default="G",
    )

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        icon_1 = "TRIA_RIGHT" if not self.Enable_Tab_01 else "TRIA_DOWN"
        box = layout.box()

        box.prop(self, "Enable_Tab_01", text="Info and Settings", emboss=False, icon=icon_1)
        if self.Enable_Tab_01:
            box.label(text="Carver Operator:", icon="LAYER_ACTIVE")
            box.label(text="Select a Mesh Object and press [CTRL]+[SHIFT]+[X] to carve",
                         icon="LAYER_USED")
            box.label(text="To finish carving press [ESC] or [RIGHT CLICK]",
                         icon="LAYER_USED")
            box.prop(self, "ProfilePrefix", text="Profile prefix")
            row = box.row(align=True)
            row.label(text="Line width:")
            row.prop(self, "LineWidth", text="")

        icon_2 = "TRIA_RIGHT" if not self.Enable_Tab_02 else "TRIA_DOWN"
        box = layout.box()
        box.prop(self, "Enable_Tab_02", text="Keys", emboss=False, icon=icon_2)
        if self.Enable_Tab_02:
            split = box.split(align=True)
            box = split.box()
            col = box.column(align=True)
            col.label(text="Object Creation:")
            col.prop(self, "Key_Create", text="")
            col.label(text="Auto bevel update:")
            col.prop(self, "Key_Update", text="")
            col.label(text="Boolean operation type:")
            col.prop(self, "Key_Bool", text="")
            col.label(text="Brush Depth:")
            col.prop(self, "Key_BrushDepth", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Brush Mode:")
            col.prop(self, "Key_Brush", text="")
            col.label(text="Help display:")
            col.prop(self, "Key_Help", text="")
            col.label(text="Instantiate object:")
            col.prop(self, "Key_Instant", text="")
            col.label(text="Random rotation:")
            col.prop(self, "Key_Randrot", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Close polygonal shape:")
            col.prop(self, "Key_Close", text="")
            col.label(text="Apply operation:")
            col.prop(self, "Key_Apply", text="")
            col.label(text="Scale object:")
            col.prop(self, "Key_Scale", text="")
            col.label(text="Subdiv add:")
            col.prop(self, "Key_Subadd", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Gap rows:")
            col.prop(self, "Key_Gapy", text="")
            col.label(text="Gap columns:")
            col.prop(self, "Key_Gapx", text="")
            col.label(text="Depth / Solidify:")
            col.prop(self, "Key_Depth", text="")
            col.label(text="Subdiv Remove:")
            col.prop(self, "Key_Subrem", text="")

            box = split.box()
            col = box.column(align=True)
            col.label(text="Grid Snap:")
            col.prop(self, "Key_Snap", text="")

addon_keymaps = []

def register():
    # print("Registered Carver")

    bpy.utils.register_class(CarverPreferences)
    # Todo : Add an icon in the toolbat
    # bpy.utils.register_tool(CarverTool, separator=True, group=True)
    carver_operator.register()

    # add keymap entry
    kcfg = bpy.context.window_manager.keyconfigs.addon
    if kcfg:
        km = kcfg.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("carver.operator", 'X', 'PRESS', shift=True, ctrl=True)
        addon_keymaps.append((km, kmi))

def unregister():
    # Todo : Add an icon in the toolbat
    # bpy.utils.unregister_tool(CarverTool)
    carver_operator.unregister()
    bpy.utils.unregister_class(CarverPreferences)

    # print("Unregistered Carver")

    # remove keymap entry
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()



if __name__ == "__main__":
    register()
