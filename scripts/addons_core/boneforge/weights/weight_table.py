"""BoneCraft Phase 2B — Per-Vertex Weight Table.

Tabular view and editor for vertex group weights on selected vertices.
Supports single-vertex detailed editing and multi-vertex batch operations.
Category: Weight Tools.
"""

import logging

import bpy
import numpy as np
from bpy.props import StringProperty, FloatProperty, EnumProperty, IntProperty
from boneforge.i18n import T

logger = logging.getLogger(__name__)

# Maximum vertices scanned for weight data in multi-vertex display
_MAX_MULTI_DISPLAY = 100


class BONEFORGE_PT_p2b_weight_table(bpy.types.Panel):
    """Per-vertex weight table - view and edit weights for selected vertices."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_weight_table"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Weight Table"))

    @classmethod
    def poll(cls, context):
        if context.mode != "PAINT_WEIGHT":
            return False

        obj = context.active_object
        if not obj or obj.type != "MESH":
            return False

        # Check if vertex selection is active (paint mask)
        mesh = obj.data
        if not mesh.use_paint_mask_vertex:
            return False

        # Check if at least one vertex is selected
        try:
            for vert in mesh.vertices:
                if vert.select:
                    return True
        except (AttributeError, ReferenceError) as exc:
            logger.debug("Weight table poll vertex check failed: %s", exc)

        return False

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mesh = obj.data
        scene = context.scene

        # Get selected vertices via a single C-level bulk read (avoids O(V) Python iteration)
        sel = np.empty(len(mesh.vertices), dtype=bool)
        mesh.vertices.foreach_get("select", sel)
        selected_verts = [mesh.vertices[int(i)] for i in np.where(sel)[0]]

        if not selected_verts:
            layout.label(text=T("No vertices selected"))
            return

        if len(selected_verts) == 1:
            self._draw_single_vertex(layout, obj, mesh, selected_verts[0], scene)
        else:
            self._draw_multi_vertex(layout, obj, mesh, selected_verts, scene)

    def _draw_single_vertex(self, layout, obj, mesh, vert, scene):
        """Draw weight table for single vertex."""
        vert_idx = vert.index

        layout.label(text=f"Vertex {vert_idx}")
        layout.separator()

        # v3.1.6 (M-1): assigned-only weight read.
        groups = obj.vertex_groups
        influences = {
            groups[vge.group].name: vge.weight
            for vge in vert.groups
            if vge.weight > 0.0
        }
        total_weight = sum(influences.values())

        # Draw influence rows
        box = layout.box()
        for bone_name, weight in sorted(influences.items()):
            row = box.row(align=True)
            row.label(text=bone_name, icon="BONE_DATA")

            # Weight display with proportion bar
            if total_weight > 0.0:
                proportion = weight / total_weight
                bar = '[' + '#' * int(proportion * 10) + '-' * (10 - int(proportion * 10)) + ']'
                row.label(text=f"{weight:.3f} ({proportion*100:.0f}%) {bar}")
            else:
                row.label(text=f"{weight:.3f}")

            # Set Weight: starts from the current weight; tune it after the click in Adjust Last Operation
            op = row.operator("boneforge.set_vertex_weight", text="", icon="HAND")
            op.vertex_index = vert_idx
            op.bone_name = bone_name
            op.weight_value = weight

            # Zero button
            op = row.operator("boneforge.zero_vertex_weight", text="", icon="X")
            op.vertex_index = vert_idx
            op.bone_name = bone_name

        # Total weight row
        layout.separator()
        row = layout.row(align=True)
        row.label(text=T("Total:"))
        row.label(text=f"{total_weight:.3f}")

        # Normalize button if needed
        if abs(total_weight - 1.0) > 0.001:
            row.operator("boneforge.normalize_vertex_weights", text=T("Normalize"))

        # Add influence row
        layout.separator()
        col = layout.column(align=True)
        col.label(text=T("Add Influence:"))
        row = col.row(align=True)

        # Bone selector dropdown
        row.prop(scene, "boneforge_add_influence_bone", text="")
        op = row.operator("boneforge.add_vertex_influence", text=T("Add"))
        op.vertex_index = vert_idx
        op.bone_name = scene.boneforge_add_influence_bone or ""

    def _draw_multi_vertex(self, layout, obj, mesh, verts, scene):
        """Draw weight table for multiple vertices."""
        total_selected = len(verts)
        display_verts = verts[:_MAX_MULTI_DISPLAY]
        layout.label(text=f"Multiple vertices ({total_selected})")
        if total_selected > _MAX_MULTI_DISPLAY:
            layout.label(text=f"(showing first {_MAX_MULTI_DISPLAY} of {total_selected})")
        layout.separator()

        # v3.1.6 (M-1): assigned-only weight read; one pass per displayed vert.
        all_influences = {}
        groups = obj.vertex_groups
        for vert in display_verts:
            for vge in vert.groups:
                if vge.weight <= 0.0:
                    continue
                name = groups[vge.group].name
                all_influences.setdefault(name, []).append(vge.weight)

        # Draw influence rows with mean values and Set All button
        box = layout.box()
        for bone_name in sorted(all_influences.keys()):
            weights = all_influences[bone_name]
            mean_weight = sum(weights) / len(weights)
            total_weight = sum(weights)

            row = box.row(align=True)
            row.label(text=bone_name, icon="BONE_DATA")
            row.label(text=f"{mean_weight:.3f} (avg)")

            # Set All button for this bone
            op = row.operator("boneforge.set_vertex_weight", text=T("Set All"), icon="HAND")
            op.bone_name = bone_name
            op.weight_value = mean_weight
            op.vertex_index = -1  # Signal to apply to all selected

        # Normalize All button
        layout.separator()
        layout.operator("boneforge.normalize_vertex_weights", text=T("Normalize All Vertices"), icon="ARROW_LEFTRIGHT")

        # Summary
        layout.separator()
        layout.label(text=T("Tip: Select single vertex for detailed editing"))


class BF_OT_SetVertexWeight(bpy.types.Operator):
    """Set weight for specific bone on selected vertices."""
    bl_idname = "boneforge.set_vertex_weight"
    bl_label = "Set Vertex Weight"
    bl_options = {"REGISTER", "UNDO"}

    vertex_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'})
    bone_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    weight_value: FloatProperty(
        name="Weight",
        description="Weight for this bone on the vertex; adjust it in Adjust Last Operation",
        min=0.0, max=1.0, default=0.5,
    )

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return {"CANCELLED"}

        if self.bone_name not in obj.vertex_groups:
            vg = obj.vertex_groups.new(name=self.bone_name)
        else:
            vg = obj.vertex_groups[self.bone_name]

        mesh = obj.data

        # Determine which vertices to modify
        if self.vertex_index >= 0:
            # Single vertex mode
            selected_verts = [self.vertex_index]
        else:
            # Multi-vertex mode: use all selected
            selected_verts = [v.index for v in mesh.vertices if v.select]

        if not selected_verts:
            self.report({"WARNING"}, "No vertices to modify")
            return {"CANCELLED"}

        for vert_idx in selected_verts:
            vg.add([vert_idx], self.weight_value, "REPLACE")

        self.report({"INFO"}, f"Set {self.bone_name} weight to {self.weight_value:.3f} for {len(selected_verts)} vertices")
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "weight_value", slider=True)


class BF_OT_ZeroVertexWeight(bpy.types.Operator):
    """Remove bone influence from selected vertices."""
    bl_idname = "boneforge.zero_vertex_weight"
    bl_label = "Zero Weight"
    bl_options = {"REGISTER", "UNDO"}

    vertex_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'})
    bone_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return {"CANCELLED"}

        if self.bone_name not in obj.vertex_groups:
            return {"FINISHED"}

        vg = obj.vertex_groups[self.bone_name]
        mesh = obj.data
        selected_verts = [v.index for v in mesh.vertices if v.select]

        if not selected_verts:
            selected_verts = [self.vertex_index]

        for vert_idx in selected_verts:
            vg.remove([vert_idx])  # v3.1.6 (M-1): vg.remove tolerates unassigned verts since 3.0.

        self.report({"INFO"}, f"Zeroed {self.bone_name} for {len(selected_verts)} vertices")
        return {"FINISHED"}


class BF_OT_NormalizeVertexWeights(bpy.types.Operator):
    """Normalize weights for selected vertices."""
    bl_idname = "boneforge.normalize_vertex_weights"
    bl_label = "Normalize Weights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return {"CANCELLED"}

        mesh = obj.data
        selected_verts = [vert for vert in mesh.vertices if vert.select]

        if not selected_verts:
            self.report({"WARNING"}, "No vertices selected")
            return {"CANCELLED"}

        normalized_count = 0

        for vert in selected_verts:
            # v3.1.6 (M-1): assigned-only weight read.
            weights = {vge.group: vge.weight for vge in vert.groups if vge.weight > 0.0}
            total_weight = sum(weights.values())

            if total_weight > 0.0 and abs(total_weight - 1.0) > 0.001:
                inv = 1.0 / total_weight
                for vg_idx, weight in weights.items():
                    obj.vertex_groups[vg_idx].add(
                        [vert.index], weight * inv, "REPLACE",
                    )
                normalized_count += 1

        self.report({"INFO"}, f"Normalized {normalized_count} vertices")
        return {"FINISHED"}


class BF_OT_AddVertexInfluence(bpy.types.Operator):
    """Add bone influence to selected vertices."""
    bl_idname = "boneforge.add_vertex_influence"
    bl_label = "Add Influence"
    bl_options = {"REGISTER", "UNDO"}

    vertex_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'})
    bone_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    weight_value: FloatProperty(
        name="Weight",
        description="Weight of the new bone influence; adjust it in Adjust Last Operation",
        min=0.0, max=1.0, default=0.5,
    )

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            return {"CANCELLED"}

        if not self.bone_name or self.bone_name == "":
            self.report({"ERROR"}, "No bone selected")
            return {"CANCELLED"}

        # Create vertex group if it doesn't exist
        if self.bone_name not in obj.vertex_groups:
            vg = obj.vertex_groups.new(name=self.bone_name)
        else:
            vg = obj.vertex_groups[self.bone_name]

        mesh = obj.data
        selected_verts = [v.index for v in mesh.vertices if v.select]

        if not selected_verts:
            selected_verts = [self.vertex_index]

        for vert_idx in selected_verts:
            vg.add([vert_idx], self.weight_value, "ADD")

        self.report({"INFO"}, f"Added {self.bone_name} to {len(selected_verts)} vertices")
        return {"FINISHED"}


def get_bone_names_for_enum(scene, context):
    """Generate enum items for bones from active armature."""
    items = []
    obj = context.active_object

    if not obj:
        return items

    # Find the associated armature
    armature = None

    # Check modifiers
    for mod in obj.modifiers:
        if mod.type == "ARMATURE" and mod.object:
            armature = mod.object
            break

    # Check parent
    if not armature and obj.parent and obj.parent.type == "ARMATURE":
        armature = obj.parent

    if armature and armature.type == "ARMATURE":
        for i, bone in enumerate(armature.data.bones):
            items.append((bone.name, bone.name, f"Add {bone.name} influence"))

    if not items:
        items.append(("NONE", "No bones found", "No bones in armature"))

    return items


def register():
    """Register weight table classes and properties."""
    bpy.utils.register_class(BONEFORGE_PT_p2b_weight_table)
    bpy.utils.register_class(BF_OT_SetVertexWeight)
    bpy.utils.register_class(BF_OT_ZeroVertexWeight)
    bpy.utils.register_class(BF_OT_NormalizeVertexWeights)
    bpy.utils.register_class(BF_OT_AddVertexInfluence)

    # Scene properties
    bpy.types.Scene.boneforge_weight_edit_value = FloatProperty(
        name="Weight",
        min=0.0,
        max=1.0,
        default=0.5
    )

    bpy.types.Scene.boneforge_add_influence_bone = EnumProperty(
        name="Bone",
        items=get_bone_names_for_enum
    )


def unregister():
    """Unregister weight table classes and properties."""
    bpy.utils.unregister_class(BONEFORGE_PT_p2b_weight_table)
    bpy.utils.unregister_class(BF_OT_SetVertexWeight)
    bpy.utils.unregister_class(BF_OT_ZeroVertexWeight)
    bpy.utils.unregister_class(BF_OT_NormalizeVertexWeights)
    bpy.utils.unregister_class(BF_OT_AddVertexInfluence)

    # Clean up properties
    if hasattr(bpy.types.Scene, "boneforge_weight_edit_value"):
        del bpy.types.Scene.boneforge_weight_edit_value
    if hasattr(bpy.types.Scene, "boneforge_add_influence_bone"):
        del bpy.types.Scene.boneforge_add_influence_bone
