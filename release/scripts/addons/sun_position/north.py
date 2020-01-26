### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bgl
import math
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


if bpy.app.background:  # ignore north line in background mode
    def north_update(self, context):
        pass
else:
    vertex_shader = '''
        uniform mat4 u_ViewProjectionMatrix;

        in vec3 position;

        flat out vec2 v_StartPos;
        out vec4 v_VertPos;

        void main()
        {
            vec4 pos    = u_ViewProjectionMatrix * vec4(position, 1.0f);
            gl_Position = pos;
            v_StartPos    = (pos / pos.w).xy;
            v_VertPos     = pos;
        }
    '''

    fragment_shader = '''
        uniform vec4 u_Color;

        flat in vec2 v_StartPos;
        in vec4 v_VertPos;
        out vec4 FragColor;

        uniform vec2 u_Resolution;

        void main()
        {
            vec4 vertPos_2d = v_VertPos / v_VertPos.w;
            vec2 dir  = (vertPos_2d.xy - v_StartPos.xy) * u_Resolution;
            float dist = length(dir);

            if (step(sin(dist / 5.0f), 0.0) == 1) discard;

            FragColor = u_Color;
        }
    '''

    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)

    def draw_north_callback():
        # ------------------------------------------------------------------
        # Set up the compass needle using the current north offset angle
        # less 90 degrees.  This forces the unit circle to begin at the
        # 12 O'clock instead of 3 O'clock position.
        # ------------------------------------------------------------------
        sun_props = bpy.context.scene.sun_pos_properties

        color = (0.2, 0.6, 1.0, 0.7)
        radius = 100
        angle = -(sun_props.north_offset - math.pi / 2)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius

        coords = Vector((x, y, 0)), Vector((0, 0, 0))   # Start & end of needle

        batch = batch_for_shader(
            shader, 'LINE_STRIP',
            {"position": coords},
        )
        shader.bind()

        matrix = bpy.context.region_data.perspective_matrix
        shader.uniform_float("u_ViewProjectionMatrix", matrix)
        shader.uniform_float("u_Resolution", (bpy.context.region.width, bpy.context.region.height))
        shader.uniform_float("u_Color", color)
        bgl.glLineWidth(2.0)
        batch.draw(shader)


    _handle = None


    def north_update(self, context):
        global _handle
        if self.show_north and _handle is None:
            _handle = bpy.types.SpaceView3D.draw_handler_add(draw_north_callback, (), 'WINDOW', 'POST_VIEW')
        elif _handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
            _handle = None
        context.area.tag_redraw()
