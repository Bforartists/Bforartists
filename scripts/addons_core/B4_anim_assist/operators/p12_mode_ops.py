# --- LIPSYNC MODE OPERATORS (Phase 12 / v12.0.0) ---
"""PREVIEW <-> SHIPPED mode toggle and render-pre warning handler.

PREVIEW mode: Blender drivers on every wired shape key/bone read the cue
table live. Scrub the audio and the mouth responds instantly. No fcurves
on the layer's Action.

SHIPPED mode: bake the driver evaluation into shape key fcurves. Drivers
removed. Render-ready, NLA-safe, exportable to game engines that don't
support drivers. Manual override sanctuary applies on rebake.

Animator blocks in PREVIEW for fast iteration, switches to SHIPPED before
final polish/render. The toggle does both in one click.
"""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..core import p12_cue_table as ct
from ..core import p12_driver_engine as de
from ..core import p12_lipsync_engine as engine
from ..core import p12_properties as p12_props
from ..core.logging import get_logger
from ..core.helpers import confirm_dialog

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _active_link(p12):
    if p12 is None or not p12.layer_links:
        return None
    if 0 <= p12.active_link_index < len(p12.layer_links):
        return p12.layer_links[p12.active_link_index]
    return None


def _resolve_link(p12, layer_name):
    if not layer_name:
        return _active_link(p12)
    return p12_props.find_layer_link(p12, layer_name) or _active_link(p12)


def _resolve_mesh(link):
    if not link or not link.mesh_name:
        return None
    obj = bpy.data.objects.get(link.mesh_name)
    if obj is None or obj.type != "MESH":
        return None
    return obj


def _shape_key_wiring_dict(p12):
    return {
        entry.viseme_name: entry.shape_key_name
        for entry in p12.shape_key_wiring
        if entry.shape_key_name
    }


def _ensure_shape_key_action(mesh_obj, link):
    """Return (or create) the Action that holds shape key fcurves for *mesh_obj*."""
    sk = mesh_obj.data.shape_keys
    if sk is None:
        return None
    if sk.animation_data is None:
        sk.animation_data_create()
    if sk.animation_data.action is None:
        sk.animation_data.action = bpy.data.actions.new(
            name="AA_P12_SK_" + link.layer_name
        )
    return sk.animation_data.action


# ---------------------------------------------------------------------------
# Toggle PREVIEW <-> SHIPPED
# ---------------------------------------------------------------------------

class AA_OT_p12_toggle_mode(Operator):
    """Switch the active lipsync layer between PREVIEW (live drivers) and SHIPPED (baked fcurves).

    PREVIEW -> SHIPPED: bake shape key fcurves from the cue table, then remove drivers.
    SHIPPED -> PREVIEW: clear auto-baked keys (manual override frames preserved), then install drivers.
    """

    bl_idname = "animassist.p12_toggle_mode"
    bl_label = "Toggle Live Preview <-> Shipped Bake"
    bl_options = {"REGISTER", "UNDO"}

    layer_name: StringProperty(  # type: ignore[valid-type]
        name="Layer Name",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        link = _resolve_link(p12, self.layer_name)
        if link is None:
            self.report({"ERROR"}, "No lipsync layer link selected. Select one in the Lipsync panel list first")
            return {"CANCELLED"}

        mesh = _resolve_mesh(link)
        wiring = _shape_key_wiring_dict(p12)

        if link.target_kind in ("SHAPE_KEYS", "BOTH") and (mesh is None or not wiring):
            self.report(
                {"ERROR"},
                "Shape key target requires a Mesh and at least one shape_key_wiring row",
            )
            return {"CANCELLED"}

        if link.mode == "PREVIEW":
            # PREVIEW -> SHIPPED
            cues = ct.read_cues_from_link(link)
            if not cues:
                self.report({"WARNING"}, "Cue table empty - bake will produce no keys")
            if link.target_kind in ("SHAPE_KEYS", "BOTH") and mesh is not None:
                action = _ensure_shape_key_action(mesh, link)
                if action is None:
                    self.report({"ERROR"}, "This mesh has no shape keys. Add mouth shape keys first")
                    return {"CANCELLED"}
                fps = context.scene.render.fps / max(1, context.scene.render.fps_base)
                report = engine.bake_shape_keys(
                    action=action,
                    cues=cues,
                    shape_key_wiring=wiring,
                    fps=fps,
                    frame_offset=link.frame_offset,
                    anticipation_frames=link.anticipation_frames,
                    anim_data=mesh.data.shape_keys.animation_data,
                )
                de.remove_drivers_for_link(mesh, wiring)
                self.report(
                    {"INFO"},
                    "SHIPPED: {} shape key keys written ({} preserved manual)".format(
                        report.keys_written, report.keys_skipped_manual
                    ),
                )
            link.mode = "SHIPPED"
        else:
            # SHIPPED -> PREVIEW
            if link.target_kind in ("SHAPE_KEYS", "BOTH") and mesh is not None:
                action = _ensure_shape_key_action(mesh, link)
                if action is not None:
                    deleted = engine.clear_auto_shape_key_keys(action, list(wiring.values()),
                        anim_data=mesh.data.shape_keys.animation_data)
                    self.report({"INFO"}, "Cleared " + str(deleted) + " auto-baked shape key keys")
                installed = de.install_drivers_for_link(link, mesh, wiring)
                self.report({"INFO"}, "PREVIEW: " + str(installed) + " driver(s) installed")
            link.mode = "PREVIEW"
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Manually install / remove drivers (for diagnostic use)
# ---------------------------------------------------------------------------

class AA_OT_p12_install_drivers(Operator):
    """Install PREVIEW drivers on the active lipsync layer's wired shape keys."""

    bl_idname = "animassist.p12_install_drivers"
    bl_label = "Install Lipsync Drivers"
    bl_options = {"REGISTER"}

    layer_name: StringProperty(default="")  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        link = _resolve_link(p12, self.layer_name)
        mesh = _resolve_mesh(link) if link else None
        wiring = _shape_key_wiring_dict(p12)
        if mesh is None or not wiring:
            self.report({"ERROR"}, "Need a wired mesh + shape_key_wiring to install drivers")
            return {"CANCELLED"}
        installed = de.install_drivers_for_link(link, mesh, wiring)
        self.report({"INFO"}, "Installed " + str(installed) + " driver(s)")
        return {"FINISHED"}


class AA_OT_p12_remove_drivers(Operator):
    """Remove PREVIEW drivers from the active lipsync layer's wired shape keys."""

    bl_idname = "animassist.p12_remove_drivers"
    bl_label = "Remove Lipsync Drivers"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):  # type: ignore[no-untyped-def]
        return confirm_dialog(self, context, event, "Remove the preview drivers from this layer's shape keys? The shape keys stop following the lipsync until drivers are rebuilt.")

    layer_name: StringProperty(default="")  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        link = _resolve_link(p12, self.layer_name)
        mesh = _resolve_mesh(link) if link else None
        wiring = _shape_key_wiring_dict(p12)
        if mesh is None or not wiring:
            self.report({"ERROR"}, "Need a wired mesh + shape_key_wiring to remove drivers")
            return {"CANCELLED"}
        removed = de.remove_drivers_for_link(mesh, wiring)
        self.report({"INFO"}, "Removed " + str(removed) + " driver(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Render-pre warning handler (Team D engineer dissent)
# ---------------------------------------------------------------------------

def render_pre_handler(scene, *args):
    """Warn if a render starts while any lipsync layer is in PREVIEW mode.

    Drivers don't always evaluate consistently across render engines and NLA
    blends, so production-final renders should use SHIPPED mode.
    """
    p12 = getattr(scene, "anim_assist_p12", None)
    if p12 is None or not p12.warn_on_render_in_preview:
        return
    in_preview = [link.layer_name for link in p12.layer_links if link.mode == "PREVIEW"]
    if in_preview:
        _log.warning(
            "Anim Assist: render started while %d lipsync layer(s) in PREVIEW mode (%s). "
            "Consider toggling to SHIPPED for render-final output.",
            len(in_preview),
            ", ".join(in_preview),
        )


def register_render_handlers():
    if render_pre_handler not in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.append(render_pre_handler)


def unregister_render_handlers():
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)


CLASSES: tuple[type, ...] = (
    AA_OT_p12_toggle_mode,
    AA_OT_p12_install_drivers,
    AA_OT_p12_remove_drivers,
)
