bl_info = {
    "name": "Presentation Slider",
    "author": "Draise (@trinumedia)",
    "version": (0, 3, 7),
    "blender": (3, 6, 2),
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
        layout.operator("screen.remove_stop", icon="FLIP")
        layout.operator("screen.hide_interface", icon="BOX_HIDE")



############ REGISTRY ############

# Register the classes
def register():
    bpy.utils.register_class(VIEW_OT_PlayAnimationOperator)
    bpy.utils.register_class(VIEW_OT_ReverseAnimationOperator)
    bpy.utils.register_class(VIEW_OT_RemoveAnimationOperator)
    bpy.utils.register_class(VIEW_OT_HideInterface)
    bpy.utils.register_class(VIEW_PT_PlayAnimationPanel)

# Unregister the classes
def unregister():
    bpy.utils.unregister_class(VIEW_OT_PlayAnimationOperator)
    bpy.utils.unregister_class(VIEW_OT_ReverseAnimationOperator)
    bpy.utils.unregister_class(VIEW_OT_RemoveAnimationOperator)
    bpy.utils.unregister_class(VIEW_OT_HideInterface)
    bpy.utils.unregister_class(VIEW_PT_PlayAnimationPanel)

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
