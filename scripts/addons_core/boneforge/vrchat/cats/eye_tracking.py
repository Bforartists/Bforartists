"""BoneCraft VRChat CATS — Eye Tracking Setup.

Creates VRChat-compatible LeftEye / RightEye bones with Limit Rotation
constraints.  BONE CONSTRAINTS ONLY — explicit driver guard prevents any
new drivers from being written; existing drivers are detected and reported
as warnings but do NOT abort the operation.

Category: VRChat Cats Tools.
"""

import logging
from math import radians

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline

logger = logging.getLogger(__name__)

# ── Left / right eye name patterns ──────────────────────────────────────────

_LEFT_PATTERNS = ["eye_l", "eye.l", "lefteye", "eyeleft", "目.l", "左目"]
_RIGHT_PATTERNS = ["eye_r", "eye.r", "righteye", "eyeright", "目.r", "右目"]
_HEAD_PATTERNS = ["head", "頭", "neck"]


# ── Settings ─────────────────────────────────────────────────────────────────

class BF_EyeTrackingSettings(PropertyGroup):
    """Scene-level settings for CATS eye tracking setup."""

    left_eye_bone: StringProperty(
        name="Left Eye Bone",
        description="Name of the left eye bone in the armature",
        default="",
    )
    right_eye_bone: StringProperty(
        name="Right Eye Bone",
        description="Name of the right eye bone in the armature",
        default="",
    )
    up_limit: FloatProperty(
        name="Up Limit",
        description="Max upward rotation (degrees)",
        default=30.0,
        min=0.0,
        max=90.0,
        subtype='ANGLE',
    )
    down_limit: FloatProperty(
        name="Down Limit",
        description="Max downward rotation (degrees)",
        default=20.0,
        min=0.0,
        max=90.0,
        subtype='ANGLE',
    )
    side_limit: FloatProperty(
        name="Side Limit",
        description="Max left/right rotation (degrees)",
        default=30.0,
        min=0.0,
        max=90.0,
        subtype='ANGLE',
    )


# ── Auto-detect operator ──────────────────────────────────────────────────────

class BF_OT_CATS_AutoDetectEyeBones(Operator):
    """Scan armature bones for common eye bone naming conventions and
    populate the Left Eye Bone and Right Eye Bone fields automatically"""

    bl_idname = "boneforge.cats_autodetect_eyes"
    bl_label = "Auto-Detect Eye Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature in context")
            return {'CANCELLED'}

        settings = context.scene.boneforge_cats_eye_settings
        bone_names = [b.name for b in arm.data.bones]

        found_left = ""
        found_right = ""

        for name in bone_names:
            lower = name.lower()
            if not found_left:
                for pat in _LEFT_PATTERNS:
                    if pat in lower:
                        found_left = name
                        break
            if not found_right:
                for pat in _RIGHT_PATTERNS:
                    if pat in lower:
                        found_right = name
                        break
            if found_left and found_right:
                break

        detected = 0
        if found_left:
            settings.left_eye_bone = found_left
            detected += 1
        if found_right:
            settings.right_eye_bone = found_right
            detected += 1

        if detected == 0:
            self.report({'WARNING'}, "No eye bones detected — set names manually")
        else:
            self.report(
                {'INFO'},
                f"Detected {detected} eye bone(s): "
                f"Left='{found_left or 'none'}', Right='{found_right or 'none'}'",
            )

        return {'FINISHED'}


# ── Create eye tracking operator ──────────────────────────────────────────────

class BF_OT_CATS_CreateEyeTracking(Operator):
    """Create VRChat-compatible eye tracking bones with Limit Rotation
    constraints.  No drivers are written; existing drivers on eye bones
    are detected and reported as warnings only"""

    bl_idname = "boneforge.cats_create_eye_tracking"
    bl_label = "Create Eye Tracking"
    bl_options = {'REGISTER', 'UNDO'}

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _find_head_bone(edit_bones):
        """Return the first EditBone whose name matches a head pattern."""
        for pat in _HEAD_PATTERNS:
            for eb in edit_bones:
                if pat in eb.name.lower():
                    return eb
        return None

    @staticmethod
    def _driver_guard(arm, left_name, right_name):
        """Scan armature animation_data for drivers targeting the eye bones.

        EXPLICIT DRIVER GUARD — this method never creates drivers.  It only
        inspects existing ones.  If rotation FCurves are found on either eye
        bone, a warning string is returned; otherwise None is returned.
        """
        if arm.animation_data is None:
            return None
        drivers = arm.animation_data.drivers
        if not drivers:
            return None

        eye_names_lower = {
            n.lower() for n in (left_name, right_name) if n
        }
        rotation_channels = {"rotation_euler", "rotation_quaternion", "rotation_axis_angle"}

        hits = []
        for fcurve in drivers:
            data_path = fcurve.data_path
            # data_path on pose bones looks like: pose.bones["BoneName"].rotation_euler
            if "pose.bones" not in data_path:
                continue
            channel_found = any(ch in data_path for ch in rotation_channels)
            if not channel_found:
                continue
            # Extract bone name from data path
            try:
                bone_part = data_path.split('["')[1].split('"]')[0]
            except IndexError:
                continue
            if bone_part.lower() in eye_names_lower:
                hits.append(bone_part)

        if hits:
            return (
                f"Driver detected on eye bones {hits} — "
                "using constraints only, drivers ignored"
            )
        return None

    # ── Execute ───────────────────────────────────────────────────

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature in context")
            return {'CANCELLED'}

        settings = context.scene.boneforge_cats_eye_settings
        left_name = settings.left_eye_bone.strip()
        right_name = settings.right_eye_bone.strip()

        if not left_name and not right_name:
            self.report(
                {'ERROR'},
                "Both eye bone names are empty — set names or use Auto-Detect",
            )
            return {'CANCELLED'}

        # ── EXPLICIT DRIVER GUARD ──────────────────────────────────────────
        # Checks for existing rotation drivers on the eye bones.
        # If found, reports WARNING and continues — NO new drivers are created.
        warning_msg = self._driver_guard(arm, left_name, right_name)
        if warning_msg:
            self.report({'WARNING'}, warning_msg)
            logger.warning("[BoneCraft EyeTracking] %s", warning_msg)

        saved_mode = arm.mode

        try:
            context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bones = arm.data.edit_bones

            head_bone = self._find_head_bone(edit_bones)

            eye_specs = [
                ("LeftEye", left_name, Vector((0.03, -0.05, 1.6))),
                ("RightEye", right_name, Vector((-0.03, -0.05, 1.6))),
            ]
            resolved_names = []  # actual bone names that will carry constraints

            for canonical, user_name, default_pos in eye_specs:
                if user_name and user_name in edit_bones:
                    eb = edit_bones[user_name]
                    resolved_names.append(user_name)
                else:
                    # Create new bone
                    eb = edit_bones.new(canonical)
                    eb.head = arm.matrix_world.inverted() @ (
                        arm.matrix_world.translation + default_pos
                    )
                    # Ensure head + tail are different to avoid zero-length bone
                    tail_offset = Vector((0.0, -0.03, 0.0))
                    eb.tail = eb.head + tail_offset
                    eb.roll = 0.0
                    if head_bone is not None:
                        eb.parent = head_bone
                        eb.use_connect = False
                    resolved_names.append(canonical)
                    logger.info(
                        "[BoneCraft EyeTracking] Created edit bone '%s'", canonical
                    )

            bpy.ops.object.mode_set(mode='POSE')

            up_rad = radians(settings.up_limit)
            down_rad = radians(settings.down_limit)
            side_rad = radians(settings.side_limit)

            for bone_name in resolved_names:
                pose_bone = arm.pose.bones.get(bone_name)
                if pose_bone is None:
                    logger.warning(
                        "[BoneCraft EyeTracking] PoseBone '%s' not found after Edit Mode",
                        bone_name,
                    )
                    continue

                pose_bone.rotation_mode = 'XYZ'

                # Remove any pre-existing LIMIT_ROTATION constraints
                for con in list(pose_bone.constraints):
                    if con.type == 'LIMIT_ROTATION':
                        pose_bone.constraints.remove(con)

                # Up/Down limit (X axis)
                con_ud = pose_bone.constraints.new(type='LIMIT_ROTATION')
                con_ud.name = "CATS Eye Limit Up/Down"
                con_ud.owner_space = 'LOCAL'
                con_ud.use_limit_x = True
                con_ud.min_x = -down_rad   # downward = negative X in local space
                con_ud.max_x = up_rad

                # Side limit (Z axis)
                con_side = pose_bone.constraints.new(type='LIMIT_ROTATION')
                con_side.name = "CATS Eye Limit Side"
                con_side.owner_space = 'LOCAL'
                con_side.use_limit_z = True
                con_side.min_z = -side_rad
                con_side.max_z = side_rad

        except Exception as exc:
            logger.exception("[BoneCraft EyeTracking] Unexpected error: %s", exc)
            self.report({'ERROR'}, f"Eye tracking setup failed: {exc}")
            return {'CANCELLED'}

        finally:
            # Always return to Object Mode regardless of outcome
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        # ── Pipeline ledger ───────────────────────────────────────────────
        scene = context.scene
        msg = f"Eye tracking created: {', '.join(resolved_names)} with Limit Rotation constraints"
        pipeline.append_ledger(scene, "eye_tracking", pipeline.OUTCOME_CHANGED, msg)
        pipeline.set_phase_complete(scene, "eye_tracking", pipeline.OUTCOME_CHANGED)

        self.report({'INFO'}, f"Eye tracking created: LeftEye, RightEye with Limit Rotation constraints")
        return {'FINISHED'}


# ── Panel ─────────────────────────────────────────────────────────────────────

class CATS_PT_eye_tracking_props(Panel):
    """CATS Eye Tracking setup panel in the 3D Viewport sidebar."""

    bl_label = " "
    bl_idname = "CATS_PT_eye_tracking_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Eye Tracking"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_eye_tracking in cats_panel.py

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.boneforge_cats_eye_settings

        # Bone name fields
        col = layout.column(align=True)
        col.prop(settings, "left_eye_bone", text=T("Left Eye"))
        col.prop(settings, "right_eye_bone", text=T("Right Eye"))

        layout.separator()

        # Rotation limit fields
        col2 = layout.column(align=True)
        col2.prop(settings, "up_limit", text=T("Up Limit °"))
        col2.prop(settings, "down_limit", text=T("Down Limit °"))
        col2.prop(settings, "side_limit", text=T("Side Limit °"))

        layout.separator()

        row = layout.row()
        row.operator("boneforge.cats_autodetect_eyes", text=T("Auto-Detect"), icon='VIEWZOOM')

        layout.operator(
            "boneforge.cats_create_eye_tracking",
            text=T("Create Eye Tracking"),
            icon='HIDE_OFF',
        )

        # Advisory: recommend running fix_model first
        from boneforge.vrchat.cats import pipeline as _pl
        fix_done = _pl.is_phase_complete(scene, "fix_model")
        if not fix_done:
            box = layout.box()
            box.label(text=T("Run Fix Model first for best results"), icon='ERROR')


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    BF_EyeTrackingSettings,
    BF_OT_CATS_AutoDetectEyeBones,
    BF_OT_CATS_CreateEyeTracking,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.boneforge_cats_eye_settings = bpy.props.PointerProperty(
        type=BF_EyeTrackingSettings
    )


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Scene, "boneforge_cats_eye_settings"):
        del bpy.types.Scene.boneforge_cats_eye_settings
