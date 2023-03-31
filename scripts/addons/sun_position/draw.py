# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import math
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


if bpy.app.background:  # ignore north line in background mode
    def north_update(self, context):
        pass
else:
    shader_interface = gpu.types.GPUStageInterfaceInfo("my_interface")
    shader_interface.flat('VEC2', "v_StartPos")
    shader_interface.smooth('VEC4', "v_VertPos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant('MAT4', "u_ViewProjectionMatrix")
    shader_info.push_constant('VEC4', "u_Color")
    shader_info.push_constant('VEC2', "u_Resolution")
    shader_info.vertex_in(0, 'VEC3', "position")
    shader_info.vertex_out(shader_interface)

    shader_info.vertex_source(
        '''
        void main()
        {
            vec4 pos    = u_ViewProjectionMatrix * vec4(position, 1.0f);
            gl_Position = pos;
            v_StartPos    = (pos / pos.w).xy;
            v_VertPos     = pos;
        }
        '''
    )

    shader_info.fragment_out(0, 'VEC4', "FragColor")
    shader_info.fragment_source(
        '''
        void main()
        {
            vec4 vertPos_2d = v_VertPos / v_VertPos.w;
            vec2 dir  = (vertPos_2d.xy - v_StartPos.xy) * u_Resolution;
            float dist = length(dir);

            if (step(sin(dist / 5.0f), 0.0) == 1) discard;

            FragColor = u_Color;
        }
        '''
    )

    shader = gpu.shader.create_from_info(shader_info)
    del shader_info
    del shader_interface

    def draw_north_callback():
        """
        Set up the compass needle using the current north offset angle
        less 90 degrees.  This forces the unit circle to begin at the
        12 O'clock instead of 3 O'clock position.
        """
        sun_props = bpy.context.scene.sun_pos_properties

        color = (0.2, 0.6, 1.0, 0.7)
        radius = 100
        angle = -(sun_props.north_offset - math.pi / 2)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        coords = Vector((x, y, 0)), Vector((0, 0, 0))
        batch = batch_for_shader(shader, 'LINE_STRIP', {"position": coords})

        matrix = bpy.context.region_data.perspective_matrix
        shader.uniform_float("u_ViewProjectionMatrix", matrix)
        shader.uniform_float("u_Resolution", (bpy.context.region.width,
                                              bpy.context.region.height))
        shader.uniform_float("u_Color", color)
        width = gpu.state.line_width_get()
        gpu.state.line_width_set(2.0)
        batch.draw(shader)
        gpu.state.line_width_set(width)

    _north_handle = None

    def north_update(self, context):
        global _north_handle
        if self.show_north and _north_handle is None:
            _north_handle = bpy.types.SpaceView3D.draw_handler_add(draw_north_callback, (), 'WINDOW', 'POST_VIEW')
        elif _north_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_north_handle, 'WINDOW')
            _north_handle = None
