# SPDX-FileCopyrightText: 2025 Damien Picard
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .sun_calc import (
    calc_analemma,
    calc_surface,
)

import bpy
from bpy.app.translations import pgettext_data as data_
from bpy.props import BoolProperty, IntProperty
from bpy.types import Operator


class SUNPOS_OT_Create_Analemmas_Object(Operator):
    """Create an object from the Sun position's analemmas"""
    bl_idname = "world.sunpos_create_analemmas_object"
    bl_label = "Create Sun Analemmas Object"
    bl_options = {'REGISTER', 'UNDO'}

    only_above_ground: BoolProperty(
        name="Only Above Ground",
        description="Discard the part of the analemmas that is below ground",
        default=True,
    )
    points: IntProperty(
        name="Points",
        description="Number of points for each analemma",
        default=365,
        min=36,
        max=365,
    )

    def execute(self, context):
        name = data_("Analemma")
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        coords, edges = calc_analemma(
            context.scene,
            points=self.points,
            only_above_ground=self.only_above_ground,
        )
        mesh.from_pydata(coords, edges, [])
        context.collection.objects.link(obj)
        return {'FINISHED'}


class SUNPOS_OT_Create_Surface_Object(Operator):
    """Create an object from the Sun position's surface visualization"""
    bl_idname = "world.sunpos_create_surface_object"
    bl_label = "Create Sun Surface Object"
    bl_options = {'REGISTER', 'UNDO'}

    only_above_ground: BoolProperty(
        name="Only Above Ground",
        description="Discard the part of the surface that is below ground",
        default=True,
    )

    def execute(self, context):
        name = data_("Sun Surface")
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        coords, faces = calc_surface(
            context.scene,
            # points=self.points,
            only_above_ground=self.only_above_ground,
            do_triangulate=False,
        )
        mesh.from_pydata(coords, [], faces)

        mesh.shade_smooth()
        context.collection.objects.link(obj)
        return {'FINISHED'}
