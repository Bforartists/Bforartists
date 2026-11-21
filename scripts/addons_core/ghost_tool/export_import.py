"""
export_import.py — JSON export and import of ghost configurations.

Serializes and deserializes the entire Ghost Tool state (ghosts, snapshots,
addon version) to a JSON file.  This enables:
- Persistence across Blender sessions
- Transferring timing references between shots
- Sharing ghost configurations between artists
"""

from __future__ import annotations

import json
import tempfile
import os
from typing import Optional

import bpy

from .ghost_data import GhostStore, Ghost
from .snapshot import SnapshotStore
from .utils import log, warn, debug, tag_viewport_redraw


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPORT_VERSION: str = "2.0.0"
"""File format version for compatibility checking."""

COMPATIBLE_VERSIONS: set[str] = {"1.0.0", "1.1.0", "2.0.0"}
"""Set of file format versions that this module can read."""

_REQUIRED_GHOST_FIELDS = {"frame", "world_position", "local_value", "channel", "object_name"}
"""Fields that must be present in every ghost dictionary for validity."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_ghost_data(ghost_dict: dict) -> tuple[bool, str]:
    """Validate a ghost dictionary has required fields. Returns (valid, error_msg)."""
    if not isinstance(ghost_dict, dict):
        return False, "Ghost entry is not a dictionary"
    missing = _REQUIRED_GHOST_FIELDS - set(ghost_dict.keys())
    if missing:
        return False, f"Missing required fields: {missing}"
    if not isinstance(ghost_dict.get("world_position"), (list, tuple)) or len(ghost_dict["world_position"]) != 3:
        return False, "world_position must be a 3-element list"
    return True, ""


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_ghosts(filepath: str, scene: bpy.types.Scene) -> bool:
    """Export the current ghost configuration and snapshots to a JSON file.

    The exported file includes:
    - Addon and format version for compatibility checking
    - All ghost positions, levels, pins, and parent keyframes
    - All snapshot data
    - Scene name for reference

    Args:
        filepath: Absolute path for the output JSON file.
        scene: The Blender scene to export from.

    Returns:
        bool: True if export succeeded, False otherwise.
    """
    try:
        ghost_store = GhostStore.get(scene)
        snapshot_store = SnapshotStore.get(scene)

        # Build export data structure with version and content
        export_data = {
            "version": EXPORT_VERSION,  # File format version for compatibility checks
            "scene_name": scene.name,   # Scene name for reference/documentation
            "ghost_count": len(ghost_store),  # Number of ghosts being exported
            "ghosts": ghost_store.to_dict_list(),  # Serialized ghost configuration
            "snapshots": snapshot_store.to_dict_list(),  # All stored snapshots
        }

        # Ensure the output directory exists (create if needed)
        output_dir = os.path.dirname(filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        payload = json.dumps(export_data, indent=2, ensure_ascii=False, allow_nan=False)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=output_dir or '.', prefix='.ghost-export-', suffix='.tmp', delete=False) as output:
                temp_path = output.name
                output.write(payload)
            os.replace(temp_path, filepath)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

        log(f"Exported {len(ghost_store)} ghosts to '{filepath}'")
        return True

    except (IOError, OSError, ValueError, TypeError) as exc:
        warn(f"Error exporting ghosts: {exc}")
        return False


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def import_ghosts(
    filepath: str,
    scene: bpy.types.Scene,
    target_object: Optional[bpy.types.Object] = None,
    remap_bones: bool = True,
) -> bool:
    """Import a ghost configuration from a JSON file.

    Reads ghost and snapshot data from the file, validates version
    compatibility, and loads the data into the scene's stores.

    If a target_object is provided and remap_bones is True, bone names
    in the imported data are matched against the target object's bones.
    Unmatched bones generate a warning but do not block the import.

    Args:
        filepath: Path to the JSON file to import.
        scene: The Blender scene to import into.
        target_object: Optional object to remap ghost data onto.
        remap_bones: If True, attempt to match bone names from the file
                     to bones on the target object.

    Returns:
        bool: True if import succeeded, False otherwise.
    """
    if not os.path.exists(filepath):
        warn(f"File not found: '{filepath}'")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        warn(f"Invalid JSON syntax in '{filepath}': {exc}")
        return False
    except (IOError, OSError, UnicodeDecodeError) as exc:
        warn(f"Error reading file '{filepath}': {exc}")
        return False

    # Parse and validate BOTH stores before replacing either one.
    from .ghost_data import Ghost
    try:
        if not isinstance(data, dict):
            raise ValueError("Import root must be an object")
        if not any(key in data for key in ('ghosts', 'snapshots')):
            raise ValueError("File contains no ghost or snapshot data")
        if data.get('version', '1.0.0') not in COMPATIBLE_VERSIONS:
            raise ValueError('Unsupported Ghost Tool file version')
        ghost_data_list = data.get('ghosts', [])
        snapshot_data_list = data.get('snapshots', [])
        if not isinstance(ghost_data_list, list) or not isinstance(snapshot_data_list, list):
            raise ValueError("Ghosts and snapshots must be lists")
        staged_ghosts = []
        for item in ghost_data_list:
            valid, error = _validate_ghost_data(item)
            if not valid:
                raise ValueError(error)
            staged_ghosts.append(Ghost.from_dict(item).to_dict())
        if len({item['uid'] for item in staged_ghosts}) != len(staged_ghosts):
            raise ValueError("Duplicate ghost IDs")
        staged_snapshots = SnapshotStore()
        staged_snapshots.load_from_dict_list(snapshot_data_list)
        existing = SnapshotStore.get(scene).get_all()
        incoming = staged_snapshots.get_all()
        from .snapshot import MAX_SNAPSHOTS
        if len(existing) + len(incoming) > MAX_SNAPSHOTS:
            raise ValueError('Import would exceed ten retained snapshots. Delete unwanted references and retry.')
        if target_object:
            staged_ghosts = _remap_ghost_data(staged_ghosts, target_object, remap_bones)
            for reference in list(staged_snapshots.get_all()):
                try:
                    staged_snapshots.bind_snapshot(reference.uid, scene, target_object)
                except ValueError as exc:
                    # Keep the complete original reference viewable when an
                    # explicit mapping cannot resolve every required channel.
                    reference.unbound_reason = str(exc)
                    if len(reference.object_names) <= 1:
                        # Preserve the explicit legacy mapping request even
                        # when a channel cannot bind. Labels move consistently;
                        # frozen samples/keys remain unchanged and restore stays
                        # unbound. Multi-source references are never collapsed.
                        reference.ghost_data = _remap_ghost_data(reference.ghost_data, target_object, remap_bones)
                        for entry in reference.curve_data + reference.scope:
                            entry['object_name'] = target_object.name
                        reference.object_names = {target_object.name}
                        reference.bone_names = {g.get('bone_name', '') for g in reference.ghost_data if g.get('bone_name')}
                    warn(f'Imported reference remains unbound: {exc}')
        incoming = staged_snapshots.get_all()
        from uuid import uuid4
        used = {s.uid for s in existing}
        remapped = {}
        for reference in incoming:
            if reference.uid in used:
                remapped[reference.uid] = uuid4().hex
            used.add(remapped.get(reference.uid, reference.uid))
        for reference in incoming:
            reference.uid = remapped.get(reference.uid, reference.uid)
            reference.parent_uid = remapped.get(reference.parent_uid, reference.parent_uid)
            if reference.origin.get('uid') in remapped:
                reference.origin['uid'] = remapped[reference.origin['uid']]
        combined = incoming + existing
        ghosts = [Ghost.from_dict(item) for item in staged_ghosts]
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        warn(f"Import rejected; existing data preserved: {exc}")
        return False

    ghost_store = GhostStore.get(scene)
    snapshot_store = SnapshotStore.get(scene)
    old_ghosts = list(ghost_store)
    old_snapshots = snapshot_store.get_all()
    snapshots_replaced = False
    try:
        snapshot_store.replace_snapshots(combined)
        snapshots_replaced = True
        ghost_store.replace_all(ghosts)
    except Exception as exc:
        # A failed replace_snapshots already restored its own state; only undo
        # a completed one. Unreadable saved data must not raise again here.
        if snapshots_replaced:
            try:
                snapshot_store.replace_snapshots(old_snapshots, allow_overflow=True)
            except Exception as rollback_exc:
                warn(f'Snapshot rollback failed: {rollback_exc}')
        ghost_store.replace_all(old_ghosts)
        warn(f'Import commit failed; existing data preserved: {exc}')
        return False
    from .session_state import SessionState
    from .viewport_draw import _batch_cache
    SessionState.get(scene).clear_all()
    _batch_cache.clear()
    log(f"Imported {len(ghost_store)} ghosts and {len(snapshot_store.get_all())} snapshots from '{filepath}'")
    return True


def _remap_ghost_data(
    ghost_data: list[dict],
    target_object: bpy.types.Object,
    remap_bones: bool,
) -> list[dict]:
    """Remap ghost object/bone references to a target object.

    Updates the object_name field for all ghosts, and optionally matches
    bone names against the target armature.

    Args:
        ghost_data: List of ghost dictionaries to remap.
        target_object: The target Blender object.
        remap_bones: Whether to validate and remap bone names.

    Returns:
        list[dict]: Remapped ghost data (modified in place and returned).
    """
    target_name = target_object.name

    # Build set of valid bone names on the target armature
    valid_bones: set[str] = set()
    if target_object.type == 'ARMATURE' and target_object.data:
        valid_bones = {bone.name for bone in target_object.data.bones}

    unmatched_bones: set[str] = set()

    for ghost_dict in ghost_data:
        # Update all ghosts to reference the target object
        ghost_dict["object_name"] = target_name

        # Validate bone names if remapping is enabled
        if remap_bones and ghost_dict.get("bone_name"):
            bone_name = ghost_dict["bone_name"]
            if bone_name not in valid_bones:
                unmatched_bones.add(bone_name)
                # Keep the original name — the ghost will be non-functional
                # for this bone but won't crash the import

    # Warn about bones that couldn't be matched
    if unmatched_bones:
        warn(f"{len(unmatched_bones)} bone(s) from import not found on '{target_name}': {sorted(unmatched_bones)}")

    return ghost_data


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class GHOST_OT_export(bpy.types.Operator):
    """Export ghost configuration to a JSON file."""

    bl_idname = "ghost_tool.export_ghosts"
    bl_label = "Export Ghosts"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path for the export JSON file",
        subtype='FILE_PATH',
        default="//ghost_export.json",
    )  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Run the export.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        # Resolve relative path
        filepath = bpy.path.abspath(self.filepath)

        success = export_ghosts(filepath, context.scene)
        if success:
            self.report({'INFO'}, f"Ghosts exported to '{filepath}'")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Export failed — check console for details")
            return {'CANCELLED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Show the file browser for path selection.

        Args:
            context: The current Blender context.
            event: The triggering event.

        Returns:
            set[str]: Result of the file browser invocation.
        """
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class GHOST_OT_import(bpy.types.Operator):
    """Import ghost configuration from a JSON file."""

    bl_idname = "ghost_tool.import_ghosts"
    bl_label = "Import Ghosts"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to the ghost JSON file to import",
        subtype='FILE_PATH',
    )  # type: ignore[assignment]

    remap_to_active: bpy.props.BoolProperty(
        name="Remap to Active Object",
        description="Remap imported ghosts to the currently active object",
        default=True,
    )  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Run the import.

        Args:
            context: The current Blender context.

        Returns:
            set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        filepath = bpy.path.abspath(self.filepath)

        target = context.active_object if self.remap_to_active else None

        success = import_ghosts(
            filepath, context.scene,
            target_object=target,
            remap_bones=True,
        )

        if success:
            # Activate ghost display
            if hasattr(context.scene, 'ghost_tool'):
                context.scene.ghost_tool.is_active = True

            self.report({'INFO'}, f"Ghosts imported from '{filepath}'")
            tag_viewport_redraw(context)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Import failed — check console for details")
            return {'CANCELLED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Show the file browser for path selection.

        Args:
            context: The current Blender context.
            event: The triggering event.

        Returns:
            set[str]: Result of the file browser invocation.
        """
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GHOST_OT_export,
    GHOST_OT_import,
)


def register() -> None:
    """Register export/import operator classes."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister export/import operator classes."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Export produces valid JSON
# >>> import tempfile, os
# >>> path = os.path.join(tempfile.gettempdir(), "ghost_test.json")
# >>> export_ghosts(path, bpy.context.scene)
# >>> with open(path) as f: data = json.load(f)
# >>> assert data["version"] == "1.0.0"
#
# Test 2: Round-trip export/import
# >>> export_ghosts(path, bpy.context.scene)
# >>> GhostStore.get(bpy.context.scene).clear()
# >>> import_ghosts(path, bpy.context.scene)
# >>> assert len(GhostStore.get(bpy.context.scene)) > 0
#
# Test 3: Bone remapping warnings
# >>> # Import onto an armature missing some bones from the file
# >>> # Console should show warning about unmatched bones
