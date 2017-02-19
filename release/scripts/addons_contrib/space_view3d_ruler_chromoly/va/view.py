# coding: utf-8

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

import re
import math

import bpy
from bpy.props import *
from bpy_extras import *
import bmesh
import mathutils
from mathutils import *
#geo = mathutils.geometry
import blf
import bgl
from bgl import glRectf
from .utils import get_matrix_element_square



MIN_NUMBER = 1E-8
GRID_MIN_PX = 6.0


def check_view(quat, local_grid_rotation=None):
	# 0:Right, 1:Front, 2:Top, 3:Left, 4:Back, 5:Bottom
	vs = ['right', 'front', 'top', 'left', 'back', 'bottom', 'user']
	thr = 1E-5
	si = math.sin(math.radians(45))
	quats = [(0.5, -0.5, -0.5, -0.5), (si, -si, 0., 0.), (1., 0., 0., 0.),
			 (0.5, -0.5, 0.5, 0.5), (0., 0., si, si), (0., 1., 0., 0.)]
	if local_grid_rotation:
		view_quat = local_grid_rotation.inverted()
		for i in range(6):
			quats[i] = Quaternion(quats[i]).cross(view_quat)
	for cnt in range(6):
		if not [1 for i, j in zip(quat, quats[cnt]) if abs(i - j) > thr]:
			return vs[cnt]
		if not [1 for i, j in zip(quat, quats[cnt]) if abs(i + j) > thr]:
			return vs[cnt]
	else:
		return vs[-1]


def check_view_context(context):
	v3d = context.space_data
	rv3d = context.region_data
	if rv3d is None:  # toolパネル上にマウスが有る場合
		if hasattr(context, 'region_data_3d'):	# パッチ。region_dataと違い、常に取得する
			if not v3d.region_quadview:
				rv3d = context.region_data_3d
	if rv3d is None:
		return None
	if hasattr(rv3d, 'view'):
		view_upper_case = rv3d.view
		if view_upper_case in ('PERSPORTHO', 'CAMERA'):
			view = 'user'
		else:
			view = view_upper_case.lower()
	else:
		if hasattr(v3d, 'use_local_grid') and v3d.use_local_grid:
			local_grid_quat = v3d.local_grid_rotation
		else:
			local_grid_quat = None
		viewmat = rv3d.view_matrix
		quat = viewmat.to_3x3().to_quaternion()
		view = check_view(quat, local_grid_quat)
	return view


def get_view_vector(persmat):
	# persmat = context.space_data.region_3d.perspective_matrix
	invpersmat = persmat.inverted()
	v0 = Vector([0, 0, 0]) * invpersmat
	v1 = Vector([0, 0, -1]) * invpersmat
	return (v1 - v0).normalized()


def world_to_window_coordinate(vec, persmat, sx, sy, size=3):
	########### hostile takeover
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d 
	
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, vec)
	if svector == None:
		return Vector([0, 0 ,0])
	else:
		return Vector([svector[0], svector[1], vec[2]])
		
	
	# return float list
	'''
	v = (vec * persmat + Vector([1., 1., 0.])) / 2
	window_pi = [v[0] * sx, v[1] * sy, v[2]]
	return window_pi
	'''
#	v = vec.to_4d()
#	v = v * persmat
#	if v[3] != 0.0:
#		v /= v[3]
#	x = sx / 2 + v[0] * sx / 2
#	y = sy / 2 + v[1] * sy / 2
#	return [x, y, v[2]][:size]


def window_to_world_coordinate(px, py, persmat, sx, sy, pz=0.):
	########### hostile takeover
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d
	depth = rv3d.view_location
	vec = Vector([px, py])
	
	svector = view3d_utils.region_2d_to_location_3d(region, rv3d, vec, depth)
	if svector == None:
		return Vector([0, 0 ,0])
	else:
		return svector
		
	
	#return vector
#	invpmat = persmat.copy()
#	invpmat.invert()
#	v = Vector([float(px) * 2 / sx, float(py) * 2 / sy, pz])
#	vec = v - Vector([1., 1., 0.])
#	vec.resize_4d()
#	vec2 = vec * invpmat
#	if vec2[3] != 0.0:
#		vec2 /= vec2[3]
#	vec2.resize_3d()
#	return vec2


def snap_to_grid(vec, grid_distance,
				 local_grid_origin=None, local_grid_rotation=None):
	local_grid = True if local_grid_rotation and local_grid_origin else False
	if local_grid:
		mat = local_grid_rotation.to_matrix().to_4x4()
		for i in range(3):
			mat[3][i] = local_grid_origin[i]
		imat = mat.inverted()
		vec = vec * imat
	else:
		vec = vec.copy()
	for i in range(3):
		vec[i] = grid_distance * math.floor(0.5 + vec[i] / grid_distance)
	if local_grid:
		vec = vec * mat
	return vec


def values_snap_to_grid(item, context, shift=False, use_local_grid=False):
	'''
	item: type(float, int, list, Vector, list of Vector)
	'''
	dpbu, dx, unit_pow = get_DPBU_dx_unit_pow(context.region)
	grid = 10 ** unit_pow
	if shift:
		grid /= 10
	if use_local_grid:
		v3d = context.space_data
		local_grid_origin = v3d.local_grid_origin
		local_grid_rotation = v3d.local_grid_rotation
		mat = local_grid_rotation.to_matrix().to_4x4()
		for i in range(3):
			mat[3][i] = local_grid_origin[i]
		imat = mat.inverted()

	def snap(val):
		val = grid * math.floor(0.5 + val / grid)
		return val

	def snap_vec(vec):
		if use_local_grid:
			vec = vec * imat
		vec = Vector([snap(f, grid) for f in vec])
		if use_local_grid:
			vec = vec * mat
		return vec

	if isinstance(item, (int, float)):
		return snap(item)
	elif isinstance(item, Vector):
		return snap_vec(item)
	else:
		ls = []
		for val in item:
			if isinstance(val, Vector):
				ls.append(snap_vec(val))
			else:
				ls.append(snap(val))
		return ls

# 新規

def convert_world_to_window(vec, persmat, sx, sy):
	
	########### hostile takeover
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d 
	
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, vec)
	if svector == None:
		return Vector([0, 0 ,0])
	else:
		return Vector([svector[0], svector[1], vec[2]])
		
	
	'''
	vec: sequence
	return Vector
	'''
	#v = vec.to_4d()
#	 v = Vector([vec[0], vec[1], vec[2], 1.0])
 #	 v = v * persmat
  #	 if v[3] != 0.0:
#		 v /= v[3]
 #	 x = sx / 2 + v[0] * sx / 2
  #	 y = sy / 2 + v[1] * sy / 2
   # return Vector([x, y, v[2]])


def convert_window_to_world(vec, persmat, sx, sy):

	########### hostile takeover
	# calculate screencoords of given Vector
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d
	depth = rv3d.view_location
	vec = Vector([vec[0], vec[1]])
	
	svector = view3d_utils.region_2d_to_location_3d(region, rv3d, vec, depth)
	if svector == None:
		return Vector([0, 0 ,0])
	else:
		return svector
		
	
	'''
	vec: sequence
	return Vector
	'''
#	 invpmat = persmat.copy()
#	 invpmat.invert()
#	 v1 = Vector([float(vec[0]) * 2 / sx, float(vec[1]) * 2 / sy, vec[2]])
#	 v2 = v1 - Vector([1., 1., 0.])
#	 v2.resize_4d()
#	 v3 = v2 * invpmat
#	 if v3[3] != 0.0:
#		 v3 /= v3[3]
#	 v3.resize_3d()
#	 return v3


def convert_mouseco_to_window(mouseco, persmat, sx, sy, center):
	'''center: type Vector. cursor_location or view_location
	'''
	vec = convert_world_to_window(center, persmat, sx, sy)
	return Vector([mouseco[0], mouseco[1], vec[2]])


def convert_mouseco_to_world(mouseco, persmat, sx, sy, center):
	'''center: type Vector. cursor_location or view_location
	'''
	vec = convert_mouseco_to_window(mouseco, persmat, sx, sy, center)
	return convert_window_to_world(vec, persmat, sx, sy)


def get_DPBU_dx_unit_pow(region):
	'''画面中心pと、そこからBlenderUnit分だけ画面と平行に移動したqを
	それぞれwindow座標に変換(p,qは共にworld座標)
	'''
	sx = region.width
	sy = region.height
	rv3d = region.region_data
	persmat = rv3d.perspective_matrix
	viewmat = rv3d.view_matrix
	viewinvmat = viewmat.inverted()
	viewloc = rv3d.view_location

	p = viewloc
	if sx >= sy:
		q = viewloc + Vector(viewinvmat[0][:3])
	else:
		q = viewloc + Vector(viewinvmat[1][:3])
	dp = convert_world_to_window(p, persmat, sx, sy)
	dq = convert_world_to_window(q, persmat, sx, sy)
	l = math.sqrt((dp[0] - dq[0]) ** 2 + (dp[1] - dq[1]) ** 2)
	dot_per_blender_unit = dx = l

	#unit = 1.0
	unit_pow = 0
	if dx < GRID_MIN_PX:
		while dx < GRID_MIN_PX:
			dx *= 10
			unit_pow += 1
	else:
		while dx > GRID_MIN_PX * 10:
			dx /= 10
			unit_pow -= 1
	return dot_per_blender_unit, dx, unit_pow


### Input String ##############################################################
class Shortcut:
	def __init__(self, name='', type='', press=True,
				 shift=False, ctrl=False, alt=False, oskey=False,
				 draw_shortcut=True, **kw):
		self.name = name
		self.type = type
		self.press = press
		self.shift = shift
		self.ctrl = ctrl
		self.alt = alt
		self.oskey = oskey
		self.draw_shortcut = draw_shortcut
		for k, v in kw.items():
			setattr(self, k, v)

	def check(self, event):
		if (self.type is None or event.type == self.type):
			if ((event.value == 'PRESS' and self.press is True) or \
				(event.value == 'RELEASE' and self.press is False) or \
				(event.value == 'NOTHING' and self.press is None)):
				if (self.shift is None or event.shift == self.shift) and \
					(self.ctrl is None or event.ctrl == self.ctrl) and \
					(self.alt is None or event.alt == self.alt) and \
					(self.oskey is None or event.oskey == self.oskey):
					return True
		return False

	def label(self):
		if self.draw_shortcut:
			l = []
			if self.shift:
				l.append('Shift + ')
			if self.ctrl:
				l.append('Ctrl + ')
			if self.alt:
				l.append('Alt + ')
			if self.oskey:
				l.append('Oskey + ')
			l.append(self.type.title())
			return ''.join(l)
		else:
			return ''


def check_shortcuts(shortcuts, event, name:'type:str'=None):
	for shortcut in shortcuts:
		if shortcut.check(event):
			if name is not None:
				if name == shortcut.name:
					return shortcut.name
			else:
				return shortcut.name
	return None


class InputExpression:
	'''
	modal内に組み込み、キーボード入力を文字列として格納。
	event: (type:Event)
	exp_strings: 構文 (type:str_list)
	caret: アクティブな構文, カーソル位置 (type:int_list)
	'''
	"""
	event_char = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
						  'abcdefghijklmnopqrstuvwxyz'))

	event_char.update(zip(('ZERO', 'ONE', 'TWO', 'THREE', 'FOUR',
						   'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE'),
						  '0123456789'))
	event_char.update({'NUMPAD_' + val: val for val in '0123456789'})
	event_char.update(zip(('NUMPAD_PERIOD', 'NUMPAD_SLASH', 'NUMPAD_ASTERIX',
						   'NUMPAD_MINUS', 'NUMPAD_PLUS'),
						  './*-+'))
	event_char.update({'SPACE': ' ',
					   'SEMI_COLON': ';', 'PERIOD': '.', 'COMMA': ',',
					   'QUOTE': "'", 'MINUS':'-', 'SLASH':'/',
					   'EQUAL':'=', 'LEFT_BRACKET':'[', 'RIGHT_BRACKET':']'})
	event_char_shift = dict(zip(('ZERO', 'ONE', 'TWO', 'THREE', 'FOUR',
								 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE'),
								'''~!"#$%&'()'''))
	event_char_shift.update({'SEMI_COLON': '+', 'MINUS': '='})
	"""
	event_caret = {'LEFT_ARROW': -1, 'RIGHT_ARROW': 1,
				   'UP_ARROW': -999, 'DOWN_ARROW': 999,
				   'HOME': -999, 'END': 999}
	event_delete = {'DEL':'del', 'BACK_SPACE':'back_space'}

	def __init__(self, names=('Dist',)):
		self.exp_names = list(names)
		self.exp_strings = ['' for i in range(len(names))]
		self.caret = [0, 0]

	def __len__(self):
		return len(self.exp_strings)

	def __getitem__(self, key):
		return self.exp_strings[key]

	def __setitem__(self, key, value):
		self.exp_strings[key] = value

	def __call__(self, index=None):
		if index is None:
			return self.get_exp_values()
		else:
			return self.get_exp_value(index)

	def input(self, event):
		exp_event = True  # メソッドで処理したという事
		if event.value != 'PRESS':
			exp_event = False
			return exp_event

		i, caret = self.caret
		string = self.exp_strings[i]
		if event.type == 'X' and event.ctrl:  # all clear
			if event.shift:
				self.caret[:] = [0, 0]
				for i in range(len(self.exp_strings)):
					self.exp_strings[i] = ''
			else:
				self.caret[1] = 0
				self.exp_strings[self.caret[0]] = ''
		#elif event.type in self.event_char:
		#	 if event.shift:
		#		 char = self.event_char_shift.get(event.type, None)
		#	 else:
		#		 char = self.event_char[event.type]
		#	 if char:
		#		 self.exp_strings[i] = string[:caret] + char + string[caret:]
		#		 self.caret[1] += 1
		#	 else:
		#		 exp_event = False
		elif event.type in self.event_caret:
			caret += self.event_caret[event.type]
			self.caret[1] = min(max(caret, 0), len(string))
		elif event.type in self.event_delete:
			deltype = self.event_delete[event.type]
			if deltype =='del':
				self.exp_strings[i] = string[:caret] + string[caret + 1:]
			elif deltype == 'back_space':
				self.exp_strings[i] = string[:max(0, caret - 1)] + \
									  string[caret:]
				self.caret[1] =	 max(0, caret - 1)
		elif event.type == 'TAB':
			if event.shift or event.ctrl:
				exp_event = False
			else:
				i += 1
				if i >= len(self.exp_strings):
					i = 0
				self.caret[0] = i
				self.caret[1] = len(self.exp_strings[i])
		elif event.ascii:  # バグ潰しが必要
			self.exp_strings[i] = string[:caret] + event.ascii + string[caret:]
			self.caret[1] += 1
		else:
			exp_event = False
		return exp_event

	def get_exp_value(self, index=0):
		val = None
		if self.exp_strings[index]:
			try:
				v = eval(self.exp_strings[index])
				if isinstance(v, (int, float)):
					val = v
			except:
				pass
		return val

	def get_exp_values(self):
		vals = []
		for i in range(len(self.exp_strings)):
			vals.append(self.get_exp_value(i))
		return vals

	def draw_exp_strings(self, font_id, ofsx, ofsy, minwidth=40, \
						 pertition=',  ', start='', end='',
						 col=None, errcol=None):
		if start:
			if col:
				bgl.glColor4f(*col)
			blf.position(font_id, ofsx, ofsy, 0)
			blf.draw(font_id, start)
			text_width, text_height = blf.dimensions(font_id, start)
			ofsx += text_width
		for i, string in enumerate(self.exp_strings):
			value = self.get_exp_value(i)
			if col and value is not None:
				bgl.glColor4f(*col)
			elif errcol and value is None:
				bgl.glColor4f(*errcol)
			name = self.exp_names[i]
			text = name.format(exp=string)
			if len(self.exp_strings) > 1 and 0 < i < len(exp_strings) - 1:
				text = text + pertition
			blf.position(font_id, ofsx, ofsy, 0)
			blf.draw(font_id, text)
			text_width, text_height = blf.dimensions(font_id, text)
			text_width = max(minwidth, text_width)
			# caret
			if i == self.caret[0]:
				if col:
					bgl.glColor4f(*col)
				t = name.split('{')[0] + string[:self.caret[1]]
				t_width, t_height = blf.dimensions(font_id, t)
				x = ofsx + t_width
				glRectf(x, ofsy - 4, x + 1, ofsy + 14)
			ofsx += text_width
			if end and i == len(self.exp_strings) - 1:
				if col:
					bgl.glColor4f(*col)
				blf.position(font_id, ofsx, ofsy, 0)
				blf.draw(font_id, end)


class MouseCoordinate:
	'''
	origin, current, shiftからrelativeを求める。
	relativeをorigin -> lockのベクトルに正射影。

	exptargetsの例:
	exptargets = {'dist': [(self.mc, 'dist', self, 'dist', 0.0),
						   (self.mc.exp, 0, self, 'dist', Null())],
				  'fac': [(self.mc, 'fac', self, 'dist', 0.0),
						  (self.mc.exp, 0, self, 'dist', Null())]}
	set_values()
		引数無しの場合:
			self.exptargetsを全て処理。
		引数をタプルとして受けとった場合:
			例 set_values(self.mc, 'dist', self, 'dist', 0.0)
			これのみ処理。
		引数を辞書として受け取った場合:
			例 set_values(default=False, fac=True)
			キーが存在したらそれを真偽によって処理、
			その他の真偽はdefault(キーが無ければ真)。
	'''

	def __init__(self, context=None, event=None, recalcDPBU=True, dpf=200,
				 expnames=('Dist {exp}',)):
		self.shift = None  # *0.1. type:Vector. relativeに影響。
		self.lock = None  # lock direction. type:Vector. relativeに影響。
		self.snap = False  # type:Bool
		self.origin = Vector()	# Rキーで変更
		self.current = Vector()	 # (event.mouse_region_x, event.mouse_region_y, 0)
		self.relative = Vector()  # shift,lockを考慮
		self.dpbu = 1.0	 # 初期化時、及びupdateの際に指定した場合に更新。
		self.unit_pow = 1.0 # 上記と同様
		self.dist = 0.0	 # relativesnapを考慮
		self.fac = 0.0

		self.inputexp = False
		self.exp = InputExpression(names=expnames)
		#self.finaldist = 0.0  # exp等を考慮した最終的な値
		self.exptargets = {}

		self.shortcuts = []

		if event:
			self.origin = Vector((event.mouse_region_x, event.mouse_region_y, \
								  0.0))
		self.dpf = dpf	# dot per fac
		self.update(context, event, recalcDPBU)

	def set_exptargets(self, exptargets):
		self.exptargets = exptargets

	def set_shortcuts(self, shortcuts):
		''' default: SC = Shortcut
		shortcuts = [SC('lock', 'MIDDLEMOUSE'),
					 SC('reset', 'R'),
		'''
		self.shortcuts = shortcuts

	def set_values(self, *target, **kw):
		if target:
			self.exptargets['targetonly'] = target[0]
		for key, values in self.exptargets.items():
			if target:
				if key != 'targetonly':
					continue
			elif kw:
				if key in kw:
					if not kw[key]:
						continue
				elif 'default' in kw:
					if not kw['default']:
						continue
			for obj, attr, tagobj, tagattr, err in values:
				# read
				if obj == self.exp:	 # (self.exp, index)
					if not self.inputexp:
						continue
					val = self.exp.get_exp_value(attr)
					if val is None:
						if isinstance(err, Null):
							continue
						val = err
				else:
					if isinstance(attr, str):
						val = getattr(obj, attr)
					else:
						val = obj[attr]
				# set
				if isinstance(tagattr, str):
					setattr(tagobj, tagattr, val)
				else:
					tagobj[tagattr] = val
		if target:
			del(self.exptargets['targetonly'])

	def handling_event(self, context, event):
		mouseco = Vector((event.mouse_region_x, event.mouse_region_y, 0.0))

		handled = True
		EXECUTE = True	# execute等を実行後、すぐにreturn {'RUNNING_MODAL'}
		if self.inputexp:  # evalの式の入力
			if event.value == 'PRESS':
				handled_by_exp = self.exp.input(event)
				if handled_by_exp:
					self.set_values()
					return handled, EXECUTE

		shortcut_name = check_shortcuts(self.shortcuts, event)

		if event.type == 'TAB' and event.value == 'PRESS':
			# <Input Expression>
			if self.inputexp and (event.shift or event.ctrl):
				self.inputexp = False
				self.update(context, event)
				self.set_values()
			elif not self.inputexp and not (event.shift or event.ctrl):
				self.inputexp = True
				self.set_values()
			else:
				handled = False
		elif event.type in ('ESC', 'RIGHTMOUSE') and event.value == 'PRESS':
			if self.inputexp:
				self.inputexp = False
				self.update(context, event)
				self.set_values()
			else:
				handled = False
		elif event.type in ('LEFT_SHIFT', 'RIGHT_SHIFT'):
			if event.value == 'PRESS':
				self.shift = mouseco.copy()
			elif event.value == 'RELEASE':
				self.shift = None
				self.update(context, event)
				self.set_values()
			else:
				handled = False
		elif event.type in ('LEFT_CTRL', 'RIGHT_CTRL'):
			if event.value == 'PRESS':
				self.snap = True
			elif event.value == 'RELEASE':
				self.snap = False
			self.update(context, event)
			self.set_values()
		elif event.type == 'MOUSEMOVE':
			# <Move Mouse>
			self.update(context, event)
			self.set_values()
		elif shortcut_name == 'lock':
			# <Lock Trans Axis>
			if self.lock is None:
				self.lock = mouseco.copy()
			else:
				self.lock = None
		elif shortcut_name == 'reset':
			# <Reset>
			if self.lock:
				self.lock = self.lock - self.origin + mouseco
			self.origin = mouseco.copy()
			self.update(context, event)
			self.set_values()
		else:
			handled = False
		return handled, False

	def update(self, context=None, event=None, recalcDPBU=False):
		shift = self.shift
		snap = self.snap
		lock = self.lock
		origin = self.origin

		if event:
			current = Vector((event.mouse_region_x, event.mouse_region_y, 0.0))
		else:
			current = self.current
		if shift:
			relative = shift - origin + (current - shift) * 0.1
		else:
			relative = current - origin
		if lock:
			origin_lock = lock - origin
			if origin_lock.length >= MIN_NUMBER:
				if relative.length >= MIN_NUMBER:
					relative = relative.project(origin_lock)
			else:
				self.lock = None
		if context and recalcDPBU:
			dpbu, dx, unit_pow = get_DPBU_dx_unit_pow(context.region)
		else:
			dpbu, unit_pow = self.dpbu, self.unit_pow

		dist = relative.length / dpbu
		fac = relative.length / self.dpf
		if lock:
			if relative.dot(origin_lock) < 0.0:
				dist = -dist
				fac = -fac
		if snap:
			grid = 10 ** unit_pow
			gridf = 0.1
			if shift:
				grid /= 10
				gridf /= 10
			dist = grid * math.floor(0.5 + dist / grid)
			fac = gridf * math.floor(0.5 + fac / gridf)

		self.current = current
		self.relative = relative
		self.dpbu = dpbu
		self.unit_pow = unit_pow
		self.dist = dist
		self.fac = fac

	def draw_origin(self, radius=5, raydirections=[], raylength=5):
		draw_sun(self.origin[0], self.origin[1], radius, 16, \
				 raydirections, raylength)

	def draw_relative(self, radius=5):
		#if self.shift:
		draw_circle(self.origin[0] + self.relative[0], \
					self.origin[1] + self.relative[1], radius, 16)

	def draw_lock_arrow(self, length=10, angle=math.radians(110)):
		if self.lock is not None:
			lock = self.lock.to_2d()
			origin = self.origin.to_2d()
			vec = (origin - lock).normalized()
			vec *= 20
			vecn = lock + vec
			draw_arrow(vecn[0], vecn[1], lock[0], lock[1], \
					   headlength=length, headangle=angle, headonly=True)

	def draw_factor_circle(self, subdivide=64):
		draw_circle(self.origin[0], self.origin[1], self.dpf, subdivide)



def adapt(selobj):
	
	# This calculation instead of .matrix_world
	# Calculate matrix.
	if selobj.rotation_mode == "AXIS_ANGLE":
		# object rotationmode axisangle
		ang, x, y, z =	selobj.rotation_axis_angle
		matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
	elif selobj.rotation_mode == "QUATERNION":
		# object rotationmode quaternion
		w, x, y, z = selobj.rotation_quaternion
		x = -x
		y = -y
		z = -z
		quat = Quaternion([w, x, y, z])
		matrix = quat.to_matrix()
		matrix.resize_4x4()
	else:
		# object rotationmode euler
		ax, ay, az = selobj.rotation_euler
		mat_rotX = Matrix.Rotation(-ax, 4, 'X')
		mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
		mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
	if selobj.rotation_mode == "XYZ":
		matrix = mat_rotX * mat_rotY * mat_rotZ
	elif selobj.rotation_mode == "XZY":
		matrix = mat_rotX * mat_rotZ * mat_rotY
	elif selobj.rotation_mode == "YXZ":
		matrix = mat_rotY * mat_rotX * mat_rotZ
	elif selobj.rotation_mode == "YZX":
		matrix = mat_rotY * mat_rotZ * mat_rotX
	elif selobj.rotation_mode == "ZXY":
		matrix = mat_rotZ * mat_rotX * mat_rotY
	elif selobj.rotation_mode == "ZYX":
		matrix = mat_rotZ * mat_rotY * mat_rotX

	# handle object scaling
	sx, sy, sz = selobj.scale
	mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
	mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
	mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
	matrix = mat_scX * mat_scY * mat_scZ * matrix
	
	return matrix



### Find nearest Vertex/Edge/Face from Mouse ##################################
def find_nearest_element_from_mouse(context, type='VERTEX', mode='ALL_EMALL'):
	v3d = context.space_data
	cursor = v3d.cursor_location.copy()
	v3d.cursor_location = [float('nan') for i in range(3)]
	bpy.ops.view3d.snap_cursor_to_element('INVOKE_REGION_WIN',
		type=type, use_mouse_cursor=True, mode=mode, redraw=False)
	if not is_nan(v3d.cursor_location[0]):
		vec = v3d.cursor_location.copy()
	else:
		vec = None
	v3d.cursor_location = cursor
	return vec


### Snap ######################################################################
def make_snap_matrix(sx, sy, persmat, snap_to='selected', \
					 snap_to_origin='selected', apply_modifiers=True, \
					 objects=None, subdivide=100):
	'''
	snap_to: ('active', 'selected', 'visible') # snap to mesh & bone
	snap_to_origin: (None, 'none', 'active', 'selected', 'visible', 'objects')\
														 #snap to object origin
	apply_modifiers: (True, False)
	'''
	scn = bpy.context.scene
	actob = bpy.context.active_object
	if objects is None:
		if snap_to == 'active':
			obs = [actob] if actob else []
		elif snap_to == 'selected':
			obs = [ob for ob in bpy.context.selected_objects]
			if actob:
				if actob and actob.mode == 'EDIT' and actob not in obs:
					obs.append(actob)
		else:
			obs = [ob for ob in scn.objects if ob.is_visible(scn)]
	else:
		obs = objects
	# window座標(ドット)に変換したベクトルの二次元配列
	#vmat = [[[] for j in range(subdivide)] for i in range(subdivide)]
	colcnt = int(math.ceil(subdivide * sx / max(sx, sy)))
	rowcnt = int(math.ceil(subdivide * sy / max(sx, sy)))
	vmat = [[[] for c in range(colcnt)] for r in range(rowcnt)]
	vwmat = [[[] for c in range(colcnt)] for r in range(rowcnt)]

	space = bpy.context.space_data
	rv3d = space.region_3d
	eye = Vector(rv3d.view_matrix[2][:3])
	eye.length = rv3d.view_distance
	eyevec = rv3d.view_location + eye
	for ob in obs:
		ob_matrix = adapt(ob)
		obmode = ob.mode
		if obmode == 'EDIT':
			bpy.ops.object.mode_set(mode='OBJECT')

		if ob.type == 'MESH':
			if ob == actob:
				if obmode == 'EDIT' and apply_modifiers and ob.modifiers:
					me = ob.to_mesh(bpy.context.scene, 1, 'PREVIEW')
					meshes = [ob.data, me]
				elif obmode == 'EDIT':
					meshes = [ob.data]
				else:
					meshes = [ob.to_mesh(bpy.context.scene, 1, 'PREVIEW')]
			else:
				meshes = [ob.to_mesh(bpy.context.scene, 1, 'PREVIEW')]
			# ※meshes == local座標
			#me.transform(ob.matrix_world)
			scn = bpy.context.scene
			if eval(str(bpy.app.build_revision)[2:7]) >= 46803:
				hideset = 1
			else:
				hideset = 0
			matrix = adapt(ob)
			eyevec = (eyevec - ob.location) * matrix.inverted()
			for me in meshes:
				bm = bmesh.new()
				bm.from_mesh(me)
				if scn.Verts:
					for v in bm.verts:
						if obmode == 'EDIT' and v.hide == hideset:
							continue
						if space.viewport_shade != "WIREFRAME":
							vno = v.normal
							vno.length = 0.0001
							vco = v.co + vno
							if rv3d.is_perspective:
								hit = ob.ray_cast(vco, eyevec)
							else:
								hit = ob.ray_cast(vco, vco + eye)
							if hit[2] != -1:
								continue
						vw = v.co * ob_matrix
						vw = vw + ob.location
						vec = Vector(world_to_window_coordinate( \
										  vw, persmat, sx, sy))
						if 0 <= vec[0] < sx and 0 <= vec[1] < sy:
							#row = int(vec[1] / sy * subdivide)
							#col = int(vec[0] / sx * subdivide)
							row = int(vec[1] / max(sx, sy) * subdivide)
							col = int(vec[0] / max(sx, sy) * subdivide)
							#if 0 <= row < subdivide and 0 <= col < subdivide:
							vmat[row][col].append(vec)
							vwmat[row][col].append(vw[:])
				if scn.Edges:
					for e in bm.edges:
						if obmode == 'EDIT' and e.hide == hideset:
							continue
						if space.viewport_shade != "WIREFRAME":
							vno = (e.verts[0].normal + e.verts[1].normal) / 2
							vno.length = 0.0001
							vco = (e.verts[0].co + e.verts[1].co) / 2 + vno
							if rv3d.is_perspective:
								hit = ob.ray_cast(vco, eyevec)
							else:
								hit = ob.ray_cast(vco, vco + eye)
							if hit[2] != -1:
								continue
						mw = ((e.verts[0].co + e.verts[1].co)/2) * ob_matrix
						mw = mw + ob.location
						vec = Vector(world_to_window_coordinate( \
										  mw, persmat, sx, sy))
						if 0 <= vec[0] < sx and 0 <= vec[1] < sy:
							#row = int(vec[1] / sy * subdivide)
							#col = int(vec[0] / sx * subdivide)
							row = int(vec[1] / max(sx, sy) * subdivide)
							col = int(vec[0] / max(sx, sy) * subdivide)
							#if 0 <= row < subdivide and 0 <= col < subdivide:
							vmat[row][col].append(vec)
							vwmat[row][col].append(mw[:])
				if scn.Faces:
					for f in bm.faces:
						if obmode == 'EDIT' and f.hide == hideset:
							continue
						if space.viewport_shade != "WIREFRAME":
							fno = f.normal
							fno.length = 0.0001
							fco = f.calc_center_median() + fno
							if rv3d.is_perspective:
								hit = ob.ray_cast(fco, eyevec)
							else:
								hit = ob.ray_cast(fco, fco + eye)
							if hit[2] != -1:
								continue
						mw = f.calc_center_median() * ob_matrix
						mw = mw + ob.location
						vec = Vector(world_to_window_coordinate( \
										  mw, persmat, sx, sy))
						if 0 <= vec[0] < sx and 0 <= vec[1] < sy:
							#row = int(vec[1] / sy * subdivide)
							#col = int(vec[0] / sx * subdivide)
							row = int(vec[1] / max(sx, sy) * subdivide)
							col = int(vec[0] / max(sx, sy) * subdivide)
							#if 0 <= row < subdivide and 0 <= col < subdivide:
							vmat[row][col].append(vec)
							vwmat[row][col].append(mw[:])

		elif ob.type == 'ARMATURE':
			if obmode == 'EDIT':
				bones = ob.data.bones
			else:
				bones = ob.pose.bones
			for bone in bones:
				if obmode == 'EDIT':
					head = bone.head_local
					tail = bone.tail_local
				else:
					head = bone.head
					tail = bone.tail
				for v in (head, tail):
					vw = v * ob_matrix
					vw = vw + ob.location
					vec = Vector(world_to_window_coordinate( \
										 vw, persmat, sx, sy))
					if 0 <= vec[0] < sx and 0 <= vec[1] < sy:
						#row = int(vec[1] / sy * subdivide)
						#col = int(vec[0] / sx * subdivide)
						row = int(vec[1] / max(sx, sy) * subdivide)
						col = int(vec[0] / max(sx, sy) * subdivide)
						#if 0 <= row < subdivide and 0 <= col < subdivide:
						vmat[row][col].append(vec)
						vwmat[row][col].append(vw[:])

		if obmode == 'EDIT':
			bpy.ops.object.mode_set(mode='EDIT')

	# object origins
	if snap_to_origin in (None, 'none'):
		obs_snap_origin = []  # 無し
	elif snap_to_origin == 'active':
		obs_snap_origin = [actob]
	elif snap_to_origin == 'selected':
		obs_snap_origin = [ob for ob in bpy.context.selected_objects]
		if actob:
			if actob.mode == 'EDIT' and actob not in obs:
				obs.append(actob)
	elif snap_to_origin == 'visible':
		obs_snap_origin = [ob for ob in scn.objects if ob.is_visible(scn)]
	else:  # snap_to_origin == 'objects'
		obs_snap_origin = objects
	for ob in obs_snap_origin:
		origin = Vector(ob_matrix[3][:3])
		origin = origin + ob.location
		vec = Vector(world_to_window_coordinate(origin, persmat, sx, sy))
		if 0 <= vec[0] < sx and 0 <= vec[1] < sy:
			#row = int(vec[1] / sy * subdivide)
			#col = int(vec[0] / sx * subdivide)
			row = int(vec[1] / max(sx, sy) * subdivide)
			col = int(vec[0] / max(sx, sy) * subdivide)
			#if 0 <= row < subdivide and 0 <= col < subdivide:
			vmat[row][col].append(vec)
			vwmat[row][col].append(origin)
			
	return vmat, vwmat


def get_vector_from_snap_maxrix(mouseco, max_size, subdivide, snap_vmat, \
								snap_vwmat, snap_range):
	# max_size: max(sx, sy)
	snap_vec = snap_vec_len = snap_vecw = None
	center = (int(mouseco[1] / max_size * subdivide), \
			  int(mouseco[0] / max_size * subdivide))
	#find_before_loop = 0
	r = 0
	find = 0
	#while i <= math.ceil(snap_range / max_size * subdivide)
	#for r in range(int(math.ceil(snap_range / subdivide)) + 1):
	while True:
		for l in get_matrix_element_square(snap_vmat, snap_vwmat, center, r):
			if not l:
				continue
			for idx in range(len(l[0])):
				v = l[0][idx]
				vw = l[1][idx]
				vec = Vector([v[0] - mouseco[0], v[1] - mouseco[1]])
				vec_len = vec.length
				if vec_len <= snap_range:
					if snap_vec_len is None:
						snap_vec_len = vec_len
						snap_vec = v
						snap_vecw = vw
						#break
						find = max(find, 1)
					elif vec_len < snap_vec_len:
						snap_vec_len = vec_len
						snap_vec = v
						snap_vecw = vw
						find = max(find, 1)
			#if snap_vec:
			#	 break
		if r > snap_range / max_size * subdivide:
			break
		if find == 1:
			find = 2
		elif find == 2:
			break
		r += 1
	return snap_vec, snap_vecw

"""
def get_viewmat_and_viewname(context):
	# viewmat not has location

	'''
	viewmat <- invert() -> emptymat
	1.world-coordinate: me.transform(ob.matrix)
	2a.empty-base-coordinate: me.transform(viewmat)
	2b.empty-base-coordinate: me.transform(emptymat.inverted())
	2Dvecs = [v.co.to_2d() for v in me.vertices]
	'''

	'''
	# 蛇使い
	view_mat = context.space_data.region_3d.perspective_matrix # view matrix
	ob_mat = context.active_object.matrix # object world space matrix
	total_mat = view_mat*ob_mat # combination of both matrices

	loc = v.co.to_4d() # location vector resized to 4 dimensions
	vec = loc*total_mat # multiply vector with matrix
	vec = mathutils.Vector((vec[0]/vec[3],vec[1]/vec[3],vec[2]/vec[3])) # dehomogenise vector

	# result (after scaling to viewport)
	x = int(mid_x + vec[0]*width/2.0)
	y = int(mid_y + vec[1]*height/2.0)
	#mid_x and mid_y are the center points of the viewport, width and height are the sizes of the viewport.
	'''

	scn = context.scene
	ob = context.active_object
	ob_selected = ob.select

	# add empty object
	l = [True for i in range(32)]
	bpy.ops.object.add(type='EMPTY', view_align=True,
					   location = (0,0,0), layer=l)	 # 原点
	ob_empty = context.active_object

	# check localgrid
	space3dview = context.space_data  # Space3DView
	try:
		use_local_grid = space3dview.use_local_grid
	except:
		use_local_grid = False
	if use_local_grid:
		local_grid_rotation = space3dview.local_grid_rotation
		local_grid_origin = space3dview.local_grid_origin
	else:
		local_grid_rotation = local_grid_origin = None

	# check view
	mat = ob_empty.matrix_world.to_3x3().transposed()
	quat = mat.to_quaternion()
	view = check_view(quat, local_grid_rotation)

	# cleanup
	scn.objects.unlink(ob_empty)
	scn.objects.active = ob
	ob.select = ob_selected
	scn.update()

	return mat, view
"""
