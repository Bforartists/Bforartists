# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import math

from collections import namedtuple

from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    PointerProperty
)


ScatterSettings = namedtuple("ScatterSettings",
    ["seed", "density", "radius", "scale", "random_scale",
     "rotation", "normal_offset", "use_normal_rotation"])

class ObjectScatterProperties(bpy.types.PropertyGroup):
    seed: IntProperty(
        name="Seed",
        default=0,
        description="Change it to get a different scatter pattern",
    )

    density: FloatProperty(
        name="Density",
        default=10,
        min=0,
        soft_max=50,
        description="The amount of objects per unit on the line",
    )

    radius: FloatProperty(
        name="Radius",
        default=1,
        min=0,
        soft_max=5,
        subtype='DISTANCE',
        unit='LENGTH',
        description="Maximum distance of the objects to the line",
    )

    scale: FloatProperty(
        name="Scale",
        default=0.3,
        min=0.00001,
        soft_max=1,
        description="Size of the generated objects",
    )

    random_scale_percentage: FloatProperty(
        name="Random Scale Percentage",
        default=80,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        precision=0,
        description="Increase to get a larger range of sizes",
    )

    rotation: FloatProperty(
        name="Rotation",
        default=0.5,
        min=0,
        max=math.pi * 2,
        soft_max=math.pi / 2,
        subtype='ANGLE',
        unit='ROTATION',
        description="Maximum rotation of the generated objects",
    )

    normal_offset: FloatProperty(
        name="Normal Offset",
        default=0,
        soft_min=-1.0,
        soft_max=1.0,
        description="Distance from the surface",
    )

    use_normal_rotation: BoolProperty(
        name="Use Normal Rotation",
        default=True,
        description="Rotate the instances according to the surface normals",
    )

    def to_settings(self):
        return ScatterSettings(
            seed=self.seed,
            density=self.density,
            radius=self.radius,
            scale=self.scale,
            random_scale=self.random_scale_percentage / 100,
            rotation=self.rotation,
            normal_offset=self.normal_offset,
            use_normal_rotation=self.use_normal_rotation,
        )


class ObjectScatterPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_object_scatter"
    bl_label = "Object Scatter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scatter = context.scene.scatter_properties

        layout.prop(scatter, "density", slider=True)
        layout.prop(scatter, "radius", slider=True)

        col = layout.column(align=True)
        col.prop(scatter, "scale", slider=True)
        col.prop(scatter, "random_scale_percentage", text="Randomness", slider=True)

        layout.prop(scatter, "use_normal_rotation")
        layout.prop(scatter, "rotation", slider=True)
        layout.prop(scatter, "normal_offset", text="Offset", slider=True)
        layout.prop(scatter, "seed")

def draw_menu(self, context):
    layout = self.layout
    layout.operator("object.scatter")

classes = (
    ObjectScatterProperties,
    ObjectScatterPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.scatter_properties = PointerProperty(type=ObjectScatterProperties)
    bpy.types.VIEW3D_MT_object.append(draw_menu)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.scatter_properties
    bpy.types.VIEW3D_MT_object.remove(draw_menu)
