"""BoneCraft — animator control-usability layer (R3).

Operators that make a generated BoneCraft control rig pleasant to animate:
IK/FK switch with no-pop snapping, frame-range IK<->FK bake, pole follow,
IK pin, foot-roll keying, lock-free limb inheritance, global rig scale with
protected locks, and per-character control state for multi-rig scenes.

Design split: the geometry that guarantees "no pop" lives in the pure
``control_math`` kernel (unit tested headlessly). This module is the thin
``bpy`` realisation — read the live chain, compute targets, write them back,
then flip the IK/FK blend property.

Clean-room / BoneCraft-native: addresses only the engine's own bone names
(``forearm.ik-L``, ``IK_FK-arm-L`` …). No third-party rig source consulted.
Registers only inside the package, which loads only under the Bforartists
guard.
"""
import math

import bpy
from mathutils import Vector

from boneforge.i18n import T
from boneforge.advanced_rigging import control_math as cm

_PROPS_BONE = "properties"
_STATE_PROP = "bf_control_state"      # per-armature JSON state (multi-rig safe)


# -- rig discovery -----------------------------------------------------

def is_engine_rig(arm):
    """True for a BoneCraft engine rig (has a properties bone with blends)."""
    if arm is None or arm.type != 'ARMATURE':
        return False
    pb = arm.pose.bones.get(_PROPS_BONE)
    if pb is None:
        return False
    return any(k.startswith("IK_FK-") for k in pb.keys())


def discover_limbs(arm):
    """Return a list of name-maps (one per IK/FK limb) found on ``arm``."""
    pb = arm.pose.bones.get(_PROPS_BONE)
    if pb is None:
        return []
    limbs = []
    for key in pb.keys():
        parsed = cm.parse_limb_prop(key)
        if not parsed:
            continue
        kind, side, tag = parsed
        names = cm.limb_bone_names(kind, side, tag)
        # only surface limbs whose bones actually exist
        if arm.pose.bones.get(names["ik"]) and arm.pose.bones.get(names["fk"][0]):
            limbs.append(names)
    return limbs


def _pb(arm, name):
    return arm.pose.bones.get(name)


def _refresh(arm, context):
    """Force a full re-evaluation (drivers + IK solve) in background mode.

    A bare ``view_layer.update()`` does not always re-run driven constraint
    influences or the IK solver after a scripted transform/property change;
    tagging the armature first makes the next update recompute them.
    """
    arm.update_tag()
    context.view_layer.update()


def limb_is_ik(arm, names):
    pb = arm.pose.bones.get(_PROPS_BONE)
    return bool(pb and pb.get(names["prop"], 0.0) >= 0.5)


# -- snapping (the no-pop core) ----------------------------------------

def snap_fk_to_ik(arm, names, context=None):
    """Currently IK -> copy the IK-solved pose onto the FK chain."""
    ctx = context or bpy.context
    _refresh(arm, ctx)
    mch0, mch1 = names["mch"][0], names["mch"][1]
    src = [_pb(arm, mch0), _pb(arm, mch1), _pb(arm, names["ik"])]
    targets = [m.matrix.copy() for m in src if m is not None]
    fk = [_pb(arm, n) for n in names["fk"]]
    for pbone, mat in zip(fk, targets):
        pbone.matrix = mat
        _refresh(arm, ctx)             # parent resolved before the child


def _signed_angle(u, v, axis):
    """Angle from ``u`` to ``v`` measured about ``axis`` (radians)."""
    if u.length < 1e-9 or v.length < 1e-9:
        return 0.0
    a = u.angle(v, 0.0)
    if u.cross(v).dot(axis) < 0.0:
        a = -a
    return a


def _ik_constraint(arm, names):
    mch_last = _pb(arm, names["mch"][-1])
    if mch_last is None:
        return None
    for con in mch_last.constraints:
        if con.type == 'IK':
            return con
    return None


def compute_pole_angle(base_pb, wrist, pole_pos):
    """Pole angle that aligns the IK bend plane with the FK chain.

    Canonical (publicly documented) formula computed from the *FK* base bone
    so it is deterministic regardless of solver state: project the pole onto
    the plane normal to the base bone and measure the signed angle from the
    bone's local X axis. ``wrist`` and ``pole_pos`` are armature-space Vectors.
    """
    base_head = base_pb.head.copy()
    bone_dir = base_pb.tail - base_head
    pole_normal = (Vector(wrist) - base_head).cross(Vector(pole_pos) - base_head)
    projected = pole_normal.cross(bone_dir)
    if projected.length < 1e-9:
        return 0.0
    return _signed_angle(base_pb.x_axis, projected, bone_dir)


def snap_ik_to_fk(arm, names, pole_distance=0.4, context=None):
    """Currently FK -> place the IK control + pole to match the FK chain.

    Sets the IK control exactly on the FK end-effector (so the hand/foot never
    pops), the pole on the FK bend side, and the IK pole angle to align the
    solved bend with the FK chain. The upper/fore bend is then produced by the
    IK solver (verified interactively — a headless ``--background`` solve does
    not fold an IK chain that has a pole target).
    """
    ctx = context or bpy.context
    _refresh(arm, ctx)
    fk = [_pb(arm, n) for n in names["fk"]]
    shoulder = fk[0].head.copy()
    elbow_fk = fk[1].head.copy()
    wrist = fk[2].head.copy()

    # The IK solver starts from the chain's current pose; a chain that is
    # straight at rest has no bend to grow and never folds, whatever the
    # pole says. Start the IK middle bone from the FK bend (both share the
    # same rest, so the local transform carries over).
    mid = _pb(arm, names["mch"][1]) if len(names["mch"]) > 1 else None
    if mid is not None:
        mid.matrix_basis = fk[1].matrix_basis.copy()

    ik = _pb(arm, names["ik"])
    ik.matrix = fk[2].matrix.copy()         # exact end-effector match
    _refresh(arm, ctx)

    pole = _pb(arm, names["pole"])
    pos = Vector(cm.pole_position(tuple(shoulder), tuple(elbow_fk),
                                  tuple(wrist), pole_distance))
    if pole is not None:
        m = pole.matrix.copy()
        m.translation = pos
        pole.matrix = m
        _refresh(arm, ctx)

    con = _ik_constraint(arm, names)
    if con is not None:
        con.pole_angle = compute_pole_angle(fk[0], wrist, pos)
        _refresh(arm, ctx)
        _correct_pole_angle(arm, names, con, shoulder, elbow_fk, wrist, ctx)


def _elbow_error(arm, names, shoulder, elbow_fk, wrist):
    """Signed angle (about shoulder->wrist) from the solved IK elbow to the FK one."""
    mid = _pb(arm, names["mch"][1]) if len(names["mch"]) > 1 else None
    if mid is None:
        return 0.0
    axis = (wrist - shoulder)
    if axis.length < 1e-9:
        return 0.0
    axis.normalize()

    def perp(p):
        v = p - shoulder
        return v - axis * v.dot(axis)
    return _signed_angle(perp(mid.head), perp(elbow_fk), axis)


def _wrap(angle):
    """Pole angle is limited to [-pi, pi]; wrap instead of clamping."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def _correct_pole_angle(arm, names, con, shoulder, elbow_fk, wrist, ctx,
                        steps=6, tol=1e-4):
    """Turn the pole angle until the solved elbow lies on the FK elbow.

    The analytic angle depends on bone roll and solver conventions, so on
    real rigs the elbow could land a few cm off (the 'pop'). Measure the
    solved chain and correct; the sign of the pole angle's effect is found
    by trying it.
    """
    err = _elbow_error(arm, names, shoulder, elbow_fk, wrist)
    sign = 1.0
    for _ in range(steps):
        if abs(err) < tol:
            break
        before = con.pole_angle
        con.pole_angle = _wrap(before + sign * err)
        _refresh(arm, ctx)
        new = _elbow_error(arm, names, shoulder, elbow_fk, wrist)
        if abs(new) > abs(err):             # wrong direction: flip and retry
            sign = -sign
            con.pole_angle = _wrap(before + sign * err)
            _refresh(arm, ctx)
            new = _elbow_error(arm, names, shoulder, elbow_fk, wrist)
        err = new


def _set_blend(arm, names, to_ik, context=None):
    arm.pose.bones[_PROPS_BONE][names["prop"]] = 1.0 if to_ik else 0.0
    # A custom-property change does not, on its own, force the IK/FK blend
    # driver to re-evaluate in background; tag the armature so the next
    # depsgraph update recomputes the driven constraint influences.
    arm.update_tag()
    (context or bpy.context).view_layer.update()


def switch_limb(arm, names, to_ik, pole_distance=0.4, context=None):
    """Snap-then-switch one limb so the deformed pose does not pop."""
    ctx = context or bpy.context
    if to_ik:
        snap_ik_to_fk(arm, names, pole_distance, ctx)
    else:
        snap_fk_to_ik(arm, names, ctx)
    _set_blend(arm, names, to_ik, ctx)
    ctx.view_layer.update()


# -- bake --------------------------------------------------------------

def _key_targets(arm, names, to_ik, frame):
    if to_ik:
        for bone_name in (names["ik"], names["pole"]):
            pbone = _pb(arm, bone_name)
            if pbone is None:
                continue
            pbone.keyframe_insert("location", frame=frame)
            pbone.rotation_mode = 'QUATERNION'
            pbone.keyframe_insert("rotation_quaternion", frame=frame)
    else:
        for bone_name in names["fk"]:
            pbone = _pb(arm, bone_name)
            if pbone is None:
                continue
            pbone.rotation_mode = 'QUATERNION'
            pbone.keyframe_insert("rotation_quaternion", frame=frame)


def bake_limb(arm, names, to_ik, frame_start, frame_end,
              pole_distance=0.4, context=None):
    """Bake a limb to IK (``to_ik``) or to FK across a frame range.

    Reads the *source* chain each frame (its f-curves still drive it,
    independent of the blend property), writes and keys the *target*
    chain, leaving a clean per-frame action on the target controls.
    """
    ctx = context or bpy.context
    scene = ctx.scene
    _set_blend(arm, names, to_ik)
    props = arm.pose.bones[_PROPS_BONE]
    n_keys = 0
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        if to_ik:
            snap_ik_to_fk(arm, names, pole_distance, ctx)
        else:
            snap_fk_to_ik(arm, names, ctx)
        _key_targets(arm, names, to_ik, frame)
        props.keyframe_insert('["%s"]' % names["prop"], frame=frame)
        n_keys += 1
    return n_keys


# -- per-character state (multi-rig isolation) -------------------------

def _read_state(arm):
    import json
    raw = arm.get(_STATE_PROP)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _write_state(arm, state):
    import json
    arm[_STATE_PROP] = json.dumps(state)


def set_control_flag(arm, key, value):
    state = _read_state(arm)
    state[key] = value
    _write_state(arm, state)


def get_control_flag(arm, key, default=None):
    return _read_state(arm).get(key, default)


# -- tool helpers (thin, testable; operators delegate here) ------------

def toggle_pole_follow(arm, names, context=None):
    """Toggle the pole following the IK control, preserving world position."""
    ctx = context or bpy.context
    pole = _pb(arm, names["pole"])
    ik = _pb(arm, names["ik"])
    if pole is None or ik is None:
        return None
    con_name = "BF_POLE_FOLLOW"
    existing = pole.constraints.get(con_name)
    world = (arm.matrix_world @ pole.matrix).copy()
    if existing is not None:
        pole.constraints.remove(existing)
        following = False
    else:
        con = pole.constraints.new('CHILD_OF')
        con.name = con_name
        con.target = arm
        con.subtarget = names["ik"]
        following = True
    pole.matrix = arm.matrix_world.inverted() @ world
    ctx.view_layer.update()
    set_control_flag(arm, "pole_follow:%s" % names["prop"], following)
    return following


def toggle_ik_pin(arm, names):
    """Pin/unpin the IK control's location (no movement); returns pinned."""
    ik = _pb(arm, names["ik"])
    if ik is None:
        return None
    pinned = not bool(get_control_flag(arm, "pin:%s" % names["prop"], False))
    ik.lock_location = (pinned, pinned, pinned)
    set_control_flag(arm, "pin:%s" % names["prop"], pinned)
    return pinned


def toggle_limb_inherit(arm, names, context=None):
    """Toggle lock-free rotation inheritance on the FK root, preserving pose."""
    ctx = context or bpy.context
    pbone = _pb(arm, names["fk"][0])
    if pbone is None:
        return None
    ctx.view_layer.update()
    world = pbone.matrix.copy()
    pbone.bone.use_inherit_rotation = not pbone.bone.use_inherit_rotation
    ctx.view_layer.update()
    pbone.matrix = world
    ctx.view_layer.update()
    return pbone.bone.use_inherit_rotation


def key_foot_roll(arm, side, value, frame, context=None):
    """Set + key a side's foot-roll value. Returns False if not present."""
    ctx = context or bpy.context
    props = arm.pose.bones.get(_PROPS_BONE)
    key = "foot_roll-%s" % side
    if props is None or key not in props:
        return False
    props[key] = value
    props.keyframe_insert('["%s"]' % key, frame=frame)
    arm.update_tag()                      # engage the foot-roll driver
    ctx.view_layer.update()
    return True


def global_rig_scale(arm, factor, context=None):
    """Scale the rig from its root, refusing if the root scale is locked."""
    ctx = context or bpy.context
    root = _pb(arm, "root")
    if root is None:
        return None
    if all(root.lock_scale):
        return False                     # protected — do not override locks
    root.scale = [s * factor for s in root.scale]
    ctx.view_layer.update()
    return True


# -- operators ---------------------------------------------------------

class _RigPoll:
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and context.mode == 'POSE'
                and is_engine_rig(obj))


class BF_OT_ControlIKFKSwitch(_RigPoll, bpy.types.Operator):
    """Switch one limb between IK and FK, snapping so the pose does not pop"""
    bl_idname = "boneforge.control_ikfk_switch"
    bl_label = "IK/FK Switch"
    bl_options = {'REGISTER', 'UNDO'}

    prop_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    to_ik: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=True)

    def execute(self, context):
        arm = context.active_object
        parsed = cm.parse_limb_prop(self.prop_name)
        if not parsed:
            self.report({'ERROR'}, "Not an IK/FK limb: %s" % self.prop_name)
            return {'CANCELLED'}
        names = cm.limb_bone_names(*parsed)
        switch_limb(arm, names, self.to_ik, context=context)
        self.report({'INFO'}, "%s -> %s"
                    % (self.prop_name, "IK" if self.to_ik else "FK"))
        return {'FINISHED'}


class BF_OT_ControlIKFKBake(_RigPoll, bpy.types.Operator):
    """Bake one limb to IK or FK over the scene frame range"""
    bl_idname = "boneforge.control_ikfk_bake"
    bl_label = "Bake IK/FK"
    bl_options = {'REGISTER', 'UNDO'}

    prop_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    to_ik: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=True)

    def execute(self, context):
        arm = context.active_object
        parsed = cm.parse_limb_prop(self.prop_name)
        if not parsed:
            self.report({'ERROR'}, "Not an IK/FK limb: %s" % self.prop_name)
            return {'CANCELLED'}
        names = cm.limb_bone_names(*parsed)
        scene = context.scene
        n = bake_limb(arm, names, self.to_ik,
                      scene.frame_start, scene.frame_end, context=context)
        self.report({'INFO'}, "Baked %d frames" % n)
        return {'FINISHED'}


class BF_OT_ControlPoleFollow(_RigPoll, bpy.types.Operator):
    """Toggle the IK pole following the IK control (preserves pose)"""
    bl_idname = "boneforge.control_pole_follow"
    bl_label = "Pole Follow"
    bl_options = {'REGISTER', 'UNDO'}

    prop_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        arm = context.active_object
        parsed = cm.parse_limb_prop(self.prop_name)
        if not parsed:
            return {'CANCELLED'}
        following = toggle_pole_follow(arm, cm.limb_bone_names(*parsed), context)
        if following is None:
            return {'CANCELLED'}
        self.report({'INFO'}, "Pole follow %s"
                    % ("on" if following else "off"))
        return {'FINISHED'}


class BF_OT_ControlIKPin(_RigPoll, bpy.types.Operator):
    """Pin/unpin an IK control's transform (auto-snap, no movement)"""
    bl_idname = "boneforge.control_ik_pin"
    bl_label = "Pin IK Control"
    bl_options = {'REGISTER', 'UNDO'}

    prop_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        arm = context.active_object
        parsed = cm.parse_limb_prop(self.prop_name)
        if not parsed:
            return {'CANCELLED'}
        pinned = toggle_ik_pin(arm, cm.limb_bone_names(*parsed))
        if pinned is None:
            return {'CANCELLED'}
        self.report({'INFO'}, "IK control %s"
                    % ("pinned" if pinned else "released"))
        return {'FINISHED'}


class BF_OT_ControlFootRollKey(_RigPoll, bpy.types.Operator):
    """Set and key the foot-roll value for one side"""
    bl_idname = "boneforge.control_foot_roll_key"
    bl_label = "Key Foot Roll"
    bl_options = {'REGISTER', 'UNDO'}

    side: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, default="L")
    value: bpy.props.FloatProperty(description='Foot roll to key: -1 rolls onto the heel, 1 onto the toes', default=0.0, min=-1.0, max=1.0)

    def execute(self, context):
        arm = context.active_object
        ok = key_foot_roll(arm, self.side, self.value,
                           context.scene.frame_current, context)
        if not ok:
            self.report({'ERROR'}, "No foot roll on side %s" % self.side)
            return {'CANCELLED'}
        return {'FINISHED'}


class BF_OT_ControlLimbInherit(_RigPoll, bpy.types.Operator):
    """Toggle lock-free rotation inheritance on a limb's root FK bone"""
    bl_idname = "boneforge.control_limb_inherit"
    bl_label = "Lock-Free Limb"
    bl_options = {'REGISTER', 'UNDO'}

    prop_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        arm = context.active_object
        parsed = cm.parse_limb_prop(self.prop_name)
        if not parsed:
            return {'CANCELLED'}
        result = toggle_limb_inherit(arm, cm.limb_bone_names(*parsed), context)
        if result is None:
            return {'CANCELLED'}
        self.report({'INFO'}, "inherit_rotation = %s" % result)
        return {'FINISHED'}


class BF_OT_ControlGlobalScale(_RigPoll, bpy.types.Operator):
    """Scale the whole rig from its root, respecting protected (locked) bones"""
    bl_idname = "boneforge.control_global_scale"
    bl_label = "Global Rig Scale"
    bl_options = {'REGISTER', 'UNDO'}

    factor: bpy.props.FloatProperty(description='Scale the whole rig by this factor', default=1.0, min=0.01, max=100.0)

    def execute(self, context):
        arm = context.active_object
        result = global_rig_scale(arm, self.factor, context)
        if result is None:
            self.report({'ERROR'}, "No root control")
            return {'CANCELLED'}
        if result is False:
            self.report({'WARNING'}, "Root scale is locked (protected)")
            return {'CANCELLED'}
        self.report({'INFO'}, "Rig scaled x%.3f" % self.factor)
        return {'FINISHED'}


# -- panel -------------------------------------------------------------

class BONEFORGE_PT_control_layer(bpy.types.Panel):
    """Animator control layer for BoneCraft engine rigs"""
    bl_idname = "BONEFORGE_PT_control_layer"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_animate"
    bl_order = 42
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Control Layer"))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and is_engine_rig(obj)

    def draw(self, context):
        layout = self.layout
        arm = context.active_object
        limbs = discover_limbs(arm)
        if not limbs:
            layout.label(text=T("No IK/FK limbs found"), icon='INFO')
            return
        for names in limbs:
            is_ik = limb_is_ik(arm, names)
            box = layout.box()
            box.label(text=names["prop"].replace("IK_FK-", ""),
                      icon='CON_KINEMATIC')
            row = box.row(align=True)
            op = row.operator("boneforge.control_ikfk_switch", text="IK",
                              depress=is_ik)
            op.prop_name = names["prop"]; op.to_ik = True
            op = row.operator("boneforge.control_ikfk_switch", text="FK",
                              depress=not is_ik)
            op.prop_name = names["prop"]; op.to_ik = False
            row = box.row(align=True)
            op = row.operator("boneforge.control_ikfk_bake", text=T("Bake IK"))
            op.prop_name = names["prop"]; op.to_ik = True
            op = row.operator("boneforge.control_ikfk_bake", text=T("Bake FK"))
            op.prop_name = names["prop"]; op.to_ik = False
            row = box.row(align=True)
            op = row.operator("boneforge.control_pole_follow",
                              text=T("Pole Follow"))
            op.prop_name = names["prop"]
            op = row.operator("boneforge.control_ik_pin", text=T("Pin"))
            op.prop_name = names["prop"]
            op = row.operator("boneforge.control_limb_inherit",
                              text=T("Lock-Free"))
            op.prop_name = names["prop"]
        layout.separator(factor=0.5)
        layout.operator("boneforge.control_global_scale",
                        text=T("Global Rig Scale"), icon='FULLSCREEN_ENTER')


# -- registration ------------------------------------------------------

classes = (
    BF_OT_ControlIKFKSwitch,
    BF_OT_ControlIKFKBake,
    BF_OT_ControlPoleFollow,
    BF_OT_ControlIKPin,
    BF_OT_ControlFootRollKey,
    BF_OT_ControlLimbInherit,
    BF_OT_ControlGlobalScale,
    BONEFORGE_PT_control_layer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
