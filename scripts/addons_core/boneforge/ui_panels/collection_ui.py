"""BoneCraft Phase 1 — Bone Collection Grouping Panel.

Sidebar panel displaying all bone collections of the active armature
as styled, reorderable buttons with visibility control, solo, and
bulk selection. Collections are groupable into named collapsible sections.

Ordering is stored as integer priorities on the armature custom property
so it survives save / append / link.
"""

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)

from boneforge.i18n import T
from bpy.types import Operator, Panel, PropertyGroup

import logging

logger = logging.getLogger(__name__)

from boneforge.core import (
    active_armature,
    bone_collections,
    collection_by_name,
    select_bones_in_collection,
    addon_prefs,
    register_draw,
    unregister_draw,
)

# ── Helpers ─────────────────────────────────────────────────────


def _get_settings(operator, context):
    """Return boneforge_settings for the active armature, or None.

    Reports a warning/error and returns None if the armature is missing
    or the property group was not registered.  Callers should return
    {'CANCELLED'} when this returns None.
    """
    arm = active_armature(context)
    if arm is None:
        operator.report({'WARNING'}, "No active armature")
        return None
    if not hasattr(arm, 'boneforge_settings'):
        operator.report(
            {'ERROR'},
            "BoneCraft settings not registered — try reloading the addon",
        )
        return None
    return arm.boneforge_settings


# ── Custom property keys ────────────────────────────────────────

_KEY_SECTIONS = "boneforge_sections"
_KEY_COLL_META = "boneforge_collection_meta"


# ── Property groups ─────────────────────────────────────────────

class BF_CollectionMeta(PropertyGroup):
    """Per-collection display metadata shown in the panel."""

    coll_name: StringProperty(
        name="Collection Name",
        description="Internal bone-collection name this metadata belongs to",
    )
    display_name: StringProperty(
        name="Display Name",
        description="User-facing label (double-click to rename)",
    )
    icon: StringProperty(
        name="Icon",
        description="Blender icon identifier for this collection button",
        default='BONE_DATA',
    )
    color: FloatVectorProperty(
        name="Accent Color",
        description="Left-border color tag for this collection button",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.4, 0.6, 1.0),
    )
    section: StringProperty(
        name="Section",
        description="Name of the section this collection belongs to (empty = ungrouped)",
        default="",
    )
    priority: IntProperty(
        name="Sort Priority",
        description="Lower numbers appear first in the panel",
        default=100,
    )


class BF_SectionItem(PropertyGroup):
    """A named, collapsible section that groups collections."""

    name: StringProperty(
        name="Section Name",
        description="Display name for this section header",
    )
    collapsed: BoolProperty(
        name="Collapsed",
        description="Whether the section is visually collapsed in the panel",
        default=False,
    )
    priority: IntProperty(
        name="Sort Priority",
        description="Lower numbers appear first among sections",
        default=100,
    )
    color: FloatVectorProperty(
        name="Section Color",
        description="Optional accent color for the section header",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.5, 0.5, 0.5),
    )


# ── Armature-level property group ───────────────────────────────

class BF_ArmatureSettings(PropertyGroup):
    """Root property group stored on every armature's Object."""

    collections_meta: CollectionProperty(
        type=BF_CollectionMeta,
        name="Collection Metadata",
        description="Display metadata for each bone collection",
    )
    sections: CollectionProperty(
        type=BF_SectionItem,
        name="Sections",
        description="Named collapsible groups for collections",
    )
    active_collection_index: IntProperty(default=0)
    active_section_index: IntProperty(default=0)


# ── Helpers ─────────────────────────────────────────────────────

def _ensure_meta(settings: BF_ArmatureSettings,
                 arm_data) -> None:
    """Synchronize collection metadata with the actual bone collections.

    Adds entries for new collections, removes stale ones.
    """
    existing_names = {c.name for c in bone_collections(arm_data)}
    meta_names = {m.coll_name for m in settings.collections_meta}

    # Add missing
    for name in sorted(existing_names - meta_names):
        item = settings.collections_meta.add()
        item.coll_name = name
        item.display_name = name
        item.priority = len(settings.collections_meta) * 10

    # Remove stale
    indices_to_remove = [
        i for i, m in enumerate(settings.collections_meta)
        if m.coll_name not in existing_names
    ]
    for i in reversed(indices_to_remove):
        settings.collections_meta.remove(i)


def _sorted_meta(settings: BF_ArmatureSettings) -> list:
    """Return collection meta items sorted by priority then name."""
    return sorted(settings.collections_meta,
                  key=lambda m: (m.priority, m.display_name))


def _sorted_sections(settings: BF_ArmatureSettings) -> list:
    """Return sections sorted by priority then name."""
    return sorted(settings.sections,
                  key=lambda s: (s.priority, s.name))


def _meta_for_collection(settings: BF_ArmatureSettings,
                         coll_name: str):
    """Find the meta entry for a given collection name."""
    for m in settings.collections_meta:
        if m.coll_name == coll_name:
            return m
    return None


# ── Operators ───────────────────────────────────────────────────

class BF_OT_ToggleCollectionVisibility(Operator):
    """Toggle visibility of a bone collection"""
    bl_idname = "boneforge.toggle_collection_vis"
    bl_label = "Toggle Collection Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        coll = collection_by_name(arm.data, self.collection_name)
        if coll is None:
            self.report({'WARNING'}, f"Collection '{self.collection_name}' not found")
            return {'CANCELLED'}
        coll.is_visible = not coll.is_visible
        return {'FINISHED'}


class BF_OT_SoloCollection(Operator):
    """Solo this collection — hide all others, show only this one"""
    bl_idname = "boneforge.solo_collection"
    bl_label = "Solo Collection"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        for coll in bone_collections(arm.data):
            coll.is_visible = (coll.name == self.collection_name)
        return {'FINISHED'}


class BF_OT_SelectCollectionBones(Operator):
    """Select all bones in this collection (Shift-click)"""
    bl_idname = "boneforge.select_collection_bones"
    bl_label = "Select Collection Bones"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    extend: BoolProperty(description='Add to the current selection instead of replacing it', default=False)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        if context.mode not in ('POSE', 'EDIT_ARMATURE'):
            self.report({'INFO'}, "Enter Pose or Edit mode to select bones")
            return {'CANCELLED'}
        count = select_bones_in_collection(
            context, arm, self.collection_name, extend=self.extend)
        self.report({'INFO'}, f"Selected {count} bones in '{self.collection_name}'")
        return {'FINISHED'}


class BF_OT_ShowAllCollections(Operator):
    """Show all bone collections"""
    bl_idname = "boneforge.show_all_collections"
    bl_label = "Show All Collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        for coll in bone_collections(arm.data):
            coll.is_visible = True
        return {'FINISHED'}


class BF_OT_HideAllCollections(Operator):
    """Hide all bone collections"""
    bl_idname = "boneforge.hide_all_collections"
    bl_label = "Hide All Collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        for coll in bone_collections(arm.data):
            coll.is_visible = False
        return {'FINISHED'}


# ── Section operators ───────────────────────────────────────────

class BF_OT_AddSection(Operator):
    """Add a new collection section"""
    bl_idname = "boneforge.add_section"
    bl_label = "Add Section"
    bl_options = {'REGISTER', 'UNDO'}

    section_name: StringProperty(
        name="Section Name",
        description="Name for the new section",
        default="New Section",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}
        if not hasattr(arm, 'boneforge_settings'):
            self.report({'ERROR'},
                        "BoneCraft settings not registered — "
                        "try reloading the addon")
            return {'CANCELLED'}
        settings = arm.boneforge_settings
        # Prevent duplicates
        for s in settings.sections:
            if s.name == self.section_name:
                self.report({'WARNING'}, f"Section '{self.section_name}' already exists")
                return {'CANCELLED'}
        item = settings.sections.add()
        item.name = self.section_name
        item.priority = len(settings.sections) * 10
        return {'FINISHED'}


class BF_OT_RemoveSection(Operator):
    """Remove a collection section (collections become ungrouped)"""
    bl_idname = "boneforge.remove_section"
    bl_label = "Remove Section"
    bl_options = {'REGISTER', 'UNDO'}

    section_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        # Ungroup collections in this section
        for m in settings.collections_meta:
            if m.section == self.section_name:
                m.section = ""
        # Remove the section entry
        for i, s in enumerate(settings.sections):
            if s.name == self.section_name:
                settings.sections.remove(i)
                break
        return {'FINISHED'}


class BF_OT_ToggleSectionCollapse(Operator):
    """Collapse or expand this section"""
    bl_idname = "boneforge.toggle_section_collapse"
    bl_label = "Toggle Section"

    section_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        for s in settings.sections:
            if s.name == self.section_name:
                s.collapsed = not s.collapsed
                break
        return {'FINISHED'}


class BF_OT_AssignCollectionToSection(Operator):
    """Assign a collection to a section"""
    bl_idname = "boneforge.assign_to_section"
    bl_label = "Assign to Section"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    section_name: StringProperty(
        name="Section",
        description="Target section name (empty to ungroup)",
    )

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        meta = _meta_for_collection(settings, self.collection_name)
        if meta is not None:
            meta.section = self.section_name
        return {'FINISHED'}


class BF_OT_MoveCollectionUp(Operator):
    """Move collection up in sort order"""
    bl_idname = "boneforge.move_collection_up"
    bl_label = "Move Up"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        meta = _meta_for_collection(settings, self.collection_name)
        if meta is not None:
            meta.priority = max(0, meta.priority - 15)
        return {'FINISHED'}


class BF_OT_MoveCollectionDown(Operator):
    """Move collection down in sort order"""
    bl_idname = "boneforge.move_collection_down"
    bl_label = "Move Down"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        meta = _meta_for_collection(settings, self.collection_name)
        if meta is not None:
            meta.priority += 15
        return {'FINISHED'}


class BF_OT_MoveSectionUp(Operator):
    """Move section up in sort order"""
    bl_idname = "boneforge.move_section_up"
    bl_label = "Move Section Up"
    bl_options = {'REGISTER', 'UNDO'}

    section_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        for s in settings.sections:
            if s.name == self.section_name:
                s.priority = max(0, s.priority - 15)
                break
        return {'FINISHED'}


class BF_OT_MoveSectionDown(Operator):
    """Move section down in sort order"""
    bl_idname = "boneforge.move_section_down"
    bl_label = "Move Section Down"
    bl_options = {'REGISTER', 'UNDO'}

    section_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        for s in settings.sections:
            if s.name == self.section_name:
                s.priority += 15
                break
        return {'FINISHED'}


class BF_OT_SetCollectionIcon(Operator):
    """Choose an icon for this collection button"""
    bl_idname = "boneforge.set_collection_icon"
    bl_label = "Set Icon"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    icon: StringProperty(
        name="Icon",
        description="Blender icon identifier",
        default='BONE_DATA',
    )

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        meta = _meta_for_collection(settings, self.collection_name)
        if meta is not None:
            meta.icon = self.icon
        return {'FINISHED'}


class BF_OT_RenameCollection(Operator):
    """Rename the display label for this collection"""
    bl_idname = "boneforge.rename_collection"
    bl_label = "Rename Collection Display"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    new_display_name: StringProperty(
        name="Display Name",
        description="New display label for this collection",
    )

    def invoke(self, context, event):
        settings = _get_settings(self, context)
        if settings is not None:
            meta = _meta_for_collection(settings, self.collection_name)
            if meta is not None:
                self.new_display_name = meta.display_name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        meta = _meta_for_collection(settings, self.collection_name)
        if meta is not None:
            meta.display_name = self.new_display_name
        return {'FINISHED'}


class BF_OT_SetCollectionColor(Operator):
    """Set the accent color for this collection"""
    bl_idname = "boneforge.set_collection_color"
    bl_label = "Set Accent Color"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    color: FloatVectorProperty(description="The collection's colour",
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.4, 0.6, 1.0),
    )

    def invoke(self, context, event):
        settings = _get_settings(self, context)
        if settings is not None:
            meta = _meta_for_collection(settings, self.collection_name)
            if meta is not None:
                self.color = meta.color
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = _get_settings(self, context)
        if settings is None:
            return {'CANCELLED'}
        meta = _meta_for_collection(settings, self.collection_name)
        if meta is not None:
            meta.color = self.color
        return {'FINISHED'}


# ── Configuration Popover ───────────────────────────────────────

class BF_PT_CollectionConfigPopover(Panel):
    """Popover panel for configuring a single collection"""
    bl_idname = "BF_PT_collection_config_popover"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    # The collection name is passed via a scene string property
    # set before the popover is opened.

    def draw_header(self, context):
        self.layout.label(text=T("Collection Settings"))

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if arm is None:
            layout.label(text=T("No active armature"), icon='ERROR')
            return
        if not hasattr(arm, 'boneforge_settings'):
            layout.label(text=T("BoneCraft settings not registered"), icon='ERROR')
            return

        settings = arm.boneforge_settings
        coll_name = context.scene.get("_bf_popover_coll", "")
        meta = _meta_for_collection(settings, coll_name)
        if meta is None:
            layout.label(text=T("Collection not found"), icon='ERROR')
            return

        layout.prop(meta, "display_name", text=T("Label"))
        layout.prop(meta, "icon", text=T("Icon"))
        layout.prop(meta, "color", text=T("Accent"))
        layout.prop(meta, "priority", text=T("Sort Order"))

        # Section assignment
        layout.separator()
        layout.label(text=T("Section:"))
        layout.prop(meta, "section", text="")

        # Move buttons
        row = layout.row(align=True)
        op = row.operator("boneforge.move_collection_up", icon='TRIA_UP', text="")
        op.collection_name = coll_name
        op = row.operator("boneforge.move_collection_down", icon='TRIA_DOWN', text="")
        op.collection_name = coll_name


# ── Main Panel ──────────────────────────────────────────────────

class BF_PT_CollectionPanel(Panel):
    """BoneCraft — Bone Collections"""
    bl_idname = "BF_PT_collection_panel"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text=T("BoneCraft Collections"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if arm is None:
            layout.label(text=T("Select an armature"), icon='INFO')
            return
        if not hasattr(arm, 'boneforge_settings'):
            layout.label(text=T("BoneCraft settings not registered"), icon='ERROR')
            return

        settings = arm.boneforge_settings
        _ensure_meta(settings, arm.data)

        # ── Toolbar row ─────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("boneforge.show_all_collections",
                      text="", icon='HIDE_OFF')
        row.operator("boneforge.hide_all_collections",
                      text="", icon='HIDE_ON')
        row.separator()
        row.operator("boneforge.add_section",
                      text="", icon='COLLECTION_NEW')

        # ── Bookmark slots (drawn by bookmarks module if loaded) ──
        # Hook point — bookmarks module draws here via append.

        # ── Sections and collections ────────────────────────────
        sorted_sections = _sorted_sections(settings)
        sorted_colls = _sorted_meta(settings)

        # Draw sectioned collections first
        drawn_coll_names = set()
        for sec in sorted_sections:
            sec_box = layout.box()
            # Section header row
            header = sec_box.row(align=True)
            icon = 'TRIA_RIGHT' if sec.collapsed else 'TRIA_DOWN'
            op = header.operator("boneforge.toggle_section_collapse",
                                  text="", icon=icon, emboss=False)
            op.section_name = sec.name
            header.label(text=sec.name)

            # Section controls
            op = header.operator("boneforge.move_section_up",
                                  text="", icon='TRIA_UP')
            op.section_name = sec.name
            op = header.operator("boneforge.move_section_down",
                                  text="", icon='TRIA_DOWN')
            op.section_name = sec.name
            op = header.operator("boneforge.remove_section",
                                  text="", icon='X')
            op.section_name = sec.name

            if sec.collapsed:
                continue

            # Draw collections in this section
            for meta in sorted_colls:
                if meta.section != sec.name:
                    continue
                drawn_coll_names.add(meta.coll_name)
                _draw_collection_button(sec_box, context, arm, meta)

        # Draw ungrouped collections
        ungrouped = [m for m in sorted_colls
                     if m.coll_name not in drawn_coll_names]
        if ungrouped:
            if sorted_sections:
                layout.separator()
            for meta in ungrouped:
                _draw_collection_button(layout, context, arm, meta)


def _draw_collection_button(parent_layout, context, arm, meta):
    """Draw a single collection button row with all controls."""
    coll = collection_by_name(arm.data, meta.coll_name)
    if coll is None:
        return

    row = parent_layout.row(align=True)

    # Color accent (uses a small color property display)
    sub = row.row(align=True)
    sub.scale_x = 0.15
    sub.prop(meta, "color", text="")

    # Visibility eye icon
    vis_icon = 'HIDE_OFF' if coll.is_visible else 'HIDE_ON'
    op = row.operator("boneforge.toggle_collection_vis",
                       text="", icon=vis_icon)
    op.collection_name = meta.coll_name

    # Main label button — shows display name with custom icon
    label = meta.display_name or meta.coll_name
    icon_val = meta.icon if meta.icon else 'BONE_DATA'
    op = row.operator("boneforge.select_collection_bones",
                       text=label, icon=icon_val)
    op.collection_name = meta.coll_name
    op.extend = False

    # Solo button
    op = row.operator("boneforge.solo_collection",
                       text="", icon='EVENT_S')
    op.collection_name = meta.coll_name

    # Config popover trigger — sets the scene string then opens popover
    op = row.operator("boneforge.rename_collection",
                       text="", icon='RENAME')
    op.collection_name = meta.coll_name


# ── Draw function for embedding in other panels ─────────────────

def draw_collection_list(layout, context):
    """Public entry point for other modules to embed the collection list.

    Used by the hotkey popup to replicate the panel contents.
    """
    arm = active_armature(context)
    if arm is None:
        layout.label(text=T("Select an armature to open the rig panel"),
                     icon='INFO')
        return
    if not hasattr(arm, 'boneforge_settings'):
        layout.label(text=T("BoneCraft settings not registered"), icon='ERROR')
        return

    settings = arm.boneforge_settings
    _ensure_meta(settings, arm.data)

    row = layout.row(align=True)
    row.operator("boneforge.show_all_collections", text="", icon='HIDE_OFF')
    row.operator("boneforge.hide_all_collections", text="", icon='HIDE_ON')
    row.separator()
    row.operator("boneforge.add_section", text="", icon='COLLECTION_NEW')

    sorted_sections = _sorted_sections(settings)
    sorted_colls = _sorted_meta(settings)

    drawn_collection_names = set()
    for sec in sorted_sections:
        sec_box = layout.box()
        header = sec_box.row(align=True)
        icon = 'TRIA_RIGHT' if sec.collapsed else 'TRIA_DOWN'
        op = header.operator("boneforge.toggle_section_collapse",
                              text="", icon=icon, emboss=False)
        op.section_name = sec.name
        header.label(text=sec.name)
        if not sec.collapsed:
            for meta in sorted_colls:
                if meta.section == sec.name:
                    drawn_collection_names.add(meta.coll_name)
                    _draw_collection_button(sec_box, context, arm, meta)

    for meta in sorted_colls:
        if meta.coll_name not in drawn_collection_names:
            _draw_collection_button(layout, context, arm, meta)


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_CollectionMeta,
    BF_SectionItem,
    BF_ArmatureSettings,
    BF_OT_ToggleCollectionVisibility,
    BF_OT_SoloCollection,
    BF_OT_SelectCollectionBones,
    BF_OT_ShowAllCollections,
    BF_OT_HideAllCollections,
    BF_OT_AddSection,
    BF_OT_RemoveSection,
    BF_OT_ToggleSectionCollapse,
    BF_OT_AssignCollectionToSection,
    BF_OT_MoveCollectionUp,
    BF_OT_MoveCollectionDown,
    BF_OT_MoveSectionUp,
    BF_OT_MoveSectionDown,
    BF_OT_SetCollectionIcon,
    BF_OT_RenameCollection,
    BF_OT_SetCollectionColor,
    BF_PT_CollectionConfigPopover,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.boneforge_settings = bpy.props.PointerProperty(
        type=BF_ArmatureSettings,
        name="BoneCraft Settings",
        description="BoneCraft collection and bookmark settings for this armature",
    )

    register_draw("collection_list", draw_collection_list)


def unregister():
    unregister_draw("collection_list")

    del bpy.types.Object.boneforge_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
