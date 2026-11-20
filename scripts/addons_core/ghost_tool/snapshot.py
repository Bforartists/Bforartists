"""
snapshot.py — Ghost snapshot storage, comparison, and restoration.

Snapshots freeze the current ghost configuration as a reference overlay.
Animators can compare their current motion timing against previous states,
or restore f-curves to a snapshot's values.

Snapshots are owned by scene RNA and survive undo and file save/load.
JSON references require explicit binding to establish restore authority.
"""

from __future__ import annotations

import time
import math
import copy
import uuid
from dataclasses import dataclass, field
from typing import Optional

import bpy
from mathutils import Vector

from .ghost_data import GhostStore, Ghost
from .utils import log, warn, debug, get_scene_id, tag_viewport_redraw


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_SNAPSHOTS: int = 10
"""Maximum new retained snapshots; existing over-limit data is never truncated."""


# ---------------------------------------------------------------------------
# GhostSnapshot Dataclass
# ---------------------------------------------------------------------------

@dataclass
class GhostSnapshot:
    """A frozen copy of a ghost configuration for reference comparison.

    Attributes:
        name: User-provided name for the snapshot.
        uid: Unique identifier.
        timestamp: Unix timestamp when the snapshot was taken.
        ghost_data: List of ghost dicts (serialized Ghost objects).
        object_names: Set of object names involved in this snapshot.
        bone_names: Set of bone names involved.
        is_visible: Whether this snapshot should be drawn as an overlay.
    """

    name: str
    uid: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: float = field(default_factory=time.time)
    ghost_data: list[dict] = field(default_factory=list)
    object_names: set[str] = field(default_factory=set)
    bone_names: set[str] = field(default_factory=set)
    is_visible: bool = True
    curve_data: list[dict] = field(default_factory=list)
    schema_version: int = 2
    scope_kind: str = 'LEGACY'
    scope: list[dict] = field(default_factory=list)
    parent_uid: str = ''
    origin: dict = field(default_factory=dict)
    bindings: list = field(default_factory=list, repr=False, compare=False)
    unbound_reason: str = 'Imported reference. Bind explicitly before restoring.'

    def to_dict(self) -> dict:
        """Serialize the snapshot for JSON export.

        Returns:
            dict: All snapshot fields as JSON-serializable types.
        """
        return {
            "schema_version": self.schema_version,
            "scope_kind": self.scope_kind,
            "scope": copy.deepcopy(self.scope),
            "parent_uid": self.parent_uid,
            "origin": copy.deepcopy(self.origin),
            "name": self.name,
            "uid": self.uid,
            "timestamp": self.timestamp,
            "ghost_data": self.ghost_data,
            "object_names": list(self.object_names),
            "bone_names": list(self.bone_names),
            "is_visible": self.is_visible,
            "curve_data": copy.deepcopy(self.curve_data),
        }

    @classmethod
    def from_dict(cls, data: dict) -> GhostSnapshot:
        """Deserialize a snapshot from a dictionary.

        Args:
            data: Dictionary with snapshot field values.

        Returns:
            GhostSnapshot: Reconstructed snapshot.
        """
        if not isinstance(data, dict):
            raise ValueError("Snapshot must be an object")
        for name in ('name', 'uid'):
            if name in data and (not isinstance(data[name], str) or not data[name]):
                raise ValueError(f"Invalid snapshot {name}")
        for name in ('ghost_data', 'curve_data', 'object_names', 'bone_names'):
            if name in data and not isinstance(data[name], list):
                raise ValueError(f"Snapshot {name} must be a list")
        for name in ('object_names', 'bone_names'):
            if any(not isinstance(value, str) for value in data.get(name, [])):
                raise ValueError(f"Invalid snapshot {name}")
        if not isinstance(data.get('timestamp', 0), (int, float)) or not math.isfinite(data.get('timestamp', 0)):
            raise ValueError("Invalid snapshot timestamp")
        if type(data.get('is_visible', True)) is not bool:
            raise ValueError("Invalid snapshot visibility")
        schema = data.get('schema_version', 1)
        if type(schema) is not int or schema not in (1, 2):
            raise ValueError('Unsupported snapshot schema')
        if not isinstance(data.get('scope', []), list) or any(not isinstance(e, dict) for e in data.get('scope', [])):
            raise ValueError('Invalid snapshot scope')
        if not isinstance(data.get('scope_kind', 'LEGACY'), str) or not isinstance(data.get('parent_uid', ''), str) or not isinstance(data.get('origin', {}), dict):
            raise ValueError('Invalid snapshot origin')
        origin = data.get('origin', {})
        if any(not isinstance(origin.get(key, ''), str) for key in ('uid', 'name')):
            raise ValueError('Invalid snapshot origin label')
        if not isinstance(origin.get('targets', []), list) or any(not isinstance(v, str) for v in origin.get('targets', [])):
            raise ValueError('Invalid snapshot origin targets')
        ghosts = [Ghost.from_dict(value).to_dict() for value in data.get('ghost_data', [])]
        for curve in data.get('curve_data', []):
            if not isinstance(curve, dict) or any(not isinstance(curve.get(k), str) for k in ('object_name', 'bone_name', 'channel')):
                raise ValueError("Invalid snapshot curve reference")
            from .fcurve_utils import validate_curve_snapshot
            validate_curve_snapshot(curve.get('keys'))
        return cls(
            schema_version=2,
            scope_kind=data.get('scope_kind', 'LEGACY'),
            scope=copy.deepcopy(data.get('scope', [])),
            parent_uid=data.get('parent_uid', ''),
            origin=copy.deepcopy(data.get('origin', {})),
            name=data.get("name", "Unnamed"),
            uid=data.get("uid", uuid.uuid4().hex[:8]),
            timestamp=data.get("timestamp", time.time()),
            ghost_data=ghosts,
            curve_data=copy.deepcopy(data.get("curve_data", [])),
            object_names=set(data.get("object_names", [])),
            bone_names=set(data.get("bone_names", [])),
            is_visible=data.get("is_visible", True),
        )


# ---------------------------------------------------------------------------
# SnapshotStore — Per-scene snapshot container
# ---------------------------------------------------------------------------

class SnapshotStore:
    """Scene-level container for ghost snapshots.

    Follows the same singleton-per-scene pattern as GhostStore.
    Enforces a maximum count via FIFO eviction.

    Usage:
        snap_store = SnapshotStore.get(context.scene)
        snap_store.take_snapshot("Before adjustment")
        snap_store.restore_snapshot(snapshot_uid)
    """

    _instances: dict[str, SnapshotStore] = {}

    def __init__(self) -> None:
        """Initialize an empty snapshot store."""
        self._snapshots: list[GhostSnapshot] = []
        self._index: dict[str, GhostSnapshot] = {}
        self._scene = None
        self._signature = None
        self.storage_error = ''
        self.last_error = '' 

    @classmethod
    def get(cls, scene: bpy.types.Scene) -> SnapshotStore:
        """Retrieve or create the SnapshotStore for the given scene.

        Args:
            scene: The Blender scene.

        Returns:
            SnapshotStore: The store for this scene.
        """
        key = get_scene_id(scene)
        if key not in cls._instances:
            cls._instances[key] = cls()
        store = cls._instances[key]
        store._scene = scene
        from . import snapshot_storage
        signature = snapshot_storage.signature(scene)
        if store._signature != signature:
            try:
                snapshots = snapshot_storage.read(scene)
                store._snapshots = snapshots
                store._index = {s.uid: s for s in snapshots}
                store.storage_error = ''
            except (ValueError, TypeError, KeyError) as exc:
                store._snapshots = []
                store._index = {}
                store.storage_error = str(exc)
            store._signature = signature
        return store

    @classmethod
    def clear_all_instances(cls) -> None:
        """Remove all SnapshotStore instances (used during addon unregistration)."""
        cls._instances.clear()

    def _persist(self):
        if self.storage_error:
            raise ValueError(self.storage_error)
        if self._scene is not None:
            from . import snapshot_storage
            snapshot_storage.commit(self._scene, self._snapshots)
            self._signature = snapshot_storage.signature(self._scene)

    @staticmethod
    def binding_reason(snapshot, scene):
        if not snapshot.bindings:
            return snapshot.unbound_reason or 'Bind explicitly before restoring.'
        for binding in snapshot.bindings:
            _, reason = binding.resolve(scene)
            if reason:
                return reason
        return ''

    def replace_snapshots(self, snapshots, *, allow_overflow=False):
        if len(snapshots) > MAX_SNAPSHOTS and not allow_overflow:
            raise ValueError('Ten snapshots are already retained. Delete unwanted references and retry.')
        if len({s.uid for s in snapshots}) != len(snapshots):
            raise ValueError('Duplicate snapshot IDs')
        old = self._snapshots, self._index
        self._snapshots = list(snapshots)
        self._index = {s.uid: s for s in snapshots}
        try:
            self._persist()
        except Exception:
            self._snapshots, self._index = old
            raise

    # --- Snapshot operations ---

    def take_snapshot(self, name: str, scene: bpy.types.Scene, *, context=None, scope="SCENE") -> tuple[GhostSnapshot, Optional[str]]:
        """Freeze the current ghost configuration as a snapshot.

        If the store is at capacity, the oldest snapshot is evicted.

        Args:
            name: Human-readable name for the snapshot.
            scene: The Blender scene to read ghosts from.

        Returns:
            tuple[GhostSnapshot, Optional[str]]: The newly created snapshot and the name of
                the evicted snapshot (if any), so callers can report it to the user via UI.
        """
        if self.storage_error:
            raise ValueError(self.storage_error)
        if len(self._snapshots) >= MAX_SNAPSHOTS:
            raise ValueError('Ten snapshots are already retained. Delete unwanted references and retry.')
        ghost_store = GhostStore.get(scene)

        # Serialize current ghost state
        from .target_binding import CurveBinding, selected_samples
        samples, path_uid = selected_samples(context, scope) if context is not None else (list(ghost_store), '')
        if context is not None and not samples:
            raise ValueError('Show curve-backed markers for the chosen target first; mesh silhouettes alone cannot be captured.')
        ghost_data = [ghost.to_dict() for ghost in samples]

        # Collect involved objects and bones
        object_names = set()
        bone_names = set()
        for ghost_entry in ghost_data:
            object_names.add(ghost_entry.get("object_name", ""))
            # Extract bone name if present (empty string means no bone constraint)
            bone_name = ghost_entry.get("bone_name", "")
            if bone_name:
                bone_names.add(bone_name)

        from . import fcurve_utils
        curves = []
        bindings = []
        seen = set()
        for ghost in samples:
            key = (ghost.object_name, ghost.bone_name, ghost.channel)
            if key in seen:
                continue
            seen.add(key)
            obj = scene.objects.get(ghost.object_name)
            curve = fcurve_utils.resolve_fcurve(obj, ghost.bone_name, ghost.channel)
            if curve is not None:
                bindings.append(CurveBinding.capture(scene, obj, ghost.bone_name, ghost.channel, path_uid, dry_run=True))
                curves.append(dict(object_name=ghost.object_name, bone_name=ghost.bone_name,
                                   channel=ghost.channel, keys=fcurve_utils.snapshot_fcurve(curve)))

        if context is not None and (not curves or len(curves) != len(seen)):
            raise ValueError('Every captured marker needs its original animation curve. Regenerate markers first.')
        bindings = [CurveBinding.capture(scene, b.obj, b.bone_name, b.channel, b.path_uid) for b in bindings]
        snapshot = GhostSnapshot(
            name=name,
            scope_kind=scope,
            bindings=bindings,
            unbound_reason='' if bindings else 'No original animation curves. Bind explicitly to restore.',
            scope=[dict(object_name=b.obj.name, action_name=b.action.name, slot=b.slot,
                        bone_name=b.bone_name, channel=b.channel, path_uid=b.path_uid) for b in bindings],
            ghost_data=ghost_data,
            curve_data=curves,
            object_names=object_names,
            bone_names=bone_names,
        )

        self.replace_snapshots(self._snapshots + [snapshot])
        return snapshot, None

    def restore_snapshot(self, snapshot_uid: str, scene: bpy.types.Scene) -> bool:
        """Restore f-curves to match a snapshot's ghost values.

        Writes each ghost's stored local_value back through the f-curve
        recalculation system.

        Args:
            snapshot_uid: UID of the snapshot to restore.
            scene: The Blender scene to modify.

        Returns:
            bool: True if restoration succeeded, False otherwise.
        """
        from . import fcurve_utils

        snapshot = self._index.get(snapshot_uid)
        if snapshot is None:
            warn(f"Snapshot '{snapshot_uid}' not found")
            return False

        self.last_error = ''
        if not snapshot.bindings:
            self.last_error = snapshot.unbound_reason or 'Original identity is unbound. Bind explicitly before restoring.'
            return False
        if snapshot.curve_data and len(snapshot.bindings) != len(snapshot.curve_data):
            self.last_error = 'Reference binding count does not match captured curves.'
            return False
        targets = []
        for binding in snapshot.bindings:
            curve, reason = binding.resolve(scene)
            if reason:
                self.last_error = reason
                return False
            targets.append((binding, curve, fcurve_utils.snapshot_fcurve(curve)))
        # Keep the rollback function before writes; an injected or real failure
        # in a later write must not prevent restoration of earlier curves.
        rollback = fcurve_utils.restore_fcurve
        try:
            if snapshot.curve_data:
                for (_binding, curve, _backup), entry in zip(targets, snapshot.curve_data):
                    if not fcurve_utils.restore_fcurve(curve, entry['keys']):
                        raise ValueError('Curve restore failed; original animation restored.')
            else:
                # Bindings follow the captured channel order (bind_snapshot).
                # Key by captured names: resolve() tracks later bone renames.
                keys = list(dict.fromkeys((sample.get('bone_name', ''), sample['channel'])
                                          for sample in snapshot.ghost_data))
                if len(keys) != len(targets):
                    raise ValueError('Reference binding count does not match captured channels.')
                lookup = {key: curve for key, (_b, curve, _backup) in zip(keys, targets)}
                restored = 0
                for sample in snapshot.ghost_data:
                    curve = lookup[(sample.get('bone_name', ''), sample['channel'])]
                    # Samples on keys, outside the key range or on non-Bezier
                    # segments cannot be reshaped; skip them as before.
                    if fcurve_utils.recalculate_handles(curve, sample['frame'], sample['local_value'],
                            mode=scene.ghost_tool.curve_mode.lower()):
                        restored += 1
                if not restored:
                    raise ValueError('Legacy sampled restore changed nothing; original animation restored.')
        except Exception as exc:
            failures = []
            for binding, curve, backup in targets:
                valid, reason = binding.resolve(scene)
                if reason or not rollback(valid, backup):
                    failures.append(binding.summary())
            self.last_error = str(exc) + (' Rollback unavailable: ' + ', '.join(failures) if failures else '')
            self._refresh(scene)
            return False
        self._refresh(scene)
        self._restore_snapshot_markers(snapshot, scene)
        if scene == bpy.context.scene:
            # Live updates may be off or frozen: recompute marker positions.
            from .api import refresh_ghosts
            refresh_ghosts()
        return True

    @staticmethod
    def _refresh(scene):
        from .ghost_pipeline import GhostPipeline
        from .fcurve_utils import invalidate_keyframe_cache, clear_frame_cache
        from .motion_paths import clear_cache
        GhostPipeline.get(scene).mark_dirty()
        invalidate_keyframe_cache()
        clear_frame_cache()
        clear_cache()
        tag_viewport_redraw(bpy.context)

    def take_variant(self, name, scene, parent_uid, *, context, scope):
        parent = self.get_by_uid(parent_uid)
        if parent is None or not parent.bindings:
            raise ValueError('Choose a bound original snapshot as the variant parent.')
        for binding in parent.bindings:
            _, reason = binding.resolve(scene)
            if reason:
                raise ValueError(reason)
        from .target_binding import selected_samples
        samples, path_uid = selected_samples(context, scope)
        actual = {(scene.objects.get(g.object_name), g.bone_name, g.channel) for g in samples}
        expected = {(b.obj, b.bone_name, b.channel) for b in parent.bindings}
        if not actual or actual != expected or any(b.path_uid != path_uid for b in parent.bindings):
            raise ValueError('Variant target must match the chosen parent scope. Select its original target and channels.')
        child, _ = self.take_snapshot(name or parent.name + ' variant', scene, context=context, scope=scope)
        child.parent_uid = parent.uid
        child.origin = dict(uid=parent.uid, name=parent.name, targets=sorted(parent.object_names),
                            timestamp=parent.timestamp)
        self._persist()
        return child

    def bind_snapshot(self, uid, scene, target_object):
        """Deliberate single-source remap; never infer authority from names."""
        original = self.get_by_uid(uid)
        if original is None or target_object is None:
            raise ValueError('Select an animated target to bind this reference.')
        if len(original.object_names) > 1:
            raise ValueError('This reference has multiple original objects. Bind each source through an explicit mapping; a single selected object is insufficient.')
        from .target_binding import CurveBinding
        staged = GhostSnapshot.from_dict(original.to_dict())
        entries = staged.curve_data or staged.ghost_data
        bindings, seen = [], set()
        for entry in entries:
            key = (entry.get('bone_name', ''), entry['channel'])
            if key not in seen:
                bindings.append(CurveBinding.capture(scene, target_object, *key, dry_run=True))
                seen.add(key)
        if not bindings:
            raise ValueError('Reference has no animation channels to bind.')
        for entry in staged.ghost_data + staged.curve_data:
            entry['object_name'] = target_object.name
        staged.object_names = {target_object.name}
        staged.bindings = [CurveBinding.capture(scene, b.obj, b.bone_name, b.channel) for b in bindings]
        staged.unbound_reason = ''
        staged.scope = [dict(object_name=b.obj.name, action_name=b.action.name, slot=b.slot,
                             bone_name=b.bone_name, channel=b.channel, path_uid='') for b in bindings]
        index = self._snapshots.index(original)
        updated = list(self._snapshots)
        updated[index] = staged
        self.replace_snapshots(updated, allow_overflow=True)
        return staged

    def toggle_visibility(self, snapshot_uid: str) -> bool:
        """Toggle the visibility of a snapshot overlay.

        Args:
            snapshot_uid: UID of the snapshot.

        Returns:
            bool: The new visibility state, or False if not found.
        """
        snapshot = self._index.get(snapshot_uid)
        if snapshot is None:
            return False
        snapshot.is_visible = not snapshot.is_visible
        try:
            self._persist()
        except Exception:
            snapshot.is_visible = not snapshot.is_visible
            raise
        return snapshot.is_visible

    def delete_snapshot(self, snapshot_uid: str) -> bool:
        """Delete a snapshot permanently.

        Args:
            snapshot_uid: UID of the snapshot to delete.

        Returns:
            bool: True if the snapshot was found and deleted.
        """
        snapshot = self._index.get(snapshot_uid)
        if snapshot is None:
            return False
        self.replace_snapshots([s for s in self._snapshots if s.uid != snapshot_uid], allow_overflow=True)
        return True

    def get_visible(self) -> list[GhostSnapshot]:
        """Return all snapshots that are currently set to visible.

        Returns:
            list[GhostSnapshot]: Visible snapshots.
        """
        return [s for s in self._snapshots if s.is_visible]

    def get_all(self) -> list[GhostSnapshot]:
        """Return all snapshots.

        Returns:
            list[GhostSnapshot]: All snapshots in the store.
        """
        return list(self._snapshots)

    def get_by_uid(self, uid: str) -> Optional[GhostSnapshot]:
        """Look up a snapshot by UID.

        Args:
            uid: The snapshot UID.

        Returns:
            GhostSnapshot or None.
        """
        return self._index.get(uid)

    def to_dict_list(self) -> list[dict]:
        """Serialize all snapshots for export.

        Returns:
            list[dict]: Serialized snapshots.
        """
        return [s.to_dict() for s in self._snapshots]

    def load_from_dict_list(self, data: list[dict]) -> None:
        """Load snapshots from serialized data (import).

        Args:
            data: List of snapshot dictionaries.
        """
        snapshots = [GhostSnapshot.from_dict(item) for item in data]
        if len({snapshot.uid for snapshot in snapshots}) != len(snapshots):
            raise ValueError("Duplicate snapshot IDs")
        self.replace_snapshots(snapshots)


    @staticmethod
    def _restore_snapshot_markers(snapshot, scene):
        """Restore the captured marker records for the snapshot's channels."""
        if not snapshot.ghost_data:
            return

        bindings = {}
        if snapshot.curve_data and len(snapshot.curve_data) == len(snapshot.bindings):
            for entry, binding in zip(snapshot.curve_data, snapshot.bindings):
                bindings[(entry['object_name'], entry['bone_name'], entry['channel'])] = binding
        else:
            keys = list(dict.fromkeys((ghost.get('object_name', ''), ghost.get('bone_name', ''), ghost['channel'])
                                      for ghost in snapshot.ghost_data))
            bindings = dict(zip(keys, snapshot.bindings))

        restored = []
        channels = set()
        for value in snapshot.ghost_data:
            data = copy.deepcopy(value)
            key = (data.get('object_name', ''), data.get('bone_name', ''), data['channel'])
            channels.add(key)
            binding = bindings.get(key)
            if binding is not None:
                try:
                    data['object_name'] = binding.obj.name
                    data['bone_name'] = binding.bone_name
                except (AttributeError, ReferenceError):
                    pass
            channels.add((data.get('object_name', ''), data.get('bone_name', ''), data['channel']))
            restored.append(Ghost.from_dict(data))

        store = GhostStore.get(scene)
        keep = [ghost for ghost in store
                if (ghost.object_name, ghost.bone_name, ghost.channel) not in channels]
        store.replace_all(keep + restored)



# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class SnapshotMutation:
    @classmethod
    def poll(cls, context):
        from .session_state import SessionState
        return SessionState.poll_available(cls)


class GHOST_OT_take_snapshot(SnapshotMutation, bpy.types.Operator):
    """Take a snapshot of the current ghost configuration."""

    bl_idname = "ghost_tool.take_snapshot"
    bl_label = "Take Snapshot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Save markers and complete curves for the chosen target in this blend file"

    snapshot_name: bpy.props.StringProperty(
        name="Name",
        description="Name for this snapshot",
        default="Snapshot",
    )  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Create a new snapshot.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'}.
        """
        store = SnapshotStore.get(context.scene)
        try:
            snapshot, evicted_name = store.take_snapshot(self.snapshot_name, context.scene,
                context=context, scope=context.scene.ghost_snapshot_scope)
        except ValueError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        self.report({'INFO'}, f"Snapshot '{snapshot.name}' taken ({len(snapshot.ghost_data)} ghosts)")
        if evicted_name:
            self.report({'WARNING'}, f"Snapshot limit reached; evicted oldest: '{evicted_name}'")
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_save_variant(SnapshotMutation, bpy.types.Operator):
    """Save the current matching motion as an independent alternate of this reference"""
    bl_idname = 'ghost_tool.save_variant'
    bl_label = 'Save Variant'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Capture current motion with the same target scope and retain the chosen reference as its origin'
    parent_uid: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    snapshot_name: bpy.props.StringProperty(name='Name', default='', description='Optional name; otherwise use the parent name')

    def execute(self, context):
        try:
            SnapshotStore.get(context.scene).take_variant(self.snapshot_name, context.scene, self.parent_uid,
                context=context, scope=context.scene.ghost_snapshot_scope)
        except ValueError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_bind_snapshot(SnapshotMutation, bpy.types.Operator):
    """Deliberately bind one reference's curves to the active animated target"""
    bl_idname = 'ghost_tool.bind_snapshot'
    bl_label = 'Bind to Active Target'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Use the active object and matching bone channels as the explicit restore target for this reference'
    snapshot_uid: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        try:
            SnapshotStore.get(context.scene).bind_snapshot(self.snapshot_uid, context.scene, context.active_object)
        except ValueError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_restore_snapshot(SnapshotMutation, bpy.types.Operator):
    """Restore f-curves to match a selected snapshot."""

    bl_idname = "ghost_tool.restore_snapshot"
    bl_label = "Restore Snapshot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Apply the snapshot's complete captured curves; legacy snapshots restore sampled values"

    snapshot_uid: bpy.props.StringProperty(
        name="Snapshot UID",
        description="UID of the snapshot to restore",
    )  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Restore the specified snapshot.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        store = SnapshotStore.get(context.scene)
        success = store.restore_snapshot(self.snapshot_uid, context.scene)
        if success:
            self.report({'INFO'}, "Snapshot restored")
            tag_viewport_redraw(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, getattr(store, "last_error", "Failed to restore snapshot"))
            return {'CANCELLED'}


class GHOST_OT_toggle_snapshot(SnapshotMutation, bpy.types.Operator):
    """Toggle the visibility of a snapshot overlay."""

    bl_idname = "ghost_tool.toggle_snapshot"
    bl_label = "Toggle Snapshot Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    snapshot_uid: bpy.props.StringProperty(
        name="Snapshot UID",
        description="Internal identifier of the snapshot whose visibility will change",
    )  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Toggle snapshot visibility.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'}.
        """
        store = SnapshotStore.get(context.scene)
        new_state = store.toggle_visibility(self.snapshot_uid)
        tag_viewport_redraw(context)
        return {'FINISHED'}


class GHOST_OT_delete_snapshot(SnapshotMutation, bpy.types.Operator):
    """Delete a retained snapshot; Undo restores it."""

    bl_idname = "ghost_tool.delete_snapshot"
    bl_label = "Delete Snapshot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Delete this snapshot. Use Undo to restore it"

    snapshot_uid: bpy.props.StringProperty(
        name="Snapshot UID",
        description="Internal identifier of the snapshot to delete",
    )  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Delete the specified snapshot.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        store = SnapshotStore.get(context.scene)
        success = store.delete_snapshot(self.snapshot_uid)
        if success:
            self.report({'INFO'}, "Snapshot deleted")
            tag_viewport_redraw(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Snapshot not found")
            return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GHOST_OT_take_snapshot,
    GHOST_OT_restore_snapshot,
    GHOST_OT_bind_snapshot,
    GHOST_OT_save_variant,
    GHOST_OT_toggle_snapshot,
    GHOST_OT_delete_snapshot,
)


def register() -> None:
    """Register snapshot classes."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ghost_snapshot_scope = bpy.props.EnumProperty(
        name='Capture Scope', description='Choose exactly which displayed marker targets to save',
        items=[('ACTIVE', 'Active Object / Selected Bones', 'Capture displayed markers on the active object or selected pose bones'),
               ('PATH', 'Selected Path', 'Capture displayed markers for the selected object or bone path'),
               ('MARKERS', 'Selected Marker Channels', 'Capture selected markers and their complete source curves'),
               ('SCENE', 'All Scene Markers', 'Explicitly capture every displayed marker target in this scene')],
        default='ACTIVE')


def unregister() -> None:
    """Unregister snapshot classes and clean up stores."""
    SnapshotStore.clear_all_instances()
    if hasattr(bpy.types.Scene, "ghost_snapshot_scope"):
        del bpy.types.Scene.ghost_snapshot_scope
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Take and restore snapshot
# >>> store = SnapshotStore.get(bpy.context.scene)
# >>> snap = store.take_snapshot("Test", bpy.context.scene)
# >>> assert snap.name == "Test"
# >>> assert len(snap.ghost_data) >= 0
#
# Test 2: FIFO eviction
# >>> for i in range(12):
# ...     store.take_snapshot(f"Snap {i}", bpy.context.scene)
# >>> assert len(store.get_all()) <= MAX_SNAPSHOTS
#
# Test 3: Visibility toggle
# >>> uid = store.get_all()[0].uid
# >>> store.toggle_visibility(uid)
# >>> assert store.get_by_uid(uid).is_visible == False
