# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Nodes: XYZ Sliders for Normal Node

Tweak the Normal node more accurately by using these sliders. Not the most
intuitive way to tweak, but it helps.

ProTip: Hit Shift+Drag for moving in very small steps.

Coded by Lukas Töenne. Thanks!
Find it on the Properties panel, when selecting a Normal node.
"""


import bpy
from mathutils import Vector


# FEATURE: Normal Node Values, by Lukas Tönne
def init():
    prop_normal_vector = bpy.props.FloatVectorProperty(
        name="Normal", size=3, subtype='XYZ',
        min=-1.0, max=1.0, soft_min=-1.0, soft_max=1.0,
        get=normal_vector_get, set=normal_vector_set
        )
    bpy.types.ShaderNodeNormal.normal_vector = prop_normal_vector
    bpy.types.CompositorNodeNormal.normal_vector = prop_normal_vector


def clear():
    del bpy.types.ShaderNodeNormal.normal_vector
    del bpy.types.CompositorNodeNormal.normal_vector


def normal_vector_get(self):
    return self.outputs['Normal'].default_value


def normal_vector_set(self, values):
    # default_value allows un-normalized values,
    # do this here to prevent awkward results
    values = Vector(values).normalized()
    self.outputs['Normal'].default_value = values


def act_node(context):
    try:
        return context.active_node
    except AttributeError:
        return None


def ui_node_normal_values(self, context):

    node = act_node(context)

    if act_node:
        if node and node.type == 'NORMAL':
            self.layout.prop(node, "normal_vector", text="")

# // FEATURE: Normal Node Values, by Lukas Tönne


def register():
    init()
    bpy.types.NODE_PT_active_node_properties.append(ui_node_normal_values)


def unregister():
    bpy.types.NODE_PT_active_node_properties.remove(ui_node_normal_values)
    clear()
