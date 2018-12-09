### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bgl
import gpu
import numpy as np

from .common_utilities import snap_utilities


class SnapDrawn():
    def __init__(self, out_color, face_color,
                 edge_color, vert_color, center_color,
                 perpendicular_color, constrain_shift_color,
                 axis_x_color, axis_y_color, axis_z_color):

        self.out_color = out_color
        self.face_color = face_color
        self.edge_color = edge_color
        self.vert_color = vert_color
        self.center_color = center_color
        self.perpendicular_color = perpendicular_color
        self.constrain_shift_color = constrain_shift_color

        self.axis_x_color = axis_x_color
        self.axis_y_color = axis_y_color
        self.axis_z_color = axis_z_color

        self._format_pos = gpu.types.GPUVertFormat()
        self._format_pos.attr_add(id="pos", comp_type='F32', len=3, fetch_mode='FLOAT')

        self._format_pos_and_color = gpu.types.GPUVertFormat()
        self._format_pos_and_color.attr_add(id="pos", comp_type='F32', len=3, fetch_mode='FLOAT')
        self._format_pos_and_color.attr_add(id="color", comp_type='F32', len=4, fetch_mode='FLOAT')

        self._program_unif_col = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
        self._program_smooth_col = gpu.shader.from_builtin("3D_SMOOTH_COLOR")

        self._batch_point = None
        self._batch_circle = None
        self._batch_vector = None


    def batch_line_strip_create(self, coords):
        vbo = gpu.types.GPUVertBuf(self._format_pos, len = len(coords))
        vbo.attr_fill(0, data = coords)
        batch_lines = gpu.types.GPUBatch(type = "LINE_STRIP", buf = vbo)
        return batch_lines

    def batch_lines_smooth_color_create(self, coords, colors):
        vbo = gpu.types.GPUVertBuf(self._format_pos_and_color, len = len(coords))
        vbo.attr_fill(0, data = coords)
        vbo.attr_fill(1, data = colors)
        batch_lines = gpu.types.GPUBatch(type = "LINES", buf = vbo)
        return batch_lines

    def batch_triangles_create(self, coords):
        vbo = gpu.types.GPUVertBuf(self._format_pos, len = len(coords))
        vbo.attr_fill(0, data = coords)
        batch_tris = gpu.types.GPUBatch(type = "TRIS", buf = vbo)
        return batch_tris

    def batch_point_get(self):
        if self._batch_point is None:
            vbo = gpu.types.GPUVertBuf(self._format_pos, len = 1)
            vbo.attr_fill(0, ((0.0, 0.0, 0.0),))
            self._batch_point = gpu.types.GPUBatch(type = "POINTS", buf = vbo)
        return self._batch_point

    def draw(self, type, location, list_verts_co, vector_constrain, prevloc):
        # draw 3d point OpenGL in the 3D View
        bgl.glEnable(bgl.GL_BLEND)
        gpu.matrix.push()
        self._program_unif_col.bind()

        if list_verts_co:
            # draw 3d line OpenGL in the 3D View
            bgl.glDepthRange(0, 0.9999)
            bgl.glLineWidth(3.0)

            batch = self.batch_line_strip_create([v.to_tuple() for v in list_verts_co] + [location.to_tuple()])

            self._program_unif_col.uniform_float("color", (1.0, 0.8, 0.0, 0.5))
            batch.draw(self._program_unif_col)
            del batch

        bgl.glDisable(bgl.GL_DEPTH_TEST)

        point_batch = self.batch_point_get()
        if vector_constrain:
            if prevloc:
                bgl.glPointSize(5)
                gpu.matrix.translate(prevloc)
                self._program_unif_col.uniform_float("color", (1.0, 1.0, 1.0, 0.5))
                point_batch.draw(self._program_unif_col)
                gpu.matrix.translate(-prevloc)

            if vector_constrain[2] == 'X':
                Color4f = self.axis_x_color
            elif vector_constrain[2] == 'Y':
                Color4f = self.axis_y_color
            elif vector_constrain[2] == 'Z':
                Color4f = self.axis_z_color
            else:
                Color4f = self.constrain_shift_color
        else:
            if type == 'OUT':
                Color4f = self.out_color
            elif type == 'FACE':
                Color4f = self.face_color
            elif type == 'EDGE':
                Color4f = self.edge_color
            elif type == 'VERT':
                Color4f = self.vert_color
            elif type == 'CENTER':
                Color4f = self.center_color
            elif type == 'PERPENDICULAR':
                Color4f = self.perpendicular_color
            else: # type == None
                Color4f = self.out_color

        bgl.glPointSize(10)

        gpu.matrix.translate(location)
        self._program_unif_col.uniform_float("color", Color4f)
        point_batch.draw(self._program_unif_col)

        # restore opengl defaults
        bgl.glDepthRange(0.0, 1.0)
        bgl.glPointSize(1.0)
        bgl.glLineWidth(1.0)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glDisable(bgl.GL_BLEND)

        gpu.matrix.pop()

    def draw_elem(self, snap_obj, bm, elem):
        from bmesh.types import(
            BMVert,
            BMEdge,
            BMFace,
        )
        # draw 3d point OpenGL in the 3D View
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_DEPTH_TEST)

        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(snap_obj.mat)

            if isinstance(elem, BMVert):
                if elem.link_edges:
                    color = self.vert_color
                    edges = np.empty((len(elem.link_edges), 2), [("pos", "f4", 3), ("color", "f4", 4)])
                    edges["pos"][:, 0] = elem.co
                    edges["pos"][:, 1] = [e.other_vert(elem).co for e in elem.link_edges]
                    edges["color"][:, 0] = color
                    edges["color"][:, 1] = (color[0], color[1], color[2], 0.0)
                    edges.shape = -1

                    self._program_smooth_col.bind()
                    bgl.glLineWidth(3.0)
                    batch = self.batch_lines_smooth_color_create(edges["pos"], edges["color"])
                    batch.draw(self._program_smooth_col)
                    bgl.glLineWidth(1.0)
            else:
                self._program_unif_col.bind()

                if isinstance(elem, BMEdge):
                    self._program_unif_col.uniform_float("color", self.edge_color)

                    bgl.glLineWidth(3.0)
                    batch = self.batch_line_strip_create([v.co for v in elem.verts])
                    batch.draw(self._program_unif_col)
                    bgl.glLineWidth(1.0)

                elif isinstance(elem, BMFace):
                    if len(snap_obj.data) == 2:
                        face_color = self.face_color[0], self.face_color[1], self.face_color[2], self.face_color[3] * 0.2
                        self._program_unif_col.uniform_float("color", face_color)

                        tris = snap_obj.data[1].get_loop_tri_co_by_bmface(bm, elem)
                        tris.shape = (-1, 3)
                        batch = self.batch_triangles_create(tris)
                        batch.draw(self._program_unif_col)

            # restore opengl defaults
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glDisable(bgl.GL_BLEND)


class SnapNavigation():
    @staticmethod
    def debug_key(key):
        for member in dir(key):
            print(member, getattr(key, member))

    @staticmethod
    def convert_to_flag(shift, ctrl, alt):
        return (shift << 0) | (ctrl << 1) | (alt << 2)

    def __init__(self, context, use_ndof):
        # TO DO:
        # 'View Orbit', 'View Pan', 'NDOF Orbit View', 'NDOF Pan View'
        self.use_ndof = use_ndof and context.user_preferences.inputs.use_ndof

        self._rotate = set()
        self._move = set()
        self._zoom = set()

        if self.use_ndof:
            self._ndof_all = set()
            self._ndof_orbit = set()
            self._ndof_orbit_zoom = set()
            self._ndof_pan = set()

        for key in context.window_manager.keyconfigs.user.keymaps['3D View'].keymap_items:
            if key.idname == 'view3d.rotate':
                self._rotate.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type, key.value))
            elif key.idname == 'view3d.move':
                self._move.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type, key.value))
            elif key.idname == 'view3d.zoom':
                if key.type == 'WHEELINMOUSE':
                    self._zoom.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), 'WHEELUPMOUSE', key.value, key.properties.delta))
                elif key.type == 'WHEELOUTMOUSE':
                    self._zoom.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), 'WHEELDOWNMOUSE', key.value, key.properties.delta))
                else:
                    self._zoom.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type, key.value, key.properties.delta))

            elif self.use_ndof:
                if key.idname == 'view3d.ndof_all':
                    self._ndof_all.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type))
                elif key.idname == 'view3d.ndof_orbit':
                    self._ndof_orbit.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type))
                elif key.idname == 'view3d.ndof_orbit_zoom':
                    self._ndof_orbit_zoom.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type))
                elif key.idname == 'view3d.ndof_pan':
                    self._ndof_pan.add((self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type))


    def run(self, context, event, snap_location):
        evkey = (self.convert_to_flag(event.shift, event.ctrl, event.alt), event.type, event.value)

        if evkey in self._rotate:
            if snap_location:
                bpy.ops.view3d.rotate_custom_pivot('INVOKE_DEFAULT', pivot=snap_location)
            else:
                bpy.ops.view3d.rotate('INVOKE_DEFAULT', use_mouse_init=True)
            return True

        if evkey in self._move:
            #if event.shift and self.vector_constrain and \
            #    self.vector_constrain[2] in {'RIGHT_SHIFT', 'LEFT_SHIFT', 'shift'}:
            #    self.vector_constrain = None
            bpy.ops.view3d.move('INVOKE_DEFAULT')
            return True

        for key in self._zoom:
            if evkey == key[0:3]:
                if snap_location and key[3]:
                    bpy.ops.view3d.zoom_custom_target('INVOKE_DEFAULT', delta=key[3], target=snap_location)
                else:
                    bpy.ops.view3d.zoom('INVOKE_DEFAULT', delta=key[3])
                return True

        if self.use_ndof:
            ndofkey = evkey[:2]
            if ndofkey in self._ndof_all:
                bpy.ops.view3d.ndof_all('INVOKE_DEFAULT')
                return True
            if ndofkey in self._ndof_orbit:
                bpy.ops.view3d.ndof_orbit('INVOKE_DEFAULT')
                return True
            if ndofkey in self._ndof_orbit_zoom:
                bpy.ops.view3d.ndof_orbit_zoom('INVOKE_DEFAULT')
                return True
            if ndofkey in self._ndof_pan:
                bpy.ops.view3d.ndof_pan('INVOKE_DEFAULT')
                return True

        return False


class CharMap:
    ascii = {
        ".", ",", "-", "+", "1", "2", "3",
        "4", "5", "6", "7", "8", "9", "0",
        "c", "m", "d", "k", "h", "a",
        " ", "/", "*", "'", "\""
        # "="
        }
    type = {
        'BACK_SPACE', 'DEL',
        'LEFT_ARROW', 'RIGHT_ARROW'
        }

    @staticmethod
    def modal(self, context, event):
        c = event.ascii
        if c:
            if c == ",":
                c = "."
            self.length_entered = self.length_entered[:self.line_pos] + c + self.length_entered[self.line_pos:]
            self.line_pos += 1
        if self.length_entered:
            if event.type == 'BACK_SPACE':
                self.length_entered = self.length_entered[:self.line_pos - 1] + self.length_entered[self.line_pos:]
                self.line_pos -= 1

            elif event.type == 'DEL':
                self.length_entered = self.length_entered[:self.line_pos] + self.length_entered[self.line_pos + 1:]

            elif event.type == 'LEFT_ARROW':
                self.line_pos = (self.line_pos - 1) % (len(self.length_entered) + 1)

            elif event.type == 'RIGHT_ARROW':
                self.line_pos = (self.line_pos + 1) % (len(self.length_entered) + 1)

g_snap_widget = [None]

class MousePointWidget(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_mouse_point"

    __slots__ = (
        "sctx",
        "bm",
        "draw_cache",
        "geom",
        "incremental",
        "preferences",
        "loc",
        "snap_obj",
        "snap_to_grid",
        "type",
    )

    def test_select(self, context, mval):
        #print('test_select', mval)
        self.snap_obj, prev_loc, self.loc, self.type, self.bm, self.geom, len = snap_utilities(
                self.sctx,
                None,
                mval,
                increment=self.incremental
        )
        context.area.tag_redraw()
        return False

    def draw(self, context):
        if self.bm:
            self.draw_cache.draw_elem(self.snap_obj, self.bm, self.geom)
        self.draw_cache.draw(self.type, self.loc, None, None, None)

    def setup(self):
        if not hasattr(self, "sctx"):
            global g_snap_widget
            g_snap_widget[0] = self

            context = bpy.context

            self.preferences = preferences = context.user_preferences.addons[__package__].preferences

            #Configure the unit of measure
            self.snap_to_grid = preferences.increments_grid
            self.incremental = bpy.utils.units.to_value(
                    context.scene.unit_settings.system, 'LENGTH', str(preferences.incremental))

            self.draw_cache = SnapDrawn(
                preferences.out_color,
                preferences.face_color,
                preferences.edge_color,
                preferences.vert_color,
                preferences.center_color,
                preferences.perpendicular_color,
                preferences.constrain_shift_color,
                (*context.user_preferences.themes[0].user_interface.axis_x, 1.0),
                (*context.user_preferences.themes[0].user_interface.axis_y, 1.0),
                (*context.user_preferences.themes[0].user_interface.axis_z, 1.0)
            )

            #Init Snap Context
            from .snap_context_l import SnapContext
            from mathutils import Vector

            self.sctx = SnapContext(context.region, context.space_data)
            self.sctx.set_pixel_dist(12)
            self.sctx.use_clip_planes(True)

            if preferences.outer_verts:
                for base in context.visible_bases:
                    self.sctx.add_obj(base.object, base.object.matrix_world)

            self.sctx.set_snap_mode(True, True, True)
            self.bm = None
            self.type = 'OUT'
            self.loc = Vector()

    def __del__(self):
        global g_snap_widget
        g_snap_widget[0] = None


class MousePointWidgetGroup(bpy.types.GizmoGroup):
    bl_idname = "MESH_GGT_mouse_point"
    bl_label = "Draw Mouse Point"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    def setup(self, context):
        snap_widget = self.gizmos.new(MousePointWidget.bl_idname)
        props = snap_widget.target_set_operator("mesh.make_line")
        props.wait_for_input = False


class VIEW3D_OT_rotate_custom_pivot(bpy.types.Operator):
    bl_idname = "view3d.rotate_custom_pivot"
    bl_label = "Rotate the view"
    bl_options = {'BLOCKING', 'GRAB_CURSOR'}

    pivot: bpy.props.FloatVectorProperty("Pivot", subtype='XYZ')
    g_up_axis: bpy.props.FloatVectorProperty("up_axis", default=(0.0, 0.0, 1.0), subtype='XYZ')
    sensitivity: bpy.props.FloatProperty("sensitivity", default=0.007)

    def modal(self, context, event):
        from mathutils import Matrix
        if event.value == 'PRESS' and event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            dx = self.init_coord[0] - event.mouse_region_x
            dy = self.init_coord[1] - event.mouse_region_y
            rot_ver = Matrix.Rotation(-dx * self.sensitivity, 3, self.g_up_axis)
            rot_hor = Matrix.Rotation(dy * self.sensitivity, 3, self.view_rot[0])
            rot_mat =  rot_hor @ rot_ver
            view_matrix = self.view_rot @ rot_mat

            pos = self.pos1 @ rot_mat + self.pivot
            qua = view_matrix.to_quaternion()
            qua.invert()

            self.rv3d.view_location = pos
            self.rv3d.view_rotation = qua

            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def invoke(self, context, event):
        self.rv3d = context.region_data
        self.init_coord = event.mouse_region_x, event.mouse_region_y
        self.pos1 = self.rv3d.view_location - self.pivot
        self.view_rot = self.rv3d.view_matrix.to_3x3()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class VIEW3D_OT_zoom_custom_target(bpy.types.Operator):
    bl_idname = "view3d.zoom_custom_target"
    bl_label = "Zoom the view"
    bl_options = {'BLOCKING', 'GRAB_CURSOR'}

    target: bpy.props.FloatVectorProperty("target", subtype='XYZ')
    delta: bpy.props.IntProperty("delta", default=0)
    step_factor = 0.333

    def modal(self, context, event):
        if event.value == 'PRESS' and event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            if not hasattr(self, "init_mouse_region_y"):
                self.init_mouse_region_y = event.mouse_region_y
                self.heigt_up = context.area.height - self.init_mouse_region_y
                self.rv3d.view_location = self.target

            fac = (event.mouse_region_y - self.init_mouse_region_y) / self.heigt_up
            ret = 'RUNNING_MODAL'
        else:
            fac = self.step_factor * self.delta
            ret = 'FINISHED'

        self.rv3d.view_location = self.init_loc + (self.target - self.init_loc) * fac
        self.rv3d.view_distance = self.init_dist - self.init_dist * fac

        context.area.tag_redraw()
        return {ret}

    def invoke(self, context, event):
        v3d = context.space_data
        dist_range = (v3d.clip_start, v3d.clip_end)
        self.rv3d = context.region_data
        self.init_dist = self.rv3d.view_distance
        if ((self.delta <= 0 and self.init_dist < dist_range[1]) or
            (self.delta >  0 and self.init_dist > dist_range[0])):
                self.init_loc = self.rv3d.view_location.copy()

                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}

        return {'FINISHED'}
