# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


# LOAD MODULE #
import bpy
from bpy import *
from bpy.props import *

import blf
import gpu
from gpu_extras.batch import batch_for_shader

import math
import mathutils
from mathutils import Vector
from mathutils.geometry import interpolate_bezier


def get_points(spline, matrix_world):

    bezier_points = spline.bezier_points

    if len(bezier_points) < 2:
        return []

    r = spline.resolution_u + 1
    if r < 2:
       return []
    segments = len(bezier_points)

    if not spline.use_cyclic_u:
        segments -= 1

    point_list = []
    for i in range(segments):
        inext = (i + 1) % len(bezier_points)

        bezier_points1 = matrix_world @ bezier_points[i].co
        handle1 = matrix_world @ bezier_points[i].handle_right
        handle2 = matrix_world @ bezier_points[inext].handle_left
        bezier_points2 = matrix_world @ bezier_points[inext].co

        bezier = bezier_points1, handle1, handle2, bezier_points2, r
        points = interpolate_bezier(*bezier)
        point_list.extend(points)

    return point_list

def draw(self, context, splines, curve_vertcolor, matrix_world):

    for spline in splines:
        points = get_points(spline, matrix_world)

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')

        batch = batch_for_shader(shader, 'POINTS', {"pos": points})

        shader.bind()
        shader.uniform_float("color", curve_vertcolor)
        batch.draw(shader)


class ShowCurveResolution(bpy.types.Operator):
    bl_idname = "curvetools.show_resolution"
    bl_label = "Show Curve Resolution"
    bl_description = "Show curve Resolution / [ESC] - remove"

    handlers = []

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'ESC'}:
            for handler in self.handlers:
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
                except:
                    pass
            for handler in self.handlers:
                self.handlers.remove(handler)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}


    def invoke(self, context, event):

        if context.area.type == 'VIEW_3D':

            # color change in the panel
            curve_vertcolor = bpy.context.scene.curvetools.curve_vertcolor

            splines = context.active_object.data.splines
            matrix_world = context.active_object.matrix_world

            # the arguments we pass the the callback
            args = (self, context, splines, curve_vertcolor, matrix_world)

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self.handlers.append(bpy.types.SpaceView3D.draw_handler_add(draw, args, 'WINDOW', 'POST_VIEW'))

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'},
            "View3D not found, cannot run operator")
            return {'CANCELLED'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'CURVE')

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()

operators = [
    ShowCurveResolution,
    ]
