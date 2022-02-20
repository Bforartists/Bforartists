# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from .naming import make_derived_name
from .bones import put_bone, copy_bone_position, align_bone_orientation
from .widgets_basic import create_pivot_widget
from .misc import force_lazy

from ..base_rig import RigComponent, stage


class CustomPivotControl(RigComponent):
    """
    A utility that generates a pivot control with a custom position.

    Generates a control bone, and a MCH output bone.
    """

    def __init__(
        self, rig, id_name, org_bone, *,
        name=None, parent=None, position=None, matrix=None,
        scale=1.0, scale_mch=None,
        move_to=None, align_to=None, snap_to=None,
        widget_axis=1.5, widget_cap=1.0, widget_square=True,
    ):
        super().__init__(rig)

        assert rig.generator.stage == 'generate_bones'

        self.bones = rig.bones
        self.id_name = id_name

        self.parent = parent
        self.scale = scale or 1
        self.scale_mch = scale_mch or (self.scale * 0.7)
        self.move_to = move_to
        self.align_to = align_to
        self.snap_to = snap_to
        self.widget_axis = widget_axis
        self.widget_cap = widget_cap
        self.widget_square = widget_square

        name = name or make_derived_name(org_bone, 'ctrl', '_pivot')

        self.do_make_bones(org_bone, name, position, matrix)

    @property
    def control(self):
        return self.ctrl

    @property
    def output(self):
        return self.mch

    def do_make_bones(self, org, name, position, matrix):
        self.bones.ctrl[self.id_name] = self.ctrl = self.copy_bone(org, name, parent=not self.parent, scale=self.scale)
        self.bones.mch[self.id_name] = self.mch = self.copy_bone(org, make_derived_name(name, 'mch'), scale=self.scale_mch)

        if position or matrix:
            put_bone(self.obj, self.ctrl, position, matrix=matrix)
            put_bone(self.obj, self.mch, position, matrix=matrix)

    def parent_bones(self):
        if self.snap_to:
            bone = force_lazy(self.snap_to)
            copy_bone_position(self.obj, bone, self.ctrl, scale=self.scale)
            copy_bone_position(self.obj, bone, self.mch, scale=self.scale_mch)

        if self.move_to:
            pos = self.get_bone(force_lazy(self.move_to)).head
            put_bone(self.obj, self.ctrl, pos)
            put_bone(self.obj, self.mch, pos)

        if self.align_to:
            self.align_to = force_lazy(self.align_to)
            align_bone_orientation(self.obj, self.ctrl, self.align_to)
            align_bone_orientation(self.obj, self.mch, self.align_to)

        if self.parent:
            self.set_bone_parent(self.ctrl, force_lazy(self.parent))

        self.set_bone_parent(self.mch, self.ctrl)

    def rig_bones(self):
        self.make_constraint(self.mch, 'COPY_LOCATION', self.ctrl, space='LOCAL', invert_xyz=(True,)*3)

    def generate_widgets(self):
        create_pivot_widget(self.obj, self.ctrl, axis_size=self.widget_axis, cap_size=self.widget_cap, square=self.widget_square)
