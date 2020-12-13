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
import json

from ...utils.animation import add_generic_snap_fk_to_ik, add_fk_ik_snap_buttons
from ...utils.rig import connected_children_names
from ...utils.bones import BoneDict, put_bone, align_bone_orientation, set_bone_widget_transform
from ...utils.naming import strip_org, make_derived_name
from ...utils.layers import ControlLayersOption
from ...utils.misc import pairwise_nozip, padnone, map_list
from ...utils.switch_parent import SwitchParentBuilder
from ...utils.components import CustomPivotControl

from ...base_rig import stage, BaseRig

from ...utils.widgets_basic import create_circle_widget, create_sphere_widget, create_line_widget, create_limb_widget
from ..widgets import create_gear_widget, create_ikarrow_widget

from ...rig_ui_template import UTILITIES_FUNC_COMMON_IKFK

from math import pi
from itertools import count, chain
from mathutils import Vector
from collections import namedtuple


SegmentEntry = namedtuple('SegmentEntry', ['org', 'org_idx', 'seg_idx', 'pos'])


class BaseLimbRig(BaseRig):
    """Common base for limb rigs."""

    segmented_orgs = 2 # Number of org bones to segment
    min_valid_orgs = None
    max_valid_orgs = None

    def find_org_bones(self, bone):
        return BoneDict(
            main=[bone.name] + connected_children_names(self.obj, bone.name),
        )

    def initialize(self):
        orgs = self.bones.org.main

        min_length = max(self.segmented_orgs + 1, self.min_valid_orgs or 0)
        if len(orgs) < min_length:
            self.raise_error("Input to rig type must be a chain of at least {} bones.", min_length)
        if self.max_valid_orgs and len(orgs) > self.max_valid_orgs:
            self.raise_error("Input to rig type must be a chain of at most {} bones.", self.max_valid_orgs)

        self.segments = self.params.segments
        self.bbone_segments = self.params.bbones
        self.use_ik_pivot = self.params.make_custom_pivot

        rot_axis = self.params.rotation_axis

        if rot_axis in {'x', 'automatic'}:
            self.main_axis, self.aux_axis = 'x', 'z'
        elif rot_axis == 'z':
            self.main_axis, self.aux_axis = 'z', 'x'
        else:
            self.raise_error('Unexpected axis value: {}', rot_axis)

        self.segment_table = [
            SegmentEntry(org, i, j, self.get_segment_pos(org, j))
            for i, org in enumerate(orgs[:self.segmented_orgs])
            for j in range(self.segments)
        ]
        self.segment_table_end = [
            SegmentEntry(org, i + self.segmented_orgs, None, self.get_bone(org).head)
            for i, org in enumerate(orgs[self.segmented_orgs:])
        ]

        self.segment_table_full = self.segment_table + self.segment_table_end
        self.segment_table_tweak = self.segment_table + self.segment_table_end[0:1]

    def generate_bones(self):
        bones = map_list(self.get_bone, self.bones.org.main[0:2])

        self.elbow_vector = self.compute_elbow_vector(bones)
        self.pole_angle = self.compute_pole_angle(bones, self.elbow_vector)
        self.rig_parent_bone = self.get_bone_parent(self.bones.org.main[0])


    ####################################################
    # Utilities

    def compute_elbow_vector(self, bones):
        lo_vector = bones[1].vector
        tot_vector = bones[1].tail - bones[0].head
        return (lo_vector.project(tot_vector) - lo_vector).normalized() * tot_vector.length

    def get_main_axis(self, bone):
        return getattr(bone, self.main_axis + '_axis')

    def get_aux_axis(self, bone):
        return getattr(bone, self.aux_axis + '_axis')

    def compute_pole_angle(self, bones, elbow_vector):
        if self.params.rotation_axis == 'z':
            return 0

        vector = self.get_aux_axis(bones[0]) + self.get_aux_axis(bones[1])

        if elbow_vector.angle(vector) > pi/2:
            return -pi/2
        else:
            return pi/2

    def get_segment_pos(self, org, seg):
        bone = self.get_bone(org)
        return bone.head + bone.vector * (seg / self.segments)

    @staticmethod
    def vector_without_z(vector):
        return Vector((vector[0], vector[1], 0))

    ####################################################
    # BONES
    #
    # org:
    #   main[]:
    #     Main ORG bone chain
    # ctrl:
    #   master:
    #     Main property control.
    #   fk[]:
    #     FK control chain.
    #   tweak[]:
    #     Tweak control chain.
    #   ik_base, ik_pole, ik
    #     IK controls
    #   ik_vispole
    #     IK pole visualization.
    #   ik_pivot
    #     Custom IK pivot (optional).
    # mch:
    #   master:
    #     Parent of the master control.
    #   follow:
    #     FK follow behavior.
    #   fk[]:
    #     FK chain parents (or None)
    #   ik_pivot
    #     Custom IK pivot result (optional).
    #   ik_stretch
    #     IK stretch switch implementation.
    #   ik_target
    #     Corrected target position.
    #   ik_base
    #     Optionally the base of the ik chain (otherwise ctrl.ik_base)
    #   ik_end
    #     End of the IK chain: [ik_base, ik_end]
    # deform[]:
    #   DEF bones
    #
    ####################################################

    ####################################################
    # Master control

    @stage.generate_bones
    def make_master_control(self):
        org = self.bones.org.main[0]
        self.bones.mch.master = name = self.copy_bone(org, make_derived_name(org, 'mch', '_parent_socket'), scale=1/12)
        self.get_bone(name).roll = 0
        self.bones.ctrl.master = name = self.copy_bone(org, make_derived_name(org, 'ctrl', '_parent'), scale=1/4)
        self.get_bone(name).roll = 0
        self.prop_bone = self.bones.ctrl.master

    @stage.parent_bones
    def parent_master_control(self):
        self.set_bone_parent(self.bones.ctrl.master, self.bones.mch.master)
        self.set_bone_parent(self.bones.mch.master, self.bones.mch.follow)

    @stage.configure_bones
    def configure_master_control(self):
        bone = self.get_bone(self.bones.ctrl.master)
        bone.lock_location = (True, True, True)
        bone.lock_rotation = (True, True, True)
        bone.lock_scale = (True, True, True)
        bone.lock_rotation_w = True

    @stage.rig_bones
    def rig_master_control(self):
        self.make_constraint(self.bones.mch.master, 'COPY_ROTATION', self.bones.org.main[0])

    @stage.generate_widgets
    def make_master_control_widget(self):
        create_gear_widget(self.obj, self.bones.ctrl.master, radius=1)


    ####################################################
    # FK follow MCH

    @stage.generate_bones
    def make_mch_follow_bone(self):
        org = self.bones.org.main[0]
        self.bones.mch.follow = self.copy_bone(org, make_derived_name(org, 'mch', '_parent'), scale=1/4)

    @stage.parent_bones
    def parent_mch_follow_bone(self):
        mch = self.bones.mch.follow
        align_bone_orientation(self.obj, mch, 'root')
        self.set_bone_parent(mch, self.rig_parent_bone, inherit_scale='FIX_SHEAR')

    @stage.configure_bones
    def configure_mch_follow_bone(self):
        ctrl = self.bones.ctrl
        panel = self.script.panel_with_selected_check(self, [ctrl.master, *ctrl.fk])

        self.make_property(self.prop_bone, 'FK_limb_follow', default=0.0)
        panel.custom_prop(self.prop_bone, 'FK_limb_follow', text='FK Limb Follow', slider=True)

    @stage.rig_bones
    def rig_mch_follow_bone(self):
        mch = self.bones.mch.follow

        self.make_constraint(mch, 'COPY_SCALE', 'root', use_make_uniform=True)

        con = self.make_constraint(mch, 'COPY_ROTATION', 'root')

        self.make_driver(con, 'influence', variables=[(self.prop_bone, 'FK_limb_follow')])


    ####################################################
    # FK control chain

    @stage.generate_bones
    def make_fk_control_chain(self):
        self.bones.ctrl.fk = map_list(self.make_fk_control_bone, count(0), self.bones.org.main)

    fk_name_suffix_cutoff = 2

    def get_fk_name(self, i, org, kind):
        return make_derived_name(org, kind, '_fk' if i <= self.fk_name_suffix_cutoff else '')

    def make_fk_control_bone(self, i, org):
        return self.copy_bone(org, self.get_fk_name(i, org, 'ctrl'))

    @stage.parent_bones
    def parent_fk_control_chain(self):
        fk = self.bones.ctrl.fk
        for args in zip(count(0), fk, [self.bones.mch.follow]+fk, self.bones.org.main, self.bones.mch.fk):
            self.parent_fk_control_bone(*args)

    def parent_fk_control_bone(self, i, ctrl, prev, org, parent_mch):
        if parent_mch:
            self.set_bone_parent(ctrl, parent_mch)
        else:
            self.set_bone_parent(ctrl, prev, use_connect=(i > 0))

    @stage.configure_bones
    def configure_fk_control_chain(self):
        for args in zip(count(0), self.bones.ctrl.fk, self.bones.org.main):
            self.configure_fk_control_bone(*args)

        ControlLayersOption.FK.assign_rig(self, self.bones.ctrl.fk[0:3])
        ControlLayersOption.FK.assign_rig(self, self.bones.ctrl.fk[3:], combine=True, priority=1)

    def configure_fk_control_bone(self, i, ctrl, org):
        self.copy_bone_properties(org, ctrl)

        if i == 2:
            self.get_bone(ctrl).lock_location = True, True, True

    @stage.generate_widgets
    def make_fk_control_widgets(self):
        for args in zip(count(0), self.bones.ctrl.fk):
            self.make_fk_control_widget(*args)

    def make_fk_control_widget(self, i, ctrl):
        if i < 2:
            create_limb_widget(self.obj, ctrl)
        elif i == 2:
            create_circle_widget(self.obj, ctrl, radius=0.4, head_tail=0.0)
        else:
            create_circle_widget(self.obj, ctrl, radius=0.4, head_tail=0.5)


    ####################################################
    # FK parents MCH chain

    @stage.generate_bones
    def make_fk_parent_chain(self):
        self.bones.mch.fk = map_list(self.make_fk_parent_bone, count(0), self.bones.org.main)

    def make_fk_parent_bone(self, i, org):
        if i >= 2:
            return self.copy_bone(org, self.get_fk_name(i, org, 'mch'), parent=True, scale=1/4)

    @stage.parent_bones
    def parent_fk_parent_chain(self):
        mch = self.bones.mch
        orgs = self.bones.org.main
        for args in zip(count(0), mch.fk, [mch.follow]+self.bones.ctrl.fk, orgs, [None]+orgs):
            self.parent_fk_parent_bone(*args)

    def parent_fk_parent_bone(self, i, parent_mch, prev_ctrl, org, prev_org):
        if i >= 2:
            self.set_bone_parent(parent_mch, prev_ctrl, use_connect=True, inherit_scale='NONE')

    @stage.rig_bones
    def rig_fk_parent_chain(self):
        for args in zip(count(0), self.bones.mch.fk, self.bones.org.main):
            self.rig_fk_parent_bone(*args)

    def rig_fk_parent_bone(self, i, parent_mch, org):
        if i >= 2:
            self.make_constraint(parent_mch, 'COPY_SCALE', 'root', use_make_uniform=True)


    ####################################################
    # IK controls

    def get_extra_ik_controls(self):
        if self.component_ik_pivot:
            return [self.component_ik_pivot.control]
        else:
            return []

    def get_middle_ik_controls(self):
        return []

    def get_ik_fk_position_chains(self):
        ik_chain = self.get_ik_output_chain()
        return ik_chain, self.bones.ctrl.fk[0:len(ik_chain)]

    def get_ik_control_chain(self):
        ctrl = self.bones.ctrl
        return [ctrl.ik_base, ctrl.ik_pole, *self.get_middle_ik_controls(), ctrl.ik]

    def get_all_ik_controls(self):
        return self.get_ik_control_chain() + self.get_extra_ik_controls()

    @stage.generate_bones
    def make_ik_controls(self):
        orgs = self.bones.org.main

        self.bones.ctrl.ik_base = self.make_ik_base_bone(orgs)
        self.bones.ctrl.ik_pole = self.make_ik_pole_bone(orgs)
        self.bones.ctrl.ik = ik_name = self.make_ik_control_bone(orgs)

        self.component_ik_pivot = self.build_ik_pivot(ik_name)
        self.build_ik_parent_switch(SwitchParentBuilder(self.generator))

    def make_ik_base_bone(self, orgs):
        return self.copy_bone(orgs[0], make_derived_name(orgs[0], 'ctrl', '_ik'))

    def make_ik_pole_bone(self, orgs):
        name = self.copy_bone(orgs[0], make_derived_name(orgs[0], 'ctrl', '_ik_target'))

        pole = self.get_bone(name)
        pole.head = self.get_bone(orgs[0]).tail + self.elbow_vector
        pole.tail = pole.head - self.elbow_vector/8
        pole.roll = 0

        return name

    def make_ik_control_bone(self, orgs):
        return self.copy_bone(orgs[2], make_derived_name(orgs[2], 'ctrl', '_ik'))

    def build_ik_pivot(self, ik_name, **args):
        if self.use_ik_pivot:
            return CustomPivotControl(self, 'ik_pivot', ik_name, parent=ik_name, **args)

    def get_ik_control_output(self):
        if self.component_ik_pivot:
            return self.component_ik_pivot.output
        else:
            return self.bones.ctrl.ik

    def get_ik_pole_parents(self):
        return [(self.bones.mch.ik_target, self.bones.ctrl.ik)]

    def register_switch_parents(self, pbuilder):
        if self.rig_parent_bone:
            pbuilder.register_parent(self, self.rig_parent_bone)

        pbuilder.register_parent(
            self, self.get_ik_control_output, name=self.bones.ctrl.ik,
            exclude_self=True, tags={'limb_ik', 'child'},
        )

    def build_ik_parent_switch(self, pbuilder):
        ctrl = self.bones.ctrl

        master = lambda: self.bones.ctrl.master
        pcontrols = lambda: [ ctrl.master ] + self.get_all_ik_controls()

        self.register_switch_parents(pbuilder)

        pbuilder.build_child(
            self, ctrl.ik, prop_bone=master, select_parent='root',
            prop_id='IK_parent', prop_name='IK Parent', controls=pcontrols,
        )

        pbuilder.build_child(
            self, ctrl.ik_pole, prop_bone=master, extra_parents=self.get_ik_pole_parents,
            prop_id='pole_parent', prop_name='Pole Parent', controls=pcontrols,
            no_fix_rotation=True, no_fix_scale=True,
        )

    @stage.parent_bones
    def parent_ik_controls(self):
        self.set_bone_parent(self.bones.ctrl.ik_base, self.bones.mch.follow)

    @stage.configure_bones
    def configure_ik_controls(self):
        base = self.get_bone(self.bones.ctrl.ik_base)
        base.rotation_mode = 'ZXY'
        base.lock_rotation = True, False, True

    @stage.rig_bones
    def rig_ik_controls(self):
        self.rig_hide_pole_control(self.bones.ctrl.ik_pole)

    @stage.generate_widgets
    def make_ik_control_widgets(self):
        ctrl = self.bones.ctrl

        set_bone_widget_transform(self.obj, ctrl.ik, self.get_ik_control_output())

        if self.use_mch_ik_base:
            set_bone_widget_transform(self.obj, ctrl.ik_base, self.bones.mch.ik_base, target_size=True)

        self.make_ik_base_widget(ctrl.ik_base)
        self.make_ik_pole_widget(ctrl.ik_pole)
        self.make_ik_ctrl_widget(ctrl.ik)

    def make_ik_base_widget(self, ctrl):
        if self.main_axis == 'x':
            roll = 0
        else:
            roll = pi/2

        create_ikarrow_widget(self.obj, ctrl, roll=roll)

    def make_ik_pole_widget(self, ctrl):
        create_sphere_widget(self.obj, ctrl)

    def make_ik_ctrl_widget(self, ctrl):
        raise NotImplementedError()


    ####################################################
    # IK pole visualization

    @stage.generate_bones
    def make_ik_vispole_bone(self):
        orgs = self.bones.org.main
        name = self.copy_bone(orgs[1], 'VIS_'+make_derived_name(orgs[0], 'ctrl', '_ik_pole'))
        self.bones.ctrl.ik_vispole = name

        bone = self.get_bone(name)
        bone.tail = bone.head + Vector((0, 0, bone.length / 10))
        bone.hide_select = True

    @stage.rig_bones
    def rig_ik_vispole_bone(self):
        name = self.bones.ctrl.ik_vispole

        self.make_constraint(name, 'COPY_LOCATION', self.bones.org.main[1])
        self.make_constraint(
            name, 'STRETCH_TO', self.bones.ctrl.ik_pole,
            volume='NO_VOLUME', rest_length=self.get_bone(name).length
        )

        self.rig_hide_pole_control(name)

    @stage.generate_widgets
    def make_ik_vispole_widget(self):
        create_line_widget(self.obj, self.bones.ctrl.ik_vispole)


    ####################################################
    # IK system MCH

    ik_input_head_tail = 0.0

    use_mch_ik_base = False

    def get_ik_input_bone(self):
        return self.get_ik_control_output()

    def get_ik_chain_base(self):
        return self.bones.mch.ik_base if self.use_mch_ik_base else self.bones.ctrl.ik_base

    def get_ik_output_chain(self):
        return [self.get_ik_chain_base(), self.bones.mch.ik_end, self.bones.mch.ik_target]

    @stage.generate_bones
    def make_ik_mch_chain(self):
        orgs = self.bones.org.main

        if self.use_mch_ik_base:
            self.bones.mch.ik_base = self.make_ik_mch_base_bone(orgs)

        self.bones.mch.ik_stretch = self.make_ik_mch_stretch_bone(orgs)
        self.bones.mch.ik_target = self.make_ik_mch_target_bone(orgs)
        self.bones.mch.ik_end = self.copy_bone(orgs[1], make_derived_name(orgs[1], 'mch', '_ik'))

    def make_ik_mch_base_bone(self, orgs):
        return self.copy_bone(orgs[0], make_derived_name(orgs[0], 'mch', '_ik'))

    def make_ik_mch_stretch_bone(self, orgs):
        name = self.copy_bone(orgs[0], make_derived_name(orgs[0], 'mch', '_ik_stretch'))
        self.get_bone(name).tail = self.get_bone(orgs[2]).head
        return name

    def make_ik_mch_target_bone(self, orgs):
        return self.copy_bone(orgs[2], make_derived_name(orgs[0], 'mch', '_ik_target'))

    @stage.parent_bones
    def parent_ik_mch_chain(self):
        if self.use_mch_ik_base:
            self.set_bone_parent(self.bones.mch.ik_base, self.bones.ctrl.ik_base, inherit_scale='AVERAGE')
        self.set_bone_parent(self.bones.mch.ik_stretch, self.bones.mch.follow)
        self.set_bone_parent(self.bones.mch.ik_target, self.get_ik_input_bone())
        self.set_bone_parent(self.bones.mch.ik_end, self.get_ik_chain_base())

    @stage.configure_bones
    def configure_ik_mch_chain(self):
        bone = self.get_bone(self.get_ik_chain_base())
        bone.ik_stretch = 0.1

        bone = self.get_bone(self.bones.mch.ik_end)
        bone.ik_stretch = 0.1
        bone.lock_ik_x = bone.lock_ik_y = bone.lock_ik_z = True
        setattr(bone, 'lock_ik_' + self.main_axis, False)

    @stage.configure_bones
    def configure_ik_mch_panel(self):
        ctrl = self.bones.ctrl
        panel = self.script.panel_with_selected_check(self, ctrl.flatten())

        rig_name = strip_org(self.bones.org.main[2])

        self.make_property(self.prop_bone, 'IK_FK', default=0.0, description='IK/FK Switch')
        panel.custom_prop(self.prop_bone, 'IK_FK', text='IK-FK ({})'.format(rig_name), slider=True)

        self.add_global_buttons(panel, rig_name)

        panel = self.script.panel_with_selected_check(self, [ctrl.master, *self.get_all_ik_controls()])

        self.make_property(self.prop_bone, 'IK_Stretch', default=1.0, description='IK Stretch')
        panel.custom_prop(self.prop_bone, 'IK_Stretch', text='IK Stretch', slider=True)

        self.make_property(self.prop_bone, 'pole_vector', default=False, description='Use a pole target control')

        self.add_ik_only_buttons(panel, rig_name)

    def add_global_buttons(self, panel, rig_name):
        ctrl = self.bones.ctrl
        ik_chain = self.get_ik_output_chain()
        fk_chain = ctrl.fk[0:len(ik_chain)]

        add_generic_snap_fk_to_ik(
            panel,
            fk_bones=fk_chain, ik_bones=ik_chain,
            ik_ctrl_bones=self.get_all_ik_controls(),
            rig_name=rig_name
        )

        ik_chain, fk_chain = self.get_ik_fk_position_chains()

        add_limb_snap_ik_to_fk(
            panel,
            master=ctrl.master,
            fk_bones=fk_chain, ik_bones=ik_chain,
            ik_ctrl_bones=self.get_ik_control_chain(),
            ik_extra_ctrls=self.get_extra_ik_controls(),
            rig_name=rig_name
        )

    def add_ik_only_buttons(self, panel, rig_name):
        ctrl = self.bones.ctrl
        ik_chain, fk_chain = self.get_ik_fk_position_chains()

        add_limb_toggle_pole(
            panel, master=ctrl.master,
            ik_bones=ik_chain,
            ik_ctrl_bones=self.get_ik_control_chain(),
            ik_extra_ctrls=self.get_extra_ik_controls(),
        )

    @stage.rig_bones
    def rig_ik_mch_chain(self):
        mch = self.bones.mch
        input_bone = self.get_ik_input_bone()

        self.rig_ik_mch_stretch_bones(mch.ik_target, mch.ik_stretch, input_bone, self.ik_input_head_tail, 2)
        self.rig_ik_mch_end_bone(mch.ik_end, mch.ik_target, self.bones.ctrl.ik_pole)

    def rig_ik_mch_stretch_bones(self, mch_target, mch_stretch, input_bone, head_tail, org_count, bias=1.035):
        # Compute increase in length to fully straighten
        orgs = self.bones.org.main[0:org_count]
        len_cur = (self.get_bone(orgs[-1]).tail - self.get_bone(orgs[0]).head).length
        len_full = sum(self.get_bone(org).length for org in orgs)
        len_scale = len_full / len_cur

        # Limited stretch on the stretch bone
        self.make_constraint(mch_stretch, 'STRETCH_TO', input_bone, head_tail=head_tail, keep_axis='SWING_Y')

        con = self.make_constraint(mch_stretch, 'LIMIT_SCALE', min_y=0.0, max_y=len_scale*bias, owner_space='LOCAL')

        self.make_driver(con, "influence", variables=[(self.prop_bone, 'IK_Stretch')], polynomial=[1.0, -1.0])

        # Snap the target to the end of the stretch bone
        self.make_constraint(mch_target, 'COPY_LOCATION', mch_stretch, head_tail=1.0)

    def rig_ik_mch_end_bone(self, mch_ik, mch_target, ctrl_pole, chain=2):
        con = self.make_constraint(
            mch_ik, 'IK', mch_target, chain_count=chain,
        )

        self.make_driver(con, "mute", variables=[(self.prop_bone, 'pole_vector')], polynomial=[0.0, 1.0])

        con_pole = self.make_constraint(
            mch_ik, 'IK', mch_target, chain_count=chain,
            pole_target=self.obj, pole_subtarget=ctrl_pole, pole_angle=self.pole_angle,
        )

        self.make_driver(con_pole, "mute", variables=[(self.prop_bone, 'pole_vector')], polynomial=[1.0, -1.0])

    def rig_hide_pole_control(self, name):
        self.make_driver(
            self.get_bone(name).bone, "hide",
            variables=[(self.prop_bone, 'pole_vector')], polynomial=[1.0, -1.0],
        )


    ####################################################
    # ORG chain

    @stage.parent_bones
    def parent_org_chain(self):
        orgs = self.bones.org.main
        if len(orgs) > 3:
            self.get_bone(orgs[3]).use_connect = False

    @stage.rig_bones
    def rig_org_chain(self):
        ik = self.get_ik_output_chain()
        for args in zip(count(0), self.bones.org.main, self.bones.ctrl.fk, padnone(ik)):
            self.rig_org_bone(*args)

    def rig_org_bone(self, i, org, fk, ik):
        self.make_constraint(org, 'COPY_TRANSFORMS', fk)

        if ik:
            con = self.make_constraint(org, 'COPY_TRANSFORMS', ik)

            self.make_driver(con, 'influence', variables=[(self.prop_bone, 'IK_FK')], polynomial=[1.0, -1.0])


    ####################################################
    # Tweak control chain

    @stage.generate_bones
    def make_tweak_chain(self):
        self.bones.ctrl.tweak = map_list(self.make_tweak_bone, count(0), self.segment_table_tweak)

    def make_tweak_bone(self, i, entry):
        name = make_derived_name(entry.org, 'ctrl', '_tweak')
        name = self.copy_bone(entry.org, name, scale=1/(2 * self.segments))
        put_bone(self.obj, name, entry.pos)
        return name

    @stage.parent_bones
    def parent_tweak_chain(self):
        for ctrl, mch in zip(self.bones.ctrl.tweak, self.bones.mch.tweak):
            self.set_bone_parent(ctrl, mch)

    @stage.configure_bones
    def configure_tweak_chain(self):
        for args in zip(count(0), self.bones.ctrl.tweak, self.segment_table_tweak):
            self.configure_tweak_bone(*args)

        ControlLayersOption.TWEAK.assign_rig(self, self.bones.ctrl.tweak)

    def configure_tweak_bone(self, i, tweak, entry):
        tweak_pb = self.get_bone(tweak)
        tweak_pb.lock_rotation = (True, False, True)
        tweak_pb.lock_scale = (False, True, False)
        tweak_pb.rotation_mode = 'ZXY'

        if i > 0 and entry.seg_idx is not None:
            self.make_rubber_tweak_property(i, tweak, entry)

    def make_rubber_tweak_property(self, i, tweak, entry):
        defval = 1.0 if entry.seg_idx else 0.0
        text = 'Rubber Tweak ({})'.format(strip_org(entry.org))

        self.make_property(tweak, 'rubber_tweak', defval, max=2.0, soft_max=1.0)

        panel = self.script.panel_with_selected_check(self, [tweak])
        panel.custom_prop(tweak, 'rubber_tweak', text=text, slider=True)

    @stage.generate_widgets
    def make_tweak_widgets(self):
        for tweak in self.bones.ctrl.tweak:
            self.make_tweak_widget(tweak)

    def make_tweak_widget(self, tweak):
        create_sphere_widget(self.obj, tweak)


    ####################################################
    # Tweak MCH chain

    @stage.generate_bones
    def make_tweak_mch_chain(self):
        self.bones.mch.tweak = map_list(self.make_tweak_mch_bone, count(0), self.segment_table_tweak)

    def make_tweak_mch_bone(self, i, entry):
        name = make_derived_name(entry.org, 'mch', '_tweak')
        name = self.copy_bone(entry.org, name, scale=1/(4 * self.segments))
        put_bone(self.obj, name, entry.pos)
        return name

    @stage.parent_bones
    def parent_tweak_mch_chain(self):
        for args in zip(count(0), self.bones.mch.tweak, self.segment_table_tweak):
            self.parent_tweak_mch_bone(*args)

    def parent_tweak_mch_bone(self, i, mch, entry):
        if i == 0:
            self.set_bone_parent(mch, self.rig_parent_bone, inherit_scale='FIX_SHEAR')
        else:
            self.set_bone_parent(mch, entry.org)

    @stage.rig_bones
    def rig_tweak_mch_chain(self):
        for args in zip(count(0), self.bones.mch.tweak, self.segment_table_tweak):
            self.rig_tweak_mch_bone(*args)

    def rig_tweak_mch_bone(self, i, tweak, entry):
        if entry.seg_idx:
            tweaks = self.bones.ctrl.tweak
            prev_tweak = tweaks[i - entry.seg_idx]
            next_tweak = tweaks[i + self.segments - entry.seg_idx]

            self.make_constraint(tweak, 'COPY_TRANSFORMS', prev_tweak)
            self.make_constraint(
                tweak, 'COPY_TRANSFORMS', next_tweak,
                influence = entry.seg_idx / self.segments
            )
            self.make_constraint(tweak, 'DAMPED_TRACK', next_tweak)

        elif entry.seg_idx is not None:
            self.make_constraint(tweak, 'COPY_SCALE', 'root', use_make_uniform=True)

        if i == 0:
            self.make_constraint(tweak, 'COPY_LOCATION', entry.org)
            self.make_constraint(tweak, 'DAMPED_TRACK', entry.org, head_tail=1)


    ####################################################
    # Deform chain

    @stage.generate_bones
    def make_deform_chain(self):
        self.bones.deform = map_list(self.make_deform_bone, count(0), self.segment_table_full)

    def make_deform_bone(self, i, entry):
        name = make_derived_name(entry.org, 'def')

        if entry.seg_idx is None:
            name = self.copy_bone(entry.org, name)
        else:
            name = self.copy_bone(entry.org, name, bbone=True, scale=1/self.segments)
            put_bone(self.obj, name, entry.pos)
            self.get_bone(name).bbone_segments = self.bbone_segments

        return name

    @stage.parent_bones
    def parent_deform_chain(self):
        self.set_bone_parent(self.bones.deform[0], self.rig_parent_bone)
        self.parent_bone_chain(self.bones.deform, use_connect=True)

    @stage.rig_bones
    def rig_deform_chain(self):
        tweaks = pairwise_nozip(padnone(self.bones.ctrl.tweak))
        entries = pairwise_nozip(padnone(self.segment_table_full))

        for args in zip(count(0), self.bones.deform, *entries, *tweaks):
            self.rig_deform_bone(*args)

    def rig_deform_bone(self, i, deform, entry, next_entry, tweak, next_tweak):
        if tweak:
            self.make_constraint(deform, 'COPY_TRANSFORMS', tweak)

            if next_tweak:
                self.make_constraint(deform, 'STRETCH_TO', next_tweak, keep_axis='SWING_Y')

                self.rig_deform_easing(i, deform, tweak, next_tweak)

            elif next_entry:
                self.make_constraint(deform, 'STRETCH_TO', next_entry.org, keep_axis='SWING_Y')

        else:
            self.make_constraint(deform, 'COPY_TRANSFORMS', entry.org)

    def rig_deform_easing(self, i, deform, tweak, next_tweak):
        pbone = self.get_bone(deform)

        if 'rubber_tweak' in self.get_bone(tweak):
            self.make_driver(pbone.bone, 'bbone_easein', variables=[(tweak, 'rubber_tweak')])
        else:
            pbone.bone.bbone_easein = 0.0

        if 'rubber_tweak' in self.get_bone(next_tweak):
            self.make_driver(pbone.bone, 'bbone_easeout', variables=[(next_tweak, 'rubber_tweak')])
        else:
            pbone.bone.bbone_easeout = 0.0


    ####################################################
    # Settings

    @classmethod
    def add_parameters(self, params):
        """ Add the parameters of this rig type to the
            RigifyParameters PropertyGroup
        """

        items = [
            ('x', 'X manual', ''),
            ('z', 'Z manual', ''),
            ('automatic', 'Automatic', '')
        ]

        params.rotation_axis = bpy.props.EnumProperty(
            items   = items,
            name    = "Rotation Axis",
            default = 'automatic'
        )

        params.auto_align_extremity = bpy.props.BoolProperty(
            name='auto_align_extremity',
            default=False,
            description="Auto Align Extremity Bone"
        )

        params.segments = bpy.props.IntProperty(
            name        = 'Limb Segments',
            default     = 2,
            min         = 1,
            description = 'Number of limb segments'
        )

        params.bbones = bpy.props.IntProperty(
            name        = 'B-Bone Segments',
            default     = 10,
            min         = 1,
            description = 'Number of B-Bone segments'
        )

        params.make_custom_pivot = bpy.props.BoolProperty(
            name        = "Custom Pivot Control",
            default     = False,
            description = "Create a rotation pivot control that can be repositioned arbitrarily"
        )

        # Setting up extra layers for the FK and tweak
        ControlLayersOption.FK.add_parameters(params)
        ControlLayersOption.TWEAK.add_parameters(params)

    @classmethod
    def parameters_ui(self, layout, params, end='End'):
        """ Create the ui for the rig parameters."""

        r = layout.row()
        r.prop(params, "rotation_axis")

        if 'auto' not in params.rotation_axis.lower():
            r = layout.row()
            r.prop(params, "auto_align_extremity", text="Auto Align "+end)

        r = layout.row()
        r.prop(params, "segments")

        r = layout.row()
        r.prop(params, "bbones")

        layout.prop(params, 'make_custom_pivot', text="Custom IK Pivot")

        ControlLayersOption.FK.parameters_ui(layout, params)
        ControlLayersOption.TWEAK.parameters_ui(layout, params)


###########################
# Limb IK to FK operator ##
###########################

SCRIPT_REGISTER_OP_SNAP_IK_FK = ['POSE_OT_rigify_limb_ik2fk', 'POSE_OT_rigify_limb_ik2fk_bake']

SCRIPT_UTILITIES_OP_SNAP_IK_FK = UTILITIES_FUNC_COMMON_IKFK + ['''
########################
## Limb Snap IK to FK ##
########################

class RigifyLimbIk2FkBase:
    prop_bone:    StringProperty(name="Settings Bone")
    pole_prop:    StringProperty(name="Pole target switch", default="pole_vector")
    fk_bones:     StringProperty(name="FK Bone Chain")
    ik_bones:     StringProperty(name="IK Result Bone Chain")
    ctrl_bones:   StringProperty(name="IK Controls")
    extra_ctrls:  StringProperty(name="Extra IK Controls")

    def init_execute(self, context):
        if self.fk_bones:
            self.fk_bone_list = json.loads(self.fk_bones)
        self.ik_bone_list = json.loads(self.ik_bones)
        self.ctrl_bone_list = json.loads(self.ctrl_bones)
        self.extra_ctrl_list = json.loads(self.extra_ctrls)

    def get_use_pole(self, obj):
        bone = obj.pose.bones[self.prop_bone]
        return self.pole_prop in bone and bone[self.pole_prop]

    def save_frame_state(self, context, obj):
        return get_chain_transform_matrices(obj, self.fk_bone_list)

    def compute_base_rotation(self, context, ik_bones, ctrl_bones, matrices, use_pole):
        context.view_layer.update()

        if use_pole:
            match_pole_target(
                context.view_layer,
                ik_bones[0], ik_bones[1], ctrl_bones[1], matrices[0],
                (ik_bones[0].length + ik_bones[1].length)
            )

        else:
            correct_rotation(context.view_layer, ik_bones[0], matrices[0], ctrl_ik=ctrl_bones[0])

    def assign_middle_controls(self, context, obj, matrices, ik_bones, ctrl_bones, *, lock=False, keyflags=None):
        for mat, ik, ctrl in reversed(list(zip(matrices[2:-1], ik_bones[2:-1], ctrl_bones[2:-1]))):
            ctrl.bone.use_inherit_rotation = not lock
            ctrl.bone.inherit_scale = 'NONE' if lock else 'FULL'
            context.view_layer.update()
            mat = convert_pose_matrix_via_rest_delta(mat, ik, ctrl)
            set_transform_from_matrix(obj, ctrl.name, mat, keyflags=keyflags)

    def apply_frame_state(self, context, obj, matrices):
        ik_bones = [ obj.pose.bones[k] for k in self.ik_bone_list ]
        ctrl_bones = [ obj.pose.bones[k] for k in self.ctrl_bone_list ]

        use_pole = self.get_use_pole(obj)

        # Set the end control position
        endmat = convert_pose_matrix_via_rest_delta(matrices[-1], ik_bones[-1], ctrl_bones[-1])

        set_transform_from_matrix(
            obj, self.ctrl_bone_list[-1], endmat, keyflags=self.keyflags
        )

        # Remove foot heel transform, if present
        for extra in self.extra_ctrl_list:
            set_transform_from_matrix(
                obj, extra, Matrix.Identity(4), space='LOCAL', keyflags=self.keyflags
            )

        # Set the base bone position
        ctrl_bones[0].matrix_basis = Matrix.Identity(4)

        set_transform_from_matrix(
            obj, self.ctrl_bone_list[0], matrices[0],
            no_scale=True, no_rot=use_pole,
        )

        # Lock middle control transforms (first pass)
        self.assign_middle_controls(context, obj, matrices, ik_bones, ctrl_bones, lock=True)

        # Adjust the base bone state
        self.compute_base_rotation(context, ik_bones, ctrl_bones, matrices, use_pole)

        correct_scale(context.view_layer, ik_bones[0], matrices[0], ctrl_ik=ctrl_bones[0])

        # Assign middle control transforms (final pass)
        self.assign_middle_controls(context, obj, matrices, ik_bones, ctrl_bones, keyflags=self.keyflags)

        # Keyframe controls
        if self.keyflags is not None:
            if use_pole:
                keyframe_transform_properties(
                    obj, self.ctrl_bone_list[1], self.keyflags,
                    no_rot=True, no_scale=True,
                )

            keyframe_transform_properties(
                obj, self.ctrl_bone_list[0], self.keyflags,
                no_rot=use_pole,
            )

class POSE_OT_rigify_limb_ik2fk(RigifyLimbIk2FkBase, RigifySingleUpdateMixin, bpy.types.Operator):
    bl_idname = "pose.rigify_limb_ik2fk_" + rig_id
    bl_label = "Snap IK->FK"
    bl_description = "Snap the IK chain to FK result"

class POSE_OT_rigify_limb_ik2fk_bake(RigifyLimbIk2FkBase, RigifyBakeKeyframesMixin, bpy.types.Operator):
    bl_idname = "pose.rigify_limb_ik2fk_bake_" + rig_id
    bl_label = "Apply Snap IK->FK To Keyframes"
    bl_description = "Snap the IK chain keyframes to FK result"

    def execute_scan_curves(self, context, obj):
        self.bake_add_bone_frames(self.fk_bone_list, TRANSFORM_PROPS_ALL)
        return self.bake_get_all_bone_curves(self.ctrl_bone_list + self.extra_ctrl_list, TRANSFORM_PROPS_ALL)
''']

def add_limb_snap_ik_to_fk(panel, *, master=None, fk_bones=[], ik_bones=[], ik_ctrl_bones=[], ik_extra_ctrls=[], rig_name=''):
    panel.use_bake_settings()
    panel.script.add_utilities(SCRIPT_UTILITIES_OP_SNAP_IK_FK)
    panel.script.register_classes(SCRIPT_REGISTER_OP_SNAP_IK_FK)

    op_props = {
        'prop_bone': master,
        'fk_bones': json.dumps(fk_bones),
        'ik_bones': json.dumps(ik_bones),
        'ctrl_bones': json.dumps(ik_ctrl_bones),
        'extra_ctrls': json.dumps(ik_extra_ctrls),
    }

    add_fk_ik_snap_buttons(
        panel, 'pose.rigify_limb_ik2fk_{rig_id}', 'pose.rigify_limb_ik2fk_bake_{rig_id}',
        label='IK->FK', rig_name=rig_name, properties=op_props,
        clear_bones=ik_ctrl_bones + ik_extra_ctrls,
    )

#########################
# Toggle Pole operator ##
#########################

SCRIPT_REGISTER_OP_TOGGLE_POLE = ['POSE_OT_rigify_limb_toggle_pole', 'POSE_OT_rigify_limb_toggle_pole_bake']

SCRIPT_UTILITIES_OP_TOGGLE_POLE = SCRIPT_UTILITIES_OP_SNAP_IK_FK + ['''
####################
## Toggle IK Pole ##
####################

class RigifyLimbTogglePoleBase(RigifyLimbIk2FkBase):
    use_pole: bpy.props.BoolProperty(name="Use Pole Vector")

    def save_frame_state(self, context, obj):
        return get_chain_transform_matrices(obj, self.ik_bone_list)

    def apply_frame_state(self, context, obj, matrices):
        ik_bones = [ obj.pose.bones[k] for k in self.ik_bone_list ]
        ctrl_bones = [ obj.pose.bones[k] for k in self.ctrl_bone_list ]

        # Set the pole property
        set_custom_property_value(
            obj, self.prop_bone, self.pole_prop, int(self.use_pole),
            keyflags=self.keyflags_switch
        )

        # Lock middle control transforms
        self.assign_middle_controls(context, obj, matrices, ik_bones, ctrl_bones, lock=True)

        # Reset the base bone rotation
        set_pose_rotation(ctrl_bones[0], Matrix.Identity(4))

        self.compute_base_rotation(context, ik_bones, ctrl_bones, matrices, self.use_pole)

        # Assign middle control transforms (final pass)
        self.assign_middle_controls(context, obj, matrices, ik_bones, ctrl_bones, keyflags=self.keyflags)

        # Keyframe controls
        if self.keyflags is not None:
            if self.use_pole:
                keyframe_transform_properties(
                    obj, self.ctrl_bone_list[2], self.keyflags,
                    no_rot=True, no_scale=True,
                )
            else:
                keyframe_transform_properties(
                    obj, self.ctrl_bone_list[0], self.keyflags,
                    no_loc=True, no_scale=True,
                )

    def init_invoke(self, context):
        self.use_pole = not bool(context.active_object.pose.bones[self.prop_bone][self.pole_prop])

class POSE_OT_rigify_limb_toggle_pole(RigifyLimbTogglePoleBase, RigifySingleUpdateMixin, bpy.types.Operator):
    bl_idname = "pose.rigify_limb_toggle_pole_" + rig_id
    bl_label = "Toggle Pole"
    bl_description = "Switch the IK chain between pole and rotation"

class POSE_OT_rigify_limb_toggle_pole_bake(RigifyLimbTogglePoleBase, RigifyBakeKeyframesMixin, bpy.types.Operator):
    bl_idname = "pose.rigify_limb_toggle_pole_bake_" + rig_id
    bl_label = "Apply Toggle Pole To Keyframes"
    bl_description = "Switch the IK chain between pole and rotation over a frame range"

    def execute_scan_curves(self, context, obj):
        self.bake_add_bone_frames(self.ctrl_bone_list, TRANSFORM_PROPS_ALL)

        rot_curves = self.bake_get_all_bone_curves(self.ctrl_bone_list[0], TRANSFORM_PROPS_ROTATION)
        pole_curves = self.bake_get_all_bone_curves(self.ctrl_bone_list[2], TRANSFORM_PROPS_LOCATION)
        return rot_curves + pole_curves

    def execute_before_apply(self, context, obj, range, range_raw):
        self.bake_replace_custom_prop_keys_constant(self.prop_bone, self.pole_prop, int(self.use_pole))

    def draw(self, context):
        self.layout.prop(self, 'use_pole')
''']

def add_limb_toggle_pole(panel, *, master=None, ik_bones=[], ik_ctrl_bones=[], ik_extra_ctrls=[]):
    panel.use_bake_settings()
    panel.script.add_utilities(SCRIPT_UTILITIES_OP_TOGGLE_POLE)
    panel.script.register_classes(SCRIPT_REGISTER_OP_TOGGLE_POLE)

    op_props = {
        'prop_bone': master,
        'ik_bones': json.dumps(ik_bones),
        'ctrl_bones': json.dumps(ik_ctrl_bones),
        'extra_ctrls': json.dumps(ik_extra_ctrls),
    }

    row = panel.row(align=True)
    lsplit = row.split(factor=0.75, align=True)
    lsplit.operator('pose.rigify_limb_toggle_pole_{rig_id}', icon='FORCE_MAGNETIC', properties=op_props)
    lsplit.custom_prop(master, 'pole_vector', text='')
    row.operator('pose.rigify_limb_toggle_pole_bake_{rig_id}', text='', icon='ACTION_TWEAK', properties=op_props)
