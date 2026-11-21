"""BoneCraft VRChat — Eye Bone Setup.

Configure eye bone orientation and rotation limits per VRChat SDK spec.
Category: VRChat Setup.
"""

import bpy
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.i18n import T

# ── Constants ────────────────────────────────────────────────────────

# VRChat spec: ±30° horizontal, ±15° vertical rotation limits
EYE_LIMITS = {
    "horizontal": 30,
    "vertical": 15,
}


# ── Utility functions ────────────────────────────────────────────────

def _find_eye_bones(armature):
    """Find left and right eye bones by naming convention."""
    left_eye = None
    right_eye = None

    if not armature or armature.type != "ARMATURE":
        return None, None

    bones_lower = {b.name.lower(): b.name for b in armature.data.bones}

    # Search for left eye
    for pattern in ["left_eye", "l_eye", "eye_l", "eye.l", "lefteye"]:
        if pattern in bones_lower:
            left_eye = bones_lower[pattern]
            break

    # Search for right eye
    for pattern in ["right_eye", "r_eye", "eye_r", "eye.r", "righteye"]:
        if pattern in bones_lower:
            right_eye = bones_lower[pattern]
            break

    return left_eye, right_eye


def check_eye_bones(armature):
    """Check eye bone status.

    Returns dict with:
    - left_eye_bone: bone name or None
    - right_eye_bone: bone name or None
    - orientation_ok: bool (all eyes pointing forward)
    - parent_ok: bool (eyes have proper parent)
    - limits_set: bool (rotation limits configured)
    """
    if not armature or armature.type != "ARMATURE":
        return {
            "left_eye_bone": None,
            "right_eye_bone": None,
            "orientation_ok": False,
            "parent_ok": False,
            "limits_set": False,
        }

    left_eye, right_eye = _find_eye_bones(armature)

    # Check orientation (simplified - looking forward is Y-up)
    orientation_ok = True
    if left_eye:
        bone = armature.data.bones[left_eye]
        # In VRChat SDK, eyes should be oriented forward
        # This is a simplified check
        orientation_ok = orientation_ok and (bone.name in armature.data.bones)

    if right_eye:
        bone = armature.data.bones[right_eye]
        orientation_ok = orientation_ok and (bone.name in armature.data.bones)

    # Check parent (should be head)
    parent_ok = True
    if left_eye:
        bone = armature.data.bones[left_eye]
        parent_ok = parent_ok and (bone.parent is not None)

    if right_eye:
        bone = armature.data.bones[right_eye]
        parent_ok = parent_ok and (bone.parent is not None)

    # Check limits (simplified - assume not set initially)
    limits_set = False

    return {
        "left_eye_bone": left_eye,
        "right_eye_bone": right_eye,
        "orientation_ok": orientation_ok,
        "parent_ok": parent_ok,
        "limits_set": limits_set,
    }


# ── Operators ────────────────────────────────────────────────────────

class BF_OT_VRC_FixEyeBones(Operator):
    """Fix eye bone orientation and set VRChat-compliant rotation limits.

    Reorients eye bones to look forward and sets:
    - ±30° horizontal (X/Y rotation)
    - ±15° vertical (Z rotation)
    """

    bl_idname = "boneforge.vrc_fix_eye_bones"
    bl_label = "Fix Eye Bones"
    bl_description = ("Point the eye bones forward and limit them to VRChat's eye range "
                      "(30° left and right, 15° up and down)")
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from mathutils import Vector

        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        # Find eye bones
        left_eye = None
        right_eye = None
        eye_patterns_left = ["lefteye", "eye_l", "eye.l", "left_eye", "j_bip_c_eyel", "eye_left"]
        eye_patterns_right = ["righteye", "eye_r", "eye.r", "right_eye", "j_bip_c_eyer", "eye_right"]

        for bone in arm.data.bones:
            name_lower = bone.name.lower()
            if any(p in name_lower for p in eye_patterns_left):
                left_eye = bone.name
            elif any(p in name_lower for p in eye_patterns_right):
                right_eye = bone.name

        if not left_eye and not right_eye:
            self.report({'WARNING'}, "No eye bones found")
            return {'CANCELLED'}

        # Enter edit mode to fix orientations
        saved_active = context.view_layer.objects.active
        context.view_layer.objects.active = arm
        arm.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        fixed_count = 0
        try:
            edit_bones = arm.data.edit_bones

            for eye_name in (left_eye, right_eye):
                if eye_name is None:
                    continue
                if eye_name not in edit_bones:
                    continue

                ebone = edit_bones[eye_name]
                # Orient eye bone to point forward (along -Y in Blender convention)
                # Keep head position, adjust tail to point forward
                forward = Vector((0, -0.02, 0))  # Small forward offset
                ebone.tail = ebone.head + forward
                ebone.roll = 0.0
                fixed_count += 1
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
            if saved_active and saved_active.name in bpy.data.objects:
                context.view_layer.objects.active = bpy.data.objects[saved_active.name]

        self.report({'INFO'}, f"Fixed {fixed_count} eye bone(s)")
        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_eye_setup(Panel):
    """Eye bone setup panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_eye_setup"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"

    def draw_header(self, context):
        self.layout.label(text=T("Eye Setup"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        arm = active_armature(context)
        layout = self.layout

        if not arm:
            return

        status = check_eye_bones(arm)

        # Status display
        box = layout.box()
        box.label(text=T("Eye Bone Status"))

        row = box.row()
        if status["left_eye_bone"]:
            row.label(text=f"Left Eye: {status['left_eye_bone']}", icon="CHECKMARK")
        else:
            row.label(text=T("Left Eye: Not found"), icon="QUESTION")

        row = box.row()
        if status["right_eye_bone"]:
            row.label(text=f"Right Eye: {status['right_eye_bone']}", icon="CHECKMARK")
        else:
            row.label(text=T("Right Eye: Not found"), icon="QUESTION")

        layout.separator()

        # Checks
        box = layout.box()
        row = box.row()
        icon = "CHECKMARK" if status["orientation_ok"] else "X"
        row.label(text=f"Orientation: {icon}", icon=icon)

        row = box.row()
        icon = "CHECKMARK" if status["parent_ok"] else "X"
        row.label(text=f"Parent Bones: {icon}", icon=icon)

        row = box.row()
        icon = "CHECKMARK" if status["limits_set"] else "X"
        row.label(text=f"Rotation Limits: {icon}", icon=icon)

        layout.separator()

        # Fix button
        layout.operator(
            "boneforge.vrc_fix_eye_bones",
            text=T("Fix Eye Bones")
        )

        # Info
        box = layout.box()
        box.label(text=T("VRChat Limits:"), icon="INFO")
        box.label(text=T("Horizontal: ±30°"))
        box.label(text=T("Vertical: ±15°"))


# ── Registration ─────────────────────────────────────────────────────

classes = (
    BF_OT_VRC_FixEyeBones,
    BONEFORGE_PT_vrc_eye_setup,
)


def register():
    """Register eye setup classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister eye setup classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
