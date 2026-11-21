"""
easing_presets.py — Named easing profiles and application logic.

Each preset defines how the bezier handles of two adjacent keyframes should
be positioned to produce a specific timing feel.  Presets are designed to
match professional animation conventions used in Maya and After Effects.

Handle offsets are expressed as fractions of the segment width (in frames)
and segment height (in value units), making them resolution-independent.
"""


from typing import Optional

import bpy

from .utils import log, warn, debug, tag_viewport_redraw


# ---------------------------------------------------------------------------
# Preset Definitions
# ---------------------------------------------------------------------------

# Each preset dict contains:
#   name            — Human-readable display name
#   description     — Tooltip text
#   left_handle_type  — Blender handle type for the left keyframe's right handle
#   right_handle_type — Blender handle type for the right keyframe's left handle
#   left_handle_offset  — (dx_fraction, dy_fraction) relative to segment size
#   right_handle_offset — (dx_fraction, dy_fraction) relative to segment size
#
# dx_fraction: fraction of segment width (0.33 = 1/3 of the distance)
# dy_fraction: fraction of segment value height (0.0 = flat, 1.0 = full slope)

PRESETS: dict[str, dict] = {
    "EASE_IN": {
        "name": "Ease In",
        "description": "Slow start, fast finish — acceleration from rest",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.42, 0.0),
        "right_handle_offset": (-0.15, -1.0),
    },
    "EASE_OUT": {
        "name": "Ease Out",
        "description": "Fast start, slow finish — deceleration to rest",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.15, 1.0),
        "right_handle_offset": (-0.42, 0.0),
    },
    "EASE_IN_OUT": {
        "name": "Ease In/Out",
        "description": "Slow at both ends — classic S-curve motion",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.42, 0.0),
        "right_handle_offset": (-0.42, 0.0),
    },
    "LINEAR": {
        "name": "Linear",
        "description": "Constant speed — no easing",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.33, 0.33),
        "right_handle_offset": (-0.33, -0.33),
    },
    "OVERSHOOT": {
        "name": "Overshoot",
        "description": "Slight overshoot past the target, then settle back",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.25, 1.0),
        "right_handle_offset": (-0.25, 0.15),
    },
    "ANTICIPATE": {
        "name": "Anticipate",
        "description": "Small reverse motion before the main movement",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.25, -0.15),
        "right_handle_offset": (-0.25, -1.0),
    },
    "BOUNCE": {
        "name": "Bounce",
        "description": "Simulated bouncing at the end of motion",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.15, 0.8),
        "right_handle_offset": (-0.08, 0.1),
    },
    "CUSTOM": {
        "name": "Custom",
        "description": "User-defined bezier tangent values",
        "left_handle_type": "FREE",
        "right_handle_type": "FREE",
        "left_handle_offset": (0.33, 0.0),
        "right_handle_offset": (-0.33, 0.0),
    },
}


# ---------------------------------------------------------------------------
# Preset Application
# ---------------------------------------------------------------------------

def apply_preset_to_range(
    fcurve: bpy.types.FCurve,
    frame_a: float,
    frame_b: float,
    preset_name: str,
    custom_left_offset: Optional[tuple[float, float]] = None,
    custom_right_offset: Optional[tuple[float, float]] = None,
) -> bool:
    """Apply a named easing preset to the f-curve segment between two keyframes.

    Finds the keyframes at frame_a and frame_b, sets their handle types
    and positions according to the preset, and updates the f-curve.

    Args:
        fcurve: The f-curve to modify.
        frame_a: Frame of the left keyframe.
        frame_b: Frame of the right keyframe.
        preset_name: Identifier of the preset (e.g. "EASE_IN", "BOUNCE").
        custom_left_offset: Override left handle offset for CUSTOM preset.
        custom_right_offset: Override right handle offset for CUSTOM preset.

    Returns:
        bool: True if the preset was applied successfully, False otherwise.
    """
    if fcurve is None:
        warn("apply_preset_to_range called with None fcurve")
        return False

    preset = PRESETS.get(preset_name)
    if preset is None:
        warn(f"Unknown easing preset '{preset_name}'. "
             f"Available: {list(PRESETS.keys())}")
        return False

    # Find keyframes at the specified frames
    keyframe_left = _find_keyframe(fcurve, frame_a)
    keyframe_right = _find_keyframe(fcurve, frame_b)

    if keyframe_left is None or keyframe_right is None:
        warn(f"Cannot find keyframes at frames {frame_a} and {frame_b} for preset application")
        return False
    if keyframe_left == keyframe_right or abs(float(frame_b) - float(frame_a)) < 1e-6:
        # Zero-width range: both ends resolve to the same key.  Applying a
        # preset here collapses that key's handles onto its own co.
        debug(f"Easing preset skipped: zero-width range at frame {frame_a}")
        return False

    try:
        # Calculate segment dimensions for proportional handle placement
        segment_width = keyframe_right.co.x - keyframe_left.co.x
        segment_height = keyframe_right.co.y - keyframe_left.co.y

        # Determine handle offsets
        if preset_name == "CUSTOM" and custom_left_offset is not None and custom_right_offset is not None:
            left_offset = custom_left_offset
            right_offset = custom_right_offset
        else:
            left_offset = preset["left_handle_offset"]
            right_offset = preset["right_handle_offset"]

        # Set handle types according to preset
        keyframe_left.handle_right_type = preset["left_handle_type"]
        keyframe_right.handle_left_type = preset["right_handle_type"]

        # Apply left keyframe's right handle
        # dx is fraction of segment width, dy is fraction of segment height
        keyframe_left.handle_right[0] = keyframe_left.co.x + left_offset[0] * segment_width
        keyframe_left.handle_right[1] = keyframe_left.co.y + left_offset[1] * segment_height

        # Apply right keyframe's left handle
        keyframe_right.handle_left[0] = keyframe_right.co.x + right_offset[0] * segment_width
        keyframe_right.handle_left[1] = keyframe_right.co.y + right_offset[1] * segment_height

        fcurve.update()
        return True

    except Exception as exc:
        warn(f"Error applying preset '{preset_name}': {exc}")
        return False


def _find_keyframe(
    fcurve: bpy.types.FCurve,
    frame: float,
    tolerance: float = 0.1,
) -> Optional[bpy.types.Keyframe]:
    """Find a keyframe at or near the given frame.

    Args:
        fcurve: The f-curve to search.
        frame: The target frame.
        tolerance: Maximum frame distance for a match.

    Returns:
        Keyframe or None: The matching keyframe point.
    """
    best_keypoint = None
    best_distance = tolerance + 1.0

    for keypoint in fcurve.keyframe_points:
        # Calculate distance from target frame
        distance = abs(keypoint.co.x - frame)
        if distance < best_distance:
            best_distance = distance
            best_keypoint = keypoint

    if best_distance <= tolerance:
        return best_keypoint
    return None


# ---------------------------------------------------------------------------
# Blender EnumProperty Items
# ---------------------------------------------------------------------------

def build_preset_menu_items() -> list[tuple[str, str, str]]:
    """Build items for a Blender EnumProperty dropdown.

    Returns:
        list[tuple]: Each item is (identifier, name, description).
    """
    items = []
    for key, preset in PRESETS.items():
        items.append((key, preset["name"], preset["description"]))
    return items


# Frozen version for use as EnumProperty items (Blender requires a fixed
# reference, not a dynamically-generated list).
PRESET_ENUM_ITEMS: list[tuple[str, str, str]] = build_preset_menu_items()


# ---------------------------------------------------------------------------
# Apply Easing Operator
# ---------------------------------------------------------------------------

class GHOST_OT_apply_easing(bpy.types.Operator):
    """Apply an easing preset to the selected ghost range."""

    bl_idname = "ghost_tool.apply_easing"
    bl_label = "Apply Easing Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(
        name="Preset",
        description="Easing preset to apply",
        items=PRESET_ENUM_ITEMS,
        default="EASE_IN_OUT",
    )  # type: ignore[assignment]

    custom_left_x: bpy.props.FloatProperty(name="Left X", description="Outgoing handle time as a fraction of the key interval", default=0.33, min=0, max=1)
    custom_left_y: bpy.props.FloatProperty(name="Left Y", description="Outgoing handle value as a fraction of the change between keys", default=0, min=-2, max=2)
    custom_right_x: bpy.props.FloatProperty(name="Right X", description="Incoming handle time offset as a fraction of the key interval", default=-0.33, min=-1, max=0)
    custom_right_y: bpy.props.FloatProperty(name="Right Y", description="Incoming handle value offset as a fraction of the change between keys", default=0, min=-2, max=2)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require an active object with animation data.

        Args:
            context: The current Blender context.

        Returns:
            bool: True if preset application can proceed.
        """
        obj = context.active_object
        if obj is None or obj.animation_data is None or obj.animation_data.action is None:
            cls.poll_message_set("Select an object with an animation action")
            return False
        from .ghost_data import GhostStore
        if not any(g.parent_frame_a != g.parent_frame_b for g in GhostStore.get(context.scene)):
            cls.poll_message_set("Generate inbetween markers between two keys first")
            return False
        from .session_state import SessionState
        return SessionState.poll_available(cls)

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Apply the selected easing preset.

        Applies to all selected ghosts, or to the entire f-curve if no
        ghosts are selected.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} on success.
        """
        from .ghost_data import GhostStore
        from . import fcurve_utils

        store = GhostStore.get(context.scene)
        selected = store.get_selected(context.scene)

        if not selected:
            # If no ghosts selected, try to apply to all ghost parent ranges
            selected = store.all_ghosts

        if not selected:
            self.report({'WARNING'}, "No ghosts to apply easing to")
            return {'CANCELLED'}

        applied_count = 0

        # Group ghosts by their parent keyframe pairs to avoid duplicate work
        processed_ranges: set[tuple[str, str, str, float, float]] = set()

        for ghost in selected:
            range_key = (
                ghost.object_name, ghost.bone_name, ghost.channel,
                ghost.parent_frame_a, ghost.parent_frame_b,
            )
            if range_key in processed_ranges:
                continue
            processed_ranges.add(range_key)

            # Keyframe ghosts (level 0) and out-of-range step ghosts carry a
            # zero-width parent range; there is no segment to ease.
            if ghost.parent_frame_a == ghost.parent_frame_b:
                continue

            obj = bpy.data.objects.get(ghost.object_name)
            if not obj:
                continue

            fcurve = fcurve_utils.resolve_fcurve(obj, ghost.bone_name, ghost.channel)
            if fcurve is None:
                continue

            success = apply_preset_to_range(
                fcurve, ghost.parent_frame_a, ghost.parent_frame_b, self.preset,
                (self.custom_left_x, self.custom_left_y),
                (self.custom_right_x, self.custom_right_y),
            )
            if success:
                applied_count += 1

        if applied_count > 0:
            self.report({'INFO'}, f"Applied '{self.preset}' to {applied_count} segment(s)")
        else:
            self.report({'WARNING'}, f"No keyframe pairs found for '{self.preset}'")
        tag_viewport_redraw(context)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GHOST_OT_apply_easing,
)


def register() -> None:
    """Register easing preset classes."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister easing preset classes."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Preset dictionary completeness
# >>> from ghost_tool.easing_presets import PRESETS
# >>> assert len(PRESETS) == 8
# >>> for name, p in PRESETS.items():
# ...     assert "left_handle_offset" in p
# ...     assert "right_handle_offset" in p
#
# Test 2: Enum items
# >>> items = build_preset_menu_items()
# >>> assert len(items) == 8
# >>> assert items[0][0] == "EASE_IN"
#
# Test 3: Apply preset to f-curve
# >>> # Setup: object with keyframes at 1 and 25
# >>> fc = obj.animation_data.action.fcurves[0]
# >>> apply_preset_to_range(fc, 1.0, 25.0, "EASE_IN_OUT")
# >>> # Verify handles are set to ease in/out positions
