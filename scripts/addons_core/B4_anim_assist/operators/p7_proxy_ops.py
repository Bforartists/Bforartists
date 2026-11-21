# --- RIGGING AND CONTROL SETUP ---
"""Proxy creation operators (Features 11-19).

A single unified operator ``AA_OT_p7_create_proxy`` handles all 9 proxy
types via a ``proxy_type`` EnumProperty.  The proxy configuration (empty
shape, constraint type, naming) is driven by the ``ProxyConfig`` registry
in ``core.p7_proxy_math``.
"""

from __future__ import annotations

import bpy
from mathutils import Vector

from ..core.logging import get_logger
from ..core import p7_session as p7s
from ..core.p7_properties import get_p7, PROXY_TYPE_ITEMS
from ..core.p7_proxy_math import (
    PROXY_CONFIGS,
    proxy_object_name,
)

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
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


def _proxy_type_items_fn(self, context):  # noqa: ARG001
    return PROXY_TYPE_ITEMS


def _compute_multi_target_position(context) -> Vector:
    """Compute the average position of all selected objects (excluding the active one).

    Used for MULTI_TARGET proxy type. Returns the average world position of all
    selected objects. If only one object is selected, returns its position.
    """
    selected = context.selected_objects
    if not selected:
        return Vector((0, 0, 0))

    positions = [obj.matrix_world.translation.copy() for obj in selected]
    avg_pos = sum(positions, Vector((0, 0, 0))) / len(positions)
    return avg_pos


# ---------------------------------------------------------------------------
# Unified proxy creation operator
# ---------------------------------------------------------------------------

class AA_OT_p7_create_proxy(bpy.types.Operator):
    """Create a proxy helper for the active object or bone."""

    bl_idname = "animassist.p7_create_proxy"
    bl_label = "Create Proxy"
    bl_description = (
        "Create a proxy helper of the chosen type, optionally "
        "auto-constraining it to the active object or bone"
    )
    bl_options = {"REGISTER", "UNDO"}

    proxy_type: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Proxy Type",
        description="Type of temporary helper to create for the active object or bone",
        items=_proxy_type_items_fn,
        default=0,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        session = _ensure_session(context)
        if session is None:
            self.report({"ERROR"}, "Cannot start a proxy session. Make sure the scene is editable (not a linked library) and try again")
            return {"CANCELLED"}

        p7 = get_p7(context)
        cfg = PROXY_CONFIGS.get(self.proxy_type)
        if cfg is None:
            self.report({"ERROR"}, f"Unknown proxy type '{self.proxy_type}'. Pick a type in the Create Proxy dropdown")
            return {"CANCELLED"}

        target_obj = context.active_object
        target_bone = getattr(context, "active_pose_bone", None)

        # Determine the world position for the proxy.
        # For MULTI_TARGET, use the average of all selected objects.
        if self.proxy_type == "MULTI_TARGET":
            world_pos = _compute_multi_target_position(context)
            target_name = target_obj.name
        elif target_bone is not None and target_obj.type == "ARMATURE":
            world_pos = (target_obj.matrix_world @ target_bone.matrix).translation.copy()
            target_name = target_bone.name
        else:
            world_pos = target_obj.matrix_world.translation.copy()
            target_name = target_obj.name

        proxy_name = proxy_object_name(target_name, self.proxy_type, session.short_id)

        # Create the proxy object (always an empty).
        proxy = bpy.data.objects.new(proxy_name, None)
        proxy.empty_display_type = cfg.empty_display
        if p7 is not None:
            proxy.empty_display_size = p7.proxy_size
        proxy.location = world_pos

        # Set wireframe colour.
        if p7 is not None:
            proxy.color = (*p7.proxy_color, 1.0)

        # Link to session collection.
        coll = _get_temp_collection(context, session)
        coll.objects.link(proxy)

        # Tag and register.
        p7s.tag_artifact(proxy, session.session_id, f"proxy_{self.proxy_type.lower()}",
                         owner_obj_name=target_obj.name)
        session.register_object(proxy_name, f"proxy_{self.proxy_type.lower()}")

        # Add constraint if auto-constrain is on and config has a constraint type.
        if p7 is not None and p7.auto_constrain and cfg.constraint_type is not None:
            con_name = p7s.make_constraint_name(session.session_id, cfg.constraint_suffix)

            if target_bone is not None:
                con = target_bone.constraints.new(cfg.constraint_type)
                con.name = con_name
                con.target = proxy
                session.register_constraint(target_obj.name, target_bone.name, con_name)
            else:
                con = target_obj.constraints.new(cfg.constraint_type)
                con.name = con_name
                con.target = proxy
                session.register_constraint(target_obj.name, "", con_name)

            if cfg.keyed_influence:
                con.influence = 0.0

        p7s.save_session_to_scene(session.session_id)
        self.report({"INFO"}, f"Created {self.proxy_type} proxy '{proxy_name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p7_create_proxy,
)
