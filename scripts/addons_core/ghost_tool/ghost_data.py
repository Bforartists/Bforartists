"""
ghost_data.py — Ghost dataclass and GhostStore for the Ghost Tool addon.

This module defines the core data structures used throughout Ghost Tool:

- ``Ghost``: a dataclass representing a single interpolated marker
  between keyframes.
- ``GhostStore``: a scene-level container managing all Ghost instances
  with O(1) uid lookups and level/bone/channel filtering.
- ``generate_ghosts()``: recursive subdivision generator that creates
  ghosts from f-curves.
- ``generate_ghosts_frame_step()``: frame-by-frame generator for
  even-step ghosting.
- ``generate_ghosts_at_keyframes()``: keyframe-only generator.

All persistent ghost data is stored via Blender PropertyGroups attached
to ``bpy.types.Scene``, ensuring compatibility with undo/redo and file
save/load. The actual Ghost objects live in-memory in ``GhostStore``
and are persisted across sessions through JSON export/import.
"""

from __future__ import annotations

import enum
import math
import hashlib
import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Optional

import bpy
from mathutils import Vector

from .utils import sampling_operation, warn, debug, find_fcurve_in_action, get_scene_id, tag_viewport_redraw
from .motion_channels import (  # noqa: F401  (re-exported for existing callers)
    LOCATION_CHANNELS, MOTION_CHANNELS, ROTATION_EULER_CHANNELS, ROTATION_QUAT_CHANNELS,
    is_rotation_channel,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UID_LENGTH: int = 8
"""Length of unique identifier hex strings."""

MAX_SUBDIVISION_LEVEL: int = 5
"""Maximum allowed recursive subdivision depth."""

KEYFRAME_SNAP_THRESHOLD: float = 0.5
"""Frames within this distance of an existing keyframe are skipped during generation."""

# Canonical transform channel names used to normalize f-curve data paths.
# Maps short names to their corresponding Blender RNA property names.
CHANNEL_MAP: dict[str, str] = {
    "location": "location",
    "rotation_euler": "rotation_euler",
    "rotation_quaternion": "rotation_quaternion",
    "scale": "scale",
}


# ---------------------------------------------------------------------------
# Diff Reference — Visual Diff Mode anchor state
# ---------------------------------------------------------------------------

class AnchorState(enum.Enum):
    """State of the Visual Diff reference anchor.

    LIVE  — The pinned reference keyframes are unchanged since pinning.
    STALE — The keyframes at the anchor frame have been edited post-pin;
            the overlay is desaturated and a warning is shown.
    """
    LIVE = "LIVE"
    STALE = "STALE"


@dataclass
class DiffReference:
    """Pinned reference frame snapshot for Visual Diff Mode.

    Stores per-bone world positions captured at pin time.  On each draw
    tick the current poses are compared against these positions and colored
    warm/cool by magnitude.  ``anchor_hash`` lets the Staleness Guard detect
    when the underlying keyframe data has changed after pinning.

    Attributes:
        anchor_frame: The frame number that was pinned.
        anchor_hash:  SHA-256 of (object_name, bone_name, frame, value) tuples
                      at pin time — used to detect post-pin edits.
        ghost_positions: Map of bone_name → world-space Vector at anchor_frame.
        state: LIVE when anchor is valid, STALE when keyframes diverged.
    """

    anchor_frame: int
    anchor_hash: str
    ghost_positions: dict[tuple[str, str], Vector]
    state: AnchorState = AnchorState.LIVE

    # ------------------------------------------------------------------
    # Singleton registry — one DiffReference per scene, keyed by scene id.
    # Declared as ClassVar so the dataclass machinery ignores it.
    # ------------------------------------------------------------------
    _registry: ClassVar[dict[str, "Optional[DiffReference]"]] = {}

    @classmethod
    def get(cls, scene: bpy.types.Scene) -> "Optional[DiffReference]":
        """Return the active DiffReference for a scene, or None."""
        key = get_scene_id(scene)
        return cls._registry.get(key)

    @classmethod
    def set(cls, scene: bpy.types.Scene, ref: "Optional[DiffReference]") -> None:
        """Store or clear the DiffReference for a scene."""
        key = get_scene_id(scene)
        if ref is None:
            cls._registry.pop(key, None)
        else:
            cls._registry[key] = ref

    @classmethod
    def clear_all(cls) -> None:
        """Remove all diff references (called on addon unregister)."""
        cls._registry.clear()


def compute_anchor_hash(
    obj: bpy.types.Object,
    frame: int,
) -> str:
    """Compute a short hash of the keyframe data at *frame* for an object.

    Used by the Staleness Guard to detect post-pin keyframe edits.  The hash
    covers (bone_name, data_path, frame_index, co_x, co_y) for every fcurve
    keyframe whose integer frame equals *frame*.

    Args:
        obj: The Blender object whose animation data is hashed.
        frame: Integer frame to examine.

    Returns:
        str: Hex digest string, or empty string if no animation data.
    """
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return ""

    from .utils import get_fcurves_from_action
    parts = []
    for curve in get_fcurves_from_action(obj.animation_data.action, obj):
        # Evaluate at the anchor; neighboring keys/handles affect between-key poses.
        keys = tuple((tuple(k.co), tuple(k.handle_left), tuple(k.handle_right),
                      k.interpolation, k.handle_left_type, k.handle_right_type)
                     for k in curve.keyframe_points)
        parts.append(repr((curve.data_path, curve.array_index, curve.evaluate(frame), keys)))
    return hashlib.sha256(repr(sorted(parts)).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Ghost Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Ghost:
    """A single ghost marker representing an interpolated f-curve position.

    Ghosts sit between keyframes and visualize the in-between motion.
    They can be dragged to reshape the f-curve, pinned to act as
    constraints, or subdivided further for fine-grained control.

    Attributes:
        frame: The frame number this ghost represents (can be fractional).
        world_position: 3D world-space position for viewport display.
        local_value: The raw f-curve value at this frame.
        channel: The data path component, e.g. "location.x", "rotation_euler.z".
        bone_name: Name of the pose bone, or empty string for object channels.
        object_name: Name of the Blender object owning this channel.
        parent_frame_a: Frame number of the left parent keyframe.
        parent_frame_b: Frame number of the right parent keyframe.
        generation_level: Subdivision depth (1 = first midpoints, 2 = midpoints of midpoints).
        is_pinned: If True, this ghost acts as a soft constraint during recalculation.
        is_selected: If True, this ghost is currently selected for operations.
        uid: Unique identifier string (8-char hex from uuid4).
    """

    frame: float
    world_position: Vector = field(default_factory=lambda: Vector((0.0, 0.0, 0.0)))
    local_value: float = 0.0
    channel: str = ""
    bone_name: str = ""
    object_name: str = ""
    parent_frame_a: float = 0.0
    parent_frame_b: float = 0.0
    generation_level: int = 1
    is_pinned: bool = False
    is_selected: bool = False
    uid: str = field(default_factory=lambda: uuid.uuid4().hex[:UID_LENGTH])

    def to_dict(self) -> dict:
        """Serialize this ghost to a plain dictionary for JSON export.

        Returns:
            dict: All ghost fields as JSON-serializable types.
        """
        return {
            "frame": self.frame,
            "world_position": list(self.world_position),
            "local_value": self.local_value,
            "channel": self.channel,
            "bone_name": self.bone_name,
            "object_name": self.object_name,
            "parent_frame_a": self.parent_frame_a,
            "parent_frame_b": self.parent_frame_b,
            "generation_level": self.generation_level,
            "is_pinned": self.is_pinned,
            "is_selected": self.is_selected,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Ghost:
        """Deserialize a ghost from a dictionary (JSON import).

        Args:
            data: Dictionary with ghost field values.

        Returns:
            Ghost: Reconstructed ghost instance.

        Note:
            If 'uid' is missing from data, a new unique ID is generated.
        """
        if not isinstance(data, dict):
            raise ValueError("Ghost must be an object")
        for key in ('frame', 'local_value', 'parent_frame_a', 'parent_frame_b'):
            value = data.get(key, 0.0)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{key} must be a finite number")
        position = data.get('world_position', (0, 0, 0))
        if not isinstance(position, (list, tuple)) or len(position) != 3 or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in position):
            raise ValueError("world_position must contain three finite numbers")
        for key in ('uid', 'object_name', 'bone_name', 'channel'):
            if key in data and not isinstance(data[key], str):
                raise ValueError(f"{key} must be text")
        if 'uid' in data and not data['uid']:
            raise ValueError("uid must not be empty")
        level = data.get('generation_level', 1)
        if type(level) is not int or not 0 <= level <= MAX_SUBDIVISION_LEVEL + 1:
            raise ValueError("Invalid generation level")
        for key in ('is_pinned', 'is_selected'):
            if key in data and type(data[key]) is not bool:
                raise ValueError(f"{key} must be boolean")
        return cls(
            frame=data["frame"],
            world_position=Vector(data.get("world_position", (0.0, 0.0, 0.0))),
            local_value=data.get("local_value", 0.0),
            channel=data.get("channel", ""),
            bone_name=data.get("bone_name", ""),
            object_name=data.get("object_name", ""),
            parent_frame_a=data.get("parent_frame_a", 0.0),
            parent_frame_b=data.get("parent_frame_b", 0.0),
            generation_level=data.get("generation_level", 1),
            is_pinned=data.get("is_pinned", False),
            is_selected=data.get("is_selected", False),
            uid=data.get("uid", uuid.uuid4().hex[:UID_LENGTH]),
        )


# ---------------------------------------------------------------------------
# GhostStore — In-memory container for all active ghosts
# ---------------------------------------------------------------------------

class GhostStore:
    """Scene-level container for all Ghost instances.

    GhostStore is accessed via the scene's custom property system.  Internally
    it keeps a flat list plus a uid-keyed index for O(1) lookups.

    Design note: Blender PropertyGroups cannot store arbitrary Python objects,
    so GhostStore maintains an in-memory dict that is rebuilt on file load
    via the export/import system.  The canonical truth for a running session
    lives here; serialization to JSON handles persistence across sessions.

    Usage:
        store = GhostStore.get(context.scene)
        store.add(ghost)
        store.get_by_uid("a1b2c3d4")
        store.filter_by_level(2)
    """

    # Per-scene singleton registry — maps stable scene IDs to GhostStore objects.
    # Avoids polluting bpy.types with complex Python objects.
    _instances: dict[str, GhostStore] = {}

    def __init__(self) -> None:
        """Initialize an empty ghost store."""
        self._ghosts: list[Ghost] = []
        self._index: dict[str, Ghost] = {}
        # Ghost count per generation level — key: level (1-5), value: ghost count.
        # Maintained by _update_level_counts() after add/remove operations.
        self._level_counts: dict[int, int] = {}
        self._version: int = 0  # Incremented on every mutation for cache invalidation
        self._cached_frame_range: tuple[float, float] | None = None

    @property
    def version(self) -> int:
        """Monotonic counter incremented on every store mutation.

        Used by the viewport draw batch cache to detect stale batches.
        """
        return self._version

    def _bump_version(self) -> None:
        """Increment the version counter and clear cached frame range."""
        self._version += 1
        self._cached_frame_range = None

    @property
    def frame_range(self) -> tuple[float, float]:
        """Cached (min_frame, max_frame) across all ghosts."""
        if self._cached_frame_range is None:
            if self._ghosts:
                frames = [g.frame for g in self._ghosts]
                self._cached_frame_range = (min(frames), max(frames))
            else:
                self._cached_frame_range = (0.0, 1.0)
        return self._cached_frame_range

    def _update_level_counts(self) -> None:
        """Recompute the per-level ghost count cache from the ghost list.

        Called after add/remove operations so that count_by_level() and
        the UI level-visibility controls stay in sync without scanning
        the full list on every draw call.
        """
        self._level_counts = {}
        for ghost in self._ghosts:
            self._level_counts[ghost.generation_level] = self._level_counts.get(ghost.generation_level, 0) + 1

    # --- Singleton access per scene ---

    @classmethod
    def get(cls, scene: bpy.types.Scene) -> GhostStore:
        """Retrieve or create the GhostStore for the given scene.

        Args:
            scene: The Blender scene to look up.

        Returns:
            GhostStore: The store associated with this scene.
        """
        key = get_scene_id(scene)
        if key not in cls._instances:
            cls._instances[key] = cls()
        return cls._instances[key]

    @classmethod
    def clear_instance(cls, scene_name: str) -> None:
        """Remove the GhostStore instance for a scene (used on unregister).

        Args:
            scene_name: Name of the scene whose store should be removed.
        """
        cls._instances.pop(scene_name, None)

    @classmethod
    def clear_all_instances(cls) -> None:
        """Remove all GhostStore instances (used during addon unregistration)."""
        cls._instances.clear()

    # --- CRUD operations ---

    def add(self, ghost: Ghost) -> None:
        """Add a ghost to the store.

        Args:
            ghost: The Ghost instance to add.

        Raises:
            ValueError: If a ghost with the same uid already exists.
        """
        if ghost.uid in self._index:
            raise ValueError(
                f"[Ghost Tool] Ghost with uid '{ghost.uid}' already exists in store."
            )
        self._ghosts.append(ghost)
        self._index[ghost.uid] = ghost
        self._level_counts[ghost.generation_level] = self._level_counts.get(ghost.generation_level, 0) + 1
        self._bump_version()

    def remove(self, uid: str) -> bool:
        """Remove a ghost by its unique identifier.

        Args:
            uid: The unique identifier of the ghost to remove.

        Returns:
            bool: True if the ghost was found and removed, False otherwise.
        """
        ghost = self._index.pop(uid, None)
        if ghost is None:
            return False
        try:
            self._ghosts.remove(ghost)
        except ValueError:
            warn(f"Ghost {uid} not found in list (index/list mismatch)")
        level = ghost.generation_level
        count = self._level_counts.get(level, 0)
        if count > 1:
            self._level_counts[level] = count - 1
        else:
            self._level_counts.pop(level, None)
        self._bump_version()
        return True

    def get_by_uid(self, uid: str) -> Optional[Ghost]:
        """Look up a ghost by its unique identifier.

        Args:
            uid: The unique identifier to search for.

        Returns:
            Ghost or None: The matching ghost, or None if not found.
        """
        return self._index.get(uid)

    def clear(self) -> None:
        """Remove all ghosts from the store."""
        self._ghosts.clear()
        self._index.clear()
        self._update_level_counts()
        self._bump_version()

    def replace_all(self, ghosts: list[Ghost]) -> None:
        """Atomically replace all ghosts in the store.

        Clears the current contents and adds all provided ghosts in one
        operation.  This is used by the pipeline to swap in a fresh set
        of evaluated ghosts without leaving the store in a partially
        empty state between clear() and add() calls.

        Args:
            ghosts: The new list of Ghost objects to store.
        """
        if ghosts is None:
            warn("replace_all called with None — ignoring")
            return
        self._ghosts.clear()
        self._index.clear()
        for ghost in ghosts:
            if ghost.uid not in self._index:
                self._ghosts.append(ghost)
                self._index[ghost.uid] = ghost
            else:
                # Duplicate uid — skip with warning
                warn(f"Duplicate uid '{ghost.uid}' during replace_all (obj={ghost.object_name}, bone={ghost.bone_name}, ch={ghost.channel}, frame={ghost.frame}), skipping.")
        self._update_level_counts()
        self._bump_version()

    def clear_level(self, level: int) -> int:
        """Remove all ghosts at a specific generation level.

        Args:
            level: The generation level to remove.

        Returns:
            int: Number of ghosts removed.
        """
        to_remove = [g for g in self._ghosts if g.generation_level == level]
        for g in to_remove:
            self._index.pop(g.uid, None)
        self._ghosts = [g for g in self._ghosts if g.generation_level != level]
        self._update_level_counts()
        if to_remove:
            self._bump_version()
        return len(to_remove)

    # --- Query / filter operations ---

    @property
    def all_ghosts(self) -> list[Ghost]:
        """Return a shallow copy of the full ghost list.

        Returns:
            list[Ghost]: All ghosts currently in the store.
        """
        return list(self._ghosts)

    def __len__(self) -> int:
        """Return the number of ghosts in the store."""
        return len(self._ghosts)

    def __iter__(self):
        """Iterate over all ghosts.

        Returns:
            iterator: Iterator over Ghost objects in the store.
        """
        return iter(self._ghosts)

    def filter_by_level(self, level: int) -> list[Ghost]:
        """Return ghosts matching a given generation level.

        Args:
            level: The generation level to filter by.

        Returns:
            list[Ghost]: Ghosts at the requested level.
        """
        return [g for g in self._ghosts if g.generation_level == level]

    def count_by_level(self, level: int) -> int:
        """Return the cached count of ghosts at a given generation level.

        This is O(1) and suitable for UI draw loops, unlike filter_by_level()
        which creates a new list each call.

        Args:
            level: The generation level to count.

        Returns:
            int: Number of ghosts at that level.
        """
        return self._level_counts.get(level, 0)

    def filter_by_bone(self, bone_name: str) -> list[Ghost]:
        """Return ghosts belonging to a specific bone.

        Args:
            bone_name: The pose bone name to filter by.

        Returns:
            list[Ghost]: Ghosts associated with that bone.
        """
        return [g for g in self._ghosts if g.bone_name == bone_name]

    def filter_by_channel(self, channel: str) -> list[Ghost]:
        """Return ghosts belonging to a specific channel.

        Args:
            channel: The channel identifier to filter by (e.g. "location.x").

        Returns:
            list[Ghost]: Ghosts associated with that channel.
        """
        return [g for g in self._ghosts if g.channel == channel]

    def filter_by_object(self, object_name: str) -> list[Ghost]:
        """Return ghosts belonging to a specific object.

        Args:
            object_name: The Blender object name to filter by.

        Returns:
            list[Ghost]: Ghosts associated with that object.
        """
        return [g for g in self._ghosts if g.object_name == object_name]

    def get_selected(self, scene=None) -> list[Ghost]:
        """Return all currently selected ghosts.

        Returns:
            list[Ghost]: Ghosts with is_selected == True.
        """
        if scene is not None:
            from .session_state import SessionState
            selected = SessionState.get(scene).selection_set
            return [g for g in self._ghosts if g.uid in selected]
        return [g for g in self._ghosts if g.is_selected]

    def get_pinned(self) -> list[Ghost]:
        """Return all pinned ghosts.

        Returns:
            list[Ghost]: Ghosts with is_pinned == True.
        """
        return [g for g in self._ghosts if g.is_pinned]

    def get_chain(self, object_name: str, bone_name: str, channel: str) -> list[Ghost]:
        """Return the ordered ghost chain for a specific object/bone/channel.

        Ghosts are sorted by frame number so they form a sequential chain
        suitable for drawing a motion arc.

        Args:
            object_name: The Blender object name.
            bone_name: The pose bone name (empty string for object channels).
            channel: The channel identifier (e.g. "location.x").

        Returns:
            list[Ghost]: Sorted ghosts matching all three criteria.
        """
        matches = [
            g for g in self._ghosts
            if g.object_name == object_name
            and g.bone_name == bone_name
            and g.channel == channel
        ]
        matches.sort(key=lambda g: g.frame)
        return matches

    def to_dict_list(self) -> list[dict]:
        """Serialize all ghosts to a list of dictionaries.

        Returns:
            list[dict]: Each ghost as a JSON-serializable dict.
        """
        return [g.to_dict() for g in self._ghosts]

    def load_from_dict_list(self, data: list[dict]) -> None:
        """Replace current store contents from a list of ghost dicts.

        Existing ghosts are cleared before loading.

        Args:
            data: List of ghost dictionaries (from JSON import).
        """
        self.clear()
        for item in data:
            try:
                ghost = Ghost.from_dict(item)
                self.add(ghost)
            except (KeyError, TypeError, ValueError) as exc:
                warn(f"Skipping invalid ghost data during load: {exc}")


# ---------------------------------------------------------------------------
# Custom range validation callbacks
# ---------------------------------------------------------------------------

def _update_custom_range_start(self, context):
    """Ensure custom_range_start is less than custom_range_end."""
    if self.custom_range_start >= self.custom_range_end:
        # Use direct RNA override to avoid triggering the other callback
        self["custom_range_end"] = self.custom_range_start + 1
    _on_ghost_sampling_changed(self, context)


def _update_custom_range_end(self, context):
    """Ensure custom_range_end is greater than custom_range_start."""
    if self.custom_range_end <= self.custom_range_start:
        self["custom_range_start"] = self.custom_range_end - 1
    _on_ghost_sampling_changed(self, context)


def _on_ghost_sampling_changed(self, context):
    """Regenerate point ghosts after sampling controls change in live mode."""
    if not context or not context.scene or not hasattr(context.scene, 'ghost_tool'):
        return
    settings = context.scene.ghost_tool
    if not settings.is_active or not settings.live_point_ghosts or settings.live_freeze:
        return
    try:
        from .ghost_pipeline import _schedule_deferred_update
        _schedule_deferred_update()
    except Exception as exc:
        warn(f"Failed to schedule ghost sampling update: {exc}")


def _on_arc_lines_changed(self, context):
    # Keep the original public flag in sync with the toolbar's newer flag.
    self['show_motion_arc'] = self.show_arc_lines
    tag_viewport_redraw(context)


def _on_motion_arc_changed(self, context):
    self['show_arc_lines'] = self.show_motion_arc
    tag_viewport_redraw(context)


def _on_ghost_feature_enabled(self, context):
    """Handle the master Ghost Tools toggle and individual feature toggles.

    When Ghost Tools (is_active) is turned ON:
        - Enables show_mesh_ghosts automatically
        - Marks pipeline dirty and schedules generation

    When Ghost Tools is turned OFF:
        - Clears all mesh ghosts from the scene
        - Clears all point ghosts from the store
        - Disables show_mesh_ghosts
    """
    if not context or not context.scene:
        return

    scene = context.scene
    settings = scene.ghost_tool

    # Detect if we're turning OFF — clear everything
    if not settings.is_active:
        # Visibility is an interlock: do not leave a persistent marker edit
        # mode or an in-progress marker drag armed behind hidden ghosts.
        try:
            from .modal_operator import GHOST_OT_pick_marker
            from .path_handle_drag import GHOST_OT_path_handle_drag
            from .session_state import SessionState
            active_path_mode = GHOST_OT_path_handle_drag._active_wait_mode
            if SessionState._gesture_owner is not None:
                SessionState.cancel_active()
            if active_path_mode is not None:
                active_path_mode._finish(context)
            if GHOST_OT_pick_marker._active_drag_mode is not None:
                active = GHOST_OT_pick_marker._active_drag_mode
                if active is not None:
                    active._finish()
        except Exception as exc:
            warn(f"Failed to exit ghost marker edit mode: {exc}")
        try:
            from .mesh_ghosts import clear_mesh_ghosts
            clear_mesh_ghosts(context)
        except Exception as exc:
            warn(f"Failed to clear mesh ghosts: {exc}")
        try:
            store = GhostStore.get(scene)
            store.clear()
        except Exception as exc:
            warn(f"Failed to clear ghost store: {exc}")
        # Key edits made while off are never marked dirty: drop the path cache so
        # turning back on re-samples. The pinned list stays.
        try:
            from .motion_paths import clear_cache
            clear_cache()
        except Exception as exc:
            warn(f"Failed to clear motion path cache: {exc}")
        # Also disable onion skin so it's clean for next enable
        if settings.show_mesh_ghosts:
            settings["show_mesh_ghosts"] = False
        settings["mesh_ghost_sources"] = ""
        # Tag viewport redraw to clear visuals
        tag_viewport_redraw(context)
        return

    # Turning ON — ensure show_mesh_ghosts is enabled so pipeline generates them
    if not settings.show_mesh_ghosts:
        settings["show_mesh_ghosts"] = True

    # Schedule forced mesh regen (bypasses live-mode gate)
    try:
        from .ghost_pipeline import _schedule_forced_mesh_regen, _schedule_deferred_update
        from .ghost_cache import GhostCache
        cache = GhostCache.get(scene)
        cache.invalidate_all()
        _schedule_forced_mesh_regen()
        # Also schedule normal deferred update for point ghosts
        _schedule_deferred_update()
    except Exception as exc:
        warn(f"Failed to schedule ghost regeneration: {exc}")


def _on_show_mesh_ghosts_changed(self, context):
    """Onion skins on: build them for the selected character. Off: clear them."""
    if not context or not context.scene:
        return
    settings = context.scene.ghost_tool
    if not settings.is_active:
        return
    if not settings.show_mesh_ghosts:
        try:
            from .mesh_ghosts import clear_mesh_ghosts
            clear_mesh_ghosts(context)
        except Exception as exc:
            warn(f"Failed to clear mesh ghosts: {exc}")
        tag_viewport_redraw(context)
        return
    try:
        from .ghost_pipeline import _schedule_forced_mesh_regen
        _schedule_forced_mesh_regen()
    except Exception as exc:
        warn(f"Failed to schedule onion skin rebuild: {exc}")


def _on_cached_markers_changed(self, context):
    """Change marker display without touching generated data or scheduling work."""
    tag_viewport_redraw(context)


def _on_cached_skin_changed(self, context):
    """Hide/show the owning scene's cached skins without generating or deleting."""
    from .mesh_ghosts import set_cached_skin_visibility
    set_cached_skin_visibility(self.id_data, self.show_cached_skin)
    tag_viewport_redraw(context)


def _on_mesh_ghost_mode_changed(self, context):
    """Instantly switch all existing mesh ghosts between solid and wireframe."""
    scene = getattr(context, 'scene', None) if context else None
    if scene is None:
        return
    try:
        from .mesh_ghosts import set_mesh_ghost_display_mode
        set_mesh_ghost_display_mode(self.mesh_ghost_mode, scene=scene)
        tag_viewport_redraw(context)
    except Exception as exc:
        warn(f"Failed to change mesh ghost display mode: {exc}")


def _on_mesh_ghost_xray_changed(self, context):
    """Show existing onion skins through the character (or stop), without a rebuild."""
    if not context or not context.scene:
        return
    from .mesh_ghosts import set_mesh_ghost_xray
    set_mesh_ghost_xray(context.scene, self.mesh_ghost_xray)


def _on_mesh_ghost_setting_changed(self, context):
    """Re-trigger mesh ghost generation when a mesh ghost setting changes.

    Called by mesh_ghost_frame_mode, mesh_ghost_past_count, etc. so that
    switching between Frame Step and Keyframes Only is seamless — no manual
    Generate click required.

    Uses the forced mesh regen path which bypasses the live-mode gate,
    ensuring the switch works even in Snapshot mode.
    """
    if not context or not context.scene:
        return
    settings = context.scene.ghost_tool
    if not settings.is_active or not settings.show_mesh_ghosts:
        return
    try:
        from .ghost_pipeline import _schedule_forced_mesh_regen
        from .ghost_cache import GhostCache
        frame_mode = settings.mesh_ghost_frame_mode
        print(f"[GhostTool] Setting changed → forced regen (frame_mode={frame_mode})")
        cache = GhostCache.get(context.scene)
        cache.invalidate_all()
        _schedule_forced_mesh_regen()
    except Exception as exc:
        print(f"[GhostTool] _on_mesh_ghost_setting_changed ERROR: {exc}")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Blender PropertyGroup — lightweight scene-level settings
# ---------------------------------------------------------------------------

def _schedule_path_refresh(context, clear: bool) -> None:
    """Schedule the re-sample; sampling calls frame_set, which an update callback
    must not do, so the pipeline's deferred timer runs it on the next idle tick."""
    try:
        from .motion_paths import clear_cache
        from .ghost_pipeline import GhostPipeline, _schedule_deferred_update
        if clear:
            clear_cache()
        GhostPipeline.get(context.scene).mark_dirty()
        _schedule_deferred_update()
        tag_viewport_redraw(context)
    except Exception as exc:
        warn(f"Motion paths: could not schedule refresh: {exc}")


def _on_path_setting_changed(self, context):
    """Paths turned on or off: key edits made while off were never marked dirty,
    so drop the cache and re-sample everything."""
    if not self.paths_enabled:
        # Turning paths off exits the persistent path-handle picker and rolls
        # back any handle edit that is still in progress.
        try:
            from .path_handle_drag import GHOST_OT_path_handle_drag
            active = GHOST_OT_path_handle_drag._active_wait_mode
            if active is not None:
                active._abort()
                active._finish(context)
        except Exception as exc:
            warn(f"Failed to exit path marker edit mode: {exc}")
    _schedule_path_refresh(context, clear=True)


def _on_path_anchor_changed(self, context):
    """Head <-> Tail: this path's cached points belong to the other end of the bone."""
    try:
        from .motion_paths import forget
        forget((self.object_name, self.bone_name))
    except Exception as exc:
        warn(f"Motion paths: could not drop the path cache: {exc}")
    _schedule_path_refresh(context, clear=False)


def _on_path_window_changed(self, context):
    """Range, step or follow changed, globally or for one path: cached positions stay valid (they are
    keyed by frame; refresh_paths re-samples an anchor change), so only the frames
    that entered the window are sampled."""
    _schedule_path_refresh(context, clear=False)


def _get_path_marker_count(self, side):
    name = 'paths_markers_' + side
    if self.paths_use_marker_counts:
        return self.get(name, getattr(self, 'paths_' + side) // max(1, self.paths_step))
    from .motion_paths import desired_frames
    scene = self.id_data
    frames = desired_frames(self, scene)
    return sum(f < scene.frame_current if side == 'before' else f > scene.frame_current for f in frames)


def _set_path_marker_count(self, value, side):
    # Preserve the effective opposite count when switching a saved frame range.
    other = 'after' if side == 'before' else 'before'
    self['paths_markers_' + other] = _get_path_marker_count(self, other)
    self['paths_markers_' + side] = max(0, min(500, value))
    self['paths_use_marker_counts'] = True


def _get_path_markers_before(self):
    return _get_path_marker_count(self, 'before')


def _get_path_markers_after(self):
    return _get_path_marker_count(self, 'after')


def _set_path_markers_before(self, value):
    _set_path_marker_count(self, value, 'before')


def _set_path_markers_after(self, value):
    _set_path_marker_count(self, value, 'after')


def _on_paths_show_markers_changed(self, context):
    """Generating markers samples frames, so it runs on the next idle tick, not here."""
    try:
        from .motion_paths import request_marker_sync
        request_marker_sync()
    except Exception as exc:
        warn(f"Motion paths markers: {exc}")


def _get_path_color_before(self):
    # Until set, the before-colour is this path's own colour at 55 %, so paths saved
    # before 3.6 (no stored value) draw Split in their own colour, not the gold default.
    stored = self.get("color_before_value")
    return tuple(stored) if stored is not None else tuple(c * 0.55 for c in self.color)


def _set_path_color_before(self, value):
    self["color_before_value"] = tuple(value)


class GhostPathEntry(bpy.types.PropertyGroup):
    """One pinned motion path: an object, or a bone of an armature. A folder row is an entry too
    (is_folder): it stores its name in object_name and its paths point at its folder_key."""

    object_name: bpy.props.StringProperty(
        name="Object", description="Object this path follows; on a folder row, the folder's name",
    )  # type: ignore[assignment]
    is_folder: bpy.props.BoolProperty(
        name="Folder", description="This row is a folder that groups paths, not a path", default=False,
    )  # type: ignore[assignment]
    # Paths point at a folder by key, not by name, so renaming a folder keeps its paths in it.
    folder_key: bpy.props.StringProperty(
        name="Folder Key", description="Fixed identity of this folder row; its paths store it in Folder", default="",
    )  # type: ignore[assignment]
    folder: bpy.props.StringProperty(
        name="In Folder", description="Key of the folder this path is in; empty is the top level", default="",
    )  # type: ignore[assignment]
    collapsed: bpy.props.BoolProperty(
        name="Collapsed", description="Hide this folder's paths in the list", default=False,
    )  # type: ignore[assignment]
    # Saved with the file, like Blender's own selection: a checked set survives a save.
    checked: bpy.props.BoolProperty(
        name="Checked", description="Include this row in Apply to Checked and the Checked menu actions", default=False,
    )  # type: ignore[assignment]
    # A third target kind (design §8 decision 12): a mesh vertex. -1 follows the object origin or a bone,
    # so files from before 3.7 load unchanged.
    vertex_index: bpy.props.IntProperty(
        name="Vertex", description="Mesh vertex this path follows; -1 follows the object origin or the bone",
        default=-1, min=-1,
    )  # type: ignore[assignment]
    bone_name: bpy.props.StringProperty(
        name="Bone", description="Bone this path follows; empty follows the object origin", default="",
    )  # type: ignore[assignment]
    visible: bpy.props.BoolProperty(name="Visible", description="Draw this path", default=True)  # type: ignore[assignment]
    color: bpy.props.FloatVectorProperty(
        name="Color", description="Colour of this path",
        subtype='COLOR', size=3, min=0.0, max=1.0, default=(0.96, 0.71, 0.0),
    )  # type: ignore[assignment]
    thickness: bpy.props.IntProperty(
        name="Thickness", description="Line width of this path in pixels", default=2, min=1, max=6,
    )  # type: ignore[assignment]
    anchor: bpy.props.EnumProperty(
        name="Anchor",
        description="Which point of the bone the path traces",
        update=_on_path_anchor_changed,
        items=[('HEAD', "Head", "Bone head / object origin"), ('TAIL', "Tail", "Bone tail")],
        default='HEAD',
    )  # type: ignore[assignment]
    color_before: bpy.props.FloatVectorProperty(
        name="Colour Before", description="Colour of this path before the playhead when the style is Split",
        subtype='COLOR', size=3, min=0.0, max=1.0,
        get=_get_path_color_before, set=_set_path_color_before,   # get/set, not get_transform: Blender 4.x too
    )  # type: ignore[assignment]
    dot_size: bpy.props.IntProperty(
        name="Dot Size", description="Size of this path's key dots in pixels", default=6, min=1, max=12,
    )  # type: ignore[assignment]
    in_front: bpy.props.BoolProperty(
        name="In Front", description="Draw this path through the scene; off hides it behind geometry",
        default=True,   # draw handlers run with no depth test, so paths always drew in front
    )  # type: ignore[assignment]
    # Range override: off follows the global range, so files from before 3.6 draw as they did.
    # A change keeps the cache, like the global range fields: only frames new to the path are sampled.
    use_own_range: bpy.props.BoolProperty(
        name="Own Range", description="Give this path its own frame range instead of the global one",
        default=False, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    own_range_mode: bpy.props.EnumProperty(
        name="Range",
        description="Which frames this path covers",
        items=[
            ('AROUND_CURSOR', "Around Playhead", "Frames before and after the playhead"),
            ('SCENE', "Scene", "The scene frame range"),
            ('CUSTOM', "Custom", "This path's own start and end frames"),
        ],
        default='AROUND_CURSOR',
        update=_on_path_window_changed,
    )  # type: ignore[assignment]
    own_before: bpy.props.IntProperty(
        name="Before", description="Frames this path draws before the playhead",
        default=12, min=0, max=500, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    own_after: bpy.props.IntProperty(
        name="After", description="Frames this path draws after the playhead",
        default=12, min=0, max=500, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    own_step: bpy.props.IntProperty(
        name="Every", description="Sample every Nth frame along this path",
        default=1, min=1, max=24, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    own_start: bpy.props.IntProperty(
        name="Start", description="First frame of this path's custom range",
        default=1, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    own_end: bpy.props.IntProperty(
        name="End", description="Last frame of this path's custom range",
        default=250, update=_on_path_window_changed,
    )  # type: ignore[assignment]

    @property
    def label(self) -> str:
        if self.is_folder:
            return self.object_name
        if self.vertex_index >= 0:
            return f"{self.object_name} · v{self.vertex_index}"
        if self.bone_name:
            return f"{self.object_name} › {self.bone_name}"
        return self.object_name


class GhostToolSceneSettings(bpy.types.PropertyGroup):
    """Scene-level settings stored as a Blender PropertyGroup.

    These are the properties that survive undo/redo and file save/load.
    The actual Ghost objects live in GhostStore (in memory) and are
    persisted via JSON export for cross-session use.
    """

    is_active: bpy.props.BoolProperty(
        name="Ghost Tools",
        description="Enable Ghost Tool visualization and controls in the viewport",
        default=True,
        update=_on_ghost_feature_enabled,
    )  # type: ignore[assignment]

    show_cached_markers: bpy.props.BoolProperty(
        name="Show cached markers",
        description="Show or hide existing cached markers without regenerating them",
        default=True,
        update=_on_cached_markers_changed,
    )  # type: ignore[assignment]

    show_cached_skin: bpy.props.BoolProperty(
        name="Show cached skin",
        description="Show or hide existing cached onion skins without regenerating them",
        default=True,
        update=_on_cached_skin_changed,
    )  # type: ignore[assignment]

    subdivision_level: bpy.props.IntProperty(
        name="Subdivision Level",
        description="Number of recursive subdivision passes (1 = midpoints only)",
        default=1,
        min=1,
        max=MAX_SUBDIVISION_LEVEL,
        update=_on_ghost_sampling_changed,
    )  # type: ignore[assignment]

    show_level_1: bpy.props.BoolProperty(
        name="Show Level 1",
        description="Show ghosts from the first subdivision level (midpoints between keyframes)",
        default=True,
    )  # type: ignore[assignment]
    show_level_2: bpy.props.BoolProperty(
        name="Show Level 2",
        description="Show ghosts from the second subdivision level (midpoints of midpoints)",
        default=True,
    )  # type: ignore[assignment]
    show_level_3: bpy.props.BoolProperty(
        name="Show Level 3",
        description="Show ghosts from the third subdivision level",
        default=True,
    )  # type: ignore[assignment]
    show_level_4: bpy.props.BoolProperty(
        name="Show Level 4",
        description="Show ghosts from the fourth subdivision level",
        default=True,
    )  # type: ignore[assignment]
    show_level_5: bpy.props.BoolProperty(
        name="Show Level 5",
        description="Show ghosts from the fifth subdivision level (maximum depth)",
        default=True,
    )  # type: ignore[assignment]

    show_motion_arc: bpy.props.BoolProperty(
        name="Show Motion Arc",
        description="Draw a line connecting ghosts and keyframes",
        default=True,
        update=_on_motion_arc_changed,
    )  # type: ignore[assignment]

    show_spacing_ticks: bpy.props.BoolProperty(
        name="Show Spacing Ticks",
        description="Draw tick marks along the arc showing frame spacing",
        default=False,
    )  # type: ignore[assignment]

    show_acceleration_markers: bpy.props.BoolProperty(
        name="Show Acceleration Markers",
        description=(
            "Display markers at points where velocity changes significantly. "
            "Green ticks indicate acceleration (speeding up), red ticks "
            "indicate deceleration (slowing down)"
        ),
        default=False,
    )  # type: ignore[assignment]

    curve_mode: bpy.props.EnumProperty(
        name="Curve Shape Mode",
        description="How f-curve handles behave when a ghost is moved",
        items=[
            # FREE: handles adjust freely without constraints
            ("FREE", "Free", "Handles adjust freely to pass through new position"),
            # LOCKED: preserve handle angles, only allow length changes
            ("LOCKED", "Locked", "Handle angle is preserved, only length changes"),
            # SMOOTH: redistribute handle influence across both affected segments
            ("SMOOTH", "Smooth", "Handle influence is redistributed across the segment"),
        ],
        default="FREE",
    )  # type: ignore[assignment]

    grab_radius: bpy.props.IntProperty(
        name="Grab Radius",
        description="Screen-space pixel radius for ghost picking",
        default=20,
        min=5,
        max=100,
    )  # type: ignore[assignment]

    # Custom frame range for ghost generation
    use_custom_range: bpy.props.BoolProperty(
        name="Use Custom Range",
        description="Limit ghost generation to a custom frame range",
        default=False,
    )  # type: ignore[assignment]

    custom_range_start: bpy.props.IntProperty(
        name="Range Start",
        description="Start frame for ghost generation",
        default=1,
        update=_update_custom_range_start,
    )  # type: ignore[assignment]

    custom_range_end: bpy.props.IntProperty(
        name="Range End",
        description="End frame for ghost generation",
        default=250,
        update=_update_custom_range_end,
    )  # type: ignore[assignment]

    # ── Mesh Onion Skinning ──────────────────────────────────────────────
    # Controls for the transparent mesh duplicate system that renders
    # full character silhouettes at nearby frames (onion skinning).

    show_mesh_ghosts: bpy.props.BoolProperty(
        name="Show Mesh Ghosts",
        description="Display transparent mesh duplicates at ghost frames (onion skinning)",
        default=False,
        update=_on_show_mesh_ghosts_changed,
    )  # type: ignore[assignment]

    mesh_ghost_past_count: bpy.props.IntProperty(
        name="Past Ghosts",
        description="Number of mesh ghosts to show before the current frame",
        default=3,
        min=0,
        max=16,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_future_count: bpy.props.IntProperty(
        name="Future Ghosts",
        description="Number of mesh ghosts to show after the current frame",
        default=3,
        min=0,
        max=16,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_step: bpy.props.IntProperty(
        name="Frame Step",
        description="Frame interval between mesh ghosts",
        default=2,
        min=1,
        max=24,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_mode: bpy.props.EnumProperty(
        name="Mesh Ghost Mode",
        description="How mesh ghosts are displayed in the viewport",
        items=[
            # SOLID: render as semi-transparent shaded mesh
            ("SOLID", "Solid", "Semi-transparent shaded mesh"),
            # WIRE: render only edges/wireframe for silhouette
            ("WIRE", "Wireframe", "Wireframe silhouette only"),
        ],
        default="SOLID",
        update=_on_mesh_ghost_mode_changed,
    )  # type: ignore[assignment]

    mesh_ghost_xray: bpy.props.BoolProperty(
        name="X-Ray",
        description="Draw onion skins in front of everything, so poses behind the character stay visible",
        default=False,
        update=_on_mesh_ghost_xray_changed,
    )  # type: ignore[assignment]

    mesh_ghost_falloff: bpy.props.EnumProperty(
        name="Onion Skin Fade",
        description="How onion skins fade with distance from the current frame",
        items=[
            ("LINEAR", "Linear", "Even fade across the range"),
            ("SMOOTH", "Smooth", "Gentle near the current frame and at the ends, faster in the middle"),
            ("EXPONENTIAL", "Exponential", "Fade quickly near the current frame, long faint tail"),
            ("CONSTANT", "Constant", "No fade: every onion skin at the same opacity"),
        ],
        default="LINEAR",
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_opacity: bpy.props.FloatProperty(
        name="Mesh Opacity",
        description="Maximum opacity for the closest mesh ghosts",
        default=0.35,
        min=0.05,
        max=0.8,
        subtype='FACTOR',
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_frame_mode: bpy.props.EnumProperty(
        name="Mesh Frame Mode",
        description="How mesh ghost frames are selected",
        items=[
            # STEP: mesh ghosts at regular frame intervals (default behavior)
            ("STEP", "Frame Step", "Mesh ghosts at every Nth frame around the playhead"),
            # KEYFRAMES: mesh ghosts only at keyframe positions
            ("KEYFRAMES", "Keyframes Only", "Mesh ghosts only at keyframe positions"),
        ],
        default="STEP",
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_keyframe_skip: bpy.props.EnumProperty(
        name="Keyframe Interval",
        description=(
            "Set the stepped interval between ghost keyframes. "
            "Controls how many keyframes to skip between each ghost — "
            "e.g. 'Every 2nd' places a ghost at every other keyframe"
        ),
        items=[
            ("1", "Every", "Place a ghost at every keyframe (no skipping)"),
            ("2", "Every 2nd", "Place a ghost at every 2nd keyframe (skip one between each)"),
            ("3", "Every 3rd", "Place a ghost at every 3rd keyframe (skip two between each)"),
            ("5", "Every 5th", "Place a ghost at every 5th keyframe (skip four between each)"),
            ("10", "Every 10th", "Place a ghost at every 10th keyframe (skip nine between each)"),
            ("CUSTOM", "Custom", "Enter a custom interval number for keyframe stepping"),
        ],
        default="1",
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_keyframe_skip_custom: bpy.props.IntProperty(
        name="Custom Interval",
        description=(
            "Custom keyframe stepped interval — e.g. 4 means place a ghost "
            "at every 4th keyframe, skipping three in between"
        ),
        default=4,
        min=1,
        max=100,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_past_color: bpy.props.FloatVectorProperty(
        name="Past Mesh Color",
        description="Color tint for mesh ghosts before the current frame",
        subtype='COLOR',
        size=3,
        default=(0.25, 0.55, 1.0),
        min=0.0,
        max=1.0,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_future_color: bpy.props.FloatVectorProperty(
        name="Future Mesh Color",
        description="Color tint for mesh ghosts after the current frame",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.55, 0.15),
        min=0.0,
        max=1.0,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    show_mesh_past: bpy.props.BoolProperty(
        name="Show Past Meshes",
        description="Show mesh ghosts from before the current frame",
        default=True,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    show_mesh_future: bpy.props.BoolProperty(
        name="Show Future Meshes",
        description="Show mesh ghosts from after the current frame",
        default=True,
        update=_on_mesh_ghost_setting_changed,
    )  # type: ignore[assignment]

    mesh_ghost_sources: bpy.props.StringProperty(
        name="Onion Skin Sources",
        description=(
            "Objects the onion skins follow, pinned by Show Onion Skin "
            "(newline-separated names). Empty: follow the selection"
        ),
        default="",
        options={'HIDDEN'},
    )  # type: ignore[assignment]

    # ── Motion Paths ────────────────────────────────────────────────────
    motion_paths: bpy.props.CollectionProperty(type=GhostPathEntry)  # type: ignore[assignment]
    motion_paths_index: bpy.props.IntProperty(default=-1)  # type: ignore[assignment]

    paths_enabled: bpy.props.BoolProperty(
        name="Motion Paths",
        description="Draw motion paths for the pinned bones and objects",
        default=False,
        update=_on_path_setting_changed,
    )  # type: ignore[assignment]
    paths_follow_selection: bpy.props.BoolProperty(
        name="Follow Selection",
        description="Also draw a grey path for whatever is selected right now",
        default=False,
        update=_on_path_window_changed,
    )  # type: ignore[assignment]
    paths_show_markers: bpy.props.BoolProperty(
        name="Markers on Paths",
        description="Generate draggable markers on pinned paths: sampled points in count mode, keyframes in frame-range mode. "
                    "Head paths show location markers; Tail paths also show rotation markers",
        default=False,
        update=_on_paths_show_markers_changed,
    )  # type: ignore[assignment]
    paths_show_key_dots: bpy.props.BoolProperty(
        name="Key Dots", description="Mark keyframes on each path", default=True,
    )  # type: ignore[assignment]
    paths_show_frame_numbers: bpy.props.BoolProperty(
        name="Frame Numbers", description="Label each sampled frame", default=False,
    )  # type: ignore[assignment]
    paths_range_mode: bpy.props.EnumProperty(
        name="Range",
        description="Which frames every motion path covers",
        items=[
            ('AROUND_CURSOR', "Around Playhead", "Frames before and after the playhead"),
            ('SCENE', "Scene", "The scene frame range"),
            ('CUSTOM', "Custom", "The custom range from Settings"),
        ],
        default='AROUND_CURSOR',
        update=_on_path_window_changed,
    )  # type: ignore[assignment]
    paths_before: bpy.props.IntProperty(
        name="Before", description="Frames drawn before the playhead",
        default=12, min=0, max=500, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    paths_after: bpy.props.IntProperty(
        name="After", description="Frames drawn after the playhead",
        default=12, min=0, max=500, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    paths_step: bpy.props.IntProperty(
        name="Every", description="Sample every Nth frame along the paths",
        default=1, min=1, max=24, update=_on_path_window_changed,
    )  # type: ignore[assignment]
    paths_sampling_mode: bpy.props.EnumProperty(
        name="Sampling",
        description="Place motion-line samples at regular frame intervals or at animation keyframes",
        items=[('STEP', "Frame by Frame", "Sample every N frames"),
               ('KEYFRAMES', "By Keyframe", "Sample animation keys; counts mean previous and ahead keyframes")],
        default='STEP', update=_on_path_window_changed,
    )
    paths_keyframe_skip: bpy.props.IntProperty(
        name="Every Nth Keyframe", description="Sample every Nth animation key, starting with the nearest on each side",
        default=1, min=1, max=24, update=_on_path_window_changed,
    )
    paths_use_marker_counts: bpy.props.BoolProperty(
        name="Before/After Marker Counts",
        description="Use sampled marker counts around the playhead instead of the frame range; individual path range overrides still apply",
        default=False, update=_on_path_window_changed,
    )
    paths_markers_before: bpy.props.IntProperty(
        name="Previous Markers", description="Number of sampled motion-line markers before the current frame; editing selects the count window",
        min=0, max=500, get=_get_path_markers_before,
        set=_set_path_markers_before, update=_on_path_window_changed,
    )
    paths_markers_after: bpy.props.IntProperty(
        name="Ahead Markers", description="Number of sampled motion-line markers after the current frame; editing selects the count window",
        min=0, max=500, get=_get_path_markers_after,
        set=_set_path_markers_after, update=_on_path_window_changed,
    )
    paths_style: bpy.props.EnumProperty(
        name="Style",
        description="How the path line is coloured",
        items=[('SOLID', "Solid", "One colour"), ('SPEED', "Speed", "Blue slow, red fast"),
               ('FADE', "Fade", "Fade with distance from the playhead"),
               ('SPLIT', "Split", "Each path's before-colour up to the playhead, its colour after it")],
        default='SOLID',
    )  # type: ignore[assignment]
    paths_active_glow: bpy.props.BoolProperty(
        name="Glow", description="Draw a wide faint glow under the path selected in the list", default=True,
    )  # type: ignore[assignment]
    # Design §8 decision 14 (reverses §4): Bezier handles of the location keys, drawn at each key dot.
    # Off by default; turning it on samples the handle points, so it refreshes like a window change.
    paths_show_handles: bpy.props.BoolProperty(
        name="Handles", description="Show the Bezier handles of each key's location curves at its key dot",
        default=False, update=_on_path_window_changed,
    )  # type: ignore[assignment]

    # ── Ghost Mode & Range ──────────────────────────────────────────────
    # How ghost frames are selected (subdivision vs frame-step vs
    # keyframes-only) and which frame range they cover.

    ghost_mode: bpy.props.EnumProperty(
        name="Ghost Mode",
        description="How ghost frames are selected",
        items=[
            # SUBDIVISION: recursive midpoint subdivision between keyframes (original mode)
            ("SUBDIVISION", "Subdivision", "Recursive midpoint subdivision between keyframes (original mode)"),
            # FRAME_STEP: ghost at every Nth frame
            ("FRAME_STEP", "Frame Step", "Ghost at every Nth frame"),
            # KEYFRAMES_ONLY: ghost only at keyframe positions, no in-betweens
            ("KEYFRAMES_ONLY", "Keyframes Only", "Ghost only at keyframe positions"),
        ],
        default="FRAME_STEP",
        update=_on_ghost_sampling_changed,
    )  # type: ignore[assignment]

    ghost_range_mode: bpy.props.EnumProperty(
        name="Range Mode",
        description="Which frames to generate ghosts across",
        items=[
            # AROUND_CURSOR: show N ghosts before and after the current playhead frame
            ("AROUND_CURSOR", "Around Cursor", "Show N ghosts before/after the current frame"),
            # FULL_TIMELINE: show ghosts across entire action or scene range
            ("FULL_TIMELINE", "Full Timeline", "Show ghosts across the entire action or scene range"),
            # BETWEEN_KEYS: only between adjacent keyframes (like subdivision mode)
            ("BETWEEN_KEYS", "Between Keys", "Only between adjacent keyframes (like subdivision)"),
            # CUSTOM: user-specified start/end frame range
            ("CUSTOM", "Custom Range", "User-specified start/end frame"),
        ],
        default="AROUND_CURSOR",
        update=_on_ghost_sampling_changed,
    )  # type: ignore[assignment]

    frame_step: bpy.props.IntProperty(
        name="Frame Step",
        description="Generate a ghost every N frames",
        default=2,
        min=1,
        max=24,
        update=_on_ghost_sampling_changed,
    )  # type: ignore[assignment]

    ghosts_before: bpy.props.IntProperty(
        name="Before",
        description="Number of ghost frames before the current frame (Around Cursor mode)",
        default=8,
        min=0,
        max=64,
        update=_on_ghost_sampling_changed,
    )  # type: ignore[assignment]

    ghosts_after: bpy.props.IntProperty(
        name="After",
        description="Number of ghost frames after the current frame (Around Cursor mode)",
        default=8,
        min=0,
        max=64,
        update=_on_ghost_sampling_changed,
    )  # type: ignore[assignment]

    ghost_color_mode: bpy.props.EnumProperty(
        name="Color Mode",
        description="How ghosts are colored in the viewport",
        items=[
            ("LEVEL", "By Level", "Color by subdivision level (original mode)"),
            ("TIME", "Past/Future", "Blue for past frames, orange for future"),
            ("FADE", "Proximity Fade", "Bright near cursor, fading with distance"),
            ("RAINBOW", "Rainbow", "Full spectrum spread across the frame range"),
            ("KEY_INBETWEEN", "Key/Inbetween", "Distinct colors for keyframe vs in-between ghosts"),
        ],
        default="TIME",
    )  # type: ignore[assignment]

    ghost_fade_factor: bpy.props.FloatProperty(
        name="Fade Factor",
        description="How quickly ghost opacity fades with distance from the current frame",
        default=0.7,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )  # type: ignore[assignment]

    # ── User-Configurable Colors ────────────────────────────────────────
    # Per-mode color overrides for ghost markers. Each color mode
    # (TIME, KEY_INBETWEEN, etc.) reads from these properties.

    ghost_past_color: bpy.props.FloatVectorProperty(
        name="Past Color",
        description="Color for ghosts before the current frame (Past/Future mode)",
        subtype='COLOR',
        size=3,
        default=(0.25, 0.55, 1.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    ghost_future_color: bpy.props.FloatVectorProperty(
        name="Future Color",
        description="Color for ghosts after the current frame (Past/Future mode)",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.55, 0.15),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    ghost_key_color: bpy.props.FloatVectorProperty(
        name="Key Color",
        description="Color for ghosts at keyframe positions (Key/Inbetween mode)",
        subtype='COLOR',
        size=3,
        default=(1.0, 0.85, 0.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    ghost_inbetween_color: bpy.props.FloatVectorProperty(
        name="Inbetween Color",
        description="Color for ghosts between keyframes (Key/Inbetween mode)",
        subtype='COLOR',
        size=3,
        default=(0.4, 0.75, 1.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    ghost_label_color: bpy.props.FloatVectorProperty(
        name="Label Color",
        description="Color for frame number labels displayed next to ghosts",
        subtype='COLOR',
        size=3,
        default=(0.9, 0.9, 0.9),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    ghost_min_alpha: bpy.props.FloatProperty(
        name="Min Alpha",
        description=(
            "Minimum opacity for the most distant ghosts. "
            "Higher values keep far ghosts more visible"
        ),
        default=0.15,
        min=0.0,
        max=0.5,
        subtype='FACTOR',
    )  # type: ignore[assignment]

    ghost_falloff_curve: bpy.props.EnumProperty(
        name="Falloff Curve",
        description="How ghost opacity falls off with distance from the current frame",
        items=[
            # LINEAR: straight-line fade with even reduction across the entire range
            ("LINEAR", "Linear", "Straight-line fade — even reduction across the range"),
            # SMOOTH: ease-in-out curve with gentle start/end but faster middle fade
            ("SMOOTH", "Smooth", "Ease-in-out fade — gentle start and end, faster middle"),
            # EXPONENTIAL: fast fade near cursor, slow tail for emphasis on nearby ghosts
            ("EXPONENTIAL", "Exponential", "Quick fade near cursor, slow tail — emphasis on close ghosts"),
            # CONSTANT: no falloff, all ghosts rendered at full opacity regardless of distance
            ("CONSTANT", "Constant", "No fade — all ghosts at full opacity"),
        ],
        default="LINEAR",
    )  # type: ignore[assignment]

    # ── Outline Rendering ──────────────────────────────────────────────
    # Inverted-hull outline via Solidify modifier on mesh ghosts.

    ghost_outline_enabled: bpy.props.BoolProperty(
        name="Ghost Outline",
        description="Add a solid outline (Solidify modifier) to mesh ghosts for silhouette clarity",
        default=False,
    )  # type: ignore[assignment]

    ghost_outline_width: bpy.props.FloatProperty(
        name="Outline Width",
        description="Thickness of the mesh ghost outline in scene units",
        default=0.002,
        min=0.0005,
        max=0.05,
        precision=4,
    )  # type: ignore[assignment]

    ghost_outline_color: bpy.props.FloatVectorProperty(
        name="Outline Color",
        description="Color of the mesh ghost outline edges",
        subtype='COLOR',
        size=3,
        default=(0.0, 0.0, 0.0),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    # ── Ballistic Preview ──────────────────────────────────────────────
    # Physics-informed arc preview showing where ghosts would land
    # under gravity. Non-destructive overlay for motion planning.

    show_ballistic_preview: bpy.props.BoolProperty(
        name="Ballistic Preview",
        description="Show a physics-informed arc preview of where ghosts would land under gravity",
        default=False,
    )  # type: ignore[assignment]

    ballistic_offset: bpy.props.FloatVectorProperty(
        name="Ballistic Offset",
        description="Manual offset applied to ballistic preview positions (scene units)",
        size=3,
        default=(0.0, 0.0, 0.0),
    )  # type: ignore[assignment]

    ballistic_gravity: bpy.props.FloatProperty(
        name="Ballistic Gravity",
        description="Gravity strength for ballistic preview (m/s²)",
        default=9.81,
        min=0.0,
        max=100.0,
    )  # type: ignore[assignment]

    ballistic_gravity_axis: bpy.props.EnumProperty(
        name="Gravity Axis",
        description="Axis along which gravity acts for ballistic preview",
        items=[
            # X: gravity acts along negative X axis
            ("X", "X", "Gravity along -X"),
            # Y: gravity acts along negative Y axis
            ("Y", "Y", "Gravity along -Y"),
            # Z: gravity acts along negative Z axis (downward in standard Blender orientation)
            ("Z", "Z", "Gravity along -Z"),
        ],
        default="Z",
    )  # type: ignore[assignment]

    # ── Archetype Preview / Generate ───────────────────────────────────
    # Generative physics-feel tools.  The animator selects an archetype
    # (PENDULUM, BOUNCE, etc.), tunes amplitude and axis, previews the
    # displacement overlay, then stamps keyframes with "Stamp to Keys".
    # Naming follows the show_ballistic_preview / show_diff_overlay
    # convention established throughout this PropertyGroup.

    show_archetype_preview: bpy.props.BoolProperty(
        name="Archetype Preview",
        description=(
            "Show a physics-feel displacement overlay for the selected "
            "archetype.  Non-destructive — stamp to keyframes separately"
        ),
        default=False,
    )  # type: ignore[assignment]

    archetype_active: bpy.props.EnumProperty(
        name="Archetype",
        description="Physics-feel curve shape to preview and stamp",
        items=[
            ("PENDULUM",   "Pendulum",   "Damped swing — oscillates out from rest and settles back"),
            ("BOUNCE",     "Bounce",     "Impact arcs — decaying parabolic bounces toward the floor"),
            ("SETTLE",     "Settle",     "Exponential approach — accelerates toward target and arrives"),
            ("WOBBLE",     "Wobble",     "Decaying ring — symmetric oscillation fading to rest after impulse"),
            ("SPRINGBACK", "Springback", "Overshoot cubic — snaps past target, returns toward rest"),
        ],
        default="BOUNCE",
    )  # type: ignore[assignment]

    archetype_amplitude: bpy.props.FloatProperty(
        name="Amplitude",
        description="Peak displacement applied by the archetype (scene units)",
        default=1.0,
        min=0.001,
        max=100.0,
    )  # type: ignore[assignment]

    archetype_axis: bpy.props.EnumProperty(
        name="Axis",
        description="World-space axis along which the archetype displacement is applied",
        items=[
            ("X", "X", "Apply displacement along the X axis"),
            ("Y", "Y", "Apply displacement along the Y axis"),
            ("Z", "Z", "Apply displacement along the Z axis"),
        ],
        default="Z",
    )  # type: ignore[assignment]

    archetype_start_frame: bpy.props.IntProperty(
        name="Start Frame",
        description="First frame of the archetype bake range",
        default=1,
        min=0,
    )  # type: ignore[assignment]

    archetype_end_frame: bpy.props.IntProperty(
        name="End Frame",
        description="Last frame (inclusive) of the archetype bake range",
        default=24,
        min=1,
    )  # type: ignore[assignment]

    show_arc_lines: bpy.props.BoolProperty(
        name="Show Arc Lines",
        description="Draw continuous trajectory lines through ghost positions across the timeline",
        default=True,
        update=_on_arc_lines_changed,
    )  # type: ignore[assignment]

    arc_line_style: bpy.props.EnumProperty(
        name="Arc Style",
        description="Visual style for the trajectory arc lines",
        items=[
            # SOLID: render trajectory as a solid monochromatic line
            ("SOLID", "Solid", "Solid colored line"),
            # SPEED: color-code the line by local speed (blue=slow, red=fast)
            ("SPEED", "Speed Colored", "Blue where slow, red where fast"),
            # FADE: line opacity fades with distance from the current frame
            ("FADE", "Fade", "Line fades with distance from the cursor"),
        ],
        default="SPEED",
    )  # type: ignore[assignment]

    show_frame_numbers: bpy.props.BoolProperty(
        name="Show Frame Numbers",
        description="Display frame numbers next to each ghost marker",
        default=False,
    )  # type: ignore[assignment]

    # ── Live Generation ────────────────────────────────────────────────
    # Auto-regeneration settings that update ghosts whenever the
    # playhead moves. Throttling prevents CPU overload.

    live_point_ghosts: bpy.props.BoolProperty(
        name="Live Update Markers",
        description=(
            "Update markers when the timeline changes. Off keeps their last snapshot "
            "while scrubbing. Animation edits refresh it after you finish moving; "
            "updates pause during a move, rotation or scale"
        ),
        default=False,
    )  # type: ignore[assignment]

    live_mesh_ghosts: bpy.props.BoolProperty(
        name="Live Update Skin",
        description=(
            "Update onion skins when the timeline changes. Off keeps their last snapshot "
            "while scrubbing. Animation edits refresh it after you finish moving; "
            "updates pause during a move, rotation or scale"
        ),
        default=False,
    )  # type: ignore[assignment]

    live_throttle_ms: bpy.props.IntProperty(
        name="Throttle (ms)",
        description=(
            "Minimum milliseconds between live updates. "
            "Lower = more responsive but heavier on CPU. "
            "50ms ≈ 20 updates/sec, 100ms ≈ 10 updates/sec"
        ),
        default=50,
        min=16,
        max=500,
    )  # type: ignore[assignment]

    live_freeze: bpy.props.BoolProperty(
        name="Freeze",
        description=(
            "Temporarily pause all live ghost updates without disabling the feature. "
            "Useful during playback scrubbing or heavy scene operations"
        ),
        default=False,
    )  # type: ignore[assignment]

    # ── Editing Mode (v1 feature: Model A / Model B) ──────────────────
    # Controls what happens when a ghost drag is confirmed.

    editing_mode: bpy.props.EnumProperty(
        name="Editing Mode",
        description="What happens when you confirm a ghost drag",
        items=[
            # RESHAPE: adjust bezier handles so the curve passes through the new position (Model B)
            ("RESHAPE", "Reshape Handles",
             "Adjust bezier handles to hit the target position — non-destructive, no new keyframes"),
            # INSERT_KEY: insert a real keyframe at the ghost's frame with the new value (Model A)
            ("INSERT_KEY", "Insert Keyframe",
             "Insert a real keyframe at the ghost position — the ghost becomes a key"),
        ],
        default="RESHAPE",
    )  # type: ignore[assignment]

    smooth_neighbors_on_commit: bpy.props.BoolProperty(
        name="Smooth Neighbors on Commit",
        description=(
            "After inserting a keyframe from a ghost drag (INSERT_KEY mode), "
            "smooth the handles of the two adjacent keyframes for a cleaner "
            "curve transition through the new key"
        ),
        default=False,
    )  # type: ignore[assignment]

    # ── Keyframe Marker Display ────────────────────────────────────────
    # Visual distinction between keyframe positions and ghost in-betweens.

    show_keyframe_markers: bpy.props.BoolProperty(
        name="Show Keyframe Markers",
        description=(
            "Render keyframe positions on the trail with a distinct visual style "
            "(larger, different color) so they stand out from ghost in-betweens"
        ),
        default=True,
    )  # type: ignore[assignment]

    keyframe_marker_color: bpy.props.FloatVectorProperty(
        name="Keyframe Marker Color",
        description="Color for keyframe position markers on the motion trail",
        subtype='COLOR',
        size=4,
        default=(1.0, 0.85, 0.0, 0.90),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    show_key_bookends: bpy.props.BoolProperty(
        name="Show Key Bookends",
        description=(
            "Always show keyframe markers at the two keyframes immediately "
            "before and after the ghost range, even if those frames are "
            "outside the configured range. Helps maintain context."
        ),
        default=True,
    )  # type: ignore[assignment]

    key_bookend_color: bpy.props.FloatVectorProperty(
        name="Key Bookend Color",
        description="Color for bookend keyframe markers outside the ghost range",
        subtype='COLOR',
        size=4,
        default=(0.8, 0.8, 0.8, 0.5),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    # ── Hover Display ──────────────────────────────────────────────────
    # Frame label shown when the cursor hovers over a ghost.

    show_hover_frame_label: bpy.props.BoolProperty(
        name="Show Frame Label on Hover",
        description="Display the frame number when hovering over a ghost marker",
        default=True,
    )  # type: ignore[assignment]

    hover_highlight_color: bpy.props.FloatVectorProperty(
        name="Hover Highlight Color",
        description="Color of the highlight ring shown when hovering over a ghost",
        subtype='COLOR',
        size=4,
        default=(0.8, 0.9, 1.0, 0.9),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    # ── Sculpt Falloff ────────────────────────────────────────────────
    # Controls how dragging one ghost affects its neighbors in the chain.

    sculpt_falloff_radius: bpy.props.IntProperty(
        name="Falloff Radius",
        description=(
            "Number of frames around the dragged ghost that are affected. "
            "0 means only the dragged ghost moves (single-ghost mode). "
            "Higher values create smoother sculpted adjustments"
        ),
        default=0,
        min=0,
        max=20,
    )  # type: ignore[assignment]

    sculpt_falloff_curve: bpy.props.EnumProperty(
        name="Falloff Curve",
        description="Shape of the falloff curve applied to neighboring ghosts",
        items=[
            ("LINEAR", "Linear", "Linear falloff from center to edge"),
            ("SMOOTH", "Smooth", "Smooth (cosine) falloff — natural feel"),
            ("SHARP", "Sharp", "Sharp falloff — strong center, fast drop"),
        ],
        default="SMOOTH",
    )  # type: ignore[assignment]

    # ── Visual Diff Mode ──────────────────────────────────────────────
    # Per-bone warm/cool difference overlay against a pinned reference frame.

    show_diff_overlay: bpy.props.BoolProperty(
        name="Visual Diff Mode",
        description=(
            "Show a per-bone warm/cool overlay comparing the current pose "
            "against a pinned reference frame.  Pin a frame with the "
            "'Pin Diff Reference' operator"
        ),
        default=False,
    )  # type: ignore[assignment]

    diff_anchor_frame: bpy.props.IntProperty(
        name="Diff Reference Frame",
        description="Frame number pinned as the Visual Diff reference pose",
        default=0,
        min=0,
    )  # type: ignore[assignment]

    diff_cool_color: bpy.props.FloatVectorProperty(
        name="Diff Cool Color",
        description="Color for bones that have moved less than average (cool end of diff spectrum)",
        subtype='COLOR',
        size=4,
        default=(0.2, 0.4, 1.0, 0.75),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    diff_warm_color: bpy.props.FloatVectorProperty(
        name="Diff Warm Color",
        description="Color for bones that have moved more than average (warm end of diff spectrum)",
        subtype='COLOR',
        size=4,
        default=(1.0, 0.25, 0.05, 0.75),
        min=0.0,
        max=1.0,
    )  # type: ignore[assignment]

    diff_max_distance: bpy.props.FloatProperty(
        name="Diff Max Distance",
        description=(
            "World-space distance considered 100% movement for diff coloring. "
            "Bones moving further than this value are fully warm"
        ),
        default=0.5,
        min=0.001,
        max=10.0,
        precision=3,
    )  # type: ignore[assignment]

    # ── Mode Label HUD ────────────────────────────────────────────────
    # Persistent 2D text overlay showing the active ghost display mode.

    show_mode_label: bpy.props.BoolProperty(
        name="Show Mode Label",
        description=(
            "Display a persistent HUD label in the viewport showing the "
            "active ghost mode (Live, Snapshot, Diff, or Bake in Progress)"
        ),
        default=True,
    )  # type: ignore[assignment]

    # ── Timeline Skeleton View ────────────────────────────────────────
    # Collapse arc display to root/spine bones only for a clean overview.

    show_skeleton_view: bpy.props.BoolProperty(
        name="Skeleton View",
        description=(
            "Collapse the motion arc to root and spine bones only. "
            "Reduces visual clutter on dense rigs by showing a simplified skeleton trail"
        ),
        default=False,
    )  # type: ignore[assignment]

    skeleton_view_bone_filter: bpy.props.StringProperty(
        name="Skeleton Bone Filter",
        description=(
            "Comma-separated list of bone name substrings to include in Skeleton View. "
            "Leave empty to use the built-in root/spine heuristic"
        ),
        default="",
    )  # type: ignore[assignment]

    def is_level_visible(self, level: int) -> bool:
        """Check whether a given subdivision level should be displayed.

        Args:
            level: The generation level to check (1–5).

        Returns:
            bool: True if that level's visibility toggle is on.
        """
        if level < 1 or level > MAX_SUBDIVISION_LEVEL:
            return False
        return getattr(self, f"show_level_{level}", True)


# ---------------------------------------------------------------------------
# Ghost generation — recursive subdivision of f-curves
# ---------------------------------------------------------------------------

def _get_fcurve_for_channel(
    action: bpy.types.Action,
    bone_name: str,
    channel: str,
    obj: Optional[bpy.types.Object] = None,
) -> Optional[bpy.types.FCurve]:
    """Locate the FCurve in an Action matching a bone and channel path.

    Compatible with both legacy (Blender < 4.4) and slotted (5.x+) Actions.

    Args:
        action: The Blender Action containing f-curves.
        bone_name: Pose bone name, or empty string for object channels.
        channel: Channel identifier like "location.x" or "rotation_euler.z".
        obj: The owning Blender object (needed for Blender 5.x slot resolution).

    Returns:
        FCurve or None: The matching f-curve, or None if not found.
    """
    # Parse channel into data_path and array_index
    # e.g. "location.x" -> data_path="location", array_index=0
    axis_map = {"x": 0, "y": 1, "z": 2, "w": 3}

    parts = channel.rsplit(".", 1)
    if len(parts) == 2:
        prop_name = parts[0]
        axis = parts[1].lower()
        if prop_name == "rotation_quaternion":
            axis_map = {"w": 0, "x": 1, "y": 2, "z": 3}
        array_index = axis_map.get(axis, 0)
    else:
        prop_name = channel
        array_index = 0

    # Build the full data path
    if bone_name:
        data_path = f'pose.bones["{bpy.utils.escape_identifier(bone_name)}"].{prop_name}'
    else:
        data_path = prop_name

    # Use the compatibility helper that handles both legacy and slotted APIs
    return find_fcurve_in_action(action, data_path, array_index, obj=obj)


def _get_keyframe_frames(fcurve: bpy.types.FCurve) -> list[float]:
    """Extract sorted frame numbers from an f-curve's keyframe points.

    Args:
        fcurve: The f-curve to inspect.

    Returns:
        list[float]: Sorted list of frame numbers where keyframes exist.
    """
    return sorted(keypoint.co.x for keypoint in fcurve.keyframe_points)


def _frame_has_keyframe(fcurve: bpy.types.FCurve, frame: float) -> bool:
    """Check whether a frame is within KEYFRAME_SNAP_THRESHOLD of an existing keyframe.

    Args:
        fcurve: The f-curve to check against.
        frame: The frame number to test.

    Returns:
        bool: True if a real keyframe exists within the threshold.
    """
    for keypoint in fcurve.keyframe_points:
        if abs(keypoint.co.x - frame) < KEYFRAME_SNAP_THRESHOLD:
            return True
    return False


_IN_DRAW_HANDLER = False
"""Module flag to track if we're currently inside a draw handler context."""


def _get_world_position_cached(
    depsgraph: bpy.types.Depsgraph,
    scene: bpy.types.Scene,
    obj: bpy.types.Object,
    bone_name: str,
    frame: float,
    cache: dict[tuple[str, str, float], Vector],
    tail: bool = False,
) -> Vector:
    """Evaluate the world-space position of an object or bone at a given frame.

    ``tail=True`` returns the bone's tail instead of its head: rotation
    channels never move a bone's own head, so their markers follow the tail.

    Uses a cache keyed on (object_name, bone_name, frame) to avoid
    redundant scene.frame_set() calls, which are expensive.

    Args:
        depsgraph: The current dependency graph.
        scene: The active scene.
        obj: The Blender object.
        bone_name: Pose bone name, or empty string for object origin.
        frame: The frame to evaluate at.
        cache: Mutable dict used for caching results.

    Returns:
        Vector: The world-space position (copy).
    """
    # Safety: this function calls scene.frame_set() and must NEVER be called from a draw handler
    if _IN_DRAW_HANDLER:
        raise RuntimeError("_get_world_position_cached must not be called from a draw handler (calls scene.frame_set)")

    cache_key = (obj.name, bone_name, frame, tail)
    if cache_key in cache:
        return cache[cache_key].copy()

    # Evaluate every requested bone at once. The cache lasts for this pass only.
    # frame_set synchronously evaluates the dependency graph.
    whole_frame = math.floor(frame)
    scene.frame_set(whole_frame, subframe=frame - whole_frame)
    evaluated = obj.evaluated_get(depsgraph)
    for name in getattr(cache, 'bone_names', (bone_name,)):
        pose_bone = evaluated.pose.bones.get(name) if name and evaluated.type == 'ARMATURE' else None
        if pose_bone is not None:
            head = evaluated.matrix_world @ pose_bone.head
            tail_position = evaluated.matrix_world @ pose_bone.tail
        else:
            if name:
                warn(f"Bone '{name}' not found on '{obj.name}'")
            head = tail_position = evaluated.matrix_world.translation
        cache[(obj.name, name, frame, False)] = head.copy()
        cache[(obj.name, name, frame, True)] = tail_position.copy()
    return cache[cache_key].copy()


class _WorldPositionCache(dict):
    """One frame evaluation supplies positions for every requested bone."""
    def __init__(self, bones):
        super().__init__()
        self.bone_names = tuple(dict.fromkeys(bones or ['']))


def _find_surrounding_keyframes(
    keyframes: list[float],
    frame: float,
) -> tuple[float, float]:
    """Find the two keyframes that bracket a given frame.

    Scans the sorted keyframe list and returns the pair (left, right)
    where ``left <= frame < right``. If the frame is beyond all
    keyframes, both values default to the nearest endpoint.

    Args:
        keyframes: Sorted list of keyframe frame numbers.
        frame: The frame to locate within the keyframe list.

    Returns:
        tuple[float, float]: (left_keyframe, right_keyframe).
    """
    if not keyframes:
        return (0.0, 0.0)

    for index, keyframe_time in enumerate(keyframes):
        if keyframe_time > frame:
            left = keyframes[index - 1] if index > 0 else keyframe_time
            return (left, keyframe_time)

    # Frame is at or beyond the last keyframe.
    return (keyframes[-1], keyframes[-1])


def _subdivide_segment(
    fcurve: bpy.types.FCurve,
    frame_a: float,
    frame_b: float,
    level: int,
    max_level: int,
    obj: bpy.types.Object,
    bone_name: str,
    channel: str,
    scene: bpy.types.Scene,
    depsgraph: bpy.types.Depsgraph,
    cache: dict[tuple[str, str, float], Vector],
    results: list[Ghost],
) -> None:
    """Recursively generate ghosts between two parent frames.

    At each level, a midpoint ghost is created. If the current level is
    below max_level, the function recurses into the left and right
    sub-segments created by the new midpoint.

    Args:
        fcurve: The f-curve being subdivided.
        frame_a: Left parent frame number.
        frame_b: Right parent frame number.
        level: Current subdivision depth (starts at 1).
        max_level: Maximum subdivision depth to reach.
        obj: The Blender object owning this channel.
        bone_name: Pose bone name or empty string.
        channel: Channel identifier (e.g. "location.x").
        scene: The active scene (for frame_set).
        depsgraph: The dependency graph (for evaluation).
        cache: Position cache dict to reuse across calls.
        results: Accumulator list for generated Ghost objects.
    """
    if frame_a >= frame_b:
        return

    if level > max_level:
        return

    mid_frame = (frame_a + frame_b) / 2.0

    # Skip if a real keyframe already exists at or near this frame
    if _frame_has_keyframe(fcurve, mid_frame):
        return

    # Sample the f-curve value at the midpoint
    local_value = fcurve.evaluate(mid_frame)

    # Get world position for viewport display
    world_pos = _get_world_position_cached(
        depsgraph, scene, obj, bone_name, mid_frame, cache,
        tail=is_rotation_channel(channel),
    )

    ghost = Ghost(
        frame=mid_frame,
        world_position=world_pos,
        local_value=local_value,
        channel=channel,
        bone_name=bone_name,
        object_name=obj.name,
        parent_frame_a=frame_a,
        parent_frame_b=frame_b,
        generation_level=level,
    )
    results.append(ghost)

    # Recurse into sub-segments for deeper subdivision levels
    if level < max_level:
        _subdivide_segment(
            fcurve, frame_a, mid_frame, level + 1, max_level,
            obj, bone_name, channel, scene, depsgraph, cache, results,
        )
        _subdivide_segment(
            fcurve, mid_frame, frame_b, level + 1, max_level,
            obj, bone_name, channel, scene, depsgraph, cache, results,
        )


def _resolve_animation_target(
    obj: bpy.types.Object,
    armature: Optional[bpy.types.Object],
) -> Optional[tuple[bpy.types.Object, bpy.types.Action]]:
    """Resolve the target object and its action for ghost generation.

    Determines which object holds animation data (preferring armature over
    mesh) and retrieves its active action.

    Args:
        obj: The base Blender object.
        armature: The armature object, or None for non-armature targets.

    Returns:
        tuple[Object, Action] or None: The target object and its action,
            or None if no valid animation target was found.
    """
    target_obj = armature if armature else obj
    if not target_obj:
        warn("No valid object provided for ghost generation.")
        return None

    action = None
    if target_obj.animation_data:
        action = target_obj.animation_data.action

    if not action:
        debug(f"No action found on '{target_obj.name}'")
        return None

    return (target_obj, action)


@sampling_operation
def generate_ghosts(
    obj: bpy.types.Object,
    armature: Optional[bpy.types.Object],
    bones: list[str],
    channels: list[str],
    level: int,
    frame_range: Optional[tuple[int, int]] = None,
) -> list[Ghost]:
    """Generate ghosts for the specified object, bones, and channels.

    This is the main entry point for ghost generation.  It iterates over
    each requested channel, finds adjacent keyframe pairs, and recursively
    subdivides each segment up to the requested level.

    Args:
        obj: The Blender object whose f-curves to sample.  For armatures,
             this should be the armature object itself.
        armature: The armature object (same as obj for armature channels,
                  None for plain object channels).  Kept as a separate
                  param for clarity in multi-object workflows.
        bones: List of pose bone names to generate ghosts for.  Pass an
               empty list for object-level channels.
        channels: List of channel identifiers to process, e.g.
                  ["location.x", "location.y", "location.z"].
        level: Maximum subdivision depth (1–5).
        frame_range: Optional (start, end) frame range.  If None, the
                     full f-curve range is used.

    Returns:
        list[Ghost]: All generated Ghost objects across all bones/channels.
    """
    if frame_range and frame_range[0] >= frame_range[1]:
        warn(f"Invalid frame range: start ({frame_range[0]}) >= end ({frame_range[1]})")
        frame_range = None

    level = max(1, min(level, MAX_SUBDIVISION_LEVEL))

    # Determine which object holds the action
    result = _resolve_animation_target(obj, armature)
    if result is None:
        return []
    target_obj, action = result

    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    # Position cache to minimize redundant frame_set calls
    position_cache = _WorldPositionCache(bones)

    all_ghosts: list[Ghost] = []

    # If no bones specified, process as object-level channels
    bone_list = bones if bones else [""]

    for bone_name in bone_list:
        for channel in channels:
            fcurve = _get_fcurve_for_channel(action, bone_name, channel, obj=target_obj)
            if fcurve is None:
                # No f-curve for this bone/channel combo — skip silently
                continue

            keyframes = _get_keyframe_frames(fcurve)
            if len(keyframes) < 2:
                # Need at least two keyframes to create midpoints
                continue

            # Apply frame range filter if specified
            for i in range(len(keyframes) - 1):
                frame_a = keyframes[i]
                frame_b = keyframes[i + 1]

                # Skip segments entirely outside the requested range
                if frame_range:
                    # Skip segments entirely outside the visible frame range
                    if frame_b < frame_range[0] or frame_a > frame_range[1]:
                        continue

                _subdivide_segment(
                    fcurve=fcurve,
                    frame_a=frame_a,
                    frame_b=frame_b,
                    level=1,
                    max_level=level,
                    obj=target_obj,
                    bone_name=bone_name,
                    channel=channel,
                    scene=scene,
                    depsgraph=depsgraph,
                    cache=position_cache,
                    results=all_ghosts,
                )

    return all_ghosts


@sampling_operation
def generate_ghosts_frame_step(
    obj: bpy.types.Object,
    armature: Optional[bpy.types.Object],
    bones: list[str],
    channels: list[str],
    frame_list: list[float],
    anchor: Optional[str] = None,
) -> list[Ghost]:
    """Generate ghosts at explicit frame positions (frame-by-frame mode).

    Unlike subdivision mode, this creates a ghost at every specified frame
    regardless of where keyframes are.  This is the "every Nth frame" mode.

    Args:
        obj: The Blender object.
        armature: The armature object (or None).
        bones: List of pose bone names.
        channels: List of channel identifiers.
        frame_list: Explicit list of frame numbers to generate ghosts at.
        anchor: Optional HEAD/TAIL override for markers on a motion path.

    Returns:
        list[Ghost]: All generated ghosts.
    """
    result = _resolve_animation_target(obj, armature)
    if result is None:
        return []
    target_obj, action = result

    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    position_cache = _WorldPositionCache(bones)
    all_ghosts: list[Ghost] = []

    bone_list = bones if bones else [""]

    for bone_name in bone_list:
        for channel in channels:
            fcurve = _get_fcurve_for_channel(action, bone_name, channel, obj=target_obj)
            if fcurve is None:
                continue

            keyframes = _get_keyframe_frames(fcurve)

            for frame in frame_list:
                # Skip if this frame IS a keyframe (we only want in-betweens)
                if _frame_has_keyframe(fcurve, frame):
                    continue

                local_value = fcurve.evaluate(frame)
                world_pos = _get_world_position_cached(
                    depsgraph, scene, target_obj, bone_name, frame, position_cache,
                    tail=is_rotation_channel(channel) if anchor is None else anchor == 'TAIL',
                )

                # Determine which two keyframes this frame sits between.
                parent_a, parent_b = _find_surrounding_keyframes(keyframes, frame)

                ghost = Ghost(
                    frame=frame,
                    world_position=world_pos,
                    local_value=local_value,
                    channel=channel,
                    bone_name=bone_name,
                    object_name=target_obj.name,
                    parent_frame_a=parent_a,
                    parent_frame_b=parent_b,
                    generation_level=1,
                )
                all_ghosts.append(ghost)

    return all_ghosts


@sampling_operation
def generate_ghosts_at_keyframes(
    obj: bpy.types.Object,
    armature: Optional[bpy.types.Object],
    bones: list[str],
    channels: list[str],
    frame_range: Optional[tuple[int, int]] = None,
    anchor: Optional[str] = None,
    frames: Optional[set[float]] = None,
) -> list[Ghost]:
    """Generate ghosts at keyframe positions only.

    Useful for seeing poses at key positions without in-betweens.

    Args:
        obj: The Blender object.
        armature: The armature object (or None).
        bones: Pose bone names.
        channels: Channel identifiers.
        frame_range: Optional frame range.
        anchor: 'HEAD' or 'TAIL' places every marker on that bone point (a motion
            path's anchor); None keeps the per-channel choice (rotation -> tail).
        frames: Optional set of frames; keys on other frames are skipped.

    Returns:
        list[Ghost]: Ghosts at keyframe positions.
    """
    result = _resolve_animation_target(obj, armature)
    if result is None:
        return []
    target_obj, action = result

    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    position_cache = _WorldPositionCache(bones)
    all_ghosts: list[Ghost] = []

    bone_list = bones if bones else [""]

    for bone_name in bone_list:
        for channel in channels:
            fcurve = _get_fcurve_for_channel(action, bone_name, channel, obj=target_obj)
            if fcurve is None:
                continue

            keyframes = _get_keyframe_frames(fcurve)

            for frame in keyframes:
                if frame_range is not None and (frame < frame_range[0] or frame > frame_range[1]):
                    continue
                if frames is not None and float(frame) not in frames:
                    continue

                local_value = fcurve.evaluate(frame)
                tail = is_rotation_channel(channel) if anchor is None else anchor == 'TAIL'
                world_pos = _get_world_position_cached(
                    depsgraph, scene, target_obj, bone_name, frame, position_cache, tail=tail,
                )

                ghost = Ghost(
                    frame=frame,
                    world_position=world_pos,
                    local_value=local_value,
                    channel=channel,
                    bone_name=bone_name,
                    object_name=target_obj.name,
                    parent_frame_a=frame,
                    parent_frame_b=frame,
                    generation_level=0,  # 0 = keyframe ghost
                )
                all_ghosts.append(ghost)

    return all_ghosts


def build_frame_list_from_settings(
    settings: GhostToolSceneSettings,
    scene: bpy.types.Scene,
) -> list[float]:
    """Build the list of frames to ghost based on current settings.

    This centralises the frame-list logic for FRAME_STEP mode. Generates
    frame lists based on the ghost_range_mode setting: AROUND_CURSOR,
    FULL_TIMELINE, or CUSTOM range.

    Args:
        settings: GhostToolSceneSettings instance containing ghost_range_mode,
                  frame_step, and range parameters.
        scene: The Blender scene (for frame bounds and current playhead position).

    Returns:
        list[float]: Sorted list of frames to generate ghosts at.
    """
    current = scene.frame_current
    step = max(1, settings.frame_step)
    range_mode = settings.ghost_range_mode

    if range_mode == "AROUND_CURSOR":
        frames = []
        for i in range(1, settings.ghosts_before + 1):
            frames.append(current - i * step)
        for i in range(1, settings.ghosts_after + 1):
            frames.append(current + i * step)
        # Clamp to scene range
        start = scene.frame_start
        end = scene.frame_end
        frames = [f for f in frames if start <= f <= end]
        return sorted(frames)

    elif range_mode == "FULL_TIMELINE":
        start = scene.frame_start
        end = scene.frame_end
        frames = []
        frame = start
        while frame <= end:
            if frame != current:  # skip current frame
                frames.append(float(frame))
            frame += step
        return frames

    elif range_mode == "BETWEEN_KEYS":
        # Check generation mode and warn if incompatible
        # Note: We need to determine generation_mode from context
        # For now, check if this is being called in a frame_step context
        if hasattr(settings, 'ghost_mode') and settings.ghost_mode == "FRAME_STEP":
            warn("BETWEEN_KEYS range mode is not supported with FRAME_STEP generation. Use SUBDIVISION mode instead.")
        return []  # Will be handled by the subdivision generator

    elif range_mode == "CUSTOM":
        start = settings.custom_range_start
        end = settings.custom_range_end
        frames = []
        frame = start
        while frame <= end:
            if frame != current:
                frames.append(float(frame))
            frame += step
        return frames

    return []


def generate_and_store_ghosts(
    context: bpy.types.Context,
    obj: bpy.types.Object,
    armature: Optional[bpy.types.Object],
    bones: list[str],
    channels: list[str],
    level: int,
    frame_range: Optional[tuple[int, int]] = None,
    clear_existing: bool = True,
) -> int:
    """Generate ghosts and add them to the scene's GhostStore.

    Reads ghost_mode from scene settings to choose between subdivision,
    frame-step, or keyframes-only generation.

    Args:
        context: The current Blender context.
        obj: The Blender object to generate ghosts for.
        armature: The armature object (or None).
        bones: List of pose bone names.
        channels: List of channel identifiers.
        level: Maximum subdivision depth (for SUBDIVISION mode).
        frame_range: Optional frame range constraint.
        clear_existing: If True, clear the store before adding new ghosts.

    Returns:
        int: Number of ghosts generated.
    """
    store = GhostStore.get(context.scene)

    # Before clearing, build a lookup of old ghosts by identity tuple
    old_ghost_map = {}
    if clear_existing:
        for g in store:
            identity = (g.object_name, g.bone_name, g.channel, round(g.frame, 4))
            old_ghost_map[identity] = g
        store.clear()

    settings = context.scene.ghost_tool
    mode = getattr(settings, 'ghost_mode', 'SUBDIVISION')

    if mode == "FRAME_STEP":
        frame_list = build_frame_list_from_settings(settings, context.scene)
        ghosts = generate_ghosts_frame_step(obj, armature, bones, channels, frame_list)
    elif mode == "KEYFRAMES_ONLY":
        ghosts = generate_ghosts_at_keyframes(obj, armature, bones, channels, frame_range)
    else:
        # SUBDIVISION — original mode
        ghosts = generate_ghosts(obj, armature, bones, channels, level, frame_range)

    # After generation, preserve UID/state from old ghosts
    for ghost in ghosts:
        identity = (ghost.object_name, ghost.bone_name, ghost.channel, round(ghost.frame, 4))
        old = old_ghost_map.get(identity)
        if old is not None:
            ghost.uid = old.uid
            ghost.is_selected = old.is_selected
            ghost.is_pinned = old.is_pinned
        store.add(ghost)

    return len(ghosts)


# ---------------------------------------------------------------------------
# Default channel lists for common animation workflows
# ---------------------------------------------------------------------------

# LOCATION_CHANNELS, ROTATION_*_CHANNELS and MOTION_CHANNELS live in motion_channels.
SCALE_CHANNELS: list[str] = ["scale.x", "scale.y", "scale.z"]
ALL_TRANSFORM_CHANNELS: list[str] = (
    LOCATION_CHANNELS + ROTATION_EULER_CHANNELS + SCALE_CHANNELS
)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class GHOST_OT_initialize(bpy.types.Operator):
    """Initialize Ghost Tool on the current scene.

    This operator attaches the GhostToolSceneSettings PropertyGroup
    to bpy.types.Scene if it is missing.  It is shown as a button in
    the Ghost Tool menu when the addon detects that ``scene.ghost_tool`` does
    not exist — typically after a failed registration or a file that
    was saved before the addon was installed.
    """

    bl_idname = "ghost_tool.initialize"
    bl_label = "Initialize Ghost Tool"
    bl_description = "Attach Ghost Tool settings to this scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Ensure the scene-level ghost_tool property exists.

        If the GhostToolSceneSettings class is not yet registered with
        Blender, it is registered first.  Then the PointerProperty is
        attached to bpy.types.Scene.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} on success.
        """
        # Make sure the PropertyGroup class is registered
        if not _is_class_registered(GhostToolSceneSettings):
            bpy.utils.register_class(GhostToolSceneSettings)

        # Attach the PointerProperty if missing
        if not hasattr(bpy.types.Scene, "ghost_tool"):
            bpy.types.Scene.ghost_tool = bpy.props.PointerProperty(
                type=GhostToolSceneSettings,
                name="Ghost Tool Settings",
                description="Scene-level settings for the Ghost Tool addon",
            )

        self.report({'INFO'}, "Ghost Tool initialized")

        # Force a full UI redraw so panels update immediately
        if context.screen:
            for area in context.screen.areas:
                area.tag_redraw()

        return {'FINISHED'}


def _is_class_registered(cls) -> bool:
    """Check whether a Blender RNA class is already registered.

    Args:
        cls: The class to check (e.g. a PropertyGroup subclass).

    Returns:
        bool: True if the class is registered with Blender.
    """
    try:
        bpy.utils.register_class(cls)
        bpy.utils.unregister_class(cls)
        # If we got here, it was NOT registered (we just did a round-trip).
        return False
    except (RuntimeError, ValueError):
        # Already registered: Blender raises ValueError here (RuntimeError on
        # older builds).  Either way the class is present.
        return True


CLASSES: tuple[type, ...] = (
    GhostPathEntry,
    GhostToolSceneSettings,
    GHOST_OT_initialize,
)


def register() -> None:
    """Register ghost_data module classes and attach scene properties."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.ghost_tool = bpy.props.PointerProperty(
        type=GhostToolSceneSettings,
        name="Ghost Tool Settings",
        description="Scene-level settings for the Ghost Tool addon",
    )


def unregister() -> None:
    """Unregister ghost_data module classes and clean up scene properties."""
    # Clean up the in-memory store
    GhostStore.clear_all_instances()

    if hasattr(bpy.types.Scene, "ghost_tool"):
        del bpy.types.Scene.ghost_tool

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ---------------------------------------------------------------------------
# Test notes (for manual verification in Blender's Python console)
# ---------------------------------------------------------------------------
#
# >>> from ghost_tool.ghost_data import Ghost, GhostStore, generate_ghosts
#
# Test 1: Ghost creation and serialization
# >>> g = Ghost(frame=5.0, channel="location.x", object_name="Cube")
# >>> d = g.to_dict()
# >>> g2 = Ghost.from_dict(d)
# >>> assert g.frame == g2.frame and g.uid == g2.uid
#
# Test 2: GhostStore CRUD
# >>> store = GhostStore.get(bpy.context.scene)
# >>> store.clear()
# >>> store.add(Ghost(frame=1.0, generation_level=1))
# >>> store.add(Ghost(frame=2.0, generation_level=2))
# >>> assert len(store) == 2
# >>> assert len(store.filter_by_level(1)) == 1
# >>> store.clear_level(2)
# >>> assert len(store) == 1
#
# Test 3: Ghost generation on a cube with 3 keyframes at frames 1, 25, 50
# >>> obj = bpy.context.active_object  # must be a Cube with an action
# >>> ghosts = generate_ghosts(obj, None, [], ["location.x"], level=2)
# >>> print(f"Generated {len(ghosts)} ghosts")
# >>> # Level 1: 2 ghosts (midpoints of [1,25] and [25,50])
# >>> # Level 2: 4 more ghosts (midpoints of those sub-segments)
# >>> # Total: 6 ghosts
