# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from mathutils import Vector


class AMTH_NODE_OT_AddTemplateVectorBlur(bpy.types.Operator):
    bl_idname = "node.template_add_vectorblur"
    bl_label = "Add Vector Blur"
    bl_description = "Add a vector blur filter"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        tree = context.scene.node_tree
        return space.type == "NODE_EDITOR" \
            and space.node_tree is not None \
            and space.tree_type == "CompositorNodeTree" \
            and tree \
            and tree.nodes.active \
            and tree.nodes.active.type == "R_LAYERS"

    def _setupNodes(self, context):
        scene = context.scene
        space = context.space_data
        tree = scene.node_tree

        bpy.ops.node.select_all(action="DESELECT")

        act_node = tree.nodes.active
        #rlayer = act_node.scene.render.layers[act_node.layer]

        #if not rlayer.use_pass_vector:
            #rlayer.use_pass_vector = True

        vblur = tree.nodes.new(type="CompositorNodeVecBlur")
        vblur.use_curved = True
        vblur.factor = 0.5

        tree.links.new(act_node.outputs["Image"], vblur.inputs["Image"])
        tree.links.new(act_node.outputs["Depth"], vblur.inputs["Z"])
        tree.links.new(act_node.outputs["Vector"], vblur.inputs["Speed"])

        if tree.nodes.active:
            vblur.location = tree.nodes.active.location
            vblur.location += Vector((250.0, 0.0))
        else:
            vblur.location += Vector(
                (space.cursor_location[0], space.cursor_location[1]))

        vblur.select = True

    def execute(self, context):
        self._setupNodes(context)

        return {"FINISHED"}
