"""BoneCraft Phase 2B — Weight Mirror.

Mirrors vertex group weights across a symmetry axis (X, Y, or Z)
with configurable direction and topology/positional matching.
Category: Weight Tools.
"""

import bpy
from bpy.props import EnumProperty, BoolProperty, FloatProperty, StringProperty

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)


class BONEFORGE_PT_p2b_weight_mirror(bpy.types.Panel):
    """Weight Mirror panel - mirrors vertex group weights across symmetry axis."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_weight_mirror"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Weight Mirror"))

    @classmethod
    def poll(cls, context):
        # M-04: Defensive check to ensure properties exist
        return (context.mode == "PAINT_WEIGHT" and
                context.scene is not None and
                hasattr(bpy.types.Scene, 'boneforge_mirror_mirrored_count'))

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # act first, tune later: the options are the operators' own, adjusted after the click
        # in Adjust Last Operation (owner's UI critique, 2026-10-10)
        col = layout.column(align=True)
        col.operator("boneforge.mirror_all_weights", text=T("Mirror All Weights"))
        col.operator("boneforge.mirror_active_weight", text=T("Mirror Active Weight"))
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Axis, direction and search distance: adjust them after mirroring, "
                                       "in the Adjust Last Operation panel."))

        # Results display
        if hasattr(scene, "boneforge_mirror_mirrored_count"):
            col = layout.column(align=True)
            col.label(text=f"Mirrored: {scene.boneforge_mirror_mirrored_count}")
            col.label(text=f"Unmatched: {scene.boneforge_mirror_unmatched_count}")
            col.operator("boneforge.select_unmatched_vertices", text=T("Select Unmatched"))
            col.label(text=T("Weights may need normalization"))
            col.operator("boneforge.normalize_mirrored_weights", text=T("Normalize Weights"))


class _MirrorOptions:
    """Mirror options: the operator's own, tuned after the click in Adjust Last Operation."""
    axis: EnumProperty(
        name="Axis",
        description="Axis to mirror across",
        items=[("X", "X", "Mirror across X axis"),
               ("Y", "Y", "Mirror across Y axis"),
               ("Z", "Z", "Mirror across Z axis")],
        default="X",
    )
    direction: EnumProperty(
        name="Direction",
        description="Which side's weights are copied to the other",
        items=[("LEFT_TO_RIGHT", "Left → Right", "Mirror left to right"),
               ("RIGHT_TO_LEFT", "Right → Left", "Mirror right to left"),
               ("BIDIRECTIONAL", "Bidirectional", "Mirror both ways and average")],
        default="LEFT_TO_RIGHT",
    )
    search_distance: FloatProperty(
        name="Search Distance",
        description="Maximum distance to search for the mirror vertex",
        default=0.001, min=0.0, step=0.001,
    )


class BF_OT_MirrorAllWeights(_MirrorOptions, bpy.types.Operator):
    """Mirror all vertex groups across symmetry axis."""
    bl_idname = "boneforge.mirror_all_weights"
    bl_label = "Mirror All Weights"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.mode == "PAINT_WEIGHT" and
                context.active_object and
                context.active_object.type == "MESH")

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        scene = context.scene

        # Get mirror parameters
        axis = self.axis
        direction = self.direction
        search_dist = self.search_distance

        # Build KDTree for efficient vertex matching
        from mathutils import kdtree
        kd = kdtree.KDTree(len(mesh.vertices))
        for i, vert in enumerate(mesh.vertices):
            kd.insert(vert.co, i)
        kd.balance()

        # Get axis index
        axis_idx = {"X": 0, "Y": 1, "Z": 2}[axis]

        mirrored_count = 0
        unmatched_count = 0

        # v3.1.6 (M-1, M-3): pre-build a {(vert_idx, group_idx): weight} table
        # so each vertex group iteration walks only the verts that actually
        # belong to it. Replaces O(V * G) RuntimeError-driven scans.
        verts_by_group: dict[int, dict[int, float]] = {}
        for vert in mesh.vertices:
            for vge in vert.groups:
                if vge.weight > 0.0:
                    verts_by_group.setdefault(vge.group, {})[vert.index] = vge.weight
        unmatched_set: set[int] = set()

        # Mirror each vertex group
        for vgroup in obj.vertex_groups:
            assigned = verts_by_group.get(vgroup.index, {})
            for vert_idx, weight in assigned.items():
                vert = mesh.vertices[vert_idx]

                # Check vertex selection mask if enabled
                if mesh.use_paint_mask_vertex and not vert.select:
                    continue

                # Find mirror vertex
                mirror_co = vert.co.copy()
                mirror_co[axis_idx] *= -1

                # v3.1.6 (M-4): the previous if/else used the same spatial
                # search for both branches — "use topology" was a dead
                # toggle. Genuine topology-based mirroring is a TODO and
                # would call bpy.ops.object.vertex_group_mirror or walk the
                # mesh\'s mirror map; for now we always do spatial.
                found, mirror_idx, dist = kd.find_nearest(mirror_co)

                if found and dist <= search_dist:
                    if direction == "BIDIRECTIONAL":
                        # v3.1.6 (M-1): mirror weight from precomputed table.
                        mirror_weight = assigned.get(mirror_idx, 0.0)
                        avg_weight = (weight + mirror_weight) / 2.0
                        vgroup.add([vert_idx], avg_weight, "REPLACE")
                        vgroup.add([mirror_idx], avg_weight, "REPLACE")
                        mirrored_count += 1
                    else:
                        if direction == "LEFT_TO_RIGHT":
                            if mirror_co[axis_idx] > vert.co[axis_idx]:
                                vgroup.add([mirror_idx], weight, "REPLACE")
                                mirrored_count += 1

                        if direction == "RIGHT_TO_LEFT":
                            if mirror_co[axis_idx] < vert.co[axis_idx]:
                                vgroup.add([mirror_idx], weight, "REPLACE")
                                mirrored_count += 1
                else:
                    # v3.1.6 (M-3): set membership is O(1).
                    unmatched_set.add(vert_idx)
                    unmatched_count += 1

        scene.boneforge_mirror_mirrored_count = mirrored_count
        scene.boneforge_mirror_unmatched_count = unmatched_count
        scene.boneforge_mirror_unmatched_vertices = ",".join(
            str(i) for i in sorted(unmatched_set)
        )

        self.report({"INFO"}, f"Mirrored {mirrored_count} weights, {unmatched_count} unmatched")
        return {"FINISHED"}


class BF_OT_MirrorActiveWeight(_MirrorOptions, bpy.types.Operator):
    """Mirror only the active vertex group."""
    bl_idname = "boneforge.mirror_active_weight"
    bl_label = "Mirror Active Weight"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.mode == "PAINT_WEIGHT" and
                context.active_object and
                context.active_object.type == "MESH" and
                context.active_object.vertex_groups.active)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        scene = context.scene
        vgroup = obj.vertex_groups.active

        # Get mirror parameters
        axis = self.axis
        direction = self.direction
        search_dist = self.search_distance

        # Build KDTree
        from mathutils import kdtree
        kd = kdtree.KDTree(len(mesh.vertices))
        for i, vert in enumerate(mesh.vertices):
            kd.insert(vert.co, i)
        kd.balance()

        axis_idx = {"X": 0, "Y": 1, "Z": 2}[axis]

        mirrored_count = 0
        unmatched_count = 0
        unmatched_set: set[int] = set()

        # v3.1.6 (M-1): build {vert_idx: weight} for the active group only.
        assigned = {
            vert.index: vge.weight
            for vert in mesh.vertices
            for vge in vert.groups
            if vge.group == vgroup.index and vge.weight > 0.0
        }

        for vert_idx, weight in assigned.items():
            vert = mesh.vertices[vert_idx]

            # Check vertex selection mask if enabled
            if mesh.use_paint_mask_vertex and not vert.select:
                continue

            # Find mirror vertex
            mirror_co = vert.co.copy()
            mirror_co[axis_idx] *= -1

            found, mirror_idx, dist = kd.find_nearest(mirror_co)

            if found and dist <= search_dist:
                if direction == "BIDIRECTIONAL":
                    # v3.1.6 (M-1): mirror weight from precomputed table.
                    mirror_weight = assigned.get(mirror_idx, 0.0)

                    avg_weight = (weight + mirror_weight) / 2.0
                    vgroup.add([vert_idx], avg_weight, "REPLACE")
                    vgroup.add([mirror_idx], avg_weight, "REPLACE")
                    mirrored_count += 1
                else:
                    if direction == "LEFT_TO_RIGHT":
                        if mirror_co[axis_idx] > vert.co[axis_idx]:
                            vgroup.add([mirror_idx], weight, "REPLACE")
                            mirrored_count += 1

                    if direction == "RIGHT_TO_LEFT":
                        if mirror_co[axis_idx] < vert.co[axis_idx]:
                            vgroup.add([mirror_idx], weight, "REPLACE")
                            mirrored_count += 1
            else:
                # v3.1.6 (M-3): set membership is O(1).
                unmatched_set.add(vert_idx)
                unmatched_count += 1

        scene.boneforge_mirror_mirrored_count = mirrored_count
        scene.boneforge_mirror_unmatched_count = unmatched_count
        scene.boneforge_mirror_unmatched_vertices = ",".join(
            str(i) for i in sorted(unmatched_set)
        )

        self.report({"INFO"}, f"Mirrored {mirrored_count} weights, {unmatched_count} unmatched")
        return {"FINISHED"}


class BF_OT_NormalizeMirroredWeights(bpy.types.Operator):
    """Normalize vertex weights after mirroring operation."""
    bl_idname = "boneforge.normalize_mirrored_weights"
    bl_label = "Normalize Mirrored Weights"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == "MESH")

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # v3.1.6 (M-1): normalize via assigned-only weight read.
        for vert in mesh.vertices:
            weights = {vge.group: vge.weight for vge in vert.groups if vge.weight > 0.0}
            total_weight = sum(weights.values())
            if total_weight > 0.0 and total_weight != 1.0:
                inv = 1.0 / total_weight
                for vg_idx, weight in weights.items():
                    obj.vertex_groups[vg_idx].add(
                        [vert.index], weight * inv, "REPLACE",
                    )

        self.report({"INFO"}, f"Normalized weights for {len(mesh.vertices)} vertices")
        return {"FINISHED"}


class BF_OT_SelectUnmatched(bpy.types.Operator):
    """Select vertices that couldn't find a mirror match."""
    bl_idname = "boneforge.select_unmatched_vertices"
    bl_label = "Select Unmatched"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == "MESH")

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        scene = context.scene

        if not hasattr(scene, "boneforge_mirror_unmatched_vertices"):
            self.report({"WARNING"}, "No unmatched vertices from previous mirror operation")
            return {"CANCELLED"}

        # Switch to edit mode
        if context.mode != "EDIT_MESH":
            bpy.ops.object.mode_set(mode="EDIT")

        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)  # Vertex mode

        # Select unmatched vertices - parse comma-separated string
        bpy.ops.object.mode_set(mode="OBJECT")
        unmatched_str = scene.boneforge_mirror_unmatched_vertices
        if unmatched_str:
            unmatched_list = [int(idx) for idx in unmatched_str.split(",") if idx.strip()]
        else:
            unmatched_list = []

        for vert_idx in unmatched_list:
            if vert_idx < len(mesh.vertices):
                mesh.vertices[vert_idx].select = True

        bpy.ops.object.mode_set(mode="EDIT")

        self.report({"INFO"}, f"Selected {len(unmatched_list)} unmatched vertices")
        return {"FINISHED"}


def register():
    """Register weight mirror classes and properties and scene properties."""
    bpy.utils.register_class(BONEFORGE_PT_p2b_weight_mirror)
    bpy.utils.register_class(BF_OT_MirrorAllWeights)
    bpy.utils.register_class(BF_OT_MirrorActiveWeight)
    bpy.utils.register_class(BF_OT_NormalizeMirroredWeights)
    bpy.utils.register_class(BF_OT_SelectUnmatched)

    # Scene properties
    bpy.types.Scene.boneforge_mirror_axis = EnumProperty(
        name="Mirror Axis",
        items=[("X", "X", "Mirror across X axis"),
               ("Y", "Y", "Mirror across Y axis"),
               ("Z", "Z", "Mirror across Z axis")],
        default="X"
    )

    bpy.types.Scene.boneforge_mirror_direction = EnumProperty(
        name="Mirror Direction",
        items=[("LEFT_TO_RIGHT", "Left → Right", "Mirror left to right"),
               ("RIGHT_TO_LEFT", "Right → Left", "Mirror right to left"),
               ("BIDIRECTIONAL", "Bidirectional", "Mirror both ways and average")],
        default="LEFT_TO_RIGHT"
    )

    bpy.types.Scene.boneforge_use_mirror_topology = BoolProperty(
        name="Topology Mirror",
        description="Use mesh topology for mirroring",
        default=False
    )

    bpy.types.Scene.boneforge_mirror_search_distance = FloatProperty(
        name="Search Distance",
        description="Maximum distance to search for mirror vertex",
        default=0.001,
        min=0.0,
        step=0.001
    )

    bpy.types.Scene.boneforge_mirror_mirrored_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.boneforge_mirror_unmatched_count = bpy.props.IntProperty(default=0)
    bpy.types.Scene.boneforge_mirror_unmatched_vertices = StringProperty(default="")


def unregister():
    """Unregister weight mirror classes and properties."""
    bpy.utils.unregister_class(BONEFORGE_PT_p2b_weight_mirror)
    bpy.utils.unregister_class(BF_OT_MirrorAllWeights)
    bpy.utils.unregister_class(BF_OT_MirrorActiveWeight)
    bpy.utils.unregister_class(BF_OT_NormalizeMirroredWeights)
    bpy.utils.unregister_class(BF_OT_SelectUnmatched)

    # Clean up scene properties
    if hasattr(bpy.types.Scene, "boneforge_mirror_axis"):
        del bpy.types.Scene.boneforge_mirror_axis
    if hasattr(bpy.types.Scene, "boneforge_mirror_direction"):
        del bpy.types.Scene.boneforge_mirror_direction
    if hasattr(bpy.types.Scene, "boneforge_use_mirror_topology"):
        del bpy.types.Scene.boneforge_use_mirror_topology
    if hasattr(bpy.types.Scene, "boneforge_mirror_search_distance"):
        del bpy.types.Scene.boneforge_mirror_search_distance
    if hasattr(bpy.types.Scene, "boneforge_mirror_mirrored_count"):
        del bpy.types.Scene.boneforge_mirror_mirrored_count
    if hasattr(bpy.types.Scene, "boneforge_mirror_unmatched_count"):
        del bpy.types.Scene.boneforge_mirror_unmatched_count
    if hasattr(bpy.types.Scene, "boneforge_mirror_unmatched_vertices"):
        del bpy.types.Scene.boneforge_mirror_unmatched_vertices
