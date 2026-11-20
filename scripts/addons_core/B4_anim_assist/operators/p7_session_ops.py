# --- SESSION SETUP ---
"""Session safety-hatch operators.

These operators are available as user-accessible recovery tools before any
rigging feature operators exist.  They allow the user (or the addon itself)
to detect and clean up orphaned proxy-session artifacts.

Operators:

* **Purge P7 Artifacts** — remove all tagged temporary objects, collections,
  and constraints from the current scene.  Visible only when stale session
  data is detected.

* **Recover P7 Session** — attempt to reconstruct a P7Session from the
  scene's custom property so rollback or commit can be completed.  This is
  the entry point called by the ``_on_load_post`` handler when it finds a
  non-committed session record.
"""

from __future__ import annotations

import bpy

from ..core.logging import get_logger
from ..core import p7_session as p7s

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Purge All Rigging Artifacts
# ---------------------------------------------------------------------------

class AA_OT_p7_purge_artifacts(bpy.types.Operator):
    """Remove all temporary rigging objects, constraints, and collections."""

    bl_idname = "animassist.p7_purge_artifacts"
    bl_label = "Purge Proxy Artifacts"
    bl_description = (
        "Remove all temporary objects, constraints, and collections "
        "created by proxy/bake workflows"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "scene") or context.scene is None:
            return False
        # Show this operator only if the scene has a P7 session record
        # or there are tagged temp objects in the file.
        scene = context.scene
        if scene.get(p7s.SCENE_SESSION_KEY) is not None:
            return True
        # Fallback: scan objects for the temp tag (capped for poll perf).
        for obj in bpy.data.objects:
            if obj.get(p7s.TAG_TEMP):
                return True
        return False

    def execute(self, context):
        removed = p7s.purge_session_artifacts(session_id=None)
        # Also clear the Python-side registry in case any sessions lingered.
        p7s.clear_all_sessions()

        if removed:
            self.report({"INFO"}, f"Purged {removed} P7 artifact(s)")
        else:
            self.report({"INFO"}, "No P7 artifacts found to purge")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 2. Recover / Inspect Stale Session
# ---------------------------------------------------------------------------

class AA_OT_p7_recover_session(bpy.types.Operator):
    """Inspect and optionally roll back a stale rigging session on this scene."""

    bl_idname = "animassist.p7_recover_session"
    bl_label = "Recover Proxy Session"
    bl_description = (
        "Detect incomplete proxy sessions and roll back "
        "their artifacts to restore the scene to a clean state"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "scene") or context.scene is None:
            return False
        return context.scene.get(p7s.SCENE_SESSION_KEY) is not None

    def execute(self, context):
        scene = context.scene
        session = p7s.load_session_from_scene(scene)
        if session is None:
            self.report({"WARNING"}, "No recoverable session data on this scene")
            # Clear the stale key anyway.
            p7s.clear_scene_session(scene)
            return {"CANCELLED"}

        if session.stage == "COMMITTED":
            # Session was already committed; just remove the stale record.
            p7s.clear_scene_session(scene)
            self.report({"INFO"}, "Stale committed-session record cleaned up")
            return {"FINISHED"}

        # Reconstruct the session into the Python registry so rollback
        # can use it.
        from ..core.p7_session import _sessions
        _sessions[session.session_id] = session

        ok = p7s.rollback_session(session.session_id)
        p7s.clear_scene_session(scene)

        if ok:
            self.report(
                {"INFO"},
                f"Session {session.short_id} recovered — "
                f"{len(session.created_objects)} object(s), "
                f"{len(session.created_constraints)} constraint(s) removed",
            )
        else:
            self.report(
                {"WARNING"},
                f"Session {session.short_id} recovery completed with errors — "
                "some artifacts may remain",
            )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p7_purge_artifacts,
    AA_OT_p7_recover_session,
)
