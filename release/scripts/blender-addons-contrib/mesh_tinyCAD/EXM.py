'''
BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

END GPL LICENCE BLOCK
'''

import math
import itertools

import bpy
import bgl
import mathutils
import bmesh

from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d

from mesh_tinyCAD import cad_module as cm


line_colors = {
    "prime": (0.2, 0.8, 0.9),
    "extend": (0.9, 0.8, 0.2),
    "projection": (0.9, 0.6, 0.5)
}


def restore_bgl_defaults():
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


def get_projection_coords(self):
    list2d = [val for key, val in self.xvectors.items()]
    list2d = [[p, self.bm.verts[pidx].co] for (p, pidx) in list2d]
    return list(itertools.chain.from_iterable(list2d))


def get_extender_coords(self):
    coords = []
    for idx in self.selected_edges:
        c = cm.coords_tuple_from_edge_idx(self.bm, idx)
        coords.extend(c)
    return coords


def add_or_remove_new_edge(self, idx):
    '''
        - only add idx if not edge_prime
        - and not currently present in selected_edges
    '''
    p_idx = self.edge_prime_idx

    if idx == p_idx:
        print(idx, 'is edge prime, not adding')
        return

    if (idx in self.selected_edges):
        self.selected_edges.remove(idx)
        del self.xvectors[idx]
    else:
        edge_prime = cm.coords_tuple_from_edge_idx(self.bm, p_idx)
        edge2 = cm.coords_tuple_from_edge_idx(self.bm, idx)
        p = cm.get_intersection(edge_prime, edge2)

        if not cm.point_on_edge(p, edge_prime):
            return

        vert_idx_closest = cm.closest_idx(p, self.bm.edges[idx])
        self.xvectors[idx] = [p, vert_idx_closest]
        self.selected_edges.append(idx)


def set_mesh_data(self):
    history = self.bm.select_history
    if not (len(history) > 0):
        return

    a = history[-1]
    if not isinstance(a, bmesh.types.BMEdge):
        return

    add_or_remove_new_edge(self, a.index)
    a.select = False


def draw_callback_px(self, context, event):

    if context.mode != "EDIT_MESH":
        return

    # get screen information
    region = context.region
    rv3d = context.space_data.region_3d
    this_object = context.active_object
    matrix_world = this_object.matrix_world
    # scene = context.scene

    def draw_gl_strip(coords, line_thickness):
        bgl.glLineWidth(line_thickness)
        bgl.glBegin(bgl.GL_LINES)
        for coord in coords:
            vector3d = matrix_world * coord
            vector2d = loc3d2d(region, rv3d, vector3d)
            bgl.glVertex2f(*vector2d)
        bgl.glEnd()

    def draw_edge(coords, mode, lt):
        bgl.glColor3f(*line_colors[mode])
        draw_gl_strip(coords, lt)

    def do_single_draw_pass(self):

        # draw edge prime
        c = cm.coords_tuple_from_edge_idx(self.bm, self.edge_prime_idx)
        draw_edge(c, "prime", 3)

        # draw extender edges and projections.
        if len(self.selected_edges) > 0:

            # get and draw selected valid edges
            coords_ext = get_extender_coords(self)
            draw_edge(coords_ext, "extend", 3)

            # get and draw extenders only
            coords_proj = get_projection_coords(self)
            draw_edge(coords_proj, "projection", 3)

        restore_bgl_defaults()

    do_single_draw_pass(self)


class ExtendEdgesMulti(bpy.types.Operator):
    bl_idname = "mesh.extendmulti"
    bl_label = "EXM extend multiple edges"
    bl_description = "extend edge towards"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def modify_geometry(self, context, event_type):
        list2d = [val for key, val in self.xvectors.items()]
        vertex_count = len(self.bm.verts)

        # adds new geometry
        if event_type == 'PERIOD':

            for point, closest_idx in list2d:
                self.bm.verts.new((point))
                v1 = self.bm.verts[-1]
                v2 = self.bm.verts[closest_idx]
                self.bm.edges.new((v1, v2))

        # extend current egdes towards intersections
        elif event_type == 'COMMA':

            for point, closest_idx in list2d:
                self.bm.verts[closest_idx].co = point

        bmesh.update_edit_mesh(self.me)

    def modal(self, context, event):

        if event.type in ('PERIOD', 'COMMA', 'ESC'):
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            bpy.context.space_data.show_manipulator = True

            if not (event.type is 'ESC'):
                self.modify_geometry(context, event.type)

            del self.selected_edges
            del self.xvectors
            return {'FINISHED'}

        if (event.type, event.value) == ("RIGHTMOUSE", "RELEASE"):
            set_mesh_data(self)

        if context.area:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == "VIEW_3D":

            self.selected_edges = []
            self.xvectors = {}
            self.me = context.active_object.data
            self.bm = bmesh.from_edit_mesh(self.me)
            self.me.update()

            # enforce singular edge selection first then assign to edge_prime
            m = [e.index for e in self.bm.edges if e.select]
            if not len(m) is 1:
                self.report({"WARNING"}, "Please select 1 edge only")
                return {'CANCELLED'}

            # switch off axial manipulator, set important variables.
            self.edge_prime_idx = m[0]
            bpy.context.space_data.show_manipulator = False

            # configure draw handler
            fparams = self, context, event
            handler_config = draw_callback_px, fparams, 'WINDOW', 'POST_PIXEL'
            draw_handler_add = bpy.types.SpaceView3D.draw_handler_add
            self.handle = draw_handler_add(*handler_config)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({"WARNING"}, "Please run operator from within 3d view")
            return {'CANCELLED'}
