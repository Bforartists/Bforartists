# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
########################################################
#
# Before changing this file please discuss with admins.
#
########################################################
# <pep8 compliant>

import bpy
from bpy.props import *
import math
import mathutils as Math
from mathutils import Matrix, Euler, Vector, Quaternion

### Save Properties ###########################################################
class SaveProperties:
	def __init__(self):
		self.data = {}

	def update(self, operator, attrs=None):
		name = operator.__class__.bl_idname
		vals = self.data.setdefault(name, {})
		if attrs is not None:
			for attr in attrs:

				val = getattr(operator, attr, None)
				if hasattr(val, '__iter__'):
					val = val[:]
				vals[attr] = val
		else:
			for attr in vals.keys():
				val = getattr(operator, attr, None)
				if hasattr(val, '__iter__'):
					val = val[:]
				vals[attr] = val

	def read(self, operator, attrs=None):
		name = operator.__class__.bl_idname
		if name in self.data:
			if attrs is not None:
				for attr in attrs:
					if attr in self.data[name]:
						setattr(operator, attr, self.data[name][attr])
					else:
						if hasattr(operator, attr):
							self.data[name][attr] = getattr(operator, attr)
						else:
							self.data[name][attr] = None
							setattr(operator, attr, None)
			else:
				for attr, value in self.data[name].items():
					setattr(operator, attr, value)
		else:
			self.update(operator, attrs)

	def get(self, operator, attr):
		name = operator.__class__.bl_idname
		if name in self.data:
			if attr in self.data[name]:
				return self.data[name][attr]
		return None

	def set(self, operator, attr, value):
		name = operator.__class__.bl_idname
		if hasattr(value, '__iter__'):
			value = value[:]
		if name in self.data:
			self.data[name][attr] = value
		else:
			self.data[name] = {attr: value}


op_prop_values = SaveProperties()

class WatchProperties:
	'''?????????????????????
	'''
	def __init__(self, operator, attrs):
		self.operator = operator
		self.attrs = attrs
		for attr in attrs:
			setattr(self, attr, getattr(operator, attr))
	def update(self):
		operator = self.operator
		changed = set()
		for attr in self.attrs:
			if getattr(self, attr) != getattr(operator, attr):
				changed.add(attr)
			setattr(self, attr, getattr(operator, attr))
		return changed

def get_matrix_element_square(mat, wmat, center, r):
	i = [center[0] - r, center[1] - r]
	cnt = 0
	while True:
		if cnt != 0 and cnt >= 8 * r:
			raise StopIteration
		if 0 <= i[0] < len(mat) and 0 <= i[1] < len(mat[0]):
			yield [mat[i[0]][i[1]], wmat[i[0]][i[1]]]
		if cnt < 2 * r:
			i[1] += 1
		elif cnt < 4 * r:
			i[0] += 1
		elif cnt < 6 * r:
			i[1] -= 1
		elif cnt < 8 * r:
			i[0] -= 1
		cnt += 1
		

### Utils #####################################################################
class Null():
	def __init__(self):
		pass

def axis_angle_to_quat(axis, angle):
	q = Math.Quaternion([1.0, 0.0, 0.0, 0.0])
	if axis.length == 0.0:
		return None
	nor = axis.normalized()
	si = math.sin(angle / 2)
	q.w = math.cos(angle / 2)
	v = nor * si
	q.x = v.x
	q.y = v.y
	q.z = v.z

	return q

def the_other(ls, item):
	return ls[ls.index(item) - 1]

def print_event(event):
	if event.type == 'NONE':
		return
	modlist = []
	if event.ctrl:
		modlist.append('ctrl')
	if event.shift:
		modlist.append('shift')
	if event.alt:
		modlist.append('alt')
	if event.oskey:
		modlist.append('oskey')
	mods = ' + '.join(modlist)

	if event.type in ('MOUSEMOVE'):
		if modlist:
			print(mods)
	else:
		if event.value == 'PRESS':
			if event.type not in('LEFT_SHIFT', 'RIGHT_SHIFT',
								 'LEFT_CTRL', 'RIGHT_CTRL',
								 'LEFT_ALT', 'RIGHT_ALT', 'COMMAND'):
				if mods:
					text = mods + ' + ' + event.type
				else:
					text = event.type
				print(text)
