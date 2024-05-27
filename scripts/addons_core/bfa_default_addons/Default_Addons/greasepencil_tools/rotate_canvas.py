# SPDX-FileCopyrightText: 2020-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from .prefs import get_addon_prefs

import bpy
import math
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from time import time
## draw utils
import gpu
import blf
from gpu_extras.batch import batch_for_shader

def step_value(value, step):
    '''return the step closer to the passed value'''
    abs_angle = abs(value)
    diff = abs_angle % step
    lower_step = abs_angle - diff
    higher_step = lower_step + step
    if abs_angle - lower_step < higher_step - abs_angle:
        return math.copysign(lower_step, value)
    else:
        return math.copysign(higher_step, value)

def draw_callback_px(self, context):
    # 50% alpha, 2 pixel width line
    if context.area != self.current_area:
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)

    # init
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [self.center, self.initial_pos]})#self.vector_initial
    shader.bind()
    shader.uniform_float("color", (0.5, 0.5, 0.8, 0.6))
    batch.draw(shader)

    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [self.center, self.pos_current]})
    shader.bind()
    shader.uniform_float("color", (0.3, 0.7, 0.2, 0.5))
    batch.draw(shader)

    ## debug lines
    # batch = batch_for_shader(shader, 'LINES', {"pos": [
    #     (0,0), (context.area.width, context.area.height),
    #     (context.area.width, 0), (0, context.area.height)
    #     ]})
    # shader.bind()
    # shader.uniform_float("color", (0.8, 0.1, 0.1, 0.5))
    # batch.draw(shader)

    # restore opengl defaults
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')

    ## text
    font_id = 0
    ## draw text debug infos
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20.0)
    blf.draw(font_id, f'angle: {math.degrees(self.angle):.1f}')


class RC_OT_RotateCanvas(bpy.types.Operator):
    bl_idname = 'view3d.rotate_canvas'
    bl_label = 'Rotate Canvas'
    bl_options = {"REGISTER"}

    def get_center_view(self, context, cam):
        '''
        https://blender.stackexchange.com/questions/6377/coordinates-of-corners-of-camera-view-border
        Thanks to ideasman42
        '''

        frame = cam.data.view_frame()
        mat = cam.matrix_world
        frame = [mat @ v for v in frame]
        frame_px = [location_3d_to_region_2d(context.region, context.space_data.region_3d, v) for v in frame]
        center_x = frame_px[2].x + (frame_px[0].x - frame_px[2].x)/2
        center_y = frame_px[1].y + (frame_px[0].y - frame_px[1].y)/2

        return mathutils.Vector((center_x, center_y))

    def set_cam_view_offset_from_angle(self, context, angle):
        '''apply inverse of the rotation on view offset in cam rotate from view center'''
        neg = -angle
        rot_mat2d = mathutils.Matrix([[math.cos(neg), -math.sin(neg)], [math.sin(neg), math.cos(neg)]])

        # scale_mat = mathutils.Matrix([[1.0, 0.0], [0.0, self.ratio]])
        new_cam_offset = self.view_cam_offset.copy()

        ## area deformation correction
        new_cam_offset = mathutils.Vector((new_cam_offset[0], new_cam_offset[1] * self.ratio))

        ## rotate by matrix
        new_cam_offset.rotate(rot_mat2d)

        ## area deformation restore
        new_cam_offset = mathutils.Vector((new_cam_offset[0], new_cam_offset[1] * self.ratio_inv))

        context.space_data.region_3d.view_camera_offset = new_cam_offset

    def execute(self, context):
        if self.hud:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.tag_redraw()
        if self.in_cam:
            self.cam.rotation_mode = self.org_rotation_mode
            # Undo step is only needed if used within camera
            bpy.ops.ed.undo_push(message='Rotate Canvas')
        return {'FINISHED'}


    def modal(self, context, event):
        if event.type in {'MOUSEMOVE'}:#,'INBETWEEN_MOUSEMOVE'
            # Get current mouse coordination (region)
            self.pos_current = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
            # Get current vector
            self.vector_current = (self.pos_current - self.center).normalized()
            # Calculates the angle between initial and current vectors
            self.angle = self.vector_initial.angle_signed(self.vector_current)#radian
            # print (math.degrees(self.angle), self.vector_initial, self.vector_current)


            ## handle snap key
            snap = False
            if self.snap_ctrl and event.ctrl:
                snap = True
            if self.snap_shift and event.shift:
                snap = True
            if self.snap_alt and event.alt:
                snap = True
            ## Snapping to specific degrees angle
            if snap:
                self.angle = step_value(self.angle, self.snap_step)

            if self.in_cam:
                self.cam.matrix_world = self.cam_matrix
                self.cam.rotation_euler.rotate_axis("Z", self.angle)

                if self.use_view_center:
                    ## apply inverse rotation on view offset
                    self.set_cam_view_offset_from_angle(context, self.angle)

            else: # free view
                context.space_data.region_3d.view_rotation = self._rotation
                rot = context.space_data.region_3d.view_rotation
                rot = rot.to_euler()
                rot.rotate_axis("Z", self.angle)
                context.space_data.region_3d.view_rotation = rot.to_quaternion()

        if event.type in {'RIGHTMOUSE', 'LEFTMOUSE', 'MIDDLEMOUSE'} and event.value == 'RELEASE':
            # Trigger reset : Less than 150ms and less than 2 degrees move
            if time() - self.timer < 0.15 and abs(math.degrees(self.angle)) < 2:
                # self.report({'INFO'}, 'Reset')
                aim = context.space_data.region_3d.view_rotation @ mathutils.Vector((0.0, 0.0, 1.0)) # view vector
                z_up_quat = aim.to_track_quat('Z','Y') # track Z, up Y
                if self.in_cam:

                    q = self.cam.matrix_world.to_quaternion() # store current rotation

                    if self.cam.parent:
                        q = self.cam.parent.matrix_world.inverted().to_quaternion() @ q
                        cam_quat = self.cam.parent.matrix_world.inverted().to_quaternion() @ z_up_quat
                    else:
                        cam_quat = z_up_quat
                    self.cam.rotation_euler = cam_quat.to_euler('XYZ')

                    # get diff angle (might be better way to get view axis rot diff)
                    diff_angle = q.rotation_difference(cam_quat).to_euler('ZXY').z
                    # print('diff_angle: ', math.degrees(diff_angle))
                    self.set_cam_view_offset_from_angle(context, diff_angle)

                else:
                    context.space_data.region_3d.view_rotation = z_up_quat
            self.execute(context)
            return {'FINISHED'}

        if event.type == 'ESC':#Cancel
            self.execute(context)
            if self.in_cam:
                self.cam.matrix_world = self.cam_matrix
                context.space_data.region_3d.view_camera_offset = self.view_cam_offset
            else:
                context.space_data.region_3d.view_rotation = self._rotation
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.current_area = context.area
        prefs = get_addon_prefs()
        self.hud = prefs.canvas_use_hud
        self.use_view_center = prefs.canvas_use_view_center
        self.angle = 0.0
        ## Check if scene camera or local camera exists ?
        # if (context.space_data.use_local_camera and context.space_data.camera) or context.scene.camera
        self.in_cam = context.region_data.view_perspective == 'CAMERA'

        ## store ratio for view rotate correction

        # CORRECT UI OVERLAP FROM HEADER TOOLBAR
        regs = context.area.regions
        if context.preferences.system.use_region_overlap:
            w = context.area.width
            # minus tool header
            h = context.area.height - regs[0].height
        else:
            # minus tool leftbar + sidebar right
            w = context.area.width - regs[2].width - regs[3].width
            # minus tool header + header
            h = context.area.height - regs[0].height - regs[1].height

        self.ratio = h / w
        self.ratio_inv = w / h

        if self.in_cam:
            # Get camera from scene
            if context.space_data.use_local_camera and context.space_data.camera:
                self.cam = context.space_data.camera
            else:
                self.cam = context.scene.camera

            #return if one element is locked (else bypass location)
            if self.cam.lock_rotation[:] != (False, False, False):
                self.report({'WARNING'}, 'Camera rotation is locked')
                return {'CANCELLED'}

            if self.use_view_center:
                self.center = mathutils.Vector((w/2, h/2))
            else:
                self.center = self.get_center_view(context, self.cam)

            # store original rotation mode
            self.org_rotation_mode = self.cam.rotation_mode
            # set to euler to works with quaternions, restored at finish
            self.cam.rotation_mode = 'XYZ'
            # store camera matrix world
            self.cam_matrix = self.cam.matrix_world.copy()
            # self.cam_init_euler = self.cam.rotation_euler.copy()

            ## initialize current view_offset in camera
            self.view_cam_offset = mathutils.Vector(context.space_data.region_3d.view_camera_offset)

        else:
            self.center = mathutils.Vector((w/2, h/2))
            # self.center = mathutils.Vector((context.area.width/2, context.area.height/2))

            # store current rotation
            self._rotation = context.space_data.region_3d.view_rotation.copy()

        # Get current mouse coordination
        self.pos_current = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        self.initial_pos = self.pos_current# for draw debug, else no need
        # Calculate initial vector
        self.vector_initial = self.pos_current - self.center
        self.vector_initial.normalize()

        # Initializes the current vector with the same initial vector.
        self.vector_current = self.vector_initial.copy()


        #Snap keys
        self.snap_ctrl = not prefs.use_ctrl
        self.snap_shift = not prefs.use_shift
        self.snap_alt = not prefs.use_alt
        # round to closer degree and convert back to radians
        self.snap_step = math.radians(round(math.degrees(prefs.rc_angle_step)))

        self.timer = time()
        args = (self, context)
        if self.hud:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


## -- Set / Reset rotation buttons

class RC_OT_Set_rotation(bpy.types.Operator):
    bl_idname = 'view3d.rotate_canvas_set'
    bl_label = 'Save Rotation'
    bl_description = 'Save active camera rotation (per camera property)'
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' \
            and context.space_data.region_3d.view_perspective == 'CAMERA'

    def execute(self, context):
        cam_ob = context.scene.camera
        cam_ob['stored_rotation'] = cam_ob.rotation_euler
        if not cam_ob.get('_RNA_UI'):
            cam_ob['_RNA_UI'] = {}
            cam_ob['_RNA_UI']["stored_rotation"] = {
                    "description":"Stored camera rotation (Gpencil tools > rotate canvas operator)",
                    "subtype":'EULER',
                    # "is_overridable_library":0,
                    }

        return {'FINISHED'}

class RC_OT_Reset_rotation(bpy.types.Operator):
    bl_idname = 'view3d.rotate_canvas_reset'
    bl_label = 'Restore Rotation'
    bl_description = 'Restore active camera rotation from previously saved state'
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' \
            and context.space_data.region_3d.view_perspective == 'CAMERA' \
            and context.scene.camera.get('stored_rotation')

    def execute(self, context):
        cam_ob = context.scene.camera
        cam_ob.rotation_euler = cam_ob['stored_rotation']
        return {'FINISHED'}


### --- REGISTER

classes = (
    RC_OT_RotateCanvas,
    RC_OT_Set_rotation,
    RC_OT_Reset_rotation,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
