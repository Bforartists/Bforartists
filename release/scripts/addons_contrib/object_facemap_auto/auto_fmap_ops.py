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

# <pep8 compliant>

import bpy
from bpy.types import (
    Operator,
)
from bpy.props import (
    EnumProperty,
)

from . import USE_RELOAD


class MyFaceMapClear(Operator):
    """Clear face-map transform"""
    bl_idname = "my_facemap.transform_clear"
    bl_label = "My Face Map Clear Transform"
    bl_options = {'REGISTER', 'UNDO'}

    clear_types = EnumProperty(
        name="Clear Types",
        options={'ENUM_FLAG'},
        items=(
            ('LOCATION', "Location", ""),
            ('ROTATION', "Rotation", ""),
            ('SCALE', "Scale", ""),
        ),
        description="Clear transform",
        # default=set(),
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, _event):
        self._group = context.manipulator_group
        return self.execute(context)

    def execute(self, context):
        # trick since redo wont have manipulator_group
        group = self._group

        from .auto_fmap_utils import import_reload_or_none
        auto_fmap_widgets_xform = import_reload_or_none(
            __package__ + "." + "auto_fmap_widgets_xform", reload=USE_RELOAD,
        )

        if auto_fmap_widgets_xform is None:
            return {'CANCELED'}

        for mpr in group.manipulators:
            ob = mpr.fmap_mesh_object
            fmap_target = mpr.fmap_target
            fmap = mpr.fmap

            if mpr.select:
                if 'LOCATION' in self.clear_types:
                    auto_fmap_widgets_xform.widget_clear_location(
                        context, mpr, ob, fmap, fmap_target,
                    )
                if 'ROTATION' in self.clear_types:
                    auto_fmap_widgets_xform.widget_clear_rotation(
                        context, mpr, ob, fmap, fmap_target,
                    )
                if 'SCALE' in self.clear_types:
                    auto_fmap_widgets_xform.widget_clear_scale(
                        context, mpr, ob, fmap, fmap_target,
                    )
        return {'FINISHED'}


classes = (
    MyFaceMapClear,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
