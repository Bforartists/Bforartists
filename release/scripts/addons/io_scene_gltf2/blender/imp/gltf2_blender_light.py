# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

import bpy
from math import pi

from ..com.gltf2_blender_extras import set_extras
from io_scene_gltf2.io.imp.gltf2_io_user_extensions import import_user_extensions


class BlenderLight():
    """Blender Light."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def create(gltf, vnode, light_id):
        """Light creation."""
        pylight = gltf.data.extensions['KHR_lights_punctual']['lights'][light_id]

        import_user_extensions('gather_import_light_before_hook', gltf, vnode, pylight)

        if pylight['type'] == "directional":
            light = BlenderLight.create_directional(gltf, light_id)
        elif pylight['type'] == "point":
            light = BlenderLight.create_point(gltf, light_id)
        elif pylight['type'] == "spot":
            light = BlenderLight.create_spot(gltf, light_id)

        if 'color' in pylight.keys():
            light.color = pylight['color']

        if 'intensity' in pylight.keys():
            light.energy = pylight['intensity']

        # TODO range

        set_extras(light, pylight.get('extras'))

        return light

    @staticmethod
    def create_directional(gltf, light_id):
        pylight = gltf.data.extensions['KHR_lights_punctual']['lights'][light_id]

        if 'name' not in pylight.keys():
            pylight['name'] = "Sun"

        sun = bpy.data.lights.new(name=pylight['name'], type="SUN")
        return sun

    @staticmethod
    def create_point(gltf, light_id):
        pylight = gltf.data.extensions['KHR_lights_punctual']['lights'][light_id]

        if 'name' not in pylight.keys():
            pylight['name'] = "Point"

        point = bpy.data.lights.new(name=pylight['name'], type="POINT")
        return point

    @staticmethod
    def create_spot(gltf, light_id):
        pylight = gltf.data.extensions['KHR_lights_punctual']['lights'][light_id]

        if 'name' not in pylight.keys():
            pylight['name'] = "Spot"

        spot = bpy.data.lights.new(name=pylight['name'], type="SPOT")

        # Angles
        if 'spot' in pylight.keys() and 'outerConeAngle' in pylight['spot']:
            spot.spot_size = pylight['spot']['outerConeAngle'] * 2
        else:
            spot.spot_size = pi / 2

        if 'spot' in pylight.keys() and 'innerConeAngle' in pylight['spot']:
            spot.spot_blend = 1 - ( pylight['spot']['innerConeAngle'] / pylight['spot']['outerConeAngle'] )
        else:
            spot.spot_blend = 1.0

        return spot
