"""BoneCraft VRChat — Blendshape-Safe Decimation.

Decimate meshes while preserving blendshape (shape key) geometry fidelity.
Protects vertices used by shape keys and validates post-decimation integrity.
Category: Performance.
"""

import bpy
from bpy.props import (
    FloatProperty,
    BoolProperty,
    PointerProperty,
    EnumProperty,
)
from boneforge.i18n import T
from bpy.types import Operator, Panel, PropertyGroup


# ── Settings property group ────────────────────────────────────

class BF_VRCDecimationSettings(PropertyGroup):
    """Decimation configuration."""

    target_ratio: FloatProperty(
        name="Decimate Ratio",
        description="Target polygon count ratio (0.0 = remove all, 1.0 = keep all)",
        min=0.01, max=1.0,
        default=0.5,
    )
    target_polygon_count: FloatProperty(
        name="Target Polygon Count",
        description="Target absolute polygon count (overrides ratio if > 0)",
        min=0, max=1000000,
        default=0,
    )
    shape_key_safety: BoolProperty(
        name="Shape Key Safety",
        description="Protect vertices used by shape keys from decimation",
        default=True,
    )
    tolerance: FloatProperty(
        name="Deviation Tolerance",
        description="Maximum allowed shape key delta deviation (0.001 = 0.1%)",
        min=0.0, max=0.1,
        default=0.001,
    )
    use_mode: EnumProperty(
        name="Target Mode",
        items=[
            ('RATIO', "Ratio", "Use polygon count ratio"),
            ('COUNT', "Count", "Use absolute polygon count"),
        ],
        default='RATIO',
    )


# ── Helpers ─────────────────────────────────────────────────────

def _get_shape_key_vertices(mesh_obj):
    """Get set of vertex indices with non-zero shape key influence.

    Args:
        mesh_obj: Mesh object

    Returns:
        Set of vertex indices
    """
    protected_verts = set()

    if mesh_obj.data.shape_keys is None:
        return protected_verts

    for shape_key in mesh_obj.data.shape_keys.key_blocks:
        if shape_key.name == "Basis":
            continue

        for i, key_point in enumerate(shape_key.data):
            # Check if vertex has significant delta from basis
            if key_point.co.length > 0.00001:
                protected_verts.add(i)

    return protected_verts


def _create_protection_vertex_group(mesh_obj, protected_verts):
    """Create or update a vertex group for protected vertices.

    Args:
        mesh_obj: Mesh object
        protected_verts: Set of vertex indices to protect

    Returns:
        Vertex group name
    """
    group_name = "BF_Decimate_Protect"

    # Create or clear group
    if group_name in mesh_obj.vertex_groups:
        mesh_obj.vertex_groups.remove(mesh_obj.vertex_groups[group_name])

    vgroup = mesh_obj.vertex_groups.new(name=group_name)

    # Add protected vertices
    for vert_idx in protected_verts:
        vgroup.add([vert_idx], 1.0, 'ADD')

    return group_name


def _snapshot_shape_keys(mesh_obj):
    """Capture shape key statistical signatures before decimation.

    Uses aggregate statistics (not per-vertex data) so comparisons
    remain valid after vertex count changes from decimation.

    Args:
        mesh_obj: Mesh object

    Returns:
        dict mapping shape key name to statistical signature dict
    """
    snapshots = {}
    mesh = mesh_obj.data
    if not mesh.shape_keys:
        return snapshots

    basis = mesh.shape_keys.key_blocks[0]
    basis_coords = [v.co.copy() for v in basis.data]

    for kb in mesh.shape_keys.key_blocks[1:]:
        deltas = []
        for i, sv in enumerate(kb.data):
            delta = (sv.co - basis_coords[i]).length
            if delta > 0.00001:
                deltas.append(delta)

        affected_count = len(deltas)
        if affected_count > 0:
            snapshots[kb.name] = {
                'affected_vertices': affected_count,
                'affected_ratio': affected_count / len(basis_coords),
                'mean_delta': sum(deltas) / affected_count,
                'max_delta': max(deltas),
            }
        else:
            snapshots[kb.name] = {
                'affected_vertices': 0,
                'affected_ratio': 0.0,
                'mean_delta': 0.0,
                'max_delta': 0.0,
            }
    return snapshots


def _compare_shape_keys(mesh_obj, pre_snapshot, tolerance=0.001):
    """Compare post-decimation shape keys against pre-decimation signatures.

    Compares statistical signatures rather than per-vertex data, making
    comparisons valid after vertex count changes from decimation.

    Args:
        mesh_obj: Mesh object
        pre_snapshot: Pre-decimation snapshot from _snapshot_shape_keys
        tolerance: Maximum allowed deviation

    Returns:
        list of issue strings describing detected degradation
    """
    issues = []
    post_snapshot = _snapshot_shape_keys(mesh_obj)

    for name, pre in pre_snapshot.items():
        if name not in post_snapshot:
            issues.append(f"Shape key '{name}' lost after decimation")
            continue

        post = post_snapshot[name]

        if pre['affected_vertices'] == 0:
            continue

        # Check if affected ratio dropped significantly
        ratio_drop = pre['affected_ratio'] - post['affected_ratio']
        if ratio_drop > 0.2:
            issues.append(
                f"Shape key '{name}' lost {ratio_drop:.0%} of affected vertices"
            )

        # Check mean delta shift
        mean_shift = abs(pre['mean_delta'] - post['mean_delta'])
        if mean_shift > tolerance:
            issues.append(
                f"Shape key '{name}' mean delta shifted by {mean_shift:.6f}"
            )

        # Check max delta shift
        max_shift = abs(pre['max_delta'] - post['max_delta'])
        if max_shift > tolerance * 2:
            issues.append(
                f"Shape key '{name}' max delta shifted by {max_shift:.6f}"
            )

    return issues


# ── Operators ───────────────────────────────────────────────────

class BF_OT_VRC_ProtectBlendshapeRegions(Operator):
    """Mark and protect all vertices used by shape keys."""
    bl_idname = "boneforge.vrc_protect_blendshape_regions"
    bl_label = "Protect Blendshape Regions"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'MESH' and
                obj.data.shape_keys is not None)

    def execute(self, context):
        mesh_obj = context.object

        protected_verts = _get_shape_key_vertices(mesh_obj)
        if not protected_verts:
            self.report({'INFO'}, "No shape key vertices found to protect")
            return {'CANCELLED'}

        group_name = _create_protection_vertex_group(mesh_obj, protected_verts)
        self.report({'INFO'}, f"Protected {len(protected_verts)} vertices in group '{group_name}'")
        return {'FINISHED'}


class BF_OT_VRC_PreviewDecimation(Operator):
    """Preview decimation effect without applying it."""
    bl_idname = "boneforge.vrc_preview_decimation"
    bl_label = "Preview Decimation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        mesh_obj = context.object
        settings = mesh_obj.boneforge_vrc_decimation

        # Create a temporary modifier for preview
        mod_name = "BF_Decimate_Preview"
        if mod_name in mesh_obj.modifiers:
            mesh_obj.modifiers.remove(mesh_obj.modifiers[mod_name])

        mod = mesh_obj.modifiers.new(name=mod_name, type='DECIMATE')

        # Configure based on settings
        if settings.use_mode == 'RATIO':
            mod.ratio = settings.target_ratio
        else:
            # Estimate ratio from absolute count
            current_count = len(mesh_obj.data.polygons)
            if current_count > 0:
                mod.ratio = max(0.01, settings.target_polygon_count / current_count)

        # Use vertex group protection if available
        if (settings.shape_key_safety and
                "BF_Decimate_Protect" in mesh_obj.vertex_groups):
            mod.vertex_group = "BF_Decimate_Protect"
            mod.invert_vertex_group = True

        self.report({'INFO'}, f"Preview modifier added as '{mod_name}' (temporary)")
        return {'FINISHED'}


class BF_OT_VRC_Decimate(Operator):
    """Apply decimation with optional shape key safety checks."""
    bl_idname = "boneforge.vrc_decimate"
    bl_label = "Decimate Mesh"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        mesh_obj = context.object
        settings = mesh_obj.boneforge_vrc_decimation

        # M-09: Guard against meshes with no polygons
        if len(mesh_obj.data.polygons) == 0:
            self.report({'WARNING'}, f"Mesh '{mesh_obj.name}' has no polygons, skipping")
            return {'CANCELLED'}

        # Clean up preview modifier if present
        if "BF_Decimate_Preview" in mesh_obj.modifiers:
            mesh_obj.modifiers.remove(mesh_obj.modifiers["BF_Decimate_Preview"])

        # Snapshot shape keys before decimation
        shape_key_snapshot = _snapshot_shape_keys(mesh_obj) if settings.shape_key_safety else {}

        # Protect shape key vertices if enabled
        if settings.shape_key_safety:
            protected_verts = _get_shape_key_vertices(mesh_obj)
            if protected_verts:
                _create_protection_vertex_group(mesh_obj, protected_verts)

        # Apply decimation modifier
        mod = mesh_obj.modifiers.new(name="Decimate", type='DECIMATE')

        if settings.use_mode == 'RATIO':
            mod.ratio = settings.target_ratio
        else:
            current_count = len(mesh_obj.data.polygons)
            if current_count > 0:
                mod.ratio = max(0.01, settings.target_polygon_count / current_count)

        # Apply vertex group protection
        if (settings.shape_key_safety and
                "BF_Decimate_Protect" in mesh_obj.vertex_groups):
            mod.vertex_group = "BF_Decimate_Protect"
            mod.invert_vertex_group = True

        # Apply modifier
        # S-13: Wrap apply in try/finally to ensure cleanup on failure
        try:
            bpy.context.view_layer.objects.active = mesh_obj
            bpy.ops.object.modifier_apply(modifier=mod.name)

            # Check shape key degradation
            if settings.shape_key_safety and shape_key_snapshot:
                issues = _compare_shape_keys(mesh_obj, shape_key_snapshot, settings.tolerance)

                if issues:
                    self.report({'WARNING'}, f"Shape key degradation detected: {len(issues)} issue(s)")
                    for issue in issues[:3]:
                        self.report({'WARNING'}, f"  {issue}")
                else:
                    self.report({'INFO'}, "Shape keys preserved within tolerance")
            else:
                self.report({'INFO'}, "Decimation applied")
        except RuntimeError as e:
            self.report({'WARNING'}, f"Decimation apply failed: {e}")
        finally:
            # Clean up preview modifier if it exists
            for mod_item in list(mesh_obj.modifiers):
                if mod_item.name.startswith("BF_Decimate"):
                    mesh_obj.modifiers.remove(mod_item)

        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_decimation(Panel):
    """VRChat Blendshape-Safe Decimation."""
    bl_idname = "BONEFORGE_PT_vrc_decimation"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("VRChat Decimation"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        mesh_obj = context.object

        if not mesh_obj or mesh_obj.type != 'MESH':
            layout.label(text=T("Select a mesh object"), icon='INFO')
            return

        settings = mesh_obj.boneforge_vrc_decimation

        # Display current polygon count
        poly_count = len(mesh_obj.data.polygons)
        layout.label(text=f"Current polygons: {poly_count}")

        # Target mode selection
        layout.prop(settings, "use_mode")

        if settings.use_mode == 'RATIO':
            layout.prop(settings, "target_ratio", slider=True)
            target_count = int(poly_count * settings.target_ratio)
            layout.label(text=f"Target: ~{target_count} polygons")
        else:
            layout.prop(settings, "target_polygon_count")

        layout.separator()

        # Shape key safety
        layout.prop(settings, "shape_key_safety")

        if settings.shape_key_safety:
            layout.prop(settings, "tolerance", slider=True)

            if mesh_obj.data.shape_keys is not None:
                sk_count = len(mesh_obj.data.shape_keys.key_blocks) - 1  # Exclude Basis
                layout.label(text=f"Shape keys: {sk_count}")

                layout.operator(
                    "boneforge.vrc_protect_blendshape_regions",
                    text=T("Protect Blendshape Regions"),
                    icon='PINNED'
                )

        layout.separator()

        # Preview and apply buttons
        row = layout.row(align=True)
        row.operator("boneforge.vrc_preview_decimation", text=T("Preview"), icon='HIDE_OFF')
        row.operator("boneforge.vrc_decimate", text=T("Apply"), icon='MOD_DECIM')


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_VRCDecimationSettings,
    BF_OT_VRC_ProtectBlendshapeRegions,
    BF_OT_VRC_PreviewDecimation,
    BF_OT_VRC_Decimate,
    BONEFORGE_PT_vrc_decimation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.boneforge_vrc_decimation = PointerProperty(
        type=BF_VRCDecimationSettings,
        name="BoneCraft VRChat Decimation Settings",
    )


def unregister():
    del bpy.types.Object.boneforge_vrc_decimation

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
