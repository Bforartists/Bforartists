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
import re

from math import cos, pi
from itertools import count, repeat

from rigify.utils.rig import is_rig_base_bone
from rigify.utils.naming import strip_org, make_derived_name
from rigify.utils.widgets import create_widget
from rigify.utils.misc import map_list

from rigify.base_rig import BaseRig, stage


def bone_siblings(obj, bone):
    """ Returns a list of the siblings of the given bone.
        This requires that the bones has a parent.
    """
    parent = obj.data.bones[bone].parent

    if parent is None:
        return []

    bones = []

    for b in parent.children:
        if b.name != bone and not is_rig_base_bone(obj, b.name):
            bones += [b.name]

    return bones


class Rig(BaseRig):
    """ A "palm" rig.  A set of sibling bones that bend with each other.
        This is a control and deformation rig.
    """

    def find_org_bones(self, bone):
        base_head = bone.bone.head
        siblings = bone_siblings(self.obj, bone.name)

        # Sort list by name and distance
        siblings.sort()
        siblings.sort(key=lambda b: (self.get_bone(b).bone.head - base_head).length)

        return [bone.name] + siblings

    def initialize(self):
        if len(self.bones.org) <= 1:
            self.raise_error('The palm rig must have a parent and at least one sibling')

        self.palm_rotation_axis = self.params.palm_rotation_axis
        self.make_secondary = self.params.palm_both_sides

        self.order = 'YXZ' if 'X' in self.palm_rotation_axis else 'YZX'

        # Figure out the name for the control bone (remove the last .##)
        self.ctrl_name = re.sub("([0-9]+\.)", "", strip_org(self.bones.org[-1])[::-1], count=1)[::-1]

    def parent_bones(self):
        self.rig_parent_bone = self.get_bone_parent(self.bones.org[0])

        # Parent to the deform bone of the parent if exists
        def_bone = make_derived_name(self.rig_parent_bone, 'def')

        if def_bone in self.obj.data.bones:
            self.rig_parent_bone = def_bone

    ####################################################
    # BONES
    #
    # org[]:
    #   Original bones in order of distance.
    # ctrl:
    #   master:
    #     Main control.
    #   secondary:
    #     Control for the other side.
    # deform[]:
    #   DEF bones
    #
    ####################################################

    ####################################################
    # Master control

    @stage.generate_bones
    def make_master_control(self):
        orgs = self.bones.org

        self.bones.ctrl.master = self.copy_bone(orgs[-1], self.ctrl_name, parent=True)

        if self.make_secondary:
            second_name = make_derived_name(orgs[0], 'ctrl')
            self.bones.ctrl.secondary = self.copy_bone(orgs[0], second_name, parent=True)

    @stage.parent_bones
    def parent_master_control(self):
        self.set_bone_parent(self.bones.ctrl.master, self.rig_parent_bone, inherit_scale='AVERAGE')

        if self.make_secondary:
            self.set_bone_parent(self.bones.ctrl.secondary, self.rig_parent_bone, inherit_scale='AVERAGE')

    @stage.configure_bones
    def configure_master_control(self):
        self.configure_control_bone(self.bones.ctrl.master, self.bones.org[-1])

        if self.make_secondary:
            self.configure_control_bone(self.bones.ctrl.secondary, self.bones.org[0])

    def configure_control_bone(self, ctrl, org):
        self.copy_bone_properties(org, ctrl)
        self.get_bone(ctrl).lock_scale = (True, True, True)

    @stage.generate_widgets
    def make_master_control_widgets(self):
        self.make_control_widget(self.bones.ctrl.master)

        if self.make_secondary:
            self.make_control_widget(self.bones.ctrl.secondary)

    def make_control_widget(self, ctrl):
        w = create_widget(self.obj, ctrl)
        if w is not None:
            mesh = w.data
            verts = [
                (0.1578, 0.0, -0.3),
                (0.1578, 1.0, -0.2),
                (-0.1578, 1.0, -0.2),
                (-0.1578, -0.0, -0.3),
                (-0.1578, -0.0, 0.3),
                (-0.1578, 1.0, 0.2),
                (0.1578, 1.0, 0.2),
                (0.1578, 0.0, 0.3),
                (0.1578, 0.25, -0.275),
                (-0.1578, 0.25, -0.275),
                (0.1578, 0.75, -0.225),
                (-0.1578, 0.75, -0.225),
                (0.1578, 0.75, 0.225),
                (0.1578, 0.25, 0.275),
                (-0.1578, 0.25, 0.275),
                (-0.1578, 0.75, 0.225),
                ]

            if 'Z' in self.palm_rotation_axis:
                # Flip x/z coordinates
                verts = [v[::-1] for v in verts]

            edges = [
                (1, 2), (0, 3), (4, 7), (5, 6),
                (8, 0), (9, 3), (10, 1), (11, 2),
                (12, 6), (13, 7), (4, 14), (15, 5),
                (10, 8), (11, 9), (15, 14), (12, 13),
                ]
            mesh.from_pydata(verts, edges, [])
            mesh.update()

            mod = w.modifiers.new("subsurf", 'SUBSURF')
            mod.levels = 2

    ####################################################
    # ORG bones

    @stage.parent_bones
    def parent_org_chain(self):
        for org in self.bones.org:
            self.set_bone_parent(org, self.rig_parent_bone, inherit_scale='NONE')

    @stage.rig_bones
    def rig_org_chain(self):
        orgs = self.bones.org
        ctrl = self.bones.ctrl

        for args in zip(count(0), orgs, repeat(len(orgs))):
            self.rig_org_bone(*args)

    def rig_org_bone(self, i, org, num_orgs):
        ctrl = self.bones.ctrl
        fac = i / (num_orgs - 1)

        if fac > 0:
            self.make_constraint(
                org, 'COPY_TRANSFORMS', ctrl.master, space='LOCAL',
                influence=fac
            )

            if self.make_secondary and fac < 1:
                self.make_constraint(
                    org, 'COPY_LOCATION', ctrl.secondary, space='LOCAL',
                    use_offset=True, influence=1-fac
                )
                self.make_constraint(
                    org, 'COPY_ROTATION', ctrl.secondary, space='LOCAL',
                    euler_order=self.order, mix_mode='ADD', influence=1-fac
                )

        elif self.make_secondary:
            self.make_constraint(
                org, 'COPY_TRANSFORMS', ctrl.secondary, space='LOCAL'
            )

        self.make_constraint(org, 'COPY_SCALE', self.rig_parent_bone)

        self.rig_org_back_rotation(org, ctrl.master, fac)

        if self.make_secondary:
            self.rig_org_back_rotation(org, ctrl.secondary, 1 - fac)

    def rig_org_back_rotation(self, org, ctrl, fac):
        if 0 < fac < 1:
            inf = (fac + 1) * (fac + cos(fac * pi / 2) - 1)

            if 'X' in self.palm_rotation_axis:
                self.make_constraint(
                    org, 'COPY_ROTATION', ctrl, space='LOCAL',
                    invert_x=True, use_xyz=(True,False,False),
                    euler_order=self.order, mix_mode='ADD', influence=inf
                )
            else:
                self.make_constraint(
                    org, 'COPY_ROTATION', ctrl, space='LOCAL',
                    invert_z=True, use_xyz=(False,False,True),
                    euler_order=self.order, mix_mode='ADD', influence=inf
                )

    ####################################################
    # DEF bones

    @stage.generate_bones
    def make_def_chain(self):
        self.bones.deform = map_list(self.make_deform_bone, self.bones.org)

    def make_deform_bone(self, org):
        return self.copy_bone(org, make_derived_name(org, 'def'))

    @stage.parent_bones
    def parent_deform_chain(self):
        for deform, org in zip(self.bones.deform, self.bones.org):
            self.set_bone_parent(deform, org, use_connect=False)

    ####################################################
    # Settings

    @classmethod
    def add_parameters(cls, params):
        items = [('X', 'X', ''), ('Z', 'Z', '')]
        params.palm_rotation_axis = bpy.props.EnumProperty(
                items=items,
                name="Palm Rotation Axis",
                default='X',
                )
        params.palm_both_sides = bpy.props.BoolProperty(
                name="Both Sides",
                default=False,
                description="Create controls for both sides of the palm"
                )

    @classmethod
    def parameters_ui(cls, layout, params):
        r = layout.row()
        r.label(text="Primary rotation axis:")
        r.prop(params, "palm_rotation_axis", text="")
        layout.prop(params, "palm_both_sides")


def create_sample(obj):
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('palm.parent')
    bone.head[:] = 0.0000, 0.0000, 0.0000
    bone.tail[:] = 0.0577, 0.0000, -0.0000
    bone.roll = 3.1416
    bone.use_connect = False
    bones['palm.parent'] = bone.name
    bone = arm.edit_bones.new('palm.04')
    bone.head[:] = 0.0577, 0.0315, -0.0000
    bone.tail[:] = 0.1627, 0.0315, -0.0000
    bone.roll = 3.1416
    bone.use_connect = False
    bone.parent = arm.edit_bones[bones['palm.parent']]
    bones['palm.04'] = bone.name
    bone = arm.edit_bones.new('palm.03')
    bone.head[:] = 0.0577, 0.0105, -0.0000
    bone.tail[:] = 0.1627, 0.0105, -0.0000
    bone.roll = 3.1416
    bone.use_connect = False
    bone.parent = arm.edit_bones[bones['palm.parent']]
    bones['palm.03'] = bone.name
    bone = arm.edit_bones.new('palm.02')
    bone.head[:] = 0.0577, -0.0105, -0.0000
    bone.tail[:] = 0.1627, -0.0105, -0.0000
    bone.roll = 3.1416
    bone.use_connect = False
    bone.parent = arm.edit_bones[bones['palm.parent']]
    bones['palm.02'] = bone.name
    bone = arm.edit_bones.new('palm.01')
    bone.head[:] = 0.0577, -0.0315, -0.0000
    bone.tail[:] = 0.1627, -0.0315, -0.0000
    bone.roll = 3.1416
    bone.use_connect = False
    bone.parent = arm.edit_bones[bones['palm.parent']]
    bones['palm.01'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['palm.parent']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['palm.04']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, True, True)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'YXZ'
    pbone = obj.pose.bones[bones['palm.03']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, True, True)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'YXZ'
    pbone = obj.pose.bones[bones['palm.02']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, True, True)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'YXZ'
    pbone = obj.pose.bones[bones['palm.01']]
    pbone.rigify_type = 'limbs.super_palm'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, True, True)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'YXZ'

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
