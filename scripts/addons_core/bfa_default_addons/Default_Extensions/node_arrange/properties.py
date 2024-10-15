# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.props import IntVectorProperty, PointerProperty
from bpy.types import PropertyGroup, Scene
from bpy.utils import register_class, unregister_class


class NA_PG_Settings(PropertyGroup):
    margin: IntVectorProperty(
      name="Spacing",
      description="Space between nodes",
      default=(70, 70),
      min=0,
      options=set(),
      subtype='XYZ',
      size=2,
    )


classes = [NA_PG_Settings]


def register() -> None:
    for cls in classes:
        register_class(cls)

    Scene.na_settings = PointerProperty(type=NA_PG_Settings)


def unregister() -> None:
    for cls in reversed(classes):
        if cls.is_registered:
            unregister_class(cls)

    del Scene.na_settings
