# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    'name': 'PathFinder',
    'author': 'Spivak Vladimir (cwolf3d)',
    'version': (0, 5, 1),
    'blender': (3, 0, 0),
    'location': 'Curve Tools addon. (N) Panel',
    'description': 'PathFinder - quick search, selection, removal of splines',
    'warning': '', # used for warning icon and text in addons panel
    'doc_url': '',
    'tracker_url': '',
    'category': 'Curve',
}

import time
import threading

import gpu
from gpu_extras.batch import batch_for_shader

import bpy
from bpy.props import *
from bpy_extras import object_utils, view3d_utils
from mathutils import  *
from math import  *

from . import mathematics
from . import util

def get_bezier_points(spline, matrix_world):
    point_list = []
    len_bezier_points = len(spline.bezier_points)
    if len_bezier_points > 1:
        for i in range(0, len_bezier_points - 1):
            point_list.extend([matrix_world @ spline.bezier_points[i].co])
            for t in range(0, 100, 2):
                h = mathematics.subdivide_cubic_bezier(spline.bezier_points[i].co,
                                           spline.bezier_points[i].handle_right,
                                           spline.bezier_points[i + 1].handle_left,
                                           spline.bezier_points[i + 1].co,
                                           t/100)
                point_list.extend([matrix_world @ h[2]])
        if spline.use_cyclic_u and len_bezier_points > 2:
            point_list.extend([matrix_world @ spline.bezier_points[len_bezier_points - 1].co])
            for t in range(0, 100, 2):
                h = mathematics.subdivide_cubic_bezier(spline.bezier_points[len_bezier_points - 1].co,
                                           spline.bezier_points[len_bezier_points - 1].handle_right,
                                           spline.bezier_points[0].handle_left,
                                           spline.bezier_points[0].co,
                                           t/100)
                point_list.extend([matrix_world @ h[2]])
            point_list.extend([matrix_world @ spline.bezier_points[0].co])

    return point_list

def get_points(spline, matrix_world):
    point_list = []
    len_points = len(spline.points)
    if len_points > 1:
        for i in range(0, len_points - 1):
            point_list.extend([matrix_world @ Vector((spline.points[i].co.x, spline.points[i].co.y, spline.points[i].co.z))])
            for t in range(0, 100, 2):
                x = (spline.points[i].co.x + t / 100 * spline.points[i + 1].co.x) / (1 + t / 100)
                y = (spline.points[i].co.y + t / 100 * spline.points[i + 1].co.y) / (1 + t / 100)
                z = (spline.points[i].co.z + t / 100 * spline.points[i + 1].co.z) / (1 + t / 100)
                point_list.extend([matrix_world @ Vector((x, y, z))])
        if spline.use_cyclic_u and len_points > 2:
            point_list.extend([matrix_world @ Vector((spline.points[len_points - 1].co.x, spline.points[len_points - 1].co.y, spline.points[len_points - 1].co.z))])
            for t in range(0, 100, 2):
                x = (spline.points[len_points - 1].co.x + t / 100 * spline.points[0].co.x) / (1 + t / 100)
                y = (spline.points[len_points - 1].co.y + t / 100 * spline.points[0].co.y) / (1 + t / 100)
                z = (spline.points[len_points - 1].co.z + t / 100 * spline.points[0].co.z) / (1 + t / 100)
                point_list.extend([matrix_world @ Vector((x, y, z))])
            point_list.extend([matrix_world @ Vector((spline.points[0].co.x, spline.points[0].co.y, spline.points[0].co.z))])
    return point_list

def draw_bezier_points(self, context, spline, matrix_world, path_color, path_thickness):

    points = get_bezier_points(spline, matrix_world)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})

    shader.bind()
    shader.uniform_float("color", path_color)
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(path_thickness)
    batch.draw(shader)

def draw_points(self, context, spline, matrix_world, path_color, path_thickness):

    points = get_points(spline, matrix_world)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})

    shader.bind()
    shader.uniform_float("color", path_color)
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(path_thickness)
    batch.draw(shader)

def near(location3D, point, radius):
    factor = 0
    if point.x > (location3D.x - radius):
        factor += 1
    if point.x < (location3D.x + radius):
        factor += 1
    if point.y > (location3D.y - radius):
        factor += 1
    if point.y < (location3D.y + radius):
        factor += 1
    if point.z > (location3D.z - radius):
        factor += 1
    if point.z < (location3D.z + radius):
        factor += 1

    return factor

def click(self, context, event):
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.context.view_layer.update()
    for object in context.selected_objects:
        matrix_world = object.matrix_world
        if object.type == 'CURVE':
            curvedata = object.data

            radius = bpy.context.scene.curvetools.PathFinderRadius

            for spline in curvedata.splines:
                len_bezier_points = len(spline.bezier_points)
                factor_max = 0
                for i in range(0, len_bezier_points):

                    co = matrix_world @ spline.bezier_points[i].co
                    factor = near(self.location3D, co, radius)
                    if factor > factor_max:
                                factor_max = factor

                    if i < len_bezier_points - 1:
                        for t in range(0, 100, 2):
                            h = mathematics.subdivide_cubic_bezier(spline.bezier_points[i].co,
                                           spline.bezier_points[i].handle_right,
                                           spline.bezier_points[i + 1].handle_left,
                                           spline.bezier_points[i + 1].co,
                                           t/100)
                            co = matrix_world @ h[2]
                            factor = near(self.location3D, co, radius)
                            if factor > factor_max:
                                factor_max = factor

                    if spline.use_cyclic_u and len_bezier_points > 2:
                        for t in range(0, 100, 2):
                            h = mathematics.subdivide_cubic_bezier(spline.bezier_points[len_bezier_points - 1].co,
                                           spline.bezier_points[len_bezier_points - 1].handle_right,
                                           spline.bezier_points[0].handle_left,
                                           spline.bezier_points[0].co,
                                           t/100)
                            co = matrix_world @ h[2]
                            factor = near(self.location3D, co, radius)
                            if factor > factor_max:
                                factor_max = factor

                if factor_max == 6:
                    args = (self, context, spline, matrix_world, self.path_color, self.path_thickness)
                    self.handlers.append(bpy.types.SpaceView3D.draw_handler_add(draw_bezier_points, args, 'WINDOW', 'POST_VIEW'))

                    for bezier_point in spline.bezier_points:
                        bezier_point.select_control_point = True
                        bezier_point.select_left_handle = True
                        bezier_point.select_right_handle = True

            for spline in curvedata.splines:
                len_points = len(spline.points)
                factor_max = 0
                for i in range(0, len_points):
                    co = matrix_world @ Vector((spline.points[i].co.x, spline.points[i].co.y, spline.points[i].co.z))
                    factor = near(self.location3D, co, radius)
                    if factor > factor_max:
                        factor_max = factor

                    if i < len_bezier_points - 1:
                        for t in range(0, 100, 2):
                            x = (spline.points[i].co.x + t / 100 * spline.points[i + 1].co.x) / (1 + t / 100)
                            y = (spline.points[i].co.y + t / 100 * spline.points[i + 1].co.y) / (1 + t / 100)
                            z = (spline.points[i].co.z + t / 100 * spline.points[i + 1].co.z) / (1 + t / 100)
                            co = matrix_world @ Vector((x, y, z))
                            factor = near(self.location3D, co, radius)
                            if factor > factor_max:
                                factor_max = factor

                    if spline.use_cyclic_u and len_points > 2:
                        for t in range(0, 100, 2):
                            x = (spline.points[len_points - 1].co.x + t / 100 * spline.points[0].co.x) / (1 + t / 100)
                            y = (spline.points[len_points - 1].co.y + t / 100 * spline.points[0].co.y) / (1 + t / 100)
                            z = (spline.points[len_points - 1].co.z + t / 100 * spline.points[0].co.z) / (1 + t / 100)
                            co = matrix_world @ Vector((x, y, z))
                            factor = near(self.location3D, co, radius)
                            if factor > factor_max:
                                factor_max = factor

                if factor_max == 6:
                    args = (self, context, spline, matrix_world, self.path_color, self.path_thickness)
                    self.handlers.append(bpy.types.SpaceView3D.draw_handler_add(draw_points, args, 'WINDOW', 'POST_VIEW'))

                    for point in spline.points:
                        point.select = True

def remove_handler(handlers):
    for handler in handlers:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        except:
            pass
    for handler in handlers:
        handlers.remove(handler)

class PathFinder(bpy.types.Operator):
    bl_idname = "curvetools.pathfinder"
    bl_label = "Path Finder"
    bl_description = "Path Finder"
    bl_options = {'REGISTER', 'UNDO'}

    x: IntProperty(name="x", description="x")
    y: IntProperty(name="y", description="y")
    location3D: FloatVectorProperty(name = "",
                description = "Start location",
                default = (0.0, 0.0, 0.0),
                subtype = 'XYZ')

    handlers = []

    def execute(self, context):
        self.report({'INFO'}, "ESC or TAB - cancel")
        bpy.ops.object.mode_set(mode = 'EDIT')

        # color change in the panel
        self.path_color = bpy.context.scene.curvetools.path_color
        self.path_thickness = bpy.context.scene.curvetools.path_thickness

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'ESC', 'TAB'}:  # Cancel
            remove_handler(self.handlers)
            return {'CANCELLED'}

        if event.type in {'X', 'DEL'}:  # Cancel
            remove_handler(self.handlers)
            bpy.ops.curve.delete(type='VERT')
            return {'RUNNING_MODAL'}

        elif event.alt and event.shift and event.type == 'LEFTMOUSE':
            click(self, context, event)

        elif event.alt and not event.shift and event.type == 'LEFTMOUSE':
            remove_handler(self.handlers)
            bpy.ops.curve.select_all(action='DESELECT')
            click(self, context, event)

        elif event.alt and event.type == 'RIGHTMOUSE':
           remove_handler(self.handlers)
           bpy.ops.curve.select_all(action='DESELECT')
           click(self, context, event)

        elif event.alt and not event.shift and event.shift and event.type == 'RIGHTMOUSE':
            click(self, context, event)

        elif event.type == 'A':
            remove_handler(self.handlers)
            bpy.ops.curve.select_all(action='DESELECT')

        elif event.type == 'MOUSEMOVE':  #
            self.x = event.mouse_x
            self.y = event.mouse_y
            region = bpy.context.region
            rv3d = bpy.context.space_data.region_3d
            self.location3D = view3d_utils.region_2d_to_location_3d(
                region,
                rv3d,
                (event.mouse_region_x, event.mouse_region_y),
                (0.0, 0.0, 0.0)
                )

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()


operators = [PathFinder]
