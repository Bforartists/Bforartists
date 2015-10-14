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

bl_info = {
	'name': 'Ruler',
	'author': 'chromoly - adapted for 2.63 by Gert De Roost',
	'version': (2, 3, 0),
	'blender': (2, 63, 0),
	'location': 'View3D > Properties > Ruler',
	'category': '3D View'}

'''
Pour afficher la règle en 3D Voir.
Pour utiliser le patch la fonctionnalité complète sera nécessaire.
'''


import time	 # debug
from functools import reduce
from collections import OrderedDict
import math

import bpy
from bpy.props import *
import bgl
from bgl import glEnable, glDisable, GL_BLEND, \
				GL_LINES, GL_LINE_LOOP, GL_LINE_STRIP, GL_TRIANGLES, \
				glBegin, glEnd, glColor4f, glLineWidth, glRectf, glVertex2f, \
				glLineStipple, GL_LINE_STIPPLE
import mathutils
from mathutils import *
geo = mathutils.geometry
intersect_line_line_2d = geo.intersect_line_line_2d
import blf

from .va.view import check_view, check_view_context, \
					make_snap_matrix, get_vector_from_snap_maxrix, \
					convert_world_to_window, convert_window_to_world, window_to_world_coordinate
from .va.utils import get_matrix_element_square
from .va.gl import draw_box, draw_triangles, draw_triangle_relative, \
				  draw_circle, draw_arc12

import copy
# from va.utils import print_mat

debug = 0
globmx = 0
globmy = 0
started = 0
cursorstate = 0
snapon = snapon3d = 0

class TmpClass():
	def __init__(self, d=None):
		if isinstance(d, (dict, OrderedDict)):
			self.__dict__.update(d)


# Valeur utilisée pour initialiser
default_config = d = OrderedDict()	# OrderedDict  Il y avait pas de besoin d'utiliser particulier
d['color_background'] = [0, 0, 0, 1]
d['scale_size'] = [5, 4, 4]	 # (10 Mémoire, le nombre pair, l'impair) de la taille de la mémoire
d['number_min_px'] = [18, 40]
# 36 # Affiche un nombre dans la position de la (ou grille minimum) de grille minimum de 5 *
# devient plus grande que cette valeur (.) taille minimale de la grille.
d['draw_mouse_coordinate'] = 1	# 0:off, 1:on Patched pour afficher les coordonnées de la souris.
d['autohide_mouse_coordinate'] = 1
d['autohide_MC_threthold'] = 2	# -1:off, Comme valeur de seuil: supérieur ou égal à 0.
# masquer l'affichage des coordonnées lors des approches de la souris.
#d['font_main'] = [0, 10, 72, 3]  #(id, size, dpi, offset)
d['font_main'] = TmpClass({'id':0, 'size':10, 'dpi':72, 'offset':3})
d['font_mc'] = TmpClass({'id':0, 'size':12, 'dpi':72, 'offset':3})	# mouse coordinate box
d['font_measure'] = TmpClass({'id':0, 'size':10, 'dpi':72, 'offset':3}) # measure mode
d['cursor_type'] = 'cross_scale'  # enum['none', 'cross', 'cross_scale']0 Patched pour
d['cursor_scale_size'] = [12, 6, 2]	 # La taille de la mémoire (main, sub1, sub2)
d['measure_cursor_scale_size'] = [16, 6, 6]	 # La taille de la mémoire (main, sub1, sub2)
d['measure_scale_size'] = [14, 5, 5]  # draw measure.rulers
d['measure_select_point_threthold'] = 30  # MeasureMode Temps, la distance peut être sélectionné par un clic-droit
d['draw_scale_type'] = 1  # 0:offz, 1:on Affichage dans le coin supérieur droit
d['draw_unit'] = 1	# 0:offz, 1:on Affichage dans le coin inférieur droit, la plus petite grille minutes BlenderUnit
d['color_main'] = [1.0, 1.0, 0.2, 1.0]	# [r, g, b, a]
d['color_number'] = d['color_main']
d['color_cursor'] = [1.0, 1.0, 1.0, 0.3]
d['color_cursor_bold'] = [1.0, 1.0, 1.0, 1.0]
#d['color_cursor_number'] = [1.0, 1.0, 1.0, 1.0]  # inutilisé
d['color_measure'] = [0.9, 1.0, 0.7, 0.6]
d['color_measure_sub'] = [0.9, 1.0, 0.7, 0.3]  # ligne auxiliaire & ruler.draw_circle
d['color_measure_number'] = [0.9, 1.0, 1.0, 1.0]
d['color_measure_angle'] = [1.0, 0.7, 0.7, 1.0]
d['color_measure_cursor'] = d['color_measure']
d['color_measure_cursor_bold'] = [0.9, 1.0, 0.7, 0.8]
d['color_measure_alpha'] = 0.8


class FontMain(bpy.types.PropertyGroup):
	'''
	Note: Lorsque vous héritez de cette classe en outre, toutes les méthodes vont disparaître.
	'''
	id = IntProperty(name='ID',
					 default=default_config['font_main'].id,
					 min=0, max=100, soft_min=0, soft_max=100)
	size = IntProperty(name='Size',
					   default=default_config['font_main'].size,
					   min=1, max=100, soft_min=1, soft_max=100)
	dpi = IntProperty(name='DPI',
					  default=default_config['font_main'].dpi,
					  min=1, max=300, soft_min=1, soft_max=300)
	offset = IntProperty(name='Offset',
						 default=default_config['font_main'].offset,
						 min=0, max=100, soft_min=0, soft_max=100)

class FontMC(bpy.types.PropertyGroup):
	id = IntProperty(name='ID',
					 default=default_config['font_mc'].id,
					 min=0, max=100, soft_min=0, soft_max=100)
	size = IntProperty(name='Size',
					   default=default_config['font_mc'].size,
					   min=1, max=100, soft_min=1, soft_max=100)
	dpi = IntProperty(name='DPI',
					  default=default_config['font_mc'].dpi,
					  min=1, max=300, soft_min=1, soft_max=300)
	offset = IntProperty(name='Offset',
						 default=default_config['font_mc'].offset,
						 min=0, max=100, soft_min=0, soft_max=100)

class FontMeasure(bpy.types.PropertyGroup):
	id = IntProperty(name='ID',
					 default=default_config['font_measure'].id,
					 min=0, max=100, soft_min=0, soft_max=100)
	size = IntProperty(name='Size',
					   default=default_config['font_measure'].size,
					   min=1, max=100, soft_min=1, soft_max=100)
	dpi = IntProperty(name='DPI',
					  default=default_config['font_measure'].dpi,
					  min=1, max=300, soft_min=1, soft_max=300)
	offset = IntProperty(name='Offset',
						 default=default_config['font_measure'].offset,
						 min=0, max=100, soft_min=0, soft_max=100)


def blf_text_height_max(fontid):
		text_width, text_height = blf.dimensions(fontid,
							  reduce(lambda x, y: x+chr(y), range(32, 127), ''))
		return text_height

class RulerConfig(bpy.types.PropertyGroup):
	# IntVectorProporty Ne peut être utilisé en raison d'un bug
	color_background = FloatVectorProperty(attr='color_background', name='Back',
									default=default_config['color_background'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_main = FloatVectorProperty(attr='color_main', name='Main',
									default=default_config['color_main'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_number = FloatVectorProperty(attr='color_number', name='Number',
									default=default_config['color_number'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_cursor = FloatVectorProperty(attr='color_cursor', name='Cursor',
									default=default_config['color_cursor'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_cursor_bold = FloatVectorProperty(attr='color_cursor_bold', name='Cursor Bold',
									default=default_config['color_cursor_bold'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure = FloatVectorProperty(attr='color_measure', name='Measure',
									default=default_config['color_measure'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure_sub = FloatVectorProperty(attr='color_measure_sub', name='M-Sub',
									default=default_config['color_measure_sub'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure_number = FloatVectorProperty(attr='color_measure_number',
									name='M-Number',
									description='Measure number',
									default=default_config['color_measure_number'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure_angle = FloatVectorProperty(attr='color_measure_angle', name='M-Angle',
									description='Measure angle number',
									default=default_config['color_measure_angle'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure_cursor = FloatVectorProperty(attr='color_measure_cursor',
									name='M-Cursor',
									default=default_config['color_measure_cursor'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure_cursor_bold = FloatVectorProperty(attr='color_measure_cursor_bold',
									name='M-Cursor Bold',
									default=default_config['color_measure_cursor_bold'],
									min=0., max=1., soft_min=0., soft_max=1.,
									subtype='COLOR', size=4)
	color_measure_alpha = FloatProperty(attr='color_measure_alpha',
							  name='Alpha in Normal Mode',
							  default=default_config['color_measure_alpha'],
							  min=0., max=1., soft_min=0., soft_max=1.,
							  subtype='PERCENTAGE')

	font_main = PointerProperty(attr='font_main', name='font main', type=FontMain)
	font_mc = PointerProperty(attr='font_mc', name='font MC', type=FontMC)
	font_measure = PointerProperty(attr='font_measure', name='font measure', type=FontMeasure)

	scale_size = FloatVectorProperty(attr='scale_size', name='Scale size',
									default=default_config['scale_size'],
									min=0, max=40, soft_min=0, soft_max=40,
									step=100, size=3)
	number_min_px = FloatVectorProperty(attr='number_min_px', name='Number min px',
									description='(5, 1)',
									default=default_config['number_min_px'],
									min=6, max=60, soft_min=6, soft_max=60,
									step=100, size=2)
	draw_mouse_coordinate = BoolProperty(attr='draw_mouse_coordinate',
							 name='Draw mouse coordinate',
							 default=default_config['draw_mouse_coordinate'])
	autohide_mouse_coordinate = BoolProperty(attr='autohide_mouse_coordinate',
							 name='Autohide MC',
							 default=default_config['autohide_mouse_coordinate'])
	autohide_MC_threthold = IntProperty(attr='autohide_MC_threthold',  # 'autohide_mouse_coordinate_threthold' est faux trop longtemps
							name='Thretholed',
							default=default_config['autohide_MC_threthold'],
							min=0, max=100, soft_min=0, soft_max=100)

	cursor_type = EnumProperty(attr='cursor_type',
							 name='Cursor type',
							 items=(('none', 'None', ''),
									('cross', 'Cross Line', ''),
									('cross_scale', 'Cross Line & Scale', '')),
							 default=str(default_config['cursor_type']))
	cursor_scale_size = FloatVectorProperty(attr='cursor_scale_size',
									name='Cursor scale size',
									default=default_config['cursor_scale_size'],
									min=0, max=40, soft_min=0, soft_max=40,
									step=100, size=3)
	measure_cursor_scale_size = FloatVectorProperty(attr='measure_cursor_scale_size',
									name='Measure cursor scale size',
									default=default_config['measure_cursor_scale_size'],
									min=0, max=40, soft_min=0, soft_max=40,
									step=100, size=3)
	measure_scale_size = FloatVectorProperty(attr='measure_scale_size',
									name='Measure scale size',
									default=default_config['measure_scale_size'],
									min=0, max=40, soft_min=0, soft_max=40,
									step=100, size=3)
	measure_select_point_threthold = IntProperty(attr='measure_select_point_threthold',
							name='Measure_R-Click threthold',
							default=default_config['measure_select_point_threthold'],
							min=0, max=60, soft_min=0, soft_max=60)
	draw_scale_type = BoolProperty(attr='draw_scale_type',
							 name='Draw scale type',
							 default=default_config['draw_scale_type'])
	draw_unit = BoolProperty(attr='draw_unit',
							 name='Draw unit',
							 default=default_config['draw_unit'])
	scene = StringProperty(attr='scene', name='Scene')

	def config_check(self):
		if not hasattr(bpy.context.window, 'event'): # patch disponible après application
			self.cursor_type = 'none'
			self.draw_mouse_coordinate = True
			return False
		return True


class VIEW3D_OT_ruler_config_reset(bpy.types.Operator):
	'''reset current config'''
	bl_idname = 'view3d.ruler_config_reset'
	bl_label = 'Reset Ruler Config'
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		config = context.scene.ruler_config
		tmp_class = TmpClass(d)
		copy_ruler_config(config, tmp_class)
		config.color_background = FloatVectorProperty(attr='color_background', name='Back',
										default=d['color_background'],
										min=0., max=1., soft_min=0., soft_max=1.,
										subtype='COLOR', size=4)
		return {'FINISHED'}


def copy_ruler_config(config, source, copy_font=True):
	c = config
	cc = source
	c.color_main = cc.color_main
	c.color_number = cc.color_number
	c.color_background = cc.color_background
	c.color_cursor = cc.color_cursor
	c.color_cursor_bold = cc.color_cursor_bold
	c.color_measure = cc.color_measure
	c.color_measure_sub = cc.color_measure_sub
	c.color_measure_number = cc.color_measure_number
	c.color_measure_angle = cc.color_measure_angle
	c.color_measure_cursor = cc.color_measure_cursor
	c.color_measure_cursor_bold = cc.color_measure_cursor_bold
	c.color_measure_alpha = cc.color_measure_alpha
	if copy_font:
		c.font_main.id = cc.font_main.id
		c.font_main.size = cc.font_main.size
		c.font_main.dpi = cc.font_main.dpi
		c.font_main.offset = cc.font_main.offset
		c.font_mc.id = cc.font_mc.id
		c.font_mc.size = cc.font_mc.size
		c.font_mc.dpi = cc.font_mc.dpi
		c.font_mc.offset = cc.font_mc.offset
		c.font_measure.id = cc.font_measure.id
		c.font_measure.size = cc.font_measure.size
		c.font_measure.dpi = cc.font_measure.dpi
		c.font_measure.offset = cc.font_measure.offset
	c.scale_size = cc.scale_size
	c.number_min_px = cc.number_min_px
	c.draw_mouse_coordinate = cc.draw_mouse_coordinate
	c.autohide_mouse_coordinate = cc.autohide_mouse_coordinate
	c.autohide_MC_threthold = cc.autohide_MC_threthold
	c.cursor_type = cc.cursor_type
	c.cursor_scale_size = cc.cursor_scale_size
	c.measure_cursor_scale_size = cc.measure_cursor_scale_size
	c.measure_scale_size = cc.measure_scale_size
	c.measure_select_point_threthold = cc.measure_select_point_threthold
	c.draw_scale_type = cc.draw_scale_type
	c.draw_unit = cc.draw_unit

class VIEW3D_OT_ruler_config_copy(bpy.types.Operator):
	'''copy current config to ... or from'''
	bl_idname = 'view3d.ruler_config_copy'
	bl_label = 'Copy Ruler Config'
	bl_options = {'REGISTER', 'UNDO'}

	mode = EnumProperty(name='Mode',
						 items=(('from', 'From', ''),
								('to', 'To', ''),
								('all', 'To All', '')),
						 default='all')

	def execute(self, context):
		cc = bpy.context.scene.ruler_config
		if self.properties.mode == 'all':
			for scene in bpy.data.scenes:
				c = scene.ruler_config
				copy_ruler_config(c, cc)
		else:
			if context.scene.ruler_config.scene in bpy.data.scenes:
				scene = context.scene.ruler_config.scene
				c = bpy.data.scenes[scene].ruler_config
				if self.properties.mode == 'from':
					copy_ruler_config(cc, c)
				else:
					copy_ruler_config(c, cc)
		return {'FINISHED'}

class RulerConfigPanel(bpy.types.Panel):
	bl_label = 'Ruler Config'
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = 'scene'
	bl_default_closed = True

	def draw(self, context):

		global rulerconfig

		layout = self.layout

		scn = context.scene
		rulerconfig = scn.ruler_config

		# Main
		row = layout.row()
		row.label('Config Main')
		row = layout.row()
		row.prop(rulerconfig, 'color_main')
		row.prop(rulerconfig, 'color_number')
		row = layout.row()
		row.prop(rulerconfig, 'color_cursor')
		row.prop(rulerconfig, 'color_cursor_bold')

		row = layout.row()
		row.prop(rulerconfig, 'scale_size')
		row = layout.row()
		row.prop(rulerconfig, 'number_min_px')
		row = layout.row()
		row.prop(rulerconfig, 'draw_mouse_coordinate')
		row = layout.row()
		row.active = rulerconfig.draw_mouse_coordinate
		row.prop(rulerconfig, 'autohide_mouse_coordinate')
		sub = row.column()
		sub.active = bool(rulerconfig.draw_mouse_coordinate) and bool(rulerconfig.autohide_mouse_coordinate)
		sub.prop(rulerconfig, 'autohide_MC_threthold')
		row = layout.row()
		row.prop(rulerconfig, 'cursor_type')
		row = layout.row()
		row.active = rulerconfig.cursor_type == 'cross_scale'
		row.prop(rulerconfig, 'cursor_scale_size')

		row = layout.row()
		row.prop(rulerconfig, 'draw_scale_type', text='Draw ruler type')
		row.prop(rulerconfig, 'draw_unit')

		# Measure
		row = layout.row()
		row.separator()
		row = layout.row()
		row.label('Config Measure')
		row = layout.row()
		row.prop(rulerconfig, 'color_measure')
		row.prop(rulerconfig, 'color_measure_sub')
		row = layout.row()
		row.prop(rulerconfig, 'color_measure_number')
		row.prop(rulerconfig, 'color_measure_angle')
		row = layout.row()
		row.prop(rulerconfig, 'color_measure_cursor')
		row.prop(rulerconfig, 'color_measure_cursor_bold')
		row = layout.row()
		row.prop(rulerconfig, 'color_measure_alpha', slider=True)

		row = layout.row()
		row.prop(rulerconfig, 'measure_cursor_scale_size', text='Cursor scale size')
		row = layout.row()
		row.prop(rulerconfig, 'measure_scale_size', text='Scale size')
		row = layout.row()
		row.prop(rulerconfig, 'measure_select_point_threthold')


		# Font
		row = layout.row()
		row.separator()
		row = layout.row()
		row.label('Font: Main')
		row = layout.row(align=True)
		row.prop(rulerconfig.font_main, 'id')
		row.prop(rulerconfig.font_main, 'size')
		row.prop(rulerconfig.font_main, 'dpi')
		row.prop(rulerconfig.font_main, 'offset')

		row = layout.row()
		row.label('Font: Mouse Coordinate')
		row = layout.row(align=True)
		row.prop(rulerconfig.font_mc, 'id')
		row.prop(rulerconfig.font_mc, 'size')
		row.prop(rulerconfig.font_mc, 'dpi')
		row.prop(rulerconfig.font_mc, 'offset')

		row = layout.row()
		row.label('Font: Measure')
		row = layout.row(align=True)
		row.prop(rulerconfig.font_measure, 'id')
		row.prop(rulerconfig.font_measure, 'size')
		row.prop(rulerconfig.font_measure, 'dpi')
		row.prop(rulerconfig.font_measure, 'offset')

		# Copy
		row = layout.row()
		row.separator()
		row = layout.row()
		row.label('Copy')
		row = layout.row()
		row.prop_search(rulerconfig, 'scene', bpy.data, 'scenes')
		row = layout.row(align=True)
		row.operator('view3d.ruler_config_copy', text='Copy from').mode='from'
		row.operator('view3d.ruler_config_copy', text='Copy to').mode='to'
		row.operator('view3d.ruler_config_copy', text='Copy to All').mode='all'
		row = layout.row()
		row.operator('view3d.ruler_config_reset', text='Reset')


# s = str([1, 2, 3])
# ls = re.findall('[-\+]?\.?\d+\.?\d*', s)
# ls = re.findall('([-\+]?\d+\.?\d*|[-\+]?\.?\d+)', s)
# l = [int(i) for i in ls if i.isdigit()]
# l = [float(i) for i in ls]


###############################################################################




class MeasureRuler(list):
	total_mode = 0 # 0:segment, 1:total
	draw_scale = 2 # 0:off,	 1:scale, 2:scale&number
	draw_angle = 0 # 0:off, 1:on
	draw_length = 1 # 0:off, 1:on
	draw_circle = 0 # 0:off, 1:type1, 2:type2
	draw_point = 1 # 0:off, 1:on
	subdivide = 0 # Ctrl + (0 ~ 9)
	f = 0 # FLAG, peut être utilisé pour quelque chose
	def __init__(self, l, total_mode=0, draw_scale=2, draw_angle=0, \
				 draw_length=1, draw_circle=0, draw_point=1, subdivide = 0,f=0):
		super(MeasureRuler, self).__init__(l)
		self.total_mode = total_mode
		self.draw_scale = draw_scale
		self.draw_angle = draw_angle
		self.draw_length = draw_length
		self.draw_circle = draw_circle
		self.draw_point = draw_point
		self.subdivide = subdivide
		self.f = f


class MeasurePoint():
	vec_window = Vector([0.0, 0.0, 0.0]) # window co
	vec_world = Vector([0.0, 0.0, 0.0]) # world co
	#dpu = 1.0 # dot per blender unit. Valeur entre le point suivant
	#angle = 0.0 # Valeur entre le point suivant; Change la direction tracée selon une valeur positive et/ou négative(traverser déterminée)
	#cross = Vector([0, 0, 0])
	#length = 0.0
	offset = 0.0 # scale du dessin
	length_to_next = 0.0
	length_to_prev = 0.0
	length_total = 0.0
	f = 0 # FLAG, peut être utilisé pour quelque chose
	def __init__(self, vec):
		self.vec_world = vec.copy()
	def copy(self):
		point = MeasurePoint(self.vec_world)
		point.vec_window = self.vec_window.copy()
		#point.dpu = self.dpu
		#point.length = self.length
		point.offset = self.offset
		point.length_to_next = self.length_to_next
		point.length_to_prev = self.length_to_prev
		point.length_total = self.length_total
		point.f = self.f
		return point
	def update(self, persmat, sx, sy):
		v = convert_world_to_window(self.vec_world, persmat, sx, sy)
		self.vec_window = Vector(v)

class Measure():
	on = 0 # 1:on
	always = 0 # 1:draw when not measure mode
	drag = 0 # 0:def, 1:drag, 2:transform
	drag_threthold = 5
	mouseco_drag_start = Vector([0, 0, 0]) # [x, y, z]
	point_bak = None # Transforme le point de départ
	rulers = []
	active_index = None
	mouse_point = MeasurePoint(Vector([0, 0, 0]))
	draw_circle = 1 # 1:Origine centrale, 2:Le cœur de la souris
	space_type = '3D' # or '2D'
	draw_shortcut = 0 # Liste des raccourcis sur la gauche
	draw_column_max = 0 # Nombre de décimales.

	offset_angle = 20 # config。Distance depuis le point lors de l'élaboration
	offset_angle_2 = 50 # est active dans la règle
	offset_length = 20
	text_height_max = 0 # width&height box : Lors de l'élaboration, pour empêcher le changement de hauteur par le nombre
	draw_text_list = [] # [('text', (posx, posy, posz)), ...] # Enfin, en réunissant

	# snap
	# region.width, region.height Indique la valeur maximale qui pourraient être prises pour créer un carré.
	# (Appuyer Ctrl longtemps: Ont fait la liste à chaque fois ).
	'''
	snap_region_xsize = 1920
	snap_region_ysize = 1200
	snap_vmat = [[[] for j in range(snap_region_xsize)] \
											   for i in range(snap_region_ysize)]
	snap_imat = [[[] for j in range(snap_region_xsize)] \
											   for i in range(snap_region_ysize)]
	'''
	snap_region_subdivide = 100 # Placé dans le carré (la matrice) de 100 * 100 par la fenêtre de coordonnées sommet.
	snap_vmat = snap_imat = snap_vwmat = None

	snap_range = 20
	ctrl = 0 # hold
	alt = 0 # hold
	snapon = 0
	snap_point = MeasurePoint(Vector([0, 0, 0])) # Maj coordonnées du monde, shift+clic commutation 2DSnap, 3DSnap.
	snap_find = 0 # 0:None, 2:snap2D, 3:snap3D
	snap_X = 0
	snap_Y = 0
	snap_Z = 0
	snap_to_visible = 0 # 0:snap to active & selected, 1:snap to ob.is_visible
	snap_to_dm = 1 # active&EditMode. Ne fonctionne qu'avec ob.create_mesh(context.scene, 1, 'PREVIEW')
	#inutile snap_me = None # ob.create_mesh(context.scene, 1, 'PREVIEW')

	def __init__(self):
		'''self.snap_vmat = [[[] for j in range(self.snap_region_xsize)] \
										 for i in range(self.snap_region_ysize)]
		self.snap_imat = [[[] for j in range(self.snap_region_xsize)] \
										 for i in range(self.snap_region_ysize)]
		'''
		pass
	def active(self, type='point', index=None):
		if index is None:
			i = self.active_index
		else:
			i = index
		if type == 'point':
			if i is not None:
				return self.rulers[i[0]][i[1]]
			else:
				return None
		else: # ruler
			if i is not None:
				return self.rulers[i[0]]
			else:
				return None

	def update_mouse_point(self, data):
		cursor = Vector(bpy.context.scene.cursor_location)
		point = self.active('point')
		mouseco = data.mouseco.copy()
		sx = data.sx
		sy = data.sy
		persmat = data.persmat
		if point:
			vec_win = convert_world_to_window(point.vec_world, persmat, sx, sy)
			vec = convert_window_to_world((mouseco[0], mouseco[1],vec_win[2]),
										  persmat, sx, sy)
			mouse_win = [mouseco[0], mouseco[1], vec_win[2]]
		else:
			cursor_win = convert_world_to_window(cursor, persmat, sx, sy)
			vec = convert_window_to_world((mouseco[0], mouseco[1],
										   cursor_win[2]),
										  persmat, sx, sy)
			mouse_win = [mouseco[0], mouseco[1], cursor_win[2]]
		self.mouse_point.vec_world[:] = vec[:] # update
		self.mouse_point.vec_window[:] = mouse_win[:]
		if len(self.rulers) > 0:
			if self.snap_X:
				x = self.mouse_point.vec_world[0]
				y = self.rulers[-1][-1].vec_world[1]
				z = self.rulers[-1][-1].vec_world[2]
				self.mouse_point.vec_world = Vector((x, y, z))
			if self.snap_Y:
				x = self.rulers[-1][-1].vec_world[0]
				y = self.mouse_point.vec_world[1]
				z = self.rulers[-1][-1].vec_world[2]
				self.mouse_point.vec_world = Vector((x, y, z))
			if self.snap_Z:
				x = self.rulers[-1][-1].vec_world[0]
				y = self.rulers[-1][-1].vec_world[1]
				z = self.mouse_point.vec_world[2]
				self.mouse_point.vec_world = Vector((x, y, z))
		return


	def update_points_vec_window(self, data):
		# update window
		persmat = data.persmat
		sx = data.sx
		sy = data.sy
		# ruler points
		for points in self.rulers:
			for p in points:
				v = convert_world_to_window(p.vec_world, persmat, sx, sy)
				p.vec_window = Vector(v)
		# mouse point
		p = self.mouse_point
		v = convert_world_to_window(p.vec_world, persmat, sx, sy)
		p.vec_window = Vector(v)

		# point bak
		p = self.point_bak
		if p:
			v = convert_world_to_window(p.vec_world, persmat, sx, sy)
			p.vec_window = Vector(v)

		# snap target
		p = self.snap_point
		v = convert_world_to_window(p.vec_world, persmat, sx, sy)
		p.vec_window = Vector(v)

	'''
	def update_snap_me(self, ob):
		obmode = ob.mode
		if obmode == 'EDIT':
			bpy.ops.object.mode_set(mode='OBJECT')
		if self.snap_to_dm:
			self.snap_me = ob.create_mesh(bpy.context.scene, 1, 'PREVIEW') # coordonnées locales
		else:
			self.snap_me = ob.data
		if obmode == 'EDIT':
			bpy.ops.object.mode_set(mode='EDIT')
	'''

#config_ = Config()
#color_ = Color()
measure_ = Measure()
### Config end #################################################################

### ShortCut ###################################################################
class ShortCut():
	def __init__(self, type,
				 any=False, shift=False, ctrl=False, alt=False, oskey=False):
		self.type = type
		self.any = any
		self.shift = shift
		self.ctrl = ctrl
		self.alt = alt
		self.oskey = oskey

# pass_keyboard_inputs: raccourci à passer à Blender en mode "MESURE", annuler pour autre.
pass_keyboard_types = ['MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
					   'NUMPAD_0', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3',
					   'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7',
					   'NUMPAD_8', 'NUMPAD_9',# 'NUMPAD_PLUS','NUMPAD_MINUS',
					   'NUMPAD_PERIOD', 'NUMPAD_SLASH', 'BUTTON8MOUSE']
pass_keyboard_inputs = [ShortCut(type, any=True) \
						for type in pass_keyboard_types]
pass_keyboard_types = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
					   'SIX', 'SEVEN', 'EIGHT', 'NINE']
pass_keyboard_inputs.extend([ShortCut(type) \
							 for type in pass_keyboard_types])
pass_keyboard_inputs.extend([ShortCut(type, shift=True) \
							 for type in pass_keyboard_types])
pass_keyboard_inputs.extend([ShortCut(type, alt=True) \
							 for type in pass_keyboard_types])
pass_keyboard_inputs.extend([ShortCut(type, shift=True, alt=True) \
							 for type in pass_keyboard_types])
pass_keyboard_inputs.append(ShortCut('C', shift=True))
pass_keyboard_inputs.extend([ShortCut('A', oskey=True), ShortCut('S', oskey=True),
							 ShortCut('Q', oskey=True), ShortCut('D', oskey=True),
							 ShortCut('F', oskey=True), ShortCut('W', oskey=True),
							 ShortCut('A', ctrl=True, oskey=True),
							 ShortCut('S', ctrl=True, oskey=True),
							 ShortCut('Q', ctrl=True, oskey=True),
							 ShortCut('A', shift=True, ctrl=True, oskey=True),
							 ShortCut('S', shift=True, ctrl=True, oskey=True),
							 ShortCut('Q', shift=True, ctrl=True, oskey=True),
							 ShortCut('Z', shift=True),
							 ShortCut('Z', alt=True),
							 ShortCut('Q', ctrl=True, alt=True)])
#keyboard_input_measure = ('A', 'C', 'R', 'S', 'T', )
### ShortCut end ###############################################################

SHIFT = 1
CTRL = 1 << 1
ALT = 1 << 2
OSKEY = 1 << 3
def get_modifier(event):
	return int(event.shift) | int(event.ctrl) << 1 | \
		   int(event.alt) << 2 | int(event.oskey) << 3


GRID_MIN_PX = 6.0

class Data():
	rv3d = None
	persmat = viewmat = viewloc = None
	sx = sy = 0
	mouseco = Vector([0, 0, 0])
	in_region = True
	dx = 1.0 # La mémoire minimale
	dot_per_blender_unit = 1.0
	unit_pow = 0 # puissance de l'unité	 = 10 ** unit_pow = dx Augmentation de la minute
	offset = [0, 0, 0] # origine des coordonnées de la fenêtre
	offset_3d = Vector([0, 0, 0]) # ou utiliser local_grid_origin, center_ofs,  pour l'origine des coordonnées 3d
	view = 'top'
	center_ofs = Vector([0,0,0]) # Coordonnées 3D position zéro de la règle

	# Echelle du dessin
	draw_offset_x = draw_offset_y = 0.0 # distance des bords de la fenêtre pour les cotes extérieures
	start_number_x = start_number_y = 0.0 # Origine de l'echelle de départ
	unit_x = unit_y = 1.0 # unité avec un signe

	# update in draw_mouse_coordinate. for measure
	mouse_coordinate_box_top_ymin = 0
	mouse_coordinate_box_right_xmin = 0

	def update(self, class_self, context, measure_mode=False):
		scn = bpy.context.scene
		if scn.Follow:
			self.rulerorigin = Vector((scn.oriX, scn.oriY, scn.oriZ))
			bpy.ops.ruler.rulertoorig('INVOKE_DEFAULT')
		if measure_mode:
			# measure_mode Mise à jour autant de fois que nécessaire à
			window = context.window
			region = bpy.context.region
			self.in_region = False # REGION seulement un clic de souris dans la même réaction. (Sont les mêmes dans la redéfinition)
#			if not region:
#				return
			rv3d = bpy.context.space_data.region_3d
#			if not rv3d:
				# Seulement mettre à jour les coordonnées de la souris
#				self.mouseco = Vector([event.mouse_region_x, \
#											 event.mouse_region_y, 0])
#				return
			self.region = region
			self.sx = region.width
			self.sy = region.height
			self.persmat = rv3d.perspective_matrix
			self.mouseco = Vector([globmx, globmy, 0])
			self.in_region = 0 <= self.mouseco[0] <= self.sx - 1	 and \
							 0 <= self.mouseco[1] <= self.sy - 1

			return

#		screen = context.screen
		region = context.region
#		if screen.name in class_self.__class__.disable_regions:
#			if region.id in class_self.__class__.disable_regions[screen.name]:
#				return False

		window = context.window
		spaceview3d = context.space_data # Space3DView
		rv3d = get_rv3d(context, spaceview3d)
		if rv3d is None:
			return False
		persmat = rv3d.perspective_matrix
		viewmat = rv3d.view_matrix

#		localgrid, localgrid_orig, localgrid_quat = \
#											  get_localgrid_status(spaceview3d)
#		if localgrid:
#			origin_offset = localgrid_orig
#		else:
		origin_offset = self.center_ofs

		sx = region.width
		sy = region.height
#		if event is not None:
		mouseco = Vector([globmx, globmy, 0])
		in_region = 0 <= mouseco[0] <= sx - 1  and 0 <= mouseco[1] <= sy - 1
#		else:
#			mouseco = None
#			in_region = False

		### Set Data ###
		self.persmat = persmat
		self.persinvmat = persmat.inverted()
		self.viewmat = viewmat
		self.viewinvmat = viewmat.inverted()
		self.viewloc = rv3d.view_location
		self.sx = sx
		self.sy = sy
		self.mouseco = mouseco.copy()
		self.in_region = in_region
		self.dot_per_blender_unit, self.dx, self.unit_pow = \
							  get_dx(sx, sy, persmat, viewmat, self.viewinvmat, self.viewloc)
		self.offset = convert_world_to_window(origin_offset, persmat, sx, sy)
		self.offset_3d = origin_offset
		self.view = check_view_context(context)
		self.set_scale_draw_options() # Fonction ECHELLE a également été bonne (calculer la valeur nécessaire pour en tirer?
		return True

	def get_window_data(self):
		return self.sx, self.sy, self.mouseco, self.dx, \
			   self.unit_pow, self.offset, self.view

	def set_scale_draw_options(self):
		dx = self.dx
		dot_per_blender_unit = self.dot_per_blender_unit
		unit = 10 ** self.unit_pow
		unit_x10 = unit * 10
		view = self.view

		vec = self.offset_3d.copy()
		vec[0] = (vec[0] - (self.sx / 2)) / dot_per_blender_unit
		vec[1] = (vec[1] - (self.sy / 2)) / dot_per_blender_unit
		vec[0] += (self.sx / 2) / dot_per_blender_unit
		vec[1] += (self.sy / 2) / dot_per_blender_unit # Coin inférieur gauche de l'écran des critères

		### X ###
		if view in ('left', 'back'):
			unit_x = -unit
			count_x = divmod(vec[0], unit_x10)[0] + 1.0
		else:
			unit_x = unit
			count_x = -divmod(vec[0], unit_x10)[0] - 1.0
		start_number_x = count_x * unit_x10
		draw_offset_x = (vec[0] % unit_x10) * dot_per_blender_unit
		if draw_offset_x > 0:
			draw_offset_x -= dx * 10
		### Y ###
		if view in ('bottom'):
			unit_y = -unit
			count_y = divmod(vec[1], unit_x10)[0] + 1.0
		else:
			unit_y = unit
			count_y = -divmod(vec[1], unit_x10)[0] - 1.0
		start_number_y = count_y * unit_x10
		draw_offset_y = (vec[1] % unit_x10) * dot_per_blender_unit
		if draw_offset_y > 0:
			draw_offset_y -= dx * 10

		self.draw_offset_x = draw_offset_x
		self.draw_offset_y = draw_offset_y
		self.start_number_x = start_number_x
		self.start_number_y = start_number_y
		self.unit_x = unit_x
		self.unit_y = unit_y

data_ = Data()

def get_rv3d(context, spaceview3d):
	rv3d = bpy.context.space_data.region_3d
	# TODO, quadview
	'''
	if hasattr(spaceview3d, 'region_quadview_nw'):
		available_quadview = True
	else:
		available_quadview = False
	if not rv3d:
		return None

	if available_quadview is False:
		if spaceview3d.region_quadview:
			return None
	'''
	return rv3d

def get_localgrid_status(spaceview3d):
	'''check localgrid
	'''
#	if hasattr(spaceview3d, 'use_local_grid'):
	localgrid = 1
#	else:
#		localgrid = False
#	if localgrid:
	localgrid_orig = spaceview3d.view_location
	localgrid_quat = spaceview3d.view_rotation
#	else:
#		localgrid_orig = localgrid_quat = None
	return localgrid, localgrid_orig, localgrid_quat

def get_dx(sx, sy, persmat, viewmat, viewinvmat, viewloc):
	'''
	Conversion	pour coordonner chaque fenêtre	(P, Q sont des coordonnées GLOBALE)
	P le centre de l'écran et Q, sont déplacés parallèlement à l'écran, à faible distance en unité Blender
	'''
	p = viewloc
	if sx >= sy:
		rightvec = Vector(viewmat[0][:3])
		rightvec.length = 1
		q = viewloc + rightvec
	else:
		upvec = Vector(viewmat[1][:3])
		upvec.length = 1
		q = viewloc + upvec
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


def number_adjust_column(f, unit_pow, zero=False, floor=False):
	# unit_pow==-1: text='1.00', unit_pow==0: text='1.0'
	number = 0.0 if zero and abs(f) < 1E-8 else f
	if floor:
		column = -unit_pow
		if number >= 0.0:
			number = math.floor(number * 10 ** column) * 10 ** -column
		else:
			number = math.ceil(number * 10 ** column) * 10 ** -column
	column = -unit_pow if unit_pow <= -1 else 0
	text = '{0:.{1}f}'.format(number, column)
	return text

def draw_cross_cursor(data, config, measure):
	if not data.in_region:
		return
	if measure.on:
		offset = 0
	else:
		offset = 12
	sx = data.sx - 1
	sy = data.sy - 1
	data = data_
	mouseco = data.mouseco.copy()
	dx = data.dx
	if measure.on:
		cssm = config.measure_cursor_scale_size[0] / 2
		csss = config.measure_cursor_scale_size[1] / 2
		cssl = config.measure_cursor_scale_size[2] / 2
		color_main = config.color_measure_cursor
		color_bold = config.color_measure_cursor_bold
	else:
		cssm = config.cursor_scale_size[0] / 2
		csss = config.cursor_scale_size[1] / 2
		cssl = config.cursor_scale_size[2] / 2
		color_main = config.color_cursor
		color_bold = config.color_cursor_bold

	glColor4f(*color_main)
	glBegin(GL_LINES)
	for x, y in ((mouseco[0] - offset, mouseco[1]), (0, mouseco[1]), #left
				 (mouseco[0] + offset, mouseco[1]), (sx, mouseco[1]), # right
				 (mouseco[0], mouseco[1] + offset), (mouseco[0], sy), # top
				 (mouseco[0], mouseco[1] - offset), (mouseco[0], 0)): # bottom
		glVertex2f(x, y)
	glEnd()

	if config.cursor_type != 'cross_scale':
		return

	color_tmp = list(color_bold[:])

	glBegin(GL_LINES)
	for d in (dx, -dx):
		p = 0
		css = cssm
		cnt = 0
		while 0 <= mouseco[0] + p <= sx or 0 <= mouseco[1] + p <= sy:
			if abs(p) < offset or cnt == 0 and offset == 0:
				p += d
				if css == cssm:
					css = cssl
				else:
					css = cssl if css == csss else csss
				cnt += 1
				continue
			draw_5 = cnt % 5 == 0 and d >= config.number_min_px[0]
			if cnt % 10 == 0:
				css = cssm
				glColor4f(*color_bold)
			else:
				f = 1 if not measure.on else 2
				color_tmp[3] = color_bold[3] * (1.0 - GRID_MIN_PX / dx / f)
				glColor4f(*color_tmp)
			glVertex2f(mouseco[0] + p, mouseco[1] - css)
			glVertex2f(mouseco[0] + p, mouseco[1] + css)
			glVertex2f(mouseco[0] - css, mouseco[1] + p)
			glVertex2f(mouseco[0] + css, mouseco[1] + p)
			if cnt % 10 != 0 and cnt % 5 == 0:
				glVertex2f(mouseco[0] + p - 3, mouseco[1] - cssm)
				glVertex2f(mouseco[0] + p, mouseco[1] - csss)
				glVertex2f(mouseco[0] + p, mouseco[1] - csss)
				glVertex2f(mouseco[0] + p + 3, mouseco[1] - cssm)
				glVertex2f(mouseco[0] - cssm, mouseco[1] + p - 3)
				glVertex2f(mouseco[0] - csss, mouseco[1] + p)
				glVertex2f(mouseco[0] - csss, mouseco[1] + p)
				glVertex2f(mouseco[0] - cssm, mouseco[1] + p + 3)
			p += d
			if css == cssm:
				css = cssl
			else:
				css = cssl if css == csss else csss
			cnt += 1
	glEnd()

def draw_scale(data, config):
	sx, sy, mouseco, dx, unit_pow, offset, view = data.get_window_data()
	sx -= 1
	sy -= 1
	draw_position_x = data.draw_offset_x
	draw_position_y = data.draw_offset_y
	unit_x = data.unit_x # signé
	unit_y = data.unit_y # signé
	number_x = data.start_number_x
	number_y = data.start_number_y
	#ssm, sss = config.scale_size
	ssl, ssm, sss = config.scale_size
	glEnable(GL_BLEND)
	glColor4f(*config.color_main)
	font = config.font_main
	blf.size(font.id, font.size, font.dpi)

	ss = ssm
	cnt = 0
	while draw_position_x <= sx - 20:
		if draw_position_x >= 90:
			if cnt % 10 == 0:
				ss = ssl
			elif cnt % 2 == 0:
				ss = ssm
			else:
				ss = sss
			glLineWidth(3 if cnt % 10 == 0 else 1)

			# scale
			glBegin(GL_LINES)
			glVertex2f(draw_position_x, sy)
			glVertex2f(draw_position_x, sy - ss)
			glEnd()

			draw_5 = cnt % 5 == 0 and dx >= config.number_min_px[0]
			draw_1 = cnt % 5 != 0 and dx >= config.number_min_px[1]
			# triangle marker
			if cnt % 5 == 0 and cnt % 10 != 0:
				f = 3 if draw_5 or draw_1 else 0
				draw_triangles(((draw_position_x, sy - ssm + f),
								(draw_position_x - 2, sy - ssm - 3 + f),
								(draw_position_x + 2, sy - ssm - 3 + f)),
								poly=True)
			# text
			if cnt % 10 == 0 or draw_5 or draw_1:
				text = number_adjust_column(number_x, unit_pow, zero=True)
				text_width, text_height = blf.dimensions(font.id, text)
				blf.position(font.id, draw_position_x - text_width / 2,
									sy - ssl - text_height - font.offset, 0)
				glColor4f(*config.color_number)
				blf.draw(font.id, text)
				glEnable(GL_BLEND)
				glColor4f(*config.color_main)
				# origin marker
				if abs(number_x) <= 1E-8:
					p = [draw_position_x - text_width / 2 - font.offset - 5,
						 sy - ssl - font.offset - text_height / 2]
					draw_triangle_relative(p, [5, 0], text_height)
					p = [draw_position_x + text_width / 2 + font.offset + 5,
						 sy - ssl - font.offset - text_height / 2]
					draw_triangle_relative(p, [-5, 0], text_height)
					#glEnable(GL_BLEND)

		draw_position_x += dx
		number_x += unit_x
		#ss = sss if ss == ssm else ssm
		cnt += 1

	text_width, text_height = blf.dimensions(font.id, '-.0123456789')
	if config.draw_unit:
		draw_position_y_min = text_height + font.offset * 2
	else:
		draw_position_y_min = 0

	#ss = ssm
	cnt = 0
	while draw_position_y <= sy - 20:
		if draw_position_y >= draw_position_y_min:
			if cnt % 10 == 0:
				ss = ssl
			elif cnt % 2 == 0:
				ss = ssm
			else:
				ss = sss
			glLineWidth(3 if cnt % 10 == 0 else 1)

			# scale
			glBegin(GL_LINES)
			glVertex2f(sx, draw_position_y)
			glVertex2f(sx - ss, draw_position_y)
			glEnd()

			draw_5 = cnt % 5 == 0 and dx >= config.number_min_px[0]
			draw_1 = cnt % 5 != 0 and dx >= config.number_min_px[1]
			# triangle marker
			if cnt % 5 == 0 and cnt % 10 != 0:
				f = 3 if draw_5 or draw_1 else 0
				draw_triangles(((sx - ssm + f, draw_position_y),
								(sx - ssm - 3 + f, draw_position_y - 2),
								(sx - ssm - 3 + f, draw_position_y + 2)),
								poly=True)
			# text
			if cnt % 10 == 0 or draw_5 or draw_1:
				text = number_adjust_column(number_y, unit_pow)
				text_width, text_height = blf.dimensions(font.id, text)
				blf.position(font.id, sx - ssl - text_width - font.offset,
							 draw_position_y - text_height / 2, 0)
				glColor4f(*config.color_number)
				blf.draw(font.id, text)
				glEnable(GL_BLEND)
				glColor4f(*config.color_main)
				# origin marker
				if abs(number_y) <= 1E-8:
					p = [sx - ssl - font.offset - text_width / 2,
						 draw_position_y - font.offset - text_height / 2 - 5]
					draw_triangle_relative(p, [0, 5], text_height)
					p = [sx - ssl - font.offset - text_width / 2,
						 draw_position_y + font.offset + text_height / 2 + 5]
					draw_triangle_relative(p, [0, -5], text_height)
					#glEnable(GL_BLEND)

		draw_position_y += dx
		number_y += unit_y
		#ss = sss if ss == ssm else ssm
		cnt += 1
	glLineWidth(1)

def draw_scale_type(data, config):
	view = data.view
	sx = data.sx - 1
	sy = data.sy - 1
	font = config.font_main
	offset = font.offset
	box_distance = 4
	lines = [] # prime

	if view in ('right', 'left'):
		text_x = 'Y'
		text_y = 'Z'
	elif view in ('front', 'back'):
		text_x = 'X'
		text_y = 'Z'
	elif view in ('top', 'bottom'):
		text_x = 'X'
		text_y = 'Y'
	else:
		text_x = text_y = None
	if text_x is not None:
		if data.unit_x < 0.0:
			text_x = '- ' + text_x
	else:
		text_x = 'U'
	if text_y is not None:
		if data.unit_y < 0.0:
			text_y = '- ' + text_y
	else:
		text_y = 'U'

	blf.size(font.id, font.size, font.dpi)
	text_width_x, text_height_x = blf.dimensions(font.id, text_x)
	p1 = (sx - text_width_x - offset * 2,
		  sy - text_height_x - offset * 2)
	if started:
		glColor4f(*config.color_background)
	glRectf(p1[0], p1[1], sx, sy)
	glColor4f(*config.color_main)
	draw_box(p1[0], p1[1],
			 text_width_x + offset * 2, text_height_x + offset * 2)
	blf.position(font.id, p1[0] + offset, p1[1] + offset, 0)
	blf.draw(font.id, text_x)
	lines.append((p1[0], sy, p1[0] - 10, sy))

	if text_y != 'U':
		text_width_y, text_height_y = blf.dimensions(font.id, text_y)
		p2 = (sx - text_width_y - offset * 2,
			  sy - text_height_x - text_height_y - offset * 4 - box_distance)

		glColor4f(*config.color_background)
		glRectf(p2[0], p2[1], sx, p2[1] + text_height_y + offset * 2)
		glColor4f(*config.color_main)
		draw_box(p2[0], p2[1],
				 text_width_y + offset * 2, text_height_y + offset * 2)
		glBegin(GL_LINES)
		glVertex2f(sx, p2[1])
		glVertex2f(sx, p2[1] - 10)
		glEnd()
		blf.position(font.id, p2[0] + offset, p2[1] + offset, 0)
		blf.draw(font.id, text_y)
		lines.append((sx, p2[1], sx, p2[1] - 10))
	else:
		lines.append((sx, p1[1], sx, p1[1] - 10))
	glBegin(GL_LINES)
	for x1, y1, x2, y2 in lines:
		glVertex2f(x1, y1)
		glVertex2f(x2, y2)
	glEnd()

def draw_unit(data, config):
	font = config.font_main
	sx = data.sx - 1
	text = number_adjust_column(10.0 ** data.unit_pow, data.unit_pow)

	blf.size(font.id, font.size, font.dpi)
	text_width, text_height = blf.dimensions(font.id, text)
	px = sx - text_width - font.offset * 2
	glColor4f(*config.color_background)
	glRectf(px, 0, sx, text_height + font.offset * 2)
	glColor4f(*config.color_main)
	draw_box(px, 0, text_width + font.offset * 2, text_height + font.offset * 2)
	blf.position(font.id, px + font.offset, font.offset, 0)
	blf.draw(font.id, text)

def draw_mouse_coordinate(data, config):
	if not data.in_region:
		return
	font_mc = config.font_mc
	blf.size(font_mc.id, font_mc.size, font_mc.dpi)
	offset = font_mc.offset
	ssm = config.scale_size[0]
	sx = data.sx - 1
	sy = data.sy - 1
	mouseco = data.mouseco.copy()
	rotviewmat = data.viewmat.copy().to_3x3()
	triangle_size = 5 # bas

	v = convert_world_to_window(data.viewloc, data.persmat, sx, sy)
#	vec = convert_window_to_world((mouseco[0], mouseco[1], v[2]),
#								  data.viewmat, data.sx, data.sy)
#	vec -= data.offset_3d
#	vec = vec * rotviewmat
#	if data.unit_x < 0.0:
#		vec[0] = -vec[0]
#	if data.unit_y < 0.0:
#		vec[1] = -vec[1]

	# overrides all the preceding
	vec = [0, 0]
	vec[0] = (mouseco[0] - data.sx/2) / data.dot_per_blender_unit
	vec[1] = (mouseco[1] - data.sy/2) / data.dot_per_blender_unit

	text_width_all, text_height_all = blf.dimensions(font_mc.id, '-.0123456789')

	# top
	text = number_adjust_column(vec[0], data.unit_pow - 1, floor=True)
	text_width, text_height = blf.dimensions(font_mc.id, text)
	px = mouseco[0] - text_width / 2 - offset
	py = sy - ssm - offset * 2 - text_height_all
	if not config.autohide_mouse_coordinate or \
	   mouseco[1] < py - config.autohide_MC_threthold:
		glColor4f(*config.color_background)
		glRectf(px, py, \
				px + text_width + offset * 2, py + text_height_all + offset * 2)
		glColor4f(*config.color_main)
		draw_box(px, py, text_width + offset * 2, text_height_all + offset * 2)
		draw_triangle_relative((mouseco[0], sy), (0, -ssm), triangle_size)
		blf.position(font_mc.id, px + offset, py + offset, 0)
		glColor4f(*config.color_number)
		blf.draw(font_mc.id, text)
	data.mouse_coordinate_box_top_ymin = py # for measure

	# right
	text = number_adjust_column(vec[1], data.unit_pow - 1, floor=True)
	text_width, text_height = blf.dimensions(font_mc.id, text)
	px = sx - ssm - text_width - offset * 2
	py = mouseco[1] - text_height_all / 2 - offset
	if not config.autohide_mouse_coordinate or \
	   mouseco[0] < px - config.autohide_MC_threthold:
		glColor4f(*config.color_background)
		glRectf(px, py, \
				px + text_width + offset * 2, py + text_height_all + offset * 2)
		glColor4f(*config.color_main)
		draw_box(px, py, text_width + offset * 2, text_height_all + offset * 2)
		draw_triangle_relative((sx, mouseco[1]), (-ssm, 0), triangle_size)
		blf.position(font_mc.id, px + offset, py + offset, 0)
		glColor4f(*config.color_number)
		blf.draw(font_mc.id, text)
	data.mouse_coordinate_box_right_xmin = px # for measure
	rv3d = bpy.context.space_data.region_3d
	rv3d.view_rotation = rv3d.view_rotation


def draw_measure_status(data, config, measure):
	scn = bpy.context.scene
	sx = data.sx
	sy = data.sy
	glColor4f(*config.color_main)
	font = config.font_measure
	blf.size(font.id, font.size, font.dpi)
	text_height_max = blf_text_height_max(font.id)#font.height_max()
	ofs = text_height_max + font.offset
	offset = sy - 40
	text_list = []
	if measure.draw_shortcut:
		text_list += ['Draw Always: R  [{0}]'.format(measure.always),
					 'Space Type: D	 [{0}]'.format(measure.space_type),
					 'Snap to Visible (0:Selected): O  [{0}]'.format(measure.snap_to_visible),
					 'Modifiers Applied (editmode): M  [{0}]'.format(measure.snap_to_dm),
					 'Max Column: NUMPAD_PLUS, NUMPAD_MINUS	 [{0}]'.format(measure.draw_column_max)
					 ]

	else:
		text_list.append('Draw Always: [{0}]'.format(measure.always))
		text_list.append('Space Type: [{0}]'.format(measure.space_type))
		if measure.snap_to_visible:
			text_list.append('Snap to Visible Mesh')
		else:
			text_list.append('Snap to Selected Mesh')
		text_list.append('Modifiers Applied: [{0}]'.format(measure.snap_to_dm))
		text_list.append('Column [{0}]'.format(measure.draw_column_max))
	text_list += ['', 'Show Hide Shortcut: H', '']
	if measure.draw_shortcut:
		text_list +=['Toggle: Ctrl + Shift + R',
					 'Draw Always: R',
					 '',
					 'Set Point: LEFTMOUSE',
					 'Add Point: Shift + LEFTMOUSE',
					 'Select: RIGHTMOUSE',
					 'Move Point: Drag RIGHTMOUSE',
					 'Switch Direction: W',
					 'Deselect: ESC',
					 'Delete: Q',
					 'Delete All: Shift + Q',
					 '',
					 'Snap to Mesh 2D toggle: S',
					 'Snap to Mesh 3D toggle: Shift-S',
					 'Snap to X: X',
					 'Snap to Y: Y',
					 'Snap to Z: Z',
					 '',
					 'TotalMode: T',
					 'Draw Circle: C',
					 'Draw Length: L',
					 'Draw Angle: A',
					 'Draw Scale: N',
					 'Draw Point: P',
					 'Draw LineCircle: E',
					 ]
	if not(scn.Active):
		text_list = []
	for text in text_list:
		blf.position(font.id, 10, offset, 0)
		blf.draw(font.id, text)
		offset -= ofs

def draw_measure_box(data, config, font, measure):
	# draw line
	if not data.in_region:
		return
	active_point = measure.active('point')
	if not (active_point and measure.on):
		return

	mouseco = measure.mouse_point.vec_window
	drag = measure.drag
	text_height_max = measure.text_height_max

	vec_x = Vector([1.0, 0.0, 0.0])
	vec_y = Vector([0.0, 1.0, 0.0])
	if drag == 2:
		point_bak = measure.point_bak
		point_bak_window = convert_world_to_window(point_bak.vec_world,
												data.persmat, data.sx, data.sy)
		active_vec_window = Vector(point_bak_window)
	else:
		active_vec_window = active_point.vec_window

	### calc ###
	# calc angle
	active_to_mouse_vec = mouseco - active_vec_window
	active_to_mouse_vec[2] = 0.0
	if active_to_mouse_vec.length == 0.0:
		angle_x_text = angle_y_text = '0.0'
	else:
		cross_x = vec_x.cross(active_to_mouse_vec)
		cross_y = vec_y.cross(active_to_mouse_vec)
		angle_x = math.degrees(vec_x.angle(active_to_mouse_vec))
		if cross_x[2] >= 0.0:
			angle_x = -angle_x
		angle_y = math.degrees(vec_y.angle(active_to_mouse_vec))
		if cross_y[2] >= 0.0:
			angle_y = -angle_y
		angle_x_text = '{0:.{1}f}'.format(angle_x, 1)
		angle_y_text = '{0:.{1}f}'.format(angle_y, 1)

	# calc lengh
	length_width = active_to_mouse_vec[0] / data.dot_per_blender_unit
	length_height = active_to_mouse_vec[1] / data.dot_per_blender_unit
	dpu = data.dot_per_blender_unit
	upd = 1.0 / dpu
	for column in range(10):
		if upd * (10 ** column) >= 1.0:
			break
	length_width_text = '{0:.{1}f}'.format(length_width, column)
	length_height_text = '{0:.{1}f}'.format(length_height, column)


	### draw ###
	### RIGHT ###
	# right height box
	text_width, text_height = blf.dimensions(font.id, length_height_text)
	x2 = data.mouse_coordinate_box_right_xmin
	x1 = x2 - text_width - font.offset * 2
	if active_to_mouse_vec[1] >= 0.0:
		y1 = active_vec_window[1] + text_height_max + font.offset * 2 # extrémité inférieure
		height_box_y = y1 + text_height_max + font.offset * 2 # Utilisé pour attirer la ligne droite
	else:
		y1 = active_vec_window[1] - text_height_max * 2 - font.offset * 4 # extrémité inférieure
		height_box_y = y1
	y2 = y1 + text_height_max + font.offset * 2
	glBegin(GL_LINE_STRIP)
	glVertex2f(x2, y1)
	glVertex2f(x1, y1)
	glVertex2f(x1, y2)
	glVertex2f(x2, y2)
	glEnd()

	# text
	data.mouse_coordinate_box_right_xmin
	text_width, text_height = blf.dimensions(font.id, angle_x_text)
	x = data.mouse_coordinate_box_right_xmin - text_width - font.offset
	if active_to_mouse_vec[1] >= 0:
		y = active_vec_window[1] + font.offset
	else:
		y = active_vec_window[1] - text_height_max - font.offset
	measure.draw_text_list.append((angle_x_text, (x, y, 0), 'angle'))
	measure.draw_text_list.append((length_height_text, (x1 + font.offset, y1 + font.offset, 0), 'length'))

	### TOP ###
	# top width box
	text_angle_width, text_angle_height = blf.dimensions(font.id, angle_y_text)
	text_width, text_height = blf.dimensions(font.id, length_width_text)
	if active_to_mouse_vec[0] >= 0.0:
		x1 = active_vec_window[0] + text_angle_width + font.offset * 2
		x2 = width_box_x = x1 + text_width + font.offset * 2
	else:
		x2 = active_vec_window[0] - text_angle_width - font.offset * 2
		x1 = width_box_x = x2 - text_width - font.offset * 2
	y2 = data.mouse_coordinate_box_top_ymin
	y1 = y2 - text_height_max - font.offset * 2
	glBegin(GL_LINE_STRIP)
	glVertex2f(x1, y2)
	glVertex2f(x1, y1)
	glVertex2f(x2, y1)
	glVertex2f(x2, y2)
	glEnd()

	# text
	text_width, text_height = blf.dimensions(font.id, angle_y_text)
	y = data.mouse_coordinate_box_top_ymin - text_height_max - font.offset
	if active_to_mouse_vec[0] >= 0:
		x = active_vec_window[0] + font.offset
	else:
		x = active_vec_window[0] - text_width - font.offset
	measure.draw_text_list.append((angle_y_text, (x, y, 0), 'angle'))
	measure.draw_text_list.append((length_width_text, (x1 + font.offset, y1 + font.offset, 0), 'length'))

	glBegin(GL_LINES)
	# x line
	x = min(mouseco[0], active_vec_window[0])
	y = active_vec_window[1]
	glVertex2f(x, y)
	glVertex2f(data.mouse_coordinate_box_right_xmin, y)
	# right line
	glVertex2f(data.mouse_coordinate_box_right_xmin, y)
	if active_to_mouse_vec[1] >= 0.0:
		glVertex2f(data.mouse_coordinate_box_right_xmin, max(mouseco[1], height_box_y))
	else:
		glVertex2f(data.mouse_coordinate_box_right_xmin, min(mouseco[1], height_box_y))

	# y line
	x = active_vec_window[0]
	y = min(mouseco[1], active_vec_window[1])
	glVertex2f(x, y)
	glVertex2f(x, data.mouse_coordinate_box_top_ymin)
	# top line
	glVertex2f(x, data.mouse_coordinate_box_top_ymin)
	if active_to_mouse_vec[0] >= 0.0:
		glVertex2f(max(mouseco[0], width_box_x), data.mouse_coordinate_box_top_ymin)
	else:
		glVertex2f(min(mouseco[0], width_box_x), data.mouse_coordinate_box_top_ymin)
	#glVertex2f(mouseco[0], data.mouse_coordinate_box_top_ymin)
	glEnd()


	# La ligne en pointillé lorsque drag
	if drag == 2:
		glEnable(GL_LINE_STIPPLE);
		glLineStipple(5 , int(0b101010101010101)) # (factor, pattern)
		glBegin(GL_LINES)
		glVertex2f(active_vec_window[0], active_vec_window[1])
		glVertex2f(mouseco[0], mouseco[1])
		glEnd()
		glLineStipple(1 , 1)
		glDisable(GL_LINE_STIPPLE)

def draw_measure_circle(measure, config, dpu, alpha):
	subdivide = 256

	# active
	mouseco = measure.mouse_point.vec_window
	if measure.draw_circle and measure.on:
		active_point = measure.active('point')
		if active_point and measure.drag != 1:
			mouse_vec_world = measure.mouse_point.vec_world
			if measure.drag == 0:
				vec_world = active_point.vec_world
				vec_window = active_point.vec_window
			else:
				vec_world = measure.point_bak.vec_world
				vec_window = measure.point_bak.vec_window
				if measure.snap_find:
					mouse_vec_world = measure.snap_point.vec_world
			if measure.space_type == '3D':
				radius_3d = (vec_world - mouse_vec_world).length
				radius = radius_3d * dpu
			else:
				radius = (vec_window - mouseco).length
			if measure.draw_circle == 1:
				x = vec_window[0]
				y = vec_window[1]
			elif measure.draw_circle == 2:
				x = mouseco[0]
				y = mouseco[1]
			else:
				x, y, z = (vec_window + mouseco) / 2
				radius /= 2

			draw_circle(x, y, radius, subdivide)

	# line
	col = config.color_measure_sub[:3] + (config.color_measure_sub[3] * alpha, )
	glColor4f(*col)
	for ruler in measure.rulers:
		if ruler.draw_circle == 0:
			continue
		if len(ruler) <= 1:
			continue
		points = ruler
		for p1, p2 in zip(points, points[1:]):
			if measure.space_type == '3D':
				radius_3d = (p1.vec_world - p2.vec_world).length
				radius = radius_3d * dpu
			else:
				radius = (p1.vec_window - p2.vec_window).length
			if ruler.draw_circle == 1:
				x, y, z = p1.vec_window
			elif ruler.draw_circle == 2:
				x, y, z = p2.vec_window
			else:
				x, y, z = (p1.vec_window + p2.vec_window) / 2
				radius /= 2
			draw_circle(x, y, radius, subdivide)
	#glColor4f(*config.color_measure)

def draw_measure_subdivide(config, measure):
	mssl, mssm, msss = config.measure_scale_size
	mouse_point = measure.mouse_point.copy()
	mouseco = mouse_point.vec_window
	active_ruler = measure.active('ruler')
	active_point = measure.active('point')
	rulers_ex = []
	if active_point and measure.on:
		if measure.drag == 0:
			if len(active_ruler) == 1:
				rulers_ex = [MeasureRuler([active_point, mouse_point], \
										  subdivide = active_ruler.subdivide)]
			elif active_point == active_ruler[0]:
				active_ruler.insert(0, mouse_point)
			elif active_point == active_ruler[-1]:
				active_ruler.append(mouse_point)
			else:
				rulers_ex = [MeasureRuler([active_point, mouse_point], \
										  subdivide = active_ruler.subdivide)]

	for ruler in measure.rulers + rulers_ex:
		total_length = 0.0
		### article ###
		# 3D: vec, l
		# 2D: v, d
		# vec1 -> vec2 = vec12, vec12.length = l12
		ruler[0].length_total = 0.0
		for p1, p2 in zip(ruler, ruler[1:]):
			if measure.space_type == '3D':
				vec1 = p1.vec_world
				vec2 = p2.vec_world
			else:
				# Rendre le vecteur(GLOBAL) identique à la valeur Z en coordonnées de fenêtre
				vec1 = window_to_world_coordinate(p1.vec_window[0],
												  p1.vec_window[1],
												  persmat, sx, sy,
												  p1.vec_window[2])
				vec2 = window_to_world_coordinate(p2.vec_window[0],
												  p2.vec_window[1],
												  persmat, sx, sy,
												  p1.vec_window[2])
			l = (vec1 - vec2).length
			total_length += l
			p1.length_to_next = l
			p2.length_to_prev = l
			p2.length_total = total_length

	glBegin(GL_LINES)
	for ruler in measure.rulers + rulers_ex:
		if ruler.subdivide == 0:
			continue
		total_length = ruler[-1].length_total
		for p1, p2 in zip(ruler, ruler[1:]):
			if ruler.total_mode == 0:
				v1 = Vector(p1.vec_window[:2])
				v2 = Vector(p2.vec_window[:2])
				v12 = v2 - v1
				v12n = v12.normalized()
				v12vn = Vector([-v12n[1], v12n[0]])
				v12tmp = v12 / (ruler.subdivide + 1)
				for i in range(ruler.subdivide):
					v3 = v1 + v12tmp * (i + 1)
					glVertex2f(*v3)
					glVertex2f(*(v3 + v12vn * mssl))
			else:
				pass
	glEnd()

	if active_point and measure.drag == 0:
		if mouse_point in active_ruler:
			active_ruler.remove(mouse_point)

def draw_measure_scale(data, config, measure, font):
	'''
	# column
	data.dot_per_blender_unit
	upd = 1.0 / dpu
	for column in range(10):
		if upd * (10 ** column) >= 1.0:
			break
	'''

	dx = data.dx
	#dpu = data.dot_per_blender_unit
	sx = data.sx
	sy = data.sy
	persmat = data.persmat

	mouse_point = measure.mouse_point.copy()
	mouseco = mouse_point.vec_window
	active_ruler = measure.active('ruler')
	active_point = measure.active('point')
	rulers_ex = []
	if active_point and measure.on:
		if measure.drag == 0:
			if len(active_ruler) == 1:
				rulers_ex = [MeasureRuler([active_point, mouse_point], \
										  draw_scale = active_ruler.draw_scale)]
			elif active_point == active_ruler[0]:
				active_ruler.insert(0, mouse_point)
			elif active_point == active_ruler[-1]:
				active_ruler.append(mouse_point)
			else:
				rulers_ex = [MeasureRuler([active_point, mouse_point], \
										  draw_scale = active_ruler.draw_scale)]
	c1 = Vector([0, 0])
	c2 = Vector([sx - 1, 0])
	c3 = Vector([0, sy - 1])
	c4 = Vector([sx - 1, sy - 1])
	for ruler in measure.rulers + rulers_ex:
		if ruler.draw_scale == 0:
			continue
		total_length = 0.0
		### article ###
		# 3D: vec, l
		# 2D: v, d
		# vec1 -> vec2 = vec12, vec12.length = l12
		for p1, p2 in zip(ruler, ruler[1:]):
			v1 = Vector(p1.vec_window[:2])
			v2 = Vector(p2.vec_window[:2])
			# Calculer l'intersection avec le bord de l'écran
			cross_vs = []
			for c5, c6 in [(c1, c2), (c3, c4), (c1, c3), (c2, c4)]:
				v = intersect_line_line_2d(v1, v2, c5, c6)
				if v:
					cross_vs.append(v)
			d12 = (v2 - v1).length
			if measure.space_type == '3D':
				vec1 = p1.vec_world
				vec2 = p2.vec_world
			else:
				# Rendre le vecteur(GLOBAL) identique à la valeur Z en coordonnées de fenêtre
				vec1 = window_to_world_coordinate(p1.vec_window[0],
												  p1.vec_window[1],
												  persmat, sx, sy,
												  p1.vec_window[2])
				vec2 = window_to_world_coordinate(p2.vec_window[0],
												  p2.vec_window[1],
												  persmat, sx, sy,
												  p1.vec_window[2])
			vec12 = vec2 - vec1
			l12 = vec12.length
			if len(cross_vs) >= 2:
				d1 = (cross_vs[0] - v1).length
				d2 = (cross_vs[1] - v1).length
				f = d1 / d12 if d12 else 0.0
				start_point = MeasurePoint(vec1 + vec12 * f) # Si son intersection coupe le bord de l'écran
				f = d2 / d12 if d12 else 0.0
				end_point = MeasurePoint(vec1 + vec12 * f) # Si son intersection coupe le bord de l'écran
				if d1 > d2:
					d1, d2 = d2, d1
					start_point, end_point = end_point, start_point
			elif len(cross_vs) == 1:
				d1 = (cross_vs[0] - v1).length
				f = d1 / d12 if d12 else 0.0
				start_point = MeasurePoint(vec1 + vec12 * f) # p1 est pris dans le cas de l'extérieur
				end_point = MeasurePoint(vec2)
				if 0 <= v1[0] < sx and 0 <= v1[1] < sy: # Si vous étiez à l'intérieur, p1
					#d1 = d12 - d1
					d1 = 0.0
					end_point = start_point
					start_point = MeasurePoint(vec1)
			elif 0 <= v1[0] < sx and 0 <= v1[1] < sy and \
				 0 <= v2[0] < sx and 0 <= v2[1] < sy:
				d1 = 0.0
				start_point = MeasurePoint(vec1)
				end_point = MeasurePoint(vec2)
			else:
				total_length += l12
				continue
			#if d12 == 0.0 or l12 == 0.0: # Doivent être tirées de la direction du vecteur
			# si vous voulez voir le  vecteur en trois dimensions
			#	 continue

			# set offset
			dpu = d12 / l12 if l12 else 0.0 # Mise à jour toutes les lignes . par unité blender
			upd = l12 / d12 if d12 else 0.0
			start_point.offset = d1 * upd
			if ruler.total_mode:
				start_point.offset += total_length

			total_length += l12 # for next loop

			# update point 2D coordinate
			start_point.update(persmat, sx, sy)
			end_point.update(persmat, sx,sy)

			### draw ###
			mssl, mssm, msss = config.measure_scale_size
			#mssl /= 2; mssm /= 2; msss /= 2
			v12n = (v2 - v1).normalized()
			v12nv = Vector([v12n[1], -v12n[0]]) # et v12n verticale
			unit = 10 ** data.unit_pow # mise à l'echelle d'une minute d'unité blender

			# start
			v = start_point.vec_window.to_2d() # échelle de position de début de dessin
			if start_point.offset > 1E-8: # Le mode total est sur le côté gauche quand l'échelle supplémentaire est attirée
				cnt_start = int(start_point.offset / unit) + 1
			else:
				cnt_start = int(start_point.offset / unit)
			v += v12n * (-start_point.offset + cnt_start * unit) * dpu
			# last
			l_se = (start_point.vec_world - end_point.vec_world).length
			cnt_last = int((start_point.offset + l_se) / unit)

			glBegin(GL_LINES)
			for cnt in range(cnt_start, cnt_last + 1):
				# text
				draw_5 = cnt % 5 == 0 and data.dx >= config.number_min_px[0]
				if ruler.draw_scale == 2 and (cnt % 10 == 0 or draw_5):
					#if (ruler.total_mode or ruler.total_mode == 0 and cnt != 0):
					text = ''
					if (cnt != 0):
						text = number_adjust_column(unit * cnt, data.unit_pow)
					elif (ruler.total_mode):
						text = 'T'
					if text:
						'''text_width, text_height = blf.dimensions(font.id, text)
						v3 = ((text_width / 2 + font.offset) * v12nv[0],\
							  (text_height / 2 + font.offset) * v12nv[1])
						v4 = (v12nv[0] * mssl, v12nv[1] * mssl)
						position = (v[0] + v3[0] + v4[0] - text_width / 2,\
									v[1] + v3[1] + v4[1] - text_height / 2, 0)
						'''
						position = text_draw_position_along_line(text, font,
																v, v12nv * mssl)
						measure.draw_text_list.append((text, position, 'length'))

				if cnt % 10 == 0:
					mss = mssl
				elif cnt % 2 == 0:
					mss = mssm
				else:
					mss = msss
				glVertex2f(*v)
				glVertex2f(*(v + v12nv * mss))

				if cnt == 0: # Marquer le point de départ indiquant
					glVertex2f(*(v + v12nv * mssl / 1.5))
					glVertex2f(*(v + v12n * mssl / 1.5))
				elif cnt % 10 != 0 and cnt% 5 == 0: # Barème des 1/2
					l = 3
					glVertex2f(*(v + v12nv * mss + (v12n + v12nv) * l))
					glVertex2f(*(v + v12nv * mss))
					glVertex2f(*(v + v12nv * mss))
					glVertex2f(*(v + v12nv * mss + (-v12n + v12nv) * l))
					#glVertex2f(*(v + v12nv * mss + (-v12n + v12nv) * l))
					#glVertex2f(*(v + v12nv * mss + (v12n + v12nv) * l))
				v += v12n * unit * dpu

			glEnd()

	if active_point and measure.drag == 0:
		if mouse_point in active_ruler:
			active_ruler.remove(mouse_point)


def draw_measure_line(measure):
	mouseco = measure.mouse_point.vec_window
	glBegin(GL_LINES)
	for points in measure.rulers:
		for p1, p2 in zip(points, points[1:]):
			glVertex2f(p1.vec_window[0], p1.vec_window[1])
			glVertex2f(p2.vec_window[0], p2.vec_window[1])
	if measure.drag == 0 and measure.on:
		point = measure.active('point')
		if point:
			glVertex2f(point.vec_window[0], point.vec_window[1])
			glVertex2f(mouseco[0], mouseco[1])
	glEnd()

def draw_measure_ponit(measure):
	l = 3
	glBegin(GL_LINES)
	for points in measure.rulers:
		if points.draw_point == 0:
			continue
		for point in points:
			if point != measure.active('point'):
				v = point.vec_window
				#draw_box(v[0] - 2, v[1] - 2, 5, 5)
				glVertex2f(v[0] - l, v[1])
				glVertex2f(v[0] + l, v[1])
				glVertex2f(v[0], v[1] - l)
				glVertex2f(v[0], v[1] + l)
	glEnd()

def draw_measure_snap(measure):
	if not measure.snap_find or not measure.on:
		return
	snap_point = measure.snap_point
	vec = snap_point.vec_window
	if measure.snap_find == 2:
		draw_box(vec[0] - 6, vec[1] - 6, 12, 12)
	elif measure.snap_find == 3:
		draw_circle(vec[0], vec[1], 8, 12)

def draw_measure_angle(measure, config, font, alpha):
	# active
	rulers_ex = []
	acti = measure.active_index
	mouse_point = measure.mouse_point
	if measure.on and acti and measure.drag == 0:
		active_ruler = measure.active('ruler')
		active_point = measure.active('point')
		if len(active_ruler) >= 2:
			if active_point == active_ruler[0]:
				point_f = active_ruler[1]
				rulers_ex = [MeasureRuler([mouse_point, active_point, point_f])]
			elif active_point == active_ruler[-1]:
				point_b = active_ruler[-2]
				rulers_ex = [MeasureRuler([point_b, active_point, mouse_point])]
			else:
				point_b = active_ruler[acti[1] - 1]
				point_f = active_ruler[acti[1] + 1]
				r1 = MeasureRuler([point_b, active_point, mouse_point], f=1) # spécial
				r2 = MeasureRuler([mouse_point, active_point, point_f], f=2)
				rulers_ex = [r1, r2]

		for ruler in rulers_ex:
			ruler.draw_angle = active_ruler.draw_angle

	# ruler
	for ruler in measure.rulers + rulers_ex:
		if not ruler.draw_angle:
			continue
		if len(ruler) <= 2:
			continue
		for i in range(len(ruler) - 2):
			# angle
			if measure.space_type == '3D':
				v1 = ruler[i].vec_world
				v0 = ruler[i + 1].vec_world
				v2 = ruler[i + 2].vec_world
			else:
				v1 = ruler[i].vec_window
				v0 = ruler[i + 1].vec_window
				v2 = ruler[i + 2].vec_window
			v01 = v1 - v0
			v02 = v2 - v0
			if v01.length == 0.0 or v02.length == 0.0:
				angle = 0.0
			else:
				angle = math.degrees(v01.angle(v02))
			text_angle = '{0:.{1}f}'.format(angle, max(measure.draw_column_max, 1))

			# Afficher la position
			v1 = ruler[i].vec_window.copy()
			v0 = ruler[i + 1].vec_window.copy()
			v2 = ruler[i + 2].vec_window.copy()
			v0[2] = v1[2] = v2[2] = 0.0
			v01 = v1 - v0
			v02 = v2 - v0
			if v01.length == 0 or v02.length == 0:
				draw_vec = Vector([0, -1, 0])
			else:
				v01.normalize()
				v02.normalize()
				draw_vec = (v01 + v02).normalized()
			text_width, text_height = blf.dimensions(font.id, text_angle)
			if ruler.f:
				if v01.length != 0.0 and v02.length != 0.0:
					angle_v01y = Vector([0, 1, 0]).angle(v01)
					angle_v02y = Vector([0, 1, 0]).angle(v02)
					if Vector([0, 1, 0]).cross(v01)[2] >= 0.0:
						angle_v01y = math.pi * 2 - angle_v01y
					if Vector([0, 1, 0]).cross(v02)[2] >= 0.0:
						angle_v02y = math.pi * 2 - angle_v02y
					cross_v0102 = v01.cross(v02)
					if cross_v0102[2] >= 0.0:
						start_angle = angle_v02y
						end_angle = angle_v01y
					else:
						start_angle = angle_v01y
						end_angle = angle_v02y
					if ruler.f == 1:
						draw_vec *= measure.offset_angle_2 - 4
						radius = measure.offset_angle_2 - 4
					else:
						draw_vec *= measure.offset_angle_2 + 4
						radius = measure.offset_angle_2 + 4
					col = config.color_measure_sub[:3] + (config.color_measure_sub[3] * alpha, )
					glColor4f(*col)
					draw_arc12(v0[0], v0[1], radius, start_angle, end_angle, 32)
					col = config.color_measure[:3] + (config.color_measure[3] * alpha, )
					glColor4f(*col)

			else:
				draw_vec *= measure.offset_angle
			draw_position = v0 + draw_vec
			draw_position -= Vector([text_width / 2, text_height / 2, 0])
			#draw_position.resize_3d()

			measure.draw_text_list.append((text_angle, (draw_position), 'angle'))


def draw_measure_length_def(measure, rulers, font, column, dpu):
	for ruler in rulers:
		if not ruler.draw_length:
			continue
		if ruler.total_mode:
			continue
		for p1, p2 in zip(ruler, ruler[1:]):
			if measure.space_type == '3D':
				length = (p2.vec_world - p1.vec_world).length
			else:
				length = (p2.vec_window - p1.vec_window).length / dpu
			column_max = max(measure.draw_column_max, column)
			length_text = '{0:.{1}f}'.format(length, column_max)
			text_width, text_height = blf.dimensions(font.id, length_text)

			v1 = p1.vec_window.copy()
			v2 = p2.vec_window.copy()
			v1[2] = v2[2] = 0.0
			if (v2 - v1).length == 0.0:
				continue

			v = (Vector(v1[:2]) + Vector(v2[:2])) / 2
			v12n = (v2 - v1).normalized()
			v12nv = Vector([-v12n[1], v12n[0]])
			'''
			v3 = (v12nv[0] * (text_width / 2 + font.offset),\
				  v12nv[1] * (text_height / 2 + font.offset))
			v4 = (v12nv[0] * 3, v12nv[1] * 3)
			position = (v[0] + v3[0] + v4[0] - text_width / 2,\
						v[1] + v3[1] + v4[1] - text_height / 2, 0)
			'''
			position = text_draw_position_along_line(length_text, font, v, v12nv * 3)
			measure.draw_text_list.append((length_text, position, 'length'))

def draw_measure_length_total(measure, rulers, font, column, dpu):
	text_height = measure.text_height_max
	for ruler in rulers:
		if not ruler.draw_length:
			continue
		if not ruler.total_mode:
			continue
		total_length = 0.0
		for p1, p2 in zip(ruler, ruler[1:]):
			v = Vector((p2.vec_window - p1.vec_window)[:2])
			vv = Vector([-v[1], v[0]])
			vv.normalize()

			# zero
			if total_length == 0.0:
				total_length_text = '0'
				position = text_draw_position_along_line(total_length_text, \
													font, p1.vec_window, vv * 3)
				measure.draw_text_list.append((total_length_text, position, 'length'))

			# other
			if measure.space_type == '3D':
				length = (p2.vec_world - p1.vec_world).length
			else:
				length = (p2.vec_window - p1.vec_window).length / dpu
			total_length += length

			column_max = max(measure.draw_column_max, column)
			total_length_text = '{0:.{1}f}'.format(total_length, column_max)
			if p2.f == 0:
				position = text_draw_position_along_line(total_length_text, \
													font, p2.vec_window, vv * 3)
			else: # mouse
				position = p2.vec_window + Vector([15, -text_height - 15, 0])
				position[2] = 0.0
			measure.draw_text_list.append((total_length_text, position, 'length'))


		'''
		# draw last
		total_length_text = '{0:.{1}f}'.format(total_length, column)
		if p2.f == 0:
			position = p2.vec_window + Vector([5, 5, 0])
		else: # mouse
			position = p2.vec_window + Vector([15, -text_height - 15, 0])
		position[2] = 0.0
		measure.draw_text_list.append((total_length_text, position, 'length'))
		'''


def draw_measure_length(measure, dpu, font):
	upd = 1.0 / dpu
	for column in range(10):
		if upd * (10 ** column) >= 1.0:
			break

	rulers_ex = []
	acti = measure.active_index
	mouse_point = measure.mouse_point.copy()

	active_ruler = measure.active('ruler')
	active_point = measure.active('point')
	rulers_ex = []
	if acti:
		if active_ruler.total_mode:
			if active_point == active_ruler[-1] or \
			   active_point == active_ruler[0]: # Affichage de Total_length près de la souris
				mouse_point.f = 1
		if measure.drag == 0:
			if measure.on:
				if active_ruler.total_mode:
					if active_point == active_ruler[-1]: # add to tail
						active_ruler.append(mouse_point)
					elif active_point == active_ruler[0]: # add to head
						active_ruler.insert(0, mouse_point)
				rulers_ex = [MeasureRuler([active_point, mouse_point])] # total_mode=0

		elif measure.drag == 2: # measure.on==0 toujours, quand drag=0
			point_bak = measure.point_bak
			rulers_ex = [MeasureRuler([point_bak, mouse_point])] # total_mode=0

	draw_measure_length_def(measure, measure.rulers + rulers_ex, font, column, dpu)
	draw_measure_length_total(measure, measure.rulers + rulers_ex, font, column, dpu)

	if acti:
		if mouse_point == active_ruler[-1] or mouse_point == active_ruler[0]:
			active_ruler.remove(mouse_point)

def draw_measure_text(config, measure, alpha):
	glEnable(GL_BLEND)
	font = config.font_measure
	col = config.color_measure_number[:3] + (config.color_measure_number[3] * alpha, )
	cola = config.color_measure_angle[:3] + (config.color_measure_angle[3] * alpha, )
	for text, position, dtype in measure.draw_text_list:
		if dtype == 'length':
			glColor4f(*col)
		elif dtype == 'angle':
			glColor4f(*cola)
		blf.position(font.id, *position)
		blf.draw(font.id, text)


def draw_measure(data, config, measure):
	glEnable(GL_BLEND)
	glColor4f(*config.color_main)
	if measure.on:
		draw_measure_status(data, config, measure)

	if measure.on == 0 and measure.always == 1:
		alpha = config.color_measure_alpha
	else:
		alpha = 1.0
	glEnable(GL_BLEND)
	col = config.color_measure[:3] + (config.color_measure[3] * alpha, )
	glColor4f(*col)

	if measure.on == 0 and measure.always == 0:
		return
	rulers = measure.rulers
	if not rulers and measure.snap_find:
		# Etablissement seul du snap
		measure.update_points_vec_window(data)
		draw_measure_snap(measure)
		return

	# update & reset
	measure.update_points_vec_window(data) # Mettre à jour uniquement les coordonnées WINDOW
	measure.draw_text_list = []

	font = config.font_measure
	blf.size(font.id, font.size, font.dpi)
	text_width, measure.text_height_max = blf.dimensions(font.id, '-01234567890.')

	dpu = data.dot_per_blender_unit

	# draw width&height box
	draw_measure_box(data, config, font, measure)

	# draw circle
	draw_measure_circle(measure, config, dpu, alpha)

	col = config.color_measure[:3] + (config.color_measure[3] * alpha, )
	glColor4f(*col)

	# draw scale
	draw_measure_scale(data, config, measure, font)

	# draw subdivide
	#draw_measure_subdivide(config, measure)

	# draw line
	draw_measure_line(measure)

	# draw point
	draw_measure_ponit(measure)

	# draw snap
	draw_measure_snap(measure)

	# draw length
	draw_measure_length(measure, dpu, font)

	# draw angle
	draw_measure_angle(measure, config, font, alpha)

	# draw text
	glEnable(GL_BLEND)
	draw_measure_text(config, measure, alpha)


def get_active_region_id(event, return_data=False):
	#  Bug si vous appelez context.region en modal
	#  This isnt possible anymore in the latest Blender version:
	#  Only region can be used where invoked...
	region = bpy.context.region
	return region

#	 mouseco = [event.mouse_region_x, event.mouse_region_y]
#	 for area in bpy.context.screen.areas:
#		 for region in area.regions:
#			 if 0 <= mouseco[0] <= region.width and \
#				0 <= mouseco[1] <= region.height:
#				 if return_data:
#					 return region
#				 else:
#					 return region.id
#	 if return_data:
#		 return None
#	 else:
#		 return -1

def get_active_spaceview3d(event):
	return bpy.context.space_data
#	region = get_active_region_id(event, return_data=True)
#	rv3d = bpy.context.space_data.region_3d
#	if not rv3d:
#		return None
#	for area in bpy.context.screen.areas:
#		if area.type != 'VIEW_3D':
#			continue
#		for space in area.spaces:
#			if space.type == 'VIEW_3D':
#				if space.region_quadview:
#					if rv3d in (space.region_quadview_ne,
#								space.region_quadview_nw,
#								space.region_quadview_se,
#								space.region_quadview_sw):
#						return space
#				elif rv3d == space.region_3d:
#					return space
#	return None


def redraw_area_by_regionid(event, id=None):
#	if id is None:
#		id = get_active_region_id(event)
	bpy.context.area.tag_redraw()
#	for area in bpy.context.screen.areas:
#		if area.type == 'VIEW_3D':
#			for region in area.regions:
#				if region.id == id:
#					area.tag_redraw()
#					break


def text_draw_position_along_line(text, font, origin_vec, offset_vec, \
								  text_offset=None):
	# in 2D, retrun 3D
	text_width, text_height = blf.dimensions(font.id, text)
	if text_offset is None:
		text_offset = font.offset
	l = offset_vec.length
	offset_vec_normalized = offset_vec.normalized()
	v = (offset_vec_normalized[0] * (text_width / 2 + text_offset),
		  (offset_vec_normalized[1] * text_height / 2 + text_offset))
	vec = Vector([origin_vec[0] + offset_vec[0] + v[0] - text_width / 2, \
				  origin_vec[1] + offset_vec[1] + v[1] - text_height / 2, 0])
	return vec

def measure_shortcut_draw_set(measure, stype, event_type=None):
	rulers = measure.rulers
	active_index = measure.active_index
	active_ruler = measure.active('ruler')
	active_point = measure.active('point')

	def same_all(ls):
		if len(ls) <= 1:
			return True
		val = ls[0]
		for i in ls[1:]:
			if i != val:
				return False
		return True


	if stype == 'always':
		measure.always ^= 1

	elif stype == 'status':
		measure.draw_shortcut ^= 1

	elif stype == 'space_type':
		measure.space_type = '2D' if measure.space_type == '3D' else '3D'

	elif stype == 'column_+':
		if measure.draw_column_max < 6:
			measure.draw_column_max += 1
	elif stype == 'column_-':
		if measure.draw_column_max > 0:
			measure.draw_column_max -= 1

	elif stype == 'total_mode':
		if not active_ruler and rulers:
			vals = [ruler.total_mode for ruler in rulers]
			val = vals[0] ^ 1 if same_all(vals) else max(vals)
			for ruler in rulers:
				ruler.total_mode = val
		elif active_ruler:
			active_ruler.total_mode ^= 1

	elif stype == 'angle':
		if not active_ruler and rulers:
			vals = [ruler.draw_angle for ruler in rulers]
			val = vals[0] ^ 1 if same_all(vals) else max(vals)
			for ruler in rulers:
				ruler.draw_angle = val
		elif active_ruler:
			active_ruler.draw_angle ^= 1

	elif stype == 'length':
		if not active_ruler and rulers:
			vals = [ruler.draw_length for ruler in rulers]
			val = vals[0] ^ 1 if same_all(vals) else max(vals)
			for ruler in rulers:
				ruler.draw_length = val
		elif active_ruler:
			active_ruler.draw_length ^= 1

	elif stype == 'point':
		if not active_ruler and rulers:
			vals = [ruler.draw_point for ruler in rulers]
			val = vals[0] ^ 1 if same_all(vals) else max(vals)
			for ruler in rulers:
				ruler.draw_point = val
		elif active_ruler:
			active_ruler.draw_point ^= 1

	elif stype == 'scale':
		if not active_ruler and rulers:
			vals = [ruler.draw_scale for ruler in rulers]
			if same_all(vals):
				val = max(vals) + 1 if max(vals) < 2 else 0
			else:
				val = max(vals)
			for ruler in rulers:
				ruler.draw_scale = val
		elif active_ruler:
			active_ruler.draw_scale += 1 if active_ruler.draw_scale < 2 else -2

	elif stype == 'line_circle':
		if not active_ruler and rulers:
			vals = [ruler.draw_circle for ruler in rulers]
			if same_all(vals):
				val = max(vals) + 1 if max(vals) < 3 else 0
			else:
				val = max(vals)
			for ruler in rulers:
				ruler.draw_circle = val
		elif active_ruler:
			active_ruler.draw_circle += 1 if active_ruler.draw_circle < 3 else -3

	elif stype == 'circle':
		measure.draw_circle += 1 if measure.draw_circle < 3 else -3

	elif stype == 'subdivide':
		d = {}
		for cnt, s in enumerate(['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',\
											  'SIX', 'SEVEN', 'EIGHT', 'NINE']):
			d[s] = cnt
		if not active_ruler and rulers:
			for ruler in rulers:
				ruler.subdivide = d[event_type]
		elif active_ruler:
			active_ruler.subdivide = d[event_type]

def draw_callback_px(self, context):
	#global config_, color_, font_, font_mc_, data_, measure_
	#config = config_
	config = context.scene.ruler_config
	#color = color_
	data = data_
	measure = measure_

	if data.update(self, context) is False:
		return
	#if set_data(self, context, data) is False:
	#	 return

	### Draw ###
	glEnable(GL_BLEND)

	# mouse_cursor
	if data.mouseco and (config.cursor_type != 'none' and self.draw_cursor or \
						 measure.on):
		draw_cross_cursor(data, config, measure)

	# draw scale
	draw_scale(data, config)

	if config.draw_scale_type:
		draw_scale_type(data, config) # Affichage dans le coin supérieur droit

	if config.draw_unit:
		draw_unit(data, config) # Affichage dans le coin inférieur droit

	if data.mouseco and (config.draw_mouse_coordinate and self.draw_mc or measure.on):
		draw_mouse_coordinate(data, config)

	# measure
	if measure.on or measure.always:
		draw_measure(data, config, measure)

	# restore opengl defaults
	glLineWidth(1)
	glDisable(GL_BLEND)
	glColor4f(0.0, 0.0, 0.0, 1.0)
	blf.size(0, 11, bpy.context.user_preferences.system.dpi)




def scenechange(dummy):
	global viewchange
	viewchange = 1




class VIEW3D_OT_display_ruler(bpy.types.Operator):

	'''Draw Ruler (Ctrl+Shift+R: MeasureMode)'''
	bl_idname = 'view3d.display_ruler'
	bl_label = 'VIEW3D OT display ruler'
	#bl_options = {'REGISTER', 'UNDO'}

	# 1 modal=pass_through, invoke
	# 2 modal=finished, execute

	mode = IntProperty(name = 'Mode', default = 0, options = {'HIDDEN'})

	added = 0
#	disable_regions = {}

	draw_cursor = draw_mc = 0

	#config = color = font = font_mc = data = None

	def mousemove(self, measure):
		# changer des coordonnées du point selon le snap ou la transformation
		mouseco = measure.mouse_point.vec_window
		if len(measure.rulers) > 0:
			if measure.snap_X:
				x = measure.mouse_point.vec_world[0]
				y = measure.rulers[-1][-1].vec_world[1]
				z = measure.rulers[-1][-1].vec_world[2]
				measure.mouse_point.vec_world = Vector((x, y, z))
			if measure.snap_Y:
				x = measure.rulers[-1][-1].vec_world[0]
				y = measure.mouse_point.vec_world[1]
				z = measure.rulers[-1][-1].vec_world[2]
				measure.mouse_point.vec_world = Vector((x, y, z))
			if measure.snap_Z:
				x = measure.rulers[-1][-1].vec_world[0]
				y = measure.rulers[-1][-1].vec_world[1]
				z = measure.mouse_point.vec_world[2]
				measure.mouse_point.vec_world = Vector((x, y, z))
		if measure.drag == 0:
			if measure.snap_find:
				measure.mouse_point.vec_world = measure.snap_point.vec_world.copy()
		if measure.drag == 1:
			l = (measure.mouseco_drag_start - mouseco).length
			if l > measure.drag_threthold:
				measure.drag = 2
		elif measure.drag == 2: # translation
			point = measure.active('point')
			if measure.snap_find:
				point.vec_world = measure.snap_point.vec_world.copy()
			else:
				point.vec_world = measure.mouse_point.vec_world.copy()


	def add_handler(self, context):

		global _handle, started

		if context.area.type == 'VIEW_3D':
			#if not self.bl_label in context.window_manager.operators.keys(): # Ne sont pas ajoutés, Si vous ne retournez pas FINISHED dans invoke
			# Add the region OpenGL drawing callback
#			for region in context.area.regions:
#				if region.type == 'WINDOW':
#					break
			if not(started):
				started = 1
				'''
				Lors du démarrage à exécuter une seule fois exactement.
				Draw_callback_px est appelé à quelques minutes seulement ajouté.

				REGION de cible est également appelée en référence dans Bpy.data.screens
				self.__class__.region.callback_remove(handle)
				'''
				context.window_manager.modal_handler_add(self)

				bpy.app.handlers.scene_update_post.append(scenechange)
				
				_handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')

			print("Ruler display callback added")
			context.area.tag_redraw()

			return {'RUNNING_MODAL'}

		else:
			self.report({'WARNING'}, "View3D not found, cannot run operator")
			return {'CANCELLED'}

	def modal(self, context, event):

		global globmx, globmy, cursorstate, snapon, snapon3d, viewchange

		scn = bpy.context.scene

		if not(started):
			return {"FINISHED"}

		measure = measure_
		globmx = event.mouse_region_x
		globmy = event.mouse_region_y
		# toggle Measure Mode
		if event.type == 'R' and event.value == 'PRESS':
			if get_modifier(event) == SHIFT | CTRL:
#				if hasattr(context.window, 'event'): # patch
				region = get_active_region_id(event, return_data=True)
				region_id = region.id
				toggle = True
#				screen = context.screen
#				if screen.name in self.__class__.disable_regions:
#					if region.id in self.__class__.disable_regions[screen.name]:
#						toggle = False
				if toggle and bpy.context.space_data.region_3d:
					# drag cancel
					if measure.drag:
						if measure.drag == 2:
							point = measure.active('point')
							point.vec_world[:] = measure.point_bak.vec_world[:]
						measure.drag = 0

					measure.on ^= 1
					redraw_area_by_regionid(event)
					return {'RUNNING_MODAL'}

		if not(scn.Active):
			return {'PASS_THROUGH'}

		if measure.on:
			scn = bpy.context.scene
			if scn.Wire:
				bpy.context.space_data.viewport_shade = "WIREFRAME"
			else:
				if bpy.context.space_data.viewport_shade == "WIREFRAME":
					bpy.context.space_data.viewport_shade = "SOLID"
			if debug:
				if event.type not in ('MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', \
									  'TIMER1', 'COMMAND'):
					text = ''
					if event.shift:
						text += 'Shift + '
					if event.ctrl:
						text += 'Ctrl + '
					if event.alt:
						text += 'Alt + '
					if event.oskey:
						text += 'Cmd + '
					text += event.type
					if event.type == 'RIGHTMOUSE':
						text += ' (' + event.value + ')'
					if event.value == 'PRESS' or event.type == 'RIGHTMOUSE':
						print(text)
			need_redraw = 1 # supprimer redraw -1
			data = data_
			#config = config_
			config = context.scene.ruler_config

			data.update(self, context, measure_mode=True)

			cursor = Vector(context.scene.cursor_location)
			#mouseco = data.mouseco # window co (3D) valeur de z est toujours 0

			measure.update_mouse_point(data) # Ce n'est pas nécessaire lorsque measure.update_points_vec_window()
			mouseco = measure.mouse_point.vec_window

			measure.snap_find = 0

			if event.type == "S":
				if event.value == "RELEASE":
					measure.snapon = 0
					if event.shift:
						snapon3d = not(snapon3d)
						if snapon3d:
							snapon = 0
					else:
						snapon = not(snapon)
						if snapon:
							snapon3d = 0


			if snapon or snapon3d:
				# update mouse
				#measure.update_mouse_point(data)

				# mesh_fake_knife.py améliore les choses
				region = data.region
				sx = region.width
				sy = region.height
				persmat = bpy.context.space_data.region_3d.perspective_matrix
				subdivide = measure.snap_region_subdivide
				if measure.snapon == 0 or viewchange:
					viewchange = 0
					# recalc
					spaceview3d = get_active_spaceview3d(event)
					all_origins = spaceview3d.show_all_objects_origin
					if debug:
						t = time.time()
					'''measure.snap_vmat = make_snap_matrix(region, None,
										100, measure.snap_to_visible,
										measure.snap_to_dm, all_origins)
					'''
					snap_to = ('selected', 'visible')[measure.snap_to_visible]
					snap_to_origin = (snap_to, 'visible')[all_origins]
					measure.snap_vmat, measure.snap_vwmat = make_snap_matrix(sx, sy, persmat, \
									 snap_to, snap_to_origin, \
									 apply_modifiers=measure.snap_to_dm, \
									 objects=None, subdivide=100)
					if debug:
						print('calc {0:.4f}s'.format(time.time() - t))
					#measure.ctrl = 1
				snap_vmat = measure.snap_vmat
				snap_vwmat = measure.snap_vwmat
				##snap_imat = measure.snap_imat
				# Col: colonne dans la direction horizontale, row: à la verticale
				snap_range = measure.snap_range
				snap_vec, snap_vecw = get_vector_from_snap_maxrix(mouseco, max(sx, sy), \
													   subdivide, snap_vmat, \
													   snap_vwmat, snap_range)
				if snap_vec:
					if snapon: # snap 2D
						snap_vec_3d = convert_window_to_world(
										(snap_vec[0], snap_vec[1], mouseco[2]),
										persmat, region.width, region.height)
#						snap_vec_3d = snap_vecw
						measure.snap_point.vec_world[:] = snap_vec_3d[:]
						measure.snap_find = 2
					elif snapon3d: # snap 3D
#						snap_vec_3d = convert_window_to_world(
#									   (snap_vec[0], snap_vec[1], snap_vec[2]),
#									   persmat, region.width, region.height)
						snap_vec_3d = snap_vecw
						measure.snap_point.vec_world[:] = snap_vec_3d[:]
						measure.snap_find = 3


				if measure.snapon == 0:
					measure.snapon = 1
					self.mousemove(measure)
					redraw_area_by_regionid(event)
					need_redraw = -1

			else:
				if measure.snapon == 1:
					measure.snapon = 0
					self.mousemove(measure)
					redraw_area_by_regionid(event)
					need_redraw = -1


			if event.type == 'MOUSEMOVE':
				self.mousemove(measure)
				bpy.context.region.tag_redraw()

			elif event.type == 'ESC':
				if event.value == 'PRESS':
					if measure.active_index:
						if measure.drag:
							# drag cancel
							measure.drag = 0
							point = measure.active('point')
							point.vec_world[:] = measure.point_bak.vec_world[:]
						if measure.active_index:
							ruler = measure.active('ruler')
							if len(ruler) == 1:
								measure.rulers.remove(ruler)
						measure.active_index = None


			elif event.type == 'RIGHTMOUSE' and data.in_region:
				if event.value == 'PRESS':
					if measure.drag == 0:
						if measure.rulers:
							# change Active Point
							measure.update_points_vec_window(data) # Coordonner le calcul
							new_index = active_point = None
							for i, ruler in enumerate(measure.rulers):
								for j, point in enumerate(ruler):
									p = point.vec_window.copy()
									p[2] = 0.0
									l = (p - mouseco).length
									if l <= config.measure_select_point_threthold:
										if new_index is None:
											new_index = [i, j]
											active_point = measure.active('point', new_index)
										elif l <= (active_point.vec_window - mouseco).length:
												new_index = [i, j]

							# delete single point
							remove = False
							if measure.active_index is None:
								pass
							elif new_index is None and \
							   measure.active_index is not None:
								remove = True
							elif new_index[0] != measure.active_index[0] or \
								 new_index[1] != measure.active_index[1]:
								remove = True
							if remove:
								ruler = measure.active('ruler')
								if len(ruler) == 1:
									measure.rulers.remove(ruler)

							measure.active_index = new_index
						if measure.active_index is not None:
							measure.drag = 1
							measure.mouseco_drag_start = mouseco.copy()
							active_point = measure.active('point')
							measure.point_bak = active_point.copy()
					else:
						# drag cancel
						measure.drag = 0
						point = measure.active('point')
						point.vec_world[:] = measure.point_bak.vec_world[:]
				elif event.value == 'RELEASE':
					if measure.drag == 1:
						measure.drag = 0
			elif event.type == 'LEFTMOUSE' and event.value == 'PRESS' and data.in_region:
				measure.snap_X = 0
				measure.snap_Y = 0
				measure.snap_Z = 0
				if measure.drag == 0:
					#vec_world = measure.update_mouse_point(data) # Si vous devez appuyer sans bouger la souris après clic
					if (snapon or snapon3d) and measure.snap_find:
						vec_world = measure.snap_point.vec_world
					else:
						#vec_world = measure.update_mouse_point(data)
						vec_world = measure.mouse_point.vec_world
					point = MeasurePoint(vec_world)
					i = measure.active_index
					active_ruler = measure.active('ruler')
					active_point = measure.active('point')
					if event.shift and measure.rulers and active_ruler:
						if active_point == active_ruler[0] and \
						   len(active_ruler) != 1:
							# Ajouté au sommet
							active_ruler.insert(0, point)
							measure.active_index[1] = 0
						elif active_point == active_ruler[-1]:
							# Ajouté à l'arrière
							active_ruler.append(point)
							measure.active_index[1] = len(active_ruler) - 1
						else:
							# insérer
							active_ruler.insert(i[1] + 1, point)
							measure.active_index[1] += 1
					elif measure.rulers and i is not None:
						# règle sélectionnée, videz le point supplémentaire
						active_ruler[:] = [point]
						measure.active_index[1] = 0
					else:
						# Ajout d'une nouvelle règle
						measure.rulers.append(MeasureRuler([point]))
						measure.active_index = [len(measure.rulers) - 1, 0]
				elif measure.drag == 1:
					# cancel
					measure.drag = 0
					point = measure.active('point')
					point.vec_world[:] = measure.point_bak.vec_world[:]
				elif measure.drag == 2:
					# assign draging Point
					measure.drag = 0

			elif event.type == 'X' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure.snap_X ^= 1
					if measure.snap_X == 1:
						measure.snap_Y = 0
						measure.snap_Z = 0
			elif event.type == 'Y' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure.snap_Y ^= 1
					if measure.snap_Y == 1:
						measure.snap_X = 0
						measure.snap_Z = 0
			elif event.type == 'Z' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure.snap_Z ^= 1
					if measure.snap_Z == 1:
						measure.snap_Y = 0
						measure.snap_X = 0
			elif event.type == 'O' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure.snap_to_visible ^= 1
					#elif get_modifier(event) == SHIFT:
					#	 measure.snap_to_dm ^= 1
			elif event.type == 'M' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure.snap_to_dm ^= 1

			elif event.type == 'R' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'always')

			elif event.type == 'H' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'status')

			elif event.type == 'D' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'space_type')

			elif event.type == 'C' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'circle')

			elif event.type == 'T' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'total_mode')

			elif event.type == 'L' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'length')

			elif event.type == 'A' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'angle')

			elif event.type == 'N' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'scale')

			elif event.type == 'P' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'point')

			elif event.type == 'E' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'line_circle')

			elif event.type == 'NUMPAD_PLUS' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'column_+')

			elif event.type == 'NUMPAD_MINUS' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'column_-')

			elif event.type in ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', \
										  'SIX', 'SEVEN', 'EIGHT', 'NINE'] and \
													get_modifier(event) == CTRL:
				if event.value == 'PRESS':
					measure_shortcut_draw_set(measure, 'subdivide', event.type)

			elif event.type == 'Q':
				if event.value == 'PRESS':
					modifier = get_modifier(event)
					# remove point or ruler
					ruler = measure.active('ruler')
					if ruler:
						if len(ruler) >= 2 and modifier == 0:
							ruler.remove(measure.active('point'))
							active_index = measure.active_index
							if active_index[1] >= len(ruler): # hors de portée
								measure.active_index[1] = len(ruler) - 1
						else:
							measure.rulers.remove(ruler)
							measure.active_index = None
					else:
						measure.rulers = []

			elif event.type == 'W' and get_modifier(event) == 0:
				if event.value == 'PRESS':
					ruler = measure.active('ruler')
					if ruler:
						ruler.reverse()
						pi = len(ruler) -1 - ruler.index(measure.active('point'))
						measure.active_index[1] = pi
					else:
						for ruler in measure.rulers:
							ruler.reverse()
			else:
				if need_redraw == 1:
					need_redraw = 0
			for shortcut in pass_keyboard_inputs:
				if event.type == shortcut.type:
					if shortcut.any or \
					   (event.shift == shortcut.shift and
						event.ctrl == shortcut.ctrl and
						event.alt == shortcut.alt and
						event.oskey == shortcut.oskey):
						return {'PASS_THROUGH'}

			if event.type == 'MOUSEMOVE' or need_redraw == 1:
			#if need_redraw == 1:
				# Redessiné par le snap ont été exécutés。 (need_redraw == -1)
				if context.area:
					id = get_active_region_id(event)
					if self.regionid != id:
						# Lorsque activeRegion est actif, redessiner l'ancien
						#if self.regionid not in self.__class__.disable_regions:
						redraw_area_by_regionid(event, self.regionid)
						self.regionid = id
						return {'PASS_THROUGH'}
						# Afin d'éviter que le curseur de la souris quitte le redimensionnement
					else:
						id = data.region.id # 3dview
#						if id not in self.__class__.disable_regions:
							#if data.in_region:
						redraw_area_by_regionid(event, id)

			if not data.in_region: # Y at-il une souris dans la vue3D?
				# Transmis si la souris est dans la vue3D
				return {'PASS_THROUGH'}
			else:
				return {'RUNNING_MODAL'}

		else:
			# measure off
			if event.type == "C":
				if event.value == "PRESS":
					cursorstate = not(cursorstate)
					if cursorstate == 0:
						if self.__class__.draw_cursor is not None:
							self.__class__.draw_cursor = 1
							self.__class__.draw_mc = 1
							region = context.region
							if region:
								region.tag_redraw()
						return {'RUNNING_MODAL'}
					else:
						if self.__class__.draw_cursor is not None:
							self.__class__.draw_cursor = 0
							self.__class__.draw_mc = 0
							region = context.region
							if region:
								region.tag_redraw()
						return {'RUNNING_MODAL'}

			if event.type in ('MOUSEMOVE',):
				if context.area and \
				   (self.__class__.draw_cursor or self.__class__.draw_mc):
					id = get_active_region_id(event)
					if self.regionid != id:
						# Lorsque activeRegion est actif, redessiner l'ancien
						#if self.regionid not in self.__class__.disable_regions:
						redraw_area_by_regionid(event, self.regionid)
						self.regionid = id
					else:
#						if id not in self.__class__.disable_regions:
						redraw_area_by_regionid(event, id)
			return {'PASS_THROUGH'}

	def invoke(self, context, event):

		global started, color_background, default_config

		scn = bpy.context.scene
#		started = 1

		color_background = bpy.context.user_preferences.themes['Default'].user_preferences.space.back
		default_config['color_background'] = list(color_background) + [1.0]	# alpha
		bpy.types.Scene.ruler_config = PointerProperty(name='Ruler Config',
													   type=RulerConfig,
													   options={'HIDDEN'})
#		scn.ruler_config.color_background = d['color_background']
		print (scn.ruler_config.color_background)
		print ("BACKGROUND")

		if bpy.context.space_data.viewport_shade == "WIREFRAME":
			scn.Wire = True
		else:
			scn.Wire = False
		#global config_
		window = context.window
		screen = context.screen
		area = context.area
		mode = self.mode
		if mode == 1:
			# reset
			config = context.scene.ruler_config
#			enable_patch = config.config_check()
			enable_patch = True
			self.__class__.draw_cursor = 1 if enable_patch else None
			self.__class__.draw_mc = config.draw_mouse_coordinate
			self.regionid = context.region.id

#			self.__class__.disable_regions = {}

			retval = self.add_handler(context)
			return {'RUNNING_MODAL'}

#		elif mode == 1:
			# draw enable
#			disable_regions = self.__class__.disable_regions
#			if area.type == 'VIEW_3D':
#				for region in area.regions:
#					if region.type == 'WINDOW':
#						id = region.id
#						if screen.name in disable_regions:
#							if id in disable_regions[screen.name]:
#								disable_regions[screen.name].remove(id)
#								area.tag_redraw()
#			return {'FINISHED'}

		elif mode == -1:
			bpy.types.SpaceView3D.draw_handler_remove(_handle, "WINDOW")
			started = 0
			bpy.context.area.tag_redraw()
			# draw disable
#			disable_regions = self.__class__.disable_regions
#			if area.type == 'VIEW_3D':
#				for region in area.regions:
#					if region.type == 'WINDOW':
#						id = region.id
#						if screen.name not in disable_regions:
#							disable_regions[screen.name] = set([id])
#						else:
#							disable_regions[screen.name].add(id)
#						area.tag_redraw()
			return {'FINISHED'}
		elif mode == 2:
			if self.__class__.draw_cursor is not None:
				self.__class__.draw_cursor = 1
				self.__class__.draw_mc = 1
			return {'FINISHED'}
		elif mode == 3:
			if self.__class__.draw_cursor is not None:
				self.__class__.draw_cursor = 0
				self.__class__.draw_mc = 0
			return {'FINISHED'}
		'''elif mode == 4:
			self.__class__.draw_mc = 1
			return {'FINISHED'}
		elif mode == 5:
			self.__class__.draw_mc = 0
			return {'FINISHED'}
		'''



bpy.types.Scene.Active = bpy.props.BoolProperty(
		name = "Active",
		description = "Measuring active or normal Blender operation?",
		default = True)

bpy.types.Scene.Follow = bpy.props.BoolProperty(
		name = "Follow Origin",
		description = "Does the ruler stick to same origin or to screen?",
		default = True)

bpy.types.Scene.oriX = bpy.props.FloatProperty(
		name = "OriginX",
		description = "Ruler origin X coordinate",
		default = 0,
		min = -100,
		max = 100)

bpy.types.Scene.oriY = bpy.props.FloatProperty(
		name = "OriginY",
		description = "Ruler origin Y coordinate",
		default = 0,
		min = -100,
		max = 100)

bpy.types.Scene.oriZ = bpy.props.FloatProperty(
		name = "OriginZ",
		description = "Ruler origin Z coordinate",
		default = 0,
		min = -100,
		max = 100)

bpy.types.Scene.Wire = bpy.props.BoolProperty(
		name = "Wire",
		description = "Turn to wireframe for non-occlusion.",
		default = True)

bpy.types.Scene.Verts = bpy.props.BoolProperty(
		name = "Verts",
		description = "Snap to verts",
		default = True)

bpy.types.Scene.Edges = bpy.props.BoolProperty(
		name = "Edges",
		description = "Snap to edges",
		default = True)

bpy.types.Scene.Faces = bpy.props.BoolProperty(
		name = "Faces",
		description = "Snap to faces",
		default = True)

class VIEW3D_PT_ruler(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_label = "Ruler"
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		return context.area is not None

	def draw(self, context):
		scn = context.scene
		col = self.layout.column(align=True)
#		col.operator('view3d.display_ruler', text='modal_handler_add()').mode=0
#		row = col.row(align=True)
		if not(started):
			col.operator('view3d.display_ruler', text='Enable').mode=1
		else:
			measure = measure_
			if measure.on:
				self.layout.prop(scn, "Active")
			if scn.Active:
				col.operator('view3d.display_ruler', text='Disable').mode=-1
				self.layout.prop(scn, "Follow")
				col = self.layout.column(align=True)
				col.prop(scn, "oriX")
				col.prop(scn, "oriY")
				col.prop(scn, "oriZ")
				if measure.on:
					row = self.layout.row()
					row.label("Snap To:")
					row.prop(scn, "Wire")
					row = self.layout.row()
					row.prop(scn, "Verts")
					row.prop(scn, "Edges")
					row.prop(scn, "Faces")

		#col.separator()
#		row = col.row(align=True)
#		row.operator('view3d.display_ruler', text='Cursor ON').mode=2
#		row.operator('view3d.display_ruler', text='Cursor OFF').mode=3
		'''row = col.row(align=True)
		row.operator('view3d.display_ruler', text='MC ON').mode=4
		row.operator('view3d.display_ruler', text='MC OFF').mode=5
		'''

class RulerToOrig(bpy.types.Operator):
	bl_idname = "ruler.rulertoorig"
	bl_label = "Ruler->Orig"
	bl_description = "Snap rulers to custom origin."
	bl_options = {"REGISTER"}

	def invoke(self, context, event):
		global data_

		data = data_
		rv3d = bpy.context.space_data.region_3d
		offset = convert_world_to_window(data.rulerorigin, None, 0, 0)
		offset[2] = 0

		data.center_ofs = offset

		return {'FINISHED'}




def register():
	bpy.utils.register_module(__name__)

#	 bpy.types.Scene.PointerProperty(attr='ruler_config', name='Ruler Config',
#									type=RulerConfig, options={'HIDDEN'})



def unregister():
	bpy.utils.unregister_module(__name__)



if __name__ == "__main__":
	register()
