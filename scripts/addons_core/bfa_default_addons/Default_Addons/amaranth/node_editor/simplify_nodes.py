# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Nodes Simplify Panel [WIP Feature]

Disable/Enable certain nodes at a time. Useful to quickly "simplify"
compositing.
This feature is a work in progress, the main issue now is when switching
many different kinds one after the other.

On the Nodes Editor Properties N panel.
"""

import bpy


def init():
    nodes_compo_types = (
        ("ALL", "All Types", "", 0),
        ("BLUR", "Blur", "", 1),
        ("BOKEHBLUR", "Bokeh Blur", "", 2),
        ("VECBLUR", "Vector Blur", "", 3),
        ("DEFOCUS", "Defocus", "", 4),
        ("R_LAYERS", "Render Layer", "", 5),
    )
    node = bpy.types.Node
    nodes_compo = bpy.types.CompositorNodeTree
    nodes_compo.types = bpy.props.EnumProperty(
        items=nodes_compo_types, name="Types")
    nodes_compo.toggle_mute = bpy.props.BoolProperty(default=False)
    node.status = bpy.props.BoolProperty(default=False)


def clear():
    wm = bpy.context.window_manager
    for p in ("types", "toggle_mute", "status"):
        if wm.get(p):
            del wm[p]


class AMTH_NODE_PT_simplify(bpy.types.Panel):

    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Simplify"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR" \
            and space.node_tree is not None \
            and space.tree_type == "CompositorNodeTree"

    def draw(self, context):
        layout = self.layout
        node_tree = context.scene.node_tree

        if node_tree is not None:
            layout.prop(node_tree, "types")
            layout.operator(AMTH_NODE_OT_toggle_mute.bl_idname,
                            text="Turn On" if node_tree.toggle_mute else "Turn Off",
                            icon="RESTRICT_VIEW_OFF" if node_tree.toggle_mute else "RESTRICT_VIEW_ON")

            if node_tree.types == "VECBLUR":
                layout.label(text="This will also toggle the Vector pass {}".format(
                    "on" if node_tree.toggle_mute else "off"), icon="INFO")


class AMTH_NODE_OT_toggle_mute(bpy.types.Operator):

    bl_idname = "node.toggle_mute"
    bl_label = "Toggle Mute"

    def execute(self, context):
        scene = context.scene
        node_tree = scene.node_tree
        node_type = node_tree.types
        rlayers = scene.render

        if "amaranth_pass_vector" not in scene.keys():
            scene["amaranth_pass_vector"] = []

        # can"t extend() the list, so make a dummy one
        pass_vector = scene["amaranth_pass_vector"]

        if not pass_vector:
            pass_vector = []

        if node_tree.toggle_mute:
            for node in node_tree.nodes:
                if node_type == "ALL":
                    node.mute = node.status
                if node.type == node_type:
                    node.mute = node.status
                if node_type == "VECBLUR":
                    for layer in rlayers.layers:
                        if layer.name in pass_vector:
                            layer.use_pass_vector = True
                            pass_vector.remove(layer.name)

                node_tree.toggle_mute = False

        else:
            for node in node_tree.nodes:
                if node_type == "ALL":
                    node.mute = True
                if node.type == node_type:
                    node.status = node.mute
                    node.mute = True
                if node_type == "VECBLUR":
                    for layer in rlayers.layers:
                        if layer.use_pass_vector:
                            pass_vector.append(layer.name)
                            layer.use_pass_vector = False
                            pass

                node_tree.toggle_mute = True

        # Write back to the custom prop
        pass_vector = sorted(set(pass_vector))
        scene["amaranth_pass_vector"] = pass_vector

        return {"FINISHED"}


def register():
    init()
    bpy.utils.register_class(AMTH_NODE_PT_simplify)
    bpy.utils.register_class(AMTH_NODE_OT_toggle_mute)


def unregister():
    clear()
    bpy.utils.unregister_class(AMTH_NODE_PT_simplify)
    bpy.utils.unregister_class(AMTH_NODE_OT_toggle_mute)
