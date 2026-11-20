"""Import / export addon preferences to JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .. import constants
from ..core.logging import get_logger
from ..core.helpers import report_failure

_log = get_logger(__name__)


def _prefs_available(context: bpy.types.Context) -> bool:
    """Return whether addon preferences are reachable."""
    return _get_prefs(context) is not None


def _get_prefs(context: bpy.types.Context):
    from ..prefs import get_prefs
    return get_prefs(context)


def _is_compatible_value(current_value: Any, new_value: Any) -> bool:
    if isinstance(current_value, bool):
        return isinstance(new_value, bool)
    if isinstance(current_value, int) and not isinstance(current_value, bool):
        return isinstance(new_value, int) and not isinstance(new_value, bool)
    if isinstance(current_value, float):
        return isinstance(new_value, (int, float)) and not isinstance(
            new_value, bool
        )
    if isinstance(current_value, str):
        return isinstance(new_value, str)
    return True


class AA_OT_export_settings(bpy.types.Operator, ExportHelper):
    bl_idname = "anim_assist.export_settings"
    bl_label = "Export AnimAssist Settings"
    bl_description = "Export addon preferences to a JSON file"
    bl_options = {"REGISTER"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _prefs_available(context)

    def execute(self, context: bpy.types.Context):
        prefs = _get_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Add-on preferences unavailable. Re-enable Anim Assist in Preferences > Add-ons")
            return {"CANCELLED"}

        if not self.filepath:
            self.report({"ERROR"}, "Choose a file to export to first")
            return {"CANCELLED"}

        data: dict[str, Any] = {}
        for key in constants.MODULE_KEYS:
            attr = f"enable_{key}"
            if hasattr(prefs, attr):
                data[attr] = getattr(prefs, attr)
        data["debug_mode"] = prefs.debug_mode
        data["performance_mode"] = prefs.performance_mode
        data["diagnostics_visible"] = prefs.diagnostics_visible
        from ..ui.timeline_catalog import ACTIONS, quick_property_name
        for action in ACTIONS:
            name = quick_property_name(action)
            data[name] = getattr(prefs, name)
        data["timeline_quick_family"] = prefs.timeline_quick_family
        from ..prefs import timeline_record
        from ..ui.timeline_config import encode
        data['timeline_layouts_json']=prefs.timeline_layouts_json or encode(timeline_record(prefs),ACTIONS)
        data['timeline_toolbar_row']=prefs.timeline_toolbar_row
        data['timeline_canvas_row_initialized']=prefs.timeline_canvas_row_initialized
        data["_version"] = constants.ADDON_VERSION_STRING

        try:
            Path(self.filepath).write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except (OSError, ValueError, TypeError) as exc:
            report_failure(self, "Could not export settings", "Choose a writable location and try again", exc)
            _log.exception("Settings export failed")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Settings exported to {self.filepath}")
        return {"FINISHED"}


class AA_OT_import_settings(bpy.types.Operator, ImportHelper):
    bl_idname = "anim_assist.import_settings"
    bl_label = "Import AnimAssist Settings"
    bl_description = "Import addon preferences from a JSON file"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _prefs_available(context)

    def execute(self, context: bpy.types.Context):
        prefs = _get_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Add-on preferences unavailable. Re-enable Anim Assist in Preferences > Add-ons")
            return {"CANCELLED"}

        if not self.filepath:
            self.report({"ERROR"}, "Choose a settings file to import first")
            return {"CANCELLED"}

        try:
            raw = Path(self.filepath).read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            report_failure(self, "Could not import settings", "Choose a settings file exported by Anim Assist", exc)
            _log.exception("Settings import failed")
            return {"CANCELLED"}

        if not isinstance(data, dict):
            self.report({"ERROR"}, "Import failed: JSON root must be an object")
            return {"CANCELLED"}

        # Validate the whole toolbar record before assigning any preferences.
        # A rejected layout file cannot partially overwrite a user's library.
        from ..ui import timeline_config as toolbar_model
        from ..ui.timeline_catalog import ACTIONS, quick_property_name
        from ..prefs import timeline_record
        try:
            layout_raw=data.get('timeline_layouts_json')
            if 'timeline_layouts_json' in data and not isinstance(layout_raw,str):
                raise ValueError('Toolbar layout must be a JSON string')
            if layout_raw:
                if not isinstance(layout_raw,str): raise ValueError('Toolbar layout must be a JSON string')
                data['timeline_layouts_json']=toolbar_model.encode(toolbar_model.decode(layout_raw,ACTIONS),ACTIONS)
            elif any(quick_property_name(action) in data for action in ACTIONS):
                existing=timeline_record(prefs)
                chosen={a for a in ACTIONS if existing['active']['tools'][a]['mode']!='HIDDEN'}
                for action in ACTIONS:
                    key=quick_property_name(action)
                    if key in data:
                        if type(data[key]) is not bool: raise ValueError('Quick tool choices must be checkboxes')
                        if data[key]: chosen.add(action)
                        else: chosen.discard(action)
                migrated=toolbar_model.from_legacy(ACTIONS,chosen)
                migrated['saved']=existing['saved']
                data['timeline_layouts_json']=toolbar_model.encode(migrated,ACTIONS)
            elif 'timeline_layouts_json' in data:
                raise ValueError('The settings file has an empty toolbar layout record')
        except ValueError as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}

        applied = 0
        from ..ui.timeline_catalog import GROUPS
        families = {key for key, _label, _actions in GROUPS}
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if not hasattr(prefs, key):
                continue
            if key == "timeline_quick_family" and (not isinstance(value, str) or value not in families):
                _log.warning("Skipping unknown quick family: %r", value)
                continue

            current_value = getattr(prefs, key)
            if not _is_compatible_value(current_value, value):
                _log.warning(
                    "Skipping setting '%s': expected %s, got %s",
                    key,
                    type(current_value).__name__,
                    type(value).__name__,
                )
                continue

            try:
                setattr(prefs, key, value)
                applied += 1
            except Exception:
                _log.warning("Could not apply setting '%s'", key, exc_info=True)

        self.report({"INFO"}, f"Applied {applied} settings from {self.filepath}")
        return {"FINISHED"}
