# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

from typing import Optional
from ...io.com import gltf2_io_lights_punctual


def gather_light_spot(blender_lamp, export_settings) -> Optional[gltf2_io_lights_punctual.LightSpot]:

    if not __filter_light_spot(blender_lamp, export_settings):
        return None

    spot = gltf2_io_lights_punctual.LightSpot(
        inner_cone_angle=__gather_inner_cone_angle(blender_lamp, export_settings),
        outer_cone_angle=__gather_outer_cone_angle(blender_lamp, export_settings)
    )
    return spot


def __filter_light_spot(blender_lamp, _) -> bool:
    if blender_lamp.type != "SPOT":
        return False

    return True


def __gather_inner_cone_angle(blender_lamp, _) -> Optional[float]:
    angle = blender_lamp.spot_size * 0.5
    return angle - angle * blender_lamp.spot_blend


def __gather_outer_cone_angle(blender_lamp, _) -> Optional[float]:
    return blender_lamp.spot_size * 0.5
