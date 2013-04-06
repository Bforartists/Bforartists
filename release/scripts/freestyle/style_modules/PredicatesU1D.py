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

#  Filename : PredicatesU1D.py
#  Authors  : Fredo Durand, Stephane Grabli, Francois Sillion, Emmanuel Turquin 
#  Date     : 08/04/2005
#  Purpose  : Unary predicates (functors) to be used for 1D elements

from Freestyle import Curvature2DAngleF0D, CurveNatureF1D, DensityF1D, GetCompleteViewMapDensityF1D, \
    GetDirectionalViewMapDensityF1D, GetOccludersF1D, GetProjectedZF1D, GetShapeF1D, GetSteerableViewMapDensityF1D, \
    IntegrationType, ShapeUP1D, TVertex, UnaryPredicate1D
from Functions1D import pyDensityAnisotropyF1D, pyViewMapGradientNormF1D

class pyNFirstUP1D(UnaryPredicate1D):
	def __init__(self, n):
		UnaryPredicate1D.__init__(self)
		self.__n = n
		self.__count = 0
	def __call__(self, inter):
		self.__count = self.__count + 1
		if self.__count <= self.__n:
			return 1
		return 0

class pyHigherLengthUP1D(UnaryPredicate1D):
	def __init__(self,l):
		UnaryPredicate1D.__init__(self)
		self._l = l
	def __call__(self, inter):
		return (inter.length_2d > self._l)

class pyNatureUP1D(UnaryPredicate1D):
	def __init__(self,nature):
		UnaryPredicate1D.__init__(self)
		self._nature = nature
		self._getNature = CurveNatureF1D()
	def __call__(self, inter):
		if(self._getNature(inter) & self._nature):
			return 1
		return 0

class pyHigherNumberOfTurnsUP1D(UnaryPredicate1D):
	def __init__(self,n,a):
		UnaryPredicate1D.__init__(self)
		self._n = n
		self._a = a
	def __call__(self, inter):
		count = 0
		func = Curvature2DAngleF0D()
		it = inter.vertices_begin()
		while not it.is_end:
			if func(it) > self._a:
				count = count+1
			if count > self._n:
				return 1
			it.increment()
		return 0

class pyDensityUP1D(UnaryPredicate1D):
	def __init__(self,wsize,threshold, integration = IntegrationType.MEAN, sampling=2.0):
		UnaryPredicate1D.__init__(self)
		self._wsize = wsize
		self._threshold = threshold
		self._integration = integration
		self._func = DensityF1D(self._wsize, self._integration, sampling)
	def __call__(self, inter):
		if self._func(inter) < self._threshold:
			return 1
		return 0

class pyLowSteerableViewMapDensityUP1D(UnaryPredicate1D):
	def __init__(self,threshold, level,integration = IntegrationType.MEAN):
		UnaryPredicate1D.__init__(self)
		self._threshold = threshold
		self._level = level
		self._integration = integration
	def __call__(self, inter):
		func = GetSteerableViewMapDensityF1D(self._level, self._integration)
		v = func(inter)
		print(v)
		if v < self._threshold:
			return 1
		return 0

class pyLowDirectionalViewMapDensityUP1D(UnaryPredicate1D):
	def __init__(self,threshold, orientation, level,integration = IntegrationType.MEAN):
		UnaryPredicate1D.__init__(self)
		self._threshold = threshold
		self._orientation = orientation
		self._level = level
		self._integration = integration
	def __call__(self, inter):
		func = GetDirectionalViewMapDensityF1D(self._orientation, self._level, self._integration)
		v = func(inter)
		#print(v)
		if v < self._threshold:
			return 1
		return 0

class pyHighSteerableViewMapDensityUP1D(UnaryPredicate1D):
	def __init__(self,threshold, level,integration = IntegrationType.MEAN):
		UnaryPredicate1D.__init__(self)
		self._threshold = threshold
		self._level = level
		self._integration = integration
		self._func = GetSteerableViewMapDensityF1D(self._level, self._integration)	
	def __call__(self, inter):
		v = self._func(inter)
		if v > self._threshold:
			return 1
		return 0

class pyHighDirectionalViewMapDensityUP1D(UnaryPredicate1D):
	def __init__(self,threshold, orientation, level,integration = IntegrationType.MEAN, sampling=2.0):
		UnaryPredicate1D.__init__(self)
		self._threshold = threshold
		self._orientation = orientation
		self._level = level
		self._integration = integration
		self._sampling = sampling		
	def __call__(self, inter):
		func = GetDirectionalViewMapDensityF1D(self._orientation, self._level, self._integration, self._sampling)
		v = func(inter)
		if v > self._threshold:
			return 1
		return 0

class pyHighViewMapDensityUP1D(UnaryPredicate1D):
	def __init__(self,threshold, level,integration = IntegrationType.MEAN, sampling=2.0):
		UnaryPredicate1D.__init__(self)
		self._threshold = threshold
		self._level = level
		self._integration = integration
		self._sampling = sampling
		self._func = GetCompleteViewMapDensityF1D(self._level, self._integration, self._sampling) # 2.0 is the smpling
	def __call__(self, inter):
		#print("toto")
		#print(func.name)
		#print(inter.name)
		v= self._func(inter)
		if v > self._threshold:
			return 1
		return 0

class pyDensityFunctorUP1D(UnaryPredicate1D):
	def __init__(self,wsize,threshold, functor, funcmin=0.0, funcmax=1.0, integration = IntegrationType.MEAN):
		UnaryPredicate1D.__init__(self)
		self._wsize = wsize
		self._threshold = float(threshold)
		self._functor = functor
		self._funcmin = float(funcmin)
		self._funcmax = float(funcmax)
		self._integration = integration
	def __call__(self, inter):
		func = DensityF1D(self._wsize, self._integration)
		res = self._functor(inter)
		k = (res-self._funcmin)/(self._funcmax-self._funcmin)
		if func(inter) < self._threshold*k:
			return 1
		return 0

class pyZSmallerUP1D(UnaryPredicate1D):
	def __init__(self,z, integration=IntegrationType.MEAN):
		UnaryPredicate1D.__init__(self)
		self._z = z
		self._integration = integration
	def __call__(self, inter):
		func = GetProjectedZF1D(self._integration)
		if func(inter) < self._z:
			return 1
		return 0

class pyIsOccludedByUP1D(UnaryPredicate1D):
	def __init__(self,id):
		UnaryPredicate1D.__init__(self)
		self._id = id
	def __call__(self, inter):
		func = GetShapeF1D()
		shapes = func(inter)
		for s in shapes:
			if(s.id == self._id):
				return 0
		it = inter.vertices_begin()
		itlast = inter.vertices_end()
		itlast.decrement()
		v =  it.object
		vlast = itlast.object
		tvertex = v.viewvertex
		if type(tvertex) is TVertex:
			print("TVertex: [ ", tvertex.id.first, ",",  tvertex.id.second," ]")
			eit = tvertex.edges_begin()
			while not eit.is_end:
				ve, incoming = eit.object
				if ve.id == self._id:
					return 1
				print("-------", ve.id.first, "-", ve.id.second)
				eit.increment()
		tvertex = vlast.viewvertex
		if type(tvertex) is TVertex:
			print("TVertex: [ ", tvertex.id.first, ",",  tvertex.id.second," ]")
			eit = tvertex.edges_begin()
			while not eit.is_end:
				ve, incoming = eit.object
				if ve.id == self._id:
					return 1
				print("-------", ve.id.first, "-", ve.id.second)
				eit.increment()
		return 0

class pyIsInOccludersListUP1D(UnaryPredicate1D):
	def __init__(self,id):
		UnaryPredicate1D.__init__(self)
		self._id = id
	def __call__(self, inter):
		func = GetOccludersF1D()
		occluders = func(inter)
		for a in occluders:
			if a.id == self._id:
				return 1
		return 0

class pyIsOccludedByItselfUP1D(UnaryPredicate1D):
	def __init__(self):
		UnaryPredicate1D.__init__(self)
		self.__func1 = GetOccludersF1D()
		self.__func2 = GetShapeF1D()
	def __call__(self, inter):
		lst1 = self.__func1(inter)
		lst2 = self.__func2(inter)
		for vs1 in lst1:
			for vs2 in lst2:
				if vs1.id == vs2.id:
					return 1
		return 0

class pyIsOccludedByIdListUP1D(UnaryPredicate1D):
	def __init__(self, idlist):
		UnaryPredicate1D.__init__(self)
		self._idlist = idlist
		self.__func1 = GetOccludersF1D()
	def __call__(self, inter):
		lst1 = self.__func1(inter)
		for vs1 in lst1:
			for _id in self._idlist:
				if vs1.id == _id:
					return 1
		return 0

class pyShapeIdListUP1D(UnaryPredicate1D):
	def __init__(self,idlist):
		UnaryPredicate1D.__init__(self)
		self._idlist = idlist
		self._funcs = []
		for _id in idlist :
			self._funcs.append(ShapeUP1D(_id.first, _id.second))
	def __call__(self, inter):
		for func in self._funcs :
			if func(inter) == 1:
				return 1
		return 0

## deprecated
class pyShapeIdUP1D(UnaryPredicate1D):
	def __init__(self, _id):
		UnaryPredicate1D.__init__(self)
		self._id = _id
	def __call__(self, inter):
		func = GetShapeF1D()
		shapes = func(inter)
		for a in shapes:
			if a.id == self._id:
				return 1
		return 0

class pyHighDensityAnisotropyUP1D(UnaryPredicate1D):
	def __init__(self,threshold, level, sampling=2.0):
		UnaryPredicate1D.__init__(self)
		self._l = threshold
		self.func = pyDensityAnisotropyF1D(level, IntegrationType.MEAN, sampling)
	def __call__(self, inter):
		return (self.func(inter) > self._l)

class pyHighViewMapGradientNormUP1D(UnaryPredicate1D):
	def __init__(self,threshold, l, sampling=2.0):
		UnaryPredicate1D.__init__(self)
		self._threshold = threshold
		self._GetGradient = pyViewMapGradientNormF1D(l, IntegrationType.MEAN)
	def __call__(self, inter):
		gn = self._GetGradient(inter)
		#print(gn)
		return (gn > self._threshold)

class pyDensityVariableSigmaUP1D(UnaryPredicate1D):
	def __init__(self,functor, sigmaMin,sigmaMax, lmin, lmax, tmin, tmax, integration = IntegrationType.MEAN, sampling=2.0):
		UnaryPredicate1D.__init__(self)
		self._functor = functor
		self._sigmaMin = float(sigmaMin)
		self._sigmaMax = float(sigmaMax)
		self._lmin = float(lmin)
		self._lmax = float(lmax)
		self._tmin = tmin
		self._tmax = tmax
		self._integration = integration
		self._sampling = sampling
	def __call__(self, inter):
		sigma = (self._sigmaMax-self._sigmaMin)/(self._lmax-self._lmin)*(self._functor(inter)-self._lmin) + self._sigmaMin
		t = (self._tmax-self._tmin)/(self._lmax-self._lmin)*(self._functor(inter)-self._lmin) + self._tmin
		if sigma < self._sigmaMin:
			sigma = self._sigmaMin
		self._func = DensityF1D(sigma, self._integration, self._sampling)
		d = self._func(inter)
		if d < t:
			return 1
		return 0

class pyClosedCurveUP1D(UnaryPredicate1D):
	def __call__(self, inter):
		it = inter.vertices_begin()
		itlast = inter.vertices_end()
		itlast.decrement()	
		vlast = itlast.object
		v = it.object
		print(v.id.first, v.id.second)
		print(vlast.id.first, vlast.id.second)
		if v.id == vlast.id:
			return 1
		return 0
