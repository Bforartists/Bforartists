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
import os
import mathutils
from . import properties

op = bpy.types.Operator


# Get window manager from context - this is the correct way to access it
context = bpy.context
wm = context.window_manager

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

        # Create a list to store frames to be moved for GP
        frames_to_move = []

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                for layer in action.layers:
                    for strip in layer.strips:
                        if strip.type == 'KEYFRAME':
                            for channelbag in strip.channelbags:
                                # Iterate over each fcurve in the channelbag
                                for fcurve in channelbag.fcurves:
                                    # Iterate over each keyframe point in the fcurve
                                    for keyframe in fcurve.keyframe_points:
                                        # If the keyframe is after the current frame
                                        if keyframe.co.x < current_frame:
                                            # Nudge the key frame one frame backward
                                            keyframe.co.x -= 1

            # Check if the object is a grease pencil object
            if obj.type == 'GREASEPENCIL':
                for layer in obj.data.layers:
                    # Clear the frames_to_move list
                    frames_to_move.clear()

                    for frame in layer.frames:
                        # Ensure frames to move are only those higher than the current frame, and not 0.
                        if frame.frame_number < current_frame and frame.frame_number != 0:
                            frames_to_move.append(frame.frame_number)

                    # Sort the frames in descending order of their frame numbers
                    frames_to_move.sort(key=lambda frame: frame, reverse=False)

                    # Move all frames in the list one frame forward
                    for frame in frames_to_move:
                        source_frame = frame
                        target_frame = frame - 1
                        layer.frames.move(source_frame, target_frame)


                        # Ensure frames are aligned correctly after movement
                        layer.frames.update()

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

        # Create a list to store frames to be moved for GP
        frames_to_move = []

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                # Iterate over each fcurve in the action
                action = obj.animation_data.action
                for layer in action.layers:
                    for strip in layer.strips:
                        if strip.type == 'KEYFRAME':
                            for channelbag in strip.channelbags:
                                # Iterate over each fcurve in the channelbag
                                for fcurve in channelbag.fcurves:
                                    # Iterate over each keyframe point in the fcurve
                                    for keyframe in fcurve.keyframe_points:
                                        # If the keyframe is after the current frame
                                        if keyframe.co.x > current_frame:
                                            # Nudge the key frame one frame backward
                                            keyframe.co.x += 1

            # Check if the object is a grease pencil object
            if obj.type == 'GREASEPENCIL':
                for layer in obj.data.layers:
                    # Clear the frames_to_move list
                    frames_to_move.clear()

                    for frame in layer.frames:
                        # Ensure frames to move are only those higher than the current frame, and not 0.
                        if frame.frame_number > current_frame and frame.frame_number != 0:
                            frames_to_move.append(frame.frame_number)

                    # Sort the frames in descending order of their frame numbers
                    frames_to_move.sort(key=lambda frame: frame, reverse=True)

                    # Move all frames in the list one frame forward
                    for frame in frames_to_move:
                        source_frame = frame
                        target_frame = frame + 1
                        layer.frames.move(source_frame, target_frame)

                        # Ensure frames are aligned correctly after movement
                        layer.frames.update()

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

        # Create a list to store frames to be moved for GP
        frames_to_move = []

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                for layer in action.layers:
                    for strip in layer.strips:
                        if strip.type == 'KEYFRAME':
                            for channelbag in strip.channelbags:
                                # Iterate over each fcurve in the channelbag
                                for fcurve in channelbag.fcurves:
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
            if obj.type == 'GREASEPENCIL':
                for layer in obj.data.layers:
                    # Clear the frames_to_move list
                    frames_to_move.clear()

                    for frame in layer.frames:
                        # Ensure frames to move are only those higher than the current frame, and not 0.
                        if frame.frame_number <= current_frame and frame.frame_number != 0:
                            frames_to_move.append(frame.frame_number)

                    # Sort the frames in descending order of their frame numbers
                    frames_to_move.sort(key=lambda frame: frame, reverse=True)

                    # Move all frames in the list one frame forward
                    for frame in frames_to_move:
                        source_frame = frame
                        target_frame = frame + 1

                        if frame == current_frame:
                            layer.frames.remove(frame)
                        else:
                            layer.frames.move(source_frame, target_frame)


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

        # Create a list to store frames to be moved for GP
        frames_to_move = []

        # Iterate over each selected object
        for obj in selected_objects:
            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                for layer in action.layers:
                    for strip in layer.strips:
                        if strip.type == 'KEYFRAME':
                            for channelbag in strip.channelbags:
                                # Iterate over each fcurve in the channelbag
                                for fcurve in channelbag.fcurves:
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
            if obj.type == 'GREASEPENCIL':

                for layer in obj.data.layers:


                    # Clear the frames_to_move list
                    frames_to_move.clear()

                    for frame in layer.frames:
                        # Ensure frames to move are only those higher than the current frame, and not 0.
                        if frame.frame_number >= current_frame and frame.frame_number != 0:
                            frames_to_move.append(frame.frame_number)

                    # Print the frames that were appended to frames_to_move
                    for frame in frames_to_move:
                        print(f"Appended frame: {frame}")

                    # Sort the frames in descending order of their frame numbers
                    frames_to_move.sort(key=lambda frame: frame, reverse=False)

                    # Print frames_to_move frames
                    for frame in frames_to_move:
                        print(f"Frame to move in order: {frame}")

                    # Move all frames in the list one frame forward
                    for frame in frames_to_move:
                        source_frame = frame
                        target_frame = frame - 1

                        if frame == current_frame:
                            layer.frames.remove(frame)
                            print(f"Removed frame: {frame}")
                        else:
                            layer.frames.move(source_frame, target_frame)




                        # Ensure frames are aligned correctly after movement
                        layer.frames.update()

        # Update the scene
        bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}


    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
            self.layout.operator(BFA_OT_removeframe_right.bl_idname, icon=BFA_OT_removeframe_right.bl_icon)


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
            shading.color_type = 'SINGLE'
            shading.single_color = (1, 1, 1)
            shading.show_backface_culling = True

        return {'FINISHED'}


    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_viewport:
            self.layout.operator(BFA_PROP_toggle_viewport.bl_idname, icon=BFA_PROP_toggle_viewport.bl_icon)

################## Grease Pencil Operators ##################

# Shared hit-detection logic for both GP select operators
def _gp_find_layers_under_mouse(context, event):
    """Find all Grease Pencil layers that have strokes under the mouse cursor.
    Returns (hit_layers_set, gp_data) or (None, None) on failure."""
    region = context.region
    region_data = context.region_data

    if not region or not region_data:
        return None, None

    from bpy_extras.view3d_utils import location_3d_to_region_2d

    mouse_x = event.mouse_region_x
    mouse_y = event.mouse_region_y

    obj = context.active_object
    gp_data = obj.data
    scene_frame = context.scene.frame_current
    world_mat = obj.matrix_world

    # Get brush from the current mode's tool settings for consistent hit radius
    ts = context.tool_settings
    brush = None
    try:
        if context.mode == 'PAINT_GREASE_PENCIL':
            brush = ts.gpencil_paint.brush
        elif context.mode == 'SCULPT_GREASE_PENCIL':
            brush = ts.gpencil_sculpt.brush
        elif context.mode == 'VERTEX_GREASE_PENCIL':
            brush = ts.gpencil_vertex.brush
        elif context.mode == 'WEIGHT_GREASE_PENCIL':
            brush = ts.gpencil_weight.brush
    except AttributeError:
        brush = None
    hit_threshold_px = brush.size / 2 if brush else 15

    hit_layers = set()

    for layer in gp_data.layers:
        if layer.hide:
            continue
        if layer in hit_layers:
            continue

        # Find the active keyframe at current scene frame
        active_frame = None
        for frame in layer.frames:
            if frame.frame_number <= scene_frame:
                if active_frame is None or frame.frame_number > active_frame.frame_number:
                    active_frame = frame

        if active_frame is None:
            continue

        for stroke in active_frame.drawing.strokes:
            for point in stroke.points:
                # Project world position to 2D screen coordinates
                world_pos = world_mat @ point.position
                screen_pos = location_3d_to_region_2d(region, region_data, world_pos)
                if screen_pos is None:
                    continue  # Behind camera
                dx = screen_pos.x - mouse_x
                dy = screen_pos.y - mouse_y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < hit_threshold_px:
                    hit_layers.add(layer)
                    break
            if layer in hit_layers:
                break

    return hit_layers, gp_data


def _gp_select_hit_layers(hit_layers, gp_data):
    """Deselect all strokes, then select strokes on hit_layers and set the first as active.
    Returns list of layer names."""
    # Deselect all strokes across all layers
    for layer in gp_data.layers:
        for frame in layer.frames:
            for stroke in frame.drawing.strokes:
                stroke.select = False

    # Select all strokes in the found layers and set the first hit as active
    layer_names = []
    for i, layer in enumerate(hit_layers):
        layer_names.append(layer.name)
        if i == 0:
            gp_data.layers.active = layer
        for frame in layer.frames:
            for stroke in frame.drawing.strokes:
                stroke.select = True

    return layer_names


class BFA_OT_gp_select_layer_under_mouse(bpy.types.Operator):
    """Select all strokes of the layer under the mouse cursor"""
    bl_idname = "view3d.gp_select_layer_under_mouse"
    bl_label = "Layer Under Mouse"
    bl_description = "Detects the strokes and layer under the mouse in all modes and selects the layer or all strokes on that layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'GREASEPENCIL' and context.mode in {
            'PAINT_GREASE_PENCIL',
            'EDIT_GREASE_PENCIL',
            'SCULPT_GREASE_PENCIL',
            'VERTEX_GREASE_PENCIL',
            'WEIGHT_GREASE_PENCIL',
        }

    def invoke(self, context, event):
        hit_layers, gp_data = _gp_find_layers_under_mouse(context, event)
        if hit_layers is None:
            self.report({'WARNING'}, "No active 3D viewport")
            return {'CANCELLED'}

        if hit_layers:
            layer_names = _gp_select_hit_layers(hit_layers, gp_data)
            self.report({'INFO'}, f"Selected strokes on: {', '.join(layer_names)}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No stroke found under mouse")
            return {'CANCELLED'}

    def menu_func(self, context):
        self.layout.operator(BFA_OT_gp_select_layer_under_mouse.bl_idname, icon='GREASEPENCIL')


class BFA_OT_gp_select_layer_under_mouse_isolate(bpy.types.Operator):
    """Select all strokes of the layer under the mouse cursor and isolate it"""
    bl_idname = "view3d.gp_select_layer_under_mouse_isolate"
    bl_label = "Layer and Isolate Under Mouse"
    bl_description = "Detects the strokes and layer under the mouse in all modes, selects them, and isolates that layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'GREASEPENCIL' and context.mode in {
            'PAINT_GREASE_PENCIL',
            'EDIT_GREASE_PENCIL',
            'SCULPT_GREASE_PENCIL',
            'VERTEX_GREASE_PENCIL',
            'WEIGHT_GREASE_PENCIL',
        }

    def invoke(self, context, event):
        hit_layers, gp_data = _gp_find_layers_under_mouse(context, event)
        if hit_layers is None:
            self.report({'WARNING'}, "No active 3D viewport")
            return {'CANCELLED'}

        if hit_layers:
            layer_names = _gp_select_hit_layers(hit_layers, gp_data)
            self.report({'INFO'}, f"Selected and Isolated strokes on: {', '.join(layer_names)}")

            # Isolate the active layer (lock all others)
            bpy.ops.grease_pencil.layer_isolate(affect_visibility=False)

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No stroke found under mouse")
            return {'CANCELLED'}

    def menu_func(self, context):
        self.layout.operator(BFA_OT_gp_select_layer_under_mouse_isolate.bl_idname, icon='LOCKED')



################## File Operators ##################
class BFA_OT_open_blend_file_window(bpy.types.Operator):
    """Open the file explorer to show the current blend file"""
    bl_idname = "bfa.open_blend_file_window"
    bl_label = "Open Blend File Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the current blend file path
        blend_file_path = bpy.data.filepath

        # Check if the file is saved
        if not blend_file_path:
            self.report({'WARNING'}, "Please save the file first")
            return {'CANCELLED'}

        # Open the file explorer/finder to show the file
        if bpy.app.version >= (3, 0, 0):
            # For Blender 3.0+ use the new system operator
            bpy.ops.wm.path_open(filepath=os.path.dirname(blend_file_path))
        else:
            # For older versions use platform-specific methods
            import platform
            import subprocess

            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{blend_file_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(['open', '-R', blend_file_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', os.path.dirname(blend_file_path)])

        return {'FINISHED'}

    def menu_func(self, context):
        wm = context.window_manager
        if wm.BFA_UI_addon_props.BFA_PROP_toggle_file:
            self.layout.operator(BFA_PROP_toggle_file.bl_idname, icon=BFA_PROP_toggle_file.bl_icon)


operator_list = [
    # Animation Operators
    BFA_OT_insertframe_left,
    BFA_OT_insertframe_right,
    BFA_OT_removeframe_left,
    BFA_OT_removeframe_right,
    # Viewport Operators
    BFA_OT_viewport_silhuette_toggle,
    # File Operators
    BFA_OT_open_blend_file_window,
    # Grease Pencil Operators
    BFA_OT_gp_select_layer_under_mouse,
    BFA_OT_gp_select_layer_under_mouse_isolate,
    # Add more operators as needed
]

def register():
    for ops in operator_list:
        bpy.utils.register_class(ops)

def unregister():
    for ops in operator_list:
        bpy.utils.unregister_class(ops)