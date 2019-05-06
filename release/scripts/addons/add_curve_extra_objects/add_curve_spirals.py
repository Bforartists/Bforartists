# gpl: author Alejandro Omar Chocano Vasquez

"""
bl_info = {
    "name": "Spirals",
    "description": "Make spirals",
    "author": "Alejandro Omar Chocano Vasquez",
    "version": (1, 2, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Curve",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.4/Py/"
                "Scripts/Object/Spirals",
    "tracker_url": "http://alexvaqp.googlepages.com?"
                   "func=detail&aid=<number>",
    "category": "Add Curve",
}
"""

import bpy
import time
from bpy.props import (
        EnumProperty,
        BoolProperty,
        FloatProperty,
        IntProperty,
        FloatVectorProperty
        )
from mathutils import (
        Vector,
        Matrix,
        )
from math import (
        sin, cos, pi
        )
from bpy_extras.object_utils import object_data_add
from bpy.types import (
        Operator,
        Menu,
        )
from bl_operators.presets import AddPresetBase


# make normal spiral
# ----------------------------------------------------------------------------

def make_spiral(props, context):
    # archemedian and logarithmic can be plotted in cylindrical coordinates

    # INPUT: turns->degree->max_phi, steps, direction
    # Initialise Polar Coordinate Environment
    props.degree = 360 * props.turns     # If you want to make the slider for degree
    steps = props.steps * props.turns    # props.steps[per turn] -> steps[for the whole spiral]
    props.z_scale = props.dif_z * props.turns

    max_phi = pi * props.degree / 180  # max angle in radian
    step_phi = max_phi / steps  # angle in radians between two vertices

    if props.spiral_direction == 'CLOCKWISE':
        step_phi *= -1  # flip direction
        max_phi *= -1

    step_z = props.z_scale / (steps - 1)  # z increase in one step

    verts = []
    verts.append([props.radius, 0, 0])

    cur_phi = 0
    cur_z = 0

    # Archemedean: dif_radius, radius
    cur_rad = props.radius
    step_rad = props.dif_radius / (steps * 360 / props.degree)
    # radius increase per angle for archemedean spiral|
    # (steps * 360/props.degree)...Steps needed for 360 deg
    # Logarithmic: radius, B_force, ang_div, dif_z

    while abs(cur_phi) <= abs(max_phi):
        cur_phi += step_phi
        cur_z += step_z

        if props.spiral_type == 'ARCH':
            cur_rad += step_rad
        if props.spiral_type == 'LOG':
            # r = a*e^{|theta| * b}
            cur_rad = props.radius * pow(props.B_force, abs(cur_phi))

        px = cur_rad * cos(cur_phi)
        py = cur_rad * sin(cur_phi)
        verts.append([px, py, cur_z])

    return verts


# make Spheric spiral
# ----------------------------------------------------------------------------

def make_spiral_spheric(props, context):
    # INPUT: turns, steps[per turn], radius
    # use spherical Coordinates
    step_phi = (2 * pi) / props.steps  # Step of angle in radians for one turn
    steps = props.steps * props.turns  # props.steps[per turn] -> steps[for the whole spiral]

    max_phi = 2 * pi * props.turns  # max angle in radian
    step_phi = max_phi / steps      # angle in radians between two vertices
    if props.spiral_direction == 'CLOCKWISE':  # flip direction
        step_phi *= -1
        max_phi *= -1
    step_theta = pi / (steps - 1)  # theta increase in one step (pi == 180 deg)

    verts = []
    verts.append([0, 0, -props.radius])  # First vertex at south pole

    cur_phi = 0
    cur_theta = -pi / 2  # Beginning at south pole

    while abs(cur_phi) <= abs(max_phi):
        # Coordinate Transformation sphere->rect
        px = props.radius * cos(cur_theta) * cos(cur_phi)
        py = props.radius * cos(cur_theta) * sin(cur_phi)
        pz = props.radius * sin(cur_theta)

        verts.append([px, py, pz])
        cur_theta += step_theta
        cur_phi += step_phi

    return verts


# make torus spiral
# ----------------------------------------------------------------------------

def make_spiral_torus(props, context):
    # INPUT: turns, steps, inner_radius, curves_number,
    # mul_height, dif_inner_radius, cycles
    max_phi = 2 * pi * props.turns * props.cycles  # max angle in radian
    step_phi = 2 * pi / props.steps  # Step of angle in radians between two vertices

    if props.spiral_direction == 'CLOCKWISE':  # flip direction
        step_phi *= -1
        max_phi *= -1

    step_theta = (2 * pi / props.turns) / props.steps
    step_rad = props.dif_radius / (props.steps * props.turns)
    step_inner_rad = props.dif_inner_radius / props.steps
    step_z = props.dif_z / (props.steps * props.turns)

    verts = []

    cur_phi = 0  # Inner Ring Radius Angle
    cur_theta = 0  # Ring Radius Angle
    cur_rad = props.radius
    cur_inner_rad = props.inner_radius
    cur_z = 0
    n_cycle = 0

    while abs(cur_phi) <= abs(max_phi):
        # Torus Coordinates -> Rect
        px = (cur_rad + cur_inner_rad * cos(cur_phi)) * \
              cos(props.curves_number * cur_theta)
        py = (cur_rad + cur_inner_rad * cos(cur_phi)) * \
              sin(props.curves_number * cur_theta)
        pz = cur_inner_rad * sin(cur_phi) + cur_z

        verts.append([px, py, pz])

        if props.touch and cur_phi >= n_cycle * 2 * pi:
            step_z = ((n_cycle + 1) * props.dif_inner_radius +
                      props.inner_radius) * 2 / (props.steps * props.turns)
            n_cycle += 1

        cur_theta += step_theta
        cur_phi += step_phi
        cur_rad += step_rad
        cur_inner_rad += step_inner_rad
        cur_z += step_z

    return verts

# ------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref

def align_matrix(context, location):
    loc = Matrix.Translation(location)
    obj_align = context.preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D' and
            obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.to_3x3().inverted().to_4x4()
    else:
        rot = Matrix()
    align_matrix = loc @ rot

    return align_matrix

# ------------------------------------------------------------
# get array of vertcoordinates according to splinetype
def vertsToPoints(Verts, splineType):

    # main vars
    vertArray = []

    # array for BEZIER spline output (V3)
    if splineType == 'BEZIER':
        for v in Verts:
            vertArray += v

    # array for nonBEZIER output (V4)
    else:
        for v in Verts:
            vertArray += v
            if splineType == 'NURBS':
                # for nurbs w=1
                vertArray.append(1)
            else:
                # for poly w=0
                vertArray.append(0)
    return vertArray

def draw_curve(props, context, align_matrix):
    # output splineType 'POLY' 'NURBS' 'BEZIER'
    splineType = props.curve_type
    
    if props.spiral_type == 'ARCH':
        verts = make_spiral(props, context)
    if props.spiral_type == 'LOG':
        verts = make_spiral(props, context)
    if props.spiral_type == 'SPHERE':
        verts = make_spiral_spheric(props, context)
    if props.spiral_type == 'TORUS':
        verts = make_spiral_torus(props, context)

    # create object
    if bpy.context.mode == 'EDIT_CURVE':
        Curve = context.active_object
        spline = Curve.data.splines.new(type=splineType)          # spline
    else:
        # create curve
        newCurve = bpy.data.curves.new(name='Spiral', type='CURVE')  # curvedatablock
        spline = newCurve.splines.new(type=splineType)          # spline

        # set curveOptions
        newCurve.dimensions = props.shape
        newCurve.use_path = True
        
        # create object with newCurve
        Curve = object_data_add(context, newCurve)  # place in active scene
        Curve.select_set(True)
        
    Curve.matrix_world = align_matrix  # apply matrix
    Curve.rotation_euler = props.rotation_euler
        
    # set curveOptions
    spline.use_cyclic_u = props.use_cyclic_u
    spline.use_endpoint_u = props.endp_u
    spline.order_u = props.order_u
    
    # turn verts into array
    vertArray = vertsToPoints(verts, splineType)
        
    # create spline from vertarray
    if splineType == 'BEZIER':
        spline.bezier_points.add(int(len(vertArray) * 0.33))
        spline.bezier_points.foreach_set('co', vertArray)
        for point in spline.bezier_points:
            point.handle_right_type = props.handleType
            point.handle_left_type = props.handleType
    else:
        spline.points.add(int(len(vertArray) * 0.25 - 1))
        spline.points.foreach_set('co', vertArray)
        spline.use_endpoint_u = False

class CURVE_OT_spirals(Operator):
    bl_idname = "curve.spirals"
    bl_label = "Curve Spirals"
    bl_description = "Create different types of spirals"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # align_matrix for the invoke
    align_matrix : Matrix()
    
    spiral_type : EnumProperty(
            items=[('ARCH', "Archemedian", "Archemedian"),
                   ("LOG", "Logarithmic", "Logarithmic"),
                   ("SPHERE", "Spheric", "Spheric"),
                   ("TORUS", "Torus", "Torus")],
            default='ARCH',
            name="Spiral Type",
            description="Type of spiral to add"
            )
    spiral_direction : EnumProperty(
            items=[('COUNTER_CLOCKWISE', "Counter Clockwise",
                    "Wind in a counter clockwise direction"),
                   ("CLOCKWISE", "Clockwise",
                   "Wind in a clockwise direction")],
            default='COUNTER_CLOCKWISE',
            name="Spiral Direction",
            description="Direction of winding"
            )
    turns : IntProperty(
            default=1,
            min=1, max=1000,
            description="Length of Spiral in 360 deg"
            )
    steps : IntProperty(
            default=24,
            min=2, max=1000,
            description="Number of Vertices per turn"
            )
    radius : FloatProperty(
            default=1.00,
            min=0.00, max=100.00,
            description="Radius for first turn"
            )
    dif_z : FloatProperty(
            default=0,
            min=-10.00, max=100.00,
            description="Increase in Z axis per turn"
            )
    # needed for 1 and 2 spiral_type
    # Archemedian variables
    dif_radius : FloatProperty(
            default=0.00,
            min=-50.00, max=50.00,
            description="Radius increment in each turn"
            )
    # step between turns(one turn equals 360 deg)
    # Log variables
    B_force : FloatProperty(
            default=1.00,
            min=0.00, max=30.00,
            description="Factor of exponent"
            )
    # Torus variables
    inner_radius : FloatProperty(
            default=0.20,
            min=0.00, max=100,
            description="Inner Radius of Torus"
            )
    dif_inner_radius : FloatProperty(
            default=0,
            min=-10, max=100,
            description="Increase of inner Radius per Cycle"
            )
    dif_radius : FloatProperty(
            default=0,
            min=-10, max=100,
            description="Increase of Torus Radius per Cycle"
            )
    cycles : FloatProperty(
            default=1,
            min=0.00, max=1000,
            description="Number of Cycles"
            )
    curves_number : IntProperty(
            default=1,
            min=1, max=400,
            description="Number of curves of spiral"
            )
    touch: BoolProperty(
            default=False,
            description="No empty spaces between cycles"
            )
    # Curve Options
    shapeItems = [
        ('2D', "2D", "2D shape Curve"),
        ('3D', "3D", "3D shape Curve")]
    shape : EnumProperty(
            name="2D / 3D",
            items=shapeItems,
            description="2D or 3D Curve",
            default='3D'
            )
    curve_type : EnumProperty(
            name="Output splines",
            description="Type of splines to output",
            items=[
            ('POLY', "Poly", "Poly Spline type"),
            ('NURBS', "Nurbs", "Nurbs Spline type"),
            ('BEZIER', "Bezier", "Bezier Spline type")],
            default='POLY'
            )
    use_cyclic_u : BoolProperty(
            name="Cyclic",
            default=False,
            description="make curve closed"
            )
    endp_u : BoolProperty(
            name="Use endpoint u",
            default=True,
            description="stretch to endpoints"
            )
    order_u : IntProperty(
            name="Order u",
            default=4,
            min=2, soft_min=2,
            max=6, soft_max=6,
            description="Order of nurbs spline"
            )
    handleType : EnumProperty(
            name="Handle type",
            default='VECTOR',
            description="Bezier handles type",
            items=[
            ('VECTOR', "Vector", "Vector type Bezier handles"),
            ('AUTO', "Auto", "Automatic type Bezier handles")]
            )
    startlocation : FloatVectorProperty(
            name="",
            description="Start location",
            default=(0.0, 0.0, 0.0),
            subtype='TRANSLATION'
            )
    rotation_euler : FloatVectorProperty(
            name="",
            description="Rotation",
            default=(0.0, 0.0, 0.0),
            subtype='EULER'
            )

    def draw(self, context):
        layout = self.layout
        col = layout.column_flow(align=True)

        col.label(text="Presets:")

        row = col.row(align=True)
        row.menu("OBJECT_MT_spiral_curve_presets",
                 text=bpy.types.OBJECT_MT_spiral_curve_presets.bl_label)
        row.operator("curve_extras.spiral_presets", text=" + ")
        op = row.operator("curve_extras.spiral_presets", text=" - ")
        op.remove_active = True

        layout.prop(self, "spiral_type")
        layout.prop(self, "spiral_direction")

        col = layout.column(align=True)
        col.label(text="Spiral Parameters:")
        col.prop(self, "turns", text="Turns")
        col.prop(self, "steps", text="Steps")

        box = layout.box()
        if self.spiral_type == 'ARCH':
            box.label(text="Archemedian Settings:")
            col = box.column(align=True)
            col.prop(self, "dif_radius", text="Radius Growth")
            col.prop(self, "radius", text="Radius")
            col.prop(self, "dif_z", text="Height")

        if self.spiral_type == 'LOG':
            box.label(text="Logarithmic Settings:")
            col = box.column(align=True)
            col.prop(self, "radius", text="Radius")
            col.prop(self, "B_force", text="Expansion Force")
            col.prop(self, "dif_z", text="Height")

        if self.spiral_type == 'SPHERE':
            box.label(text="Spheric Settings:")
            box.prop(self, "radius", text="Radius")

        if self.spiral_type == 'TORUS':
            box.label(text="Torus Settings:")
            col = box.column(align=True)
            col.prop(self, "cycles", text="Number of Cycles")

            if self.dif_inner_radius == 0 and self.dif_z == 0:
                self.cycles = 1
            col.prop(self, "radius", text="Radius")

            if self.dif_z == 0:
                col.prop(self, "dif_z", text="Height per Cycle")
            else:
                box2 = box.box()
                col2 = box2.column(align=True)
                col2.prop(self, "dif_z", text="Height per Cycle")
                col2.prop(self, "touch", text="Make Snail")

            col = box.column(align=True)
            col.prop(self, "curves_number", text="Curves Number")
            col.prop(self, "inner_radius", text="Inner Radius")
            col.prop(self, "dif_radius", text="Increase of Torus Radius")
            col.prop(self, "dif_inner_radius", text="Increase of Inner Radius")

        row = layout.row()
        row.prop(self, "shape", expand=True)
        
        # output options
        col = layout.column()
        col.label(text="Output Curve Type:")
        col.row().prop(self, "curve_type", expand=True)
        
        if self.curve_type == 'NURBS':
            col.prop(self, "order_u")
        elif self.curve_type == 'BEZIER':
            col.row().prop(self, 'handleType', expand=True)

        col = layout.column()
        col.row().prop(self, "use_cyclic_u", expand=True)
        
        box = layout.box()
        box.label(text="Location:")
        box.prop(self, "startlocation")
        box = layout.box()
        box.label(text="Rotation:")
        box.prop(self, "rotation_euler")

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        time_start = time.time()
        self.align_matrix = align_matrix(context, self.startlocation)
        draw_curve(self, context, self.align_matrix)

        #self.report({'INFO'},
                    #"Drawing Spiral Finished: %.4f sec" % (time.time() - time_start))

        return {'FINISHED'}


class CURVE_EXTRAS_OT_spirals_presets(AddPresetBase, Operator):
    bl_idname = "curve_extras.spiral_presets"
    bl_label = "Spirals"
    bl_description = "Spirals Presets"
    preset_menu = "OBJECT_MT_spiral_curve_presets"
    preset_subdir = "curve_extras/curve.spirals"

    preset_defines = [
            "op = bpy.context.active_operator",
            ]
    preset_values = [
            "op.spiral_type",
            "op.curve_type",
            "op.spiral_direction",
            "op.turns",
            "op.steps",
            "op.radius",
            "op.dif_z",
            "op.dif_radius",
            "op.B_force",
            "op.inner_radius",
            "op.dif_inner_radius",
            "op.cycles",
            "op.curves_number",
            "op.touch",
            ]


class OBJECT_MT_spiral_curve_presets(Menu):
    '''Presets for curve.spiral'''
    bl_label = "Spiral Curve Presets"
    bl_idname = "OBJECT_MT_spiral_curve_presets"
    preset_subdir = "curve_extras/curve.spirals"
    preset_operator = "script.execute_preset"

    draw = bpy.types.Menu.draw_preset


# Register
classes = [
    CURVE_OT_spirals,
    CURVE_EXTRAS_OT_spirals_presets,
    OBJECT_MT_spiral_curve_presets
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
