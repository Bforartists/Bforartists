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
    "name": "Hotkey: 'Ctrl Space'",
    "description": "Extended Manipulator Menu",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Manipulator Pie"
    }

import bpy
from bpy.types import (
    Menu,
    Operator,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
)


class PIE_OT_WManupulators(Operator):
    bl_idname = "w.manipulators"
    bl_label = "W Manupulators"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = " Show/Hide Manipulator"

    extend: BoolProperty(
        default=False,
    )
    type: EnumProperty(
        items=(
            ('TRANSLATE', "Move", ""),
            ('ROTATE', "Rotate", ""),
            ('SCALE', "Scale", ""),
        )
    )

    def execute(self, context):
        space_data = context.space_data
        space_data.show_gizmo_context = True

        attrs = (
            "show_gizmo_object_translate",
            "show_gizmo_object_rotate",
            "show_gizmo_object_scale",
        )
        attr_t, attr_r, attr_s = attrs
        attr_index = ('TRANSLATE', 'ROTATE', 'SCALE').index(self.type)
        attr_active = attrs[attr_index]

        if self.extend:
            setattr(space_data, attr_active, not getattr(space_data, attr_active))
        else:
            for attr in attrs:
                setattr(space_data, attr, attr == attr_active)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)


# Pie Manipulators - Ctrl + Space
class PIE_MT_Manipulator(Menu):
    bl_idname = "PIE_MT_manipulator"
    bl_label = "Pie Manipulator"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("w.manipulators", text="Translate", icon='NONE').type = 'TRANSLATE'
        # 6 - RIGHT
        pie.operator("w.manipulators", text="Rotate", icon='NONE').type = 'ROTATE'
        # 2 - BOTTOM
        pie.operator("w.manipulators", text="Scale", icon='NONE').type = 'SCALE'
        # 8 - TOP
        props = pie.operator("wm.context_toggle", text="Show/Hide Toggle", icon='NONE')
        props.data_path = "space_data.show_gizmo_context"


classes = (
    PIE_OT_WManupulators,
    PIE_MT_Manipulator,
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Manipulators
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', ctrl=True)
        kmi.properties.name = "PIE_MT_manipulator"
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
