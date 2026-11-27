"""Humanoid naming profiles for isolated export copies.

These profiles change names, never hierarchy, rest pose, or bone orientation.
Recognition is exact (after removing separators), so controls/twists are not
silently mistaken for limbs. A user's saved humanoid mapping takes precedence.
"""

from contextlib import contextmanager
from copy import deepcopy
import json
import re
import uuid


NAMING_ITEMS = (
    ('NONE', 'Keep Original Names', 'Export the existing bone names'),
    ('UNITY', 'Unity-Preset', 'Rename recognized export bones to Unity Humanoid names; keep the working rig unchanged'),
    ('UNREAL', 'Unreal-Preset', 'Rename recognized export bones to Unreal humanoid names; does not rebuild a Manny or Quinn skeleton'),
)

_ITEM_CACHE = {}


def naming_items(_self, _context):
    """Keep translated strings alive for Blender's dynamic EnumProperty API."""
    from boneforge.i18n import T
    items = tuple((key, T(label), T(tip), 0, index)
                  for index, (key, label, tip) in enumerate(NAMING_ITEMS))
    return _ITEM_CACHE.setdefault(items, items)

_UNREAL = {
    'Hips': 'pelvis', 'Spine': 'spine_01', 'Chest': 'spine_02',
    'UpperChest': 'spine_03', 'Neck': 'neck_01', 'Head': 'head', 'Jaw': 'jaw',
}
_ALIASES = {
    'Hips': ('hips', 'hip', 'pelvis', 'J_Bip_C_Hips'),
    'Spine': ('spine', 'spine_01', 'J_Bip_C_Spine'),
    'Chest': ('chest', 'spine_02', 'Spine1', 'J_Bip_C_Chest'),
    'UpperChest': ('upperchest', 'spine_03', 'Spine2', 'J_Bip_C_UpperChest'),
    'Neck': ('neck', 'neck_01', 'J_Bip_C_Neck'),
    'Head': ('head', 'J_Bip_C_Head'), 'Jaw': ('jaw',),
}
for _side, _suffix in (('Left', 'l'), ('Right', 'r')):
    for _part, _ue, _blender, _mixamo in (
        ('Shoulder', 'clavicle', 'shoulder', 'Shoulder'),
        ('UpperArm', 'upperarm', 'upper_arm', 'Arm'),
        ('LowerArm', 'lowerarm', 'forearm', 'ForeArm'),
        ('Hand', 'hand', 'hand', 'Hand'),
        ('UpperLeg', 'thigh', 'thigh', 'UpLeg'),
        ('LowerLeg', 'calf', 'shin', 'Leg'),
        ('Foot', 'foot', 'foot', 'Foot'),
        ('Toes', 'ball', 'toe', 'ToeBase'),
        ('Eye', 'eye', 'eye', 'Eye'),
    ):
        _slot = _side + _part
        _UNREAL[_slot] = f'{_ue}_{_suffix}'
        _ALIASES[_slot] = (_slot, f'{_ue}_{_suffix}', f'{_blender}.{_suffix}',
                           f'{_side}{_mixamo}', f'J_Bip_{_suffix.upper()}_{_part}')
    for _finger, _uefinger, _bfinger in (
        ('Thumb', 'thumb', 'thumb'), ('Index', 'index', 'f_index'),
        ('Middle', 'middle', 'f_middle'), ('Ring', 'ring', 'f_ring'),
        ('Little', 'pinky', 'f_pinky'),
    ):
        for _index, _segment in enumerate(('Proximal', 'Intermediate', 'Distal'), 1):
            _slot = _side + _finger + _segment
            _UNREAL[_slot] = f'{_uefinger}_{_index:02d}_{_suffix}'
            _ALIASES[_slot] = (
                _slot, _UNREAL[_slot], f'{_bfinger}.{_index:02d}.{_suffix}',
                f'{_side}Hand{_finger}{_index}',
                f'{_side}Hand{"Pinky" if _finger == "Little" else _finger}{_index}',
                f'J_Bip_{_suffix.upper()}_{_finger}{_index}',
            )


def _key(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


def make_plan(armature, preset):
    """Return a validated old->new map; ambiguous recognition fails closed."""
    if preset == 'NONE':
        return {}, {}
    if preset not in {'UNITY', 'UNREAL'}:
        raise ValueError('Unknown bone naming preset: ' + preset)
    bones = armature.data.bones
    names = {b.name for b in bones}
    raw = armature.get('boneforge_vrchat_humanoid', '{}')
    try:
        stored = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        stored = {}
    if not isinstance(stored, dict):
        stored = {}
    slots = {}
    # Namespaced Mixamo and VRoid names, DEF bones and plain humanoids.
    for slot, aliases in _ALIASES.items():
        if isinstance(stored.get(slot), str) and stored[slot] in names:
            slots[slot] = stored[slot]
            continue
        keys = {_key(a) for a in aliases} | {_key(slot)}
        matches = []
        for bone in bones:
            name = bone.name.rsplit(':', 1)[-1]
            if name.startswith('DEF-'):
                name = name[4:]
            if _key(name) in keys:
                matches.append(bone)
        deform = [b for b in matches if b.use_deform]
        matches = deform or matches
        if len(matches) > 1:
            raise ValueError(f'Ambiguous {slot}: ' + ', '.join(b.name for b in matches)
                             + '. Set its Humanoid Mapper slot before exporting.')
        if matches:
            slots[slot] = matches[0].name
    if not slots:
        raise ValueError('No humanoid bones recognized. Set Humanoid Mapper slots or keep original names.')
    if len(set(slots.values())) != len(slots):
        raise ValueError('Humanoid slots share a bone. Correct the Humanoid Mapper before exporting.')
    mapping = {old: (slot if preset == 'UNITY' else _UNREAL[slot])
               for slot, old in slots.items()}
    if preset == 'UNREAL':
        roots = [b.name for b in bones if b.parent is None and _key(b.name) == 'root'
                 and b.name not in mapping]
        if len(roots) == 1:
            mapping[roots[0]] = 'root'
    final_names = [mapping.get(b.name, b.name) for b in bones]
    if any(new in names and old != new for old, new in mapping.items()):
        raise ValueError('A target bone name is already occupied. Resolve the target-name conflict first.')
    if len(final_names) != len(set(final_names)):
        raise ValueError('Bone naming preset would create duplicate names. Resolve the target-name conflict first.')
    return {a: b for a, b in mapping.items() if a != b}, slots


def _path(path, mapping):
    # Simultaneous replacement also supports swaps and escaped bone names.
    lookup = {json.dumps(a, ensure_ascii=False): json.dumps(b, ensure_ascii=False)
              for a, b in mapping.items()}
    return re.sub(r'(?<=bones\[)("(?:[^"\\]|\\.)*")(?=\])',
                  lambda m: lookup.get(m[0], m[0]), path)


def remap_sidecar(data, mapping, slots=None):
    """Rename known bone references while retaining the full source metadata."""
    data = deepcopy(data)
    for slot in data.get('humanoid_mapping', {}).get('slots', []):
        slot['bone_name'] = mapping.get(slot['bone_name'], slot['bone_name'])
    if slots:
        humanoid = data.setdefault('humanoid_mapping', {})
        by_slot = {s['slot_name']: s['bone_name'] for s in humanoid.get('slots', [])}
        by_slot.update({slot: mapping.get(old, old) for slot, old in slots.items()})
        humanoid['slots'] = [{'slot_name': slot, 'bone_name': bone}
                             for slot, bone in by_slot.items()]
    for chain in data.get('physbone_chains', []):
        chain['root_bone'] = mapping.get(chain['root_bone'], chain['root_bone'])
        chain['collider_bones'] = [mapping.get(b, b) for b in chain.get('collider_bones', [])]
    for collider in data.get('colliders', []):
        collider['parent_bone'] = mapping.get(collider['parent_bone'], collider['parent_bone'])
    return data


def _curves(action):
    for layer in getattr(action, 'layers', ()):
        for strip in layer.strips:
            for bag in getattr(strip, 'channelbags', ()):
                yield from bag.fcurves
    yield from getattr(action, 'fcurves', ())


def _remap_pointers(owner, replacements):
    for prop in owner.bl_rna.properties:
        if prop.type == 'POINTER' and not prop.is_readonly:
            value = getattr(owner, prop.identifier, None)
            try:
                replacement = replacements.get(value)
            except TypeError:
                continue
            if replacement is not None:
                setattr(owner, prop.identifier, replacement)


def deselect_objects(context):
    """Change object selection without an editor/mode-dependent operator."""
    for obj in context.view_layer.objects:
        if obj.select_get():
            obj.select_set(False)


@contextmanager
def object_export_context(context):
    """Flush edit data, export in Object Mode, then restore the caller's state.

    Object selection uses the data API so Properties-panel calls and cleanup
    never depend on object.select_all.poll(). The mode transition occurs before
    any temporary object or name changes, including before export validation.
    """
    import bpy
    layer = context.view_layer
    active = layer.objects.active
    selected = [obj for obj in layer.objects if obj.select_get()]
    mode = active.mode if active is not None else 'OBJECT'
    entered = False
    try:
        if mode != 'OBJECT':
            if not bpy.ops.object.mode_set.poll():
                raise ValueError('Cannot prepare export: select an editable object and switch to Object Mode')
            bpy.ops.object.mode_set(mode='OBJECT')
        entered = True
        yield
    finally:
        if entered:
            current = layer.objects.active
            if current is not None and current.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            deselect_objects(context)
            for obj in selected:
                if obj.name in layer.objects:
                    obj.select_set(True)
            layer.objects.active = active if active is not None and active.name in layer.objects else None
            if mode != 'OBJECT' and layer.objects.active is not None:
                bpy.ops.object.mode_set(mode=mode)


@contextmanager
def export_copies(context, objects, preset):
    """Select isolated, renamed copies for the exporter; always restore state.

    Yield original->export object lookup (identity for NONE). Local actions,
    NLA, shape keys, vertex groups, constraint targets, drivers and bone-parent
    attachments follow copied IDs. Original objects/data/actions are untouched.
    """
    import bpy
    objects = list(dict.fromkeys(objects))
    if preset == 'NONE':
        yield {o: o for o in objects}
        return
    if context.mode != 'OBJECT':
        raise ValueError('Switch to Object Mode before exporting with a bone naming preset.')
    if any(o.library for o in objects):
        raise ValueError('Make linked objects local before exporting with a bone naming preset.')
    plans = {o: make_plan(o, preset) for o in objects if o.type == 'ARMATURE'}
    if not plans:
        raise ValueError('Select an armature with the meshes to use a bone naming preset.')
    for obj in objects:
        if obj.type != 'MESH':
            continue
        rigs = {m.object for m in obj.modifiers if m.type == 'ARMATURE' and m.object}
        if obj.parent and obj.parent.type == 'ARMATURE':
            rigs.add(obj.parent)
        if rigs - plans.keys():
            raise ValueError('Select every armature that deforms the exported meshes.')
        maps = [plans[r][0] for r in rigs]
        combined = {}
        for mapping in maps:
            for old, new in mapping.items():
                if old in combined and combined[old] != new:
                    raise ValueError('The mesh uses armatures with incompatible bone naming maps.')
                combined[old] = new
        final = [combined.get(g.name, g.name) for g in obj.vertex_groups]
        if len(final) != len(set(final)):
            raise ValueError(f'{obj.name}: preset would create duplicate vertex groups.')
    selected = list(context.selected_objects)
    active = context.view_layer.objects.active
    copies, data_copies, actions, parked = {}, [], [], []
    replacements = {}
    try:
        for original in objects:
            dup = original.copy()
            copies[original] = dup
            context.scene.collection.objects.link(dup)
            if original.type in {'ARMATURE', 'MESH'}:
                dup.data = original.data.copy()
                dup.data.use_fake_user = False
                data_copies.append(dup.data)
                replacements[original.data] = dup.data
                if original.type == 'MESH' and original.data.shape_keys:
                    replacements[original.data.shape_keys] = dup.data.shape_keys
        replacements.update(copies)
        # Copy actions before ANY bone rename (Blender updates bound paths).
        action_cache = {}
        for original, dup in copies.items():
            mapping = plans.get(original, ({}, {}))[0]
            for owner in (dup, dup.data if dup.type in {'ARMATURE', 'MESH'} else None,
                          dup.data.shape_keys if dup.type == 'MESH' else None):
                anim = getattr(owner, 'animation_data', None)
                if anim is None:
                    continue
                bindings = [anim]
                for track in anim.nla_tracks:
                    bindings.extend(track.strips)
                for binding in bindings:
                    action = binding.action
                    if action is None:
                        continue
                    key = (action, tuple(sorted(mapping.items())))
                    if key not in action_cache:
                        copied = action.copy()
                        copied.use_fake_user = False
                        actions.append(copied)
                        action_cache[key] = copied
                        for fc in _curves(copied):
                            fc.data_path = _path(fc.data_path, mapping)
                    slot_id = getattr(getattr(binding, 'action_slot', None), 'identifier', None)
                    binding.action = action_cache[key]
                    if slot_id and hasattr(binding.action, 'slots'):
                        slot = next((s for s in binding.action.slots if s.identifier == slot_id), None)
                        if slot:
                            binding.action_slot = slot
                for fc in anim.drivers:
                    fc.data_path = _path(fc.data_path, mapping)
                    for variable in fc.driver.variables:
                        for target in variable.targets:
                            rig = target.id
                            target_map = plans.get(rig, ({}, {}))[0]
                            if rig in replacements:
                                target.id = replacements[rig]
                            target.data_path = _path(target.data_path, target_map)
                            target.bone_target = target_map.get(target.bone_target, target.bone_target)
            world = dup.matrix_world.copy()
            if dup.parent in copies:
                parent = dup.parent
                dup.parent = copies[parent]
                dup.matrix_world = world
            owners = [dup]
            if dup.type == 'ARMATURE':
                owners += list(dup.pose.bones)
            for owner in owners:
                for constraint in owner.constraints:
                    rig = getattr(constraint, 'target', None)
                    target_map = plans.get(rig, ({}, {}))[0]
                    pole_rig = getattr(constraint, 'pole_target', None)
                    if hasattr(constraint, 'subtarget'):
                        constraint.subtarget = target_map.get(constraint.subtarget, constraint.subtarget)
                    if hasattr(constraint, 'pole_subtarget'):
                        pole_map = plans.get(pole_rig, ({}, {}))[0]
                        constraint.pole_subtarget = pole_map.get(constraint.pole_subtarget, constraint.pole_subtarget)
                    for target in getattr(constraint, 'targets', ()):
                        target_map = plans.get(target.target, ({}, {}))[0]
                        target.subtarget = target_map.get(target.subtarget, target.subtarget)
                        _remap_pointers(target, replacements)
                    _remap_pointers(constraint, replacements)
            for mod in dup.modifiers:
                _remap_pointers(mod, replacements)
        for original, dup in copies.items():
            if dup.type == 'MESH':
                mapping = {}
                for mod in original.modifiers:
                    if mod.type == 'ARMATURE' and mod.object in plans:
                        mapping.update(plans[mod.object][0])
                if original.parent in plans:
                    mapping.update(plans[original.parent][0])
                groups = [(g, mapping[g.name]) for g in dup.vertex_groups if g.name in mapping]
                for group, _ in groups:
                    group.name = '__BF_' + uuid.uuid4().hex
                for group, name in groups:
                    group.name = name
            if original in plans:
                mapping, slots = plans[original]
                bones = [(dup.data.bones[old], new) for old, new in mapping.items()]
                for bone, _ in bones:
                    bone.name = '__BF_' + uuid.uuid4().hex
                for bone, name in bones:
                    bone.name = name
                mapped = {slot: mapping.get(old, old) for slot, old in slots.items()}
                dup['boneforge_vrchat_humanoid'] = json.dumps(mapped)
                dup.data['boneforge_humanoid_mapping'] = json.dumps(mapped)
        # Bone attachments are resolved after their parent skeleton is renamed.
        for original, dup in copies.items():
            if original.parent in plans:
                mapping = plans[original.parent][0]
                dup.parent_bone = mapping.get(original.parent_bone, original.parent_bone)
        for original, dup in copies.items():
            old_name = original.name
            parked.append((original, old_name))
            original.name = '__BF_ORIGINAL_' + uuid.uuid4().hex
            dup.name = old_name
        for obj in context.selected_objects:
            obj.select_set(False)
        for dup in copies.values():
            dup.hide_set(False)
            dup.hide_viewport = False
            dup.select_set(True)
        context.view_layer.objects.active = copies.get(active, next(iter(copies.values())))
        context.view_layer.update()
        yield copies
    finally:
        for dup in copies.values():
            bpy.data.objects.remove(dup, do_unlink=True)
        for original, name in parked:
            original.name = name
        for data in data_copies:
            if data.users == 0:
                collection = bpy.data.armatures if isinstance(data, bpy.types.Armature) else bpy.data.meshes
                collection.remove(data)
        for action in actions:
            if action.users == 0:
                bpy.data.actions.remove(action)
        for obj in context.selected_objects:
            obj.select_set(False)
        for obj in selected:
            obj.select_set(True)
        context.view_layer.objects.active = active
        context.view_layer.update()


def draw_naming(layout, settings, context):
    from boneforge.i18n import T
    from boneforge.core import active_armature
    layout.prop(settings, 'bone_naming', text=T('Bone Names'))
    if settings.bone_naming == 'NONE':
        return
    layout.label(text=T('Export copies only'))
    layout.label(text=T('Working rig unchanged'))
    arm = active_armature(context)
    if arm is None:
        layout.label(text=T('Select an armature to preview names'), icon='INFO')
        return
    try:
        mapping, slots = make_plan(arm, settings.bone_naming)
        layout.label(text=T('Recognized / renamed') + f': {len(slots)} / {len(mapping)}')
        for old, new in list(mapping.items())[:3]:
            layout.label(text=f'{old} → {new}')
        layout.label(text=T('Other bones keep their names'))
    except ValueError as exc:
        layout.label(text=str(exc), icon='ERROR')
