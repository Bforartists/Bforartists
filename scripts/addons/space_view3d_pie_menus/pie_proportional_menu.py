# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'Shift O'",
    "description": "Proportional Object/Edit Tools",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "3D View Object & Edit modes",
    "warning": "",
    "doc_url": "",
    "category": "Proportional Edit Pie"
}

import bpy
from bpy.types import (
    Menu,
    Operator,
)


# Proportional Edit Object
class PIE_OT_ProportionalEditObj(Operator):
    bl_idname = "proportional_obj.active"
    bl_label = "Proportional Edit Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings

        if ts.use_proportional_edit_objects is True:
            ts.use_proportional_edit_objects = False

        elif ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True

        return {'FINISHED'}


class PIE_OT_ProportionalSmoothObj(Operator):
    bl_idname = "proportional_obj.smooth"
    bl_label = "Proportional Smooth Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'SMOOTH'

        if ts.proportional_edit_falloff != 'SMOOTH':
            ts.proportional_edit_falloff = 'SMOOTH'
        return {'FINISHED'}


class PIE_OT_ProportionalSphereObj(Operator):
    bl_idname = "proportional_obj.sphere"
    bl_label = "Proportional Sphere Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'SPHERE'

        if ts.proportional_edit_falloff != 'SPHERE':
            ts.proportional_edit_falloff = 'SPHERE'
        return {'FINISHED'}


class PIE_OT_ProportionalRootObj(Operator):
    bl_idname = "proportional_obj.root"
    bl_label = "Proportional Root Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'ROOT'

        if ts.proportional_edit_falloff != 'ROOT':
            ts.proportional_edit_falloff = 'ROOT'
        return {'FINISHED'}


class PIE_OT_ProportionalSharpObj(Operator):
    bl_idname = "proportional_obj.sharp"
    bl_label = "Proportional Sharp Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'SHARP'

        if ts.proportional_edit_falloff != 'SHARP':
            ts.proportional_edit_falloff = 'SHARP'
        return {'FINISHED'}


class PIE_OT_ProportionalLinearObj(Operator):
    bl_idname = "proportional_obj.linear"
    bl_label = "Proportional Linear Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'LINEAR'

        if ts.proportional_edit_falloff != 'LINEAR':
            ts.proportional_edit_falloff = 'LINEAR'
        return {'FINISHED'}


class PIE_OT_ProportionalConstantObj(Operator):
    bl_idname = "proportional_obj.constant"
    bl_label = "Proportional Constant Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'CONSTANT'

        if ts.proportional_edit_falloff != 'CONSTANT':
            ts.proportional_edit_falloff = 'CONSTANT'
        return {'FINISHED'}


class PIE_OT_ProportionalRandomObj(Operator):
    bl_idname = "proportional_obj.random"
    bl_label = "Proportional Random Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'RANDOM'

        if ts.proportional_edit_falloff != 'RANDOM':
            ts.proportional_edit_falloff = 'RANDOM'
        return {'FINISHED'}


class PIE_OT_ProportionalInverseSquareObj(Operator):
    bl_idname = "proportional_obj.inversesquare"
    bl_label = "Proportional Random Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        if ts.use_proportional_edit_objects is False:
            ts.use_proportional_edit_objects = True
            ts.proportional_edit_falloff = 'INVERSE_SQUARE'

        if ts.proportional_edit_falloff != 'INVERSE_SQUARE':
            ts.proportional_edit_falloff = 'INVERSE_SQUARE'
        return {'FINISHED'}


# Proportional Edit Edit Mode
class PIE_OT_ProportionalEditEdt(Operator):
    bl_idname = "proportional_edt.active"
    bl_label = "Proportional Edit EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit ^= 1
        return {'FINISHED'}


class PIE_OT_ProportionalConnectedEdt(Operator):
    bl_idname = "proportional_edt.connected"
    bl_label = "Proportional Connected EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_connected ^= 1
        return {'FINISHED'}


class PIE_OT_ProportionalProjectedEdt(Operator):
    bl_idname = "proportional_edt.projected"
    bl_label = "Proportional projected EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_projected ^= 1
        return {'FINISHED'}


class PIE_OT_ProportionalSmoothEdt(Operator):
    bl_idname = "proportional_edt.smooth"
    bl_label = "Proportional Smooth EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'SMOOTH'
        return {'FINISHED'}


class PIE_OT_ProportionalSphereEdt(Operator):
    bl_idname = "proportional_edt.sphere"
    bl_label = "Proportional Sphere EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'SPHERE'
        return {'FINISHED'}


class PIE_OT_ProportionalRootEdt(Operator):
    bl_idname = "proportional_edt.root"
    bl_label = "Proportional Root EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'ROOT'
        return {'FINISHED'}


class PIE_OT_ProportionalSharpEdt(Operator):
    bl_idname = "proportional_edt.sharp"
    bl_label = "Proportional Sharp EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'SHARP'
        return {'FINISHED'}


class PIE_OT_ProportionalLinearEdt(Operator):
    bl_idname = "proportional_edt.linear"
    bl_label = "Proportional Linear EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'LINEAR'
        return {'FINISHED'}


class PIE_OT_ProportionalConstantEdt(Operator):
    bl_idname = "proportional_edt.constant"
    bl_label = "Proportional Constant EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'CONSTANT'
        return {'FINISHED'}


class PIE_OT_ProportionalRandomEdt(Operator):
    bl_idname = "proportional_edt.random"
    bl_label = "Proportional Random EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'RANDOM'
        return {'FINISHED'}


class PIE_OT_ProportionalInverseSquareEdt(Operator):
    bl_idname = "proportional_edt.inversesquare"
    bl_label = "Proportional Inverese Square EditMode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings
        ts.use_proportional_edit = True
        ts.proportional_edit_falloff = 'INVERSE_SQUARE'
        return {'FINISHED'}


# Pie ProportionalEditObj - O
class PIE_MT_ProportionalObj(Menu):
    bl_idname = "PIE_MT_proportional_obj"
    bl_label = "Pie Proportional Obj"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("proportional_obj.smooth", text="Smooth", icon='SMOOTHCURVE')
        # 6 - RIGHT
        pie.operator("proportional_obj.sphere", text="Sphere", icon='SPHERECURVE')
        # 2 - BOTTOM
        pie.operator("proportional_obj.linear", text="Linear", icon='LINCURVE')
        # 8 - TOP
        pie.prop(context.tool_settings, "use_proportional_edit_objects", text="Proportional On/Off")
        # 7 - TOP - LEFT
        pie.operator("proportional_obj.root", text="Root", icon='ROOTCURVE')
        # 9 - TOP - RIGHT
        pie.operator("proportional_obj.inversesquare", text="Inverse Square", icon='INVERSESQUARECURVE')
        # 1 - BOTTOM - LEFT
        pie.operator("proportional_obj.sharp", text="Sharp", icon='SHARPCURVE')
        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_proportional_moreob", text="More", icon='LINCURVE')


# Pie ProportionalEditEdt - O
class PIE_MT_ProportionalEdt(Menu):
    bl_idname = "PIE_MT_proportional_edt"
    bl_label = "Pie Proportional Edit"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("proportional_edt.smooth", text="Smooth", icon='SMOOTHCURVE')
        # 6 - RIGHT
        pie.operator("proportional_edt.sphere", text="Sphere", icon='SPHERECURVE')
        # 2 - BOTTOM
        pie.operator("proportional_edt.inversesquare", text="Inverse Square", icon='INVERSESQUARECURVE')
        # 8 - TOP
        pie.operator("proportional_edt.active", text="Proportional On/Off", icon='PROP_ON')
        # 7 - TOP - LEFT
        pie.operator("proportional_edt.connected", text="Connected", icon='PROP_CON')
        # 9 - TOP - RIGHT
        pie.operator("proportional_edt.projected", text="Projected", icon='PROP_PROJECTED')
        # 1 - BOTTOM - LEFT
        pie.operator("proportional_edt.root", text="Root", icon='ROOTCURVE')
        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_proportional_more", text="More", icon='LINCURVE')


# Pie ProportionalEditEdt - O
class PIE_MT_ProportionalMore(Menu):
    bl_idname = "PIE_MT_proportional_more"
    bl_label = "Pie Proportional More"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("proportional_edt.sharp", text="Sharp", icon='SHARPCURVE')
        box.operator("proportional_edt.linear", text="Linear", icon='LINCURVE')
        box.operator("proportional_edt.constant", text="Constant", icon='NOCURVE')
        box.operator("proportional_edt.random", text="Random", icon='RNDCURVE')


# Pie ProportionalEditEdt2
class PIE_MT_proportionalmoreob(Menu):
    bl_idname = "PIE_MT_proportional_moreob"
    bl_label = "Pie Proportional More"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("proportional_obj.constant", text="Constant", icon='NOCURVE')
        box.operator("proportional_obj.random", text="Random", icon='RNDCURVE')


classes = (
    PIE_OT_ProportionalEditObj,
    PIE_OT_ProportionalSmoothObj,
    PIE_OT_ProportionalSphereObj,
    PIE_OT_ProportionalRootObj,
    PIE_OT_ProportionalSharpObj,
    PIE_OT_ProportionalLinearObj,
    PIE_OT_ProportionalConstantObj,
    PIE_OT_ProportionalRandomObj,
    PIE_OT_ProportionalInverseSquareObj,
    PIE_OT_ProportionalEditEdt,
    PIE_OT_ProportionalConnectedEdt,
    PIE_OT_ProportionalProjectedEdt,
    PIE_OT_ProportionalSmoothEdt,
    PIE_OT_ProportionalSphereEdt,
    PIE_OT_ProportionalRootEdt,
    PIE_OT_ProportionalSharpEdt,
    PIE_OT_ProportionalLinearEdt,
    PIE_OT_ProportionalConstantEdt,
    PIE_OT_ProportionalRandomEdt,
    PIE_OT_ProportionalInverseSquareEdt,
    PIE_MT_ProportionalObj,
    PIE_MT_ProportionalEdt,
    PIE_MT_ProportionalMore,
    PIE_MT_proportionalmoreob
)

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # ProportionalEditObj
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'O', 'PRESS', shift=True)
        kmi.properties.name = "PIE_MT_proportional_obj"
        addon_keymaps.append((km, kmi))

        # ProportionalEditEdt
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'O', 'PRESS', shift=True)
        kmi.properties.name = "PIE_MT_proportional_edt"
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
