# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

bl_info = {
    "name": "UI Animation Render",
    "author": "Luca Rood",
    "description": "Render animations of the Blender UI.",
    "blender": (2, 80, 0),
    "version": (0, 1, 0),
    "location": "View3D > Sidebar > View Tab and Ctrl+Shift+F12",
    "warning": "",
    "category": "Render"
}

km = None


def draw_ui(prefs, layout):
    layout.prop(prefs, "delay")

    col = layout.column(align=True)
    col.label(text="Animation Highlight:")

    row = col.row()
    row.prop(prefs, "anim_highlight", expand=True)

    if prefs.anim_highlight == "replace":
        split = col.split(factor=0.2)
        split.label(text="Color")
        row = split.row(align=True)
        row.prop(prefs, "highlight_color", text="")
        row.prop(prefs, "highlight_blend", text="Blend")


class UIAnimationRenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    delay: bpy.props.FloatProperty(
        name="Capture Delay",
        description="How much time to wait (seconds) before capturing each frame, to allow the viewport to clean up",
        default=0.5
    )

    anim_highlight: bpy.props.EnumProperty(
        name="Animation Highlight",
        description="What to do with the animated field highlight color",
        items=[("keep", "Keep", "Keep the animated field highlight", 0),
               ("hide", "Hide", "Hide the animated field highlight", 1),
               ("replace", "Replace", "Replace the animated field highlight", 2)],
        default="keep"
    )

    highlight_color: bpy.props.FloatVectorProperty(
        name="Highlight Color",
        description="Color to use for animated field highlights",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0)
    )

    highlight_blend: bpy.props.FloatProperty(
        name="Highlight Blend",
        description="How much the highlight color influences the field color",
        default=0.5
    )

    def draw(self, context):
        draw_ui(self, self.layout)


class RenderScreen(bpy.types.Operator):
    bl_idname = "render.render_screen"
    bl_label = "Render Screen"
    bl_description = "Capture the screen for each animation frame and write to the render output path"

    _timer = None
    _f_initial = 1
    _theme_blend = 0.0
    _theme_key = (0, 0, 0)
    _theme_key_sel = (0, 0, 0)
    _theme_anim = (0, 0, 0)
    _theme_anim_sel = (0, 0, 0)
    _theme_driven = (0, 0, 0)
    _theme_driven_sel = (0, 0, 0)

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.stop(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            scene = context.scene
            f_curr = scene.frame_current

            bpy.ops.screen.screenshot(filepath=context.scene.render.frame_path(frame=f_curr))

            if f_curr < scene.frame_end:
                scene.frame_set(f_curr + 1)
            else:
                self.stop(context)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        # Adjust animation highlight (theme)
        prefs = context.preferences
        addon_prefs = prefs.addons[__name__].preferences
        theme = prefs.themes[0].user_interface.wcol_state

        if addon_prefs.anim_highlight == "hide":
            self._theme_blend = theme.blend
            theme.blend = 0.0
        elif addon_prefs.anim_highlight == "replace":
            self._theme_blend = theme.blend
            self._theme_key = theme.inner_key.copy()
            self._theme_key_sel = theme.inner_key_sel.copy()
            self._theme_anim = theme.inner_anim.copy()
            self._theme_anim_sel = theme.inner_anim_sel.copy()
            self._theme_driven = theme.inner_driven.copy()
            self._theme_driven_sel = theme.inner_driven_sel.copy()

            theme.blend = addon_prefs.highlight_blend
            theme.inner_key = addon_prefs.highlight_color
            theme.inner_key_sel = addon_prefs.highlight_color
            theme.inner_anim = addon_prefs.highlight_color
            theme.inner_anim_sel = addon_prefs.highlight_color
            theme.inner_driven = addon_prefs.highlight_color
            theme.inner_driven_sel = addon_prefs.highlight_color

        # Set frame
        scene = context.scene
        self._f_initial = scene.frame_current
        scene.frame_set(scene.frame_start)

        # Start timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(addon_prefs.delay, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def stop(self, context):
        # Stop timer
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        # Reset frame
        context.scene.frame_set(self._f_initial)

        # Reset theme
        prefs = context.preferences
        addon_prefs = prefs.addons[__name__].preferences
        theme = prefs.themes[0].user_interface.wcol_state

        if addon_prefs.anim_highlight == "hide":
            theme.blend = self._theme_blend
        elif addon_prefs.anim_highlight == "replace":
            theme.blend = self._theme_blend
            theme.inner_key = self._theme_key
            theme.inner_key_sel = self._theme_key_sel
            theme.inner_anim = self._theme_anim
            theme.inner_anim_sel = self._theme_anim_sel
            theme.inner_driven = self._theme_driven
            theme.inner_driven_sel = self._theme_driven_sel


class VIEW3D_PT_ui_animation_render(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "UI Animation Render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        prefs = context.preferences
        addon_prefs = prefs.addons[__name__].preferences

        layout.operator(RenderScreen.bl_idname)
        draw_ui(addon_prefs, layout)


def register():
    global km

    bpy.utils.register_class(UIAnimationRenderPreferences)
    bpy.utils.register_class(RenderScreen)
    bpy.utils.register_class(VIEW3D_PT_ui_animation_render)

    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Screen', space_type='EMPTY')
        km.keymap_items.new('render.render_screen', 'F12', 'PRESS', shift=True, ctrl=True)


def unregister():
    global km

    bpy.utils.unregister_class(UIAnimationRenderPreferences)
    bpy.utils.unregister_class(RenderScreen)
    bpy.utils.unregister_class(VIEW3D_PT_ui_animation_render)

    if km is not None:
        wm = bpy.context.window_manager
        wm.keyconfigs.addon.keymaps.remove(km)
        km = None
