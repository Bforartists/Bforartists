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

from ...base_generate import SubstitutionRig

from .limb_rigs import BaseLimbRig

from . import arm, leg, paw


RIGS = { 'arm': arm.Rig, 'leg': leg.Rig, 'paw': paw.Rig }


class Rig(SubstitutionRig):
    def substitute(self):
        return [ self.instantiate_rig(RIGS[self.params.limb_type], self.base_bone) ]


def add_parameters(params):
    items = [
        ('arm', 'Arm', ''),
        ('leg', 'Leg', ''),
        ('paw', 'Paw', '')
    ]

    params.limb_type = bpy.props.EnumProperty(
        items   = items,
        name    = "Limb Type",
        default = 'arm'
    )

    BaseLimbRig.add_parameters(params)


def parameters_ui(layout, params):
    r = layout.row()
    r.prop(params, "limb_type")

    RIGS[params.limb_type].parameters_ui(layout, params)


def create_sample(obj):
    arm.create_sample(obj, limb=True)
