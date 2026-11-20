"""BoneCraft — export in T-pose.

VRoid/VRM characters are modelled in an A-pose (arms ~30-45 degrees down).
Unity's humanoid importer and VRChat expect a T-pose rest, so an A-pose
export shows up bent in the target app. This puts a *copy* of the rig and its
meshes into a T-pose (arms horizontal, legs straight down), bakes the meshes
and every shape key through that pose, makes it the new rest, and hands the
copies to the exporter. The scene the user works in is never changed.

Clean-room: plain bpy pose/mesh operations, bone names are BoneCraft's own
(``upperarm.def-L`` ...).
"""
import bpy
from mathutils import Matrix, Vector

# (segments straightened, target direction in armature space per side)
_ARM_SEGS = ("upperarm", "forearm", "hand")
_LEG_SEGS = ("thigh", "shin")
_KEEP_WORLD = ("foot",)          # keep its rest orientation after the leg moves


def _side_sign(side):
    """Character left is +X in Blender's front view (character faces -Y)."""
    return 1.0 if side == "L" else -1.0


def tpose_targets(arm):
    """``{bone name: target direction}`` for the limb deform bones present."""
    bones = arm.pose.bones
    out = {}
    for side in ("L", "R"):
        for seg in _ARM_SEGS:
            name = "%s.def-%s" % (seg, side)
            if name in bones:
                out[name] = Vector((_side_sign(side), 0.0, 0.0))
        for seg in _LEG_SEGS:
            name = "%s.def-%s" % (seg, side)
            if name in bones:
                out[name] = Vector((0.0, 0.0, -1.0))
    return out


def _aim(pb, direction):
    """Rotate a pose bone about its head so its Y axis points along ``direction``."""
    m = pb.matrix.copy()
    y = m.to_3x3().col[1].normalized()
    q = y.rotation_difference(direction.normalized())
    rot = q.to_matrix().to_4x4() @ m.to_3x3().to_4x4()
    pb.matrix = Matrix.Translation(m.translation) @ rot


def _strip_controls(arm):
    """Remove constraints and drivers so the copy holds exactly the pose we set."""
    for pb in arm.pose.bones:
        for con in list(pb.constraints):
            pb.constraints.remove(con)
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    if arm.animation_data:
        arm.animation_data_clear()


def pose_to_t(arm, context=None):
    """Pose ``arm`` (a stripped copy) into a T-pose. Returns bones moved."""
    ctx = context or bpy.context
    targets = tpose_targets(arm)
    keep = {}
    for side in ("L", "R"):
        for seg in _KEEP_WORLD:
            name = "%s.def-%s" % (seg, side)
            if name in arm.pose.bones:
                keep[name] = arm.pose.bones[name].matrix.to_3x3().copy()
    moved = []
    # parents before children: order by depth in the hierarchy
    order = sorted(targets, key=lambda n: len(arm.pose.bones[n].parent_recursive))
    for name in order:
        _aim(arm.pose.bones[name], targets[name])
        ctx.view_layer.update()
        moved.append(name)
    for name, rot in keep.items():
        pb = arm.pose.bones[name]
        pb.matrix = Matrix.Translation(pb.matrix.translation) @ rot.to_4x4()
        ctx.view_layer.update()
    return moved


def _eval_coords(ob, depsgraph):
    import numpy as np
    ev = ob.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get("co", co)
    finally:
        ev.to_mesh_clear()
    return co


def bake_mesh_pose(ob, context=None):
    """Write the armature-deformed shape into the mesh and every shape key.

    A mesh with shape keys cannot have its armature modifier applied, so
    each key is evaluated on its own (show-only) through the armature and
    written back. Other modifiers are switched off meanwhile so the vertex
    count matches.
    """
    ctx = context or bpy.context
    others = [(m, m.show_viewport) for m in ob.modifiers if m.type != 'ARMATURE']
    for m, _v in others:
        m.show_viewport = False
    keys = ob.data.shape_keys
    try:
        if keys is None or len(keys.key_blocks) == 0:
            ctx.view_layer.update()
            co = _eval_coords(ob, ctx.evaluated_depsgraph_get())
            ob.data.vertices.foreach_set("co", co)
        else:
            prev_only, prev_idx = ob.show_only_shape_key, ob.active_shape_key_index
            ob.show_only_shape_key = True
            baked = []
            for i in range(len(keys.key_blocks)):
                ob.active_shape_key_index = i
                ob.data.update_tag()
                ctx.view_layer.update()
                baked.append(_eval_coords(ob, ctx.evaluated_depsgraph_get()))
            for kb, co in zip(keys.key_blocks, baked):
                kb.data.foreach_set("co", co)
            ob.data.vertices.foreach_set("co", baked[0])
            ob.show_only_shape_key = prev_only
            ob.active_shape_key_index = prev_idx
        ob.data.update()
    finally:
        for m, v in others:
            m.show_viewport = v


def apply_pose_as_rest(arm, context=None):
    ctx = context or bpy.context
    prev_active = ctx.view_layer.objects.active
    prev_mode = arm.mode
    ctx.view_layer.objects.active = arm
    with ctx.temp_override(active_object=arm, object=arm):
        if arm.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.object.mode_set(mode='OBJECT' if prev_mode != 'POSE' else 'POSE')
    ctx.view_layer.objects.active = prev_active


def make_tpose_copies(arm, meshes, context=None):
    """Copy ``arm`` + ``meshes``, put the copies in a T-pose rest.

    Returns ``(arm_copy, mesh_copies, moved_bones)``. The copies take the
    originals' names (the originals are renamed with a suffix until
    :func:`remove_tpose_copies` restores them), so the export carries the
    same object names.
    """
    ctx = context or bpy.context
    coll = ctx.scene.collection
    arm2 = arm.copy()
    arm2.data = arm.data.copy()
    coll.objects.link(arm2)
    _strip_controls(arm2)
    ctx.view_layer.update()
    copies = []
    for ob in meshes:
        ob2 = ob.copy()
        ob2.data = ob.data.copy()
        if ob2.data.shape_keys and ob2.data.shape_keys.animation_data:
            ob2.data.shape_keys.animation_data_clear()    # corrective drivers
        if ob2.parent is arm:
            ob2.parent = arm2
        for m in ob2.modifiers:
            if m.type == 'ARMATURE' and m.object is arm:
                m.object = arm2
        coll.objects.link(ob2)
        copies.append(ob2)
    moved = pose_to_t(arm2, ctx)
    for ob2 in copies:
        bake_mesh_pose(ob2, ctx)
    apply_pose_as_rest(arm2, ctx)
    for orig, dup in [(arm, arm2)] + list(zip(meshes, copies)):
        name = orig.name
        orig.name = name + "__bf_tpose_src"
        dup.name = name
    return arm2, copies, moved


def remove_tpose_copies(arm, meshes, arm2, copies):
    for dup in copies + [arm2]:
        data = dup.data
        bpy.data.objects.remove(dup, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Armature):
                bpy.data.armatures.remove(data)
    for orig in [arm] + list(meshes):
        if orig.name.endswith("__bf_tpose_src"):
            orig.name = orig.name[:-len("__bf_tpose_src")]
