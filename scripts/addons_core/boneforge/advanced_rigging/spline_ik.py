"""BoneCraft Phase 2C — Spline IK Chain System.

Creates NURBS-curve-based Spline IK setups for flexible chains
like tails, tentacles, spines, and hair.
Category: Advanced Rigging.
"""

import bpy
from bpy.props import IntProperty, BoolProperty, EnumProperty
from bpy.types import Panel, Operator
import mathutils
from boneforge.weights.shapes import generate_sphere_wire, create_shape_object
from boneforge.i18n import T


class BONEFORGE_PT_p2c_spline_ik(Panel):
    """Spline IK Chain System panel"""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_spline_ik"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Spline IK"))

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

        # act first, tune later: chain length, resolution, stretch and volume are adjusted after generating
        layout.operator("boneforge.generate_spline_ik", text=T("Generate Spline IK"))
        layout.operator("boneforge.remove_spline_ik", text=T("Remove Spline IK"))
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Chain length, curve resolution, stretch and volume: adjust them after "
                                       "generating, in the Adjust Last Operation panel."))


class BF_OT_GenerateSplineIK(Operator):
    """Generate Spline IK constraint on selected bone chain"""
    bl_idname = "boneforge.generate_spline_ik"
    bl_label = "Generate Spline IK"
    bl_options = {"REGISTER", "UNDO"}

    # options: tuned after the click in Adjust Last Operation
    chain_length: IntProperty(
        name="Chain Length",
        description="Number of bones in the chain, starting at the active bone",
        min=1, max=20, default=4,
    )
    curve_resolution: IntProperty(
        name="Curve Resolution",
        description="Number of control points on the curve",
        min=2, max=12, default=4,
    )
    stretch: BoolProperty(
        name="Stretch",
        description="Stretch the bones to fit the whole curve; off keeps their own length",
        default=True,
    )
    volume_preservation: BoolProperty(
        name="Volume Preservation",
        description="Thin the bones as they stretch and thicken them as they squash",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and context.active_bone is not None
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        root_bone = context.active_bone

        chain_length = self.chain_length
        curve_resolution = self.curve_resolution
        stretch = self.stretch
        volume_preservation = self.volume_preservation

        # Collect chain bones (by name below: entering edit mode rebuilds the bones)
        chain_bones = self._collect_chain(root_bone, chain_length)
        if len(chain_bones) < 2:
            self.report({"ERROR"}, "Chain must have at least 2 bones")
            return {"FINISHED"}

        root_name, tip_name = root_bone.name, chain_bones[-1].name

        # Create NURBS curve
        curve_name = f"{root_name}_Spline_Curve"
        curve_data = bpy.data.curves.new(curve_name, "CURVE")
        curve_data.dimensions = "3D"
        curve_obj = bpy.data.objects.new(curve_name, curve_data)
        context.collection.objects.link(curve_obj)

        # Create NURBS curve fitted to chain
        self._fit_curve_to_chain(curve_obj, arm_obj, chain_bones, curve_resolution)

        # Create control bones collection
        coll_name = f"{root_name}_Spline_Controls"
        if coll_name not in bpy.data.collections:
            ctrl_coll = bpy.data.collections.new(coll_name)
            context.collection.children.link(ctrl_coll)
        else:
            ctrl_coll = bpy.data.collections[coll_name]

        # Create control bones
        control_bones = self._create_control_bones(
            arm_obj, curve_obj, root_name, curve_resolution, ctrl_coll
        )

        # Apply Spline IK constraint
        tip_pose_bone = arm_obj.pose.bones.get(tip_name)
        if tip_pose_bone is None:
            self.report({"ERROR"}, f"Pose bone not found: {tip_name}")
            return {"FINISHED"}
        spline_constraint = tip_pose_bone.constraints.new(type="SPLINE_IK")
        spline_constraint.target = curve_obj
        spline_constraint.chain_count = len(chain_bones)   # the bones that exist, not the length asked for
        # the Spline IK constraint's own settings (the old use_stretch / use_volume_preservation /
        # twist-mode names do not exist on it and stopped the operator)
        spline_constraint.y_scale_mode = 'FIT_CURVE' if stretch else 'BONE_ORIGINAL'
        spline_constraint.xz_scale_mode = 'VOLUME_PRESERVE' if volume_preservation else 'NONE'

        self.report({"INFO"}, f"Created Spline IK on {tip_name}")
        return {"FINISHED"}

    def _collect_chain(self, root_bone, length):
        """Collect bone chain starting from root"""
        chain = [root_bone]
        current = root_bone
        for _ in range(length - 1):
            if not current.children:
                break
            current = current.children[0]
            chain.append(current)
        return chain

    def _fit_curve_to_chain(self, curve_obj, arm_obj, chain_bones, resolution):
        """Create NURBS curve fitted to bone chain"""
        curve = curve_obj.data
        curve.resolution_u = resolution

        # Get bone positions in world space
        positions = []
        for bone in chain_bones:
            bone_world = arm_obj.matrix_world @ bone.head
            positions.append(bone_world)

        # Create nurbs points
        polyline = curve.splines.new("NURBS")
        polyline.points.add(len(positions) - 1)

        for i, pos in enumerate(positions):
            point = polyline.points[i]
            point.co = (pos.x, pos.y, pos.z, 1.0)

        polyline.use_endpoint_u = True

    def _create_control_bones(self, arm_obj, curve_obj, root_name, resolution, ctrl_coll):
        """Create control bones with hook constraints"""
        arm = arm_obj.data
        control_bones = []

        # Get curve points
        curve = curve_obj.data
        if not curve.splines:
            return control_bones

        spline = curve.splines[0]
        num_controls = len(spline.points)

        # Enter edit mode to create bones
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")

        for i in range(num_controls):
            bone_name = f"{root_name}_Spline_Ctrl_{i:02d}"
            new_bone = arm.edit_bones.new(bone_name)

            # Position at curve point
            point = spline.points[i]
            new_bone.head = mathutils.Vector((point.co[0], point.co[1], point.co[2]))
            new_bone.tail = new_bone.head + mathutils.Vector((0, 0, 0.1))

            control_bones.append(new_bone.name)      # names: edit bones die when edit mode ends

        bpy.ops.object.mode_set(mode="OBJECT")

        # Add hook constraints from curve points to control bones and assign shapes
        for name in control_bones:
            # Create and assign sphere wireframe shape
            verts, edges = generate_sphere_wire(radius=0.03, rings=4, segments=6)
            shape_obj = create_shape_object(f"{name}_Shape", verts, edges)

            # Assign shape to control bone
            arm_obj.pose.bones[name].custom_shape = shape_obj

            # Tag as non-deform control bone
            arm.bones[name]['boneforge_deform_layer'] = False

        return control_bones


class BF_OT_RemoveSplineIK(Operator):
    """Remove Spline IK from selected bone chain"""
    bl_idname = "boneforge.remove_spline_ik"
    bl_label = "Remove Spline IK"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and context.active_bone is not None
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        active_bone = context.active_bone
        active_pose_bone = context.active_pose_bone or arm_obj.pose.bones.get(active_bone.name)
        if active_pose_bone is None:
            self.report({"WARNING"}, "Active pose bone not found")
            return {"CANCELLED"}

        # Remove Spline IK constraint
        for constraint in list(active_pose_bone.constraints):
            if constraint.type == "SPLINE_IK":
                active_pose_bone.constraints.remove(constraint)

        self.report({"INFO"}, "Removed Spline IK constraints")
        return {"FINISHED"}


def register():
    """Register Spline IK classes and properties"""
    bpy.utils.register_class(BONEFORGE_PT_p2c_spline_ik)
    bpy.utils.register_class(BF_OT_GenerateSplineIK)
    bpy.utils.register_class(BF_OT_RemoveSplineIK)

    # Scene properties
    bpy.types.Scene.boneforge_spline_chain_length = IntProperty(
        name="Chain Length",
        description="Number of bones in the chain",
        min=1,
        max=20,
        default=4,
    )
    bpy.types.Scene.boneforge_spline_curve_resolution = IntProperty(
        name="Curve Resolution",
        description="Control point resolution for the curve",
        min=2,
        max=12,
        default=4,
    )
    bpy.types.Scene.boneforge_spline_stretch = BoolProperty(
        name="Stretch",
        description="Enable stretch on the spline",
        default=True,
    )
    bpy.types.Scene.boneforge_spline_twist_distribution = EnumProperty(
        name="Twist Distribution",
        description="Twist distribution method",
        items=[
            ("LINEAR", "Linear", "Linear twist distribution"),
            ("EASE_IN", "Ease In", "Ease in twist distribution"),
            ("EASE_OUT", "Ease Out", "Ease out twist distribution"),
            ("SMOOTH", "Smooth", "Smooth twist distribution"),
        ],
        default="LINEAR",
    )
    bpy.types.Scene.boneforge_spline_volume_preservation = BoolProperty(
        name="Volume Preservation",
        description="Enable volume preservation",
        default=False,
    )


def unregister():
    """Unregister Spline IK classes and properties"""
    bpy.utils.unregister_class(BONEFORGE_PT_p2c_spline_ik)
    bpy.utils.unregister_class(BF_OT_GenerateSplineIK)
    bpy.utils.unregister_class(BF_OT_RemoveSplineIK)

    # Remove scene properties
    if hasattr(bpy.types.Scene, "boneforge_spline_chain_length"):
        del bpy.types.Scene.boneforge_spline_chain_length
    if hasattr(bpy.types.Scene, "boneforge_spline_curve_resolution"):
        del bpy.types.Scene.boneforge_spline_curve_resolution
    if hasattr(bpy.types.Scene, "boneforge_spline_stretch"):
        del bpy.types.Scene.boneforge_spline_stretch
    if hasattr(bpy.types.Scene, "boneforge_spline_twist_distribution"):
        del bpy.types.Scene.boneforge_spline_twist_distribution
    if hasattr(bpy.types.Scene, "boneforge_spline_volume_preservation"):
        del bpy.types.Scene.boneforge_spline_volume_preservation
