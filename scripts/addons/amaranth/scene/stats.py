# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Scene, Cameras, and Meshlights Count

Increase the stats by displaying the number of scenes, cameras, and light
emitting meshes.
On the Info header.
"""

import bpy
from amaranth import utils


def stats_scene(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    if context.preferences.addons["amaranth"].preferences.use_scene_stats:
        scenes_count = str(len(bpy.data.scenes))
        cameras_count = str(len(bpy.data.cameras))
        cameras_selected = 0
        meshlights = 0
        meshlights_visible = 0

        for ob in context.scene.objects:
            if utils.cycles_is_emission(context, ob):
                meshlights += 1
                if ob in context.visible_objects:
                    meshlights_visible += 1

            if ob in context.selected_objects:
                if ob.type == 'CAMERA':
                    cameras_selected += 1

        meshlights_string = '| Meshlights:{}/{}'.format(
            meshlights_visible, meshlights)

        row = self.layout.row(align=True)
        row.label(text="Scenes:{} | Cameras:{}/{} {}".format(
                  scenes_count, cameras_selected, cameras_count,
                  meshlights_string if utils.cycles_active(context) else ''))


def register():
    bpy.types.STATUSBAR_HT_header.append(stats_scene)


def unregister():
    bpy.types.STATUSBAR_HT_header.remove(stats_scene)
