"""BoneCraft — control-rig construction primitives.

Thin, idempotent wrappers over Blender's constraint and driver APIs used
by the control-rig construction engine (``autorig/rig_build.py``). Kept
deliberately small and side-effect-local so the engine's *planning* layer
stays pure-Python and testable; only these helpers touch ``bpy``.

Clean-room: these are first-principles wrappers over public Blender Python
APIs (``PoseBone.constraints``, ``Object.driver_add``). No third-party
rigging source is consulted or reproduced.
"""

import bpy


# -- constraints --------------------------------------------------------

def add_constraint(pose_bone, ctype, name, target=None, subtarget=None,
                   **params):
    """Add (or replace by name) a constraint on ``pose_bone``.

    Idempotent: an existing constraint with the same name is removed first
    so re-running the engine never stacks duplicates.
    """
    existing = pose_bone.constraints.get(name)
    if existing is not None:
        pose_bone.constraints.remove(existing)
    con = pose_bone.constraints.new(ctype)
    con.name = name
    # Self-acting constraints (LIMIT_ROTATION/LOCATION/SCALE, TRANSFORM in
    # some modes) expose no ``target``/``subtarget``; guard so this generic
    # helper stays safe for every constraint type the engine emits.
    if target is not None and hasattr(con, "target"):
        con.target = target
    if subtarget is not None and hasattr(con, "subtarget"):
        con.subtarget = subtarget
    for key, value in params.items():
        if hasattr(con, key):
            setattr(con, key, value)
    return con


def add_ik(pose_bone, target, subtarget, chain_count=2,
           pole_target=None, pole_subtarget=None, pole_angle=0.0,
           name="BF_IK"):
    """Standard IK constraint with optional pole target."""
    con = add_constraint(
        pose_bone, 'IK', name, target=target, subtarget=subtarget,
        chain_count=chain_count,
    )
    if pole_target is not None and pole_subtarget:
        con.pole_target = pole_target
        con.pole_subtarget = pole_subtarget
        con.pole_angle = pole_angle
    return con


def add_copy_rotation(pose_bone, target, subtarget, name, influence=1.0):
    return add_constraint(
        pose_bone, 'COPY_ROTATION', name, target=target,
        subtarget=subtarget, influence=influence,
    )


def add_copy_location(pose_bone, target, subtarget, name, influence=1.0):
    return add_constraint(
        pose_bone, 'COPY_LOCATION', name, target=target,
        subtarget=subtarget, influence=influence,
    )


def add_stretch_to(pose_bone, target, subtarget, name):
    return add_constraint(
        pose_bone, 'STRETCH_TO', name, target=target, subtarget=subtarget,
    )


def add_limit_rotation(pose_bone, name, **params):
    return add_constraint(pose_bone, 'LIMIT_ROTATION', name, **params)


def add_child_of(pose_bone, target, subtarget, name):
    return add_constraint(
        pose_bone, 'CHILD_OF', name, target=target, subtarget=subtarget,
    )


def add_damped_track(pose_bone, target, subtarget, name):
    return add_constraint(
        pose_bone, 'DAMPED_TRACK', name, target=target, subtarget=subtarget,
    )


# -- custom properties --------------------------------------------------

def ensure_custom_prop(pose_bone, name, default=0.0, soft_min=0.0,
                       soft_max=1.0, description=""):
    """Create a UI custom property on a pose bone if missing."""
    if name not in pose_bone:
        pose_bone[name] = default
    try:
        ui = pose_bone.id_properties_ui(name)
        ui.update(min=soft_min, max=soft_max, soft_min=soft_min,
                  soft_max=soft_max, description=description)
    except Exception:
        # Older API fallback: rna_ui dict
        rna = pose_bone.get("_RNA_UI")
        if rna is None:
            pose_bone["_RNA_UI"] = {}
            rna = pose_bone["_RNA_UI"]
        rna[name] = {"min": soft_min, "max": soft_max,
                     "soft_min": soft_min, "soft_max": soft_max,
                     "description": description}
    return pose_bone[name]


# -- drivers ------------------------------------------------------------

def add_driver(owner_object, data_path, index, expression, variables):
    """Add a scripted-expression driver.

    ``variables`` is a list of dicts:
        {"name": str, "id": Object, "bone_path": str}          # SINGLE_PROP
      or
        {"name": str, "id": Object, "bone": str,
         "transform_type": "ROT_X", "space": "LOCAL_SPACE"}     # TRANSFORMS (space: WORLD_SPACE, TRANSFORM_SPACE or LOCAL_SPACE)

    Idempotent at the f-curve level: re-adding the same data_path/index
    replaces the existing driver.
    """
    # remove existing driver on this path/index
    try:
        owner_object.driver_remove(data_path, index)
    except Exception:
        pass
    fcurve = owner_object.driver_add(data_path, index)
    drv = fcurve.driver
    drv.type = 'SCRIPTED'
    # clear any default vars
    for v in list(drv.variables):
        drv.variables.remove(v)
    for spec in variables:
        var = drv.variables.new()
        var.name = spec["name"]
        if "bone_path" in spec:
            var.type = 'SINGLE_PROP'
            tgt = var.targets[0]
            tgt.id = spec["id"]
            tgt.data_path = spec["bone_path"]
        else:
            var.type = 'TRANSFORMS'      # Blender 4.x / 5.x name (was TRANSFORM_CHANNELS)
            tgt = var.targets[0]
            tgt.id = spec["id"]
            tgt.bone_target = spec["bone"]
            tgt.transform_type = spec.get("transform_type", "ROT_X")
            tgt.transform_space = spec.get("space", "LOCAL_SPACE")
    drv.expression = expression
    return fcurve


# -- generated actions (BoneCraft Mechanisms) ----------------------------

def ensure_action(name, tag, key, data_path, index, keys, current=None):
    """Refill ``current`` in place, or create a one-curve layered action tagged ``tag`` / ``key``.

    ``current`` is the action already on this rig's constraint. It is reused only
    when it carries the same tag and key and nothing else uses it, so a duplicated
    rig never shares or overwrites another rig's action. ``keys`` is
    [(frame, value, interpolation, easing)]; easing "" keeps the default.
    Returns (action, slot). The slot targets objects, as Action constraints need.
    """
    act = current
    if (act is None or act.get("bc_mech_id") != tag or act.get("bc_key") != key
            or act.users > 1):
        act = bpy.data.actions.new(name)
        act["bc_mech_id"] = tag
        act["bc_key"] = key
    act.name = name
    slot = act.slots[0] if len(act.slots) else act.slots.new(id_type='OBJECT', name="BoneCraft")
    layer = act.layers[0] if len(act.layers) else act.layers.new("BoneCraft")
    strip = layer.strips[0] if len(layer.strips) else layer.strips.new(type='KEYFRAME')
    bag = strip.channelbag(slot, ensure=True)
    for fc in list(bag.fcurves):
        bag.fcurves.remove(fc)
    fc = bag.fcurves.new(data_path, index=index)
    for frame, value, interpolation, easing in keys:
        kp = fc.keyframe_points.insert(frame, value)
        kp.interpolation = interpolation
        if easing:
            kp.easing = easing
    fc.update()
    return act, slot


def assign_action(con, action, slot):
    """Point an Action constraint at ``action`` and its ``slot`` (layered actions need both)."""
    con.action = action
    con.action_slot = slot


def release_action(action):
    """Remove a BoneCraft-generated action once nothing uses it; return True if removed."""
    if action is None or action.get("bc_mech_id") is None or action.users > 0:
        return False
    bpy.data.actions.remove(action)
    return True


# -- bone collections / display ----------------------------------------

def ensure_collection(armature_data, name):
    """Return (creating if needed) a bone collection by name (Blender 4.x)."""
    colls = getattr(armature_data, "collections", None)
    if colls is None:
        return None
    coll = colls.get(name) if hasattr(colls, "get") else None
    if coll is None:
        coll = colls.new(name)
    return coll


def assign_to_collection(armature_data, bone_name, coll_name):
    coll = ensure_collection(armature_data, coll_name)
    bone = armature_data.bones.get(bone_name)
    if coll is not None and bone is not None:
        try:
            coll.assign(bone)
        except Exception:
            pass


def assign_widget(pose_bone, widget_object, scale=1.0):
    """Assign a custom display shape to a pose bone."""
    pose_bone.custom_shape = widget_object
    try:
        pose_bone.custom_shape_scale_xyz = (scale, scale, scale)
    except Exception:
        try:
            pose_bone.custom_shape_scale = scale
        except Exception:
            pass
