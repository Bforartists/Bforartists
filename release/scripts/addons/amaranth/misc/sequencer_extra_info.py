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
Sequencer: Display Image File Name

When seeking through an image sequence, display the active strips' file name
for the current frame, and it's [playhead].

Find it on the VSE header.
"""
import bpy


# FEATURE: Sequencer Extra Info
def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None


def ui_sequencer_extra_info(self, context):
    layout = self.layout
    strip = act_strip(context)
    if strip:
        seq_type = strip.type
        if seq_type and seq_type == 'IMAGE':
            elem = strip.strip_elem_from_frame(context.scene.frame_current)
            if elem:
                layout.label(
                    text="%s %s" %
                    (elem.filename, "[%s]" %
                     (context.scene.frame_current - strip.frame_start)))

# // FEATURE: Sequencer Extra Info


def register():
    bpy.types.SEQUENCER_HT_header.append(ui_sequencer_extra_info)


def unregister():
    bpy.types.SEQUENCER_HT_header.remove(ui_sequencer_extra_info)
