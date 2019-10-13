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
import math

from itertools import count
from mathutils import Vector

from ...utils.rig import is_rig_base_bone
from ...utils.bones import align_chain_x_axis, align_bone_x_axis, align_bone_y_axis, align_bone_z_axis
from ...utils.bones import align_bone_to_axis, flip_bone, put_bone, align_bone_orientation
from ...utils.naming import make_derived_name
from ...utils.misc import map_list

from ..widgets import create_foot_widget, create_ballsocket_widget

from ...base_rig import stage

from .limb_rigs import BaseLimbRig


DEG_360 = math.pi * 2
ALL_TRUE = (True, True, True)


class Rig(BaseLimbRig):
    """Human leg rig."""

    def find_org_bones(self, bone):
        bones = super().find_org_bones(bone)

        for b in self.get_bone(bones.main[2]).bone.children:
            if not b.use_connect and not b.children and not is_rig_base_bone(self.obj, b.name):
                bones.heel = b.name
                break
        else:
            self.raise_error("Heel bone not found.")

        return bones

    def initialize(self):
        if len(self.bones.org.main) != 4:
            self.raise_error("Input to rig type must be a chain of 4 bones.")

        super().initialize()

    def prepare_bones(self):
        orgs = self.bones.org.main

        foot_x = self.vector_without_z(self.get_bone(orgs[2]).y_axis).cross((0, 0, -1))

        if self.params.rotation_axis == 'automatic':
            align_chain_x_axis(self.obj, orgs[0:2])

            # Orient foot and toe
            align_bone_x_axis(self.obj, orgs[2], foot_x)
            align_bone_x_axis(self.obj, orgs[3], -foot_x)

            align_bone_x_axis(self.obj, self.bones.org.heel, Vector((0, 0, 1)))

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
    # org:
    #   heel:
    #     Heel location marker bone
    # ctrl:
    #   heel:
    #     Foot roll control
    # mch:
    #   heel[]:
    #     Chain of bones implementing foot roll.
    #
    ####################################################

    ####################################################
    # IK controls

    def get_extra_ik_controls(self):
        return [self.bones.ctrl.heel]

    def make_ik_control_bone(self, orgs):
        name = self.copy_bone(orgs[2], make_derived_name(orgs[2], 'ctrl', '_ik'))

        if self.params.rotation_axis == 'automatic' or self.params.auto_align_extremity:
            align_bone_to_axis(self.obj, name, 'y', flip=True)

        else:
            flip_bone(self.obj, name)

            bone = self.get_bone(name)
            bone.tail[2] = bone.head[2]
            bone.roll = 0

        return name

    def register_switch_parents(self, pbuilder):
        super().register_switch_parents(pbuilder)

        pbuilder.register_parent(self, self.bones.org.main[2], exclude_self=True)

    def make_ik_ctrl_widget(self, ctrl):
        create_foot_widget(self.obj, ctrl)


    ####################################################
    # Heel control

    @stage.generate_bones
    def make_heel_control_bone(self):
        org = self.bones.org.main[2]
        name = self.copy_bone(org, make_derived_name(org, 'ctrl', '_heel_ik'), scale=1/2)
        self.bones.ctrl.heel = name

        self.align_roll_bone(org, name, -self.vector_without_z(self.get_bone(org).vector))

    @stage.parent_bones
    def parent_heel_control_bone(self):
        self.set_bone_parent(self.bones.ctrl.heel, self.bones.ctrl.ik)

    @stage.configure_bones
    def configure_heel_control_bone(self):
        bone = self.get_bone(self.bones.ctrl.heel)
        bone.lock_location = True, True, True

        if self.main_axis == 'x':
            bone.lock_rotation = False, False, True
        else:
            bone.lock_rotation = True, False, False

        bone.lock_scale = True, True, True

    @stage.generate_widgets
    def generate_heel_control_widget(self):
        create_ballsocket_widget(self.obj, self.bones.ctrl.heel)


    ####################################################
    # Heel roll MCH

    @stage.generate_bones
    def make_roll_mch_chain(self):
        orgs = self.bones.org.main
        self.bones.mch.heel = self.make_roll_mch_bones(orgs[2], orgs[3], self.bones.org.heel)

    def make_roll_mch_bones(self, foot, toe, heel):
        foot_bone = self.get_bone(foot)
        heel_bone = self.get_bone(heel)
        axis = -self.vector_without_z(foot_bone.vector)

        roll1 = self.copy_bone(foot, make_derived_name(heel, 'mch', '_roll1'))

        flip_bone(self.obj, roll1)
        self.align_roll_bone(foot, roll1, -foot_bone.vector)

        roll2 = self.copy_bone(toe, make_derived_name(heel, 'mch', '_roll2'), scale=1/4)

        put_bone(self.obj, roll2, (heel_bone.head + heel_bone.tail) / 2)
        self.align_roll_bone(foot, roll2, -axis)

        rock1 = self.copy_bone(heel, make_derived_name(heel, 'mch', '_rock1'))

        align_bone_to_axis(self.obj, rock1, 'y', roll=0, length=heel_bone.length/2, flip=True)
        align_bone_y_axis(self.obj, rock1, axis)

        rock2 = self.copy_bone(heel, make_derived_name(heel, 'mch', '_rock2'))

        align_bone_to_axis(self.obj, rock2, 'y', roll=0, length=heel_bone.length/2)
        align_bone_y_axis(self.obj, rock2, axis)

        return [ rock2, rock1, roll2, roll1 ]

    @stage.parent_bones
    def parent_roll_mch_chain(self):
        chain = self.bones.mch.heel
        self.set_bone_parent(chain[0], self.bones.ctrl.ik)
        self.parent_bone_chain(chain)

    @stage.rig_bones
    def rig_roll_mch_chain(self):
        self.rig_roll_mch_bones(self.bones.mch.heel, self.bones.ctrl.heel, self.bones.org.heel)

    def rig_roll_mch_bones(self, chain, heel, org_heel):
        rock2, rock1, roll2, roll1 = chain

        self.make_constraint(roll1, 'COPY_ROTATION', heel, space='LOCAL')
        self.make_constraint(roll2, 'COPY_ROTATION', heel, space='LOCAL')

        if self.main_axis == 'x':
            self.make_constraint(roll1, 'LIMIT_ROTATION', use_limit_x=True, max_x=DEG_360, space='LOCAL')
            self.make_constraint(roll2, 'LIMIT_ROTATION', use_limit_xyz=ALL_TRUE, min_x=-DEG_360, space='LOCAL')
        else:
            self.make_constraint(roll1, 'LIMIT_ROTATION', use_limit_z=True, max_z=DEG_360, space='LOCAL')
            self.make_constraint(roll2, 'LIMIT_ROTATION', use_limit_xyz=ALL_TRUE, min_z=-DEG_360, space='LOCAL')

        direction = self.get_main_axis(self.get_bone(heel)).dot(self.get_bone(org_heel).vector)

        if direction < 0:
            rock2, rock1 = rock1, rock2

        self.make_constraint(rock1, 'COPY_ROTATION', heel, space='LOCAL')
        self.make_constraint(rock2, 'COPY_ROTATION', heel, space='LOCAL')

        self.make_constraint(rock1, 'LIMIT_ROTATION', use_limit_xyz=ALL_TRUE, max_y=DEG_360, space='LOCAL')
        self.make_constraint(rock2, 'LIMIT_ROTATION', use_limit_xyz=ALL_TRUE, min_y=-DEG_360, space='LOCAL')


    ####################################################
    # FK parents MCH chain

    def parent_fk_parent_bone(self, i, parent_mch, prev_ctrl, org, prev_org):
        if i == 3:
            align_bone_orientation(self.obj, parent_mch, self.bones.mch.heel[-2])

            self.set_bone_parent(parent_mch, prev_org, use_connect=True)

        else:
            super().parent_fk_parent_bone(i, parent_mch, prev_ctrl, org, prev_org)

    def rig_fk_parent_bone(self, i, parent_mch, org):
        if i == 3:
            con = self.make_constraint(parent_mch, 'COPY_TRANSFORMS', self.bones.mch.heel[-2])

            self.make_driver(con, 'influence', variables=[(self.prop_bone, 'IK_FK')], polynomial=[1.0, -1.0])

        else:
            super().rig_fk_parent_bone(i, parent_mch, org)


    ####################################################
    # IK system MCH

    ik_input_head_tail = 1.0

    def get_ik_input_bone(self):
        return self.bones.mch.heel[-1]

    @stage.parent_bones
    def parent_ik_mch_chain(self):
        super().parent_ik_mch_chain()

        self.set_bone_parent(self.bones.mch.ik_target, self.bones.ctrl.heel)


    ####################################################
    # Settings

    @classmethod
    def parameters_ui(self, layout, params):
        super().parameters_ui(layout, params, 'Foot')


def create_sample(obj):
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('thigh.L')
    bone.head[:] = 0.0980, 0.0124, 1.0720
    bone.tail[:] = 0.0980, -0.0286, 0.5372
    bone.roll = 0.0000
    bone.use_connect = False
    bones['thigh.L'] = bone.name
    bone = arm.edit_bones.new('shin.L')
    bone.head[:] = 0.0980, -0.0286, 0.5372
    bone.tail[:] = 0.0980, 0.0162, 0.0852
    bone.roll = 0.0000
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['thigh.L']]
    bones['shin.L'] = bone.name
    bone = arm.edit_bones.new('foot.L')
    bone.head[:] = 0.0980, 0.0162, 0.0852
    bone.tail[:] = 0.0980, -0.0934, 0.0167
    bone.roll = 0.0000
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['shin.L']]
    bones['foot.L'] = bone.name
    bone = arm.edit_bones.new('toe.L')
    bone.head[:] = 0.0980, -0.0934, 0.0167
    bone.tail[:] = 0.0980, -0.1606, 0.0167
    bone.roll = -0.0000
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['foot.L']]
    bones['toe.L'] = bone.name
    bone = arm.edit_bones.new('heel.02.L')
    bone.head[:] = 0.0600, 0.0459, 0.0000
    bone.tail[:] = 0.1400, 0.0459, 0.0000
    bone.roll = 0.0000
    bone.use_connect = False
    bone.parent = arm.edit_bones[bones['foot.L']]
    bones['heel.02.L'] = bone.name


    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['thigh.L']]
    pbone.rigify_type = 'limbs.leg'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    try:
        pbone.rigify_parameters.separate_ik_layers = True
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.ik_layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.separate_hose_layers = True
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.hose_layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.limb_type = "leg"
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.fk_layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.tweak_layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
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
    pbone = obj.pose.bones[bones['heel.02.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'

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

    for eb in arm.edit_bones:
        eb.layers = (False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)

    arm.layers = (False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)

    return bones
