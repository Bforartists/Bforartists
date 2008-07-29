#
#  Filename : near_lines.py
#  Author   : Stephane Grabli
#  Date     : 04/08/2005
#  Purpose  : Draws the lines that are "closer" than a threshold 
#             (between 0 and 1)
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
from PredicatesB1D import *
from PredicatesU1D import *
from shaders import *

upred = AndUP1D(QuantitativeInvisibilityUP1D(0), pyZSmallerUP1D(0.5, IntegrationType.MEAN)) 
Operators.select(upred)
Operators.bidirectionalChain(ChainSilhouetteIterator(), NotUP1D(upred))
shaders_list = 	[
		TextureAssignerShader(-1),
		ConstantThicknessShader(5), 
		ConstantColorShader(0.0, 0.0, 0.0)
		]
Operators.create(TrueUP1D(), shaders_list)
