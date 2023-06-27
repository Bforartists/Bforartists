# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# by Yann Bertrand, january 2014.

bl_info = {
    "name": "Curve Outline",
    "description": "creates an Outline",
    "author": "Yann Bertrand (jimflim), Vladimir Spivak (cwolf3d)",
    "version": (0, 5),
    "blender": (2, 69, 0),
    "category": "Object",
}

import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_line

from . import util


def createOutline(curve, outline):

    for spline in curve.data.splines[:]:
        if spline.type == 'BEZIER':
            p = spline.bezier_points
            if len(p) < 2:
                return
            out = []

            n = ((p[0].handle_right - p[0].co).normalized() - (p[0].handle_left - p[0].co).normalized()).normalized()
            n = Vector((-n[1], n[0], n[2]))
            o = p[0].co + outline * n
            out.append(o)

            for i in range(1,len(p)-1):
                n = ((p[i].handle_right - p[i].co).normalized() - (p[i].handle_left - p[i].co).normalized()).normalized()
                n = Vector((-n[1], n[0], n[2]))
                o = intersect_line_line(out[-1], (out[-1]+p[i].co - p[i-1].co), p[i].co, p[i].co + n)[0]
                out.append(o)

            n = ((p[-1].handle_right - p[-1].co).normalized() - (p[-1].handle_left - p[-1].co).normalized()).normalized()
            n = Vector((-n[1], n[0], n[2]))
            o = p[-1].co + outline * n
            out.append(o)

            curve.data.splines.new(spline.type)
            if spline.use_cyclic_u:
                curve.data.splines[-1].use_cyclic_u = True
            p_out = curve.data.splines[-1].bezier_points
            p_out.add(len(out)-1)

            for i in range(len(out)):
                p_out[i].handle_left_type = 'FREE'
                p_out[i].handle_right_type = 'FREE'

                p_out[i].co = out[i]

                if i<len(out)-1:
                    l = (p[i + 1].co - p[i].co).length
                    l2 = (out[i] - out[i + 1]).length

                if i==0:
                    p_out[i].handle_left = out[i] + ((p[i].handle_left - p[i].co) * l2/l)
                if i<len(out)-1:
                    p_out[i + 1].handle_left = out[i + 1] + ((p[i + 1].handle_left - p[i + 1].co) * l2/l)
                p_out[i].handle_right = out[i] + ((p[i].handle_right - p[i].co) * l2/l)

            for i in range(len(p)):
                p_out[i].handle_left_type = p[i].handle_left_type
                p_out[i].handle_right_type = p[i].handle_right_type

        else:
            if len(spline.points) < 2:
                return
            p = []
            for point in spline.points:
               v = Vector((point.co[0], point.co[1], point.co[2]))
               p.append(v)
            out = []

            n = ((p[1] - p[0]).normalized() - (p[-1] - p[0]).normalized()).normalized()
            n = Vector((-n[1], n[0], n[2]))
            o = p[0] + outline * n
            out.append(o)

            for i in range(1,len(p)-1):
                n = ((p[i+1] - p[i]).normalized() - (p[i-1] - p[i]).normalized()).normalized()
                n = Vector((-n[1], n[0], n[2]))
                o = intersect_line_line(out[-1], (out[-1]+p[i] - p[i-1]), p[i], p[i] + n)[0]
                out.append(o)

            n = ((p[0] - p[-1]).normalized() - (p[-2] - p[-1]).normalized()).normalized()
            n = Vector((-n[1], n[0], n[2]))
            o = p[-1] + outline * n
            out.append(o)

            curve.data.splines.new(spline.type)
            if spline.use_cyclic_u:
                curve.data.splines[-1].use_cyclic_u = True
            p_out = curve.data.splines[-1].points
            p_out.add(len(out)-1)

            for i in range(len(out)):
                p_out[i].co = (out[i][0], out[i][1], out[i][2], 0.0)

    return


class CurveOutline(bpy.types.Operator):
    """Curve Outliner"""
    bl_idname = "curvetools.outline"
    bl_label = "Create Outline"
    bl_options = {'REGISTER', 'UNDO'}
    outline: bpy.props.FloatProperty(name="Amount", default=0.1)

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        createOutline(context.object, self.outline)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

def menu_func(self, context):
    self.layout.operator(CurveOutline.bl_idname)

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()

operators = [CurveOutline]
