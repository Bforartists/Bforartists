from freestyle_init import *
from logical_operators import *
from PredicatesU1D import *
from PredicatesU0D import *
from PredicatesB1D import *
from Functions0D import *
from Functions1D import *
from shaders import *

Operators.select(QuantitativeInvisibilityUP1D(0))
Operators.bidirectional_chain(ChainSilhouetteIterator())
#Operators.sequential_split(pyVertexNatureUP0D(Nature.VIEW_VERTEX), 2)
Operators.sort(pyZBP1D())
shaders_list = 	[
		StrokeTextureShader("smoothAlpha.bmp", Stroke.OPAQUE_MEDIUM, False),
		ConstantThicknessShader(3), 
		SamplingShader(5.0),
		ConstantColorShader(0,0,0,1)
		]
Operators.create(pyDensityUP1D(2,0.05, IntegrationType.MEAN,4), shaders_list)
#Operators.create(pyDensityFunctorUP1D(8,0.03, pyGetInverseProjectedZF1D(), 0,1, IntegrationType.MEAN), shaders_list)

