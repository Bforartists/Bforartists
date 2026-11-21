# --- RIGGING AND CONTROL SETUP ---
"""Temp locator and locator bake/match operators (Features 1-10).

Features:
  1. Create temp locator at selected target
  2. Create temp locator at average selection
  3. Create temp locator at cursor
  4. Parent temp locator to selected target
  5. Constrain selected target to temp locator
  6. Constrain temp locator to selected target
  7. Bake temp locator from target
  8. Bake target from temp locator
  9. Match target to temp locator
 10. Match temp locator to target
"""

from __future__ import annotations

import bpy
from mathutils import Vector

from ..core.logging import get_logger
from ..core import p7_session as p7s
from ..core.p7_properties import get_p7
from ..core.p7_proxy_math import locator_object_name, resolve_bake_range
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _ensure_session(context) -> p7s.P7Session | None:
    """Return the active session or begin a new one."""
    p7 = get_p7(context)
    if p7 is None:
        return None
    sid = p7.active_session_id
    session = p7s.get_session(sid) if sid else None
    if session is None:
        session = p7s.begin_session(context.scene.name)
        p7.active_session_id = session.session_id
    return session


def _get_temp_collection(context, session: p7s.P7Session):
    """Return (or create) the session's temporary collection."""
    coll_name = p7s.TEMP_COLLECTION_TEMPLATE.format(short_id=session.short_id)
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        coll = bpy.data.collections.new(coll_name)
        context.scene.collection.children.link(coll)
        p7s.tag_artifact(coll, session.session_id, "temp_collection")
        session.register_collection(coll_name)
        p7s.save_session_to_scene(session.session_id)
    return coll


def _create_locator_at(context, session, name, position, owner_name=""):
    """Create a tagged empty at *position* and return it."""
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    p7 = get_p7(context)
    if p7 is not None:
        empty.empty_display_size = p7.proxy_size
    empty.location = position

    coll = _get_temp_collection(context, session)
    coll.objects.link(empty)

    p7s.tag_artifact(empty, session.session_id, "locator",
                     owner_obj_name=owner_name)
    session.register_object(name, "locator")
    p7s.save_session_to_scene(session.session_id)
    return empty


def _get_bake_range(context, p7):
    """Resolve the bake frame range from current settings."""
    scene = context.scene
    obj = context.active_object
    action_start = action_end = None
    if obj is not None:
        ad = getattr(obj, "animation_data", None)
        action = getattr(ad, "action", None) if ad else None
        if action is not None:
            action_start, action_end = action.frame_range
    return resolve_bake_range(
        mode=p7.bake_range_mode,
        scene_start=scene.frame_start,
        scene_end=scene.frame_end,
        action_start=action_start,
        action_end=action_end,
        custom_start=p7.bake_range_start,
        custom_end=p7.bake_range_end,
        preview_start=getattr(scene, "frame_preview_start", None),
        preview_end=getattr(scene, "frame_preview_end", None),
    )


def _find_last_locator(session):
    """Return the most recently created locator bpy object, or None."""
    for name in reversed(session.created_objects):
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.get(p7s.TAG_ARTIFACT_ROLE) == "locator":
            return obj
    return None


# ---------------------------------------------------------------------------
# Feature 1 — Create temp locator at selected target
# ---------------------------------------------------------------------------

class AA_OT_p7_create_locator(bpy.types.Operator):
    """Create a temporary locator empty at the active object or bone's world-space position."""

    bl_idname = "animassist.p7_create_locator"
    bl_label = "Create Locator at Target"
    bl_description = (
        "Create a temporary locator at the active target's world position (a bone's head when a bone is active). Session-managed"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        obj = context.active_object
        bone = getattr(context, "active_pose_bone", None)
        if bone is not None and obj.type == "ARMATURE":
            pos = (obj.matrix_world @ bone.matrix).translation.copy()
            name = locator_object_name(bone.name, session.short_id)
            owner = obj.name
        else:
            pos = obj.matrix_world.translation.copy()
            name = locator_object_name(obj.name, session.short_id)
            owner = obj.name

        empty = _create_locator_at(context, session, name, pos, owner)
        self.report({"INFO"}, f"Created locator '{empty.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 2 — Create temp locator at average selection
# ---------------------------------------------------------------------------

class AA_OT_p7_create_locator_average(bpy.types.Operator):
    """Create a temporary locator at the averaged position of all selected objects."""

    bl_idname = "animassist.p7_create_locator_average"
    bl_label = "Locator at Average"
    bl_description = (
        "Create a temporary locator at the average world position of the selected objects"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    def execute(self, context):
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        positions = [obj.matrix_world.translation for obj in context.selected_objects]
        avg = sum(positions, Vector()) / len(positions)
        name = locator_object_name("Average", session.short_id)
        empty = _create_locator_at(context, session, name, avg)
        self.report({"INFO"}, f"Created average locator '{empty.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 3 — Create temp locator at cursor
# ---------------------------------------------------------------------------

class AA_OT_p7_create_locator_cursor(bpy.types.Operator):
    """Create a temporary locator at the 3D cursor position."""

    bl_idname = "animassist.p7_create_locator_cursor"
    bl_label = "Locator at Cursor"
    bl_description = (
        "Create a temporary locator at the current 3D cursor position. "
        "Useful for placing reference points at arbitrary locations."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        pos = context.scene.cursor.location.copy()
        name = locator_object_name("Cursor", session.short_id)
        empty = _create_locator_at(context, session, name, pos)
        self.report({"INFO"}, f"Created cursor locator '{empty.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 4 — Parent temp locator to selected target
# ---------------------------------------------------------------------------

class AA_OT_p7_parent_locator(bpy.types.Operator):
    """Parent the most recent locator to the selected target without altering its world transform."""

    bl_idname = "animassist.p7_parent_locator"
    bl_label = "Parent Locator to Target"
    bl_description = (
        "Parent the latest locator to the active object, keeping its transform so it follows without jumping"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            return False
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        target = context.active_object
        mw = locator.matrix_world.copy()
        locator.parent = target
        locator.matrix_world = mw
        self.report({"INFO"}, f"Parented '{locator.name}' to '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 5 — Constrain selected target to temp locator
# ---------------------------------------------------------------------------

class AA_OT_p7_constrain_target_to_locator(bpy.types.Operator):
    """Add a Copy Location constraint on the target pointing at the session locator."""

    bl_idname = "animassist.p7_constrain_target_to_locator"
    bl_label = "Constrain Target → Locator"
    bl_description = (
        "Constrain the active object or bone to follow the latest locator (Copy Location, session-managed)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            return False
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        obj = context.active_object
        con_name = p7s.make_constraint_name(session.session_id, "CopyLoc")
        bone = getattr(context, "active_pose_bone", None)
        if bone is not None:
            con = bone.constraints.new("COPY_LOCATION")
            con.name = con_name
            con.target = locator
            session.register_constraint(obj.name, bone.name, con_name)
        else:
            con = obj.constraints.new("COPY_LOCATION")
            con.name = con_name
            con.target = locator
            session.register_constraint(obj.name, "", con_name)

        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Constrained '{obj.name}' → '{locator.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 6 — Constrain temp locator to selected target
# ---------------------------------------------------------------------------

class AA_OT_p7_constrain_locator_to_target(bpy.types.Operator):
    """Add a Copy Location constraint on the locator pointing at the active target."""

    bl_idname = "animassist.p7_constrain_locator_to_target"
    bl_label = "Constrain Locator → Target"
    bl_description = (
        "Constrain the latest locator to follow the active object (Copy Location, session-managed)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            return False
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        target = context.active_object
        con_name = p7s.make_constraint_name(session.session_id, "LocFollow")
        con = locator.constraints.new("COPY_LOCATION")
        con.name = con_name
        con.target = target
        session.register_constraint(locator.name, "", con_name)

        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Constrained '{locator.name}' → '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 7 — Bake temp locator from target
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_locator_from_target(bpy.types.Operator):
    """Bake the active target's world position as keyframes on the session locator."""

    bl_idname = "animassist.p7_bake_locator_from_target"
    bl_label = "Bake Locator from Target"
    bl_description = (
        "Bake the active target's world position onto the latest locator across the bake range"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None or get_p7(context) is None:
            return False
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        source = context.active_object
        frame_start, frame_end = _get_bake_range(context, p7)
        scene = context.scene
        orig_frame = scene.frame_current

        if locator.animation_data is None:
            locator.animation_data_create()
        if locator.animation_data.action is None:
            locator.animation_data.action = bpy.data.actions.new(f"{locator.name}_Bake")

        for frame in range(frame_start, frame_end + 1, max(1, p7.bake_step)):
            scene.frame_set(frame)
            locator.location = source.matrix_world.translation
            locator.keyframe_insert(data_path="location", frame=frame)

        scene.frame_set(orig_frame)
        if locator.animation_data and locator.animation_data.action:
            for fc in get_fcurves(locator.animation_data.action, anim_data=locator.animation_data):
                fc.update()

        self.report({"INFO"}, f"Baked target→locator over [{frame_start}–{frame_end}]")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 8 — Bake target from temp locator
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_target_from_locator(bpy.types.Operator):
    """Bake the session locator's world position as keyframes on the active target."""

    bl_idname = "animassist.p7_bake_target_from_locator"
    bl_label = "Bake Target from Locator"
    bl_description = (
        "Bake the latest locator's world position back onto the active target across the bake range"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None or get_p7(context) is None:
            return False
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        target = context.active_object
        frame_start, frame_end = _get_bake_range(context, p7)
        scene = context.scene
        orig_frame = scene.frame_current

        if target.animation_data is None:
            target.animation_data_create()
        if target.animation_data.action is None:
            target.animation_data.action = bpy.data.actions.new(f"{target.name}_P7Bake")

        for frame in range(frame_start, frame_end + 1, max(1, p7.bake_step)):
            scene.frame_set(frame)
            target.location = locator.matrix_world.translation
            target.keyframe_insert(data_path="location", frame=frame)

        scene.frame_set(orig_frame)
        if target.animation_data and target.animation_data.action:
            for fc in get_fcurves(target.animation_data.action, anim_data=target.animation_data):
                fc.update()

        self.report({"INFO"}, f"Baked locator→target over [{frame_start}–{frame_end}]")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 9 — Match target to temp locator
# ---------------------------------------------------------------------------

class AA_OT_p7_match_target_to_locator(bpy.types.Operator):
    """Snap the active target's transform to match the session locator at the current frame."""

    bl_idname = "animassist.p7_match_target_to_locator"
    bl_label = "Match Target → Locator"
    bl_description = (
        "Move the active target to the latest locator's world position at the current frame (no key inserted)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None or get_p7(context) is None:
            return False
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        target = context.active_object
        target.location = locator.matrix_world.translation.copy()
        self.report({"INFO"}, f"Matched '{target.name}' → '{locator.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 10 — Match temp locator to target
# ---------------------------------------------------------------------------

class AA_OT_p7_match_locator_to_target(bpy.types.Operator):
    """Snap the session locator to match the active target's position at the current frame."""

    bl_idname = "animassist.p7_match_locator_to_target"
    bl_label = "Match Locator → Target"
    bl_description = (
        "Move the latest locator to the active target's world position at the current frame"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object is None or get_p7(context) is None:
            return False
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        locator = _find_last_locator(session)
        if locator is None:
            self.report({"WARNING"}, "No session locator found")
            return {"CANCELLED"}

        target = context.active_object
        locator.location = target.matrix_world.translation.copy()
        self.report({"INFO"}, f"Matched '{locator.name}' → '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p7_create_locator,
    AA_OT_p7_create_locator_average,
    AA_OT_p7_create_locator_cursor,
    AA_OT_p7_parent_locator,
    AA_OT_p7_constrain_target_to_locator,
    AA_OT_p7_constrain_locator_to_target,
    AA_OT_p7_bake_locator_from_target,
    AA_OT_p7_bake_target_from_locator,
    AA_OT_p7_match_target_to_locator,
    AA_OT_p7_match_locator_to_target,
)
