#
#  Filename : external_contour_sketchy.py
#  Author   : Stephane Grabli
#  Date     : 04/08/2005
#  Purpose  : Draws the external contour of the scene using a sketchy 
#             chaining iterator (in particular each ViewEdge can be drawn 
#             several times
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


from Freestyle import *
from logical_operators import *
from ChainingIterators import *
from shaders import *


upred = AndUP1D(QuantitativeInvisibilityUP1D(0), ExternalContourUP1D()) 
Operators.select(upred)
Operators.bidirectionalChain(pySketchyChainingIterator(), NotUP1D(upred))
shaders_list = 	[
		SamplingShader(4),
		SpatialNoiseShader(10, 150, 2, 1, 1), 
		IncreasingThicknessShader(4, 10), 
		SmoothingShader(400, 0.1, 0, 0.2, 0, 0, 0, 1),
		IncreasingColorShader(1,0,0,1,0,1,0,1),
		TextureAssignerShader(4)
		]
Operators.create(TrueUP1D(), shaders_list)
