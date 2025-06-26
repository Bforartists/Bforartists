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
    "version": (0, 3, 8),
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

from bpy.types import Operator, Panel
from bpy.utils import register_class, unregister_class
from bpy.props import IntProperty


def stop_playback(scene):
    if bpy.context.screen.is_animation_playing:
    # Animation is playing, do something...
        #print("...")
        if scene.frame_current >= scene.frame_end:
            #print("Stopping")
            bpy.ops.screen.animation_cancel(restore_frame=False)
            #print("Stopped")
    else:
        pass
        #Animation is not playing, do something else...
        #print("Animation is not playing, pass")

        # Get the current scene
        #current_scene = bpy.context.scene
        
        # Reset to first frame
        #current_scene.frame_set(bpy.context.scene.frame_end)
        #bpy.ops.screen.frame_jump(end=True)




def get_next_s_name():
    pattern = re.compile(r"S(\d{3})")
    indices = []

    for scene in bpy.data.scenes:
        match = pattern.fullmatch(scene.name)
        if match:
            indices.append(int(match.group(1)))

    next_index = max(indices, default=-1) + 1
    return f"S{str(next_index).zfill(3)}"

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
    bl_label = "Setup Slide Scene"
    bl_description = "Sets up a new slide scene/collection/camera structure, or duplicates current slide scene"
    
    def execute(self, context):
        # === Config ===
        scene_name = "S000"
        camera_name = "S000"
        collection_set_name = "SET"
        collection_shot_name = scene_name

        current_scene = bpy.context.scene
        # Only run setup if S000 does NOT exist at all
        if scene_name not in bpy.data.scenes:
            # Step 1: Create new scene
            new_scene = bpy.data.scenes.new(scene_name)
            bpy.context.window.scene = new_scene
            self.report({'INFO'}, f"📂 Created new scene: '{scene_name}'")

            # Step 2: Create/set SET collection
            set_collection = bpy.data.collections.get(collection_set_name)
            if set_collection is None:
                set_collection = bpy.data.collections.new(collection_set_name)
                set_collection.color_tag = 'COLOR_05'  # Red
                bpy.data.collections.link(set_collection)
                self.report({'INFO'}, f"📁 Created red collection: '{collection_set_name}'")
            # Link SET collection to scene
            if all(child.name != set_collection.name for child in new_scene.collection.children):
                new_scene.collection.children.link(set_collection)

            # Step 3: Create shot collection (S000)
            shot_collection = bpy.data.collections.get(collection_shot_name)
            if shot_collection is None:
                shot_collection = bpy.data.collections.new(collection_shot_name)
                bpy.data.collections.link(shot_collection)
                self.report({'INFO'}, f"🎬 Created collection: '{collection_shot_name}'")
            if all(child.name != shot_collection.name for child in new_scene.collection.children):
                new_scene.collection.children.link(shot_collection)

            # Step 4: Create camera named S000 at origin if not present
            cam_object = bpy.data.objects.get(camera_name)
            if cam_object is None:
                cam_data = bpy.data.cameras.new(camera_name)
                cam_object = bpy.data.objects.new(camera_name, cam_data)
                cam_object.location = (0.0, 0.0, 0.0)
                shot_collection.objects.link(cam_object)
                new_scene.camera = cam_object
                self.report({'INFO'}, f"🎥 Created camera '{camera_name}' at origin.")
            else:
                self.report({'WARNING'}, f"⚠️ Camera '{camera_name}' already exists.")

            self.report({'INFO'}, f"✅ Initial slide '{scene_name}' ready.")
            return {'FINISHED'}
        else:
            # If we are currently on S000, do nothing further

            # === Main Process: Duplicate from current S### (not S000) ===
            original_scene = bpy.context.scene
            original_scene_name = original_scene.name

            # Only allow duplication if selected scene's name matches S### and is not S000
            pattern = re.compile(r"S\d{3}")
            match = pattern.fullmatch(original_scene_name)
            if not match:
                self.report({'WARNING'}, "Please select a slide scene (S###) other than S000 to duplicate.")
                return {'CANCELLED'}

            new_scene_name = get_next_s_name()

            # Clean orphaned collections
            clean_orphaned_s_collections()

            # Duplicate scene
            new_scene = original_scene.copy()
            new_scene.name = new_scene_name
            new_scene.frame_start += 30
            new_scene.frame_end += 30
            bpy.context.window.scene = new_scene

            scene_collection = new_scene.collection

            # Get original collection named like the original scene
            original_collection = bpy.data.collections.get(original_scene_name)
            existing_duplicate = bpy.data.collections.get(new_scene_name)

            if original_collection:
                if existing_duplicate:
                    # Reuse if exists
                    if existing_duplicate.name not in [c.name for c in scene_collection.children]:
                        scene_collection.children.link(existing_duplicate)
                    self.report({'INFO'}, f"🔁 Reused existing collection '{existing_duplicate.name}'.")
                else:
                    # Deep copy with hierarchy + set blue color
                    duplicated = duplicate_collection_recursive(original_collection, new_scene_name)
                    scene_collection.children.link(duplicated)
                    self.report({'INFO'}, f"📦 Duplicated '{original_collection.name}' to '{duplicated.name}' with hierarchy preserved and color set.")

                # Unlink original collection from new scene
                if original_collection.name in [c.name for c in scene_collection.children]:
                    scene_collection.children.unlink(original_collection)
                    self.report({'INFO'}, f"🧹 Unlinked original collection '{original_collection.name}' from scene '{new_scene_name}'.")

            self.report({'INFO'}, f"✅ Scene '{new_scene_name}' ready: colored, cleaned, and structured.")

        return {'FINISHED'}


  
class VIEW_OT_PlayAnimationOperator(Operator):
    """Tooltip"""
    bl_idname = "screen.play_animation"
    bl_label = "Next"
    bl_description = "Plays the next slide as the next Scene\nThis will add a hook so playback stops on final frame of the timeline\nPress the Loop Animation button to remove the hook"

    _timer = None

    def execute(self, context):
        #print("---------Running")
        
        # If the timeline is playing, pause it
        
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
            #print("Was playing, trying to stop")

            # Set the current frame to the first frame
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            bpy.ops.screen.frame_jump(end=False)
        else:
            #print("Was not playing")

            # Set the current frame to the first frame
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            bpy.ops.screen.frame_jump(end=False)
        
        # Make Animations stop at end
        if stop_playback in bpy.app.handlers.frame_change_post:
            #print("Handler is already appended. Pass.")
            pass
        else:
            print("Handler is not appended.")
            # Append Handler
            bpy.app.handlers.frame_change_post.append(stop_playback)
            #print("Handler appended.")

        # Get the current scene
        current_scene = context.scene

        # Get the list of scenes
        scenes = bpy.data.scenes

        # Find the index of the current scene in the list
        current_index = scenes.find(current_scene.name)

        #reset to first frame
        current_scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)

        # If this isn't the last scene, switch to the next one
        if current_index < len(scenes) - 1:
            next_scene = scenes[current_index + 1]
            context.window.scene = next_scene

            #print("---Next Scene Loaded")

            #print("Waiting")
            #time.sleep(1)
            #print("---Waiting done")

            # Start playback
            #print("Playing")
            bpy.ops.screen.animation_play()
            

        else:
            # If this is the last scene, switch back to the first one
            first_scene = scenes[0]
            context.window.scene = first_scene

            # Set the current frame to the first frame
            #bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            #bpy.ops.screen.frame_jump(end=False)

            #print("---Last Scene Loaded")

            # Start playback
            #print("Playing")
            bpy.ops.screen.animation_play()


        return {'FINISHED'}


# Define the operator class for the button
class VIEW_OT_ReverseAnimationOperator(Operator):
    """Tooltip"""
    bl_idname = "screen.play_back_animation"
    bl_label = "Previous"
    bl_description = "Plays the previous slide as the last Scene\nThis will add a hook so playback stops on final frame of the timeline\nPress the Loop Animation button to remove the hook"

    _timer = None

    def execute(self, context):
        #print("---------Running")
        
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
            #print("Playing, trying to stop")

            # Set the current frame to the first frame
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            bpy.ops.screen.frame_jump(end=False)
        else:
            bpy.ops.screen.animation_cancel(restore_frame=False)

            # Set the current frame to the first frame
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            bpy.ops.screen.frame_jump(end=False)

        # Make Animations stop at end
        if stop_playback in bpy.app.handlers.frame_change_post:
            #print("Handler is appended.")
            pass
        else:
            #print("Handler is not appended.")

            # Append Handler
            bpy.app.handlers.frame_change_post.append(stop_playback)
            #print("Handler appended.")

        # Get the current scene
        current_scene = context.scene

        # Get the list of scenes
        scenes = bpy.data.scenes

        # Find the index of the current scene in the list
        current_index = scenes.find(current_scene.name)

        #reset to first frame
        current_scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)

        # If this isn't the last scene, switch to the next one
        if current_index < len(scenes) + 1:
            next_scene = scenes[current_index - 1]
            context.window.scene = next_scene

            # Start playback
            bpy.ops.screen.animation_play()


        else:
            # If this is the last scene, switch back to the first one EDIT: not necessary backwards
           
            #first_scene = scenes[0]
            #context.window.scene = first_scene

            # Set the current frame to the first frame
            #bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            #bpy.ops.screen.frame_jump(end=False)

            # Start playback
            bpy.ops.screen.animation_play()

        return {'FINISHED'}


class VIEW_OT_RemoveAnimationOperator(Operator):
    """Tooltip"""
    bl_idname = "screen.remove_stop"
    bl_label = "Loop Animation"
    bl_description = "Resets playback looping and plays animation in the current scene"

    _timer = None
    handler_added = False

    # Add or remove stop_playback from frame_change_post handlers
    def execute(self, context):
        if stop_playback in bpy.app.handlers.frame_change_post:
            #print("Handler is appended.")
            bpy.app.handlers.frame_change_post.remove(stop_playback)
            #print("Handler removed.")

            # Set the current frame to the first frame
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            bpy.ops.screen.frame_jump(end=False)

            # Start playback
            bpy.ops.screen.animation_play()

        else:
            #print("Handler is not appended.")

            # Set the current frame to the first frame
            #bpy.context.scene.frame_set(bpy.context.scene.frame_start)
            #bpy.ops.screen.frame_jump(end=False)
            # Start playback
            bpy.ops.screen.animation_play()

        return {'FINISHED'}


class VIEW_OT_HideInterface(Operator):
    """Tooltip"""
    bl_idname = "screen.hide_interface"
    bl_label = "Hide Interface"
    bl_description = "Hides the interface toolbars and maximizes the viewport for an alternative fullscreen"
    
    # Shows or hides the interface to full screen
    def execute(self, context):
        space = bpy.context.space_data

        # Find 3D View area
        #if space.show_region_header or space.show_region_ui or space.show_region_toolbar:
        if space.show_region_header:
            bpy.ops.screen.screen_full_area()

            # When you toggle fullscreen, also toggle `is_fullscreen`
    
            #print("Set is_fullscreen True")

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':

                    # Update space reference after screen change
                    space = area.spaces.active

                    space.show_region_header = False
                    space.show_region_ui = False
                    space.show_region_toolbar = False

                    space.overlay.show_overlays = False
                    space.shading.type = 'RENDERED'
                    space.show_gizmo = False
                    #space.view_all(center=False)
        else:
            bpy.ops.screen.screen_full_area()

            #print("Set is_fullscreen False")
            
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':

                    # Update space reference after screen change
                    space = area.spaces.active

                    space.show_region_header = True
                    space.show_region_ui = True
                    space.show_region_toolbar = True

                    space.overlay.show_overlays = True
                    #space.shading.type = 'RENDERED'
                    space.show_gizmo = True

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
        # Add a button that calls the operator

        # Math From Box
        box = layout.box()
        col = box.column(align=True)      
        
        col.label(text="Slides:")
        layout.use_property_split = False

        row = col.row(align = True)
        row.operator("screen.play_back_animation", icon="PREV_KEYFRAME")
        row.operator("screen.play_animation", icon="NEXT_KEYFRAME")
                
        row = layout.row()
        layout.operator("scene.setup_slide_scene", icon="ADD")
        layout.operator("screen.remove_stop", icon="FLIP")
        layout.operator("screen.hide_interface", icon="BOX_HIDE")



############ REGISTRY ############

# Register the classes
classes = [
    VIEW_OT_SlideSetupOperator,
    VIEW_OT_PlayAnimationOperator,
    VIEW_OT_ReverseAnimationOperator,
    VIEW_OT_RemoveAnimationOperator,
    VIEW_OT_HideInterface,
    VIEW_PT_PlayAnimationPanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


    if stop_playback in bpy.app.handlers.frame_change_post:
        print("Handler is appended.")
        bpy.app.handlers.frame_change_post.remove(stop_playback)
        print("Handler removed.")
        #handler_added = True
    else:
        print("Handler is not appended.")
        #handler_added = False

# Run the register function when the script is executed
if __name__ == "__main__":
    register()
