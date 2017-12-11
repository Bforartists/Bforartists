
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

import bpy
import copy
import bgl
import blf
from blf import ROTATION
import mathutils
from mathutils import *
from math import *
#from math import sin, cos, tan, atan, degrees, radians, asin, acos
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent

from .utils_geometry import *
from .utils_function import *

# GET ADDON COLOR SETTINGS AND PRODUCE VALUES:

class SettingsStore:
    add_set_graph_dict = None

# Use global SettingsStore class to store dict so it is not recreated each call
# todo : come up with better way for storing and checking add-on settings
def addon_settings_graph(key):
    addon_prefs = bpy.context.user_preferences.addons[__package__].preferences

    if SettingsStore.add_set_graph_dict is not None:
        add_set_graph_dict = SettingsStore.add_set_graph_dict
        settings_change = (
            add_set_graph_dict['col_scheme'] != addon_prefs.np_col_scheme,
            add_set_graph_dict['size_num'] != addon_prefs.np_size_num,
            add_set_graph_dict['scale_dist'] != addon_prefs.np_scale_dist,
            add_set_graph_dict['suffix_dist'] != addon_prefs.np_suffix_dist,
            add_set_graph_dict['display_badge'] != addon_prefs.np_display_badge,
            add_set_graph_dict['size_badge'] != addon_prefs.np_size_badge)
        if True in settings_change:
            SettingsStore.add_set_graph_dict = None

    if SettingsStore.add_set_graph_dict is None:
        #print(" add_set_graph_dict == None ")
        add_set_graph_dict = {}
        add_set_graph_dict.update(
            col_scheme = addon_prefs.np_col_scheme,
            size_num = addon_prefs.np_size_num,
            scale_dist = addon_prefs.np_scale_dist,
            suffix_dist = addon_prefs.np_suffix_dist,
            display_badge = addon_prefs.np_display_badge,
            size_badge = addon_prefs.np_size_badge)

        if addon_prefs.np_col_scheme == 'csc_default_grey':
            add_set_graph_dict.update(
                col_font_np = (0.95, 0.95, 0.95, 1.0),
                col_font_instruct_main = (0.67, 0.67, 0.67, 1.0),
                col_font_instruct_shadow = (0.15, 0.15, 0.15, 1.0),
                col_font_keys = (0.15, 0.15, 0.15, 1.0),
                col_field_keys_aff = (0.51, 0.51, 0.51, 1.0),
                col_field_keys_neg = (0.41, 0.41, 0.41, 1.0),

                col_line_main = (0.9, 0.9, 0.9, 1.0),
                col_line_shadow = (0.1, 0.1, 0.1, 0.25),
                col_num_main = (0.95, 0.95, 0.95, 1.0),
                col_num_shadow = (0.0, 0.0, 0.0, 0.75),

                col_gw_line_cross = (0.25, 0.35, 0.4, 0.87),
                col_gw_line_base_free = (1.0, 1.0, 1.0, 0.85),
                col_gw_line_base_lock_x = (1.0, 0.0, 0.0, 1.0),
                col_gw_line_base_lock_y = (0.5, 0.75, 0.0, 1.0),
                col_gw_line_base_lock_z = (0.0, 0.2, 0.85, 1.0),
                col_gw_line_base_lock_arb = (0.0, 0.0, 0.0, 0.5),
                col_gw_line_all = (1.0, 1.0, 1.0, 0.85),

                col_gw_fill_base_x = (1.0, 0.0, 0.0, 0.2),
                col_gw_fill_base_y = (0.0, 1.0, 0.0, 0.2),
                col_gw_fill_base_z = (0.0, 0.2, 0.85, 0.2),
                col_gw_fill_base_arb = (0.0, 0.0, 0.0, 0.15),

                col_bg_fill_main_run = (1.0, 0.5, 0.0, 1.0),
                col_bg_fill_main_nav = (0.5, 0.75 ,0.0 ,1.0),
                col_bg_fill_square = (0.0, 0.0, 0.0, 1.0),
                col_bg_fill_aux = (0.4, 0.15, 0.75, 1.0), #(0.4, 0.15, 0.75, 1.0) (0.2, 0.15, 0.55, 1.0)
                col_bg_line_symbol = (1.0, 1.0, 1.0, 1.0),
                col_bg_font_main = (1.0, 1.0, 1.0, 1.0),
                col_bg_font_aux = (1.0, 1.0, 1.0, 1.0)
            )

        elif addon_prefs.np_col_scheme == 'csc_school_marine':
            add_set_graph_dict.update(
                col_font_np = (0.25, 0.35, 0.4, 0.87),
                col_font_instruct_main = (1.0, 1.0, 1.0, 1.0),
                col_font_instruct_shadow = (0.25, 0.35, 0.4, 0.6),
                col_font_keys = (1.0, 1.0, 1.0, 1.0),
                col_field_keys_aff = (0.55, 0.6, 0.64, 1.0),
                col_field_keys_neg = (0.67, 0.72, 0.76, 1.0),

                col_line_main = (1.0, 1.0, 1.0, 1.0),
                col_line_shadow = (0.1, 0.1, 0.1, 0.25),
                col_num_main = (0.25, 0.35, 0.4, 1.0), #(1.0, 0.5, 0.0, 1.0)
                col_num_shadow = (1.0, 1.0, 1.0, 1.0),

                col_gw_line_cross = (0.25, 0.35, 0.4, 0.87),
                col_gw_line_base_free = (1.0, 1.0, 1.0, 0.85),
                col_gw_line_base_lock_x = (1.0, 0.0, 0.0, 1.0),
                col_gw_line_base_lock_y = (0.5, 0.75, 0.0, 1.0),
                col_gw_line_base_lock_z = (0.0, 0.2, 0.85, 1.0),
                col_gw_line_base_lock_arb = (0.0, 0.0, 0.0, 0.5),
                col_gw_line_all = (1.0, 1.0, 1.0, 0.85),

                col_gw_fill_base_x = (1.0, 0.0, 0.0, 0.2),
                col_gw_fill_base_y = (0.0, 1.0, 0.0, 0.2),
                col_gw_fill_base_z = (0.0, 0.2, 0.85, 0.2),
                col_gw_fill_base_arb = (0.0, 0.0, 0.0, 0.15),

                col_bg_fill_main_run = (1.0, 0.5, 0.0, 1.0),
                col_bg_fill_main_nav = (0.5, 0.75 ,0.0 ,1.0),
                col_bg_fill_square = (0.0, 0.0, 0.0, 1.0),
                col_bg_fill_aux = (0.4, 0.15, 0.75, 1.0), #(0.4, 0.15, 0.75, 1.0) (0.2, 0.15, 0.55, 1.0)
                col_bg_line_symbol = (1.0, 1.0, 1.0, 1.0),
                col_bg_font_main = (1.0, 1.0, 1.0, 1.0),
                col_bg_font_aux = (1.0, 1.0, 1.0, 1.0)
            )
        SettingsStore.add_set_graph_dict = add_set_graph_dict.copy()

    return SettingsStore.add_set_graph_dict[key]


# ON-SCREEN INSTRUCTIONS:

def display_instructions(region, rv3d, instruct, keys_aff, keys_nav, keys_neg):


    userpref = bpy.context.user_preferences
    system = userpref.system
    rwtools = 0
    rwui = 0

    np_print(system.window_draw_method, system.use_region_overlap)


    if system.use_region_overlap:
        if system.window_draw_method in ('TRIPLE_BUFFER', 'AUTOMATIC') :

            area = bpy.context.area
            np_print('GO', area.regions)
            for r in area.regions:
                if r.type == 'TOOLS':
                    rwtools = r.width
                elif r.type == 'UI':
                    rwui = r.width

    np_print('rwtools', rwtools, 'rwui', rwui)
    field_keys_y = 46
    field_keys_x = 80
    rw = region.width
    rh = region.height
    np_print('rw, rh', rw, rh)

    expand = False
    crop = False

    len_aff_max = rw - 140 - rwtools - rwui
    len_aff = len(keys_aff) * 5
    len_neg = len(keys_neg) * 5
    len_ins = len(instruct) * 18
    if len_aff > len_aff_max: expand = True

    rw_min = 480
    rh_min = 280
    if rw - rwtools - rwui < rw_min or rh < rh_min: crop = True


    version = '020'
    font_id = 0

    keys_aff_1 = copy.deepcopy(keys_aff)
    keys_aff_2 = ' '
    if expand:
        keys_aff_1 = ''
        keys_aff_2 = ''
        np_print('len(keys_aff)', len(keys_aff))
        stop = 0
        for i in range (0, len(keys_aff)-1):
            #np_print(keys_aff[i])
            if keys_aff[i] == ',' and i * 5 <= len_aff_max and i > stop:
                stop = i
        np_print('stop', stop)
        for i in range(0, stop + 1):
            keys_aff_1 = keys_aff_1 + keys_aff[i]
        for i in range(stop + 2, len(keys_aff)):
            keys_aff_2 = keys_aff_2 + keys_aff[i]
        np_print(keys_aff_1)
        np_print(keys_aff_2)


    field_keys_aff_1 = [[field_keys_x + rwtools, field_keys_y + 21], [field_keys_x + rwtools, field_keys_y + 39], [rw - int(field_keys_x / 2) - rwui, field_keys_y + 39], [rw - int(field_keys_x / 2) - rwui, field_keys_y + 21]]
    field_keys_aff_2 = copy.deepcopy(field_keys_aff_1)
    field_keys_neg = [[field_keys_x + rwtools, field_keys_y], [field_keys_x + rwtools, field_keys_y + 18], [rw - int(field_keys_x / 2) - rwui, field_keys_y + 18], [rw - int(field_keys_x / 2) - rwui, field_keys_y]]
    if expand:
        field_keys_aff_2 = copy.deepcopy(field_keys_neg)
        field_keys_neg = [[field_keys_x + rwtools, field_keys_y - 21], [field_keys_x + rwtools, field_keys_y - 3], [rw - int(field_keys_x / 2) - rwui, field_keys_y - 3], [rw - int(field_keys_x / 2) - rwui, field_keys_y - 21]]

    size_font_np = 25
    size_font_instruct = 21
    size_font_keys = 11
    len_np_ins = len_ins + int(size_font_np * 2.1)

    pos_font_np_x = (rw - len_np_ins / 2) / 2 + rwtools / 2 - rwui / 2
    pos_font_np_y = 150
    if crop: pos_font_np_y = 75
    pos_font_instruct_x = pos_font_np_x + int(size_font_np * 2.1)
    pos_font_instruct_y = pos_font_np_y + 4
    pos_font_keys_aff_1_x = field_keys_x + 8 + rwtools
    pos_font_keys_aff_1_y = field_keys_y + 26
    pos_font_keys_aff_2_x = copy.deepcopy(pos_font_keys_aff_1_x)
    pos_font_keys_aff_2_y = copy.deepcopy(pos_font_keys_aff_1_y)
    pos_font_keys_nav_x = field_keys_x + 8 + rwtools
    pos_font_keys_nav_y = field_keys_y + 5
    pos_font_keys_neg_x = rw - 52 - len_neg - rwui
    np_print('len_neg', len_neg)
    np_print('pos_font_keys_neg_x', pos_font_keys_neg_x)
    pos_font_keys_neg_y = field_keys_y + 5
    if expand:
        pos_font_keys_aff_2_x = field_keys_x + 8 + rwtools
        pos_font_keys_aff_2_y = field_keys_y + 5
        pos_font_keys_nav_x = field_keys_x + 8 + rwtools
        pos_font_keys_nav_y = field_keys_y - 16
        pos_font_keys_neg_x = rw - 52 - len_neg - rwui
        pos_font_keys_neg_y = field_keys_y - 16 - rwui

    col_font_np = addon_settings_graph('col_font_np')
    col_font_instruct_main = addon_settings_graph('col_font_instruct_main')
    col_font_instruct_shadow = addon_settings_graph('col_font_instruct_shadow')
    col_font_keys = addon_settings_graph('col_font_keys')
    col_field_keys_aff = addon_settings_graph('col_field_keys_aff')
    col_field_keys_neg = addon_settings_graph('col_field_keys_neg')



    # instructions - NP:

    bgl.glColor4f(*col_font_np)
    blf.size(font_id, size_font_np, 72)
    blf.position(font_id, pos_font_np_x, pos_font_np_y, 0)
    blf.draw(font_id, 'NP')

    blf.enable(font_id, ROTATION)
    ang = radians(90)
    blf.size(font_id, int(size_font_np / 2.2), 72)
    blf.rotation(font_id, ang)
    blf.position(font_id, pos_font_np_x + int(size_font_np * 1.72) , pos_font_np_y - 2, 0)
    blf.draw(font_id, version)
    blf.disable(font_id, ROTATION)

    # instructions - instruct:

    bgl.glColor4f(*col_font_instruct_shadow)
    blf.position(font_id, pos_font_instruct_x + 1, pos_font_instruct_y - 1, 0)
    blf.size(font_id, size_font_instruct, 72)
    blf.draw(font_id, instruct)

    bgl.glColor4f(*col_font_instruct_main)
    blf.position(font_id, pos_font_instruct_x, pos_font_instruct_y, 0)
    blf.size(font_id, size_font_instruct, 72)
    blf.draw(font_id, instruct)

    bgl.glDisable(bgl.GL_BLEND)

    # instructions - keys - backdrop fields:

    bgl.glEnable(bgl.GL_BLEND)

    if crop == False:

        bgl.glColor4f(*col_field_keys_aff)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for co in field_keys_aff_1:
            bgl.glVertex2f(*co)
        bgl.glEnd()

        bgl.glColor4f(*col_field_keys_aff)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for co in field_keys_aff_2:
            bgl.glVertex2f(*co)
        bgl.glEnd()

        bgl.glColor4f(*col_field_keys_neg)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for co in field_keys_neg:
            bgl.glVertex2f(*co)
        bgl.glEnd()


        # instructions - keys - writing:

        bgl.glColor4f(*col_font_keys)
        blf.size(font_id, size_font_keys, 72)

        blf.position(font_id, pos_font_keys_aff_1_x, pos_font_keys_aff_1_y, 0)
        blf.draw(font_id, keys_aff_1)

        blf.position(font_id, pos_font_keys_aff_2_x, pos_font_keys_aff_2_y, 0)
        blf.draw(font_id, keys_aff_2)

        blf.position(font_id, pos_font_keys_nav_x, pos_font_keys_nav_y, 0)
        blf.draw(font_id, keys_nav)

        blf.position(font_id, pos_font_keys_neg_x, pos_font_keys_neg_y, 0)
        blf.draw(font_id, keys_neg)



# ON-SCREEN DISPLAY OF GEOWIDGET:

def display_geowidget(region, rv3d, fac, ro_hor, q, helploc, n, qdef, geowidget_base, geowidget_top, geowidget_rest):


    geowidget_cross = [(0.0 ,2.1 ,0.0), (0.0, 0.9, 0.0), (-2.1 ,0.0 ,0.0), (-0.9, 0.0, 0.0)]


    # drawing of geowidget - cross part:
    for i, co in enumerate(geowidget_cross):
        co = Vector(co)
        co = co*fac
        geowidget_cross[i] = co

    geowidget_cross = rotate_graphic(geowidget_cross, ro_hor)
    geowidget_cross = rotate_graphic(geowidget_cross, q)
    geowidget_cross = translate_graphic(geowidget_cross, helploc)

    col_gw_line_cross = addon_settings_graph('col_gw_line_cross')
    col_gw_line_base_free = addon_settings_graph('col_gw_line_base_free')
    col_gw_line_base_lock_x = addon_settings_graph('col_gw_line_base_lock_x')
    col_gw_line_base_lock_y = addon_settings_graph('col_gw_line_base_lock_y')
    col_gw_line_base_lock_z = addon_settings_graph('col_gw_line_base_lock_z')
    col_gw_line_base_lock_arb = addon_settings_graph('col_gw_line_base_lock_arb')
    col_gw_line_all = addon_settings_graph('col_gw_line_all')

    col_gw_fill_base_x = addon_settings_graph('col_gw_fill_base_x')
    col_gw_fill_base_y = addon_settings_graph('col_gw_fill_base_y')
    col_gw_fill_base_z = addon_settings_graph('col_gw_fill_base_z')
    col_gw_fill_base_arb = addon_settings_graph('col_gw_fill_base_arb')



    bgl.glColor4f(*col_gw_line_cross)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i, co in enumerate(geowidget_cross):
        if i in range(0, 2): # range is always - first as is, second one one higher than last
            #np_print(i)
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
            geowidget_cross[i] = co
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i, co in enumerate(geowidget_cross):
        if i in range(2, 4): # range is always - first as is, second one one higher than last
            #np_print(i)
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
            geowidget_cross[i] = co
    bgl.glEnd()


    # drawing of geowidget - base part:

    for i, co in enumerate(geowidget_base):
        co = Vector(co)
        co = co*fac
        geowidget_base[i] = co

    geowidget_base = rotate_graphic(geowidget_base, ro_hor)
    geowidget_base = rotate_graphic(geowidget_base, q)
    geowidget_base = translate_graphic(geowidget_base, helploc)


    n = n.to_tuple()
    n = list(n)
    for i, co in enumerate(n): n[i] = abs(round(co,4))
    np_print('n for color', n)


    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(*col_gw_line_base_free)
    bgl.glLineWidth(1)
    if qdef != None:
        if n[0] == 0.0 and n[1] == 0.0 and n[2] == 1.0: bgl.glColor4f(*col_gw_line_base_lock_z)
        elif n[0] == 1.0 and n[1] == 0.0 and n[2] == 0.0: bgl.glColor4f(*col_gw_line_base_lock_x)
        elif n[0] == 0.0 and n[1] == 1.0 and n[2] == 0.0: bgl.glColor4f(*col_gw_line_base_lock_y)
        else:
            bgl.glColor4f(*col_gw_line_base_lock_arb)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i, co in enumerate(geowidget_base):
        #np_print(i)
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
        bgl.glVertex2f(*co)
        geowidget_base[i] = co
    bgl.glVertex2f(*geowidget_base[0])
    bgl.glEnd()

    bgl.glColor4f(*col_gw_fill_base_arb)
    if n[0] == 0.0 and n[1] == 0.0 and n[2] == 1.0:
        bgl.glColor4f(*col_gw_fill_base_z)
        np_print('go_Z')
    elif n[0] == 1.0 and n[1] == 0.0 and n[2] == 0.0:
        bgl.glColor4f(*col_gw_fill_base_x)
        np_print('go_X')
    elif n[0] == 0.0 and n[1] == 1.0 and n[2] == 0.0:
        bgl.glColor4f(*col_gw_fill_base_y)
        np_print('go_Y')
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    for co in geowidget_base:
        bgl.glVertex2f(*co)
    bgl.glEnd()


    # drawing of geowidget - top part:

    if geowidget_top != None:
        for i, co in enumerate(geowidget_top):
            co = Vector(co)
            co = co*fac
            geowidget_top[i] = co

        geowidget_top = rotate_graphic(geowidget_top, ro_hor)
        geowidget_top = rotate_graphic(geowidget_top, q)
        geowidget_top = translate_graphic(geowidget_top, helploc)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(*col_gw_line_all)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for i, co in enumerate(geowidget_top):
            #np_print(i)
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
            geowidget_top[i] = co
        bgl.glVertex2f(*geowidget_top[0])
        bgl.glEnd()


    # drawing of geowidget - rest part:

    if geowidget_rest != None:
        for i, co in enumerate(geowidget_rest):
            co = Vector(co)
            co = co*fac
            geowidget_rest[i] = co

        geowidget_rest = rotate_graphic(geowidget_rest, ro_hor)
        geowidget_rest = rotate_graphic(geowidget_rest, q)
        geowidget_rest = translate_graphic(geowidget_rest, helploc)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(*col_gw_line_all)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for i, co in enumerate(geowidget_rest):
            #np_print(i)
            co = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            bgl.glVertex2f(*co)
            geowidget_rest[i] = co
        bgl.glVertex2f(*geowidget_rest[0])
        bgl.glEnd()


# ON-SCREEN DISPLAY OF DISTANCE BETWEEN TWO 3D POINTS:

def display_distance_between_two_points(region, rv3d, p1_3d, p2_3d):

    size_num = addon_settings_graph('size_num')
    scale_dist = addon_settings_graph('scale_dist')
    suffix_dist = addon_settings_graph('suffix_dist')

    if type(p1_3d) is not Vector:
        p1_3d = Vector(p1_3d)

    if type(p2_3d) is not Vector:
        p2_3d = Vector(p2_3d)


    p1_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p1_3d)
    p2_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p2_3d)

    if p1_2d is None:
        p1_2d = 0.0, 0.0
        p2_2d = 0.0, 0.0

    def get_pts_mean(locs2d, max):
        res = 0
        for i in locs2d:
            if i > max:
                res += max
            elif i > 0:
                res += i
        return res / 2

    mean_x = get_pts_mean( (p1_2d[0], p2_2d[0]), region.width )
    mean_y = get_pts_mean( (p1_2d[1], p2_2d[1]), region.height )
    distloc = mean_x, mean_y

    dist_3d = (p2_3d - p1_3d).length
    dist_3d_rnd = abs(round(dist_3d, 2))
    dist = str(dist_3d_rnd)

    dist_num = (p2_3d - p1_3d).length * scale_dist
    dist_num = abs(round(dist_num, 2))


    if suffix_dist != 'None':
        dist = str(dist_num) + suffix_dist
    else:
        dist = str(dist_num)

    col_num_main = addon_settings_graph('col_num_main')
    col_num_shadow = addon_settings_graph('col_num_shadow')


    #np_print('dist = ', dist, 'distloc = ', distloc, 'dist_num = ', dist_num)
    if dist_num not in (0, 'a'):
        bgl.glColor4f(*col_num_shadow)
        font_id = 0
        blf.size(font_id, size_num, 72)
        blf.position(font_id, (distloc[0]-1), (distloc[1]-1), 0)
        blf.draw(font_id, dist)

        bgl.glColor4f(*col_num_main)
        font_id = 0
        blf.size(font_id, size_num, 72)
        blf.position(font_id, distloc[0], distloc[1], 0)
        blf.draw(font_id, dist)


    return (dist_num, dist)


# LINE:

def display_line_between_two_points(region, rv3d, p1_3d, p2_3d):

    bgl.glEnable(bgl.GL_BLEND)

    p1_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p1_3d)
    p2_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, p2_3d)

    if p1_2d is None:
        p1_2d = (0.0, 0.0)
        p2_2d = (0.0, 0.0)

    col_line_main = addon_settings_graph('col_line_main')
    col_line_shadow = addon_settings_graph('col_line_shadow')

    bgl.glColor4f(*col_line_shadow)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f((p1_2d[0]-1),(p1_2d[1]-1))
    bgl.glVertex2f((p2_2d[0]-1),(p2_2d[1]-1))
    bgl.glEnd()
    bgl.glColor4f(*col_line_main)
    bgl.glLineWidth(1.4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glVertex2f(*p1_2d)
    bgl.glVertex2f(*p2_2d)
    bgl.glEnd()

    bgl.glDisable(bgl.GL_BLEND)


# BADGE:

def display_cursor_badge(co2d, symbol, badge_mode, message_main, message_aux, aux_num, aux_str):

    display_badge = addon_settings_graph('display_badge')
    size_badge = addon_settings_graph('size_badge')
    col_bg_fill_main_run = addon_settings_graph('col_bg_fill_main_run')
    col_bg_fill_main_nav = addon_settings_graph('col_bg_fill_main_nav')
    col_bg_fill_aux = addon_settings_graph('col_bg_fill_aux')
    col_bg_fill_square = addon_settings_graph('col_bg_fill_square')
    col_bg_line_symbol = addon_settings_graph('col_bg_line_symbol')
    col_bg_font_main = addon_settings_graph('col_bg_font_main')
    col_bg_font_aux = addon_settings_graph('col_bg_font_aux')




    if badge_mode == 'RUN':
        col_bg_fill_main = col_bg_fill_main_run
    elif badge_mode == 'NAV':
        col_bg_fill_main = col_bg_fill_main_nav

    if display_badge:
        font_id = 0
        square = [[17, 30], [17, 40], [27, 40], [27, 30]]
        rectangle = [[27, 30], [27, 40], [67, 40], [67, 30]]
        ipx = 29
        ipy = 33
        for co in square:
            co[0] = round((co[0] * size_badge), 0) - (size_badge * 10) + co2d[0]
            co[1] = round((co[1] * size_badge), 0) - (size_badge * 25) + co2d[1]
        for co in rectangle:
            co[0] = round((co[0] * size_badge), 0) - (size_badge * 10) + co2d[0]
            co[1] = round((co[1] * size_badge), 0) - (size_badge * 25) + co2d[1]
        for co in symbol:
            co[0] = round((co[0] * size_badge), 0) - (size_badge * 10) + co2d[0]
            co[1] = round((co[1] * size_badge), 0) - (size_badge * 25) + co2d[1]

        ipx = round((ipx * size_badge), 0) - (size_badge * 10) + co2d[0]
        ipy = round((ipy * size_badge), 0) - (size_badge * 25) + co2d[1]
        ipsize = int(round((6 * size_badge), 0))

        bgl.glEnable(bgl.GL_BLEND)


        bgl.glColor4f(*col_bg_fill_square)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in square:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        bgl.glColor4f(*col_bg_fill_main)
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        for x, y in rectangle:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        bgl.glColor4f(*col_bg_line_symbol)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x, y in symbol:
            bgl.glVertex2f(x, y)
        bgl.glEnd()

        bgl.glColor4f(*col_bg_font_main)
        blf.position(font_id, ipx, ipy, 0)
        blf.size(font_id, ipsize, 72)
        blf.draw(font_id, message_main)

        if message_aux != None:

            bgl.glColor4f(*col_bg_fill_aux)
            bgl.glBegin(bgl.GL_TRIANGLE_FAN)
            if aux_num == None and aux_str == None:
                rectangle = [[17, 30], [17, 40], [67, 40], [67, 30]]
                for co in rectangle:
                    co[0] = round((co[0] * size_badge), 0) - (size_badge * 10) + co2d[0]
                    co[1] = round((co[1] * size_badge), 0) - (size_badge * 25) + co2d[1]
            for x, y in rectangle:
                if aux_num == None and aux_str == None:
                    bgl.glVertex2f(x, (y - (size_badge * 10)))
                    np_print('111111111111')
                elif aux_num != None:
                    bgl.glVertex2f(x, y - (size_badge*35))
                    np_print('222222222222')
                elif aux_str != None:
                    bgl.glVertex2f(x, y - (size_badge*25))
                    np_print('3333333333333')
            bgl.glEnd()

            bgl.glColor4f(*col_bg_font_aux)
            if aux_num == None and aux_str == None:
                blf.position(font_id, ipx, ipy - (size_badge * 10), 0)
            elif aux_num != None:
                blf.position(font_id, ipx, ipy - (size_badge*35), 0)
            elif aux_str != None:
                blf.position(font_id, ipx, ipy - (size_badge*25), 0)
            blf.size(font_id, ipsize, 72)
            blf.draw(font_id, message_aux)

        if aux_num != None:
            bgl.glColor4f(*col_bg_font_aux)
            blf.position(font_id, ipx, int(ipy - size_badge*25), 0)
            blf.size(font_id, int(size_badge*24), 72)
            blf.draw(font_id, aux_num)

        if aux_str != None:
            bgl.glColor4f(*col_bg_font_aux)
            blf.position(font_id, ipx, int(ipy - size_badge*15), 0)
            blf.size(font_id, ipsize, 72)
            blf.draw(font_id, aux_num)

        '''
        if step == 'continuous':
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots1:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots2:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for x, y in dots3:
                bgl.glVertex2f(x, y)
            bgl.glEnd()
        '''
        bgl.glDisable(bgl.GL_BLEND)

