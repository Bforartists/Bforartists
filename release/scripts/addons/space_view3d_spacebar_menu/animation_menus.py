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
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )

from bl_ui.properties_paint_common import UnifiedPaintPanel



# Animation Player (Thanks to marvin.k.breuer) #
class VIEW3D_MT_Animation_Player(Menu):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout

        layout.operator("screen.animation_play", text="PLAY", icon='PLAY')
        layout.operator("screen.animation_play", text="Stop", icon='PAUSE')
        layout.operator("screen.animation_play", text="Reverse", icon='PLAY_REVERSE').reverse = True
        layout.separator()


        layout.operator("screen.keyframe_jump", text="Next FR", icon='NEXT_KEYFRAME').next = True
        layout.operator("screen.keyframe_jump", text="Previous FR", icon='PREV_KEYFRAME').next = False
        layout.separator()

        layout.operator("screen.frame_jump", text="Jump FF", icon='FF').end = True
        layout.operator("screen.frame_jump", text="Jump REW", icon='REW').end = False
        layout.separator()

        layout.menu("VIEW3D_MT_object_animation", text="Keyframes", icon='DECORATE_ANIMATE')



# List The Classes #

classes = (
    VIEW3D_MT_Animation_Player,
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
