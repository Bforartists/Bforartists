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


class VIEW3D_OT_rotate_custom_pivot(bpy.types.Operator):
    bl_idname = "view3d.rotate_custom_pivot"
    bl_label = "Rotate the view"
    bl_options = {'BLOCKING', 'GRAB_CURSOR'}

    __slots__ = 'rv3d', 'init_coord', 'pos1', 'view_rot'

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

    __slots__ = 'rv3d', 'init_dist', 'delta', 'init_loc'

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
