"""
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

#============================================================================

mesh_xoffsets.py (alpha version 009 with experimental snap code)

#============================================================================

todo:
  [?] rewrite/refactor code to optimize for modal operation
  [?] make sure point removal state resets are correct (try_add)
  [X] fix: when btn clicked, dialog will not appear until after mouse moved
  [X] fix: when new meas input, transform not applied until after mouse moved
  [ ] prevent selection of non-visible vertices
  [ ] fix bug: obj is not subscriptable error if perspective is changed after
        launching addon, disabling perspective change for now
  [ ] better measurement input panel
  [ ] add hotkey reference info into 3D View ?
  [?] snap_point not deleted after exit
  [X] only free move during translate when in selected objects
  [X] snap toggle button still drawn when dialog opened (jumps to dialog box)
  [ ]

#============================================================================
"""

bl_info = {
    "name": "Exact Offsets",
    "author": "nBurn",
    "version": (0, 0, 9),
    "blender": (2, 7, 7),
    "location": "View3D",
    "description": "Tool for precisely setting distance, scale, and rotation of mesh geometry",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Mesh/Exact_Offsets",
    "category": "Mesh"
}

import bpy
import bgl
import blf
import bmesh
from copy import deepcopy
from math import fmod, sqrt, degrees, radians
from mathutils import Vector, geometry, Quaternion, Euler
from mathutils.geometry import intersect_line_line_2d
from bpy_extras import view3d_utils
from bpy_extras.view3d_utils import location_3d_to_region_2d

#print("Exact Offsets loaded")

# "constant" values
(
    CLICK_CHECK,
    CHECK_POPUP_INFO,
    GET_0_OR_180,
    DO_TRANSFORM,

    MOVE,
    SCALE,
    ROTATE,

    SLOW3DTO2D,
    GRABONLY
) = range(9)

curr_meas_stor = 0.0
new_meas_stor = None
popup_active = False
reg_rv3d = ()
pt_store = []
font_dpi = bpy.context.user_preferences.system.dpi


def get_reg_rv3d():
    global reg_rv3d
    region = bpy.context.region
    rv3d = []
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            rv3d = area.spaces[0].region_3d
            break
    reg_rv3d = (region, rv3d)


class Colr:
    red    = 1.0, 0.0, 0.0, 0.5
    green  = 0.0, 1.0, 0.0, 0.5
    blue   = 0.0, 0.0, 1.0, 0.5
    white  = 1.0, 1.0, 1.0, 0.5
    grey   = 1.0, 1.0, 1.0, 0.4
    white1 = 1.0, 1.0, 1.0, 1.0


# Class to stores selection info for scene and/or edited mesh
# Generates a list of mesh objects in the scene and lists of selected mesh
# and non-mesh objects and selected vertices (if in Edit Mode). These lists
# are used to speed up mesh object iteration and for restoring the selected
# objects after transforms.
class SceneSelectionInfo:
    def __init__(self):
        self.sel_nm_objs = []  # selected non-mesh objects
        self.msh_objs = []
        self.sel_msh_objs = []
        self.sel_msh_vts = []
        self.active_obj = None
        self.obj = bpy.context.scene.objects  # short hand, for internal use

    # Checks if there was changes to the selected objects or verts. It is
    # assumed no objects added or removed while the addon is running. This
    # should not be run while the snap point is active / existing.
    def update(self):
        tmp = []
        if bpy.context.mode == "OBJECT":
            if self.obj.active.type == 'MESH':
                self.active_obj = self.obj.active
            else:
                self.obj.active = self.obj[ self.msh_objs[0] ]
                self.active_obj = self.obj.active
            for i in self.msh_objs:
                if self.obj[i].select:
                    tmp.append(i)
            self.sel_msh_objs = tmp.copy()

        elif bpy.context.mode == "EDIT_MESH":
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            if hasattr(bm.verts, "ensure_lookup_table"):
                bm.verts.ensure_lookup_table()
            for ind in range(len(bm.verts)):
                if bm.verts[ind].select is True:
                    tmp.append(ind)
            self.sel_msh_vts = tmp.copy()

    def restore_selected(self):
        if bpy.context.mode == "OBJECT":
            bpy.ops.object.select_all(action='DESELECT')
            self.obj.active = self.active_obj
            for ind in self.sel_msh_objs:
                self.obj[ind].select = True
        elif bpy.context.mode == "EDIT_MESH":
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            if hasattr(bm.verts, "ensure_lookup_table"):
                bm.verts.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            for ind in self.sel_msh_vts:
                bm.verts[ind].select = True

    # for generating msh_objs and sel_nm_objs info when addon first run
    def start_run(self):
        for i in range(len(self.obj)):
            if self.obj[i].type == 'MESH':
                self.msh_objs.append(i)
            elif self.obj[i].select:
                self.sel_nm_objs.append(i)
        self.update()


def backup_snap_settings():
    backup = [
        deepcopy(bpy.context.tool_settings.use_snap),
        deepcopy(bpy.context.tool_settings.snap_element),
        deepcopy(bpy.context.tool_settings.snap_target),
        deepcopy(bpy.context.space_data.transform_orientation),
        deepcopy(bpy.context.space_data.show_manipulator)
    ]
    return backup


def init_snap_settings():
    bpy.context.tool_settings.use_snap = True
    bpy.context.tool_settings.snap_element = 'VERTEX'
    bpy.context.tool_settings.snap_target = 'ACTIVE'
    bpy.context.space_data.transform_orientation = 'GLOBAL'
    bpy.context.space_data.show_manipulator = False
    return


def restore_snap_settings(backup):
    bpy.context.tool_settings.use_snap = deepcopy(backup[0])
    bpy.context.tool_settings.snap_element = deepcopy(backup[1])
    bpy.context.tool_settings.snap_target = deepcopy(backup[2])
    bpy.context.space_data.transform_orientation = deepcopy(backup[3])
    bpy.context.space_data.show_manipulator = deepcopy(backup[4])
    return


# vertex storage class, stores reference point info
class VertObj:
    def __init__(self, obj_idx=-1, vert_idx=-1, co3d=(), co2d=()):
        self.obj_idx = obj_idx
        self.vert_idx = vert_idx
        self.co3d = co3d
        self.co2d = co2d
        self.obj = bpy.context.scene.objects  # short hand, for internal use

    # Have to use deepcopy for co's as tuples are the default init
    # value and tuples don't have a ".copy()" method.
    def copy(self):  # returns independent copy of VertObj
        return VertObj(self.obj_idx, self.vert_idx, deepcopy(self.co3d),
                deepcopy(self.co2d))

    def set2d(self):
        global reg_rv3d
        region, rv3d = reg_rv3d[0], reg_rv3d[1]
        self.co2d = location_3d_to_region_2d(region, rv3d, self.co3d)

    def update3d(self):
        tmp_co_local = self.obj[self.obj_idx].data.vertices[self.vert_idx].co
        self.co3d = self.obj[self.obj_idx].matrix_world * tmp_co_local


# Stores the reference points and ref pt related info.
class ReferencePoints:
    def __init__(self):
        self.cnt = 0  # count
        self.rp_ls = [(), (), ()]  # ref pt list
        self.lp_ls = [(), (), ()]  # lock pt list
        self.ax_lock = ''  # axis lock
        self.colr_ls = Colr.red, Colr.green

    def update_colr_ls(self):
        if self.cnt < 3:
            self.colr_ls = Colr.red, Colr.green
        else:  # self.cnt > 2
            self.colr_ls = Colr.red, Colr.blue, Colr.green

    def remove_pt(self, rem_idx):
        # hackery or smart, you decide...
        if rem_idx != self.cnt - 1:
            ind = [0, 1, 2][:self.cnt]
            ind.remove(rem_idx)
            for i in range(len(ind)):
                self.rp_ls[i] = self.rp_ls[ind[i]].copy()
                self.rp_ls[i].ref_idx = i
        self.cnt -= 1

    def try_add(self, found_pt):
        if self.cnt > 0:
            for rp in range(self.cnt):
                if self.rp_ls[rp].co3d == found_pt.co3d:
                    self.ax_lock = ''
                    self.remove_pt(self.rp_ls[rp].ref_idx)
                    self.lp_ls = self.rp_ls
                    self.update_colr_ls()
                    return
        # if duplicate not found and cnt not max, add found_pt to rp_ls
        if self.cnt < 3:
            self.rp_ls[self.cnt] = found_pt.copy()
            self.rp_ls[self.cnt].ref_idx = self.cnt
            self.cnt += 1
        self.update_colr_ls()
        return


# Stores rotation info for passing data from draw_callback_px to
# external functions. Not as bad as hiding arguments in passed
# variables, but still seems hackish...
class RotationData:
    def __init__(self):
        self.new_ang_r = 0.0
        self.new_ang_d = 0.0
        self.ang_diff_d = 0.0
        self.ang_diff_r = 0.0
        self.axis_lk = ''
        self.piv_norm = []  # pivot normal


# Floating point math fun! Since equality tests on floats are a crap shoot,
# instead check if floats are almost equal (is the first float within a
# certain tolerance amount of the second).
# Note, this function may fail in certain circumstances depending on the
# number of significant figures. If comparisons become problematic, you can
# try a different power of ten for the "tol" value (eg 0.01 or 0.00001)
# todo: replace this with Python 3.5's math.isclose() ?
# do recent versions of Blender support math.isclose()?
def flts_alm_eq(flt_a, flt_b):
    tol = 0.0001
    return flt_a > (flt_b - tol) and flt_a < (flt_b + tol)


# === Linear Equations ===

def get_midpoint(pt1, pt2):
    return pt1.lerp(pt2, 0.5)


def get_dist(pt1, pt2):
    return (pt1 - pt2).length


# For making sure rise over run doesn't get flipped.
def slope_check(pt1, pt2):
    cmp_ls = []
    for i in range(len(pt1)):
        cmp_ls.append(flts_alm_eq(pt1[i], pt2[i]) or pt1[i] > pt2[i])
    return cmp_ls


# Finds 3D location that shares same slope of line connecting Anchor and
# Free or that is on axis line going through Anchor.
def get_new_3d_co(self, lock, rp_ls, old_dis, new_dis):
    pt_anc, pt_fr = rp_ls[0].co3d, rp_ls[1].co3d
    if lock == '':
        if new_dis == 0:
            return pt_anc
        orig_slope = slope_check(pt_anc, pt_fr)
        scale = new_dis / old_dis
        pt_pos = pt_anc.lerp(pt_fr,  scale)
        pt_neg = pt_anc.lerp(pt_fr, -scale)
        pt_pos_slp = slope_check(pt_anc, pt_pos)
        pt_neg_slp = slope_check(pt_anc, pt_neg)
        if orig_slope == pt_pos_slp:
            if new_dis > 0:
                return pt_pos
            else:
                # for negative distances
                return pt_neg
        elif orig_slope == pt_neg_slp:
            if new_dis > 0:
                return pt_neg
            else:
                return pt_pos
        else:  # neither slope matches
            self.report({'ERROR'}, 'Slope mismatch. Cannot calculate new point.')
            return None
    elif lock == 'X':
        if pt_fr[0] > pt_anc[0]:
            return Vector([ pt_anc[0] + new_dis, pt_fr[1], pt_fr[2] ])
        else:
            return Vector([ pt_anc[0] - new_dis, pt_fr[1], pt_fr[2] ])
    elif lock == 'Y':
        if pt_fr[1] > pt_anc[1]:
            return Vector([ pt_fr[0], pt_anc[1] + new_dis, pt_fr[2] ])
        else:
            return Vector([ pt_fr[0], pt_anc[1] - new_dis, pt_fr[2] ])
    elif lock == 'Z':
        if pt_fr[2] > pt_anc[2]:
            return Vector([ pt_fr[0], pt_fr[1], pt_anc[2] + new_dis ])
        else:
            return Vector([ pt_fr[0], pt_fr[1], pt_anc[2] - new_dis ])
    else:  # neither slope matches
        self.report({'ERROR'}, "Slope mismatch. Can't calculate new point.")
        return None


# co1, co2, and co3 are Vector based 3D coordinates
# coordinates must share a common center "pivot" point (co2)
def get_line_ang_3d(co1, co2, co3):
    algn_co1 = co1 - co2
    algn_co3 = co3 - co2
    return algn_co1.angle(algn_co3)


# Checks if the 3 coordinates arguments (pt1, pt2, pt3) will create
# an angle with a measurement matching the value in the argument
# exp_ang (expected angle measurement).
def ang_match3d(pt1, pt2, pt3, exp_ang):
    ang_meas = get_line_ang_3d(pt1, pt2, pt3)
    return flts_alm_eq(ang_meas, exp_ang)


# Calculates rotation around axis or face normal at Pivot's location.
# Takes two 3D coordinate Vectors (piv_co and mov_co), rotation angle in
# radians (ang_diff_rad), and rotation data storage object (rot_dat).
# Aligns mov_co to world origin (0, 0, 0) and rotates aligned
# mov_co (mov_aligned) around axis stored in rot_dat. After rotation,
# removes world-origin alignment.
def get_rotated_pt(piv_co, ang_diff_rad, rot_dat, mov_co):
    axis_lk = rot_dat.axis_lk
    mov_aligned = mov_co - piv_co
    rot_val = []
    if   axis_lk == '':  # arbitrary axis / spherical rotations
        rot_val = Quaternion(rot_dat.piv_norm, ang_diff_rad)
    elif axis_lk == 'X':
        rot_val = Euler((ang_diff_rad, 0.0, 0.0), 'XYZ')
    elif axis_lk == 'Y':
        rot_val = Euler((0.0, ang_diff_rad, 0.0), 'XYZ')
    elif axis_lk == 'Z':
        rot_val = Euler((0.0, 0.0, ang_diff_rad), 'XYZ')
    mov_aligned.rotate(rot_val)
    return mov_aligned + piv_co


# Takes a ref_pts (ReferencePoints class) argument and modifies its member
# variable lp_ls (lock pt list). The lp_ls variable is assigned a modified list
# of 3D coordinates (if an axis lock was provided), the contents of the
# ref_pts' rp_ls var (if no axis lock was provided), or an empty list (if there
# wasn't enough ref_pts or there was a problem creating the modified list).
# todo : move inside ReferencePoints class ?
def set_lock_pts(ref_pts):
    if ref_pts.cnt < 2:
        ref_pts.lp_ls = []
    elif ref_pts.ax_lock == '':
        ref_pts.lp_ls = ref_pts.rp_ls
    else:
        ref_pts.lp_ls = []
        new0, new1 = VertObj(), VertObj()
        ptls = [ref_pts.rp_ls[i].co3d for i in range(ref_pts.cnt)]  # shorthand
        # finds 3D midpoint between 2 supplied coordinates
        # axis determines which coordinates are assigned midpoint values
        # if X, Anchor is [AncX, MidY, MidZ] and Free is [FreeX, MidY, MidZ]
        if ref_pts.cnt == 2:  # translate
            mid3d = get_midpoint(ptls[0], ptls[1])
            if ref_pts.ax_lock == 'X':
                new0.co3d = Vector([ ptls[0][0], mid3d[1], mid3d[2] ])
                new1.co3d = Vector([ ptls[1][0], mid3d[1], mid3d[2] ])
            elif ref_pts.ax_lock == 'Y':
                new0.co3d = Vector([ mid3d[0], ptls[0][1], mid3d[2] ])
                new1.co3d = Vector([ mid3d[0], ptls[1][1], mid3d[2] ])
            elif ref_pts.ax_lock == 'Z':
                new0.co3d = Vector([ mid3d[0], mid3d[1], ptls[0][2] ])
                new1.co3d = Vector([ mid3d[0], mid3d[1], ptls[1][2] ])
            if new0.co3d != new1.co3d:
                ref_pts.lp_ls = [new0, new1]

        # axis determines which of the Free's coordinates are assigned
        # to Anchor and Pivot coordinates eg:
        # if X, Anchor is [FreeX, AncY, AncZ] and Pivot is [FreeX, PivY, PivZ]
        elif ref_pts.cnt == 3:  # rotate
            mov_co = ref_pts.rp_ls[2].co3d.copy()
            if ref_pts.ax_lock == 'X':
                new0.co3d = Vector([ mov_co[0], ptls[0][1], ptls[0][2] ])
                new1.co3d = Vector([ mov_co[0], ptls[1][1], ptls[1][2] ])
            elif ref_pts.ax_lock == 'Y':
                new0.co3d = Vector([ ptls[0][0], mov_co[1], ptls[0][2] ])
                new1.co3d = Vector([ ptls[1][0], mov_co[1], ptls[1][2] ])
            elif ref_pts.ax_lock == 'Z':
                new0.co3d = Vector([ ptls[0][0], ptls[0][1], mov_co[2] ])
                new1.co3d = Vector([ ptls[1][0], ptls[1][1], mov_co[2] ])
            if new0.co3d != new1.co3d and \
            new0.co3d != mov_co and \
            new1.co3d != mov_co:
                new2 = VertObj(-1, -1, mov_co, ())
                ref_pts.lp_ls = [new0, new1, new2]

        if ref_pts.lp_ls != []:
            for itm in ref_pts.lp_ls: itm.set2d()


# Finds out whether positive rot_dat.new_ang_r or negative rot_dat.new_ang_r
# will result in the desired rotation angle.
def find_correct_rot(ref_pts, rot_dat):
    ang_diff_rad, new_ang_rad = rot_dat.ang_diff_r, rot_dat.new_ang_r
    piv_pt, move_pt = ref_pts.rp_ls[1].co3d, ref_pts.rp_ls[2].co3d
    t_co_pos = get_rotated_pt(piv_pt, ang_diff_rad, rot_dat, move_pt)
    t_co_neg = get_rotated_pt(piv_pt,-ang_diff_rad, rot_dat, move_pt)
    set_lock_pts(ref_pts)
    lock_pts = ref_pts.lp_ls
    # is below check needed? is lock_pts tested before find_correct_rot called?
    # will be needed for a selection move?
    if lock_pts == []:
        print("lock_pts == [] CHECK IS NEEDED!")
        ref_pts.ax_lock = ''
        return ()
    else:
        if ang_match3d(lock_pts[0].co3d, lock_pts[1].co3d, t_co_pos, new_ang_rad):
            return t_co_pos, ang_diff_rad
        else:
            return t_co_neg, -ang_diff_rad


# === Original point finding code ===


# Returns the closest vertex found to the supplied 2D location.
# Returns None if no vertex found.
def find_closest_vert(loc, mesh_idx_ls):
    global reg_rv3d
    region, rv3d = reg_rv3d[0], reg_rv3d[1]
    shortest_dist = 40  # minimum distance from loc
    closest = None
    for obj_idx in mesh_idx_ls:
        mesh_obj = bpy.context.scene.objects[obj_idx]
        if len(mesh_obj.data.vertices) > 0:
            for i, v in enumerate(mesh_obj.data.vertices):
                co3d = mesh_obj.matrix_world * v.co
                co2d = location_3d_to_region_2d(region, rv3d, co3d)
                dist2d = get_dist(loc, co2d)
                if dist2d < shortest_dist:
                    shortest_dist = dist2d
                    closest = VertObj(obj_idx, i, co3d, co2d)
    return closest


# === Experimental PointFind code ===

def inside_bound_box(obj_num, co):
    objs = bpy.context.scene.objects  # shorthand
    m_w = objs[obj_num].matrix_world
    bb = [m_w * Vector(v[:]) for v in objs[obj_num].bound_box]
    bbx = [x[0] for x in bb]
    bby = [y[1] for y in bb]
    bbz = [z[2] for z in bb]
    x_min, x_max = min(bbx), max(bbx)
    y_min, y_max = min(bby), max(bby)
    z_min, z_max = min(bbz), max(bbz)
    tol = 0.0001
    if co[0] < (x_min - tol) or co[0] > (x_max + tol): return False
    if co[1] < (y_min - tol) or co[1] > (y_max + tol): return False
    if co[2] < (z_min - tol) or co[2] > (z_max + tol): return False
    return True


# Returns the first vertex found at the supplied 3D location
# Returns None if no vertex found.
def find_snap_loc(loc, mesh_objs):
    global pt_store
    objs = bpy.context.scene.objects
    for i in mesh_objs:
        if inside_bound_box(i, loc):
            test_loc = objs[i].matrix_world.inverted() * loc
            v_idx = 0
            for v in objs[i].data.vertices:
                if flts_alm_eq( v.co[0], test_loc[0] ):
                    if flts_alm_eq( v.co[1], test_loc[1] ):
                        if flts_alm_eq( v.co[2], test_loc[2] ):
                            world_loc = objs[i].matrix_world * v.co
                            return VertObj(i, v_idx, world_loc)  # success!
                v_idx += 1
    # find_snap_loc failed to find loc match if it reaches here
    return None


def create_snap_pt(ms_loc, sel_backup):
    global reg_rv3d, pt_store
    sel_backup.update()
    region, rv3d = reg_rv3d[0], reg_rv3d[1]
    v_u = view3d_utils  # shorthand
    persp_md_fix = v_u.region_2d_to_vector_3d(region, rv3d, ms_loc) / 5
    enterloc = v_u.region_2d_to_origin_3d(region, rv3d, ms_loc) + persp_md_fix
    if bpy.context.mode == 'OBJECT':
        bpy.ops.object.add(type='MESH', location=enterloc)
        pt_store = bpy.context.object
    elif bpy.context.mode == 'EDIT_MESH':
        # Make sure transform.translate only grabs newly created vert. Only
        # need to do this in edit mode, object mode does this automatically.
        bpy.ops.mesh.select_all(action='DESELECT')
        inver_mw = bpy.context.edit_object.matrix_world.inverted()
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        bm.verts.new(inver_mw * enterloc)
        if hasattr(bm.verts, "ensure_lookup_table"):
            bm.verts.ensure_lookup_table()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
        bm.select_history.add(bm.verts[-1])
        bm.verts[-1].select = True
        pt_store = bm.select_history.active.co
    bpy.ops.transform.translate('INVOKE_DEFAULT')


# Makes sure only the "guide point" object or vert
# added with create_snap_pt is deleted.
def remove_snap_pt(sel_backup):
    if bpy.context.mode == 'OBJECT':
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects[0].select = True
        bpy.ops.object.delete()
    elif bpy.context.mode == 'EDIT_MESH':
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        bm.verts[-1].select = True
        editmode_refresh()
        bpy.ops.mesh.delete(type='VERT')
    sel_backup.restore_selected()


# === 3D View mouse location and button code ===
# Functions outside_loop() and point_inside_loop() for creating the measure
# change "button" in the 3D View taken from patmo141's Virtual Button script:
# https://blenderartists.org/forum/showthread.php?259085

def outside_loop(loop_coords):
    xs = [v[0] for v in loop_coords]
    ys = [v[1] for v in loop_coords]
    max_x = max(xs)
    max_y = max(ys)
    bound = (1.1 * max_x, 1.1 * max_y)
    return bound


def point_inside_loop(loop_coords, mous_loc):
    if loop_coords is None:
        return False
    else:
        num_verts = len(loop_coords)
        # vectorize our two item tuple
        out = Vector(outside_loop(loop_coords))
        vec_mous = Vector(mous_loc)
        intersections = 0
        for i in range(num_verts):
            a = Vector(loop_coords[i-1])
            b = Vector(loop_coords[i])
            if intersect_line_line_2d(vec_mous, out, a, b):
                intersections += 1
        inside = False
        if fmod(intersections, 2):
            inside = True
        return inside


# === OpenGL drawing functions ===


def draw_logo(text, pt_co):
    global font_dpi
    pt_color = [1.0, 1.0, 0.5, 0.6]  # pale yellow
    font_id = 0
    bgl.glColor4f(*pt_color)
    blf.position(font_id, pt_co[0], pt_co[1], 0)
    blf.size(font_id, 16, font_dpi)
    blf.draw(font_id, text)
    return


def get_btn_coor(origin, r_width, r_height, x_offset, y_offset):
    co_bl = (origin[0]-x_offset), (origin[1]-y_offset)
    co_tl = (origin[0]-x_offset), (origin[1]+r_height+y_offset)
    co_tr = (origin[0]+r_width+x_offset), (origin[1]+r_height+y_offset)
    co_br = (origin[0]+r_width+x_offset), (origin[1]-y_offset)
    return [co_bl, co_tl, co_tr, co_br]


def draw_font_at_pt(text, pt_co, pt_color):
    if pt_co is not None:
        global font_dpi
        font_id = 0
        bgl.glColor4f(*pt_color)
        blf.position(font_id, pt_co[0], pt_co[1], 0)
        blf.size(font_id, 32, font_dpi)
        blf.draw(font_id, text)
    return


def draw_font_at_pt2(text, pt_co, pt_size, pt_color):
    if pt_co is not None:
        global font_dpi
        font_id = 0
        bgl.glColor4f(*pt_color)
        blf.position(font_id, pt_co[0], pt_co[1], 0)
        blf.size(font_id, pt_size, font_dpi)
        blf.draw(font_id, text)
    return


def draw_pt_2d(pt_co, pt_color, sz=8):
    if pt_co is not None:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glPointSize(sz)
        bgl.glColor4f(*pt_color)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex2f(*pt_co)
        bgl.glEnd()
    return


def draw_line_2d(pt_co_1, pt_co_2, pt_color):
    if pt_co_1 is not None and pt_co_2 is not None:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glPointSize(7)
        bgl.glColor4f(*pt_color)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(*pt_co_1)
        bgl.glVertex2f(*pt_co_2)
        bgl.glEnd()
    return


def draw_box(box_co, color):
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for coord in box_co:
        bgl.glVertex2f(coord[0], coord[1])
    bgl.glVertex2f(box_co[0][0], box_co[0][1])
    bgl.glEnd()
    return


# Draw measure button
def draw_meas_btn(text, co2d, mouse_co, color_off, color_on):
    btn_co = None
    if co2d is not None:
        global font_dpi
        color = color_off
        offset = 5
        font_id = 0
        blf.size(font_id, 24, font_dpi)
        w, h = blf.dimensions(font_id, text)
        text_co = (co2d[0] - w / 2, (co2d[1] + 5 * offset))
        btn_co = get_btn_coor(text_co, w, h, offset, offset)

        bgl.glColor4f(*color)
        blf.position(font_id, text_co[0], text_co[1], 0.0)
        blf.draw(font_id, text)
        if point_inside_loop(btn_co, mouse_co):
            color = color_on

        draw_box(btn_co, color)
    return btn_co


# Draw snap toggle button
def draw_st_btn(text, co2d, mouse_co, color_off, color_on):
    # snap toggle button has fixed position so co2d==None check not needed
    global font_dpi
    color = color_off
    offset = 5
    font_id = 0
    blf.size(font_id, 18, font_dpi)
    w, h = blf.dimensions(font_id, text)
    text_co = (co2d[0] - w / 2, (co2d[1]))
    btn_co = get_btn_coor(text_co, w, h, offset, offset)

    bgl.glColor4f(*color)
    blf.position(font_id, text_co[0], text_co[1] + 4, 0.0)
    blf.draw(font_id, text)
    if point_inside_loop(btn_co, mouse_co):
        color = color_on

    draw_box(btn_co, color)
    return btn_co


# Draw User Interface
def draw_ui(self):
    if self.ref_pts.cnt > 0:
        global curr_meas_stor
        ref_pts, meas_btn_act = self.ref_pts, self.meas_btn_act
        if ref_pts.cnt == 1:
            ref_pts.rp_ls[0].set2d()
            draw_pt_2d(ref_pts.rp_ls[0].co2d, ref_pts.colr_ls[0])
        else:
            last_pt = []
            if ref_pts.ax_lock == '':
                for i in range(ref_pts.cnt):
                    ref_pts.rp_ls[i].set2d()
                    draw_pt_2d(ref_pts.rp_ls[i].co2d, ref_pts.colr_ls[i])
                    if last_pt != []:
                        draw_line_2d(last_pt, ref_pts.rp_ls[i].co2d, Colr.white)
                    last_pt = ref_pts.rp_ls[i].co2d
            else:
                x_pos = self.rtoolsw + 80
                if   ref_pts.ax_lock == 'X':
                    draw_font_at_pt(ref_pts.ax_lock, [x_pos, 36], Colr.red)
                elif ref_pts.ax_lock == 'Y':
                    draw_font_at_pt(ref_pts.ax_lock, [x_pos, 36], Colr.green)
                elif ref_pts.ax_lock == 'Z':
                    draw_font_at_pt(ref_pts.ax_lock, [x_pos, 36], Colr.blue)
                for i in range(ref_pts.cnt):
                    ref_pts.rp_ls[i].set2d()
                    draw_pt_2d(ref_pts.rp_ls[i].co2d, ref_pts.colr_ls[i])
                    ref_pts.lp_ls[i].set2d()
                    draw_pt_2d(ref_pts.lp_ls[i].co2d, ref_pts.colr_ls[i])
                    if last_pt != []:
                        draw_line_2d(last_pt, ref_pts.lp_ls[i].co2d, Colr.white)
                    last_pt = ref_pts.lp_ls[i].co2d
            if meas_btn_act:
                mbtn_co = []  # measure button coordinates (location)
                if ref_pts.cnt < 3:
                    mbtn_co = VertObj(-1, -1, get_midpoint(
                            ref_pts.rp_ls[0].co3d, ref_pts.rp_ls[1].co3d))
                else:
                    mbtn_co = VertObj( -1, -1, ref_pts.rp_ls[1].co3d.copy() )
                mbtn_co.set2d()
                meas_str = format(curr_meas_stor, '.2f')
                self.meas_btn_co = draw_meas_btn(meas_str, mbtn_co.co2d,
                            self.mouse_co, Colr.white1, Colr.red)

    if self.snap_btn_act:
        sbtn_co = self.rtoolsw + 200, 12
        sbtn_str = "Snap: off"
        if self.pt_find_md == GRABONLY:
            sbtn_str = "Snap: on"
        self.snap_btn_co = draw_st_btn(sbtn_str, sbtn_co, self.mouse_co,
                    Colr.white1, Colr.red)


# Refreshes mesh drawing in 3D view and updates mesh coordinate
# data so ref_pts are drawn at correct locations.
# Using editmode_toggle to do this seems hackish, but editmode_toggle seems
# to be the only thing that updates both drawing and coordinate info.
def editmode_refresh():
    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()


# Takes  new_co (Vector) and free_obj (VertObj) as arguments. Calculates
# difference between the 3D locations in new_co and free_obj to determine
# the translation to apply to the selected geometry.
def do_translation(new_co, free_obj):
    objs = bpy.context.scene.objects  # shorthand
    if bpy.context.mode == "OBJECT":
        co_chg = -(free_obj.co3d - new_co)  # co_chg = coordinate change
        bpy.ops.transform.translate(value=(co_chg[0], co_chg[1], co_chg[2]))
    elif bpy.context.mode == "EDIT_MESH":
        t_loc = objs[free_obj.obj_idx].data.vertices[free_obj.vert_idx].co
        old_co = bpy.context.edit_object.matrix_world * t_loc
        co_chg = -(old_co - new_co)
        bpy.ops.transform.translate(value=(co_chg[0], co_chg[1], co_chg[2]))


# Performs a scale transformation using the provided s_fac (scale factor)
# argument. The scale factor is the result from dividing the user input
# measure (new_meas_stor) by the distance between the Anchor and Free
# (curr_meas_stor). After the object is scaled, it is then translated so the
# Anchor point returns to its "pre-scaled" location.
# takes:  ref_pts (ReferencePoints), s_fac (float)
def do_scale(ref_pts, s_fac):
    # back up settings before changing them
    piv_back = deepcopy(bpy.context.space_data.pivot_point)
    curs_back = bpy.context.scene.cursor_location.copy()
    bpy.context.space_data.pivot_point = 'CURSOR'
    bpy.context.scene.cursor_location = ref_pts.rp_ls[0].co3d.copy()
    ax_multip, cnstrt_bls = (), ()
    if   ref_pts.ax_lock ==  '':
        ax_multip, cnstrt_bls = (s_fac, s_fac, s_fac), (True, True, True)
    elif ref_pts.ax_lock == 'X':
        ax_multip, cnstrt_bls = (s_fac, 1, 1), (True, False, False)
    elif ref_pts.ax_lock == 'Y':
        ax_multip, cnstrt_bls = (1, s_fac, 1), (False, True, False)
    elif ref_pts.ax_lock == 'Z':
        ax_multip, cnstrt_bls = (1, 1, s_fac), (False, False, True)
    bpy.ops.transform.resize(value=ax_multip, constraint_axis=cnstrt_bls)
    # restore settings back to their pre "do_scale" state
    bpy.context.scene.cursor_location = curs_back.copy()
    bpy.context.space_data.pivot_point = deepcopy(piv_back)


# Takes 2D Pivot Point (piv) for piv to temp lines, 2 possible rotation
# coordinates to choose between (r_p_co, r_n_co), 2 rotation angles used to
# obtain the coordinates (r_p_ang_r, r_n_ang_r), and 2D mouse location (mouse_co)
# for determining which rotation coordinate is closest to the cursor.
# Returns the rotation coordinate closest to the 2d mouse position.
# r_p_co == rotation Positive coordinate,  r_n_co == rot Negative coor
# todo : make r_p_co2d and r_n_co2d VertObj types ?
def choose_0_or_180(piv, r_p_co, r_p_ang_r, r_n_co, r_n_ang_r, mouse_co):
    global reg_rv3d
    region, rv3d = reg_rv3d[0], reg_rv3d[1]
    r_p_co2d = location_3d_to_region_2d(region, rv3d, r_p_co)
    r_n_co2d = location_3d_to_region_2d(region, rv3d, r_n_co)
    piv2d = location_3d_to_region_2d(region, rv3d, piv.co3d)
    ms_co_1_dis = get_dist(r_p_co2d, mouse_co)
    ms_co_2_dis = get_dist(r_n_co2d, mouse_co)
    # draw both buttons and show which is closer to mouse
    if   ms_co_1_dis < ms_co_2_dis:
        draw_line_2d(piv2d, r_p_co2d, Colr.green)
        draw_pt_2d(r_p_co2d, Colr.green, 14)
        draw_pt_2d(r_n_co2d, Colr.grey)
        return r_p_co, r_p_ang_r
    elif ms_co_2_dis < ms_co_1_dis:
        draw_line_2d(piv2d, r_n_co2d, Colr.green)
        draw_pt_2d(r_n_co2d, Colr.green, 14)
        draw_pt_2d(r_p_co2d, Colr.grey)
        return r_n_co, r_n_ang_r
    else:
        draw_pt_2d(r_p_co2d, Colr.grey)
        draw_pt_2d(r_n_co2d, Colr.grey)
    return None, None


# Reduces the provided rotation amount (new_ms_stor) to an "equivalent" value
# less than or equal to 180 degrees. Calculates the angle offset from
# curr_ms_stor to achieve a new_ms_stor value. Finally, copies axis lock info
# from ref_pts to r_dat.
def prep_rotation_info(ref_pts, r_dat, curr_ms_stor, new_ms_stor):
    # workaround for negative angles and angles over 360 degrees
    if new_ms_stor < 0 or new_ms_stor > 360:
        new_ms_stor = new_ms_stor % 360
    r_dat.ang_diff_d = new_ms_stor - curr_ms_stor
    # fix for angles over 180 degrees
    if new_ms_stor > 180:
        r_dat.new_ang_r = radians(180 - (new_ms_stor % 180))
    else:
        r_dat.new_ang_r = radians(new_ms_stor)
    r_dat.ang_diff_r = radians(r_dat.ang_diff_d)
    r_dat.axis_lk = ref_pts.ax_lock


# Takes: ref_pts (ReferencePoints) and r_dat (RotationData) as args.
# Uses r_dat to obtain the rotation value and then rotates the
# selected objects or selected vertices using the provided values.
def do_rotate(ref_pts, r_dat):
    # back up settings before changing them
    piv_back = deepcopy(bpy.context.space_data.pivot_point)
    curs_back = bpy.context.scene.cursor_location.copy()
    bpy.context.space_data.pivot_point = 'CURSOR'
    bpy.context.scene.cursor_location = ref_pts.rp_ls[1].co3d.copy()

    axis_lock = ref_pts.ax_lock
    op_ax_lock = ()
    if   axis_lock == 'X': op_ax_lock = 1, 0, 0
    elif axis_lock == 'Y': op_ax_lock = 0, 1, 0
    elif axis_lock == 'Z': op_ax_lock = 0, 0, 1
    elif axis_lock ==  '': op_ax_lock = r_dat.piv_norm

    if bpy.context.mode == "OBJECT":
        bpy.ops.transform.rotate(value=r_dat.ang_diff_r, axis=op_ax_lock,
                constraint_axis=(False, False, False))

    elif bpy.context.mode == "EDIT_MESH":
        bpy.ops.transform.rotate(value=r_dat.ang_diff_r, axis=op_ax_lock,
                constraint_axis=(False, False, False))
        editmode_refresh()

    # restore settings back to their pre "do_rotate" state
    bpy.context.scene.cursor_location = curs_back.copy()
    bpy.context.space_data.pivot_point = deepcopy(piv_back)


# == pop-up dialog code ==
# todo: update with newer menu code if it can ever be made to work
class ChangeInputPanel(bpy.types.Operator):
    bl_idname = "object.ms_input_dialog_op"
    bl_label = "Measurement Input Panel"
    bl_options = {'INTERNAL'}

    float_new_meas = bpy.props.FloatProperty(name="Measurement")

    def execute(self, context):
        global popup_active, new_meas_stor
        new_meas_stor = self.float_new_meas
        popup_active = False
        return {'FINISHED'}

    def invoke(self, context, event):
        global curr_meas_stor
        self.float_new_meas = curr_meas_stor
        return context.window_manager.invoke_props_dialog(self)

    def cancel(self, context):  # testing
        global popup_active
        popup_active = False

class DialogPanel(bpy.types.Panel):
    def draw(self, context):
        self.layout.operator("object.ms_input_dialog_op")


# Updates lock points and changes curr_meas_stor to use measure based on
# lock points instead of ref_pts (for axis constrained transformations).
def updatelock_pts(self, ref_pts):
    global curr_meas_stor
    set_lock_pts(ref_pts)
    if ref_pts.lp_ls == []:
        self.report({'ERROR'}, ref_pts.ax_lock+' axis lock creates identical points')
        ref_pts.lp_ls = ref_pts.rp_ls
        ref_pts.ax_lock = ''
    # update Measurement in curr_meas_stor
    lk_pts = ref_pts.lp_ls
    if ref_pts.cnt < 2:
        curr_meas_stor = 0.0
    elif ref_pts.cnt == 2:
        curr_meas_stor = get_dist(lk_pts[0].co3d, lk_pts[1].co3d)
    elif ref_pts.cnt == 3:
        line_ang_r = get_line_ang_3d(lk_pts[0].co3d, lk_pts[1].co3d, lk_pts[2].co3d)
        curr_meas_stor = degrees(line_ang_r)


# See if key was pressed that would require updating the axis lock info.
# If one was, update the lock points to use new info.
def axis_key_check(self, new_axis):
    if self.ref_pts.cnt < 2:
        return
    else:
        if new_axis != self.ref_pts.ax_lock:
            self.ref_pts.ax_lock = new_axis
            updatelock_pts(self, self.ref_pts)


# Adjusts settings so proc_click can run again for next possible transform
def reset_settings(self):
    global new_meas_stor
    new_meas_stor = None
    self.mouse_co = Vector((-9900, -9900))
    editmode_refresh()
    for ob in range(self.ref_pts.cnt):
        self.ref_pts.rp_ls[ob].update3d()
        self.ref_pts.rp_ls[ob].set2d()
    if self.ref_pts.cnt < 2:
        self.meas_btn_act = False
    else:
        updatelock_pts(self, self.ref_pts)
        self.meas_btn_act = True
    self.snap_btn_act = True
    self.addon_mode = CLICK_CHECK
    set_lock_pts(self.ref_pts)

    # restore selected items (except Anchor)
    # needed so GRABONLY and SLOW3DTO2D update selection correctly
    self.sel_backup.restore_selected()

    # make sure last transform didn't cause points to overlap
    pt1 = self.ref_pts.rp_ls[0].co3d
    pt2 = self.ref_pts.rp_ls[self.ref_pts.cnt - 1].co3d
    if flts_alm_eq(pt1[0], pt2[0]):
        if flts_alm_eq(pt1[1], pt2[1]):
            if flts_alm_eq(pt1[2], pt2[2]):
                self.report({'ERROR'}, 'Free and Anchor share same location.')
                self.ref_pts = ReferencePoints()  # reset ref pt data

    if self.pt_find_md == GRABONLY:
        create_snap_pt(self.left_click_co, self.sel_backup)


# Can a transformation be performed? Called after measure button is clicked
# to let user know if valid options are set before enabling pop-up to get
# user input.
def can_transf(self):
    global curr_meas_stor
    success = False
    objs = bpy.context.scene.objects
    if self.ref_pts.cnt == 2:
        # activate scale mode if Anchor and Free attached to same object
        self.transf_type = MOVE
        if bpy.context.mode == "OBJECT":
            if self.ref_pts.rp_ls[0].obj_idx == self.ref_pts.rp_ls[1].obj_idx:
                self.transf_type = SCALE
            success = True
        elif bpy.context.mode == "EDIT_MESH" and \
        objs[self.ref_pts.rp_ls[1].obj_idx].mode != 'EDIT':
            self.report({'ERROR'}, 'Free must be in active mesh in Edit Mode.')
        else:
            success = True
    elif self.ref_pts.cnt == 3:
        self.transf_type = ROTATE
        if bpy.context.mode == "OBJECT" and \
        self.ref_pts.rp_ls[0].obj_idx == self.ref_pts.rp_ls[2].obj_idx:
            self.report({'ERROR'}, "Free & Anchor can't be on same object for rotations.")
        elif bpy.context.mode == "EDIT_MESH" and \
        objs[self.ref_pts.rp_ls[2].obj_idx].mode != 'EDIT':
            self.report({'ERROR'}, "Free must be in active mesh in Edit Mode.")
        elif self.ref_pts.ax_lock != '':
            success = True
        # if not flat angle and no axis lock set, begin preparations for
        # arbitrary axis / spherical rotation
        elif flts_alm_eq(curr_meas_stor, 0.0) is False and \
        flts_alm_eq(curr_meas_stor, 180.0) is False:
            anc_co = self.ref_pts.rp_ls[0].co3d
            piv_co = self.ref_pts.rp_ls[1].co3d
            fre_co = self.ref_pts.rp_ls[2].co3d
            self.r_dat.piv_norm = geometry.normal(anc_co, piv_co, fre_co)
            success = True
        else:
            # would need complex angle processing workaround to get
            # spherical rotations working with flat angles. todo item?
            # blocking execution for now.
            self.report({'INFO'}, "Need axis lock for 0 and 180 degree angles.")
    return success


# Handles left mouse clicks. Sets and removes reference points, activates
# the pop-up dialog (ChangeInputPanel) if the "meas button" is clicked,
# changes pt_find_md if "snap button" is clicked, and confirms the
# angle offset for 0 or 180 degree rotations.
def proc_click(self):
    # if angle offset from flat angle (0 or 180 degrees) was chosen
    if self.addon_mode == GET_0_OR_180:
        self.new_free_co, self.r_dat.ang_diff_r = choose_0_or_180(
                self.ref_pts.rp_ls[1], *self.modal_buff, self.mouse_co)
        self.addon_mode = DO_TRANSFORM
        do_transform(self)

    # if measure button was clicked
    elif self.meas_btn_act and point_inside_loop(self.meas_btn_co, self.left_click_co):
        global popup_active
        if self.pt_find_md == GRABONLY:
            remove_snap_pt(self.sel_backup)
        if can_transf(self):
            # refresh the viewport and update the selection list just in
            # case we are coming here from an earlier reset_settings call
            # and the selection was changed after that
            editmode_refresh()
            if self.pt_find_md == SLOW3DTO2D:
                self.sel_backup.update()
            # operation will continue on in background
            # after "ms_input_dialog_op" is called
            # need to have popup loop running and waiting for input
            self.meas_btn_act = False
            self.snap_btn_act = False
            popup_active = True
            self.addon_mode = CHECK_POPUP_INFO
            bpy.ops.object.ms_input_dialog_op('INVOKE_DEFAULT')
        else:
            reset_settings(self)

    # if snap toggle button was clicked
    elif self.snap_btn_act and point_inside_loop(self.snap_btn_co, self.left_click_co):
        if self.pt_find_md == SLOW3DTO2D:
            self.pt_find_md = GRABONLY
            create_snap_pt(self.left_click_co, self.sel_backup)
        else:
            remove_snap_pt(self.sel_backup)
            self.pt_find_md = SLOW3DTO2D

    # if no buttons were clicked, check to see if a reference point
    # was added or removed
    # prevent execution in the event we're coming here from a cancelled
    # pop-up request so a non-existant snap point isn't deleted
    # todo : find nicer way to prevent bugs with snap point removal?
    elif self.addon_mode != CHECK_POPUP_INFO:
        found_pt = None
        if self.pt_find_md == GRABONLY:
            t_loc = None
            if bpy.context.mode == 'OBJECT':
                t_loc = pt_store.location.copy()
            elif bpy.context.mode == 'EDIT_MESH':
                t_loc = bpy.context.edit_object.matrix_world * pt_store
            remove_snap_pt(self.sel_backup)
            found_pt = find_snap_loc(t_loc, self.sel_backup.msh_objs)
            create_snap_pt(self.left_click_co, self.sel_backup)
        else:
            found_pt = find_closest_vert(self.mouse_co, self.sel_backup.msh_objs)
        if found_pt is not None:
            self.ref_pts.try_add(found_pt)
            set_lock_pts(self.ref_pts)
            if self.ref_pts.cnt < 2:
                self.meas_btn_act = False
            else:
                updatelock_pts(self, self.ref_pts)
                self.meas_btn_act = True


# Generates a list of which selected mesh objects or selected vertices will
# remain selected based on the editor type, the transform mode, and whether
# the Free was part of the selected geometry. Mesh objects or vertices are
# then selected or unselected to match the contents of the generated list.
def prepare_selected(sel_backup, ref_pts, transf_type):
    objs = bpy.context.scene.objects  # shorthand
    anch = ref_pts.rp_ls[0]
    free = ref_pts.rp_ls[ref_pts.cnt - 1]
    free_in_sel = False
    selected_ls = None

    if bpy.context.mode == "OBJECT":
        selected_ls = sel_backup.sel_msh_objs.copy()
        free_idx = free.obj_idx
        # If Scale Mode, auto-fail free_in_sel as Scale only runs on Free Obj
        if transf_type == SCALE:
            free_in_sel = False
        else:
            # See if Free's Obj was selected
            if objs[anch.obj_idx].select:
                selected_ls.remove(anch.obj_idx)
            if objs[free_idx].select:
                free_in_sel = True
        # Unselect everything in case a non-mesh obj was selected
        bpy.ops.object.select_all(action='DESELECT')
        if free_in_sel is False:
            selected_ls = [free_idx]
        # Reselect just the mesh objects contained in selectedLs
        for ind in selected_ls:
            objs[ind].select = True

    elif bpy.context.mode == "EDIT_MESH":
        selected_ls = sel_backup.sel_msh_vts.copy()
        free_idx = free.vert_idx
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        if hasattr(bm.verts, "ensure_lookup_table"):
            bm.verts.ensure_lookup_table()
        # The 'EDIT' mode check below is not needed as this was
        # already verified in can_transf()
        #if objs[free.obj_idx].mode == 'EDIT':
        if bm.verts[free_idx].select:
            free_in_sel = True
            # Make sure the anchor isn't selected. If it is, "unselect" it.
            # Note that it's not possible to just unselect a single vert
            # without also unselecting ALL edges and faces that vert was
            # a part of. As there does not seem to be any simple method to
            # find and unselect those edges and faces, instead unselect
            # everything and then reselect all the verts that were
            # originally selected, one-by-one, except the the vert that is
            # being "unselected".
            if objs[anch.obj_idx].mode == 'EDIT':
                if bm.verts[anch.vert_idx].select:
                    selected_ls.remove(anch.vert_idx)
                    if free_in_sel is True:
                        bpy.ops.mesh.select_all(action='DESELECT')
                        for ind in selected_ls:
                            bm.verts[ind].select = True
        # If the Free is not selected the transform will be on the Free only.
        # Unselect everything else and make so only the Free is selected.
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts[free_idx].select = True
        editmode_refresh()


# runs transformation functions depending on which options are set.
# transform functions cannot be called directly due to use of pop-up for
# getting user input
def do_transform(self):
    global curr_meas_stor, new_meas_stor
    rp_ls, ax_lock = self.ref_pts.rp_ls, self.ref_pts.ax_lock

    # Onto Transformations...

    if self.transf_type == MOVE:
        new_coor = get_new_3d_co(self, ax_lock, rp_ls, curr_meas_stor, new_meas_stor)
        if new_coor is not None:
            do_translation(new_coor, rp_ls[1])
        reset_settings(self)

    elif self.transf_type == SCALE:
        scale_factor = new_meas_stor / curr_meas_stor
        do_scale(self.ref_pts, scale_factor)
        reset_settings(self)

    elif self.transf_type == ROTATE:
        if self.new_free_co != ():
            do_rotate(self.ref_pts, self.r_dat)
        reset_settings(self)


# Waits for ChangeInputPanel pop-up to disable popup_active, then checks if
# a valid number was input, and finally determines what to do based on what
# was input into pop-up (if anything).
def check_popup_input(self):
    global popup_active, curr_meas_stor, new_meas_stor
    if popup_active is False:
        if new_meas_stor is not None:
            if self.transf_type == SCALE and new_meas_stor < 0:
                self.report({'ERROR'}, 'Scale input cannot be negative.')
                reset_settings(self)
            else:
                prepare_selected(self.sel_backup, self.ref_pts, self.transf_type)
                self.addon_mode = DO_TRANSFORM
                if self.transf_type == ROTATE:
                    prep_rotation_info(self.ref_pts, self.r_dat, curr_meas_stor, new_meas_stor)
                    # if angle is 0 or 180, setup angle chooser
                    if flts_alm_eq(curr_meas_stor, 0.0) or flts_alm_eq(curr_meas_stor, 180.0):
                        rot_dat, ang_diff_rad = self.r_dat, self.r_dat.ang_diff_r
                        piv, mov = self.ref_pts.rp_ls[1].co3d, self.ref_pts.rp_ls[2].co3d
                        t_co_pos = get_rotated_pt(piv, ang_diff_rad, rot_dat, mov)
                        t_co_neg = get_rotated_pt(piv, -ang_diff_rad, rot_dat, mov)
                        self.modal_buff = (t_co_pos, ang_diff_rad, t_co_neg, -ang_diff_rad)
                        self.addon_mode = GET_0_OR_180
                    else:
                        self.new_free_co, self.r_dat.ang_diff_r = \
                                find_correct_rot(self.ref_pts, self.r_dat)
                        do_transform(self)
                else:  # transf_type == MOVE
                    do_transform(self)
        else:
            reset_settings(self)


# Deletes snap point (if it exists), restores selected objects / verts,
# and restores Blender to previous settings before add-on was launched.
def exit_addon(self):
    if self.pt_find_md == GRABONLY:
        remove_snap_pt(self.sel_backup)
        self.pt_find_md = SLOW3DTO2D
        if bpy.context.mode == 'EDIT_MESH':
            for i in self.sel_backup.sel_msh_objs:
                self.sel_backup.obj[i].select = True
    for i in self.sel_backup.sel_nm_objs:
        self.sel_backup.obj[i].select = True
    restore_snap_settings(self.settings_backup)
    #print("\n\n\n  Add-On Exited!\n")  # debug


# Sees if "use_region_overlap" is enabled and X offset is needed.
def check_for_reg_overlap(self):
    system = bpy.context.user_preferences.system
    if system.use_region_overlap:
        area = bpy.context.area
        for r in area.regions:
            if r.type == 'TOOLS':
                self.rtoolsw = r.width


def draw_callback_px(self, context):
    draw_logo(  "Exact", [self.rtoolsw + 10, 92])
    draw_logo("Offsets", [self.rtoolsw + 10, 78])
    get_reg_rv3d()

    # would prefer not to do pop-up check inside draw_callback, but not sure
    # how else to check for input. need higher level "input handler" class?
    if self.addon_mode == CHECK_POPUP_INFO:
        check_popup_input(self)

    elif self.addon_mode == GET_0_OR_180:
        choose_0_or_180(self.ref_pts.rp_ls[1], *self.modal_buff, self.mouse_co)

    draw_ui(self)


class Xoffsets(bpy.types.Operator):
    """Select vertices with the mouse"""
    bl_idname = "view3d.xoffsets_main"
    bl_label = "Exact Offsets"

    # Only launch Add-On when active object is a MESH and Blender
    # is in OBJECT mode or EDIT_MESH mode.
    @classmethod
    def poll(self, context):
        if context.mode == 'OBJECT' or context.mode == 'EDIT_MESH':
            if bpy.context.scene.objects.active is not None:
                return bpy.context.scene.objects.active.type == 'MESH'
        else:
            return False

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'A', 'MIDDLEMOUSE', 'WHEELUPMOUSE',
        'WHEELDOWNMOUSE', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4',
        'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9', 'TAB'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFTMOUSE':
            self.left_click_held = event.value == 'PRESS'

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            # below needed for snap b/c grab op will eat mouse events
            self.left_click_co = Vector((event.mouse_region_x, event.mouse_region_y))
            proc_click(self)

        if event.type == 'RIGHTMOUSE':
            if self.left_click_held:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                exit_addon(self)
                return {'CANCELLED'}
            else:
                return {'PASS_THROUGH'}

        if event.type == 'C' and event.value == 'PRESS':
            axis_key_check(self, '')

        if event.type == 'X' and event.value == 'PRESS':
            axis_key_check(self, 'X')

        if event.type == 'Y' and event.value == 'PRESS':
            axis_key_check(self, 'Y')

        if event.type == 'Z' and event.value == 'PRESS':
            axis_key_check(self, 'Z')

        #if event.type == 'D' and event.value == 'PRESS':
        #    __import__('code').interact(local=dict(globals(), **locals()))

        if event.type == 'ESC':
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
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                    draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.settings_backup = None
            self.sel_backup = SceneSelectionInfo()  # selection backup
            self.rtoolsw = 0  # region tools (toolbar) width
            self.addon_mode = CLICK_CHECK  # addon mode
            self.transf_type = ""  # transform type
            self.pt_find_md = SLOW3DTO2D  # point find mode
            self.r_dat = RotationData()
            self.ref_pts = ReferencePoints()
            self.new_free_co = ()  # new free coordinates
            self.meas_btn_co = []
            self.meas_btn_act = False  # measure button active
            self.snap_btn_co = []
            self.snap_btn_act = True
            self.modal_buff = []
            self.mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))
            self.left_click_held = False
            self.left_click_co = None
            self.force_quit = False

            #print("Exact Offsets started!")  # debug
            check_for_reg_overlap(self)
            self.sel_backup.start_run()
            self.settings_backup = backup_snap_settings()
            init_snap_settings()
            draw_ui(self)  # sets up self.snap_btn_co values
            editmode_refresh()  # refresh the viewport
            context.window_manager.modal_handler_add(self)
            get_reg_rv3d()

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(Xoffsets)
    bpy.utils.register_class(ChangeInputPanel)

def unregister():
    bpy.utils.unregister_class(Xoffsets)
    bpy.utils.unregister_class(ChangeInputPanel)

if __name__ == "__main__":
    register()
