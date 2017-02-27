bl_info = {
    "name": "Arrange on Curve",
    "author": "Mano-Wii",
    "version": (6, 3, 0),
    "blender": (2, 7, 7),
    "location": "View3D > TOOLS > Mano-Wii > Dist_Mano",
    "description": "Arrange objects along a curve",
    "warning": "Select curve",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?361029-Specify-an-object-from-a-list-with-all-selectable-objects",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "3D View"
    }

import bpy, mathutils

FLT_MIN = 0.004

class PanelDupliCurve(bpy.types.Panel) :
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Tools"
    bl_label = "Duplicate on curve"

    @classmethod
    def poll(cls, context):
        return context.object and context.mode == 'OBJECT' and context.object.type == 'CURVE'

    def draw(self, context) :
        layout = self.layout
        layout.prop(context.scene, "use_selected")
        if not context.scene.use_selected:
            layout.prop(context.scene, "select_type", expand=True)
            if context.scene.select_type == 'O':
                layout.column(align = True).prop_search(context.scene, "objeto_arranjar", bpy.data, "objects")
            elif context.scene.select_type == 'G':
                layout.column(align = True).prop_search(context.scene, "objeto_arranjar", bpy.data, "groups")
        if context.object.type == 'CURVE':
            layout.operator("object.arranjar_numa_curva", text = "Arrange Objects")

class DupliCurve(bpy.types.Operator):
    bl_idname = "object.arranjar_numa_curva"
    bl_label = "Arrange Objects"
    bl_options = {'REGISTER', 'UNDO'}

    use_distance = bpy.props.EnumProperty(
        items = [
            ("D", "Distance", "Objects are arranged depending on the distance", 0),
            ("Q", "Quantity", "Objects are arranged depending on the quantity", 1),
            ("R", "Range", "Objects are arranged uniformly between the corners", 2)
            ]
    )

    distance = bpy.props.FloatProperty(
        name = "Distance",
        description = "Distancia entre objetos",
        default = 1.0,
        min = FLT_MIN,
        soft_min = 0.1,
        unit='LENGTH',
      )

    object_qt = bpy.props.IntProperty(
        name = "Quantity",
        description = "Object amount.",
        default = 2,
        min = 0,
      )

    scale = bpy.props.FloatProperty(
        name = "Scale",
        description = "Object Scale",
        default = 1.0,
        min = FLT_MIN,
        unit='LENGTH',
      )

    Yaw = bpy.props.FloatProperty(default=0.0,name="X", unit='ROTATION')
    Pitch = bpy.props.FloatProperty(default=0.0,name="Y", unit='ROTATION')
    Roll = bpy.props.FloatProperty(default=0.0,name="Z", unit='ROTATION')

    max_angle = bpy.props.FloatProperty(default = 1.57079, max = 3.141592, name="Angle", unit='ROTATION')
    offset = bpy.props.FloatProperty(default = 0.0, name="offset", unit='LENGTH')

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "use_distance", text="")
        col = layout.column(align=True)
        if self.use_distance == "D":
            col.prop(self, "distance")
        elif self.use_distance == "Q":
            col.prop(self, "object_qt")
        else:
            col.prop(self, "distance")
            col.prop(self, "max_angle")
            col.prop(self, "offset")

        col = layout.column(align=True)
        col.prop(self, "scale")
        col.prop(self, "Yaw")
        col.prop(self, "Pitch")
        col.prop(self, "Roll")

    def Glpoints(self, curve):
        Gpoints = []
        for i, spline in enumerate(curve.data.splines):
            segments = len(spline.bezier_points)
            if segments >= 2:
                r = spline.resolution_u + 1

                points = []
                for j in range(segments):
                    bp1 = spline.bezier_points[j]
                    inext = (j + 1)
                    if inext == segments:
                        if not spline.use_cyclic_u:
                            break
                        inext = 0
                    bp2 = spline.bezier_points[inext]
                    if bp1.handle_right_type == bp2.handle_left_type == 'VECTOR':
                        _points = (bp1.co, bp2.co) if j == 0 else (bp2.co,)
                    else:
                        knot1 = bp1.co
                        handle1 = bp1.handle_right
                        handle2 = bp2.handle_left
                        knot2 = bp2.co
                        _points = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, r)
                    points.extend(_points)
                Gpoints.append(tuple((curve.matrix_world*p for p in points)))
            elif len(spline.points) >= 2:
                l = [curve.matrix_world*p.co.xyz for p in spline.points]
                if spline.use_cyclic_u:
                    l.append(l[0])
                Gpoints.append(tuple(l))

            if self.use_distance == "R":
                max_angle = self.max_angle
                tmp_Gpoints = []
                sp = Gpoints[i]
                sp2 = [sp[0], sp[1]]
                lp = sp[1]
                v1 = lp - sp[0]
                for p in sp[2:]:
                    v2 = p - lp
                    try:
                        if (3.14158 - v1.angle(v2)) < max_angle:
                            tmp_Gpoints.append(tuple(sp2))
                            sp2 = [lp]
                    except Exception as e:
                        print(e)
                        pass
                    sp2.append(p)
                    v1 = v2
                    lp = p
                tmp_Gpoints.append(tuple(sp2))
                Gpoints = Gpoints[:i] + tmp_Gpoints

        lengths = []
        if self.use_distance != "D":
            for sp in Gpoints:
                lp = sp[1]
                leng = (lp - sp[0]).length
                for p in sp[2:]:
                    leng += (p - lp).length
                    lp = p
                lengths.append(leng)
        return Gpoints, lengths

    def execute(self, context):
        if context.object.type != 'CURVE':
            return {'CANCELLED'}

        curve = context.active_object
        Gpoints, lengs = self.Glpoints(curve)

        if context.scene.use_selected:
            G_Objeto = context.selected_objects
            G_Objeto.remove(curve)
            if not G_Objeto:
                return {'CANCELLED'}
        elif context.scene.select_type == 'O':
            G_Objeto = bpy.data.objects[context.scene.objeto_arranjar],
        elif context.scene.select_type == 'G':
            G_Objeto = bpy.data.groups[context.scene.objeto_arranjar].objects
        #qt = 0 #(To see in System Console)
        yawMatrix = mathutils.Matrix.Rotation(self.Yaw, 4, 'X')
        pitchMatrix = mathutils.Matrix.Rotation(self.Pitch, 4, 'Y')
        rollMatrix = mathutils.Matrix.Rotation(self.Roll, 4, 'Z')
        max_angle = self.max_angle

        if self.use_distance == "D":
            dist  = self.distance
            for sp_points in Gpoints:
                dx = 0.0 # Length of initial calculation of section
                last_point = sp_points[0]
                j = 0
                for point in sp_points[1:]:
                    vetorx  = point-last_point# Vector spline section
                    quat = mathutils.Vector.to_track_quat(vetorx, 'X', 'Z') # Tracking the selected objects
                    quat = quat.to_matrix().to_4x4()

                    v_len = vetorx.length
                    if v_len > 0.0:
                        dx+= v_len # Defined length calculation equal total length of the spline section
                        v_norm = vetorx/v_len
                        while dx > dist:
                            object = G_Objeto[j % len(G_Objeto)]
                            j += 1
                            dx -= dist # Calculating the remaining length of the section
                            obj = object.copy()
                            context.scene.objects.link(obj)
                            obj.matrix_world = quat*yawMatrix*pitchMatrix*rollMatrix
                            obj.matrix_world.translation = point - v_norm*dx # Putting in the correct position
                            obj.scale *= self.scale
                        last_point = point

        elif self.use_distance == "Q":
            object_qt = self.object_qt + 1
            for i, sp_points in enumerate(Gpoints):
                dx = 0.0 # Length of initial calculation of section
                dist = lengs[i] / object_qt
                last_point = sp_points[0]
                j = 0
                for point in sp_points[1:]:
                    vetorx  = point-last_point# Vector spline section
                    quat = mathutils.Vector.to_track_quat(vetorx, 'X', 'Z') # Tracking the selected objects
                    quat = quat.to_matrix().to_4x4()

                    v_len = vetorx.length
                    if v_len > 0.0:
                        dx+= v_len # Defined length calculation equal total length of the spline section
                        v_norm = vetorx/v_len
                        while dx > dist:
                            object = G_Objeto[j % len(G_Objeto)]
                            j += 1
                            dx -= dist # Calculating the remaining length of the section
                            obj = object.copy()
                            context.scene.objects.link(obj)
                            obj.matrix_world = quat*yawMatrix*pitchMatrix*rollMatrix
                            obj.matrix_world.translation = point - v_norm*dx # Putting in the correct position
                            obj.scale *= self.scale
                        last_point = point

        else:
            dist  = self.distance
            offset2 = 2*self.offset
            for i, sp_points in enumerate(Gpoints):
                leng = lengs[i] - offset2
                rest = leng % dist
                offset = offset2 + rest
                leng -= rest
                #leng += FLT_MIN
                offset /= 2
                last_point = sp_points[0]

                dx = dist - offset # Length of initial calculation of section
                j = 0
                for point in sp_points[1:]:
                    vetorx  = point-last_point# Vector spline section
                    quat = mathutils.Vector.to_track_quat(vetorx, 'X', 'Z') # Tracking the selected objects
                    quat = quat.to_matrix().to_4x4()

                    v_len = vetorx.length
                    if v_len > 0.0:
                        dx += v_len
                        v_norm = vetorx/v_len
                        while dx >= dist and leng >= 0.0:
                            leng -= dist
                            dx -= dist # Calculating the remaining length of the section
                            object = G_Objeto[j % len(G_Objeto)]
                            j += 1
                            obj = object.copy()
                            context.scene.objects.link(obj)
                            obj.matrix_world = quat*yawMatrix*pitchMatrix*rollMatrix
                            obj.matrix_world.translation = point - v_norm*dx # Putting in the correct position
                            obj.scale *= self.scale
                        last_point = point

        return {"FINISHED"}

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.use_selected = bpy.props.BoolProperty(
        name='Use Selected',
        description='Use the selected objects to duplicate',
        default=True,
        )
    bpy.types.Scene.objeto_arranjar = bpy.props.StringProperty(name="")
    bpy.types.Scene.select_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Select object or group",
        items = [
            ('O',"OBJECT","make duplicates of a specific object"),
            ('G',"GROUP","make duplicates of the objects in a group"),
        ],
        default='O',
    )

def unregister() :
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.objeto_arranjar
    del bpy.types.Scene.use_selected
    del bpy.types.Scene.select_type

if __name__ == "__main__" :
    register()
