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

from ...utils.bones import compute_chain_x_axis, align_bone_x_axis, align_bone_z_axis
from ...utils.bones import align_bone_to_axis, flip_bone
from ...utils.naming import make_derived_name

from ..widgets import create_foot_widget, create_ballsocket_widget

from ...base_rig import stage

from .limb_rigs import BaseLimbRig


class Rig(BaseLimbRig):
    """Paw rig."""

    segmented_orgs = 3

    def initialize(self):
        if len(self.bones.org.main) != 4:
            self.raise_error("Input to rig type must be a chain of 4 bones.")

        super().initialize()

    def prepare_bones(self):
        orgs = self.bones.org.main

        foot_x = self.vector_without_z(self.get_bone(orgs[2]).y_axis).cross((0, 0, 1))

        if self.params.rotation_axis == 'automatic':
            axis = compute_chain_x_axis(self.obj, orgs[0:2])

            for bone in orgs:
                align_bone_x_axis(self.obj, bone, axis)

        elif self.params.auto_align_extremity:
            if self.main_axis == 'x':
                align_bone_x_axis(self.obj, orgs[2], foot_x)
                align_bone_x_axis(self.obj, orgs[3], -foot_x)
            else:
                align_bone_z_axis(self.obj, orgs[2], foot_x)
                align_bone_z_axis(self.obj, orgs[3], -foot_x)


    ####################################################
    # EXTRA BONES
    #
    # ctrl:
    #   heel:
    #     Foot heel control
    # mch:
    #   toe_socket:
    #     IK toe orientation bone.
    #
    ####################################################

    ####################################################
    # IK controls

    def get_extra_ik_controls(self):
        return super().get_extra_ik_controls() + [self.bones.ctrl.heel]

    def make_ik_control_bone(self, orgs):
        name = self.copy_bone(orgs[3], make_derived_name(orgs[2], 'ctrl', '_ik'))

        if self.params.rotation_axis == 'automatic' or self.params.auto_align_extremity:
            align_bone_to_axis(self.obj, name, 'y', flip=True)

        else:
            flip_bone(self.obj, name)

            bone = self.get_bone(name)
            bone.tail[2] = bone.head[2]
            bone.roll = 0

        vec = self.get_bone(orgs[3]).tail - self.get_bone(orgs[2]).head
        self.get_bone(name).length = self.vector_without_z(vec).length

        return name

    def register_switch_parents(self, pbuilder):
        super().register_switch_parents(pbuilder)

        pbuilder.register_parent(self, self.bones.org.main[3], exclude_self=True, tags={'limb_end'})

    def make_ik_ctrl_widget(self, ctrl):
        create_foot_widget(self.obj, ctrl)


    ####################################################
    # Heel control

    @stage.generate_bones
    def make_heel_control_bone(self):
        org = self.bones.org.main[2]
        name = self.copy_bone(org, make_derived_name(org, 'ctrl', '_heel_ik'))
        self.bones.ctrl.heel = name

        flip_bone(self.obj, name)

    @stage.parent_bones
    def parent_heel_control_bone(self):
        self.set_bone_parent(self.bones.ctrl.heel, self.get_ik_control_output())

    @stage.configure_bones
    def configure_heel_control_bone(self):
        bone = self.get_bone(self.bones.ctrl.heel)
        bone.lock_location = True, True, True
        bone.lock_scale = True, True, True

    @stage.generate_widgets
    def generate_heel_control_widget(self):
        create_ballsocket_widget(self.obj, self.bones.ctrl.heel)


    ####################################################
    # FK parents MCH chain

    @stage.generate_bones
    def make_toe_socket_bone(self):
        org = self.bones.org.main[3]
        self.bones.mch.toe_socket = self.copy_bone(org, make_derived_name(org, 'mch', '_ik_socket'))

    def parent_fk_parent_bone(self, i, parent_mch, prev_ctrl, org, prev_org):
        if i == 3:
            self.set_bone_parent(parent_mch, prev_org, use_connect=True)
            self.set_bone_parent(self.bones.mch.toe_socket, self.get_ik_control_output())

        else:
            super().parent_fk_parent_bone(i, parent_mch, prev_ctrl, org, prev_org)

    def rig_fk_parent_bone(self, i, parent_mch, org):
        if i == 3:
            con = self.make_constraint(parent_mch, 'COPY_TRANSFORMS', self.bones.mch.toe_socket)

            self.make_driver(con, 'influence', variables=[(self.prop_bone, 'IK_FK')], polynomial=[1.0, -1.0])

        else:
            super().rig_fk_parent_bone(i, parent_mch, org)


    ####################################################
    # IK system MCH

    ik_input_head_tail = 1.0

    def get_ik_input_bone(self):
        return self.bones.ctrl.heel

    @stage.parent_bones
    def parent_ik_mch_chain(self):
        super().parent_ik_mch_chain()

        self.set_bone_parent(self.bones.mch.ik_target, self.bones.ctrl.heel)


    ####################################################
    # Deform chain

    def rig_deform_bone(self, i, deform, entry, next_entry, tweak, next_tweak):
        super().rig_deform_bone(i, deform, entry, next_entry, tweak, next_tweak)

        if tweak and not (next_tweak or next_entry):
            self.make_constraint(deform, 'DAMPED_TRACK', entry.org, head_tail=1.0)
            self.make_constraint(deform, 'STRETCH_TO', entry.org, head_tail=1.0)


    ####################################################
    # Settings

    @classmethod
    def parameters_ui(self, layout, params):
        super().parameters_ui(layout, params, 'Claw')


def create_sample(obj):
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('thigh.L')
    bone.head[:] = 0.0000, 0.0017, 0.7379
    bone.tail[:] = 0.0000, -0.0690, 0.4731
    bone.roll = 0.0000
    bone.use_connect = False
    bones['thigh.L'] = bone.name
    bone = arm.edit_bones.new('shin.L')
    bone.head[:] = 0.0000, -0.0690, 0.4731
    bone.tail[:] = 0.0000, 0.1364, 0.2473
    bone.roll = 0.0000
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['thigh.L']]
    bones['shin.L'] = bone.name
    bone = arm.edit_bones.new('foot.L')
    bone.head[:] = 0.0000, 0.1364, 0.2473
    bone.tail[:] = 0.0000, 0.0736, 0.0411
    bone.roll = -0.0002
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['shin.L']]
    bones['foot.L'] = bone.name
    bone = arm.edit_bones.new('toe.L')
    bone.head[:] = 0.0000, 0.0736, 0.0411
    bone.tail[:] = 0.0000, -0.0594, 0.0000
    bone.roll = -3.1416
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['foot.L']]
    bones['toe.L'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['thigh.L']]
    pbone.rigify_type = 'limbs.paw'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    try:
        pbone.rigify_parameters.fk_layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.tweak_layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.limb_type = "paw"
    except AttributeError:
        pass
    pbone = obj.pose.bones[bones['shin.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['foot.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['toe.L']]
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
        arm.edit_bones.active = bone
