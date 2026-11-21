# --- RIGGING AND CONTROL SETUP ---
"""Cleanup, validation, batch operations, and one-click workflow operators.

Features 24-25, 40-45:

* **Feature 24 — Cleanup Session**        — rollback active session
* **Feature 25 — Cleanup All Sessions**   — purge ALL P7 artifacts from file
* **Feature 40 — Batch Proxy Creation**   — create proxies for all selected objects
* **Feature 41 — Batch Cleanup Stale**    — detect and remove orphans (auto cleanup)
* **Feature 42 — Constraint Validation**  — check for orphaned artifacts & constraints
* **Feature 43 — Unsupported Setup Check**— validate target transforms & constraints
* **Feature 44 — Proxy Mirroring**        — create mirrored copy of selected proxy
* **Feature 45 — One-Click Workflows**    — bake + cleanup shortcuts

Also includes:
* **Remove Proxy**          — delete single selected proxy
* **Remove Constraints**    — strip session constraints without deleting proxies
* **One-Click Proxy Bake**  — create proxy → bake → cleanup
* **One-Click Cleanup**     — bake all → cleanup all
* **Quick Proxy**           — position proxy with defaults
* **Export Session**        — JSON session dump to clipboard
"""

from __future__ import annotations

import json

import bpy

from ..core.logging import get_logger
from ..core import p7_session as p7s
from ..core.p7_properties import get_p7
from ..core.p7_proxy_math import PROXY_CONFIGS, proxy_object_name, mirror_name

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_session(context) -> p7s.P7Session | None:
    """Ensure an active session exists, creating one if needed."""
    p7 = get_p7(context)
    if p7 is None:
        return None
    sid = p7.active_session_id
    session = p7s.get_session(sid) if sid else None
    if session is None:
        session = p7s.begin_session(context.scene.name)
        p7.active_session_id = session.session_id
    return session


def _get_temp_collection(context, session):
    """Get or create the temporary collection for this session."""
    coll_name = p7s.TEMP_COLLECTION_TEMPLATE.format(short_id=session.short_id)
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        coll = bpy.data.collections.new(coll_name)
        context.scene.collection.children.link(coll)
        p7s.tag_artifact(coll, session.session_id, "temp_collection")
        session.register_collection(coll_name)
        p7s.save_session_to_scene(session.session_id)
    return coll


# ---------------------------------------------------------------------------
# Feature 24 — Cleanup Session
# ---------------------------------------------------------------------------

class AA_OT_p7_cleanup_session(bpy.types.Operator):
    """Remove all temporary artifacts from the active session."""

    bl_idname = "animassist.p7_cleanup_session"
    bl_label = "Cleanup Session"
    bl_description = (
        "Roll back the active session: remove constraints first, "
        "then proxy objects, then empty collections"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        return bool(p7.active_session_id) and p7s.get_session(p7.active_session_id) is not None

    def execute(self, context):
        p7 = get_p7(context)
        sid = p7.active_session_id
        session = p7s.get_session(sid)
        if session is None:
            self.report({"WARNING"}, "No active session to clean up")
            return {"CANCELLED"}

        n_obj = len(session.created_objects)
        n_con = len(session.created_constraints)

        ok = p7s.rollback_session(sid)
        p7s.clear_scene_session(context.scene)
        p7.active_session_id = ""

        status = "clean" if ok else "with some errors"
        self.report({"INFO"},
                    f"Session {session.short_id} cleaned: "
                    f"{n_obj} object(s), {n_con} constraint(s) ({status})")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 25 — Cleanup All Sessions
# ---------------------------------------------------------------------------

class AA_OT_p7_cleanup_all(bpy.types.Operator):
    """Purge all rigging artifacts from the entire file."""

    bl_idname = "animassist.p7_cleanup_all"
    bl_label = "Cleanup All Sessions"
    bl_description = (
        "Scan the entire file for P7-tagged artifacts and remove "
        "all of them — constraints, objects, and collections"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        # Available if any P7-tagged objects exist.
        for obj in bpy.data.objects:
            if obj.get(p7s.TAG_TEMP):
                return True
        # Or if any session records exist.
        if p7s.get_all_sessions():
            return True
        return False

    def execute(self, context):
        removed = p7s.purge_session_artifacts(session_id=None)
        p7s.clear_all_sessions()

        p7 = get_p7(context)
        if p7 is not None:
            p7.active_session_id = ""

        if removed:
            self.report({"INFO"}, f"Purged {removed} P7 artifact(s)")
        else:
            self.report({"INFO"}, "No P7 artifacts found")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Remove Proxy (Keep as-is)
# ---------------------------------------------------------------------------

class AA_OT_p7_remove_proxy(bpy.types.Operator):
    """Delete the selected proxy and its constraints."""

    bl_idname = "animassist.p7_remove_proxy"
    bl_label = "Remove Proxy"
    bl_description = (
        "Delete the active proxy object and any session-managed "
        "constraints that reference it"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        proxy = context.active_object
        proxy_name = proxy.name
        sid = proxy.get(p7s.TAG_SESSION_ID, "")
        session = p7s.get_session(sid) if sid else None

        # Remove constraints referencing this proxy.
        removed_cons = 0
        removed_keys: set[tuple[str, str, str]] = set()
        for obj in bpy.data.objects:
            for con in list(obj.constraints):
                if getattr(con, "target", None) == proxy:
                    removed_keys.add((obj.name, "", con.name))
                    obj.constraints.remove(con)
                    removed_cons += 1
            if hasattr(obj, "pose") and obj.pose:
                for bone in obj.pose.bones:
                    for con in list(bone.constraints):
                        if getattr(con, "target", None) == proxy:
                            removed_keys.add((obj.name, bone.name, con.name))
                            bone.constraints.remove(con)
                            removed_cons += 1

        # Unlink and delete.
        for coll in list(proxy.users_collection):
            coll.objects.unlink(proxy)
        bpy.data.objects.remove(proxy, do_unlink=True)

        # Update session.
        if session is not None:
            if proxy_name in session.created_objects:
                session.created_objects.remove(proxy_name)
            # Remove matching constraint records.
            # Drop only the records for constraints removed above. The old
            # prefix match (CONSTRAINT_PREFIX + session id) matched EVERY
            # constraint of the session, orphaning the other proxies' records.
            session.created_constraints = [
                rec for rec in session.created_constraints
                if not (bpy.data.objects.get(rec.object_name) is None
                        or (rec.object_name, rec.bone_name, rec.constraint_name) in removed_keys)
            ]
            p7s.save_session_to_scene(session.session_id)

        self.report({"INFO"},
                    f"Removed proxy '{proxy_name}' and {removed_cons} constraint(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Remove Session Constraints (Keep as-is)
# ---------------------------------------------------------------------------

class AA_OT_p7_remove_constraints(bpy.types.Operator):
    """Strip all session-managed constraints without deleting proxy objects."""

    bl_idname = "animassist.p7_remove_constraints"
    bl_label = "Remove Session Constraints"
    bl_description = (
        "Remove every constraint registered under the active session "
        "but keep all proxy and locator objects in the scene"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_constraints)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        removed = 0

        for rec in list(session.created_constraints):
            obj = bpy.data.objects.get(rec.object_name)
            if obj is None:
                continue
            if rec.bone_name and hasattr(obj, "pose") and obj.pose:
                bone = obj.pose.bones.get(rec.bone_name)
                if bone:
                    con = bone.constraints.get(rec.constraint_name)
                    if con:
                        bone.constraints.remove(con)
                        removed += 1
            else:
                con = obj.constraints.get(rec.constraint_name)
                if con:
                    obj.constraints.remove(con)
                    removed += 1

        session.created_constraints.clear()
        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Removed {removed} constraint(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 40 — Batch Proxy Creation
# ---------------------------------------------------------------------------

class AA_OT_p7_batch_create_proxies(bpy.types.Operator):
    """Create proxies for all selected objects at once."""

    bl_idname = "animassist.p7_batch_create_proxies"
    bl_label = "Batch Create Proxies"
    bl_description = (
        "Create a proxy of the configured type for every selected "
        "object, all registered under the same session"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects) and get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        cfg = PROXY_CONFIGS.get(p7.proxy_type)
        if cfg is None:
            self.report({"ERROR"}, f"Unknown proxy type '{p7.proxy_type}'. Pick a type in the Create Proxy dropdown")
            return {"CANCELLED"}

        created = 0
        for obj in list(context.selected_objects):
            world_pos = obj.matrix_world.translation.copy()
            name = proxy_object_name(obj.name, p7.proxy_type, session.short_id)

            proxy = bpy.data.objects.new(name, None)
            proxy.empty_display_type = cfg.empty_display
            proxy.empty_display_size = p7.proxy_size
            proxy.location = world_pos

            proxy.color = (*p7.proxy_color, 1.0)
            coll = _get_temp_collection(context, session)
            coll.objects.link(proxy)

            p7s.tag_artifact(proxy, session.session_id,
                             f"proxy_{p7.proxy_type.lower()}", owner_obj_name=obj.name)
            session.register_object(name, f"proxy_{p7.proxy_type.lower()}")

            if p7.auto_constrain and cfg.constraint_type is not None:
                con_name = p7s.make_constraint_name(session.session_id, cfg.constraint_suffix)
                con = obj.constraints.new(cfg.constraint_type)
                con.name = con_name
                con.target = proxy
                session.register_constraint(obj.name, "", con_name)
                if cfg.keyed_influence:
                    con.influence = 0.0

            created += 1

        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Created {created} proxy/proxies")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 41 — Auto Cleanup (Batch Cleanup Stale)
# ---------------------------------------------------------------------------

class AA_OT_p7_auto_cleanup(bpy.types.Operator):
    """Detect and remove orphaned rigging artifacts."""

    bl_idname = "animassist.p7_auto_cleanup"
    bl_label = "Auto Cleanup"
    bl_description = (
        "Scan for rigging artifacts not tracked by any session "
        "and remove them automatically"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Find orphaned objects (tagged but no matching session).
        active_sids = set(p7s.get_all_sessions().keys())
        orphaned = 0

        for obj in list(bpy.data.objects):
            if not obj.get(p7s.TAG_TEMP):
                continue
            sid = obj.get(p7s.TAG_SESSION_ID, "")
            if sid not in active_sids:
                # Orphan — remove constraints first.
                for other in bpy.data.objects:
                    for con in list(other.constraints):
                        if getattr(con, "target", None) == obj:
                            other.constraints.remove(con)
                for coll in list(obj.users_collection):
                    coll.objects.unlink(obj)
                bpy.data.objects.remove(obj, do_unlink=True)
                orphaned += 1

        # Remove orphaned constraints by prefix.
        for obj in bpy.data.objects:
            for con in list(obj.constraints):
                if con.name.startswith(p7s.CONSTRAINT_PREFIX):
                    # Check if the session prefix matches any active session.
                    prefix_sid = con.name[len(p7s.CONSTRAINT_PREFIX):len(p7s.CONSTRAINT_PREFIX) + 8]
                    matched = any(s.short_id == prefix_sid for s in p7s.get_all_sessions().values())
                    if not matched:
                        obj.constraints.remove(con)
                        orphaned += 1

        if orphaned:
            self.report({"INFO"}, f"Auto-cleaned {orphaned} orphaned artifact(s)")
        else:
            self.report({"INFO"}, "No orphaned artifacts found")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 42 — Constraint Validation Report
# ---------------------------------------------------------------------------

class AA_OT_p7_validate_session(bpy.types.Operator):
    """Check for orphaned artifacts, missing targets, and unsupported constraints."""

    bl_idname = "animassist.p7_validate_session"
    bl_label = "Validate Session"
    bl_description = (
        "Scan the session's artifact registry against the scene and "
        "report any orphaned, missing, or conflicting items"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        return bool(p7.active_session_id) and p7s.get_session(p7.active_session_id) is not None

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)

        issues = []

        # Check objects.
        for name in session.created_objects:
            if bpy.data.objects.get(name) is None:
                issues.append(f"Missing object: '{name}'")

        # Check constraints.
        for rec in session.created_constraints:
            obj = bpy.data.objects.get(rec.object_name)
            if obj is None:
                issues.append(f"Missing constraint owner: '{rec.object_name}'")
                continue
            if rec.bone_name:
                if not (hasattr(obj, "pose") and obj.pose):
                    issues.append(f"Non-armature object has bone constraint: '{rec.object_name}'")
                    continue
                bone = obj.pose.bones.get(rec.bone_name)
                if bone is None:
                    issues.append(f"Missing bone: '{rec.bone_name}' on '{rec.object_name}'")
                    continue
                if bone.constraints.get(rec.constraint_name) is None:
                    issues.append(f"Missing constraint: '{rec.constraint_name}' on bone '{rec.bone_name}'")
            else:
                if obj.constraints.get(rec.constraint_name) is None:
                    issues.append(f"Missing constraint: '{rec.constraint_name}' on '{rec.object_name}'")

        # Check collections.
        for name in session.created_collections:
            if bpy.data.collections.get(name) is None:
                issues.append(f"Missing collection: '{name}'")

        # Check for unsupported constraint configurations on constrained objects.
        constrained_objects = {rec.object_name for rec in session.created_constraints}
        for obj_name in constrained_objects:
            obj = bpy.data.objects.get(obj_name)
            if obj is None:
                continue
            # Check for conflicting constraints that might interfere with proxy operation.
            conflict_types = ("CHILD_OF", "ARMATURE", "OBJECT_SOLVER", "POLE_TARGET")
            for con in obj.constraints:
                if con.type in conflict_types:
                    issues.append(
                        f"Potential conflict: '{obj_name}' has {con.type} constraint "
                        f"that may interfere with proxy operation"
                    )

        if issues:
            for issue in issues:
                self.report({"WARNING"}, issue)
            self.report({"WARNING"}, f"Validation found {len(issues)} issue(s)")
        else:
            self.report({"INFO"}, "Session is valid — no issues found")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 43 — Unsupported Setup Warning
# ---------------------------------------------------------------------------

class AA_OT_p7_check_setup(bpy.types.Operator):
    """Check if the target has conflicting constraints or transforms."""

    bl_idname = "animassist.p7_check_setup"
    bl_label = "Check Setup"
    bl_description = (
        "Verify that the active object's constraints and transforms "
        "are compatible with proxy operation"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        issues = []

        # Check for existing conflicting constraints.
        conflict_types = ("CHILD_OF", "ARMATURE", "OBJECT_SOLVER", "POLE_TARGET")
        for con in obj.constraints:
            if con.type in conflict_types:
                issues.append(
                    f"Conflict: constraint '{con.name}' ({con.type}) may interfere "
                    f"with proxy operation"
                )

        # Check for unusual transform state.
        import math
        loc = obj.location
        rot = obj.rotation_euler
        scale = obj.scale

        if any(math.isnan(v) for v in (*loc, *rot, *scale)):
            issues.append("Warning: object has NaN values in transform")

        if any(abs(v) > 1e6 for v in (*loc, *rot)):
            issues.append("Warning: object has extremely large transform values")

        if any(abs(s) < 1e-6 for s in scale):
            issues.append("Warning: object has near-zero scale which may cause issues")

        # Check if object has a parent (parent-in-transform).
        if obj.parent is not None:
            issues.append(f"Note: object is parented to '{obj.parent.name}' — "
                         f"proxy will be in world space")

        if issues:
            for issue in issues:
                self.report({"WARNING"}, issue)
            self.report({"WARNING"}, f"Setup check found {len(issues)} issue(s)")
        else:
            self.report({"INFO"}, "Setup is compatible with proxy operation")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 44 — Proxy Mirroring
# ---------------------------------------------------------------------------

class AA_OT_p7_mirror_proxy(bpy.types.Operator):
    """Create a mirrored copy of the selected proxy on the opposite side."""

    bl_idname = "animassist.p7_mirror_proxy"
    bl_label = "Mirror Proxy"
    bl_description = (
        "Duplicate the active proxy mirrored across the YZ plane and "
        "attempt to link it to the opposite-side target"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        p7 = get_p7(context)
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        src = context.active_object
        new_name = mirror_name(src.name)

        # Create mirrored empty.
        mirror = bpy.data.objects.new(new_name, None)
        mirror.empty_display_type = src.empty_display_type if src.type == "EMPTY" else "PLAIN_AXES"
        if src.type == "EMPTY":
            mirror.empty_display_size = src.empty_display_size
        mirror.location = (-src.location.x, src.location.y, src.location.z)
        mirror.color = src.color[:]

        coll = _get_temp_collection(context, session)
        coll.objects.link(mirror)

        p7s.tag_artifact(mirror, session.session_id, "mirrored_proxy",
                         owner_obj_name=src.get(p7s.TAG_OWNER_OBJ, ""))
        session.register_object(new_name, "mirrored_proxy")
        p7s.save_session_to_scene(session.session_id)

        self.report({"INFO"}, f"Mirrored '{src.name}' → '{mirror.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 45 — One-Click Proxy & Bake
# ---------------------------------------------------------------------------

class AA_OT_p7_one_click_proxy_bake(bpy.types.Operator):
    """Create a proxy, bake the animation through it, then clean up."""

    bl_idname = "animassist.p7_one_click_proxy_bake"
    bl_label = "One-Click Proxy & Bake"
    bl_description = (
        "Automation: record the active object's world motion on a temporary "
        "translation proxy, bake it back to keys, then remove that proxy. "
        "Other proxy sessions are left alone"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and get_p7(context) is not None

    def execute(self, context):
        from .p7_bake_ops import (
            _bake_object_transform, _get_bake_range, _reduce_fcurves, _restore_frame,
        )

        p7 = get_p7(context)
        target = context.active_object
        cfg = PROXY_CONFIGS["TRANSLATION"]
        scene = context.scene
        frame_start, frame_end = _get_bake_range(context, p7)
        frames = list(range(frame_start, frame_end + 1, max(1, p7.bake_step)))

        # Record the target's world motion before anything constrains it, so the
        # proxy carries that motion instead of a single still position.
        original_frame = float(scene.frame_current_final)
        motion = []
        for frame in frames:
            scene.frame_set(frame)
            motion.append((frame, target.matrix_world.translation.copy()))
        _restore_frame(scene, original_frame)

        # Use a session of its own so the rollback below never removes the
        # helpers of a proxy session the user already has open.
        previous_id = p7.active_session_id
        previous = p7s.get_session(previous_id) if previous_id else None
        session = p7s.begin_session(scene.name)
        p7.active_session_id = session.session_id
        proxy_action = None
        try:
            # Create proxy, keyed along the recorded motion.
            name = proxy_object_name(target.name, "TRANSLATION", session.short_id)
            proxy = bpy.data.objects.new(name, None)
            proxy.empty_display_type = cfg.empty_display
            proxy.empty_display_size = p7.proxy_size
            proxy.location = motion[0][1] if motion else target.matrix_world.translation

            coll = _get_temp_collection(context, session)
            coll.objects.link(proxy)
            p7s.tag_artifact(proxy, session.session_id, "proxy_translation",
                             owner_obj_name=target.name)
            session.register_object(name, "proxy_translation")
            for frame, position in motion:
                proxy.location = position
                proxy.keyframe_insert(data_path="location", frame=frame)
            if proxy.animation_data is not None:
                proxy_action = proxy.animation_data.action

            # Add constraint.
            con_name = p7s.make_constraint_name(session.session_id, cfg.constraint_suffix)
            con = target.constraints.new(cfg.constraint_type)
            con.name = con_name
            con.target = proxy
            session.register_constraint(target.name, "", con_name)
            p7s.save_session_to_scene(session.session_id)

            # Bake.
            _bake_object_transform(context, target, frame_start, frame_end,
                                   step=p7.bake_step, channel_mode=p7.bake_channels)
            _reduce_fcurves(target, p7.smart_bake_tolerance)
        finally:
            # Cleanup, then hand the scene record back to the earlier session.
            p7s.rollback_session(session.session_id)
            if proxy_action is not None and proxy_action.users == 0:
                bpy.data.actions.remove(proxy_action)
            if previous is not None:
                p7.active_session_id = previous_id
                p7s.save_session_to_scene(previous_id)
            else:
                p7s.clear_scene_session(scene)
                p7.active_session_id = ""

        self.report({"INFO"},
                    f"One-click proxy bake complete for '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 45 — One-Click Cleanup
# ---------------------------------------------------------------------------

class AA_OT_p7_one_click_cleanup(bpy.types.Operator):
    """Bake all session constraints and clean up all artifacts."""

    bl_idname = "animassist.p7_one_click_cleanup"
    bl_label = "One-Click Cleanup"
    bl_description = (
        "Bake every constrained object in the active session, "
        "then perform a full session rollback"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None

    def execute(self, context):
        from .p7_bake_ops import _bake_object_transform, _get_bake_range, _reduce_fcurves

        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        if session is None:
            self.report({"WARNING"}, "No active session")
            return {"CANCELLED"}

        frame_start, frame_end = _get_bake_range(context, p7)

        # Bake all constrained objects.
        obj_names = {rec.object_name for rec in session.created_constraints}
        for name in obj_names:
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            _bake_object_transform(context, obj, frame_start, frame_end,
                                   step=p7.bake_step, channel_mode=p7.bake_channels)
            _reduce_fcurves(obj, p7.smart_bake_tolerance)

        # Full rollback.
        n_obj = len(session.created_objects)
        p7s.rollback_session(session.session_id)
        p7s.clear_scene_session(context.scene)
        p7.active_session_id = ""

        self.report({"INFO"}, f"One-click cleanup: baked and removed {n_obj} artifact(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 45 — Quick Proxy
# ---------------------------------------------------------------------------

class AA_OT_p7_quick_proxy(bpy.types.Operator):
    """Create a translation proxy with default settings in one click."""

    bl_idname = "animassist.p7_quick_proxy"
    bl_label = "Quick Proxy"
    bl_description = (
        "Shortcut: create a Translation Proxy with current defaults, "
        "auto-constrained to the active object"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and get_p7(context) is not None

    def execute(self, context):
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        p7 = get_p7(context)
        target = context.active_object
        cfg = PROXY_CONFIGS["TRANSLATION"]
        world_pos = target.matrix_world.translation.copy()
        name = proxy_object_name(target.name, "TRANSLATION", session.short_id)

        proxy = bpy.data.objects.new(name, None)
        proxy.empty_display_type = cfg.empty_display
        proxy.empty_display_size = p7.proxy_size
        proxy.location = world_pos
        proxy.color = (*p7.proxy_color, 1.0)

        coll = _get_temp_collection(context, session)
        coll.objects.link(proxy)
        p7s.tag_artifact(proxy, session.session_id, "proxy_translation",
                         owner_obj_name=target.name)
        session.register_object(name, "proxy_translation")

        # Auto-constrain.
        con_name = p7s.make_constraint_name(session.session_id, cfg.constraint_suffix)
        con = target.constraints.new(cfg.constraint_type)
        con.name = con_name
        con.target = proxy
        session.register_constraint(target.name, "", con_name)

        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Quick proxy created for '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 45 — Export Session
# ---------------------------------------------------------------------------

class AA_OT_p7_export_session(bpy.types.Operator):
    """Export session data as JSON to the clipboard."""

    bl_idname = "animassist.p7_export_session"
    bl_label = "Export Session"
    bl_description = (
        "Serialize the active session's state to JSON and copy "
        "it to the system clipboard"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        return bool(p7.active_session_id) and p7s.get_session(p7.active_session_id) is not None

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        if session is None:
            self.report({"WARNING"}, "No active session")
            return {"CANCELLED"}

        blob = json.dumps(session.to_dict(), indent=2)
        context.window_manager.clipboard = blob
        self.report({"INFO"},
                    f"Session {session.short_id} exported to clipboard "
                    f"({len(blob)} chars)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p7_cleanup_session,
    AA_OT_p7_cleanup_all,
    AA_OT_p7_remove_proxy,
    AA_OT_p7_remove_constraints,
    AA_OT_p7_batch_create_proxies,
    AA_OT_p7_auto_cleanup,
    AA_OT_p7_validate_session,
    AA_OT_p7_check_setup,
    AA_OT_p7_mirror_proxy,
    AA_OT_p7_one_click_proxy_bake,
    AA_OT_p7_one_click_cleanup,
    AA_OT_p7_quick_proxy,
    AA_OT_p7_export_session,
)
