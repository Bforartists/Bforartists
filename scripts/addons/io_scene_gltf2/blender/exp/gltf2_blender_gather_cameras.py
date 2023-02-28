# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from ..com.gltf2_blender_extras import generate_extras
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions

import bpy
import math


@cached
def gather_camera(blender_camera, export_settings):
    if not __filter_camera(blender_camera, export_settings):
        return None

    camera = gltf2_io.Camera(
        extensions=__gather_extensions(blender_camera, export_settings),
        extras=__gather_extras(blender_camera, export_settings),
        name=__gather_name(blender_camera, export_settings),
        orthographic=__gather_orthographic(blender_camera, export_settings),
        perspective=__gather_perspective(blender_camera, export_settings),
        type=__gather_type(blender_camera, export_settings)
    )

    export_user_extensions('gather_camera_hook', export_settings, camera, blender_camera)

    return camera


def __filter_camera(blender_camera, export_settings):
    return bool(__gather_type(blender_camera, export_settings))


def __gather_extensions(blender_camera, export_settings):
    return None


def __gather_extras(blender_camera, export_settings):
    if export_settings['gltf_extras']:
        return generate_extras(blender_camera)
    return None


def __gather_name(blender_camera, export_settings):
    return blender_camera.name


def __gather_orthographic(blender_camera, export_settings):
    if __gather_type(blender_camera, export_settings) == "orthographic":
        orthographic = gltf2_io.CameraOrthographic(
            extensions=None,
            extras=None,
            xmag=None,
            ymag=None,
            zfar=None,
            znear=None
        )

        _render = bpy.context.scene.render
        scene_x = _render.resolution_x * _render.pixel_aspect_x
        scene_y = _render.resolution_y * _render.pixel_aspect_y
        scene_square = max(scene_x, scene_y)
        del _render

        # `Camera().ortho_scale` (and also FOV FTR) maps to the maximum of either image width or image height— This is the box that gets shown from camera view with the checkbox `.show_sensor = True`.

        orthographic.xmag = blender_camera.ortho_scale * (scene_x / scene_square) / 2
        orthographic.ymag = blender_camera.ortho_scale * (scene_y / scene_square) / 2

        orthographic.znear = blender_camera.clip_start
        orthographic.zfar = blender_camera.clip_end

        return orthographic
    return None


def __gather_perspective(blender_camera, export_settings):
    if __gather_type(blender_camera, export_settings) == "perspective":
        perspective = gltf2_io.CameraPerspective(
            aspect_ratio=None,
            extensions=None,
            extras=None,
            yfov=None,
            zfar=None,
            znear=None
        )

        _render = bpy.context.scene.render
        width = _render.pixel_aspect_x * _render.resolution_x
        height = _render.pixel_aspect_y * _render.resolution_y
        perspective.aspect_ratio = width / height
        del _render

        if width >= height:
            if blender_camera.sensor_fit != 'VERTICAL':
                perspective.yfov = 2.0 * math.atan(math.tan(blender_camera.angle * 0.5) / perspective.aspect_ratio)
            else:
                perspective.yfov = blender_camera.angle
        else:
            if blender_camera.sensor_fit != 'HORIZONTAL':
                perspective.yfov = blender_camera.angle
            else:
                perspective.yfov = 2.0 * math.atan(math.tan(blender_camera.angle * 0.5) / perspective.aspect_ratio)

        perspective.znear = blender_camera.clip_start
        perspective.zfar = blender_camera.clip_end

        return perspective
    return None


def __gather_type(blender_camera, export_settings):
    if blender_camera.type == 'PERSP':
        return "perspective"
    elif blender_camera.type == 'ORTHO':
        return "orthographic"
    return None
