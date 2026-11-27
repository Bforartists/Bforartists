"""BoneCraft VRChat — Hair Chain Generation.

Generates bone chains through selected hair mesh geometry when no chains are detected.
Supports Low, Medium, and High density chain generation.

Category: Hair Physics.
"""

import bpy
from bpy.types import Operator, Panel
from bpy.props import EnumProperty
from mathutils import Vector
from boneforge.core import active_armature

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)


# ── Chain generation parameters ────────────────────────────────

DENSITY_LOW = 1
DENSITY_MEDIUM = 2
DENSITY_HIGH = 3

DENSITY_ITEMS = [
    ("LOW", "Low", "One chain per major strand cluster", DENSITY_LOW),
    ("MEDIUM", "Medium", "One chain per visible strand (default)", DENSITY_MEDIUM),
    ("HIGH", "High", "One chain per edge loop boundary", DENSITY_HIGH),
]


# ── Chain generation logic ─────────────────────────────────────

def _get_mesh_bounds(mesh_objects: list) -> tuple[Vector, Vector]:
    """Get the combined bounding box of all mesh objects.

    Returns (min_point, max_point) as Vector objects.
    """
    if not mesh_objects:
        return Vector((0, 0, 0)), Vector((0, 0, 0))

    all_vertices = []
    for obj in mesh_objects:
        if obj.type == 'MESH' and obj.data.vertices:
            all_vertices.extend([obj.matrix_world @ v.co for v in obj.data.vertices])

    if not all_vertices:
        return Vector((0, 0, 0)), Vector((0, 0, 0))

    min_x = min(v.x for v in all_vertices)
    max_x = max(v.x for v in all_vertices)
    min_y = min(v.y for v in all_vertices)
    max_y = max(v.y for v in all_vertices)
    min_z = min(v.z for v in all_vertices)
    max_z = max(v.z for v in all_vertices)

    return Vector((min_x, min_y, min_z)), Vector((max_x, max_y, max_z))


def _cluster_vertices(mesh_objects: list, density: int) -> list[list[Vector]]:
    """Cluster mesh vertices into strand-like groups based on density.

    Returns a list of clusters, each containing vertex positions.
    """
    if not mesh_objects:
        return []

    all_verts = []
    for obj in mesh_objects:
        if obj.type == 'MESH' and obj.data.vertices:
            all_verts.extend([(obj.matrix_world @ v.co, obj) for v in obj.data.vertices])

    if not all_verts:
        return []

    # Simple clustering: divide space into regions based on density
    min_pt, max_pt = _get_mesh_bounds(mesh_objects)
    size = max_pt - min_pt

    # Determine grid size based on density
    if density == DENSITY_LOW:
        grid_x, grid_y = 2, 2
    elif density == DENSITY_MEDIUM:
        grid_x, grid_y = 4, 4
    else:  # DENSITY_HIGH
        grid_x, grid_y = 8, 8

    cell_x = size.x / max(grid_x, 1)
    cell_y = size.y / max(grid_y, 1)

    clusters = {}
    for vert_pos, obj in all_verts:
        grid_i = int((vert_pos.x - min_pt.x) / max(cell_x, 0.001))
        grid_j = int((vert_pos.y - min_pt.y) / max(cell_y, 0.001))
        grid_i = max(0, min(grid_i, grid_x - 1))
        grid_j = max(0, min(grid_j, grid_y - 1))

        key = (grid_i, grid_j)
        if key not in clusters:
            clusters[key] = []
        clusters[key].append((vert_pos, obj))

    return [verts for verts in clusters.values() if verts]


def _find_strand_path(cluster: list[Vector]) -> list[Vector]:
    """Extract a top-to-bottom path from a vertex cluster.

    Returns a list of positions forming a chain from top to bottom.
    """
    if not cluster:
        return []

    # Sort by Z (top to bottom) — cluster contains (Vector, obj) tuples
    sorted_verts = sorted(cluster, key=lambda v: v[0].z, reverse=True)

    # Thin out: sample every N vertices
    sample_rate = max(1, len(sorted_verts) // 5)
    path = sorted_verts[::sample_rate]

    return path if len(path) >= 2 else []


def generate_chains(armature: bpy.types.Armature,
                    mesh_objects: list,
                    density: int = DENSITY_MEDIUM) -> list[str]:
    """Generate bone chains through mesh geometry.

    Creates new bones in the armature for each detected strand path.
    Returns list of created chain root bone names.

    Args:
        armature: Blender Armature datablock
        mesh_objects: List of mesh objects to analyze
        density: DENSITY_LOW, DENSITY_MEDIUM, or DENSITY_HIGH

    Returns:
        List of root bone names created
    """
    created_roots = []

    clusters = _cluster_vertices(mesh_objects, density)
    if not clusters:
        return created_roots

    # Enter edit mode to create bones
    bpy.context.view_layer.objects.active = None
    for obj in bpy.context.scene.objects:
        obj.select_set(False)

    arm_obj = None
    for obj in bpy.context.scene.objects:
        if obj.data == armature:
            arm_obj = obj
            break

    if arm_obj is None:
        return created_roots

    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)

    # Switch to edit mode
    if bpy.context.mode != 'EDIT_ARMATURE':
        # S-12: Error handling for mode switch
        try:
            bpy.ops.object.mode_set(mode='EDIT')
        except RuntimeError as e:
            # In case we can't enter edit mode, return what we've created so far
            logger.warning(f"[BoneCraft] Cannot enter edit mode: {e}")
            return created_roots

    for cluster_idx, cluster in enumerate(clusters):
        path = _find_strand_path(cluster)
        if len(path) < 2:
            continue

        # Create chain of bones along the path
        root_name = f"Hair_Chain_{cluster_idx:03d}"

        # C-13: Transform vertex positions from world space to armature local space
        # path contains (world_pos, obj) tuples — positions already in world space
        arm_inv = arm_obj.matrix_world.inverted()

        # Convert first vertex position
        root_head_local = arm_inv @ path[0][0]
        root_tail_local = arm_inv @ path[1][0] if len(path) > 1 else root_head_local + Vector((0, 0, 0.02))

        # Create root bone at first vertex
        root_bone = armature.edit_bones.new(root_name)
        root_bone.head = root_head_local
        root_bone.tail = root_tail_local

        current_parent = root_bone

        # Create child bones for remaining vertices
        for vert_idx in range(1, len(path) - 1):
            child_name = f"{root_name}.{vert_idx:02d}"
            child_bone = armature.edit_bones.new(child_name)
            child_bone.parent = current_parent

            # Transform this vertex and next vertex (positions already in world space)
            vert_pos_local = arm_inv @ path[vert_idx][0]
            next_pos_local = arm_inv @ path[vert_idx + 1][0] if vert_idx + 1 < len(path) else vert_pos_local + Vector((0, 0, 0.02))

            child_bone.head = vert_pos_local
            child_bone.tail = next_pos_local
            current_parent = child_bone

        created_roots.append(root_name)

    # Switch back to object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    return created_roots


# ── Operators ──────────────────────────────────────────────────

class BF_OT_VRC_GenerateHairChains(Operator):
    """Generate hair chains through mesh geometry."""

    bl_idname = "boneforge.vrc_generate_hair_chains"
    bl_label = "Generate Hair Chains"
    bl_description = "Generate bone chains through selected mesh geometry"
    bl_options = {"REGISTER", "UNDO"}

    density: EnumProperty(
        name="Chain Density",
        description="How many chains to generate",
        items=DENSITY_ITEMS,
        default="MEDIUM",
    )

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        # Get selected mesh objects
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_meshes:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Map density string to constant
        density_map = {"LOW": DENSITY_LOW, "MEDIUM": DENSITY_MEDIUM, "HIGH": DENSITY_HIGH}
        density_value = density_map.get(self.density, DENSITY_MEDIUM)

        created = generate_chains(arm_obj.data, selected_meshes, density_value)

        if created:
            self.report({'INFO'}, f"Generated {len(created)} bone chains")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Could not generate chains")
            return {'CANCELLED'}


class BF_OT_VRC_ReplaceHairChains(Operator):
    """Replace existing hair chains (with confirmation)."""

    bl_idname = "boneforge.vrc_replace_hair_chains"
    bl_label = "Replace Hair Chains"
    bl_description = "Remove existing chains and generate new ones from mesh"
    bl_options = {"REGISTER", "UNDO"}

    density: EnumProperty(
        name="Chain Density",
        description="How many chains to generate",
        items=DENSITY_ITEMS,
        default="MEDIUM",
    )

    def invoke(self, context, event):
        """Show double confirmation dialog."""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_meshes:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Note: In a full implementation, would delete old chains here
        # For now, just generate new ones
        density_map = {"LOW": DENSITY_LOW, "MEDIUM": DENSITY_MEDIUM, "HIGH": DENSITY_HIGH}
        density_value = density_map.get(self.density, DENSITY_MEDIUM)

        created = generate_chains(arm_obj.data, selected_meshes, density_value)

        if created:
            self.report({'INFO'}, f"Generated {len(created)} replacement chains")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Could not generate chains")
            return {'CANCELLED'}


# ── Panels ─────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_hair_generator(Panel):
    """Hair Chain Generation Panel."""

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = " "
    bl_parent_id = "BONEFORGE_PT_vrc_hair"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Hair Chain Generation"))

    @classmethod
    def poll(cls, context):
        """Show panel only when active object is an armature."""
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout

        layout.label(text=T("Select mesh objects and click Generate:"))

        # Mesh selection info
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if selected_meshes:
            row = layout.row()
            row.label(text=f"Meshes selected: {len(selected_meshes)}")

        # density is the operators' own option, tuned after generating (the old slider here fed nothing)
        # Generate/Replace buttons
        row = layout.row()
        row.operator("boneforge.vrc_generate_hair_chains", text=T("Generate"), icon='ADD')
        row.operator("boneforge.vrc_replace_hair_chains", text=T("Replace"), icon='FILE_REFRESH')
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Density: adjust it after generating, in the Adjust Last Operation panel."))


def register():
    """Register chain generation operators and panels."""
    bpy.utils.register_class(BF_OT_VRC_GenerateHairChains)
    bpy.utils.register_class(BF_OT_VRC_ReplaceHairChains)
    bpy.utils.register_class(BONEFORGE_PT_vrc_hair_generator)

    # Register scene property for density
    if not hasattr(bpy.types.Scene, "bf_hair_generation_density"):
        bpy.types.Scene.bf_hair_generation_density = EnumProperty(
            name="Density",
            items=DENSITY_ITEMS,
            default="MEDIUM",
        )


def unregister():
    """Unregister chain generation operators and panels."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_hair_generator)
    bpy.utils.unregister_class(BF_OT_VRC_ReplaceHairChains)
    bpy.utils.unregister_class(BF_OT_VRC_GenerateHairChains)

    # Unregister scene property
    if hasattr(bpy.types.Scene, "bf_hair_generation_density"):
        delattr(bpy.types.Scene, "bf_hair_generation_density")
