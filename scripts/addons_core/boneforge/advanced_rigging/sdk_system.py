"""BoneCraft Phase 2C — Set Driven Key (SDK) System.

Generalized driver creation for arbitrary driver-to-driven
relationships using native Blender FCurves (no Python expressions).
Category: Advanced Rigging.
"""

import json
import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
)
from boneforge.i18n import T
from bpy.types import Panel, Operator, PropertyGroup


# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Maps an SDK attribute identifier to the (pose-bone property name, component
# index) pair used for both value extraction and driver-target construction.
# This single table replaces three parallel 9-branch elif ladders.
_SDK_ATTRIBUTE_MAP = {
    "LOC_X":   ("location",        0),
    "LOC_Y":   ("location",        1),
    "LOC_Z":   ("location",        2),
    "ROT_X":   ("rotation_euler",  0),
    "ROT_Y":   ("rotation_euler",  1),
    "ROT_Z":   ("rotation_euler",  2),
    "SCALE_X": ("scale",           0),
    "SCALE_Y": ("scale",           1),
    "SCALE_Z": ("scale",           2),
}


def _get_bone_attribute_value(pose_bone, attribute):
    """Return the scalar component of ``pose_bone`` named by ``attribute``.

    Returns ``0.0`` for unknown attribute identifiers, matching the original
    elif-ladder fallthrough behavior.
    """
    mapping = _SDK_ATTRIBUTE_MAP.get(attribute)
    if mapping is None:
        return 0.0
    prop_name, index = mapping
    return getattr(pose_bone, prop_name)[index]


def _get_driver_target(pose_bone, attribute):
    """Return (pose_bone, property-path, component-index) for ``attribute``.

    Returns ``None`` for unknown attribute identifiers.
    """
    mapping = _SDK_ATTRIBUTE_MAP.get(attribute)
    if mapping is None:
        return None
    prop_name, index = mapping
    return (pose_bone, prop_name, index)


# SDK Data Model
class BF_SDKCurvePoint(PropertyGroup):
    """Single point on an SDK curve"""
    driver_value: FloatProperty(
        name="Driver Value",
        description="Input value from driver bone",
        default=0.0,
    )
    driven_value: FloatProperty(
        name="Driven Value",
        description="Output value for target attribute",
        default=0.0,
    )


class BF_SDKDrivenTarget(PropertyGroup):
    """Single driven target in an SDK relationship"""
    target_bone_name: StringProperty(
        name="Target Bone",
        description="Name of the bone being driven",
        default="",
    )
    target_type: EnumProperty(
        name="Target Type",
        description="Type of target being driven",
        items=[
            ("BONE", "Bone", "Drive a bone transform"),
            ("SHAPE_KEY", "Shape Key", "Drive a shape key"),
        ],
        default="BONE",
    )
    target_attribute: EnumProperty(
        name="Target Attribute",
        description="Attribute being driven",
        items=[
            ("LOC_X", "Location X", "X location"),
            ("LOC_Y", "Location Y", "Y location"),
            ("LOC_Z", "Location Z", "Z location"),
            ("ROT_X", "Rotation X", "X rotation"),
            ("ROT_Y", "Rotation Y", "Y rotation"),
            ("ROT_Z", "Rotation Z", "Z rotation"),
            ("SCALE_X", "Scale X", "X scale"),
            ("SCALE_Y", "Scale Y", "Y scale"),
            ("SCALE_Z", "Scale Z", "Z scale"),
        ],
        default="LOC_Z",
    )
    curve_points: CollectionProperty(
        type=BF_SDKCurvePoint,
        name="Curve Points",
        description="Control points defining the driver/driven relationship",
    )


class BF_SDKRelationship(PropertyGroup):
    """Complete SDK relationship linking driver to driven targets"""
    driver_bone_name: StringProperty(
        name="Driver Bone",
        description="Name of the bone controlling the SDK",
        default="",
    )
    driver_attribute: EnumProperty(
        name="Driver Attribute",
        description="Attribute being read from driver bone",
        items=[
            ("LOC_X", "Location X", "X location"),
            ("LOC_Y", "Location Y", "Y location"),
            ("LOC_Z", "Location Z", "Z location"),
            ("ROT_X", "Rotation X", "X rotation"),
            ("ROT_Y", "Rotation Y", "Y rotation"),
            ("ROT_Z", "Rotation Z", "Z rotation"),
            ("SCALE_X", "Scale X", "X scale"),
            ("SCALE_Y", "Scale Y", "Y scale"),
            ("SCALE_Z", "Scale Z", "Z scale"),
            ("CUSTOM", "Custom", "Custom property"),
        ],
        default="LOC_Z",
    )
    driven_targets: CollectionProperty(
        type=BF_SDKDrivenTarget,
        name="Driven Targets",
        description="Targets controlled by this SDK",
    )


class BONEFORGE_PT_p2c_sdk_author(Panel):
    """SDK Author and Inspector panel"""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_sdk_author"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Set Driven Key"))

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )

    def draw(self, context):
        layout = self.layout
        arm = context.active_object
        scene = context.scene

        # Author sub-panel
        box = layout.box()
        box.label(text=T("Author SDK"))

        col = box.column(align=True)
        col.prop(scene, "boneforge_sdk_driver_bone", text=T("Driver Bone"))
        col.prop(scene, "boneforge_sdk_driver_attribute", text=T("Driver Attribute"))

        col = box.column(align=True)
        col.label(text=T("Driven Targets"))
        col.prop(scene, "boneforge_sdk_driven_target_bone", text=T("Target Bone"))
        col.prop(scene, "boneforge_sdk_driven_target_attr", text=T("Target Attribute"))

        row = box.row(align=True)
        row.operator("boneforge.sdk_set_driver_value", text=T("Set Value"))
        row.operator("boneforge.sdk_record_point", text=T("Record Point"))

        box.operator("boneforge.sdk_create", text=T("Create SDK"))

        # Inspect sub-panel
        if arm.data.get("boneforge_p2c_sdk"):
            box = layout.box()
            box.label(text=T("Existing SDKs"))

            sdk_data = json.loads(arm.data["boneforge_p2c_sdk"])
            for i, sdk in enumerate(sdk_data):
                sub = box.column(align=True)
                sub.label(
                    text=f"{sdk['driver_bone']} ({sdk['driver_attribute']}) → {len(sdk['driven_targets'])} targets"
                )

                row = sub.row(align=True)
                row.operator(
                    "boneforge.sdk_edit",
                    text=T("Edit"),
                ).sdk_index = i
                row.operator(
                    "boneforge.sdk_delete",
                    text=T("Delete"),
                ).sdk_index = i


class BF_OT_SDKSetDriverValue(Operator):
    """Set the current driver bone value"""
    bl_idname = "boneforge.sdk_set_driver_value"
    bl_label = "Set Driver Value"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and scene.boneforge_sdk_driver_bone != ""
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        scene = context.scene

        driver_bone_name = scene.boneforge_sdk_driver_bone
        driver_attr = scene.boneforge_sdk_driver_attribute

        if driver_bone_name not in arm.bones:
            self.report({"ERROR"}, f"Driver bone '{driver_bone_name}' not found")
            return {"FINISHED"}

        pose_bone = arm_obj.pose.bones[driver_bone_name]

        # Get current value
        value = self._get_bone_attribute_value(pose_bone, driver_attr)

        # Store in temporary scene property
        scene.boneforge_sdk_current_driver_value = value

        self.report({"INFO"}, f"Driver value set to {value:.3f}")
        return {"FINISHED"}

    def _get_bone_attribute_value(self, pose_bone, attribute):
        """Extract value from bone attribute (delegates to module helper)."""
        return _get_bone_attribute_value(pose_bone, attribute)


class BF_OT_SDKRecordPoint(Operator):
    """Record current driver and driven values as SDK curve point"""
    bl_idname = "boneforge.sdk_record_point"
    bl_label = "Record SDK Point"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and scene.boneforge_sdk_driver_bone != ""
            and scene.boneforge_sdk_driven_target_bone != ""
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        scene = context.scene

        driver_bone_name = scene.boneforge_sdk_driver_bone
        driver_attr = scene.boneforge_sdk_driver_attribute
        target_bone_name = scene.boneforge_sdk_driven_target_bone
        target_attr = scene.boneforge_sdk_driven_target_attr

        if driver_bone_name not in arm.bones:
            self.report({"ERROR"}, f"Driver bone '{driver_bone_name}' not found")
            return {"FINISHED"}

        if target_bone_name not in arm.bones:
            self.report({"ERROR"}, f"Target bone '{target_bone_name}' not found")
            return {"FINISHED"}

        pose_driver = arm_obj.pose.bones[driver_bone_name]
        pose_target = arm_obj.pose.bones[target_bone_name]

        driver_value = self._get_bone_attribute_value(pose_driver, driver_attr)
        driven_value = self._get_bone_attribute_value(pose_target, target_attr)

        # Store temporary values
        scene.boneforge_sdk_current_driver_value = driver_value
        scene.boneforge_sdk_current_driven_value = driven_value
        scene.boneforge_sdk_current_driven_bone = target_bone_name

        self.report(
            {"INFO"},
            f"Recorded point: {driver_value:.3f} → {driven_value:.3f}",
        )
        return {"FINISHED"}

    def _get_bone_attribute_value(self, pose_bone, attribute):
        """Extract value from bone attribute (delegates to module helper)."""
        return _get_bone_attribute_value(pose_bone, attribute)


class BF_OT_SDKCreate(Operator):
    """Create native Blender driver with SDK curve points"""
    bl_idname = "boneforge.sdk_create"
    bl_label = "Create SDK"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and scene.boneforge_sdk_driver_bone != ""
            and scene.boneforge_sdk_driven_target_bone != ""
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        scene = context.scene

        driver_bone_name = scene.boneforge_sdk_driver_bone
        driver_attr = scene.boneforge_sdk_driver_attribute
        target_bone_name = scene.boneforge_sdk_driven_target_bone
        target_attr = scene.boneforge_sdk_driven_target_attr

        # Validate bones exist
        if driver_bone_name not in arm.bones or target_bone_name not in arm.bones:
            self.report({"ERROR"}, "Driver or target bone not found")
            return {"FINISHED"}

        pose_target = arm_obj.pose.bones[target_bone_name]

        # Collect all curve points to insert
        curve_points = []
        if arm.get("boneforge_p2c_sdk"):
            sdk_data = json.loads(arm["boneforge_p2c_sdk"])
            for sdk in sdk_data:
                if (sdk['driver_bone'] == driver_bone_name and
                    sdk['driver_attribute'] == driver_attr):
                    for target in sdk['driven_targets']:
                        if (target['target_bone'] == target_bone_name and
                            target['target_attribute'] == target_attr):
                            for point in target['curve_points']:
                                curve_points.append((point['driver'], point['driven']))
                            break

        # If no stored points, use current recorded values
        if not curve_points:
            driver_value_1 = scene.boneforge_sdk_current_driver_value
            driven_value_1 = scene.boneforge_sdk_current_driven_value
            curve_points = [(driver_value_1, driven_value_1)]

        # Check if target is a shape key
        target_is_shape_key = False
        if arm.get("boneforge_p2c_sdk"):
            sdk_data = json.loads(arm["boneforge_p2c_sdk"])
            for sdk in sdk_data:
                if (sdk['driver_bone'] == driver_bone_name and
                    sdk['driver_attribute'] == driver_attr):
                    for target in sdk['driven_targets']:
                        if (target['target_bone'] == target_bone_name and
                            target.get('target_type') == 'SHAPE_KEY'):
                            target_is_shape_key = True
                            break

        if target_is_shape_key:
            # Handle shape key target
            mesh_obj = None
            for obj in context.scene.objects:
                if (obj.type == 'MESH' and obj.parent == arm_obj):
                    mesh_obj = obj
                    break

            if not mesh_obj or not mesh_obj.data.shape_keys:
                self.report({"ERROR"}, "No shape keys found on parented mesh")
                return {"FINISHED"}

            shape_keys = mesh_obj.data.shape_keys
            if target_bone_name not in shape_keys.key_blocks:
                self.report({"ERROR"}, f"Shape key '{target_bone_name}' not found")
                return {"FINISHED"}

            shape_key_block = shape_keys.key_blocks[target_bone_name]
            fcurve = shape_key_block.driver_add("value")
            driver = fcurve.driver
        else:
            # Handle bone target
            driver_info = self._get_driver_target(pose_target, target_attr)
            if not driver_info:
                self.report({"ERROR"}, f"Cannot create driver for {target_attr}")
                return {"FINISHED"}

            obj, path, index = driver_info
            fcurve = obj.driver_add(path, index)
            driver = fcurve.driver

        # Set up driver
        driver.type = "AVERAGE"
        driver_var = driver.variables.new()
        driver_var.type = "TRANSFORMS"
        driver_var.targets[0].id = arm_obj
        driver_var.targets[0].bone_target = driver_bone_name
        driver_var.targets[0].transform_type = self._get_transform_type(driver_attr)
        driver_var.targets[0].transform_space = "LOCAL_SPACE"

        # Insert all curve points
        for driver_value, driven_value in curve_points:
            fcurve.keyframe_points.insert(driver_value, driven_value)

        # Store in JSON data for inspection
        self._store_sdk_relationship(
            arm,
            driver_bone_name,
            driver_attr,
            target_bone_name,
            target_attr,
            curve_points,
        )

        self.report({"INFO"}, f"Created SDK: {driver_bone_name} → {target_bone_name}")
        return {"FINISHED"}

    def _get_driver_target(self, pose_bone, attribute):
        """Get (object, path, index) for the attribute (delegates to module helper)."""
        return _get_driver_target(pose_bone, attribute)

    def _get_transform_type(self, attribute):
        """Map attribute to Blender transform type"""
        mapping = {
            "LOC_X": "LOC_X",
            "LOC_Y": "LOC_Y",
            "LOC_Z": "LOC_Z",
            "ROT_X": "ROT_X",
            "ROT_Y": "ROT_Y",
            "ROT_Z": "ROT_Z",
            "SCALE_X": "SCALE_X",
            "SCALE_Y": "SCALE_Y",
            "SCALE_Z": "SCALE_Z",
        }
        return mapping.get(attribute, "LOC_Z")

    def _store_sdk_relationship(self, arm, driver_bone, driver_attr, target_bone, target_attr, points):
        """Store SDK relationship in JSON custom property"""
        sdk_data = []
        if arm.get("boneforge_p2c_sdk"):
            sdk_data = json.loads(arm["boneforge_p2c_sdk"])

        new_relationship = {
            "driver_bone": driver_bone,
            "driver_attribute": driver_attr,
            "driven_targets": [
                {
                    "target_bone": target_bone,
                    "target_attribute": target_attr,
                    "curve_points": [{"driver": p[0], "driven": p[1]} for p in points],
                }
            ],
        }

        sdk_data.append(new_relationship)
        arm["boneforge_p2c_sdk"] = json.dumps(sdk_data)


class BF_OT_SDKEdit(Operator):
    """Edit an existing SDK relationship"""
    bl_idname = "boneforge.sdk_edit"
    bl_label = "Edit SDK"
    bl_options = {"REGISTER", "UNDO"}

    sdk_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )

    def execute(self, context):
        arm = context.active_object.data
        scene = context.scene

        if not arm.get("boneforge_p2c_sdk"):
            self.report({"ERROR"}, "No SDK data found")
            return {"FINISHED"}

        sdk_data = json.loads(arm["boneforge_p2c_sdk"])
        if self.sdk_index >= len(sdk_data):
            self.report({"ERROR"}, "SDK index out of range")
            return {"FINISHED"}

        sdk = sdk_data[self.sdk_index]

        # Populate scene properties from stored relationship data
        scene.boneforge_sdk_driver_bone = sdk['driver_bone']
        scene.boneforge_sdk_driver_attribute = sdk['driver_attribute']

        # Populate first driven target into the scene properties
        if sdk['driven_targets']:
            first_target = sdk['driven_targets'][0]
            scene.boneforge_sdk_driven_target_bone = first_target['target_bone']
            scene.boneforge_sdk_driven_target_attr = first_target['target_attribute']

        self.report(
            {"INFO"},
            f"Editing: {sdk['driver_bone']} → {len(sdk['driven_targets'])} targets",
        )
        return {"FINISHED"}


class BF_OT_SDKDelete(Operator):
    """Delete an existing SDK relationship"""
    bl_idname = "boneforge.sdk_delete"
    bl_label = "Delete SDK"
    bl_options = {"REGISTER", "UNDO"}

    sdk_index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0)

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        arm = context.active_object.data

        if not arm.get("boneforge_p2c_sdk"):
            self.report({"ERROR"}, "No SDK data found")
            return {"FINISHED"}

        sdk_data = json.loads(arm["boneforge_p2c_sdk"])
        if self.sdk_index >= len(sdk_data):
            self.report({"ERROR"}, "SDK index out of range")
            return {"FINISHED"}

        deleted = sdk_data.pop(self.sdk_index)
        arm["boneforge_p2c_sdk"] = json.dumps(sdk_data)

        self.report({"INFO"}, f"Deleted SDK: {deleted['driver_bone']}")
        return {"FINISHED"}


def register():
    """Register SDK system classes and properties"""
    bpy.utils.register_class(BF_SDKCurvePoint)
    bpy.utils.register_class(BF_SDKDrivenTarget)
    bpy.utils.register_class(BF_SDKRelationship)
    bpy.utils.register_class(BONEFORGE_PT_p2c_sdk_author)
    bpy.utils.register_class(BF_OT_SDKSetDriverValue)
    bpy.utils.register_class(BF_OT_SDKRecordPoint)
    bpy.utils.register_class(BF_OT_SDKCreate)
    bpy.utils.register_class(BF_OT_SDKEdit)
    bpy.utils.register_class(BF_OT_SDKDelete)

    # Scene properties
    bpy.types.Scene.boneforge_sdk_driver_bone = StringProperty(
        name="Driver Bone",
        description="Bone that drives the SDK",
        default="",
    )
    bpy.types.Scene.boneforge_sdk_driver_attribute = EnumProperty(
        name="Driver Attribute",
        description="Attribute being read",
        items=[
            ("LOC_X", "Location X", "X location"),
            ("LOC_Y", "Location Y", "Y location"),
            ("LOC_Z", "Location Z", "Z location"),
            ("ROT_X", "Rotation X", "X rotation"),
            ("ROT_Y", "Rotation Y", "Y rotation"),
            ("ROT_Z", "Rotation Z", "Z rotation"),
            ("SCALE_X", "Scale X", "X scale"),
            ("SCALE_Y", "Scale Y", "Y scale"),
            ("SCALE_Z", "Scale Z", "Z scale"),
            ("CUSTOM", "Custom", "Custom property"),
        ],
        default="LOC_Z",
    )
    bpy.types.Scene.boneforge_sdk_driven_target_bone = StringProperty(
        name="Driven Target Bone",
        description="Bone being driven",
        default="",
    )
    bpy.types.Scene.boneforge_sdk_driven_target_attr = EnumProperty(
        name="Driven Target Attribute",
        description="Attribute being driven",
        items=[
            ("LOC_X", "Location X", "X location"),
            ("LOC_Y", "Location Y", "Y location"),
            ("LOC_Z", "Location Z", "Z location"),
            ("ROT_X", "Rotation X", "X rotation"),
            ("ROT_Y", "Rotation Y", "Y rotation"),
            ("ROT_Z", "Rotation Z", "Z rotation"),
            ("SCALE_X", "Scale X", "X scale"),
            ("SCALE_Y", "Scale Y", "Y scale"),
            ("SCALE_Z", "Scale Z", "Z scale"),
        ],
        default="LOC_Z",
    )
    bpy.types.Scene.boneforge_sdk_current_driver_value = FloatProperty(
        name="Current Driver Value",
        description="Current value of driver attribute",
        default=0.0,
    )
    bpy.types.Scene.boneforge_sdk_current_driven_value = FloatProperty(
        name="Current Driven Value",
        description="Current value of driven attribute",
        default=0.0,
    )
    bpy.types.Scene.boneforge_sdk_current_driven_bone = StringProperty(
        name="Current Driven Bone",
        description="Currently recorded driven bone",
        default="",
    )


def unregister():
    """Unregister SDK system classes and properties"""
    bpy.utils.unregister_class(BF_OT_SDKDelete)
    bpy.utils.unregister_class(BF_OT_SDKEdit)
    bpy.utils.unregister_class(BF_OT_SDKCreate)
    bpy.utils.unregister_class(BF_OT_SDKRecordPoint)
    bpy.utils.unregister_class(BF_OT_SDKSetDriverValue)
    bpy.utils.unregister_class(BONEFORGE_PT_p2c_sdk_author)
    bpy.utils.unregister_class(BF_SDKRelationship)
    bpy.utils.unregister_class(BF_SDKDrivenTarget)
    bpy.utils.unregister_class(BF_SDKCurvePoint)

    # Remove scene properties
    if hasattr(bpy.types.Scene, "boneforge_sdk_driver_bone"):
        del bpy.types.Scene.boneforge_sdk_driver_bone
    if hasattr(bpy.types.Scene, "boneforge_sdk_driver_attribute"):
        del bpy.types.Scene.boneforge_sdk_driver_attribute
    if hasattr(bpy.types.Scene, "boneforge_sdk_driven_target_bone"):
        del bpy.types.Scene.boneforge_sdk_driven_target_bone
    if hasattr(bpy.types.Scene, "boneforge_sdk_driven_target_attr"):
        del bpy.types.Scene.boneforge_sdk_driven_target_attr
    if hasattr(bpy.types.Scene, "boneforge_sdk_current_driver_value"):
        del bpy.types.Scene.boneforge_sdk_current_driver_value
    if hasattr(bpy.types.Scene, "boneforge_sdk_current_driven_value"):
        del bpy.types.Scene.boneforge_sdk_current_driven_value
    if hasattr(bpy.types.Scene, "boneforge_sdk_current_driven_bone"):
        del bpy.types.Scene.boneforge_sdk_current_driven_bone
