"""BoneCraft Phase 1 — Visibility Bookmarks.

Save and restore named snapshots of bone-collection visibility states.
Bookmark data is stored as a JSON custom property on the armature object
so it travels with the .blend file and survives append operations.

Four default bookmark slots are always visible at the top of the
collection panel. Additional bookmarks expand below.
"""

import json

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup

import logging

from boneforge.i18n import T

logger = logging.getLogger(__name__)

from boneforge.core import (
    active_armature,
    snapshot_visibility,
    restore_visibility,
    read_custom_json,
    write_custom_json,
    addon_prefs,
    register_draw,
    unregister_draw,
)

# ── Custom property key ─────────────────────────────────────────

_KEY_BOOKMARKS = "boneforge_bookmarks"
_DEFAULT_SLOT_COUNT = 4


# ── Property group ──────────────────────────────────────────────

class BF_BookmarkItem(PropertyGroup):
    """A single visibility bookmark."""

    bm_name: StringProperty(
        name="Bookmark Name",
        description="User-facing label for this bookmark",
        default="Untitled",
    )
    state_json: StringProperty(
        name="State JSON",
        description="JSON dict mapping collection names to visibility booleans",
        default="{}",
    )
    color: FloatVectorProperty(
        name="Color",
        description="Optional indicator color for this bookmark button",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.6, 0.6, 0.6),
    )
    is_set: BoolProperty(
        name="Is Set",
        description="Whether this bookmark slot has been saved at least once",
        default=False,
    )


class BF_BookmarkSettings(PropertyGroup):
    """Bookmark list stored on the armature object."""

    bookmarks: CollectionProperty(
        type=BF_BookmarkItem,
        name="Visibility Bookmarks",
    )
    active_bookmark_index: IntProperty(default=0)
    show_extra_bookmarks: BoolProperty(
        name="Show Extra Bookmarks",
        description="Expand to show bookmarks beyond the default four slots",
        default=False,
    )


# ── Helpers ─────────────────────────────────────────────────────

def _ensure_default_slots(settings: BF_BookmarkSettings) -> None:
    """Ensure at least four bookmark slots exist."""
    default_names = ["FK Arms", "IK Body", "Face Only", "Full Rig"]
    while len(settings.bookmarks) < _DEFAULT_SLOT_COUNT:
        idx = len(settings.bookmarks)
        item = settings.bookmarks.add()
        item.bm_name = default_names[idx] if idx < len(default_names) else f"Slot {idx + 1}"


def _bookmark_settings(arm_obj) -> BF_BookmarkSettings:
    """Get or lazily initialize bookmark settings on the armature."""
    return arm_obj.boneforge_bookmark_settings


def _persist_to_custom_prop(arm_obj) -> None:
    """Serialize all bookmark data to the armature custom property.

    This ensures bookmarks survive append / library link.
    """
    settings = _bookmark_settings(arm_obj)
    data = []
    for bm in settings.bookmarks:
        data.append({
            "name": bm.bm_name,
            "state": json.loads(bm.state_json) if bm.state_json else {},
            "color": list(bm.color),
            "is_set": bm.is_set,
        })
    write_custom_json(arm_obj, _KEY_BOOKMARKS, data)


def _load_from_custom_prop(arm_obj) -> None:
    """Load bookmark data from the armature custom property into
    the PropertyGroup, if present. Called once on first access.
    """
    settings = _bookmark_settings(arm_obj)
    data = read_custom_json(arm_obj, _KEY_BOOKMARKS)
    if data is None or not isinstance(data, list):
        return

    # Clear existing and rebuild
    settings.bookmarks.clear()
    for entry in data:
        item = settings.bookmarks.add()
        item.bm_name = entry.get("name", "Untitled")
        state = entry.get("state", {})
        item.state_json = json.dumps(state)
        color = entry.get("color", [0.6, 0.6, 0.6])
        item.color = color[:3]
        item.is_set = entry.get("is_set", False)


# ── Operators ───────────────────────────────────────────────────

class BF_OT_SaveBookmark(Operator):
    """Save the current visibility state to this bookmark slot"""
    bl_idname = "boneforge.save_bookmark"
    bl_label = "Save Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    slot_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)
    bookmark_name: StringProperty(
        name="Name",
        description="Name for this bookmark",
        default="",
    )

    def invoke(self, context, event):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        settings = _bookmark_settings(arm)
        _ensure_default_slots(settings)
        if 0 <= self.slot_index < len(settings.bookmarks):
            self.bookmark_name = settings.bookmarks[self.slot_index].bm_name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = _bookmark_settings(arm)
        _ensure_default_slots(settings)

        if not (0 <= self.slot_index < len(settings.bookmarks)):
            self.report({'WARNING'}, "Invalid bookmark slot")
            return {'CANCELLED'}

        state = snapshot_visibility(arm.data)
        bm = settings.bookmarks[self.slot_index]
        bm.bm_name = self.bookmark_name or bm.bm_name
        bm.state_json = json.dumps(state)
        bm.is_set = True

        _persist_to_custom_prop(arm)
        self.report({'INFO'}, f"Bookmark '{bm.bm_name}' saved")
        return {'FINISHED'}


class BF_OT_RestoreBookmark(Operator):
    """Restore visibility from this bookmark"""
    bl_idname = "boneforge.restore_bookmark"
    bl_label = "Restore Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    slot_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = _bookmark_settings(arm)
        _ensure_default_slots(settings)

        if not (0 <= self.slot_index < len(settings.bookmarks)):
            self.report({'WARNING'}, "Invalid bookmark slot")
            return {'CANCELLED'}

        bm = settings.bookmarks[self.slot_index]
        if not bm.is_set:
            self.report({'INFO'}, f"Bookmark '{bm.bm_name}' is empty — save first")
            return {'CANCELLED'}

        try:
            state = json.loads(bm.state_json)
        except (json.JSONDecodeError, TypeError):
            self.report({'WARNING'}, f"Bookmark '{bm.bm_name}' has corrupted data")
            return {'CANCELLED'}

        missing = restore_visibility(arm.data, state)
        if missing:
            names = ", ".join(missing[:3])
            suffix = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
            self.report({'INFO'},
                        f"Restored '{bm.bm_name}' — skipped missing: {names}{suffix}")
        else:
            self.report({'INFO'}, f"Restored '{bm.bm_name}'")
        return {'FINISHED'}


class BF_OT_ClearBookmark(Operator):
    """Clear this bookmark slot"""
    bl_idname = "boneforge.clear_bookmark"
    bl_label = "Clear Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    slot_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = _bookmark_settings(arm)
        if 0 <= self.slot_index < len(settings.bookmarks):
            bm = settings.bookmarks[self.slot_index]
            bm.state_json = "{}"
            bm.is_set = False
            _persist_to_custom_prop(arm)
            self.report({'INFO'}, f"Bookmark '{bm.bm_name}' cleared")
        return {'FINISHED'}


class BF_OT_AddBookmark(Operator):
    """Add a new bookmark slot"""
    bl_idname = "boneforge.add_bookmark"
    bl_label = "Add Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    bookmark_name: StringProperty(description='Name of the new bookmark',
        name="Name",
        default="New Bookmark",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = _bookmark_settings(arm)
        item = settings.bookmarks.add()
        item.bm_name = self.bookmark_name

        state = snapshot_visibility(arm.data)
        item.state_json = json.dumps(state)
        item.is_set = True

        _persist_to_custom_prop(arm)
        self.report({'INFO'}, f"Bookmark '{self.bookmark_name}' added and saved")
        return {'FINISHED'}


class BF_OT_RemoveBookmark(Operator):
    """Remove a bookmark slot (only extra bookmarks, not default four)"""
    bl_idname = "boneforge.remove_bookmark"
    bl_label = "Remove Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    slot_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = _bookmark_settings(arm)
        if self.slot_index < _DEFAULT_SLOT_COUNT:
            self.report({'WARNING'}, "Cannot remove default bookmark slots — use Clear instead")
            return {'CANCELLED'}

        if 0 <= self.slot_index < len(settings.bookmarks):
            settings.bookmarks.remove(self.slot_index)
            _persist_to_custom_prop(arm)
        return {'FINISHED'}


class BF_OT_RenameBookmark(Operator):
    """Rename this bookmark"""
    bl_idname = "boneforge.rename_bookmark"
    bl_label = "Rename Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    slot_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)
    new_name: StringProperty(description="The bookmark's new name", name="Name")

    def invoke(self, context, event):
        arm = active_armature(context)
        if arm is not None:
            settings = _bookmark_settings(arm)
            _ensure_default_slots(settings)
            if 0 <= self.slot_index < len(settings.bookmarks):
                self.new_name = settings.bookmarks[self.slot_index].bm_name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        settings = _bookmark_settings(arm)
        if 0 <= self.slot_index < len(settings.bookmarks):
            settings.bookmarks[self.slot_index].bm_name = self.new_name
            _persist_to_custom_prop(arm)
        return {'FINISHED'}


class BF_OT_SetBookmarkColor(Operator):
    """Set the indicator color for this bookmark"""
    bl_idname = "boneforge.set_bookmark_color"
    bl_label = "Bookmark Color"
    bl_options = {'REGISTER', 'UNDO'}

    slot_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)
    color: FloatVectorProperty(description="The bookmark's colour",
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.6, 0.6, 0.6),
    )

    def invoke(self, context, event):
        arm = active_armature(context)
        if arm is not None:
            settings = _bookmark_settings(arm)
            _ensure_default_slots(settings)
            if 0 <= self.slot_index < len(settings.bookmarks):
                self.color = settings.bookmarks[self.slot_index].color
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        settings = _bookmark_settings(arm)
        if 0 <= self.slot_index < len(settings.bookmarks):
            settings.bookmarks[self.slot_index].color = self.color
            _persist_to_custom_prop(arm)
        return {'FINISHED'}


# ── Bookmark Panel (sub-panel of the collection panel) ──────────

class BF_PT_BookmarkPanel(Panel):
    """BoneCraft — Visibility Bookmarks"""
    bl_idname = "BF_PT_bookmark_panel"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_collections"  # v3.3.2: re-parented from BF_PT_collection_panel to hub delegate
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Visibility Bookmarks"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        draw_bookmarks(self.layout, context)


def draw_bookmarks(layout, context):
    """Public draw function for embedding bookmarks in other panels."""
    arm = active_armature(context)
    if arm is None:
        layout.label(text=T("No active armature"), icon='INFO')
        return

    settings = _bookmark_settings(arm)

    # Load from custom property on first access
    if len(settings.bookmarks) == 0:
        _load_from_custom_prop(arm)
    _ensure_default_slots(settings)

    # Default four slots — persistent buttons
    grid = layout.grid_flow(row_major=True, columns=2, align=True)
    for i in range(_DEFAULT_SLOT_COUNT):
        if i >= len(settings.bookmarks):
            break
        bm = settings.bookmarks[i]
        _draw_bookmark_slot(grid, bm, i)

    # Extra bookmarks toggle
    if len(settings.bookmarks) > _DEFAULT_SLOT_COUNT:
        row = layout.row()
        icon = 'TRIA_DOWN' if settings.show_extra_bookmarks else 'TRIA_RIGHT'
        row.prop(settings, "show_extra_bookmarks",
                 text=f"{len(settings.bookmarks) - _DEFAULT_SLOT_COUNT} more",
                 icon=icon, emboss=False)

        if settings.show_extra_bookmarks:
            for i in range(_DEFAULT_SLOT_COUNT, len(settings.bookmarks)):
                bm = settings.bookmarks[i]
                _draw_bookmark_slot(layout, bm, i, removable=True)

    # Add button
    layout.operator("boneforge.add_bookmark",
                     text=T("Add Bookmark"), icon='ADD')


def _draw_bookmark_slot(parent, bm, index, removable=False):
    """Draw a single bookmark slot with restore / save / clear buttons."""
    row = parent.row(align=True)

    # Color indicator
    sub = row.row(align=True)
    sub.scale_x = 0.1
    sub.prop(bm, "color", text="")

    # Restore button (main)
    if bm.is_set:
        op = row.operator("boneforge.restore_bookmark",
                           text=bm.bm_name, icon='BOOKMARKS')
        op.slot_index = index
    else:
        row.label(text=f"[ {bm.bm_name} ]", icon='BOOKMARKS')

    # Save
    op = row.operator("boneforge.save_bookmark",
                       text="", icon='FILE_TICK')
    op.slot_index = index

    # Clear
    op = row.operator("boneforge.clear_bookmark",
                       text="", icon='X')
    op.slot_index = index

    # Remove (extra slots only)
    if removable:
        op = row.operator("boneforge.remove_bookmark",
                           text="", icon='X')
        op.slot_index = index


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_BookmarkItem,
    BF_BookmarkSettings,
    BF_OT_SaveBookmark,
    BF_OT_RestoreBookmark,
    BF_OT_ClearBookmark,
    BF_OT_AddBookmark,
    BF_OT_RemoveBookmark,
    BF_OT_RenameBookmark,
    BF_OT_SetBookmarkColor,
    BF_PT_BookmarkPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.boneforge_bookmark_settings = bpy.props.PointerProperty(
        type=BF_BookmarkSettings,
        name="BoneCraft Bookmark Settings",
    )

    register_draw("bookmarks", draw_bookmarks)


def unregister():
    unregister_draw("bookmarks")

    del bpy.types.Object.boneforge_bookmark_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
