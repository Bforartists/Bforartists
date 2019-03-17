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


#=============================================
# UI utilities
#=============================================

class ControlLayersOption:
    def __init__(self, name, toggle_name=None, toggle_default=True, description="Set of control layers"):
        self.name = name
        self.toggle_default = toggle_default
        self.description = description

        self.toggle_option = self.name+'_layers_extra'
        self.layers_option = self.name+'_layers'
        self.toggle_name = toggle_name if toggle_name else self.toggle_option

    def get(self, params):
        if getattr(params, self.toggle_option):
            return list(getattr(params, self.layers_option))
        else:
            return None

    def assign(self, params, bone_set, bone_list):
        layers = self.get(params)

        if layers:
            for name in bone_list:
                bone = bone_set[name]
                if isinstance(bone, bpy.types.PoseBone):
                    bone = bone.bone

                bone.layers = layers

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
            default=tuple([i == 1 for i in range(0, 32)])
        )

        setattr(params, self.layers_option, prop_layers)

    def parameters_ui(self, layout, params):
        r = layout.row()
        r.prop(params, self.toggle_option)
        r.active = getattr(params, self.toggle_option)

        col = r.column(align=True)
        row = col.row(align=True)

        bone_layers = bpy.context.active_pose_bone.bone.layers[:]

        for i in range(8):    # Layers 0-7
            icon = "NONE"
            if bone_layers[i]:
                icon = "LAYER_ACTIVE"
            row.prop(params, self.layers_option, index=i, toggle=True, text="", icon=icon)

        row = col.row(align=True)

        for i in range(16, 24):     # Layers 16-23
            icon = "NONE"
            if bone_layers[i]:
                icon = "LAYER_ACTIVE"
            row.prop(params, self.layers_option, index=i, toggle=True, text="", icon=icon)

        col = r.column(align=True)
        row = col.row(align=True)

        for i in range(8, 16):  # Layers 8-15
            icon = "NONE"
            if bone_layers[i]:
                icon = "LAYER_ACTIVE"
            row.prop(params, self.layers_option, index=i, toggle=True, text="", icon=icon)

        row = col.row(align=True)

        for i in range(24, 32):     # Layers 24-31
            icon = "NONE"
            if bone_layers[i]:
                icon = "LAYER_ACTIVE"
            row.prop(params, self.layers_option, index=i, toggle=True, text="", icon=icon)


ControlLayersOption.FK = ControlLayersOption('fk', description="Layers for the FK controls to be on")
ControlLayersOption.TWEAK = ControlLayersOption('tweak', description="Layers for the tweak controls to be on")
