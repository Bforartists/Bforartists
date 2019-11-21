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

from ...base_rig import BaseRig

from ...utils.layers import DEF_LAYER
from ...utils.naming import strip_org, make_deformer_name
from ...utils.widgets_basic import create_bone_widget, create_circle_widget

from itertools import repeat


class Rig(BaseRig):
    """ A "copy" rig.  All it does is duplicate the original bone and
        constrain it.
        This is a control and deformation rig.

    """
    def find_org_bones(self, pose_bone):
        return pose_bone.name


    def initialize(self):
        """ Gather and validate data about the rig.
        """
        self.org_name     = strip_org(self.bones.org)

        self.make_control = self.params.make_control
        self.make_widget  = self.params.make_widget

        deform = self.params.make_deform
        rename = self.params.rename_to_deform

        self.make_deform  = deform and not rename
        self.rename_deform = deform and rename

        self.relink = self.params.relink_constraints


    def generate_bones(self):
        bones = self.bones

        # Make a control bone (copy of original).
        if self.make_control:
            bones.ctrl = self.copy_bone(bones.org, self.org_name, parent=True)

        # Make a deformation bone (copy of original, child of original).
        if self.make_deform:
            bones.deform = self.copy_bone(bones.org, make_deformer_name(self.org_name), bbone=True)


    def parent_bones(self):
        bones = self.bones

        if self.make_deform:
            self.set_bone_parent(bones.deform, bones.org, use_connect=False)

        if self.relink:
            self.generator.disable_auto_parent(bones.org)

            parent_spec = self.params.parent_bone
            if parent_spec:
                old_parent = self.get_bone_parent(bones.org)
                new_parent = self.find_relink_target(parent_spec, old_parent or '') or None
                self.set_bone_parent(bones.org, new_parent)

                if self.make_control:
                    self.set_bone_parent(bones.ctrl, new_parent)


    def configure_bones(self):
        bones = self.bones

        if self.make_control:
            self.copy_bone_properties(bones.org, bones.ctrl)


    def rig_bones(self):
        bones = self.bones

        if self.relink:
            for con in self.get_bone(bones.org).constraints:
                parts = con.name.split('@')

                if len(parts) > 1:
                    self.relink_constraint(con, parts[1:])

        if self.make_control:
            # Constrain the original bone.
            self.make_constraint(bones.org, 'COPY_TRANSFORMS', bones.ctrl, insert_index=0)

    def relink_constraint(self, con, specs):
        if con.type == 'ARMATURE':
            if len(specs) == 1:
                specs = repeat(specs[0])
            elif len(specs) != len(con.specs):
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
        elif spec in {'DEF', 'MCH'}:
            spec = spec + '-' + strip_org(old_target)

        if spec not in self.obj.pose.bones:
            # Hack: allow referring to copy rigs using Rename To Deform as DEF
            if old_target.startswith('ORG-') and spec == make_deformer_name(strip_org(old_target)):
                from . import copy_chain

                owner = self.generator.bone_owners.get(old_target)

                if ((isinstance(owner, Rig) and owner.rename_deform) or
                    (isinstance(owner, copy_chain.Rig) and owner.rename_deforms)):
                    return old_target

            self.report_error("Cannot find bone '{}' for relinking", spec)

        return spec


    def generate_widgets(self):
        bones = self.bones

        if self.make_control:
            # Create control widget
            if self.make_widget:
                create_circle_widget(self.obj, bones.ctrl, radius=0.5)
            else:
                create_bone_widget(self.obj, bones.ctrl)


    def finalize(self):
        if self.rename_deform:
            new_name = self.rename_bone(self.bones.org, make_deformer_name(self.org_name))

            bone = self.get_bone(new_name).bone
            bone.use_deform = True
            bone.layers = DEF_LAYER


    @classmethod
    def add_parameters(self, params):
        """ Add the parameters of this rig type to the
            RigifyParameters PropertyGroup
        """
        params.make_control = bpy.props.BoolProperty(
            name        = "Control",
            default     = True,
            description = "Create a control bone for the copy"
        )

        params.make_widget = bpy.props.BoolProperty(
            name        = "Widget",
            default     = True,
            description = "Choose a widget for the bone control"
        )

        params.make_deform = bpy.props.BoolProperty(
            name        = "Deform",
            default     = True,
            description = "Create a deform bone for the copy"
        )

        params.rename_to_deform = bpy.props.BoolProperty(
            name        = "Rename To Deform",
            default     = False,
            description = "Rename the original bone itself to use as deform bone (advanced feature)"
        )

        params.relink_constraints = bpy.props.BoolProperty(
            name        = "Relink Constraints",
            default     = False,
            description = "For constraints with names formed like 'base@bonename', use the part after '@' as the new subtarget after all bones are created. Use '@DEF' or '@MCH' to simply prepend the prefix"
        )

        params.parent_bone = bpy.props.StringProperty(
            name        = "Parent",
            default     = "",
            description = "Replace the parent with a different bone after all bones are created. Using simply DEF or MCH will prepend the prefix instead"
        )


    @classmethod
    def parameters_ui(self, layout, params):
        """ Create the ui for the rig parameters.
        """
        r = layout.row()
        r.prop(params, "make_control")
        r = layout.row()
        r.prop(params, "make_widget")
        r.enabled = params.make_control
        r = layout.row()
        r.prop(params, "make_deform")

        if params.make_deform:
            r = layout.row()
            r.prop(params, "rename_to_deform")

        r = layout.row()
        r.prop(params, "relink_constraints")

        if params.relink_constraints:
            r = layout.row()
            r.prop(params, "parent_bone")


def create_sample(obj):
    """ Create a sample metarig for this rig type.
    """
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('Bone')
    bone.head[:] = 0.0000, 0.0000, 0.0000
    bone.tail[:] = 0.0000, 0.0000, 0.2000
    bone.roll = 0.0000
    bone.use_connect = False
    bones['Bone'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['Bone']]
    pbone.rigify_type = 'basic.super_copy'
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
