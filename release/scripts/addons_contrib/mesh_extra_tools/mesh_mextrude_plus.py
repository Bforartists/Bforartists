# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

################################################################################
# Repeats extrusion + rotation + scale for one or more faces                   #

################################################################################

bl_info = {
    "name": "MExtrude Plus1",
    "author": "liero",
    "version": (1, 2, 9),
    "blender": (2, 77, 0),
    "location": "View3D > Tool Shelf",
    "description": "Repeat extrusions from faces to create organic shapes",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/T28570",
    "category": "Mesh"}


import bpy
import bmesh
import mathutils
import random
from random import gauss
from math import radians
from mathutils import Euler, Vector
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty


def vloc(self, r):
    random.seed(self.ran + r)
    return self.off * (1 + random.gauss(0, self.var1 / 3))


def vrot(self, r):
    random.seed(self.ran + r)
    return Euler((radians(self.rotx) + random.gauss(0, self.var2 / 3),
                  radians(self.roty) + random.gauss(0, self.var2 / 3),
                  radians(self.rotz) + random.gauss(0, self.var2 / 3)), 'XYZ')


def vsca(self, r):
    random.seed(self.ran + r)
    return self.sca * (1 + random.gauss(0, self.var3 / 3))


class MExtrude(bpy.types.Operator):
    bl_idname = 'object.mextrude'
    bl_label = 'MExtrude'
    bl_description = 'Multi Extrude'
    bl_options = {'REGISTER', 'UNDO'}

    off = FloatProperty(name='Offset', min=-2, soft_min=0.001,
                        soft_max=2, max=5, default=.5, description='Translation')
    rotx = FloatProperty(name='Rot X', min=-85, soft_min=-30,
                         soft_max=30, max=85, default=0, description='X rotation')
    roty = FloatProperty(name='Rot Y', min=-85, soft_min=-30,
                         soft_max=30, max=85, default=0, description='Y rotation')
    rotz = FloatProperty(name='Rot Z', min=-85, soft_min=-30,
                         soft_max=30, max=85, default=-0, description='Z rotation')
    sca = FloatProperty(name='Scale', min=0.1, soft_min=0.5,
                        soft_max=1.2, max=2, default=1.0, description='Scaling')
    var1 = FloatProperty(name='Offset Var', min=-5, soft_min=-1,
                         soft_max=1, max=5, default=0, description='Offset variation')
    var2 = FloatProperty(name='Rotation Var', min=-5, soft_min=-1,
                         soft_max=1, max=5, default=0, description='Rotation variation')
    var3 = FloatProperty(name='Scale Noise', min=-5, soft_min=-1,
                         soft_max=1, max=5, default=0, description='Scaling noise')
    num = IntProperty(name='Repeat', min=1, max=50, soft_max=100,
                      default=5, description='Repetitions')
    ran = IntProperty(name='Seed', min=-9999, max=9999, default=0,
                      description='Seed to feed random values')

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Transformations:')
        column.prop(self, 'off', slider=True)
        column.prop(self, 'rotx', slider=True)
        column.prop(self, 'roty', slider=True)
        column.prop(self, 'rotz', slider=True)
        column.prop(self, 'sca', slider=True)
        column = layout.column(align=True)
        column.label(text='Variation settings:')
        column.prop(self, 'var1', slider=True)
        column.prop(self, 'var2', slider=True)
        column.prop(self, 'var3', slider=True)
        column.prop(self, 'ran')
        column = layout.column(align=False)
        column.prop(self, 'num')

    def execute(self, context):
        obj = bpy.context.object
        data, om = obj.data, obj.mode
        bpy.context.tool_settings.mesh_select_mode = [False, False, True]

        # bmesh operations
        bpy.ops.object.mode_set()
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        sel = [f for f in bm.faces if f.select]

        after = []

        # faces loop
        for i, of in enumerate(sel):
            rot = vrot(self, i)
            off = vloc(self, i)
            of.normal_update()

            # extrusion loop
            for r in range(self.num):
                nf = of.copy()
                nf.normal_update()
                no = nf.normal.copy()
                ce = nf.calc_center_bounds()
                s = vsca(self, i + r)

                for v in nf.verts:
                    v.co -= ce
                    v.co.rotate(rot)
                    v.co += ce + no * off
                    v.co = v.co.lerp(ce, 1 - s)

                # extrude code from TrumanBlending
                for a, b in zip(of.loops, nf.loops):
                    sf = bm.faces.new((a.vert, a.link_loop_next.vert,
                                       b.link_loop_next.vert, b.vert))
                    sf.normal_update()

                bm.faces.remove(of)
                of = nf
            after.append(of)

        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False

        for f in after:
            f.select = True

        bm.to_mesh(obj.data)
        obj.data.update()

        # restore user settings
        bpy.ops.object.mode_set(mode=om)

        if not len(sel):
            self.report({'INFO'}, 'Select one or more faces...')
        return{'FINISHED'}


class mextrude_help(bpy.types.Operator):
    bl_idname = 'help.mextrude'
    bl_label = ''

    def draw(self, context):
        layout = self.layout
        layout.label('To use:')
        layout.label('Make a selection or selection of Faces.')
        layout.label('Extrude, rotate extrusions & more.')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)


def register():
    bpy.utils.register_module(__name__)

    # bpy.utils.register_class(BB)


def unregister():
    bpy.utils.unregister_module(__name__)

    # bpy.utils.unregister_class(BB)


if __name__ == '__main__':
    register()
