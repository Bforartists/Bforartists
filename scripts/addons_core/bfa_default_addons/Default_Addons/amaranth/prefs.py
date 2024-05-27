# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import (
        BoolProperty,
        IntProperty,
        )


class AmaranthToolsetPreferences(bpy.types.AddonPreferences):
    bl_idname = "amaranth"
    use_frame_current: BoolProperty(
        name="Current Frame Slider",
        description="Set the current frame from the Specials menu in the 3D View",
        default=True,
    )
    use_file_save_reload: BoolProperty(
        name="Save & Reload File",
        description="File menu > Save & Reload, or Ctrl + Shift + W",
        default=True,
    )
    use_scene_refresh: BoolProperty(
        name="Refresh Scene",
        description="Specials Menu [W]",
        default=True,
    )
    use_image_node_display: BoolProperty(
        name="Active Image Node in Editor",
        description="Display active node image in image editor",
        default=True,
    )
    use_scene_stats: BoolProperty(
        name="Extra Scene Statistics",
        description="Display extra scene statistics in the status bar (may be slow in heavy scenes)",
        default=False,
    )
    frames_jump: IntProperty(
        name="Frames",
        description="Number of frames to jump forward/backward",
        default=10,
        min=1
    )
    use_framerate: BoolProperty(
        name="Framerate Jump",
        description="Jump the amount of frames forward/backward that you have set as your framerate",
        default=False,
    )
    use_layers_for_render: BoolProperty(
        name="Current Layers for Render",
        description="Save the layers that should be enabled for render",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        layout.label(
            text="Here you can enable or disable specific tools, "
                 "in case they interfere with others or are just plain annoying")

        split = layout.split(factor=0.25)

        col = split.column()
        sub = col.column(align=True)
        sub.label(text="3D View", icon="VIEW3D")
        sub.prop(self, "use_frame_current")
        sub.prop(self, "use_scene_refresh")

        sub.separator()

        sub.label(text="General", icon="SCENE_DATA")
        sub.prop(self, "use_file_save_reload")
        sub.prop(self, "use_scene_stats")
        sub.prop(self, "use_layers_for_render")
        sub.prop(self, "use_framerate")

        sub.separator()

        sub.label(text="Nodes Editor", icon="NODETREE")
        sub.prop(self, "use_image_node_display")

        col = split.column()
        sub = col.column(align=True)
        sub.label(text="")
        sub.label(
            text="Set the current frame from the Specials menu in the 3D View [W]")
        sub.label(
            text="Refresh the current Scene. Hotkey: F5 or in Specials menu [W]")

        sub.separator()
        sub.label(text="")  # General icon
        sub.label(
            text="Quickly save and reload the current file (no warning!). "
                 "File menu or Ctrl+Shift+W")
        sub.label(
            text="Display extra stats for Scenes, Cameras, Meshlights (Cycles). Can be slow in heavy scenes")
        sub.label(
            text="Save the set of layers that should be activated for a final render")
        sub.label(
            text="Jump the amount of frames forward/backward that you've set as your framerate")

        sub.separator()
        sub.label(text="")  # Nodes
        sub.label(
            text="When double-clicking an Image node, display it on the Image editor "
                 "(if any)")


def register():
    bpy.utils.register_class(AmaranthToolsetPreferences)


def unregister():
    bpy.utils.unregister_class(AmaranthToolsetPreferences)
