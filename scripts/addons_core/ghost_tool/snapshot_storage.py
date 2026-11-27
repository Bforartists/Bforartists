"""Scene-owned snapshot payloads and typed source bindings.

All runtime objects are derived from this RNA data. Exported JSON carries
descriptions only; it never gains binding authority by matching names.
"""
import json

import bpy
from bpy.app.handlers import persistent


class GhostSnapshotBinding(bpy.types.PropertyGroup):
    source_scene: bpy.props.PointerProperty(type=bpy.types.Scene)
    source_object: bpy.props.PointerProperty(type=bpy.types.Object)
    source_action: bpy.props.PointerProperty(type=bpy.types.Action)
    scene_anchor: bpy.props.PointerProperty(type=bpy.types.Text)
    slot: bpy.props.IntProperty()
    bone_uid: bpy.props.StringProperty()
    bone_name: bpy.props.StringProperty()
    channel: bpy.props.StringProperty()
    curve_uid: bpy.props.StringProperty()
    path_uid: bpy.props.StringProperty()


class GhostRetainedSnapshot(bpy.types.PropertyGroup):
    uid: bpy.props.StringProperty()
    schema_version: bpy.props.IntProperty(default=2)
    payload: bpy.props.StringProperty()
    bindings: bpy.props.CollectionProperty(type=GhostSnapshotBinding)


FIELDS = ('source_scene', 'source_object', 'source_action', 'scene_anchor', 'slot', 'bone_uid',
          'bone_name', 'channel', 'curve_uid', 'path_uid')


def signature(scene):
    return tuple((r.uid, r.payload, tuple((b.source_object.as_pointer() if b.source_object else 0,
        b.source_action.as_pointer() if b.source_action else 0, b.slot, b.curve_uid)
        for b in r.bindings)) for r in scene.ghost_snapshots)


def read(scene):
    from .snapshot import GhostSnapshot
    from .target_binding import CurveBinding
    snapshots = []
    for record in scene.ghost_snapshots:
        if record.schema_version not in (1, 2):
            raise ValueError('Unsupported saved snapshot schema; original records were preserved.')
        snap = GhostSnapshot.from_dict(json.loads(record.payload))
        if snap.uid != record.uid:
            raise ValueError('Saved snapshot identity mismatch; original records were preserved.')
        for stored in record.bindings:
            binding = CurveBinding(stored.source_scene, stored.source_object, stored.source_action,
                stored.slot, stored.bone_uid, stored.channel, 0, stored.path_uid,
                stored.bone_name, stored.curve_uid, stored.scene_anchor)
            curve, reason = binding.resolve(scene, allow_rehydrate=True)
            if not reason:
                binding.curve_pointer = curve.as_pointer()
            snap.bindings.append(binding)
        if snap.bindings:
            snap.unbound_reason = ''
        snapshots.append(snap)
    if len({s.uid for s in snapshots}) != len(snapshots):
        raise ValueError('Duplicate saved snapshot identities; original records were preserved.')
    return snapshots


def _raw(scene):
    return [(r.uid, r.schema_version, r.payload,
             [{field: getattr(b, field) for field in FIELDS} for b in r.bindings])
            for r in scene.ghost_snapshots]


def _write(scene, entries):
    scene.ghost_snapshots.clear()
    for uid, schema, payload, bindings in entries:
        record = scene.ghost_snapshots.add()
        record.uid, record.schema_version, record.payload = uid, schema, payload
        for values in bindings:
            binding = record.bindings.add()
            for field, value in values.items():
                setattr(binding, field, value)


def commit(scene, snapshots):
    """Validate all serialization before changing RNA; preserve old data on error."""
    from .snapshot import GhostSnapshot
    entries = []
    for snap in snapshots:
        payload = json.dumps(snap.to_dict(), ensure_ascii=False, allow_nan=False, sort_keys=True)
        GhostSnapshot.from_dict(json.loads(payload))
        bindings = []
        for b in snap.bindings:
            try:
                values = dict(source_scene=b.scene, source_object=b.obj, source_action=b.action,
                    scene_anchor=b.scene_anchor,
                    slot=b.slot, bone_uid=b.bone_uid, bone_name=b.bone_name,
                    channel=b.channel, curve_uid=b.curve_uid, path_uid=b.path_uid)
                # Invalidated RNA pointers cannot be assigned. Keep unresolved
                # metadata and null pointers rather than seeking namesakes.
                for field in ('source_scene', 'source_object', 'source_action'):
                    if values[field] is not None:
                        values[field].as_pointer()
            except ReferenceError:
                values = dict(source_scene=None, source_object=None, source_action=None, scene_anchor=None,
                    slot=b.slot, bone_uid=b.bone_uid, bone_name=b.bone_name,
                    channel=b.channel, curve_uid=b.curve_uid, path_uid=b.path_uid)
            bindings.append(values)
        entries.append((snap.uid, 2, payload, bindings))
    if len({e[0] for e in entries}) != len(entries):
        raise ValueError('Duplicate snapshot IDs')
    backup = _raw(scene)
    try:
        _write(scene, entries)
    except Exception:
        _write(scene, backup)
        raise


@persistent
def invalidate(*_args):
    from .snapshot import SnapshotStore
    SnapshotStore.clear_all_instances()


@persistent
def remove_stale_curve_tags(*_args):
    """Earlier candidates left a muted modifier on edited curves, which blocks
    Blender's Cycles modifier; gesture tags can survive a crash or autosave."""
    from .target_binding import remove_stale_tags
    try:
        remove_stale_tags()
    except (AttributeError, RuntimeError, ReferenceError):
        pass  # Restricted data during startup; the next file load retries.
    return None


CLASSES = (GhostSnapshotBinding, GhostRetainedSnapshot)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ghost_snapshots = bpy.props.CollectionProperty(type=GhostRetainedSnapshot)
    for handlers in (bpy.app.handlers.load_post, bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        if invalidate not in handlers:
            handlers.append(invalidate)
    if remove_stale_curve_tags not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(remove_stale_curve_tags)
    # bpy.data may be restricted while add-ons register; clean up right after.
    bpy.app.timers.register(remove_stale_curve_tags, first_interval=0.0)
    invalidate()


def unregister():
    for handlers in (bpy.app.handlers.load_post, bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        if invalidate in handlers:
            handlers.remove(invalidate)
    if remove_stale_curve_tags in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(remove_stale_curve_tags)
    if bpy.app.timers.is_registered(remove_stale_curve_tags):
        bpy.app.timers.unregister(remove_stale_curve_tags)
    invalidate()
    # Removing the RNA interface leaves the Scene's ID-property payload intact.
    if hasattr(bpy.types.Scene, 'ghost_snapshots'):
        del bpy.types.Scene.ghost_snapshots
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
