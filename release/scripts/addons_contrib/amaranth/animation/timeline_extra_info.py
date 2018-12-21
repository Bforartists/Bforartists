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
Timeline Extra Info

Display amount of frames left until Frame End, very handy especially when
rendering an animation or OpenGL preview.
Display current/end time on SMPTE. Find it on the Timeline header.
"""

import bpy


def label_timeline_extra_info(self, context):
    get_addon = "amaranth" in context.user_preferences.addons.keys()
    if not get_addon:
        return

    layout = self.layout
    scene = context.scene

    if context.user_preferences.addons["amaranth"].preferences.use_timeline_extra_info:
        row = layout.row(align=True)

        # Check for preview range
        frame_start = scene.frame_preview_start if scene.use_preview_range else scene.frame_start
        frame_end = scene.frame_preview_end if scene.use_preview_range else scene.frame_end

        row.label(
            text="%s / %s" %
            (bpy.utils.smpte_from_frame(
                scene.frame_current -
                frame_start),
                bpy.utils.smpte_from_frame(
                    frame_end -
                    frame_start)))

        if (scene.frame_current > frame_end):
            row.label(text="%s Frames Ahead" %
                      ((frame_end - scene.frame_current) * -1))
        elif (scene.frame_current == frame_start):
            row.label(text="Start Frame (%s left)" %
                      (frame_end - scene.frame_current))
        elif (scene.frame_current == frame_end):
            row.label(text="%s End Frame" % scene.frame_current)
        else:
            row.label(text="%s Frames Left" %
                      (frame_end - scene.frame_current))


def register():
    bpy.types.STATUSBAR_HT_header.append(label_timeline_extra_info)


def unregister():
    bpy.types.STATUSBAR_HT_header.remove(label_timeline_extra_info)
