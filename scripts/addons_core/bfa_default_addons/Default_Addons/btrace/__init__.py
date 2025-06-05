# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


bl_info = {
    "name": "BTracer",
    "author": "liero, crazycourier, Atom, Meta-Androcto, MacKracken",
    "version": (1, 2, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Create Tab",
    "description": "Tools for converting/animating objects/particles into curves",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/btracer.html",
    "category": "Add Curve",
}

import bpy

# if "bpy" in locals():
#     import importlib
#     importlib.reload(bTrace_props)
#     importlib.reload(bTrace)
# else:
#     from . import bTrace_props
#     from . import bTrace
from . import bTrace_props
from . import bTrace

from bpy.types import AddonPreferences
from . bTrace_props import TracerProperties

from . bTrace import (
    OBJECT_OT_convertcurve,
    OBJECT_OT_objecttrace,
    OBJECT_OT_objectconnect,
    OBJECT_OT_writing,
    OBJECT_OT_particletrace,
    OBJECT_OT_traceallparticles,
    OBJECT_OT_curvegrow,
    OBJECT_OT_reset,
    OBJECT_OT_fcnoise,
    OBJECT_OT_meshfollow,
    OBJECT_OT_materialChango,
    OBJECT_OT_clearColorblender,
)

from . bTrace_panel import addTracerObjectPanel
from bpy.props import (
    EnumProperty,
    PointerProperty,
)


# Add-on Preferences
class btrace_preferences(AddonPreferences):
    bl_idname = __name__

    expand_enum: EnumProperty(
            name="UI Options",
            items=[
                 ('list', "Drop down list",
                  "Show all the items as dropdown list in the Tools Region"),
                 ('col', "Enable Expanded UI Panel",
                  "Show all the items expanded in the Tools Region in a column"),
                 ('row', "Icons only in a row",
                  "Show all the items as icons expanded in a row in the Tools Region")
                  ],
            description="",
            default='list'
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="UI Options:")

        row = layout.row(align=True)
        row.prop(self, "expand_enum", text="UI Options", expand=True)


# Define Classes to register
classes = (
    TracerProperties,
    addTracerObjectPanel,
    OBJECT_OT_convertcurve,
    OBJECT_OT_objecttrace,
    OBJECT_OT_objectconnect,
    OBJECT_OT_writing,
    OBJECT_OT_particletrace,
    OBJECT_OT_traceallparticles,
    OBJECT_OT_curvegrow,
    OBJECT_OT_reset,
    OBJECT_OT_fcnoise,
    OBJECT_OT_meshfollow,
    OBJECT_OT_materialChango,
    OBJECT_OT_clearColorblender,
    btrace_preferences
    )



# register, unregister = bpy.utils.register_classes_factory(classes)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.curve_tracer = PointerProperty(type=TracerProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.curve_tracer

# if __name__ == "__main__":
#     register()
