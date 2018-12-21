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

import bpy
import math

from collections import namedtuple

from bpy.props import (
    IntProperty,
    FloatProperty,
    PointerProperty
)


ScatterSettings = namedtuple("ScatterSettings",
    ["seed", "density", "radius", "scale", "random_scale",
     "rotation", "normal_offset"])

class ObjectScatterProperties(bpy.types.PropertyGroup):
    seed: IntProperty(
        name="Seed",
        default=0
    )

    density: FloatProperty(
        name="Density",
        default=10,
        min=0,
        soft_max=50
    )

    radius: FloatProperty(
        name="Radius",
        default=1,
        min=0,
        soft_max=5,
        subtype='DISTANCE',
        unit='LENGTH'
    )

    scale: FloatProperty(
        name="Scale",
        default=0.3,
        min=0.00001,
        soft_max=1
    )

    random_scale_percentage: FloatProperty(
        name="Random Scale Percentage",
        default=80,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        precision=0
    )

    rotation: FloatProperty(
        name="Rotation",
        default=0.5,
        min=0,
        max=math.pi * 2,
        soft_max=math.pi / 2,
        subtype='ANGLE',
        unit='ROTATION'
    )

    normal_offset: FloatProperty(
        name="Normal Offset",
        default=0,
        soft_min=-1.0,
        soft_max=1.0
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
        )


class ObjectScatterPanel(bpy.types.Panel):
    bl_label = "Object Scatter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = '.objectmode'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scatter = context.scene.scatter_properties

        layout.prop(scatter, "density", slider=True)
        layout.prop(scatter, "radius", slider=True)

        col = layout.column(align=True)
        col.prop(scatter, "scale", slider=True)
        col.prop(scatter, "random_scale_percentage", text="Randomness", slider=True)

        layout.prop(scatter, "rotation", slider=True)
        layout.prop(scatter, "normal_offset", text="Offset", slider=True)
        layout.prop(scatter, "seed")


classes = (
    ObjectScatterProperties,
    ObjectScatterPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.scatter_properties = PointerProperty(type=ObjectScatterProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.scatter_properties
