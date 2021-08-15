# ====================== BEGIN GPL LICENSE BLOCK ======================
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
# ======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy
import math

from itertools import count, repeat
from mathutils import Vector, Matrix

from ....utils.naming import make_derived_name
from ....utils.widgets_basic import create_cube_widget
from ....utils.misc import LazyRef

from ....base_rig import stage

from ..skin_parents import ControlBoneParentArmature
from ..skin_rigs import BaseSkinRig


class Rig(BaseSkinRig):
    """
    This rig transforms its child nodes' locations, but keeps
    their rotation and scale stable. This demonstrates implementing
    a basic parent controller rig.
    """

    def find_org_bones(self, bone):
        return bone.name

    def initialize(self):
        super().initialize()

        self.make_control = self.params.make_control

        # Choose the parent bone for the child nodes
        if self.make_control:
            self.input_ref = LazyRef(self.bones.ctrl, 'master')
        else:
            self.input_ref = self.base_bone

        # Retrieve the orientation of the control
        matrix = self.get_bone(self.base_bone).bone.matrix_local

        self.transform_orientation = matrix.to_quaternion()

    ####################################################
    # Control Nodes

    def build_control_node_parent(self, node, parent_bone):
        # Parent nodes to the control bone, but isolate rotation and scale
        return ControlBoneParentArmature(
            self, node, bones=[self.input_ref],
            orientation=self.transform_orientation,
            copy_scale=LazyRef(self.bones.mch, 'template'),
            copy_rotation=LazyRef(self.bones.mch, 'template'),
        )

    def get_child_chain_parent(self, rig, parent_bone):
        # Forward child chain parenting to the next rig, so that
        # only control nodes are affected by this one.
        return self.get_child_chain_parent_next(rig)

    ####################################################
    # BONES
    #
    # ctrl:
    #   master
    #     Master control
    # mch:
    #   template
    #     Bone used to lock rotation and scale of child nodes.
    #
    ####################################################

    ####################################################
    # Master control

    @stage.generate_bones
    def make_master_control(self):
        if self.make_control:
            self.bones.ctrl.master = self.copy_bone(
                self.bones.org, make_derived_name(self.bones.org, 'ctrl'), parent=True)

    @stage.configure_bones
    def configure_master_control(self):
        if self.make_control:
            self.copy_bone_properties(self.bones.org, self.bones.ctrl.master)

    @stage.generate_widgets
    def make_master_control_widget(self):
        if self.make_control:
            create_cube_widget(self.obj, self.bones.ctrl.master)

    ####################################################
    # Template MCH

    @stage.generate_bones
    def make_mch_template_bone(self):
        self.bones.mch.template = self.copy_bone(
            self.bones.org, make_derived_name(self.bones.org, 'mch', '_orient'), parent=True)

    @stage.parent_bones
    def parent_mch_template_bone(self):
        self.set_bone_parent(self.bones.mch.template, self.get_child_chain_parent_next(self))

    ####################################################
    # ORG bone

    @stage.rig_bones
    def rig_org_bone(self):
        pass

    ####################################################
    # SETTINGS

    @classmethod
    def add_parameters(self, params):
        params.make_control = bpy.props.BoolProperty(
            name="Control",
            default=True,
            description="Create a control bone for the copy"
        )

    @classmethod
    def parameters_ui(self, layout, params):
        layout.prop(params, "make_control", text="Generate Control")


def create_sample(obj):
    from rigify.rigs.basic.super_copy import create_sample as inner
    obj.pose.bones[inner(obj)["Bone"]].rigify_type = 'skin.transform.basic'
