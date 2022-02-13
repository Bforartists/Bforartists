# SPDX-License-Identifier: GPL-2.0-or-later
import bpy


# FEATURE: Shader Nodes Extra Info
def node_shader_extra(self, context):
    if context.space_data.tree_type == 'ShaderNodeTree':
        ob = context.active_object
        snode = context.space_data
        layout = self.layout

        if ob and snode.shader_type == 'OBJECT':
            if ob.type == 'LAMP':
                layout.label(text="%s" % ob.name,
                             icon="LAMP_%s" % ob.data.type)
            else:
                layout.label(text="%s" % ob.name,
                             icon="OUTLINER_DATA_%s" % ob.type)

# // FEATURE: Shader Nodes Extra Info


def register():
    bpy.types.NODE_HT_header.append(node_shader_extra)


def unregister():
    bpy.types.NODE_HT_header.remove(node_shader_extra)
