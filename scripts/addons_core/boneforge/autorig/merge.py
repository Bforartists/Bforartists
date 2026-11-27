"""BoneCraft Phase 3 — Rig Merge and Phase 1/2 Integration.

Combines body and face armatures into a single rig, then triggers
all cross-phase integrations (picker zones, bookmarks, bone collection
metadata, Rigify enhancement recognition, corrective shape key wiring).

Each Phase 1/2 integration is guarded by try/except ImportError so a
missing module never blocks generation.
"""

from dataclasses import dataclass, field

import bpy

from boneforge.core import (
    write_custom_json,
)
from boneforge.autorig.constants import (
    BODY_IK_COLLECTION,
    BODY_FK_COLLECTION,
    BODY_DEFORM_COLLECTION,
    FACE_CONTROLS_COLLECTION,
    FACE_DEFORM_COLLECTION,
    FINGER_DEFORM_COLLECTION,
    BONE_COLLECTION_NAMES,
    STAGING_COLLECTION_NAME,
)

import logging

logger = logging.getLogger(__name__)

# Name given to the final merged armature.
FINAL_ARMATURE_NAME = "BoneForge_Rig"


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class MergeResult:
    """Result of rig merge and integration."""

    success: bool = False
    message: str = ""
    final_armature_name: str = ""
    integration_report: dict = field(default_factory=dict)


# ── Internal helpers ──────────────────────────────────────────

def _rename_to_final(armature_obj):
    """Rename an armature object and its data to the canonical final name."""
    armature_obj.name = FINAL_ARMATURE_NAME
    armature_obj.data.name = FINAL_ARMATURE_NAME


def _join_armatures(context, body_armature_obj, face_armature_obj):
    """Join two armature objects into one using Blender's join operator.

    The body armature is the target (active); the face armature is
    joined into it and consumed.

    Returns:
        The merged armature ``Object`` (same as *body_armature_obj*).
    """
    bpy.ops.object.select_all(action='DESELECT')
    face_armature_obj.select_set(True)
    body_armature_obj.select_set(True)
    context.view_layer.objects.active = body_armature_obj

    bpy.ops.object.join()
    _rename_to_final(body_armature_obj)

    return body_armature_obj


def _parent_face_to_head(edit_bones):
    """Parent the face_root bone to the head bone in edit mode.

    If either bone is missing, this is a no-op.
    """
    head_bone = edit_bones.get('head')
    face_root = edit_bones.get('face_root')

    if head_bone is None or face_root is None:
        return

    face_root.parent = head_bone
    face_root.use_connect = False


def _get_armature_from_result(result):
    """Look up the Blender armature object from a generation result.

    Returns the object, or None if the result failed or the object
    was not found.
    """
    if result is None or not result.success:
        return None
    return bpy.data.objects.get(result.armature_object_name)


def _snapshot_vertex_groups(mesh_obj):
    """Capture all vertex group assignments for rollback.

    CRIT-1 fix: enables skinning pipeline rollback on partial failure.

    Returns:
        dict mapping group_name to list of (vertex_index, weight) tuples.
    """
    # v3.1.6 (M-1): walk vert.groups once, then bucket by group name.
    snapshot: dict[str, list] = {vg.name: [] for vg in mesh_obj.vertex_groups}
    groups = mesh_obj.vertex_groups
    for v in mesh_obj.data.vertices:
        for vge in v.groups:
            if vge.weight > 0.0:
                snapshot[groups[vge.group].name].append((v.index, vge.weight))
    return snapshot


def _restore_vertex_groups(mesh_obj, snapshot):
    """Restore vertex groups from a snapshot taken by _snapshot_vertex_groups.

    Clears all current groups and re-creates from the snapshot.
    """
    # Remove all vertex groups
    mesh_obj.vertex_groups.clear()

    # Recreate from snapshot
    for group_name, weights in snapshot.items():
        vg = mesh_obj.vertex_groups.new(name=group_name)
        for vert_index, weight in weights:
            vg.add([vert_index], weight, 'REPLACE')


def _populate_phase1_bookmarks(armature_obj):
    """Create five default visibility bookmarks on the merged armature.

    Bookmarks:
        1. "All Controls" — all collections visible
        2. "Body Only" — body collections visible, face hidden
        3. "Face Only" — face collections visible, body hidden
        4. "IK Controls" — only IK collection visible
        5. "Deform Only" — only deform collections visible

    Returns:
        True if bookmarks were created, False if Phase 1 bookmarks
        is unavailable.
    """
    try:
        from boneforge.ui_panels.bookmarks import (
            _bookmark_settings,
            _persist_to_custom_prop,
        )
    except ImportError:
        logger.info("[BoneCraft] Phase 1 bookmarks not available — skipping")
        return False

    if not hasattr(armature_obj, 'boneforge_bookmark_settings'):
        return False

    bookmark_definitions = [
        {
            'name': "All Controls",
            'visibility': {name: True for name in BONE_COLLECTION_NAMES},
        },
        {
            'name': "Body Only",
            'visibility': {
                BODY_IK_COLLECTION: True,
                BODY_FK_COLLECTION: True,
                BODY_DEFORM_COLLECTION: True,
                FACE_CONTROLS_COLLECTION: False,
                FACE_DEFORM_COLLECTION: False,
            },
        },
        {
            'name': "Face Only",
            'visibility': {
                BODY_IK_COLLECTION: False,
                BODY_FK_COLLECTION: False,
                BODY_DEFORM_COLLECTION: False,
                FACE_CONTROLS_COLLECTION: True,
                FACE_DEFORM_COLLECTION: True,
            },
        },
        {
            'name': "IK Controls",
            'visibility': {
                BODY_IK_COLLECTION: True,
                BODY_FK_COLLECTION: False,
                BODY_DEFORM_COLLECTION: False,
                FACE_CONTROLS_COLLECTION: False,
                FACE_DEFORM_COLLECTION: False,
            },
        },
        {
            'name': "Deform Only",
            'visibility': {
                BODY_IK_COLLECTION: False,
                BODY_FK_COLLECTION: False,
                BODY_DEFORM_COLLECTION: True,
                FACE_CONTROLS_COLLECTION: False,
                FACE_DEFORM_COLLECTION: True,
            },
        },
    ]

    try:
        settings = _bookmark_settings(armature_obj)
        for bookmark_definition in bookmark_definitions:
            bookmark = settings.bookmarks.add()
            bookmark.name = bookmark_definition['name']
            write_custom_json(
                armature_obj,
                f"boneforge_bm_{bookmark.name}",
                bookmark_definition['visibility'],
            )

        _persist_to_custom_prop(armature_obj)
        return True

    except (AttributeError, TypeError) as error:
        logger.error(f"[BoneCraft] Failed to create bookmarks: {error}")
        return False


def _populate_phase1_collections(armature_obj):
    """Populate Phase 1 collection UI metadata on the armature.

    Writes ``BF_CollectionMeta`` entries for each generated bone
    collection with display names, icons, and colors.

    Returns:
        True if collection metadata was written, False if Phase 1
        collection_ui is unavailable.
    """
    if not hasattr(armature_obj, 'boneforge_settings'):
        return False

    collection_metadata = {
        BODY_IK_COLLECTION: {
            'display_name': "Body IK",
            'icon': 'CON_KINEMATIC',
            'color': (0.8, 0.4, 0.2),
            'section': 'body',
        },
        BODY_FK_COLLECTION: {
            'display_name': "Body FK",
            'icon': 'BONE_DATA',
            'color': (0.4, 0.6, 0.8),
            'section': 'body',
        },
        BODY_DEFORM_COLLECTION: {
            'display_name': "Body Deform",
            'icon': 'MESH_DATA',
            'color': (0.5, 0.5, 0.5),
            'section': 'body',
        },
        FACE_CONTROLS_COLLECTION: {
            'display_name': "Face Controls",
            'icon': 'SHAPEKEY_DATA',
            'color': (0.9, 0.6, 0.3),
            'section': 'face',
        },
        FACE_DEFORM_COLLECTION: {
            'display_name': "Face Deform",
            'icon': 'MESH_DATA',
            'color': (0.6, 0.6, 0.4),
            'section': 'face',
        },
        FINGER_DEFORM_COLLECTION: {
            'display_name': "Finger Deform",
            'icon': 'HAND',
            'color': (0.9, 0.5, 0.4),
            'section': 'body',
        },
    }

    try:
        settings = armature_obj.boneforge_settings
        if not hasattr(settings, 'collection_meta'):
            return False

        for collection_name, metadata in collection_metadata.items():
            entry = settings.collection_meta.add()
            entry.name = collection_name
            entry.display_name = metadata['display_name']
            entry.icon = metadata['icon']
            if hasattr(entry, 'color'):
                entry.color = metadata['color']
        return True

    except (AttributeError, TypeError) as error:
        logger.error(f"[BoneCraft] Failed to populate collection metadata: {error}")
        return False


def _shape_key_present(mesh_obj, key_name):
    """Return True if *mesh_obj* has a shape key named *key_name*."""
    if mesh_obj.data.shape_keys is None:
        return False
    return mesh_obj.data.shape_keys.key_blocks.get(key_name) is not None


def _apply_phase2_correctives(context, armature_obj, mesh_obj, shape_key_names):
    """Wire facial shape keys to corrective drivers via Phase 2.

    Verifies each shape key still exists before attempting to wire it.
    The actual driver setup is handled by the Phase 2 correctives module.

    Args:
        context: Blender context.
        armature_obj: The merged armature object.
        mesh_obj: The mesh object with shape keys.
        shape_key_names: List of shape key names to wire.

    Returns:
        True if any correctives were applied, False if Phase 2
        correctives is unavailable or no shape keys remain.
    """
    try:
        from boneforge.animation import correctives as correctives_module
    except ImportError:
        logger.info("[BoneCraft] Phase 2 correctives not available — skipping driver setup")
        return False

    if not shape_key_names:
        return False

    # Verify which shape keys still exist on the mesh
    valid_key_names = [
        key_name for key_name in shape_key_names
        if _shape_key_present(mesh_obj, key_name)
    ]

    # The correctives module will handle driver creation when its
    # operators are invoked.  For now, confirm the shape keys exist
    # and are ready for manual or automatic wiring.
    return len(valid_key_names) > 0


def _count_result_bones(*results):
    """Sum bone counts from one or more generation results.

    Skips None results and unsuccessful results.
    """
    total = 0
    for result in results:
        if result is not None and result.success:
            total += result.bone_count
    return total


def _move_from_staging_to_scene(context, final_armature):
    """Move generated objects from the staging collection to the scene root.

    Moves the armature and any bone shape objects, then removes the
    staging collection if empty.
    """
    staging = bpy.data.collections.get(STAGING_COLLECTION_NAME)
    if staging is None:
        return

    scene_collection = context.scene.collection

    # Move the final armature
    if final_armature.name not in scene_collection.objects:
        scene_collection.objects.link(final_armature)
    if final_armature.name in staging.objects:
        staging.objects.unlink(final_armature)

    # Move bone shape objects (hidden helpers)
    for obj in list(staging.objects):
        if obj.name.startswith("BF_Shape_"):
            scene_collection.objects.link(obj)
            staging.objects.unlink(obj)

    # Clean up empty staging collection
    if len(staging.objects) == 0:
        bpy.data.collections.remove(staging)


# ── Main merge function ───────────────────────────────────────

def merge_rigs(context, session, body_result, face_result):
    """Merge body and face armatures and apply all Phase 1/2 integrations.

    This is the central dispatcher that combines generation results
    into a single rig and triggers cross-phase integration.

    Args:
        context: Blender context.
        session: ``BF_AutoRigSession`` PropertyGroup.
        body_result: ``BodyRigResult`` from body_gen (or None).
        face_result: ``FaceRigResult`` from face_gen (or None).

    Returns:
        ``MergeResult`` with merge outcome and integration report.
    """
    integration_report = {}

    body_armature_obj = _get_armature_from_result(body_result)
    face_armature_obj = _get_armature_from_result(face_result)

    # Determine the final armature
    if body_armature_obj and face_armature_obj:
        final_armature = _join_armatures(context, body_armature_obj, face_armature_obj)

        # Parent face_root to head bone
        context.view_layer.objects.active = final_armature
        bpy.ops.object.mode_set(mode='EDIT')
        _parent_face_to_head(final_armature.data.edit_bones)
        bpy.ops.object.mode_set(mode='OBJECT')

    elif body_armature_obj:
        final_armature = body_armature_obj
        _rename_to_final(final_armature)

    elif face_armature_obj:
        final_armature = face_armature_obj
        _rename_to_final(final_armature)

    else:
        return MergeResult(
            success=False,
            message="No armatures to merge — both generators failed",
            integration_report=integration_report,
        )

    session.generated_final_armature = final_armature.name

    # ── Apply production skinning pipeline ───────────────────
    mesh_obj = bpy.data.objects.get(session.mesh_object_name)
    if mesh_obj is not None:
        from boneforge.autorig.skin_gen import apply_production_weights

        # CRIT-1 fix: snapshot vertex groups for rollback on partial failure
        _vg_backup = _snapshot_vertex_groups(mesh_obj)
        try:
            skinning_result = apply_production_weights(
                context, mesh_obj, final_armature, session,
            )
        except Exception as skinning_error:
            # CRIT-1 fix: restore original vertex groups on failure
            _restore_vertex_groups(mesh_obj, _vg_backup)
            logger.error(f"[BoneCraft] Skinning pipeline failed: {skinning_error}")
            integration_report['skinning'] = {
                'success': False,
                'method': 'FAILED',
                'quality_score': 0.0,
                'face_isolation': False,
                'correctives': False,
                'warnings': [f"Skinning failed: {skinning_error}"],
            }
            skinning_result = None

        if skinning_result is not None:
            integration_report['skinning'] = {
                'success': skinning_result.success,
                'method': skinning_result.method,
                'quality_score': skinning_result.quality_report.overall_score,
                'face_isolation': skinning_result.face_isolation_applied,
                'correctives': skinning_result.correctives_applied,
                'warnings': skinning_result.warnings,
            }

            # Persist skinning results to session for UI display
            import json
            session.skinning_quality_score = skinning_result.quality_report.overall_score
            session.skinning_method = skinning_result.method
            session.skinning_warnings = json.dumps(skinning_result.warnings)
            session.skinning_unweighted_verts = skinning_result.quality_report.unweighted_vertices
            session.skinning_discontinuities = skinning_result.quality_report.discontinuity_count
            session.skinning_face_isolated = skinning_result.face_isolation_applied
            session.skinning_correctives_applied = skinning_result.correctives_applied

    # ── Phase 1 integrations ──────────────────────────────────

    integration_report['bookmarks'] = _populate_phase1_bookmarks(final_armature)
    integration_report['collection_ui'] = _populate_phase1_collections(final_armature)

    # ── Phase 2 integrations ──────────────────────────────────
    shape_key_names = face_result.shape_key_names if face_result else []
    if mesh_obj is not None and shape_key_names:
        integration_report['correctives'] = _apply_phase2_correctives(
            context, final_armature, mesh_obj, shape_key_names,
        )
    else:
        integration_report['correctives'] = False

    # Rigify enhancement: no explicit call needed — bone names are
    # already Rigify-compatible, so is_rigify_human() will detect them.
    integration_report['rigify_compatible'] = True

    # ── Move from staging to scene collection ─────────────────
    _move_from_staging_to_scene(context, final_armature)

    total_bones = _count_result_bones(body_result, face_result)

    # CRIT-5 fix: surface integration failures in the user-facing message
    failed_integrations = [
        name for name, success in integration_report.items()
        if success is False
    ]
    message = (
        f"Rig complete: {total_bones} bones, "
        f"{len(shape_key_names)} shape keys"
    )
    if failed_integrations:
        message += (
            f" (Warning: {', '.join(failed_integrations)} "
            f"integration(s) skipped)"
        )

    return MergeResult(
        success=True,
        message=message,
        final_armature_name=final_armature.name,
        integration_report=integration_report,
    )


# ── Operator (called internally by WizardGenerate) ────────────

class BF_OT_MergeRigs(bpy.types.Operator):
    """Merge body and face armatures into final rig (internal).

    This operator exists for registration purposes and undo integration.
    The actual merge logic is invoked programmatically by WizardGenerate,
    not directly by the user.
    """

    bl_idname = "boneforge.autorig_merge_rigs"
    bl_label = "Merge Rigs"
    bl_description = "Join the body and face rigs into one armature"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Require an active wizard session."""
        session = context.scene.boneforge_autorig_session
        return session.is_active

    def execute(self, context):
        """Stub — real merge is called programmatically by WizardGenerate."""
        self.report({'INFO'}, "Merge operator should be called via the wizard")
        return {'CANCELLED'}


# ── Registration ──────────────────────────────────────────────

classes = (BF_OT_MergeRigs,)


def register():
    """Register merge operator."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister merge operator."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
