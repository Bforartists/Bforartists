# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import bmesh
from math import sin, cos, tan, pi
from mathutils import Vector
from .pdt_functions import (
    set_mode,
    view_coords,
)

class PDT_OT_WaveGenerator(bpy.types.Operator):
    """Generate Trig Waves in Active Object"""
    bl_idname = "pdt.wave_generator"
    bl_label = "Generate Waves"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        pg = context.scene.pdt_pg
        return pg.trig_obj is not None

    def execute(self, context):
        """Generate Trig Waves in Active Object.

        Note:
            Uses all the PDT trig_* variables.

            This function will draw a trigonometrical wave based upon cycle length
            One cycle is assumed to be 180 degrees, so half a revolution of an imaginary
            rotating object. If a full cycle from 0 to 360 degrees is required, the cycles
            number should be set to 2.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        pg = context.scene.pdt_pg
        plane = pg.plane
        # Find the horizontal, vertical and depth axes in the view from working plane.
        # Order is: H, V, D.
        #
        a1, a2, a3 = set_mode(plane)
        # Make sure object selected in the UI is the active object.
        #
        for obj in bpy.data.objects:
            obj.select_set(state=False)
        context.view_layer.objects.active = pg.trig_obj
        # x_inc is the increase in X (Horiz axis) per unit of resolution of the wave, so if
        # resolution is 9, nine points will be drawn in each cycle representing increases of
        # 20 degrees and 1/9th of the cycle length.
        #
        x_inc = pg.trig_len / pg.trig_res

        if pg.trig_del:
            # Delete all existing vertices first.
            #
            bpy.ops.object.mode_set(mode='EDIT')
            for v in pg.trig_obj.data.vertices:
                v.select = True
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

        if pg.trig_obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(pg.trig_obj.data)

        # Loop for each point in the number of cycles times the resolution value.
        # Uses basic trigonomtry to calculate the wave locations.
        # If Absolute has been set, all values are made positive.
        # z_val is assumed to be the offset from the horizontal axis of the wave.
        # These values will be offset by the Offset Vector given in the UI.
        #
        for i in range((pg.trig_res * pg.trig_cycles) + 1):
            # Uses a calculation of trig function angle of imaginary object times maximum amplitude
            # of wave. So with reolution at 9, angular increments are 20 degrees.
            # Angles must be in Radians for this calcultion.
            #
            if pg.trig_type == "sin":
                if pg.trig_abs:
                    z_val = abs(sin((i / pg.trig_res) * pi) * pg.trig_amp)
                else:
                    z_val = sin((i / pg.trig_res) * pi) * pg.trig_amp
            elif pg.trig_type == "cos":
                if pg.trig_abs:
                    z_val = abs(cos((i / pg.trig_res) * pi) * pg.trig_amp)
                else:
                    z_val = cos((i / pg.trig_res) * pi) * pg.trig_amp
            else:
                if pg.trig_abs:
                    z_val = abs(tan((i / pg.trig_res) * pi) * pg.trig_amp)
                else:
                    z_val = tan((i / pg.trig_res) * pi) * pg.trig_amp

                if abs(z_val) > pg.trig_tanmax:
                    if z_val >= 0:
                        z_val = pg.trig_tanmax
                    else:
                        if pg.trig_abs:
                            z_val = pg.trig_tanmax
                        else:
                            z_val = -pg.trig_tanmax

            # Start with Offset Vector from UI and add wave offsets to it.
            # Axis a3 (depth) is never changed from offset vector in UI.
            #
            vert_loc = Vector(pg.trig_off)
            vert_loc[a1] = vert_loc[a1] + (i * x_inc)
            vert_loc[a2] = vert_loc[a2] + z_val
            if plane == "LO":
                # Translate view local coordinates (horiz, vert, depth) into World XYZ
                #
                vert_loc = view_coords(vert_loc[a1], vert_loc[a2], vert_loc[a3])
            vertex_new = bm.verts.new(vert_loc)
            # Refresh Vertices list in object data.
            #
            bm.verts.ensure_lookup_table()
            if i > 0:
                # Make an edge from last two vertices in object data.
                #
                bm.edges.new([bm.verts[-2], vertex_new])

        bmesh.update_edit_mesh(pg.trig_obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        return {"FINISHED"}
