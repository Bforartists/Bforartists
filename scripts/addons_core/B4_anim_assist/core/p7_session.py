# --- PROXY AND BAKE PREP ---
"""Session management for proxy / bake / helper-object workflows.

proxy introduces temporary scene artifacts (objects, collections,
constraints) that must be tracked and cleaned up reliably.  This module
provides the centralized session registry, rollback, commit, and
stale-session detection that all proxy operators depend on.

No proxy operator may create a scene artifact without registering it
through this module.

Architecture overview
---------------------

Tier 1 — **Python-side registry** (module-level ``_sessions`` dict)
    Fast-path lookup during a running session.  Lost on Blender shutdown.

Tier 2 — **Scene-side persistence** (custom property on ``bpy.types.Scene``)
    JSON-serialized session record survives file save/reload so orphaned
    artifacts can be detected and purged even after a crash.

The session lifecycle is:

    begin  →  ACTIVE  →  BAKING  →  commit  →  (session removed)
                 │                      │
                 └── rollback ──────────┘  →  (artifacts purged)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Literal

from .logging import get_logger

__all__ = [
    "SessionStage",
    "ConstraintRecord",
    "P7Session",
    "get_session",
    "get_all_sessions",
    "restore_session",
    "clear_all_sessions",
    "begin_session",
    "set_stage",
    "commit_session",
    "rollback_session",
    "save_session_to_scene",
    "load_session_from_scene",
    "clear_scene_session",
    "detect_stale_sessions",
    "purge_session_artifacts",
    "tag_artifact",
    "make_constraint_name",
    "exclude_from_view_layers",
    "TAG_TEMP",
    "TAG_SESSION_ID",
    "TAG_ARTIFACT_ROLE",
    "TAG_OWNER_OBJ",
    "CONSTRAINT_PREFIX",
    "SCENE_SESSION_KEY",
    "TEMP_COLLECTION_TEMPLATE",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants (mirrored from constants.py for convenience)
# ---------------------------------------------------------------------------

#: Custom-property key set on every temporary scene object / collection.
TAG_TEMP: str = "anim_assist_temp"
#: Session UUID stored as a custom property on every temporary artifact.
TAG_SESSION_ID: str = "anim_assist_session_id"
#: Role descriptor for the artifact ("proxy_locator", "bake_target", …).
TAG_ARTIFACT_ROLE: str = "anim_assist_artifact_role"
#: Name of the source object that "owns" this artifact.
TAG_OWNER_OBJ: str = "anim_assist_owner_obj"

#: Name prefix for injected constraints (first 8 chars of session_id
#: are appended).  Constraints cannot carry custom properties, so the
#: name prefix is the only scanner-detectable tag.
CONSTRAINT_PREFIX: str = "AA_P7_"

#: Scene custom-property key holding the JSON session record.
SCENE_SESSION_KEY: str = "anim_assist_p7_session"

#: Collection name template for temporary helper collections.
TEMP_COLLECTION_TEMPLATE: str = "AA_P7_Temp_{short_id}"


# ---------------------------------------------------------------------------
# Session stages
# ---------------------------------------------------------------------------

SessionStage = Literal["ACTIVE", "BAKING", "COMMITTED", "ABORTED"]


# ---------------------------------------------------------------------------
# Constraint record
# ---------------------------------------------------------------------------

@dataclass
class ConstraintRecord:
    """Identifies an injected constraint by its owner and name."""

    object_name: str
    bone_name: str       # Empty string for object-level constraints.
    constraint_name: str

    def as_dict(self) -> dict:
        """Serialize constraint record to a JSON-safe dict."""
        return {
            "object_name": self.object_name,
            "bone_name": self.bone_name,
            "constraint_name": self.constraint_name,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ConstraintRecord:
        """Reconstruct constraint record from a dict."""
        return cls(
            object_name=d["object_name"],
            bone_name=d["bone_name"],
            constraint_name=d["constraint_name"],
        )


# ---------------------------------------------------------------------------
# P7Session dataclass
# ---------------------------------------------------------------------------

@dataclass
class P7Session:
    """Canonical record of a single proxy / bake session."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scene_name: str = ""
    stage: SessionStage = "ACTIVE"

    # Artifact tracking — names, not pointers, so they can be serialized.
    created_objects: list[str] = field(default_factory=list)
    created_constraints: list[ConstraintRecord] = field(default_factory=list)
    created_collections: list[str] = field(default_factory=list)
    created_custom_props: list[tuple[str, str]] = field(default_factory=list)

    # Pre-operation backup (opaque dict consumed by restore logic).
    pre_state_backup: dict | None = None

    @property
    def short_id(self) -> str:
        """First 8 chars of the UUID, used for naming."""
        return self.session_id[:8]

    # ----- Artifact registration ----- #

    def register_object(self, obj_name: str, role: str = "helper") -> None:
        """Register a temporary object so it can be cleaned up on rollback.

        Called when creating proxy empties, bake targets, or helper objects.
        """
        if obj_name not in self.created_objects:
            self.created_objects.append(obj_name)
        _log.debug("Session %s: registered object '%s' (role=%s)",
                   self.short_id, obj_name, role)

    def register_constraint(
        self,
        object_name: str,
        bone_name: str,
        constraint_name: str,
    ) -> None:
        """Register an injected constraint so it can be removed on rollback.

        Called when adding driving constraints from proxies to targets.
        Constraints are always removed BEFORE objects to avoid breaking references.
        """
        rec = ConstraintRecord(object_name, bone_name, constraint_name)
        self.created_constraints.append(rec)
        _log.debug("Session %s: registered constraint '%s' on %s/%s",
                   self.short_id, constraint_name, object_name, bone_name)

    def register_collection(self, coll_name: str) -> None:
        """Register a temporary collection so it can be removed on rollback.

        Called when creating helper collections for proxy/target organization.
        """
        if coll_name not in self.created_collections:
            self.created_collections.append(coll_name)
        _log.debug("Session %s: registered collection '%s'",
                   self.short_id, coll_name)

    def register_custom_prop(self, obj_name: str, prop_key: str) -> None:
        """Register a custom property so it can be removed on rollback.

        Called when tagging artifacts or storing session metadata on objects.
        """
        pair = (obj_name, prop_key)
        if pair not in self.created_custom_props:
            self.created_custom_props.append(pair)

    # ----- Serialization ----- #

    def to_dict(self) -> dict:
        """Convert session to a JSON-safe dict for scene-side persistence.

        Used to save the session to a scene custom property so it survives
        a Blender crash and can be recovered on file re-load.
        """
        return {
            "session_id": self.session_id,
            "scene_name": self.scene_name,
            "stage": self.stage,
            "created_objects": list(self.created_objects),
            "created_constraints": [c.as_dict() for c in self.created_constraints],
            "created_collections": list(self.created_collections),
            "created_custom_props": [list(p) for p in self.created_custom_props],
        }

    @classmethod
    def from_dict(cls, d: dict) -> P7Session:
        """Reconstruct session from a dict loaded from scene persistence.

        Used when recovering from a crash-saved session record.
        """
        session = cls(
            session_id=d["session_id"],
            scene_name=d.get("scene_name", ""),
            stage=d.get("stage", "ACTIVE"),
        )
        session.created_objects = list(d.get("created_objects", []))
        session.created_constraints = [
            ConstraintRecord.from_dict(c)
            for c in d.get("created_constraints", [])
        ]
        session.created_collections = list(d.get("created_collections", []))
        session.created_custom_props = [
            tuple(p) for p in d.get("created_custom_props", [])
        ]
        return session


# ---------------------------------------------------------------------------
# Module-level session registry (Tier 1 — Python-side)
# ---------------------------------------------------------------------------

_sessions: dict[str, P7Session] = {}


def get_session(session_id: str) -> P7Session | None:
    """Look up a session by its UUID."""
    return _sessions.get(session_id)


def get_all_sessions() -> dict[str, P7Session]:
    """Return the full session registry (read-only intent)."""
    return dict(_sessions)


def restore_session(session: P7Session) -> None:
    """Insert a reconstructed session into the Python-side registry.

    Used by the reconnect operator to re-register sessions loaded from
    scene-side persistence (Tier 2) without touching private internals.
    """
    _sessions[session.session_id] = session
    _log.info("P7 session %s restored into registry", session.short_id)


def clear_all_sessions() -> None:
    """Drop all Python-side session state.  Called on file-load and disable."""
    _sessions.clear()
    _log.debug("All P7 sessions cleared from Python registry")


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------

def begin_session(scene_name: str) -> P7Session:
    """Create and register a new session.  Returns the session object."""
    session = P7Session(scene_name=scene_name)
    _sessions[session.session_id] = session
    _log.info("P7 session %s started for scene '%s'",
              session.short_id, scene_name)
    return session


def set_stage(session_id: str, stage: SessionStage) -> None:
    """Transition a session to a new stage."""
    session = _sessions.get(session_id)
    if session is None:
        _log.warning("set_stage: unknown session %s", session_id)
        return
    old = session.stage
    session.stage = stage
    _log.debug("Session %s: %s → %s", session.short_id, old, stage)


def commit_session(session_id: str) -> None:
    """Mark a session as committed and remove it from the registry.

    At commit time all temporary artifacts should already have been removed
    by the operator.  This method only cleans up the bookkeeping.
    """
    session = _sessions.pop(session_id, None)
    if session is None:
        _log.warning("commit_session: unknown session %s", session_id)
        return
    session.stage = "COMMITTED"
    _log.info("P7 session %s committed", session.short_id)


# ---------------------------------------------------------------------------
# Rollback — CONSTRAINT REMOVAL BEFORE OBJECT DELETION (strictly enforced)
# ---------------------------------------------------------------------------

def rollback_session(session_id: str) -> bool:
    """Roll back all artifacts registered under *session_id*.

    Returns True if rollback completed without errors, False otherwise.
    Safe to call multiple times — idempotent.

    **Order of operations** (non-negotiable for rig safety):
    1. Remove constraints first (so targets are still valid).
    2. Unlink and remove objects.
    3. Unlink and remove collections.
    4. Remove custom properties.
    5. Drop session from registry.
    """

    session = _sessions.get(session_id)
    if session is None:
        _log.debug("rollback_session: session %s not found — already rolled back?",
                    session_id)
        return True

    session.stage = "ABORTED"
    ok = True

    # 1. Remove constraints FIRST.
    ok = _rollback_constraints(session, ok)

    # 2. Remove objects.
    ok = _rollback_objects(session, ok)

    # 3. Remove collections.
    ok = _rollback_collections(session, ok)

    # 4. Remove custom properties.
    _rollback_custom_props(session)

    # 5. Drop from registry.
    _sessions.pop(session_id, None)
    _log.info("P7 session %s rolled back (%s)", session_id[:8],
              "clean" if ok else "with errors")
    return ok


def _rollback_constraints(session: P7Session, ok: bool) -> bool:
    """Helper: remove constraints from session."""
    import bpy

    for rec in session.created_constraints:
        try:
            obj = bpy.data.objects.get(rec.object_name)
            if obj is None:
                continue
            if rec.bone_name and hasattr(obj, "pose") and obj.pose:
                bone = obj.pose.bones.get(rec.bone_name)
                if bone is None:
                    continue
                con = bone.constraints.get(rec.constraint_name)
                if con is not None:
                    bone.constraints.remove(con)
                    _log.debug("Rollback: removed constraint '%s' from bone '%s'",
                               rec.constraint_name, rec.bone_name)
            else:
                con = obj.constraints.get(rec.constraint_name)
                if con is not None:
                    obj.constraints.remove(con)
                    _log.debug("Rollback: removed object constraint '%s' from '%s'",
                               rec.constraint_name, rec.object_name)
        except Exception:
            _log.exception("Rollback: failed to remove constraint '%s'",
                           rec.constraint_name)
            ok = False
    return ok


def _rollback_objects(session: P7Session, ok: bool) -> bool:
    """Helper: remove objects from session."""
    import bpy

    for obj_name in session.created_objects:
        try:
            obj = bpy.data.objects.get(obj_name)
            if obj is None:
                continue
            # Unlink from all collections first.
            for coll in list(obj.users_collection):
                coll.objects.unlink(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
            _log.debug("Rollback: removed object '%s'", obj_name)
        except Exception:
            _log.exception("Rollback: failed to remove object '%s'", obj_name)
            ok = False
    return ok


def _rollback_collections(session: P7Session, ok: bool) -> bool:
    """Helper: remove collections from session."""
    import bpy

    for coll_name in session.created_collections:
        try:
            coll = bpy.data.collections.get(coll_name)
            if coll is None:
                continue
            bpy.data.collections.remove(coll)
            _log.debug("Rollback: removed collection '%s'", coll_name)
        except Exception:
            _log.exception("Rollback: failed to remove collection '%s'", coll_name)
            ok = False
    return ok


def _rollback_custom_props(session: P7Session) -> None:
    """Helper: remove custom properties from session."""
    import bpy

    for obj_name, prop_key in session.created_custom_props:
        try:
            obj = bpy.data.objects.get(obj_name)
            if obj is not None and prop_key in obj:
                del obj[prop_key]
        except Exception:
            _log.debug("Rollback: custom property cleanup failed for %s.%s",
                       obj_name, prop_key, exc_info=True)


# ---------------------------------------------------------------------------
# Scene-side persistence (Tier 2)
# ---------------------------------------------------------------------------

def save_session_to_scene(session_id: str) -> None:
    """Serialize the session to a custom property on its owning scene.

    Must be called after each artifact registration so the scene-side
    record stays in sync for crash-recovery purposes.
    """
    import bpy

    session = _sessions.get(session_id)
    if session is None:
        return
    scene = bpy.data.scenes.get(session.scene_name)
    if scene is None:
        return
    scene[SCENE_SESSION_KEY] = json.dumps(session.to_dict())


def load_session_from_scene(scene) -> P7Session | None:
    """Attempt to reconstruct a session from a scene's custom property.

    Returns ``None`` if no session record is stored or parsing fails.
    """
    raw = scene.get(SCENE_SESSION_KEY)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return P7Session.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        _log.warning("Failed to parse P7 session from scene '%s'", scene.name)
        return None


def clear_scene_session(scene) -> None:
    """Remove the session record from the scene custom property."""
    try:
        del scene[SCENE_SESSION_KEY]
    except KeyError:
        pass


# ---------------------------------------------------------------------------
# Stale-session detection (called from _on_load_post)
# ---------------------------------------------------------------------------

def detect_stale_sessions() -> list[P7Session]:
    """Scan all scenes for non-COMMITTED session records.

    Returns a list of session objects that were found on scenes but
    are not in the COMMITTED state, meaning they represent incomplete
    workflows whose artifacts may still be in the file.
    """
    import bpy

    stale: list[P7Session] = []
    for scene in bpy.data.scenes:
        session = load_session_from_scene(scene)
        if session is None:
            continue
        if session.stage != "COMMITTED":
            stale.append(session)
            _log.warning(
                "Stale P7 session detected: %s (stage=%s) on scene '%s'",
                session.short_id, session.stage, scene.name,
            )
    return stale


# ---------------------------------------------------------------------------
# Orphan scanner — fallback artifact purge by tag scanning
# ---------------------------------------------------------------------------

def purge_session_artifacts(session_id: str | None = None) -> int:
    """Remove all tagged temporary artifacts from the file.

    If *session_id* is given, only artifacts matching that session are
    removed.  If ``None``, ALL tagged artifacts are purged.

    **Removal order**: constraints → objects → collections.

    Returns the total number of artifacts removed.
    """
    import bpy

    removed = 0

    # --- Constraints (scan all pose bones) ---
    prefix = CONSTRAINT_PREFIX
    if session_id:
        prefix = f"{CONSTRAINT_PREFIX}{session_id[:8]}_"
    for obj in bpy.data.objects:
        # Object-level constraints.
        for con in list(obj.constraints):
            if con.name.startswith(prefix):
                obj.constraints.remove(con)
                removed += 1
        # Pose bone constraints.
        if hasattr(obj, "pose") and obj.pose:
            for bone in obj.pose.bones:
                for con in list(bone.constraints):
                    if con.name.startswith(prefix):
                        bone.constraints.remove(con)
                        removed += 1

    # --- Objects ---
    for obj in list(bpy.data.objects):
        if not obj.get(TAG_TEMP):
            continue
        if session_id and obj.get(TAG_SESSION_ID) != session_id:
            continue
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        bpy.data.objects.remove(obj, do_unlink=True)
        removed += 1

    # --- Collections ---
    for coll in list(bpy.data.collections):
        if not coll.get(TAG_TEMP):
            continue
        if session_id and coll.get(TAG_SESSION_ID) != session_id:
            continue
        bpy.data.collections.remove(coll)
        removed += 1

    # --- Scene session keys ---
    for scene in bpy.data.scenes:
        session = load_session_from_scene(scene)
        if session is None:
            continue
        if session_id is None or session.session_id == session_id:
            clear_scene_session(scene)

    if removed:
        _log.info("Purged %d P7 artifact(s)%s", removed,
                  f" for session {session_id[:8]}" if session_id else "")
    return removed


# ---------------------------------------------------------------------------
# Helper: tag an object or collection at creation time
# ---------------------------------------------------------------------------

def tag_artifact(
    data_block,
    session_id: str,
    role: str,
    owner_obj_name: str = "",
) -> None:
    """Apply the standard custom-property tags to a freshly created artifact.

    Must be called atomically in the same operator step as the creation.
    """
    data_block[TAG_TEMP] = True
    data_block[TAG_SESSION_ID] = session_id
    data_block[TAG_ARTIFACT_ROLE] = role
    if owner_obj_name:
        data_block[TAG_OWNER_OBJ] = owner_obj_name


def make_constraint_name(session_id: str, suffix: str) -> str:
    """Build a standard constraint name from session ID and a short suffix.

    Example: ``AA_P7_a3f8c12b_IK``
    """
    return f"{CONSTRAINT_PREFIX}{session_id[:8]}_{suffix}"


# ---------------------------------------------------------------------------
# Helper: exclude a collection from all view layers
# ---------------------------------------------------------------------------

def exclude_from_view_layers(scene, collection) -> None:  # type: ignore[no-untyped-def]
    """Recursively find *collection* in all view layers and set exclude=True.

    Prevents temporary objects from appearing in renders.
    """

    def _exclude_in_layer(layer_coll, target):  # type: ignore[no-untyped-def]
        """Recursively find and exclude target collection."""
        if layer_coll.collection == target:
            layer_coll.exclude = True
            return True
        for child in layer_coll.children:
            if _exclude_in_layer(child, target):
                return True
        return False

    for vl in scene.view_layers:
        _exclude_in_layer(vl.layer_collection, collection)
