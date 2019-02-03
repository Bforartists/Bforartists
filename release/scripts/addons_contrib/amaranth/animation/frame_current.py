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
"""
Current Frame Slider

Currently the only way to change the current frame is to have a Timeline
editor open, but sometimes you don't have one, or you're fullscreen.
This option adds the Current Frame slider to the Specials menu. Find it
hitting the W menu in Object mode, you can slide or click in the middle
of the button to set the frame manually.
"""

import bpy


def button_frame_current(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    scene = context.scene
    if context.preferences.addons["amaranth"].preferences.use_frame_current:
        self.layout.separator()
        self.layout.prop(scene, "frame_current", text="Set Current Frame")


def register():
    bpy.types.VIEW3D_MT_object_specials.append(button_frame_current)
    bpy.types.VIEW3D_MT_pose_specials.append(button_frame_current)


def unregister():
    bpy.types.VIEW3D_MT_object_specials.remove(button_frame_current)
    bpy.types.VIEW3D_MT_pose_specials.remove(button_frame_current)
