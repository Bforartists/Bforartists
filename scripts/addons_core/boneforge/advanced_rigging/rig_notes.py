"""BoneCraft Phase 2C — Rig Annotation and Documentation.

Annotation system for documenting rig controls with viewport overlays.
Supports Info, Warning, Limit, and Do Not Key note types.
Category: Rig Documentation.
"""

import bpy
import json
import blf
from bpy_extras import view3d_utils
from bpy.props import (
    StringProperty,
    EnumProperty,
)
from boneforge.i18n import T
from bpy.types import PropertyGroup, Operator, Panel
import logging

logger = logging.getLogger(__name__)


NOTE_TYPE_ENUM = [
    ('INFO', "Info", "Informational note", 'INFO', 0),
    ('WARNING', "Warning", "Warning note", 'ERROR', 1),
    ('LIMIT', "Limit", "Limitation note", 'LOCKED', 2),
    ('DO_NOT_KEY', "Do Not Key", "Should not be keyframed", 'KEYPOINTTYPE', 3),
]

VISIBILITY_ENUM = [
    ('ALWAYS', "Always", "Always visible"),
    ('HOVER', "On Hover", "Visible when hovering"),
    ('HIDDEN', "Hidden", "Not displayed"),
]

ICON_MAP = {
    'INFO': 'INFO',
    'WARNING': 'ERROR',
    'LIMIT': 'LOCKED',
    'DO_NOT_KEY': 'KEYPOINTTYPE',
}


class BF_RigNote(PropertyGroup):
    """Single annotation note on a bone."""
    bone_name: StringProperty(name="Bone Name")
    note_type: EnumProperty(
        name="Type",
        items=NOTE_TYPE_ENUM,
        default='INFO'
    )
    text: StringProperty(
        name="Note Text",
        default="Note"
    )
    visibility: EnumProperty(
        name="Visibility",
        items=VISIBILITY_ENUM,
        default='ALWAYS'
    )


class BF_OT_AddRigNote(Operator):
    """Add annotation note to a bone."""
    bl_idname = "boneforge.add_rig_note"
    bl_label = "Add Rig Note"
    bl_options = {'REGISTER', 'UNDO'}

    bone_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Bone Name")
    note_type: EnumProperty(description='What the note marks: information, a warning, a limit, or a bone not to key', name="Type", items=NOTE_TYPE_ENUM, default='INFO')
    text: StringProperty(description="The note's text", name="Text", default="New note")
    visibility: EnumProperty(description='When the note shows in the viewport', name="Visibility", items=VISIBILITY_ENUM, default='ALWAYS')

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.object

        # Determine target bone
        if not self.bone_name:
            if context.active_pose_bone:
                self.bone_name = context.active_pose_bone.name
            else:
                self.report({'ERROR'}, "No bone selected")
                return {'CANCELLED'}

        # Load or initialize notes
        if "boneforge_p2c_annotations" not in armature:
            notes_data = {"notes": []}
        else:
            try:
                notes_data = json.loads(armature["boneforge_p2c_annotations"])
            except (json.JSONDecodeError, TypeError):
                notes_data = {"notes": []}

        # Add note
        note = {
            "bone_name": self.bone_name,
            "note_type": self.note_type,
            "text": self.text,
            "visibility": self.visibility
        }
        notes_data["notes"].append(note)

        armature["boneforge_p2c_annotations"] = json.dumps(notes_data)
        self.report({'INFO'}, f"Added note to {self.bone_name}")
        return {'FINISHED'}


class BF_OT_RemoveRigNote(Operator):
    """Remove a rig note."""
    bl_idname = "boneforge.remove_rig_note"
    bl_label = "Remove Rig Note"
    bl_options = {'REGISTER', 'UNDO'}

    note_index: bpy.props.IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Note Index", default=0)

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_annotations" not in armature:
            self.report({'ERROR'}, "No annotations on this armature")
            return {'CANCELLED'}

        try:
            notes_data = json.loads(armature["boneforge_p2c_annotations"])
        except (json.JSONDecodeError, TypeError):
            self.report({'ERROR'}, "Corrupted annotation data")
            return {'CANCELLED'}

        notes = notes_data.get("notes", [])
        if 0 <= self.note_index < len(notes):
            removed = notes.pop(self.note_index)
            armature["boneforge_p2c_annotations"] = json.dumps(notes_data)
            self.report({'INFO'}, f"Removed note from {removed['bone_name']}")
            return {'FINISHED'}

        self.report({'ERROR'}, "Invalid note index")
        return {'CANCELLED'}


class BF_OT_EditRigNote(Operator):
    """Edit an existing rig note."""
    bl_idname = "boneforge.edit_rig_note"
    bl_label = "Edit Rig Note"
    bl_options = {'REGISTER', 'UNDO'}

    note_index: bpy.props.IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Note Index", default=0)
    note_type: EnumProperty(description='What the note marks: information, a warning, a limit, or a bone not to key', name="Type", items=NOTE_TYPE_ENUM, default='INFO')
    text: StringProperty(description="The note's text", name="Text", default="")
    visibility: EnumProperty(description='When the note shows in the viewport', name="Visibility", items=VISIBILITY_ENUM, default='ALWAYS')

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_annotations" not in armature:
            self.report({'ERROR'}, "No annotations on this armature")
            return {'CANCELLED'}

        try:
            notes_data = json.loads(armature["boneforge_p2c_annotations"])
        except (json.JSONDecodeError, TypeError):
            self.report({'ERROR'}, "Corrupted annotation data")
            return {'CANCELLED'}

        notes = notes_data.get("notes", [])
        if 0 <= self.note_index < len(notes):
            notes[self.note_index]["note_type"] = self.note_type
            notes[self.note_index]["text"] = self.text
            notes[self.note_index]["visibility"] = self.visibility
            armature["boneforge_p2c_annotations"] = json.dumps(notes_data)
            self.report({'INFO'}, "Note updated")
            return {'FINISHED'}

        self.report({'ERROR'}, "Invalid note index")
        return {'CANCELLED'}


# Viewport drawing handler
def _draw_rig_notes_3d(scene=None, depsgraph=None):
    """Draw rig note overlays in 3D viewport.

    Registered on ``depsgraph_update_post``, which invokes handlers with
    ``(scene, depsgraph)``.  Both are accepted but unused — we read the
    active object off ``bpy.context`` instead.
    """
    context = bpy.context
    if not context.object or context.object.type != 'ARMATURE':
        return

    armature = context.object

    if "boneforge_p2c_annotations" not in armature:
        return

    try:
        notes_data = json.loads(armature["boneforge_p2c_annotations"])
    except (json.JSONDecodeError, TypeError):
        return

    notes = notes_data.get("notes", [])

    # Filter only ALWAYS visible notes
    visible_notes = [n for n in notes if n.get("visibility") == "ALWAYS"]

    if not visible_notes:
        return

    # Get region for viewport drawing
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            region = area.regions[4] if len(area.regions) > 4 else None
            if not region:
                break

            # Draw text for each note
            blf.size(0, 12)
            blf.color(0, 1.0, 1.0, 0.0, 1.0)  # Yellow text

            for note in visible_notes:
                bone_name = note.get("bone_name", "")
                text = note.get("text", "")

                if bone_name not in armature.pose.bones:
                    continue

                bone = armature.data.bones[bone_name]
                bone_head_world = armature.matrix_world @ bone.head_local

                # Convert 3D world position to 2D screen position
                try:
                    screen_pos = view3d_utils.location_3d_to_region_2d(
                        region, context.space_data.region_3d, bone_head_world
                    )
                    if screen_pos:
                        blf.position(0, int(screen_pos.x), int(screen_pos.y), 0)
                        blf.draw(0, text)
                except (RuntimeError, AttributeError) as exc:
                    logger.debug("./advanced_rigging/rig_notes.py suppressed (RuntimeError, AttributeError): %s", exc)
            break


def _register_rig_notes_handler():
    """Register viewport drawing handler."""
    if _draw_rig_notes_3d not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_draw_rig_notes_3d)


def _unregister_rig_notes_handler():
    """Unregister viewport drawing handler."""
    if _draw_rig_notes_3d in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_draw_rig_notes_3d)


class BONEFORGE_PT_p2c_rig_notes(Panel):
    """Rig Notes panel in Rig Construction tab."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_rig_notes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Rig Notes"))

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def draw(self, context):
        layout = self.layout
        armature = context.object

        # Quick add button
        row = layout.row()
        op = row.operator("boneforge.add_rig_note", text=T("Add Note"), icon='ADD')
        if context.active_pose_bone:
            op.bone_name = context.active_pose_bone.name

        # List existing notes
        if "boneforge_p2c_annotations" in armature:
            try:
                notes_data = json.loads(armature["boneforge_p2c_annotations"])
                notes = notes_data.get("notes", [])

                if notes:
                    layout.label(text=T("Annotations"))

                    for idx, note in enumerate(notes):
                        box = layout.box()
                        row = box.row()

                        # Icon and bone name
                        icon = ICON_MAP.get(note.get("note_type"), "INFO")
                        row.label(text=note["bone_name"], icon=icon)

                        # Visibility indicator
                        vis = note.get("visibility", "ALWAYS")
                        row.label(text=f"({vis})", text_ctxt="Visibility")

                        # Text
                        box.label(text=note["text"])

                        # Remove button
                        row = box.row()
                        op = row.operator("boneforge.remove_rig_note", text=T("Remove"), icon='X')
                        op.note_index = idx

            except (json.JSONDecodeError, TypeError):
                layout.label(text=T("Corrupted annotation data"), icon='ERROR')


class BONEFORGE_PT_p2c_rig_readme(Panel):
    """Rig Readme sub-panel showing documentation."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_rig_readme"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Rig Readme"))

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        armature = context.object

        if "boneforge_p2c_annotations" not in armature:
            layout.label(text=T("No annotations"), icon='INFO')
            return

        try:
            notes_data = json.loads(armature["boneforge_p2c_annotations"])
        except (json.JSONDecodeError, TypeError):
            layout.label(text=T("Corrupted annotation data"), icon='ERROR')
            return

        notes = notes_data.get("notes", [])

        # Filter for ALWAYS visible notes
        always_notes = [n for n in notes if n.get("visibility") == "ALWAYS"]

        if not always_notes:
            layout.label(text=T("No public notes"), icon='INFO')
            return

        # Group by bone
        bones_to_notes = {}
        for note in always_notes:
            bone_name = note.get("bone_name", "Unknown")
            if bone_name not in bones_to_notes:
                bones_to_notes[bone_name] = []
            bones_to_notes[bone_name].append(note)

        # Display grouped
        for bone_name, bone_notes in sorted(bones_to_notes.items()):
            box = layout.box()
            box.label(text=bone_name, icon='BONE_DATA')

            for note in bone_notes:
                row = box.row()
                icon = ICON_MAP.get(note.get("note_type"), "INFO")
                row.label(text=note["text"], icon=icon)


def register():
    """Register rig notes classes and properties."""
    bpy.utils.register_class(BF_RigNote)
    bpy.utils.register_class(BF_OT_AddRigNote)
    bpy.utils.register_class(BF_OT_RemoveRigNote)
    bpy.utils.register_class(BF_OT_EditRigNote)
    # Neither BONEFORGE_PT_p2c_rig_notes nor BONEFORGE_PT_p2c_rig_readme
    # are registered as standalone panels. Both are delegated through
    # taskboard/sidebar.py: rig_notes via BF_PT_sb_rig_notes (Overview hub)
    # and rig_readme via BF_PT_sb_rig_readme (Inspect hub).

    _register_rig_notes_handler()


def unregister():
    """Unregister rig notes classes and properties."""
    _unregister_rig_notes_handler()

    bpy.utils.unregister_class(BF_OT_EditRigNote)
    bpy.utils.unregister_class(BF_OT_RemoveRigNote)
    bpy.utils.unregister_class(BF_OT_AddRigNote)
    bpy.utils.unregister_class(BF_RigNote)
