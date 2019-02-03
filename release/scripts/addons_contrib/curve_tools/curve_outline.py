'''
by Yann Bertrand, january 2014.

BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

END GPL LICENCE BLOCK
'''

bl_info = {
    "name": "Curve Outline",
    "description": "creates an Outline",
    "category": "Object",
    "author": "Yann Bertrand (jimflim)",
    "version": (0, 4),
    "blender": (2, 69, 0),
}

import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_line


def createOutline(curve, outline):

    for spline in curve.data.splines[:]:
        p = spline.bezier_points
        out = []

        n = ((p[0].handle_right-p[0].co).normalized()-(p[0].handle_left-p[0].co).normalized()).normalized()
        n = Vector((-n[1], n[0], n[2]))
        o = p[0].co+outline*n
        out.append(o)

        for i in range(1,len(p)):
            n = ((p[i].handle_right-p[i].co).normalized()-(p[i].handle_left-p[i].co).normalized()).normalized()
            n = Vector((-n[1], n[0], n[2]))
            o = intersect_line_line(out[-1], (out[-1]+p[i].co-p[i-1].co), p[i].co, p[i].co+n)[0]
            out.append(o)

        curve.data.splines.new('BEZIER')
        if spline.use_cyclic_u:
            curve.data.splines[-1].use_cyclic_u = True
        p_out = curve.data.splines[-1].bezier_points
        p_out.add(len(out)-1)

        for i in range(len(out)):
            p_out[i].handle_left_type = 'FREE'
            p_out[i].handle_right_type = 'FREE'

            p_out[i].co = out[i]

            if i<len(out)-1:
                l = (p[i+1].co-p[i].co).length
                l2 = (out[i]-out[i+1]).length

            if i==0:
                p_out[i].handle_left = out[i] + ((p[i].handle_left-p[i].co)*l2/l)
            if i<len(out)-1:
                p_out[i+1].handle_left = out[i+1] + ((p[i+1].handle_left-p[i+1].co)*l2/l)
            p_out[i].handle_right = out[i] + ((p[i].handle_right-p[i].co)*l2/l)

        for i in range(len(p)):
            p_out[i].handle_left_type = p[i].handle_left_type
            p_out[i].handle_right_type = p[i].handle_right_type

    return


class CurveOutline(bpy.types.Operator):
    """Curve Outliner"""
    bl_idname = "object._curve_outline"
    bl_label = "Create Outline"
    bl_options = {'REGISTER', 'UNDO'}
    outline: bpy.props.FloatProperty(name="Amount", default=0.1, min=-10, max=10)

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'CURVE')

    def execute(self, context):
        createOutline(context.object, self.outline)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

def menu_func(self, context):
    self.layout.operator(CurveOutline.bl_idname)

def register():
    bpy.utils.register_class(CurveOutline)

def unregister():
    bpy.utils.unregister_class(CurveOutline)

if __name__ == "__main__":
    register()
