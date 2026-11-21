"""BoneCraft Phase 2 — Graph & Viewport Tools.

Breakdowner modal, delta mover, and inline graph editor controls
(tangent types, handle type toggle, buffer curves, euler filter,
smart bake).

v3.0.26: Onion skinning overlay removed — it was an animation-centric
feature and BoneCraft is a rigging-focused addon.  Blender's native
Overlays → Motion Paths (or the built-in Ghost option on the armature
display) cover the same workflow.
"""

import math

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    PointerProperty,
)

from boneforge.i18n import T
from mathutils import Vector

from boneforge.core import active_armature, addon_prefs

import logging

logger = logging.getLogger(__name__)


# ── Constants ──────────────────────────────────────────────────

# ZEN-2 fix: Drag this many pixels to sweep from 0 % to 100 % blend
_BREAKDOWNER_PIXEL_RANGE: float = 400.0

# ── Module-level transient state ────────────────────────────────

# Buffer curves: {(action_name, data_path, array_index): [(frame, value, ...)]}
_curve_buffer: dict = {}

# Keymaps for cleanup
addon_keymaps: list = []


# ── PropertyGroups ──────────────────────────────────────────────

class BF_DeltaMoverSettings(bpy.types.PropertyGroup):
    """Session-scoped delta mover parameters on WindowManager."""
    offset_x: FloatProperty(
        name="X Offset",
        description="Screen-space horizontal offset in pixels",
        default=0.0,
    )
    offset_y: FloatProperty(
        name="Y Offset",
        description="Screen-space vertical offset in pixels",
        default=0.0,
    )
    uniform: BoolProperty(
        name="Uniform Nudge",
        description="Apply the same delta to all selected bones",
        default=True,
    )
    world_units: BoolProperty(
        name="World Units",
        description="Interpret offset values as world units instead of pixels",
        default=False,
    )


# ── Breakdowner helpers ────────────────────────────────────────

def _find_neighbor_keys(fcurve, frame):
    """Return (prev_key, next_key) surrounding *frame*."""
    prev_kf = None
    next_kf = None
    for kf in fcurve.keyframe_points:
        if kf.co.x < frame:
            if prev_kf is None or kf.co.x > prev_kf.co.x:
                prev_kf = kf
        elif kf.co.x > frame:
            if next_kf is None or kf.co.x < next_kf.co.x:
                next_kf = kf
    return prev_kf, next_kf


def _action_fcurves(action):
    """F-curves across legacy and layered (Blender 4.4+/5.x) action APIs.

    Blender 5 removed ``Action.fcurves``: curves live in
    ``layers[].strips[].channelbags[].fcurves``.
    """
    if action is None:
        return []
    layers = getattr(action, "layers", None)
    if layers:
        fcurves = []
        for layer in layers:
            for strip in layer.strips:
                for bag in getattr(strip, "channelbags", []):
                    fcurves.extend(bag.fcurves)
        if fcurves:
            return fcurves
    return list(getattr(action, "fcurves", []))


def _bone_fcurves(action, bone_name):
    """Yield FCurves belonging to *bone_name*."""
    prefix = f'pose.bones["{bone_name}"].'
    for fc in _action_fcurves(action):
        if fc.data_path.startswith(prefix):
            yield fc


def _property_from_data_path(pbone, data_path):
    """Extract the property attribute (location, rotation_*, scale) from an FCurve data_path.

    Returns the property array on the pose bone, or None.
    """
    # data_path is like: pose.bones["BoneName"].location
    parts = data_path.rsplit('.', 1)
    if len(parts) < 2:
        return None
    prop_name = parts[1]
    return getattr(pbone, prop_name, None)


def _is_base_locked(context):
    """Legacy hook — always False since anim_layers was removed in v3.0.16."""
    return False


# ── Operators — Breakdowner ─────────────────────────────────────

class BF_OT_Breakdowner(bpy.types.Operator):
    """Interactive breakdown pose creation with mouse-driven blending"""
    bl_idname = "boneforge.breakdowner"
    bl_label = "Breakdowner"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        return (context.mode == 'POSE'
                and arm.animation_data is not None
                and arm.animation_data.action is not None
                and context.selected_pose_bones)

    def invoke(self, context, event):
        # SIG-2: Check lock_base before proceeding
        if _is_base_locked(context):
            self.report({'WARNING'}, "Base action is locked — unlock to use breakdowner")
            return {'CANCELLED'}

        arm = active_armature(context)

        # SIG-2 fix: re-validate animation data in case it was removed
        # between poll() and invoke()
        if arm.animation_data is None or arm.animation_data.action is None:
            self.report({'WARNING'}, "Animation data was removed — cannot create breakdown")
            return {'CANCELLED'}

        action = arm.animation_data.action
        frame = context.scene.frame_current

        # Store the original frame so it can be restored on cancel
        self._original_frame = context.scene.frame_current

        # SIG-1: Store bone names at invoke time for reliable cancel
        self._bone_names = [pb.name for pb in context.selected_pose_bones]

        # Collect neighbor data per bone per fcurve
        self._bone_data = {}  # {bone_name: {(data_path, idx): (prev_val, next_val, current_val)}}
        self._original_transforms = {}  # {bone_name: (loc, rot_q, rot_e, rot_aa, scale)}

        has_neighbors = False
        for pbone in context.selected_pose_bones:
            self._original_transforms[pbone.name] = (
                pbone.location.copy(),
                pbone.rotation_quaternion.copy(),
                pbone.rotation_euler.copy(),
                pbone.rotation_axis_angle[:],
                pbone.scale.copy(),
            )
            bone_curves = {}
            for fc in _bone_fcurves(action, pbone.name):
                prev_kf, next_kf = _find_neighbor_keys(fc, frame)
                if prev_kf is not None and next_kf is not None:
                    current = fc.evaluate(frame)
                    bone_curves[(fc.data_path, fc.array_index)] = (
                        prev_kf.co.y, next_kf.co.y, current
                    )
                    has_neighbors = True
            self._bone_data[pbone.name] = bone_curves

        if not has_neighbors:
            self.report({'INFO'}, "No neighboring keyframes — cannot create breakdown")
            return {'CANCELLED'}

        self._start_x = event.mouse_x
        self._blend = 0.5

        context.window_manager.modal_handler_add(self)
        # CRIT-1 fix: guard context.area before header_text_set
        if context.area is not None:
            context.area.header_text_set("Breakdowner: 50% | LMB/Enter: Confirm | RMB/Esc: Cancel")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            dx = event.mouse_x - self._start_x
            # ZEN-2 fix: extract magic number
            self._blend = max(0.0, min(1.0, 0.5 + dx / _BREAKDOWNER_PIXEL_RANGE))
            self._apply_blend(context)
            # CRIT-1 fix: guard context.area
            if context.area is not None:
                context.area.header_text_set(
                    f"Breakdowner: {self._blend * 100:.0f}% | "
                    "LMB/Enter: Confirm | RMB/Esc: Cancel"
                )
            return {'RUNNING_MODAL'}

        if event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            # Confirm — insert breakdown keys
            self._insert_breakdown_keys(context)
            # CRIT-1 fix: guard context.area
            if context.area is not None:
                context.area.header_text_set(None)
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            # Cancel — restore original transforms and frame position
            self._restore_original(context)
            context.scene.frame_set(self._original_frame)
            # CRIT-1 fix: guard context.area
            if context.area is not None:
                context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def _apply_blend(self, context):
        """Interpolate each tracked bone's transform channels toward the next keyframe.

        Writes ``prev + (next - prev) * self._blend`` to every tracked
        property for a live preview during the modal breakdowner.
        """
        arm = active_armature(context)
        t = self._blend
        # SIG-1: Iterate stored bone names, not current selection
        for bname in self._bone_names:
            pbone = arm.pose.bones.get(bname)
            if pbone is None:
                continue
            curves = self._bone_data.get(bname, {})
            for (data_path, array_index), (prev_val, next_val, _) in curves.items():
                val = prev_val + (next_val - prev_val) * t
                # Write directly to pose bone property instead of path_resolve
                prop = _property_from_data_path(pbone, data_path)
                if prop is not None and hasattr(prop, '__setitem__'):
                    try:
                        prop[array_index] = val
                    except (IndexError, TypeError) as exc:
                        logger.debug("./animation/graph_tools.py suppressed (IndexError, TypeError): %s", exc)
        context.view_layer.update()

    def _restore_original(self, context):
        """Revert every tracked bone back to its pre-modal transform.

        Called when the modal breakdowner is cancelled so the scene state
        matches what the user saw before invoking the operator.
        """
        arm = active_armature(context)
        # SIG-1: Iterate stored bone names, not current selection
        for bname in self._bone_names:
            pbone = arm.pose.bones.get(bname)
            if pbone is None:
                continue
            orig = self._original_transforms.get(bname)
            if orig is not None:
                pbone.location = orig[0]
                pbone.rotation_quaternion = orig[1]
                pbone.rotation_euler = orig[2]
                pbone.rotation_axis_angle = orig[3]
                pbone.scale = orig[4]
        context.view_layer.update()

    def _insert_breakdown_keys(self, context):
        """Commit the current blend as breakdown keyframes at the playhead.

        For each tracked bone property, inserts a keyframe at the
        current frame using the interpolated value produced by
        ``_apply_blend``.
        """
        arm = active_armature(context)
        action = arm.animation_data.action
        frame = context.scene.frame_current
        # SIG-1: Iterate stored bone names, not current selection
        for bname in self._bone_names:
            pbone = arm.pose.bones.get(bname)
            if pbone is None:
                continue
            for fc in _bone_fcurves(action, bname):
                key = (fc.data_path, fc.array_index)
                if key in self._bone_data.get(bname, {}):
                    val = fc.evaluate(frame)  # Current blended value
                    kf = fc.keyframe_points.insert(frame, val, options={'FAST'})
                    kf.type = 'BREAKDOWN'
            for fc in _bone_fcurves(action, bname):
                fc.update()


# ── Operators — Delta Mover ─────────────────────────────────────

class BF_OT_DeltaMove(bpy.types.Operator):
    """Nudge selected bones in screen-space coordinates"""
    bl_idname = "boneforge.delta_move"
    bl_label = "Delta Move"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and context.selected_pose_bones)

    def execute(self, context):
        arm = active_armature(context)
        settings = context.window_manager.boneforge_delta_mover

        # CRIT-2 fix: Get the 3D viewport region with robust validation
        region = None
        rv3d = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for r in area.regions:
                    if r.type == 'WINDOW':
                        region = r
                        # CRIT-2 fix: validate spaces list before indexing
                        if area.spaces and hasattr(area.spaces[0], 'region_3d'):
                            rv3d = area.spaces[0].region_3d
                        break
                break

        if region is None or rv3d is None:
            self.report({'WARNING'}, "No valid 3D viewport found")
            return {'CANCELLED'}

        from bpy_extras.view3d_utils import (
            location_3d_to_region_2d,
            region_2d_to_location_3d,
        )

        dx = settings.offset_x
        dy = settings.offset_y
        behind_camera = False

        for pbone in context.selected_pose_bones or []:
            # World position of bone head
            head_world = arm.matrix_world @ pbone.head

            # Project to screen
            screen_co = location_3d_to_region_2d(region, rv3d, head_world)
            if screen_co is None:
                behind_camera = True
                continue

            # Check if behind camera
            view_co = rv3d.view_matrix @ head_world
            if view_co.z > 0:
                behind_camera = True

            # Apply delta
            if settings.world_units:
                # Interpret dx/dy as world units on screen-aligned axes
                view_mat = rv3d.view_matrix
                right = Vector((view_mat[0][0], view_mat[0][1], view_mat[0][2]))
                up = Vector((view_mat[1][0], view_mat[1][1], view_mat[1][2]))
                world_delta = right * dx + up * dy
            else:
                # Pixel offset → unproject
                new_screen = Vector((screen_co.x + dx, screen_co.y + dy))
                # Unproject at the same depth
                new_world = region_2d_to_location_3d(region, rv3d, new_screen, head_world)
                if new_world is None:
                    continue
                world_delta = new_world - head_world

            # Convert world delta to bone-local space
            bone_mat = arm.matrix_world @ pbone.bone.matrix_local
            local_delta = bone_mat.inverted().to_3x3() @ world_delta
            pbone.location += local_delta

        if behind_camera:
            self.report({'INFO'}, "Some bones are behind the view — results may be unexpected")

        context.view_layer.update()
        return {'FINISHED'}


# ── Operators — Tangent Tools ───────────────────────────────────

# Module-level constant for tangent handle types.
# Referenced by both BF_OT_TangentSetType and BF_PT_TangentSubPanel
# to avoid fragile annotation introspection.
TANGENT_TYPE_ITEMS = [
    ('AUTO', "Auto", "Automatic tangent handles"),
    ('VECTOR', "Vector", "Point-to-point tangent handles"),
    ('ALIGNED', "Aligned", "Aligned tangent handles"),
    ('FREE', "Free", "Independent tangent handles"),
    ('AUTO_CLAMPED', "Auto Clamped", "Auto clamped handles"),
]


class BF_OT_TangentSetType(bpy.types.Operator):
    """Set tangent handle type on selected keyframes"""
    bl_idname = "boneforge.tangent_set_type"
    bl_label = "Set Tangent Type"
    bl_options = {'REGISTER', 'UNDO'}

    type: EnumProperty(description='Handle type to set on the selected keys',
        name="Type",
        items=[
            ('AUTO', "Auto", "Automatic tangent handles"),
            ('VECTOR', "Vector", "Point-to-point tangent handles"),
            ('ALIGNED', "Aligned", "Aligned tangent handles"),
            ('FREE', "Free", "Independent tangent handles"),
            ('AUTO_CLAMPED', "Auto Clamped", "Auto clamped handles"),
        ],
    )

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action)

    def execute(self, context):
        arm = active_armature(context)
        action = arm.animation_data.action
        count = 0

        for pbone in context.selected_pose_bones or []:
            for fc in _bone_fcurves(action, pbone.name):
                for kf in fc.keyframe_points:
                    if kf.select_control_point:
                        kf.handle_left_type = self.type
                        kf.handle_right_type = self.type
                        count += 1

        if count == 0:
            self.report({'INFO'}, "No selected keyframes found")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Set {count} keyframe handles to {self.type}")
        return {'FINISHED'}


class BF_OT_TangentToggleHandleType(bpy.types.Operator):
    """Toggle between Auto and Free handle types on selected keyframes"""
    bl_idname = "boneforge.tangent_toggle_weighted"
    bl_label = "Toggle Handle Type"  # SIG-4 fix: renamed from "Toggle Weighted Tangents"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action)

    def execute(self, context):
        arm = active_armature(context)
        action = arm.animation_data.action
        count = 0

        for pbone in context.selected_pose_bones or []:
            for fc in _bone_fcurves(action, pbone.name):
                for kf in fc.keyframe_points:
                    if kf.select_control_point:
                        # Toggle between Auto and Free handle types
                        if kf.handle_left_type in {'AUTO', 'AUTO_CLAMPED'}:
                            kf.handle_left_type = 'FREE'
                            kf.handle_right_type = 'FREE'
                        else:
                            kf.handle_left_type = 'AUTO'
                            kf.handle_right_type = 'AUTO'
                        count += 1

        if count == 0:
            self.report({'INFO'}, "No selected keyframes found")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Toggled handle type on {count} keyframes")
        return {'FINISHED'}


# ── Operators — Buffer Curves ───────────────────────────────────

class BF_OT_BufferCapture(bpy.types.Operator):
    """Capture current animation curves to the buffer for comparison"""
    bl_idname = "boneforge.buffer_capture"
    bl_label = "Capture Buffer"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action)

    def execute(self, context):
        global _curve_buffer
        arm = active_armature(context)
        action = arm.animation_data.action
        _curve_buffer.clear()

        count = 0
        for pbone in context.selected_pose_bones or []:
            for fc in _bone_fcurves(action, pbone.name):
                key = (action.name, fc.data_path, fc.array_index)
                keyframes = []
                for kf in fc.keyframe_points:
                    keyframes.append((
                        kf.co.x, kf.co.y,
                        tuple(kf.handle_left), tuple(kf.handle_right),
                        kf.interpolation,
                        kf.handle_left_type, kf.handle_right_type,
                    ))
                _curve_buffer[key] = keyframes
                count += 1

        self.report({'INFO'}, f"Captured {count} curves to buffer")
        return {'FINISHED'}


class BF_OT_BufferSwap(bpy.types.Operator):
    """Swap current curves with the captured buffer"""
    bl_idname = "boneforge.buffer_swap"
    bl_label = "Swap with Buffer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None or not arm.animation_data or not arm.animation_data.action:
            return False
        return len(_curve_buffer) > 0

    def execute(self, context):
        global _curve_buffer
        arm = active_armature(context)
        action = arm.animation_data.action

        # Check buffer matches current action
        if _curve_buffer:
            first_key = next(iter(_curve_buffer))
            if first_key[0] != action.name:
                self.report({'INFO'},
                            "Buffer was captured for a different action — capture a new buffer first")
                return {'CANCELLED'}

        new_buffer = {}
        swapped = 0

        for pbone in context.selected_pose_bones or []:
            for fc in _bone_fcurves(action, pbone.name):
                key = (action.name, fc.data_path, fc.array_index)
                if key not in _curve_buffer:
                    continue

                # Save current state to new buffer
                current_kfs = []
                for kf in fc.keyframe_points:
                    current_kfs.append((
                        kf.co.x, kf.co.y,
                        tuple(kf.handle_left), tuple(kf.handle_right),
                        kf.interpolation,
                        kf.handle_left_type, kf.handle_right_type,
                    ))
                new_buffer[key] = current_kfs

                # Clear current and restore from buffer
                while len(fc.keyframe_points) > 0:
                    fc.keyframe_points.remove(fc.keyframe_points[0])

                for kf_data in _curve_buffer[key]:
                    frame, val, hl, hr, interp, hlt, hrt = kf_data
                    kf = fc.keyframe_points.insert(frame, val, options={'FAST'})
                    kf.handle_left = Vector(hl)
                    kf.handle_right = Vector(hr)
                    kf.interpolation = interp
                    kf.handle_left_type = hlt
                    kf.handle_right_type = hrt

                fc.update()
                swapped += 1

        _curve_buffer = new_buffer
        self.report({'INFO'}, f"Swapped {swapped} curves with buffer")
        return {'FINISHED'}


# ── Operators — Euler Filter ────────────────────────────────────

class BF_OT_EulerFilter(bpy.types.Operator):
    """Resolve gimbal lock on Euler rotation curves"""
    bl_idname = "boneforge.euler_filter"
    bl_label = "Euler Filter"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action)

    def execute(self, context):
        arm = active_armature(context)
        action = arm.animation_data.action
        filtered = 0
        skipped_quat = 0

        for pbone in context.selected_pose_bones or []:
            if pbone.rotation_mode not in {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}:
                skipped_quat += 1
                continue

            # Find the three euler rotation fcurves
            euler_fcs = {}
            dp = f'pose.bones["{pbone.name}"].rotation_euler'
            for fc in _action_fcurves(action):
                if fc.data_path == dp:
                    euler_fcs[fc.array_index] = fc

            if len(euler_fcs) < 3:
                continue

            # Discontinuity filter — unwrap euler angles
            for axis_idx in range(3):
                fc = euler_fcs.get(axis_idx)
                if fc is None or len(fc.keyframe_points) < 2:
                    continue
                prev_val = fc.keyframe_points[0].co.y
                for i in range(1, len(fc.keyframe_points)):
                    kf = fc.keyframe_points[i]
                    diff = kf.co.y - prev_val
                    if abs(diff) > math.pi:
                        # Unwrap by adding/subtracting 2*pi
                        turns = round(diff / (2 * math.pi))
                        kf.co.y -= turns * 2 * math.pi
                        # Adjust handles proportionally
                        kf.handle_left.y -= turns * 2 * math.pi
                        kf.handle_right.y -= turns * 2 * math.pi
                    prev_val = kf.co.y
                fc.update()
                filtered += 1

        msg = f"Euler filter applied to {filtered} curves"
        if skipped_quat > 0:
            msg += f" — skipped {skipped_quat} bones using quaternion rotation"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


# ── Operators — Smart Bake ──────────────────────────────────────

class BF_OT_SmartBake(bpy.types.Operator):
    """Bake animation with tolerance — keeps keys only where curve deviates"""
    bl_idname = "boneforge.smart_bake"
    bl_label = "Smart Bake"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action)

    def execute(self, context):
        prefs = addon_prefs(context)
        tolerance = prefs.smart_bake_tolerance
        arm = active_armature(context)
        action = arm.animation_data.action
        total_before = 0
        total_after = 0

        for pbone in context.selected_pose_bones or []:
            for fc in _bone_fcurves(action, pbone.name):
                points = [(kf.co.x, kf.co.y) for kf in fc.keyframe_points]
                if len(points) <= 2:
                    total_before += len(points)
                    total_after += len(points)
                    continue

                total_before += len(points)

                # Ramer-Douglas-Peucker-style simplification
                keep = _simplify_curve(points, tolerance)

                # Remove non-kept keyframes (iterate in reverse)
                remove_indices = [i for i in range(len(points)) if i not in keep]
                for idx in reversed(remove_indices):
                    fc.keyframe_points.remove(fc.keyframe_points[idx])

                fc.update()
                total_after += len(keep)

        removed = total_before - total_after
        self.report({'INFO'},
                    f"Smart bake: {total_after} keys remaining (removed {removed})")
        return {'FINISHED'}


def _simplify_curve(points, tolerance):
    """Return set of indices to keep using a simplified RDP algorithm.

    Always keeps the first and last points.
    """
    if len(points) <= 2:
        return set(range(len(points)))

    keep = {0, len(points) - 1}
    _rdp_recurse(points, 0, len(points) - 1, tolerance, keep)
    return keep


def _rdp_recurse(points, start, end, tolerance, keep):
    """Recursive Ramer-Douglas-Peucker."""
    if end - start <= 1:
        return

    # Find point with maximum distance from the line (start → end)
    sx, sy = points[start]
    ex, ey = points[end]
    max_dist = 0.0
    max_idx = start

    line_len = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    for i in range(start + 1, end):
        px, py = points[i]
        if line_len < 1e-10:
            dist = ((px - sx) ** 2 + (py - sy) ** 2) ** 0.5
        else:
            # Perpendicular distance to line
            dist = abs((ey - sy) * px - (ex - sx) * py + ex * sy - ey * sx) / line_len
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > tolerance:
        keep.add(max_idx)
        _rdp_recurse(points, start, max_idx, tolerance, keep)
        _rdp_recurse(points, max_idx, end, tolerance, keep)


# ── Panels ──────────────────────────────────────────────────────

# FP-7 fix: Split monolithic panel into sub-panels

class BF_PT_GraphToolsPanel(bpy.types.Panel):
    """Parent panel for graph and animation tools"""
    bl_idname = "BONEFORGE_PT_graph_tools"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 20

    def draw_header(self, context):
        self.layout.label(text=T("Graph & Animation Tools"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        has_action = (arm and arm.animation_data and arm.animation_data.action)
        has_selection = bool(context.selected_pose_bones) if context.mode == 'POSE' else False

        if not has_action:
            layout.label(text=T("No action on active armature"), icon='INFO')
        elif not has_selection:
            layout.label(text=T("Select bones in Pose mode"), icon='INFO')


class BF_PT_BreakdownerSubPanel(bpy.types.Panel):
    """Breakdowner sub-panel"""
    bl_idname = "BONEFORGE_PT_breakdowner"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_graph"  # v3.3.2: re-parented from BONEFORGE_PT_graph_tools

    def draw_header(self, context):
        self.layout.label(text=T("Breakdowner"))

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action
                and context.selected_pose_bones)

    def draw(self, context):
        layout = self.layout
        layout.operator("boneforge.breakdowner", text=T("Interactive Breakdown"), icon='BREAKDOWNER_POSE')


class BF_PT_DeltaMoverSubPanel(bpy.types.Panel):
    """Delta mover sub-panel"""
    bl_idname = "BONEFORGE_PT_delta_mover"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_graph"  # v3.3.2: re-parented from BONEFORGE_PT_graph_tools to hub delegate

    def draw_header(self, context):
        self.layout.label(text=T("Delta Mover"))

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and context.selected_pose_bones)

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.boneforge_delta_mover

        layout.operator("boneforge.delta_move", text=T("Apply Delta"), icon='ORIENTATION_VIEW')
        from boneforge.core.helpers import draw_helper, options_fold
        col = options_fold(layout, "bc_delta_mover_options", default_closed=False)
        if col is None:
            return
        # FP-5 fix: Dynamic label based on world_units toggle
        x_label = "X Offset (m)" if settings.world_units else "X Offset (px)"
        y_label = "Y Offset (m)" if settings.world_units else "Y Offset (px)"
        col.prop(settings, "offset_x", text=x_label)
        col.prop(settings, "offset_y", text=y_label)
        col.prop(settings, "world_units")
        col.prop(settings, "uniform")
        # SIG-3 fix: snap_neighbor removed from settings and UI


class BF_PT_TangentSubPanel(bpy.types.Panel):
    """Tangent tools sub-panel"""
    bl_idname = "BONEFORGE_PT_tangent_tools"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_graph"  # v3.3.2: re-parented from BONEFORGE_PT_graph_tools to hub delegate

    def draw_header(self, context):
        self.layout.label(text=T("Tangent Handles"))

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action
                and context.selected_pose_bones)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        for item_id, label, _ in TANGENT_TYPE_ITEMS:
            op = row.operator("boneforge.tangent_set_type", text=label)
            op.type = item_id
        # SIG-4 fix: label now says "Toggle Handle Type" instead of "Toggle Weighted"
        layout.operator("boneforge.tangent_toggle_weighted", text=T("Toggle Handle Type"),
                         icon='HANDLE_ALIGNED')


class BF_PT_BufferBakeSubPanel(bpy.types.Panel):
    """Buffer curves and bake tools sub-panel"""
    bl_idname = "BONEFORGE_PT_buffer_bake"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_graph"  # v3.3.2: re-parented from BONEFORGE_PT_graph_tools to hub delegate

    def draw_header(self, context):
        self.layout.label(text=T("Buffer & Bake"))

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and arm.animation_data and arm.animation_data.action
                and context.selected_pose_bones)

    def draw(self, context):
        layout = self.layout

        # Buffer Curves
        box = layout.box()
        box.label(text=T("Buffer Curves"))
        row = box.row(align=True)
        row.operator("boneforge.buffer_capture", text=T("Capture"), icon='REC')
        row.operator("boneforge.buffer_swap", text=T("Swap"), icon='UV_SYNC_SELECT')
        if _curve_buffer:
            box.label(text=f"Buffer: {len(_curve_buffer)} curves stored", icon='INFO')
        else:
            box.label(text=T("Buffer empty"), icon='INFO')

        # Euler Filter & Smart Bake
        box = layout.box()
        box.label(text=T("Bake & Filter"))
        box.operator("boneforge.euler_filter", text=T("Euler Filter"),
                      icon='DRIVER_ROTATIONAL_DIFFERENCE')
        box.operator("boneforge.smart_bake", text=T("Smart Bake"), icon='NORMALIZE_FCURVES')
        from boneforge.core.helpers import draw_helper, options_fold
        col = options_fold(box, "bc_smart_bake_options")
        if col is not None:
            col.prop(addon_prefs(context), "smart_bake_tolerance", text=T("Tolerance"))




# ── Registration ────────────────────────────────────────────────

classes = (
    BF_DeltaMoverSettings,
    BF_OT_Breakdowner,
    BF_OT_DeltaMove,
    BF_OT_TangentSetType,
    BF_OT_TangentToggleHandleType,
    BF_OT_BufferCapture,
    BF_OT_BufferSwap,
    BF_OT_EulerFilter,
    BF_OT_SmartBake,
    BF_PT_BreakdownerSubPanel,
    BF_PT_DeltaMoverSubPanel,
    BF_PT_TangentSubPanel,
    BF_PT_BufferBakeSubPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.boneforge_delta_mover = PointerProperty(
        type=BF_DeltaMoverSettings,
    )

    # Keymaps
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon is not None:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')

        kmi = km.keymap_items.new('boneforge.breakdowner', 'B', 'PRESS',
                                   ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('boneforge.delta_move', 'D', 'PRESS',
                                   ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))


def unregister():
    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Remove properties
    if hasattr(bpy.types.WindowManager, 'boneforge_delta_mover'):
        del bpy.types.WindowManager.boneforge_delta_mover

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
