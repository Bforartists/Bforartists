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
Passepartout on Specials menu

The passepartout value of local cameras is now available on the Specials
menu for easy access.
Under Specials menu W, when in Camera view.
"""

import bpy


def button_camera_passepartout(self, context):

    view3d = context.space_data.region_3d
    cam = context.scene.camera.data

    if view3d.view_perspective == "CAMERA":
        layout = self.layout
        if cam.show_passepartout:
            layout.prop(cam, "passepartout_alpha", text="Passepartout")
        else:
            layout.prop(cam, "show_passepartout")


def register():
    bpy.types.VIEW3D_MT_object_specials.append(button_camera_passepartout)


def unregister():
    bpy.types.VIEW3D_MT_object_specials.remove(button_camera_passepartout)
