# --- RIGGING AND CONTROL SETUP ---
"""Display, control, and utility operators (Features 20-23, 26-30, 36-39).

Operators for managing proxy visibility, naming, collection management, session
inspection, batch operations, and proxy helper utilities.
"""

from __future__ import annotations

import bpy

from ..core.logging import get_logger
from ..core import p7_session as p7s
from ..core.p7_properties import get_p7
from ..core.p7_proxy_math import PROXY_CONFIGS, proxy_object_name
from ..core.helpers import report_failure

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session_objects(session: p7s.P7Session):
    """Yield actual bpy objects that still exist in the file."""
    for name in session.created_objects:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            yield obj


def _ensure_session(context) -> p7s.P7Session | None:
    """Get or create the active session."""
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
    """Return or create the temp collection for this session."""
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
# Feature 20 — Toggle Proxy Display
# ---------------------------------------------------------------------------

class AA_OT_p7_toggle_display(bpy.types.Operator):
    """Cycle proxy visibility between Full, Dimmed, and Hidden."""

    bl_idname = "animassist.p7_toggle_display"
    bl_label = "Toggle Proxy Display"
    bl_description = (
        "Cycle all session proxies through Full → Dimmed → Hidden display modes"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_objects)

    def execute(self, context):
        p7 = get_p7(context)
        # Cycle: FULL → DIM → HIDDEN → FULL
        modes = ["FULL", "DIM", "HIDDEN"]
        idx = modes.index(p7.display_mode) if p7.display_mode in modes else 0
        new_mode = modes[(idx + 1) % len(modes)]
        p7.display_mode = new_mode

        session = p7s.get_session(p7.active_session_id)
        for obj in _session_objects(session):
            if new_mode == "HIDDEN":
                obj.hide_viewport = True
            elif new_mode == "DIM":
                obj.hide_viewport = False
                if obj.type == "EMPTY":
                    obj.empty_display_size = max(0.1, obj.empty_display_size * 0.5)
            else:  # FULL
                obj.hide_viewport = False
                if obj.type == "EMPTY":
                    obj.empty_display_size = p7.proxy_size

        self.report({"INFO"}, f"Proxy display: {new_mode}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 21 — Set Proxy Color
# ---------------------------------------------------------------------------

class AA_OT_p7_set_proxy_color(bpy.types.Operator):
    """Change the wireframe colour of the selected proxy."""

    bl_idname = "animassist.p7_set_proxy_color"
    bl_label = "Set Proxy Color"
    bl_description = "Apply the configured Proxy Color to the active proxy object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object
        if p7 is not None:
            obj.color = (*p7.proxy_color, 1.0)
        self.report({"INFO"}, f"Color applied to '{obj.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 22 — Rename Proxy
# ---------------------------------------------------------------------------

class AA_OT_p7_rename_proxy(bpy.types.Operator):
    """Rename the active proxy following the standard naming pattern."""

    bl_idname = "animassist.p7_rename_proxy"
    bl_label = "Rename Proxy"
    bl_description = "Rename the active proxy following the standard naming convention"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        obj = context.active_object
        p7 = get_p7(context)

        if p7 is None:
            self.report({"ERROR"}, "Proxy settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        # Get the session ID from the object tag
        session_id = obj.get(p7s.TAG_SESSION_ID)
        if not session_id:
            self.report({"ERROR"}, "This object is not part of a proxy session. Select a proxy created by Anim Assist")
            return {"CANCELLED"}

        session = p7s.get_session(session_id)
        if session is None:
            self.report({"ERROR"}, "Proxy session not found. Run Recover Proxy Session, or create a new proxy")
            return {"CANCELLED"}

        # Get the owner object name
        owner_name = obj.get(p7s.TAG_OWNER_OBJ, "Unknown")

        # Generate new name following the proxy naming convention
        new_name = proxy_object_name(owner_name, p7.proxy_type, session.short_id)

        # Capture old name BEFORE the rename so we can update the session registry.
        old_name = obj.name
        obj.name = new_name
        # Blender may append .001 etc. — read back the actual name.
        actual_name = obj.name

        # Update the session's created_objects list
        if old_name in session.created_objects:
            idx = session.created_objects.index(old_name)
            session.created_objects[idx] = actual_name

        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Renamed '{old_name}' → '{actual_name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 23 — Toggle Collection Visibility
# ---------------------------------------------------------------------------

class AA_OT_p7_toggle_collection(bpy.types.Operator):
    """Toggle visibility of the session's temp collection."""

    bl_idname = "animassist.p7_toggle_collection"
    bl_label = "Toggle Collection"
    bl_description = "Toggle visibility of the session's temporary collection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        session = p7s.get_session(p7.active_session_id) if p7.active_session_id else None
        return session is not None and bool(session.created_collections)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)

        # Get the temp collection
        coll = _get_temp_collection(context, session)

        # Toggle visibility in the viewport
        coll.hide_viewport = not coll.hide_viewport

        state = "hidden" if coll.hide_viewport else "visible"
        self.report({"INFO"}, f"Collection '{coll.name}' is now {state}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 26 — Reconnect Previous Proxy Session
# ---------------------------------------------------------------------------

class AA_OT_p7_reconnect_session(bpy.types.Operator):
    """Scan scene for P7-tagged objects and reconstruct a session from them."""

    bl_idname = "animassist.p7_reconnect_session"
    bl_label = "Reconnect Session"
    bl_description = "Scan the scene for P7-tagged objects and restore a session"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)

        # Scan all objects in the scene for P7 tags
        tagged_objects = {}
        for obj in context.scene.objects:
            if obj.get(p7s.TAG_TEMP):
                session_id = obj.get(p7s.TAG_SESSION_ID)
                if session_id:
                    if session_id not in tagged_objects:
                        tagged_objects[session_id] = []
                    tagged_objects[session_id].append(obj.name)

        if not tagged_objects:
            self.report({"WARNING"}, "No P7-tagged objects found in scene")
            return {"CANCELLED"}

        # Use the first (or most recent) session found
        session_id = list(tagged_objects.keys())[0]

        # Check if session already exists in registry
        existing_session = p7s.get_session(session_id)
        if existing_session is None:
            # Reconstruct the session from scene data
            scene_data = context.scene.get(p7s.SCENE_SESSION_KEY)
            if scene_data:
                import json
                try:
                    session_dict = json.loads(scene_data)
                    existing_session = p7s.P7Session.from_dict(session_dict)
                    p7s.restore_session(existing_session)
                except Exception as e:
                    _log.error("Failed to reconstruct session: %s", e)
                    report_failure(self, "Could not rebuild the proxy session", "Run Recover Session, or Cleanup Session to start fresh", e)
                    return {"CANCELLED"}
            else:
                # Create a new session with the tagged objects
                existing_session = p7s.begin_session(context.scene.name)
                for obj_name in tagged_objects[session_id]:
                    existing_session.register_object(obj_name)
                p7s.save_session_to_scene(existing_session.session_id)
                session_id = existing_session.session_id

        # Set as active session
        p7.active_session_id = session_id
        obj_count = len(tagged_objects[session_id])
        self.report({"INFO"}, f"Reconnected session {existing_session.short_id} with {obj_count} object(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 27 — List Sessions (Proxy Session Metadata)
# ---------------------------------------------------------------------------

class AA_OT_p7_list_sessions(bpy.types.Operator):
    """Print a summary of all active P7 sessions."""

    bl_idname = "animassist.p7_list_sessions"
    bl_label = "List Sessions"
    bl_description = "Report all active P7 sessions and their artifact counts"
    bl_options = {"REGISTER"}

    def execute(self, context):
        sessions = p7s.get_all_sessions()
        if not sessions:
            self.report({"INFO"}, "No active P7 sessions")
            return {"FINISHED"}

        for sid, s in sessions.items():
            self.report(
                {"INFO"},
                f"Session {s.short_id}: stage={s.stage}, "
                f"objects={len(s.created_objects)}, "
                f"constraints={len(s.created_constraints)}, "
                f"scene='{s.scene_name}'",
            )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 27b — Show Session Info
# ---------------------------------------------------------------------------

class AA_OT_p7_show_session_info(bpy.types.Operator):
    """Show detailed information about the active session."""

    bl_idname = "animassist.p7_show_session_info"
    bl_label = "Session Info"
    bl_description = "Display detailed information about the current P7 session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        if p7 is None:
            return False
        return bool(p7.active_session_id)

    def execute(self, context):
        p7 = get_p7(context)
        session = p7s.get_session(p7.active_session_id)
        if session is None:
            self.report({"WARNING"}, "No active session")
            return {"CANCELLED"}

        scene = bpy.data.scenes.get(session.scene_name)
        has_scene_record = (
            scene is not None and scene.get(p7s.SCENE_SESSION_KEY) is not None
        )

        self.report({"INFO"},
                    f"Session: {session.short_id} | Stage: {session.stage} | "
                    f"Scene: {session.scene_name} | "
                    f"Objects: {len(session.created_objects)} | "
                    f"Constraints: {len(session.created_constraints)} | "
                    f"Collections: {len(session.created_collections)} | "
                    f"Scene record: {'yes' if has_scene_record else 'no'}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 28 — Mute/Unmute Proxy Constraints
# ---------------------------------------------------------------------------

class AA_OT_p7_mute_constraints(bpy.types.Operator):
    """Toggle mute on all session constraints."""

    bl_idname = "animassist.p7_mute_constraints"
    bl_label = "Mute Constraints"
    bl_description = "Toggle mute on all constraints in the active session"
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

        # Determine the current mute state from the first constraint
        current_mute = None
        muted_count = 0
        unmuted_count = 0

        for rec in session.created_constraints:
            obj = bpy.data.objects.get(rec.object_name)
            if obj is None:
                continue

            # Find the constraint
            con = None
            if rec.bone_name and hasattr(obj, "pose") and obj.pose:
                bone = obj.pose.bones.get(rec.bone_name)
                if bone:
                    con = bone.constraints.get(rec.constraint_name)
            else:
                con = obj.constraints.get(rec.constraint_name)

            if con is not None:
                # Store the state of the first constraint as the toggle target
                if current_mute is None:
                    current_mute = con.mute

                # Toggle the mute state
                new_mute = not current_mute
                con.mute = new_mute

                if new_mute:
                    muted_count += 1
                else:
                    unmuted_count += 1

        total = muted_count + unmuted_count
        self.report({"INFO"}, f"Toggled {total} constraint(s): {muted_count} muted, {unmuted_count} unmuted")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 29 — Lock Original Target
# ---------------------------------------------------------------------------

class AA_OT_p7_lock_target(bpy.types.Operator):
    """Lock the original target's transform channels while proxy is active."""

    bl_idname = "animassist.p7_lock_target"
    bl_label = "Lock Target"
    bl_description = "Lock transform channels on the target object(s) of the active proxy"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        obj = context.active_object

        # Get the owner object (the target being proxied)
        owner_name = obj.get(p7s.TAG_OWNER_OBJ)
        if not owner_name:
            self.report({"ERROR"}, "This proxy is not linked to an object. Recreate it from its target")
            return {"CANCELLED"}

        target = bpy.data.objects.get(owner_name)
        if target is None:
            self.report({"ERROR"}, f"Target object '{owner_name}' was renamed or deleted. Recreate the proxy from its target")
            return {"CANCELLED"}

        # Lock all transform channels on the target
        target.lock_location = (True, True, True)
        target.lock_rotation = (True, True, True)
        target.lock_scale = (True, True, True)

        self.report({"INFO"}, f"Locked target '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 30 — Quick Switch Active Proxy Mode
# ---------------------------------------------------------------------------

class AA_OT_p7_switch_proxy_mode(bpy.types.Operator):
    """Toggle between CONSTRAIN and OFFSET modes."""

    bl_idname = "animassist.p7_switch_proxy_mode"
    bl_label = "Switch Proxy Mode"
    bl_description = "Toggle the active proxy between CONSTRAIN and OFFSET modes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p7 = get_p7(context)
        return p7 is not None

    def execute(self, context):
        p7 = get_p7(context)

        # Toggle between CONSTRAIN and OFFSET
        modes = ["CONSTRAIN", "OFFSET"]
        current = p7.proxy_mode if hasattr(p7, "proxy_mode") and p7.proxy_mode in modes else "CONSTRAIN"
        new_mode = "OFFSET" if current == "CONSTRAIN" else "CONSTRAIN"

        p7.proxy_mode = new_mode
        self.report({"INFO"}, f"Proxy mode switched to: {new_mode}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 36 — Apply Proxy Offset
# ---------------------------------------------------------------------------

class AA_OT_p7_apply_offset(bpy.types.Operator):
    """Apply the current proxy offset as additive on top of existing animation."""

    bl_idname = "animassist.p7_apply_offset"
    bl_label = "Apply Offset"
    bl_description = "Apply the current proxy offset as additive animation on the target"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        proxy = context.active_object

        # Get the target object
        owner_name = proxy.get(p7s.TAG_OWNER_OBJ)
        if not owner_name:
            self.report({"ERROR"}, "This proxy is not linked to an object. Recreate it from its target")
            return {"CANCELLED"}

        target = bpy.data.objects.get(owner_name)
        if target is None:
            self.report({"ERROR"}, f"Target object '{owner_name}' was renamed or deleted. Recreate the proxy from its target")
            return {"CANCELLED"}

        # Compute additive delta between proxy and target world transforms,
        # then apply as an offset so we don't obliterate existing animation.
        frame = context.scene.frame_current

        from mathutils import Vector, Euler

        proxy_world_loc = proxy.matrix_world.translation
        target_world_loc = target.matrix_world.translation
        delta_loc = Vector(proxy_world_loc) - Vector(target_world_loc)

        proxy_world_rot = proxy.matrix_world.to_euler()
        target_world_rot = target.matrix_world.to_euler()
        delta_rot = Euler((
            proxy_world_rot.x - target_world_rot.x,
            proxy_world_rot.y - target_world_rot.y,
            proxy_world_rot.z - target_world_rot.z,
        ))

        # Ensure animation data exists.
        if target.animation_data is None:
            target.animation_data_create()

        # Apply additive deltas (local space).
        target.location.x += delta_loc.x
        target.location.y += delta_loc.y
        target.location.z += delta_loc.z

        target.rotation_euler.x += delta_rot.x
        target.rotation_euler.y += delta_rot.y
        target.rotation_euler.z += delta_rot.z

        target.keyframe_insert(data_path="location", frame=frame)
        target.keyframe_insert(data_path="rotation_euler", frame=frame)

        self.report({"INFO"}, f"Applied offset delta to '{target.name}' at frame {frame}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 37 — Zero-Out Proxy Helper
# ---------------------------------------------------------------------------

class AA_OT_p7_zero_proxy(bpy.types.Operator):
    """Reset proxy transforms to identity."""

    bl_idname = "animassist.p7_zero_proxy"
    bl_label = "Zero Proxy"
    bl_description = "Reset the active proxy to identity transforms"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        proxy = context.active_object

        # Reset transforms to identity
        proxy.location = (0, 0, 0)
        proxy.rotation_euler = (0, 0, 0)
        proxy.scale = (1, 1, 1)

        self.report({"INFO"}, f"Reset '{proxy.name}' to identity")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 38 — Recenter Proxy to Driven Target
# ---------------------------------------------------------------------------

class AA_OT_p7_recenter_proxy(bpy.types.Operator):
    """Snap the proxy back to the driven target's current position."""

    bl_idname = "animassist.p7_recenter_proxy"
    bl_label = "Recenter Proxy"
    bl_description = "Snap the active proxy to the target's current position"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and bool(obj.get(p7s.TAG_TEMP))

    def execute(self, context):
        proxy = context.active_object

        # Get the target object
        owner_name = proxy.get(p7s.TAG_OWNER_OBJ)
        if not owner_name:
            self.report({"ERROR"}, "This proxy is not linked to an object. Recreate it from its target")
            return {"CANCELLED"}

        target = bpy.data.objects.get(owner_name)
        if target is None:
            self.report({"ERROR"}, f"Target object '{owner_name}' was renamed or deleted. Recreate the proxy from its target")
            return {"CANCELLED"}

        # Snap proxy to target's world position
        proxy.location = target.matrix_world.translation.copy()
        proxy.rotation_euler = target.rotation_euler.copy()

        self.report({"INFO"}, f"Recentered '{proxy.name}' to '{target.name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 39 — Temporary Pivot Proxy
# ---------------------------------------------------------------------------

class AA_OT_p7_temp_pivot(bpy.types.Operator):
    """Create a pivot-point proxy (POLE type with no constraint) at cursor."""

    bl_idname = "animassist.p7_temp_pivot"
    bl_label = "Temp Pivot"
    bl_description = "Create a pole helper proxy at the 3D cursor position"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        # Create a POLE proxy at the 3D cursor position
        cfg = PROXY_CONFIGS.get("POLE")
        if cfg is None:
            self.report({"ERROR"}, "No pole setup found. Create a pole proxy first")
            return {"CANCELLED"}

        # Use cursor location
        cursor_loc = context.scene.cursor.location.copy()
        name = f"AA_P7_Pivot_{session.short_id}"

        # Create empty as POLE type
        proxy = bpy.data.objects.new(name, None)
        proxy.empty_display_type = cfg.empty_display
        proxy.empty_display_size = p7.proxy_size
        proxy.location = cursor_loc
        proxy.color = (*p7.proxy_color, 1.0)

        # Add to temp collection
        coll = _get_temp_collection(context, session)
        coll.objects.link(proxy)

        # Tag as temporary artifact (no owner object for pivot)
        p7s.tag_artifact(proxy, session.session_id, "pivot_proxy", owner_obj_name="")
        session.register_object(name, "pivot_proxy")
        p7s.save_session_to_scene(session.session_id)

        self.report({"INFO"}, f"Created pivot proxy '{name}' at cursor")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p7_toggle_display,
    AA_OT_p7_set_proxy_color,
    AA_OT_p7_rename_proxy,
    AA_OT_p7_toggle_collection,
    AA_OT_p7_reconnect_session,
    AA_OT_p7_list_sessions,
    AA_OT_p7_show_session_info,
    AA_OT_p7_mute_constraints,
    AA_OT_p7_lock_target,
    AA_OT_p7_switch_proxy_mode,
    AA_OT_p7_apply_offset,
    AA_OT_p7_zero_proxy,
    AA_OT_p7_recenter_proxy,
    AA_OT_p7_temp_pivot,
)
