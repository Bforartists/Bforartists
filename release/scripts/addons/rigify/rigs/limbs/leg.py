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

from mathutils import Vector, Matrix

from ...utils.rig import is_rig_base_bone
from ...utils.bones import align_chain_x_axis, align_bone_x_axis, align_bone_z_axis
from ...utils.bones import put_bone, align_bone_orientation
from ...utils.naming import make_derived_name
from ...utils.misc import matrix_from_axis_roll, matrix_from_axis_pair
from ...utils.widgets import adjust_widget_transform_mesh

from ..widgets import create_foot_widget, create_ballsocket_widget

from ...base_rig import stage

from .limb_rigs import BaseLimbRig


DEG_360 = math.pi * 2
ALL_TRUE = (True, True, True)


class Rig(BaseLimbRig):
    """Human leg rig."""

    min_valid_orgs = max_valid_orgs = 4

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
        super().initialize()

        self.pivot_type = self.params.foot_pivot_type
        self.heel_euler_order = 'ZXY' if self.main_axis == 'x' else 'XZY'

        assert self.pivot_type in {'ANKLE', 'TOE', 'ANKLE_TOE'}

    def prepare_bones(self):
        orgs = self.bones.org.main
        foot = self.get_bone(orgs[2])

        ik_y_axis = (0, 1, 0)
        foot_y_axis = -self.vector_without_z(foot.y_axis)
        foot_x = foot_y_axis.cross((0, 0, 1))

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

        else:
            ik_y_axis = foot_y_axis

        # Orientation of the IK main and roll control bones
        self.ik_matrix = matrix_from_axis_roll(ik_y_axis, 0)
        self.roll_matrix = matrix_from_axis_pair(ik_y_axis, foot_x, self.main_axis)

    ####################################################
    # EXTRA BONES
    #
    # org:
    #   heel:
    #     Heel location marker bone
    # ctrl:
    #   ik_spin:
    #     Toe spin control.
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
        controls = super().get_extra_ik_controls() + [self.bones.ctrl.heel]
        if self.pivot_type == 'ANKLE_TOE':
            controls += [self.bones.ctrl.ik_spin]
        return controls

    def make_ik_control_bone(self, orgs):
        name = self.copy_bone(orgs[2], make_derived_name(orgs[2], 'ctrl', '_ik'))
        if self.pivot_type == 'TOE':
            put_bone(self.obj, name, self.get_bone(name).tail, matrix=self.ik_matrix)
        else:
            put_bone(self.obj, name, None, matrix=self.ik_matrix)
        return name

    def build_ik_pivot(self, ik_name, **args):
        heel_bone = self.get_bone(self.bones.org.heel)
        args = {
            'position': (heel_bone.head + heel_bone.tail)/2,
            **args
        }
        return super().build_ik_pivot(ik_name, **args)

    def register_switch_parents(self, pbuilder):
        super().register_switch_parents(pbuilder)

        pbuilder.register_parent(self, self.bones.org.main[2], exclude_self=True, tags={'limb_end'})

    def make_ik_ctrl_widget(self, ctrl):
        obj = create_foot_widget(self.obj, ctrl)

        if self.pivot_type != 'TOE':
            ctrl = self.get_bone(ctrl)
            org = self.get_bone(self.bones.org.main[2])
            offset = org.tail - (ctrl.custom_shape_transform or ctrl).head
            adjust_widget_transform_mesh(obj, Matrix.Translation(offset))

    ####################################################
    # IK pivot controls

    def get_ik_pivot_output(self):
        if self.pivot_type == 'ANKLE_TOE':
            return self.bones.ctrl.ik_spin
        else:
            return self.get_ik_control_output()

    @stage.generate_bones
    def make_ik_pivot_controls(self):
        if self.pivot_type == 'ANKLE_TOE':
            self.bones.ctrl.ik_spin = self.make_ik_spin_bone(self.bones.org.main)

    def make_ik_spin_bone(self, orgs):
        name = self.copy_bone(orgs[2], make_derived_name(orgs[2], 'ctrl', '_spin_ik'))
        put_bone(self.obj, name, self.get_bone(orgs[3]).head, matrix=self.ik_matrix, scale=0.5)
        return name

    @stage.parent_bones
    def parent_ik_pivot_controls(self):
        if self.pivot_type == 'ANKLE_TOE':
            self.set_bone_parent(self.bones.ctrl.ik_spin, self.get_ik_control_output())

    @stage.generate_widgets
    def make_ik_spin_control_widget(self):
        if self.pivot_type == 'ANKLE_TOE':
            obj = create_ballsocket_widget(self.obj, self.bones.ctrl.ik_spin, size=0.75)
            rotfix = Matrix.Rotation(math.pi/2, 4, self.main_axis.upper())
            adjust_widget_transform_mesh(obj, rotfix, local=True)

    ####################################################
    # Heel control

    @stage.generate_bones
    def make_heel_control_bone(self):
        org = self.bones.org.main[2]
        name = self.copy_bone(org, make_derived_name(org, 'ctrl', '_heel_ik'))
        put_bone(self.obj, name, None, matrix=self.roll_matrix, scale=0.5)
        self.bones.ctrl.heel = name

    @stage.parent_bones
    def parent_heel_control_bone(self):
        self.set_bone_parent(self.bones.ctrl.heel, self.get_ik_pivot_output(), inherit_scale='AVERAGE')

    @stage.configure_bones
    def configure_heel_control_bone(self):
        bone = self.get_bone(self.bones.ctrl.heel)
        bone.lock_location = True, True, True
        bone.rotation_mode = self.heel_euler_order
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

        heel_middle = (heel_bone.head + heel_bone.tail) / 2

        result = self.copy_bone(foot, make_derived_name(foot, 'mch', '_roll'), scale=0.25)

        roll1 = self.copy_bone(toe, make_derived_name(heel, 'mch', '_roll1'), scale=0.3)
        roll2 = self.copy_bone(toe, make_derived_name(heel, 'mch', '_roll2'), scale=0.3)
        rock1 = self.copy_bone(heel, make_derived_name(heel, 'mch', '_rock1'))
        rock2 = self.copy_bone(heel, make_derived_name(heel, 'mch', '_rock2'))

        put_bone(self.obj, roll1, None, matrix=self.roll_matrix)
        put_bone(self.obj, roll2, heel_middle, matrix=self.roll_matrix)
        put_bone(self.obj, rock1, heel_bone.tail, matrix=self.roll_matrix, scale=0.5)
        put_bone(self.obj, rock2, heel_bone.head, matrix=self.roll_matrix, scale=0.5)

        return [ rock2, rock1, roll2, roll1, result ]

    @stage.parent_bones
    def parent_roll_mch_chain(self):
        chain = self.bones.mch.heel
        self.set_bone_parent(chain[0], self.get_ik_pivot_output())
        self.parent_bone_chain(chain)

    @stage.rig_bones
    def rig_roll_mch_chain(self):
        self.rig_roll_mch_bones(self.bones.mch.heel, self.bones.ctrl.heel, self.bones.org.heel)

    def rig_roll_mch_bones(self, chain, heel, org_heel):
        rock2, rock1, roll2, roll1, result = chain

        # This order is required for correct working of the constraints
        for bone in chain:
            self.get_bone(bone).rotation_mode = self.heel_euler_order

        self.make_constraint(roll1, 'COPY_ROTATION', heel, space='POSE')

        if self.main_axis == 'x':
            self.make_constraint(roll2, 'COPY_ROTATION', heel, space='LOCAL', use_xyz=(True, False, False))
            self.make_constraint(roll2, 'LIMIT_ROTATION', min_x=-DEG_360, space='LOCAL')
        else:
            self.make_constraint(roll2, 'COPY_ROTATION', heel, space='LOCAL', use_xyz=(False, False, True))
            self.make_constraint(roll2, 'LIMIT_ROTATION', min_z=-DEG_360, space='LOCAL')

        direction = self.get_main_axis(self.get_bone(heel)).dot(self.get_bone(org_heel).vector)

        if direction < 0:
            rock2, rock1 = rock1, rock2

        self.make_constraint(
            rock1, 'COPY_ROTATION', heel, space='LOCAL',
            use_xyz=(False, True, False),
        )
        self.make_constraint(
            rock2, 'COPY_ROTATION', heel, space='LOCAL',
            use_xyz=(False, True, False),
        )

        self.make_constraint(rock1, 'LIMIT_ROTATION', max_y=DEG_360, space='LOCAL')
        self.make_constraint(rock2, 'LIMIT_ROTATION', min_y=-DEG_360, space='LOCAL')


    ####################################################
    # FK parents MCH chain

    def parent_fk_parent_bone(self, i, parent_mch, prev_ctrl, org, prev_org):
        if i == 3:
            align_bone_orientation(self.obj, parent_mch, self.bones.mch.heel[2])

            self.set_bone_parent(parent_mch, prev_org, use_connect=True)

        else:
            super().parent_fk_parent_bone(i, parent_mch, prev_ctrl, org, prev_org)

    def rig_fk_parent_bone(self, i, parent_mch, org):
        if i == 3:
            con = self.make_constraint(parent_mch, 'COPY_TRANSFORMS', self.bones.mch.heel[2])

            self.make_driver(con, 'influence', variables=[(self.prop_bone, 'IK_FK')], polynomial=[1.0, -1.0])

        else:
            super().rig_fk_parent_bone(i, parent_mch, org)


    ####################################################
    # IK system MCH

    def get_ik_input_bone(self):
        return self.bones.mch.heel[-1]

    @stage.parent_bones
    def parent_ik_mch_chain(self):
        super().parent_ik_mch_chain()

        self.set_bone_parent(self.bones.mch.ik_target, self.bones.mch.heel[-1])


    ####################################################
    # Settings

    @classmethod
    def add_parameters(self, params):
        super().add_parameters(params)

        items = [
            ('ANKLE', 'Ankle',
             'The foots pivots at the ankle'),
            ('TOE', 'Toe',
             'The foot pivots around the base of the toe'),
            ('ANKLE_TOE', 'Ankle and Toe',
             'The foots pivots at the ankle, with extra toe pivot'),
        ]

        params.foot_pivot_type = bpy.props.EnumProperty(
            items   = items,
            name    = "Foot Pivot",
            default = 'ANKLE_TOE'
        )

    @classmethod
    def parameters_ui(self, layout, params):
        layout.prop(params, 'foot_pivot_type')

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
