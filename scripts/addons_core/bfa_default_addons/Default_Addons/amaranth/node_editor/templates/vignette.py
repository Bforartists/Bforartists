# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from mathutils import Vector


class AMTH_NODE_OT_AddTemplateVignette(bpy.types.Operator):
    bl_idname = "node.template_add_vignette"
    bl_label = "Add Vignette"
    bl_description = "Add a vignette effect"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR" \
            and space.node_tree is not None \
            and space.tree_type == "CompositorNodeTree"

    # used as reference the setup scene script from master nazgul
    def _setupNodes(self, context):
        scene = context.scene
        space = context.space_data
        tree = scene.node_tree
        has_act = True if tree.nodes.active else False

        bpy.ops.node.select_all(action="DESELECT")

        ellipse = tree.nodes.new(type="CompositorNodeEllipseMask")
        ellipse.width = 0.8
        ellipse.height = 0.4
        blur = tree.nodes.new(type="CompositorNodeBlur")
        blur.use_relative = True
        blur.factor_x = 30
        blur.factor_y = 50
        ramp = tree.nodes.new(type="CompositorNodeValToRGB")
        ramp.color_ramp.interpolation = "B_SPLINE"
        ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1)

        overlay = tree.nodes.new(type="CompositorNodeMixRGB")
        overlay.blend_type = "OVERLAY"
        overlay.inputs[0].default_value = 0.8
        overlay.inputs[1].default_value = (0.5, 0.5, 0.5, 1)

        tree.links.new(ellipse.outputs["Mask"], blur.inputs["Image"])
        tree.links.new(blur.outputs["Image"], ramp.inputs[0])
        tree.links.new(ramp.outputs["Image"], overlay.inputs[2])
        if has_act:
            tree.links.new(tree.nodes.active.outputs[0], overlay.inputs[1])

        if has_act:
            overlay.location = tree.nodes.active.location
            overlay.location += Vector((350.0, 0.0))
        else:
            overlay.location += Vector(
                (space.cursor_location[0], space.cursor_location[1]))

        ellipse.location = overlay.location
        ellipse.location += Vector((-715.0, -400))
        ellipse.inputs[0].hide = True
        ellipse.inputs[1].hide = True

        blur.location = ellipse.location
        blur.location += Vector((300.0, 0.0))
        blur.inputs["Size"].hide = True

        ramp.location = blur.location
        ramp.location += Vector((175.0, 0))
        ramp.outputs["Alpha"].hide = True

        for node in (ellipse, blur, ramp, overlay):
            node.select = True
            node.show_preview = False

        bpy.ops.node.join()

        frame = ellipse.parent
        frame.label = "Vignette"
        frame.use_custom_color = True
        frame.color = (0.1, 0.1, 0.1)

        overlay.parent = None
        overlay.label = "Vignette Overlay"

    def execute(self, context):
        self._setupNodes(context)

        return {"FINISHED"}
