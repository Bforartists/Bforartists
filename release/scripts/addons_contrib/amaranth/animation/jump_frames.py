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
"""
Jump X Frames on Shift Up/Down

When you hit Shift Up/Down, you'll jump 10 frames forward/backwards.
Sometimes is nice to tweak that value.

In the User Preferences, Editing tab, you'll find a "Frames to Jump"
slider where you can adjust how many frames you'd like to move
forwards/backwards.

Make sure you save your user settings if you want to use this value from
now on.

Find it on the User Preferences, Editing.
"""

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

KEYMAPS = list()


# FUNCTION: Check if object has keyframes for a specific frame
def is_keyframe(ob, frame):
    if ob is not None and ob.animation_data is not None and ob.animation_data.action is not None:
        for fcu in ob.animation_data.action.fcurves:
            if frame in (p.co.x for p in fcu.keyframe_points):
                return True
    return False


# monkey path is_keyframe function
bpy.types.Object.is_keyframe = is_keyframe


# FEATURE: Jump to frame in-between next and previous keyframe
class AMTH_SCREEN_OT_keyframe_jump_inbetween(Operator):
    """Jump to half in-between keyframes"""
    bl_idname = "screen.amth_keyframe_jump_inbetween"
    bl_label = "Jump to Keyframe In-between"

    backwards = BoolProperty()

    def execute(self, context):
        back = self.backwards

        scene = context.scene
        ob = bpy.context.object
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        if not context.scene.get("amth_keyframes_jump"):
            context.scene["amth_keyframes_jump"] = list()

        keyframes_list = context.scene["amth_keyframes_jump"]

        for f in range(frame_start, frame_end):
            if ob.is_keyframe(f):
                keyframes_list = list(keyframes_list)
                keyframes_list.append(f)

        if keyframes_list:
            keyframes_list_half = []

            for i, item in enumerate(keyframes_list):
                try:
                    next_item = keyframes_list[i + 1]
                    keyframes_list_half.append(int((item + next_item) / 2))
                except:
                    pass

            if len(keyframes_list_half) > 1:
                if back:
                    v = (scene.frame_current == keyframes_list_half[::-1][-1],
                         scene.frame_current < keyframes_list_half[::-1][-1])
                    if any(v):
                        self.report({"INFO"}, "No keyframes behind")
                    else:
                        for i in keyframes_list_half[::-1]:
                            if scene.frame_current > i:
                                scene.frame_current = i
                                break
                else:
                    v = (scene.frame_current == keyframes_list_half[-1],
                         scene.frame_current > keyframes_list_half[-1])
                    if any(v):
                        self.report({"INFO"}, "No keyframes ahead")
                    else:
                        for i in keyframes_list_half:
                            if scene.frame_current < i:
                                scene.frame_current = i
                                break
            else:
                self.report({"INFO"}, "Object has only 1 keyframe")
        else:
            self.report({"INFO"}, "Object has no keyframes")

        return {"FINISHED"}


# FEATURE: Jump forward/backward every N frames
class AMTH_SCREEN_OT_frame_jump(Operator):
    """Jump a number of frames forward/backwards"""
    bl_idname = "screen.amaranth_frame_jump"
    bl_label = "Jump Frames"

    forward = BoolProperty(default=True)

    def execute(self, context):
        scene = context.scene

        get_addon = "amaranth" in context.user_preferences.addons.keys()
        if not get_addon:
            return {"CANCELLED"}

        preferences = context.user_preferences.addons["amaranth"].preferences

        if preferences.use_framerate:
            framedelta = scene.render.fps
        else:
            framedelta = preferences.frames_jump
        if self.forward:
            scene.frame_current = scene.frame_current + framedelta
        else:
            scene.frame_current = scene.frame_current - framedelta

        return {"FINISHED"}


def ui_userpreferences_edit(self, context):
    get_addon = "amaranth" in context.user_preferences.addons.keys()
    if not get_addon:
        return

    preferences = context.user_preferences.addons["amaranth"].preferences

    col = self.layout.column()
    split = col.split(percentage=0.21)
    split.prop(preferences, "frames_jump",
               text="Frames to Jump")


def label(self, context):
    get_addon = "amaranth" in context.user_preferences.addons.keys()
    if not get_addon:
        return

    layout = self.layout

    if context.user_preferences.addons["amaranth"].preferences.use_timeline_extra_info:
        row = layout.row(align=True)

        row.operator(AMTH_SCREEN_OT_keyframe_jump_inbetween.bl_idname,
                     icon="PREV_KEYFRAME", text="").backwards = True
        row.operator(AMTH_SCREEN_OT_keyframe_jump_inbetween.bl_idname,
                     icon="NEXT_KEYFRAME", text="").backwards = False


def register():
    bpy.utils.register_class(AMTH_SCREEN_OT_frame_jump)
    bpy.utils.register_class(AMTH_SCREEN_OT_keyframe_jump_inbetween)
    bpy.types.USERPREF_PT_edit.append(ui_userpreferences_edit)
    bpy.types.USERPREF_PT_edit.append(label)

    # register keyboard shortcuts
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new(name="Frames")
    kmi = km.keymap_items.new('screen.amth_keyframe_jump_inbetween', 'UP_ARROW', 'PRESS', shift=True, ctrl=True)
    kmi.properties.backwards = False
    KEYMAPS.append((km, kmi))

    kmi = km.keymap_items.new('screen.amth_keyframe_jump_inbetween', 'DOWN_ARROW', 'PRESS', shift=True, ctrl=True)
    kmi.properties.backwards = True
    KEYMAPS.append((km, kmi))

    kmi = km.keymap_items.new(
        "screen.amaranth_frame_jump", "UP_ARROW", "PRESS", shift=True)
    kmi.properties.forward = True
    KEYMAPS.append((km, kmi))

    kmi = km.keymap_items.new(
        "screen.amaranth_frame_jump", "DOWN_ARROW", "PRESS", shift=True)
    kmi.properties.forward = False
    KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(AMTH_SCREEN_OT_frame_jump)
    bpy.utils.unregister_class(AMTH_SCREEN_OT_keyframe_jump_inbetween)
    bpy.types.USERPREF_PT_edit.remove(ui_userpreferences_edit)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()
