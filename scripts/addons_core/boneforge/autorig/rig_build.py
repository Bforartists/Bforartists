"""BoneCraft — Control-Rig Construction Engine (Task 1, FOUNDATION).

Bforartists-exclusive. Turns a marker/preset description (:class:`RigSpec`)
into a production control rig: dual IK/FK limbs with pole targets and blend
drivers, an FK spine/neck/head, FK finger chains, and a driven foot-roll —
plus control widgets and bone-collection organisation.

Two layers, deliberately separated:

* ``compute_build_plan(spec)`` — **pure Python**, no ``bpy``. Produces a
  declarative :class:`~boneforge.autorig.components.BuildPlan`. This is what
  closes the production-rig gap (the old generator created a single IK
  constraint and no drivers) and it is unit-testable headlessly.
* ``apply_build_plan(plan, armature_obj)`` — realises the plan in Blender
  via ``core.rig_ops``. Imports ``bpy`` lazily.

Clean-room: rig topology, the IK/FK blend, and foot-roll are implemented
from first principles / public rigging references with BoneCraft-native
bone names. No third-party rig source or asset is used. Runs only under
the Bforartists guard.
"""
from dataclasses import dataclass, field

from .components import BuildPlan, CollectionDef
from .components import spine as _spine
from .components import limb as _limb
from .components import digit as _digit
from .components import foot as _foot
from .components import tail as _tail
from .components import spline as _spline_chain
from .components import face as _face
from .components import validate_plan

# Collections in UI order.
_COLLECTION_ORDER = ["Root", "Controls", "FK", "IK", "Fingers", "Tail",
                     "Spline", "Face", "Deform", "MCH"]


@dataclass
class RigSpec:
    """Declarative description of the rig to build (preset + options)."""
    name: str = "BoneCraft Rig"
    sides: tuple = ("L", "R")
    arms: bool = True
    legs: bool = True
    fingers: bool = True
    foot_roll: bool = True
    stretch: bool = True
    preset: str = "human"
    tail_segments: int = 0
    spline_chains: tuple = ()      # each: (name, count, attach_bone)
    face: bool = False             # add the facial rig (eyes/lids/brows/jaw/lips)
    muzzle: bool = False           # face muzzle (creatures)


def compute_build_plan(spec: RigSpec) -> BuildPlan:
    """Pure: build the full declarative plan for ``spec`` (no bpy)."""
    plan = BuildPlan()
    _spine.build_spine(plan)
    if spec.preset == "quadruped":
        # spine + four legs (front offset forward, back offset back) + tail
        for side in spec.sides:
            _limb.build_limb(plan, "leg", side, stretch=spec.stretch,
                             tag="front", y_offset=0.45)
            _limb.build_limb(plan, "leg", side, stretch=spec.stretch,
                             tag="back", y_offset=-0.35)
        if spec.tail_segments == 0:
            spec = RigSpec(**{**spec.__dict__, "tail_segments": 5})
    else:
        for side in spec.sides:
            if spec.arms:
                _limb.build_limb(plan, "arm", side, stretch=spec.stretch)
                if spec.fingers:
                    _digit.build_hand_digits(plan, side)
            if spec.legs:
                _limb.build_limb(plan, "leg", side, stretch=spec.stretch)
                if spec.foot_roll:
                    _foot.build_foot_roll(plan, side)
    # optional extras for any preset
    if spec.face:
        _face.build_face(plan, muzzle=spec.muzzle or spec.preset == "quadruped")
    if spec.tail_segments:
        _tail.build_tail(plan, spec.tail_segments)
    for sc in spec.spline_chains:
        name, count = sc[0], sc[1]
        attach = sc[2] if len(sc) > 2 else "chest"
        _spline_chain.build_spline_chain(plan, name, count, attach=attach)
    # register collections actually used, in canonical order
    used = {b.collection for b in plan.bones}
    for i, name in enumerate([c for c in _COLLECTION_ORDER if c in used]):
        plan.add_collection(name, ui_row=i)
    return plan


# ---------------------------------------------------------------- apply

def apply_build_plan(plan, armature_obj, context=None):
    """Realise ``plan`` on an existing armature object (Blender side)."""
    import bpy
    from boneforge.core import rig_ops
    if context is None:
        context = bpy.context
    arm = armature_obj.data

    # 1) edit bones
    prev_active = context.view_layer.objects.active
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        ebs = arm.edit_bones
        for bd in plan.bones:
            eb = ebs.get(bd.name) or ebs.new(bd.name)
            eb.head = bd.head
            eb.tail = bd.tail
            eb.roll = bd.roll
            eb.use_deform = bd.deform
        # parent pass (all bones exist now)
        for bd in plan.bones:
            eb = ebs.get(bd.name)
            if bd.parent:
                eb.parent = ebs.get(bd.parent)
                eb.use_connect = bd.use_connect
    finally:
        bpy.ops.object.mode_set(mode='POSE')

    pbones = armature_obj.pose.bones

    # 1b) per-bone pose settings (native IK stretch on solved chains).
    # Always written (0.0 is the rigid default) so a chain bone is never
    # left with a stale stretch value from a previous build.
    for bd in plan.bones:
        pb = pbones.get(bd.name)
        if pb is not None:
            pb.ik_stretch = bd.ik_stretch

    # 2) custom properties
    for pd in plan.props:
        pb = pbones.get(pd.bone)
        if pb is not None:
            rig_ops.ensure_custom_prop(pb, pd.name, pd.default,
                                       pd.soft_min, pd.soft_max, pd.description)

    # 3) constraints
    for cd in plan.constraints:
        pb = pbones.get(cd.bone)
        if pb is None:
            continue
        if cd.type == 'IK':
            rig_ops.add_ik(
                pb, target=armature_obj, subtarget=cd.subtarget,
                chain_count=cd.params.get("chain_count", 2),
                pole_target=armature_obj,
                pole_subtarget=cd.params.get("pole_subtarget"),
                pole_angle=cd.params.get("pole_angle", 0.0),
                name=cd.name,
            )
        else:
            tgt = armature_obj if cd.target_self else None
            rig_ops.add_constraint(pb, cd.type, cd.name, target=tgt,
                                   subtarget=cd.subtarget, **cd.params)

    # 4) drivers
    for dd in plan.drivers:
        full_path = 'pose.bones["%s"].%s' % (dd.bone, dd.data_path_suffix)
        variables = []
        for v in dd.variables:
            spec = dict(v)
            spec["id"] = armature_obj
            variables.append(spec)
        rig_ops.add_driver(armature_obj, full_path, dd.index,
                           dd.expression, variables)

    # 5) collections + 6) widgets
    for cd in plan.collections:
        rig_ops.ensure_collection(arm, cd.name)
    for bd in plan.bones:
        rig_ops.assign_to_collection(arm, bd.name, bd.collection)
    try:
        from boneforge.weights import widgets as _widgets
        for wa in plan.widgets:
            pb = pbones.get(wa.bone)
            if pb is None:
                continue
            wobj = _widgets.ensure_widget_object(wa.widget, context)
            if wobj is not None:
                rig_ops.assign_widget(pb, wobj, wa.scale)
    except Exception:
        import traceback
        traceback.print_exc()

    context.view_layer.objects.active = prev_active
    return plan


def build_control_rig(armature_obj, spec=None, context=None):
    """Compute and apply a control rig on ``armature_obj``.

    On a skeleton generated (and skinned) by the Auto-Rig wizard the rig is
    fitted to it and takes over its skin weights, so the controls drive the
    mesh; on any other armature the engine template is built as-is.
    """
    from . import rig_integrate
    if rig_integrate.is_wizard_skeleton(b.name for b in armature_obj.data.bones):
        plan = rig_integrate.integrate_control_rig(armature_obj, spec, context)
        # the wizard's "Twist Bones" option (was shown but never applied)
        import bpy
        ctx = context or bpy.context
        session = getattr(ctx.scene, "boneforge_autorig_session", None)
        if session is not None and getattr(session, "twist_bones", False):
            rig_integrate.add_twist_bones(armature_obj,
                                          max(1, int(session.twist_segments)), ctx)
        wants_face = session is None or getattr(session, "face_controls", True)
        if wants_face and "eye.L" in armature_obj.data.bones:
            from . import face_controls
            face_controls.add_face_controls(armature_obj, ctx)
        if session is None or getattr(session, "skirt_bones", True):
            from . import skirt_rig
            skirt_rig.add_skirt_bones(armature_obj, ctx)    # skips itself without a skirt
        skin = getattr(session, "skinning_settings", None) if session is not None else None
        if skin is not None and getattr(skin, "joint_correctives", False):
            from . import joint_correctives
            for ob in bpy.data.objects:
                if ob.type == 'MESH' and any(m.type == 'ARMATURE' and m.object == armature_obj
                                             for m in ob.modifiers):
                    # correctives replace Preserve Volume: dual-quaternion
                    # skinning on top of them bulged bent knees into a knot.
                    # Switch it off first, so the keys correct the deformation
                    # that will actually play.
                    for mod in ob.modifiers:
                        if mod.type == 'ARMATURE' and mod.object == armature_obj:
                            mod.use_deform_preserve_volume = False
                    joint_correctives.generate_all(ob, armature_obj, ctx)
        return plan
    spec = spec or RigSpec()
    plan = compute_build_plan(spec)
    apply_build_plan(plan, armature_obj, context)
    return plan


# ----------------------------------------------------------- operator

def _register_classes():
    import bpy
    from boneforge import bfa_guard

    class BONEFORGE_OT_build_control_rig(bpy.types.Operator):
        """Build a BoneCraft control rig on the active armature"""
        bl_idname = "boneforge.build_control_rig"
        bl_label = "Build Control Rig"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj is not None and obj.type == 'ARMATURE'

        def execute(self, context):
            # Hard gate: never runs outside Bforartists, even via script.
            bfa_guard.require_bforartists("rig_build")
            try:
                build_control_rig(context.active_object, RigSpec(), context)
            except Exception as exc:
                self.report({'ERROR'}, "Rig build failed: %s" % exc)
                return {'CANCELLED'}
            self.report({'INFO'}, "BoneCraft control rig built")
            return {'FINISHED'}

    class BONEFORGE_OT_generate_twist_bones(bpy.types.Operator):
        """Add forearm twist bones so a turned wrist does not pinch the forearm"""
        bl_idname = "boneforge.generate_twist_bones"
        bl_label = "Generate Twist Bones"
        bl_options = {'REGISTER', 'UNDO'}

        segments: bpy.props.IntProperty(description='Twist bones per limb segment', name="Segments", default=2, min=1, max=4)

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return (obj is not None and obj.type == 'ARMATURE'
                    and obj.data.bones.get("forearm.def-L") is not None)

        def execute(self, context):
            bfa_guard.require_bforartists("rig_build")
            from . import rig_integrate
            added = rig_integrate.add_twist_bones(context.active_object,
                                                  self.segments, context)
            self.report({'INFO'}, "Added %d twist bones" % len(added)
                        if added else "Twist bones already present")
            return {'FINISHED'}

    return (BONEFORGE_OT_build_control_rig, BONEFORGE_OT_generate_twist_bones)


_classes = ()


def register():
    import bpy
    global _classes
    _classes = _register_classes()
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
