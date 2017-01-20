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

'''
bl_info = {
    "name": "Torus Knots",
    "author": "testscreenings",
    "version": (0, 1),
    "blender": (2, 59, 0),
    "location": "View3D > Add > Curve",
    "description": "Adds many types of (torus) knots",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Curve/Torus_Knot",
    "category": "Add Curve"}
'''

##------------------------------------------------------------
#### import modules
import bpy
from bpy.props import *
from math import sin, cos, pi
from bpy_extras.object_utils import AddObjectHelper, object_data_add


########################################################################
####################### Knot Definitions ###############################
########################################################################
def Torus_Knot(self):
    p = self.torus_p
    q = self.torus_q
    w = self.torus_w
    res = self.torus_res
    h = self.torus_h
    u = self.torus_u
    v = self.torus_v
    rounds = self.torus_rounds

    newPoints = []
    angle = 2*rounds
    step = angle/(res-1)
    scale = h
    height = w

    for i in range(res-1):
        t = ( i*step*pi)

        x = (2 * scale + cos((q*t)/p*v)) * cos(t * u)
        y = (2 * scale + cos((q*t)/p*v)) * sin(t * u)
        z = sin(q*t/p) * height

        newPoints.extend([x,y,z,1])

    return newPoints


##------------------------------------------------------------
# Main Function
def create_torus_knot(self, context):
    verts = Torus_Knot(self)

    curve_data = bpy.data.curves.new(name='Torus Knot', type='CURVE')
    spline = curve_data.splines.new(type='NURBS')
    spline.points.add(int(len(verts)*0.25 - 1))
    spline.points.foreach_set('co', verts)
    spline.use_endpoint_u = True
    spline.use_cyclic_u = True
    spline.order_u = 4
    curve_data.dimensions = '3D'

    if self.geo_surf:
        curve_data.bevel_depth = self.geo_bDepth
        curve_data.bevel_resolution = self.geo_bRes
        curve_data.fill_mode = 'FULL'
        curve_data.extrude = self.geo_extrude
        #curve_data.offset = self.geo_width # removed, somehow screws things up all of a sudden
        curve_data.resolution_u = self.geo_res

    new_obj = object_data_add(context, curve_data, operator=self)


class torus_knot_plus(bpy.types.Operator, AddObjectHelper):
    """"""
    bl_idname = "curve.torus_knot_plus"
    bl_label = "Torus Knot +"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    bl_description = "adds many types of knots"

    #### general options
    options_plus = BoolProperty(name="plus options",
                default=False,
                description="Show more options (the plus part)")

    #### GEO Options
    geo_surf = BoolProperty(name="Surface",
                default=True)
    geo_bDepth = FloatProperty(name="bevel",
                default=0.08,
                min=0, soft_min=0)
    geo_bRes = IntProperty(name="bevel res",
                default=2,
                min=0, soft_min=0,
                max=4, soft_max=4)
    geo_extrude = FloatProperty(name="extrude",
                default=0.0,
                min=0, soft_min=0)
    geo_res = IntProperty(name="resolution",
                default=12,
                min=1, soft_min=1)


    #### Parameters
    torus_res = IntProperty(name="Resoulution",
                default=100,
                min=3, soft_min=3,
                description='Resolution, Number of controlverticies')
    torus_p = IntProperty(name="p",
                default=2,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="p")
    torus_q = IntProperty(name="q",
                default=3,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="q")
    torus_w = FloatProperty(name="Height",
                default=1,
                #min=0, soft_min=0,
                #max=1, soft_max=1,
                description="Height in Z")
    torus_h = FloatProperty(name="Scale",
                default=1,
                #min=0, soft_min=0,
                #max=1, soft_max=1,
                description="Scale, in XY")
    torus_u = IntProperty(name="u",
                default=1,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="u")
    torus_v = IntProperty(name="v",
                default=1,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="v")
    torus_rounds = IntProperty(name="Rounds",
                default=2,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="Rounds")

    ##### DRAW #####
    def draw(self, context):
        layout = self.layout

        # general options
        layout.label(text="Torus Knot Parameters:")

        # Parameters
        box = layout.box()
        box.prop(self, 'torus_res')
        box.prop(self, 'torus_w')
        box.prop(self, 'torus_h')
        box.prop(self, 'torus_p')
        box.prop(self, 'torus_q')
        box.prop(self, 'options_plus')
        if self.options_plus:
            box.prop(self, 'torus_u')
            box.prop(self, 'torus_v')
            box.prop(self, 'torus_rounds')

        # surface Options
        col = layout.column()
        col.label(text="Geometry Options:")
        box = layout.box()
        box.prop(self, 'geo_surf')
        if self.geo_surf:
            box.prop(self, 'geo_bDepth')
            box.prop(self, 'geo_bRes')
            box.prop(self, 'geo_extrude')
            box.prop(self, 'geo_res')

        col = layout.column()
        col.prop(self, 'location')
        col.prop(self, 'rotation')

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        if not self.options_plus:
            self.torus_rounds = self.torus_p

        #recoded for add_utils
        create_torus_knot(self, context)

        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}
