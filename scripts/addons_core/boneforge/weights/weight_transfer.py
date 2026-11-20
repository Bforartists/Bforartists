"""BoneCraft Phase 2B — Weight Transfer.

Transfers vertex group weights between meshes using nearest vertex,
nearest face (barycentric), or ray cast methods.
Category: Weight Tools.
"""

import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty, FloatProperty
import numpy as np
from mathutils import Vector

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)


class BONEFORGE_PT_p2b_weight_transfer(bpy.types.Panel):
    """Weight Transfer panel - transfers weights from one mesh to another."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_weight_transfer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Weight Transfer"))

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Source mesh selector
        col = layout.column(align=True)
        col.label(text=T("Source Mesh:"))
        col.prop(scene, "boneforge_transfer_source", text="")

        # Source mesh info display
        source_name = scene.boneforge_transfer_source
        if source_name and source_name in bpy.data.objects:
            src = bpy.data.objects[source_name]
            if src.type == 'MESH':
                col.label(text=f"Vertices: {len(src.data.vertices)}")
                col.label(text=f"Groups: {len(src.vertex_groups)}")

        # Target mesh (usually active)
        col = layout.column(align=True)
        col.label(text=T("Target:"))
        col.label(text=T("Active Object"))

        # act first, tune later: the options are the operators' own, adjusted after the click
        # in Adjust Last Operation (owner's UI critique, 2026-10-10)
        col = layout.column(align=True)
        col.operator("boneforge.transfer_weights", text=T("Transfer Weights"))
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Method, bone filter and normalize: adjust them after transferring, "
                                       "in the Adjust Last Operation panel."))

        # Results display
        if hasattr(scene, "boneforge_transfer_mean_distance"):
            col = layout.column(align=True)
            col.label(text=f"Mean Distance: {scene.boneforge_transfer_mean_distance:.4f}")
            col.label(text=f"Max Distance: {scene.boneforge_transfer_max_distance:.4f}")
            col.label(text=f"Within Threshold: {scene.boneforge_transfer_threshold_percent:.1f}%")
            col.operator("boneforge.select_flagged_transfer", text=T("Select Problem Vertices"))


class BF_OT_TransferWeights(bpy.types.Operator):
    """Transfer vertex weights from source to target mesh."""
    bl_idname = "boneforge.transfer_weights"
    bl_label = "Transfer Weights"
    bl_options = {"REGISTER", "UNDO"}

    # options: tuned after the click in Adjust Last Operation (the source mesh is picked first)
    method: EnumProperty(
        name="Method",
        description="How each target vertex finds its weights on the source mesh",
        items=[("NEAREST_VERTEX", "Nearest Vertex", "Transfer from nearest vertex"),
               ("NEAREST_FACE", "Nearest Face", "Interpolate from nearest face"),
               ("RAY_CAST", "Ray Cast", "Use raycasting to find weights")],
        default="NEAREST_VERTEX",
    )
    bone_filter: EnumProperty(
        name="Bone Filter",
        description="Which bones' vertex groups to transfer",
        items=[("ALL", "All Bones", "Transfer all bones"),
               ("SELECTED_ONLY", "Selected Only", "Only selected bones"),
               ("MATCHING_ONLY", "Matching Only", "Only bones in both armatures")],
        default="ALL",
    )
    normalize: BoolProperty(
        name="Normalize",
        description="Normalize weights after transfer",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == "PAINT_WEIGHT" and
                context.active_object and
                context.active_object.type == "MESH")

    def execute(self, context):
        scene = context.scene
        target_obj = context.active_object
        target_mesh = target_obj.data

        # Get source mesh
        source_name = scene.boneforge_transfer_source
        if not source_name or source_name not in bpy.data.objects:
            self.report({"ERROR"}, "Source mesh not found")
            return {"CANCELLED"}

        source_obj = bpy.data.objects[source_name]
        if source_obj.type != "MESH":
            self.report({"ERROR"}, "Source object is not a mesh")
            return {"CANCELLED"}

        source_mesh = source_obj.data
        transfer_method = self.method
        bone_filter = self.bone_filter
        normalize = self.normalize

        # Get list of vertex groups to transfer
        vgroups_to_transfer = []

        # Get selected bones if SELECTED_ONLY filter is used
        selected_bone_names = set()
        if bone_filter == "SELECTED_ONLY":
            if hasattr(context, 'selected_pose_bones') and context.selected_pose_bones:
                selected_bone_names = {bone.name for bone in context.selected_pose_bones}

        for vg in source_obj.vertex_groups:
            if bone_filter == "ALL":
                vgroups_to_transfer.append(vg.name)
            elif bone_filter == "SELECTED_ONLY":
                if vg.name in selected_bone_names:
                    vgroups_to_transfer.append(vg.name)
            elif bone_filter == "MATCHING_ONLY":
                if vg.name in [vg_target.name for vg_target in target_obj.vertex_groups]:
                    vgroups_to_transfer.append(vg.name)

        if not vgroups_to_transfer:
            self.report({"WARNING"}, "No vertex groups to transfer")
            return {"CANCELLED"}

        # Validate source mesh prerequisites before mutating target groups
        if transfer_method == "NEAREST_VERTEX" and len(source_mesh.vertices) == 0:
            self.report({"ERROR"}, "Source mesh has no vertices")
            return {"CANCELLED"}
        if transfer_method == "NEAREST_FACE" and len(source_mesh.polygons) == 0:
            self.report({"ERROR"}, "Source mesh has no faces")
            return {"CANCELLED"}

        # Ensure target has vertex groups
        for vg_name in vgroups_to_transfer:
            if vg_name not in target_obj.vertex_groups:
                target_obj.vertex_groups.new(name=vg_name)

        distances = []
        flagged_vertices = []

        if transfer_method == "NEAREST_VERTEX":
            self._transfer_nearest_vertex(source_obj, target_obj, vgroups_to_transfer,
                                        distances, flagged_vertices)
        elif transfer_method == "NEAREST_FACE":
            self._transfer_nearest_face(source_obj, target_obj, vgroups_to_transfer,
                                       distances, flagged_vertices)
        elif transfer_method == "RAY_CAST":
            self._transfer_raycast(source_obj, target_obj, vgroups_to_transfer,
                                  distances, flagged_vertices)

        # Store results in scene properties
        if distances:
            mean_dist = np.mean(distances)
            max_dist = np.max(distances)
            threshold = 0.01  # Default threshold
            within_threshold = sum(1 for d in distances if d <= threshold) / len(distances) * 100
        else:
            mean_dist = 0.0
            max_dist = 0.0
            within_threshold = 100.0

        scene.boneforge_transfer_mean_distance = mean_dist
        scene.boneforge_transfer_max_distance = max_dist
        scene.boneforge_transfer_threshold_percent = within_threshold
        # v3.1.6 (C-4): IntVectorProperty is fixed-size 3, so the previous
        # assignment silently corrupted the list. Encode as CSV string.
        scene.boneforge_transfer_flagged_vertices = ','.join(
            str(idx) for idx in flagged_vertices
        )

        # Normalize if requested
        if normalize:
            self._normalize_weights(target_obj)

        self.report({"INFO"}, f"Transferred weights to {len(target_mesh.vertices)} vertices")
        return {"FINISHED"}

    def _transfer_nearest_vertex(self, source_obj, target_obj, vgroups, distances, flagged):
        """Transfer weights using nearest vertex method with KDTree."""
        source_mesh = source_obj.data
        target_mesh = target_obj.data

        # v3.1.6 (M-2): mathutils.kdtree is built into Blender — the previous
        # ImportError fallback was dead code that nobody could reach.
        from mathutils import kdtree
        kd = kdtree.KDTree(len(source_mesh.vertices))

        # Use KDTree
        for i, vert in enumerate(source_mesh.vertices):
            kd.insert(vert.co, i)
        kd.balance()

        src_inv_mat = source_obj.matrix_world.inverted()
        tgt_mat = target_obj.matrix_world

        for target_vert in target_mesh.vertices:
            query_co = src_inv_mat @ (tgt_mat @ target_vert.co)
            found, source_idx, dist = kd.find_nearest(query_co)
            if found:
                distances.append(dist)
                if dist > 0.01:
                    flagged.append(target_vert.index)

                # v3.1.6 (M-1): read assigned-only weights from the source vertex.
                source_vert = source_mesh.vertices[source_idx]
                source_weights = {
                    source_obj.vertex_groups[vge.group].name: vge.weight
                    for vge in source_vert.groups
                }
                for vg_name in vgroups:
                    weight = source_weights.get(vg_name, 0.0)
                    if weight > 0.0:
                        target_obj.vertex_groups[vg_name].add(
                            [target_vert.index], weight, "REPLACE",
                        )

    def _transfer_nearest_face(self, source_obj, target_obj, vgroups, distances, flagged):
        """Transfer weights using nearest face with barycentric interpolation."""
        from mathutils import kdtree
        source_mesh = source_obj.data
        target_mesh = target_obj.data

        # Precompute source face centers once (same "simple face center distance" semantic)
        face_centers = []
        for face in source_mesh.polygons:
            face_center = sum((source_mesh.vertices[vi].co for vi in face.vertices), Vector()) / len(face.vertices)
            face_centers.append(face_center)

        # Build KDTree over face centers for O(log F) per-query lookup
        kd = kdtree.KDTree(len(face_centers))
        for i, center in enumerate(face_centers):
            kd.insert(center, i)
        kd.balance()

        src_inv_mat = source_obj.matrix_world.inverted()
        tgt_mat = target_obj.matrix_world

        for target_vert in target_mesh.vertices:
            query_co = src_inv_mat @ (tgt_mat @ target_vert.co)
            nearest_co, face_idx, min_dist = kd.find(query_co)
            if face_idx is None:
                min_dist = float('inf')
                nearest_face = None
                nearest_co = None
            else:
                min_dist = float(min_dist)
                nearest_face = source_mesh.polygons[face_idx]

            distances.append(min_dist)
            if min_dist > 0.01:
                flagged.append(target_vert.index)

            if nearest_face:
                # v3.1.6 (M-1): build a per-face-vertex weight table once,
                # then average per requested group. Replaces O(face_verts *
                # vgroups) RuntimeError-driven lookups.
                face_vert_weights = []
                for vertex_index in nearest_face.vertices:
                    sv = source_mesh.vertices[vertex_index]
                    face_vert_weights.append({
                        source_obj.vertex_groups[vge.group].name: vge.weight
                        for vge in sv.groups
                    })

                face_vert_count = len(face_vert_weights)
                if face_vert_count == 0:
                    continue

                for vg_name in vgroups:
                    avg_weight = sum(
                        per_vert.get(vg_name, 0.0) for per_vert in face_vert_weights
                    ) / face_vert_count
                    if avg_weight > 0.0:
                        target_obj.vertex_groups[vg_name].add(
                            [target_vert.index], avg_weight, "REPLACE",
                        )

    def _transfer_raycast(self, source_obj, target_obj, vgroups, distances, flagged):
        """Transfer weights using raycasting."""
        source_mesh = source_obj.data
        target_mesh = target_obj.data

        for target_vert in target_mesh.vertices:
            # Cast rays in multiple directions
            ray_dir = Vector((0, 0, 1))  # Default ray direction

            # Transform target vertex to source object local space
            world_co = target_obj.matrix_world @ target_vert.co
            local_co = source_obj.matrix_world.inverted() @ world_co
            local_dir = (source_obj.matrix_world.inverted().to_3x3() @ ray_dir).normalized()

            # ray_cast returns (bool, Vector, Vector, int)
            hit, location, normal, face_index = source_obj.ray_cast(local_co, local_dir)

            if hit:
                # Find closest vertex on hit face
                if face_index is not None:
                    face = source_mesh.polygons[face_index]
                    min_dist = float('inf')
                    closest_vert_idx = None

                    for vertex_index in face.vertices:
                        vert = source_mesh.vertices[vertex_index]
                        vert_world = source_obj.matrix_world @ vert.co
                        dist = (world_co - vert_world).length
                        if dist < min_dist:
                            min_dist = dist
                            closest_vert_idx = vertex_index

                    if closest_vert_idx is not None:
                        distances.append(min_dist)
                        if min_dist > 0.01:
                            flagged.append(target_vert.index)

                        # v3.1.6 (M-1): assigned-only weight read.
                        source_vert = source_mesh.vertices[closest_vert_idx]
                        source_weights = {
                            source_obj.vertex_groups[vge.group].name: vge.weight
                            for vge in source_vert.groups
                        }
                        for vg_name in vgroups:
                            weight = source_weights.get(vg_name, 0.0)
                            if weight > 0.0:
                                target_obj.vertex_groups[vg_name].add(
                                    [target_vert.index], weight, "REPLACE",
                                )
                    else:
                        distances.append(float('inf'))
                        flagged.append(target_vert.index)
                else:
                    distances.append(float('inf'))
                    flagged.append(target_vert.index)
            else:
                distances.append(float('inf'))
                flagged.append(target_vert.index)

    def _normalize_weights(self, obj):
        """Normalize vertex weights for all vertices.

        v3.1.6 (M-1): walk vert.groups (assigned-only) instead of every
        vertex group with try/except RuntimeError. Materially faster on
        production meshes — no behaviour change.
        """
        mesh = obj.data
        for vert in mesh.vertices:
            weights = {vge.group: vge.weight for vge in vert.groups if vge.weight > 0.0}
            total_weight = sum(weights.values())
            if total_weight > 0.0 and total_weight != 1.0:
                inv = 1.0 / total_weight
                for vg_idx, weight in weights.items():
                    obj.vertex_groups[vg_idx].add(
                        [vert.index], weight * inv, "REPLACE",
                    )


class BF_OT_SelectFlaggedTransfer(bpy.types.Operator):
    """Select vertices that exceeded transfer distance threshold."""
    bl_idname = "boneforge.select_flagged_transfer"
    bl_label = "Select Flagged Vertices"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == "MESH")

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        mesh = obj.data

        flagged_csv = getattr(scene, "boneforge_transfer_flagged_vertices", "")
        if not flagged_csv:
            self.report({"WARNING"}, "No flagged vertices from previous transfer")
            return {"CANCELLED"}

        # v3.1.6 (C-4): decode CSV; tolerate empty entries.
        flagged = [
            int(token) for token in flagged_csv.split(",")
            if token.strip().isdigit()
        ]
        if not flagged:
            self.report({"WARNING"}, "No flagged vertices from previous transfer")
            return {"CANCELLED"}

        # Switch to edit mode if needed
        if context.mode != "EDIT_MESH":
            bpy.ops.object.mode_set(mode="EDIT")

        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)

        bpy.ops.object.mode_set(mode="OBJECT")
        for vert_idx in flagged:
            if 0 <= vert_idx < len(mesh.vertices):
                mesh.vertices[vert_idx].select = True

        bpy.ops.object.mode_set(mode="EDIT")

        self.report({"INFO"}, f"Selected {len(flagged)} flagged vertices")
        return {"FINISHED"}


def register():
    """Register weight transfer classes and properties."""
    bpy.utils.register_class(BONEFORGE_PT_p2b_weight_transfer)
    bpy.utils.register_class(BF_OT_TransferWeights)
    bpy.utils.register_class(BF_OT_SelectFlaggedTransfer)

    # Scene properties
    bpy.types.Scene.boneforge_transfer_source = StringProperty(
        name="Source Mesh",
        description="Source mesh to transfer weights from",
        default=""
    )

    bpy.types.Scene.boneforge_transfer_method = EnumProperty(
        name="Transfer Method",
        items=[("NEAREST_VERTEX", "Nearest Vertex", "Transfer from nearest vertex"),
               ("NEAREST_FACE", "Nearest Face", "Interpolate from nearest face"),
               ("RAY_CAST", "Ray Cast", "Use raycasting to find weights")],
        default="NEAREST_VERTEX"
    )

    bpy.types.Scene.boneforge_transfer_bone_filter = EnumProperty(
        name="Bone Filter",
        items=[("ALL", "All Bones", "Transfer all bones"),
               ("SELECTED_ONLY", "Selected Only", "Only selected bones"),
               ("MATCHING_ONLY", "Matching Only", "Only bones in both armatures")],
        default="ALL"
    )

    bpy.types.Scene.boneforge_transfer_normalize = BoolProperty(
        name="Normalize",
        description="Normalize weights after transfer",
        default=True
    )

    bpy.types.Scene.boneforge_transfer_mean_distance = FloatProperty(default=0.0)
    bpy.types.Scene.boneforge_transfer_max_distance = FloatProperty(default=0.0)
    bpy.types.Scene.boneforge_transfer_threshold_percent = FloatProperty(default=0.0)
    # v3.1.6 (C-4): variable-length list of ints — IntVectorProperty
    # is fixed-size 3, so we store as a comma-separated StringProperty.
    bpy.types.Scene.boneforge_transfer_flagged_vertices = StringProperty(default="")


def unregister():
    """Unregister weight transfer classes and properties."""
    bpy.utils.unregister_class(BONEFORGE_PT_p2b_weight_transfer)
    bpy.utils.unregister_class(BF_OT_TransferWeights)
    bpy.utils.unregister_class(BF_OT_SelectFlaggedTransfer)

    # Clean up properties
    if hasattr(bpy.types.Scene, "boneforge_transfer_source"):
        del bpy.types.Scene.boneforge_transfer_source
    if hasattr(bpy.types.Scene, "boneforge_transfer_method"):
        del bpy.types.Scene.boneforge_transfer_method
    if hasattr(bpy.types.Scene, "boneforge_transfer_bone_filter"):
        del bpy.types.Scene.boneforge_transfer_bone_filter
    if hasattr(bpy.types.Scene, "boneforge_transfer_normalize"):
        del bpy.types.Scene.boneforge_transfer_normalize
    if hasattr(bpy.types.Scene, "boneforge_transfer_mean_distance"):
        del bpy.types.Scene.boneforge_transfer_mean_distance
    if hasattr(bpy.types.Scene, "boneforge_transfer_max_distance"):
        del bpy.types.Scene.boneforge_transfer_max_distance
    if hasattr(bpy.types.Scene, "boneforge_transfer_threshold_percent"):
        del bpy.types.Scene.boneforge_transfer_threshold_percent
    if hasattr(bpy.types.Scene, "boneforge_transfer_flagged_vertices"):
        del bpy.types.Scene.boneforge_transfer_flagged_vertices
