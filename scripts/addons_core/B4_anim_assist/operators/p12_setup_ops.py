# --- LIPSYNC SETUP OPERATORS (Phase 12) ---
"""One-click lipsync setup operators.

These operators handle the "premade setup" workflow: pick an audio file +
preset, get a Phase 11 override layer scoped to the face bones, an audio
strip in the sequencer, and a populated rig wiring entry — all from one
click. After this runs, the animator either runs ``Bake Lipsync`` or
hand-keys against the placed phoneme markers.

Operators kept small and orthogonal: setup creates the link + speaker;
viseme + audio operators live in their own files.
"""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

from .. import constants
from ..core import p12_audio_utils as au
from ..core import p12_properties as p12_props
from ..core import p12_viseme_library as vl
from ..core.logging import get_logger
from ..core.p11_properties import get_p11

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_armature(context: bpy.types.Context) -> bool:
    obj = context.active_object
    return obj is not None and obj.type == "ARMATURE"


def _ensure_face_bone_group(arm_obj: bpy.types.Object) -> set[str]:
    """Return the set of bone names already in the face_lipsync collection.

    On Bforartists / Blender 4.x the bone group concept lives under
    ``armature.collections``. We don't *create* a collection here — the
    setup operator only reports back what's there so the animator can
    confirm/adjust before running Bake.
    """
    armature = arm_obj.data
    collections = getattr(armature, "collections", None)
    if collections is None:
        return set()
    members: set[str] = set()
    for coll in collections:
        if coll.name == constants.P12_DEFAULT_FACE_GROUP:
            for bone in getattr(coll, "bones", ()):
                members.add(bone.name)
    return members


def _ensure_layer(p11, layer_name: str, scope_filter: str) -> object | None:
    """Return the AA_P11_AnimLayer with *layer_name*; create it if absent."""
    for layer in p11.layers:
        if layer.name == layer_name:
            return layer
    layer = p11.layers.add()
    layer.name = layer_name
    try:
        layer.layer_scope = "CUSTOM"
        layer.custom_filter = scope_filter
    except (AttributeError, TypeError):
        # Tolerate enum mismatches — leave defaults if scope schema differs.
        pass
    p11.active_layer_index = len(p11.layers) - 1
    return layer


def _ensure_speaker_strip(
    scene: bpy.types.Scene,
    audio_path: str,
    frame_offset: int,
) -> str:
    """Create a sound strip on the sequencer, return its name.

    Returns "" if the sequencer is unavailable or the file cannot be added.
    """
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    seq = scene.sequence_editor
    if seq is None:
        return ""
    # Find a free channel — search 1..32, take the first with no overlapping strip.
    used_channels = {s.channel for s in seq.sequences_all if s.frame_final_start <= frame_offset <= s.frame_final_end}
    channel = next((c for c in range(1, 33) if c not in used_channels), 1)
    name = f"AA_P12_{constants.P12_DEFAULT_FACE_GROUP}_{frame_offset}"
    try:
        # bpy 4.x uses sequences.new_sound; bforartists/older sequence_editor
        # may expose the same on .sequences.
        sequences = getattr(seq, "sequences", None) or seq
        strip = sequences.new_sound(
            name=name,
            filepath=audio_path,
            channel=channel,
            frame_start=frame_offset,
        )
    except (AttributeError, RuntimeError) as exc:
        _log.warning("Could not create sound strip: %s", exc)
        return ""
    return getattr(strip, "name", name)


def _seed_rig_wiring(p12, arm_obj: bpy.types.Object, library_id: str) -> int:
    """Pre-fill the rig wiring with best-guess bone names.

    Heuristic: for each role required by *library_id*, look for a bone whose
    name contains the role string (case-insensitive). Don't overwrite
    existing entries — the animator may have customised them.
    """
    required = vl.library_role_set(library_id)
    existing_roles = {entry.role for entry in p12.rig_wiring}
    bone_names = [b.name for b in arm_obj.data.bones]
    seeded = 0
    for role in sorted(required):
        if role in existing_roles:
            continue
        target = role.lower()
        match = next((b for b in bone_names if target in b.lower()), "")
        entry = p12.rig_wiring.add()
        entry.role = role
        entry.bone_name = match
        seeded += 1
    return seeded


# ---------------------------------------------------------------------------
# Setup Lipsync — the marquee operator
# ---------------------------------------------------------------------------

class AA_OT_p12_setup_lipsync(Operator):
    """Create a lipsync layer wired to an audio file in one step.

    Builds the AA_P11 override layer, drops the audio strip on the sequencer,
    and seeds rig wiring. After this finishes, run ``Bake Lipsync`` to write
    viseme keys, or pick "Markers Only" mode and hand-key against markers.
    """

    bl_idname = "animassist.p12_setup_lipsync"
    bl_label = "Setup Lipsync"
    bl_options = {"REGISTER", "UNDO"}

    audio_path: StringProperty(  # type: ignore[valid-type]
        name="Audio File",
        description="Path to the .wav file used for analysis",
        subtype="FILE_PATH",
        default="",
    )
    viseme_library: EnumProperty(  # type: ignore[valid-type]
        name="Viseme Library",
        description="Which viseme set drives the bake",
        items=p12_props._viseme_library_items,
    )
    setup_mode: EnumProperty(  # type: ignore[valid-type]
        name="Setup Mode",
        description="How the layer is populated when audio arrives",
        items=p12_props._setup_mode_items,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not _has_armature(context):
            return False
        return p12_props.get_p12(context) is not None

    def invoke(self, context, event):  # noqa: ARG002
        # Open a file picker if the audio path hasn't been set.
        if not self.audio_path:
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):  # noqa: ARG002
        layout = self.layout
        layout.prop(self, "audio_path")
        layout.prop(self, "viseme_library")
        layout.prop(self, "setup_mode")
        if self.audio_path and not au.is_supported_audio(self.audio_path):
            layout.label(
                text="Only .wav is supported in v11.0.0 — convert and re-pick.",
                icon="ERROR",
            )

    def execute(self, context):
        if not au.is_supported_audio(self.audio_path):
            self.report({"ERROR"}, "Lipsync v11.0.0 supports .wav only — convert the file first.")
            return {"CANCELLED"}

        p11 = get_p11(context)
        p12 = p12_props.get_p12(context)
        if p11 is None or p12 is None:
            self.report({"ERROR"}, "Layer and lipsync settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        arm_obj = context.active_object
        scene = context.scene
        layer_name = f"Lipsync_{arm_obj.name}"
        scope_filter = constants.P12_DEFAULT_FACE_GROUP
        layer = _ensure_layer(p11, layer_name, scope_filter)
        if layer is None:
            self.report({"ERROR"}, "Could not create the Phase 11 lipsync layer.")
            return {"CANCELLED"}

        face_bones = _ensure_face_bone_group(arm_obj)
        if not face_bones:
            self.report(
                {"WARNING"},
                f"No bones in the '{constants.P12_DEFAULT_FACE_GROUP}' collection — "
                "add the face bones to that collection before baking.",
            )

        # Sequencer strip.
        frame_offset = max(1, int(scene.frame_current))
        strip_name = _ensure_speaker_strip(scene, self.audio_path, frame_offset)

        # Rig wiring seed.
        seeded = _seed_rig_wiring(p12, arm_obj, self.viseme_library)

        # Layer link.
        link = p12_props.find_layer_link(p12, layer_name)
        if link is None:
            link = p12.layer_links.add()
            link.layer_name = layer_name
        link.armature_name = arm_obj.name
        link.audio_path = self.audio_path
        link.audio_sha256 = au.sha256_of_file(self.audio_path)
        link.speaker_strip_name = strip_name
        link.viseme_library = self.viseme_library
        link.backend = constants.P12_DEFAULT_BACKEND
        link.setup_mode = self.setup_mode
        link.frame_offset = frame_offset
        link.is_stale = False
        p12.active_link_index = len(p12.layer_links) - 1

        msg = f"Lipsync layer ready: {layer_name}"
        if seeded:
            msg += f" — seeded {seeded} rig roles"
        if not strip_name:
            msg += " (sequencer strip unavailable — bind manually)"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Refresh Audio Hash — recheck stale state without touching keys
# ---------------------------------------------------------------------------

class AA_OT_p12_refresh_audio_hash(Operator):
    """Recompute the audio file's SHA-256 and update the stale flag.

    Called by the panel automatically when drawn, and exposed as a button so
    the user can force a refresh after editing the audio externally.
    """

    bl_idname = "animassist.p12_refresh_audio_hash"
    bl_label = "Refresh Audio Hash"
    bl_options = {"REGISTER"}

    layer_name: StringProperty(  # type: ignore[valid-type]
        name="Layer Name",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        if p12 is None:
            return {"CANCELLED"}
        link = p12_props.find_layer_link(p12, self.layer_name)
        if link is None:
            self.report({"WARNING"}, f"No lipsync link for layer '{self.layer_name}'")
            return {"CANCELLED"}
        current = au.sha256_of_file(link.audio_path)
        if current and link.audio_sha256 and current != link.audio_sha256:
            link.is_stale = True
            self.report({"INFO"}, "Audio changed — rebake recommended")
        else:
            link.is_stale = False
            self.report({"INFO"}, "Audio is up to date")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p12_setup_lipsync,
    AA_OT_p12_refresh_audio_hash,
)
