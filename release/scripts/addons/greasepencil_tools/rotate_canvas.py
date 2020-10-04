from .prefs import get_addon_prefs

import bpy
import math
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy.props import BoolProperty, EnumProperty
## draw utils
import gpu
import bgl
import blf
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d


def draw_callback_px(self, context):
    # 50% alpha, 2 pixel width line
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(2)

    # init
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [self.center, self.initial_pos]})#self.vector_initial
    shader.bind()
    shader.uniform_float("color", (0.5, 0.5, 0.8, 0.6))
    batch.draw(shader)

    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [self.center, self.pos_current]})
    shader.bind()
    shader.uniform_float("color", (0.3, 0.7, 0.2, 0.5))
    batch.draw(shader)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)

    ## text
    font_id = 0
    ## draw text debug infos
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20, 72)
    blf.draw(font_id, f'angle: {math.degrees(self.angle):.1f}')


class RC_OT_RotateCanvas(bpy.types.Operator):
    bl_idname = 'view3d.rotate_canvas'
    bl_label = 'Rotate Canvas'
    bl_options = {"REGISTER", "UNDO"}

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

    def execute(self, context):
        if self.hud:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.tag_redraw()
        if self.in_cam:
                self.cam.rotation_mode = self.org_rotation_mode
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE','INBETWEEN_MOUSEMOVE'}:
            # Get current mouse coordination (region)
            self.pos_current = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
            # Get current vector
            self.vector_current = (self.pos_current - self.center).normalized()
            # Calculates the angle between initial and current vectors
            self.angle = self.vector_initial.angle_signed(self.vector_current)#radian
            # print (math.degrees(self.angle), self.vector_initial, self.vector_current)

            if self.in_cam:
                self.cam.matrix_world = self.cam_matrix
                self.cam.rotation_euler.rotate_axis("Z", self.angle)
            
            else:#free view
                context.space_data.region_3d.view_rotation = self._rotation
                rot = context.space_data.region_3d.view_rotation
                rot = rot.to_euler()
                rot.rotate_axis("Z", self.angle)
                context.space_data.region_3d.view_rotation = rot.to_quaternion()
        
        if event.type in {'RIGHTMOUSE', 'LEFTMOUSE', 'MIDDLEMOUSE'} and event.value == 'RELEASE':
            if not self.angle:
                # self.report({'INFO'}, 'Reset')
                aim = context.space_data.region_3d.view_rotation @ mathutils.Vector((0.0, 0.0, 1.0))#view vector
                context.space_data.region_3d.view_rotation = aim.to_track_quat('Z','Y')#track Z, up Y
            self.execute(context)
            return {'FINISHED'}
        
        if event.type == 'ESC':#Cancel
            self.execute(context)
            if self.in_cam:
                self.cam.matrix_world = self.cam_matrix
            else:
                context.space_data.region_3d.view_rotation = self._rotation
            return {'CANCELLED'}


        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.hud = get_addon_prefs().canvas_use_hud
        self.angle = 0.0
        self.in_cam = context.region_data.view_perspective == 'CAMERA'

        if self.in_cam:
            # Get camera from scene
            self.cam = bpy.context.scene.camera
            
            #return if one element is locked (else bypass location)
            if self.cam.lock_rotation[:] != (False, False, False):
                self.report({'WARNING'}, 'Camera rotation is locked') 
                return {'CANCELLED'}

            self.center = self.get_center_view(context, self.cam)
            # store original rotation mode
            self.org_rotation_mode = self.cam.rotation_mode
            # set to euler to works with quaternions, restored at finish
            self.cam.rotation_mode = 'XYZ'
            # store camera matrix world
            self.cam_matrix = self.cam.matrix_world.copy()
            # self.cam_init_euler = self.cam.rotation_euler.copy()

        else:
            self.center = mathutils.Vector((context.area.width/2, context.area.height/2))
            
            # store current rotation
            self._rotation = context.space_data.region_3d.view_rotation.copy()

        # Get current mouse coordination
        self.pos_current = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
        
        self.initial_pos = self.pos_current# for draw debug, else no need
        # Calculate inital vector
        self.vector_initial = self.pos_current - self.center
        self.vector_initial.normalize()
        
        # Initializes the current vector with the same initial vector.
        self.vector_current = self.vector_initial.copy()
        
        args = (self, context)
        if self.hud:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


### --- REGISTER

def register():
    bpy.utils.register_class(RC_OT_RotateCanvas)


def unregister():
    bpy.utils.unregister_class(RC_OT_RotateCanvas)

# if __name__ == "__main__":
#     register()