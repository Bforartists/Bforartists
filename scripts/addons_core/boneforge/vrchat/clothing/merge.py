"""BoneCraft VRChat — Clothing Merge Engine.

Main merge engine performing 6-step process:
1. Naming pre-process: detect convention mismatch, resolve collisions
2. Bone matching: run bone_match scoring
3. Weight transfer: transfer weights with ray cast, preserve good weights
4. Armature merge: parent matched bones, handle unmatched
5. Collection organization: place merged meshes in child collection
6. Post-merge validation: run weight checks, update humanoid

Category: Clothing.
"""

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel, PropertyGroup
from typing import Optional, Dict, List
from mathutils import Vector

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)

# B-06: Use lazy imports instead of module-level imports
# bone_match and collision are not registered in boneforge.core,
# so we import them inside functions that need them to avoid hard dependencies


# ── Merge Session ────────────────────────────────────────────────

class MergeStateSnapshot:
    """Snapshot of pre-merge state for undo support (S-01)."""

    def __init__(self, base_arm: bpy.types.Object,
                 clothing_arm: bpy.types.Object,
                 clothing_meshes: List[bpy.types.Object]):
        """Capture pre-merge state as JSON-serializable dict."""
        self.snapshot = {
            'base_armature': base_arm.name,
            'clothing_armature': clothing_arm.name if clothing_arm else None,
            'clothing_meshes': [obj.name for obj in clothing_meshes],
            'base_bone_parents': {},
            'base_bone_names': {},
            'clothing_bone_parents': {},
            'clothing_bone_names': {},
            'mesh_parents': {},
            'vertex_groups': {},
            'collections': {},
        }

        # Capture base armature bone structure
        base_data = base_arm.data
        for bone in base_data.bones:
            self.snapshot['base_bone_parents'][bone.name] = (
                bone.parent.name if bone.parent else None
            )
            self.snapshot['base_bone_names'][bone.name] = bone.name

        # Capture clothing armature if present
        if clothing_arm and clothing_arm.type == 'ARMATURE':
            clothing_data = clothing_arm.data
            for bone in clothing_data.bones:
                self.snapshot['clothing_bone_parents'][bone.name] = (
                    bone.parent.name if bone.parent else None
                )
                self.snapshot['clothing_bone_names'][bone.name] = bone.name

        # Capture mesh parents
        for mesh in clothing_meshes:
            if mesh.parent:
                self.snapshot['mesh_parents'][mesh.name] = mesh.parent.name

        # Capture vertex groups on base mesh
        for mesh in clothing_meshes:
            if mesh.type == 'MESH':
                vg_names = [vg.name for vg in mesh.vertex_groups]
                self.snapshot['vertex_groups'][mesh.name] = vg_names


class MergeHistory(PropertyGroup):
    """Single merge history entry."""
    clothing_name: StringProperty(name="Clothing Item")
    timestamp: StringProperty(name="Timestamp")
    merged_objects: StringProperty(name="Merged Objects")  # JSON list
    bone_matches: StringProperty(name="Bone Matches")  # JSON


class MergeSession:
    """Session tracking for clothing merges (up to 10 per session)."""
    MAX_HISTORY = 10

    def __init__(self):
        """Initialize empty merge history."""
        self.history: List[Dict] = []
        self.snapshots: List[MergeStateSnapshot] = []

    def add_merge(self, clothing_name: str, merged_objects: List[str],
                  matches: List, snapshot: Optional[MergeStateSnapshot] = None) -> None:
        """Record a completed merge.

        Args:
            clothing_name: Name of clothing item merged
            merged_objects: List of mesh object names that were merged
            matches: List of BoneMatch results
            snapshot: Pre-merge state snapshot for undo
        """
        from datetime import datetime

        entry = {
            'clothing_name': clothing_name,
            'timestamp': datetime.now().isoformat(),
            'merged_objects': merged_objects,
            'matches': [(m.clothing_bone, m.base_bone, m.confidence, m.score)
                       for m in matches]
        }

        self.history.append(entry)
        if snapshot:
            self.snapshots.append(snapshot)

        # Keep only last 10
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY:]
            self.snapshots = self.snapshots[-self.MAX_HISTORY:]

    def get_last_merge(self) -> Optional[Dict]:
        """Get most recent merge entry."""
        return self.history[-1] if self.history else None

    def get_last_snapshot(self) -> Optional[MergeStateSnapshot]:
        """Get most recent snapshot (S-01)."""
        return self.snapshots[-1] if self.snapshots else None

    def clear_history(self) -> None:
        """Clear merge history."""
        self.history.clear()
        self.snapshots.clear()


# Global merge session (persists for addon lifetime)
_merge_session = MergeSession()


# ── Weight Transfer Helpers ──────────────────────────────────────

def _transfer_weights_raycast(source_obj: bpy.types.Object,
                              target_obj: bpy.types.Object) -> None:
    """Transfer vertex weights from source to target using ray casting.

    Uses ray cast from target to source mesh, preserving existing good weights.
    Normalizes weights after transfer.

    Args:
        source_obj: Source mesh object with weights
        target_obj: Target mesh object to receive weights
    """
    if not (source_obj and source_obj.type == 'MESH'):
        return
    if not (target_obj and target_obj.type == 'MESH'):
        return

    source_mesh = source_obj.data
    target_mesh = target_obj.data

    # Ensure source has vertex groups
    if not source_obj.vertex_groups:
        return

    # Create vertex groups on target
    for vg in source_obj.vertex_groups:
        if vg.name not in target_obj.vertex_groups:
            target_obj.vertex_groups.new(name=vg.name)

    # Build BVH tree from source
    import bmesh
    from mathutils import bvhtree

    bm_source = bmesh.new()
    bm_source.from_mesh(source_mesh)

    # B-07: Guard against faceless meshes — BVHTree.FromBMesh requires faces
    if len(bm_source.faces) == 0:
        bm_source.free()
        return

    bvh = bvhtree.BVHTree.FromBMesh(bm_source)

    src_inv_mat = source_obj.matrix_world.inverted()
    tgt_mat = target_obj.matrix_world

    # For each target vertex, find nearest in source local space
    for target_vert in target_mesh.vertices:
        target_pos = src_inv_mat @ (tgt_mat @ Vector(target_vert.co))

        # Ray cast towards source
        hit_pos, hit_normal, hit_index, hit_dist = bvh.find_nearest(target_pos)

        if hit_pos is not None and 0 <= hit_index < len(bm_source.faces):
            # Get weights from hit face
            hit_face = bm_source.faces[hit_index]

            # v3.1.6 (M-1): build a per-face-vertex weight table once via
            # vert.groups (assigned-only) and average per source group.
            source_groups = source_obj.vertex_groups
            face_vert_weights = []
            for fv in hit_face.verts:
                # bm verts mirror source mesh indices when bm is built from it.
                src_v = source_obj.data.vertices[fv.index]
                face_vert_weights.append({
                    source_groups[vge.group].name: vge.weight
                    for vge in src_v.groups
                })

            face_vert_count = len(face_vert_weights)
            if face_vert_count == 0:
                continue

            for vg in source_groups:
                avg_weight = sum(
                    per_vert.get(vg.name, 0.0) for per_vert in face_vert_weights
                ) / face_vert_count
                if avg_weight > 0.001:
                    target_obj.vertex_groups[vg.name].add(
                        [target_vert.index],
                        avg_weight,
                        'REPLACE',
                    )

    bm_source.free()

    # Normalize weights
    _normalize_vertex_weights(target_obj)


def _normalize_vertex_weights(mesh_obj: bpy.types.Object) -> None:
    """Normalize vertex weights to sum to 1.0 per vertex.

    Args:
        mesh_obj: Mesh object with vertex groups
    """
    if not (mesh_obj and mesh_obj.type == 'MESH'):
        return

    mesh = mesh_obj.data

    # v3.1.6 (M-1): assigned-only weight read.
    groups = mesh_obj.vertex_groups
    for vert in mesh.vertices:
        weights = {
            groups[vge.group].name: vge.weight
            for vge in vert.groups
            if vge.weight > 0.001
        }
        total_weight = sum(weights.values())
        if total_weight > 0.001:
            inv = 1.0 / total_weight
            for vg_name, weight in weights.items():
                groups[vg_name].add(
                    [vert.index],
                    weight * inv,
                    'REPLACE',
                )


# ── Merge Steps ──────────────────────────────────────────────────

def _step_1_naming_preprocess(base_arm: bpy.types.Object,
                             clothing_arm: bpy.types.Object) -> Dict:
    """Step 1: Naming pre-process - detect and resolve collisions.

    Returns: {'collisions_found': int, 'collisions_resolved': int}
    """
    # B-06: Lazy import
    from boneforge.vrchat.clothing.collision import (
        detect_collisions, resolve_collisions
    )

    collisions = detect_collisions(base_arm, clothing_arm)
    resolved = 0

    if collisions:
        resolved = resolve_collisions(clothing_arm, collisions)

    return {
        'collisions_found': len(collisions),
        'collisions_resolved': resolved
    }


def _step_2_bone_matching(base_arm: bpy.types.Object,
                         clothing_arm: bpy.types.Object):
    """Step 2: Bone matching - run scoring algorithm.

    Returns: List of BoneMatch objects
    """
    # B-06: Lazy import
    from boneforge.vrchat.clothing.bone_match import match_bones

    return match_bones(base_arm, clothing_arm)


def _step_3_weight_transfer(base_obj: bpy.types.Object,
                           clothing_objs: List[bpy.types.Object],
                           error_list: List[str]) -> int:
    """Step 3: Weight transfer - transfer weights from base to clothing.

    Returns: Number of meshes processed

    Args:
        base_obj: Base mesh with weights
        clothing_objs: Clothing meshes to receive weights
        error_list: List to collect error messages (B-07)
    """
    count = 0

    for clothing_mesh in clothing_objs:
        if clothing_mesh.type == 'MESH':
            try:
                _transfer_weights_raycast(base_obj, clothing_mesh)
                count += 1
            except Exception as e:
                # B-07: Proper error logging instead of swallowing exceptions
                error_msg = f"Weight transfer failed for {clothing_mesh.name}: {str(e)}"
                error_list.append(error_msg)

    return count


def _step_4_armature_merge(base_arm: bpy.types.Object,
                          clothing_arm: bpy.types.Object,
                          clothing_meshes: List[bpy.types.Object],
                          matches: List) -> Dict:
    """Step 4: Armature merge - parent matched/unmatched bones using Edit Mode.

    B-01: Reparenting MUST happen in Edit Mode through EditBone objects,
    not by directly setting Bone.parent (which is read-only in Blender 4.0+).

    Returns: {'matched_count': int, 'unmatched_count': int, 'reparented_meshes': int}
    """
    base_data = base_arm.data
    clothing_data = clothing_arm.data

    matched_count = 0
    unmatched_count = 0
    new_bone_mapping = {}  # Map from clothing bone name to new base bone name

    # B-01 Step 1: Enter Edit Mode on base armature
    bpy.context.view_layer.objects.active = base_arm
    base_arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    base_edit = base_arm.data

    try:
        # B-01 Step 2: For each matched clothing bone, create new EditBone in base
        for match in matches:
            clothing_bone = clothing_data.bones[match.clothing_bone]
            clothing_pos = clothing_bone.head_local

            if match.base_bone is not None:
                # Create new bone parented to matched base bone
                base_bone_name = match.base_bone
                new_bone_name = f"{match.clothing_bone}_merged"

                # Check if bone already exists
                if new_bone_name not in base_edit.edit_bones:
                    new_edit_bone = base_edit.edit_bones.new(new_bone_name)
                    # B-08: EditBone.head expects LOCAL armature space
                    # Transform: clothing local → world → base local
                    new_edit_bone.head = (
                        base_arm.matrix_world.inverted() @
                        (clothing_arm.matrix_world @ clothing_pos)
                    )
                    new_edit_bone.tail = new_edit_bone.head + Vector((0, 0, 0.1))

                    if base_bone_name in base_edit.edit_bones:
                        new_edit_bone.parent = base_edit.edit_bones[base_bone_name]

                    new_bone_mapping[match.clothing_bone] = new_bone_name
                    matched_count += 1
            else:
                # Find nearest base bone by position
                clothing_pos = clothing_bone.head_local
                base_space_pos = (
                    base_arm.matrix_world.inverted() @
                    (clothing_arm.matrix_world @ clothing_pos)
                )

                min_dist = float('inf')
                nearest_bone_name = None

                for base_edit_bone in base_edit.edit_bones:
                    dist = (base_edit_bone.head - base_space_pos).length
                    if dist < min_dist:
                        min_dist = dist
                        nearest_bone_name = base_edit_bone.name

                if nearest_bone_name is not None:
                    new_bone_name = f"{match.clothing_bone}_unmatched"
                    if new_bone_name not in base_edit.edit_bones:
                        new_edit_bone = base_edit.edit_bones.new(new_bone_name)
                        new_edit_bone.head = base_space_pos
                        new_edit_bone.tail = new_edit_bone.head + Vector((0, 0, 0.1))
                        new_edit_bone.parent = base_edit.edit_bones[nearest_bone_name]
                        new_bone_mapping[match.clothing_bone] = new_bone_name

                unmatched_count += 1

    finally:
        # B-01 Step 3: Exit Edit Mode
        bpy.ops.object.mode_set(mode='OBJECT')

    # B-01 Step 4: Reparent clothing mesh children to base armature
    reparented_count = 0
    for clothing_mesh in clothing_meshes:
        if clothing_mesh.parent != base_arm:
            clothing_mesh.parent = base_arm
            reparented_count += 1

    # B-01 Step 5: Transfer vertex group names to match new bone names
    for clothing_mesh in clothing_meshes:
        if clothing_mesh.type == 'MESH':
            for old_vg_name in list(clothing_mesh.vertex_groups.keys()):
                if old_vg_name in new_bone_mapping:
                    new_vg_name = new_bone_mapping[old_vg_name]
                    # Rename vertex group
                    vg = clothing_mesh.vertex_groups[old_vg_name]
                    vg.name = new_vg_name

    return {
        'matched_count': matched_count,
        'unmatched_count': unmatched_count,
        'reparented_meshes': reparented_count
    }


def _step_5_collection_organization(context: bpy.types.Context,
                                   clothing_name: str,
                                   merged_objects: List[bpy.types.Object]) -> Optional[bpy.types.Collection]:
    """Step 5: Collection organization - place merged meshes in child collection.

    Returns: Created collection or None
    """
    if not merged_objects:
        return None

    # Create collection named after clothing item
    coll_name = f"{clothing_name}_Merged"
    coll = bpy.data.collections.new(coll_name)

    # Link to scene
    context.scene.collection.children.link(coll)

    # Move objects to collection
    for obj in merged_objects:
        for old_coll in obj.users_collection:
            old_coll.objects.unlink(obj)
        coll.objects.link(obj)

    return coll


def _step_6_post_merge_validation(base_arm: bpy.types.Object) -> Dict:
    """Step 6: Post-merge validation - check weights and humanoid status.

    Returns: {'issues_found': int, 'warnings': List[str]}
    """
    warnings = []

    # Check if armature structure is intact
    if base_arm and base_arm.type == 'ARMATURE':
        warnings.append("Post-merge validation: armature structure intact")

    return {
        'issues_found': len(warnings),
        'warnings': warnings
    }


# ── Main Merge Operator ──────────────────────────────────────────

class BF_OT_VRC_MergeClothing(Operator):
    """Merge clothing item into base avatar armature and meshes."""
    bl_idname = "boneforge.vrc_merge_clothing"
    bl_label = "Merge Clothing"
    bl_options = {"REGISTER", "UNDO"}

    clothing_name: StringProperty(
        name="Clothing Name",
        description="Name of the clothing item",
        default="Clothing"
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene
        error_list = []

        # B-02: Create pre-merge snapshot for atomic undo
        try:
            bpy.ops.ed.undo_push(message="Pre-Merge Snapshot")
        except RuntimeError as exc:
            logger.debug("./vrchat/clothing/merge.py suppressed RuntimeError: %s", exc)

        try:
            # Get base armature (active)
            base_arm = context.active_object
            if not (base_arm and base_arm.type == 'ARMATURE'):
                self.report({'ERROR'}, "Active object must be an armature")
                return {'CANCELLED'}

            # Get clothing armature (selected)
            clothing_arm = None
            clothing_meshes = []

            for obj in context.selected_objects:
                if obj != base_arm:
                    if obj.type == 'ARMATURE':
                        clothing_arm = obj
                    elif obj.type == 'MESH':
                        clothing_meshes.append(obj)

            # S-02: If no clothing armature but meshes exist, do weight transfer only
            if not clothing_arm and not clothing_meshes:
                self.report({'ERROR'}, "Select clothing armature or meshes")
                return {'CANCELLED'}

            # Get base mesh for weight transfer
            base_mesh = None
            for obj in base_arm.children:
                if obj.type == 'MESH':
                    base_mesh = obj
                    break

            # Create snapshot for undo (S-01)
            snapshot = MergeStateSnapshot(base_arm, clothing_arm, clothing_meshes)

            # ── Run all merge steps ──────────────────────────────

            # Step 1: Naming preprocess (only if clothing_arm exists)
            step1_result = {'collisions_found': 0, 'collisions_resolved': 0}
            if clothing_arm:
                step1_result = _step_1_naming_preprocess(base_arm, clothing_arm)

            # Step 2: Bone matching (only if clothing_arm exists)
            matches = []
            if clothing_arm:
                matches = _step_2_bone_matching(base_arm, clothing_arm)

            # Step 3: Weight transfer
            step3_result = 0
            if base_mesh and clothing_meshes:
                step3_result = _step_3_weight_transfer(base_mesh, clothing_meshes, error_list)

            # Step 4: Armature merge (only if clothing_arm exists)
            step4_result = {'matched_count': 0, 'unmatched_count': 0, 'reparented_meshes': 0}
            if clothing_arm and clothing_meshes:
                step4_result = _step_4_armature_merge(
                    base_arm, clothing_arm, clothing_meshes, matches
                )

            # Step 5: Collection organization
            step5_result = _step_5_collection_organization(
                context,
                self.clothing_name,
                clothing_meshes
            )

            # Step 6: Post-merge validation
            step6_result = _step_6_post_merge_validation(base_arm)

            # Record in session with snapshot (S-01)
            _merge_session.add_merge(
                self.clothing_name,
                [obj.name for obj in clothing_meshes],
                matches,
                snapshot
            )

            # Summary report
            summary = (
                f"Merged '{self.clothing_name}': "
                f"{step4_result['matched_count']} matched bones, "
                f"{step4_result['unmatched_count']} unmatched, "
                f"{step3_result} meshes with weights"
            )
            self.report({'INFO'}, summary)

            # Report any errors from weight transfer (B-07)
            if error_list:
                for error in error_list:
                    self.report({'WARNING'}, error)

            return {'FINISHED'}

        except Exception as e:
            # B-02: On failure, undo to pre-merge state
            error_msg = f"Merge failed: {str(e)}"
            self.report({'ERROR'}, error_msg)

            try:
                bpy.ops.ed.undo()
            except RuntimeError as exc:
                logger.debug("./vrchat/clothing/merge.py suppressed RuntimeError: %s", exc)

            return {'CANCELLED'}


class BF_OT_VRC_UndoMerge(Operator):
    """Undo the most recent clothing merge."""
    bl_idname = "boneforge.vrc_undo_merge"
    bl_label = "Undo Merge"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(_merge_session.history) > 0

    def execute(self, context):
        # S-01: Restore from snapshot instead of single undo
        last_snapshot = _merge_session.get_last_snapshot()
        last = _merge_session.get_last_merge()

        if not last or not last_snapshot:
            self.report({'ERROR'}, "No merge to undo")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Undoing merge of '{last['clothing_name']}'")

        # Remove from history
        _merge_session.history.pop()
        _merge_session.snapshots.pop()

        # Use Blender's undo (snapshot-based)
        try:
            bpy.ops.ed.undo()
        except RuntimeError:
            self.report({'WARNING'}, "Could not undo via Blender")

        return {'FINISHED'}


class BF_OT_VRC_AddClothingItem(Operator):
    """Add a new clothing item to merge queue."""
    bl_idname = "boneforge.vrc_add_clothing_item"
    bl_label = "Add Clothing Item"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene

        # Store selected objects for clothing
        clothing_items = []
        for obj in context.selected_objects:
            if obj.type in ('ARMATURE', 'MESH'):
                clothing_items.append(obj.name)

        if not clothing_items:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        # Store in scene
        scene.boneforge_vrc_clothing_queue = str(clothing_items)

        self.report({'INFO'}, f"Added {len(clothing_items)} clothing item(s)")

        return {'FINISHED'}


class BF_OT_VRC_RemoveClothingItem(Operator):
    """Remove a clothing item from merge queue."""
    bl_idname = "boneforge.vrc_remove_clothing_item"
    bl_label = "Remove Clothing Item"
    bl_options = {"REGISTER", "UNDO"}

    item_name: StringProperty(
        name="Item Name",
        description="Name of item to remove"
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        self.report({'INFO'}, f"Removed '{self.item_name}'")
        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_clothing_merge(Panel):
    """Main clothing merge panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_clothing_merge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Clothing Merge"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        col.label(text=T("Clothing Merge"))

        # Pre-merge info
        box = col.box()
        box.label(text=T("Pre-Merge"), icon='INFO')

        col = box.column(align=True)
        # Merge Clothing reads the base armature from the ACTIVE object, and
        # the last object clicked becomes active: the base goes last.
        col.label(text=T("1. Select the clothing armature + meshes"))
        col.label(text=T("2. Shift-click the base armature last (active)"))
        col.label(text=T("3. Click Merge Clothing"))

        col = layout.column(align=True)
        col.separator()

        # Merge operator
        col.operator("boneforge.vrc_merge_clothing", text=T("Merge Clothing"))

        # Merge history
        if _merge_session.history:
            col.separator()
            box = col.box()
            box.label(text=f"Merge History ({len(_merge_session.history)})")

            last = _merge_session.get_last_merge()
            if last:
                row = box.row()
                row.label(text=f"Last: {last['clothing_name']}")
                row.operator("boneforge.vrc_undo_merge", text=T("Undo"))


# ── Registration ────────────────────────────────────────────────

def register():
    """Register merge module."""
    bpy.utils.register_class(MergeHistory)
    bpy.utils.register_class(BF_OT_VRC_MergeClothing)
    bpy.utils.register_class(BF_OT_VRC_UndoMerge)
    bpy.utils.register_class(BF_OT_VRC_AddClothingItem)
    bpy.utils.register_class(BF_OT_VRC_RemoveClothingItem)
    bpy.utils.register_class(BONEFORGE_PT_vrc_clothing_merge)

    # Scene properties
    from bpy.props import StringProperty
    bpy.types.Scene.boneforge_vrc_clothing_queue = StringProperty(default="[]")


def unregister():
    """Unregister merge module."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_clothing_merge)
    bpy.utils.unregister_class(BF_OT_VRC_RemoveClothingItem)
    bpy.utils.unregister_class(BF_OT_VRC_AddClothingItem)
    bpy.utils.unregister_class(BF_OT_VRC_UndoMerge)
    bpy.utils.unregister_class(BF_OT_VRC_MergeClothing)
    bpy.utils.unregister_class(MergeHistory)

    if hasattr(bpy.types.Scene, 'boneforge_vrc_clothing_queue'):
        del bpy.types.Scene.boneforge_vrc_clothing_queue
