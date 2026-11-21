"""Data identity shared by snapshots, editors and bounded editing gestures.

Window ownership belongs to callers. Names are labels, never object authority.
FCurves have no custom properties. A curve is identified by its channel:
original scene, object, action, slot, bone identity and channel. Editing
gestures additionally hold a temporary tag, so a curve replaced during the
gesture never receives its rollback. No tag outlives the gesture: any curve
modifier blocks Blender's Cycles modifier (Make Cyclic).
"""
from dataclasses import dataclass
from uuid import uuid4

import bpy

BONE_UID = '_ghost_binding_uid'
# Name of the bone that received BONE_UID. Duplicating a bone copies both;
# the copy's name differs, which identifies it as the copy.
BONE_OWNER = '_ghost_binding_owner'
# 4.2.0 review candidates stored a persistent muted Limits modifier per curve.
CURVE_TAG = 'Ghost Tool identity '
GESTURE_TAG = 'Ghost Tool gesture '
SCENE_ANCHOR = '_ghost_snapshot_anchor'


def scene_anchor(scene, *, create=False):
    anchor = scene.get(SCENE_ANCHOR)
    if create and (anchor is None or anchor.get(SCENE_ANCHOR) != scene):
        # Scene.copy remaps self-pointers inside the copied Scene. This small
        # external ID anchor retains its original owner, so a copied record
        # cannot silently acquire the copied Scene as its original identity.
        anchor = bpy.data.texts.new('.Ghost Tool scene identity')
        anchor[SCENE_ANCHOR] = scene
        scene[SCENE_ANCHOR] = anchor
    return anchor


def action_fcurves(action):
    """Every FCurve of an Action, layered (4.4+) or legacy."""
    layers = getattr(action, 'layers', None)
    if layers is not None and len(layers):
        for layer in layers:
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', ()):
                    yield from bag.fcurves
    else:
        yield from getattr(action, 'fcurves', ())


def _tags(curve, prefix):
    return [m for m in curve.modifiers if m.type == 'LIMITS' and m.name.startswith(prefix)]


def add_gesture_tag(curve):
    """Temporary replacement guard; removed by remove_gesture_tags."""
    tag = curve.modifiers.new('LIMITS')
    tag.mute = True
    tag.show_expanded = False
    tag.name = GESTURE_TAG + uuid4().hex
    return tag.name


def has_gesture_tag(curve, name):
    return any(m.name == name for m in curve.modifiers)


def remove_gesture_tags(action, names):
    """Remove the named gesture tags wherever they are in the Action."""
    names = set(names)
    if not names or action is None:
        return
    try:
        for curve in action_fcurves(action):
            for tag in [m for m in curve.modifiers if m.name in names]:
                curve.modifiers.remove(tag)
    except (ReferenceError, AttributeError, RuntimeError):
        pass


def remove_stale_tags(actions=None):
    """Drop legacy identity tags and gesture tags left by a crash or autosave."""
    removed = 0
    for action in (bpy.data.actions if actions is None else actions):
        for curve in action_fcurves(action):
            for tag in _tags(curve, CURVE_TAG) + _tags(curve, GESTURE_TAG):
                curve.modifiers.remove(tag)
                removed += 1
    return removed


def _original_bone(sharing, hint_name=''):
    """The original among bones sharing one BONE_UID (a duplicate copied it)."""
    for test in (lambda b: bool(hint_name) and b.name == hint_name,
                 lambda b: b.get(BONE_OWNER, '') == b.name,
                 # Blender names a duplicate "<original>.001".
                 lambda b: all(o == b or o.name.startswith(b.name + '.') for o in sharing)):
        found = [b for b in sharing if test(b)]
        if len(found) == 1:
            return found[0]
    return None


def find_bone(obj, bone_uid, hint_name=''):
    """Resolve a stored bone identity; None when missing or ambiguous."""
    sharing = [b for b in obj.data.bones if b.get(BONE_UID, '') == bone_uid]
    if len(sharing) == 1:
        return sharing[0]
    return _original_bone(sharing, hint_name) if sharing else None


def ensure_bone_uid(obj, bone, *, dry_run=False):
    """Bone identity for capture. A copied bone gets its own identity."""
    uid = bone.get(BONE_UID, '')
    if uid:
        sharing = [b for b in obj.data.bones if b.get(BONE_UID, '') == uid]
        if len(sharing) > 1 and _original_bone(sharing) != bone:
            uid = ''
    if dry_run:
        return uid
    if not uid:
        uid = uuid4().hex
        bone[BONE_UID] = uid
    bone[BONE_OWNER] = bone.name
    return uid


def object_reason(scene, obj, source_scene=None):
    try:
        if source_scene is not None and scene != source_scene:
            return 'Scene changed. Return to the original scene or bind deliberately.'
        if obj is None or scene.objects.get(obj.name) != obj:
            return 'Original object is unavailable. Bind explicitly to another target.'
    except ReferenceError:
        return 'Original object was removed. Bind explicitly to another target.'
    return ''


def resolve_editor_target(target, scene):
    reason = object_reason(scene, target.obj, target.scene)
    if reason:
        return None, reason + ' Refresh Target to choose again.'
    if not target.path_uid:
        return None, ''
    from . import motion_paths as mp
    for entry in scene.ghost_tool.motion_paths:
        if entry.get('_ghost_editor_uid', '') == target.path_uid:
            if entry.is_folder or mp.entry_key(entry) != target.path_key or mp.entry_is_missing(entry):
                return None, 'Target path changed or is unavailable. Refresh Target.'
            return entry, ''
    return None, 'Target path was removed. Refresh Target to choose another.'


def slot_handle(obj):
    slot = getattr(obj.animation_data, 'action_slot', None)
    return slot.handle if slot is not None else 0


@dataclass
class CurveBinding:
    scene: object
    obj: object
    action: object
    slot: int
    bone_uid: str
    channel: str
    curve_pointer: int
    path_uid: str = ''
    bone_name: str = ''
    curve_uid: str = ''
    scene_anchor: object = None
    gesture_tag: str = ''

    @classmethod
    def capture(cls, scene, obj, bone_name, channel, path_uid='', *, dry_run=False):
        reason = object_reason(scene, obj)
        if reason:
            raise ValueError(reason)
        from .fcurve_utils import resolve_fcurve
        curve = resolve_fcurve(obj, bone_name, channel)
        if curve is None:
            raise ValueError('No animation curve for this target. Show curve-backed markers first.')
        bone_uid = ''
        if bone_name:
            bone = obj.data.bones.get(bone_name) if obj.type == 'ARMATURE' else None
            if bone is None:
                raise ValueError('Original bone is unavailable.')
            bone_uid = ensure_bone_uid(obj, bone, dry_run=dry_run)
        if not dry_run:
            for tag in _tags(curve, CURVE_TAG):
                curve.modifiers.remove(tag)
        uid = uuid4().hex
        return cls(scene, obj, obj.animation_data.action, slot_handle(obj), bone_uid,
                   channel, curve.as_pointer(), path_uid, bone_name, uid,
                   scene_anchor(scene, create=not dry_run))

    def resolve(self, scene, *, allow_rehydrate=False):
        """Resolve the original channel.

        Within a session the captured curve must still be the channel's curve.
        A binding read from the blend file (no pointer) or ``allow_rehydrate``
        adopts the channel's current curve. A binding holding a ``gesture_tag``
        also requires that tag on the curve.
        """
        reason = object_reason(scene, self.obj, self.scene)
        if reason:
            return None, reason
        try:
            if self.scene_anchor is None or self.scene_anchor.get(SCENE_ANCHOR) != scene:
                return None, 'Original Scene identity changed or was copied. Bind explicitly.'
            anim = self.obj.animation_data
            if self.action is None or anim is None or anim.action != self.action:
                return None, 'Original action changed or was removed. Restore its assignment or bind explicitly.'
            if slot_handle(self.obj) != self.slot:
                return None, 'Action slot changed. Restore the original slot or bind explicitly.'
            for other in scene.objects:
                if other != self.obj and other.animation_data and other.animation_data.action == self.action and slot_handle(other) == self.slot:
                    return None, 'This action slot is shared by another object. Make its animation single-user and bind explicitly.'
            bone_name = ''
            if self.bone_uid:
                bone = find_bone(self.obj, self.bone_uid, self.bone_name)
                if bone is None:
                    return None, 'Original bone is missing or ambiguous. Bind explicitly.'
                bone_name = bone.name
            if self.path_uid:
                matches = [e for e in scene.ghost_tool.motion_paths
                           if e.get('_ghost_editor_uid', '') == self.path_uid]
                if len(matches) != 1 or matches[0].is_folder or matches[0].object_name != self.obj.name or matches[0].bone_name != bone_name:
                    return None, 'Original path changed or was removed. Bind explicitly.'
            from .fcurve_utils import resolve_fcurve
            curve = resolve_fcurve(self.obj, bone_name, self.channel)
            if curve is None:
                return None, 'Original curve is unavailable. Bind explicitly.'
            if self.gesture_tag:
                if curve.as_pointer() != self.curve_pointer or not has_gesture_tag(curve, self.gesture_tag):
                    return None, 'Original curve was replaced. Bind explicitly before restoring.'
            elif self.curve_pointer and not allow_rehydrate and curve.as_pointer() != self.curve_pointer:
                return None, 'Original curve was replaced. Bind explicitly before restoring.'
            # A binding read from the blend file (no pointer yet) adopts the
            # channel's current curve when it first resolves.
            self.curve_pointer = curve.as_pointer()
            self.bone_name = bone_name
            return curve, ''
        except (ReferenceError, AttributeError, TypeError, ValueError):
            return None, 'Original target is unavailable. Bind explicitly.'

    def summary(self):
        try:
            return self.obj.name + (' / ' + self.bone_name if self.bone_name else '')
        except (ReferenceError, AttributeError):
            return 'Unavailable target'


def selected_samples(context, mode='ACTIVE', *, assign=True):
    """Explicit capture scope; mesh-only/path-only views never invent samples.

    ``assign=False`` never writes data (panel draw), so a path without an
    identity yet is reported with an empty path uid.
    """
    from .ghost_data import GhostStore
    from . import settings_editor
    store = GhostStore.get(context.scene)
    ghosts = list(store)
    path_uid = ''
    obj = context.active_object
    if settings_editor.is_editor(context):
        target = settings_editor._targets[context.window.as_pointer()]
        _, reason = resolve_editor_target(target, context.scene)
        if reason:
            raise ValueError(reason)
        obj = target.obj
    if mode == 'SCENE':
        return ghosts, path_uid
    if mode == 'MARKERS':
        ghosts = store.get_selected()
        if not ghosts:
            raise ValueError('Select markers to capture their channels.')
        return ghosts, path_uid
    if mode == 'PATH':
        paths = context.scene.ghost_tool.motion_paths
        index = context.scene.ghost_tool.motion_paths_index
        entry = paths[index] if 0 <= index < len(paths) else None
        if entry is None or entry.is_folder or entry.vertex_index >= 0:
            raise ValueError('Select an object or bone path with curve-backed markers first.')
        path_uid = entry.get('_ghost_editor_uid', '')
        if not path_uid and assign:
            path_uid = uuid4().hex
            entry['_ghost_editor_uid'] = path_uid
        return [g for g in ghosts if g.object_name == entry.object_name and g.bone_name == entry.bone_name], path_uid
    reason = object_reason(context.scene, obj)
    if reason:
        raise ValueError('Select an animated object or pose bones, then show markers.')
    bones = None
    if obj.type == 'ARMATURE' and context.mode == 'POSE':
        bones = {b.name for b in (context.selected_pose_bones or [])}
        if not bones:
            raise ValueError('Select the pose bones to capture.')
    return [g for g in ghosts if g.object_name == obj.name and (bones is None or g.bone_name in bones)], path_uid


def capture_label(context, *, compact=False):
    mode = getattr(context.scene, 'ghost_snapshot_scope', 'ACTIVE')
    try:
        samples, _ = selected_samples(context, mode, assign=False)
        if compact and samples:
            objects = {g.object_name for g in samples}
            bones = {(g.object_name, g.bone_name) for g in samples if g.bone_name}
            label = next(iter(objects)) if len(objects) == 1 else f'{len(objects)} objects'
            if bones:
                label += f" / {len(bones)} {'bone' if len(bones) == 1 else 'bones'}"
            return 'Capture: ' + label
        names = sorted({g.object_name + (' / ' + g.bone_name if g.bone_name else '') for g in samples})
        return 'Capture: ' + (', '.join(names) if names else 'show markers for the chosen target first')
    except ValueError as exc:
        return str(exc)
