"""BoneCraft Phase 2 — Angle-Based Corrective Shape Keys.

Corrective shape key authoring tool that creates driver-based shape keys
activated by joint angle. Drivers use explicit map-range functions via
FCurve keyframes — no custom Python expressions — so they evaluate
correctly on render farms without BoneCraft installed.
"""

import bpy
import math
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from boneforge.i18n import T

from boneforge.core import (
    active_armature,
    read_custom_json,
    write_custom_json,
    addon_prefs,
)


_CUSTOM_PROP_KEY = "boneforge_correctives"


# ── Persistence ─────────────────────────────────────────────────

def _persist_correctives(arm_obj, settings):
    """Write corrective metadata to JSON custom property."""
    data = {"correctives": []}
    for entry in settings.correctives:
        data["correctives"].append({
            "shape_key_name": entry.shape_key_name,
            "driver_bone": entry.driver_bone,
            "rotation_axis": entry.rotation_axis,
            "activation_angle": entry.activation_angle,
            "falloff_range": entry.falloff_range,
            "driver_index": entry.driver_index,
        })
    write_custom_json(arm_obj, _CUSTOM_PROP_KEY, data)


def _load_correctives(arm_obj, settings):
    """Load corrective metadata from JSON custom property."""
    data = read_custom_json(arm_obj, _CUSTOM_PROP_KEY)
    if data is None or "correctives" not in data:
        return
    settings.correctives.clear()
    for cdata in data["correctives"]:
        entry = settings.correctives.add()
        entry.shape_key_name = cdata.get("shape_key_name", "")
        entry.driver_bone = cdata.get("driver_bone", "")
        entry.rotation_axis = cdata.get("rotation_axis", "X")
        entry.activation_angle = cdata.get("activation_angle", 90.0)
        entry.falloff_range = cdata.get("falloff_range", 30.0)
        entry.driver_index = cdata.get("driver_index", 0)


def _ensure_correctives(arm_obj, settings):
    """Lazy-load correctives from custom property if runtime is empty."""
    if len(settings.correctives) == 0:
        _load_correctives(arm_obj, settings)


# ── Driver helpers ──────────────────────────────────────────────

_AXIS_MAP = {
    'X': 'ROT_X',
    'Y': 'ROT_Y',
    'Z': 'ROT_Z',
}


def _find_mesh_with_shape_keys(arm_obj):
    """Find the first child mesh with shape keys, or None."""
    for child in arm_obj.children:
        if (child.type == 'MESH'
                and child.data.shape_keys is not None
                and len(child.data.shape_keys.key_blocks) > 1):
            return child
    return None


def _shape_key_has_driver(mesh_obj, shape_key_name):
    """Check if a shape key already has a driver."""
    shape_keys = mesh_obj.data.shape_keys
    if shape_keys is None or shape_keys.animation_data is None:
        return False
    data_path = f'key_blocks["{shape_key_name}"].value'
    for driver in shape_keys.animation_data.drivers:
        if driver.data_path == data_path:
            return True
    return False


def _create_corrective_driver(arm_obj, mesh_obj, shape_key_name,
                               driver_bone, axis, activation_angle, falloff_range):
    """Create a driver on a shape key controlled by bone rotation.

    Returns the driver index for bookkeeping, or -1 on failure.
    """
    shape_keys = mesh_obj.data.shape_keys
    if shape_keys is None:
        return -1
    shape_key_block = shape_keys.key_blocks.get(shape_key_name)
    if shape_key_block is None:
        return -1

    # Add driver
    data_path = f'key_blocks["{shape_key_name}"].value'
    fcurve = shape_keys.driver_add(data_path)
    driver = fcurve.driver
    driver.type = 'AVERAGE'

    # Add variable: bone rotation on specified axis
    var = driver.variables.new()
    var.name = "angle"
    var.type = 'TRANSFORMS'
    target = var.targets[0]
    target.id = arm_obj
    target.bone_target = driver_bone
    target.transform_type = _AXIS_MAP[axis]
    target.transform_space = 'LOCAL_SPACE'

    # Build map-range via FCurve keyframes:
    # At (activation_angle - falloff_range) → shape key value = 0
    # At (activation_angle) → shape key value = 1
    angle_start = math.radians(activation_angle - falloff_range)
    angle_end = math.radians(activation_angle)

    # Clear default keyframe points
    while len(fcurve.keyframe_points) > 0:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0])

    # Add mapping keyframes
    kf1 = fcurve.keyframe_points.insert(angle_start, 0.0)
    kf1.interpolation = 'LINEAR'
    kf2 = fcurve.keyframe_points.insert(angle_end, 1.0)
    kf2.interpolation = 'LINEAR'

    # Clamp: add points at extremes so the value doesn't extrapolate
    kf0 = fcurve.keyframe_points.insert(angle_start - math.radians(10), 0.0)
    kf0.interpolation = 'LINEAR'
    kf3 = fcurve.keyframe_points.insert(angle_end + math.radians(10), 1.0)
    kf3.interpolation = 'LINEAR'

    fcurve.update()

    # Return driver index for tracking
    if shape_keys.animation_data and shape_keys.animation_data.drivers:
        return len(shape_keys.animation_data.drivers) - 1
    return 0


def _remove_corrective_driver(mesh_obj, shape_key_name):
    """Remove the driver from a shape key."""
    shape_keys = mesh_obj.data.shape_keys
    if shape_keys is None:
        return
    data_path = f'key_blocks["{shape_key_name}"].value'
    try:
        shape_keys.driver_remove(data_path)
    except TypeError:
        pass  # No driver to remove


# ── PropertyGroups ──────────────────────────────────────────────

class BF_CorrectiveEntry(bpy.types.PropertyGroup):
    """Metadata for a single corrective shape key driver."""
    shape_key_name: StringProperty(
        name="Shape Key",
        description="Name of the corrective shape key",
    )
    driver_bone: StringProperty(
        name="Driver Bone",
        description="Bone whose rotation drives this corrective",
    )
    rotation_axis: EnumProperty(
        name="Axis",
        description="Rotation axis that activates the corrective",
        items=[
            ('X', "X", "X axis rotation"),
            ('Y', "Y", "Y axis rotation"),
            ('Z', "Z", "Z axis rotation"),
        ],
        default='X',
    )
    activation_angle: FloatProperty(
        name="Activation Angle",
        description="Rotation angle (degrees) at which the corrective is fully active",
        default=90.0,
        min=0.0,
        max=180.0,
    )
    falloff_range: FloatProperty(
        name="Falloff Range",
        description="Degrees before the activation angle where blending begins",
        default=30.0,
        min=1.0,
        max=90.0,
    )
    driver_index: IntProperty(
        name="Driver Index",
        description="Index of the driver in the shape key's animation data",
        default=0,
    )


class BF_CorrectiveList(bpy.types.PropertyGroup):
    """Collection of corrective entries on the armature."""
    correctives: CollectionProperty(type=BF_CorrectiveEntry)
    active_index: IntProperty(name="Active", default=0, min=0)

    # Input fields for the create operator (not persisted as correctives)
    new_shape_key: StringProperty(name="Shape Key", default="")
    new_driver_bone: StringProperty(name="Driver Bone", default="")
    new_axis: EnumProperty(
        name="Axis",
        items=[
            ('X', "X", "X axis"),
            ('Y', "Y", "Y axis"),
            ('Z', "Z", "Z axis"),
        ],
        default='X',
    )
    new_activation: FloatProperty(name="Activation Angle", default=90.0, min=0, max=180)
    new_falloff: FloatProperty(name="Falloff", default=30.0, min=1, max=90)


# ── Operators ───────────────────────────────────────────────────

class BF_OT_CorrectiveSelect(bpy.types.Operator):
    """Select the active corrective entry"""
    bl_idname = "boneforge.corrective_select"
    bl_label = "Select Corrective"
    bl_options = {'REGISTER'}

    index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Index", default=0, min=0)

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        return len(arm.boneforge_correctives.correctives) > 0

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_correctives
        if self.index < len(settings.correctives):
            settings.active_index = self.index
        return {'FINISHED'}


class BF_OT_CorrectiveCreate(bpy.types.Operator):
    """Create a corrective shape key driver from the panel settings"""
    bl_idname = "boneforge.corrective_create"
    bl_label = "Create Corrective"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        return _find_mesh_with_shape_keys(arm) is not None

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_correctives
        mesh_obj = _find_mesh_with_shape_keys(arm)

        if mesh_obj is None:
            self.report({'WARNING'}, "No child mesh with shape keys found")
            return {'CANCELLED'}

        sk_name = settings.new_shape_key.strip()
        bone_name = settings.new_driver_bone.strip()
        axis = settings.new_axis
        angle = settings.new_activation
        falloff = settings.new_falloff

        if not sk_name:
            self.report({'WARNING'}, "No shape key name specified")
            return {'CANCELLED'}

        if not bone_name:
            self.report({'WARNING'}, "No driver bone specified")
            return {'CANCELLED'}

        # Validate bone exists
        if arm.pose.bones.get(bone_name) is None:
            self.report({'ERROR'}, f"Driver bone '{bone_name}' not found on armature")
            return {'CANCELLED'}

        # Validate shape key exists
        sk = mesh_obj.data.shape_keys
        if sk is None or sk.key_blocks.get(sk_name) is None:
            self.report({'ERROR'}, f"Shape key '{sk_name}' not found on mesh")
            return {'CANCELLED'}

        # Check for existing driver (conflict C-6)
        if _shape_key_has_driver(mesh_obj, sk_name):
            self.report({'WARNING'},
                        "Shape key already has a driver — edit or remove the existing corrective first")
            return {'CANCELLED'}

        # Create the driver
        drv_idx = _create_corrective_driver(
            arm, mesh_obj, sk_name, bone_name, axis, angle, falloff
        )
        if drv_idx < 0:
            # MIN-1 fix: include shape key name in error message
            self.report({'ERROR'}, f"Failed to create driver on '{sk_name}'")
            return {'CANCELLED'}

        # Record metadata
        entry = settings.correctives.add()
        entry.shape_key_name = sk_name
        entry.driver_bone = bone_name
        entry.rotation_axis = axis
        entry.activation_angle = angle
        entry.falloff_range = falloff
        entry.driver_index = drv_idx
        settings.active_index = len(settings.correctives) - 1

        _persist_correctives(arm, settings)

        self.report({'INFO'},
                    f"Created corrective: '{sk_name}' driven by '{bone_name}' {axis} at {angle:.0f} deg")
        return {'FINISHED'}


class BF_OT_CorrectiveEdit(bpy.types.Operator):
    """Edit parameters of an existing corrective driver"""
    bl_idname = "boneforge.corrective_edit"
    bl_label = "Edit Corrective"
    bl_options = {'REGISTER', 'UNDO'}

    activation_angle: FloatProperty(
        name="Activation Angle",
        description="Bone angle, in degrees, at which the corrective shape is fully on",
        default=90.0, min=0, max=180,
    )
    falloff_range: FloatProperty(
        name="Falloff",
        description="Degrees before the activation angle over which the shape fades in",
        default=30.0, min=1, max=90,
    )

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_correctives
        return len(settings.correctives) > 0

    def invoke(self, context, event):
        arm = active_armature(context)
        settings = arm.boneforge_correctives
        idx = settings.active_index
        if idx < len(settings.correctives):
            entry = settings.correctives[idx]
            self.activation_angle = entry.activation_angle
            self.falloff_range = entry.falloff_range
        # starts from the corrective's current values; tuned after the click in Adjust Last Operation
        return self.execute(context)

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_correctives
        mesh_obj = _find_mesh_with_shape_keys(arm)
        idx = settings.active_index

        if idx >= len(settings.correctives):
            self.report({'WARNING'}, "No corrective selected")
            return {'CANCELLED'}

        entry = settings.correctives[idx]

        if mesh_obj is None:
            self.report({'WARNING'}, "Mesh not found")
            return {'CANCELLED'}

        # Remove old driver and create new one with updated params
        _remove_corrective_driver(mesh_obj, entry.shape_key_name)
        drv_idx = _create_corrective_driver(
            arm, mesh_obj, entry.shape_key_name, entry.driver_bone,
            entry.rotation_axis, self.activation_angle, self.falloff_range
        )

        entry.activation_angle = self.activation_angle
        entry.falloff_range = self.falloff_range
        if drv_idx >= 0:
            entry.driver_index = drv_idx

        _persist_correctives(arm, settings)
        self.report({'INFO'}, f"Updated corrective '{entry.shape_key_name}'")
        return {'FINISHED'}


class BF_OT_CorrectiveDelete(bpy.types.Operator):
    """Remove a corrective driver and its metadata"""
    bl_idname = "boneforge.corrective_delete"
    bl_label = "Delete Corrective"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        settings = arm.boneforge_correctives
        return len(settings.correctives) > 0

    def execute(self, context):
        arm = active_armature(context)
        settings = arm.boneforge_correctives
        mesh_obj = _find_mesh_with_shape_keys(arm)
        idx = settings.active_index

        if idx >= len(settings.correctives):
            self.report({'WARNING'}, "No corrective selected")
            return {'CANCELLED'}

        entry = settings.correctives[idx]
        name = entry.shape_key_name

        # SIG-5 fix: Remove the driver from the mesh, inform user if mesh missing
        if mesh_obj is not None:
            _remove_corrective_driver(mesh_obj, name)
        else:
            self.report({'INFO'}, f"Mesh not found — removed metadata for '{name}'")

        # Remove metadata
        settings.correctives.remove(idx)
        settings.active_index = max(0, min(idx, len(settings.correctives) - 1))

        _persist_correctives(arm, settings)
        if mesh_obj is not None:
            self.report({'INFO'}, f"Deleted corrective '{name}'")
        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BF_PT_CorrectivesPanel(bpy.types.Panel):
    """Corrective shape key authoring panel"""
    bl_idname = "BONEFORGE_PT_correctives"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 35

    def draw_header(self, context):
        self.layout.label(text=T("Corrective Shape Keys"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        settings = arm.boneforge_correctives
        _ensure_correctives(arm, settings)

        mesh_obj = _find_mesh_with_shape_keys(arm)
        if mesh_obj is None:
            layout.label(text=T("No child mesh with shape keys found"), icon='INFO')
            layout.label(text=T("Add a basis shape key to the mesh first"))
            return

        # Existing correctives list
        if len(settings.correctives) > 0:
            for i, entry in enumerate(settings.correctives):
                box = layout.box()
                row = box.row()

                # Check if shape key still exists
                shape_keys = mesh_obj.data.shape_keys
                shape_key_exists = (shape_keys is not None
                                    and shape_keys.key_blocks.get(entry.shape_key_name) is not None)

                if not shape_key_exists:
                    row.label(text=f"[Missing] {entry.shape_key_name}", icon='ERROR')
                else:
                    # FP-3 fix: Clickable row to select active corrective
                    is_active = (i == settings.active_index)
                    icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                    sub = row.operator("boneforge.corrective_select", text=entry.shape_key_name, icon=icon)
                    sub.index = i

                row.label(text=f"{entry.driver_bone} {entry.rotation_axis}")
                row.label(text=f"{entry.activation_angle:.0f} deg")

            row = layout.row(align=True)
            row.operator("boneforge.corrective_edit", text=T("Edit"), icon='GREASEPENCIL')
            row.operator("boneforge.corrective_delete", text=T("Delete"), icon='REMOVE')
        else:
            layout.label(text=T("No correctives defined"), icon='INFO')

        layout.separator()

        # Create new corrective
        box = layout.box()
        box.label(text=T("New Corrective"))
        col = box.column(align=True)
        # FP-2 fix: Use prop_search for auto-complete dropdowns
        shape_keys = mesh_obj.data.shape_keys
        if shape_keys is not None:
            col.prop_search(settings, "new_shape_key", shape_keys, "key_blocks", text=T("Shape Key"))
        else:
            col.prop(settings, "new_shape_key")
        col.prop_search(settings, "new_driver_bone", arm.pose, "bones", text=T("Driver Bone"))
        col.prop(settings, "new_axis")
        col.prop(settings, "new_activation")
        col.prop(settings, "new_falloff")

        # Live preview: show what the driver curve would look like
        angle_start = settings.new_activation - settings.new_falloff
        box.label(
            text=f"Driver: 0.0 at {angle_start:.0f} deg → 1.0 at {settings.new_activation:.0f} deg",
        )

        box.operator("boneforge.corrective_create", text=T("Create Corrective"), icon='ADD')


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_CorrectiveEntry,
    BF_CorrectiveList,
    BF_OT_CorrectiveSelect,
    BF_OT_CorrectiveCreate,
    BF_OT_CorrectiveEdit,
    BF_OT_CorrectiveDelete,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.boneforge_correctives = PointerProperty(
        type=BF_CorrectiveList,
    )


def unregister():
    if hasattr(bpy.types.Object, 'boneforge_correctives'):
        del bpy.types.Object.boneforge_correctives
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
