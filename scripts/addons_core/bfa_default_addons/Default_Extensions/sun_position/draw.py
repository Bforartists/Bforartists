# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import math
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .sun_calc import calc_surface, calc_analemma


if bpy.app.background:  # ignore drawing in background mode
    def north_update(self, context):
        pass
    def surface_update(self, context):
        pass
    def analemmas_update(self, context):
        pass
else:
    # North line

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

    def north_draw():
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
        sun_props = context.scene.sun_pos_properties
        addon_prefs = context.preferences.addons[__package__].preferences

        if addon_prefs.show_overlays and sun_props.show_north:
            if _north_handle is None:
                _north_handle = bpy.types.SpaceView3D.draw_handler_add(north_draw, (), 'WINDOW', 'POST_VIEW')
        elif _north_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_north_handle, 'WINDOW')
            _north_handle = None

    # Analemmas

    def analemmas_draw(batch, shader):
        shader.uniform_float("color", (1, 0, 0, 1))
        batch.draw(shader)

    _analemmas_handle = None

    def analemmas_update(self, context):
        global _analemmas_handle
        sun_props = context.scene.sun_pos_properties
        addon_prefs = context.preferences.addons[__package__].preferences

        if addon_prefs.show_overlays and sun_props.show_analemmas:
            coords = []
            indices = []
            coord_offset = 0
            for h in range(24):
                analemma_verts = calc_analemma(context, h)
                coords.extend(analemma_verts)
                for i in range(len(analemma_verts) - 1):
                    indices.append((coord_offset + i,
                                    coord_offset + i+1))
                coord_offset += len(analemma_verts)

            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINES',
                                    {"pos": coords}, indices=indices)

            if _analemmas_handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(_analemmas_handle, 'WINDOW')
            _analemmas_handle = bpy.types.SpaceView3D.draw_handler_add(
                analemmas_draw, (batch, shader), 'WINDOW', 'POST_VIEW')
        elif _analemmas_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_analemmas_handle, 'WINDOW')
            _analemmas_handle = None

    # Surface

    def surface_draw(batch, shader):
        blend = gpu.state.blend_get()
        gpu.state.blend_set("ALPHA")
        shader.uniform_float("color", (.8, .6, 0, 0.2))
        batch.draw(shader)
        gpu.state.blend_set(blend)

    _surface_handle = None

    def surface_update(self, context):
        global _surface_handle
        sun_props = context.scene.sun_pos_properties
        addon_prefs = context.preferences.addons[__package__].preferences

        if addon_prefs.show_overlays and sun_props.show_surface:
            coords = calc_surface(context)
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords})

            if _surface_handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(_surface_handle, 'WINDOW')
            _surface_handle = bpy.types.SpaceView3D.draw_handler_add(
                surface_draw, (batch, shader), 'WINDOW', 'POST_VIEW')
        elif _surface_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_surface_handle, 'WINDOW')
            _surface_handle = None
