"""BoneCraft VRChat CATS — Shape Key Tools.

Pose to Shape Key: captures the current evaluated mesh state (including any
armature pose influence) as a new shape key.

Shape Key to Basis: rebases all shape keys onto a chosen key, making that
key the new Basis and recomputing all other keys' deltas accordingly.

Category: VRChat Cats Tools.
"""

import logging

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel

from boneforge.core import active_armature  # noqa: F401 — kept for symmetry with other modules
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline

logger = logging.getLogger(__name__)


# ── Pose to Shape Key ─────────────────────────────────────────────────────────

class BF_OT_CATS_PoseToShape(Operator):
    """Bake the current pose (including armature deform) into a new shape key
    on the active mesh object"""

    bl_idname = "boneforge.cats_pose_to_shape"
    bl_label = "Pose to Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    shape_name: StringProperty(
        name="Shape Key Name",
        description="Name for the new shape key",
        default="PoseShape",
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        # Save mode — we need Object Mode for shape_key_add to evaluate correctly
        saved_mode = obj.mode
        if saved_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        try:
            # Ensure the object has at least a Basis key so shape_key_add
            # with from_mix=True works reliably on key-less meshes.
            if obj.data.shape_keys is None:
                obj.shape_key_add(name="Basis", from_mix=False)

            new_key = obj.shape_key_add(name=self.shape_name, from_mix=True)

            # Move new key to the end of the stack (shape_key_add already does
            # this in most Blender versions, but make certain).
            key_blocks = obj.data.shape_keys.key_blocks
            if key_blocks[-1].name != new_key.name:
                # Move to bottom: set active index then move
                obj.active_shape_key_index = key_blocks.find(new_key.name)
                while obj.active_shape_key_index < len(key_blocks) - 1:
                    bpy.ops.object.shape_key_move(type='DOWN')

            new_key.value = 1.0

        except Exception as exc:
            logger.exception("[BoneCraft PoseToShape] Error: %s", exc)
            self.report({'ERROR'}, f"Failed to create shape key: {exc}")
            return {'CANCELLED'}

        finally:
            if saved_mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode=saved_mode)
                except RuntimeError:
                    pass

        name = new_key.name
        scene = context.scene
        msg = f"Created shape key '{name}' from pose"
        pipeline.append_ledger(scene, "pose_to_shape", pipeline.OUTCOME_CHANGED, msg)
        pipeline.set_phase_complete(scene, "pose_to_shape", pipeline.OUTCOME_CHANGED)

        self.report({'INFO'}, f"Shape key '{name}' created from pose")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "shape_name")


# ── Shape Key to Basis ────────────────────────────────────────────────────────

class BF_OT_CATS_ShapeKeyToBasis(Operator):
    """Rebase all shape keys so the active shape key becomes the new Basis.
    All other keys' deltas are recomputed relative to the new Basis position."""

    bl_idname = "boneforge.cats_shape_key_to_basis"
    bl_label = "Shape Key to Basis"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        if obj.data.shape_keys is None:
            self.report({'ERROR'}, "Object has no shape keys")
            return {'CANCELLED'}

        active_key = obj.active_shape_key
        if active_key is None:
            self.report({'ERROR'}, "No active shape key")
            return {'CANCELLED'}

        if active_key.name == "Basis":
            self.report({'ERROR'}, "Select a non-Basis shape key")
            return {'CANCELLED'}

        key_blocks = obj.data.shape_keys.key_blocks
        n_verts = len(obj.data.vertices)
        n_floats = n_verts * 3

        # ── Read coordinate arrays for Basis and target ────────────────────
        basis_cos = [0.0] * n_floats
        target_cos = [0.0] * n_floats

        key_blocks["Basis"].data.foreach_get("co", basis_cos)
        active_key.data.foreach_get("co", target_cos)

        target_name = active_key.name

        # ── Rebase every key except Basis and the target ───────────────────
        # new_delta = old_absolute - old_basis + new_basis
        #           = old_absolute - old_basis + target_absolute
        # i.e. new_absolute = old_absolute - basis_cos + target_cos
        for kb in key_blocks:
            if kb.name == "Basis" or kb.name == target_name:
                continue
            key_cos = [0.0] * n_floats
            kb.data.foreach_get("co", key_cos)

            for i in range(n_floats):
                key_cos[i] = key_cos[i] - basis_cos[i] + target_cos[i]

            kb.data.foreach_set("co", key_cos)

        # ── Set Basis vertices to target positions ─────────────────────────
        key_blocks["Basis"].data.foreach_set("co", target_cos)

        # ── Remove the target key (it is now identical to the new Basis) ───
        target_idx = key_blocks.find(target_name)
        obj.active_shape_key_index = target_idx
        bpy.ops.object.shape_key_remove(all=False)

        # Notify mesh of the change
        obj.data.update()

        scene = context.scene
        msg = f"Basis replaced with '{target_name}'"
        pipeline.append_ledger(scene, "shape_key_to_basis", pipeline.OUTCOME_CHANGED, msg)
        pipeline.set_phase_complete(scene, "shape_key_to_basis", pipeline.OUTCOME_CHANGED)

        self.report({'INFO'}, f"'{target_name}' set as new Basis")
        return {'FINISHED'}


# ── Panel ─────────────────────────────────────────────────────────────────────

class CATS_PT_shape_key_tools(Panel):
    """CATS Shape Key Tools panel in the 3D Viewport sidebar."""

    bl_label = " "
    bl_idname = "CATS_PT_shape_key_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Shape Key Tools"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_pose_shape in cats_panel.py

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # ── Pose to Shape ──────────────────────────────────────────────────
        box = layout.box()
        box.label(text=T("Pose to Shape Key"))

        if obj is not None and obj.type == 'MESH':
            box.operator(
                "boneforge.cats_pose_to_shape",
                text=T("Capture Pose as Shape Key"),
                icon='SHAPEKEY_DATA',
            )
        else:
            box.label(text=T("Select a mesh object"), icon='INFO')

        layout.separator()

        # ── Shape Key to Basis ─────────────────────────────────────────────
        box2 = layout.box()
        box2.label(text=T("Shape Key to Basis"))

        if obj is not None and obj.type == 'MESH' and obj.data.shape_keys is not None:
            active_key = obj.active_shape_key
            if active_key and active_key.name != "Basis":
                box2.label(text=f"{T('Active')}: {active_key.name}")
                box2.operator(
                    "boneforge.cats_shape_key_to_basis",
                    text=T("Set as New Basis"),
                    icon='SHAPEKEY_DATA',
                )
            else:
                box2.label(text=T("Select a non-Basis shape key"), icon='INFO')
        else:
            box2.label(text=T("Select a mesh with shape keys"), icon='INFO')


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    BF_OT_CATS_PoseToShape,
    BF_OT_CATS_ShapeKeyToBasis,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
