#re creating the functionality of the manipulator menu from 2.49

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


bl_info = {
    "name": "3d View: Manipulator Menu",
    "author": "MichaelW",
    "version": (1, 2, 1),
    "blender": (2, 61, 0),
    "location": "View3D > Ctrl Space ",
    "description": "Menu to change the manipulator type and/or disable it",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Manipulator_Menu",
    "tracker_url": "https://developer.blender.org/T22092",
    "category": "3D View"}


import bpy

def main(context):
    bpy.context.space_data.manipulator = False

#class VIEW3D_OT_disable_manipulator(bpy.types.Operator):
#    """"""
#    bl_idname = "VIEW3D_OT_disable_manipulator"
#    bl_label = "disable manipulator"
#
#    def poll(self, context):
#        return context.active_object != None
#
#    def execute(self, context):
#        main(context)
#        return {'FINISHED'}
#


class VIEW3D_MT_ManipulatorMenu(bpy.types.Menu):
    bl_label = "ManipulatorType"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        props = layout.operator("view3d.enable_manipulator",text ='Translate', icon='MAN_TRANS')
        props.translate = True

        props = layout.operator("view3d.enable_manipulator",text ='Rotate', icon='MAN_ROT')
        props.rotate = True

        props = layout.operator("view3d.enable_manipulator",text ='Scale', icon='MAN_SCALE')
        props.scale = True
        layout.separator()

        props = layout.operator("view3d.enable_manipulator",text ='Combo', icon='MAN_SCALE')
        props.scale = True
        props.rotate = True
        props.translate = True

        layout.separator()

        props = layout.operator("view3d.enable_manipulator",text ='Hide', icon='MAN_SCALE')
        props.scale = False
        props.rotate = False
        props.translate = False

        layout.separator()



def register():
    bpy.utils.register_module(__name__)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
    kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS', ctrl=True)
    kmi.properties.name = "VIEW3D_MT_ManipulatorMenu"


def unregister():
    bpy.utils.unregister_module(__name__)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps['3D View Generic']
    for kmi in km.keymap_items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == "VIEW3D_MT_ManipulatorMenu":
                km.keymap_items.remove(kmi)
                break

if __name__ == "__main__":
    register
