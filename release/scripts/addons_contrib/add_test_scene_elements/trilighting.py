# gpl: author Daniel Schalla

'''
bl_info = {
    "name": "Tri-Lighting Creator",
    "category": "Object",
    "author": "Daniel Schalla",
    "version": (1, 0),
    "blender": (2, 75, 0),
    "location": "Object Mode > Toolbar > Add Tri-Lighting",
    "description": "Add 3 Point Lighting to selected Object"
}
'''

import bpy
import mathutils
from bpy.props import *
import math


class TriLighting(bpy.types.Operator):
    """TriL ightning"""
    bl_idname = "object.trilighting"
    bl_label = "Tri-Lighting Creator"
    bl_options = {'REGISTER', 'UNDO'}

    height = bpy.props.FloatProperty(name="Height", default=5)
    distance = bpy.props.FloatProperty(name="Distance", default=5, min=0.1, subtype="DISTANCE")
    energy = bpy.props.IntProperty(name="Base Energy", default=3, min=1)
    contrast = bpy.props.IntProperty(name="Contrast", default=50, min=-100, max=100, subtype="PERCENTAGE")
    leftangle = bpy.props.IntProperty(name="Left Angle", default=26, min=1, max=90, subtype="ANGLE")
    rightangle = bpy.props.IntProperty(name="Right Angle", default=45, min=1, max=90, subtype="ANGLE")
    backangle = bpy.props.IntProperty(name="Back Angle", default=235, min=90, max=270, subtype="ANGLE")

    Light_Type_List = [('POINT', 'Point', 'Point Light'),
                       ('SUN', 'Sun', 'Sun Light'),
                       ('SPOT', 'Spot', 'Spot Light'),
                       ('HEMI', 'Hemi', 'Hemi Light'),
                       ('AREA', 'Area', 'Area Light')]
    primarytype = EnumProperty(attr='tl_type',
                               name='Key Type',
                               description='Choose the type off Key Light you would like',
                               items=Light_Type_List, default='HEMI')

    secondarytype = EnumProperty(attr='tl_type',
                                 name='Fill+Back Type',
                                 description='Choose the type off secondary Light you would like',
                                 items=Light_Type_List, default='POINT')

    def execute(self, context):
        scene = context.scene
        view = context.space_data
        if view.type == 'VIEW_3D' and not view.lock_camera_and_layers:
            camera = view.camera
        else:
            camera = scene.camera

        if (camera is None):

            cam_data = bpy.data.cameras.new(name='Camera')
            cam_obj = bpy.data.objects.new(name='Camera', object_data=cam_data)
            scene.objects.link(cam_obj)
            scene.camera = cam_obj
            bpy.ops.view3d.camera_to_view()
            camera = cam_obj
            bpy.ops.view3d.viewnumpad(type='TOP')

        obj = bpy.context.scene.objects.active

# Calculate Energy for each Lamp

        if(self.contrast > 0):
            keyEnergy = self.energy
            backEnergy = (self.energy / 100) * abs(self.contrast)
            fillEnergy = (self.energy / 100) * abs(self.contrast)
        else:
            keyEnergy = (self.energy / 100) * abs(self.contrast)
            backEnergy = self.energy
            fillEnergy = self.energy

        print(self.contrast)
# Calculate Direction for each Lamp

# Calculate current Distance and get Delta
        obj_position = obj.location
        cam_position = camera.location

        delta_position = cam_position - obj_position
        vector_length = math.sqrt((pow(delta_position.x, 2) + pow(delta_position.y, 2) + pow(delta_position.z, 2)))
        single_vector = (1 / vector_length) * delta_position

# Calc back position
        singleback_vector = single_vector.copy()
        singleback_vector.x = math.cos(math.radians(self.backangle)) * single_vector.x + (-math.sin(math.radians(self.backangle)) * single_vector.y)
        singleback_vector.y = math.sin(math.radians(self.backangle)) * single_vector.x + (math.cos(math.radians(self.backangle)) * single_vector.y)
        backx = obj_position.x + self.distance * singleback_vector.x
        backy = obj_position.y + self.distance * singleback_vector.y

        backData = bpy.data.lamps.new(name="TriLamp-Back", type=self.secondarytype)
        backData.energy = backEnergy

        backLamp = bpy.data.objects.new(name="TriLamp-Back", object_data=backData)
        scene.objects.link(backLamp)
        backLamp.location = (backx, backy, self.height)

        trackToBack = backLamp.constraints.new(type="TRACK_TO")
        trackToBack.target = obj
        trackToBack.track_axis = "TRACK_NEGATIVE_Z"
        trackToBack.up_axis = "UP_Y"

        # Calc right position
        singleright_vector = single_vector.copy()
        singleright_vector.x = math.cos(math.radians(self.rightangle)) * single_vector.x + (-math.sin(math.radians(self.rightangle)) * single_vector.y)
        singleright_vector.y = math.sin(math.radians(self.rightangle)) * single_vector.x + (math.cos(math.radians(self.rightangle)) * single_vector.y)
        rightx = obj_position.x + self.distance * singleright_vector.x
        righty = obj_position.y + self.distance * singleright_vector.y

        rightData = bpy.data.lamps.new(name="TriLamp-Fill", type=self.secondarytype)
        rightData.energy = fillEnergy
        rightLamp = bpy.data.objects.new(name="TriLamp-Fill", object_data=rightData)
        scene.objects.link(rightLamp)
        rightLamp.location = (rightx, righty, self.height)
        trackToRight = rightLamp.constraints.new(type="TRACK_TO")
        trackToRight.target = obj
        trackToRight.track_axis = "TRACK_NEGATIVE_Z"
        trackToRight.up_axis = "UP_Y"

        # Calc left position
        singleleft_vector = single_vector.copy()
        singleleft_vector.x = math.cos(math.radians(-self.leftangle)) * single_vector.x + (-math.sin(math.radians(-self.leftangle)) * single_vector.y)
        singleleft_vector.y = math.sin(math.radians(-self.leftangle)) * single_vector.x + (math.cos(math.radians(-self.leftangle)) * single_vector.y)
        leftx = obj_position.x + self.distance * singleleft_vector.x
        lefty = obj_position.y + self.distance * singleleft_vector.y

        leftData = bpy.data.lamps.new(name="TriLamp-Key", type=self.primarytype)
        leftData.energy = keyEnergy

        leftLamp = bpy.data.objects.new(name="TriLamp-Key", object_data=leftData)
        scene.objects.link(leftLamp)
        leftLamp.location = (leftx, lefty, self.height)
        trackToLeft = leftLamp.constraints.new(type="TRACK_TO")
        trackToLeft.target = obj
        trackToLeft.track_axis = "TRACK_NEGATIVE_Z"
        trackToLeft.up_axis = "UP_Y"

        return {'FINISHED'}

