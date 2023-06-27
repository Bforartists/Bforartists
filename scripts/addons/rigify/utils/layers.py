# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from typing import TYPE_CHECKING, Sequence, Optional, Mapping
from bpy.types import Bone, UILayout, Object, PoseBone, Armature

if TYPE_CHECKING:
    from ..base_rig import BaseRig


ORG_LAYER = [n == 31 for n in range(0, 32)]  # Armature layer that original bones should be moved to.
MCH_LAYER = [n == 30 for n in range(0, 32)]  # Armature layer that mechanism bones should be moved to.
DEF_LAYER = [n == 29 for n in range(0, 32)]  # Armature layer that deformation bones should be moved to.
ROOT_LAYER = [n == 28 for n in range(0, 32)]  # Armature layer that root bone should be moved to.


def get_layers(layers) -> list[bool]:
    """ Does its best to extract a set of layers from any data thrown at it.
    """
    if type(layers) == int:
        return [x == layers for x in range(0, 32)]
    elif type(layers) == str:
        items = layers.split(",")
        layers = []
        for i in items:
            try:
                layers += [int(float(i))]
            except ValueError:
                pass
        return [x in layers for x in range(0, 32)]
    elif type(layers) == tuple or type(layers) == list:
        return [x in layers for x in range(0, 32)]
    else:
        try:
            list(layers)
        except TypeError:
            pass
        else:
            return [x in layers for x in range(0, 32)]


def set_bone_layers(bone: Bone, layers: Sequence[bool], combine=False):
    if combine:
        bone.layers = [a or b for a, b in zip(bone.layers, layers)]
    else:
        bone.layers = layers


##############################################
# UI utilities
##############################################


def layout_layer_buttons(layout: UILayout, params, option: str, active_layers: Sequence[bool]):
    """Draw a layer selection button UI with certain layers marked with dots."""
    outer = layout.row()

    for x in [0, 8]:
        col = outer.column(align=True)

        for y in [0, 16]:
            row = col.row(align=True)

            for i in range(x+y, x+y+8):
                row.prop(
                    params, option, index=i, toggle=True, text="",
                    icon="LAYER_ACTIVE" if active_layers[i] else "NONE"
                )


class ControlLayersOption:
    def __init__(self, name: str,
                 toggle_name: Optional[str] = None,
                 toggle_default=True, description="Set of control layers"):
        self.name = name
        self.toggle_default = toggle_default
        self.description = description

        self.toggle_option = self.name+'_layers_extra'
        self.layers_option = self.name+'_layers'

        if toggle_name:
            self.toggle_name = toggle_name
        else:
            self.toggle_name = "Assign " + self.name.title() + " Layers"

    def get(self, params) -> Optional[list[bool]]:
        if getattr(params, self.toggle_option):
            return list(getattr(params, self.layers_option))
        else:
            return None

    def assign(self, params,
               bone_set: Object | Mapping[str, Bone | PoseBone],
               bone_list: Sequence[str],
               combine=False):
        layers = self.get(params)

        if isinstance(bone_set, Object):
            assert isinstance(bone_set.data, Armature)
            bone_set = bone_set.data.bones

        if layers:
            for name in bone_list:
                bone = bone_set[name]
                if isinstance(bone, PoseBone):
                    bone = bone.bone

                set_bone_layers(bone, layers, combine)

    def assign_rig(self, rig: 'BaseRig', bone_list: Sequence[str], combine=False, priority=None):
        layers = self.get(rig.params)
        bone_set = rig.obj.data.bones

        if layers:
            for name in bone_list:
                set_bone_layers(bone_set[name], layers, combine)

                if priority is not None:
                    rig.generator.set_layer_group_priority(name, layers, priority)

    def add_parameters(self, params):
        prop_toggle = bpy.props.BoolProperty(
            name=self.toggle_name,
            default=self.toggle_default,
            description=""
        )

        setattr(params, self.toggle_option, prop_toggle)

        prop_layers = bpy.props.BoolVectorProperty(
            size=32,
            description=self.description,
            subtype='LAYER',
            default=tuple([i == 1 for i in range(0, 32)])
        )

        setattr(params, self.layers_option, prop_layers)

    def parameters_ui(self, layout: UILayout, params):
        box = layout.box()
        box.prop(params, self.toggle_option)

        active = getattr(params, self.toggle_option)

        if not active:
            return

        active_layers = bpy.context.active_pose_bone.bone.layers[:]

        layout_layer_buttons(box, params, self.layers_option, active_layers)

    # Declarations for auto-completion
    FK: 'ControlLayersOption'
    TWEAK: 'ControlLayersOption'
    EXTRA_IK: 'ControlLayersOption'
    FACE_PRIMARY: 'ControlLayersOption'
    FACE_SECONDARY: 'ControlLayersOption'
    SKIN_PRIMARY: 'ControlLayersOption'
    SKIN_SECONDARY: 'ControlLayersOption'


ControlLayersOption.FK = ControlLayersOption(
    'fk', description="Layers for the FK controls to be on")
ControlLayersOption.TWEAK = ControlLayersOption(
    'tweak', description="Layers for the tweak controls to be on")

ControlLayersOption.EXTRA_IK = ControlLayersOption(
    'extra_ik', toggle_default=False,
    toggle_name="Extra IK Layers",
    description="Layers for the optional IK controls to be on",
)

# Layer parameters used by the super_face rig.
ControlLayersOption.FACE_PRIMARY = ControlLayersOption(
    'primary', description="Layers for the primary controls to be on")
ControlLayersOption.FACE_SECONDARY = ControlLayersOption(
    'secondary', description="Layers for the secondary controls to be on")

# Layer parameters used by the skin rigs
ControlLayersOption.SKIN_PRIMARY = ControlLayersOption(
    'skin_primary', toggle_default=False,
    toggle_name="Primary Control Layers",
    description="Layers for the primary controls to be on",
)

ControlLayersOption.SKIN_SECONDARY = ControlLayersOption(
    'skin_secondary', toggle_default=False,
    toggle_name="Secondary Control Layers",
    description="Layers for the secondary controls to be on",
)
