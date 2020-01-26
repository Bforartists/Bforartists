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
