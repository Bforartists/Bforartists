"""BoneCraft Phase 2 — Pose Library with Thumbnail Previews.

Visual pose browser panel with rendered thumbnails, save/apply/mirror,
blend apply, category filtering, and .bfpose file I/O.

Pose data is dual-stored: runtime PropertyGroup + JSON custom property
on the armature Object for portability.
"""

import bpy
import json
import base64
from bpy.props import (
    CollectionProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from boneforge.i18n import T
from mathutils import Quaternion, Vector

import logging

logger = logging.getLogger(__name__)

from boneforge.core import (
    active_armature,
    read_custom_json,
    write_custom_json,
    addon_prefs,
)


_CUSTOM_PROP_KEY = "boneforge_pose_library"


# ── Mirror helpers ──────────────────────────────────────────────

_MIRROR_SUFFIXES = [
    ('.L', '.R'),
    ('.l', '.r'),
    ('_L', '_R'),
    ('_l', '_r'),
    ('Left', 'Right'),
    ('left', 'right'),
]


def _mirror_bone_name(name):
    """Swap left/right naming in a bone name. Returns the mirrored name."""
    for left, right in _MIRROR_SUFFIXES:
        if name.endswith(left):
            return name[:-len(left)] + right
        if name.endswith(right):
            return name[:-len(right)] + left
    return name


def _mirror_transform(loc, rot):
    """Mirror a transform across the YZ plane (negate X location, mirror quat)."""
    mirrored_location = (-loc[0], loc[1], loc[2])
    # Mirror quaternion: negate Y and Z components
    mirrored_rotation = (rot[0], -rot[1], -rot[2], rot[3])
    return mirrored_location, mirrored_rotation


# ── Persistence ─────────────────────────────────────────────────

def _capture_bone_transforms(context, arm_obj):
    """Capture transforms of selected pose bones as a serializable dict."""
    data = {}
    for pbone in context.selected_pose_bones or []:
        rot = pbone.rotation_quaternion
        data[pbone.name] = {
            "loc": list(pbone.location),
            "rot": [rot.w, rot.x, rot.y, rot.z],
            "scale": list(pbone.scale),
        }
    return data


def _poses_to_json(settings):
    """Serialize all poses in the PropertyGroup to a JSON-ready dict."""
    poses = []
    for entry in settings.poses:
        poses.append({
            "name": entry.name,
            "category": entry.category,
            "bones": json.loads(entry.bone_data_json) if entry.bone_data_json else {},
            "thumbnail_b64": entry.thumbnail_b64 if entry.thumbnail_b64 else None,
        })
    return {"poses": poses}


def _persist_poses(arm_obj, settings):
    """Write all pose data to JSON custom property."""
    write_custom_json(arm_obj, _CUSTOM_PROP_KEY, _poses_to_json(settings))


def _load_poses(arm_obj, settings):
    """Load pose data from JSON custom property into the PropertyGroup."""
    data = read_custom_json(arm_obj, _CUSTOM_PROP_KEY)
    if data is None or "poses" not in data:
        return
    settings.poses.clear()
    for pose_data in data["poses"]:
        entry = settings.poses.add()
        entry.name = pose_data.get("name", "Untitled")
        entry.category = pose_data.get("category", "")
        entry.bone_data_json = json.dumps(pose_data.get("bones", {}))
        entry.thumbnail_b64 = pose_data.get("thumbnail_b64", "") or ""


def _ensure_poses(arm_obj, settings):
    """Lazy-load poses from custom property if the runtime collection is empty."""
    if len(settings.poses) == 0:
        _load_poses(arm_obj, settings)


# ── Thumbnail helpers ───────────────────────────────────────────

def _try_render_thumbnail(context, entry):
    """Deferred thumbnail rendering via app timer."""
    def _timer_callback():
        try:
            # Attempt a viewport snapshot via opengl render to a temp image
            original_path = context.scene.render.filepath
            original_resolution_x = context.scene.render.resolution_x
            original_resolution_y = context.scene.render.resolution_y
            original_resolution_percentage = context.scene.render.resolution_percentage

            context.scene.render.resolution_x = 128
            context.scene.render.resolution_y = 128
            context.scene.render.resolution_percentage = 100

            # Use opengl render (viewport render) to capture
            bpy.ops.render.opengl(write_still=False)

            img = bpy.data.images.get("Render Result")
            if img is not None and img.has_data:
                # Save to temp file and encode
                import tempfile
                import os
                tmp = os.path.join(tempfile.gettempdir(), "bf_thumb.png")
                img.save_render(tmp)
                with open(tmp, 'rb') as f:
                    entry.thumbnail_b64 = base64.b64encode(f.read()).decode('ascii')
                try:
                    os.remove(tmp)
                except OSError as exc:
                    logger.debug("./animation/pose_library.py suppressed OSError: %s", exc)

            # Restore render settings
            context.scene.render.filepath = original_path
            context.scene.render.resolution_x = original_resolution_x
            context.scene.render.resolution_y = original_resolution_y
            context.scene.render.resolution_percentage = original_resolution_percentage
        except Exception:
            # Thumbnail rendering is best-effort
            entry.thumbnail_b64 = ""
        return None  # Do not repeat

    bpy.app.timers.register(_timer_callback, first_interval=0.0)


# ── PropertyGroups ──────────────────────────────────────────────

class BF_PoseEntry(bpy.types.PropertyGroup):
    """Single saved pose in the library."""
    name: StringProperty(name="Name", default="Untitled")
    category: StringProperty(
        name="Category",
        description="Tag for filtering (e.g., hands, face, walk)",
        default="",
    )
    bone_data_json: StringProperty(
        name="Bone Data",
        description="JSON-serialized bone transforms",
        default="{}",
    )
    thumbnail_b64: StringProperty(
        name="Thumbnail",
        description="Base64-encoded 128x128 PNG",
        default="",
    )


class BF_PoseLibrary(bpy.types.PropertyGroup):
    """Pose library container on the armature object."""
    poses: CollectionProperty(type=BF_PoseEntry)
    active_index: IntProperty(
        name="Active Pose",
        description="Index of the currently selected pose",
        default=0,
        min=0,
    )
    filter_category: StringProperty(
        name="Filter",
        description="Show only poses matching this category (empty = show all)",
        default="",
    )


# ── Operators ───────────────────────────────────────────────────

class BF_OT_PoseSave(bpy.types.Operator):
    """Save the current pose of selected bones to the library"""
    bl_idname = "boneforge.pose_save"
    bl_label = "Save Pose"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(description='Name of the saved pose', name="Name", default="New Pose")
    category: StringProperty(description='Category to file the pose under', name="Category", default="")

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return (arm is not None and context.mode == 'POSE'
                and context.selected_pose_bones)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        bone_data = _capture_bone_transforms(context, arm)
        if not bone_data:
            self.report({'WARNING'}, "No bones selected to save")
            return {'CANCELLED'}

        entry = settings.poses.add()
        entry.name = self.name
        entry.category = self.category
        entry.bone_data_json = json.dumps(bone_data)
        entry.thumbnail_b64 = ""

        settings.active_index = len(settings.poses) - 1

        # Deferred thumbnail rendering
        _try_render_thumbnail(context, entry)

        _persist_poses(arm, settings)
        self.report({'INFO'}, f"Saved pose '{self.name}'")
        return {'FINISHED'}


class BF_OT_PoseApply(bpy.types.Operator):
    """Apply the selected pose to matching bones"""
    bl_idname = "boneforge.pose_apply"
    bl_label = "Apply Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None or context.mode != 'POSE':
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        if settings.active_index >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        entry = settings.poses[settings.active_index]
        bones_data = json.loads(entry.bone_data_json) if entry.bone_data_json else {}
        applied = 0
        skipped = []

        for bname, xform in bones_data.items():
            pbone = arm.pose.bones.get(bname)
            if pbone is None:
                skipped.append(bname)
                continue
            pbone.location = Vector(xform["loc"])
            pbone.rotation_quaternion = Quaternion(xform["rot"])
            pbone.scale = Vector(xform["scale"])
            applied += 1

        msg = f"Applied '{entry.name}'"
        if skipped:
            extra = f" (+{len(skipped) - 2} more)" if len(skipped) > 2 else ""
            names = ", ".join(skipped[:2])
            msg += f" — skipped {len(skipped)} missing bones: {names}{extra}"
        self.report({'INFO'}, msg)
        context.view_layer.update()
        return {'FINISHED'}


class BF_OT_PoseApplyMirrored(bpy.types.Operator):
    """Apply the selected pose with left/right sides swapped"""
    bl_idname = "boneforge.pose_apply_mirrored"
    bl_label = "Apply Mirrored"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None or context.mode != 'POSE':
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        if settings.active_index >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        entry = settings.poses[settings.active_index]
        bones_data = json.loads(entry.bone_data_json) if entry.bone_data_json else {}
        applied = 0
        skipped = []

        for bname, xform in bones_data.items():
            target_name = _mirror_bone_name(bname)
            pbone = arm.pose.bones.get(target_name)
            if pbone is None:
                skipped.append(target_name)
                continue
            mirrored_location, mirrored_rotation = _mirror_transform(xform["loc"], xform["rot"])
            pbone.location = Vector(mirrored_location)
            pbone.rotation_quaternion = Quaternion(mirrored_rotation)
            pbone.scale = Vector(xform["scale"])
            applied += 1

        msg = f"Applied mirrored '{entry.name}'"
        if skipped:
            msg += f" — skipped {len(skipped)} missing bones"
        self.report({'INFO'}, msg)
        context.view_layer.update()
        return {'FINISHED'}


class BF_OT_PoseApplyBlended(bpy.types.Operator):
    """Apply the selected pose at a user-defined blend strength"""
    bl_idname = "boneforge.pose_apply_blended"
    bl_label = "Apply Blended"
    bl_options = {'REGISTER', 'UNDO'}

    blend: FloatProperty(
        name="Blend %",
        description="Strength of the pose application (0-100%)",
        default=50.0,
        min=0.0,
        max=100.0,
    )

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None or context.mode != 'POSE':
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    # no dialog: it applies at once; the blend is tuned after the click in Adjust Last Operation

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        if settings.active_index >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        entry = settings.poses[settings.active_index]
        bones_data = json.loads(entry.bone_data_json) if entry.bone_data_json else {}
        blend_factor = self.blend / 100.0
        applied = 0

        for bname, xform in bones_data.items():
            pbone = arm.pose.bones.get(bname)
            if pbone is None:
                continue
            target_loc = Vector(xform["loc"])
            target_rot = Quaternion(xform["rot"])
            target_scale = Vector(xform["scale"])

            pbone.location = pbone.location.lerp(target_loc, blend_factor)
            pbone.rotation_quaternion = pbone.rotation_quaternion.slerp(target_rot, blend_factor)
            pbone.scale = pbone.scale.lerp(target_scale, blend_factor)
            applied += 1

        self.report({'INFO'}, f"Applied '{entry.name}' at {self.blend:.0f}% ({applied} bones)")
        context.view_layer.update()
        return {'FINISHED'}


class BF_OT_PoseDelete(bpy.types.Operator):
    """Delete the selected pose from the library"""
    bl_idname = "boneforge.pose_delete"
    bl_label = "Delete Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        idx = settings.active_index
        if idx >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        name = settings.poses[idx].name
        settings.poses.remove(idx)
        settings.active_index = min(idx, len(settings.poses) - 1)
        _persist_poses(arm, settings)
        self.report({'INFO'}, f"Deleted pose '{name}'")
        return {'FINISHED'}


class BF_OT_PoseRename(bpy.types.Operator):
    """Rename the selected pose"""
    bl_idname = "boneforge.pose_rename"
    bl_label = "Rename Pose"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: StringProperty(description="The pose's new name", name="Name", default="")

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def invoke(self, context, event):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        if settings.active_index < len(settings.poses):
            self.new_name = settings.poses[settings.active_index].name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        idx = settings.active_index
        if idx >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        settings.poses[idx].name = self.new_name
        _persist_poses(arm, settings)
        self.report({'INFO'}, f"Renamed to '{self.new_name}'")
        return {'FINISHED'}


class BF_OT_PoseSetCategory(bpy.types.Operator):
    """Set the category tag on the selected pose"""
    bl_idname = "boneforge.pose_set_category"
    bl_label = "Set Category"
    bl_options = {'REGISTER', 'UNDO'}

    category: StringProperty(description='Category to move the pose to', name="Category", default="")

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def invoke(self, context, event):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        if settings.active_index < len(settings.poses):
            self.category = settings.poses[settings.active_index].category
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        idx = settings.active_index
        if idx >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        settings.poses[idx].category = self.category
        _persist_poses(arm, settings)
        self.report({'INFO'}, f"Set category to '{self.category}'")
        return {'FINISHED'}


class BF_OT_PoseExport(bpy.types.Operator):
    """Export the pose library to a .bfpose file"""
    bl_idname = "boneforge.pose_export"
    bl_label = "Export Poses"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.bfpose", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        data = _poses_to_json(settings)
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            self.report({'ERROR'}, f"Export failed: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Exported {len(settings.poses)} poses to {self.filepath}")
        return {'FINISHED'}


class BF_OT_PoseImport(bpy.types.Operator):
    """Import poses from a .bfpose file"""
    bl_idname = "boneforge.pose_import"
    bl_label = "Import Poses"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.bfpose", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}

        if "poses" not in data:
            self.report({'ERROR'}, "Invalid .bfpose file — missing 'poses' key")
            return {'CANCELLED'}

        count = 0
        for pose_data in data["poses"]:
            entry = settings.poses.add()
            entry.name = pose_data.get("name", "Imported")
            entry.category = pose_data.get("category", "")
            entry.bone_data_json = json.dumps(pose_data.get("bones", {}))
            entry.thumbnail_b64 = pose_data.get("thumbnail_b64", "") or ""
            count += 1

        _persist_poses(arm, settings)
        self.report({'INFO'}, f"Imported {count} poses")
        return {'FINISHED'}


class BF_OT_PoseRefreshThumbnail(bpy.types.Operator):
    """Re-render the thumbnail for the selected pose"""
    bl_idname = "boneforge.pose_refresh_thumbnail"
    bl_label = "Refresh Thumbnail"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_pose_library
        return len(settings.poses) > 0

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_pose_library
        idx = settings.active_index
        if idx >= len(settings.poses):
            self.report({'WARNING'}, "No pose selected")
            return {'CANCELLED'}

        entry = settings.poses[idx]
        _try_render_thumbnail(context, entry)
        _persist_poses(arm, settings)
        self.report({'INFO'}, f"Refreshed thumbnail for '{entry.name}'")
        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BF_PT_PoseLibraryPanel(bpy.types.Panel):
    """Visual pose browser with thumbnail grid"""
    bl_idname = "BONEFORGE_PT_pose_library"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 15

    def draw_header(self, context):
        self.layout.label(text=T("Pose Library"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if arm is None:
            return

        settings = arm.boneforge_pose_library
        _ensure_poses(arm, settings)

        # Category filter
        row = layout.row(align=True)
        row.prop(settings, "filter_category", text=T("Filter"), icon='FILTER')

        active_filter = settings.filter_category.strip()

        # Collect visible categories for info
        categories = set()
        for entry in settings.poses:
            if entry.category:
                categories.add(entry.category)

        if categories:
            row = layout.row()
            row.label(text=f"Categories: {', '.join(sorted(categories))}")

        # Pose grid
        if len(settings.poses) == 0:
            layout.label(text=T("No poses saved"), icon='INFO')
        else:
            grid = layout.grid_flow(columns=3, even_columns=True, align=True)
            for i, entry in enumerate(settings.poses):
                if active_filter and entry.category != active_filter:
                    continue

                box = grid.box()
                col = box.column(align=True)

                # Thumbnail placeholder or icon
                if entry.thumbnail_b64:
                    col.label(text="", icon='IMAGE_DATA')
                else:
                    col.label(text="", icon='GHOST_DISABLED')

                col.label(text=entry.name)
                if entry.category:
                    col.label(text=entry.category, icon='TAG')

                # Selection highlight
                if i == settings.active_index:
                    col.operator("boneforge.pose_apply", text=T("Apply"), icon='POSE_HLT')
                else:
                    op = col.operator("boneforge.pose_apply", text=T("Select"))
                    # Set active index on click
                    # (Apply always uses active_index, so we need to
                    #  set it before calling apply)

        # Active pose index selector
        if len(settings.poses) > 0:
            layout.prop(settings, "active_index", text=T("Active"))

        layout.separator()

        # Action buttons
        row = layout.row(align=True)
        row.operator("boneforge.pose_save", text=T("Save"), icon='ADD')
        row.operator("boneforge.pose_delete", text=T("Delete"), icon='REMOVE')

        row = layout.row(align=True)
        row.operator("boneforge.pose_apply", text=T("Apply"), icon='POSE_HLT')
        row.operator("boneforge.pose_apply_mirrored", text=T("Mirror"), icon='MOD_MIRROR')
        row.operator("boneforge.pose_apply_blended", text=T("Blend"), icon='IPO_EASE_IN_OUT')

        row = layout.row(align=True)
        row.operator("boneforge.pose_rename", text=T("Rename"), icon='OUTLINER_DATA_FONT')
        row.operator("boneforge.pose_set_category", text=T("Category"), icon='TAG')
        row.operator("boneforge.pose_refresh_thumbnail", text="", icon='FILE_REFRESH')

        layout.separator()

        row = layout.row(align=True)
        row.operator("boneforge.pose_export", text=T("Export"), icon='EXPORT')
        row.operator("boneforge.pose_import", text=T("Import"), icon='IMPORT')


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_PoseEntry,
    BF_PoseLibrary,
    BF_OT_PoseSave,
    BF_OT_PoseApply,
    BF_OT_PoseApplyMirrored,
    BF_OT_PoseApplyBlended,
    BF_OT_PoseDelete,
    BF_OT_PoseRename,
    BF_OT_PoseSetCategory,
    BF_OT_PoseExport,
    BF_OT_PoseImport,
    BF_OT_PoseRefreshThumbnail,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.boneforge_pose_library = PointerProperty(type=BF_PoseLibrary)


def unregister():
    if hasattr(bpy.types.Object, "boneforge_pose_library"):
        del bpy.types.Object.boneforge_pose_library
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
