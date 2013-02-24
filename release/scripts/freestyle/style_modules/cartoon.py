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

#  Filename : cartoon.py
#  Author   : Stephane Grabli
#  Date     : 04/08/2005
#  Purpose  : Draws colored lines. The color is automatically 
#             infered from each object's material in a cartoon-like
#             fashion.

from Freestyle import BezierCurveShader, ChainSilhouetteIterator, ConstantThicknessShader, Operators, \
    QuantitativeInvisibilityUP1D, TrueUP1D
from logical_operators import NotUP1D
from shaders import pyMaterialColorShader

Operators.select(QuantitativeInvisibilityUP1D(0))
Operators.bidirectional_chain(ChainSilhouetteIterator(), NotUP1D(QuantitativeInvisibilityUP1D(0)))
shaders_list = [
    BezierCurveShader(3),
    ConstantThicknessShader(4),
    pyMaterialColorShader(0.8),
    ]
Operators.create(TrueUP1D(), shaders_list)
