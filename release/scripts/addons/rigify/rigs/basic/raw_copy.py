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

from ...utils.naming import strip_org, strip_prefix, choose_derived_bone

from ...base_rig import BaseRig
from ...base_generate import SubstitutionRig

from itertools import repeat


class Rig(SubstitutionRig):
    """ A raw copy rig, preserving the metarig bone as is, without the ORG prefix. """

    def substitute(self):
        # Strip the ORG prefix during the rig instantiation phase
        new_name = strip_org(self.base_bone)
        new_name = self.generator.rename_org_bone(self.base_bone, new_name)

        return [ self.instantiate_rig(InstanceRig, new_name) ]


class RelinkConstraintsMixin:
    """ Utilities for constraint relinking. """

    def relink_bone_constraints(self, bone_name):
        if self.params.relink_constraints:
            for con in self.get_bone(bone_name).constraints:
                parts = con.name.split('@')

                if len(parts) > 1:
                    self.relink_constraint(con, parts[1:])


    def relink_bone_parent(self, bone_name):
        if self.params.relink_constraints:
            self.generator.disable_auto_parent(bone_name)

            parent_spec = self.params.parent_bone
            if parent_spec:
                old_parent = self.get_bone_parent(bone_name)
                new_parent = self.find_relink_target(parent_spec, old_parent or '') or None
                self.set_bone_parent(bone_name, new_parent)
                return new_parent


    def relink_constraint(self, con, specs):
        if con.type == 'ARMATURE':
            if len(specs) == 1:
                specs = repeat(specs[0])
            elif len(specs) != len(con.targets):
                self.report_error("Constraint {} actually has {} targets", con.name, len(con.targets))

            for tgt, spec in zip(con.targets, specs):
                tgt.subtarget = self.find_relink_target(spec, tgt.subtarget)

        else:
            if len(specs) > 1:
                self.report_error("Only the Armature constraint can have multiple '@' targets: {}", con.name)

            con.subtarget = self.find_relink_target(specs[0], con.subtarget)


    def find_relink_target(self, spec, old_target):
        if spec == '':
            return old_target
        elif spec in {'CTRL', 'DEF', 'MCH'}:
            result = choose_derived_bone(self.generator, old_target, spec.lower())
            if not result:
                result = choose_derived_bone(self.generator, old_target, spec.lower(), by_owner=False)
            if not result:
                self.report_error("Cannot find derived {} bone of bone '{}' for relinking", spec, old_target)
            return result
        else:
            if spec not in self.obj.pose.bones:
                self.report_error("Cannot find bone '{}' for relinking", spec)
            return spec


    @classmethod
    def add_relink_constraints_params(self, params):
        params.relink_constraints = bpy.props.BoolProperty(
            name        = "Relink Constraints",
            default     = False,
            description = "For constraints with names formed like 'base@bonename', use the part after '@' as the new subtarget after all bones are created. Use '@CTRL', '@DEF' or '@MCH' to simply replace the prefix"
        )

        params.parent_bone = bpy.props.StringProperty(
            name        = "Parent",
            default     = "",
            description = "Replace the parent with a different bone after all bones are created. Using simply CTRL, DEF or MCH will replace the prefix instead"
        )

    @classmethod
    def add_relink_constraints_ui(self, layout, params):
        r = layout.row()
        r.prop(params, "relink_constraints")

        if params.relink_constraints:
            r = layout.row()
            r.prop(params, "parent_bone")


class InstanceRig(BaseRig, RelinkConstraintsMixin):
    def find_org_bones(self, pose_bone):
        return pose_bone.name

    def initialize(self):
        self.relink = self.params.relink_constraints

    def parent_bones(self):
        self.relink_bone_parent(self.bones.org)

    def rig_bones(self):
        self.relink_bone_constraints(self.bones.org)

    @classmethod
    def add_parameters(self, params):
        self.add_relink_constraints_params(params)

    @classmethod
    def parameters_ui(self, layout, params):
        col = layout.column()
        col.label(text='This rig type does not add the ORG prefix.')
        col.label(text='Manually add ORG, MCH or DEF as needed.')

        self.add_relink_constraints_ui(layout, params)


add_parameters = InstanceRig.add_parameters
parameters_ui = InstanceRig.parameters_ui


def create_sample(obj):
    """ Create a sample metarig for this rig type.
    """
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('DEF-bone')
    bone.head[:] = 0.0000, 0.0000, 0.0000
    bone.tail[:] = 0.0000, 0.0000, 0.2000
    bone.roll = 0.0000
    bone.use_connect = False
    bones['DEF-bone'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['DEF-bone']]
    pbone.rigify_type = 'basic.raw_copy'
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

    return bones
