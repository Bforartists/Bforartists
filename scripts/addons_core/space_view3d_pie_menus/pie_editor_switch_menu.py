# SPDX-FileCopyrightText: 2016-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'Ctrl Alt S' ",
    "description": "Switch Editor Type Menu",
    "author": "saidenka, meta-androcto",
    "version": (0, 1, 2),
    "blender": (3, 40, 1),
    "location": "All Editors",
    "warning": "",
    "doc_url": "",
    "category": "Editor Switch Pie"
}

import bpy
from bpy.types import (
    Menu,
    Operator,
)
from bpy.props import (
    StringProperty,
)

# Pie Menu


class PIE_MT_AreaPieEditor(Menu):
    bl_idname = "PIE_MT_editor"
    bl_label = "Editor Switch"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator(PIE_OT_SetAreaType.bl_idname,
                     text="Video Sequence Editor", icon="SEQUENCE").types = "SEQUENCE_EDITOR"
        # 6 - RIGHT
        pie.menu(PIE_MT_AreaTypePieNode.bl_idname, text="Node Editors", icon="NODETREE")
        # 2 - BOTTOM
        pie.menu(PIE_MT_AreaTypePieOther.bl_idname, text="Script/Data Editors", icon="PREFERENCES")
        # 8 - TOP
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="3D View", icon="VIEW3D").types = "VIEW_3D"
        # 7 - TOP - LEFT
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="Image Editor", icon="IMAGE").types = "IMAGE_EDITOR"
        # 9 - TOP - RIGHT
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="UV Editor", icon="UV").types = "UV"
        # 1 - BOTTOM - LEFT
        pie.operator(PIE_OT_SetAreaType.bl_idname,
                     text="Movie Clip Editor", icon="TRACKER").types = "CLIP_EDITOR"
        # 3 - BOTTOM - RIGHT
        pie.menu(PIE_MT_AreaTypePieAnim.bl_idname, text="Animation Editors", icon="ACTION")

# Sub Menu Script/Data Editors


class PIE_MT_AreaTypePieOther(Menu):
    bl_idname = "TOPBAR_MT_window_pie_area_type_other"
    bl_label = "Editor Type (other)"
    bl_description = "Is pie menu change editor type (other)"

    def draw(self, context):
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Outliner", icon="OUTLINER").types = "OUTLINER"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Properties", icon="PROPERTIES").types = "PROPERTIES"
        self.layout.operator(
            PIE_OT_SetAreaType.bl_idname,
            text="File Browser",
            icon="FILEBROWSER").types = "FILES"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Preferences",
                             icon="PREFERENCES").types = "PREFERENCES"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Text Editor", icon="TEXT").types = "TEXT_EDITOR"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Python Console", icon="CONSOLE").types = "CONSOLE"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Info", icon="INFO").types = "INFO"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Spreadsheet", icon="SPREADSHEET").types = "SPREADSHEET"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Asset Browser", icon="ASSET_MANAGER").types = "ASSETS"


# Sub Menu Node editors.
class PIE_MT_AreaTypePieNode(Menu):
    bl_idname = "TOPBAR_MT_window_pie_area_type_node"
    bl_label = "Editor Type (Node)"
    bl_description = "Menu to change node editor types"

    def draw(self, context):
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Shader", icon="NODE_MATERIAL").types = "ShaderNodeTree"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Compositor",
                             icon="NODE_COMPOSITING").types = "CompositorNodeTree"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Texture",
                             icon="NODE_TEXTURE").types = "TextureNodeTree"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Geometry",
                             icon="NODETREE").types = "GeometryNodeTree"


# Sub Menu animation Editors.
class PIE_MT_AreaTypePieAnim(Menu):
    bl_idname = "TOPBAR_MT_window_pie_area_type_anim"
    bl_label = "Editor Type (Animation)"
    bl_description = "Menu for changing editor type (animation related)"

    def draw(self, context):
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="DopeSheet", icon="ACTION").types = "DOPESHEET"
        self.layout.operator(PIE_OT_Timeline.bl_idname, text="Timeline", icon="TIME")
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Graph Editor", icon="GRAPH").types = "FCURVES"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Drivers", icon="DRIVER").types = "DRIVERS"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="NLA Editor", icon="NLA").types = "NLA_EDITOR"


# Operators.
class PIE_OT_SetAreaType(Operator):
    bl_idname = "wm.set_area_type"
    bl_label = "Change Editor Type"
    bl_description = "Change Editor Type"
    bl_options = {'REGISTER'}

    types: StringProperty(name="Area Type")

    def execute(self, context):
        context.area.ui_type = self.types
        return {'FINISHED'}


class PIE_OT_Timeline(Operator):
    bl_idname = "wm.set_timeline"
    bl_label = "Change Editor Type"
    bl_description = "Change Editor Type"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.context.area.ui_type = 'TIMELINE'
        return {'FINISHED'}


classes = (
    PIE_MT_AreaPieEditor,
    PIE_MT_AreaTypePieOther,
    PIE_OT_SetAreaType,
    PIE_MT_AreaTypePieAnim,
    PIE_OT_Timeline,
    PIE_MT_AreaTypePieNode
)

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Snapping
        km = wm.keyconfigs.addon.keymaps.new(name='Window')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', ctrl=True, alt=True)
        kmi.properties.name = "PIE_MT_editor"
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
