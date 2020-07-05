#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy

from collections import OrderedDict

from .utils.animation import SCRIPT_REGISTER_BAKE, SCRIPT_UTILITIES_BAKE
from .utils.rig import attach_persistent_script

from . import base_generate

from rna_prop_ui import rna_idprop_quote_path


UI_IMPORTS = [
    'import bpy',
    'import math',
    'import json',
    'import collections',
    'import traceback',
    'from math import pi',
    'from bpy.props import StringProperty',
    'from mathutils import Euler, Matrix, Quaternion, Vector',
    'from rna_prop_ui import rna_idprop_quote_path',
]

UI_BASE_UTILITIES = '''
rig_id = "%s"


############################
## Math utility functions ##
############################

def perpendicular_vector(v):
    """ Returns a vector that is perpendicular to the one given.
        The returned vector is _not_ guaranteed to be normalized.
    """
    # Create a vector that is not aligned with v.
    # It doesn't matter what vector.  Just any vector
    # that's guaranteed to not be pointing in the same
    # direction.
    if abs(v[0]) < abs(v[1]):
        tv = Vector((1,0,0))
    else:
        tv = Vector((0,1,0))

    # Use cross prouct to generate a vector perpendicular to
    # both tv and (more importantly) v.
    return v.cross(tv)


def rotation_difference(mat1, mat2):
    """ Returns the shortest-path rotational difference between two
        matrices.
    """
    q1 = mat1.to_quaternion()
    q2 = mat2.to_quaternion()
    angle = math.acos(min(1,max(-1,q1.dot(q2)))) * 2
    if angle > pi:
        angle = -angle + (2*pi)
    return angle

def find_min_range(f,start_angle,delta=pi/8):
    """ finds the range where lies the minimum of function f applied on bone_ik and bone_fk
        at a certain angle.
    """
    angle = start_angle
    while (angle > (start_angle - 2*pi)) and (angle < (start_angle + 2*pi)):
        l_dist = f(angle-delta)
        c_dist = f(angle)
        r_dist = f(angle+delta)
        if min((l_dist,c_dist,r_dist)) == c_dist:
            return (angle-delta,angle+delta)
        else:
            angle=angle+delta

def ternarySearch(f, left, right, absolutePrecision):
    """
    Find minimum of unimodal function f() within [left, right]
    To find the maximum, revert the if/else statement or revert the comparison.
    """
    while True:
        #left and right are the current bounds; the maximum is between them
        if abs(right - left) < absolutePrecision:
            return (left + right)/2

        leftThird = left + (right - left)/3
        rightThird = right - (right - left)/3

        if f(leftThird) > f(rightThird):
            left = leftThird
        else:
            right = rightThird
'''

UTILITIES_FUNC_COMMON_IKFK = ['''
#########################################
## "Visual Transform" helper functions ##
#########################################

def get_pose_matrix_in_other_space(mat, pose_bone):
    """ Returns the transform matrix relative to pose_bone's current
        transform space.  In other words, presuming that mat is in
        armature space, slapping the returned matrix onto pose_bone
        should give it the armature-space transforms of mat.
    """
    return pose_bone.id_data.convert_space(matrix=mat, pose_bone=pose_bone, from_space='POSE', to_space='LOCAL')


def get_local_pose_matrix(pose_bone):
    """ Returns the local transform matrix of the given pose bone.
    """
    return get_pose_matrix_in_other_space(pose_bone.matrix, pose_bone)


def set_pose_translation(pose_bone, mat):
    """ Sets the pose bone's translation to the same translation as the given matrix.
        Matrix should be given in bone's local space.
    """
    pose_bone.location = mat.to_translation()


def set_pose_rotation(pose_bone, mat):
    """ Sets the pose bone's rotation to the same rotation as the given matrix.
        Matrix should be given in bone's local space.
    """
    q = mat.to_quaternion()

    if pose_bone.rotation_mode == 'QUATERNION':
        pose_bone.rotation_quaternion = q
    elif pose_bone.rotation_mode == 'AXIS_ANGLE':
        pose_bone.rotation_axis_angle[0] = q.angle
        pose_bone.rotation_axis_angle[1] = q.axis[0]
        pose_bone.rotation_axis_angle[2] = q.axis[1]
        pose_bone.rotation_axis_angle[3] = q.axis[2]
    else:
        pose_bone.rotation_euler = q.to_euler(pose_bone.rotation_mode)


def set_pose_scale(pose_bone, mat):
    """ Sets the pose bone's scale to the same scale as the given matrix.
        Matrix should be given in bone's local space.
    """
    pose_bone.scale = mat.to_scale()


def match_pose_translation(pose_bone, target_bone):
    """ Matches pose_bone's visual translation to target_bone's visual
        translation.
        This function assumes you are in pose mode on the relevant armature.
    """
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_translation(pose_bone, mat)


def match_pose_rotation(pose_bone, target_bone):
    """ Matches pose_bone's visual rotation to target_bone's visual
        rotation.
        This function assumes you are in pose mode on the relevant armature.
    """
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_rotation(pose_bone, mat)


def match_pose_scale(pose_bone, target_bone):
    """ Matches pose_bone's visual scale to target_bone's visual
        scale.
        This function assumes you are in pose mode on the relevant armature.
    """
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_scale(pose_bone, mat)


##############################
## IK/FK snapping functions ##
##############################

def correct_rotation(view_layer, bone_ik, target_matrix):
    """ Corrects the ik rotation in ik2fk snapping functions
    """

    axis = target_matrix.to_3x3().col[1].normalized()

    def distance(angle):
        # Rotate the bone and return the actual angle between bones
        bone_ik.rotation_euler[1] = angle
        view_layer.update()

        return -(bone_ik.vector.normalized().dot(axis))

    if bone_ik.rotation_mode in {'QUATERNION', 'AXIS_ANGLE'}:
        bone_ik.rotation_mode = 'ZXY'

    start_angle = bone_ik.rotation_euler[1]

    alfarange = find_min_range(distance, start_angle)
    alfamin = ternarySearch(distance, alfarange[0], alfarange[1], pi / 180)

    bone_ik.rotation_euler[1] = alfamin
    view_layer.update()


def correct_scale(view_layer, bone_ik, target_matrix):
    """ Correct the scale of the base IK bone. """
    input_scale = target_matrix.to_scale()

    for i in range(3):
        cur_scale = bone_ik.matrix.to_scale()

        bone_ik.scale = [
            v * i / c for v, i, c in zip(bone_ik.scale, input_scale, cur_scale)
        ]

        view_layer.update()

        if all(abs((c - i)/i) < 0.01 for i, c in zip(input_scale, cur_scale)):
            break


def match_pole_target(view_layer, ik_first, ik_last, pole, match_bone_matrix, length):
    """ Places an IK chain's pole target to match ik_first's
        transforms to match_bone.  All bones should be given as pose bones.
        You need to be in pose mode on the relevant armature object.
        ik_first: first bone in the IK chain
        ik_last:  last bone in the IK chain
        pole:  pole target bone for the IK chain
        match_bone:  bone to match ik_first to (probably first bone in a matching FK chain)
        length:  distance pole target should be placed from the chain center
    """
    a = ik_first.matrix.to_translation()
    b = ik_last.matrix.to_translation() + ik_last.vector

    # Vector from the head of ik_first to the
    # tip of ik_last
    ikv = b - a

    # Get a vector perpendicular to ikv
    pv = perpendicular_vector(ikv).normalized() * length

    def set_pole(pvi):
        """ Set pole target's position based on a vector
            from the arm center line.
        """
        # Translate pvi into armature space
        ploc = a + (ikv/2) + pvi

        # Set pole target to location
        mat = get_pose_matrix_in_other_space(Matrix.Translation(ploc), pole)
        set_pose_translation(pole, mat)

        view_layer.update()

    set_pole(pv)

    # Get the rotation difference between ik_first and match_bone
    angle = rotation_difference(ik_first.matrix, match_bone_matrix)

    # Try compensating for the rotation difference in both directions
    pv1 = Matrix.Rotation(angle, 4, ikv) @ pv
    set_pole(pv1)
    ang1 = rotation_difference(ik_first.matrix, match_bone_matrix)

    pv2 = Matrix.Rotation(-angle, 4, ikv) @ pv
    set_pole(pv2)
    ang2 = rotation_difference(ik_first.matrix, match_bone_matrix)

    # Do the one with the smaller angle
    if ang1 < ang2:
        set_pole(pv1)

##########
## Misc ##
##########

def parse_bone_names(names_string):
    if names_string[0] == '[' and names_string[-1] == ']':
        return eval(names_string)
    else:
        return names_string

''']

UTILITIES_FUNC_OLD_ARM_FKIK = ['''
######################
## IK Arm functions ##
######################

def fk2ik_arm(obj, fk, ik):
    """ Matches the fk bones in an arm rig to the ik bones.
        obj: armature object
        fk:  list of fk bone names
        ik:  list of ik bone names
    """
    view_layer = bpy.context.view_layer
    uarm  = obj.pose.bones[fk[0]]
    farm  = obj.pose.bones[fk[1]]
    hand  = obj.pose.bones[fk[2]]
    uarmi = obj.pose.bones[ik[0]]
    farmi = obj.pose.bones[ik[1]]
    handi = obj.pose.bones[ik[2]]

    if 'auto_stretch' in handi.keys():
        # This is kept for compatibility with legacy rigify Human
        # Stretch
        if handi['auto_stretch'] == 0.0:
            uarm['stretch_length'] = handi['stretch_length']
        else:
            diff = (uarmi.vector.length + farmi.vector.length) / (uarm.vector.length + farm.vector.length)
            uarm['stretch_length'] *= diff

        # Upper arm position
        match_pose_rotation(uarm, uarmi)
        match_pose_scale(uarm, uarmi)
        view_layer.update()

        # Forearm position
        match_pose_rotation(farm, farmi)
        match_pose_scale(farm, farmi)
        view_layer.update()

        # Hand position
        match_pose_rotation(hand, handi)
        match_pose_scale(hand, handi)
        view_layer.update()
    else:
        # Upper arm position
        match_pose_translation(uarm, uarmi)
        match_pose_rotation(uarm, uarmi)
        match_pose_scale(uarm, uarmi)
        view_layer.update()

        # Forearm position
        #match_pose_translation(hand, handi)
        match_pose_rotation(farm, farmi)
        match_pose_scale(farm, farmi)
        view_layer.update()

        # Hand position
        match_pose_translation(hand, handi)
        match_pose_rotation(hand, handi)
        match_pose_scale(hand, handi)
        view_layer.update()


def ik2fk_arm(obj, fk, ik):
    """ Matches the ik bones in an arm rig to the fk bones.
        obj: armature object
        fk:  list of fk bone names
        ik:  list of ik bone names
    """
    view_layer = bpy.context.view_layer
    uarm  = obj.pose.bones[fk[0]]
    farm  = obj.pose.bones[fk[1]]
    hand  = obj.pose.bones[fk[2]]
    uarmi = obj.pose.bones[ik[0]]
    farmi = obj.pose.bones[ik[1]]
    handi = obj.pose.bones[ik[2]]

    main_parent = obj.pose.bones[ik[4]]

    if ik[3] != "" and main_parent['pole_vector']:
        pole  = obj.pose.bones[ik[3]]
    else:
        pole = None


    if pole:
        # Stretch
        # handi['stretch_length'] = uarm['stretch_length']

        # Hand position
        match_pose_translation(handi, hand)
        match_pose_rotation(handi, hand)
        match_pose_scale(handi, hand)
        view_layer.update()

        # Pole target position
        match_pole_target(view_layer, uarmi, farmi, pole, uarm.matrix, (uarmi.length + farmi.length))

    else:
        # Hand position
        match_pose_translation(handi, hand)
        match_pose_rotation(handi, hand)
        match_pose_scale(handi, hand)
        view_layer.update()

        # Upper Arm position
        match_pose_translation(uarmi, uarm)
        #match_pose_rotation(uarmi, uarm)
        set_pose_rotation(uarmi, Matrix())
        match_pose_scale(uarmi, uarm)
        view_layer.update()

        # Rotation Correction
        correct_rotation(view_layer, uarmi, uarm.matrix)

    correct_scale(view_layer, uarmi, uarm.matrix)
''']

UTILITIES_FUNC_OLD_LEG_FKIK = ['''
######################
## IK Leg functions ##
######################

def fk2ik_leg(obj, fk, ik):
    """ Matches the fk bones in a leg rig to the ik bones.
        obj: armature object
        fk:  list of fk bone names
        ik:  list of ik bone names
    """
    view_layer = bpy.context.view_layer
    thigh  = obj.pose.bones[fk[0]]
    shin   = obj.pose.bones[fk[1]]
    foot   = obj.pose.bones[fk[2]]
    mfoot  = obj.pose.bones[fk[3]]
    thighi = obj.pose.bones[ik[0]]
    shini  = obj.pose.bones[ik[1]]
    footi  = obj.pose.bones[ik[2]]
    mfooti = obj.pose.bones[ik[3]]

    if 'auto_stretch' in footi.keys():
        # This is kept for compatibility with legacy rigify Human
        # Stretch
        if footi['auto_stretch'] == 0.0:
            thigh['stretch_length'] = footi['stretch_length']
        else:
            diff = (thighi.vector.length + shini.vector.length) / (thigh.vector.length + shin.vector.length)
            thigh['stretch_length'] *= diff

        # Thigh position
        match_pose_rotation(thigh, thighi)
        match_pose_scale(thigh, thighi)
        view_layer.update()

        # Shin position
        match_pose_rotation(shin, shini)
        match_pose_scale(shin, shini)
        view_layer.update()

        # Foot position
        mat = mfoot.bone.matrix_local.inverted() @ foot.bone.matrix_local
        footmat = get_pose_matrix_in_other_space(mfooti.matrix, foot) @ mat
        set_pose_rotation(foot, footmat)
        set_pose_scale(foot, footmat)
        view_layer.update()

    else:
        # Thigh position
        match_pose_translation(thigh, thighi)
        match_pose_rotation(thigh, thighi)
        match_pose_scale(thigh, thighi)
        view_layer.update()

        # Shin position
        match_pose_rotation(shin, shini)
        match_pose_scale(shin, shini)
        view_layer.update()

        # Foot position
        mat = mfoot.bone.matrix_local.inverted() @ foot.bone.matrix_local
        footmat = get_pose_matrix_in_other_space(mfooti.matrix, foot) @ mat
        set_pose_rotation(foot, footmat)
        set_pose_scale(foot, footmat)
        view_layer.update()


def ik2fk_leg(obj, fk, ik):
    """ Matches the ik bones in a leg rig to the fk bones.
        obj: armature object
        fk:  list of fk bone names
        ik:  list of ik bone names
    """
    view_layer = bpy.context.view_layer
    thigh    = obj.pose.bones[fk[0]]
    shin     = obj.pose.bones[fk[1]]
    mfoot    = obj.pose.bones[fk[2]]
    if fk[3] != "":
        foot      = obj.pose.bones[fk[3]]
    else:
        foot = None
    thighi   = obj.pose.bones[ik[0]]
    shini    = obj.pose.bones[ik[1]]
    footi    = obj.pose.bones[ik[2]]
    footroll = obj.pose.bones[ik[3]]

    main_parent = obj.pose.bones[ik[6]]

    if ik[4] != "" and main_parent['pole_vector']:
        pole     = obj.pose.bones[ik[4]]
    else:
        pole = None
    mfooti   = obj.pose.bones[ik[5]]

    if (not pole) and (foot):

        # Clear footroll
        set_pose_rotation(footroll, Matrix())
        view_layer.update()

        # Foot position
        mat = mfooti.bone.matrix_local.inverted() @ footi.bone.matrix_local
        footmat = get_pose_matrix_in_other_space(foot.matrix, footi) @ mat
        set_pose_translation(footi, footmat)
        set_pose_rotation(footi, footmat)
        set_pose_scale(footi, footmat)
        view_layer.update()

        # Thigh position
        match_pose_translation(thighi, thigh)
        #match_pose_rotation(thighi, thigh)
        set_pose_rotation(thighi, Matrix())
        match_pose_scale(thighi, thigh)
        view_layer.update()

        # Rotation Correction
        correct_rotation(view_layer, thighi, thigh.matrix)

    else:
        # Stretch
        if 'stretch_length' in footi.keys() and 'stretch_length' in thigh.keys():
            # Kept for compat with legacy rigify Human
            footi['stretch_length'] = thigh['stretch_length']

        # Clear footroll
        set_pose_rotation(footroll, Matrix())
        view_layer.update()

        # Foot position
        mat = mfooti.bone.matrix_local.inverted() @ footi.bone.matrix_local
        footmat = get_pose_matrix_in_other_space(mfoot.matrix, footi) @ mat
        set_pose_translation(footi, footmat)
        set_pose_rotation(footi, footmat)
        set_pose_scale(footi, footmat)
        view_layer.update()

        # Pole target position
        match_pole_target(view_layer, thighi, shini, pole, thigh.matrix, (thighi.length + shini.length))

    correct_scale(view_layer, thighi, thigh.matrix)
''']

UTILITIES_FUNC_OLD_POLE = ['''
################################
## IK Rotation-Pole functions ##
################################

def rotPoleToggle(rig, limb_type, controls, ik_ctrl, fk_ctrl, parent, pole):

    rig_id = rig.data['rig_id']
    leg_fk2ik = eval('bpy.ops.pose.rigify_leg_fk2ik_' + rig_id)
    arm_fk2ik = eval('bpy.ops.pose.rigify_arm_fk2ik_' + rig_id)
    leg_ik2fk = eval('bpy.ops.pose.rigify_leg_ik2fk_' + rig_id)
    arm_ik2fk = eval('bpy.ops.pose.rigify_arm_ik2fk_' + rig_id)

    controls = parse_bone_names(controls)
    ik_ctrl = parse_bone_names(ik_ctrl)
    fk_ctrl = parse_bone_names(fk_ctrl)
    parent = parse_bone_names(parent)
    pole = parse_bone_names(pole)

    pbones = bpy.context.selected_pose_bones
    bpy.ops.pose.select_all(action='DESELECT')

    for b in pbones:

        new_pole_vector_value = not rig.pose.bones[parent]['pole_vector']

        if b.name in controls or b.name in ik_ctrl:
            if limb_type == 'arm':
                func1 = arm_fk2ik
                func2 = arm_ik2fk
                rig.pose.bones[controls[0]].bone.select = not new_pole_vector_value
                rig.pose.bones[controls[4]].bone.select = not new_pole_vector_value
                rig.pose.bones[parent].bone.select = not new_pole_vector_value
                rig.pose.bones[pole].bone.select = new_pole_vector_value

                kwargs1 = {'uarm_fk': controls[1], 'farm_fk': controls[2], 'hand_fk': controls[3],
                          'uarm_ik': controls[0], 'farm_ik': ik_ctrl[1],
                          'hand_ik': controls[4]}
                kwargs2 = {'uarm_fk': controls[1], 'farm_fk': controls[2], 'hand_fk': controls[3],
                          'uarm_ik': controls[0], 'farm_ik': ik_ctrl[1], 'hand_ik': controls[4],
                          'pole': pole, 'main_parent': parent}
            else:
                func1 = leg_fk2ik
                func2 = leg_ik2fk
                rig.pose.bones[controls[0]].bone.select = not new_pole_vector_value
                rig.pose.bones[controls[6]].bone.select = not new_pole_vector_value
                rig.pose.bones[controls[5]].bone.select = not new_pole_vector_value
                rig.pose.bones[parent].bone.select = not new_pole_vector_value
                rig.pose.bones[pole].bone.select = new_pole_vector_value

                kwargs1 = {'thigh_fk': controls[1], 'shin_fk': controls[2], 'foot_fk': controls[3],
                          'mfoot_fk': controls[7], 'thigh_ik': controls[0], 'shin_ik': ik_ctrl[1],
                          'foot_ik': ik_ctrl[2], 'mfoot_ik': ik_ctrl[2]}
                kwargs2 = {'thigh_fk': controls[1], 'shin_fk': controls[2], 'foot_fk': controls[3],
                          'mfoot_fk': controls[7], 'thigh_ik': controls[0], 'shin_ik': ik_ctrl[1],
                          'foot_ik': controls[6], 'pole': pole, 'footroll': controls[5], 'mfoot_ik': ik_ctrl[2],
                          'main_parent': parent}

            func1(**kwargs1)
            rig.pose.bones[parent]['pole_vector'] = new_pole_vector_value
            func2(**kwargs2)

            bpy.ops.pose.select_all(action='DESELECT')
''']

REGISTER_OP_OLD_ARM_FKIK = ['Rigify_Arm_FK2IK', 'Rigify_Arm_IK2FK']

UTILITIES_OP_OLD_ARM_FKIK = ['''
##################################
## IK/FK Arm snapping operators ##
##################################

class Rigify_Arm_FK2IK(bpy.types.Operator):
    """ Snaps an FK arm to an IK arm.
    """
    bl_idname = "pose.rigify_arm_fk2ik_" + rig_id
    bl_label = "Rigify Snap FK arm to IK"
    bl_options = {'UNDO', 'INTERNAL'}

    uarm_fk: StringProperty(name="Upper Arm FK Name")
    farm_fk: StringProperty(name="Forerm FK Name")
    hand_fk: StringProperty(name="Hand FK Name")

    uarm_ik: StringProperty(name="Upper Arm IK Name")
    farm_ik: StringProperty(name="Forearm IK Name")
    hand_ik: StringProperty(name="Hand IK Name")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        fk2ik_arm(context.active_object, fk=[self.uarm_fk, self.farm_fk, self.hand_fk], ik=[self.uarm_ik, self.farm_ik, self.hand_ik])
        return {'FINISHED'}


class Rigify_Arm_IK2FK(bpy.types.Operator):
    """ Snaps an IK arm to an FK arm.
    """
    bl_idname = "pose.rigify_arm_ik2fk_" + rig_id
    bl_label = "Rigify Snap IK arm to FK"
    bl_options = {'UNDO', 'INTERNAL'}

    uarm_fk: StringProperty(name="Upper Arm FK Name")
    farm_fk: StringProperty(name="Forerm FK Name")
    hand_fk: StringProperty(name="Hand FK Name")

    uarm_ik: StringProperty(name="Upper Arm IK Name")
    farm_ik: StringProperty(name="Forearm IK Name")
    hand_ik: StringProperty(name="Hand IK Name")
    pole   : StringProperty(name="Pole IK Name")

    main_parent: StringProperty(name="Main Parent", default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        ik2fk_arm(context.active_object, fk=[self.uarm_fk, self.farm_fk, self.hand_fk], ik=[self.uarm_ik, self.farm_ik, self.hand_ik, self.pole, self.main_parent])
        return {'FINISHED'}
''']

REGISTER_OP_OLD_LEG_FKIK = ['Rigify_Leg_FK2IK', 'Rigify_Leg_IK2FK']

UTILITIES_OP_OLD_LEG_FKIK = ['''
##################################
## IK/FK Leg snapping operators ##
##################################

class Rigify_Leg_FK2IK(bpy.types.Operator):
    """ Snaps an FK leg to an IK leg.
    """
    bl_idname = "pose.rigify_leg_fk2ik_" + rig_id
    bl_label = "Rigify Snap FK leg to IK"
    bl_options = {'UNDO', 'INTERNAL'}

    thigh_fk: StringProperty(name="Thigh FK Name")
    shin_fk:  StringProperty(name="Shin FK Name")
    foot_fk:  StringProperty(name="Foot FK Name")
    mfoot_fk: StringProperty(name="MFoot FK Name")

    thigh_ik: StringProperty(name="Thigh IK Name")
    shin_ik:  StringProperty(name="Shin IK Name")
    foot_ik:  StringProperty(name="Foot IK Name")
    mfoot_ik: StringProperty(name="MFoot IK Name")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        fk2ik_leg(context.active_object, fk=[self.thigh_fk, self.shin_fk, self.foot_fk, self.mfoot_fk], ik=[self.thigh_ik, self.shin_ik, self.foot_ik, self.mfoot_ik])
        return {'FINISHED'}


class Rigify_Leg_IK2FK(bpy.types.Operator):
    """ Snaps an IK leg to an FK leg.
    """
    bl_idname = "pose.rigify_leg_ik2fk_" + rig_id
    bl_label = "Rigify Snap IK leg to FK"
    bl_options = {'UNDO', 'INTERNAL'}

    thigh_fk: StringProperty(name="Thigh FK Name")
    shin_fk:  StringProperty(name="Shin FK Name")
    mfoot_fk: StringProperty(name="MFoot FK Name")
    foot_fk:  StringProperty(name="Foot FK Name", default="")
    thigh_ik: StringProperty(name="Thigh IK Name")
    shin_ik:  StringProperty(name="Shin IK Name")
    foot_ik:  StringProperty(name="Foot IK Name")
    footroll: StringProperty(name="Foot Roll Name")
    pole:     StringProperty(name="Pole IK Name")
    mfoot_ik: StringProperty(name="MFoot IK Name")

    main_parent: StringProperty(name="Main Parent", default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        ik2fk_leg(context.active_object, fk=[self.thigh_fk, self.shin_fk, self.mfoot_fk, self.foot_fk], ik=[self.thigh_ik, self.shin_ik, self.foot_ik, self.footroll, self.pole, self.mfoot_ik, self.main_parent])
        return {'FINISHED'}
''']

REGISTER_OP_OLD_POLE = ['Rigify_Rot2PoleSwitch']

UTILITIES_OP_OLD_POLE = ['''
###########################
## IK Rotation Pole Snap ##
###########################

class Rigify_Rot2PoleSwitch(bpy.types.Operator):
    bl_idname = "pose.rigify_rot2pole_" + rig_id
    bl_label = "Rotation - Pole toggle"
    bl_description = "Toggles IK chain between rotation and pole target"

    bone_name: StringProperty(default='')
    limb_type: StringProperty(name="Limb Type")
    controls: StringProperty(name="Controls string")
    ik_ctrl: StringProperty(name="IK Controls string")
    fk_ctrl: StringProperty(name="FK Controls string")
    parent: StringProperty(name="Parent name")
    pole: StringProperty(name="Pole name")

    def execute(self, context):
        rig = context.object

        if self.bone_name:
            bpy.ops.pose.select_all(action='DESELECT')
            rig.pose.bones[self.bone_name].bone.select = True

        rotPoleToggle(rig, self.limb_type, self.controls, self.ik_ctrl, self.fk_ctrl, self.parent, self.pole)
        return {'FINISHED'}
''']

REGISTER_RIG_OLD_ARM = REGISTER_OP_OLD_ARM_FKIK + REGISTER_OP_OLD_POLE

UTILITIES_RIG_OLD_ARM = [
    *UTILITIES_FUNC_COMMON_IKFK,
    *UTILITIES_FUNC_OLD_ARM_FKIK,
    *UTILITIES_FUNC_OLD_POLE,
    *UTILITIES_OP_OLD_ARM_FKIK,
    *UTILITIES_OP_OLD_POLE,
]

REGISTER_RIG_OLD_LEG = REGISTER_OP_OLD_LEG_FKIK + REGISTER_OP_OLD_POLE

UTILITIES_RIG_OLD_LEG = [
    *UTILITIES_FUNC_COMMON_IKFK,
    *UTILITIES_FUNC_OLD_LEG_FKIK,
    *UTILITIES_FUNC_OLD_POLE,
    *UTILITIES_OP_OLD_LEG_FKIK,
    *UTILITIES_OP_OLD_POLE,
]

##############################
## Default set of utilities ##
##############################

UI_REGISTER = [
    'RigUI',
    'RigLayers',
]

UI_UTILITIES = [
]

UI_SLIDERS = '''
###################
## Rig UI Panels ##
###################

class RigUI(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Main Properties"
    bl_idname = "VIEW3D_PT_rig_ui_" + rig_id
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        if context.mode != 'POSE':
            return False
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        pose_bones = context.active_object.pose.bones
        try:
            selected_bones = set(bone.name for bone in context.selected_pose_bones)
            selected_bones.add(context.active_pose_bone.name)
        except (AttributeError, TypeError):
            return

        def is_selected(names):
            # Returns whether any of the named bones are selected.
            if isinstance(names, list) or isinstance(names, set):
                return not selected_bones.isdisjoint(names)
            elif names in selected_bones:
                return True
            return False

        num_rig_separators = [-1]

        def emit_rig_separator():
            if num_rig_separators[0] >= 0:
                layout.separator()
            num_rig_separators[0] += 1
'''

UI_REGISTER_BAKE_SETTINGS = ['RigBakeSettings']

UI_BAKE_SETTINGS = '''
class RigBakeSettings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Bake Settings"
    bl_idname = "VIEW3D_PT_rig_bake_settings_" + rig_id
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        return RigUI.poll(context) and find_action(context.active_object) is not None

    def draw(self, context):
        RigifyBakeKeyframesMixin.draw_common_bake_ui(context, self.layout)
'''

def layers_ui(layers, layout):
    """ Turn a list of booleans + a list of names into a layer UI.
    """

    code = '''
class RigLayers(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Layers"
    bl_idname = "VIEW3D_PT_rig_layers_" + rig_id
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        col = layout.column()
'''
    rows = {}
    for i in range(28):
        if layers[i]:
            if layout[i][1] not in rows:
                rows[layout[i][1]] = []
            rows[layout[i][1]] += [(layout[i][0], i)]

    keys = list(rows.keys())
    keys.sort()

    for key in keys:
        code += "\n        row = col.row()\n"
        i = 0
        for l in rows[key]:
            if i > 3:
                code += "\n        row = col.row()\n"
                i = 0
            code += "        row.prop(context.active_object.data, 'layers', index=%s, toggle=True, text='%s')\n" % (str(l[1]), l[0])
            i += 1

    # Root layer
    code += "\n        row = col.row()"
    code += "\n        row.separator()"
    code += "\n        row = col.row()"
    code += "\n        row.separator()\n"
    code += "\n        row = col.row()\n"
    code += "        row.prop(context.active_object.data, 'layers', index=28, toggle=True, text='Root')\n"

    return code


def quote_parameters(positional, named):
    """Quote the given positional and named parameters as a code string."""
    positional_list = [ repr(v) for v in positional ]
    named_list = [ "%s=%r" % (k, v) for k, v in named.items() ]
    return ', '.join(positional_list + named_list)

def indent_lines(lines, indent=4):
    if indent > 0:
        prefix = ' ' * indent
        return [ prefix + line for line in lines ]
    else:
        return lines


class PanelLayout(object):
    """Utility class that builds code for creating a layout."""

    def __init__(self, parent, index=0):
        if isinstance(parent, PanelLayout):
            self.parent = parent
            self.script = parent.script
        else:
            self.parent = None
            self.script = parent

        self.header = []
        self.items = []
        self.indent = 0
        self.index = index
        self.layout = self._get_layout_var(index)
        self.is_empty = True

    @staticmethod
    def _get_layout_var(index):
        return 'layout' if index == 0 else 'group' + str(index)

    def clear_empty(self):
        self.is_empty = False

        if self.parent:
            self.parent.clear_empty()

    def get_lines(self):
        lines = []

        for item in self.items:
            if isinstance(item, PanelLayout):
                lines += item.get_lines()
            else:
                lines.append(item)

        if len(lines) > 0:
            return self.wrap_lines(lines)
        else:
            return []

    def wrap_lines(self, lines):
        return self.header + indent_lines(lines, self.indent)

    def add_line(self, line):
        assert isinstance(line, str)

        self.items.append(line)

        if self.is_empty:
            self.clear_empty()

    def use_bake_settings(self):
        """This panel contains operators that need the common Bake settings."""
        self.parent.use_bake_settings()

    def custom_prop(self, bone_name, prop_name, **params):
        """Add a custom property input field to the panel."""
        param_str = quote_parameters([ rna_idprop_quote_path(prop_name) ], params)
        self.add_line(
            "%s.prop(pose_bones[%r], %s)" % (self.layout, bone_name, param_str)
        )

    def operator(self, operator_name, *, properties=None, **params):
        """Add an operator call button to the panel."""
        name = operator_name.format_map(self.script.format_args)
        param_str = quote_parameters([ name ], params)
        call_str = "%s.operator(%s)" % (self.layout, param_str)
        if properties:
            self.add_line("props = " + call_str)
            for k, v in properties.items():
                self.add_line("props.%s = %r" % (k,v))
        else:
            self.add_line(call_str)

    def add_nested_layout(self, name, params):
        param_str = quote_parameters([], params)
        sub_panel = PanelLayout(self, self.index + 1)
        sub_panel.header.append('%s = %s.%s(%s)' % (sub_panel.layout, self.layout, name, param_str))
        self.items.append(sub_panel)
        return sub_panel

    def row(self, **params):
        """Add a nested row layout to the panel."""
        return self.add_nested_layout('row', params)

    def column(self, **params):
        """Add a nested column layout to the panel."""
        return self.add_nested_layout('column', params)

    def split(self, **params):
        """Add a split layout to the panel."""
        return self.add_nested_layout('split', params)


class BoneSetPanelLayout(PanelLayout):
    """Panel restricted to a certain set of bones."""

    def __init__(self, rig_panel, bones):
        assert isinstance(bones, frozenset)
        super().__init__(rig_panel)
        self.bones = bones
        self.show_bake_settings = False

    def clear_empty(self):
        self.parent.bones |= self.bones

        super().clear_empty()

    def wrap_lines(self, lines):
        if self.bones != self.parent.bones:
            header = ["if is_selected(%r):" % (set(self.bones))]
            return header + indent_lines(lines)
        else:
            return lines

    def use_bake_settings(self):
        self.show_bake_settings = True
        if not self.script.use_bake_settings:
            self.script.use_bake_settings = True
            self.script.add_utilities(SCRIPT_UTILITIES_BAKE)
            self.script.register_classes(SCRIPT_REGISTER_BAKE)


class RigPanelLayout(PanelLayout):
    """Panel owned by a certain rig."""

    def __init__(self, script, rig):
        super().__init__(script)
        self.bones = set()
        self.subpanels = OrderedDict()

    def wrap_lines(self, lines):
        header = [ "if is_selected(%r):" % (set(self.bones)) ]
        prefix = [ "emit_rig_separator()" ]
        return header + indent_lines(prefix + lines)

    def panel_with_selected_check(self, control_names):
        selected_set = frozenset(control_names)

        if selected_set in self.subpanels:
            return self.subpanels[selected_set]
        else:
            panel = BoneSetPanelLayout(self, selected_set)
            self.subpanels[selected_set] = panel
            self.items.append(panel)
            return panel


class ScriptGenerator(base_generate.GeneratorPlugin):
    """Generator plugin that builds the python script attached to the rig."""

    priority = -100

    def __init__(self, generator):
        super().__init__(generator)

        self.ui_scripts = []
        self.ui_imports = UI_IMPORTS.copy()
        self.ui_utilities = UI_UTILITIES.copy()
        self.ui_register = UI_REGISTER.copy()
        self.ui_register_drivers = []
        self.ui_register_props = []

        self.ui_rig_panels = OrderedDict()

        self.use_bake_settings = False

    # Structured panel code generation
    def panel_with_selected_check(self, rig, control_names):
        """Add a panel section with restricted selection."""
        rig_key = id(rig)

        if rig_key in self.ui_rig_panels:
            panel = self.ui_rig_panels[rig_key]
        else:
            panel = RigPanelLayout(self, rig)
            self.ui_rig_panels[rig_key] = panel

        return panel.panel_with_selected_check(control_names)

    # Raw output
    def add_panel_code(self, str_list):
        """Add raw code to the panel."""
        self.ui_scripts += str_list

    def add_imports(self, str_list):
        self.ui_imports += str_list

    def add_utilities(self, str_list):
        self.ui_utilities += str_list

    def register_classes(self, str_list):
        self.ui_register += str_list

    def register_driver_functions(self, str_list):
        self.ui_register_drivers += str_list

    def register_property(self, name, definition):
        self.ui_register_props.append((name, definition))

    def initialize(self):
        self.format_args = {
            'rig_id': self.generator.rig_id,
        }

    def finalize(self):
        metarig = self.generator.metarig
        rig_id = self.generator.rig_id

        vis_layers = self.obj.data.layers

        # Ensure the collection of layer names exists
        for i in range(1 + len(metarig.data.rigify_layers), 29):
            metarig.data.rigify_layers.add()

        # Create list of layer name/row pairs
        layer_layout = []
        for l in metarig.data.rigify_layers:
            layer_layout += [(l.name, l.row)]

        # Generate the UI script
        if metarig.data.rigify_rig_basename:
            rig_ui_name = metarig.data.rigify_rig_basename + '_ui.py'
        else:
            rig_ui_name = 'rig_ui.py'

        script = None

        if metarig.data.rigify_generate_mode == 'overwrite':
            script = metarig.data.rigify_rig_ui

            if not script and rig_ui_name in bpy.data.texts:
                script = bpy.data.texts[rig_ui_name]

            if script:
                script.clear()
                script.name = rig_ui_name

        if script is None:
            script = bpy.data.texts.new(rig_ui_name)

        metarig.data.rigify_rig_ui = script

        for s in OrderedDict.fromkeys(self.ui_imports):
            script.write(s + "\n")

        script.write(UI_BASE_UTILITIES % rig_id)

        for s in OrderedDict.fromkeys(self.ui_utilities):
            script.write(s + "\n")

        script.write(UI_SLIDERS)

        for s in self.ui_scripts:
            script.write("\n        " + s.replace("\n", "\n        ") + "\n")

        if len(self.ui_scripts) > 0:
            script.write("\n        num_rig_separators[0] = 0\n")

        for panel in self.ui_rig_panels.values():
            lines = panel.get_lines()
            if len(lines) > 1:
                script.write("\n        ".join([''] + lines) + "\n")

        if self.use_bake_settings:
            self.ui_register = UI_REGISTER_BAKE_SETTINGS + self.ui_register
            script.write(UI_BAKE_SETTINGS)

        script.write(layers_ui(vis_layers, layer_layout))

        script.write("\ndef register():\n")

        ui_register = OrderedDict.fromkeys(self.ui_register)
        for s in ui_register:
            script.write("    bpy.utils.register_class("+s+")\n")

        ui_register_drivers = OrderedDict.fromkeys(self.ui_register_drivers)
        for s in ui_register_drivers:
            script.write("    bpy.app.driver_namespace['"+s+"'] = "+s+"\n")

        ui_register_props = OrderedDict.fromkeys(self.ui_register_props)
        for s in ui_register_props:
            script.write("    bpy.types.%s = %s\n " % (*s,))

        script.write("\ndef unregister():\n")

        for s in ui_register_props:
            script.write("    del bpy.types.%s\n" % s[0])

        for s in ui_register:
            script.write("    bpy.utils.unregister_class("+s+")\n")

        for s in ui_register_drivers:
            script.write("    del bpy.app.driver_namespace['"+s+"']\n")

        script.write("\nregister()\n")
        script.use_module = True

        # Run UI script
        exec(script.as_string(), {})

        # Attach the script to the rig
        attach_persistent_script(self.obj, script)
