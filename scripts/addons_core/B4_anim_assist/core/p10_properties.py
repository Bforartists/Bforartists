"""PropertyGroups for tool orchestration and advanced workflows.

This module defines all PropertyGroup classes for tool organization and orchestration, including:
- Favorite tool items
- Recent tool entries with timestamps
- Macro steps and macro entries
- Workspace profiles
- Main orchestration properties (shelf mode, batch processing, recovery, audit)

All EnumProperty items use callable functions for GC safety.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Context, PropertyGroup

__all__ = [
    "P10_SCENE_ATTR",
    "AA_P10_FavoriteItem",
    "AA_P10_RecentItem",
    "AA_P10_MacroStep",
    "AA_P10_MacroEntry",
    "AA_P10_WorkspaceProfile",
    "AA_P10_Properties",
    "CLASSES",
    "register_properties",
    "unregister_properties",
    "get_p10",
    "recents_newest_first",
    "sort_recents",
]

P10_SCENE_ATTR = "anim_assist_p10"


# ============================================================================
# Enum Item Getters (GC-safe)
# ============================================================================


def _get_shelf_mode_items(self, context):
    """Return shelf display mode options."""
    return [
        ("COMPACT", "Compact", "Show compact shelf view", 0),
        ("EXPANDED", "Expanded", "Show expanded shelf view", 1),
        ("FAVORITES", "Favorites", "Show only favorites", 2),
    ]


def _get_batch_mode_items(self, context):
    """Return batch processing mode options."""
    return [
        ("SELECTED", "Selected Objects", "Process selected objects", 0),
        ("BOOKMARKED", "Bookmarked Frames", "Process bookmarked frames", 1),
        ("FRAME_STEPS", "Frame Steps", "Process frames by step size", 2),
    ]


# ============================================================================
# PropertyGroup Classes
# ============================================================================


class AA_P10_FavoriteItem(PropertyGroup):  # type: ignore[valid-type]
    """A favorite tool entry."""

    op_id: StringProperty(  # type: ignore[valid-type]
        name="Operator ID",
        description="Operator bl_idname",
        default="",
    )

    label: StringProperty(  # type: ignore[valid-type]
        name="Label",
        description="Display name for the favorite",
        default="",
    )

    icon: StringProperty(  # type: ignore[valid-type]
        name="Icon",
        description="Blender icon identifier",
        default="NONE",
    )


class AA_P10_RecentItem(PropertyGroup):  # type: ignore[valid-type]
    """A recent tool entry with timestamp."""

    op_id: StringProperty(  # type: ignore[valid-type]
        name="Operator ID",
        description="Operator bl_idname",
        default="",
    )

    label: StringProperty(  # type: ignore[valid-type]
        name="Label",
        description="Display name for the recent item",
        default="",
    )

    timestamp: FloatProperty(  # type: ignore[valid-type]
        name="Timestamp",
        description="Time when this item was last used (time.time())",
        default=0.0,
    )


class AA_P10_MacroStep(PropertyGroup):  # type: ignore[valid-type]
    """One step in a macro sequence."""

    op_id: StringProperty(  # type: ignore[valid-type]
        name="Operator ID",
        description="Operator bl_idname",
        default="",
    )

    label: StringProperty(  # type: ignore[valid-type]
        name="Label",
        description="Display name for the step",
        default="",
    )

    enabled: BoolProperty(  # type: ignore[valid-type]
        name="Enabled",
        description="Whether this step is executed",
        default=True,
    )


class AA_P10_MacroEntry(PropertyGroup):  # type: ignore[valid-type]
    """A saved macro with multiple steps."""

    name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="Macro name",
        default="Untitled Macro",
    )

    steps: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P10_MacroStep,
        name="Steps",
        description="Macro steps",
    )

    description: StringProperty(  # type: ignore[valid-type]
        name="Description",
        description="Macro description",
        default="",
    )

    icon: StringProperty(  # type: ignore[valid-type]
        name="Icon",
        description="Blender icon identifier",
        default="SEQUENCE",
    )


class AA_P10_WorkspaceProfile(PropertyGroup):  # type: ignore[valid-type]
    """A named workspace configuration profile."""

    name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="Profile name",
        default="Untitled Profile",
    )

    data_json: StringProperty(  # type: ignore[valid-type]
        name="Data JSON",
        description="Serialized profile settings as JSON",
        default="",
    )


class AA_P10_Properties(PropertyGroup):  # type: ignore[valid-type]
    """Main PropertyGroup for orchestration and macro features."""

    # ========================================================================
    # Shelf Properties
    # ========================================================================

    first_run_complete: BoolProperty(  # type: ignore[valid-type]
        name="First Run Complete",
        description="Whether the initial Anim Assist setup has completed",
        default=False,
        options={'HIDDEN'},
    )

    shelf_mode: EnumProperty(  # type: ignore[valid-type]
        name="Shelf Mode",
        description="Display mode for the tool shelf",
        items=_get_shelf_mode_items,
    )

    shelf_filter_phase: IntProperty(  # type: ignore[valid-type]
        name="Tool Group",
        description="Show only tools from one group on the shelf (0 shows all groups)",
        default=0,
        min=0,
        max=10,
    )

    shelf_search_query: StringProperty(  # type: ignore[valid-type]
        name="Shelf Search Query",
        description="Current search query for shelf filtering",
        default="",
    )

    # ========================================================================
    # Favorites
    # ========================================================================

    favorites: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P10_FavoriteItem,
        name="Favorites",
        description="Favorite tool entries",
    )

    active_favorite_index: IntProperty(  # type: ignore[valid-type]
        name="Active Favorite Index",
        description="Index of the active favorite",
        default=0,
        min=0,
    )

    # ========================================================================
    # Recents
    # ========================================================================

    recents: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P10_RecentItem,
        name="Recents",
        description="Recently used tool entries",
    )

    max_recents: IntProperty(  # type: ignore[valid-type]
        name="Max Recents",
        description="Maximum number of recent items to store",
        default=20,
        min=5,
        max=50,
    )

    # ========================================================================
    # Macros
    # ========================================================================

    macros: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P10_MacroEntry,
        name="Macros",
        description="Saved macro entries",
    )

    active_macro_index: IntProperty(  # type: ignore[valid-type]
        name="Active Macro Index",
        description="Index of the active macro",
        default=0,
        min=0,
    )

    # ========================================================================
    # Profiles
    # ========================================================================

    profiles: CollectionProperty(  # type: ignore[valid-type]
        type=AA_P10_WorkspaceProfile,
        name="Profiles",
        description="Workspace configuration profiles",
    )

    active_profile_index: IntProperty(  # type: ignore[valid-type]
        name="Active Profile Index",
        description="Index of the active profile",
        default=0,
        min=0,
    )

    # ========================================================================
    # Recovery Settings
    # ========================================================================

    recovery_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Recovery Enabled",
        description="Enable automatic state recovery",
        default=True,
    )

    max_snapshots: IntProperty(  # type: ignore[valid-type]
        name="Max Snapshots",
        description="Maximum number of recovery snapshots to store",
        default=10,
        min=1,
        max=50,
    )

    # ========================================================================
    # Audit Settings
    # ========================================================================

    audit_enabled: BoolProperty(  # type: ignore[valid-type]
        name="Audit Enabled",
        description="Enable operation audit logging",
        default=True,
    )

    max_audit_entries: IntProperty(  # type: ignore[valid-type]
        name="Max Audit Entries",
        description="Maximum number of audit entries to store",
        default=100,
        min=10,
        max=500,
    )

    # ========================================================================
    # Debug Settings
    # ========================================================================

    show_debug_panel: BoolProperty(  # type: ignore[valid-type]
        name="Show Debug Panel",
        description="Show debug information panel",
        default=False,
    )

    # ========================================================================
    # Batch Processing Settings
    # ========================================================================

    batch_mode: EnumProperty(  # type: ignore[valid-type]
        name="Batch Mode",
        description="Batch processing mode",
        items=_get_batch_mode_items,
    )

    batch_frame_step: IntProperty(  # type: ignore[valid-type]
        name="Batch Frame Step",
        description="Frame step size for batch processing",
        default=1,
        min=1,
        max=100,
    )

    batch_frame_start: IntProperty(  # type: ignore[valid-type]
        name="Batch Frame Start",
        description="Starting frame for batch processing",
        default=1,
    )

    batch_frame_end: IntProperty(  # type: ignore[valid-type]
        name="Batch Frame End",
        description="Ending frame for batch processing",
        default=250,
    )


# ============================================================================
# Registration
# ============================================================================

CLASSES = (
    AA_P10_FavoriteItem,
    AA_P10_RecentItem,
    AA_P10_MacroStep,
    AA_P10_MacroEntry,
    AA_P10_WorkspaceProfile,
    AA_P10_Properties,
)


def register_properties() -> None:
    """Attach the orchestration PointerProperty to Scene.

    Note: PropertyGroup class registration is handled by the ClassRegistry
    via the CLASSES tuple in operators/__init__.py.  This function only
    attaches the scene-level PointerProperty.
    """
    bpy.types.Scene.anim_assist_p10 = PointerProperty(  # type: ignore[attr-defined]
        type=AA_P10_Properties,
        name="Anim Assist Orchestration",
    )


def unregister_properties() -> None:
    """Detach the orchestration PointerProperty from Scene.

    Note: PropertyGroup class unregistration is handled by the ClassRegistry.
    """
    if hasattr(bpy.types.Scene, P10_SCENE_ATTR):
        delattr(bpy.types.Scene, P10_SCENE_ATTR)


# ============================================================================
# Accessor
# ============================================================================


def get_p10(context: Context) -> AA_P10_Properties | None:
    """Get the orchestration PropertyGroup from the current scene.

    Args:
        context: Blender context.

    Returns:
        The AA_P10_Properties instance, or None if not available.
    """
    if not hasattr(context.scene, P10_SCENE_ATTR):
        return None
    return getattr(context.scene, P10_SCENE_ATTR)


def recents_newest_first(p10: AA_P10_Properties) -> list:
    """Recent entries, newest first.

    Files saved by 12.1.0 and earlier stored Recents oldest-first; the
    timestamp, not the collection order, is the authority.
    """
    return sorted(p10.recents, key=lambda item: item.timestamp, reverse=True)


def sort_recents(p10: AA_P10_Properties) -> None:
    """Reorder the stored collection newest-first (requires writable data)."""
    recents = p10.recents
    for target in range(len(recents)):
        newest = max(range(target, len(recents)), key=lambda i: recents[i].timestamp)
        if recents[newest].timestamp > recents[target].timestamp:
            recents.move(newest, target)
