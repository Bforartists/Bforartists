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

#  Filename : thickness_fof_depth_discontinuity.py
#  Author   : Stephane Grabli
#  Date     : 04/08/2005
#  Purpose  : Assigns to strokes a thickness that depends on the depth discontinuity

from freestyle import ChainSilhouetteIterator, ConstantColorShader, ConstantThicknessShader, \
    Operators, QuantitativeInvisibilityUP1D, SamplingShader, TrueUP1D
from logical_operators import NotUP1D
from shaders import pyDepthDiscontinuityThicknessShader

Operators.select(QuantitativeInvisibilityUP1D(0))
Operators.bidirectional_chain(ChainSilhouetteIterator(), NotUP1D(QuantitativeInvisibilityUP1D(0)))
shaders_list = [
    SamplingShader(1),
    ConstantThicknessShader(3),
    ConstantColorShader(0.0, 0.0, 0.0),
    pyDepthDiscontinuityThicknessShader(0.8, 6),
    ]
Operators.create(TrueUP1D(), shaders_list)
