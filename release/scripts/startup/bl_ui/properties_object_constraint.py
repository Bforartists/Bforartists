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

# <pep8 compliant>
import bpy
from bpy.types import Panel
from blf import gettext as _


class ConstraintButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "constraint"

    def draw_constraint(self, context, con):
        layout = self.layout

        box = layout.template_constraint(con)

        if box:
            # match enum type to our functions, avoids a lookup table.
            getattr(self, con.type)(context, box, con)

            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")

    def space_template(self, layout, con, target=True, owner=True):
        if target or owner:

            split = layout.split(percentage=0.2)

            split.label(text=_("Space:"))
            row = split.row()

            if target:
                row.prop(con, "target_space", text="")

            if target and owner:
                row.label(icon='ARROW_LEFTRIGHT')

            if owner:
                row.prop(con, "owner_space", text="")

    def target_template(self, layout, con, subtargets=True):
        layout.prop(con, "target")  # XXX limiting settings for only 'curves' or some type of object

        if con.target and subtargets:
            if con.target.type == 'ARMATURE':
                layout.prop_search(con, "subtarget", con.target.data, "bones", text=_("Bone"))

                if hasattr(con, "head_tail"):
                    row = layout.row()
                    row.label(text=_("Head/Tail:"))
                    row.prop(con, "head_tail", text="")
            elif con.target.type in {'MESH', 'LATTICE'}:
                layout.prop_search(con, "subtarget", con.target, "vertex_groups", text=_("Vertex Group"))

    def ik_template(self, layout, con):
        # only used for iTaSC
        layout.prop(con, "pole_target")

        if con.pole_target and con.pole_target.type == 'ARMATURE':
            layout.prop_search(con, "pole_subtarget", con.pole_target.data, "bones", text=_("Bone"))

        if con.pole_target:
            row = layout.row()
            row.label()
            row.prop(con, "pole_angle")

        split = layout.split(percentage=0.33)
        col = split.column()
        col.prop(con, "use_tail")
        col.prop(con, "use_stretch")

        col = split.column()
        col.prop(con, "chain_count")
        col.prop(con, "use_target")

    def CHILD_OF(self, context, layout, con):
        self.target_template(layout, con)

        split = layout.split()

        col = split.column()
        col.label(text=_("Location:"))
        col.prop(con, "use_location_x", text="X")
        col.prop(con, "use_location_y", text="Y")
        col.prop(con, "use_location_z", text="Z")

        col = split.column()
        col.label(text=_("Rotation:"))
        col.prop(con, "use_rotation_x", text="X")
        col.prop(con, "use_rotation_y", text="Y")
        col.prop(con, "use_rotation_z", text="Z")

        col = split.column()
        col.label(text=_("Scale:"))
        col.prop(con, "use_scale_x", text="X")
        col.prop(con, "use_scale_y", text="Y")
        col.prop(con, "use_scale_z", text="Z")

        row = layout.row()
        row.operator("constraint.childof_set_inverse")
        row.operator("constraint.childof_clear_inverse")

    def TRACK_TO(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row()
        row.label(text=_("To:"))
        row.prop(con, "track_axis", expand=True)

        row = layout.row()
        row.prop(con, "up_axis", text=_("Up"))
        row.prop(con, "use_target_z")

        self.space_template(layout, con)

    def IK(self, context, layout, con):
        if context.object.pose.ik_solver == "ITASC":
            layout.prop(con, "ik_type")
            getattr(self, 'IK_' + con.ik_type)(context, layout, con)
        else:
            # Legacy IK constraint
            self.target_template(layout, con)
            layout.prop(con, "pole_target")

            if con.pole_target and con.pole_target.type == 'ARMATURE':
                layout.prop_search(con, "pole_subtarget", con.pole_target.data, "bones", text=_("Bone"))

            if con.pole_target:
                row = layout.row()
                row.prop(con, "pole_angle")
                row.label()

            split = layout.split()
            col = split.column()
            col.prop(con, "iterations")
            col.prop(con, "chain_count")

            col.label(text=_("Weight:"))
            col.prop(con, "weight", text=_("Position"), slider=True)
            sub = col.column()
            sub.active = con.use_rotation
            sub.prop(con, "orient_weight", text=_("Rotation"), slider=True)

            col = split.column()
            col.prop(con, "use_tail")
            col.prop(con, "use_stretch")
            col.separator()
            col.prop(con, "use_target")
            col.prop(con, "use_rotation")

    def IK_COPY_POSE(self, context, layout, con):
        self.target_template(layout, con)
        self.ik_template(layout, con)

        row = layout.row()
        row.label(text=_("Axis Ref:"))
        row.prop(con, "reference_axis", expand=True)
        split = layout.split(percentage=0.33)
        split.row().prop(con, "use_location")
        row = split.row()
        row.prop(con, "weight", text=_("Weight"), slider=True)
        row.active = con.use_location
        split = layout.split(percentage=0.33)
        row = split.row()
        row.label(text=_("Lock:"))
        row = split.row()
        row.prop(con, "lock_location_x", text="X")
        row.prop(con, "lock_location_y", text="Y")
        row.prop(con, "lock_location_z", text="Z")
        split.active = con.use_location

        split = layout.split(percentage=0.33)
        split.row().prop(con, "use_rotation")
        row = split.row()
        row.prop(con, "orient_weight", text=_("Weight"), slider=True)
        row.active = con.use_rotation
        split = layout.split(percentage=0.33)
        row = split.row()
        row.label(text=_("Lock:"))
        row = split.row()
        row.prop(con, "lock_rotation_x", text="X")
        row.prop(con, "lock_rotation_y", text="Y")
        row.prop(con, "lock_rotation_z", text="Z")
        split.active = con.use_rotation

    def IK_DISTANCE(self, context, layout, con):
        self.target_template(layout, con)
        self.ik_template(layout, con)

        layout.prop(con, "limit_mode")

        row = layout.row()
        row.prop(con, "weight", text=_("Weight"), slider=True)
        row.prop(con, "distance", text=_("Distance"), slider=True)

    def FOLLOW_PATH(self, context, layout, con):
        self.target_template(layout, con)

        split = layout.split()

        col = split.column()
        col.prop(con, "use_curve_follow")
        col.prop(con, "use_curve_radius")

        col = split.column()
        col.prop(con, "use_fixed_location")
        if con.use_fixed_location:
            col.prop(con, "offset_factor", text=_("Offset"))
        else:
            col.prop(con, "offset")

        row = layout.row()
        row.label(text=_("Forward:"))
        row.prop(con, "forward_axis", expand=True)

        row = layout.row()
        row.prop(con, "up_axis", text=_("Up"))
        row.label()

    def LIMIT_ROTATION(self, context, layout, con):
        split = layout.split()

        col = split.column(align=True)
        col.prop(con, "use_limit_x")
        sub = col.column()
        sub.active = con.use_limit_x
        sub.prop(con, "min_x", text=_("Min"))
        sub.prop(con, "max_x", text=_("Max"))

        col = split.column(align=True)
        col.prop(con, "use_limit_y")
        sub = col.column()
        sub.active = con.use_limit_y
        sub.prop(con, "min_y", text=_("Min"))
        sub.prop(con, "max_y", text=_("Max"))

        col = split.column(align=True)
        col.prop(con, "use_limit_z")
        sub = col.column()
        sub.active = con.use_limit_z
        sub.prop(con, "min_z", text=_("Min"))
        sub.prop(con, "max_z", text=_("Max"))

        layout.prop(con, "use_transform_limit")

        row = layout.row()
        row.label(text=_("Convert:"))
        row.prop(con, "owner_space", text="")

    def LIMIT_LOCATION(self, context, layout, con):
        split = layout.split()

        col = split.column()
        col.prop(con, "use_min_x")
        sub = col.column()
        sub.active = con.use_min_x
        sub.prop(con, "min_x", text="")
        col.prop(con, "use_max_x")
        sub = col.column()
        sub.active = con.use_max_x
        sub.prop(con, "max_x", text="")

        col = split.column()
        col.prop(con, "use_min_y")
        sub = col.column()
        sub.active = con.use_min_y
        sub.prop(con, "min_y", text="")
        col.prop(con, "use_max_y")
        sub = col.column()
        sub.active = con.use_max_y
        sub.prop(con, "max_y", text="")

        col = split.column()
        col.prop(con, "use_min_z")
        sub = col.column()
        sub.active = con.use_min_z
        sub.prop(con, "min_z", text="")
        col.prop(con, "use_max_z")
        sub = col.column()
        sub.active = con.use_max_z
        sub.prop(con, "max_z", text="")

        row = layout.row()
        row.prop(con, "use_transform_limit")
        row.label()

        row = layout.row()
        row.label(text=_("Convert:"))
        row.prop(con, "owner_space", text="")

    def LIMIT_SCALE(self, context, layout, con):
        split = layout.split()

        col = split.column()
        col.prop(con, "use_min_x")
        sub = col.column()
        sub.active = con.use_min_x
        sub.prop(con, "min_x", text="")
        col.prop(con, "use_max_x")
        sub = col.column()
        sub.active = con.use_max_x
        sub.prop(con, "max_x", text="")

        col = split.column()
        col.prop(con, "use_min_y")
        sub = col.column()
        sub.active = con.use_min_y
        sub.prop(con, "min_y", text="")
        col.prop(con, "use_max_y")
        sub = col.column()
        sub.active = con.use_max_y
        sub.prop(con, "max_y", text="")

        col = split.column()
        col.prop(con, "use_min_z")
        sub = col.column()
        sub.active = con.use_min_z
        sub.prop(con, "min_z", text="")
        col.prop(con, "use_max_z")
        sub = col.column()
        sub.active = con.use_max_z
        sub.prop(con, "max_z", text="")

        row = layout.row()
        row.prop(con, "use_transform_limit")
        row.label()

        row = layout.row()
        row.label(text=_("Convert:"))
        row.prop(con, "owner_space", text="")

    def COPY_ROTATION(self, context, layout, con):
        self.target_template(layout, con)

        split = layout.split()

        col = split.column()
        col.prop(con, "use_x", text="X")
        sub = col.column()
        sub.active = con.use_x
        sub.prop(con, "invert_x", text=_("Invert"))

        col = split.column()
        col.prop(con, "use_y", text="Y")
        sub = col.column()
        sub.active = con.use_y
        sub.prop(con, "invert_y", text=_("Invert"))

        col = split.column()
        col.prop(con, "use_z", text="Z")
        sub = col.column()
        sub.active = con.use_z
        sub.prop(con, "invert_z", text=_("Invert"))

        layout.prop(con, "use_offset")

        self.space_template(layout, con)

    def COPY_LOCATION(self, context, layout, con):
        self.target_template(layout, con)

        split = layout.split()

        col = split.column()
        col.prop(con, "use_x", text="X")
        sub = col.column()
        sub.active = con.use_x
        sub.prop(con, "invert_x", text=_("Invert"))

        col = split.column()
        col.prop(con, "use_y", text="Y")
        sub = col.column()
        sub.active = con.use_y
        sub.prop(con, "invert_y", text=_("Invert"))

        col = split.column()
        col.prop(con, "use_z", text="Z")
        sub = col.column()
        sub.active = con.use_z
        sub.prop(con, "invert_z", text=_("Invert"))

        layout.prop(con, "use_offset")

        self.space_template(layout, con)

    def COPY_SCALE(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row(align=True)
        row.prop(con, "use_x", text="X")
        row.prop(con, "use_y", text="Y")
        row.prop(con, "use_z", text="Z")

        layout.prop(con, "use_offset")

        self.space_template(layout, con)

    def MAINTAIN_VOLUME(self, context, layout, con):

        row = layout.row()
        row.label(text=_("Free:"))
        row.prop(con, "free_axis", expand=True)

        layout.prop(con, "volume")

        self.space_template(layout, con)

    def COPY_TRANSFORMS(self, context, layout, con):
        self.target_template(layout, con)

        self.space_template(layout, con)

    #def SCRIPT(self, context, layout, con):

    def ACTION(self, context, layout, con):
        self.target_template(layout, con)

        layout.prop(con, "action")

        layout.prop(con, "transform_channel")

        split = layout.split()

        col = split.column(align=True)
        col.label(text=_("Action Length:"))
        col.prop(con, "frame_start", text=_("Start"))
        col.prop(con, "frame_end", text=_("End"))

        col = split.column(align=True)
        col.label(text=_("Target Range:"))
        col.prop(con, "min", text=_("Min"))
        col.prop(con, "max", text=_("Max"))

        row = layout.row()
        row.label(text=_("Convert:"))
        row.prop(con, "target_space", text="")

    def LOCKED_TRACK(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row()
        row.label(text=_("To:"))
        row.prop(con, "track_axis", expand=True)

        row = layout.row()
        row.label(text=_("Lock:"))
        row.prop(con, "lock_axis", expand=True)

    def LIMIT_DISTANCE(self, context, layout, con):
        self.target_template(layout, con)

        col = layout.column(align=True)
        col.prop(con, "distance")
        col.operator("constraint.limitdistance_reset")

        row = layout.row()
        row.label(text=_("Clamp Region:"))
        row.prop(con, "limit_mode", text="")

        row = layout.row()
        row.prop(con, "use_transform_limit")
        row.label()

    def STRETCH_TO(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row()
        row.prop(con, "rest_length", text=_("Rest Length"))
        row.operator("constraint.stretchto_reset", text=_("Reset"))

        layout.prop(con, "bulge", text=_("Volume Variation"))

        row = layout.row()
        row.label(text=_("Volume:"))
        row.prop(con, "volume", expand=True)

        row.label(text=_("Plane:"))
        row.prop(con, "keep_axis", expand=True)

    def FLOOR(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row()
        row.prop(con, "use_sticky")
        row.prop(con, "use_rotation")

        layout.prop(con, "offset")

        row = layout.row()
        row.label(text=_("Min/Max:"))
        row.prop(con, "floor_location", expand=True)

        self.space_template(layout, con)

    def RIGID_BODY_JOINT(self, context, layout, con):
        self.target_template(layout, con, subtargets=False)

        layout.prop(con, "pivot_type")
        layout.prop(con, "child")

        row = layout.row()
        row.prop(con, "use_linked_collision", text=_("Linked Collision"))
        row.prop(con, "show_pivot", text=_("Display Pivot"))

        split = layout.split()

        col = split.column(align=True)
        col.label(text=_("Pivot:"))
        col.prop(con, "pivot_x", text="X")
        col.prop(con, "pivot_y", text="Y")
        col.prop(con, "pivot_z", text="Z")

        col = split.column(align=True)
        col.label(text=_("Axis:"))
        col.prop(con, "axis_x", text="X")
        col.prop(con, "axis_y", text="Y")
        col.prop(con, "axis_z", text="Z")

        if con.pivot_type == 'CONE_TWIST':
            layout.label(text=_("Limits:"))
            split = layout.split()

            col = split.column()
            col.prop(con, "use_angular_limit_x", text=_("Angle X"))
            sub = col.column()
            sub.active = con.use_angular_limit_x
            sub.prop(con, "limit_angle_max_x", text="")

            col = split.column()
            col.prop(con, "use_angular_limit_y", text=_("Angle Y"))
            sub = col.column()
            sub.active = con.use_angular_limit_y
            sub.prop(con, "limit_angle_max_y", text="")

            col = split.column()
            col.prop(con, "use_angular_limit_z", text=_("Angle Z"))
            sub = col.column()
            sub.active = con.use_angular_limit_z
            sub.prop(con, "limit_angle_max_z", text="")

        elif con.pivot_type == 'GENERIC_6_DOF':
            layout.label(text=_("Limits:"))
            split = layout.split()

            col = split.column(align=True)
            col.prop(con, "use_limit_x", text="X")
            sub = col.column()
            sub.active = con.use_limit_x
            sub.prop(con, "limit_min_x", text=_("Min"))
            sub.prop(con, "limit_max_x", text=_("Max"))

            col = split.column(align=True)
            col.prop(con, "use_limit_y", text="Y")
            sub = col.column()
            sub.active = con.use_limit_y
            sub.prop(con, "limit_min_y", text=_("Min"))
            sub.prop(con, "limit_max_y", text=_("Max"))

            col = split.column(align=True)
            col.prop(con, "use_limit_z", text="Z")
            sub = col.column()
            sub.active = con.use_limit_z
            sub.prop(con, "limit_min_z", text=_("Min"))
            sub.prop(con, "limit_max_z", text=_("Max"))

            split = layout.split()

            col = split.column(align=True)
            col.prop(con, "use_angular_limit_x", text=_("Angle X"))
            sub = col.column()
            sub.active = con.use_angular_limit_x
            sub.prop(con, "limit_angle_min_x", text=_("Min"))
            sub.prop(con, "limit_angle_max_x", text=_("Max"))

            col = split.column(align=True)
            col.prop(con, "use_angular_limit_y", text=_("Angle Y"))
            sub = col.column()
            sub.active = con.use_angular_limit_y
            sub.prop(con, "limit_angle_min_y", text=_("Min"))
            sub.prop(con, "limit_angle_max_y", text=_("Max"))

            col = split.column(align=True)
            col.prop(con, "use_angular_limit_z", text=_("Angle Z"))
            sub = col.column()
            sub.active = con.use_angular_limit_z
            sub.prop(con, "limit_angle_min_z", text=_("Min"))
            sub.prop(con, "limit_angle_max_z", text=_("Max"))

        elif con.pivot_type == 'HINGE':
            layout.label(text=_("Limits:"))
            split = layout.split()

            row = split.row(align=True)
            col = row.column()
            col.prop(con, "use_angular_limit_x", text=_("Angle X"))

            col = row.column()
            col.active = con.use_angular_limit_x
            col.prop(con, "limit_angle_min_x", text=_("Min"))
            col = row.column()
            col.active = con.use_angular_limit_x
            col.prop(con, "limit_angle_max_x", text=_("Max"))

    def CLAMP_TO(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row()
        row.label(text=_("Main Axis:"))
        row.prop(con, "main_axis", expand=True)

        layout.prop(con, "use_cyclic")

    def TRANSFORM(self, context, layout, con):
        self.target_template(layout, con)

        layout.prop(con, "use_motion_extrapolate", text=_("Extrapolate"))

        col = layout.column()
        col.row().label(text=_("Source:"))
        col.row().prop(con, "map_from", expand=True)

        split = layout.split()

        sub = split.column(align=True)
        sub.label(text="X:")
        sub.prop(con, "from_min_x", text=_("Min"))
        sub.prop(con, "from_max_x", text=_("Max"))

        sub = split.column(align=True)
        sub.label(text="Y:")
        sub.prop(con, "from_min_y", text=_("Min"))
        sub.prop(con, "from_max_y", text=_("Max"))

        sub = split.column(align=True)
        sub.label(text="Z:")
        sub.prop(con, "from_min_z", text=_("Min"))
        sub.prop(con, "from_max_z", text=_("Max"))

        col = layout.column()
        row = col.row()
        row.label(text=_("Source to Destination Mapping:"))

        # note: chr(187) is the ASCII arrow ( >> ). Blender Text Editor can't
        # open it. Thus we are using the hardcoded value instead.
        row = col.row()
        row.prop(con, "map_to_x_from", expand=False, text="")
        row.label(text=" %s    X" % chr(187))

        row = col.row()
        row.prop(con, "map_to_y_from", expand=False, text="")
        row.label(text=" %s    Y" % chr(187))

        row = col.row()
        row.prop(con, "map_to_z_from", expand=False, text="")
        row.label(text=" %s    Z" % chr(187))

        split = layout.split()

        col = split.column()
        col.label(text=_("Destination:"))
        col.row().prop(con, "map_to", expand=True)

        split = layout.split()

        col = split.column()
        col.label(text="X:")

        sub = col.column(align=True)
        sub.prop(con, "to_min_x", text=_("Min"))
        sub.prop(con, "to_max_x", text=_("Max"))

        col = split.column()
        col.label(text="Y:")

        sub = col.column(align=True)
        sub.prop(con, "to_min_y", text=_("Min"))
        sub.prop(con, "to_max_y", text=_("Max"))

        col = split.column()
        col.label(text="Z:")

        sub = col.column(align=True)
        sub.prop(con, "to_min_z", text=_("Min"))
        sub.prop(con, "to_max_z", text=_("Max"))

        self.space_template(layout, con)

    def SHRINKWRAP(self, context, layout, con):
        self.target_template(layout, con, False)

        layout.prop(con, "distance")
        layout.prop(con, "shrinkwrap_type")

        if con.shrinkwrap_type == 'PROJECT':
            row = layout.row(align=True)
            row.prop(con, "use_x")
            row.prop(con, "use_y")
            row.prop(con, "use_z")

    def DAMPED_TRACK(self, context, layout, con):
        self.target_template(layout, con)

        row = layout.row()
        row.label(text=_("To:"))
        row.prop(con, "track_axis", expand=True)

    def SPLINE_IK(self, context, layout, con):
        self.target_template(layout, con)

        col = layout.column()
        col.label(text=_("Spline Fitting:"))
        col.prop(con, "chain_count")
        col.prop(con, "use_even_divisions")
        col.prop(con, "use_chain_offset")

        col = layout.column()
        col.label(text=_("Chain Scaling:"))
        col.prop(con, "use_y_stretch")
        col.prop(con, "xz_scale_mode")
        col.prop(con, "use_curve_radius")

    def PIVOT(self, context, layout, con):
        self.target_template(layout, con)

        if con.target:
            col = layout.column()
            col.prop(con, "offset", text=_("Pivot Offset"))
        else:
            col = layout.column()
            col.prop(con, "use_relative_location")
            if con.use_relative_location:
                col.prop(con, "offset", text=_("Relative Pivot Point"))
            else:
                col.prop(con, "offset", text=_("Absolute Pivot Point"))

        col = layout.column()
        col.prop(con, "rotation_range", text=_("Pivot When"))

    def SCRIPT(self, context, layout, con):
        layout.label(_("Blender 2.5 has no py-constraints"))


class OBJECT_PT_constraints(ConstraintButtonsPanel, Panel):
    bl_label = "Object Constraints"
    bl_context = "constraint"

    @classmethod
    def poll(cls, context):
        return (context.object)

    def draw(self, context):
        layout = self.layout

        ob = context.object

        if ob.mode == 'POSE':
            box = layout.box()
            box.alert = True
            box.label(icon='INFO', text=_("See Bone Constraints tab to Add Constraints to active bone"))
        else:
            layout.operator_menu_enum("object.constraint_add", "type")

        for con in ob.constraints:
            self.draw_constraint(context, con)


class BONE_PT_constraints(ConstraintButtonsPanel, Panel):
    bl_label = "Bone Constraints"
    bl_context = "bone_constraint"

    @classmethod
    def poll(cls, context):
        return (context.pose_bone)

    def draw(self, context):
        layout = self.layout

        layout.operator_menu_enum("pose.constraint_add", "type")

        for con in context.pose_bone.constraints:
            self.draw_constraint(context, con)

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
