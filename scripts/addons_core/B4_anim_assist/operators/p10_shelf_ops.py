"""
Quick Shelf and Tool Access operators for AnimAssist P10.

Manages shelf modes (COMPACT/EXPANDED/FAVORITES), favorites list,
tool search, recent tools tracking, and quick repeat functionality.
"""

import time

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty
from bpy.types import Operator

from ..core.p10_properties import get_p10, recents_newest_first, sort_recents
from ..core.logging import get_logger
from ..core.helpers import report_failure

_log = get_logger(__name__)


class AA_OT_p10_toggle_shelf_mode(Operator):
    """Cycle shelf display mode: COMPACT → EXPANDED → FAVORITES → COMPACT"""
    bl_idname = "animassist.p10_toggle_shelf_mode"
    bl_label = "Toggle Shelf Mode"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            p10 = get_p10(context)
            if not p10:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            # Cycle through modes: 0 (COMPACT) -> 1 (EXPANDED) -> 2 (FAVORITES) -> 0
            modes = ['COMPACT', 'EXPANDED', 'FAVORITES']
            current_index = modes.index(p10.shelf_mode)
            next_index = (current_index + 1) % len(modes)
            p10.shelf_mode = modes[next_index]

            _log.info(f"Toggled shelf mode to {p10.shelf_mode}")
            self.report({'INFO'}, f"Shelf mode: {p10.shelf_mode}")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Error toggling shelf mode: {e}")
            report_failure(self, "Could not change the shelf mode", "Run First Run Setup from Properties > Scene > Anim Assist > Setup to rebuild the shelf", e)
            return {'CANCELLED'}


class AA_OT_p10_add_favorite(Operator):
    """Add current tool to favorites list"""
    bl_idname = "animassist.p10_add_favorite"
    bl_label = "Add to Favorites"
    bl_options = {'REGISTER'}

    op_id: StringProperty(
        name="Operator ID",
        description="The operator ID to add as favorite",
        default=""
    )
    label: StringProperty(
        name="Label",
        description="Display label for the favorite",
        default=""
    )
    icon: StringProperty(
        name="Icon",
        description="Icon identifier",
        default="NONE"
    )

    def execute(self, context):
        try:
            p10 = get_p10(context)
            if not p10:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if not self.op_id:
                self.report({'ERROR'}, "No tool selected. Pick a tool for this shelf slot first")
                return {'CANCELLED'}

            # Check for duplicate
            for fav in p10.favorites:
                if fav.op_id == self.op_id:
                    self.report({'WARNING'}, f"'{self.label}' is already in favorites")
                    return {'CANCELLED'}

            # Add new favorite
            fav_item = p10.favorites.add()
            fav_item.op_id = self.op_id
            fav_item.label = self.label or self.op_id
            fav_item.icon = self.icon

            _log.info(f"Added favorite: {self.op_id}")
            self.report({'INFO'}, f"Added '{self.label}' to favorites")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Error adding favorite: {e}")
            report_failure(self, "Could not add the favorite", "Run First Run Setup from Properties > Scene > Anim Assist > Setup to rebuild the shelf", e)
            return {'CANCELLED'}


class AA_OT_p10_remove_favorite(Operator):
    """Remove a favorite by index"""
    bl_idname = "animassist.p10_remove_favorite"
    bl_label = "Remove Favorite"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Index",
        description="Index of favorite to remove",
        default=0,
        min=0
    )

    def execute(self, context):
        try:
            p10 = get_p10(context)
            if not p10:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if self.index < 0 or self.index >= len(p10.favorites):
                self.report({'ERROR'}, f"Select a favorite in the list first")
                return {'CANCELLED'}

            removed_label = p10.favorites[self.index].label
            p10.favorites.remove(self.index)

            _log.info(f"Removed favorite at index {self.index}")
            self.report({'INFO'}, f"Removed '{removed_label}' from favorites")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Error removing favorite: {e}")
            report_failure(self, "Could not remove the favorite", "Run First Run Setup from Properties > Scene > Anim Assist > Setup to rebuild the shelf", e)
            return {'CANCELLED'}


# Blender keeps references to strings returned by dynamic EnumProperty
# callbacks. Retain the items and their metadata for the popup's lifetime.
_tool_enum_snapshot = None
_tool_enum_items = []


def _get_tool_items(self, context):
    """Enum callback to populate tool choices from registry."""
    global _tool_enum_snapshot, _tool_enum_items
    try:
        from ..core.p10_tool_registry import all_tools

        tools = tuple(all_tools())
        if tools == _tool_enum_snapshot:
            return _tool_enum_items
        if not tools:
            _tool_enum_snapshot = tools
            _tool_enum_items = [(
                "NONE", "Run First Run Setup to restore tools",
                "Open Properties > Scene > Anim Assist > Setup", 0,
            )]
            return _tool_enum_items

        items = []
        for i, tool in enumerate(tools):
            icon = tool.icon if tool.icon != "NONE" else "NONE"
            items.append((tool.op_id, tool.label, tool.description, icon, i))

        _tool_enum_snapshot = tools
        _tool_enum_items = items
        return _tool_enum_items

    except Exception as e:
        _log.error(f"Error building tool enum items: {e}")
        _tool_enum_snapshot = None
        _tool_enum_items = [(
            "NONE", "Tools could not load", "Run First Run Setup and try again", 0,
        )]
        return _tool_enum_items


def _run_shelf_tool(operator, context, op_id):
    """Open a real tool through the same invoke route as a panel button."""
    from ..core.p10_tool_registry import get_tool

    tool = get_tool(op_id)
    if tool is None:
        operator.report({'WARNING'}, "This tool is unavailable. Run First Run Setup, then choose a tool from Search")
        return {'CANCELLED'}
    parts = op_id.split(".")
    if len(parts) != 2 or parts[0] != "animassist":
        operator.report({'ERROR'}, "This is not an Anim Assist tool. Choose a tool from Search")
        return {'CANCELLED'}
    op_func = getattr(getattr(bpy.ops, parts[0]), parts[1])
    op_func.get_rna_type()
    # INVOKE respects tool-specific defaults, file pickers and modal setup.
    # EXEC_DEFAULT bypassed these and could silently use different settings.
    result = op_func("INVOKE_DEFAULT")
    if 'CANCELLED' in result:
        return {'CANCELLED'}
    if 'FINISHED' in result:
        # History is optional bookkeeping, not a reason to misreport a
        # completed edit as cancelled. Clearing history must leave it empty.
        if op_id != "animassist.p10_clear_recents" and get_p10(context) is not None:
            try:
                bpy.ops.animassist.p10_record_recent(op_id=op_id, label=tool.label)
            except Exception:
                _log.warning("Could not record completed tool %s", op_id, exc_info=True)
        return {'FINISHED'}
    if result.intersection({'RUNNING_MODAL', 'INTERFACE'}):
        # The target owns its modal handler/dialog. Close only this wrapper;
        # do not claim completion or add an uncompleted tool to Recents.
        return {'FINISHED'}
    operator.report({'WARNING'}, "The tool did not run. Open its panel and check the required selection")
    return {'CANCELLED'}


class AA_OT_p10_search_tools(Operator):
    """Open tool search popup"""
    bl_idname = "animassist.p10_search_tools"
    bl_label = "Search Tools"
    bl_options = {'REGISTER'}
    bl_property = "tool_enum"

    tool_enum: EnumProperty(
        name="Tool",
        description="Select a tool to run",
        items=_get_tool_items
    )

    def execute(self, context):
        try:
            if self.tool_enum and self.tool_enum != "NONE":
                _log.info(f"Executing tool: {self.tool_enum}")
                return _run_shelf_tool(self, context, self.tool_enum)
            else:
                return {'CANCELLED'}

        except Exception as e:
            _log.error(f"Error executing tool search: {e}")
            report_failure(self, "Could not run the tool from the shelf", "Open the tool from its own panel instead", e)
            return {'CANCELLED'}

    def invoke(self, context, event):
        """Invoke with search popup"""
        from ..core.p10_tool_registry import all_tools

        if not all_tools():
            self.report({'WARNING'}, "No tools available. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


class AA_OT_p10_record_recent(Operator):
    """Record a tool usage in the recents list"""
    bl_idname = "animassist.p10_record_recent"
    bl_label = "Record Recent Tool"
    bl_options = {'REGISTER', 'INTERNAL'}

    op_id: StringProperty(
        name="Operator ID",
        description="The operator ID being used",
        default=""
    )
    label: StringProperty(
        name="Label",
        description="Display label for the tool",
        default=""
    )

    def execute(self, context):
        try:
            p10 = get_p10(context)
            if not p10:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if not self.op_id:
                self.report({'ERROR'}, "No tool selected. Pick a tool for this shelf slot first")
                return {'CANCELLED'}

            # Check if tool already exists in recents
            existing_idx = None
            for idx, recent in enumerate(p10.recents):
                if recent.op_id == self.op_id:
                    existing_idx = idx
                    break

            # Remove existing entry if found (will re-add at top)
            if existing_idx is not None:
                p10.recents.remove(existing_idx)

            # Add new entry at the beginning
            recent_item = p10.recents.add()
            recent_item.op_id = self.op_id
            recent_item.label = self.label or self.op_id
            recent_item.timestamp = time.time()
            # CollectionProperty.add appends; Repeat Last reads index zero.
            p10.recents.move(len(p10.recents) - 1, 0)
            # Entries saved oldest-first by 12.1.0 and earlier are reordered
            # by timestamp; equal timestamps keep the new entry first.
            sort_recents(p10)

            # Trim to max_recents
            max_recents = getattr(p10, 'max_recents', 10)
            while len(p10.recents) > max_recents:
                # Remove the oldest (last) entry
                p10.recents.remove(len(p10.recents) - 1)

            _log.info(f"Recorded recent tool: {self.op_id}")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Error recording recent tool: {e}")
            report_failure(self, "Failed to record recent tool", "Run First Run Setup from Properties > Scene > Anim Assist > Setup to rebuild the shelf", e)
            return {'CANCELLED'}


class AA_OT_p10_repeat_last(Operator):
    """Repeat the most recently used tool"""
    bl_idname = "animassist.p10_repeat_last"
    bl_label = "Repeat Last Tool"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            p10 = get_p10(context)
            if not p10:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            if len(p10.recents) == 0:
                self.report({'WARNING'}, "No recent tools available")
                return {'CANCELLED'}

            # Get the most recent tool (legacy files may be stored oldest-first)
            last_tool = recents_newest_first(p10)[0]
            op_id = last_tool.op_id

            if not op_id:
                self.report({'ERROR'}, "That recent tool is no longer available. Clear Recents and use the tool again")
                return {'CANCELLED'}

            _log.info(f"Repeating last tool: {op_id}")
            return _run_shelf_tool(self, context, op_id)

        except Exception as e:
            _log.error(f"Error repeating last tool: {e}")
            report_failure(self, "Failed to repeat last tool", "Run First Run Setup from Properties > Scene > Anim Assist > Setup to rebuild the shelf", e)
            return {'CANCELLED'}


class AA_OT_p10_clear_recents(Operator):
    """Clear the recent tools list"""
    bl_idname = "animassist.p10_clear_recents"
    bl_label = "Clear Recents"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            p10 = get_p10(context)
            if not p10:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            count = len(p10.recents)
            p10.recents.clear()

            _log.info(f"Cleared {count} recent tools")
            self.report({'INFO'}, f"Cleared {count} recent tools")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Error clearing recents: {e}")
            report_failure(self, "Failed to clear recents", "Run First Run Setup from Properties > Scene > Anim Assist > Setup to rebuild the shelf", e)
            return {'CANCELLED'}


# Registry of all operators in this module
CLASSES = (
    AA_OT_p10_toggle_shelf_mode,
    AA_OT_p10_add_favorite,
    AA_OT_p10_remove_favorite,
    AA_OT_p10_search_tools,
    AA_OT_p10_record_recent,
    AA_OT_p10_repeat_last,
    AA_OT_p10_clear_recents,
)
