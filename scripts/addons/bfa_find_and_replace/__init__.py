# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "BFA Find and Replace",
    "author" : "Blenux (Juso3D)",
    "description" : "A Popup Panel for Find and Replace",
    "blender" : (3, 0, 0),
    "version" : (1, 0, 0),
    "location" : "Text Editor via Keymap (Check Addon Preferences)",
    "warning" : "",
    "doc_url": "",
    "tracker_url": "",
    "category" : "Text Editor"
}


import bpy
import bpy.utils.previews


addon_keymaps = {}
_icons = None


def find_user_keyconfig(key):
    km, kmi = addon_keymaps[key]
    for item in bpy.context.window_manager.keyconfigs.user.keymaps[km.name].keymap_items:
        found_item = False
        if kmi.idname == item.idname:
            found_item = True
            for name in dir(kmi.properties):
                if not name in ["bl_rna", "rna_type"] and not name[0] == "_":
                    if name in kmi.properties and name in item.properties and not kmi.properties[name] == item.properties[name]:
                        found_item = False
        if found_item:
            return item
    print(f"Couldn't find keymap item for {key}, using addon keymap instead. This won't be saved across sessions!")
    return kmi


class BFA_PT_FIND_AND_REPLACE(bpy.types.Panel):
    bl_label = 'Find and Replace'
    bl_idname = 'BFA_PT_FIND_AND_REPLACE'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_context = ''
    bl_order = 0
    bl_ui_units_x=16

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        layout.label(text='Find and Replace', icon="NONE")

        if hasattr(bpy.types,"TEXT_PT_find"):
            if not hasattr(bpy.types.TEXT_PT_find, "poll") or bpy.types.TEXT_PT_find.poll(context):
                bpy.types.TEXT_PT_find.draw(self, context)
            else:
                layout.label(text="Can't display this panel here!", icon="ERROR")
        else:
            layout.label(text="Can't display this panel!", icon="ERROR")

        row = layout.row(heading='', align=False)
        split = row.split(factor=0.65, align=False)
        split.prop(bpy.context.scene, 'bfa_show_properties', text='Show Properties', icon="NONE", emboss=True)

        if bpy.context.scene.bfa_show_properties is True:
            split.label(icon='DISCLOSURE_TRI_DOWN')
        else:
            split.label(icon='DISCLOSURE_TRI_RIGHT')

        if bpy.context.scene.bfa_show_properties:
            if hasattr(bpy.types,"TEXT_PT_properties"):
                if not hasattr(bpy.types.TEXT_PT_properties, "poll") or bpy.types.TEXT_PT_properties.poll(context):
                    bpy.types.TEXT_PT_properties.draw(self, context)
                else:
                    layout.label(text="Can't display this panel here!", icon="ERROR")
            else:
                layout.label(text="Can't display this panel!", icon="ERROR")


class BFA_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = 'bfa_find_and_replace'

    def draw(self, context):
        if not (False):
            layout = self.layout
            layout.prop(find_user_keyconfig('C5E0F'), 'type', text='Keymap', full_event=True)


def register():
    global _icons
    _icons = bpy.utils.previews.new()

    bpy.types.Scene.bfa_show_properties = bpy.props.BoolProperty(name='Show Properties', description='Show/Hide the Text Options', default=False)
    bpy.utils.register_class(BFA_PT_FIND_AND_REPLACE)
    bpy.utils.register_class(BFA_AddonPreferences)

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Text', space_type='TEXT_EDITOR')
    kmi = km.keymap_items.new('wm.call_panel', 'RIGHTMOUSE', 'PRESS',
        ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'BFA_PT_FIND_AND_REPLACE'
    kmi.properties.keep_open = True
    addon_keymaps['C5E0F'] = (km, kmi)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Scene.bfa_show_properties

    bpy.utils.unregister_class(BFA_PT_FIND_AND_REPLACE)
    bpy.utils.unregister_class(BFA_AddonPreferences)
