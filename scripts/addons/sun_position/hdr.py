# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# -*- coding: utf-8 -*-

import bpy
from bpy.props import FloatProperty, FloatVectorProperty
from bpy.app.translations import pgettext_iface as iface_
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from math import sqrt, pi, atan2, asin


if not bpy.app.background:  # ignore drawing in background mode
    image_shader = gpu.shader.from_builtin('IMAGE_COLOR')
    line_shader = gpu.shader.from_builtin('FLAT_COLOR')


def draw_callback_px(self, context):
    nt = context.scene.world.node_tree.nodes
    env_tex_node = nt.get(context.scene.sun_pos_properties.hdr_texture)
    image = env_tex_node.image
    texture = gpu.texture.from_image(image)

    if self.area != context.area:
        return

    bottom = 0
    top = context.area.height
    right = context.area.width

    position = Vector((right, top)) / 2 + self.offset
    scale = Vector((context.area.width, context.area.width / 2)) * self.scale

    coords = ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))
    uv_coords = ((0, 0), (1, 0), (1, 1), (0, 1))
    batch = batch_for_shader(image_shader, 'TRI_FAN',
                             {"pos": coords, "texCoord": uv_coords})

    with gpu.matrix.push_pop():
        gpu.matrix.translate(position)
        gpu.matrix.scale(scale)

        image_shader.bind()
        image_shader.uniform_sampler("image", texture)
        image_shader.uniform_float("color", (self.exposure, self.exposure, self.exposure, 1.0))
        batch.draw(image_shader)

    # Crosshair
    # vertical
    coords = ((self.mouse_position[0], bottom), (self.mouse_position[0], top))
    colors = ((1,) * 4,) * 2
    batch = batch_for_shader(line_shader, 'LINES',
                             {"pos": coords, "color": colors})
    line_shader.bind()
    batch.draw(line_shader)

    # horizontal
    if bottom <= self.mouse_position[1] <= top:
        coords = ((0, self.mouse_position[1]), (context.area.width, self.mouse_position[1]))
        batch = batch_for_shader(line_shader, 'LINES',
                                 {"pos": coords, "color": colors})
        line_shader.bind()
        batch.draw(line_shader)


class SUNPOS_OT_ShowHdr(bpy.types.Operator):
    """Select the location of the Sun in any 3D viewport and keep it in sync with the environment"""
    bl_idname = "world.sunpos_show_hdr"
    bl_label = "Pick Sun in Viewport"

    exposure: FloatProperty(name="Exposure", default=1.0)
    scale: FloatProperty(name="Scale", default=1.0)
    offset: FloatVectorProperty(name="Offset", default=(0.0, 0.0), size=2, subtype='COORDINATES')

    @classmethod
    def poll(self, context):
        sun_props = context.scene.sun_pos_properties
        if sun_props.sun_object is None:
            self.poll_message_set("Please select a Sun object")
            return False
        if not sun_props.hdr_texture:
            self.poll_message_set("Please select an Environment Texture node")
            return False

        nt = context.scene.world.node_tree.nodes
        env_tex_node = nt.get(context.scene.sun_pos_properties.hdr_texture)
        if env_tex_node is None or env_tex_node.type != "TEX_ENVIRONMENT":
            self.poll_message_set("Please select a valid Environment Texture node")
            return False
        return True

    def update(self, context, event):
        sun_props = context.scene.sun_pos_properties
        mouse_position_abs = Vector((event.mouse_x, event.mouse_y))

        # Get current area
        for area in context.screen.areas:
            # Compare absolute mouse position to area bounds
            if (area.x < mouse_position_abs.x < area.x + area.width
                    and area.y < mouse_position_abs.y < area.y + area.height):
                self.area = area
            if area.type == 'VIEW_3D':
                # Redraw all areas
                area.tag_redraw()

        if self.area.type == 'VIEW_3D':
            self.top = self.area.height
            self.right = self.area.width

            nt = context.scene.world.node_tree.nodes
            env_tex = nt.get(sun_props.hdr_texture)

            # Mouse position relative to window
            self.mouse_position = Vector((mouse_position_abs.x - self.area.x,
                                          mouse_position_abs.y - self.area.y))

            self.selected_point = (self.mouse_position
                                   - self.offset
                                   - Vector((self.right, self.top)) / 2) / self.scale
            u = self.selected_point.x / self.area.width + 0.5
            v = (self.selected_point.y) / (self.area.width / 2) + 0.5

            # Set elevation and azimuth from selected point
            if env_tex.projection == 'EQUIRECTANGULAR':
                el = v * pi - pi/2
                az = u * pi*2 - pi/2 + env_tex.texture_mapping.rotation.z

                # Clamp elevation
                el = max(el, -pi/2)
                el = min(el, pi/2)

                sun_props.hdr_elevation = el
                sun_props.hdr_azimuth = az
            elif env_tex.projection == 'MIRROR_BALL':
                # Formula from intern/cycles/kernel/kernel_projection.h
                # Point on sphere
                dir = Vector()

                # Normalize to -1, 1
                dir.x = 2.0 * u - 1.0
                dir.z = 2.0 * v - 1.0

                # Outside bounds
                if (dir.x * dir.x + dir.z * dir.z > 1.0):
                    dir = Vector()

                else:
                    dir.y = -sqrt(max(1.0 - dir.x * dir.x - dir.z * dir.z, 0.0))

                    # Reflection
                    i = Vector((0.0, -1.0, 0.0))

                    dir = 2.0 * dir.dot(i) * dir - i

                # Convert vector to euler
                el = asin(dir.z)
                az = atan2(dir.x, dir.y) + env_tex.texture_mapping.rotation.z
                sun_props.hdr_elevation = el
                sun_props.hdr_azimuth = az

            else:
                self.report({'ERROR'}, 'Unknown projection')
                return {'CANCELLED'}

    def pan(self, context, event):
        self.offset += Vector((event.mouse_region_x - self.mouse_prev_x,
                               event.mouse_region_y - self.mouse_prev_y))
        self.mouse_prev_x, self.mouse_prev_y = event.mouse_region_x, event.mouse_region_y

    def modal(self, context, event):
        self.area.tag_redraw()
        if event.type == 'MOUSEMOVE':
            if self.is_panning:
                self.pan(context, event)
            self.update(context, event)

        # Confirm
        elif event.type in {'LEFTMOUSE', 'RET'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            for area in context.screen.areas:
                area.tag_redraw()
            # Bind the environment texture to the sun
            context.scene.sun_pos_properties.bind_to_sun = True
            context.workspace.status_text_set(None)
            return {'FINISHED'}

        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            for area in context.screen.areas:
                area.tag_redraw()
            # Reset previous values
            context.scene.sun_pos_properties.hdr_elevation = self.initial_elevation
            context.scene.sun_pos_properties.hdr_azimuth = self.initial_azimuth
            context.workspace.status_text_set(None)
            return {'CANCELLED'}

        # Set exposure or zoom
        elif event.type == 'WHEELUPMOUSE':
            # Exposure
            if event.ctrl:
                self.exposure *= 1.1
            # Zoom
            else:
                self.scale *= 1.1
                self.offset -= (self.mouse_position - (Vector((self.right, self.top)) / 2 + self.offset)) / 10.0
                self.update(context, event)
        elif event.type == 'WHEELDOWNMOUSE':
            # Exposure
            if event.ctrl:
                self.exposure /= 1.1
            # Zoom
            else:
                self.scale /= 1.1
                self.offset += (self.mouse_position - (Vector((self.right, self.top)) / 2 + self.offset)) / 11.0
                self.update(context, event)

        # Toggle pan
        elif event.type == 'MIDDLEMOUSE':
            if event.value == 'PRESS':
                self.mouse_prev_x, self.mouse_prev_y = event.mouse_region_x, event.mouse_region_y
                self.is_panning = True
            elif event.value == 'RELEASE':
                self.is_panning = False

        else:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.is_panning = False
        self.mouse_prev_x = 0.0
        self.mouse_prev_y = 0.0

        # Get at least one 3D View
        area_3d = None
        for a in context.screen.areas:
            if a.type == 'VIEW_3D':
                area_3d = a
                break

        if area_3d is None:
            self.report({'ERROR'}, 'Could not find 3D View')
            return {'CANCELLED'}

        nt = context.scene.world.node_tree.nodes
        env_tex_node = nt.get(context.scene.sun_pos_properties.hdr_texture)
        if env_tex_node is None or env_tex_node.type != "TEX_ENVIRONMENT":
            self.report({'ERROR'}, 'Please select an Environment Texture node')
            return {'CANCELLED'}

        self.area = context.area

        self.mouse_position = event.mouse_region_x, event.mouse_region_y

        self.initial_elevation = context.scene.sun_pos_properties.hdr_elevation
        self.initial_azimuth = context.scene.sun_pos_properties.hdr_azimuth

        context.workspace.status_text_set(
            iface_("Enter/LMB: confirm, Esc/RMB: cancel, MMB: pan, "
                   "mouse wheel: zoom, Ctrl + mouse wheel: set exposure"))

        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL'
        )
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
