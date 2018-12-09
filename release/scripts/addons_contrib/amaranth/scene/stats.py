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
Scene, Cameras, and Meshlights Count

Increase the stats by displaying the number of scenes, cameras, and light
emitting meshes.
On the Info header.
"""

import bpy
from amaranth import utils


def stats_scene(self, context):
    get_addon = "amaranth" in context.user_preferences.addons.keys()
    if not get_addon:
        return

    if context.user_preferences.addons["amaranth"].preferences.use_scene_stats:
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
