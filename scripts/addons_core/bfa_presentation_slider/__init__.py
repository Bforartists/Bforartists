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
    bl_description = "Sets up a new slide scene/collection/camera structure, or duplicates current slide scene"

    frame_range: IntProperty(
        name="Duration",
        description="Number of frames for each slide",
        default=30,
        min=1,
        soft_max=300
    )

    def execute(self, context):
        base_scene_name = "S000"
        base_collection_name = "SET"

        def create_slide_camera(collection, cam_name):
            cam_obj = bpy.data.objects.get(cam_name)
            if not cam_obj:
                cam_data = bpy.data.cameras.new(cam_name)
                cam_obj = bpy.data.objects.new(cam_name, cam_data)
                cam_obj.location = (0, 0, 0)
                collection.objects.link(cam_obj)
                self.report({'INFO'}, f"🎥 Created camera '{cam_name}' in '{collection.name}'")
            elif cam_obj.name not in [o.name for o in collection.objects]:
                collection.objects.link(cam_obj)
                self.report({'INFO'}, f"🎥 Linked existing camera '{cam_name}' to '{collection.name}'")
            return cam_obj

        # ======= 1. SETUP S000 ===========
        if base_scene_name not in bpy.data.scenes:
            new_scene = bpy.data.scenes.new(base_scene_name)
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
                self.report({'INFO'}, f"📁 Created new SET collection '{base_collection_name}'")
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
                self.report({'INFO'}, f"📦 Created slide collection '{slide_coll_name}'")
            else:
                if slide_coll.name not in [c.name for c in new_scene.collection.children]:
                    new_scene.collection.children.link(slide_coll)
            # -- Setup SET and Slide links
            if set_coll.name not in [c.name for c in new_scene.collection.children]:
                new_scene.collection.children.link(set_coll)
            if slide_coll.name not in [c.name for c in new_scene.collection.children]:
                new_scene.collection.children.link(slide_coll)
            # -- Add camera named S000 in S000 collection
            cam_obj = create_slide_camera(slide_coll, slide_coll_name)
            new_scene.camera = cam_obj
            # -- Set frame range
            new_scene.frame_start = 1
            new_scene.frame_end = self.frame_range
            self.report({'INFO'}, f"✅ Initial slide '{base_scene_name}' ready.")
            return {'FINISHED'}

        # ======= 2. INSERT SLIDE SCENE (SEQUENTIALLY, shifting higher) ===========
        # Identify where to insert: the current selected Sxxx scene
        current_scene = context.scene
        s_pattern = re.compile(r"S(\d{3})")
        current_match = s_pattern.fullmatch(current_scene.name)
        if not current_match:
            self.report({'ERROR'}, "Current scene is not a slide (Sxxx). Select a slide scene to insert after!")
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
                        self.report({'WARNING'}, f"Scene '{new_scenename}' already exists, skipping shift.")
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
            self.report({'ERROR'}, "Couldn't find S000 for duplication.")
            return {'CANCELLED'}
        new_slide_name = get_next_s_name(insert_idx)
        new_scene = src_scene.copy()
        new_scene.name = new_slide_name
        bpy.context.window.scene = new_scene
        new_scene.frame_start = 1
        new_scene.frame_end = self.frame_range
        # Remove S000 from children of new scene
        for coll in list(new_scene.collection.children):
            if coll.name == base_scene_name:
                new_scene.collection.children.unlink(coll)
                self.report({'INFO'}, f"🧹 Unlinked '{base_scene_name}' collection from new scene '{new_slide_name}'")
                break
        # Create new slide collection with appropriate name/color, link to new scene
        new_slide_coll = bpy.data.collections.get(new_slide_name)
        if new_slide_coll is None:
            new_slide_coll = bpy.data.collections.new(new_slide_name)
            new_slide_coll.color_tag = 'COLOR_02'
            new_scene.collection.children.link(new_slide_coll)
            self.report({'INFO'}, f"📦 Created new slide collection '{new_slide_name}'")
        else:
            if new_slide_coll.name not in [c.name for c in new_scene.collection.children]:
                new_scene.collection.children.link(new_slide_coll)
                self.report({'INFO'}, f"🔁 Linked existing collection '{new_slide_coll.name}'")
        # Add new camera for this slide (named slide)
        cam_obj = create_slide_camera(new_slide_coll, new_slide_name)
        new_scene.camera = cam_obj
        self.report({'INFO'}, f"✅ Inserted slide '{new_slide_name}' with new collection & camera, scenes updated!")
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
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Math From Box (Slides and playback control)
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Slides:")

        row = col.row(align=True)
        row.operator("screen.play_back_animation", icon="PREV_KEYFRAME")
        row.operator("screen.play_animation", icon="NEXT_KEYFRAME")

        # Big button for Insert Slide
        row = layout.row()
        row.scale_y = 2.0
        row.operator("scene.setup_slide_scene", icon="ADD")

        # Property field for frames
        row = layout.row()
        row.scale_y = 1.0
        row.prop(context.scene, "frame_end", text="Duration")

        # Spacer/break
        layout.separator()

        # Full width Loop Animation button
        row = layout.row()
        row.scale_y = 1
        row.operator("screen.remove_stop", icon="FLIP")

        # Full width Hide Interface button
        row = layout.row()
        row.operator("screen.hide_interface", icon="BOX_HIDE")




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
