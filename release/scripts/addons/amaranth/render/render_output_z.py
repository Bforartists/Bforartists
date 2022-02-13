# SPDX-License-Identifier: GPL-2.0-or-later
"""
EXR Render: Warn when Z not connected
Display a little warning label when exporting EXR, with Z Buffer enabled, but
forgot to plug the Z input in the Compositor.

Might be a bit too specific, but found it nice to remember to plug the Z input
if we explicitly specify for Z Buffers to be saved (because it's disabled by
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
