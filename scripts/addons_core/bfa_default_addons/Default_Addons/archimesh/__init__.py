# SPDX-FileCopyrightText: 2016-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------------------
# Author: Antonio Vazquez (antonioya)
# ----------------------------------------------------------

# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
    "name": "Archimesh",
    "author": "Antonio Vazquez (antonioya)",
    "location": "View3D > Add Mesh / Sidebar > Create Tab",
    "version": (1, 2, 5),
    "blender": (3, 0, 0),
    "description": "Generate rooms, doors, windows, and other architecture objects",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_mesh/archimesh.html",
    "category": "Add Mesh"
    }

import sys
import os

# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import importlib
    importlib.reload(achm_room_maker)
    importlib.reload(achm_door_maker)
    importlib.reload(achm_window_maker)
    importlib.reload(achm_roof_maker)
    importlib.reload(achm_column_maker)
    importlib.reload(achm_stairs_maker)
    importlib.reload(achm_kitchen_maker)
    importlib.reload(achm_shelves_maker)
    importlib.reload(achm_books_maker)
    importlib.reload(achm_lamp_maker)
    importlib.reload(achm_curtain_maker)
    importlib.reload(achm_venetian_maker)
    importlib.reload(achm_main_panel)
    importlib.reload(achm_window_panel)
    # print("archimesh: Reloaded multifiles")
else:
    from . import achm_books_maker
    from . import achm_column_maker
    from . import achm_curtain_maker
    from . import achm_venetian_maker
    from . import achm_door_maker
    from . import achm_kitchen_maker
    from . import achm_lamp_maker
    from . import achm_main_panel
    from . import achm_roof_maker
    from . import achm_room_maker
    from . import achm_shelves_maker
    from . import achm_stairs_maker
    from . import achm_window_maker
    from . import achm_window_panel

    # print("archimesh: Imported multifiles")

# noinspection PyUnresolvedReferences
import bpy
# noinspection PyUnresolvedReferences
from bpy.props import (
        BoolProperty,
        FloatVectorProperty,
        IntProperty,
        FloatProperty,
        StringProperty,
        )
# noinspection PyUnresolvedReferences
from bpy.types import (
        AddonPreferences,
        Menu,
        Scene,
        VIEW3D_MT_mesh_add,
        WindowManager,
        )

# ----------------------------------------------------------
# Decoration assets
# ----------------------------------------------------------


class ARCHIMESH_MT_MeshDecorationAdd(Menu):
    bl_idname = "VIEW3D_MT_mesh_decoration_add"
    bl_label = "Decoration assets"

    # noinspection PyUnusedLocal
    def draw(self, context):
        self.layout.operator("mesh.archimesh_books", text="Books")
        self.layout.operator("mesh.archimesh_light", text="Lamp")
        self.layout.operator("mesh.archimesh_roller", text="Roller curtains")
        self.layout.operator("mesh.archimesh_venetian", text="Venetian blind")
        self.layout.operator("mesh.archimesh_japan", text="Japanese curtains")

# ----------------------------------------------------------
# Registration
# ----------------------------------------------------------


class ARCHIMESH_MT_CustomMenuAdd(Menu):
    bl_idname = "VIEW3D_MT_mesh_custom_menu_add"
    bl_label = "Archimesh"

    # noinspection PyUnusedLocal
    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator("mesh.archimesh_room", text="Room")
        self.layout.operator("mesh.archimesh_door", text="Door")
        self.layout.operator("mesh.archimesh_window", text="Rail Window")
        self.layout.operator("mesh.archimesh_winpanel", text="Panel Window")
        self.layout.operator("mesh.archimesh_kitchen", text="Cabinet")
        self.layout.operator("mesh.archimesh_shelves", text="Shelves")
        self.layout.operator("mesh.archimesh_column", text="Column")
        self.layout.operator("mesh.archimesh_stairs", text="Stairs")
        self.layout.operator("mesh.archimesh_roof", text="Roof")
        self.layout.menu("VIEW3D_MT_mesh_decoration_add", text="Decoration props", icon="GROUP")

# --------------------------------------------------------------
# Register all operators and panels
# --------------------------------------------------------------

# Define menu
# noinspection PyUnusedLocal
def AchmMenu_func(self, context):
    layout = self.layout
    layout.separator()
    self.layout.menu("VIEW3D_MT_mesh_custom_menu_add", icon="GROUP")


classes = (
    ARCHIMESH_MT_CustomMenuAdd,
    ARCHIMESH_MT_MeshDecorationAdd,
    achm_room_maker.ARCHIMESH_OT_Room,
    achm_room_maker.ARCHIMESH_PT_RoomGenerator,
    achm_room_maker.ARCHIMESH_OT_ExportRoom,
    achm_room_maker.ARCHIMESH_OT_ImportRoom,
    achm_door_maker.ARCHIMESH_OT_Door,
    achm_door_maker.ARCHIMESH_PT_DoorObjectgenerator,
    achm_window_maker.ARCHIMESH_OT_Windows,
    achm_window_maker.ARCHIMESH_PT_WindowObjectgenerator,
    achm_roof_maker.ARCHIMESH_OT_Roof,
    achm_column_maker.ARCHIMESH_OT_Column,
    achm_stairs_maker.ARCHIMESH_OT_Stairs,
    achm_kitchen_maker.ARCHIMESH_OT_Kitchen,
    achm_kitchen_maker.ARCHIMESH_OT_ExportInventory,
    achm_shelves_maker.ARCHIMESH_OT_Shelves,
    achm_books_maker.ARCHIMESH_OT_Books,
    achm_lamp_maker.ARCHIMESH_PT_Lamp,
    achm_curtain_maker.ARCHIMESH_OT_Roller,
    achm_curtain_maker.ARCHIMESH_OT_Japan,
    achm_venetian_maker.ARCHIMESH_OT_Venetian,
    achm_venetian_maker.ARCHIMESH_PT_VenetianObjectgenerator,
    achm_main_panel.ARCHIMESH_PT_Main,
    achm_main_panel.ARCHIMESH_OT_Hole,
    achm_main_panel.ARCHIMESH_OT_Pencil,
    achm_main_panel.ARCHIMESH_OT_HintDisplay,
    achm_window_panel.ARCHIMESH_PT_Win,
    achm_window_panel.ARCHIMESH_PT_WindowEdit
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    VIEW3D_MT_mesh_add.append(AchmMenu_func)

    # Define properties
    Scene.archimesh_select_only = BoolProperty(
            name="Only selected",
            description="Apply auto holes only to selected objects",
            default=False,
            )
    Scene.archimesh_ceiling = BoolProperty(
            name="Ceiling",
            description="Create a ceiling",
            default=False,
            )
    Scene.archimesh_floor = BoolProperty(
            name="Floor",
            description="Create a floor automatically",
            default=False,
            )

    Scene.archimesh_merge = BoolProperty(
            name="Close walls",
            description="Close walls to create a full closed room",
            default=False,
            )

    Scene.archimesh_text_color = FloatVectorProperty(
            name="Hint color",
            description="Color for the text and lines",
            default=(0.173, 0.545, 1.0, 1.0),
            min=0.1,
            max=1,
            subtype='COLOR',
            size=4,
            )
    Scene.archimesh_walltext_color = FloatVectorProperty(
            name="Hint color",
            description="Color for the wall label",
            default=(1, 0.8, 0.1, 1.0),
            min=0.1,
            max=1,
            subtype='COLOR',
            size=4,
            )
    Scene.archimesh_font_size = IntProperty(
            name="Text Size",
            description="Text size for hints",
            default=14, min=10, max=150,
            )
    Scene.archimesh_wfont_size = IntProperty(
            name="Text Size",
            description="Text size for wall labels",
            default=16, min=10, max=150,
            )
    Scene.archimesh_hint_space = FloatProperty(
            name='Separation', min=0, max=5, default=0.1,
            precision=2,
            description='Distance from object to display hint',
            )
    Scene.archimesh_gl_measure = BoolProperty(
            name="Measures",
            description="Display measures",
            default=True,
            )
    Scene.archimesh_gl_name = BoolProperty(
            name="Names",
            description="Display names",
            default=True,
            )
    Scene.archimesh_gl_ghost = BoolProperty(
            name="All",
            description="Display measures for all objects,"
            " not only selected",
            default=True,
            )

    # OpenGL flag
    wm = WindowManager
    # register internal property
    wm.archimesh_run_opengl = BoolProperty(default=False)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    VIEW3D_MT_mesh_add.remove(AchmMenu_func)

    # Remove properties
    del Scene.archimesh_select_only
    del Scene.archimesh_ceiling
    del Scene.archimesh_floor
    del Scene.archimesh_merge
    del Scene.archimesh_text_color
    del Scene.archimesh_walltext_color
    del Scene.archimesh_font_size
    del Scene.archimesh_wfont_size
    del Scene.archimesh_hint_space
    del Scene.archimesh_gl_measure
    del Scene.archimesh_gl_name
    del Scene.archimesh_gl_ghost
    # remove OpenGL data
    achm_main_panel.ARCHIMESH_OT_HintDisplay.handle_remove(achm_main_panel.ARCHIMESH_OT_HintDisplay, bpy.context)
    wm = bpy.context.window_manager
    p = 'archimesh_run_opengl'
    if p in wm:
        del wm[p]


if __name__ == '__main__':
    register()
