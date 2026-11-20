"""BoneCraft VRChat — Batch Rename Tools.

Four independent operators for bulk renaming bones:
1. Find and Replace
2. Add/Remove Prefix
3. Add/Remove Suffix
4. Regex Replace

All operations are single undoable steps with preview support.

Category: VRChat Naming.
"""

import re

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.i18n import T


# ── Helpers ──────────────────────────────────────────────────────

def _get_bone_list(armature, selected_only=False):
    """Return list of bone names to process."""
    if selected_only:
        return [bone.name for bone in armature.data.bones if bone.select]
    return [bone.name for bone in armature.data.bones]


def _validate_rename_map(armature, new_names_map: dict, operator) -> bool:
    """Validate a batch rename won't create duplicates or empty names.

    Args:
        armature: The armature being renamed
        new_names_map: Dict mapping old_name -> new_name (only changed names)
        operator: The calling operator (for self.report)

    Returns:
        True if validation passes, False if blocked
    """
    existing_names = {b.name for b in armature.data.bones}
    # Names that will be freed by renames
    freed_names = set(new_names_map.keys())
    # Names that will be occupied after renames
    future_names = (existing_names - freed_names) | set(new_names_map.values())

    duplicates = []
    empty_names = []

    for old_name, new_name in new_names_map.items():
        if not new_name or not new_name.strip():
            empty_names.append(old_name)
        elif new_name in (existing_names - freed_names) or list(new_names_map.values()).count(new_name) > 1:
            duplicates.append(f"{old_name} -> {new_name}")

    if empty_names:
        operator.report({'ERROR'}, "Rename blocked — would create empty bone name")
        return False

    if duplicates:
        operator.report({'ERROR'},
                       f"Rename blocked — would create duplicates: {', '.join(duplicates[:5])}")
        return False

    return True


# ── Find and Replace ─────────────────────────────────────────────

class BF_OT_VRC_FindReplace(Operator):
    """Find and replace text in bone names"""
    bl_idname = "boneforge.vrc_find_replace"
    bl_label = "Find and Replace"
    bl_options = {"REGISTER", "UNDO"}

    search_text: StringProperty(
        name="Find",
        description="Text to search for",
        default="",
    )
    replace_text: StringProperty(
        name="Replace With",
        description="Text to replace with",
        default="",
    )
    case_sensitive: BoolProperty(
        name="Case Sensitive",
        description="Match case exactly",
        default=False,
    )
    selected_only: BoolProperty(
        name="Selected Only",
        description="Only rename selected bones",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        col = layout.column()
        col.prop(self, "search_text")
        col.prop(self, "replace_text")
        col.prop(self, "case_sensitive")
        col.prop(self, "selected_only")

        if arm is not None:
            # Preview count
            bones = _get_bone_list(arm, self.selected_only)
            match_count = 0
            for bone_name in bones:
                if self.case_sensitive:
                    if self.search_text in bone_name:
                        match_count += 1
                else:
                    if self.search_text.lower() in bone_name.lower():
                        match_count += 1

            col.separator()
            col.label(text=f"Would match: {match_count} bone(s)")

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        if not self.search_text:
            self.report({'WARNING'}, "Search text is empty")
            return {'CANCELLED'}

        bones = _get_bone_list(arm, self.selected_only)

        # Build rename map (only changed names)
        new_names_map = {}
        for bone_name in bones:
            bone = arm.data.bones[bone_name]
            if self.case_sensitive:
                if self.search_text in bone.name:
                    new_name = bone.name.replace(self.search_text, self.replace_text)
                else:
                    continue
            else:
                pattern = re.compile(re.escape(self.search_text), re.IGNORECASE)
                new_name = pattern.sub(self.replace_text, bone.name)
                if new_name == bone.name:
                    continue

            new_names_map[bone.name] = new_name

        if not _validate_rename_map(arm, new_names_map, self):
            return {'CANCELLED'}

        # Apply renames
        count = 0
        for bone_name, new_name in new_names_map.items():
            arm.data.bones[bone_name].name = new_name
            count += 1

        self.report({'INFO'}, f"Replaced in {count} bone(s)")
        return {'FINISHED'}


# ── Prefix Manager ───────────────────────────────────────────────

class BF_OT_VRC_AddPrefix(Operator):
    """Add a prefix to bone names"""
    bl_idname = "boneforge.vrc_add_prefix"
    bl_label = "Add Prefix"
    bl_options = {"REGISTER", "UNDO"}

    prefix: StringProperty(
        name="Prefix",
        description="Prefix to add",
        default="",
    )
    selected_only: BoolProperty(
        name="Selected Only",
        description="Only rename selected bones",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        col = layout.column()
        col.prop(self, "prefix")
        col.prop(self, "selected_only")

        if arm is not None and self.prefix:
            bones = _get_bone_list(arm, self.selected_only)
            col.separator()
            col.label(text=f"Will affect: {len(bones)} bone(s)")
            if bones:
                col.label(text=f"  Example: {self.prefix}{bones[0]}")

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        if not self.prefix:
            self.report({'WARNING'}, "Prefix is empty")
            return {'CANCELLED'}

        bones = _get_bone_list(arm, self.selected_only)
        new_names_map = {name: self.prefix + name for name in bones}

        if not _validate_rename_map(arm, new_names_map, self):
            return {'CANCELLED'}

        for bone_name, new_name in new_names_map.items():
            arm.data.bones[bone_name].name = new_name

        self.report({'INFO'}, f"Added prefix to {len(new_names_map)} bone(s)")
        return {'FINISHED'}


class BF_OT_VRC_RemovePrefix(Operator):
    """Remove a prefix from bone names"""
    bl_idname = "boneforge.vrc_remove_prefix"
    bl_label = "Remove Prefix"
    bl_options = {"REGISTER", "UNDO"}

    prefix: StringProperty(
        name="Prefix",
        description="Prefix to remove",
        default="",
    )
    selected_only: BoolProperty(
        name="Selected Only",
        description="Only rename selected bones",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        col = layout.column()
        col.prop(self, "prefix")
        col.prop(self, "selected_only")

        if arm is not None and self.prefix:
            bones = _get_bone_list(arm, self.selected_only)
            match_count = 0
            for bone_name in bones:
                if bone_name.startswith(self.prefix):
                    match_count += 1

            col.separator()
            col.label(text=f"Will match: {match_count} bone(s)")
            if match_count > 0:
                for bone_name in bones:
                    if bone_name.startswith(self.prefix):
                        col.label(text=f"  {bone_name[len(self.prefix):]}", icon='NONE')
                        break

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        if not self.prefix:
            self.report({'WARNING'}, "Prefix is empty")
            return {'CANCELLED'}

        bones = _get_bone_list(arm, self.selected_only)
        new_names_map = {}
        for bone_name in bones:
            if bone_name.startswith(self.prefix):
                new_names_map[bone_name] = bone_name[len(self.prefix):]

        if not _validate_rename_map(arm, new_names_map, self):
            return {'CANCELLED'}

        for bone_name, new_name in new_names_map.items():
            arm.data.bones[bone_name].name = new_name

        self.report({'INFO'}, f"Removed prefix from {len(new_names_map)} bone(s)")
        return {'FINISHED'}


# ── Suffix Manager ───────────────────────────────────────────────

class BF_OT_VRC_AddSuffix(Operator):
    """Add a suffix to bone names"""
    bl_idname = "boneforge.vrc_add_suffix"
    bl_label = "Add Suffix"
    bl_options = {"REGISTER", "UNDO"}

    suffix: StringProperty(
        name="Suffix",
        description="Suffix to add",
        default="",
    )
    selected_only: BoolProperty(
        name="Selected Only",
        description="Only rename selected bones",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "selected_only")

        if arm is not None and self.suffix:
            bones = _get_bone_list(arm, self.selected_only)
            col.separator()
            col.label(text=f"Will affect: {len(bones)} bone(s)")
            if bones:
                col.label(text=f"  Example: {bones[0]}{self.suffix}")

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        if not self.suffix:
            self.report({'WARNING'}, "Suffix is empty")
            return {'CANCELLED'}

        bones = _get_bone_list(arm, self.selected_only)
        new_names_map = {name: name + self.suffix for name in bones}

        if not _validate_rename_map(arm, new_names_map, self):
            return {'CANCELLED'}

        for bone_name, new_name in new_names_map.items():
            arm.data.bones[bone_name].name = new_name

        self.report({'INFO'}, f"Added suffix to {len(new_names_map)} bone(s)")
        return {'FINISHED'}


class BF_OT_VRC_RemoveSuffix(Operator):
    """Remove a suffix from bone names"""
    bl_idname = "boneforge.vrc_remove_suffix"
    bl_label = "Remove Suffix"
    bl_options = {"REGISTER", "UNDO"}

    suffix: StringProperty(
        name="Suffix",
        description="Suffix to remove",
        default="",
    )
    selected_only: BoolProperty(
        name="Selected Only",
        description="Only rename selected bones",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "selected_only")

        if arm is not None and self.suffix:
            bones = _get_bone_list(arm, self.selected_only)
            match_count = 0
            for bone_name in bones:
                if bone_name.endswith(self.suffix):
                    match_count += 1

            col.separator()
            col.label(text=f"Will match: {match_count} bone(s)")
            if match_count > 0:
                for bone_name in bones:
                    if bone_name.endswith(self.suffix):
                        col.label(text=f"  {bone_name[:-len(self.suffix)]}", icon='NONE')
                        break

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        if not self.suffix:
            self.report({'WARNING'}, "Suffix is empty")
            return {'CANCELLED'}

        bones = _get_bone_list(arm, self.selected_only)
        new_names_map = {}
        for bone_name in bones:
            if bone_name.endswith(self.suffix):
                new_names_map[bone_name] = bone_name[:-len(self.suffix)]

        if not _validate_rename_map(arm, new_names_map, self):
            return {'CANCELLED'}

        for bone_name, new_name in new_names_map.items():
            arm.data.bones[bone_name].name = new_name

        self.report({'INFO'}, f"Removed suffix from {len(new_names_map)} bone(s)")
        return {'FINISHED'}


# ── Regex Replace ────────────────────────────────────────────────

class BF_OT_VRC_RegexReplace(Operator):
    """Replace using regex pattern"""
    bl_idname = "boneforge.vrc_regex_replace"
    bl_label = "Regex Replace"
    bl_options = {"REGISTER", "UNDO"}

    pattern: StringProperty(
        name="Pattern",
        description="Regex pattern to match",
        default="",
    )
    replacement: StringProperty(
        name="Replacement",
        description="Replacement string (supports groups: \\1, \\2, etc.)",
        default="",
    )
    selected_only: BoolProperty(
        name="Selected Only",
        description="Only rename selected bones",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        col = layout.column()
        col.prop(self, "pattern")
        col.prop(self, "replacement")
        col.prop(self, "selected_only")

        if arm is not None and self.pattern:
            try:
                regex = re.compile(self.pattern)
                bones = _get_bone_list(arm, self.selected_only)
                matches = []

                for bone_name in bones:
                    if regex.search(bone_name):
                        new_name = regex.sub(self.replacement, bone_name)
                        matches.append((bone_name, new_name))

                col.separator()
                col.label(text=f"Would match: {len(matches)} bone(s)")
                if matches:
                    for old, new in matches[:3]:
                        col.label(text=f"  {old} → {new}", icon='NONE')
                    if len(matches) > 3:
                        col.label(text=f"  ... and {len(matches) - 3} more")

            except re.error as e:
                col.separator()
                col.label(text=f"Invalid regex: {str(e)[:50]}", icon='ERROR')

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        if not self.pattern:
            self.report({'WARNING'}, "Pattern is empty")
            return {'CANCELLED'}

        try:
            regex = re.compile(self.pattern)
        except re.error as e:
            self.report({'ERROR'}, f"Invalid regex: {e}")
            return {'CANCELLED'}

        bones = _get_bone_list(arm, self.selected_only)
        new_names_map = {}
        for bone_name in bones:
            new_name = regex.sub(self.replacement, bone_name)
            if new_name != bone_name:
                new_names_map[bone_name] = new_name

        if not _validate_rename_map(arm, new_names_map, self):
            return {'CANCELLED'}

        for bone_name, new_name in new_names_map.items():
            arm.data.bones[bone_name].name = new_name

        self.report({'INFO'}, f"Replaced in {len(new_names_map)} bone(s)")
        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_batch_rename(Panel):
    """Batch rename tools panel"""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_batch_rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Batch Rename"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout

        # Find and Replace
        col = layout.column(align=True)
        col.label(text=T("Find and Replace"))
        col.operator("boneforge.vrc_find_replace", text=T("Find and Replace"),
                    icon='SORTALPHA')

        # Prefix
        col.separator()
        col.label(text=T("Prefix"))
        col.operator("boneforge.vrc_add_prefix", text=T("Add Prefix"), icon='ADD')
        col.operator("boneforge.vrc_remove_prefix", text=T("Remove Prefix"), icon='REMOVE')

        # Suffix
        col.separator()
        col.label(text=T("Suffix"))
        col.operator("boneforge.vrc_add_suffix", text=T("Add Suffix"), icon='ADD')
        col.operator("boneforge.vrc_remove_suffix", text=T("Remove Suffix"), icon='REMOVE')

        # Regex
        col.separator()
        col.label(text=T("Advanced"))
        col.operator("boneforge.vrc_regex_replace", text=T("Regex Replace"),
                    icon='EXPERIMENTAL')


# ── Registration ─────────────────────────────────────────────────

_classes = [
    BF_OT_VRC_FindReplace,
    BF_OT_VRC_AddPrefix,
    BF_OT_VRC_RemovePrefix,
    BF_OT_VRC_AddSuffix,
    BF_OT_VRC_RemoveSuffix,
    BF_OT_VRC_RegexReplace,
    BONEFORGE_PT_vrc_batch_rename,
]


def register():
    """Register batch rename module."""
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister batch rename module."""
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
