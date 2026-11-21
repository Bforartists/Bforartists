"""Place Rig Markers: the Auto-Rig Wizard's marker placement as a 3D Viewport tool (UI critique, 2026-10-10).

Gesture first: with the tool active, a click on the mesh places the next marker of the wizard's current
step (body, fingers or face), in the order the wizard lists them. The tool header says which marker is
next and holds the axis locks and the mirror switch. The wizard's own per-marker Place buttons still work.
"""
from types import SimpleNamespace

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

from boneforge.autorig import constants as C
from boneforge.autorig.session import get_body_marker, get_face_marker, get_finger_marker
from boneforge.i18n import T

_GET = {'BODY': get_body_marker, 'FACE': get_face_marker, 'FINGER': get_finger_marker}
_MIRROR = {'BODY': "body_symmetry_enabled", 'FACE': "face_symmetry_enabled", 'FINGER': "finger_symmetry"}


def marker_order(session):
    """(marker type, the step's marker names in the wizard's order); (None, ()) off a marker step."""
    step = session.wizard_step
    if step == C.STEP_BODY_MARKERS:
        optional = tuple(C.OPTIONAL_BODY_MARKERS)
        return 'BODY', tuple(n for n in C.BODY_MARKERS if n not in optional) + optional
    if step == C.STEP_FACE_MARKERS:
        return 'FACE', tuple(C.FACE_MARKERS)
    if step == C.STEP_FINGER_MARKERS:
        left = tuple(C.FINGER_MARKERS_BY_COUNT.get(int(session.finger_count), ()))
        right = () if session.finger_symmetry else tuple(n.replace("_L", "_R") for n in left)
        return 'FINGER', left + right
    return None, ()


def next_marker(session):
    """(marker type, the first marker of the step not yet confirmed, or None)."""
    mtype, names = marker_order(session)
    get = _GET.get(mtype)
    for name in names:
        marker = get(session, name) if get else None
        if marker is not None and not marker.confirmed:
            return mtype, name
    return mtype, None


def _label(name):
    return name.replace("_", " ").title()


def place_next_marker(context, position):
    """Place the next marker at ``position`` (world space) and confirm it, as the wizard's own Place does:
    surface snap, axis locks, symmetry. Returns the marker's name, or None when the step is done."""
    from boneforge.autorig import wizard
    session = context.scene.boneforge_autorig_session
    mtype, name = next_marker(session)
    if name is None:
        return None
    wizard._apply_default_axis_lock_for_marker(session, name, mtype)
    stub = SimpleNamespace(marker_name=name, marker_type=mtype)     # the wizard's helpers read only these
    pos = Vector(position)
    if mtype in ('BODY', 'FACE'):
        pos = wizard.BF_OT_WizardPlaceMarker._apply_axis_constraints(stub, context, pos)
    bpy.ops.boneforge.autorig_move_marker(marker_name=name, marker_type=mtype, position=tuple(pos))
    bpy.ops.boneforge.autorig_confirm_marker(marker_name=name, marker_type=mtype)
    if mtype in ('BODY', 'FACE'):
        pair = wizard.BF_OT_WizardPlaceMarker._get_mirror_info(stub, context)
    else:
        marker = get_finger_marker(session, name)
        pair = (name.replace("_L", "_R") if session.finger_symmetry and marker is not None
                and marker.symmetry_locked and name.endswith("_L") else None)
    if pair is not None:
        bpy.ops.boneforge.autorig_confirm_marker(marker_name=pair, marker_type=mtype)
    return name


def raycast_mesh(context, event, mesh_name):
    """World-space point where the click hits the wizard's mesh, or None."""
    region = context.region
    rv3d = getattr(context.space_data, "region_3d", None)
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x, event.mouse_region_y)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    hit, location, _normal, _index, obj, _matrix = context.scene.ray_cast(
        context.evaluated_depsgraph_get(), origin, direction)
    if not hit or obj is None or getattr(obj, "original", obj).name != mesh_name:
        return None                                      # only the wizard's own mesh, not one named like it
    return Vector(location)


class BF_OT_PlaceMarkerAtClick(bpy.types.Operator):
    """Place the Auto-Rig Wizard's next marker where you click on the mesh"""
    bl_idname = "boneforge.autorig_place_marker_click"
    bl_label = "Place Next Marker"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        session = getattr(context.scene, "boneforge_autorig_session", None)
        if session is None or not session.is_active:
            cls.poll_message_set("Start the Auto-Rig Wizard first (Rig Builder tab).")
            return False
        if marker_order(session)[0] is None:
            cls.poll_message_set("Go to a marker step of the Auto-Rig Wizard.")
            return False
        return True

    def invoke(self, context, event):
        session = context.scene.boneforge_autorig_session
        if next_marker(session)[1] is None:
            self.report({'INFO'}, "Every marker of this step is placed: press Next in the wizard.")
            return {'CANCELLED'}
        hit = raycast_mesh(context, event, session.mesh_object_name)
        if hit is None:
            return {'PASS_THROUGH'}                      # not on the mesh: the click is the viewport's
        name = place_next_marker(context, hit)
        if context.area is not None:
            context.area.tag_redraw()
        self.report({'INFO'}, f"Placed {_label(name)}")
        return {'FINISHED'}


class BF_WT_place_rig_markers(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "boneforge.place_rig_markers"
    bl_label = "Place Rig Markers"
    bl_description = "Click the mesh to place the Auto-Rig Wizard's next marker"
    bl_icon = "ops.paint.eyedropper_add"
    bl_keymap = (
        ("boneforge.autorig_place_marker_click", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
    )

    def draw_settings(context, layout, tool):
        session = getattr(context.scene, "boneforge_autorig_session", None)
        if session is None or not session.is_active:
            layout.label(text=T("Start the Auto-Rig Wizard in the Rig Builder tab"))
            return
        mtype, name = next_marker(session)
        if mtype is None:
            layout.label(text=T("Go to a marker step of the wizard"))
            return
        layout.label(text=(T("Next:") + " " + _label(name)) if name else T("Step done: press Next in the wizard"))
        row = layout.row(align=True)
        for axis in "xyz":
            row.prop(session, f"placement_axis_{axis}", text=axis.upper(), toggle=True)
        mirror = _MIRROR.get(mtype)
        if mirror and hasattr(session, mirror):
            layout.prop(session, mirror, text=T("Mirror"))


def register():
    from boneforge.core import toolbar
    old = getattr(bpy.types, "BONEFORGE_OT_autorig_place_marker_click", None)
    if old is not None:                                            # a reloaded copy's operator
        bpy.utils.unregister_class(old)
    bpy.utils.register_class(BF_OT_PlaceMarkerAtClick)
    # Append at top level: anchoring inside a native group puts the separator inside it too.
    toolbar.register(BF_WT_place_rig_markers, separator=True, group=False)


def unregister():
    from boneforge.core import toolbar
    toolbar.unregister(BF_WT_place_rig_markers)
    if BF_OT_PlaceMarkerAtClick.is_registered:
        bpy.utils.unregister_class(BF_OT_PlaceMarkerAtClick)
