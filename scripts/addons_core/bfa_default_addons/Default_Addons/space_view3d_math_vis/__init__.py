# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Math Vis (Console)",
    "author": "Campbell Barton",
    "version": (0, 2, 2),
    "blender": (3, 0, 0),
    "location": "Properties: Scene > Math Vis Console and Python Console: Menu",
    "description": "Display console defined mathutils variables in the 3D view",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/3d_view/math_vis_console.html",
    "support": "OFFICIAL",
    "category": "3D View",
}


if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(draw)
else:
    from . import utils
    from . import draw

import bpy
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
    UIList,
)
from bpy.props import (
    StringProperty,
    BoolProperty,
    BoolVectorProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    CollectionProperty,
)


class PanelConsoleVars(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_label = "Math Vis Console"
    bl_idname = "MATHVIS_PT_panel_console_vars"
    bl_category = "Math Vis"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        state_props = wm.MathVisStatePropList

        if len(state_props) == 0:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="No vars to display")
        else:
            layout.template_list(
                MathVisVarList.bl_idname,
                'MathVisStatePropList',
                bpy.context.window_manager,
                'MathVisStatePropList',
                bpy.context.window_manager.MathVisProp,
                'index',
                rows=10
            )
        col = layout.column()
        mvp = wm.MathVisProp
        col.prop(mvp, "name_hide")
        col.prop(mvp, "bbox_hide")
        col.prop(mvp, "in_front")
        col.prop(mvp, "bbox_scale")
        col.operator("mathvis.cleanup_console")


class DeleteVar(Operator):
    bl_idname = "mathvis.delete_var"
    bl_label = "Delete Var"
    bl_description = "Remove the variable from the Console"
    bl_options = {'REGISTER'}

    key: StringProperty(name="Key")

    def execute(self, context):
        locals = utils.console_namespace()
        utils.VarStates.delete(self.key)
        del locals[self.key]
        draw.tag_redraw_areas()
        return {'FINISHED'}


class ToggleDisplay(Operator):
    bl_idname = "mathvis.toggle_display"
    bl_label = "Hide/Unhide"
    bl_description = "Change the display state of the var"
    bl_options = {'REGISTER'}

    key: StringProperty(name="Key")

    def execute(self, context):
        utils.VarStates.toggle_display_state(self.key)
        draw.tag_redraw_areas()
        return {'FINISHED'}


class ToggleLock(Operator):
    bl_idname = "mathvis.toggle_lock"
    bl_label = "Lock/Unlock"
    bl_description = "Lock the var from being deleted"
    bl_options = {'REGISTER'}

    key: StringProperty(name="Key")

    def execute(self, context):
        utils.VarStates.toggle_lock_state(self.key)
        draw.tag_redraw_areas()
        return {'FINISHED'}


class ToggleMatrixBBoxDisplay(Operator):
    bl_idname = "mathvis.show_bbox"
    bl_label = "Show BBox"
    bl_description = "Show/Hide the BBox of Matrix items"
    bl_options = {'REGISTER'}

    def execute(self, context):
        utils.VarStates.toggle_show_bbox()
        draw.tag_redraw_areas()
        return {'FINISHED'}


class CleanupConsole(Operator):
    bl_idname = "mathvis.cleanup_console"
    bl_label = "Cleanup Math Vis Console"
    bl_description = "Remove all visualized variables from the Console"
    bl_options = {'REGISTER'}

    def execute(self, context):
        utils.cleanup_math_data()
        draw.tag_redraw_areas()
        return {'FINISHED'}


def menu_func_cleanup(self, context):
    self.layout.operator("mathvis.cleanup_console", text="Clear Math Vis")


def console_hook():
    utils.VarStates.store_states()
    draw.tag_redraw_areas()
    context = bpy.context
    for window in context.window_manager.windows:
        window.screen.areas.update()


def call_console_hook(self, context):
    console_hook()


class MathVisStateProp(PropertyGroup):
    ktype: StringProperty()
    state: BoolVectorProperty(default=(False, False), size=2)


class MathVisVarList(UIList):
    bl_idname = "MATHVIS_UL_MathVisVarList"

    def draw_item(self,
                  context,
                  layout,
                  data,
                  item,
                  icon,
                  active_data,
                  active_propname
                  ):

        col = layout.column()
        key = item.name
        ktype = item.ktype
        is_visible = item.state[0]
        is_locked = item.state[1]

        row = col.row(align=True)
        row.label(text='%s - %s' % (key, ktype))

        icon = 'RESTRICT_VIEW_OFF' if is_visible else 'RESTRICT_VIEW_ON'
        prop = row.operator("mathvis.toggle_display", text='', icon=icon, emboss=False)
        prop.key = key

        icon = 'LOCKED' if is_locked else 'UNLOCKED'
        prop = row.operator("mathvis.toggle_lock", text='', icon=icon, emboss=False)
        prop.key = key

        if is_locked:
            row.label(text='', icon='BLANK1')
        else:
            prop = row.operator("mathvis.delete_var", text='', icon='X', emboss=False)
            prop.key = key


class MathVis(PropertyGroup):

    index: IntProperty(
        name="index"
    )
    bbox_hide: BoolProperty(
        name="Hide BBoxes",
        default=False,
        description="Hide the bounding boxes rendered for Matrix like items",
        update=call_console_hook
    )
    name_hide: BoolProperty(
        name="Hide Names",
        default=False,
        description="Hide the names of the rendered items",
        update=call_console_hook
    )
    bbox_scale: FloatProperty(
        name="Scale factor",
        min=0, default=1,
        description="Resize the Bounding Box and the coordinate "
        "lines for the display of Matrix items"
    )

    in_front: BoolProperty(
        name="Always In Front",
        default=True,
        description="Draw Points and lines always in front",
        update=call_console_hook
    )


classes = (
    PanelConsoleVars,
    DeleteVar,
    ToggleDisplay,
    ToggleLock,
    ToggleMatrixBBoxDisplay,
    CleanupConsole,
    MathVisStateProp,
    MathVisVarList,
    MathVis,
)


def register():
    from bpy.utils import register_class

    draw.callback_enable()

    import console_python
    console_python.execute.hooks.append((console_hook, ()))
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.MathVisProp = PointerProperty(type=MathVis)
    bpy.types.WindowManager.MathVisStatePropList = CollectionProperty(type=MathVisStateProp)
    bpy.types.CONSOLE_MT_console.prepend(menu_func_cleanup)


def unregister():
    from bpy.utils import unregister_class

    draw.callback_disable()

    import console_python
    console_python.execute.hooks.remove((console_hook, ()))
    bpy.types.CONSOLE_MT_console.remove(menu_func_cleanup)
    del bpy.types.WindowManager.MathVisProp
    del bpy.types.WindowManager.MathVisStatePropList

    for cls in classes:
        unregister_class(cls)
