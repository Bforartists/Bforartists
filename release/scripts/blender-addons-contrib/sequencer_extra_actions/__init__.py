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
    "name": "Extra Sequencer Actions",
    "author": "Turi Scandurra, Carlos Padial",
    "version": (3, 8),
    "blender": (2, 69, 0),
    "category": "Sequencer",
    "location": "Sequencer",
    "description": "Collection of extra operators to manipulate VSE strips",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Sequencer/Extra_Sequencer_Actions",
    "tracker_url": "https://developer.blender.org/T32532",
    # old tracker_url: https://developer.blender.org/T30474
    "support": "COMMUNITY"}


if "bpy" in locals():
    import imp
    imp.reload(operators_extra_actions)
    imp.reload(ui)
else:
    from . import operators_extra_actions
    from . import ui

import bpy
import os.path
from bpy.types import Menu
from bpy.types import Header


# Registration
def register():
    bpy.utils.register_module(__name__)

    # Append menu entries
    bpy.types.SEQUENCER_MT_add.prepend(ui.sequencer_add_menu_func)
    bpy.types.SEQUENCER_MT_select.prepend(ui.sequencer_select_menu_func)
    bpy.types.SEQUENCER_MT_strip.prepend(ui.sequencer_strip_menu_func)
    bpy.types.SEQUENCER_HT_header.append(ui.sequencer_header_func)
    bpy.types.CLIP_HT_header.append(ui.clip_header_func)
    bpy.types.CLIP_MT_clip.prepend(ui.clip_clip_menu_func)
    bpy.types.TIME_MT_frame.prepend(ui.time_frame_menu_func)
    bpy.types.TIME_HT_header.append(ui.time_header_func)

    # Add keyboard shortcut configuration
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Frames')
    kmi = km.keymap_items.new('screenextra.frame_skip',
    'RIGHT_ARROW', 'PRESS', ctrl=True, shift=True)
    kmi.properties.back = False
    kmi = km.keymap_items.new('screenextra.frame_skip',
    'LEFT_ARROW', 'PRESS', ctrl=True, shift=True)
    kmi.properties.back = True


def unregister():
    bpy.utils.unregister_module(__name__)

    #  Remove menu entries
    bpy.types.SEQUENCER_MT_add.remove(ui.sequencer_add_menu_func)
    bpy.types.SEQUENCER_MT_select.remove(ui.sequencer_select_menu_func)
    bpy.types.SEQUENCER_MT_strip.remove(ui.sequencer_strip_menu_func)
    bpy.types.SEQUENCER_HT_header.remove(ui.sequencer_header_func)
    bpy.types.CLIP_HT_header.remove(ui.clip_header_func)
    bpy.types.CLIP_MT_clip.remove(ui.clip_clip_menu_func)
    bpy.types.TIME_MT_frame.remove(ui.time_frame_menu_func)
    bpy.types.TIME_HT_header.remove(ui.time_header_func)

    #  Remove keyboard shortcut configuration
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps['Frames']
    km.keymap_items.remove(km.keymap_items['screenextra.frame_skip'])
    km.keymap_items.remove(km.keymap_items['screenextra.frame_skip'])


if __name__ == '__main__':
    register()
