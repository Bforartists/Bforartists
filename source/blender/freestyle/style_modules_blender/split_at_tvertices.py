#
#  Filename : split_at_tvertices.py
#  Author   : Stephane Grabli
#  Date     : 04/08/2005
#  Purpose  : Draws strokes that starts and stops at Tvertices (visible or not)
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

from Blender.Freestyle import *
from logical_operators import *
from PredicatesU1D import *
from PredicatesU0D import *
from Functions0D import *

Operators.select(QuantitativeInvisibilityUP1D(0))
Operators.bidirectionalChain(ChainSilhouetteIterator(), NotUP1D(QuantitativeInvisibilityUP1D(0)))
start = pyVertexNatureUP0D(T_VERTEX)
## use the same predicate to decide where to start and where to stop 
## the strokes:
Operators.sequentialSplit(start, start, 10)
shaders_list = [ConstantThicknessShader(5), IncreasingColorShader(1,0,0,1,0,1,0,1), TextureAssignerShader(3)]
Operators.create(TrueUP1D(), shaders_list)

