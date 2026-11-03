# SPDX-FileCopyrightText: 2011-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Demo Mode",
    "author": "Campbell Barton",
    "blender": (2, 80, 0),
    "location": "File > Demo Menu",
    "description": "Demo mode lets you select multiple blend files and loop over them.",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/system/demo_mode.html",
    "support": 'OFFICIAL',
    "category": "System",
}

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    import importlib
    if "config" in locals():
        importlib.reload(config)


import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
)

DEMO_CFG = "demo.py"


class DemoModeSetup(bpy.types.Operator):
    """Create a demo script and optionally execute it"""
    bl_idname = "wm.demo_mode_setup"
    bl_label = "Demo Mode (Setup)"
    bl_options = {'PRESET'}

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    # these are used to create the file list.
    directory: StringProperty(
        name="Search Path",
        description="Directory used for importing the file",
        maxlen=1024,
        subtype='DIR_PATH',
    )
    random_order: BoolProperty(
        name="Random Order",
        description="Select files randomly",
        default=False,
    )
    mode: EnumProperty(
        name="Method",
        items=(
            ('AUTO', "Auto", ""),
            ('PLAY', "Play", ""),
            ('RENDER', "Render", ""),
        )
    )

    run: BoolProperty(
        name="Run Immediately!",
        description="Run demo immediately",
        default=True,
    )
    exit: BoolProperty(
        name="Exit",
        description="Run once and exit",
        default=False,
    )

    # these are mapped directly to the config!
    #
    # anim
    # ====
    anim_cycles: IntProperty(
        name="Cycles",
        description="Number of times to play the animation",
        min=1, max=1000,
        default=2,
    )
    anim_time_min: FloatProperty(
        name="Time Min",
        description="Minimum number of seconds to show the animation for "
                    "(for small loops)",
        min=0.0, max=1000.0,
        soft_min=1.0, soft_max=1000.0,
        default=4.0,
    )
    anim_time_max: FloatProperty(
        name="Time Max",
        description="Maximum number of seconds to show the animation for "
                    "(in case the end frame is very high for no reason)",
        min=0.0, max=100000000.0,
        soft_min=1.0, soft_max=100000000.0,
        default=8.0,
    )
    anim_screen_switch: FloatProperty(
        name="Screen Switch",
        description="Time between switching screens (in seconds) "
                    "or 0 to disable",
        min=0.0, max=100000000.0,
        soft_min=1.0, soft_max=60.0,
        default=0.0,
    )
    #
    # render
    # ======
    display_render: FloatProperty(
        name="Render Delay",
        description="Time to display the rendered image before moving on "
                    "(in seconds)",
        min=0.0, max=60.0,
        default=4.0,
    )
    anim_render: BoolProperty(
        name="Render Anim",
        description="Render entire animation (render mode only)",
        default=False,
    )

    def execute(self, context):
        from . import config

        keywords = self.as_keywords(ignore=("directory", "random_order", "run", "exit"))
        cfg_str, cfg_file_count, _dirpath = config.as_string(
            self.directory,
            self.random_order,
            self.exit,
            **keywords,
        )
        text = bpy.data.texts.get(DEMO_CFG)
        if text:
            text.name += ".back"

        text = bpy.data.texts.new(DEMO_CFG)
        text.from_string(cfg_str)

        # When run is disabled, no messages makes it seems as if nothing happened.
        self.report({'INFO'}, "Demo text \"%s\" created with %s file(s)" % (DEMO_CFG, "{:,d}".format(cfg_file_count)))

        if self.run:
            extern_demo_mode_run()

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def check(self, context):
        return True  # lazy

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Search *.blend recursively")
        box.label(text="Writes: %s config text" % DEMO_CFG)

        layout.prop(self, "run")
        layout.prop(self, "exit")

        layout.label(text="Generate Settings:")
        row = layout.row()
        row.prop(self, "mode", expand=True)
        layout.prop(self, "random_order")

        mode = self.mode

        layout.separator()
        sub = layout.column()
        sub.active = (mode in {'AUTO', 'PLAY'})
        sub.label(text="Animate Settings:")
        sub.prop(self, "anim_cycles")
        sub.prop(self, "anim_time_min")
        sub.prop(self, "anim_time_max")
        sub.prop(self, "anim_screen_switch")

        layout.separator()
        sub = layout.column()
        sub.active = (mode in {'AUTO', 'RENDER'})
        sub.label(text="Render Settings:")
        sub.prop(self, "display_render")


class DemoModeRun(bpy.types.Operator):
    bl_idname = "wm.demo_mode_run"
    bl_label = "Demo Mode (Start)"

    def execute(self, context):
        if extern_demo_mode_run():
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Can't load %s config, run: File -> Demo Mode (Setup)" % DEMO_CFG)
            return {'CANCELLED'}


# --- call demo_mode.py funcs
def extern_demo_mode_run():
    # this accesses demo_mode.py which is kept standalone
    # and can be run direct.
    from . import demo_mode
    if demo_mode.load_config():
        demo_mode.demo_mode_load_file()  # kick starts the modal operator
        return True
    else:
        return False


def extern_demo_mode_register():
    # this accesses demo_mode.py which is kept standalone
    # and can be run direct.
    from . import demo_mode
    demo_mode.register()


def extern_demo_mode_unregister():
    # this accesses demo_mode.py which is kept standalone
    # and can be run direct.
    from . import demo_mode
    demo_mode.unregister()

# --- integration


def menu_func(self, context):
    layout = self.layout
    layout.operator(DemoModeSetup.bl_idname, icon='PREFERENCES')
    layout.operator(DemoModeRun.bl_idname, icon='PLAY')
    layout.separator()


classes = (
    DemoModeSetup,
    DemoModeRun,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.TOPBAR_MT_file.prepend(menu_func)

    extern_demo_mode_register()


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    bpy.types.TOPBAR_MT_file.remove(menu_func)

    extern_demo_mode_unregister()


if __name__ == "__main__":
    register()
