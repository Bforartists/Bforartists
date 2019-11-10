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
import re

from itertools import count

from ...utils.errors import MetarigError
from ...utils.bones import put_bone, flip_bone, align_chain_x_axis, set_bone_widget_transform
from ...utils.naming import make_derived_name
from ...utils.widgets import create_widget
from ...utils.widgets_basic import create_circle_widget
from ...utils.misc import map_list
from ...utils.layers import ControlLayersOption

from ...base_rig import stage

from ..chain_rigs import SimpleChainRig


class Rig(SimpleChainRig):
    """A finger rig with master control."""
    def initialize(self):
        super().initialize()

        self.bbone_segments = self.params.bbones
        self.first_parent = self.get_bone_parent(self.bones.org[0])

    def prepare_bones(self):
        if self.params.primary_rotation_axis == 'automatic':
            align_chain_x_axis(self.obj, self.bones.org)

    ##############################
    # Master Control

    @stage.generate_bones
    def make_master_control(self):
        orgs = self.bones.org
        name = self.copy_bone(orgs[0], make_derived_name(orgs[0], 'ctrl', '_master'), parent=True)
        self.bones.ctrl.master = name

        first_bone = self.get_bone(orgs[0])
        last_bone = self.get_bone(orgs[-1])
        self.get_bone(name).tail += (last_bone.tail - first_bone.head) * 1.25

    @stage.configure_bones
    def configure_master_control(self):
        master = self.bones.ctrl.master

        bone = self.get_bone(master)
        bone.lock_scale = True, False, True

    @stage.generate_widgets
    def make_master_control_widget(self):
        master_name = self.bones.ctrl.master

        w = create_widget(self.obj, master_name)
        if w is not None:
            mesh = w.data
            verts = [(0, 0, 0), (0, 1, 0), (0.05, 1, 0), (0.05, 1.1, 0), (-0.05, 1.1, 0), (-0.05, 1, 0)]
            if 'Z' in self.params.primary_rotation_axis:
                # Flip x/z coordinates
                temp = []
                for v in verts:
                    temp += [(v[2], v[1], v[0])]
                verts = temp
            edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
            mesh.from_pydata(verts, edges, [])
            mesh.update()

    ##############################
    # Control chain

    @stage.generate_bones
    def make_control_chain(self):
        orgs = self.bones.org
        self.bones.ctrl.fk = map_list(self.make_control_bone, count(0), orgs)
        self.bones.ctrl.fk += [self.make_tip_control_bone(orgs[-1], orgs[0])]

    def make_control_bone(self, i, org):
        return self.copy_bone(org, make_derived_name(org, 'ctrl'), parent=False)

    def make_tip_control_bone(self, org, name_org):
        name = self.copy_bone(org, make_derived_name(name_org, 'ctrl'), parent=False)

        flip_bone(self.obj, name)
        self.get_bone(name).length /= 2

        return name

    @stage.parent_bones
    def parent_control_chain(self):
        ctrls = self.bones.ctrl.fk
        for args in zip(ctrls, self.bones.mch.bend + ctrls[-2:]):
            self.set_bone_parent(*args)

    @stage.configure_bones
    def configure_control_chain(self):
        for args in zip(count(0), self.bones.ctrl.fk, self.bones.org + [None]):
            self.configure_control_bone(*args)

        ControlLayersOption.TWEAK.assign(self.params, self.obj, self.bones.ctrl.fk)

    def configure_control_bone(self, i, ctrl, org):
        if org:
            self.copy_bone_properties(org, ctrl)
        else:
            bone = self.get_bone(ctrl)
            bone.lock_rotation_w = True
            bone.lock_rotation = (True, True, True)
            bone.lock_scale = (True, True, True)

    def make_control_widget(self, i, ctrl):
        if ctrl == self.bones.ctrl.fk[-1]:
            # Tip control
            create_circle_widget(self.obj, ctrl, radius=0.3, head_tail=0.0)
        else:
            set_bone_widget_transform(self.obj, ctrl, self.bones.org[i])

            create_circle_widget(self.obj, ctrl, radius=0.3, head_tail=0.5)

    ##############################
    # MCH bend chain

    @stage.generate_bones
    def make_mch_bend_chain(self):
        self.bones.mch.bend = map_list(self.make_mch_bend_bone, self.bones.org)

    def make_mch_bend_bone(self, org):
        return self.copy_bone(org, make_derived_name(org, 'mch', '_drv'), parent=False)

    @stage.parent_bones
    def parent_mch_bend_chain(self):
        ctrls = self.bones.ctrl.fk
        for args in zip(self.bones.mch.bend, [self.first_parent] + ctrls):
            self.set_bone_parent(*args)

    # Match axis to expression
    axis_options = {
        "automatic": {"axis": 0,
                      "expr": '(1-sy)*pi'},
        "X": {"axis": 0,
              "expr": '(1-sy)*pi'},
        "-X": {"axis": 0,
               "expr": '-((1-sy)*pi)'},
        "Y": {"axis": 1,
              "expr": '(1-sy)*pi'},
        "-Y": {"axis": 1,
               "expr": '-((1-sy)*pi)'},
        "Z": {"axis": 2,
              "expr": '(1-sy)*pi'},
        "-Z": {"axis": 2,
               "expr": '-((1-sy)*pi)'}
    }

    @stage.rig_bones
    def rig_mch_bend_chain(self):
        for args in zip(count(0), self.bones.mch.bend):
            self.rig_mch_bend_bone(*args)

    def rig_mch_bend_bone(self, i, mch):
        master = self.bones.ctrl.master
        if i == 0:
            self.make_constraint(mch, 'COPY_LOCATION', master)
            self.make_constraint(mch, 'COPY_ROTATION', master, space='LOCAL')
        else:
            axis = self.params.primary_rotation_axis
            options = self.axis_options[axis]

            bone = self.get_bone(mch)
            bone.rotation_mode = 'YZX'

            self.make_driver(
                bone, 'rotation_euler', index=options['axis'],
                expression=options['expr'],
                variables={'sy': (master, '.scale.y')}
            )

    ##############################
    # MCH stretch chain

    @stage.generate_bones
    def make_mch_stretch_chain(self):
        self.bones.mch.stretch = map_list(self.make_mch_stretch_bone, self.bones.org)

    def make_mch_stretch_bone(self, org):
        return self.copy_bone(org, make_derived_name(org, 'mch'), parent=False)

    @stage.parent_bones
    def parent_mch_stretch_chain(self):
        ctrls = self.bones.ctrl.fk
        for args in zip(self.bones.mch.stretch, [self.first_parent] + ctrls[1:]):
            self.set_bone_parent(*args)

    @stage.rig_bones
    def rig_mch_stretch_chain(self):
        ctrls = self.bones.ctrl.fk
        for args in zip(count(0), self.bones.mch.stretch, ctrls, ctrls[1:]):
            self.rig_mch_stretch_bone(*args)

    def rig_mch_stretch_bone(self, i, mch, ctrl, ctrl_next):
        if i == 0:
            self.make_constraint(mch, 'COPY_LOCATION', ctrl)
            self.make_constraint(mch, 'COPY_SCALE', ctrl)

        self.make_constraint(mch, 'DAMPED_TRACK', ctrl_next)
        self.make_constraint(mch, 'STRETCH_TO', ctrl_next, volume='NO_VOLUME')

    ##############################
    # ORG chain

    @stage.rig_bones
    def rig_org_chain(self):
        for args in zip(count(0), self.bones.org, self.bones.mch.stretch):
            self.rig_org_bone(*args)

    ##############################
    # Deform chain

    @stage.configure_bones
    def configure_master_properties(self):
        master = self.bones.ctrl.master

        if self.bbone_segments > 1:
            self.make_property(master, 'finger_curve', 0.0, description="Rubber hose finger cartoon effect")

            # Create UI
            panel = self.script.panel_with_selected_check(self, self.bones.ctrl.flatten())
            panel.custom_prop(master, 'finger_curve', text="Curvature", slider=True)

    def rig_deform_bone(self, i, deform, org):
        master = self.bones.ctrl.master
        bone = self.get_bone(deform)

        self.make_constraint(deform, 'COPY_TRANSFORMS', org)

        if self.bbone_segments > 1:
            self.make_driver(bone.bone, 'bbone_easein', variables=[(master, 'finger_curve')])
            self.make_driver(bone.bone, 'bbone_easeout', variables=[(master, 'finger_curve')])

    ###############
    # OPTIONS

    @classmethod
    def add_parameters(self, params):
        """ Add the parameters of this rig type to the
            RigifyParameters PropertyGroup
        """
        items = [('automatic', 'Automatic', ''), ('X', 'X manual', ''), ('Y', 'Y manual', ''), ('Z', 'Z manual', ''),
                ('-X', '-X manual', ''), ('-Y', '-Y manual', ''), ('-Z', '-Z manual', '')]
        params.primary_rotation_axis = bpy.props.EnumProperty(items=items, name="Primary Rotation Axis", default='automatic')

        params.bbones = bpy.props.IntProperty(
            name        = 'B-Bone Segments',
            default     = 10,
            min         = 1,
            description = 'Number of B-Bone segments'
        )

        ControlLayersOption.TWEAK.add_parameters(params)

    @classmethod
    def parameters_ui(self, layout, params):
        """ Create the ui for the rig parameters.
        """
        r = layout.row()
        r.label(text="Bend rotation axis:")
        r.prop(params, "primary_rotation_axis", text="")

        layout.prop(params, 'bbones')

        ControlLayersOption.TWEAK.parameters_ui(layout, params)


def create_sample(obj):
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('palm.04.L')
    bone.head[:] = 0.0043, -0.0030, -0.0026
    bone.tail[:] = 0.0642, 0.0037, -0.0469
    bone.roll = -2.5155
    bone.use_connect = False
    bones['palm.04.L'] = bone.name
    bone = arm.edit_bones.new('f_pinky.01.L')
    bone.head[:] = 0.0642, 0.0037, -0.0469
    bone.tail[:] = 0.0703, 0.0039, -0.0741
    bone.roll = -1.9749
    bone.use_connect = False
    bone.parent = arm.edit_bones[bones['palm.04.L']]
    bones['f_pinky.01.L'] = bone.name
    bone = arm.edit_bones.new('f_pinky.02.L')
    bone.head[:] = 0.0703, 0.0039, -0.0741
    bone.tail[:] = 0.0732, 0.0044, -0.0965
    bone.roll = -1.9059
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['f_pinky.01.L']]
    bones['f_pinky.02.L'] = bone.name
    bone = arm.edit_bones.new('f_pinky.03.L')
    bone.head[:] = 0.0732, 0.0044, -0.0965
    bone.tail[:] = 0.0725, 0.0046, -0.1115
    bone.roll = -1.7639
    bone.use_connect = True
    bone.parent = arm.edit_bones[bones['f_pinky.02.L']]
    bones['f_pinky.03.L'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['palm.04.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'YXZ'
    pbone = obj.pose.bones[bones['f_pinky.01.L']]
    pbone.rigify_type = 'limbs.super_finger'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    try:
        pbone.rigify_parameters.extra_layers = [False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.tweak_extra_layers = False
    except AttributeError:
        pass
    pbone = obj.pose.bones[bones['f_pinky.02.L']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['f_pinky.03.L']]
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
