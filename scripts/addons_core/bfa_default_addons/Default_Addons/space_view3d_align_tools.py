# SPDX-FileCopyrightText: 2009-2010 gabhead, Lell, Anfeo.
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Align Tools",
    "author": "gabhead, Lell, Anfeo",
    "version": (0, 3, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Item Tab",
    "description": "Align Selected Objects to Active Object",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/object/align_tools.html",
    "category": "Object",
}

import bpy
from bpy.types import (
        Operator,
        Panel,
        AddonPreferences,
        )
from bpy.props import (
        EnumProperty,
        BoolProperty,
        FloatVectorProperty,
        StringProperty,
        )
from mathutils import (
        Vector,
        Matrix,
        )


# Simple Align Defs #

# Align all
def main(context):
    for i in bpy.context.selected_objects:
        i.matrix_world.translation = bpy.context.active_object.matrix_world.translation.copy()
        i.rotation_euler = bpy.context.active_object.rotation_euler


# Align Location
def LocAll(context):
    for i in bpy.context.selected_objects:
        i.matrix_world.translation = bpy.context.active_object.matrix_world.translation.copy()


def LocX(context):
    for i in bpy.context.selected_objects:
        i.matrix_world.translation.x = bpy.context.active_object.matrix_world.translation.x


def LocY(context):
    for i in bpy.context.selected_objects:
        i.matrix_world.translation.y = bpy.context.active_object.matrix_world.translation.y


def LocZ(context):
    for i in bpy.context.selected_objects:
        i.matrix_world.translation.z = bpy.context.active_object.matrix_world.translation.z


# Align Rotation
def RotAll(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler = bpy.context.active_object.rotation_euler


def RotX(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler.x = bpy.context.active_object.rotation_euler.x


def RotY(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler.y = bpy.context.active_object.rotation_euler.y


def RotZ(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler.z = bpy.context.active_object.rotation_euler.z


# Align Scale
def ScaleAll(context):
    for i in bpy.context.selected_objects:
        i.scale = bpy.context.active_object.scale


def ScaleX(context):
    for i in bpy.context.selected_objects:
        i.scale.x = bpy.context.active_object.scale.x


def ScaleY(context):
    for i in bpy.context.selected_objects:
        i.scale.y = bpy.context.active_object.scale.y


def ScaleZ(context):
    for i in bpy.context.selected_objects:
        i.scale.z = bpy.context.active_object.scale.z


# Advanced Align Defs #

# subject to object 0, 1 and 2 to pivot for cursor
def align_function(subject, active_too, consistent, self_or_active, loc_x, loc_y, loc_z, ref1, ref2, loc_offset,
                   rot_x, rot_y, rot_z, rot_offset, scale_x, scale_y, scale_z, scale_offset,
                   fit_x, fit_y, fit_z):

    sel_obj = bpy.context.selected_objects
    act_obj = bpy.context.active_object

    global sel_max
    global sel_min
    global sel_center
    global ref2_co

    def get_reference_points(obj, space):

        me = obj.data
        co_list = []
        # let's get all the points coordinates
        if space == "global":
            ok = False
            obj_mtx = obj.matrix_world
            if obj.type == 'MESH' and len(me.vertices) > 0:
                ok = True
                for p in me.vertices:
                    co_list.append((obj_mtx @ p.co))

            elif obj.type == 'SURFACE' and len(me.splines) > 0:
                ok = True
                for s in me.splines:
                    for p in s.points:
                        co_list.append((obj_mtx @ p.co))
            elif obj.type == 'FONT' and len(me.splines) > 0:
                ok = True
                for s in me.splines:
                    for p in s.bezier_points:
                        co_list.append((obj_mtx @ p.co))

        elif space == "local":
            ok = False
            if obj.type == 'MESH' and len(me.vertices) > 0:
                ok = True
                for p in me.vertices:
                    co_list.append(p.co)

            elif obj.type == 'SURFACE' and len(me.splines) > 0:
                ok = True
                for s in me.splines:
                    for p in s.points:
                        co_list.append(p.co)
            elif obj.type == 'FONT' and len(obj.data.splines) > 0:
                ok = True
                for s in me.splines:
                    for p in s.bezier_points:
                        co_list.append(p.co)

        # if a valid point found
        # proceed to calculate the extremes
        if ok:
            max_x = co_list[0][0]
            min_x = co_list[0][0]
            max_y = co_list[0][1]
            min_y = co_list[0][1]
            max_z = co_list[0][2]
            min_z = co_list[0][2]

            for v in co_list:
                # the strings of the list compared with the smaller and more found
                # in order to find the minor and major for each axis
                act_x = v[0]
                if act_x > max_x:
                    max_x = act_x
                if act_x < min_x:
                    min_x = act_x

                act_y = v[1]
                if act_y > max_y:
                    max_y = act_y
                if act_y < min_y:
                    min_y = act_y

                act_z = v[2]
                if act_z > max_z:
                    max_z = act_z
                if act_z < min_z:
                    min_z = act_z

        else:
            # otherwise use the pivot object
            a = obj.matrix_world.translation
            min_x = a[0]
            max_x = a[0]
            min_y = a[1]
            max_y = a[1]
            min_z = a[2]
            max_z = a[2]

        center_x = min_x + ((max_x - min_x) / 2)
        center_y = min_y + ((max_y - min_y) / 2)
        center_z = min_z + ((max_z - min_z) / 2)

        reference_points = [min_x, center_x, max_x, min_y, center_y, max_y, min_z, center_z, max_z]
        return reference_points

    def get_sel_ref(ref_co, sel_obj):  # I look for the selection end points

        sel_min = ref_co.copy()
        sel_max = ref_co.copy()

        for obj in sel_obj:
            if obj != act_obj or (active_too and obj == act_obj):

                ref_points = get_reference_points(obj, "global")
                ref_min = Vector([ref_points[0], ref_points[3], ref_points[6]])
                ref_max = Vector([ref_points[2], ref_points[5], ref_points[8]])

                if ref_min[0] < sel_min[0]:
                    sel_min[0] = ref_min[0]
                if ref_max[0] > sel_max[0]:
                    sel_max[0] = ref_max[0]
                if ref_min[1] < sel_min[1]:
                    sel_min[1] = ref_min[1]
                if ref_max[1] > sel_max[1]:
                    sel_max[1] = ref_max[1]
                if ref_min[2] < sel_min[2]:
                    sel_min[2] = ref_min[2]
                if ref_max[2] > sel_max[2]:
                    sel_max[2] = ref_max[2]

        return sel_min, sel_max

    def find_ref2_co(act_obj):
        # It contains the coordinates of the reference point for the positioning
        if ref2 == "0":
            ref_points = get_reference_points(act_obj, "global")
            ref2_co = [ref_points[0], ref_points[3], ref_points[6]]
            ref2_co = Vector(ref2_co)
        elif ref2 == "1":
            ref_points = get_reference_points(act_obj, "global")
            ref2_co = [ref_points[1], ref_points[4], ref_points[7]]
            ref2_co = Vector(ref2_co)
        elif ref2 == "2":
            ref2_co = act_obj.location
            ref2_co = Vector(ref2_co)
        elif ref2 == "3":
            ref_points = get_reference_points(act_obj, "global")
            ref2_co = [ref_points[2], ref_points[5], ref_points[8]]
            ref2_co = Vector(ref2_co)
        elif ref2 == "4":
            ref2_co = bpy.context.scene.cursor.location

        return ref2_co

    def find_new_coord(obj):

        ref_points = get_reference_points(obj, "global")

        if loc_x is True:
            if ref1 == "0":
                min_x = ref_points[0]
                new_x = ref2_co[0] + (obj.location[0] - min_x) + loc_offset[0]
            elif ref1 == "1":
                center_x = ref_points[1]
                new_x = ref2_co[0] + (obj.location[0] - center_x) + loc_offset[0]
            elif ref1 == "2":
                new_x = ref2_co[0] + loc_offset[0]
            elif ref1 == "3":
                max_x = ref_points[2]
                new_x = ref2_co[0] - (max_x - obj.location[0]) + loc_offset[0]
            obj.matrix_world.translation[0] = new_x
        if loc_y is True:
            if ref1 == "0":
                min_y = ref_points[3]
                new_y = ref2_co[1] + (obj.location[1] - min_y) + loc_offset[1]
            elif ref1 == "1":
                center_y = ref_points[4]
                new_y = ref2_co[1] + (obj.location[1] - center_y) + loc_offset[1]
            elif ref1 == "2":
                new_y = ref2_co[1] + loc_offset[1]
            elif ref1 == "3":
                max_y = ref_points[5]
                new_y = ref2_co[1] - (max_y - obj.location[1]) + loc_offset[1]
            obj.matrix_world.translation[1] = new_y
        if loc_z is True:
            if ref1 == "0":
                min_z = ref_points[6]
                new_z = ref2_co[2] + (obj.location[2] - min_z) + loc_offset[2]
            elif ref1 == "1":
                center_z = ref_points[7]
                new_z = ref2_co[2] + (obj.location[2] - center_z) + loc_offset[2]
            elif ref1 == "2":
                new_z = ref2_co[2] + loc_offset[2]
            elif ref1 == "3":
                max_z = ref_points[8]
                new_z = ref2_co[2] - (max_z - obj.location[2]) + loc_offset[2]
            obj.matrix_world.translation[2] = new_z

    def find_new_rotation(obj):
        if rot_x is True:
            obj.rotation_euler[0] = act_obj.rotation_euler[0] + rot_offset[0]
        if rot_y is True:
            obj.rotation_euler[1] = act_obj.rotation_euler[1] + rot_offset[1]
        if rot_z is True:
            obj.rotation_euler[2] = act_obj.rotation_euler[2] + rot_offset[2]

    def find_new_scale(obj):
        if scale_x is True:
            obj.scale[0] = act_obj.scale[0] + scale_offset[0]
        if scale_y is True:
            obj.scale[1] = act_obj.scale[1] + scale_offset[1]
        if scale_z is True:
            obj.scale[2] = act_obj.scale[2] + scale_offset[2]

    def find_new_dimensions(obj, ref_dim):
        ref_points = get_reference_points(obj, "local")
        if fit_x:
            dim = ref_points[2] - ref_points[0]
            obj.scale[0] = (ref_dim[0] / dim) * act_obj.scale[0]
        if fit_y:
            dim = ref_points[5] - ref_points[3]
            obj.scale[1] = (ref_dim[1] / dim) * act_obj.scale[1]
        if fit_z:
            dim = ref_points[8] - ref_points[6]
            obj.scale[2] = (ref_dim[2] / dim) * act_obj.scale[2]

    def move_pivot(obj):
        me = obj.data
        vec_ref2_co = Vector(ref2_co)
        offset = vec_ref2_co - obj.location
        offset_x = [offset[0] + loc_offset[0], 0, 0]
        offset_y = [0, offset[1] + loc_offset[1], 0]
        offset_z = [0, 0, offset[2] + loc_offset[2]]

        def movement(vec):
            obj_mtx = obj.matrix_world.copy()
            # What's the displacement vector for the pivot?
            move_pivot = Vector(vec)

            # Move the pivot point (which is the object's location)
            pivot = obj.location
            pivot += move_pivot

            nm = obj_mtx.inverted() @ Matrix.Translation(-move_pivot) @ obj_mtx

            # Transform the mesh now
            me.transform(nm)

        if loc_x:
            movement(offset_x)
        if loc_y:
            movement(offset_y)
        if loc_z:
            movement(offset_z)

    def point_in_selection(act_obj, sel_obj):
        ok = False
        for o in sel_obj:
            if o != act_obj:
                ref_ob = o
                obj_mtx = o.matrix_world
                if o.type == 'MESH' and len(o.data.vertices) > 0:
                    ref_co = o.data.vertices[0].co.copy()
                    ref_co = obj_mtx @ ref_co
                    ok = True
                    break
                elif o.type == 'CURVE' and len(o.data.splines) > 0:
                    ref_co = o.data.splines[0].bezier_point[0].co.copy()
                    ref_co = obj_mtx @ ref_co
                    ok = True
                    break
                elif o.type == 'SURFACE' and len(o.data.splines) > 0:
                    ref_co = o.data.splines[0].points[0].co.copy()
                    ref_co = obj_mtx @ ref_co
                    ok = True
                    break
                elif o.type == 'FONT' and len(o.data.splines) > 0:
                    ref_co = o.data.splines[0].bezier_points[0].co.copy()
                    ref_co = obj_mtx @ ref_co
                    ok = True
                    break
        # if no object had data, use the position of an object that was not active as an internal
        # point of selection
        if ok is False:
            ref_co = ref_ob.matrix_world.translation

        return ref_co

    if subject == "0":
        # if act_obj.type == ('MESH' or 'FONT' or 'CURVE' or 'SURFACE'):
        if act_obj.type == 'MESH' or act_obj.type == 'FONT' or act_obj.type == 'SURFACE':
            ref2_co = find_ref2_co(act_obj)
        else:
            if ref2 == "4":
                ref2_co = bpy.context.scene.cursor.location
            else:
                ref2_co = act_obj.matrix_world.translation

        # in the case of substantial selection
        if consistent:
            # I am seeking a point that is in the selection space
            ref_co = point_in_selection(act_obj, sel_obj)

            sel_min, sel_max = get_sel_ref(ref_co, sel_obj)

            sel_center = sel_min + ((sel_max - sel_min) / 2)
            translate = [0, 0, 0]

            # calculating how much to move the selection
            if ref1 == "0":
                translate = ref2_co - sel_min + loc_offset
            elif ref1 == "1":
                translate = ref2_co - sel_center + loc_offset
            elif ref1 == "3":
                translate = ref2_co - sel_max + loc_offset

            # Move the various objects
            for obj in sel_obj:

                if obj != act_obj or (active_too and obj == act_obj):

                    if loc_x:
                        obj.location[0] += translate[0]
                    if loc_y:
                        obj.location[1] += translate[1]
                    if loc_z:
                        obj.location[2] += translate[2]
        else:  # not consistent
            for obj in sel_obj:
                if obj != act_obj:
                    if rot_x or rot_y or rot_z:
                        find_new_rotation(obj)

                    if fit_x or fit_y or fit_z:
                        dim = [0, 0, 0]
                        ref_points = get_reference_points(act_obj, "local")
                        dim[0] = ref_points[2] - ref_points[0]
                        dim[1] = ref_points[5] - ref_points[3]
                        dim[2] = ref_points[8] - ref_points[6]
                        find_new_dimensions(obj, dim)

                    if scale_x or scale_y or scale_z:
                        find_new_scale(obj)

                    if loc_x or loc_y or loc_z:
                        # print("ehy", ref2_co)
                        find_new_coord(obj)

            if active_too is True:
                if loc_x or loc_y or loc_z:
                    find_new_coord(act_obj)
                if rot_x or rot_y or rot_z:
                    find_new_rotation(act_obj)
                if scale_x or scale_y or scale_z:
                    find_new_scale(act_obj)
                # add dimensions if dim offset will be added

    elif subject == "1":
        if self_or_active == "1":
            if act_obj.type == 'MESH':
                ref2_co = find_ref2_co(act_obj)
        for obj in sel_obj:
            if self_or_active == "0":
                ref2_co = find_ref2_co(obj)
            if loc_x or loc_y or loc_z:
                if obj != act_obj and obj.type == 'MESH':
                    move_pivot(obj)

        if active_too is True:
            if act_obj.type == 'MESH':
                if loc_x or loc_y or loc_z:
                    if self_or_active == "0":
                        ref2_co = find_ref2_co(act_obj)
                    move_pivot(act_obj)

    elif subject == "2":
        if self_or_active == "1":
            if act_obj.type == 'MESH' or act_obj.type == 'FONT' or act_obj.type == 'SURFACE':
                ref2_co = find_ref2_co(act_obj)
                ref_points = get_reference_points(act_obj, "global")
            else:
                ref2_co = act_obj.matrix_world.translation
                ref_points = [ref2_co[0], ref2_co[0], ref2_co[0],
                              ref2_co[1], ref2_co[1], ref2_co[1],
                              ref2_co[2], ref2_co[2], ref2_co[2]]

            if ref2 == "0":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = ref_points[0] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = ref_points[3] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = ref_points[6] + loc_offset[2]
            elif ref2 == "1":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = ref_points[1] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = ref_points[4] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = ref_points[7] + loc_offset[2]
            elif ref2 == "2":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = act_obj.location[0] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = act_obj.location[1] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = act_obj.location[2] + loc_offset[2]
            elif ref2 == "3":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = ref_points[2] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = ref_points[5] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = ref_points[8] + loc_offset[2]
        elif self_or_active == "2":
            ref_co = point_in_selection(act_obj, sel_obj)

            sel_min, sel_max = get_sel_ref(ref_co, sel_obj)
            sel_center = sel_min + ((sel_max - sel_min) / 2)

            if ref2 == "0":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = sel_min[0] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = sel_min[1] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = sel_min[2] + loc_offset[2]
            elif ref2 == "1":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = sel_center[0] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = sel_center[1] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = sel_center[2] + loc_offset[2]
            elif ref2 == "3":
                if loc_x is True:
                    bpy.context.scene.cursor.location[0] = sel_max[0] + loc_offset[0]
                if loc_y is True:
                    bpy.context.scene.cursor.location[1] = sel_max[1] + loc_offset[1]
                if loc_z is True:
                    bpy.context.scene.cursor.location[2] = sel_max[2] + loc_offset[2]


# Classes #

# Advanced Align
class OBJECT_OT_align_tools(Operator):
    bl_idname = "object.align_tools"
    bl_label = "Align Operator"
    bl_description = "Align Object Tools"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # property definitions

    # Object-Pivot-Cursor:
    subject: EnumProperty(
            items=(("0", "Object", "Align Objects"),
                   ("1", "Pivot", "Align Objects Pivot"),
                   ("2", "Cursor", "Align Cursor To Active")),
            name="Align To",
            description="What will be moved"
            )
    # Move active Too:
    active_too: BoolProperty(
            name="Active too",
            default=False,
            description="Move the active object too"
            )
    # advanced options
    advanced: BoolProperty(
            name="Advanced Options",
            default=False,
            description="Show advanced options"
            )
    consistent: BoolProperty(
            name="Consistent Selection",
            default=False,
            description="Use consistent selection"
            )
    # Align Location:
    loc_x: BoolProperty(
            name="Align to X axis",
            default=False,
            description="Enable X axis alignment"
            )
    loc_y: BoolProperty(
            name="Align to Y axis",
            default=False,
            description="Enable Y axis alignment"
            )
    loc_z: BoolProperty(
            name="Align to Z axis",
            default=False,
            description="Enable Z axis alignment"
            )
    # Selection Option:
    ref1: EnumProperty(
            items=(("3", "Max", "Align the maximum point"),
                   ("1", "Center", "Align the center point"),
                   ("2", "Pivot", "Align the pivot"),
                   ("0", "Min", "Align the minimum point")),
            name="Selection reference",
            description="Moved objects reference point"
            )
    # Active Object Option:
    ref2: EnumProperty(
            items=(("3", "Max", "Align to the maximum point"),
                   ("1", "Center", "Align to the center point"),
                   ("2", "Pivot", "Align to the pivot"),
                   ("0", "Min", "Align to the minimum point"),
                   ("4", "Cursor", "Description")),
            name="Active reference",
            description="Destination point"
            )
    self_or_active: EnumProperty(
            items=(("0", "Self", "In relation of itself"),
                   ("1", "Active", "In relation of the active object"),
                   ("2", "Selection", "In relation of the entire selection")),
            name="Relation",
            default="1",
            description="To what the pivot will be aligned"
            )
    # Location Offset
    loc_offset: FloatVectorProperty(
            name="Location Offset",
            description="Offset for location align position",
            default=(0.0, 0.0, 0.0),
            subtype='XYZ', size=3
            )
    # Rotation Offset
    rot_offset: FloatVectorProperty(
            name="Rotation Offset",
            description="Offset for rotation alignment",
            default=(0.0, 0.0, 0.0),
            subtype='EULER', size=3
            )
    # Scale Offset
    scale_offset: FloatVectorProperty(
            name="Scale Offset",
            description="Offset for scale match",
            default=(0.0, 0.0, 0.0),
            subtype='XYZ', size=3
            )
    # Fit Dimension Prop:
    fit_x: BoolProperty(
            name="Fit Dimension to X axis",
            default=False,
            description=""
            )
    fit_y: BoolProperty(
            name="Fit Dimension to Y axis",
            default=False,
            description=""
            )
    fit_z: BoolProperty(
            name="Fit Dimension to Z axis",
            default=False,
            description=""
            )
    # Apply Fit Dimension:
    apply_dim: BoolProperty(
            name="Apply  Dimension",
            default=False,
            description=""
            )
    # Align Rot Prop:
    rot_x: BoolProperty(
            name="Align Rotation to X axis",
            default=False,
            description=""
            )
    rot_y: BoolProperty(
            name="Align Rotation to Y axis",
            default=False,
            description=""
            )
    rot_z: BoolProperty(
            name="Align Rotation to Z axis",
            default=False,
            description=""
            )
    # Apply Rot:
    apply_rot: BoolProperty(
            name="Apply Rotation",
            default=False,
            description=""
            )
    # Align Scale:
    scale_x: BoolProperty(
            name="Match Scale to X axis",
            default=False,
            description=""
            )
    scale_y: BoolProperty(
            name="Match Scale to Y axis",
            default=False,
            description=""
            )
    scale_z: BoolProperty(
            name="match Scale to Z axis",
            default=False,
            description=""
            )
    # Apply Scale:
    apply_scale: BoolProperty(
            name="Apply Scale",
            default=False,
            description=""
            )

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.label(text="Active object is: ", icon='OBJECT_DATA')
        box = layout.box()
        box.label(text=obj.name, icon='EDITMODE_HLT')
        # Object-Pivot-Cursor:
        row0 = layout.row()
        row0.prop(self, 'subject', expand=True)

        # Move active Too:
        row1 = layout.row()
        row1.prop(self, 'active_too')
        row1.prop(self, 'advanced')
        if self.advanced:
            row1b = layout.row()
            row1b.prop(self, 'consistent')

        row2 = layout.row()
        row2.label(text="Align Location:")

        # Align Location:
        row3 = layout.row()
        row3.prop(self, "loc_x", text="X", toggle=True)
        row3.prop(self, "loc_y", text="Y", toggle=True)
        row3.prop(self, "loc_z", text="Z", toggle=True)

        # Offset:
        if self.advanced is True:
            # row8 = col.row()
            # row8.label(text='Location Offset')
            row9 = layout.row()
            row9.prop(self, 'loc_offset', text='')

        # Selection Options
        if self.advanced is True:
            sel = bpy.context.selected_objects
            sel_obs = len(sel)
            if sel_obs != 0:
                row4 = layout.row()
                row4.label(text="Selected: " + str(sel_obs) + " Objects", icon='OBJECT_DATA')
        if self.subject == "1" or self.subject == "2":
            row5b = layout.row()
            row5b.prop(self, 'self_or_active', expand=True)
        else:
            row5 = layout.row()
            row5.prop(self, 'ref1', expand=True)

        # Active Object Options: Number of select objects
        act = bpy.context.active_object

        if self.advanced is True:
            if act:
                row6 = layout.row()
                row6.label(text="Active: " + act.name, icon='OBJECT_DATA')
        row7 = layout.row()
        row7.prop(self, 'ref2', expand=True)

        if self.subject == "0":
            row12 = layout.row()
            row12.label(text='Align Rotation:')
            row13 = layout.row(align=True)
            row13.prop(self, 'rot_x', text='X', toggle=True)
            row13.prop(self, 'rot_y', text='Y', toggle=True)
            row13.prop(self, 'rot_z', text='Z', toggle=True)
            row13.prop(self, 'apply_rot', text='Apply', toggle=True)
            if self.advanced is True:
                row13b = layout.row()
                row13b.prop(self, 'rot_offset', text='')

            row14 = layout.row()
            row14.label(text='Match Scale:')
            row15 = layout.row(align=True)
            row15.prop(self, 'scale_x', text='X', toggle=True)
            row15.prop(self, 'scale_y', text='Y', toggle=True)
            row15.prop(self, 'scale_z', text='Z', toggle=True)
            row15.prop(self, 'apply_scale', text='Apply', toggle=True)
            if self.advanced is True:
                row15b = layout.row()
                row15b.prop(self, 'scale_offset', text='')

            row10 = layout.row()
            row10.label(text='Fit Dimensions:')
            row11 = layout.row(align=True)
            row11.prop(self, 'fit_x', text='X', toggle=True)
            row11.prop(self, 'fit_y', text='Y', toggle=True)
            row11.prop(self, 'fit_z', text='Z', toggle=True)
            row11.prop(self, 'apply_dim', text='Apply', toggle=True)

    def execute(self, context):
        align_function(
                self.subject, self.active_too, self.consistent,
                self.self_or_active, self.loc_x, self.loc_y, self.loc_z,
                self.ref1, self.ref2, self.loc_offset,
                self.rot_x, self.rot_y, self.rot_z, self.rot_offset,
                self.scale_x, self.scale_y, self.scale_z, self.scale_offset,
                self.fit_x, self.fit_y, self.fit_z
                )

        return {'FINISHED'}


# Simple Align Classes #

# Align All Rotation And Location
class OBJECT_OT_AlignOperator(Operator):
    bl_idname = "object.align"
    bl_label = "Align Selected To Active"
    bl_description = "Align Selected To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


# Align Location All
class OBJECT_OT_AlignLocationOperator(Operator):
    bl_idname = "object.align_location_all"
    bl_label = "Align Selected Location To Active"
    bl_description = "Align Selected Location To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        LocAll(context)
        return {'FINISHED'}


# Align Location X
class OBJECT_OT_AlignLocationXOperator(Operator):
    bl_idname = "object.align_location_x"
    bl_label = "Align Selected Location X To Active"
    bl_description = "Align Selected Location X To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        LocX(context)
        return {'FINISHED'}


# Align Location Y
class OBJECT_OT_AlignLocationYOperator(Operator):
    bl_idname = "object.align_location_y"
    bl_label = "Align Selected Location Y To Active"
    bl_description = "Align Selected Location Y To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        LocY(context)
        return {'FINISHED'}


# Align LocationZ
class OBJECT_OT_AlignLocationZOperator(Operator):
    bl_idname = "object.align_location_z"
    bl_label = "Align Selected Location Z To Active"
    bl_description = "Align Selected Location Z To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        LocZ(context)
        return {'FINISHED'}


# Align Rotation All
class OBJECT_OT_AlignRotationOperator(Operator):
    bl_idname = "object.align_rotation_all"
    bl_label = "Align Selected Rotation To Active"
    bl_description = "Align Selected Rotation To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        RotAll(context)
        return {'FINISHED'}


# Align Rotation X
class OBJECT_OT_AlignRotationXOperator(Operator):
    bl_idname = "object.align_rotation_x"
    bl_label = "Align Selected Rotation X To Active"
    bl_description = "Align Selected Rotation X To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        RotX(context)
        return {'FINISHED'}


# Align Rotation Y
class OBJECT_OT_AlignRotationYOperator(Operator):
    bl_idname = "object.align_rotation_y"
    bl_label = "Align Selected Rotation Y To Active"
    bl_description = "Align Selected Rotation Y To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        RotY(context)
        return {'FINISHED'}


# Align Rotation Z
class OBJECT_OT_AlignRotationZOperator(Operator):
    bl_idname = "object.align_rotation_z"
    bl_label = "Align Selected Rotation Z To Active"
    bl_description = "Align Selected Rotation Z To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        RotZ(context)
        return {'FINISHED'}


# Scale All
class OBJECT_OT_AlignScaleOperator(Operator):
    bl_idname = "object.align_objects_scale_all"
    bl_label = "Align Selected Scale To Active"
    bl_description = "Align Selected Scale To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        ScaleAll(context)
        return {'FINISHED'}


# Align Scale X
class OBJECT_OT_AlignScaleXOperator(Operator):
    bl_idname = "object.align_objects_scale_x"
    bl_label = "Align Selected Scale X To Active"
    bl_description = "Align Selected Scale X To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        ScaleX(context)
        return {'FINISHED'}


# Align Scale Y
class OBJECT_OT_AlignScaleYOperator(Operator):
    bl_idname = "object.align_objects_scale_y"
    bl_label = "Align Selected Scale Y To Active"
    bl_description = "Align Selected Scale Y To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        ScaleY(context)
        return {'FINISHED'}


# Align Scale Z
class OBJECT_OT_AlignScaleZOperator(Operator):
    bl_idname = "object.align_objects_scale_z"
    bl_label = "Align Selected Scale Z To Active"
    bl_description = "Align Selected Scale Z To Active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        ScaleZ(context)
        return {'FINISHED'}


# Interface Panel

class VIEW3D_PT_AlignUi(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Align Tools"
    bl_context = "objectmode"
    bl_category = 'Item'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is not None:
            row = layout.row()
            row.label(text="Active object is: ", icon='OBJECT_DATA')
            box = layout.box()
            box.label(text=obj.name, icon='EDITMODE_HLT')

        col = layout.column()
        col.label(text="Align Loc + Rot:")

        col = layout.column(align=False)
        col.operator("object.align", text="XYZ")

        col = layout.column()
        col.label(text="Align Location:")

        col = layout.column_flow(columns=4, align=True)
        col.operator("object.align_location_x", text="X")
        col.operator("object.align_location_y", text="Y")
        col.operator("object.align_location_z", text="Z")
        col.operator("object.align_location_all", text="All")

        col = layout.column()
        col.label(text="Align Rotation:")

        col = layout.column_flow(columns=4, align=True)
        col.operator("object.align_rotation_x", text="X")
        col.operator("object.align_rotation_y", text="Y")
        col.operator("object.align_rotation_z", text="Z")
        col.operator("object.align_rotation_all", text="All")

        col = layout.column()
        col.label(text="Align Scale:")

        col = layout.column_flow(columns=4, align=True)
        col.operator("object.align_objects_scale_x", text="X")
        col.operator("object.align_objects_scale_y", text="Y")
        col.operator("object.align_objects_scale_z", text="Z")
        col.operator("object.align_objects_scale_all", text="All")

        if obj is not None:
            col = layout.column()
            col.label(text="Advanced Align Operations")
            layout = self.layout
            self.layout.operator("object.align_tools", text="Advanced")


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        VIEW3D_PT_AlignUi,
        )


def update_panel(self, context):
    message = "Align Tools: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class AlignAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="Item",
            update=update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")


# Class List
classes = (
    VIEW3D_PT_AlignUi,
    OBJECT_OT_AlignOperator,
    OBJECT_OT_AlignLocationOperator,
    OBJECT_OT_AlignLocationXOperator,
    OBJECT_OT_AlignLocationYOperator,
    OBJECT_OT_AlignLocationZOperator,
    OBJECT_OT_AlignRotationOperator,
    OBJECT_OT_AlignRotationXOperator,
    OBJECT_OT_AlignRotationYOperator,
    OBJECT_OT_AlignRotationZOperator,
    OBJECT_OT_AlignScaleOperator,
    OBJECT_OT_AlignScaleXOperator,
    OBJECT_OT_AlignScaleYOperator,
    OBJECT_OT_AlignScaleZOperator,
    OBJECT_OT_align_tools,
    AlignAddonPreferences,
    )


# Register all operators and panels
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
