# <pep8-80 compliant>

# ##### BEGIN GPL LICENSE BLOCK #####
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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"


from ..utils.property_class_registry import PropertyClassRegistry

__all__ = [
    'MUV_Properties',
    'init_props',
    'clear_props',
]


# Properties used in this add-on.
# pylint: disable=W0612
class MUV_Properties():
    def __init__(self):
        self.prefs = MUV_Prefs()


class MUV_Prefs():
    expanded = {
        "info_desc": False,
        "info_loc": False,
        "conf_uvsculpt": False,
        "conf_uvinsp": False,
        "conf_texproj": False,
        "conf_uvbb": False
    }


def init_props(scene):
    scene.muv_props = MUV_Properties()
    PropertyClassRegistry.init_props(scene)


def clear_props(scene):
    PropertyClassRegistry.del_props(scene)
    del scene.muv_props
