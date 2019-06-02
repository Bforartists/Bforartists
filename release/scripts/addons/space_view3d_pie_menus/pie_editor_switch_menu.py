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

# <pep8 compliant>

bl_info = {
    "name": "Hotkey: 'Ctrl Alt S ",
    "description": "Switch Editor Type Menu",
    "author": "saidenka, meta-androcto",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "All Editors",
    "warning": "",
    "wiki_url": "",
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


class PIE_MT_AreaPieMenu(Menu):
    bl_idname = "TOPBAR_MT_window_pie"
    bl_label = "Pie Menu"
    bl_description = "Window Pie Menus"

    def draw(self, context):
        self.layout.operator(PIE_OT_AreaTypePieOperator.bl_idname, icon="PLUGIN")


class PIE_OT_AreaTypePieOperator(Operator):
    bl_idname = "wm.area_type_pie_operator"
    bl_label = "Editor Type"
    bl_description = "This is pie menu of editor type change"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=PIE_MT_AreaPieEditor.bl_idname)

        return {'FINISHED'}


class PIE_MT_AreaPieEditor(Menu):
    bl_idname = "PIE_MT_editor"
    bl_label = "Editor Switch"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="Text Editor", icon="TEXT").types = "TEXT_EDITOR"
        # 6 - RIGHT
        pie.menu(PIE_MT_AreaTypePieAnim.bl_idname, text="Animation Editors", icon="ACTION")
        # 2 - BOTTOM
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="Property", icon="PROPERTIES").types = "PROPERTIES"
        # 8 - TOP
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="3D View", icon="MESH_CUBE").types = "VIEW_3D"
        # 7 - TOP - LEFT
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="UV/Image Editor", icon="UV").types = "IMAGE_EDITOR"
        # 9 - TOP - RIGHT
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="Node Editor", icon="NODETREE").types = "NODE_EDITOR"
        # 1 - BOTTOM - LEFT
        pie.operator(PIE_OT_SetAreaType.bl_idname, text="Outliner", icon="OUTLINER").types = "OUTLINER"
        # 3 - BOTTOM - RIGHT
        pie.menu(PIE_MT_AreaTypePieOther.bl_idname, text="More Editors", icon="QUESTION")


class PIE_MT_AreaTypePieOther(Menu):
    bl_idname = "TOPBAR_MT_window_pie_area_type_other"
    bl_label = "Editor Type (other)"
    bl_description = "Is pie menu change editor type (other)"

    def draw(self, context):
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="File Browser", icon="FILEBROWSER").types = "FILE_BROWSER"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Python Console", icon="CONSOLE").types = "CONSOLE"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="User Preferences",
                             icon="PREFERENCES").types = "USER_PREFERENCES"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Info", icon="INFO").types = "INFO"


class PIE_OT_SetAreaType(Operator):
    bl_idname = "wm.set_area_type"
    bl_label = "Change Editor Type"
    bl_description = "Change Editor Type"
    bl_options = {'REGISTER'}

    types: StringProperty(name="Area Type")

    def execute(self, context):
        context.area.type = self.types
        return {'FINISHED'}


class PIE_MT_AreaTypePieAnim(Menu):
    bl_idname = "TOPBAR_MT_window_pie_area_type_anim"
    bl_label = "Editor Type (Animation)"
    bl_description = "Menu for changing editor type (animation related)"

    def draw(self, context):
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="NLA Editor", icon="NLA").types = "NLA_EDITOR"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="DopeSheet", icon="ACTION").types = "DOPESHEET_EDITOR"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Graph Editor", icon="GRAPH").types = "GRAPH_EDITOR"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname, text="Timeline", icon="TIME").types = "TIMELINE"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname,
                             text="Video Sequence Editor", icon="SEQUENCE").types = "SEQUENCE_EDITOR"
        self.layout.operator(PIE_OT_SetAreaType.bl_idname,
                             text="Video Clip Editor", icon="RENDER_ANIMATION").types = "CLIP_EDITOR"


classes = (
    PIE_MT_AreaPieMenu,
    PIE_OT_AreaTypePieOperator,
    PIE_MT_AreaPieEditor,
    PIE_MT_AreaTypePieOther,
    PIE_OT_SetAreaType,
    PIE_MT_AreaTypePieAnim,
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
