"""Addon-wide constants and configuration."""

from __future__ import annotations

ADDON_PACKAGE: str = "anim_assist"

ADDON_VERSION: tuple[int, int, int] = (12, 11, 2)
ADDON_VERSION_STRING: str = "12.11.2"

BREAKDOWN_ANCHOR_HINT: str = (
    "An existing key at the playhead becomes the previous anchor; "
    "an empty frame blends between the surrounding keys."
)

SCENE_PROP_ATTR: str = "anim_assist"
WM_PROP_ATTR: str = "anim_assist_wm"
OBJECT_META_ATTR: str = "anim_assist_meta"

MODULE_KEYS: tuple[str, ...] = (
    "selection", "keys", "transform", "breakdown", "trajectory",
    "retime", "controls", "matching", "orchestration", "layers", "lipsync",
)

MIGRATION_CURRENT_VERSION: int = 3

HELP_ICON: str = "QUESTION"
HELP_POPUP_WIDTH: int = 400
HELP_DEFAULT_CATEGORY: str = "General"

UI_STATE_ATTR: str = "anim_assist_ui"
ANIMASSIST_CATEGORY: str = "Anim Assist"

P7_TAG_TEMP: str = "anim_assist_temp"
P7_TAG_SESSION_ID: str = "anim_assist_session_id"
P7_TAG_ARTIFACT_ROLE: str = "anim_assist_artifact_role"
P7_TAG_OWNER_OBJ: str = "anim_assist_owner_obj"
P7_CONSTRAINT_PREFIX: str = "AA_P7_"
P7_SCENE_SESSION_KEY: str = "anim_assist_p7_session"
P7_TEMP_COLLECTION_TEMPLATE: str = "AA_P7_Temp_{short_id}"

# --- LIPSYNC LAYER (Phase 12) ---
P12_SCENE_ATTR: str = "anim_assist_p12"
P12_KEY_MANUAL_OVERRIDE_KEY: str = "aa_p12_manual"
P12_KEY_AUTO_BAKED_KEY: str = "aa_p12_auto"
P12_DEFAULT_BACKEND: str = "AMPLITUDE"
P12_DEFAULT_FACE_GROUP: str = "face_lipsync"
P12_STALE_SUFFIX: str = " WARN"
