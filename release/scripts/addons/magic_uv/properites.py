# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8-80 compliant>

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.5"
__date__ = "6 Mar 2021"


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
