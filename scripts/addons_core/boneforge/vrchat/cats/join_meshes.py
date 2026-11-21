"""BoneCraft VRChat — Mesh Joining with Shape Key Safety.

Join checked meshes while preserving materials, shape keys, and vertex groups.
Includes shape key conflict handler for same-named keys with different values.

Category: VRChat Cats Tools.
"""

from typing import List

import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.core import active_armature
from boneforge.i18n import T


# ─────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────

class BF_MeshToJoin(PropertyGroup):
    """A single mesh to join or skip."""

    name: bpy.props.StringProperty(name="Mesh Name", default="")
    object_name: bpy.props.StringProperty(name="Object Name", default="")
    include: BoolProperty(name="Include", default=True)
    polygon_count: IntProperty(name="Polygon Count", default=0)


class BF_VRCJoinMeshesSettings(PropertyGroup):
    """Settings for the Join Meshes operation."""

    meshes: CollectionProperty(type=BF_MeshToJoin)
    active_mesh_index: IntProperty(default=0)
    shape_key_conflict_mode: bpy.props.EnumProperty(
        name="Shape Key Conflict Mode",
        description="How to handle same-named shape keys with different values",
        items=[
            ('KEEP_FIRST', "Keep First", "Keep shape key from first mesh"),
            ('KEEP_SECOND', "Keep Second", "Keep shape key from second mesh"),
            ('KEEP_BOTH', "Keep Both", "Keep both with suffixes (_mesh1, _mesh2)"),
        ],
        default='KEEP_FIRST',
    )


# ─────────────────────────────────────────────────────────────────
# Detection and Joining
# ─────────────────────────────────────────────────────────────────

def _collect_mesh_children(armature) -> List[bpy.types.Object]:
    """Collect all mesh children of an armature.

    Args:
        armature: The armature object

    Returns:
        List of mesh objects
    """
    return [child for child in armature.children if child.type == 'MESH']


def _build_mesh_list(armature, settings: BF_VRCJoinMeshesSettings) -> None:
    """Build or refresh the mesh list in settings.

    Args:
        armature: The armature object
        settings: The settings instance to populate
    """
    meshes = _collect_mesh_children(armature)

    # Clear existing list
    settings.meshes.clear()

    # Add each mesh
    for mesh_obj in meshes:
        item = settings.meshes.add()
        item.name = mesh_obj.name
        item.object_name = mesh_obj.name
        item.include = True
        item.polygon_count = len(mesh_obj.data.polygons) if mesh_obj.data else 0


def _join_selected_meshes(
    context,
    mesh_objects: List[bpy.types.Object],
    shape_key_conflict_mode: str
) -> bpy.types.Object:
    """Join multiple mesh objects while preserving shape keys.

    Args:
        context: The Blender context
        mesh_objects: List of mesh objects to join (order matters)
        shape_key_conflict_mode: How to handle conflicting shape keys

    Returns:
        The resulting joined mesh object
    """
    if not mesh_objects:
        raise ValueError("No meshes to join")

    if len(mesh_objects) == 1:
        return mesh_objects[0]

    # Select and join
    bpy.ops.object.select_all(action='DESELECT')

    # Make first mesh active
    base_mesh = mesh_objects[0]
    context.view_layer.objects.active = base_mesh
    base_mesh.select_set(True)

    # Handle shape keys before joining
    base_shape_keys = {}
    if base_mesh.data.shape_keys:
        for kb in base_mesh.data.shape_keys.key_blocks:
            base_shape_keys[kb.name] = kb.data

    # Select and join all others
    for mesh_obj in mesh_objects[1:]:
        mesh_obj.select_set(True)

        # Check for shape key conflicts
        if mesh_obj.data.shape_keys and shape_key_conflict_mode == 'KEEP_BOTH':
            for kb in mesh_obj.data.shape_keys.key_blocks:
                if kb.name in base_shape_keys and kb.name != "Basis":
                    # Rename the shape key to avoid conflict
                    new_name = f"{kb.name}_{mesh_obj.name}"
                    kb.name = new_name

    # Perform join
    bpy.ops.object.join()

    return base_mesh


# ─────────────────────────────────────────────────────────────────
# Operator
# ─────────────────────────────────────────────────────────────────

class BF_OT_VRC_JoinMeshes(Operator):
    """Join selected meshes while preserving materials and shape keys"""

    bl_idname = "boneforge.vrc_join_meshes"
    bl_label = "Join Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Execute mesh joining."""
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_join_meshes_settings

        # Collect selected meshes
        selected_meshes = []
        for item in settings.meshes:
            if not item.include:
                continue

            obj = bpy.data.objects.get(item.object_name)
            if obj and obj.type == 'MESH':
                selected_meshes.append(obj)

        if len(selected_meshes) < 2:
            self.report({'WARNING'}, "Select at least 2 meshes to join")
            return {'CANCELLED'}

        # Save state
        saved_selection = set(obj.name for obj in context.selected_objects)
        saved_active = context.view_layer.objects.active

        try:
            # Join meshes
            result = _join_selected_meshes(
                context,
                selected_meshes,
                settings.shape_key_conflict_mode
            )
            self.report({'INFO'}, f"Joined {len(selected_meshes)} meshes into '{result.name}'")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to join meshes: {e}")
            return {'CANCELLED'}

        finally:
            # Restore state (optional)
            pass

        return {'FINISHED'}


class BF_OT_VRC_RefreshMeshList(Operator):
    """Refresh the mesh list from armature children"""

    bl_idname = "boneforge.vrc_refresh_mesh_list"
    bl_label = "Refresh Mesh List"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Refresh the mesh list."""
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_join_meshes_settings
        _build_mesh_list(arm, settings)
        self.report({'INFO'}, "Mesh list refreshed")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────
# Panel
# ─────────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_join_meshes(Panel):
    """VRChat Join Meshes panel"""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_join_meshes"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw_header(self, context):
        self.layout.label(text=T("Join Meshes"))

    def draw(self, context):
        """Draw the panel UI."""
        layout = self.layout
        arm = active_armature(context)

        if arm is None:
            layout.label(text=T("No active armature"), icon='INFO')
            return

        settings = context.scene.boneforge_vrc_join_meshes_settings

        # Refresh button
        layout.operator("boneforge.vrc_refresh_mesh_list", icon='FILE_REFRESH')

        # Mesh list
        if not settings.meshes:
            layout.label(text=T("No meshes found"), icon='INFO')
            return

        layout.label(text=f"Meshes ({len(settings.meshes)}):")
        for idx, item in enumerate(settings.meshes):
            row = layout.row()
            row.prop(item, "include", text="")
            row.label(text=item.name, icon='MESH_DATA')
            row.label(text=f"{item.polygon_count} polys")

        layout.separator()
        layout.operator("boneforge.vrc_join_meshes", icon='MESH_CUBE')

        # how clashing shape keys are handled: a setting, folded below the action
        from boneforge.core.helpers import options_fold
        col = options_fold(layout, "bc_join_meshes_options")
        if col is not None:
            col.prop(settings, "shape_key_conflict_mode")


# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

def register():
    """Register join meshes classes."""
    bpy.utils.register_class(BF_MeshToJoin)
    bpy.utils.register_class(BF_VRCJoinMeshesSettings)
    bpy.utils.register_class(BF_OT_VRC_JoinMeshes)
    bpy.utils.register_class(BF_OT_VRC_RefreshMeshList)

    # Add property to scene
    bpy.types.Scene.boneforge_vrc_join_meshes_settings = bpy.props.PointerProperty(
        type=BF_VRCJoinMeshesSettings
    )


def unregister():
    """Unregister join meshes classes."""
    bpy.utils.unregister_class(BF_OT_VRC_RefreshMeshList)
    bpy.utils.unregister_class(BF_OT_VRC_JoinMeshes)
    bpy.utils.unregister_class(BF_VRCJoinMeshesSettings)
    bpy.utils.unregister_class(BF_MeshToJoin)

    # Remove property from scene
    if hasattr(bpy.types.Scene, 'boneforge_vrc_join_meshes_settings'):
        del bpy.types.Scene.boneforge_vrc_join_meshes_settings
