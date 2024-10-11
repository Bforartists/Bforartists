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

import bpy

op = bpy.types.Operator

################## Animation Operators ##################

class BFA_OT_insertframe_left(op):
    bl_idname = "anim.insertframe_left"
    bl_label = "Insert Frame Left"
    bl_description = "Inserts an empty frame and nudges all frames to the left of the timeline cursor"
    bl_icon = 'TRIA_LEFT'

    def execute(self, context):
        # Get the current frame
        current_frame = bpy.context.scene.frame_current

        # Get all selected objects
        selected_objects = bpy.context.selected_objects

        # Iterate over each selected object
        for obj in selected_objects:
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
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            self.layout.operator(BFA_OT_insertframe_left.bl_idname, icon=BFA_OT_insertframe_left.bl_icon)


class BFA_OT_insertframe_right(op):
    bl_idname = "anim.insertframe_right"
    bl_label = "Insert Frame Right"
    bl_description = "Inserts an empty frame and nudges all frames to the right of the timeline cursor"
    bl_icon = 'TRIA_RIGHT'

    def execute(self, context):
        # Get the current frame
        current_frame = bpy.context.scene.frame_current

        # Get all selected objects
        selected_objects = bpy.context.selected_objects

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                # Iterate over each fcurve in the action
                for fcurve in obj.animation_data.action.fcurves:
                    # Iterate over each keyframe point in the fcurve
                    for keyframe in fcurve.keyframe_points:
                        # If the keyframe is after the current frame
                        if keyframe.co.x > current_frame:
                            # Nudge the key frame one frame backward
                            keyframe.co.x += 1

            # Check if the object is a grease pencil object
            if obj.type == 'GPENCIL':
                # Iterate over each layer in the grease pencil object
                for layer in obj.data.layers:
                    # Iterate over each frame in the layer
                    for frame in layer.frames:
                        # If the frame is after the current frame
                        if frame.frame_number > current_frame:
                            # Nudge the frame one frame backward
                            frame.frame_number += 1

        # Update the scene
        bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            self.layout.operator(BFA_OT_insertframe_right.bl_idname, icon=BFA_OT_insertframe_right.bl_icon)


class BFA_OT_removeframe_left(op):
    bl_idname = "anim.removeframe_left"
    bl_label = "Remove Frame Left"
    bl_description = "Removes a frame and nudges all frames on the left towards the timeline cursor"
    bl_icon = 'PANEL_CLOSE'

    def execute(self, context):
        # Get the current frame
        current_frame = bpy.context.scene.frame_current

        # Get all selected objects
        selected_objects = bpy.context.selected_objects

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                # Iterate over each fcurve in the action
                for fcurve in obj.animation_data.action.fcurves:
                    # Iterate over each keyframe point in the fcurve
                    for keyframe in fcurve.keyframe_points:
                        # If the keyframe is on the current frame
                        if keyframe.co.x == current_frame:
                            # Delete the keyframe
                            fcurve.keyframe_points.remove(keyframe)
                        # If the keyframe is to the right of the current frame
                        elif keyframe.co.x < current_frame:
                            # Nudge the key frame one frame backward
                            keyframe.co.x += 1

        # Check if the object is a grease pencil object
        if obj.type == 'GPENCIL':
            # Iterate over each layer in the grease pencil object
            for layer in obj.data.layers:
                # Create a list of frames to remove
                frames_to_remove = []
                # Iterate over each frame in the layer
                for frame in layer.frames:
                    # If the frame is on the current frame
                    if frame.frame_number == current_frame:
                        # Add the frame to the list of frames to remove
                        frames_to_remove.append(frame)
                    # If the frame is to the right of the current frame
                    elif frame.frame_number < current_frame:
                        # Nudge the frame one frame backwards
                        frame.frame_number += 1
                # Remove the frames at the current frame
                for frame in frames_to_remove:
                    layer.frames.remove(frame)

        # Update the scene
        bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}


    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            self.layout.operator(BFA_OT_removeframe_left.bl_idname, icon=BFA_OT_removeframe_left.bl_icon)


class BFA_OT_removeframe_right(op):
    bl_idname = "anim.removeframe_right"
    bl_label = "Remove Frame Right"
    bl_description = "Removes a frame and nudges all frames on the right towards the timeline cursor"
    bl_icon = 'PANEL_CLOSE'

    def execute(self, context):
        # Get the current frame
        current_frame = bpy.context.scene.frame_current

        # Get all selected objects
        selected_objects = bpy.context.selected_objects

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                # Iterate over each fcurve in the action
                for fcurve in obj.animation_data.action.fcurves:
                    # Iterate over each keyframe point in the fcurve
                    for keyframe in fcurve.keyframe_points:
                        # If the keyframe is on the current frame
                        if keyframe.co.x == current_frame:
                            # Delete the keyframe
                            fcurve.keyframe_points.remove(keyframe)
                        # If the keyframe is to the right of the current frame
                        elif keyframe.co.x > current_frame:
                            # Nudge the key frame one frame backward
                            keyframe.co.x -= 1

        # Check if the object is a grease pencil object
        if obj.type == 'GPENCIL':
            # Iterate over each layer in the grease pencil object
            for layer in obj.data.layers:
                # Create a list of frames to remove
                frames_to_remove = []
                # Iterate over each frame in the layer
                for frame in layer.frames:
                    # If the frame is on the current frame
                    if frame.frame_number == current_frame:
                        # Add the frame to the list of frames to remove
                        frames_to_remove.append(frame)
                    # If the frame is to the right of the current frame
                    elif frame.frame_number > current_frame:
                        # Nudge the frame one frame backwards
                        frame.frame_number -= 1
                # Remove the frames at the current frame
                for frame in frames_to_remove:
                    layer.frames.remove(frame)

        # Update the scene
        bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}


    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            self.layout.operator(BFA_OT_removeframe_right.bl_idname, icon=BFA_OT_removeframe_right.bl_icon)


class BFA_OT_jump_forward(op):
    bl_idname = "anim.jump_forward"
    bl_label = "Frame Jump Forward"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.frame_current += context.scene.frameskip
        return {'FINISHED'}


class BFA_OT_jump_back(op):
    bl_idname = "anim.jump_back"
    bl_label = "Frame Jump Back"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.frame_current -= context.scene.frameskip
        return {'FINISHED'}


################## Viewport Operators ##################

# Store the previous settings in a dictionary
previous_viewport_settings = {}

class BFA_OT_viewport_silhuette_toggle(op):
    bl_idname = "view3d.viewport_silhouette_toggle"
    bl_label = "Viewport Silhuette Toggle Operator"
    bl_description = "Toggles the viewport overlay to a viewport material color silhuette mode"
    bl_icon = 'ARMATURE_DATA'

    def execute(self, context):
        # Find the active 3D viewport
        area = next((area for area in bpy.context.screen.areas if area.type == 'VIEW_3D' and area == context.area), None)

        if not area:
            self.report({'WARNING'}, "No active 3D viewport found")
            return {'CANCELLED'}

        shading = area.spaces.active.shading

        global previous_viewport_settings

        # If the previous settings are stored, restore them
        if previous_viewport_settings:
            shading.type = previous_viewport_settings['type']
            shading.light = previous_viewport_settings['light']
            shading.show_object_outline = previous_viewport_settings['show_object_outline']
            shading.background_type = previous_viewport_settings['background_type']
            shading.background_color = previous_viewport_settings['background_color']
            shading.show_xray = previous_viewport_settings['show_xray']
            shading.show_shadows = previous_viewport_settings['show_shadows']
            shading.show_cavity = previous_viewport_settings['show_cavity']
            shading.color_type = previous_viewport_settings['color_type']
            shading.single_color = previous_viewport_settings['single_color']
            shading.show_backface_culling = previous_viewport_settings['backface']

            # Clear the previous settings
            previous_viewport_settings = {}
        else:
            # Store the current settings
            previous_viewport_settings = {
                'type': shading.type,
                'light': shading.light,
                'show_object_outline': shading.show_object_outline,
                'background_type': shading.background_type,
                'background_color': shading.background_color,
                'show_xray': shading.show_xray,
                'show_shadows': shading.show_shadows,
                'show_cavity': shading.show_cavity,
                'color_type': shading.color_type,
                'single_color': shading.single_color,
                'backface': shading.show_backface_culling,
            }

            # Change the settings to the desired values
            shading.type = 'SOLID'
            shading.light = 'FLAT'
            shading.show_object_outline = False
            shading.background_type = 'VIEWPORT'
            shading.background_color = (0, 0, 0)
            shading.show_xray = False
            shading.show_shadows = False
            shading.show_cavity = False
            shading.color_type = 'MATERIAL'
            shading.single_color = (1, 1, 1)
            shading.show_backface_culling = True

        return {'FINISHED'}


    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_viewport:
            self.layout.operator(BFA_PROP_toggle_viewport.bl_idname, icon=BFA_PROP_toggle_viewport.bl_icon)




operator_list = [
    # Animation Operators
    BFA_OT_insertframe_left,
    BFA_OT_insertframe_right,
    BFA_OT_removeframe_left,
    BFA_OT_removeframe_right,
    BFA_OT_jump_forward,
    BFA_OT_jump_back,
    # Viewport Operators
    BFA_OT_viewport_silhuette_toggle
    # Add more operators as needed
]

def register():
    for ops in operator_list:
        bpy.utils.register_class(ops)

    # Remove Properties
    bpy.types.Scene.frameskip = bpy.props.IntProperty(name="Jump Frames", default=10)

def unregister():
    for ops in operator_list:
        bpy.utils.unregister_class(ops)

    # Add Properties
    del bpy.types.Scene.frameskip