# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import bmesh

from mathutils import Vector
from mathutils.geometry import intersect_point_line

from .snap_context_l.utils_projection import intersect_ray_ray_fac

from .common_utilities import snap_utilities
from .common_classes import (
    CharMap,
    Constrain,
    SnapNavigation,
    SnapUtilities,
)


if not __package__:
    __package__ = "mesh_snap_utilities_line"


def get_closest_edge(bm, point, dist):
    r_edge = None
    for edge in bm.edges:
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        # Test the BVH (AABB) first
        for i in range(3):
            if v1[i] <= v2[i]:
                isect = v1[i] - dist <= point[i] <= v2[i] + dist
            else:
                isect = v2[i] - dist <= point[i] <= v1[i] + dist

            if not isect:
                break
        else:
            ret = intersect_point_line(point, v1, v2)

            if ret[1] < 0.0:
                tmp = v1
            elif ret[1] > 1.0:
                tmp = v2
            else:
                tmp = ret[0]

            new_dist = (point - tmp).length
            if new_dist <= dist:
                dist = new_dist
                r_edge = edge

    return r_edge


def get_loose_linked_edges(vert):
    linked = [e for e in vert.link_edges if e.is_wire]
    for e in linked:
        linked += [le for v in e.verts if v.is_wire for le in v.link_edges if le not in linked]
    return linked


def make_line(self, bm_geom, location):
    obj = self.main_snap_obj.data[0]
    bm = self.main_bm
    split_faces = set()

    update_edit_mesh = False

    if bm_geom is None:
        vert = bm.verts.new(location)
        self.list_verts.append(vert)
        update_edit_mesh = True

    elif isinstance(bm_geom, bmesh.types.BMVert):
        if (bm_geom.co - location).length_squared < .001:
            if self.list_verts == [] or self.list_verts[-1] != bm_geom:
                self.list_verts.append(bm_geom)
        else:
            vert = bm.verts.new(location)
            self.list_verts.append(vert)
            update_edit_mesh = True

    elif isinstance(bm_geom, bmesh.types.BMEdge):
        self.list_edges.append(bm_geom)
        ret = intersect_point_line(
            location, bm_geom.verts[0].co, bm_geom.verts[1].co)

        if (ret[0] - location).length_squared < .001:
            if ret[1] == 0.0:
                vert = bm_geom.verts[0]
            elif ret[1] == 1.0:
                vert = bm_geom.verts[1]
            else:
                edge, vert = bmesh.utils.edge_split(
                    bm_geom, bm_geom.verts[0], ret[1])
                update_edit_mesh = True

            if self.list_verts == [] or self.list_verts[-1] != vert:
                self.list_verts.append(vert)
                self.geom = vert  # hack to highlight in the drawing
            # self.list_edges.append(edge)

        else:  # constrain point is near
            vert = bm.verts.new(location)
            self.list_verts.append(vert)
            update_edit_mesh = True

    elif isinstance(bm_geom, bmesh.types.BMFace):
        split_faces.add(bm_geom)
        vert = bm.verts.new(location)
        self.list_verts.append(vert)
        update_edit_mesh = True

    # draw, split and create face
    if len(self.list_verts) >= 2:
        v1, v2 = self.list_verts[-2:]
        edge = bm.edges.get([v1, v2])
        if edge:
            self.list_edges.append(edge)
        else:
            if not v2.link_edges:
                edge = bm.edges.new([v1, v2])
                self.list_edges.append(edge)
            else:  # split face
                v1_link_faces = v1.link_faces
                v2_link_faces = v2.link_faces
                if v1_link_faces and v2_link_faces:
                    split_faces.update(
                        set(v1_link_faces).intersection(v2_link_faces))

                else:
                    if v1_link_faces:
                        faces = v1_link_faces
                        co2 = v2.co.copy()
                    else:
                        faces = v2_link_faces
                        co2 = v1.co.copy()

                    for face in faces:
                        if bmesh.geometry.intersect_face_point(face, co2):
                            co = co2 - face.calc_center_median()
                            if co.dot(face.normal) < 0.001:
                                split_faces.add(face)

                if split_faces:
                    edge = bm.edges.new([v1, v2])
                    self.list_edges.append(edge)
                    ed_list = get_loose_linked_edges(v2)
                    for face in split_faces:
                        facesp = bmesh.utils.face_split_edgenet(face, ed_list)
                    del split_faces
                else:
                    if self.intersect:
                        facesp = bmesh.ops.connect_vert_pair(
                            bm, verts=[v1, v2], verts_exclude=bm.verts)
                        # print(facesp)
                    if not self.intersect or not facesp['edges']:
                        edge = bm.edges.new([v1, v2])
                        self.list_edges.append(edge)
                    else:
                        for edge in facesp['edges']:
                            self.list_edges.append(edge)
            update_edit_mesh = True

        # create face
        if self.create_face:
            ed_list = set(self.list_edges)
            for edge in v2.link_edges:
                if edge not in ed_list and edge.other_vert(v2) in self.list_verts:
                    ed_list.add(edge)
                    break

            ed_list.update(get_loose_linked_edges(v2))
            ed_list = list(ed_list)

            # WORKAROUND: `edgenet_fill` only works with loose edges or boundary
            # edges, so remove the other edges and create temporary elements to
            # replace them.
            targetmap = {}
            ed_new = []
            for edge in ed_list:
                if not edge.is_wire and not edge.is_boundary:
                    v1, v2 = edge.verts
                    tmp_vert = bm.verts.new(v2.co)
                    e1 = bm.edges.new([v1, tmp_vert])
                    e2 = bm.edges.new([tmp_vert, v2])
                    ed_list.remove(edge)
                    ed_new.append(e1)
                    ed_new.append(e2)
                    targetmap[tmp_vert] = v2

            bmesh.ops.edgenet_fill(bm, edges=ed_list + ed_new)
            if targetmap:
                bmesh.ops.weld_verts(bm, targetmap=targetmap)

            update_edit_mesh = True
            # print('face created')

    if update_edit_mesh:
        obj.data.update_gpu_tag()
        obj.data.update_tag()
        obj.update_from_editmode()
        obj.update_tag()
        bmesh.update_edit_mesh(obj.data)
        self.sctx.tag_update_drawn_snap_object(self.main_snap_obj)
        # bm.verts.index_update()

        bpy.ops.ed.undo_push(message="Undo draw line*")

    return [obj.matrix_world @ v.co for v in self.list_verts]


class SnapUtilitiesLine(SnapUtilities, bpy.types.Operator):
    """Make Lines. Connect them to split faces"""
    bl_idname = "mesh.snap_utilities_line"
    bl_label = "Line Tool"
    bl_options = {'REGISTER'}

    wait_for_input: bpy.props.BoolProperty(name="Wait for Input", default=True)

    def _exit(self, context):
        # avoids unpredictable crashes
        del self.main_snap_obj
        del self.main_bm
        del self.list_edges
        del self.list_verts
        del self.list_verts_co

        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.area.header_text_set(None)
        self.snap_context_free()

        # Restore initial state
        context.tool_settings.mesh_select_mode = self.select_mode
        context.space_data.overlay.show_face_center = self.show_face_center

    def _init_snap_line_context(self, context):
        self.prevloc = Vector()
        self.list_verts = []
        self.list_edges = []
        self.list_verts_co = []
        self.bool_update = True
        self.vector_constrain = ()
        self.len = 0
        self.curr_dir = Vector()

        if not (self.bm and self.obj):
            self.obj = context.edit_object
            self.bm = bmesh.from_edit_mesh(self.obj.data)

        self.main_snap_obj = self.snap_obj = self.sctx._get_snap_obj_by_obj(
            self.obj)
        self.main_bm = self.bm

    def _shift_contrain_callback(self):
        if isinstance(self.geom, bmesh.types.BMEdge):
            mat = self.main_snap_obj.mat
            verts_co = [mat @ v.co for v in self.geom.verts]
            return verts_co[1] - verts_co[0]

    def modal(self, context, event):
        if self.navigation_ops.run(context, event, self.prevloc if self.vector_constrain else self.location):
            return {'RUNNING_MODAL'}

        if event.ctrl and event.type == 'Z' and event.value == 'PRESS':
            bpy.ops.ed.undo()
            if not self.wait_for_input:
                self._exit(context)
                return {'FINISHED'}
            else:
                del self.bm
                del self.main_bm
                self.charmap.clear()

                bpy.ops.object.mode_set(mode='EDIT')  # just to be sure
                bpy.ops.mesh.select_all(action='DESELECT')
                context.tool_settings.mesh_select_mode = (True, False, True)
                context.space_data.overlay.show_face_center = True

                self.snap_context_update(context)
                self._init_snap_line_context(context)
                self.sctx.update_all()

                return {'RUNNING_MODAL'}

        is_making_lines = bool(self.list_verts_co)

        if (event.type == 'MOUSEMOVE' or self.bool_update):
            mval = Vector((event.mouse_region_x, event.mouse_region_y))
            if self.charmap.length_entered_value != 0.0:
                ray_dir, ray_orig = self.sctx.get_ray(mval)
                loc = self.list_verts_co[-1]
                fac = intersect_ray_ray_fac(loc, self.curr_dir, ray_orig, ray_dir)
                if fac < 0.0:
                    self.curr_dir.negate()
                    self.location = loc - (self.location - loc)
            else:
                if self.rv3d.view_matrix != self.rotMat:
                    self.rotMat = self.rv3d.view_matrix.copy()
                    self.bool_update = True
                    snap_utilities.cache.clear()
                else:
                    self.bool_update = False

                self.snap_obj, self.prevloc, self.location, self.type, self.bm, self.geom, self.len = snap_utilities(
                    self.sctx,
                    self.main_snap_obj,
                    mval,
                    constrain=self.vector_constrain,
                    previous_vert=(
                        self.list_verts[-1] if self.list_verts else None),
                    increment=self.incremental)

                self.snap_to_grid()

                if is_making_lines:
                    loc = self.list_verts_co[-1]
                    self.curr_dir = self.location - loc
                    if self.preferences.auto_constrain:
                        vec, cons_type = self.constrain.update(
                            self.sctx.region, self.sctx.rv3d, mval, loc)
                        self.vector_constrain = [loc, loc + vec, cons_type]

        elif event.value == 'PRESS':
            if is_making_lines and self.charmap.modal_(context, event):
                self.bool_update = self.charmap.length_entered_value == 0.0

                if not self.bool_update:
                    text_value = self.charmap.length_entered_value
                    vector = self.curr_dir.normalized()
                    self.location = self.list_verts_co[-1] + (vector * text_value)

            elif self.constrain.modal(event, self._shift_contrain_callback):
                self.bool_update = True
                if self.constrain.last_vec:
                    if self.list_verts_co:
                        loc = self.list_verts_co[-1]
                    else:
                        loc = self.location

                    self.vector_constrain = (
                        loc, loc + self.constrain.last_vec, self.constrain.last_type)
                else:
                    self.vector_constrain = None

            elif event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}:
                if event.type == 'LEFTMOUSE' or self.charmap.length_entered_value != 0.0:
                    if not is_making_lines and self.bm:
                        self.main_snap_obj = self.snap_obj
                        self.main_bm = self.bm

                    mat_inv = self.main_snap_obj.mat.inverted_safe()
                    point = mat_inv @ self.location
                    geom2 = self.geom
                    if geom2:
                        geom2.select = False

                    if self.vector_constrain:
                        geom2 = get_closest_edge(self.main_bm, point, .001)

                    self.list_verts_co = make_line(self, geom2, point)

                    self.vector_constrain = None
                    self.charmap.clear()
                else:
                    self._exit(context)
                    return {'FINISHED'}

            elif event.type == 'F8':
                self.vector_constrain = None
                self.constrain.toggle()

            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                if not self.wait_for_input or not is_making_lines or event.type == 'ESC':
                    if self.geom:
                        self.geom.select = True
                    self._exit(context)
                    return {'FINISHED'}
                else:
                    snap_utilities.cache.clear()
                    self.vector_constrain = None
                    self.list_edges = []
                    self.list_verts = []
                    self.list_verts_co = []
                    self.charmap.clear()
        else:
            return {'RUNNING_MODAL'}

        a = ""
        if is_making_lines:
            a = 'length: ' + self.charmap.get_converted_length_str(self.len)

        context.area.header_text_set(
            text="hit: %.3f %.3f %.3f %s" % (*self.location, a))

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def draw_callback_px(self):
        if self.bm:
            self.draw_cache.draw_elem(self.snap_obj, self.bm, self.geom)
        self.draw_cache.draw(self.type, self.location,
                             self.list_verts_co, self.vector_constrain, self.prevloc)

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            self.snap_context_init(context)
            self.snap_context_update(context)

            self.constrain = Constrain(
                self.preferences, context.scene, self.obj)

            self.intersect = self.preferences.intersect
            self.create_face = self.preferences.create_face
            self.navigation_ops = SnapNavigation(context, True)
            self.charmap = CharMap(context)

            self._init_snap_line_context(context)

            # print('name', __name__, __package__)

            # Store current state
            self.select_mode = context.tool_settings.mesh_select_mode[:]
            self.show_face_center = context.space_data.overlay.show_face_center

            # Modify the current state
            bpy.ops.mesh.select_all(action='DESELECT')
            context.tool_settings.mesh_select_mode = (True, False, True)
            context.space_data.overlay.show_face_center = True

            # Store values from 3d view context
            self.rv3d = context.region_data
            self.rotMat = self.rv3d.view_matrix.copy()
            # self.obj_matrix.transposed())

            # modals
            context.window_manager.modal_handler_add(self)

            if not self.wait_for_input:
                if not self.snapwidgets:
                    self.modal(context, event)
                else:
                    mat_inv = self.obj.matrix_world.inverted_safe()
                    point = mat_inv @ self.location
                    self.list_verts_co = make_line(self, self.geom, point)

            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                self.draw_callback_px, (), 'WINDOW', 'POST_VIEW')

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(SnapUtilitiesLine)


if __name__ == "__main__":
    register()
