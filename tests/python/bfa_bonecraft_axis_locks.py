"""In-Bforartists test: the Auto-Rig wizard's axis-lock toolbar.

* midline markers (PELVIS) default to X off, paired markers to all axes on;
* a locked axis survives the surface snap — the snap must not drag it;
* an unplaced marker locks to the mesh's centreline, not to the world origin
  (a body modelled off X=0 would otherwise start the marker off-body);
* finger markers obey the lock too (they used to read the face-marker list and
  silently ignore it).
"""
import bpy
import bmesh
from mathutils import Vector

import boneforge
from boneforge.autorig import wizard
from boneforge.autorig.session import (
    _ensure_marker_slots,
    get_body_marker,
    get_finger_marker,
)

OFFSET_X = 0.35   # the body is deliberately not centred on world X=0


def _body():
    """Box torso + arm, shifted to OFFSET_X, wide enough to ray-cast against."""
    bm = bmesh.new()
    for centre, half in (((0, 0, 1.20), (0.17, 0.10, 0.27)),
                         ((0.47, 0, 1.45), (0.27, 0.05, 0.05)),
                         ((-0.47, 0, 1.45), (0.27, 0.05, 0.05))):
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res["verts"]:
            v.co.x = v.co.x * 2 * half[0] + centre[0] + OFFSET_X
            v.co.y = v.co.y * 2 * half[1] + centre[1]
            v.co.z = v.co.z * 2 * half[2] + centre[2]
    me = bpy.data.meshes.new("AxisLockBody")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("AxisLockBody", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def run():
    try:
        boneforge.register()
    except Exception:
        pass                                   # already registered by another test

    ob = _body()
    bpy.ops.boneforge.autorig_wizard_start()
    s = bpy.context.scene.boneforge_autorig_session
    s.mesh_object_name = ob.name
    _ensure_marker_slots(s)
    context = bpy.context

    # defaults: midline vs paired
    wizard._apply_default_axis_lock_for_marker(s, "PELVIS", 'BODY')
    assert (s.placement_axis_x, s.placement_axis_y, s.placement_axis_z) == \
        (False, True, True), "midline marker must default to X off"
    wizard._apply_default_axis_lock_for_marker(s, "WRIST_LEFT", 'BODY')
    assert (s.placement_axis_x, s.placement_axis_y, s.placement_axis_z) == \
        (True, True, True), "paired marker must default to all axes on"

    # a placed marker keeps its X through the snap
    marker = get_body_marker(s, "PELVIS")
    marker.position = (OFFSET_X, 0.0, 0.95)
    marker.confirmed = True
    s.placement_axis_x, s.placement_axis_y, s.placement_axis_z = False, True, True
    bpy.ops.boneforge.autorig_move_marker(
        marker_name="PELVIS", marker_type='BODY',
        position=(OFFSET_X + 0.30, 0.02, 1.10), respect_axis_lock=True,
    )
    placed_x = get_body_marker(s, "PELVIS").position[0]
    assert abs(placed_x - OFFSET_X) < 1e-4, \
        "surface snap moved a locked axis to %r" % (placed_x,)

    # an unplaced marker locks to the mesh centreline, not to world X=0
    marker.position = (0.0, 0.0, 0.0)
    marker.confirmed = False
    centre_x = wizard._get_mesh_bounds_center(s).x
    assert abs(centre_x - OFFSET_X) < 1e-4, "mesh bounds centre wrong"
    bpy.ops.boneforge.autorig_move_marker(
        marker_name="PELVIS", marker_type='BODY',
        position=(OFFSET_X + 0.30, 0.02, 1.10), respect_axis_lock=True,
    )
    unplaced_x = get_body_marker(s, "PELVIS").position[0]
    assert abs(unplaced_x - centre_x) < 1e-4, \
        "unplaced midline marker locked to %r, not the centreline %r" % (
            unplaced_x, centre_x)

    # finger markers obey the lock
    finger = get_finger_marker(s, "FINGER_INDEX_TIP_L")
    assert finger is not None, "finger marker slot missing"
    finger.position = (OFFSET_X + 0.60, 0.0, 1.45)
    s.placement_axis_x = s.placement_axis_y = s.placement_axis_z = False
    bpy.ops.boneforge.autorig_move_marker(
        marker_name="FINGER_INDEX_TIP_L", marker_type='FINGER',
        position=(9.0, 9.0, 9.0), snap=False, respect_axis_lock=True,
    )
    got = tuple(get_finger_marker(s, "FINGER_INDEX_TIP_L").position)
    assert abs(got[0] - (OFFSET_X + 0.60)) < 1e-4 and abs(got[1]) < 1e-4 \
        and abs(got[2] - 1.45) < 1e-4, \
        "finger marker ignored the axis lock: %r" % (got,)

    bpy.ops.boneforge.autorig_wizard_cancel()
    print("test_axis_lock PASS (defaults, snap-safe lock, centreline "
          "reference, finger lock)")


run()
