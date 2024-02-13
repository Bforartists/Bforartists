# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# my_operator.py
import bpy

op = bpy.types.Operator

################## Animation Operators ##################

class BFA_OT_insertframe_left(op):
    bl_idname = "anim.insertframe_left"
    bl_label = "Insert Frame Left"
    bl_description = "Inserts an empty frame and nudges all keyframes to the left of the time cursor"
    bl_icon = 'TRIA_LEFT'

    def execute(self, context):
        # Get the current frame
        current_frame = bpy.context.scene.frame_current

        # Get the active object
        obj = bpy.context.active_object

        # Check if the object has animation data
        if obj.animation_data and obj.animation_data.action:
            # Iterate over each fcurve in the action
            for fcurve in obj.animation_data.action.fcurves:
                # Iterate over each keyframe point in the fcurve
                for keyframe in fcurve.keyframe_points:
                    # If the keyframe is after the current frame
                    if keyframe.co.x < current_frame:
                        # Nudge the key frame one frame backward
                        keyframe.co.x -= 1

        # Check if the object is a grease pencil object
        if obj.type == 'GPENCIL':
            # Iterate over each layer in the grease pencil object
            for layer in obj.data.layers:
                # Iterate over each frame in the layer
                for frame in layer.frames:
                    # If the frame is after the current frame
                    if frame.frame_number < current_frame:
                        # Nudge the frame one frame backward
                        frame.frame_number -= 1

        # Update the scene
        bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertkeyframes:
            self.layout.operator(BFA_OT_insertframe_left.bl_idname, icon=BFA_OT_insertframe_left.bl_icon)


class BFA_OT_insertframe_right(op):
    bl_idname = "anim.insertframe_right"
    bl_label = "Insert Frame Right"
    bl_description = "Inserts an empty frame and nudges all keyframes to the right of the time cursor"
    bl_icon = 'TRIA_RIGHT'

    def execute(self, context):
        # Get the current frame
        current_frame = bpy.context.scene.frame_current

        # Get the active object
        obj = bpy.context.active_object

        # Check if the object has animation data
        if obj.animation_data and obj.animation_data.action:
            # Iterate over each fcurve in the action
            for fcurve in obj.animation_data.action.fcurves:
                # Iterate over each keyframe point in the fcurve
                for keyframe in fcurve.keyframe_points:
                    # If the keyframe is after the current frame
                    if keyframe.co.x > current_frame:
                        # Nudge the key frame one frame forward
                        keyframe.co.x += 1

        # Check if the object is a grease pencil object
        if obj.type == 'GPENCIL':
            # Iterate over each layer in the grease pencil object
            for layer in obj.data.layers:
                # Iterate over each frame in the layer
                for frame in layer.frames:
                    # If the frame is after the current frame
                    if frame.frame_number > current_frame:
                        # Nudge the frame one frame forward
                        frame.frame_number += 1

        # Update the scene
        bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertkeyframes:
            self.layout.operator(BFA_OT_insertframe_right.bl_idname, icon=BFA_OT_insertframe_right.bl_icon)
            self.layout.separator()



