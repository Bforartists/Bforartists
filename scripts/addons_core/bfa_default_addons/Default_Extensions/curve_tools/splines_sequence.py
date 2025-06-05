# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

import blf
import gpu
from gpu_extras.batch import batch_for_shader

import math
import mathutils
from mathutils import Vector

from bpy.props import (
        EnumProperty,
        )

# ------------------------------------------------------------
# ShowSplinesSequence

def draw_number(n, co, font_height):

    point_list = []

    numeral = [
              [Vector((0, 0, 0)), Vector((0, 2, 0)), Vector((0, 2, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((1, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 0))],
              [Vector((0, 1, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((1, 0, 0))],
              [Vector((0, 2, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((1, 1, 0)), Vector((1, 1, 0)), Vector((0, 0, 0)), Vector((0, 0, 0)), Vector((1, 0, 0))],
              [Vector((0, 2, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((1, 1, 0)), Vector((1, 1, 0)), Vector((0, 0, 0))],
              [Vector((0, 2, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((1, 1, 0)), Vector((1, 1, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((1, 0, 0))],
              [Vector((1, 2, 0)), Vector((0, 2, 0)), Vector((0, 2, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((1, 1, 0)), Vector((1, 1, 0)), Vector((1, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 0))],
              [Vector((1, 2, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((0, 0, 0)), Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((1, 0, 0)), Vector((1, 1, 0)), Vector((1, 1, 0)), Vector((0, 1, 0))],
              [Vector((0, 2, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((0, 0, 0))],
              [Vector((0, 1, 0)), Vector((0, 2, 0)), Vector((0, 2, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((1, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 0)), Vector((0, 0, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((1, 1, 0))],
              [Vector((0, 0, 0)), Vector((1, 1, 0)), Vector((1, 1, 0)), Vector((1, 2, 0)), Vector((1, 2, 0)), Vector((0, 2, 0)), Vector((0, 2, 0)), Vector((0, 1, 0)), Vector((0, 1, 0)), Vector((1, 1, 0))],
              ]

    for num in numeral[n]:
        point_list.extend([num * font_height + co])

    return point_list


def draw(self, context, splines, sequence_color, font_thickness, font_size, matrix_world):

    splines_len = len(splines)
    for n in range(0, splines_len):

        res = [int(x) for x in str(n)]

        i = 0
        for r in res:
            # draw some text
            if splines[n].type == 'BEZIER':
                first_point_co = matrix_world @ splines[n].bezier_points[0].co
            else:
                first_point = matrix_world @ splines[n].points[0].co
                first_point_co = Vector((first_point.x, first_point.y, first_point.z))

            first_point_co = Vector((i, 0, 0)) + first_point_co
            points = draw_number(r, first_point_co, font_size)

            shader = gpu.shader.from_builtin('UNIFORM_COLOR')

            batch = batch_for_shader(shader, 'LINES', {"pos": points})

            shader.bind()
            gpu.state.line_width_set(font_thickness)
            shader.uniform_float("color", sequence_color)
            batch.draw(shader)
            i += font_size + font_size * 0.5

class ShowSplinesSequence(bpy.types.Operator):
    bl_idname = "curvetools.show_splines_sequence"
    bl_label = "Show Splines Sequence"
    bl_description = "Show Splines Sequence / [ESC] - remove"

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
            sequence_color = bpy.context.scene.curvetools.sequence_color
            font_thickness = bpy.context.scene.curvetools.font_thickness
            font_size = bpy.context.scene.curvetools.font_size

            splines = context.active_object.data.splines
            matrix_world = context.active_object.matrix_world

            # the arguments we pass the the callback
            args = (self, context, splines, sequence_color, font_thickness, font_size, matrix_world)

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

# ------------------------------------------------------------
# RearrangeSpline

def rearrangesplines(dataCurve, select_spline1, select_spline2):

    spline1 = dataCurve.splines[select_spline1]
    spline2 = dataCurve.splines[select_spline2]

    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.spline_type_set(type='BEZIER')
    bpy.ops.curve.select_all(action='DESELECT')

    type1 = spline1.type
    type2 = spline2.type

    len_spline1 = len(spline1.bezier_points)
    len_spline2 = len(spline2.bezier_points)

    newSpline = dataCurve.splines.new(type=type1)
    newSpline.bezier_points.add(len_spline1 - 1)
    newSpline.use_cyclic_u = spline1.use_cyclic_u
    for n in range(0, len_spline1):
        newSpline.bezier_points[n].co = spline1.bezier_points[n].co
        newSpline.bezier_points[n].handle_left_type = spline1.bezier_points[n].handle_left_type
        newSpline.bezier_points[n].handle_left = spline1.bezier_points[n].handle_left
        newSpline.bezier_points[n].handle_right_type = spline1.bezier_points[n].handle_right_type
        newSpline.bezier_points[n].handle_right = spline1.bezier_points[n].handle_right
        spline1.bezier_points[n].select_control_point = True

    spline1.bezier_points[0].select_control_point = False
    spline1.bezier_points[0].select_left_handle = False
    spline1.bezier_points[0].select_right_handle = False
    bpy.ops.curve.delete(type='VERT')

    spline1.bezier_points[0].select_control_point = True
    bpy.ops.curve.spline_type_set(type=type2)

    bpy.ops.curve.select_all(action='DESELECT')

    spline1.bezier_points.add(len_spline2 - 1)
    spline1.use_cyclic_u = spline2.use_cyclic_u
    for n in range(0, len_spline2):
        spline1.bezier_points[n].co = spline2.bezier_points[n].co
        spline1.bezier_points[n].handle_left_type = spline2.bezier_points[n].handle_left_type
        spline1.bezier_points[n].handle_left = spline2.bezier_points[n].handle_left
        spline1.bezier_points[n].handle_right_type = spline2.bezier_points[n].handle_right_type
        spline1.bezier_points[n].handle_right = spline2.bezier_points[n].handle_right
        spline1.bezier_points[n].select_control_point = False
        spline1.bezier_points[n].select_left_handle = False
        spline1.bezier_points[n].select_right_handle = False
        spline2.bezier_points[n].select_control_point = True

    spline2.bezier_points[0].select_control_point = False
    spline2.bezier_points[0].select_left_handle = False
    spline2.bezier_points[0].select_right_handle = False
    bpy.ops.curve.delete(type='VERT')

    spline2.bezier_points[0].select_control_point = True
    bpy.ops.curve.spline_type_set(type=type1)

    spline2.bezier_points.add(len_spline1 - 1)
    spline2.use_cyclic_u = newSpline.use_cyclic_u
    for m in range(0, len_spline1):
        spline2.bezier_points[m].co = newSpline.bezier_points[m].co
        spline2.bezier_points[m].handle_left_type = newSpline.bezier_points[m].handle_left_type
        spline2.bezier_points[m].handle_left = newSpline.bezier_points[m].handle_left
        spline2.bezier_points[m].handle_right_type = newSpline.bezier_points[m].handle_right_type
        spline2.bezier_points[m].handle_right = newSpline.bezier_points[m].handle_right

    bpy.ops.curve.select_all(action='DESELECT')
    for point in newSpline.bezier_points:
        point.select_control_point = True
    bpy.ops.curve.delete(type='VERT')

    spline2.bezier_points[0].select_control_point = True

def rearrange(dataCurve, select_spline, command):
    len_splines = len(dataCurve.splines)
    if command == 'NEXT':
        if select_spline < len_splines - 1:
            rearrangesplines(dataCurve, select_spline + 1, select_spline)

    if command == 'PREV':
        if select_spline > 0:
            rearrangesplines(dataCurve, select_spline, select_spline - 1)

class RearrangeSpline(bpy.types.Operator):
    bl_idname = "curvetools.rearrange_spline"
    bl_label = "Rearrange Spline"
    bl_description = "Rearrange Spline"
    bl_options = {'UNDO'}

    Types = [('NEXT', "Next", "next"),
             ('PREV', "Prev", "prev")]
    command : EnumProperty(
            name="command",
            description="Command (prev or next)",
            items=Types
            )

    def execute(self, context):
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.context.view_layer.update()

        dataCurve = context.active_object.data

        splines = context.active_object.data.splines

        select_spline = 0

        sn = 0
        for spline in splines:
            for bezier_points in spline.bezier_points:
                if bezier_points.select_control_point:
                    select_spline = sn
            sn += 1

        sn = 0
        for spline in splines:
            for point in spline.points:
                if point.select:
                    select_spline = sn
            sn += 1

        rearrange(dataCurve, select_spline, self.command)

        return {'FINISHED'}

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

operators = [ShowSplinesSequence, RearrangeSpline]
