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
    "version": (0, 4, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > View > Presentation Slider",
    "description": "Add controls to switch to the next Scene then plays the animation once using built-in STOP_END_FRAME mode, useful for presentation slides setup as Scenes",
    "warning": "",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "support": "OFFICIAL",
    "category": "Bforartists",
}


import bpy
import re
from mathutils import Vector

from bpy.types import Operator, Panel, PropertyGroup
from bpy.utils import register_class, unregister_class
from bpy.props import (
    IntProperty,
    PointerProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
)


class SlideSettings(PropertyGroup):
    frame_range: IntProperty(
        name="Duration",
        description="Number of frames for each slide",
        default=30,
        min=1,
        soft_max=300
    )

    # Camera Transition Settings
    camera_transition: BoolProperty(
        name="Camera Transition",
        description="Enable automatic camera transition animation between slides",
        default=True,
    )

    camera_ease_in: EnumProperty(
        name="Ease In",
        description="Easing type at the end of the camera transition (arrival)",
        items=[
            ('EASE_IN', "Ease In", "Slow at end"),
            ('EASE_OUT', "Ease Out", "Slow at start"),
            ('EASE_IN_OUT', "Ease In & Out", "Slow at both ends"),
            ('LINEAR', "Linear", "Constant speed"),
        ],
        default='EASE_IN_OUT',
    )

    camera_ease_out: EnumProperty(
        name="Ease Out",
        description="Easing type at the start of the camera transition (departure)",
        items=[
            ('EASE_OUT', "Ease Out", "Slow at start"),
            ('EASE_IN', "Ease In", "Slow at end"),
            ('EASE_IN_OUT', "Ease In & Out", "Slow at both ends"),
            ('LINEAR', "Linear", "Constant speed"),
        ],
        default='EASE_IN_OUT',
    )

    transition_distance: FloatProperty(
        name="Default Distance",
        description="Default distance for new slide POS empties when using auto-positioning",
        default=20.0,
        min=0.1,
        soft_max=100.0,
    )

    new_slide_direction: EnumProperty(
        name="New Slide Direction",
        description="Direction to place the new slide's camera position relative to previous",
        items=[
            ('CUSTOM', "Custom (Manual)", "User positions the empty manually"),
            ('RIGHT', "Right", "Camera moves right"),
            ('LEFT', "Left", "Camera moves left"),
            ('UP', "Up", "Camera moves up"),
            ('DOWN', "Down", "Camera moves down"),
            ('FORWARD', "Forward (Zoom In)", "Camera moves forward"),
            ('BACKWARD', "Backward (Zoom Out)", "Camera moves backward"),
        ],
        default='CUSTOM',
    )

def register_properties():
    bpy.utils.register_class(SlideSettings)
    bpy.types.Scene.slide_settings = PointerProperty(type=SlideSettings)

def unregister_properties():
    del bpy.types.Scene.slide_settings
    bpy.utils.unregister_class(SlideSettings)




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


# ---------------------------------------------------------------------------
# Camera Transition System – POS (Position) Empty helpers
# ---------------------------------------------------------------------------

def get_pos_empty_name(slide_name):
    """Return the POS empty name for a given slide name e.g. 'S000' -> 'S000_POS'."""
    return f"{slide_name}_POS"


def find_or_create_pos_empty(slide_scene, slide_collection, slide_name):
    """Find existing POS empty in the slide collection, or create one at origin.
    Returns the empty object.
    """
    pos_name = get_pos_empty_name(slide_name)
    # Look in the slide collection first
    if slide_collection:
        for obj in slide_collection.objects:
            if obj.name == pos_name and obj.type == 'EMPTY':
                return obj
    # Look in all data objects
    empty = bpy.data.objects.get(pos_name)
    if empty and empty.type == 'EMPTY':
        # Make sure it's linked to the slide collection
        if slide_collection and pos_name not in [o.name for o in slide_collection.objects]:
            slide_collection.objects.link(empty)
        return empty
    # Create a new one
    empty = bpy.data.objects.new(pos_name, None)
    empty.empty_display_type = 'ARROWS'
    empty.empty_display_size = 2.0
    if slide_collection:
        slide_collection.objects.link(empty)
    return empty


def get_pos_for_slide(slide_name):
    """Get the POS empty's world location for a slide, or None if missing."""
    pos_name = get_pos_empty_name(slide_name)
    obj = bpy.data.objects.get(pos_name)
    if obj:
        return obj.matrix_world.translation.copy(), obj.matrix_world.to_euler().copy()
    return None, None


def animation_data_clear(obj):
    """Safely clear all animation data from an object."""
    if obj.animation_data:
        obj.animation_data_clear()


def fcurve_set_easing(action, data_path_base, index, frame, easing_type, interpolation='BEZIER'):
    """Set the easing type and interpolation for a keyframe on an fcurve."""
    for fc in action.fcurves:
        if fc.data_path == data_path_base and fc.array_index == index:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:  # tolerance
                    kp.interpolation = interpolation
                    if interpolation == 'BEZIER':
                        kp.easing = easing_type
                        kp.handle_left_type = 'AUTO_CLAMPED'
                        kp.handle_right_type = 'AUTO_CLAMPED'
                    return True
    return False


def fcurve_apply_easing(action, data_path_base, start_frame, end_frame, easing_start, easing_end):
    """Apply easing to the first and last keyframe of an fcurve."""
    for fc in action.fcurves:
        if fc.data_path == data_path_base:
            kps = fc.keyframe_points
            if len(kps) >= 2:
                # Start keyframe (ease-away)
                kps[0].interpolation = 'BEZIER'
                kps[0].easing = easing_start
                kps[0].handle_left_type = 'AUTO_CLAMPED'
                kps[0].handle_right_type = 'AUTO_CLAMPED'
                # End keyframe (ease-into)
                kps[-1].interpolation = 'BEZIER'
                kps[-1].easing = easing_end
                kps[-1].handle_left_type = 'AUTO_CLAMPED'
                kps[-1].handle_right_type = 'AUTO_CLAMPED'


def bake_slide_camera_transition(scene, slide_name, prev_slide_name,
                                  frame_start, frame_end,
                                  easing_in='EASE_IN_OUT', easing_out='EASE_IN_OUT',
                                  direction=None, default_distance=20.0):
    """Bake camera transition from previous slide's POS empty to this slide's POS empty.
    
    The camera uses constraints (Copy Location + Copy Rotation) targeting the previous
    slide's POS empty, and the influence of those constraints is animated from 1.0 -> 0.0,
    while a second pair of constraints targeting this slide's POS empty is animated 0.0 -> 1.0,
    creating a smooth blend between the two positions.
    
    If the current slide has no POS empty, one will be created following `direction`.
    """
    cam = scene.camera
    if not cam:
        return

    prev_pos_name = get_pos_empty_name(prev_slide_name)
    curr_pos_name = get_pos_empty_name(slide_name)

    prev_pos = bpy.data.objects.get(prev_pos_name)
    curr_pos = bpy.data.objects.get(curr_pos_name)

    # Safety – ensure both empties exist
    if not prev_pos:
        print(f"  ⚠️ No POS empty for '{prev_slide_name}', camera transition skipped.")
        return

    # Find or create the current slide's POS empty
    slide_coll_name = slide_name
    slide_coll = bpy.data.collections.get(slide_coll_name)
    if not curr_pos:
        curr_pos = find_or_create_pos_empty(scene, slide_coll, slide_name)
        # Apply default offset based on direction
        if direction and direction != 'CUSTOM':
            offsets = {
                'RIGHT': (default_distance, 0, 0),
                'LEFT': (-default_distance, 0, 0),
                'UP': (0, 0, default_distance),
                'DOWN': (0, 0, -default_distance),
                'FORWARD': (0, default_distance, 0),
                'BACKWARD': (0, -default_distance, 0),
            }
            offset = offsets.get(direction, (default_distance, 0, 0))
            prev_loc = prev_pos.matrix_world.translation
            curr_pos.location = prev_loc + Vector(offset)
            curr_pos.rotation_euler = prev_pos.matrix_world.to_euler().copy()
        elif direction == 'CUSTOM' and curr_pos.location.length < 0.001:
            # If custom and at origin, just put it slightly to the right as a hint
            prev_loc = prev_pos.matrix_world.translation
            curr_pos.location = prev_loc + Vector((default_distance, 0, 0))
            curr_pos.rotation_euler = prev_pos.matrix_world.to_euler().copy()

    # Make sure both empties are tracked by the scene
    for e in [prev_pos, curr_pos]:
        if e and e.name not in [o.name for o in scene.collection.objects]:
            scene.collection.objects.link(e)

    # ---- Clear existing constraints and animation on camera ----
    # Remove all constraints from the camera
    cam.constraints.clear()
    animation_data_clear(cam)

    # ---- Build constraint pairs ----
    # From_Prev: Copy Location + Copy Rotation from PREV slide's POS (influence 1→0)
    from_loc = cam.constraints.new(type='COPY_LOCATION')
    from_loc.name = f"TRANS_FROM_{prev_slide_name}"
    from_loc.target = prev_pos
    from_loc.use_x = True
    from_loc.use_y = True
    from_loc.use_z = True
    from_loc.target_space = 'WORLD'
    from_loc.owner_space = 'WORLD'

    from_rot = cam.constraints.new(type='COPY_ROTATION')
    from_rot.name = f"TRANS_FROM_{prev_slide_name}_ROT"
    from_rot.target = prev_pos
    from_rot.use_x = True
    from_rot.use_y = True
    from_rot.use_z = True
    from_rot.target_space = 'WORLD'
    from_rot.owner_space = 'WORLD'
    from_rot.mix_mode = 'REPLACE'

    # To_Curr: Copy Location + Copy Rotation from CURRENT slide's POS (influence 0→1)
    to_loc = cam.constraints.new(type='COPY_LOCATION')
    to_loc.name = f"TRANS_TO_{slide_name}"
    to_loc.target = curr_pos
    to_loc.use_x = True
    to_loc.use_y = True
    to_loc.use_z = True
    to_loc.target_space = 'WORLD'
    to_loc.owner_space = 'WORLD'

    to_rot = cam.constraints.new(type='COPY_ROTATION')
    to_rot.name = f"TRANS_TO_{slide_name}_ROT"
    to_rot.target = curr_pos
    to_rot.use_x = True
    to_rot.use_y = True
    to_rot.use_z = True
    to_rot.target_space = 'WORLD'
    to_rot.owner_space = 'WORLD'
    to_rot.mix_mode = 'REPLACE'

    # ---- Keyframe the influence ----
    # Frame A: FROM=1.0, TO=0.0  (camera at previous slide's position)
    scene.frame_set(frame_start)
    from_loc.influence = 1.0
    from_loc.keyframe_insert(data_path="influence", frame=frame_start)
    from_rot.influence = 1.0
    from_rot.keyframe_insert(data_path="influence", frame=frame_start)
    to_loc.influence = 0.0
    to_loc.keyframe_insert(data_path="influence", frame=frame_start)
    to_rot.influence = 0.0
    to_rot.keyframe_insert(data_path="influence", frame=frame_start)

    # Frame B: FROM=0.0, TO=1.0  (camera at current slide's position)
    scene.frame_set(frame_end)
    from_loc.influence = 0.0
    from_loc.keyframe_insert(data_path="influence", frame=frame_end)
    from_rot.influence = 0.0
    from_rot.keyframe_insert(data_path="influence", frame=frame_end)
    to_loc.influence = 1.0
    to_loc.keyframe_insert(data_path="influence", frame=frame_end)
    to_rot.influence = 1.0
    to_rot.keyframe_insert(data_path="influence", frame=frame_end)

    # ---- Apply easing to all influence f-curves ----
    if cam.animation_data and cam.animation_data.action:
        action = cam.animation_data.action
        for base_path in [
            f'constraints["{from_loc.name}"].influence',
            f'constraints["{from_rot.name}"].influence',
            f'constraints["{to_loc.name}"].influence',
            f'constraints["{to_rot.name}"].influence',
        ]:
            fcurve_apply_easing(action, base_path, frame_start, frame_end,
                                easing_out, easing_in)

    print(f"  🎥 Camera transition baked: {prev_slide_name} → {slide_name} "
          f"({frame_start}-{frame_end})")


def bake_all_camera_transitions(context, from_idx=0, to_idx=None):
    """Bake camera transitions for all slides in the index range [from_idx, to_idx].
    Each slide's camera animates from the previous POS to its own POS.
    """
    s_pattern = re.compile(r"S(\d{3})")
    slides = []
    for sc in bpy.data.scenes:
        m = s_pattern.fullmatch(sc.name)
        if m:
            slides.append((int(m.group(1)), sc))
    slides.sort()

    if to_idx is None:
        to_idx = slides[-1][0] if slides else 0

    settings = context.scene.slide_settings
    easing_in = settings.camera_ease_in if settings.camera_ease_in != 'LINEAR' else 'LINEAR'
    easing_out = settings.camera_ease_out if settings.camera_ease_out != 'LINEAR' else 'LINEAR'
    # Translate LINEAR: we just use BEZIER with no custom easing (default handles)
    if easing_in == 'LINEAR':
        easing_in = 'LINEAR'
    if easing_out == 'LINEAR':
        easing_out = 'LINEAR'

    count = 0
    for idx, sc in slides:
        if idx < from_idx or idx > to_idx:
            continue
        if idx == 0:
            continue  # S000 has no previous slide to transition from
        prev_name = f"S{idx-1:03d}"
        prev_scene = bpy.data.scenes.get(prev_name)
        if not prev_scene:
            continue

        # Ensure camera is the slide's camera and exists
        if not sc.camera:
            # Try to find camera by name
            cam = bpy.data.objects.get(sc.name)
            if cam and cam.type == 'CAMERA':
                sc.camera = cam

        # Only bake if we have a camera
        if not sc.camera:
            continue

        bake_slide_camera_transition(
            scene=sc,
            slide_name=sc.name,
            prev_slide_name=prev_name,
            frame_start=sc.frame_start,
            frame_end=sc.frame_end,
            easing_in=settings.camera_ease_in if settings.camera_ease_in != 'LINEAR' else 'LINEAR',
            easing_out=settings.camera_ease_out if settings.camera_ease_out != 'LINEAR' else 'LINEAR',
            direction=settings.new_slide_direction,
            default_distance=settings.transition_distance,
        )
        count += 1

    if count == 0:
        print("  No slides to bake transitions for (need at least S000 and S001).")
    else:
        print(f"  ✅ Baked camera transitions for {count} slides.")
    return count


def rebuild_transitions_after_shift(context, old_to_new_map):
    """After slides have been renamed (shifted), rebuild transitions.
    old_to_new_map: dict mapping old_name -> new_name for shifted slides.
    All slide transitions in the affected range need rebaking.
    """
    bake_all_camera_transitions(context)


# ---------------------------------------------------------------------------
# Operators for position empty management
# ---------------------------------------------------------------------------

class VIEW_OT_SetPosEmpty(Operator):
    """Set or jump to the POS (Position) empty for the current slide"""
    bl_idname = "scene.set_pos_empty"
    bl_label = "Set Position Empty"
    bl_description = "Create or locate the Position empty for this slide"

    def execute(self, context):
        sc = context.scene
        s_pattern = re.compile(r"S(\d{3})")
        if not s_pattern.fullmatch(sc.name):
            self.report({'ERROR'}, "Current scene is not a slide (Sxxx)")
            return {'CANCELLED'}

        slide_coll = bpy.data.collections.get(sc.name)
        pos = find_or_create_pos_empty(sc, slide_coll, sc.name)

        # Select and focus on it
        bpy.ops.object.select_all(action='DESELECT')
        pos.select_set(True)
        context.view_layer.objects.active = pos

        self.report({'INFO'}, f"📍 Position empty '{pos.name}' ready at ({pos.location.x:.2f}, {pos.location.y:.2f}, {pos.location.z:.2f})")
        return {'FINISHED'}


class VIEW_OT_BakeCameraTransitions(Operator):
    """Bake camera transitions for all slides"""
    bl_idname = "scene.bake_camera_transitions"
    bl_label = "Bake All Camera Transitions"
    bl_description = "Bake camera transition animation for all slides using POS empties"

    def execute(self, context):
        count = bake_all_camera_transitions(context)
        if count > 0:
            self.report({'INFO'}, f"🎥 Baked camera transitions for {count} slides")
        else:
            self.report({'WARNING'}, "No transitions to bake. Need at least 2 slides (S000, S001).")
        return {'FINISHED'}


class VIEW_OT_SetPosDirectionPreset(Operator):
    """Set direction preset for the current slide's position empty"""
    bl_idname = "scene.set_pos_direction"
    bl_label = "Set Direction"
    bl_description = "Position the current slide's POS empty relative to the previous slide"

    direction: bpy.props.StringProperty(default='RIGHT')
    distance: bpy.props.FloatProperty(default=20.0)

    def execute(self, context):
        sc = context.scene
        s_pattern = re.compile(r"S(\d{3})")
        m = s_pattern.fullmatch(sc.name)
        if not m:
            self.report({'ERROR'}, "Current scene is not a slide.")
            return {'CANCELLED'}
        idx = int(m.group(1))
        if idx == 0:
            self.report({'ERROR'}, "S000 cannot have a direction preset (no previous slide).")
            return {'CANCELLED'}

        prev_name = f"S{idx-1:03d}"
        prev_pos_name = get_pos_empty_name(prev_name)
        prev_pos = bpy.data.objects.get(prev_pos_name)
        if not prev_pos:
            self.report({'ERROR'}, f"Previous slide '{prev_name}' has no POS empty. Create one first.")
            return {'CANCELLED'}

        slide_coll = bpy.data.collections.get(sc.name)
        pos = find_or_create_pos_empty(sc, slide_coll, sc.name)

        offsets = {
            'RIGHT': (self.distance, 0, 0),
            'LEFT': (-self.distance, 0, 0),
            'UP': (0, 0, self.distance),
            'DOWN': (0, 0, -self.distance),
            'FORWARD': (0, self.distance, 0),
            'BACKWARD': (0, -self.distance, 0),
        }
        offset = offsets.get(self.direction, (self.distance, 0, 0))
        prev_loc = prev_pos.matrix_world.translation
        pos.location = prev_loc + Vector(offset)
        pos.rotation_euler = prev_pos.matrix_world.to_euler().copy()

        self.report({'INFO'}, f"📍 Position empty '{pos.name}' set {self.direction} from '{prev_name}'")
        return {'FINISHED'}


class VIEW_OT_SelectPosEmpty(Operator):
    """Select the POS empty for the current slide and make it active"""
    bl_idname = "scene.select_pos_empty"
    bl_label = "Select Position Empty"
    bl_description = "Select the Position empty for this slide"

    def execute(self, context):
        sc = context.scene
        pos_name = get_pos_empty_name(sc.name)
        pos = bpy.data.objects.get(pos_name)
        if not pos:
            self.report({'ERROR'}, f"No POS empty found for '{sc.name}'.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        pos.select_set(True)
        context.view_layer.objects.active = pos

        # Focus view on it
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                override = {'area': area, 'region': area.regions[-1]}
                bpy.ops.view3d.view_selected(override)
                break

        return {'FINISHED'}


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
            # -- Create POS empty for S000
            pos_empty = find_or_create_pos_empty(new_scene, slide_coll, base_scene_name)
            pos_empty.location = (0, 0, 0)
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
            # SHIFT UP: from highest down to insert_idx, shift scene & collection & camera & POS names
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
                    old_pos_empty = bpy.data.objects.get(get_pos_empty_name(f"S{idx:03d}"))

                    scene.name = new_scenename

                    # Rename corresponding slide collection
                    if old_collection and f"S{new_index:03d}" not in bpy.data.collections:
                        old_collection.name = f"S{new_index:03d}"
                    # Rename camera object (if present and safe)
                    if old_camera and f"S{new_index:03d}" not in bpy.data.objects:
                        old_camera.name = f"S{new_index:03d}"
                    # Rename POS empty (if present and safe)
                    new_pos_name = get_pos_empty_name(f"S{new_index:03d}")
                    if old_pos_empty and new_pos_name not in bpy.data.objects:
                        old_pos_empty.name = new_pos_name

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

        # ---- Camera transition: create POS empty and bake animation ----
        if context.scene.slide_settings.camera_transition:
            # Find or create POS empty for the new slide
            pos = find_or_create_pos_empty(new_scene, new_slide_coll, new_slide_name)

            # Apply default offset based on direction setting
            direction = context.scene.slide_settings.new_slide_direction
            if direction != 'CUSTOM':
                prev_pos = bpy.data.objects.get(get_pos_empty_name(prev_scene_name))
                if prev_pos:
                    offsets = {
                        'RIGHT': (context.scene.slide_settings.transition_distance, 0, 0),
                        'LEFT': (-context.scene.slide_settings.transition_distance, 0, 0),
                        'UP': (0, 0, context.scene.slide_settings.transition_distance),
                        'DOWN': (0, 0, -context.scene.slide_settings.transition_distance),
                        'FORWARD': (0, context.scene.slide_settings.transition_distance, 0),
                        'BACKWARD': (0, -context.scene.slide_settings.transition_distance, 0),
                    }
                    offset = offsets.get(direction, (context.scene.slide_settings.transition_distance, 0, 0))
                    prev_loc = prev_pos.matrix_world.translation
                    pos.location = prev_loc + Vector(offset)
                    pos.rotation_euler = prev_pos.matrix_world.to_euler().copy()

            # Bake the transition for this slide (and possibly the next slide too if it exists)
            next_scene_name = get_next_s_name(insert_idx)
            next_scene = bpy.data.scenes.get(next_scene_name)

            # Check if previous slide has a baked camera with constraints - if so, clear and rebake
            prev_sc = bpy.data.scenes.get(prev_scene_name)
            if prev_sc and prev_sc.camera and context.scene.slide_settings.camera_transition:
                # Also rebake previous slide's transition (since its end keyframes may need updating)
                prev_prev_name = f"S{insert_idx-2:03d}" if insert_idx > 1 else None
                if prev_prev_name and bpy.data.scenes.get(prev_prev_name):
                    bake_slide_camera_transition(
                        scene=prev_sc,
                        slide_name=prev_sc.name,
                        prev_slide_name=prev_prev_name,
                        frame_start=prev_sc.frame_start,
                        frame_end=prev_sc.frame_end,
                        easing_in=context.scene.slide_settings.camera_ease_in,
                        easing_out=context.scene.slide_settings.camera_ease_out,
                    )

            # Bake the new slide's transition
            bake_slide_camera_transition(
                scene=new_scene,
                slide_name=new_slide_name,
                prev_slide_name=prev_scene_name,
                frame_start=new_scene.frame_start,
                frame_end=new_scene.frame_end,
                easing_in=context.scene.slide_settings.camera_ease_in,
                easing_out=context.scene.slide_settings.camera_ease_out,
            )

            # If there's a next scene after us, rebake its transition too (it now points to us)
            if next_scene and next_scene.camera:
                bake_slide_camera_transition(
                    scene=next_scene,
                    slide_name=next_scene.name,
                    prev_slide_name=new_slide_name,
                    frame_start=next_scene.frame_start,
                    frame_end=next_scene.frame_end,
                    easing_in=context.scene.slide_settings.camera_ease_in,
                    easing_out=context.scene.slide_settings.camera_ease_out,
                )

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
    bl_description = "Plays the next slide as the next Scene\nUses built-in STOP_END_FRAME mode for automatic stop"

    def execute(self, context):
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        # Set the current frame to the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)
        
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

        # Set playback mode to STOP_END_FRAME for automatic stop
        context.scene.playback_loop_mode = 'STOP_END_FRAME'
            
        # Start playback
        bpy.ops.screen.animation_play()

        return {'FINISHED'}


class VIEW_OT_ReverseAnimationOperator(Operator):
    """Plays the previous slide scene and its animation"""
    bl_idname = "screen.play_back_animation"
    bl_label = "Previous"
    bl_description = "Plays the previous slide as the last Scene\nUses built-in STOP_END_FRAME mode for automatic stop"

    def execute(self, context):
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        # Set the current frame to the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)

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

        # Set playback mode to STOP_END_FRAME for automatic stop
        context.scene.playback_loop_mode = 'STOP_END_FRAME'
            
        # Start playback
        bpy.ops.screen.animation_play()

        return {'FINISHED'}

class VIEW_OT_RemoveAnimationOperator(Operator):
    """Play animation for current scene with auto-stop"""
    bl_idname = "screen.remove_stop"
    bl_label = "Play Current Slide"
    bl_description = "Plays animation for the current scene with automatic stop at the end\nUses built-in STOP_END_FRAME mode"

    def execute(self, context):
        # If the timeline is playing, pause it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        # Set the current frame to the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.screen.frame_jump(end=False)

        # Set playback mode to STOP_END_FRAME for automatic stop
        context.scene.playback_loop_mode = 'STOP_END_FRAME'
            
        # Start playback
        bpy.ops.screen.animation_play()

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
        settings = context.scene.slide_settings

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
        row.prop(settings, "frame_range", text="Duration")

        # ---- Camera Transition Section ----
        layout.separator()
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Camera Transition:", icon="CAMERA_DATA")

        row = col.row(align=True)
        row.prop(settings, "camera_transition", text="Enabled")

        if settings.camera_transition:
            col.separator()
            row = col.row(align=True)
            row.prop(settings, "camera_ease_in", text="Ease In")
            row = col.row(align=True)
            row.prop(settings, "camera_ease_out", text="Ease Out")

            col.separator()
            row = col.row(align=True)
            row.prop(settings, "new_slide_direction", text="Direction")
            row = col.row(align=True)
            row.prop(settings, "transition_distance", text="Distance")

            col.separator()
            # Position empty tools
            row = col.row(align=True)
            row.operator("scene.set_pos_empty", text="Edit POS", icon="EMPTY_ARROWS")
            row.operator("scene.select_pos_empty", text="Select POS", icon="RESTRICT_SELECT_OFF")

            # Direction presets row
            col.separator()
            row = col.row(align=True)
            row.scale_y = 0.8
            row.operator("scene.set_pos_direction", text="→ Right", icon="TRIA_RIGHT").direction = 'RIGHT'
            row.operator("scene.set_pos_direction", text="← Left", icon="TRIA_LEFT").direction = 'LEFT'
            row = col.row(align=True)
            row.scale_y = 0.8
            row.operator("scene.set_pos_direction", text="↑ Up", icon="TRIA_UP").direction = 'UP'
            row.operator("scene.set_pos_direction", text="↓ Down", icon="TRIA_DOWN").direction = 'DOWN'
            row = col.row(align=True)
            row.scale_y = 0.8
            row.operator("scene.set_pos_direction", text="+ Zoom In", icon="ADD").direction = 'FORWARD'
            row.operator("scene.set_pos_direction", text="− Zoom Out", icon="REMOVE").direction = 'BACKWARD'

            col.separator()
            # Bake all button
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("scene.bake_camera_transitions", text="Bake All Transitions", icon="ACTION_TWEAK")

        layout.separator()

        # Presentation View Button (with custom style)
        row = layout.row()
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
]

def register():
    register_properties()

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _presentation_view_active
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_properties()

    # Reset presentation view state
    _presentation_view_active = False


# Run the register function when the script is executed
if __name__ == "__main__":
    register()
