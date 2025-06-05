# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy, math
from mathutils import Vector, Matrix
from bpy_extras.io_utils import ExportHelper
from . import internal

class SvgExport(bpy.types.Operator, ExportHelper):
    bl_idname = 'export_svg_format.svg'
    bl_description = bl_label = 'Curves (.svg)'
    filename_ext = '.svg'

    selection_only: bpy.props.BoolProperty(name='Selection only', description='instead of exporting all visible curves')
    absolute_coordinates: bpy.props.BoolProperty(name='Absolute coordinates', description='instead of relative coordinates')
    viewport_projection: bpy.props.BoolProperty(name='Viewport projection', description='WYSIWYG instead of an local orthographic projection')
    unit_name: bpy.props.EnumProperty(name='Unit', items=internal.units, default='mm')

    def serialize_point(self, position, update_ref_position=True):
        if self.transform:
            position = self.transform@Vector((position[0], position[1], position[2], 1.0))
            position *= 0.5/position.w
        ref_position = self.origin if self.absolute_coordinates else self.ref_position
        command = '{:.3f},{:.3f}'.format((position[0]-ref_position[0])*self.scale[0], (position[1]-ref_position[1])*self.scale[1])
        if update_ref_position:
            self.ref_position = position
        return command

    def serialize_point_command(self, point, drawing):
        if self.absolute_coordinates:
            return ('L' if drawing else 'M')+self.serialize_point(point.co)
        else:
            return ('l' if drawing else 'm')+self.serialize_point(point.co)

    def serialize_curve_command(self, prev, next):
        return ('C' if self.absolute_coordinates else 'c')+self.serialize_point(prev.handle_right, False)+' '+self.serialize_point(next.handle_left, False)+' '+self.serialize_point(next.co)

    def serialize_spline(self, spline):
        path = ''
        points = spline.bezier_points if spline.type == 'BEZIER' else spline.points

        for index, next in enumerate(points):
            if index == 0:
                path += self.serialize_point_command(next, False)
            elif spline.type == 'BEZIER' and (points[index-1].handle_right_type != 'VECTOR' or next.handle_left_type != 'VECTOR'):
                path += self.serialize_curve_command(points[index-1], next)
            else:
                path += self.serialize_point_command(next, True)

        if spline.use_cyclic_u:
            if spline.type == 'BEZIER' and (points[-1].handle_right_type != 'VECTOR' or points[0].handle_left_type != 'VECTOR'):
                path += self.serialize_curve_command(points[-1], points[0])
            else:
                self.serialize_point(points[0].co)
            path += 'Z' if self.absolute_coordinates else 'z'

        return path

    def serialize_object(self, obj):
        if self.area:
            self.transform = self.area.spaces.active.region_3d.perspective_matrix@obj.matrix_world
            self.origin = Vector((-0.5, 0.5, 0, 0))
        else:
            self.transform = None
            self.origin = Vector((obj.bound_box[0][0], obj.bound_box[7][1], obj.bound_box[0][2], 0))

        xml = '\t<g id="'+obj.name+'">\n'
        styles = {}
        for spline in obj.data.splines:
            style = 'none'
            if obj.data.dimensions == '2D' and spline.use_cyclic_u:
                if spline.material_index < len(obj.data.materials) and obj.data.materials[spline.material_index] != None:
                    style = Vector(obj.data.materials[spline.material_index].diffuse_color)*255
                else:
                    style = Vector((0.8, 0.8, 0.8))*255
                style = 'rgb({},{},{})'.format(round(style[0]), round(style[1]), round(style[2]))
            if style in styles:
                styles[style].append(spline)
            else:
                styles[style] = [spline]

        for style, splines in styles.items():
            style = 'fill:'+style+';'
            if style == 'fill:none;':
                style += 'stroke:black;'
            xml += '\t\t<path style="'+style+'" d="'
            self.ref_position = self.origin
            for spline in splines:
                xml += self.serialize_spline(spline)
            xml += '"/>\n'

        return xml+'\t</g>\n'

    def execute(self, context):
        objects = bpy.context.selected_objects if self.selection_only else bpy.context.visible_objects
        curves = []
        for obj in objects:
            if obj.type == 'CURVE':
                curves.append(obj)
        if len(curves) == 0:
            self.report({'WARNING'}, 'Nothing to export')
            return {'CANCELLED'}

        self.area = None
        if self.viewport_projection:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    self.region = None
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            self.region = region
                    if self.region == None:
                        continue
                    self.area = area
                    self.bounds = Vector((self.region.width, self.region.height, 0))
                    self.scale = Vector(self.bounds)
                    if self.unit_name != 'px':
                        self.unit_name = '-'

        if self.area == None:
            self.bounds = Vector((0, 0, 0))
            for obj in curves:
                self.bounds[0] = max(self.bounds[0], obj.bound_box[7][0]-obj.bound_box[0][0])
                self.bounds[1] = max(self.bounds[1], obj.bound_box[7][1]-obj.bound_box[0][1])
            self.scale = Vector((1, 1, 0))
            for unit in internal.units:
                if self.unit_name == unit[0]:
                    self.scale *= 1.0/float(unit[2])
                    break
            self.scale *= context.scene.unit_settings.scale_length
            self.bounds = Vector(a*b for a,b in zip(self.bounds, self.scale))

        self.scale[1] *= -1
        with open(self.filepath, 'w') as f:
            svg_view = ('' if self.unit_name == '-' else 'width="{0:.3f}{2}" height="{1:.3f}{2}" ')+'viewBox="0 0 {0:.3f} {1:.3f}">\n'
            f.write('''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" fill-rule="evenodd" '''+svg_view.format(self.bounds[0], self.bounds[1], self.unit_name))
            for obj in curves:
                f.write(self.serialize_object(obj))
            f.write('</svg>')

        return {'FINISHED'}

class GCodeExport(bpy.types.Operator, ExportHelper):
    bl_idname = 'export_gcode_format.gcode'
    bl_description = bl_label = 'Toolpath (.gcode)'
    filename_ext = '.gcode'

    speed: bpy.props.FloatProperty(name='Speed', description='Maximal speed in mm / minute', min=0, default=60)
    step_angle: bpy.props.FloatProperty(name='Resolution', description='Smaller values make curves smoother by adding more vertices', unit='ROTATION', min=math.pi/128, default=math.pi/16)
    local_coordinates: bpy.props.BoolProperty(name='Local coords', description='instead of global coordinates')
    detect_circles: bpy.props.BoolProperty(name='Detect Circles', description='Export bezier circles and helixes as G02 and G03') # TODO: Detect polygon circles too, merge consecutive circle segments

    @classmethod
    def poll(cls, context):
        obj = bpy.context.object
        return obj != None and obj.type == 'CURVE' and len(obj.data.splines) == 1 and not obj.data.splines[0].use_cyclic_u

    def execute(self, context):
        self.scale = Vector((1, 1, 1))
        self.scale *= context.scene.unit_settings.scale_length*1000.0
        with open(self.filepath, 'w') as f:
            f.write('G21\n') # Length is measured in millimeters
            spline = bpy.context.object.data.splines[0]
            if spline.use_cyclic_u:
                return gcode
            def transform(position):
                result = Vector((position[0]*self.scale[0], position[1]*self.scale[1], position[2]*self.scale[2])) # , 1.0
                return result if self.local_coordinates else bpy.context.object.matrix_world@result
            points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
            prevSpeed = -1
            for index, current in enumerate(points):
                speed = self.speed*max(0.0, min(current.weight_softbody, 1.0))
                if speed != prevSpeed and current.weight_softbody != 1.0:
                    f.write('F{:.3f}\n'.format(speed))
                    prevSpeed = speed
                speed_code = 'G00' if current.weight_softbody == 1.0 else 'G01'
                prev = points[index-1]
                linear = spline.type != 'BEZIER' or index == 0 or (prev.handle_right_type == 'VECTOR' and current.handle_left_type == 'VECTOR')
                position = transform(current.co)
                if linear:
                    f.write(speed_code+' X{:.3f} Y{:.3f} Z{:.3f}\n'.format(position[0], position[1], position[2]))
                else:
                    segment_points = internal.bezierSegmentPoints(prev, current)
                    circle = None
                    if self.detect_circles:
                        for axis in range(0, 3):
                            projected_points = []
                            for point in segment_points:
                                projected_point = Vector(point)
                                projected_point[axis] = 0.0
                                projected_points.append(projected_point)
                            circle = internal.circleOfBezier(projected_points)
                            if circle:
                                normal = circle.orientation.col[2]
                                center = transform(circle.center-prev.co)
                                f.write('G{} G0{} I{:.3f} J{:.3f} K{:.3f} X{:.3f} Y{:.3f} Z{:.3f}\n'.format(19-axis, 3 if normal[axis] > 0.0 else 2, center[0], center[1], center[2], position[0], position[1], position[2]))
                                break
                    if circle == None:
                        bezier_samples = 128
                        prev_tangent = internal.bezierTangentAt(segment_points, 0).normalized()
                        for t in range(1, bezier_samples+1):
                            t /= bezier_samples
                            tangent = internal.bezierTangentAt(segment_points, t).normalized()
                            if t == 1 or math.acos(min(max(-1, prev_tangent@tangent), 1)) >= self.step_angle:
                                position = transform(internal.bezierPointAt(segment_points, t))
                                prev_tangent = tangent
                                f.write(speed_code+' X{:.3f} Y{:.3f} Z{:.3f}\n'.format(position[0], position[1], position[2]))
        return {'FINISHED'}

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()

operators = [SvgExport, GCodeExport]
