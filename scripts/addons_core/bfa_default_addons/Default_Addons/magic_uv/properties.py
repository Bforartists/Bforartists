# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"


from .utils.property_class_registry import PropertyClassRegistry


# Properties used in this add-on.
# pylint: disable=W0612
class MUV_Properties():
    pass


def init_props(scene):
    scene.muv_props = MUV_Properties()
    PropertyClassRegistry.init_props(scene)


def clear_props(scene):
    PropertyClassRegistry.del_props(scene)
    del scene.muv_props
