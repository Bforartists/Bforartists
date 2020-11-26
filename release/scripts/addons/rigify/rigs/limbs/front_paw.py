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

from ...utils.bones import align_bone_roll, put_bone, copy_bone_position, flip_bone
from ...utils.naming import make_derived_name
from ...utils.misc import map_list

from itertools import count

from ...base_rig import stage

from .limb_rigs import BaseLimbRig
from .paw import Rig as pawRig


class Rig(pawRig):
    """Front paw rig with special IK automation."""

    ####################################################
    # EXTRA BONES
    #
    # mch:
    #   ik2_chain[2]
    #     Second IK system (pre-driving heel)
    #   heel_track
    #     Bone tracking IK2 to rotate heel
    #   heel_parent
    #     Parent of the heel control
    #
    ####################################################

    ####################################################
    # IK controls

    def get_middle_ik_controls(self):
        return [self.bones.ctrl.heel]

    def get_ik_fk_position_chains(self):
        ik_chain, fk_chain = super().get_ik_fk_position_chains()
        if not self.use_heel2:
            return [*ik_chain, ik_chain[-1]], [*fk_chain, fk_chain[-1]]
        return ik_chain, fk_chain

    def get_extra_ik_controls(self):
        extra = [self.bones.ctrl.heel2] if self.use_heel2 else []
        return BaseLimbRig.get_extra_ik_controls(self) + extra

    def get_ik_pole_parents(self):
        return [(self.get_ik2_target_bone(), self.bones.ctrl.ik)]


    ####################################################
    # Second IK system (pre-driving heel)

    use_mch_ik_base = True

    def get_ik2_target_bone(self):
        return self.bones.mch.ik2_target if self.use_heel2 else self.bones.mch.toe_socket

    @stage.generate_bones
    def make_ik2_mch_chain(self):
        orgs = self.bones.org.main
        chain = map_list(self.make_ik2_mch_bone, count(0), orgs[0:2])
        self.bones.mch.ik2_chain = chain

        if self.use_heel2:
            self.bones.mch.ik2_target = self.make_ik2_mch_target_bone(orgs)

        # Connect the chain end to the target
        self.get_bone(chain[1]).tail = self.get_bone(orgs[2]).tail
        align_bone_roll(self.obj, chain[1], orgs[1])

    def make_ik2_mch_target_bone(self, orgs):
        return self.copy_bone(orgs[3], make_derived_name(orgs[0], 'mch', '_ik2_target'), scale=1/2)

    def make_ik2_mch_bone(self, i, org):
        return self.copy_bone(org, make_derived_name(org, 'mch', '_ik2'))

    @stage.parent_bones
    def parent_ik2_mch_chain(self):
        mch = self.bones.mch
        if self.use_heel2:
            self.set_bone_parent(mch.ik2_target, self.bones.ctrl.heel2)
        self.set_bone_parent(mch.ik2_chain[0], self.bones.ctrl.ik_base, inherit_scale='AVERAGE')
        self.parent_bone_chain(mch.ik2_chain, use_connect=True)

    @stage.configure_bones
    def configure_ik2_mch_chain(self):
        for i, mch in enumerate(self.bones.mch.ik2_chain):
            self.configure_ik2_mch_bone(i, mch)

    def configure_ik2_mch_bone(self, i, mch):
        bone = self.get_bone(mch)
        bone.ik_stretch = 0.1
        if i == 1:
            bone.lock_ik_x = bone.lock_ik_y = bone.lock_ik_z = True
            setattr(bone, 'lock_ik_' + self.main_axis, False)

    @stage.rig_bones
    def rig_ik2_mch_chain(self):
        target_bone = self.get_ik2_target_bone()
        self.rig_ik_mch_end_bone(self.bones.mch.ik2_chain[-1], target_bone, self.bones.ctrl.ik_pole)


    ####################################################
    # Heel tracking from IK2

    @stage.generate_bones
    def make_heel_track_bones(self):
        orgs = self.bones.org.main
        mch = self.bones.mch
        mch.heel_track = self.copy_bone(orgs[2], make_derived_name(orgs[2], 'mch', '_track'))
        mch.heel_parent = self.copy_bone(orgs[2], make_derived_name(orgs[2], 'mch', '_parent'))

        # This two bone setup is used to move the damped track singularity out
        # of the way to a forbidden zone of the rig, and thus avoid flipping.
        # The bones are aligned to the center of the valid transformation zone.
        self.align_ik_control_bone(mch.heel_track)
        put_bone(self.obj, mch.heel_track, self.get_bone(orgs[2]).tail, scale=1/3)
        copy_bone_position(self.obj, mch.heel_track, mch.heel_parent, scale=3/4)

    @stage.parent_bones
    def parent_heel_control_bone(self):
        self.set_bone_parent(self.bones.ctrl.heel, self.bones.mch.heel_parent)

    @stage.parent_bones
    def parent_heel_track_bones(self):
        # Parenting heel_parent deferred to apply_bones.
        self.set_bone_parent(self.bones.mch.heel_track, self.get_ik2_target_bone())

    @stage.configure_bones
    def prerig_heel_track_bones(self):
        # Assign the constraint before the apply stage.
        self.make_constraint(
            self.bones.mch.heel_track, 'DAMPED_TRACK', self.bones.mch.ik2_chain[1],
            influence=self.params.front_paw_heel_influence
        )

    @stage.preapply_bones
    def preapply_heel_track_bones(self):
        # Assign local transform negating the effect of the constraint at rest.
        track_bone = self.get_bone(self.bones.mch.heel_track)
        bone = self.get_bone(self.bones.mch.heel_parent)
        bone.matrix_basis = track_bone.matrix.inverted() @ bone.matrix

    @stage.apply_bones
    def apply_heel_track_bones(self):
        # Complete the parent chain.
        self.set_bone_parent(self.bones.mch.heel_parent, self.bones.mch.heel_track)


    ####################################################
    # Settings

    @classmethod
    def add_parameters(self, params):
        super().add_parameters(params)

        params.front_paw_heel_influence = bpy.props.FloatProperty(
            name        = 'Heel IK Influence',
            default     = 0.8,
            min         = 0,
            max         = 1,
            description = 'Influence of the secondary IK on the heel control rotation'
        )

    @classmethod
    def parameters_ui(self, layout, params):
        r = layout.row()
        r.prop(params, "front_paw_heel_influence", slider=True)

        super().parameters_ui(layout, params)


def create_sample(obj):
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('front_thigh.L')
    bone.head = 0.0000, 0.0000, 0.6902
    bone.tail = 0.0000, 0.0916, 0.4418
    bone.roll = 0.0000
    bone.use_connect = False
    bones['front_thigh.L'] = bone.name
    bone = arm.edit_bones.new('front_shin.L')
    bone.head = 0.0000, 0.0916, 0.4418
    bone.tail = 0.0000, 0.1014, 0.1698
    bone.roll = 0.0000
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['front_thigh.L']]
    bones['front_shin.L'] = bone.name
    bone = arm.edit_bones.new('front_foot.L')
    bone.head = 0.0000, 0.1014, 0.1698
    bone.tail = 0.0000, 0.0699, 0.0411
    bone.roll = 0.0000
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['front_shin.L']]
    bones['front_foot.L'] = bone.name
    bone = arm.edit_bones.new('front_toe.L')
    bone.head = 0.0000, 0.0699, 0.0411
    bone.tail = 0.0000, -0.0540, 0.0000
    bone.roll = 3.1416
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['front_foot.L']]
    bones['front_toe.L'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['front_thigh.L']]
    pbone.rigify_type = 'limbs.front_paw'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    try:
        pbone.rigify_parameters.limb_type = "paw"
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.fk_layers = [False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.tweak_layers = [False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    pbone = obj.pose.bones[bones['front_shin.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['front_foot.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['front_toe.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    try:
        pbone.rigify_parameters.limb_type = "paw"
    except AttributeError:
        pass

    bpy.ops.object.mode_set(mode='EDIT')
    for bone in arm.edit_bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False
    for b in bones:
        bone = arm.edit_bones[bones[b]]
        bone.select = True
        bone.select_head = True
        bone.select_tail = True
        bone.bbone_x = bone.bbone_z = bone.length * 0.05
        arm.edit_bones.active = bone

    return bones
