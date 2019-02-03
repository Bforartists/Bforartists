'''
BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

END GPL LICENSE BLOCK
'''

from copy import deepcopy
from math import degrees, radians, pi

import bpy
import bmesh
import bgl
import blf
from mathutils import geometry, Euler, Quaternion, Vector
from bpy_extras import view3d_utils
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d_to_reg2d
from bpy_extras.view3d_utils import region_2d_to_vector_3d as reg2d_to_vec3d
from bpy_extras.view3d_utils import region_2d_to_location_3d as reg2d_to_loc3d
from bpy_extras.view3d_utils import region_2d_to_origin_3d as reg2d_to_org3d

# "Constant" values
(
    X,
    Y,
    Z,

    CLICK_CHECK,
    WAIT_FOR_POPUP,
    GET_0_OR_180,
    DO_TRANSFORM,

    MOVE,
    SCALE,
    ROTATE,
) = range(10)

# globals
curr_meas_stor = 0.0
new_meas_stor = None
popup_active = False


#print("Loaded add-on.\n")  # debug


class Colr:
    red    = 1.0, 0.0, 0.0, 0.6
    green  = 0.0, 1.0, 0.0, 0.6
    blue   = 0.0, 0.0, 1.0, 0.6
    white  = 1.0, 1.0, 1.0, 1.0
    grey   = 1.0, 1.0, 1.0, 0.4
    black  = 0.0, 0.0, 0.0, 1.0
    yellow = 1.0, 1.0, 0.0, 0.6
    brown  = 0.15, 0.15, 0.15, 0.20


class RotDat:
    placeholder = True


# Refreshes mesh drawing in 3D view and updates mesh coordinate
# data so ref_pts are drawn at correct locations.
# Using editmode_toggle to do this seems hackish, but editmode_toggle seems
# to be the only thing that updates both drawing and coordinate info.
def editmode_refresh():
    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()


def backup_blender_settings():
    backup = [
        deepcopy(bpy.context.tool_settings.use_snap),
        deepcopy(bpy.context.tool_settings.snap_element),
        deepcopy(bpy.context.tool_settings.snap_target),
        deepcopy(bpy.context.space_data.pivot_point),
        deepcopy(bpy.context.space_data.transform_orientation),
        deepcopy(bpy.context.space_data.show_manipulator),
        deepcopy(bpy.context.scene.cursor_location)]
    return backup


def init_blender_settings():
    bpy.context.tool_settings.use_snap = False
    bpy.context.tool_settings.snap_element = 'VERTEX'
    bpy.context.tool_settings.snap_target = 'CLOSEST'
    bpy.context.space_data.pivot_point = 'ACTIVE_ELEMENT'
    bpy.context.space_data.transform_orientation = 'GLOBAL'
    bpy.context.space_data.show_manipulator = False
    return


def restore_blender_settings(backup):
    bpy.context.tool_settings.use_snap = deepcopy(backup[0])
    bpy.context.tool_settings.snap_element = deepcopy(backup[1])
    bpy.context.tool_settings.snap_target = deepcopy(backup[2])
    bpy.context.space_data.pivot_point = deepcopy(backup[3])
    bpy.context.space_data.transform_orientation = deepcopy(backup[4])
    bpy.context.space_data.show_manipulator = deepcopy(backup[5])
    bpy.context.scene.cursor_location = deepcopy(backup[6])
    return


def flts_alm_eq(flt_a, flt_b):
    tol = 0.0001
    return flt_a > (flt_b - tol) and flt_a < (flt_b + tol)


# todo : replace with flt_lists_alm_eq?
def vec3s_alm_eq(vec_a, vec_b):
    X, Y, Z = 0, 1, 2
    if flts_alm_eq(vec_a[X], vec_b[X]):
        if flts_alm_eq(vec_a[Y], vec_b[Y]):
            if flts_alm_eq(vec_a[Z], vec_b[Z]):
                return True
    return False


# assume both float lists are same size?
def flt_lists_alm_eq(ls_a, ls_b):
    for i in range(len(ls_a)):
        if not flts_alm_eq(ls_a[i], ls_b[i]):
            return False
    return True


class MenuStore:
    def __init__(self):
        self.cnt = 0
        self.active = 0  # unused ?
        # todo : replace above with self.current ?
        self.txtcolrs = []
        self.tcoords = []
        self.texts = []
        self.arrows = []  # arrow coordinates


class MenuHandler:
    def __init__(self, title, tsize, act_colr, dis_colr, toolwid, reg):
        self.dpi = bpy.context.preferences.system.dpi
        self.title = title
        # todo : better solution than None "magic numbers"
        self.menus = [None]  # no menu for 0
        self.menu_cnt = len(self.menus)
        self.current = 0  # current active menu
        self.tsize = tsize  # text size
        self.act_colr = act_colr
        self.dis_colr = dis_colr  # disabled color
        self.reg = reg  # region

        view_offset = 36, 45  # box left top start
        self.box_y_pad = 8  # vertical space between boxes

        fontid = 0
        blf.size(fontid, tsize, self.dpi)
        lcase_wid, lcase_hgt = blf.dimensions(fontid, "n")
        ucase_wid, ucase_hgt = blf.dimensions(fontid, "N")
        bot_space = blf.dimensions(fontid, "gp")[1] - lcase_hgt
        self.full_hgt = blf.dimensions(fontid, "NTgp")[1]

        arr_wid, arr_hgt = 12, 16
        arrow_base = (0, 0), (0, arr_hgt), (arr_wid, arr_hgt/2)
        aw_adj, ah_adj = arr_wid * 1.5, (arr_hgt - ucase_hgt) / 2
        self.arrow_pts = []
        for a in arrow_base:
            self.arrow_pts.append((a[0] - aw_adj, a[1] - ah_adj))

        self.blef = view_offset[0] + toolwid  # box left start
        self.titlco = self.blef // 2, self.reg.height - view_offset[1]
        self.btop = self.titlco[1] - (self.full_hgt // 1.5)
        self.txt_y_pad = bot_space * 2

    def add_menu(self, strings):
        self.menus.append(MenuStore())
        new = self.menus[-1]
        btop = self.btop
        tlef = self.blef  # text left
        new.cnt = len(strings)
        for i in range(new.cnt):
            new.txtcolrs.append(self.dis_colr)
            new.texts.append(strings[i])
            bbot = btop - self.full_hgt
            new.tcoords.append((tlef, bbot))
            btop = bbot - self.box_y_pad
            new.arrows.append((
                (self.arrow_pts[0][0] + tlef, self.arrow_pts[0][1] + bbot),
                (self.arrow_pts[1][0] + tlef, self.arrow_pts[1][1] + bbot),
                (self.arrow_pts[2][0] + tlef, self.arrow_pts[2][1] + bbot)))
        new.txtcolrs[new.active] = self.act_colr
        self.menu_cnt += 1

    def update_active(self, change):
        menu = self.menus[self.current]
        if menu is None:
            return
        menu.txtcolrs[menu.active] = self.dis_colr
        menu.active = (menu.active + change) % menu.cnt
        menu.txtcolrs[menu.active] = self.act_colr

    def change_menu(self, new):
        self.current = new

    def get_mode(self):
        menu = self.menus[self.current]
        return menu.texts[menu.active]

    #def rebuild_menus(self)  # add in case blender window size changes?
    #    return

    def draw(self, menu_visible):
        menu = self.menus[self.current]
        # prepare to draw text
        font_id = 0
        blf.size(font_id, self.tsize, self.dpi)
        # draw title
        bgl.glColor4f(*self.dis_colr)
        blf.position(font_id, self.titlco[0], self.titlco[1], 0)
        blf.draw(font_id, self.title)
        # draw menu
        if menu_visible and menu is not None:
            for i in range(menu.cnt):
                bgl.glColor4f(*menu.txtcolrs[i])
                blf.position(font_id, menu.tcoords[i][0], menu.tcoords[i][1], 0)
                blf.draw(font_id, menu.texts[i])

            # draw arrow
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glColor4f(*self.act_colr)
            bgl.glBegin(bgl.GL_LINE_LOOP)
            for p in menu.arrows[menu.active]:
                bgl.glVertex2f(*p)
            bgl.glEnd()


# === 3D View mouse location and button code ===
class ViewButton():
    def __init__(self, colr_on, colr_off, txt_sz, txt_colr, offs=(0, 0)):
        self.dpi = bpy.context.preferences.system.dpi
        self.is_drawn = False
        self.ms_over = False  # mouse over button
        self.wid = 0
        self.coords = None
        #self.co_outside_btn = None
        self.co2d = None
        self.colr_off = colr_off  # colr when mouse not over button
        self.colr_on = colr_on  # colr when mouse over button
        self.txt = ""
        self.txt_sz = txt_sz
        self.txt_colr = txt_colr
        self.txt_co = None
        self.offset = Vector(offs)

        # Set button height and text offsets (to determine where text would
        # be placed within button). Done in __init__ as this will not change
        # during program execution and prevents having to recalculate these
        # values every time text is changed.
        font_id = 0
        blf.size(font_id, self.txt_sz, self.dpi)
        samp_txt_max = "Tgp"  # text with highest and lowest pixel values
        x, max_y =  blf.dimensions(font_id, samp_txt_max)
        y = blf.dimensions(font_id, "T")[1]  # T = sample text
        y_diff = (max_y - y)

        self.hgt = int(max_y + (y_diff * 2))
        self.txt_x_offs = int(x / (len(samp_txt_max) * 2) )
        self.txt_y_offs = int(( self.hgt - y) / 2) + 1
        # added 1 to txt_y_offs to compensate for possible int rounding

    # replace text string and update button width
    def set_text(self, txt):
        font_id = 0
        self.txt = txt
        blf.size(font_id, self.txt_sz, self.dpi)
        w = blf.dimensions(font_id, txt)[0]  # get text width
        self.wid = w + (self.txt_x_offs * 2)
        return

    def set_btn_coor(self, co2d):
        #offs_2d = Vector((-self.wid / 2, 25))
        offs_2d = Vector((-self.wid / 2, 0))
        new2d = co2d + offs_2d
        
        # co_bl == coordinate bottom left, co_tr == coordinate top right
        co_bl = new2d[0], new2d[1]
        co_tl = new2d[0], new2d[1] + self.hgt
        co_tr = new2d[0] + self.wid, new2d[1] + self.hgt
        co_br = new2d[0] + self.wid, new2d[1]
        self.coords = co_bl, co_tl, co_tr, co_br
        self.txt_co = new2d[0] + self.txt_x_offs, new2d[1] + self.txt_y_offs
        self.ms_chk = co_bl[0], co_tr[0], co_bl[1], co_tr[1]

    def pt_inside_btn2(self, mouse_co):
        mx, my = mouse_co[0], mouse_co[1]
        if mx < self.ms_chk[0] or mx > self.ms_chk[1]:
            return False
        if my < self.ms_chk[2] or my > self.ms_chk[3]:
            return False
        return True
    
    def draw_btn(self, btn_loc, mouse_co, highlight_mouse=False):
        if btn_loc is not None:
            offs_loc = btn_loc + self.offset
            font_id = 0
            colr = self.colr_off
            self.set_btn_coor(offs_loc)
            if self.pt_inside_btn2(mouse_co):
                colr = self.colr_on
                self.ms_over = True
            else:
                self.ms_over = False
            # draw button box
            bgl.glColor4f(*colr)
            bgl.glBegin(bgl.GL_LINE_STRIP)
            for coord in self.coords:
                bgl.glVertex2f(coord[0], coord[1])
            bgl.glVertex2f(self.coords[0][0], self.coords[0][1])
            bgl.glEnd()
            # draw outline around button box
            if highlight_mouse and self.ms_over:
                bgl.glColor4f(*self.colr_off)
                HO = 4  # highlight_mouse offset
                offs = (-HO, -HO), (-HO, HO), (HO, HO), (HO, -HO)
                bgl.glBegin(bgl.GL_LINE_STRIP)
                for i, coord in enumerate(self.coords):
                    bgl.glVertex2f(coord[0] + offs[i][0], coord[1] + offs[i][1])
                bgl.glVertex2f(self.coords[0][0] + offs[0][0], self.coords[0][1] + offs[0][1])
                bgl.glEnd()
            # draw button text
            bgl.glColor4f(*self.txt_colr)
            blf.size(font_id, self.txt_sz, self.dpi)
            blf.position(font_id, self.txt_co[0], self.txt_co[1], 0)
            blf.draw(font_id, self.txt)
        else:
            self.ms_over = False


# Used for mod_pt mode
class TempPoint():
    def __init__(self):
        self.ls = []  # point list
        self.cnt = 0
        self.co3d = None
        self.max_cnt = 50

    def average(self):
        vsum = Vector()
        for p in self.ls:
            vsum += p
        self.co3d = vsum / self.cnt

    def find_pt(self, co3d):
        found_idx = None
        for i in range(self.cnt):
            if self.ls[i] == co3d:
                found_idx = i
                break
        return found_idx

    def rem_pt(self, idx):
        self.ls.pop(idx)
        self.cnt -= 1
        if self.cnt > 0:
            self.average()
        else:
            self.co3d = None

    def try_add(self, co3d):
        found_idx = self.find_pt(co3d)
        if found_idx is None:
            if len(self.ls) < self.max_cnt:
                self.ls.append(co3d.copy())
                self.cnt += 1
                self.average()

    def reset(self, co3d):
        self.co3d = co3d.copy()
        self.ls = [co3d.copy()]
        self.cnt = 1

    def get_co(self):
        return self.co3d.copy()

    def print_vals(self):  # debug
        print("self.cnt:", self.cnt)
        print("self.ls:", self.cnt)
        print("self.co3d:", self.co3d)
        for i in range(self.cnt):
            print("  [" + str(i) + "]:", [self.ls[i]])


# Basically this is just a "wrapper" around a 3D coordinate (Vector type)
# to centralize certain Reference Point features and make them easier to
# work with.
# note: if co3d is None, point does not "exist"
class ReferencePoint:
    def __init__(self, ptype, colr, co3d=None):
        self.ptype = ptype  # debug?
        self.colr = colr  # color (tuple), for displaying point in 3D view
        self.co3d = co3d  # 3D coordinate (Vector)

    # use this method to get co2d because "non-existing" points
    # will lead to a function call like this and throw an error:
    # loc3d_to_reg2d(reg, rv3d, None)
    def get_co2d(self):
        co2d = None
        if self.co3d is not None:
            reg = bpy.context.region
            rv3d = bpy.context.region_data
            co2d = loc3d_to_reg2d(reg, rv3d, self.co3d)
        return co2d

    def copy(self):
        return ReferencePoint( self.ptype, self.colr, self.co3d.copy() )

    def print_vals(self):  # debug
        print("self.ptype:", self.ptype)
        print("self.colr :", self.colr)
        print("self.co3d :", self.co3d)


def init_ref_pts(self):
    self.pts = [
        ReferencePoint("fre", Colr.green),
        ReferencePoint("anc", Colr.red),
        ReferencePoint("piv", Colr.yellow)
    ]
    # todo : move this part of initialization elsewhere?
    RotDat.piv_norm = None
    RotDat.new_ang_r = None
    RotDat.ang_diff_r = None
    RotDat.axis_lock = None
    RotDat.lock_pts = None
    RotDat.rot_pt_pos = None
    RotDat.rot_pt_neg = None
    RotDat.arc_pts = None


def set_piv(self):
    #if self.pt_cnt == 2:
    if self.pt_cnt == 3:
        rpts = [p.co3d for p in self.pts]
        RotDat.piv_norm = geometry.normal(*rpts)

def set_mouse_highlight(self):
    if self.pt_cnt < 3:
        self.highlight_mouse = True
    else:
        self.highlight_mouse = False


def in_ref_pts(self, co3d, skip_idx=None):
    p_idxs = [0, 1, 2][:self.pt_cnt]
    # skip_idx so co3d is not checked against itself
    if skip_idx is not None:
        p_idxs.remove(skip_idx)
    found = False
    for i in p_idxs:
        if vec3s_alm_eq(self.pts[i].co3d, co3d):
            found = True
            self.swap_pt = i  # todo : better solution than this
            break
    return found


def add_pt(self, co3d):
    if not in_ref_pts(self, co3d):
        self.pts[self.pt_cnt].co3d = co3d
        self.pt_cnt += 1
        self.menu.change_menu(self.pt_cnt)
        if self.pt_cnt > 1:
            updatelock_pts(self, self.pts)
        set_mouse_highlight(self)
        ''' Begin Debug
        cnt = self.pt_cnt - 1
        pt_fnd_str = str(self.pts[cnt].co3d)
        pt_fnd_str = pt_fnd_str.replace("<Vector ", "Vector(")
        pt_fnd_str = pt_fnd_str.replace(">", ")")
        print("ref_pt_" + str(cnt) + ' =', pt_fnd_str)
        #print("ref pt added:", self.cnt, "cnt:", self.cnt+1)
        End Debug '''


def rem_ref_pt(self, idx):
    # hackery or smart, you decide...
    if idx != self.pt_cnt - 1:
        keep_idx = [0, 1, 2][:self.pt_cnt]
        keep_idx.remove(idx)
        for i in range(len(keep_idx)):
            self.pts[i].co3d = self.pts[keep_idx[i]].co3d.copy()
    self.pt_cnt -= 1
    self.menu.change_menu(self.pt_cnt)
    # set "non-existing" points to None
    for j in range(self.pt_cnt, 3):
        self.pts[j].co3d = None
    if self.pt_cnt > 1:
        updatelock_pts(self, self.pts)
    else:
        RotDat.axis_lock = None
    self.highlight_mouse = True


def add_select(self):
    if self.pt_cnt < 3:
        if bpy.context.mode == "OBJECT":
            if len(bpy.context.selected_objects) > 0:
                for obj in bpy.context.selected_objects:
                    add_pt(self, obj.location.copy())
                    if self.pt_cnt > 2:
                        break
        elif bpy.context.mode == "EDIT_MESH":
            m_w = bpy.context.edit_object.matrix_world
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            if len(bm.select_history) > 0:
                exit_loop = False  # simplify checking...
                for sel in bm.select_history:
                    sel_verts = []
                    if type(sel) is bmesh.types.BMVert:
                        sel_verts = [sel]
                    elif type(sel) is bmesh.types.BMEdge:
                        sel_verts = sel.verts
                    elif type(sel) is bmesh.types.BMFace:
                        sel_verts = sel.verts
                    for v in sel_verts:
                        v_co3d = m_w * v.co
                        add_pt(self, v_co3d)
                        if self.pt_cnt > 2:
                            exit_loop = True
                            break
                    if exit_loop:
                        break


# todo : find way to merge this with add_select ?
def add_select_multi(self):
    if self.multi_tmp.cnt < self.multi_tmp.max_cnt:
        if bpy.context.mode == "OBJECT":
            if len(bpy.context.selected_objects) > 0:
                for obj in bpy.context.selected_objects:
                    self.multi_tmp.try_add(obj.location)
                    if self.multi_tmp.cnt == self.multi_tmp.max_cnt:
                        break
        elif bpy.context.mode == "EDIT_MESH":
            m_w = bpy.context.edit_object.matrix_world
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            if len(bm.select_history) > 0:
                exit_loop = False  # simplify checking...
                for sel in bm.select_history:
                    sel_verts = []
                    if type(sel) is bmesh.types.BMVert:
                        sel_verts = [sel]
                    elif type(sel) is bmesh.types.BMEdge:
                        sel_verts = sel.verts
                    elif type(sel) is bmesh.types.BMFace:
                        sel_verts = sel.verts
                    for v in sel_verts:
                        v_co3d = m_w * v.co
                        self.multi_tmp.try_add(v_co3d)
                        if self.multi_tmp.cnt == self.multi_tmp.max_cnt:
                            exit_loop = True
                            break
                    if exit_loop:
                        break
        if in_ref_pts(self, self.multi_tmp.get_co(), self.mod_pt):
            self.report({'WARNING'}, 'Points overlap.')
        self.pts[self.mod_pt].co3d = self.multi_tmp.get_co()


def swap_ref_pts(self, pt1, pt2):
    temp = self.pts[pt1].co3d.copy()
    self.pts[pt1].co3d = self.pts[pt2].co3d.copy()
    self.pts[pt2].co3d = temp


# For adding multi point without first needing a reference point
# todo : clean up TempPoint so this function isn't needed
# todo : find way to merge this with add_select_multi
def new_select_multi(self):
    def enable_multi_mode(self):
        if self.grab_pt is not None:
            self.multi_tmp.__init__()
            self.multi_tmp.co3d = Vector()
            self.mod_pt = self.grab_pt
            self.grab_pt = None
        elif self.mod_pt is None:
            self.multi_tmp.__init__()
            self.multi_tmp.co3d = Vector()
            self.mod_pt = self.pt_cnt
            self.pt_cnt += 1

    if bpy.context.mode == "OBJECT":
        if len(bpy.context.selected_objects) > 0:
            enable_multi_mode(self)
            for obj in bpy.context.selected_objects:
                self.multi_tmp.try_add(obj.location)
                if self.multi_tmp.cnt == self.multi_tmp.max_cnt:
                    break
        else:
            return
    elif bpy.context.mode == "EDIT_MESH":
        m_w = bpy.context.edit_object.matrix_world
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        if len(bm.select_history) > 0:
            enable_multi_mode(self)
            exit_loop = False  # simplify checking...
            for sel in bm.select_history:
                sel_verts = []
                if type(sel) is bmesh.types.BMVert:
                    sel_verts = [sel]
                elif type(sel) is bmesh.types.BMEdge:
                    sel_verts = sel.verts
                elif type(sel) is bmesh.types.BMFace:
                    sel_verts = sel.verts
                for v in sel_verts:
                    v_co3d = m_w * v.co
                    self.multi_tmp.try_add(v_co3d)
                    if self.multi_tmp.cnt == self.multi_tmp.max_cnt:
                        exit_loop = True
                        break
                if exit_loop:
                    break
        else:
            return


def exit_multi_mode(self):
    m_co3d = self.multi_tmp.get_co()
    if in_ref_pts(self, m_co3d, self.mod_pt):
        self.report({'ERROR'}, "Point overlapped another and was removed.")
        rem_ref_pt(self, self.mod_pt)
    else:
        self.pts[self.mod_pt].co3d = m_co3d
        if self.pt_cnt > 1:
            updatelock_pts(self, self.pts)
        set_mouse_highlight(self)
    self.mod_pt = None
    set_help_text(self, "CLICK")


def get_axis_line_co(p1, p2, x_max, y_max):
    if None not in (p1, p2):
        x_min, y_min = 0.0, 0.0
        x1, y1 = p1
        x2, y2 = p2
        if flts_alm_eq(x1, x2):
            return Vector((x1, y_min)), Vector((x1, y_max))
        elif flts_alm_eq(y1, y2):
            return Vector((x_min, y1)), Vector((x_max, y1))
        tol = 0.0001
        xb_min, xb_max = x_min - tol, x_max + tol
        yb_min, yb_max = y_min - tol, y_max + tol
        ln_pts = []
        slope = (y2 - y1) / (x2 - x1)

        x_bot = ((y_min - y1) / slope) + x1
        if x_bot > xb_min and x_bot < xb_max:
            ln_pts.append( Vector((x_bot, y_min)) )
        x_top = ((y_max - y1) / slope) + x1
        if x_top > xb_min and x_top < xb_max:
            ln_pts.append( Vector((x_top, y_max)) )
            if len(ln_pts) > 1: return ln_pts
        y_lef = (slope * (x_min - x1)) + y1
        if y_lef > yb_min and y_lef < yb_max:
            ln_pts.append( Vector((x_min, y_lef)) )
            if len(ln_pts) > 1: return ln_pts
        y_rgt = (slope * (x_max - x1)) + y1
        if y_rgt > yb_min and y_rgt < yb_max:
            ln_pts.append( Vector((x_max, y_rgt)) )
            if len(ln_pts) > 1: return ln_pts


# Returns the closest object origin or vertex to the supplied 2D location
# as 3D Vector.
# Returns None if no found coordinate closer than minimum distance.
def find_closest_point(loc):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    shortest_dist = 40.0  # minimum distance from loc
    closest = None
    for obj in bpy.context.scene.objects:
        o_co2d = loc3d_to_reg2d(region, rv3d, obj.location)
        if o_co2d is None:
            continue
        dist2d = (loc - o_co2d).length
        if dist2d < shortest_dist:
            shortest_dist = dist2d
            closest = obj.location.copy()
        if obj.type == 'MESH':
            if len(obj.data.vertices) > 0:
                for v in obj.data.vertices:
                    v_co3d = obj.matrix_world * v.co
                    v_co2d = loc3d_to_reg2d(region, rv3d, v_co3d)
                    if v_co2d is not None:
                        dist2d = (loc - v_co2d).length
                        if dist2d < shortest_dist:
                            shortest_dist = dist2d
                            closest = v_co3d
    return closest


def draw_pt_2d(pt_co, pt_color, pt_size):
    if pt_co is not None:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glPointSize(pt_size)
        bgl.glColor4f(*pt_color)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*pt_co)
        bgl.glEnd()
    return


def draw_line_2d(pt_co_1, pt_co_2, pt_color):
    if None not in (pt_co_1, pt_co_2):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glPointSize(15)
        bgl.glColor4f(*pt_color)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*pt_co_1)
        bgl.glVertex2f(*pt_co_2)
        bgl.glEnd()
    return


def closest_to_point(pt, pts):
    smallest_dist = 15.0
    closest, pt_idx = None, None
    for p in range(len(pts)):
        if pts[p] is not None:
            tmp_d = (pt - pts[p]).length
            if tmp_d < smallest_dist:
                smallest_dist = tmp_d
                closest = pts[p]
                pt_idx = p
    return closest, pt_idx


def set_arc_pts(ref_pts):
    fre, anc, piv = ref_pts[0].co3d, ref_pts[1].co3d, ref_pts[2].co3d
    arc_pts = []
    ang = (fre - piv).angle(anc - piv)
    deg_ang = degrees(ang)
    if deg_ang > 0.01 and deg_ang < 179.99:
        piv_norm = geometry.normal(fre, piv, anc)
        rot_val = Quaternion(piv_norm, ang)
        rotated = fre - piv
        rotated.rotate(rot_val)
        rotated += piv
        rot_ang = (anc - piv).angle(rotated - piv)
        if not flts_alm_eq(rot_ang, 0.0):
            ang = -ang
        dis_p_f = (piv - fre).length
        dis_p_a = (piv - anc).length
        if dis_p_f < dis_p_a:
            ratio = 0.5
        else:  # dis_p_a < dis_p_f:
            ratio = dis_p_a / dis_p_f * 0.5
        mid_piv_free = piv.lerp(fre, ratio)
        arc_pts = [mid_piv_free]
        steps = abs( int(degrees(ang) // 10) )
        ang_step = ang / steps
        mid_align = mid_piv_free - piv
        for a in range(1, steps):
            rot_val = Quaternion(piv_norm, ang_step * a)
            temp = mid_align.copy()
            temp.rotate(rot_val)
            arc_pts.append(temp + piv)
        # in case steps <= 1
        rot_val = Quaternion(piv_norm, ang)
        temp = mid_align.copy()
        temp.rotate(rot_val)
        arc_pts.append(temp + piv)

    elif RotDat.axis_lock is not None:
        #if RotDat.axis_lock == 'X':
        #    rot_val = Euler((pi*2, 0.0, 0.0), 'XYZ')
        if RotDat.axis_lock == 'X':
            piv_norm = 1.0, 0.0, 0.0
        elif RotDat.axis_lock == 'Y':
            piv_norm = 0.0, 1.0, 0.0
        elif RotDat.axis_lock == 'Z':
            piv_norm = 0.0, 0.0, 1.0
        dis_p_f = (piv - fre).length
        dis_p_a = (piv - anc).length
        if dis_p_f < dis_p_a:
            ratio = 0.5
        else:  # dis_p_a < dis_p_f:
            ratio = dis_p_a / dis_p_f * 0.5
        mid_piv_free = piv.lerp(fre, ratio)
        arc_pts = [mid_piv_free]
        steps = 36
        ang_step = pi*2 / steps
        mid_align = mid_piv_free - piv
        for a in range(1, steps+1):
            rot_val = Quaternion(piv_norm, ang_step * a)
            temp = mid_align.copy()
            temp.rotate(rot_val)
            arc_pts.append(temp + piv)

    RotDat.arc_pts = arc_pts


# Takes a ref_pts (ReferencePoints class) argument and modifies its member
# variable lp_ls (lock pt list). The lp_ls variable is assigned a modified list
# of 3D coordinates (if an axis lock was provided), the contents of the
# ref_pts' rp_ls var (if no axis lock was provided), or an empty list (if there
# wasn't enough ref_pts or there was a problem creating the modified list).
# todo : move inside ReferencePoints class ?
def set_lock_pts(ref_pts, pt_cnt):
    if pt_cnt < 2:
        RotDat.lock_pts = []
    elif RotDat.axis_lock is None:
        RotDat.lock_pts = ref_pts
        if pt_cnt == 3:
            set_arc_pts(ref_pts)


# end_a, piv_pt, and end_b are Vector based 3D coordinates
# coordinates must share a common center "pivot" point (piv_pt)
def get_line_ang_3d(end_a, piv_pt, end_b):
    algn_a = end_a - piv_pt
    algn_b = end_b - piv_pt
    return algn_a.angle(algn_b)


# Checks if the 3 Vector coordinate arguments (end_a, piv_pt, end_b)
# will create an angle with a measurement matching the value in the
# argument exp_ang (expected angle measurement).
def ang_match3d(end_a, piv_pt, end_b, exp_ang):
    ang_meas = get_line_ang_3d(end_a, piv_pt, end_b)
    #print("end_a", end_a)  # debug
    #print("piv_pt", piv_pt)  # debug
    #print("end_b", end_b)  # debug
    #print("exp_ang ", exp_ang)  # debug
    #print("ang_meas ", ang_meas)  # debug
    return flts_alm_eq(ang_meas, exp_ang)


# Updates lock points and changes curr_meas_stor to use measure based on
# lock points instead of ref_pts (for axis constrained transformations).
def updatelock_pts(self, ref_pts):
    global curr_meas_stor
    set_lock_pts(ref_pts, self.pt_cnt)
    if RotDat.lock_pts == []:
        if RotDat.axis_lock is not None:
            self.report({'ERROR'}, 'Axis lock \''+ RotDat.axis_lock+
                    '\' creates identical points')
        RotDat.lock_pts = ref_pts
        RotDat.axis_lock = None


# See if key was pressed that would require updating the axis lock info.
# If one was, update the lock points to use new info.
def axis_key_check(self, new_axis):
    if self.pt_cnt == 1:
        if new_axis != RotDat.axis_lock:
            RotDat.axis_lock = new_axis


def draw_rot_arc(colr):
    reg = bpy.context.region
    rv3d = bpy.context.region_data
    len_arc_pts = len(RotDat.arc_pts)
    if len_arc_pts > 1:
        last = loc3d_to_reg2d(reg, rv3d, RotDat.arc_pts[0])
        for p in range(1, len_arc_pts):
            p2d = loc3d_to_reg2d(reg, rv3d, RotDat.arc_pts[p])
            draw_line_2d(last, p2d, Colr.white)
            last = p2d


# Called when add-on mode changes and every time point is added or removed.
def set_help_text(self, mode):
    text = ""
    if mode == "CLICK":
        if self.pt_cnt == 0:
            text = "ESC/LMB+RMB - exits add-on, LMB - add ref point"
        elif self.pt_cnt == 1:
            text = "ESC/LMB+RMB - exits add-on, LMB - add/remove ref points, X/Y/Z - set axis lock, C - clear axis lock, G - grab point, SHIFT+LMB enter mid point mode"
        elif self.pt_cnt == 2:
            text = "ESC/LMB+RMB - exits add-on, LMB - add/remove ref points, G - grab point, SHIFT+LMB enter mid point mode"
        else:  # self.pt_cnt == 3
            text = "ESC/LMB+RMB - exits add-on, LMB - remove ref points, G - grab point, SHIFT+LMB enter mid point mode"
    elif mode == "MULTI":
        text = "ESC/LMB+RMB - exits add-on, SHIFT+LMB exit mid point mode, LMB - add/remove point"
    elif mode == "GRAB":
        text = "ESC/LMB+RMB - exits add-on, G - cancel grab, LMB - place/swap ref points"
    elif mode == "POPUP":
        text = "ESC/LMB+RMB - exits add-on, LMB/RMB (outside pop-up) - cancel pop-up input"

    bpy.context.area.header_text_set(text)


# todo : move most of below to mouse_co update in modal?
def draw_callback_px(self, context):
    reg = bpy.context.region
    rv3d = bpy.context.region_data
    ptsz_lrg = 20
    ptsz_sml = 10

    add_rm_co = Vector((self.rtoolsw, 0))
    self.add_rm_btn.draw_btn(add_rm_co, self.mouse_co, self.shift_held)
    self.rotate_btn.is_drawn = False  # to-do : cleaner btn activation

    # allow appending None so indexing does not get messed up
    # causing potential false positive for overlap
    pts2d = [p.get_co2d() for p in self.pts]
    ms_colr = Colr.yellow
    if self.pt_cnt < 3:
        ms_colr = self.pts[self.pt_cnt].colr

    if self.grab_pt is not None:  # not enabled if mod_pt active
        line_beg = pts2d[self.grab_pt]  # backup orignal co for move line
        pts2d[self.grab_pt] = None  # prevent check on grabbed pt
        closest_pt, self.overlap_idx = closest_to_point(self.mouse_co, pts2d)
        pts2d[self.grab_pt] = self.mouse_co
        ms_colr = self.pts[self.grab_pt].colr
        if not self.shift_held:
            draw_line_2d(line_beg, self.mouse_co, self.pts[self.grab_pt].colr)
            draw_pt_2d(closest_pt, Colr.white, ptsz_lrg)

    elif self.mod_pt is not None:
        ms_colr = self.pts[self.mod_pt].colr
        m_pts2d = [loc3d_to_reg2d(reg, rv3d, p) for p in self.multi_tmp.ls]
        closest_pt, self.overlap_idx = closest_to_point(self.mouse_co, m_pts2d)
        draw_pt_2d(pts2d[self.mod_pt], Colr.white, ptsz_lrg)
        if self.shift_held:
            draw_pt_2d(self.mouse_co, Colr.black, ptsz_lrg)
            if len(m_pts2d) > 1:
                for mp in m_pts2d:
                    draw_pt_2d(mp, Colr.black, ptsz_lrg)
        else:
            draw_pt_2d(closest_pt, Colr.black, ptsz_lrg)
        if len(m_pts2d) > 1:
            for p in m_pts2d:
                draw_pt_2d(p, ms_colr, ptsz_sml)
        last_mod_pt = loc3d_to_reg2d(reg, rv3d, self.multi_tmp.ls[-1])
        draw_line_2d(last_mod_pt, self.mouse_co, self.pts[self.mod_pt].colr)

    else:  # "Normal" mode
        closest_pt, self.overlap_idx = closest_to_point(self.mouse_co, pts2d)
        if self.shift_held:
            draw_pt_2d(closest_pt, Colr.white, ptsz_lrg)
        else:
            draw_pt_2d(closest_pt, Colr.black, ptsz_lrg)

        rwid = context.region.width
        rhgt = context.region.height
        if self.pt_cnt == 1:
            if RotDat.axis_lock is not None:
                if self.running_transf is False:
                    self.rotate_btn.draw_btn(pts2d[0], self.mouse_co)
                    self.rotate_btn.is_drawn = True

                if RotDat.axis_lock == 'X':
                    test = self.pts[0].co3d + Vector((1, 0, 0))
                    colr = Colr.red
                if RotDat.axis_lock == 'Y':
                    test = self.pts[0].co3d + Vector((0, 1, 0))
                    colr = Colr.green
                if RotDat.axis_lock == 'Z':
                    test = self.pts[0].co3d + Vector((0, 0, 1))
                    colr = Colr.blue

                t2d = loc3d_to_reg2d(reg, rv3d, test)
                axis_pts = get_axis_line_co(pts2d[0], t2d, rwid, rhgt)
                if axis_pts is not None:
                    draw_line_2d(axis_pts[0], axis_pts[1], colr)

                dpi = bpy.context.preferences.system.dpi
                font_id, txt_sz = 0, 32
                x_pos, y_pos = self.rtoolsw + 80, 36
                bgl.glColor4f(*colr)
                blf.size(font_id, txt_sz, dpi)
                blf.position(font_id, x_pos, y_pos, 0)
                blf.draw(font_id, RotDat.axis_lock)

        elif self.pt_cnt == 2:
            axis_pts = get_axis_line_co(pts2d[0], pts2d[1], rwid, rhgt)
            #draw_line_2d(pts2d[0], pts2d[1], Colr.white)
            if axis_pts is not None:
                draw_line_2d(axis_pts[0], axis_pts[1], Colr.white)
                #draw_line_2d(pts2d[0], self.mouse_co, Colr.white)
                btn_co = pts2d[0].lerp(pts2d[1], 0.5)
                #self.meas_btn.draw_btn(btn_co, self.mouse_co)
                #self.meas_btn.active = True
                if not self.running_transf:
                    self.rotate_btn.draw_btn(btn_co, self.mouse_co)
                    self.rotate_btn.is_drawn = True
        elif self.pt_cnt == 3:
            test = self.pts[2].co3d + RotDat.piv_norm
            t2d = loc3d_to_reg2d(reg, rv3d, test)
            axis_pts = get_axis_line_co(pts2d[2], t2d, rwid, rhgt)
            if axis_pts is not None:
                draw_line_2d(axis_pts[0], axis_pts[1], Colr.white)
                
            #btn_co = pts2d[2] + Vector((0, 20))
            draw_line_2d(pts2d[0], pts2d[2], Colr.white)
            draw_line_2d(pts2d[1], pts2d[2], Colr.white)
            #self.meas_btn.draw_btn(pts2d[2], self.mouse_co)
            #self.meas_btn.active = True
            #draw_btn(self, btn_loc, mouse_co):
            if not self.running_transf:
                self.rotate_btn.draw_btn(pts2d[2], self.mouse_co)
                self.rotate_btn.is_drawn = True

    # todo : figure out reason for weirdness below
    cnt = 0
    for p in pts2d:
        draw_pt_2d(p, self.pts[cnt].colr, ptsz_sml)
        cnt += 1

    if self.highlight_mouse and not self.running_transf:
        draw_pt_2d(self.mouse_co, ms_colr, ptsz_sml)

    self.menu.draw(self.rotate_btn.is_drawn)


def exit_addon(self):
    restore_blender_settings(self.settings_backup)
    bpy.context.area.header_text_set()
    # todo : reset openGL settings?
    #bgl.glColor4f()
    #blf.size()
    #blf.position()
    #print("\n\nAdd-On Exited\n")  # debug


# Sees if "use_region_overlap" is enabled and X offset is needed.
def get_reg_overlap():
    rtoolsw = 0  # region tools (toolbar) width
    #ruiw = 0  # region ui (Number/n-panel) width
    system = bpy.context.preferences.system
    if system.use_region_overlap:
        area = bpy.context.area
        for r in area.regions:
            if r.type == 'TOOLS':
                rtoolsw = r.width
                #elif r.type == 'UI':
                #    ruiw = r.width
    #return rtoolsw, ruiw
    return rtoolsw


class XEditFreeRotate(bpy.types.Operator):
    bl_idname = "view3d.xedit_free_rotate_op"
    bl_label = "XEdit Free Rotate"

    # Only launch Add-On from OBJECT or EDIT modes
    @classmethod
    def poll(self, context):
        return context.mode == 'OBJECT' or context.mode == 'EDIT_MESH'

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'A', 'MIDDLEMOUSE', 'WHEELUPMOUSE',
        'WHEELDOWNMOUSE', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4',
        'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'NUMPAD_0', 'TAB'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))

        if event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            if event.value == 'PRESS':
                self.shift_held = True
                #print("\nShift pressed")  # debug
            elif event.value == 'RELEASE':
                self.shift_held = False
                #print("\nShift released")  # debug

        if event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                if self.lmb_held:
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    exit_addon(self)
                    return {'CANCELLED'}
            elif event.value == 'RELEASE':
                self.running_transf = False
                set_mouse_highlight(self)
                set_help_text(self, "CLICK")
            return {'PASS_THROUGH'}

        elif event.type == 'SPACE' and event.value == 'RELEASE':
            # Safely exit transform
            if self.running_transf:
                self.running_transf = False

        elif event.type in {'RET', 'LEFTMOUSE'} and event.value == 'PRESS':
            self.mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))
            if event.type == 'LEFTMOUSE':
                self.lmb_held = True
            #print("LEFTMOUSE PRESS")  # debug

        elif event.type in {'RET', 'LEFTMOUSE'} and event.value == 'RELEASE':
            # prevent click/enter that launched add-on from doing anything
            if self.first_run:
                self.first_run = False
                return {'RUNNING_MODAL'}
            if event.type == 'LEFTMOUSE':
                self.lmb_held = False
            #print("LeftMouse released")  # debug
            self.mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))

            #===========================
            # Safely exit transform
            #===========================
            if self.running_transf is True:
                self.running_transf = False

            #===================================
            # Check for click on Rotate Button
            #===================================
            elif self.rotate_btn.is_drawn is True and \
                    self.rotate_btn.ms_over is True:
                #print("Button Clicked")
                curs_loc = None
                #bpy.ops.object.ms_input_dialog_op('INVOKE_DEFAULT')
                if self.pt_cnt == 1:
                    if RotDat.axis_lock == 'X':
                        rot_axis = 1.0, 0.0, 0.0
                    elif RotDat.axis_lock == 'Y':
                        rot_axis = 0.0, 1.0, 0.0
                    elif RotDat.axis_lock == 'Z':
                        # -1 because it is assumed most rotations
                        # will have negative z pointing down
                        rot_axis = 0.0, 0.0, -1.0
                    curs_loc = self.pts[0].co3d.copy()
                elif self.pt_cnt == 2:
                    #if RotDat.axis_lock is None:
                    rot_vec = self.pts[1].co3d - self.pts[0].co3d
                    rot_axis = rot_vec.normalized()
                    curs_loc = self.pts[0].co3d.lerp(self.pts[1].co3d, 0.5)
                elif self.pt_cnt == 3:
                    #if RotDat.axis_lock is None:
                    rot_axis = RotDat.piv_norm
                    curs_loc = self.pts[2].co3d.copy()
                self.running_transf = True
                bpy.context.space_data.pivot_point = 'CURSOR'
                bpy.context.scene.cursor_location = curs_loc
                bpy.ops.transform.rotate('INVOKE_DEFAULT',axis=rot_axis)

            #===========================================
            # Check for click on "Add Selected" Button
            #===========================================
            elif self.add_rm_btn.ms_over:
                if self.mod_pt is not None:
                    if not self.shift_held:
                        add_select_multi(self)
                    else:
                        if self.pt_cnt < 3:
                            new_select_multi(self)
                            exit_multi_mode(self)
                            self.menu.change_menu(self.pt_cnt)
                elif self.grab_pt is not None:
                    co3d = None
                    if bpy.context.mode == "OBJECT":
                        if len(bpy.context.selected_objects) > 0:
                            if not self.shift_held:
                                co3d = bpy.context.selected_objects[0].location
                            else:
                                new_select_multi(self)
                                exit_multi_mode(self)
                                self.menu.change_menu(self.pt_cnt)
                    elif bpy.context.mode == "EDIT_MESH":
                        m_w = bpy.context.edit_object.matrix_world
                        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
                        if len(bm.select_history) > 0:
                            if not self.shift_held:
                                for sel in bm.select_history:
                                    if type(sel) is bmesh.types.BMVert:
                                        co3d = m_w * sel.co
                                        break
                                    elif type(sel) is bmesh.types.BMEdge or \
                                            type(sel) is bmesh.types.BMFace:
                                        co3d = Vector()
                                        for v in sel.verts:
                                            co3d += m_w * v.co
                                        co3d = co3d / len(sel.verts)
                                        break
                            else:
                                new_select_multi(self)
                                exit_multi_mode(self)
                                self.menu.change_menu(self.pt_cnt)

                    if co3d is not None:
                        if not in_ref_pts(self, co3d):
                            self.pts[self.grab_pt].co3d = co3d
                        else:
                            swap_ref_pts(self, self.grab_pt, self.swap_pt)
                            self.swap_pt = None
                    self.grab_pt = None
                    updatelock_pts(self, self.pts)
                    set_piv(self)
                else:  # no grab or mod point
                    if self.shift_held:
                        if self.pt_cnt < 3:
                            new_select_multi(self)
                            if in_ref_pts(self, self.multi_tmp.get_co(), self.mod_pt):
                                self.report({'WARNING'}, 'Points overlap.')
                            self.pts[self.mod_pt].co3d = self.multi_tmp.get_co()
                            self.menu.change_menu(self.pt_cnt)
                    else:
                        add_select(self)
                # todo : see if this is really a good solution...
                if self.mod_pt is None:
                    set_help_text(self, "CLICK")
                else:
                    set_help_text(self, "MULTI")

            #===========================
            # Point Place or Grab Mode
            #===========================
            elif self.mod_pt is None:
                if self.overlap_idx is None:  # no point overlap
                    if not self.shift_held:
                        if self.grab_pt is not None:
                            found_pt = find_closest_point(self.mouse_co)
                            if found_pt is not None:
                                if not in_ref_pts(self, found_pt):
                                    self.pts[self.grab_pt].co3d = found_pt
                            self.grab_pt = None
                            if self.pt_cnt > 1:
                                updatelock_pts(self, self.pts)
                            set_mouse_highlight(self)
                            set_piv(self)
                            set_help_text(self, "CLICK")
                        elif self.pt_cnt < 3:
                            found_pt = find_closest_point(self.mouse_co)
                            if found_pt is not None:
                                if not in_ref_pts(self, found_pt):
                                    self.pts[self.pt_cnt].co3d = found_pt
                                    self.pt_cnt += 1
                                    self.menu.change_menu(self.pt_cnt)
                                    if self.pt_cnt > 1:
                                        RotDat.axis_lock = None
                                        updatelock_pts(self, self.pts)
                                        set_piv(self)
                                        #if self.pt_cnt
                                    set_mouse_highlight(self)
                                    set_help_text(self, "CLICK")
                                    ''' Begin Debug
                                    cnt = self.pt_cnt - 1
                                    pt_fnd_str = str(self.pts[cnt].co3d)
                                    pt_fnd_str = pt_fnd_str.replace("<Vector ", "Vector(")
                                    pt_fnd_str = pt_fnd_str.replace(">", ")")
                                    print("ref_pt_" + str(cnt) + ' =', pt_fnd_str)
                                    #print("ref pt added:", self.cnt, "cnt:", self.cnt+1)
                                    End Debug '''
                else:  # overlap
                    if self.grab_pt is not None:
                        if not self.shift_held:
                            if self.grab_pt != self.overlap_idx:
                                swap_ref_pts(self, self.grab_pt, self.overlap_idx)
                            self.grab_pt = None
                            if self.pt_cnt > 1:
                                updatelock_pts(self, self.pts)
                            set_mouse_highlight(self)
                            set_piv(self)
                            set_help_text(self, "CLICK")

                    elif not self.shift_held:
                        # overlap and shift not held == remove point
                        rem_ref_pt(self, self.overlap_idx)
                        set_help_text(self, "CLICK")
                    else:  # shift_held
                        # enable multi point mode
                        self.mod_pt = self.overlap_idx
                        self.multi_tmp.reset(self.pts[self.mod_pt].co3d)
                        self.highlight_mouse = True
                        set_help_text(self, "MULTI")

            #===========================
            # Mod Ref Point Mode
            #===========================
            else:  # mod_pt exists
                if self.overlap_idx is None:  # no point overlap
                    if not self.shift_held:
                        # attempt to add new point to multi_tmp
                        found_pt = find_closest_point(self.mouse_co)
                        if found_pt is not None:
                            self.multi_tmp.try_add(found_pt)
                            mult_co3d = self.multi_tmp.get_co()
                            if in_ref_pts(self, mult_co3d, self.mod_pt):
                                self.report({'WARNING'}, 'Points overlap.')
                            self.pts[self.mod_pt].co3d = mult_co3d
                    else:  # shift_held, exit multi_tmp
                        exit_multi_mode(self)
                        set_piv(self)
                else:  # overlap multi_tmp
                    if not self.shift_held:
                        # remove multi_tmp point
                        self.multi_tmp.rem_pt(self.overlap_idx)
                        # if all multi_tmp points removed,
                        # exit multi mode, remove edited point
                        if self.multi_tmp.co3d is None:
                            rem_ref_pt(self, self.mod_pt)
                            self.mod_pt = None
                            set_help_text(self, "CLICK")
                        elif in_ref_pts(self, self.multi_tmp.co3d, self.mod_pt):
                            self.report({'WARNING'}, 'Points overlap.')
                            self.pts[self.mod_pt].co3d = self.multi_tmp.get_co()
                        else:
                            self.pts[self.mod_pt].co3d = self.multi_tmp.get_co()
                    else:  # shift_held
                        exit_multi_mode(self)

        if event.type == 'C' and event.value == 'PRESS':
            #print("Pressed C\n")  # debug
            axis_key_check(self, None)

        elif event.type == 'X' and event.value == 'PRESS':
            #print("Pressed X\n")  # debug
            axis_key_check(self, 'X')

        elif event.type == 'Y' and event.value == 'PRESS':
            #print("Pressed Y\n")  # debug
            axis_key_check(self, 'Y')

        elif event.type == 'Z' and event.value == 'PRESS':
            #print("Pressed Z\n")  # debug
            axis_key_check(self, 'Z')

            '''
            elif event.type == 'D' and event.value == 'RELEASE':
                # open debug console
                __import__('code').interact(local=dict(globals(), **locals()))
            '''

        elif event.type == 'G' and event.value == 'RELEASE':
            # if already in grab mode, cancel grab
            if self.grab_pt is not None:
                self.grab_pt = None
                set_mouse_highlight(self)
                set_help_text(self, "CLICK")
            # else enable grab mode (if possible)
            elif self.mod_pt is None:
                if self.overlap_idx is not None:
                    self.grab_pt = self.overlap_idx
                    self.highlight_mouse = False
                    set_help_text(self, "GRAB")

        elif event.type in {'ESC'} and event.value == 'RELEASE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            exit_addon(self)
            return {'CANCELLED'}

        if self.force_quit:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            exit_addon(self)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px,
                    args, 'WINDOW', 'POST_PIXEL')

            self.settings_backup = backup_blender_settings()
            self.mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))
            self.rtoolsw = get_reg_overlap()  # region tools (toolbar) width
            self.highlight_mouse = True  # draw ref point on mouse
            self.pts = []
            self.running_transf = False
            self.pt_cnt = 0
            self.lk_pts = []
            self.multi_tmp = TempPoint()
            self.rotate_btn = ViewButton(Colr.red, Colr.white, 18, Colr.white, (0.0, 20))
            self.rotate_btn.set_text("Rotate")
            self.add_rm_btn = ViewButton(Colr.red, Colr.white, 18, Colr.white, (190, 36))
            self.overlap_idx = None
            self.shift_held = False
            #self.debug_flag = False
            self.mod_pt = None
            self.first_run = event.type in {'RET', 'LEFTMOUSE'} and event.value != 'RELEASE'
            self.force_quit = False
            self.grab_pt = None
            self.new_free_co = ()
            self.swap_pt = None
            #self.addon_mode = CLICK_CHECK
            self.lmb_held = False

            self.menu = MenuHandler("Free Rotate", 18, Colr.yellow, Colr.white, \
                    self.rtoolsw, context.region)
            self.menu.add_menu(["Axis Lock Rotate"])
            self.menu.add_menu(["Axis Rotate"])
            self.menu.add_menu(["Planar Rotate"])

            context.window_manager.modal_handler_add(self)

            init_ref_pts(self)
            init_blender_settings()
            editmode_refresh()
            #print("Add-on started")  # debug
            self.add_rm_btn.set_text("Add Selected")
            set_help_text(self, "CLICK")

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
