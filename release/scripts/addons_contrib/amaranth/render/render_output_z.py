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
EXR Render: Warn when Z not connected
Display a little warning label when exporting EXR, with Z Buffer enabled, but
forgot to plug the Z input in the Compositor.

Might be a bit too specific, but found it nice to remember to plug the Z input
if we explicitely specify for Z Buffers to be saved (because it's disabled by
default).

Find it on the Output panel, Render properties.
"""
import bpy


# // FEATURE: Object ID for objects inside DupliGroups
# UI: Warning about Z not connected when using EXR
def ui_render_output_z(self, context):

    scene = bpy.context.scene
    image = scene.render.image_settings
    if scene.render.use_compositing and \
            image.file_format == 'OPEN_EXR' and \
            image.use_zbuffer:
        if scene.node_tree and scene.node_tree.nodes:
            for no in scene.node_tree.nodes:
                if no.type == 'COMPOSITE':
                    if not no.inputs['Z'].is_linked:
                        self.layout.label(
                            text="The Z output in node \"%s\" is not connected" %
                            no.name, icon="ERROR")

# // UI: Warning about Z not connected


def register():
    bpy.types.RENDER_PT_output.append(ui_render_output_z)


def unregister():
    bpy.types.RENDER_PT_output.remove(ui_render_output_z)
