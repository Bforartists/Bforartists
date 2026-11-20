# --- ANIMATION LAYER MANAGEMENT OPERATORS ---
"""Operators for animation layer CRUD: add, remove, reorder, duplicate,
rename, solo, mute, lock, and layer initialization.
"""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty

from ..core.logging import get_logger
from ..core.p11_properties import get_p11
from ..core import p11_layer_engine as engine

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Poll helpers
# ---------------------------------------------------------------------------

def _p11_poll(context: bpy.types.Context) -> bool:
    return get_p11(context) is not None


def _has_layers(context: bpy.types.Context) -> bool:
    p11 = get_p11(context)
    return p11 is not None and len(p11.layers) > 0


def _active_layer_valid(context: bpy.types.Context) -> bool:
    p11 = get_p11(context)
    if p11 is None:
        return False
    return 0 <= p11.active_layer_index < len(p11.layers)


# ---------------------------------------------------------------------------
# Initialize Layer Stack
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_init_layers(bpy.types.Operator):
    """Initialize the animation layer stack with a base layer"""

    bl_idname = "animassist.p11_init_layers"
    bl_label = "Initialize Layers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _p11_poll(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        if p11 is None:
            return {'CANCELLED'}

        engine.ensure_base_layer(p11)

        # Assign the object's current action to the base layer.
        obj = context.active_object
        if obj is not None and obj.animation_data and obj.animation_data.action:
            p11.layers[0].action_name = obj.animation_data.action.name

        self.report({'INFO'}, "Layer stack initialized")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Add Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_add_layer(bpy.types.Operator):
    """Add a new animation layer to the stack"""

    bl_idname = "animassist.p11_add_layer"
    bl_label = "Add Layer"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="Name for the new layer",
        default="New Layer",
    )

    blend_mode: EnumProperty(  # type: ignore[valid-type]
        name="Blend Mode",
        description="How this layer combines with layers below",
        items=[
            ("OVERRIDE", "Override", "Replace base values"),
            ("ADDITIVE", "Additive", "Add on top of base"),
            ("MULTIPLY", "Multiply", "Scale base values"),
            ("COMBINE", "Combine", "NLA-style combine"),
        ],
        default="OVERRIDE",
    )

    weight: FloatProperty(  # type: ignore[valid-type]
        name="Weight",
        description="Initial layer weight",
        default=1.0, min=0.0, max=1.0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _p11_poll(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        if p11 is None:
            return {'CANCELLED'}

        idx = engine.add_layer(
            p11,
            name=self.name,
            blend_mode=self.blend_mode,
            weight=self.weight,
        )

        # Create backing Action for the new layer.
        engine.get_layer_action(p11.layers[idx], create=True)

        self.report({'INFO'}, f"Added layer '{self.name}' at position {idx}")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Remove Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_remove_layer(bpy.types.Operator):
    """Remove the active animation layer"""

    bl_idname = "animassist.p11_remove_layer"
    bl_label = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p11 = get_p11(context)
        if p11 is None or len(p11.layers) <= 1:
            return False
        idx = p11.active_layer_index
        if idx < 0 or idx >= len(p11.layers):
            return False
        layer = p11.layers[idx]
        return not layer.is_base_layer and not layer.protected

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        if p11 is None:
            return {'CANCELLED'}

        idx = p11.active_layer_index
        name = p11.layers[idx].name

        # Optionally remove the backing Action.
        action = engine.get_layer_action(p11.layers[idx])
        if action is not None and action.users <= 1:
            bpy.data.actions.remove(action)

        if engine.remove_layer(p11, idx):
            self.report({'INFO'}, f"Removed layer '{name}'")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"Cannot remove layer '{name}'")
            return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Move Layer Up / Down
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_move_layer_up(bpy.types.Operator):
    """Move the active layer up in the stack (higher priority)"""

    bl_idname = "animassist.p11_move_layer_up"
    bl_label = "Move Layer Up"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p11 = get_p11(context)
        if p11 is None:
            return False
        idx = p11.active_layer_index
        if not (0 <= idx < len(p11.layers)):
            return False
        return idx < len(p11.layers) - 1 and not p11.layers[idx].is_base_layer

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        idx = p11.active_layer_index
        if engine.move_layer(p11, idx, idx + 1):
            return {'FINISHED'}
        return {'CANCELLED'}


class ANIMASSIST_OT_p11_move_layer_down(bpy.types.Operator):
    """Move the active layer down in the stack (lower priority)"""

    bl_idname = "animassist.p11_move_layer_down"
    bl_label = "Move Layer Down"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p11 = get_p11(context)
        if p11 is None:
            return False
        idx = p11.active_layer_index
        # Poll runs on every redraw: never index an empty or shorter list.
        if not (0 <= idx < len(p11.layers)):
            return False
        # Can't move below base layer (index 0).
        min_idx = 1 if p11.layers[0].is_base_layer else 0
        return idx > min_idx and not p11.layers[idx].is_base_layer

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        idx = p11.active_layer_index
        if engine.move_layer(p11, idx, idx - 1):
            return {'FINISHED'}
        return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Duplicate Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_duplicate_layer(bpy.types.Operator):
    """Duplicate the active animation layer"""

    bl_idname = "animassist.p11_duplicate_layer"
    bl_label = "Duplicate Layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context) and not get_p11(context).layers[
            get_p11(context).active_layer_index
        ].is_base_layer

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        idx = p11.active_layer_index
        new_idx = engine.duplicate_layer(p11, idx)
        if new_idx >= 0:
            self.report({'INFO'}, f"Duplicated layer to position {new_idx}")
            return {'FINISHED'}
        return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Toggle Solo / Mute / Lock
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_toggle_solo(bpy.types.Operator):
    """Toggle solo on the active layer"""

    bl_idname = "animassist.p11_toggle_solo"
    bl_label = "Toggle Solo"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]
        layer.solo = not layer.solo
        p11.eval_generation += 1
        state = "ON" if layer.solo else "OFF"
        self.report({'INFO'}, f"Solo {state}: {layer.name}")
        return {'FINISHED'}


class ANIMASSIST_OT_p11_toggle_mute(bpy.types.Operator):
    """Toggle mute on the active layer"""

    bl_idname = "animassist.p11_toggle_mute"
    bl_label = "Toggle Mute"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]
        layer.mute = not layer.mute
        p11.eval_generation += 1
        state = "ON" if layer.mute else "OFF"
        self.report({'INFO'}, f"Mute {state}: {layer.name}")
        return {'FINISHED'}


class ANIMASSIST_OT_p11_toggle_lock(bpy.types.Operator):
    """Toggle lock on the active layer"""

    bl_idname = "animassist.p11_toggle_lock"
    bl_label = "Toggle Lock"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]
        layer.locked = not layer.locked
        state = "ON" if layer.locked else "OFF"
        self.report({'INFO'}, f"Lock {state}: {layer.name}")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Set Active Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_set_active(bpy.types.Operator):
    """Set a layer as the active editing layer"""

    bl_idname = "animassist.p11_set_active"
    bl_label = "Set Active Layer"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(  # type: ignore[valid-type]
        name="Layer Index",
        description="Index of the layer to activate",
        default=0,
        min=0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_layers(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        if 0 <= self.index < len(p11.layers):
            p11.active_layer_index = self.index
            self.report({'INFO'}, f"Active layer: {p11.layers[self.index].name}")
            return {'FINISHED'}
        return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Rename Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_rename_layer(bpy.types.Operator):
    """Rename the active animation layer"""

    bl_idname = "animassist.p11_rename_layer"
    bl_label = "Rename Layer"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: StringProperty(  # type: ignore[valid-type]
        name="New Name",
        description="New name for the active layer",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def invoke(self, context: bpy.types.Context, event) -> set[str]:
        p11 = get_p11(context)
        self.new_name = p11.layers[p11.active_layer_index].name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]
        old_name = layer.name
        layer.name = self.new_name
        self.report({'INFO'}, f"Renamed '{old_name}' to '{self.new_name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Evaluate Layer Stack (apply blended result to bones)
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_evaluate_stack(bpy.types.Operator):
    """Evaluate the layer stack and apply results to the armature"""

    bl_idname = "animassist.p11_evaluate_stack"
    bl_label = "Evaluate Layer Stack"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p11 = get_p11(context)
        if p11 is None or not p11.layers_enabled:
            return False
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE" and context.mode == "POSE"

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        obj = context.active_object
        frame = context.scene.frame_current

        bones_updated = 0
        for bone in obj.pose.bones:
            result = engine.evaluate_layer_stack(p11, bone.name, frame, obj)
            if result.layers_applied:
                engine.apply_eval_result(bone, result)
                bones_updated += 1

        self.report({'INFO'}, f"Evaluated {bones_updated} bones across {len(p11.layers)} layers")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Select Layer by Index (for UIList clicks)
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_select_layer(bpy.types.Operator):
    """Select a layer by index in the stack"""

    bl_idname = "animassist.p11_select_layer"
    bl_label = "Select Layer"

    index: IntProperty(default=0, min=0)  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_layers(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        if 0 <= self.index < len(p11.layers):
            p11.active_layer_index = self.index
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Class collection
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    ANIMASSIST_OT_p11_init_layers,
    ANIMASSIST_OT_p11_add_layer,
    ANIMASSIST_OT_p11_remove_layer,
    ANIMASSIST_OT_p11_move_layer_up,
    ANIMASSIST_OT_p11_move_layer_down,
    ANIMASSIST_OT_p11_duplicate_layer,
    ANIMASSIST_OT_p11_toggle_solo,
    ANIMASSIST_OT_p11_toggle_mute,
    ANIMASSIST_OT_p11_toggle_lock,
    ANIMASSIST_OT_p11_set_active,
    ANIMASSIST_OT_p11_rename_layer,
    ANIMASSIST_OT_p11_evaluate_stack,
    ANIMASSIST_OT_p11_select_layer,
)
