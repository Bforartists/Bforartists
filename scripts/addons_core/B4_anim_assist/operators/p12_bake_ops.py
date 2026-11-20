# --- LIPSYNC BAKE OPERATORS (Phase 12 / v12.0.0) ---
"""Bake / clear / rebake operators - now route by link.target_kind.

v12 changes
-----------
- Bake always writes the cue table to the link (used by both PREVIEW drivers
  and SHIPPED bake).
- Dispatches to bone bake, shape key bake, or both based on link.target_kind.
- Mode-aware: in PREVIEW the bake only updates the cue table; in SHIPPED it
  also writes fcurves.
"""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..core import p12_audio_utils as au
from ..core import p12_cue_table as ct
from ..core import p12_driver_engine as de
from ..core import p12_lipsync_engine as engine
from ..core import p12_properties as p12_props
from ..core import p12_session as session
from ..core.logging import get_logger
from ..core.p11_properties import get_p11
from ..core.helpers import report_failure
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_layer(p11, layer_name):
    if p11 is None:
        return None
    for layer in p11.layers:
        if layer.name == layer_name:
            return layer
    return None


def _resolve_action(scene, armature_name, layer):
    arm_obj = bpy.data.objects.get(armature_name)
    if arm_obj is None:
        return None
    if getattr(layer, "is_base_layer", False):
        if arm_obj.animation_data is None:
            return None
        return arm_obj.animation_data.action
    action_name = getattr(layer, "action_name", "")
    if not action_name:
        action = bpy.data.actions.new(name="AA_P12_" + layer.name)
        layer.action_name = action.name
        return action
    return bpy.data.actions.get(action_name)


def _resolve_shape_key_action(mesh_name, link):
    mesh_obj = bpy.data.objects.get(mesh_name) if mesh_name else None
    if mesh_obj is None or mesh_obj.type != "MESH":
        return None
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


def _bone_wiring(p12):
    return {entry.role: entry.bone_name for entry in p12.rig_wiring if entry.bone_name}


def _shape_key_wiring(p12):
    return {entry.viseme_name: entry.shape_key_name for entry in p12.shape_key_wiring if entry.shape_key_name}


def _user_pose_overrides(p12):
    return [(e.viseme_name, e.pose_json) for e in p12.viseme_poses]


def _resolve_link(p12, layer_name):
    link = p12_props.find_layer_link(p12, layer_name) if layer_name else None
    if link is None and p12.layer_links and 0 <= p12.active_link_index < len(p12.layer_links):
        link = p12.layer_links[p12.active_link_index]
    return link


# ---------------------------------------------------------------------------
# Bake
# ---------------------------------------------------------------------------

class AA_OT_p12_bake_lipsync(Operator):
    """Run audio analysis, write the cue table, and bake fcurves per link.target_kind.

    In PREVIEW mode only the cue table is written - drivers do the rest.
    In SHIPPED mode the cue table is also baked into shape key/bone fcurves.
    Manual override sanctuary applies to all bake paths.
    """

    bl_idname = "animassist.p12_bake_lipsync"
    bl_label = "Bake Lipsync"
    bl_options = {"REGISTER", "UNDO"}

    layer_name: StringProperty(default="")  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context):
        if p12_props.get_p12(context) is None or get_p11(context) is None:
            cls.poll_message_set("Enable Anim Assist's lipsync and animation-layer settings for this scene")
            return False
        return True

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        p11 = get_p11(context)
        link = _resolve_link(p12, self.layer_name)
        if link is None:
            self.report({"ERROR"}, "No lipsync layer link to bake. Add one in the Lipsync panel first")
            return {"CANCELLED"}

        if not au.is_supported_audio(link.audio_path):
            self.report({"ERROR"}, "The bound audio is not a .wav file. Bind a .wav file in the Lipsync panel")
            return {"CANCELLED"}

        # Refresh hash + run analysis through the cache.
        link.audio_sha256 = au.sha256_of_file(link.audio_path)
        analyze_result = session.get_analyze(
            link.audio_path,
            link.audio_sha256,
            link.backend,
            rhubarb_path=p12.rhubarb_path,
        )
        if analyze_result.fallback_used:
            self.report({"WARNING"}, "Backend fallback: " + analyze_result.fallback_reason)

        # ALWAYS write the cue table - both PREVIEW and SHIPPED read from it.
        cues = [ct.Cue(time_seconds=c.time_seconds, viseme_name=c.viseme_name)
                for c in analyze_result.cues]
        ct.write_cues_to_link(link, cues)

        fps = context.scene.render.fps / max(1, context.scene.render.fps_base)
        total_written = 0
        total_skipped = 0
        notes = []

        # Bones path
        if link.target_kind in ("BONES", "BOTH"):
            layer = _resolve_layer(p11, link.layer_name)
            if layer is None:
                notes.append("layer not found - bone bake skipped")
            else:
                action = _resolve_action(context.scene, link.armature_name, layer)
                arm = bpy.data.objects.get(link.armature_name)
                rig_wiring = _bone_wiring(p12)
                if action is None or arm is None:
                    notes.append("armature/action missing - bone bake skipped")
                elif not rig_wiring:
                    notes.append("rig_wiring empty - bone bake skipped")
                else:
                    request = engine.BakeRequest(
                        armature=arm, action=action, cues=analyze_result.cues,
                        library_id=link.viseme_library,
                        user_pose_overrides=_user_pose_overrides(p12),
                        rig_wiring=rig_wiring, fps=fps,
                        frame_offset=link.frame_offset,
                        anticipation_frames=link.anticipation_frames,
                    )
                    report = engine.bake_lipsync(request)
                    total_written += report.keys_written
                    total_skipped += report.keys_skipped_manual
                    notes.append("bones: " + str(report.keys_written) + "k/" + str(report.bones_touched) + "b")

        # Shape keys path
        if link.target_kind in ("SHAPE_KEYS", "BOTH"):
            sk_wiring = _shape_key_wiring(p12)
            sk_action = _resolve_shape_key_action(link.mesh_name, link)
            if sk_action is None:
                notes.append("mesh/shape-keys missing - shape key bake skipped")
            elif not sk_wiring:
                notes.append("shape_key_wiring empty - shape key bake skipped")
            elif link.mode == "SHIPPED":
                # SHIPPED: write fcurves
                report = engine.bake_shape_keys(
                    action=sk_action,
                    cues=analyze_result.cues,
                    shape_key_wiring=sk_wiring,
                    fps=fps,
                    frame_offset=link.frame_offset,
                    anticipation_frames=link.anticipation_frames,
                    anim_data=bpy.data.objects[link.mesh_name].data.shape_keys.animation_data,
                )
                total_written += report.keys_written
                total_skipped += report.keys_skipped_manual
                notes.append("shape keys: " + str(report.keys_written) + "k/" + str(report.bones_touched) + "sk")
            else:
                # PREVIEW: ensure drivers are installed & read from the new cue table.
                mesh = bpy.data.objects.get(link.mesh_name)
                if mesh is not None:
                    de.install_drivers_for_link(link, mesh, sk_wiring)
                    notes.append("shape keys: drivers refreshed (PREVIEW)")

        link.last_baked_start = link.frame_offset
        link.last_baked_end = link.frame_offset + int(round(
            (analyze_result.cues[-1].time_seconds if analyze_result.cues else 0.0) * fps
        ))
        link.is_stale = False

        session.record_bake(
            link.layer_name,
            session.BakeRecord(
                keys_written=total_written, keys_skipped=total_skipped,
                bones_touched=0, cue_count=len(analyze_result.cues),
                backend=analyze_result.backend,
                fallback_used=analyze_result.fallback_used,
                fallback_reason=analyze_result.fallback_reason,
                range_start=link.last_baked_start, range_end=link.last_baked_end,
            ),
        )

        msg = "Bake [" + link.mode + "/" + link.target_kind + "]: " + str(total_written) + " keys, "
        msg += str(total_skipped) + " preserved manual (" + analyze_result.backend + ")"
        if notes:
            msg += " - " + "; ".join(notes)
        self.report({"INFO"}, msg)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Clear auto keys (both bone + shape key paths)
# ---------------------------------------------------------------------------

class AA_OT_p12_clear_auto_keys(Operator):
    """Remove auto-generated lipsync keys for the active link; preserve manual edits."""

    bl_idname = "animassist.p12_clear_auto_keys"
    bl_label = "Clear Auto Keys"
    bl_options = {"REGISTER", "UNDO"}

    layer_name: StringProperty(default="")  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None and get_p11(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        p11 = get_p11(context)
        link = _resolve_link(p12, self.layer_name)
        if link is None:
            self.report({"ERROR"}, "No lipsync layer link selected. Select one in the Lipsync panel list first")
            return {"CANCELLED"}

        total_deleted = 0

        if link.target_kind in ("BONES", "BOTH"):
            layer = _resolve_layer(p11, link.layer_name)
            action = _resolve_action(context.scene, link.armature_name, layer) if layer else None
            bone_names = [e.bone_name for e in p12.rig_wiring if e.bone_name]
            if action is not None and bone_names:
                arm = bpy.data.objects.get(link.armature_name)
                anim_data = engine.action_context(action, owner=arm, create=False)
                if anim_data is not None:
                    total_deleted += engine.clear_auto_keys(action, bone_names, anim_data=anim_data)

        if link.target_kind in ("SHAPE_KEYS", "BOTH"):
            sk_action = _resolve_shape_key_action(link.mesh_name, link)
            sk_names = [e.shape_key_name for e in p12.shape_key_wiring if e.shape_key_name]
            if sk_action is not None and sk_names:
                total_deleted += engine.clear_auto_shape_key_keys(sk_action, sk_names,
                    anim_data=bpy.data.objects[link.mesh_name].data.shape_keys.animation_data)

        self.report({"INFO"}, "Cleared " + str(total_deleted) + " auto-baked keys (manual preserved)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Rebake convenience
# ---------------------------------------------------------------------------

class AA_OT_p12_rebake(Operator):
    """Clear auto keys then bake again - manual edits survive both steps."""

    bl_idname = "animassist.p12_rebake"
    bl_label = "Rebake Lipsync"
    bl_options = {"REGISTER", "UNDO"}

    layer_name: StringProperty(default="")  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None and get_p11(context) is not None

    def execute(self, context):
        try:
            bpy.ops.animassist.p12_clear_auto_keys(layer_name=self.layer_name)
            bpy.ops.animassist.p12_bake_lipsync(layer_name=self.layer_name)
        except RuntimeError as exc:
            return report_failure(self, "Rebake did not finish", "Check the bound .wav file and the layer link, then rebake", exc)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Mark Selected as Manual Override (extends to shape keys per unanimous addition)
# ---------------------------------------------------------------------------

class AA_OT_p12_mark_manual(Operator):
    """Flag the selected keyframes (bones AND shape keys) as manual overrides."""

    bl_idname = "animassist.p12_mark_manual"
    bl_label = "Mark as Manual Override"
    bl_options = {"REGISTER", "UNDO"}

    layer_name: StringProperty(default="")  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context):
        return p12_props.get_p12(context) is not None and get_p11(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        p11 = get_p11(context)
        link = _resolve_link(p12, self.layer_name)
        if link is None:
            self.report({"ERROR"}, "No lipsync layer link selected. Select one in the Lipsync panel list first")
            return {"CANCELLED"}
        marked = 0

        # Bones
        if link.target_kind in ("BONES", "BOTH"):
            layer = _resolve_layer(p11, link.layer_name)
            action = _resolve_action(context.scene, link.armature_name, layer) if layer else None
            bone_names = [e.bone_name for e in p12.rig_wiring if e.bone_name]
            if action is not None:
                arm = bpy.data.objects.get(link.armature_name)
                anim_data = engine.action_context(action, owner=arm, create=False)
                for fc in (get_fcurves(action, anim_data=anim_data) if anim_data is not None else ()):
                    data_path = getattr(fc, "data_path", "")
                    if not any('pose.bones["' + n + '"]' in data_path for n in bone_names):
                        continue
                    for i, point in enumerate(getattr(fc, "keyframe_points", ())):
                        if not getattr(point, "select_control_point", False):
                            continue
                        engine.mark_manual_override(action, data_path, fc.array_index, i, anim_data=anim_data)
                        marked += 1

        # Shape keys
        if link.target_kind in ("SHAPE_KEYS", "BOTH"):
            sk_action = _resolve_shape_key_action(link.mesh_name, link)
            sk_names = [e.shape_key_name for e in p12.shape_key_wiring if e.shape_key_name]
            if sk_action is not None:
                anim_data = bpy.data.objects[link.mesh_name].data.shape_keys.animation_data
                for fc in get_fcurves(sk_action, anim_data=anim_data):
                    data_path = getattr(fc, "data_path", "")
                    if not any('key_blocks["' + n + '"]' in data_path for n in sk_names):
                        continue
                    for i, point in enumerate(getattr(fc, "keyframe_points", ())):
                        if not getattr(point, "select_control_point", False):
                            continue
                        engine.mark_manual_override(sk_action, data_path, 0, i, anim_data=anim_data)
                        marked += 1

        self.report({"INFO"}, "Marked " + str(marked) + " keyframe(s) as manual override")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p12_bake_lipsync,
    AA_OT_p12_clear_auto_keys,
    AA_OT_p12_rebake,
    AA_OT_p12_mark_manual,
)
