# SPDX-FileCopyrightText: 2011-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Inset Straight Skeleton",
    "author": "Howard Trickey",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "3DView Operator",
    "description": "Make an inset inside selection using straight skeleton algorithm.",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/mesh/inset_straight_skeleton.html",
    "category": "Mesh",
}


if "bpy" in locals():
    import importlib
else:
    from . import (
            geom,
            model,
            offset,
            triquad,
            )

import math
import bpy
import bmesh
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        )

SpaceView3D = bpy.types.SpaceView3D

INSET_VALUE = 0
HEIGHT_VALUE = 1
NUM_VALUES = 2

# TODO: make a dooted-line shader
shader = gpu.shader.from_builtin('UNIFORM_COLOR') if not bpy.app.background else None

class MESH_OT_InsetStraightSkeleton(bpy.types.Operator):
    bl_idname = "mesh.insetstraightskeleton"
    bl_label = "Inset Straight Skeleton"
    bl_description = "Make an inset inside selection using straight skeleton algorithm"
    bl_options = {'UNDO', 'REGISTER', 'GRAB_CURSOR', 'BLOCKING'}

    inset_amount: FloatProperty(name="Amount",
        description="Amount to move inset edges",
        default=0.0,
        min=0.0,
        max=1000.0,
        soft_min=0.0,
        soft_max=100.0,
        unit='LENGTH')
    inset_height: FloatProperty(name="Height",
        description="Amount to raise inset faces",
        default=0.0,
        min=-10000.0,
        max=10000.0,
        soft_min=-500.0,
        soft_max=500.0,
        unit='LENGTH')
    region: BoolProperty(name="Region",
        description="Inset selection as one region?",
        default=True)
    quadrangulate: BoolProperty(name="Quadrangulate",
        description="Quadrangulate after inset?",
        default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Inset Options:")
        box.prop(self, "inset_amount")
        box.prop(self, "inset_height")
        box.prop(self, "region")
        box.prop(self, "quadrangulate")

    def invoke(self, context, event):
        self.modal = True
        # make backup bmesh from current mesh, after flushing editmode to mesh
        bpy.context.object.update_from_editmode()
        self.backup = bmesh.new()
        self.backup.from_mesh(bpy.context.object.data)
        self.inset_amount = 0.0
        self.inset_height = 0.0
        self.center, self.center3d = calc_select_center(context)
        self.center_pixel_size = calc_pixel_size(context, self.center3d)
        udpi = context.preferences.system.dpi
        upixelsize = context.preferences.system.pixel_size
        self.pixels_per_inch = udpi * upixelsize
        self.value_mode = INSET_VALUE
        self.initial_length = [-1.0, -1.0]
        self.scale = [self.center_pixel_size] * NUM_VALUES
        self.calc_initial_length(event, True)
        self.mouse_cur = Vector((event.mouse_region_x, event.mouse_region_y))
        col = context.preferences.themes["Default"].view_3d.view_overlay
        self.line_color = (col.r, col.g, col.b, 1.0)

        self.action(context)

        context.window_manager.modal_handler_add(self)
        self.draw_handle = SpaceView3D.draw_handler_add(draw_callback,
            (self,), 'WINDOW', 'POST_PIXEL')

        return {'RUNNING_MODAL'}

    def calc_initial_length(self, event, mode_changed):
        mdiff = self.center - Vector((event.mouse_region_x, event.mouse_region_y))
        mlen = mdiff.length;
        vmode = self.value_mode
        if mode_changed or self.initial_length[vmode] == -1:
            if vmode == INSET_VALUE:
                value = self.inset_amount
            else:
               value = self.inset_height
            sc = self.scale[vmode]
            if value != 0.0:
                mlen = mlen - value / sc
        self.initial_length[vmode] = mlen

    def modal(self, context, event):
        if event.type in ['LEFTMOUSE', 'RIGHTMOUSE', 'ESC']:
            if self.modal:
                self.backup.free()
            if self.draw_handle:
                SpaceView3D.draw_handler_remove(self.draw_handle, 'WINDOW')
                context.area.tag_redraw()
            if event.type == 'LEFTMOUSE':  # Confirm
                return {'FINISHED'}
            else:  # Cancel
                return {'CANCELLED'}
        else:
            # restore mesh to original state
            bpy.ops.object.editmode_toggle()
            self.backup.to_mesh(bpy.context.object.data)
            bpy.ops.object.editmode_toggle()
            if event.type == 'MOUSEMOVE':
                if self.value_mode == INSET_VALUE and event.ctrl:
                    self.value_mode = HEIGHT_VALUE
                    self.calc_initial_length(event, True)
                elif self.value_mode == HEIGHT_VALUE and not event.ctrl:
                    self.value_mode = INSET_VALUE
                    self.calc_initial_length(event, True)
                self.mouse_cur = Vector((event.mouse_region_x, event.mouse_region_y))
                vmode = self.value_mode
                mdiff = self.center - self.mouse_cur
                value = (mdiff.length - self.initial_length[vmode]) * self.scale[vmode]
                if vmode == INSET_VALUE:
                    self.inset_amount = value
                else:
                    self.inset_height = value
            elif event.type == 'R' and event.value == 'PRESS':
                self.region = not self.region
            elif event.type == 'Q' and event.value == 'PRESS':
                self.quadrangulate = not self.quadrangulate
            self.action(context)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.modal = False
        self.action(context)
        return {'FINISHED'}

    def action(self, context):
        obj = bpy.context.active_object
        mesh = obj.data
        do_inset(mesh, self.inset_amount, self.inset_height, self.region,
                self.quadrangulate)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()


def draw_callback(op):
    startpos = op.mouse_cur
    endpos = op.center
    coords = [startpos.to_tuple(), endpos.to_tuple()]
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})

    try:
        shader.bind()
        shader.uniform_float("color", op.line_color)
        batch.draw(shader)
    except:
        pass

def calc_pixel_size(context, co):
    # returns size in blender units of a pixel at 3d coord co
    # see C code in ED_view3d_pixel_size and ED_view3d_update_viewmat
    m = context.region_data.perspective_matrix
    v1 = m[0].to_3d()
    v2 = m[1].to_3d()
    ll = min(v1.length_squared, v2.length_squared)
    len_pz = 2.0 / math.sqrt(ll)
    len_sz = max(context.region.width, context.region.height)
    rv3dpixsize = len_pz / len_sz
    proj = m[3][0] * co[0] + m[3][1] * co[1] + m[3][2] * co[2] + m[3][3]
    ups = context.preferences.system.pixel_size
    return proj * rv3dpixsize * ups

def calc_select_center(context):
    # returns region 2d coord and global 3d coord of selection center
    ob = bpy.context.active_object
    mesh = ob.data
    center = Vector((0.0, 0.0, 0.0))
    n = 0
    for v in mesh.vertices:
        if v.select:
            center = center + Vector(v.co)
            n += 1
    if n > 0:
        center = center / n
    world_center = ob.matrix_world @ center
    world_center_2d = view3d_utils.location_3d_to_region_2d( \
        context.region, context.region_data, world_center)
    return (world_center_2d, world_center)

def do_inset(mesh, amount, height, region, quadrangulate):
    if amount <= 0.0:
        return
    pitch = math.atan(height / amount)
    selfaces = []
    selface_indices = []
    bm = bmesh.from_edit_mesh(mesh)
    for face in bm.faces:
        if face.select:
            selfaces.append(face)
            selface_indices.append(face.index)
    m = geom.Model()
    # if add all mesh.vertices, coord indices will line up
    # Note: not using Points.AddPoint which does dup elim
    # because then would have to map vertices in and out
    m.points.pos = [v.co.to_tuple() for v in bm.verts]
    for f in selfaces:
        m.faces.append([loop.vert.index for loop in f.loops])
        m.face_data.append(f.index)
    orig_numv = len(m.points.pos)
    orig_numf = len(m.faces)
    model.BevelSelectionInModel(m, amount, pitch, quadrangulate, region, False)
    if len(m.faces) == orig_numf:
        # something went wrong with Bevel - just treat as no-op
        return
    blender_faces = m.faces[orig_numf:len(m.faces)]
    blender_old_face_index = m.face_data[orig_numf:len(m.faces)]
    for i in range(orig_numv, len(m.points.pos)):
        bvertnew = bm.verts.new(m.points.pos[i])
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    new_faces = []
    start_faces = len(bm.faces)
    for i, newf in enumerate(blender_faces):
        vs = remove_dups([bm.verts[j] for j in newf])
        if len(vs) < 3:
            continue
        # copy face attributes from old face that it was derived from
        bfi = blender_old_face_index[i]
        # sometimes, not sure why, this face already exists
        # bmesh will give a value error in bm.faces.new() in that case
        try:
            if bfi and 0 <= bfi < start_faces:
                bm.faces.ensure_lookup_table()
                oldface = bm.faces[bfi]
                bfacenew = bm.faces.new(vs, oldface)
                # bfacenew.copy_from_face_interp(oldface)
            else:
                bfacenew = bm.faces.new(vs)
            new_faces.append(bfacenew)
        except ValueError:
            # print("dup face with amount", amount)

            # print([v.index for v in vs])
            pass
    # deselect original faces
    for face in selfaces:
        face.select_set(False)
    # remove original faces
    bmesh.ops.delete(bm, geom=selfaces, context='FACES')
    # select all new faces (should only select inner faces, but that needs more surgery on rest of code)
    for face in new_faces:
        face.select_set(True)
    bmesh.update_edit_mesh(mesh)

def remove_dups(vs):
    seen = set()
    return [x for x in vs if not (x in seen or seen.add(x))]

def menu(self, context):
    self.layout.operator("mesh.insetstraightskeleton", text="Inset Straight Skeleton")

def register():
    bpy.utils.register_class(MESH_OT_InsetStraightSkeleton)
    bpy.types.VIEW3D_MT_edit_mesh_faces.append(menu)

def unregister():
    bpy.utils.unregister_class(MESH_OT_InsetStraightSkeleton)
    bpy.types.VIEW3D_MT_edit_mesh_faces.remove(menu)
