"""
session_state.py — Centralized transient state for Ghost Tool viewport interaction.

This module owns all per-scene session-local state that does NOT survive
undo/redo or file save/load.  It provides a single ``SessionState`` class
holding:

- **hovered_ghost_uid**: The uid of the ghost currently under the cursor
  (used by the draw handler for highlight rendering and frame label display).
- **selection_set**: A set of ghost uids that are actively selected
  (populated via shift-click; used by the draw handler for multi-select rings).

Design notes:
    - One ``SessionState`` instance per scene, accessed via ``SessionState.get(scene)``.
    - All fields are transient — regenerating ghosts clears hover/selection
      because ghost uids change on regeneration.
    - Drawing code reads from this module.  Interaction code writes to it.
    - No Blender PropertyGroup is used — this is pure Python in-memory state.
"""

from __future__ import annotations

from typing import Optional

import bpy
from .utils import get_scene_id, debug


class CurveTransaction:
    """Bounded original curves. Rollback never resolves a replacement by name."""

    def __init__(self, scene, targets):
        from .target_binding import CurveBinding, add_gesture_tag
        from .fcurve_utils import snapshot_fcurve
        self.scene, self.entries, self.finished = scene, [], False
        seen = set()
        try:
            for obj, bone, channel in targets:
                binding = CurveBinding.capture(scene, obj, bone, channel)
                curve, reason = binding.resolve(scene)
                if reason:
                    raise ValueError(reason)
                if curve.as_pointer() not in seen:
                    seen.add(curve.as_pointer())
                    # Temporary tag: a curve replaced mid-gesture is never
                    # written. finish() removes it before any undo push.
                    binding.gesture_tag = add_gesture_tag(curve)
                    self.entries.append((binding, snapshot_fcurve(curve), obj.name, bone))
        except Exception:
            self._release_tags()
            raise

    def _release_tags(self):
        from .target_binding import remove_gesture_tags
        by_action = {}
        for binding, _keys, _obj_name, _bone_name in self.entries:
            if binding.gesture_tag:
                by_action.setdefault(binding.action, []).append(binding.gesture_tag)
                binding.gesture_tag = ''
        for action, names in by_action.items():
            remove_gesture_tags(action, names)

    def valid(self):
        if self.finished:
            return False
        for binding, _keys, object_name, bone_name in self.entries:
            curve, reason = binding.resolve(self.scene)
            # Modal marker/path caches still contain names. Abort on rename,
            # while rollback can safely follow the original identity.
            if reason or binding.obj.name != object_name or binding.bone_name != bone_name:
                return False
        return True

    def rollback(self):
        if self.finished:
            return
        self.finished = True
        from .fcurve_utils import restore_fcurve
        for binding, keys, _obj_name, _bone_name in self.entries:
            curve, reason = binding.resolve(self.scene)
            if not reason:
                restore_fcurve(curve, keys)
        self._release_tags()
        from .snapshot import SnapshotStore
        SnapshotStore._refresh(self.scene)

    def finish(self):
        self.finished = True
        self._release_tags()
        self.entries.clear()


class SessionState:
    """Per-scene transient state for viewport interaction.

    Holds hover and selection information that the draw handler reads
    and modal operators write.  Cleared automatically when ghosts are
    regenerated (because uids change).

    Usage:
        state = SessionState.get(context.scene)
        state.hovered_ghost_uid = ghost.uid
        state.toggle_selection(ghost.uid)
    """

    # Class-level dict mapping scene names to SessionState instances.
    _instances: dict[str, SessionState] = {}
    _gesture_owner = None
    _gesture_scene = None
    _cancel = None
    _validate = None
    _windows = ()
    _workspace = None
    _cancelling = False

    @classmethod
    def available(cls, owner=None):
        return cls._gesture_owner is None or cls._gesture_owner is owner

    @classmethod
    def poll_available(cls, operator):
        if not cls.available():
            operator.poll_message_set("Finish or cancel the current Ghost Tool gesture first")
            return False
        return True

    @classmethod
    def begin_gesture(cls, owner, scene, *, context=None, cancel=None, validate=None):
        if not cls.available(owner):
            return False
        cls._gesture_owner, cls._gesture_scene = owner, scene
        cls._cancel, cls._validate = cancel, validate
        cls._windows = ()
        cls._workspace = None
        if context is not None and getattr(context, 'window', None) is not None:
            from . import settings_editor
            target = settings_editor._targets.get(context.window.as_pointer())
            cls._windows = tuple(w.as_pointer() for w in (context.window,
                getattr(target, 'source_window', None), getattr(target, 'editor_window', None)) if w is not None)
            cls._workspace = context.workspace.as_pointer()
        if cancel is not None and not bpy.app.timers.is_registered(_watch_gesture):
            bpy.app.timers.register(_watch_gesture, first_interval=0.1)
        cls.get(scene).drag_active = True
        return True

    @classmethod
    def end_gesture(cls, owner):
        if cls._gesture_owner is owner:
            for state in cls._instances.values():
                state.drag_active = False
            cls._gesture_owner = cls._gesture_scene = None
            cls._cancel = cls._validate = None
            cls._windows = ()
            if cls._workspace is not None:
                try:
                    window = next((w for w in bpy.context.window_manager.windows
                                   if w.workspace.as_pointer() == cls._workspace), None)
                    if window is not None:
                        with bpy.context.temp_override(window=window):
                            window.workspace.status_text_set(None)
                except (ReferenceError, RuntimeError):
                    pass
            cls._workspace = None
            if bpy.app.timers.is_registered(_watch_gesture):
                bpy.app.timers.unregister(_watch_gesture)

    @classmethod
    def valid_context(cls):
        try:
            live = {w.as_pointer(): w for w in bpy.context.window_manager.windows}
            if any(pointer not in live or live[pointer].scene != cls._gesture_scene for pointer in cls._windows):
                return False
            return cls._validate is None or cls._validate()
        except (ReferenceError, RuntimeError):
            return False

    @classmethod
    def cancel_active(cls):
        if cls._gesture_owner is None or cls._cancelling:
            return
        owner, callback = cls._gesture_owner, cls._cancel
        cls._cancelling = True
        try:
            if callback is not None:
                callback()
        except Exception as exc:
            debug(f'Gesture cleanup: {exc}')
        finally:
            cls.end_gesture(owner)
            cls._cancelling = False

    @classmethod
    def owns_gesture(cls, owner, scene):
        return cls._gesture_owner is owner and cls._gesture_scene == scene and cls.valid_context()

    def __init__(self) -> None:
        """Initialize with empty hover and selection state."""
        self.hovered_ghost_uid: Optional[str] = None
        self.selection_set: set[str] = set()
        self.drag_active = False

    # --- Singleton access per scene ---

    @classmethod
    def get(cls, scene: bpy.types.Scene) -> SessionState:
        """Retrieve or create the SessionState for the given scene.

        Args:
            scene: The Blender scene to look up.

        Returns:
            SessionState: The state associated with this scene.
        """
        key = get_scene_id(scene)
        if key not in cls._instances:
            cls._instances[key] = cls()
        return cls._instances[key]

    @classmethod
    def clear_all_instances(cls) -> None:
        """Remove all SessionState instances (used during addon unregistration)."""
        cls._instances.clear()
        cls.end_gesture(cls._gesture_owner)

    # --- Hover management ---

    def set_hover(self, ghost_uid: Optional[str]) -> None:
        """Set the currently hovered ghost uid.

        Args:
            ghost_uid: The uid of the ghost under the cursor, or None to clear.
        """
        self.hovered_ghost_uid = ghost_uid

    def clear_hover(self) -> None:
        """Clear the hover state."""
        self.hovered_ghost_uid = None

    # --- Selection management ---

    def select(self, ghost_uid: str) -> None:
        """Add a ghost to the selection set (shift-click behavior).

        Args:
            ghost_uid: The uid of the ghost to select.
        """
        self.selection_set.add(ghost_uid)

    def deselect(self, ghost_uid: str) -> None:
        """Remove a ghost from the selection set.

        Args:
            ghost_uid: The uid of the ghost to deselect.
        """
        self.selection_set.discard(ghost_uid)

    def toggle_selection(self, ghost_uid: str) -> None:
        """Toggle a ghost's selection state (for shift-click).

        Args:
            ghost_uid: The uid of the ghost to toggle.
        """
        if ghost_uid in self.selection_set:
            self.selection_set.discard(ghost_uid)
        else:
            self.selection_set.add(ghost_uid)

    def select_only(self, ghost_uid: str) -> None:
        """Select exactly one ghost, clearing all others (plain click).

        Args:
            ghost_uid: The uid of the ghost to select.
        """
        self.selection_set.clear()
        self.selection_set.add(ghost_uid)

    def clear_selection(self) -> None:
        """Clear the entire selection set."""
        self.selection_set.clear()

    def is_selected(self, ghost_uid: str) -> bool:
        """Check whether a ghost is in the selection set.

        Args:
            ghost_uid: The uid to check.

        Returns:
            bool: True if the ghost is selected.
        """
        return ghost_uid in self.selection_set

    # --- Bulk reset ---

    def clear_all(self) -> None:
        """Reset all transient state (called after ghost regeneration)."""
        self.hovered_ghost_uid = None
        self.selection_set.clear()
        self.drag_active = SessionState._gesture_owner is not None


# ---------------------------------------------------------------------------
# Undo/Redo Handler
# ---------------------------------------------------------------------------

def _watch_gesture():
    if SessionState._gesture_owner is None:
        return None
    if not SessionState.valid_context():
        SessionState.cancel_active()
        return None
    return 0.1


@bpy.app.handlers.persistent
def _before_transition(*args):
    SessionState.cancel_active()


def register():
    for handlers in (bpy.app.handlers.load_pre, bpy.app.handlers.undo_pre, bpy.app.handlers.redo_pre):
        if _before_transition not in handlers:
            handlers.append(_before_transition)


def unregister():
    SessionState.cancel_active()
    SessionState.clear_all_instances()
    for handlers in (bpy.app.handlers.load_pre, bpy.app.handlers.undo_pre, bpy.app.handlers.redo_pre):
        if _before_transition in handlers:
            handlers.remove(_before_transition)

@bpy.app.handlers.persistent
def _on_undo_redo(scene: bpy.types.Scene, *args) -> None:
    """Clear transient session state and invalidate caches after undo/redo.

    Ghost UIDs change when ghosts are regenerated, so any stored UIDs
    in hover/selection state become stale after undo. This handler
    clears all transient state to prevent referencing nonexistent ghosts.

    Also invalidates ghost caches and marks the pipeline dirty so stale
    ghosts don't persist when f-curve state changes during undo/redo.

    Args:
        scene: The scene that was affected by undo/redo.
    """
    if scene is None or not isinstance(scene, bpy.types.Scene):
        scene = bpy.context.scene
    if scene is None:
        return

    # Clear transient session state (hover, selection)
    SessionState.clear_all_instances()

    # Invalidate caches so stale ghosts don't persist after undo
    from .ghost_cache import GhostCache
    from .ghost_pipeline import GhostPipeline
    from .fcurve_utils import invalidate_keyframe_cache, clear_frame_cache

    cache = GhostCache.get(scene)
    cache.invalidate_all()

    pipeline = GhostPipeline.get(scene)
    pipeline.mark_dirty()

    # Clear sorted keyframe cache (keyframe edits may have been undone)
    invalidate_keyframe_cache()
    clear_frame_cache()

    # Undo can move any motion path and no depsgraph update says which: re-sample them all
    from .motion_paths import clear_cache
    clear_cache()
    from .ghost_pipeline import _schedule_deferred_update
    _schedule_deferred_update()
