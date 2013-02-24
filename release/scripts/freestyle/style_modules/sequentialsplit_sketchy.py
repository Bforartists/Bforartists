#
#  Filename : sequentialsplit_sketchy.py
#  Author   : Stephane Grabli
#  Date     : 04/08/2005
#  Purpose  : Use the sequential split with two different
#             predicates to specify respectively the starting and
#             the stopping extremities for strokes 
#
#############################################################################  
#
#  Copyright (C) : Please refer to the COPYRIGHT file distributed 
#  with this source distribution. 
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
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#############################################################################

from freestyle_init import *
from logical_operators import *
from PredicatesU1D import *
from PredicatesU0D import *
from Functions0D import *

upred = QuantitativeInvisibilityUP1D(0)
Operators.select(upred)
Operators.bidirectional_chain(ChainSilhouetteIterator(), NotUP1D(upred))
## starting and stopping predicates:
start = pyVertexNatureUP0D(Nature.NON_T_VERTEX)
stop = pyBackTVertexUP0D()
Operators.sequential_split(start, stop, 10)
shaders_list = [
		SpatialNoiseShader(7, 120, 2, True, True), 
		IncreasingThicknessShader(5, 8), 
		ConstantColorShader(0.2, 0.2, 0.2, 1), 
		TextureAssignerShader(4)
		]
Operators.create(TrueUP1D(), shaders_list)

