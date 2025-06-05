# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
