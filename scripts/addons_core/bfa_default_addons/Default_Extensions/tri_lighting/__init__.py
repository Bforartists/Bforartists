# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# author Daniel Schalla, maintained by meta-androcto

import bpy
from bpy.types import Operator
from bpy.props import (
        EnumProperty,
        FloatProperty,
        IntProperty,
        )
from math import (
        sin, cos,
        radians,
        sqrt,
        )


class OBJECT_OT_TriLighting(Operator):
    bl_idname = "object.trilighting"
    bl_label = "3-Point Lighting"
    bl_description = ("Add 3 point lighting around selected object(s)")
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'CYCLES', 'EEVEE'}

    height: FloatProperty(
        name="Height",
        subtype="DISTANCE",
        default=5,
    )
    distance: FloatProperty(
        name="Distance",
        subtype="DISTANCE",
        min=0.1,
        default=5,
    )
    energy: IntProperty(
        name="Base Energy",
        subtype='POWER',
        min=1,
        default=100,
    )
    contrast: IntProperty(
        name="Contrast",
        subtype="PERCENTAGE",
        min=-100, max=100,
        default=50,
    )
    leftangle: IntProperty(
        name="Left Angle",
        subtype="ANGLE",
        min=1, max=90,
        default=26,
    )
    rightangle: IntProperty(
        name="Right Angle",
        subtype="ANGLE",
        min=1, max=90,
        default=45,
    )
    backangle: IntProperty(
        name="Back Angle",
        subtype="ANGLE",
        min=90, max=270,
        default=235,
    )

    # Light Type
    Light_Type_List = [
        ('POINT', "Point", "Point Light"),
        ('SUN', "Sun", "Sun Light"),
        ('SPOT', "Spot", "Spot Light"),
        ('AREA', "Area", "Area Light")
    ]
    primarytype: EnumProperty(
        attr='tl_type',
        name="Key Type",
        description="Choose the types of Key Lights you would like",
        items=Light_Type_List,
        default='AREA',
    )
    secondarytype: EnumProperty(
        attr='tl_type',
        name="Fill + Back Type",
        description="Choose the types of secondary Lights you would like",
        items=Light_Type_List,
        default="AREA",
    )

    # Light Shape
    Light_Shape_List = [
        ('SQUARE', "Square", "Square Light"),
        ('RECTANGLE', "Rectangle", "Rectangular Light"),
        ('DISK', "Disk", "Disk Light"),
        ('ELLIPSE', "Ellipse", "Elliptical Light")
    ]
    key_light_shape: EnumProperty(
        name="Key Light Shape",
        items=Light_Shape_List,
        default='SQUARE',
    )
    secondary_light_shape: EnumProperty(
        name="Fill + Back Light Shape",
        items=Light_Shape_List,
        default='SQUARE',
    )

    # Light Properties
    # Key Light Size (Single size for SQUARE and DISK)
    key_light_size: FloatProperty(
        name="Key Light Size",
        subtype='DISTANCE',
        min=0,
        default=1,
    )

    # Fill + Back Light Size (Single size for SQUARE and DISK)
    secondary_light_size: FloatProperty(
        name="Fill + Back Light Size",
        subtype='DISTANCE',
        min=0,
        default=1,
    )

    # Key Light Size (Separate X and Y for RECTANGLE and ELLIPSE)
    key_light_size_x: FloatProperty(
        name="Key Light Size X",
        subtype='DISTANCE',
        min=0,
        default=1,
    )

    key_light_size_y: FloatProperty(
        name="Key Light Size Y",
        subtype='DISTANCE',
        min=0,
        default=1,
    )

    # Fill + Back Light Size (Separate X and Y for RECTANGLE and ELLIPSE)
    secondary_light_size_x: FloatProperty(
        name="Fill + Back Light Size X",
        subtype='DISTANCE',
        min=0,
        default=1,
    )

    secondary_light_size_y: FloatProperty(
        name="Fill + Back Light Size Y",
        subtype='DISTANCE',
        min=0,
        default=1,
    )

    # Shadow Soft Size
    shadow_soft_size_key: FloatProperty(
        name="Key Light Shadow Soft Size",
        subtype='DISTANCE',
        default=0.0,
        min=0.0,
    )

    shadow_soft_size_fill: FloatProperty(
        name="Fill + Back Light Shadow Soft Size",
        subtype='DISTANCE',
        default=0.0,
        min=0.0,
    )

    # Spot Light Size and Blend
    spot_size_key: FloatProperty(
        name="Key Spot Light Size",
        subtype='ANGLE',
        min=0, max=3.14,
        default=0.7853982,
    )

    spot_blend_key: FloatProperty(
        name="Key Spot Light Blend",
        min=0.0, max=1.0,
        default=0.150,
    )

    spot_size_fill: FloatProperty(
        name="Fill + Back Spot Light Size",
        subtype='ANGLE',
        min=0, max=3.14,
        default=0.7853982,
    )

    spot_blend_fill: FloatProperty(
        name="Fill + Back Spot Light Blend",
        min=0.0, max=1.0,
        default=0.150,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "distance")
        layout.separator()

        col = layout.column(align=True)
        col.prop(self, "energy")
        col.prop(self, "contrast")
        layout.separator()

        col = layout.column(align=True)
        col.prop(self, "leftangle")
        col.prop(self, "rightangle")
        col.prop(self, "backangle")
        layout.separator()

        # Key Light Properties
        header, panel = layout.panel("KeyLightPanel", default_closed=False)
        header.label(text="Key Light")

        if panel:
            col = panel.column()
            col.prop(self, "primarytype", text="Type")

            # Area Light Shape & Size
            if self.primarytype == 'AREA':
                col.prop(self, "key_light_shape", text="Shape")

                col = panel.column(align=True)
                if self.key_light_shape in {'SQUARE', 'DISK'}:
                    col.prop(self, "key_light_size", text="Size")
                elif self.key_light_shape in {'RECTANGLE', 'ELLIPSE'}:
                    col.prop(self, "key_light_size_x", text="Size X")
                    col.prop(self, "key_light_size_y", text="Size Y")

            # Radius
            if self.primarytype in {'POINT', 'SPOT'}:
                col.prop(self, "shadow_soft_size_key", text="Radius")

            # Spot Light
            if self.primarytype == 'SPOT':
                col.prop(self, "spot_size_key", text="Spot Size")
                col.prop(self, "spot_blend_key", text="Blend", slider=True)


        # Fill + Back Light Properties
        header, panel = layout.panel("KeyLightPanel", default_closed=False)
        header.label(text="Fill & Back Light")

        if panel:
            col = panel.column()
            col.prop(self, "secondarytype", text="Type")

            # Area Light Shape & Size
            if self.secondarytype == 'AREA':
                col.prop(self, "secondary_light_shape", text="Shape")

                col = panel.column(align=True)
                if self.secondary_light_shape in {'SQUARE', 'DISK'}:
                    col.prop(self, "secondary_light_size", text="Size")
                elif self.secondary_light_shape in {'RECTANGLE', 'ELLIPSE'}:
                    row = col.row()
                    row.prop(self, "secondary_light_size_x", text="Size X")
                    row.prop(self, "secondary_light_size_y", text="Size Y")

            # Radius
            if self.secondarytype in {'POINT', 'SPOT'}:
                col.prop(self, "shadow_soft_size_fill", text="Radius")

            # Spot Light
            if self.secondarytype == 'SPOT':
                col.prop(self, "spot_size_fill", text="Spot Size")
                col.prop(self, "spot_blend_fill", text="Blend", slider=True)


    def execute(self, context):
        collection = context.collection
        scene = context.scene
        view = context.space_data

        if view.type == 'VIEW_3D' and view.use_local_camera:
            camera = view.camera
        else:
            camera = scene.camera
        if not camera:
            self.report({'WARNING'}, "Lights couldn't be placed because there is no active camera in the scene")
            return {'CANCELLED'}

        obj = bpy.context.view_layer.objects.active

        # Calculate Energy for each Lamp
        if(self.contrast > 0):
            keyEnergy = self.energy
            backEnergy = (self.energy / 100) * abs(self.contrast)
            fillEnergy = (self.energy / 100) * abs(self.contrast)
        else:
            keyEnergy = (self.energy / 100) * abs(self.contrast)
            backEnergy = self.energy
            fillEnergy = self.energy

        # Calculate Direction for each Lamp

        # Calculate current Distance and get Delta
        obj_position = obj.location
        cam_position = camera.location

        delta_position = cam_position - obj_position
        vector_length = sqrt(
                        (pow(delta_position.x, 2) +
                            pow(delta_position.y, 2) +
                            pow(delta_position.z, 2))
                        )
        if not vector_length:
            # division by zero most likely
            self.report({'WARNING'},
                        "Operation Cancelled. No viable object in the scene")

            return {'CANCELLED'}

        single_vector = (1 / vector_length) * delta_position

        # Calc back position
        singleback_vector = single_vector.copy()
        singleback_vector.x = cos(radians(self.backangle)) * single_vector.x + \
                                (-sin(radians(self.backangle)) * single_vector.y)

        singleback_vector.y = sin(radians(self.backangle)) * single_vector.x + \
                                (cos(radians(self.backangle)) * single_vector.y)

        backx = obj_position.x + self.distance * singleback_vector.x
        backy = obj_position.y + self.distance * singleback_vector.y

        backData = bpy.data.lights.new(name="TriLamp-Back", type=self.secondarytype)
        backData.energy = backEnergy

        if self.secondarytype == 'AREA':
            backData.shape = self.secondary_light_shape
            if self.secondary_light_shape in {'RECTANGLE', 'ELLIPSE'}:
                backData.size = self.secondary_light_size_x
                backData.size_y = self.secondary_light_size_y
            else:
                backData.size = self.secondary_light_size

        if self.secondarytype == 'SPOT':
            backData.spot_size = self.spot_size_fill
            backData.spot_blend = self.spot_blend_fill

        if self.secondarytype in {'POINT', 'SPOT'}:
            backData.shadow_soft_size = self.shadow_soft_size_fill

        backLamp = bpy.data.objects.new(name="TriLamp-Back", object_data=backData)
        collection.objects.link(backLamp)
        backLamp.location = (backx, backy, self.height)

        trackToBack = backLamp.constraints.new(type="TRACK_TO")
        trackToBack.target = obj
        trackToBack.track_axis = "TRACK_NEGATIVE_Z"
        trackToBack.up_axis = "UP_Y"

        # Calc right position
        singleright_vector = single_vector.copy()
        singleright_vector.x = cos(radians(self.rightangle)) * single_vector.x + \
                                (-sin(radians(self.rightangle)) * single_vector.y)

        singleright_vector.y = sin(radians(self.rightangle)) * single_vector.x + \
                                (cos(radians(self.rightangle)) * single_vector.y)

        rightx = obj_position.x + self.distance * singleright_vector.x
        righty = obj_position.y + self.distance * singleright_vector.y

        rightData = bpy.data.lights.new(name="TriLamp-Fill", type=self.secondarytype)
        rightData.energy = fillEnergy
        if self.secondarytype == 'AREA':
            rightData.shape = self.secondary_light_shape
            if self.secondary_light_shape in {'RECTANGLE', 'ELLIPSE'}:
                rightData.size = self.secondary_light_size_x
                rightData.size_y = self.secondary_light_size_y
            else:
                rightData.size = self.secondary_light_size

        if self.secondarytype == 'SPOT':
            rightData.spot_size = self.spot_size_fill
            rightData.spot_blend = self.spot_blend_fill

        if self.secondarytype in {'POINT', 'SPOT'}:
            rightData.shadow_soft_size = self.shadow_soft_size_fill

        rightLamp = bpy.data.objects.new(name="TriLamp-Fill", object_data=rightData)
        collection.objects.link(rightLamp)
        rightLamp.location = (rightx, righty, self.height)
        trackToRight = rightLamp.constraints.new(type="TRACK_TO")
        trackToRight.target = obj
        trackToRight.track_axis = "TRACK_NEGATIVE_Z"
        trackToRight.up_axis = "UP_Y"

        # Calc left position
        singleleft_vector = single_vector.copy()
        singleleft_vector.x = cos(radians(-self.leftangle)) * single_vector.x + \
                            (-sin(radians(-self.leftangle)) * single_vector.y)
        singleleft_vector.y = sin(radians(-self.leftangle)) * single_vector.x + \
                            (cos(radians(-self.leftangle)) * single_vector.y)
        leftx = obj_position.x + self.distance * singleleft_vector.x
        lefty = obj_position.y + self.distance * singleleft_vector.y

        leftData = bpy.data.lights.new(name="TriLamp-Key", type=self.primarytype)
        leftData.energy = keyEnergy
        if self.primarytype == 'AREA':
            leftData.shape = self.key_light_shape
            if self.key_light_shape in {'RECTANGLE', 'ELLIPSE'}:
                leftData.size = self.key_light_size_x
                leftData.size_y = self.key_light_size_y
            else:
                leftData.size = self.key_light_size

        if self.primarytype == 'SPOT':
            leftData.spot_size = self.spot_size_key
            leftData.spot_blend = self.spot_blend_key

        if self.primarytype in {'POINT', 'SPOT'}:
            leftData.shadow_soft_size = self.shadow_soft_size_key

        leftLamp = bpy.data.objects.new(name="TriLamp-Key", object_data=leftData)
        collection.objects.link(leftLamp)
        leftLamp.location = (leftx, lefty, self.height)
        trackToLeft = leftLamp.constraints.new(type="TRACK_TO")
        trackToLeft.target = obj
        trackToLeft.track_axis = "TRACK_NEGATIVE_Z"
        trackToLeft.up_axis = "UP_Y"

        return {'FINISHED'}


# Menu
def menu_func(self, context):
    self.layout.operator(OBJECT_OT_TriLighting.bl_idname, icon='LIGHT')


# Registration
def register():
    bpy.utils.register_class(OBJECT_OT_TriLighting)
    bpy.types.VIEW3D_MT_light_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_TriLighting)
    bpy.types.VIEW3D_MT_light_add.remove(menu_func)

if __name__ == "__main__":
    register()
