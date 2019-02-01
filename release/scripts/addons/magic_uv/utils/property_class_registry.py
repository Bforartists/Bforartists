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
__version__ = "6.0"
__date__ = "26 Jan 2019"

from .. import common


class PropertyClassRegistry:
    class_list = []

    def __init__(self, *_, **kwargs):
        self.legacy = kwargs.get('legacy', False)

    def __call__(self, cls):
        PropertyClassRegistry.add_class(cls.idname, cls, self.legacy)
        return cls

    @classmethod
    def add_class(cls, idname, prop_class, legacy):
        for class_ in cls.class_list:
            if (class_["idname"] == idname) and (class_["legacy"] == legacy):
                raise RuntimeError("{} is already registered".format(idname))

        new_op = {
            "idname": idname,
            "class": prop_class,
            "legacy": legacy,
        }
        cls.class_list.append(new_op)
        common.debug_print("{} is registered.".format(idname))

    @classmethod
    def init_props(cls, scene):
        for class_ in cls.class_list:
            class_["class"].init_props(scene)
            common.debug_print("{} is initialized.".format(class_["idname"]))

    @classmethod
    def del_props(cls, scene):
        for class_ in cls.class_list:
            class_["class"].del_props(scene)
            common.debug_print("{} is cleared.".format(class_["idname"]))

    @classmethod
    def cleanup(cls):
        cls.class_list = []
        common.debug_print("Cleanup registry.")
