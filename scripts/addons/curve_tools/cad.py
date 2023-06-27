# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    'name': 'Curve CAD Tools',
    'author': 'Alexander Meißner',
    'version': (1, 0, 0),
    'blender': (2, 80, 0),
    'category': 'Curve',
    'doc_url': 'https://github.com/Lichtso/curve_cad',
    'tracker_url': 'https://github.com/lichtso/curve_cad/issues'
}

import bpy
from . import internal
from . import util

class Fillet(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_fillet'
    bl_description = bl_label = 'Fillet'
    bl_options = {'REGISTER', 'UNDO'}

    radius: bpy.props.FloatProperty(name='Radius', description='Radius of the rounded corners', unit='LENGTH', min=0.0, default=0.1)
    chamfer_mode: bpy.props.BoolProperty(name='Chamfer', description='Cut off sharp without rounding', default=False)
    limit_half_way: bpy.props.BoolProperty(name='Limit Half Way', description='Limits the segments to half their length in order to prevent collisions', default=False)

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        splines = internal.getSelectedSplines(True, True, True)
        if len(splines) == 0:
            self.report({'WARNING'}, 'Nothing selected')
            return {'CANCELLED'}
        for spline in splines:
            internal.filletSpline(spline, self.radius, self.chamfer_mode, self.limit_half_way)
            bpy.context.object.data.splines.remove(spline)
        return {'FINISHED'}

class Boolean(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_boolean'
    bl_description = bl_label = 'Boolean'
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(name='Type', items=[
        ('UNION', 'Union', 'Boolean OR', 0),
        ('INTERSECTION', 'Intersection', 'Boolean AND', 1),
        ('DIFFERENCE', 'Difference', 'Active minus Selected', 2)
    ])

    @classmethod
    def poll(cls, context):
        return util.Selected1Curve()

    def execute(self, context):
        current_mode = bpy.context.object.mode

        bpy.ops.object.mode_set(mode = 'EDIT')
        if bpy.context.object.data.dimensions != '2D':
            self.report({'WARNING'}, 'Can only be applied in 2D')
            return {'CANCELLED'}
        splines = internal.getSelectedSplines(True, True)
        if len(splines) != 2:
            self.report({'WARNING'}, 'Invalid selection. Only work to selected two spline.')
            return {'CANCELLED'}
        bpy.ops.curve.spline_type_set(type='BEZIER')
        splineA = bpy.context.object.data.splines.active
        splineB = splines[0] if (splines[1] == splineA) else splines[1]
        if not internal.bezierBooleanGeometry(splineA, splineB, self.operation):
            self.report({'WARNING'}, 'Invalid selection. Only work to selected two spline.')
            return {'CANCELLED'}

        bpy.ops.object.mode_set (mode = current_mode)

        return {'FINISHED'}

class Intersection(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_intersection'
    bl_description = bl_label = 'Intersection'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        segments = internal.bezierSegments(bpy.context.object.data.splines, True)
        if len(segments) < 2:
            self.report({'WARNING'}, 'Invalid selection')
            return {'CANCELLED'}

        internal.bezierMultiIntersection(segments)
        return {'FINISHED'}

class HandleProjection(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_handle_projection'
    bl_description = bl_label = 'Handle Projection'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        segments = internal.bezierSegments(bpy.context.object.data.splines, True)
        if len(segments) < 1:
            self.report({'WARNING'}, 'Nothing selected')
            return {'CANCELLED'}

        internal.bezierProjectHandles(segments)
        return {'FINISHED'}

class MergeEnds(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_merge_ends'
    bl_description = bl_label = 'Merge Ends'
    bl_options = {'REGISTER', 'UNDO'}

    max_dist: bpy.props.FloatProperty(name='Distance', description='Threshold of the maximum distance at which two control points are merged', unit='LENGTH', min=0.0, default=0.1)

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        splines = [spline for spline in internal.getSelectedSplines(True, False) if spline.use_cyclic_u == False]

        while len(splines) > 0:
            spline = splines.pop()
            closest_pair = ([spline, spline], [spline.bezier_points[0], spline.bezier_points[-1]], [False, True])
            min_dist = (spline.bezier_points[0].co-spline.bezier_points[-1].co).length
            for other_spline in splines:
                for j in range(-1, 1):
                    for i in range(-1, 1):
                        dist = (spline.bezier_points[i].co-other_spline.bezier_points[j].co).length
                        if min_dist > dist:
                            min_dist = dist
                            closest_pair = ([spline, other_spline], [spline.bezier_points[i], other_spline.bezier_points[j]], [i == -1, j == -1])
            if min_dist > self.max_dist:
                continue
            if closest_pair[0][0] != closest_pair[0][1]:
                splines.remove(closest_pair[0][1])
            spline = internal.mergeEnds(closest_pair[0], closest_pair[1], closest_pair[2])
            if spline.use_cyclic_u == False:
                splines.append(spline)

        return {'FINISHED'}

class Subdivide(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_subdivide'
    bl_description = bl_label = 'Subdivide'
    bl_options = {'REGISTER', 'UNDO'}

    params: bpy.props.StringProperty(name='Params', default='0.25 0.5 0.75')

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        current_mode = bpy.context.object.mode

        bpy.ops.object.mode_set(mode = 'EDIT')

        segments = internal.bezierSegments(bpy.context.object.data.splines, True)
        if len(segments) == 0:
            self.report({'WARNING'}, 'Nothing selected')
            return {'CANCELLED'}

        cuts = []
        for param in self.params.split(' '):
            cuts.append({'param': max(0.0, min(float(param), 1.0))})
        cuts.sort(key=(lambda cut: cut['param']))
        for segment in segments:
            segment['cuts'].extend(cuts)
        internal.subdivideBezierSegments(segments)

        bpy.ops.object.mode_set (mode = current_mode)
        return {'FINISHED'}

class Array(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_array'
    bl_description = bl_label = 'Array'
    bl_options = {'REGISTER', 'UNDO'}

    offset: bpy.props.FloatVectorProperty(name='Offset', unit='LENGTH', description='Vector between to copies', subtype='DIRECTION', default=(0.0, 0.0, -1.0), size=3)
    count: bpy.props.IntProperty(name='Count', description='Number of copies', min=1, default=2)
    connect: bpy.props.BoolProperty(name='Connect', description='Concatenate individual copies', default=False)
    serpentine: bpy.props.BoolProperty(name='Serpentine', description='Switch direction of every second copy', default=False)

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        splines = internal.getSelectedSplines(True, True)
        if len(splines) == 0:
            self.report({'WARNING'}, 'Nothing selected')
            return {'CANCELLED'}
        internal.arrayModifier(splines, self.offset, self.count, self.connect, self.serpentine)
        return {'FINISHED'}

class Circle(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_circle'
    bl_description = bl_label = 'Circle'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        segments = internal.bezierSegments(bpy.context.object.data.splines, True)
        if len(segments) != 1:
            self.report({'WARNING'}, 'Invalid selection')
            return {'CANCELLED'}

        segment = internal.bezierSegmentPoints(segments[0]['beginPoint'], segments[0]['endPoint'])
        circle = internal.circleOfBezier(segment)
        if circle == None:
            self.report({'WARNING'}, 'Not a circle')
            return {'CANCELLED'}
        bpy.context.scene.cursor.location = circle.center
        bpy.context.scene.cursor.rotation_mode = 'QUATERNION'
        bpy.context.scene.cursor.rotation_quaternion = circle.orientation.to_quaternion()
        return {'FINISHED'}

class Length(bpy.types.Operator):
    bl_idname = 'curvetools.bezier_cad_length'
    bl_description = bl_label = 'Length'

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        segments = internal.bezierSegments(bpy.context.object.data.splines, True)
        if len(segments) == 0:
            self.report({'WARNING'}, 'Nothing selected')
            return {'CANCELLED'}

        length = 0
        for segment in segments:
            length += internal.bezierLength(internal.bezierSegmentPoints(segment['beginPoint'], segment['endPoint']))
        self.report({'INFO'}, bpy.utils.units.to_string(bpy.context.scene.unit_settings.system, 'LENGTH', length))
        return {'FINISHED'}

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()

operators = [Fillet, Boolean, Intersection, HandleProjection, MergeEnds, Subdivide, Array, Circle, Length]
