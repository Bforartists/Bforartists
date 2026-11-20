"""Named selection sets + side-mirror for the control picker (per-character)."""
import json

import bpy

from boneforge.control_ui import layout as _layout
from boneforge.control_ui import picker as _picker

_SETS_PROP = "bf_picker_sets"          # per-armature JSON {name: [bones]}


# ── per-character selection-set store (testable) ──────────────

def get_sets(arm):
    raw = arm.get(_SETS_PROP)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def store_set(arm, name, bone_names):
    sets = get_sets(arm)
    sets[name] = list(bone_names)
    arm[_SETS_PROP] = json.dumps(sets)


def remove_set(arm, name):
    sets = get_sets(arm)
    sets.pop(name, None)
    arm[_SETS_PROP] = json.dumps(sets)


def _current_selection(context):
    return [pb.name for pb in (context.selected_pose_bones or [])]


# ── operators ─────────────────────────────────────────────────

class BF_OT_AddSelectionSet(bpy.types.Operator):
    """Store the current pose-bone selection as a named set"""
    bl_idname = "boneforge.picker_add_set"
    bl_label = "Add Selection Set"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(description='Name of the new selection set', name="Name", default="Set")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):
        arm = context.active_object
        names = _current_selection(context)
        if not names and arm.data.bones.active:
            names = [arm.data.bones.active.name]
        if not names:
            self.report({'WARNING'}, "Nothing selected")
            return {'CANCELLED'}
        store_set(arm, self.name, names)
        self.report({'INFO'}, "Stored set '%s' (%d)" % (self.name, len(names)))
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BF_OT_SelectSet(bpy.types.Operator):
    """Select the bones in a named selection set"""
    bl_idname = "boneforge.picker_select_set"
    bl_label = "Select Set"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    extend: bpy.props.BoolProperty(description='Add to the current selection instead of replacing it', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):
        arm = context.active_object
        names = get_sets(arm).get(self.name, [])
        n = _picker.select_control_bones(arm, names, self.extend, context)
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Selected set '%s' (%d)" % (self.name, n))
        return {'FINISHED'}


class BF_OT_MirrorSelection(bpy.types.Operator):
    """Select the side-mirror of the current selection (-L <-> -R)"""
    bl_idname = "boneforge.picker_mirror_selection"
    bl_label = "Mirror Selection"
    bl_options = {'REGISTER', 'UNDO'}

    extend: bpy.props.BoolProperty(description='Add to the current selection instead of replacing it', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):
        arm = context.active_object
        current = _current_selection(context)
        if not current and arm.data.bones.active:
            current = [arm.data.bones.active.name]
        mirrored = _layout.mirror_selection(current)
        n = _picker.select_control_bones(arm, mirrored, self.extend, context)
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Mirrored selection (%d)" % n)
        return {'FINISHED'}


classes = (
    BF_OT_AddSelectionSet,
    BF_OT_SelectSet,
    BF_OT_MirrorSelection,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
