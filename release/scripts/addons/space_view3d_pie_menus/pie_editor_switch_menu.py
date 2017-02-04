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
    #    "author": "saidenka",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
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


class AreaPieMenu(Menu):
    bl_idname = "INFO_MT_window_pie"
    bl_label = "Pie Menu"
    bl_description = "Window Pie Menus"

    def draw(self, context):
        self.layout.operator(AreaTypePieOperator.bl_idname, icon="PLUGIN")


class AreaTypePieOperator(Operator):
    bl_idname = "wm.area_type_pie_operator"
    bl_label = "Editor Type"
    bl_description = "This is pie menu of editor type change"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=AreaTypeEditor.bl_idname)
        return {'FINISHED'}


class AreaPieEditor(Menu):
    bl_idname = "pie.editor"
    bl_label = "Editor Switch"

    def draw(self, context):
        # 4 - LEFT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Text Editor", icon="TEXT").type = "TEXT_EDITOR"
        # 6 - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Outliner", icon="OOPS").type = "OUTLINER"
        # 2 - BOTTOM
        self.layout.menu_pie().operator("wm.call_menu_pie", text="More Types", icon="QUESTION").name = AreaTypePieOther.bl_idname
        # 8 - TOP
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="3D View", icon="MESH_CUBE").type = "VIEW_3D"
        # 7 - TOP - LEFT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="UV/Image Editor", icon="IMAGE_COL").type = "IMAGE_EDITOR"
        # 9 - TOP - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Node Editor", icon="NODETREE").type = "NODE_EDITOR"
        # 1 - BOTTOM - LEFT
        self.layout.menu_pie().operator("wm.call_menu_pie", text="Animation Pie", icon="ACTION").name = AreaTypePieAnim.bl_idname
        # 3 - BOTTOM - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Property", icon="BUTS").type = "PROPERTIES"


class AreaTypePieOther(Menu):
    bl_idname = "INFO_MT_window_pie_area_type_other"
    bl_label = "Editor Type (other)"
    bl_description = "Is pie menu change editor type (other)"

    def draw(self, context):
        # 4 - LEFT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Logic Editor", icon="LOGIC").type = "LOGIC_EDITOR"
        # 6 - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="File Browser", icon="FILESEL").type = "FILE_BROWSER"
        # 2 - BOTTOM
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Python Console", icon="CONSOLE").type = "CONSOLE"
        # 8 - TOP
        self.layout.menu_pie().operator("wm.call_menu_pie", text="Back", icon="BACK").name = AreaPieEditor.bl_idname
        # 7 - TOP - LEFT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="User Setting", icon="PREFERENCES").type = "USER_PREFERENCES"
        # 9 - TOP - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Info", icon="INFO").type = "INFO"
        # 1 - BOTTOM - LEFT
        # 3 - BOTTOM - RIGHT


class SetAreaType(Operator):
    bl_idname = "wm.set_area_type"
    bl_label = "Change Editor Type"
    bl_description = "Change Editor Type"
    bl_options = {'REGISTER'}

    type = StringProperty(name="Area Type")

    def execute(self, context):
        context.area.type = self.type
        return {'FINISHED'}


class AreaTypePieAnim(Menu):
    bl_idname = "INFO_MT_window_pie_area_type_anim"
    bl_label = "Editor Type (Animation)"
    bl_description = "Is pie menu change editor type (animation related)"

    def draw(self, context):
        # 4 - LEFT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="NLA Editor", icon="NLA").type = "NLA_EDITOR"
        # 6 - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="DopeSheet", icon="ACTION").type = "DOPESHEET_EDITOR"
        # 2 - BOTTOM
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Graph Editor", icon="IPO").type = "GRAPH_EDITOR"
        # 8 - TOP
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Timeline", icon="TIME").type = "TIMELINE"
        # 7 - TOP - LEFT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Video Sequence Editor", icon="SEQUENCE").type = "SEQUENCE_EDITOR"
        # 9 - TOP - RIGHT
        self.layout.menu_pie().operator(SetAreaType.bl_idname, text="Video Clip Editor", icon="RENDER_ANIMATION").type = "CLIP_EDITOR"
        # 1 - BOTTOM - LEFT
        self.layout.menu_pie().operator("wm.call_menu_pie", text="Back", icon="BACK").name = PieEditor.bl_idname
        # 3 - BOTTOM - RIGHT

classes = (
    AreaPieMenu,
    AreaTypePieOperator,
    AreaPieEditor,
    AreaTypePieOther,
    SetAreaType,
    AreaTypePieAnim,
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
        kmi.properties.name = "pie.editor"
#        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Window']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "wm.area_type_pie_operator":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
