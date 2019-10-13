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

from itertools import count

from ...utils.layers import ControlLayersOption
from ...utils.naming import make_derived_name
from ...utils.bones import align_bone_orientation, align_bone_to_axis
from ...utils.widgets_basic import create_cube_widget
from ...utils.switch_parent import SwitchParentBuilder

from ...base_rig import stage

from ..chain_rigs import TweakChainRig, ConnectingChainRig


class BaseSpineRig(TweakChainRig):
    """
    Spine rig with tweaks.
    """

    bbone_segments = 8

    def initialize(self):
        if len(self.bones.org) < 3:
            self.raise_error("Input to rig type must be a chain of 3 or more bones.")

        self.length = sum([self.get_bone(b).length for b in self.bones.org])

    ####################################################
    # BONES
    #
    # ctrl:
    #   master
    #     Main control.
    #
    ####################################################

    ####################################################
    # Master control bone

    @stage.generate_bones
    def make_master_control(self):
        self.bones.ctrl.master = name = self.copy_bone(self.bones.org[0], 'torso')

        align_bone_to_axis(self.obj, name, 'y', length=self.length * 0.6)

        self.build_parent_switch(name)

    def build_parent_switch(self, master_name):
        pbuilder = SwitchParentBuilder(self.generator)
        pbuilder.register_parent(self, master_name, name='Torso')
        pbuilder.build_child(
            self, master_name, exclude_self=True,
            prop_id='torso_parent', prop_name='Torso Parent',
            controls=lambda: self.bones.flatten('ctrl'),
        )

        self.register_parent_bones(pbuilder)

    def register_parent_bones(self, pbuilder):
        pbuilder.register_parent(self, self.bones.org[0], name='Hips', exclude_self=True)
        pbuilder.register_parent(self, self.bones.org[-1], name='Chest', exclude_self=True)

    @stage.parent_bones
    def parent_master_control(self):
        pass

    @stage.configure_bones
    def configure_master_control(self):
        pass

    @stage.generate_widgets
    def make_master_control_widget(self):
        create_cube_widget(
            self.obj, self.bones.ctrl.master,
            radius=0.5,
        )

    ####################################################
    # Tweak bones

    @stage.configure_bones
    def configure_tweak_chain(self):
        super().configure_tweak_chain()

        ControlLayersOption.TWEAK.assign(self.params, self.obj, self.bones.ctrl.tweak)

    ####################################################
    # Deform bones

    @stage.configure_bones
    def configure_bbone_chain(self):
        self.get_bone(self.bones.deform[0]).bone.bbone_easein = 0.0

    ####################################################
    # SETTINGS

    @classmethod
    def add_parameters(self, params):
        # Setting up extra layers for the FK and tweak
        ControlLayersOption.TWEAK.add_parameters(params)

    @classmethod
    def parameters_ui(self, layout, params):
        ControlLayersOption.TWEAK.parameters_ui(layout, params)


class BaseHeadTailRig(ConnectingChainRig):
    """ Base for head and tail rigs. """

    def initialize(self):
        super().initialize()

        self.rotation_bones = []

    ####################################################
    # Utilities

    def get_parent_master(self, default_bone):
        """ Return the parent's master control bone if connecting and found. """

        if self.use_connect_chain and 'master' in self.rigify_parent.bones.ctrl:
            return self.rigify_parent.bones.ctrl.master
        else:
            return default_bone

    def get_parent_master_panel(self, default_bone):
        """ Return the parent's master control bone if connecting and found, and script panel. """

        controls = self.bones.ctrl.flatten()
        prop_bone = self.get_parent_master(default_bone)

        if prop_bone != default_bone:
            owner = self.rigify_parent
            controls += self.rigify_parent.bones.ctrl.flatten()
        else:
            owner = self

        return prop_bone, self.script.panel_with_selected_check(owner, controls)

    ####################################################
    # Rotation follow

    def make_mch_follow_bone(self, org, name, defval, *, copy_scale=False):
        bone = self.copy_bone(org, make_derived_name('ROT-'+name, 'mch'), parent=True)
        self.rotation_bones.append((org, name, bone, defval, copy_scale))
        return bone

    @stage.parent_bones
    def align_mch_follow_bones(self):
        self.follow_bone = self.get_parent_master('root')

        for org, name, bone, defval, copy_scale in self.rotation_bones:
            align_bone_orientation(self.obj, bone, self.follow_bone)

    @stage.configure_bones
    def configure_mch_follow_bones(self):
        self.prop_bone, panel = self.get_parent_master_panel(self.default_prop_bone)

        for org, name, bone, defval, copy_scale in self.rotation_bones:
            textname = name.replace('_',' ').title() + ' Follow'

            self.make_property(self.prop_bone, name+'_follow', default=float(defval))
            panel.custom_prop(self.prop_bone, name+'_follow', text=textname, slider=True)

    @stage.rig_bones
    def rig_mch_follow_bones(self):
        for org, name, bone, defval, copy_scale in self.rotation_bones:
            self.rig_mch_rotation_bone(bone, name+'_follow', copy_scale)

    def rig_mch_rotation_bone(self, mch, prop_name, copy_scale):
        con = self.make_constraint(mch, 'COPY_ROTATION', self.follow_bone)

        self.make_driver(con, 'influence', variables=[(self.prop_bone, prop_name)], polynomial=[1,-1])

        if copy_scale:
            self.make_constraint(mch, 'COPY_SCALE', self.follow_bone)

    ####################################################
    # Tweak chain

    @stage.configure_bones
    def configure_tweak_chain(self):
        super().configure_tweak_chain()

        ControlLayersOption.TWEAK.assign(self.params, self.obj, self.bones.ctrl.tweak)

    ####################################################
    # Settings

    @classmethod
    def add_parameters(self, params):
        super().add_parameters(params)

        # Setting up extra layers for the FK and tweak
        ControlLayersOption.TWEAK.add_parameters(params)

    @classmethod
    def parameters_ui(self, layout, params):
        super().parameters_ui(layout, params)

        ControlLayersOption.TWEAK.parameters_ui(layout, params)
