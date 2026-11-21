"""
Preset and workspace profile operators for batch operations and automation.

Provides operators for:
- Exporting/importing workspace profiles to/from files
- Saving/loading named workspace profiles to the p10.profiles collection
- Managing profiles (remove, tag)
"""

import json
from typing import Any

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ..core.logging import get_logger
from ..core.p10_properties import get_p10
from ..core.p10_preset_io import (
    export_workspace_profile,
    import_workspace_profile,
    get_preset_directory,
    collect_scene_settings,
    apply_scene_settings,
)
from ..core.p10_audit import log_operation
from ..core.helpers import report_failure

_log = get_logger(__name__)


class AA_OT_p10_export_workspace(Operator):
    """Export workspace profile to file"""
    bl_idname = "animassist.p10_export_workspace"
    bl_label = "Export Workspace Profile"
    bl_options = {'REGISTER'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath for the exported workspace profile",
        subtype='FILE_PATH',
    )
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        """Open file browser to select output path."""
        preset_dir = get_preset_directory()
        self.filepath = str(preset_dir / "workspace_profile.json")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context: bpy.types.Context):
        """Export the current workspace profile to the selected file."""
        try:
            success = export_workspace_profile(context, self.filepath)
            if success:
                log_operation(
                    self.bl_idname,
                    success=True,
                    detail=f"Exported to {self.filepath}",
                )
                self.report({'INFO'}, f"Workspace profile exported: {self.filepath}")
                return {'FINISHED'}
            else:
                log_operation(
                    self.bl_idname,
                    success=False,
                    detail="export_workspace_profile returned False",
                )
                self.report({'ERROR'}, "Could not export the profile. Choose a writable location and try again")
                return {'CANCELLED'}
        except Exception as exc:
            _log.exception("Export workspace failed")
            log_operation(
                self.bl_idname,
                success=False,
                detail=str(exc),
            )
            report_failure(self, "Could not export the profile", "Choose a writable location and try again", exc)
            return {'CANCELLED'}


class AA_OT_p10_import_workspace(Operator):
    """Import workspace profile from file"""
    bl_idname = "animassist.p10_import_workspace"
    bl_label = "Import Workspace Profile"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath of the workspace profile to import",
        subtype='FILE_PATH',
    )
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        """Open file browser to select input file."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context: bpy.types.Context):
        """Import workspace profile from the selected file."""
        try:
            count = import_workspace_profile(context, self.filepath)
            if count >= 0:
                log_operation(
                    self.bl_idname,
                    success=True,
                    detail=f"Applied {count} properties from {self.filepath}",
                )
                self.report(
                    {'INFO'},
                    f"Workspace profile imported: {count} properties applied",
                )
                return {'FINISHED'}
            else:
                log_operation(
                    self.bl_idname,
                    success=False,
                    detail="import_workspace_profile returned -1",
                )
                self.report({'ERROR'}, "Could not import the profile. Choose a profile exported by Anim Assist")
                return {'CANCELLED'}
        except Exception as exc:
            _log.exception("Import workspace failed")
            log_operation(
                self.bl_idname,
                success=False,
                detail=str(exc),
            )
            report_failure(self, "Could not import the profile", "Choose a profile exported by Anim Assist", exc)
            return {'CANCELLED'}


class AA_OT_p10_save_profile(Operator):
    """Save current settings as a named profile"""
    bl_idname = "animassist.p10_save_profile"
    bl_label = "Save Profile"
    bl_options = {'REGISTER'}

    name: StringProperty(
        name="Profile Name",
        description="Name for the new profile",
        default="Default",
    )

    def execute(self, context: bpy.types.Context):
        """Save current scene settings to a new profile in the collection."""
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            # Collect current scene settings
            settings = collect_scene_settings(context)

            # Serialize to JSON
            profile_data = {
                "type": "workspace_profile",
                "scene_name": context.scene.name,
                "settings": settings,
            }
            data_json = json.dumps(profile_data, indent=2)

            # Add new profile to collection
            profile = p10.profiles.add()
            profile.name = self.name or "Default"
            profile.data_json = data_json

            log_operation(
                self.bl_idname,
                success=True,
                detail=f"Saved profile '{profile.name}'",
            )
            self.report({'INFO'}, f"Profile saved: {profile.name}")
            return {'FINISHED'}

        except Exception as exc:
            _log.exception("Save profile failed")
            log_operation(
                self.bl_idname,
                success=False,
                detail=str(exc),
            )
            report_failure(self, "Could not save the profile", "Give the profile a name and try again", exc)
            return {'CANCELLED'}


class AA_OT_p10_load_profile(Operator):
    """Load a profile from the collection"""
    bl_idname = "animassist.p10_load_profile"
    bl_label = "Load Profile"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Profile Index",
        description="Index of the profile to load",
        default=0,
        min=0,
    )

    def execute(self, context: bpy.types.Context):
        """Load profile settings from the collection and apply to scene."""
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if self.index >= len(p10.profiles):
                self.report({'ERROR'}, f"Select a profile in the list first")
                return {'CANCELLED'}

            profile = p10.profiles[self.index]

            # Deserialize JSON
            try:
                profile_data = json.loads(profile.data_json)
            except json.JSONDecodeError as exc:
                _log.exception("Failed to deserialize profile JSON")
                report_failure(self, "The profile data is not valid", "Re-save the profile from Dope Sheet > Anim Assist > Shelf & Macros > System & Recovery", exc)
                return {'CANCELLED'}

            # Extract and apply settings
            settings = profile_data.get("settings", {})
            count = apply_scene_settings(context, settings)

            log_operation(
                self.bl_idname,
                success=True,
                detail=f"Loaded profile '{profile.name}' ({count} properties)",
            )
            self.report({'INFO'}, f"Profile loaded: {profile.name} ({count} properties)")
            return {'FINISHED'}

        except Exception as exc:
            _log.exception("Load profile failed")
            log_operation(
                self.bl_idname,
                success=False,
                detail=str(exc),
            )
            report_failure(self, "Could not load the profile", "Select a profile in the list and try again", exc)
            return {'CANCELLED'}


class AA_OT_p10_remove_profile(Operator):
    """Remove a profile by index"""
    bl_idname = "animassist.p10_remove_profile"
    bl_label = "Remove Profile"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Profile Index",
        description="Index of the profile to remove",
        default=0,
        min=0,
    )

    def execute(self, context: bpy.types.Context):
        """Remove profile from the collection."""
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if self.index >= len(p10.profiles):
                self.report({'ERROR'}, f"Select a profile in the list first")
                return {'CANCELLED'}

            profile_name = p10.profiles[self.index].name
            p10.profiles.remove(self.index)

            log_operation(
                self.bl_idname,
                success=True,
                detail=f"Removed profile '{profile_name}'",
            )
            self.report({'INFO'}, f"Profile removed: {profile_name}")
            return {'FINISHED'}

        except Exception as exc:
            _log.exception("Remove profile failed")
            log_operation(
                self.bl_idname,
                success=False,
                detail=str(exc),
            )
            report_failure(self, "Remove failed", "Select a profile in the list and try again", exc)
            return {'CANCELLED'}


class AA_OT_p10_tag_preset(Operator):
    """Add a tag to a profile (stored in data_json metadata)"""
    bl_idname = "animassist.p10_tag_preset"
    bl_label = "Tag Preset"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Profile Index",
        description="Index of the profile to tag",
        default=0,
        min=0,
    )
    tag: StringProperty(
        name="Tag",
        description="Tag to add to the profile",
        default="",
    )

    def execute(self, context: bpy.types.Context):
        """Add a tag to the profile's metadata."""
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if self.index >= len(p10.profiles):
                self.report({'ERROR'}, f"Select a profile in the list first")
                return {'CANCELLED'}

            if not self.tag:
                self.report({'ERROR'}, "Enter a tag name first")
                return {'CANCELLED'}

            profile = p10.profiles[self.index]

            # Deserialize JSON
            try:
                profile_data: dict[str, Any] = json.loads(profile.data_json)
            except json.JSONDecodeError:
                # If JSON is invalid, create a minimal structure
                profile_data = {
                    "type": "workspace_profile",
                    "settings": {},
                }

            # Ensure tags list exists
            if "tags" not in profile_data:
                profile_data["tags"] = []

            # Append tag if not already present
            tags = profile_data.get("tags", [])
            if self.tag not in tags:
                tags.append(self.tag)
                profile_data["tags"] = tags

            # Serialize back to JSON
            profile.data_json = json.dumps(profile_data, indent=2)

            log_operation(
                self.bl_idname,
                success=True,
                detail=f"Tagged profile '{profile.name}' with '{self.tag}'",
            )
            self.report({'INFO'}, f"Tag added: {self.tag}")
            return {'FINISHED'}

        except Exception as exc:
            _log.exception("Tag preset failed")
            log_operation(
                self.bl_idname,
                success=False,
                detail=str(exc),
            )
            report_failure(self, "Tag failed", "Select a profile in the list and try again", exc)
            return {'CANCELLED'}


CLASSES = (
    AA_OT_p10_export_workspace,
    AA_OT_p10_import_workspace,
    AA_OT_p10_save_profile,
    AA_OT_p10_load_profile,
    AA_OT_p10_remove_profile,
    AA_OT_p10_tag_preset,
)
