"""BoneCraft VRChat CATS — Mesh Tools.

Three mesh separation utilities for avatar preparation:
  - Separate by Materials: splits mesh into per-material objects.
  - Separate by Loose Parts: splits mesh into disconnected geometry islands.
  - Separate by Shape Keys: duplicates mesh once per shape key so each copy
    carries only Basis + one target key.

All three operators work on the active mesh object, or on every mesh child of
the active armature when none is explicitly selected.

Category: VRChat Cats Tools.
"""

import logging

import bpy
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline

logger = logging.getLogger(__name__)


# ── Private helpers ──────────────────────────────────────────────────────────

def _target_meshes(context):
    """Return the list of mesh objects to operate on.

    If the active object is a MESH it is returned alone; otherwise all MESH
    children of the active armature are returned.
    """
    active = context.view_layer.objects.active
    if active is not None and active.type == 'MESH':
        return [active]

    arm = active_armature(context)
    if arm is not None:
        return [c for c in arm.children if c.type == 'MESH']

    return []


def _parent_new_objects(context, before_names, armature):
    """Re-parent any objects that appeared after a separation to *armature*."""
    if armature is None:
        return
    after_names = {obj.name for obj in bpy.data.objects}
    new_names = after_names - before_names
    for name in new_names:
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.type == 'MESH' and obj.parent is None:
            obj.parent = armature


def _separate_mesh(context, mesh_obj, sep_type):
    """Enter Edit Mode on *mesh_obj*, separate by *sep_type*, exit Object Mode.

    Returns the set of object names present before separation so the caller can
    identify newly created objects.
    """
    before_names = {obj.name for obj in bpy.data.objects}

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type=sep_type)
    bpy.ops.object.mode_set(mode='OBJECT')

    return before_names


# ── Operators ────────────────────────────────────────────────────────────────

class BF_OT_CATS_SeparateByMaterials(Operator):
    """Separate mesh(es) into per-material objects"""

    bl_idname = "boneforge.cats_separate_by_materials"
    bl_label = "Separate by Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        meshes = _target_meshes(context)

        if not meshes:
            self.report({'ERROR'}, "No mesh found — select a mesh or activate an armature with mesh children")
            return {'CANCELLED'}

        arm = active_armature(context)
        op_count = 0

        for mesh_obj in meshes:
            try:
                before_names = _separate_mesh(context, mesh_obj, 'MATERIAL')
                _parent_new_objects(context, before_names, arm)
                op_count += 1
            except Exception as exc:
                logger.warning(f"[BoneCraft] Separate by material failed on '{mesh_obj.name}': {exc}")

        msg = f"Separated {op_count} mesh(es) by materials"
        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "separate_materials", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


class BF_OT_CATS_SeparateByLooseParts(Operator):
    """Separate mesh(es) into disconnected geometry islands"""

    bl_idname = "boneforge.cats_separate_by_loose"
    bl_label = "Separate by Loose Parts"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        meshes = _target_meshes(context)

        if not meshes:
            self.report({'ERROR'}, "No mesh found — select a mesh or activate an armature with mesh children")
            return {'CANCELLED'}

        arm = active_armature(context)
        op_count = 0

        for mesh_obj in meshes:
            try:
                before_names = _separate_mesh(context, mesh_obj, 'LOOSE')
                _parent_new_objects(context, before_names, arm)
                op_count += 1
            except Exception as exc:
                logger.warning(f"[BoneCraft] Separate by loose failed on '{mesh_obj.name}': {exc}")

        msg = f"Separated {op_count} mesh(es) by loose parts"
        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "separate_loose", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


class BF_OT_CATS_SeparateByShapeKeys(Operator):
    """Create one mesh copy per shape key, each carrying only Basis + that key"""

    bl_idname = "boneforge.cats_separate_by_shape_keys"
    bl_label = "Separate by Shape Keys"
    bl_options = {'REGISTER', 'UNDO'}

    def _separate_one_mesh(self, context, mesh_obj, arm):
        """Duplicate mesh_obj for each non-Basis shape key.

        Each copy keeps Basis + one target key; the original is left intact.
        Returns the count of copies created.
        """
        sk = mesh_obj.data.shape_keys
        if sk is None or len(sk.key_blocks) <= 1:
            return 0

        # Gather non-Basis keys
        target_keys = [kb.name for kb in sk.key_blocks if kb.name != "Basis"]
        created = 0

        for key_name in target_keys:
            # Duplicate object and mesh data
            new_obj = mesh_obj.copy()
            new_obj.data = mesh_obj.data.copy()
            new_obj.name = f"{mesh_obj.name}_{key_name}"
            context.collection.objects.link(new_obj)

            # Parent to armature
            if arm is not None:
                new_obj.parent = arm

            # Keep only Basis and the target key; remove all others
            new_sk = new_obj.data.shape_keys
            if new_sk is not None:
                keys_to_remove = [
                    kb for kb in new_sk.key_blocks
                    if kb.name not in ("Basis", key_name)
                ]
                for kb in keys_to_remove:
                    new_obj.shape_key_remove(kb)

            created += 1

        return created

    def execute(self, context):
        scene = context.scene
        meshes = _target_meshes(context)

        if not meshes:
            self.report({'ERROR'}, "No mesh found — select a mesh or activate an armature with mesh children")
            return {'CANCELLED'}

        arm = active_armature(context)
        total_created = 0

        for mesh_obj in meshes:
            try:
                total_created += self._separate_one_mesh(context, mesh_obj, arm)
            except Exception as exc:
                logger.warning(f"[BoneCraft] Separate by shape keys failed on '{mesh_obj.name}': {exc}")

        if total_created == 0:
            self.report({'WARNING'}, "No shape keys found to separate — meshes need non-Basis shape keys")
            return {'CANCELLED'}

        msg = f"Created {total_created} mesh copy/copies from shape keys"
        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "separate_shape_keys", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────────────────

class CATS_PT_mesh_tools_standalone(Panel):
    """Mesh Tools panel in the CATS sidebar tab."""

    bl_label = " "
    bl_idname = "CATS_PT_mesh_tools_standalone"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Mesh Tools"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_mesh_tools in cats_panel.py

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "boneforge.cats_separate_by_materials",
            text=T("Separate by Materials"),
            icon='SEPARATE_BYMATERIAL',
        )
        layout.operator(
            "boneforge.cats_separate_by_loose",
            text=T("Separate by Loose Parts"),
            icon='SEPARATE_LOOSE',
        )
        layout.operator(
            "boneforge.cats_separate_by_shape_keys",
            text=T("Separate by Shape Keys"),
            icon='SHAPEKEY_DATA',
        )

        layout.separator()
        box = layout.box()
        box.label(
            text=T("Operates on active mesh or all armature children"),
            icon='INFO',
        )


# ── Registration ─────────────────────────────────────────────────────────────

_classes = (
    BF_OT_CATS_SeparateByMaterials,
    BF_OT_CATS_SeparateByLooseParts,
    BF_OT_CATS_SeparateByShapeKeys,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
