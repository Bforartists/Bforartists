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


ORG_LAYER = [n == 31 for n in range(0, 32)]  # Armature layer that original bones should be moved to.
MCH_LAYER = [n == 30 for n in range(0, 32)]  # Armature layer that mechanism bones should be moved to.
DEF_LAYER = [n == 29 for n in range(0, 32)]  # Armature layer that deformation bones should be moved to.
ROOT_LAYER = [n == 28 for n in range(0, 32)]  # Armature layer that root bone should be moved to.


def get_layers(layers):
    """ Does its best to extract a set of layers from any data thrown at it.
    """
    if type(layers) == int:
        return [x == layers for x in range(0, 32)]
    elif type(layers) == str:
        s = layers.split(",")
        l = []
        for i in s:
            try:
                l += [int(float(i))]
            except ValueError:
                pass
        return [x in l for x in range(0, 32)]
    elif type(layers) == tuple or type(layers) == list:
        return [x in layers for x in range(0, 32)]
    else:
        try:
            list(layers)
        except TypeError:
            pass
        else:
            return [x in layers for x in range(0, 32)]


def set_bone_layers(bone, layers, combine=False):
    if combine:
        bone.layers = [ a or b for a, b in zip(bone.layers, layers) ]
    else:
        bone.layers = layers


#=============================================
# UI utilities
#=============================================


def layout_layer_buttons(layout, params, option, active_layers):
    "Draw a layer selection button UI with certain layers marked with dots."
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
    def __init__(self, name, toggle_name=None, toggle_default=True, description="Set of control layers"):
        self.name = name
        self.toggle_default = toggle_default
        self.description = description

        self.toggle_option = self.name+'_layers_extra'
        self.layers_option = self.name+'_layers'
        self.toggle_name = toggle_name if toggle_name else "Assign " + self.name.title() + " Layers"

    def get(self, params):
        if getattr(params, self.toggle_option):
            return list(getattr(params, self.layers_option))
        else:
            return None

    def assign(self, params, bone_set, bone_list, combine=False):
        layers = self.get(params)

        if isinstance(bone_set, bpy.types.Object):
            bone_set = bone_set.data.bones

        if layers:
            for name in bone_list:
                bone = bone_set[name]
                if isinstance(bone, bpy.types.PoseBone):
                    bone = bone.bone

                set_bone_layers(bone, layers, combine)

    def assign_rig(self, rig, bone_list, combine=False, priority=None):
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

    def parameters_ui(self, layout, params):
        box = layout.box()
        box.prop(params, self.toggle_option)

        active = getattr(params, self.toggle_option)

        if not active:
            return

        active_layers = bpy.context.active_pose_bone.bone.layers[:]

        layout_layer_buttons(box, params, self.layers_option, active_layers)


ControlLayersOption.FK = ControlLayersOption('fk', description="Layers for the FK controls to be on")
ControlLayersOption.TWEAK = ControlLayersOption('tweak', description="Layers for the tweak controls to be on")

# Layer parameters used by the super_face rig.
ControlLayersOption.FACE_PRIMARY = ControlLayersOption('primary', description="Layers for the primary controls to be on")
ControlLayersOption.FACE_SECONDARY = ControlLayersOption('secondary', description="Layers for the secondary controls to be on")
