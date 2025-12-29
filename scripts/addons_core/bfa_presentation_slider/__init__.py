# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Presentation Slider",
    "author": "Draise (@trinumedia)",
    "version": (0, 3, 4),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > View > Presentation Slider",
    "description": "Add controls to switch to the next Scene then plays the animation once, useful for presentation slides setup as Scenes",
    "warning": "",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "support": "OFFICIAL",
    "category": "Bforartists",
}


import bpy
import time
import re

from bpy.types import Operator, Panel, PropertyGroup
from bpy.utils import register_class, unregister_class
from bpy.props import IntProperty, PointerProperty


class SlideSettings(PropertyGroup):
    frame_range: IntProperty(
        name="Duration",
        description="Number of frames for each slide",
        default=30,
        min=1,
        soft_max=300
    )

def register_properties():
    bpy.utils.register_class(SlideSettings)
    bpy.types.Scene.slide_settings = PointerProperty(type=SlideSettings)

def unregister_properties():
    del bpy.types.Scene.slide_settings
    bpy.utils.unregister_class(SlideSettings)


# Track playback state
_presentation_playback_active = False

# Function to completely reset presentation mode and remove handler
def reset_presentation_mode():
    global _presentation_playback_active
    _presentation_playback_active = False
    
    # Remove the handler if it exists
    if stop_playback in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(stop_playback)
        print("Slide Playback stopped")

# Simple handler for end of animation
def stop_playback(scene):
    global _presentation_playback_active
    
    # Only process if we're in presentation playback mode
    if not _presentation_playback_active:
        return
    
    # If animation is playing and we're at the end frame
    if bpy.context.screen.is_animation_playing and scene.frame_current >= scene.frame_end:
        # Stop animation playback
        bpy.ops.screen.animation_cancel(restore_frame=False)
        
        # Completely reset presentation mode
        reset_presentation_mode()

# Monitor animation state continuously
class PRESENTATION_OT_AnimationMonitor(bpy.types.Operator):
    """Monitor animation state and remove handler when animation stops"""
    bl_idname = "presentation.animation_monitor"
    bl_label = "Monitor Animation State"
    
    _timer = None
    _was_playing = False
    
    def modal(self, context, event):
        global _presentation_playback_active
        
        # Check if animation state changed from playing to stopped
        is_playing = context.screen.is_animation_playing
        
        # If animation was playing but now stopped
        if self._was_playing and not is_playing:
            # Reset presentation mode to ensure handler is removed
            reset_presentation_mode()
            # Remove the timer and exit modal
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}
            
        # Update animation state
        self._was_playing = is_playing
        
        # If presentation mode was disabled externally, exit
        if not _presentation_playback_active:
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}
            
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        self._was_playing = context.screen.is_animation_playing
        
        # Start the timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

# Custom keybinding to ensure ESC key removes the handler
def register_keymaps():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Screen', space_type='EMPTY')
    
    # ESC key to stop animation and reset
    kmi = km.keymap_items.new('screen.animation_cancel', 'ESC', 'PRESS')
    kmi.properties.restore_frame = False
    
    return (km, kmi)

def unregister_keymaps(km, kmi):
    km.keymap_items.remove(kmi)

# Store keymap reference
_keymap_data = None


def get_next_s_name(insert_idx=None):
    pattern = re.compile(r"S(\d{3})")
    used_indices = set()
    for scene in bpy.data.scenes:
        match = pattern.fullmatch(scene.name)
        if match:
            used_indices.add(int(match.group(1)))
    if insert_idx is None:
        # default: lowest available (backwards compatible)
        for idx in range(1000):
            if idx not in used_indices:
                return f"S{str(idx).zfill(3)}"
        return f"S{str(max(used_indices, default=-1) + 1).zfill(3)}"
    else:
        # force S{insert_idx:03d}
        return f"S{str(insert_idx).zfill(3)}"


def duplicate_collection_recursive(original_coll, new_name):
    # Duplicate collection and its full hierarchy
    new_coll = bpy.data.collections.new(new_name)
    for obj in original_coll.objects:
        obj_copy = obj.copy()
        if obj.data:
            obj_copy.data = obj.data.copy()
        new_coll.objects.link(obj_copy)
    for child in original_coll.children:
        child_copy = duplicate_collection_recursive(child, child.name)
        new_coll.children.link(child_copy)
    # 🖌️ Color tag — 3 is "Red"
    new_coll.color_tag = 'COLOR_01'
    return new_coll


def clean_orphaned_s_collections():
    pattern = re.compile(r"S(\d{3})")
    orphan_names = []
    for coll in bpy.data.collections:
        if pattern.fullmatch(coll.name):
            # Check if it's linked to any scene
            linked = any(coll.name in [c.name for c in scene.collection.children] for scene in bpy.data.scenes)
            if not linked:
                orphan_names.append(coll.name)
    for name in orphan_names:
        coll = bpy.data.collections.get(name)
        if coll:
            bpy.data.collections.remove(coll)
            print(f"🗑️ Removed orphaned collection '{name}'")


class VIEW_OT_SlideSetupOperator(Operator):
    """Setup or duplicate slide scenes and collections with camera"""
    bl_idname = "scene.setup_slide_scene"
    bl_label = "Insert New Slide Scene"
    bl_description = "Sets up a new slide scene/collection/camera structure, or inserts a new slide scene after current select slide scene"

    def execute(self, context):
        base_scene_name = "S000"
        base_collection_name = "SET"

        self.frame_range = context.scene.slide_settings.frame_range

        def create_slide_camera(collection, cam_name, source_camera=None):
            cam_obj = bpy.data.objects.get(cam_name)
            if not cam_obj:
                # If we have a source camera, copy its data
                if source_camera:
                    cam_data = source_camera.data.copy()
                    cam_data.name = cam_name
                    cam_obj = source_camera.copy()
                    cam_obj.name = cam_name
                    cam_obj.data = cam_data
                else:
                    # Fall back to default camera creation
                    cam_data = bpy.data.cameras.new(cam_name)
                    cam_obj = bpy.data.objects.new(cam_name, cam_data)
                    cam_obj.location = (0, 0, 0)
                    
                collection.objects.link(cam_obj)
            elif cam_obj.name not in [o.name for o in collection.objects]:
                collection.objects.link(cam_obj)
            
            return cam_obj

        # ======= 1. SETUP S000 ===========
        if base_scene_name not in bpy.data.scenes:
            new_scene = bpy.data.scenes.new(base_scene_name)
            # Ensure the scene is kept even with 0 users
            new_scene.use_fake_user = True
            bpy.context.window.scene = new_scene
            new_scene.name = base_scene_name
            # -- Setup SET collection (red tag)
            set_coll = bpy.data.collections.get(base_collection_name)
            if set_coll is None:
                set_coll = bpy.data.collections.new(base_collection_name)
                set_coll.color_tag = 'COLOR_05'
                for sc in bpy.data.scenes:
                    if set_coll.name not in [c.name for c in sc.collection.children]:
                        sc.collection.children.link(set_coll)
                # self.report({'INFO'}, f"📁 Created new SET collection '{base_collection_name}'")
            else:
                for sc in bpy.data.scenes:
                    if set_coll.name not in [c.name for c in sc.collection.children]:
                        sc.collection.children.link(set_coll)
            # -- Create S000 slide collection (blue)
            slide_coll_name = base_scene_name
            slide_coll = bpy.data.collections.get(slide_coll_name)
            if slide_coll is None:
                slide_coll = bpy.data.collections.new(slide_coll_name)
                slide_coll.color_tag = 'COLOR_02'
                new_scene.collection.children.link(slide_coll)
                # self.report({'INFO'}, f"📦 Created slide collection '{slide_coll_name}'")
            else:
                if slide_coll.name not in [c.name for c in new_scene.collection.children]:
                    new_scene.collection.children.link(slide_coll)
            # -- Setup SET and Slide links
            if set_coll.name not in [c.name for c in new_scene.collection.children]:
                new_scene.collection.children.link(set_coll)
            if slide_coll.name not in [c.name for c in new_scene.collection.children]:
                new_scene.collection.children.link(slide_coll)
            # -- Add camera named S000 in S000 collection
            # For first scene (S000), create a default camera with horizontal rotation
            cam_data = bpy.data.cameras.new(slide_coll_name)
            cam_obj = bpy.data.objects.new(slide_coll_name, cam_data)
            cam_obj.location = (0, -10, 0)  # Move back on Y axis
            cam_obj.rotation_euler = (1.5708, 0, 0)  # 90 degrees in radians for horizontal view
            slide_coll.objects.link(cam_obj)
            new_scene.camera = cam_obj
            # -- Set frame range
            new_scene.frame_start = 1
            new_scene.frame_end = context.scene.slide_settings.frame_range
            
            # Reset timeline to start frame
            new_scene.frame_current = new_scene.frame_start
            bpy.ops.screen.animation_cancel(restore_frame=True)
            bpy.ops.screen.frame_jump(end=False)
            
            # self.report({'INFO'}, f"✅ Initial slide '{base_scene_name}' ready.")
            return {'FINISHED'}

        # ======= 2. INSERT SLIDE SCENE (SEQUENTIALLY, shifting higher) ===========
        # Identify where to insert: the current selected Sxxx scene
        current_scene = context.scene
        s_pattern = re.compile(r"S(\d{3})")
        current_match = s_pattern.fullmatch(current_scene.name)
        if not current_match:
            # self.report({'ERROR'}, "Current scene is not a slide (Sxxx). Select a slide scene to insert after!")
            return {'CANCELLED'}
        insert_idx = int(current_match.group(1)) + 1

        # Collect all "Sxxx" scenes, sorted by index
        scenes_s = []
        for sc in bpy.data.scenes:
            m = s_pattern.fullmatch(sc.name)
            if m:
                scenes_s.append((int(m.group(1)), sc))
        scenes_s.sort()

        # Check if insert_idx is already taken. If NOT, we can just add S{insert_idx:03d}
        target_scene_name = f"S{insert_idx:03d}"
        if target_scene_name in bpy.data.scenes:
            # SHIFT UP: from highest down to insert_idx, shift scene & collection & camera names
            for idx, scene in reversed(scenes_s):
                if idx >= insert_idx:
                    new_index = idx + 1
                    new_scenename = f"S{new_index:03d}"
                    if new_scenename in bpy.data.scenes:
                        # self.report({'WARNING'}, f"Scene '{new_scenename}' already exists, skipping shift.")
                        continue

                    old_collection = bpy.data.collections.get(f"S{idx:03d}")
                    old_camera = None
                    for obj in bpy.data.objects:
                        if obj.type == 'CAMERA' and obj.name == f"S{idx:03d}":
                            old_camera = obj
                            break

                    scene.name = new_scenename

                    # Rename corresponding slide collection
                    if old_collection and f"S{new_index:03d}" not in bpy.data.collections:
                        old_collection.name = f"S{new_index:03d}"
                    # Rename camera object (if present and safe)
                    if old_camera and f"S{new_index:03d}" not in bpy.data.objects:
                        old_camera.name = f"S{new_index:03d}"

        # Now, insert new slide at insert_idx (name Sxxx with insert_idx)
        src_scene = bpy.data.scenes.get(base_scene_name)
        if not src_scene:
            # self.report({'ERROR'}, "Couldn't find S000 for duplication.")
            return {'CANCELLED'}
        new_slide_name = get_next_s_name(insert_idx)
        new_scene = src_scene.copy()
        new_scene.name = new_slide_name
        # Ensure the scene is kept even with 0 users
        new_scene.use_fake_user = True
        bpy.context.window.scene = new_scene
        # Copy the slide settings from the current scene to maintain consistency
        new_scene.slide_settings.frame_range = context.scene.slide_settings.frame_range
        
        # Calculate the new scene's frame range based on the previous scene's end frame
        frame_range = context.scene.slide_settings.frame_range
        prev_scene_name = f"S{insert_idx-1:03d}"
        prev_scene = bpy.data.scenes.get(prev_scene_name)
        if prev_scene:
            # Calculate start frame directly based on previous scene's end frame
            new_scene.frame_start = prev_scene.frame_end + 1
        else:
            new_scene.frame_start = 1
        # End frame will be start + duration - 1 to maintain exact duration length
        new_scene.frame_end = new_scene.frame_start + frame_range - 1
        
        # Remove S000 from children of new scene
        for coll in list(new_scene.collection.children):
            if coll.name == base_scene_name:
                new_scene.collection.children.unlink(coll)
                # self.report({'INFO'}, f"🧹 Unlinked '{base_scene_name}' collection from new scene '{new_slide_name}'")
                break
        # Create new slide collection with appropriate name/color, link to new scene
        new_slide_coll = bpy.data.collections.get(new_slide_name)
        if new_slide_coll is None:
            new_slide_coll = bpy.data.collections.new(new_slide_name)
            new_slide_coll.color_tag = 'COLOR_02'
            new_scene.collection.children.link(new_slide_coll)
            # self.report({'INFO'}, f"📦 Created new slide collection '{new_slide_name}'")
        else:
            if new_slide_coll.name not in [c.name for c in new_scene.collection.children]:
                new_scene.collection.children.link(new_slide_coll)
                # self.report({'INFO'}, f"🔁 Linked existing collection '{new_slide_coll.name}'")
        # Get the camera from the previous scene by name
        prev_scene_name = f"S{insert_idx-1:03d}"
        prev_scene = bpy.data.scenes.get(prev_scene_name)
        if prev_scene and prev_scene.camera:
            # Add new camera for this slide, copying from previous scene's camera
            cam_obj = create_slide_camera(new_slide_coll, new_slide_name, source_camera=prev_scene.camera)
        else:
            # Fallback to copying from S000 if something goes wrong
            base_scene = bpy.data.scenes.get("S000")
            if base_scene and base_scene.camera:
                cam_obj = create_slide_camera(new_slide_coll, new_slide_name, source_camera=base_scene.camera)
            else:
                cam_obj = create_slide_camera(new_slide_coll, new_slide_name)
        new_scene.camera = cam_obj

        # Reset timeline to start frame
        new_scene.frame_current = new_scene.frame_start
        bpy.ops.screen.animation_cancel(restore_frame=True)
        bpy.ops.screen.frame_jump(end=False)

        # self.report({'INFO'}, f"✅ Inserted slide '{new_slide_name}' with new collection & camera, scenes updated!")
        return {'FINISHED'}


  
class VIEW_OT_PlayAnimationOperator(Operator):
    """Plays the next slide scene and its animation"""
    bl_idname = "screen.play_animation"
    bl_label = "Next"
    bl_description = "Plays the next slide as the next Scene\nThis will add a hook so playback stops on final frame of the timeline\nPress the Loop Animation button to remove the hook"

    def execute(self, context):
        global _presentation_playback_active
        
        # First make sure any existing handlers/monitors are removed
        reset_presentation_mode()
        
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        # Set the current frame to the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)
        
        # Add frame change handler
        if stop_playback not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(stop_playback)
            print("Slide Playback started")

        # Get the current scene
        current_scene = context.scene

        # Get the list of scenes
        scenes = bpy.data.scenes

        # Find the index of the current scene in the list
        current_index = scenes.find(current_scene.name)

        # If this isn't the last scene, switch to the next one
        if current_index < len(scenes) - 1:
            next_scene = scenes[current_index + 1]
            context.window.scene = next_scene
        else:
            # If this is the last scene, switch back to the first one
            first_scene = scenes[0]
            context.window.scene = first_scene

        # Enable presentation mode tracking
        _presentation_playback_active = True
            
        # Start playback
        bpy.ops.screen.animation_play()
        
        # Start the animation monitor
        bpy.ops.presentation.animation_monitor('INVOKE_DEFAULT')

        return {'FINISHED'}


class VIEW_OT_ReverseAnimationOperator(Operator):
    """Plays the previous slide scene and its animation"""
    bl_idname = "screen.play_back_animation"
    bl_label = "Previous"
    bl_description = "Plays the previous slide as the last Scene\nThis will add a hook so playback stops on final frame of the timeline\nPress the Loop Animation button to remove the hook"

    def execute(self, context):
        global _presentation_playback_active
        
        # First make sure any existing handlers/monitors are removed
        reset_presentation_mode()
        
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        # Set the current frame to the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)

        # Add frame change handler
        if stop_playback not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(stop_playback)
            print("Presentation handler appended")

        # Get the current scene
        current_scene = context.scene

        # Get the list of scenes
        scenes = bpy.data.scenes

        # Find the index of the current scene in the list
        current_index = scenes.find(current_scene.name)

        # Go to the previous scene if possible
        if current_index > 0:
            prev_scene = scenes[current_index - 1]
            context.window.scene = prev_scene
            
        # Enable presentation mode tracking
        _presentation_playback_active = True
            
        # Start playback
        bpy.ops.screen.animation_play()
        
        # Start the animation monitor
        bpy.ops.presentation.animation_monitor('INVOKE_DEFAULT')

        return {'FINISHED'}

class VIEW_OT_RemoveAnimationOperator(Operator):
    """Play animation for current scene with auto-stop"""
    bl_idname = "screen.remove_stop"
    bl_label = "Play Current Slide"
    bl_description = "Plays animation for the current scene with automatic stop at the end, just like Next/Previous buttons"

    def execute(self, context):
        global _presentation_playback_active
        
        # First make sure any existing handlers/monitors are removed
        reset_presentation_mode()
        
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        # Set the current frame to the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)
        
        # Add frame change handler
        if stop_playback not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(stop_playback)
            print("Presentation handler appended")

        # Enable presentation mode tracking
        _presentation_playback_active = True
            
        # Start playback
        bpy.ops.screen.animation_play()
        
        # Start the animation monitor
        bpy.ops.presentation.animation_monitor('INVOKE_DEFAULT')

        return {'FINISHED'}


# Track presentation view state
_presentation_view_active = False
_original_view_settings = {}

class VIEW_OT_HideInterface(Operator):
    """Toggle presentation view mode - hides interface and maximizes viewport"""
    bl_idname = "screen.hide_interface"
    bl_label = "Presentation View"
    bl_description = "Toggles presentation mode - hides interface and maximizes viewport with render view"
    
    def execute(self, context):
        global _presentation_view_active, _original_view_settings
        
        space = bpy.context.space_data
        
        # Toggle presentation mode state
        _presentation_view_active = not _presentation_view_active
        
        if _presentation_view_active:  # Entering presentation mode
            # Store current settings before changing them
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    _original_view_settings = {
                        'show_region_header': space.show_region_header,
                        'show_region_ui': space.show_region_ui,
                        'show_region_toolbar': space.show_region_toolbar,
                        'show_region_asset_shelf': getattr(space, 'show_region_asset_shelf', False),
                        'show_overlays': space.overlay.show_overlays,
                        'shading_type': space.shading.type,
                        'show_gizmo': space.show_gizmo,
                    }
                    break
            
            # Enter fullscreen mode
            bpy.ops.screen.screen_full_area()
            
            # Apply presentation settings
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    # Update space reference after screen change
                    space = area.spaces.active
                    
                    # Hide all UI elements
                    space.show_region_header = False
                    space.show_region_ui = False
                    space.show_region_toolbar = False
                    if hasattr(space, 'show_region_asset_shelf'):
                        space.show_region_asset_shelf = False
                    
                    # Set clean viewport
                    space.overlay.show_overlays = False
                    space.shading.type = 'RENDERED'
                    space.show_gizmo = False
                    
                    self.report({'INFO'}, "Entered presentation view mode")
        else:  # Exiting presentation mode
            # Exit fullscreen mode
            bpy.ops.screen.screen_full_area()
            
            # Restore original settings
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    # Update space reference after screen change
                    space = area.spaces.active
                    
                    # Restore all saved settings
                    if _original_view_settings:
                        space.show_region_header = _original_view_settings.get('show_region_header', True)
                        space.show_region_ui = _original_view_settings.get('show_region_ui', True)
                        space.show_region_toolbar = _original_view_settings.get('show_region_toolbar', True)
                        if hasattr(space, 'show_region_asset_shelf'):
                            space.show_region_asset_shelf = _original_view_settings.get('show_region_asset_shelf', False)
                        
                        space.overlay.show_overlays = _original_view_settings.get('show_overlays', True)
                        space.shading.type = _original_view_settings.get('shading_type', 'SOLID')
                        space.show_gizmo = _original_view_settings.get('show_gizmo', True)

                    self.report({'INFO'}, "Exited presentation view mode")

        return {'FINISHED'}



############ INTERFACE ############

# Define the panel class for the property shelf
class VIEW_PT_PlayAnimationPanel(bpy.types.Panel):
    bl_idname = "SCENE_PT_play_animation"
    bl_label = "Presentation Slides"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    #bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Math From Box (Slides and playback control)
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Slides:")

        row = col.row(align=True)
        row.operator("screen.play_back_animation", icon="PREV_KEYFRAME")
        row.operator("screen.play_animation", icon="NEXT_KEYFRAME")

        col.separator()

        # Full width Play Current Slide button (inside the box)
        row = col.row(align=False)
        row.scale_y = 1
        row.operator("screen.remove_stop", icon="PLAY")

        # Big button for Insert Slide
        row = layout.row()
        row.scale_y = 2.0
        row.operator("scene.setup_slide_scene", icon="ADD")

        # Property field for frames
        row = layout.row()
        row.scale_y = 1.0
        row.prop(context.scene.slide_settings, "frame_range", text="Duration")

        layout.separator()

        # Presentation View Button (with custom style)
        row.scale_y = 1.2
        
        # Use different icon and text based on active state
        if _presentation_view_active:
            row.operator("screen.hide_interface", text="Exit Presentation View", icon="FULLSCREEN_EXIT")
        else:
            row.operator("screen.hide_interface", text="Enter Presentation View", icon="FULLSCREEN_ENTER")



############ REGISTRY ############

# Register the classes
classes = [
    VIEW_OT_SlideSetupOperator,
    VIEW_OT_PlayAnimationOperator,
    VIEW_OT_ReverseAnimationOperator,
    VIEW_OT_RemoveAnimationOperator,
    VIEW_OT_HideInterface,
    VIEW_PT_PlayAnimationPanel,
    PRESENTATION_OT_AnimationMonitor,
]

def register():
    global _keymap_data
    
    register_properties()

    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register keymap
    _keymap_data = register_keymaps()


def unregister():
    global _keymap_data, _presentation_playback_active, _presentation_view_active
    
    # Unregister keymap
    if _keymap_data:
        unregister_keymaps(*_keymap_data)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_properties()

    # Reset all global state
    _presentation_playback_active = False
    _presentation_view_active = False
    
    # Remove handler if it exists
    if stop_playback in bpy.app.handlers.frame_change_post:
        print("Removing presentation playback handler on unregister")
        bpy.app.handlers.frame_change_post.remove(stop_playback)


# Run the register function when the script is executed
if __name__ == "__main__":
    register()
