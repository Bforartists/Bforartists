"""Blender property groups attached to Scene, WindowManager, and Object."""

from __future__ import annotations

import json

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from .. import constants
from .logging import get_logger

__all__ = [
    "AA_BoneMetadataItem",
    "AA_ObjectMetadata",
    "AA_BookmarkItem",
    "AA_KeyMetaItem",
    "AA_MaskSettings",
    "AA_SceneProperties",
    "AA_WindowManagerProperties",
    "CLASSES",
    "get_object_metadata",
    "set_object_metadata",
    "register_properties",
    "unregister_properties",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Property groups
# ---------------------------------------------------------------------------

class AA_BoneMetadataItem(bpy.types.PropertyGroup):
    """One record of tool metadata keyed by object + bone name."""

    object_name: StringProperty(name="Object", description="Object associated with this metadata record", default="")  # type: ignore[valid-type]
    bone_name: StringProperty(name="Bone", description="Bone associated with this metadata record", default="")  # type: ignore[valid-type]
    metadata_json: StringProperty(name="Data", default="{}")  # type: ignore[valid-type]


class AA_ObjectMetadata(bpy.types.PropertyGroup):
    """Per-object tool metadata stored on the object."""

    tool_state_json: StringProperty(name="Tool State", default="{}")  # type: ignore[valid-type]
    last_tool: StringProperty(name="Last Tool", default="")  # type: ignore[valid-type]
    flags: IntProperty(name="Flags", default=0)  # type: ignore[valid-type]


class AA_BookmarkItem(bpy.types.PropertyGroup):
    """A named frame bookmark stored on the scene."""

    name: StringProperty(name="Name", description="Display name of the frame bookmark", default="Bookmark")  # type: ignore[valid-type]
    frame: IntProperty(name="Frame", default=1)  # type: ignore[valid-type]


class AA_KeyMetaItem(bpy.types.PropertyGroup):
    """Per-keyframe metadata record for diagnostics and key management.

    Indexed by ``(object_name, data_path, array_index, frame)``. Stored on
    the scene so it persists with the .blend.
    """

    object_name: StringProperty(name="Object", description="Object whose animation this record belongs to", default="")  # type: ignore[valid-type]
    data_path: StringProperty(name="Data Path", default="")  # type: ignore[valid-type]
    array_index: IntProperty(name="Array Index", default=0)  # type: ignore[valid-type]
    frame: FloatProperty(name="Frame", default=0.0)  # type: ignore[valid-type]

    tag: StringProperty(name="Tag", default="")  # type: ignore[valid-type]
    note: StringProperty(name="Note", default="")  # type: ignore[valid-type]
    protected: BoolProperty(name="Protected", default=False)  # type: ignore[valid-type]
    flavor: StringProperty(name="Flavor", default="")  # type: ignore[valid-type]


class AA_MaskSettings(bpy.types.PropertyGroup):
    """Anim Offset mask / blend region settings."""

    enabled: BoolProperty(name="Use Mask", description="Limit Anim Offset propagation to the masked frame range", default=True)  # type: ignore[valid-type]
    start_frame: IntProperty(name="Start", description="First frame of the Anim Offset mask", default=1)  # type: ignore[valid-type]
    end_frame: IntProperty(name="End", description="Last frame of the Anim Offset mask", default=250)  # type: ignore[valid-type]
    blend_left: IntProperty(  # type: ignore[valid-type]
        name="Blend In",
        description="Blend-in frames on the left edge of the mask",
        default=5,
        min=0,
    )
    blend_right: IntProperty(  # type: ignore[valid-type]
        name="Blend Out",
        description="Blend-out frames on the right edge of the mask",
        default=5,
        min=0,
    )


class AA_SceneProperties(bpy.types.PropertyGroup):
    """Scene-level data persisted in the .blend file."""

    migration_version: IntProperty(name="Migration Version", default=0)  # type: ignore[valid-type]
    bone_metadata: CollectionProperty(type=AA_BoneMetadataItem)  # type: ignore[valid-type]

    # Anim Offset tool state
    anim_offset_active: BoolProperty(  # type: ignore[valid-type]
        name="Anim Offset Active",
        description="Whether the Anim Offset modal operator is currently running",
        default=False,
    )
    mask: PointerProperty(type=AA_MaskSettings)  # type: ignore[valid-type]

    # Curve tool / blend frame state
    reference_frame: IntProperty(  # type: ignore[valid-type]
        name="Reference Frame",
        description="Frame used as blend target by Blend Frame and Push/Pull operators",
        default=0,
    )
    bookmarks: CollectionProperty(type=AA_BookmarkItem)  # type: ignore[valid-type]
    active_bookmark_index: IntProperty(  # type: ignore[valid-type]
        name="Active Bookmark",
        default=0,
        min=0,
    )

    # Per-keyframe metadata store for diagnostics and key management.
    key_metadata: CollectionProperty(type=AA_KeyMetaItem)  # type: ignore[valid-type]

    # UI state
    panel_compact: BoolProperty(  # type: ignore[valid-type]
        name="Compact Panel",
        description="Show Curve Tools as a single compact column instead of sub-panels",
        default=False,
    )

    # Header toolbar category visibility toggles.
    # Each controls whether a toolbar group is drawn in the editor header.
    header_show_breakdown: BoolProperty(  # type: ignore[valid-type]
        name="Breakdown",
        description="Show breakdown percentage and drag buttons in the header toolbar",
        default=True,
    )
    header_show_pushpull: BoolProperty(  # type: ignore[valid-type]
        name="Push/Pull",
        description="Show push/pull directional buttons in the header toolbar",
        default=True,
    )
    header_show_retime: BoolProperty(  # type: ignore[valid-type]
        name="Retime",
        description="Show retime speed-scaling presets in the header toolbar",
        default=True,
    )
    header_show_selection: BoolProperty(  # type: ignore[valid-type]
        name="Selection",
        description="Show key selection shortcuts in the Dope Sheet header toolbar",
        default=True,
    )
    header_show_trajectory: BoolProperty(  # type: ignore[valid-type]
        name="Trajectory",
        description="Show trajectory overlay toggles in the 3D Viewport header toolbar",
        default=True,
    )
    header_show_matching: BoolProperty(  # type: ignore[valid-type]
        name="Matching",
        description="Show quick-match buttons (W/P/V) in the 3D Viewport header toolbar",
        default=True,
    )


class AA_WindowManagerProperties(bpy.types.PropertyGroup):
    """Window-manager-scoped addon state (session/UI scope).

    For truly transient non-RNA runtime state use ``core.runtime`` and
    ``core.cache`` instead.
    """

    is_tool_active: BoolProperty(name="Tool Active", default=False)  # type: ignore[valid-type]
    active_tool_name: StringProperty(name="Active Tool", default="")  # type: ignore[valid-type]
    last_operator_time: FloatProperty(name="Op Time", default=0.0)  # type: ignore[valid-type]


# ---------------------------------------------------------------------------
# Metadata accessors
# ---------------------------------------------------------------------------

def get_object_metadata(obj: bpy.types.Object | None) -> dict:
    """Return deserialised tool-state dict for *obj*, or empty dict."""
    if obj is None:
        return {}
    meta = getattr(obj, constants.OBJECT_META_ATTR, None)
    if meta is None:
        return {}
    try:
        return json.loads(meta.tool_state_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def set_object_metadata(
    obj: bpy.types.Object | None,
    data: dict,
    last_tool: str = "",
) -> bool:
    """Serialise *data* into the object's tool-state property.

    Returns ``True`` on success.
    """
    if obj is None:
        return False

    if not isinstance(data, dict):
        _log.warning("Object metadata must be a dict, got %s", type(data).__name__)
        return False

    if obj.library is not None and obj.override_library is None:
        _log.debug("Skipping metadata write for linked object '%s'", obj.name)
        return False

    meta = getattr(obj, constants.OBJECT_META_ATTR, None)
    if meta is None:
        return False

    meta.tool_state_json = json.dumps(data, ensure_ascii=False)
    if last_tool:
        meta.last_tool = last_tool
    return True


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

# Order matters: items must be registered before collections/pointers that
# reference them.
CLASSES: tuple[type, ...] = (
    AA_BoneMetadataItem,
    AA_BookmarkItem,
    AA_KeyMetaItem,
    AA_MaskSettings,
    AA_ObjectMetadata,
    AA_SceneProperties,
    AA_WindowManagerProperties,
)


def register_properties() -> None:
    """Attach PointerProperty attributes to Blender types (idempotent)."""
    if not hasattr(bpy.types.Scene, constants.SCENE_PROP_ATTR):
        setattr(
            bpy.types.Scene,
            constants.SCENE_PROP_ATTR,
            PointerProperty(type=AA_SceneProperties),
        )
    if not hasattr(bpy.types.WindowManager, constants.WM_PROP_ATTR):
        setattr(
            bpy.types.WindowManager,
            constants.WM_PROP_ATTR,
            PointerProperty(type=AA_WindowManagerProperties),
        )
    if not hasattr(bpy.types.Object, constants.OBJECT_META_ATTR):
        setattr(
            bpy.types.Object,
            constants.OBJECT_META_ATTR,
            PointerProperty(type=AA_ObjectMetadata),
        )


def unregister_properties() -> None:
    """Detach PropertyGroups from Scene/WindowManager/Object to avoid Blender RNA dangling-pointer crashes."""
    for attr, owner in (
        (constants.OBJECT_META_ATTR, bpy.types.Object),
        (constants.WM_PROP_ATTR, bpy.types.WindowManager),
        (constants.SCENE_PROP_ATTR, bpy.types.Scene),
    ):
        try:
            delattr(owner, attr)
        except AttributeError:
            pass
